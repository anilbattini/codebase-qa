import os
import streamlit as st
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from config import ProjectConfig
from logger import log_highlight, log_to_sublog
from build_rag import build_rag
from chat_handler import ChatHandler

class RagManager:
    """
    Orchestrates project session lifecycle: (re)build, load, and chat handler wiring.
    All side effects (indexing, logs, etc.) are routed via logger.py.
    """

    def __init__(self):
        self.llm = None
        self.retriever = None
        self.qa_chain = None
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        st.session_state.setdefault("retriever", None)
        st.session_state.setdefault("project_dir_used", None)
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.setdefault("qa_chain", None)
        st.session_state.setdefault("chat_history", [])
    
    def setup_llm(self, ollama_model, ollama_endpoint):
        """Setup the language model."""
        self.llm = ChatOllama(model=ollama_model, base_url=ollama_endpoint)
        return self.llm
    
    def should_rebuild_index(self, project_dir, force_rebuild):
        """Check if the RAG index should be rebuilt."""
        return (
            st.session_state["retriever"] is None or
            st.session_state["project_dir_used"] != project_dir or
            force_rebuild
        )
    
    def build_rag_index(self, project_dir, ollama_model, ollama_endpoint, project_type, log_placeholder):
        """Build the RAG index and setup QA chain."""
        log_highlight("RagManager.build_rag_index")
        with st.spinner("🔄 Building RAG index..."):
            retriever = build_rag(
                project_dir=project_dir,
                ollama_model=ollama_model,
                ollama_endpoint=ollama_endpoint,
                log_placeholder=log_placeholder,
                project_type=project_type
            )
            
            st.session_state["retriever"] = retriever
            st.session_state["project_dir_used"] = project_dir
            log_to_sublog(project_dir, "rag_manager.log", f"RAG index built for project: {project_dir}")
            
            # Setup LLM first
            llm = self.setup_llm(ollama_model, ollama_endpoint)
            log_to_sublog(project_dir, "rag_manager.log", f"LLM setup: {ollama_model} at {ollama_endpoint}")
            
            # Setup QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                retriever=retriever,
                return_source_documents=True
            )
            st.session_state["qa_chain"] = qa_chain
            log_to_sublog(project_dir, "rag_manager.log", "QA chain created successfully")
            
            return retriever, qa_chain
    
    def get_project_config(self, project_type):
        """Get project configuration."""
        return ProjectConfig(project_type) if project_type else ProjectConfig()
    
    def is_ready(self):
        """Check if RAG system is ready for queries."""
        return st.session_state.get("qa_chain") is not None

    def reset(self):
        """Reset/restart all resources for a new session—used in tests or after rebuild."""
        log_highlight("RagManager.reset")
        self.retriever = None
        self.qa_chain = None
        # Can extend to clean stateful logs or diagnostics here

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - Parameter-based constructor that required project_dir, model, endpoint - replaced with simple constructor for better flexibility.
# - Complex build_or_load_rag method - simplified to build_rag_index with clear separation of concerns.
# ADDED
# - initialize_session_state: Proper session state initialization for Streamlit app.
# - setup_llm: Dedicated method for LLM setup with proper logging.
# - build_rag_index: Enhanced with proper logging using logger.py utilities.
# - Enhanced logging throughout with log_highlight and log_to_sublog for better debugging.
# - Fixed method signature to match old working version with project_type and log_placeholder parameters.
