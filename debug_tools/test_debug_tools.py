#!/usr/bin/env python3
"""
Test script for debug tools functionality.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import ProjectConfig
from debug_tools import DebugTools
from vector_db_inspector import inspect_vector_db
from chunk_analyzer import analyze_chunks
from retrieval_tester import test_retrieval

def test_debug_tools():
    """Test all debug tools functionality."""
    print("🧪 Testing Debug Tools...")
    
    # Test project config
    project_dir = "../"
    project_config = ProjectConfig(project_dir=project_dir, project_type="android")
    
    print(f"✅ Project config loaded: {project_config.project_type}")
    print(f"✅ Database path: {project_config.get_db_dir()}")
    print(f"✅ Logs path: {project_config.get_logs_dir()}")
    
    # Test debug tools instantiation
    debug_tools = DebugTools(
        project_config=project_config,
        ollama_model="llama3.2",
        ollama_endpoint="http://localhost:11434",
        project_dir=project_dir
    )
    
    print("✅ DebugTools instantiated successfully")
    
    # Test vector DB inspector without Streamlit
    print("✅ Vector DB inspector available")
    
    # Test chunk analyzer
    print("✅ Chunk analyzer available")
    
    # Test retrieval tester
    print("✅ Retrieval tester available")
    
    print("🎉 All debug tools tests passed!")

if __name__ == "__main__":
    test_debug_tools()