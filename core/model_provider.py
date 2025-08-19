"""
model_provider.py

Abstract model provider interface for supporting both Ollama and Hugging Face models.
This ensures backward compatibility while adding new provider support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import streamlit as st
from logger import log_to_sublog

class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    @abstractmethod
    def get_embedding_model(self, **kwargs):
        """Get embedding model instance."""
        pass
    
    @abstractmethod
    def get_llm_model(self, **kwargs):
        """Get LLM model instance."""
        pass
    
    @abstractmethod
    def check_availability(self, **kwargs) -> bool:
        """Check if the provider is available."""
        pass
    
    @abstractmethod
    def get_info(self) -> Dict[str, str]:
        """Get provider information."""
        pass

class OllamaProvider(ModelProvider):
    """Ollama provider implementation."""
    
    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.endpoint = endpoint
    
    def get_embedding_model(self, **kwargs):
        """Get Ollama embedding model."""
        try:
            from langchain_ollama import OllamaEmbeddings
            model = kwargs.get('model', 'nomic-embed-text:latest')
            return OllamaEmbeddings(model=model, base_url=self.endpoint)
        except ImportError:
            raise ImportError("langchain_ollama not installed. Install with: pip install langchain_ollama")
    
    def get_llm_model(self, **kwargs):
        """Get Ollama LLM model."""
        try:
            from langchain_ollama import ChatOllama
            model = kwargs.get('model', 'llama3.1:latest')
            return ChatOllama(model=model, base_url=self.endpoint)
        except ImportError:
            raise ImportError("langchain_ollama not installed. Install with: pip install langchain_ollama")
    
    def check_availability(self, **kwargs) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_info(self) -> Dict[str, str]:
        """Get Ollama provider info."""
        return {
            "name": "Ollama",
            "description": "Local LLM server with easy model management",
            "type": "local"
        }

class HuggingFaceProvider(ModelProvider):
    """Hugging Face provider implementation using local models."""
    
    def __init__(self, embedding_model: str = "sentence-transformers/paraphrase-MiniLM-L3-v2", 
                 llm_model: str = "microsoft/DialoGPT-small"):
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        self._downloaded_models = set()
        
        # CRITICAL FIX: Add in-memory caching to prevent reloading
        self._embedding_instances = {}
        self._llm_instances = {}
        
        # Set custom cache directory in user's home folder
        import os
        username = os.getenv('USER') or os.getenv('USERNAME') or 'unknown'
        self.cache_dir = f"/Users/{username}/codebase-qa/huggingface"
        
        # Create the directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Set environment variables for Hugging Face to use our custom cache
        os.environ['HF_HOME'] = self.cache_dir
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(self.cache_dir, 'sentence_transformers')
        
        log_to_sublog(".", "model_provider.log", f"📁 Using custom cache directory: {self.cache_dir}")
    
    def _ensure_model_downloaded(self, model_name: str, model_type: str = "model"):
        """Ensure a model is downloaded locally to custom cache directory."""
        if model_name in self._downloaded_models:
            log_to_sublog(".", "model_provider.log", f"✅ Model already loaded: {model_name}")
            return
        
        try:
            # Check if model is already in cache directory
            if model_type == "embedding":
                from sentence_transformers import SentenceTransformer
                import torch
                import os
                
                # Check if the model files exist in cache
                model_cache_path = os.path.join(self.cache_dir, "models--" + model_name.replace("/", "--"))
                if os.path.exists(model_cache_path):
                    log_to_sublog(".", "model_provider.log", f"✅ Model already cached: {model_name} in {model_cache_path}")
                    # Try to load the cached model to verify it works
                    try:
                        # Use device="cpu" to avoid meta tensor issues
                        model = SentenceTransformer(model_name, cache_folder=self.cache_dir, device="cpu")
                        log_to_sublog(".", "model_provider.log", f"✅ Successfully loaded cached embedding model: {model_name}")
                        self._downloaded_models.add(model_name)
                        return
                    except Exception as load_error:
                        log_to_sublog(".", "model_provider.log", f"⚠️ Cached model load failed, will re-download: {load_error}")
                
                log_to_sublog(".", "model_provider.log", f"📥 Downloading embedding model: {model_name} to {self.cache_dir}")
                
                try:
                    # Try with explicit CPU device first to avoid meta tensor issues
                    model = SentenceTransformer(model_name, cache_folder=self.cache_dir, device="cpu")
                    log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir}")
                except Exception as cpu_error:
                    log_to_sublog(".", "model_provider.log", f"⚠️ CPU device failed, trying default: {cpu_error}")
                    try:
                        # Fallback to default device handling
                        model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir} (default device)")
                    except Exception as default_error:
                        log_to_sublog(".", "model_provider.log", f"⚠️ Default device failed, trying minimal config: {default_error}")
                        # Last resort: minimal configuration without device specification
                        model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir} (minimal config)")
            else:  # LLM model
                from transformers import AutoTokenizer, AutoModelForCausalLM
                import torch
                import os
                
                # Check if the model files exist in cache
                model_cache_path = os.path.join(self.cache_dir, "models--" + model_name.replace("/", "--"))
                if os.path.exists(model_cache_path):
                    log_to_sublog(".", "model_provider.log", f"✅ Model already cached: {model_name} in {model_cache_path}")
                    # Try to load the cached model to verify it works
                    try:
                        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=self.cache_dir)
                        model = AutoModelForCausalLM.from_pretrained(
                            model_name, 
                            cache_dir=self.cache_dir,
                            torch_dtype=torch.float32,
                            device_map="cpu",
                            low_cpu_mem_usage=True,
                            trust_remote_code=True
                        )
                        log_to_sublog(".", "model_provider.log", f"✅ Successfully loaded cached LLM model: {model_name}")
                        self._downloaded_models.add(model_name)
                        return
                    except Exception as load_error:
                        log_to_sublog(".", "model_provider.log", f"⚠️ Cached model load failed, will re-download: {load_error}")
                
                log_to_sublog(".", "model_provider.log", f"📥 Downloading LLM model: {model_name} to {self.cache_dir}")
                
                # Download tokenizer and model to custom cache directory
                tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=self.cache_dir)
                
                # Use safer model loading approach to avoid meta tensor issues
                try:
                    # First try with device_map="cpu" and low_cpu_mem_usage=True
                    model = AutoModelForCausalLM.from_pretrained(
                        model_name, 
                        cache_dir=self.cache_dir,
                        torch_dtype=torch.float32,  # Use float32 to avoid precision issues
                        device_map="cpu",  # Force CPU usage
                        low_cpu_mem_usage=True,  # Reduce memory usage
                        trust_remote_code=True  # Trust remote code for better compatibility
                    )
                    log_to_sublog(".", "model_provider.log", f"✅ Downloaded LLM model: {model_name} to {self.cache_dir} (device_map=cpu)")
                except Exception as e:
                    log_to_sublog(".", "model_provider.log", f"⚠️ device_map=cpu failed, trying manual CPU placement: {e}")
                    try:
                        # Fallback: load without device_map and manually place on CPU
                        model = AutoModelForCausalLM.from_pretrained(
                            model_name, 
                            cache_dir=self.cache_dir,
                            torch_dtype=torch.float32,
                            low_cpu_mem_usage=True,
                            trust_remote_code=True
                        )
                        # Only call .to(device) if the model supports it and isn't already on CPU
                        if hasattr(model, 'to') and hasattr(model, 'device'):
                            current_device = next(model.parameters()).device
                            if current_device.type != 'cpu':
                                model = model.to(torch.device("cpu"))
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded LLM model: {model_name} to {self.cache_dir} (manual CPU)")
                    except Exception as manual_error:
                        log_to_sublog(".", "model_provider.log", f"⚠️ Manual CPU placement failed, trying minimal config: {manual_error}")
                        # Last resort: minimal configuration
                        model = AutoModelForCausalLM.from_pretrained(
                            model_name, 
                            cache_dir=self.cache_dir,
                            torch_dtype=torch.float32,
                            trust_remote_code=True
                        )
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded LLM model: {model_name} to {self.cache_dir} (minimal config)")
                
                log_to_sublog(".", "model_provider.log", f"✅ Downloaded LLM model: {model_name} to {self.cache_dir}")
            
            self._downloaded_models.add(model_name)
            
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to download {model_type} {model_name}: {e}")
            raise Exception(f"Failed to download {model_type} {model_name}: {e}")


    """
    Updated model_provider.py with Meta Tensor Fix

    Replace the get_embedding_model and _ensure_model_downloaded methods in the HuggingFaceProvider class
    with these implementations to fix the PyTorch meta tensor issue.
    """

    # Replace the entire get_embedding_model method in HuggingFaceProvider class:
    
    def get_embedding_model(self, **kwargs):
        """Get Hugging Face embedding model from custom cache — memoized."""
        # CRITICAL FIX: Check in-memory cache first
        model_name = kwargs.get('model', self.embedding_model)
        if model_name in self._embedding_instances:
            log_to_sublog(".", "model_provider.log", f"✅ Returning cached embedding model: {model_name}")
            return self._embedding_instances[model_name]
        
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            import os
            
            # Check if model is already in cache directory
            model_cache_path = os.path.join(self.cache_dir, "models--" + model_name.replace("/", "--"))
            if os.path.exists(model_cache_path):
                log_to_sublog(".", "model_provider.log", f"✅ Model already cached: {model_name} in {model_cache_path}")
                # Try to load the cached model to verify it works
                try:
                    # Use device="cpu" to avoid meta tensor issues
                    model = SentenceTransformer(model_name, cache_folder=self.cache_dir, device="cpu")
                    log_to_sublog(".", "model_provider.log", f"✅ Successfully loaded cached embedding model: {model_name}")
                    # self._downloaded_models.add(model_name)
                    
                    # CRITICAL FIX: Cache the model instance in memory
                    # self._embedding_instances[model_name] = model
                    # log_to_sublog(".", "model_provider.log", f"✅ Cached embedding model in memory: {model_name}")
                    # return model
                except Exception as load_error:
                    log_to_sublog(".", "model_provider.log", f"⚠️ Cached model load failed, will re-download: {load_error}")
            else:
            
                log_to_sublog(".", "model_provider.log", f"📥 Downloading embedding model: {model_name} to {self.cache_dir}")
                try:
                    # Try with explicit CPU device first to avoid meta tensor issues
                    model = SentenceTransformer(model_name, cache_folder=self.cache_dir, device="cpu")
                    log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir}")
                except Exception as cpu_error:
                    log_to_sublog(".", "model_provider.log", f"⚠️ CPU device failed, trying default: {cpu_error}")
                    try:
                        # Fallback to default device handling
                        model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir} (default device)")
                    except Exception as default_error:
                        log_to_sublog(".", "model_provider.log", f"⚠️ Default device failed, trying minimal config: {default_error}")
                        # Last resort: minimal configuration without device specification
                        model = SentenceTransformer(model_name, cache_folder=self.cache_dir)
                        log_to_sublog(".", "model_provider.log", f"✅ Downloaded embedding model: {model_name} to {self.cache_dir} (minimal config)")
            
            # # CRITICAL FIX: Cache the model instance in memory
            # self._embedding_instances[model_name] = model
            # self._downloaded_models.add(model_name)
            # log_to_sublog(".", "model_provider.log", f"✅ Cached embedding model in memory: {model_name}")
            
            class LocalHuggingFaceEmbeddings:
                """Wrapper class for Hugging Face embedding models with proper interface."""
                
                def __init__(self, model, model_name: str):
                    self.model = model
                    self.model_name = model_name
                    log_to_sublog(".", "model_provider.log", f"✅ Embedding wrapper created for: {model_name}")

                def embed_documents(self, texts):
                    try:
                        self.model.eval()
                        with torch.no_grad():
                            # Ensure texts is a list
                            if isinstance(texts, str):
                                texts = [texts]
                            
                            # Get embeddings - this returns numpy array or list
                            embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=False)
                            
                            # Convert to proper format: list of lists (each inner list is one document's embedding)
                            if hasattr(embeddings, 'tolist'):
                                result = embeddings.tolist()
                            else:
                                result = embeddings
                            
                            # Ensure we have a list of lists format
                            if len(texts) == 1 and isinstance(result[0], (int, float)):
                                # Single document case: wrap the single embedding in a list
                                result = [result]
                            
                            log_to_sublog(".", "model_provider.log", f"✅ Embedded {len(texts)} documents, shape: {len(result)}x{len(result[0]) if result else 0}")
                            return result
                            
                    except Exception as e:
                        log_to_sublog(".", "model_provider.log", f"❌ Error embedding documents: {e}")
                        raise RuntimeError(f"Embedding documents failed: {e}")

                def embed_query(self, text):
                    try:
                        self.model.eval()
                        with torch.no_grad():
                            # Get embedding for single text - this returns numpy array or list
                            embedding = self.model.encode(text, convert_to_tensor=False, show_progress_bar=False)
                            
                            # Convert to flat list format (single embedding vector)
                            if hasattr(embedding, 'tolist'):
                                result = embedding.tolist()
                            else:
                                result = embedding
                            
                            # Ensure result is a flat list, not nested
                            if isinstance(result, list) and len(result) > 0 and isinstance(result, list):
                                # If it's nested, flatten it (take first element if it's a list of one embedding)
                                result = result
                            
                            log_to_sublog(".", "model_provider.log", f"✅ Embedded query, dimension: {len(result) if isinstance(result, list) else 'unknown'}")
                            return result
                            
                    except Exception as e:
                        log_to_sublog(".", "model_provider.log", f"❌ Error embedding query: {e}")
                        raise RuntimeError(f"Embedding query failed: {e}")


            # Create and return the embedding wrapper
            embedding_wrapper = LocalHuggingFaceEmbeddings(model, model_name)
            self._embedding_instances[model_name] = embedding_wrapper
            self._downloaded_models.add(model_name)
            return embedding_wrapper
            
        except ImportError:
            raise ImportError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to initialize embedding model: {e}")
            raise Exception(f"Failed to initialize embedding model: {e}")


    def get_llm_model(self, **kwargs):
        """Get Hugging Face LLM model (open, ungated) from custom cache — memoized."""
        # CRITICAL FIX: Check in-memory cache first
        model_name = kwargs.get('model', self.llm_model)
        if model_name in self._llm_instances:
            log_to_sublog(".", "model_provider.log", f"✅ Returning cached LLM model: {model_name}")
            return self._llm_instances[model_name]

        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM
            import torch
            from langchain_core.language_models.llms import LLM
            from langchain_core.callbacks.manager import CallbackManagerForLLMRun
            from typing import Any, List, Optional

            self._ensure_model_downloaded(model_name, "llm")

            class LocalHuggingFaceLLM(LLM):
                # Declare all attributes as class fields for Pydantic
                model_name: str
                cache_dir: str
                _tokenizer: Any = None
                _model: Any = None
                
                def __init__(self, model_name: str, cache_dir: str, **kwargs):
                    super().__init__(model_name=model_name, cache_dir=cache_dir, **kwargs)
                    
                    log_to_sublog(".", "model_provider.log", f"🔄 Loading LLM model: {model_name}")
                    log_to_sublog(".", "model_provider.log", f"⏳ This may take 30-60 seconds for large models...")
                    
                    # Load tokenizer and model (this is where "Loading checkpoint shards" appears)
                    self._tokenizer = AutoTokenizer.from_pretrained(
                        model_name, cache_dir=cache_dir, trust_remote_code=True
                    )
                    
                    log_to_sublog(".", "model_provider.log", f"📥 Loading model weights (checkpoint shards)...")
                    
                    self._model = AutoModelForCausalLM.from_pretrained(
                        model_name,
                        cache_dir=cache_dir,
                        torch_dtype=torch.float32,
                        device_map="cpu",
                        low_cpu_mem_usage=True,
                        trust_remote_code=True
                    )
                    
                    if self._tokenizer.pad_token is None:
                        self._tokenizer.pad_token = self._tokenizer.eos_token
                    
                    log_to_sublog(".", "model_provider.log", f"✅ LLM model loaded successfully: {model_name}")


                @property
                def _llm_type(self) -> str:
                    return "huggingface"

                def _call(self, prompt: str, stop: Optional[List[str]] = None,
                        run_manager: Optional[CallbackManagerForLLMRun] = None, **kwargs: Any) -> str:
                    try:
                        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
                        with torch.no_grad():
                            outputs = self._model.generate(
                                **inputs,
                                max_length=inputs["input_ids"].shape[1] + kwargs.get("max_new_tokens", 512),
                                temperature=kwargs.get("temperature", 0.7),
                                do_sample=True,
                                pad_token_id=self._tokenizer.eos_token_id
                            )
                        txt = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
                        return txt[len(prompt):].strip() if txt.startswith(prompt) else txt.strip()
                    except Exception as e:
                        log_to_sublog(".", "model_provider.log", f"❌ Error in LLM generation: {e}")
                        return f"Error generating response: {str(e)}"


            # Create and cache the LLM instance
            llm_instance = LocalHuggingFaceLLM(model_name=model_name, cache_dir=self.cache_dir)
            self._llm_instances[model_name] = llm_instance
            self._downloaded_models.add(model_name)
            log_to_sublog(".", "model_provider.log", f"✅ Cached LLM model in memory: {model_name}")
            return llm_instance
            
        except ImportError:
            raise ImportError("transformers not installed. Install with: pip install transformers")
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to initialize LLM model: {e}")
            raise Exception(f"Failed to initialize LLM model: {e}")


    def check_availability(self, **kwargs) -> bool:
        """
        Lightweight availability check for Hugging Face provider.
        Ensures required libraries are available and verifies that the embedding model
        can be loaded from cache if it exists. LLM presence is NOT enforced at this stage,
        so missing models will be downloaded on demand in get_embedding_model/get_llm_model.
        """
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
            import transformers  # noqa: F401
            import torch  # noqa: F401
            import os

            model_name = self.embedding_model
            model_cache_path = os.path.join(self.cache_dir, "models--" + model_name.replace("/", "--"))
            if os.path.exists(model_cache_path):
                try:
                    _ = SentenceTransformer(
                        model_name,
                        cache_folder=self.cache_dir,
                        device="cpu",
                        local_files_only=True,
                        trust_remote_code=True
                    )
                    log_to_sublog(".", "model_provider.log",
                                f"✅ HF availability: cache-only embedding load OK for {model_name}")
                except Exception as e:
                    log_to_sublog(".", "model_provider.log",
                                f"⚠️ HF availability: cache exists but failed to load: {e}")
                    # Still OK; a clean re-download will be attempted on demand.
            else:
                log_to_sublog(".", "model_provider.log",
                            f"ℹ️ HF availability: embedding not cached yet — will download on demand")

            log_to_sublog(".", "model_provider.log",
                        "ℹ️ HF availability: skipping LLM pre-check (on-demand download allowed)")
            return True
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ HF availability check failed: {e}")
            return False



    def download_all_models(self):
        """Download all configured models to custom cache directory."""
        try:
            log_to_sublog(".", "model_provider.log", f"🚀 Starting model downloads to {self.cache_dir}...")
            
            # Download embedding model
            self._ensure_model_downloaded(self.embedding_model, "embedding")
            
            # Download LLM model
            self._ensure_model_downloaded(self.llm_model, "llm")
            
            log_to_sublog(".", "model_provider.log", f"✅ All models downloaded successfully to {self.cache_dir}")
            return True
            
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"❌ Failed to download models: {e}")
            return False
    
    def clear_cache(self):
        """Clear the in-memory model cache to free memory."""
        log_to_sublog(".", "model_provider.log", "🗑️ Clearing Hugging Face model cache...")
        self._embedding_instances.clear()
        self._llm_instances.clear()
        self._downloaded_models.clear()
        log_to_sublog(".", "model_provider.log", "✅ Hugging Face model cache cleared")

    def get_cache_info(self):
        """Get information about the custom cache directory."""
        import os
        return {
            "cache_directory": self.cache_dir,
            "exists": os.path.exists(self.cache_dir),
            "size": 0,  # Simplified - not calculating complex sizes
            "models": list(self._downloaded_models),
            "cached_instances": {
                "embeddings": list(self._embedding_instances.keys()),
                "llms": list(self._llm_instances.keys())
            }
        }
    
    def _get_directory_size(self, path):
        """Calculate directory size in bytes."""
        import os
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except:
            pass
        return total_size
    
    def get_info(self) -> Dict[str, str]:
        """Get Hugging Face provider info."""
        return {
            "name": "Hugging Face",
            "description": "Local open-source models for NLP tasks",
            "type": "local",
            "cache_directory": self.cache_dir
        }

class ModelProviderFactory:
    """Factory for creating model providers."""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """Register a provider class."""
        cls._providers[name.lower()] = provider_class
    
    @classmethod
    def create_provider(cls, provider_type: str, **kwargs) -> ModelProvider:
        """Create a provider instance."""
        provider_type = provider_type.lower()
        
        if provider_type == "ollama":
            return OllamaProvider(**kwargs)
        elif provider_type == "huggingface":
            return HuggingFaceProvider(**kwargs)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
        return ["ollama", "huggingface"]

# Register default providers
ModelProviderFactory.register_provider("ollama", OllamaProvider)
ModelProviderFactory.register_provider("huggingface", HuggingFaceProvider)

# Global provider management
_current_provider = None
_current_provider_type = "ollama"

def set_provider(provider_type: str, **kwargs):
    """Set the current model provider."""
    global _current_provider, _current_provider_type
    
    try:
        log_to_sublog(".", "model_provider.log", f"🔄 Setting provider to: {provider_type}")
        log_to_sublog(".", "model_provider.log", f"📋 Provider arguments: {kwargs}")
        
        # CRITICAL FIX: Clear cache when switching providers to prevent memory issues
        if _current_provider and hasattr(_current_provider, 'clear_cache'):
            log_to_sublog(".", "model_provider.log", "🗑️ Clearing previous provider cache...")
            _current_provider.clear_cache()
        
        _current_provider = ModelProviderFactory.create_provider(provider_type, **kwargs)
        _current_provider_type = provider_type
        
        # Test the provider to ensure it's working
        if hasattr(_current_provider, 'check_availability'):
            if _current_provider.check_availability(**kwargs):
                log_to_sublog(".", "model_provider.log", f"✅ Provider {provider_type} set successfully and verified working")
            else:
                log_to_sublog(".", "model_provider.log", f"⚠️ Provider {provider_type} set but availability check failed")
        else:
            log_to_sublog(".", "model_provider.log", f"✅ Provider {provider_type} set successfully")
            
    except Exception as e:
        log_to_sublog(".", "model_provider.log", f"❌ Failed to set provider {provider_type}: {e}")
        log_to_sublog(".", "model_provider.log", f"🔧 Falling back to Ollama provider")
        
        # Fallback to Ollama provider
        try:
            _current_provider = ModelProviderFactory.create_provider("ollama", endpoint="http://localhost:11434")
            _current_provider_type = "ollama"
            log_to_sublog(".", "model_provider.log", f"✅ Fallback to Ollama provider successful")
        except Exception as fallback_error:
            log_to_sublog(".", "model_provider.log", f"❌ Fallback to Ollama also failed: {fallback_error}")
            raise Exception(f"Failed to set provider {provider_type} and fallback failed: {e}")

def force_provider_initialization(provider_type: str, **kwargs):
    """Force provider initialization with retry logic."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            log_to_sublog(".", "model_provider.log", f"🔄 Force initializing provider {provider_type} (attempt {attempt + 1}/{max_retries})")
            set_provider(provider_type, **kwargs)
            return True
        except Exception as e:
            log_to_sublog(".", "model_provider.log", f"⚠️ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                import time
                time.sleep(1)  # Wait before retry
            else:
                log_to_sublog(".", "model_provider.log", f"❌ All {max_retries} attempts failed")
                raise e
    return False

def get_current_provider() -> ModelProvider:
    """Get the current model provider."""
    global _current_provider
    if _current_provider is None:
        # Initialize with default Ollama provider
        set_provider("ollama")
    return _current_provider

def get_current_provider_type() -> str:
    """Get the current provider type."""
    global _current_provider_type
    return _current_provider_type
