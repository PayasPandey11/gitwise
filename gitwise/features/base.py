from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import typer
from gitwise.config import ConfigError, get_llm_backend, get_secure_config
from gitwise.core.git_manager import GitManager
from gitwise.exceptions import ConfigurationError, LLMError
from gitwise.ui import components

class BaseFeature(ABC):
    def __init__(self, auto_confirm: bool = False):
        self.auto_confirm = auto_confirm
        self.git_manager = GitManager()
        self.config = self._ensure_config_initialized()
    
    def _ensure_config_initialized(self) -> Dict[str, Any]:
        try:
            return get_secure_config()
        except ConfigError as e:
            components.show_error(str(e))
            
            if self.auto_confirm or typer.confirm(
                "Would you like to run 'gitwise init' now?", default=True
            ):
                from gitwise.cli.init import init_command
                init_command()
                return get_secure_config()
            else:
                raise ConfigurationError(
                    "Configuration is required to use GitWise features"
                ) from e
    
    def get_backend_display_name(self) -> str:
        backend = get_llm_backend()
        display_names = {
            "ollama": "Ollama (local)",
            "online": "Online providers",
            "openai": "OpenAI",
            "anthropic": "Anthropic", 
            "google_gemini": "Google Gemini"
        }
        return display_names.get(backend, backend.title())
    
    def safe_confirm(self, message: str, default: bool = True) -> bool:
        if self.auto_confirm:
            return default
        return typer.confirm(message, default=default)
    
    def show_progress(self, message: str, *, spinner: bool = True):
        if spinner:
            return components.spinner(message)
        else:
            components.show_info(message)
            from contextlib import nullcontext
            return nullcontext()
    
    def handle_llm_error(self, error: Exception, operation: str) -> bool:
        if isinstance(error, LLMError):
            components.show_error(f"LLM error during {operation}: {error}")
        else:
            components.show_error(f"Unexpected error during {operation}: {error}")
        
        backend = get_llm_backend()
        if backend == "ollama":
            components.show_info(
                "Troubleshooting: Ensure Ollama is running with 'ollama serve' "
                "and you have a model installed with 'ollama pull llama3'"
            )
        elif backend == "online":
            components.show_info(
                "Troubleshooting: Check your API keys and network connection"
            )
        
        return False
    
    def validate_git_state(self, require_clean: bool = False) -> bool:
        try:
            self.git_manager.get_current_branch()
            
            if require_clean:
                if self.git_manager.has_staged_changes() or self.git_manager.has_unstaged_changes():
                    components.show_error(
                        "Working directory is not clean. "
                        "Please commit or stash changes first."
                    )
                    return False
            
            return True
            
        except Exception as e:
            components.show_error(f"Git repository error: {e}")
            return False
    
    @abstractmethod
    def execute(self, **kwargs) -> bool:
        pass

class FeatureExecutionResult:
    def __init__(
        self, 
        success: bool, 
        message: Optional[str] = None, 
        data: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.message = message
        self.data = data or {}
    
    def __bool__(self) -> bool:
        return self.success
    
    def __str__(self) -> str:
        return self.message or ("Success" if self.success else "Failed")
    
    def __eq__(self, other):
        if isinstance(other, FeatureExecutionResult):
            return self.success == other.success and self.message == other.message
        return False