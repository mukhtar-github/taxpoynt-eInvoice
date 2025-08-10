"""
SI Tier Validator - Validation and enforcement for SI services

This module provides validation and enforcement of SI subscription tiers
across all SI services, ensuring proper access control and usage compliance.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .si_tier_manager import SITierManager, SIFeatureCategory, SIUsageType
from ...hybrid_services.service_access_control.subscription_guard import SubscriptionGuard
from ...core_platform.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class SIValidationResult(str, Enum):
    """SI tier validation results"""
    VALID = "valid"
    TIER_INSUFFICIENT = "tier_insufficient"
    USAGE_EXCEEDED = "usage_exceeded"
    FEATURE_RESTRICTED = "feature_restricted"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    PAYMENT_REQUIRED = "payment_required"


@dataclass
class SIValidationResponse:
    """Response from SI tier validation"""
    organization_id: str
    validation_result: SIValidationResult
    allowed: bool
    reason: str
    current_tier: Optional[str] = None
    required_tier: Optional[str] = None
    usage_info: Optional[Dict[str, Any]] = None
    recommended_action: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SITierValidator:
    """
    Validates SI tier access and enforces subscription compliance
    for all SI service operations.
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        subscription_guard: SubscriptionGuard,
        metrics_collector: MetricsCollector,
        config: Optional[Dict[str, Any]] = None
    ):
        self.si_tier_manager = si_tier_manager
        self.subscription_guard = subscription_guard
        self.metrics_collector = metrics_collector
        self.config = config or {}
        
        # SI service feature mappings
        self.service_feature_map = self._load_service_feature_mappings()
    
    def _load_service_feature_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings between SI services and required tier features"""
        return {
            # ERP Integration Services
            "erp_basic_connection": {
                "feature": "basic_erp_integration",
                "usage_type": SIUsageType.ERP_CONNECTIONS,
                "min_tier": "starter"
            },
            "erp_advanced_integration": {
                "feature": "advanced_erp_integration", 
                "usage_type": SIUsageType.ERP_CONNECTIONS,
                "min_tier": "professional"
            },
            "multi_erp_support": {
                "feature": "multi_erp_support",
                "usage_type": SIUsageType.ERP_CONNECTIONS,
                "min_tier": "professional"
            },
            "custom_erp_connectors": {
                "feature": "custom_erp_connectors",
                "usage_type": SIUsageType.ERP_CONNECTIONS,
                "min_tier": "enterprise"
            },
            
            # Document Processing Services
            "document_basic_processing": {
                "feature": "standard_document_processing",
                "usage_type": SIUsageType.INVOICES_PROCESSED,
                "min_tier": "starter"
            },
            "document_advanced_processing": {
                "feature": "advanced_document_processing",
                "usage_type": SIUsageType.INVOICES_PROCESSED,
                "min_tier": "professional"
            },
            "bulk_document_processing": {
                "feature": "bulk_document_processing",
                "usage_type": SIUsageType.BULK_OPERATIONS,
                "min_tier": "professional"
            },
            "custom_document_templates": {
                "feature": "custom_document_templates",
                "usage_type": SIUsageType.INVOICES_PROCESSED,
                "min_tier": "enterprise"
            },
            
            # Certificate Management Services
            "certificate_basic_management": {
                "feature": "basic_certificate_management",
                "usage_type": SIUsageType.CERTIFICATE_REQUESTS,
                "min_tier": "starter"
            },
            "certificate_advanced_management": {
                "feature": "advanced_certificate_management",
                "usage_type": SIUsageType.CERTIFICATE_REQUESTS,
                "min_tier": "professional"
            },
            "certificate_automation": {
                "feature": "certificate_automation",
                "usage_type": SIUsageType.CERTIFICATE_REQUESTS,
                "min_tier": "enterprise"
            },
            
            # Data Extraction Services
            "data_basic_extraction": {
                "feature": "basic_data_extraction",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "starter"
            },
            "data_advanced_extraction": {
                "feature": "advanced_data_extraction",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "professional"
            },
            "real_time_data_sync": {
                "feature": "real_time_data_sync",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "professional"
            },
            "custom_data_mappings": {
                "feature": "custom_data_mappings",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            
            # IRN Generation Services
            "irn_standard_generation": {
                "feature": "standard_irn_generation",
                "usage_type": SIUsageType.INVOICES_PROCESSED,
                "min_tier": "starter"
            },
            "irn_bulk_generation": {
                "feature": "bulk_irn_generation",
                "usage_type": SIUsageType.BULK_OPERATIONS,
                "min_tier": "professional"
            },
            "irn_priority_processing": {
                "feature": "priority_irn_processing",
                "usage_type": SIUsageType.INVOICES_PROCESSED,
                "min_tier": "enterprise"
            },
            
            # Reporting Services
            "reporting_basic": {
                "feature": "basic_reporting",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "starter"
            },
            "analytics_advanced": {
                "feature": "advanced_analytics",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "professional"
            },
            "reports_custom": {
                "feature": "custom_reports",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            "dashboards_real_time": {
                "feature": "real_time_dashboards",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            
            # API Access Services
            "api_basic_access": {
                "feature": "basic_api_access",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "starter"
            },
            "api_advanced_access": {
                "feature": "advanced_api_access",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "professional"
            },
            "webhook_support": {
                "feature": "webhook_support",
                "usage_type": SIUsageType.WEBHOOK_CALLS,
                "min_tier": "professional"
            },
            "api_extended_limits": {
                "feature": "api_rate_limits_extended",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            
            # Support Services
            "support_standard": {
                "feature": "standard_support",
                "usage_type": SIUsageType.SUPPORT_REQUESTS,
                "min_tier": "starter"
            },
            "support_priority": {
                "feature": "priority_support",
                "usage_type": SIUsageType.SUPPORT_REQUESTS,
                "min_tier": "professional"
            },
            "support_dedicated": {
                "feature": "dedicated_support",
                "usage_type": SIUsageType.SUPPORT_REQUESTS,
                "min_tier": "enterprise"
            },
            "support_24_7": {
                "feature": "support_24_7",
                "usage_type": SIUsageType.SUPPORT_REQUESTS,
                "min_tier": "scale"
            },
            
            # Enterprise Features
            "custom_integrations": {
                "feature": "custom_integrations",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            "white_label": {
                "feature": "white_label",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "enterprise"
            },
            "sla_guarantee": {
                "feature": "sla_guarantee",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "scale"
            },
            "custom_deployment": {
                "feature": "custom_deployment",
                "usage_type": SIUsageType.API_CALLS,
                "min_tier": "scale"
            }
        }
    
    async def validate_si_service_access(
        self,
        organization_id: str,
        service_name: str,
        usage_amount: int = 1
    ) -> SIValidationResponse:
        """Validate access to specific SI service"""
        try:
            # First check basic subscription validity
            subscription_validation = await self.subscription_guard.validate_subscription(
                organization_id
            )
            
            if not subscription_validation.allowed:
                return SIValidationResponse(
                    organization_id=organization_id,
                    validation_result=SIValidationResult.SUBSCRIPTION_EXPIRED,
                    allowed=False,
                    reason=subscription_validation.reason,
                    recommended_action=subscription_validation.recommended_action
                )
            
            # Get service requirements
            service_config = self.service_feature_map.get(service_name)
            if not service_config:
                # Unknown service, allow by default but log
                logger.warning(f"Unknown SI service: {service_name}")
                return SIValidationResponse(
                    organization_id=organization_id,
                    validation_result=SIValidationResult.VALID,
                    allowed=True,
                    reason="Unknown service - allowed by default"
                )
            
            # Get organization's tier config
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            if not tier_config:
                return SIValidationResponse(
                    organization_id=organization_id,
                    validation_result=SIValidationResult.SUBSCRIPTION_EXPIRED,
                    allowed=False,
                    reason="No valid SI subscription found",
                    recommended_action="Subscribe to an SI plan"
                )
            
            # Check feature access
            feature_name = service_config["feature"]
            feature_enabled = getattr(tier_config.features, feature_name, False)
            
            if not feature_enabled:
                return SIValidationResponse(
                    organization_id=organization_id,
                    validation_result=SIValidationResult.FEATURE_RESTRICTED,
                    allowed=False,
                    reason=f"Feature '{feature_name}' not available in {tier_config.tier.value} tier",
                    current_tier=tier_config.tier.value,
                    required_tier=service_config["min_tier"],
                    recommended_action=f"Upgrade to {service_config['min_tier']} or higher"
                )
            
            # Check usage limits
            usage_type = service_config["usage_type"]
            usage_check = await self.si_tier_manager.check_si_usage_limits(
                organization_id, usage_type, usage_amount
            )
            
            if not usage_check["allowed"]:
                return SIValidationResponse(
                    organization_id=organization_id,
                    validation_result=SIValidationResult.USAGE_EXCEEDED,
                    allowed=False,
                    reason=usage_check["reason"],
                    current_tier=tier_config.tier.value,
                    usage_info=usage_check,
                    recommended_action="Upgrade tier or wait for usage reset" if not usage_check.get("overage_cost") else "Overage charges will apply"
                )
            
            # All checks passed
            return SIValidationResponse(
                organization_id=organization_id,
                validation_result=SIValidationResult.VALID,
                allowed=True,
                reason="Access granted",
                current_tier=tier_config.tier.value,
                usage_info=usage_check
            )
            
        except Exception as e:
            logger.error(f"Error validating SI service access for {organization_id}: {e}")
            return SIValidationResponse(
                organization_id=organization_id,
                validation_result=SIValidationResult.TIER_INSUFFICIENT,
                allowed=False,
                reason=f"Validation error: {str(e)}"
            )
    
    async def validate_bulk_operation(
        self,
        organization_id: str,
        operation_type: str,
        item_count: int
    ) -> SIValidationResponse:
        """Validate bulk operation with special considerations"""
        
        # Map operation types to service names
        operation_service_map = {
            "bulk_invoice_processing": "bulk_document_processing",
            "bulk_irn_generation": "irn_bulk_generation",
            "bulk_data_extraction": "data_advanced_extraction",
            "bulk_certificate_requests": "certificate_advanced_management"
        }
        
        service_name = operation_service_map.get(operation_type, operation_type)
        
        # Validate with item count as usage amount
        validation = await self.validate_si_service_access(
            organization_id, service_name, item_count
        )
        
        # Add bulk-specific metadata
        if validation.allowed:
            validation.metadata.update({
                "operation_type": operation_type,
                "item_count": item_count,
                "estimated_completion": self._estimate_bulk_completion_time(item_count),
                "priority_processing": self._check_priority_processing(organization_id)
            })
        
        return validation
    
    async def validate_api_access(
        self,
        organization_id: str,
        endpoint: str,
        rate_limit_window: str = "minute"
    ) -> SIValidationResponse:
        """Validate API access with rate limiting considerations"""
        
        # Determine service type based on endpoint
        if "/erp/" in endpoint:
            service_name = "api_advanced_access" if "/advanced" in endpoint else "api_basic_access"
        elif "/webhook/" in endpoint:
            service_name = "webhook_support"
        elif "/bulk/" in endpoint:
            service_name = "api_advanced_access"
        else:
            service_name = "api_basic_access"
        
        validation = await self.validate_si_service_access(organization_id, service_name)
        
        if validation.allowed:
            # Add API-specific rate limit info
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            if tier_config:
                rate_limit = tier_config.limits.api_calls_per_minute
                validation.metadata.update({
                    "rate_limit": rate_limit,
                    "rate_limit_window": rate_limit_window,
                    "extended_limits": tier_config.features.api_rate_limits_extended
                })
        
        return validation
    
    async def get_feature_availability(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get complete feature availability for organization"""
        try:
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            
            if not tier_config:
                return {
                    "error": "No valid subscription found",
                    "features": {},
                    "limits": {}
                }
            
            # Get all available features
            available_features = {}
            for service_name, service_config in self.service_feature_map.items():
                feature_name = service_config["feature"]
                available_features[service_name] = {
                    "available": getattr(tier_config.features, feature_name, False),
                    "feature_name": feature_name,
                    "min_tier_required": service_config["min_tier"],
                    "usage_type": service_config["usage_type"].value
                }
            
            # Get current usage information
            usage_info = {}
            for usage_type in SIUsageType:
                usage_check = await self.si_tier_manager.check_si_usage_limits(
                    organization_id, usage_type, 0
                )
                usage_info[usage_type.value] = usage_check
            
            return {
                "tier": tier_config.tier.value,
                "features": available_features,
                "limits": asdict(tier_config.limits),
                "usage": usage_info,
                "overage_rate": float(tier_config.overage_rate)
            }
            
        except Exception as e:
            logger.error(f"Error getting feature availability for {organization_id}: {e}")
            return {
                "error": f"Error retrieving features: {str(e)}",
                "features": {},
                "limits": {}
            }
    
    def _estimate_bulk_completion_time(self, item_count: int) -> str:
        """Estimate completion time for bulk operations"""
        # Rough estimate: 100 items per minute
        minutes = max(1, item_count // 100)
        
        if minutes < 60:
            return f"~{minutes} minutes"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"~{hours}h {remaining_minutes}m"
    
    async def _check_priority_processing(self, organization_id: str) -> bool:
        """Check if organization has priority processing"""
        tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
        if not tier_config:
            return False
        
        return (
            tier_config.features.priority_irn_processing or
            tier_config.features.priority_support or
            tier_config.tier.value in ["enterprise", "scale"]
        )


# Decorator for SI service validation

def require_si_tier(service_name: str, usage_amount: int = 1):
    """
    Decorator to enforce SI tier validation on service methods
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract organization_id from function parameters
            organization_id = None
            
            # Look for organization_id in kwargs first
            if "organization_id" in kwargs:
                organization_id = kwargs["organization_id"]
            else:
                # Look for it in args (assuming it's a method with self as first arg)
                for arg in args[1:]:  # Skip 'self'
                    if isinstance(arg, str) and len(arg) > 10:  # Rough UUID check
                        organization_id = arg
                        break
            
            if not organization_id:
                raise ValueError("Organization ID not found for SI tier validation")
            
            # Get validator from dependency injection or create one
            # This would typically be injected via FastAPI dependencies
            validator = getattr(args[0], '_si_tier_validator', None)
            if not validator:
                raise ValueError("SI tier validator not available")
            
            # Validate access
            validation = await validator.validate_si_service_access(
                organization_id, service_name, usage_amount
            )
            
            if not validation.allowed:
                from fastapi import HTTPException
                
                status_code = 403
                if validation.validation_result == SIValidationResult.SUBSCRIPTION_EXPIRED:
                    status_code = 402
                elif validation.validation_result == SIValidationResult.USAGE_EXCEEDED:
                    status_code = 429
                
                raise HTTPException(
                    status_code=status_code,
                    detail=f"SI tier validation failed: {validation.reason}",
                    headers={"X-Required-Tier": validation.required_tier} if validation.required_tier else {}
                )
            
            # Store validation result for potential logging/monitoring
            if hasattr(args[0], '_last_validation'):
                args[0]._last_validation = validation
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator