"""
FIRS API Authentication Service

This module provides authentication services specifically for FIRS (Federal Inland
Revenue Service) API integration, handling various FIRS authentication methods,
API key management, and secure communication protocols for SI services.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
import hmac
import base64
import secrets
import aiohttp
import ssl
from urllib.parse import urlencode, parse_qs

from .auth_manager import (
    BaseAuthProvider,
    AuthenticationType,
    AuthenticationContext,
    AuthenticationCredentials,
    AuthenticationResult,
    AuthenticationStatus,
    AuthenticationScope,
    ServiceType
)

logger = logging.getLogger(__name__)


class FIRSEnvironment(Enum):
    """FIRS environment types"""
    SANDBOX = "sandbox"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


class FIRSAPIVersion(Enum):
    """FIRS API versions"""
    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


class FIRSAuthMethod(Enum):
    """FIRS authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    CERTIFICATE = "certificate"
    BASIC_AUTH = "basic_auth"
    DIGEST_AUTH = "digest_auth"
    BEARER_TOKEN = "bearer_token"


class FIRSServiceType(Enum):
    """FIRS service types"""
    IRN_GENERATION = "irn_generation"
    DOCUMENT_SUBMISSION = "document_submission"
    STATUS_INQUIRY = "status_inquiry"
    CERTIFICATE_VALIDATION = "certificate_validation"
    TAXPAYER_LOOKUP = "taxpayer_lookup"
    DOCUMENT_CANCELLATION = "document_cancellation"
    BULK_OPERATIONS = "bulk_operations"


@dataclass
class FIRSEndpointConfig:
    """Configuration for FIRS API endpoints"""
    base_url: str
    api_version: FIRSAPIVersion
    environment: FIRSEnvironment
    endpoints: Dict[str, str] = field(default_factory=dict)
    default_headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_per_minute: int = 100


@dataclass
class FIRSAuthConfig:
    """Configuration for FIRS authentication"""
    auth_method: FIRSAuthMethod
    endpoint_config: FIRSEndpointConfig
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    api_key: Optional[str] = None
    certificate_path: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    scope: List[str] = field(default_factory=list)
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FIRSSession:
    """FIRS API session information"""
    session_id: str
    access_token: str
    token_type: str = "Bearer"
    expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    scope: List[str] = field(default_factory=list)
    rate_limit_remaining: int = 100
    rate_limit_reset: Optional[datetime] = None
    last_request_time: datetime = field(default_factory=datetime.now)
    request_count: int = 0
    session_metadata: Dict[str, Any] = field(default_factory=dict)


