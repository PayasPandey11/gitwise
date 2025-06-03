"""OpenAI provider implementation."""

import os
from typing import Dict, List, Union, Any

try:
    import openai
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False

from .base import BaseLLMProvider
# We'll need to define these or a similar mechanism for OpenAI
# from ..models.openai_models import AVAILABLE_OPENAI_MODELS, DEFAULT_OPENAI_MODEL


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider with configuration."""
        if not _HAS_OPENAI:
            raise ImportError(
                "OpenAI Python package not found. "
                "Install with: pip install openai"
            )
        
        super().__init__(config)
        self.client = None
        self._setup_client()

    def _setup_client(self) -> None:
        """Setup the OpenAI client with API key."""
        api_key = self._get_api_key()
        # OpenAI client initialization might differ based on version
        # For openai >= 1.0.0
        self.client = openai.OpenAI(api_key=api_key)
        
        # Optionally, test the connection (e.g., by listing models)
        try:
            self.client.models.list()
        except openai.AuthenticationError as e:
            raise RuntimeError(f"OpenAI API key is invalid or missing: {e}")
        except Exception as e:
            # Catch other potential errors during client setup/test
            raise RuntimeError(f"Failed to initialize OpenAI client or test connection: {e}")


    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        api_key = (
            self.config.get("openai_api_key") or
            os.environ.get("OPENAI_API_KEY")
        )
        
        if not api_key:
            raise ValueError(
                "OpenAI API key not found. Please set 'openai_api_key' in config "
                "or OPENAI_API_KEY environment variable."
            )
        return api_key

    def _messages_to_openai_format(self, prompt_or_messages: Union[str, List[Dict[str, str]]]) -> List[Dict[str, str]]:
        """Convert input to OpenAI's expected message format."""
        if isinstance(prompt_or_messages, str):
            return [{"role": "user", "content": prompt_or_messages}]
        
        # Validate messages format (basic check)
        valid_messages = []
        for msg in prompt_or_messages:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                valid_messages.append(msg)
            else:
                # Handle or log malformed messages if necessary
                # For now, we'll just skip them or raise an error
                # Example: raise ValueError(f"Malformed message: {msg}")
                # For simplicity, let's assume well-formed messages or convert as best as possible
                if isinstance(msg, dict) and "content" in msg: # if role is missing, default to user
                    valid_messages.append({"role": "user", "content": msg["content"]})
                # else skip if content is missing
        return valid_messages

    def _build_request_params(self, **kwargs) -> Dict[str, Any]:
        """Build request parameters for OpenAI API from kwargs."""
        params = {}
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            params["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        # OpenAI doesn't directly use top_k for chat completions in the same way as Gemini.
        # It has `frequency_penalty` and `presence_penalty` instead.
        # We will not map top_k for now to keep it simple.
        return params

    def get_response(self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs) -> str:
        """Get response from OpenAI.

        Args:
            prompt_or_messages: Either a string prompt or list of message dicts.
            **kwargs: Additional parameters (temperature, max_tokens, model, etc.).

        Returns:
            The response text from OpenAI.

        Raises:
            RuntimeError: If the API call fails.
        """
        if not self.client:
            # This should ideally not happen if constructor ensures client is setup
            self._setup_client()

        model_name = self.get_model()
        messages = self._messages_to_openai_format(prompt_or_messages)
        
        if not messages:
            raise ValueError("Input prompt or messages resulted in an empty message list.")

        request_params = self._build_request_params(**kwargs)

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                **request_params
            )
            
            if response.choices and response.choices[0].message:
                content = response.choices[0].message.content
                if content is not None:
                    return content.strip()
            
            # Fallback or error if no content
            # Check for finish reasons if needed, e.g. 'length' if max_tokens hit
            finish_reason = response.choices[0].finish_reason if response.choices else "unknown"
            if finish_reason == "length":
                 # If content is empty and finish_reason is length, it might mean max_tokens was too small
                 # or some other issue. For now, we treat empty content as an issue.
                raise RuntimeError(f"OpenAI response was truncated (max_tokens reached) or content is missing. Finish reason: {finish_reason}")

            raise RuntimeError("Empty response or unexpected format from OpenAI.")

        except openai.AuthenticationError as e:
            raise RuntimeError(
                "OpenAI API key is invalid or expired. Please check your OPENAI_API_KEY "
                "or 'openai_api_key' in your configuration."
            ) from e
        except openai.NotFoundError as e: # Often indicates model not found
            raise RuntimeError(
                f"OpenAI API error: Model '{model_name}' not found or you do not have access. {e}"
            ) from e
        except openai.RateLimitError as e:
            raise RuntimeError(
                "OpenAI API rate limit exceeded. Please check your usage and limits."
            ) from e
        except openai.APIError as e: # Catch other API related errors
            raise RuntimeError(f"OpenAI API error: {e}") from e
        except Exception as e: # Catch any other unexpected errors
            raise RuntimeError(f"An unexpected error occurred while communicating with OpenAI: {e}") from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate OpenAI-specific configuration.

        Args:
            config: Configuration dictionary.

        Returns:
            True if valid, False otherwise.
        """
        # Check for API key
        has_api_key = any([
            config.get("openai_api_key"),
            os.environ.get("OPENAI_API_KEY")
        ])
        if not has_api_key:
            return False
        
        # Model validation is implicitly handled by API calls; explicit validation here
        # could involve listing models, but that's an API call itself.
        # For simplicity, we'll rely on the API call in get_response to fail if the model is invalid.
        # model = self.get_model() 
        # if model and not self._is_valid_model(model): # _is_valid_model would need to be implemented
        #     return False
            
        return True

    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models.

        Returns:
            List of available model names.
        """
        # For now, return a common default. Later, can fetch dynamically or use a predefined list.
        # return AVAILABLE_OPENAI_MODELS.copy()
        # Example: return ["gpt-4", "gpt-3.5-turbo"]
        # Fetching models dynamically:
        if not self.client:
            # This might happen if called before full init or if client setup failed silently (though it shouldn't)
            # For safety, or if we want to allow calling this before full init
            try:
                self._setup_client() # Ensure client is set up
            except RuntimeError: # If API key isn't set up, this will fail
                 return [self.get_default_model()] # Fallback

        try:
            models = self.client.models.list()
            # Filter for models that are typically used for chat/completions, if desired
            # For now, returning all model IDs
            return [model.id for model in models.data if "gpt" in model.id] # Simple filter for GPT models
        except Exception:
            # If API call fails (e.g. network, auth error not caught in setup)
            return [self.get_default_model()] # Fallback to default

    @property
    def provider_name(self) -> str:
        """Return the provider name.

        Returns:
            Provider name 'openai'.
        """
        return "openai"

    def get_default_model(self) -> str:
        """Get the default OpenAI model.

        Returns:
            Default model name.
        """
        # return DEFAULT_OPENAI_MODEL
        return "gpt-3.5-turbo" # A common default

    # def _is_valid_model(self, model_name: str) -> bool:
    #     """Check if model name is valid for OpenAI.
    #
    #     Args:
    #         model_name: Model name to validate.
    #
    #     Returns:
    #         True if valid, False otherwise.
    #     """
    #     # This would require fetching all available models and checking against the list.
    #     # For simplicity, actual API calls will validate the model.
    #     # return model_name in self.get_available_models() 