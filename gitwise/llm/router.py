"""
LLM routing for GitWise - Routes between Ollama (local) and online providers.

Simplified architecture without offline mode for better maintainability.
Enhanced with structured logging and proper exception handling.
"""

import time
import logging
from gitwise.config import get_llm_backend, get_secure_config, ConfigError
from gitwise.exceptions import LLMError, NetworkError, ConfigurationError
from gitwise.llm.ollama import OllamaError
from gitwise.ui import components

logger = logging.getLogger(__name__)


def get_llm_response(*args, **kwargs):
    """
    Route LLM calls to the selected backend with enhanced logging and error handling.
    
    Supports two backends:
    - ollama (default): Local Ollama server
    - online: Cloud-based LLM providers
    
    Args:
        *args: Arguments to pass to the LLM backend
        **kwargs: Keyword arguments to pass to the LLM backend
        
    Returns:
        str: Response from the LLM
        
    Raises:
        LLMError: If all backends fail
        NetworkError: If network-related issues occur
        ConfigurationError: If configuration is invalid
    """
    backend = get_llm_backend()
    
    # Log the request
    prompt_text = args[0] if args else str(kwargs.get('prompt', ''))
    prompt_length = len(prompt_text)
    
    logger.info(f"LLM request initiated for backend: {backend}, prompt length: {prompt_length}")
    
    try:
        if backend == "online":
            response = _get_online_llm_response(*args, **kwargs)
        elif backend == "ollama":
            response = _get_ollama_llm_response(*args, **kwargs)
        else:
            logger.warning(f"Unknown backend '{backend}', defaulting to Ollama")
            components.show_warning(f"Unknown backend '{backend}', defaulting to Ollama")
            response = _get_ollama_llm_response(*args, **kwargs)
        
        logger.info(f"LLM request completed, response length: {len(response) if response else 0}")
        return response
            
    except LLMError:
        # Re-raise LLM errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in LLM routing: {e}")
        raise LLMError(f"Unexpected error in LLM routing: {e}") from e


def _get_ollama_llm_response(*args, **kwargs):
    """
    Get response from Ollama with retry logic.
    
    Returns:
        str: Response from Ollama
        
    Raises:
        LLMError: If Ollama is unavailable after retries
    """
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            from gitwise.llm.ollama import get_llm_response as ollama_llm
            return ollama_llm(*args, **kwargs)
            
        except OllamaError as e:
            components.show_warning(
                f"Ollama connection attempt {attempt + 1}/{max_retries} failed: {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Ollama failed after {max_retries} attempts")
                raise LLMError(
                    f"Ollama failed after {max_retries} attempts. "
                    "Please ensure Ollama is running: 'ollama serve'"
                ) from e
                
        except ImportError as e:
            logger.error("Ollama backend not available")
            raise LLMError(
                "Ollama backend not available. Please install Ollama: "
                "https://ollama.ai/"
            ) from e
            
        except Exception as e:
            logger.warning(f"Unexpected Ollama error (attempt {attempt + 1}/{max_retries}): {e}")
            components.show_warning(
                f"Unexpected Ollama error (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error(f"Ollama failed with unexpected error: {e}")
                raise LLMError(f"Ollama failed with unexpected error: {e}") from e


def _get_online_llm_response(*args, **kwargs):
    """
    Handle online LLM requests using the provider system.
    
    Returns:
        str: Response from online provider
        
    Raises:
        LLMError: If online providers fail
    """
    try:
        # Use new provider system
        from gitwise.llm.providers import get_provider_with_fallback
        
        # Use secure config that retrieves API keys from keychain
        config = get_secure_config()
        provider = get_provider_with_fallback(config)
        return provider.get_response(*args, **kwargs)
        
    except ImportError as e:
        # Fallback to legacy OpenRouter implementation
        logger.warning(f"Provider system unavailable: {e}")
        components.show_warning(
            f"Provider system unavailable ({e}), falling back to OpenRouter..."
        )
        return _get_legacy_online_response(*args, **kwargs)
        
    except ConfigError as e:
        # No valid config, try legacy implementation
        logger.warning(f"Config error: {e}")
        components.show_warning(
            f"Config error ({e}), falling back to OpenRouter..."
        )
        return _get_legacy_online_response(*args, **kwargs)
        
    except Exception as e:
        # If provider system fails, try legacy as final fallback
        logger.warning(f"Provider system error: {e}")
        components.show_warning(
            f"Provider system error ({str(e)}), trying OpenRouter fallback..."
        )
        return _get_legacy_online_response(*args, **kwargs)


def _get_legacy_online_response(*args, **kwargs):
    """
    Fallback to legacy OpenRouter implementation.
    
    Returns:
        str: Response from OpenRouter
        
    Raises:
        LLMError: If legacy implementation fails
    """
    try:
        from gitwise.llm.online import get_llm_response as legacy_online_llm
        return legacy_online_llm(*args, **kwargs)
    except Exception as e:
        logger.error(f"All online providers failed: {e}")
        raise LLMError(
            f"All online providers failed: {str(e)}. "
            "Please check your API keys and network connection."
        ) from e