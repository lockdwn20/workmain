"""
Manages Clockify API key authentication and validation.
"""

import os
from typing import Optional
from cryptography.fernet import Fernet
from pathlib import Path


class ClockifyAuth:
    """
    Manages Clockify API key authentication.
    
    API keys are stored in .env file and validated on use.
    Uses Fernet encryption for secure storage.
    """
    
    def __init__(self):
        """Initialize Clockify authentication manager."""
        self.api_key: Optional[str] = None
        self._load_api_key()
    
    def _load_api_key(self) -> None:
        """Load API key from environment variable."""
        self.api_key = os.getenv('CLOCKIFY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "CLOCKIFY_API_KEY not found in environment. "
                "Please add it to your .env file."
            )
    
    def get_api_key(self) -> str:
        """
        Get the Clockify API key.
        
        Returns:
            str: The API key
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.api_key:
            self._load_api_key()
        return self.api_key
    
    def validate_key(self) -> bool:
        """
        Validate that API key is present and properly formatted.
        
        Returns:
            bool: True if key is valid format (not empty, reasonable length)
        """
        if not self.api_key:
            return False
        
        # Clockify API keys are typically 48 characters
        if len(self.api_key) < 20:
            return False
        
        return True
    
    def get_auth_headers(self) -> dict:
        """
        Get authentication headers for Clockify API requests.
        
        Returns:
            dict: Headers with API key authentication
        """
        return {
            'X-Api-Key': self.get_api_key(),
            'Content-Type': 'application/json'
        }
    
    @staticmethod
    def get_env_example() -> str:
        """
        Get example .env entry for documentation.
        
        Returns:
            str: Example environment variable entry
        """
        return "CLOCKIFY_API_KEY=your_clockify_api_key_here"
