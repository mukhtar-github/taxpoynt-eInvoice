"""
Sage Business Cloud Accounting Authentication Manager
Handles Sage API authentication including OAuth2 and business selection.
"""
import asyncio
import logging
import base64
import hashlib
import secrets
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from urllib.parse import urlencode, parse_qs
import aiohttp

from .exceptions import (
    SageAuthenticationError,
    SageConnectionError,
    SageBusinessError
)


class SageAuthManager:
    """
    Manages Sage Business Cloud Accounting API authentication using OAuth2.
    
    Handles:
    - OAuth2 authorization code flow
    - Token refresh and management
    - Multi-business access
    - PKCE security extension
    - Business selection and management
    """
    
    # Sage OAuth2 endpoints
    BASE_URL = "https://www.sageone.com"
    AUTHORIZE_URL = f"{BASE_URL}/oauth2/auth/central"
    TOKEN_URL = f"{BASE_URL}/oauth2/auth/central/token"
    
    # Sage API base URLs
    API_BASE_URL = "https://api.accounting.sage.com/v3.1"
    
    # OAuth2 configuration
    REQUIRED_SCOPES = [
        "full_access"  # Sage uses simplified scope model
    ]
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Sage authentication manager.
        
        Args:
            client_id: Sage app client ID
            client_secret: Sage app client secret
            redirect_uri: OAuth2 redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_ui = redirect_uri
        self.logger = logging.getLogger(__name__)
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Business management
        self.business_id: Optional[str] = None
        self.available_businesses: List[Dict[str, Any]] = []
        
        # PKCE parameters
        self.code_verifier: Optional[str] = None
        self.code_challenge: Optional[str] = None
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self) -> None:
        """Initialize HTTP session."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'User-Agent': 'TaxPoynt-Sage-Integration/1.0'}
            )
    
    async def disconnect(self) -> None:
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _generate_pkce_parameters(self) -> None:
        """Generate PKCE code verifier and challenge for OAuth2 security."""
        # Generate code verifier (43-128 characters)
        self.code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode('utf-8').rstrip('=')
        
        # Generate code challenge
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
    
    def get_authorization_url(self, state: str, scopes: Optional[List[str]] = None) -> str:
        """
        Generate OAuth2 authorization URL.
        
        Args:
            state: OAuth2 state parameter for CSRF protection
            scopes: Optional custom scopes (defaults to required scopes)
            
        Returns:
            Authorization URL for user redirection
        """
        self._generate_pkce_parameters()
        
        # Use provided scopes or default required scopes
        request_scopes = scopes or self.REQUIRED_SCOPES
        
        params = {
            'response_type': 'code',
            'client_id': self.client_id,
            'redirect_uri': self.redirect_ui,
            'scope': ' '.join(request_scopes),
            'state': state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        self.logger.info(f"Generated Sage authorization URL with scopes: {', '.join(request_scopes)}")
        
        return auth_url
    
    async def exchange_code_for_tokens(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access tokens.
        
        Args:
            authorization_code: OAuth2 authorization code
            state: OAuth2 state parameter
            
        Returns:
            Token information dictionary
            
        Raises:
            SageAuthenticationError: Token exchange failed
        """
        if not self.code_verifier:
            raise SageAuthenticationError("PKCE code verifier not found. Authorization flow not initiated properly.")
        
        if not self.session:
            await self.connect()
        
        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': authorization_code,
            'redirect_uri': self.redirect_ui,
            'code_verifier': self.code_verifier
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            async with self.session.post(
                self.TOKEN_URL,
                data=token_data,
                headers=headers
            ) as response:
                
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error_description', 'Token exchange failed')
                    raise SageAuthenticationError(f"Token exchange failed: {error_msg}")
                
                # Store tokens
                self.access_token = response_data['access_token']
                self.refresh_token = response_data.get('refresh_token')
                
                # Calculate expiration
                expires_in = response_data.get('expires_in', 3600)  # Default 1 hour
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Fetch available businesses
                await self._fetch_available_businesses()
                
                self.logger.info(f"Successfully exchanged code for tokens. Found {len(self.available_businesses)} businesses.")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_at': self.token_expires_at.isoformat(),
                    'businesses': self.available_businesses
                }
        
        except aiohttp.ClientError as e:
            raise SageConnectionError(f"Network error during token exchange: {str(e)}")
        except Exception as e:
            raise SageAuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token information
            
        Raises:
            SageAuthenticationError: Token refresh failed
        """
        if not self.refresh_token:
            raise SageAuthenticationError("No refresh token available")
        
        if not self.session:
            await self.connect()
        
        # Prepare refresh request
        token_data = {
            'grant_type': 'refresh_token',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            async with self.session.post(
                self.TOKEN_URL,
                data=token_data,
                headers=headers
            ) as response:
                
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error_description', 'Token refresh failed')
                    raise SageAuthenticationError(f"Token refresh failed: {error_msg}")
                
                # Update tokens
                self.access_token = response_data['access_token']
                if 'refresh_token' in response_data:
                    self.refresh_token = response_data['refresh_token']
                
                # Calculate new expiration
                expires_in = response_data.get('expires_in', 3600)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully refreshed access token")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_at': self.token_expires_at.isoformat()
                }
        
        except aiohttp.ClientError as e:
            raise SageConnectionError(f"Network error during token refresh: {str(e)}")
        except Exception as e:
            raise SageAuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def _fetch_available_businesses(self) -> None:
        """Fetch available Sage businesses."""
        if not self.access_token:
            raise SageAuthenticationError("No access token available")
        
        if not self.session:
            await self.connect()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json'
        }
        
        # Sage businesses endpoint
        businesses_url = f"{self.API_BASE_URL}/businesses"
        
        try:
            async with self.session.get(businesses_url, headers=headers) as response:
                if response.status == 200:
                    response_data = await response.json()
                    self.available_businesses = response_data.get('$items', [])
                    
                    # Auto-select first business if only one available
                    if len(self.available_businesses) == 1:
                        self.business_id = self.available_businesses[0]['id']
                        business_name = self.available_businesses[0].get('name', 'Unknown')
                        self.logger.info(f"Auto-selected business: {business_name}")
                    
                elif response.status == 401:
                    raise SageAuthenticationError("Invalid access token when fetching businesses")
                else:
                    error_data = await response.json()
                    raise SageConnectionError(f"Failed to fetch businesses: {error_data}")
        
        except aiohttp.ClientError as e:
            raise SageConnectionError(f"Network error fetching businesses: {str(e)}")
    
    def set_business(self, business_id: str) -> None:
        """
        Set active business.
        
        Args:
            business_id: Sage business ID to activate
            
        Raises:
            SageBusinessError: Invalid business ID
        """
        # Verify business ID is valid
        valid_business_ids = [business['id'] for business in self.available_businesses]
        
        if business_id not in valid_business_ids:
            available_businesses = [
                f"{b.get('name', 'Unknown')} ({b['id']})" 
                for b in self.available_businesses
            ]
            raise SageBusinessError(
                f"Invalid business ID: {business_id}. Available businesses: {', '.join(available_businesses)}",
                business_id=business_id
            )
        
        self.business_id = business_id
        business_name = next(
            b.get('name', 'Unknown') for b in self.available_businesses 
            if b['id'] == business_id
        )
        self.logger.info(f"Set active business: {business_name} ({business_id})")
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of authentication headers
            
        Raises:
            SageAuthenticationError: No valid token available
            SageBusinessError: No business selected
        """
        # Check if token needs refresh
        if self._token_needs_refresh():
            await self.refresh_access_token()
        
        if not self.access_token:
            raise SageAuthenticationError("No access token available")
        
        if not self.business_id:
            raise SageBusinessError("No business selected. Call set_business() first.")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def _token_needs_refresh(self) -> bool:
        """Check if access token needs to be refreshed."""
        if not self.token_expires_at:
            return True
        
        # Refresh if token expires within 5 minutes
        return datetime.now() + timedelta(minutes=5) >= self.token_expires_at
    
    async def set_tokens(
        self,
        access_token: str,
        refresh_token: str,
        expires_at: Optional[str] = None,
        business_id: Optional[str] = None
    ) -> None:
        """
        Set authentication tokens (for restoring from storage).
        
        Args:
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            expires_at: Token expiration timestamp (ISO format)
            business_id: Sage business ID
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        if expires_at:
            try:
                self.token_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid expires_at format: {expires_at}")
                self.token_expires_at = None
        
        # Fetch available businesses if we have a valid token
        if self.access_token:
            try:
                await self._fetch_available_businesses()
                
                # Set business if provided and valid
                if business_id:
                    self.set_business(business_id)
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch businesses after setting tokens: {str(e)}")
    
    def get_business_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently active business.
        
        Returns:
            Business information dictionary or None
        """
        if not self.business_id:
            return None
        
        for business in self.available_businesses:
            if business['id'] == self.business_id:
                return business
        
        return None
    
    def list_available_businesses(self) -> List[Dict[str, Any]]:
        """
        Get list of available businesses.
        
        Returns:
            List of business information dictionaries
        """
        return self.available_businesses.copy()
    
    async def revoke_tokens(self) -> None:
        """Revoke current access and refresh tokens."""
        if not self.access_token:
            return
        
        # Sage doesn't have a standard revocation endpoint
        # Clear tokens locally
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.business_id = None
        self.available_businesses = []
        
        self.logger.info("Tokens revoked and cleared")
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated with valid tokens.
        
        Returns:
            True if authenticated
        """
        return (
            self.access_token is not None and
            self.refresh_token is not None and
            self.business_id is not None and
            not self._token_needs_refresh()
        )
    
    def get_auth_status(self) -> Dict[str, Any]:
        """
        Get current authentication status.
        
        Returns:
            Authentication status information
        """
        return {
            'authenticated': self.is_authenticated(),
            'has_access_token': self.access_token is not None,
            'has_refresh_token': self.refresh_token is not None,
            'token_expires_at': self.token_expires_at.isoformat() if self.token_expires_at else None,
            'token_needs_refresh': self._token_needs_refresh(),
            'active_business_id': self.business_id,
            'available_businesses_count': len(self.available_businesses),
            'available_businesses': [
                {
                    'id': b['id'],
                    'name': b.get('name', 'Unknown'),
                    'country': b.get('country', ''),
                    'currency': b.get('base_currency', {}).get('currency_code', ''),
                    'subscription_type': b.get('subscription_type', ''),
                    'active': b.get('active', True)
                }
                for b in self.available_businesses
            ]
        }
    
    def get_business_url(self, endpoint: str) -> str:
        """
        Build business-specific API URL.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            Full business-specific URL
            
        Raises:
            SageBusinessError: No business selected
        """
        if not self.business_id:
            raise SageBusinessError("No business selected. Call set_business() first.")
        
        # Remove leading slash if present
        endpoint = endpoint.lstrip('/')
        
        return f"{self.API_BASE_URL}/businesses/{self.business_id}/{endpoint}"
    
    async def test_business_access(self, business_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Test access to a specific business.
        
        Args:
            business_id: Business ID to test (uses current business if None)
            
        Returns:
            Test results
        """
        test_business_id = business_id or self.business_id
        
        if not test_business_id:
            return {
                'success': False,
                'error': 'No business ID provided'
            }
        
        if not self.session:
            await self.connect()
        
        headers = await self.get_auth_headers()
        test_url = f"{self.API_BASE_URL}/businesses/{test_business_id}"
        
        try:
            async with self.session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    business_data = await response.json()
                    return {
                        'success': True,
                        'business_id': test_business_id,
                        'business_data': business_data
                    }
                else:
                    error_data = await response.json()
                    return {
                        'success': False,
                        'business_id': test_business_id,
                        'status_code': response.status,
                        'error': error_data
                    }
        
        except Exception as e:
            return {
                'success': False,
                'business_id': test_business_id,
                'error': str(e)
            }