import os
import sys
import json

# Importiamo il parser del catalogo VNF
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import parser_catalogo

# Programma che crea un file JSON per il testing nell'approccio 3-fold cross-validation per contesto.
# Seleziona un intervallo di contesti e per ciascuno include tutti e 3 gli schemi (A, B, C).
# Ogni contesto produce 3 elementi nel JSON (uno per schema).

# ============================================================
# CONFIGURAZIONE: Modifica questi valori per selezionare l'intervallo di contesti
# ============================================================
CONTEXT_START = 1   # Numero del primo contesto da includere (incluso)
CONTEXT_END = 34     # Numero dell'ultimo contesto da includere (incluso)
# ============================================================

def main():
    base_dir = os.path.join(_PROJECT_ROOT, "intent")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    schemi = ["A", "B", "C"]

    if CONTEXT_START > CONTEXT_END:
        print(f"Errore: CONTEXT_START ({CONTEXT_START}) deve essere <= CONTEXT_END ({CONTEXT_END}).")
        sys.exit(1)

    # Carichiamo la mappa VNF una sola volta per efficienza
    catalogo_json = os.path.join(base_dir, "catalogoVNF.json")
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
        print(f"Catalogo VNF caricato: {len(mappa_vnf)} VNF trovate.")
    except FileNotFoundError:
        print(f"Attenzione: catalogo VNF non trovato in {catalogo_json}. Il testo non verrà arricchito.")
        mappa_vnf = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"Creazione file di testing per contesti da {CONTEXT_START} a {CONTEXT_END}...")
    print(f"Per ogni contesto verranno inclusi tutti e 3 gli schemi: A, B, C")

    intents = []
    contesti_trovati = 0

    for i in range(CONTEXT_START, CONTEXT_END + 1):
        context_name = f"context{i}"
        context_path = os.path.join(base_dir, context_name)

        if not os.path.exists(context_path):
            print(f"  [SKIP] {context_name} - cartella non trovata.")
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

                # Arricchiamo il testo con i valori hardware del catalogo VNF
                if mappa_vnf:
                    content = parser_catalogo.arricchisci_intento_con_hardware(content, mappa_vnf)

                intents.append({
                    "id": f"{context_name}_intent{schema}",
                    "input": content
                })
            else:
                print(f"  [WARN] {context_name}/{intent_filename} non trovato.")

    output_file = os.path.join(output_dir, f"test_context{CONTEXT_START}-{CONTEXT_END}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(intents, f, indent=4, ensure_ascii=False)

    print(f"\n[OK] Creato {output_file}")
    print(f"     Contesti processati: {contesti_trovati} (da context{CONTEXT_START} a context{CONTEXT_END})")
    print(f"     Intenti totali: {len(intents)} (3 schemi x {contesti_trovati} contesti)")

if __name__ == "__main__":
    main()

