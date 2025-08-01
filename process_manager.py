"""
Process state manager to prevent UI interference during critical operations.
"""

import streamlit as st
from logger import log_highlight, log_to_sublog

class ProcessManager:
    """Manages critical process states to prevent UI interference."""
    
    @staticmethod
    def is_building_rag():
        """Check if RAG building is in progress."""
        return st.session_state.get("rag_building_in_progress", False)
    
    @staticmethod
    def start_rag_build():
        """Mark RAG building as started."""
        st.session_state["rag_building_in_progress"] = True
        st.session_state["rag_build_start_time"] = None
        log_highlight("ProcessManager: RAG build started")
    
    @staticmethod
    def finish_rag_build():
        """Mark RAG building as finished."""
        st.session_state["rag_building_in_progress"] = False
        if "rag_build_start_time" in st.session_state:
            del st.session_state["rag_build_start_time"]
        log_highlight("ProcessManager: RAG build finished")
    
    @staticmethod
    def get_safe_ui_state():
        """Get UI state that's safe to modify during processes."""
        return {
            "project_dir": st.session_state.get("project_dir"),
            "selected_project_type": st.session_state.get("selected_project_type"),
            "ollama_model": st.session_state.get("ollama_model", "llama3.2"),
            "ollama_endpoint": st.session_state.get("ollama_endpoint", "http://localhost:11434")
        }
    
    @staticmethod
    def disable_ui_during_build():
        """Disable UI elements that could interfere with RAG building."""
        if ProcessManager.is_building_rag():
            st.warning("🔄 **RAG Index Building in Progress**")
            st.info("UI controls are temporarily disabled to prevent process interference.")
            st.info("Please wait for the build to complete before making changes.")
            return True
        return False
    
    @staticmethod
    def safe_debug_mode_check():
        """Check debug mode safely without interfering with processes."""
        if ProcessManager.is_building_rag():
            # Show disabled checkbox during build
            previous_state = st.session_state.get("debug_mode", False)
            st.checkbox("🐞 Enable Debug Mode", value=previous_state, disabled=True, 
                       help="Disabled during RAG building")
            return previous_state
        else:
            # Allow normal debug mode control - let Streamlit manage the state
            return st.checkbox("🐞 Enable Debug Mode", value=st.session_state.get("debug_mode", False), 
                             key="debug_mode", help="Show debugging tools and detailed logs")
    
    @staticmethod
    def safe_force_rebuild_check():
        """Check force rebuild safely without interfering with processes."""
        if ProcessManager.is_building_rag():
            # Disable force rebuild during build
            st.button("🔁 Rebuild Index", disabled=True, help="Disabled during RAG building")
            return False
        else:
            return st.button("🔁 Rebuild Index", disabled=(st.session_state.get("selected_project_type") is None))
    
    @staticmethod
    def safe_project_type_change():
        """Handle project type changes safely."""
        if ProcessManager.is_building_rag():
            current_type = st.session_state.get("selected_project_type", "python")
            st.selectbox("Project Type", ["android", "python", "ios", "javascript"], 
                        index=["android", "python", "ios", "javascript"].index(current_type),
                        disabled=True, help="Disabled during RAG building")
            return False  # No change allowed
        else:
            return True  # Allow normal project type UI
    
    @staticmethod
    def render_build_status():
        """Render build status if in progress."""
        if ProcessManager.is_building_rag():
            with st.container():
                st.info("🔄 **RAG Index Building in Progress...**")
                
                # Show progress if available
                thinking_logs = st.session_state.get("thinking_logs", [])
                if thinking_logs:
                    latest_log = thinking_logs[-1] if thinking_logs else "Starting build..."
                    st.write(f"Status: {latest_log}")
                
                # Show elapsed time if available
                import time
                start_time = st.session_state.get("rag_build_start_time")
                if start_time:
                    elapsed = time.time() - start_time
                    st.write(f"Elapsed: {elapsed:.1f} seconds")
                
                st.warning("⚠️ Do not refresh the page or change settings during build")
                
                # Emergency stop button
                if st.button("🛑 Emergency Stop Build", type="secondary"):
                    ProcessManager.finish_rag_build()
                    st.session_state["emergency_stop"] = True
                    st.error("❌ Build stopped by user")
                    st.rerun()
    
    @staticmethod
    def log_process_state(project_dir, action):
        """Log process state changes."""
        state = "building" if ProcessManager.is_building_rag() else "idle"
        log_to_sublog(project_dir, "process_manager.log", f"Process state: {state}, Action: {action}")

def with_process_protection(func):
    """Decorator to protect functions from UI interference."""
    def wrapper(*args, **kwargs):
        try:
            ProcessManager.start_rag_build()
            result = func(*args, **kwargs)
            ProcessManager.finish_rag_build()
            return result
        except Exception as e:
            ProcessManager.finish_rag_build()
            raise e
    return wrapper