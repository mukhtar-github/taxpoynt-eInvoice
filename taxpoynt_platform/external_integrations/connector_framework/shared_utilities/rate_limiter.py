"""
API Rate Limiting Utilities
===========================

Intelligent rate limiting for financial service API integrations.
Supports token bucket, sliding window, and adaptive rate limiting strategies.
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import redis.asyncio as redis
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"

class RateLimitScope(str, Enum):
    """Rate limit scope"""
    GLOBAL = "global"
    PER_USER = "per_user"
    PER_ENDPOINT = "per_endpoint"
    PER_IP = "per_ip"
    PER_API_KEY = "per_api_key"

@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    
    # Basic limits
    requests_per_second: int
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    
    # Strategy and scope
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET
    scope: RateLimitScope = RateLimitScope.GLOBAL
    
    # Token bucket specific
    bucket_size: Optional[int] = None
    refill_rate: Optional[int] = None
    
    # Burst handling
    allow_burst: bool = True
    burst_multiplier: float = 2.0
    
    # Adaptive settings
    adaptive_window_minutes: int = 15
    adaptive_threshold_percent: float = 80.0
    
    # Penalties
    violation_penalty_seconds: int = 60
    max_violations_per_hour: int = 10

@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    
    allowed: bool
    remaining_requests: int
    reset_time: datetime
    retry_after_seconds: Optional[int] = None
    
    # Additional info
    current_usage: int = 0
    limit_exceeded_reason: Optional[str] = None
    suggested_delay_ms: int = 0

@dataclass
class RateLimitState:
    """Internal rate limit state"""
    
    identifier: str
    strategy: RateLimitStrategy
    
    # Token bucket state
    tokens: float = 0.0
    last_refill: datetime = field(default_factory=datetime.utcnow)
    
    # Window state
    request_timestamps: deque = field(default_factory=deque)
    window_start: datetime = field(default_factory=datetime.utcnow)
    window_requests: int = 0
    
    # Violation tracking
    violations: List[datetime] = field(default_factory=list)
    penalty_until: Optional[datetime] = None
    
    # Adaptive state
    adaptive_history: deque = field(default_factory=deque)
    current_limit_multiplier: float = 1.0

class TokenBucketLimiter:
    """Token bucket rate limiter implementation"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.TokenBucketLimiter")
        
        # Calculate bucket parameters
        self.bucket_size = config.bucket_size or config.requests_per_second * 2
        self.refill_rate = config.refill_rate or config.requests_per_second
        
    def check_limit(self, state: RateLimitState) -> RateLimitResult:
        """Check if request is allowed under token bucket"""
        
        current_time = datetime.utcnow()
        
        # Check penalty period
        if state.penalty_until and current_time < state.penalty_until:
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=state.penalty_until,
                retry_after_seconds=int((state.penalty_until - current_time).total_seconds()),
                limit_exceeded_reason="penalty_period"
            )
        
        # Refill tokens
        time_passed = (current_time - state.last_refill).total_seconds()
        tokens_to_add = time_passed * self.refill_rate
        state.tokens = min(self.bucket_size, state.tokens + tokens_to_add)
        state.last_refill = current_time
        
        # Check if tokens available
        if state.tokens >= 1.0:
            state.tokens -= 1.0
            
            # Calculate reset time (when bucket will be full)
            time_to_full = (self.bucket_size - state.tokens) / self.refill_rate
            reset_time = current_time + timedelta(seconds=time_to_full)
            
            return RateLimitResult(
                allowed=True,
                remaining_requests=int(state.tokens),
                reset_time=reset_time,
                current_usage=self.bucket_size - int(state.tokens)
            )
        else:
            # Calculate when next token will be available
            time_to_next_token = (1.0 - state.tokens) / self.refill_rate
            reset_time = current_time + timedelta(seconds=time_to_next_token)
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=reset_time,
                retry_after_seconds=int(time_to_next_token),
                limit_exceeded_reason="insufficient_tokens",
                suggested_delay_ms=int(time_to_next_token * 1000)
            )

