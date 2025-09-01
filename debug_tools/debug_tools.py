import os
import sys
import streamlit as st
import json
import time
import requests
from langchain.docstore.document import Document
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma

# Add parent directory to path to import from codebase-qa root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import ProjectConfig
from config.model_config import model_config
from logger import log_highlight, log_to_sublog
from rag_manager import RagManager

class DebugTools:
    """Debug tools for RAG system inspection and diagnostics using actual core functionality."""
    
    def __init__(self, project_config, ollama_model, ollama_endpoint, project_dir):
        self.project_config = project_config
        self.ollama_model = ollama_model
        self.ollama_endpoint = ollama_endpoint
        self.project_dir = project_dir
        self.vector_db_dir = project_config.get_db_dir()
        
        # Use the latest embedding model configuration
        self.embedding_model = self._get_optimal_embedding_model()
        
        log_to_sublog(self.project_dir, "debug_tools.log", 
                     f"DebugTools initialized with embedding_model={self.embedding_model}")
    
    def _get_optimal_embedding_model(self):
        """Get the optimal embedding model from centralized configuration."""
        try:
            # Use centralized model configuration
            embedding_model = model_config.get_embedding_model()
            log_to_sublog(self.project_dir, "debug_tools.log", 
                        f"Using centralized embedding model: {embedding_model}")
            return embedding_model
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                        f"Error getting embedding model from config, using LLM model: {self.ollama_model}, error: {e}")
            return self.ollama_model
    

    
    def _get_retriever(self):
        """Get the retriever from session state - use the same one as the main app."""
        log_to_sublog(self.project_dir, "debug_tools.log", 
                     f"=== GETTING RETRIEVER FROM SESSION STATE ===")
        
        try:
            # Check if session state exists
            if not hasattr(st, 'session_state'):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ No session_state available")
                return None
            
            # Check what's in session state
            session_keys = list(st.session_state.keys())
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Session state keys: {session_keys}")
            
            # Get retriever
            retriever = st.session_state.get("retriever")
            
            if retriever is None:
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ No retriever found in session state")
                return None
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"✅ Retriever found: {type(retriever)}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Retriever id: {id(retriever)}")
            
            return retriever
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"❌ Error getting retriever from session state: {e}")
            import traceback
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Traceback: {traceback.format_exc()}")
            return None
    
    def get_available_files(self):
        """Get list of files available for analysis from git_tracking.json."""
        try:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== GETTING AVAILABLE FILES ===")
            
            # Get the git tracking file path
            git_tracking_file = os.path.join(self.vector_db_dir, "git_tracking.json")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Git tracking file path: {git_tracking_file}")
            
            if not os.path.exists(git_tracking_file):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ Git tracking file not found: {git_tracking_file}")
                return []
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"✅ Git tracking file found")
            
            # Read the git tracking file to get processed files
            with open(git_tracking_file, 'r') as f:
                git_data = json.load(f)
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Git data keys: {list(git_data.keys())[:5]}... (showing first 5)")
            
            # Get the list of processed files (they are the keys, not in a "files" subobject)
            processed_files = list(git_data.keys())
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Total processed files: {len(processed_files)}")
            
            # Convert absolute paths to relative paths
            relative_files = []
            for abs_path in processed_files:
                try:
                    rel_path = os.path.relpath(abs_path, self.project_dir)
                    relative_files.append(rel_path)
                except ValueError:
                    # If the file is not in the project directory, skip it
                    continue
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"✅ Found {len(relative_files)} processed files for analysis")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"First 5 files: {relative_files[:5]}")
            return sorted(relative_files)
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== GETTING AVAILABLE FILES FAILED ===")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Error type: {type(e)}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Error message: {str(e)}")
            import traceback
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Traceback: {traceback.format_exc()}")
            return []
    
    def inspect_vector_db(self):
        """Inspect vector database and return statistics using actual core methods."""
        try:
            log_to_sublog(self.project_dir, "debug_tools.log", "=== VECTOR DB INSPECTION STARTED ===")
            
            # Use the retriever from session state to get the vectorstore
            retriever = self._get_retriever()
            if not retriever:
                log_to_sublog(self.project_dir, "debug_tools.log", "❌ No retriever available for vector DB inspection")
                return {"error": "No retriever available - RAG system not ready"}
            
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Retriever found for vector DB inspection: {type(retriever)}")
            
            vectorstore = retriever.vectorstore
            if not vectorstore:
                log_to_sublog(self.project_dir, "debug_tools.log", "❌ Could not load vectorstore from retriever")
                return {"error": "Could not load vectorstore from retriever"}
            
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Vectorstore found: {type(vectorstore)}")
            
            # Get collection info
            collection = vectorstore._collection
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Collection found: {type(collection)}")
            
            try:
                count = collection.count()
                log_to_sublog(self.project_dir, "debug_tools.log", f"Collection count: {count}")
            except Exception as e:
                log_to_sublog(self.project_dir, "debug_tools.log", f"❌ Error getting collection count: {e}")
                return {"error": f"Error getting collection count: {e}"}
            
            # Get all documents
            try:
                results = collection.get()
                documents = results.get('documents', [])
                metadatas = results.get('metadatas', [])
                log_to_sublog(self.project_dir, "debug_tools.log", f"Retrieved {len(documents)} documents, {len(metadatas)} metadatas")
            except Exception as e:
                log_to_sublog(self.project_dir, "debug_tools.log", f"❌ Error getting documents from collection: {e}")
                return {"error": f"Error getting documents from collection: {e}"}
            
            # Analyze file distribution
            file_distribution = {}
            for metadata in metadatas:
                if metadata and 'source' in metadata:
                    source = metadata['source']
                    file_distribution[source] = file_distribution.get(source, 0) + 1
            
            # Get database size
            db_size = 0
            if os.path.exists(self.vector_db_dir):
                for root, dirs, files in os.walk(self.vector_db_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        db_size += os.path.getsize(file_path)
            
            result = {
                "total_documents": count,
                "unique_files": len(file_distribution),
                "file_distribution": file_distribution,
                "database_size_mb": db_size / (1024 * 1024),
                "embedding_model": self.embedding_model,
                "database_path": self.vector_db_dir
            }
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== VECTOR DB INSPECTION COMPLETED: {count} documents, {len(file_distribution)} files ===")
            return result
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"=== VECTOR DB INSPECTION FAILED ===")
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error type: {type(e)}")
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error message: {str(e)}")
            import traceback
            log_to_sublog(self.project_dir, "debug_tools.log", f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def clear_vector_db(self):
        """Clear the vector database."""
        try:
            import shutil
            if os.path.exists(self.vector_db_dir):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Clearing vector DB: {self.vector_db_dir}")
                shutil.rmtree(self.vector_db_dir)
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Successfully cleared vector DB: {self.vector_db_dir}")
                return True
            else:
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Vector DB directory does not exist: {self.vector_db_dir}")
                return False
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error clearing vector DB: {e}")
            return False
    
    def analyze_file_chunks(self, file_path):
        """Analyze chunks for a specific file using actual vector database."""
        try:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== FILE CHUNK ANALYSIS STARTED ===")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"File path: {file_path}")
            
            # Use the retriever from session state to get the vectorstore
            retriever = self._get_retriever()
            if not retriever:
                log_to_sublog(self.project_dir, "debug_tools.log", "❌ No retriever available in session state")
                return []
            
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Retriever found for file analysis: {type(retriever)}")
            
            vectorstore = retriever.vectorstore
            if not vectorstore:
                log_to_sublog(self.project_dir, "debug_tools.log", "❌ Could not load vectorstore from retriever")
                return []
            
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Vectorstore found for file analysis: {type(vectorstore)}")
            
            # Get all documents from the vectorstore
            collection = vectorstore._collection
            log_to_sublog(self.project_dir, "debug_tools.log", f"✅ Collection found for file analysis: {type(collection)}")
            
            try:
                results = collection.get()
                documents = results.get('documents', [])
                metadatas = results.get('metadatas', [])
                log_to_sublog(self.project_dir, "debug_tools.log", f"Retrieved {len(documents)} documents, {len(metadatas)} metadatas")
            except Exception as e:
                log_to_sublog(self.project_dir, "debug_tools.log", f"❌ Error getting documents from collection: {e}")
                return []
            
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
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Found {len(file_chunks)} chunks for file: {file_path}")
            
            # Sort by chunk index
            file_chunks.sort(key=lambda x: x.get('chunk_index', 0))
            
            return file_chunks
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Error analyzing file chunks for {file_path}: {e}")
            return []
    
    def test_retrieval(self, query):
        """Test retrieval with a specific query using the existing retriever from session state."""
        try:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== RETRIEVAL TEST STARTED ===")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Query: {query}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"DebugTools instance: {self}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Project dir: {self.project_dir}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Vector DB dir: {self.vector_db_dir}")
            
            # Use the retriever from session state (same as main app)
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Getting retriever from session state...")
            retriever = self._get_retriever()
            
            if not retriever:
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ No retriever available in session state")
                return {"error": "No retriever available - RAG system not ready"}
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"✅ Retriever found: {type(retriever)}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Retriever attributes: {dir(retriever)}")
            
            # Check if retriever has vectorstore attribute
            if hasattr(retriever, 'vectorstore'):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"✅ Retriever has vectorstore: {type(retriever.vectorstore)}")
                vectorstore = retriever.vectorstore
                
                if hasattr(vectorstore, '_collection'):
                    collection = vectorstore._collection
                    log_to_sublog(self.project_dir, "debug_tools.log", 
                                 f"✅ Vectorstore has collection: {type(collection)}")
                    
                    # Check collection info
                    try:
                        count = collection.count()
                        log_to_sublog(self.project_dir, "debug_tools.log", 
                                     f"Collection count: {count}")
                    except Exception as e:
                        log_to_sublog(self.project_dir, "debug_tools.log", 
                                     f"❌ Error getting collection count: {e}")
            else:
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ Retriever has no vectorstore attribute")
            
            # Use the actual retriever to get documents
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Calling retriever.get_relevant_documents(query='{query}', k=5)...")
            docs = retriever.get_relevant_documents(query, k=5)
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Retrieved {len(docs)} documents")
            
            if not docs:
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"❌ No documents retrieved")
                return {"error": "No documents retrieved"}
            
            # Process results
            results = []
            for i, doc in enumerate(docs, 1):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Processing document {i}: {type(doc)}")
                
                # Safely get metadata
                metadata = getattr(doc, 'metadata', {})
                if not isinstance(metadata, dict):
                    metadata = {}
                
                result = {
                    "rank": i,
                    "source": metadata.get("source", "Unknown") if isinstance(metadata, dict) else "Unknown",
                    "content": getattr(doc, 'page_content', '')[:200] + "..." if len(getattr(doc, 'page_content', '')) > 200 else getattr(doc, 'page_content', ''),
                    "metadata": metadata,
                    "relevance_score": metadata.get('score', 'N/A') if isinstance(metadata, dict) else 'N/A'
                }
                results.append(result)
                
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Result {i}: {result['source']} (score: {result['relevance_score']})")
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== RETRIEVAL TEST COMPLETED SUCCESSFULLY: {len(results)} results ===")
            return results
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"=== RETRIEVAL TEST FAILED ===")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Error type: {type(e)}")
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Error message: {str(e)}")
            import traceback
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def test_multiple_queries(self, queries):
        """Test multiple queries and return results."""
        try:
            results = {}
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Testing multiple queries: {len(queries)} queries")
            
            for i, query in enumerate(queries, 1):
                log_to_sublog(self.project_dir, "debug_tools.log", 
                             f"Testing query {i}/{len(queries)}: {query}")
                results[query] = self.test_retrieval(query)
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Multiple query testing completed: {len(results)} results")
            return results
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error testing multiple queries: {e}")
            return {}
    

    
    def get_database_debug_report(self):
        """Get comprehensive database debug report using actual core methods."""
        try:
            log_to_sublog(self.project_dir, "debug_tools.log", "Generating database debug report")
            
            # Get vector DB inspection
            vector_db_info = self.inspect_vector_db()
            
            # Get hierarchical index info
            hierarchy_file = self.project_config.get_hierarchy_file()
            hierarchy_info = {}
            if os.path.exists(hierarchy_file):
                with open(hierarchy_file, 'r') as f:
                    hierarchy = json.load(f)
                    hierarchy_info = {
                        "file_count": len(hierarchy.get("file_level", {})),
                        "total_chunks": sum(file_data.get("chunk_count", 0) for file_data in hierarchy.get("file_level", {}).values()),
                        "hierarchy_file_size": os.path.getsize(hierarchy_file)
                    }
            
            # Get git tracking info
            git_tracking_file = os.path.join(self.vector_db_dir, "git_tracking.json")
            git_info = {}
            if os.path.exists(git_tracking_file):
                with open(git_tracking_file, 'r') as f:
                    git_data = json.load(f)
                    git_info = {
                        "tracked_files": len(git_data.get("files", {})),
                        "last_commit": git_data.get("last_commit", "unknown")
                    }
            
            report = {
                "vector_db": vector_db_info,
                "hierarchy": hierarchy_info,
                "git_tracking": git_info,
                "embedding_model": self.embedding_model,
                "database_path": self.vector_db_dir
            }
            
            log_to_sublog(self.project_dir, "debug_tools.log", 
                         f"Database debug report generated successfully")
            return report
            
        except Exception as e:
            log_to_sublog(self.project_dir, "debug_tools.log", f"Error getting database debug report: {e}")
            return {"error": str(e)}
    
    def render_debug_interface(self, retriever):
        """Render the comprehensive debug interface with all diagnostic tools."""
        log_highlight("DebugTools.render_debug_interface")
        
        st.header("🛠️ RAG Debug & Diagnostic Tools")
        st.write("Comprehensive debugging tools for analyzing RAG system performance and quality.")
        
        # Debug tabs for organized interface
        tabs = st.tabs([
            "🗄️ Vector DB", 
            "🧩 Chunks", 
            "🔍 Retrieval", 
            "🧪 Testing", 
            "⚙️ Configuration"
        ])
        
        with tabs[0]:  # Vector DB Inspector
            st.subheader("🗄️ Vector Database Inspector")
            if st.button("🔍 Inspect Vector DB", type="primary"):
                with st.spinner("Inspecting vector database..."):
                    try:
                        stats = self.inspect_vector_db()
                        if "error" not in stats:
                            st.success("✅ Vector DB inspection complete!")
                            
                            # Display statistics
                            st.subheader("📈 Database Statistics")
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Total Documents", stats.get("total_documents", 0))
                            with col_b:
                                st.metric("Unique Files", stats.get("unique_files", 0))
                            with col_c:
                                st.metric("Database Size", f"{stats.get('database_size_mb', 0):.2f} MB")
                            
                            # Display file breakdown
                            if "file_distribution" in stats:
                                st.subheader("📁 File Distribution")
                                file_data = []
                                for file_path, count in stats["file_distribution"].items():
                                    file_data.append({"File": file_path, "Chunks": count})
                                
                                if file_data:
                                    import pandas as pd
                                    df = pd.DataFrame(file_data)
                                    st.dataframe(df, use_container_width=True)
                        else:
                            st.error(f"❌ Error inspecting vector DB: {stats.get('error')}")
                            
                    except Exception as e:
                        st.error(f"❌ Error inspecting vector DB: {e}")
            
            if st.button("🗑️ Clear Vector DB"):
                if st.checkbox("I understand this will delete all vector data"):
                    with st.spinner("Clearing vector database..."):
                        try:
                            if self.clear_vector_db():
                                st.success("✅ Vector database cleared!")
                                st.rerun()
                            else:
                                st.error("❌ Error clearing vector DB")
                        except Exception as e:
                            st.error(f"❌ Error clearing vector DB: {e}")
        
        with tabs[1]:  # Chunk Analysis
            st.subheader("🧩 Chunk Analyzer")
            
            # File selector
            files = self.get_available_files()
            if files:
                selected_file = st.selectbox("Select file to analyze:", files)
                
                if selected_file and st.button("🔍 Analyze Chunks", type="primary"):
                    with st.spinner("Analyzing chunks..."):
                        try:
                            chunks = self.analyze_file_chunks(selected_file)
                            
                            st.subheader(f"📄 Chunks for: {selected_file}")
                            st.write(f"Found {len(chunks)} chunks")
                            
                            # Display chunks
                            for i, chunk in enumerate(chunks):
                                with st.expander(f"Chunk {i+1}: {chunk.get('type', 'unknown')} (lines {chunk.get('start_line', 0)}-{chunk.get('end_line', 0)})"):
                                    st.write("**Content:**")
                                    st.code(chunk.get('content', '')[:500] + "..." if len(chunk.get('content', '')) > 500 else chunk.get('content', ''))
                                    
                                    st.write("**Metadata:**")
                                    st.json(chunk.get('metadata', {}))
                        except Exception as e:
                            st.error(f"❌ Error analyzing chunks: {e}")
            else:
                st.warning("No files available for analysis")
        
        with tabs[2]:  # Retrieval Analysis
            st.subheader("🔍 Retrieval Analysis")
            
            # Custom query testing
            test_query = st.text_input("Enter test query:", placeholder="e.g., MainActivity onCreate method")
            k_docs = st.number_input("Documents to retrieve:", min_value=1, max_value=20, value=5)
            
            if test_query and st.button("🔍 Test Retrieval", type="primary"):
                with st.spinner("Testing retrieval..."):
                    try:
                        results = self.test_retrieval(test_query)
                        if "error" not in results:
                            st.success(f"✅ Retrieved {len(results)} documents")
                            
                            for i, result in enumerate(results):
                                with st.expander(f"Result {i+1}: {result['source']}"):
                                    st.write("**Content:**")
                                    st.write(result['content'])
                                    st.write("**Score:**", result['relevance_score'])
                                    st.write("**Metadata:**")
                                    st.json(result['metadata'])
                        else:
                            st.error(f"❌ Retrieval failed: {results.get('error')}")
                    except Exception as e:
                        st.error(f"❌ Error testing retrieval: {e}")
        
        with tabs[3]:  # Interactive Testing
            st.subheader("🧪 Interactive Testing")
            
            # Test embedding compatibility
            st.write("**Embedding Compatibility Test**")
            if st.button("Test Embedding Compatibility"):
                with st.spinner("Testing embedding compatibility..."):
                    result = self.test_embedding_compatibility()
                    if result["status"] == "success":
                        st.success(f"✅ Embedding test successful!")
                        st.info(f"Model: {result['embedding_model']}")
                        st.info(f"Dimension: {result['embedding_dimension']}")
                    else:
                        st.error(f"❌ Embedding test failed: {result.get('error', 'Unknown error')}")
            
            # Test multiple queries
            st.write("**Multiple Query Test**")
            test_queries = [
                "MainActivity class",
                "onCreate method",
                "Fragment navigation",
                "Button click listener"
            ]
            
            if st.button("Run Multiple Query Test"):
                with st.spinner("Testing multiple queries..."):
                    results = self.test_multiple_queries(test_queries)
                    if results:
                        st.success(f"✅ Tested {len(results)} queries")
                        for query, result in results.items():
                            if "error" not in result:
                                st.info(f"✅ {query}: {len(result)} results")
                            else:
                                st.warning(f"⚠️ {query}: {result.get('error')}")
        
        with tabs[4]:  # Configuration
            st.subheader("⚙️ Configuration Debug")
            config_info = {
                "project_type": self.project_config.project_type,
                "extensions": self.project_config.get_extensions(),
                "ollama_model": self.ollama_model,
                "embedding_model": self.embedding_model,
                "ollama_endpoint": self.ollama_endpoint,
                "database_path": self.project_config.get_db_dir(),
                "logs_path": self.project_config.get_logs_dir()
            }
            st.json(config_info)
            log_to_sublog(self.project_dir, "debug_tools.log", f"Configuration: {config_info}")
            
            # Database debug report
            st.write("**Database Debug Report**")
            if st.button("Generate Debug Report"):
                with st.spinner("Generating debug report..."):
                    report = self.get_database_debug_report()
                    if "error" not in report:
                        st.success("✅ Debug report generated!")
                        st.json(report)
                    else:
                        st.error(f"❌ Error generating debug report: {report.get('error')}")

