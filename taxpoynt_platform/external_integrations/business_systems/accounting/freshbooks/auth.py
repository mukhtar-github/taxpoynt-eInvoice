"""
FreshBooks Authentication Manager
Handles OAuth2 authentication for FreshBooks API access.
"""
import asyncio
import logging
import secrets
import base64
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    FreshBooksAuthenticationError,
    FreshBooksAuthorizationError,
    FreshBooksConnectionError,
    FreshBooksConfigurationError
)


logger = logging.getLogger(__name__)


class FreshBooksAuthManager:
    """
    Manages OAuth2 authentication flow for FreshBooks API.
    
    FreshBooks uses OAuth2 with Authorization Code flow.
    Supports both sandbox and production environments.
    """
    
    # FreshBooks OAuth2 endpoints
    SANDBOX_BASE_URL = "https://api.freshbooks.com"
    PRODUCTION_BASE_URL = "https://api.freshbooks.com"
    
    AUTHORIZATION_ENDPOINT = "/service/auth/oauth/authorize"
    TOKEN_ENDPOINT = "/service/auth/oauth/token"
    IDENTITY_ENDPOINT = "/auth/api/v1/users/me"
    
    # Required scopes for e-invoicing
    REQUIRED_SCOPES = [
        "user:profile:read",
        "user:clients:read",
        "user:clients:write",
        "user:items:read", 
        "user:items:write",
        "user:invoices:read",
        "user:invoices:write",
        "user:payments:read"
    ]
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        sandbox: bool = True,
        session: Optional[ClientSession] = None
    ):
        """
        Initialize FreshBooks authentication manager.
        
        Args:
            client_id: FreshBooks application client ID
            client_secret: FreshBooks application client secret
            redirect_uri: OAuth2 redirect URI (must match FreshBooks app config)
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session to use
        """
        if not client_id or not client_secret:
            raise FreshBooksConfigurationError("Client ID and client secret are required")
        
        if not redirect_uri:
            raise FreshBooksConfigurationError("Redirect URI is required")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sandbox = sandbox
        self.session = session
        self.should_close_session = session is None
        
        self.base_url = self.SANDBOX_BASE_URL if sandbox else self.PRODUCTION_BASE_URL
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        self.token_scope: Optional[str] = None
        self.account_id: Optional[str] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=30, connect=10)
            self.session = ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str]:
        """
        Generate authorization URL for OAuth2 flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.REQUIRED_SCOPES),
            "state": state
        }
        
        authorization_url = f"{self.base_url}{self.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
        
        return authorization_url, state
    
    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for validation
            
        Returns:
            Token response data
        """
        if not self.session:
            raise FreshBooksConnectionError("No HTTP session available")
        
        # Prepare authentication
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_header = base64.b64encode(auth_bytes).decode('ascii')
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code": authorization_code
        }
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}{self.TOKEN_ENDPOINT}",
                data=data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error_description", "Token exchange failed")
                    raise FreshBooksAuthenticationError(f"Token exchange failed: {error_msg}")
                
                # Store tokens
                self.access_token = response_data.get("access_token")
                self.refresh_token = response_data.get("refresh_token")
                self.token_scope = response_data.get("scope")
                
                # Calculate expiration time
                expires_in = response_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                # Get account ID from identity endpoint
                await self._fetch_account_info()
                
                logger.info("Successfully exchanged authorization code for tokens")
                return response_data
                
        except ClientError as e:
            raise FreshBooksConnectionError(f"Failed to connect to FreshBooks API: {str(e)}")
        except Exception as e:
            raise FreshBooksAuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            New token response data
        """
        if not self.refresh_token:
            raise FreshBooksAuthenticationError("No refresh token available")
        
        if not self.session:
            raise FreshBooksConnectionError("No HTTP session available")
        
        # Prepare authentication
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_header = base64.b64encode(auth_bytes).decode('ascii')
        
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}{self.TOKEN_ENDPOINT}",
                data=data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error_description", "Token refresh failed")
                    raise FreshBooksAuthenticationError(f"Token refresh failed: {error_msg}")
                
                # Update tokens
                self.access_token = response_data.get("access_token")
                if "refresh_token" in response_data:
                    self.refresh_token = response_data["refresh_token"]
                self.token_scope = response_data.get("scope")
                
                # Update expiration time
                expires_in = response_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("Successfully refreshed access token")
                return response_data
                
        except ClientError as e:
            raise FreshBooksConnectionError(f"Failed to connect to FreshBooks API: {str(e)}")
        except Exception as e:
            raise FreshBooksAuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token
        """
        if not self.access_token:
            raise FreshBooksAuthenticationError("No access token available")
        
        # Check if token is expired (with 5 minute buffer)
        if self.token_expires_at:
            buffer_time = datetime.utcnow() + timedelta(minutes=5)
            if buffer_time >= self.token_expires_at:
                logger.info("Access token expired, refreshing...")
                await self.refresh_access_token()
        
        return self.access_token
    
    async def _fetch_account_info(self) -> None:
        """Fetch account information after authentication."""
        if not self.session or not self.access_token:
            return
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                f"{self.base_url}{self.IDENTITY_ENDPOINT}",
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Extract account ID from response
                    if "response" in data and data["response"]:
                        user_data = data["response"]
                        # FreshBooks identity response contains business memberships
                        memberships = user_data.get("business_memberships", [])
                        if memberships:
                            # Use the first business account
                            self.account_id = memberships[0].get("business", {}).get("account_id")
                        
        except Exception as e:
            logger.warning(f"Failed to fetch account info: {e}")
    
    async def get_identity_info(self) -> Dict[str, Any]:
        """
        Get user identity information using the access token.
        
        Returns:
            User identity information
        """
        if not self.session:
            raise FreshBooksConnectionError("No HTTP session available")
        
        token = await self.ensure_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                f"{self.base_url}{self.IDENTITY_ENDPOINT}",
                headers=headers
            ) as response:
                if response.status == 401:
                    raise FreshBooksAuthenticationError("Invalid or expired access token")
                elif response.status == 403:
                    raise FreshBooksAuthorizationError("Insufficient permissions")
                elif response.status != 200:
                    raise FreshBooksAuthenticationError(f"Failed to get identity info: {response.status}")
                
                return await response.json()
                
        except ClientError as e:
            raise FreshBooksConnectionError(f"Failed to connect to FreshBooks API: {str(e)}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dict with authorization
        """
        if not self.access_token:
            raise FreshBooksAuthenticationError("No access token available")
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self.access_token is not None
    
    def has_required_scopes(self) -> bool:
        """
        Check if we have all required scopes.
        
        Returns:
            True if all required scopes are granted
        """
        if not self.token_scope:
            return False
        
        granted_scopes = set(self.token_scope.split())
        required_scopes = set(self.REQUIRED_SCOPES)
        
        return required_scopes.issubset(granted_scopes)
    
    def get_account_id(self) -> Optional[str]:
        """
        Get the FreshBooks account ID.
        
        Returns:
            Account ID if available
        """
        return self.account_id
    
    async def revoke_token(self) -> bool:
        """
        Revoke the current access token.
        
        Returns:
            True if revocation successful
        """
        if not self.access_token or not self.session:
            return True
        
        # FreshBooks doesn't have a public revoke endpoint, so we just clear tokens
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.token_scope = None
        self.account_id = None
        
        logger.info("Tokens cleared successfully")
        return True
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get current token information.
        
        Returns:
            Token information dict
        """
        return {
            "has_access_token": self.access_token is not None,
            "has_refresh_token": self.refresh_token is not None,
            "token_expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
            "token_scope": self.token_scope,
            "account_id": self.account_id,
            "is_expired": (
                self.token_expires_at and datetime.utcnow() >= self.token_expires_at
            ) if self.token_expires_at else False,
            "has_required_scopes": self.has_required_scopes()
        }