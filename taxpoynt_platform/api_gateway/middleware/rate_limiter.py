"""
Role-Based Rate Limiter Middleware
==================================
FastAPI middleware for role-based rate limiting with advanced algorithms.
Provides flexible rate limiting strategies based on user roles, endpoints, and usage patterns.
"""
import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple, NamedTuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from ...core_platform.authentication.role_manager import PlatformRole
from ..role_routing.models import HTTPRoutingContext, HTTPMethod

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms."""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW_LOG = "sliding_window_log"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    rule_id: str
    name: str
    path_pattern: str
    methods: Optional[List[HTTPMethod]] = None
    platform_roles: Optional[List[PlatformRole]] = None
    
    # Rate limit configuration
    requests_per_minute: int = 60
    requests_per_hour: int = 3600
    requests_per_day: int = 86400
    burst_limit: Optional[int] = None
    
    # Algorithm and behavior
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    grace_period_seconds: int = 0
    
    # Advanced features
    adaptive_limiting: bool = False
    priority_boost: bool = False
    
    # Limits by scope
    per_user_limit: Optional[int] = None
    per_ip_limit: Optional[int] = None
    per_organization_limit: Optional[int] = None
    global_limit: Optional[int] = None


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from bucket."""
        now = time.time()
        
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now
        
        # Check if we have enough tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        
        return False
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """Get wait time until tokens are available."""
        if self.tokens >= tokens:
            return 0.0
        
        needed_tokens = tokens - self.tokens
        return needed_tokens / self.refill_rate


class SlidingWindow:
    """Sliding window rate limiter implementation."""
    
    def __init__(self, window_size: int, limit: int):
        self.window_size = window_size  # seconds
        self.limit = limit
        self.requests = deque()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window_size:
            self.requests.popleft()
        
        # Check if under limit
        if len(self.requests) < self.limit:
            self.requests.append(now)
            return True
        
        return False
    
    def get_wait_time(self) -> float:
        """Get wait time until next request is allowed."""
        if len(self.requests) < self.limit:
            return 0.0
        
        oldest_request = self.requests[0]
        return (oldest_request + self.window_size) - time.time()


class RateLimitStatus(NamedTuple):
    """Rate limit status information."""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[float] = None


