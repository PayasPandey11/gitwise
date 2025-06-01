"""Model presets for OpenRouter online mode selection."""

from typing import Dict, Any

# Model preset definitions for online mode
MODEL_PRESETS = {
    "best": {
        "model": "anthropic/claude-opus-4",
        "name": "Best Model (Most Powerful)",
        "description": "Claude Opus 4 - World's best coding model with advanced reasoning capabilities",
        "characteristics": "Highest quality output, best for complex tasks and coding",
        "pricing": "Premium ($15/M input, $75/M output)",
        "use_case": "Complex coding, advanced reasoning, multi-step problem solving"
    },
    "balanced": {
        "model": "anthropic/claude-3.7-sonnet",
        "name": "Balanced Model (Speed vs Performance)",
        "description": "Claude 3.7 Sonnet - Popular choice with excellent performance at reasonable cost",
        "characteristics": "Great balance of speed, quality, and cost",
        "pricing": "Moderate ($3/M input, $15/M output)",
        "use_case": "General development tasks, good for most use cases"
    },
    "fastest": {
        "model": "anthropic/claude-3-haiku",
        "name": "Fastest Model",
        "description": "Claude 3 Haiku - Optimized for speed with good quality",
        "characteristics": "Fast responses, efficient for simple to moderate tasks",
        "pricing": "Budget-friendly (lowest cost)",
        "use_case": "Quick responses, simple tasks, high-volume usage"
    },
    "custom": {
        "model": None,  # Will be set by user input
        "name": "Custom Model",
        "description": "Enter your own OpenRouter model name",
        "characteristics": "Full flexibility to choose any available model",
        "pricing": "Varies by model",
        "use_case": "When you know exactly which model you want to use"
    }
}

# Default fallback model if user doesn't select any option
DEFAULT_MODEL = MODEL_PRESETS["balanced"]["model"]

def get_model_options() -> Dict[str, Dict[str, Any]]:
    """Get all available model preset options."""
    return MODEL_PRESETS

def get_model_by_key(key: str) -> Dict[str, Any]:
    """Get a specific model preset by key."""
    return MODEL_PRESETS.get(key, MODEL_PRESETS["balanced"])

def validate_custom_model_name(model_name: str) -> bool:
    """
    Validate a custom model name format.
    
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
    invalid_chars = [" ", "\n", "\t", "\\", "\"", "'"]
    if any(char in model_name for char in invalid_chars):
        return False
    
    # Must not be empty after splitting by "/"
    parts = model_name.split("/")
    if len(parts) < 2 or any(not part.strip() for part in parts):
        return False
    
    return True

def get_model_display_info(key: str) -> str:
    """
    Get formatted display information for a model preset.
    
    Args:
        key: The model preset key
        
    Returns:
        str: Formatted display string for the model
    """
    preset = get_model_by_key(key)
    if not preset:
        return ""
    
    return f"{preset['name']}\n  {preset['description']}\n  {preset['characteristics']}\n  Pricing: {preset['pricing']}" 