"""OpenRouter model definitions and presets."""

from typing import Dict, Any, List

# Model preset definitions for OpenRouter
OPENROUTER_MODEL_PRESETS = {
    "best": {
        "model": "anthropic/claude-3.5-sonnet",
        "name": "Best Model (Most Powerful)",
        "description": "Claude 3.5 Sonnet - World's best coding model with advanced reasoning capabilities",
        "characteristics": "Highest quality output, best for complex tasks and coding",
        "pricing": "Premium ($3/M input, $15/M output)",
        "use_case": "Complex coding, advanced reasoning, multi-step problem solving",
    },
    "balanced": {
        "model": "anthropic/claude-3-haiku",
        "name": "Balanced Model (Speed vs Performance)",
        "description": "Claude 3 Haiku - Popular choice with excellent performance at reasonable cost",
        "characteristics": "Great balance of speed, quality, and cost",
        "pricing": "Moderate ($0.25/M input, $1.25/M output)",
        "use_case": "General development tasks, good for most use cases",
    },
    "fastest": {
        "model": "google/gemma-2-9b-it",
        "name": "Fastest Model",
        "description": "Google Gemma 2 - Optimized for speed with good quality",
        "characteristics": "Fast responses, efficient for simple to moderate tasks",
        "pricing": "Budget-friendly (free)",
        "use_case": "Quick responses, simple tasks, high-volume usage",
    },
    "custom": {
        "model": None,  # Will be set by user input
        "name": "Custom Model",
        "description": "Enter your own OpenRouter model name",
        "characteristics": "Full flexibility to choose any available model",
        "pricing": "Varies by model",
        "use_case": "When you know exactly which model you want to use",
    },
}

# Default fallback model if user doesn't select any option
DEFAULT_OPENROUTER_MODEL = OPENROUTER_MODEL_PRESETS["balanced"]["model"]

# For OpenRouter, the list of available models is vast and dynamic.
# We will list the preset models as a starting point.
AVAILABLE_OPENROUTER_MODELS = [
    preset["model"] for preset in OPENROUTER_MODEL_PRESETS.values() if preset["model"]
]


def get_openrouter_model_info(model_name: str) -> Dict[str, Any]:
    """Get information about a specific OpenRouter model preset.

    Args:
        model_name: The model name to look up

    Returns:
        Model information dictionary or a basic dict if not in presets.
    """
    for preset in OPENROUTER_MODEL_PRESETS.values():
        if preset["model"] == model_name:
            return preset

    # For custom models, return a basic info dict
    return {
        "model": model_name,
        "name": model_name,
        "description": f"Custom OpenRouter model: {model_name}",
        "characteristics": "User-specified model",
        "use_case": "Specific user requirements",
    }


def validate_openrouter_model(model_name: str) -> bool:
    """Validate a custom model name format for OpenRouter.

    Args:
        model_name: The model name to validate

    Returns:
        bool: True if the format appears valid, False otherwise
    """
    if not model_name or not isinstance(model_name, str):
        return False

    # Basic validation - OpenRouter models typically follow "provider/model-name" format
    model_name = model_name.strip()

    # Must contain at least one forward slash
    if "/" not in model_name:
        return False

    # Should not contain spaces or special characters that would break API calls
    invalid_chars = [" ", "\n", "\t", "\\", '"', "'"]
    if any(char in model_name for char in invalid_chars):
        return False

    # Must not be empty after splitting by "/"
    parts = model_name.split("/")
    if len(parts) < 2 or any(not part.strip() for part in parts):
        return False

    return True 