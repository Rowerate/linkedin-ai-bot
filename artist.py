import os
from huggingface_hub import InferenceClient
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

def generate_hf_image(visual_prompt):
    """
    Calls the FLUX.1-schnell text-to-image generative AI model 
    natively using the official Hugging Face Hub client library.
    """
    # Pull the universal token from the environment
    hf_token = os.environ.get("HF_TOKEN")
    
    if not hf_token:
        raise ValueError("HF_TOKEN is missing from your environment variables.")
        
    # Initialize the official client
    client = InferenceClient(token=hf_token)
    
    print("Sending generation request to FLUX generative AI model...")
    
    # Execute the text-to-image generation model
    image = client.text_to_image(
        prompt=visual_prompt,
        model="black-forest-labs/FLUX.1-schnell"
    )
    
    image.load()

    return image