"""
WorkmAIn
Configuration Loader v0.1.0
20251219

Load and manage JSON configuration files with environment variable overrides
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ConfigLoader:
    """Load and manage configuration from JSON files and environment"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration loader
        
        Args:
            config_dir: Path to config directory (defaults to ./config)
        """
        if config_dir is None:
            # Default to project root/config
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self._configs = {}
        self._loaded = False
    
    def load(self, config_name: str, required: bool = True) -> Optional[Dict[str, Any]]:
        """
        Load a configuration file
        
        Args:
            config_name: Name of config file (without .json)
            required: Whether to raise error if file not found
            
        Returns:
            Configuration dict or None if not found and not required
            
        Raises:
            FileNotFoundError: If required config file not found
            json.JSONDecodeError: If config file is invalid JSON
        """
        config_file = self.config_dir / f"{config_name}.json"
        
        if not config_file.exists():
            if required:
                raise FileNotFoundError(
                    f"Required configuration file not found: {config_file}"
                )
            return None
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Store in cache
            self._configs[config_name] = config
            
            return config
            
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in {config_file}: {e.msg}",
                e.doc,
                e.pos
            )
    
    def load_all(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all configuration files
        
        Returns:
            Dict mapping config names to their contents
        """
        if self._loaded:
            return self._configs
        
        # List of config files to load
        config_files = [
            ("database", False),  # May not exist, will use env vars
            ("integrations", False),  # Created during setup
            ("notifications", False),  # Created during setup
            ("ai_settings", False),  # Created during setup
            ("projects", False),  # Created during setup
            ("recipients", False),  # Created during setup
            ("clients", False),  # Created during setup
            ("user_preferences", False),  # Created during setup
        ]
        
        for config_name, required in config_files:
            try:
                self.load(config_name, required=required)
            except FileNotFoundError:
                # Create empty config for optional files
                self._configs[config_name] = {}
        
        self._loaded = True
        return self._configs
    
    def get(self, config_name: str, key: str = None, default: Any = None) -> Any:
        """
        Get configuration value with optional key path
        
        Args:
            config_name: Name of config file
            key: Optional dot-separated key path (e.g., "database.host")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        # Load config if not already loaded
        if config_name not in self._configs:
            self.load(config_name, required=False)
        
        config = self._configs.get(config_name, {})
        
        if key is None:
            return config if config else default
        
        # Handle dot-separated key paths
        keys = key.split(".")
        value = config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_with_env_override(
        self,
        config_name: str,
        key: str,
        env_var: str,
        default: Any = None
    ) -> Any:
        """
        Get config value with environment variable override
        
        Priority: ENV VAR > Config File > Default
        
        Args:
            config_name: Name of config file
            key: Config key path
            env_var: Environment variable name
            default: Default value
            
        Returns:
            Configuration value from highest priority source
        """
        # Check environment variable first
        env_value = os.getenv(env_var)
        if env_value is not None:
            return env_value
        
        # Check config file
        config_value = self.get(config_name, key)
        if config_value is not None:
            return config_value
        
        # Return default
        return default
    
    def save(self, config_name: str, config: Dict[str, Any]) -> None:
        """
        Save configuration to file
        
        Args:
            config_name: Name of config file (without .json)
            config: Configuration dict to save
        """
        config_file = self.config_dir / f"{config_name}.json"
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Save with pretty printing
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Update cache
        self._configs[config_name] = config
    
    def reload(self, config_name: str) -> Dict[str, Any]:
        """
        Reload a configuration file from disk
        
        Args:
            config_name: Name of config file to reload
            
        Returns:
            Reloaded configuration
        """
        if config_name in self._configs:
            del self._configs[config_name]
        
        return self.load(config_name)
    
    def get_database_config(self) -> Dict[str, str]:
        """
        Get database configuration with environment variable overrides
        
        Returns:
            Dict with database connection parameters
        """
        return {
            "host": self.get_with_env_override(
                "database", "host", "DB_HOST", "localhost"
            ),
            "port": self.get_with_env_override(
                "database", "port", "DB_PORT", "5432"
            ),
            "name": self.get_with_env_override(
                "database", "name", "DB_NAME", "workmain"
            ),
            "user": self.get_with_env_override(
                "database", "user", "DB_USER", "workmain_user"
            ),
            "password": self.get_with_env_override(
                "database", "password", "DB_PASSWORD", "workmain_dev_pass"
            ),
        }
    
    def get_ai_provider_for_report(self, report_type: str) -> str:
        """
        Get AI provider for a specific report type
        
        Args:
            report_type: Type of report (daily_internal, weekly_client, etc.)
            
        Returns:
            Provider name (claude, gemini)
        """
        ai_config = self.get("ai_settings", default={})
        
        # Check per-report override
        overrides = ai_config.get("per_report_override", {})
        if report_type in overrides:
            return overrides[report_type]
        
        # Return default provider
        return ai_config.get("default_provider", "claude")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider (with environment variable support)
        
        Args:
            provider: Provider name (claude, gemini)
            
        Returns:
            API key or None
        """
        ai_config = self.get("ai_settings", default={})
        providers = ai_config.get("providers", {})
        
        if provider not in providers:
            return None
        
        # Get environment variable name for API key
        env_var = providers[provider].get("api_key_env")
        
        if env_var:
            return os.getenv(env_var)
        
        return None


# Global config loader instance
_config_loader = None


def get_config() -> ConfigLoader:
    """
    Get global configuration loader instance
    
    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
