import os
import json

#programma che crea il dataset in formato jsonl tramite l'ordinamento a cartelle definito 


# 1. La nostra istruzione fissa per il modello
INSTRUCTION = """"""

# 2. Il nome del file che vogliamo creare
nome_file_jsonl = "dataset.jsonl"
cartella_base = "intenti2.0"
numero_totale_contesti = 30 # Da context1 a context30

opzioni_testo = ["intentA.txt", "intentB.txt", "intentC.txt"]
nome_file_pl = "facts.pl"

print(f"Inizio la scansione di {numero_totale_contesti} cartelle in {cartella_base}...")

# Apriamo il file jsonl in modalità scrittura ("w")
with open(nome_file_jsonl, "w", encoding="utf-8") as f_out:
    
    # Un ciclo che va da 1 a 30
    for i in range(1, numero_totale_contesti + 1):
        nome_cartella = f"context{i}"
        percorso_cartella = os.path.join(cartella_base, nome_cartella)
        percorso_pl = os.path.join(percorso_cartella, nome_file_pl)
        
        # Controlliamo che il file .pl esista davvero per evitare errori
        if os.path.exists(percorso_pl):
            
            # Leggiamo il codice Prolog (OUTPUT) che sarà uguale per tutte le 3 varianti
            with open(percorso_pl, "r", encoding="utf-8") as f_pl:
                codice_prolog = f_pl.read().strip()
                
            # Iteriamo sulle 3 opzioni di testo (INPUT)
            for nome_txt in opzioni_testo:
                percorso_txt = os.path.join(percorso_cartella, nome_txt)
                
                if os.path.exists(percorso_txt):
                    with open(percorso_txt, "r", encoding="utf-8") as f_txt:
                        testo_naturale = f_txt.read().strip()
                        
                    # 3. Assembliamo il nostro dizionario JSON
                    riga_json = {
                        "instruction": INSTRUCTION,
                        "input": testo_naturale,
                        "output": codice_prolog
                    }
                    
                    # 4. Scriviamo la riga nel file JSONL
                    f_out.write(json.dumps(riga_json, ensure_ascii=False) + "\n")
                    
            print(f"  [OK] Elaborata {nome_cartella}")
            
        else:
            print(f"  [ATTENZIONE] File {nome_file_pl} mancante in {nome_cartella}. Salto la cartella.")

print(f"\nOperazione completata! Creato il file {nome_file_jsonl} pronto per l'addestramento.")