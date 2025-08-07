"""
Chunk analysis tools for debugging semantic chunking and anchor quality using actual core functionality.
"""

import os
import sys
import json
import streamlit as st
from typing import List, Dict, Any

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import log_highlight, log_to_sublog
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

def get_available_files(project_config):
    """Get list of files that were actually processed from git_tracking.json."""
    try:
        # Get the git tracking file path
        db_dir = project_config.get_db_dir()
        git_tracking_file = os.path.join(db_dir, "git_tracking.json")
        
        if not os.path.exists(git_tracking_file):
            log_to_sublog(project_config.project_dir, "debug_tools.log", 
                         f"Git tracking file not found: {git_tracking_file}")
            return []
        
        # Read the git tracking file to get processed files
        with open(git_tracking_file, 'r') as f:
            git_data = json.load(f)
        
        # Get the list of processed files (they are the keys, not in a "files" subobject)
        processed_files = list(git_data.keys())
        
        # Convert absolute paths to relative paths
        relative_files = []
        for abs_path in processed_files:
            try:
                rel_path = os.path.relpath(abs_path, project_config.project_dir)
                relative_files.append(rel_path)
            except ValueError:
                # If the file is not in the project directory, skip it
                continue
        
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Found {len(relative_files)} processed files from git_tracking.json")
        
        return sorted(relative_files)
        
    except Exception as e:
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Error getting processed files: {e}")
        return []

def analyze_chunks(project_config, retriever=None):
    """Analyze chunk quality and anchor distribution using the existing retriever from session state."""
    log_highlight("ChunkAnalyzer.analyze_chunks")
    
    st.subheader("🧩 Chunk Quality Analysis")
    
    try:
        # Use the retriever from session state (same as main app)
        if not retriever:
            retriever = st.session_state.get("retriever")
        
        if not retriever:
            st.error("❌ No retriever available - RAG system not ready")
            return
        
        # Get vectorstore from the retriever
        vectorstore = retriever.vectorstore
        if not vectorstore:
            st.error("❌ Could not access vectorstore from retriever")
            return
        
        # Get all documents from the vectorstore
        collection = vectorstore._collection
        results = collection.get()
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        st.write(f"**📊 Total chunks in database: {len(documents)}**")
        
        # Analyze chunk distribution by file
        file_distribution = {}
        for metadata in metadatas:
            if metadata and 'source' in metadata:
                source = metadata['source']
                file_distribution[source] = file_distribution.get(source, 0) + 1
        
        st.write(f"**📁 Files with chunks: {len(file_distribution)}**")
        
        # Show top files by chunk count
        top_files = sorted(file_distribution.items(), key=lambda x: x[1], reverse=True)[:10]
        st.write("**📈 Top files by chunk count:**")
        for file_path, count in top_files:
            st.write(f"  • {file_path}: {count} chunks")
        
        # Show processed files vs all project files
        processed_files = get_available_files(project_config)
        if processed_files:
            st.write(f"**📋 Actually processed files: {len(processed_files)}**")
            st.write("These are the files that were actually processed and indexed:")
            for file_path in processed_files[:10]:  # Show first 10
                st.write(f"  • {file_path}")
            if len(processed_files) > 10:
                st.write(f"  ... and {len(processed_files) - 10} more files")
        
        # Analyze anchor quality
        analyze_anchor_quality_from_metadata(metadatas)
        
    except Exception as e:
        st.error(f"❌ Error analyzing chunks: {e}")
        log_to_sublog(project_config.project_dir, "debug_tools.log", f"Error analyzing chunks: {e}")

def analyze_file_chunks(project_config, retriever=None, file_path=None):
    """Analyze chunks for a specific file using the existing retriever from session state."""
    log_highlight(f"ChunkAnalyzer.analyze_file_chunks for {file_path}")
    
    if not file_path:
        log_to_sublog(project_config.project_dir, "debug_tools.log", "No file path provided for chunk analysis")
        return []
    
    try:
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Starting chunk analysis for file: {file_path}")
        
        # Use the retriever from session state (same as main app)
        if not retriever:
            retriever = st.session_state.get("retriever")
        
        if not retriever:
            log_to_sublog(project_config.project_dir, "debug_tools.log", "No retriever available in session state")
            return []
        
        # Get vectorstore from the retriever
        vectorstore = retriever.vectorstore
        if not vectorstore:
            log_to_sublog(project_config.project_dir, "debug_tools.log", "Could not access vectorstore from retriever")
            return []
        
        # Get all documents from the vectorstore
        collection = vectorstore._collection
        results = collection.get()
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        # Filter chunks for the specific file
        file_chunks = []
        for i, metadata in enumerate(metadatas):
            if metadata and metadata.get('source') == file_path:
                chunk = {
                    "content": documents[i] if i < len(documents) else "",
                    "metadata": metadata,
                    "chunk_index": metadata.get('chunk_index', i),
                    "type": metadata.get('type', 'unknown'),
                    "start_line": metadata.get('start_line', 0),
                    "end_line": metadata.get('end_line', 0)
                }
                file_chunks.append(chunk)
        
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Found {len(file_chunks)} chunks for file: {file_path}")
        
        # Sort by chunk index
        file_chunks.sort(key=lambda x: x.get('chunk_index', 0))
        
        return file_chunks
        
    except Exception as e:
        log_to_sublog(project_config.project_dir, "debug_tools.log", 
                     f"Error analyzing file chunks for {file_path}: {e}")
        return []

