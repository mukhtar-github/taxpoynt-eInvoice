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

logger = logging.getLogger(__name__)


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
    """OAuth2 authentication handler."""
    
    def __init__(self, auth_config: Dict[str, Any]):
        """
        Initialize the OAuth2 authentication handler.
        
        Args:
            auth_config: Authentication configuration
        """
        super().__init__(auth_config)
        self.token_data = {}
        self.token_expiry = None
    
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
