import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Modules to test
from gitwise.llm import router  # router is primary entry point
from gitwise.llm import ollama, offline, online, download
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
    monkeypatch.delenv("GITWISE_OFFLINE_MODEL", raising=False)
    monkeypatch.delenv("HF_HOME", raising=False)
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


# --- Tests for gitwise.llm.offline ---
@patch("gitwise.llm.offline._load_offline_model")
def test_offline_get_llm_response_success(mock_load_offline_model, mock_env_vars):
    mock_env_vars.setenv("GITWISE_OFFLINE_MODEL", "TestOfflineModel/v1")

    # Mock the pipeline directly on the offline module
    mock_pipeline = MagicMock()
    mock_pipeline.return_value = [
        {"generated_text": "Offline prompt text then offline says hello"}
    ]

    mock_tokenizer = MagicMock()
    mock_tokenizer.eos_token_id = 50256

    # Set up the offline module's global state
    offline._pipeline = mock_pipeline
    offline._tokenizer = mock_tokenizer
    offline._model_ready = True

    response = offline.get_llm_response("Offline prompt text then ")
    assert response == "offline says hello"

    # Verify pipeline was called with correct parameters
    mock_pipeline.assert_called_once()
    call_args = mock_pipeline.call_args
    assert call_args[0][0] == "Offline prompt text then "
    assert call_args[1]["max_new_tokens"] == 128
    assert call_args[1]["pad_token_id"] == 50256


@patch("gitwise.llm.download.download_offline_model")
@patch("gitwise.llm.offline._load_offline_model")
def test_offline_ensure_model_download_prompt_no(
    mock_load_offline, mock_download_offline, mock_env_vars
):
    # First attempt to load fails
    mock_load_offline.side_effect = [
        offline.OfflineModelError("Model not found"),  # First call fails
        offline.OfflineModelError(
            "Still not loaded"
        ),  # Second call after download also fails
    ]
    offline._model_ready = False

    with pytest.raises(
        offline.OfflineModelError,
        match="Failed to load offline model after download attempt",
    ):
        offline.ensure_offline_model_ready()

    # Verify download was attempted
    mock_download_offline.assert_called_once()
    # Verify we tried to load twice (before and after download)
    assert mock_load_offline.call_count == 2


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
@patch("gitwise.llm.offline.get_llm_response")
def test_router_routes_to_offline(mock_offline_llm_func, mock_router_get_backend):
    mock_router_get_backend.return_value = "offline"
    mock_offline_llm_func.return_value = "Offline response via router"

    response = router.get_llm_response("test prompt")
    assert response == "Offline response via router"
    mock_offline_llm_func.assert_called_once_with("test prompt")


@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.llm.router.load_config")  # Mock load_config in the router
@patch("gitwise.llm.providers.get_provider_with_fallback")  # Mock the new provider path
def test_router_routes_to_online(
    mock_get_provider_with_fallback, mock_load_config, mock_router_get_backend
):
    mock_router_get_backend.return_value = "online"
    
    # Simulate a successful config load
    mock_load_config.return_value = {"some_config_key": "some_value"} 

    mock_provider_instance = MagicMock()
    mock_provider_instance.get_response.return_value = "Online response via router"
    mock_get_provider_with_fallback.return_value = mock_provider_instance

    response = router.get_llm_response("test prompt")
    assert response == "Online response via router"
    
    mock_get_provider_with_fallback.assert_called_once_with(mock_load_config.return_value)
    mock_provider_instance.get_response.assert_called_once_with("test prompt")


