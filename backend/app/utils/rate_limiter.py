"""
Rate Limiter for Transmission API endpoints

Provides a configurable rate limiting mechanism to prevent API abuse
while allowing legitimate high-volume transmission scenarios.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Set, Any
from uuid import UUID
import threading
from functools import wraps
from fastapi import HTTPException, Request, Depends
from app.config import settings

logger = logging.getLogger(__name__)

class TokenBucket:
    """
    Token Bucket Algorithm implementation for rate limiting.
    
    This algorithm allows for controlled bursts while enforcing
    a long-term rate limit. Each bucket has:
    - A maximum capacity (tokens)
    - A refill rate (tokens per second)
    - A current token count
    
    When a request is made, tokens are consumed. If no tokens
    are available, the request is rejected.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize a token bucket.
        
        Args:
            capacity: Maximum number of tokens the bucket can hold
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def refill(self) -> None:
        """Refill tokens based on elapsed time since last refill"""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        with self.lock:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if not enough tokens
        """
        self.refill()
        
        with self.lock:
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimiter:
    """
    Rate limiter implementation for the application.
    
    Supports multiple rate limit tiers and different limits
    per organization, user, and endpoint.
    """
    
    # Default rate limit settings
    DEFAULT_TIER = {
        "tier_name": "default",
        "transmission_per_minute": 60,
        "burst_capacity": 100,
        "max_payload_size_mb": 5,
        "concurrent_transmissions": 10
    }
    
    # Premium tier settings for high-volume customers
    PREMIUM_TIER = {
        "tier_name": "premium",
        "transmission_per_minute": 500,
        "burst_capacity": 1000,
        "max_payload_size_mb": 20,
        "concurrent_transmissions": 50
    }
    
    # Admin tier with practically no limits
    ADMIN_TIER = {
        "tier_name": "admin",
        "transmission_per_minute": 3000,
        "burst_capacity": 5000,
        "max_payload_size_mb": 50,
        "concurrent_transmissions": 200
    }
    
    def __init__(self):
        """Initialize rate limiter with storage for buckets"""
        # Mapping of (org_id, endpoint) to TokenBucket
        self.org_buckets: Dict[Tuple[str, str], TokenBucket] = {}
        
        # Mapping of (user_id, endpoint) to TokenBucket
        self.user_buckets: Dict[Tuple[str, str], TokenBucket] = {}
        
        # Global bucket for IP-based rate limiting
        self.ip_buckets: Dict[str, TokenBucket] = {}
        
        # Track active transmissions per organization
        self.active_transmissions: Dict[str, Set[str]] = {}
        
        # Track organization rate limit tiers
        self.org_tiers: Dict[str, Dict[str, Any]] = {}
        
        # Lock for thread safety
        self.lock = threading.RLock()
    
    def get_org_tier(self, org_id: str) -> Dict[str, Any]:
        """Get rate limit tier for an organization"""
        with self.lock:
            return self.org_tiers.get(org_id, self.DEFAULT_TIER)
    
    def set_org_tier(self, org_id: str, tier_name: str) -> None:
        """Set rate limit tier for an organization"""
        with self.lock:
            if tier_name == "premium":
                self.org_tiers[org_id] = self.PREMIUM_TIER
            elif tier_name == "admin":
                self.org_tiers[org_id] = self.ADMIN_TIER
            else:
                self.org_tiers[org_id] = self.DEFAULT_TIER
    
    def get_org_bucket(self, org_id: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for organization and endpoint"""
        key = (org_id, endpoint)
        
        with self.lock:
            if key not in self.org_buckets:
                tier = self.get_org_tier(org_id)
                capacity = tier["burst_capacity"]
                rate = tier["transmission_per_minute"] / 60.0  # Convert to per-second
                self.org_buckets[key] = TokenBucket(capacity, rate)
            
            return self.org_buckets[key]
    
    def get_user_bucket(self, user_id: str, endpoint: str) -> TokenBucket:
        """Get or create token bucket for user and endpoint"""
        key = (user_id, endpoint)
        
        with self.lock:
            if key not in self.user_buckets:
                # User limits are lower than org limits to prevent a single user
                # from consuming all of an organization's capacity
                self.user_buckets[key] = TokenBucket(50, 0.5)  # 30 per minute
            
            return self.user_buckets[key]
    
    def get_ip_bucket(self, ip: str) -> TokenBucket:
        """Get or create token bucket for IP address"""
        with self.lock:
            if ip not in self.ip_buckets:
                # Very restrictive for IPs to prevent DDoS
                self.ip_buckets[ip] = TokenBucket(30, 0.2)  # 12 per minute
            
            return self.ip_buckets[ip]
    
    def start_transmission(self, org_id: str, transmission_id: str) -> bool:
        """
        Register an active transmission for concurrency tracking.
        
        Returns:
            True if transmission can start, False if org is at capacity
        """
        tier = self.get_org_tier(org_id)
        max_concurrent = tier["concurrent_transmissions"]
        
        with self.lock:
            if org_id not in self.active_transmissions:
                self.active_transmissions[org_id] = set()
            
            active_set = self.active_transmissions[org_id]
            if len(active_set) >= max_concurrent:
                return False
            
            active_set.add(transmission_id)
            return True
    
    def end_transmission(self, org_id: str, transmission_id: str) -> None:
        """Mark a transmission as complete, removing it from active set"""
        with self.lock:
            if org_id in self.active_transmissions:
                self.active_transmissions[org_id].discard(transmission_id)
    
    def check_payload_size(self, org_id: str, size_bytes: int) -> bool:
        """Check if payload size is within allowed limits"""
        tier = self.get_org_tier(org_id)
        max_size_bytes = tier["max_payload_size_mb"] * 1024 * 1024
        return size_bytes <= max_size_bytes
    
    def allow_request(
        self, 
        org_id: str, 
        user_id: Optional[str], 
        ip: str, 
        endpoint: str, 
        payload_size: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Determine if a request should be allowed based on rate limits.
        
        Args:
            org_id: Organization ID
            user_id: User ID (optional)
            ip: Client IP address
            endpoint: API endpoint being accessed
            payload_size: Size of payload in bytes (optional)
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        # Check payload size if provided
        if payload_size is not None:
            if not self.check_payload_size(org_id, payload_size):
                tier = self.get_org_tier(org_id)
                return False, f"Payload size exceeds the maximum allowed ({tier['max_payload_size_mb']} MB)"
        
        # Check IP rate limit (prevents DDoS)
        ip_bucket = self.get_ip_bucket(ip)
        if not ip_bucket.consume():
            return False, "IP rate limit exceeded"
        
        # Check organization rate limit
        org_bucket = self.get_org_bucket(org_id, endpoint)
        if not org_bucket.consume():
            tier = self.get_org_tier(org_id)
            return False, f"Organization rate limit exceeded ({tier['transmission_per_minute']} per minute)"
        
        # Check user rate limit if user_id provided
        if user_id:
            user_bucket = self.get_user_bucket(user_id, endpoint)
            if not user_bucket.consume():
                return False, "User rate limit exceeded"
        
        return True, "Request allowed"


# Create a singleton instance
rate_limiter = RateLimiter()

def rate_limit_dependency(request: Request):
    """FastAPI dependency for rate limiting"""
    return rate_limiter

def check_rate_limit(tokens: int = 1, payload_size_param: Optional[str] = None):
    """
    Decorator for FastAPI endpoints to apply rate limiting.
    
    Args:
        tokens: Number of tokens to consume (default: 1)
        payload_size_param: Name of the parameter containing payload size (optional)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            org_id = None
            user_id = None
            
            # Extract request, org_id, and user_id from kwargs
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
            
            if request is None:
                request = kwargs.get('request')
            
            if request is None:
                # If we can't find request, skip rate limiting
                return await func(*args, **kwargs)
            
            # Get client IP
            client_ip = request.client.host if request.client else "unknown"
            
            # Extract org_id and user_id from request
            org_id = request.headers.get("X-Organization-ID")
            user_id = request.headers.get("X-User-ID")
            
            if not org_id:
                # Try to get from path parameters
                org_id = kwargs.get("organization_id") or kwargs.get("org_id")
            
            if not user_id:
                # Try to get from path parameters
                user_id = kwargs.get("user_id")
            
            # If we still don't have org_id, skip rate limiting
            if not org_id:
                return await func(*args, **kwargs)
            
            # Get endpoint path
            endpoint = request.url.path
            
            # Check payload size if specified
            payload_size = None
            if payload_size_param and payload_size_param in kwargs:
                payload_size = len(str(kwargs[payload_size_param]).encode())
            
            # Check rate limit
            allowed, reason = rate_limiter.allow_request(
                org_id=str(org_id),
                user_id=str(user_id) if user_id else None,
                ip=client_ip,
                endpoint=endpoint,
                payload_size=payload_size
            )
            
            if not allowed:
                logger.warning(f"Rate limit exceeded: {reason} (org: {org_id}, ip: {client_ip})")
                raise HTTPException(status_code=429, detail=f"Too many requests: {reason}")
            
            # If allowed, proceed with the original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator
