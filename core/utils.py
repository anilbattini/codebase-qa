"""
utils.py

Utility functions used across the codebase to avoid circular imports.
"""

import streamlit as st

def update_logs(log_placeholder):
    """Update the log display in the UI."""
    logs = st.session_state.get('thinking_logs', [])
    if logs:
        recent_logs = logs[-20:]
        formatted_logs = [f"[{i+1:02d}] {log}" for i, log in enumerate(recent_logs)]
        log_text = "\n".join(formatted_logs)
        with log_placeholder.container():
            st.text_area(
                "Live Processing Status",
                value=log_text,
                height=200,
                disabled=True,
                key=f"live_logs_{len(logs)}", label_visibility="collapsed"
            )

def get_impact(file_name: str, project_dir: str = None) -> list:
    """
    Get impact analysis for a file.
    This is a simplified version - in the full implementation, this would analyze dependencies.
    """
    # For now, return an empty list to avoid complex dependency analysis
    # This can be enhanced later with proper impact analysis
    return []

