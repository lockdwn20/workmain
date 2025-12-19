"""
WorkmAIn
Encryption Utilities v0.1.0
20251219

Encrypt/decrypt sensitive data like API keys
Uses Fernet symmetric encryption (AES 128)
"""

import os
import base64
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional


class EncryptionManager:
    """Manage encryption/decryption of sensitive data"""
    
    def __init__(self, key_file: Optional[Path] = None):
        """
        Initialize encryption manager
        
        Args:
            key_file: Path to key file (default: ~/.workmain/encryption.key)
        """
        if key_file is None:
            key_file = Path.home() / ".workmain" / "encryption.key"
        
        self.key_file = Path(key_file)
        self._fernet = None
    
    def _ensure_key_exists(self) -> bytes:
        """
        Ensure encryption key exists, create if not
        
        Returns:
            Encryption key bytes
        """
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save key securely
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (owner read/write only)
        os.chmod(self.key_file, 0o600)
        
        return key
    
    def _get_fernet(self) -> Fernet:
        """
        Get Fernet instance (lazy initialization)
        
        Returns:
            Fernet instance
        """
        if self._fernet is None:
            key = self._ensure_key_exists()
            self._fernet = Fernet(key)
        return self._fernet
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext string
        
        Args:
            plaintext: String to encrypt
            
        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        
        fernet = self._get_fernet()
        encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt encrypted string
        
        Args:
            encrypted: Base64-encoded encrypted string
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            return ""
        
        try:
            fernet = self._get_fernet()
            encrypted_bytes = base64.b64decode(encrypted.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Failed to decrypt data: {e}")
    
    def encrypt_dict(self, data: dict, keys_to_encrypt: list) -> dict:
        """
        Encrypt specific keys in a dictionary
        
        Args:
            data: Dictionary with data
            keys_to_encrypt: List of keys to encrypt
            
        Returns:
            New dict with specified keys encrypted
        """
        encrypted_data = data.copy()
        
        for key in keys_to_encrypt:
            if key in encrypted_data and encrypted_data[key]:
                encrypted_data[key] = self.encrypt(str(encrypted_data[key]))
        
        return encrypted_data
    
    def decrypt_dict(self, data: dict, keys_to_decrypt: list) -> dict:
        """
        Decrypt specific keys in a dictionary
        
        Args:
            data: Dictionary with encrypted data
            keys_to_decrypt: List of keys to decrypt
            
        Returns:
            New dict with specified keys decrypted
        """
        decrypted_data = data.copy()
        
        for key in keys_to_decrypt:
            if key in decrypted_data and decrypted_data[key]:
                decrypted_data[key] = self.decrypt(decrypted_data[key])
        
        return decrypted_data
    
    def rotate_key(self) -> None:
        """
        Rotate encryption key
        
        WARNING: This will invalidate all previously encrypted data!
        Only use if you've backed up and re-encrypted all data.
        """
        if self.key_file.exists():
            # Backup old key
            backup_file = self.key_file.with_suffix('.key.backup')
            self.key_file.rename(backup_file)
        
        # Generate new key
        self._fernet = None
        self._ensure_key_exists()


# Global encryption manager instance
_encryption_manager = None


def get_encryption() -> EncryptionManager:
    """
    Get global encryption manager instance
    
    Returns:
        EncryptionManager instance
    """
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager()
    return _encryption_manager


def encrypt_api_key(api_key: str) -> str:
    """
    Convenience function to encrypt an API key
    
    Args:
        api_key: API key to encrypt
        
    Returns:
        Encrypted API key
    """
    return get_encryption().encrypt(api_key)


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Convenience function to decrypt an API key
    
    Args:
        encrypted_key: Encrypted API key
        
    Returns:
        Decrypted API key
    """
    return get_encryption().decrypt(encrypted_key)
