"""
Microsoft Dynamics CRM Authentication Module
Handles connection management and OAuth 2.0 authentication for Microsoft Dynamics CRM.
"""

import logging
import base64
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode, parse_qs, urlparse

from .exceptions import (
    DynamicsCRMAuthenticationError,
    DynamicsCRMConnectionError,
    DynamicsCRMConfigurationError
)


class DynamicsCRMAuthenticator:
    """
    Handles authentication and connection management for Microsoft Dynamics CRM.
    Supports OAuth 2.0 with various flows including Authorization Code, Client Credentials,
    and On-Behalf-Of flows for both online and on-premise Dynamics instances.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Dynamics CRM authenticator.
        
        Args:
            config: Authentication configuration containing:
                - environment_url: Dynamics CRM environment URL
                - client_id: Azure AD application ID
                - client_secret: Azure AD application secret
                - tenant_id: Azure AD tenant ID
                - resource: Dynamics CRM resource URL
                - auth_flow: Authentication flow (authorization_code, client_credentials, on_behalf_of)
                - redirect_uri: OAuth redirect URI (for authorization code flow)
                - username: Username (for username/password flow)
                - password: Password (for username/password flow)
                - api_version: Dynamics CRM Web API version (default: v9.2)
        """
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        required_fields = ['environment_url', 'client_id', 'tenant_id']
        for field in required_fields:
            if not config.get(field):
                raise DynamicsCRMConfigurationError(f"Missing required configuration: {field}")
        
        self.environment_url = config['environment_url'].rstrip('/')
        self.client_id = config['client_id']
        self.client_secret = config.get('client_secret')
        self.tenant_id = config['tenant_id']
        self.resource = config.get('resource', self.environment_url)
        self.auth_flow = config.get('auth_flow', 'client_credentials')
        self.redirect_uri = config.get('redirect_uri')
        self.username = config.get('username')
        self.password = config.get('password')
        self.api_version = config.get('api_version', 'v9.2')
        
        # Authentication endpoints
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.token_endpoint = f"{self.authority}/oauth2/v2.0/token"
        self.auth_endpoint = f"{self.authority}/oauth2/v2.0/authorize"
        
        # Token storage
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.token_type = "Bearer"
        
        # Session management
        self.session = None

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Microsoft Dynamics CRM using configured flow.
        
        Returns:
            Authentication response containing access token and metadata
        """
        try:
            if self.auth_flow == 'authorization_code':
                return await self._authenticate_authorization_code()
            elif self.auth_flow == 'client_credentials':
                return await self._authenticate_client_credentials()
            elif self.auth_flow == 'password':
                return await self._authenticate_password()
            elif self.auth_flow == 'on_behalf_of':
                return await self._authenticate_on_behalf_of()
            else:
                raise DynamicsCRMAuthenticationError(f"Unsupported authentication flow: {self.auth_flow}")
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise DynamicsCRMAuthenticationError(f"Authentication failed: {str(e)}")

    async def _authenticate_client_credentials(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 Client Credentials flow."""
        if not self.client_secret:
            raise DynamicsCRMAuthenticationError("Client secret required for client credentials flow")
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': f"{self.resource}/.default"
        }
        
        return await self._request_token(data)

    async def _authenticate_password(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 Resource Owner Password Credentials flow."""
        if not self.username or not self.password:
            raise DynamicsCRMAuthenticationError("Username and password required for password flow")
        
        data = {
            'grant_type': 'password',
            'client_id': self.client_id,
            'username': self.username,
            'password': self.password,
            'scope': f"{self.resource}/.default"
        }
        
        if self.client_secret:
            data['client_secret'] = self.client_secret
        
        return await self._request_token(data)

    async def _authenticate_authorization_code(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 Authorization Code flow."""
        if not self.redirect_uri:
            raise DynamicsCRMAuthenticationError("Redirect URI required for authorization code flow")
        
        # This would typically be handled by a web application
        # For demonstration, we'll show how to generate the authorization URL
        auth_params = {
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'scope': f"{self.resource}/.default",
            'state': 'random_state_string'
        }
        
        auth_url = f"{self.auth_endpoint}?{urlencode(auth_params)}"
        
        raise DynamicsCRMAuthenticationError(
            f"Authorization code flow requires user interaction. "
            f"Direct user to: {auth_url}"
        )

    async def _authenticate_on_behalf_of(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 On-Behalf-Of flow."""
        # This would require an assertion token from another service
        raise DynamicsCRMAuthenticationError("On-Behalf-Of flow not implemented")

    async def _request_token(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Request access token from Azure AD."""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                self.token_endpoint,
                data=urlencode(data),
                headers=headers
            ) as response:
                
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error_description', 'Token request failed')
                    raise DynamicsCRMAuthenticationError(f"Token request failed: {error_msg}")
                
                # Store token information
                self.access_token = response_data['access_token']
                self.token_type = response_data.get('token_type', 'Bearer')
                expires_in = response_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                if 'refresh_token' in response_data:
                    self.refresh_token = response_data['refresh_token']
                
                self.logger.info("Successfully authenticated with Microsoft Dynamics CRM")
                
                return {
                    'access_token': self.access_token,
                    'token_type': self.token_type,
                    'expires_in': expires_in,
                    'expires_at': self.token_expires_at.isoformat(),
                    'scope': response_data.get('scope', ''),
                    'resource': self.resource
                }
                
        except aiohttp.ClientError as e:
            raise DynamicsCRMConnectionError(f"Network error during authentication: {str(e)}")

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise DynamicsCRMAuthenticationError("No refresh token available")
        
        data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'refresh_token': self.refresh_token
        }
        
        if self.client_secret:
            data['client_secret'] = self.client_secret
        
        return await self._request_token(data)

    async def get_valid_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not self.access_token:
            await self.authenticate()
            return self.access_token
        
        # Check if token is expired (with 5 minute buffer)
        if self.token_expires_at and datetime.now() >= (self.token_expires_at - timedelta(minutes=5)):
            if self.refresh_token:
                try:
                    await self.refresh_access_token()
                except DynamicsCRMAuthenticationError:
                    # Refresh failed, re-authenticate
                    await self.authenticate()
            else:
                # No refresh token, re-authenticate
                await self.authenticate()
        
        return self.access_token

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.access_token:
            raise DynamicsCRMAuthenticationError("No access token available")
        
        return {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'OData-MaxVersion': '4.0',
            'OData-Version': '4.0'
        }

    async def validate_connection(self) -> bool:
        """Validate the connection to Microsoft Dynamics CRM."""
        try:
            token = await self.get_valid_token()
            if not token:
                return False
            
            # Test connection with a simple OData query
            headers = self.get_auth_headers()
            test_url = f"{self.environment_url}/api/data/{self.api_version}/WhoAmI"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    self.logger.info(f"Connection validated for user: {user_info.get('UserId', 'Unknown')}")
                    return True
                else:
                    self.logger.error(f"Connection validation failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Connection validation error: {str(e)}")
            return False

    async def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user."""
        headers = self.get_auth_headers()
        user_url = f"{self.environment_url}/api/data/{self.api_version}/WhoAmI"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(user_url, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    
                    # Get additional user details
                    user_id = user_data.get('UserId')
                    if user_id:
                        user_detail_url = f"{self.environment_url}/api/data/{self.api_version}/systemusers({user_id})"
                        async with self.session.get(user_detail_url, headers=headers) as detail_response:
                            if detail_response.status == 200:
                                detail_data = await detail_response.json()
                                user_data.update(detail_data)
                    
                    return user_data
                else:
                    raise DynamicsCRMAuthenticationError(f"Failed to get user info: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise DynamicsCRMConnectionError(f"Network error getting user info: {str(e)}")

    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None

    def __del__(self):
        """Cleanup when object is destroyed."""
        if self.session and not self.session.closed:
            # Note: This won't work in async context, better to call close() explicitly
            pass