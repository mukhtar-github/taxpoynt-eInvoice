"""
Moniepoint Authentication Manager
================================

Handles authentication and API key management for Moniepoint integration.
Supports agent banking authentication, business verification, and secure API access.

Features:
- API key authentication with signature validation
- Agent banking credential management
- Business verification status tracking
- Rate limiting and security controls
- Nigerian regulatory compliance checks
"""

import hashlib
import hmac
import json
import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import aiohttp

logger = logging.getLogger(__name__)


class MoniepointAuthManager:
    """
    Manages authentication for Moniepoint payment processor.
    
    Moniepoint uses API key authentication with HMAC signature verification
    for secure communication in agent banking scenarios.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Moniepoint authentication manager.
        
        Args:
            config: Configuration containing Moniepoint credentials
        """
        self.config = config
        
        # Moniepoint API credentials
        self.api_key = config.get('api_key')
        self.secret_key = config.get('secret_key')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        
        # Environment configuration
        self.is_sandbox = config.get('sandbox_mode', True)
        self.business_id = config.get('business_id')
        self.agent_id = config.get('agent_id')  # For agent banking
        
        # API configuration
        if self.is_sandbox:
            self.base_url = "https://sandbox.moniepoint.com/api/v1"
        else:
            self.base_url = "https://api.moniepoint.com/api/v1"
        
        # Authentication state
        self._access_token = None
        self._token_expires_at = None
        self._authenticated = False
        self._last_auth_check = None
        self._auth_valid_duration = timedelta(minutes=30)  # Check auth every 30 minutes
        
        # Business verification
        self._business_verified = False
        self._agent_verified = False
        self._kyc_status = None
        
        # Rate limiting
        self._request_count = 0
        self._rate_limit_window_start = datetime.utcnow()
        self._rate_limit_per_minute = config.get('rate_limit', 60)
        
        self.logger = logging.getLogger(__name__)

    async def authenticate(self) -> bool:
        """
        Authenticate with Moniepoint API and verify business status.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Authenticating with Moniepoint API...")
            
            # Validate credentials are present
            if not self._validate_credentials():
                self.logger.error("Missing required Moniepoint credentials")
                return False
            
            # Get access token
            token_success = await self._obtain_access_token()
            if not token_success:
                return False
            
            # Verify business and agent status
            verification_success = await self._verify_business_status()
            if not verification_success:
                self.logger.warning("Business verification incomplete - limited functionality")
            
            # Test API connectivity
            connectivity_success = await self._test_api_connectivity()
            
            if connectivity_success:
                self._authenticated = True
                self._last_auth_check = datetime.utcnow()
                self.logger.info(
                    f"Successfully authenticated with Moniepoint "
                    f"({self._get_mode_description()}) - Business: {self._business_verified}, "
                    f"Agent: {self._agent_verified}"
                )
                return True
            else:
                self._authenticated = False
                self.logger.error("Moniepoint API connectivity test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Moniepoint authentication error: {str(e)}")
            self._authenticated = False
            return False

    async def validate_token(self) -> bool:
        """
        Validate current authentication status and refresh if needed.
        
        Returns:
            bool: True if authentication is valid
        """
        try:
            # Check if we need to re-authenticate
            if not self._authenticated or not self._last_auth_check:
                return await self.authenticate()
            
            # Check if auth check is still valid
            time_since_check = datetime.utcnow() - self._last_auth_check
            if time_since_check > self._auth_valid_duration:
                return await self.authenticate()
            
            # Check if access token needs refresh
            if self._token_expires_at and datetime.utcnow() >= self._token_expires_at:
                return await self._refresh_access_token()
            
            return self._authenticated
            
        except Exception as e:
            self.logger.error(f"Error validating Moniepoint token: {str(e)}")
            return False

    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dict containing authorization headers
        """
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'TaxPoynt-eInvoice/1.0'
        }
        
        if self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        elif self.api_key:
            headers['Authorization'] = f'ApiKey {self.api_key}'
        
        # Add client identification
        if self.client_id:
            headers['X-Client-ID'] = self.client_id
        
        return headers

    def create_signature(self, payload: str, timestamp: str) -> str:
        """
        Create HMAC signature for secure API communication.
        
        Args:
            payload: Request payload
            timestamp: Request timestamp
            
        Returns:
            HMAC signature string
        """
        if not self.secret_key:
            raise ValueError("Secret key required for signature creation")
        
        # Create signature string
        signature_string = f"{timestamp}{payload}"
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature

    async def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify webhook signature from Moniepoint.
        
        Args:
            payload: Webhook payload
            signature: Provided signature
            timestamp: Request timestamp
            
        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = self.create_signature(payload, timestamp)
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        try:
            self.logger.info("Cleaning up Moniepoint authentication...")
            self._authenticated = False
            self._access_token = None
            self._token_expires_at = None
            self._last_auth_check = None
            
        except Exception as e:
            self.logger.error(f"Error during Moniepoint auth cleanup: {str(e)}")

    async def _obtain_access_token(self) -> bool:
        """Obtain access token from Moniepoint OAuth."""
        try:
            token_url = f"{self.base_url}/auth/token"
            
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'payment_processing agent_banking'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_url, 
                    data=token_data,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        self._access_token = token_response.get('access_token')
                        expires_in = token_response.get('expires_in', 3600)
                        self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                        
                        self.logger.debug("Access token obtained successfully")
                        return True
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Token request failed: {response.status} - {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("Token request timeout")
            return False
        except Exception as e:
            self.logger.error(f"Token request failed: {str(e)}")
            return False

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token."""
        return await self._obtain_access_token()

    async def _verify_business_status(self) -> bool:
        """Verify business and agent verification status."""
        try:
            headers = self.get_headers()
            
            # Check business verification
            business_url = f"{self.base_url}/business/{self.business_id}/status"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(business_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        business_data = await response.json()
                        self._business_verified = business_data.get('verified', False)
                        self._kyc_status = business_data.get('kyc_status', 'pending')
                        
                        # Check agent verification if agent_id provided
                        if self.agent_id:
                            await self._verify_agent_status(session, headers)
                        
                        return self._business_verified
                    else:
                        self.logger.warning(f"Business verification check failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Business verification failed: {str(e)}")
            return False

    async def _verify_agent_status(self, session: aiohttp.ClientSession, headers: Dict[str, str]) -> None:
        """Verify agent banking status."""
        try:
            agent_url = f"{self.base_url}/agents/{self.agent_id}/status"
            
            async with session.get(agent_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    agent_data = await response.json()
                    self._agent_verified = agent_data.get('verified', False)
                    agent_tier = agent_data.get('tier', 'standard')
                    
                    self.logger.debug(f"Agent verification status: {self._agent_verified}, tier: {agent_tier}")
                else:
                    self.logger.warning(f"Agent verification check failed: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Agent verification failed: {str(e)}")

    async def _test_api_connectivity(self) -> bool:
        """Test API connectivity with a simple request."""
        try:
            headers = self.get_headers()
            test_url = f"{self.base_url}/health"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        self.logger.debug("Moniepoint API connectivity test successful")
                        return True
                    else:
                        self.logger.error(f"Moniepoint API returned status {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("Moniepoint API connection timeout")
            return False
        except Exception as e:
            self.logger.error(f"Moniepoint API connectivity test failed: {str(e)}")
            return False

    def _validate_credentials(self) -> bool:
        """Validate that required credentials are present."""
        required_fields = ['api_key', 'client_id', 'client_secret']
        
        for field in required_fields:
            if not self.config.get(field):
                self.logger.error(f"Missing required credential: {field}")
                return False
        
        return True

    def _get_mode_description(self) -> str:
        """Get human-readable mode description."""
        return "Sandbox Mode" if self.is_sandbox else "Live Mode"

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        now = datetime.utcnow()
        
        # Reset counter if window has passed
        if (now - self._rate_limit_window_start).total_seconds() >= 60:
            self._request_count = 0
            self._rate_limit_window_start = now
        
        # Check if we're within limits
        if self._request_count >= self._rate_limit_per_minute:
            return False
        
        self._request_count += 1
        return True

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._authenticated

    @property
    def is_business_verified(self) -> bool:
        """Check if business is verified."""
        return self._business_verified

    @property
    def is_agent_verified(self) -> bool:
        """Check if agent is verified."""
        return self._agent_verified

    @property
    def merchant_info(self) -> Dict[str, Any]:
        """Get merchant and agent information."""
        return {
            'business_id': self.business_id,
            'agent_id': self.agent_id,
            'mode': self._get_mode_description(),
            'authenticated': self._authenticated,
            'business_verified': self._business_verified,
            'agent_verified': self._agent_verified,
            'kyc_status': self._kyc_status,
            'last_auth_check': self._last_auth_check.isoformat() if self._last_auth_check else None,
            'token_expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None
        }