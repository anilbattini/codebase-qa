import os
import sys
import streamlit as st
import json
from langchain.docstore.document import Document

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

class DebugTools:
    """Debug tools for RAG system inspection and diagnostics."""
    
    def __init__(self, project_config, ollama_model, ollama_endpoint, project_dir):
        self.project_config = project_config
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.project_dir = project_dir
        self.vector_db_dir = project_config.get_db_dir()
    
    def render_debug_interface(self, retriever):
        """Render the comprehensive debug interface with all diagnostic tools."""
        log_highlight("DebugTools.render_debug_interface")
        
        st.header("🛠️ RAG Debug & Diagnostic Tools")
        st.write("Comprehensive debugging tools for analyzing RAG system performance and quality.")
        
        # Import the comprehensive tools
        from .vector_db_inspector import inspect_vector_db, analyze_hierarchical_index, check_retrieval_health
        from .chunk_analyzer import analyze_chunks
        from .retrieval_tester import test_retrieval
        
        # Debug tabs for organized interface
        tabs = st.tabs([
            "🗄️ Vector DB", 
            "🧩 Chunks", 
            "🔍 Retrieval", 
            "🧪 Testing", 
            "⚙️ Legacy Tools"
        ])
        
        with tabs[0]:  # Vector DB Inspector
            inspect_vector_db(self.project_config, retriever)
            analyze_hierarchical_index(self.project_config)
            if retriever:
                check_retrieval_health(self.project_config, retriever)
        
        with tabs[1]:  # Chunk Analysis
            analyze_chunks(self.project_config, retriever)
        
        with tabs[2]:  # Retrieval Analysis
            if retriever:
                st.subheader("🔍 Retriever Diagnostics")
                retriever_type = type(retriever).__name__
                st.info(f"Retriever type: {retriever_type}")
                log_to_sublog(self.project_dir, "debug_tools.log", f"Retriever type: {retriever_type}")
                
                if hasattr(retriever, 'vectorstore'):
                    vectorstore_type = type(retriever.vectorstore).__name__
                    st.info(f"Vector store: {vectorstore_type}")
                    log_to_sublog(self.project_dir, "debug_tools.log", f"Vector store: {vectorstore_type}")
            else:
                st.warning("⚠️ No retriever available for analysis")
        
        with tabs[3]:  # Interactive Testing
            qa_chain = st.session_state.get("qa_chain")
            test_retrieval(self.project_config, retriever, qa_chain)
        
        with tabs[4]:  # Legacy Tools
            st.subheader("⚙️ Configuration Debug")
            config_info = {
                "project_type": self.project_config.project_type,
                "extensions": self.project_config.get_extensions(),
                "ollama_model": self.ollama_model,
                "ollama_endpoint": self.ollama_endpoint,
                "database_path": self.project_config.get_db_dir(),
                "logs_path": self.project_config.get_logs_dir()
            }
            st.json(config_info)
            log_to_sublog(self.project_dir, "debug_tools.log", f"Configuration: {config_info}")
            
            # Show legacy debug interface
            show_debug_tools(self.project_dir, self.vector_db_dir)

def load_documents_from_vector_db(vector_db_dir):
    """
    Loads all Document metadata for inspection/debugging.
    Assumes Chroma/FAISS/etc. stores docs as .jsonl or .json file.
    """
    docfile = os.path.join(vector_db_dir, "chroma_docs.json")
    if os.path.isfile(docfile):
        with open(docfile, "r") as f:
            for line in f:
                yield json.loads(line)
    else:
        return []  # Handle alternate vector DBs or throw

def load_hierarchical_index(vector_db_dir):
    """Loads the project’s hierarchical_index.json if available."""
    index_file = os.path.join(vector_db_dir, "hierarchical_index.json")
    if not os.path.isfile(index_file):
        return {}
    with open(index_file, "r") as f:
        return json.load(f)

def surface_anchorless_chunks(vector_db_dir, required_anchors=None):
    """Returns a list of chunks/documents missing all required anchors."""
    if required_anchors is None:
        required_anchors = ["screen_name", "class_names", "function_names", "component_name"]
    docs = list(load_documents_from_vector_db(vector_db_dir))
    anchorless = []
    for d in docs:
        meta = d.get("metadata", d)  # map to same interface
        if not any(meta.get(anchor) for anchor in required_anchors):
            anchorless.append({
                "source": meta.get("source", "unknown"),
                "chunk_index": meta.get("chunk_index", "?"),
                "summary": meta.get("summary", "")[:80],
                "anchors": {k: meta.get(k) for k in required_anchors}
            })
    return anchorless

def show_debug_tools(project_dir, vector_db_dir):
    """Entry point: Display main debug tools panel."""
    log_highlight("debug_tools.show_debug_tools")
    st.header("🛠️ RAG Debug & Diagnostic Tools")
    st.write("These tools help you debug weak or generic chunks, orphan files, anchor gaps, and overall project metadata quality.")

    # 1. Orphan/Anchorless chunks
    st.subheader("🔎 Chunks missing semantic anchors")
    anchorless = surface_anchorless_chunks(vector_db_dir)
    st.write(f"{len(anchorless)} chunks with missing/weak anchors (screen/class/function/component):")
    for chunk in anchorless[:20]:  # Only show a sample for brevity
        st.code(f"{chunk['source']} [idx {chunk['chunk_index']}]: {chunk['summary']} | anchors: {chunk['anchors']}")

    if len(anchorless) > 20:
        st.info(f"...{len(anchorless)-20} more chunks omitted for brevity.")

    # 2. Hierarchy index inspection
    st.subheader("📂 Hierarchical Index Inspection")
    hierarchy = load_hierarchical_index(vector_db_dir)
    if hierarchy:
        st.write("File level (top 5):")
        fl = hierarchy.get("file_level", {})
        for i, (fname, meta) in enumerate(list(fl.items())[:5]):
            st.markdown(f"- **{fname}**: {meta.get('chunk_count', 0)} chunks, {meta.get('file_type', 'unknown')}")
        st.write("Missing anchors at index build (first 5):")
        missing = fl.get("missing", [])
        for x in missing[:5]:
            st.code(x)
    else:
        st.warning("No hierarchy index found; try rebuilding the vector DB.")

    # 3. Quick project structure summary
    st.subheader("🗂️ Project Structure Overview")
    files_by_type = {}
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            files_by_type.setdefault(ext, 0)
            files_by_type[ext] += 1
    for ext, count in sorted(files_by_type.items(), key=lambda x: -x[1]):
        st.write(f"{ext or '[no ext]'}: {count} files")

    st.success("RAG debugging complete.")

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - Local print/debug log helpers (now all logging via logger.py)
# - Redundant per-call anchor validation (now in upstream metadata extraction & chunk filtering)
# ADDED
# - DebugTools class: Complete implementation with render_debug_interface method.
# - surface_anchorless_chunks: explicitly gathers all documents/chunks missing core semantic anchors for user/developer inspection.
# - Modular helpers for loading documents/hierarchy, previewing missing/weak chunks, and visualizing project structure.
# - Enhanced logging throughout with log_highlight and log_to_sublog for better debugging.
# - Retriever diagnostics with detailed type information logging.
# - Configuration debugging with comprehensive project settings display.
# - Only logger.py used for highlight/diagnostic logs.
