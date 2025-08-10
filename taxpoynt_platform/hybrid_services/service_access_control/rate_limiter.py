"""
Service Rate Limiter - API rate limiting and throttling

This module provides comprehensive rate limiting capabilities that integrate with
existing backend rate limiting middleware while extending functionality for the
platform's service-oriented architecture with tier-based limits and intelligent
throttling strategies.

Integrates with:
- backend/app/middleware/rate_limit.py for basic middleware
- backend/app/utils/rate_limiter.py for token bucket algorithm
- billing_orchestration/tier_manager.py for tier-based rate limits
- Platform monitoring and metrics collection
"""

import asyncio
import logging
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import threading

# Import existing platform services
from ...billing_orchestration.tier_manager import TierManager
from ....core_platform.monitoring import MetricsCollector
from ....core_platform.data_management.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(str, Enum):
    """Scope of rate limiting"""
    GLOBAL = "global"
    IP_ADDRESS = "ip_address"
    USER = "user"
    ORGANIZATION = "organization"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    FEATURE = "feature"


class RateLimitDecision(str, Enum):
    """Rate limit decisions"""
    ALLOWED = "allowed"
    THROTTLED = "throttled"
    BLOCKED = "blocked"
    UPGRADE_SUGGESTED = "upgrade_suggested"


@dataclass
class RateLimitConfig:
    """Configuration for a rate limit"""
    limit_id: str
    name: str
    description: str
    scope: RateLimitScope
    algorithm: RateLimitAlgorithm
    requests_per_window: int
    window_seconds: int
    burst_capacity: Optional[int] = None
    tier_multipliers: Dict[str, float] = None
    path_patterns: List[str] = None
    exclude_paths: List[str] = None
    enable_throttling: bool = True
    throttle_threshold: float = 0.8  # Start throttling at 80% of limit
    block_threshold: float = 1.0     # Block at 100% of limit
    grace_period_seconds: int = 0
    enabled: bool = True
    
    def __post_init__(self):
        if self.tier_multipliers is None:
            self.tier_multipliers = {}
        if self.path_patterns is None:
            self.path_patterns = []
        if self.exclude_paths is None:
            self.exclude_paths = []
        if self.burst_capacity is None:
            self.burst_capacity = self.requests_per_window


@dataclass
class RateLimitState:
    """Current state of a rate limit"""
    limit_id: str
    scope_id: str
    requests_made: int
    requests_remaining: int
    window_start: datetime
    window_end: datetime
    last_request: datetime
    consecutive_blocks: int = 0
    total_requests: int = 0
    
    @property
    def usage_percentage(self) -> float:
        total_limit = self.requests_made + self.requests_remaining
        return (self.requests_made / total_limit * 100) if total_limit > 0 else 0


