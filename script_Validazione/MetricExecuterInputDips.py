import re

# ==============================================================================
#  PARSING PROLOG
# ==============================================================================

def trova_target_list(testo_pl):
    """Estrae la lista VNF dal predicato target/2 (es. target(_, [fw, ids]) → ['fw','ids'])."""
    match = re.search(r"target\([^,]+,\s*\[(.*?)\]\)", testo_pl)
    return [v.strip() for v in match.group(1).split(',') if v.strip()] if match else []


def crea_mappatura_vnf(lista_vnf):
    """Mappa ogni VNF al nome normalizzato: {fw: vnf_0, ids: vnf_1, ...}."""
    return {vnf: f"vnf_{i}" for i, vnf in enumerate(lista_vnf)}


# ==============================================================================
#  NORMALIZZAZIONE PREDICATI
# ==============================================================================

def _norm_property_expectation(args):
    """Rimuove ID Regola e ID Intento (primi 2 parametri)."""
    parts = args.split(',')
    return ",".join(parts[2:]) if len(parts) > 2 else args


def _norm_intent(args):
    """Rimuove ID Intento (primo) e ID Target (ultimo)."""
    parts = args.split(',')
    return ",".join(parts[1:-1]) if len(parts) > 2 else args


def _norm_target(args):
    """Mantiene solo la lista tra parentesi quadre."""
    match = re.search(r'\[(.*?)\]', args)
    return f"[{match.group(1)}]" if match else args


# Dispatch: predicato → funzione di normalizzazione degli argomenti
_NORMALIZZATORI = {
    'propertyExpectation': _norm_property_expectation,
    'intent':              _norm_intent,
    'target':              _norm_target,
}


def normalizza_argomenti(predicato, argomenti_raw):
    """Applica la normalizzazione specifica al predicato, se definita."""
    args = re.sub(r'\s+', ' ', argomenti_raw).replace(', ', ',').strip()
    normalizzatore = _NORMALIZZATORI.get(predicato)
    return normalizzatore(args) if normalizzatore else args


# ==============================================================================
#  ESTRAZIONE SET DI FATTI
# ==============================================================================

def estrai_set_da_pl(percorso_file):
    """Legge un .pl, estrae i fatti Prolog e li normalizza (VNF + ID arbitrari)."""
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo = f.read()
    except FileNotFoundError:
        print(f"❌ Errore: Il file {percorso_file} non esiste!")
        return set()

    testo = re.sub(r'%.*', '', testo)                    # rimuovi commenti
    # mappatura = crea_mappatura_vnf(trova_target_list(testo))

    set_fatti = set()
    for m in re.finditer(r"([a-zA-Z0-9_]+)\((.*?)\)\.", testo):
        predicato, argomenti = m.group(1).strip(), m.group(2)

        # LA NORMALIZZAZIONE DELLE VNF È STATA DISABILITATA
        # for orig, norm in mappatura.items():
        #     argomenti = re.sub(rf'\b{re.escape(orig)}\b', norm, argomenti)

        args_norm = normalizza_argomenti(predicato, argomenti)
        if args_norm:
            set_fatti.add(f"{predicato}({args_norm})")

    return set_fatti


def set_to_string(s):
    """Formatta un set di fatti come stringa ordinata, una riga per fatto."""
    return "\n".join(sorted(s)) if s else "Nessun fatto trovato (Set vuoto)"


# ==============================================================================
#  METRICHE DI VALUTAZIONE
# ==============================================================================

def calcola_jaccard(set_ideale, set_llm):
    """Jaccard: |I ∩ L| / |I ∪ L|  — penalizza omissioni e allucinazioni."""
    if not set_ideale and not set_llm: return 1.0
    if not set_ideale or  not set_llm: return 0.0
    return round(len(set_ideale & set_llm) / len(set_ideale | set_llm), 4)


def calcola_recall(set_ideale, set_llm):
    """Recall: |I ∩ L| / |I|  — misura le omissioni dell'LLM."""
    if not set_ideale: return 1.0
    if not set_llm:    return 0.0
    return round(len(set_ideale & set_llm) / len(set_ideale), 4)


def calcola_precision(set_ideale, set_llm):
    """Precision: |I ∩ L| / |L|  — misura le allucinazioni dell'LLM."""
    if not set_llm and not set_ideale: return 1.0
    if not set_llm:                    return 0.0
    return round(len(set_ideale & set_llm) / len(set_llm), 4)


def calcola_f1(precision, recall):
    """F1-Score: media armonica tra Precision e Recall."""
    return round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0


# ==============================================================================
#  MAIN
# ==============================================================================

if __name__ == "__main__":
    FILE_IDEALE = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent0/intent0.pl"
    FILE_LLM    = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent1/intent1.pl"

    set_ideale = estrai_set_da_pl(FILE_IDEALE)
    set_llm    = estrai_set_da_pl(FILE_LLM)

    print("=== VALUTATORE SEMANTICO PROLOG ===\n")
    print("--- Fatti Estratti Ideale ---")
    print(set_to_string(set_ideale), "\n")
    print("--- Fatti Estratti LLM ---")
    print(set_to_string(set_llm), "\n")

    recall    = calcola_recall(set_ideale, set_llm)
    precision = calcola_precision(set_ideale, set_llm)
    jaccard   = calcola_jaccard(set_ideale, set_llm)
    f1        = calcola_f1(precision, recall)

    print("==================================================")
    print("📊 RISULTATI VALUTAZIONE LOGICA")
    print("==================================================")
    print(f"✅ Recall      (Omissioni)     : {recall}")
    print(f"🎯 Precision   (Allucinazioni) : {precision}")
    print(f"⚖️  Jaccard     (Globale)       : {jaccard}")
    print(f"🏆 F1-Score    (Equilibrio)    : {f1}")
    print("==================================================")