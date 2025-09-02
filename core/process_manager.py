"""
Process state manager to prevent UI interference during critical operations.
"""

import streamlit as st
from logger import log_highlight, log_to_sublog
import time

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
        st.session_state["rag_build_start_time"] = time.time()
        log_highlight("ProcessManager: RAG build started")
        
        # Log the build start with project details
        project_dir = st.session_state.get("project_dir", "unknown")
        project_type = st.session_state.get("selected_project_type", "unknown")
        log_to_sublog(project_dir, "process_manager.log", f"=== RAG BUILD STARTED ===")
        log_to_sublog(project_dir, "process_manager.log", f"Project directory: {project_dir}")
        log_to_sublog(project_dir, "process_manager.log", f"Project type: {project_type}")
        log_to_sublog(project_dir, "process_manager.log", f"Build start time: {time.time()}")
    
    @staticmethod
    def finish_rag_build():
        """Mark RAG building as finished."""
        st.session_state["rag_building_in_progress"] = False
        if "rag_build_start_time" in st.session_state:
            del st.session_state["rag_build_start_time"]
        log_highlight("ProcessManager: RAG build finished")
        
        # Log the build completion
        project_dir = st.session_state.get("project_dir", "unknown")
        log_to_sublog(project_dir, "process_manager.log", f"=== RAG BUILD FINISHED ===")
        log_to_sublog(project_dir, "process_manager.log", f"Build end time: {time.time()}")
    
    @staticmethod
    def check_rag_build_timeout():
        """Check if RAG building has been running too long."""
        if ProcessManager.is_building_rag():
            start_time = st.session_state.get("rag_build_start_time")
            if start_time:
                elapsed = time.time() - start_time
                timeout_minutes = 15  # 15 minute timeout for entire RAG build
                if elapsed > (timeout_minutes * 60):
                    project_dir = st.session_state.get("project_dir", "unknown")
                    log_to_sublog(project_dir, "process_manager.log", f"⚠️ RAG BUILD TIMEOUT: {elapsed/60:.1f} minutes")
                    return True, elapsed
        return False, 0
    
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
            debug_mode = st.checkbox("🐞 Enable Debug Mode", value=st.session_state.get("debug_mode", False), 
                             key="debug_mode", help="Show debugging tools and detailed logs")
            
            # Log debug mode changes
            project_dir = st.session_state.get("project_dir", "unknown")
            if debug_mode != st.session_state.get("debug_mode", False):
                log_to_sublog(project_dir, "process_manager.log", f"🔧 Debug mode changed to: {debug_mode}")
            
            return debug_mode
    
    @staticmethod
    def safe_force_rebuild_check():
        """Check force rebuild safely without interfering with processes."""
        project_dir = st.session_state.get("project_dir", "unknown")
        
        if ProcessManager.is_building_rag():
            # Disable force rebuild during build
            st.button("🔁 Rebuild Index", disabled=True, help="Disabled during RAG building")
            log_to_sublog(project_dir, "process_manager.log", "🔁 Rebuild button disabled (RAG building in progress)")
            return False
        else:
            # Create the button and return True if clicked
            rebuild_clicked = st.button("🔁 Rebuild Index", disabled=(st.session_state.get("selected_project_type") is None))
            
            if rebuild_clicked:
                log_to_sublog(project_dir, "process_manager.log", "=== REBUILD INDEX BUTTON CLICKED ===")
                log_to_sublog(project_dir, "process_manager.log", f"Project directory: {project_dir}")
                log_to_sublog(project_dir, "process_manager.log", f"Project type: {st.session_state.get('selected_project_type')}")
                log_to_sublog(project_dir, "process_manager.log", f"Current session state keys: {list(st.session_state.keys())}")
                
                # Clear existing RAG state to force rebuild
                cleared_keys = []
                for key in ['retriever', 'vectorstore', 'project_dir_used']:
                    if key in st.session_state:
                        del st.session_state[key]
                        cleared_keys.append(key)
                
                log_to_sublog(project_dir, "process_manager.log", f"✅ Cleared session state keys: {cleared_keys}")
                st.session_state["force_rebuild"] = True
                log_to_sublog(project_dir, "process_manager.log", "✅ Set force_rebuild flag to True")
                log_to_sublog(project_dir, "process_manager.log", "🔄 Triggering page rerun for rebuild")
                st.rerun()
            
            force_rebuild = st.session_state.get("force_rebuild", False)
            if force_rebuild:
                log_to_sublog(project_dir, "process_manager.log", f"🔁 Force rebuild flag is: {force_rebuild}")
            
            return force_rebuild
    
    @staticmethod
    def safe_project_type_change():
        """Handle project type changes safely."""
        if ProcessManager.is_building_rag():
            current_type = st.session_state.get("selected_project_type", "python")
            st.selectbox("🎯 Project Type", ["python", "javascript", "android", "ios"], 
                        index=["python", "javascript", "android", "ios"].index(current_type), 
                        disabled=True, help="Disabled during RAG building")
            return False
        else:
            return True
    
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