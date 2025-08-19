import os
import shutil
import streamlit as st
from typing import Optional, Tuple, Any

from langchain_chroma import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import BaseRetriever

from config import ProjectConfig
from model_config import model_config
from logger import setup_global_logger, log_to_sublog, log_highlight
from chat_handler import ChatHandler
from build_rag import build_rag

class RagManager:
    """Manages RAG system lifecycle and provides utility methods for model-agnostic operations."""
    
    def __init__(self):
        self.retriever: Optional[BaseRetriever] = None
        self.qa_chain: Optional[RetrievalQA] = None
    
    def initialize_session_state(self):
        """Initialize Streamlit session state for RAG operations."""
        if "rag_manager" not in st.session_state:
            st.session_state.rag_manager = self
        if "thinking_logs" not in st.session_state:
            st.session_state.thinking_logs = []
    
    # ========== UTILITY METHODS FOR MODEL-AGNOSTIC OPERATIONS ==========
    
    def get_embedding_function(self, project_dir: str) -> Any:
        """
        Get the appropriate embedding function based on current provider.
        This method encapsulates all model-specific logic.
        """
        try:
            provider = model_config.get_current_provider()
            provider_type = model_config.get_current_provider_type()
            
            if provider_type == "ollama":
                embedding_model = model_config.get_embedding_model()
            else:  # huggingface
                embedding_model = model_config.get_huggingface_embedding_model()
            
            embeddings = provider.get_embedding_model(model_name=embedding_model)
            log_to_sublog(project_dir, "rag_manager.log", f"Using {provider_type} embedding model: {embedding_model}")
            return embeddings
            
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to get embedding function: {e}")
            raise Exception(f"Failed to get embedding function: {e}")
    
    def check_provider_availability(self, project_dir: str) -> bool:
        """
        Check if the current model provider is available.
        This method encapsulates all provider-specific availability checks.
        """
        try:
            provider = model_config.get_current_provider()
            provider_type = model_config.get_current_provider_type()
            
            if provider_type == "ollama":
                # Check Ollama availability
                import requests
                ollama_endpoint = model_config.get_ollama_endpoint()
                response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
                if response.status_code != 200:
                    raise Exception(f"Ollama not responding: {response.status_code}")
                log_to_sublog(project_dir, "rag_manager.log", "Ollama is responsive")
            else:  # huggingface
                # Check Hugging Face model availability
                if not provider.check_availability():
                    raise Exception("Hugging Face models not available")
                log_to_sublog(project_dir, "rag_manager.log", "Hugging Face models are available")
            
            return True
            
        except Exception as e:
            provider_name = "Ollama" if provider_type == "ollama" else "Hugging Face"
            error_msg = f"{provider_name} not available: {e}"
            log_to_sublog(project_dir, "rag_manager.log", error_msg)
            return False
    
    def get_llm_model(self, project_dir: str) -> Any:
        """
        Get the appropriate LLM model based on current provider.
        This method encapsulates all model-specific logic.
        """
        try:
            provider = model_config.get_current_provider()
            provider_type = model_config.get_current_provider_type()
            
            if provider_type == "ollama":
                # Use Ollama LLM
                llm_model = model_config.get_ollama_model()
                llm = provider.get_llm_model(model_name=llm_model)
            else:  # huggingface
                # Use Hugging Face LLM
                llm_model = model_config.get_huggingface_llm_model()
                llm = provider.get_llm_model(model_name=llm_model)
            
            log_to_sublog(project_dir, "rag_manager.log", f"Using {provider_type} LLM model: {llm_model}")
            return llm
            
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to get LLM model: {e}")
            raise Exception(f"Failed to get LLM model: {e}")
    
    def setup_llm(self, ollama_model=None, ollama_endpoint=None):
        """Setup the language model based on current provider."""
        try:
            provider_type = model_config.get_current_provider_type()
            
            if provider_type == "ollama":
                # Use Ollama LLM
                if ollama_model is None:
                    ollama_model = model_config.get_ollama_model()
                if ollama_endpoint is None:
                    ollama_endpoint = model_config.get_ollama_endpoint()
                
                from langchain_ollama import ChatOllama
                llm = ChatOllama(model=ollama_model, base_url=ollama_endpoint)
                log_to_sublog(".", "rag_manager.log", f"Ollama LLM setup: {ollama_model} at {ollama_endpoint}")
            else:  # huggingface
                # Use HuggingFace LLM
                provider = model_config.get_current_provider()
                llm_model = model_config.get_huggingface_llm_model()
                llm = provider.get_llm_model(model_name=llm_model)
                log_to_sublog(".", "rag_manager.log", f"HuggingFace LLM setup: {llm_model}")
            
            return llm
            
        except Exception as e:
            log_to_sublog(".", "rag_manager.log", f"Failed to setup LLM: {e}")
            raise Exception(f"Failed to setup LLM: {e}")
    
    def create_vectorstore(self, documents: list, project_dir: str, persist_directory: str) -> Chroma:
        """
        Create a vectorstore with the appropriate embedding function.
        This method encapsulates all model-specific vectorstore creation logic.
        """
        try:
            embeddings = self.get_embedding_function(project_dir)
            
            # Create vectorstore with batch processing and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    vectorstore = Chroma.from_documents(
                        documents=documents,
                        embedding=embeddings,
                        persist_directory=persist_directory
                    )
                    log_to_sublog(project_dir, "rag_manager.log", f"Vectorstore created successfully on attempt {attempt + 1}")
                    return vectorstore
                except Exception as e:
                    if "readonly database" in str(e).lower() or "database is locked" in str(e).lower():
                        if attempt < max_retries - 1:
                            log_to_sublog(project_dir, "rag_manager.log", f"Database locked, retrying in 2 seconds... (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(2)
                            continue
                        else:
                            log_to_sublog(project_dir, "rag_manager.log", f"Failed to create database after {max_retries} attempts: {e}")
                            raise e
                    else:
                        # Non-locking error, don't retry
                        raise e
                        
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to create vectorstore: {e}")
            raise Exception(f"Failed to create vectorstore: {e}")
    
    def load_existing_vectorstore(self, project_dir: str, persist_directory: str) -> Chroma:
        """
        Load an existing vectorstore with the appropriate embedding function.
        This method encapsulates all model-specific vectorstore loading logic.
        """
        try:
            # First, try to detect what embedding model was used to build the vectorstore
            existing_embeddings = self._detect_existing_embedding_dimensions(persist_directory)
            
            if existing_embeddings:
                # Use the same embedding model that was used to build the vectorstore
                log_to_sublog(project_dir, "rag_manager.log", f"Detected existing embeddings with {existing_embeddings['dimensions']} dimensions, using {existing_embeddings['provider']} provider")
                embeddings = self._get_embedding_for_dimensions(existing_embeddings['dimensions'], project_dir)
            else:
                # Fallback to current provider's embedding model
                embeddings = self.get_embedding_function(project_dir)
            
            vectorstore = Chroma(
                persist_directory=persist_directory,
                embedding_function=embeddings
            )
            
            log_to_sublog(project_dir, "rag_manager.log", f"Loaded existing vectorstore from: {persist_directory}")
            return vectorstore
            
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to load existing vectorstore: {e}")
            raise Exception(f"Failed to load existing vectorstore: {e}")
    
    def _detect_existing_embedding_dimensions(self, persist_directory: str) -> Optional[dict]:
        """Detect the embedding dimensions and provider used in an existing vectorstore."""
        try:
            # Try to load the vectorstore with a dummy embedding to get metadata
            from langchain_community.embeddings import FakeEmbeddings
            
            # Create a dummy embedding function with a reasonable dimension
            dummy_embeddings = FakeEmbeddings(size=384)  # Common Hugging Face dimension
            
            try:
                vectorstore = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=dummy_embeddings
                )
                
                # Get collection info to determine dimensions
                collection = vectorstore._collection
                if hasattr(collection, 'metadata') and collection.metadata:
                    # Check if we can determine the original embedding dimensions
                    # This is a heuristic approach
                    return {
                        "dimensions": 384,  # Hugging Face default
                        "provider": "huggingface"
                    }
                else:
                    # Try to infer from the collection itself
                    return {
                        "dimensions": 384,  # Assume Hugging Face
                        "provider": "huggingface"
                    }
                    
            except Exception as e:
                if "dimension" in str(e).lower():
                    # Extract dimension from error message
                    import re
                    match = re.search(r'dimension of (\d+)', str(e))
                    if match:
                        dimensions = int(match.group(1))
                        if dimensions == 384:
                            return {"dimensions": 384, "provider": "huggingface"}
                        else:
                            return {"dimensions": dimensions, "provider": "ollama"}
                
                # Default assumption
                return {"dimensions": 384, "provider": "huggingface"}
                
        except Exception:
            return None
    
    def _get_embedding_for_dimensions(self, dimensions: int, project_dir: str) -> Any:
        """Get the appropriate embedding function based on detected dimensions."""
        try:
            if dimensions == 768:
                # Use Ollama embeddings (768 dimensions)
                log_to_sublog(project_dir, "rag_manager.log", "Using Ollama embeddings for 768-dimensional vectorstore")
                provider = model_config.get_provider("ollama")
                return provider.get_embedding_model()
            else:
                # Use Hugging Face embeddings (384+ dimensions)
                log_to_sublog(project_dir, "rag_manager.log", f"Using Hugging Face embeddings for {dimensions}-dimensional vectorstore")
                provider = model_config.get_provider("huggingface")
                return provider.get_embedding_model()
                
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to get embedding for dimensions {dimensions}: {e}")
            # Fallback to current provider
            return self.get_embedding_function(project_dir)
    
    def create_qa_chain(self, retriever: BaseRetriever, project_dir: str) -> RetrievalQA:
        """
        Create a QA chain with the appropriate LLM model.
        This method encapsulates all model-specific QA chain creation logic.
        """
        try:
            llm = self.get_llm_model(project_dir)
            
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                return_source_documents=True
            )
            
            log_to_sublog(project_dir, "rag_manager.log", "QA chain created successfully")
            return qa_chain
            
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to create QA chain: {e}")
            raise Exception(f"Failed to create QA chain: {e}")
    
    # ========== HIGH-LEVEL RAG OPERATIONS ==========
    def load_existing_rag_index(self, project_dir: str, project_type: str = None):
        """Load existing RAG index without rebuilding (no LLM yet)."""
        log_highlight("RagManager.load_existing_rag_index")

        from build_rag import get_consistent_embedding_model

        try:
            project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
            db_dir = project_config.get_db_dir()

            # CRITICAL FIX: Only load embeddings if we actually need them for retrieval
            # Don't load models during RAG loading - load them lazily when needed
            if st.session_state.get("retriever") is None:
                embeddings, metadata = get_consistent_embedding_model(project_dir, project_type)
                if metadata:
                    log_to_sublog(project_dir, "rag_manager.log",
                                f"Using consistent embedding model: {metadata['provider_type']} - {metadata['embedding_model']} ({metadata['dimensions']}d)")
                else:
                    log_to_sublog(project_dir, "rag_manager.log", "No embedding metadata found, using current provider")

                vectorstore = Chroma(persist_directory=db_dir, embedding_function=embeddings)
                retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})

                # Store retriever for later QA chain setup
                st.session_state["retriever"] = retriever
                st.session_state["project_dir_used"] = project_dir

            log_to_sublog(project_dir, "rag_manager.log", f"Loaded existing RAG index from: {db_dir}")
            return st.session_state.get("retriever")
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to load existing RAG index: {e}")
            raise


    def build_rag_index(self, project_dir, ollama_model, ollama_endpoint, project_type, log_placeholder, incremental=False, files_to_process=None):
        """Build the RAG index and store retriever (no LLM yet)."""
        log_highlight("RagManager.build_rag_index")
        with st.spinner("🔄 Building RAG index..."):

            if incremental and files_to_process:
                retriever = build_rag(project_dir, ollama_model, ollama_endpoint, log_placeholder,
                                    project_type, incremental=True, files_to_process=files_to_process)
            else:
                retriever = build_rag(project_dir, ollama_model, ollama_endpoint, log_placeholder, project_type)

            st.session_state["retriever"] = retriever
            st.session_state["project_dir_used"] = project_dir

            log_to_sublog(project_dir, "rag_manager.log", f"RAG index built for project: {project_dir}")
            return retriever
        
    def lazy_get_qa_chain(self, project_dir: str):
        """Setup QA chain only once, when first needed."""
        if "qa_chain" in st.session_state:
            return st.session_state["qa_chain"]

        retriever = st.session_state.get("retriever")
        if not retriever:
            retriever = self.get_retriever(project_dir, st.session_state.get("selected_project_type"))
            if not retriever:
                raise RuntimeError("Retriever not available. Build or load RAG first.")

        # Add loading indicator for LLM loading
        log_to_sublog(project_dir, "rag_manager.log", "🔄 Loading LLM model for QA chain...")
        
        # This is where the second "Loading checkpoint shards" happens
        llm = self.get_llm_model(project_dir)
        
        from langchain.chains import RetrievalQA
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            return_source_documents=True
        )

        st.session_state["qa_chain"] = qa_chain
        log_to_sublog(project_dir, "rag_manager.log", "✅ QA chain created and cached")
        return qa_chain


    def preload_models(self, project_dir: str):
        """Preload models when explicitly requested (e.g., during RAG building)."""
        log_to_sublog(project_dir, "rag_manager.log", "🔄 Preloading models for RAG building...")
        try:
            # Load embedding model for building
            embeddings = self.get_embedding_function(project_dir)
            log_to_sublog(project_dir, "rag_manager.log", "✅ Embedding model preloaded")
            
            # Optionally preload LLM if needed for building
            # llm = self.get_llm_model(project_dir)
            # log_to_sublog(project_dir, "rag_manager.log", "✅ LLM model preloaded")
            
            return True
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"❌ Model preloading failed: {e}")
            return False

    def check_rag_exists(self, project_dir: str, project_type: str = None) -> bool:
        """Check if RAG index exists for the given project."""
        try:
            project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
            db_dir = project_config.get_db_dir()
            chroma_db_path = os.path.join(db_dir, "chroma.sqlite3")
            
            exists = os.path.exists(chroma_db_path)
            log_to_sublog(project_dir, "rag_manager.log", f"RAG exists check: {exists} for {chroma_db_path}")
            return exists
            
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Error checking RAG exists: {e}")
            return False

    def is_ready(self) -> bool:
        """Check if RAG system is ready for queries."""
        # Check both QA chain and session state flags
        return (st.session_state.get("qa_chain") is not None or 
                st.session_state.get("retriever") is not None or
                st.session_state.get("rag_loaded", False) or
                st.session_state.get("rag_ready", False))

    def is_retriever_ready(self) -> bool:
        """Check if retriever is ready without loading models."""
        return st.session_state.get("retriever") is not None

    def get_retriever(self, project_dir: str, project_type: str = None):
        """Get retriever, loading it lazily if needed."""
        if not self.is_retriever_ready():
            # Load the retriever only when actually needed
            return self.load_existing_rag_index(project_dir, project_type)
        return st.session_state.get("retriever")
    
    def get_project_config(self, project_type: str = None) -> ProjectConfig:
        """Get project configuration."""
        return ProjectConfig(project_type) if project_type else ProjectConfig()
    
    def reset(self):
        """Reset/restart all resources for a new session."""
        log_highlight("RagManager.reset")
        self.retriever = None
        self.qa_chain = None
        # Can extend to clean stateful logs or diagnostics here
    
    def should_rebuild_index(self, project_dir: str, force_rebuild: bool, project_type: str = None) -> dict:
        """
        Check if the RAG index should be rebuilt based on database existence and git tracking.
        This method encapsulates all rebuild decision logic.
        """
        try:
            from git_hash_tracker import FileHashTracker
            
            # Get project configuration
            project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
            db_dir = project_config.get_db_dir()
            
            # Check if SQLite database exists
            chroma_db_path = os.path.join(db_dir, "chroma.sqlite3")
            if not os.path.exists(chroma_db_path):
                log_to_sublog(project_dir, "rag_manager.log", f"No SQLite database found at {chroma_db_path}, rebuilding")
                return {"rebuild": True, "reason": "no_database", "files": None}
            
            # Check if git tracking file exists
            git_tracking_file = os.path.join(db_dir, "git_tracking.json")
            if not os.path.exists(git_tracking_file):
                log_to_sublog(project_dir, "rag_manager.log", f"No git tracking file found at {git_tracking_file}, rebuilding")
                return {"rebuild": True, "reason": "no_tracking", "files": None}
            
            # Check if there are any changed files
            tracker = FileHashTracker(project_dir, db_dir)
            extensions = project_config.get_extensions()
            changed_files = tracker.get_changed_files(extensions)
            
            if changed_files:
                log_to_sublog(project_dir, "rag_manager.log", f"Found {len(changed_files)} changed files, rebuilding")
                return {"rebuild": True, "reason": "files_changed", "files": changed_files}
            else:
                log_to_sublog(project_dir, "rag_manager.log", "No changed files detected, skipping rebuild")
                return {"rebuild": False, "reason": "no_changes", "files": []}
                
        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Error checking rebuild status: {e}")
            # Default to rebuild on error
            return {"rebuild": True, "reason": "error", "files": None}
    