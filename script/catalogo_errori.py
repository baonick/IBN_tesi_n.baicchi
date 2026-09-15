"""
catalogo_errori.py — Catalogazione degli errori LLM su fatti Prolog IBN
========================================================================

Classifica ogni differenza tra Gold Standard e Predizione LLM in 4 categorie:
    A. SINTASSI     — errori strutturali (punti, parentesi, arity)        → Alta
    B. VALORI ERRATI — type/valore-unità/hard-soft mismatch               → Alta
       Eccezioni Bassa: hard→soft (vincolo più rigido),
                        latenza inferiore o banda superiore (vincolo più stretto)
    C. VNF ERRATE    — topologia, target chain, assegnazione edge/cloud   → Alta
    D. INSERZIONI/RIMOZIONI — fatti extra o mancanti (FP / FN)            → Alta

Percorre automaticamente tutte le cartelle di output nel workspace, rileva
i file predizione (pattern 'output_context*' e 'context*_intent*'), li
accoppia al gold standard in intent/ e produce un report riassuntivo.

Utilizza la stessa logica a insiemi di esegui_valutazione_tutti_schemi.py
e MetricExecuterInputDips.py per l'estrazione e normalizzazione dei fatti.
"""

import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
#  Importa il modulo metriche esistente
# ---------------------------------------------------------------------------
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import MetricExecuterInputDips as metrics  # noqa: E402

# ---------------------------------------------------------------------------
#  CONFIGURAZIONE
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)  # radice del progetto (IBN github/)
CARTELLA_INTENTI_IDEALI = os.path.join(BASE_DIR, "intent")




# ============================================================================
#  STRUTTURA PER ACCUMULARE ERRORI
# ============================================================================
class ErrorEntry:
    """Singola segnalazione di errore catalogato."""
    def __init__(self, categoria, sottotipo, gravita, descrizione,
                 fatto_llm="", fatto_gold="", file_sorgente=""):
        self.categoria = categoria       # "A", "B", "C", "D"
        self.sottotipo = sottotipo       # es. "PARENTESI_SBILANCIATE"
        self.gravita = gravita           # "Alta" o "Bassa"
        self.descrizione = descrizione   # stringa human-readable
        self.fatto_llm = fatto_llm
        self.fatto_gold = fatto_gold
        self.file_sorgente = file_sorgente

    def __repr__(self):
        return (f"[{self.categoria}.{self.sottotipo}/{self.gravita}] "
                f"{self.descrizione}")


# ============================================================================
#  A. ANALISI SINTATTICA (sul testo raw, scollegata dal Gold Standard)
# ============================================================================

# Arity attese per ogni predicato
_ARITY_ATTESE = {
    "intent": 4,
    "target": 2,
    "vnf": 3,
    "vnfXUser": 4,
}


def check_syntax_errors(raw_text, file_sorgente=""):
    """
    Analizza il testo raw del file LLM per errori sintattici Prolog.
    Ogni riga non vuota e non-commento che non rispetta il formato Prolog
    viene segnalata come errore di categoria A / SINTASSI.

    Restituisce una lista di ErrorEntry di categoria A.
    """
    errori = []
    lines = raw_text.strip().split("\n")

    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue

        # Ignora commenti Prolog
        if line_stripped.startswith("%"):
            continue

        # Punto finale mancante
        if not line_stripped.endswith("."):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SINTASSI", gravita="Alta",
                descrizione=f"Riga {i}: manca il punto finale → '{line_stripped}'",
                fatto_llm=line_stripped, file_sorgente=file_sorgente
            ))

        # Parentesi sbilanciate
        content = line_stripped.rstrip(".")
        if content.count("(") != content.count(")"):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SINTASSI", gravita="Alta",
                descrizione=f"Riga {i}: parentesi tonde sbilanciate → '{line_stripped}'",
                fatto_llm=line_stripped, file_sorgente=file_sorgente
            ))
        if content.count("[") != content.count("]"):
            errori.append(ErrorEntry(
                categoria="A", sottotipo="SINTASSI", gravita="Alta",
                descrizione=f"Riga {i}: parentesi quadre sbilanciate → '{line_stripped}'",
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
                        categoria="A", sottotipo="SINTASSI", gravita="Alta",
                        descrizione=(f"Riga {i}: propertyExpectation ha {num_args} "
                                     f"parametri (attesi 6 o 9) → '{line_stripped}'"),
                        fatto_llm=line_stripped, file_sorgente=file_sorgente
                    ))
            elif predicato in _ARITY_ATTESE:
                expected = _ARITY_ATTESE[predicato]
                if num_args != expected:
                    errori.append(ErrorEntry(
                        categoria="A", sottotipo="SINTASSI", gravita="Alta",
                        descrizione=(f"Riga {i}: {predicato} ha {num_args} "
                                     f"parametri (attesi {expected}) → '{line_stripped}'"),
                        fatto_llm=line_stripped, file_sorgente=file_sorgente
                    ))

    return errori



