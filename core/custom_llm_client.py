# core/custom_llm_client.py

import json
import requests
from typing import Dict, Any, List, Optional, Union
from langchain.schema.runnable import Runnable
from logger import log_to_sublog

class CustomLLMClient(Runnable):
    """
    Langchain-compatible OpenAI client with system/user prompt separation.
    Simple and clean implementation following OpenAI best practices.
    """
    
    def __init__(self, endpoint: str, api_key: str, model: str = "gpt-4", 
                 max_tokens: int = 2000, temperature: float = 0.1, 
                 project_dir: str = "."):
        """Initialize the custom LLM client with cloud provider settings."""
        super().__init__()  # Initialize Runnable
        
        self.endpoint = endpoint
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.project_dir = project_dir
        
        # Validate configuration
        if not self.api_key:
            raise ValueError("API key is required for cloud provider")
        if not self.endpoint:
            raise ValueError("Endpoint URL is required for cloud provider")
            
        log_to_sublog(self.project_dir, "custom_llm_client.log", 
                      f"CustomLLMClient initialized: {self.endpoint}, model={self.model}")

    def invoke(self, input_data, config=None, **kwargs):
        """
        🔧 FIXED: Handle Langchain's invoke signature properly.
        
        Args:
            input_ Can be string, dict, or custom object from Langchain chains
            config: Langchain config (unused)
            **kwargs: Additional parameters
            
        Returns:
            CustomLLMResponse object with .content attribute
        """
        # Extract the actual prompt from Langchain's input format
        if hasattr(input_data, 'to_string'):
            prompt_text = input_data.to_string()
        elif isinstance(input_data, dict):
            # Handle PromptValue or similar dict-like objects
            prompt_text = input_data.get('text', str(input_data))
        elif hasattr(input_data, 'text'):
            prompt_text = input_data.text
        else:
            prompt_text = str(input_data)
        
        log_to_sublog(self.project_dir, "custom_llm_client.log", 
                      f"Received input type: {type(input_data)}, prompt_length: {len(prompt_text)}")
        
        return self._process_prompt(prompt_text, **kwargs)

    def invoke_with_system_user(self, system_prompt: str, user_prompt: str, **kwargs):
        """
        🆕 NEW: Direct method for system/user prompt separation.
        Called directly from chat_handler.py for cloud provider.
        """
        messages = []
        
        if system_prompt and system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt.strip()})
            
        if user_prompt and user_prompt.strip():
            messages.append({"role": "user", "content": user_prompt.strip()})
        
        if not messages:
            raise ValueError("Either system_prompt or user_prompt must be provided")
        
        # Build OpenAI request
        request_payload = {
            "model": kwargs.get('model', self.model),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "stream": False
        }
        
        # Add additional parameters
        for key in ['top_p', 'frequency_penalty', 'presence_penalty', 'stop']:
            if key in kwargs:
                request_payload[key] = kwargs[key]
        
        log_to_sublog(self.project_dir, "custom_llm_client.log", 
                      f"System/User invoke: system_chars={len(system_prompt)}, user_chars={len(user_prompt)}")
        
        try:
            response_data = self._make_api_call(request_payload)
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                
                log_to_sublog(self.project_dir, "custom_llm_client.log", 
                              f"Response received: {len(content)} characters")
                
                return CustomLLMResponse(content=content, raw_response=response_data)
            else:
                raise RuntimeError("Invalid response format from cloud API")
                
        except Exception as e:
            log_to_sublog(self.project_dir, "custom_llm_client.log", f"Error: {e}")
            raise

    def _process_prompt(self, prompt_text: str, **kwargs):
        """Internal method for single prompt processing (fallback)."""
        messages = [{"role": "user", "content": prompt_text}]
        
        request_payload = {
            "model": kwargs.get('model', self.model),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "stream": False
        }
        
        try:
            response_data = self._make_api_call(request_payload)
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                content = response_data['choices'][0]['message']['content']
                return CustomLLMResponse(content=content, raw_response=response_data)
            else:
                raise RuntimeError("Invalid response format from cloud API")
                
        except Exception as e:
            log_to_sublog(self.project_dir, "custom_llm_client.log", f"Error: {e}")
            raise
    
    async def ainvoke(self, input_data, config=None, **kwargs):
        """Async version for Langchain compatibility."""
        import asyncio
        return await asyncio.to_thread(self.invoke, input_data, config, **kwargs)

    @property
    def _llm_type(self) -> str:
        return "custom_openai_compatible"

    def _make_api_call(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to cloud API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(
                self.endpoint, 
                json=request_payload, 
                headers=headers, 
                timeout=120
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            raise RuntimeError(f"Request timeout to cloud API: {self.endpoint}")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Request to cloud API failed: {e}")
        except json.JSONDecodeError:
            raise RuntimeError(f"Invalid JSON response from cloud API")


class CustomLLMResponse:
    """Response object mimicking Langchain format."""
    
    def __init__(self, content: str, raw_response: Dict[str, Any]):
        self.content = content
        self.raw_response = raw_response
        
    def __str__(self) -> str:
        return self.content
    
    def __repr__(self) -> str:
        return f"CustomLLMResponse(content='{self.content[:50]}...')"
