"""
Authentication Manager - Universal Connector Framework
Multi-protocol authentication management for external system connectors.
Provides unified authentication handling across different protocols and auth types.
"""

import asyncio
import logging
import time
import hashlib
import hmac
import base64
import json
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlencode, quote
import jwt

from .base_connector import AuthenticationType

logger = logging.getLogger(__name__)

class TokenType(Enum):
    ACCESS_TOKEN = "access_token"
    REFRESH_TOKEN = "refresh_token"
    ID_TOKEN = "id_token"
    API_KEY = "api_key"
    SESSION_TOKEN = "session_token"
    CUSTOM = "custom"

class TokenStatus(Enum):
    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    REVOKED = "revoked"
    UNKNOWN = "unknown"

@dataclass
class AuthToken:
    token_type: TokenType
    value: str
    expires_at: Optional[datetime] = None
    issued_at: datetime = field(default_factory=datetime.utcnow)
    scope: Optional[str] = None
    refresh_token: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuthCredentials:
    auth_type: AuthenticationType
    credentials: Dict[str, Any]
    tokens: Dict[TokenType, AuthToken] = field(default_factory=dict)
    last_authenticated: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuthProvider:
    provider_id: str
    name: str
    auth_type: AuthenticationType
    config: Dict[str, Any]
    endpoints: Dict[str, str] = field(default_factory=dict)
    supported_protocols: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AuthenticationManager:
    """Universal authentication manager for all connector protocols"""
    
    def __init__(self):
        self.auth_providers: Dict[str, AuthProvider] = {}
        self.active_credentials: Dict[str, AuthCredentials] = {}
        self.session_cache: Dict[str, aiohttp.ClientSession] = {}
        
        # Initialize built-in auth providers
        self._initialize_builtin_providers()
    
    def _initialize_builtin_providers(self):
        """Initialize built-in authentication providers"""
        builtin_providers = [
            AuthProvider(
                provider_id="oauth2_client_credentials",
                name="OAuth 2.0 Client Credentials",
                auth_type=AuthenticationType.OAUTH2,
                config={
                    "grant_type": "client_credentials"
                },
                endpoints={
                    "token": "/oauth/token"
                },
                supported_protocols=["rest", "graphql", "odata"]
            ),
            AuthProvider(
                provider_id="oauth2_authorization_code",
                name="OAuth 2.0 Authorization Code",
                auth_type=AuthenticationType.OAUTH2,
                config={
                    "grant_type": "authorization_code"
                },
                endpoints={
                    "authorize": "/oauth/authorize",
                    "token": "/oauth/token"
                },
                supported_protocols=["rest", "graphql"]
            ),
            AuthProvider(
                provider_id="basic_auth",
                name="HTTP Basic Authentication",
                auth_type=AuthenticationType.BASIC_AUTH,
                config={},
                supported_protocols=["rest", "soap", "odata", "rpc"]
            ),
            AuthProvider(
                provider_id="api_key_header",
                name="API Key (Header)",
                auth_type=AuthenticationType.API_KEY,
                config={
                    "location": "header"
                },
                supported_protocols=["rest", "graphql", "rpc"]
            ),
            AuthProvider(
                provider_id="api_key_query",
                name="API Key (Query Parameter)",
                auth_type=AuthenticationType.API_KEY,
                config={
                    "location": "query"
                },
                supported_protocols=["rest", "graphql"]
            ),
            AuthProvider(
                provider_id="jwt_bearer",
                name="JWT Bearer Token",
                auth_type=AuthenticationType.JWT,
                config={},
                supported_protocols=["rest", "graphql", "rpc"]
            ),
            AuthProvider(
                provider_id="saml_assertion",
                name="SAML Assertion",
                auth_type=AuthenticationType.SAML,
                config={},
                supported_protocols=["soap", "rest"]
            )
        ]
        
        for provider in builtin_providers:
            self.auth_providers[provider.provider_id] = provider
    
    def add_auth_provider(self, provider: AuthProvider) -> bool:
        """Add a custom authentication provider"""
        try:
            self.auth_providers[provider.provider_id] = provider
            logger.info(f"Added authentication provider: {provider.provider_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add auth provider: {e}")
            return False
    
    def get_auth_provider(self, provider_id: str) -> Optional[AuthProvider]:
        """Get authentication provider by ID"""
        return self.auth_providers.get(provider_id)
    
    def list_auth_providers(self, protocol: Optional[str] = None) -> List[AuthProvider]:
        """List available authentication providers"""
        if protocol:
            return [
                provider for provider in self.auth_providers.values()
                if protocol in provider.supported_protocols
            ]
        return list(self.auth_providers.values())
    
    async def authenticate(self, connector_id: str, auth_config: Dict[str, Any],
                          session: Optional[aiohttp.ClientSession] = None) -> Optional[AuthCredentials]:
        """Authenticate using the specified configuration"""
        try:
            auth_type = AuthenticationType(auth_config.get('type', 'none'))
            
            if auth_type == AuthenticationType.NONE:
                return AuthCredentials(
                    auth_type=auth_type,
                    credentials={},
                    last_authenticated=datetime.utcnow()
                )
            
            # Find appropriate provider
            provider_id = auth_config.get('provider')
            if provider_id and provider_id in self.auth_providers:
                provider = self.auth_providers[provider_id]
            else:
                provider = self._find_provider_by_type(auth_type)
            
            if not provider:
                logger.error(f"No authentication provider found for type: {auth_type}")
                return None
            
            # Perform authentication based on type
            credentials = None
            if auth_type == AuthenticationType.OAUTH2:
                credentials = await self._authenticate_oauth2(auth_config, provider, session)
            elif auth_type == AuthenticationType.BASIC_AUTH:
                credentials = await self._authenticate_basic_auth(auth_config, provider)
            elif auth_type == AuthenticationType.API_KEY:
                credentials = await self._authenticate_api_key(auth_config, provider)
            elif auth_type == AuthenticationType.JWT:
                credentials = await self._authenticate_jwt(auth_config, provider)
            elif auth_type == AuthenticationType.SAML:
                credentials = await self._authenticate_saml(auth_config, provider, session)
            elif auth_type == AuthenticationType.CUSTOM_TOKEN:
                credentials = await self._authenticate_custom_token(auth_config, provider)
            
            if credentials:
                self.active_credentials[connector_id] = credentials
                logger.info(f"Authentication successful for connector: {connector_id}")
            
            return credentials
            
        except Exception as e:
            logger.error(f"Authentication failed for connector {connector_id}: {e}")
            return None
    
    def _find_provider_by_type(self, auth_type: AuthenticationType) -> Optional[AuthProvider]:
        """Find a provider by authentication type"""
        for provider in self.auth_providers.values():
            if provider.auth_type == auth_type:
                return provider
        return None
    
    async def _authenticate_oauth2(self, auth_config: Dict[str, Any], provider: AuthProvider,
                                  session: Optional[aiohttp.ClientSession]) -> Optional[AuthCredentials]:
        """Perform OAuth 2.0 authentication"""
        try:
            if not session:
                session = aiohttp.ClientSession()
                should_close_session = True
            else:
                should_close_session = False
            
            try:
                # Extract OAuth 2.0 parameters
                token_url = auth_config.get('token_url') or auth_config.get('base_url', '') + provider.endpoints.get('token', '/oauth/token')
                client_id = auth_config.get('client_id')
                client_secret = auth_config.get('client_secret')
                grant_type = auth_config.get('grant_type', provider.config.get('grant_type', 'client_credentials'))
                scope = auth_config.get('scope', '')
                
                if not all([token_url, client_id, client_secret]):
                    logger.error("OAuth 2.0 configuration incomplete")
                    return None
                
                # Prepare token request
                token_data = {
                    'grant_type': grant_type,
                    'client_id': client_id,
                    'client_secret': client_secret
                }
                
                if scope:
                    token_data['scope'] = scope
                
                # Add grant type specific parameters
                if grant_type == 'authorization_code':
                    code = auth_config.get('code')
                    redirect_uri = auth_config.get('redirect_uri')
                    if code and redirect_uri:
                        token_data['code'] = code
                        token_data['redirect_uri'] = redirect_uri
                    else:
                        logger.error("Authorization code or redirect URI missing")
                        return None
                elif grant_type == 'refresh_token':
                    refresh_token = auth_config.get('refresh_token')
                    if refresh_token:
                        token_data['refresh_token'] = refresh_token
                    else:
                        logger.error("Refresh token missing")
                        return None
                
                # Make token request
                headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                
                async with session.post(token_url, data=token_data, headers=headers) as response:
                    if response.status == 200:
                        token_response = await response.json()
                        
                        access_token = token_response.get('access_token')
                        if not access_token:
                            logger.error("No access token in OAuth response")
                            return None
                        
                        # Calculate expiration time
                        expires_in = token_response.get('expires_in')
                        expires_at = None
                        if expires_in:
                            expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)  # 60 second buffer
                        
                        # Create auth credentials
                        tokens = {
                            TokenType.ACCESS_TOKEN: AuthToken(
                                token_type=TokenType.ACCESS_TOKEN,
                                value=access_token,
                                expires_at=expires_at,
                                scope=token_response.get('scope'),
                                refresh_token=token_response.get('refresh_token')
                            )
                        }
                        
                        # Add refresh token if present
                        refresh_token = token_response.get('refresh_token')
                        if refresh_token:
                            tokens[TokenType.REFRESH_TOKEN] = AuthToken(
                                token_type=TokenType.REFRESH_TOKEN,
                                value=refresh_token
                            )
                        
                        return AuthCredentials(
                            auth_type=AuthenticationType.OAUTH2,
                            credentials=auth_config,
                            tokens=tokens,
                            last_authenticated=datetime.utcnow(),
                            expires_at=expires_at,
                            metadata={'token_response': token_response}
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"OAuth 2.0 token request failed: {response.status} - {error_text}")
                        return None
                        
            finally:
                if should_close_session:
                    await session.close()
                    
        except Exception as e:
            logger.error(f"OAuth 2.0 authentication error: {e}")
            return None
    
    async def _authenticate_basic_auth(self, auth_config: Dict[str, Any], provider: AuthProvider) -> Optional[AuthCredentials]:
        """Perform HTTP Basic authentication"""
        try:
            username = auth_config.get('username')
            password = auth_config.get('password')
            
            if not username or not password:
                logger.error("Username or password not provided for basic auth")
                return None
            
            # Encode credentials
            credentials_string = f"{username}:{password}"
            encoded_credentials = base64.b64encode(credentials_string.encode()).decode()
            
            return AuthCredentials(
                auth_type=AuthenticationType.BASIC_AUTH,
                credentials={
                    'username': username,
                    'password': '***',  # Don't store actual password
                    'encoded': encoded_credentials
                },
                last_authenticated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Basic auth error: {e}")
            return None
    
    async def _authenticate_api_key(self, auth_config: Dict[str, Any], provider: AuthProvider) -> Optional[AuthCredentials]:
        """Perform API key authentication"""
        try:
            api_key = auth_config.get('api_key')
            if not api_key:
                logger.error("API key not provided")
                return None
            
            # API key configuration
            key_header = auth_config.get('header', 'X-API-Key')
            key_query_param = auth_config.get('query_param', 'api_key')
            location = auth_config.get('location', provider.config.get('location', 'header'))
            
            return AuthCredentials(
                auth_type=AuthenticationType.API_KEY,
                credentials={
                    'api_key': api_key,
                    'header': key_header,
                    'query_param': key_query_param,
                    'location': location
                },
                last_authenticated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"API key auth error: {e}")
            return None
    
    async def _authenticate_jwt(self, auth_config: Dict[str, Any], provider: AuthProvider) -> Optional[AuthCredentials]:
        """Perform JWT authentication"""
        try:
            jwt_token = auth_config.get('jwt_token')
            
            if jwt_token:
                # Use provided JWT token
                try:
                    # Decode without verification to get expiration
                    decoded = jwt.decode(jwt_token, options={"verify_signature": False})
                    exp = decoded.get('exp')
                    expires_at = datetime.fromtimestamp(exp) if exp else None
                    
                    return AuthCredentials(
                        auth_type=AuthenticationType.JWT,
                        credentials={'jwt_token': jwt_token},
                        tokens={
                            TokenType.ACCESS_TOKEN: AuthToken(
                                token_type=TokenType.ACCESS_TOKEN,
                                value=jwt_token,
                                expires_at=expires_at
                            )
                        },
                        last_authenticated=datetime.utcnow(),
                        expires_at=expires_at
                    )
                except Exception as e:
                    logger.warning(f"JWT token validation error (proceeding anyway): {e}")
                    # Proceed with token even if validation fails
                    return AuthCredentials(
                        auth_type=AuthenticationType.JWT,
                        credentials={'jwt_token': jwt_token},
                        tokens={
                            TokenType.ACCESS_TOKEN: AuthToken(
                                token_type=TokenType.ACCESS_TOKEN,
                                value=jwt_token
                            )
                        },
                        last_authenticated=datetime.utcnow()
                    )
            else:
                # Generate JWT token if we have the necessary information
                secret = auth_config.get('secret')
                algorithm = auth_config.get('algorithm', 'HS256')
                payload = auth_config.get('payload', {})
                
                if secret and payload:
                    # Add standard claims
                    now = datetime.utcnow()
                    payload.setdefault('iat', int(now.timestamp()))
                    payload.setdefault('exp', int((now + timedelta(hours=1)).timestamp()))
                    
                    token = jwt.encode(payload, secret, algorithm=algorithm)
                    expires_at = datetime.fromtimestamp(payload['exp'])
                    
                    return AuthCredentials(
                        auth_type=AuthenticationType.JWT,
                        credentials={
                            'secret': '***',
                            'algorithm': algorithm,
                            'payload': payload
                        },
                        tokens={
                            TokenType.ACCESS_TOKEN: AuthToken(
                                token_type=TokenType.ACCESS_TOKEN,
                                value=token,
                                expires_at=expires_at
                            )
                        },
                        last_authenticated=datetime.utcnow(),
                        expires_at=expires_at
                    )
                else:
                    logger.error("JWT token or generation parameters not provided")
                    return None
                    
        except Exception as e:
            logger.error(f"JWT auth error: {e}")
            return None
    
    async def _authenticate_saml(self, auth_config: Dict[str, Any], provider: AuthProvider,
                               session: Optional[aiohttp.ClientSession]) -> Optional[AuthCredentials]:
        """Perform SAML authentication"""
        try:
            # SAML authentication is complex and typically requires specific libraries
            # This is a simplified implementation
            
            saml_assertion = auth_config.get('saml_assertion')
            if saml_assertion:
                return AuthCredentials(
                    auth_type=AuthenticationType.SAML,
                    credentials={'saml_assertion': saml_assertion},
                    last_authenticated=datetime.utcnow()
                )
            else:
                logger.error("SAML assertion not provided")
                return None
                
        except Exception as e:
            logger.error(f"SAML auth error: {e}")
            return None
    
    async def _authenticate_custom_token(self, auth_config: Dict[str, Any], provider: AuthProvider) -> Optional[AuthCredentials]:
        """Perform custom token authentication"""
        try:
            token = auth_config.get('token')
            if not token:
                logger.error("Custom token not provided")
                return None
            
            token_header = auth_config.get('header', 'Authorization')
            token_prefix = auth_config.get('prefix', 'Bearer')
            
            return AuthCredentials(
                auth_type=AuthenticationType.CUSTOM_TOKEN,
                credentials={
                    'token': token,
                    'header': token_header,
                    'prefix': token_prefix
                },
                last_authenticated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Custom token auth error: {e}")
            return None
    
    async def refresh_token(self, connector_id: str, session: Optional[aiohttp.ClientSession] = None) -> bool:
        """Refresh authentication token if possible"""
        try:
            if connector_id not in self.active_credentials:
                logger.warning(f"No active credentials found for connector: {connector_id}")
                return False
            
            credentials = self.active_credentials[connector_id]
            
            if credentials.auth_type == AuthenticationType.OAUTH2:
                return await self._refresh_oauth2_token(credentials, session)
            elif credentials.auth_type == AuthenticationType.JWT:
                return await self._refresh_jwt_token(credentials)
            else:
                # For other auth types, re-authenticate
                logger.info(f"Re-authenticating connector {connector_id} (auth type doesn't support refresh)")
                return True  # Assume success for non-refreshable tokens
                
        except Exception as e:
            logger.error(f"Token refresh failed for connector {connector_id}: {e}")
            return False
    
    async def _refresh_oauth2_token(self, credentials: AuthCredentials, session: Optional[aiohttp.ClientSession]) -> bool:
        """Refresh OAuth 2.0 access token"""
        try:
            refresh_token = None
            if TokenType.REFRESH_TOKEN in credentials.tokens:
                refresh_token = credentials.tokens[TokenType.REFRESH_TOKEN].value
            elif TokenType.ACCESS_TOKEN in credentials.tokens:
                refresh_token = credentials.tokens[TokenType.ACCESS_TOKEN].refresh_token
            
            if not refresh_token:
                logger.warning("No refresh token available for OAuth 2.0 refresh")
                return False
            
            # Prepare refresh token request
            refresh_config = credentials.credentials.copy()
            refresh_config['grant_type'] = 'refresh_token'
            refresh_config['refresh_token'] = refresh_token
            
            # Use the same provider that was used initially
            provider = self._find_provider_by_type(AuthenticationType.OAUTH2)
            if not provider:
                return False
            
            # Refresh the token
            new_credentials = await self._authenticate_oauth2(refresh_config, provider, session)
            if new_credentials:
                # Update existing credentials
                credentials.tokens.update(new_credentials.tokens)
                credentials.last_authenticated = new_credentials.last_authenticated
                credentials.expires_at = new_credentials.expires_at
                credentials.metadata.update(new_credentials.metadata)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"OAuth 2.0 token refresh error: {e}")
            return False
    
    async def _refresh_jwt_token(self, credentials: AuthCredentials) -> bool:
        """Refresh JWT token if we have the necessary information"""
        try:
            if 'secret' in credentials.credentials and 'payload' in credentials.credentials:
                # Regenerate JWT token
                secret = credentials.credentials.get('secret')
                algorithm = credentials.credentials.get('algorithm', 'HS256')
                payload = credentials.credentials.get('payload', {}).copy()
                
                # Update timestamps
                now = datetime.utcnow()
                payload['iat'] = int(now.timestamp())
                payload['exp'] = int((now + timedelta(hours=1)).timestamp())
                
                new_token = jwt.encode(payload, secret, algorithm=algorithm)
                expires_at = datetime.fromtimestamp(payload['exp'])
                
                # Update token
                credentials.tokens[TokenType.ACCESS_TOKEN] = AuthToken(
                    token_type=TokenType.ACCESS_TOKEN,
                    value=new_token,
                    expires_at=expires_at
                )
                credentials.last_authenticated = now
                credentials.expires_at = expires_at
                
                return True
            else:
                logger.warning("Cannot refresh JWT token: missing secret or payload")
                return False
                
        except Exception as e:
            logger.error(f"JWT token refresh error: {e}")
            return False
    
    def is_token_valid(self, connector_id: str) -> bool:
        """Check if the authentication token is still valid"""
        try:
            if connector_id not in self.active_credentials:
                return False
            
            credentials = self.active_credentials[connector_id]
            
            # Check expiration
            if credentials.expires_at and credentials.expires_at <= datetime.utcnow():
                return False
            
            # Check individual tokens
            for token in credentials.tokens.values():
                if token.expires_at and token.expires_at <= datetime.utcnow():
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Token validation error for connector {connector_id}: {e}")
            return False
    
    def get_token_status(self, connector_id: str, token_type: TokenType = TokenType.ACCESS_TOKEN) -> TokenStatus:
        """Get the status of a specific token"""
        try:
            if connector_id not in self.active_credentials:
                return TokenStatus.UNKNOWN
            
            credentials = self.active_credentials[connector_id]
            
            if token_type not in credentials.tokens:
                return TokenStatus.UNKNOWN
            
            token = credentials.tokens[token_type]
            
            if token.expires_at and token.expires_at <= datetime.utcnow():
                return TokenStatus.EXPIRED
            
            return TokenStatus.VALID
            
        except Exception as e:
            logger.error(f"Token status check error: {e}")
            return TokenStatus.UNKNOWN
    
    def apply_authentication(self, connector_id: str, headers: Dict[str, str], 
                           params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, str], Optional[Dict[str, Any]]]:
        """Apply authentication to request headers and parameters"""
        try:
            if connector_id not in self.active_credentials:
                return headers, params
            
            credentials = self.active_credentials[connector_id]
            headers = headers.copy()
            params = params.copy() if params else {}
            
            if credentials.auth_type == AuthenticationType.OAUTH2:
                if TokenType.ACCESS_TOKEN in credentials.tokens:
                    token = credentials.tokens[TokenType.ACCESS_TOKEN].value
                    headers['Authorization'] = f"Bearer {token}"
            
            elif credentials.auth_type == AuthenticationType.BASIC_AUTH:
                encoded = credentials.credentials.get('encoded')
                if encoded:
                    headers['Authorization'] = f"Basic {encoded}"
            
            elif credentials.auth_type == AuthenticationType.API_KEY:
                api_key = credentials.credentials.get('api_key')
                location = credentials.credentials.get('location', 'header')
                
                if api_key:
                    if location == 'header':
                        header_name = credentials.credentials.get('header', 'X-API-Key')
                        headers[header_name] = api_key
                    elif location == 'query':
                        param_name = credentials.credentials.get('query_param', 'api_key')
                        params[param_name] = api_key
            
            elif credentials.auth_type == AuthenticationType.JWT:
                if TokenType.ACCESS_TOKEN in credentials.tokens:
                    token = credentials.tokens[TokenType.ACCESS_TOKEN].value
                    headers['Authorization'] = f"Bearer {token}"
            
            elif credentials.auth_type == AuthenticationType.CUSTOM_TOKEN:
                token = credentials.credentials.get('token')
                header_name = credentials.credentials.get('header', 'Authorization')
                prefix = credentials.credentials.get('prefix', 'Bearer')
                
                if token:
                    if prefix:
                        headers[header_name] = f"{prefix} {token}"
                    else:
                        headers[header_name] = token
            
            elif credentials.auth_type == AuthenticationType.SAML:
                saml_assertion = credentials.credentials.get('saml_assertion')
                if saml_assertion:
                    headers['Authorization'] = f"SAML {saml_assertion}"
            
            return headers, params
            
        except Exception as e:
            logger.error(f"Authentication application error: {e}")
            return headers, params
    
    def revoke_credentials(self, connector_id: str) -> bool:
        """Revoke authentication credentials"""
        try:
            if connector_id in self.active_credentials:
                del self.active_credentials[connector_id]
                logger.info(f"Revoked credentials for connector: {connector_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Credential revocation error: {e}")
            return False
    
    def get_authentication_info(self, connector_id: str) -> Optional[Dict[str, Any]]:
        """Get authentication information for a connector"""
        try:
            if connector_id not in self.active_credentials:
                return None
            
            credentials = self.active_credentials[connector_id]
            
            token_info = {}
            for token_type, token in credentials.tokens.items():
                token_info[token_type.value] = {
                    'expires_at': token.expires_at.isoformat() if token.expires_at else None,
                    'scope': token.scope,
                    'status': self.get_token_status(connector_id, token_type).value
                }
            
            return {
                'auth_type': credentials.auth_type.value,
                'last_authenticated': credentials.last_authenticated.isoformat() if credentials.last_authenticated else None,
                'expires_at': credentials.expires_at.isoformat() if credentials.expires_at else None,
                'tokens': token_info,
                'is_valid': self.is_token_valid(connector_id)
            }
            
        except Exception as e:
            logger.error(f"Authentication info retrieval error: {e}")
            return None
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """Get authentication manager statistics"""
        try:
            auth_type_counts = {}
            valid_credentials = 0
            expired_credentials = 0
            
            for connector_id, credentials in self.active_credentials.items():
                auth_type = credentials.auth_type.value
                auth_type_counts[auth_type] = auth_type_counts.get(auth_type, 0) + 1
                
                if self.is_token_valid(connector_id):
                    valid_credentials += 1
                else:
                    expired_credentials += 1
            
            return {
                'total_credentials': len(self.active_credentials),
                'valid_credentials': valid_credentials,
                'expired_credentials': expired_credentials,
                'auth_type_distribution': auth_type_counts,
                'total_providers': len(self.auth_providers),
                'provider_types': list(set(p.auth_type.value for p in self.auth_providers.values()))
            }
            
        except Exception as e:
            logger.error(f"Statistics generation error: {e}")
            return {}

# Global authentication manager instance
authentication_manager = AuthenticationManager()

async def initialize_authentication_manager():
    """Initialize the authentication manager"""
    try:
        logger.info("Authentication manager initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize authentication manager: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_authentication_manager()
        
        # Example usage
        auth_config = {
            'type': 'oauth2',
            'token_url': 'https://api.example.com/oauth/token',
            'client_id': 'test_client',
            'client_secret': 'test_secret',
            'scope': 'read write'
        }
        
        credentials = await authentication_manager.authenticate('test_connector', auth_config)
        if credentials:
            print(f"Authentication successful: {credentials.auth_type.value}")
            
            # Apply authentication to headers
            headers = {'Content-Type': 'application/json'}
            auth_headers, _ = authentication_manager.apply_authentication('test_connector', headers)
            print(f"Authenticated headers: {auth_headers}")
            
            # Get auth info
            auth_info = authentication_manager.get_authentication_info('test_connector')
            print(f"Auth info: {auth_info}")
        
        # Get statistics
        stats = authentication_manager.get_manager_statistics()
        print(f"Manager statistics: {stats}")
    
    asyncio.run(main())