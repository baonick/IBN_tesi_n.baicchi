"""
catalogo_errori.py — LLM Error Catalog on IBN Prolog Facts
========================================================================

Classifies each difference between Gold Standard and LLM Prediction into 4 categories:
    A. SYNTAX        — structural errors (dots, parentheses, arity)          → High
    B. WRONG VALUES  — type/value-unit/hard-soft mismatch                    → High
       Low Severity Exceptions: hard→soft (stricter constraint),
                                lower latency or higher bandwidth (stricter constraint)
    C. WRONG VNFs    — topology, target chain, edge/cloud assignment         → High
    D. INSERTIONS/REMOVALS — extra or missing facts (FP / FN)                → High

Automatically traverses all output folders in the workspace, detects
prediction files (pattern 'output_context*' and 'context*_intent*'), pairs them
with the gold standard in intent/ and produces a summary report.

It uses the same set logic of esegui_valutazione_tutti_schemi.py
and MetricExecuterInputDips.py for extraction and normalization of facts.
"""

import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
#  Import the existing metrics module
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import MetricExecuterInputDips as metrics  # noqa: E402

# ---------------------------------------------------------------------------
#  CONFIGURATION
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # project root (IBN github/)
CARTELLA_INTENTI_IDEALI = os.path.join(BASE_DIR, "intent")




# ============================================================================
#  STRUCTURE FOR ACCUMULATING ERRORS
# ============================================================================
class ErrorEntry:
    """Single cataloged error entry."""
    def __init__(self, categoria, sottotipo, gravita, descrizione,
                 fatto_llm="", fatto_gold="", file_sorgente=""):
        self.categoria = categoria       # "A", "B", "C", "D"
        self.sottotipo = sottotipo       # e.g. "UNBALANCED_PARENTHESES"
        self.gravita = gravita           # "Alta" (High) or "Bassa" (Low)
        self.descrizione = descrizione   # human-readable string
        self.fatto_llm = fatto_llm
        self.fatto_gold = fatto_gold
        self.file_sorgente = file_sorgente

    def __repr__(self):
        return (f"[{self.categoria}.{self.sottotipo}/{self.gravita}] "
                f"{self.descrizione}")


# ============================================================================
#  A. SYNTACTIC ANALYSIS (on raw text, disconnected from Gold Standard)
# ============================================================================

# Expected arity for each predicate
_ARITY_ATTESE = {
    "intent": 4,
    "target": 2,
    "vnf": 3,
    "vnfXUser": 4,
}


def check_syntax_errors(raw_text, file_sorgente=""):
    """
    Analyzes the raw text of the LLM file for Prolog syntax errors.
    Every non-empty, non-comment line that doesn't respect the Prolog format
    is reported as a category A / SYNTAX error.

    Returns a list of category A ErrorEntry.
    """
    errori = []
    lines = raw_text.strip().split("\n")

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Ignore Prolog comments
        if line_stripped.startswith("%"):
            continue

        # Missing final dot
        if not line_stripped.endswith("."):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SYNTAX", gravita="Alta",
                descrizione=f"Line {i}: missing final dot → '{line_stripped}'",
                fatto_llm=line_stripped, file_sorgente=file_sorgente
            ))

        # Unbalanced parentheses
        content = line_stripped.rstrip(".")
        if content.count("(") != content.count(")"):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SYNTAX", gravita="Alta",
                descrizione=f"Line {i}: unbalanced round parentheses → '{line_stripped}'",
                fatto_llm=line_stripped, file_sorgente=file_sorgente
            ))
        if content.count("[") != content.count("]"):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SYNTAX", gravita="Alta",
                descrizione=f"Line {i}: unbalanced square parentheses → '{line_stripped}'",
                fatto_llm=line_stripped, file_sorgente=file_sorgente
            ))

        # Arity mismatch
        match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)\s*\.\s*$', line_stripped)
        if match:
            predicato = match.group(1)
            args = _parse_args(match.group(2))
            num_args = len(args)

            if predicato == "propertyExpectation":
                if num_args not in (6, 9):
                    errori.append(ErrorEntry(
                        categoria="A", sottotipo="SYNTAX", gravita="Alta",
                        descrizione=(f"Line {i}: propertyExpectation has {num_args} "
                                     f"parameters (expected 6 or 9) → '{line_stripped}'"),
                        fatto_llm=line_stripped, file_sorgente=file_sorgente
                    ))
            elif predicato in _ARITY_ATTESE:
                expected = _ARITY_ATTESE[predicato]
                if num_args != expected:
                    errori.append(ErrorEntry(
                        categoria="A", sottotipo="SYNTAX", gravita="Alta",
                        descrizione=(f"Line {i}: {predicato} has {num_args} "
                                     f"parameters (expected {expected}) → '{line_stripped}'"),
                        fatto_llm=line_stripped, file_sorgente=file_sorgente
                    ))

    return errori



