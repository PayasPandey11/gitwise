"""
Utility functions for GitWise logging.

Provides helpers for log sharing, cleanup, and analysis.
"""

import os
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple

from .config import get_log_directory


def get_log_files() -> List[Path]:
    """
    Get list of all GitWise log files.
    
    Returns:
        List of log file paths
    """
    log_dir = get_log_directory()
    log_files = []
    
    # Get main log file and rotated backups
    for log_file in log_dir.glob("gitwise.log*"):
        if log_file.is_file():
            log_files.append(log_file)
    
    # Sort by modification time (newest first)
    log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return log_files


def get_recent_logs(hours: int = 24) -> str:
    """
    Get recent log entries from the last N hours.
    
    Args:
        hours: Number of hours to look back
        
    Returns:
        Combined log content from recent entries
    """
    cutoff_time = datetime.now() - timedelta(hours=hours)
    log_files = get_log_files()
    
    recent_logs = []
    
    for log_file in log_files:
        # Check if file was modified recently
        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_mtime < cutoff_time:
            continue
            
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Filter lines by timestamp if they have timestamps
            for line in lines:
                # Simple timestamp check - lines starting with YYYY-MM-DD
                if line[:10].replace('-', '').isdigit():
                    try:
                        line_time = datetime.fromisoformat(line[:19])
                        if line_time >= cutoff_time:
                            recent_logs.append(line.rstrip())
                    except ValueError:
                        # If we can't parse timestamp, include the line anyway
                        recent_logs.append(line.rstrip())
                else:
                    # No timestamp or unrecognized format, include it
                    recent_logs.append(line.rstrip())
                    
        except Exception:
            # Skip files we can't read
            continue
    
    return '\n'.join(recent_logs)


def create_shareable_log_package(hours: int = 24, include_config: bool = False) -> str:
    """
    Create a sanitized log package for sharing.
    
    Args:
        hours: Hours of recent logs to include
        include_config: Whether to include sanitized config info
        
    Returns:
        Path to the created log package (zip file)
    """
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = Path(temp_dir) / "gitwise_logs"
        package_dir.mkdir()
        
        # Get recent logs and save to file
        recent_logs = get_recent_logs(hours)
        if recent_logs:
            log_file = package_dir / "recent_logs.txt"
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"GitWise Logs (Last {hours} hours)\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(recent_logs)
        
        # Add system info
        info_file = package_dir / "system_info.txt"
        with open(info_file, 'w', encoding='utf-8') as f:
            f.write("GitWise System Information\n")
            f.write("=" * 30 + "\n")
            f.write(f"OS: {os.name}\n")
            f.write(f"Platform: {os.uname().sysname if hasattr(os, 'uname') else 'Unknown'}\n")
            f.write(f"Python: {os.sys.version.split()[0]}\n")
            
            # Add GitWise version
            try:
                from gitwise import __version__
                f.write(f"GitWise Version: {__version__}\n")
            except ImportError:
                f.write("GitWise Version: Unknown\n")
        
        # Add sanitized config if requested
        if include_config:
            try:
                from gitwise.config import load_config
                config = load_config()
                
                # Sanitize config - remove sensitive data
                safe_config = {}
                for key, value in config.items():
                    if 'key' in key.lower() or 'token' in key.lower() or 'secret' in key.lower():
                        safe_config[key] = '[REDACTED]'
                    else:
                        safe_config[key] = value
                
                config_file = package_dir / "config_info.txt"
                with open(config_file, 'w', encoding='utf-8') as f:
                    f.write("GitWise Configuration (Sanitized)\n")
                    f.write("=" * 35 + "\n")
                    for key, value in safe_config.items():
                        f.write(f"{key}: {value}\n")
                        
            except Exception:
                # If config can't be loaded, skip it
                pass
        
        # Create zip package
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"gitwise_diagnostic_{timestamp}"
        
        # Use shutil to create zip
        zip_path = str(Path(temp_dir) / package_name)
        shutil.make_archive(zip_path, 'zip', package_dir)
        
        # Move to safe location - gitwise logs directory (not user's working dir)
        log_dir = get_log_directory()
        final_path = log_dir / f"{package_name}.zip"
        shutil.move(f"{zip_path}.zip", final_path)
        
        return str(final_path)


def cleanup_old_logs(days: int = 30) -> int:
    """
    Clean up log files older than specified days.
    
    Args:
        days: Number of days to keep logs
        
    Returns:
        Number of files cleaned up
    """
    cutoff_time = datetime.now() - timedelta(days=days)
    log_files = get_log_files()
    
    cleaned_count = 0
    for log_file in log_files:
        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if file_mtime < cutoff_time:
            try:
                log_file.unlink()
                cleaned_count += 1
            except Exception:
                # Skip files we can't delete
                pass
    
    return cleaned_count


def get_log_summary() -> dict:
    """
    Get a summary of current logging status.
    
    Returns:
        Dictionary with log statistics
    """
    log_files = get_log_files()
    
    if not log_files:
        return {
            'total_files': 0,
            'total_size_mb': 0,
            'oldest_log': None,
            'newest_log': None,
            'log_directory': str(get_log_directory())
        }
    
    total_size = sum(f.stat().st_size for f in log_files)
    oldest_file = min(log_files, key=lambda f: f.stat().st_mtime)
    newest_file = max(log_files, key=lambda f: f.stat().st_mtime)
    
    return {
        'total_files': len(log_files),
        'total_size_mb': round(total_size / (1024 * 1024), 2),
        'oldest_log': datetime.fromtimestamp(oldest_file.stat().st_mtime).isoformat(),
        'newest_log': datetime.fromtimestamp(newest_file.stat().st_mtime).isoformat(),
        'log_directory': str(get_log_directory())
    } 