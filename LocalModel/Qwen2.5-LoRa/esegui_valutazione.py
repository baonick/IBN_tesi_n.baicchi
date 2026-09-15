import os
import sys
import re
import json

# Dynamically calculates the project root and adds script/ to the path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import MetricExecuterInputDips as metrics
# pyrefly: ignore [missing-import]
import parser_catalogo


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTELLA_INTENTI_IDEALI = os.path.join(_PROJECT_ROOT, "intent")


def analizza_differenze_fatti(set_ideale, set_llm):
    """
    Extracts differences (removing perfect matches), associates generated facts to the
    gold most similar gold ones and identifies which parameters differ.
    Returns:
    - error_details: dictionary {generated_fact: error_string}
    - unassociated_omissions: set of gold facts that found no association
    """
    mancanti = set_ideale - set_llm
    extra = set_llm - set_ideale
    
    def parse_fact(fact_str):
        match = re.match(r'^([a-zA-Z0-9_]+)\((.*)\)$', fact_str)
        if not match:
            return fact_str, []
        pred = match.group(1)
        args_str = match.group(2)
        args = []
        bracket_level = 0
        current_arg = ""
        for char in args_str:
            if char == '[':
                bracket_level += 1
                current_arg += char
            elif char == ']':
                bracket_level -= 1
                current_arg += char
            elif char == ',' and bracket_level == 0:
                args.append(current_arg.strip())
                current_arg = ""
            else:
                current_arg += char
        if current_arg:
            args.append(current_arg.strip())
        return pred, args

    dettagli_errori = {}
    matched_mancanti = set()
    
    for ex in extra:
        ex_pred, ex_args = parse_fact(ex)
        best_match = None
        best_score = -1
        best_diffs = []
        
        for man in mancanti:
            if man in matched_mancanti:
                continue
                
            man_pred, man_args = parse_fact(man)
            if ex_pred != man_pred:
                continue
                
            score = 0
            diffs = []
            max_len = max(len(ex_args), len(man_args))
            for i in range(max_len):
                arg_ex = ex_args[i] if i < len(ex_args) else "<mancante>"
                arg_man = man_args[i] if i < len(man_args) else "<mancante>"
                if arg_ex == arg_man:
                    score += 1
                else:
                    diffs.append(f"parameter {i+1} wrong (expected: '{arg_man}')")
                    
            if score > best_score:
                best_score = score
                best_match = man
                best_diffs = diffs
                
        if best_match is not None:
            matched_mancanti.add(best_match)
            dettaglio = "Error: " + ", ".join(best_diffs)
            dettagli_errori[ex] = dettaglio
        else:
            dettagli_errori[ex] = "Hallucination (no corresponding gold predicate)"
            
    omissioni_non_associate = mancanti - matched_mancanti
    return dettagli_errori, omissioni_non_associate