class RoleBasedRateLimiter(BaseHTTPMiddleware):
    """
    Role-Based Rate Limiter Middleware
    ==================================
    
    **Rate Limiting Strategies:**
    - **Role-Based Limits**: Different limits per platform role
    - **Endpoint-Specific**: Custom limits for specific API endpoints
    - **Multi-Dimensional**: Per-user, per-IP, per-organization limits
    - **Adaptive Limiting**: Dynamic adjustment based on system load
    - **Priority Handling**: Priority users get higher limits
    
    **Algorithms Supported:**
    - **Token Bucket**: Smooth rate limiting with burst capacity
    - **Sliding Window**: Rolling time window for consistent rates
    - **Fixed Window**: Simple time-based windows
    - **Sliding Window Log**: Precise per-request tracking
    
    **Role-Specific Limits:**
    - **SI**: High limits for integration operations
    - **APP**: Medium limits for FIRS operations  
    - **Hybrid**: Combined limits with priority
    - **Admin**: Lower limits but with override capability
    """
    
    def __init__(
        self,
        app,
        enable_rate_limiting: bool = True,
        default_algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        enable_adaptive_limiting: bool = False,
        enable_priority_handling: bool = True,
        redis_client: Optional[Any] = None,  # For distributed rate limiting
        excluded_paths: Optional[List[str]] = None
    ):
        super().__init__(app)
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.enable_rate_limiting = enable_rate_limiting
        self.default_algorithm = default_algorithm
        self.enable_adaptive_limiting = enable_adaptive_limiting
        self.enable_priority_handling = enable_priority_handling
        self.redis_client = redis_client  # For distributed rate limiting
        
        # Excluded paths
        self.excluded_paths = excluded_paths or [
            "/health", "/docs", "/redoc", "/openapi.json"
        ]
        
        # Rate limit rules
        self.rate_limit_rules: Dict[str, RateLimitRule] = {}
        
        # Rate limiter instances
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.sliding_windows: Dict[str, SlidingWindow] = {}
        self.fixed_windows: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Default limits by role
        self.default_role_limits = {
            PlatformRole.SYSTEM_INTEGRATOR: {
                "requests_per_minute": 120,
                "requests_per_hour": 7200,
                "burst_limit": 150
            },
            PlatformRole.ACCESS_POINT_PROVIDER: {
                "requests_per_minute": 100,
                "requests_per_hour": 6000,
                "burst_limit": 120
            },
            PlatformRole.HYBRID: {
                "requests_per_minute": 200,
                "requests_per_hour": 12000,
                "burst_limit": 250
            },
            PlatformRole.PLATFORM_ADMIN: {
                "requests_per_minute": 60,
                "requests_per_hour": 3600,
                "burst_limit": 100
            },
            PlatformRole.USER: {
                "requests_per_minute": 30,
                "requests_per_hour": 1800,
                "burst_limit": 50
            }
        }
        
        # Adaptive limiting
        self.system_load_factor = 1.0
        self.adaptive_adjustment_interval = 60  # seconds
        self.last_adaptive_check = time.time()
        
        # Priority users
        self.priority_users: Set[str] = set()
        self.priority_multiplier = 2.0
        
        # Metrics
        self.rate_limit_metrics = {
            "total_requests": 0,
            "allowed_requests": 0,
            "limited_requests": 0,
            "limits_by_role": defaultdict(int),
            "limits_by_endpoint": defaultdict(int),
            "algorithm_usage": defaultdict(int)
        }
        
        # Background cleanup task
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Initialize default rules
        self._initialize_default_rules()
        
        # Start background tasks
        asyncio.create_task(self._start_background_tasks())
        
        logger.info("RoleBasedRateLimiter middleware initialized")
    
    async def dispatch(self, request: Request, call_next):
        """Main middleware dispatch method."""
        try:
            # Skip rate limiting for excluded paths
            if not self.enable_rate_limiting or self._is_excluded_path(request.url.path):
                return await call_next(request)
            
            self.rate_limit_metrics["total_requests"] += 1
            
            # Get routing context from previous middleware
            routing_context = getattr(request.state, "routing_context", None)
            
            # Apply rate limiting
            rate_limit_status = await self._check_rate_limits(request, routing_context)
            
            if not rate_limit_status.allowed:
                self.rate_limit_metrics["limited_requests"] += 1
                
                # Track limits by role and endpoint
                if routing_context and routing_context.platform_role:
                    self.rate_limit_metrics["limits_by_role"][routing_context.platform_role.value] += 1
                self.rate_limit_metrics["limits_by_endpoint"][request.url.path] += 1
                
                # Return rate limit exceeded response
                headers = {
                    "X-RateLimit-Remaining": str(rate_limit_status.remaining),
                    "X-RateLimit-Reset": str(int(rate_limit_status.reset_time))
                }
                
                if rate_limit_status.retry_after:
                    headers["Retry-After"] = str(int(rate_limit_status.retry_after))
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers=headers
                )
            
            # Add rate limit headers
            response = await call_next(request)
            
            # Add rate limit info to response headers
            response.headers["X-RateLimit-Remaining"] = str(rate_limit_status.remaining)
            response.headers["X-RateLimit-Reset"] = str(int(rate_limit_status.reset_time))
            
            self.rate_limit_metrics["allowed_requests"] += 1
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Rate limiting error: {str(e)}")
            # Continue without rate limiting on error
            return await call_next(request)
    
    async def _check_rate_limits(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> RateLimitStatus:
        """Check rate limits for the request."""
        
        # Find applicable rate limit rules
        applicable_rules = self._find_applicable_rules(request, routing_context)
        
        # If no specific rules, use default role-based limits
        if not applicable_rules:
            return await self._check_default_rate_limits(request, routing_context)
        
        # Check each applicable rule
        for rule in applicable_rules:
            status = await self._check_rule_rate_limit(request, routing_context, rule)
            if not status.allowed:
                return status
        
        # All rules passed
        return RateLimitStatus(
            allowed=True,
            remaining=100,  # Default remaining
            reset_time=time.time() + 60
        )
    
    async def _check_default_rate_limits(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> RateLimitStatus:
        """Check default role-based rate limits."""
        
        # Determine role limits
        role = routing_context.platform_role if routing_context else PlatformRole.USER
        role_limits = self.default_role_limits.get(role, self.default_role_limits[PlatformRole.USER])
        
        # Apply adaptive limiting
        if self.enable_adaptive_limiting:
            await self._update_adaptive_limits()
            role_limits = self._apply_adaptive_adjustment(role_limits)
        
        # Apply priority boost
        if (self.enable_priority_handling and routing_context and 
            routing_context.user_id in self.priority_users):
            role_limits = self._apply_priority_boost(role_limits)
        
        # Create rate limit key
        rate_limit_key = self._create_rate_limit_key(request, routing_context, "default")
        
        # Check per-minute limit using sliding window
        return await self._check_sliding_window_limit(
            rate_limit_key + ":minute",
            role_limits["requests_per_minute"],
            60  # 1 minute window
        )
    
    async def _check_rule_rate_limit(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext],
        rule: RateLimitRule
    ) -> RateLimitStatus:
        """Check rate limit for a specific rule."""
        
        self.rate_limit_metrics["algorithm_usage"][rule.algorithm.value] += 1
        
        # Create base key for this rule
        base_key = self._create_rate_limit_key(request, routing_context, rule.rule_id)
        
        # Check different limit scopes
        if rule.per_user_limit and routing_context and routing_context.user_id:
            user_key = f"{base_key}:user:{routing_context.user_id}"
            status = await self._apply_algorithm_check(
                user_key, rule.per_user_limit, 60, rule.algorithm
            )
            if not status.allowed:
                return status
        
        if rule.per_ip_limit:
            ip = self._get_client_ip(request)
            ip_key = f"{base_key}:ip:{ip}"
            status = await self._apply_algorithm_check(
                ip_key, rule.per_ip_limit, 60, rule.algorithm
            )
            if not status.allowed:
                return status
        
        if rule.per_organization_limit and routing_context and routing_context.organization_id:
            org_key = f"{base_key}:org:{routing_context.organization_id}"
            status = await self._apply_algorithm_check(
                org_key, rule.per_organization_limit, 60, rule.algorithm
            )
            if not status.allowed:
                return status
        
        if rule.global_limit:
            global_key = f"{base_key}:global"
            status = await self._apply_algorithm_check(
                global_key, rule.global_limit, 60, rule.algorithm
            )
            if not status.allowed:
                return status
        
        # Check main rule limit
        return await self._apply_algorithm_check(
            base_key, rule.requests_per_minute, 60, rule.algorithm
        )
    
    async def _apply_algorithm_check(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int,
        algorithm: RateLimitAlgorithm
    ) -> RateLimitStatus:
        """Apply specific rate limiting algorithm."""
        
        if algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._check_token_bucket_limit(key, limit, window_seconds)
        elif algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._check_sliding_window_limit(key, limit, window_seconds)
        elif algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._check_fixed_window_limit(key, limit, window_seconds)
        else:
            # Default to sliding window
            return await self._check_sliding_window_limit(key, limit, window_seconds)
    
    async def _check_token_bucket_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> RateLimitStatus:
        """Check rate limit using token bucket algorithm."""
        
        # Get or create token bucket
        if key not in self.token_buckets:
            refill_rate = limit / window_seconds  # tokens per second
            self.token_buckets[key] = TokenBucket(limit, refill_rate)
        
        bucket = self.token_buckets[key]
        
        if bucket.consume():
            return RateLimitStatus(
                allowed=True,
                remaining=int(bucket.tokens),
                reset_time=time.time() + window_seconds
            )
        else:
            wait_time = bucket.get_wait_time()
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=time.time() + wait_time,
                retry_after=wait_time
            )
    
    async def _check_sliding_window_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> RateLimitStatus:
        """Check rate limit using sliding window algorithm."""
        
        # Get or create sliding window
        if key not in self.sliding_windows:
            self.sliding_windows[key] = SlidingWindow(window_seconds, limit)
        
        window = self.sliding_windows[key]
        
        if window.is_allowed():
            remaining = limit - len(window.requests)
            return RateLimitStatus(
                allowed=True,
                remaining=remaining,
                reset_time=time.time() + window_seconds
            )
        else:
            wait_time = window.get_wait_time()
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=time.time() + wait_time,
                retry_after=wait_time
            )
    
    async def _check_fixed_window_limit(
        self, 
        key: str, 
        limit: int, 
        window_seconds: int
    ) -> RateLimitStatus:
        """Check rate limit using fixed window algorithm."""
        
        now = time.time()
        window_start = int(now // window_seconds) * window_seconds
        window_key = f"{key}:{window_start}"
        
        # Get or initialize window
        if window_key not in self.fixed_windows:
            self.fixed_windows[window_key] = {
                "count": 0,
                "start_time": window_start,
                "end_time": window_start + window_seconds
            }
        
        window_data = self.fixed_windows[window_key]
        
        if window_data["count"] < limit:
            window_data["count"] += 1
            remaining = limit - window_data["count"]
            return RateLimitStatus(
                allowed=True,
                remaining=remaining,
                reset_time=window_data["end_time"]
            )
        else:
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=window_data["end_time"],
                retry_after=window_data["end_time"] - now
            )
    
    def _find_applicable_rules(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext]
    ) -> List[RateLimitRule]:
        """Find rate limit rules applicable to the request."""
        applicable_rules = []
        path = str(request.url.path)
        method = HTTPMethod(request.method)
        
        for rule in self.rate_limit_rules.values():
            # Check path pattern
            if not self._path_matches_pattern(path, rule.path_pattern):
                continue
            
            # Check HTTP method
            if rule.methods and method not in rule.methods:
                continue
            
            # Check platform role
            if rule.platform_roles and routing_context:
                if routing_context.platform_role not in rule.platform_roles:
                    continue
            
            applicable_rules.append(rule)
        
        return applicable_rules
    
    def _create_rate_limit_key(
        self, 
        request: Request, 
        routing_context: Optional[HTTPRoutingContext],
        rule_id: str
    ) -> str:
        """Create rate limit key for request."""
        components = [rule_id]
        
        # Add user ID if available
        if routing_context and routing_context.user_id:
            components.append(f"user:{routing_context.user_id}")
        else:
            # Fall back to IP
            ip = self._get_client_ip(request)
            components.append(f"ip:{ip}")
        
        # Add organization context if available
        if routing_context and routing_context.organization_id:
            components.append(f"org:{routing_context.organization_id}")
        
        return ":".join(components)
    
    async def _update_adaptive_limits(self):
        """Update adaptive rate limiting based on system load."""
        now = time.time()
        if now - self.last_adaptive_check < self.adaptive_adjustment_interval:
            return
        
        self.last_adaptive_check = now
        
        # Simulate system load check (in production, this would check actual metrics)
        # For example: CPU usage, memory usage, response times, error rates
        simulated_load = 0.5  # 50% load
        
        if simulated_load > 0.8:
            self.system_load_factor = 0.5  # Reduce limits by 50%
        elif simulated_load > 0.6:
            self.system_load_factor = 0.75  # Reduce limits by 25%
        else:
            self.system_load_factor = 1.0  # Normal limits
        
        self.logger.debug(f"Adaptive rate limiting factor: {self.system_load_factor}")
    
    def _apply_adaptive_adjustment(self, limits: Dict[str, int]) -> Dict[str, int]:
        """Apply adaptive adjustment to rate limits."""
        return {
            key: int(value * self.system_load_factor)
            for key, value in limits.items()
        }
    
    def _apply_priority_boost(self, limits: Dict[str, int]) -> Dict[str, int]:
        """Apply priority boost to rate limits."""
        return {
            key: int(value * self.priority_multiplier)
            for key, value in limits.items()
        }
    
    def _initialize_default_rules(self):
        """Initialize default rate limiting rules."""
        
        # SI high-frequency endpoints
        si_integration_rule = RateLimitRule(
            rule_id="si_integration",
            name="SI Integration Endpoints",
            path_pattern="/api/v*/si/integration/**",
            methods=[HTTPMethod.POST, HTTPMethod.PUT],
            platform_roles=[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID],
            requests_per_minute=200,
            burst_limit=250,
            algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
            per_organization_limit=150
        )
        
        # APP FIRS submission endpoints
        app_firs_rule = RateLimitRule(
            rule_id="app_firs",
            name="APP FIRS Endpoints",
            path_pattern="/api/v*/app/firs/**",
            methods=[HTTPMethod.POST],
            platform_roles=[PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID],
            requests_per_minute=100,
            burst_limit=120,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
            per_organization_limit=80
        )
        
        # Admin endpoints - stricter limits
        admin_rule = RateLimitRule(
            rule_id="admin_endpoints",
            name="Admin Endpoints",
            path_pattern="/api/v*/admin/**",
            platform_roles=[PlatformRole.PLATFORM_ADMIN],
            requests_per_minute=30,
            requests_per_hour=1800,
            algorithm=RateLimitAlgorithm.FIXED_WINDOW,
            per_user_limit=30
        )
        
        # Store rules
        self.rate_limit_rules = {
            si_integration_rule.rule_id: si_integration_rule,
            app_firs_rule.rule_id: app_firs_rule,
            admin_rule.rule_id: admin_rule
        }
    
    async def _start_background_tasks(self):
        """Start background cleanup tasks."""
        
        async def cleanup_expired_entries():
            """Clean up expired rate limit entries."""
            while True:
                try:
                    await asyncio.sleep(300)  # Run every 5 minutes
                    await self._cleanup_expired_entries()
                except Exception as e:
                    self.logger.error(f"Error in cleanup task: {str(e)}")
        
        self.cleanup_task = asyncio.create_task(cleanup_expired_entries())
    
    async def _cleanup_expired_entries(self):
        """Clean up expired rate limiting entries."""
        now = time.time()
        
        # Clean up fixed windows
        expired_windows = []
        for window_key, window_data in self.fixed_windows.items():
            if window_data["end_time"] < now - 3600:  # Older than 1 hour
                expired_windows.append(window_key)
        
        for key in expired_windows:
            del self.fixed_windows[key]
        
        # Clean up sliding windows with no recent activity
        expired_sliding = []
        for key, window in self.sliding_windows.items():
            if not window.requests or window.requests[-1] < now - 3600:
                expired_sliding.append(key)
        
        for key in expired_sliding:
            del self.sliding_windows[key]
        
        if expired_windows or expired_sliding:
            self.logger.debug(f"Cleaned up {len(expired_windows)} fixed windows and {len(expired_sliding)} sliding windows")
    
    # Helper methods
    def _is_excluded_path(self, path: str) -> bool:
        """Check if path is excluded from rate limiting."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _path_matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches pattern."""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    # Public API methods
    async def add_rate_limit_rule(self, rule: RateLimitRule):
        """Add a new rate limit rule."""
        self.rate_limit_rules[rule.rule_id] = rule
        self.logger.info(f"Added rate limit rule: {rule.name}")
    
    async def add_priority_user(self, user_id: str):
        """Add user to priority list."""
        self.priority_users.add(user_id)
        self.logger.info(f"Added priority user: {user_id}")
    
    async def remove_priority_user(self, user_id: str):
        """Remove user from priority list."""
        self.priority_users.discard(user_id)
        self.logger.info(f"Removed priority user: {user_id}")
    
    async def get_rate_limit_status(self, user_id: str) -> Dict[str, Any]:
        """Get current rate limit status for a user."""
        user_keys = [key for key in self.token_buckets.keys() if f"user:{user_id}" in key]
        user_keys.extend([key for key in self.sliding_windows.keys() if f"user:{user_id}" in key])
        
        status = {
            "user_id": user_id,
            "is_priority": user_id in self.priority_users,
            "active_limits": len(user_keys),
            "limits": []
        }
        
        for key in user_keys:
            if key in self.token_buckets:
                bucket = self.token_buckets[key]
                status["limits"].append({
                    "key": key,
                    "type": "token_bucket",
                    "tokens_remaining": int(bucket.tokens),
                    "capacity": bucket.capacity
                })
            elif key in self.sliding_windows:
                window = self.sliding_windows[key]
                status["limits"].append({
                    "key": key,
                    "type": "sliding_window",
                    "requests_in_window": len(window.requests),
                    "limit": window.limit
                })
        
        return status
    
    async def get_rate_limit_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics."""
        return {
            "rate_limit_metrics": self.rate_limit_metrics.copy(),
            "active_rules": len(self.rate_limit_rules),
            "token_buckets": len(self.token_buckets),
            "sliding_windows": len(self.sliding_windows),
            "fixed_windows": len(self.fixed_windows),
            "priority_users": len(self.priority_users),
            "system_load_factor": self.system_load_factor,
            "adaptive_limiting_enabled": self.enable_adaptive_limiting
        }
    
    async def reset_user_limits(self, user_id: str):
        """Reset rate limits for a specific user."""
        user_keys = [key for key in list(self.token_buckets.keys()) if f"user:{user_id}" in key]
        user_keys.extend([key for key in list(self.sliding_windows.keys()) if f"user:{user_id}" in key])
        
        for key in user_keys:
            if key in self.token_buckets:
                del self.token_buckets[key]
            if key in self.sliding_windows:
                del self.sliding_windows[key]
        
        self.logger.info(f"Reset rate limits for user: {user_id}")
    
    async def shutdown(self):
        """Shutdown rate limiter and cleanup resources."""
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("RoleBasedRateLimiter shutdown complete")


def create_rate_limiter(**kwargs) -> RoleBasedRateLimiter:
    """Factory function to create RoleBasedRateLimiter middleware."""
    return RoleBasedRateLimiter(app=None, **kwargs)