#!/usr/bin/env python3
"""
Test Helpers - Common Test Utilities and Mock Classes
=====================================================

This module contains common test utilities, mock classes, and helper functions
used across multiple test suites. It follows clean code principles by keeping
files focused and under 250 lines.

Usage:
    from test_helpers import MockSessionState, MockLogPlaceholder, TestConfig
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

class MockSessionState:
    """Mock Streamlit session state for testing outside Streamlit context."""
    
    def __init__(self):
        self._data = {}
    
    def get(self, key, default=None):
        """Get value from session state."""
        return self._data.get(key, default)
    
    def __setitem__(self, key, value):
        """Set value in session state."""
        self._data[key] = value
    
    def __getitem__(self, key):
        """Get value from session state."""
        return self._data[key]
    
    def __contains__(self, key):
        """Check if key exists in session state."""
        return key in self._data
    
    def __delitem__(self, key):
        """Delete key from session state."""
        if key in self._data:
            del self._data[key]
    
    def setdefault(self, key, default=None):
        """Set default value if key doesn't exist."""
        if key not in self._data:
            self._data[key] = default
        return self._data[key]
    
    def keys(self):
        """Get all keys in session state."""
        return self._data.keys()


class MockLogPlaceholder:
    """Mock Streamlit placeholder for testing logging functionality."""
    
    def container(self):
        """Return self as container."""
        return self
    
    def text_area(self, *args, **kwargs):
        """Mock text area - does nothing."""
        pass
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


class TestConfig:
    """Test configuration and utilities."""
    
    def __init__(self):
        self.project_types = {
            "1": "android",
            "2": "python", 
            "3": "javascript",
            "4": "react",
            "5": "vue",
            "6": "angular",
            "7": "flutter",
            "8": "ios"
        }
    
    def get_default_project_config(self) -> Dict[str, Any]:
        """Get default project configuration for testing."""
        # Import centralized model configuration
        import sys
        import os
        core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'core')
        if core_path not in sys.path:
            sys.path.insert(0, core_path)
        
        from config.model_config import model_config
        
        return {
            "project_dir": "/Users/macuser/WORK/Samples/Android/SampleResponsive",
            "project_type": "android",
            "ollama_endpoint": model_config.get_ollama_endpoint(),
            "ollama_model": model_config.get_ollama_model(),
            "embedding_model": model_config.get_embedding_model(),
            "chunk_size": model_config.get_chunk_size(),
            "chunk_overlap": model_config.get_chunk_overlap(),
            "search_k": model_config.get_search_k()
        }
    
    def setup_test_environment(self):
        """Setup test environment with proper session state mocking."""
        import streamlit as st
        
        # Mock session state if not in Streamlit context
        if not hasattr(st, 'session_state'):
            st.session_state = MockSessionState()
        
        # Initialize common session variables
        st.session_state.setdefault("thinking_logs", [])
        st.session_state.setdefault("rag_building_in_progress", False)
        st.session_state.setdefault("rag_build_start_time", None)
        
        return st.session_state


class TestResult:
    """Standardized test result structure."""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.timestamp = datetime.now().isoformat()
        self.status = "unknown"
        self.details = {}
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "test_name": self.test_name,
            "timestamp": self.timestamp,
            "status": self.status,
            "details": self.details,
            "error": self.error
        }
    
    def set_success(self, details: Dict[str, Any] = None):
        """Mark test as successful."""
        self.status = "success"
        if details:
            self.details.update(details)
    
    def set_failed(self, error: str, details: Dict[str, Any] = None):
        """Mark test as failed."""
        self.status = "failed"
        self.error = error
        if details:
            self.details.update(details)


def create_test_logger(project_dir: str, log_file: str = "test.log"):
    """Create a test logger that writes to a test-specific log file."""
    log_path = os.path.join(project_dir, "logs", log_file)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    def log_message(message: str):
        timestamp = datetime.now().isoformat()
        with open(log_path, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    return log_message


def cleanup_test_files(project_dir: str):
    """Clean up test-generated files."""
    import shutil
    
    # List of directories/files to clean up
    cleanup_paths = [
        os.path.join(project_dir, "codebase-qa_android"),
        os.path.join(project_dir, "logs"),
        os.path.join(project_dir, "git_tracking.json"),
        os.path.join(project_dir, "git_commit.json")
    ]
    
    for path in cleanup_paths:
        if os.path.exists(path):
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
            print(f"🧹 Cleaned up: {path}")


def validate_project_structure(project_dir: str) -> Dict[str, Any]:
    """Validate project structure and return validation results."""
    result = {
        "valid": True,
        "issues": [],
        "file_count": 0,
        "supported_files": 0
    }
    
    if not os.path.exists(project_dir):
        result["valid"] = False
        result["issues"].append(f"Project directory does not exist: {project_dir}")
        return result
    
    # Count files
    for root, dirs, files in os.walk(project_dir):
        for file in files:
            result["file_count"] += 1
            if file.endswith(('.py', '.js', '.ts', '.java', '.kt', '.xml', '.gradle')):
                result["supported_files"] += 1
    
    if result["supported_files"] == 0:
        result["valid"] = False
        result["issues"].append("No supported file types found")
    
    return result 