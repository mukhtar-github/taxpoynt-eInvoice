"""
NetSuite Authentication Module
Handles connection management and OAuth 2.0 authentication for NetSuite ERP.
"""

import logging
import hmac
import hashlib
import base64
import json
import secrets
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, quote

import aiohttp

from .exceptions import NetSuiteAuthenticationError, NetSuiteConnectionError

logger = logging.getLogger(__name__)


class NetSuiteAuthenticator:
    """Manages NetSuite ERP connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize NetSuite authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.account_id = config.get('account_id', '')
        self.consumer_key = config.get('consumer_key', '')
        self.consumer_secret = config.get('consumer_secret', '')
        self.token_id = config.get('token_id', '')
        self.token_secret = config.get('token_secret', '')
        self.base_url = config.get('base_url', '').rstrip('/')
        
        # If base_url not provided, construct from account_id
        if not self.base_url and self.account_id:
            self.base_url = f"https://{self.account_id}.suitetalk.api.netsuite.com"
        
        # NetSuite API paths
        self.api_paths = {
            'restlets': '/services/rest',
            'suitetalk': '/services/NetSuitePort_2021_2',
            'rest_api': '/services/rest/record/v1',
            'suiteql': '/services/rest/query/v1/suiteql',
            'metadata': '/services/rest/system/v1'
        }
        
        # Authentication state
        self.access_token = None
        self.token_type = 'OAuth'
        self.expires_at = None
        self.session = None
        
        # OAuth 1.0a specific
        self.oauth_version = '1.0'
        self.signature_method = 'HMAC-SHA256'
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create an aiohttp session with appropriate settings."""
        timeout = aiohttp.ClientTimeout(total=60, connect=15)
        session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-eInvoice-NetSuite-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with NetSuite ERP - SI Role Function.
        
        Performs OAuth 1.0a authentication with NetSuite using configured
        credentials for System Integrator data access.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # NetSuite uses OAuth 1.0a with Token-Based Authentication (TBA)
            result = await self._oauth_authenticate()
            if result.get('success'):
                self.access_token = f"{self.token_id}"
                self.token_type = 'OAuth'
                
                # NetSuite tokens don't expire but we set a long expiration for consistency
                self.expires_at = datetime.now() + timedelta(days=365)
                
                logger.info("Successfully authenticated with NetSuite ERP")
                return True
            else:
                logger.error(f"NetSuite authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"NetSuite authentication error: {str(e)}")
            return False
    
    async def _oauth_authenticate(self) -> Dict[str, Any]:
        """Perform OAuth 1.0a Token-Based Authentication test."""
        try:
            # Test authentication by making a simple API call
            test_url = urljoin(self.base_url, self.api_paths['metadata'] + '/companies')
            
            # Generate OAuth headers
            oauth_headers = self._generate_oauth_headers('GET', test_url)
            
            async with self.session.get(test_url, headers=oauth_headers) as response:
                if response.status == 200:
                    return {
                        'success': True,
                        'message': 'NetSuite OAuth 1.0a authentication successful'
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'OAuth failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'OAuth authentication error: {str(e)}'
            }
    
    def _generate_oauth_headers(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """Generate OAuth 1.0a headers for NetSuite requests."""
        try:
            # OAuth parameters
            oauth_params = {
                'oauth_consumer_key': self.consumer_key,
                'oauth_token': self.token_id,
                'oauth_signature_method': self.signature_method,
                'oauth_timestamp': str(int(datetime.now().timestamp())),
                'oauth_nonce': secrets.token_hex(16),
                'oauth_version': self.oauth_version
            }
            
            # Create parameter string
            all_params = oauth_params.copy()
            if params:
                all_params.update(params)
            
            # Sort parameters
            sorted_params = sorted(all_params.items())
            param_string = '&'.join([f"{quote(str(k))}={quote(str(v))}" for k, v in sorted_params])
            
            # Create signature base string
            base_string = f"{method.upper()}&{quote(url)}&{quote(param_string)}"
            
            # Create signing key
            signing_key = f"{quote(self.consumer_secret)}&{quote(self.token_secret)}"
            
            # Generate signature
            signature = base64.b64encode(
                hmac.new(
                    signing_key.encode('utf-8'),
                    base_string.encode('utf-8'),
                    hashlib.sha256
                ).digest()
            ).decode('utf-8')
            
            oauth_params['oauth_signature'] = signature
            
            # Create Authorization header
            auth_header_params = []
            for key, value in oauth_params.items():
                auth_header_params.append(f'{quote(key)}="{quote(str(value))}"')
            
            auth_header = f"OAuth {', '.join(auth_header_params)}"
            
            return {
                'Authorization': auth_header,
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
        except Exception as e:
            logger.error(f"Error generating OAuth headers: {str(e)}")
            raise NetSuiteAuthenticationError(f"Error generating OAuth headers: {str(e)}")
    
    async def ensure_valid_token(self) -> bool:
        """Ensure we have valid authentication."""
        if not self.access_token:
            return await self.authenticate()
        
        # NetSuite TBA tokens don't expire, but check if we need to re-authenticate
        if self.expires_at and datetime.now() >= (self.expires_at - timedelta(days=1)):
            return await self.authenticate()
        
        return True
    
    async def test_authentication(self) -> Dict[str, Any]:
        """Test authentication without storing credentials."""
        try:
            if not self.session:
                self.session = await self._create_session()
            
            auth_result = await self._oauth_authenticate()
            return auth_result
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Authentication test failed: {str(e)}'
            }
    
    async def test_api_access(self, endpoint: str = 'companies') -> Dict[str, Any]:
        """Test access to NetSuite API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'companies': f"{self.api_paths['metadata']}/companies",
                'customers': f"{self.api_paths['rest_api']}/customer",
                'vendors': f"{self.api_paths['rest_api']}/vendor",
                'invoices': f"{self.api_paths['rest_api']}/invoice",
                'items': f"{self.api_paths['rest_api']}/item",
                'suiteql': f"{self.api_paths['suiteql']}"
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['companies']))
            
            # Add limit parameter for data endpoints
            params = {}
            if endpoint != 'companies':
                params['limit'] = 1
            
            headers = self._generate_oauth_headers('GET', test_url, params)
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': len(data.get('items', [])) if isinstance(data, dict) else 1,
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
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid credentials."""
        return bool(self.access_token and self.consumer_key and self.token_id)
    
    async def disconnect(self) -> bool:
        """Disconnect and cleanup session."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear authentication state
            self.access_token = None
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during NetSuite disconnect: {str(e)}")
            return False
    
    def get_api_url(self, api_type: str, endpoint: str) -> str:
        """Get full API URL for a specific API type and endpoint."""
        if api_type not in self.api_paths:
            raise NetSuiteConnectionError(f"Unknown NetSuite API type: {api_type}")
        
        base_path = self.api_paths[api_type]
        return urljoin(self.base_url, f"{base_path}/{endpoint}")
    
    def get_rest_api_url(self, record_type: str) -> str:
        """Get REST API URL for a specific record type."""
        return urljoin(self.base_url, f"{self.api_paths['rest_api']}/{record_type}")
    
    def get_suiteql_url(self) -> str:
        """Get SuiteQL API URL."""
        return urljoin(self.base_url, self.api_paths['suiteql'])
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'account_id': self.account_id,
            'consumer_key': self.consumer_key,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_apis': list(self.api_paths.keys()),
            'oauth_version': self.oauth_version,
            'signature_method': self.signature_method
        }