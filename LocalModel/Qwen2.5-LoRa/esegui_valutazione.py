import os
import sys
import re
import json

# Calcola dinamicamente la root del progetto e aggiunge script/ al path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "../../.."))
sys.path.insert(0, os.path.join(_PROJECT_ROOT, "script"))
# pyrefly: ignore [missing-import]
import MetricExecuterInputDips as metrics
# pyrefly: ignore [missing-import]
import parser_catalogo


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARTELLA_INTENTI_IDEALI = os.path.join(_PROJECT_ROOT, "intent")


def analizza_differenze_fatti(set_ideale, set_llm):
    """
    Estrae le differenze (rimuovendo i match perfetti), associa i fatti generati a quelli
    gold più simili e identifica quali parametri differiscono.
    Restituisce:
    - dettagli_errori: dizionario {fatto_generato: stringa_con_errore}
    - omissioni_non_associate: set di fatti gold che non hanno trovato associazione
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
                    diffs.append(f"parametro {i+1} errato (atteso: '{arg_man}')")
                    
            if score > best_score:
                best_score = score
                best_match = man
                best_diffs = diffs
                
        if best_match is not None:
            matched_mancanti.add(best_match)
            dettaglio = "Errore: " + ", ".join(best_diffs)
            dettagli_errori[ex] = dettaglio
        else:
            dettagli_errori[ex] = "Allucinazione (nessun predicato gold corrispondente)"
            
    omissioni_non_associate = mancanti - matched_mancanti
    return dettagli_errori, omissioni_non_associate


def processa_cartella(dir_path, mappa_vnf):
    """
    Cerca tutti i file di output in una singola cartella (es. una cartella 'result'),
    crea il report individuale per ciascun file e infine crea un report globale
    (report_valutazione.txt) con le medie di tutti i file trovati in QUELLA cartella.
    
    Restituisce un dizionario con le metriche medie della cartella, oppure None
    se non ci sono file di output da analizzare.
    """
    # Identifica tutti i file di output nella cartella corrente
    files_output = [f for f in os.listdir(dir_path) if f.startswith("output_context") and f.endswith(".txt")]
    
    if not files_output:
        return None
        
    print(f"\nAnalisi cartella: {dir_path}")
    
    # Carica il file dei tempi di esecuzione, se presente
    tempi_path = os.path.join(dir_path, "tempi_esecuzione.json")
    tempi_esecuzione = {}
    if os.path.exists(tempi_path):
        try:
            with open(tempi_path, "r", encoding="utf-8") as f_tempi:
                tempi_esecuzione = json.load(f_tempi)
            print(f"  Caricati tempi di esecuzione da: {tempi_path}")
        except (json.JSONDecodeError, IOError) as e:
            print(f"  Attenzione: errore nel caricamento dei tempi: {e}")
    
    totale_recall = 0.0
    totale_precision = 0.0
    totale_jaccard = 0.0
    totale_f1 = 0.0
    numero_test = 0
    lista_metriche_per_accuracy = []  # lista di (precision, recall) per ogni elemento
    totale_tempo = 0.0
    contatore_tempo = 0
    
    for file_name in sorted(files_output):
        # Estraiamo contesto e lettera intent
        match = re.search(r'output_(context\d+)_intent([A-Za-z]+)\.txt', file_name)
        if not match:
            continue
            
        context_name = match.group(1)
        lettera_intent = match.group(2)
        
        file_path = os.path.join(dir_path, file_name)
        file_ideale = os.path.join(CARTELLA_INTENTI_IDEALI, context_name, "facts.pl")
        file_testo_intento = os.path.join(CARTELLA_INTENTI_IDEALI, context_name, f"intent{lettera_intent}.txt")
        
        if not os.path.exists(file_ideale):
            print(f"  Attenzione: file ideale non trovato per {context_name} ({file_ideale})")
            continue
            
        # Lettura e arricchimento dell'intento testuale
        testo_intento = "Testo dell'intento non trovato."
        if os.path.exists(file_testo_intento):
            with open(file_testo_intento, "r", encoding="utf-8") as f_intento:
                testo_intento = f_intento.read().strip()
                
            if mappa_vnf:
                testo_intento = parser_catalogo.arricchisci_intento_con_hardware(testo_intento, mappa_vnf)
                
        # Calcolo metriche
        set_ideale = metrics.estrai_set_da_pl(file_ideale)
        set_llm = metrics.estrai_set_da_pl(file_path)
        
        recall = metrics.calcola_recall(set_ideale, set_llm)
        precision = metrics.calcola_precision(set_ideale, set_llm)
        jaccard = metrics.calcola_jaccard(set_ideale, set_llm)
        f1 = metrics.calcola_f1(precision, recall)
        
        print(f"  [{context_name} intent{lettera_intent}] R: {recall:.4f} | P: {precision:.4f} | J: {jaccard:.4f} | F1: {f1:.4f}")
        
        # Recupera il tempo di esecuzione per questo file
        tempo_info = tempi_esecuzione.get(file_name, {})
        tempo_esec = tempo_info.get("durata_secondi", None)
        if tempo_esec is not None:
            totale_tempo += tempo_esec
            contatore_tempo += 1
        
        # Raccogli la coppia (precision, recall) per il calcolo dell'accuracy
        lista_metriche_per_accuracy.append((precision, recall))
        
        # Somma per le medie della cartella
        totale_recall += recall
        totale_precision += precision
        totale_jaccard += jaccard
        totale_f1 += f1
        numero_test += 1
        
        # 1) REPORT INDIVIDUALE
        report_name = f"report_{context_name}_intent{lettera_intent}.txt"
        report_path = os.path.join(dir_path, report_name)
        
        with open(report_path, "w", encoding="utf-8") as f_singolo:
            f_singolo.write(f"RISULTATI PER {context_name.upper()} - INTENTO {lettera_intent.upper()}\n")
            f_singolo.write(f"File analizzato: {file_name}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write("--- INTENTO TESTUALE ---\n")
            f_singolo.write(f"{testo_intento}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write(f"Recall    (Omissioni)     : {recall:.4f}\n")
            f_singolo.write(f"Precision (Allucinazioni) : {precision:.4f}\n")
            f_singolo.write(f"Jaccard   (Globale)       : {jaccard:.4f}\n")
            f_singolo.write(f"F1-Score  (Equilibrio)    : {f1:.4f}\n")
            if tempo_esec is not None:
                f_singolo.write(f"Tempo Esecuzione          : {tempo_esec:.4f}s\n")
                f_singolo.write(f"Inizio: {tempo_info.get('timestamp_inizio', 'N/A')} | Fine: {tempo_info.get('timestamp_fine', 'N/A')}\n")
            f_singolo.write("==================================================\n\n")
            
            # Se le metriche sono perfette, stampa semplicemente i fatti
            if recall == 1.0 and precision == 1.0:
                f_singolo.write("--- Fatti Estratti Ideale ---\n")
                f_singolo.write(metrics.set_to_string(set_ideale) + "\n\n")
                f_singolo.write("--- Fatti Estratti LLM ---\n")
                f_singolo.write(metrics.set_to_string(set_llm) + "\n")
            else:
                # Se non sono perfette, applica la funzione di analisi dettagliata
                dettagli_errori, omissioni = analizza_differenze_fatti(set_ideale, set_llm)
                
                f_singolo.write("--- Fatti Estratti Ideale (Gold) ---\n")
                f_singolo.write(metrics.set_to_string(set_ideale) + "\n\n")
                
                f_singolo.write("--- Fatti Estratti LLM (Analisi) ---\n")
                corretti = set_ideale & set_llm
                
                # Fatti corretti
                for c in sorted(corretti):
                    f_singolo.write(f"{c}  [ Corretto]\n")
                    
                # Fatti errati/extra (annotati)
                extra = set_llm - set_ideale
                for ex in sorted(extra):
                    nota = dettagli_errori.get(ex, "")
                    f_singolo.write(f"{ex}  [ {nota}]\n")
                    
                # Omissioni non associate a niente (rimaste indietro)
                if omissioni:
                    f_singolo.write("\n--- Fatti Gold Mancanti (Omissioni assolute) ---\n")
                    for om in sorted(omissioni):
                        f_singolo.write(f"{om}  [ Fatto non generato dal LLM]\n")
            
    # 2) REPORT GLOBALE DELLA CARTELLA
    if numero_test > 0:
        avg_recall = totale_recall / numero_test
        avg_precision = totale_precision / numero_test
        avg_jaccard = totale_jaccard / numero_test
        avg_f1 = totale_f1 / numero_test
        accuracy = metrics.calcola_accuracy(lista_metriche_per_accuracy)
        num_perfetti = sum(1 for p, r in lista_metriche_per_accuracy if p == 1.0 and r == 1.0)
        
        report_globale_path = os.path.join(dir_path, "report_valutazione.txt")
        with open(report_globale_path, "w", encoding="utf-8") as f_out:
            f_out.write(f"RISULTATI MEDI CARTELLA SU {numero_test} TEST\n")
            f_out.write("==================================================\n")
            f_out.write(f"Recall Media      : {avg_recall:.4f}\n")
            f_out.write(f"Precision Media   : {avg_precision:.4f}\n")
            f_out.write(f"Jaccard Medio     : {avg_jaccard:.4f}\n")
            f_out.write(f"F1-Score Medio    : {avg_f1:.4f}\n")
            f_out.write(f"Accuracy          : {accuracy:.4f}  ({num_perfetti}/{numero_test} perfetti)\n")
            if contatore_tempo > 0:
                avg_tempo = totale_tempo / contatore_tempo
                f_out.write(f"Tempo Medio Esec. : {avg_tempo:.4f}s  (su {contatore_tempo} test)\n")
                f_out.write(f"Tempo Totale Esec.: {totale_tempo:.4f}s\n")
            f_out.write("==================================================")
            
        print(f"  -> Accuracy: {accuracy:.4f} ({num_perfetti}/{numero_test} perfetti)")
        if contatore_tempo > 0:
            print(f"  -> Tempo medio: {avg_tempo:.4f}s | Tempo totale: {totale_tempo:.4f}s")
        print(f"  -> Creato report globale per la cartella: {report_globale_path}")
        
        return {
            "cartella": dir_path,
            "num_test": numero_test,
            "recall": avg_recall,
            "precision": avg_precision,
            "jaccard": avg_jaccard,
            "f1": avg_f1,
            "accuracy": accuracy,
            "num_perfetti": num_perfetti,
            "tempo_totale": totale_tempo,
            "tempo_medio": totale_tempo / contatore_tempo if contatore_tempo > 0 else None,
            "num_con_tempo": contatore_tempo,
        }
    
    return None


def genera_report_5fold(risultati_cartelle, output_path):
    """
    Genera un report globale con la media delle metriche di tutte le cartelle
    analizzate nel 5-fold cross-validation.
    """
    if not risultati_cartelle:
        print("Nessun risultato da aggregare per il report 5-fold.")
        return
    
    n = len(risultati_cartelle)
    avg_recall = sum(r["recall"] for r in risultati_cartelle) / n
    avg_precision = sum(r["precision"] for r in risultati_cartelle) / n
    avg_jaccard = sum(r["jaccard"] for r in risultati_cartelle) / n
    avg_f1 = sum(r["f1"] for r in risultati_cartelle) / n
    totale_test = sum(r["num_test"] for r in risultati_cartelle)
    totale_perfetti = sum(r["num_perfetti"] for r in risultati_cartelle)
    accuracy_globale = round(totale_perfetti / totale_test, 4) if totale_test > 0 else 0.0
    avg_accuracy_per_fold = sum(r["accuracy"] for r in risultati_cartelle) / n
    
    # Calcolo tempi globali
    tempi_disponibili = [r for r in risultati_cartelle if r.get("tempo_medio") is not None]
    tempo_totale_globale = sum(r["tempo_totale"] for r in tempi_disponibili)
    num_con_tempo_globale = sum(r["num_con_tempo"] for r in tempi_disponibili)
    tempo_medio_globale = tempo_totale_globale / num_con_tempo_globale if num_con_tempo_globale > 0 else None
    
    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write("REPORT GLOBALE 5-FOLD CROSS-VALIDATION\n")
        f_out.write("=" * 60 + "\n\n")
        f_out.write(f"Numero di fold analizzati: {n}\n")
        f_out.write(f"Numero totale di test: {totale_test}\n\n")
        
        f_out.write("--- DETTAGLIO PER CARTELLA ---\n\n")
        for r in risultati_cartelle:
            nome_cartella = os.path.basename(os.path.dirname(r["cartella"]))
            f_out.write(f"  {nome_cartella} ({r['num_test']} test)\n")
            f_out.write(f"    Recall: {r['recall']:.4f} | Precision: {r['precision']:.4f} | ")
            f_out.write(f"Jaccard: {r['jaccard']:.4f} | F1: {r['f1']:.4f} | ")
            f_out.write(f"Accuracy: {r['accuracy']:.4f} ({r['num_perfetti']}/{r['num_test']})")
            if r.get("tempo_medio") is not None:
                f_out.write(f" | Tempo Medio: {r['tempo_medio']:.4f}s")
            f_out.write("\n\n")
        
        f_out.write("=" * 60 + "\n")
        f_out.write(f"MEDIE GLOBALI SU {n} FOLD ({totale_test} test totali)\n")
        f_out.write("=" * 60 + "\n")
        f_out.write(f"Recall Media      : {avg_recall:.4f}\n")
        f_out.write(f"Precision Media   : {avg_precision:.4f}\n")
        f_out.write(f"Jaccard Medio     : {avg_jaccard:.4f}\n")
        f_out.write(f"F1-Score Medio    : {avg_f1:.4f}\n")
        f_out.write(f"Accuracy Globale  : {accuracy_globale:.4f}  ({totale_perfetti}/{totale_test} perfetti)\n")
        f_out.write(f"Accuracy Media/Fold: {avg_accuracy_per_fold:.4f}\n")
        if tempo_medio_globale is not None:
            f_out.write(f"Tempo Medio Esec. : {tempo_medio_globale:.4f}s  (su {num_con_tempo_globale} test)\n")
            f_out.write(f"Tempo Totale Esec.: {tempo_totale_globale:.4f}s\n")
        f_out.write("=" * 60 + "\n")
    
    print(f"\n=> Report globale 5-fold salvato in: {output_path}")


def main():
    catalogo_json = os.path.join(CARTELLA_INTENTI_IDEALI, "catalogoVNF.json")

    # Carichiamo il catalogo una sola volta
    try:
        mappa_vnf = parser_catalogo.carica_catalogo_vnf(catalogo_json)
    except FileNotFoundError:
        print(f"Attenzione: catalogo VNF non trovato in {catalogo_json}. Il testo degli intenti non verrà arricchito.")
        mappa_vnf = {}

    print("=" * 60)
    print("=== GENERAZIONE REPORT SINGOLI E REPORT GLOBALE PER CARTELLA ===")
    print("=" * 60)

    risultati_cartelle = []

    # Scansiona tutte le cartelle all'interno di BASE_DIR
    for root, dirs, files in os.walk(BASE_DIR):
        risultato = processa_cartella(root, mappa_vnf)
        if risultato is not None:
            risultati_cartelle.append(risultato)

    # Genera il report globale del 5-fold
    report_5fold_path = os.path.join(BASE_DIR, "report_5fold_globale.txt")
    genera_report_5fold(risultati_cartelle, report_5fold_path)

    print("\nElaborazione completata!")


if __name__ == "__main__":
    main()

