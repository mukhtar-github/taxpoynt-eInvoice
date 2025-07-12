"""
SAP OAuth 2.0 Authentication Module for TaxPoynt eInvoice

This module provides enterprise-grade OAuth 2.0 authentication for SAP S/4HANA
systems with token management, refresh capabilities, and security features.

Features:
- OAuth 2.0 Client Credentials flow
- OAuth 2.0 Authorization Code flow (for user delegation)
- Automatic token refresh
- Token caching and storage
- Security validation
- Error handling and retry logic
- Multi-tenant support

SAP OAuth Endpoints:
- Token Endpoint: /sap/bc/sec/oauth2/token
- Authorization Endpoint: /sap/bc/sec/oauth2/authorize
- Token Info Endpoint: /sap/bc/sec/oauth2/tokeninfo
- Revocation Endpoint: /sap/bc/sec/oauth2/revoke
"""

import aiohttp
import asyncio
import base64
import hashlib
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode, quote_plus
import jwt

logger = logging.getLogger(__name__)


class SAPOAuthError(Exception):
    """Base exception for SAP OAuth errors"""
    pass


class SAPTokenExpiredError(SAPOAuthError):
    """Exception raised when SAP OAuth token is expired"""
    pass


class SAPAuthenticationError(SAPOAuthError):
    """Exception raised for SAP authentication failures"""
    pass


