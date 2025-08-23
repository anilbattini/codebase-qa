import os
import torch
from transformers import pipeline

# Set the Hugging Face cache directory
os.environ.pop("TRANSFORMERS_CACHE", None)  # avoid deprecation/path conflicts
if "HF_HOME" not in os.environ:
    username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
    os.environ["HF_HOME"] = f"/Users/{username}/codebase-qa/huggingface"

# Define the model name and parameters
model_name = 'Qwen/Qwen2.5-7B-Instruct'  # You can change this to any other Hugging Face model
prompt = "Hello, world!, how are you buddy"
max_new_tokens = 50  # Use max_new_tokens instead of max_length
temperature = 0.7

# Load the Hugging Face model from the cache directory
generator = pipeline('text-generation', model=model_name)
# # Set the device to use MPS if available
# device = "mps" if torch.backends.mps.is_available() else "cpu"

# # Initialize the Hugging Face model pipeline
# generator = pipeline('text-generation', model=model_name, device=0 if device == "mps" else -1)

# # Use mixed precision if on MPS
# with torch.amp.autocast(device_type='mps' if device == "mps" else 'cpu'):
output = generator(prompt, max_new_tokens=512, num_return_sequences=1, temperature=temperature, truncation=True)

# Extract and print the generated text
response_text = output[0]['generated_text']
print("Generated Text:")
print(response_text)
