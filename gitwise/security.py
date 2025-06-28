import os
from typing import Optional, Dict
from gitwise.exceptions import SecurityError
from gitwise.ui import components

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    components.show_warning(
        "Keyring not available. API keys will be stored in environment variables only. "
        "Install keyring for secure storage: pip install keyring"
    )

SERVICE_NAME = "gitwise"
SUPPORTED_PROVIDERS = {
    "openai": "OpenAI API Key",
    "anthropic": "Anthropic API Key", 
    "google_gemini": "Google Gemini API Key",
    "openrouter": "OpenRouter API Key"
}

class SecureCredentialManager:
    def __init__(self):
        self.keyring_available = KEYRING_AVAILABLE
    
    def store_api_key(self, provider: str, api_key: str) -> bool:
        if provider not in SUPPORTED_PROVIDERS:
            raise SecurityError(f"Unsupported provider: {provider}")
        if not api_key or not api_key.strip():
            raise SecurityError("API key cannot be empty")
        
        self._validate_api_key(provider, api_key)
        username = f"{provider}_api_key"
        
        if self.keyring_available:
            try:
                keyring.set_password(SERVICE_NAME, username, api_key)
                return True
            except Exception as e:
                components.show_warning(f"Keychain storage failed: {e}")
                return self._store_in_env_fallback(provider, api_key)
        else:
            return self._store_in_env_fallback(provider, api_key)
    
    def get_api_key(self, provider: str) -> Optional[str]:
        if provider not in SUPPORTED_PROVIDERS:
            raise SecurityError(f"Unsupported provider: {provider}")
        
        username = f"{provider}_api_key"
        
        if self.keyring_available:
            try:
                api_key = keyring.get_password(SERVICE_NAME, username)
                if api_key:
                    return api_key
            except Exception:
                pass
        
        env_var_name = f"{provider.upper()}_API_KEY"
        if provider == "google_gemini":
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        else:
            api_key = os.environ.get(env_var_name)
        
        return api_key
    
    def list_stored_keys(self) -> Dict[str, bool]:
        stored_keys = {}
        for provider in SUPPORTED_PROVIDERS:
            api_key = self.get_api_key(provider)
            stored_keys[provider] = bool(api_key)
        return stored_keys
    
    def _validate_api_key(self, provider: str, api_key: str) -> None:
        api_key = api_key.strip()
        
        if provider == "openai":
            if not api_key.startswith("sk-"):
                raise SecurityError("OpenAI API key must start with 'sk-'")
        elif provider == "anthropic":
            if not api_key.startswith("sk-ant-"):
                raise SecurityError("Anthropic API key must start with 'sk-ant-'")
        elif provider == "openrouter":
            if not api_key.startswith("sk-or-"):
                raise SecurityError("OpenRouter API key must start with 'sk-or-'")
        elif provider == "google_gemini":
            if not api_key.startswith("AIza"):
                components.show_warning("Google API key should typically start with 'AIza'")
        
        if len(api_key) < 20:
            raise SecurityError("API key appears too short to be valid")
    
    def _store_in_env_fallback(self, provider: str, api_key: str) -> bool:
        env_var_name = f"{provider.upper()}_API_KEY"
        os.environ[env_var_name] = api_key
        return False

credential_manager = SecureCredentialManager()

def store_api_key(provider: str, api_key: str) -> bool:
    return credential_manager.store_api_key(provider, api_key)

def get_api_key(provider: str) -> Optional[str]:
    return credential_manager.get_api_key(provider)

def list_stored_keys() -> Dict[str, bool]:
    return credential_manager.list_stored_keys()