import torch
from unsloth import FastLanguageModel
from unsloth.chat_templates import get_chat_template
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Programma per addestrare Qwen 2.5 Coder con il chat template nativo

# --- FASE 1: CARICAMENTO DEL MODELLO ---
max_seq_length = 2048

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/Qwen2.5-Coder-7B-Instruct",
    max_seq_length = max_seq_length,
    load_in_4bit = False,
)

# Applichiamo il chat template nativo di Qwen 2.5
# Questo configura il tokenizer per usare i token <|im_start|> e <|im_end|>
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "qwen-2.5",
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 32,
    use_gradient_checkpointing = "unsloth",
)

# --- FASE 2: PREPARAZIONE DEI DATI ---
# Istruzione di sistema estratta direttamente dal dataset

def formatta_dati(examples):
    """Formatta ogni esempio nel formato conversazionale nativo di Qwen 2.5.
    
    Converte i campi instruction/input/output del dataset nel formato:
    [{"role": "system", ...}, {"role": "user", ...}, {"role": "assistant", ...}]
    e poi applica il chat template del tokenizer.
    """
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for inst, inp, out in zip(instructions, inputs, outputs):
        # Combiniamo instruction e input nel messaggio utente
        user_message = inp  # L'input contiene la richiesta in linguaggio naturale
        
        # Costruiamo la conversazione nel formato chat
        conversation = [
            {"role": "system", "content": inst},
            {"role": "user",   "content": user_message},
            {"role": "assistant", "content": out},
        ]
        
        # Applichiamo il template nativo di Qwen 2.5
        text = tokenizer.apply_chat_template(
            conversation,
            tokenize = False,
            add_generation_prompt = False,
        )
        texts.append(text)
    return { "text" : texts }

# MODIFICA QUI: inserisci il percorso del tuo dataset di training
dataset = load_dataset("json", data_files="dataset_train_context1-21_29-34.jsonl", split="train")
dataset = dataset.map(formatta_dati, batched = True)

# --- FASE 3: MOTORE DI ADDESTRAMENTO ---
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 2,      
        gradient_accumulation_steps = 2,      
        num_train_epochs = 5,                
        learning_rate = 2e-4,
        weight_decay = 0.01,                                      
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(), 
        logging_steps = 10,                   
        optim = "adamw_8bit",
        output_dir = "risultati",
        save_strategy = "no",
    ),
)

trainer.train()

# --- FASE 4: SALVATAGGIO ---
# MODIFICA QUI: nome della cartella dove salvare il modello addestrato
model.save_pretrained("../tester/qwen2.5-7b-1-21_29-34")
