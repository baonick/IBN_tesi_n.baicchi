import os
import sys
import json

# Importiamo il parser del catalogo VNF
sys.path.append(r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\Script_Unsloth_base")
# pyrefly: ignore [missing-import]
import parser_catalogo

# Programma che crea 3 dataset in formato JSONL per l'approccio 3-fold cross-validation.
# - dataset_train_AB.jsonl (Addestramento su A e B, per testare poi su C)
# - dataset_train_AC.jsonl (Addestramento su A e C, per testare poi su B)
# - dataset_train_BC.jsonl (Addestramento su B e C, per testare poi su A)

def main():
    INSTRUCTION = """Translate the natural language network intent into formal Prolog facts using the following strict schema:
1. Intent: intent(IntentID, ProviderOp, NumUsers, ServiceName). (camelCase; IntentID ends in 'Intent', ProviderOp in 'Op').
2. Target: target(ServiceName, [vnf1, vnf2, ...]). (VNFs in camelCase ending in 'VF').
3. Nodes: For each VNF, write vnf(VnfID, edge/cloud, HardwareValue) and vnfXUser(VnfID, s/m/l, (1, NumUsers), ComputingValue).
4. Non-Changing Properties (9 params): propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF). (Used for totChainHW, affinity, bandwidth, latency. Map 'must' to 'hard', 'prefer' to 'soft').
5. Changing Properties (6 params): propertyExpectation(PropID, IntentID, Type, _, Source, Destination). (Used for security, decoding, logging, etc. Parameter 4 is always a wildcard '_').
   - 'after VnfID': VnfID is the Source (5th param), Destination (6th param) is '_'.
   - 'before VnfID': VnfID is the Destination (6th param), Source (5th param) is '_'.
Generate ONLY the valid Prolog code. No explanations."""

    cartella_base = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\intenti2.0"
    output_dir = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\3-fold-qwen2.5-Coder-7B-Instruct-bnb-4bit\BC_on_A\train"
    numero_totale_contesti = 30
    nome_file_pl = "facts.pl"

    # Carichiamo la mappa VNF una sola volta per efficienza
    catalogo_json = os.path.join(cartella_base, "catalogoVNF.json")
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
        print(f"Catalogo VNF caricato: {len(mappa_vnf)} VNF trovate.")
    except FileNotFoundError:
        print(f"Attenzione: catalogo VNF non trovato in {catalogo_json}. Il testo non verrà arricchito.")
        mappa_vnf = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Definiamo i fold: la chiave è il nome del fold, il valore sono i file txt da includere
    folds = {
        "BC": ["intentB.txt", "intentC.txt"]
    }

    print(f"Inizio la scansione di {numero_totale_contesti} cartelle in {cartella_base}...")

    for fold_name, opzioni_testo in folds.items():
        nome_file_jsonl = os.path.join(output_dir, f"dataset_train_{fold_name}.jsonl")
        
        with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
            count = 0
            for i in range(1, numero_totale_contesti + 1):
                nome_cartella = f"context{i}"
                percorso_cartella = os.path.join(cartella_base, nome_cartella)
                percorso_pl = os.path.join(percorso_cartella, nome_file_pl)
                
                if os.path.exists(percorso_pl):
                    with open(percorso_pl, "r", encoding="utf-8") as f_pl:
                        codice_prolog = f_pl.read().strip()
                        
                    for nome_txt in opzioni_testo:
                        percorso_txt = os.path.join(percorso_cartella, nome_txt)
                        
                        if os.path.exists(percorso_txt):
                            with open(percorso_txt, "r", encoding="utf-8") as f_txt:
                                testo_naturale = f_txt.read().strip()

                            # Arricchiamo il testo con i valori hardware del catalogo VNF
                            if mappa_vnf:
                                testo_naturale = parser_catalogo.arricchisci_intento_con_hardware(testo_naturale, mappa_vnf)
                                
                            riga_json = {
                                "instruction": INSTRUCTION,
                                "input": testo_naturale,
                                "output": codice_prolog
                            }
                            
                            f_out.write(json.dumps(riga_json, ensure_ascii=False) + "\n")
                            count += 1
            print(f"[OK] Creato {nome_file_jsonl} contenente {count} righe (combinando {opzioni_testo}).")

if __name__ == "__main__":
    main()
