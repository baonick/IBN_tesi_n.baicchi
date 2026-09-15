from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import json
import os
import time
from datetime import datetime

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# System instruction (must be identical to the one used in train_qwen.py)
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

# --- PHASE 1: LOADING THE TRAINED MODEL ---
# MODIFY HERE: insert the path of the trained model folder
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "qwen2.5-7b-1-21_29-34",
    max_seq_length = 2048,
    load_in_4bit = False,
)

# Apply the same chat template used during training
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
)

FastLanguageModel.for_inference(model)  # Optimize the model for inference

# --- PHASE 2: LOADING THE JSON FILE WITH REQUESTS ---
# MODIFY HERE: insert the path of the test JSON file
percorso_json = "test_context22-28.json"
cartella_output = "../result"

# Create the output folder if it doesn't exist
if not os.path.exists(cartella_output):
    os.makedirs(cartella_output)

try:
    with open(percorso_json, "r", encoding="utf-8") as f:
        richieste = json.load(f)
except FileNotFoundError:
    print(f"Error: The file '{percorso_json}' was not found.")
    richieste = []

print(f"Found {len(richieste)} requests to process.")

# Dictionary to collect execution times
tempi_esecuzione = {}

# --- PHASE 3: PROCESSING EACH REQUEST ---
for i, item in enumerate(richieste):
    # Handles both a list of strings and a list of JSON dictionaries
    if isinstance(item, dict):
        testo_richiesta = item.get("input", item.get("richiesta", item.get("text", str(item))))
        nome_file = f"output_{item.get('id', i+1)}.txt"
    else:
        testo_richiesta = str(item)
        nome_file = f"output_{i+1}.txt"

    print(f"[{i+1}/{len(richieste)}] Processing request in progress...")

    # Measure inference execution time
    timestamp_inizio = datetime.now()
    tempo_inizio = time.time()

    # Build the conversation in the native chat format of Qwen 2.5
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": testo_richiesta},
    ]

    # Apply the chat template and tokenize
    prompt = tokenizer.apply_chat_template(
        conversation,
        tokenize = False,
        add_generation_prompt = True,  # Adds <|im_start|>assistant\n to start generation
    )

    inputs = tokenizer(
        [prompt],
        return_tensors = "pt",
    ).to("cuda")

    # Generate the response
    outputs = model.generate(**inputs, max_new_tokens = 2048)
    risposta = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # End time measurement
    tempo_fine = time.time()
    timestamp_fine = datetime.now()
    durata_secondi = round(tempo_fine - tempo_inizio, 4)

    # Clean the response: extract only the last assistant message
    try:
        # With the Qwen 2.5 format, the assistant's response follows the last "assistant\n"
        risposta_completa = risposta[0]
        # Look for the last occurrence of the assistant role in the decoded text
        parti = risposta_completa.rsplit("assistant\n", 1)
        if len(parti) > 1:
            risposta_pulita = parti[-1].strip()
        else:
            # Fallback: let's try with the Alpaca format just in case
            risposta_pulita = risposta_completa.split("### Response:")[-1].strip()
    except (IndexError, AttributeError):
        risposta_pulita = risposta[0].strip()  # Generic fallback

    # --- PHASE 4: SAVING IN A SEPARATE TXT FILE ---
    percorso_salvataggio = os.path.join(cartella_output, nome_file)
    with open(percorso_salvataggio, "w", encoding="utf-8") as f_out:
        f_out.write(risposta_pulita)

    # Save the execution time for this file
    tempi_esecuzione[nome_file] = {
        "durata_secondi": durata_secondi,
        "timestamp_inizio": timestamp_inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_fine": timestamp_fine.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print(f"    Execution time: {durata_secondi:.4f}s")

# --- PHASE 5: SAVING EXECUTION TIMES FILE ---
percorso_tempi = os.path.join(cartella_output, "tempi_esecuzione.json")
with open(percorso_tempi, "w", encoding="utf-8") as f_tempi:
    json.dump(tempi_esecuzione, f_tempi, indent=2, ensure_ascii=False)

print(f"\nProcessing completed. All results have been saved in '{cartella_output}/'.")
print(f"Execution times file saved in: {percorso_tempi}")
