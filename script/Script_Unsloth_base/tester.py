
from unsloth import FastLanguageModel
import torch

import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

INSTRUCTION = """"""

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

import json

# 2. Caricamento del file JSON con le richieste
percorso_json = "richieste.json"  # Modifica questo con il nome del tuo file JSON
cartella_output = "risultati_test"

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