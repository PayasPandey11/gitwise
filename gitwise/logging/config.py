"""
Logging configuration for GitWise.

Handles setup of loggers, handlers, formatters with privacy and performance in mind.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Dict, Any

from .formatters import GitWiseFormatter, DebugFormatter
from .handlers import SafeRotatingFileHandler


def get_log_level_from_config() -> int:
    """
    Get log level from GitWise config or environment.
    
    Returns:
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    try:
        from gitwise.config import load_config
        config = load_config()
        level_str = config.get("log_level", "INFO").upper()
    except Exception:
        # Fallback to environment variable
        level_str = os.environ.get("GITWISE_LOG_LEVEL", "INFO").upper()
    
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO, 
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    return level_mapping.get(level_str, logging.INFO)


def get_log_directory() -> Path:
    """
    Get the directory where log files should be stored.
    
    Returns:
        Path to log directory (creates if doesn't exist)
    """
    # Try local .gitwise directory first, then global
    local_log_dir = Path.cwd() / ".gitwise" / "logs"
    global_log_dir = Path.home() / ".gitwise" / "logs"
    
    # Prefer local directory if we're in a git repository
    if (Path.cwd() / ".git").exists():
        log_dir = local_log_dir
    else:
        log_dir = global_log_dir
    
    # Create directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging() -> None:
    """
    Setup GitWise logging configuration.
    
    Creates:
    - Console handler for user-facing logs (WARNING+ only)
    - File handler for debug logs (configurable level)
    - Proper formatters and filters
    """
    # Get the root GitWise logger
    logger = logging.getLogger('gitwise')
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return
    
    log_level = get_log_level_from_config()
    logger.setLevel(logging.DEBUG)  # Capture everything, filter at handler level
    
    # Console handler - only show important messages to users
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Users only see warnings/errors
    console_handler.setFormatter(GitWiseFormatter())
    
    # File handler - debug logs for developers/troubleshooting
    log_dir = get_log_directory()
    log_file = log_dir / "gitwise.log"
    
    file_handler = SafeRotatingFileHandler(
        filename=str(log_file),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(DebugFormatter())
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False


def get_debug_mode() -> bool:
    """Check if debug mode is enabled via config or environment."""
    try:
        from gitwise.config import load_config
        config = load_config()
        return config.get("debug", False)
    except Exception:
        return os.environ.get("GITWISE_DEBUG", "").lower() in ("1", "true", "yes")


def update_log_level(level: str) -> None:
    """
    Update the log level for file handler at runtime.
    
    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level_mapping = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING, 
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    new_level = level_mapping.get(level.upper())
    if new_level is None:
        return
    
    logger = logging.getLogger('gitwise')
    for handler in logger.handlers:
        if isinstance(handler, (logging.FileHandler, SafeRotatingFileHandler)):
            handler.setLevel(new_level) 