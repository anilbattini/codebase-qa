# build_rag.py (Enhanced Version)

import os
import re
import time
import json
from typing import List, Dict
from langchain.docstore.document import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings

from chunker_factory import get_chunker, summarize_chunk
from git_hash_tracker import FileHashTracker
from config import ProjectConfig
from metadata_extractor import MetadataExtractor
from hierarchical_indexer import HierarchicalIndexer

VECTOR_DB_DIR = "vector_db"
METADATA_FILE = os.path.join(VECTOR_DB_DIR, "code_relationships.json")

def chunk_fingerprint(chunk: str) -> str:
    """Create a unique fingerprint for chunk deduplication."""
    import hashlib
    return hashlib.sha256(chunk.encode("utf-8")).hexdigest()

def update_logs(log_placeholder):
    """Update the processing logs display with proper formatting."""
    import streamlit as st
    
    logs = st.session_state.get('thinking_logs', [])
    
    if logs:
        # Display only recent logs to keep it manageable
        recent_logs = logs[-20:]  # Last 20 logs
        
        # Create formatted log text with timestamps
        formatted_logs = []
        for i, log in enumerate(recent_logs):
            formatted_logs.append(f"[{i+1:02d}] {log}")
        
        log_text = "\n".join(formatted_logs)
        
        # Update the placeholder with scrollable text area
        with log_placeholder.container():
            st.text_area(
                "Live Processing Status",
                value=log_text,
                height=200,
                disabled=True,
                key=f"live_logs_{len(logs)}",  # Unique key to force refresh
                label_visibility="collapsed"
            )


def extract_dependencies(content: str, ext: str, project_config: ProjectConfig) -> List[str]:
    """Enhanced dependency extraction based on project configuration."""
    chunk_types = project_config.get_chunk_types()
    import_patterns = chunk_types.get("import", ["import ", "require("])
    
    dependencies = []
    
    for line in content.splitlines():
        line = line.strip()
        for pattern in import_patterns:
            if line.startswith(pattern):
                # Extract the actual dependency name
                if "import " in pattern:
                    # Handle various import formats
                    if " from " in line:
                        # from module import something
                        match = re.search(r'from\s+([^\s]+)', line)
                        if match:
                            dependencies.append(match.group(1))
                    else:
                        # import module
                        parts = line.replace("import ", "").split()
                        if parts:
                            dependencies.append(parts.split('.'))  # Take base module
                
                elif "require(" in pattern:
                    # Handle require('module') pattern
                    match = re.search(r'require$$["\']([^"\']+)["\']', line)
                    if match:
                        dependencies.append(match.group(1))
                break
    
    return list(set(dependencies))  # Remove duplicates

