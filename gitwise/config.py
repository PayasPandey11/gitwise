"""Handles loading, saving, and validating GitWise configuration files."""

import json
import os
from typing import Any, Dict, Optional

CONFIG_FILENAME = "config.json"
LOCAL_CONFIG_DIR = ".gitwise"
GLOBAL_CONFIG_DIR = os.path.expanduser("~/.gitwise")


class ConfigError(Exception):
    """Configuration error - will be replaced with gitwise.exceptions.ConfigurationError"""
    pass


def get_local_config_path() -> str:
    """Returns the absolute path to the local configuration file."""
    return os.path.join(os.getcwd(), LOCAL_CONFIG_DIR, CONFIG_FILENAME)


def get_global_config_path() -> str:
    """Returns the absolute path to the global configuration file."""
    return os.path.join(GLOBAL_CONFIG_DIR, CONFIG_FILENAME)


def load_config() -> Dict[str, Any]:
    """Load config from local .gitwise/config.json, falling back to global ~/.gitwise/config.json."""
    local_path = get_local_config_path()
    global_path = get_global_config_path()
    for path in [local_path, global_path]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                raise ConfigError(
                    f"Config file at {path} is corrupt or invalid. Please re-run 'gitwise init'."
                )
    raise ConfigError(
        "GitWise is not initialized in this repository. Please run 'gitwise init' first."
    )


def write_config(config: Dict[str, Any], global_config: bool = False) -> str:
    """Write config to .gitwise/config.json (local) or ~/.gitwise/config.json (global). Returns path."""
    if global_config:
        config_dir = GLOBAL_CONFIG_DIR
    else:
        config_dir = os.path.join(os.getcwd(), LOCAL_CONFIG_DIR)
    os.makedirs(config_dir, exist_ok=True)
    path = os.path.join(config_dir, CONFIG_FILENAME)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return path


def config_exists(local_only: bool = False) -> bool:
    """Check if config exists (local or global)."""
    if os.path.exists(get_local_config_path()):
        return True
    if not local_only and os.path.exists(get_global_config_path()):
        return True
    return False


def validate_config(config: Dict[str, Any]) -> bool:
    """Basic validation for required keys based on backend."""
    backend = config.get("llm_backend", "ollama")
    
    # Only support ollama and online backends
    if backend not in {"ollama", "online"}:
        return False
    
    # Validate backend-specific requirements
    if backend == "online":
        # Check for any online provider API key
        has_online_key = any([
            config.get("openrouter_api_key"),
            config.get("openai", {}).get("api_key"),
            config.get("anthropic", {}).get("api_key"),
            config.get("google_gemini", {}).get("api_key"),
        ])
        if not has_online_key:
            return False
    
    # Ollama backend is valid if it exists (model will use defaults)
    return True


def get_llm_backend() -> str:
    """Get the LLM backend from config, or fall back to env var."""
    try:
        config = load_config()
        return config.get("llm_backend", "ollama").lower()
    except ConfigError:
        return os.environ.get("GITWISE_LLM_BACKEND", "ollama").lower()


def get_secure_config() -> Dict[str, Any]:
    """
    Get configuration with secure API key retrieval.
    
    Loads standard config but retrieves API keys from secure storage.
    
    Returns:
        Dict with configuration including securely retrieved API keys
    """
    try:
        config = load_config()
    except ConfigError:
        config = {"llm_backend": "ollama"}
    
    # Import here to avoid circular imports
    from gitwise.security import get_api_key
    
    # Retrieve API keys from secure storage
    secure_keys = {}
    providers = ["openai", "anthropic", "google_gemini", "openrouter"]
    
    for provider in providers:
        api_key = get_api_key(provider)
        if api_key:
            if provider == "openrouter":
                secure_keys["openrouter_api_key"] = api_key
            else:
                if provider not in config:
                    config[provider] = {}
                config[provider]["api_key"] = api_key
    
    # Add legacy OpenRouter support
    if secure_keys:
        config.update(secure_keys)
    
    return config


def should_use_secure_storage() -> bool:
    """Check if secure storage should be used for new API keys."""
    try:
        from gitwise.security import credential_manager
        return credential_manager.keyring_available
    except ImportError:
        return False