# ============================================================================
#  MATCHING E CLASSIFICAZIONE (Cat. B valori, Cat. C vnf, Cat. D ins/rim)
# ============================================================================
def _parse_args(args_str):
    """
    Parsa la stringa degli argomenti di un fatto Prolog,
    gestendo correttamente le liste [...] e le tuple (...).
    Restituisce una lista di stringhe (un elemento per parametro).
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
    Parsa un fatto normalizzato (senza ID arbitrari) nel formato
    'predicato(arg1, arg2, ...)' restituendo (predicato, [arg1, arg2, ...]).
    """
    match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', fact_str)
    if not match:
        return fact_str, []
    return match.group(1), _parse_args(match.group(2))


def _parse_raw_fact(line):
    """
    Parsa un fatto Prolog raw (con punto finale) restituendo
    (predicato, [arg1, arg2, ...]) oppure (None, []) se malformato.
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
    Dato un parametro che differisce tra LLM e Gold, determina la categoria
    e il sottotipo dell'errore.

    La logica dipende dal predicato e dalla posizione del parametro:

    Per propertyExpectation NORMALIZZATO (senza i primi 2 ID):
      - Parametri non-changing (7 args): Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF
        index:                             0      1         2        3     4       5          6
      - Parametri changing (4 args):      Type, _, Source, Dest
        index:                             0    1    2      3

    Per intent NORMALIZZATO (senza ID iniziale e finale):
      - args: ProviderOp, NumUsers
        index:    0           1

    Per target NORMALIZZATO:
      - args: [lista vnf]
        index:   0

    Per vnf / vnfXUser: non normalizzati, tutti i parametri visibili.
    """
    # ---------- propertyExpectation ----------
    if predicato == "propertyExpectation":
        num_args = len(args_gold)  # usiamo il gold come riferimento

        if num_args == 7:
            # Non-changing: Type(0), Operator(1), hard/soft(2), Value(3), Unit(4), SrcVNF(5), DstVNF(6)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "Alta", \
                    f"Type errato: '{val_llm}' invece di '{val_gold}'"
            elif param_index == 2 and val_llm in ("hard", "soft") and val_gold in ("hard", "soft"):
                # hard al posto di soft → vincolo più rigido → Bassa
                # soft al posto di hard → vincolo più lasco → Alta
                if val_llm == "hard" and val_gold == "soft":
                    return "B", "HARD_SOFT_MISMATCH", "Bassa", \
                        f"Hard/Soft errato: '{val_llm}' invece di '{val_gold}' (vincolo più rigido)"
                else:
                    return "B", "HARD_SOFT_MISMATCH", "Alta", \
                        f"Hard/Soft errato: '{val_llm}' invece di '{val_gold}'"
            elif param_index in (1, 2, 3, 4):
                # Per param_index==3 (Value) nelle property non-changing,
                # controlla se l'errore è "benigno" (vincolo più stretto):
                #   - latency: valore LLM inferiore al Gold → Bassa
                #   - bandwidth: valore LLM superiore al Gold → Bassa
                if param_index == 3 and len(args_gold) > 0:
                    tipo = args_gold[0].strip().lower()
                    try:
                        v_llm = float(val_llm)
                        v_gold = float(val_gold)
                        if tipo == "latency" and v_llm < v_gold:
                            return "B", "VALORE_UNITA_MISMATCH", "Bassa", \
                                f"Latenza più bassa: '{val_llm}' invece di '{val_gold}' (vincolo più stretto)"
                        elif tipo == "bandwidth" and v_llm > v_gold:
                            return "B", "VALORE_UNITA_MISMATCH", "Bassa", \
                                f"Banda più alta: '{val_llm}' invece di '{val_gold}' (vincolo più stretto)"
                    except (ValueError, TypeError):
                        pass  # valori non numerici → resta Alta
                return "B", "VALORE_UNITA_MISMATCH", "Alta", \
                    f"Valore/Unità errato (param {param_index+1}): '{val_llm}' invece di '{val_gold}'"
            elif param_index in (5, 6):
                # Nelle property da 9 parametri Source e Dest sono sempre
                # intercambiabili (vincoli di collegamento VNF o affinity):
                # uno swap puro NON costituisce errore.
                other_idx = 6 if param_index == 5 else 5
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return None  # swap Source/Dest accettato: nessun errore
                return "C", "ERRORE_TOPOLOGICO", "Alta", \
                    f"VNF errata (param {param_index+1}): '{val_llm}' invece di '{val_gold}'"

        elif num_args == 4:
            # Changing: Type(0), _(1), Source(2), Dest(3)
            if param_index == 0:
                return "B", "TYPE_MISMATCH", "Alta", \
                    f"Type errato: '{val_llm}' invece di '{val_gold}'"
            elif param_index == 1:
                return "B", "VALORE_UNITA_MISMATCH", "Alta", \
                    f"Placeholder 4° parametro errato: '{val_llm}' invece di '{val_gold}'"
            elif param_index in (2, 3):
                # Controlla se è uno swap Source↔Dest
                other_idx = 3 if param_index == 2 else 2
                val_llm_other = args_llm[other_idx] if other_idx < len(args_llm) else ""
                val_gold_other = args_gold[other_idx] if other_idx < len(args_gold) else ""
                if val_llm == val_gold_other and val_llm_other == val_gold:
                    return "C", "SOURCE_DEST_SWAP", "Alta", \
                        f"Source/Dest invertiti: LLM ha ({args_llm[2]},{args_llm[3]}) invece di ({args_gold[2]},{args_gold[3]})"
                return "C", "ERRORE_TOPOLOGICO", "Alta", \
                    f"VNF errata (param {param_index+1}): '{val_llm}' invece di '{val_gold}'"

        # Fallback per arity inattesa (ma comunque matchata)
        return "B", "VALORE_UNITA_MISMATCH", "Alta", \
            f"Parametro {param_index+1} errato: '{val_llm}' invece di '{val_gold}'"

    # ---------- intent ----------
    if predicato == "intent":
        # Normalizzato: ProviderOp(0), NumUsers(1)
        if param_index == 0:
            return "B", "VALORE_UNITA_MISMATCH", "Alta", \
                f"ProviderOp errato: '{val_llm}' invece di '{val_gold}'"
        elif param_index == 1:
            return "B", "VALORE_UNITA_MISMATCH", "Alta", \
                f"NumUsers errato: '{val_llm}' invece di '{val_gold}'"
        return "B", "VALORE_UNITA_MISMATCH", "Alta", \
            f"Parametro intent errato: '{val_llm}' invece di '{val_gold}'"

    # ---------- target ----------
    if predicato == "target":
        return "C", "TARGET_CHAIN_ERRATA", "Alta", \
            f"Target chain errata: '{val_llm}' invece di '{val_gold}'"

    # ---------- vnf / vnfXUser ----------
    if predicato in ("vnf", "vnfXUser"):
        # vnf: VnfID(0), edge/cloud(1), HW(2)
        # vnfXUser: VnfID(0), l(1), (1,N)(2), HW(3)
        if param_index == 0:
            return "C", "ERRORE_TOPOLOGICO", "Alta", \
                f"VnfID errato: '{val_llm}' invece di '{val_gold}'"
        elif predicato == "vnf" and param_index == 1:
            return "C", "ASSEGNAZIONE_ERRATA", "Alta", \
                f"Posizionamento errato: '{val_llm}' invece di '{val_gold}'"
        elif predicato == "vnf" and param_index == 2:
            return "C", "ASSEGNAZIONE_ERRATA", "Alta", \
                f"Hardware errato: '{val_llm}' invece di '{val_gold}'"
        elif predicato == "vnfXUser":
            return "C", "ASSEGNAZIONE_ERRATA", "Alta", \
                f"Parametro vnfXUser errato (pos {param_index+1}): '{val_llm}' invece di '{val_gold}'"

    # Fallback generico
    return "B", "VALORE_UNITA_MISMATCH", "Alta", \
        f"Parametro {param_index+1} errato: '{val_llm}' invece di '{val_gold}'"


