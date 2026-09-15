import subprocess
import os
import re
import sys
import shutil

# ==============================================================================
# CONFIGURAZIONE PERCORSI E PARAMETRI
# ==============================================================================
# Cartella dello script (script/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Radice del progetto (IBN github/) — da qui parte la scansione dei file LLM
BASE_DIR = os.path.dirname(SCRIPT_DIR)

# Cartella di installazione di DIPS (contiene dips.pl)
CARTELLA_DIPS = os.path.join(BASE_DIR, "dips")

# Cartella radice in cui creare le sottocartelle dei risultati DIPS
CARTELLA_OUTPUT_BASE = os.path.join(SCRIPT_DIR, "risultati_dips")

# Timeout in secondi per ciascuna esecuzione di Prolog
TIMEOUT_SECONDI = 15


# ==============================================================================
# RILEVAMENTO ESEGUIBILE SWI-PROLOG
# ==============================================================================
def trova_eseguibile_swipl():
    """
    Cerca l'eseguibile di SWI-Prolog (swipl) nel PATH di sistema
    o nei percorsi di installazione predefiniti su Windows/Linux.
    """
    # 1. Controlla nel PATH di sistema
    swipl_in_path = shutil.which("swipl")
    if swipl_in_path:
        return swipl_in_path

    # 2. Percorsi standard su Windows
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
# ESTRAZIONE INFORMAZIONI DAI FILE PROLOG / TXT
# ==============================================================================
def trova_intent_id(percorso_file):
    """Estrae l'ID dell'intento dal primo parametro del predicato intent/4."""
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
    """Estrae la lista delle VNF dal predicato target/2."""
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
# SCANSIONE CARTELLE E FILE GENERATI DA LLM
# ==============================================================================
def estrai_chiave_ordinamento(nome_file):
    """
    Estrae una chiave numerica per ordinare i file in modo naturale:
    es. 'output_context2_intentA.txt' -> (2, 'A')
    """
    m = re.search(r'context(\d+)_intent([A-Za-z0-9_]+)', nome_file)
    if m:
        return (int(m.group(1)), m.group(2))
    return (999999, nome_file)


def trova_file_llm_nella_cartella(dir_path):
    """
    Trova tutti i file generati da LLM in una specifica cartella:
    - 'output_contextN_intentX.txt' (Qwen)
    - 'contextN_intentX.txt' (Gemini)
    
    Restituisce una lista di tuple: (nome_file, percorso_completo)
    ordinata in modo naturale per contesto e intento.
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

        # Verifica se corrisponde a uno dei due formati
        if re.match(r'^(output_)?context\d+_intent[A-Za-z0-9_]+\.txt$', f):
            risultati.append((f, os.path.join(dir_path, f)))

    risultati.sort(key=lambda x: estrai_chiave_ordinamento(x[0]))
    return risultati


def genera_nome_cartella_output(rel_path):
    """
    Converte un percorso relativo (es. '3-shot-.../3-shot/Qwen2.5-3b')
    in un nome cartella pulito e leggibile (es. '3-shot_Qwen2.5-3b').
    """
    parti = rel_path.replace("\\", "/").split("/")
    parti_filtrate = [p for p in parti if not p.endswith("-001") and p != "."]
    if parti_filtrate:
        return "_".join(parti_filtrate)
    return rel_path.replace("\\", "_").replace("/", "_")


def scopri_cartelle_llm(base_dir):
    """
    Esplora ricorsivamente base_dir e restituisce un dizionario:
    { nome_pulito_modello: (cartella_sorgente, lista_file) }
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
        # Salta le cartelle speciali
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
# ESECUZIONE SINGOLO FILE IN DIPS
# ==============================================================================
def DipsExecutor(cartella_dips, file_pl, file_txt_output, swipl_bin="swipl", timeout=TIMEOUT_SECONDI):
    """
    Esegue DIPS per un singolo file Prolog/TXT generato da LLM:
    1. Estrae l'intent_id e il target dal file.
    2. Chiama SWI-Prolog eseguendo il goal: consult(file), dips(intent_id, Output), writeln(Output).
    3. Salva il risultato nel file_txt_output con formato:
       - Riga 1: TARGET:<vnf1,vnf2,...>
       - Righe successive: output di DIPS o messaggio di errore.
    
    Restituisce una stringa con l'esito: 'SOLUZIONE', 'FALSE', 'ERRORE_PROLOG', 'TIMEOUT', 'ERRORE_INTENT', 'ERRORE_SWIPL'
    """
    intent_id = trova_intent_id(file_pl)
    target_list = trova_target_list(file_pl)
    target_str = ",".join(target_list) if target_list else "NESSUN_TARGET"

    # Assicurati che la cartella di output esista
    os.makedirs(os.path.dirname(file_txt_output), exist_ok=True)

    if not intent_id:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERRORE:\nImpossibile trovare l'intent ID nel file.\n")
        return "ERRORE_INTENT"

    # In Prolog su Windows i percorsi con backslash devono essere normalizzati con slash /
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
                f.write(f"ERRORE:\n{stderr_pulito}\n")
                return "ERRORE_PROLOG"
            elif stdout_pulito:
                f.write(stdout_pulito + "\n")
                if stdout_pulito == "false":
                    return "FALSE"
                return "SOLUZIONE"
            else:
                f.write("NESSUN_OUTPUT\n")
                return "ERRORE_PROLOG"

    except subprocess.TimeoutExpired:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write("ERRORE_TIMEOUT\n")
        return "TIMEOUT"

    except FileNotFoundError:
        with open(file_txt_output, 'w', encoding='utf-8') as f:
            f.write(f"TARGET:{target_str}\n")
            f.write(f"ERRORE_SWIPL_NON_TROVATO: Impossibile eseguire '{swipl_bin}'. Verificare l'installazione di SWI-Prolog.\n")
        return "ERRORE_SWIPL"


