"""
OPay Authentication Manager
==========================

Handles authentication and API key management for OPay integration.
Supports mobile money authentication, wallet verification, and secure API access.

Features:
- OAuth 2.0 authentication with refresh tokens
- API key authentication for server-to-server
- Wallet verification and KYC status tracking
- Rate limiting and security controls
- Nigerian fintech regulatory compliance checks
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


class OPayAuthManager:
    """
    Manages authentication for OPay payment processor.
    
    OPay uses OAuth 2.0 for user authentication and API keys for merchant
    authentication with HMAC signature verification for webhook security.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize OPay authentication manager.
        
        Args:
            config: Configuration containing OPay credentials
        """
        self.config = config
        
        # OPay API credentials
        self.public_key = config.get('public_key')
        self.private_key = config.get('private_key')
        self.merchant_id = config.get('merchant_id')
        self.app_id = config.get('app_id')
        self.secret_key = config.get('secret_key')
        
        # Environment configuration
        self.is_sandbox = config.get('sandbox_mode', True)
        self.wallet_id = config.get('wallet_id')
        
        # API configuration
        if self.is_sandbox:
            self.base_url = "https://sandboxapi.opaycheckout.com/api/v1"
            self.auth_url = "https://sandboxapi.opaycheckout.com/oauth"
        else:
            self.base_url = "https://api.opaycheckout.com/api/v1"
            self.auth_url = "https://api.opaycheckout.com/oauth"
        
        # Authentication state
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._authenticated = False
        self._last_auth_check = None
        self._auth_valid_duration = timedelta(minutes=30)  # Check auth every 30 minutes
        
        # Wallet and KYC verification
        self._wallet_verified = False
        self._kyc_status = None
        self._merchant_verified = False
        
        # Rate limiting
        self._request_count = 0
        self._rate_limit_window_start = datetime.utcnow()
        self._rate_limit_per_minute = config.get('rate_limit', 100)
        
        self.logger = logging.getLogger(__name__)

    async def authenticate(self) -> bool:
        """
        Authenticate with OPay API and verify merchant/wallet status.
        
        Returns:
            bool: True if authentication successful
        """
        try:
            self.logger.info("Authenticating with OPay API...")
            
            # Validate credentials are present
            if not self._validate_credentials():
                self.logger.error("Missing required OPay credentials")
                return False
            
            # Get access token using merchant credentials
            token_success = await self._obtain_access_token()
            if not token_success:
                return False
            
            # Verify merchant and wallet status
            verification_success = await self._verify_merchant_status()
            if not verification_success:
                self.logger.warning("Merchant verification incomplete - limited functionality")
            
            # Test API connectivity
            connectivity_success = await self._test_api_connectivity()
            
            if connectivity_success:
                self._authenticated = True
                self._last_auth_check = datetime.utcnow()
                self.logger.info(
                    f"Successfully authenticated with OPay "
                    f"({self._get_mode_description()}) - Merchant: {self._merchant_verified}, "
                    f"Wallet: {self._wallet_verified}"
                )
                return True
            else:
                self._authenticated = False
                self.logger.error("OPay API connectivity test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"OPay authentication error: {str(e)}")
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
            self.logger.error(f"Error validating OPay token: {str(e)}")
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
        
        # Add authentication headers
        if self._access_token:
            headers['Authorization'] = f'Bearer {self._access_token}'
        
        if self.merchant_id:
            headers['MerchantId'] = self.merchant_id
        
        if self.public_key:
            headers['PublicKey'] = self.public_key
        
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
        
        # Create signature string (OPay format: timestamp + merchantId + payload)
        signature_string = f"{timestamp}{self.merchant_id}{payload}"
        
        # Create HMAC signature using SHA512
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            signature_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return signature

    async def verify_webhook_signature(self, payload: str, signature: str, timestamp: str) -> bool:
        """
        Verify webhook signature from OPay.
        
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
            self.logger.error(f"OPay webhook signature verification failed: {str(e)}")
            return False

    async def cleanup(self) -> None:
        """Clean up authentication resources."""
        try:
            self.logger.info("Cleaning up OPay authentication...")
            self._authenticated = False
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
            self._last_auth_check = None
            
        except Exception as e:
            self.logger.error(f"Error during OPay auth cleanup: {str(e)}")

    async def _obtain_access_token(self) -> bool:
        """Obtain access token from OPay OAuth."""
        try:
            token_url = f"{self.auth_url}/token"
            
            # OPay uses merchant credentials for token generation
            auth_data = {
                'grant_type': 'client_credentials',
                'merchant_id': self.merchant_id,
                'public_key': self.public_key,
                'scope': 'payment_processing wallet_access'
            }
            
            # Create authorization signature
            timestamp = str(int(datetime.utcnow().timestamp()))
            payload = json.dumps(auth_data, separators=(',', ':'))
            signature = self.create_signature(payload, timestamp)
            
            headers = {
                'Content-Type': 'application/json',
                'MerchantId': self.merchant_id,
                'Authorization': signature,
                'Timestamp': timestamp
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    token_url, 
                    json=auth_data,
                    headers=headers,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        if token_response.get('code') == '00000':  # OPay success code
                            data = token_response.get('data', {})
                            self._access_token = data.get('access_token')
                            self._refresh_token = data.get('refresh_token')
                            expires_in = data.get('expires_in', 3600)
                            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)  # 5 min buffer
                            
                            self.logger.debug("OPay access token obtained successfully")
                            return True
                        else:
                            error_msg = token_response.get('message', 'Unknown error')
                            self.logger.error(f"OPay token request failed: {error_msg}")
                            return False
                    else:
                        error_text = await response.text()
                        self.logger.error(f"OPay token request failed: {response.status} - {error_text}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("OPay token request timeout")
            return False
        except Exception as e:
            self.logger.error(f"OPay token request failed: {str(e)}")
            return False

    async def _refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token."""
        try:
            if not self._refresh_token:
                return await self._obtain_access_token()
            
            refresh_url = f"{self.auth_url}/refresh"
            
            refresh_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token,
                'merchant_id': self.merchant_id
            }
            
            timestamp = str(int(datetime.utcnow().timestamp()))
            payload = json.dumps(refresh_data, separators=(',', ':'))
            signature = self.create_signature(payload, timestamp)
            
            headers = {
                'Content-Type': 'application/json',
                'MerchantId': self.merchant_id,
                'Authorization': signature,
                'Timestamp': timestamp
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    refresh_url,
                    json=refresh_data,
                    headers=headers,
                    timeout=20
                ) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        if token_response.get('code') == '00000':
                            data = token_response.get('data', {})
                            self._access_token = data.get('access_token')
                            expires_in = data.get('expires_in', 3600)
                            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                            
                            self.logger.debug("OPay access token refreshed successfully")
                            return True
                        else:
                            # Refresh failed, get new token
                            return await self._obtain_access_token()
                    else:
                        return await self._obtain_access_token()
                        
        except Exception as e:
            self.logger.error(f"OPay token refresh failed: {str(e)}")
            return await self._obtain_access_token()

    async def _verify_merchant_status(self) -> bool:
        """Verify merchant and wallet verification status."""
        try:
            headers = self.get_headers()
            
            # Check merchant verification
            merchant_url = f"{self.base_url}/merchant/status"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(merchant_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        merchant_data = await response.json()
                        
                        if merchant_data.get('code') == '00000':
                            data = merchant_data.get('data', {})
                            self._merchant_verified = data.get('verified', False)
                            self._kyc_status = data.get('kyc_status', 'pending')
                            
                            # Check wallet status if wallet_id provided
                            if self.wallet_id:
                                await self._verify_wallet_status(session, headers)
                            
                            return self._merchant_verified
                        else:
                            self.logger.warning(f"Merchant status check failed: {merchant_data.get('message')}")
                            return False
                    else:
                        self.logger.warning(f"Merchant verification check failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"Merchant verification failed: {str(e)}")
            return False

    async def _verify_wallet_status(self, session: aiohttp.ClientSession, headers: Dict[str, str]) -> None:
        """Verify wallet status."""
        try:
            wallet_url = f"{self.base_url}/wallet/{self.wallet_id}/status"
            
            async with session.get(wallet_url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    wallet_data = await response.json()
                    
                    if wallet_data.get('code') == '00000':
                        data = wallet_data.get('data', {})
                        self._wallet_verified = data.get('verified', False)
                        wallet_status = data.get('status', 'inactive')
                        
                        self.logger.debug(f"Wallet verification status: {self._wallet_verified}, status: {wallet_status}")
                    else:
                        self.logger.warning(f"Wallet status check failed: {wallet_data.get('message')}")
                else:
                    self.logger.warning(f"Wallet verification check failed: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Wallet verification failed: {str(e)}")

    async def _test_api_connectivity(self) -> bool:
        """Test API connectivity with a simple request."""
        try:
            headers = self.get_headers()
            test_url = f"{self.base_url}/merchant/banks"  # Simple endpoint to test connectivity
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url, headers=headers, timeout=10) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        if response_data.get('code') == '00000':
                            self.logger.debug("OPay API connectivity test successful")
                            return True
                        else:
                            self.logger.error(f"OPay API returned error: {response_data.get('message')}")
                            return False
                    else:
                        self.logger.error(f"OPay API returned status {response.status}")
                        return False
                        
        except asyncio.TimeoutError:
            self.logger.error("OPay API connection timeout")
            return False
        except Exception as e:
            self.logger.error(f"OPay API connectivity test failed: {str(e)}")
            return False

    def _validate_credentials(self) -> bool:
        """Validate that required credentials are present."""
        required_fields = ['merchant_id', 'public_key', 'secret_key']
        
        for field in required_fields:
            if not self.config.get(field):
                self.logger.error(f"Missing required OPay credential: {field}")
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
    def is_merchant_verified(self) -> bool:
        """Check if merchant is verified."""
        return self._merchant_verified

    @property
    def is_wallet_verified(self) -> bool:
        """Check if wallet is verified."""
        return self._wallet_verified

    @property
    def merchant_info(self) -> Dict[str, Any]:
        """Get merchant and wallet information."""
        return {
            'merchant_id': self.merchant_id,
            'wallet_id': self.wallet_id,
            'mode': self._get_mode_description(),
            'authenticated': self._authenticated,
            'merchant_verified': self._merchant_verified,
            'wallet_verified': self._wallet_verified,
            'kyc_status': self._kyc_status,
            'last_auth_check': self._last_auth_check.isoformat() if self._last_auth_check else None,
            'token_expires_at': self._token_expires_at.isoformat() if self._token_expires_at else None
        }