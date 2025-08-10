"""
PalmPay POS Authentication Module
Handles authentication and API access management for PalmPay POS integration.
Supports PalmPay's API authentication with Nigerian mobile payment systems.
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
from .exceptions import PalmPayAuthenticationError, PalmPayAPIError

logger = logging.getLogger(__name__)


class PalmPayAuthManager:
    """
    PalmPay POS Authentication Manager
    
    Handles API key authentication, token management, and Nigerian mobile payment
    compliance for PalmPay POS systems including mobile money and agent services.
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize PalmPay authentication manager.
        
        Args:
            config: Connection configuration with PalmPay credentials
        """
        self.config = config
        self.encryption = EncryptionUtils()
        self.cache = CacheUtils()
        
        # Extract credentials
        credentials = config.credentials or {}
        self.app_id = credentials.get('app_id')
        self.app_key = credentials.get('app_key')
        self.merchant_id = credentials.get('merchant_id')
        self.terminal_id = credentials.get('terminal_id')
        self.environment = credentials.get('environment', 'sandbox')
        
        if not all([self.app_id, self.app_key, self.merchant_id]):
            raise PalmPayAuthenticationError("PalmPay app_id, app_key, and merchant_id are required")
        
        # PalmPay API endpoints
        self.base_urls = {
            'sandbox': 'https://openapi-uat.palmpay.com',
            'production': 'https://openapi.palmpay.com'
        }
        
        self.base_url = self.base_urls.get(self.environment)
        if not self.base_url:
            raise PalmPayAuthenticationError(f"Invalid PalmPay environment: {self.environment}")
        
        # Authentication state
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        
        # PalmPay-specific settings
        self.auth_config = {
            'signature_algorithm': 'SHA256',
            'max_retries': 3,
            'retry_delay': 5,
            'session_timeout': 3600,  # 1 hour session timeout
            'api_version': 'v1'
        }
        
        logger.info(f"Initialized PalmPay auth manager for environment: {self.environment}")
    
    async def authenticate(self) -> bool:
        """
        Authenticate with PalmPay POS system.
        PalmPay uses signature-based authentication without tokens.
        
        Returns:
            bool: True if authentication setup is valid
            
        Raises:
            PalmPayAuthenticationError: If authentication fails
        """
        try:
            logger.info("Validating PalmPay POS authentication...")
            
            # Test authentication by making a simple API call
            test_result = await self._test_authentication()
            
            if test_result:
                logger.info("Successfully validated PalmPay POS authentication")
                return True
            else:
                raise PalmPayAuthenticationError("PalmPay authentication validation failed")
                
        except Exception as e:
            logger.error(f"PalmPay authentication failed: {str(e)}")
            raise PalmPayAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def get_auth_headers(self, request_body: str = "", endpoint: str = "") -> Dict[str, str]:
        """
        Get authentication headers for PalmPay API requests.
        
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
            'app-id': self.app_id,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature,
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
        Get merchant information from PalmPay.
        
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
                        if data.get('code') == '200':  # PalmPay success code
                            merchant_info = data.get('data', {})
                            logger.info("Retrieved PalmPay merchant information")
                            return merchant_info
                        else:
                            raise PalmPayAPIError(f"PalmPay API error: {data.get('message', 'Unknown error')}")
                    else:
                        error_text = await response.text()
                        raise PalmPayAPIError(f"Failed to get merchant info: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get merchant information: {str(e)}")
            raise PalmPayAuthenticationError(f"Failed to get merchant info: {str(e)}")
    
    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        self._access_token = None
        self._token_expires_at = None
        
        if self._session and not self._session.closed:
            await self._session.close()
        
        logger.info("PalmPay authentication cleanup completed")
    
    # Private methods
    
    def _create_signature(self, body: str, timestamp: str, nonce: str, endpoint: str) -> str:
        """Create HMAC signature for PalmPay API requests."""
        # PalmPay signature format: app_id + timestamp + nonce + body
        message = f"{self.app_id}{timestamp}{nonce}{body}"
        
        signature = hmac.new(
            self.app_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature
    
    def _generate_nonce(self) -> str:
        """Generate a unique nonce for request."""
        import uuid
        return str(uuid.uuid4()).replace('-', '')[:16]
    
    async def _test_authentication(self) -> bool:
        """Test authentication by making a simple API call."""
        try:
            # Test with a simple balance inquiry or merchant info call
            endpoint = f"/api/{self.auth_config['api_version']}/balance/query"
            request_data = {"merchantId": self.merchant_id}
            request_body = json.dumps(request_data)
            headers = await self.get_auth_headers(request_body, endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.post(url, headers=headers, data=request_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('code') == '200'  # PalmPay success code
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
        timestamp: str,
        nonce: str
    ) -> str:
        """
        Create webhook signature for validating PalmPay webhook requests.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            nonce: Request nonce
            
        Returns:
            str: HMAC signature
        """
        message = f"{self.app_id}{timestamp}{nonce}{payload}"
        signature = hmac.new(
            self.app_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest().upper()
        
        return signature
    
    def validate_webhook_signature(
        self,
        payload: str,
        timestamp: str,
        nonce: str,
        received_signature: str
    ) -> bool:
        """
        Validate PalmPay webhook signature.
        
        Args:
            payload: Webhook payload as string
            timestamp: Request timestamp
            nonce: Request nonce
            received_signature: Signature from webhook headers
            
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self.create_webhook_signature(payload, timestamp, nonce)
            return hmac.compare_digest(expected_signature.upper(), received_signature.upper())
        except Exception as e:
            logger.error(f"Webhook signature validation failed: {str(e)}")
            return False
    
    async def get_supported_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Get list of supported payment methods.
        
        Returns:
            List[Dict]: List of supported payment methods
        """
        try:
            endpoint = f"/api/{self.auth_config['api_version']}/payment/methods"
            headers = await self.get_auth_headers("", endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '200':
                            methods = data.get('data', [])
                            logger.info(f"Retrieved {len(methods)} supported payment methods")
                            return methods
                        else:
                            raise PalmPayAPIError(f"Failed to get payment methods: {data.get('message')}")
                    else:
                        error_text = await response.text()
                        raise PalmPayAPIError(f"Failed to get payment methods: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get supported payment methods: {str(e)}")
            return []
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get PalmPay wallet balance.
        
        Returns:
            Dict: Wallet balance information
        """
        try:
            endpoint = f"/api/{self.auth_config['api_version']}/balance/query"
            request_data = {"merchantId": self.merchant_id}
            request_body = json.dumps(request_data)
            headers = await self.get_auth_headers(request_body, endpoint)
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}{endpoint}"
                async with session.post(url, headers=headers, data=request_body) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('code') == '200':
                            balance_info = data.get('data', {})
                            logger.info("Retrieved PalmPay wallet balance")
                            return balance_info
                        else:
                            raise PalmPayAPIError(f"Failed to get balance: {data.get('message')}")
                    else:
                        error_text = await response.text()
                        raise PalmPayAPIError(f"Failed to get balance: {error_text}", status_code=response.status)
                        
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            return {}
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authentication is configured."""
        return all([self.app_id, self.app_key, self.merchant_id])
    
    @property
    def environment_info(self) -> Dict[str, str]:
        """Get environment information."""
        return {
            'environment': self.environment,
            'base_url': self.base_url,
            'merchant_id': self.merchant_id,
            'terminal_id': self.terminal_id,
            'api_version': self.auth_config['api_version']
        }