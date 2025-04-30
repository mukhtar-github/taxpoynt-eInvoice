"""
Encryption utilities for FIRS e-Invoice system.

This module provides functions for:
- Loading and extracting crypto keys from FIRS
- Encrypting IRN data with public keys
- Generating QR codes with encrypted data
- Secure storage of sensitive credentials
- Field-level encryption for database records
- Key management functions
"""

import base64
import json
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Tuple, Union, Optional, Any

from cryptography.hazmat.backends import default_backend # type: ignore
from cryptography.hazmat.primitives import hashes, serialization # type: ignore
from cryptography.hazmat.primitives.asymmetric import padding, rsa # type: ignore
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes # type: ignore
from cryptography.hazmat.primitives.ciphers.aead import AESGCM # type: ignore
from fastapi import HTTPException # type: ignore

from app.core.config import settings


def extract_keys_from_file(file_path: str) -> Tuple[bytes, bytes]:
    """
    Extract public key and certificate from the FIRS crypto_keys.txt file.
    
    Args:
        file_path: Path to the crypto_keys.txt file
        
    Returns:
        Tuple containing (public_key_bytes, certificate_bytes)
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Extract public key
        pub_key_start = content.find("-----BEGIN PUBLIC KEY-----")
        pub_key_end = content.find("-----END PUBLIC KEY-----") + len("-----END PUBLIC KEY-----")
        
        if pub_key_start == -1 or pub_key_end == -1:
            raise ValueError("Public key not found in the crypto keys file")
            
        public_key_pem = content[pub_key_start:pub_key_end]
        
        # Extract certificate (everything after the public key)
        certificate = content[pub_key_end:].strip()
        
        return public_key_pem.encode(), certificate.encode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to extract keys: {str(e)}")


def load_public_key(public_key_pem: bytes) -> rsa.RSAPublicKey:
    """
    Load RSA public key from PEM formatted bytes.
    
    Args:
        public_key_pem: PEM encoded public key
        
    Returns:
        RSA public key object
    """
    try:
        public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )
        return public_key
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load public key: {str(e)}")


def encrypt_irn_data(irn: str, certificate: str, public_key: rsa.RSAPublicKey) -> str:
    """
    Encrypt IRN and certificate using the FIRS public key.
    
    Args:
        irn: Invoice Reference Number
        certificate: FIRS certificate
        public_key: RSA public key for encryption
        
    Returns:
        Base64 encoded encrypted data
    """
    try:
        # Prepare data to encrypt
        data = {
            "irn": irn,
            "certificate": certificate
        }
        data_bytes = json.dumps(data).encode()
        
        # Encrypt data with the public key
        encrypted_data = public_key.encrypt(
            data_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # Return Base64 encoded encrypted data
        return base64.b64encode(encrypted_data).decode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


def encrypt_sensitive_value(value: str, secret_key: bytes) -> str:
    """
    Encrypt sensitive values like API keys or secrets before storing in database.
    
    Args:
        value: Value to encrypt
        secret_key: Secret key for encryption
        
    Returns:
        Encrypted value in base64 format
    """
    if not value:
        return None
        
    try:
        # Generate a random IV
        iv = os.urandom(16)
        
        # Create an encryptor
        cipher = Cipher(
            algorithms.AES(secret_key),
            modes.CFB(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Encrypt the value
        encrypted_value = encryptor.update(value.encode()) + encryptor.finalize()
        
        # Return IV + encrypted value in base64
        return base64.b64encode(iv + encrypted_value).decode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Value encryption failed: {str(e)}")


def decrypt_sensitive_value(encrypted_value: str, secret_key: bytes) -> str:
    """
    Decrypt sensitive values retrieved from database.
    
    Args:
        encrypted_value: Encrypted value in base64 format
        secret_key: Secret key for decryption
        
    Returns:
        Decrypted value
    """
    if not encrypted_value:
        return None
        
    try:
        # Decode from base64
        data = base64.b64decode(encrypted_value)
        
        # Extract IV (first 16 bytes)
        iv = data[:16]
        ciphertext = data[16:]
        
        # Create a decryptor
        cipher = Cipher(
            algorithms.AES(secret_key),
            modes.CFB(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        # Decrypt and return the value
        decrypted_value = decryptor.update(ciphertext) + decryptor.finalize()
        return decrypted_value.decode()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Value decryption failed: {str(e)}")


# ======== AES-GCM Encryption (Enhanced Security) ========

def encrypt_with_gcm(data: Union[str, dict], key: bytes) -> str:
    """
    Encrypt data using AES-GCM mode (provides authentication and higher security).
    
    Args:
        data: String or dictionary to encrypt
        key: 32-byte key for AES-256
        
    Returns:
        Encrypted data in format: base64(nonce + ciphertext + tag)
    """
    if data is None:
        return None
        
    try:
        # Convert dict to JSON string if needed
        if isinstance(data, dict):
            data = json.dumps(data)
            
        plaintext = data.encode()
        
        # Generate a random 96-bit nonce
        nonce = os.urandom(12)
        
        # Create AESGCM instance
        aesgcm = AESGCM(key)
        
        # Encrypt and authenticate (tag is appended to ciphertext)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)
        
        # Format: nonce + ciphertext
        encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')
        return encrypted_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCM encryption failed: {str(e)}")


def decrypt_with_gcm(encrypted_data: str, key: bytes, as_dict: bool = False) -> Union[str, dict]:
    """
    Decrypt data that was encrypted using AES-GCM.
    
    Args:
        encrypted_data: Encrypted data in base64 format
        key: 32-byte key for AES-256
        as_dict: Whether to parse the decrypted data as JSON dict
        
    Returns:
        Decrypted data as string or dict
    """
    if encrypted_data is None:
        return None
        
    try:
        # Decode the base64 data
        decoded = base64.b64decode(encrypted_data)
        
        # Split into nonce and ciphertext+tag
        nonce = decoded[:12]
        ciphertext = decoded[12:]
        
        # Create AESGCM instance
        aesgcm = AESGCM(key)
        
        # Decrypt and verify (tag is part of ciphertext)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        decrypted = plaintext.decode('utf-8')
        
        # Return as dict if requested
        if as_dict:
            return json.loads(decrypted)
            
        return decrypted
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCM decryption failed: {str(e)}")


# ======== Key Management ========

def generate_secret_key() -> bytes:
    """Generate a random secret key for AES encryption."""
    return os.urandom(32)  # 256-bit key


def get_app_encryption_key() -> bytes:
    """
    Get the application's encryption key from environment or generate a new one.
    In production, this should be retrieved from a secure key management system.
    """
    key_env = os.getenv("ENCRYPTION_KEY", settings.ENCRYPTION_KEY)
    
    # First try base64 decoding in case it's stored that way
    try:
        return base64.b64decode(key_env)
    except:
        # If it's not base64 encoded, use it as bytes directly
        # but ensure it's 32 bytes (pad or truncate)
        key_bytes = key_env.encode()
        if len(key_bytes) < 32:
            # Pad to 32 bytes using PKCS#7 padding
            padding_size = 32 - (len(key_bytes) % 32)
            key_bytes += bytes([padding_size]) * padding_size
        return key_bytes[:32]


def generate_key_id() -> str:
    """Generate a unique ID for a key version."""
    return f"key_{datetime.now().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"


def create_key_entry(key_id: str, key: bytes) -> dict:
    """
    Create a key entry for storage.
    
    Args:
        key_id: Unique identifier for the key
        key: The encryption key
        
    Returns:
        Dict containing key metadata
    """
    created_at = datetime.now()
    return {
        "id": key_id,
        "key": base64.b64encode(key).decode(),
        "created_at": created_at.isoformat(),
        "rotation_date": (created_at + timedelta(days=90)).isoformat(),
        "active": True
    }


def rotate_encryption_key() -> Tuple[str, bytes]:
    """
    Generate a new encryption key for rotation.
    
    Returns:
        Tuple of (key_id, new_key)
    """
    key_id = generate_key_id()
    new_key = generate_secret_key()
    return key_id, new_key


# ======== Field-level Encryption Utilities ========

def encrypt_field(value: Any, key: Optional[bytes] = None) -> str:
    """
    Encrypt a field value using AES-GCM.
    
    Args:
        value: Value to encrypt
        key: Optional key to use (defaults to app encryption key)
        
    Returns:
        Encrypted value as base64 string
    """
    if value is None:
        return None
        
    if key is None:
        key = get_app_encryption_key()
        
    # Convert non-string types to string
    if not isinstance(value, (str, dict)):
        value = str(value)
        
    return encrypt_with_gcm(value, key)


def decrypt_field(value: str, key: Optional[bytes] = None, as_dict: bool = False) -> Any:
    """
    Decrypt a field value using AES-GCM.
    
    Args:
        value: Encrypted value in base64 format
        key: Optional key to use (defaults to app encryption key)
        as_dict: Whether to parse the decrypted data as JSON
        
    Returns:
        Decrypted value
    """
    if value is None:
        return None
        
    if key is None:
        key = get_app_encryption_key()
        
    return decrypt_with_gcm(value, key, as_dict)


def encrypt_dict_fields(data: dict, fields: list, key: Optional[bytes] = None) -> dict:
    """
    Encrypt specific fields in a dictionary.
    
    Args:
        data: Dictionary containing data
        fields: List of field names to encrypt
        key: Optional encryption key
        
    Returns:
        Dictionary with specified fields encrypted
    """
    if key is None:
        key = get_app_encryption_key()
        
    result = data.copy()
    for field in fields:
        if field in result and result[field] is not None:
            result[field] = encrypt_field(result[field], key)
            
    return result


def decrypt_dict_fields(data: dict, fields: list, key: Optional[bytes] = None) -> dict:
    """
    Decrypt specific fields in a dictionary.
    
    Args:
        data: Dictionary containing encrypted data
        fields: List of field names to decrypt
        key: Optional decryption key
        
    Returns:
        Dictionary with specified fields decrypted
    """
    if key is None:
        key = get_app_encryption_key()
        
    result = data.copy()
    for field in fields:
        if field in result and result[field] is not None:
            is_dict = field.endswith('_json')
            result[field] = decrypt_field(result[field], key, as_dict=is_dict)
            
    return result 