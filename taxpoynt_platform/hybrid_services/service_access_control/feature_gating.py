"""
Feature Gating - Feature-based restrictions and dynamic access control

This module provides comprehensive feature gating capabilities that integrate with
the existing feature flag manager and tier management system to provide dynamic
feature access control based on subscription tiers, user roles, and business rules.

Integrates with:
- configuration_management/feature_flag_manager.py for flag evaluation
- billing_orchestration/tier_manager.py for tier-based features  
- core platform security for access validation
"""

import asyncio
import logging
import hashlib
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set, Union
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import inspect

# Import existing platform services
from ...configuration_management.feature_flag_manager import (
    FeatureFlagManager, FlagType, FlagStatus, RolloutStrategy
)
from ...billing_orchestration.tier_manager import TierManager, FeatureCategory
from ....core_platform.monitoring import MetricsCollector
from ....core_platform.data_management.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class FeatureAccessDecision(str, Enum):
    """Feature access decisions"""
    GRANTED = "granted"
    DENIED = "denied"
    TIER_RESTRICTED = "tier_restricted"
    FLAG_DISABLED = "flag_disabled"
    ROLLOUT_EXCLUDED = "rollout_excluded"
    QUOTA_EXCEEDED = "quota_exceeded"
    TEMPORARILY_DISABLED = "temporarily_disabled"


class FeatureType(str, Enum):
    """Types of features that can be gated"""
    CORE_FEATURE = "core_feature"
    PREMIUM_FEATURE = "premium_feature"
    EXPERIMENTAL_FEATURE = "experimental_feature"
    INTEGRATION_FEATURE = "integration_feature"
    API_ENDPOINT = "api_endpoint"
    UI_COMPONENT = "ui_component"
    WORKFLOW = "workflow"
    ENHANCEMENT = "enhancement"


class GatingStrategy(str, Enum):
    """Feature gating strategies"""
    TIER_BASED = "tier_based"          # Based on subscription tier
    ROLE_BASED = "role_based"          # Based on user role
    FLAG_BASED = "flag_based"          # Based on feature flags
    HYBRID = "hybrid"                  # Combination of multiple strategies
    USAGE_BASED = "usage_based"        # Based on usage quotas
    TIME_BASED = "time_based"          # Based on time windows


@dataclass
class FeatureContext:
    """Context for feature access evaluation"""
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    subscription_tier: Optional[str] = None
    user_roles: List[str] = None
    client_ip: str = "unknown"
    user_agent: str = "unknown"
    request_path: str = ""
    session_id: Optional[str] = None
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_roles is None:
            self.user_roles = []
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class FeatureGateConfig:
    """Configuration for a feature gate"""
    feature_name: str
    feature_type: FeatureType
    gating_strategy: GatingStrategy
    required_tier: Optional[str] = None
    required_roles: List[str] = None
    feature_flag: Optional[str] = None
    rollout_percentage: Optional[float] = None
    max_usage_per_day: Optional[int] = None
    max_usage_per_month: Optional[int] = None
    time_restrictions: Optional[Dict[str, Any]] = None
    custom_rules: List[str] = None
    enabled: bool = True
    description: str = ""
    
    def __post_init__(self):
        if self.required_roles is None:
            self.required_roles = []
        if self.custom_rules is None:
            self.custom_rules = []


@dataclass
class FeatureAccessResult:
    """Result of feature access evaluation"""
    feature_name: str
    decision: FeatureAccessDecision
    allowed: bool
    reason: str
    context: FeatureContext
    metadata: Dict[str, Any] = None
    cache_ttl: int = 300  # 5 minutes default
    expires_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.expires_at is None:
            self.expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.cache_ttl)


