# rag_manager.py

import streamlit as st
from langchain_ollama import ChatOllama
from langchain.chains import RetrievalQA
from build_rag import build_rag
from config import ProjectConfig

class RAGManager:
    """Manages RAG setup, building, and retrieval functionality."""
    
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
            
            # Setup QA chain
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever,
                return_source_documents=True
            )
            st.session_state["qa_chain"] = qa_chain
            
            return retriever, qa_chain
    
    def get_project_config(self, project_type):
        """Get project configuration."""
        return ProjectConfig(project_type) if project_type else ProjectConfig()
    
    def is_ready(self):
        """Check if RAG system is ready for queries."""
        return st.session_state.get("qa_chain") is not None