def processa_cartella(dir_path, mappa_vnf):
    """
    Searches all output files in a single folder (e.g. a 'result' folder),
    creates the individual report for each file and finally creates a global report
    (report_valutazione.txt) with the averages of all files found in THAT folder.
    
    Returns a dictionary with the average metrics of the folder, or None
    if there are no output files to analyze.
    """
    # Identify all output files in the current folder
    files_output = [f for f in os.listdir(dir_path) if f.startswith("output_context") and f.endswith(".txt")]
    
    if not files_output:
        return None
        
    print(f"\nFolder analysis: {dir_path}")
    
    # Load the execution times file, if present
    tempi_path = os.path.join(dir_path, "tempi_esecuzione.json")
    tempi_esecuzione = {}
    if os.path.exists(tempi_path):
        try:
            with open(tempi_path, "r", encoding="utf-8") as f_tempi:
                tempi_esecuzione = json.load(f_tempi)
            print(f"  Loaded execution times from: {tempi_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Warning: error loading times: {e}")
    
    totale_recall = 0.0
    totale_precision = 0.0
    totale_jaccard = 0.0
    totale_f1 = 0.0
    numero_test = 0
    lista_metriche_per_accuracy = []  # lista di (precision, recall) per ogni elemento
    totale_tempo = 0.0
    contatore_tempo = 0
    
    for file_name in sorted(files_output):
        # Extract context and intent letter
        match = re.search(r'output_(context\d+)_intent([A-Za-z]+)\.txt', file_name)
        if not match:
            continue
            
        context_name = match.group(1)
        lettera_intent = match.group(2)
        
        file_path = os.path.join(dir_path, file_name)
        file_ideale = os.path.join(CARTELLA_INTENTI_IDEALI, context_name, "facts.pl")
        file_testo_intento = os.path.join(CARTELLA_INTENTI_IDEALI, context_name, f"intent{lettera_intent}.txt")
        
        if not os.path.exists(file_ideale):
            print(f"  Warning: ideal file not found for {context_name} ({file_ideale})")
            continue
            
        # Reading and enrichment of textual intent
        testo_intento = "Intent text not found."
        if os.path.exists(file_testo_intento):
            with open(file_testo_intento, "r", encoding="utf-8") as f_intento:
                testo_intento = f_intento.read().strip()
                
            if mappa_vnf:
                testo_intento = parser_catalogo.arricchisci_intento_con_hardware(testo_intento, mappa_vnf)
                
        # Metrics calculation
        set_ideale = metrics.estrai_set_da_pl(file_ideale)
        set_llm = metrics.estrai_set_da_pl(file_path)
        
        recall = metrics.calcola_recall(set_ideale, set_llm)
        precision = metrics.calcola_precision(set_ideale, set_llm)
        jaccard = metrics.calcola_jaccard(set_ideale, set_llm)
        f1 = metrics.calcola_f1(precision, recall)
        
        print(f"  [{context_name} intent{lettera_intent}] R: {recall:.4f} | P: {precision:.4f} | J: {jaccard:.4f} | F1: {f1:.4f}")
        
        # Retrieve execution time for this file
        tempo_info = tempi_esecuzione.get(file_name, {})
        tempo_esec = tempo_info.get("durata_secondi", None)
        if tempo_esec is not None:
            totale_tempo += tempo_esec
            contatore_tempo += 1
        
        # Collect the (precision, recall) pair for accuracy calculation
        lista_metriche_per_accuracy.append((precision, recall))
        
        # Sum for folder averages
        totale_recall += recall
        totale_precision += precision
        totale_jaccard += jaccard
        totale_f1 += f1
        numero_test += 1
        
        # 1) INDIVIDUAL REPORT
        report_name = f"report_{context_name}_intent{lettera_intent}.txt"
        report_path = os.path.join(dir_path, report_name)
        
        with open(report_path, "w", encoding="utf-8") as f_singolo:
            f_singolo.write(f"RESULTS FOR {context_name.upper()} - INTENT {lettera_intent.upper()}\n")
            f_singolo.write(f"Analyzed file: {file_name}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write("--- INTENT TESTSUALE ---\n")
            f_singolo.write(f"{testo_intento}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write(f"Recall    (Omissions)     : {recall:.4f}\n")
            f_singolo.write(f"Precision (Hallucinations) : {precision:.4f}\n")
            f_singolo.write(f"Jaccard   (Global)       : {jaccard:.4f}\n")
            f_singolo.write(f"F1-Score  (Balance)    : {f1:.4f}\n")
            if tempo_esec is not None:
                f_singolo.write(f"Execution Time          : {tempo_esec:.4f}s\n")
                f_singolo.write(f"Start: {tempo_info.get('timestamp_inizio', 'N/A')} | End: {tempo_info.get('timestamp_fine', 'N/A')}\n")
            f_singolo.write("==================================================\n\n")
            
            # If the metrics are perfect, simply print the facts
            if recall == 1.0 and precision == 1.0:
                f_singolo.write("--- Ideal Extracted Facts ---\n")
                f_singolo.write(metrics.set_to_string(set_ideale) + "\n\n")
                f_singolo.write("--- LLM Extracted Facts ---\n")
                f_singolo.write(metrics.set_to_string(set_llm) + "\n")
            else:
                # If they are not perfect, apply the detailed analysis function
                dettagli_errori, omissioni = analizza_differenze_fatti(set_ideale, set_llm)
                
                f_singolo.write("--- Ideal Extracted Facts (Gold) ---\n")
                f_singolo.write(metrics.set_to_string(set_ideale) + "\n\n")
                
                f_singolo.write("--- LLM Extracted Facts (Analisi) ---\n")
                corretti = set_ideale & set_llm
                
                # Correct facts
                for c in sorted(corretti):
                    f_singolo.write(f"{c}  [ Correct]\n")
                    
                # Wrong/extra facts (annotated)
                extra = set_llm - set_ideale
                for ex in sorted(extra):
                    nota = dettagli_errori.get(ex, "")
                    f_singolo.write(f"{ex}  [ {nota}]\n")
                    
                # Omissions non associate a niente (rimaste indietro)
                if omissioni:
                    f_singolo.write("\n--- Fatti Gold Mancanti (Omissions assolute) ---\n")
                    for om in sorted(omissioni):
                        f_singolo.write(f"{om}  [ Fact not generated by LLM]\n")
            
    # 2) GLOBAL FOLDSER REPORT
    if numero_test > 0:
        avg_recall = totale_recall / numero_test
        avg_precision = totale_precision / numero_test
        avg_jaccard = totale_jaccard / numero_test
        avg_f1 = totale_f1 / numero_test
        accuracy = metrics.calcola_accuracy(lista_metriche_per_accuracy)
        num_perfect = sum(1 for p, r in lista_metriche_per_accuracy if p == 1.0 and r == 1.0)
        
        report_globale_path = os.path.join(dir_path, "report_valutazione.txt")
        with open(report_globale_path, "w", encoding="utf-8") as f_out:
            f_out.write(f"AVERAGE FOLDSER RESULTS ON {numero_test} TESTS\n")
            f_out.write("==================================================\n")
            f_out.write(f"Average Recall      : {avg_recall:.4f}\n")
            f_out.write(f"Average Precision   : {avg_precision:.4f}\n")
            f_out.write(f"Average Jaccard     : {avg_jaccard:.4f}\n")
            f_out.write(f"Average F1-Score    : {avg_f1:.4f}\n")
            f_out.write(f"Accuracy          : {accuracy:.4f}  ({num_perfect}/{numero_test} perfect)\n")
            if contatore_tempo > 0:
                avg_tempo = totale_tempo / contatore_tempo
                f_out.write(f"Average Exec. Time : {avg_tempo:.4f}s  (on {contatore_tempo} tests)\n")
                f_out.write(f"Total Exec. Time: {totale_tempo:.4f}s\n")
            f_out.write("==================================================")
            
        print(f"  -> Accuracy: {accuracy:.4f} ({num_perfect}/{numero_test} perfect)")
        if contatore_tempo > 0:
            print(f"  -> Average time: {avg_tempo:.4f}s | Total time: {totale_tempo:.4f}s")
        print(f"  -> Created global report for folder: {report_globale_path}")
        
        return {
            "cartella": dir_path,
            "num_test": numero_test,
            "recall": avg_recall,
            "precision": avg_precision,
            "jaccard": avg_jaccard,
            "f1": avg_f1,
            "accuracy": accuracy,
            "num_perfect": num_perfect,
            "tempo_totale": totale_tempo,
            "tempo_medio": totale_tempo / contatore_tempo if contatore_tempo > 0 else None,
            "num_con_tempo": contatore_tempo,
        }
    
    return None


def genera_report_5fold(risultati_cartelle, output_path):
    """
    Generates a global report with the average of metrics of all folders
    analyzed in the 5-fold cross-validation.
    """
    if not risultati_cartelle:
        print("No results to aggregate for the 5-fold report.")
        return
    
    n = len(risultati_cartelle)
    avg_recall = sum(r["recall"] for r in risultati_cartelle) / n
    avg_precision = sum(r["precision"] for r in risultati_cartelle) / n
    avg_jaccard = sum(r["jaccard"] for r in risultati_cartelle) / n
    avg_f1 = sum(r["f1"] for r in risultati_cartelle) / n
    totale_test = sum(r["num_test"] for r in risultati_cartelle)
    totale_perfect = sum(r["num_perfect"] for r in risultati_cartelle)
    accuracy_globale = round(totale_perfect / totale_test, 4) if totale_test > 0 else 0.0
    avg_accuracy_per_fold = sum(r["accuracy"] for r in risultati_cartelle) / n
    
    # Global times calculation
    tempi_disponibili = [r for r in risultati_cartelle if r.get("tempo_medio") is not None]
    tempo_totale_globale = sum(r["tempo_totale"] for r in tempi_disponibili)
    num_con_tempo_globale = sum(r["num_con_tempo"] for r in tempi_disponibili)
    tempo_medio_globale = tempo_totale_globale / num_con_tempo_globale if num_con_tempo_globale > 0 else None
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write("5-FOLDS CROSS-VALIDATION GLOBAL REPORT\n")
        f_out.write("=" * 60 + "\n\n")
        f_out.write(f"Number of analyzed folds: {n}\n")
        f_out.write(f"Total number of tests: {totale_test}\n\n")
        
        f_out.write("--- FOLDSER DETAIL ---\n\n")
        for r in risultati_cartelle:
            nome_cartella = os.path.basename(os.path.dirname(r["cartella"]))
            f_out.write(f"  {nome_cartella} ({r['num_test']} test)\n")
            f_out.write(f"    Recall: {r['recall']:.4f} | Precision: {r['precision']:.4f} | ")
            f_out.write(f"Jaccard: {r['jaccard']:.4f} | F1: {r['f1']:.4f} | ")
            f_out.write(f"Accuracy: {r['accuracy']:.4f} ({r['num_perfect']}/{r['num_test']})")
            if r.get("tempo_medio") is not None:
                f_out.write(f" | Average Time: {r['tempo_medio']:.4f}s")
            f_out.write("\n\n")
        
        f_out.write("=" * 60 + "\n")
        f_out.write(f"GLOBAL AVERAGES ON {n} FOLDS ({totale_test} total tests)\n")
        f_out.write("=" * 60 + "\n")
        f_out.write(f"Average Recall      : {avg_recall:.4f}\n")
        f_out.write(f"Average Precision   : {avg_precision:.4f}\n")
        f_out.write(f"Average Jaccard     : {avg_jaccard:.4f}\n")
        f_out.write(f"Average F1-Score    : {avg_f1:.4f}\n")
        f_out.write(f"Accuracy Global  : {accuracy_globale:.4f}  ({totale_perfect}/{totale_test} perfect)\n")
        f_out.write(f"Average Accuracy/Fold: {avg_accuracy_per_fold:.4f}\n")
        if tempo_medio_globale is not None:
            f_out.write(f"Average Exec. Time : {tempo_medio_globale:.4f}s  (su {num_con_tempo_globale} test)\n")
            f_out.write(f"Total Exec. Time: {tempo_totale_globale:.4f}s\n")
        f_out.write("=" * 60 + "\n")
    
    print(f"\n=> 5-fold global report saved in: {output_path}")


def main():
    catalogo_json = os.path.join(CARTELLA_INTENTI_IDEALI, "catalogoVNF.json")

    # We load the catalog only once
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
    except FileNotFoundError:
        print(f"Warning: VNF catalog not found in {catalogo_json}. Intents text will not be enriched.")
        mappa_vnf = {}

    print("=" * 60)
    print("=== SINGLE REPORTS AND FOLDER GLOBAL REPORT GENERATION ===")
    print("=" * 60)

    risultati_cartelle = []

    # Scan all folders inside BASE_DIR
    for root, dirs, files in os.walk(BASE_DIR):
        risultato = processa_cartella(root, mappa_vnf)
        if risultato is not None:
            risultati_cartelle.append(risultato)

    # Generate the 5-fold global report
    report_5fold_path = os.path.join(BASE_DIR, "report_5fold_globale.txt")
    genera_report_5fold(risultati_cartelle, report_5fold_path)

    print("\nProcessing completed!")


if __name__ == "__main__":
    main()

