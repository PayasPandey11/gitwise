"""Provider registry and factory for LLM providers."""

from typing import Dict, Type, Optional
from .base import BaseLLMProvider


def _lazy_import_providers():
    """Lazy import providers to avoid import errors if dependencies are missing."""
    providers = {}
    
    # Import Gemini provider
    try:
        from .gemini_provider import GeminiProvider
        providers["google"] = GeminiProvider
    except ImportError:
        pass  # Gemini dependencies not available
    
    # Import OpenAI provider
    try:
        from .openai_provider import OpenAIProvider
        providers["openai"] = OpenAIProvider
    except ImportError:
        pass  # OpenAI dependencies not available
    
    # Import Claude provider
    try:
        from .anthropic_provider import AnthropicProvider
        providers["anthropic"] = AnthropicProvider
    except ImportError:
        pass  # Anthropic dependencies not available
    
    # Import OpenRouter provider (when converted)
    try:
        from .openrouter_provider import OpenRouterProvider
        providers["openrouter"] = OpenRouterProvider
    except ImportError:
        pass  # Will be converted from existing online.py
    
    return providers


def get_provider_registry() -> Dict[str, Type[BaseLLMProvider]]:
    """Get the registry of available providers.
    
    Returns:
        Dictionary mapping provider names to provider classes
    """
    return _lazy_import_providers()


def get_available_providers() -> list[str]:
    """Get list of available provider names.
    
    Returns:
        List of provider names that can be instantiated
    """
    return list(get_provider_registry().keys())


def get_provider(provider_name: str, config: Dict) -> BaseLLMProvider:
    """Factory function to get configured provider instance.
    
    Args:
        provider_name: Name of the provider ('google', 'openai', 'anthropic', 'openrouter')
        config: Configuration dictionary
        
    Returns:
        Configured provider instance
        
    Raises:
        ValueError: If provider is unknown or not available
        ImportError: If provider dependencies are not installed
    """
    registry = get_provider_registry()
    
    if provider_name not in registry:
        available = ", ".join(get_available_providers())
        if available:
            raise ValueError(
                f"Unknown provider: {provider_name}. Available providers: {available}"
            )
        else:
            raise ValueError(
                f"No providers available. Please install dependencies for your chosen provider."
            )
    
    provider_class = registry[provider_name]
    return provider_class(config)


def detect_provider_from_config(config: Dict) -> Optional[str]:
    """Auto-detect provider based on available API keys in config.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Provider name if detected, None otherwise
    """
    # Check for direct provider API keys
    if config.get("google_api_key") or config.get("gemini_api_key"):
        return "google"
    elif config.get("openai_api_key"):
        return "openai"
    elif config.get("anthropic_api_key") or config.get("claude_api_key"):
        return "anthropic"
    elif config.get("openrouter_api_key"):
        return "openrouter"
    
    return None


def get_provider_with_fallback(config: Dict) -> BaseLLMProvider:
    """Get a provider with automatic detection and fallback logic.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Configured provider instance
        
    Raises:
        ValueError: If no suitable provider can be found
    """
    # 1. Try explicit provider setting
    if "provider" in config:
        return get_provider(config["provider"], config)
    
    # 2. Try auto-detection from API keys
    detected_provider = detect_provider_from_config(config)
    if detected_provider:
        return get_provider(detected_provider, config)
    
    # 3. Fallback to OpenRouter for backward compatibility
    available_providers = get_available_providers()
    if "openrouter" in available_providers:
        return get_provider("openrouter", config)
    
    # 4. If no OpenRouter, try any available provider
    if available_providers:
        return get_provider(available_providers[0], config)
    
    raise ValueError(
        "No LLM provider configuration found. Please set an API key for one of the "
        "supported providers (Google Gemini, OpenAI, Anthropic, or OpenRouter)."
    ) 