"""
GitWise Logging System

Provides privacy-safe, performance-optimized logging for debugging support.
All logs are sanitized to remove API keys, tokens, and personal information.

Usage:
    from gitwise.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("Operation completed", extra={'operation': 'commit'})
"""

import logging
import os
from typing import Optional

from .config import setup_logging
from .filters import PrivacyFilter

# Global flag to track if logging has been initialized
_logging_initialized = False


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given module name.
    
    Args:
        name: Usually __name__ from the calling module
        
    Returns:
        Configured logger instance with privacy filters
    """
    global _logging_initialized
    
    # Initialize logging on first use (lazy initialization)
    if not _logging_initialized:
        setup_logging()
        _logging_initialized = True
    
    logger = logging.getLogger(name)
    
    # Add privacy filter if not already present
    if not any(isinstance(f, PrivacyFilter) for f in logger.filters):
        logger.addFilter(PrivacyFilter())
    
    return logger


def reset_logging():
    """Reset logging state - useful for testing."""
    global _logging_initialized
    _logging_initialized = False
    
    # Clear all handlers
    root_logger = logging.getLogger('gitwise')
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)


# Public API
__all__ = ['get_logger', 'reset_logging'] 