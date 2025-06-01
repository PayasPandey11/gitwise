"""Online LLM support for GitWise (OpenRouter/OpenAI)."""

import os
from typing import Dict, List, Union

from openai import OpenAI

from gitwise.config import ConfigError, load_config

# Default model if not specified in config or environment
DEFAULT_OPENROUTER_MODEL = "anthropic/claude-3-haiku"


def get_llm_response(
    prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs
) -> str:
    """Get response from online LLM (OpenRouter/OpenAI)."""
    api_key = None
    model_name = DEFAULT_OPENROUTER_MODEL
    try:
        try:
            config = load_config()
            api_key = config.get("openrouter_api_key")
            # Get model from config, fallback to env, then to default
            model_name = config.get(
                "openrouter_model",
                os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL),
            )
        except ConfigError:  # Config file might not exist or be valid
            api_key = os.environ.get("OPENROUTER_API_KEY")
            model_name = os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)

        if not api_key:
            raise RuntimeError(
                "OpenRouter API key not found in config or environment. Please run 'gitwise init' or set OPENROUTER_API_KEY."
            )

        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = prompt_or_messages

        response = client.chat.completions.create(
            model=model_name,  # Use the configured/default model name
            messages=messages,
            extra_headers={
                "HTTP-Referer": "https://github.com/payas/gitwise",  # Consider making this dynamic if project moves
                "X-Title": "GitWise",
            },
        )

        if not response.choices or not response.choices[0].message:
            raise RuntimeError("Empty response from LLM")
        return response.choices[0].message.content.strip()
    except Exception as e:
        if hasattr(e, "status_code") and e.status_code == 401:
            raise RuntimeError(
                "Authentication failed (401). Your OpenRouter API key was found, but was rejected by the server. "
                "This may mean your key is invalid, disabled, revoked, a provisioning key, or you lack access to the requested model. "
                "Please check your OpenRouter dashboard or try generating a new key."
            ) from e
        # It might be useful to log the model_name being used when an error occurs
        raise RuntimeError(
            f"Error getting LLM response (model: {model_name}): {str(e)}"
        ) from e
