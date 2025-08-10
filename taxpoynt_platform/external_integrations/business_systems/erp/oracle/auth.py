"""
Oracle Authentication Module
Handles connection management and OAuth 2.0 authentication for Oracle ERP Cloud.
"""

import logging
import base64
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from .exceptions import OracleAuthenticationError, OracleConnectionError

logger = logging.getLogger(__name__)


class OracleAuthenticator:
    """Manages Oracle ERP Cloud connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Oracle authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.base_url = config.get('base_url', '').rstrip('/')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.scope = config.get('scope', 'urn:opc:fusion:apps:scoped:invoke')
        
        # Oracle-specific endpoints
        self.auth_endpoints = {
            'token': '/oauth/v1/token',
            'authorization': '/oauth/v1/authorization'
        }
        
        # REST API base paths
        self.api_paths = {
            'fscm': '/fscmRestApi/resources/11.13.18.05',  # Financial Supply Chain Management
            'crm': '/crmRestApi/resources/11.13.18.05',    # Customer Relationship Management
            'hcm': '/hcmRestApi/resources/11.13.18.05',    # Human Capital Management
            'ppm': '/ppmRestApi/resources/11.13.18.05'     # Project Portfolio Management
        }
        
        # Authentication state
        self.access_token = None
        self.token_type = 'Bearer'
        self.expires_at = None
        self.refresh_token = None
        self.session = None
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create an aiohttp session with appropriate settings."""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-eInvoice-Oracle-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Oracle ERP Cloud - SI Role Function.
        
        Performs OAuth 2.0 authentication with Oracle ERP Cloud using configured
        credentials for System Integrator data access.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Use OAuth 2.0 Resource Owner Password Credentials Grant
            result = await self._oauth_authenticate()
            if result.get('success'):
                self.access_token = result.get('access_token')
                self.token_type = result.get('token_type', 'Bearer')
                self.refresh_token = result.get('refresh_token')
                
                # Calculate expiration time
                expires_in = result.get('expires_in', 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Successfully authenticated with Oracle ERP Cloud")
                return True
            else:
                logger.error(f"Oracle authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Oracle authentication error: {str(e)}")
            return False
    
    async def _oauth_authenticate(self) -> Dict[str, Any]:
        """Perform OAuth 2.0 Resource Owner Password Credentials Grant."""
        try:
            token_url = urljoin(self.base_url, self.auth_endpoints['token'])
            
            # Prepare OAuth request
            auth_data = {
                'grant_type': 'password',
                'username': self.username,
                'password': self.password,
                'scope': self.scope
            }
            
            # Create basic auth header with client credentials
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return {
                        'success': True,
                        'access_token': token_data.get('access_token'),
                        'token_type': token_data.get('token_type', 'Bearer'),
                        'expires_in': token_data.get('expires_in', 3600),
                        'refresh_token': token_data.get('refresh_token'),
                        'scope': token_data.get('scope', '')
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
    
    async def refresh_access_token(self) -> bool:
        """Refresh the access token using refresh token."""
        try:
            if not self.refresh_token:
                logger.warning("No refresh token available, performing full authentication")
                return await self.authenticate()
            
            token_url = urljoin(self.base_url, self.auth_endpoints['token'])
            
            auth_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
            
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    self.access_token = token_data.get('access_token')
                    self.token_type = token_data.get('token_type', 'Bearer')
                    
                    # Update expiration time
                    expires_in = token_data.get('expires_in', 3600)
                    self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                    
                    # Update refresh token if provided
                    new_refresh_token = token_data.get('refresh_token')
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                    
                    logger.info("Successfully refreshed Oracle access token")
                    return True
                else:
                    logger.error(f"Token refresh failed with status {response.status}")
                    return await self.authenticate()  # Fall back to full authentication
                    
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return await self.authenticate()  # Fall back to full authentication
    
    async def ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token."""
        if not self.access_token:
            return await self.authenticate()
        
        # Check if token is expired (with 5-minute buffer)
        if self.expires_at and datetime.now() >= (self.expires_at - timedelta(minutes=5)):
            return await self.refresh_access_token()
        
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
    
    async def test_api_access(self, endpoint: str = 'invoices') -> Dict[str, Any]:
        """Test access to Oracle REST API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'invoices': f"{self.api_paths['fscm']}/invoices",
                'accounts': f"{self.api_paths['crm']}/accounts", 
                'receivables': f"{self.api_paths['fscm']}/receivables",
                'erpintegrations': f"{self.api_paths['fscm']}/erpintegrations"
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['invoices']))
            
            headers = await self._get_auth_headers()
            params = {
                'limit': 1,  # Minimal query
                'fields': 'InvoiceId'  # Basic field only
            }
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': len(data.get('items', [])),
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
        headers = {}
        
        if self.access_token:
            headers['Authorization'] = f'{self.token_type} {self.access_token}'
        
        return headers
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid token."""
        if not self.access_token:
            return False
        
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
            self.access_token = None
            self.refresh_token = None
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Oracle disconnect: {str(e)}")
            return False
    
    def get_api_url(self, module: str, endpoint: str) -> str:
        """Get full API URL for a specific module and endpoint."""
        if module not in self.api_paths:
            raise OracleConnectionError(f"Unknown Oracle module: {module}")
        
        base_path = self.api_paths[module]
        return urljoin(self.base_url, f"{base_path}/{endpoint}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_modules': list(self.api_paths.keys()),
            'client_id': self.client_id
        }