"""
Tier Manager - Tier-based access control and feature management
Comprehensive tier management system providing dynamic access control, feature flags,
and quota enforcement based on subscription tiers.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID
from functools import wraps
import inspect

from core_platform.data_management.billing_repository import BillingRepository, SubscriptionTier
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class AccessDecision(str, Enum):
    """Access control decisions"""
    GRANTED = "granted"
    DENIED = "denied"
    THROTTLED = "throttled"
    USAGE_LIMITED = "usage_limited"
    UPGRADE_REQUIRED = "upgrade_required"


class FeatureCategory(str, Enum):
    """Feature categories for organization"""
    CORE = "core"
    ADVANCED = "advanced"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    INTEGRATION = "integration"
    ANALYTICS = "analytics"
    SUPPORT = "support"


class QuotaType(str, Enum):
    """Types of quotas that can be enforced"""
    DAILY = "daily"
    MONTHLY = "monthly"
    CONCURRENT = "concurrent"
    TOTAL = "total"


@dataclass
class Feature:
    """Feature definition with tier access controls"""
    feature_id: str
    name: str
    description: str
    category: FeatureCategory
    enabled_tiers: Set[SubscriptionTier]
    quota_limits: Dict[SubscriptionTier, Dict[QuotaType, int]]
    dependencies: List[str]  # Other features this depends on
    metadata: Dict[str, Any]


@dataclass
class AccessRequest:
    """Access control request"""
    request_id: str
    tenant_id: UUID
    organization_id: UUID
    feature_id: str
    user_id: Optional[str]
    request_type: str  # 'feature_access', 'quota_check', 'api_call', etc.
    requested_quantity: int
    metadata: Dict[str, Any]
    timestamp: datetime


@dataclass
class AccessResponse:
    """Access control response"""
    request_id: str
    decision: AccessDecision
    granted_quantity: int
    reason: str
    tier_required: Optional[SubscriptionTier]
    quota_remaining: Optional[int]
    reset_time: Optional[datetime]
    suggestions: List[str]
    metadata: Dict[str, Any]


@dataclass
class TierConfiguration:
    """Tier-specific configuration"""
    tier: SubscriptionTier
    features: Set[str]
    quotas: Dict[str, Dict[QuotaType, int]]
    rate_limits: Dict[str, int]
    support_level: str
    sla_guarantees: Dict[str, Any]
    customizations: Dict[str, Any]


@dataclass
class UsageTrackingRecord:
    """Usage tracking for quota enforcement"""
    tracking_id: str
    tenant_id: UUID
    feature_id: str
    quota_type: QuotaType
    current_usage: int
    quota_limit: int
    reset_time: datetime
    first_usage: datetime
    last_usage: datetime


class TierManager:
    """Tier-based Access Control and Feature Management System"""
    
    def __init__(self):
        self.billing_repository = BillingRepository()
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Tier management registries
        self.features: Dict[str, Feature] = {}
        self.tier_configurations: Dict[SubscriptionTier, TierConfiguration] = {}
        self.usage_tracking: Dict[str, UsageTrackingRecord] = {}
        self.access_requests: Dict[str, AccessRequest] = {}
        
        # Configuration
        self.config = {
            "cache_ttl_seconds": 300,  # 5 minutes
            "usage_reset_check_interval": 3600,  # 1 hour
            "quota_warning_threshold": 0.8,  # 80%
            "access_log_retention_days": 30,
            "upgrade_suggestion_threshold": 3,  # After 3 denials
            "rate_limit_window_seconds": 60
        }
        
        # Initialize features and tier configurations
        self._initialize_features()
        self._initialize_tier_configurations()
    
    async def check_feature_access(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        feature_id: str,
        user_id: Optional[str] = None,
        requested_quantity: int = 1
    ) -> AccessResponse:
        """Check access to a specific feature"""
        try:
            request_id = f"access_{int(datetime.now().timestamp())}_{tenant_id}"
            
            # Create access request
            request = AccessRequest(
                request_id=request_id,
                tenant_id=tenant_id,
                organization_id=organization_id,
                feature_id=feature_id,
                user_id=user_id,
                request_type="feature_access",
                requested_quantity=requested_quantity,
                metadata={},
                timestamp=datetime.now(timezone.utc)
            )
            
            # Store request for audit
            self.access_requests[request_id] = request
            
            # Get subscription details
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.DENIED,
                    granted_quantity=0,
                    reason="No active subscription found",
                    tier_required=SubscriptionTier.STARTER,
                    quota_remaining=None,
                    reset_time=None,
                    suggestions=["Please activate a subscription to access features"],
                    metadata={}
                )
            
            current_tier = SubscriptionTier(subscription["subscription_tier"])
            
            # Check if feature exists
            feature = self.features.get(feature_id)
            if not feature:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.DENIED,
                    granted_quantity=0,
                    reason=f"Feature '{feature_id}' not found",
                    tier_required=None,
                    quota_remaining=None,
                    reset_time=None,
                    suggestions=[],
                    metadata={}
                )
            
            # Check tier access
            if current_tier not in feature.enabled_tiers:
                required_tier = await self._get_minimum_tier_for_feature(feature_id)
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.UPGRADE_REQUIRED,
                    granted_quantity=0,
                    reason=f"Feature requires {required_tier.value} tier or higher",
                    tier_required=required_tier,
                    quota_remaining=None,
                    reset_time=None,
                    suggestions=[f"Upgrade to {required_tier.value} tier to access this feature"],
                    metadata={"current_tier": current_tier.value}
                )
            
            # Check quota limits
            quota_check = await self._check_quota_limits(
                tenant_id, feature_id, current_tier, requested_quantity
            )
            
            if not quota_check["allowed"]:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.USAGE_LIMITED,
                    granted_quantity=quota_check["available_quantity"],
                    reason=quota_check["reason"],
                    tier_required=None,
                    quota_remaining=quota_check["remaining"],
                    reset_time=quota_check["reset_time"],
                    suggestions=quota_check["suggestions"],
                    metadata=quota_check["metadata"]
                )
            
            # Check dependencies
            dependency_check = await self._check_feature_dependencies(
                tenant_id, feature_id, current_tier
            )
            
            if not dependency_check["satisfied"]:
                return AccessResponse(
                    request_id=request_id,
                    decision=AccessDecision.DENIED,
                    granted_quantity=0,
                    reason=f"Missing dependencies: {', '.join(dependency_check['missing'])}",
                    tier_required=None,
                    quota_remaining=None,
                    reset_time=None,
                    suggestions=dependency_check["suggestions"],
                    metadata={"missing_dependencies": dependency_check["missing"]}
                )
            
            # Grant access and track usage
            await self._track_usage(tenant_id, feature_id, requested_quantity)
            
            # Log access
            await self._log_access_granted(request, current_tier)
            
            # Emit event
            await self.event_bus.emit("feature_access_granted", {
                "request_id": request_id,
                "tenant_id": str(tenant_id),
                "feature_id": feature_id,
                "tier": current_tier.value,
                "quantity": requested_quantity,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return AccessResponse(
                request_id=request_id,
                decision=AccessDecision.GRANTED,
                granted_quantity=requested_quantity,
                reason="Access granted",
                tier_required=None,
                quota_remaining=quota_check["remaining"] - requested_quantity,
                reset_time=quota_check["reset_time"],
                suggestions=[],
                metadata={"tier": current_tier.value}
            )
            
        except Exception as e:
            self.logger.error(f"Error checking feature access: {str(e)}")
            return AccessResponse(
                request_id=request_id,
                decision=AccessDecision.DENIED,
                granted_quantity=0,
                reason=f"Internal error: {str(e)}",
                tier_required=None,
                quota_remaining=None,
                reset_time=None,
                suggestions=["Please try again later"],
                metadata={"error": str(e)}
            )
    
    async def get_tier_features(
        self,
        tenant_id: UUID,
        include_quota_info: bool = True
    ) -> Dict[str, Any]:
        """Get available features for tenant's subscription tier"""
        try:
            # Get subscription
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {
                    "status": "error",
                    "message": "No active subscription found"
                }
            
            current_tier = SubscriptionTier(subscription["subscription_tier"])
            tier_config = self.tier_configurations.get(current_tier)
            
            if not tier_config:
                return {
                    "status": "error",
                    "message": f"Configuration not found for tier {current_tier.value}"
                }
            
            # Get available features
            available_features = []
            for feature_id in tier_config.features:
                feature = self.features.get(feature_id)
                if not feature:
                    continue
                
                feature_info = {
                    "feature_id": feature_id,
                    "name": feature.name,
                    "description": feature.description,
                    "category": feature.category.value
                }
                
                # Add quota information if requested
                if include_quota_info:
                    quota_info = await self._get_feature_quota_info(
                        tenant_id, feature_id, current_tier
                    )
                    feature_info["quota_info"] = quota_info
                
                available_features.append(feature_info)
            
            # Get tier comparison for upgrade suggestions
            tier_comparison = await self._get_tier_comparison(current_tier)
            
            return {
                "status": "success",
                "current_tier": current_tier.value,
                "tier_configuration": asdict(tier_config),
                "available_features": available_features,
                "tier_comparison": tier_comparison,
                "total_features": len(available_features),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tier features: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_usage_summary(
        self,
        tenant_id: UUID,
        feature_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get usage summary for tenant"""
        try:
            # Filter usage records
            usage_records = []
            for record in self.usage_tracking.values():
                if record.tenant_id == tenant_id:
                    if not feature_id or record.feature_id == feature_id:
                        usage_records.append(record)
            
            # Calculate summary metrics
            total_features_used = len(set(r.feature_id for r in usage_records))
            
            # Group by feature
            feature_usage = {}
            for record in usage_records:
                if record.feature_id not in feature_usage:
                    feature_usage[record.feature_id] = []
                feature_usage[record.feature_id].append(record)
            
            # Calculate feature-wise usage
            feature_summaries = []
            for fid, records in feature_usage.items():
                feature = self.features.get(fid)
                if not feature:
                    continue
                
                # Calculate total usage across all quota types
                total_usage = sum(r.current_usage for r in records)
                total_limit = sum(r.quota_limit for r in records)
                
                # Find most restrictive quota
                most_restrictive = min(records, key=lambda r: r.current_usage / r.quota_limit if r.quota_limit > 0 else 0)
                
                feature_summaries.append({
                    "feature_id": fid,
                    "feature_name": feature.name,
                    "total_usage": total_usage,
                    "total_limit": total_limit,
                    "usage_percentage": (total_usage / total_limit * 100) if total_limit > 0 else 0,
                    "most_restrictive_quota": {
                        "type": most_restrictive.quota_type.value,
                        "usage": most_restrictive.current_usage,
                        "limit": most_restrictive.quota_limit,
                        "percentage": (most_restrictive.current_usage / most_restrictive.quota_limit * 100) if most_restrictive.quota_limit > 0 else 0,
                        "reset_time": most_restrictive.reset_time.isoformat()
                    }
                })
            
            # Sort by usage percentage
            feature_summaries.sort(key=lambda x: x["usage_percentage"], reverse=True)
            
            return {
                "tenant_id": str(tenant_id),
                "total_features_used": total_features_used,
                "feature_usage": feature_summaries,
                "high_usage_features": [
                    f for f in feature_summaries 
                    if f["usage_percentage"] > 80
                ],
                "upgrade_recommendations": await self._get_upgrade_recommendations(tenant_id, feature_summaries),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting usage summary: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def require_tier(self, required_tier: SubscriptionTier, feature_id: Optional[str] = None):
        """Decorator for tier-based access control"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract tenant_id from function arguments
                tenant_id = None
                
                # Check function signature for tenant_id
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                if 'tenant_id' in bound_args.arguments:
                    tenant_id = bound_args.arguments['tenant_id']
                elif 'self' in bound_args.arguments and hasattr(bound_args.arguments['self'], 'tenant_id'):
                    tenant_id = bound_args.arguments['self'].tenant_id
                
                if not tenant_id:
                    raise ValueError("Cannot determine tenant_id for tier check")
                
                # Check access
                if feature_id:
                    access_response = await self.check_feature_access(
                        tenant_id=tenant_id,
                        organization_id=tenant_id,  # Assuming same for simplicity
                        feature_id=feature_id
                    )
                    
                    if access_response.decision != AccessDecision.GRANTED:
                        raise PermissionError(f"Access denied: {access_response.reason}")
                else:
                    # Simple tier check
                    subscription = await self.billing_repository.get_subscription(tenant_id)
                    if not subscription:
                        raise PermissionError("No active subscription found")
                    
                    current_tier = SubscriptionTier(subscription["subscription_tier"])
                    tier_order = {
                        SubscriptionTier.STARTER: 1,
                        SubscriptionTier.PROFESSIONAL: 2,
                        SubscriptionTier.ENTERPRISE: 3,
                        SubscriptionTier.SCALE: 4
                    }
                    
                    if tier_order.get(current_tier, 0) < tier_order.get(required_tier, 0):
                        raise PermissionError(f"Requires {required_tier.value} tier or higher")
                
                # Execute original function
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    async def enforce_quota(
        self,
        tenant_id: UUID,
        feature_id: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Enforce quota limits for feature usage"""
        try:
            # Check current usage against limits
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {
                    "allowed": False,
                    "reason": "No active subscription",
                    "remaining": 0
                }
            
            current_tier = SubscriptionTier(subscription["subscription_tier"])
            quota_check = await self._check_quota_limits(
                tenant_id, feature_id, current_tier, quantity
            )
            
            if quota_check["allowed"]:
                # Track the usage
                await self._track_usage(tenant_id, feature_id, quantity)
                
                # Emit usage event
                await self.event_bus.emit("quota_enforced", {
                    "tenant_id": str(tenant_id),
                    "feature_id": feature_id,
                    "quantity": quantity,
                    "remaining": quota_check["remaining"],
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return quota_check
            
        except Exception as e:
            self.logger.error(f"Error enforcing quota: {str(e)}")
            return {
                "allowed": False,
                "reason": f"Error: {str(e)}",
                "remaining": 0
            }
    
    # Private helper methods
    
    def _initialize_features(self):
        """Initialize feature definitions"""
        try:
            # Core features available to all tiers
            self.features["basic_erp_integration"] = Feature(
                feature_id="basic_erp_integration",
                name="Basic ERP Integration",
                description="Connect to basic ERP systems",
                category=FeatureCategory.INTEGRATION,
                enabled_tiers={SubscriptionTier.STARTER, SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE, SubscriptionTier.SCALE},
                quota_limits={
                    SubscriptionTier.STARTER: {QuotaType.MONTHLY: 1000, QuotaType.DAILY: 50},
                    SubscriptionTier.PROFESSIONAL: {QuotaType.MONTHLY: 10000, QuotaType.DAILY: 500},
                    SubscriptionTier.ENTERPRISE: {QuotaType.MONTHLY: 100000, QuotaType.DAILY: 5000},
                    SubscriptionTier.SCALE: {QuotaType.MONTHLY: 1000000, QuotaType.DAILY: 50000}
                },
                dependencies=[],
                metadata={"core_feature": True}
            )
            
            # Advanced features
            self.features["advanced_analytics"] = Feature(
                feature_id="advanced_analytics",
                name="Advanced Analytics",
                description="Detailed analytics and reporting",
                category=FeatureCategory.ANALYTICS,
                enabled_tiers={SubscriptionTier.PROFESSIONAL, SubscriptionTier.ENTERPRISE, SubscriptionTier.SCALE},
                quota_limits={
                    SubscriptionTier.PROFESSIONAL: {QuotaType.MONTHLY: 100, QuotaType.DAILY: 10},
                    SubscriptionTier.ENTERPRISE: {QuotaType.MONTHLY: 1000, QuotaType.DAILY: 100},
                    SubscriptionTier.SCALE: {QuotaType.MONTHLY: 10000, QuotaType.DAILY: 1000}
                },
                dependencies=["basic_erp_integration"],
                metadata={"premium_feature": True}
            )
            
            # Enterprise features
            self.features["custom_integrations"] = Feature(
                feature_id="custom_integrations",
                name="Custom Integrations",
                description="Build custom integration connectors",
                category=FeatureCategory.INTEGRATION,
                enabled_tiers={SubscriptionTier.ENTERPRISE, SubscriptionTier.SCALE},
                quota_limits={
                    SubscriptionTier.ENTERPRISE: {QuotaType.TOTAL: 5, QuotaType.CONCURRENT: 2},
                    SubscriptionTier.SCALE: {QuotaType.TOTAL: 50, QuotaType.CONCURRENT: 10}
                },
                dependencies=["advanced_analytics"],
                metadata={"enterprise_feature": True}
            )
            
            # Scale features
            self.features["white_label"] = Feature(
                feature_id="white_label",
                name="White Label Solution",
                description="Fully customizable white-label deployment",
                category=FeatureCategory.PREMIUM,
                enabled_tiers={SubscriptionTier.SCALE},
                quota_limits={
                    SubscriptionTier.SCALE: {QuotaType.TOTAL: 1}
                },
                dependencies=["custom_integrations"],
                metadata={"scale_feature": True}
            )
            
            self.logger.info(f"Initialized {len(self.features)} features")
            
        except Exception as e:
            self.logger.error(f"Error initializing features: {str(e)}")
    
    def _initialize_tier_configurations(self):
        """Initialize tier-specific configurations"""
        try:
            # Starter tier
            self.tier_configurations[SubscriptionTier.STARTER] = TierConfiguration(
                tier=SubscriptionTier.STARTER,
                features={"basic_erp_integration"},
                quotas={
                    "api_calls": {QuotaType.MONTHLY: 10000, QuotaType.DAILY: 500},
                    "storage": {QuotaType.TOTAL: 10},  # GB
                    "users": {QuotaType.TOTAL: 5}
                },
                rate_limits={"api_rate_per_minute": 100},
                support_level="email",
                sla_guarantees={"uptime": 99.0},
                customizations={}
            )
            
            # Professional tier
            self.tier_configurations[SubscriptionTier.PROFESSIONAL] = TierConfiguration(
                tier=SubscriptionTier.PROFESSIONAL,
                features={"basic_erp_integration", "advanced_analytics"},
                quotas={
                    "api_calls": {QuotaType.MONTHLY: 100000, QuotaType.DAILY: 5000},
                    "storage": {QuotaType.TOTAL: 100},  # GB
                    "users": {QuotaType.TOTAL: 25}
                },
                rate_limits={"api_rate_per_minute": 500},
                support_level="priority_email",
                sla_guarantees={"uptime": 99.5},
                customizations={"webhooks": True}
            )
            
            # Enterprise tier
            self.tier_configurations[SubscriptionTier.ENTERPRISE] = TierConfiguration(
                tier=SubscriptionTier.ENTERPRISE,
                features={"basic_erp_integration", "advanced_analytics", "custom_integrations"},
                quotas={
                    "api_calls": {QuotaType.MONTHLY: 1000000, QuotaType.DAILY: 50000},
                    "storage": {QuotaType.TOTAL: 1000},  # GB
                    "users": {QuotaType.TOTAL: 100}
                },
                rate_limits={"api_rate_per_minute": 2000},
                support_level="phone_and_email",
                sla_guarantees={"uptime": 99.9, "support_response_hours": 4},
                customizations={"webhooks": True, "custom_branding": True}
            )
            
            # Scale tier
            self.tier_configurations[SubscriptionTier.SCALE] = TierConfiguration(
                tier=SubscriptionTier.SCALE,
                features={"basic_erp_integration", "advanced_analytics", "custom_integrations", "white_label"},
                quotas={
                    "api_calls": {QuotaType.MONTHLY: 10000000, QuotaType.DAILY: 500000},
                    "storage": {QuotaType.TOTAL: 5000},  # GB
                    "users": {QuotaType.TOTAL: 500}
                },
                rate_limits={"api_rate_per_minute": 10000},
                support_level="dedicated_support",
                sla_guarantees={"uptime": 99.95, "support_response_hours": 1},
                customizations={"webhooks": True, "custom_branding": True, "dedicated_infrastructure": True}
            )
            
            self.logger.info(f"Initialized {len(self.tier_configurations)} tier configurations")
            
        except Exception as e:
            self.logger.error(f"Error initializing tier configurations: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for tier manager"""
        try:
            return {
                "status": "healthy",
                "service": "tier_manager",
                "features": len(self.features),
                "tier_configurations": len(self.tier_configurations),
                "usage_tracking_records": len(self.usage_tracking),
                "access_requests": len(self.access_requests),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "tier_manager",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_tier_manager() -> TierManager:
    """Create tier manager instance"""
    return TierManager()