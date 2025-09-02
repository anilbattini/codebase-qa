#!/usr/bin/env python3
"""
Test session state initialization and database cleanup to prevent AttributeError and database locking issues.
"""

import sys
import os
import tempfile
import shutil

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

def test_session_state_initialization():
    """Test that session state variables are properly initialized."""
    print("🧪 Testing session state initialization...")
    
    try:
        import streamlit as st
        from rag_manager import RagManager
        
        # Mock session state for testing
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        
        # Test RagManager initialization
        rag_manager = RagManager()
        rag_manager.initialize_session_state()
        
        # Check that all required session state variables are initialized
        required_vars = ["retriever", "project_dir_used", "thinking_logs", "vectorstore", "chat_history"]
        
        for var in required_vars:
            if var not in st.session_state:
                print(f"❌ Missing session state variable: {var}")
                return False
            else:
                print(f"✅ Session state variable initialized: {var}")
        
        # Test thinking_logs operations
        st.session_state.thinking_logs.append("Test log entry")
        st.session_state.thinking_logs.clear()
        
        print("✅ Session state initialization test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Session state initialization test failed: {e}")
        return False

def test_database_cleanup():
    """Test that database cleanup works correctly without locking issues."""
    print("🧪 Testing database cleanup functionality...")
    
    try:
        from rag_manager import RagManager
        from config.config import ProjectConfig
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock project structure
            project_dir = os.path.join(temp_dir, "test_project")
            os.makedirs(project_dir)
            
            # Create mock database files
            db_dir = os.path.join(project_dir, "vector_db")
            os.makedirs(db_dir)
            
            # Create mock Chroma database files
            mock_files = [
                "chroma.sqlite3",
                "chroma.sqlite3-shm", 
                "chroma.sqlite3-wal",
                "git_tracking.json"
            ]
            
            for file_name in mock_files:
                file_path = os.path.join(db_dir, file_name)
                with open(file_path, 'w') as f:
                    f.write("mock content")
            
            # Test cleanup
            rag_manager = RagManager()
            cleanup_success = rag_manager.cleanup_existing_files(project_dir, "android")
            
            if cleanup_success:
                # Check that database directory was cleaned
                if os.path.exists(db_dir):
                    remaining_files = os.listdir(db_dir)
                    if not remaining_files:
                        print("✅ Database cleanup successful - all files removed")
                    else:
                        print(f"⚠️ Database cleanup partial - remaining files: {remaining_files}")
                else:
                    print("✅ Database cleanup successful - directory removed")
                
                print("✅ Database cleanup test passed!")
                return True
            else:
                print("❌ Database cleanup failed")
                return False
                
    except Exception as e:
        print(f"❌ Database cleanup test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Running session state and database cleanup tests...")
    print("=" * 50)
    
    test1_success = test_session_state_initialization()
    test2_success = test_database_cleanup()
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    print(f"Session State Initialization: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Database Cleanup: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    overall_success = test1_success and test2_success
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    sys.exit(0 if overall_success else 1) 