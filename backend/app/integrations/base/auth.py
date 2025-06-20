"""
Authentication handler for integration connectors.

This module provides authentication mechanisms for different authentication types
commonly used by external systems:
- API Key
- OAuth2
- Basic Auth
- Token-based auth
"""

import base64
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import httpx
import secrets
import urllib.parse
from cryptography.fernet import Fernet

from app.core.config import settings

logger = logging.getLogger(__name__)


class SecureCredentialManager:
    """Secure manager for integration credentials with encryption."""
    
    def __init__(self):
        """Initialize with encryption key from settings."""
        # Use the encryption key from settings or generate one
        encryption_key = getattr(settings, 'CREDENTIAL_ENCRYPTION_KEY', None)
        if not encryption_key:
            # Generate a key for development (in production, this should be set in settings)
            encryption_key = Fernet.generate_key()
            logger.warning("No CREDENTIAL_ENCRYPTION_KEY found in settings. Using generated key.")
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
            
        self.cipher_suite = Fernet(encryption_key)
        
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials for secure storage.
        
        Args:
            credentials: Dictionary of credential information
            
        Returns:
            str: Encrypted credentials string
        """
        if not credentials:
            return ""
            
        # Convert to JSON string
        credentials_json = json.dumps(credentials, sort_keys=True)
        
        # Encrypt
        encrypted_data = self.cipher_suite.encrypt(credentials_json.encode('utf-8'))
        
        return encrypted_data.decode('utf-8')
        
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credentials for use.
        
        Args:
            encrypted_data: Encrypted credentials string
            
        Returns:
            Dict: Decrypted credentials dictionary
        """
        if not encrypted_data:
            return {}
            
        try:
            # Decrypt
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
            
            # Convert from JSON
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            return {}


