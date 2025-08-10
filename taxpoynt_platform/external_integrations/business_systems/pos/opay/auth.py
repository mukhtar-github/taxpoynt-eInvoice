"""
OPay POS Authentication Module
Handles authentication and API access management for OPay POS integration.
Supports OPay's API authentication with Nigerian mobile money and payment systems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
import aiohttp
import hashlib
import hmac
import json
from urllib.parse import urlencode

from ....framework.models.pos_models import ConnectionConfig
from ....shared.utils.encryption_utils import EncryptionUtils
from ....shared.utils.cache_utils import CacheUtils
from .exceptions import OPayAuthenticationError, OPayAPIError

logger = logging.getLogger(__name__)


class OPayAuthManager:
    """
    OPay POS Authentication Manager
    
    Handles API key authentication, token management, and Nigerian mobile money
    compliance for OPay POS systems including wallet and payment processing.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize OPay authentication manager.
        
        Args:
            config: Connection configuration with OPay credentials
        """
        self.config = config
        self.encryption = EncryptionUtils()
        self.cache = CacheUtils()
        
        # Extract credentials
        credentials = config.credentials or {}
        self.public_key = credentials.get('public_key')
        self.private_key = credentials.get('private_key')
        self.merchant_id = credentials.get('merchant_id')
        self.environment = credentials.get('environment', 'sandbox')
        
        if not all([self.public_key, self.private_key, self.merchant_id]):
            raise OPayAuthenticationError("OPay public_key, private_key, and merchant_id are required")
        
        # OPay API endpoints
        self.base_urls = {
            'sandbox': 'https://sandboxapi.opayweb.com',
            'production': 'https://liveapi.opayweb.com'
        }
        
        self.base_url = self.base_urls.get(self.environment)
        if not self.base_url:
            raise OPayAuthenticationError(f"Invalid OPay environment: {self.environment}")
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # OPay-specific settings
        self.auth_config = {
            'signature_algorithm': 'SHA512',
            'max_retries': 3,
            'retry_delay': 5,
            'session_timeout': 3600,  # 1 hour session timeout
            'api_version': 'v3'
        }
        
        logger.info(f"Initialized OPay auth manager for environment: {self.environment}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with OPay POS system.
        OPay uses signature-based authentication without tokens.
        
        Returns:
            bool: True if authentication setup is valid
            
        Raises:
            OPayAuthenticationError: If authentication fails
        """
        try:
            logger.info("Validating OPay POS authentication...")
            
            # Test authentication by making a simple API call
            test_result = await self._test_authentication()
            
            if test_result:
                logger.info("Successfully validated OPay POS authentication")
                return True
            else:
                raise OPayAuthenticationError("OPay authentication validation failed")
                
        except Exception as e:
            logger.error(f"OPay authentication failed: {str(e)}")
            raise OPayAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def get_auth_headers(self, request_body: str = "", endpoint: str = "") -> Dict[str, str]:
        """
        Get authentication headers for OPay API requests.
        
        Args:
            request_body: JSON request body as string
            endpoint: API endpoint path
            
        Returns:
            Dict: Authentication headers
        """
        timestamp = str(int(datetime.utcnow().timestamp() * 1000))
        nonce = self._generate_nonce()
        
        # Create signature
        signature = self._create_signature(request_body, timestamp, nonce, endpoint)
        
        return {
            'Authorization': f'Bearer {self.public_key}',
            'MerchantId': self.merchant_id,
            'Timestamp': timestamp,
            'Nonce': nonce,
            'Signature': signature,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    async def validate_credentials(self) -> bool:
        """
        Validate current credentials.
        
        Returns:
            bool: True if credentials are valid
        """
        try:
            # Test credentials by calling merchant info endpoint
            return await self._test_authentication()
        except Exception as e:
            logger.error(f"Credential validation failed: {str(e)}")
            return False
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information from OPay.
        
        Returns:
            Dict: Merchant information
        """
        try:
            endpoint = f"/api/{self.auth_config['api_version']}/merchant/info"
            headers = await self.get_auth_headers("", endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '00000':  # OPay success code
                            merchant_info = data.get('data', {})
                            logger.info("Retrieved OPay merchant information")
                            return merchant_info
                        else:
                            raise OPayAPIError(f"OPay API error: {data.get('message', 'Unknown error')}")
                    else:
                        error_text = await response.text()
                        raise OPayAPIError(f"Failed to get merchant info: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get merchant information: {str(e)}")
            raise OPayAuthenticationError(f"Failed to get merchant info: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._access_token = None
        self._token_expires_at = None
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("OPay authentication cleanup completed")
    
    # Private methods
    
    def _create_signature(self, body: str, timestamp: str, nonce: str, endpoint: str) -> str:
        """Create HMAC signature for OPay API requests."""
        # OPay signature format: privateKey+body+timestamp+nonce
        message = f"{self.private_key}{body}{timestamp}{nonce}"
        
        signature = hmac.new(
            self.private_key.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest().upper()
        
        return signature
    
    def _generate_nonce(self) -> str:
        """Generate a unique nonce for request."""
        import uuid
        return str(uuid.uuid4()).replace('-', '')
    
    async def _test_authentication(self) -> bool:
        """Test authentication by making a simple API call."""
        try:
            # Test with a simple balance inquiry or merchant info call
            endpoint = f"/api/{self.auth_config['api_version']}/merchant/balance"
            headers = await self.get_auth_headers("", endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == '00000'  # OPay success code
                    elif response.status == 401:
                        return False  # Authentication failed
                    else:
                        # Other errors might still indicate valid auth but other issues
                        return response.status != 403
                        
        except Exception as e:
            logger.error(f"Authentication test failed: {str(e)}")
            return False
    
    def create_webhook_signature(
        self,
        payload: str,
        timestamp: str
    ) -> str:
        """
        Create webhook signature for validating OPay webhook requests.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            
        Returns:
            str: HMAC signature
        """
        message = f"{self.private_key}{payload}{timestamp}"
        signature = hmac.new(
            self.private_key.encode(),
            message.encode(),
            hashlib.sha512
        ).hexdigest().upper()
        
        return signature
    
    def validate_webhook_signature(
        self,
        payload: str,
        timestamp: str,
        received_signature: str
    ) -> bool:
        """
        Validate OPay webhook signature.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            received_signature: Signature from webhook headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self.create_webhook_signature(payload, timestamp)
            return hmac.compare_digest(expected_signature.upper(), received_signature.upper())
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
            endpoint = f"/api/{self.auth_config['api_version']}/banks"
            headers = await self.get_auth_headers("", endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '00000':
                            banks = data.get('data', [])
                            logger.info(f"Retrieved {len(banks)} supported banks")
                            return banks
                        else:
                            raise OPayAPIError(f"Failed to get banks: {data.get('message')}")
                    else:
                        error_text = await response.text()
                        raise OPayAPIError(f"Failed to get banks: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get supported banks: {str(e)}")
            return []
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get OPay wallet balance.
        
        Returns:
            Dict: Wallet balance information
        """
        try:
            endpoint = f"/api/{self.auth_config['api_version']}/merchant/balance"
            headers = await self.get_auth_headers("", endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '00000':
                            balance_info = data.get('data', {})
                            logger.info("Retrieved OPay wallet balance")
                            return balance_info
                        else:
                            raise OPayAPIError(f"Failed to get balance: {data.get('message')}")
                    else:
                        error_text = await response.text()
                        raise OPayAPIError(f"Failed to get balance: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            return {}
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authentication is configured."""
        return all([self.public_key, self.private_key, self.merchant_id])
    
    @property
    def environment_info(self) -> Dict[str, str]:
        """Get environment information."""
        return {
            'environment': self.environment,
            'base_url': self.base_url,
            'merchant_id': self.merchant_id,
            'api_version': self.auth_config['api_version']
        }