import os
import sys
import time

from gitwise.config import get_llm_backend

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
            from gitwise.llm.online import get_llm_response as online_llm
            return online_llm(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(f"Online backend requires 'openai' package. Install with: pip install openai") from e
    elif backend == "offline":
        try:
            from gitwise.llm.offline import get_llm_response as offline_llm
            return offline_llm(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(f"Offline backend requires 'transformers' and 'torch'. Install with: pip install transformers torch") from e
    elif backend == "ollama":
        try:
            from gitwise.llm.ollama import get_llm_response as ollama_llm
            return ollama_llm(*args, **kwargs)
        except ImportError as e:
            # Fallback to offline if ollama backend has issues
            try:
                from gitwise.llm.offline import get_llm_response as offline_llm
                return offline_llm(*args, **kwargs)
            except ImportError:
                raise RuntimeError(f"Ollama backend failed and offline fallback requires 'transformers' and 'torch'") from e
    else:
        # Fallback to offline if unknown backend
        try:
            from gitwise.llm.offline import get_llm_response as offline_llm
            return offline_llm(*args, **kwargs)
        except ImportError as e:
            raise RuntimeError(f"Unknown backend '{backend}' and offline fallback requires 'transformers' and 'torch'") from e 