class SlidingWindowLimiter:
    """Sliding window rate limiter implementation"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.SlidingWindowLimiter")
    
    def check_limit(self, state: RateLimitState) -> RateLimitResult:
        """Check if request is allowed under sliding window"""
        
        current_time = datetime.utcnow()
        
        # Check penalty period
        if state.penalty_until and current_time < state.penalty_until:
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=state.penalty_until,
                retry_after_seconds=int((state.penalty_until - current_time).total_seconds()),
                limit_exceeded_reason="penalty_period"
            )
        
        # Clean old timestamps (sliding window)
        window_start = current_time - timedelta(seconds=60)  # 1 minute window
        
        # Remove timestamps outside window
        while state.request_timestamps and state.request_timestamps[0] < window_start:
            state.request_timestamps.popleft()
        
        # Check current usage
        current_requests = len(state.request_timestamps)
        
        if current_requests < self.config.requests_per_minute:
            # Add current request timestamp
            state.request_timestamps.append(current_time)
            
            # Calculate reset time (when oldest request exits window)
            if state.request_timestamps:
                oldest_request = state.request_timestamps[0]
                reset_time = oldest_request + timedelta(seconds=60)
            else:
                reset_time = current_time + timedelta(seconds=60)
            
            return RateLimitResult(
                allowed=True,
                remaining_requests=self.config.requests_per_minute - current_requests - 1,
                reset_time=reset_time,
                current_usage=current_requests + 1
            )
        else:
            # Calculate when window will have space
            oldest_request = state.request_timestamps[0]
            reset_time = oldest_request + timedelta(seconds=60)
            retry_after = int((reset_time - current_time).total_seconds())
            
            return RateLimitResult(
                allowed=False,
                remaining_requests=0,
                reset_time=reset_time,
                retry_after_seconds=max(1, retry_after),
                limit_exceeded_reason="window_full",
                suggested_delay_ms=max(1000, retry_after * 1000)
            )

class AdaptiveLimiter:
    """Adaptive rate limiter that adjusts based on system load"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.AdaptiveLimiter")
        self.base_limiter = TokenBucketLimiter(config)
    
    def check_limit(self, state: RateLimitState, system_load: float = 0.5) -> RateLimitResult:
        """Check limit with adaptive adjustment"""
        
        current_time = datetime.utcnow()
        
        # Update adaptive history
        state.adaptive_history.append((current_time, system_load))
        
        # Keep only recent history
        history_cutoff = current_time - timedelta(minutes=self.config.adaptive_window_minutes)
        while state.adaptive_history and state.adaptive_history[0][0] < history_cutoff:
            state.adaptive_history.popleft()
        
        # Calculate average system load
        if state.adaptive_history:
            avg_load = sum(load for _, load in state.adaptive_history) / len(state.adaptive_history)
        else:
            avg_load = system_load
        
        # Adjust limit based on system load
        if avg_load > 0.8:  # High load
            state.current_limit_multiplier = 0.5
        elif avg_load > 0.6:  # Medium load
            state.current_limit_multiplier = 0.7
        elif avg_load < 0.3:  # Low load
            state.current_limit_multiplier = 1.5
        else:  # Normal load
            state.current_limit_multiplier = 1.0
        
        # Apply multiplier to refill rate
        original_refill_rate = self.base_limiter.refill_rate
        self.base_limiter.refill_rate = int(original_refill_rate * state.current_limit_multiplier)
        
        # Get base result
        result = self.base_limiter.check_limit(state)
        
        # Restore original refill rate
        self.base_limiter.refill_rate = original_refill_rate
        
        # Add adaptive info
        if hasattr(result, 'metadata'):
            result.metadata = {}
        result.metadata = {
            'adaptive_multiplier': state.current_limit_multiplier,
            'system_load': avg_load,
            'adjusted_limit': int(self.config.requests_per_second * state.current_limit_multiplier)
        }
        
        return result