@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.llm.ollama.get_llm_response")
@patch("gitwise.llm.offline.get_llm_response")
@patch("gitwise.llm.router.time.sleep")
def test_router_ollama_fallback_to_offline(
    mock_time_sleep,
    mock_offline_llm_func,
    mock_ollama_llm_func,
    mock_router_get_backend,
    capsys,
):
    mock_router_get_backend.return_value = "ollama"
    mock_ollama_llm_func.side_effect = ollama.OllamaError("Ollama connect failed")
    mock_offline_llm_func.return_value = "Offline fallback success"

    response = router.get_llm_response("test prompt")
    assert response == "Offline fallback success"
    assert mock_ollama_llm_func.call_count == 3  # Default 3 retries
    mock_offline_llm_func.assert_called_once_with("test prompt")
    captured = capsys.readouterr()
    # Normalize by splitting all whitespace and joining with single space for robust checking
    normalized_out = " ".join(captured.out.split())

    # Check for key phrases in normalized output
    assert "Ollama connection attempt 1/3 failed" in normalized_out
    assert "Ollama connection attempt 2/3 failed" in normalized_out
    assert "Ollama connection attempt 3/3 failed" in normalized_out
    assert "Ollama failed after multiple retries" in normalized_out
    assert "Attempting to fall back to offline model" in normalized_out
    assert "Attempting to use offline model as fallback..." in normalized_out


@patch("gitwise.llm.router.get_llm_backend")
@patch("gitwise.llm.ollama.get_llm_response")
@patch("gitwise.llm.offline.get_llm_response")
@patch("gitwise.llm.router.time.sleep")
def test_router_ollama_fallback_offline_fails_too(
    mock_time_sleep,
    mock_offline_llm_func,
    mock_ollama_llm_func,
    mock_router_get_backend,
):
    mock_router_get_backend.return_value = "ollama"
    mock_ollama_llm_func.side_effect = ollama.OllamaError("Ollama connect failed")
    mock_offline_llm_func.side_effect = RuntimeError("Offline model load failed")

    with pytest.raises(
        RuntimeError,
        match="Ollama backend failed AND offline fallback also failed with an error: Offline model load failed",
    ):
        router.get_llm_response("test prompt")


# --- Tests for gitwise.llm.download ---
@patch("gitwise.llm.download.os.path.exists")
@patch("gitwise.llm.download.input")
@patch("gitwise.llm.download.subprocess.run")
def test_download_offline_model_downloads_if_not_exists(
    mock_subprocess_run, mock_input, mock_exists, mock_env_vars, capsys
):
    mock_exists.return_value = False  # Model does not exist
    mock_env_vars.setenv("GITWISE_OFFLINE_MODEL", "TestModel/ForDownload")

    # Mock that dependencies are missing
    mock_input.side_effect = ["y"]  # User says yes to install

    # Mock the imports to fail by patching the import mechanism
    with patch.dict(sys.modules, {"torch": None, "huggingface_hub": None}):
        download.download_offline_model()

    # Should have asked to install and run pip
    mock_subprocess_run.assert_called_once_with(
        [sys.executable, "-m", "pip", "install", "gitwise[offline]"]
    )
    captured = capsys.readouterr()
    assert "Offline mode requires 'transformers' and 'torch'" in captured.out


@patch("gitwise.llm.download.os.path.exists")
@patch("gitwise.llm.download.shutil.disk_usage")
def test_download_offline_model_exists(
    mock_disk_usage, mock_exists, mock_env_vars, capsys
):
    mock_exists.return_value = True
    mock_disk_usage.return_value = MagicMock(used=500 * 1024 * 1024)  # 500MB
    mock_env_vars.setenv("GITWISE_OFFLINE_MODEL", "TestModel/Existing")

    # Mock successful imports by creating mock modules
    mock_torch = MagicMock()
    mock_hf_hub = MagicMock()
    mock_hf_hub.snapshot_download = MagicMock()

    with patch.dict(sys.modules, {"torch": mock_torch, "huggingface_hub": mock_hf_hub}):
        download.download_offline_model()

    # Should not try to download since it exists
    mock_hf_hub.snapshot_download.assert_not_called()
    captured = capsys.readouterr()
    assert "Model already present at" in captured.out
    assert "Model disk usage: ~500 MB" in captured.out
