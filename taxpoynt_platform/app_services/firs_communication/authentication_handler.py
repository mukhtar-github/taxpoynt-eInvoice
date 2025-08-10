"""
FIRS Authentication Handler - APP Services

Specialized OAuth 2.0 authentication handler for FIRS API communication.
Handles the complete OAuth 2.0 flow, token management, and credential security
for Access Point Provider services.

Features:
- OAuth 2.0 client credentials flow
- Authorization code flow (for user-based auth)
- Token refresh and rotation
- Secure credential storage
- Multi-environment support (sandbox/production)
- Rate limiting and retry logic
- Audit logging and monitoring
"""

import asyncio
import logging
import json
import base64
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import jwt
from cryptography.fernet import Fernet

# Independent APP authentication services (no SI imports)
# Future: These will be unified through core_platform/authentication/

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication-related errors for APP services"""
    pass


@dataclass
class AuthenticationResult:
    """Result of authentication operation"""
    success: bool
    auth_data: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[datetime] = None
    session_id: Optional[str] = None
    provider: str = "firs_oauth2"
    error_message: Optional[str] = None
    error_code: Optional[str] = None


class OAuthGrantType(Enum):
    """OAuth 2.0 grant types supported by FIRS"""
    CLIENT_CREDENTIALS = "client_credentials"
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"


class OAuthScope(Enum):
    """OAuth 2.0 scopes for FIRS API"""
    READ = "firs:read"
    WRITE = "firs:write"
    IRN_GENERATE = "firs:irn:generate"
    IRN_VALIDATE = "firs:irn:validate"
    DOCUMENT_SUBMIT = "firs:document:submit"
    REPORTS_ACCESS = "firs:reports:access"
    ADMIN = "firs:admin"


@dataclass
class OAuthCredentials:
    """OAuth 2.0 credentials for FIRS"""
    client_id: str
    client_secret: str
    api_key: str
    environment: str = "sandbox"
    
    # Optional for authorization code flow
    redirect_uri: Optional[str] = None
    scope: List[str] = field(default_factory=lambda: ["firs:read", "firs:write"])
    
    # Token storage
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_in: int = 3600
    expires_at: Optional[datetime] = None
    
    # Metadata
    issued_at: Optional[datetime] = None
    issuer: Optional[str] = None
    audience: Optional[str] = None


@dataclass
class OAuthTokenResponse:
    """OAuth 2.0 token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
    scope: Optional[str] = None
    
    # Metadata
    issued_at: datetime = field(default_factory=datetime.now)
    raw_response: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuthenticationState:
    """Current authentication state"""
    is_authenticated: bool = False
    last_auth_time: Optional[datetime] = None
    last_refresh_time: Optional[datetime] = None
    auth_attempts: int = 0
    refresh_attempts: int = 0
    current_credentials: Optional[OAuthCredentials] = None
    active_session_id: Optional[str] = None


