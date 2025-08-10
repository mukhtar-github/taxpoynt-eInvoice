"""
WooCommerce E-commerce Authentication Manager
Handles WooCommerce REST API authentication including OAuth 1.0a and API key authentication.
"""

import asyncio
import logging
import hashlib
import hmac
import base64
import secrets
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse, quote
import aiohttp

from ....framework.models.base_models import ConnectionConfig
from ....shared.exceptions.integration_exceptions import AuthenticationError
from .exceptions import (
    WooCommerceAuthenticationError,
    WooCommerceConfigurationError,
    create_woocommerce_exception
)

logger = logging.getLogger(__name__)


class WooCommerceAuthManager:
    """
    WooCommerce Authentication Manager
    
    Handles WooCommerce REST API authentication including:
    - OAuth 1.0a authentication (recommended)
    - Basic authentication with API keys
    - Webhook signature verification
    - SSL/TLS verification for secure connections
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize WooCommerce authentication manager.
        
        Args:
            config: Connection configuration with WooCommerce credentials
        """
        self.config = config
        self.credentials = config.credentials
        
        # Extract WooCommerce-specific configuration
        self.store_url = self.credentials.get('store_url', '').rstrip('/')
        self.consumer_key = self.credentials.get('consumer_key')
        self.consumer_secret = self.credentials.get('consumer_secret')
        self.webhook_secret = self.credentials.get('webhook_secret')
        self.use_oauth = self.credentials.get('use_oauth', True)
        self.api_version = self.credentials.get('api_version', 'wc/v3')
        
        # SSL configuration
        self.verify_ssl = self.credentials.get('verify_ssl', True)
        self.force_ssl = self.credentials.get('force_ssl', True)
        
        # Authentication state
        self._authenticated = False
        self._store_info: Optional[Dict[str, Any]] = None
        
        # Construct API base URL
        if self.store_url:
            # Ensure HTTPS for OAuth
            if self.use_oauth and not self.store_url.startswith('https://'):
                if self.force_ssl:
                    self.store_url = self.store_url.replace('http://', 'https://')
                else:
                    logger.warning("OAuth requires HTTPS - consider enabling force_ssl")
            
            self.api_base_url = f"{self.store_url}/wp-json/{self.api_version}"
        else:
            self.api_base_url = None
        
        logger.info(f"Initialized WooCommerce auth manager for store: {self.store_url}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with WooCommerce REST API.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            WooCommerceAuthenticationError: If authentication fails
        """
        try:
            if not self.store_url or not self.consumer_key or not self.consumer_secret:
                raise WooCommerceAuthenticationError(
                    "Store URL, consumer key, and consumer secret are required"
                )
            
            # Test authentication by making a simple API call
            success = await self._test_api_access()
            self._authenticated = success
            
            if success:
                logger.info(f"Successfully authenticated with WooCommerce store: {self.store_url}")
            
            return success
            
        except Exception as e:
            logger.error(f"WooCommerce authentication failed: {str(e)}")
            raise create_woocommerce_exception(e, {
                'store_url': self.store_url,
                'auth_type': 'oauth' if self.use_oauth else 'basic'
            })
    
    async def _test_api_access(self) -> bool:
        """Test API access with current credentials."""
        try:
            headers = await self._get_api_headers('GET', '/system_status')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/system_status",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        system_status = await response.json()
                        self._update_store_info(system_status)
                        return True
                    elif response.status == 401:
                        logger.error("Invalid WooCommerce API credentials")
                        return False
                    elif response.status == 404:
                        logger.error("WooCommerce REST API not available - check if WooCommerce is installed and REST API is enabled")
                        return False
                    else:
                        logger.error(f"API test failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"API access test failed: {str(e)}")
            return False
    
    async def _get_api_headers(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Get headers for WooCommerce API requests.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict: Headers for API request
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-WooCommerce-Connector/1.0'
        }
        
        if self.use_oauth:
            # Use OAuth 1.0a authentication
            oauth_headers = await self._generate_oauth_headers(method, endpoint, params)
            headers.update(oauth_headers)
        else:
            # Use Basic authentication
            auth_string = f"{self.consumer_key}:{self.consumer_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
            headers['Authorization'] = f'Basic {auth_b64}'
        
        return headers
    
    async def _generate_oauth_headers(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Generate OAuth 1.0a headers for WooCommerce API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Dict: OAuth headers
        """
        # OAuth parameters
        oauth_params = {
            'oauth_consumer_key': self.consumer_key,
            'oauth_nonce': secrets.token_hex(16),
            'oauth_signature_method': 'HMAC-SHA256',
            'oauth_timestamp': str(int(time.time())),
            'oauth_version': '1.0'
        }
        
        # Construct full URL
        url = f"{self.api_base_url}{endpoint}"
        
        # Combine OAuth params with query params
        all_params = oauth_params.copy()
        if params:
            all_params.update(params)
        
        # Create signature base string
        param_string = '&'.join([
            f"{quote(str(k))}={quote(str(v))}"
            for k, v in sorted(all_params.items())
        ])
        
        base_string = f"{method.upper()}&{quote(url)}&{quote(param_string)}"
        
        # Create signing key
        signing_key = f"{quote(self.consumer_secret)}&"  # No token secret for two-legged OAuth
        
        # Generate signature
        signature = hmac.new(
            signing_key.encode('utf-8'),
            base_string.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        oauth_signature = base64.b64encode(signature).decode('utf-8')
        oauth_params['oauth_signature'] = oauth_signature
        
        # Create authorization header
        oauth_header_params = [
            f'{quote(str(k))}="{quote(str(v))}"'
            for k, v in sorted(oauth_params.items())
        ]
        
        oauth_header = f"OAuth {', '.join(oauth_header_params)}"
        
        return {'Authorization': oauth_header}
    
    def verify_webhook_signature(
        self,
        payload: str,
        signature: str,
        secret: Optional[str] = None
    ) -> bool:
        """
        Verify WooCommerce webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: X-WC-Webhook-Signature header value
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
            expected_signature = base64.b64encode(
                hmac.new(
                    webhook_secret.encode('utf-8'),
                    payload.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if not is_valid:
                logger.warning(f"Invalid webhook signature for store: {self.store_url}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
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
            
            # Test current credentials
            return await self._test_api_access()
            
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False
    
    def _update_store_info(self, system_status: Dict[str, Any]) -> None:
        """Update store information from API response."""
        environment = system_status.get('environment', {})
        
        self._store_info = {
            'home_url': environment.get('home_url'),
            'site_url': environment.get('site_url'),
            'wp_version': environment.get('wp_version'),
            'wc_version': environment.get('wc_version'),
            'rest_api_version': environment.get('wc_rest_api_version'),
            'theme': environment.get('theme', {}).get('name'),
            'active_plugins': environment.get('active_plugins', []),
            'settings': {
                'api_enabled': environment.get('settings', {}).get('api_enabled'),
                'force_ssl': environment.get('settings', {}).get('force_ssl'),
                'currency': environment.get('settings', {}).get('currency'),
                'currency_symbol': environment.get('settings', {}).get('currency_symbol'),
                'currency_position': environment.get('settings', {}).get('currency_position'),
                'thousand_separator': environment.get('settings', {}).get('thousand_separator'),
                'decimal_separator': environment.get('settings', {}).get('decimal_separator'),
                'number_of_decimals': environment.get('settings', {}).get('number_of_decimals')
            }
        }
        
        logger.info(f"Updated store info - WC: {self._store_info.get('wc_version')}, WP: {self._store_info.get('wp_version')}")
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store information.
        
        Returns:
            Dict: Store information
        """
        if not self._store_info:
            await self._test_api_access()
        
        return self._store_info or {}
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._authenticated = False
        self._store_info = None
        logger.info("Cleaned up WooCommerce authentication resources")
    
    def get_query_params(self, additional_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get query parameters for API requests (when not using OAuth).
        
        Args:
            additional_params: Additional query parameters
            
        Returns:
            Dict: Query parameters including authentication
        """
        params = additional_params or {}
        
        if not self.use_oauth:
            # Add consumer key and secret as query parameters
            params.update({
                'consumer_key': self.consumer_key,
                'consumer_secret': self.consumer_secret
            })
        
        return params
    
    def construct_api_url(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> str:
        """
        Construct full API URL with authentication parameters.
        
        Args:
            endpoint: API endpoint
            params: Additional query parameters
            
        Returns:
            str: Full API URL
        """
        base_url = f"{self.api_base_url}{endpoint}"
        
        if not self.use_oauth and (self.consumer_key and self.consumer_secret):
            # Add authentication parameters
            auth_params = {
                'consumer_key': self.consumer_key,
                'consumer_secret': self.consumer_secret
            }
            
            if params:
                auth_params.update(params)
            
            query_string = urlencode(auth_params)
            return f"{base_url}?{query_string}"
        elif params:
            query_string = urlencode(params)
            return f"{base_url}?{query_string}"
        
        return base_url
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated and bool(self.consumer_key and self.consumer_secret)
    
    @property
    def api_headers_method(self):
        """Get method to generate API headers."""
        return self._get_api_headers
    
    @property
    def store_base_url(self) -> Optional[str]:
        """Get store base URL."""
        return self.store_url
    
    @property
    def api_url(self) -> Optional[str]:
        """Get API base URL."""
        return self.api_base_url
    
    @property
    def uses_oauth(self) -> bool:
        """Check if using OAuth authentication."""
        return self.use_oauth
    
    @property
    def ssl_verification(self) -> bool:
        """Check if SSL verification is enabled."""
        return self.verify_ssl