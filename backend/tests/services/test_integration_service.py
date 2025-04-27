import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.integration_service import (
    encrypt_sensitive_config_fields,
    decrypt_sensitive_config_fields,
    create_integration,
    SENSITIVE_CONFIG_FIELDS
)


def test_encrypt_sensitive_config_fields():
    """Test encrypting sensitive fields in config."""
    # Sample config with sensitive fields
    config = {
        "api_url": "https://api.example.com",
        "api_key": "secret-api-key",
        "client_id": "client-123",
        "client_secret": "super-secret",
        "settings": {
            "timeout": 30,
            "password": "nested-password"
        }
    }
    
    # Mock the encryption function
    with patch("app.services.integration_service.encrypt_sensitive_value") as mock_encrypt:
        # Mock encryption by adding prefix
        mock_encrypt.side_effect = lambda value, key: f"encrypted_{value}"
        
        # Mock the encryption key
        with patch("app.services.integration_service.get_app_encryption_key") as mock_key:
            mock_key.return_value = b"test-key"
            
            # Encrypt the config
            encrypted_config = encrypt_sensitive_config_fields(config)
            
            # Verify top-level sensitive fields were encrypted
            assert encrypted_config["api_url"] == "https://api.example.com"  # Not sensitive
            assert encrypted_config["api_key"] == "encrypted_secret-api-key"
            assert encrypted_config["client_id"] == "client-123"  # Not sensitive
            assert encrypted_config["client_secret"] == "encrypted_super-secret"
            
            # Verify nested sensitive fields were encrypted
            assert encrypted_config["settings"]["timeout"] == 30  # Not sensitive
            assert encrypted_config["settings"]["password"] == "encrypted_nested-password"
            
            # Verify encrypt_sensitive_value was called for sensitive fields
            sensitive_calls = [
                call for call in mock_encrypt.call_args_list 
                if any(field in str(call) for field in SENSITIVE_CONFIG_FIELDS)
            ]
            assert len(sensitive_calls) == 3  # api_key, client_secret, nested password


def test_decrypt_sensitive_config_fields():
    """Test decrypting sensitive fields in config."""
    # Sample config with encrypted sensitive fields
    config = {
        "api_url": "https://api.example.com",
        "api_key": "encrypted_secret-api-key",
        "client_id": "client-123",
        "client_secret": "encrypted_super-secret",
        "settings": {
            "timeout": 30,
            "password": "encrypted_nested-password"
        }
    }
    
    # Mock the decryption function
    with patch("app.services.integration_service.decrypt_sensitive_value") as mock_decrypt:
        # Mock decryption by removing prefix
        mock_decrypt.side_effect = lambda value, key: value.replace("encrypted_", "")
        
        # Mock the encryption key
        with patch("app.services.integration_service.get_app_encryption_key") as mock_key:
            mock_key.return_value = b"test-key"
            
            # Decrypt the config
            decrypted_config = decrypt_sensitive_config_fields(config)
            
            # Verify top-level sensitive fields were decrypted
            assert decrypted_config["api_url"] == "https://api.example.com"  # Not sensitive
            assert decrypted_config["api_key"] == "secret-api-key"
            assert decrypted_config["client_id"] == "client-123"  # Not sensitive
            assert decrypted_config["client_secret"] == "super-secret"
            
            # Verify nested sensitive fields were decrypted
            assert decrypted_config["settings"]["timeout"] == 30  # Not sensitive
            assert decrypted_config["settings"]["password"] == "nested-password"


def test_create_integration():
    """Test creating an integration with encrypted config."""
    # Mock DB session
    db = MagicMock()
    
    # Mock integration create schema
    user_id = uuid4()
    integration_in = MagicMock()
    integration_in.config = {
        "api_url": "https://api.example.com",
        "api_key": "secret-api-key",
        "client_secret": "super-secret"
    }
    integration_in.dict.return_value = {
        "client_id": uuid4(),
        "name": "Test Integration",
        "description": "Test Description",
        "config": integration_in.config
    }
    
    # Mock crud.integration.create
    with patch("app.services.integration_service.crud.integration.create") as mock_create:
        # Mock the created integration
        mock_integration = MagicMock()
        mock_integration.__dict__ = {
            "id": uuid4(),
            "client_id": uuid4(),
            "name": "Test Integration",
            "description": "Test Description",
            "config": {
                "api_url": "https://api.example.com",
                "api_key": "encrypted_secret-api-key",
                "client_secret": "encrypted_super-secret"
            },
            "created_at": "2023-06-01T12:00:00Z",
            "updated_at": "2023-06-01T12:00:00Z",
            "status": "configured"
        }
        mock_create.return_value = mock_integration
        
        # Mock encrypt_sensitive_config_fields
        with patch("app.services.integration_service.encrypt_sensitive_config_fields") as mock_encrypt:
            mock_encrypt.return_value = {
                "api_url": "https://api.example.com",
                "api_key": "encrypted_secret-api-key",
                "client_secret": "encrypted_super-secret"
            }
            
            # Mock decrypt_integration_config
            with patch("app.services.integration_service.decrypt_integration_config") as mock_decrypt:
                expected_result = MagicMock()
                mock_decrypt.return_value = expected_result
                
                # Call the function
                result = create_integration(db, integration_in, user_id)
                
                # Verify the result
                assert result == expected_result
                
                # Verify encrypt_sensitive_config_fields was called
                mock_encrypt.assert_called_once_with(integration_in.config)
                
                # Verify crud.integration.create was called
                mock_create.assert_called_once()
                
                # Verify decrypt_integration_config was called
                mock_decrypt.assert_called_once_with(mock_integration) 