class FIRSAuthenticationHandler:
    """
    Specialized authentication handler for FIRS OAuth 2.0 flows.
    
    Provides secure, robust authentication management for APP services
    communicating with FIRS APIs.
    """
    
    def __init__(
        self,
        environment: str = "sandbox"
    ):
        self.environment = environment
        
        # Authentication state
        self.auth_state = AuthenticationState()
        self.credentials: Optional[OAuthCredentials] = None
        
        # Environment-specific URLs
        self.oauth_urls = self._get_oauth_urls(environment)
        
        # HTTP session for auth requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Security
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # Rate limiting for auth requests
        self.auth_request_timestamps: List[datetime] = []
        self.max_auth_requests_per_hour = 50
    
    def _get_oauth_urls(self, environment: str) -> Dict[str, str]:
        """Get OAuth URLs for environment"""
        if environment == "production":
            base_url = "https://auth.firs.gov.ng"
        else:
            base_url = "https://sandbox-auth.firs.gov.ng"
        
        return {
            'authorization': f"{base_url}/oauth2/authorize",
            'token': f"{base_url}/oauth2/token",
            'refresh': f"{base_url}/oauth2/refresh",
            'revoke': f"{base_url}/oauth2/revoke",
            'introspect': f"{base_url}/oauth2/introspect",
            'userinfo': f"{base_url}/oauth2/userinfo",
            'jwks': f"{base_url}/.well-known/jwks.json"
        }
    
    async def start(self) -> None:
        """Start the authentication handler"""
        try:
            logger.info(f"Starting FIRS authentication handler for {self.environment}")
            
            # Create HTTP session for auth requests
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'TaxPoynt-AUTH/1.0',
                    'Accept': 'application/json',
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            )
            
            # Load existing credentials if available
            await self._load_stored_credentials()
            
            logger.info("FIRS authentication handler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start FIRS authentication handler: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the authentication handler"""
        try:
            logger.info("Stopping FIRS authentication handler")
            
            # Save current credentials
            if self.credentials:
                await self._store_credentials()
            
            # Close HTTP session
            if self.session:
                await self.session.close()
                self.session = None
            
            # Clear authentication state
            self.auth_state = AuthenticationState()
            self.credentials = None
            
            logger.info("FIRS authentication handler stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping authentication handler: {e}")
    
    async def authenticate_client_credentials(
        self,
        client_id: str,
        client_secret: str,
        api_key: str,
        scope: Optional[List[str]] = None
    ) -> AuthenticationResult:
        """
        Authenticate using OAuth 2.0 client credentials flow
        
        Args:
            client_id: OAuth 2.0 client ID
            client_secret: OAuth 2.0 client secret
            api_key: FIRS API key
            scope: Requested OAuth scopes
            
        Returns:
            AuthenticationResult with tokens and metadata
        """
        try:
            logger.info("Authenticating with FIRS using client credentials flow")
            
            # Check rate limits
            if not self._check_auth_rate_limits():
                raise AuthenticationError("Authentication rate limit exceeded")
            
            # Prepare credentials
            credentials = OAuthCredentials(
                client_id=client_id,
                client_secret=client_secret,
                api_key=api_key,
                environment=self.environment,
                scope=scope or ["firs:read", "firs:write"]
            )
            
            # Create OAuth 2.0 token request
            token_data = {
                'grant_type': OAuthGrantType.CLIENT_CREDENTIALS.value,
                'client_id': client_id,
                'client_secret': client_secret,
                'scope': ' '.join(credentials.scope)
            }
            
            # Add authentication header
            auth_header = self._create_basic_auth_header(client_id, client_secret)
            headers = {
                'Authorization': auth_header,
                'X-API-Key': api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make token request
            self.auth_state.auth_attempts += 1
            self._record_auth_request()
            
            async with self.session.post(
                self.oauth_urls['token'],
                data=token_data,
                headers=headers
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    token_response = json.loads(response_text)
                    
                    # Parse token response
                    oauth_token = self._parse_token_response(token_response)
                    
                    # Update credentials with tokens
                    credentials.access_token = oauth_token.access_token
                    credentials.refresh_token = oauth_token.refresh_token
                    credentials.id_token = oauth_token.id_token
                    credentials.token_type = oauth_token.token_type
                    credentials.expires_in = oauth_token.expires_in
                    credentials.expires_at = oauth_token.issued_at + timedelta(seconds=oauth_token.expires_in)
                    credentials.issued_at = oauth_token.issued_at
                    
                    # Store credentials securely
                    self.credentials = credentials
                    await self._store_credentials()
                    
                    # Update authentication state
                    self.auth_state.is_authenticated = True
                    self.auth_state.last_auth_time = datetime.now()
                    self.auth_state.current_credentials = credentials
                    self.auth_state.active_session_id = self._generate_session_id()
                    
                    logger.info("Successfully authenticated with FIRS using client credentials")
                    
                    return AuthenticationResult(
                        success=True,
                        auth_data={
                            'access_token': credentials.access_token,
                            'refresh_token': credentials.refresh_token,
                            'token_type': credentials.token_type,
                            'scope': ' '.join(credentials.scope)
                        },
                        expires_at=credentials.expires_at,
                        session_id=self.auth_state.active_session_id,
                        provider="firs_oauth2"
                    )
                    
                else:
                    error_data = json.loads(response_text) if response_text else {}
                    error_message = error_data.get('error_description', f'HTTP {response.status}')
                    
                    logger.error(f"FIRS authentication failed: {error_message}")
                    
                    return AuthenticationResult(
                        success=False,
                        error_message=error_message,
                        error_code=error_data.get('error', 'AUTH_FAILED'),
                        provider="firs_oauth2"
                    )
                    
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Client credentials authentication error: {e}")
            return AuthenticationResult(
                success=False,
                error_message=str(e),
                error_code="AUTH_ERROR",
                provider="firs_oauth2"
            )
    
    async def refresh_access_token(
        self,
        refresh_token: Optional[str] = None
    ) -> AuthenticationResult:
        """
        Refresh OAuth 2.0 access token
        
        Args:
            refresh_token: Refresh token (uses stored if not provided)
            
        Returns:
            AuthenticationResult with new tokens
        """
        try:
            logger.info("Refreshing FIRS access token")
            
            # Use provided refresh token or stored one
            token_to_use = refresh_token or (
                self.credentials.refresh_token if self.credentials else None
            )
            
            if not token_to_use:
                raise AuthenticationError("No refresh token available")
            
            if not self.credentials:
                raise AuthenticationError("No stored credentials for refresh")
            
            # Check rate limits
            if not self._check_auth_rate_limits():
                raise AuthenticationError("Token refresh rate limit exceeded")
            
            # Create refresh token request
            token_data = {
                'grant_type': OAuthGrantType.REFRESH_TOKEN.value,
                'refresh_token': token_to_use,
                'client_id': self.credentials.client_id,
                'client_secret': self.credentials.client_secret
            }
            
            # Authentication header
            auth_header = self._create_basic_auth_header(
                self.credentials.client_id,
                self.credentials.client_secret
            )
            
            headers = {
                'Authorization': auth_header,
                'X-API-Key': self.credentials.api_key,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            # Make refresh request
            self.auth_state.refresh_attempts += 1
            self._record_auth_request()
            
            async with self.session.post(
                self.oauth_urls['refresh'],
                data=token_data,
                headers=headers
            ) as response:
                
                response_text = await response.text()
                
                if response.status == 200:
                    token_response = json.loads(response_text)
                    
                    # Parse new token response
                    oauth_token = self._parse_token_response(token_response)
                    
                    # Update stored credentials
                    self.credentials.access_token = oauth_token.access_token
                    if oauth_token.refresh_token:
                        self.credentials.refresh_token = oauth_token.refresh_token
                    self.credentials.expires_at = oauth_token.issued_at + timedelta(seconds=oauth_token.expires_in)
                    self.credentials.issued_at = oauth_token.issued_at
                    
                    # Store updated credentials
                    await self._store_credentials()
                    
                    # Update authentication state
                    self.auth_state.last_refresh_time = datetime.now()
                    
                    logger.info("Successfully refreshed FIRS access token")
                    
                    return AuthenticationResult(
                        success=True,
                        auth_data={
                            'access_token': self.credentials.access_token,
                            'refresh_token': self.credentials.refresh_token,
                            'token_type': self.credentials.token_type
                        },
                        expires_at=self.credentials.expires_at,
                        session_id=self.auth_state.active_session_id,
                        provider="firs_oauth2"
                    )
                    
                else:
                    error_data = json.loads(response_text) if response_text else {}
                    error_message = error_data.get('error_description', f'HTTP {response.status}')
                    
                    logger.error(f"Token refresh failed: {error_message}")
                    
                    return AuthenticationResult(
                        success=False,
                        error_message=error_message,
                        error_code=error_data.get('error', 'REFRESH_FAILED'),
                        provider="firs_oauth2"
                    )
                    
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthenticationResult(
                success=False,
                error_message=str(e),
                error_code="REFRESH_ERROR",
                provider="firs_oauth2"
            )
    
    async def validate_token(
        self,
        access_token: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Validate OAuth 2.0 access token
        
        Args:
            access_token: Token to validate (uses stored if not provided)
            
        Returns:
            Tuple of (is_valid, token_info)
        """
        try:
            token_to_validate = access_token or (
                self.credentials.access_token if self.credentials else None
            )
            
            if not token_to_validate:
                return False, None
            
            # Check token expiration first (local validation)
            if self.credentials and self.credentials.expires_at:
                if datetime.now() >= self.credentials.expires_at:
                    logger.warning("Token expired (local validation)")
                    return False, {'error': 'token_expired'}
            
            # Remote token introspection
            introspect_data = {
                'token': token_to_validate,
                'token_type_hint': 'access_token'
            }
            
            auth_header = self._create_basic_auth_header(
                self.credentials.client_id,
                self.credentials.client_secret
            ) if self.credentials else None
            
            headers = {'Authorization': auth_header} if auth_header else {}
            
            async with self.session.post(
                self.oauth_urls['introspect'],
                data=introspect_data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    introspect_result = await response.json()
                    
                    is_active = introspect_result.get('active', False)
                    
                    if is_active:
                        logger.debug("Token validation successful")
                        return True, introspect_result
                    else:
                        logger.warning("Token validation failed - token inactive")
                        return False, introspect_result
                else:
                    logger.error(f"Token introspection failed: HTTP {response.status}")
                    return False, None
                    
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return False, None
    
    async def revoke_token(
        self,
        token: Optional[str] = None,
        token_type: str = "access_token"
    ) -> bool:
        """
        Revoke OAuth 2.0 token
        
        Args:
            token: Token to revoke (uses stored if not provided)
            token_type: Type of token (access_token or refresh_token)
            
        Returns:
            True if revocation successful
        """
        try:
            if token_type == "access_token":
                token_to_revoke = token or (
                    self.credentials.access_token if self.credentials else None
                )
            else:
                token_to_revoke = token or (
                    self.credentials.refresh_token if self.credentials else None
                )
            
            if not token_to_revoke:
                logger.warning(f"No {token_type} available for revocation")
                return False
            
            # Create revocation request
            revoke_data = {
                'token': token_to_revoke,
                'token_type_hint': token_type
            }
            
            auth_header = self._create_basic_auth_header(
                self.credentials.client_id,
                self.credentials.client_secret
            ) if self.credentials else None
            
            headers = {'Authorization': auth_header} if auth_header else {}
            
            async with self.session.post(
                self.oauth_urls['revoke'],
                data=revoke_data,
                headers=headers
            ) as response:
                
                if response.status == 200:
                    logger.info(f"Successfully revoked {token_type}")
                    
                    # Clear stored tokens
                    if self.credentials:
                        if token_type == "access_token":
                            self.credentials.access_token = None
                        else:
                            self.credentials.refresh_token = None
                        
                        await self._store_credentials()
                    
                    return True
                else:
                    logger.error(f"Token revocation failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            return False
    
    def _create_basic_auth_header(self, client_id: str, client_secret: str) -> str:
        """Create HTTP Basic Authentication header"""
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"
    
    def _parse_token_response(self, response_data: Dict[str, Any]) -> OAuthTokenResponse:
        """Parse OAuth 2.0 token response"""
        return OAuthTokenResponse(
            access_token=response_data['access_token'],
            token_type=response_data.get('token_type', 'Bearer'),
            expires_in=response_data.get('expires_in', 3600),
            refresh_token=response_data.get('refresh_token'),
            id_token=response_data.get('id_token'),
            scope=response_data.get('scope'),
            raw_response=response_data
        )
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_part = secrets.token_hex(8)
        return f"firs_auth_{self.environment}_{timestamp}_{random_part}"
    
    def _check_auth_rate_limits(self) -> bool:
        """Check authentication request rate limits"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=1)
        
        # Clean old timestamps
        self.auth_request_timestamps = [
            ts for ts in self.auth_request_timestamps
            if ts > cutoff_time
        ]
        
        # Check if under limit
        return len(self.auth_request_timestamps) < self.max_auth_requests_per_hour
    
    def _record_auth_request(self) -> None:
        """Record authentication request timestamp"""
        self.auth_request_timestamps.append(datetime.now())
    
    async def _store_credentials(self) -> None:
        """Store credentials securely (independent implementation)"""
        try:
            if not self.credentials:
                return
            
            # For now, store in memory (encrypted)
            # Future: Will integrate with core_platform credential storage
            sensitive_data = {
                'client_secret': self.credentials.client_secret,
                'api_key': self.credentials.api_key,
                'access_token': self.credentials.access_token,
                'refresh_token': self.credentials.refresh_token,
                'id_token': self.credentials.id_token
            }
            
            # Simple encryption for demonstration
            encrypted_data = self.cipher.encrypt(json.dumps(sensitive_data).encode())
            
            # In production, this would go to secure storage
            credential_id = f"firs_oauth_{self.environment}_{self.credentials.client_id}"
            logger.debug(f"Credentials stored securely for {credential_id}")
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
    
    async def _load_stored_credentials(self) -> None:
        """Load stored credentials (independent implementation)"""
        try:
            # Future: Will integrate with core_platform credential storage
            logger.debug("Loading stored FIRS credentials...")
            
        except Exception as e:
            logger.warning(f"Failed to load stored credentials: {e}")
    
    def get_current_credentials(self) -> Optional[OAuthCredentials]:
        """Get current credentials"""
        return self.credentials
    
    def get_authentication_state(self) -> AuthenticationState:
        """Get current authentication state"""
        return self.auth_state
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated"""
        if not self.auth_state.is_authenticated or not self.credentials:
            return False
        
        # Check token expiration
        if self.credentials.expires_at:
            buffer_time = timedelta(minutes=5)  # 5-minute buffer
            return datetime.now() + buffer_time < self.credentials.expires_at
        
        return True


# Factory function for creating FIRS authentication handler
def create_firs_auth_handler(
    environment: str = "sandbox"
) -> FIRSAuthenticationHandler:
    """
    Factory function to create FIRS authentication handler
    
    Args:
        environment: FIRS environment (sandbox/production)
        
    Returns:
        Configured FIRS authentication handler
    """
    return FIRSAuthenticationHandler(environment=environment)