"""
OAuth Coordinator Service

This service coordinates OAuth authentication with external systems for the TaxPoynt platform,
managing OAuth flows, token exchange, and integration with third-party services.
"""

import asyncio
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import urllib.parse
from urllib.parse import urlencode, parse_qs
import aiohttp

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)


class OAuthFlow(Enum):
    """OAuth flow types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    DEVICE_CODE = "device_code"
    REFRESH_TOKEN = "refresh_token"
    PKCE = "pkce"


class GrantType(Enum):
    """OAuth grant types"""
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    REFRESH_TOKEN = "refresh_token"
    DEVICE_CODE = "urn:ietf:params:oauth:grant-type:device_code"


class TokenType(Enum):
    """Token types"""
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    BEARER = "Bearer"


class OAuthProvider(Enum):
    """Supported OAuth providers"""
    FIRS = "firs"
    MICROSOFT = "microsoft"
    GOOGLE = "google"
    GITHUB = "github"
    CUSTOM = "custom"


@dataclass
class OAuthClient:
    """OAuth client configuration"""
    client_id: str
    client_secret: str
    provider: OAuthProvider
    authorization_url: str
    token_url: str
    user_info_url: Optional[str] = None
    scopes: Set[str] = field(default_factory=set)
    redirect_uri: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OAuthToken:
    """OAuth token information"""
    token_id: str
    user_id: str
    client_id: str
    provider: OAuthProvider
    access_token: str
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: TokenType = TokenType.BEARER
    expires_at: Optional[datetime] = None
    scopes: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OAuthSession:
    """OAuth session tracking"""
    session_id: str
    user_id: Optional[str] = None
    client_id: str = ""
    provider: OAuthProvider = OAuthProvider.CUSTOM
    flow: OAuthFlow = OAuthFlow.AUTHORIZATION_CODE
    state: str = ""
    code_verifier: Optional[str] = None
    code_challenge: Optional[str] = None
    nonce: Optional[str] = None
    redirect_uri: Optional[str] = None
    scopes: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=10))
    completed: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OAuthUserInfo:
    """OAuth user information"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture: Optional[str] = None
    locale: Optional[str] = None
    verified_email: bool = False
    provider: Optional[OAuthProvider] = None
    provider_user_id: Optional[str] = None
    raw_info: Dict[str, Any] = field(default_factory=dict)


