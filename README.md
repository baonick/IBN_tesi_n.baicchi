# LLM Intent-to-Prolog Translation for DIPS

Framework sperimentale per la traduzione automatica di intenti di rete espressi in linguaggio naturale in fatti logici formali Prolog compatibili con il framework **DIPS**(Declarative Intent Processing System).  

Il repository implementa e confronta due strategie di adattamento di modelli linguistici in scenari con scarsità di dati:
- **In-Context Learning (ICL):** Valutazione in configurazioni *0-shot*, *3-shot* e *9-shot*.
- **Parameter-Efficient Fine-Tuning (PEFT via LoRA):** Addestramento con validazione incrociata *5-Fold Cross-Validation* partizionata a livello di contesto semantico per prevenire il data leakage.

## Struttura del Repository

IBN github/
├── CloudModel/                                 # Modello Gemini 3.5 flash (Cloud)
│   ├── prompt_fewShot/                         # Valutazione In-Context Learning 3-shot e 9-shot
│   └── prompt_zeroShot/                        # Valutazione In-Context Learning 0-shot
├── dips/                                       # File sorgente e regole formali DIPS (Prolog)
├── intent/                                     # Dataset di intenti in 3 differenti formati
├── LocalModel/
│   ├── Qwen2.5-inContext/
│   │   ├── zeroShot/                           # Script Qwen ICL 0-shot (3B, 7B, 14B)
│   │   ├── 3-Shot/                             # Script Qwen ICL 3-shot (3B, 7B, 14B)
│   │   └── 9-Shot/                             # Script Qwen ICL 9-shot (3B, 7B, 14B)
│   └── Qwen2.5-LoRa/
│       ├── 5-fold-Qwen2.5-3B/                  # Esperimenti 5-Fold per Qwen 3B
│       ├── 5-fold-Qwen2.5-7B/                  # Esperimenti 5-Fold per Qwen 7B
│       ├── 5-fold-Qwen2.5-14B/                 # Esperimenti 5-Fold per Qwen 14B
│       ├── esegui_creazione_dataset_json.py    # Preparazione dataset partizionato per i fold
│       ├── esegui_pipeline.py                  # Pipeline completa training LoRA e inferenza
│       └── esegui_valutazione.py               # Calcolo metriche globali e per-fold
├── script/
│   ├── DipsExecuter.py                         # Esecuzione query DIPS
│   ├── MetricExecuterInputDips.py              # Calcolo metriche su sintassi Prolog (F1, Recall, Exact Match)
│   ├── catalogo_errori.py                      # Tassonomia e tracciamento errori sintattici/logici
│   └── parser_catalogo.py                      # Parsing degli intenti di test
├── prompts.txt                                 # Definizioni dei template di prompt (LoRA e ICL)
└── README.md




## Requisiti di Sistema e Dipendenze

**Hardware & Sistema**
* **Sistema Operativo:** Linux
* **GPU:** NVIDIA con supporto CUDA (compute capability adeguata per modelli 3B–14B)
* **Driver & Toolkit:** NVIDIA CUDA Toolkit (v12.4 consigliata)
* **Storage:** Spazio su disco sufficiente per pesi dei modelli e cache Hugging Face (`HF_HOME`)

**Software di Rete & Logica**
* **SWI-Prolog (`swipl`):** Necessario per l'esecuzione del framework DIPS e la validazione dei fatti Prolog generati

**Librerie Python Core**
* **Python:** 3.10+
* **PyTorch (`torch`, `torchvision`, `torchaudio`):** Compilato con supporto CUDA
* **Unsloth:** Framework di accelerazione e ottimizzazione memoria per PEFT/LoRA
* **Transformers, Datasets & Accelerate:** Gestione modelli Hugging Face e pipeline di training
* **google-genai** / **requests:** Interfacciamento API per i test su modelli in cloud (Gemini / gateway OpenRouter)






### Descrizione degli Script Principali

