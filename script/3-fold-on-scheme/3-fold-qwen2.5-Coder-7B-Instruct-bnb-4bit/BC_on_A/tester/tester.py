
from unsloth import FastLanguageModel
import torch

import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

INSTRUCTION = """Translate the natural language network intent into formal Prolog facts using the following strict schema:
1. Intent: intent(IntentID, ProviderOp, NumUsers, ServiceName). (camelCase; IntentID ends in 'Intent', ProviderOp in 'Op').
2. Target: target(ServiceName, [vnf1, vnf2, ...]). (VNFs in camelCase ending in 'VF').
3. Nodes: For each VNF, write vnf(VnfID, edge/cloud, HardwareValue) and vnfXUser(VnfID, s/m/l, (1, NumUsers), ComputingValue).
4. Non-Changing Properties (9 params): propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF). (Used for totChainHW, affinity, bandwidth, latency. Map 'must' to 'hard', 'prefer' to 'soft').
5. Changing Properties (6 params): propertyExpectation(PropID, IntentID, Type, _, Source, Destination). (Used for security, decoding, logging, etc. Parameter 4 is always a wildcard '_').
   - 'after VnfID': VnfID is the Source (5th param), Destination (6th param) is '_'.
   - 'before VnfID': VnfID is the Destination (6th param), Source (5th param) is '_'.
Generate ONLY the valid Prolog code. No explanations."""

#programma per provare il modello addestrato 

# 1. Carichiamo il modello base + il TUO modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "qwen2.5-Coder-7B-Instruct-trainOn-BC", # Carica la tua cartella!
    max_seq_length = 2048,
    load_in_4bit = True,
)
FastLanguageModel.for_inference(model) # Lo prepariamo per rispondere

# 2. Prepariamo la domanda (puoi cambiare il testo in 'input')
prompt_template = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

import json

# 2. Caricamento del file JSON con le richieste
percorso_json = "test_intentA.json"  # Modifica questo con il nome del tuo file JSON
cartella_output = "../result"

# Crea la cartella per gli output se non esiste
if not os.path.exists(cartella_output):
    os.makedirs(cartella_output)

try:
    with open(percorso_json, "r", encoding="utf-8") as f:
        richieste = json.load(f)
except FileNotFoundError:
    print(f"Errore: Il file '{percorso_json}' non è stato trovato.")
    richieste = []

print(f"Trovate {len(richieste)} richieste da elaborare.")

# 3. Ciclo per elaborare ogni richiesta
for i, item in enumerate(richieste):
    # Gestisce sia una lista di stringhe che una lista di dizionari JSON
    if isinstance(item, dict):
        # Cerca i campi più comuni, altrimenti converte l'oggetto in stringa
        testo_richiesta = item.get("input", item.get("richiesta", item.get("text", str(item))))
        nome_file = f"output_{item.get('id', i+1)}.txt"
    else:
        testo_richiesta = str(item)
        nome_file = f"output_{i+1}.txt"

    print(f"[{i+1}/{len(richieste)}] Elaborazione richiesta in corso...")

    inputs = tokenizer(
        [prompt_template.format(INSTRUCTION, testo_richiesta, "")],
        return_tensors = "pt"
    ).to("cuda")

    # Generiamo la risposta
    outputs = model.generate(**inputs, max_new_tokens = 1024)
    risposta = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # Puliamo la risposta per vedere solo la parte Prolog
    try:
        risposta_pulita = risposta[0].split("### Response:")[1].strip()
    except IndexError:
        risposta_pulita = risposta[0].strip() # Fallback

    # 4. Salvataggio in un file txt separato
    percorso_salvataggio = os.path.join(cartella_output, nome_file)
    with open(percorso_salvataggio, "w", encoding="utf-8") as f_out:
        f_out.write(risposta_pulita)
        
print(f"\nElaborazione completata. Tutti i risultati sono stati salvati in '{cartella_output}/'.")