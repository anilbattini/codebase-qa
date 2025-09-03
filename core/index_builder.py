# core/index_builder.py

import os
import time
import json
from typing import List, Dict
import streamlit as st

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.docstore.document import Document

from config.config import ProjectConfig
from config.model_config import model_config
from logger import setup_global_logger, log_highlight, log_to_sublog
from context.chunker_factory import get_chunker, summarize_chunk
from context.context_builder import ContextBuilder
from context.git_hash_tracker import FileHashTracker
from context.metadata_extractor import MetadataExtractor
from context.hierarchical_indexer import HierarchicalIndexer
from context.cross_reference_builder import CrossReferenceBuilder

def chunk_fingerprint(chunk: str) -> str:
    """Generate SHA-256 hash fingerprints for each chunk to eliminate duplicate embeddings."""
    import hashlib
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def update_logs(log_placeholder):
    """Update processing logs in the UI."""
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
                key=f"live_logs_{len(logs)}",
                label_visibility="collapsed"
            )

def sanitize_metadata(meta: dict) -> dict:
    """Handle all metadata types safely, especially complex Kotlin metadata."""
    sanitized = {}
    for k, v in meta.items():
        try:
            if v is None:
                continue
            elif isinstance(v, (str, int, float, bool)):
                sanitized[k] = v
            elif isinstance(v, list):
                if not v:
                    continue
                elif all(isinstance(item, (str, int, float)) for item in v):
                    sanitized[k] = ', '.join(str(item) for item in v)
                else:
                    try:
                        import json
                        sanitized[k] = json.dumps(v, default=str, ensure_ascii=False)
                    except (TypeError, ValueError):
                        sanitized[k] = f"complex_list_{len(v)}_items"
            elif isinstance(v, dict):
                try:
                    import json
                    sanitized[k] = json.dumps(v, default=str, ensure_ascii=False)
                except (TypeError, ValueError):
                    sanitized[k] = f"complex_dict_{len(v)}_keys"
            elif isinstance(v, set):
                sanitized[k] = ', '.join(str(item) for item in sorted(v))
            else:
                try:
                    sanitized[k] = str(v)
                except Exception:
                    sanitized[k] = f"unconvertible_{type(v).__name__}"
        except Exception as e:
            log_to_sublog(".", "build_rag.log", f"Failed to sanitize metadata field '{k}': {type(v)} - {e}")
            sanitized[k] = f"sanitization_error_{k}"
    
    if 'source' not in sanitized and 'source' in meta:
        sanitized['source'] = str(meta['source'])
    return sanitized

def build_code_relationship_map(documents: List[Document]) -> Dict[str, set]:
    """Build code relationship map from documents."""
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

