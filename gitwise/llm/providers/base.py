"""Base provider interface for all LLM providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration.
        
        Args:
            config: Configuration dictionary containing API keys and settings
        """
        self.config = config
        self._validate_config()
    
    @abstractmethod
    def get_response(self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs) -> str:
        """Get response from the provider.
        
        Args:
            prompt_or_messages: Either a string prompt or list of message dicts
            **kwargs: Additional provider-specific parameters
            
        Returns:
            The response text from the LLM
            
        Raises:
            RuntimeError: If the API call fails
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider-specific configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider.
        
        Returns:
            List of model names/identifiers
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name.
        
        Returns:
            Provider name (e.g., 'openai', 'anthropic', 'google')
        """
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider.
        
        Returns:
            Default model name
        """
        pass
    
    def _validate_config(self) -> None:
        """Internal config validation that calls the abstract method.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not self.validate_config(self.config):
            raise ValueError(f"Invalid configuration for {self.provider_name} provider")
    
    def get_model(self) -> str:
        """Get the model to use for this provider.
        
        Returns:
            Model name from config or default
        """
        # Provider-specific model field (e.g., 'model', 'gemini_model', etc.)
        model_key = f"{self.provider_name}_model" if self.provider_name != "openrouter" else "openrouter_model"
        
        # Fallback chain: provider_model -> model -> default
        return (
            self.config.get(model_key) or 
            self.config.get("model") or 
            self.get_default_model()
        ) 