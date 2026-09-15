import os
import sys
import json

# Import the VNF catalog parser
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import parser_catalogo

# Program that creates a dataset in JSONL format for the 3-fold cross-validation approach by context.
# Selects TWO distinct ranges of contexts and for each includes all 3 schemas (A, B, C).
# Each context produces 3 rows in JSONL (one per schema).

# ============================================================
# CONFIGURATION: Modify these values to select the two context ranges
# ============================================================
# First range
CONTEXT_START_1 = 1     # Number of the first context of the first range (included)
CONTEXT_END_1 = 21      # Number of the last context of the first range (included)

# Second range
CONTEXT_START_2 = 29    # Number of the first context of the second range (included)
CONTEXT_END_2 = 34      # Number of the last context of the second range (included)
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

    # Range validation
    if CONTEXT_START_1 > CONTEXT_END_1:
        print(f"Error: CONTEXT_START_1 ({CONTEXT_START_1}) must be <= CONTEXT_END_1 ({CONTEXT_END_1}).")
        sys.exit(1)
    if CONTEXT_START_2 > CONTEXT_END_2:
        print(f"Error: CONTEXT_START_2 ({CONTEXT_START_2}) must be <= CONTEXT_END_2 ({CONTEXT_END_2}).")
        sys.exit(1)

    # We load the VNF map only once for efficiency
    catalogo_json = os.path.join(cartella_base, "catalogoVNF.json")
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
        print(f"VNF catalog loaded: {len(mappa_vnf)} VNFs found.")
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalogo_json}. Text will not be enriched.")
        mappa_vnf = {}

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Build the context list from the two ranges
    contesti_da_processare = list(range(CONTEXT_START_1, CONTEXT_END_1 + 1)) + \
                             list(range(CONTEXT_START_2, CONTEXT_END_2 + 1))

    nome_file_jsonl = os.path.join(
        output_dir,
        f"dataset_train_context{CONTEXT_START_1}-{CONTEXT_END_1}_{CONTEXT_START_2}-{CONTEXT_END_2}.jsonl"
    )

    print(f"Training dataset creation for two context ranges:")
    print(f"  Range 1: context{CONTEXT_START_1} - context{CONTEXT_END_1}")
    print(f"  Range 2: context{CONTEXT_START_2} - context{CONTEXT_END_2}")
    print(f"For each context, all 3 schemas will be included: A, B, C")

    with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
        count = 0
        contesti_trovati = 0

        for i in contesti_da_processare:
            nome_cartella = f"context{i}"
            percorso_cartella = os.path.join(cartella_base, nome_cartella)
            percorso_pl = os.path.join(percorso_cartella, nome_file_pl)

            if not os.path.exists(percorso_cartella):
                print(f"  [SKIP] {nome_cartella} - folder not found.")
                continue

            if not os.path.exists(percorso_pl):
                print(f"  [SKIP] {nome_cartella} - {nome_file_pl} not found.")
                continue

            with open(percorso_pl, "r", encoding="utf-8") as f_pl:
                codice_prolog = f_pl.read().strip()

            contesti_trovati += 1

            for nome_txt in schemi:
                percorso_txt = os.path.join(percorso_cartella, nome_txt)

                if os.path.exists(percorso_txt):
                    with open(percorso_txt, "r", encoding="utf-8") as f_txt:
                        testo_naturale = f_txt.read().strip()

                    # Enrich the text with the hardware values of the VNF catalog
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
                    print(f"  [WARN] {nome_cartella}/{nome_txt} not found.")

    print(f"\n[OK] Created {nome_file_jsonl}")
    print(f"     Processed contexts: {contesti_trovati}")
    print(f"       Intervallo 1: context{CONTEXT_START_1}-{CONTEXT_END_1}")
    print(f"       Intervallo 2: context{CONTEXT_START_2}-{CONTEXT_END_2}")
    print(f"     Total rows: {count} (3 schemas x {contesti_trovati} contexts)")

if __name__ == "__main__":
    main()

