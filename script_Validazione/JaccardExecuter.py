import re

def crea_mappatura_vnf(prima_riga):
    """
    Crea un dizionario per mappare i nomi originali delle VNF ai nomi normalizzati (es. vnf_0)
    basandosi sulla riga TARGET.
    """
    mappatura_vnf = {}
    if prima_riga.startswith("TARGET:"):
        target_str = prima_riga.replace("TARGET:", "")
        if target_str != "NESSUN_TARGET" and target_str != "":
            lista_vnf = target_str.split(",")
            # Creiamo il dizionario: es. {"meterGatewayVF": "vnf_0"}
            for i, vnf in enumerate(lista_vnf):
                mappatura_vnf[vnf.strip()] = f"vnf_{i}"
    return mappatura_vnf

def estrai_set_da_txt(percorso_file):
    """
    Legge un file txt generato da Prolog, normalizza i nomi delle VNF 
    basandosi sull'intestazione TARGET, ed estrae le configurazioni.
    """
    set_soluzioni = set()
    
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            linee = f.readlines()
            
        if not linee:
            return set_soluzioni
            
        # 1. PARSING DELLA PRIMA RIGA (La Stele di Rosetta)
        prima_riga = linee[0].strip()
        mappatura_vnf = crea_mappatura_vnf(prima_riga)
                    
        # 2. UNIAMO IL RESTO DEL FILE (Dalla seconda riga in poi)
        contenuto = "".join(linee[1:]).strip()
            
        # Se il file contiene errori o zero soluzioni, restituiamo un set vuoto
        if not contenuto or contenuto == "false" or contenuto == "[]" or "ERRORE" in contenuto:
            return set_soluzioni
            
        # Regex per isolare le soluzioni e i piazzamenti
        pattern_soluzione = re.compile(r"\(\s*\d+\s*,\s*\[(.*?)\]\s*,")
        pattern_on = re.compile(r"on\(([^,]+),\s*([^,]+),\s*([^)]+)\)")
        
        for match_sol in pattern_soluzione.finditer(contenuto):
            placements_str = match_sol.group(1)
            piazzamenti_originali = pattern_on.findall(placements_str)
            
            # 3. TRADUZIONE DEI NOMI (La magia avviene qui)
            piazzamenti_normalizzati = []
            for vnf, dim, nodo in piazzamenti_originali:
                vnf_pulita = vnf.strip()
                # Se la VNF è nel dizionario, usiamo il nuovo nome (es. vnf_0).
                # Altrimenti (fallback di sicurezza), teniamo il nome originale.
                nome_normalizzato = mappatura_vnf.get(vnf_pulita, vnf_pulita)
                
                piazzamenti_normalizzati.append((nome_normalizzato, dim.strip(), nodo.strip()))
            
            configurazione = frozenset(piazzamenti_normalizzati)
            set_soluzioni.add(configurazione)
            
    except FileNotFoundError:
        print(f"❌ Errore: Il file {percorso_file} non esiste!")
        
    return set_soluzioni


def set_to_string(set_soluzioni):
    """Restituisce una stringa formattata del set."""
    if not set_soluzioni:
        return "Nessuna soluzione (Set vuoto)"
    
    linee_testo = []
    for indice, configurazione in enumerate(set_soluzioni, start=1):
        piazzamenti_ordinati = sorted(list(configurazione), key=lambda x: x[0])
        stringhe_on = [f"on({vnf}, {dim}, {nodo})" for vnf, dim, nodo in piazzamenti_ordinati]
        riga_soluzione = f"Soluzione {indice}: [" + ", ".join(stringhe_on) + "]"
        linee_testo.append(riga_soluzione)
        
    return "\n".join(linee_testo)


def calcola_jaccard(set_ideale, set_llm):
    """Calcola la Jaccard Similarity tra i due set."""
    if not set_ideale and not set_llm:
        return 1.0 
    if not set_ideale or not set_llm:
        return 0.0
        
    intersezione = set_ideale.intersection(set_llm)
    unione = set_ideale.union(set_llm)
    
    return round(len(intersezione) / len(unione), 4)


# ==========================================
# MAIN DI TEST
# ==========================================
if __name__ == "__main__":
    print("=== SCRIPT 2: VALUTATORE JACCARD ===")
    
    FILE_IDEALE = "output_intent0.txt"
    FILE_LLM = "output_intent1.txt" 
    
    print(f"\nLettura di '{FILE_IDEALE}'...")
    set_ideale = estrai_set_da_txt(FILE_IDEALE)
    print("--- ESTRATTO (Ideale) ---")
    print(set_to_string(set_ideale)[:500] + "...\n") # Stampo solo i primi 500 caratteri per non intasare il terminale
    
    print(f"Lettura di '{FILE_LLM}'...")
    set_llm = estrai_set_da_txt(FILE_LLM)
    print("--- ESTRATTO (LLM) ---")
    print(set_to_string(set_llm)[:500] + "...\n")
    
    print(f"Soluzioni uniche trovate (Ideale): {len(set_ideale)}")
    print(f"Soluzioni uniche trovate (LLM)   : {len(set_llm)}")
    
    score_jaccard = calcola_jaccard(set_ideale, set_llm)
    
    print("\n===============================")
    print(f"🎯 JACCARD SIMILARITY: {score_jaccard}")
    print("===============================")
    
    if score_jaccard == 1.0:
        print("✅ Match PERFETTO! L'architettura è equivalente a prescindere dai nomi usati.")
    elif score_jaccard > 0:
        print("⚠️ Match PARZIALE.")
    else:
        print("❌ Match ZERO. Configurazioni totalmente diverse o assenti.")