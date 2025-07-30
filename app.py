# app.py

import streamlit as st
from ui_components import UIComponents
from chat_handler import ChatHandler
from rag_manager import RAGManager

# Page configuration
st.set_page_config(page_title="🧠 Codebase Q&A", layout="wide")
st.title("💬 Chat with Your Codebase")

# Initialize components
ui = UIComponents()
rag_manager = RAGManager()

# Initialize session state
rag_manager.initialize_session_state()

# Render sidebar and get configuration
project_dir, ollama_model, ollama_endpoint, force_rebuild, debug_mode = ui.render_sidebar_config()

# Check if project type is selected
if st.session_state.get("selected_project_type") is None:
    ui.render_welcome_screen()
    st.stop()

# Setup project configuration and LLM
project_config = rag_manager.get_project_config(st.session_state.selected_project_type)
llm = rag_manager.setup_llm(ollama_model, ollama_endpoint)

# Main content area
st.subheader("💬 Ask about your codebase")
ui.render_project_info(project_config)
ui.render_custom_css()

# Create log placeholder
log_placeholder = st.empty()

# Build RAG index if needed
if rag_manager.should_rebuild_index(project_dir, force_rebuild):
    rag_manager.build_rag_index(
        project_dir, ollama_model, ollama_endpoint, 
        st.session_state.selected_project_type, log_placeholder
    )

# Chat interface
if rag_manager.is_ready():
    # Initialize chat handler
    chat_handler = ChatHandler(llm, project_config)
    
    # Render chat input
    query, submitted = ui.render_chat_input(project_config)
    
    # Process query if submitted
    if submitted and query:
        with st.spinner("💭 Thinking..."):
            chat_handler.process_query(
                query, st.session_state["qa_chain"], 
                log_placeholder, debug_mode
            )
else:
    st.warning("⚠️ Please build the RAG index first by clicking '🔁 Rebuild Index' in the sidebar")

# Display chat history
ui.render_chat_history()

# Debug section
if debug_mode:
    ui.render_debug_section(project_config, ollama_model, ollama_endpoint, project_dir)

# Processing logs
ui.render_processing_logs(log_placeholder, debug_mode)
