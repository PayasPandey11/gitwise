"""
Privacy filters for GitWise logging.

Automatically redacts sensitive information like API keys, tokens, personal paths,
and other sensitive data to ensure logs can be safely shared.
"""

import logging
import re
import os
from pathlib import Path
from typing import Pattern, List


class PrivacyFilter(logging.Filter):
    """
    Filter that redacts sensitive information from log records.
    
    Redacts:
    - API keys and tokens
    - Personal file paths  
    - Email addresses
    - URLs with credentials
    - Environment variables with secrets
    """
    
    def __init__(self):
        super().__init__()
        self._setup_patterns()
        self._user_home = str(Path.home())
        self._username = os.environ.get('USER', os.environ.get('USERNAME', 'user'))
    
    def _setup_patterns(self) -> None:
        """Setup regex patterns for sensitive data detection."""
        
        # API Keys and tokens (various formats)
        self._api_key_patterns = [
            re.compile(r'(?i)(api[_\s-]*key\s*[=:]\s*)["\']?([a-zA-Z0-9_-]{10,})["\']?'),
            re.compile(r'(?i)(token\s*[=:]\s*)["\']?([a-zA-Z0-9_.-]{10,})["\']?'),
            re.compile(r'(?i)(bearer\s+)([a-zA-Z0-9_.-]{10,})'),
            re.compile(r'(?i)(authorization[:\s]+bearer\s+)([a-zA-Z0-9_.-]{10,})'),
            re.compile(r'(?i)(openrouter[_-]?api[_-]?key\s*[=:]\s*)["\']?([a-zA-Z0-9_-]{10,})["\']?'),
            re.compile(r'(?i)(openai[_-]?api[_-]?key\s*[=:]\s*)["\']?([a-zA-Z0-9_-]{10,})["\']?'),
            # GitHub tokens
            re.compile(r'(gh[pousr]_[A-Za-z0-9_]{36,})'),
            # Generic patterns for "key: value" or "key = value"
            re.compile(r'(?i)(key|token|secret|password)["\']?\s*[=:]\s*["\']?([a-zA-Z0-9+/=_-]{8,})["\']?'),
            # Common API key formats like sk-... 
            re.compile(r'(sk-[a-zA-Z0-9]{20,})'),
        ]
        
        # Environment variables that commonly contain secrets
        self._env_secret_patterns = [
            re.compile(r'(?i)(export\s+)?([A-Z_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)[A-Z_]*\s*=\s*)([^\s\'\"]+)'),
        ]
        
        # Email patterns
        self._email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        
        # URLs with credentials
        self._url_cred_pattern = re.compile(r'(https?://)[^:\s]+:[^@\s]+@([^\s]+)')
    
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter the log record, redacting sensitive information.
        
        Args:
            record: The log record to filter
            
        Returns:
            True (always allow the record through after filtering)
        """
        # Apply filters to the message
        if hasattr(record, 'msg') and record.msg:
            record.msg = self._redact_sensitive_data(str(record.msg))
        
        # Apply filters to any args
        if hasattr(record, 'args') and record.args:
            filtered_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    filtered_args.append(self._redact_sensitive_data(arg))
                else:
                    filtered_args.append(arg)
            record.args = tuple(filtered_args)
        
        # Apply filters to pathname (remove personal path info)
        if hasattr(record, 'pathname'):
            record.pathname = self._redact_personal_path(record.pathname)
        
        return True
    
    def _redact_sensitive_data(self, text: str) -> str:
        """
        Redact sensitive data from a text string.
        
        Args:
            text: Text to redact
            
        Returns:
            Text with sensitive data replaced with placeholders
        """
        # Redact API keys and tokens
        for pattern in self._api_key_patterns:
            text = pattern.sub(r'\1[REDACTED_API_KEY]', text)
        
        # Redact environment variables with secrets
        for pattern in self._env_secret_patterns:
            text = pattern.sub(r'\1\2[REDACTED_SECRET]', text)
        
        # Redact emails
        text = self._email_pattern.sub('[REDACTED_EMAIL]', text)
        
        # Redact URLs with credentials
        text = self._url_cred_pattern.sub(r'\1[REDACTED_CREDS]@\2', text)
        
        # Redact personal paths
        text = self._redact_personal_path(text)
        
        return text
    
    def _redact_personal_path(self, path: str) -> str:
        """
        Redact personal information from file paths.
        
        Args:
            path: File path string
            
        Returns:
            Path with personal info redacted
        """
        # Replace home directory with placeholder
        if self._user_home in path:
            path = path.replace(self._user_home, '~')
        
        # Replace username in paths
        path = re.sub(f'/Users/{self._username}/', '/Users/[USER]/', path)
        path = re.sub(f'/home/{self._username}/', '/home/[USER]/', path)
        path = re.sub(f'C:\\\\Users\\\\{self._username}\\\\', 'C:\\\\Users\\\\[USER]\\\\', path)
        
        return path


class PerformanceSensitiveFilter(logging.Filter):
    """
    Filter that drops or throttles logs that might impact performance.
    
    Designed to prevent excessive logging in tight loops or high-frequency operations.
    """
    
    def __init__(self, max_frequency: int = 10):
        """
        Initialize performance filter.
        
        Args:
            max_frequency: Maximum logs per second for performance-sensitive operations
        """
        super().__init__()
        self._max_frequency = max_frequency
        self._last_log_times = {}
        
    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter records based on performance considerations.
        
        Args:
            record: Log record to evaluate
            
        Returns:
            True if record should be processed, False if throttled
        """
        import time
        
        # Check if this is a performance-sensitive operation
        if hasattr(record, 'performance_sensitive') and record.performance_sensitive:
            current_time = time.time()
            key = f"{record.name}:{record.levelno}"
            
            last_time = self._last_log_times.get(key, 0)
            time_diff = current_time - last_time
            
            # Throttle if logging too frequently
            if time_diff < (1.0 / self._max_frequency):
                return False
            
            self._last_log_times[key] = current_time
        
        return True 