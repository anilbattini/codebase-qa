# rag_manager.py

import os
import shutil
import streamlit as st
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from config.config import ProjectConfig
from config.model_config import model_config
from logger import log_highlight, log_to_sublog
from build_rag import build_rag

class RagManager:
    """
    Orchestrates project session lifecycle: (re)build, load, and chat handler wiring.
    All side effects (indexing, logs, etc.) are routed via logger.py.
    """

    def __init__(self):
        self.llm = None
        self.retriever = None
        self.vectorstore = None

    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        st.session_state.setdefault("retriever", None)
        st.session_state.setdefault("project_dir_used", None)
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.setdefault("vectorstore", None)
        st.session_state.setdefault("chat_history", [])

    def setup_llm(self, ollama_model=None, ollama_endpoint=None):
        """Create LLM via centralized model_config factory."""
        overrides = {}
        if ollama_model:
            overrides['model'] = ollama_model
        if ollama_endpoint:
            overrides['endpoint'] = ollama_endpoint

        llm = model_config.get_llm(**overrides)
        self.llm = llm

        try:
            active = model_config.get_active_llm_config()
            log_to_sublog(self.project_dir if hasattr(self, 'project_dir') else ".",
                "rag_manager.log",
                f"LLM setup via model_config: provider={active.get('provider')} model={active.get('model')} endpoint={active.get('endpoint')}")
        except Exception as e:
            log_to_sublog(self.project_dir if hasattr(self, 'project_dir') else ".",
                "rag_manager.log",
                f"LLM setup via model_config (active config unavailable): {e}")

        return self.llm

    def cleanup_existing_files(self, project_dir, project_type):
        """Delete all existing generated files for a complete rebuild."""
        log_to_sublog(project_dir, "rag_manager.log", "=== FORCE REBUILD: CLEANING UP EXISTING FILES ===")
        try:
            project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
            db_dir = project_config.get_db_dir()

            cleanup_targets = []
            if os.path.exists(db_dir):
                cleanup_targets.append(db_dir)
                log_to_sublog(project_dir, "rag_manager.log", f"Will delete vector database directory: {db_dir}")

            for target in cleanup_targets:
                if os.path.exists(target):
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            if os.path.isdir(target):
                                shutil.rmtree(target)
                                log_to_sublog(project_dir, "rag_manager.log", f"✅ Deleted directory: {target}")
                            else:
                                os.remove(target)
                                log_to_sublog(project_dir, "rag_manager.log", f"✅ Deleted file: {target}")
                            break
                        except PermissionError as e:
                            if attempt < max_retries - 1:
                                log_to_sublog(project_dir, "rag_manager.log", 
                                    f"⚠️ Permission error deleting {target}, retrying in 1 second... (attempt {attempt + 1}/{max_retries})")
                                import time
                                time.sleep(1)
                            else:
                                log_to_sublog(project_dir, "rag_manager.log", 
                                    f"❌ Failed to delete {target} after {max_retries} attempts: {e}")
                                raise e
                        except Exception as e:
                            log_to_sublog(project_dir, "rag_manager.log", f"❌ Error deleting {target}: {e}")
                            raise e

            session_keys_to_clear = ["retriever", "vectorstore", "project_dir_used", "thinking_logs"]
            for key in session_keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
                    log_to_sublog(project_dir, "rag_manager.log", f"✅ Cleared session state: {key}")

            self.retriever = None
            self.vectorstore = None
            self.llm = None

            import time
            time.sleep(0.5)
            log_to_sublog(project_dir, "rag_manager.log", "=== CLEANUP COMPLETE ===")
            return True

        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"❌ Error during cleanup: {e}")
            import traceback
            log_to_sublog(project_dir, "rag_manager.log", f"Traceback: {traceback.format_exc()}")
            return False

    def should_rebuild_index(self, project_dir, force_rebuild, project_type):
        """Check if the RAG index should be rebuilt based on database existence and git tracking."""
        from git_hash_tracker import FileHashTracker

        project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
        db_dir = project_config.get_db_dir()

        chroma_db_path = os.path.join(db_dir, "chroma.sqlite3")
        if not os.path.exists(chroma_db_path):
            log_to_sublog(project_dir, "rag_manager.log", f"No SQLite database found at {chroma_db_path}, rebuilding")
            return {"rebuild": True, "reason": "no_database", "files": None}

        git_tracking_file = os.path.join(db_dir, "git_tracking.json")
        if not os.path.exists(git_tracking_file):
            log_to_sublog(project_dir, "rag_manager.log", f"No git tracking file found at {git_tracking_file}, rebuilding")
            return {"rebuild": True, "reason": "no_tracking", "files": None}

        tracker = FileHashTracker(project_dir, db_dir)
        extensions = project_config.get_extensions()
        changed_files = tracker.get_changed_files(extensions)

        if changed_files:
            log_to_sublog(project_dir, "rag_manager.log", f"Found {len(changed_files)} changed files, rebuilding")
            return {"rebuild": True, "reason": "files_changed", "files": changed_files}
        else:
            log_to_sublog(project_dir, "rag_manager.log", "No changed files detected, skipping rebuild")
            return {"rebuild": False, "reason": "no_changes", "files": []}

    def build_rag_index(self, project_dir, ollama_model, ollama_endpoint, project_type, log_placeholder, incremental=False, files_to_process=None):
        """Build the RAG index and setup QA chain."""
        log_highlight("RagManager.build_rag_index")
        with st.spinner("🔄 Building RAG index..."):
            if incremental and files_to_process:
                log_to_sublog(project_dir, "rag_manager.log", f"Incremental rebuild: processing {len(files_to_process)} changed files")
                vectorstore = build_rag(
                    project_dir=project_dir,
                    ollama_model=ollama_model,
                    ollama_endpoint=ollama_endpoint,
                    log_placeholder=log_placeholder,
                    project_type=project_type,
                    incremental=True,
                    files_to_process=files_to_process
                )
            else:
                log_to_sublog(project_dir, "rag_manager.log", "Full rebuild: processing all files")
                vectorstore = build_rag(
                    project_dir=project_dir,
                    ollama_model=ollama_model,
                    ollama_endpoint=ollama_endpoint,
                    log_placeholder=log_placeholder,
                    project_type=project_type
                )

            st.session_state["vectorstore"] = vectorstore
            st.session_state["project_dir_used"] = project_dir
            log_to_sublog(project_dir, "rag_manager.log", f"RAG index built for project: {project_dir}")

    def load_existing_rag_index(self, project_dir, ollama_model, ollama_endpoint, project_type):
        """Load existing RAG index without rebuilding."""
        log_highlight("RagManager.load_existing_rag_index")
        try:
            project_config = ProjectConfig(project_type=project_type, project_dir=project_dir)
            db_dir = project_config.get_db_dir()

            embedding_model = "nomic-embed-text:latest"

            try:
                import requests
                response = requests.get(f"{ollama_endpoint}/api/tags", timeout=5)
                if response.status_code == 200:
                    available_models = response.json().get("models", [])
                    model_names = [model.get("name", "") for model in available_models]
                    if embedding_model in model_names:
                        log_to_sublog(project_dir, "rag_manager.log", f"Using dedicated embedding model: {embedding_model}")
                    else:
                        log_to_sublog(project_dir, "rag_manager.log", f"Dedicated embedding model not found, using LLM model: {ollama_model}")
                        embedding_model = ollama_model
                else:
                    log_to_sublog(project_dir, "rag_manager.log", f"Could not check models, using LLM model: {ollama_model}")
                    embedding_model = ollama_model
            except Exception as e:
                log_to_sublog(project_dir, "rag_manager.log", f"Could not check available models, using LLM model: {e}")
                embedding_model = ollama_model

            embeddings = OllamaEmbeddings(model=embedding_model, base_url=ollama_endpoint)

            vectorstore = Chroma(
                persist_directory=db_dir,
                embedding_function=embeddings
            )

            st.session_state["vectorstore"] = vectorstore
            st.session_state["project_dir_used"] = project_dir
            log_to_sublog(project_dir, "rag_manager.log", f"Loaded existing RAG index built for: {project_dir}")

        except Exception as e:
            log_to_sublog(project_dir, "rag_manager.log", f"Failed to load existing RAG index: {e}")
            raise e

    def get_project_config(self, project_type):
        """Get project configuration."""
        return ProjectConfig(project_type) if project_type else ProjectConfig()

    def is_ready(self):
        """Check if RAG system is ready for queries."""
        return st.session_state.get("vectorstore") is not None

    def reset(self):
        """Reset/restart all resources for a new session."""
        log_highlight("RagManager.reset")
        self.retriever = None
        self.vectorstore = None
