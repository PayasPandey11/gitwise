import pytest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys

# Modules to test
from gitwise.llm import router # router is primary entry point
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
    assert call_args[0][0] == "http://localhost:11434/api/generate" # Default URL
    assert call_args[1]["json"]["model"] == "test-ollama-model"
    assert call_args[1]["json"]["prompt"] == "prompt text"

@patch("gitwise.llm.ollama.requests.post")
def test_ollama_get_llm_response_connection_error(mock_post, mock_env_vars):
    mock_post.side_effect = ollama.requests.exceptions.ConnectionError("Test connection error")
    with pytest.raises(ollama.OllamaError, match="Could not connect to Ollama"):
        ollama.get_llm_response("prompt")

# --- Tests for gitwise.llm.offline --- 
@patch("gitwise.llm.offline.AutoTokenizer.from_pretrained")
@patch("gitwise.llm.offline.AutoModelForCausalLM.from_pretrained")
@patch("gitwise.llm.offline.pipeline")
@patch("gitwise.llm.offline.snapshot_download")
@patch("gitwise.llm.offline.os.path.exists")
def test_offline_get_llm_response_success(mock_exists, mock_snapshot, mock_pipeline_constructor, mock_model_loader, mock_tokenizer_loader, mock_env_vars):
    mock_env_vars.setenv("GITWISE_OFFLINE_MODEL", "TestOfflineModel/v1")
    mock_exists.return_value = True # Model exists
    
    mock_tokenizer = MagicMock()
    mock_tokenizer_loader.return_value = mock_tokenizer
    mock_model = MagicMock()
    mock_model_loader.return_value = mock_model
    
    mock_pipe_instance = MagicMock()
    mock_pipe_instance.return_value = [{"generated_text": "Offline prompt text then offline says hello"}] # Simulate prompt being part of output
    mock_pipeline_constructor.return_value = mock_pipe_instance

    # Reset _model_ready for a clean test, as it's a global in offline.py
    offline._model_ready = False 
    response = offline.get_llm_response("Offline prompt text then ")
    assert response == "offline says hello"
    
    mock_tokenizer_loader.assert_called_once_with("TestOfflineModel/v1")
    mock_model_loader.assert_called_once_with("TestOfflineModel/v1", torch_dtype=offline.torch.float32)
    mock_pipeline_constructor.assert_called_once_with("text-generation", model=mock_model, tokenizer=mock_tokenizer, device=-1)
    mock_pipe_instance.assert_called_once()
    assert offline._model_ready is True

@patch("gitwise.llm.offline.snapshot_download")
@patch("gitwise.llm.offline.os.path.exists")
@patch("gitwise.llm.offline.input", return_value='n') # User says no to download
def test_offline_ensure_model_download_prompt_no(mock_input, mock_exists, mock_snapshot, mock_env_vars):
    mock_exists.return_value = False # Model does not exist
    offline._model_ready = False 
    with pytest.raises(SystemExit): # Should exit if user says no
        offline.ensure_offline_model_ready()
    mock_snapshot.assert_not_called()

# --- Tests for gitwise.llm.online --- 
@patch("gitwise.llm.online.OpenAI")
def test_online_get_llm_response_success(mock_openai_constructor, mock_config_load, mock_env_vars):
    mock_config_load.return_value = {
        "openrouter_api_key": "test_api_key_from_config",
        "openrouter_model": "test_model_from_config"
    }
    
    mock_client_instance = MagicMock()
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="Online says hello"))]
    mock_client_instance.chat.completions.create.return_value = mock_completion
    mock_openai_constructor.return_value = mock_client_instance

    response = online.get_llm_response("prompt text")
    assert response == "Online says hello"
    mock_openai_constructor.assert_called_once_with(base_url="https://openrouter.ai/api/v1", api_key="test_api_key_from_config")
    mock_client_instance.chat.completions.create.assert_called_once()
    call_args = mock_client_instance.chat.completions.create.call_args
    assert call_args[1]["model"] == "test_model_from_config"
    assert call_args[1]["messages"] == [{"role": "user", "content": "prompt text"}]

@patch("gitwise.llm.online.OpenAI")
def test_online_get_llm_response_no_apikey(mock_openai_constructor, mock_config_load, mock_env_vars):
    mock_config_load.return_value = {} # No API key in config
    # Ensure OPENROUTER_API_KEY is not in env by virtue of mock_env_vars fixture
    with pytest.raises(RuntimeError, match="OpenRouter API key not found"):
        online.get_llm_response("prompt")

# --- Tests for gitwise.llm.router --- 
@patch("gitwise.config.get_llm_backend")
@patch("gitwise.llm.router.ollama_llm") # Mock the routed-to function
def test_router_routes_to_ollama(mock_ollama_call, mock_get_backend):
    mock_get_backend.return_value = "ollama"
    mock_ollama_call.return_value = "Ollama response via router"
    
    response = router.get_llm_response("test prompt", model="ollama-model-override")
    assert response == "Ollama response via router"
    mock_ollama_call.assert_called_once_with("test prompt", model="ollama-model-override")

