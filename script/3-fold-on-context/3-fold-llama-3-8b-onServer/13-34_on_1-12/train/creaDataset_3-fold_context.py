import os
import sys
import json

# Importiamo il parser del catalogo VNF
sys.path.append(r"/disk1/n.baicchi/IBN_tesi_n.baicchi/script/Script_Unsloth_base")
# pyrefly: ignore [missing-import]
import parser_catalogo

# Programma che crea un dataset in formato JSONL per l'approccio 3-fold cross-validation per contesto.
# Seleziona un intervallo di contesti e per ciascuno include tutti e 3 gli schemi (A, B, C).
# Ogni contesto produce 3 righe nel JSONL (una per schema).

# ============================================================
# CONFIGURAZIONE: Modifica questi valori per selezionare l'intervallo di contesti
# ============================================================
CONTEXT_START = 13    # Numero del primo contesto da includere (incluso)
CONTEXT_END = 34     # Numero dell'ultimo contesto da includere (incluso)
# ============================================================

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

    cartella_base = r"/disk1/n.baicchi/IBN_tesi_n.baicchi/intenti2.0"
    output_dir = os.path.dirname(os.path.abspath(__file__))
    nome_file_pl = "facts.pl"
    schemi = ["intentA.txt", "intentB.txt", "intentC.txt"]

    if CONTEXT_START > CONTEXT_END:
        print(f"Errore: CONTEXT_START ({CONTEXT_START}) deve essere <= CONTEXT_END ({CONTEXT_END}).")
        sys.exit(1)

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

    nome_file_jsonl = os.path.join(output_dir, f"dataset_train_context{CONTEXT_START}-{CONTEXT_END}.jsonl")

    print(f"Creazione dataset di training per contesti da {CONTEXT_START} a {CONTEXT_END}...")
    print(f"Per ogni contesto verranno inclusi tutti e 3 gli schemi: A, B, C")

    with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
        count = 0
        contesti_trovati = 0

        for i in range(CONTEXT_START, CONTEXT_END + 1):
            nome_cartella = f"context{i}"
            percorso_cartella = os.path.join(cartella_base, nome_cartella)
            percorso_pl = os.path.join(percorso_cartella, nome_file_pl)

            if not os.path.exists(percorso_cartella):
                print(f"  [SKIP] {nome_cartella} - cartella non trovata.")
                continue

            if not os.path.exists(percorso_pl):
                print(f"  [SKIP] {nome_cartella} - {nome_file_pl} non trovato.")
                continue

            with open(percorso_pl, "r", encoding="utf-8") as f_pl:
                codice_prolog = f_pl.read().strip()

            contesti_trovati += 1

            for nome_txt in schemi:
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
                else:
                    print(f"  [WARN] {nome_cartella}/{nome_txt} non trovato.")

    print(f"\n[OK] Creato {nome_file_jsonl}")
    print(f"     Contesti processati: {contesti_trovati} (da context{CONTEXT_START} a context{CONTEXT_END})")
    print(f"     Righe totali: {count} (3 schemi x {contesti_trovati} contesti)")

if __name__ == "__main__":
    main()
