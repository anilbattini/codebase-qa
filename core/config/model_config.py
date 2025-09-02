"""
model_config.py

Centralized model configuration management including cloud provider support.
Single source of truth for all model settings across the application.
Follows clean code principles with getters/setters and proper encapsulation.
"""

import os
from typing import Dict, Any, Optional

from custom_llm_client import CustomLLMClient
from langchain.prompts import PromptTemplate
from logger import log_highlight

class ModelConfig:
    """
    Centralized model configuration management with cloud provider support.
    Single source of truth for all model settings across the application.
    """

    def __init__(self):
        """Initialize with default values."""
        self.reset_to_defaults()
        
    def reset_to_defaults(self):
        """Reset all model settings to defaults - single source of truth."""
        # Default model settings
        self._ollama_model = "llama3.1:latest"
        self._embedding_model = "nomic-embed-text:latest"
        self._ollama_endpoint = "http://localhost:11434"
        self._chunk_size = 1000
        self._chunk_overlap = 200
        self._search_k = 5
        
        # Provider and cloud configuration
        self._provider = None  # No default - user must choose
        self._cloud_endpoint = None  # User selection overrides env
        self._cloud_api_key = os.getenv("CLOUD_API_KEY", None)
        self._cloud_model = "gpt-4.1"  # Hardcoded as requested
        
        # LLM Configuration parameters
        self._max_tokens = 2000
        self._temperature = 0.1
        self._streaming = False
        
        log_highlight("ModelConfig: Reset to defaults")
        
    # NEW: LLM Parameters Configuration
    def get_max_tokens(self) -> int:
        return self._max_tokens
    
    def set_max_tokens(self, value: int):
        self._max_tokens = value
        log_highlight(f"ModelConfig: Set max_tokens to {value}")
    
    def get_temperature(self) -> float:
        return self._temperature
    
    def set_temperature(self, value: float):
        self._temperature = value
        log_highlight(f"ModelConfig: Set temperature to {value}")
    
    def get_streaming(self) -> bool:
        return self._streaming
    
    def set_streaming(self, value: bool):
        self._streaming = value
        log_highlight(f"ModelConfig: Set streaming to {value}")
    
    # Add this import at the top of model_config.py
    from custom_llm_client import CustomLLMClient

    def get_llm(self, **overrides):
        """
        Returns a properly configured LLM client based on current provider.
        Now supports CustomLLMClient for cloud providers with Runnable compatibility.
        """
        provider = self.get_provider()
        if provider is None:
            raise ValueError("No provider selected. User must choose provider first.")

        # Extract common overrides
        model_override = overrides.pop('model', None)
        endpoint_override = overrides.pop('endpoint', None)
        
        if provider == 'ollama':
            from langchain_ollama import ChatOllama
            
            model = model_override or self.get_ollama_model()
            endpoint = endpoint_override or self.get_ollama_endpoint()
            
            params = {
                'model': model,
                'base_url': endpoint
            }
            params.update(overrides)
            
            log_highlight(f"ModelConfig: Creating Ollama LLM - {model} at {endpoint}")
            return ChatOllama(**params)
            
        elif provider == 'cloud':
            # 🆕 NEW: Use Runnable-compatible CustomLLMClient
            from custom_llm_client import CustomLLMClient
            
            api_key = self.get_cloud_api_key()
            if not api_key:
                raise ValueError("CLOUD_API_KEY environment variable not set")
                
            endpoint = endpoint_override or self.get_cloud_endpoint()
            if not endpoint:
                raise ValueError("Cloud endpoint not configured")
                
            model = model_override or self.get_cloud_model()
            
            # Extract parameters for CustomLLMClient
            max_tokens = overrides.pop('max_tokens', self.get_max_tokens())
            temperature = overrides.pop('temperature', self.get_temperature())
            
            log_highlight(f"ModelConfig: Creating Runnable CustomLLMClient - {model} at {endpoint}")
            
            return CustomLLMClient(
                endpoint=endpoint,
                api_key=api_key,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                project_dir=getattr(self, 'project_dir', '.')
            )
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")


    def get_rewrite_llm(self, **overrides):
        """
        Get LLM specifically for query rewriting.

        Always uses local Ollama, regardless of the main provider selection.
        """
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            raise ImportError("langchain_ollama package required for rewrite LLM. Install with: pip install langchain-ollama")

        model = overrides.pop('model', self.get_ollama_model())
        endpoint = overrides.pop('endpoint', self.get_ollama_endpoint())

        params = {
            'model': model,
            'base_url': endpoint,
        }
        params.update(overrides)

        log_highlight(f"ModelConfig: Creating Rewrite LLM (Ollama) - {model} at {endpoint}")
        return ChatOllama(**params)


    def create_rewrite_chain(self, rewrite_llm, intent, project_type):
        """Enhanced rewrite chain that preserves code entities."""
        prompt = PromptTemplate(
            input_variables=["question"],
            template=(
                f"Convert this question into search terms for a {project_type} codebase.\n\n"
                f"Intent: {intent}\n"
                "Question: {question}\n\n"
                "CRITICAL RULES:\n"
                "Return ONLY the search terms, nothing else.\n"
                "NO explanations, NO formatting, NO additional text.\n\n"
                "Example queries converted to search terms:\n"
                "- 'Where is UserService called?' → 'UserService called usage'\n"
                "- 'How does DatabaseManager work?' → 'DatabaseManager implementation'\n"
                "- 'What does auth_helper.py do?' → 'auth_helper.py functionality'\n\n"
                "- 'Where is login screen?' → 'LoginScreen composable activity'\n"
                "- 'What does UserService do?' → 'UserService purpose functionality implementation'\n"
                "- 'Where is MainActivity defined?' → 'MainActivity class definition location file'\n"
                "- 'How does auth work?' → 'authentication process workflow implementation'\n\n"
            ),
        )
        return prompt | rewrite_llm


    # Existing Ollama Model methods
    @property
    def ollama_model(self) -> str:
        return self._ollama_model

    @ollama_model.setter
    def ollama_model(self, value: str):
        self._ollama_model = value

    def get_ollama_model(self) -> str:
        return self._ollama_model

    def set_ollama_model(self, value: str):
        self._ollama_model = value
        log_highlight(f"ModelConfig: Set Ollama model to {value}")

    # Existing Embedding Model methods
    @property
    def embedding_model(self) -> str:
        return self._embedding_model

    @embedding_model.setter
    def embedding_model(self, value: str):
        self._embedding_model = value

    def get_embedding_model(self) -> str:
        return self._embedding_model

    def set_embedding_model(self, value: str):
        self._embedding_model = value
        log_highlight(f"ModelConfig: Set embedding model to {value}")

    # Existing Ollama Endpoint methods
    @property
    def ollama_endpoint(self) -> str:
        return self._ollama_endpoint

    @ollama_endpoint.setter
    def ollama_endpoint(self, value: str):
        self._ollama_endpoint = value

    def get_ollama_endpoint(self) -> str:
        return self._ollama_endpoint

    def set_ollama_endpoint(self, value: str):
        self._ollama_endpoint = value
        log_highlight(f"ModelConfig: Set Ollama endpoint to {value}")

    # NEW: Provider Configuration
    def get_provider(self) -> Optional[str]:
        """Get the current provider selection (ollama or cloud)."""
        return self._provider

    def set_provider(self, provider: str):
        """Set the provider (ollama or cloud)."""
        if provider not in ["ollama", "cloud"]:
            raise ValueError("Provider must be 'ollama' or 'cloud'")
        self._provider = provider
        log_highlight(f"ModelConfig: Set provider to {provider}")

    # NEW: Cloud Endpoint Configuration
    def get_cloud_endpoint(self) -> Optional[str]:
        """Get cloud endpoint - user selection overrides env variable."""
        if self._cloud_endpoint:
            return self._cloud_endpoint
        return os.getenv("CLOUD_ENDPOINT", None)

    def set_cloud_endpoint(self, endpoint: str):
        """Set cloud endpoint - overrides env variable."""
        self._cloud_endpoint = endpoint
        log_highlight(f"ModelConfig: Set cloud endpoint to {endpoint}")

    # NEW: Cloud API Key (always from env)
    def get_cloud_api_key(self) -> str:
        """Get cloud API key from environment variable."""
        if self._cloud_api_key:
            return self._cloud_api_key
        return os.getenv("CLOUD_API_KEY", None)

    # NEW: Cloud Model Configuration
    def get_cloud_model(self) -> str:
        """Get cloud model name (hardcoded gpt-4.1)."""
        return self._cloud_model

    # Existing Chunk Size methods
    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    @chunk_size.setter
    def chunk_size(self, value: int):
        self._chunk_size = value

    def get_chunk_size(self) -> int:
        return self._chunk_size

    def set_chunk_size(self, value: int):
        self._chunk_size = value

    # Existing Chunk Overlap methods
    @property
    def chunk_overlap(self) -> int:
        return self._chunk_overlap

    @chunk_overlap.setter
    def chunk_overlap(self, value: int):
        self._chunk_overlap = value

    def get_chunk_overlap(self) -> int:
        return self._chunk_overlap

    def set_chunk_overlap(self, value: int):
        self._chunk_overlap = value

    # Existing Search K methods
    @property
    def search_k(self) -> int:
        return self._search_k

    @search_k.setter
    def search_k(self, value: int):
        self._search_k = value

    def get_search_k(self) -> int:
        return self._search_k

    def set_search_k(self, value: int):
        self._search_k = value

    # NEW: Active Configuration Helper
    def get_active_llm_config(self) -> Dict[str, Any]:
        """Get configuration for the currently selected provider."""
        if self._provider == "ollama":
            return {
                "provider": "ollama",
                "model": self._ollama_model,
                "endpoint": self._ollama_endpoint
            }
        elif self._provider == "cloud":
            return {
                "provider": "cloud",
                "model": self.get_cloud_model(),
                "endpoint": self.get_cloud_endpoint(),
                "api_key": self.get_cloud_api_key()
            }
        else:
            raise ValueError("No provider selected. User must choose provider first.")

    # Existing convenience methods
    def get_all_config(self) -> Dict[str, Any]:
        """Get all model configuration as a dictionary."""
        return {
            "ollama_model": self._ollama_model,
            "embedding_model": self._embedding_model,
            "ollama_endpoint": self._ollama_endpoint,
            "chunk_size": self._chunk_size,
            "chunk_overlap": self._chunk_overlap,
            "search_k": self._search_k,
            "provider": self._provider,
            "cloud_endpoint": self.get_cloud_endpoint(),
            "cloud_model": self._cloud_model
        }

# Global model configuration instance
model_config = ModelConfig()