@dataclass
class RateLimitResult:
    """Result of rate limit evaluation"""
    limit_id: str
    scope_id: str
    decision: RateLimitDecision
    allowed: bool
    reason: str
    current_usage: int
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    throttle_delay: Optional[float] = None
    headers: Dict[str, str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.headers is None:
            self.headers = {}
        if self.metadata is None:
            self.metadata = {}


class TokenBucket:
    """
    Enhanced token bucket implementation with thread safety and persistence
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        initial_tokens: Optional[int] = None
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Attempt to consume tokens from the bucket"""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def peek(self) -> float:
        """Get current token count without consuming"""
        with self.lock:
            self._refill()
            return self.tokens
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        tokens_to_add = elapsed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize bucket state for persistence"""
        return {
            "capacity": self.capacity,
            "refill_rate": self.refill_rate,
            "tokens": self.tokens,
            "last_refill": self.last_refill
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenBucket":
        """Deserialize bucket state from persistence"""
        bucket = cls(
            capacity=data["capacity"],
            refill_rate=data["refill_rate"],
            initial_tokens=data["tokens"]
        )
        bucket.last_refill = data["last_refill"]
        return bucket


class SlidingWindowCounter:
    """
    Sliding window counter for rate limiting
    """
    
    def __init__(self, window_seconds: int, max_requests: int):
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.requests: List[float] = []
        self.lock = threading.RLock()
    
    def add_request(self) -> bool:
        """Add a request and check if within limit"""
        with self.lock:
            now = time.time()
            
            # Remove old requests outside the window
            cutoff = now - self.window_seconds
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            
            # Check if we can add this request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            
            return False
    
    def get_count(self) -> int:
        """Get current request count in window"""
        with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds
            self.requests = [req_time for req_time in self.requests if req_time > cutoff]
            return len(self.requests)
    
    def time_until_reset(self) -> float:
        """Get seconds until window resets"""
        if not self.requests:
            return 0
        
        oldest_request = min(self.requests)
        return max(0, self.window_seconds - (time.time() - oldest_request))


class ServiceRateLimiter:
    """
    Comprehensive rate limiting service that provides multi-tier, multi-scope
    rate limiting with intelligent throttling and integration with subscription tiers.
    """
    
    def __init__(
        self,
        tier_manager: TierManager,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        config: Optional[Dict[str, Any]] = None
    ):
        self.tier_manager = tier_manager
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.config = config or {}
        
        # Rate limit configurations
        self.rate_limits: Dict[str, RateLimitConfig] = {}
        self.bucket_cache: Dict[str, TokenBucket] = {}
        self.window_cache: Dict[str, SlidingWindowCounter] = {}
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 3600)  # 1 hour
        self.enable_persistence = self.config.get("enable_persistence", True)
        self.default_throttle_factor = self.config.get("default_throttle_factor", 0.5)
        
        # Load default rate limits
        self._load_default_rate_limits()
    
    def _load_default_rate_limits(self):
        """Load default rate limit configurations"""
        default_limits = [
            # Global rate limits
            RateLimitConfig(
                limit_id="global_api_requests",
                name="Global API Rate Limit",
                description="Global rate limit for all API requests",
                scope=RateLimitScope.GLOBAL,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                requests_per_window=100000,
                window_seconds=3600,  # 1 hour
                enable_throttling=False
            ),
            
            # IP-based rate limits
            RateLimitConfig(
                limit_id="ip_api_requests",
                name="IP-based API Rate Limit",
                description="Rate limit per IP address",
                scope=RateLimitScope.IP_ADDRESS,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                requests_per_window=1000,
                window_seconds=3600,  # 1 hour
                burst_capacity=100,
                tier_multipliers={
                    "FREE": 0.5,
                    "STARTER": 1.0,
                    "PROFESSIONAL": 2.0,
                    "ENTERPRISE": 5.0,
                    "SCALE": 10.0
                }
            ),
            
            # User-based rate limits
            RateLimitConfig(
                limit_id="user_api_requests",
                name="User API Rate Limit",
                description="Rate limit per authenticated user",
                scope=RateLimitScope.USER,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                requests_per_window=2000,
                window_seconds=3600,  # 1 hour
                burst_capacity=200,
                tier_multipliers={
                    "FREE": 0.5,
                    "STARTER": 1.0,
                    "PROFESSIONAL": 3.0,
                    "ENTERPRISE": 10.0,
                    "SCALE": 25.0
                }
            ),
            
            # Organization-based rate limits
            RateLimitConfig(
                limit_id="org_api_requests",
                name="Organization API Rate Limit",
                description="Rate limit per organization",
                scope=RateLimitScope.ORGANIZATION,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                requests_per_window=5000,
                window_seconds=3600,  # 1 hour
                burst_capacity=500,
                tier_multipliers={
                    "FREE": 0.2,
                    "STARTER": 1.0,
                    "PROFESSIONAL": 5.0,
                    "ENTERPRISE": 20.0,
                    "SCALE": 50.0
                }
            ),
            
            # Endpoint-specific rate limits
            RateLimitConfig(
                limit_id="auth_endpoints",
                name="Authentication Endpoints",
                description="Rate limit for authentication endpoints",
                scope=RateLimitScope.IP_ADDRESS,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                requests_per_window=10,
                window_seconds=300,  # 5 minutes
                path_patterns=["/api/v1/auth/*"],
                enable_throttling=False,
                grace_period_seconds=60
            ),
            
            RateLimitConfig(
                limit_id="firs_submissions",
                name="FIRS Submission Rate Limit",
                description="Rate limit for FIRS submission endpoints",
                scope=RateLimitScope.ORGANIZATION,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                requests_per_window=1000,
                window_seconds=3600,  # 1 hour
                burst_capacity=50,
                path_patterns=["/api/v1/firs/*", "/api/v1/irn/*"],
                tier_multipliers={
                    "FREE": 0.1,
                    "STARTER": 1.0,
                    "PROFESSIONAL": 5.0,
                    "ENTERPRISE": 20.0,
                    "SCALE": 100.0
                }
            ),
            
            # Feature-specific rate limits
            RateLimitConfig(
                limit_id="bulk_operations",
                name="Bulk Operations Rate Limit",
                description="Rate limit for bulk processing operations",
                scope=RateLimitScope.ORGANIZATION,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                requests_per_window=10,
                window_seconds=3600,  # 1 hour
                path_patterns=["/api/v1/*/bulk", "/api/v1/bulk/*"],
                tier_multipliers={
                    "PROFESSIONAL": 1.0,
                    "ENTERPRISE": 5.0,
                    "SCALE": 20.0
                }
            )
        ]
        
        for limit_config in default_limits:
            self.register_rate_limit(limit_config)
    
    def register_rate_limit(self, config: RateLimitConfig):
        """Register a new rate limit configuration"""
        self.rate_limits[config.limit_id] = config
        logger.info(f"Registered rate limit: {config.limit_id}")
    
    async def check_rate_limit(
        self,
        limit_id: str,
        scope_id: str,
        request_path: str = "",
        organization_tier: Optional[str] = None,
        request_count: int = 1
    ) -> RateLimitResult:
        """
        Check if request is within rate limits
        """
        try:
            # Get rate limit configuration
            config = self.rate_limits.get(limit_id)
            if not config or not config.enabled:
                return RateLimitResult(
                    limit_id=limit_id,
                    scope_id=scope_id,
                    decision=RateLimitDecision.ALLOWED,
                    allowed=True,
                    reason="Rate limit not configured or disabled",
                    current_usage=0,
                    limit=0,
                    remaining=0,
                    reset_time=datetime.now(timezone.utc)
                )
            
            # Check if path should be excluded
            if self._should_exclude_path(config, request_path):
                return RateLimitResult(
                    limit_id=limit_id,
                    scope_id=scope_id,
                    decision=RateLimitDecision.ALLOWED,
                    allowed=True,
                    reason="Path excluded from rate limiting",
                    current_usage=0,
                    limit=0,
                    remaining=0,
                    reset_time=datetime.now(timezone.utc)
                )
            
            # Check if path matches (if patterns specified)
            if config.path_patterns and not self._matches_path_pattern(config, request_path):
                return RateLimitResult(
                    limit_id=limit_id,
                    scope_id=scope_id,
                    decision=RateLimitDecision.ALLOWED,
                    allowed=True,
                    reason="Path not covered by rate limit",
                    current_usage=0,
                    limit=0,
                    remaining=0,
                    reset_time=datetime.now(timezone.utc)
                )
            
            # Get effective limits (considering tier multipliers)
            effective_limit, burst_capacity = await self._get_effective_limits(
                config, organization_tier
            )
            
            # Evaluate based on algorithm
            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                result = await self._check_token_bucket(
                    config, scope_id, effective_limit, burst_capacity, request_count
                )
            elif config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                result = await self._check_sliding_window(
                    config, scope_id, effective_limit, request_count
                )
            elif config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                result = await self._check_fixed_window(
                    config, scope_id, effective_limit, request_count
                )
            else:
                # Default to token bucket
                result = await self._check_token_bucket(
                    config, scope_id, effective_limit, burst_capacity, request_count
                )
            
            # Add rate limit headers
            result.headers = self._generate_rate_limit_headers(result, config)
            
            # Record metrics
            await self._record_rate_limit_metrics(config, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking rate limit {limit_id}:{scope_id}: {e}")
            # Fail open - allow request but log error
            return RateLimitResult(
                limit_id=limit_id,
                scope_id=scope_id,
                decision=RateLimitDecision.ALLOWED,
                allowed=True,
                reason=f"Rate limit check error: {str(e)}",
                current_usage=0,
                limit=0,
                remaining=0,
                reset_time=datetime.now(timezone.utc)
            )
    
    async def _check_token_bucket(
        self,
        config: RateLimitConfig,
        scope_id: str,
        limit: int,
        burst_capacity: int,
        request_count: int
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm"""
        
        bucket_key = f"{config.limit_id}:{scope_id}"
        
        # Get or create token bucket
        bucket = await self._get_or_create_bucket(
            bucket_key, burst_capacity, limit / config.window_seconds
        )
        
        # Check if we can consume tokens
        can_consume = bucket.consume(request_count)
        current_tokens = bucket.peek()
        
        # Calculate usage and remaining
        current_usage = burst_capacity - int(current_tokens)
        remaining = max(0, int(current_tokens))
        
        # Calculate reset time (when bucket will be full again)
        seconds_to_full = (burst_capacity - current_tokens) / bucket.refill_rate
        reset_time = datetime.now(timezone.utc) + timedelta(seconds=seconds_to_full)
        
        if can_consume:
            # Request allowed
            decision = RateLimitDecision.ALLOWED
            allowed = True
            reason = "Within rate limit"
            
            # Check if throttling should be applied
            usage_percentage = current_usage / burst_capacity
            if config.enable_throttling and usage_percentage >= config.throttle_threshold:
                decision = RateLimitDecision.THROTTLED
                throttle_delay = self._calculate_throttle_delay(usage_percentage)
                reason = "Throttled due to high usage"
            else:
                throttle_delay = None
        else:
            # Request blocked
            decision = RateLimitDecision.BLOCKED
            allowed = False
            reason = "Rate limit exceeded"
            throttle_delay = None
            
            # Calculate retry after
            retry_after = max(1, int(request_count / bucket.refill_rate))
        
        # Persist bucket state if enabled
        if self.enable_persistence:
            await self._persist_bucket(bucket_key, bucket)
        
        return RateLimitResult(
            limit_id=config.limit_id,
            scope_id=scope_id,
            decision=decision,
            allowed=allowed,
            reason=reason,
            current_usage=current_usage,
            limit=burst_capacity,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after if not can_consume else None,
            throttle_delay=throttle_delay
        )
    
    async def _check_sliding_window(
        self,
        config: RateLimitConfig,
        scope_id: str,
        limit: int,
        request_count: int
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm"""
        
        window_key = f"{config.limit_id}:{scope_id}"
        
        # Get or create sliding window counter
        counter = await self._get_or_create_window(window_key, config.window_seconds, limit)
        
        # Check if we can add this request
        can_add = counter.add_request() if request_count == 1 else False
        
        # For multi-request counts, check manually
        if request_count > 1:
            current_count = counter.get_count()
            can_add = (current_count + request_count) <= limit
            
            if can_add:
                # Add the requests
                for _ in range(request_count):
                    counter.add_request()
        
        current_usage = counter.get_count()
        remaining = max(0, limit - current_usage)
        
        # Calculate reset time
        time_until_reset = counter.time_until_reset()
        reset_time = datetime.now(timezone.utc) + timedelta(seconds=time_until_reset)
        
        if can_add:
            decision = RateLimitDecision.ALLOWED
            allowed = True
            reason = "Within rate limit"
            throttle_delay = None
            retry_after = None
            
            # Check if throttling should be applied
            usage_percentage = current_usage / limit if limit > 0 else 0
            if config.enable_throttling and usage_percentage >= config.throttle_threshold:
                decision = RateLimitDecision.THROTTLED
                throttle_delay = self._calculate_throttle_delay(usage_percentage)
                reason = "Throttled due to high usage"
        else:
            decision = RateLimitDecision.BLOCKED
            allowed = False
            reason = "Rate limit exceeded"
            throttle_delay = None
            retry_after = max(1, int(time_until_reset))
        
        return RateLimitResult(
            limit_id=config.limit_id,
            scope_id=scope_id,
            decision=decision,
            allowed=allowed,
            reason=reason,
            current_usage=current_usage,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after,
            throttle_delay=throttle_delay
        )
    
    async def _check_fixed_window(
        self,
        config: RateLimitConfig,
        scope_id: str,
        limit: int,
        request_count: int
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm"""
        
        # Calculate current window
        now = datetime.now(timezone.utc)
        window_start = now.replace(
            minute=0 if config.window_seconds >= 3600 else (now.minute // (config.window_seconds // 60)) * (config.window_seconds // 60),
            second=0,
            microsecond=0
        )
        
        if config.window_seconds < 3600:
            window_start = window_start.replace(second=0)
        
        window_key = f"{config.limit_id}:{scope_id}:{window_start.isoformat()}"
        
        # Get current usage from cache
        current_usage = await self.cache_manager.get(window_key) or 0
        current_usage = int(current_usage)
        
        # Check if request can be allowed
        projected_usage = current_usage + request_count
        can_allow = projected_usage <= limit
        
        if can_allow:
            # Update usage count
            window_end = window_start + timedelta(seconds=config.window_seconds)
            ttl = int((window_end - now).total_seconds())
            await self.cache_manager.set(window_key, projected_usage, ttl=ttl)
            
            decision = RateLimitDecision.ALLOWED
            allowed = True
            reason = "Within rate limit"
            current_usage = projected_usage
        else:
            decision = RateLimitDecision.BLOCKED
            allowed = False
            reason = "Rate limit exceeded"
        
        remaining = max(0, limit - current_usage)
        
        # Calculate reset time
        reset_time = window_start + timedelta(seconds=config.window_seconds)
        retry_after = int((reset_time - now).total_seconds()) if not can_allow else None
        
        return RateLimitResult(
            limit_id=config.limit_id,
            scope_id=scope_id,
            decision=decision,
            allowed=allowed,
            reason=reason,
            current_usage=current_usage,
            limit=limit,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=retry_after
        )
    
    async def _get_effective_limits(
        self,
        config: RateLimitConfig,
        organization_tier: Optional[str]
    ) -> Tuple[int, int]:
        """Get effective limits considering tier multipliers"""
        
        base_limit = config.requests_per_window
        base_burst = config.burst_capacity or base_limit
        
        if organization_tier and organization_tier in config.tier_multipliers:
            multiplier = config.tier_multipliers[organization_tier]
            effective_limit = int(base_limit * multiplier)
            effective_burst = int(base_burst * multiplier)
        else:
            effective_limit = base_limit
            effective_burst = base_burst
        
        return effective_limit, effective_burst
    
    def _should_exclude_path(self, config: RateLimitConfig, path: str) -> bool:
        """Check if path should be excluded from rate limiting"""
        for exclude_pattern in config.exclude_paths:
            if self._match_pattern(path, exclude_pattern):
                return True
        return False
    
    def _matches_path_pattern(self, config: RateLimitConfig, path: str) -> bool:
        """Check if path matches any of the configured patterns"""
        for pattern in config.path_patterns:
            if self._match_pattern(path, pattern):
                return True
        return False
    
    def _match_pattern(self, path: str, pattern: str) -> bool:
        """Match path against pattern (supports wildcards)"""
        if pattern.endswith('*'):
            return path.startswith(pattern[:-1])
        return path == pattern
    
    async def _get_or_create_bucket(
        self,
        bucket_key: str,
        capacity: int,
        refill_rate: float
    ) -> TokenBucket:
        """Get existing token bucket or create new one"""
        
        if bucket_key in self.bucket_cache:
            return self.bucket_cache[bucket_key]
        
        # Try to load from persistence
        if self.enable_persistence:
            bucket_data = await self.cache_manager.get(f"bucket:{bucket_key}")
            if bucket_data:
                bucket = TokenBucket.from_dict(bucket_data)
                self.bucket_cache[bucket_key] = bucket
                return bucket
        
        # Create new bucket
        bucket = TokenBucket(capacity, refill_rate)
        self.bucket_cache[bucket_key] = bucket
        return bucket
    
    async def _get_or_create_window(
        self,
        window_key: str,
        window_seconds: int,
        max_requests: int
    ) -> SlidingWindowCounter:
        """Get existing sliding window counter or create new one"""
        
        if window_key in self.window_cache:
            return self.window_cache[window_key]
        
        # Create new window counter
        counter = SlidingWindowCounter(window_seconds, max_requests)
        self.window_cache[window_key] = counter
        return counter
    
    async def _persist_bucket(self, bucket_key: str, bucket: TokenBucket):
        """Persist token bucket state"""
        await self.cache_manager.set(
            f"bucket:{bucket_key}",
            bucket.to_dict(),
            ttl=self.cache_ttl
        )
    
    def _calculate_throttle_delay(self, usage_percentage: float) -> float:
        """Calculate throttle delay based on usage percentage"""
        if usage_percentage >= 0.95:
            return 2.0  # 2 second delay
        elif usage_percentage >= 0.90:
            return 1.0  # 1 second delay
        elif usage_percentage >= 0.80:
            return 0.5  # 0.5 second delay
        else:
            return 0.1  # 0.1 second delay
    
    def _generate_rate_limit_headers(
        self,
        result: RateLimitResult,
        config: RateLimitConfig
    ) -> Dict[str, str]:
        """Generate standard rate limit headers"""
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
            "X-RateLimit-Window": str(config.window_seconds)
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        if result.throttle_delay:
            headers["X-RateLimit-Throttle-Delay"] = str(result.throttle_delay)
        
        return headers
    
    async def _record_rate_limit_metrics(
        self,
        config: RateLimitConfig,
        result: RateLimitResult
    ):
        """Record rate limiting metrics"""
        await self.metrics_collector.record_counter(
            "rate_limit_checks",
            tags={
                "limit_id": config.limit_id,
                "scope": config.scope.value,
                "decision": result.decision.value
            }
        )
        
        if result.decision == RateLimitDecision.BLOCKED:
            await self.metrics_collector.record_counter(
                "rate_limit_blocks",
                tags={
                    "limit_id": config.limit_id,
                    "scope": config.scope.value
                }
            )


# Decorator for rate limiting

def rate_limit(limit_id: str, scope_attr: str = "organization_id"):
    """
    Decorator to apply rate limiting to FastAPI endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and scope from function parameters
            request = None
            scope_id = None
            
            for arg in args:
                if hasattr(arg, 'url') and hasattr(arg, 'headers'):  # FastAPI Request
                    request = arg
                    scope_id = getattr(request.state, scope_attr, None)
                    break
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Rate limiter: Request object not found"
                )
            
            # Get rate limiter from request state
            rate_limiter = getattr(request.state, 'rate_limiter', None)
            if not rate_limiter:
                raise HTTPException(
                    status_code=500,
                    detail="Rate limiter not available"
                )
            
            # Get organization tier if available
            organization_tier = getattr(request.state, 'subscription_tier', None)
            
            # Check rate limit
            result = await rate_limiter.check_rate_limit(
                limit_id=limit_id,
                scope_id=scope_id or request.client.host,
                request_path=request.url.path,
                organization_tier=organization_tier
            )
            
            if not result.allowed:
                # Add rate limit headers to error response
                headers = result.headers
                
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {result.reason}",
                    headers=headers
                )
            
            # Add throttle delay if specified
            if result.throttle_delay:
                await asyncio.sleep(result.throttle_delay)
            
            # Store result for potential use
            request.state.rate_limit_result = result
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator