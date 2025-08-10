"""
HubSpot Authentication Module
Handles connection management and OAuth 2.0 authentication for HubSpot CRM.
"""

import logging
import base64
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp

from .exceptions import HubSpotAuthenticationError, HubSpotConnectionError

logger = logging.getLogger(__name__)


class HubSpotAuthenticator:
    """Manages HubSpot CRM connection and OAuth 2.0 authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize HubSpot authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.access_token = config.get('access_token', '')
        self.refresh_token = config.get('refresh_token', '')
        self.api_key = config.get('api_key', '')  # For API key authentication
        
        # HubSpot API settings
        self.base_url = 'https://api.hubapi.com'
        self.api_version = config.get('api_version', 'v3')
        
        # OAuth endpoints
        self.auth_endpoints = {
            'token': 'https://api.hubapi.com/oauth/v1/token',
            'authorize': 'https://app.hubspot.com/oauth/authorize',
            'refresh': 'https://api.hubapi.com/oauth/v1/token'
        }
        
        # API endpoints
        self.api_endpoints = {
            'crm_objects': f'/crm/{self.api_version}/objects',
            'crm_properties': f'/crm/{self.api_version}/properties',
            'crm_associations': f'/crm/{self.api_version}/associations',
            'crm_pipelines': f'/crm/{self.api_version}/pipelines',
            'crm_search': f'/crm/{self.api_version}/objects',
            'integrations': f'/integrations/{self.api_version}',
            'webhooks': f'/webhooks/{self.api_version}'
        }
        
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
                'User-Agent': 'TaxPoynt-eInvoice-HubSpot-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with HubSpot CRM - SI Role Function.
        
        Supports multiple authentication methods:
        1. OAuth 2.0 Access Token (with refresh)
        2. API Key authentication
        3. Private App access token
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Try OAuth 2.0 flow first
            if self.access_token or self.refresh_token:
                result = await self._oauth_authenticate()
            # Fall back to API key authentication
            elif self.api_key:
                result = await self._api_key_authenticate()
            else:
                logger.error("No valid authentication method configured")
                return False
            
            if result.get('success'):
                self.current_access_token = result.get('access_token')
                self.token_type = result.get('token_type', 'Bearer')
                
                # Calculate expiration time
                expires_in = result.get('expires_in', 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Store refresh token if provided
                if result.get('refresh_token'):
                    self.refresh_token = result['refresh_token']
                
                logger.info("Successfully authenticated with HubSpot CRM")
                return True
            else:
                logger.error(f"HubSpot authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"HubSpot authentication error: {str(e)}")
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
                        'expires_in': 3600  # Default expiration
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
                        'expires_in': 3600
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
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token
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
                        'refresh_token': token_data.get('refresh_token', self.refresh_token)
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Token refresh failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Token refresh error: {str(e)}'
            }
    
    async def _api_key_authenticate(self) -> Dict[str, Any]:
        """Perform API key authentication."""
        try:
            # Test API key by making a simple request
            test_url = urljoin(self.base_url, f"{self.api_endpoints['crm_objects']}/contacts")
            params = {
                'hapikey': self.api_key,
                'limit': 1
            }
            
            async with self.session.get(test_url, params=params) as response:
                if response.status == 200:
                    return {
                        'success': True,
                        'access_token': self.api_key,
                        'token_type': 'API-Key',
                        'expires_in': 86400  # API keys don't expire but set long duration
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'API key authentication failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'API key authentication error: {str(e)}'
            }
    
    async def _test_access_token(self, token: str) -> bool:
        """Test if an access token is valid."""
        try:
            test_url = urljoin(self.base_url, f"{self.api_endpoints['crm_objects']}/contacts")
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }
            params = {'limit': 1}
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                return response.status == 200
                
        except Exception:
            return False
    
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
                    self.expires_at = datetime.now() + timedelta(seconds=refresh_result.get('expires_in', 3600))
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
            # Try API key authentication
            elif self.api_key:
                auth_result = await self._api_key_authenticate()
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
    
    async def test_api_access(self, endpoint: str = 'contacts') -> Dict[str, Any]:
        """Test access to HubSpot API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'contacts': f"{self.api_endpoints['crm_objects']}/contacts",
                'companies': f"{self.api_endpoints['crm_objects']}/companies",
                'deals': f"{self.api_endpoints['crm_objects']}/deals",
                'products': f"{self.api_endpoints['crm_objects']}/products",
                'pipelines': f"{self.api_endpoints['crm_pipelines']}/deals"
            }
            
            test_url = urljoin(self.base_url, test_endpoints.get(endpoint, test_endpoints['contacts']))
            
            headers = await self._get_auth_headers()
            params = {'limit': 1}
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': len(data.get('results', [])),
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
        
        if self.current_access_token:
            if self.token_type == 'API-Key':
                # API key authentication uses query parameter, not header
                headers['Accept'] = 'application/json'
            else:
                headers['Authorization'] = f'{self.token_type} {self.current_access_token}'
        
        return headers
    
    def get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for requests (for API key auth)."""
        params = {}
        
        if self.token_type == 'API-Key' and self.current_access_token:
            params['hapikey'] = self.current_access_token
        
        return params
    
    def is_authenticated(self) -> bool:
        """Check if authenticated with valid token."""
        if not self.current_access_token:
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
            self.current_access_token = None
            self.expires_at = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during HubSpot disconnect: {str(e)}")
            return False
    
    def get_api_url(self, endpoint_type: str, object_type: str = '', action: str = '') -> str:
        """Get full API URL for a specific endpoint type and object."""
        if endpoint_type not in self.api_endpoints:
            raise HubSpotConnectionError(f"Unknown HubSpot API endpoint type: {endpoint_type}")
        
        base_path = self.api_endpoints[endpoint_type]
        
        if object_type:
            if action:
                return urljoin(self.base_url, f"{base_path}/{object_type}/{action}")
            else:
                return urljoin(self.base_url, f"{base_path}/{object_type}")
        else:
            return urljoin(self.base_url, base_path)
    
    def get_crm_object_url(self, object_type: str, object_id: Optional[str] = None, action: Optional[str] = None) -> str:
        """Get CRM object API URL."""
        base_url = urljoin(self.base_url, f"{self.api_endpoints['crm_objects']}/{object_type}")
        
        if object_id:
            if action:
                return f"{base_url}/{object_id}/{action}"
            else:
                return f"{base_url}/{object_id}"
        else:
            return base_url
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'base_url': self.base_url,
            'client_id': self.client_id,
            'api_version': self.api_version,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_endpoints': list(self.api_endpoints.keys()),
            'auth_method': self.token_type,
            'has_refresh_token': bool(self.refresh_token)
        }