import subprocess
import os
import re

def trova_intent_id(percorso_file):
    pattern = re.compile(r"intent\(\s*'?([a-zA-Z0-9_]+)'?\s*,")
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            for riga in f:
                match = pattern.search(riga)
                if match:
                    return match.group(1)
    except FileNotFoundError:
        return None
    return None

def trova_target_list(percorso_file):
    """Estrae la lista delle VNF dal predicato target/2."""
    pattern = re.compile(r"target\([^,]+,\s*\[(.*?)\]\)")
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            for riga in f:
                match = pattern.search(riga)
                if match:
                    # Rimuoviamo gli spazi e creiamo una lista pulita
                    vnfs = [v.strip() for v in match.group(1).split(',')]
                    return vnfs
    except FileNotFoundError:
        return []
    return []

def DipsExecutor(CARTELLA_DIPS, FILE_PL, FILE_TXT_OUTPUT):
    print(f"\n⚙️ Avvio esecuzione singola per: {os.path.basename(FILE_PL)}")

    intent_id = trova_intent_id(FILE_PL)
    if not intent_id:
        print("❌ Errore: Impossibile trovare l'intent ID nel file.")
        return

    print(f"🔍 Intent ID trovato: {intent_id}")

    # Estraiamo la "Stele di Rosetta" (il target)
    target_list = trova_target_list(FILE_PL)
    target_str = ",".join(target_list) if target_list else "NESSUN_TARGET"
    print(f"🎯 Target trovati: {target_str}")

    goal = f"consult('{FILE_PL}'), dips('{intent_id}', Output), writeln(Output)."
    
    comando = [
        "swipl", "-q",
        "-s", "dips.pl", 
        "-g", goal,      
        "-t", "halt"
    ]

    print("⏳ Lancio Prolog... attendere.")

    try:
        risultato = subprocess.run(
            comando,
            cwd=CARTELLA_DIPS,
            capture_output=True,
            text=True,
            timeout=15
        )

        stdout_pulito = risultato.stdout.strip()
        stderr_pulito = risultato.stderr.strip()

        with open(FILE_TXT_OUTPUT, 'w', encoding='utf-8') as f:
            # 1. SCRIVIAMO L'INTESTAZIONE NELLA PRIMA RIGA
            f.write(f"TARGET:{target_str}\n")
            
            # 2. SCRIVIAMO L'OUTPUT PROLOG DALLA SECONDA RIGA
            if stderr_pulito and ("ERROR:" in stderr_pulito or "Syntax error" in stderr_pulito):
                print("❌ Trovato errore Prolog! Lo salvo nel TXT.")
                f.write(f"ERRORE:\n{stderr_pulito}")
                
            elif stdout_pulito:
                if stdout_pulito == "false":
                    print(f"⚠️ DIPS non ha trovato nessuna soluzione! Salvato 'false' in -> {FILE_TXT_OUTPUT}")
                else:
                    print(f"✅ Fatto! Soluzioni trovate e salvate in -> {FILE_TXT_OUTPUT}")
                f.write(stdout_pulito)
                
            else:
                print("⚠️ Errore anomalo: Nessun output generato. Prolog potrebbe essere crashato.")
                f.write("NESSUN_OUTPUT")
                
    except subprocess.TimeoutExpired:
        print("❌ Esecuzione interrotta per TIMEOUT (oltre 15 secondi).")
        with open(FILE_TXT_OUTPUT, 'w', encoding='utf-8') as f:
            f.write("TARGET:NESSUN_TARGET\nERRORE_TIMEOUT")


if __name__ == "__main__":
    # Percorso all'installazione di DIPS
    CARTELLA_DIPS = "/home/nick/Scrivania/Tesi_git/dips"
    
    # Percorso della directory base che contiene le cartelle context1, context2, ..., context30
    BASE_DIR = "/home/nick/Scrivania/Tesi_git/IBN_tesi_n.baicchi/intenti2.0" 

    # Ciclo per entrare in context1 fino a context30
    for i in range(1, 31):
        context_folder = f"context{i}"
        
        # Costruisce il percorso per il file Prolog in ingresso
        file_pl = os.path.join(BASE_DIR, context_folder, "facts.pl")
        
        # NUOVO: Costruisce il percorso per il file di output SALVANDOLO NELLA CARTELLA DEL CONTESTO
        file_txt_output = os.path.join(BASE_DIR, context_folder, "resultDips.txt")
        
        print(f"\n=======================================================")
        print(f"Inizio elaborazione per: {context_folder}")
        
        if os.path.exists(file_pl):
            DipsExecutor(CARTELLA_DIPS, file_pl, file_txt_output)
        else:
            print(f"⚠️ ATTENZIONE: Il file {file_pl} non esiste. Salto l'esecuzione per {context_folder}.")