# ============================================================================
#  MATCHING AND CLASSIFICATION (Cat. B values, Cat. C vnf, Cat. D ins/rem)
# ============================================================================
def _parse_args(args_str):
    """
    Parses the arguments string of a Prolog fact,
    correctly handling lists [...] and tuples (...).
    Returns a list of strings (one element per parameter).
    """
    args = []
    bracket_level = 0
    paren_level = 0
    current_arg = ""

    for char in args_str:
        if char == "[":
            bracket_level += 1
            current_arg += char
        elif char == "]":
            bracket_level -= 1
            current_arg += char
        elif char == "(":
            paren_level += 1
            current_arg += char
        elif char == ")":
            paren_level -= 1
            current_arg += char
        elif char == "," and bracket_level == 0 and paren_level == 0:
            args.append(current_arg.strip())
            current_arg = ""
        else:
            current_arg += char

    if current_arg.strip():
        args.append(current_arg.strip())

    return args


def _parse_fact(fact_str):
    """
    Parses a normalized fact (without arbitrary IDs) in the format
    'predicate(arg1, arg2, ...)' returning (predicate, [arg1, arg2, ...]).
    """
    match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', fact_str)
    if not match:
        return fact_str, []
    return match.group(1), _parse_args(match.group(2))


def _parse_raw_fact(line):
    """
    Parses a raw Prolog fact (with final dot) returning
    (predicate, [arg1, arg2, ...]) or (None, []) if malformed.
    """
    line = line.strip().rstrip(".")
    match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', line)
    if not match:
        return None, []
    return match.group(1), _parse_args(match.group(2))


