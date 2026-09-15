import os
import sys
import subprocess

# Configuration: prefixes of files to search and execute in their respective subfolders
# You can add or modify the prefixes here. The script will look for .py files
# that start with these names within the specified folders.
SCRIPT_PREFIXES = {
    "test": ["crea_json", "crea_dataset"],
    "tester": ["crea_json", "crea_dataset"],  # Sometimes the folder is called 'tester'
    "train": ["creaDataset", "crea_dataset", "crea_json"] 
}

def main():
    # Takes the base folder (e.g. '5-fold-llama-3.1-8b-onServer' or '5-fold-on-context')
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
    else:
        # If not specified, uses the folder where this script is located
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
    base_dir = os.path.abspath(base_dir)
    print(f"Starting recursive exploration of base folder: {base_dir}")
    
    if not os.path.exists(base_dir):
        print(f"The specified folder does not exist: {base_dir}")
        sys.exit(1)
    
    # os.walk recursively explores all folders and subfolders
    for root, dirs, files in os.walk(base_dir):
        # Skip system or cache folders (modify dirs in-place to not enter them at all)
        dirs[:] = [d for d in dirs if not d.startswith("__")]
        
        # We extract the names of all parent folders of the current path
        path_parts = root.split(os.sep)
        
        # We determine which prefixes are valid for the current folder
        applicable_prefixes = set()
        for folder_name, prefixes in SCRIPT_PREFIXES.items():
            if folder_name in path_parts:
                applicable_prefixes.update(prefixes)
                
        # If we are not in a test/tester/train subfolder, we skip
        if not applicable_prefixes:
            continue
            
        # We search and execute .py files that match the prefixes
        for filename in sorted(files):
            if filename.endswith(".py"):
                for prefix in applicable_prefixes:
                    if filename.startswith(prefix):
                        script_path = os.path.join(root, filename)
                        print(f"\n{'='*60}")
                        print(f" SCRIPT FOUND: {filename}")
                        print(f" FOLDER:       {root}")
                        print(f"{'='*60}")
                        
                        # Executes the script setting the working directory to `root`
                        result = subprocess.run([sys.executable, filename], cwd=root)
                        
                        if result.returncode != 0:
                            print(f"!!! ERROR during execution of {filename} in {root}")
                        else:
                            print(f"---> {filename} successfully executed.")
                        
                        # Avoids executing the same file twice if it matches multiple prefixes
                        break 

    print(f"\n{'*'*60}\nGLOBAL EXECUTION TERMINATED\n{'*'*60}")

if __name__ == "__main__":
    main()