class RateLimiter:
    """Main rate limiter class"""
    
    def __init__(self, 
                 config: RateLimitConfig,
                 redis_client: Optional[redis.Redis] = None):
        """Initialize rate limiter"""
        
        self.config = config
        self.redis_client = redis_client
        self.logger = logging.getLogger(f"{__name__}.RateLimiter")
        
        # In-memory state for local operation
        self.local_states: Dict[str, RateLimitState] = {}
        
        # Create strategy-specific limiter
        if config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            self.limiter = TokenBucketLimiter(config)
        elif config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            self.limiter = SlidingWindowLimiter(config)
        elif config.strategy == RateLimitStrategy.ADAPTIVE:
            self.limiter = AdaptiveLimiter(config)
        else:
            self.limiter = TokenBucketLimiter(config)  # Default
        
        self.logger.info(f"Rate limiter initialized with {config.strategy} strategy")
    
    async def check_rate_limit(self, 
                              identifier: str,
                              scope_value: Optional[str] = None,
                              system_load: float = 0.5) -> RateLimitResult:
        """Check if request should be rate limited"""
        
        try:
            # Create full identifier
            full_identifier = self._create_identifier(identifier, scope_value)
            
            # Get or create state
            state = await self._get_state(full_identifier)
            
            # Check limits
            if hasattr(self.limiter, 'system_load'):
                result = self.limiter.check_limit(state, system_load)
            else:
                result = self.limiter.check_limit(state)
            
            # Handle violations
            if not result.allowed:
                await self._record_violation(state)
            
            # Save state
            await self._save_state(full_identifier, state)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Rate limit check error: {e}")
            # Fail open - allow request but log error
            return RateLimitResult(
                allowed=True,
                remaining_requests=self.config.requests_per_second,
                reset_time=datetime.utcnow() + timedelta(seconds=60),
                limit_exceeded_reason=f"rate_limiter_error: {str(e)}"
            )
    
    def _create_identifier(self, identifier: str, scope_value: Optional[str] = None) -> str:
        """Create full rate limit identifier"""
        
        if self.config.scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope_value:
            return f"{self.config.scope.value}:{scope_value}:{identifier}"
        else:
            return f"{self.config.scope.value}:{identifier}"
    
    async def _get_state(self, identifier: str) -> RateLimitState:
        """Get rate limit state"""
        
        if self.redis_client:
            return await self._get_redis_state(identifier)
        else:
            return self._get_local_state(identifier)
    
    def _get_local_state(self, identifier: str) -> RateLimitState:
        """Get state from local memory"""
        
        if identifier not in self.local_states:
            self.local_states[identifier] = RateLimitState(
                identifier=identifier,
                strategy=self.config.strategy,
                tokens=float(self.config.requests_per_second)
            )
        
        return self.local_states[identifier]
    
    async def _get_redis_state(self, identifier: str) -> RateLimitState:
        """Get state from Redis"""
        
        try:
            state_key = f"rate_limit:{identifier}"
            state_data = await self.redis_client.hgetall(state_key)
            
            if state_data:
                # Reconstruct state from Redis data
                state = RateLimitState(
                    identifier=identifier,
                    strategy=RateLimitStrategy(state_data.get('strategy', 'token_bucket')),
                    tokens=float(state_data.get('tokens', self.config.requests_per_second)),
                    last_refill=datetime.fromisoformat(state_data.get('last_refill', datetime.utcnow().isoformat())),
                    window_requests=int(state_data.get('window_requests', 0)),
                    current_limit_multiplier=float(state_data.get('multiplier', 1.0))
                )
                
                # Handle penalty
                penalty_until = state_data.get('penalty_until')
                if penalty_until:
                    state.penalty_until = datetime.fromisoformat(penalty_until)
                
                return state
            else:
                # Create new state
                return RateLimitState(
                    identifier=identifier,
                    strategy=self.config.strategy,
                    tokens=float(self.config.requests_per_second)
                )
                
        except Exception as e:
            self.logger.error(f"Redis state retrieval error: {e}")
            # Fallback to local state
            return self._get_local_state(identifier)
    
    async def _save_state(self, identifier: str, state: RateLimitState):
        """Save rate limit state"""
        
        if self.redis_client:
            await self._save_redis_state(identifier, state)
        # Local state is saved by reference, no action needed
    
    async def _save_redis_state(self, identifier: str, state: RateLimitState):
        """Save state to Redis"""
        
        try:
            state_key = f"rate_limit:{identifier}"
            state_data = {
                'strategy': state.strategy.value,
                'tokens': str(state.tokens),
                'last_refill': state.last_refill.isoformat(),
                'window_requests': str(state.window_requests),
                'multiplier': str(state.current_limit_multiplier)
            }
            
            if state.penalty_until:
                state_data['penalty_until'] = state.penalty_until.isoformat()
            
            await self.redis_client.hset(state_key, mapping=state_data)
            await self.redis_client.expire(state_key, 3600)  # Expire in 1 hour
            
        except Exception as e:
            self.logger.error(f"Redis state save error: {e}")
    
    async def _record_violation(self, state: RateLimitState):
        """Record rate limit violation"""
        
        current_time = datetime.utcnow()
        state.violations.append(current_time)
        
        # Clean old violations (last hour)
        hour_ago = current_time - timedelta(hours=1)
        state.violations = [v for v in state.violations if v > hour_ago]
        
        # Apply penalty if too many violations
        if len(state.violations) >= self.config.max_violations_per_hour:
            penalty_duration = self.config.violation_penalty_seconds * len(state.violations)
            state.penalty_until = current_time + timedelta(seconds=penalty_duration)
            
            self.logger.warning(f"Rate limit penalty applied: {state.identifier} for {penalty_duration}s")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        
        stats = {
            'config': {
                'strategy': self.config.strategy.value,
                'scope': self.config.scope.value,
                'requests_per_second': self.config.requests_per_second,
                'requests_per_minute': self.config.requests_per_minute,
                'requests_per_hour': self.config.requests_per_hour
            },
            'active_identifiers': len(self.local_states),
            'violations_last_hour': 0,
            'penalties_active': 0
        }
        
        # Count violations and penalties
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        
        for state in self.local_states.values():
            # Count recent violations
            recent_violations = [v for v in state.violations if v > hour_ago]
            stats['violations_last_hour'] += len(recent_violations)
            
            # Count active penalties
            if state.penalty_until and current_time < state.penalty_until:
                stats['penalties_active'] += 1
        
        return stats
    
    async def reset_limits(self, identifier: Optional[str] = None):
        """Reset rate limits for identifier or all"""
        
        if identifier:
            full_identifier = self._create_identifier(identifier)
            if full_identifier in self.local_states:
                del self.local_states[full_identifier]
            
            if self.redis_client:
                await self.redis_client.delete(f"rate_limit:{full_identifier}")
        else:
            # Reset all
            self.local_states.clear()
            
            if self.redis_client:
                keys = await self.redis_client.keys("rate_limit:*")
                if keys:
                    await self.redis_client.delete(*keys)
        
        self.logger.info(f"Rate limits reset for: {identifier or 'all identifiers'}")

