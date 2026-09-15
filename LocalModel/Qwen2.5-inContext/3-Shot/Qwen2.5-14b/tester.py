from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
import torch
import json
import os
import time
from datetime import datetime

os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

# Istruzione di sistema (deve essere identica a quella usata in train_qwen.py)
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

EXAMPLES

1)

INPUT:
The financial provider fraudSafeOp requires an antifraud analysis service to manage 200,000 transactions per hour. This system intercepts every digital payment request, compares it with habitual user spending patterns via machine learning, and authorizes the transaction in a few milliseconds. The deployed service chain includes, in order: a <requestInterceptorVF, 8> at the edge, a <profileMatcherVF, 16> at the edge, an <mlAnalyzerVF, 32> in the cloud, a <policyEnforcerVF, 12> in the cloud, and a <responseEmitterVF, 8> in the cloud. Regarding requirements, security is applied after the <requestInterceptorVF, 8>. Furthermore, it is strictly required that the <requestInterceptorVF, 8> and the <profileMatcherVF, 16> are deployed on the same hosting node. Privacy is executed before the <mlAnalyzerVF, 32>. Finally, the provider prefers that the bandwidth from the <mlAnalyzerVF, 32> to the <policyEnforcerVF, 12> remains higher than 1000 Mbps, and that the total chain hardware remains lower than 120 GB.

OUTPUT:
intent(fraudDetectionIntent, fraudSafeOp, 200000, fraudDetectionService).


propertyExpectation(affReq, fraudDetectionIntent, affinity, same, hard, _, _, requestInterceptorVF, profileMatcherVF).
propertyExpectation(bwReq, fraudDetectionIntent, bandwidth, greater, soft, 1000, megabps, mlAnalyzerVF, policyEnforcerVF).
propertyExpectation(hwReq, fraudDetectionIntent, totChainHW, lower, soft, 120, gb, _, _).

propertyExpectation(secReq, fraudDetectionIntent, security, _, requestInterceptorVF, _).
propertyExpectation(privReq, fraudDetectionIntent, privacy, _, _, mlAnalyzerVF).

target(fraudDetectionService, [requestInterceptorVF, profileMatcherVF, mlAnalyzerVF, policyEnforcerVF, responseEmitterVF]).

vnf(requestInterceptorVF, edge, 8).
vnf(profileMatcherVF, edge, 16).
vnf(mlAnalyzerVF, cloud, 32).
vnf(policyEnforcerVF, cloud, 12).
vnf(responseEmitterVF, cloud, 8).

vnfXUser(requestInterceptorVF, l, (1, 200000), 8).
vnfXUser(profileMatcherVF, l, (1, 200000), 16).
vnfXUser(mlAnalyzerVF, l, (1, 200000), 32).
vnfXUser(policyEnforcerVF, l, (1, 200000), 12).
vnfXUser(responseEmitterVF, l, (1, 200000), 8).


2)

INPUT:
The healthcare provider medDiagnosticOp requires a radiology AI diagnostics service to manage 10,000 daily scans. This pipeline receives high-resolution medical images, processes them with computer vision algorithms to highlight suspicious lesions, and stores them securely. The service chain begins with a <dicomIngesterVF, 16> allocated at the edge, specifying compression is applied after it. The chain then connects to a <lesionAnalyzerVF, 32> located in the cloud and a <metadataExtractorVF, 12> located in the cloud; for these two components, it is mandatory that they are isolated on dedicated hardware nodes, while ensuring the bandwidth from the <dicomIngesterVF, 16> to the <lesionAnalyzerVF, 32> remains higher than 500 Mbps. Finally, the system routes the data to a secure <secureArchiverVF, 24> in the cloud, ensuring that data encoding is executed before it.

OUTPUT:
intent(radiologyAIIntent, medDiagnosticOp, 10000, radiologyPipelineService).

propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, lesionAnalyzerVF, _).
propertyExpectation(affReq, radiologyAIIntent, affinity, dedicated, hard, _, _, metadataExtractorVF, _).
propertyExpectation(bwReq, radiologyAIIntent, bandwidth, greater, hard, 500, megabps, dicomIngesterVF, lesionAnalyzerVF).

propertyExpectation(compReq, radiologyAIIntent, compression, _, dicomIngesterVF, _).
propertyExpectation(encReq, radiologyAIIntent, encoding, _, _, secureArchiverVF).

target(radiologyPipelineService, [dicomIngesterVF, lesionAnalyzerVF, metadataExtractorVF, secureArchiverVF]).

vnf(dicomIngesterVF, edge, 16).
vnf(lesionAnalyzerVF, cloud, 32).
vnf(metadataExtractorVF, cloud, 12).
vnf(secureArchiverVF, cloud, 24).

vnfXUser(dicomIngesterVF, l, (1, 10000), 16).
vnfXUser(lesionAnalyzerVF, l, (1, 10000), 32).
vnfXUser(metadataExtractorVF, l, (1, 10000), 12).
vnfXUser(secureArchiverVF, l, (1, 10000), 24).

3)

INPUT:
The financial provider onlineBankOp requires a digital identity verification service to manage 10,000 daily uploads. This service processes photos of documents uploaded by users, verifies their authenticity, and compares the data with international blacklists to prevent money laundering. Specifying that encoding is applied after the initial receiving function, the service begins with a <documentReceiverVF, 12> allocated at the edge. Ensuring that security is executed before the second phase, the chain connects to an <authenticityCheckerVF, 24> located in the cloud. Specifying that privacy is applied after the <amlMatcherVF, 16>, the chain incorporates an <amlMatcherVF, 16> located in the cloud. Finally, ensuring that compression is executed before the final node, the system completes the pipeline with a <profileCreatorVF, 16> located in the cloud.

OUTPUT:
intent(kycVerificationIntent, onlineBankOp, 10000, digitalIdentityService).

propertyExpectation(encReq, kycVerificationIntent, encoding, _, documentReceiverVF, _).
propertyExpectation(secReq, kycVerificationIntent, security, _, _, authenticityCheckerVF).
propertyExpectation(privReq, kycVerificationIntent, privacy, _, amlMatcherVF, _).
propertyExpectation(compReq, kycVerificationIntent, compression, _, _, profileCreatorVF).

target(digitalIdentityService, [documentReceiverVF, authenticityCheckerVF, amlMatcherVF, profileCreatorVF]).

vnf(documentReceiverVF, edge, 12).
vnf(authenticityCheckerVF, cloud, 24).
vnf(amlMatcherVF, cloud, 16).
vnf(profileCreatorVF, cloud, 16).

vnfXUser(documentReceiverVF, l, (1, 10000), 12).
vnfXUser(authenticityCheckerVF, l, (1, 10000), 24).
vnfXUser(amlMatcherVF, l, (1, 10000), 16).
vnfXUser(profileCreatorVF, l, (1, 10000), 16).


