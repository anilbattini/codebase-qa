# rag_logic.py

import os
import time
import hashlib
from typing import List, Dict
from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from chunker_factory import get_chunker, summarize_chunk

EXTENSIONS = (".kt", ".kts", ".gradle", ".gitignore", ".properties", ".xml")
VECTOR_DB_DIR = "vector_db"
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "code_relationships.json")

def chunk_fingerprint(chunk: str) -> str:
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def update_logs(log_placeholder):
    import streamlit as st
    log_placeholder.write("\n".join(st.session_state.thinking_logs[-20:]))

def get_files_to_process(project_dir: str, extensions: tuple) -> List[str]:
    from pathspec import PathSpec
    ignore_path = os.path.join(project_dir, ".gitignore")
    ignore_spec = None
    if os.path.exists(ignore_path):
        with open(ignore_path) as f:
            ignore_spec = PathSpec.from_lines("gitwildmatch", f.readlines())
    valid_files = []
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith(extensions):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_dir)
                if ignore_spec and ignore_spec.match_file(rel_path):
                    continue
                valid_files.append(full_path)
    return valid_files

def detect_chunk_type(chunk: str) -> str:
    # Simple heuristic: look for class, def, fun, etc.
    lower = chunk.strip().lower()
    if lower.startswith('class '): return "class"
    if lower.startswith('fun ') or lower.startswith('def '): return "function"
    if lower.startswith('import '): return "import"
    return "other"

def extract_dependencies(content: str, ext: str) -> List[str]:
    if ext in [".kt", ".kts"]:
        return [line.split()[1] for line in content.splitlines() if line.strip().startswith("import")]
    return []

def build_code_relationship_map(documents: List[Document]) -> Dict[str, set]:
    code_relationship_map = {}
    for doc in documents:
        file = doc.metadata.get("source")
        deps_meta = doc.metadata.get("dependencies")
        
        if deps_meta is None:
            deps = []
        elif isinstance(deps_meta, str):
            deps = [d.strip() for d in deps_meta.split(",") if d.strip()]
        else:
            deps = list(deps_meta)  # fallback, shouldn't happen anymore

        if file:
            code_relationship_map.setdefault(file, set()).update(deps)
    return code_relationship_map

def build_rag(project_dir, ollama_model, ollama_endpoint, log_placeholder):
    import streamlit as st
    files_to_process = get_files_to_process(project_dir, EXTENSIONS)
    embeddings = OllamaEmbeddings(model=ollama_model, base_url=ollama_endpoint)

    if not files_to_process:
        st.info("✅ All files already processed. Loading existing vector DB...")
        # Also load relationships map for impact analysis, if present
        return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings).as_retriever()

    start_time = time.time()
    st.info(f"📂 Processing {len(files_to_process)} new/updated files...")
    st.session_state.thinking_logs.append(f"🔍 Starting RAG for {len(files_to_process)} files...")
    update_logs(log_placeholder)

    total_chunks, documents, seen_fingerprints = 0, [], set()

    for path in files_to_process:
        ext = os.path.splitext(path)[1]
        chunker = get_chunker(ext)
        st.session_state.thinking_logs.append(f"📄 Processing: {path}")
        update_logs(log_placeholder)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            chunks = chunker(content)
            for i, chunk_data in enumerate(chunks):
                chunk = chunk_data["content"]
                fingerprint = chunk_fingerprint(chunk)
                if fingerprint in seen_fingerprints:
                    continue
                seen_fingerprints.add(fingerprint)

                summary = summarize_chunk(chunk, path)
                chunk_type = chunk_data.get("type", "other")
                chunk_name = chunk_data.get("name")

                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": path,
                        "chunk_index": i,
                        "summary": summary,
                        "fingerprint": fingerprint,
                        "type": chunk_type,
                        "name": chunk_name,
                        "dependencies": ", ".join(extract_dependencies(chunk, ext)) if ext in [".kt", ".kts", ".java"] else None,
                    }
                ))

            st.session_state.thinking_logs.append(f"✅ {path}: {len(chunks)} chunks")
            update_logs(log_placeholder)
        except Exception as e:
            st.warning(f"Failed to process {path}: {e}")
            st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
            update_logs(log_placeholder)

    # Store relationships for impact analysis
    code_relationship_map = build_code_relationship_map(documents)
    with open(METADATA_FILE, "w") as f:
        # Convert sets to lists for JSON serialization
        jsonable = {k: list(v) for k, v in code_relationship_map.items()}
        import json
        json.dump(jsonable, f, indent=2)

    vectorstore = Chroma.from_documents(documents, embedding=embeddings, persist_directory=VECTOR_DB_DIR)
    st.session_state.thinking_logs.append(
        f"📦 Indexed {total_chunks} unique chunks from {len(files_to_process)} files in {time.time()-start_time:.2f}s"
    )
    update_logs(log_placeholder)
    st.success("✅ Vector DB updated")
    return vectorstore.as_retriever()

def get_impact(file_name: str, relationship_file: str = METADATA_FILE) -> List[str]:
    # Returns list of files impacted if file_name changes
    import json
    if not os.path.exists(relationship_file):
        return []
    with open(relationship_file) as f:
        code_map = json.load(f)
    impacted = set()
    todo = {file_name}
    while todo:
        f = todo.pop()
        for dependant, deps in code_map.items():
            if f in deps and dependant not in impacted:
                impacted.add(dependant)
                todo.add(dependant)
    return list(impacted)
