"""OpenRouter provider for GitWise LLM system."""

from typing import Dict, Union, List, Any
from .base import BaseLLMProvider


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider using legacy online.py implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenRouter provider.
        
        Args:
            config: Configuration dictionary containing API keys and settings
        """
        super().__init__(config)
    
    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "openrouter"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenRouter-specific configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        # Check if OpenRouter API key is present and valid format
        api_key = config.get("openrouter_api_key")
        if not api_key:
            return False
        
        # OpenRouter API keys should start with "sk-or-"
        if not api_key.startswith("sk-or-"):
            return False
            
        return True
    
    def get_available_models(self) -> List[str]:
        """Get list of available models for OpenRouter.
        
        Returns:
            List of popular OpenRouter model names
        """
        return [
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-3.7-sonnet",
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            "openai/gpt-3.5-turbo",
            "google/gemini-pro",
            "meta-llama/llama-2-70b-chat",
            "mistralai/mistral-7b-instruct"
        ]
    
    def get_default_model(self) -> str:
        """Get the default model for OpenRouter.
        
        Returns:
            Default OpenRouter model name
        """
        return "anthropic/claude-3-haiku"
    
    def get_response(self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs) -> str:
        """Get response from OpenRouter.
        
        Args:
            prompt_or_messages: Either a string prompt or list of message dictionaries
            **kwargs: Additional arguments (not used for OpenRouter)
            
        Returns:
            Response string from OpenRouter
            
        Raises:
            RuntimeError: If OpenRouter API call fails
        """
        try:
            # Import and use the legacy OpenRouter implementation
            from gitwise.llm.online import get_llm_response as legacy_online_llm
            return legacy_online_llm(prompt_or_messages, **kwargs)
        except Exception as e:
            raise RuntimeError(f"OpenRouter provider error: {str(e)}") from e 