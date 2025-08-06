"""
model_config.py

Centralized model configuration management.
Single source of truth for all model settings across the application.
Follows clean code principles with getters/setters and proper encapsulation.
"""

from typing import Dict, Any


class ModelConfig:
    """
    Centralized model configuration management.
    Single source of truth for all model settings across the application.
    """
    
    def __init__(self):
        # Default model settings
        self._ollama_model = "llama3.1:latest"
        self._embedding_model = "nomic-embed-text:latest"
        self._ollama_endpoint = "http://localhost:11434"
        self._chunk_size = 1000
        self._chunk_overlap = 200
        self._search_k = 5
    
    # Ollama Model
    @property
    def ollama_model(self) -> str:
        """Get the current Ollama model name."""
        return self._ollama_model
    
    @ollama_model.setter
    def ollama_model(self, value: str):
        """Set the Ollama model name."""
        self._ollama_model = value
    
    def get_ollama_model(self) -> str:
        """Get the current Ollama model name."""
        return self._ollama_model
    
    def set_ollama_model(self, value: str):
        """Set the Ollama model name."""
        self._ollama_model = value
    
    # Embedding Model
    @property
    def embedding_model(self) -> str:
        """Get the current embedding model name."""
        return self._embedding_model
    
    @embedding_model.setter
    def embedding_model(self, value: str):
        """Set the embedding model name."""
        self._embedding_model = value
    
    def get_embedding_model(self) -> str:
        """Get the current embedding model name."""
        return self._embedding_model
    
    def set_embedding_model(self, value: str):
        """Set the embedding model name."""
        self._embedding_model = value
    
    # Ollama Endpoint
    @property
    def ollama_endpoint(self) -> str:
        """Get the current Ollama endpoint URL."""
        return self._ollama_endpoint
    
    @ollama_endpoint.setter
    def ollama_endpoint(self, value: str):
        """Set the Ollama endpoint URL."""
        self._ollama_endpoint = value
    
    def get_ollama_endpoint(self) -> str:
        """Get the current Ollama endpoint URL."""
        return self._ollama_endpoint
    
    def set_ollama_endpoint(self, value: str):
        """Set the Ollama endpoint URL."""
        self._ollama_endpoint = value
    
    # Chunk Size
    @property
    def chunk_size(self) -> int:
        """Get the current chunk size."""
        return self._chunk_size
    
    @chunk_size.setter
    def chunk_size(self, value: int):
        """Set the chunk size."""
        self._chunk_size = value
    
    def get_chunk_size(self) -> int:
        """Get the current chunk size."""
        return self._chunk_size
    
    def set_chunk_size(self, value: int):
        """Set the chunk size."""
        self._chunk_size = value
    
    # Chunk Overlap
    @property
    def chunk_overlap(self) -> int:
        """Get the current chunk overlap."""
        return self._chunk_overlap
    
    @chunk_overlap.setter
    def chunk_overlap(self, value: int):
        """Set the chunk overlap."""
        self._chunk_overlap = value
    
    def get_chunk_overlap(self) -> int:
        """Get the current chunk overlap."""
        return self._chunk_overlap
    
    def set_chunk_overlap(self, value: int):
        """Set the chunk overlap."""
        self._chunk_overlap = value
    
    # Search K
    @property
    def search_k(self) -> int:
        """Get the current search_k value."""
        return self._search_k
    
    @search_k.setter
    def search_k(self, value: int):
        """Set the search_k value."""
        self._search_k = value
    
    def get_search_k(self) -> int:
        """Get the current search_k value."""
        return self._search_k
    
    def set_search_k(self, value: int):
        """Set the search_k value."""
        self._search_k = value
    
    # Convenience methods
    def get_all_config(self) -> Dict[str, Any]:
        """Get all model configuration as a dictionary."""
        return {
            "ollama_model": self._ollama_model,
            "embedding_model": self._embedding_model,
            "ollama_endpoint": self._ollama_endpoint,
            "chunk_size": self._chunk_size,
            "chunk_overlap": self._chunk_overlap,
            "search_k": self._search_k
        }
    
    def set_all_config(self, config: Dict[str, Any]):
        """Set all model configuration from a dictionary."""
        if "ollama_model" in config:
            self._ollama_model = config["ollama_model"]
        if "embedding_model" in config:
            self._embedding_model = config["embedding_model"]
        if "ollama_endpoint" in config:
            self._ollama_endpoint = config["ollama_endpoint"]
        if "chunk_size" in config:
            self._chunk_size = config["chunk_size"]
        if "chunk_overlap" in config:
            self._chunk_overlap = config["chunk_overlap"]
        if "search_k" in config:
            self._search_k = config["search_k"]
    
    def reset_to_defaults(self):
        """Reset all model settings to defaults."""
        self._ollama_model = "llama3.1:latest"
        self._embedding_model = "nomic-embed-text:latest"
        self._ollama_endpoint = "http://localhost:11434"
        self._chunk_size = 1000
        self._chunk_overlap = 200
        self._search_k = 5


# Global model configuration instance
model_config = ModelConfig() 