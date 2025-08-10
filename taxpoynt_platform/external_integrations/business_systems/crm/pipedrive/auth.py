"""
Pipedrive Authentication Module
Handles connection management and API key authentication for Pipedrive CRM.
"""

import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import aiohttp

from .exceptions import (
    PipedriveAuthenticationError,
    PipedriveConnectionError,
    PipedriveConfigurationError
)


class PipedriveAuthenticator:
    """
    Handles authentication and connection management for Pipedrive CRM.
    Supports API token authentication and OAuth 2.0 flows.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Pipedrive authenticator.
        
        Args:
            config: Authentication configuration containing:
                - api_token: Pipedrive API token
                - company_domain: Pipedrive company domain
                - auth_method: Authentication method (api_token, oauth2)
                - client_id: OAuth client ID (for OAuth flow)
                - client_secret: OAuth client secret (for OAuth flow)
                - redirect_uri: OAuth redirect URI (for OAuth flow)
        """
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        required_fields = ['company_domain']
        for field in required_fields:
            if not config.get(field):
                raise PipedriveConfigurationError(f"Missing required configuration: {field}")
        
        self.company_domain = config['company_domain']
        self.api_token = config.get('api_token')
        self.auth_method = config.get('auth_method', 'api_token')
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.redirect_uri = config.get('redirect_uri')
        
        # API URLs
        self.base_url = f"https://{self.company_domain}.pipedrive.com/api/v1"
        self.oauth_base_url = "https://oauth.pipedrive.com"
        
        # OAuth endpoints
        self.auth_url = f"{self.oauth_base_url}/oauth/authorize"
        self.token_url = f"{self.oauth_base_url}/oauth/token"
        
        # Token storage for OAuth
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        # Session management
        self.session = None
        
        # Validate authentication method
        if self.auth_method == 'api_token' and not self.api_token:
            raise PipedriveConfigurationError("API token is required for api_token authentication")
        elif self.auth_method == 'oauth2' and not (self.client_id and self.client_secret):
            raise PipedriveConfigurationError("Client ID and secret are required for OAuth2 authentication")

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Pipedrive using configured method.
        
        Returns:
            Authentication response containing access details and metadata
        """
        try:
            if self.auth_method == 'api_token':
                return await self._authenticate_api_token()
            elif self.auth_method == 'oauth2':
                return await self._authenticate_oauth2()
            else:
                raise PipedriveAuthenticationError(f"Unsupported authentication method: {self.auth_method}")
                
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise PipedriveAuthenticationError(f"Authentication failed: {str(e)}")

    async def _authenticate_api_token(self) -> Dict[str, Any]:
        """Authenticate using API token."""
        if not self.api_token:
            raise PipedriveAuthenticationError("API token is required")
        
        # Test the API token by making a simple request
        if await self.validate_connection():
            self.logger.info("Successfully authenticated with Pipedrive using API token")
            return {
                'auth_method': 'api_token',
                'status': 'authenticated',
                'company_domain': self.company_domain,
                'authenticated_at': datetime.now().isoformat()
            }
        else:
            raise PipedriveAuthenticationError("Invalid API token")

    async def _authenticate_oauth2(self) -> Dict[str, Any]:
        """Authenticate using OAuth 2.0 flow."""
        if not self.redirect_uri:
            raise PipedriveAuthenticationError("Redirect URI required for OAuth2 flow")
        
        # Generate authorization URL
        auth_params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'state': 'pipedrive_auth'
        }
        
        from urllib.parse import urlencode
        auth_url = f"{self.auth_url}?{urlencode(auth_params)}"
        
        raise PipedriveAuthenticationError(
            f"OAuth2 flow requires user interaction. "
            f"Direct user to: {auth_url}"
        )

    def get_auth_params(self) -> Dict[str, str]:
        """Get authentication parameters for API requests."""
        if self.auth_method == 'api_token':
            return {'api_token': self.api_token}
        elif self.auth_method == 'oauth2' and self.access_token:
            return {'access_token': self.access_token}
        else:
            raise PipedriveAuthenticationError("No valid authentication available")

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.auth_method == 'oauth2' and self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        return headers

    async def validate_connection(self) -> bool:
        """Validate the connection to Pipedrive."""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test connection with user info request
            test_url = f"{self.base_url}/users/me"
            params = self.get_auth_params()
            headers = self.get_auth_headers()
            
            async with self.session.get(test_url, params=params, headers=headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    if user_data.get('success'):
                        user_info = user_data.get('data', {})
                        self.logger.info(f"Connection validated for user: {user_info.get('name', 'Unknown')}")
                        return True
                    else:
                        self.logger.error("API request unsuccessful")
                        return False
                else:
                    self.logger.error(f"Connection validation failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Connection validation error: {str(e)}")
            return False

    async def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        user_url = f"{self.base_url}/users/me"
        params = self.get_auth_params()
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(user_url, params=params, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        return response_data.get('data', {})
                    else:
                        raise PipedriveAuthenticationError("Failed to get user info: API request unsuccessful")
                else:
                    raise PipedriveAuthenticationError(f"Failed to get user info: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise PipedriveConnectionError(f"Network error getting user info: {str(e)}")

    async def get_company_info(self) -> Dict[str, Any]:
        """Get company information."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        company_url = f"{self.base_url}/companies"
        params = self.get_auth_params()
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(company_url, params=params, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        companies = response_data.get('data', [])
                        if companies:
                            return companies[0]  # Return first company
                        else:
                            return {}
                    else:
                        raise PipedriveAuthenticationError("Failed to get company info: API request unsuccessful")
                else:
                    raise PipedriveAuthenticationError(f"Failed to get company info: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise PipedriveConnectionError(f"Network error getting company info: {str(e)}")

    async def get_currencies(self) -> List[Dict[str, Any]]:
        """Get available currencies."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        currencies_url = f"{self.base_url}/currencies"
        params = self.get_auth_params()
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(currencies_url, params=params, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        return response_data.get('data', [])
                    else:
                        return []
                else:
                    self.logger.warning(f"Failed to get currencies: {response.status}")
                    return []
                    
        except aiohttp.ClientError as e:
            self.logger.warning(f"Network error getting currencies: {str(e)}")
            return []

    async def get_pipelines(self) -> List[Dict[str, Any]]:
        """Get available pipelines."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        pipelines_url = f"{self.base_url}/pipelines"
        params = self.get_auth_params()
        headers = self.get_auth_headers()
        
        try:
            async with self.session.get(pipelines_url, params=params, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        return response_data.get('data', [])
                    else:
                        return []
                else:
                    self.logger.warning(f"Failed to get pipelines: {response.status}")
                    return []
                    
        except aiohttp.ClientError as e:
            self.logger.warning(f"Network error getting pipelines: {str(e)}")
            return []

    async def get_stages(self, pipeline_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get pipeline stages."""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        stages_url = f"{self.base_url}/stages"
        params = self.get_auth_params()
        headers = self.get_auth_headers()
        
        if pipeline_id:
            params['pipeline_id'] = str(pipeline_id)
        
        try:
            async with self.session.get(stages_url, params=params, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('success'):
                        return response_data.get('data', [])
                    else:
                        return []
                else:
                    self.logger.warning(f"Failed to get stages: {response.status}")
                    return []
                    
        except aiohttp.ClientError as e:
            self.logger.warning(f"Network error getting stages: {str(e)}")
            return []

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