"""
Shopify E-commerce Authentication Manager
Handles OAuth 2.0 authentication and API access token management for Shopify stores.
"""

import asyncio
import logging
import hashlib
import hmac
import base64
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import secrets
import aiohttp

from ....framework.models.base_models import ConnectionConfig
from ....shared.exceptions.integration_exceptions import AuthenticationError
from .exceptions import (
    ShopifyAuthenticationError,
    ShopifyConfigurationError,
    create_shopify_exception
)

logger = logging.getLogger(__name__)


class ShopifyAuthManager:
    """
    Shopify OAuth 2.0 Authentication Manager
    
    Handles Shopify app authentication using OAuth 2.0 flow including:
    - OAuth authorization URL generation
    - Access token exchange
    - Token validation and refresh
    - API access token management
    - Webhook signature verification
    - Private app authentication support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Shopify authentication manager.
        
        Args:
            config: Connection configuration with Shopify credentials
        """
        self.config = config
        self.credentials = config.credentials
        
        # Extract Shopify-specific configuration
        self.shop_name = self.credentials.get('shop_name', '').replace('.myshopify.com', '')
        self.api_key = self.credentials.get('api_key')
        self.api_secret = self.credentials.get('api_secret')
        self.access_token = self.credentials.get('access_token')
        self.webhook_secret = self.credentials.get('webhook_secret')
        self.private_app = self.credentials.get('private_app', False)
        self.api_version = self.credentials.get('api_version', '2023-10')
        
        # OAuth configuration
        self.oauth_config = {
            'redirect_uri': self.credentials.get('redirect_uri', 'http://localhost:3000/auth/callback'),
            'scopes': self.credentials.get('scopes', [
                'read_orders', 'read_products', 'read_customers',
                'read_inventory', 'read_locations', 'read_fulfillments',
                'read_shipping', 'read_analytics'
            ]),
            'state': None  # Will be generated for each auth request
        }
        
        # Authentication state
        self._authenticated = False
        self._token_expires_at: Optional[datetime] = None
        
        # Shopify URLs
        if self.shop_name:
            self.shop_domain = f"{self.shop_name}.myshopify.com"
            self.base_url = f"https://{self.shop_domain}"
            self.api_base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
        else:
            self.shop_domain = None
            self.base_url = None
            self.api_base_url = None
        
        logger.info(f"Initialized Shopify auth manager for shop: {self.shop_name}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Shopify API.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            ShopifyAuthenticationError: If authentication fails
        """
        try:
            if not self.shop_name:
                raise ShopifyAuthenticationError("Shop name is required for authentication")
            
            if self.private_app:
                # Private app authentication using password/access token
                success = await self._authenticate_private_app()
            elif self.access_token:
                # Public app with existing access token
                success = await self._validate_existing_token()
            else:
                # Public app requiring OAuth flow
                raise ShopifyAuthenticationError(
                    "OAuth flow required - use get_authorization_url() to start OAuth process"
                )
            
            self._authenticated = success
            
            if success:
                logger.info(f"Successfully authenticated with Shopify shop: {self.shop_name}")
            
            return success
            
        except Exception as e:
            logger.error(f"Shopify authentication failed: {str(e)}")
            raise create_shopify_exception(e, {
                'shop_name': self.shop_name,
                'auth_type': 'private_app' if self.private_app else 'oauth'
            })
    
    async def _authenticate_private_app(self) -> bool:
        """Authenticate using private app credentials."""
        if not self.access_token:
            raise ShopifyAuthenticationError("Access token required for private app authentication")
        
        # Test the token by making a simple API call
        return await self._test_api_access()
    
    async def _validate_existing_token(self) -> bool:
        """Validate existing OAuth access token."""
        if not self.access_token:
            return False
        
        # Test the token by making a simple API call
        return await self._test_api_access()
    
    async def _test_api_access(self) -> bool:
        """Test API access with current token."""
        try:
            headers = self._get_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/shop.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        shop_data = await response.json()
                        self._update_shop_info(shop_data.get('shop', {}))
                        return True
                    elif response.status == 401:
                        logger.error("Invalid or expired Shopify access token")
                        return False
                    else:
                        logger.error(f"API test failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"API access test failed: {str(e)}")
            return False
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth authorization URL for public apps.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            str: Authorization URL
            
        Raises:
            ShopifyConfigurationError: If required parameters are missing
        """
        if not self.shop_name or not self.api_key:
            raise ShopifyConfigurationError("Shop name and API key required for OAuth")
        
        if not state:
            state = secrets.token_urlsafe(32)
        
        self.oauth_config['state'] = state
        
        params = {
            'client_id': self.api_key,
            'scope': ','.join(self.oauth_config['scopes']),
            'redirect_uri': self.oauth_config['redirect_uri'],
            'state': state
        }
        
        auth_url = f"{self.base_url}/admin/oauth/authorize?{urlencode(params)}"
        
        logger.info(f"Generated Shopify OAuth URL for shop: {self.shop_name}")
        return auth_url
    
    async def exchange_authorization_code(
        self,
        code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            state: State parameter from OAuth callback
            
        Returns:
            Dict: Token response including access_token and scope
            
        Raises:
            ShopifyAuthenticationError: If token exchange fails
        """
        try:
            # Validate state parameter if provided
            if state and self.oauth_config.get('state') != state:
                raise ShopifyAuthenticationError("Invalid state parameter - possible CSRF attack")
            
            # Prepare token exchange request
            token_data = {
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'code': code
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/admin/oauth/access_token",
                    json=token_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        token_response = await response.json()
                        
                        # Store the access token
                        self.access_token = token_response.get('access_token')
                        self._authenticated = True
                        
                        logger.info(f"Successfully obtained Shopify access token for shop: {self.shop_name}")
                        return token_response
                    else:
                        error_data = await response.json()
                        raise ShopifyAuthenticationError(
                            f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}",
                            details={'response': error_data}
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during token exchange: {str(e)}")
            raise ShopifyAuthenticationError(f"Token exchange network error: {str(e)}")
        except Exception as e:
            logger.error(f"Token exchange failed: {str(e)}")
            raise create_shopify_exception(e, {'shop_name': self.shop_name})
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers for Shopify API requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-Shopify-Connector/1.0'
        }
        
        if self.access_token:
            headers['X-Shopify-Access-Token'] = self.access_token
        
        return headers
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """
        Verify Shopify webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: X-Shopify-Hmac-Sha256 header value
            secret: Webhook secret (uses configured secret if not provided)
            
        Returns:
            bool: True if signature is valid
        """
        try:
            webhook_secret = secret or self.webhook_secret
            if not webhook_secret:
                logger.warning("No webhook secret configured for signature verification")
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).digest()
            
            # Base64 encode the signature
            expected_signature_b64 = base64.b64encode(expected_signature).decode('utf-8')
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature_b64, signature)
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature for shop: {self.shop_name}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            return False
    
    def verify_app_proxy_signature(
        self,
        query_string: str,
        signature: str
    ) -> bool:
        """
        Verify Shopify app proxy signature.
        
        Args:
            query_string: Query string from app proxy request
            signature: Signature from query parameters
            
        Returns:
            bool: True if signature is valid
        """
        try:
            if not self.api_secret:
                logger.warning("No API secret configured for app proxy verification")
                return False
            
            # Parse and sort query parameters
            query_params = parse_qs(query_string)
            
            # Remove signature from params
            if 'signature' in query_params:
                del query_params['signature']
            
            # Sort parameters and create query string
            sorted_params = []
            for key in sorted(query_params.keys()):
                for value in query_params[key]:
                    sorted_params.append(f"{key}={value}")
            
            query_string_for_signing = '&'.join(sorted_params)
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.api_secret.encode('utf-8'),
                query_string_for_signing.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if not is_valid:
                logger.warning(f"Invalid app proxy signature for shop: {self.shop_name}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"App proxy signature verification failed: {str(e)}")
            return False
    
    async def validate_credentials(self) -> bool:
        """
        Validate current credentials.
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            if not self._authenticated:
                return await self.authenticate()
            
            # Test current token
            return await self._test_api_access()
            
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False
    
    def _update_shop_info(self, shop_data: Dict[str, Any]) -> None:
        """Update shop information from API response."""
        self.shop_info = {
            'id': shop_data.get('id'),
            'name': shop_data.get('name'),
            'email': shop_data.get('email'),
            'domain': shop_data.get('domain'),
            'country': shop_data.get('country'),
            'currency': shop_data.get('currency'),
            'timezone': shop_data.get('iana_timezone'),
            'plan_name': shop_data.get('plan_name'),
            'plan_display_name': shop_data.get('plan_display_name')
        }
        
        logger.info(f"Updated shop info for: {shop_data.get('name')}")
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._authenticated = False
        self.access_token = None
        self._token_expires_at = None
        logger.info("Cleaned up Shopify authentication resources")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated and bool(self.access_token)
    
    @property
    def api_headers(self) -> Dict[str, str]:
        """Get API headers for requests."""
        return self._get_api_headers()
    
    @property
    def shop_url(self) -> Optional[str]:
        """Get shop URL."""
        return self.base_url
    
    @property
    def api_url(self) -> Optional[str]:
        """Get API base URL."""
        return self.api_base_url