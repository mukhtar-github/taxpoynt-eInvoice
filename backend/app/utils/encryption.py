"""
Encryption utilities for FIRS e-Invoice system.

This module provides functions for:
- Loading and extracting crypto keys from FIRS
- Encrypting IRN data with public keys
- Generating QR codes with encrypted data
- Secure storage of sensitive credentials
"""

import base64
import json
import os
from pathlib import Path
from typing import Dict, Tuple, Union

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from fastapi import HTTPException # type: ignore


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


def generate_secret_key() -> bytes:
    """Generate a random secret key for AES encryption."""
    return os.urandom(32)  # 256-bit key


def get_app_encryption_key() -> bytes:
    """
    Get the application's encryption key from environment or generate a new one.
    In production, this should be retrieved from a secure key management system.
    """
    key_env = os.getenv("ENCRYPTION_KEY")
    if key_env:
        return base64.b64decode(key_env)
    
    # For development only - in production, don't generate random keys
    # as they'll be lost on restart
    return generate_secret_key() 