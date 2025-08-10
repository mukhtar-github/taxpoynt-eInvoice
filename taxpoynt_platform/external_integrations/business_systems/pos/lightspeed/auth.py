"""
Lightspeed POS Authentication Module

Handles OAuth 2.0 authentication and API access management for Lightspeed Retail POS integration.
Supports both Lightspeed Retail (R-Series) and Lightspeed Restaurant (K-Series) authentication.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode, parse_qs, urlparse
import aiohttp

from .exceptions import (
    LightspeedAuthenticationError, LightspeedConfigurationError, 
    LightspeedConnectionError, LightspeedAPIError
)

logger = logging.getLogger(__name__)


class LightspeedAuthenticator:
    """
    Lightspeed POS authentication manager for TaxPoynt eInvoice System Integrator functions.
    
    Supports OAuth 2.0 authentication for both Lightspeed Retail and Restaurant APIs.
    Handles token management, refresh, and API access validation.
    
    Lightspeed API Endpoints:
    - Retail (R-Series): https://api.lightspeedapp.com/API/
    - Restaurant (K-Series): https://api.ikentoo.com/
    
    Authentication Features:
    - OAuth 2.0 Authorization Code flow
    - Automatic token refresh
    - Multi-account support (for different locations/businesses)
    - Rate limiting and quota management
    - API version management
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Lightspeed authenticator.
        
        Args:
            config: Configuration dictionary containing Lightspeed credentials and settings
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Lightspeed API configuration
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        self.scope = config.get('scope', 'employee:all')
        
        # API endpoints and version
        self.api_type = config.get('api_type', 'retail')  # 'retail' or 'restaurant'
        self.api_version = config.get('api_version', 'API')
        
        # Set API endpoints based on type
        if self.api_type == 'retail':
            self.base_url = 'https://api.lightspeedapp.com'
            self.oauth_base_url = 'https://cloud.lightspeedapp.com/oauth'
        elif self.api_type == 'restaurant':
            self.base_url = 'https://api.ikentoo.com'
            self.oauth_base_url = 'https://oauth.ikentoo.com'
        else:
            raise LightspeedConfigurationError('api_type', f"Unsupported API type: {self.api_type}")
        
        # Environment settings
        self.sandbox = config.get('sandbox', True)
        if self.sandbox and self.api_type == 'retail':
            self.base_url = 'https://api.lightspeedapp.com'  # Lightspeed doesn't have separate sandbox URL
        
        # Authentication state
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.token_expires_at = None
        self.account_id = config.get('account_id')  # Required for API calls
        
        # Session management
        self.session = None
        self.rate_limit_remaining = 100
        self.rate_limit_reset_time = datetime.now()
        
        # Validate required configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate required configuration parameters."""
        if not self.client_id:
            raise LightspeedConfigurationError('client_id', 'Client ID is required')
        
        if not self.client_secret:
            raise LightspeedConfigurationError('client_secret', 'Client secret is required')
        
        if not self.redirect_uri:
            raise LightspeedConfigurationError('redirect_uri', 'Redirect URI is required')
    
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
        Generate OAuth 2.0 authorization URL for user consent.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL for user redirection
        """
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope
        }
        
        if state:
            params['state'] = state
        
        auth_url = f"{self.oauth_base_url}/authorize?" + urlencode(params)
        self.logger.info(f"Generated Lightspeed OAuth authorization URL")
        
        return auth_url
    
    async def exchange_authorization_code(self, authorization_code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            authorization_code: Authorization code received from OAuth callback
            state: State parameter for verification (if used)
            
        Returns:
            Token response containing access_token, refresh_token, etc.
        """
        try:
            session = await self.get_session()
            
            # Prepare token exchange request
            token_url = f"{self.oauth_base_url}/access_token.php"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri
            }
            
            self.logger.info("Exchanging authorization code for access token")
            
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LightspeedAuthenticationError(
                        f"Token exchange failed: {error_text}",
                        error_code=str(response.status)
                    )
                
                token_data = await response.json()
                
                # Store tokens and expiration
                self.access_token = token_data.get('access_token')
                self.refresh_token = token_data.get('refresh_token')
                
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully obtained Lightspeed access token")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_in': expires_in,
                    'token_type': token_data.get('token_type', 'Bearer'),
                    'scope': token_data.get('scope', self.scope)
                }
        
        except Exception as e:
            self.logger.error(f"Authorization code exchange failed: {str(e)}")
            if isinstance(e, LightspeedAuthenticationError):
                raise
            raise LightspeedAuthenticationError(f"Token exchange error: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            New token data
        """
        if not self.refresh_token:
            raise LightspeedAuthenticationError("No refresh token available")
        
        try:
            session = await self.get_session()
            
            token_url = f"{self.oauth_base_url}/access_token.php"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            self.logger.info("Refreshing Lightspeed access token")
            
            async with session.post(token_url, data=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise LightspeedAuthenticationError(
                        f"Token refresh failed: {error_text}",
                        error_code=str(response.status)
                    )
                
                token_data = await response.json()
                
                # Update stored tokens
                self.access_token = token_data.get('access_token')
                if token_data.get('refresh_token'):  # Some APIs don't return new refresh token
                    self.refresh_token = token_data.get('refresh_token')
                
                expires_in = token_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully refreshed Lightspeed access token")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_in': expires_in,
                    'token_type': token_data.get('token_type', 'Bearer')
                }
        
        except Exception as e:
            self.logger.error(f"Token refresh failed: {str(e)}")
            if isinstance(e, LightspeedAuthenticationError):
                raise
            raise LightspeedAuthenticationError(f"Token refresh error: {str(e)}")
    
    async def ensure_valid_token(self) -> bool:
        """
        Ensure we have a valid access token, refreshing if necessary.
        
        Returns:
            True if valid token is available
        """
        if not self.access_token:
            return False
        
        # Check if token is expired or expiring soon (5 minutes buffer)
        if self.token_expires_at:
            buffer_time = datetime.now() + timedelta(minutes=5)
            if buffer_time >= self.token_expires_at:
                try:
                    await self.refresh_access_token()
                    return True
                except LightspeedAuthenticationError:
                    self.logger.warning("Token refresh failed")
                    return False
        
        return True
    
    async def authenticate(self) -> bool:
        """
        Perform authentication check and setup.
        
        Returns:
            True if authentication is successful
        """
        try:
            # If we have stored tokens, validate them
            if self.access_token:
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
    
    async def test_api_access(self, endpoint: str = 'Account') -> Dict[str, Any]:
        """
        Test API access with current authentication.
        
        Args:
            endpoint: API endpoint to test (default: Account for basic access check)
            
        Returns:
            Test result with success status and details
        """
        try:
            session = await self.get_session()
            
            # Build test URL
            if self.api_type == 'retail':
                if not self.account_id:
                    # First get account info
                    test_url = f"{self.base_url}/{self.api_version}/Account.json"
                else:
                    test_url = f"{self.base_url}/{self.api_version}/Account/{self.account_id}/{endpoint}.json"
            else:  # restaurant
                test_url = f"{self.base_url}/v1/{endpoint}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract account ID if not already set
                    if not self.account_id and self.api_type == 'retail' and endpoint == 'Account':
                        if isinstance(data, dict) and 'Account' in data:
                            accounts = data['Account']
                            if isinstance(accounts, list) and accounts:
                                self.account_id = str(accounts[0].get('accountID'))
                            elif isinstance(accounts, dict):
                                self.account_id = str(accounts.get('accountID'))
                    
                    # Update rate limit info
                    self._update_rate_limit_info(response.headers)
                    
                    return {
                        'success': True,
                        'status_code': response.status,
                        'data': data,
                        'account_id': self.account_id,
                        'rate_limit_remaining': self.rate_limit_remaining
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
            
            # Test API access
            api_test = await self.test_api_access()
            
            if api_test['success']:
                return {
                    'success': True,
                    'message': 'Lightspeed authentication successful',
                    'api_type': self.api_type,
                    'account_id': self.account_id,
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
        # Lightspeed uses different rate limit headers
        if 'X-LS-API-Bucket-Level' in headers:
            # Lightspeed Retail API bucket system
            bucket_level = headers.get('X-LS-API-Bucket-Level')
            if bucket_level:
                try:
                    current_level, max_level = bucket_level.split('/')
                    self.rate_limit_remaining = int(max_level) - int(current_level)
                except (ValueError, IndexError):
                    pass
        
        # Update reset time if provided
        if 'X-LS-API-Drip-Rate' in headers:
            # Drip rate indicates requests per second
            drip_rate = headers.get('X-LS-API-Drip-Rate')
            if drip_rate:
                try:
                    # Estimate next reset based on drip rate
                    self.rate_limit_reset_time = datetime.now() + timedelta(seconds=1)
                except ValueError:
                    pass
    
    async def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information for the authenticated user.
        
        Returns:
            Account information
        """
        try:
            if not await self.ensure_valid_token():
                raise LightspeedAuthenticationError("No valid access token")
            
            session = await self.get_session()
            
            if self.api_type == 'retail':
                url = f"{self.base_url}/{self.api_version}/Account.json"
            else:  # restaurant
                url = f"{self.base_url}/v1/account"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Store account ID if not already set
                    if not self.account_id and self.api_type == 'retail':
                        if isinstance(data, dict) and 'Account' in data:
                            accounts = data['Account']
                            if isinstance(accounts, list) and accounts:
                                self.account_id = str(accounts[0].get('accountID'))
                            elif isinstance(accounts, dict):
                                self.account_id = str(accounts.get('accountID'))
                    
                    return data
                else:
                    error_text = await response.text()
                    raise LightspeedAPIError(
                        f"Failed to get account info: {error_text}",
                        status_code=response.status
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to get account info: {str(e)}")
            raise
    
    async def disconnect(self) -> bool:
        """
        Disconnect and cleanup authentication session.
        
        Returns:
            True if disconnection successful
        """
        try:
            # Clear authentication state
            self.access_token = None
            self.refresh_token = None
            self.token_expires_at = None
            self.account_id = None
            
            # Close HTTP session
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
            
            self.logger.info("Lightspeed authentication session disconnected")
            return True
        
        except Exception as e:
            self.logger.error(f"Error during disconnect: {str(e)}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            'api_type': self.api_type,
            'base_url': self.base_url,
            'account_id': self.account_id,
            'authenticated': bool(self.access_token),
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'rate_limit_remaining': self.rate_limit_remaining,
            'rate_limit_reset_time': self.rate_limit_reset_time.isoformat() if self.rate_limit_reset_time else None
        }