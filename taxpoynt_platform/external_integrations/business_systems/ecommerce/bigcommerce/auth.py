"""
BigCommerce E-commerce Authentication Manager
Handles BigCommerce API authentication including OAuth2 and API token authentication.
"""
import asyncio
import logging
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp

from .exceptions import (
    BigCommerceAuthenticationError,
    BigCommerceConnectionError,
    BigCommerceAPIError
)

logger = logging.getLogger(__name__)


class BigCommerceAuthManager:
    """
    BigCommerce E-commerce Authentication Manager
    
    Handles various BigCommerce authentication methods:
    - API Token (X-Auth-Token) - recommended for server-to-server
    - OAuth2 Apps - for public applications
    - Store API Tokens - for single-store integrations
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize BigCommerce authentication manager.
        
        Args:
            config: Configuration dictionary containing:
                - store_hash: BigCommerce store hash (required)
                - auth_type: Authentication type ('api_token', 'oauth2', 'store_token')
                - api_token: API access token (for api_token auth)
                - client_id: OAuth2 client ID (for oauth2 auth)
                - client_secret: OAuth2 client secret (for oauth2 auth)
                - access_token: OAuth2 access token (for oauth2 auth)
                - store_token: Store-specific API token (for store_token auth)
                - webhook_secret: Secret for webhook verification
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Required configuration
        self.store_hash = config.get('store_hash')
        if not self.store_hash:
            raise BigCommerceAuthenticationError("store_hash is required for BigCommerce authentication")
        
        # Authentication configuration
        self.auth_type = config.get('auth_type', 'api_token')
        self.api_token = config.get('api_token')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.access_token = config.get('access_token')
        self.store_token = config.get('store_token')
        self.webhook_secret = config.get('webhook_secret', '')
        
        # Authentication state
        self._authenticated = False
        self._auth_headers = {}
        self._token_expires_at = None
        
        # Base API URL
        self.base_url = f"https://api.bigcommerce.com/stores/{self.store_hash}/v3"
        
        # Session for HTTP requests
        self.session = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with BigCommerce API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info(f"Authenticating with BigCommerce using {self.auth_type} method...")
            
            if self.auth_type == 'api_token':
                success = await self._authenticate_api_token()
            elif self.auth_type == 'oauth2':
                success = await self._authenticate_oauth2()
            elif self.auth_type == 'store_token':
                success = await self._authenticate_store_token()
            else:
                raise BigCommerceAuthenticationError(f"Unsupported authentication type: {self.auth_type}")
            
            if success:
                self._authenticated = True
                self.logger.info("BigCommerce authentication successful")
            else:
                self.logger.error("BigCommerce authentication failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"BigCommerce authentication error: {e}")
            self._authenticated = False
            raise BigCommerceAuthenticationError(f"Authentication failed: {e}")
    
    async def _authenticate_api_token(self) -> bool:
        """Authenticate using API token (X-Auth-Token)."""
        if not self.api_token:
            raise BigCommerceAuthenticationError("api_token is required for API token authentication")
        
        try:
            # Set authentication headers
            self._auth_headers = {
                'X-Auth-Token': self.api_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Test authentication with a simple API call
            await self._test_authentication()
            return True
            
        except Exception as e:
            raise BigCommerceAuthenticationError(f"API token authentication failed: {e}")
    
    async def _authenticate_oauth2(self) -> bool:
        """Authenticate using OAuth2."""
        if not self.client_id or not self.access_token:
            raise BigCommerceAuthenticationError("client_id and access_token are required for OAuth2 authentication")
        
        try:
            # Set authentication headers
            self._auth_headers = {
                'X-Auth-Client': self.client_id,
                'X-Auth-Token': self.access_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Test authentication
            await self._test_authentication()
            return True
            
        except Exception as e:
            raise BigCommerceAuthenticationError(f"OAuth2 authentication failed: {e}")
    
    async def _authenticate_store_token(self) -> bool:
        """Authenticate using store-specific token."""
        if not self.store_token:
            raise BigCommerceAuthenticationError("store_token is required for store token authentication")
        
        try:
            # Set authentication headers
            self._auth_headers = {
                'X-Auth-Token': self.store_token,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Test authentication
            await self._test_authentication()
            return True
            
        except Exception as e:
            raise BigCommerceAuthenticationError(f"Store token authentication failed: {e}")
    
    async def _test_authentication(self):
        """Test authentication with a simple API call."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test with store information endpoint
            url = f"{self.base_url}/store/information"
            
            async with self.session.get(url, headers=self._auth_headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise BigCommerceAuthenticationError("Invalid authentication credentials")
                elif response.status == 403:
                    raise BigCommerceAuthenticationError("Insufficient permissions")
                else:
                    response_text = await response.text()
                    raise BigCommerceAuthenticationError(f"Authentication test failed: {response.status} - {response_text}")
                    
        except aiohttp.ClientError as e:
            raise BigCommerceConnectionError(f"Connection error during authentication test: {e}")
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of authentication headers
        """
        if not self._authenticated:
            await self.authenticate()
        
        return self._auth_headers.copy()
    
    async def refresh_authentication(self) -> bool:
        """
        Refresh authentication if needed.
        
        Returns:
            True if refresh successful or not needed, False otherwise
        """
        try:
            # For BigCommerce, most tokens don't expire automatically
            # But we can re-validate the current authentication
            return await self._test_authentication()
            
        except Exception as e:
            self.logger.warning(f"Authentication refresh failed: {e}")
            self._authenticated = False
            return False
    
    async def validate_authentication(self) -> bool:
        """
        Validate current authentication status.
        
        Returns:
            True if authentication is valid, False otherwise
        """
        try:
            if not self._authenticated:
                return False
            
            # Test current authentication
            await self._test_authentication()
            return True
            
        except Exception as e:
            self.logger.warning(f"Authentication validation failed: {e}")
            self._authenticated = False
            return False
    
    async def revoke_authentication(self) -> bool:
        """
        Revoke authentication.
        
        Returns:
            True if revocation successful
        """
        try:
            # Clear authentication state
            self._authenticated = False
            self._auth_headers = {}
            self._token_expires_at = None
            
            # Close session if open
            if self.session:
                await self.session.close()
                self.session = None
            
            self.logger.info("BigCommerce authentication revoked")
            return True
            
        except Exception as e:
            self.logger.error(f"Error revoking authentication: {e}")
            return False
    
    async def verify_webhook_signature(
        self,
        payload: Union[str, bytes, Dict[str, Any]],
        signature: str,
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify BigCommerce webhook signature.
        
        Args:
            payload: Webhook payload (string, bytes, or dict)
            signature: Webhook signature from headers
            timestamp: Webhook timestamp (optional)
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            if not self.webhook_secret:
                self.logger.warning("No webhook secret configured - cannot verify signature")
                return True  # Allow webhook if no secret configured
            
            # Convert payload to string if needed
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            elif isinstance(payload, bytes):
                payload_str = payload.decode('utf-8')
            else:
                payload_str = str(payload)
            
            # Create expected signature
            secret_bytes = self.webhook_secret.encode('utf-8')
            payload_bytes = payload_str.encode('utf-8')
            
            expected_signature = hmac.new(
                secret_bytes,
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature.lower(), expected_signature.lower())
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def generate_oauth2_authorization_url(
        self,
        redirect_uri: str,
        scope: str = "store_v2_orders store_v2_products store_v2_customers",
        state: Optional[str] = None
    ) -> str:
        """
        Generate OAuth2 authorization URL for app installation.
        
        Args:
            redirect_uri: OAuth2 redirect URI
            scope: Requested permissions scope
            state: Optional state parameter for CSRF protection
            
        Returns:
            OAuth2 authorization URL
        """
        if not self.client_id:
            raise BigCommerceAuthenticationError("client_id is required to generate authorization URL")
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope
        }
        
        if state:
            params['state'] = state
        
        base_url = "https://login.bigcommerce.com/oauth2/authorize"
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
        scope: str
    ) -> Dict[str, Any]:
        """
        Exchange OAuth2 authorization code for access token.
        
        Args:
            code: Authorization code from callback
            redirect_uri: OAuth2 redirect URI (must match)
            scope: Requested scope (must match)
            
        Returns:
            Token response containing access_token and other details
        """
        if not self.client_id or not self.client_secret:
            raise BigCommerceAuthenticationError("client_id and client_secret are required for token exchange")
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            token_url = "https://login.bigcommerce.com/oauth2/token"
            
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code',
                'code': code,
                'scope': scope
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, data=data, headers=headers) as response:
                response_data = await response.json()
                
                if response.status == 200:
                    # Store the access token
                    self.access_token = response_data.get('access_token')
                    self.store_hash = response_data.get('context', '').replace('stores/', '')
                    
                    # Update base URL with new store hash
                    if self.store_hash:
                        self.base_url = f"https://api.bigcommerce.com/stores/{self.store_hash}/v3"
                    
                    return response_data
                else:
                    error_msg = response_data.get('error_description', 'Token exchange failed')
                    raise BigCommerceAuthenticationError(f"Token exchange failed: {error_msg}")
                    
        except aiohttp.ClientError as e:
            raise BigCommerceConnectionError(f"Connection error during token exchange: {e}")
    
    def get_store_hash(self) -> Optional[str]:
        """Get the current store hash."""
        return self.store_hash
    
    def get_base_url(self) -> str:
        """Get the base API URL for the current store."""
        return self.base_url
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated
    
    async def close(self):
        """Close the authentication manager and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self._authenticated = False
        self._auth_headers = {}
    
    def __str__(self) -> str:
        """String representation of the auth manager."""
        return f"BigCommerceAuthManager(store_hash={self.store_hash}, auth_type={self.auth_type})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the auth manager."""
        return (f"BigCommerceAuthManager("
                f"store_hash='{self.store_hash}', "
                f"auth_type='{self.auth_type}', "
                f"authenticated={self._authenticated})")