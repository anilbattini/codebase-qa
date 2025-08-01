# logger.py

import os
import logging
import sys
import inspect
from datetime import datetime

def setup_global_logger(log_dir="logs"):
    """Configure a global logger with file and stdout output, with file rotation per session."""
    # Ensure log_dir is an absolute path
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"rag_session_{timestamp}.log")

    logger = logging.getLogger("RAG")
    logger.setLevel(logging.DEBUG)  # always log at DEBUG level for file

    # Console handler (INFO+)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s %(message)s", datefmt="%H:%M:%S")
    ch.setFormatter(formatter)

    # File handler (DEBUG+)
    fh = logging.FileHandler(log_filename, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter("[%(levelname)s] %(asctime)s %(filename)s:%(lineno)s %(message)s")
    fh.setFormatter(file_formatter)

    # Remove old handlers to avoid duplicate logs
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.propagate = False

    logger.info(f"Logger initialized at {log_filename}")
    return logger

def get_project_log_file(project_dir, subname):
    """Get log file path, handling path resolution internally."""
    return os.path.join(_get_logs_dir(project_dir), subname)

def log_to_sublog(project_dir, subname, msg):
    """Write to sublog, handling all path resolution internally."""
    logfile = os.path.join(_get_logs_dir(project_dir), subname)
    os.makedirs(os.path.dirname(logfile), exist_ok=True)
    with open(logfile, "a", encoding="utf-8") as f:
        f.write(msg.rstrip() + "\n")

def _get_logs_dir(project_dir):
    """Internal helper to resolve logs directory consistently."""
    if not project_dir:
        project_dir = "../"
    
    # Convert to absolute path
    abs_project_dir = os.path.abspath(project_dir)
    
    # Ensure we're pointing to the source project, not the tool
    if abs_project_dir.endswith('/codebase-qa'):
        abs_project_dir = os.path.dirname(abs_project_dir)
    
    # Import ProjectConfig here to avoid circular dependency at module level
    from config import ProjectConfig 
    
    # Try to get project type from session state or environment
    project_type = None
    try:
        import streamlit as st
        if hasattr(st, 'session_state') and st.session_state.get("selected_project_type"):
            project_type = st.session_state.selected_project_type
    except:
        pass
    
    # If no project type from session, try to auto-detect
    if not project_type:
        temp_config = ProjectConfig(project_dir=abs_project_dir)
        project_type = temp_config.project_type
    
    # Only create logs directory if project type is selected and not unknown
    if project_type and project_type != "unknown":
        logs_dir = os.path.join(abs_project_dir, f"codebase-qa_{project_type}", "logs")
        # Ensure the directory exists
        os.makedirs(logs_dir, exist_ok=True)
        return logs_dir
    else:
        # Fallback to a temporary location if no project type selected
        temp_dir = os.path.join(abs_project_dir, "temp_logs")
        os.makedirs(temp_dir, exist_ok=True)
        return temp_dir

def log_highlight(msg, logger=None):
    frame = inspect.currentframe().f_back
    file = os.path.basename(frame.f_code.co_filename)
    lineno = frame.f_lineno
    highlight_msg = f"\n###### {msg} (file {file}, {lineno}) ######\n"
    if logger:
        logger.info(highlight_msg)
    else:
        print(highlight_msg)

# --------------- CODE CHANGE SUMMARY ---------------
# ADDED
# - get_project_log_file (lines 28-32): always write sublogs to per-project log folder, bug-free.
# - log_to_sublog (lines 34-38): simple DRY-style log append for any event/context/block throughout project.
# - log_highlight (lines 40-49): standard highlight log to mark major processing, usable anywhere.
# - All logging helpers now live here (import everywhere else).
# REMOVED
# - N/A (brand new logging centralization module).
