# ui_components.py

import streamlit as st
import os
import shutil
from config import ProjectConfig

class UIComponents:
    """Handles all UI rendering components for the RAG app."""
    
    def __init__(self):
        self.project_config = None
    
    def render_sidebar_config(self):
        """Render the sidebar configuration section."""
        with st.sidebar:
            st.header("🔧 Configuration")
            
            project_dir = st.text_input("📁 Project Directory", value="../")
            
            # Project type selection
            project_types = list(ProjectConfig.LANGUAGE_CONFIGS.keys())
            
            # Check if we have a stored project type
            if "selected_project_type" not in st.session_state:
                st.session_state.selected_project_type = None
            
            self._render_project_type_selector(project_types)
            
            ollama_model = st.text_input("🧠 Ollama Model", value="llama3.1")
            ollama_endpoint = st.text_input("🔗 Ollama Endpoint", value="http://127.0.0.1:11434")
            
            # Only show rebuild button if project type is selected
            if st.session_state.selected_project_type:
                force_rebuild = st.button("🔁 Rebuild Index")
            else:
                force_rebuild = False
                st.info("👆 Select project type first")
            
            # Debug mode toggle
            st.divider()
            debug_mode = st.checkbox("🔧 Enable Debug Mode", help="Show debugging tools and detailed logs")
            
            return project_dir, ollama_model, ollama_endpoint, force_rebuild, debug_mode
    
    def _render_project_type_selector(self, project_types):
        """Render project type selection and change dialog."""
        if st.session_state.selected_project_type is None:
            st.warning("⚠️ Please select your project type to begin")
            
            selected_type = st.selectbox(
                "🎯 Select Project Type",
                [""] + project_types,
                index=0,
                key="project_type_selector",  # Add unique key
                help="Choose the primary programming language/framework of your project"
            )
            
            if selected_type and selected_type != "":
                if st.button("✅ Confirm Project Type"):
                    st.session_state.selected_project_type = selected_type
                    st.success(f"✅ Project type set to: {selected_type}")
                    st.rerun()
        else:
            self._render_project_type_change_dialog(project_types)
    
    def _render_project_type_change_dialog(self, project_types):
        """Render the project type change dialog."""
        current_type = st.session_state.selected_project_type
        st.success(f"📌 Current project type: **{current_type}**")
        
        if st.button("🔄 Change Project Type"):
            st.session_state.show_project_change_dialog = True
        
        if st.session_state.get("show_project_change_dialog", False):
            st.warning("⚠️ **Changing project type will rebuild the entire index!**")
            st.info("💡 **Recommendation:** Backup your `vector_db` folder before proceeding")
            
            new_type = st.selectbox(
                "🎯 New Project Type",
                project_types,
                index=project_types.index(current_type) if current_type in project_types else 0
            )
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Confirm Change"):
                    self._handle_project_type_change(new_type)
            
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_project_change_dialog = False
                    st.rerun()
            
            with col3:
                if st.button("💾 Backup First"):
                    st.info("📋 **Manual Backup Instructions:**\n1. Copy the `vector_db` folder\n2. Rename it to `vector_db_backup`\n3. Then proceed with the change")
    
    def _handle_project_type_change(self, new_type):
        """Handle project type change with cleanup."""
        if os.path.exists("./vector_db"):
            try:
                shutil.rmtree("./vector_db")
                st.success("🗑️ Cleared existing vector database")
            except Exception as e:
                st.error(f"Error clearing vector DB: {e}")
        
        st.session_state.selected_project_type = new_type
        
        for key in ['retriever', 'qa_chain', 'project_dir_used']:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state.show_project_change_dialog = False
        st.success(f"✅ Changed to {new_type}. Please rebuild the index.")
        st.rerun()
    
    def render_welcome_screen(self):
        """Render welcome screen when no project type is selected."""
        st.info("🎯 **Welcome!** Please select your project type in the sidebar to get started.")
        
        st.markdown("""
        **Supported Project Types:**
        - **Android**: Kotlin/Java Android applications
        - **JavaScript**: Node.js, React, Vue.js projects  
        - **Python**: Django, Flask, FastAPI applications
        - **Web**: HTML/CSS/JS frontend projects
        """)
    
    def render_project_info(self, project_config):
        """Render current project information."""
        st.info(f"🎯 Analyzing: **{project_config.project_type.upper()}** project | Extensions: {', '.join(project_config.get_extensions())}")
    
    def render_custom_css(self):
        """Render custom CSS for styling."""
        st.markdown("""
        <style>
        .stExpander > div:first-child {
            background-color: #f0f2f6;
        }
        .stExpander > div:first-child:hover {
            background-color: #e6e9ef;
        }
        
        /* Custom styling for log text areas */
        .stTextArea textarea {
            font-family: 'Courier New', monospace !important;
            font-size: 12px !important;
            line-height: 1.4 !important;
        }
        
        /* Ensure text areas scroll to bottom (for newer logs) */
        .stTextArea textarea:focus {
            scroll-behavior: smooth;
        }
        </style>
        """, unsafe_allow_html=True)

    
    def render_chat_input(self, project_config):
        """Render chat input form."""
        with st.form("query_form", clear_on_submit=True):
            query = st.text_input(
                "📝 Your question",
                placeholder=f"What does this {project_config.project_type} project do?",
                key="query_input"
            )
            
            submitted = st.form_submit_button("🚀 Ask")
            
            return query, submitted
    
    def render_chat_history(self):
        """Render chat history with auto-expansion and enhanced metadata support."""
        if st.session_state.get("chat_history"):
            for i, chat_item in enumerate(reversed(st.session_state["chat_history"][-10:])):
                
                # Handle both old format (4 items) and new format (5 items) for backward compatibility
                if len(chat_item) == 4:
                    q, a, srcs, impact_files = chat_item
                    metadata = None
                elif len(chat_item) == 5:
                    q, a, srcs, impact_files, metadata = chat_item
                else:
                    # Skip malformed entries
                    continue
                
                qa_key = f"qa_{len(st.session_state['chat_history']) - 1 - i}"
                is_latest = qa_key == st.session_state.get("expand_latest")
                
                # Create expander title with enhanced information
                expander_title = f"Q: {q}"
                if metadata and metadata.get('intent'):
                    expander_title += f" [{metadata['intent'].title()}]"
                
                with st.expander(expander_title, expanded=is_latest):
                    st.markdown(f"**A:** {a}")
                    
                    # Show metadata if available (enhanced version)
                    if metadata:
                        with st.container():
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if metadata.get('intent'):
                                    st.caption(f"🎯 **Intent:** {metadata['intent'].title()}")
                                if metadata.get('confidence'):
                                    confidence_pct = round(metadata['confidence'] * 100, 1)
                                    st.caption(f"📊 **Confidence:** {confidence_pct}%")
                            
                            with col2:
                                if metadata.get('rewritten_query') and metadata['rewritten_query'] != q:
                                    st.caption(f"🔄 **Enhanced Query:** {metadata['rewritten_query'][:60]}...")
                    
                    # Show impact files
                    if impact_files:
                        st.markdown(f"**🔍 Impacted files:** {', '.join(impact_files)}")
                    
                    # Show sources with enhanced information
                    if srcs:
                        st.markdown("**🔎 Top Sources:**")
                        for doc in srcs[:5]:
                            md = doc.metadata
                            source_name = md.get('source', 'Unknown')
                            chunk_type = md.get('type', 'text')
                            chunk_index = md.get('chunk_index', 0)
                            summary = md.get('summary', '')
                            
                            # Enhanced source display
                            source_line = f"- `{source_name}` [{chunk_type}]"
                            
                            # Add chunk name if available
                            chunk_name = md.get('name')
                            if chunk_name:
                                source_line += f" *{chunk_name}*"
                            
                            source_line += f" (chunk {chunk_index})"
                            
                            # Add summary if available
                            if summary:
                                source_line += f" | {summary}"
                            
                            st.markdown(source_line)
                
                # Clean up expand_latest flag after showing
                if is_latest and "expand_latest" in st.session_state:
                    del st.session_state["expand_latest"]
    
    def render_debug_section(self, project_config, ollama_model, ollama_endpoint, project_dir):
        """Render debug tools section."""
        st.divider()
        st.subheader("🔧 Debug Tools")
        
        try:
            from debug_tools import DebugTools
            debug_tools = DebugTools(
                project_config=project_config,
                ollama_model=ollama_model,
                ollama_endpoint=ollama_endpoint,
                project_dir=project_dir
            )
            debug_tools.render_debug_interface(st.session_state.get("retriever"))
        except ImportError:
            st.error("Debug tools not available. Make sure debug_tools.py is in your project directory.")
    
    def render_processing_logs(self, log_placeholder, debug_mode):
        """Render processing logs section with scrollable display."""
        with st.expander("🛠️ Processing Logs", expanded=debug_mode):
            st.markdown("**Real-time processing status:**")
            
            # Get the logs from session state
            logs = st.session_state.get('thinking_logs', [])
            
            if logs:
                # Display logs as scrollable text area - each log on a new line
                log_text = "\n".join(logs[-50:])  # Show last 50 logs to prevent overwhelming
                
                # Create scrollable text area with fixed height
                st.text_area(
                    label="Processing Logs",
                    value=log_text,
                    height=300,  # Fixed height to enable scrolling
                    disabled=True,  # Make it read-only
                    key="processing_logs_display",
                    label_visibility="collapsed"  # Hide the label since we have markdown above
                )
            else:
                st.info("No logs available yet.")
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Clear Logs"):
                    st.session_state.thinking_logs = []
                    st.rerun()
            
            with col2:
                if st.button("📋 Copy Logs"):
                    if logs:
                        # This will show a text area that users can select and copy from
                        st.code("\n".join(logs), language="text")

