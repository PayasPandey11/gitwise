import pytest
from unittest.mock import patch, MagicMock
import os

# Modules to test
from gitwise.llm import router
from gitwise.llm import ollama, online
from gitwise.config import ConfigError


# --- Fixtures ---
@pytest.fixture
def mock_config_load():
    with patch("gitwise.config.load_config") as mock_load:
        yield mock_load


@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.delenv("GITWISE_LLM_BACKEND", raising=False)
    monkeypatch.delenv("OLLAMA_URL", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    yield monkeypatch


# --- Tests for gitwise.llm.ollama ---
@patch("gitwise.llm.ollama.requests.post")
def test_ollama_get_llm_response_success(mock_post, mock_env_vars):
    mock_env_vars.setenv("OLLAMA_MODEL", "test-ollama-model")
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Ollama says hello"}
    mock_response.raise_for_status = MagicMock()
    mock_post.return_value = mock_response

    response = ollama.get_llm_response("prompt text")
    assert response == "Ollama says hello"
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "http://localhost:11434/api/generate"  # Default URL
    assert call_args[1]["json"]["model"] == "test-ollama-model"
    assert call_args[1]["json"]["prompt"] == "prompt text"


@patch("gitwise.llm.ollama.requests.post")
def test_ollama_get_llm_response_connection_error(mock_post, mock_env_vars):
    mock_post.side_effect = ollama.requests.exceptions.ConnectionError(
        "Test connection error"
    )
    with pytest.raises(ollama.OllamaError, match="Could not connect to Ollama"):
        ollama.get_llm_response("prompt")




# --- Tests for gitwise.llm.online ---
@patch("gitwise.llm.online.load_config")
@patch("gitwise.llm.online.OpenAI")
def test_online_get_llm_response_success(
    mock_openai_constructor, mock_load_config, mock_env_vars
):
    mock_load_config.return_value = {
        "openrouter_api_key": "test_api_key_from_config",
        "openrouter_model": "test_model_from_config",
    }

    mock_client_instance = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(message=MagicMock(content="Online says hello"))
    ]
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_openai_constructor.return_value = mock_client_instance

    response = online.get_llm_response("prompt text")
    assert response == "Online says hello"
    mock_openai_constructor.assert_called_once_with(
        base_url="https://openrouter.ai/api/v1", api_key="test_api_key_from_config"
    )
    mock_client_instance.chat.completions.create.assert_called_once()
    call_args = mock_client_instance.chat.completions.create.call_args
    assert call_args[1]["model"] == "test_model_from_config"
    assert call_args[1]["messages"] == [{"role": "user", "content": "prompt text"}]


@patch("gitwise.llm.online.OpenAI")
@patch("gitwise.llm.online.load_config")
def test_online_get_llm_response_no_apikey(
    mock_load_config, mock_openai_constructor, mock_env_vars
):
    mock_load_config.side_effect = ConfigError("No config")  # No config file
    # Ensure OPENROUTER_API_KEY is not in env by virtue of mock_env_vars fixture
    with pytest.raises(RuntimeError, match="OpenRouter API key not found"):
        online.get_llm_response("prompt")


# --- Tests for gitwise.llm.router ---
@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.llm.ollama.get_llm_response")
def test_router_routes_to_ollama(mock_ollama_llm_func, mock_router_get_backend):
    mock_router_get_backend.return_value = "ollama"
    mock_ollama_llm_func.return_value = "Ollama response via router"

    response = router.get_llm_response("test prompt", model="ollama-model-override")
    assert response == "Ollama response via router"
    mock_ollama_llm_func.assert_called_once_with(
        "test prompt", model="ollama-model-override"
    )




@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.config.get_secure_config")  # Mock secure config function
@patch("gitwise.llm.providers.get_provider_with_fallback")  # Mock the new provider path
def test_router_routes_to_online(
    mock_get_provider_with_fallback, mock_get_secure_config, mock_router_get_backend
):
    mock_router_get_backend.return_value = "online"
    
    # Simulate a successful config load
    mock_get_secure_config.return_value = {"some_config_key": "some_value"} 

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_response.return_value = "Online response via router"
    mock_get_provider_with_fallback.return_value = mock_provider_instance

    response = router.get_llm_response("test prompt")
    assert response == "Online response via router"
    
    # Check that provider was called (actual config values may vary)
    mock_get_provider_with_fallback.assert_called_once()
    mock_provider_instance.get_response.assert_called_once_with("test prompt")




@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.llm.ollama.get_llm_response")
@patch("gitwise.llm.router.time.sleep")  # Mock sleep to speed up test
def test_router_ollama_error_handling(
    mock_sleep,
    mock_ollama_llm_func,
    mock_router_get_backend,
):
    mock_router_get_backend.return_value = "ollama"
    mock_ollama_llm_func.side_effect = ollama.OllamaError("Ollama connect failed")

    from gitwise.exceptions import LLMError
    with pytest.raises(LLMError, match="Ollama failed after 3 attempts"):
        router.get_llm_response("test prompt")
    
    # Verify it retried 3 times
    assert mock_ollama_llm_func.call_count == 3
