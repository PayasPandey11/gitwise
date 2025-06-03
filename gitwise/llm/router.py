import time

from gitwise.config import get_llm_backend, load_config, ConfigError
from gitwise.llm.ollama import OllamaError
from gitwise.ui import components


def get_llm_response(*args, **kwargs):
    """
    Route LLM calls to the selected backend.
    Priority: GITWISE_LLM_BACKEND (ollama|offline|online). Default: ollama.
    Fallback to offline, then online, with warnings if needed.
    If Ollama is selected, try up to 3 times before falling back.
    """
    backend = get_llm_backend()

    if backend == "online":
        try:
            return _get_online_llm_response(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(
                f"Online backend dependencies missing. {str(e)}"
            ) from e
    elif backend == "offline":
        try:
            from gitwise.llm.offline import get_llm_response as offline_llm

            return offline_llm(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(
                f"Offline backend requires 'transformers' and 'torch'. Install with: pip install transformers torch"
            ) from e
    elif backend == "ollama":
        ollama_max_retries = 3
        ollama_retry_delay = 2  # seconds
        for attempt in range(ollama_max_retries):
            try:
                from gitwise.llm.ollama import get_llm_response as ollama_llm

                return ollama_llm(*args, **kwargs)
            except OllamaError as e_ollama:
                components.show_warning(
                    f"Ollama connection attempt {attempt + 1}/{ollama_max_retries} failed: {e_ollama}"
                )
                if attempt < ollama_max_retries - 1:
                    time.sleep(ollama_retry_delay)
                else:
                    components.show_warning(
                        "Ollama failed after multiple retries. Attempting to fall back to offline model."
                    )
                    break  # Break from retry loop to fall through to offline
            except ImportError as e_import_ollama:
                components.show_warning(
                    f"Could not import Ollama backend: {e_import_ollama}. Attempting to fall back to offline model."
                )
                break  # Break to fall through to offline
            except (
                Exception
            ) as e_unexpected_ollama:  # Catch any other unexpected error during ollama attempt
                components.show_warning(
                    f"Unexpected error with Ollama backend (attempt {attempt + 1}/{ollama_max_retries}): {e_unexpected_ollama}"
                )
                if attempt < ollama_max_retries - 1:
                    time.sleep(ollama_retry_delay)
                else:
                    components.show_warning(
                        "Ollama failed due to unexpected error after multiple retries. Attempting to fall back to offline model."
                    )
                    break  # Break from retry loop
        else:  # This else belongs to the for loop, executed if loop completed without break (i.e., ollama_llm call was successful)
            pass  # Ollama succeeded, result already returned

        # Fallback to offline if Ollama fails (either by retries exhausting, import error, or unexpected error)
        try:
            # Message already shown if Ollama failed after retries or import
            # components.show_warning("Falling back to offline LLM model due to Ollama issues.") # This might be redundant if specific error was already shown
            from gitwise.llm.offline import get_llm_response as offline_llm

            components.show_warning(
                "Attempting to use offline model as fallback..."
            )  # Add this for clarity
            return offline_llm(*args, **kwargs)
        except ImportError as e_import_offline:
            raise RuntimeError(
                f"Ollama backend failed AND offline fallback also failed (requires 'transformers' and 'torch'): {e_import_offline}"
            ) from e_import_offline
        except (
            Exception
        ) as e_offline_fallback:  # Catch errors during offline fallback itself
            raise RuntimeError(
                f"Ollama backend failed AND offline fallback also failed with an error: {e_offline_fallback}"
            ) from e_offline_fallback

    else:
        # Fallback to offline if unknown backend
        try:
            from gitwise.llm.offline import get_llm_response as offline_llm

            return offline_llm(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(
                f"Unknown backend '{backend}' and offline fallback requires 'transformers' and 'torch'"
            ) from e


def _get_online_llm_response(*args, **kwargs):
    """Handle online LLM requests using the new provider system.
    
    This function supports both the new provider system and backward compatibility
    with the existing OpenRouter implementation.
    """
    try:
        # Try new provider system first
        from gitwise.llm.providers import get_provider_with_fallback
        
        config = load_config()
        provider = get_provider_with_fallback(config)
        return provider.get_response(*args, **kwargs)
        
    except ImportError as e:
        # Fallback to legacy OpenRouter implementation
        components.show_warning(
            f"Provider system unavailable ({e}), falling back to OpenRouter..."
        )
        from gitwise.llm.online import get_llm_response as legacy_online_llm
        return legacy_online_llm(*args, **kwargs)
        
    except ConfigError as e:
        # No config file, try legacy implementation
        components.show_warning(
            f"Config error ({e}), falling back to OpenRouter..."
        )
        from gitwise.llm.online import get_llm_response as legacy_online_llm
        return legacy_online_llm(*args, **kwargs)
        
    except Exception as e:
        # If provider system fails, try legacy as final fallback
        components.show_warning(
            f"Provider system error ({str(e)}), trying OpenRouter fallback..."
        )
        try:
            from gitwise.llm.online import get_llm_response as legacy_online_llm
            return legacy_online_llm(*args, **kwargs)
        except Exception as fallback_error:
            raise RuntimeError(
                f"Both provider system and OpenRouter fallback failed. "
                f"Provider error: {str(e)}. Fallback error: {str(fallback_error)}"
            ) from e
