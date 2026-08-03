"""
Manages template aliases for simplified CLI usage.

Features:
- Load aliases from config/template_aliases.json
- Register new aliases
- Unregister aliases
- Resolve alias to template name
- List all aliases

Example:
    alias_manager = get_alias_manager()
    template_name = alias_manager.resolve("daily")  # Returns "daily_internal"
    alias_manager.register("monthly", "monthly_executive")
"""

import json
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class AliasInfo:
    """Information about a template alias."""
    alias: str
    template_name: str


class AliasManager:
    """
    Manage template aliases.
    
    Provides methods to load, register, resolve, and list template aliases.
    Aliases are stored in config/template_aliases.json.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize alias manager.
        
        Args:
            config_path: Path to template_aliases.json (optional)
        """
        if config_path is None:
            # Default to config/template_aliases.json
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "template_aliases.json"
        
        self.config_path = Path(config_path)
        self._aliases: Dict[str, str] = {}
        self._load_aliases()
    
    def resolve(self, alias_or_name: str) -> str:
        """
        Resolve alias to template name.
        
        If input is already a template name (not an alias), returns as-is.
        
        Args:
            alias_or_name: Alias or template name
            
        Returns:
            Template name
        """
        return self._aliases.get(alias_or_name, alias_or_name)
    
    def is_alias(self, name: str) -> bool:
        """
        Check if name is a registered alias.
        
        Args:
            name: Name to check
            
        Returns:
            True if name is an alias
        """
        return name in self._aliases
    
    def register(self, alias: str, template_name: str) -> bool:
        """
        Register a new alias.
        
        Args:
            alias: Alias name
            template_name: Template name to map to
            
        Returns:
            True if successful, False if alias already exists
            
        Raises:
            ValueError: If alias or template_name is invalid
        """
        if not alias or not template_name:
            raise ValueError("Alias and template name must not be empty")
        
        if alias in self._aliases:
            return False  # Alias already exists
        
        # Add to in-memory dict
        self._aliases[alias] = template_name
        
        # Persist to file
        self._save_aliases()
        
        return True
    
    def unregister(self, alias: str) -> bool:
        """
        Unregister an alias.
        
        Args:
            alias: Alias to remove
            
        Returns:
            True if successful, False if alias not found
        """
        if alias not in self._aliases:
            return False
        
        # Remove from in-memory dict
        del self._aliases[alias]
        
        # Persist to file
        self._save_aliases()
        
        return True
    
    def list_aliases(self) -> List[AliasInfo]:
        """
        Get list of all registered aliases.
        
        Returns:
            List of AliasInfo objects
        """
        return [
            AliasInfo(alias=alias, template_name=template)
            for alias, template in sorted(self._aliases.items())
        ]
    
    def get_template_for_alias(self, alias: str) -> Optional[str]:
        """
        Get template name for an alias.
        
        Args:
            alias: Alias to look up
            
        Returns:
            Template name or None if alias not found
        """
        return self._aliases.get(alias)
    
    def _load_aliases(self):
        """Load aliases from config file."""
        if not self.config_path.exists():
            # Create default config
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                self._aliases = data.get('aliases', {})
        except Exception as e:
            print(f"Warning: Failed to load template aliases: {e}")
            self._aliases = {}
    
    def _save_aliases(self):
        """Save aliases to config file."""
        try:
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing data to preserve metadata
            existing_data = {}
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    existing_data = json.load(f)
            
            # Update aliases
            existing_data['aliases'] = self._aliases
            
            # Write back
            with open(self.config_path, 'w') as f:
                json.dump(existing_data, f, indent=2)
        
        except Exception as e:
            print(f"Warning: Failed to save template aliases: {e}")
    
    def _create_default_config(self):
        """Create default alias configuration."""
        default_config = {
            "version": "1.0",
            "aliases": {
                "daily": "daily_internal",
                "weekly": "weekly_client"
            },
            "metadata": {
                "created_at": "2025-12-30",
                "description": "Template alias registry for WorkmAIn report templates"
            }
        }
        
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self._aliases = default_config['aliases']
        except Exception as e:
            print(f"Warning: Failed to create default alias config: {e}")


# Singleton instance
_alias_manager_instance: Optional[AliasManager] = None


def get_alias_manager(config_path: Optional[Path] = None) -> AliasManager:
    """
    Get singleton instance of AliasManager.
    
    Args:
        config_path: Optional path to template_aliases.json
        
    Returns:
        AliasManager singleton instance
    """
    global _alias_manager_instance
    if _alias_manager_instance is None:
        _alias_manager_instance = AliasManager(config_path)
    return _alias_manager_instance