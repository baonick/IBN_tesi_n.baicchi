from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import json
import os
import time
from datetime import datetime

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Istruzione di sistema (deve essere identica a quella usata in train_qwen.py)
SYSTEM_PROMPT = """ROLE AND OBJECTIVE
You are an expert networking logic parser. Your task is to extract information from a natural language network intent and translate it into formal Prolog facts using ONLY the strictly defined schema below. You must not hallucinate, invent, or assume any information outside the provided text.


STEP 1: VNF CHAIN IDENTIFICATION & GROUNDING
- Identify the exact chain of Virtual Network Functions (VNFs) explicitly requested in the input text.
- This VNF chain constitutes the list of VNFs inside the target fact:
  target(ServiceName, [vnf1, vnf2, ...]).
- CRITICAL: For all subsequent Prolog facts (vnf, vnfXUser, propertyExpectation), you MUST USE ONLY the VNFs from this exact target list.


STEP 2: VOCABULARY AND KEYWORD MAPPING

Strictness Mapping:
- "must", "strictly", "required", "guaranteeing", "ensuring", "mandatory" -> hard
- "prefer", "optimally", "should", "desired", "if possible" -> soft

Operator Mapping:
- "greater than", "higher than", "above" -> greater
- "lower than", "below", "less than" -> lower

Unit Mapping:
- "Mbps", "megabps" -> megabps
- "ms", "milliseconds" -> ms
- "GB", "gigabytes" -> gb


STEP 3: TOPOLOGY AND PROPERTY MAPPING (BEFORE vs AFTER)
When mapping Changing Properties (like security, decoding, etc.), topology depends on the preposition in the text.
Use the underscore "_" to denote an empty or unspecified argument.

- AFTER Rule:
  If "[Service] AFTER [VnfID]", Source is VnfID and Destination is "_".
  Template: propertyExpectation(PropID, IntentID, Type, _, VnfID, _).

- BEFORE Rule:
  If "[Service] BEFORE [VnfID]", Source is "_" and Destination is VnfID.
  Template: propertyExpectation(PropID, IntentID, Type, _, _, VnfID).


STEP 4: STRICT PROLOG SCHEMA DEFINITIONS
Generate the output using EXACTLY these formats. Do not add extra parameters. Note on PropIDs: You must invent unique identifiers for each PropID (e.g., prop1, prop2, prop3). These identifiers have no semantic meaning in the results, but they must be strictly unique within your generated response.

1. Intent & Target:
- intent(IntentID, ProviderOp, NumUsers, ServiceName).
  (Note: IntentID must end in 'Intent', ProviderOp in 'Op')
- target(ServiceName, [vnf1, vnf2, ...]).

2. Nodes (Hardware & Computing):
- vnf(VnfID, edge/cloud, HardwareValue).
- vnfXUser(VnfID, l, (1, NumUsers), HardwareValue).

3. Non-Changing Properties (Expects EXACTLY 9 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF).
- Valid Types: bandwidth, latency, totChainHW, affinity
- Affinity Values: dedicated, same
- Note: For affinity and totChainHW, use "_" for Operator, Value, Unit, Source, or Dest where not applicable.

4. Changing Properties (Expects EXACTLY 6 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, _, Source, Destination).
- Note: The 4th parameter is ALWAYS "_".
- Valid Types: security, compression, logging, privacy, caching, decoding, encoding


FINAL OUTPUT INSTRUCTION
Return ONLY the generated Prolog facts.
Do not include introductory text, conversational filler, or explanations.
"""

# --- FASE 1: CARICAMENTO DEL MODELLO ADDESTRATO ---
# MODIFICA QUI: inserisci il percorso della cartella del modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-Coder-7B-Instruct",
    max_seq_length = 8192,
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
percorso_json = "test_context1-34.json"
cartella_output = "./result"

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
    outputs = model.generate(**inputs, max_new_tokens = 8192)
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
