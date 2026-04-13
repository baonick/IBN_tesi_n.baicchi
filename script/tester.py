from unsloth import FastLanguageModel
import torch

import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

INSTRUCTION = """You are an expert Intent-Based Networking (IBN) engineer and a Prolog programmer.
Your task is to translate the operator's natural language requirements into formal Prolog facts.

Follow these strict rules:
1. Extract parameters from the input. Generate identifiers for both the Intent ID and VNF names by combining key descriptive words from the text (e.g., 'smart grid' -> 'smartGridIntent'; 'mountain controller' -> 'mountainControllerVF'). Do not invent operator names or service IDs, extract them directly from text.
2. Structure the output strictly with these facts in order:
   - intent(IntentId, Operator, Users, Service).
   - propertyExpectation(PropId, IntentId, PropertyType, Requirement, Type, Param1, Param2). 
     You must support all property types described: latency, affinity (e.g., same, dedicated), caching, security, privacy, logging, encoding, decoding, bandwidth, and any others mentioned.
     - For Requirement: use the specific value (e.g., 'caching', '30', 'same').
     - For Type: specify if it is 'hard' (mandatory) or 'soft' (preferred).
   - target(Service, [VNF_List]).
   - vnf(VnfName, Location, Resources).
   - vnfXUser(VnfName, Size, UserRange, Capacity). You MUST generate exactly one vnfXUser fact for EVERY single VNF defined in the target list.
3. Ensure perfectly valid Prolog syntax. Use lowercase for atoms where appropriate and end every fact with a period (.).
4. Output ONLY the Prolog code. No explanations."""

#programma per provare il modello addestrato 

# 1. Carichiamo il modello base + il TUO modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "modello_ibn_prolog", # Carica la tua cartella!
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

richiesta = "The healthcare provider healthAdminOp requires a service to manage 1000 remote monitors. The service chain includes, in order: a patient sensor allocated at the edge, a medical analyzer allocated at the edge, and a health database located in the cloud. Regarding requirements, it is a mandatory requirement that the latency from the sensor to the analyzer remains below 10 milliseconds. Furthermore, it is preferred that the patient sensor and the medical analyzer operate on the same node."

inputs = tokenizer(
    [prompt_template.format(INSTRUCTION, richiesta, "")],
    return_tensors = "pt"
).to("cuda")

# 3. Generiamo la risposta
outputs = model.generate(**inputs, max_new_tokens = 1024)
risposta = tokenizer.batch_decode(outputs)

# Puliamo la risposta per vedere solo la parte Prolog
print("\n--- RISPOSTA DEL MODELLO ---")
print(risposta[0].split("### Response:")[1].strip())