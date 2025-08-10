"""
PalmPay Authentication Manager
=============================

Secure authentication and token management for PalmPay API integration.
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
class PalmPayCredentials:
    """PalmPay API credentials with encryption support"""
    api_key: str
    secret_key: str
    merchant_id: str
    environment: str = "sandbox"  # sandbox or production
    
    def __post_init__(self):
        """Encrypt sensitive data after initialization"""
        self.encryption_service = EncryptionService()
        self._encrypted_secret = self.encryption_service.encrypt(self.secret_key)
        # Clear plaintext secret from memory
        self.secret_key = "[ENCRYPTED]"
    
    def get_secret_key(self) -> str:
        """Decrypt and return secret key"""
        return self.encryption_service.decrypt(self._encrypted_secret)


@dataclass
class PalmPayAuthToken:
    """PalmPay authentication token with expiration handling"""
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


class PalmPayAuthManager:
    """
    PalmPay authentication manager with secure token handling
    """
    
    def __init__(self, credentials: PalmPayCredentials):
        self.credentials = credentials
        self.current_token: Optional[PalmPayAuthToken] = None
        self.logger = LoggingService().get_logger("palmpay_auth")
        
        # PalmPay API endpoints
        self.base_url = self._get_base_url()
        self.auth_endpoint = f"{self.base_url}/auth/token"
        
        # Rate limiting
        self._last_auth_request = 0
        self._min_auth_interval = 60  # Minimum 60 seconds between auth requests
    
    def _get_base_url(self) -> str:
        """Get base URL based on environment"""
        if self.credentials.environment == "production":
            return "https://api.palmpay.com"
        else:
            return "https://sandbox-api.palmpay.com"
    
    async def get_valid_token(self) -> PalmPayAuthToken:
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
            
            self.logger.info("PalmPay authentication successful", extra={
                'merchant_id': self.credentials.merchant_id,
                'environment': self.credentials.environment,
                'expires_at': self.current_token.expires_at.isoformat()
            })
            
            return self.current_token
            
        except Exception as e:
            self.logger.error("PalmPay authentication failed", extra={
                'error': str(e),
                'merchant_id': self.credentials.merchant_id
            })
            raise
    
    async def _authenticate(self) -> PalmPayAuthToken:
        """
        Perform OAuth authentication with PalmPay
        """
        auth_payload = {
            'api_key': self.credentials.api_key,
            'merchant_id': self.credentials.merchant_id,
            'timestamp': int(time.time())
        }
        
        # Generate signature
        signature = self._generate_signature(auth_payload)
        auth_payload['signature'] = signature
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'TaxPoynt-PalmPay-Connector/1.0.0'
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
                    return PalmPayAuthToken(
                        access_token=data['access_token'],
                        token_type=data.get('token_type', 'Bearer'),
                        expires_in=data.get('expires_in', 3600)
                    )
                else:
                    error_data = await response.text()
                    raise Exception(f"Authentication failed: {response.status} - {error_data}")
    
    def _generate_signature(self, payload: Dict[str, Any]) -> str:
        """
        Generate HMAC signature for PalmPay API authentication
        """
        # Create signature string (sorted parameters)
        sorted_params = sorted(payload.items())
        signature_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
        
        # Generate HMAC-SHA256 signature
        secret_key = self.credentials.get_secret_key()
        signature = hmac.new(
            secret_key.encode('utf-8'),
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
            'User-Agent': 'TaxPoynt-PalmPay-Connector/1.0.0',
            'X-Merchant-ID': self.credentials.merchant_id
        }
    
    async def create_signed_request_headers(self, payload: Dict[str, Any]) -> Dict[str, str]:
        """
        Create headers with signature for sensitive operations
        """
        headers = await self.create_authenticated_headers()
        
        # Add request signature
        timestamp = int(time.time())
        payload_with_timestamp = {**payload, 'timestamp': timestamp}
        signature = self._generate_signature(payload_with_timestamp)
        
        headers.update({
            'X-Timestamp': str(timestamp),
            'X-Signature': signature
        })
        
        return headers
    
    def validate_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Validate PalmPay webhook signature
        """
        try:
            # Check timestamp (should be within 5 minutes)
            webhook_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - webhook_time) > 300:  # 5 minutes
                self.logger.warning("Webhook timestamp too old", extra={
                    'webhook_time': webhook_time,
                    'current_time': current_time
                })
                return False
            
            # Generate expected signature
            signature_string = f"{timestamp}.{payload}"
            secret_key = self.credentials.get_secret_key()
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
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
    
    async def refresh_token(self) -> PalmPayAuthToken:
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
        self.logger.info("PalmPay credentials cleared")


# Export for use in other modules
__all__ = [
    'PalmPayCredentials',
    'PalmPayAuthToken', 
    'PalmPayAuthManager'
]