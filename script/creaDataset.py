import os
import json

# 1. La nostra istruzione fissa per il modello
INSTRUCTION = "Traduci la richiesta dell'operatore di rete nel codice Prolog corrispondente."

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