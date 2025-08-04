import os
import sys
import streamlit as st
import json
from langchain.docstore.document import Document

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ProjectConfig
from logger import log_highlight, log_to_sublog

# Import debug tools
from .db_inspector import ChromaDBInspector, inspect_chroma_database, print_debug_report
from .query_runner import QueryRunner, run_debug_analysis, print_quick_analysis

class DebugTools:
    """Debug tools for RAG system inspection and diagnostics."""
    
    def __init__(self, project_config, ollama_model, ollama_endpoint, project_dir):
        self.project_config = project_config
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.project_dir = project_dir
        self.vector_db_dir = project_config.get_db_dir()
    
    def get_available_files(self):
        """Get list of files available for analysis from the project directory."""
        try:
            files = []
            extensions = self.project_config.get_extensions()
            
            for root, dirs, filenames in os.walk(self.project_dir):
                # Skip codebase-qa directory
                if 'codebase-qa' in dirs:
                    dirs.remove('codebase-qa')
                
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in extensions):
                        rel_path = os.path.relpath(os.path.join(root, filename), self.project_dir)
                        files.append(rel_path)
            
            return sorted(files)
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error getting available files: {e}")
            return []
    
    def inspect_vector_db(self):
        """Inspect vector database and return statistics."""
        try:
            from .vector_db_inspector import inspect_vector_db
            return inspect_vector_db(self.project_config, None)  # No retriever needed for inspection
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error inspecting vector DB: {e}")
            return {"error": str(e)}
    
    def clear_vector_db(self):
        """Clear the vector database."""
        try:
            import shutil
            if os.path.exists(self.vector_db_dir):
                shutil.rmtree(self.vector_db_dir)
                log_to_sublog(self.project_dir, "debug_tools.log", f"Cleared vector DB: {self.vector_db_dir}")
                return True
            return False
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error clearing vector DB: {e}")
            return False
    
    def analyze_file_chunks(self, file_path):
        """Analyze chunks for a specific file."""
        try:
            from .chunk_analyzer import analyze_chunks
            return analyze_chunks(self.project_config, None, file_path)
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error analyzing file chunks: {e}")
            return []
    
    def test_retrieval(self, query):
        """Test retrieval with a specific query."""
        try:
            from .retrieval_tester import test_retrieval_results
            qa_chain = st.session_state.get("qa_chain")
            return test_retrieval_results(query, None, self.project_config, qa_chain)
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error testing retrieval: {e}")
            return []
    
    def test_multiple_queries(self, queries):
        """Test multiple queries and return results."""
        try:
            results = {}
            for query in queries:
                results[query] = self.test_retrieval(query)
            return results
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error testing multiple queries: {e}")
            return {}
    
    def run_database_analysis(self, analysis_type="quick"):
        """Run database analysis using the new debug tools."""
        try:
            chroma_db_path = os.path.join(self.vector_db_dir, "chroma.sqlite3")
            if not os.path.exists(chroma_db_path):
                return {"error": f"Chroma database not found at {chroma_db_path}"}
            
            return run_debug_analysis(chroma_db_path, analysis_type)
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error running database analysis: {e}")
            return {"error": str(e)}
    
    def get_database_debug_report(self):
        """Get comprehensive database debug report."""
        try:
            chroma_db_path = os.path.join(self.vector_db_dir, "chroma.sqlite3")
            if not os.path.exists(chroma_db_path):
                return {"error": f"Chroma database not found at {chroma_db_path}"}
            
            return inspect_chroma_database(chroma_db_path)
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error getting database debug report: {e}")
            return {"error": str(e)}
    
    def run_custom_database_query(self, query):
        """Run a custom SQL query against the Chroma database."""
        try:
            chroma_db_path = os.path.join(self.vector_db_dir, "chroma.sqlite3")
            if not os.path.exists(chroma_db_path):
                return {"error": f"Chroma database not found at {chroma_db_path}"}
            
            runner = QueryRunner(chroma_db_path)
            if not runner.connect():
                return {"error": "Could not connect to database"}
            
            try:
                return runner.run_query(query, "Custom Query")
            finally:
                runner.disconnect()
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error running custom query: {e}")
            return {"error": str(e)}
    
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
# - Test files from debug_tools directory (test_debug_tools.py, test_vector_db_location.py, test_detection.py, test_git_tracking.py)
# - Local print/debug log helpers (now all logging via logger.py)
# - Redundant per-call anchor validation (now in upstream metadata extraction & chunk filtering)
# ADDED
# - DebugTools class: Complete implementation with render_debug_interface method.
# - get_available_files(): Returns list of files available for analysis from project directory.
# - inspect_vector_db(): Inspects vector database and returns statistics.
# - clear_vector_db(): Clears the vector database.
# - analyze_file_chunks(): Analyzes chunks for a specific file.
# - test_retrieval(): Tests retrieval with a specific query.
# - test_multiple_queries(): Tests multiple queries and returns results.
# - analyze_file_chunks(): New function in chunk_analyzer.py for file-specific chunk analysis.
# - test_retrieval_results(): New function in retrieval_tester.py that returns results instead of just displaying.
# - surface_anchorless_chunks: explicitly gathers all documents/chunks missing core semantic anchors for user/developer inspection.
# - Modular helpers for loading documents/hierarchy, previewing missing/weak chunks, and visualizing project structure.
# - Enhanced logging throughout with log_highlight and log_to_sublog for better debugging.
# - Retriever diagnostics with detailed type information logging.
# - Configuration debugging with comprehensive project settings display.
# - Only logger.py used for highlight/diagnostic logs.
# REFACTORED
# - DebugTools class now has all required methods for UI integration.
# - Fixed function signatures to match UI expectations.
# - Proper error handling and logging throughout all debug methods.
# - Clean separation between display functions and data return functions.
