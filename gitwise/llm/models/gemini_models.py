"""Gemini model definitions and presets for Google AI."""

from typing import Dict, Any

# Google Gemini model presets
GEMINI_MODEL_PRESETS = {
    "best": {
        "model": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash (Best Quality)",
        "description": "Google's most advanced and capable model with enhanced reasoning",
        "characteristics": "Latest generation with superior reasoning, coding, and analysis capabilities",
        "context_window": "1M tokens",
        "use_case": "Complex reasoning, advanced coding, multimodal tasks"
    },
    "balanced": {
        "model": "gemini-2.0-flash",
        "name": "Gemini 2.0 Flash (Balanced)",
        "description": "Fast and versatile next-generation model with excellent performance",
        "characteristics": "Great balance of speed, quality, and cost with latest capabilities",
        "context_window": "1M tokens", 
        "use_case": "General development tasks, good for most use cases"
    },
    "fastest": {
        "model": "gemini-2.0-flash-lite",
        "name": "Gemini 2.0 Flash-Lite (Fast)",
        "description": "Lightweight model optimized for speed and efficiency",
        "characteristics": "Ultra-fast responses while maintaining good quality",
        "context_window": "1M tokens",
        "use_case": "Quick responses, simple tasks, high-volume usage"
    },
    "multimodal": {
        "model": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash (Multimodal)",
        "description": "Advanced model with excellent multimodal understanding", 
        "characteristics": "Superior image analysis and vision capabilities",
        "context_window": "1M tokens",
        "use_case": "Image analysis, document processing, multimodal tasks"
    }
}

# Default model for Gemini
DEFAULT_GEMINI_MODEL = GEMINI_MODEL_PRESETS["balanced"]["model"]

# Available Gemini models (full list)
AVAILABLE_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash", 
    "gemini-2.0-flash-lite",
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