"""
Paystack Authentication Manager
==============================

Handles authentication and API key management for Paystack integration.
Supports both test and live environments.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PaystackAuthManager:
    """
    Manages authentication for Paystack payment processor.
    
    Paystack uses API key authentication with separate keys for test and live modes.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Paystack authentication manager.
        
        Args:
            config: Configuration containing Paystack credentials
        """
        self.config = config
        
        # Paystack API keys
        self.public_key = config.get('public_key')
        self.secret_key = config.get('secret_key')
        self.test_public_key = config.get('test_public_key')
        self.test_secret_key = config.get('test_secret_key')
        
        # Environment configuration
        self.is_test_mode = config.get('test_mode', True)
        self.merchant_email = config.get('merchant_email')
        
        # API configuration
        self.base_url = "https://api.paystack.co" if not self.is_test_mode else "https://api.paystack.co"
        self.api_version = config.get('api_version', 'v1')
        
        # Authentication state
        self._authenticated = False
        self._last_auth_check = None
        self._auth_valid_duration = timedelta(hours=1)  # Check auth hourly
        
        self.logger = logging.getLogger(__name__)

    async def authenticate(self) -> bool:
        """
        Authenticate with Paystack API.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Authenticating with Paystack API...")
            
            # Validate API keys are present
            if not self._validate_api_keys():
                self.logger.error("Missing required Paystack API keys")
                return False
            
            # Test API connectivity with a simple request
            success = await self._test_api_connection()
            
            if success:
                self._authenticated = True
                self._last_auth_check = datetime.utcnow()
                self.logger.info(f"Successfully authenticated with Paystack ({self._get_mode_description()})")
                return True
            else:
                self._authenticated = False
                self.logger.error("Paystack API authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Paystack authentication error: {str(e)}")
            self._authenticated = False
            return False

    async def validate_token(self) -> bool:
        """
        Validate current authentication status.
        
        Returns:
            bool: True if authentication is valid
        """
        try:
            # Check if we need to re-validate
            if not self._authenticated or not self._last_auth_check:
                return await self.authenticate()
            
            # Check if auth check is still valid
            time_since_check = datetime.utcnow() - self._last_auth_check
            if time_since_check > self._auth_valid_duration:
                return await self.authenticate()
            
            return self._authenticated
            
        except Exception as e:
            self.logger.error(f"Error validating Paystack token: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict containing authorization headers
        """
        secret_key = self._get_secret_key()
        
        return {
            'Authorization': f'Bearer {secret_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-eInvoice/1.0'
        }

    def get_public_key(self) -> str:
        """
        Get appropriate public key based on mode.
        
        Returns:
            Public key for current mode
        """
        if self.is_test_mode:
            return self.test_public_key or self.public_key
        return self.public_key

    async def cleanup(self) -> None:
        """
        Clean up authentication resources.
        """
        try:
            self.logger.info("Cleaning up Paystack authentication...")
            self._authenticated = False
            self._last_auth_check = None
            
        except Exception as e:
            self.logger.error(f"Error during Paystack auth cleanup: {str(e)}")

    async def _test_api_connection(self) -> bool:
        """
        Test API connection by making a simple request.
        
        Returns:
            bool: True if connection successful
        """
        import aiohttp
        
        try:
            headers = self.get_headers()
            url = f"{self.base_url}/bank"  # Simple endpoint to test connectivity
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        self.logger.debug("Paystack API connection test successful")
                        return True
                    else:
                        self.logger.error(f"Paystack API returned status {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("Paystack API connection timeout")
            return False
        except Exception as e:
            self.logger.error(f"Paystack API connection test failed: {str(e)}")
            return False

    def _validate_api_keys(self) -> bool:
        """
        Validate that required API keys are present.
        
        Returns:
            bool: True if keys are valid
        """
        if self.is_test_mode:
            # In test mode, we need at least test secret key
            if not self.test_secret_key and not self.secret_key:
                return False
        else:
            # In live mode, we need live secret key
            if not self.secret_key:
                return False
        
        return True

    def _get_secret_key(self) -> str:
        """
        Get appropriate secret key based on mode.
        
        Returns:
            Secret key for current mode
        """
        if self.is_test_mode:
            return self.test_secret_key or self.secret_key
        return self.secret_key

    def _get_mode_description(self) -> str:
        """
        Get human-readable mode description.
        
        Returns:
            Mode description string
        """
        return "Test Mode" if self.is_test_mode else "Live Mode"

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated

    @property
    def merchant_info(self) -> Dict[str, Any]:
        """Get merchant information."""
        return {
            'merchant_email': self.merchant_email,
            'mode': self._get_mode_description(),
            'authenticated': self._authenticated,
            'last_auth_check': self._last_auth_check.isoformat() if self._last_auth_check else None
        }