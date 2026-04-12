from unsloth import FastLanguageModel
import torch

# 1. Carichiamo il modello base + il TUO modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "modello_ibn_prolog", # Carica la tua cartella!
    max_seq_length = 2048,
    load_in_4bit = True,
)
FastLanguageModel.for_inference(model) # Lo prepariamo per rispondere

# 2. Prepariamo la domanda (puoi cambiare il testo in 'input')
prompt_template = """Di seguito è riportata un'istruzione che descrive un task, seguita da un input. Scrivi la risposta adeguata.

### Instruction:
Traduci la richiesta dell'operatore di rete nel codice Prolog corrispondente.

### Input:
{}

### Response:
{}"""

richiesta = "The healthcare provider healthAdminOp requires a service to manage 1000 remote monitors. The service chain includes, in order: a patient sensor allocated at the edge, a medical analyzer allocated at the edge, and a health database located in the cloud. Regarding requirements, it is a mandatory requirement that the latency from the sensor to the analyzer remains below 10 milliseconds. Furthermore, it is preferred that the patient sensor and the medical analyzer operate on the same node."

inputs = tokenizer(
    [prompt_template.format(richiesta, "")], 
    return_tensors = "pt"
).to("cuda")

# 3. Generiamo la risposta
outputs = model.generate(**inputs, max_new_tokens = 1024)
risposta = tokenizer.batch_decode(outputs)

# Puliamo la risposta per vedere solo la parte Prolog
print("\n--- RISPOSTA DEL MODELLO ---")
print(risposta[0].split("### Response:")[1].strip())