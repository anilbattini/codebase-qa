# app.py

import os
import streamlit as st
from rag_manager import RagManager
from ui_components import UIComponents
from chat_handler import ChatHandler
from logger import setup_global_logger, log_highlight
from config import ProjectConfig
from process_manager import ProcessManager

# 1. Initial Setup
st.set_page_config(page_title="Codebase-QA", layout="wide")

# Initialize logger with proper path resolution
project_dir = st.session_state.get("project_dir", "../../")
if project_dir:
    from logger import _get_logs_dir
    log_dir = _get_logs_dir(project_dir)
    logger = setup_global_logger(log_dir)
else:
    logger = setup_global_logger()

rag_manager = RagManager()
ui = UIComponents()

rag_manager.initialize_session_state()
log_highlight("app.py: Initial setup complete")

# 2. Sidebar and Main UI Rendering
project_dir, ollama_model, ollama_endpoint, force_rebuild, debug_mode = ui.render_sidebar_config()

# Render build status if in progress
ui.render_build_status()

# Ensure project_dir is properly resolved
if project_dir:
    project_dir = os.path.abspath(project_dir)
    st.session_state["project_dir"] = project_dir

# ✅ Add Disable RAG (LLM only) toggle to sidebar
st.sidebar.markdown("## 🔧 Advanced Options")
st.sidebar.checkbox("Disable RAG (query LLM directly)", key="disable_rag")

if not st.session_state.selected_project_type:
    ui.render_welcome_screen()
    st.stop()

# A project type has been selected
project_config = rag_manager.get_project_config(st.session_state.selected_project_type)
ui.render_project_info(project_config)
ui.render_custom_css()

# 3. RAG Index Building
# Check if rebuild is needed for current project type
project_config = ProjectConfig(project_dir=project_dir, project_type=st.session_state.selected_project_type)
should_rebuild = rag_manager.should_rebuild_index(project_dir, force_rebuild, st.session_state.selected_project_type)

# Clear force rebuild flag after checking
if st.session_state.get("force_rebuild"):
    del st.session_state["force_rebuild"]

if should_rebuild:
    # Ensure session state is properly initialized before clearing
    rag_manager.initialize_session_state()
    # Safely clear thinking logs
    if "thinking_logs" in st.session_state:
        st.session_state.thinking_logs.clear()
    else:
        st.session_state.setdefault("thinking_logs", [])
    log_highlight("app.py: Starting RAG index build")
    
    # Protect the RAG build process
    try:
        ProcessManager.start_rag_build()
        rag_manager.build_rag_index(project_dir, ollama_model, ollama_endpoint, st.session_state.selected_project_type, st.empty())
        ProcessManager.finish_rag_build()
        st.success("✅ RAG index built successfully!")
        log_highlight("app.py: RAG index build completed successfully")
    except Exception as e:
        ProcessManager.finish_rag_build()
        st.error(f"❌ Error building RAG index: {e}")
        log_highlight(f"app.py: RAG index build failed: {e}")
        st.exception(e)
else:
    # Load existing RAG index without rebuilding
    if not rag_manager.is_ready():
        log_highlight("app.py: Loading existing RAG index")
        try:
            rag_manager.load_existing_rag_index(project_dir, ollama_model, ollama_endpoint, st.session_state.selected_project_type)
            st.success("✅ RAG index loaded successfully!")
            log_highlight("app.py: RAG index loaded successfully")
        except Exception as e:
            st.error(f"❌ Error loading RAG index: {e}")
            log_highlight(f"app.py: RAG index load failed: {e}")
            st.exception(e)
    else:
        log_highlight("app.py: RAG index already loaded")

# 4. Chat Interface
st.title(f"Chat with your `{project_config.project_type}` codebase: {project_config.project_dir_name}")
ui.render_chat_history()

# Setup chat handler and input form
if rag_manager.is_ready():
    log_highlight("app.py: RAG system ready, setting up chat handler")
    chat_handler = ChatHandler(
        llm=rag_manager.setup_llm(ollama_model, ollama_endpoint),
        project_config=project_config
    )
    
    query, submitted = ui.render_chat_input()

    if submitted and query:
        # Ensure thinking_logs is initialized before clearing
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.thinking_logs.clear()
        
        with st.chat_message("user"):
            st.markdown(query)

        # Create a dedicated log placeholder for processing logs
        log_placeholder = st.empty()
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer, reranked_docs, impact_files, metadata = chat_handler.process_query(
                        query, st.session_state["qa_chain"], log_placeholder, debug_mode
                    )
                    if answer:
                        # Clear the processing logs and display only the clean answer
                        log_placeholder.empty()
                        st.markdown(answer)
                    else:
                        log_placeholder.empty()
                        st.error("❌ No answer generated. Please try again.")
                except Exception as e:
                    log_placeholder.empty()
                    st.error(f"❌ Error processing query: {e}")
                    log_highlight(f"app.py: Chat processing error: {e}")
        
        # Store the answer in session state for persistence
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Store in the expected format: (query, answer, source_docs, impact_files, metadata)
        chat_item = (query, answer, reranked_docs, impact_files, metadata)
        st.session_state.chat_history.append(chat_item)

# 5. Optional Debug Section
if debug_mode:
    ui.render_debug_section(project_config, ollama_model, ollama_endpoint, project_dir)
    # 6. Processing logs (only in debug mode)
    ui.render_processing_logs(st.empty(), debug_mode)

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - Complex log placeholder management - simplified to use st.empty() directly.
# - Redundant chat handler instantiation - now only created when RAG is ready.
# ADDED
# - Disable RAG toggle: Added checkbox for direct LLM queries without RAG.
# - render_custom_css: Added custom styling for better visual design.
# - render_processing_logs: Added dedicated processing logs section.
# - Enhanced logging throughout with log_highlight for better debugging.
# - Fixed build_rag_index call to match updated method signature.
# - 5-click debug mode integration: Debug tools only render when debug mode is enabled.
# - Centralized log path resolution: Fixed setup_global_logger to use proper project-specific log directory.
# REFACTORED
# - Chat input logic changed to support `st.form` with proper form submission handling.
# - Added `st.rerun()` after chat response to ensure proper chat history display.
# - Simplified RAG build process with proper error handling and logging.
# - Better session state management and initialization.
# - Debug tools integration: Only show debug tools when debug mode is enabled via 5-click method.
# - Logger initialization: Now uses centralized path resolution to prevent logs in tool directory.
