from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import json
import os
import time
from datetime import datetime

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Istruzione di sistema (deve essere identica a quella usata in train_qwen.py)
SYSTEM_PROMPT = """Translate the natural language network intent into formal Prolog facts using the strictly defined schema below.

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

# --- FASE 1: CARICAMENTO DEL MODELLO ADDESTRATO ---
# MODIFICA QUI: inserisci il percorso della cartella del modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "qwen2.5-7b-1-28",
    max_seq_length = 2048,
    load_in_4bit = False,
)

# Applichiamo lo stesso chat template usato durante il training
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
)

FastLanguageModel.for_inference(model)  # Ottimizza il modello per l'inferenza

# --- FASE 2: CARICAMENTO DEL FILE JSON CON LE RICHIESTE ---
# MODIFICA QUI: inserisci il percorso del file JSON di test
percorso_json = "test_context29-34.json"
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

# Dizionario per raccogliere i tempi di esecuzione
tempi_esecuzione = {}

# --- FASE 3: ELABORAZIONE DI OGNI RICHIESTA ---
for i, item in enumerate(richieste):
    # Gestisce sia una lista di stringhe che una lista di dizionari JSON
    if isinstance(item, dict):
        testo_richiesta = item.get("input", item.get("richiesta", item.get("text", str(item))))
        nome_file = f"output_{item.get('id', i+1)}.txt"
    else:
        testo_richiesta = str(item)
        nome_file = f"output_{i+1}.txt"

    print(f"[{i+1}/{len(richieste)}] Elaborazione richiesta in corso...")

    # Misuriamo il tempo di esecuzione dell'inferenza
    timestamp_inizio = datetime.now()
    tempo_inizio = time.time()

    # Costruiamo la conversazione nel formato chat nativo di Qwen 2.5
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": testo_richiesta},
    ]

    # Applichiamo il chat template e tokenizziamo
    prompt = tokenizer.apply_chat_template(
        conversation,
        tokenize = False,
        add_generation_prompt = True,  # Aggiunge <|im_start|>assistant\n per far partire la generazione
    )

    inputs = tokenizer(
        [prompt],
        return_tensors = "pt",
    ).to("cuda")

    # Generiamo la risposta
    outputs = model.generate(**inputs, max_new_tokens = 2048)
    risposta = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # Fine misurazione tempo
    tempo_fine = time.time()
    timestamp_fine = datetime.now()
    durata_secondi = round(tempo_fine - tempo_inizio, 4)

    # Puliamo la risposta: estraiamo solo l'ultimo messaggio dell'assistant
    try:
        # Con il formato Qwen 2.5 la risposta dell'assistant segue l'ultimo "assistant\n"
        risposta_completa = risposta[0]
        # Cerchiamo l'ultima occorrenza del ruolo assistant nel testo decodificato
        parti = risposta_completa.rsplit("assistant\n", 1)
        if len(parti) > 1:
            risposta_pulita = parti[-1].strip()
        else:
            # Fallback: proviamo con il formato Alpaca nel caso
            risposta_pulita = risposta_completa.split("### Response:")[-1].strip()
    except (IndexError, AttributeError):
        risposta_pulita = risposta[0].strip()  # Fallback generico

    # --- FASE 4: SALVATAGGIO IN UN FILE TXT SEPARATO ---
    percorso_salvataggio = os.path.join(cartella_output, nome_file)
    with open(percorso_salvataggio, "w", encoding="utf-8") as f_out:
        f_out.write(risposta_pulita)

    # Salva il tempo di esecuzione per questo file
    tempi_esecuzione[nome_file] = {
        "durata_secondi": durata_secondi,
        "timestamp_inizio": timestamp_inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_fine": timestamp_fine.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print(f"    Tempo di esecuzione: {durata_secondi:.4f}s")

# --- FASE 5: SALVATAGGIO FILE TEMPI DI ESECUZIONE ---
percorso_tempi = os.path.join(cartella_output, "tempi_esecuzione.json")
with open(percorso_tempi, "w", encoding="utf-8") as f_tempi:
    json.dump(tempi_esecuzione, f_tempi, indent=2, ensure_ascii=False)

print(f"\nElaborazione completata. Tutti i risultati sono stati salvati in '{cartella_output}/'.")
print(f"File tempi di esecuzione salvato in: {percorso_tempi}")
