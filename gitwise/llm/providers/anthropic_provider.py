"""Anthropic (Claude) provider implementation."""

import os
from typing import Dict, List, Union, Any, Optional

try:
    import anthropic
    _HAS_ANTHROPIC = True
except ImportError:
    _HAS_ANTHROPIC = False

from .base import BaseLLMProvider
# from ..models.anthropic_models import AVAILABLE_ANTHROPIC_MODELS, DEFAULT_ANTHROPIC_MODEL # Placeholder


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider with configuration."""
        if not _HAS_ANTHROPIC:
            raise ImportError(
                "Anthropic Python package not found. "
                "Install with: pip install anthropic"
            )
        
        super().__init__(config)
        self.client = None
        self._setup_client()

    def _setup_client(self) -> None:
        """Setup the Anthropic client with API key."""
        api_key = self._get_api_key()
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Anthropic library doesn't have a simple list_models() or similar lightweight call
        # to test the key without making a content generation request.
        # We will assume the key is valid if the client initializes.
        # Actual validation will occur on the first get_response call.
        if not self.client:
            raise RuntimeError("Failed to initialize Anthropic client.")

    def _get_api_key(self) -> str:
        """Get API key from config or environment."""
        api_key = (
            self.config.get("anthropic_api_key") or
            self.config.get("claude_api_key") or # For backward compatibility/common naming
            os.environ.get("ANTHROPIC_API_KEY") or
            os.environ.get("CLAUDE_API_KEY")
        )
        
        if not api_key:
            raise ValueError(
                "Anthropic API key not found. Please set 'anthropic_api_key' or 'claude_api_key' in config, "
                "or ANTHROPIC_API_KEY/CLAUDE_API_KEY environment variable."
            )
        return api_key

    def _prepare_anthropic_messages_and_system_prompt(self, prompt_or_messages: Union[str, List[Dict[str, str]]]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Prepare messages for Anthropic API, extracting a system prompt if present."""
        system_prompt: Optional[str] = None
        messages: List[Dict[str, str]] = []

        if isinstance(prompt_or_messages, str):
            messages.append({"role": "user", "content": prompt_or_messages})
            return system_prompt, messages

        # If it's a list of dicts
        temp_messages = []
        for msg in prompt_or_messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                # Skip malformed messages or handle as per project policy
                continue 
            
            if msg["role"] == "system":
                if system_prompt is None: # Use the first system message
                    system_prompt = str(msg["content"])
                else: # Append to existing system prompt if multiple are found
                    system_prompt += "\n" + str(msg["content"])
            else:
                # Ensure roles are 'user' or 'assistant'
                role = msg["role"] if msg["role"] in ["user", "assistant"] else "user"
                temp_messages.append({"role": role, "content": str(msg["content"])})
        
        # Ensure the first message is from the user if there are messages
        if temp_messages and temp_messages[0]["role"] != "user":
            # This case needs careful handling. Anthropic expects user message first.
            # If first is assistant, we might prepend a dummy user message or error out.
            # For now, let's prepend a generic user message if assistant is first.
            # A better approach might be to error or ensure upstream data is correct.
            if system_prompt and not any(m["role"] == "user" for m in temp_messages):
                # If there's only a system prompt and no user messages, create one.
                messages.append({"role": "user", "content": "Understood."})
            elif temp_messages[0]["role"] == "assistant":
                 messages.append({"role": "user", "content": "Continue:"}) # Placeholder
            messages.extend(temp_messages)
        else:
            messages = temp_messages
            
        # If messages list is empty but there was a system prompt, create a default user message
        if not messages and system_prompt:
            messages.append({"role": "user", "content": "Understood the instructions."})
        elif not messages and not system_prompt:
            # No system prompt and no messages, this is an invalid state.
            # Handled by the check in get_response.
            pass # Let get_response handle empty messages
            
        return system_prompt, messages

    def _build_request_params(self, **kwargs) -> Dict[str, Any]:
        """Build request parameters for Anthropic API from kwargs."""
        params = {}
        if "temperature" in kwargs:
            params["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs: # Anthropic uses max_tokens
            params["max_tokens"] = kwargs["max_tokens"]
        if "top_p" in kwargs:
            params["top_p"] = kwargs["top_p"]
        if "top_k" in kwargs:
            params["top_k"] = kwargs["top_k"]
        return params

    def get_response(self, prompt_or_messages: Union[str, List[Dict[str, str]]], **kwargs) -> str:
        """Get response from Anthropic (Claude)."""
        if not self.client:
            self._setup_client()

        model_name = self.get_model()
        system_prompt, messages = self._prepare_anthropic_messages_and_system_prompt(prompt_or_messages)
        
        if not messages:
            raise ValueError("Input prompt or messages resulted in an empty message list for Anthropic.")

        request_params = self._build_request_params(**kwargs)
        
        try:
            api_params: Dict[str, Any] = {
                "model": model_name,
                "messages": messages,
                **request_params
            }
            if system_prompt:
                api_params["system"] = system_prompt
            
            # Ensure max_tokens is present, as it's required by Anthropic
            if "max_tokens" not in api_params or not isinstance(api_params["max_tokens"], int) or api_params["max_tokens"] <=0:
                # Set a default if not provided or invalid, Anthropic requires this
                # This default should be reasonable, e.g. 2048 or 4096. For now, 1024 as a placeholder.
                api_params["max_tokens"] = kwargs.get("max_output_tokens", 1024) 

            response = self.client.messages.create(**api_params)

            if response.content and isinstance(response.content, list) and len(response.content) > 0:
                # Assuming the first block is the primary text response
                first_content_block = response.content[0]
                if hasattr(first_content_block, 'text') and isinstance(first_content_block.text, str):
                    return first_content_block.text.strip()
            
            # Check for stop reason if content is empty or not as expected
            stop_reason = response.stop_reason
            if stop_reason == "max_tokens":
                raise RuntimeError(f"Anthropic response was truncated (max_tokens reached). Stop reason: {stop_reason}")
            
            raise RuntimeError(f"Empty or unexpected response format from Anthropic. Stop reason: {stop_reason}")

        except anthropic.AuthenticationError as e:
            raise RuntimeError(
                "Anthropic API key is invalid or expired. Please check your ANTHROPIC_API_KEY/CLAUDE_API_KEY "
                "or relevant key in your configuration."
            ) from e
        except anthropic.NotFoundError as e: # Model not found or other resource not found
            raise RuntimeError(
                f"Anthropic API error: Resource not found (e.g., model '{model_name}' may be invalid or unavailable). {e}"
            ) from e
        except anthropic.RateLimitError as e:
            raise RuntimeError(
                "Anthropic API rate limit exceeded. Please check your usage and limits."
            ) from e
        except anthropic.APIError as e:
            raise RuntimeError(f"Anthropic API error: {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while communicating with Anthropic: {e}") from e

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Anthropic-specific configuration."""
        has_api_key = any([
            config.get("anthropic_api_key"),
            config.get("claude_api_key"),
            os.environ.get("ANTHROPIC_API_KEY"),
            os.environ.get("CLAUDE_API_KEY")
        ])
        if not has_api_key:
            return False
        # Model validation will rely on API call success for now.
        return True

    def get_available_models(self) -> List[str]:
        """Get list of available Anthropic models."""
        # Anthropic models are typically versioned, e.g., "claude-2", "claude-instant-1"
        # For now, a predefined list. This could be updated based on Anthropic's offerings.
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]

    @property
    def provider_name(self) -> str:
        """Return the provider name."""
        return "anthropic"

    def get_default_model(self) -> str:
        """Get the default Anthropic model."""
        return "claude-3-haiku-20240307" # Haiku is a good balance of speed and capability 