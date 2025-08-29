# logger.py

from datetime import datetime
import os
import logging
import sys
import inspect
import shutil, os, re

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
        project_dir = "../../"
    
    # Convert to absolute path
    abs_project_dir = os.path.abspath(project_dir)
    
    # Ensure we're pointing to the source project, not the tool
    if abs_project_dir.endswith('/codebase-qa'):
        abs_project_dir = os.path.dirname(abs_project_dir)
    
    # Import ProjectConfig here to avoid circular dependency at module level
    try:
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
            # Build the logs directory path
            logs_dir = os.path.join(abs_project_dir, f"codebase-qa_{project_type}", "logs")
            
            # CRITICAL: Prevent nested logs directories
            # If the path already contains '/logs', don't append another one
            if '/logs' in logs_dir and logs_dir.endswith('/logs'):
                # Remove any trailing /logs to prevent nesting
                logs_dir = logs_dir.replace('/logs/logs', '/logs').replace('/logs/logs/', '/logs/')
            
            # Ensure the directory exists
            os.makedirs(logs_dir, exist_ok=True)
            return logs_dir
        else:
            # Fallback to a temporary location if no project type selected
            temp_dir = os.path.join(abs_project_dir, "temp_logs")
            os.makedirs(temp_dir, exist_ok=True)
            return temp_dir
            
    except ImportError:
        # Fallback if config module is not available
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
        log_to_sublog(None, "highlight.log", msg)
        
# logger.py  ── FEEDBACK HELPERS ─────────────────────────────────────────


def move_query_log(query: str, project_dir: str, debug_mode: bool):
    """
    Move preparing_full_context.log  ➜  logs/queries/<TS>_<first7>.log
    Returns (new_path, liked_dir, disliked_dir) or None.
    """
    if not debug_mode:
        return None

    base_logs   = get_project_log_file(project_dir, "")      # …/logs/
    src_log     = get_project_log_file(project_dir, "preparing_full_context.log")
    if not os.path.exists(src_log):
        return None

    for sub in ("queries", "liked", "disliked"):
        os.makedirs(os.path.join(base_logs, sub), exist_ok=True)

    slug = "_".join(re.findall(r"\w+", query)[:7]) or "query"
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst  = os.path.join(base_logs, "queries", f"{ts}_{slug}.log")

    try:  shutil.move(src_log, dst)
    except Exception as e:
        log_highlight(f"move_query_log warning: {e}")
        return None

    return dst, os.path.join(base_logs, "liked"), os.path.join(base_logs, "disliked")


def rate_and_copy(log_path: str, target_dir: str,
                  score: int, remark: str):
    """
    • Append rating block to the source log (score + remark)
    • Copy to target_dir (liked/ or disliked/) without duplicates
    """
    if not (log_path and os.path.exists(log_path)):
        return False

    # 1. append feedback
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n--- USER FEEDBACK --------------------------------\n")
            f.write(f"RATING : {score}/10\n")
            f.write(f"COMMENT: {remark or '(no comment)'}\n")
    except Exception as e:
        log_highlight(f"rate_and_copy append warning: {e}")
        return False

    # 2. copy (dedupe)
    os.makedirs(target_dir, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(log_path))
    candidate = os.path.join(target_dir, base + ext)
    idx = 1
    while os.path.exists(candidate):
        candidate = os.path.join(target_dir, f"{base}_{idx}{ext}")
        idx += 1
    try:
        shutil.copy(log_path, candidate)
        return True
    except Exception as e:
        log_highlight(f"rate_and_copy copy warning: {e}")
        return False
# ────────────────────────────────────────────────────────────────────────