*   **`esegui_pipeline.py`**
    Questo è lo script di orchestrazione principale, progettato per automatizzare l'esecuzione batch dei test su tutte le varianti dimensionali del modello locale (3B, 7B e 14B). Il suo comportamento si adatta dinamicamente in base alla directory in cui viene eseguito:
    *   **In ambiente LoRA:** Gestisce automaticamente l'intera coda di esecuzione, avviando in sequenza l'addestramento e la successiva inferenza per tutti i 5 fold, ripetendo il processo per i modelli da 3B, 7B e 14B.
    *   **In ambiente In-Context** Esegue sequenzialmente i test di inferenza per i tre modelli (3B, 7B, 14B), applicando tutti i vari set di prompt (0-shot, 3-shot, 9-shot) a tutto il dataset di test.
    *   **`esegui_valutazione.py`** Questo script è responsabile dell'analisi prestazionale e del calcolo delle metriche. Si occupa di confrontare i fatti Prolog generati dai modelli (salvati all'interno delle cartelle dei risultati) con il *ground truth* atteso presente nel dataset originale degli intenti. Il calcolo delle metriche (F1-Score, Accuracy Globale/Exact Match, Precision, Recall e Jaccard Index) avviene in modo ricorsivo: nel caso del LoRA, lo script attraversa in automatico tutti i fold, analizzando le singole iterazioni. Al termine dell'esecuzione, genera e salva dei report di testo dettagliati per ogni modello e configurazione analizzata.
    *   **`esegui_creazione_dataset_json.py`** Questo script si occupa di generare i file JSON strutturati che verranno forniti in input ai modelli sia per la fase di addestramento (Train) che per i test di inferenza. 
    Risulta fondamentale qualora si decida di espandere o modificare il dataset originale: eseguendo lo script, tutte le partizioni necessarie vengono rigenerate. Nel progetto è presente anche un file master che, sfruttando `os.walk`, rintraccia e avvia a cascata tutti gli script di creazione dataset presenti nelle varie sottocartelle.
    * **Nota di configurazione:** Le regole di partizionamento (come il numero totale di contesti o il range assegnato a ciascun fold) sono definite direttamente all'interno del codice. Qualora si aggiungano nuovi elementi al dataset (oltre i 34 contesti attuali), sarà necessario aggiornare manualmente queste variabili all'interno dello script prima di eseguirlo.
    *   **`catalogo_errori.py`**
    Questo script si occupa dell'analisi qualitativa dei risultati. Va eseguito a valle dell'inferenza e del calcolo delle metriche generali. Attraversando automaticamente tutte le directory dei risultati, effettua un parsing avanzato dei fatti Prolog generati per identificare la natura esatta degli errori commessi dai modelli. Al termine, genera una cartella contenente report diagnostici dettagliati. 
    Per fornire una tassonomia precisa, gli errori sono classificati in quattro macro-categorie (di cui le ultime tre ulteriormente divise in sotto-categorie specifiche):
    *   **Sintassi:** Errori di formattazione che impediscono la compilazione in Prolog.
    *   **Valori errati:** Assegnazione scorretta di parametri, attributi (es. `hard`/`soft`) o topologie (`Before`/`After`).
    *   **VNF errate:** Allucinazione di Network Function inesistenti o scambio di nodi validi.
    *   **Inserzioni e Rimozioni:** Fatti Prolog aggiunti in eccesso (non richiesti) o mancanti rispetto al *ground truth*.
    *   **`DipsExecuter.py`**
    Questo script funge da interfaccia diretta tra le predizioni generate dai modelli linguistici e il framework logico DIPS. Attraversa in modo automatizzato l'intero progetto per individuare tutti i file di risultato generati, rispettando rigorosamente la gerarchia delle sottocartelle, e li sottopone all'esecuzione diretta in DIPS. Questo passaggio è cruciale per validare sul campo se il codice Prolog generato (anche qualora sintatticamente corretto e privo di errori di battitura) viene effettivamente accettato, elaborato e validato dal framework di rete ricevente.



### Il dataset proprietario utilizzato per questo esperimento è stato costruito per valutare la capacità di astrazione dei modelli. È composto da un nucleo di **34 contesti di rete originali**, ciascuno espanso in tre varianti strutturali (per un totale di 102 campioni):

- **Schema A:** Formulazione standard e diretta.
- **Schema B:** Formulazione passiva o con struttura sintattica invertita.
- **Schema C:** Formulazione discorsiva frammentata.

Per garantire la validità scientifica (evitando il *data leakage*), la **5-Fold Cross-Validation** nel training LoRA non separa le singole frasi, ma isola i contesti semantici interi. In questo modo il modello in fase di test affronta sempre topologie e catene VNF mai viste durante l'addestramento. 


## 🚀 Quick Start (Pipeline di Esecuzione)

L'ambiente e i dataset sono già preconfigurati. Il flusso di esecuzione è standardizzato e risulta identico per entrambe le strategie analizzate nel progetto (In-Context Learning e LoRA). 

Per riprodurre i test, segui questi semplici passaggi:

1. **Naviga nella cartella di test desiderata:** Posizionati all'interno della directory della strategia che intendi eseguire (all'interno di `LocalModel`).
   ```bash
   # Esempio: Entra nella cartella dell'In-Context Learning
   cd LocalModel/Qwen2.5-inContext/
   
   # OPPURE nella cartella del LoRA
   # cd LocalModel/Qwen2.5-LoRa/
   ```
2. **Esegui la pipeline principale:** Avvia lo script di orchestrazione per avviare i test in sequenza.
   ```bash
   python esegui_all_pipeline.py

3. **Avvia il tool di valutazione:** Una volta completata l'inferenza, esegui lo script di valutazione per analizzare i risultati.
   ```bash
   python esegui_valutazione.py
   ```


## Contesto del Progetto e Autore

Questo progetto è stato sviluppato come parte di un lavoro di Tesi presso l'**Università di Pisa**. 
Gli intenti generati da questa pipeline sono progettati specificamente per alimentare **DIPS**, un framework basato su logica dichiarativa (Prolog) per la modellazione, la traduzione e la risoluzione dei conflitti degli intenti di rete.

- **Autore:** Niccolò Baicchi
- **Istituzione:** Università di Pisa