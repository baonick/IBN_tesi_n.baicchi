import os
import sys
import subprocess


def main():
    # If a folder is passed as an argument, we use it, otherwise we use the script folder
    if len(sys.argv) > 1:
        base_dir = os.path.abspath(sys.argv[1])
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"{'*'*60}")
    print(f" PIPELINE EXECUTION ON ALL SUB-FOLDERS")
    print(f" Base folder: {base_dir}")
    print(f"{'*'*60}")
    
    # Find all sub-folders that contain esegui_pipeline.py
    sottocartelle = sorted([
        d for d in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, d))
        and not d.startswith("__")
        and os.path.exists(os.path.join(base_dir, d, "esegui_pipeline.py"))
    ])
    
    if not sottocartelle:
        print("\nNo sub-folder with esegui_pipeline.py found.")
        return
    
    print(f"\nFound {len(sottocartelle)} folders to process:")
    for i, nome in enumerate(sottocartelle, 1):
        print(f"  {i}. {nome}")
    
    successi = 0
    fallimenti = 0
    
    for i, nome_cartella in enumerate(sottocartelle, 1):
        dir_path = os.path.join(base_dir, nome_cartella)
        
        print(f"\n{'='*60}")
        print(f" [{i}/{len(sottocartelle)}] PIPELINE START: {nome_cartella}")
        print(f"{'='*60}")
        
        # Executes esegui_pipeline.py in the sub-folder
        result = subprocess.run(
            [sys.executable, "esegui_pipeline.py"],
            cwd=dir_path
        )
        
        if result.returncode != 0:
            print(f"\n!!! ERROR in pipeline of: {nome_cartella}")
            fallimenti += 1
        else:
            print(f"\n>>> SUCCESSFULLY COMPLETED: {nome_cartella}")
            successi += 1
    
    # Final summary
    print(f"\n{'*'*60}")
    print(f" GLOBAL EXECUTION SUMMARY")
    print(f"{'*'*60}")
    print(f"  Total folders processed: {len(sottocartelle)}")
    print(f"  Successes: {successi}")
    print(f"  Failures: {fallimenti}")
    print(f"{'*'*60}")


if __name__ == "__main__":
    main()
