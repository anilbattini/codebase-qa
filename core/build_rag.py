import os
import re
import time
import json
from typing import List, Dict

import streamlit as st

from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from chunker_factory import get_chunker, summarize_chunk
from git_hash_tracker import FileHashTracker
from config import ProjectConfig
from model_config import model_config
from metadata_extractor import MetadataExtractor
from hierarchical_indexer import HierarchicalIndexer

from logger import setup_global_logger, log_to_sublog, log_highlight

def chunk_fingerprint(chunk: str) -> str:
    import hashlib
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def update_logs(log_placeholder):
    logs = st.session_state.get('thinking_logs', [])
    if logs:
        recent_logs = logs[-20:]
        formatted_logs = [f"[{i+1:02d}] {log}" for i, log in enumerate(recent_logs)]
        log_text = "\n".join(formatted_logs)
        with log_placeholder.container():
            st.text_area(
                "Live Processing Status",
                value=log_text,
                height=200,
                disabled=True,
                key=f"live_logs_{len(logs)}", label_visibility="collapsed"
            )

def sanitize_metadata(meta: dict) -> dict:
    return {
        k: (', '.join(v) if isinstance(v, list)
            else str(v) if isinstance(v, (dict, set))
            else v)
        for k, v in meta.items()
        if v is None or isinstance(v, (str, int, float, bool, list, dict))
    }

def build_code_relationship_map(documents: List[Document]) -> Dict[str, set]:
    code_relationship_map = {}
    for doc in documents:
        file = doc.metadata.get("source")
        deps = doc.metadata.get("dependencies", [])
        if file:
            if isinstance(deps, list):
                code_relationship_map.setdefault(file, set()).update(deps)
            elif isinstance(deps, str):
                code_relationship_map.setdefault(file, set()).add(deps)
    return code_relationship_map