class OAuthCoordinator(BaseService):
    """
    OAuth Coordinator Service
    
    Coordinates OAuth authentication with external systems for the TaxPoynt platform,
    managing OAuth flows, token exchange, and integration with third-party services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # OAuth clients
        self.oauth_clients: Dict[str, OAuthClient] = {}
        
        # Token storage
        self.tokens: Dict[str, OAuthToken] = {}
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> token_ids
        
        # Session management
        self.sessions: Dict[str, OAuthSession] = {}
        
        # User information cache
        self.user_info_cache: Dict[str, OAuthUserInfo] = {}
        self.cache_ttl: timedelta = timedelta(hours=1)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # HTTP client for OAuth requests
        self.http_client: Optional[aiohttp.ClientSession] = None
        
        # Security settings
        self.state_entropy_bytes = 32
        self.code_verifier_entropy_bytes = 64
        self.nonce_entropy_bytes = 32
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance metrics
        self.metrics = {
            'clients_managed': 0,
            'tokens_issued': 0,
            'tokens_refreshed': 0,
            'sessions_created': 0,
            'auth_flows_completed': 0,
            'auth_flows_failed': 0,
            'user_info_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def initialize(self) -> None:
        """Initialize OAuth coordinator"""
        try:
            self.logger.info("Initializing OAuthCoordinator")
            
            # Initialize HTTP client
            timeout = aiohttp.ClientTimeout(total=30)
            self.http_client = aiohttp.ClientSession(timeout=timeout)
            
            # Load default OAuth clients
            await self._load_default_clients()
            
            # Start background workers
            await self._start_background_workers()
            
            self.logger.info("OAuthCoordinator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize OAuthCoordinator: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def register_oauth_client(
        self,
        client_id: str,
        client_secret: str,
        provider: OAuthProvider,
        authorization_url: str,
        token_url: str,
        user_info_url: Optional[str] = None,
        scopes: Optional[Set[str]] = None,
        redirect_uri: Optional[str] = None,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> OAuthClient:
        """Register OAuth client"""
        try:
            client = OAuthClient(
                client_id=client_id,
                client_secret=client_secret,
                provider=provider,
                authorization_url=authorization_url,
                token_url=token_url,
                user_info_url=user_info_url,
                scopes=scopes or set(),
                redirect_uri=redirect_uri,
                additional_params=additional_params or {}
            )
            
            self.oauth_clients[client_id] = client
            
            self.metrics['clients_managed'] += 1
            self.logger.info(f"OAuth client registered: {client_id} ({provider.value})")
            
            return client
            
        except Exception as e:
            self.logger.error(f"Failed to register OAuth client {client_id}: {str(e)}")
            raise AuthenticationError(f"Client registration failed: {str(e)}")
    
    async def initiate_authorization_flow(
        self,
        client_id: str,
        user_id: Optional[str] = None,
        scopes: Optional[Set[str]] = None,
        redirect_uri: Optional[str] = None,
        use_pkce: bool = True,
        additional_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate OAuth authorization flow"""
        try:
            # Validate client
            if client_id not in self.oauth_clients:
                raise ValidationError(f"OAuth client {client_id} not found")
            
            client = self.oauth_clients[client_id]
            
            # Generate session
            session_id = self._generate_session_id()
            state = self._generate_state()
            nonce = self._generate_nonce()
            
            # PKCE parameters
            code_verifier = None
            code_challenge = None
            if use_pkce:
                code_verifier = self._generate_code_verifier()
                code_challenge = self._generate_code_challenge(code_verifier)
            
            # Create session
            session = OAuthSession(
                session_id=session_id,
                user_id=user_id,
                client_id=client_id,
                provider=client.provider,
                flow=OAuthFlow.PKCE if use_pkce else OAuthFlow.AUTHORIZATION_CODE,
                state=state,
                code_verifier=code_verifier,
                code_challenge=code_challenge,
                nonce=nonce,
                redirect_uri=redirect_uri or client.redirect_uri,
                scopes=scopes or client.scopes
            )
            
            self.sessions[session_id] = session
            
            # Build authorization URL
            auth_params = {
                'response_type': 'code',
                'client_id': client_id,
                'redirect_uri': session.redirect_uri,
                'scope': ' '.join(session.scopes),
                'state': state,
                'nonce': nonce
            }
            
            if use_pkce:
                auth_params.update({
                    'code_challenge': code_challenge,
                    'code_challenge_method': 'S256'
                })
            
            # Add additional parameters
            if additional_params:
                auth_params.update(additional_params)
            
            # Add client-specific parameters
            auth_params.update(client.additional_params)
            
            authorization_url = f"{client.authorization_url}?{urlencode(auth_params)}"
            
            self.metrics['sessions_created'] += 1
            self.logger.info(f"Authorization flow initiated: {session_id}")
            
            return {
                'session_id': session_id,
                'authorization_url': authorization_url,
                'state': state,
                'expires_at': session.expires_at.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initiate authorization flow: {str(e)}")
            raise AuthenticationError(f"Authorization flow failed: {str(e)}")
    
    async def handle_authorization_callback(
        self,
        session_id: str,
        authorization_code: str,
        state: str,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle OAuth authorization callback"""
        try:
            # Validate session
            if session_id not in self.sessions:
                raise ValidationError(f"Session {session_id} not found")
            
            session = self.sessions[session_id]
            
            # Check if session expired
            if datetime.utcnow() > session.expires_at:
                raise AuthenticationError("Session expired")
            
            # Validate state
            if state != session.state:
                raise AuthenticationError("Invalid state parameter")
            
            # Handle error
            if error:
                session.error = error
                session.completed = True
                self.metrics['auth_flows_failed'] += 1
                raise AuthenticationError(f"Authorization error: {error}")
            
            # Exchange code for token
            token_response = await self._exchange_code_for_token(session, authorization_code)
            
            # Create token record
            token = await self._create_token_record(session, token_response)
            
            # Get user information
            user_info = None
            if session.client_id in self.oauth_clients:
                client = self.oauth_clients[session.client_id]
                if client.user_info_url:
                    user_info = await self._fetch_user_info(client, token.access_token)
            
            # Mark session as completed
            session.completed = True
            session.user_id = user_info.user_id if user_info else session.user_id
            
            self.metrics['auth_flows_completed'] += 1
            self.logger.info(f"Authorization callback handled: {session_id}")
            
            return {
                'session_id': session_id,
                'token_id': token.token_id,
                'user_info': user_info.__dict__ if user_info else None,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle authorization callback: {str(e)}")
            if session_id in self.sessions:
                self.sessions[session_id].error = str(e)
                self.sessions[session_id].completed = True
                self.metrics['auth_flows_failed'] += 1
            raise AuthenticationError(f"Authorization callback failed: {str(e)}")
    
    async def client_credentials_flow(
        self,
        client_id: str,
        scopes: Optional[Set[str]] = None
    ) -> OAuthToken:
        """Perform client credentials OAuth flow"""
        try:
            # Validate client
            if client_id not in self.oauth_clients:
                raise ValidationError(f"OAuth client {client_id} not found")
            
            client = self.oauth_clients[client_id]
            
            # Prepare token request
            token_data = {
                'grant_type': GrantType.CLIENT_CREDENTIALS.value,
                'scope': ' '.join(scopes or client.scopes)
            }
            
            # Make token request
            token_response = await self._make_token_request(client, token_data)
            
            # Create token record
            token_id = self._generate_token_id()
            token = OAuthToken(
                token_id=token_id,
                user_id='',  # No user for client credentials
                client_id=client_id,
                provider=client.provider,
                access_token=token_response['access_token'],
                token_type=TokenType(token_response.get('token_type', 'Bearer')),
                scopes=scopes or client.scopes
            )
            
            # Set expiration
            if 'expires_in' in token_response:
                token.expires_at = datetime.utcnow() + timedelta(seconds=int(token_response['expires_in']))
            
            # Store token
            self.tokens[token_id] = token
            
            self.metrics['tokens_issued'] += 1
            self.logger.info(f"Client credentials token issued: {token_id}")
            
            return token
            
        except Exception as e:
            self.logger.error(f"Failed client credentials flow: {str(e)}")
            raise AuthenticationError(f"Client credentials flow failed: {str(e)}")
    
    async def refresh_token(self, token_id: str) -> OAuthToken:
        """Refresh OAuth token"""
        try:
            # Validate token
            if token_id not in self.tokens:
                raise ValidationError(f"Token {token_id} not found")
            
            token = self.tokens[token_id]
            
            if not token.refresh_token:
                raise ValidationError(f"Token {token_id} has no refresh token")
            
            # Get client
            if token.client_id not in self.oauth_clients:
                raise ValidationError(f"OAuth client {token.client_id} not found")
            
            client = self.oauth_clients[token.client_id]
            
            # Prepare refresh request
            refresh_data = {
                'grant_type': GrantType.REFRESH_TOKEN.value,
                'refresh_token': token.refresh_token
            }
            
            # Make refresh request
            token_response = await self._make_token_request(client, refresh_data)
            
            # Update token
            token.access_token = token_response['access_token']
            token.updated_at = datetime.utcnow()
            
            # Update refresh token if provided
            if 'refresh_token' in token_response:
                token.refresh_token = token_response['refresh_token']
            
            # Update expiration
            if 'expires_in' in token_response:
                token.expires_at = datetime.utcnow() + timedelta(seconds=int(token_response['expires_in']))
            
            self.metrics['tokens_refreshed'] += 1
            self.logger.info(f"Token refreshed: {token_id}")
            
            return token
            
        except Exception as e:
            self.logger.error(f"Failed to refresh token {token_id}: {str(e)}")
            raise AuthenticationError(f"Token refresh failed: {str(e)}")
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke OAuth token"""
        try:
            if token_id not in self.tokens:
                return False
            
            token = self.tokens[token_id]
            
            # Get client
            if token.client_id in self.oauth_clients:
                client = self.oauth_clients[token.client_id]
                
                # Try to revoke at provider if supported
                try:
                    await self._revoke_token_at_provider(client, token)
                except Exception as e:
                    self.logger.warning(f"Failed to revoke token at provider: {str(e)}")
            
            # Remove from storage
            del self.tokens[token_id]
            
            # Remove from user tokens
            if token.user_id in self.user_tokens:
                self.user_tokens[token.user_id] = [
                    tid for tid in self.user_tokens[token.user_id] if tid != token_id
                ]
            
            self.logger.info(f"Token revoked: {token_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke token {token_id}: {str(e)}")
            return False
    
    async def get_user_tokens(
        self,
        user_id: str,
        provider: Optional[OAuthProvider] = None,
        active_only: bool = True
    ) -> List[OAuthToken]:
        """Get user's OAuth tokens"""
        try:
            if user_id not in self.user_tokens:
                return []
            
            user_token_list = []
            
            for token_id in self.user_tokens[user_id]:
                if token_id not in self.tokens:
                    continue
                
                token = self.tokens[token_id]
                
                # Filter by provider
                if provider and token.provider != provider:
                    continue
                
                # Filter by active status
                if active_only:
                    if token.expires_at and datetime.utcnow() > token.expires_at:
                        continue
                
                user_token_list.append(token)
            
            return user_token_list
            
        except Exception as e:
            self.logger.error(f"Failed to get user tokens for {user_id}: {str(e)}")
            return []
    
    async def get_user_info(
        self,
        token_id: str,
        use_cache: bool = True
    ) -> Optional[OAuthUserInfo]:
        """Get user information using OAuth token"""
        try:
            # Validate token
            if token_id not in self.tokens:
                return None
            
            token = self.tokens[token_id]
            
            # Check cache
            if use_cache and token.user_id in self.user_info_cache:
                cached_info = self.user_info_cache[token.user_id]
                timestamp = self.cache_timestamps.get(token.user_id)
                
                if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                    self.metrics['cache_hits'] += 1
                    return cached_info
            
            # Get client
            if token.client_id not in self.oauth_clients:
                return None
            
            client = self.oauth_clients[token.client_id]
            
            # Fetch user info
            user_info = await self._fetch_user_info(client, token.access_token)
            
            # Cache result
            if user_info and use_cache:
                self.user_info_cache[token.user_id] = user_info
                self.cache_timestamps[token.user_id] = datetime.utcnow()
            
            self.metrics['cache_misses'] += 1
            return user_info
            
        except Exception as e:
            self.logger.error(f"Failed to get user info for token {token_id}: {str(e)}")
            return None
    
    async def validate_token(self, token_id: str) -> bool:
        """Validate OAuth token"""
        try:
            if token_id not in self.tokens:
                return False
            
            token = self.tokens[token_id]
            
            # Check expiration
            if token.expires_at and datetime.utcnow() > token.expires_at:
                return False
            
            # Additional validation can be added here
            # e.g., introspection endpoint call
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to validate token {token_id}: {str(e)}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get OAuth coordinator health status"""
        try:
            # Calculate token statistics
            active_tokens = 0
            expired_tokens = 0
            now = datetime.utcnow()
            
            for token in self.tokens.values():
                if token.expires_at:
                    if token.expires_at > now:
                        active_tokens += 1
                    else:
                        expired_tokens += 1
                else:
                    active_tokens += 1
            
            # Calculate session statistics
            active_sessions = len([s for s in self.sessions.values() if not s.completed and s.expires_at > now])
            
            return {
                'service': 'OAuthCoordinator',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'clients': {
                    'total': len(self.oauth_clients),
                    'by_provider': {
                        provider.value: len([c for c in self.oauth_clients.values() if c.provider == provider])
                        for provider in OAuthProvider
                    },
                    'active': len([c for c in self.oauth_clients.values() if c.active])
                },
                'tokens': {
                    'total': len(self.tokens),
                    'active': active_tokens,
                    'expired': expired_tokens,
                    'users_with_tokens': len(self.user_tokens)
                },
                'sessions': {
                    'total': len(self.sessions),
                    'active': active_sessions,
                    'completed': len([s for s in self.sessions.values() if s.completed])
                },
                'cache': {
                    'user_info_size': len(self.user_info_cache),
                    'hit_ratio': (
                        self.metrics['cache_hits'] / 
                        (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
                        else 0
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'OAuthCoordinator',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_clients(self) -> None:
        """Load default OAuth clients"""
        # FIRS OAuth client (example configuration)
        await self.register_oauth_client(
            client_id="firs_client_id",
            client_secret="firs_client_secret",
            provider=OAuthProvider.FIRS,
            authorization_url="https://auth.firs.gov.ng/oauth/authorize",
            token_url="https://auth.firs.gov.ng/oauth/token",
            user_info_url="https://api.firs.gov.ng/user/profile",
            scopes={"invoice:manage", "certificate:read"},
            additional_params={"audience": "firs-api"}
        )
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Token cleanup worker
        async def token_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._cleanup_expired_tokens()
                except Exception as e:
                    self.logger.error(f"Token cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        # Session cleanup worker
        async def session_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    await self._cleanup_expired_sessions()
                except Exception as e:
                    self.logger.error(f"Session cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        # Cache cleanup worker
        async def cache_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._cleanup_user_info_cache()
                except Exception as e:
                    self.logger.error(f"Cache cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        self.background_tasks['token_cleanup'] = asyncio.create_task(token_cleanup_worker())
        self.background_tasks['session_cleanup'] = asyncio.create_task(session_cleanup_worker())
        self.background_tasks['cache_cleanup'] = asyncio.create_task(cache_cleanup_worker())
    
    async def _exchange_code_for_token(self, session: OAuthSession, authorization_code: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens"""
        if session.client_id not in self.oauth_clients:
            raise ValidationError(f"OAuth client {session.client_id} not found")
        
        client = self.oauth_clients[session.client_id]
        
        # Prepare token request data
        token_data = {
            'grant_type': GrantType.AUTHORIZATION_CODE.value,
            'code': authorization_code,
            'redirect_uri': session.redirect_uri,
            'client_id': session.client_id
        }
        
        # Add PKCE verifier if used
        if session.code_verifier:
            token_data['code_verifier'] = session.code_verifier
        
        return await self._make_token_request(client, token_data)
    
    async def _make_token_request(self, client: OAuthClient, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make token request to OAuth provider"""
        if not self.http_client:
            raise AuthenticationError("HTTP client not initialized")
        
        # Prepare authentication
        auth_header = base64.b64encode(f"{client.client_id}:{client.client_secret}".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        }
        
        try:
            async with self.http_client.post(
                client.token_url,
                data=data,
                headers=headers
            ) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = response_data.get('error_description', response_data.get('error', 'Unknown error'))
                    raise AuthenticationError(f"Token request failed: {error_msg}")
                
                return response_data
                
        except aiohttp.ClientError as e:
            raise AuthenticationError(f"Token request failed: {str(e)}")
    
    async def _create_token_record(self, session: OAuthSession, token_response: Dict[str, Any]) -> OAuthToken:
        """Create token record from OAuth response"""
        token_id = self._generate_token_id()
        
        token = OAuthToken(
            token_id=token_id,
            user_id=session.user_id or '',
            client_id=session.client_id,
            provider=session.provider,
            access_token=token_response['access_token'],
            refresh_token=token_response.get('refresh_token'),
            id_token=token_response.get('id_token'),
            token_type=TokenType(token_response.get('token_type', 'Bearer')),
            scopes=session.scopes
        )
        
        # Set expiration
        if 'expires_in' in token_response:
            token.expires_at = datetime.utcnow() + timedelta(seconds=int(token_response['expires_in']))
        
        # Store token
        self.tokens[token_id] = token
        
        # Add to user tokens
        if token.user_id:
            if token.user_id not in self.user_tokens:
                self.user_tokens[token.user_id] = []
            self.user_tokens[token.user_id].append(token_id)
        
        self.metrics['tokens_issued'] += 1
        return token
    
    async def _fetch_user_info(self, client: OAuthClient, access_token: str) -> Optional[OAuthUserInfo]:
        """Fetch user information from OAuth provider"""
        if not client.user_info_url or not self.http_client:
            return None
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        try:
            async with self.http_client.get(
                client.user_info_url,
                headers=headers
            ) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed to fetch user info: HTTP {response.status}")
                    return None
                
                user_data = await response.json()
                
                # Map provider-specific fields to standard format
                user_info = self._map_user_info(client.provider, user_data)
                
                self.metrics['user_info_requests'] += 1
                return user_info
                
        except aiohttp.ClientError as e:
            self.logger.error(f"Failed to fetch user info: {str(e)}")
            return None
    
    def _map_user_info(self, provider: OAuthProvider, raw_data: Dict[str, Any]) -> OAuthUserInfo:
        """Map provider-specific user info to standard format"""
        if provider == OAuthProvider.MICROSOFT:
            return OAuthUserInfo(
                user_id=raw_data.get('id', ''),
                email=raw_data.get('mail') or raw_data.get('userPrincipalName'),
                name=raw_data.get('displayName'),
                given_name=raw_data.get('givenName'),
                family_name=raw_data.get('surname'),
                provider=provider,
                provider_user_id=raw_data.get('id'),
                raw_info=raw_data
            )
        elif provider == OAuthProvider.GOOGLE:
            return OAuthUserInfo(
                user_id=raw_data.get('sub', ''),
                email=raw_data.get('email'),
                name=raw_data.get('name'),
                given_name=raw_data.get('given_name'),
                family_name=raw_data.get('family_name'),
                picture=raw_data.get('picture'),
                locale=raw_data.get('locale'),
                verified_email=raw_data.get('email_verified', False),
                provider=provider,
                provider_user_id=raw_data.get('sub'),
                raw_info=raw_data
            )
        elif provider == OAuthProvider.FIRS:
            return OAuthUserInfo(
                user_id=raw_data.get('user_id', ''),
                email=raw_data.get('email'),
                name=raw_data.get('full_name'),
                given_name=raw_data.get('first_name'),
                family_name=raw_data.get('last_name'),
                provider=provider,
                provider_user_id=raw_data.get('user_id'),
                raw_info=raw_data
            )
        else:
            # Generic mapping
            return OAuthUserInfo(
                user_id=raw_data.get('id') or raw_data.get('user_id', ''),
                email=raw_data.get('email'),
                name=raw_data.get('name') or raw_data.get('full_name'),
                provider=provider,
                provider_user_id=raw_data.get('id') or raw_data.get('user_id'),
                raw_info=raw_data
            )
    
    async def _revoke_token_at_provider(self, client: OAuthClient, token: OAuthToken) -> None:
        """Revoke token at OAuth provider"""
        # This would depend on provider-specific revocation endpoints
        # Implementation would vary by provider
        pass
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"oauth_session_{secrets.token_urlsafe(16)}"
    
    def _generate_token_id(self) -> str:
        """Generate unique token ID"""
        return f"oauth_token_{secrets.token_urlsafe(16)}"
    
    def _generate_state(self) -> str:
        """Generate OAuth state parameter"""
        return secrets.token_urlsafe(self.state_entropy_bytes)
    
    def _generate_nonce(self) -> str:
        """Generate OAuth nonce parameter"""
        return secrets.token_urlsafe(self.nonce_entropy_bytes)
    
    def _generate_code_verifier(self) -> str:
        """Generate PKCE code verifier"""
        return secrets.token_urlsafe(self.code_verifier_entropy_bytes)
    
    def _generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code challenge"""
        digest = hashlib.sha256(code_verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip('=')
    
    async def _cleanup_expired_tokens(self) -> None:
        """Clean up expired tokens"""
        now = datetime.utcnow()
        expired_tokens = []
        
        for token_id, token in self.tokens.items():
            if token.expires_at and token.expires_at <= now:
                expired_tokens.append(token_id)
        
        for token_id in expired_tokens:
            await self.revoke_token(token_id)
        
        if expired_tokens:
            self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
    
    async def _cleanup_expired_sessions(self) -> None:
        """Clean up expired sessions"""
        now = datetime.utcnow()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.expires_at <= now:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def _cleanup_user_info_cache(self) -> None:
        """Clean up expired user info cache"""
        now = datetime.utcnow()
        expired_entries = []
        
        for user_id, timestamp in self.cache_timestamps.items():
            if now - timestamp > self.cache_ttl:
                expired_entries.append(user_id)
        
        for user_id in expired_entries:
            if user_id in self.user_info_cache:
                del self.user_info_cache[user_id]
            del self.cache_timestamps[user_id]
        
        if expired_entries:
            self.logger.debug(f"Cleaned up {len(expired_entries)} expired cache entries")
    
    async def cleanup(self) -> None:
        """Cleanup OAuth coordinator resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Close HTTP client
            if self.http_client:
                await self.http_client.close()
            
            # Clear caches
            self.user_info_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("OAuthCoordinator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during OAuthCoordinator cleanup: {str(e)}")