class IndexBuilder:
    """Handles detailed RAG index building and processing."""
    
    def __init__(self, project_config: ProjectConfig, project_dir: str):
        self.project_config = project_config
        self.project_dir = project_dir

    def build_index(self, ollama_model, ollama_endpoint, log_placeholder, incremental=False, files_to_process=None):
        """Build the RAG index with enhanced processing and logging."""
        VECTOR_DB_DIR = self.project_config.get_db_dir()

        if not incremental:
            if os.path.exists(VECTOR_DB_DIR):
                try:
                    chroma_files = [
                        os.path.join(VECTOR_DB_DIR, "chroma.sqlite3"),
                        os.path.join(VECTOR_DB_DIR, "chroma.sqlite3-shm"),
                        os.path.join(VECTOR_DB_DIR, "chroma.sqlite3-wal")
                    ]
                    for file_path in chroma_files:
                        if os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                                log_to_sublog(self.project_dir, "build_rag.log", f"Removed existing database file: {file_path}")
                            except PermissionError:
                                time.sleep(0.5)
                                try:
                                    os.remove(file_path)
                                    log_to_sublog(self.project_dir, "build_rag.log", f"Removed locked database file: {file_path}")
                                except Exception as e:
                                    log_to_sublog(self.project_dir, "build_rag.log", f"Could not remove database file {file_path}: {e}")
                except Exception as e:
                    log_to_sublog(self.project_dir, "build_rag.log", f"Warning: Could not clean database directory: {e}")

        self.project_config.create_directories()
        logger = setup_global_logger(self.project_config.get_logs_dir())
        log_highlight("START build_rag", logger)

        METADATA_FILE = self.project_config.get_metadata_file()
        metadata_extractor = MetadataExtractor(self.project_config, self.project_dir)
        hierarchical_indexer = HierarchicalIndexer(self.project_config, VECTOR_DB_DIR)
        extensions = self.project_config.get_extensions()

        st.info(f"🎯 Detected project type: **{self.project_config.project_type.upper()}**")
        if incremental:
            st.info("🔄 **Incremental build mode** - processing only changed files")
        st.info(f"📁 Processing files with extensions: {', '.join(extensions)} of project {self.project_config.project_dir_name}")

        log_highlight("Initialized components", logger)
        hash_tracker = FileHashTracker(self.project_dir, self.project_config.get_db_dir())

        if incremental and files_to_process:
            log_to_sublog(self.project_dir, "build_rag.log", f"Incremental build: using provided {len(files_to_process)} files")
        else:
            files_to_process = hash_tracker.get_changed_files(extensions)
            log_to_sublog(self.project_dir, "build_rag.log", f"Full build: detected {len(files_to_process)} changed files")

        embedding_model = model_config.get_embedding_model()
        ollama_endpoint = model_config.get_ollama_endpoint()

        try:
            import requests
            response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
            if response.status_code == 200:
                available_models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in available_models]
                if embedding_model in model_names:
                    st.info(f"🚀 Using dedicated embedding model: {embedding_model}")
                    log_to_sublog(self.project_dir, "rag_manager.log", f"Using dedicated embedding model: {embedding_model}")
                else:
                    st.warning(f"⚠️ Dedicated embedding model '{embedding_model}' not found, using LLM model for embeddings (slower)")
                    log_to_sublog(self.project_dir, "rag_manager.log", f"Dedicated embedding model not found, using LLM model: {ollama_model}")
                    embedding_model = ollama_model
            else:
                st.warning(f"⚠️ Could not check available models, using LLM model for embeddings")
                embedding_model = ollama_model
        except Exception as e:
            st.warning(f"⚠️ Could not check available models, using LLM model for embeddings: {e}")
            log_to_sublog(self.project_dir, "rag_manager.log", f"Could not check models, using LLM model: {ollama_model}")
            embedding_model = ollama_model

        embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)
        tracking_status = hash_tracker.get_tracking_status()
        tracking_method = tracking_status['tracking_method']

        if not files_to_process:
            st.success("✅ All files already processed. Loading existing vector DB...")
            st.info(f"📊 Tracking method: **{tracking_method.upper()}**")
            if tracking_status.get('current_commit'):
                st.info(f"📊 Current commit: `{tracking_status['current_commit'][:8]}`")
            log_highlight("Existing vector DB loaded", logger)
            vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
            return vectorstore

        start_time = time.time()
        st.info(f"📂 Processing **{len(files_to_process)}** new/updated files... of project {self.project_config.project_dir_name}")
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

        anchor_required_fields = ["screen_name", "class_names", "function_names", "component_name"]
        st.session_state.thinking_logs.append(f"📄 Processing {len(files_to_process)} files...")
        update_logs(log_placeholder)
        logger.info(f"Starting processing of {len(files_to_process)} files")
        log_to_sublog(self.project_dir, "rag_manager.log", f"Starting processing of {len(files_to_process)} files")

        for file_index, path in enumerate(files_to_process):
            ext = os.path.splitext(path)[1]
            chunker = get_chunker(ext, self.project_config)
            st.session_state.thinking_logs.append(f"📄 Processing ({file_index + 1}/{len(files_to_process)}): {path}")
            update_logs(log_placeholder)
            logger.info(f"Processing file: {path}")
            log_to_sublog(self.project_dir, "rag_manager.log", f"Processing file ({file_index + 1}/{len(files_to_process)}): {path}")

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
                        continue

                    fingerprint = chunk_fingerprint(chunk)
                    if fingerprint in seen_fingerprints:
                        processing_stats["duplicates_skipped"] += 1
                        continue
                    seen_fingerprints.add(fingerprint)

                    normalized_path = self.project_config.normalize_path_for_storage(path)
                    enhanced_metadata = metadata_extractor.create_enhanced_metadata(chunk, normalized_path, i)

                    has_anchors = any(enhanced_metadata.get(field) for field in anchor_required_fields)
                    if not has_anchors:
                        processing_stats["anchorless_chunks"] += 1
                        log_to_sublog(self.project_dir, "chunking_metadata.log",
                                     f"Chunk without semantic anchors from {path}, idx {i}. Meta {dict(enhanced_metadata)}")

                    enhanced_metadata["has_semantic_anchors"] = has_anchors
                    enhanced_metadata.update({
                        "summary": summarize_chunk(chunk, path, self.project_config),
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
                log_to_sublog(self.project_dir, "rag_manager.log", f"Completed {path}: {file_chunk_count} chunks (total: {total_chunks})")

            except Exception as e:
                st.warning(f"⚠️ Failed to process {path}: {e}")
                st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
                processing_stats["errors"] += 1
                logger.exception(f"Error with {path}: {e}")
                log_to_sublog(self.project_dir, "rag_manager.log", f"Error processing {path}: {e}")
                update_logs(log_placeholder)

        if successfully_processed_files:
            hash_tracker.update_tracking_info(successfully_processed_files)
            st.session_state.thinking_logs.append("💾 Updated file tracking information")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "rag_manager.log", "Updated file tracking information")

        if documents:
            st.session_state.thinking_logs.append("🔗 Building cross-reference maps...")
            update_logs(log_placeholder)
            logger.info("Starting cross-reference building")
            log_to_sublog(self.project_dir, "rag_manager.log", "Building cross-reference maps...")
            try:
                cross_ref_builder = CrossReferenceBuilder(self.project_config, self.project_dir)
                cross_references = cross_ref_builder.build_cross_references(documents)
                cross_ref_builder.save_cross_references(cross_references)
                st.session_state.thinking_logs.append("✅ Cross-reference maps created successfully!")
                update_logs(log_placeholder)
                logger.info("Cross-reference building completed")
                log_to_sublog(self.project_dir, "rag_manager.log", "Cross-reference maps created successfully")
                stats = cross_references.get('statistics', {})
                log_to_sublog(self.project_dir, "rag_manager.log", f"Cross-reference stats: {stats}")
            except Exception as e:
                st.session_state.thinking_logs.append(f"⚠️ Warning: Cross-reference building failed: {e}")
                update_logs(log_placeholder)
                logger.warning(f"Cross-reference building failed: {e}")
                log_to_sublog(self.project_dir, "rag_manager.log", f"Warning: Cross-reference building failed: {e}")

        if documents:
            st.session_state.thinking_logs.append("🧠 Preparing enhanced context assembly...")
            update_logs(log_placeholder)
            logger.info("Initializing enhanced context assembly")
            log_to_sublog(self.project_dir, "rag_manager.log", "Preparing enhanced context assembly...")
            try:
                context_builder = ContextBuilder(self.project_config, self.project_dir)
                context_loaded = context_builder.load_context_data()
                if context_loaded:
                    st.session_state.thinking_logs.append("✅ Enhanced context assembly ready!")
                    update_logs(log_placeholder)
                    log_to_sublog(self.project_dir, "rag_manager.log", "Enhanced context assembly initialized successfully")
                else:
                    st.session_state.thinking_logs.append("⚠️ Enhanced context assembly initialization failed")
                    log_to_sublog(self.project_dir, "rag_manager.log", "Enhanced context assembly initialization failed")
            except Exception as e:
                st.session_state.thinking_logs.append(f"⚠️ Warning: Enhanced context assembly failed: {e}")
                update_logs(log_placeholder)
                logger.warning(f"Enhanced context assembly failed: {e}")
                log_to_sublog(self.project_dir, "rag_manager.log", f"Warning: Enhanced context assembly failed: {e}")

        if documents:
            st.session_state.thinking_logs.append("🔗 Building code relationships...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "rag_manager.log", "Building code relationships...")

            code_relationship_map = build_code_relationship_map(documents)
            normalized_relationship_map = {}
            for file_path, deps in code_relationship_map.items():
                normalized_file = self.project_config.normalize_path_for_storage(file_path)
                normalized_deps = [self.project_config.normalize_path_for_storage(dep) for dep in deps]
                normalized_relationship_map[normalized_file] = normalized_deps

            with open(METADATA_FILE, "w") as f:
                jsonable = {k: list(v) for k, v in normalized_relationship_map.items()}
                json.dump(jsonable, f, indent=2)

            st.session_state.thinking_logs.append("🏗️ Creating hierarchical indexes...")
            update_logs(log_placeholder)
            logger.info("Starting hierarchical index creation")
            log_to_sublog(self.project_dir, "rag_manager.log", "Creating hierarchical indexes...")

            try:
                hierarchy = hierarchical_indexer.create_hierarchical_index(documents)
                st.session_state.thinking_logs.append("✅ Hierarchical indexes created successfully!")
                update_logs(log_placeholder)
                logger.info("Hierarchical index creation completed")
                log_to_sublog(self.project_dir, "rag_manager.log", "Hierarchical indexes created successfully")
            except Exception as e:
                st.session_state.thinking_logs.append(f"⚠️ Warning: Hierarchical indexing failed: {e}")
                update_logs(log_placeholder)
                logger.warning(f"Hierarchical indexing failed: {e}")
                log_to_sublog(self.project_dir, "rag_manager.log", f"Warning: Hierarchical indexing failed: {e}")

        st.session_state.thinking_logs.append("🧹 Sanitizing documents for vector storage...")
        update_logs(log_placeholder)
        logger.info("Starting document sanitization")
        log_to_sublog(self.project_dir, "rag_manager.log", "Sanitizing documents for vector storage...")

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

            if (i + 1) % 10 == 0:
                st.session_state.thinking_logs.append(f"🧹 Sanitized {i + 1}/{len(documents)} documents...")
                update_logs(log_placeholder)
                log_to_sublog(self.project_dir, "rag_manager.log", f"Sanitized {i + 1}/{len(documents)} documents...")

        st.session_state.thinking_logs.append(f"✅ Sanitized {len(sanitized_docs)} documents")
        update_logs(log_placeholder)
        logger.info(f"Document sanitization completed: {len(sanitized_docs)} documents ready")
        log_to_sublog(self.project_dir, "rag_manager.log", f"Sanitized {len(sanitized_docs)} documents")

        st.session_state.thinking_logs.append("🔄 Creating vector database...")
        update_logs(log_placeholder)
        logger.info("Starting vector database creation")
        log_to_sublog(self.project_dir, "rag_manager.log", "Creating vector database...")

        try:
            start_time = time.time()
            timeout_minutes = 10
            batch_size = 10
            total_batches = (len(sanitized_docs) + batch_size - 1) // batch_size

            st.session_state.thinking_logs.append(f"📊 Processing {len(sanitized_docs)} documents in {total_batches} batches...")
            update_logs(log_placeholder)
            log_to_sublog(self.project_dir, "rag_manager.log", f"Processing {len(sanitized_docs)} documents in {total_batches} batches...")

            try:
                import requests
                response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
                if response.status_code != 200:
                    raise Exception(f"Ollama not responding: {response.status_code}")
                log_to_sublog(self.project_dir, "rag_manager.log", "Ollama is responsive, starting embedding computation...")
            except Exception as e:
                error_msg = f"Ollama not available at {ollama_endpoint}: {e}"
                st.error(f"❌ {error_msg}")
                log_to_sublog(self.project_dir, "rag_manager.log", error_msg)
                raise Exception(error_msg)

            if incremental and os.path.exists(os.path.join(self.project_config.get_db_dir(), "chroma.sqlite3")):
                log_to_sublog(self.project_dir, "build_rag.log", "Incremental build: Loading existing vector database")
                st.session_state.thinking_logs.append("🔄 Loading existing vector database for incremental update...")
                update_logs(log_placeholder)
                try:
                    existing_vectorstore = Chroma(
                        persist_directory=self.project_config.get_db_dir(),
                        embedding_function=embeddings
                    )
                    log_to_sublog(self.project_dir, "build_rag.log", f"Incremental build: Processing {len(sanitized_docs)} changed documents")
                    st.session_state.thinking_logs.append(f"🔄 Incremental update: Processing {len(sanitized_docs)} changed documents...")
                    update_logs(log_placeholder)
                    vectorstore = Chroma.from_documents(
                        documents=sanitized_docs,
                        embedding=embeddings,
                        persist_directory=self.project_config.get_db_dir()
                    )
                    log_to_sublog(self.project_dir, "build_rag.log", "Incremental build: Successfully updated vector database")
                    st.session_state.thinking_logs.append("✅ Incremental update completed successfully!")
                    update_logs(log_placeholder)
                except Exception as e:
                    log_to_sublog(self.project_dir, "build_rag.log", f"Incremental build failed, falling back to full rebuild: {e}")
                    st.session_state.thinking_logs.append(f"⚠️ Incremental update failed, doing full rebuild: {e}")
                    update_logs(log_placeholder)
                    vectorstore = Chroma.from_documents(
                        documents=sanitized_docs,
                        embedding=embeddings,
                        persist_directory=self.project_config.get_db_dir()
                    )
            else:
                log_to_sublog(self.project_dir, "build_rag.log", "Full build: Creating new vector database")
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        vectorstore = Chroma.from_documents(
                            documents=sanitized_docs,
                            embedding=embeddings,
                            persist_directory=self.project_config.get_db_dir()
                        )
                        break
                    except Exception as e:
                        if "readonly database" in str(e).lower() or "database is locked" in str(e).lower():
                            if attempt < max_retries - 1:
                                log_to_sublog(self.project_dir, "build_rag.log", f"Database locked, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                                st.session_state.thinking_logs.append(f"⚠️ Database locked, retrying... (attempt {attempt + 1}/{max_retries})")
                                update_logs(log_placeholder)
                                time.sleep(2)
                                continue
                            else:
                                log_to_sublog(self.project_dir, "build_rag.log", f"Failed to create database after {max_retries} attempts: {e}")
                                raise e
                        else:
                            raise e

            elapsed_time = time.time() - start_time
            if elapsed_time > (timeout_minutes * 60):
                error_msg = f"Embedding computation timed out after {timeout_minutes} minutes"
                st.error(f"❌ {error_msg}")
                log_to_sublog(self.project_dir, "rag_manager.log", error_msg)
                raise TimeoutError(error_msg)

            st.session_state.thinking_logs.append("💾 Vector database created and persisted!")
            update_logs(log_placeholder)
            logger.info("Vector database created and persisted to disk")
            log_to_sublog(self.project_dir, "rag_manager.log", "Vector database created and persisted!")

            st.session_state.thinking_logs.append("✅ Vector database created successfully!")
            update_logs(log_placeholder)
            logger.info("Vector database creation completed")
            log_to_sublog(self.project_dir, "rag_manager.log", f"Vector database created successfully! (took {elapsed_time:.1f}s)")

        except TimeoutError as e:
            st.error(f"❌ {e}")
            log_to_sublog(self.project_dir, "rag_manager.log", f"Embedding computation timeout: {e}")
            raise e
        except Exception as e:
            st.session_state.thinking_logs.append(f"❌ Error creating vector database: {e}")
            update_logs(log_placeholder)
            logger.error(f"Vector database creation failed: {e}")
            log_to_sublog(self.project_dir, "rag_manager.log", f"Error creating vector database: {e}")
            raise e

        processing_time = time.time() - start_time

        st.session_state.thinking_logs.append(
            f"📊 Processing complete: {processing_stats['chunks_created']} chunks from "
            f"{processing_stats['files_processed']} files in {processing_time:.2f}s"
        )
        log_to_sublog(self.project_dir, "rag_manager.log",
                      f"Processing complete: {processing_stats['chunks_created']} chunks from "
                      f"{processing_stats['files_processed']} files in {processing_time:.2f}s")

        if processing_stats["duplicates_skipped"] > 0:
            st.session_state.thinking_logs.append(
                f"🔍 Skipped {processing_stats['duplicates_skipped']} duplicate chunks"
            )
            log_to_sublog(self.project_dir, "rag_manager.log", f"Skipped {processing_stats['duplicates_skipped']} duplicate chunks")

        if processing_stats["anchorless_chunks"] > 0:
            st.session_state.thinking_logs.append(
                f"⚠️ Processed {processing_stats['anchorless_chunks']} chunks with missing semantic anchors – see chunking_metadata.log"
            )
            log_to_sublog(self.project_dir, "rag_manager.log", f"Processed {processing_stats['anchorless_chunks']} chunks with missing semantic anchors")

        if processing_stats["errors"] > 0:
            st.session_state.thinking_logs.append(
                f"⚠️ {processing_stats['errors']} files had processing errors"
            )
            log_to_sublog(self.project_dir, "rag_manager.log", f"{processing_stats['errors']} files had processing errors")

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
        return vectorstore