def build_code_relationship_map(documents: List[Document]) -> Dict[str, set]:
    """Build enhanced code relationship mapping."""
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
    """Enhanced RAG building with improved metadata and indexing."""
    import streamlit as st
    
    # Initialize enhanced components
    project_config = ProjectConfig(project_type) if project_type else ProjectConfig()
    metadata_extractor = MetadataExtractor(project_config)
    hierarchical_indexer = HierarchicalIndexer(project_config, VECTOR_DB_DIR)
    
    extensions = project_config.get_extensions()
    
    st.info(f"🎯 Detected project type: **{project_config.project_type.upper()}**")
    st.info(f"📁 Processing extensions: {', '.join(extensions)}")
    
    # Initialize file hash tracker
    hash_tracker = FileHashTracker(project_dir, VECTOR_DB_DIR)
    
    # Get files that need processing
    files_to_process = hash_tracker.get_changed_files(extensions)
    
    # Initialize embeddings
    embeddings = OllamaEmbeddings(model=ollama_model, base_url=ollama_endpoint)
    
    # Display tracking status
    tracking_status = hash_tracker.get_tracking_status()
    tracking_method = tracking_status['tracking_method']
    
    if not files_to_process:
        st.success("✅ All files already processed. Loading existing vector DB...")
        st.info(f"📊 Tracking method: **{tracking_method.upper()}**")
        if tracking_status.get('current_commit'):
            st.info(f"📊 Current commit: `{tracking_status['current_commit'][:8]}`")
        
        # Load existing hierarchical index
        vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
        return vectorstore.as_retriever()
    
    # Start processing
    start_time = time.time()
    st.info(f"📂 Processing **{len(files_to_process)}** new/updated files...")
    st.info(f"📊 Tracking method: **{tracking_method.upper()}**")
    if tracking_status.get('current_commit'):
        st.info(f"📊 Git commit: `{tracking_status['current_commit'][:8]}`")
    
    st.session_state.thinking_logs.append(
        f"🔍 Starting enhanced RAG for {len(files_to_process)} files using {tracking_method} tracking"
    )
    update_logs(log_placeholder)
    
    # Processing variables
    total_chunks, documents, seen_fingerprints = 0, [], set()
    successfully_processed_files = []
    processing_stats = {
        "files_processed": 0,
        "chunks_created": 0,
        "duplicates_skipped": 0,
        "errors": 0
    }
    
    # Process each file
    for file_index, path in enumerate(files_to_process):
        ext = os.path.splitext(path)[1]
        chunker = get_chunker(ext, project_config)
        
        st.session_state.thinking_logs.append(
            f"📄 Processing ({file_index + 1}/{len(files_to_process)}): {path}"
        )
        update_logs(log_placeholder)
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            # Create chunks with enhanced chunker
            chunks = chunker(content)
            file_chunk_count = 0
            
            for i, chunk_data in enumerate(chunks):
                chunk = chunk_data["content"]
                fingerprint = chunk_fingerprint(chunk)
                
                # Skip duplicates
                if fingerprint in seen_fingerprints:
                    processing_stats["duplicates_skipped"] += 1
                    continue
                
                seen_fingerprints.add(fingerprint)
                
                # Create enhanced metadata
                enhanced_metadata = metadata_extractor.create_enhanced_metadata(chunk, path, i)
                
                # Add original metadata
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
                
                # Create document
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
            
        except Exception as e:
            st.warning(f"⚠️ Failed to process {path}: {e}")
            st.session_state.thinking_logs.append(f"❌ Error with {path}: {e}")
            processing_stats["errors"] += 1
            update_logs(log_placeholder)
    
    # Update tracking information
    if successfully_processed_files:
        hash_tracker.update_tracking_info(successfully_processed_files)
        st.session_state.thinking_logs.append("💾 Updated file tracking information")
        update_logs(log_placeholder)
    
    # Build relationships and hierarchical indexes
    if documents:
        st.session_state.thinking_logs.append("🔗 Building code relationships...")
        update_logs(log_placeholder)
        
        # Build traditional relationship map
        code_relationship_map = build_code_relationship_map(documents)
        with open(METADATA_FILE, "w") as f:
            jsonable = {k: list(v) for k, v in code_relationship_map.items()}
            json.dump(jsonable, f, indent=2)
        
        # Build hierarchical index
        st.session_state.thinking_logs.append("🏗️ Creating hierarchical indexes...")
        update_logs(log_placeholder)
        
        hierarchy = hierarchical_indexer.create_hierarchical_index(documents)
        
        # Create/update vector store
        st.session_state.thinking_logs.append("🗄️ Storing vectors in database...")
        update_logs(log_placeholder)
        
        vectorstore = Chroma.from_documents(
            documents, 
            embedding=embeddings, 
            persist_directory=VECTOR_DB_DIR
        )
    else:
        # Load existing vector store
        vectorstore = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embeddings)
    
    # Final statistics
    processing_time = time.time() - start_time
    st.session_state.thinking_logs.append(
        f"📊 Processing complete: {processing_stats['chunks_created']} chunks from "
        f"{processing_stats['files_processed']} files in {processing_time:.2f}s"
    )
    
    if processing_stats["duplicates_skipped"] > 0:
        st.session_state.thinking_logs.append(
            f"🔍 Skipped {processing_stats['duplicates_skipped']} duplicate chunks"
        )
    
    if processing_stats["errors"] > 0:
        st.session_state.thinking_logs.append(
            f"⚠️ {processing_stats['errors']} files had processing errors"
        )
    
    update_logs(log_placeholder)
    
    # Display success message with stats
    st.success("✅ Enhanced vector database created successfully!")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Files Processed", processing_stats["files_processed"])
    with col2:
        st.metric("Chunks Created", processing_stats["chunks_created"])
    with col3:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    
    return vectorstore.as_retriever()

def get_impact(file_name: str, relationship_file: str = METADATA_FILE) -> List[str]:
    """Enhanced impact analysis with hierarchical index support."""
    if not os.path.exists(relationship_file):
        return []
    
    try:
        with open(relationship_file) as f:
            code_map = json.load(f)
        
        impacted = set()
        todo = {file_name}
        
        # BFS to find all impacted files
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
