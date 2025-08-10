"""
Role-Based Authentication Middleware
===================================
FastAPI middleware for role-based authentication and user identity verification.
Integrates with existing role management system and JWT validation.
"""
import logging
import jwt
import json
import base64
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from ...core_platform.authentication.role_manager import (
    RoleManager, PlatformRole, RoleScope, UserRoleContext
)
from ..role_routing.models import HTTPRoutingContext
from ..role_routing.role_detector import HTTPRoleDetector

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom authentication error."""
    pass


class RoleAuthenticator(BaseHTTPMiddleware):
    """
    Role-Based Authentication Middleware
    ===================================
    
    **Authentication Methods Supported:**
    - JWT tokens with role claims
    - API keys with role prefixes  
    - Session-based authentication
    - Certificate-based authentication
    - Service-to-service authentication
    
    **Role Validation Features:**
    - Platform role verification
    - Permission-based access control
    - Organization context validation
    - Multi-role support for hybrid users
    - Token expiration and refresh
    """
    
    def __init__(
        self,
        app,
        role_manager: RoleManager,
        role_detector: HTTPRoleDetector,
        jwt_secret_key: str,
        jwt_algorithm: str = "HS256",
        token_expiry_hours: int = 24,
        enable_api_key_auth: bool = True,
        enable_session_auth: bool = True,
        enable_certificate_auth: bool = False,
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Core dependencies
        self.role_manager = role_manager
        self.role_detector = role_detector
        
        # JWT configuration
        self.jwt_secret_key = jwt_secret_key
        self.jwt_algorithm = jwt_algorithm
        self.token_expiry_hours = token_expiry_hours
        
        # Authentication methods
        self.enable_api_key_auth = enable_api_key_auth
        self.enable_session_auth = enable_session_auth
        self.enable_certificate_auth = enable_certificate_auth
        
        # Security configuration
        self.bearer_scheme = HTTPBearer(auto_error=False)
        self.excluded_paths = excluded_paths or [
            "/health", "/docs", "/redoc", "/openapi.json",
            "/api/health", "/api/versions"
        ]
        
        # Authentication cache
        self.auth_cache: Dict[str, Tuple[HTTPRoutingContext, datetime]] = {}
        self.cache_ttl = timedelta(minutes=5)
        
        # API key storage (in production, this would be in a database)
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.session_store: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.auth_metrics = {
            "total_authentications": 0,
            "successful_authentications": 0,
            "failed_authentications": 0,
            "jwt_authentications": 0,
            "api_key_authentications": 0,
            "session_authentications": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        logger.info("RoleAuthenticator middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method."""
        try:
            # Skip authentication for excluded paths
            if self._is_excluded_path(request.url.path):
                return await call_next(request)
            
            self.auth_metrics["total_authentications"] += 1
            
            # Perform authentication
            routing_context = await self._authenticate_request(request)
            
            # Add context to request state
            request.state.routing_context = routing_context
            
            # Continue with request
            response = await call_next(request)
            
            self.auth_metrics["successful_authentications"] += 1
            return response
            
        except HTTPException:
            self.auth_metrics["failed_authentications"] += 1
            raise
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            self.auth_metrics["failed_authentications"] += 1
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error"
            )
    
    async def _authenticate_request(self, request: Request) -> HTTPRoutingContext:
        """Authenticate request and return routing context."""
        
        # Check cache first
        cache_key = self._generate_cache_key(request)
        cached_context = self._get_cached_context(cache_key)
        if cached_context:
            self.auth_metrics["cache_hits"] += 1
            return cached_context
        
        self.auth_metrics["cache_misses"] += 1
        
        # Try different authentication methods
        auth_result = None
        
        # 1. JWT Authentication
        auth_result = await self._try_jwt_authentication(request)
        if auth_result:
            self.auth_metrics["jwt_authentications"] += 1
        
        # 2. API Key Authentication
        if not auth_result and self.enable_api_key_auth:
            auth_result = await self._try_api_key_authentication(request)
            if auth_result:
                self.auth_metrics["api_key_authentications"] += 1
        
        # 3. Session Authentication
        if not auth_result and self.enable_session_auth:
            auth_result = await self._try_session_authentication(request)
            if auth_result:
                self.auth_metrics["session_authentications"] += 1
        
        # 4. Certificate Authentication
        if not auth_result and self.enable_certificate_auth:
            auth_result = await self._try_certificate_authentication(request)
        
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        user_id, auth_data = auth_result
        
        # Build routing context
        routing_context = await self._build_routing_context(request, user_id, auth_data)
        
        # Validate role access
        await self._validate_role_access(routing_context, request)
        
        # Cache the context
        self._cache_context(cache_key, routing_context)
        
        return routing_context
    
    async def _try_jwt_authentication(self, request: Request) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Try JWT token authentication."""
        # Get Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return None
        
        # Check Bearer format
        if not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header[7:]  # Remove "Bearer " prefix
        
        try:
            # Decode and validate JWT
            payload = jwt.decode(
                token, 
                self.jwt_secret_key, 
                algorithms=[self.jwt_algorithm]
            )
            
            # Validate required claims
            if "user_id" not in payload:
                raise AuthenticationError("Missing user_id in token")
            
            # Check expiration
            if "exp" in payload:
                exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
                if datetime.now(timezone.utc) > exp_time:
                    raise AuthenticationError("Token expired")
            
            return payload["user_id"], payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            self.logger.warning(f"JWT authentication error: {str(e)}")
            return None
    
    async def _try_api_key_authentication(self, request: Request) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Try API key authentication."""
        # Check various API key headers
        api_key_headers = [
            "x-api-key", "x-api-token", "api-key", 
            "x-si-api-key", "x-app-api-key", "x-platform-key"
        ]
        
        api_key = None
        for header in api_key_headers:
            api_key = request.headers.get(header)
            if api_key:
                break
        
        if not api_key:
            return None
        
        # Validate API key
        key_data = self.api_keys.get(api_key)
        if not key_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        # Check if key is active
        if not key_data.get("active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key inactive"
            )
        
        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key expired"
            )
        
        return key_data["user_id"], key_data
    
    async def _try_session_authentication(self, request: Request) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Try session-based authentication."""
        # Get session ID from header or cookie
        session_id = request.headers.get("x-session-id")
        if not session_id:
            session_id = request.cookies.get("session_id")
        
        if not session_id:
            return None
        
        # Validate session
        session_data = self.session_store.get(session_id)
        if not session_data:
            return None
        
        # Check session expiration
        expires_at = session_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
            # Clean up expired session
            del self.session_store[session_id]
            return None
        
        return session_data["user_id"], session_data
    
    async def _try_certificate_authentication(self, request: Request) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Try certificate-based authentication."""
        # Check for client certificate headers (set by reverse proxy)
        cert_header = request.headers.get("x-client-certificate")
        cert_dn = request.headers.get("x-ssl-client-dn")
        cert_id = request.headers.get("x-certificate-id")
        
        if not any([cert_header, cert_dn, cert_id]):
            return None
        
        # In a real implementation, validate the certificate
        # For now, return dummy data
        if cert_id:
            return f"cert_user_{cert_id}", {
                "auth_method": "certificate",
                "certificate_id": cert_id,
                "certificate_dn": cert_dn
            }
        
        return None
    
    async def _build_routing_context(
        self, 
        request: Request, 
        user_id: str, 
        auth_data: Dict[str, Any]
    ) -> HTTPRoutingContext:
        """Build HTTP routing context from authentication data."""
        
        # Get user role context from role manager
        user_context = await self.role_manager.get_user_context(user_id)
        
        # Extract organization and tenant info
        organization_id = auth_data.get("organization_id") or auth_data.get("org_id")
        tenant_id = auth_data.get("tenant_id")
        
        # Determine primary platform role
        primary_role = None
        if user_context.platform_roles:
            # Prioritize roles: HYBRID > ADMIN > SI > APP > USER
            role_priority = {
                PlatformRole.HYBRID: 5,
                PlatformRole.PLATFORM_ADMIN: 4,
                PlatformRole.SYSTEM_INTEGRATOR: 3,
                PlatformRole.ACCESS_POINT_PROVIDER: 2,
                PlatformRole.TENANT_ADMIN: 1,
                PlatformRole.USER: 0
            }
            primary_role = max(user_context.platform_roles, 
                             key=lambda r: role_priority.get(r, -1))
        
        # Create routing context
        routing_context = HTTPRoutingContext(
            user_id=user_id,
            organization_id=organization_id,
            tenant_id=tenant_id,
            platform_role=primary_role,
            permissions=list(user_context.effective_permissions),
            session_id=auth_data.get("session_id"),
            api_key=auth_data.get("api_key"),
            client_ip=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent"),
            correlation_id=request.headers.get("x-correlation-id")
        )
        
        # Add authentication metadata
        routing_context.metadata.update({
            "auth_method": auth_data.get("auth_method", "jwt"),
            "auth_timestamp": datetime.now(timezone.utc).isoformat(),
            "user_roles": [role.value for role in user_context.platform_roles],
            "tenant_roles": list(user_context.tenant_roles.keys()),
            "service_roles": list(user_context.service_roles.keys())
        })
        
        return routing_context
    
    async def _validate_role_access(self, routing_context: HTTPRoutingContext, request: Request):
        """Validate that the user has appropriate role access for the request."""
        
        # Use role detector to analyze the request
        analysis = await self.role_detector.analyze_request(request)
        
        # Check if user has required platform role
        if analysis.detected_roles and routing_context.platform_role:
            required_roles = set(analysis.detected_roles)
            user_roles = set()
            
            # Add user's platform role
            user_roles.add(routing_context.platform_role)
            
            # Add HYBRID role if user has both SI and APP
            user_context = await self.role_manager.get_user_context(routing_context.user_id)
            if (PlatformRole.SYSTEM_INTEGRATOR in user_context.platform_roles and 
                PlatformRole.ACCESS_POINT_PROVIDER in user_context.platform_roles):
                user_roles.add(PlatformRole.HYBRID)
            
            # Add ADMIN roles if user has admin permissions
            if PlatformRole.PLATFORM_ADMIN in user_context.platform_roles:
                user_roles.update([PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID])
            
            # Check if user has any of the required roles
            if not (required_roles & user_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied. Required roles: {[r.value for r in required_roles]}"
                )
        
        # Check required permissions
        if analysis.required_permissions:
            missing_permissions = set(analysis.required_permissions) - set(routing_context.permissions)
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {list(missing_permissions)}"
                )
    
    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key for authentication context."""
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")
        session_id = request.headers.get("x-session-id", "") or request.cookies.get("session_id", "")
        
        # Use hash of auth information
        import hashlib
        auth_string = f"{auth_header}:{api_key}:{session_id}"
        return hashlib.md5(auth_string.encode()).hexdigest()
    
    def _get_cached_context(self, cache_key: str) -> Optional[HTTPRoutingContext]:
        """Get cached authentication context if valid."""
        if cache_key in self.auth_cache:
            context, cached_at = self.auth_cache[cache_key]
            if datetime.now(timezone.utc) - cached_at < self.cache_ttl:
                return context
            else:
                # Remove expired cache entry
                del self.auth_cache[cache_key]
        return None
    
    def _cache_context(self, cache_key: str, context: HTTPRoutingContext):
        """Cache authentication context."""
        self.auth_cache[cache_key] = (context, datetime.now(timezone.utc))
        
        # Clean up old cache entries
        if len(self.auth_cache) > 1000:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key for key, (_, cached_at) in self.auth_cache.items()
                if now - cached_at > self.cache_ttl
            ]
            for key in expired_keys:
                del self.auth_cache[key]
    
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from authentication."""
        for excluded in self.excluded_paths:
            if path.startswith(excluded) or path == excluded:
                return True
        return False
    
    def _get_client_ip(self, request: Request) -> Optional[str]:
        """Get client IP from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return None
    
    # API key management methods
    async def create_api_key(
        self, 
        user_id: str, 
        name: str, 
        role: PlatformRole,
        organization_id: Optional[str] = None,
        expires_in_days: Optional[int] = None
    ) -> str:
        """Create a new API key for a user."""
        import secrets
        
        # Generate secure API key
        api_key = f"{role.value[:3]}_" + secrets.token_urlsafe(32)
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.now(timezone.utc) + timedelta(days=expires_in_days)).isoformat()
        
        # Store API key data
        self.api_keys[api_key] = {
            "user_id": user_id,
            "name": name,
            "role": role.value,
            "organization_id": organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "active": True,
            "auth_method": "api_key"
        }
        
        self.logger.info(f"Created API key for user {user_id}: {name}")
        return api_key
    
    async def revoke_api_key(self, api_key: str) -> bool:
        """Revoke an API key."""
        if api_key in self.api_keys:
            self.api_keys[api_key]["active"] = False
            self.logger.info(f"Revoked API key: {api_key[:10]}...")
            return True
        return False
    
    async def create_session(
        self, 
        user_id: str, 
        organization_id: Optional[str] = None,
        expires_in_hours: int = 24
    ) -> str:
        """Create a new session for a user."""
        import secrets
        
        session_id = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)).isoformat()
        
        self.session_store[session_id] = {
            "user_id": user_id,
            "organization_id": organization_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,
            "auth_method": "session"
        }
        
        return session_id
    
    async def get_auth_metrics(self) -> Dict[str, Any]:
        """Get authentication metrics."""
        return {
            "metrics": self.auth_metrics.copy(),
            "cache_size": len(self.auth_cache),
            "api_keys_count": len(self.api_keys),
            "active_sessions": len(self.session_store),
            "cache_hit_ratio": (
                self.auth_metrics["cache_hits"] / 
                (self.auth_metrics["cache_hits"] + self.auth_metrics["cache_misses"])
                if (self.auth_metrics["cache_hits"] + self.auth_metrics["cache_misses"]) > 0
                else 0
            )
        }


def create_role_authenticator(
    role_manager: RoleManager,
    role_detector: HTTPRoleDetector,
    jwt_secret_key: str,
    **kwargs
) -> RoleAuthenticator:
    """Factory function to create RoleAuthenticator middleware."""
    return RoleAuthenticator(
        app=None,  # Will be set when added to FastAPI app
        role_manager=role_manager,
        role_detector=role_detector,
        jwt_secret_key=jwt_secret_key,
        **kwargs
    )