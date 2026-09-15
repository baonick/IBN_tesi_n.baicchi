import subprocess
import os
import re
import sys
import shutil

# ==============================================================================
# PATHS AND PARAMETERS CONFIGURATION
# ==============================================================================
# Script folder (script/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root (IBN github/) — LLM files scanning starts from here
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# DIPS installation folder (contains dips.pl)
CARTELLA_DIPS = os.path.join(BASE_DIR, "dips")

# Root folder in which to create DIPS results subfolders
CARTELLA_OUTPUT_BASE = os.path.join(SCRIPT_DIR, "risultati_dips")

# Timeout in seconds for each Prolog execution
TIMEOUT_SECONDI = 15


# ==============================================================================
# SWI-PROLOG EXECUTABLE DETECTION
# ==============================================================================
def trova_eseguibile_swipl():
    """
    Searches for the SWI-Prolog executable (swipl) in the system PATH
    or in the default installation paths on Windows/Linux.
    """
    # 1. Check in the system PATH
    swipl_in_path = shutil.which("swipl")
    if swipl_in_path:
        return swipl_in_path

    # 2. Standard paths on Windows
    percorsi_windows = [
        r"C:\Program Files\swipl\bin\swipl.exe",
        r"C:\Program Files (x86)\swipl\bin\swipl.exe",
        r"C:\swipl\bin\swipl.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\swipl\bin\swipl.exe"),
    ]
    for p in percorsi_windows:
        if os.path.isfile(p):
            return p

    # 3. Default fallback
    return "swipl"


# ==============================================================================
# EXTRACTING INFORMATION FROM PROLOG / TXT FILES
# ==============================================================================
def trova_intent_id(percorso_file):
    """Extracts the intent ID from the first parameter of the intent/4 predicate."""
    pattern = re.compile(r"intent\(\s*'?([a-zA-Z0-9_]+)'?\s*,")
    try:
        with open(percorso_file, 'r', encoding='utf-8', errors='ignore') as f:
            for riga in f:
                match = pattern.search(riga)
                if match:
                    return match.group(1)
    except OSError:
        return None
    return None


def trova_target_list(percorso_file):
    """Extracts the VNF list from the target/2 predicate."""
    pattern = re.compile(r"target\([^,]+,\s*\[(.*?)\]\)")
    try:
        with open(percorso_file, 'r', encoding='utf-8', errors='ignore') as f:
            for riga in f:
                match = pattern.search(riga)
                if match:
                    vnfs = [v.strip() for v in match.group(1).split(',') if v.strip()]
                    return vnfs
    except OSError:
        return []
    return []


# ==============================================================================
# SCANNING LLM GENERATED FOLDERS AND FILES
# ==============================================================================
def estrai_chiave_ordinamento(nome_file):
    """
    Extracts a numeric key to sort files naturally:
    e.g. 'output_context2_intentA.txt' -> (2, 'A')
    """
    m = re.search(r'context(\d+)_intent([A-Za-z0-9_]+)', nome_file)
    if m:
        return (int(m.group(1)), m.group(2))
    return (999999, nome_file)


def trova_file_llm_nella_cartella(dir_path):
    """
    Finds all LLM generated files in a specific folder:
    - 'output_contextN_intentX.txt' (Qwen)
    - 'contextN_intentX.txt' (Gemini)
    
    Returns a list of tuples: (file_name, full_path)
    sorted naturally by context and intent.
    """
    risultati = []
    try:
        files = os.listdir(dir_path)
    except OSError:
        return risultati

    for f in files:
        if not f.endswith(".txt"):
            continue
        if f.startswith("report"):
            continue

        # Check if it matches one of the two formats
        if re.match(r'^(output_)?context\d+_intent[A-Za-z0-9_]+\.txt$', f):
            risultati.append((f, os.path.join(dir_path, f)))

    risultati.sort(key=lambda x: estrai_chiave_ordinamento(x[0]))
    return risultati


def genera_nome_cartella_output(rel_path):
    """
    Converts a relative path (e.g. '3-shot-.../3-shot/Qwen2.5-3b')
    into a clean and readable folder name (e.g. '3-shot_Qwen2.5-3b').
    """
    parti = rel_path.replace("\\", "/").split("/")
    parti_filtrate = [p for p in parti if not p.endswith("-001") and p != "."]
    if parti_filtrate:
        return "_".join(parti_filtrate)
    return rel_path.replace("\\", "_").replace("/", "_")


