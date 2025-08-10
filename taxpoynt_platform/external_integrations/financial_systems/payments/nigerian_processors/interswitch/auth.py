"""
Interswitch Authentication Manager
=================================

Secure authentication and token management for Interswitch API integration.
Handles OAuth flows, token refresh, and secure credential storage.
"""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
import aiohttp
from dataclasses import dataclass

from taxpoynt_platform.core_platform.security.encryption.service import EncryptionService
from taxpoynt_platform.core_platform.monitoring.logging.service import LoggingService


@dataclass
class InterswitchCredentials:
    """Interswitch API credentials with encryption support"""
    client_id: str
    client_secret: str
    merchant_id: str
    environment: str = "sandbox"  # sandbox or production
    
    def __post_init__(self):
        """Encrypt sensitive data after initialization"""
        self.encryption_service = EncryptionService()
        self._encrypted_secret = self.encryption_service.encrypt(self.client_secret)
        # Clear plaintext secret from memory
        self.client_secret = "[ENCRYPTED]"
    
    def get_client_secret(self) -> str:
        """Decrypt and return client secret"""
        return self.encryption_service.decrypt(self._encrypted_secret)


@dataclass
class InterswitchAuthToken:
    """Interswitch authentication token with expiration handling"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def expires_at(self) -> datetime:
        """Calculate token expiration time"""
        return self.created_at + timedelta(seconds=self.expires_in)
    
    @property
    def is_expired(self) -> bool:
        """Check if token is expired (with 5-minute buffer)"""
        buffer_time = timedelta(minutes=5)
        return datetime.utcnow() >= (self.expires_at - buffer_time)
    
    @property
    def authorization_header(self) -> str:
        """Get authorization header value"""
        return f"{self.token_type} {self.access_token}"


class InterswitchAuthManager:
    """
    Interswitch authentication manager with secure token handling
    """
    
    def __init__(self, credentials: InterswitchCredentials):
        self.credentials = credentials
        self.current_token: Optional[InterswitchAuthToken] = None
        self.logger = LoggingService().get_logger("interswitch_auth")
        
        # Interswitch API endpoints
        self.base_url = self._get_base_url()
        self.auth_endpoint = f"{self.base_url}/api/v1/auth/token"
        
        # Rate limiting
        self._last_auth_request = 0
        self._min_auth_interval = 60  # Minimum 60 seconds between auth requests
    
    def _get_base_url(self) -> str:
        """Get base URL based on environment"""
        if self.credentials.environment == "production":
            return "https://webpay.interswitchng.com"
        else:
            return "https://sandbox.interswitchng.com"
    
    async def get_valid_token(self) -> InterswitchAuthToken:
        """
        Get a valid authentication token, refreshing if necessary
        """
        if self.current_token and not self.current_token.is_expired:
            return self.current_token
        
        # Check rate limiting
        current_time = time.time()
        if current_time - self._last_auth_request < self._min_auth_interval:
            if self.current_token:  # Use expired token if rate limited
                self.logger.warning("Rate limited, using potentially expired token")
                return self.current_token
            else:
                # Wait for rate limit if no token available
                wait_time = self._min_auth_interval - (current_time - self._last_auth_request)
                await asyncio.sleep(wait_time)
        
        try:
            self.current_token = await self._authenticate()
            self._last_auth_request = time.time()
            
            self.logger.info("Interswitch authentication successful", extra={
                'merchant_id': self.credentials.merchant_id,
                'environment': self.credentials.environment,
                'expires_at': self.current_token.expires_at.isoformat()
            })
            
            return self.current_token
            
        except Exception as e:
            self.logger.error("Interswitch authentication failed", extra={
                'error': str(e),
                'merchant_id': self.credentials.merchant_id
            })
            raise
    
    async def _authenticate(self) -> InterswitchAuthToken:
        """
        Perform OAuth authentication with Interswitch
        """
        timestamp = str(int(time.time() * 1000))  # Milliseconds
        nonce = self._generate_nonce()
        
        # Create signature
        signature_params = {
            'client_id': self.credentials.client_id,
            'timestamp': timestamp,
            'nonce': nonce
        }
        
        signature = self._generate_signature(signature_params)
        
        auth_payload = {
            'client_id': self.credentials.client_id,
            'timestamp': timestamp,
            'nonce': nonce,
            'signature': signature,
            'grant_type': 'client_credentials'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-Interswitch-Connector/1.0.0'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.auth_endpoint,
                json=auth_payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return InterswitchAuthToken(
                        access_token=data['access_token'],
                        token_type=data.get('token_type', 'Bearer'),
                        expires_in=data.get('expires_in', 3600)
                    )
                else:
                    error_data = await response.text()
                    raise Exception(f"Authentication failed: {response.status} - {error_data}")
    
    def _generate_nonce(self) -> str:
        """Generate a unique nonce for the request"""
        return hashlib.md5(f"{time.time()}{self.credentials.client_id}".encode()).hexdigest()
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for Interswitch API authentication
        """
        # Create signature string (sorted parameters)
        sorted_params = sorted(params.items())
        signature_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # Generate HMAC-SHA256 signature
        client_secret = self.credentials.get_client_secret()
        signature = hmac.new(
            client_secret.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    async def create_authenticated_headers(self) -> Dict[str, str]:
        """
        Create headers with valid authentication token
        """
        token = await self.get_valid_token()
        
        return {
            'Authorization': token.authorization_header,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-Interswitch-Connector/1.0.0',
            'X-Merchant-ID': self.credentials.merchant_id,
            'X-Client-ID': self.credentials.client_id
        }
    
    async def create_signed_request_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Create headers with signature for sensitive operations
        """
        headers = await self.create_authenticated_headers()
        
        # Add request signature
        timestamp = str(int(time.time() * 1000))
        nonce = self._generate_nonce()
        
        signature_params = {
            **payload,
            'timestamp': timestamp,
            'nonce': nonce,
            'client_id': self.credentials.client_id
        }
        
        signature = self._generate_signature(signature_params)
        
        headers.update({
            'X-Timestamp': timestamp,
            'X-Nonce': nonce,
            'X-Signature': signature
        })
        
        return headers
    
    def validate_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Validate Interswitch webhook signature
        """
        try:
            # Check timestamp (should be within 5 minutes)
            webhook_time = int(timestamp)
            current_time = int(time.time() * 1000)
            if abs(current_time - webhook_time) > 300000:  # 5 minutes in milliseconds
                self.logger.warning("Webhook timestamp too old", extra={
                    'webhook_time': webhook_time,
                    'current_time': current_time
                })
                return False
            
            # Generate expected signature
            signature_string = f"{timestamp}.{payload}"
            client_secret = self.credentials.get_client_secret()
            expected_signature = hmac.new(
                client_secret.encode('utf-8'),
                signature_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            self.logger.error("Webhook signature validation failed", extra={
                'error': str(e)
            })
            return False
    
    async def refresh_token(self) -> InterswitchAuthToken:
        """
        Force token refresh
        """
        self.current_token = None
        return await self.get_valid_token()
    
    def clear_credentials(self):
        """
        Clear stored credentials and tokens
        """
        self.current_token = None
        # Credentials are encrypted, but clear references
        self.credentials = None
        self.logger.info("Interswitch credentials cleared")


# Export for use in other modules
__all__ = [
    'InterswitchCredentials',
    'InterswitchAuthToken', 
    'InterswitchAuthManager'
]