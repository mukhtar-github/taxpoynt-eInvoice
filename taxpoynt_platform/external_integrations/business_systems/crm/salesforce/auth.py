"""
Salesforce Authentication Module
Handles connection management and OAuth 2.0/JWT authentication for Salesforce CRM.
"""

import logging
import base64
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin

import aiohttp
import jwt

from .exceptions import SalesforceAuthenticationError, SalesforceConnectionError

logger = logging.getLogger(__name__)


class SalesforceAuthenticator:
    """Manages Salesforce CRM connection and authentication."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Salesforce authenticator with configuration."""
        self.config = config
        
        # Extract configuration
        self.instance_url = config.get('instance_url', '').rstrip('/')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.security_token = config.get('security_token', '')
        
        # JWT Bearer Token Flow (for server-to-server)
        self.private_key = config.get('private_key', '')
        self.key_id = config.get('key_id', '')
        
        # Environment settings
        self.environment = config.get('environment', 'production')  # 'production' or 'sandbox'
        self.api_version = config.get('api_version', 'v58.0')
        
        # OAuth endpoints
        if self.environment == 'sandbox':
            self.auth_base_url = 'https://test.salesforce.com'
        else:
            self.auth_base_url = 'https://login.salesforce.com'
        
        self.auth_endpoints = {
            'token': '/services/oauth2/token',
            'revoke': '/services/oauth2/revoke'
        }
        
        # API endpoints
        self.api_endpoints = {
            'sobjects': f'/services/data/{self.api_version}/sobjects',
            'query': f'/services/data/{self.api_version}/query',
            'search': f'/services/data/{self.api_version}/search',
            'composite': f'/services/data/{self.api_version}/composite',
            'limits': f'/services/data/{self.api_version}/limits'
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
                'User-Agent': 'TaxPoynt-eInvoice-Salesforce-Connector/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return session
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Salesforce CRM - SI Role Function.
        
        Supports multiple authentication flows:
        1. JWT Bearer Token Flow (server-to-server)
        2. Username-Password Flow
        3. Client Credentials Flow
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            if not self.session:
                self.session = await self._create_session()
            
            # Try JWT Bearer Token flow first (recommended for server-to-server)
            if self.private_key:
                result = await self._jwt_bearer_authenticate()
            # Fall back to username-password flow
            elif self.username and self.password:
                result = await self._username_password_authenticate()
            # Client credentials flow
            elif self.client_secret:
                result = await self._client_credentials_authenticate()
            else:
                logger.error("No valid authentication method configured")
                return False
            
            if result.get('success'):
                self.access_token = result.get('access_token')
                self.instance_url = result.get('instance_url', self.instance_url)
                self.token_type = result.get('token_type', 'Bearer')
                
                # Calculate expiration time
                expires_in = result.get('expires_in', 3600)
                self.expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Successfully authenticated with Salesforce CRM")
                return True
            else:
                logger.error(f"Salesforce authentication failed: {result.get('error')}")
                return False
                
        except Exception as e:
            logger.error(f"Salesforce authentication error: {str(e)}")
            return False
    
    async def _jwt_bearer_authenticate(self) -> Dict[str, Any]:
        """Perform JWT Bearer Token authentication."""
        try:
            # Create JWT payload
            iat = int(time.time())
            exp = iat + 300  # 5 minutes
            
            payload = {
                'iss': self.client_id,
                'sub': self.username,
                'aud': self.auth_base_url,
                'exp': exp,
                'iat': iat
            }
            
            # Create JWT assertion
            assertion = jwt.encode(payload, self.private_key, algorithm='RS256')
            
            # Prepare token request
            token_url = urljoin(self.auth_base_url, self.auth_endpoints['token'])
            
            auth_data = {
                'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                'assertion': assertion
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
                        'instance_url': token_data.get('instance_url'),
                        'expires_in': 3600  # JWT tokens typically last 1 hour
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'JWT Bearer authentication failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'JWT Bearer authentication error: {str(e)}'
            }
    
    async def _username_password_authenticate(self) -> Dict[str, Any]:
        """Perform Username-Password OAuth flow."""
        try:
            token_url = urljoin(self.auth_base_url, self.auth_endpoints['token'])
            
            auth_data = {
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': self.username,
                'password': f"{self.password}{self.security_token}"
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
                        'instance_url': token_data.get('instance_url'),
                        'expires_in': token_data.get('expires_in', 3600),
                        'refresh_token': token_data.get('refresh_token')
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Username-Password authentication failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Username-Password authentication error: {str(e)}'
            }
    
    async def _client_credentials_authenticate(self) -> Dict[str, Any]:
        """Perform Client Credentials OAuth flow."""
        try:
            token_url = urljoin(self.auth_base_url, self.auth_endpoints['token'])
            
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
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
                        'instance_url': token_data.get('instance_url'),
                        'expires_in': token_data.get('expires_in', 3600)
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Client Credentials authentication failed with status {response.status}: {error_text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Client Credentials authentication error: {str(e)}'
            }
    
    async def refresh_access_token(self) -> bool:
        """Refresh the access token."""
        try:
            if not self.refresh_token:
                # Re-authenticate if no refresh token
                return await self.authenticate()
            
            token_url = urljoin(self.auth_base_url, self.auth_endpoints['token'])
            
            auth_data = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json'
            }
            
            async with self.session.post(token_url, data=auth_data, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get('access_token')
                    self.expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))
                    return True
                else:
                    logger.warning("Token refresh failed, re-authenticating")
                    return await self.authenticate()
                    
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return await self.authenticate()
    
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
            
            # Try to authenticate
            if self.private_key:
                auth_result = await self._jwt_bearer_authenticate()
            elif self.username and self.password:
                auth_result = await self._username_password_authenticate()
            elif self.client_secret:
                auth_result = await self._client_credentials_authenticate()
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
    
    async def test_api_access(self, endpoint: str = 'limits') -> Dict[str, Any]:
        """Test access to Salesforce API endpoints."""
        try:
            if not await self.ensure_valid_token():
                return {
                    'success': False,
                    'error': 'Authentication failed'
                }
            
            # Test specific endpoint
            test_endpoints = {
                'limits': self.api_endpoints['limits'],
                'accounts': f"{self.api_endpoints['sobjects']}/Account",
                'contacts': f"{self.api_endpoints['sobjects']}/Contact",
                'opportunities': f"{self.api_endpoints['sobjects']}/Opportunity",
                'leads': f"{self.api_endpoints['sobjects']}/Lead",
                'query': self.api_endpoints['query']
            }
            
            test_url = urljoin(self.instance_url, test_endpoints.get(endpoint, test_endpoints['limits']))
            
            headers = await self._get_auth_headers()
            params = {}
            
            # Add test query for query endpoint
            if endpoint == 'query':
                params['q'] = 'SELECT Id FROM Account LIMIT 1'
            
            async with self.session.get(test_url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'message': f'{endpoint} API access successful',
                        'record_count': len(data.get('records', [])) if 'records' in data else 1,
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
            # Revoke token if available
            if self.access_token:
                try:
                    revoke_url = urljoin(self.auth_base_url, self.auth_endpoints['revoke'])
                    revoke_data = {'token': self.access_token}
                    async with self.session.post(revoke_url, data=revoke_data):
                        pass  # Don't care about response for revocation
                except Exception:
                    pass  # Ignore revocation errors
            
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear authentication state
            self.access_token = None
            self.expires_at = None
            self.refresh_token = None
            
            return True
            
        except Exception as e:
            logger.error(f"Error during Salesforce disconnect: {str(e)}")
            return False
    
    def get_api_url(self, endpoint: str) -> str:
        """Get full API URL for a specific endpoint."""
        if endpoint not in self.api_endpoints:
            raise SalesforceConnectionError(f"Unknown Salesforce API endpoint: {endpoint}")
        
        api_path = self.api_endpoints[endpoint]
        return urljoin(self.instance_url, api_path)
    
    def get_sobject_url(self, sobject_type: str, record_id: Optional[str] = None) -> str:
        """Get SObject API URL."""
        base_url = urljoin(self.instance_url, f"{self.api_endpoints['sobjects']}/{sobject_type}")
        if record_id:
            return f"{base_url}/{record_id}"
        return base_url
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information."""
        return {
            'instance_url': self.instance_url,
            'client_id': self.client_id,
            'environment': self.environment,
            'api_version': self.api_version,
            'authenticated': self.is_authenticated(),
            'token_expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'available_endpoints': list(self.api_endpoints.keys()),
            'auth_method': 'JWT Bearer' if self.private_key else 'Username-Password' if self.username else 'Client Credentials'
        }