class FIRSAuthService(BaseAuthProvider):
    """FIRS API authentication service"""
    
    def __init__(self):
        super().__init__("firs_auth", AuthenticationType.API_KEY)
        self.http_session: Optional[aiohttp.ClientSession] = None
        self.auth_configs: Dict[str, FIRSAuthConfig] = {}
        self.active_sessions: Dict[str, FIRSSession] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # FIRS endpoint configurations
        self.default_endpoints = {
            FIRSEnvironment.SANDBOX: {
                "base_url": "https://sandbox-api.firs.gov.ng",
                "endpoints": {
                    "auth": "/oauth/token",
                    "irn_generate": "/api/v1/irn/generate",
                    "irn_status": "/api/v1/irn/status",
                    "document_submit": "/api/v1/documents/submit",
                    "taxpayer_lookup": "/api/v1/taxpayers/lookup",
                    "certificate_validate": "/api/v1/certificates/validate"
                }
            },
            FIRSEnvironment.PRODUCTION: {
                "base_url": "https://api.firs.gov.ng",
                "endpoints": {
                    "auth": "/oauth/token",
                    "irn_generate": "/api/v1/irn/generate",
                    "irn_status": "/api/v1/irn/status",
                    "document_submit": "/api/v1/documents/submit",
                    "taxpayer_lookup": "/api/v1/taxpayers/lookup",
                    "certificate_validate": "/api/v1/certificates/validate"
                }
            }
        }
    
    async def initialize(self) -> None:
        """Initialize FIRS authentication service"""
        try:
            # Setup HTTP session
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=20,
                ssl=ssl.create_default_context()
            )
            
            timeout = aiohttp.ClientTimeout(total=300)
            self.http_session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            )
            
            logger.info("FIRS authentication service initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize FIRS auth service: {e}")
            raise
    
    async def shutdown(self) -> None:
        """Shutdown FIRS authentication service"""
        try:
            if self.http_session:
                await self.http_session.close()
            
            # Revoke active sessions
            for session in self.active_sessions.values():
                await self._revoke_firs_session(session)
            
            logger.info("FIRS authentication service shutdown")
            
        except Exception as e:
            logger.error(f"FIRS auth service shutdown error: {e}")
    
    def register_firs_config(
        self,
        service_identifier: str,
        config: FIRSAuthConfig
    ) -> None:
        """Register FIRS authentication configuration"""
        try:
            self.auth_configs[service_identifier] = config
            logger.info(f"Registered FIRS config for {service_identifier}")
        except Exception as e:
            logger.error(f"Failed to register FIRS config: {e}")
    
    async def authenticate(
        self,
        credentials: AuthenticationCredentials,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate with FIRS API"""
        try:
            config = self.auth_configs.get(credentials.service_identifier)
            if not config:
                return self._create_failed_result(credentials, "No FIRS configuration found")
            
            # Check rate limits
            if not await self._check_rate_limits(credentials.service_identifier):
                return self._create_failed_result(credentials, "Rate limit exceeded")
            
            # Authenticate based on method
            if config.auth_method == FIRSAuthMethod.API_KEY:
                return await self._authenticate_api_key(credentials, config, context)
            elif config.auth_method == FIRSAuthMethod.OAUTH2:
                return await self._authenticate_oauth2(credentials, config, context)
            elif config.auth_method == FIRSAuthMethod.CERTIFICATE:
                return await self._authenticate_certificate(credentials, config, context)
            elif config.auth_method == FIRSAuthMethod.BEARER_TOKEN:
                return await self._authenticate_bearer(credentials, config, context)
            else:
                return self._create_failed_result(
                    credentials,
                    f"Unsupported FIRS auth method: {config.auth_method}"
                )
                
        except Exception as e:
            logger.error(f"FIRS authentication failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_api_key(
        self,
        credentials: AuthenticationCredentials,
        config: FIRSAuthConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using FIRS API key"""
        try:
            # Test API key with a simple request
            test_url = f"{config.endpoint_config.base_url}/api/v1/health"
            
            headers = {
                "X-API-Key": credentials.api_key or config.api_key,
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-SI/1.0",
                **config.endpoint_config.default_headers
            }
            
            async with self.http_session.get(test_url, headers=headers) as response:
                if response.status in [200, 404]:  # 404 is OK if health endpoint doesn't exist
                    # API key is valid, create session
                    session = FIRSSession(
                        session_id=f"firs_{secrets.token_hex(8)}",
                        access_token=credentials.api_key or config.api_key,
                        token_type="API-Key",
                        scope=config.scope,
                        session_metadata={
                            "auth_method": "api_key",
                            "environment": config.endpoint_config.environment.value
                        }
                    )
                    
                    self.active_sessions[session.session_id] = session
                    
                    return self._create_success_result(credentials, session)
                else:
                    error_text = await response.text()
                    return self._create_failed_result(
                        credentials,
                        f"API key validation failed: HTTP {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"FIRS API key auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_oauth2(
        self,
        credentials: AuthenticationCredentials,
        config: FIRSAuthConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using FIRS OAuth2"""
        try:
            token_url = f"{config.endpoint_config.base_url}{config.endpoint_config.endpoints.get('auth', '/oauth/token')}"
            
            # Prepare OAuth2 request
            token_data = {
                "grant_type": "client_credentials",
                "client_id": credentials.oauth_client_id or config.client_id,
                "client_secret": credentials.oauth_client_secret or config.client_secret,
                "scope": " ".join(config.scope) if config.scope else "read write"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "TaxPoynt-SI/1.0",
                **config.endpoint_config.default_headers
            }
            
            async with self.http_session.post(
                token_url,
                data=urlencode(token_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    token_result = await response.json()
                    
                    access_token = token_result.get("access_token")
                    if access_token:
                        # Calculate expiration
                        expires_in = token_result.get("expires_in", 3600)
                        expires_at = datetime.now() + timedelta(seconds=expires_in)
                        
                        session = FIRSSession(
                            session_id=f"firs_oauth_{secrets.token_hex(8)}",
                            access_token=access_token,
                            token_type=token_result.get("token_type", "Bearer"),
                            expires_at=expires_at,
                            refresh_token=token_result.get("refresh_token"),
                            scope=config.scope,
                            session_metadata={
                                "auth_method": "oauth2",
                                "environment": config.endpoint_config.environment.value,
                                "client_id": credentials.oauth_client_id or config.client_id
                            }
                        )
                        
                        self.active_sessions[session.session_id] = session
                        
                        return self._create_success_result(credentials, session)
                    else:
                        return self._create_failed_result(credentials, "No access token received")
                else:
                    error_text = await response.text()
                    return self._create_failed_result(
                        credentials,
                        f"OAuth2 authentication failed: HTTP {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"FIRS OAuth2 auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_certificate(
        self,
        credentials: AuthenticationCredentials,
        config: FIRSAuthConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using FIRS client certificate"""
        try:
            # This would integrate with the certificate authentication provider
            # For now, we'll create a placeholder implementation
            
            cert_path = credentials.certificate_path or config.certificate_path
            if not cert_path:
                return self._create_failed_result(credentials, "No certificate path provided")
            
            # Test certificate authentication
            test_url = f"{config.endpoint_config.base_url}/api/v1/auth/certificate"
            
            # Create SSL context with client certificate
            ssl_context = ssl.create_default_context()
            if credentials.certificate_path:
                ssl_context.load_cert_chain(
                    credentials.certificate_path,
                    keyfile=credentials.private_key_path,
                    password=credentials.password
                )
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-SI/1.0",
                **config.endpoint_config.default_headers
            }
            
            async with self.http_session.get(
                test_url,
                headers=headers,
                ssl=ssl_context
            ) as response:
                if response.status == 200:
                    cert_result = await response.json()
                    
                    # Extract certificate-based session token
                    session_token = cert_result.get("session_token", f"cert_{secrets.token_hex(8)}")
                    
                    session = FIRSSession(
                        session_id=f"firs_cert_{secrets.token_hex(8)}",
                        access_token=session_token,
                        token_type="Certificate",
                        scope=config.scope,
                        session_metadata={
                            "auth_method": "certificate",
                            "environment": config.endpoint_config.environment.value,
                            "certificate_path": cert_path
                        }
                    )
                    
                    self.active_sessions[session.session_id] = session
                    
                    return self._create_success_result(credentials, session)
                else:
                    error_text = await response.text()
                    return self._create_failed_result(
                        credentials,
                        f"Certificate authentication failed: HTTP {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"FIRS certificate auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def _authenticate_bearer(
        self,
        credentials: AuthenticationCredentials,
        config: FIRSAuthConfig,
        context: AuthenticationContext
    ) -> AuthenticationResult:
        """Authenticate using FIRS bearer token"""
        try:
            bearer_token = credentials.token or credentials.custom_params.get("bearer_token")
            if not bearer_token:
                return self._create_failed_result(credentials, "No bearer token provided")
            
            # Test bearer token
            test_url = f"{config.endpoint_config.base_url}/api/v1/auth/validate"
            
            headers = {
                "Authorization": f"Bearer {bearer_token}",
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-SI/1.0",
                **config.endpoint_config.default_headers
            }
            
            async with self.http_session.get(test_url, headers=headers) as response:
                if response.status == 200:
                    session = FIRSSession(
                        session_id=f"firs_bearer_{secrets.token_hex(8)}",
                        access_token=bearer_token,
                        token_type="Bearer",
                        scope=config.scope,
                        session_metadata={
                            "auth_method": "bearer_token",
                            "environment": config.endpoint_config.environment.value
                        }
                    )
                    
                    self.active_sessions[session.session_id] = session
                    
                    return self._create_success_result(credentials, session)
                else:
                    error_text = await response.text()
                    return self._create_failed_result(
                        credentials,
                        f"Bearer token validation failed: HTTP {response.status} - {error_text}"
                    )
                    
        except Exception as e:
            logger.error(f"FIRS bearer auth failed: {e}")
            return self._create_failed_result(credentials, str(e))
    
    async def validate_token(self, token: str, context: AuthenticationContext) -> bool:
        """Validate FIRS API token"""
        try:
            # Find session by token
            for session in self.active_sessions.values():
                if session.access_token == token:
                    # Check if session is still valid
                    if session.expires_at and datetime.now() > session.expires_at:
                        return False
                    
                    return True
            
            return False
            
        except Exception:
            return False
    
    async def refresh_token(
        self,
        refresh_token: str,
        context: AuthenticationContext
    ) -> Optional[AuthenticationResult]:
        """Refresh FIRS API token"""
        try:
            # Find session with refresh token
            session = None
            for s in self.active_sessions.values():
                if s.refresh_token == refresh_token:
                    session = s
                    break
            
            if not session:
                return None
            
            # Find config for this session
            config = None
            for service_id, cfg in self.auth_configs.items():
                if cfg.auth_method == FIRSAuthMethod.OAUTH2:
                    config = cfg
                    break
            
            if not config:
                return None
            
            # Refresh token
            token_url = f"{config.endpoint_config.base_url}{config.endpoint_config.endpoints.get('auth', '/oauth/token')}"
            
            refresh_data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": config.client_id,
                "client_secret": config.client_secret
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "TaxPoynt-SI/1.0"
            }
            
            async with self.http_session.post(
                token_url,
                data=urlencode(refresh_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    token_result = await response.json()
                    
                    new_access_token = token_result.get("access_token")
                    if new_access_token:
                        # Update session
                        expires_in = token_result.get("expires_in", 3600)
                        session.access_token = new_access_token
                        session.expires_at = datetime.now() + timedelta(seconds=expires_in)
                        session.refresh_token = token_result.get("refresh_token", refresh_token)
                        
                        # Create new authentication result
                        credentials = AuthenticationCredentials(
                            credential_id="refreshed",
                            auth_type=AuthenticationType.OAUTH2,
                            service_identifier="firs_api",
                            oauth_client_id=config.client_id
                        )
                        
                        return self._create_success_result(credentials, session)
            
            return None
            
        except Exception as e:
            logger.error(f"FIRS token refresh failed: {e}")
            return None
    
    async def revoke_token(self, token: str, context: AuthenticationContext) -> bool:
        """Revoke FIRS API token"""
        try:
            # Find and remove session
            session_to_remove = None
            for session_id, session in self.active_sessions.items():
                if session.access_token == token:
                    session_to_remove = session_id
                    break
            
            if session_to_remove:
                session = self.active_sessions[session_to_remove]
                await self._revoke_firs_session(session)
                del self.active_sessions[session_to_remove]
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"FIRS token revocation failed: {e}")
            return False
    
    async def _revoke_firs_session(self, session: FIRSSession) -> None:
        """Revoke FIRS session on server side"""
        try:
            # Find config for this session
            config = None
            auth_method = session.session_metadata.get("auth_method")
            
            for cfg in self.auth_configs.values():
                if cfg.auth_method.value == auth_method:
                    config = cfg
                    break
            
            if not config:
                return
            
            # Call revocation endpoint if available
            revoke_url = f"{config.endpoint_config.base_url}/oauth/revoke"
            
            revoke_data = {
                "token": session.access_token,
                "token_type_hint": "access_token"
            }
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"{session.token_type} {session.access_token}"
            }
            
            async with self.http_session.post(
                revoke_url,
                data=urlencode(revoke_data),
                headers=headers
            ) as response:
                if response.status == 200:
                    logger.info(f"Successfully revoked FIRS session {session.session_id}")
                else:
                    logger.warning(f"Failed to revoke FIRS session: HTTP {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to revoke FIRS session: {e}")
    
    async def _check_rate_limits(self, service_identifier: str) -> bool:
        """Check FIRS API rate limits"""
        try:
            current_time = datetime.now()
            
            if service_identifier not in self.rate_limits:
                self.rate_limits[service_identifier] = {
                    "requests": [],
                    "limit": 100,  # Default rate limit
                    "window_minutes": 1
                }
            
            rate_limit = self.rate_limits[service_identifier]
            
            # Remove old requests outside the window
            window_start = current_time - timedelta(minutes=rate_limit["window_minutes"])
            rate_limit["requests"] = [
                req_time for req_time in rate_limit["requests"]
                if req_time > window_start
            ]
            
            # Check if within limit
            if len(rate_limit["requests"]) >= rate_limit["limit"]:
                return False
            
            # Add current request
            rate_limit["requests"].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    def _create_success_result(
        self,
        credentials: AuthenticationCredentials,
        session: FIRSSession
    ) -> AuthenticationResult:
        """Create successful FIRS authentication result"""
        return AuthenticationResult(
            session_id=session.session_id,
            status=AuthenticationStatus.AUTHENTICATED,
            auth_type=credentials.auth_type,
            service_identifier=credentials.service_identifier,
            authenticated_at=datetime.now(),
            expires_at=session.expires_at,
            granted_scopes=[AuthenticationScope.FIRS_API],
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            service_metadata={
                "firs_session": session.__dict__,
                "token_type": session.token_type,
                "environment": session.session_metadata.get("environment"),
                "auth_method": session.session_metadata.get("auth_method")
            }
        )
    
    def _create_failed_result(
        self,
        credentials: AuthenticationCredentials,
        error_message: str
    ) -> AuthenticationResult:
        """Create failed FIRS authentication result"""
        return AuthenticationResult(
            session_id=f"firs_failed_{secrets.token_hex(4)}",
            status=AuthenticationStatus.FAILED,
            auth_type=credentials.auth_type,
            service_identifier=credentials.service_identifier,
            authenticated_at=datetime.now(),
            error_message=error_message
        )
    
    async def get_firs_session(self, session_id: str) -> Optional[FIRSSession]:
        """Get FIRS session by ID"""
        return self.active_sessions.get(session_id)
    
    async def list_firs_sessions(self) -> List[Dict[str, Any]]:
        """List all active FIRS sessions"""
        try:
            sessions = []
            
            for session in self.active_sessions.values():
                sessions.append({
                    "session_id": session.session_id,
                    "token_type": session.token_type,
                    "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                    "scope": session.scope,
                    "rate_limit_remaining": session.rate_limit_remaining,
                    "request_count": session.request_count,
                    "last_request_time": session.last_request_time.isoformat(),
                    "environment": session.session_metadata.get("environment"),
                    "auth_method": session.session_metadata.get("auth_method")
                })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to list FIRS sessions: {e}")
            return []
    
    async def make_authenticated_request(
        self,
        session_id: str,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Make authenticated request to FIRS API"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                logger.error(f"FIRS session not found: {session_id}")
                return None
            
            # Check if session is still valid
            if session.expires_at and datetime.now() > session.expires_at:
                logger.error(f"FIRS session expired: {session_id}")
                return None
            
            # Check rate limits
            if session.rate_limit_remaining <= 0:
                if session.rate_limit_reset and datetime.now() < session.rate_limit_reset:
                    logger.warning(f"FIRS rate limit exceeded for session: {session_id}")
                    return None
                else:
                    # Reset rate limit
                    session.rate_limit_remaining = 100
                    session.rate_limit_reset = datetime.now() + timedelta(minutes=1)
            
            # Find config for this session
            config = None
            auth_method = session.session_metadata.get("auth_method")
            
            for cfg in self.auth_configs.values():
                if cfg.auth_method.value == auth_method:
                    config = cfg
                    break
            
            if not config:
                logger.error("No config found for FIRS session")
                return None
            
            # Build request URL
            base_url = config.endpoint_config.base_url
            if endpoint.startswith("/"):
                url = f"{base_url}{endpoint}"
            else:
                url = f"{base_url}/{endpoint}"
            
            # Prepare headers
            headers = {
                "Authorization": f"{session.token_type} {session.access_token}",
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-SI/1.0",
                **config.endpoint_config.default_headers
            }
            
            # Make request
            async with self.http_session.request(
                method,
                url,
                json=data,
                params=params,
                headers=headers
            ) as response:
                # Update rate limit info
                session.rate_limit_remaining = int(response.headers.get("X-RateLimit-Remaining", session.rate_limit_remaining - 1))
                session.request_count += 1
                session.last_request_time = datetime.now()
                
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"FIRS API request failed: HTTP {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"FIRS authenticated request failed: {e}")
            return None
    
    def get_default_endpoint_config(self, environment: FIRSEnvironment) -> Optional[Dict[str, Any]]:
        """Get default FIRS endpoint configuration"""
        return self.default_endpoints.get(environment)
    
    def create_firs_config(
        self,
        environment: FIRSEnvironment,
        auth_method: FIRSAuthMethod,
        **kwargs
    ) -> FIRSAuthConfig:
        """Create FIRS authentication configuration"""
        try:
            default_config = self.get_default_endpoint_config(environment)
            if not default_config:
                raise ValueError(f"No default config for environment: {environment}")
            
            endpoint_config = FIRSEndpointConfig(
                base_url=default_config["base_url"],
                api_version=FIRSAPIVersion.V1,
                environment=environment,
                endpoints=default_config["endpoints"],
                default_headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                }
            )
            
            return FIRSAuthConfig(
                auth_method=auth_method,
                endpoint_config=endpoint_config,
                **kwargs
            )
            
        except Exception as e:
            logger.error(f"Failed to create FIRS config: {e}")
            raise


# Factory function for creating FIRS auth service
def create_firs_auth_service() -> FIRSAuthService:
    """Factory function to create FIRS authentication service"""
    return FIRSAuthService()