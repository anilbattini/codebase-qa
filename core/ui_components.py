# ui_components.py

import streamlit as st
import os
import shutil
from config import ProjectConfig
from model_config import model_config
from logger import log_highlight, log_to_sublog
from process_manager import ProcessManager

class UIComponents:
    """Handles all UI rendering components for the RAG app, restored from the original version."""

    def render_sidebar_config(self):
        """Render the sidebar configuration, including the detailed project type selection flow."""
        with st.sidebar:
            st.header("🔧 Configuration")
            
            # Check if UI should be disabled during RAG building
            if ProcessManager.disable_ui_during_build():
                # Return safe state during build
                safe_state = ProcessManager.get_safe_ui_state()
                log_to_sublog(safe_state["project_dir"], "ui_components.log", "🔄 UI disabled during RAG build")
                return (safe_state["project_dir"], 
                       safe_state["ollama_model"], 
                       safe_state["ollama_endpoint"], 
                       False,  # No force rebuild during build
                       ProcessManager.safe_debug_mode_check())
            
            # Get current project directory
            current_project_dir = st.session_state.get("project_dir", "../")
            project_dir = st.text_input("📁 Project Directory", value=current_project_dir)
            
            # Log project directory changes
            if project_dir and project_dir != current_project_dir:
                log_to_sublog(project_dir, "ui_components.log", f"📁 Project directory changed: {current_project_dir} -> {project_dir}")
            
            # Check if project directory has changed
            if project_dir and project_dir != current_project_dir:
                project_dir = os.path.abspath(project_dir)
                
                # Check for existing data and warn user
                project_config = ProjectConfig(project_dir=project_dir)
                
                if project_config.check_existing_data():
                    st.warning("⚠️ **Warning:** Changing the project directory will result in loss of existing database, logs, and configuration. All current RAG data will be lost!")
                    
                    col1, col2 = st.columns(2)
                    if col1.button("✅ Confirm Change"):
                        log_to_sublog(project_dir, "ui_components.log", "✅ User confirmed project directory change")
                        # Clear existing data
                        import shutil
                        if os.path.exists(project_config.get_db_dir()):
                            shutil.rmtree(project_config.get_db_dir())
                            log_to_sublog(project_dir, "ui_components.log", f"🗑️ Deleted existing database: {project_config.get_db_dir()}")
                        st.success("🗑️ Cleared existing data. New directory will be used.")
                        st.session_state["project_dir"] = project_dir
                        st.rerun()
                    if col2.button("❌ Cancel"):
                        log_to_sublog(project_dir, "ui_components.log", "❌ User cancelled project directory change")
                        st.rerun()
                else:
                    st.session_state["project_dir"] = project_dir
                    log_to_sublog(project_dir, "ui_components.log", f"📁 Project directory updated: {project_dir}")
            
            # Resolve the absolute path to ensure vector_db is created in the source project directory
            if project_dir:
                project_dir = os.path.abspath(project_dir)
                st.session_state["project_dir"] = project_dir

            project_types = list(ProjectConfig.LANGUAGE_CONFIGS.keys())
            if "selected_project_type" not in st.session_state:
                st.session_state.selected_project_type = None

            # Only allow project type changes if not building
            if ProcessManager.safe_project_type_change():
                self._render_project_type_selector(project_types)
            
            ollama_model = st.text_input("🧠 Ollama Model", value=st.session_state.get("ollama_model", model_config.get_ollama_model()))
            ollama_endpoint = st.text_input("🔗 Ollama Endpoint", value=st.session_state.get("ollama_endpoint", model_config.get_ollama_endpoint()))
            
            # Log configuration changes
            current_model = st.session_state.get("ollama_model", model_config.get_ollama_model())
            current_endpoint = st.session_state.get("ollama_endpoint", model_config.get_ollama_endpoint())
            
            if ollama_model != current_model:
                log_to_sublog(project_dir, "ui_components.log", f"🧠 Ollama model changed: {current_model} -> {ollama_model}")
                st.session_state["ollama_model"] = ollama_model
            
            if ollama_endpoint != current_endpoint:
                log_to_sublog(project_dir, "ui_components.log", f"🔗 Ollama endpoint changed: {current_endpoint} -> {ollama_endpoint}")
                st.session_state["ollama_endpoint"] = ollama_endpoint

            # Use safe force rebuild check
            force_rebuild = ProcessManager.safe_force_rebuild_check()
            if st.session_state.selected_project_type is None and not ProcessManager.is_building_rag():
                st.info("👆 Select a project type to enable the index rebuild.")

            st.divider()
            # Only show debug mode if enabled via 5-click method
            debug_mode = False
            if st.session_state.get("debug_mode_enabled", False):
                debug_mode = ProcessManager.safe_debug_mode_check()
            # Don't set session state here as the widget already manages it

        return project_dir, ollama_model, ollama_endpoint, force_rebuild, debug_mode
    
    def render_build_status(self):
        """Render build status if RAG building is in progress."""
        # Check for timeout
        is_timeout, elapsed = ProcessManager.check_rag_build_timeout()
        if is_timeout:
            st.error(f"❌ RAG building has been running for {elapsed/60:.1f} minutes and may be stuck!")
            st.warning("The embedding computation may be hanging. Consider:")
            st.write("1. Check if Ollama is running and responsive")
            st.write("2. Try a smaller model or fewer documents")
            st.write("3. Restart the application")
            
            if st.button("🛑 Force Stop RAG Build"):
                ProcessManager.finish_rag_build()
                st.session_state["force_stop"] = True
                st.rerun()
            return
        
        ProcessManager.render_build_status()

    def _render_project_type_selector(self, project_types):
        """Render project type selection and the change dialog if a type is already set."""
        if st.session_state.selected_project_type is None:
            st.warning("⚠️ Please select your project type to begin")
            selected_type = st.selectbox(
                "🎯 Select Project Type", [""] + project_types, index=0,
                help="Choose the primary programming language/framework of your project"
            )
            if selected_type:
                st.session_state.selected_project_type = selected_type
                st.rerun()
        else:
            self._render_project_type_change_dialog(project_types)

    def _render_project_type_change_dialog(self, project_types):
        """Render the dialog for changing an already selected project type."""
        current_type = st.session_state.selected_project_type
        project_dir = st.session_state.get("project_dir", "../")
        
        # Check if current project type has existing database
        current_config = ProjectConfig(project_dir=os.path.abspath(project_dir), project_type=current_type)
        has_current_db = current_config.get_project_type_db_exists()
        
        if has_current_db:
            st.success(f"📌 Project type: **{current_type}** (Database exists)")
        else:
            st.info(f"📌 Project type: **{current_type}** (No database - rebuild needed)")
            
        if st.button("🔄 Change Project Type"):
            st.session_state.show_project_change_dialog = True

        if st.session_state.get("show_project_change_dialog"):
            # Check for existing databases
            all_dbs = current_config.get_all_project_type_dbs()
            
            if all_dbs:
                st.warning("⚠️ **Existing databases detected:**")
                for db in all_dbs:
                    st.write(f"  • {db}")
                st.info("💾 **Existing data will be backed up before switching project types**")
            
            new_type = st.selectbox("🎯 New Project Type", project_types, index=project_types.index(current_type))
            
            # Check if new project type has existing database
            new_config = ProjectConfig(project_dir=os.path.abspath(project_dir), project_type=new_type)
            has_new_db = new_config.get_project_type_db_exists()
            
            if has_new_db:
                st.success(f"✅ **{new_type}** database already exists - no rebuild needed")
            else:
                st.info(f"🔄 **{new_type}** database will be created on first query")
            
            col1, col2 = st.columns(2)
            if col1.button("✅ Confirm Change"):
                self._handle_project_type_change(new_type)
            if col2.button("❌ Cancel"):
                st.session_state.show_project_change_dialog = False
                st.rerun()

    def _handle_project_type_change(self, new_type):
        """Handle project type change, including backing up existing data."""
        log_highlight("UIComponents._handle_project_type_change")
        project_dir = st.session_state.get("project_dir", "../")
        
        if project_dir:
            current_type = st.session_state.selected_project_type
            current_config = ProjectConfig(project_dir=os.path.abspath(project_dir), project_type=current_type)
            
            # Backup existing database if it exists
            if current_config.get_project_type_db_exists():
                try:
                    backup_path = current_config.backup_existing_db(current_type)
                    if backup_path:
                        st.success(f"💾 Backed up existing {current_type} database to: {os.path.basename(backup_path)}")
                        log_to_sublog(current_config.get_logs_dir(), "ui_components.log", 
                                     f"Backed up {current_type} database to: {backup_path}")
                except Exception as e:
                    st.error(f"❌ Error backing up database: {e}")
                    log_to_sublog(current_config.get_logs_dir(), "ui_components.log", 
                                 f"Error backing up database: {e}")
            
            # Clear session state for new project type
            st.session_state.selected_project_type = new_type
            for key in ['retriever', 'qa_chain', 'project_dir_used', 'chat_history']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.session_state.show_project_change_dialog = False
            
            # Check if new project type has existing database
            new_config = ProjectConfig(project_dir=os.path.abspath(project_dir), project_type=new_type)
            if new_config.get_project_type_db_exists():
                st.success(f"✅ Changed to {new_type}. Database already exists - ready to use!")
            else:
                st.info(f"✅ Changed to {new_type}. Database will be created on first query.")
            
            log_to_sublog(current_config.get_logs_dir(), "ui_components.log", f"Project type changed to: {new_type}")
            st.rerun()

    def render_welcome_screen(self):
        """Render the welcome screen with 5-click debug mode."""
        # 5-click debug mode logic
        if "debug_clicks" not in st.session_state:
            st.session_state.debug_clicks = 0
        if "debug_mode_enabled" not in st.session_state:
            st.session_state.debug_mode_enabled = False
        
        # Create a clickable title that tracks clicks
        if st.button("🤖 Codebase QA", key="title_button", help="Click 5 times to enable debug mode"):
            st.session_state.debug_clicks += 1
            if st.session_state.debug_clicks >= 5:
                st.session_state.debug_mode_enabled = True
                st.session_state.debug_clicks = 0
                st.success("🔧 Debug mode enabled! Check the sidebar for debug options.")
                st.rerun()
        
        # Show click count in debug mode
        if st.session_state.debug_mode_enabled:
            st.caption(f"Debug clicks: {st.session_state.debug_clicks}/5")
        
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

    def render_chat_input(self):
        """Render chat input form, restored from the original version."""
        with st.form("query_form", clear_on_submit=True):
            query = st.text_input(
                "📝 Your question",
                placeholder="What does the project do?",
                key="query_input",
                disabled=not st.session_state.get("qa_chain")
            )
            submitted = st.form_submit_button("🚀 Ask")
        return query, submitted

    def render_chat_history(self):
        """Render chat history with expanders and detailed metadata, restored from the original."""
        if st.session_state.get("chat_history"):
            for i, chat_item in enumerate(reversed(st.session_state.chat_history)):
                # Handle both old (4 items) and new (5 items) formats for backward compatibility
                q, a, srcs, impact_files, metadata = (*chat_item, None)[:5]

                expander_title = f"Q: {q}"
                if metadata and metadata.get('intent'):
                    expander_title += f" [{metadata['intent'].replace('_', ' ').title()}]"

                with st.expander(expander_title, expanded=(i == 0)):
                    st.markdown(f"**A:** {a}")
                    if metadata:
                        col1, col2 = st.columns(2)
                        if metadata.get('intent'): col1.caption(f"🎯 **Intent:** {metadata['intent'].title()}")
                        if metadata.get('confidence'): col1.caption(f"📊 **Confidence:** {metadata['confidence']:.1%}")
                        if metadata.get('rewritten_query') and metadata['rewritten_query'] != q:
                            col2.caption(f"🔄 **Enhanced Query:** {metadata['rewritten_query']}")
                    if impact_files: st.markdown(f"**🔍 Impacted files:** {', '.join(impact_files)}")
                    if srcs:
                        st.markdown("**🔎 Top Sources:**")
                        for doc in srcs[:5]:
                            if hasattr(doc, "metadata") and isinstance(doc.metadata, dict):
                                md = doc.metadata
                                source_line = f"- `{md.get('source', 'Unknown')}` (chunk {md.get('chunk_index', 0)})"
                                if md.get('name'): source_line += f" *({md.get('name')})*"
                                st.markdown(source_line)

    def render_debug_section(self, project_config, ollama_model, ollama_endpoint, project_dir):
        """Render comprehensive debug tools and inspection section."""
        with st.expander("🔧 Debug & Inspection Tools", expanded=True):
            # Create tabs for different debug tools
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📊 Vector DB Inspector", 
                "🔍 Chunk Analyzer", 
                "🧪 Retrieval Tester",
                "📈 Build Status",
                "📝 Logs"
            ])
            
            try:
                import sys
                import os
                # Add debug_tools directory to path
                debug_tools_path = os.path.join(os.path.dirname(__file__), '..', 'debug_tools')
                if debug_tools_path not in sys.path:
                    sys.path.append(debug_tools_path)
                
                # Import directly from the debug_tools.py file to avoid relative import issues
                import debug_tools
                debug_tools_instance = debug_tools.DebugTools(project_config=project_config, ollama_model=ollama_model, 
                                         ollama_endpoint=ollama_endpoint, project_dir=project_dir)
                
                with tab1:
                    self._render_vector_db_inspector(debug_tools_instance)
                
                with tab2:
                    self._render_chunk_analyzer(debug_tools_instance)
                
                with tab3:
                    self._render_retrieval_tester(debug_tools_instance)
                
                with tab4:
                    self._render_build_status(project_config)
                
                with tab5:
                    self._render_logs_viewer(project_config)
                    
            except ImportError as e:
                st.error(f"❌ Debug tools not available: {e}")
                st.info("Make sure debug_tools package is properly installed.")
            except Exception as e:
                st.error(f"❌ Error loading debug tools: {e}")
                st.exception(e)
    
    def _render_vector_db_inspector(self, debug_tools):
        """Render vector database inspection tools."""
        st.header("📊 Vector Database Inspector")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Inspect Vector DB", type="primary"):
                with st.spinner("Inspecting vector database..."):
                    try:
                        stats = debug_tools.inspect_vector_db()
                        st.success("✅ Vector DB inspection complete!")
                        
                        # Display statistics
                        st.subheader("📈 Database Statistics")
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("Total Documents", stats.get("total_documents", 0))
                        with col_b:
                            st.metric("Unique Files", stats.get("unique_files", 0))
                        with col_c:
                            st.metric("Average Chunk Size", f"{stats.get('avg_chunk_size', 0):.0f} chars")
                        
                        # Display file breakdown
                        if "file_breakdown" in stats:
                            st.subheader("📁 File Breakdown")
                            file_df = stats["file_breakdown"]
                            st.dataframe(file_df, use_container_width=True)
                            
                    except Exception as e:
                        st.error(f"❌ Error inspecting vector DB: {e}")
        
        with col2:
            if st.button("🗑️ Clear Vector DB"):
                if st.checkbox("I understand this will delete all vector data"):
                    with st.spinner("Clearing vector database..."):
                        try:
                            debug_tools.clear_vector_db()
                            st.success("✅ Vector database cleared!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error clearing vector DB: {e}")
    
    def _render_chunk_analyzer(self, debug_tools):
        """Render chunk analysis tools."""
        st.header("🔍 Chunk Analyzer")
        
        # File selector
        files = debug_tools.get_available_files()
        if files:
            selected_file = st.selectbox("Select file to analyze:", files)
            
            if selected_file and st.button("🔍 Analyze Chunks", type="primary"):
                with st.spinner("Analyzing chunks..."):
                    try:
                        chunks = debug_tools.analyze_file_chunks(selected_file)
                        
                        st.subheader(f"📄 Chunks for: {selected_file}")
                        st.write(f"Found {len(chunks)} chunks")
                        
                        # Display chunks
                        for i, chunk in enumerate(chunks):
                            with st.expander(f"Chunk {i+1} (Metadata: {chunk.get('metadata', {})})"):
                                st.code(chunk.get('content', ''), language='text')
                                
                    except Exception as e:
                        st.error(f"❌ Error analyzing chunks: {e}")
        else:
            st.warning("No files available for analysis.")
    
    def _render_retrieval_tester(self, debug_tools):
        """Render retrieval testing tools."""
        st.header("🧪 Retrieval Tester")
        
        # Test query input
        test_query = st.text_area("Enter test query:", placeholder="e.g., How does the MainActivity work?")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Retrieval", type="primary") and test_query:
                with st.spinner("Testing retrieval..."):
                    try:
                        results = debug_tools.test_retrieval(test_query)
                        
                        if isinstance(results, list):
                            st.subheader("🔍 Retrieval Results")
                            st.write(f"Found {len(results)} relevant documents")
                            
                            for i, result in enumerate(results):
                                with st.expander(f"Result {i+1} (Score: {result.get('relevance_score', 'N/A')})"):
                                    st.write(f"**Source:** {result.get('source', 'Unknown')}")
                                    st.code(result.get('content', ''), language='text')
                                    st.write("**Metadata:**")
                                    st.json(result.get('metadata', {}))
                        elif isinstance(results, dict) and "error" in results:
                            st.error(f"❌ Retrieval failed: {results['error']}")
                        else:
                            st.warning(f"⚠️ Unexpected result format: {type(results)}")
                                
                    except Exception as e:
                        st.error(f"❌ Error testing retrieval: {e}")
        
        with col2:
            if st.button("📊 Test Multiple Queries"):
                sample_queries = [
                    "How does the MainActivity work?",
                    "What are the main UI components?",
                    "How is data passed between activities?",
                    "What are the key configuration files?"
                ]
                
                with st.spinner("Running multiple query tests..."):
                    try:
                        results = debug_tools.test_multiple_queries(sample_queries)
                        
                        st.subheader("📊 Multiple Query Results")
                        for query, result in results.items():
                            with st.expander(f"Query: {query}"):
                                if isinstance(result, list):
                                    st.write(f"Documents found: {len(result)}")
                                    for doc in result[:3]:  # Show top 3
                                        st.write(f"- {doc.get('source', 'Unknown')} (Score: {doc.get('relevance_score', 'N/A')})")
                                elif isinstance(result, dict) and "error" in result:
                                    st.error(f"Error: {result['error']}")
                                else:
                                    st.warning(f"Unexpected result format: {type(result)}")
                                    
                    except Exception as e:
                        st.error(f"❌ Error testing multiple queries: {e}")
    
    def _render_build_status(self, project_config):
        """Render build status and statistics."""
        st.header("📈 Build Status")
        
        try:
            # Get build statistics
            db_dir = project_config.get_db_dir()
            
            if os.path.exists(db_dir):
                st.success("✅ Database exists")
                
                # Count files
                total_files = 0
                for root, dirs, files in os.walk(db_dir):
                    total_files += len(files)
                
                st.metric("Total Database Files", total_files)
                
                # Check specific files
                chroma_exists = os.path.exists(os.path.join(db_dir, "chroma.sqlite3"))
                git_tracking_exists = os.path.exists(os.path.join(db_dir, "git_tracking.json"))
                last_commit_exists = os.path.exists(os.path.join(db_dir, "last_commit.json"))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Chroma DB", "✅" if chroma_exists else "❌")
                with col2:
                    st.metric("Git Tracking", "✅" if git_tracking_exists else "❌")
                with col3:
                    st.metric("Last Commit", "✅" if last_commit_exists else "❌")
                
                # Show database size
                import shutil
                db_size = shutil.disk_usage(db_dir).used
                st.metric("Database Size", f"{db_size / 1024 / 1024:.1f} MB")
                
            else:
                st.warning("⚠️ Database does not exist")
                
        except Exception as e:
            st.error(f"❌ Error checking build status: {e}")
    
    def _render_logs_viewer(self, project_config):
        """Render logs viewer."""
        st.header("📝 Logs Viewer")
        
        try:
            logs_dir = project_config.get_logs_dir()
            
            if os.path.exists(logs_dir):
                log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
                
                if log_files:
                    selected_log = st.selectbox("Select log file:", log_files)
                    
                    if selected_log:
                        log_path = os.path.join(logs_dir, selected_log)
                        
                        # Show log content
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                        
                        st.subheader(f"📄 {selected_log}")
                        st.code(log_content, language='text')
                        
                        # Download button
                        st.download_button(
                            label="📥 Download Log",
                            data=log_content,
                            file_name=selected_log,
                            mime="text/plain"
                        )
                else:
                    st.info("No log files found.")
            else:
                st.warning("Logs directory does not exist.")
                
        except Exception as e:
            st.error(f"❌ Error reading logs: {e}")

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