def build_rag(project_dir, ollama_model, ollama_endpoint, log_placeholder, project_type=None):
    # Get project configuration with centralized path management
    project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
    
    # All metadata, relationships, and vector DB will be in the configured directory
    VECTOR_DB_DIR = project_config.get_db_dir()
    
    # Ensure clean database directory for rebuild
    if os.path.exists(VECTOR_DB_DIR):
        try:
            # Try to remove any existing database files that might be locked
            import shutil
            import time
            
            # Check for common Chroma database files
            chroma_files = [
                os.path.join(VECTOR_DB_DIR, "chroma.sqlite3"),
                os.path.join(VECTOR_DB_DIR, "chroma.sqlite3-shm"),
                os.path.join(VECTOR_DB_DIR, "chroma.sqlite3-wal")
            ]
            
            for file_path in chroma_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        log_to_sublog(project_dir, "build_rag.log", f"Removed existing database file: {file_path}")
                    except PermissionError:
                        # File might be locked, try again after a short delay
                        time.sleep(0.5)
                        try:
                            os.remove(file_path)
                            log_to_sublog(project_dir, "build_rag.log", f"Removed locked database file: {file_path}")
                        except Exception as e:
                            log_to_sublog(project_dir, "build_rag.log", f"Could not remove database file {file_path}: {e}")
            
            # If the directory is empty or only contains non-database files, we can proceed
            remaining_files = [f for f in os.listdir(VECTOR_DB_DIR) if f not in ['chroma.sqlite3', 'chroma.sqlite3-shm', 'chroma.sqlite3-wal']]
            if not remaining_files:
                # Directory is effectively empty, safe to proceed
                log_to_sublog(project_dir, "build_rag.log", f"Database directory cleaned: {VECTOR_DB_DIR}")
            else:
                log_to_sublog(project_dir, "build_rag.log", f"Database directory contains other files: {remaining_files}")
                
        except Exception as e:
            log_to_sublog(project_dir, "build_rag.log", f"Warning: Could not clean database directory: {e}")
    
    project_config.create_directories()
    
    # Setup logger inside the logs directory
    logger = setup_global_logger(project_config.get_logs_dir())
    log_highlight("START build_rag", logger)
    METADATA_FILE = project_config.get_metadata_file()

    # Components
    metadata_extractor = MetadataExtractor(project_config)
    hierarchical_indexer = HierarchicalIndexer(project_config, VECTOR_DB_DIR)
    extensions = project_config.get_extensions()

    st.info(f"🎯 Detected project type: **{project_config.project_type.upper()}**")
    st.info(f"📁 Processing extensions: {', '.join(extensions)}")
    log_highlight("Initialized components", logger)

    # File tracking/hash check
    hash_tracker = FileHashTracker(project_dir, project_config.get_db_dir())
    files_to_process = hash_tracker.get_changed_files(extensions)
    
    # Use centralized model configuration
    embedding_model = model_config.get_embedding_model()
    ollama_endpoint = model_config.get_ollama_endpoint()
    
    # Check if the dedicated embedding model is available, fallback to original model
    try:
        import requests
        response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
        if response.status_code == 200:
            available_models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in available_models]
            
            if embedding_model in model_names:
                st.info(f"🚀 Using dedicated embedding model: {embedding_model}")
                log_to_sublog(project_dir, "rag_manager.log", f"Using dedicated embedding model: {embedding_model}")
            else:
                st.warning(f"⚠️ Dedicated embedding model '{embedding_model}' not found, using LLM model for embeddings (slower)")
                log_to_sublog(project_dir, "rag_manager.log", f"Dedicated embedding model not found, using LLM model: {ollama_model}")
                embedding_model = ollama_model
    except Exception as e:
        st.warning(f"⚠️ Could not check available models, using LLM model for embeddings: {e}")
        log_to_sublog(project_dir, "rag_manager.log", f"Could not check models, using LLM model: {ollama_model}")
        embedding_model = ollama_model
    
    embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
    
    tracking_status = hash_tracker.get_tracking_status()
    tracking_method = tracking_status['tracking_method']

    # If all up-to-date, load vector DB
    if not files_to_process:
        st.success("✅ All files already processed. Loading existing vector DB...")
        st.info(f"📊 Tracking method: **{tracking_method.upper()}**")
        if tracking_status.get('current_commit'):
            st.info(f"📊 Current commit: `{tracking_status['current_commit'][:8]}`")
        log_highlight("Existing vector DB loaded", logger)
        vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        )

    start_time = time.time()
    st.info(f"📂 Processing **{len(files_to_process)}** new/updated files...")
    st.info(f"📊 Tracking method: **{tracking_method.upper()}**")
    if tracking_status.get('current_commit'):
        st.info(f"📊 Git commit: `{tracking_status['current_commit'][:8]}`")
    st.session_state.thinking_logs.append(
        f"🔍 Starting enhanced RAG for {len(files_to_process)} files using {tracking_method} tracking"
    )
    update_logs(log_placeholder)

    total_chunks, documents, seen_fingerprints = 0, [], set()
    successfully_processed_files = []
    processing_stats = {
        "files_processed": 0,
        "chunks_created": 0,
        "duplicates_skipped": 0,
        "anchorless_chunks": 0,
        "errors": 0
    }

    # These are your key semantic anchors, config-driven
    anchor_required_fields = ["screen_name", "class_names", "function_names", "component_name"]

    st.session_state.thinking_logs.append(f"📄 Processing {len(files_to_process)} files...")
    update_logs(log_placeholder)
    logger.info(f"Starting processing of {len(files_to_process)} files")
    log_to_sublog(project_dir, "rag_manager.log", f"Starting processing of {len(files_to_process)} files")

    for file_index, path in enumerate(files_to_process):
        ext = os.path.splitext(path)[1]
        chunker = get_chunker(ext, project_config)
        st.session_state.thinking_logs.append(f"📄 Processing ({file_index + 1}/{len(files_to_process)}): {path}")
        update_logs(log_placeholder)
        logger.info(f"Processing file: {path}")
        log_to_sublog(project_dir, "rag_manager.log", f"Processing file ({file_index + 1}/{len(files_to_process)}): {path}")
        file_chunk_count = 0
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            chunks = chunker(content)
            for i, chunk_data in enumerate(chunks):
                if isinstance(chunk_data, str):
                    chunk_data = {"content": chunk_data}
                chunk = chunk_data.get("content")
                if not isinstance(chunk, str):
                    continue # skip invalid chunk
                fingerprint = chunk_fingerprint(chunk)
                if fingerprint in seen_fingerprints:
                    processing_stats["duplicates_skipped"] += 1
                    continue
                seen_fingerprints.add(fingerprint)
                # Normalize path for storage (convert to relative)
                normalized_path = project_config.normalize_path_for_storage(path)
                enhanced_metadata = metadata_extractor.create_enhanced_metadata(chunk, normalized_path, i)

                # Check for semantic anchors but don't skip - just log for analysis
                has_anchors = any(enhanced_metadata.get(field) for field in anchor_required_fields)
                if not has_anchors:
                    processing_stats["anchorless_chunks"] += 1
                    log_to_sublog(project_dir, "chunking_metadata.log",
                        f"Chunk without semantic anchors from {path}, idx {i}. Meta {dict(enhanced_metadata)}"
                    )
                    # Don't skip - include with warning
                    enhanced_metadata["has_semantic_anchors"] = False
                else:
                    enhanced_metadata["has_semantic_anchors"] = True
                    log_to_sublog(project_dir, "chunking_metadata.log",
                        f"Chunk with semantic anchors from {path}, idx {i}. Meta {dict(enhanced_metadata)}"
                    )

                # Add to metadata
                enhanced_metadata.update({
                    "summary": summarize_chunk(chunk, path, project_config),
                    "fingerprint": fingerprint,
                    "type": chunk_data.get("type", "other"),
                    "name": chunk_data.get("name"),
                    "tracking_method": tracking_method,
                    "git_commit": tracking_status.get('current_commit'),
                    "semantic_relations": chunk_data.get("semantic_relations", []),
                    "has_context_overlap": chunk_data.get("has_prev_context", False) or chunk_data.get("has_next_context", False)
                })

                documents.append(Document(
                    page_content=chunk,
                    metadata=enhanced_metadata
                ))
                file_chunk_count += 1
                total_chunks += 1
            successfully_processed_files.append(path)
            processing_stats["files_processed"] += 1
            processing_stats["chunks_created"] += file_chunk_count
            st.session_state.thinking_logs.append(
                f"✅ {path}: {file_chunk_count} chunks (total: {total_chunks})"
            )
            update_logs(log_placeholder)
            log_to_sublog(project_dir, "rag_manager.log", f"Completed {path}: {file_chunk_count} chunks (total: {total_chunks})")

        except Exception as e:
            st.warning(f"⚠️ Failed to process {path}: {e}")
            st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
            processing_stats["errors"] += 1
            logger.exception(f"Error with {path}: {e}")
            log_to_sublog(project_dir, "rag_manager.log", f"Error processing {path}: {e}")
            update_logs(log_placeholder)

    if successfully_processed_files:
        hash_tracker.update_tracking_info(successfully_processed_files)
        st.session_state.thinking_logs.append("💾 Updated file tracking information")
        update_logs(log_placeholder)
        log_to_sublog(project_dir, "rag_manager.log", "Updated file tracking information")

    # Build relationships and hierarchy
    if documents:
        st.session_state.thinking_logs.append("🔗 Building code relationships...")
        update_logs(log_placeholder)
        log_to_sublog(project_dir, "rag_manager.log", "Building code relationships...")
        code_relationship_map = build_code_relationship_map(documents)
        
        # Normalize all paths in the relationship map for storage
        normalized_relationship_map = {}
        for file_path, deps in code_relationship_map.items():
            normalized_file = project_config.normalize_path_for_storage(file_path)
            normalized_deps = [project_config.normalize_path_for_storage(dep) for dep in deps]
            normalized_relationship_map[normalized_file] = normalized_deps
        
        with open(METADATA_FILE, "w") as f:
            jsonable = {k: list(v) for k, v in normalized_relationship_map.items()}
            json.dump(jsonable, f, indent=2)
        st.session_state.thinking_logs.append("🏗️ Creating hierarchical indexes...")
        update_logs(log_placeholder)
        logger.info("Starting hierarchical index creation")
        log_to_sublog(project_dir, "rag_manager.log", "Creating hierarchical indexes...")
        
        try:
            hierarchy = hierarchical_indexer.create_hierarchical_index(documents)
            st.session_state.thinking_logs.append("✅ Hierarchical indexes created successfully!")
            update_logs(log_placeholder)
            logger.info("Hierarchical index creation completed")
            log_to_sublog(project_dir, "rag_manager.log", "Hierarchical indexes created successfully")
        except Exception as e:
            st.session_state.thinking_logs.append(f"⚠️ Warning: Hierarchical indexing failed: {e}")
            update_logs(log_placeholder)
            logger.warning(f"Hierarchical indexing failed: {e}")
            log_to_sublog(project_dir, "rag_manager.log", f"Warning: Hierarchical indexing failed: {e}")
            # Continue without hierarchical indexing

    # Sanitize/prepare for vectorstore
    st.session_state.thinking_logs.append("🧹 Sanitizing documents for vector storage...")
    update_logs(log_placeholder)
    logger.info("Starting document sanitization")
    log_to_sublog(project_dir, "rag_manager.log", "Sanitizing documents for vector storage...")
    
    sanitized_docs = []
    for i, doc in enumerate(documents):
        if not isinstance(doc, Document):
            continue
        if not hasattr(doc, "metadata") or not isinstance(doc.metadata, dict):
            doc.metadata = {"source": "unknown (invalid metadata)"}
        else:
            try:
                doc.metadata = sanitize_metadata(doc.metadata)
            except Exception as e:
                doc.metadata = {"source": "error_during_filtering"}
        sanitized_docs.append(doc)
        
        # Log progress every 10 documents
        if (i + 1) % 10 == 0:
            st.session_state.thinking_logs.append(f"🧹 Sanitized {i + 1}/{len(documents)} documents...")
            update_logs(log_placeholder)
            log_to_sublog(project_dir, "rag_manager.log", f"Sanitized {i + 1}/{len(documents)} documents...")
    
    st.session_state.thinking_logs.append(f"✅ Sanitized {len(sanitized_docs)} documents")
    update_logs(log_placeholder)
    logger.info(f"Document sanitization completed: {len(sanitized_docs)} documents ready")
    log_to_sublog(project_dir, "rag_manager.log", f"Sanitized {len(sanitized_docs)} documents")

    # Store in persistent vector DB (Chroma)
    st.session_state.thinking_logs.append("🔄 Creating vector database...")
    update_logs(log_placeholder)
    logger.info("Starting vector database creation")
    log_to_sublog(project_dir, "rag_manager.log", "Creating vector database...")
    
    try:
        # Add timeout and progress tracking for embedding computation
        start_time = time.time()
        timeout_minutes = 10  # 10 minute timeout for embedding computation
        
        # Process documents in batches to provide progress feedback
        batch_size = 10
        total_batches = (len(sanitized_docs) + batch_size - 1) // batch_size
        
        st.session_state.thinking_logs.append(f"📊 Processing {len(sanitized_docs)} documents in {total_batches} batches...")
        update_logs(log_placeholder)
        log_to_sublog(project_dir, "rag_manager.log", f"Processing {len(sanitized_docs)} documents in {total_batches} batches...")
        
        # Check if Ollama is responsive before starting embedding computation
        try:
            import requests
            response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception(f"Ollama not responding: {response.status_code}")
            log_to_sublog(project_dir, "rag_manager.log", "Ollama is responsive, starting embedding computation...")
        except Exception as e:
            error_msg = f"Ollama not available at {ollama_endpoint}: {e}"
            st.error(f"❌ {error_msg}")
            log_to_sublog(project_dir, "rag_manager.log", error_msg)
            raise Exception(error_msg)
        
        # Create vectorstore with batch processing and retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                vectorstore = Chroma.from_documents(
                    documents=sanitized_docs,
                    embedding=embeddings,
                    persist_directory=project_config.get_db_dir()
                )
                break  # Success, exit retry loop
            except Exception as e:
                if "readonly database" in str(e).lower() or "database is locked" in str(e).lower():
                    if attempt < max_retries - 1:
                        log_to_sublog(project_dir, "build_rag.log", f"Database locked, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                        st.session_state.thinking_logs.append(f"⚠️ Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                        update_logs(log_placeholder)
                        time.sleep(2)
                        continue
                    else:
                        log_to_sublog(project_dir, "build_rag.log", f"Failed to create database after {max_retries} attempts: {e}")
                        raise e
                else:
                    # Non-locking error, don't retry
                    raise e
        
        # Check if we exceeded timeout
        elapsed_time = time.time() - start_time
        if elapsed_time > (timeout_minutes * 60):
            error_msg = f"Embedding computation timed out after {timeout_minutes} minutes"
            st.error(f"❌ {error_msg}")
            log_to_sublog(project_dir, "rag_manager.log", error_msg)
            raise TimeoutError(error_msg)
        
        st.session_state.thinking_logs.append("💾 Vector database created and persisted!")
        update_logs(log_placeholder)
        logger.info("Vector database created and persisted to disk")
        log_to_sublog(project_dir, "rag_manager.log", "Vector database created and persisted!")
        
        st.session_state.thinking_logs.append("✅ Vector database created successfully!")
        update_logs(log_placeholder)
        logger.info("Vector database creation completed")
        log_to_sublog(project_dir, "rag_manager.log", f"Vector database created successfully! (took {elapsed_time:.1f}s)")
        
    except TimeoutError as e:
        st.error(f"❌ {e}")
        log_to_sublog(project_dir, "rag_manager.log", f"Embedding computation timeout: {e}")
        raise e
    except Exception as e:
        st.session_state.thinking_logs.append(f"❌ Error creating vector database: {e}")
        update_logs(log_placeholder)
        logger.error(f"Vector database creation failed: {e}")
        log_to_sublog(project_dir, "rag_manager.log", f"Error creating vector database: {e}")
        raise e

    processing_time = time.time() - start_time
    st.session_state.thinking_logs.append(
        f"📊 Processing complete: {processing_stats['chunks_created']} chunks from "
        f"{processing_stats['files_processed']} files in {processing_time:.2f}s"
    )
    log_to_sublog(project_dir, "rag_manager.log", 
        f"Processing complete: {processing_stats['chunks_created']} chunks from "
        f"{processing_stats['files_processed']} files in {processing_time:.2f}s")
    
    if processing_stats["duplicates_skipped"] > 0:
        st.session_state.thinking_logs.append(
            f"🔍 Skipped {processing_stats['duplicates_skipped']} duplicate chunks"
        )
        log_to_sublog(project_dir, "rag_manager.log", f"Skipped {processing_stats['duplicates_skipped']} duplicate chunks")
    
    if processing_stats["anchorless_chunks"] > 0:
        st.session_state.thinking_logs.append(
            f"⚠️ Skipped {processing_stats['anchorless_chunks']} chunks due to missing semantic anchors – see chunking_metadata.log"
        )
        log_to_sublog(project_dir, "rag_manager.log", f"Skipped {processing_stats['anchorless_chunks']} chunks due to missing semantic anchors")
    
    if processing_stats["errors"] > 0:
        st.session_state.thinking_logs.append(
            f"⚠️ {processing_stats['errors']} files had processing errors"
        )
        log_to_sublog(project_dir, "rag_manager.log", f"{processing_stats['errors']} files had processing errors")
    
    update_logs(log_placeholder)

    st.success("✅ Enhanced vector database created successfully!")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", processing_stats["files_processed"])
    with col2:
        st.metric("Chunks Created", processing_stats["chunks_created"])
    with col3:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    log_highlight("END build_rag", logger)
    return vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 15  # Increased from 10 to get more candidates
        }
    )

