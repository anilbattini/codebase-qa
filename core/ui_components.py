# ui_components.py

import streamlit as st
import os
from config.config import ProjectConfig
from config.model_config import model_config
from logger import get_project_log_file, log_highlight, log_to_sublog, rate_and_copy
from process_manager import ProcessManager

class UIComponents:
    """Handles all UI rendering components for the RAG app, restored from the original version."""
    
    # Add this method to UIComponents class:

    def render_feature_toggles_sidebar(self, project_dir: str = "."):
        """Render feature toggle status in sidebar for admin users."""
        from config.feature_toggle_manager import FeatureToggleManager
        
        if st.sidebar.expander("🎛️ Feature Toggles", expanded=False):
            try:
                current_version = FeatureToggleManager.app_version()
                st.sidebar.write(f"**App Version:** `{current_version}`")
                
                feature_states = FeatureToggleManager.get_all_feature_states(project_dir)
                
                for feature_name, state in feature_states.items():
                    config = state["config"]
                    enabled = state["enabled"]
                    
                    # Status indicator
                    status_icon = "🟢" if enabled else "🔴"
                    st.sidebar.write(f"{status_icon} **{feature_name}**")
                    st.sidebar.write(f"   Enabled: {config.get('enabled', False)}")
                    st.sidebar.write(f"   Min Version: {config.get('minVersion', 'N/A')}")
                    st.sidebar.write(f"   Status: {'ACTIVE' if enabled else 'DISABLED'}")
                    
                    if config.get("description"):
                        st.sidebar.caption(config["description"])
                    st.sidebar.write("---")
                    
            except Exception as e:
                st.sidebar.error(f"Error loading toggles: {e}")

    
    # In ui_components.py - UPDATED with concurrency safety
    def _collect_feedback_ui(self, log_path: str, target_dir: str):
        """
        Safe feedback collection that doesn't disrupt ongoing operations.
        """
        feedback_key = f"feedback_state_{log_path}"
        
        # Initialize feedback state if not exists
        if feedback_key not in st.session_state:
            st.session_state[feedback_key] = {
                'show_dialog': False,
                'submitted': False,
                'score': 8,
                'remark': ''
            }
        
        feedback_state = st.session_state[feedback_key]
        
        if feedback_state['show_dialog'] and not feedback_state['submitted']:
            with st.container():
                st.markdown("### 📝 Provide Feedback")
                
                # Use the stored values to maintain state
                score = st.slider(
                    "Score (1 = bad, 10 = great)", 
                    1, 10, feedback_state.get('score', 8),
                    key=f"score_slider_{log_path}"
                )
                
                remark = st.text_area(
                    "Remarks", 
                    value=feedback_state.get('remark', ""),
                    height=80,
                    key=f"remark_area_{log_path}"
                )
                
                # Update state without triggering rerun
                st.session_state[feedback_key]['score'] = score
                st.session_state[feedback_key]['remark'] = remark
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Submit", key=f"submit_btn_{log_path}"):
                        if rate_and_copy(log_path, target_dir, score, remark):
                            st.session_state.rated_logs.add(log_path)
                            st.session_state[feedback_key]['submitted'] = True
                            st.session_state[feedback_key]['show_dialog'] = False
                            st.success("✅ Feedback saved!")
                            # NO st.rerun() here - let natural refresh handle it
                        else:
                            st.error("❌ Failed to save feedback.")
                
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_btn_{log_path}"):
                        st.session_state[feedback_key]['show_dialog'] = False
                        # NO st.rerun() here

    
    # Render "Answer Detail Level"
    def render_debug_controls(self, debug_mode: bool) -> str:
        """
        Shows 'Answer Detail Level' dropdown (simple | moderate | elaborate)
        – visible only when debug_mode is True.
        Returns the selected level (defaults to 'moderate').
        """
        if not debug_mode:
            return "moderate"
        with st.sidebar:
            st.markdown("### 📝 Answer Verbosity")
            return st.selectbox(
                "Detail level",
                options=["simple", "moderate", "elaborate"],
                index=1,                      # default == moderate
                help="Controls how verbose the assistant replies"
        )

    def render_sidebar_config(self):
        """Render the sidebar configuration with locked Ollama fields when provider is Ollama."""
        
        with st.sidebar:
            st.header("🔧 Configuration")

            # Check if UI should be disabled during RAG building
            if ProcessManager.disable_ui_during_build():
                safe_state = ProcessManager.get_safe_ui_state()
                log_to_sublog(safe_state["project_dir"], "ui_components.log", "🔄 UI disabled during RAG build")
                return (safe_state["project_dir"], safe_state["ollama_model"], 
                    safe_state["ollama_endpoint"], False, ProcessManager.safe_debug_mode_check(), False)

            # Get current project directory
            current_project_dir = st.session_state.get("project_dir", "../")
            project_dir = st.text_input("📁 Project Directory", value=current_project_dir)

            # Handle project directory changes (existing logic...)
            if project_dir and project_dir != current_project_dir:
                # ... existing project directory change logic ...
                pass

            # Resolve absolute path
            if project_dir:
                project_dir = os.path.abspath(project_dir)
                st.session_state["project_dir"] = project_dir

            # Project type selection
            project_types = list(ProjectConfig.LANGUAGE_CONFIGS.keys())
            if "selected_project_type" not in st.session_state:
                st.session_state.selected_project_type = None

            # Only allow project type changes if not building
            if ProcessManager.safe_project_type_change():
                self._render_project_type_selector(project_types)

            # Provider selection - CRITICAL: Check both conditions before proceeding
            provider_selected = self._render_provider_selection()
            
            # Only return ready status if BOTH project type AND provider are selected
            project_type_selected = st.session_state.selected_project_type is not None
            both_selected = project_type_selected and provider_selected
            
            if not both_selected:
                if not project_type_selected and not provider_selected:
                    st.warning("⚠️ Please select both project type and provider to continue")
                elif not project_type_selected:
                    st.warning("⚠️ Please select a project type to continue")
                elif not provider_selected:
                    st.warning("⚠️ Please select a provider to continue")
                
                # Return default values but mark as not ready
                return (project_dir, model_config.get_ollama_model(), 
                    model_config.get_ollama_endpoint(), False, False, False)

            # Both selected - proceed with normal flow
            force_rebuild = ProcessManager.safe_force_rebuild_check()
            debug_mode = st.session_state.get("debug_mode_enabled", False) and ProcessManager.safe_debug_mode_check()
            
            detail_level = self.render_debug_controls(debug_mode)
            st.session_state["detail_level"] = detail_level      # persist

            return (project_dir, model_config.get_ollama_model(), 
                model_config.get_ollama_endpoint(), force_rebuild, debug_mode, True)

    def _render_provider_selection(self):
        """Render provider selection with locked Ollama fields."""
        
        provider_options = ["Choose Provider...", "Ollama (Local)", "Cloud (OpenAI Compatible)"]
        provider_choice = st.selectbox("🔗 Provider", provider_options, key="provider_selection")
        
        if provider_choice == "Choose Provider...":
            st.info("👆 Please select a provider to continue")
            return False
        
        elif provider_choice == "Ollama (Local)":
            model_config.set_provider("ollama")
            log_to_sublog(st.session_state.get("project_dir", "."), "ui_components.log", "Provider set to Ollama (Local)")
            
            # 🔒 LOCKED OLLAMA FIELDS - Issue 1 Fix
            st.text_input(
                "🧠 Ollama Model",
                value=model_config.get_ollama_model(),
                disabled=True,  # 🔒 LOCKED for consistency
                help="Fixed model for consistency across builds"
            )
            
            st.text_input(
                "🔗 Ollama Endpoint", 
                value=model_config.get_ollama_endpoint(),
                disabled=True,  # 🔒 LOCKED for consistency
                help="Standard local Ollama endpoint"
            )
            
            return True
            
        elif provider_choice == "Cloud (OpenAI Compatible)":
            model_config.set_provider("cloud")
            log_to_sublog(st.session_state.get("project_dir", "."), "ui_components.log", "Provider set to Cloud (OpenAI Compatible)")
            
            # Cloud endpoint selection (editable)
            cloud_env = os.getenv("CLOUD_ENDPOINT", None)
            endpoint_options = [
                f"From Environment" + (f" ({cloud_env})" if cloud_env else " (Not Set)"),
                "Custom Endpoint"
            ]
            endpoint_choice = st.selectbox("🌐 Cloud Endpoint", endpoint_options, key="cloud_endpoint_selection")
            
            if endpoint_choice == "Custom Endpoint":
                custom_endpoint = st.text_input("Enter Cloud Endpoint URL", 
                                            placeholder="https://api.openai.com/v1",
                                            key="custom_cloud_endpoint")
                if custom_endpoint:
                    model_config.set_cloud_endpoint(custom_endpoint)
            else:
                model_config.set_cloud_endpoint(None)
                if not cloud_env:
                    st.warning("⚠️ CLOUD_ENDPOINT environment variable not set!")

            # API key status
            api_key = model_config.get_cloud_api_key()
            if api_key:
                st.success(f"✅ Cloud API key found (sk-...{api_key[-4:] if len(api_key) > 4 else '***'})")
            else:
                st.error("❌ CLOUD_API_KEY environment variable not set!")

            st.info(f"🤖 Using model: **{model_config.get_cloud_model()}**")
            
            # Still need Ollama for embeddings (editable for cloud)
            st.subheader("🔗 Local Ollama (for embeddings)")
            ollama_model = st.text_input("🧠 Ollama Model (for embeddings)",
                                        value=model_config.get_ollama_model())
            ollama_endpoint = st.text_input("🔗 Ollama Endpoint (for embeddings)",
                                        value=model_config.get_ollama_endpoint())
            
            # Update model config if changed
            if ollama_model != model_config.get_ollama_model():
                model_config.set_ollama_model(ollama_model)
            if ollama_endpoint != model_config.get_ollama_endpoint():
                model_config.set_ollama_endpoint(ollama_endpoint)
                
            return True
        
        return False


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
            for key in ['retriever', 'vectorstore', 'project_dir_used', 'chat_history']:
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
                disabled=not st.session_state.get("vectorstore")
            )
            submitted = st.form_submit_button("🚀 Ask")
        return query, submitted

    # Updated render_chat_history method - SAFE button handling
    def render_chat_history(self, project_dir):
        """Render chat history with non-disruptive feedback buttons."""
        if st.session_state.get("chat_history"):
            for i, chat_item in enumerate(reversed(st.session_state.chat_history)):
                q, a, srcs, impact_files, metadata = (*chat_item, None)[:5]
                
                expander_title = f"Q: {q}"
                if metadata and metadata.get('intent'):
                    expander_title += f" [{metadata['intent'].replace('_', ' ').title()}]"

                with st.expander(expander_title, expanded=False):
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
                    # Rating buttons inside history (debug only)
                    # UPDATED: Safe feedback buttons
                    debug_mode = st.session_state.get("debug_mode_enabled", False)
                    log_path = (metadata or {}).get("log_path")
                    
                    if debug_mode and log_path and log_path not in st.session_state.rated_logs:
                        feedback_key = f"feedback_state_{log_path}"
                        
                        # Initialize if needed
                        if feedback_key not in st.session_state:
                            st.session_state[feedback_key] = {'show_dialog': False, 'submitted': False}
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            if st.button("👍 Like", key=f"like_btn_{i}"):
                                st.session_state[feedback_key]['show_dialog'] = True
                                st.session_state[f"target_dir_{log_path}"] = get_project_log_file(project_dir, "liked")
                                # NO st.rerun() - let component refresh naturally
                        
                        with col2:
                            if st.button("👎 Dislike", key=f"dislike_btn_{i}"):
                                st.session_state[feedback_key]['show_dialog'] = True
                                st.session_state[f"target_dir_{log_path}"] = get_project_log_file(project_dir, "disliked")
                                # NO st.rerun() - let component refresh naturally
                        
                        # Show feedback dialog if requested
                        target_dir = st.session_state.get(f"target_dir_{log_path}")
                        if st.session_state[feedback_key]['show_dialog'] and target_dir:
                            self._collect_feedback_ui(log_path, target_dir)
                    
                    elif debug_mode and log_path and log_path in st.session_state.rated_logs:
                        st.caption("✅ Feedback recorded")


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

