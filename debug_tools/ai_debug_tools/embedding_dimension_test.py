#!/usr/bin/env python3
"""
Embedding Dimension Test and Fix
Diagnoses and fixes the 'Collection expecting embedding with dimension of 768, got 4096' error.
"""

import os
import sys
import shutil
import requests
from typing import Dict, Any

# Add the core directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from config.config import ProjectConfig
from logger import log_to_sublog, log_highlight

class EmbeddingDimensionTest:
    """Test and fix embedding dimension issues."""
    
    def __init__(self, project_dir: str, ollama_endpoint: str = "http://127.0.0.1:11434", is_streamlit_context: bool = False):
        self.project_dir = project_dir
        self.ollama_endpoint = ollama_endpoint
        self.project_config = ProjectConfig(project_type="android", project_dir=project_dir)
        self.is_streamlit_context = is_streamlit_context
        
        # Determine log directory based on context
        if is_streamlit_context:
            # When run from Streamlit UI
            self.log_dir = os.path.join(project_dir, "debug_tools", "logs")
        else:
            # When run manually from ai_debug_tools
            self.log_dir = os.path.join(os.path.dirname(__file__), "logs")
        
        os.makedirs(self.log_dir, exist_ok=True)
        
    def diagnose_embedding_issue(self) -> Dict[str, Any]:
        """Diagnose the embedding dimension issue."""
        log_highlight("Diagnosing embedding dimension issue")
        log_to_sublog(self.project_dir, "embedding_test.log", "=== EMBEDDING DIMENSION DIAGNOSIS ===")
        
        results = {
            "test_name": "embedding_dimension_diagnosis",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Check Ollama models
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code != 200:
                results["status"] = "failed"
                results["details"]["error"] = f"Ollama connection failed: {response.status_code}"
                return results
            
            models_data = response.json()
            available_models = [model.get("name", "") for model in models_data.get("models", [])]
            
            log_to_sublog(self.project_dir, "embedding_test.log", f"Available models: {available_models}")
            results["details"]["available_models"] = available_models
            
            # Check for embedding models
            embedding_models = [model for model in available_models if "embed" in model.lower()]
            results["details"]["embedding_models"] = embedding_models
            
            # Check vector database directory
            vector_db_dir = self.project_config.get_db_dir()
            if os.path.exists(vector_db_dir):
                log_to_sublog(self.project_dir, "embedding_test.log", f"Vector DB exists at: {vector_db_dir}")
                results["details"]["vector_db_exists"] = True
                results["details"]["vector_db_path"] = vector_db_dir
                
                # Check for Chroma files
                chroma_files = []
                if os.path.exists(vector_db_dir):
                    for file in os.listdir(vector_db_dir):
                        if file.endswith('.parquet') or file.endswith('.json'):
                            chroma_files.append(file)
                
                results["details"]["chroma_files"] = chroma_files
                log_to_sublog(self.project_dir, "embedding_test.log", f"Chroma files found: {chroma_files}")
            else:
                results["details"]["vector_db_exists"] = False
                log_to_sublog(self.project_dir, "embedding_test.log", "Vector DB does not exist")
            
            results["status"] = "success"
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "embedding_test.log", f"Diagnosis failed: {e}")
        
        return results
    
    def fix_embedding_issue(self) -> Dict[str, Any]:
        """Fix the embedding dimension issue by clearing and rebuilding."""
        log_highlight("Fixing embedding dimension issue")
        log_to_sublog(self.project_dir, "embedding_test.log", "=== EMBEDDING DIMENSION FIX ===")
        
        results = {
            "test_name": "embedding_dimension_fix",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Step 1: Clear existing vector database
            vector_db_dir = self.project_config.get_db_dir()
            if os.path.exists(vector_db_dir):
                log_to_sublog(self.project_dir, "embedding_test.log", f"Clearing vector DB: {vector_db_dir}")
                shutil.rmtree(vector_db_dir)
                results["details"]["vector_db_cleared"] = True
            else:
                log_to_sublog(self.project_dir, "embedding_test.log", "Vector DB does not exist, nothing to clear")
                results["details"]["vector_db_cleared"] = False
            
            # Step 2: Check if proper embedding model is available
            response = requests.get(f"{self.ollama_endpoint}/api/tags", timeout=10)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [model.get("name", "") for model in models_data.get("models", [])]
                
                # Look for proper embedding model
                embedding_model = None
                for model in available_models:
                    if "nomic-embed" in model.lower():
                        embedding_model = model
                        break
                
                if embedding_model:
                    log_to_sublog(self.project_dir, "embedding_test.log", f"Found embedding model: {embedding_model}")
                    results["details"]["embedding_model"] = embedding_model
                    results["status"] = "ready_for_rebuild"
                else:
                    log_to_sublog(self.project_dir, "embedding_test.log", "No proper embedding model found")
                    results["details"]["embedding_model"] = None
                    results["status"] = "needs_embedding_model"
            else:
                results["status"] = "failed"
                results["details"]["error"] = "Cannot connect to Ollama"
            
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "embedding_test.log", f"Fix failed: {e}")
        
        return results
    
    def install_embedding_model(self) -> Dict[str, Any]:
        """Install the proper embedding model."""
        log_highlight("Installing embedding model")
        log_to_sublog(self.project_dir, "embedding_test.log", "=== INSTALLING EMBEDDING MODEL ===")
        
        results = {
            "test_name": "install_embedding_model",
            "status": "unknown",
            "details": {}
        }
        
        try:
            # Try to pull the embedding model
            import subprocess
            
            log_to_sublog(self.project_dir, "embedding_test.log", "Pulling nomic-embed-text model...")
            
            # Use subprocess to run ollama pull
            result = subprocess.run(
                ["ollama", "pull", "nomic-embed-text"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                log_to_sublog(self.project_dir, "embedding_test.log", "Embedding model installed successfully")
                results["status"] = "success"
                results["details"]["installation_output"] = result.stdout
            else:
                log_to_sublog(self.project_dir, "embedding_test.log", f"Embedding model installation failed: {result.stderr}")
                results["status"] = "failed"
                results["details"]["error"] = result.stderr
                
        except Exception as e:
            results["status"] = "failed"
            results["details"]["error"] = str(e)
            log_to_sublog(self.project_dir, "embedding_test.log", f"Installation failed: {e}")
        
        return results
    
    def run_complete_fix(self) -> Dict[str, Any]:
        """Run complete fix for embedding dimension issue."""
        log_highlight("Running complete embedding dimension fix")
        log_to_sublog(self.project_dir, "embedding_test.log", "=== COMPLETE EMBEDDING FIX ===")
        
        # Step 1: Diagnose
        diagnosis = self.diagnose_embedding_issue()
        log_to_sublog(self.project_dir, "embedding_test.log", f"Diagnosis result: {diagnosis['status']}")
        
        # Step 2: Fix
        fix_result = self.fix_embedding_issue()
        log_to_sublog(self.project_dir, "embedding_test.log", f"Fix result: {fix_result['status']}")
        
        # Step 3: Install embedding model if needed
        if fix_result["status"] == "needs_embedding_model":
            install_result = self.install_embedding_model()
            log_to_sublog(self.project_dir, "embedding_test.log", f"Installation result: {install_result['status']}")
        else:
            install_result = {"status": "skipped", "details": {"reason": "Embedding model already available"}}
        
        return {
            "diagnosis": diagnosis,
            "fix": fix_result,
            "installation": install_result,
            "recommendation": self._get_recommendation(diagnosis, fix_result, install_result)
        }
    
    def _get_recommendation(self, diagnosis: Dict, fix: Dict, install: Dict) -> str:
        """Get recommendation based on test results."""
        if diagnosis["status"] == "failed":
            return "❌ Cannot diagnose issue. Check Ollama connection."
        
        if fix["status"] == "failed":
            return "❌ Cannot fix issue. Check file permissions."
        
        if install["status"] == "failed":
            return "❌ Cannot install embedding model. Run 'ollama pull nomic-embed-text' manually."
        
        if fix["status"] == "ready_for_rebuild":
            return "✅ Ready to rebuild RAG index. Restart the application."
        
        if install["status"] == "success":
            return "✅ Embedding model installed. Ready to rebuild RAG index."
        
        return "⚠️ Unknown state. Check logs for details."

def main():
    """Main function to run embedding dimension test and fix."""
    print("🔧 Embedding Dimension Test and Fix")
    print("=" * 50)
    
    # Configuration
    project_dir = "../"  # Adjust as needed
    ollama_endpoint = "http://127.0.0.1:11434"
    
    # Initialize test (manual run, not from Streamlit)
    test = EmbeddingDimensionTest(project_dir, ollama_endpoint, is_streamlit_context=False)
    
    # Run complete fix
    results = test.run_complete_fix()
    
    # Print results
    print("\n📊 Results:")
    print("=" * 50)
    
    print(f"Diagnosis: {results['diagnosis']['status']}")
    print(f"Fix: {results['fix']['status']}")
    print(f"Installation: {results['installation']['status']}")
    print(f"\nRecommendation: {results['recommendation']}")
    
    print(f"\n📝 Logs saved to: {test.log_dir}/embedding_test.log")

if __name__ == "__main__":
    main() 