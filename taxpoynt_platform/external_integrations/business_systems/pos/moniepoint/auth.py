"""
Moniepoint POS Authentication Module
Handles authentication and API access management for Moniepoint POS integration.
Supports Moniepoint's API authentication with Nigerian banking compliance.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import aiohttp
import hashlib
import hmac
import base64
import json
from urllib.parse import urlencode

from ....framework.models.pos_models import ConnectionConfig
from ....shared.utils.encryption_utils import EncryptionUtils
from ....shared.utils.cache_utils import CacheUtils
from .exceptions import MoniepointAuthenticationError, MoniepointAPIError

logger = logging.getLogger(__name__)


class MoniepointAuthManager:
    """
    Moniepoint POS Authentication Manager
    
    Handles API key authentication, token management, and Nigerian banking
    compliance for Moniepoint POS systems.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Moniepoint authentication manager.
        
        Args:
            config: Connection configuration with Moniepoint credentials
        """
        self.config = config
        self.encryption = EncryptionUtils()
        self.cache = CacheUtils()
        
        # Extract credentials
        credentials = config.credentials or {}
        self.api_key = credentials.get('api_key')
        self.secret_key = credentials.get('secret_key')
        self.merchant_id = credentials.get('merchant_id')
        self.terminal_id = credentials.get('terminal_id')
        self.environment = credentials.get('environment', 'sandbox')
        
        if not all([self.api_key, self.secret_key, self.merchant_id]):
            raise MoniepointAuthenticationError("Moniepoint api_key, secret_key, and merchant_id are required")
        
        # Moniepoint API endpoints
        self.base_urls = {
            'sandbox': 'https://sandbox.monnify.com',
            'production': 'https://api.monnify.com'
        }
        
        self.auth_urls = {
            'sandbox': 'https://sandbox.monnify.com/api/v1/auth/login',
            'production': 'https://api.monnify.com/api/v1/auth/login'
        }
        
        self.base_url = self.base_urls.get(self.environment)
        self.auth_url = self.auth_urls.get(self.environment)
        
        if not self.base_url:
            raise MoniepointAuthenticationError(f"Invalid Moniepoint environment: {self.environment}")
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Moniepoint-specific settings
        self.auth_config = {
            'token_expiry_buffer': 300,  # 5 minutes before expiry
            'max_retries': 3,
            'retry_delay': 5,
            'session_timeout': 3600,  # 1 hour session timeout
            'signature_algorithm': 'SHA512'
        }
        
        logger.info(f"Initialized Moniepoint auth manager for environment: {self.environment}")
    
    async def authenticate(self) -> str:
        """
        Authenticate with Moniepoint POS and obtain access token.
        
        Returns:
            str: Access token
            
        Raises:
            MoniepointAuthenticationError: If authentication fails
        """
        try:
            logger.info("Authenticating with Moniepoint POS...")
            
            # Check for cached token
            cached_token = await self._get_cached_token()
            if cached_token and await self._is_token_valid(cached_token):
                self._access_token = cached_token['access_token']
                self._token_expires_at = datetime.fromisoformat(cached_token['expires_at'])
                logger.info("Using cached Moniepoint access token")
                return self._access_token
            
            # Authenticate using API key and secret
            token_data = await self._request_access_token()
            
            # Store token
            self._access_token = token_data['responseBody']['accessToken']
            # Moniepoint tokens typically expire in 1 hour
            expires_in = token_data['responseBody'].get('expiresIn', 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            # Cache token
            await self._cache_token(token_data)
            
            logger.info("Successfully authenticated with Moniepoint POS")
            return self._access_token
            
        except Exception as e:
            logger.error(f"Moniepoint authentication failed: {str(e)}")
            raise MoniepointAuthenticationError(f"Authentication failed: {str(e)}")
    
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
                url = f"{self.base_url}/api/v1/merchant/transactions"
                async with session.get(url, headers=headers) as response:
                    return response.status in [200, 404]  # 404 is okay for empty results
                    
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            return False
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information from Moniepoint.
        
        Returns:
            Dict: Merchant information
        """
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v1/merchant/{self.merchant_id}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        merchant_info = data.get('responseBody', {})
                        logger.info("Retrieved Moniepoint merchant information")
                        return merchant_info
                    else:
                        error_text = await response.text()
                        raise MoniepointAPIError(f"Failed to get merchant info: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get merchant information: {str(e)}")
            raise MoniepointAuthenticationError(f"Failed to get merchant info: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._access_token = None
        self._token_expires_at = None
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("Moniepoint authentication cleanup completed")
    
    # Private methods
    
    async def _request_access_token(self) -> Dict[str, Any]:
        """Request access token from Moniepoint OAuth endpoint."""
        # Create basic auth header
        credentials = f"{self.api_key}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Empty body for basic auth
        auth_data = {}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.auth_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    if 'responseBody' not in token_data or 'accessToken' not in token_data['responseBody']:
                        raise MoniepointAuthenticationError("Invalid token response from Moniepoint")
                    return token_data
                else:
                    error_text = await response.text()
                    logger.error(f"Token request failed: {response.status} - {error_text}")
                    raise MoniepointAuthenticationError(f"Token request failed: {error_text}")
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        token = await self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _create_signature(self, payload: str, timestamp: str) -> str:
        """Create HMAC signature for Moniepoint API requests."""
        message = f"{timestamp}{payload}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest()
        return signature
    
    async def _token_needs_refresh(self) -> bool:
        """Check if token needs refresh."""
        if not self._token_expires_at:
            return True
        
        # Refresh if token expires within buffer time
        buffer_time = timedelta(seconds=self.auth_config['token_expiry_buffer'])
        return datetime.utcnow() + buffer_time >= self._token_expires_at
    
    async def _get_cached_token(self) -> Optional[Dict[str, Any]]:
        """Get cached access token."""
        cache_key = f"moniepoint_token_{self.api_key}_{self.environment}"
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
        cache_key = f"moniepoint_token_{self.api_key}_{self.environment}"
        
        cache_data = {
            'access_token': token_data['responseBody']['accessToken'],
            'expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None,
            'cached_at': datetime.utcnow().isoformat()
        }
        
        try:
            # Encrypt token data
            encrypted_data = self.encryption.encrypt(cache_data)
            
            # Cache for token expiry time
            ttl = (self._token_expires_at - datetime.utcnow()).total_seconds() if self._token_expires_at else 3600
            await self.cache.set(cache_key, encrypted_data, ttl=int(ttl))
            logger.debug("Cached Moniepoint access token")
            
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
    
    def create_webhook_signature(
        self,
        payload: str,
        timestamp: str
    ) -> str:
        """
        Create webhook signature for validating Moniepoint webhook requests.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            
        Returns:
            str: HMAC signature
        """
        return self._create_signature(payload, timestamp)
    
    def validate_webhook_signature(
        self,
        payload: str,
        timestamp: str,
        received_signature: str
    ) -> bool:
        """
        Validate Moniepoint webhook signature.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            received_signature: Signature from webhook headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self.create_webhook_signature(payload, timestamp)
            return hmac.compare_digest(expected_signature, received_signature)
        except Exception as e:
            logger.error(f"Webhook signature validation failed: {str(e)}")
            return False
    
    async def get_supported_banks(self) -> List[Dict[str, Any]]:
        """
        Get list of supported banks for transfers.
        
        Returns:
            List[Dict]: List of supported banks
        """
        try:
            headers = await self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/api/v1/sdk/transactions/banks"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        banks = data.get('responseBody', [])
                        logger.info(f"Retrieved {len(banks)} supported banks")
                        return banks
                    else:
                        error_text = await response.text()
                        raise MoniepointAPIError(f"Failed to get banks: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get supported banks: {str(e)}")
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
            'auth_url': self.auth_url,
            'merchant_id': self.merchant_id,
            'terminal_id': self.terminal_id
        }