"""
Square POS Authentication Module
Handles connection management and OAuth 2.0 authentication for Square POS system.
"""

import logging
import base64
import json
import secrets
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, urljoin

import aiohttp

from .exceptions import SquareAuthenticationError, SquareConnectionError

logger = logging.getLogger(__name__)


class SquareAuthenticator:
    """Manages Square POS connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Square authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.application_id = config.get('application_id', '')
        self.application_secret = config.get('application_secret', '')
        self.access_token = config.get('access_token', '')
        self.refresh_token = config.get('refresh_token', '')
        self.sandbox = config.get('sandbox', True)
        
        # Square API settings
        self.base_url = 'https://connect.squareupsandbox.com' if self.sandbox else 'https://connect.squareup.com'
        self.api_version = config.get('api_version', '2023-10-18')
        
        # OAuth endpoints
        self.auth_endpoints = {
            'token': f'{self.base_url}/oauth2/token',
            'authorize': f'{self.base_url}/oauth2/authorize',
            'refresh': f'{self.base_url}/oauth2/token',
            'revoke': f'{self.base_url}/oauth2/revoke'
        }
        
        # API endpoints
        self.api_endpoints = {
            'locations': '/v2/locations',
            'payments': '/v2/payments',
            'orders': '/v2/orders',
            'customers': '/v2/customers',
            'catalog': '/v2/catalog',
            'inventory': '/v2/inventory',
            'webhooks': '/v2/webhooks',
            'merchant': '/v2/merchants'
        }
        
        # Required OAuth scopes for POS operations
        self.oauth_scopes = [
            'PAYMENTS_READ',
            'PAYMENTS_WRITE',
            'ORDERS_READ',
            'CUSTOMERS_READ',
            'INVENTORY_READ',
            'MERCHANT_PROFILE_READ',
            'WEBHOOK_SUBSCRIPTION_MANAGEMENT'
        ]
        
        # Authentication state
        self.current_access_token = None
        self.token_type = 'Bearer'
        self.expires_at = None
        self.session = None
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create an aiohttp session with appropriate settings."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-eInvoice-Square-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'Square-Version': self.api_version
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Square POS - SI Role Function.
        
        Supports OAuth 2.0 authentication with access token and refresh token management.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Try OAuth 2.0 flow
            if self.access_token or self.refresh_token:
                result = await self._oauth_authenticate()
            else:
                logger.error("No valid authentication method configured")
                return False
            
            if result.get('success'):
                self.current_access_token = result.get('access_token')
                self.token_type = result.get('token_type', 'Bearer')
                
                # Calculate expiration time
                expires_in = result.get('expires_in', 30 * 24 * 3600)  # Square tokens typically last 30 days
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Store refresh token if provided
                if result.get('refresh_token'):
                    self.refresh_token = result['refresh_token']
                
                logger.info("Successfully authenticated with Square POS")
                return True
            else:
                logger.error(f"Square authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Square authentication error: {str(e)}")
            return False
    
    async def _oauth_authenticate(self) -> Dict[str, Any]:
        """Perform OAuth 2.0 authentication or token refresh."""
        try:
            # If we have an access token, try to use it
            if self.access_token and not self.current_access_token:
                # Validate the provided access token
                test_result = await self._test_access_token(self.access_token)
                if test_result:
                    return {
                        'success': True,
                        'access_token': self.access_token,
                        'token_type': 'Bearer',
                        'expires_in': 30 * 24 * 3600  # 30 days default
                    }
            
            # If we have a refresh token, use it to get a new access token
            if self.refresh_token:
                return await self._refresh_access_token()
            
            # If we have current access token, validate it
            if self.current_access_token:
                test_result = await self._test_access_token(self.current_access_token)
                if test_result:
                    return {
                        'success': True,
                        'access_token': self.current_access_token,
                        'token_type': 'Bearer',
                        'expires_in': 30 * 24 * 3600
                    }
            
            return {
                'success': False,
                'error': 'No valid OAuth tokens available'
            }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'OAuth authentication error: {str(e)}'
            }
    
    async def _refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the OAuth access token."""
        try:
            token_url = self.auth_endpoints['refresh']
            
            auth_data = {
                'grant_type': 'refresh_token',
                'client_id': self.application_id,
                'client_secret': self.application_secret,
                'refresh_token': self.refresh_token
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return {
                        'success': True,
                        'access_token': token_data.get('access_token'),
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'expires_in': token_data.get('expires_in', 30 * 24 * 3600),
                        'refresh_token': token_data.get('refresh_token', self.refresh_token)
                    }
                else:
                    error_text = await response.text()
                    try:
                        error_data = await response.json()
                        errors = error_data.get('errors', [])
                        error_msg = errors[0].get('detail', error_text) if errors else error_text
                    except:
                        error_msg = error_text
                    
                    return {
                        'success': False,
                        'error': f'Token refresh failed with status {response.status}: {error_msg}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Token refresh error: {str(e)}'
            }
    
    async def _test_access_token(self, token: str) -> bool:
        """Test if an access token is valid."""
        try:
            test_url = urljoin(self.base_url, self.api_endpoints['locations'])
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Square-Version': self.api_version
            }
            
            async with self.session.get(test_url, headers=headers) as response:
                return response.status == 200
                
        except Exception:
            return False
    
    def get_oauth_authorization_url(self, state: Optional[str] = None, scope: Optional[List[str]] = None) -> str:
        """
        Generate OAuth authorization URL.
        
        Args:
            state: CSRF protection state parameter
            scope: List of OAuth scopes (defaults to required POS scopes)
        
        Returns:
            Authorization URL for Square OAuth flow
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        if not scope:
            scope = self.oauth_scopes
        
        params = {
            'client_id': self.application_id,
            'scope': ' '.join(scope),
            'session': 'false',
            'state': state
        }
        
        base_url = self.auth_endpoints['authorize']
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Args:
            authorization_code: OAuth authorization code from callback
        
        Returns:
            Token exchange result
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            token_url = self.auth_endpoints['token']
            
            auth_data = {
                'client_id': self.application_id,
                'client_secret': self.application_secret,
                'code': authorization_code,
                'grant_type': 'authorization_code'
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, json=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Update stored tokens
                    self.access_token = token_data.get('access_token')
                    self.refresh_token = token_data.get('refresh_token')
                    self.current_access_token = self.access_token
                    
                    # Calculate expiration
                    expires_in = token_data.get('expires_in', 30 * 24 * 3600)
                    self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    return {
                        'success': True,
                        'access_token': self.access_token,
                        'refresh_token': self.refresh_token,
                        'expires_in': expires_in,
                        'token_type': token_data.get('token_type', 'Bearer')
                    }
                else:
                    error_text = await response.text()
                    try:
                        error_data = await response.json()
                        error_msg = error_data.get('error_description', error_text)
                    except:
                        error_msg = error_text
                    
                    return {
                        'success': False,
                        'error': f'Authorization code exchange failed: {error_msg}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Authorization code exchange error: {str(e)}'
            }
    
    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.current_access_token:
            return await self.authenticate()
        
        # Check if token is expired (with 5-minute buffer)
        if self.expires_at and datetime.now() >= (self.expires_at - timedelta(minutes=5)):
            if self.refresh_token:
                refresh_result = await self._refresh_access_token()
                if refresh_result.get('success'):
                    self.current_access_token = refresh_result.get('access_token')
                    expires_in = refresh_result.get('expires_in', 30 * 24 * 3600)
                    self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    return True
            return await self.authenticate()
        
        return True
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication without storing credentials."""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Try OAuth authentication
            if self.access_token or self.refresh_token:
                auth_result = await self._oauth_authenticate()
            else:
                return {
                    'success': False,
                    'error': 'No valid authentication method configured'
                }
            
            return auth_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Authentication test failed: {str(e)}'
            }
    
    async def test_api_access(self, endpoint: str = 'locations') -> Dict[str, Any]:
        """Test access to Square API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'locations': self.api_endpoints['locations'],
                'payments': f"{self.api_endpoints['payments']}/search",
                'orders': f"{self.api_endpoints['orders']}/search",
                'customers': f"{self.api_endpoints['customers']}/search",
                'catalog': f"{self.api_endpoints['catalog']}/search",
                'merchant': self.api_endpoints['merchant']
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['locations']))
            
            headers = await self._get_auth_headers()
            
            # For search endpoints, we need to POST
            if 'search' in test_url:
                data = {'limit': 1}
                async with self.session.post(test_url, headers=headers, json=data) as response:
                    success = response.status == 200
            else:
                async with self.session.get(test_url, headers=headers) as response:
                    success = response.status == 200
            
            if success:
                try:
                    data = await response.json()
                    result_count = 0
                    if endpoint == 'locations':
                        result_count = len(data.get('locations', []))
                    elif endpoint in ['payments', 'orders', 'customers']:
                        result_count = len(data.get('results', []))
                    
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': result_count,
                        'endpoint': endpoint
                    }
                except:
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'endpoint': endpoint
                    }
            else:
                error_text = await response.text()
                return {
                    'success': False,
                    'error': f'{endpoint} API access failed with status {response.status}: {error_text}'
                }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'{endpoint} API test failed: {str(e)}'
            }
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests."""
        headers = {
            'Square-Version': self.api_version,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.current_access_token:
            headers['Authorization'] = f'{self.token_type} {self.current_access_token}'
        
        return headers
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid token."""
        if not self.current_access_token:
            return False
        
        # Check if token is expired
        if self.expires_at and datetime.now() >= self.expires_at:
            return False
        
        return True
    
    async def revoke_token(self, token: Optional[str] = None) -> bool:
        """
        Revoke access token.
        
        Args:
            token: Token to revoke (defaults to current access token)
        
        Returns:
            True if revocation successful
        """
        try:
            revoke_url = self.auth_endpoints['revoke']
            token_to_revoke = token or self.current_access_token
            
            if not token_to_revoke:
                return False
            
            revoke_data = {
                'client_id': self.application_id,
                'access_token': token_to_revoke
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            async with self.session.post(revoke_url, json=revoke_data, headers=headers) as response:
                success = response.status == 200
                
                if success:
                    # Clear stored tokens if we revoked the current token
                    if token_to_revoke == self.current_access_token:
                        self.current_access_token = None
                        self.access_token = None
                        self.expires_at = None
                
                return success
                
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup session."""
        try:
            # Revoke current token if available
            if self.current_access_token:
                await self.revoke_token()
            
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear authentication state
            self.current_access_token = None
            self.access_token = None
            self.refresh_token = None
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Square disconnect: {str(e)}")
            return False
    
    def get_api_url(self, endpoint_type: str, action: str = '') -> str:
        """Get full API URL for a specific endpoint type."""
        if endpoint_type not in self.api_endpoints:
            raise SquareConnectionError(f"Unknown Square API endpoint type: {endpoint_type}")
        
        base_path = self.api_endpoints[endpoint_type]
        
        if action:
            return urljoin(self.base_url, f"{base_path}/{action}")
        else:
            return urljoin(self.base_url, base_path)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'application_id': self.application_id,
            'api_version': self.api_version,
            'sandbox': self.sandbox,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_endpoints': list(self.api_endpoints.keys()),
            'oauth_scopes': self.oauth_scopes,
            'has_refresh_token': bool(self.refresh_token)
        }