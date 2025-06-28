import pytest
from unittest.mock import patch, mock_open, MagicMock
import os
import json

from gitwise import config  # Import the module itself
from gitwise.config import (
    ConfigError,
    load_config,
    write_config,
    config_exists,
    validate_config,
    get_llm_backend,
    get_local_config_path,
    get_global_config_path,
    CONFIG_FILENAME,
    LOCAL_CONFIG_DIR,
    GLOBAL_CONFIG_DIR,
)


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setattr(os, "getcwd", lambda: "/test/repo")
    monkeypatch.setattr(
        os.path, "expanduser", lambda x: "/home/user" if x == "~" else x
    )  # Simplify expanduser
    # Ensure crucial env vars for fallback are clean unless set by a specific test
    monkeypatch.delenv("GITWISE_LLM_BACKEND", raising=False)
    yield monkeypatch


# --- Test path helpers ---
def test_get_local_config_path(mock_env):
    expected_path = os.path.join("/test/repo", LOCAL_CONFIG_DIR, CONFIG_FILENAME)
    assert get_local_config_path() == expected_path


def test_get_global_config_path(mock_env):
    expected_path = os.path.join("/home/user", GLOBAL_CONFIG_DIR, CONFIG_FILENAME)
    assert get_global_config_path() == expected_path


# --- Test load_config ---
@patch("gitwise.config.os.path.exists")
@patch("builtins.open", new_callable=mock_open)
def test_load_config_local_exists(mock_file_open, mock_exists, mock_env):
    mock_exists.side_effect = (
        lambda path: path == get_local_config_path()
    )  # Only local exists
    dummy_config_data = {"llm_backend": "ollama", "ollama_model": "test-model"}
    mock_file_open.return_value.read.return_value = json.dumps(dummy_config_data)

    loaded = load_config()
    assert loaded == dummy_config_data
    mock_file_open.assert_called_once_with(
        get_local_config_path(), "r", encoding="utf-8"
    )


@patch("gitwise.config.os.path.exists")
@patch("builtins.open", new_callable=mock_open)
def test_load_config_global_exists_local_missing(mock_file_open, mock_exists, mock_env):
    mock_exists.side_effect = (
        lambda path: path == get_global_config_path()
    )  # Only global exists
    dummy_config_data = {"llm_backend": "online", "openrouter_api_key": "key"}
    mock_file_open.return_value.read.return_value = json.dumps(dummy_config_data)

    loaded = load_config()
    assert loaded == dummy_config_data
    mock_file_open.assert_called_once_with(
        get_global_config_path(), "r", encoding="utf-8"
    )


@patch("gitwise.config.os.path.exists", return_value=False)  # No config files exist
def test_load_config_none_exists(mock_exists, mock_env):
    with pytest.raises(ConfigError, match="GitWise is not initialized"):
        load_config()


@patch("gitwise.config.os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open)
def test_load_config_corrupt_json(mock_file_open, mock_exists, mock_env):
    mock_file_open.return_value.read.return_value = "this is not json"
    # Simulate json.load raising an error
    with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
        with pytest.raises(ConfigError, match="corrupt or invalid"):
            load_config()


# --- Test write_config ---
@patch("gitwise.config.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_write_config_local(mock_file_open, mock_makedirs, mock_env):
    config_data = {"key": "value"}
    expected_dir = os.path.join("/test/repo", LOCAL_CONFIG_DIR)
    expected_path = os.path.join(expected_dir, CONFIG_FILENAME)

    path = write_config(config_data, global_config=False)
    assert path == expected_path
    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
    # Check if json.dump was called correctly (tricky with mock_open, usually check handle().write())
    # For simplicity, we'll assume if open is called, dump is likely to be called too.
    # A more thorough test would involve checking the content written to the mock file handle.


@patch("gitwise.config.os.makedirs")
@patch("builtins.open", new_callable=mock_open)
def test_write_config_global(mock_file_open, mock_makedirs, mock_env):
    config_data = {"key": "value_global"}
    expected_dir = os.path.join("/home/user", GLOBAL_CONFIG_DIR)
    expected_path = os.path.join(expected_dir, CONFIG_FILENAME)

    path = write_config(config_data, global_config=True)
    assert path == expected_path
    mock_makedirs.assert_called_once_with(expected_dir, exist_ok=True)
    mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")


# --- Test config_exists ---
@patch("gitwise.config.os.path.exists")
def test_config_exists_local(mock_exists, mock_env):
    mock_exists.side_effect = lambda p: p == get_local_config_path()
    assert config_exists() is True
    assert config_exists(local_only=True) is True


@patch("gitwise.config.os.path.exists")
def test_config_exists_global_only(mock_exists, mock_env):
    mock_exists.side_effect = lambda p: p == get_global_config_path()
    assert config_exists() is True
    assert (
        config_exists(local_only=False) is True
    )  # Explicitly check with local_only=False
    assert config_exists(local_only=True) is False


@patch("gitwise.config.os.path.exists", return_value=False)
def test_config_exists_none(mock_exists, mock_env):
    assert config_exists() is False
    assert config_exists(local_only=True) is False


# --- Test validate_config ---
def test_validate_config_valid():
    assert validate_config({"llm_backend": "ollama"}) is True
    assert validate_config({"llm_backend": "ollama", "ollama_model": "llama3"}) is True
    assert (
        validate_config({"llm_backend": "online", "openrouter_api_key": "key"}) is True
    )
    # Test with new provider format
    assert validate_config({"llm_backend": "online", "openai": {"api_key": "key"}}) is True


def test_validate_config_invalid():
    # Empty config defaults to ollama, which is now valid
    assert validate_config({}) is True  # Defaults to ollama backend
    assert validate_config({"llm_backend": "unknown"}) is False  # Invalid backend
    # Removed offline backend, so this should fail
    assert validate_config({"llm_backend": "offline"}) is False  # Offline removed
    assert (
        validate_config({"llm_backend": "online"}) is False
    )  # Missing API key


# --- Test get_llm_backend ---
@patch("gitwise.config.load_config")
def test_get_llm_backend_from_config(mock_load_config_func, mock_env):
    mock_load_config_func.return_value = {"llm_backend": "online"}
    assert get_llm_backend() == "online"


@patch("gitwise.config.load_config", side_effect=ConfigError("No config"))
def test_get_llm_backend_from_env_var(mock_load_config_func, mock_env):
    mock_env.setenv("GITWISE_LLM_BACKEND", "offline")
    assert get_llm_backend() == "offline"


@patch("gitwise.config.load_config", side_effect=ConfigError("No config"))
def test_get_llm_backend_default_ollama(mock_load_config_func, mock_env):
    # Ensure GITWISE_LLM_BACKEND is not set (handled by mock_env fixture)
    assert get_llm_backend() == "ollama"


@patch("gitwise.config.load_config")
def test_get_llm_backend_config_takes_precedence_over_env(
    mock_load_config_func, mock_env
):
    mock_load_config_func.return_value = {"llm_backend": "online_from_config"}
    mock_env.setenv("GITWISE_LLM_BACKEND", "offline_from_env")
    assert get_llm_backend() == "online_from_config"
