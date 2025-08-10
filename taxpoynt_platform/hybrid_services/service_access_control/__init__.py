"""
TaxPoynt Platform - Service Access Control Package

This package provides centralized access control, feature gating, quota management,
rate limiting, and subscription validation for the TaxPoynt platform. It integrates
with existing backend middleware and platform services to provide unified access control.

Key Components:
- AccessMiddleware: Runtime access control and request validation
- FeatureGating: Dynamic feature-based restrictions and rollouts  
- QuotaManager: Usage-based limits and enforcement
- RateLimiter: API rate limiting and throttling
- SubscriptionGuard: Subscription tier validation and compliance

This package complements existing implementations:
- Backend middleware (rate_limit.py, api_key_auth.py, security.py)
- Platform services (tier_manager.py, usage_tracker.py, access_controller.py)
- Configuration management (feature_flag_manager.py)
"""

from .access_middleware import AccessMiddleware, AccessRequest, AccessResponse
from .feature_gating import FeatureGate, FeatureGateConfig, FeatureAccessResult
from .quota_manager import QuotaManager, QuotaConfig, QuotaEnforcement
from .rate_limiter import ServiceRateLimiter, RateLimitConfig, RateLimitResult
from .subscription_guard import SubscriptionGuard, SubscriptionValidation, AccessDecision

__all__ = [
    # Access Middleware
    "AccessMiddleware",
    "AccessRequest", 
    "AccessResponse",
    
    # Feature Gating
    "FeatureGate",
    "FeatureGateConfig",
    "FeatureAccessResult",
    
    # Quota Management
    "QuotaManager",
    "QuotaConfig", 
    "QuotaEnforcement",
    
    # Rate Limiting
    "ServiceRateLimiter",
    "RateLimitConfig",
    "RateLimitResult",
    
    # Subscription Guard
    "SubscriptionGuard",
    "SubscriptionValidation",
    "AccessDecision",
]

__version__ = "1.0.0"