import os
import sys
import json

# Importiamo il parser del catalogo VNF
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import parser_catalogo

# Programma che crea un dataset in formato JSONL per l'approccio 3-fold cross-validation per contesto.
# Seleziona DUE intervalli distinti di contesti e per ciascuno include tutti e 3 gli schemi (A, B, C).
# Ogni contesto produce 3 righe nel JSONL (una per schema).

# ============================================================
# CONFIGURAZIONE: Modifica questi valori per selezionare i due intervalli di contesti
# ============================================================
# Primo intervallo
CONTEXT_START_1 = 1     # Numero del primo contesto del primo intervallo (incluso)
CONTEXT_END_1 = 7      # Numero dell'ultimo contesto del primo intervallo (incluso)

# Secondo intervallo
CONTEXT_START_2 = 15    # Numero del primo contesto del secondo intervallo (incluso)
CONTEXT_END_2 = 34      # Numero dell'ultimo contesto del secondo intervallo (incluso)
# ============================================================

def main():
    INSTRUCTION = """Translate the natural language network intent into formal Prolog facts using the strictly defined schema below.

CRITICAL LOGIC RULES (MUST FOLLOW STEP-BY-STEP):

1. VNF Chain Identification & Grounding:
   - First, identify the exact chain of network functions (VNFs) explicitly requested in the input text.
   - This VNF chain constitutes the list of VNFs inside the 'target' fact (e.g., target(ServiceName, [vnf1, vnf2, ...])).
   - For all subsequent Prolog facts (vnf, vnfXUser, propertyExpectation), you MUST USE ONLY the VNFs from this exact target list. DO NOT invent, hallucinate, or mix up VNFs from other examples or contexts.

2. HARD vs SOFT Mapping (Non-Changing Properties):
   - Mandatory words: "must", "strictly", "required", "guaranteeing", "ensuring", "mandatory" -> Map to 'hard'.
   - Preference words: "prefer", "optimally", "should", "desired", "if possible" -> Map to 'soft'.

3. BEFORE vs AFTER Mapping (Changing Properties):
   - Topology depends on the preposition in the natural language:
   - If "[Service] AFTER [VnfID]": Source is VnfID, Destination is '_'.
     Template: propertyExpectation(PropID, IntentID, Type, _, VnfID, _).
   - If "[Service] BEFORE [VnfID]": Source is '_', Destination is VnfID.
     Template: propertyExpectation(PropID, IntentID, Type, _, _, VnfID).
   
SCHEMA DEFINITIONS:

1. Intent & Target:
   - intent(IntentID, ProviderOp, NumUsers, ServiceName). (IntentID ends in 'Intent', ProviderOp in 'Op').
   - target(ServiceName, [vnf1, vnf2, ...]).

2. Nodes (Hardware & Computing):
   - vnf(VnfID, edge/cloud, HardwareValue).
   - vnfXUser(VnfID, l, (1, NumUsers), ComputingValue).

3. Non-Changing Properties (9 params):
   - propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF).
   - Valid Types: bandwidth, latency, totChainHW, affinity. (Affinity Values: bound, dedicated, same).

4. Changing Properties (6 params):
   - propertyExpectation(PropID, IntentID, Type, _, Source, Destination).
   - Valid Types: security, compression, logging, privacy, caching, decoding, encoding.
"""

    cartella_base = os.path.join(_PROJECT_ROOT, "intent")
    output_dir = os.path.dirname(os.path.abspath(__file__))
    nome_file_pl = "facts.pl"
    schemi = ["intentA.txt", "intentB.txt", "intentC.txt"]

    # Validazione degli intervalli
    if CONTEXT_START_1 > CONTEXT_END_1:
        print(f"Errore: CONTEXT_START_1 ({CONTEXT_START_1}) deve essere <= CONTEXT_END_1 ({CONTEXT_END_1}).")
        sys.exit(1)
    if CONTEXT_START_2 > CONTEXT_END_2:
        print(f"Errore: CONTEXT_START_2 ({CONTEXT_START_2}) deve essere <= CONTEXT_END_2 ({CONTEXT_END_2}).")
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

    # Costruiamo la lista di contesti dai due intervalli
    contesti_da_processare = list(range(CONTEXT_START_1, CONTEXT_END_1 + 1)) + \
                             list(range(CONTEXT_START_2, CONTEXT_END_2 + 1))

    nome_file_jsonl = os.path.join(
        output_dir,
        f"dataset_train_context{CONTEXT_START_1}-{CONTEXT_END_1}_{CONTEXT_START_2}-{CONTEXT_END_2}.jsonl"
    )

    print(f"Creazione dataset di training per due intervalli di contesti:")
    print(f"  Intervallo 1: context{CONTEXT_START_1} - context{CONTEXT_END_1}")
    print(f"  Intervallo 2: context{CONTEXT_START_2} - context{CONTEXT_END_2}")
    print(f"Per ogni contesto verranno inclusi tutti e 3 gli schemi: A, B, C")

    with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
        count = 0
        contesti_trovati = 0

        for i in contesti_da_processare:
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
    print(f"     Contesti processati: {contesti_trovati}")
    print(f"       Intervallo 1: context{CONTEXT_START_1}-{CONTEXT_END_1}")
    print(f"       Intervallo 2: context{CONTEXT_START_2}-{CONTEXT_END_2}")
    print(f"     Righe totali: {count} (3 schemi x {contesti_trovati} contesti)")

if __name__ == "__main__":
    main()

