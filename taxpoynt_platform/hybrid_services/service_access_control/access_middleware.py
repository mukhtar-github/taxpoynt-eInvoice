"""
Access Middleware - Runtime access control and request validation

This module provides comprehensive access control middleware that integrates with
existing backend middleware and platform services to provide unified request validation,
authentication, authorization, and audit logging.

Integrates with:
- Backend middleware (rate_limit.py, api_key_auth.py, security.py)
- Platform tier_manager.py for subscription-based access
- Platform access_controller.py for advanced security
"""

import asyncio
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Import existing platform services
from ...billing_orchestration.tier_manager import TierManager, AccessDecision
from ...billing_orchestration.usage_tracker import UsageTracker
from ....app_services.security_compliance.access_controller import AccessController
from ....core_platform.monitoring import MetricsCollector
from ....core_platform.data_management.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class AccessLevel(str, Enum):
    """Access levels for request validation"""
    PUBLIC = "public"              # No authentication required
    AUTHENTICATED = "authenticated" # Valid authentication required
    AUTHORIZED = "authorized"      # Specific permissions required
    ELEVATED = "elevated"          # Enhanced verification required
    ADMIN = "admin"               # Administrative access required


class AccessRequestType(str, Enum):
    """Types of access requests"""
    API_CALL = "api_call"
    FEATURE_ACCESS = "feature_access"
    RESOURCE_ACCESS = "resource_access"
    ADMIN_ACTION = "admin_action"
    INTEGRATION_CALL = "integration_call"