def classify_parameter_diff(predicato, param_index, val_llm, val_gold,
                            args_llm, args_gold, fatto_llm_str, fatto_gold_str,
                            file_sorgente=""):
    """
    Given a parameter that differs between LLM and Gold, determines the category
    and subtype of the error.

    The logic depends on the predicate and the position of the parameter:

    For NORMALIZED propertyExpectation (without first 2 IDs):
      - Non-changing parameters (7 args): Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF
        index:                             0      1         2        3     4       5          6
      - Changing parameters (4 args):      Type, _, Source, Dest
        index:                             0    1    2      3

    For NORMALIZED intent (without starting and ending ID):
      - args: ProviderOp, NumUsers
        index:    0           1

    For NORMALIZED target:
      - args: [vnf list]
        index:   0

    For vnf / vnfXUser: not normalized, all parameters visible.
    """
    # ---------- propertyExpectation ----------
    if predicato == "propertyExpectation":
        num_args = len(args_gold)  # use gold as reference

        if num_args == 7:
            # Non-changing: Type(0), Operator(1), hard/soft(2), Value(3), Unit(4), SrcVNF(5), DstVNF(6)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "Alta", \
                    f"Wrong type: '{val_llm}' instead of '{val_gold}'"
            elif param_index == 2 and val_llm in ("hard", "soft") and val_gold in ("hard", "soft"):
                # hard instead of soft → stricter constraint → Low (Bassa)
                # soft instead of hard → looser constraint → High (Alta)
                if val_llm == "hard" and val_gold == "soft":
                    return "B", "HARD_SOFT_MISMATCH", "Bassa", \
                        f"Wrong Hard/Soft: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                else:
                    return "B", "HARD_SOFT_MISMATCH", "Alta", \
                        f"Wrong Hard/Soft: '{val_llm}' instead of '{val_gold}'"
            elif param_index in (1, 2, 3, 4):
                # For param_index==3 (Value) in non-changing properties,
                # check if the error is "benign" (stricter constraint):
                #   - latency: LLM value lower than Gold → Low
                #   - bandwidth: LLM value higher than Gold → Low
                if param_index == 3 and len(args_gold) > 0:
                    tipo = args_gold[0].strip().lower()
                    try:
                        v_llm = float(val_llm)
                        v_gold = float(val_gold)
                        if tipo == "latency" and v_llm < v_gold:
                            return "B", "VALUE_UNIT_MISMATCH", "Bassa", \
                                f"Lower latency: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                        elif tipo == "bandwidth" and v_llm > v_gold:
                            return "B", "VALUE_UNIT_MISMATCH", "Bassa", \
                                f"Higher bandwidth: '{val_llm}' instead of '{val_gold}' (stricter constraint)"
                    except (ValueError, TypeError):
                        pass  # non-numeric values → stays High
                return "B", "VALUE_UNIT_MISMATCH", "Alta", \
                    f"Wrong Value/Unit (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"
            elif param_index in (5, 6):
                # In 9-parameter properties, Source and Dest are always
                # interchangeable (VNF link constraints or affinity):
                # a pure swap DOES NOT constitute an error.
                other_idx = 6 if param_index == 5 else 5
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return None  # Source/Dest swap accepted: no error
                return "C", "TOPOLOGY_ERROR", "Alta", \
                    f"Wrong VNF (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"

        elif num_args == 4:
            # Changing: Type(0), _(1), Source(2), Dest(3)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "Alta", \
                    f"Wrong Type: '{val_llm}' instead of '{val_gold}'"
            elif param_index == 1:
                return "B", "VALUE_UNIT_MISMATCH", "Alta", \
                    f"Wrong 4th parameter placeholder: '{val_llm}' instead of '{val_gold}'"
            elif param_index in (2, 3):
                # Check if it's a Source↔Dest swap
                other_idx = 3 if param_index == 2 else 2
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return "C", "SOURCE_DEST_SWAP", "Alta", \
                        f"Source/Dest swapped: LLM has ({args_llm[2]},{args_llm[3]}) instead of ({args_gold[2]},{args_gold[3]})"
                return "C", "TOPOLOGY_ERROR", "Alta", \
                    f"Wrong VNF (param {param_index+1}): '{val_llm}' instead of '{val_gold}'"

        # Fallback for unexpected arity (but still matched)
        return "B", "VALUE_UNIT_MISMATCH", "Alta", \
            f"Wrong parameter {param_index+1}: '{val_llm}' instead of '{val_gold}'"

    # ---------- intent ----------
    if predicato == "intent":
        # Normalized: ProviderOp(0), NumUsers(1)
        if param_index == 0:
            return "B", "VALUE_UNIT_MISMATCH", "Alta", \
                f"Wrong ProviderOp: '{val_llm}' instead of '{val_gold}'"
        elif param_index == 1:
            return "B", "VALUE_UNIT_MISMATCH", "Alta", \
                f"Wrong NumUsers: '{val_llm}' instead of '{val_gold}'"
        return "B", "VALUE_UNIT_MISMATCH", "Alta", \
            f"Wrong intent parameter: '{val_llm}' instead of '{val_gold}'"

    # ---------- target ----------
    if predicato == "target":
        return "C", "WRONG_TARGET_CHAIN", "Alta", \
            f"Wrong Target chain: '{val_llm}' instead of '{val_gold}'"

    # ---------- vnf / vnfXUser ----------
    if predicato in ("vnf", "vnfXUser"):
        # vnf: VnfID(0), edge/cloud(1), HW(2)
        # vnfXUser: VnfID(0), l(1), (1,N)(2), HW(3)
        if param_index == 0:
            return "C", "TOPOLOGY_ERROR", "Alta", \
                f"Wrong VnfID: '{val_llm}' instead of '{val_gold}'"
        elif predicato == "vnf" and param_index == 1:
            return "C", "WRONG_ASSIGNMENT", "Alta", \
                f"Wrong placement: '{val_llm}' instead of '{val_gold}'"
        elif predicato == "vnf" and param_index == 2:
            return "C", "WRONG_ASSIGNMENT", "Alta", \
                f"Wrong Hardware: '{val_llm}' instead of '{val_gold}'"
        elif predicato == "vnfXUser":
            return "C", "WRONG_ASSIGNMENT", "Alta", \
                f"Wrong vnfXUser parameter (pos {param_index+1}): '{val_llm}' instead of '{val_gold}'"

    # Generic fallback
    return "B", "VALUE_UNIT_MISMATCH", "Alta", \
        f"Wrong parameter {param_index+1}: '{val_llm}' instead of '{val_gold}'"


