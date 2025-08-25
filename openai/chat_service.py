from flask import Flask, request, jsonify
import subprocess
import os
import torch
from transformers import pipeline
import sys

# # Add parent directory to path to import from codebase-qa root
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# from logger import log_highlight, log_to_sublog

app = Flask(__name__)

# Set this flag to choose between Ollama and Hugging Face
USE_OLLAMA = True  # Change to True to use Ollama

# Set the Hugging Face cache directory
os.environ.pop("TRANSFORMERS_CACHE", None)  # avoid deprecation/path conflicts
if "HF_HOME" not in os.environ:
    username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
    os.environ["HF_HOME"] = f"/Users/{username}/codebase-qa/huggingface"
    

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    data = request.json
    model_name = data.get('model', 'llama3.1:latest')  # Default to llama3.1:latest if not specified
    messages = data.get('messages', [])
    max_new_tokens = data.get('max_tokens', 3000)  # Use max_new_tokens for Hugging Face
    temperature = data.get('temperature', 0.1)

    # Extract the user prompt from the messages
    prompt = ""
    if messages and isinstance(messages, list):
        for message in messages:
            if message.get('role') == 'user':
                prompt = message.get('content', '')
                
    def log_to_sublog(project_dir, subname, msg):
        """Write to sublog, handling all path resolution internally."""
        logfile = os.path.join(_get_logs_dir(project_dir), subname)
        os.makedirs(os.path.dirname(logfile), exist_ok=True)
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(msg.rstrip() + "\n")

    def _get_logs_dir(project_dir):
        """Internal helper to resolve logs directory consistently."""
        if not project_dir:
            project_dir = "../../"
        
        # Convert to absolute path
        abs_project_dir = os.path.abspath(project_dir)
        
        # Ensure we're pointing to the source project, not the tool
        if abs_project_dir.endswith('/codebase-qa'):
            abs_project_dir = os.path.dirname(abs_project_dir)
        
        # Import ProjectConfig here to avoid circular dependency at module level
        try:
            from config import ProjectConfig 
            
            # Try to get project type from session state or environment
            project_type = None
            try:
                import streamlit as st
                if hasattr(st, 'session_state') and st.session_state.get("selected_project_type"):
                    project_type = st.session_state.selected_project_type
            except:
                pass
            
            # If no project type from session, try to auto-detect
            if not project_type:
                temp_config = ProjectConfig(project_dir=abs_project_dir)
                project_type = temp_config.project_type
            
            # Only create logs directory if project type is selected and not unknown
            if project_type and project_type != "unknown":
                # Build the logs directory path
                logs_dir = os.path.join(abs_project_dir, f"codebase-qa_{project_type}", "logs")
                
                # CRITICAL: Prevent nested logs directories
                # If the path already contains '/logs', don't append another one
                if '/logs' in logs_dir and logs_dir.endswith('/logs'):
                    # Remove any trailing /logs to prevent nesting
                    logs_dir = logs_dir.replace('/logs/logs', '/logs').replace('/logs/logs/', '/logs/')
                
                # Ensure the directory exists
                os.makedirs(logs_dir, exist_ok=True)
                return logs_dir
            else:
                # Fallback to a temporary location if no project type selected
                temp_dir = os.path.join(abs_project_dir, "temp_logs")
                os.makedirs(temp_dir, exist_ok=True)
                return temp_dir
                
        except ImportError:
            # Fallback if config module is not available
            temp_dir = os.path.join(abs_project_dir, "temp_logs")
            os.makedirs(temp_dir, exist_ok=True)
            return temp_dir
    
    if USE_OLLAMA:
        model_name = "llama3.1:latest" # Always override model name for OLLAMA
        # Call the Ollama model using subprocess
        command = f"""ollama run {model_name} {prompt}"""
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        response_text = result.stdout.strip()
    else:
        # Use Hugging Face model
        generator = pipeline('text-generation', model=model_name)
        # # Set the device to use MPS if available
        # device = "mps" if torch.backends.mps.is_available() else "cpu"
        # # Initialize the Hugging Face model pipeline
        # generator = pipeline('text-generation', model=model_name, device=0 if device == "mps" else -1)
        # # Use mixed precision if on MPS
        # with torch.amp.autocast(device_type='mps' if device == "mps" else 'cpu'):
        output = generator(prompt, max_new_tokens=2000, num_return_sequences=1, temperature=temperature, truncation=True)
        # Extract and print the generated text
        response_text = output[0]['generated_text']

    log_to_sublog(".", "chat_service.log", f"✅ Received request with prompt: {prompt} \n Response: \n{response_text}")
    # Construct the response in OpenAI format
    response = {
        'id': 'cmpl-123456',
        'object': 'chat.completion',
        'created': 1234567890,
        'model': model_name,
        'choices': [{
            'message': {
                'role': 'assistant',
                'content': response_text
            },
            'index': 0,
            'finish_reason': 'stop'
        }],
        'usage': {
            'prompt_tokens': len(prompt.split()),
            'completion_tokens': len(response_text.split()),
            'total_tokens': len(prompt.split()) + len(response_text.split())
        }
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(port=5000)