class FeatureGate:
    """
    Comprehensive feature gating system that provides dynamic access control
    for features based on multiple factors including subscription tiers, user roles,
    feature flags, and custom business rules.
    """
    
    def __init__(
        self,
        feature_flag_manager: FeatureFlagManager,
        tier_manager: TierManager,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        config: Optional[Dict[str, Any]] = None
    ):
        self.feature_flag_manager = feature_flag_manager
        self.tier_manager = tier_manager
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.config = config or {}
        
        # Feature gate configurations
        self.feature_gates: Dict[str, FeatureGateConfig] = {}
        self.custom_evaluators: Dict[str, callable] = {}
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 300)
        self.enable_rollout_hashing = self.config.get("enable_rollout_hashing", True)
        self.default_rollout_percentage = self.config.get("default_rollout_percentage", 0.0)
        
        # Load default feature gates
        self._load_default_feature_gates()
    
    def _load_default_feature_gates(self):
        """Load default feature gate configurations"""
        default_gates = {
            # Core FIRS features
            "firs_irn_generation": FeatureGateConfig(
                feature_name="firs_irn_generation",
                feature_type=FeatureType.CORE_FEATURE,
                gating_strategy=GatingStrategy.TIER_BASED,
                required_tier="STARTER",
                description="FIRS IRN generation capability"
            ),
            
            "firs_bulk_processing": FeatureGateConfig(
                feature_name="firs_bulk_processing",
                feature_type=FeatureType.PREMIUM_FEATURE,
                gating_strategy=GatingStrategy.TIER_BASED,
                required_tier="PROFESSIONAL",
                max_usage_per_day=1000,
                description="Bulk IRN processing"
            ),
            
            # Integration features
            "erp_integration": FeatureGateConfig(
                feature_name="erp_integration",
                feature_type=FeatureType.INTEGRATION_FEATURE,
                gating_strategy=GatingStrategy.TIER_BASED,
                required_tier="PROFESSIONAL",
                description="ERP system integration"
            ),
            
            "advanced_analytics": FeatureGateConfig(
                feature_name="advanced_analytics",
                feature_type=FeatureType.PREMIUM_FEATURE,
                gating_strategy=GatingStrategy.TIER_BASED,
                required_tier="ENTERPRISE",
                description="Advanced analytics and reporting"
            ),
            
            # API features
            "api_rate_limit_extended": FeatureGateConfig(
                feature_name="api_rate_limit_extended",
                feature_type=FeatureType.PREMIUM_FEATURE,
                gating_strategy=GatingStrategy.TIER_BASED,
                required_tier="PROFESSIONAL",
                description="Extended API rate limits"
            ),
            
            # Experimental features
            "ai_invoice_validation": FeatureGateConfig(
                feature_name="ai_invoice_validation",
                feature_type=FeatureType.EXPERIMENTAL_FEATURE,
                gating_strategy=GatingStrategy.HYBRID,
                feature_flag="enable_ai_validation",
                required_tier="ENTERPRISE",
                rollout_percentage=10.0,
                description="AI-powered invoice validation"
            ),
            
            # Admin features
            "platform_admin": FeatureGateConfig(
                feature_name="platform_admin",
                feature_type=FeatureType.CORE_FEATURE,
                gating_strategy=GatingStrategy.ROLE_BASED,
                required_roles=["admin", "platform_admin"],
                description="Platform administration features"
            )
        }
        
        for feature_name, config in default_gates.items():
            self.register_feature_gate(config)
    
    def register_feature_gate(self, config: FeatureGateConfig):
        """Register a new feature gate configuration"""
        self.feature_gates[config.feature_name] = config
        logger.info(f"Registered feature gate: {config.feature_name}")
    
    def register_custom_evaluator(self, feature_name: str, evaluator: callable):
        """Register a custom evaluator function for a feature"""
        self.custom_evaluators[feature_name] = evaluator
        logger.info(f"Registered custom evaluator for feature: {feature_name}")
    
    async def check_feature_access(
        self,
        feature_name: str,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """
        Check if feature access should be granted based on context
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(feature_name, context)
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result and not self._is_result_expired(cached_result):
                result = FeatureAccessResult(**cached_result)
                await self._record_access_metrics(feature_name, result.decision, "cached")
                return result
            
            # Get feature gate configuration
            gate_config = self.feature_gates.get(feature_name)
            if not gate_config:
                result = FeatureAccessResult(
                    feature_name=feature_name,
                    decision=FeatureAccessDecision.DENIED,
                    allowed=False,
                    reason="Feature gate not configured",
                    context=context
                )
                await self._record_access_metrics(feature_name, result.decision, "unconfigured")
                return result
            
            # Check if feature is enabled
            if not gate_config.enabled:
                result = FeatureAccessResult(
                    feature_name=feature_name,
                    decision=FeatureAccessDecision.TEMPORARILY_DISABLED,
                    allowed=False,
                    reason="Feature temporarily disabled",
                    context=context
                )
                await self._record_access_metrics(feature_name, result.decision, "disabled")
                return result
            
            # Evaluate based on gating strategy
            result = await self._evaluate_feature_access(gate_config, context)
            
            # Cache the result if successful
            if result.allowed:
                await self.cache_manager.set(
                    cache_key,
                    asdict(result),
                    ttl=result.cache_ttl
                )
            
            await self._record_access_metrics(feature_name, result.decision, "evaluated")
            return result
            
        except Exception as e:
            logger.error(f"Error checking feature access for {feature_name}: {e}")
            result = FeatureAccessResult(
                feature_name=feature_name,
                decision=FeatureAccessDecision.DENIED,
                allowed=False,
                reason=f"Evaluation error: {str(e)}",
                context=context
            )
            await self._record_access_metrics(feature_name, result.decision, "error")
            return result
    
    async def _evaluate_feature_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate feature access based on gating strategy"""
        
        strategy = gate_config.gating_strategy
        
        if strategy == GatingStrategy.TIER_BASED:
            return await self._evaluate_tier_based_access(gate_config, context)
        elif strategy == GatingStrategy.ROLE_BASED:
            return await self._evaluate_role_based_access(gate_config, context)
        elif strategy == GatingStrategy.FLAG_BASED:
            return await self._evaluate_flag_based_access(gate_config, context)
        elif strategy == GatingStrategy.HYBRID:
            return await self._evaluate_hybrid_access(gate_config, context)
        elif strategy == GatingStrategy.USAGE_BASED:
            return await self._evaluate_usage_based_access(gate_config, context)
        elif strategy == GatingStrategy.TIME_BASED:
            return await self._evaluate_time_based_access(gate_config, context)
        else:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.DENIED,
                allowed=False,
                reason=f"Unknown gating strategy: {strategy}",
                context=context
            )
    
    async def _evaluate_tier_based_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access based on subscription tier"""
        
        if not gate_config.required_tier:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="No tier restriction",
                context=context
            )
        
        if not context.organization_id or not context.subscription_tier:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.TIER_RESTRICTED,
                allowed=False,
                reason="Organization or subscription tier not identified",
                context=context
            )
        
        # Check tier access through tier manager
        tier_check = await self.tier_manager.check_feature_access(
            organization_id=context.organization_id,
            feature=gate_config.feature_name,
            tier=context.subscription_tier
        )
        
        if tier_check.decision == "granted":
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="Tier access granted",
                context=context,
                metadata={"tier_info": asdict(tier_check)}
            )
        else:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.TIER_RESTRICTED,
                allowed=False,
                reason=f"Tier access denied: {tier_check.decision}",
                context=context,
                metadata={"tier_info": asdict(tier_check)}
            )
    
    async def _evaluate_role_based_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access based on user roles"""
        
        if not gate_config.required_roles:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="No role restriction",
                context=context
            )
        
        if not context.user_roles:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.DENIED,
                allowed=False,
                reason="User roles not identified",
                context=context
            )
        
        # Check if user has any of the required roles
        user_roles_set = set(context.user_roles)
        required_roles_set = set(gate_config.required_roles)
        
        if user_roles_set.intersection(required_roles_set):
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="Role access granted",
                context=context,
                metadata={"matching_roles": list(user_roles_set.intersection(required_roles_set))}
            )
        else:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.DENIED,
                allowed=False,
                reason="Required roles not found",
                context=context,
                metadata={"required_roles": gate_config.required_roles}
            )
    
    async def _evaluate_flag_based_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access based on feature flags"""
        
        if not gate_config.feature_flag:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="No feature flag restriction",
                context=context
            )
        
        # Evaluate feature flag
        flag_result = await self.feature_flag_manager.evaluate_flag(
            flag_name=gate_config.feature_flag,
            user_id=context.user_id,
            organization_id=context.organization_id,
            attributes=context.metadata
        )
        
        if flag_result.enabled:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="Feature flag enabled",
                context=context,
                metadata={"flag_result": asdict(flag_result)}
            )
        else:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.FLAG_DISABLED,
                allowed=False,
                reason="Feature flag disabled",
                context=context,
                metadata={"flag_result": asdict(flag_result)}
            )
    
    async def _evaluate_hybrid_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access using multiple strategies (AND logic)"""
        
        # Check tier-based access if required
        if gate_config.required_tier:
            tier_result = await self._evaluate_tier_based_access(gate_config, context)
            if not tier_result.allowed:
                return tier_result
        
        # Check role-based access if required
        if gate_config.required_roles:
            role_result = await self._evaluate_role_based_access(gate_config, context)
            if not role_result.allowed:
                return role_result
        
        # Check feature flag if specified
        if gate_config.feature_flag:
            flag_result = await self._evaluate_flag_based_access(gate_config, context)
            if not flag_result.allowed:
                return flag_result
        
        # Check rollout percentage if specified
        if gate_config.rollout_percentage is not None:
            if not self._check_rollout_eligibility(gate_config, context):
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.ROLLOUT_EXCLUDED,
                    allowed=False,
                    reason="Excluded from rollout",
                    context=context
                )
        
        # Check custom rules if specified
        if gate_config.custom_rules:
            custom_result = await self._evaluate_custom_rules(gate_config, context)
            if not custom_result.allowed:
                return custom_result
        
        return FeatureAccessResult(
            feature_name=gate_config.feature_name,
            decision=FeatureAccessDecision.GRANTED,
            allowed=True,
            reason="All hybrid checks passed",
            context=context
        )
    
    async def _evaluate_usage_based_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access based on usage quotas"""
        
        if not context.organization_id:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.DENIED,
                allowed=False,
                reason="Organization not identified",
                context=context
            )
        
        # Check daily usage if specified
        if gate_config.max_usage_per_day:
            daily_usage = await self._get_daily_usage(
                gate_config.feature_name,
                context.organization_id
            )
            if daily_usage >= gate_config.max_usage_per_day:
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.QUOTA_EXCEEDED,
                    allowed=False,
                    reason="Daily usage quota exceeded",
                    context=context,
                    metadata={"daily_usage": daily_usage, "daily_limit": gate_config.max_usage_per_day}
                )
        
        # Check monthly usage if specified
        if gate_config.max_usage_per_month:
            monthly_usage = await self._get_monthly_usage(
                gate_config.feature_name,
                context.organization_id
            )
            if monthly_usage >= gate_config.max_usage_per_month:
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.QUOTA_EXCEEDED,
                    allowed=False,
                    reason="Monthly usage quota exceeded",
                    context=context,
                    metadata={"monthly_usage": monthly_usage, "monthly_limit": gate_config.max_usage_per_month}
                )
        
        return FeatureAccessResult(
            feature_name=gate_config.feature_name,
            decision=FeatureAccessDecision.GRANTED,
            allowed=True,
            reason="Usage quota available",
            context=context
        )
    
    async def _evaluate_time_based_access(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate access based on time restrictions"""
        
        if not gate_config.time_restrictions:
            return FeatureAccessResult(
                feature_name=gate_config.feature_name,
                decision=FeatureAccessDecision.GRANTED,
                allowed=True,
                reason="No time restrictions",
                context=context
            )
        
        current_time = context.timestamp or datetime.now(timezone.utc)
        restrictions = gate_config.time_restrictions
        
        # Check time window restrictions
        if "allowed_hours" in restrictions:
            current_hour = current_time.hour
            allowed_hours = restrictions["allowed_hours"]
            if current_hour not in allowed_hours:
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.TEMPORARILY_DISABLED,
                    allowed=False,
                    reason="Outside allowed time window",
                    context=context,
                    metadata={"current_hour": current_hour, "allowed_hours": allowed_hours}
                )
        
        # Check date range restrictions
        if "start_date" in restrictions and "end_date" in restrictions:
            start_date = datetime.fromisoformat(restrictions["start_date"])
            end_date = datetime.fromisoformat(restrictions["end_date"])
            if not (start_date <= current_time <= end_date):
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.TEMPORARILY_DISABLED,
                    allowed=False,
                    reason="Outside allowed date range",
                    context=context,
                    metadata={"current_time": current_time.isoformat(), "allowed_range": restrictions}
                )
        
        return FeatureAccessResult(
            feature_name=gate_config.feature_name,
            decision=FeatureAccessDecision.GRANTED,
            allowed=True,
            reason="Time restrictions satisfied",
            context=context
        )
    
    async def _evaluate_custom_rules(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> FeatureAccessResult:
        """Evaluate custom business rules"""
        
        # Check if custom evaluator is registered
        if gate_config.feature_name in self.custom_evaluators:
            try:
                evaluator = self.custom_evaluators[gate_config.feature_name]
                result = await evaluator(gate_config, context)
                return result
            except Exception as e:
                logger.error(f"Custom evaluator error for {gate_config.feature_name}: {e}")
                return FeatureAccessResult(
                    feature_name=gate_config.feature_name,
                    decision=FeatureAccessDecision.DENIED,
                    allowed=False,
                    reason=f"Custom rule evaluation failed: {str(e)}",
                    context=context
                )
        
        # Default: allow if no custom rules
        return FeatureAccessResult(
            feature_name=gate_config.feature_name,
            decision=FeatureAccessDecision.GRANTED,
            allowed=True,
            reason="No custom rules to evaluate",
            context=context
        )
    
    def _check_rollout_eligibility(
        self,
        gate_config: FeatureGateConfig,
        context: FeatureContext
    ) -> bool:
        """Check if user/org is eligible for feature rollout"""
        
        if not self.enable_rollout_hashing:
            return random.random() * 100 < gate_config.rollout_percentage
        
        # Use deterministic hashing for consistent rollout
        hash_input = f"{gate_config.feature_name}:{context.organization_id or context.user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        percentage = (hash_value % 100) + 1
        
        return percentage <= gate_config.rollout_percentage
    
    def _generate_cache_key(self, feature_name: str, context: FeatureContext) -> str:
        """Generate cache key for feature access result"""
        key_parts = [
            f"feature_gate",
            feature_name,
            context.user_id or "anonymous",
            context.organization_id or "no_org",
            context.subscription_tier or "no_tier",
            "|".join(sorted(context.user_roles)) if context.user_roles else "no_roles"
        ]
        return ":".join(key_parts)
    
    def _is_result_expired(self, cached_result: Dict[str, Any]) -> bool:
        """Check if cached result has expired"""
        expires_at = cached_result.get("expires_at")
        if not expires_at:
            return True
        
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        return datetime.now(timezone.utc) > expires_at
    
    async def _get_daily_usage(self, feature_name: str, organization_id: str) -> int:
        """Get daily usage count for feature"""
        # This would integrate with usage tracking system
        cache_key = f"daily_usage:{feature_name}:{organization_id}:{datetime.now().strftime('%Y-%m-%d')}"
        usage = await self.cache_manager.get(cache_key)
        return int(usage) if usage else 0
    
    async def _get_monthly_usage(self, feature_name: str, organization_id: str) -> int:
        """Get monthly usage count for feature"""
        # This would integrate with usage tracking system
        cache_key = f"monthly_usage:{feature_name}:{organization_id}:{datetime.now().strftime('%Y-%m')}"
        usage = await self.cache_manager.get(cache_key)
        return int(usage) if usage else 0
    
    async def _record_access_metrics(self, feature_name: str, decision: str, source: str):
        """Record feature access metrics"""
        await self.metrics_collector.record_counter(
            "feature_gate_access",
            tags={
                "feature": feature_name,
                "decision": decision,
                "source": source
            }
        )


# Decorators for easy integration

def require_feature(feature_name: str):
    """
    Decorator to require feature access for FastAPI endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and context from function parameters
            request = None
            for arg in args:
                if hasattr(arg, 'url') and hasattr(arg, 'headers'):  # FastAPI Request
                    request = arg
                    break
            
            if not request:
                raise HTTPException(
                    status_code=500,
                    detail="Feature gate decorator: Request object not found"
                )
            
            # Get feature gate from request state (set by middleware)
            feature_gate = getattr(request.state, 'feature_gate', None)
            if not feature_gate:
                raise HTTPException(
                    status_code=500,
                    detail="Feature gate not available"
                )
            
            # Build context from request
            context = FeatureContext(
                user_id=getattr(request.state, 'user_id', None),
                organization_id=getattr(request.state, 'organization_id', None),
                subscription_tier=getattr(request.state, 'subscription_tier', None),
                user_roles=getattr(request.state, 'user_roles', []),
                client_ip=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
                request_path=request.url.path,
                session_id=request.cookies.get("session_id")
            )
            
            # Check feature access
            result = await feature_gate.check_feature_access(feature_name, context)
            
            if not result.allowed:
                raise HTTPException(
                    status_code=403,
                    detail=f"Feature access denied: {result.reason}"
                )
            
            # Store result in request state for potential use
            request.state.feature_access_result = result
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def feature_flag_enabled(flag_name: str):
    """
    Decorator to check if feature flag is enabled
    """
    def decorator(func):
        func._required_feature_flag = flag_name
        return func
    return decorator