# Legacy functions for backward compatibility
def load_documents_from_vector_db(vector_db_dir):
    """Loads all Document metadata for inspection/debugging."""
    try:
        from langchain_ollama import OllamaEmbeddings
        from langchain_community.vectorstores import Chroma
        
        embeddings = OllamaEmbeddings(model="nomic-embed-text:latest")
        vectorstore = Chroma(
            persist_directory=vector_db_dir,
            embedding_function=embeddings
        )
        
        collection = vectorstore._collection
        results = collection.get()
        documents = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        chunks = []
        for i, metadata in enumerate(metadatas):
            if metadata:
                chunks.append({
                    "content": documents[i] if i < len(documents) else "",
                    "metadata": metadata
                })
        
        return chunks
    except Exception as e:
        print(f"Error loading documents: {e}")
        return []

def load_hierarchical_index(vector_db_dir):
    """Loads the project's hierarchical_index.json if available."""
    index_file = os.path.join(vector_db_dir, "hierarchical_index.json")
    if not os.path.isfile(index_file):
        return {}
    with open(index_file, "r") as f:
        return json.load(f)

def surface_anchorless_chunks(vector_db_dir, required_anchors=None):
    """Returns a list of chunks/documents missing all required anchors."""
    if required_anchors is None:
        required_anchors = ["screen_name", "class_names", "function_names", "component_name"]
    
    chunks = load_documents_from_vector_db(vector_db_dir)
    anchorless = []
    
    for chunk in chunks:
        meta = chunk.get("metadata", {})
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