class SAPOAuthClient:
    """
    SAP OAuth 2.0 client for enterprise authentication
    
    Provides OAuth 2.0 authentication capabilities for SAP S/4HANA systems
    with proper token management, security, and enterprise features.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SAP OAuth client
        
        Args:
            config: OAuth configuration parameters
        """
        # SAP system configuration
        self.host = config.get('host', '')
        self.port = config.get('port', 443)
        self.use_https = config.get('use_https', True)
        self.verify_ssl = config.get('verify_ssl', True)
        
        # OAuth configuration
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.scope = config.get('scope', 'API_BILLING_DOCUMENT_SRV_0001 API_BUSINESS_PARTNER_0001')
        self.redirect_uri = config.get('redirect_uri', '')
        
        # Flow configuration
        self.grant_type = config.get('grant_type', 'client_credentials')
        self.response_type = config.get('response_type', 'code')
        
        # Token management
        self.access_token = None
        self.refresh_token = None
        self.token_type = 'Bearer'
        self.expires_at = None
        self.token_scope = None
        
        # Security settings
        self.state = None
        self.code_verifier = None
        self.code_challenge = None
        self.nonce = None
        
        # Session management
        self.session = None
        self.timeout = config.get('timeout', 30)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 1)
        
        # Build base URL and endpoints
        self.base_url = self._build_base_url()
        self.endpoints = {
            'token': '/sap/bc/sec/oauth2/token',
            'authorize': '/sap/bc/sec/oauth2/authorize',
            'tokeninfo': '/sap/bc/sec/oauth2/tokeninfo',
            'revoke': '/sap/bc/sec/oauth2/revoke',
            'userinfo': '/sap/bc/sec/oauth2/userinfo'
        }
        
        logger.info(f"Initialized SAP OAuth client for {self.host}")
    
    def _build_base_url(self) -> str:
        """Build base URL for SAP OAuth endpoints"""
        protocol = 'https' if self.use_https else 'http'
        if self.port in [80, 443]:
            return f"{protocol}://{self.host}"
        return f"{protocol}://{self.host}:{self.port}"
    
    async def _create_session(self) -> aiohttp.ClientSession:
        """Create aiohttp session for OAuth requests"""
        if self.session and not self.session.closed:
            return self.session
        
        # Configure SSL
        ssl_context = None
        if self.use_https:
            import ssl as ssl_module
            ssl_context = ssl_module.create_default_context()
            if not self.verify_ssl:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl_module.CERT_NONE
        
        # Configure connector
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        # Configure timeout
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        # Create session
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'TaxPoynt-SAP-OAuth/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )
        
        return self.session
    
    def generate_state(self) -> str:
        """Generate secure state parameter for OAuth flow"""
        self.state = secrets.token_urlsafe(32)
        return self.state
    
    def generate_pkce_pair(self) -> Tuple[str, str]:
        """Generate PKCE code verifier and challenge pair"""
        # Generate code verifier (43-128 characters, URL-safe)
        self.code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
        
        # Generate code challenge (SHA256 hash of verifier, base64url encoded)
        challenge_bytes = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        self.code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('utf-8').rstrip('=')
        
        return self.code_verifier, self.code_challenge
    
    def generate_nonce(self) -> str:
        """Generate nonce for OpenID Connect"""
        self.nonce = secrets.token_urlsafe(16)
        return self.nonce
    
    def build_authorization_url(self, **extra_params) -> str:
        """
        Build authorization URL for OAuth 2.0 authorization code flow
        
        Args:
            **extra_params: Additional parameters for authorization request
            
        Returns:
            Authorization URL
        """
        # Generate security parameters
        state = self.generate_state()
        code_verifier, code_challenge = self.generate_pkce_pair()
        nonce = self.generate_nonce()
        
        # Build authorization parameters
        auth_params = {
            'response_type': self.response_type,
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'scope': self.scope,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
            'nonce': nonce
        }
        
        # Add extra parameters
        auth_params.update(extra_params)
        
        # Build URL
        auth_url = f"{self.base_url}{self.endpoints['authorize']}?{urlencode(auth_params)}"
        
        logger.info(f"Generated authorization URL with state: {state}")
        return auth_url
    
    async def exchange_code_for_token(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for validation
            
        Returns:
            Token response data
        """
        # Validate state parameter
        if state != self.state:
            raise SAPAuthenticationError(f"Invalid state parameter: {state}")
        
        session = await self._create_session()
        
        # Prepare token request
        token_data = {
            'grant_type': 'authorization_code',
            'code': authorization_code,
            'redirect_uri': self.redirect_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code_verifier': self.code_verifier
        }
        
        # Make token request
        token_response = await self._make_token_request(session, token_data)
        
        if token_response['success']:
            self._store_tokens(token_response['data'])
            logger.info("Successfully exchanged authorization code for tokens")
        
        return token_response
    
    async def get_client_credentials_token(self) -> Dict[str, Any]:
        """
        Get access token using client credentials flow
        
        Returns:
            Token response data
        """
        session = await self._create_session()
        
        # Prepare client credentials request
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        # Make token request
        token_response = await self._make_token_request(session, token_data)
        
        if token_response['success']:
            self._store_tokens(token_response['data'])
            logger.info("Successfully obtained client credentials token")
        
        return token_response
    
    async def refresh_access_token(self) -> Dict[str, Any]:
        """
        Refresh access token using refresh token
        
        Returns:
            Token response data
        """
        if not self.refresh_token:
            raise SAPAuthenticationError("No refresh token available")
        
        session = await self._create_session()
        
        # Prepare refresh token request
        token_data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': self.scope
        }
        
        # Make token request
        token_response = await self._make_token_request(session, token_data)
        
        if token_response['success']:
            self._store_tokens(token_response['data'])
            logger.info("Successfully refreshed access token")
        
        return token_response
    
    async def _make_token_request(self, session: aiohttp.ClientSession, token_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Make token request with retry logic
        
        Args:
            session: aiohttp session
            token_data: Token request data
            
        Returns:
            Token response data
        """
        token_url = f"{self.base_url}{self.endpoints['token']}"
        
        # Prepare headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'Cache-Control': 'no-cache'
        }
        
        # Add basic authentication header
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        headers['Authorization'] = f'Basic {auth_b64}'
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                async with session.post(token_url, data=token_data, headers=headers) as response:
                    response_data = await response.json()
                    
                    if response.status == 200:
                        return {
                            'success': True,
                            'data': response_data,
                            'status_code': response.status
                        }
                    else:
                        error_msg = response_data.get('error_description', response_data.get('error', 'Unknown error'))
                        
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        
                        return {
                            'success': False,
                            'error': error_msg,
                            'error_code': response_data.get('error'),
                            'status_code': response.status
                        }
                        
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                else:
                    return {
                        'success': False,
                        'error': f'Request failed: {str(e)}',
                        'error_code': 'REQUEST_FAILED'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'error_code': 'UNEXPECTED_ERROR'
                }
    
    def _store_tokens(self, token_data: Dict[str, Any]) -> None:
        """Store tokens from response data"""
        self.access_token = token_data.get('access_token')
        self.refresh_token = token_data.get('refresh_token')
        self.token_type = token_data.get('token_type', 'Bearer')
        self.token_scope = token_data.get('scope', self.scope)
        
        # Calculate expiration time
        expires_in = token_data.get('expires_in', 3600)
        self.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        logger.debug(f"Stored tokens, expires at: {self.expires_at}")
    
    def is_token_expired(self) -> bool:
        """Check if access token is expired"""
        if not self.access_token or not self.expires_at:
            return True
        
        # Add 60 second buffer before expiration
        buffer_time = timedelta(seconds=60)
        return datetime.utcnow() >= (self.expires_at - buffer_time)
    
    async def ensure_valid_token(self) -> str:
        """
        Ensure we have a valid access token
        
        Returns:
            Valid access token
        """
        if self.is_token_expired():
            if self.refresh_token:
                # Try to refresh token
                refresh_result = await self.refresh_access_token()
                if not refresh_result['success']:
                    # Refresh failed, get new token
                    if self.grant_type == 'client_credentials':
                        token_result = await self.get_client_credentials_token()
                        if not token_result['success']:
                            raise SAPAuthenticationError(f"Failed to obtain access token: {token_result['error']}")
                    else:
                        raise SAPTokenExpiredError("Access token expired and refresh failed")
            else:
                # No refresh token, get new token
                if self.grant_type == 'client_credentials':
                    token_result = await self.get_client_credentials_token()
                    if not token_result['success']:
                        raise SAPAuthenticationError(f"Failed to obtain access token: {token_result['error']}")
                else:
                    raise SAPTokenExpiredError("Access token expired and no refresh token available")
        
        return self.access_token
    
    async def get_authorization_header(self) -> Dict[str, str]:
        """
        Get authorization header with valid token
        
        Returns:
            Authorization header dictionary
        """
        token = await self.ensure_valid_token()
        return {'Authorization': f'{self.token_type} {token}'}
    
    async def validate_token(self) -> Dict[str, Any]:
        """
        Validate current access token
        
        Returns:
            Token validation response
        """
        if not self.access_token:
            return {
                'valid': False,
                'error': 'No access token available'
            }
        
        session = await self._create_session()
        tokeninfo_url = f"{self.base_url}{self.endpoints['tokeninfo']}"
        
        headers = {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            async with session.get(tokeninfo_url, headers=headers) as response:
                if response.status == 200:
                    token_info = await response.json()
                    return {
                        'valid': True,
                        'token_info': token_info,
                        'expires_at': self.expires_at.isoformat() if self.expires_at else None
                    }
                else:
                    error_text = await response.text()
                    return {
                        'valid': False,
                        'error': f'Token validation failed: {error_text}',
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'valid': False,
                'error': f'Token validation error: {str(e)}'
            }
    
    async def revoke_token(self, token: Optional[str] = None, token_type_hint: str = 'access_token') -> Dict[str, Any]:
        """
        Revoke access or refresh token
        
        Args:
            token: Token to revoke (defaults to current access token)
            token_type_hint: Type of token being revoked
            
        Returns:
            Revocation response
        """
        if not token:
            token = self.access_token if token_type_hint == 'access_token' else self.refresh_token
        
        if not token:
            return {
                'success': False,
                'error': f'No {token_type_hint} available to revoke'
            }
        
        session = await self._create_session()
        revoke_url = f"{self.base_url}{self.endpoints['revoke']}"
        
        # Prepare revocation request
        revoke_data = {
            'token': token,
            'token_type_hint': token_type_hint,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            async with session.post(revoke_url, data=revoke_data, headers=headers) as response:
                if response.status in [200, 204]:
                    # Clear tokens if we revoked our current tokens
                    if token == self.access_token:
                        self.access_token = None
                        self.expires_at = None
                    if token == self.refresh_token:
                        self.refresh_token = None
                    
                    return {
                        'success': True,
                        'message': f'{token_type_hint} revoked successfully'
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'Token revocation failed: {error_text}',
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Token revocation error: {str(e)}'
            }
    
    async def get_user_info(self) -> Dict[str, Any]:
        """
        Get user information (for authorization code flow)
        
        Returns:
            User information response
        """
        if not self.access_token:
            return {
                'success': False,
                'error': 'No access token available'
            }
        
        session = await self._create_session()
        userinfo_url = f"{self.base_url}{self.endpoints['userinfo']}"
        
        headers = {
            'Authorization': f'{self.token_type} {self.access_token}',
            'Accept': 'application/json'
        }
        
        try:
            async with session.get(userinfo_url, headers=headers) as response:
                if response.status == 200:
                    user_info = await response.json()
                    return {
                        'success': True,
                        'user_info': user_info
                    }
                else:
                    error_text = await response.text()
                    return {
                        'success': False,
                        'error': f'User info request failed: {error_text}',
                        'status_code': response.status
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'User info request error: {str(e)}'
            }
    
    def get_token_info(self) -> Dict[str, Any]:
        """
        Get current token information
        
        Returns:
            Current token information
        """
        return {
            'has_access_token': bool(self.access_token),
            'has_refresh_token': bool(self.refresh_token),
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_token_expired(),
            'scope': self.token_scope,
            'grant_type': self.grant_type,
            'client_id': self.client_id
        }
    
    async def disconnect(self) -> None:
        """Disconnect and cleanup resources"""
        try:
            # Revoke tokens if available
            if self.access_token:
                await self.revoke_token(self.access_token, 'access_token')
            if self.refresh_token:
                await self.revoke_token(self.refresh_token, 'refresh_token')
        except Exception as e:
            logger.warning(f"Error revoking tokens during disconnect: {str(e)}")
        
        # Close session
        if self.session and not self.session.closed:
            await self.session.close()
        
        # Clear tokens
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.token_scope = None
        
        logger.info("SAP OAuth client disconnected")


class SAPOAuthManager:
    """
    SAP OAuth manager for multi-tenant scenarios
    
    Manages multiple OAuth clients for different SAP systems or tenants.
    """
    
    def __init__(self):
        """Initialize OAuth manager"""
        self.clients: Dict[str, SAPOAuthClient] = {}
        self.default_client_id = None
        logger.info("Initialized SAP OAuth manager")
    
    def add_client(self, client_id: str, config: Dict[str, Any], set_default: bool = False) -> SAPOAuthClient:
        """
        Add OAuth client for a SAP system
        
        Args:
            client_id: Unique identifier for the client
            config: OAuth client configuration
            set_default: Whether to set as default client
            
        Returns:
            Created OAuth client
        """
        client = SAPOAuthClient(config)
        self.clients[client_id] = client
        
        if set_default or not self.default_client_id:
            self.default_client_id = client_id
        
        logger.info(f"Added SAP OAuth client: {client_id}")
        return client
    
    def get_client(self, client_id: Optional[str] = None) -> SAPOAuthClient:
        """
        Get OAuth client by ID
        
        Args:
            client_id: Client ID (uses default if not provided)
            
        Returns:
            OAuth client
        """
        if not client_id:
            client_id = self.default_client_id
        
        if not client_id or client_id not in self.clients:
            raise SAPAuthenticationError(f"OAuth client not found: {client_id}")
        
        return self.clients[client_id]
    
    def remove_client(self, client_id: str) -> None:
        """
        Remove OAuth client
        
        Args:
            client_id: Client ID to remove
        """
        if client_id in self.clients:
            del self.clients[client_id]
            
            if self.default_client_id == client_id:
                self.default_client_id = next(iter(self.clients.keys())) if self.clients else None
            
            logger.info(f"Removed SAP OAuth client: {client_id}")
    
    async def disconnect_all(self) -> None:
        """Disconnect all OAuth clients"""
        for client in self.clients.values():
            await client.disconnect()
        
        self.clients.clear()
        self.default_client_id = None
        logger.info("Disconnected all SAP OAuth clients")
    
    def list_clients(self) -> List[Dict[str, Any]]:
        """
        List all OAuth clients
        
        Returns:
            List of client information
        """
        return [
            {
                'client_id': client_id,
                'host': client.host,
                'grant_type': client.grant_type,
                'is_default': client_id == self.default_client_id,
                'token_info': client.get_token_info()
            }
            for client_id, client in self.clients.items()
        ]