def match_and_classify(set_ideale, set_llm, file_sorgente=""):
    """
    Logica a insiemi: calcola leftovers, accoppia i fatti per predicato + best-match,
    classifica ogni parametro differente nelle categorie B/C, e i fatti non accoppiati
    nella categoria D.

    Restituisce una lista di ErrorEntry.
    """
    errori = []

    # Fatti in comune → nessun errore
    # Leftovers
    leftovers_gs = set_ideale - set_llm       # Fatti gold mancanti nell'LLM
    leftovers_llm = set_llm - set_ideale      # Fatti LLM extra (non nel gold)

    if not leftovers_gs and not leftovers_llm:
        return errori  # perfetto match

    # -------------------------------------------------------------------
    #  FASE 1: Accoppiamento per predicato + best-match
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

            # Devono avere lo stesso predicato per essere accoppiabili
            if llm_pred != gs_pred:
                continue

            # Calcola score di similarità (numero parametri uguali)
            max_len = max(len(llm_args), len(gs_args))
            if max_len == 0:
                continue

            score = 0
            diffs = []
            for idx in range(max_len):
                val_llm = llm_args[idx] if idx < len(llm_args) else "<mancante>"
                val_gs = gs_args[idx] if idx < len(gs_args) else "<mancante>"
                if val_llm == val_gs:
                    score += 1
                else:
                    diffs.append((idx, val_llm, val_gs))

            if score > best_score:
                best_score = score
                best_match = gs_fact
                best_diffs = diffs

        # Se trovato un match, classifica le differenze parametriche
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
    #  FASE 2: Fatti non accoppiati → Inserzioni (D) e Rimozioni (D)
    # -------------------------------------------------------------------
    # Inserzioni: fatti nell'LLM senza corrispondente nel gold
    for llm_fact in sorted(leftovers_llm - matched_llm):
        errori.append(ErrorEntry(
            categoria="D",
            sottotipo="INSERZIONE",
            gravita="Alta",
            descrizione=f"Fatto extra generato dall'LLM (Falso Positivo): '{llm_fact}'",
            fatto_llm=llm_fact,
            fatto_gold="",
            file_sorgente=file_sorgente
        ))

    # Rimozioni: fatti nel gold non generati dall'LLM
    for gs_fact in sorted(leftovers_gs - matched_gs):
        errori.append(ErrorEntry(
            categoria="D",
            sottotipo="RIMOZIONE",
            gravita="Alta",
            descrizione=f"Fatto gold non generato dall'LLM (Falso Negativo): '{gs_fact}'",
            fatto_llm="",
            fatto_gold=gs_fact,
            file_sorgente=file_sorgente
        ))

    return errori


