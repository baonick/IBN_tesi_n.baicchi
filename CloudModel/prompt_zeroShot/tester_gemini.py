import os
import json
import time
from datetime import datetime
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable



API_KEY = os.getenv("GEMINI_API_KEY", "")#inserire chiave di gemini qui
genai.configure(api_key=API_KEY)

SYSTEM_PROMPT = """ROLE AND OBJECTIVE
You are an expert networking logic parser. Your task is to extract information from a natural language network intent and translate it into formal Prolog facts using ONLY the strictly defined schema below. You must not hallucinate, invent, or assume any information outside the provided text.


STEP 1: VNF CHAIN IDENTIFICATION & GROUNDING
- Identify the exact chain of Virtual Network Functions (VNFs) explicitly requested in the input text.
- This VNF chain constitutes the list of VNFs inside the target fact:
  target(ServiceName, [vnf1, vnf2, ...]).
- CRITICAL: For all subsequent Prolog facts (vnf, vnfXUser, propertyExpectation), you MUST USE ONLY the VNFs from this exact target list.


STEP 2: VOCABULARY AND KEYWORD MAPPING

Strictness Mapping:
- "must", "strictly", "required", "guaranteeing", "ensuring", "mandatory" -> hard
- "prefer", "optimally", "should", "desired", "if possible" -> soft

Operator Mapping:
- "greater than", "higher than", "above" -> greater
- "lower than", "below", "less than" -> lower

Unit Mapping:
- "Mbps", "megabps" -> megabps
- "ms", "milliseconds" -> ms
- "GB", "gigabytes" -> gb


STEP 3: TOPOLOGY AND PROPERTY MAPPING (BEFORE vs AFTER)
When mapping Changing Properties (like security, decoding, etc.), topology depends on the preposition in the text.
Use the underscore "_" to denote an empty or unspecified argument.

- AFTER Rule:
  If "[Service] AFTER [VnfID]", Source is VnfID and Destination is "_".
  Template: propertyExpectation(PropID, IntentID, Type, _, VnfID, _).

- BEFORE Rule:
  If "[Service] BEFORE [VnfID]", Source is "_" and Destination is VnfID.
  Template: propertyExpectation(PropID, IntentID, Type, _, _, VnfID).


STEP 4: STRICT PROLOG SCHEMA DEFINITIONS
Generate the output using EXACTLY these formats. Do not add extra parameters. Note on PropIDs: You must invent unique identifiers for each PropID (e.g., prop1, prop2, prop3). These identifiers have no semantic meaning in the results, but they must be strictly unique within your generated response.

1. Intent & Target:
- intent(IntentID, ProviderOp, NumUsers, ServiceName).
  (Note: IntentID must end in 'Intent', ProviderOp in 'Op')
- target(ServiceName, [vnf1, vnf2, ...]).

2. Nodes (Hardware & Computing):
- vnf(VnfID, edge/cloud, HardwareValue).
- vnfXUser(VnfID, l, (1, NumUsers), HardwareValue).

3. Non-Changing Properties (Expects EXACTLY 9 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, Operator, hard/soft, Value, Unit, SourceVNF, DestVNF).
- Valid Types: bandwidth, latency, totChainHW, affinity
- Affinity Values: dedicated, same
- Note: For affinity and totChainHW, use "_" for Operator, Value, Unit, Source, or Dest where not applicable.

4. Changing Properties (Expects EXACTLY 6 parameters):
- Template: propertyExpectation(PropID, IntentID, Type, _, Source, Destination).
- Note: The 4th parameter is ALWAYS "_".
- Valid Types: security, compression, logging, privacy, caching, decoding, encoding


FINAL OUTPUT INSTRUCTION
Return ONLY the generated Prolog facts.
Do not include introductory text, conversational filler, or explanations.
"""

