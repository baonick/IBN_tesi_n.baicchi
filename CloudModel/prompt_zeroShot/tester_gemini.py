import os
import json
import time
from datetime import datetime
# pyrefly: ignore [missing-import]
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable



API_KEY = os.getenv("GEMINI_API_KEY", "") # insert Gemini key here
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

# Gemini model initialization
model = genai.GenerativeModel(
    model_name="gemini-3.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# ==========================================
# 2. API CALL FUNCTION WITH RETRY
# ==========================================
def chiama_gemini_con_retry(prompt_utente, max_retries=5):
    """
    Automatically handles rate limits (429) and server unavailability (503).
    """
    attesa_secondi = 60
    
    for tentativo in range(1, max_retries + 1):
        try:
            response = model.generate_content(prompt_utente)
            
            # Safety pause of 5 seconds
            time.sleep(5) 
            
            return response.text.strip() if response.text else ""

        except (ResourceExhausted, ServiceUnavailable) as e:
            print(f"\n⚠️ [Attempt {tentativo}/{max_retries}] API Error: {type(e).__name__}")
            print(f"   Quota exceeded or server busy. Pausing for {attesa_secondi}s...")
            time.sleep(attesa_secondi)
            
        except Exception as e:
            errore_str = str(e)
            if "429" in errore_str or "503" in errore_str or "RESOURCE_EXHAUSTED" in errore_str:
                print(f"\n⚠️ [Attempt {tentativo}/{max_retries}] Quota/service block.")
                print(f"   Pausing for {attesa_secondi}s...")
                time.sleep(attesa_secondi)
            else:
                print(f"\n❌ Critical error: {e}")
                raise e

    raise Exception(f"Unable to complete request after {max_retries} attempts.")

# ==========================================
# 3. JSON READING AND TXT SAVING
# ==========================================
def main():
    file_json_input = "test_context33-34.json"  # Insert here the name of your JSON file
    cartella_output = "result_3.5-flash"
    
    # Create the output folder if it doesn't exist
    os.makedirs(cartella_output, exist_ok=True)

    if not os.path.exists(file_json_input):
        print(f"❌ Error: The input file '{file_json_input}' was not found.")
        return

    # Load data from the JSON file
    with open(file_json_input, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    totale = len(dataset)
    print(f"Starting baseline test on {totale} requests extracted from JSON...\n")

    # Dictionary to accumulate execution times
    percorso_json_tempi = os.path.join(cartella_output, "tempi_esecuzione.json")

    # Load already existing times (append) if the file exists
    if os.path.exists(percorso_json_tempi):
        with open(percorso_json_tempi, "r", encoding="utf-8") as f_tempi:
            tempi_esecuzione = json.load(f_tempi)
        print(f"📂 Loaded {len(tempi_esecuzione)} existing times from '{percorso_json_tempi}'.")
    else:
        tempi_esecuzione = {}

    for idx, item in enumerate(dataset, 1):
        # Extracts ID and input text from JSON
        id_richiesta = item.get("id", f"unknown_{idx}")
        intento_testo = item.get("input", "")
        
        if not intento_testo:
            print(f"[{idx}/{totale}] ⚠️ No input found for ID '{id_richiesta}', skipping.")
            continue

        print(f"[{idx}/{totale}] Interrogating Gemini for: {id_richiesta}.txt")

        try:
            # Timestamp BEFORE the API call
            timestamp_inizio = datetime.now()
            t_start = time.time()

            # API call with Rate Limit management
            prolog_generato = chiama_gemini_con_retry(intento_testo)

            # Timestamp AFTER receiving the response
            t_end = time.time()
            timestamp_fine = datetime.now()
            durata_secondi = round(t_end - t_start, 4)

            # Create the file name using the "id" field
            nome_file = f"{id_richiesta}.txt"
            percorso_file = os.path.join(cartella_output, nome_file)

            # Save the result generated by Gemini in the txt file
            with open(percorso_file, "w", encoding="utf-8") as f_out:
                f_out.write(prolog_generato)

            # Record execution times
            tempi_esecuzione[nome_file] = {
                "durata_secondi": durata_secondi,
                "timestamp_inizio": timestamp_inizio.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp_fine": timestamp_fine.strftime("%Y-%m-%d %H:%M:%S")
            }

            # Save the times JSON incrementally (at each iteration)
            with open(percorso_json_tempi, "w", encoding="utf-8") as f_tempi:
                json.dump(tempi_esecuzione, f_tempi, indent=2, ensure_ascii=False)

            print(f"   ⏱️ Response time: {durata_secondi}s")

        except Exception as e:
            print(f"❌ Unable to process item {id_richiesta}: {e}")

    print(f"\n✅ Test completed! The {totale} .txt files have been saved in the '{cartella_output}' folder.")
    print(f"📊 Execution times saved in: {percorso_json_tempi}")

if __name__ == "__main__":
    main()