class OAuthHandler:
    """OAuth 2.0 handler for external integrations."""
    
    def __init__(self, platform_name: str, credential_manager: SecureCredentialManager):
        """
        Initialize OAuth handler.
        
        Args:
            platform_name: Name of the platform (e.g., 'hubspot', 'salesforce')
            credential_manager: Secure credential manager instance
        """
        self.platform_name = platform_name
        self.credential_manager = credential_manager
        self.token_data = {}
        self.token_expiry = None
        
    async def get_authorization_url(self, redirect_uri: str, scopes: Optional[str] = None, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            redirect_uri: URI to redirect to after authorization
            scopes: Optional space-separated list of scopes
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        # This method should be implemented by platform-specific subclasses
        raise NotImplementedError("Must be implemented by platform-specific subclasses")
        
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth provider
            redirect_uri: URI that was used in authorization request
            
        Returns:
            Dict containing token information
        """
        # This method should be implemented by platform-specific subclasses
        raise NotImplementedError("Must be implemented by platform-specific subclasses")
        
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            Dict containing new token information
        """
        # This method should be implemented by platform-specific subclasses
        raise NotImplementedError("Must be implemented by platform-specific subclasses")


class IntegrationAuth:
    """Base authentication handler for integration connectors."""
    
    def __init__(self, auth_config: Dict[str, Any]):
        """
        Initialize the authentication handler.
        
        Args:
            auth_config: Authentication configuration
        """
        self.config = auth_config
        self.type = auth_config.get("auth_type", "unknown")
        self.credentials = auth_config.get("credentials", {})


class ApiKeyAuth(IntegrationAuth):
    """API key authentication handler."""
    
    async def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare authentication headers for API key authentication.
        
        Returns:
            Dict containing authentication headers
        """
        key_name = self.config.get("key_name", "X-API-Key")
        key_value = self.credentials.get("api_key", "")
        
        return {key_name: key_value}


class BasicAuth(IntegrationAuth):
    """Basic authentication handler."""
    
    async def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare authentication headers for basic authentication.
        
        Returns:
            Dict containing authentication headers
        """
        username = self.credentials.get("username", "")
        password = self.credentials.get("password", "")
        
        auth_string = f"{username}:{password}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        
        return {"Authorization": f"Basic {encoded}"}


class OAuth2Auth(IntegrationAuth):
    """OAuth2 authentication handler with full OAuth 2.0 flow support."""
    
    def __init__(self, auth_config: Dict[str, Any]):
        """
        Initialize the OAuth2 authentication handler.
        
        Args:
            auth_config: Authentication configuration
        """
        super().__init__(auth_config)
        self.token_data = {}
        self.token_expiry = None
        self.credential_manager = SecureCredentialManager()
    
    async def get_access_token(self) -> Tuple[str, datetime]:
        """
        Get or refresh OAuth2 access token.
        
        Returns:
            Tuple of (access_token, expiry_datetime)
        """
        client_id = self.credentials.get("client_id", "")
        client_secret = self.credentials.get("client_secret", "")
        token_url = self.config.get("token_url", "")
        refresh_token = self.credentials.get("refresh_token")
        
        # If we have an existing non-expired token, return it
        if self.token_data.get("access_token") and self.token_expiry and \
           datetime.now() < self.token_expiry - timedelta(minutes=5):
            return self.token_data["access_token"], self.token_expiry
        
        # Otherwise, get a new token
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        if refresh_token:
            data.update({
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            })
        else:
            data.update({
                "grant_type": "client_credentials"
            })
            
        # Handle additional OAuth parameters
        scope = self.config.get("scope")
        if scope:
            data["scope"] = scope
            
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            
        self.token_data = token_data
        
        # Calculate token expiry time
        expires_in = token_data.get("expires_in", 3600)  # Default to 1 hour
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        # Store the refresh token if provided
        if token_data.get("refresh_token"):
            self.credentials["refresh_token"] = token_data["refresh_token"]
            
        return token_data["access_token"], self.token_expiry
    
    async def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare authentication headers for OAuth2 authentication.
        
        Returns:
            Dict containing authentication headers
        """
        token, _ = await self.get_access_token()
        return {"Authorization": f"Bearer {token}"}
    
    async def get_authorization_url(self, redirect_uri: str, scopes: Optional[str] = None, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL for the authorization code flow.
        
        Args:
            redirect_uri: URI to redirect to after authorization
            scopes: Optional space-separated list of scopes
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL
        """
        auth_url = self.config.get("auth_url")
        if not auth_url:
            raise ValueError("Authorization URL not configured")
            
        client_id = self.credentials.get("client_id")
        if not client_id:
            raise ValueError("Client ID not configured")
            
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
        }
        
        if scopes:
            params["scope"] = scopes
        elif self.config.get("scope"):
            params["scope"] = self.config["scope"]
            
        if state:
            params["state"] = state
        else:
            # Generate a random state for CSRF protection
            params["state"] = secrets.token_urlsafe(32)
            
        # Add any additional authorization parameters
        extra_params = self.config.get("auth_params", {})
        params.update(extra_params)
        
        query_string = urllib.parse.urlencode(params)
        return f"{auth_url}?{query_string}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth provider
            redirect_uri: URI that was used in authorization request
            state: State parameter for verification
            
        Returns:
            Dict containing token information
        """
        token_url = self.config.get("token_url")
        if not token_url:
            raise ValueError("Token URL not configured")
            
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        
        if not client_id or not client_secret:
            raise ValueError("Client credentials not configured")
            
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
            
            if not response.is_success:
                error_detail = response.text
                logger.error(f"Token exchange failed: {response.status_code} - {error_detail}")
                raise ValueError(f"Token exchange failed: {response.status_code}")
                
            token_data = response.json()
            
        # Store token data and calculate expiry
        self.token_data = token_data
        expires_in = token_data.get("expires_in", 3600)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        # Update credentials with new tokens
        if token_data.get("refresh_token"):
            self.credentials["refresh_token"] = token_data["refresh_token"]
            
        return token_data
    
    async def refresh_token(self, refresh_token: Optional[str] = None) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: Optional refresh token (uses stored one if not provided)
            
        Returns:
            Dict containing new token information
        """
        token_url = self.config.get("token_url")
        if not token_url:
            raise ValueError("Token URL not configured")
            
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        
        if not client_id or not client_secret:
            raise ValueError("Client credentials not configured")
            
        refresh_token = refresh_token or self.credentials.get("refresh_token")
        if not refresh_token:
            raise ValueError("No refresh token available")
            
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        
        # Add scope if configured
        if self.config.get("scope"):
            data["scope"] = self.config["scope"]
            
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data, headers=headers)
            
            if not response.is_success:
                error_detail = response.text
                logger.error(f"Token refresh failed: {response.status_code} - {error_detail}")
                raise ValueError(f"Token refresh failed: {response.status_code}")
                
            token_data = response.json()
            
        # Update stored token data
        self.token_data = token_data
        expires_in = token_data.get("expires_in", 3600)
        self.token_expiry = datetime.now() + timedelta(seconds=expires_in)
        
        # Update credentials with new tokens
        if token_data.get("refresh_token"):
            self.credentials["refresh_token"] = token_data["refresh_token"]
            
        return token_data


class TokenAuth(IntegrationAuth):
    """Token-based authentication handler."""
    
    async def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare authentication headers for token authentication.
        
        Returns:
            Dict containing authentication headers
        """
        token = self.credentials.get("token", "")
        token_prefix = self.config.get("token_prefix", "Bearer")
        
        return {"Authorization": f"{token_prefix} {token}"}


def create_auth_handler(auth_config: Dict[str, Any]) -> IntegrationAuth:
    """
    Create appropriate authentication handler based on config.
    
    Args:
        auth_config: Authentication configuration
        
    Returns:
        IntegrationAuth handler instance
    """
    auth_type = auth_config.get("auth_type", "").lower()
    
    if auth_type == "api_key":
        return ApiKeyAuth(auth_config)
    elif auth_type == "basic":
        return BasicAuth(auth_config)
    elif auth_type == "oauth2":
        return OAuth2Auth(auth_config)
    elif auth_type == "token":
        return TokenAuth(auth_config)
    else:
        logger.warning(f"Unknown auth type: {auth_type}, using default implementation")
        return IntegrationAuth(auth_config)
