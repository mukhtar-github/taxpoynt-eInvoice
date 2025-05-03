"""Rate limiting middleware for API security."""
import time
from typing import Dict, Tuple, Optional, Callable, Any
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.db.redis import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to protect against abuse.
    Uses Redis to track request counts across instances.
    """
    
    def __init__(
        self, 
        app: ASGIApp, 
        default_limits: Dict[str, Tuple[int, int]] = None,
        path_limits: Dict[str, Tuple[int, int]] = None,
        identify_user_func: Optional[Callable[[Request], Any]] = None
    ):
        """
        Initialize the rate limit middleware.
        
        Args:
            app: The ASGI application
            default_limits: Default rate limits (requests, seconds) for all endpoints
            path_limits: Path-specific rate limits mapping endpoint paths to (requests, seconds)
            identify_user_func: Function to extract user identifier from request
        """
        super().__init__(app)
        self.redis = get_redis_client()
        self.default_limits = default_limits or {
            "ip": (60, 60),     # 60 requests per minute per IP
            "user": (120, 60),  # 120 requests per minute per user
        }
        self.path_limits = path_limits or {
            # Auth endpoints
            "^/api/v1/auth/login": (10, 60),          # 10 requests per minute
            "^/api/v1/auth/register": (5, 60),        # 5 requests per minute
            "^/api/v1/auth/password-reset": (5, 60),  # 5 requests per minute
            
            # High-volume endpoints
            "^/api/v1/irn/generate-batch": (10, 60),  # 10 requests per minute
            
            # API key management
            "^/api/v1/api-keys": (20, 60),            # 20 requests per minute
        }
        self.identify_user_func = identify_user_func
        
    async def dispatch(self, request: Request, call_next):
        """
        Process request through rate limiter.
        
        Args:
            request: The incoming request
            call_next: Function to call next middleware
        
        Returns:
            Response object
        """
        # Skip OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Get client IP address
        client_ip = self._get_client_ip(request)
        
        # Get user identifier if available
        user_id = None
        if self.identify_user_func:
            try:
                user_id = await self.identify_user_func(request)
            except:
                # If user identification fails, just rate limit by IP
                pass
                
        # Get path-specific limits
        path = request.url.path
        limits = self._get_limits_for_path(path)
        
        # Check rate limits
        if not await self._check_rate_limit(client_ip, user_id, path, limits):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )
            
        # Process request
        response = await call_next(request)
        
        # Include rate limit headers
        if isinstance(response, Response):
            ip_remaining, ip_reset = await self._get_limit_info(client_ip, path, limits["ip"])
            response.headers["X-RateLimit-Limit-IP"] = str(limits["ip"][0])
            response.headers["X-RateLimit-Remaining-IP"] = str(ip_remaining)
            response.headers["X-RateLimit-Reset-IP"] = str(ip_reset)
            
            if user_id:
                user_remaining, user_reset = await self._get_limit_info(user_id, path, limits["user"])
                response.headers["X-RateLimit-Limit-User"] = str(limits["user"][0])
                response.headers["X-RateLimit-Remaining-User"] = str(user_remaining)
                response.headers["X-RateLimit-Reset-User"] = str(user_reset)
                
        return response
        
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Try to get IP from X-Forwarded-For header (common in production with proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, use the first one (client IP)
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            # Fallback to client host
            client_ip = request.client.host if request.client else "unknown"
            
        return client_ip
        
    def _get_limits_for_path(self, path: str) -> Dict[str, Tuple[int, int]]:
        """Get rate limits for a specific path."""
        import re
        
        # Start with default limits
        limits = self.default_limits.copy()
        
        # Check if path matches any specific limits
        for path_pattern, path_limit in self.path_limits.items():
            if re.match(path_pattern, path):
                # Use smaller of IP limits (more restrictive)
                current_ip_limit = limits.get("ip", (float("inf"), 60))
                if path_limit[0] < current_ip_limit[0]:
                    limits["ip"] = path_limit
                    
                # Use smaller of user limits (more restrictive)
                current_user_limit = limits.get("user", (float("inf"), 60))
                if path_limit[0] < current_user_limit[0]:
                    limits["user"] = path_limit
                    
                break
                
        return limits
        
    async def _check_rate_limit(
        self, 
        client_ip: str, 
        user_id: Optional[str], 
        path: str, 
        limits: Dict[str, Tuple[int, int]]
    ) -> bool:
        """
        Check if request exceeds rate limits.
        
        Args:
            client_ip: Client IP address
            user_id: User identifier (if authenticated)
            path: Request path
            limits: Rate limits to apply
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # Always check IP-based rate limit
        ip_key = f"ratelimit:ip:{client_ip}:{path}"
        ip_limit, ip_window = limits.get("ip", (float("inf"), 60))
        
        if not await self._increment_counter(ip_key, ip_limit, ip_window):
            return False
            
        # Check user-based rate limit if user is authenticated
        if user_id:
            user_key = f"ratelimit:user:{user_id}:{path}"
            user_limit, user_window = limits.get("user", (float("inf"), 60))
            
            if not await self._increment_counter(user_key, user_limit, user_window):
                return False
                
        return True
        
    async def _increment_counter(self, key: str, limit: int, window: int) -> bool:
        """
        Increment rate limit counter and check if limit is exceeded.
        
        Args:
            key: Redis key for counter
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        # Get current count
        current = self.redis.get(key)
        current_count = int(current) if current else 0
        
        # Check if limit exceeded
        if current_count >= limit:
            return False
            
        # Use pipelining for atomic operations
        pipe = self.redis.pipeline()
        
        # Increment counter
        pipe.incr(key)
        
        # Set expiration if counter is new
        if current_count == 0:
            pipe.expire(key, window)
            
        # Execute pipeline
        pipe.execute()
        
        return True
        
    async def _get_limit_info(self, identifier: str, path: str, limit_config: Tuple[int, int]) -> Tuple[int, int]:
        """
        Get remaining requests and reset time for rate limit.
        
        Args:
            identifier: IP or user identifier
            path: Request path
            limit_config: Rate limit configuration (max_requests, window)
            
        Returns:
            Tuple of (remaining_requests, seconds_until_reset)
        """
        # Get appropriate key
        if len(identifier) > 20:  # Assume user ID if long string
            key = f"ratelimit:user:{identifier}:{path}"
        else:  # Otherwise assume IP
            key = f"ratelimit:ip:{identifier}:{path}"
            
        # Get current count and TTL
        current = self.redis.get(key)
        current_count = int(current) if current else 0
        ttl = self.redis.ttl(key)
        
        # Calculate remaining requests and reset time
        max_requests, _ = limit_config
        remaining = max(0, max_requests - current_count)
        reset_time = max(0, ttl) if ttl > 0 else 0
        
        return remaining, reset_time 