def match_and_classify(set_ideale, set_llm, file_sorgente=""):
    """
    Set logic: computes leftovers, pairs facts by predicate + best-match,
    classifies every differing parameter in categories B/C, and unpaired facts
    in category D.

    Returns a list of ErrorEntry.
    """
    errori = []

    # Facts in common → no error
    # Leftovers
    leftovers_gs = set_ideale - set_llm       # Gold facts missing in LLM
    leftovers_llm = set_llm - set_ideale      # Extra LLM facts (not in gold)

    if not leftovers_gs and not leftovers_llm:
        return errori  # perfect match

    # -------------------------------------------------------------------
    #  PHASE 1: Pairing by predicate + best-match
    # -------------------------------------------------------------------
    matched_gs = set()
    matched_llm = set()

    for llm_fact in sorted(leftovers_llm):
        llm_pred, llm_args = _parse_fact(llm_fact)

        best_match = None
        best_score = -1
        best_diffs = []

        for gs_fact in sorted(leftovers_gs):
            if gs_fact in matched_gs:
                continue

            gs_pred, gs_args = _parse_fact(gs_fact)

            # They must have the same predicate to be paired
            if llm_pred != gs_pred:
                continue

            # Compute similarity score (number of identical parameters)
            max_len = max(len(llm_args), len(gs_args))
            if max_len == 0:
                continue

            score = 0
            diffs = []
            for idx in range(max_len):
                val_llm = llm_args[idx] if idx < len(llm_args) else "<missing>"
                val_gs = gs_args[idx] if idx < len(gs_args) else "<missing>"
                if val_llm == val_gs:
                    score += 1
                else:
                    diffs.append((idx, val_llm, val_gs))

            if score > best_score:
                best_score = score
                best_match = gs_fact
                best_diffs = diffs

        # If a match is found, classify the parameter differences
        if best_match is not None and best_score > 0:
            matched_gs.add(best_match)
            matched_llm.add(llm_fact)

            gs_pred, gs_args = _parse_fact(best_match)
            for (idx, val_llm, val_gs) in best_diffs:
                result = classify_parameter_diff(
                    llm_pred, idx, val_llm, val_gs,
                    llm_args, gs_args,
                    llm_fact, best_match, file_sorgente
                )
                if result is None:
                    continue
                cat, sottotipo, gravita, desc = result
                errori.append(ErrorEntry(
                    categoria=cat,
                    sottotipo=sottotipo,
                    gravita=gravita,
                    descrizione=desc,
                    fatto_llm=llm_fact,
                    fatto_gold=best_match,
                    file_sorgente=file_sorgente
                ))

    # -------------------------------------------------------------------
    #  PHASE 2: Unpaired facts → Insertions (D) and Removals (D)
    # -------------------------------------------------------------------
    # Insertions: facts in LLM without correspondent in gold
    for llm_fact in sorted(leftovers_llm - matched_llm):
        errori.append(ErrorEntry(
            categoria="D",
            sottotipo="INSERTION",
            gravita="Alta",
            descrizione=f"Extra fact generated by LLM (False Positive): '{llm_fact}'",
            fatto_llm=llm_fact,
            fatto_gold="",
            file_sorgente=file_sorgente
        ))

    # Removals: gold facts not generated by LLM
    for gs_fact in sorted(leftovers_gs - matched_gs):
        errori.append(ErrorEntry(
            categoria="D",
            sottotipo="REMOVAL",
            gravita="Alta",
            descrizione=f"Gold fact not generated by LLM (False Negative): '{gs_fact}'",
            fatto_llm="",
            fatto_gold=gs_fact,
            file_sorgente=file_sorgente
        ))

    return errori


