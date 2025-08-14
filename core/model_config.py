"""
model_config.py

Centralized model configuration management.
Single source of truth for all model settings across the application.
Now supports both Ollama and Hugging Face models locally (no API tokens required).
"""

from typing import Dict, Any, List
from model_provider import set_provider, get_current_provider, get_current_provider_type
from logger import log_to_sublog


class ModelConfig:
    """
    Centralized model configuration management.
    Single source of truth for all model settings across the application.
    Now supports both Ollama and Hugging Face providers locally.
    """
    
    def __init__(self):
        # Default model settings
        self._ollama_model = "llama3.1:latest"
        self._embedding_model = "nomic-embed-text:latest"
        self._ollama_endpoint = "http://localhost:11434"
        self._chunk_size = 1000
        self._chunk_overlap = 200
        self._search_k = 5
        
        # New provider settings
        self._provider_type = "ollama"  # Default to Ollama for backward compatibility
        # self._huggingface_embedding_model = "sentence-transformers/paraphrase-MiniLM-L3-v2"
        # self._huggingface_llm_model = "microsoft/DialoGPT-medium"
        
        # self._huggingface_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        # self._huggingface_llm_model = "mistralai/Mistral-7B-Instruct-v0.2"
        
        self._huggingface_embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self._huggingface_llm_model = "Qwen/Qwen2.5-7B-Instruct"

        
        # Prevent multiple initializations
        self._initialized = False
        
        # Initialize default provider
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the default model provider."""
        # Prevent multiple initializations
        if self._initialized:
            return
            
        try:
            log_to_sublog(".", "model_provider.log", f"🔄 Initializing {self._provider_type} provider...")
            
            if self._provider_type == "ollama":
                from model_provider import set_provider
                set_provider("ollama", endpoint=self._ollama_endpoint)
                self._initialized = True
                log_to_sublog(".", "model_provider.log", f"✅ Ollama provider initialized successfully")
            elif self._provider_type == "huggingface":
                from model_provider import set_provider, force_provider_initialization
                try:
                    # Try normal initialization first
                    set_provider("huggingface", 
                               embedding_model=self._huggingface_embedding_model,
                               llm_model=self._huggingface_llm_model)
                    self._initialized = True
                    log_to_sublog(".", "model_provider.log", f"✅ HuggingFace provider initialized successfully")
                except Exception as e:
                    log_to_sublog(".", "model_provider.log", f"⚠️ Normal HuggingFace initialization failed: {e}")
                    log_to_sublog(".", "model_provider.log", f"🔄 Trying force initialization...")
                    
                    # Try force initialization with retry logic
                    if force_provider_initialization("huggingface", 
                                                   embedding_model=self._huggingface_embedding_model,
                                                   llm_model=self._huggingface_llm_model):
                        self._initialized = True
                        log_to_sublog(".", "model_provider.log", f"✅ Force initialization successful")
                    else:
                        raise Exception("Force initialization failed")
                        
        except Exception as e:
            # Log error but don't fail - fallback to Ollama
            log_to_sublog(".", "model_provider.log", f"❌ Could not initialize {self._provider_type} provider: {e}")
            log_to_sublog(".", "model_provider.log", f"🔄 Falling back to Ollama provider")
            
            # Only fallback if we haven't already initialized Ollama
            if not self._initialized or self._provider_type != "ollama":
                self._provider_type = "ollama"
                try:
                    from model_provider import set_provider
                    set_provider("ollama", endpoint=self._ollama_endpoint)
                    self._initialized = True
                    log_to_sublog(".", "model_provider.log", f"✅ Fallback to Ollama successful")
                except Exception as fallback_error:
                    log_to_sublog(".", "model_provider.log", f"❌ Fallback to Ollama also failed: {fallback_error}")
                    # At this point, we can't do much more - the app will likely fail
                    print(f"Critical: Could not initialize any model provider: {fallback_error}")
    
    # Provider Type
    @property
    def provider_type(self) -> str:
        """Get the current provider type."""
        return self._provider_type
    
    @provider_type.setter
    def provider_type(self, value: str):
        """Set the provider type and reinitialize."""
        if value.lower() in ["ollama", "huggingface"]:
            self._provider_type = value.lower()
            self._initialize_provider()
        else:
            raise ValueError(f"Unsupported provider type: {value}")
    
    def get_provider_type(self) -> str:
        """Get the current provider type."""
        return self._provider_type
    
    def set_provider_type(self, value: str):
        """Set the provider type."""
        self.provider_type = value
    
    # Hugging Face Models (Local - No API token required)
    @property
    def huggingface_embedding_model(self) -> str:
        """Get the Hugging Face embedding model name."""
        return self._huggingface_embedding_model
    
    @huggingface_embedding_model.setter
    def huggingface_embedding_model(self, value: str):
        """Set the Hugging Face embedding model name."""
        self._huggingface_embedding_model = value
        if self._provider_type == "huggingface":
            self._initialize_provider()
    
    def get_huggingface_embedding_model(self) -> str:
        """Get the Hugging Face embedding model name."""
        return self._huggingface_embedding_model
    
    def set_huggingface_embedding_model(self, value: str):
        """Set the Hugging Face embedding model name."""
        self.huggingface_embedding_model = value
    
    @property
    def huggingface_llm_model(self) -> str:
        """Get the Hugging Face LLM model name."""
        return self._huggingface_llm_model
    
    @huggingface_llm_model.setter
    def huggingface_llm_model(self, value: str):
        """Set the Hugging Face LLM model name."""
        self._huggingface_llm_model = value
        if self._provider_type == "huggingface":
            self._initialize_provider()
    
    def get_huggingface_llm_model(self) -> str:
        """Get the Hugging Face LLM model name."""
        return self._huggingface_llm_model
    
    def set_huggingface_llm_model(self, value: str):
        """Set the Hugging Face LLM model name."""
        self.huggingface_llm_model = value
    
    # Ollama Models
    @property
    def ollama_model(self) -> str:
        """Get the Ollama model name."""
        return self._ollama_model
    
    @ollama_model.setter
    def ollama_model(self, value: str):
        """Set the Ollama model name."""
        self._ollama_model = value
    
    def get_ollama_model(self) -> str:
        """Get the Ollama model name."""
        return self._ollama_model
    
    def set_ollama_model(self, value: str):
        """Set the Ollama model name."""
        self.ollama_model = value
    
    # Embedding Model (Provider-aware)
    @property
    def embedding_model(self) -> str:
        """Get the current embedding model based on provider."""
        if self._provider_type == "ollama":
            return self._embedding_model
        else:
            return self._huggingface_embedding_model
    
    @embedding_model.setter
    def embedding_model(self, value: str):
        """Set the embedding model for the current provider."""
        if self._provider_type == "ollama":
            self._embedding_model = value
        else:
            self._huggingface_embedding_model = value
    
    def get_embedding_model(self) -> str:
        """Get the current embedding model."""
        return self.embedding_model
    
    def set_embedding_model(self, value: str):
        """Set the embedding model."""
        self.embedding_model = value
    
    # Ollama Endpoint
    @property
    def ollama_endpoint(self) -> str:
        """Get the Ollama endpoint URL."""
        return self._ollama_endpoint
    
    @ollama_endpoint.setter
    def ollama_endpoint(self, value: str):
        """Set the Ollama endpoint URL."""
        self._ollama_endpoint = value
        if self._provider_type == "ollama":
            self._initialize_provider()
    
    def get_ollama_endpoint(self) -> str:
        """Get the Ollama endpoint URL."""
        return self._ollama_endpoint
    
    def set_ollama_endpoint(self, value: str):
        """Set the Ollama endpoint URL."""
        self.ollama_endpoint = value
    
    # Chunk Settings
    @property
    def chunk_size(self) -> int:
        """Get the chunk size."""
        return self._chunk_size
    
    @chunk_size.setter
    def chunk_size(self, value: int):
        """Set the chunk size."""
        self._chunk_size = value
    
    def get_chunk_size(self) -> int:
        """Get the chunk size."""
        return self._chunk_size
    
    def set_chunk_size(self, value: int):
        """Set the chunk size."""
        self.chunk_size = value
    
    @property
    def chunk_overlap(self) -> int:
        """Get the chunk overlap."""
        return self._chunk_overlap
    
    @chunk_overlap.setter
    def chunk_overlap(self, value: int):
        """Set the chunk overlap."""
        self._chunk_overlap = value
    
    def get_chunk_overlap(self) -> int:
        """Get the chunk overlap."""
        return self._chunk_overlap
    
    def set_chunk_overlap(self, value: int):
        """Set the chunk overlap."""
        self.chunk_overlap = value
    
    # Search Settings
    @property
    def search_k(self) -> int:
        """Get the search k value."""
        return self._search_k
    
    @search_k.setter
    def search_k(self, value: int):
        """Set the search k value."""
        self._search_k = value
    
    def get_search_k(self) -> int:
        """Get the search k value."""
        return self._search_k
    
    def set_search_k(self, value: int):
        """Set the search k value."""
        self.search_k = value
    
    # Provider Management
    def get_current_provider(self):
        """Get the current model provider instance."""
        return get_current_provider()
    
    def get_current_provider_type(self) -> str:
        """Get the current provider type."""
        return self._provider_type
    
    def get_provider(self, provider_type: str = None):
        """Get a specific provider instance."""
        if provider_type is None:
            provider_type = self._provider_type
        
        if provider_type == "ollama":
            from model_provider import OllamaProvider
            return OllamaProvider(endpoint=self._ollama_endpoint)
        elif provider_type == "huggingface":
            from model_provider import HuggingFaceProvider
            return HuggingFaceProvider(
                embedding_model=self._huggingface_embedding_model,
                llm_model=self._huggingface_llm_model
            )
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    def diagnose_provider_issues(self) -> List[str]:
        """Diagnose common provider issues and return suggestions."""
        issues = []
        status = self.get_provider_status()
        
        if status["status"] == "error":
            issues.append(f"Provider error: {status['error']}")
            
        if status["provider_type"] == "ollama":
            if status["status"] == "unavailable":
                issues.append("Ollama server is not responding")
                issues.append("Check if Ollama is running: ollama serve")
                issues.append(f"Verify endpoint: {self._ollama_endpoint}")
                
        elif status["provider_type"] == "huggingface":
            if status["status"] == "unavailable":
                issues.append("HuggingFace models are not available")
                issues.append("Check if models are downloaded")
                issues.append("Verify cache directory permissions")
                issues.append("Check available disk space")
                
        return issues

    def switch_to_ollama(self):
        """Switch to Ollama provider."""
        try:
            log_to_sublog(".", "model_provider.log", f"🔄 Switching to Ollama provider...")
            self._provider_type = "ollama"
            self._initialized = False  # Reset initialization flag
            from model_provider import set_provider
            set_provider("ollama", endpoint=self._ollama_endpoint)
            self._initialized = True
            log_to_sublog(".", "model_provider.log", f"✅ Successfully switched to Ollama provider")
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to switch to Ollama provider: {e}")
            raise e

    def switch_to_huggingface(self):
        """Switch to HuggingFace provider."""
        try:
            log_to_sublog(".", "model_provider.log", f"🔄 Switching to HuggingFace provider...")
            self._provider_type = "huggingface"
            self._initialized = False  # Reset initialization flag
            from model_provider import set_provider, force_provider_initialization
            try:
                # Try normal initialization first
                set_provider("huggingface", 
                           embedding_model=self._huggingface_embedding_model,
                           llm_model=self._huggingface_llm_model)
                self._initialized = True
                log_to_sublog(".", "model_provider.log", f"✅ Successfully switched to HuggingFace provider")
            except Exception as e:
                log_to_sublog(".", "model_provider.log", f"⚠️ Normal HuggingFace initialization failed: {e}")
                log_to_sublog(".", "model_provider.log", f"🔄 Trying force initialization...")
                
                # Try force initialization with retry logic
                if force_provider_initialization("huggingface", 
                                               embedding_model=self._huggingface_embedding_model,
                                               llm_model=self._huggingface_llm_model):
                    self._initialized = True
                    log_to_sublog(".", "model_provider.log", f"✅ Force initialization successful")
                else:
                    raise Exception("Force initialization failed")
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to switch to HuggingFace provider: {e}")
            raise e

    def download_huggingface_models(self):
        """Manually trigger Hugging Face model downloads."""
        try:
            if self._provider_type == "huggingface":
                provider = self.get_current_provider()
                if hasattr(provider, 'download_all_models'):
                    return provider.download_all_models()
                else:
                    return False
            else:
                return False
        except Exception as e:
            print(f"Model download failed: {e}")
            return False
    
    # Configuration Export
    def get_config(self) -> Dict[str, Any]:
        """Get the complete configuration as a dictionary."""
        return {
            "provider_type": self._provider_type,
            "ollama_model": self._ollama_model,
            "ollama_endpoint": self._ollama_endpoint,
            "embedding_model": self.embedding_model,
            "huggingface_embedding_model": self._huggingface_embedding_model,
            "huggingface_llm_model": self._huggingface_llm_model,
            "chunk_size": self._chunk_size,
            "chunk_overlap": self._chunk_overlap,
            "search_k": self._search_k
        }
    
    def load_config(self, config: Dict[str, Any]):
        """Load configuration from a dictionary."""
        if "provider_type" in config:
            self._provider_type = config["provider_type"]
        if "ollama_model" in config:
            self._ollama_model = config["ollama_model"]
        if "ollama_endpoint" in config:
            self._ollama_endpoint = config["ollama_endpoint"]
        if "huggingface_embedding_model" in config:
            self._huggingface_embedding_model = config["huggingface_embedding_model"]
        if "huggingface_llm_model" in config:
            self._huggingface_llm_model = config["huggingface_llm_model"]
        if "chunk_size" in config:
            self._chunk_size = config["chunk_size"]
        if "chunk_overlap" in config:
            self._chunk_overlap = config["chunk_overlap"]
        if "search_k" in config:
            self._search_k = config["search_k"]
        
        # Reinitialize provider with new settings
        self._initialize_provider()

    def get_provider_status(self) -> Dict[str, Any]:
        """Get detailed provider status information."""
        try:
            provider = self.get_current_provider()
            provider_type = self.get_current_provider_type()
            
            status = {
                "provider_type": provider_type,
                "status": "unknown",
                "details": {},
                "error": None
            }
            
            if provider_type == "ollama":
                # Check Ollama availability
                try:
                    import requests
                    response = requests.get(f"{self._ollama_endpoint}/api/tags", timeout=5)
                    if response.status_code == 200:
                        status["status"] = "available"
                        status["details"] = {
                            "endpoint": self._ollama_endpoint,
                            "response_time": response.elapsed.total_seconds()
                        }
                    else:
                        status["status"] = "unavailable"
                        status["error"] = f"HTTP {response.status_code}"
                except Exception as e:
                    status["status"] = "error"
                    status["error"] = str(e)
                    
            elif provider_type == "huggingface":
                # Check HuggingFace availability
                try:
                    if hasattr(provider, 'check_availability'):
                        if provider.check_availability():
                            status["status"] = "available"
                            status["details"] = {
                                "embedding_model": self._huggingface_embedding_model,
                                "llm_model": self._huggingface_llm_model,
                                "cache_directory": getattr(provider, 'cache_dir', 'unknown')
                            }
                        else:
                            status["status"] = "unavailable"
                            status["error"] = "Availability check failed"
                    else:
                        status["status"] = "unknown"
                        status["error"] = "Provider has no availability check method"
                except Exception as e:
                    status["status"] = "error"
                    status["error"] = str(e)
            
            return status
            
        except Exception as e:
            return {
                "provider_type": "unknown",
                "status": "error",
                "details": {},
                "error": str(e)
            }
    
    def diagnose_provider_issues(self) -> List[str]:
        """Diagnose common provider issues and return suggestions."""
        issues = []
        status = self.get_provider_status()
        
        if status["status"] == "error":
            issues.append(f"Provider error: {status['error']}")
            
        if status["provider_type"] == "ollama":
            if status["status"] == "unavailable":
                issues.append("Ollama server is not responding")
                issues.append("Check if Ollama is running: ollama serve")
                issues.append(f"Verify endpoint: {self._ollama_endpoint}")
                
        elif status["provider_type"] == "huggingface":
            if status["status"] == "unavailable":
                issues.append("HuggingFace models are not available")
                issues.append("Check if models are downloaded")
                issues.append("Verify cache directory permissions")
                issues.append("Check available disk space")
                
        return issues


# Global model configuration instance
model_config = ModelConfig() 