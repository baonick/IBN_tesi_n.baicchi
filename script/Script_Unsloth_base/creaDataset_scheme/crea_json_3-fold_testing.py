import os
import json

#in questo programma non viene chiamto il parser

def main():
    base_dir = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\intenti2.0"
    output_dir = r"C:\Users\nbaic\Desktop\IBN_tesi_n.baicchi\script\3-fold"
    
    # Dictionaries to hold the intents
    intents = {
        'A': [],
        'B': [],
        'C': []
    }
    
    # Iterate over context directories
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} not found.")
        return

    for context_name in os.listdir(base_dir):
        context_path = os.path.join(base_dir, context_name)
        
        # Check if it's a directory and starts with 'context'
        if os.path.isdir(context_path) and context_name.startswith('context'):
            # For each type A, B, C
            for intent_type in ['A', 'B', 'C']:
                intent_filename = f"intent{intent_type}.txt"
                intent_path = os.path.join(context_path, intent_filename)
                
                if os.path.exists(intent_path):
                    with open(intent_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        
                    # We store it as a dict to use the 'id' and 'input' format supported by tester.py
                    intents[intent_type].append({
                        "id": f"{context_name}_intent{intent_type}",
                        "input": content
                    })
    
    # Write to JSON files
    for intent_type, data in intents.items():
        if data:
            output_file = os.path.join(output_dir, f"test_intent{intent_type}.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print(f"Creato {output_file} con {len(data)} intenti di tipo {intent_type}.")

if __name__ == "__main__":
    main()