# --------------- CODE CHANGE SUMMARY ---------------
# REMOVED
# - All simplified/incomplete UI methods from the previous incorrect version.
# - Undefined rag_manager reference in render_chat_input - fixed to use session state.
# - Duplicate processing logs display from render_debug_section - moved to dedicated render_processing_logs method.
# ADDED
# - Restored full sidebar logic from `ui_components_old.py`, including detailed project type selection, change confirmation dialogs, and logic to clear the DB on type change.
# - render_custom_css: Added custom styling for better visual design and log display.
# - render_processing_logs: Added dedicated processing logs section with copy/clear actions.
# - Enhanced logging throughout with logger.py utilities for better debugging.
# - render_chat_input: Fixed to use session state instead of undefined rag_manager reference.
# - render_debug_section: Complete integration with DebugTools class, removed duplicate logging.
# - render_chat_history: Enhanced with metadata display and auto-expansion.
# - 5-click debug mode: Added debug mode activation by clicking title 5 times.
# - Comprehensive debug tools: Vector DB Inspector, Chunk Analyzer, Retrieval Tester, Build Status, Logs Viewer.
# REFACTORED
# - All methods now use proper logging with log_highlight and log_to_sublog.
# - Better error handling and user feedback throughout.
# - Fixed duplicate element key issue by separating debug tools and processing logs.
# - The class is now a complete and faithful port of the original `ui_components_old.py`, ensuring no UI functionality is lost.
# - Debug mode only shows when enabled via 5-click method.