@patch("gitwise.config.get_llm_backend")
@patch("gitwise.llm.router.offline_llm") # Mock the routed-to function
def test_router_routes_to_offline(mock_offline_call, mock_get_backend):
    mock_get_backend.return_value = "offline"
    mock_offline_call.return_value = "Offline response via router"
    
    response = router.get_llm_response("test prompt")
    assert response == "Offline response via router"
    mock_offline_call.assert_called_once_with("test prompt")

@patch("gitwise.config.get_llm_backend")
@patch("gitwise.llm.router.online_llm") # Mock the routed-to function
def test_router_routes_to_online(mock_online_call, mock_get_backend):
    mock_get_backend.return_value = "online"
    mock_online_call.return_value = "Online response via router"
    
    response = router.get_llm_response("test prompt")
    assert response == "Online response via router"
    mock_online_call.assert_called_once_with("test prompt")

@patch("gitwise.config.get_llm_backend")
@patch("gitwise.llm.router.ollama_llm")
@patch("gitwise.llm.router.offline_llm")
@patch("gitwise.llm.router.time.sleep") # Mock sleep to speed up test
def test_router_ollama_fallback_to_offline(mock_sleep, mock_offline_call, mock_ollama_call, mock_get_backend, capsys):
    mock_get_backend.return_value = "ollama"
    mock_ollama_call.side_effect = ollama.OllamaError("Ollama connect failed")
    mock_offline_call.return_value = "Offline fallback success"

    response = router.get_llm_response("test prompt")
    assert response == "Offline fallback success"
    assert mock_ollama_call.call_count == 3 # Default 3 retries
    mock_offline_call.assert_called_once_with("test prompt")
    captured = capsys.readouterr()
    assert "Ollama connection attempt 1/3 failed" in captured.out
    assert "Ollama connection attempt 2/3 failed" in captured.out
    assert "Ollama connection attempt 3/3 failed" in captured.out
    assert "Ollama failed after multiple retries. Attempting to fall back to offline model." in captured.out
    assert "Attempting to use offline model as fallback..." in captured.out

@patch("gitwise.config.get_llm_backend")
@patch("gitwise.llm.router.ollama_llm")
@patch("gitwise.llm.router.offline_llm")
@patch("gitwise.llm.router.time.sleep")
def test_router_ollama_fallback_offline_fails_too(mock_sleep, mock_offline_call, mock_ollama_call, mock_get_backend):
    mock_get_backend.return_value = "ollama"
    mock_ollama_call.side_effect = ollama.OllamaError("Ollama connect failed")
    mock_offline_call.side_effect = RuntimeError("Offline model load failed")

    with pytest.raises(RuntimeError, match="Ollama backend failed AND offline fallback also failed with an error: Offline model load failed"):
        router.get_llm_response("test prompt")

# --- Tests for gitwise.llm.download --- 
@patch("gitwise.llm.download.snapshot_download")
@patch("gitwise.llm.download.os.path.exists")
@patch("gitwise.llm.download.input", return_value='y') # User says yes to download
@patch("gitwise.llm.download.shutil.disk_usage")
def test_download_offline_model_downloads_if_not_exists(mock_disk_usage, mock_input, mock_exists, mock_snapshot, mock_env_vars, capsys):
    mock_exists.return_value = False # Model does not exist
    mock_env_vars.setenv("GITWISE_OFFLINE_MODEL", "TestModel/ForDownload")
    mock_snapshot.return_value = "/fake/path/to/model"
    
    # Mock missing transformers and torch initially to test that part of the flow too
    with patch.dict(sys.modules, {'transformers': None, 'torch': None}):
        with patch("gitwise.llm.download.subprocess.run") as mock_pip_install:
             # First call to download_offline_model will try to install deps
            download.download_offline_model() 
            mock_pip_install.assert_called_once_with([sys.executable, "-m", "pip", "install", "gitwise[offline]"])
    
    # Now assume deps are installed for the actual download part
    # We need to re-patch os.path.exists because the module was reloaded effectively
    with patch("gitwise.llm.download.os.path.exists", return_value=False) as mock_exists_again, \
         patch("gitwise.llm.download.snapshot_download", return_value="/fake/path/to/model") as mock_snapshot_again, \
         patch("gitwise.llm.download.input", return_value='y'): # Re-patch input for this scope
        download.download_offline_model() # Call again
    
    mock_exists_again.assert_called_once()
    mock_snapshot_again.assert_called_once_with(repo_id="TestModel/ForDownload", local_files_only=False)
    captured = capsys.readouterr()
    assert "Model downloaded to: /fake/path/to/model" in captured.out

@patch("gitwise.llm.download.os.path.exists")
@patch("gitwise.llm.download.shutil.disk_usage")
def test_download_offline_model_exists(mock_disk_usage, mock_exists, capsys):
    mock_exists.return_value = True
    mock_disk_usage.return_value = MagicMock(used=500 * 1024 * 1024) # 500MB
    # Ensure transformers and torch are importable for this test case directly
    with patch.dict(sys.modules, {'transformers': MagicMock(), 'torch': MagicMock()}):
        download.download_offline_model()
    captured = capsys.readouterr()
    assert "Model already present at" in captured.out
    assert "Model disk usage: ~500 MB" in captured.out 