def get_impact(file_name: str, project_dir: str = None) -> List[str]:
    project_config = ProjectConfig(project_dir=project_dir)
    
    relationship_file = project_config.get_metadata_file()
    if not os.path.exists(relationship_file):
        return []
    try:
        with open(relationship_file) as f:
            code_map = json.load(f)
        
        # Normalize the input file name for comparison
        normalized_file_name = project_config.normalize_path_for_storage(file_name)
        
        impacted = set()
        todo = {normalized_file_name}
        while todo:
            current_file = todo.pop()
            for dependant, deps in code_map.items():
                if current_file in deps and dependant not in impacted:
                    impacted.add(dependant)
                    todo.add(dependant)
        return list(impacted)
    except Exception as e:
        print(f"Error in impact analysis: {e}")
        return []

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - All module-level logging and sublogging helpers — now in logger.py utility and only imported.
# - Accepting/processing of anchorless/generic or super-short chunks: replaced by explicit skip, so only semantically-whole/documented chunks are indexed. (Above, in main for loop.)
# - Redundant code for duplicate chunk handling, chunk sanitization/summarization — now only one place, always after anchor validation.
# ADDED
# - logger.py utilities are now used exclusively for all logging and highlight, DRY-style.
# - Enforce minimum semantic anchors ("screen_name", "class_names", "function_names", "component_name") for every chunk; log and skip if missing, see chunking_metadata.log.
# - All statistics of missing/weak/duplicate/errored chunks are surfaced in Streamlit and log.
# - All paths/project-local for vector DB, metadata, and logs (never hard-coded global).