# ==============================================================================
# MAIN: ESECUZIONE SU TUTTE LE CARTELLE
# ==============================================================================
def main():
    print("=" * 70)
    print("🚀 DIPS EXECUTER — Esecuzione batch per tutti gli output LLM")
    print("=" * 70)

    # 1. Verifica cartella DIPS
    if not os.path.isdir(CARTELLA_DIPS):
        print(f"❌ Errore: Cartella DIPS non trovata in: {CARTELLA_DIPS}")
        return

    file_dips_pl = os.path.join(CARTELLA_DIPS, "dips.pl")
    if not os.path.isfile(file_dips_pl):
        print(f"❌ Errore: File dips.pl non trovato in: {file_dips_pl}")
        return

    # 2. Rileva eseguibile SWI-Prolog
    swipl_bin = trova_eseguibile_swipl()
    print(f"📁 Cartella DIPS     : {CARTELLA_DIPS}")
    print(f"📂 Cartella Output   : {CARTELLA_OUTPUT_BASE}")
    print(f"⚙️ Eseguibile Prolog : {swipl_bin}")
    print(f"⏱️ Timeout per file  : {TIMEOUT_SECONDI}s")
    print("=" * 70)

    # 3. Trova tutte le cartelle con file LLM
    cartelle_llm = scopri_cartelle_llm(BASE_DIR)

    if not cartelle_llm:
        print("⚠️ Nessuna cartella con file di output LLM trovata.")
        return

    print(f"\n🔍 Trovate {len(cartelle_llm)} cartelle di modelli da elaborare:")
    for nome_modello, (cartella_src, file_list) in sorted(cartelle_llm.items()):
        print(f"  • {nome_modello:30s} : {len(file_list):3d} file (in {os.path.relpath(cartella_src, BASE_DIR)})")

    # 4. Creazione cartella base di output
    os.makedirs(CARTELLA_OUTPUT_BASE, exist_ok=True)

    # 5. Esecuzione per ogni cartella / modello
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
        "SOLUZIONE": "✅ Soluzione trovata",
        "FALSE": "⚠️ false (nessuna soluzione)",
        "ERRORE_PROLOG": "❌ Errore Prolog / Sintassi",
        "TIMEOUT": "⏱️ Timeout superato",
        "ERRORE_INTENT": "❌ Intent ID mancante",
        "ERRORE_SWIPL": "❌ SWI-Prolog non trovato"
    }

    for indice_modello, (nome_modello, (cartella_src, file_list)) in enumerate(sorted(cartelle_llm.items()), 1):
        # Cartella dedicata per questo modello
        cartella_output_modello = os.path.join(CARTELLA_OUTPUT_BASE, nome_modello)
        os.makedirs(cartella_output_modello, exist_ok=True)

        print(f"\n[{indice_modello}/{len(cartelle_llm)}] 📦 Elaborazione: {nome_modello}")
        print(f"    Sorgente : {os.path.relpath(cartella_src, BASE_DIR)}")
        print(f"    Output   : {os.path.relpath(cartella_output_modello, BASE_DIR)}")
        print(f"    File     : {len(file_list)}")
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

            # Stampa progresso sintetico
            desc_esito = simboli_esito.get(esito, esito)
            print(f"  [{idx:3d}/{len(file_list):3d}] {nome_file:<35s} -> {desc_esito}")

            # Se swipl non esiste, interrompi per evitare 768 messaggi di errore inutili
            if esito == "ERRORE_SWIPL":
                print(f"\n❌ ERRORE CRITICO: Eseguibile SWI-Prolog '{swipl_bin}' non trovato!")
                print("   Installare SWI-Prolog o verificare che 'swipl' sia nel PATH di sistema.")
                return

        # Aggiornamento statistiche globali
        statistiche_globali["soluzioni"] += conteggi_modello["SOLUZIONE"]
        statistiche_globali["false"] += conteggi_modello["FALSE"]
        statistiche_globali["errori_prolog"] += conteggi_modello["ERRORE_PROLOG"]
        statistiche_globali["timeout"] += conteggi_modello["TIMEOUT"]
        statistiche_globali["errori_intent"] += conteggi_modello["ERRORE_INTENT"]

        # Riepilogo modello
        print(f"\n📊 Riepilogo {nome_modello}:")
        print(f"   Soluzioni trovate : {conteggi_modello['SOLUZIONE']:3d}")
        print(f"   False (no soluz.) : {conteggi_modello['FALSE']:3d}")
        print(f"   Errori Prolog     : {conteggi_modello['ERRORE_PROLOG']:3d}")
        print(f"   Timeout           : {conteggi_modello['TIMEOUT']:3d}")
        print(f"   Intent mancanti   : {conteggi_modello['ERRORE_INTENT']:3d}")

    # 6. Report finale globale
    print("\n" + "=" * 70)
    print("🏁 ESECUZIONE BATCH COMPLETATA")
    print("=" * 70)
    print(f"Totale file esaminati : {statistiche_globali['totale_file']}")
    print(f"Soluzioni trovate     : {statistiche_globali['soluzioni']}")
    print(f"False (nessuna soluz.): {statistiche_globali['false']}")
    print(f"Errori Prolog/Sintassi: {statistiche_globali['errori_prolog']}")
    print(f"Timeout               : {statistiche_globali['timeout']}")
    print(f"Intent ID mancanti    : {statistiche_globali['errori_intent']}")
    print(f"Cartella risultati    : {CARTELLA_OUTPUT_BASE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
