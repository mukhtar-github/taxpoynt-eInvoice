"""
Test cases for the integration authentication framework.
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from cryptography.fernet import Fernet

from app.integrations.base.auth import (
    SecureCredentialManager,
    OAuthHandler,
    IntegrationAuth,
    ApiKeyAuth,
    BasicAuth,
    OAuth2Auth,
    TokenAuth,
    create_auth_handler
)


class TestSecureCredentialManager:
    """Test cases for SecureCredentialManager."""

    def test_encrypt_decrypt_credentials(self):
        """Test credential encryption and decryption."""
        manager = SecureCredentialManager()
        
        test_credentials = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "refresh_token": "test_refresh_token"
        }
        
        # Encrypt credentials
        encrypted = manager.encrypt_credentials(test_credentials)
        assert encrypted != ""
        assert encrypted != json.dumps(test_credentials)
        
        # Decrypt credentials
        decrypted = manager.decrypt_credentials(encrypted)
        assert decrypted == test_credentials
    
    def test_encrypt_empty_credentials(self):
        """Test encrypting empty credentials."""
        manager = SecureCredentialManager()
        
        encrypted = manager.encrypt_credentials({})
        assert encrypted == ""
        
        encrypted = manager.encrypt_credentials(None)
        assert encrypted == ""
    
    def test_decrypt_empty_credentials(self):
        """Test decrypting empty credentials."""
        manager = SecureCredentialManager()
        
        decrypted = manager.decrypt_credentials("")
        assert decrypted == {}
        
        decrypted = manager.decrypt_credentials(None)
        assert decrypted == {}
    
    def test_decrypt_invalid_data(self):
        """Test decrypting invalid data."""
        manager = SecureCredentialManager()
        
        # Test with random string
        decrypted = manager.decrypt_credentials("invalid_encrypted_data")
        assert decrypted == {}


class TestOAuthHandler:
    """Test cases for OAuthHandler."""

    def test_init(self):
        """Test OAuthHandler initialization."""
        credential_manager = SecureCredentialManager()
        handler = OAuthHandler("hubspot", credential_manager)
        
        assert handler.platform_name == "hubspot"
        assert handler.credential_manager == credential_manager
        assert handler.token_data == {}
        assert handler.token_expiry is None
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_not_implemented(self):
        """Test that get_authorization_url raises NotImplementedError."""
        credential_manager = SecureCredentialManager()
        handler = OAuthHandler("hubspot", credential_manager)
        
        with pytest.raises(NotImplementedError):
            await handler.get_authorization_url("http://localhost:8000/callback")
    
    @pytest.mark.asyncio
    async def test_exchange_code_for_token_not_implemented(self):
        """Test that exchange_code_for_token raises NotImplementedError."""
        credential_manager = SecureCredentialManager()
        handler = OAuthHandler("hubspot", credential_manager)
        
        with pytest.raises(NotImplementedError):
            await handler.exchange_code_for_token("auth_code", "http://localhost:8000/callback")
    
    @pytest.mark.asyncio
    async def test_refresh_token_not_implemented(self):
        """Test that refresh_token raises NotImplementedError."""
        credential_manager = SecureCredentialManager()
        handler = OAuthHandler("hubspot", credential_manager)
        
        with pytest.raises(NotImplementedError):
            await handler.refresh_token("refresh_token")


class TestApiKeyAuth:
    """Test cases for ApiKeyAuth."""

    @pytest.mark.asyncio
    async def test_prepare_headers_default(self):
        """Test preparing headers with default key name."""
        config = {
            "auth_type": "api_key",
            "credentials": {
                "api_key": "test_key_123"
            }
        }
        
        auth = ApiKeyAuth(config)
        headers = await auth.prepare_headers()
        
        assert headers == {"X-API-Key": "test_key_123"}
    
    @pytest.mark.asyncio
    async def test_prepare_headers_custom_key_name(self):
        """Test preparing headers with custom key name."""
        config = {
            "auth_type": "api_key",
            "key_name": "Authorization",
            "credentials": {
                "api_key": "Bearer test_token"
            }
        }
        
        auth = ApiKeyAuth(config)
        headers = await auth.prepare_headers()
        
        assert headers == {"Authorization": "Bearer test_token"}


class TestBasicAuth:
    """Test cases for BasicAuth."""

    @pytest.mark.asyncio
    async def test_prepare_headers(self):
        """Test preparing basic auth headers."""
        config = {
            "auth_type": "basic",
            "credentials": {
                "username": "testuser",
                "password": "testpass"
            }
        }
        
        auth = BasicAuth(config)
        headers = await auth.prepare_headers()
        
        # testuser:testpass in base64 is dGVzdHVzZXI6dGVzdHBhc3M=
        assert headers == {"Authorization": "Basic dGVzdHVzZXI6dGVzdHBhc3M="}


class TestOAuth2Auth:
    """Test cases for OAuth2Auth."""

    def test_init(self):
        """Test OAuth2Auth initialization."""
        config = {
            "auth_type": "oauth2",
            "credentials": {
                "client_id": "test_client",
                "client_secret": "test_secret"
            }
        }
        
        auth = OAuth2Auth(config)
        assert auth.token_data == {}
        assert auth.token_expiry is None
        assert auth.credential_manager is not None
    
    @pytest.mark.asyncio
    async def test_get_authorization_url(self):
        """Test generating authorization URL."""
        config = {
            "auth_type": "oauth2",
            "auth_url": "https://app.hubspot.com/oauth/authorize",
            "scope": "contacts",
            "credentials": {
                "client_id": "test_client_id"
            }
        }
        
        auth = OAuth2Auth(config)
        url = await auth.get_authorization_url("http://localhost:8000/callback")
        
        assert "https://app.hubspot.com/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=http%3A//localhost%3A8000/callback" in url
        assert "response_type=code" in url
        assert "scope=contacts" in url
        assert "state=" in url
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_with_custom_state(self):
        """Test generating authorization URL with custom state."""
        config = {
            "auth_type": "oauth2",
            "auth_url": "https://app.hubspot.com/oauth/authorize",
            "credentials": {
                "client_id": "test_client_id"
            }
        }
        
        auth = OAuth2Auth(config)
        url = await auth.get_authorization_url(
            "http://localhost:8000/callback",
            scopes="contacts crm.objects.deals.read",
            state="custom_state_123"
        )
        
        assert "state=custom_state_123" in url
        assert "scope=contacts+crm.objects.deals.read" in url
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_missing_auth_url(self):
        """Test error when auth_url is missing."""
        config = {
            "auth_type": "oauth2",
            "credentials": {
                "client_id": "test_client_id"
            }
        }
        
        auth = OAuth2Auth(config)
        
        with pytest.raises(ValueError, match="Authorization URL not configured"):
            await auth.get_authorization_url("http://localhost:8000/callback")
    
    @pytest.mark.asyncio
    async def test_get_authorization_url_missing_client_id(self):
        """Test error when client_id is missing."""
        config = {
            "auth_type": "oauth2",
            "auth_url": "https://app.hubspot.com/oauth/authorize",
            "credentials": {}
        }
        
        auth = OAuth2Auth(config)
        
        with pytest.raises(ValueError, match="Client ID not configured"):
            await auth.get_authorization_url("http://localhost:8000/callback")
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_exchange_code_for_token_success(self, mock_client):
        """Test successful token exchange."""
        # Mock response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "bearer"
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        config = {
            "auth_type": "oauth2",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "credentials": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            }
        }
        
        auth = OAuth2Auth(config)
        token_data = await auth.exchange_code_for_token(
            "auth_code_123",
            "http://localhost:8000/callback"
        )
        
        assert token_data["access_token"] == "test_access_token"
        assert token_data["refresh_token"] == "test_refresh_token"
        assert auth.credentials["refresh_token"] == "test_refresh_token"
        assert auth.token_expiry is not None
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_exchange_code_for_token_failure(self, mock_client):
        """Test failed token exchange."""
        # Mock response
        mock_response = Mock()
        mock_response.is_success = False
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        config = {
            "auth_type": "oauth2",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "credentials": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret"
            }
        }
        
        auth = OAuth2Auth(config)
        
        with pytest.raises(ValueError, match="Token exchange failed: 400"):
            await auth.exchange_code_for_token(
                "invalid_code",
                "http://localhost:8000/callback"
            )
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_refresh_token_success(self, mock_client):
        """Test successful token refresh."""
        # Mock response
        mock_response = Mock()
        mock_response.is_success = True
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
            "token_type": "bearer"
        }
        
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
        
        config = {
            "auth_type": "oauth2",
            "token_url": "https://api.hubapi.com/oauth/v1/token",
            "credentials": {
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "refresh_token": "old_refresh_token"
            }
        }
        
        auth = OAuth2Auth(config)
        token_data = await auth.refresh_token()
        
        assert token_data["access_token"] == "new_access_token"
        assert token_data["refresh_token"] == "new_refresh_token"
        assert auth.credentials["refresh_token"] == "new_refresh_token"


class TestTokenAuth:
    """Test cases for TokenAuth."""

    @pytest.mark.asyncio
    async def test_prepare_headers_default(self):
        """Test preparing token headers with default prefix."""
        config = {
            "auth_type": "token",
            "credentials": {
                "token": "test_token_123"
            }
        }
        
        auth = TokenAuth(config)
        headers = await auth.prepare_headers()
        
        assert headers == {"Authorization": "Bearer test_token_123"}
    
    @pytest.mark.asyncio
    async def test_prepare_headers_custom_prefix(self):
        """Test preparing token headers with custom prefix."""
        config = {
            "auth_type": "token",
            "token_prefix": "Token",
            "credentials": {
                "token": "test_token_123"
            }
        }
        
        auth = TokenAuth(config)
        headers = await auth.prepare_headers()
        
        assert headers == {"Authorization": "Token test_token_123"}


class TestCreateAuthHandler:
    """Test cases for create_auth_handler function."""

    def test_create_api_key_handler(self):
        """Test creating API key auth handler."""
        config = {"auth_type": "api_key"}
        handler = create_auth_handler(config)
        
        assert isinstance(handler, ApiKeyAuth)
    
    def test_create_basic_handler(self):
        """Test creating basic auth handler."""
        config = {"auth_type": "basic"}
        handler = create_auth_handler(config)
        
        assert isinstance(handler, BasicAuth)
    
    def test_create_oauth2_handler(self):
        """Test creating OAuth2 auth handler."""
        config = {"auth_type": "oauth2"}
        handler = create_auth_handler(config)
        
        assert isinstance(handler, OAuth2Auth)
    
    def test_create_token_handler(self):
        """Test creating token auth handler."""
        config = {"auth_type": "token"}
        handler = create_auth_handler(config)
        
        assert isinstance(handler, TokenAuth)
    
    def test_create_unknown_handler(self):
        """Test creating handler for unknown auth type."""
        config = {"auth_type": "unknown"}
        handler = create_auth_handler(config)
        
        assert isinstance(handler, IntegrationAuth)
        assert not isinstance(handler, (ApiKeyAuth, BasicAuth, OAuth2Auth, TokenAuth))