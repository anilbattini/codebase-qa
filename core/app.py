# app.py

import os
import streamlit as st
from config.model_config import model_config
from rag_manager import RagManager
from ui_components import UIComponents
from query.chat_handler import ChatHandler
from logger import setup_global_logger, log_highlight
from logger import move_query_log
from config.config import ProjectConfig
from process_manager import ProcessManager
from dotenv import load_dotenv

# Initial Setup
load_dotenv()
st.cache_data.clear()
st.cache_resource.clear()
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

# Sidebar and Main UI Rendering
config_result = ui.render_sidebar_config()
project_dir, ollama_model, ollama_endpoint, force_rebuild, debug_mode, config_complete = config_result

# Render build status if in progress
ui.render_build_status()

# Ensure project_dir is properly resolved
if project_dir:
    project_dir = os.path.abspath(project_dir)
    st.session_state["project_dir"] = project_dir

st.session_state.setdefault("rated_logs", set())

# Add Disable RAG toggle to sidebar
st.sidebar.markdown("## 🔧 Advanced Options")
st.sidebar.checkbox("Disable RAG (query LLM directly)", key="disable_rag")

# Check if configuration is complete
if not config_complete:
    if not st.session_state.get("selected_project_type"):
        ui.render_welcome_screen()
        st.info("🎯 **Step 1**: Please select your project type in the sidebar to continue.")
    else:
        ui.render_welcome_screen()
        st.info("🔧 **Step 2**: Please select a provider in the sidebar to continue.")
    st.stop()

# Both project type and provider are selected - proceed with RAG logic
project_config = rag_manager.get_project_config(st.session_state.get("selected_project_type"))
ui.render_project_info(project_config)
ui.render_custom_css()

# RAG Index Building
if st.session_state.get("force_rebuild"):
    del st.session_state["force_rebuild"]
    log_highlight("app.py: Force rebuild requested by user")
    st.info("🔄 **Force Rebuild**: User requested complete rebuild. Cleaning existing data...")
    
    rag_manager.initialize_session_state()
    if "thinking_logs" in st.session_state:
        st.session_state.thinking_logs.clear()
    else:
        st.session_state.setdefault("thinking_logs", [])

    try:
        ProcessManager.start_rag_build()
        rag_manager.build_rag_index(
            project_dir, ollama_model, ollama_endpoint,
            st.session_state.get("selected_project_type"), st.empty()
        )
        ProcessManager.finish_rag_build()
        st.success("✅ RAG index rebuilt successfully!")
        log_highlight("app.py: Force RAG rebuild completed successfully")
    except Exception as e:
        ProcessManager.finish_rag_build()
        st.error(f"❌ Error rebuilding RAG index: {e}")
        log_highlight(f"app.py: Force RAG rebuild failed: {e}")
        st.exception(e)
else:
    # Check if rebuild is needed for current project type
    project_config = ProjectConfig(project_dir=project_dir, project_type=st.session_state.get("selected_project_type"))
    rebuild_info = rag_manager.should_rebuild_index(project_dir, False, st.session_state.get("selected_project_type"))
    
    if rebuild_info["rebuild"]:
        rag_manager.initialize_session_state()
        if "thinking_logs" in st.session_state:
            st.session_state.thinking_logs.clear()
        else:
            st.session_state.setdefault("thinking_logs", [])

        is_incremental = rebuild_info["reason"] == "files_changed" and rebuild_info["files"]
        
        if is_incremental:
            log_highlight(f"app.py: Starting incremental RAG build for {len(rebuild_info['files'])} changed files")
            st.info(f"🔄 **Incremental Build**: Processing {len(rebuild_info['files'])} changed files...")
        else:
            log_highlight("app.py: Starting full RAG build")
            st.info("🔄 **Full Build**: Rebuilding entire RAG index...")

        try:
            ProcessManager.start_rag_build()
            if is_incremental:
                rag_manager.build_rag_index(
                    project_dir, ollama_model, ollama_endpoint,
                    st.session_state.get("selected_project_type"), st.empty(),
                    incremental=True, files_to_process=rebuild_info["files"]
                )
            else:
                rag_manager.build_rag_index(
                    project_dir, ollama_model, ollama_endpoint,
                    st.session_state.get("selected_project_type"), st.empty()
                )
            ProcessManager.finish_rag_build()
            st.success("✅ RAG index built successfully!")
            log_highlight("app.py: RAG index build completed successfully")
        except Exception as e:
            ProcessManager.finish_rag_build()
            st.error(f"❌ Error building RAG index: {e}")
            log_highlight(f"app.py: RAG index build failed: {e}")
            st.exception(e)
    else:
        if rebuild_info["reason"] == "no_changes":
            st.success("✅ No file changes detected. RAG index is up to date.")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("💡 **No new files to process.** The RAG index is already up to date with the latest changes.")
            with col2:
                if st.button("🔄 Force Rebuild", type="secondary", help="Rebuild entire RAG from scratch"):
                    st.session_state["force_rebuild"] = True
                    st.success("🔄 Force rebuild requested! The RAG will be completely rebuilt.")
                    st.rerun()

        if not rag_manager.is_ready():
            log_highlight("app.py: Loading existing RAG index")
            try:
                rag_manager.load_existing_rag_index(project_dir, ollama_model, ollama_endpoint, st.session_state.get("selected_project_type"))
                st.success("✅ RAG index loaded successfully!")
                log_highlight("app.py: RAG index loaded successfully")
            except Exception as e:
                st.error(f"❌ Error loading RAG index: {e}")
                log_highlight(f"app.py: RAG index load failed: {e}")
                st.exception(e)
        else:
            log_highlight("app.py: RAG index already loaded")

# Chat Interface
st.title(f"Chat with your `{project_config.project_type}` codebase: {project_config.project_dir_name}")
ui.render_chat_history(project_dir)

# Setup chat handler and input form
if rag_manager.is_ready():
    log_highlight("app.py: RAG system ready, setting up chat handler")
    
    qa_llm = model_config.get_llm()
    rewrite_llm = model_config.get_rewrite_llm()
    
    chat_handler = ChatHandler(
        llm=qa_llm,
        provider=model_config.get_provider(),
        project_config=project_config,
        project_dir=project_dir,
        rewrite_llm=rewrite_llm
    )

    query, submitted = ui.render_chat_input()

    if submitted and query:
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.thinking_logs.clear()

        with st.chat_message("user"):
            st.markdown(query)

        log_placeholder = st.empty()
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    answer, reranked_docs, impact_files, metadata = chat_handler.process_query(
                        query, st.session_state["vectorstore"], log_placeholder, debug_mode
                    )

                    if answer:
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

        if debug_mode:
            moved = move_query_log(query, project_dir, debug_mode)
            if moved and debug_mode:
                log_path, liked_dir, disliked_dir = moved
                if log_path not in st.session_state.get("rated_logs", set()):
                    col1, col2 = st.columns(2)
                    if col1.button("👍 Like"):
                        ui._collect_feedback_ui(log_path, liked_dir)
                    if col2.button("👎 Dislike"):
                        ui._collect_feedback_ui(log_path, disliked_dir)
                metadata["log_path"] = log_path

        chat_item = (query, answer, reranked_docs, impact_files, metadata)
        st.session_state.chat_history.append(chat_item)

# Optional Debug Section
if debug_mode:
    ui.render_debug_section(project_config, ollama_model, ollama_endpoint, project_dir)

# Processing logs (only in debug mode)
ui.render_processing_logs(st.empty(), debug_mode)
