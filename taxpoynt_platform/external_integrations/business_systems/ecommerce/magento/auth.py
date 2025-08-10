"""
Magento E-commerce Authentication Manager
Handles Magento REST API authentication including Bearer token and Integration token authentication.
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
    MagentoAuthenticationError,
    MagentoConfigurationError,
    create_magento_exception
)

logger = logging.getLogger(__name__)


class MagentoAuthManager:
    """
    Magento Authentication Manager
    
    Handles Magento REST API authentication including:
    - Bearer token authentication (admin user tokens)
    - Integration token authentication (recommended)
    - Customer token authentication (for customer-specific operations)
    - Multi-store view authentication
    - JWT token management and refresh
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Magento authentication manager.
        
        Args:
            config: Connection configuration with Magento credentials
        """
        self.config = config
        self.credentials = config.credentials
        
        # Extract Magento-specific configuration
        self.store_url = self.credentials.get('store_url', '').rstrip('/')
        self.access_token = self.credentials.get('access_token')
        self.integration_token = self.credentials.get('integration_token')
        self.username = self.credentials.get('username')
        self.password = self.credentials.get('password')
        self.auth_type = self.credentials.get('auth_type', 'integration')  # 'integration', 'admin', 'customer'
        self.api_version = self.credentials.get('api_version', 'V1')
        
        # Store view configuration
        self.store_code = self.credentials.get('store_code', 'default')
        self.store_view_id = self.credentials.get('store_view_id')
        self.website_id = self.credentials.get('website_id')
        
        # SSL configuration
        self.verify_ssl = self.credentials.get('verify_ssl', True)
        
        # Authentication state
        self._authenticated = False
        self._token_expires_at: Optional[datetime] = None
        self._store_info: Optional[Dict[str, Any]] = None
        
        # Construct API base URL
        if self.store_url:
            # Ensure HTTPS for token authentication
            if not self.store_url.startswith('https://'):
                self.store_url = self.store_url.replace('http://', 'https://')
                logger.warning("Forcing HTTPS for Magento token authentication")
            
            # Construct API URL with store code if specified
            if self.store_code and self.store_code != 'default':
                self.api_base_url = f"{self.store_url}/rest/{self.store_code}/{self.api_version}"
            else:
                self.api_base_url = f"{self.store_url}/rest/default/{self.api_version}"
        else:
            self.api_base_url = None
        
        logger.info(f"Initialized Magento auth manager for store: {self.store_url} (store: {self.store_code})")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Magento REST API.
        
        Returns:
            bool: True if authentication successful
            
        Raises:
            MagentoAuthenticationError: If authentication fails
        """
        try:
            if not self.store_url:
                raise MagentoAuthenticationError("Store URL is required for authentication")
            
            if self.auth_type == 'integration':
                # Use integration token (recommended approach)
                success = await self._authenticate_integration()
            elif self.auth_type == 'admin':
                # Use admin username/password to get bearer token
                success = await self._authenticate_admin()
            elif self.auth_type == 'customer':
                # Use customer credentials
                success = await self._authenticate_customer()
            else:
                raise MagentoAuthenticationError(f"Unsupported auth type: {self.auth_type}")
            
            self._authenticated = success
            
            if success:
                logger.info(f"Successfully authenticated with Magento store: {self.store_url}")
            
            return success
            
        except Exception as e:
            logger.error(f"Magento authentication failed: {str(e)}")
            raise create_magento_exception(e, {
                'store_url': self.store_url,
                'auth_type': self.auth_type
            })
    
    async def _authenticate_integration(self) -> bool:
        """Authenticate using integration token."""
        if not self.integration_token:
            raise MagentoAuthenticationError("Integration token required for integration authentication")
        
        # Integration tokens don't need exchange, test by making API call
        return await self._test_api_access()
    
    async def _authenticate_admin(self) -> bool:
        """Authenticate using admin username/password to get bearer token."""
        if not self.username or not self.password:
            raise MagentoAuthenticationError("Username and password required for admin authentication")
        
        try:
            # Get admin token
            token_data = {
                'username': self.username,
                'password': self.password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/integration/admin/token",
                    json=token_data,
                    headers={'Content-Type': 'application/json'},
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        # Magento returns the token as a plain string
                        token = await response.text()
                        # Remove quotes if present
                        self.access_token = token.strip('"')
                        
                        # Set token expiration (Magento admin tokens expire in 4 hours by default)
                        self._token_expires_at = datetime.utcnow() + timedelta(hours=4)
                        
                        logger.info(f"Successfully obtained Magento admin token")
                        return True
                    else:
                        error_data = await response.json()
                        raise MagentoAuthenticationError(
                            f"Admin token request failed: {error_data.get('message', 'Unknown error')}",
                            details={'response': error_data}
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during admin authentication: {str(e)}")
            raise MagentoAuthenticationError(f"Admin authentication network error: {str(e)}")
        except Exception as e:
            logger.error(f"Admin authentication failed: {str(e)}")
            raise create_magento_exception(e, {'store_url': self.store_url})
    
    async def _authenticate_customer(self) -> bool:
        """Authenticate using customer credentials."""
        if not self.username or not self.password:
            raise MagentoAuthenticationError("Username and password required for customer authentication")
        
        try:
            # Get customer token
            token_data = {
                'username': self.username,
                'password': self.password
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/integration/customer/token",
                    json=token_data,
                    headers={'Content-Type': 'application/json'},
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        # Magento returns the token as a plain string
                        token = await response.text()
                        # Remove quotes if present
                        self.access_token = token.strip('"')
                        
                        # Set token expiration (Magento customer tokens expire in 1 hour by default)
                        self._token_expires_at = datetime.utcnow() + timedelta(hours=1)
                        
                        logger.info(f"Successfully obtained Magento customer token")
                        return True
                    else:
                        error_data = await response.json()
                        raise MagentoAuthenticationError(
                            f"Customer token request failed: {error_data.get('message', 'Unknown error')}",
                            details={'response': error_data}
                        )
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error during customer authentication: {str(e)}")
            raise MagentoAuthenticationError(f"Customer authentication network error: {str(e)}")
        except Exception as e:
            logger.error(f"Customer authentication failed: {str(e)}")
            raise create_magento_exception(e, {'store_url': self.store_url})
    
    async def _test_api_access(self) -> bool:
        """Test API access with current token."""
        try:
            headers = self._get_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/store/storeConfigs",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        store_configs = await response.json()
                        self._update_store_info(store_configs)
                        return True
                    elif response.status == 401:
                        logger.error("Invalid or expired Magento access token")
                        return False
                    else:
                        logger.error(f"API test failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"API access test failed: {str(e)}")
            return False
    
    def _get_api_headers(self) -> Dict[str, str]:
        """Get headers for Magento API requests."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-Magento-Connector/1.0'
        }
        
        # Add authorization header based on auth type
        if self.auth_type == 'integration' and self.integration_token:
            headers['Authorization'] = f'Bearer {self.integration_token}'
        elif self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers
    
    async def refresh_token_if_needed(self) -> bool:
        """
        Refresh access token if it's expired or about to expire.
        
        Returns:
            bool: True if token is valid or successfully refreshed
        """
        # Integration tokens don't expire, no refresh needed
        if self.auth_type == 'integration':
            return True
        
        # Check if token needs refresh
        if self._token_expires_at:
            # Refresh if token expires in less than 5 minutes
            refresh_threshold = datetime.utcnow() + timedelta(minutes=5)
            if self._token_expires_at <= refresh_threshold:
                logger.info("Refreshing Magento access token")
                return await self.authenticate()
        
        return True
    
    async def validate_credentials(self) -> bool:
        """
        Validate current credentials.
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            if not self._authenticated:
                return await self.authenticate()
            
            # Refresh token if needed
            await self.refresh_token_if_needed()
            
            # Test current token
            return await self._test_api_access()
            
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False
    
    def _update_store_info(self, store_configs: List[Dict[str, Any]]) -> None:
        """Update store information from API response."""
        if not store_configs:
            return
        
        # Use the first store config or find matching store code
        store_config = store_configs[0]
        for config in store_configs:
            if config.get('code') == self.store_code:
                store_config = config
                break
        
        self._store_info = {
            'id': store_config.get('id'),
            'code': store_config.get('code'),
            'name': store_config.get('name'),
            'website_id': store_config.get('website_id'),
            'store_group_id': store_config.get('store_group_id'),
            'is_active': store_config.get('is_active'),
            'extension_attributes': store_config.get('extension_attributes', {}),
            'base_currency_code': store_config.get('base_currency_code'),
            'default_display_currency_code': store_config.get('default_display_currency_code'),
            'timezone': store_config.get('timezone'),
            'weight_unit': store_config.get('weight_unit'),
            'base_url': store_config.get('base_url'),
            'base_link_url': store_config.get('base_link_url'),
            'base_static_url': store_config.get('base_static_url'),
            'base_media_url': store_config.get('base_media_url'),
            'secure_base_url': store_config.get('secure_base_url'),
            'secure_base_link_url': store_config.get('secure_base_link_url'),
            'secure_base_static_url': store_config.get('secure_base_static_url'),
            'secure_base_media_url': store_config.get('secure_base_media_url')
        }
        
        logger.info(f"Updated store info for: {store_config.get('name')} (code: {store_config.get('code')})")
    
    async def get_store_info(self) -> Dict[str, Any]:
        """
        Get store information.
        
        Returns:
            Dict: Store information
        """
        if not self._store_info:
            await self._test_api_access()
        
        return self._store_info or {}
    
    async def get_store_views(self) -> List[Dict[str, Any]]:
        """
        Get all store views.
        
        Returns:
            List[Dict]: List of store views
        """
        try:
            headers = self._get_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/store/storeViews",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        store_views = await response.json()
                        logger.info(f"Retrieved {len(store_views)} store views")
                        return store_views
                    else:
                        logger.error(f"Failed to get store views: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to get store views: {str(e)}")
            return []
    
    async def get_websites(self) -> List[Dict[str, Any]]:
        """
        Get all websites.
        
        Returns:
            List[Dict]: List of websites
        """
        try:
            headers = self._get_api_headers()
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_base_url}/store/websites",
                    headers=headers,
                    ssl=self.verify_ssl,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        websites = await response.json()
                        logger.info(f"Retrieved {len(websites)} websites")
                        return websites
                    else:
                        logger.error(f"Failed to get websites: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Failed to get websites: {str(e)}")
            return []
    
    def get_store_specific_url(self, endpoint: str, store_code: Optional[str] = None) -> str:
        """
        Get store-specific API URL.
        
        Args:
            endpoint: API endpoint
            store_code: Specific store code (uses default if not provided)
            
        Returns:
            str: Store-specific API URL
        """
        target_store = store_code or self.store_code
        
        if target_store and target_store != 'default':
            base_url = f"{self.store_url}/rest/{target_store}/{self.api_version}"
        else:
            base_url = f"{self.store_url}/rest/default/{self.api_version}"
        
        return f"{base_url}{endpoint}"
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._authenticated = False
        self.access_token = None
        self._token_expires_at = None
        self._store_info = None
        logger.info("Cleaned up Magento authentication resources")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if self.auth_type == 'integration':
            return self._authenticated and bool(self.integration_token)
        else:
            return self._authenticated and bool(self.access_token)
    
    @property
    def api_headers(self) -> Dict[str, str]:
        """Get API headers for requests."""
        return self._get_api_headers()
    
    @property
    def store_base_url(self) -> Optional[str]:
        """Get store base URL."""
        return self.store_url
    
    @property
    def api_url(self) -> Optional[str]:
        """Get API base URL."""
        return self.api_base_url
    
    @property
    def current_store_code(self) -> str:
        """Get current store code."""
        return self.store_code
    
    @property
    def uses_integration_token(self) -> bool:
        """Check if using integration token authentication."""
        return self.auth_type == 'integration'
    
    @property
    def ssl_verification(self) -> bool:
        """Check if SSL verification is enabled."""
        return self.verify_ssl
    
    @property
    def token_expires_at(self) -> Optional[datetime]:
        """Get token expiration time."""
        return self._token_expires_at