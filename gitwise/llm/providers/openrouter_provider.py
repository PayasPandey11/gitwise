"""OpenRouter provider implementation."""

import os
from typing import Any, Dict, List, Union

try:
    from openai import OpenAI
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False

from .base import BaseLLMProvider
from ..models.openrouter_models import (
    AVAILABLE_OPENROUTER_MODELS,
    DEFAULT_OPENROUTER_MODEL,
)


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenRouter provider with configuration."""
        if not _HAS_OPENAI:
            raise ImportError(
                "OpenAI package not found. Install with: pip install openai"
            )

        super().__init__(config)
        self.client = self._setup_client()

    def _setup_client(self) -> OpenAI:
        """Setup the OpenRouter client with API key."""
        api_key = self._get_api_key()
        return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        api_key = self.config.get("openrouter_api_key") or os.environ.get(
            "OPENROUTER_API_KEY"
        )
        if not api_key:
            raise ValueError(
                "OpenRouter API key not found. Please set 'openrouter_api_key' in "
                "config or OPENROUTER_API_KEY environment variable."
            )
        return api_key

    def get_response(
        self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs
    ) -> str:
        """Get response from OpenRouter.

        Args:
            prompt_or_messages: Either a string prompt or list of message dicts
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            The response text from OpenRouter.

        Raises:
            RuntimeError: If the API call fails.
        """
        if isinstance(prompt_or_messages, str):
            messages = [{"role": "user", "content": prompt_or_messages}]
        else:
            messages = prompt_or_messages

        model_name = self.get_model()

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                extra_headers={
                    "HTTP-Referer": "https://github.com/payas/gitwise",
                    "X-Title": "GitWise",
                },
                **self._build_request_params(**kwargs),
            )

            if not response.choices or not response.choices[0].message:
                raise RuntimeError("Empty response from LLM")
            return response.choices[0].message.content.strip()
        except Exception as e:
            if hasattr(e, "status_code") and e.status_code == 401:
                raise RuntimeError(
                    "Authentication failed (401). Your OpenRouter API key was found, "
                    "but was rejected by the server. This may mean your key is invalid, "
                    "disabled, revoked, or you lack access to the requested model. "
                    "Please check your OpenRouter dashboard or try generating a new key."
                ) from e
            raise RuntimeError(
                f"Error getting LLM response (model: {model_name}): {str(e)}"
            ) from e

    def _build_request_params(self, **kwargs) -> Dict[str, Any]:
        """Build request parameters from kwargs."""
        params = {}
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        # OpenRouter does not use top_k in the same way, so we omit it.
        return params

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenRouter-specific configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid, False otherwise
        """
        return bool(
            config.get("openrouter_api_key")
            or os.environ.get("OPENROUTER_API_KEY")
        )

    def _is_valid_model(self, model_name: str) -> bool:
        """Check if model name is valid for OpenRouter.

        For OpenRouter, we perform a basic format check as the list of models is vast and dynamic.
        A valid name is in the format 'provider/model'.
        """
        return "/" in model_name

    def get_available_models(self) -> List[str]:
        """Get list of available OpenRouter models."""
        return AVAILABLE_OPENROUTER_MODELS.copy()

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "openrouter"

    def get_default_model(self) -> str:
        """Get the default OpenRouter model."""
        return DEFAULT_OPENROUTER_MODEL 