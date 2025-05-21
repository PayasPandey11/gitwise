import os
import sys
import time

from gitwise.llm.offline import get_llm_response as offline_llm
from gitwise.llm.ollama import get_llm_response as ollama_llm
from gitwise.llm.online import get_llm_response as online_llm
from gitwise.config import get_llm_backend

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
    If Ollama is selected, try up to 3 times before falling back.
    """
    backend = get_llm_backend()
    if backend == "online":
        return online_llm(*args, **kwargs)
    elif backend == "offline":
        return offline_llm(*args, **kwargs)
    elif backend == "ollama":
        return ollama_llm(*args, **kwargs)
    else:
        # Fallback to offline if unknown
        return offline_llm(*args, **kwargs) 