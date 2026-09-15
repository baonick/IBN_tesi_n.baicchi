import re

# ==============================================================================
#  PROLOG PARSING
# ==============================================================================

def trova_target_list(testo_pl):
    """Extracts the VNF list from the target/2 predicate (e.g. target(_, [fw, ids]) → ['fw','ids'])."""
    match = re.search(r"target\([^,]+,\s*\[(.*?)\]\)", testo_pl)
    return [v.strip() for v in match.group(1).split(',') if v.strip()] if match else []


def crea_mappatura_vnf(lista_vnf):
    """Maps each VNF to the normalized name: {fw: vnf_0, ids: vnf_1, ...}."""
    return {vnf: f"vnf_{i}" for i, vnf in enumerate(lista_vnf)}


# ==============================================================================
#  PREDICATE NORMALIZATION
# ==============================================================================

def _norm_property_expectation(args):
    """Removes Rule ID and Intent ID (first 2 parameters).
    
    For 'affinity dedicated' properties, sorts the last two VNF parameters
    (SourceVNF, DestVNF) alphabetically because they are interchangeable.
    """
    parts = args.split(',')
    if len(parts) <= 2:
        return args
    norm = parts[2:]
    # norm has 7 elements: Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF
    # If Type == 'affinity' and Value == 'dedicated', sort SourceVNF and DestVNF
    if len(norm) == 7:
        tipo = norm[0].strip()
        valore = norm[3].strip()
        if tipo == 'affinity' and valore == 'dedicated':
            norm[-2], norm[-1] = sorted([norm[-2].strip(), norm[-1].strip()])
    return ",".join(norm)


def _norm_intent(args):
    """Removes Intent ID (first) and Target ID (last)."""
    parts = args.split(',')
    return ",".join(parts[1:-1]) if len(parts) > 2 else args


def _norm_target(args):
    """Keeps only the list inside square brackets."""
    match = re.search(r'\[(.*?)\]', args)
    return f"[{match.group(1)}]" if match else args


# Dispatch: predicate → argument normalization function
_NORMALIZZATORI = {
    'propertyExpectation': _norm_property_expectation,
    'intent':              _norm_intent,
    'target':              _norm_target,
}


def normalizza_argomenti(predicato, argomenti_raw):
    """Applies specific normalization to the predicate, if defined."""
    args = re.sub(r'\s+', ' ', argomenti_raw).replace(', ', ',').strip()
    normalizzatore = _NORMALIZZATORI.get(predicato)
    return normalizzatore(args) if normalizzatore else args


# ==============================================================================
#  FACT SET EXTRACTION
# ==============================================================================

def estrai_set_da_pl(percorso_file):
    """Reads a .pl file, extracts Prolog facts and normalizes them (VNF + arbitrary IDs)."""
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo = f.read()
    except FileNotFoundError:
        print(f"❌ Error: The file {percorso_file} does not exist!")
        return set()

    testo = re.sub(r'%.*', '', testo)                    # remove comments
    # mappatura = crea_mappatura_vnf(trova_target_list(testo))

    set_fatti = set()
    for m in re.finditer(r"([a-zA-Z0-9_]+)\((.*?)\)\.", testo):
        predicato, argomenti = m.group(1).strip(), m.group(2)

        # VNF NORMALIZATION HAS BEEN DISABLED
        # for orig, norm in mappatura.items():
        #     argomenti = re.sub(rf'\b{re.escape(orig)}\b', norm, argomenti)

        args_norm = normalizza_argomenti(predicato, argomenti)
        if args_norm:
            set_fatti.add(f"{predicato}({args_norm})")

    return set_fatti


def set_to_string(s):
    """Formats a set of facts as an ordered string, one line per fact."""
    return "\n".join(sorted(s)) if s else "No facts found (Empty set)"


# ==============================================================================
#  EVALUATION METRICS
# ==============================================================================

def calcola_jaccard(set_ideale, set_llm):
    """Jaccard: |I ∩ L| / |I ∪ L|  — penalizes omissions and hallucinations."""
    if not set_ideale and not set_llm: return 1.0
    if not set_ideale or  not set_llm: return 0.0
    return round(len(set_ideale & set_llm) / len(set_ideale | set_llm), 4)


def calcola_recall(set_ideale, set_llm):
    """Recall: |I ∩ L| / |I|  — measures LLM omissions."""
    if not set_ideale: return 1.0
    if not set_llm:    return 0.0
    return round(len(set_ideale & set_llm) / len(set_ideale), 4)


def calcola_precision(set_ideale, set_llm):
    """Precision: |I ∩ L| / |L|  — measures LLM hallucinations."""
    if not set_llm and not set_ideale: return 1.0
    if not set_llm:                    return 0.0
    return round(len(set_ideale & set_llm) / len(set_llm), 4)


def calcola_f1(precision, recall):
    """F1-Score: harmonic mean between Precision and Recall."""
    return round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0


def calcola_accuracy(lista_metriche):
    """Accuracy: number of perfect elements / total number of elements.
    
    An element is 'perfect' if it has precision == 1.0 and recall == 1.0.
    
    Args:
        lista_metriche: list of tuples (precision, recall) for each element of the test set.
    
    Returns:
        Accuracy rounded to 4 decimals.
    """
    if not lista_metriche:
        return 0.0
    perfetti = sum(1 for p, r in lista_metriche if p == 1.0 and r == 1.0)
    return round(perfetti / len(lista_metriche), 4)


# ==============================================================================
#  MAIN
# ==============================================================================

if __name__ == "__main__":
    FILE_IDEALE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "intent", "context1", "facts.pl")
    FILE_LLM    = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "intent", "context2", "facts.pl")

    set_ideale = estrai_set_da_pl(FILE_IDEALE)
    set_llm    = estrai_set_da_pl(FILE_LLM)

    print("=== PROLOG SEMANTIC EVALUATOR ===\n")
    print("--- Ideal Extracted Facts ---")
    print(set_to_string(set_ideale), "\n")
    print("--- LLM Extracted Facts ---")
    print(set_to_string(set_llm), "\n")

    recall    = calcola_recall(set_ideale, set_llm)
    precision = calcola_precision(set_ideale, set_llm)
    jaccard   = calcola_jaccard(set_ideale, set_llm)
    f1        = calcola_f1(precision, recall)

    print("==================================================")
    print("📊 LOGICAL EVALUATION RESULTS")
    print("==================================================")
    print(f"✅ Recall      (Omissions)     : {recall}")
    print(f"🎯 Precision   (Hallucinations) : {precision}")
    print(f"⚖️  Jaccard     (Global)        : {jaccard}")
    print(f"🏆 F1-Score    (Balance)       : {f1}")
    print("==================================================")
