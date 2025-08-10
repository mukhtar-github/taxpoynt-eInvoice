"""
API Permission Guard
===================
FastAPI middleware for role-based endpoint protection and access control.
Enforces permissions, rate limiting, and security policies at the API gateway level.
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# Import from NEW architecture core components
from ...core_platform.authentication.role_manager import PlatformRole, RoleScope
from ...core_platform.messaging.message_router import ServiceRole

from .models import (
    HTTPRoutingContext, APIEndpointRule, RoutePermission, 
    RoutingDecision, RouteType, PermissionLevel, HTTPMethod
)
from .role_detector import HTTPRoleDetector

logger = logging.getLogger(__name__)


class RateLimitViolation(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


class PermissionDenied(Exception):
    """Exception raised when permission is denied."""
    pass


class APIPermissionGuard(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces role-based access control and security policies.
    
    Features:
    - Role-based endpoint protection
    - Rate limiting per user/IP/endpoint
    - Request validation and sanitization
    - Security header enforcement
    - Audit logging for access attempts
    - Integration with role detector and message router
    """

    def __init__(
        self, 
        app,
        role_detector: Optional[HTTPRoleDetector] = None,
        enable_rate_limiting: bool = True,
        enable_audit_logging: bool = True,
        default_rate_limit: int = 100,  # requests per minute
        security_headers: bool = True
    ):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.role_detector = role_detector or HTTPRoleDetector()
        
        # Configuration
        self.enable_rate_limiting = enable_rate_limiting
        self.enable_audit_logging = enable_audit_logging
        self.default_rate_limit = default_rate_limit
        self.security_headers = security_headers
        
        # Security rules and permissions
        self.endpoint_rules: Dict[str, APIEndpointRule] = {}
        self.route_permissions: Dict[str, RoutePermission] = {}
        self.protected_endpoints: Set[str] = set()
        
        # Rate limiting
        self.rate_limit_buckets: Dict[str, deque] = defaultdict(deque)
        self.rate_limit_config: Dict[str, Dict[str, int]] = {}
        
        # Security policies
        self.ip_whitelist: Set[str] = set()
        self.ip_blacklist: Set[str] = set()
        self.blocked_user_agents: List[str] = []
        
        # Metrics and monitoring
        self.access_stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "denied_requests": 0,
            "rate_limited_requests": 0,
            "authentication_failures": 0,
            "authorization_failures": 0
        }
        
        # Initialize default rules
        self._initialize_default_rules()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Main middleware dispatch method that processes all requests.
        
        Args:
            request: FastAPI Request object
            call_next: Next middleware/handler in chain
            
        Returns:
            Response object
        """
        start_time = time.time()
        
        try:
            self.access_stats["total_requests"] += 1
            
            # Security pre-checks
            await self._perform_security_checks(request)
            
            # Detect role context
            routing_context = await self.role_detector.detect_role_context(request)
            
            # Make routing decision
            decision = await self._make_routing_decision(request, routing_context)
            
            # Enforce access control
            await self._enforce_access_control(request, routing_context, decision)
            
            # Rate limiting check
            if self.enable_rate_limiting:
                await self._check_rate_limits(request, routing_context)
            
            # Add routing context to request state
            request.state.routing_context = routing_context
            request.state.routing_decision = decision
            
            # Process request
            response = await call_next(request)
            
            # Post-process response
            response = await self._post_process_response(request, response, routing_context)
            
            # Log successful access
            if self.enable_audit_logging:
                await self._log_access_attempt(request, routing_context, decision, True, None)
            
            self.access_stats["allowed_requests"] += 1
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            self.access_stats["denied_requests"] += 1
            
            if e.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                self.access_stats["rate_limited_requests"] += 1
            elif e.status_code == status.HTTP_401_UNAUTHORIZED:
                self.access_stats["authentication_failures"] += 1
            elif e.status_code == status.HTTP_403_FORBIDDEN:
                self.access_stats["authorization_failures"] += 1
            
            # Log failed access
            if self.enable_audit_logging:
                routing_context = getattr(request.state, "routing_context", None)
                decision = getattr(request.state, "routing_decision", None)
                await self._log_access_attempt(request, routing_context, decision, False, str(e))
            
            # Return error response
            return JSONResponse(
                status_code=e.status_code,
                content={"error": e.detail, "timestamp": datetime.now(timezone.utc).isoformat()}
            )
            
        except Exception as e:
            self.logger.error(f"Unexpected error in permission guard: {str(e)}")
            self.access_stats["denied_requests"] += 1
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "timestamp": datetime.now(timezone.utc).isoformat()}
            )
        
        finally:
            # Record processing time
            processing_time = (time.time() - start_time) * 1000
            if hasattr(request.state, "routing_decision"):
                request.state.routing_decision.processing_time_ms = processing_time

    async def add_endpoint_rule(self, rule: APIEndpointRule):
        """Add or update an endpoint access rule."""
        self.endpoint_rules[rule.path_pattern] = rule
        if rule.require_authentication:
            self.protected_endpoints.add(rule.path_pattern)
        
        # Configure rate limiting for this endpoint
        if rule.rate_limit_per_minute:
            self.rate_limit_config[rule.path_pattern] = {
                "requests_per_minute": rule.rate_limit_per_minute,
                "burst_limit": rule.burst_limit or rule.rate_limit_per_minute
            }
        
        self.logger.info(f"Added endpoint rule: {rule.name} -> {rule.path_pattern}")

    async def add_route_permission(self, permission: RoutePermission):
        """Add route-specific permission configuration."""
        self.route_permissions[permission.route_pattern] = permission
        self.logger.info(f"Added route permission: {permission.route_pattern}")

    async def _perform_security_checks(self, request: Request):
        """Perform basic security checks on the request."""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # IP blacklist check
        if client_ip in self.ip_blacklist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied from this IP address"
            )
        
        # User agent blacklist check
        for blocked_agent in self.blocked_user_agents:
            if blocked_agent.lower() in user_agent.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied for this user agent"
                )
        
        # Request size check (prevent large payload attacks)
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Request payload too large"
            )

    async def _make_routing_decision(
        self, 
        request: Request, 
        routing_context: HTTPRoutingContext
    ) -> RoutingDecision:
        """Make routing decision based on request and context."""
        decision = RoutingDecision(
            request_context=routing_context,
            allowed=False
        )
        
        path = str(request.url.path)
        method = request.method
        
        # Find applicable endpoint rules
        applicable_rules = []
        for pattern, rule in self.endpoint_rules.items():
            if self._path_matches_pattern(path, pattern):
                if not rule.methods or HTTPMethod(method) in rule.methods:
                    applicable_rules.append(rule)
                    decision.applied_rules.append(rule.rule_id)
        
        # If no specific rules, check for default behavior
        if not applicable_rules:
            # Determine target router based on path
            if "/api/" in path:
                if "/si/" in path or "/integration/" in path:
                    decision.target_router = "si"
                elif "/app/" in path or "/transmission/" in path:
                    decision.target_router = "app"
                elif "/hybrid/" in path or "/analytics/" in path:
                    decision.target_router = "hybrid"
                else:
                    decision.target_router = "hybrid"  # Default for unspecified API paths
            else:
                decision.target_router = "public"
            
            decision.allowed = True  # Allow by default if no specific rules
            return decision
        
        # Process applicable rules
        for rule in applicable_rules:
            # Check role requirements
            if rule.allowed_platform_roles:
                if routing_context.platform_role not in rule.allowed_platform_roles:
                    decision.permission_checks[f"platform_role_{rule.rule_id}"] = False
                    continue
                else:
                    decision.permission_checks[f"platform_role_{rule.rule_id}"] = True
            
            # Check service role requirements
            if rule.allowed_service_roles:
                if routing_context.service_role not in rule.allowed_service_roles:
                    decision.permission_checks[f"service_role_{rule.rule_id}"] = False
                    continue
                else:
                    decision.permission_checks[f"service_role_{rule.rule_id}"] = True
            
            # Check permission requirements
            if rule.required_permissions:
                missing_permissions = set(rule.required_permissions) - set(routing_context.permissions)
                if missing_permissions:
                    decision.permission_checks[f"permissions_{rule.rule_id}"] = False
                    decision.role_validation_results[f"missing_permissions_{rule.rule_id}"] = list(missing_permissions)
                    continue
                else:
                    decision.permission_checks[f"permissions_{rule.rule_id}"] = True
            
            # Check authentication requirements
            if rule.require_authentication and not routing_context.user_id:
                decision.permission_checks[f"authentication_{rule.rule_id}"] = False
                continue
            else:
                decision.permission_checks[f"authentication_{rule.rule_id}"] = True
            
            # Check organization context requirements
            if rule.require_organization_context and not routing_context.organization_id:
                decision.permission_checks[f"organization_context_{rule.rule_id}"] = False
                continue
            else:
                decision.permission_checks[f"organization_context_{rule.rule_id}"] = True
            
            # If we get here, the rule allows access
            decision.allowed = True
            decision.target_router = self._determine_target_router(rule)
            decision.forward_to_message_router = rule.forward_to_message_router
            
            # Add transformations
            decision.apply_transformations.extend(rule.request_transformers)
            
            break  # Use first matching rule
        
        return decision

    async def _enforce_access_control(
        self,
        request: Request,
        routing_context: HTTPRoutingContext,
        decision: RoutingDecision
    ):
        """Enforce access control based on routing decision."""
        if not decision.allowed:
            # Determine specific error type
            auth_failed = any(
                not result for key, result in decision.permission_checks.items() 
                if "authentication" in key
            )
            
            if auth_failed:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions for this endpoint"
                )

    async def _check_rate_limits(self, request: Request, routing_context: HTTPRoutingContext):
        """Check and enforce rate limits."""
        client_ip = self._get_client_ip(request)
        path = str(request.url.path)
        
        # Determine rate limit key
        if routing_context.user_id:
            rate_limit_key = f"user:{routing_context.user_id}"
        else:
            rate_limit_key = f"ip:{client_ip}"
        
        # Find applicable rate limit
        rate_limit = self.default_rate_limit
        for pattern, config in self.rate_limit_config.items():
            if self._path_matches_pattern(path, pattern):
                rate_limit = config["requests_per_minute"]
                break
        
        # Check rate limit
        now = datetime.now(timezone.utc)
        bucket = self.rate_limit_buckets[rate_limit_key]
        
        # Remove old entries (older than 1 minute)
        while bucket and bucket[0] < now - timedelta(minutes=1):
            bucket.popleft()
        
        # Check if rate limit exceeded
        if len(bucket) >= rate_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {rate_limit} requests per minute"
            )
        
        # Add current request to bucket
        bucket.append(now)

    async def _post_process_response(
        self,
        request: Request,
        response: Response,
        routing_context: HTTPRoutingContext
    ) -> Response:
        """Post-process response with security headers and modifications."""
        if self.security_headers:
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Add correlation ID if present
            if routing_context.correlation_id:
                response.headers["X-Correlation-ID"] = routing_context.correlation_id
            
            # Add request ID
            response.headers["X-Request-ID"] = routing_context.request_id
        
        return response

    async def _log_access_attempt(
        self,
        request: Request,
        routing_context: Optional[HTTPRoutingContext],
        decision: Optional[RoutingDecision],
        success: bool,
        error_message: Optional[str]
    ):
        """Log access attempt for audit purposes."""
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": routing_context.request_id if routing_context else "unknown",
            "method": request.method,
            "path": str(request.url.path),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "user_id": routing_context.user_id if routing_context else None,
            "organization_id": routing_context.organization_id if routing_context else None,
            "platform_role": routing_context.platform_role.value if routing_context and routing_context.platform_role else None,
            "service_role": routing_context.service_role.value if routing_context and routing_context.service_role else None,
            "success": success,
            "target_router": decision.target_router if decision else None,
            "processing_time_ms": decision.processing_time_ms if decision else 0,
            "error_message": error_message
        }
        
        if success:
            self.logger.info(f"API Access: {log_entry}")
        else:
            self.logger.warning(f"API Access Denied: {log_entry}")

    def _initialize_default_rules(self):
        """Initialize default endpoint protection rules."""
        # Admin endpoints - highest security
        admin_rule = APIEndpointRule(
            name="Admin Endpoints",
            path_pattern="/api/v*/admin/**",
            methods=[HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT, HTTPMethod.DELETE],
            route_type=RouteType.ADMIN,
            allowed_platform_roles=[PlatformRole.PLATFORM_ADMIN],
            required_permissions=["admin:full"],
            require_authentication=True,
            require_organization_context=False,
            rate_limit_per_minute=20,
            enable_detailed_logging=True
        )
        
        # SI endpoints
        si_rule = APIEndpointRule(
            name="SI Endpoints",
            path_pattern="/api/v*/si/**",
            methods=[HTTPMethod.GET, HTTPMethod.POST, HTTPMethod.PUT],
            route_type=RouteType.SI_ONLY,
            allowed_platform_roles=[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID],
            required_permissions=["si:access"],
            require_authentication=True,
            require_organization_context=True,
            rate_limit_per_minute=60,
            forward_to_message_router=True
        )
        
        # APP endpoints
        app_rule = APIEndpointRule(
            name="APP Endpoints",
            path_pattern="/api/v*/app/**",
            methods=[HTTPMethod.GET, HTTPMethod.POST],
            route_type=RouteType.APP_ONLY,
            allowed_platform_roles=[PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID],
            required_permissions=["app:access"],
            require_authentication=True,
            require_organization_context=True,
            rate_limit_per_minute=100,
            forward_to_message_router=True
        )
        
        # Add rules asynchronously
        asyncio.create_task(self.add_endpoint_rule(admin_rule))
        asyncio.create_task(self.add_endpoint_rule(si_rule))
        asyncio.create_task(self.add_endpoint_rule(app_rule))

    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern (supports wildcards)."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def _determine_target_router(self, rule: APIEndpointRule) -> str:
        """Determine target router based on rule."""
        if rule.route_type == RouteType.SI_ONLY:
            return "si"
        elif rule.route_type == RouteType.APP_ONLY:
            return "app"
        elif rule.route_type == RouteType.HYBRID:
            return "hybrid"
        elif rule.route_type == RouteType.ADMIN:
            return "hybrid"  # Admin goes through hybrid for access control
        else:
            return "hybrid"  # Default

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

    async def get_access_stats(self) -> Dict[str, Any]:
        """Get access statistics for monitoring."""
        return {
            "access_stats": self.access_stats.copy(),
            "protected_endpoints": len(self.protected_endpoints),
            "endpoint_rules": len(self.endpoint_rules),
            "route_permissions": len(self.route_permissions),
            "rate_limit_buckets": len(self.rate_limit_buckets),
            "ip_whitelist_size": len(self.ip_whitelist),
            "ip_blacklist_size": len(self.ip_blacklist)
        }

    def add_ip_to_whitelist(self, ip: str):
        """Add IP address to whitelist."""
        self.ip_whitelist.add(ip)
        self.logger.info(f"Added IP to whitelist: {ip}")

    def add_ip_to_blacklist(self, ip: str):
        """Add IP address to blacklist."""
        self.ip_blacklist.add(ip)
        self.logger.info(f"Added IP to blacklist: {ip}")

    def block_user_agent(self, user_agent_pattern: str):
        """Block requests from specific user agent patterns."""
        self.blocked_user_agents.append(user_agent_pattern)
        self.logger.info(f"Blocked user agent pattern: {user_agent_pattern}")