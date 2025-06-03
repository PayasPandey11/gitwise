"""Google Gemini provider implementation."""

import os
from typing import Dict, List, Union, Any

try:
    import google.generativeai as genai
    _HAS_GEMINI = True
except ImportError:
    _HAS_GEMINI = False

from .base import BaseLLMProvider
from ..models.gemini_models import AVAILABLE_GEMINI_MODELS, DEFAULT_GEMINI_MODEL


class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Gemini provider with configuration."""
        if not _HAS_GEMINI:
            raise ImportError(
                "Google Generative AI package not found. "
                "Install with: pip install google-generativeai"
            )
        
        super().__init__(config)
        self._client = None
        self._setup_client()
    
    def _setup_client(self) -> None:
        """Setup the Gemini client with API key."""
        api_key = self._get_api_key()
        genai.configure(api_key=api_key)
        
        # Test the connection by trying to list models
        try:
            # This is a lightweight way to validate the API key
            list(genai.list_models())
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini client: {e}")
    
    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        # Try config first, then environment
        api_key = (
            self.config.get("google_api_key") or 
            self.config.get("gemini_api_key") or 
            os.environ.get("GOOGLE_API_KEY") or
            os.environ.get("GEMINI_API_KEY")
        )
        
        if not api_key:
            raise ValueError(
                "Google/Gemini API key not found. Please set 'google_api_key' in config "
                "or GOOGLE_API_KEY/GEMINI_API_KEY environment variable."
            )
        
        return api_key
    
    def get_response(self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs) -> str:
        """Get response from Gemini.
        
        Args:
            prompt_or_messages: Either a string prompt or list of message dicts
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            The response text from Gemini
            
        Raises:
            RuntimeError: If the API call fails
        """
        try:
            model_name = self.get_model()
            model = genai.GenerativeModel(model_name)
            
            # Convert messages to prompt if needed
            if isinstance(prompt_or_messages, list):
                # Convert message format to simple prompt for now
                # TODO: Support proper conversation format
                prompt = self._messages_to_prompt(prompt_or_messages)
            else:
                prompt = prompt_or_messages
            
            # Set up generation config
            generation_config = self._build_generation_config(**kwargs)
            
            # Generate response
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                raise RuntimeError("Empty response from Gemini")
                
            return response.text.strip()
            
        except Exception as e:
            if "API_KEY_INVALID" in str(e):
                raise RuntimeError(
                    "Invalid Google API key. Please check your API key in the Google AI Studio "
                    "or ensure you have access to the Gemini API."
                ) from e
            elif "PERMISSION_DENIED" in str(e):
                raise RuntimeError(
                    "Permission denied. Please ensure your API key has access to the Gemini API "
                    "and the requested model."
                ) from e
            else:
                raise RuntimeError(f"Gemini API error: {e}") from e
    
    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert message format to a simple prompt.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Combined prompt string
        """
        # Simple conversion for now - just concatenate user messages
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt_parts.append(f"Instructions: {content}")
            elif role == "user":
                prompt_parts.append(content)
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        return "\n\n".join(prompt_parts)
    
    def _build_generation_config(self, **kwargs) -> genai.GenerationConfig:
        """Build generation configuration from kwargs.
        
        Args:
            **kwargs: Generation parameters
            
        Returns:
            GenerationConfig object
        """
        config_params = {}
        
        # Map common parameters
        if "temperature" in kwargs:
            config_params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            config_params["max_output_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            config_params["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            config_params["top_k"] = kwargs["top_k"]
            
        return genai.GenerationConfig(**config_params)
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Gemini-specific configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Check if API key is provided
        has_api_key = any([
            config.get("google_api_key"),
            config.get("gemini_api_key"),
            os.environ.get("GOOGLE_API_KEY"),
            os.environ.get("GEMINI_API_KEY")
        ])
        
        if not has_api_key:
            return False
        
        # Validate model if specified
        model = self.get_model()
        if model and not self._is_valid_model(model):
            return False
            
        return True
    
    def _is_valid_model(self, model_name: str) -> bool:
        """Check if model name is valid for Gemini.
        
        Args:
            model_name: Model name to validate
            
        Returns:
            True if valid, False otherwise
        """
        return model_name in AVAILABLE_GEMINI_MODELS
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models.
        
        Returns:
            List of available model names
        """
        return AVAILABLE_GEMINI_MODELS.copy()
    
    @property
    def provider_name(self) -> str:
        """Return the provider name.
        
        Returns:
            Provider name 'google'
        """
        return "google"
    
    def get_default_model(self) -> str:
        """Get the default Gemini model.
        
        Returns:
            Default model name
        """
        return DEFAULT_GEMINI_MODEL 