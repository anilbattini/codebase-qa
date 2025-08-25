import subprocess

model_name = "llama3.1:latest"
prompt = """You are a codebase search assistant. Convert the following question into a simple, searchable query for searching a android project codebase.

Intent: overview
Original: what does this project do?

Return ONLY a concise search query (no explanations, no alternatives, no markdown). Focus on key terms that would appear in the codebase.

IMPORTANT: For questions about 'what does this project do', 'project overview', or 'main purpose', include terms like: main activity, MainActivity, application, app purpose, project structure, manifest, build.gradle, README, documentation.

Search Query:"""
max_tokens = 1024
temperature = 0.5

# command = ["ollama", "run"]
# args = [
#     "--model-name", model_name,
#     "--max-tokens", str(max_tokens),
#     "--temperature", str(temperature)
# ]

# if prompt:
#     args.append("--prompt")
#     args.append(prompt)
    
command = f"ollama run {model_name} \"{prompt}\""

result = subprocess.run(command, capture_output=True, text=True)

if result.returncode == 0:
    print("Command executed successfully.")
    print(result)
else:
    print(f"Error executing command. Status code: {result.returncode}")
    print(result.stderr)