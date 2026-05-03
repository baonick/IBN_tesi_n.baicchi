import re

def trova_target_list(testo_pl):
    """Estrae la lista delle VNF dal predicato target/2 leggendo il testo Prolog."""
    pattern = re.compile(r"target\([^,]+,\s*\[(.*?)\]\)")
    match = pattern.search(testo_pl)
    if match:
        vnfs = [v.strip() for v in match.group(1).split(',')]
        return [v for v in vnfs if v]
    return []

def crea_mappatura_vnf(lista_vnf):
    """Crea il dizionario di mappatura dai nomi originali ai nomi normalizzati (es. vnf_0)."""
    return {vnf: f"vnf_{i}" for i, vnf in enumerate(lista_vnf)}

def estrai_set_da_pl(percorso_file):
    """
    Legge un file .pl, estrae i fatti Prolog, normalizza le VNF 
    e isola la pura logica dai metadati per il confronto.
    """
    set_fatti = set()
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo = f.read()
    except FileNotFoundError:
        print(f"❌ Errore: Il file {percorso_file} non esiste!")
        return set_fatti

    # Rimuoviamo i commenti Prolog (%)
    testo_pulito = re.sub(r'%.*', '', testo)

    # Mappatura VNF
    lista_vnf = trova_target_list(testo_pulito)
    mappatura_vnf = crea_mappatura_vnf(lista_vnf)
    
    # Estrazione fatti
    pattern_fatti = re.compile(r"([a-zA-Z0-9_]+)\((.*?)\)\.")
    
    for match in pattern_fatti.finditer(testo_pulito):
        predicato = match.group(1).strip()
        argomenti_str = match.group(2)
        
        # Normalizziamo le VNF usando il dizionario
        args_normalizzati = argomenti_str
        for vnf_originale, vnf_norm in mappatura_vnf.items():
            args_normalizzati = re.sub(rf'\b{re.escape(vnf_originale)}\b', vnf_norm, args_normalizzati)
        
        args_normalizzati = re.sub(r'\s+', ' ', args_normalizzati).replace(', ', ',').strip()
        
        # Normalizzazione specifica per predicato (rimozione metadati/ID fittizi)
        if predicato == 'propertyExpectation':
            parts = args_normalizzati.split(',')
            if len(parts) > 2:
                args_normalizzati = ",".join(parts[2:])
        elif predicato == 'intent':
            parts = args_normalizzati.split(',')
            if len(parts) > 0:
                args_normalizzati = ",".join(parts[1:])
        elif predicato == 'target':
            parts = args_normalizzati.split(',', 1)
            if len(parts) > 1:
                args_normalizzati = parts[1]

        fatto_normalizzato = f"{predicato}({args_normalizzati})"
        set_fatti.add(fatto_normalizzato)

    return set_fatti

def set_to_string(set_soluzioni):
    """Restituisce una stringa formattata del set."""
    if not set_soluzioni:
        return "Nessun fatto trovato (Set vuoto)"
    return "\n".join(sorted(list(set_soluzioni)))

# ==========================================
# METRICHE DI VALUTAZIONE
# ==========================================

def calcola_jaccard(set_ideale, set_llm):
    """
    Calcola la severità assoluta: |Ideale ∩ LLM| / |Ideale ∪ LLM|
    Penalizza sia le omissioni che le allucinazioni contemporaneamente.
    """
    if not set_ideale and not set_llm: return 1.0 
    if not set_ideale or not set_llm: return 0.0
    
    intersezione = set_ideale.intersection(set_llm)
    unione = set_ideale.union(set_llm)
    return round(len(intersezione) / len(unione), 4)

def calcola_sensibilita_omissioni(set_ideale, set_llm):
    """
    Calcola la Recall: |Ideale ∩ LLM| / |Ideale|
    Misura se l'LLM ha dimenticato dei fatti fondamentali.
    """
    if not set_ideale: return 1.0 # Non c'era nulla da prevedere
    if not set_llm: return 0.0    # Ha omesso tutto
    
    intersezione = set_ideale.intersection(set_llm)
    return round(len(intersezione) / len(set_ideale), 4)

def calcola_sensibilita_allucinazioni(set_ideale, set_llm):
    """
    Calcola la Precision: |Ideale ∩ LLM| / |LLM|
    Misura se l'LLM ha inventato regole non richieste (spazzatura in più).
    """
    if not set_llm and not set_ideale: return 1.0
    if not set_llm: return 0.0    # Non ha generato nulla, precisione 0
    
    intersezione = set_ideale.intersection(set_llm)
    return round(len(intersezione) / len(set_llm), 4)

# ==========================================
# MAIN DI TEST
# ==========================================
if __name__ == "__main__":
    print("=== VALUTATORE SEMANTICO PROLOG ===")
    
    # Inserisci i nomi dei tuoi file reali qui
    FILE_IDEALE = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent0/intent0.pl" 
    FILE_LLM = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent1/intent1.pl"    
    
    print(f"\nLettura di '{FILE_IDEALE}' (Gold Standard)...")
    set_ideale = estrai_set_da_pl(FILE_IDEALE)
    print("--- Fatti Estratti ---")
    print(set_to_string(set_ideale) + "\n")
    
    print(f"Lettura di '{FILE_LLM}' (Output LLM)...")
    set_llm = estrai_set_da_pl(FILE_LLM)
    print("--- Fatti Estratti ---")
    print(set_to_string(set_llm) + "\n")
    
    # Esecuzione metriche
    score_jaccard = calcola_jaccard(set_ideale, set_llm)
    score_omissioni = calcola_sensibilita_omissioni(set_ideale, set_llm)
    score_allucinazioni = calcola_sensibilita_allucinazioni(set_ideale, set_llm)
    
    print("==================================================")
    print("📊 RISULTATI VALUTAZIONE")
    print("==================================================")
    print(f"✅ Sensibilità alle Omissioni      : {score_omissioni}  (1.0 = Nessun vincolo dimenticato)")
    print(f"🎯 Sensibilità alle Allucinazioni  : {score_allucinazioni}  (1.0 = Nessun vincolo inventato)")
    print(f"⚖️ Jaccard Similarity (Globale)    : {score_jaccard}  (1.0 = Copia perfetta)")
    print("==================================================")