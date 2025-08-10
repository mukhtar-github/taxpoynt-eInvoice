"""
Jumia E-commerce Authentication Manager
Handles Jumia Marketplace API authentication including API key and seller authentication.
"""
import asyncio
import logging
import hashlib
import hmac
import base64
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import aiohttp

from .exceptions import (
    JumiaAuthenticationError,
    JumiaConnectionError,
    JumiaAPIError,
    get_marketplace_code
)

logger = logging.getLogger(__name__)


class JumiaAuthManager:
    """
    Jumia E-commerce Authentication Manager
    
    Handles Jumia Marketplace API authentication methods:
    - API Key authentication for seller access
    - Seller token authentication for marketplace operations
    - Regional marketplace authentication
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Jumia authentication manager.
        
        Args:
            config: Configuration dictionary containing:
                - seller_id: Jumia seller ID (required)
                - api_key: Jumia API key (required)
                - api_secret: Jumia API secret (required)
                - country_code: Country code for marketplace (default: 'NG')
                - marketplace: Specific marketplace identifier
                - webhook_secret: Secret for webhook verification
                - sandbox: Use sandbox environment (default: False)
        """
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Required configuration
        self.seller_id = config.get('seller_id')
        self.api_key = config.get('api_key')
        self.api_secret = config.get('api_secret')
        
        if not all([self.seller_id, self.api_key, self.api_secret]):
            raise JumiaAuthenticationError(
                "seller_id, api_key, and api_secret are required for Jumia authentication"
            )
        
        # Marketplace configuration
        self.country_code = config.get('country_code', 'NG')  # Default to Nigeria
        self.marketplace = config.get('marketplace') or get_marketplace_code(self.country_code)
        self.sandbox = config.get('sandbox', False)
        self.webhook_secret = config.get('webhook_secret', '')
        
        # Authentication state
        self._authenticated = False
        self._auth_headers = {}
        self._token_expires_at = None
        
        # Base API URL
        if self.sandbox:
            self.base_url = f"https://sellercenter-api.jumia.com.ng/v3"  # Sandbox
        else:
            # Regional API endpoints
            domain_mapping = {
                'jumia-ng': 'jumia.com.ng',
                'jumia-ke': 'jumia.co.ke',
                'jumia-ug': 'jumia.co.ug',
                'jumia-gh': 'jumia.com.gh',
                'jumia-ci': 'jumia.ci',
                'jumia-sn': 'jumia.sn',
                'jumia-ma': 'jumia.ma',
                'jumia-tn': 'jumia.com.tn',
                'jumia-dz': 'jumia.dz',
                'jumia-eg': 'jumia.com.eg'
            }
            domain = domain_mapping.get(self.marketplace, 'jumia.com.ng')
            self.base_url = f"https://sellercenter-api.{domain}/v3"
        
        # Session for HTTP requests
        self.session = None
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Jumia API.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            self.logger.info(f"Authenticating with Jumia marketplace: {self.marketplace}")
            
            # Generate authentication headers
            await self._generate_auth_headers()
            
            # Test authentication with a simple API call
            await self._test_authentication()
            
            self._authenticated = True
            self.logger.info("Jumia authentication successful")
            return True
            
        except Exception as e:
            self.logger.error(f"Jumia authentication error: {e}")
            self._authenticated = False
            raise JumiaAuthenticationError(f"Authentication failed: {e}")
    
    async def _generate_auth_headers(self):
        """Generate authentication headers for API requests."""
        try:
            # Jumia uses API key and signature-based authentication
            timestamp = str(int(datetime.now().timestamp()))
            
            # Create signature string (API key + timestamp + seller_id)
            signature_string = f"{self.api_key}{timestamp}{self.seller_id}"
            
            # Generate HMAC signature
            signature = hmac.new(
                self.api_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Set authentication headers
            self._auth_headers = {
                'Authorization': f"Bearer {self.api_key}",
                'X-Seller-ID': self.seller_id,
                'X-Timestamp': timestamp,
                'X-Signature': signature,
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'User-Agent': 'TaxPoynt-Jumia-Connector/1.0'
            }
            
        except Exception as e:
            raise JumiaAuthenticationError(f"Failed to generate auth headers: {e}")
    
    async def _test_authentication(self):
        """Test authentication with a simple API call."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test with seller profile endpoint
            url = f"{self.base_url}/seller/profile"
            
            async with self.session.get(url, headers=self._auth_headers) as response:
                if response.status == 200:
                    return True
                elif response.status == 401:
                    raise JumiaAuthenticationError("Invalid authentication credentials")
                elif response.status == 403:
                    raise JumiaAuthenticationError("Insufficient permissions")
                else:
                    response_text = await response.text()
                    raise JumiaAuthenticationError(f"Authentication test failed: {response.status} - {response_text}")
                    
        except aiohttp.ClientError as e:
            raise JumiaConnectionError(f"Connection error during authentication test: {e}")
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of authentication headers
        """
        if not self._authenticated:
            await self.authenticate()
        
        # Regenerate headers if they're old (for signature freshness)
        if self._auth_headers:
            timestamp = int(self._auth_headers.get('X-Timestamp', '0'))
            current_timestamp = int(datetime.now().timestamp())
            
            # Regenerate if headers are older than 5 minutes
            if current_timestamp - timestamp > 300:
                await self._generate_auth_headers()
        
        return self._auth_headers.copy()
    
    async def refresh_authentication(self) -> bool:
        """
        Refresh authentication if needed.
        
        Returns:
            True if refresh successful or not needed, False otherwise
        """
        try:
            # For Jumia, we regenerate the signature
            await self._generate_auth_headers()
            await self._test_authentication()
            return True
            
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
            
            self.logger.info("Jumia authentication revoked")
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
        Verify Jumia webhook signature.
        
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
            
            # Include timestamp in signature if provided
            if timestamp:
                signature_data = f"{timestamp}.{payload_str}"
            else:
                signature_data = payload_str
            
            # Create expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signature_data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures securely
            return hmac.compare_digest(signature.lower(), expected_signature.lower())
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {e}")
            return False
    
    def get_seller_id(self) -> str:
        """Get the current seller ID."""
        return self.seller_id
    
    def get_marketplace(self) -> str:
        """Get the current marketplace identifier."""
        return self.marketplace
    
    def get_country_code(self) -> str:
        """Get the current country code."""
        return self.country_code
    
    def get_base_url(self) -> str:
        """Get the base API URL for the current marketplace."""
        return self.base_url
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated
    
    def is_sandbox(self) -> bool:
        """Check if using sandbox environment."""
        return self.sandbox
    
    async def get_seller_profile(self) -> Dict[str, Any]:
        """
        Get seller profile information.
        
        Returns:
            Seller profile data
        """
        try:
            if not self._authenticated:
                await self.authenticate()
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            url = f"{self.base_url}/seller/profile"
            headers = await self.get_auth_headers()
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    raise JumiaAPIError(f"Failed to get seller profile: {response.status} - {response_text}")
                    
        except Exception as e:
            self.logger.error(f"Failed to get seller profile: {e}")
            raise JumiaAuthenticationError(f"Seller profile retrieval failed: {e}")
    
    async def close(self):
        """Close the authentication manager and clean up resources."""
        if self.session:
            await self.session.close()
            self.session = None
        
        self._authenticated = False
        self._auth_headers = {}
    
    def __str__(self) -> str:
        """String representation of the auth manager."""
        return f"JumiaAuthManager(seller_id={self.seller_id}, marketplace={self.marketplace})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the auth manager."""
        return (f"JumiaAuthManager("
                f"seller_id='{self.seller_id}', "
                f"marketplace='{self.marketplace}', "
                f"country_code='{self.country_code}', "
                f"sandbox={self.sandbox}, "
                f"authenticated={self._authenticated})")