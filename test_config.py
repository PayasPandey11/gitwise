"""Configuration management for application settings."""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class DatabaseConfig:
    """Database connection configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "myapp"
    username: str = "admin"
    password: str = ""
    ssl_mode: str = "prefer"
    connection_timeout: int = 30
    max_connections: int = 100

@dataclass
class CacheConfig:
    """Cache configuration settings."""
    provider: str = "redis"  # redis, memcached, memory
    host: str = "localhost"
    port: int = 6379
    ttl_seconds: int = 3600
    max_memory_mb: int = 256
    compression_enabled: bool = True

@dataclass
class ApiConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_enabled: bool = True
    cors_origins: list = None
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

class ConfigManager:
    """Manages application configuration from files and environment variables."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file and environment variables."""
        # Load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config file: {e}")
                self.config = {}
        
        # Override with environment variables
        self._load_env_overrides()
    
    def _load_env_overrides(self):
        """Load configuration overrides from environment variables."""
        env_mappings = {
            'DB_HOST': 'database.host',
            'DB_PORT': 'database.port',
            'DB_NAME': 'database.database',
            'DB_USER': 'database.username',
            'DB_PASSWORD': 'database.password',
            'CACHE_HOST': 'cache.host',
            'CACHE_PORT': 'cache.port',
            'API_HOST': 'api.host',
            'API_PORT': 'api.port',
            'API_DEBUG': 'api.debug',
        }
        
        for env_var, config_path in env_mappings.items():
            if env_var in os.environ:
                self._set_nested_config(config_path, os.environ[env_var])
    
    def _set_nested_config(self, path: str, value: str):
        """Set a nested configuration value using dot notation."""
        keys = path.split('.')
        current = self.config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Convert string values to appropriate types
        final_key = keys[-1]
        if value.lower() in ('true', 'false'):
            current[final_key] = value.lower() == 'true'
        elif value.isdigit():
            current[final_key] = int(value)
        else:
            current[final_key] = value
    
    def get_database_config(self) -> DatabaseConfig:
        """Get database configuration as a structured object."""
        db_config = self.config.get('database', {})
        return DatabaseConfig(**db_config)
    
    def get_cache_config(self) -> CacheConfig:
        """Get cache configuration as a structured object."""
        cache_config = self.config.get('cache', {})
        return CacheConfig(**cache_config)
    
    def get_api_config(self) -> ApiConfig:
        """Get API configuration as a structured object."""
        api_config = self.config.get('api', {})
        if 'cors_origins' not in api_config:
            api_config['cors_origins'] = ["http://localhost:3000"]
        return ApiConfig(**api_config)
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except IOError as e:
            print(f"Error saving config file: {e}")
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict:
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, updates)
    
    def get_config_value(self, path: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = path.split('.')
        current = self.config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance."""
    return config_manager

def reload_config():
    """Reload configuration from file and environment."""
    global config_manager
    config_manager.load_config() 