class RateLimitManager:
    """Manage multiple rate limiters"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.limiters: Dict[str, RateLimiter] = {}
        self.logger = logging.getLogger(f"{__name__}.RateLimitManager")
    
    def add_limiter(self, name: str, config: RateLimitConfig):
        """Add rate limiter"""
        
        self.limiters[name] = RateLimiter(config, self.redis_client)
        self.logger.info(f"Added rate limiter: {name}")
    
    async def check_limits(self, 
                          limiter_names: List[str],
                          identifier: str,
                          scope_value: Optional[str] = None) -> Dict[str, RateLimitResult]:
        """Check multiple rate limiters"""
        
        results = {}
        
        for name in limiter_names:
            if name in self.limiters:
                result = await self.limiters[name].check_rate_limit(
                    identifier, scope_value
                )
                results[name] = result
            else:
                self.logger.warning(f"Unknown rate limiter: {name}")
        
        return results
    
    async def is_allowed(self, 
                        limiter_names: List[str],
                        identifier: str,
                        scope_value: Optional[str] = None) -> bool:
        """Check if request is allowed by all limiters"""
        
        results = await self.check_limits(limiter_names, identifier, scope_value)
        return all(result.allowed for result in results.values())
    
    def get_limiter_names(self) -> List[str]:
        """Get all limiter names"""
        
        return list(self.limiters.keys())
    
    async def get_all_statistics(self) -> Dict[str, Any]:
        """Get statistics for all limiters"""
        
        all_stats = {}
        
        for name, limiter in self.limiters.items():
            all_stats[name] = await limiter.get_statistics()
        
        return all_stats