"""
Tests for encryption utilities.
"""

import base64
import json
import os
import tempfile
from unittest import mock

import pytest # type: ignore
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from fastapi import HTTPException # type: ignore

from app.utils.encryption import (
    decrypt_sensitive_value,
    encrypt_irn_data,
    encrypt_sensitive_value,
    extract_keys_from_file,
    generate_secret_key,
    get_app_encryption_key,
    load_public_key,
)


def generate_test_keys():
    """Generate test RSA key pair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    
    # Serialize public key to PEM format
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_key, public_key, pem


def test_extract_keys_from_file():
    """Test extracting keys from a file."""
    # Create a temporary file with test keys
    private_key, public_key, pem = generate_test_keys()
    
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write(pem.decode() + "\n")
        temp.write("TEST_CERTIFICATE_DATA")
        temp_path = temp.name
    
    try:
        # Extract keys from the file
        public_key_pem, certificate = extract_keys_from_file(temp_path)
        
        # Verify the extracted public key and certificate
        assert public_key_pem == pem
        assert certificate == b"TEST_CERTIFICATE_DATA"
    finally:
        # Clean up temporary file
        os.unlink(temp_path)


def test_extract_keys_from_file_invalid():
    """Test extracting keys from an invalid file."""
    # Create a temporary file without proper key format
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp:
        temp.write("INVALID_KEY_DATA")
        temp_path = temp.name
    
    try:
        # Attempt to extract keys from the invalid file
        with pytest.raises(HTTPException) as excinfo:
            extract_keys_from_file(temp_path)
        
        # Verify error details
        assert excinfo.value.status_code == 500
        assert "Failed to extract keys" in excinfo.value.detail
    finally:
        # Clean up temporary file
        os.unlink(temp_path)


def test_load_public_key():
    """Test loading a public key from PEM format."""
    # Generate test keys
    private_key, public_key, pem = generate_test_keys()
    
    # Load the public key
    loaded_key = load_public_key(pem)
    
    # Verify the loaded key by encrypting and decrypting a test message
    test_message = b"Test message"
    
    # Encrypt with loaded key
    encrypted = loaded_key.encrypt(
        test_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Decrypt with original private key
    decrypted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Verify decryption
    assert decrypted == test_message


def test_encrypt_irn_data():
    """Test encrypting IRN data."""
    # Generate test keys
    private_key, public_key, pem = generate_test_keys()
    
    # Test data
    irn = "INV001-94ND90NR-20240611"
    certificate = "TEST_CERTIFICATE"
    
    # Encrypt the IRN data
    encrypted_data = encrypt_irn_data(irn, certificate, public_key)
    
    # Verify the encrypted data is base64 encoded
    encrypted_bytes = base64.b64decode(encrypted_data)
    
    # Decrypt with private key
    decrypted = private_key.decrypt(
        encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Parse the decrypted JSON
    decrypted_data = json.loads(decrypted.decode())
    
    # Verify the decrypted data
    assert decrypted_data["irn"] == irn
    assert decrypted_data["certificate"] == certificate


def test_encrypt_decrypt_sensitive_value():
    """Test encrypting and decrypting sensitive values."""
    # Generate a secret key
    secret_key = generate_secret_key()
    
    # Test value to encrypt
    test_value = "supersecretapikey"
    
    # Encrypt the value
    encrypted = encrypt_sensitive_value(test_value, secret_key)
    
    # Decrypt the value
    decrypted = decrypt_sensitive_value(encrypted, secret_key)
    
    # Verify decryption
    assert decrypted == test_value


def test_get_app_encryption_key():
    """Test getting the application encryption key."""
    # Test with environment variable
    test_key = base64.b64encode(os.urandom(32)).decode()
    with mock.patch.dict(os.environ, {"ENCRYPTION_KEY": test_key}):
        key = get_app_encryption_key()
        assert key == base64.b64decode(test_key)
    
    # Test without environment variable
    with mock.patch.dict(os.environ, {}, clear=True):
        key = get_app_encryption_key()
        assert len(key) == 32  # 256-bit key 