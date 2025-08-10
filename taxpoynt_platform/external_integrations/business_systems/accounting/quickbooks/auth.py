"""
QuickBooks Accounting Authentication Manager
Handles QuickBooks API authentication including OAuth2 and OpenID Connect.
"""
import asyncio
import logging
import hashlib
import hmac
import base64
import json
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp

from .exceptions import (
    QuickBooksAuthenticationError,
    QuickBooksConnectionError,
    QuickBooksPermissionError
)

logger = logging.getLogger(__name__)


class QuickBooksAuthManager:
    """
    QuickBooks Accounting Authentication Manager
    
    Handles QuickBooks API authentication methods:
    - OAuth2 Authorization Code flow
    - Token refresh and management
    - OpenID Connect for user information
    - Webhook signature verification
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize QuickBooks authentication manager.
        
        Args:
            config: Configuration dictionary containing:
                - client_id: QuickBooks app client ID (required)
                - client_secret: QuickBooks app client secret (required)
                - redirect_uri: OAuth2 redirect URI (required)
                - sandbox: Use sandbox environment (default: True)
                - scope: OAuth2 scope (default: com.intuit.quickbooks.accounting)
                - webhook_verifier_token: Token for webhook verification
                - access_token: Existing access token (optional)
                - refresh_token: Existing refresh token (optional)
                - company_id: QuickBooks company ID (optional)
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Required configuration
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise QuickBooksAuthenticationError(
                "client_id, client_secret, and redirect_uri are required for QuickBooks authentication"
            )
        
        # Environment configuration
        self.sandbox = config.get('sandbox', True)
        self.scope = config.get('scope', 'com.intuit.quickbooks.accounting')
        self.webhook_verifier_token = config.get('webhook_verifier_token', '')
        
        # Token management
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.company_id = config.get('company_id')
        self.token_expires_at = None
        
        # API URLs
        if self.sandbox:
            self.base_url = "https://sandbox-quickbooks.api.intuit.com"
            self.discovery_document_url = "https://developer.api.intuit.com/.well-known/connect_app_config"
        else:
            self.base_url = "https://quickbooks.api.intuit.com"
            self.discovery_document_url = "https://developer.api.intuit.com/.well-known/connect_app_config"
        
        # OAuth2 URLs
        self.oauth_base_url = "https://appcenter.intuit.com/connect/oauth2"
        self.token_url = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
        self.revoke_url = "https://developer.api.intuit.com/v2/oauth2/tokens/revoke"
        
        # Authentication state
        self._authenticated = False
        self._auth_headers = {}
        
        # Session for HTTP requests
        self.session = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with QuickBooks API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info("Authenticating with QuickBooks API...")
            
            if self.access_token:
                # Validate existing token
                if await self._validate_token():
                    self._set_auth_headers()
                    self._authenticated = True
                    self.logger.info("QuickBooks authentication successful with existing token")
                    return True
                elif self.refresh_token:
                    # Try to refresh token
                    if await self.refresh_access_token():
                        self._set_auth_headers()
                        self._authenticated = True
                        self.logger.info("QuickBooks authentication successful with refreshed token")
                        return True
            
            # No valid token available
            self.logger.warning("No valid QuickBooks access token available. Authorization flow required.")
            return False
            
        except Exception as e:
            self.logger.error(f"QuickBooks authentication error: {e}")
            self._authenticated = False
            raise QuickBooksAuthenticationError(f"Authentication failed: {e}")
    
    def generate_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth2 authorization URL for QuickBooks app installation.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            OAuth2 authorization URL
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'scope': self.scope,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'access_type': 'offline',
            'state': state
        }
        
        return f"{self.oauth_base_url}?{urlencode(params)}"
    
    async def exchange_code_for_tokens(
        self,
        authorization_code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange OAuth2 authorization code for access and refresh tokens.
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for verification
            
        Returns:
            Token response containing access_token, refresh_token, and company info
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Prepare token exchange request
            data = {
                'grant_type': 'authorization_code',
                'code': authorization_code,
                'redirect_uri': self.redirect_uri
            }
            
            # Create basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials_b64}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(self.token_url, data=data, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Store tokens
                    self.access_token = response_data.get('access_token')
                    self.refresh_token = response_data.get('refresh_token')
                    
                    # Parse company ID from realmId
                    realm_id = response_data.get('realmId')
                    if realm_id:
                        self.company_id = realm_id
                    
                    # Calculate token expiration
                    expires_in = response_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    self.logger.info(f"Successfully exchanged code for tokens. Company ID: {self.company_id}")
                    return response_data
                else:
                    error_msg = response_data.get('error_description', 'Token exchange failed')
                    raise QuickBooksAuthenticationError(f"Token exchange failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise QuickBooksConnectionError(f"Connection error during token exchange: {e}")
    
    async def refresh_access_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            True if refresh successful, False otherwise
        """
        try:
            if not self.refresh_token:
                self.logger.warning("No refresh token available")
                return False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Prepare refresh request
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            # Create basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials_b64}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(self.token_url, data=data, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Update tokens
                    self.access_token = response_data.get('access_token')
                    
                    # Update refresh token if provided (some implementations don't return it)
                    new_refresh_token = response_data.get('refresh_token')
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                    
                    # Calculate token expiration
                    expires_in = response_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    self.logger.info("Successfully refreshed access token")
                    return True
                else:
                    error_msg = response_data.get('error_description', 'Token refresh failed')
                    self.logger.error(f"Token refresh failed: {error_msg}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Token refresh error: {e}")
            return False
    
    async def _validate_token(self) -> bool:
        """
        Validate current access token by making a test API call.
        
        Returns:
            True if token is valid, False otherwise
        """
        try:
            if not self.access_token or not self.company_id:
                return False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test token with company info endpoint
            url = f"{self.base_url}/v3/company/{self.company_id}/companyinfo/{self.company_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    self.logger.warning("Access token is invalid or expired")
                    return False
                else:
                    self.logger.warning(f"Token validation returned status {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return False
    
    def _set_auth_headers(self):
        """Set authentication headers for API requests."""
        if self.access_token:
            self._auth_headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of authentication headers
        """
        if not self._authenticated:
            await self.authenticate()
        
        return self._auth_headers.copy()
    
    async def revoke_tokens(self) -> bool:
        """
        Revoke access and refresh tokens.
        
        Returns:
            True if revocation successful
        """
        try:
            if not self.refresh_token:
                self.logger.warning("No refresh token to revoke")
                return False
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Prepare revoke request
            data = {
                'token': self.refresh_token
            }
            
            # Create basic auth header
            credentials = f"{self.client_id}:{self.client_secret}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {credentials_b64}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(self.revoke_url, data=data, headers=headers) as response:
                if response.status == 200:
                    # Clear tokens
                    self.access_token = None
                    self.refresh_token = None
                    self.token_expires_at = None
                    self._authenticated = False
                    self._auth_headers = {}
                    
                    self.logger.info("Successfully revoked tokens")
                    return True
                else:
                    response_text = await response.text()
                    self.logger.error(f"Token revocation failed: {response.status} - {response_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Token revocation error: {e}")
            return False
    
    async def verify_webhook_signature(
        self,
        payload: Union[str, bytes, Dict[str, Any]],
        signature: str
    ) -> bool:
        """
        Verify QuickBooks webhook signature.
        
        Args:
            payload: Webhook payload (string, bytes, or dict)
            signature: Webhook signature from headers
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_verifier_token:
                self.logger.warning("No webhook verifier token configured - cannot verify signature")
                return True  # Allow webhook if no token configured
            
            # Convert payload to string if needed
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            elif isinstance(payload, bytes):
                payload_str = payload.decode('utf-8')
            else:
                payload_str = str(payload)
            
            # Create expected signature using HMAC-SHA256
            expected_signature = hmac.new(
                self.webhook_verifier_token.encode('utf-8'),
                payload_str.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Base64 encode the signature
            expected_signature_b64 = base64.b64encode(expected_signature).decode()
            
            # Compare signatures securely
            return hmac.compare_digest(signature, expected_signature_b64)
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def get_company_id(self) -> Optional[str]:
        """Get the current company ID."""
        return self.company_id
    
    def get_base_url(self) -> str:
        """Get the base API URL."""
        return self.base_url
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated
    
    def is_sandbox(self) -> bool:
        """Check if using sandbox environment."""
        return self.sandbox
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get current token information.
        
        Returns:
            Dictionary with token information
        """
        return {
            'has_access_token': bool(self.access_token),
            'has_refresh_token': bool(self.refresh_token),
            'company_id': self.company_id,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'is_expired': self.token_expires_at < datetime.now() if self.token_expires_at else False,
            'sandbox': self.sandbox
        }
    
    async def close(self):
        """Close the authentication manager and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self._authenticated = False
        self._auth_headers = {}
    
    def __str__(self) -> str:
        """String representation of the auth manager."""
        return f"QuickBooksAuthManager(client_id={self.client_id[:8]}..., sandbox={self.sandbox})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the auth manager."""
        return (f"QuickBooksAuthManager("
                f"client_id='{self.client_id[:8]}...', "
                f"company_id='{self.company_id}', "
                f"sandbox={self.sandbox}, "
                f"authenticated={self._authenticated})")