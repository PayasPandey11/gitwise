"""
Custom log handlers for GitWise.

Provides safe file handling, rotation, and performance optimizations.
"""

import logging
import logging.handlers
import os
import time
from pathlib import Path
from typing import Optional


class SafeRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    Enhanced RotatingFileHandler with better error handling and safety.
    
    Handles cases where log files might be locked or inaccessible.
    """
    
    def __init__(self, filename: str, mode: str = 'a', maxBytes: int = 0, 
                 backupCount: int = 0, encoding: Optional[str] = None, 
                 delay: bool = False):
        
        # Ensure the directory exists
        log_dir = Path(filename).parent
        log_dir.mkdir(parents=True, exist_ok=True)
        
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record, with enhanced error handling.
        
        Args:
            record: The log record to emit
        """
        try:
            super().emit(record)
        except Exception as e:
            # If we can't write to the file, fall back to stderr
            # but don't raise an exception that would break the application
            self.handleError(record)
    
    def doRollover(self) -> None:
        """
        Perform rollover with enhanced error handling.
        """
        try:
            super().doRollover()
        except Exception:
            # If rollover fails, continue with current file
            # This prevents logging from completely breaking the app
            pass


class AsyncFileHandler(logging.Handler):
    """
    Asynchronous file handler for high-performance logging.
    
    Queues log records and writes them asynchronously to avoid blocking
    the main application thread.
    """
    
    def __init__(self, filename: str, maxBytes: int = 10*1024*1024, 
                 backupCount: int = 5, encoding: str = 'utf-8'):
        super().__init__()
        
        self._file_handler = SafeRotatingFileHandler(
            filename=filename,
            maxBytes=maxBytes, 
            backupCount=backupCount,
            encoding=encoding
        )
        
        # Simple queue implementation without external dependencies
        self._queue = []
        self._queue_lock = None
        self._worker_thread = None
        self._shutdown = False
        
        try:
            import threading
            import queue
            self._queue = queue.Queue(maxsize=1000)
            self._queue_lock = threading.Lock()
            self._setup_worker_thread()
        except ImportError:
            # Fall back to synchronous operation if threading is not available
            pass
    
    def _setup_worker_thread(self) -> None:
        """Setup the background worker thread for async logging."""
        import threading
        
        def worker():
            while not self._shutdown:
                try:
                    record = self._queue.get(timeout=1.0)
                    if record is None:  # Sentinel for shutdown
                        break
                    self._file_handler.emit(record)
                    self._queue.task_done()
                except Exception:
                    # Queue timeout or other error, continue
                    pass
        
        self._worker_thread = threading.Thread(target=worker, daemon=True)
        self._worker_thread.start()
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record asynchronously.
        
        Args:
            record: The log record to emit
        """
        if self._worker_thread and self._worker_thread.is_alive():
            try:
                # Non-blocking add to queue
                self._queue.put_nowait(record)
            except Exception:
                # Queue is full, drop the record to avoid blocking
                pass
        else:
            # Fall back to synchronous operation
            self._file_handler.emit(record)
    
    def close(self) -> None:
        """Clean shutdown of async handler."""
        if self._worker_thread and self._worker_thread.is_alive():
            self._shutdown = True
            try:
                self._queue.put_nowait(None)  # Sentinel to stop worker
                self._worker_thread.join(timeout=2.0)
            except Exception:
                pass
        
        self._file_handler.close()
        super().close()


class ThrottledHandler(logging.Handler):
    """
    Handler that throttles log messages to prevent spam.
    
    Useful for preventing excessive logging in loops or error conditions.
    """
    
    def __init__(self, target_handler: logging.Handler, 
                 max_rate: float = 10.0, window_size: float = 60.0):
        """
        Initialize throttled handler.
        
        Args:
            target_handler: The underlying handler to throttle
            max_rate: Maximum messages per second
            window_size: Time window for rate calculation (seconds)
        """
        super().__init__()
        self._target_handler = target_handler
        self._max_rate = max_rate
        self._window_size = window_size
        self._message_times = []
        self._dropped_count = 0
    
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit record if within rate limits.
        
        Args:
            record: The log record to emit
        """
        current_time = time.time()
        
        # Clean old entries from the window
        cutoff_time = current_time - self._window_size
        self._message_times = [t for t in self._message_times if t > cutoff_time]
        
        # Check if we're within rate limits
        if len(self._message_times) < (self._max_rate * self._window_size):
            self._message_times.append(current_time)
            
            # Add dropped count info if any messages were dropped
            if self._dropped_count > 0:
                record.msg = f"{record.msg} (Note: {self._dropped_count} similar messages dropped)"
                self._dropped_count = 0
            
            self._target_handler.emit(record)
        else:
            self._dropped_count += 1
    
    def setLevel(self, level) -> None:
        """Set level on both this handler and target handler."""
        super().setLevel(level)
        self._target_handler.setLevel(level)
    
    def setFormatter(self, formatter) -> None:
        """Set formatter on target handler."""
        self._target_handler.setFormatter(formatter)
    
    def close(self) -> None:
        """Close target handler."""
        self._target_handler.close()
        super().close()


class ConditionalHandler(logging.Handler):
    """
    Handler that only emits records based on conditions.
    
    Useful for debug-only logging or conditional output.
    """
    
    def __init__(self, target_handler: logging.Handler, condition_func=None):
        """
        Initialize conditional handler.
        
        Args:
            target_handler: The underlying handler
            condition_func: Function that returns True if record should be emitted
        """
        super().__init__()
        self._target_handler = target_handler
        self._condition_func = condition_func or (lambda record: True)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit record only if condition is met."""
        if self._condition_func(record):
            self._target_handler.emit(record)
    
    def setLevel(self, level) -> None:
        """Set level on both handlers."""
        super().setLevel(level)
        self._target_handler.setLevel(level)
    
    def setFormatter(self, formatter) -> None:
        """Set formatter on target handler."""
        self._target_handler.setFormatter(formatter)
    
    def close(self) -> None:
        """Close target handler.""" 
        self._target_handler.close()
        super().close() 