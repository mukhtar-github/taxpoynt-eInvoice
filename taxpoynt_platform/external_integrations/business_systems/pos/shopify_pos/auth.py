"""
Shopify POS Authentication Module
Handles connection management and OAuth 2.0 authentication for Shopify POS system.
"""

import logging
import base64
import json
import secrets
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, urljoin

import aiohttp

from .exceptions import ShopifyAuthenticationError, ShopifyConnectionError

logger = logging.getLogger(__name__)


class ShopifyAuthenticator:
    """Manages Shopify POS connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Shopify authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.api_key = config.get('api_key', '')
        self.api_secret = config.get('api_secret', '')
        self.access_token = config.get('access_token', '')
        self.shop_domain = config.get('shop_domain', '')
        self.private_app = config.get('private_app', False)
        
        # Ensure shop domain has proper format
        if self.shop_domain and not self.shop_domain.endswith('.myshopify.com'):
            if '.' not in self.shop_domain:
                self.shop_domain = f"{self.shop_domain}.myshopify.com"
        
        # Shopify API settings
        self.api_version = config.get('api_version', '2023-10')
        self.base_url = f"https://{self.shop_domain}" if self.shop_domain else ""
        
        # OAuth endpoints
        self.auth_endpoints = {
            'authorize': f"https://{self.shop_domain}/admin/oauth/authorize",
            'token': f"https://{self.shop_domain}/admin/oauth/access_token"
        }
        
        # API endpoints
        self.api_endpoints = {
            'admin': f'/admin/api/{self.api_version}',
            'graphql': f'/admin/api/{self.api_version}/graphql.json',
            'locations': f'/admin/api/{self.api_version}/locations.json',
            'orders': f'/admin/api/{self.api_version}/orders.json',
            'transactions': f'/admin/api/{self.api_version}/orders/{{order_id}}/transactions.json',
            'customers': f'/admin/api/{self.api_version}/customers.json',
            'products': f'/admin/api/{self.api_version}/products.json',
            'webhooks': f'/admin/api/{self.api_version}/webhooks.json',
            'pos_sales': f'/admin/api/{self.api_version}/pos_sales.json'
        }
        
        # Required OAuth scopes for POS operations
        self.oauth_scopes = [
            'read_orders',
            'read_products',
            'read_customers',
            'read_locations',
            'read_inventory',
            'read_analytics',
            'read_shopify_payments_payouts',
            'read_shopify_payments_disputes'
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
                'User-Agent': 'TaxPoynt-eInvoice-Shopify-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Shopify POS - SI Role Function.
        
        Supports multiple authentication methods:
        1. Private App access token
        2. OAuth 2.0 access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Validate required configuration
            if not self.shop_domain:
                logger.error("No shop domain configured")
                return False
            
            # Try authentication based on configuration
            if self.private_app and self.access_token:
                result = await self._private_app_authenticate()
            elif self.access_token:
                result = await self._oauth_authenticate()
            else:
                logger.error("No valid authentication method configured")
                return False
            
            if result.get('success'):
                self.current_access_token = result.get('access_token')
                self.token_type = result.get('token_type', 'Bearer')
                
                # For private apps, tokens don't expire
                if self.private_app:
                    self.expires_at = None
                else:
                    # OAuth tokens typically don't expire in Shopify unless revoked
                    self.expires_at = datetime.now() + timedelta(days=365)
                
                logger.info("Successfully authenticated with Shopify POS")
                return True
            else:
                logger.error(f"Shopify authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Shopify authentication error: {str(e)}")
            return False
    
    async def _private_app_authenticate(self) -> Dict[str, Any]:
        """Perform private app authentication."""
        try:
            # Test the access token by making a simple API call
            test_result = await self._test_access_token(self.access_token)
            if test_result:
                return {
                    'success': True,
                    'access_token': self.access_token,
                    'token_type': 'Bearer',
                    'auth_type': 'private_app'
                }
            else:
                return {
                    'success': False,
                    'error': 'Invalid private app access token'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Private app authentication error: {str(e)}'
            }
    
    async def _oauth_authenticate(self) -> Dict[str, Any]:
        """Perform OAuth 2.0 authentication."""
        try:
            # Test the provided access token
            if self.access_token:
                test_result = await self._test_access_token(self.access_token)
                if test_result:
                    return {
                        'success': True,
                        'access_token': self.access_token,
                        'token_type': 'Bearer',
                        'auth_type': 'oauth'
                    }
            
            return {
                'success': False,
                'error': 'No valid OAuth access token available'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'OAuth authentication error: {str(e)}'
            }
    
    async def _test_access_token(self, token: str) -> bool:
        """Test if an access token is valid."""
        try:
            test_url = urljoin(self.base_url, self.api_endpoints['locations'])
            headers = {
                'X-Shopify-Access-Token': token,
                'Accept': 'application/json'
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
            Authorization URL for Shopify OAuth flow
        """
        if not state:
            state = secrets.token_urlsafe(32)
        
        if not scope:
            scope = self.oauth_scopes
        
        params = {
            'client_id': self.api_key,
            'scope': ','.join(scope),
            'redirect_uri': self.config.get('redirect_uri', ''),
            'state': state
        }
        
        base_url = self.auth_endpoints['authorize']
        return f"{base_url}?{urlencode(params)}"
    
    async def exchange_authorization_code(self, authorization_code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
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
                'client_id': self.api_key,
                'client_secret': self.api_secret,
                'code': authorization_code
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
                    self.current_access_token = self.access_token
                    
                    return {
                        'success': True,
                        'access_token': self.access_token,
                        'scope': token_data.get('scope'),
                        'token_type': 'Bearer'
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
        
        # For private apps, tokens don't expire
        if self.private_app:
            return True
        
        # For OAuth apps, check if token is expired
        if self.expires_at and datetime.now() >= (self.expires_at - timedelta(minutes=5)):
            # Shopify OAuth tokens don't have refresh tokens, need to re-authenticate
            return await self.authenticate()
        
        return True
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication without storing credentials."""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Try authentication based on configuration
            if self.private_app and self.access_token:
                auth_result = await self._private_app_authenticate()
            elif self.access_token:
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
        """Test access to Shopify API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'locations': self.api_endpoints['locations'],
                'orders': self.api_endpoints['orders'],
                'customers': self.api_endpoints['customers'],
                'products': self.api_endpoints['products'],
                'webhooks': self.api_endpoints['webhooks']
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['locations']))
            
            headers = await self._get_auth_headers()
            params = {'limit': 1}
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    try:
                        data = await response.json()
                        result_count = 0
                        
                        # Get count based on endpoint
                        if endpoint == 'locations':
                            result_count = len(data.get('locations', []))
                        elif endpoint == 'orders':
                            result_count = len(data.get('orders', []))
                        elif endpoint == 'customers':
                            result_count = len(data.get('customers', []))
                        elif endpoint == 'products':
                            result_count = len(data.get('products', []))
                        elif endpoint == 'webhooks':
                            result_count = len(data.get('webhooks', []))
                        
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
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.current_access_token:
            headers['X-Shopify-Access-Token'] = self.current_access_token
        
        return headers
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid token."""
        if not self.current_access_token:
            return False
        
        # For private apps, tokens don't expire
        if self.private_app:
            return True
        
        # Check if token is expired
        if self.expires_at and datetime.now() >= self.expires_at:
            return False
        
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup session."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear authentication state
            self.current_access_token = None
            self.access_token = None
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Shopify disconnect: {str(e)}")
            return False
    
    def get_api_url(self, endpoint_type: str, action: str = '') -> str:
        """Get full API URL for a specific endpoint type."""
        if endpoint_type not in self.api_endpoints:
            raise ShopifyConnectionError(f"Unknown Shopify API endpoint type: {endpoint_type}")
        
        base_path = self.api_endpoints[endpoint_type]
        
        if action:
            return urljoin(self.base_url, f"{base_path}/{action}")
        else:
            return urljoin(self.base_url, base_path)
    
    def get_graphql_url(self) -> str:
        """Get GraphQL API URL."""
        return urljoin(self.base_url, self.api_endpoints['graphql'])
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'shop_domain': self.shop_domain,
            'api_key': self.api_key,
            'api_version': self.api_version,
            'private_app': self.private_app,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_endpoints': list(self.api_endpoints.keys()),
            'oauth_scopes': self.oauth_scopes,
            'auth_type': 'private_app' if self.private_app else 'oauth'
        }