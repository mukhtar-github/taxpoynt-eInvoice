"""
Zoho CRM Authentication Module
Handles connection management and OAuth 2.0 authentication for Zoho CRM.
"""

import logging
import base64
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import aiohttp
from urllib.parse import urlencode, parse_qs, urlparse

from .exceptions import (
    ZohoCRMAuthenticationError,
    ZohoCRMConnectionError,
    ZohoCRMConfigurationError
)


class ZohoCRMAuthenticator:
    """
    Handles authentication and connection management for Zoho CRM.
    Supports OAuth 2.0 with Authorization Code, Self-Client, and Server-based flows.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Zoho CRM authenticator.
        
        Args:
            config: Authentication configuration containing:
                - client_id: Zoho OAuth client ID
                - client_secret: Zoho OAuth client secret
                - redirect_uri: OAuth redirect URI
                - data_center: Zoho data center (us, eu, in, au, jp, ca)
                - scope: OAuth scope (ZohoCRM.modules.ALL, etc.)
                - auth_flow: Authentication flow (authorization_code, self_client)
                - refresh_token: Refresh token (for server-based apps)
                - access_token: Direct access token (for testing)
        """
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        required_fields = ['client_id', 'client_secret']
        for field in required_fields:
            if not config.get(field):
                raise ZohoCRMConfigurationError(f"Missing required configuration: {field}")
        
        self.client_id = config['client_id']
        self.client_secret = config['client_secret']
        self.redirect_uri = config.get('redirect_uri')
        self.data_center = config.get('data_center', 'us')
        self.scope = config.get('scope', 'ZohoCRM.modules.ALL,ZohoCRM.users.READ')
        self.auth_flow = config.get('auth_flow', 'authorization_code')
        
        # Data center URLs
        self.dc_urls = {
            'us': 'https://accounts.zoho.com',
            'eu': 'https://accounts.zoho.eu',
            'in': 'https://accounts.zoho.in',
            'au': 'https://accounts.zoho.com.au',
            'jp': 'https://accounts.zoho.jp',
            'ca': 'https://accounts.zohocloud.ca'
        }
        
        self.api_urls = {
            'us': 'https://www.zohoapis.com',
            'eu': 'https://www.zohoapis.eu',
            'in': 'https://www.zohoapis.in',
            'au': 'https://www.zohoapis.com.au',
            'jp': 'https://www.zohoapis.jp',
            'ca': 'https://www.zohoapis.ca'
        }
        
        # Authentication endpoints
        self.auth_base_url = self.dc_urls.get(self.data_center, self.dc_urls['us'])
        self.api_base_url = self.api_urls.get(self.data_center, self.api_urls['us'])
        
        self.auth_url = f"{self.auth_base_url}/oauth/v2/auth"
        self.token_url = f"{self.auth_base_url}/oauth/v2/token"
        self.revoke_url = f"{self.auth_base_url}/oauth/v2/token/revoke"
        
        # Token storage
        self.access_token = config.get('access_token')
        self.refresh_token = config.get('refresh_token')
        self.token_expires_at = None
        self.token_type = "Zoho-oauthtoken"
        
        # Session management
        self.session = None

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Zoho CRM using configured flow.
        
        Returns:
            Authentication response containing access token and metadata
        """
        try:
            if self.access_token:
                # Use provided access token
                return await self._validate_existing_token()
            elif self.refresh_token:
                # Use refresh token to get access token
                return await self._authenticate_with_refresh_token()
            elif self.auth_flow == 'authorization_code':
                return await self._authenticate_authorization_code()
            elif self.auth_flow == 'self_client':
                return await self._authenticate_self_client()
            else:
                raise ZohoCRMAuthenticationError(f"Unsupported authentication flow: {self.auth_flow}")
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise ZohoCRMAuthenticationError(f"Authentication failed: {str(e)}")

    async def _validate_existing_token(self) -> Dict[str, Any]:
        """Validate existing access token."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {'Authorization': f'Zoho-oauthtoken {self.access_token}'}
        test_url = f"{self.api_base_url}/crm/v2/users"
        
        try:
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    self.logger.info("Existing access token is valid")
                    return {
                        'access_token': self.access_token,
                        'token_type': self.token_type,
                        'status': 'valid_token'
                    }
                else:
                    raise ZohoCRMAuthenticationError("Invalid access token")
        except aiohttp.ClientError as e:
            raise ZohoCRMConnectionError(f"Network error validating token: {str(e)}")

    async def _authenticate_with_refresh_token(self) -> Dict[str, Any]:
        """Authenticate using refresh token."""
        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'refresh_token'
        }
        
        return await self._request_token(data)

    async def _authenticate_authorization_code(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 Authorization Code flow."""
        if not self.redirect_uri:
            raise ZohoCRMAuthenticationError("Redirect URI required for authorization code flow")
        
        # Generate authorization URL
        auth_params = {
            'scope': self.scope,
            'client_id': self.client_id,
            'response_type': 'code',
            'redirect_uri': self.redirect_uri,
            'access_type': 'offline',
            'state': 'zoho_crm_auth'
        }
        
        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"
        
        raise ZohoCRMAuthenticationError(
            f"Authorization code flow requires user interaction. "
            f"Direct user to: {auth_url}"
        )

    async def _authenticate_self_client(self) -> Dict[str, Any]:
        """Authenticate using self-client flow (for server-based applications)."""
        # This would require a grant token obtained from Zoho Developer Console
        raise ZohoCRMAuthenticationError(
            "Self-client flow requires a grant token from Zoho Developer Console"
        )

    async def _request_token(self, data: Dict[str, str]) -> Dict[str, Any]:
        """Request access token from Zoho."""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                self.token_url,
                data=urlencode(data),
                headers=headers
            ) as response:
                
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error', 'Token request failed')
                    raise ZohoCRMAuthenticationError(f"Token request failed: {error_msg}")
                
                # Store token information
                self.access_token = response_data['access_token']
                self.token_type = response_data.get('token_type', 'Zoho-oauthtoken')
                expires_in = response_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                if 'refresh_token' in response_data:
                    self.refresh_token = response_data['refresh_token']
                
                self.logger.info("Successfully authenticated with Zoho CRM")
                
                return {
                    'access_token': self.access_token,
                    'token_type': self.token_type,
                    'expires_in': expires_in,
                    'expires_at': self.token_expires_at.isoformat(),
                    'scope': response_data.get('scope', ''),
                    'api_domain': response_data.get('api_domain', self.api_base_url),
                    'refresh_token': self.refresh_token
                }
                
        except aiohttp.ClientError as e:
            raise ZohoCRMConnectionError(f"Network error during authentication: {str(e)}")

    async def refresh_access_token(self) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        if not self.refresh_token:
            raise ZohoCRMAuthenticationError("No refresh token available")
        
        return await self._authenticate_with_refresh_token()

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
                except ZohoCRMAuthenticationError:
                    # Refresh failed, re-authenticate
                    await self.authenticate()
            else:
                # No refresh token, re-authenticate
                await self.authenticate()
        
        return self.access_token

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        if not self.access_token:
            raise ZohoCRMAuthenticationError("No access token available")
        
        return {
            'Authorization': f'Zoho-oauthtoken {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    async def validate_connection(self) -> bool:
        """Validate the connection to Zoho CRM."""
        try:
            token = await self.get_valid_token()
            if not token:
                return False
            
            # Test connection with user info request
            headers = self.get_auth_headers()
            test_url = f"{self.api_base_url}/crm/v2/users"
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    users = user_data.get('users', [])
                    if users:
                        user_info = users[0]
                        self.logger.info(f"Connection validated for user: {user_info.get('full_name', 'Unknown')}")
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
        user_url = f"{self.api_base_url}/crm/v2/users"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(user_url, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    users = response_data.get('users', [])
                    
                    if users:
                        current_user = None
                        for user in users:
                            if user.get('status') == 'active':
                                current_user = user
                                break
                        
                        if not current_user:
                            current_user = users[0]
                        
                        return current_user
                    else:
                        raise ZohoCRMAuthenticationError("No user information available")
                else:
                    raise ZohoCRMAuthenticationError(f"Failed to get user info: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise ZohoCRMConnectionError(f"Network error getting user info: {str(e)}")

    async def get_organization_info(self) -> Dict[str, Any]:
        """Get organization information."""
        headers = self.get_auth_headers()
        org_url = f"{self.api_base_url}/crm/v2/org"
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.get(org_url, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    return response_data.get('org', [{}])[0]
                else:
                    raise ZohoCRMAuthenticationError(f"Failed to get org info: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise ZohoCRMConnectionError(f"Network error getting org info: {str(e)}")

    async def revoke_token(self) -> bool:
        """Revoke the current access token."""
        if not self.access_token:
            return True
        
        data = {
            'token': self.access_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            async with self.session.post(
                self.revoke_url,
                data=urlencode(data),
                headers=headers
            ) as response:
                
                if response.status == 200:
                    self.access_token = None
                    self.refresh_token = None
                    self.token_expires_at = None
                    self.logger.info("Token revoked successfully")
                    return True
                else:
                    self.logger.warning(f"Token revocation failed: {response.status}")
                    return False
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Error revoking token: {str(e)}")
            return False

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