def analyze_anchor_quality_from_metadata(metadatas):
    """Analyze anchor quality from metadata."""
    st.write("**🔍 Anchor Quality Analysis**")
    
    # Count chunks with different types of anchors
    anchor_counts = {
        "screen_name": 0,
        "class_names": 0,
        "function_names": 0,
        "component_name": 0,
        "no_anchors": 0
    }
    
    for metadata in metadatas:
        if metadata:
            has_anchors = False
            for anchor_type in ["screen_name", "class_names", "function_names", "component_name"]:
                if metadata.get(anchor_type):
                    anchor_counts[anchor_type] += 1
                    has_anchors = True
            
            if not has_anchors:
                anchor_counts["no_anchors"] += 1
    
    # Display anchor statistics
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Anchor Distribution:**")
        for anchor_type, count in anchor_counts.items():
            st.write(f"  • {anchor_type}: {count}")
    
    with col2:
        st.write("**Quality Metrics:**")
        total_chunks = len(metadatas)
        if total_chunks > 0:
            anchored_chunks = total_chunks - anchor_counts["no_anchors"]
            anchor_coverage = (anchored_chunks / total_chunks) * 100
            st.write(f"  • Anchor coverage: {anchor_coverage:.1f}%")
            st.write(f"  • Anchored chunks: {anchored_chunks}/{total_chunks}")

def analyze_chunk_distribution(hierarchy):
    """Analyze how chunks are distributed across files."""
    st.write("**📊 Chunk Distribution Analysis**")
    
    file_level = hierarchy.get("file_level", {})
    
    if not file_level:
        st.warning("No file-level data found")
        return
    
    chunk_counts = []
    file_types = {}
    
    for file_path, file_data in file_level.items():
        if isinstance(file_data, dict):
            chunk_count = file_data.get("chunk_count", 0)
            chunk_counts.append(chunk_count)
            
            # Categorize by file type
            ext = os.path.splitext(file_path)[1].lower()
            if ext not in file_types:
                file_types[ext] = {"files": 0, "total_chunks": 0}
            file_types[ext]["files"] += 1
            file_types[ext]["total_chunks"] += chunk_count
    
    if chunk_counts:
        avg_chunks = sum(chunk_counts) / len(chunk_counts)
        max_chunks = max(chunk_counts)
        min_chunks = min(chunk_counts)
        
        st.write(f"**Statistics:**")
        st.write(f"  • Average chunks per file: {avg_chunks:.1f}")
        st.write(f"  • Max chunks in a file: {max_chunks}")
        st.write(f"  • Min chunks in a file: {min_chunks}")
        st.write(f"  • Total files: {len(chunk_counts)}")
    
    if file_types:
        st.write(f"**Distribution by file type:**")
        for ext, info in file_types.items():
            st.write(f"  • {ext}: {info['files']} files, {info['total_chunks']} chunks")

def analyze_file_coverage(hierarchy, project_config):
    """Analyze file coverage and identify missing files."""
    st.write("**📁 File Coverage Analysis**")
    
    # Get all files in project
    all_files = set()
    extensions = project_config.get_extensions()
    
    for root, dirs, files in os.walk(project_config.project_dir):
        if 'codebase-qa' in dirs:
            dirs.remove('codebase-qa')
        
        for filename in files:
            if any(filename.endswith(ext) for ext in extensions):
                rel_path = os.path.relpath(os.path.join(root, filename), project_config.project_dir)
                all_files.add(rel_path)
    
    # Get files in hierarchy
    file_level = hierarchy.get("file_level", {})
    indexed_files = set(file_level.keys())
    
    # Calculate coverage
    covered_files = all_files.intersection(indexed_files)
    missing_files = all_files - indexed_files
    
    st.write(f"**Coverage Statistics:**")
    st.write(f"  • Total project files: {len(all_files)}")
    st.write(f"  • Indexed files: {len(indexed_files)}")
    st.write(f"  • Coverage: {(len(covered_files) / len(all_files) * 100):.1f}%")
    st.write(f"  • Missing files: {len(missing_files)}")
    
    if missing_files:
        st.write(f"**Missing files (first 10):**")
        for file_path in sorted(list(missing_files))[:10]:
            st.write(f"  • {file_path}")

def analyze_retrieval_patterns(retriever, project_config):
    """Analyze retrieval patterns and performance."""
    st.write("**🔍 Retrieval Pattern Analysis**")
    
    if not retriever:
        st.warning("No retriever available for analysis")
        return
    
    # Test queries to analyze retrieval patterns
    test_queries = [
        "MainActivity",
        "onCreate",
        "Fragment",
        "Button",
        "RecyclerView"
    ]
    
    st.write(f"**Testing retrieval with {len(test_queries)} queries:**")
    
    for query in test_queries:
        try:
            docs = retriever.get_relevant_documents(query, k=3)
            
            sources = [doc.metadata.get('source', 'Unknown') for doc in docs]
            unique_sources = len(set(sources))
            
            st.write(f"  • **{query}**: {len(docs)} results, {unique_sources} unique files")
            
        except Exception as e:
            st.write(f"  • **{query}**: Error - {e}")