FINAL OUTPUT INSTRUCTION
Return ONLY the generated Prolog facts.
Do not include introductory text, conversational filler, or explanations.
"""

# --- FASE 1: CARICAMENTO DEL MODELLO ADDESTRATO ---
# MODIFICA QUI: inserisci il percorso della cartella del modello addestrato
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-Coder-14B-Instruct",
    max_seq_length = 8192,
    load_in_4bit = False,
)

# Applichiamo lo stesso chat template usato durante il training
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
)

FastLanguageModel.for_inference(model)  # Ottimizza il modello per l'inferenza

# --- FASE 2: CARICAMENTO DEL FILE JSON CON LE RICHIESTE ---
# MODIFICA QUI: inserisci il percorso del file JSON di test
percorso_json = "test_context1-34.json"
cartella_output = "./result"

# Crea la cartella per gli output se non esiste
if not os.path.exists(cartella_output):
    os.makedirs(cartella_output)

try:
    with open(percorso_json, "r", encoding="utf-8") as f:
        richieste = json.load(f)
except FileNotFoundError:
    print(f"Errore: Il file '{percorso_json}' non è stato trovato.")
    richieste = []

print(f"Trovate {len(richieste)} richieste da elaborare.")

# Dizionario per raccogliere i tempi di esecuzione
tempi_esecuzione = {}

# --- FASE 3: ELABORAZIONE DI OGNI RICHIESTA ---
for i, item in enumerate(richieste):
    # Gestisce sia una lista di stringhe che una lista di dizionari JSON
    if isinstance(item, dict):
        testo_richiesta = item.get("input", item.get("richiesta", item.get("text", str(item))))
        nome_file = f"output_{item.get('id', i+1)}.txt"
    else:
        testo_richiesta = str(item)
        nome_file = f"output_{i+1}.txt"

    print(f"[{i+1}/{len(richieste)}] Elaborazione richiesta in corso...")

    # Misuriamo il tempo di esecuzione dell'inferenza
    timestamp_inizio = datetime.now()
    tempo_inizio = time.time()

    # Costruiamo la conversazione nel formato chat nativo di Qwen 2.5
    conversation = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": testo_richiesta},
    ]

    # Applichiamo il chat template e tokenizziamo
    prompt = tokenizer.apply_chat_template(
        conversation,
        tokenize = False,
        add_generation_prompt = True,  # Aggiunge <|im_start|>assistant\n per far partire la generazione
    )

    inputs = tokenizer(
        [prompt],
        return_tensors = "pt",
    ).to("cuda")

    # Generiamo la risposta
    outputs = model.generate(**inputs, max_new_tokens = 8192)
    risposta = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    # Fine misurazione tempo
    tempo_fine = time.time()
    timestamp_fine = datetime.now()
    durata_secondi = round(tempo_fine - tempo_inizio, 4)

    # Puliamo la risposta: estraiamo solo l'ultimo messaggio dell'assistant
    try:
        # Con il formato Qwen 2.5 la risposta dell'assistant segue l'ultimo "assistant\n"
        risposta_completa = risposta[0]
        # Cerchiamo l'ultima occorrenza del ruolo assistant nel testo decodificato
        parti = risposta_completa.rsplit("assistant\n", 1)
        if len(parti) > 1:
            risposta_pulita = parti[-1].strip()
        else:
            # Fallback: proviamo con il formato Alpaca nel caso
            risposta_pulita = risposta_completa.split("### Response:")[-1].strip()
    except (IndexError, AttributeError):
        risposta_pulita = risposta[0].strip()  # Fallback generico

    # --- FASE 4: SALVATAGGIO IN UN FILE TXT SEPARATO ---
    percorso_salvataggio = os.path.join(cartella_output, nome_file)
    with open(percorso_salvataggio, "w", encoding="utf-8") as f_out:
        f_out.write(risposta_pulita)

    # Salva il tempo di esecuzione per questo file
    tempi_esecuzione[nome_file] = {
        "durata_secondi": durata_secondi,
        "timestamp_inizio": timestamp_inizio.strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp_fine": timestamp_fine.strftime("%Y-%m-%d %H:%M:%S"),
    }
    print(f"    Tempo di esecuzione: {durata_secondi:.4f}s")

# --- FASE 5: SALVATAGGIO FILE TEMPI DI ESECUZIONE ---
percorso_tempi = os.path.join(cartella_output, "tempi_esecuzione.json")
with open(percorso_tempi, "w", encoding="utf-8") as f_tempi:
    json.dump(tempi_esecuzione, f_tempi, indent=2, ensure_ascii=False)

print(f"\nElaborazione completata. Tutti i risultati sono stati salvati in '{cartella_output}/'.")
print(f"File tempi di esecuzione salvato in: {percorso_tempi}")
