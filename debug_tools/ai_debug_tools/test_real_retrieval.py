#!/usr/bin/env python3
"""
Test real retrieval functionality after database rebuild.
"""

import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

def test_real_retrieval():
    """Test that the retriever actually works with real queries."""
    print("🧪 Testing real retrieval functionality...")
    
    try:
        from langchain_chroma import Chroma
        from langchain_ollama import OllamaEmbeddings
        from config.config import ProjectConfig
        
        # Test configuration
        project_config = ProjectConfig(project_type="android", project_dir="../../")
        db_dir = project_config.get_db_dir()
        
        print(f"Database directory: {db_dir}")
        
        if not os.path.exists(db_dir):
            print("❌ Database directory not found - need to rebuild RAG first")
            return False
        
        # Test embeddings
        embeddings = OllamaEmbeddings(model="nomic-embed-text:latest", base_url="http://localhost:11434")
        
        # Test Chroma configuration
        vectorstore = Chroma(
            persist_directory=db_dir,
            embedding_function=embeddings
        )
        
        # Test retriever with fixed configuration
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 15}
        )
        
        # Test actual retrieval
        test_query = "what does this project do"
        print(f"Testing query: '{test_query}'")
        
        try:
            results = retriever.get_relevant_documents(test_query)
            print(f"✅ Retrieval successful! Found {len(results)} documents")
            
            if results:
                print("📄 Sample results:")
                for i, doc in enumerate(results[:3]):  # Show first 3
                    print(f"  {i+1}. Source: {doc.metadata.get('source', 'unknown')}")
                    print(f"     Content preview: {doc.page_content[:100]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Retrieval failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_real_retrieval()
    sys.exit(0 if success else 1) 