@dataclass
class AccessContext:
    """Context information for access control decisions"""
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    api_key_id: Optional[str] = None
    client_ip: str = "unknown"
    user_agent: str = "unknown"
    request_path: str = ""
    request_method: str = ""
    timestamp: datetime = None
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class AccessRequest:
    """Represents an access control request"""
    request_id: str
    access_type: AccessRequestType
    access_level: AccessLevel
    resource: str
    context: AccessContext
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AccessResponse:
    """Response from access control evaluation"""
    request_id: str
    decision: AccessDecision
    allowed: bool
    reason: str
    metadata: Dict[str, Any] = None
    rate_limit_info: Optional[Dict[str, Any]] = None
    quota_info: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class AccessMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive access control middleware that integrates with existing
    platform services to provide unified access control and validation.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        tier_manager: TierManager,
        usage_tracker: UsageTracker,
        access_controller: AccessController,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(app)
        self.tier_manager = tier_manager
        self.usage_tracker = usage_tracker
        self.access_controller = access_controller
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.config = config or {}
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes
        self.enable_audit_logging = self.config.get("enable_audit_logging", True)
        self.bypass_paths = self.config.get("bypass_paths", [
            "/health", "/metrics", "/docs", "/openapi.json"
        ])
        
        # Path configurations
        self.path_configs = self.config.get("path_configs", {
            "/api/v1/auth/*": {
                "access_level": AccessLevel.PUBLIC,
                "rate_limit_override": True
            },
            "/api/v1/admin/*": {
                "access_level": AccessLevel.ADMIN,
                "require_mfa": True
            },
            "/api/v1/firs/*": {
                "access_level": AccessLevel.AUTHORIZED,
                "require_subscription": True
            },
            "/api/v1/integrations/*": {
                "access_level": AccessLevel.AUTHORIZED,
                "check_tier_limits": True
            }
        })
    
    async def dispatch(self, request: Request, call_next):
        """Process the request through access control layers"""
        start_time = time.time()
        request_id = str(uuid4())
        
        try:
            # Check if path should bypass access control
            if self._should_bypass(request.url.path):
                response = await call_next(request)
                await self._record_metrics(request_id, "bypassed", time.time() - start_time)
                return response
            
            # Build access context
            context = await self._build_access_context(request)
            
            # Determine access requirements
            access_level, resource = self._determine_access_requirements(request)
            
            # Create access request
            access_request = AccessRequest(
                request_id=request_id,
                access_type=AccessRequestType.API_CALL,
                access_level=access_level,
                resource=resource,
                context=context
            )
            
            # Evaluate access
            access_response = await self._evaluate_access(access_request)
            
            if not access_response.allowed:
                await self._record_metrics(request_id, "denied", time.time() - start_time)
                return await self._create_access_denied_response(access_response)
            
            # Add context to request
            request.state.access_context = context
            request.state.access_response = access_response
            
            # Process the request
            response = await call_next(request)
            
            # Record successful access
            await self._record_successful_access(access_request, response)
            await self._record_metrics(request_id, "allowed", time.time() - start_time)
            
            # Add access headers to response
            self._add_access_headers(response, access_response)
            
            return response
            
        except Exception as e:
            logger.error(f"Access middleware error for request {request_id}: {e}")
            await self._record_metrics(request_id, "error", time.time() - start_time)
            
            # In case of middleware error, allow request but log the issue
            if self.config.get("fail_open", True):
                return await call_next(request)
            else:
                return await self._create_error_response(str(e))
    
    def _should_bypass(self, path: str) -> bool:
        """Check if the path should bypass access control"""
        for bypass_path in self.bypass_paths:
            if bypass_path.endswith('*'):
                if path.startswith(bypass_path[:-1]):
                    return True
            elif path == bypass_path:
                return True
        return False
    
    async def _build_access_context(self, request: Request) -> AccessContext:
        """Build access context from request"""
        # Extract basic context
        context = AccessContext(
            client_ip=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            request_path=request.url.path,
            request_method=request.method
        )
        
        # Extract authentication information (integrate with existing auth)
        auth_header = request.headers.get("authorization")
        if auth_header:
            # This would integrate with existing JWT/API key auth
            context.user_id = await self._extract_user_id(auth_header)
            context.organization_id = await self._extract_organization_id(auth_header)
            context.api_key_id = await self._extract_api_key_id(auth_header)
        
        # Extract session information
        session_cookie = request.cookies.get("session_id")
        if session_cookie:
            context.session_id = session_cookie
        
        # Get subscription tier if organization is identified
        if context.organization_id:
            try:
                subscription = await self.tier_manager.get_organization_subscription(
                    context.organization_id
                )
                context.subscription_tier = subscription.tier.value if subscription else "FREE"
            except Exception as e:
                logger.warning(f"Failed to get subscription tier: {e}")
                context.subscription_tier = "FREE"
        
        return context
    
    def _determine_access_requirements(self, request: Request) -> tuple[AccessLevel, str]:
        """Determine the access level and resource for the request"""
        path = request.url.path
        
        # Check path-specific configurations
        for path_pattern, config in self.path_configs.items():
            if self._match_path_pattern(path, path_pattern):
                return config.get("access_level", AccessLevel.AUTHENTICATED), path
        
        # Default access requirements based on path patterns
        if path.startswith("/api/v1/admin"):
            return AccessLevel.ADMIN, path
        elif path.startswith("/api/v1/auth"):
            return AccessLevel.PUBLIC, path
        elif path.startswith("/api/v1"):
            return AccessLevel.AUTHENTICATED, path
        else:
            return AccessLevel.PUBLIC, path
    
    def _match_path_pattern(self, path: str, pattern: str) -> bool:
        """Match path against pattern (supports wildcards)"""
        if pattern.endswith('*'):
            return path.startswith(pattern[:-1])
        return path == pattern
    
    async def _evaluate_access(self, access_request: AccessRequest) -> AccessResponse:
        """Evaluate access request through multiple layers"""
        request_id = access_request.request_id
        context = access_request.context
        
        # Check cache first
        cache_key = f"access:{context.user_id}:{context.organization_id}:{access_request.resource}"
        cached_response = await self.cache_manager.get(cache_key)
        if cached_response and not self._is_cached_response_expired(cached_response):
            return AccessResponse(**cached_response)
        
        # Layer 1: Basic authentication check
        if access_request.access_level != AccessLevel.PUBLIC:
            if not context.user_id:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.DENIED,
                    allowed=False,
                    reason="Authentication required"
                )
        
        # Layer 2: Subscription tier validation
        if context.organization_id and context.subscription_tier:
            tier_check = await self.tier_manager.check_feature_access(
                organization_id=context.organization_id,
                feature=access_request.resource,
                tier=context.subscription_tier
            )
            
            if tier_check.decision != AccessDecision.GRANTED:
                return AccessResponse(
                    request_id=request_id,
                    decision=tier_check.decision,
                    allowed=False,
                    reason=f"Subscription tier access: {tier_check.decision}",
                    metadata={"tier_info": asdict(tier_check)}
                )
        
        # Layer 3: Usage quota check
        if context.organization_id:
            usage_check = await self.usage_tracker.check_usage_limits(
                organization_id=context.organization_id,
                action=access_request.access_type.value
            )
            
            if not usage_check.allowed:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.USAGE_LIMITED,
                    allowed=False,
                    reason="Usage quota exceeded",
                    quota_info=asdict(usage_check)
                )
        
        # Layer 4: Advanced security checks (anomaly detection, etc.)
        if context.user_id:
            security_check = await self.access_controller.validate_access(
                user_id=context.user_id,
                resource=access_request.resource,
                ip_address=context.client_ip,
                session_id=context.session_id
            )
            
            if not security_check.allowed:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.DENIED,
                    allowed=False,
                    reason=f"Security validation failed: {security_check.reason}"
                )
        
        # All checks passed
        response = AccessResponse(
            request_id=request_id,
            decision=AccessDecision.GRANTED,
            allowed=True,
            reason="Access granted",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl)
        )
        
        # Cache the response
        await self.cache_manager.set(
            cache_key, 
            asdict(response), 
            ttl=self.cache_ttl
        )
        
        return response
    
    async def _extract_user_id(self, auth_header: str) -> Optional[str]:
        """Extract user ID from authentication header"""
        # This would integrate with existing JWT/API key authentication
        # For now, return None as placeholder
        return None
    
    async def _extract_organization_id(self, auth_header: str) -> Optional[str]:
        """Extract organization ID from authentication header"""
        # This would integrate with existing JWT/API key authentication
        # For now, return None as placeholder
        return None
    
    async def _extract_api_key_id(self, auth_header: str) -> Optional[str]:
        """Extract API key ID from authentication header"""
        # This would integrate with existing API key authentication
        # For now, return None as placeholder
        return None
    
    def _is_cached_response_expired(self, cached_response: Dict[str, Any]) -> bool:
        """Check if cached response has expired"""
        expires_at = cached_response.get("expires_at")
        if not expires_at:
            return True
        
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        return datetime.now(timezone.utc) > expires_at
    
    async def _create_access_denied_response(self, access_response: AccessResponse) -> Response:
        """Create HTTP response for access denied"""
        status_code = status.HTTP_403_FORBIDDEN
        
        if access_response.decision == AccessDecision.DENIED:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif access_response.decision == AccessDecision.USAGE_LIMITED:
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif access_response.decision == AccessDecision.UPGRADE_REQUIRED:
            status_code = status.HTTP_402_PAYMENT_REQUIRED
        
        return Response(
            content={
                "error": "Access denied",
                "reason": access_response.reason,
                "decision": access_response.decision,
                "request_id": access_response.request_id
            },
            status_code=status_code,
            media_type="application/json"
        )
    
    async def _create_error_response(self, error_message: str) -> Response:
        """Create HTTP response for middleware errors"""
        return Response(
            content={
                "error": "Access control error",
                "message": error_message
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            media_type="application/json"
        )
    
    def _add_access_headers(self, response: Response, access_response: AccessResponse):
        """Add access control headers to response"""
        response.headers["X-Access-Decision"] = access_response.decision
        response.headers["X-Request-ID"] = access_response.request_id
        
        if access_response.quota_info:
            response.headers["X-Quota-Remaining"] = str(
                access_response.quota_info.get("remaining", "unknown")
            )
        
        if access_response.rate_limit_info:
            response.headers["X-RateLimit-Remaining"] = str(
                access_response.rate_limit_info.get("remaining", "unknown")
            )
    
    async def _record_successful_access(
        self, 
        access_request: AccessRequest, 
        response: Response
    ):
        """Record successful access for audit and analytics"""
        if not self.enable_audit_logging:
            return
        
        # Track usage if organization is identified
        if access_request.context.organization_id:
            await self.usage_tracker.record_usage(
                organization_id=access_request.context.organization_id,
                action=access_request.access_type.value,
                resource=access_request.resource,
                metadata={
                    "response_status": response.status_code,
                    "user_id": access_request.context.user_id,
                    "request_id": access_request.request_id
                }
            )
    
    async def _record_metrics(self, request_id: str, outcome: str, duration: float):
        """Record access control metrics"""
        await self.metrics_collector.record_counter(
            "access_middleware_requests",
            tags={"outcome": outcome}
        )
        
        await self.metrics_collector.record_histogram(
            "access_middleware_duration",
            duration,
            tags={"outcome": outcome}
        )


# Utility functions for integration

async def create_access_middleware(
    app: ASGIApp,
    config: Optional[Dict[str, Any]] = None
) -> AccessMiddleware:
    """
    Factory function to create access middleware with proper dependencies
    """
    # Initialize dependencies (these would come from dependency injection in real app)
    tier_manager = TierManager()
    usage_tracker = UsageTracker()
    access_controller = AccessController()
    metrics_collector = MetricsCollector()
    cache_manager = CacheManager()
    
    return AccessMiddleware(
        app=app,
        tier_manager=tier_manager,
        usage_tracker=usage_tracker,
        access_controller=access_controller,
        metrics_collector=metrics_collector,
        cache_manager=cache_manager,
        config=config
    )


def require_access_level(level: AccessLevel):
    """
    Decorator to enforce specific access levels on FastAPI endpoints
    """
    def decorator(func):
        func._required_access_level = level
        return func
    return decorator


def require_subscription_tier(tier: str):
    """
    Decorator to enforce minimum subscription tier on FastAPI endpoints
    """
    def decorator(func):
        func._required_tier = tier
        return func
    return decorator