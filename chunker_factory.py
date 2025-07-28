import os
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

def java_chunker(content):
    pattern = r"(?=^.*\b(public|protected|private)?\s*(class|interface|enum|@interface|void|[\w<>]+\s+\w+\s*\(.*\))\b)"
    return [chunk.strip() for chunk in re.split(pattern, content, flags=re.MULTILINE) if len(chunk.strip()) > 50]

def kotlin_chunker(content):
    pattern = r"(?=^.*\b(class|object|interface|fun|@[\w]+)\s+\w+\s*\(?.*\)?\s*:?)"
    return [chunk.strip() for chunk in re.split(pattern, content, flags=re.MULTILINE) if len(chunk.strip()) > 50]

def js_ts_chunker(content):
    pattern = r"(?=^.*\b(export\s+)?(async\s+)?(function|const|let|var|class)\b)"
    return [chunk.strip() for chunk in re.split(pattern, content, flags=re.MULTILINE) if len(chunk.strip()) > 50]

def python_chunker(content):
    pattern = r"(?=^.*\b(@\w+)?\s*(class|def)\s+\w+\s*\(?.*\)?\s*:)"
    return [chunk.strip() for chunk in re.split(pattern, content, flags=re.MULTILINE) if len(chunk.strip()) > 40]

def fallback_chunker(content):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return splitter.split_text(content)

# Factory: Select chunker based on extension
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
