"""
Custom log formatters for GitWise.

Provides user-friendly and debug-friendly formatting options.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any


class GitWiseFormatter(logging.Formatter):
    """
    User-friendly formatter for console output.
    
    Simple, clean format that doesn't overwhelm users with technical details.
    """
    
    def __init__(self):
        # Simple format for user-facing messages
        super().__init__(
            fmt='%(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record for user consumption."""
        
        # Use different prefixes for different levels
        level_prefixes = {
            'WARNING': '⚠️  Warning',
            'ERROR': '❌ Error',
            'CRITICAL': '🚨 Critical',
            'INFO': 'ℹ️  Info'
        }
        
        # Override the levelname for better UX
        original_levelname = record.levelname
        record.levelname = level_prefixes.get(record.levelname, record.levelname)
        
        formatted = super().format(record)
        
        # Restore original levelname
        record.levelname = original_levelname
        
        return formatted


class DebugFormatter(logging.Formatter):
    """
    Detailed formatter for debug logs and file output.
    
    Includes all relevant information for debugging including
    timestamps, module names, and structured data.
    """
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s | %(name)s | %(levelname)8s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with full debugging information."""
        
        # Add extra context if available
        if hasattr(record, 'operation'):
            record.message = f"[{record.operation}] {record.getMessage()}"
        else:
            record.message = record.getMessage()
        
        formatted = super().format(record)
        
        # Add extra data if present
        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process']:
                extra_data[key] = value
        
        # Append extra data if any
        if extra_data:
            formatted += f" | Extra: {json.dumps(extra_data, default=str)}"
        
        return formatted


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Useful for log aggregation and analysis tools.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process']:
                log_entry[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str, separators=(',', ':'))


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for performance-sensitive scenarios.
    
    Minimal overhead while still providing essential information.
    """
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s %(levelname).1s %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with minimal processing."""
        return super().format(record) 