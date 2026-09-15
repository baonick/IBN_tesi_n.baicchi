import json
import re
import os
import glob

def carica_catalogo_vnf(json_path):
    """
    Loads the VNF catalog from the JSON file and returns a dictionary
    that maps the VNF ID to its hardware value.
    
    :param json_path: Path to the catalogoVNF.json file
    :return: Dictionary { 'vnf_name': hardware_int }
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
    Searches the intent text for the VNF names present in the catalog
    and replaces them with the formatted string <identifier, hardware>.
    
    :param testo_intento: String containing the original intent text
    :param mappa_vnf: Dictionary returned by carica_catalogo_vnf()
    :return: String with the modified intent text
    """
    testo_modificato = testo_intento
    
    # Sort VNF names by length in descending order.
    # This prevents bugs in case a VNF name is a substring of another.
    vnf_ids = sorted(mappa_vnf.keys(), key=len, reverse=True)
    
    for vnf_id in vnf_ids:
        hardware = mappa_vnf[vnf_id]
        # Use \b to make sure to replace only whole words and not parts of other words
        pattern = r'\b' + re.escape(vnf_id) + r'\b'
        sostituzione = f"<{vnf_id}, {hardware}>"
        
        # Perform the replacement in the text
        testo_modificato = re.sub(pattern, sostituzione, testo_modificato)
        
    return testo_modificato

def elabora_singolo_file_intento(percorso_intento, json_path):
    """
    Reads a single intent file, applies the replacement, and returns the modified text.
    
    :param percorso_intento: Path to the intent text file
    :param json_path: Path to the JSON catalog file
    :return: Modified intent text
    """
    mappa_vnf = carica_catalogo_vnf(json_path)
    
    with open(percorso_intento, 'r', encoding='utf-8') as f:
        testo_intento = f.read()
        
    return arricchisci_intento_con_hardware(testo_intento, mappa_vnf)

def elabora_tutti_gli_intenti(cartella_intenti, json_path):
    """
    Reads all text files (.txt) inside the specified folder,
    skipping any catalogs, and returns a dictionary with the results.
    
    :param cartella_intenti: Path to the folder containing the intents (e.g. 'intent')
    :param json_path: Path to the JSON catalog file
    :return: Dictionary { 'filename.txt': 'modified_text' }
    """
    mappa_vnf = carica_catalogo_vnf(json_path)
    risultati = {}
    
    # Search for all .txt files in the folder
    pattern_ricerca = os.path.join(cartella_intenti, "*.txt")
    for percorso_file in glob.glob(pattern_ricerca):
        nome_file = os.path.basename(percorso_file)
        
        # Avoid processing the original catalog file if it is in the same folder
        if "catalogo" in nome_file.lower():
            continue
            
        with open(percorso_file, 'r', encoding='utf-8') as f:
            testo_intento = f.read()
            
        risultati[nome_file] = arricchisci_intento_con_hardware(testo_intento, mappa_vnf)
        
    return risultati

# ==========================================
# USAGE EXAMPLE (if executed directly)
# ==========================================
if __name__ == "__main__":
    # Calculate the absolute path based on where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    CATALOGO_JSON = os.path.join(script_dir, "..", "intent", "catalogoVNF.json")
    
    # Test 1: Processing a test string
    print("--- STRING TEST ---")
    
    try:
        mappa = carica_catalogo_vnf(CATALOGO_JSON)
        testo_prova = "The operator requests to deploy a mailGatewayVF and subsequently a sandboxScannerVF."
        risultato_prova = arricchisci_intento_con_hardware(testo_prova, mappa)
        print("Original:", testo_prova)
        print("Modified:", risultato_prova)
    except FileNotFoundError:
        print(f"Error: Unable to find the file '{CATALOGO_JSON}'.")
        print("Ensure that the catalogoVNF.json file exists in the intent folder.")
