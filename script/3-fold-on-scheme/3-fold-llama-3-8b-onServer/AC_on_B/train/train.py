import torch
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

#programma per addestrre un modello si inserisce il modello e li si passa il dataset

# --- FASE 1: CARICAMENTO DEL MODELLO ---
max_seq_length = 2048

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b",
    max_seq_length = max_seq_length,
    load_in_4bit = False,
)

model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    lora_alpha = 16,
    use_gradient_checkpointing = "unsloth",
)

# --- FASE 2: PREPARAZIONE DEI DATI ---
prompt_template = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token

def formatta_dati(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for inst, inp, out in zip(instructions, inputs, outputs):
        text = prompt_template.format(inst, inp, out) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts }

dataset = load_dataset("json", data_files="dataset_train_AC.jsonl", split="train")
dataset = dataset.map(formatta_dati, batched = True)

# --- FASE 3: MOTORE DI ADDESTRAMENTO ---
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    args = TrainingArguments(
        per_device_train_batch_size = 8,      # Aumentato da 1 a 8 per la A100
        gradient_accumulation_steps = 4,      # Ridotto da 8 a 4
        # max_steps = 60,                     # RIMOSSO: meglio usare le epoche per un vero addestramento
        num_train_epochs = 1,                 # Fai 1 o 3 giri completi su tutto il dataset
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(), # La A100 userà automaticamente bf16 (più veloce)
        logging_steps = 10,
        optim = "adamw_8bit",                 # Va benissimo per ottimizzare ulteriormente
        output_dir = "risultati",
        save_strategy = "no",
    ),
)

trainer.train()

# --- FASE 4: SALVATAGGIO ---
model.save_pretrained("lama-3-8b-trainOn-AC")