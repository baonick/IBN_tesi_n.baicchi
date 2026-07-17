import os
import sys
import re

# Aggiungiamo il percorso dello script di validazione per poterlo importare
sys.path.append(r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script_Validazione")
import MetricExecuterInputDips as metrics

def main():
    cartella_risultati = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\3-fold\AC_on_B\result"
    cartella_intenti_ideali = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\intenti2.0"
    
    if not os.path.exists(cartella_risultati):
        print(f"Errore: la cartella {cartella_risultati} non esiste.")
        return
        
    risultati_files = [f for f in os.listdir(cartella_risultati) if f.startswith("output_context") and f.endswith(".txt")]
    
    if not risultati_files:
        print("Nessun file di output trovato nella cartella result.")
        return
        
    totale_recall = 0.0
    totale_precision = 0.0
    totale_jaccard = 0.0
    totale_f1 = 0.0
    numero_test = 0
    
    print("=== INIZIO VALUTAZIONE RISULTATI 3-FOLD ===\n")
    
    for file_name in risultati_files:
        # Estraiamo il nome del contesto (es. 'context10' da 'output_context10_intentC.txt')
        match = re.search(r'output_(context\d+)_', file_name)
        if not match:
            continue
            
        context_name = match.group(1)
        
        file_llm = os.path.join(cartella_risultati, file_name)
        file_ideale = os.path.join(cartella_intenti_ideali, context_name, "facts.pl")
        
        # Definiamo il percorso per il file di testo dell'intento
        file_testo_intento = os.path.join(cartella_intenti_ideali, context_name, "intentB.txt")
        
        if not os.path.exists(file_ideale):
            print(f"Attenzione: file ideale non trovato per {context_name} ({file_ideale})")
            continue
            
        # Leggiamo il contenuto dell'intento testuale, se esiste
        testo_intento = "Testo dell'intento non trovato."
        if os.path.exists(file_testo_intento):
            with open(file_testo_intento, "r", encoding="utf-8") as f_intento:
                testo_intento = f_intento.read().strip()
                
        # Usiamo le funzioni di MetricExecuterInputDips
        set_ideale = metrics.estrai_set_da_pl(file_ideale)
        set_llm = metrics.estrai_set_da_pl(file_llm)
        
        recall = metrics.calcola_recall(set_ideale, set_llm)
        precision = metrics.calcola_precision(set_ideale, set_llm)
        jaccard = metrics.calcola_jaccard(set_ideale, set_llm)
        f1 = metrics.calcola_f1(precision, recall)
        
        totale_recall += recall
        totale_precision += precision
        totale_jaccard += jaccard
        totale_f1 += f1
        numero_test += 1
        
        print(f"[{context_name}] R: {recall:.4f} | P: {precision:.4f} | J: {jaccard:.4f} | F1: {f1:.4f}")
        
        # Salviamo il report per il singolo contesto includendo l'intento testuale
        report_singolo_path = os.path.join(cartella_risultati, f"report_{context_name}.txt")
        with open(report_singolo_path, "w", encoding="utf-8") as f_singolo:
            f_singolo.write(f"RISULTATI PER {context_name.upper()}\n")
            f_singolo.write(f"File analizzato: {file_name}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write("--- INTENTO TESTUALE ---\n")
            f_singolo.write(f"{testo_intento}\n")
            f_singolo.write("==================================================\n")
            f_singolo.write(f"Recall    (Omissioni)     : {recall:.4f}\n")
            f_singolo.write(f"Precision (Allucinazioni) : {precision:.4f}\n")
            f_singolo.write(f"Jaccard   (Globale)       : {jaccard:.4f}\n")
            f_singolo.write(f"F1-Score  (Equilibrio)    : {f1:.4f}\n")
            f_singolo.write("==================================================\n\n")
            
            f_singolo.write("--- Fatti Estratti Ideale ---\n")
            f_singolo.write(metrics.set_to_string(set_ideale) + "\n\n")
            f_singolo.write("--- Fatti Estratti LLM ---\n")
            f_singolo.write(metrics.set_to_string(set_llm) + "\n")

    if numero_test > 0:
        avg_recall = totale_recall / numero_test
        avg_precision = totale_precision / numero_test
        avg_jaccard = totale_jaccard / numero_test
        avg_f1 = totale_f1 / numero_test
        
        print("==================================================")
        print("RISULTATI MEDI GLOBALI SU", numero_test, "TEST")
        print("==================================================")
        print(f"Recall Media      (Omissioni)     : {avg_recall:.4f}")
        print(f"Precision Media   (Allucinazioni) : {avg_precision:.4f}")
        print(f"Jaccard Medio     (Globale)       : {avg_jaccard:.4f}")
        print(f"F1-Score Medio    (Equilibrio)    : {avg_f1:.4f}")
        print("==================================================")
        
        # Salviamo un piccolo report
        report_path = os.path.join(cartella_risultati, "report_valutazione.txt")
        with open(report_path, "w", encoding="utf-8") as f_out:
            f_out.write(f"RISULTATI MEDI SU {numero_test} TEST\n")
            f_out.write(f"Recall: {avg_recall:.4f}\n")
            f_out.write(f"Precision: {avg_precision:.4f}\n")
            f_out.write(f"Jaccard: {avg_jaccard:.4f}\n")
            f_out.write(f"F1-Score: {avg_f1:.4f}\n")
        print(f"\nReport salvato in {report_path}")

if __name__ == "__main__":
    main()