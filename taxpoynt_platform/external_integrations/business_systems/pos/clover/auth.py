"""
Clover POS Authentication Module

Handles OAuth 2.0 authentication and API access management for Clover POS integration.
Supports both Clover production and sandbox environments with comprehensive token management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import aiohttp

from .exceptions import (
    CloverAuthenticationError, CloverConfigurationError, 
    CloverConnectionError, CloverAPIError
)

logger = logging.getLogger(__name__)


class CloverAuthenticator:
    """
    Clover POS authentication manager for TaxPoynt eInvoice System Integrator functions.
    
    Supports OAuth 2.0 authentication for Clover REST API with comprehensive token management.
    Handles both sandbox and production environments with automatic token refresh.
    
    Clover API Documentation:
    - REST API: https://docs.clover.com/reference/overview
    - OAuth: https://docs.clover.com/docs/oauth-20
    
    Authentication Features:
    - OAuth 2.0 Authorization Code flow
    - Automatic token refresh and management
    - Merchant ID discovery and validation
    - Sandbox and production environment support
    - Rate limiting awareness
    - API version management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Clover authenticator.
        
        Args:
            config: Configuration dictionary containing Clover credentials and settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Clover OAuth configuration
        self.app_id = config.get('app_id')  # Clover uses app_id instead of client_id
        self.app_secret = config.get('app_secret')  # Clover uses app_secret
        self.redirect_uri = config.get('redirect_uri')
        
        # Environment configuration
        self.sandbox = config.get('sandbox', True)
        self.environment = 'sandbox' if self.sandbox else 'production'
        
        # Set API endpoints based on environment
        if self.sandbox:
            self.base_url = 'https://apisandbox.dev.clover.com'
            self.oauth_base_url = 'https://sandbox.dev.clover.com/oauth'
        else:
            self.base_url = 'https://api.clover.com'
            self.oauth_base_url = 'https://www.clover.com/oauth'
        
        # API version
        self.api_version = config.get('api_version', 'v3')
        
        # Authentication state
        self.access_token = config.get('access_token')
        self.merchant_id = config.get('merchant_id')  # Required for Clover API calls
        self.token_expires_at = None
        
        # Clover doesn't typically use refresh tokens in the same way
        # Access tokens are long-lived (but can be revoked)
        
        # Session management
        self.session = None
        self.rate_limit_remaining = 1000  # Clover default
        self.rate_limit_reset_time = datetime.now()
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        if not self.app_id:
            raise CloverConfigurationError('app_id', 'Clover App ID is required')
        
        if not self.app_secret:
            raise CloverConfigurationError('app_secret', 'Clover App Secret is required')
        
        if not self.redirect_uri:
            raise CloverConfigurationError('redirect_uri', 'Redirect URI is required')
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session for API requests."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            headers = {
                'User-Agent': 'TaxPoynt-eInvoice/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            self.session = aiohttp.ClientSession(timeout=timeout, headers=headers)
        return self.session
    
    def get_oauth_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Generate OAuth 2.0 authorization URL for merchant consent.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL for merchant redirection
        """
        params = {
            'response_type': 'code',
            'client_id': self.app_id,  # Clover uses client_id in OAuth flow
            'redirect_uri': self.redirect_uri
        }
        
        if state:
            params['state'] = state
        
        auth_url = f"{self.oauth_base_url}/authorize?" + urlencode(params)
        self.logger.info(f"Generated Clover OAuth authorization URL for {self.environment}")
        
        return auth_url
    
    async def exchange_authorization_code(self, authorization_code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Authorization code received from OAuth callback
            state: State parameter for verification (if used)
            
        Returns:
            Token response containing access_token, merchant info, etc.
        """
        try:
            session = await self.get_session()
            
            # Prepare token exchange request
            token_url = f"{self.oauth_base_url}/token"
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri
            }
            
            self.logger.info("Exchanging authorization code for Clover access token")
            
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise CloverAuthenticationError(
                        f"Token exchange failed: {error_text}",
                        error_code=str(response.status)
                    )
                
                token_data = await response.json()
                
                # Store tokens and merchant information
                self.access_token = token_data.get('access_token')
                self.merchant_id = token_data.get('merchant_id')  # Clover provides merchant_id
                
                # Clover access tokens are long-lived, but we can set a reasonable expiration
                # In practice, these tokens don't expire unless revoked
                self.token_expires_at = datetime.now() + timedelta(days=365)  # 1 year default
                
                self.logger.info(f"Successfully obtained Clover access token for merchant {self.merchant_id}")
                
                return {
                    'access_token': self.access_token,
                    'merchant_id': self.merchant_id,
                    'token_type': 'Bearer',
                    'environment': self.environment,
                    'expires_in': 365 * 24 * 3600,  # 1 year in seconds
                    'scope': token_data.get('scope', 'read write')
                }
        
        except Exception as e:
            self.logger.error(f"Authorization code exchange failed: {str(e)}")
            if isinstance(e, CloverAuthenticationError):
                raise
            raise CloverAuthenticationError(f"Token exchange error: {str(e)}")
    
    async def validate_token(self) -> bool:
        """
        Validate the current access token by making a test API call.
        
        Returns:
            True if token is valid
        """
        if not self.access_token or not self.merchant_id:
            return False
        
        try:
            # Test token with a simple API call
            test_result = await self.test_api_access('merchants')
            return test_result.get('success', False)
        
        except Exception as e:
            self.logger.error(f"Token validation failed: {str(e)}")
            return False
    
    async def ensure_valid_token(self) -> bool:
        """
        Ensure we have a valid access token.
        
        Returns:
            True if valid token is available
        """
        if not self.access_token:
            return False
        
        # Check if token is expired (though Clover tokens are long-lived)
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self.logger.warning("Clover access token has expired - re-authentication required")
            return False
        
        # Validate token with API call
        return await self.validate_token()
    
    async def authenticate(self) -> bool:
        """
        Perform authentication check and setup.
        
        Returns:
            True if authentication is successful
        """
        try:
            # If we have stored tokens, validate them
            if self.access_token and self.merchant_id:
                if await self.ensure_valid_token():
                    # Test API access to confirm authentication
                    test_result = await self.test_api_access()
                    if test_result.get('success'):
                        return True
            
            # If no valid token, authentication is needed via OAuth flow
            self.logger.warning("No valid access token available - OAuth flow required")
            return False
        
        except Exception as e:
            self.logger.error(f"Authentication check failed: {str(e)}")
            return False
    
    async def test_api_access(self, endpoint: str = 'merchants') -> Dict[str, Any]:
        """
        Test API access with current authentication.
        
        Args:
            endpoint: API endpoint to test (default: merchants for basic access check)
            
        Returns:
            Test result with success status and details
        """
        try:
            session = await self.get_session()
            
            # Build test URL
            if endpoint == 'merchants' and self.merchant_id:
                test_url = f"{self.base_url}/{self.api_version}/merchants/{self.merchant_id}"
            else:
                test_url = f"{self.base_url}/{self.api_version}/{endpoint}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Update rate limit info if available
                    self._update_rate_limit_info(response.headers)
                    
                    return {
                        'success': True,
                        'status_code': response.status,
                        'data': data,
                        'merchant_id': self.merchant_id,
                        'rate_limit_remaining': self.rate_limit_remaining,
                        'environment': self.environment
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'status_code': response.status,
                        'error': error_text
                    }
        
        except Exception as e:
            self.logger.error(f"API access test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def test_authentication(self) -> Dict[str, Any]:
        """
        Test authentication status and return detailed information.
        
        Returns:
            Authentication test results
        """
        try:
            if not self.access_token:
                return {
                    'success': False,
                    'error': 'No access token available',
                    'requires_oauth': True
                }
            
            if not self.merchant_id:
                return {
                    'success': False,
                    'error': 'No merchant ID available',
                    'requires_oauth': True
                }
            
            # Test API access
            api_test = await self.test_api_access()
            
            if api_test['success']:
                return {
                    'success': True,
                    'message': 'Clover authentication successful',
                    'environment': self.environment,
                    'merchant_id': self.merchant_id,
                    'base_url': self.base_url,
                    'api_version': self.api_version,
                    'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
                    'rate_limit_remaining': self.rate_limit_remaining
                }
            else:
                return {
                    'success': False,
                    'error': f"API access failed: {api_test.get('error')}",
                    'status_code': api_test.get('status_code')
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Authentication test failed: {str(e)}"
            }
    
    def _update_rate_limit_info(self, headers: Dict[str, str]):
        """Update rate limit information from response headers."""
        # Clover uses X-RateLimit headers
        if 'X-RateLimit-Remaining' in headers:
            try:
                self.rate_limit_remaining = int(headers['X-RateLimit-Remaining'])
            except ValueError:
                pass
        
        # Update reset time if provided
        if 'X-RateLimit-Reset' in headers:
            try:
                reset_timestamp = int(headers['X-RateLimit-Reset'])
                self.rate_limit_reset_time = datetime.fromtimestamp(reset_timestamp)
            except (ValueError, OSError):
                pass
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information for the authenticated merchant.
        
        Returns:
            Merchant information
        """
        try:
            if not await self.ensure_valid_token():
                raise CloverAuthenticationError("No valid access token")
            
            if not self.merchant_id:
                raise CloverAuthenticationError("No merchant ID available")
            
            session = await self.get_session()
            
            url = f"{self.base_url}/{self.api_version}/merchants/{self.merchant_id}"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    error_text = await response.text()
                    raise CloverAPIError(
                        f"Failed to get merchant info: {error_text}",
                        status_code=response.status
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to get merchant info: {str(e)}")
            raise
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """
        Get devices associated with the merchant.
        
        Returns:
            List of device information
        """
        try:
            if not await self.ensure_valid_token():
                raise CloverAuthenticationError("No valid access token")
            
            session = await self.get_session()
            
            url = f"{self.base_url}/{self.api_version}/merchants/{self.merchant_id}/devices"
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('elements', [])
                else:
                    error_text = await response.text()
                    raise CloverAPIError(
                        f"Failed to get devices: {error_text}",
                        status_code=response.status
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to get devices: {str(e)}")
            raise
    
    async def revoke_token(self) -> bool:
        """
        Revoke the current access token.
        
        Returns:
            True if revocation successful
        """
        try:
            if not self.access_token:
                return True  # Nothing to revoke
            
            session = await self.get_session()
            
            # Clover token revocation endpoint
            revoke_url = f"{self.oauth_base_url}/revoke"
            data = {
                'client_id': self.app_id,
                'client_secret': self.app_secret,
                'token': self.access_token
            }
            
            async with session.post(revoke_url, data=data) as response:
                success = response.status in [200, 204]
                
                if success:
                    self.logger.info("Clover access token revoked successfully")
                    # Clear authentication state
                    self.access_token = None
                    self.merchant_id = None
                    self.token_expires_at = None
                else:
                    error_text = await response.text()
                    self.logger.warning(f"Token revocation failed: {error_text}")
                
                return success
        
        except Exception as e:
            self.logger.error(f"Error during token revocation: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """
        Disconnect and cleanup authentication session.
        
        Returns:
            True if disconnection successful
        """
        try:
            # Revoke token if possible
            revoke_success = await self.revoke_token()
            
            # Clear authentication state
            self.access_token = None
            self.merchant_id = None
            self.token_expires_at = None
            
            # Close HTTP session
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
            
            self.logger.info("Clover authentication session disconnected")
            return revoke_success
        
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            'environment': self.environment,
            'base_url': self.base_url,
            'api_version': self.api_version,
            'merchant_id': self.merchant_id,
            'authenticated': bool(self.access_token),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset_time': self.rate_limit_reset_time.isoformat() if self.rate_limit_reset_time else None,
            'sandbox_mode': self.sandbox
        }