# Inizializzazione del modello Gemini
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# ==========================================
# 2. FUNZIONE CHIAMATA API CON RETRY
# ==========================================
def chiama_gemini_con_retry(prompt_utente, max_retries=5):
    """
    Gestisce in automatico i limiti di frequenza (429) e l'indisponibilità del server (503).
    """
    attesa_secondi = 60
    
    for tentativo in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt_utente)
            
            # Pausa di sicurezza di 4 secondi
            time.sleep(5) 
            
            return response.text.strip() if response.text else ""

        except (ResourceExhausted, ServiceUnavailable) as e:
            print(f"\n⚠️ [Tentativo {tentativo}/{max_retries}] Errore API: {type(e).__name__}")
            print(f"   Quota superata o server occupato. In pausa per {attesa_secondi}s...")
            time.sleep(attesa_secondi)
            
        except Exception as e:
            errore_str = str(e)
            if "429" in errore_str or "503" in errore_str or "RESOURCE_EXHAUSTED" in errore_str:
                print(f"\n⚠️ [Tentativo {tentativo}/{max_retries}] Blocco di quota/servizio.")
                print(f"   In pausa per {attesa_secondi}s...")
                time.sleep(attesa_secondi)
            else:
                print(f"\n❌ Errore critico: {e}")
                raise e

    raise Exception(f"Impossibile completare la richiesta dopo {max_retries} tentativi.")

# ==========================================
# 3. LETTURA JSON E SALVATAGGIO IN TXT
# ==========================================
def main():
    file_json_input = "test_context33-34.json"  # Inserisci qui il nome del tuo file JSON
    cartella_output = "result_3.5-flash"
    
    # Crea la cartella di output se non esiste
    os.makedirs(cartella_output, exist_ok=True)

    if not os.path.exists(file_json_input):
        print(f"❌ Errore: Il file di input '{file_json_input}' non è stato trovato.")
        return

    # Carica i dati dal file JSON
    with open(file_json_input, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    totale = len(dataset)
    print(f"Avvio test di baseline su {totale} richieste estratte dal JSON...\n")

    # Dizionario per accumulare i tempi di esecuzione
    percorso_json_tempi = os.path.join(cartella_output, "tempi_esecuzione.json")

    # Carica i tempi già esistenti (append) se il file esiste
    if os.path.exists(percorso_json_tempi):
        with open(percorso_json_tempi, "r", encoding="utf-8") as f_tempi:
            tempi_esecuzione = json.load(f_tempi)
        print(f"📂 Caricati {len(tempi_esecuzione)} tempi esistenti da '{percorso_json_tempi}'.")
    else:
        tempi_esecuzione = {}

    for idx, item in enumerate(dataset, 1):
        # Estrae l'ID e il testo di input dal JSON
        id_richiesta = item.get("id", f"sconosciuto_{idx}")
        intento_testo = item.get("input", "")
        
        if not intento_testo:
            print(f"[{idx}/{totale}] ⚠️ Nessun input trovato per l'ID '{id_richiesta}', salto.")
            continue

        print(f"[{idx}/{totale}] Interrogazione Gemini per: {id_richiesta}.txt")

        try:
            # Timestamp PRIMA della chiamata API
            timestamp_inizio = datetime.now()
            t_start = time.time()

            # Chiamata API con gestione del Rate Limit
            prolog_generato = chiama_gemini_con_retry(intento_testo)

            # Timestamp DOPO la risposta ricevuta
            t_end = time.time()
            timestamp_fine = datetime.now()
            durata_secondi = round(t_end - t_start, 4)

            # Crea il nome del file usando il campo "id"
            nome_file = f"{id_richiesta}.txt"
            percorso_file = os.path.join(cartella_output, nome_file)

            # Salva il risultato generato da Gemini nel file txt
            with open(percorso_file, "w", encoding="utf-8") as f_out:
                f_out.write(prolog_generato)

            # Registra i tempi di esecuzione
            tempi_esecuzione[nome_file] = {
                "durata_secondi": durata_secondi,
                "timestamp_inizio": timestamp_inizio.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_fine": timestamp_fine.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Salva il JSON dei tempi in modo incrementale (ad ogni iterazione)
            with open(percorso_json_tempi, "w", encoding="utf-8") as f_tempi:
                json.dump(tempi_esecuzione, f_tempi, indent=2, ensure_ascii=False)

            print(f"   ⏱️ Tempo risposta: {durata_secondi}s")

        except Exception as e:
            print(f"❌ Impossibile elaborare l'elemento {id_richiesta}: {e}")

    print(f"\n✅ Test completato! I {totale} file .txt sono stati salvati nella cartella '{cartella_output}'.")
    print(f"📊 Tempi di esecuzione salvati in: {percorso_json_tempi}")

if __name__ == "__main__":
    main()