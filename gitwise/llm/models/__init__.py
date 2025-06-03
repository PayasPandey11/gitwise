"""Model definitions and presets for different LLM providers."""

# Import model definitions
try:
    from .gemini_models import GEMINI_MODEL_PRESETS, DEFAULT_GEMINI_MODEL, AVAILABLE_GEMINI_MODELS
except ImportError:
    GEMINI_MODEL_PRESETS = {}
    DEFAULT_GEMINI_MODEL = None
    AVAILABLE_GEMINI_MODELS = []

# TODO: Import other provider models when implemented
# from .openai_models import OPENAI_MODEL_PRESETS, DEFAULT_OPENAI_MODEL, AVAILABLE_OPENAI_MODELS
# from .claude_models import CLAUDE_MODEL_PRESETS, DEFAULT_CLAUDE_MODEL, AVAILABLE_CLAUDE_MODELS
# from .openrouter_models import OPENROUTER_MODEL_PRESETS, DEFAULT_OPENROUTER_MODEL, AVAILABLE_OPENROUTER_MODELS

__all__ = [
    "GEMINI_MODEL_PRESETS",
    "DEFAULT_GEMINI_MODEL", 
    "AVAILABLE_GEMINI_MODELS",
] 