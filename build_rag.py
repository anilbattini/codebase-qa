# build_rag.py

import re
import os
import time
import json
from typing import List, Dict
from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from chunker_factory import get_chunker, summarize_chunk
from git_hash_tracker import FileHashTracker
from config import ProjectConfig

VECTOR_DB_DIR = "vector_db"
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "code_relationships.json")

def chunk_fingerprint(chunk: str) -> str:
    import hashlib
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def update_logs(log_placeholder):
    import streamlit as st
    log_placeholder.write("\n".join(st.session_state.thinking_logs[-20:]))

def extract_dependencies(content: str, ext: str, project_config: ProjectConfig) -> List[str]:
    """Extract dependencies based on project configuration."""
    chunk_types = project_config.get_chunk_types()
    import_patterns = chunk_types.get("import", ["import ", "require("])

    dependencies = []
    for line in content.splitlines():
        line = line.strip()
        for pattern in import_patterns:
            if line.startswith(pattern):
                # Extract the actual dependency name
                if "import " in pattern:
                    parts = line.replace("import ", "").split()
                    if parts:
                        dependencies.append(parts[0])
                elif "require(" in pattern:
                    # Handle require('module') pattern
                    match = re.search(r'require\(["\']([^"\']+)["\']', line)
                    if match:
                        dependencies.append(match.group(1))
                break

    return dependencies

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
            deps = list(deps_meta)

        if file:
            code_relationship_map.setdefault(file, set()).update(deps)
    return code_relationship_map

def build_rag(project_dir, ollama_model, ollama_endpoint, log_placeholder, project_type=None):
    import streamlit as st

    # Initialize project configuration
    project_config = ProjectConfig(project_type) if project_type else ProjectConfig()
    extensions = project_config.get_extensions()

    st.info(f"🎯 Detected project type: {project_config.project_type.upper()}")
    st.info(f"📁 Processing extensions: {', '.join(extensions)}")

    # Initialize file hash tracker
    hash_tracker = FileHashTracker(project_dir, VECTOR_DB_DIR)

    # Get files that need processing
    files_to_process = hash_tracker.get_changed_files(extensions)
    embeddings = OllamaEmbeddings(model=ollama_model, base_url=ollama_endpoint)

    # Display tracking status
    tracking_status = hash_tracker.get_tracking_status()
    tracking_method = tracking_status['tracking_method']

    if not files_to_process:
        st.info("✅ All files already processed. Loading existing vector DB...")
        st.info(f"📊 Tracking method: {tracking_method.upper()}")
        if tracking_status.get('current_commit'):
            st.info(f"📊 Current commit: {tracking_status['current_commit'][:8]}")
        return Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings).as_retriever()

    start_time = time.time()
    st.info(f"📂 Processing {len(files_to_process)} new/updated files...")
    st.info(f"📊 Tracking method: {tracking_method.upper()}")

    if tracking_status.get('current_commit'):
        st.info(f"📊 Git commit: {tracking_status['current_commit'][:8]}")

    st.session_state.thinking_logs.append(
        f"🔍 Starting RAG for {len(files_to_process)} files using {tracking_method} tracking"
    )
    update_logs(log_placeholder)

    total_chunks, documents, seen_fingerprints = 0, [], set()
    successfully_processed_files = []

    for path in files_to_process:
        ext = os.path.splitext(path)[1]
        chunker = get_chunker(ext, project_config)
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

                summary = summarize_chunk(chunk, path, project_config)
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
                        "dependencies": ", ".join(extract_dependencies(chunk, ext, project_config)) if extract_dependencies(chunk, ext, project_config) else None,
                        "tracking_method": tracking_method,
                        "git_commit": tracking_status.get('current_commit'),
                        "project_type": project_config.project_type,
                        "language": project_config.project_type
                    }
                ))
                total_chunks += 1

            successfully_processed_files.append(path)
            st.session_state.thinking_logs.append(f"✅ {path}: {len(chunks)} chunks")
            update_logs(log_placeholder)

        except Exception as e:
            st.warning(f"Failed to process {path}: {e}")
            st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
            update_logs(log_placeholder)

    # Update tracking information for successfully processed files
    if successfully_processed_files:
        hash_tracker.update_tracking_info(successfully_processed_files)

    # Store relationships and update vector store
    if documents:
        code_relationship_map = build_code_relationship_map(documents)
        with open(METADATA_FILE, "w") as f:
            jsonable = {k: list(v) for k, v in code_relationship_map.items()}
            json.dump(jsonable, f, indent=2)

        vectorstore = Chroma.from_documents(documents, embedding=embeddings, persist_directory=VECTOR_DB_DIR)
    else:
        vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)

    st.session_state.thinking_logs.append(
        f"📦 Indexed {total_chunks} unique chunks from {len(files_to_process)} files in {time.time()-start_time:.2f}s"
    )
    update_logs(log_placeholder)
    st.success("✅ Vector DB updated")
    return vectorstore.as_retriever()

def get_impact(file_name: str, relationship_file: str = METADATA_FILE) -> List[str]:
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
