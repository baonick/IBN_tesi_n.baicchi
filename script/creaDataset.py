import os
import json

#programma che crea il dataset in formato jsonl tramite l'ordinamento a cartelle definito 


# 1. La nostra istruzione fissa per il modello
# 1. La nostra istruzione fissa per il modello
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

# 2. Il nome del file che vogliamo creare
nome_file_jsonl = "dataset.jsonl"
numero_totale_intenti = 23 # Da intent0 a intent22

print(f"Inizio la scansione di {numero_totale_intenti} cartelle...")

# Apriamo il file jsonl in modalità scrittura ("w")
with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
    
    # Un ciclo che va da 0 a 22
    for i in range(numero_totale_intenti):
        nome_cartella = f"intent{i}"
        
        # Costruiamo i percorsi ai file (es: intent0/intent0.txt)
        percorso_txt = os.path.join(nome_cartella, f"{nome_cartella}.txt")
        percorso_pl = os.path.join(nome_cartella, f"{nome_cartella}.pl")
        
        # Controlliamo che la cartella e i file esistano davvero per evitare errori
        if os.path.exists(percorso_txt) and os.path.exists(percorso_pl):
            
            # Leggiamo il testo naturale (INPUT)
            with open(percorso_txt, "r", encoding="utf-8") as f_txt:
                # .read() legge tutto il file, .strip() toglie eventuali spazi o a capo vuoti alla fine
                testo_naturale = f_txt.read().strip()
                
            # Leggiamo il codice Prolog (OUTPUT)
            with open(percorso_pl, "r", encoding="utf-8") as f_pl:
                codice_prolog = f_pl.read().strip()
                
            # 3. Assembliamo il nostro dizionario JSON perfetto
            riga_json = {
                "instruction": INSTRUCTION,
                "input": testo_naturale,
                "output": codice_prolog
            }
            
            # 4. Scriviamo la riga nel file JSONL
            # json.dumps converte il dizionario Python in una stringa JSON
            f_out.write(json.dumps(riga_json, ensure_ascii=False) + "\n")
            print(f"  [OK] Elaborata {nome_cartella}")
            
        else:
            print(f"  [ATTENZIONE] File mancanti in {nome_cartella}. Salto la cartella.")

print(f"\nOperazione completata! Creato il file {nome_file_jsonl} pronto per l'addestramento.")