"""Gemini model definitions and presets for Google AI."""

from typing import Dict, Any

# Google Gemini model presets
GEMINI_MODEL_PRESETS = {
    "best": {
        "model": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro (Best Quality)",
        "description": "Google's most capable model with multimodal understanding",
        "characteristics": "Best reasoning, coding, and analysis capabilities",
        "context_window": "2M tokens",
        "use_case": "Complex reasoning, advanced coding, multimodal tasks"
    },
    "balanced": {
        "model": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash (Balanced)",
        "description": "Fast and versatile model with good performance",
        "characteristics": "Great balance of speed, quality, and cost",
        "context_window": "1M tokens", 
        "use_case": "General development tasks, good for most use cases"
    },
    "fastest": {
        "model": "gemini-1.0-pro",
        "name": "Gemini 1.0 Pro (Fast)",
        "description": "Efficient model optimized for speed",
        "characteristics": "Fast responses for text-only tasks",
        "context_window": "32k tokens",
        "use_case": "Quick responses, simple tasks, high-volume usage"
    },
    "multimodal": {
        "model": "gemini-1.5-pro-vision",
        "name": "Gemini 1.5 Pro Vision (Multimodal)",
        "description": "Specialized for image and multimodal understanding", 
        "characteristics": "Excellent for image analysis and vision tasks",
        "context_window": "1M tokens",
        "use_case": "Image analysis, document processing, multimodal tasks"
    }
}

# Default model for Gemini
DEFAULT_GEMINI_MODEL = GEMINI_MODEL_PRESETS["balanced"]["model"]

# Available Gemini models (full list)
AVAILABLE_GEMINI_MODELS = [
    "gemini-1.5-pro",
    "gemini-1.5-flash", 
    "gemini-1.5-pro-vision",
    "gemini-1.0-pro",
    "gemini-pro",  # Legacy alias
    "gemini-pro-vision",  # Legacy alias
]

def get_gemini_model_info(model_name: str) -> Dict[str, Any]:
    """Get information about a specific Gemini model.
    
    Args:
        model_name: The model name to look up
        
    Returns:
        Model information dictionary or empty dict if not found
    """
    for preset in GEMINI_MODEL_PRESETS.values():
        if preset["model"] == model_name:
            return preset
    
    # Return basic info for models not in presets
    if model_name in AVAILABLE_GEMINI_MODELS:
        return {
            "model": model_name,
            "name": model_name,
            "description": f"Google Gemini model: {model_name}",
            "characteristics": "Google's AI model",
            "use_case": "General AI tasks"
        }
    
    return {}

def validate_gemini_model(model_name: str) -> bool:
    """Validate if a model name is a valid Gemini model.
    
    Args:
        model_name: Model name to validate
        
    Returns:
        True if valid, False otherwise
    """
    return model_name in AVAILABLE_GEMINI_MODELS 