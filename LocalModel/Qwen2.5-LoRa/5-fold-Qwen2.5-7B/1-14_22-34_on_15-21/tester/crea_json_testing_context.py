import os
import sys
import json

# Import the VNF catalog parser
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import parser_catalogo

# Programma che crea un file JSON per il testing nell'approccio 3-fold cross-validation per contesto.
# Seleziona un intervallo di contesti e per ciascuno include tutti e 3 gli schemi (A, B, C).
# Ogni contesto produce 3 elementi nel JSON (uno per schema).

# ============================================================
# CONFIGURATION: Modify these values to select the context range
# ============================================================
CONTEXT_START = 15   # Numero del primo contesto da includere (incluso)
CONTEXT_END = 21     # Numero dell'ultimo contesto da includere (incluso)
# ============================================================

def main():
    base_dir = os.path.join(_PROJECT_ROOT, "intent")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    schemi = ["A", "B", "C"]

    if CONTEXT_START > CONTEXT_END:
        print(f"Error: CONTEXT_START ({CONTEXT_START}) must be <= CONTEXT_END ({CONTEXT_END}).")
        sys.exit(1)

    # We load the VNF map only once for efficiency
    catalogo_json = os.path.join(base_dir, "catalogoVNF.json")
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
        print(f"VNF catalog loaded: {len(mappa_vnf)} VNFs found.")
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalogo_json}. Text will not be enriched.")
        mappa_vnf = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Creazione file di testing per contesti da {CONTEXT_START} a {CONTEXT_END}...")
    print(f"For each context, all 3 schemas will be included: A, B, C")

    intents = []
    contesti_trovati = 0

    for i in range(CONTEXT_START, CONTEXT_END + 1):
        context_name = f"context{i}"
        context_path = os.path.join(base_dir, context_name)

        if not os.path.exists(context_path):
            print(f"  [SKIP] {context_name} - folder not found.")
            continue

        if not os.path.isdir(context_path):
            print(f"  [SKIP] {context_name} - non è una directory.")
            continue

        contesti_trovati += 1

        for schema in schemi:
            intent_filename = f"intent{schema}.txt"
            intent_path = os.path.join(context_path, intent_filename)

            if os.path.exists(intent_path):
                with open(intent_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()

                # Enrich the text with the hardware values of the VNF catalog
                if mappa_vnf:
                    content = parser_catalogo.arricchisci_intento_con_hardware(content, mappa_vnf)

                intents.append({
                    "id": f"{context_name}_intent{schema}",
                    "input": content
                })
            else:
                print(f"  [WARN] {context_name}/{intent_filename} not found.")

    output_file = os.path.join(output_dir, f"test_context{CONTEXT_START}-{CONTEXT_END}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=4, ensure_ascii=False)

    print(f"\n[OK] Creato {output_file}")
    print(f"     Processed contexts: {contesti_trovati} (da context{CONTEXT_START} a context{CONTEXT_END})")
    print(f"     Intenti totali: {len(intents)} (3 schemi x {contesti_trovati} contesti)")

if __name__ == "__main__":
    main()

