import os
import sys
import subprocess

def run_script_in_dir(script_name, dir_path):
    if not os.path.exists(dir_path):
        print(f"Cartella non trovata: {dir_path}")
        return False
    
    script_path = os.path.join(dir_path, script_name)
    if not os.path.exists(script_path):
        print(f"Script non trovato: {script_path}")
        return False
        
    print(f"\n---> Esecuzione di {script_name} nella cartella {os.path.basename(dir_path)}...")
    
    # Esegue lo script impostando la working directory a dir_path (come se l'utente vi fosse entrato da terminale)
    result = subprocess.run([sys.executable, script_name], cwd=dir_path)
    
    if result.returncode != 0:
        print(f"!!! Errore durante l'esecuzione di {script_name} in {dir_path}")
        return False
    return True

def main():
    # Se viene passata una cartella come argomento, la usiamo, altrimenti usiamo la cartella corrente
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        base_dir = "."
        
    base_dir = os.path.abspath(base_dir)
    print(f"Inizio pipeline sulla cartella base: {base_dir}")
    
    # Trova tutte le sottocartelle nella cartella base
    subdirs = [os.path.join(base_dir, d) for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    if not subdirs:
        print("Nessuna sottocartella trovata.")
        return
        
    for subdir in subdirs:
        # Se c'è una cartella che si chiama __pycache__ o simili la saltiamo
        if os.path.basename(subdir).startswith("__"):
            continue
            
        print(f"\n{'='*60}")
        print(f" INIZIO ELABORAZIONE FOLD: {os.path.basename(subdir)}")
        print(f"{'='*60}")
        
        # 1. Esegui train.py in train/
        train_dir = os.path.join(subdir, "train")
        if not run_script_in_dir("train.py", train_dir):
            print(f"Interruzione pipeline per {os.path.basename(subdir)}.")
            continue
            
        # 2. Esegui tester.py in tester/
        tester_dir = os.path.join(subdir, "tester")
        if not run_script_in_dir("tester.py", tester_dir):
            print(f"Interruzione pipeline per {os.path.basename(subdir)}.")
            continue
            
        
        print(f"\n>>> Completato con SUCCESSO per: {os.path.basename(subdir)}")
        
    print(f"\n{'*'*60}\nPIPELINE GLOBALE TERMINATA\n{'*'*60}")

if __name__ == "__main__":
    main()