# ============================================================================
#  COMPLETE ANALYSIS OF A SINGLE FILE
# ============================================================================
def analizza_file(file_llm_path, file_gold_path):
    """
    Complete analysis of a single LLM file vs Gold Standard.

    Pass 1: Syntax analysis on raw text (Cat. A)
    Pass 2: Normalized set comparison (Cat. B.values + C + D)

    Returns a list of ErrorEntry.
    """
    file_label = os.path.basename(file_llm_path)

    # Read the raw LLM text
    try:
        with open(file_llm_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        return [ErrorEntry("A", "FILE_NOT_FOUND", "Alta",
                           f"LLM File not found: {file_llm_path}",
                           file_sorgente=file_label)]

    # ----- PASS 1: syntactic errors -----
    errori = check_syntax_errors(raw_text, file_sorgente=file_label)

    # ----- PASS 2: normalized set comparison -----
    set_ideale = metrics.estrai_set_da_pl(file_gold_path)
    set_llm = metrics.estrai_set_da_pl(file_llm_path)

    errori += match_and_classify(set_ideale, set_llm, file_sorgente=file_label)

    return errori


# ============================================================================
#  DISCOVERY AND MAIN LOOP
# ============================================================================
def trova_file_output(dir_path):
    """
    Searches for all LLM output files in a directory.
    Detects two naming patterns:
    - 'output_contextN_intentX.txt' (Qwen folders)
    - 'contextN_intentX.txt' (Gemini folders)

    Returns a list of tuples (file_path, context_name, intent_letter).
    """
    risultati = []

    try:
        files = os.listdir(dir_path)
    except OSError:
        return risultati

    for f in sorted(files):
        if not f.endswith(".txt"):
            continue
        # Skip report files that have already been generated
        if f.startswith("report"):
            continue

        # Pattern 1: output_context10_intentA.txt (Qwen)
        match = re.match(r'output_(context\d+)_intent([A-Za-z]+)\.txt', f)
        if match:
            risultati.append((
                os.path.join(dir_path, f),
                match.group(1),
                match.group(2)
            ))
            continue

        # Pattern 2: context10_intentA.txt (Gemini)
        match = re.match(r'(context\d+)_intent([A-Za-z]+)\.txt', f)
        if match:
            risultati.append((
                os.path.join(dir_path, f),
                match.group(1),
                match.group(2)
            ))

    return risultati


# List of categories and names (used everywhere in reports)
CATEGORIE_ORDINATE = ["A", "B", "C", "D"]
NOMI_CATEGORIE = {
    "A": "A. SYNTAX",
    "B": "B. WRONG VALUES",
    "C": "C. WRONG VNFs",
    "D": "D. INSERTIONS/REMOVALS"
}


def genera_report(tutti_errori_per_modello, output_path):
    """
    Generates the summary report with error frequency and severity,
    aggregated by model and by category.

    tutti_errori_per_modello: dict { "model_name": [ErrorEntry, ...] }
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("LLM ERROR CATALOG — SUMMARY REPORT\n")
        f.write("=" * 80 + "\n\n")

        # ---- GLOBAL AGGREGATE ----
        tutti_errori = []
        for errs in tutti_errori_per_modello.values():
            tutti_errori.extend(errs)

        _scrivi_sezione_report(f, "GLOBAL AGGREGATE", tutti_errori)

        # ---- PER MODEL ----
        for modello, errori in sorted(tutti_errori_per_modello.items()):
            f.write("\n" + "=" * 80 + "\n")
            _scrivi_sezione_report(f, f"MODEL: {modello}", errori)

    print(f"\n=> Error catalog report saved at: {output_path}")


def genera_report_singolo(nome_modello, errori_per_file, output_path):
    """
    Generates a detailed report for a single model/test.

    errori_per_file: dict { "file_name": [ErrorEntry, ...] }
                     Includes files with 0 errors (empty list) as well.
    output_path: path to the report file to be created.
    """
    tutti_errori = []
    for errs in errori_per_file.values():
        tutti_errori.extend(errs)

    file_con_errori = {f: errs for f, errs in errori_per_file.items() if errs}
    file_senza_errori = [f for f, errs in errori_per_file.items() if not errs]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"ERROR CATALOG — {nome_modello}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Analyzed files:     {len(errori_per_file)}\n")
        f.write(f"Files with errors:  {len(file_con_errori)}\n")
        f.write(f"Files without errors: {len(file_senza_errori)}\n")
        f.write(f"Total errors:       {len(tutti_errori)}\n\n")

        # ---- SUMMARY OF FILES WITH ERRORS ----
        f.write("-" * 80 + "\n")
        f.write("SUMMARY OF FILES WITH ERRORS\n")
        f.write("-" * 80 + "\n\n")

        file_solo_low = []

        if file_con_errori:
            for nome_file in sorted(file_con_errori.keys()):
                errs = file_con_errori[nome_file]
                alta = sum(1 for e in errs if e.gravita == "Alta")
                bassa = sum(1 for e in errs if e.gravita == "Bassa")
                
                if alta == 0 and bassa > 0:
                    file_solo_low.append(nome_file)

                conteggio = {cat: 0 for cat in CATEGORIE_ORDINATE}
                for e in errs:
                    conteggio[e.categoria] = conteggio.get(e.categoria, 0) + 1
                parti_cat = ", ".join(
                    f"{cat}={conteggio.get(cat, 0)}" for cat in CATEGORIE_ORDINATE
                )

                f.write(f"  {nome_file:45s} : {len(errs):3d} errors (High={alta}, Low={bassa}) ({parti_cat})\n")
        else:
            f.write("  No files with errors!\n")
        f.write("\n")

        # ---- FILES WITH ONLY LOW ERRORS ----
        f.write("-" * 80 + "\n")
        f.write("FILES WITH ONLY LOW ERRORS\n")
        f.write("-" * 80 + "\n\n")

        if file_solo_low:
            for nome_file in sorted(file_solo_low):
                f.write(f"  ✓ {nome_file}\n")
        else:
            f.write("  No files with only low errors.\n")
        f.write("\n")

        # ---- AGGREGATED STATISTICS ----
        f.write("-" * 80 + "\n")
        f.write("AGGREGATED STATISTICS\n")
        f.write("-" * 80 + "\n")
        _scrivi_sezione_report(f, nome_modello, tutti_errori)

        # ---- ERROR DETAIL PER FILE ----
        f.write("\n" + "-" * 80 + "\n")
        f.write("ERROR DETAIL PER FILE\n")
        f.write("-" * 80 + "\n\n")

        for nome_file in sorted(file_con_errori.keys()):
            errs = file_con_errori[nome_file]
            f.write(f"  [{nome_file}] — {len(errs)} errors\n")
            for e in errs:
                f.write(f"    [{e.categoria}.{e.sottotipo}/{e.gravita}] {e.descrizione}\n")
            f.write("\n")

    print(f"  => Single report saved at: {output_path}")


def _scrivi_sezione_report(f, titolo, errori):
    """
    Writes a section of the report for a given set of errors.
    Includes: counts by category, subtype, severity, and top examples.
    """
    f.write(f"\n--- {titolo} ---\n")
    f.write(f"Total cataloged errors: {len(errori)}\n\n")

    if not errori:
        f.write("No errors found.\n")
        return

    # Count by CATEGORY
    conteggio_cat = defaultdict(int)
    for e in errori:
        conteggio_cat[e.categoria] += 1

    f.write("  FREQUENCY BY CATEGORY:\n")
    for cat in CATEGORIE_ORDINATE:
        count = conteggio_cat.get(cat, 0)
        pct = (count / len(errori) * 100) if errori else 0
        f.write(f"    {NOMI_CATEGORIE.get(cat, cat):30s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Count by SUBTYPE
    conteggio_sottotipo = defaultdict(int)
    for e in errori:
        chiave = f"{e.categoria}.{e.sottotipo}"
        conteggio_sottotipo[chiave] += 1

    f.write("  FREQUENCY BY SUBTYPE:\n")
    for chiave, count in sorted(conteggio_sottotipo.items(),
                                 key=lambda x: -x[1]):
        pct = (count / len(errori) * 100) if errori else 0
        f.write(f"    {chiave:40s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Count by SEVERITY
    alta = sum(1 for e in errori if e.gravita == "Alta")
    bassa = sum(1 for e in errori if e.gravita == "Bassa")
    f.write("  SEVERITY DISTRIBUTION:\n")
    f.write(f"    {'High (modifies network intent)':40s} : {alta:5d}  ({alta/len(errori)*100:5.1f}%)\n")
    f.write(f"    {'Low (fixable in post-processing)':40s} : {bassa:5d}  ({bassa/len(errori)*100:5.1f}%)\n")
    f.write("\n")

    # Count by SEVERITY per CATEGORY
    f.write("  SEVERITY PER CATEGORY:\n")
    for cat in CATEGORIE_ORDINATE:
        cat_errs = [e for e in errori if e.categoria == cat]
        if not cat_errs:
            continue
        alta_cat = sum(1 for e in cat_errs if e.gravita == "Alta")
        bassa_cat = sum(1 for e in cat_errs if e.gravita == "Bassa")
        f.write(f"    {NOMI_CATEGORIE.get(cat, cat):30s} : High={alta_cat:4d}, Low={bassa_cat:4d}\n")
    f.write("\n")




def main():
    """
    Entry point: traverses all folders in the workspace, detects LLM
    output files, compares them with gold standards, and generates the report.
    It also generates single reports for each model in a dedicated folder.
    """
    print("=" * 60)
    print("=== LLM ERROR CATALOG — Starting analysis ===")
    print("=" * 60)

    tutti_errori_per_modello = {}
    # Map: model_name → { file_name: [ErrorEntry, ...] }
    errori_per_file_per_modello = {}
    # Map: model_name → model directory (for info)
    dir_per_modello = {}
    file_analizzati = 0

    # Traverse all subfolders looking for output files
    for root, dirs, files in os.walk(BASE_DIR):
        # Skip gold standard folder, __pycache__, .git and reports_catalogo
        basename = os.path.basename(root)
        if basename in ("intent", "__pycache__", ".git", "reports_catalogo", "dips"):
            dirs.clear()  # do not descend into subfolders
            continue

        file_output = trova_file_output(root)
        if not file_output:
            continue

        # Determine the model name from the folder structure
        # e.g. "3-shot/.../Qwen2.5-14b" → "3-shot/Qwen2.5-14b"
        rel_path = os.path.relpath(root, BASE_DIR)
        parti = rel_path.replace("\\", "/").split("/")
        # Try to extract a meaningful name
        nome_modello = "/".join(p for p in parti
                                if not p.endswith("-001") and p != ".")
        if not nome_modello:
            nome_modello = rel_path

        print(f"\nAnalysis: {nome_modello} ({len(file_output)} files)")

        errori_modello = []
        errori_per_file = {}  # for the single report

        for file_path, context_name, intent_letter in file_output:
            # Find the corresponding gold standard
            gold_path = os.path.join(CARTELLA_INTENTI_IDEALI,
                                     context_name, "facts.pl")
            if not os.path.exists(gold_path):
                print(f"  ⚠ Gold standard not found for {context_name}")
                continue

            nome_file = os.path.basename(file_path)
            errori = analizza_file(file_path, gold_path)
            errori_modello.extend(errori)
            errori_per_file[nome_file] = errori
            file_analizzati += 1

        # Summary by model
        if errori_modello:
            conteggi = {cat: sum(1 for e in errori_modello if e.categoria == cat)
                        for cat in CATEGORIE_ORDINATE}
            parti_str = ", ".join(f"{cat}={conteggi[cat]}" for cat in CATEGORIE_ORDINATE)
            print(f"  Total errors: {len(errori_modello)} ({parti_str})")

        tutti_errori_per_modello[nome_modello] = errori_modello
        errori_per_file_per_modello[nome_modello] = errori_per_file
        dir_per_modello[nome_modello] = root

    # ---- Generate the global report ----
    print(f"\n{'=' * 60}")
    print(f"Analyzed files: {file_analizzati}")

    report_path = os.path.join(BASE_DIR, "report_catalogo_errori.txt")
    genera_report(tutti_errori_per_modello, report_path)

    # ---- Generate single reports in the dedicated folder ----
    cartella_reports = os.path.join(BASE_DIR, "reports_catalogo")
    os.makedirs(cartella_reports, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Generating single reports in: {cartella_reports}")

    for nome_modello in sorted(errori_per_file_per_modello.keys()):
        errori_per_file = errori_per_file_per_modello[nome_modello]
        # Create a valid file name from the model name
        # e.g. "3-shot/Qwen2.5-3b" → "3-shot_Qwen2.5-3b"
        nome_file_report = nome_modello.replace("/", "_").replace("\\", "_")
        report_singolo_path = os.path.join(
            cartella_reports, f"report_{nome_file_report}.txt"
        )
        genera_report_singolo(nome_modello, errori_per_file, report_singolo_path)

    print(f"\n{'=' * 60}")
    print("Processing completed!")


# ============================================================================
if __name__ == "__main__":
    main()
