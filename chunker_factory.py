# chunker_factory.py

import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Utility to wrap text chunks into structured form
def format_chunks(chunks, file_type):
    return [
        {
            "content": chunk.strip(),
            "type": detect_chunk_type(chunk, file_type),
            "name": extract_chunk_name(chunk, file_type)
        }
        for chunk in chunks if len(chunk.strip()) > 50
    ]

def detect_chunk_type(chunk: str, lang: str) -> str:
    chunk = chunk.strip().lower()
    if chunk.startswith("class") or "class " in chunk: return "class"
    if "fun " in chunk or "def " in chunk: return "function"
    if "interface" in chunk: return "interface"
    if "@interface" in chunk or "annotation" in chunk: return "annotation"
    return "other"

def extract_chunk_name(chunk: str, lang: str) -> str:
    try:
        if lang == "java":
            match = re.search(r'(class|interface|enum)\s+(\w+)', chunk)
        elif lang == "kotlin":
            match = re.search(r'(class|object|interface|fun)\s+(\w+)', chunk)
        elif lang == "python":
            match = re.search(r'(def|class)\s+(\w+)', chunk)
        elif lang in ("js", "ts"):
            match = re.search(r'(function|class|const|let|var)\s+(\w+)', chunk)
        else:
            return None
        return match.group(2) if match else None
    except:
        return None

def java_chunker(content):
    pattern = r"(?=^[ \t]*(public|protected|private)?[ \t]*(class|interface|enum|@interface|void|[\w<>\[\]]+\s+\w+\s*\(.*\))[^{]*\{)"
    raw_chunks = re.split(pattern, content, flags=re.MULTILINE)
    return format_chunks(raw_chunks, "java")

def kotlin_chunker(content):
    pattern = r"(?=^[ \t]*(class|object|interface|fun|@[\w]+)[ \t]+\w+\s*\(?.*\)?\s*:?)"
    raw_chunks = re.split(pattern, content, flags=re.MULTILINE)
    return format_chunks(raw_chunks, "kotlin")

def js_ts_chunker(content):
    pattern = r"(?=^[ \t]*(export\s+)?(async\s+)?(function|const|let|var|class)\s+\w+)"
    raw_chunks = re.split(pattern, content, flags=re.MULTILINE)
    return format_chunks(raw_chunks, "js")

def python_chunker(content):
    pattern = r"(?=^[ \t]*(@\w+\s*)*(class|def)\s+\w+\s*\(?.*?\)?:)"
    raw_chunks = re.split(pattern, content, flags=re.MULTILINE)
    return format_chunks(raw_chunks, "python")

def fallback_chunker(content):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return [{"content": chunk, "type": "text", "name": None} for chunk in splitter.split_text(content)]

def get_chunker(file_extension):
    ext = file_extension.lower()
    if ext == ".java":
        return java_chunker
    elif ext in [".kt", ".kts"]:
        return kotlin_chunker
    elif ext in [".js", ".ts"]:
        return js_ts_chunker
    elif ext == ".py":
        return python_chunker
    else:
        return fallback_chunker
    

def summarize_chunk(chunk: str, filename: str) -> str:
    # Simple heuristic: short summary using filename and first line
    first_line = chunk.strip().splitlines()[0] if chunk.strip() else "No content"
    return f"From {filename}: {first_line[:80]}"
