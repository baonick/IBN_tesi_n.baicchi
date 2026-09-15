import os
import sys
import subprocess


def main():
    # Se viene passata una cartella come argomento, la usiamo, altrimenti usiamo la cartella dello script
    if len(sys.argv) > 1:
        base_dir = os.path.abspath(sys.argv[1])
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"{'*'*60}")
    print(f" ESECUZIONE PIPELINE SU TUTTE LE SOTTO-CARTELLE")
    print(f" Cartella base: {base_dir}")
    print(f"{'*'*60}")
    
    # Trova tutte le sotto-cartelle che contengono esegui_pipeline.py
    sottocartelle = sorted([
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        and not d.startswith("__")
        and os.path.exists(os.path.join(base_dir, d, "esegui_pipeline.py"))
    ])
    
    if not sottocartelle:
        print("\nNessuna sotto-cartella con esegui_pipeline.py trovata.")
        return
    
    print(f"\nTrovate {len(sottocartelle)} cartelle da elaborare:")
    for i, nome in enumerate(sottocartelle, 1):
        print(f"  {i}. {nome}")
    
    successi = 0
    fallimenti = 0
    
    for i, nome_cartella in enumerate(sottocartelle, 1):
        dir_path = os.path.join(base_dir, nome_cartella)
        
        print(f"\n{'='*60}")
        print(f" [{i}/{len(sottocartelle)}] AVVIO PIPELINE: {nome_cartella}")
        print(f"{'='*60}")
        
        # Esegue esegui_pipeline.py nella sotto-cartella
        result = subprocess.run(
            [sys.executable, "esegui_pipeline.py"],
            cwd=dir_path
        )
        
        if result.returncode != 0:
            print(f"\n!!! ERRORE nella pipeline di: {nome_cartella}")
            fallimenti += 1
        else:
            print(f"\n>>> COMPLETATO CON SUCCESSO: {nome_cartella}")
            successi += 1
    
    # Riepilogo finale
    print(f"\n{'*'*60}")
    print(f" RIEPILOGO ESECUZIONE GLOBALE")
    print(f"{'*'*60}")
    print(f"  Totale cartelle elaborate: {len(sottocartelle)}")
    print(f"  Successi: {successi}")
    print(f"  Fallimenti: {fallimenti}")
    print(f"{'*'*60}")


if __name__ == "__main__":
    main()
