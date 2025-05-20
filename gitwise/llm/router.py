import os
from .offline import get_llm_response as offline_llm
from .online import get_llm_response as online_llm

def get_llm_response(*args, **kwargs):
    """Route LLM calls: offline by default, online if GITWISE_ONLINE=1 or --online flag."""
    # Check env var
    use_online = os.environ.get("GITWISE_ONLINE") == "1"
    # TODO: Add CLI flag check if needed (pass context or use global)
    if use_online:
        return online_llm(*args, **kwargs)
    return offline_llm(*args, **kwargs) 