# ============================================================================
#  ANALISI COMPLETA DI UN SINGOLO FILE
# ============================================================================
def analizza_file(file_llm_path, file_gold_path):
    """
    Analisi completa di un singolo file LLM vs Gold Standard.

    Passata 1: Analisi sintattica sul testo raw (Cat. A)
    Passata 2: Confronto a insiemi normalizzato (Cat. B.valori + C + D)

    Restituisce una lista di ErrorEntry.
    """
    file_label = os.path.basename(file_llm_path)

    # Leggi il testo raw dell'LLM
    try:
        with open(file_llm_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
    except FileNotFoundError:
        return [ErrorEntry("A", "FILE_NON_TROVATO", "Alta",
                           f"File LLM non trovato: {file_llm_path}",
                           file_sorgente=file_label)]

    # ----- PASSATA 1: errori sintattici -----
    errori = check_syntax_errors(raw_text, file_sorgente=file_label)

    # ----- PASSATA 2: confronto a insiemi normalizzato -----
    set_ideale = metrics.estrai_set_da_pl(file_gold_path)
    set_llm = metrics.estrai_set_da_pl(file_llm_path)

    errori += match_and_classify(set_ideale, set_llm, file_sorgente=file_label)

    return errori


# ============================================================================
#  DISCOVERY E MAIN LOOP
# ============================================================================
def trova_file_output(dir_path):
    """
    Cerca tutti i file di output LLM in una directory.
    Rileva due pattern di naming:
    - 'output_contextN_intentX.txt' (cartelle Qwen)
    - 'contextN_intentX.txt' (cartelle Gemini)

    Restituisce una lista di tuple (file_path, context_name, intent_letter).
    """
    risultati = []

    try:
        files = os.listdir(dir_path)
    except OSError:
        return risultati

    for f in sorted(files):
        if not f.endswith(".txt"):
            continue
        # Salta i file di report già generati
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


# Lista categorie e nomi (usata ovunque nei report)
CATEGORIE_ORDINATE = ["A", "B", "C", "D"]
NOMI_CATEGORIE = {
    "A": "A. SINTASSI",
    "B": "B. VALORI ERRATI",
    "C": "C. VNF ERRATE",
    "D": "D. INSERZIONI/RIMOZIONI"
}


def genera_report(tutti_errori_per_modello, output_path):
    """
    Genera il report riassuntivo con frequenza e gravità degli errori,
    aggregato per modello e per categoria.

    tutti_errori_per_modello: dict { "nome_modello": [ErrorEntry, ...] }
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("CATALOGO ERRORI LLM — REPORT RIASSUNTIVO\n")
        f.write("=" * 80 + "\n\n")

        # ---- AGGREGATO GLOBALE ----
        tutti_errori = []
        for errs in tutti_errori_per_modello.values():
            tutti_errori.extend(errs)

        _scrivi_sezione_report(f, "AGGREGATO GLOBALE", tutti_errori)

        # ---- PER MODELLO ----
        for modello, errori in sorted(tutti_errori_per_modello.items()):
            f.write("\n" + "=" * 80 + "\n")
            _scrivi_sezione_report(f, f"MODELLO: {modello}", errori)

    print(f"\n=> Report catalogo errori salvato in: {output_path}")


def genera_report_singolo(nome_modello, errori_per_file, output_path):
    """
    Genera un report dettagliato per un singolo modello/test.

    errori_per_file: dict { "nome_file": [ErrorEntry, ...] }
                     Include anche file con 0 errori (lista vuota).
    output_path: percorso del file di report da creare.
    """
    tutti_errori = []
    for errs in errori_per_file.values():
        tutti_errori.extend(errs)

    file_con_errori = {f: errs for f, errs in errori_per_file.items() if errs}
    file_senza_errori = [f for f, errs in errori_per_file.items() if not errs]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write(f"CATALOGO ERRORI — {nome_modello}\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"File analizzati:    {len(errori_per_file)}\n")
        f.write(f"File con errori:    {len(file_con_errori)}\n")
        f.write(f"File senza errori:  {len(file_senza_errori)}\n")
        f.write(f"Totale errori:      {len(tutti_errori)}\n\n")

        # ---- RIEPILOGO FILE CON ERRORI ----
        f.write("-" * 80 + "\n")
        f.write("RIEPILOGO FILE CON ERRORI\n")
        f.write("-" * 80 + "\n\n")

        if file_con_errori:
            for nome_file in sorted(file_con_errori.keys()):
                errs = file_con_errori[nome_file]
                conteggio = {cat: 0 for cat in CATEGORIE_ORDINATE}
                for e in errs:
                    conteggio[e.categoria] = conteggio.get(e.categoria, 0) + 1
                parti_cat = ", ".join(
                    f"{cat}={conteggio.get(cat, 0)}" for cat in CATEGORIE_ORDINATE
                )
                f.write(f"  {nome_file:45s} : {len(errs):3d} errori ({parti_cat})\n")
        else:
            f.write("  Nessun file con errori!\n")
        f.write("\n")

        # ---- FILE SENZA ERRORI ----
        f.write("-" * 80 + "\n")
        f.write("FILE SENZA ERRORI\n")
        f.write("-" * 80 + "\n\n")

        if file_senza_errori:
            for nome_file in sorted(file_senza_errori):
                f.write(f"  ✓ {nome_file}\n")
        else:
            f.write("  Tutti i file contengono errori.\n")
        f.write("\n")

        # ---- STATISTICHE AGGREGATE ----
        f.write("-" * 80 + "\n")
        f.write("STATISTICHE AGGREGATE\n")
        f.write("-" * 80 + "\n")
        _scrivi_sezione_report(f, nome_modello, tutti_errori)

        # ---- DETTAGLIO ERRORI PER FILE ----
        f.write("\n" + "-" * 80 + "\n")
        f.write("DETTAGLIO ERRORI PER FILE\n")
        f.write("-" * 80 + "\n\n")

        for nome_file in sorted(file_con_errori.keys()):
            errs = file_con_errori[nome_file]
            f.write(f"  [{nome_file}] — {len(errs)} errori\n")
            for e in errs:
                f.write(f"    [{e.categoria}.{e.sottotipo}/{e.gravita}] {e.descrizione}\n")
            f.write("\n")

    print(f"  => Report singolo salvato in: {output_path}")


def _scrivi_sezione_report(f, titolo, errori):
    """
    Scrive una sezione del report per un dato insieme di errori.
    Include: conteggi per categoria, sottotipo, gravità, e top esempi.
    """
    f.write(f"\n--- {titolo} ---\n")
    f.write(f"Totale errori catalogati: {len(errori)}\n\n")

    if not errori:
        f.write("Nessun errore trovato.\n")
        return

    # Conteggio per CATEGORIA
    conteggio_cat = defaultdict(int)
    for e in errori:
        conteggio_cat[e.categoria] += 1

    f.write("  FREQUENZA PER CATEGORIA:\n")
    for cat in CATEGORIE_ORDINATE:
        count = conteggio_cat.get(cat, 0)
        pct = (count / len(errori) * 100) if errori else 0
        f.write(f"    {NOMI_CATEGORIE.get(cat, cat):30s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Conteggio per SOTTOTIPO
    conteggio_sottotipo = defaultdict(int)
    for e in errori:
        chiave = f"{e.categoria}.{e.sottotipo}"
        conteggio_sottotipo[chiave] += 1

    f.write("  FREQUENZA PER SOTTOTIPO:\n")
    for chiave, count in sorted(conteggio_sottotipo.items(),
                                 key=lambda x: -x[1]):
        pct = (count / len(errori) * 100) if errori else 0
        f.write(f"    {chiave:40s} : {count:5d}  ({pct:5.1f}%)\n")
    f.write("\n")

    # Conteggio per GRAVITÀ
    alta = sum(1 for e in errori if e.gravita == "Alta")
    bassa = sum(1 for e in errori if e.gravita == "Bassa")
    f.write("  DISTRIBUZIONE GRAVITÀ:\n")
    f.write(f"    {'Alta (modifica intento di rete)':40s} : {alta:5d}  ({alta/len(errori)*100:5.1f}%)\n")
    f.write(f"    {'Bassa (fixabile in post-processing)':40s} : {bassa:5d}  ({bassa/len(errori)*100:5.1f}%)\n")
    f.write("\n")

    # Conteggio per GRAVITÀ per CATEGORIA
    f.write("  GRAVITÀ PER CATEGORIA:\n")
    for cat in CATEGORIE_ORDINATE:
        cat_errs = [e for e in errori if e.categoria == cat]
        if not cat_errs:
            continue
        alta_cat = sum(1 for e in cat_errs if e.gravita == "Alta")
        bassa_cat = sum(1 for e in cat_errs if e.gravita == "Bassa")
        f.write(f"    {NOMI_CATEGORIE.get(cat, cat):30s} : Alta={alta_cat:4d}, Bassa={bassa_cat:4d}\n")
    f.write("\n")




def main():
    """
    Entry point: percorre tutte le cartelle nel workspace, rileva i file
    di output LLM, li confronta con i gold standard, e genera il report.
    Genera anche report singoli per ogni modello in una cartella dedicata.
    """
    print("=" * 60)
    print("=== CATALOGO ERRORI LLM — Avvio analisi ===")
    print("=" * 60)

    tutti_errori_per_modello = {}
    # Mappa: nome_modello → { nome_file: [ErrorEntry, ...] }
    errori_per_file_per_modello = {}
    # Mappa: nome_modello → directory del modello (per info)
    dir_per_modello = {}
    file_analizzati = 0

    # Percorri tutte le sottocartelle cercando file di output
    for root, dirs, files in os.walk(BASE_DIR):
        # Salta la cartella gold standard, __pycache__, .git e reports_catalogo
        basename = os.path.basename(root)
        if basename in ("intent", "__pycache__", ".git", "reports_catalogo", "dips"):
            dirs.clear()  # non scendere nelle sotto-cartelle
            continue

        file_output = trova_file_output(root)
        if not file_output:
            continue

        # Determina il nome del modello dalla struttura della cartella
        # es. "3-shot/.../Qwen2.5-14b" → "3-shot/Qwen2.5-14b"
        rel_path = os.path.relpath(root, BASE_DIR)
        parti = rel_path.replace("\\", "/").split("/")
        # Cerca di estrarre un nome significativo
        nome_modello = "/".join(p for p in parti
                                if not p.endswith("-001") and p != ".")
        if not nome_modello:
            nome_modello = rel_path

        print(f"\nAnalisi: {nome_modello} ({len(file_output)} file)")

        errori_modello = []
        errori_per_file = {}  # per il report singolo

        for file_path, context_name, intent_letter in file_output:
            # Trova il gold standard corrispondente
            gold_path = os.path.join(CARTELLA_INTENTI_IDEALI,
                                     context_name, "facts.pl")
            if not os.path.exists(gold_path):
                print(f"  ⚠ Gold standard non trovato per {context_name}")
                continue

            nome_file = os.path.basename(file_path)
            errori = analizza_file(file_path, gold_path)
            errori_modello.extend(errori)
            errori_per_file[nome_file] = errori
            file_analizzati += 1

        # Sommario per modello
        if errori_modello:
            conteggi = {cat: sum(1 for e in errori_modello if e.categoria == cat)
                        for cat in CATEGORIE_ORDINATE}
            parti_str = ", ".join(f"{cat}={conteggi[cat]}" for cat in CATEGORIE_ORDINATE)
            print(f"  Totale errori: {len(errori_modello)} ({parti_str})")

        tutti_errori_per_modello[nome_modello] = errori_modello
        errori_per_file_per_modello[nome_modello] = errori_per_file
        dir_per_modello[nome_modello] = root

    # ---- Genera il report globale ----
    print(f"\n{'=' * 60}")
    print(f"File analizzati: {file_analizzati}")

    report_path = os.path.join(BASE_DIR, "report_catalogo_errori.txt")
    genera_report(tutti_errori_per_modello, report_path)

    # ---- Genera report singoli nella cartella dedicata ----
    cartella_reports = os.path.join(BASE_DIR, "reports_catalogo")
    os.makedirs(cartella_reports, exist_ok=True)

    print(f"\n{'=' * 60}")
    print(f"Generazione report singoli in: {cartella_reports}")

    for nome_modello in sorted(errori_per_file_per_modello.keys()):
        errori_per_file = errori_per_file_per_modello[nome_modello]
        # Crea un nome file valido dal nome modello
        # es. "3-shot/Qwen2.5-3b" → "3-shot_Qwen2.5-3b"
        nome_file_report = nome_modello.replace("/", "_").replace("\\", "_")
        report_singolo_path = os.path.join(
            cartella_reports, f"report_{nome_file_report}.txt"
        )
        genera_report_singolo(nome_modello, errori_per_file, report_singolo_path)

    print(f"\n{'=' * 60}")
    print("Elaborazione completata!")





# ============================================================================
if __name__ == "__main__":
    main()

