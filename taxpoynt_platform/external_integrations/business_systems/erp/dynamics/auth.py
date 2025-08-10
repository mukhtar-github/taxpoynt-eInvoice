"""
Microsoft Dynamics Authentication Module
Handles connection management and OAuth 2.0 authentication for Microsoft Dynamics 365.
"""

import logging
import base64
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from .exceptions import DynamicsAuthenticationError, DynamicsConnectionError

logger = logging.getLogger(__name__)


class DynamicsAuthenticator:
    """Manages Microsoft Dynamics 365 connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Dynamics authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.base_url = config.get('base_url', '').rstrip('/')
        self.tenant_id = config.get('tenant_id', '')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.resource = config.get('resource', 'https://api.businesscentral.dynamics.com/')
        self.environment = config.get('environment', 'production')
        self.company_id = config.get('company_id', '')
        
        # Microsoft OAuth endpoints
        self.oauth_base_url = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.auth_endpoints = {
            'token': '/oauth2/v2.0/token',
            'authorize': '/oauth2/v2.0/authorize'
        }
        
        # Dynamics API paths
        self.api_paths = {
            'business_central': '/v2.0',
            'finance_ops': '/api/data/v9.1',
            'common_data_service': '/api/data/v9.2'
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
                'User-Agent': 'TaxPoynt-eInvoice-Dynamics-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Dynamics 365 - SI Role Function.
        
        Performs OAuth 2.0 authentication with Microsoft Dynamics 365 using configured
        credentials for System Integrator data access.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Use OAuth 2.0 Client Credentials Grant
            result = await self._oauth_authenticate()
            if result.get('success'):
                self.access_token = result.get('access_token')
                self.token_type = result.get('token_type', 'Bearer')
                
                # Calculate expiration time
                expires_in = result.get('expires_in', 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Successfully authenticated with Microsoft Dynamics 365")
                return True
            else:
                logger.error(f"Dynamics authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Dynamics authentication error: {str(e)}")
            return False
    
    async def _oauth_authenticate(self) -> Dict[str, Any]:
        """Perform OAuth 2.0 Client Credentials Grant."""
        try:
            token_url = urljoin(self.oauth_base_url, self.auth_endpoints['token'])
            
            # Prepare OAuth request
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': f"{self.resource}.default"
            }
            
            headers = {
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
        """Refresh the access token."""
        try:
            # Microsoft Dynamics uses client credentials flow, so we re-authenticate
            return await self.authenticate()
                    
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
    
    async def test_api_access(self, endpoint: str = 'companies') -> Dict[str, Any]:
        """Test access to Microsoft Dynamics API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'companies': f"{self.api_paths['business_central']}/companies",
                'customers': f"{self.api_paths['business_central']}/companies({self.company_id})/customers",
                'vendors': f"{self.api_paths['business_central']}/companies({self.company_id})/vendors",
                'salesInvoices': f"{self.api_paths['business_central']}/companies({self.company_id})/salesInvoices",
                'purchaseInvoices': f"{self.api_paths['business_central']}/companies({self.company_id})/purchaseInvoices"
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['companies']))
            
            headers = await self._get_auth_headers()
            params = {
                '$top': 1  # Minimal query
            }
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': len(data.get('value', [])),
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
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Dynamics disconnect: {str(e)}")
            return False
    
    def get_api_url(self, module: str, endpoint: str) -> str:
        """Get full API URL for a specific module and endpoint."""
        if module not in self.api_paths:
            raise DynamicsConnectionError(f"Unknown Dynamics module: {module}")
        
        base_path = self.api_paths[module]
        return urljoin(self.base_url, f"{base_path}/{endpoint}")
    
    def get_business_central_url(self, endpoint: str) -> str:
        """Get Business Central API URL for an endpoint."""
        if self.company_id:
            base_path = f"{self.api_paths['business_central']}/companies({self.company_id})"
        else:
            base_path = self.api_paths['business_central']
        
        return urljoin(self.base_url, f"{base_path}/{endpoint}")
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'tenant_id': self.tenant_id,
            'environment': self.environment,
            'company_id': self.company_id,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_modules': list(self.api_paths.keys()),
            'client_id': self.client_id
        }