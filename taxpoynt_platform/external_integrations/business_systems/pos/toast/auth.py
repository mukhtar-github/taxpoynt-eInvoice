"""
Toast POS Authentication Module
Handles OAuth 2.0 authentication and API access management for Toast POS integration.
Supports both Toast production and sandbox environments with comprehensive token management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import aiohttp
import base64
from urllib.parse import urlencode

from ....framework.models.pos_models import ConnectionConfig
from ....shared.utils.encryption_utils import EncryptionUtils
from ....shared.utils.cache_utils import CacheUtils
from .exceptions import ToastAuthenticationError, ToastAPIError

logger = logging.getLogger(__name__)


class ToastAuthManager:
    """
    Toast POS Authentication Manager
    
    Handles OAuth 2.0 authentication flow, token management, and API access
    for Toast POS systems with support for multiple restaurant locations.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Toast authentication manager.
        
        Args:
            config: Connection configuration with Toast credentials
        """
        self.config = config
        self.encryption = EncryptionUtils()
        self.cache = CacheUtils()
        
        # Extract credentials
        credentials = config.credentials or {}
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.environment = credentials.get('environment', 'sandbox')
        
        if not self.client_id or not self.client_secret:
            raise ToastAuthenticationError("Toast client_id and client_secret are required")
        
        # Toast API endpoints
        self.base_urls = {
            'sandbox': 'https://ws-sandbox-api.toasttab.com',
            'production': 'https://ws-api.toasttab.com'
        }
        
        self.oauth_urls = {
            'sandbox': 'https://ws-sandbox-api.toasttab.com/authentication/v1/authentication/login',
            'production': 'https://ws-api.toasttab.com/authentication/v1/authentication/login'
        }
        
        self.base_url = self.base_urls.get(self.environment)
        self.oauth_url = self.oauth_urls.get(self.environment)
        
        if not self.base_url:
            raise ToastAuthenticationError(f"Invalid Toast environment: {self.environment}")
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Toast-specific settings
        self.auth_config = {
            'token_expiry_buffer': 300,  # 5 minutes before expiry
            'max_retries': 3,
            'retry_delay': 5,
            'session_timeout': 3600  # 1 hour session timeout
        }
        
        logger.info(f"Initialized Toast auth manager for environment: {self.environment}")
    
    async def authenticate(self) -> str:
        """
        Authenticate with Toast POS and obtain access token.
        
        Returns:
            str: Access token
            
        Raises:
            ToastAuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Toast POS...")
            
            # Check for cached token
            cached_token = await self._get_cached_token()
            if cached_token and await self._is_token_valid(cached_token):
                self._access_token = cached_token['access_token']
                self._token_expires_at = datetime.fromisoformat(cached_token['expires_at'])
                logger.info("Using cached Toast access token")
                return self._access_token
            
            # Authenticate using client credentials flow
            token_data = await self._request_access_token()
            
            # Store token
            self._access_token = token_data['token']
            # Toast tokens typically last 24 hours, but we'll be conservative
            self._token_expires_at = datetime.utcnow() + timedelta(hours=23)
            
            # Cache token
            await self._cache_token(token_data)
            
            logger.info("Successfully authenticated with Toast POS")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Toast authentication failed: {str(e)}")
            raise ToastAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def get_access_token(self) -> str:
        """
        Get valid access token, refreshing if necessary.
        
        Returns:
            str: Valid access token
        """
        if not self._access_token or await self._token_needs_refresh():
            await self.authenticate()
        
        return self._access_token
    
    async def validate_token(self) -> bool:
        """
        Validate current access token.
        
        Returns:
            bool: True if token is valid
        """
        if not self._access_token:
            return False
        
        try:
            # Test token by making a simple API call
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/config/v1/restaurants"
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False
    
    async def get_authorized_restaurants(self) -> List[Dict[str, Any]]:
        """
        Get list of restaurants this app is authorized for.
        
        Returns:
            List[Dict]: Restaurant information
        """
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/config/v1/restaurants"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        restaurants = data if isinstance(data, list) else [data]
                        logger.info(f"Retrieved {len(restaurants)} authorized Toast restaurants")
                        return restaurants
                    else:
                        error_text = await response.text()
                        raise ToastAPIError(f"Failed to get restaurants: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get authorized restaurants: {str(e)}")
            raise ToastAuthenticationError(f"Failed to get restaurants: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._access_token = None
        self._token_expires_at = None
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("Toast authentication cleanup completed")
    
    # Private methods
    
    async def _request_access_token(self) -> Dict[str, Any]:
        """Request access token from Toast OAuth endpoint."""
        auth_data = {
            'userAccessType': 'TOAST_MACHINE_CLIENT',
            'clientId': self.client_id,
            'clientSecret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.oauth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    if 'token' not in token_data:
                        raise ToastAuthenticationError("Invalid token response from Toast")
                    return token_data
                else:
                    error_text = await response.text()
                    logger.error(f"Token request failed: {response.status} - {error_text}")
                    raise ToastAuthenticationError(f"Token request failed: {error_text}")
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        token = await self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Toast-Restaurant-External-ID': self.config.restaurant_id or ''
        }
    
    async def _token_needs_refresh(self) -> bool:
        """Check if token needs refresh."""
        if not self._token_expires_at:
            return True
        
        # Refresh if token expires within buffer time
        buffer_time = timedelta(seconds=self.auth_config['token_expiry_buffer'])
        return datetime.utcnow() + buffer_time >= self._token_expires_at
    
    async def _get_cached_token(self) -> Optional[Dict[str, Any]]:
        """Get cached access token."""
        cache_key = f"toast_token_{self.client_id}_{self.environment}"
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                # Decrypt token data
                decrypted = self.encryption.decrypt(cached_data)
                return decrypted
        except Exception as e:
            logger.warning(f"Failed to get cached token: {str(e)}")
        
        return None
    
    async def _cache_token(self, token_data: Dict[str, Any]) -> None:
        """Cache access token securely."""
        cache_key = f"toast_token_{self.client_id}_{self.environment}"
        
        cache_data = {
            'access_token': token_data['token'],
            'expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
            'cached_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Encrypt token data
            encrypted_data = self.encryption.encrypt(cache_data)
            
            # Cache for 23 hours
            await self.cache.set(cache_key, encrypted_data, ttl=23 * 3600)
            logger.debug("Cached Toast access token")
            
        except Exception as e:
            logger.warning(f"Failed to cache token: {str(e)}")
    
    async def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """Check if cached token is still valid."""
        try:
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            buffer_time = timedelta(seconds=self.auth_config['token_expiry_buffer'])
            return datetime.utcnow() + buffer_time < expires_at
        except Exception:
            return False
    
    async def create_webhook_subscription(
        self,
        webhook_url: str,
        events: List[str],
        restaurant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create webhook subscription for Toast events.
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of event types to subscribe to
            restaurant_id: Specific restaurant ID (optional)
            
        Returns:
            Dict: Subscription information
        """
        try:
            headers = await self._get_auth_headers()
            
            # Override restaurant ID in headers if provided
            if restaurant_id:
                headers['Toast-Restaurant-External-ID'] = restaurant_id
            
            subscription_data = {
                'webhookURL': webhook_url,
                'eventTypes': events
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/config/v1/webhookSubscription"
                async with session.post(url, json=subscription_data, headers=headers) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"Created Toast webhook subscription: {webhook_url}")
                        return result
                    else:
                        error_text = await response.text()
                        raise ToastAPIError(f"Webhook subscription failed: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to create webhook subscription: {str(e)}")
            raise ToastAuthenticationError(f"Webhook subscription failed: {str(e)}")
    
    async def list_webhook_subscriptions(self, restaurant_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List existing webhook subscriptions.
        
        Args:
            restaurant_id: Specific restaurant ID (optional)
            
        Returns:
            List[Dict]: List of webhook subscriptions
        """
        try:
            headers = await self._get_auth_headers()
            
            if restaurant_id:
                headers['Toast-Restaurant-External-ID'] = restaurant_id
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/config/v1/webhookSubscription"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        subscriptions = await response.json()
                        logger.info(f"Retrieved {len(subscriptions)} Toast webhook subscriptions")
                        return subscriptions
                    else:
                        error_text = await response.text()
                        raise ToastAPIError(f"Failed to list subscriptions: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to list webhook subscriptions: {str(e)}")
            return []
    
    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._access_token is not None and not asyncio.create_task(self._token_needs_refresh()).done()
    
    @property
    def token_expires_at(self) -> Optional[datetime]:
        """Get token expiration time."""
        return self._token_expires_at
    
    @property
    def environment_info(self) -> Dict[str, str]:
        """Get environment information."""
        return {
            'environment': self.environment,
            'base_url': self.base_url,
            'oauth_url': self.oauth_url
        }