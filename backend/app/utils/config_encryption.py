"""
Configuration Encryption utilities for TaxPoynt eInvoice system.

This module provides specialized functions for:
- Encrypting configuration data with versioned keys
- Secure management of application settings
- Configuration file encryption and decryption
- Environment variable protection
"""

import json
import os
import base64
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

from app.core.config import settings
from app.utils.encryption import encrypt_field, decrypt_field, encrypt_with_gcm, decrypt_with_gcm

logger = logging.getLogger(__name__)


class ConfigEncryptor:
    """
    Utility class for encrypting and decrypting application configuration.
    
    This class provides methods to:
    - Encrypt sensitive configuration data
    - Decrypt configuration data for application use
    - Securely store credentials and API keys
    - Create encrypted configuration files
    """
    
    def __init__(self, master_key: Optional[bytes] = None, salt: Optional[bytes] = None):
        """
        Initialize with optional master key and salt.
        
        Args:
            master_key: Optional master key (will use app key if not provided)
            salt: Optional salt for key derivation
        """
        self.master_key = master_key or self._get_master_key()
        self.salt = salt or self._get_or_create_salt()
        self.derived_key = self._derive_key()
        
    def _get_master_key(self) -> bytes:
        """Get master key from environment or create one."""
        key_str = os.environ.get("CONFIG_ENCRYPTION_KEY", settings.SECRET_KEY)
        return hashlib.sha256(key_str.encode()).digest()
        
    def _get_or_create_salt(self) -> bytes:
        """Get or create salt for key derivation."""
        salt_path = Path(settings.APP_DATA_PATH) / ".encryption_salt"
        if salt_path.exists():
            with open(salt_path, "rb") as f:
                return f.read()
        else:
            # Create directory if it doesn't exist
            os.makedirs(settings.APP_DATA_PATH, exist_ok=True)
            
            # Generate new salt
            salt = os.urandom(16)
            with open(salt_path, "wb") as f:
                f.write(salt)
            return salt
            
    def _derive_key(self) -> bytes:
        """Derive encryption key from master key and salt."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(self.master_key)
    
    def encrypt_config(self, config_data: Dict[str, Any]) -> str:
        """
        Encrypt configuration data.
        
        Args:
            config_data: Configuration data to encrypt
            
        Returns:
            Encrypted configuration as base64 string
        """
        return encrypt_with_gcm(config_data, self.derived_key)
        
    def decrypt_config(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt configuration data.
        
        Args:
            encrypted_data: Encrypted configuration data
            
        Returns:
            Decrypted configuration as dictionary
        """
        return decrypt_with_gcm(encrypted_data, self.derived_key, as_dict=True)
    
    def encrypt_config_file(
        self, 
        input_file: Union[str, Path], 
        output_file: Optional[Union[str, Path]] = None,
        backup: bool = True
    ) -> str:
        """
        Encrypt a configuration file.
        
        Args:
            input_file: Path to input configuration file
            output_file: Path to output encrypted file (defaults to input + .enc)
            backup: Whether to create a backup before encrypting
            
        Returns:
            Path to encrypted file
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {input_file}")
            
        # Read configuration
        with open(input_path, "r") as f:
            config_data = json.load(f)
            
        # Create output path if not provided
        if output_file is None:
            output_path = input_path.with_suffix(input_path.suffix + ".enc")
        else:
            output_path = Path(output_file)
            
        # Create backup if requested
        if backup and input_path.exists():
            backup_path = input_path.with_suffix(input_path.suffix + ".bak")
            with open(input_path, "r") as src, open(backup_path, "w") as dst:
                dst.write(src.read())
                
        # Encrypt and save
        encrypted_data = self.encrypt_config(config_data)
        with open(output_path, "w") as f:
            f.write(encrypted_data)
            
        return str(output_path)
    
    def decrypt_config_file(
        self, 
        input_file: Union[str, Path], 
        output_file: Optional[Union[str, Path]] = None
    ) -> Dict[str, Any]:
        """
        Decrypt a configuration file.
        
        Args:
            input_file: Path to encrypted configuration file
            output_file: Optional path to save decrypted config
            
        Returns:
            Decrypted configuration data
        """
        input_path = Path(input_file)
        if not input_path.exists():
            raise FileNotFoundError(f"Encrypted configuration file not found: {input_file}")
            
        # Read encrypted data
        with open(input_path, "r") as f:
            encrypted_data = f.read()
            
        # Decrypt configuration
        config_data = self.decrypt_config(encrypted_data)
        
        # Save to output file if provided
        if output_file:
            output_path = Path(output_file)
            with open(output_path, "w") as f:
                json.dump(config_data, f, indent=2)
                
        return config_data
        
    def encrypt_env_vars(self, env_vars: Dict[str, str]) -> Dict[str, str]:
        """
        Encrypt environment variables.
        
        Args:
            env_vars: Dictionary of environment variables
            
        Returns:
            Dictionary with encrypted values
        """
        encrypted_vars = {}
        for key, value in env_vars.items():
            encrypted_vars[key] = encrypt_field(value, self.derived_key)
        return encrypted_vars
        
    def decrypt_env_vars(self, encrypted_vars: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt environment variables.
        
        Args:
            encrypted_vars: Dictionary with encrypted values
            
        Returns:
            Dictionary with decrypted values
        """
        decrypted_vars = {}
        for key, value in encrypted_vars.items():
            decrypted_vars[key] = decrypt_field(value, self.derived_key)
        return decrypted_vars


# Helper functions for easy access
def encrypt_app_config(config: Dict[str, Any]) -> str:
    """Encrypt application configuration."""
    encryptor = ConfigEncryptor()
    return encryptor.encrypt_config(config)


def decrypt_app_config(encrypted_config: str) -> Dict[str, Any]:
    """Decrypt application configuration."""
    encryptor = ConfigEncryptor()
    return encryptor.decrypt_config(encrypted_config)


def encrypt_config_file(file_path: Union[str, Path]) -> str:
    """Encrypt a configuration file in place."""
    encryptor = ConfigEncryptor()
    return encryptor.encrypt_config_file(file_path)


def decrypt_config_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Decrypt a configuration file."""
    encryptor = ConfigEncryptor()
    return encryptor.decrypt_config_file(file_path)
