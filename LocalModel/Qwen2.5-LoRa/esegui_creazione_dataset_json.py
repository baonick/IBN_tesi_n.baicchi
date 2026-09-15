import os
import sys
import subprocess

# Configurazione: prefissi dei file da cercare ed eseguire nelle rispettive sottocartelle
# Puoi aggiungere o modificare i prefissi qui. Lo script cercherà i file .py
# che iniziano con questi nomi all'interno delle cartelle specificate.
SCRIPT_PREFIXES = {
    "test": ["crea_json", "crea_dataset"],
    "tester": ["crea_json", "crea_dataset"],  # A volte la cartella si chiama 'tester'
    "train": ["creaDataset", "crea_dataset", "crea_json"] 
}

def main():
    # Prende la cartella base (es. '5-fold-llama-3.1-8b-onServer' o '5-fold-on-context')
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # Se non specificata, usa la cartella in cui si trova questo script
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    base_dir = os.path.abspath(base_dir)
    print(f"Inizio esplorazione ricorsiva cartella base: {base_dir}")
    
    if not os.path.exists(base_dir):
        print(f"La cartella specificata non esiste: {base_dir}")
        sys.exit(1)
    
    # os.walk esplora ricorsivamente tutte le cartelle e sottocartelle
    for root, dirs, files in os.walk(base_dir):
        # Salta cartelle di sistema o cache (modifica dirs in-place per non entrarci proprio)
        dirs[:] = [d for d in dirs if not d.startswith("__")]
        
        # Estraiamo i nomi di tutte le cartelle padre del percorso corrente
        path_parts = root.split(os.sep)
        
        # Determiniamo quali prefissi sono validi per la cartella corrente
        applicable_prefixes = set()
        for folder_name, prefixes in SCRIPT_PREFIXES.items():
            if folder_name in path_parts:
                applicable_prefixes.update(prefixes)
                
        # Se non siamo in una sottocartella di test/tester/train, saltiamo
        if not applicable_prefixes:
            continue
            
        # Cerchiamo ed eseguiamo i file .py che matchano i prefissi
        for filename in sorted(files):
            if filename.endswith(".py"):
                for prefix in applicable_prefixes:
                    if filename.startswith(prefix):
                        script_path = os.path.join(root, filename)
                        print(f"\n{'='*60}")
                        print(f" TROVATO SCRIPT: {filename}")
                        print(f" CARTELLA:       {root}")
                        print(f"{'='*60}")
                        
                        # Esegue lo script impostando la working directory a `root`
                        result = subprocess.run([sys.executable, filename], cwd=root)
                        
                        if result.returncode != 0:
                            print(f"!!! ERRORE durante l'esecuzione di {filename} in {root}")
                        else:
                            print(f"---> {filename} eseguito con successo.")
                        
                        # Evita di eseguire due volte lo stesso file se matcha più prefissi
                        break 

    print(f"\n{'*'*60}\nESECUZIONE GLOBALE TERMINATA\n{'*'*60}")

if __name__ == "__main__":
    main()
