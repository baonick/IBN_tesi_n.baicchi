import json
import re
import os
import glob

def carica_catalogo_vnf(json_path):
    """
    Carica il catalogo VNF dal file JSON e restituisce un dizionario
    che mappa l'ID della VNF al suo valore hardware.
    
    :param json_path: Percorso del file catalogoVNF.json
    :return: Dizionario { 'nome_vnf': hardware_int }
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        catalogo = json.load(f)
    
    mappa_vnf = {}
    for vnf in catalogo:
        vnf_id = vnf.get("id")
        hardware = vnf.get("hardware")
        if vnf_id and hardware is not None:
            mappa_vnf[vnf_id] = hardware
            
    return mappa_vnf

def arricchisci_intento_con_hardware(testo_intento, mappa_vnf):
    """
    Cerca nel testo dell'intento i nomi delle VNF presenti nel catalogo
    e li sostituisce con la stringa formattata <identificatore, hardware>.
    
    :param testo_intento: Stringa contenente il testo dell'intento originale
    :param mappa_vnf: Dizionario restituito da carica_catalogo_vnf()
    :return: Stringa con il testo dell'intento modificato
    """
    testo_modificato = testo_intento
    
    # Ordiniamo i nomi delle VNF per lunghezza decrescente.
    # Questo previene bug nel caso in cui il nome di una VNF sia una sottostringa di un'altra.
    vnf_ids = sorted(mappa_vnf.keys(), key=len, reverse=True)
    
    for vnf_id in vnf_ids:
        hardware = mappa_vnf[vnf_id]
        # Usiamo \b per assicurarci di sostituire solo parole intere e non pezzi di altre parole
        pattern = r'\b' + re.escape(vnf_id) + r'\b'
        sostituzione = f"<{vnf_id}, {hardware}>"
        
        # Effettuiamo la sostituzione nel testo
        testo_modificato = re.sub(pattern, sostituzione, testo_modificato)
        
    return testo_modificato

def elabora_singolo_file_intento(percorso_intento, json_path):
    """
    Legge un singolo file di intento, applica la sostituzione e restituisce il testo modificato.
    
    :param percorso_intento: Percorso del file di testo dell'intento
    :param json_path: Percorso del file catalogo JSON
    :return: Testo dell'intento modificato
    """
    mappa_vnf = carica_catalogo_vnf(json_path)
    
    with open(percorso_intento, 'r', encoding='utf-8') as f:
        testo_intento = f.read()
        
    return arricchisci_intento_con_hardware(testo_intento, mappa_vnf)

def elabora_tutti_gli_intenti(cartella_intenti, json_path):
    """
    Legge tutti i file di testo (.txt) all'interno della cartella specificata,
    saltando eventuali cataloghi, e restituisce un dizionario con i risultati.
    
    :param cartella_intenti: Percorso della cartella contenente gli intenti (es. 'intent')
    :param json_path: Percorso del file catalogo JSON
    :return: Dizionario { 'nome_file.txt': 'testo_modificato' }
    """
    mappa_vnf = carica_catalogo_vnf(json_path)
    risultati = {}
    
    # Cerca tutti i file .txt nella cartella
    pattern_ricerca = os.path.join(cartella_intenti, "*.txt")
    for percorso_file in glob.glob(pattern_ricerca):
        nome_file = os.path.basename(percorso_file)
        
        # Evita di elaborare il file di catalogo originale se si trova nella stessa cartella
        if "catalogo" in nome_file.lower():
            continue
            
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo_intento = f.read()
            
        risultati[nome_file] = arricchisci_intento_con_hardware(testo_intento, mappa_vnf)
        
    return risultati

# ==========================================
# ESEMPIO DI UTILIZZO (se eseguito da solo)
# ==========================================
if __name__ == "__main__":
    # Calcola il percorso assoluto in base a dove si trova questo script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    CATALOGO_JSON = os.path.join(script_dir, "..", "intent", "catalogoVNF.json")
    
    # Test 1: Elaborazione di una stringa di prova
    print("--- TEST STRINGA ---")
    
    try:
        mappa = carica_catalogo_vnf(CATALOGO_JSON)
        testo_prova = "L'operatore richiede di dispiegare un mailGatewayVF e successivamente un sandboxScannerVF."
        risultato_prova = arricchisci_intento_con_hardware(testo_prova, mappa)
        print("Originale:", testo_prova)
        print("Modificato:", risultato_prova)
    except FileNotFoundError:
        print(f"Errore: Impossibile trovare il file '{CATALOGO_JSON}'.")
        print("Assicurati che il file catalogoVNF.json esista nella cartella intent.")

