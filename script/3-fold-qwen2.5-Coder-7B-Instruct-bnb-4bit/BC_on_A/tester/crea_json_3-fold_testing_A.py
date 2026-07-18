import os
import sys
import json

# Importiamo il parser del catalogo VNF
sys.path.append(r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\Script_Unsloth_base")
# pyrefly: ignore [missing-import]
import parser_catalogo

def main():
    base_dir = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\intenti2.0"
    output_dir = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\3-fold-qwen2.5-Coder-7B-Instruct-bnb-4bit\BC_on_A\tester"

    # Carichiamo la mappa VNF una sola volta per efficienza
    catalogo_json = os.path.join(base_dir, "catalogoVNF.json")
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
        print(f"Catalogo VNF caricato: {len(mappa_vnf)} VNF trovate.")
    except FileNotFoundError:
        print(f"Attenzione: catalogo VNF non trovato in {catalogo_json}. Il testo non verrà arricchito.")
        mappa_vnf = {}
    
    # Dictionaries to hold the intents
    intents = {
        'A': [],
        'B': [],
        'C': []
    }
    
    # Iterate over context directories
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found.")
        return

    for context_name in os.listdir(base_dir):
        context_path = os.path.join(base_dir, context_name)
        
        # Check if it's a directory and starts with 'context'
        if os.path.isdir(context_path) and context_name.startswith('context'):
            # For each type A
            for intent_type in ['A']:
                intent_filename = f"intent{intent_type}.txt"
                intent_path = os.path.join(context_path, intent_filename)
                
                if os.path.exists(intent_path):
                    with open(intent_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()

                    # Arricchiamo il testo con i valori hardware del catalogo VNF
                    if mappa_vnf:
                        content = parser_catalogo.arricchisci_intento_con_hardware(content, mappa_vnf)
                        
                    # We store it as a dict to use the 'id' and 'input' format supported by tester.py
                    intents[intent_type].append({
                        "id": f"{context_name}_intent{intent_type}",
                        "input": content
                    })
    
    # Write to JSON files
    for intent_type, data in intents.items():
        if data:
            output_file = os.path.join(output_dir, f"test_intent{intent_type}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Creato {output_file} con {len(data)} intenti di tipo {intent_type}.")

if __name__ == "__main__":
    main()
