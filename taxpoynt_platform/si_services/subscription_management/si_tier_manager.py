"""
SI Tier Manager - SI-specific subscription tier management

This module provides System Integrator specific tier management that integrates
with the existing billing orchestration system while providing SI-focused
features, limits, and access control.

Integrates with:
- hybrid_services/billing_orchestration/tier_manager.py
- core_platform/data_management/billing_repository.py  
- SI-specific services for tier enforcement
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

# Import existing platform services
from ...hybrid_services.billing_orchestration.tier_manager import TierManager, AccessDecision
from ...hybrid_services.billing_orchestration.subscription_manager import SubscriptionManager
from ...core_platform.data_management.billing_repository import (
    BillingRepository, SubscriptionTier, SubscriptionPlan
)
from ...core_platform.monitoring import MetricsCollector
from ...core_platform.data_management.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class SIFeatureCategory(str, Enum):
    """SI-specific feature categories"""
    ERP_INTEGRATION = "erp_integration"
    DOCUMENT_PROCESSING = "document_processing"
    CERTIFICATE_MANAGEMENT = "certificate_management"
    DATA_EXTRACTION = "data_extraction"
    IRN_GENERATION = "irn_generation"
    COMPLIANCE_REPORTING = "compliance_reporting"
    API_ACCESS = "api_access"
    SUPPORT_LEVEL = "support_level"
    CUSTOM_INTEGRATIONS = "custom_integrations"
    WHITE_LABEL = "white_label"


class SIUsageType(str, Enum):
    """SI-specific usage metrics"""
    INVOICES_PROCESSED = "invoices_processed"
    ERP_CONNECTIONS = "erp_connections"
    API_CALLS = "api_calls"
    STORAGE_USAGE = "storage_usage"
    USER_ACCOUNTS = "user_accounts"
    CERTIFICATE_REQUESTS = "certificate_requests"
    BULK_OPERATIONS = "bulk_operations"
    WEBHOOK_CALLS = "webhook_calls"
    SUPPORT_REQUESTS = "support_requests"


@dataclass
class SITierLimits:
    """SI-specific tier limits and quotas"""
    invoices_per_month: int
    users: int
    api_calls_per_minute: int
    storage_gb: int
    erp_connections: int
    certificate_requests_per_month: int
    bulk_operations_per_day: int
    webhook_calls_per_day: int
    support_requests_per_month: int
    concurrent_sessions: int


@dataclass
class SITierFeatures:
    """SI-specific tier features"""
    basic_erp_integration: bool = False
    advanced_erp_integration: bool = False
    multi_erp_support: bool = False
    custom_erp_connectors: bool = False
    
    standard_document_processing: bool = False
    advanced_document_processing: bool = False
    custom_document_templates: bool = False
    bulk_document_processing: bool = False
    
    basic_certificate_management: bool = False
    advanced_certificate_management: bool = False
    certificate_automation: bool = False
    
    basic_data_extraction: bool = False
    advanced_data_extraction: bool = False
    real_time_data_sync: bool = False
    custom_data_mappings: bool = False
    
    standard_irn_generation: bool = False
    bulk_irn_generation: bool = False
    priority_irn_processing: bool = False
    
    basic_reporting: bool = False
    advanced_analytics: bool = False
    custom_reports: bool = False
    real_time_dashboards: bool = False
    
    basic_api_access: bool = False
    advanced_api_access: bool = False
    webhook_support: bool = False
    api_rate_limits_extended: bool = False
    
    standard_support: bool = False
    priority_support: bool = False
    dedicated_support: bool = False
    support_24_7: bool = False
    
    custom_integrations: bool = False
    white_label: bool = False
    sla_guarantee: bool = False
    custom_deployment: bool = False


@dataclass
class SITierConfig:
    """Complete SI tier configuration"""
    tier: SubscriptionTier
    monthly_price: Decimal
    limits: SITierLimits
    features: SITierFeatures
    overage_rate: Decimal
    description: str
    popular: bool = False
    enterprise_contact: bool = False


class SITierManager:
    """
    SI-specific tier management that extends the platform tier manager
    with System Integrator focused features, limits, and business logic.
    """
    
    def __init__(
        self,
        tier_manager: TierManager,
        subscription_manager: SubscriptionManager,
        billing_repository: BillingRepository,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        config: Optional[Dict[str, Any]] = None
    ):
        self.tier_manager = tier_manager
        self.subscription_manager = subscription_manager
        self.billing_repository = billing_repository
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.config = config or {}
        
        # SI-specific tier definitions
        self.si_tier_definitions = self._load_si_tier_definitions()
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes
        self.enable_overage_billing = self.config.get("enable_overage_billing", True)
        self.grace_period_days = self.config.get("grace_period_days", 3)
    
    def _load_si_tier_definitions(self) -> Dict[SubscriptionTier, SITierConfig]:
        """Load SI subscription tier definitions matching the specified structure"""
        
        return {
            SubscriptionTier.STARTER: SITierConfig(
                tier=SubscriptionTier.STARTER,
                monthly_price=Decimal("50.00"),
                limits=SITierLimits(
                    invoices_per_month=1000,
                    users=5,
                    api_calls_per_minute=100,
                    storage_gb=10,
                    erp_connections=2,
                    certificate_requests_per_month=10,
                    bulk_operations_per_day=5,
                    webhook_calls_per_day=100,
                    support_requests_per_month=5,
                    concurrent_sessions=5
                ),
                features=SITierFeatures(
                    basic_erp_integration=True,
                    standard_document_processing=True,
                    basic_certificate_management=True,
                    basic_data_extraction=True,
                    standard_irn_generation=True,
                    basic_reporting=True,
                    basic_api_access=True,
                    standard_support=True
                ),
                overage_rate=Decimal("0.05"),  # $0.05 per extra invoice
                description="Perfect for small businesses getting started with e-invoicing",
                popular=True
            ),
            
            SubscriptionTier.PROFESSIONAL: SITierConfig(
                tier=SubscriptionTier.PROFESSIONAL,
                monthly_price=Decimal("200.00"),
                limits=SITierLimits(
                    invoices_per_month=10000,
                    users=25,
                    api_calls_per_minute=500,
                    storage_gb=100,
                    erp_connections=10,
                    certificate_requests_per_month=50,
                    bulk_operations_per_day=25,
                    webhook_calls_per_day=1000,
                    support_requests_per_month=20,
                    concurrent_sessions=25
                ),
                features=SITierFeatures(
                    basic_erp_integration=True,
                    advanced_erp_integration=True,
                    multi_erp_support=True,
                    standard_document_processing=True,
                    advanced_document_processing=True,
                    bulk_document_processing=True,
                    basic_certificate_management=True,
                    advanced_certificate_management=True,
                    basic_data_extraction=True,
                    advanced_data_extraction=True,
                    real_time_data_sync=True,
                    standard_irn_generation=True,
                    bulk_irn_generation=True,
                    basic_reporting=True,
                    advanced_analytics=True,
                    basic_api_access=True,
                    advanced_api_access=True,
                    webhook_support=True,
                    priority_support=True
                ),
                overage_rate=Decimal("0.02"),  # $0.02 per extra invoice
                description="Ideal for growing businesses with advanced integration needs",
                popular=True
            ),
            
            SubscriptionTier.ENTERPRISE: SITierConfig(
                tier=SubscriptionTier.ENTERPRISE,
                monthly_price=Decimal("800.00"),
                limits=SITierLimits(
                    invoices_per_month=100000,
                    users=100,
                    api_calls_per_minute=2000,
                    storage_gb=1000,
                    erp_connections=50,
                    certificate_requests_per_month=200,
                    bulk_operations_per_day=100,
                    webhook_calls_per_day=10000,
                    support_requests_per_month=100,
                    concurrent_sessions=100
                ),
                features=SITierFeatures(
                    basic_erp_integration=True,
                    advanced_erp_integration=True,
                    multi_erp_support=True,
                    custom_erp_connectors=True,
                    standard_document_processing=True,
                    advanced_document_processing=True,
                    custom_document_templates=True,
                    bulk_document_processing=True,
                    basic_certificate_management=True,
                    advanced_certificate_management=True,
                    certificate_automation=True,
                    basic_data_extraction=True,
                    advanced_data_extraction=True,
                    real_time_data_sync=True,
                    custom_data_mappings=True,
                    standard_irn_generation=True,
                    bulk_irn_generation=True,
                    priority_irn_processing=True,
                    basic_reporting=True,
                    advanced_analytics=True,
                    custom_reports=True,
                    real_time_dashboards=True,
                    basic_api_access=True,
                    advanced_api_access=True,
                    webhook_support=True,
                    api_rate_limits_extended=True,
                    dedicated_support=True,
                    custom_integrations=True,
                    white_label=True
                ),
                overage_rate=Decimal("0.008"),  # $0.008 per extra invoice
                description="Complete solution for large enterprises with complex requirements"
            ),
            
            SubscriptionTier.SCALE: SITierConfig(
                tier=SubscriptionTier.SCALE,
                monthly_price=Decimal("2000.00"),
                limits=SITierLimits(
                    invoices_per_month=1000000,
                    users=500,
                    api_calls_per_minute=10000,
                    storage_gb=5000,
                    erp_connections=200,
                    certificate_requests_per_month=1000,
                    bulk_operations_per_day=500,
                    webhook_calls_per_day=50000,
                    support_requests_per_month=500,
                    concurrent_sessions=500
                ),
                features=SITierFeatures(
                    # All features enabled
                    basic_erp_integration=True,
                    advanced_erp_integration=True,
                    multi_erp_support=True,
                    custom_erp_connectors=True,
                    standard_document_processing=True,
                    advanced_document_processing=True,
                    custom_document_templates=True,
                    bulk_document_processing=True,
                    basic_certificate_management=True,
                    advanced_certificate_management=True,
                    certificate_automation=True,
                    basic_data_extraction=True,
                    advanced_data_extraction=True,
                    real_time_data_sync=True,
                    custom_data_mappings=True,
                    standard_irn_generation=True,
                    bulk_irn_generation=True,
                    priority_irn_processing=True,
                    basic_reporting=True,
                    advanced_analytics=True,
                    custom_reports=True,
                    real_time_dashboards=True,
                    basic_api_access=True,
                    advanced_api_access=True,
                    webhook_support=True,
                    api_rate_limits_extended=True,
                    support_24_7=True,
                    custom_integrations=True,
                    white_label=True,
                    sla_guarantee=True,
                    custom_deployment=True
                ),
                overage_rate=Decimal("0.002"),  # $0.002 per extra invoice
                description="Enterprise-scale solution with unlimited capabilities and 24/7 support",
                enterprise_contact=True
            )
        }
    
    async def get_si_tier_config(self, tier: SubscriptionTier) -> Optional[SITierConfig]:
        """Get SI tier configuration for a specific tier"""
        return self.si_tier_definitions.get(tier)
    
    async def get_organization_si_tier(self, organization_id: str) -> Optional[SITierConfig]:
        """Get SI tier configuration for an organization"""
        try:
            # Check cache first
            cache_key = f"si_tier:{organization_id}"
            cached_tier = await self.cache_manager.get(cache_key)
            if cached_tier:
                tier = SubscriptionTier(cached_tier)
                return await self.get_si_tier_config(tier)
            
            # Get subscription from subscription manager
            subscription = await self.subscription_manager.get_organization_subscription(
                organization_id
            )
            
            if not subscription:
                return None
            
            tier_config = await self.get_si_tier_config(subscription.tier)
            
            # Cache the tier
            await self.cache_manager.set(
                cache_key, 
                subscription.tier.value,
                ttl=self.cache_ttl
            )
            
            return tier_config
            
        except Exception as e:
            logger.error(f"Error getting SI tier for organization {organization_id}: {e}")
            return None
    
    async def check_si_feature_access(
        self,
        organization_id: str,
        feature: SIFeatureCategory,
        required_feature_name: str
    ) -> AccessDecision:
        """Check if organization has access to specific SI feature"""
        try:
            tier_config = await self.get_organization_si_tier(organization_id)
            
            if not tier_config:
                return AccessDecision.DENIED
            
            # Check if feature is enabled in tier
            feature_enabled = getattr(tier_config.features, required_feature_name, False)
            
            if feature_enabled:
                return AccessDecision.GRANTED
            else:
                return AccessDecision.UPGRADE_REQUIRED
                
        except Exception as e:
            logger.error(f"Error checking SI feature access for {organization_id}: {e}")
            return AccessDecision.DENIED
    
    async def check_si_usage_limits(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        requested_amount: int = 1
    ) -> Dict[str, Any]:
        """Check SI usage limits for an organization"""
        try:
            tier_config = await self.get_organization_si_tier(organization_id)
            
            if not tier_config:
                return {
                    "allowed": False,
                    "reason": "No valid subscription found",
                    "limit": 0,
                    "current_usage": 0,
                    "remaining": 0
                }
            
            # Get current usage from usage tracker
            current_usage = await self._get_current_usage(organization_id, usage_type)
            
            # Get limit from tier config
            limit = self._get_usage_limit(tier_config.limits, usage_type)
            
            # Check if request would exceed limit
            projected_usage = current_usage + requested_amount
            allowed = projected_usage <= limit
            remaining = max(0, limit - current_usage)
            
            # Handle overage billing if enabled
            overage_cost = None
            if not allowed and self.enable_overage_billing and usage_type == SIUsageType.INVOICES_PROCESSED:
                overage_amount = projected_usage - limit
                overage_cost = overage_amount * tier_config.overage_rate
                allowed = True  # Allow with overage billing
            
            return {
                "allowed": allowed,
                "reason": "Within limits" if allowed else "Usage limit exceeded",
                "limit": limit,
                "current_usage": current_usage,
                "remaining": remaining,
                "overage_cost": overage_cost
            }
            
        except Exception as e:
            logger.error(f"Error checking SI usage limits for {organization_id}: {e}")
            return {
                "allowed": False,
                "reason": f"Error checking limits: {str(e)}",
                "limit": 0,
                "current_usage": 0,
                "remaining": 0
            }
    
    async def get_si_tier_comparison(self) -> Dict[str, Any]:
        """Get comparison of all SI tiers for pricing page"""
        comparison = {}
        
        for tier, config in self.si_tier_definitions.items():
            comparison[tier.value] = {
                "name": tier.value.title(),
                "monthly_price": float(config.monthly_price),
                "description": config.description,
                "popular": config.popular,
                "enterprise_contact": config.enterprise_contact,
                "limits": asdict(config.limits),
                "features": asdict(config.features),
                "overage_rate": float(config.overage_rate)
            }
        
        return comparison
    
    async def get_upgrade_recommendations(
        self,
        organization_id: str,
        current_usage: Dict[SIUsageType, int]
    ) -> Optional[Dict[str, Any]]:
        """Get upgrade recommendations based on usage patterns"""
        try:
            current_tier_config = await self.get_organization_si_tier(organization_id)
            
            if not current_tier_config:
                return None
            
            # Find next tier that would accommodate usage
            tier_hierarchy = [
                SubscriptionTier.STARTER,
                SubscriptionTier.PROFESSIONAL, 
                SubscriptionTier.ENTERPRISE,
                SubscriptionTier.SCALE
            ]
            
            current_tier_index = tier_hierarchy.index(current_tier_config.tier)
            
            for next_tier in tier_hierarchy[current_tier_index + 1:]:
                next_tier_config = await self.get_si_tier_config(next_tier)
                
                if self._tier_accommodates_usage(next_tier_config.limits, current_usage):
                    savings = self._calculate_upgrade_savings(
                        current_tier_config, next_tier_config, current_usage
                    )
                    
                    return {
                        "recommended_tier": next_tier.value,
                        "current_tier": current_tier_config.tier.value,
                        "monthly_savings": savings,
                        "new_monthly_cost": float(next_tier_config.monthly_price),
                        "usage_violations": self._get_usage_violations(
                            current_tier_config.limits, current_usage
                        ),
                        "new_features": self._get_new_features(
                            current_tier_config.features, next_tier_config.features
                        )
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting upgrade recommendations for {organization_id}: {e}")
            return None
    
    async def _get_current_usage(self, organization_id: str, usage_type: SIUsageType) -> int:
        """Get current usage for organization and usage type"""
        # This would integrate with the usage tracking system
        # For now, return 0 as placeholder
        return 0
    
    def _get_usage_limit(self, limits: SITierLimits, usage_type: SIUsageType) -> int:
        """Get usage limit for specific usage type from tier limits"""
        usage_mapping = {
            SIUsageType.INVOICES_PROCESSED: limits.invoices_per_month,
            SIUsageType.API_CALLS: limits.api_calls_per_minute,
            SIUsageType.STORAGE_USAGE: limits.storage_gb,
            SIUsageType.USER_ACCOUNTS: limits.users,
            SIUsageType.ERP_CONNECTIONS: limits.erp_connections,
            SIUsageType.CERTIFICATE_REQUESTS: limits.certificate_requests_per_month,
            SIUsageType.BULK_OPERATIONS: limits.bulk_operations_per_day,
            SIUsageType.WEBHOOK_CALLS: limits.webhook_calls_per_day,
            SIUsageType.SUPPORT_REQUESTS: limits.support_requests_per_month
        }
        
        return usage_mapping.get(usage_type, 0)
    
    def _tier_accommodates_usage(
        self, 
        tier_limits: SITierLimits, 
        usage: Dict[SIUsageType, int]
    ) -> bool:
        """Check if tier limits can accommodate usage"""
        for usage_type, amount in usage.items():
            limit = self._get_usage_limit(tier_limits, usage_type)
            if amount > limit:
                return False
        return True
    
    def _calculate_upgrade_savings(
        self,
        current_tier: SITierConfig,
        next_tier: SITierConfig,
        usage: Dict[SIUsageType, int]
    ) -> float:
        """Calculate potential savings from upgrade vs overage costs"""
        # Calculate overage costs with current tier
        overage_costs = 0
        invoice_usage = usage.get(SIUsageType.INVOICES_PROCESSED, 0)
        if invoice_usage > current_tier.limits.invoices_per_month:
            overage_amount = invoice_usage - current_tier.limits.invoices_per_month
            overage_costs = float(overage_amount * current_tier.overage_rate)
        
        # Calculate net cost difference
        current_monthly_cost = float(current_tier.monthly_price) + overage_costs
        new_monthly_cost = float(next_tier.monthly_price)
        
        return current_monthly_cost - new_monthly_cost
    
    def _get_usage_violations(
        self,
        limits: SITierLimits,
        usage: Dict[SIUsageType, int]
    ) -> List[str]:
        """Get list of usage violations"""
        violations = []
        
        for usage_type, amount in usage.items():
            limit = self._get_usage_limit(limits, usage_type)
            if amount > limit:
                violations.append(f"{usage_type.value}: {amount} exceeds limit of {limit}")
        
        return violations
    
    def _get_new_features(
        self,
        current_features: SITierFeatures,
        new_features: SITierFeatures
    ) -> List[str]:
        """Get list of new features available in upgraded tier"""
        new_feature_list = []
        
        for feature_name in dir(new_features):
            if not feature_name.startswith('_'):
                current_value = getattr(current_features, feature_name, False)
                new_value = getattr(new_features, feature_name, False)
                
                if not current_value and new_value:
                    new_feature_list.append(feature_name.replace('_', ' ').title())
        
        return new_feature_list