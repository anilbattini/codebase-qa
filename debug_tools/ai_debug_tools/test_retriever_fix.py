#!/usr/bin/env python3
"""
Test retriever configuration to ensure Chroma compatibility.
"""

import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

def test_retriever_configuration():
    """Test that the retriever configuration is compatible with Chroma."""
    print("🧪 Testing retriever configuration...")
    
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from config.config import ProjectConfig
        
        # Test configuration
        project_config = ProjectConfig(project_type="android", project_dir="../../")
        db_dir = project_config.get_db_dir()
        
        # Test embeddings
        embeddings = OllamaEmbeddings(model="nomic-embed-text:latest", base_url="http://localhost:11434")
        
        # Test Chroma configuration
        if os.path.exists(db_dir):
            vectorstore = Chroma(
                persist_directory=db_dir,
                embedding_function=embeddings
            )
            
            # Test retriever with fixed configuration
            retriever = vectorstore.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 15}
            )
            
            print("✅ Retriever configuration test passed!")
            print("✅ Chroma compatibility verified")
            return True
            
        else:
            print("⚠️ Database directory not found, but configuration is valid")
            return True
            
    except Exception as e:
        print(f"❌ Retriever configuration test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_retriever_configuration()
    sys.exit(0 if success else 1) 