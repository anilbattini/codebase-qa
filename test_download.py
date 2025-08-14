#!/usr/bin/env python3
"""
Test script to verify Hugging Face model downloading functionality.
"""

import sys
import os

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

def test_model_download():
    """Test the model download functionality."""
    print("🧪 Testing Hugging Face Model Download")
    print("=" * 50)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from model_provider import HuggingFaceProvider
        from model_config import model_config
        print("✅ All imports successful")
        
        # Test provider creation
        print("\n🏭 Testing provider creation...")
        provider = HuggingFaceProvider()
        print("✅ HuggingFaceProvider created successfully")
        
        # Test model download
        print("\n📥 Testing model download...")
        print("This may take several minutes for the first time...")
        success = provider.download_all_models()
        
        if success:
            print("✅ All models downloaded successfully!")
        else:
            print("❌ Model download failed")
            
        # Test provider switching
        print("\n🔄 Testing provider switching...")
        model_config.switch_to_huggingface()
        print(f"✅ Switched to: {model_config.get_current_provider_type()}")
        
        # Test getting models
        print("\n🤖 Testing model retrieval...")
        try:
            embedding_model = provider.get_embedding_model()
            print("✅ Embedding model retrieved successfully")
        except Exception as e:
            print(f"❌ Failed to get embedding model: {e}")
        
        try:
            llm_model = provider.get_llm_model()
            print("✅ LLM model retrieved successfully")
        except Exception as e:
            print(f"❌ Failed to get LLM model: {e}")
        
        print("\n🎉 All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_download()
