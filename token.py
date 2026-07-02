import tiktoken
import os

def check_file_tokens(file_path):
    # 1. Check if the file actually exists
    if not os.path.exists(file_path):
        print(f"❌ Error: Could not find the file at '{file_path}'")
        return
        
    # 2. Read the markdown text
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # 3. Load the tokenizer and count
    # 'cl100k_base' is the standard encoding for most modern LLMs
    encoding = tiktoken.get_encoding("cl100k_base") 
    tokens = len(encoding.encode(text))
    
    print("-" * 40)
    print(f"📄 File: {file_path}")
    print(f"📊 Token Count: {tokens:,} tokens")
    print("-" * 40)

# Point this directly to the file you just extracted
file_to_check = "saved_context/wcms_856976_extracted.md"
check_file_tokens(file_to_check)