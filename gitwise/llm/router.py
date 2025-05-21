import os
import sys

BACKEND = os.environ.get("GITWISE_LLM_BACKEND", "ollama").lower()

# Import all backends but only use as needed
try:
    from . import ollama
except ImportError:
    ollama = None
try:
    from . import offline
except ImportError:
    offline = None
try:
    from . import online
except ImportError:
    online = None

def get_llm_response(*args, **kwargs):
    """
    Route LLM calls to the selected backend.
    Priority: GITWISE_LLM_BACKEND (ollama|offline|online). Default: ollama.
    Fallback to offline, then online, with warnings if needed.
    """
    backend = os.environ.get("GITWISE_LLM_BACKEND", "ollama").lower()
    if backend == "ollama":
        if ollama is not None:
            try:
                return ollama.get_llm_response(*args, **kwargs)
            except Exception as e:
                print(f"[gitwise] Warning: Ollama backend failed: {e}. Falling back to offline backend.", file=sys.stderr)
                if offline is not None:
                    return offline.get_llm_response(*args, **kwargs)
                else:
                    raise RuntimeError("No offline backend available for fallback.")
        else:
            print("[gitwise] Warning: Ollama backend not available. Falling back to offline backend.", file=sys.stderr)
            if offline is not None:
                return offline.get_llm_response(*args, **kwargs)
            else:
                raise RuntimeError("No offline backend available for fallback.")
    elif backend == "offline":
        if offline is not None:
            return offline.get_llm_response(*args, **kwargs)
        else:
            raise RuntimeError("Offline backend not available.")
    elif backend == "online":
        if online is not None:
            return online.get_llm_response(*args, **kwargs)
        else:
            raise RuntimeError("Online backend not available.")
    else:
        raise ValueError(f"Unknown LLM backend: {backend}") 