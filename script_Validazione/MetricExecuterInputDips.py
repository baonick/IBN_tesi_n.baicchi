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
    e rimuove tutti gli identificatori arbitrari (ID intento, ID target, ID regole).
    """
    set_fatti = set()
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo = f.read()
    except FileNotFoundError:
        print(f"❌ Errore: Il file {percorso_file} non esiste!")
        return set_fatti

    testo_pulito = re.sub(r'%.*', '', testo)
    lista_vnf = trova_target_list(testo_pulito)
    mappatura_vnf = crea_mappatura_vnf(lista_vnf)
    
    pattern_fatti = re.compile(r"([a-zA-Z0-9_]+)\((.*?)\)\.")
    
    for match in pattern_fatti.finditer(testo_pulito):
        predicato = match.group(1).strip()
        argomenti_str = match.group(2)
        
        args_normalizzati = argomenti_str
        for vnf_originale, vnf_norm in mappatura_vnf.items():
            args_normalizzati = re.sub(rf'\b{re.escape(vnf_originale)}\b', vnf_norm, args_normalizzati)
        
        args_normalizzati = re.sub(r'\s+', ' ', args_normalizzati).replace(', ', ',').strip()
        
        # === NUOVA NORMALIZZAZIONE MIGLIORATA ===
        
        if predicato == 'propertyExpectation':
            # Rimuove ID Regola e ID Intento (i primi due parametri)
            parts = args_normalizzati.split(',')
            if len(parts) > 2:
                args_normalizzati = ",".join(parts[2:])
                
        elif predicato == 'intent':
            # L'intent ha es: intent(ID_Intento, User, Value, ID_Target)
            # Dobbiamo rimuovere il PRIMO (ID_Intento) e l'ULTIMO (ID_Target)
            parts = args_normalizzati.split(',')
            if len(parts) > 2:
                args_normalizzati = ",".join(parts[1:-1]) # Prende tutto tranne il primo e l'ultimo
                
        elif predicato == 'target':
            # Il target ha es: target(ID_Target, [vnf_0, vnf_1])
            # Vogliamo tenere SOLO la lista. Usiamo una regex per estrarre le parentesi quadre
            match_list = re.search(r'\[(.*?)\]', args_normalizzati)
            if match_list:
                args_normalizzati = f"[{match_list.group(1)}]"

        # Aggiungiamo al set solo se non è vuoto
        if args_normalizzati:
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

def calcola_f1_score(precision, recall):
    """Calcola l'F1-Score (Media Armonica tra Precision e Recall)."""
    if precision + recall == 0:
        return 0.0
    return round(2 * (precision * recall) / (precision + recall), 4)

# ==========================================
# MAIN DI TEST
# ==========================================
if __name__ == "__main__":
    print("=== VALUTATORE SEMANTICO PROLOG ===")
    
    FILE_IDEALE = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent0/intent0.pl" 
    FILE_LLM = "/home/nick/UNI/IBN_tesi_n.baicchi/intenti/intent1/intent1.pl"    
    
    # ... (Stampe di lettura file omesse per brevità) ...
    set_ideale = estrai_set_da_pl(FILE_IDEALE)
    print("--- Fatti Estratti ideale ---")
    print(set_to_string(set_ideale) + "\n")
    set_llm = estrai_set_da_pl(FILE_LLM)
    print("--- Fatti Estratti LLM ---")
    print(set_to_string(set_llm) + "\n")
    
    score_jaccard = calcola_jaccard(set_ideale, set_llm)
    score_omissioni = calcola_sensibilita_omissioni(set_ideale, set_llm) # Recall
    score_allucinazioni = calcola_sensibilita_allucinazioni(set_ideale, set_llm) # Precision
    score_f1 = calcola_f1_score(score_allucinazioni, score_omissioni)
    
    print("==================================================")
    print("📊 RISULTATI VALUTAZIONE LOGICA")
    print("==================================================")
    print(f"✅ Sensibilità alle Omissioni (Recall)     : {score_omissioni}")
    print(f"🎯 Sensibilità alle Allucinazioni (Precision): {score_allucinazioni}")
    print(f"⚖️ Jaccard Similarity (Globale)            : {score_jaccard}")
    print(f"🏆 F1-Score (Equilibrio)                   : {score_f1}")
    print("==================================================")