"""
Wave Authentication Manager
Handles OAuth2 authentication for Wave Accounting API access.
"""
import asyncio
import logging
import secrets
import hashlib
import base64
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    WaveAuthenticationError,
    WaveAuthorizationError,
    WaveConnectionError,
    WaveConfigurationError
)


logger = logging.getLogger(__name__)


class WaveAuthManager:
    """
    Manages OAuth2 authentication flow for Wave Accounting API.
    
    Wave uses OAuth2 with Authorization Code flow and PKCE for security.
    Supports both sandbox and production environments.
    """
    
    # Wave OAuth2 endpoints
    SANDBOX_BASE_URL = "https://api.waveapps.com"
    PRODUCTION_BASE_URL = "https://api.waveapps.com"
    
    AUTHORIZATION_ENDPOINT = "/oauth2/authorize/"
    TOKEN_ENDPOINT = "/oauth2/token/"
    USER_INFO_ENDPOINT = "/user/"
    
    # Required scopes for e-invoicing
    REQUIRED_SCOPES = [
        "businesses.read",
        "customers.read",
        "customers.write", 
        "products.read",
        "products.write",
        "invoices.read",
        "invoices.write",
        "sales.read"
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
        Initialize Wave authentication manager.
        
        Args:
            client_id: Wave application client ID
            client_secret: Wave application client secret
            redirect_uri: OAuth2 redirect URI (must match Wave app config)
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session to use
        """
        if not client_id or not client_secret:
            raise WaveConfigurationError("Client ID and client secret are required")
        
        if not redirect_uri:
            raise WaveConfigurationError("Redirect URI is required")
        
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
    
    def generate_pkce_challenge(self) -> Tuple[str, str]:
        """
        Generate PKCE code verifier and challenge for OAuth2 flow.
        
        Returns:
            Tuple of (code_verifier, code_challenge)
        """
        # Generate random code verifier
        code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Create SHA256 hash of verifier
        challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return code_verifier, code_challenge
    
    def get_authorization_url(self, state: Optional[str] = None) -> Tuple[str, str, str]:
        """
        Generate authorization URL for OAuth2 flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, code_verifier, state)
        """
        if state is None:
            state = secrets.token_urlsafe(32)
        
        code_verifier, code_challenge = self.generate_pkce_challenge()
        
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.REQUIRED_SCOPES),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256"
        }
        
        authorization_url = f"{self.base_url}{self.AUTHORIZATION_ENDPOINT}?{urlencode(params)}"
        
        return authorization_url, code_verifier, state
    
    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        code_verifier: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Authorization code from callback
            code_verifier: PKCE code verifier
            state: State parameter for validation
            
        Returns:
            Token response data
        """
        if not self.session:
            raise WaveConnectionError("No HTTP session available")
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "code": authorization_code,
            "code_verifier": code_verifier
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}{self.TOKEN_ENDPOINT}",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error_description", "Token exchange failed")
                    raise WaveAuthenticationError(f"Token exchange failed: {error_msg}")
                
                # Store tokens
                self.access_token = response_data.get("access_token")
                self.refresh_token = response_data.get("refresh_token")
                self.token_scope = response_data.get("scope")
                
                # Calculate expiration time
                expires_in = response_data.get("expires_in", 3600)
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
                
                logger.info("Successfully exchanged authorization code for tokens")
                return response_data
                
        except ClientError as e:
            raise WaveConnectionError(f"Failed to connect to Wave API: {str(e)}")
        except Exception as e:
            raise WaveAuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            New token response data
        """
        if not self.refresh_token:
            raise WaveAuthenticationError("No refresh token available")
        
        if not self.session:
            raise WaveConnectionError("No HTTP session available")
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}{self.TOKEN_ENDPOINT}",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get("error_description", "Token refresh failed")
                    raise WaveAuthenticationError(f"Token refresh failed: {error_msg}")
                
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
            raise WaveConnectionError(f"Failed to connect to Wave API: {str(e)}")
        except Exception as e:
            raise WaveAuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token
        """
        if not self.access_token:
            raise WaveAuthenticationError("No access token available")
        
        # Check if token is expired (with 5 minute buffer)
        if self.token_expires_at:
            buffer_time = datetime.utcnow() + timedelta(minutes=5)
            if buffer_time >= self.token_expires_at:
                logger.info("Access token expired, refreshing...")
                await self.refresh_access_token()
        
        return self.access_token
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get user information using the access token.
        
        Returns:
            User information
        """
        if not self.session:
            raise WaveConnectionError("No HTTP session available")
        
        token = await self.ensure_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.get(
                f"{self.base_url}{self.USER_INFO_ENDPOINT}",
                headers=headers
            ) as response:
                if response.status == 401:
                    raise WaveAuthenticationError("Invalid or expired access token")
                elif response.status == 403:
                    raise WaveAuthorizationError("Insufficient permissions")
                elif response.status != 200:
                    raise WaveAuthenticationError(f"Failed to get user info: {response.status}")
                
                return await response.json()
                
        except ClientError as e:
            raise WaveConnectionError(f"Failed to connect to Wave API: {str(e)}")
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dict with authorization
        """
        if not self.access_token:
            raise WaveAuthenticationError("No access token available")
        
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
    
    async def revoke_token(self) -> bool:
        """
        Revoke the current access token.
        
        Returns:
            True if revocation successful
        """
        if not self.access_token or not self.session:
            return True
        
        # Wave doesn't have a public revoke endpoint, so we just clear tokens
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.token_scope = None
        
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
            "is_expired": (
                self.token_expires_at and datetime.utcnow() >= self.token_expires_at
            ) if self.token_expires_at else False,
            "has_required_scopes": self.has_required_scopes()
        }