def scopri_cartelle_llm(base_dir):
    """
    Recursively explores base_dir and returns a dictionary:
    { clean_model_name: (source_folder, file_list) }
    """
    cartelle_trovate = {}
    cartelle_da_ignorare = {
        "intent",
        "reports_catalogo",
        "risultati_dips",
        "__pycache__",
        ".git",
        "Dips",
        "scratch"
    }

    for root, dirs, files in os.walk(base_dir):
        # Skip special folders
        basename = os.path.basename(root)
        if basename in cartelle_da_ignorare:
            dirs.clear()
            continue

        file_llm = trova_file_llm_nella_cartella(root)
        if file_llm:
            rel_path = os.path.relpath(root, base_dir)
            nome_modello = genera_nome_cartella_output(rel_path)
            cartelle_trovate[nome_modello] = (root, file_llm)

    return cartelle_trovate


# ==============================================================================
# SINGLE FILE EXECUTION IN DIPS
# ==============================================================================
def DipsExecutor(cartella_dips, file_pl, file_txt_output, swipl_bin="swipl", timeout=TIMEOUT_SECONDI):
    """
    Executes DIPS for a single Prolog/TXT file generated by LLM:
    1. Extracts the intent_id and target from the file.
    2. Calls SWI-Prolog executing the goal: consult(file), dips(intent_id, Output), writeln(Output).
    3. Saves the result in file_txt_output with format:
       - Line 1: TARGET:<vnf1,vnf2,...>
       - Following lines: DIPS output or error message.
    
    Returns an outcome string: 'SOLUZIONE', 'FALSE', 'ERRORE_PROLOG', 'TIMEOUT', 'ERRORE_INTENT', 'ERRORE_SWIPL'
    """
    intent_id = trova_intent_id(file_pl)
    target_list = trova_target_list(file_pl)
    target_str = ",".join(target_list) if target_list else "NO_TARGET"

    # Make sure the output folder exists
    os.makedirs(os.path.dirname(file_txt_output), exist_ok=True)

    if not intent_id:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERROR:\nUnable to find the intent ID in the file.\n")
        return "ERRORE_INTENT"

    # In Prolog on Windows, paths with backslashes must be normalized with slashes /
    file_pl_prolog = os.path.abspath(file_pl).replace("\\", "/")
    goal = f"consult('{file_pl_prolog}'), dips('{intent_id}', Output), writeln(Output)."

    comando = [
        swipl_bin, "-q",
        "-s", "dips.pl",
        "-g", goal,
        "-t", "halt"
    ]

    try:
        risultato = subprocess.run(
            comando,
            cwd=cartella_dips,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        stdout_pulito = risultato.stdout.strip()
        stderr_pulito = risultato.stderr.strip()

        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")

            if stderr_pulito and ("ERROR:" in stderr_pulito or "Syntax error" in stderr_pulito):
                f.write(f"ERROR:\n{stderr_pulito}\n")
                return "ERRORE_PROLOG"
            elif stdout_pulito:
                f.write(stdout_pulito + "\n")
                if stdout_pulito == "false":
                    return "FALSE"
                return "SOLUZIONE"
            else:
                f.write("NO_OUTPUT\n")
                return "ERRORE_PROLOG"

    except subprocess.TimeoutExpired:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERROR_TIMEOUT\n")
        return "TIMEOUT"

    except FileNotFoundError:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write(f"ERROR_SWIPL_NOT_FOUND: Unable to execute '{swipl_bin}'. Verify the SWI-Prolog installation.\n")
        return "ERRORE_SWIPL"


# ==============================================================================
# MAIN: EXECUTION ON ALL FOLDERS
# ==============================================================================
def main():
    print("=" * 70)
    print("🚀 DIPS EXECUTER — Batch execution for all LLM outputs")
    print("=" * 70)

    # 1. Verify DIPS folder
    if not os.path.isdir(CARTELLA_DIPS):
        print(f"❌ Error: DIPS folder not found at: {CARTELLA_DIPS}")
        return

    file_dips_pl = os.path.join(CARTELLA_DIPS, "dips.pl")
    if not os.path.isfile(file_dips_pl):
        print(f"❌ Error: dips.pl file not found at: {file_dips_pl}")
        return

    # 2. Detect SWI-Prolog executable
    swipl_bin = trova_eseguibile_swipl()
    print(f"📁 DIPS Folder       : {CARTELLA_DIPS}")
    print(f"📂 Output Folder     : {CARTELLA_OUTPUT_BASE}")
    print(f"⚙️ Prolog Executable : {swipl_bin}")
    print(f"⏱️ File Timeout      : {TIMEOUT_SECONDI}s")
    print("=" * 70)

    # 3. Find all folders with LLM files
    cartelle_llm = scopri_cartelle_llm(BASE_DIR)

    if not cartelle_llm:
        print("⚠️ No folders with LLM output files found.")
        return

    print(f"\n🔍 Found {len(cartelle_llm)} model folders to process:")
    for nome_modello, (cartella_src, file_list) in sorted(cartelle_llm.items()):
        print(f"  • {nome_modello:30s} : {len(file_list):3d} files (in {os.path.relpath(cartella_src, BASE_DIR)})")

    # 4. Base output folder creation
    os.makedirs(CARTELLA_OUTPUT_BASE, exist_ok=True)

    # 5. Execution for each folder / model
    statistiche_globali = {
        "totale_file": 0,
        "soluzioni": 0,
        "false": 0,
        "errori_prolog": 0,
        "timeout": 0,
        "errori_intent": 0,
        "errori_swipl": 0
    }

    simboli_esito = {
        "SOLUZIONE": "✅ Solution found",
        "FALSE": "⚠️ false (no solution)",
        "ERRORE_PROLOG": "❌ Prolog / Syntax Error",
        "TIMEOUT": "⏱️ Timeout exceeded",
        "ERRORE_INTENT": "❌ Missing Intent ID",
        "ERRORE_SWIPL": "❌ SWI-Prolog not found"
    }

    for indice_modello, (nome_modello, (cartella_src, file_list)) in enumerate(sorted(cartelle_llm.items()), 1):
        # Dedicated folder for this model
        cartella_output_modello = os.path.join(CARTELLA_OUTPUT_BASE, nome_modello)
        os.makedirs(cartella_output_modello, exist_ok=True)

        print(f"\n[{indice_modello}/{len(cartelle_llm)}] 📦 Processing: {nome_modello}")
        print(f"    Source   : {os.path.relpath(cartella_src, BASE_DIR)}")
        print(f"    Output   : {os.path.relpath(cartella_output_modello, BASE_DIR)}")
        print(f"    Files    : {len(file_list)}")
        print("-" * 70)

        conteggi_modello = {
            "SOLUZIONE": 0,
            "FALSE": 0,
            "ERRORE_PROLOG": 0,
            "TIMEOUT": 0,
            "ERRORE_INTENT": 0,
            "ERRORE_SWIPL": 0
        }

        for idx, (nome_file, file_path) in enumerate(file_list, 1):
            file_txt_output = os.path.join(cartella_output_modello, nome_file)
            
            esito = DipsExecutor(
                cartella_dips=CARTELLA_DIPS,
                file_pl=file_path,
                file_txt_output=file_txt_output,
                swipl_bin=swipl_bin,
                timeout=TIMEOUT_SECONDI
            )

            conteggi_modello[esito] = conteggi_modello.get(esito, 0) + 1
            statistiche_globali["totale_file"] += 1

            # Synthetic progress print
            desc_esito = simboli_esito.get(esito, esito)
            print(f"  [{idx:3d}/{len(file_list):3d}] {nome_file:<35s} -> {desc_esito}")

            # If swipl does not exist, interrupt to avoid 768 useless error messages
            if esito == "ERRORE_SWIPL":
                print(f"\n❌ CRITICAL ERROR: SWI-Prolog executable '{swipl_bin}' not found!")
                print("   Install SWI-Prolog or verify that 'swipl' is in the system PATH.")
                return

        # Global stats update
        statistiche_globali["soluzioni"] += conteggi_modello["SOLUZIONE"]
        statistiche_globali["false"] += conteggi_modello["FALSE"]
        statistiche_globali["errori_prolog"] += conteggi_modello["ERRORE_PROLOG"]
        statistiche_globali["timeout"] += conteggi_modello["TIMEOUT"]
        statistiche_globali["errori_intent"] += conteggi_modello["ERRORE_INTENT"]

        # Model summary
        print(f"\n📊 Summary for {nome_modello}:")
        print(f"   Solutions found     : {conteggi_modello['SOLUZIONE']:3d}")
        print(f"   False (no solution) : {conteggi_modello['FALSE']:3d}")
        print(f"   Prolog errors       : {conteggi_modello['ERRORE_PROLOG']:3d}")
        print(f"   Timeouts            : {conteggi_modello['TIMEOUT']:3d}")
        print(f"   Missing intents     : {conteggi_modello['ERRORE_INTENT']:3d}")

    # 6. Final global report
    print("\n" + "=" * 70)
    print("🏁 BATCH EXECUTION COMPLETED")
    print("=" * 70)
    print(f"Total files examined     : {statistiche_globali['totale_file']}")
    print(f"Solutions found          : {statistiche_globali['soluzioni']}")
    print(f"False (no solution)      : {statistiche_globali['false']}")
    print(f"Prolog/Syntax errors     : {statistiche_globali['errori_prolog']}")
    print(f"Timeouts                 : {statistiche_globali['timeout']}")
    print(f"Missing Intent IDs       : {statistiche_globali['errori_intent']}")
    print(f"Results folder           : {CARTELLA_OUTPUT_BASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
