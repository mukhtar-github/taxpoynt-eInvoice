"""
Xero Accounting Authentication Manager
Handles Xero API authentication including OAuth2 and OpenID Connect.
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
    XeroAuthenticationError,
    XeroConnectionError,
    XeroOrganisationError
)


class XeroAuthManager:
    """
    Manages Xero API authentication using OAuth2 and OpenID Connect.
    
    Handles:
    - OAuth2 authorization code flow
    - Token refresh and management
    - Multi-tenant organization access
    - PKCE security extension
    - OpenID Connect identity verification
    """
    
    # Xero OAuth2 endpoints
    BASE_URL = "https://identity.xero.com"
    AUTHORIZE_URL = f"{BASE_URL}/connect/authorize"
    TOKEN_URL = f"{BASE_URL}/connect/token"
    
    # Xero API base URLs
    API_BASE_URL = "https://api.xero.com"
    CONNECTIONS_URL = f"{API_BASE_URL}/connections"
    
    # OAuth2 configuration
    REQUIRED_SCOPES = [
        "accounting.transactions",
        "accounting.contacts",
        "accounting.settings",
        "offline_access"
    ]
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Xero authentication manager.
        
        Args:
            client_id: Xero app client ID
            client_secret: Xero app client secret
            redirect_uri: OAuth2 redirect URI
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.logger = logging.getLogger(__name__)
        
        # Token storage
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.id_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Organization/tenant management
        self.tenant_id: Optional[str] = None
        self.available_tenants: List[Dict[str, Any]] = []
        
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
                headers={'User-Agent': 'TaxPoynt-Xero-Integration/1.0'}
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
            'redirect_uri': self.redirect_uri,
            'scope': ' '.join(request_scopes),
            'state': state,
            'code_challenge': self.code_challenge,
            'code_challenge_method': 'S256'
        }
        
        auth_url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        self.logger.info(f"Generated Xero authorization URL with scopes: {', '.join(request_scopes)}")
        
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
            XeroAuthenticationError: Token exchange failed
        """
        if not self.code_verifier:
            raise XeroAuthenticationError("PKCE code verifier not found. Authorization flow not initiated properly.")
        
        if not self.session:
            await self.connect()
        
        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'code_verifier': self.code_verifier
        }
        
        # Create basic auth header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/x-www-form-urlencoded'
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
                    raise XeroAuthenticationError(f"Token exchange failed: {error_msg}")
                
                # Store tokens
                self.access_token = response_data['access_token']
                self.refresh_token = response_data.get('refresh_token')
                self.id_token = response_data.get('id_token')
                
                # Calculate expiration
                expires_in = response_data.get('expires_in', 1800)  # Default 30 minutes
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                # Fetch available tenants
                await self._fetch_available_tenants()
                
                self.logger.info(f"Successfully exchanged code for tokens. Found {len(self.available_tenants)} tenants.")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'id_token': self.id_token,
                    'expires_at': self.token_expires_at.isoformat(),
                    'tenants': self.available_tenants
                }
        
        except aiohttp.ClientError as e:
            raise XeroConnectionError(f"Network error during token exchange: {str(e)}")
        except Exception as e:
            raise XeroAuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        
        Returns:
            New token information
            
        Raises:
            XeroAuthenticationError: Token refresh failed
        """
        if not self.refresh_token:
            raise XeroAuthenticationError("No refresh token available")
        
        if not self.session:
            await self.connect()
        
        # Prepare refresh request
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        
        # Create basic auth header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_bytes}',
            'Content-Type': 'application/x-www-form-urlencoded'
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
                    raise XeroAuthenticationError(f"Token refresh failed: {error_msg}")
                
                # Update tokens
                self.access_token = response_data['access_token']
                if 'refresh_token' in response_data:
                    self.refresh_token = response_data['refresh_token']
                
                # Calculate new expiration
                expires_in = response_data.get('expires_in', 1800)
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                self.logger.info("Successfully refreshed access token")
                
                return {
                    'access_token': self.access_token,
                    'refresh_token': self.refresh_token,
                    'expires_at': self.token_expires_at.isoformat()
                }
        
        except aiohttp.ClientError as e:
            raise XeroConnectionError(f"Network error during token refresh: {str(e)}")
        except Exception as e:
            raise XeroAuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def _fetch_available_tenants(self) -> None:
        """Fetch available Xero organizations/tenants."""
        if not self.access_token:
            raise XeroAuthenticationError("No access token available")
        
        if not self.session:
            await self.connect()
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with self.session.get(self.CONNECTIONS_URL, headers=headers) as response:
                if response.status == 200:
                    self.available_tenants = await response.json()
                    
                    # Auto-select first tenant if only one available
                    if len(self.available_tenants) == 1:
                        self.tenant_id = self.available_tenants[0]['tenantId']
                        self.logger.info(f"Auto-selected tenant: {self.available_tenants[0]['tenantName']}")
                    
                elif response.status == 401:
                    raise XeroAuthenticationError("Invalid access token when fetching tenants")
                else:
                    error_data = await response.json()
                    raise XeroConnectionError(f"Failed to fetch tenants: {error_data}")
        
        except aiohttp.ClientError as e:
            raise XeroConnectionError(f"Network error fetching tenants: {str(e)}")
    
    def set_tenant(self, tenant_id: str) -> None:
        """
        Set active tenant/organization.
        
        Args:
            tenant_id: Xero tenant ID to activate
            
        Raises:
            XeroOrganisationError: Invalid tenant ID
        """
        # Verify tenant ID is valid
        valid_tenant_ids = [tenant['tenantId'] for tenant in self.available_tenants]
        
        if tenant_id not in valid_tenant_ids:
            available_tenants = [
                f"{t['tenantName']} ({t['tenantId']})" 
                for t in self.available_tenants
            ]
            raise XeroOrganisationError(
                f"Invalid tenant ID: {tenant_id}. Available tenants: {', '.join(available_tenants)}",
                tenant_id=tenant_id
            )
        
        self.tenant_id = tenant_id
        tenant_name = next(
            t['tenantName'] for t in self.available_tenants 
            if t['tenantId'] == tenant_id
        )
        self.logger.info(f"Set active tenant: {tenant_name} ({tenant_id})")
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of authentication headers
            
        Raises:
            XeroAuthenticationError: No valid token available
        """
        # Check if token needs refresh
        if self._token_needs_refresh():
            await self.refresh_access_token()
        
        if not self.access_token:
            raise XeroAuthenticationError("No access token available")
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Add tenant ID header if set
        if self.tenant_id:
            headers['Xero-tenant-id'] = self.tenant_id
        
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
        tenant_id: Optional[str] = None
    ) -> None:
        """
        Set authentication tokens (for restoring from storage).
        
        Args:
            access_token: OAuth2 access token
            refresh_token: OAuth2 refresh token
            expires_at: Token expiration timestamp (ISO format)
            tenant_id: Xero tenant ID
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        
        if expires_at:
            try:
                self.token_expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except ValueError:
                self.logger.warning(f"Invalid expires_at format: {expires_at}")
                self.token_expires_at = None
        
        # Fetch available tenants if we have a valid token
        if self.access_token:
            try:
                await self._fetch_available_tenants()
                
                # Set tenant if provided and valid
                if tenant_id:
                    self.set_tenant(tenant_id)
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch tenants after setting tokens: {str(e)}")
    
    def get_tenant_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently active tenant.
        
        Returns:
            Tenant information dictionary or None
        """
        if not self.tenant_id:
            return None
        
        for tenant in self.available_tenants:
            if tenant['tenantId'] == self.tenant_id:
                return tenant
        
        return None
    
    def list_available_tenants(self) -> List[Dict[str, Any]]:
        """
        Get list of available tenants/organizations.
        
        Returns:
            List of tenant information dictionaries
        """
        return self.available_tenants.copy()
    
    async def revoke_tokens(self) -> None:
        """Revoke current access and refresh tokens."""
        if not self.access_token:
            return
        
        if not self.session:
            await self.connect()
        
        # Xero doesn't have a standard revocation endpoint
        # Clear tokens locally
        self.access_token = None
        self.refresh_token = None
        self.id_token = None
        self.token_expires_at = None
        self.tenant_id = None
        self.available_tenants = []
        
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
            self.tenant_id is not None and
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
            'active_tenant_id': self.tenant_id,
            'available_tenants_count': len(self.available_tenants),
            'available_tenants': [
                {
                    'id': t['tenantId'],
                    'name': t['tenantName'],
                    'type': t['tenantType']
                }
                for t in self.available_tenants
            ]
        }