import json
import os

try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    import urllib.error
    import urllib.request

    _HAS_REQUESTS = False

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")


class OllamaError(Exception):
    pass


def get_llm_response(prompt: str, model: str = None, **kwargs) -> str:
    """
    Send a prompt to the local Ollama server and return the generated response.
    Args:
        prompt: The prompt string to send.
        model: The model name (default: from env or 'llama3').
        **kwargs: Extra params (not used yet).
    Returns:
        The generated response as a string.
    Raises:
        OllamaError: If Ollama is not running or request fails.
    """
    # Fetch default model at runtime to respect mocked env vars in tests
    default_model_from_env = os.environ.get("OLLAMA_MODEL", "llama3")
    effective_model = model or default_model_from_env
    payload = {"model": effective_model, "prompt": prompt, "stream": False}
    try:
        if _HAS_REQUESTS:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        else:
            req = urllib.request.Request(
                OLLAMA_URL,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
        if "response" in data:
            return data["response"].strip()
        raise OllamaError(f"Unexpected Ollama response: {data}")
    except Exception as e:
        raise OllamaError(f"Could not connect to Ollama at {OLLAMA_URL}: {e}")
