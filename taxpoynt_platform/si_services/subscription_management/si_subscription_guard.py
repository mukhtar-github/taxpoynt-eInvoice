"""
SI Subscription Guard - SI-specific subscription enforcement

This module provides SI-focused subscription compliance and enforcement,
integrating with the platform subscription guard while adding SI-specific
business logic and service protection.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

from .si_tier_manager import SITierManager, SITierConfig
from .si_tier_validator import SITierValidator, SIValidationResult
from .si_usage_tracker import SIUsageTracker, SIUsageType
from ...hybrid_services.service_access_control.subscription_guard import SubscriptionGuard
from ...core_platform.monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class SIAccessDecision(str, Enum):
    """SI-specific access decisions"""
    GRANTED = "granted"
    DENIED = "denied"
    TIER_UPGRADE_REQUIRED = "tier_upgrade_required"
    USAGE_LIMIT_EXCEEDED = "usage_limit_exceeded"
    FEATURE_NOT_AVAILABLE = "feature_not_available"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    PAYMENT_OVERDUE = "payment_overdue"
    TRIAL_EXPIRED = "trial_expired"
    SUSPENDED = "suspended"
    OVERAGE_BILLING_APPLIED = "overage_billing_applied"


@dataclass
class SIAccessRequest:
    """SI service access request"""
    request_id: str
    organization_id: str
    service_name: str
    operation_type: str
    requested_resources: Dict[str, int]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_info: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)
        if self.client_info is None:
            self.client_info = {}


@dataclass
class SIAccessResponse:
    """SI service access response"""
    request_id: str
    organization_id: str
    decision: SIAccessDecision
    allowed: bool
    reason: str
    current_tier: Optional[str] = None
    required_tier: Optional[str] = None
    usage_info: Dict[str, Any] = None
    overage_cost: Optional[float] = None
    retry_after: Optional[datetime] = None
    recommended_actions: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.usage_info is None:
            self.usage_info = {}
        if self.recommended_actions is None:
            self.recommended_actions = []
        if self.metadata is None:
            self.metadata = {}


class SISubscriptionGuard:
    """
    Comprehensive SI subscription enforcement that protects SI services
    with subscription-aware access control, usage enforcement, and
    intelligent billing compliance.
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        si_tier_validator: SITierValidator,
        si_usage_tracker: SIUsageTracker,
        subscription_guard: SubscriptionGuard,
        metrics_collector: MetricsCollector,
        config: Optional[Dict[str, Any]] = None
    ):
        self.si_tier_manager = si_tier_manager
        self.si_tier_validator = si_tier_validator
        self.si_usage_tracker = si_usage_tracker
        self.subscription_guard = subscription_guard
        self.metrics_collector = metrics_collector
        self.config = config or {}
        
        # Configuration
        self.enable_overage_billing = self.config.get("enable_overage_billing", True)
        self.grace_period_hours = self.config.get("grace_period_hours", 24)
        self.trial_extension_days = self.config.get("trial_extension_days", 7)
        self.enable_soft_limits = self.config.get("enable_soft_limits", True)
        
        # Service operation mappings
        self.operation_mappings = self._load_operation_mappings()
    
    def _load_operation_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings between operations and resource requirements"""
        return {
            # ERP Integration Operations
            "erp_connect": {
                "usage_types": [SIUsageType.ERP_CONNECTIONS],
                "usage_amounts": [1],
                "service_validation": "erp_basic_connection"
            },
            "erp_sync_data": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [1],
                "service_validation": "erp_advanced_integration"
            },
            "erp_bulk_sync": {
                "usage_types": [SIUsageType.BULK_OPERATIONS, SIUsageType.API_CALLS],
                "usage_amounts": [1, 10],
                "service_validation": "bulk_document_processing"
            },
            
            # Document Processing Operations
            "process_invoice": {
                "usage_types": [SIUsageType.INVOICES_PROCESSED],
                "usage_amounts": [1],
                "service_validation": "document_basic_processing"
            },
            "process_bulk_invoices": {
                "usage_types": [SIUsageType.INVOICES_PROCESSED, SIUsageType.BULK_OPERATIONS],
                "usage_amounts": [1, 1],
                "service_validation": "bulk_document_processing"
            },
            "generate_custom_template": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [1],
                "service_validation": "custom_document_templates"
            },
            
            # Certificate Operations
            "request_certificate": {
                "usage_types": [SIUsageType.CERTIFICATE_REQUESTS],
                "usage_amounts": [1],
                "service_validation": "certificate_basic_management"
            },
            "automate_certificate_renewal": {
                "usage_types": [SIUsageType.CERTIFICATE_REQUESTS],
                "usage_amounts": [1],
                "service_validation": "certificate_automation"
            },
            
            # IRN Generation Operations
            "generate_irn": {
                "usage_types": [SIUsageType.INVOICES_PROCESSED],
                "usage_amounts": [1],
                "service_validation": "irn_standard_generation"
            },
            "generate_bulk_irn": {
                "usage_types": [SIUsageType.INVOICES_PROCESSED, SIUsageType.BULK_OPERATIONS],
                "usage_amounts": [1, 1],
                "service_validation": "irn_bulk_generation"
            },
            "priority_irn_processing": {
                "usage_types": [SIUsageType.INVOICES_PROCESSED],
                "usage_amounts": [1],
                "service_validation": "irn_priority_processing"
            },
            
            # Data Extraction Operations
            "extract_data": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [1],
                "service_validation": "data_basic_extraction"
            },
            "real_time_sync": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [2],
                "service_validation": "real_time_data_sync"
            },
            "custom_data_mapping": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [1],
                "service_validation": "custom_data_mappings"
            },
            
            # API Operations
            "api_call": {
                "usage_types": [SIUsageType.API_CALLS],
                "usage_amounts": [1],
                "service_validation": "api_basic_access"
            },
            "webhook_send": {
                "usage_types": [SIUsageType.WEBHOOK_CALLS],
                "usage_amounts": [1],
                "service_validation": "webhook_support"
            },
            
            # Support Operations
            "create_support_request": {
                "usage_types": [SIUsageType.SUPPORT_REQUESTS],
                "usage_amounts": [1],
                "service_validation": "support_standard"
            },
            
            # Storage Operations
            "store_data": {
                "usage_types": [SIUsageType.STORAGE_USAGE],
                "usage_amounts": [1],  # 1 MB
                "service_validation": "api_basic_access"
            }
        }
    
    async def validate_si_access(
        self,
        access_request: SIAccessRequest
    ) -> SIAccessResponse:
        """
        Comprehensive SI access validation with subscription compliance,
        usage enforcement, and intelligent billing decisions.
        """
        try:
            request_id = access_request.request_id
            organization_id = access_request.organization_id
            operation_type = access_request.operation_type
            
            # Step 1: Basic subscription validation
            subscription_validation = await self.subscription_guard.validate_subscription(
                organization_id
            )
            
            if not subscription_validation.allowed:
                return SIAccessResponse(
                    request_id=request_id,
                    organization_id=organization_id,
                    decision=self._map_subscription_decision(subscription_validation.validation_result),
                    allowed=False,
                    reason=subscription_validation.reason,
                    recommended_actions=[subscription_validation.recommended_action] if subscription_validation.recommended_action else []
                )
            
            # Step 2: Get operation requirements
            operation_config = self.operation_mappings.get(operation_type)
            if not operation_config:
                # Unknown operation, perform basic validation
                return await self._validate_unknown_operation(access_request)
            
            # Step 3: Validate SI service access
            service_validation = await self.si_tier_validator.validate_si_service_access(
                organization_id,
                operation_config["service_validation"],
                1  # Basic validation
            )
            
            if not service_validation.allowed:
                return SIAccessResponse(
                    request_id=request_id,
                    organization_id=organization_id,
                    decision=self._map_validation_decision(service_validation.validation_result),
                    allowed=False,
                    reason=service_validation.reason,
                    current_tier=service_validation.current_tier,
                    required_tier=service_validation.required_tier,
                    recommended_actions=["Upgrade subscription tier to access this feature"]
                )
            
            # Step 4: Check usage limits for all required resources
            usage_validations = await self._validate_usage_requirements(
                organization_id, operation_config, access_request.requested_resources
            )
            
            # Step 5: Make final access decision
            final_decision = await self._make_final_decision(
                access_request, service_validation, usage_validations
            )
            
            # Step 6: Record usage if allowed
            if final_decision.allowed:
                await self._record_operation_usage(
                    organization_id, operation_config, access_request.requested_resources
                )
            
            # Step 7: Record metrics
            await self._record_access_metrics(access_request, final_decision)
            
            return final_decision
            
        except Exception as e:
            logger.error(f"Error validating SI access for {access_request.organization_id}: {e}")
            return SIAccessResponse(
                request_id=access_request.request_id,
                organization_id=access_request.organization_id,
                decision=SIAccessDecision.DENIED,
                allowed=False,
                reason=f"Validation error: {str(e)}"
            )
    
    async def check_operation_feasibility(
        self,
        organization_id: str,
        operation_type: str,
        estimated_resources: Dict[str, int]
    ) -> Dict[str, Any]:
        """Check if operation is feasible given current subscription and usage"""
        try:
            operation_config = self.operation_mappings.get(operation_type)
            if not operation_config:
                return {
                    "feasible": True,
                    "reason": "Unknown operation type - allowed by default"
                }
            
            # Get tier configuration
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            if not tier_config:
                return {
                    "feasible": False,
                    "reason": "No valid subscription found"
                }
            
            # Check each usage requirement
            feasibility_checks = {}
            total_overage_cost = 0.0
            
            usage_types = operation_config.get("usage_types", [])
            usage_amounts = operation_config.get("usage_amounts", [])
            
            for i, usage_type in enumerate(usage_types):
                amount = usage_amounts[i] if i < len(usage_amounts) else 1
                
                # Apply resource multiplier if specified
                if usage_type.value in estimated_resources:
                    amount *= estimated_resources[usage_type.value]
                
                usage_check = await self.si_tier_manager.check_si_usage_limits(
                    organization_id, usage_type, amount
                )
                
                feasibility_checks[usage_type.value] = {
                    "current_usage": usage_check.get("current_usage", 0),
                    "limit": usage_check.get("limit", 0),
                    "requested": amount,
                    "allowed": usage_check.get("allowed", False),
                    "overage_cost": usage_check.get("overage_cost", 0)
                }
                
                if usage_check.get("overage_cost"):
                    total_overage_cost += float(usage_check["overage_cost"])
            
            # Determine overall feasibility
            all_allowed = all(check["allowed"] for check in feasibility_checks.values())
            
            return {
                "feasible": all_allowed,
                "reason": "Operation feasible" if all_allowed else "Usage limits exceeded",
                "usage_checks": feasibility_checks,
                "total_overage_cost": total_overage_cost,
                "tier": tier_config.tier.value,
                "recommendations": self._generate_feasibility_recommendations(
                    tier_config, feasibility_checks, total_overage_cost
                )
            }
            
        except Exception as e:
            logger.error(f"Error checking operation feasibility: {e}")
            return {
                "feasible": False,
                "reason": f"Feasibility check error: {str(e)}"
            }
    
    async def get_access_summary(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive access summary for organization"""
        try:
            # Get subscription status
            subscription_validation = await self.subscription_guard.validate_subscription(
                organization_id
            )
            
            # Get tier configuration
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            
            # Get current usage
            current_usage = await self.si_usage_tracker.get_current_usage(organization_id)
            
            # Get feature availability
            feature_availability = await self.si_tier_validator.get_feature_availability(
                organization_id
            )
            
            # Get usage analytics
            usage_analytics = await self.si_usage_tracker.get_usage_analytics(
                organization_id
            )
            
            # Check operation feasibility for common operations
            common_operations = [
                "process_invoice", "generate_irn", "erp_sync_data", 
                "api_call", "request_certificate"
            ]
            
            operation_feasibility = {}
            for operation in common_operations:
                feasibility = await self.check_operation_feasibility(
                    organization_id, operation, {}
                )
                operation_feasibility[operation] = feasibility
            
            return {
                "subscription_status": {
                    "valid": subscription_validation.allowed,
                    "reason": subscription_validation.reason,
                    "tier": tier_config.tier.value if tier_config else None,
                    "expires_at": subscription_validation.subscription_info.expires_at.isoformat() if subscription_validation.subscription_info and subscription_validation.subscription_info.expires_at else None
                },
                "current_usage": current_usage,
                "feature_availability": feature_availability,
                "usage_analytics": usage_analytics,
                "operation_feasibility": operation_feasibility,
                "recommendations": self._generate_access_recommendations(
                    subscription_validation, tier_config, usage_analytics
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting access summary for {organization_id}: {e}")
            return {
                "error": f"Access summary error: {str(e)}"
            }
    
    async def _validate_unknown_operation(
        self,
        access_request: SIAccessRequest
    ) -> SIAccessResponse:
        """Handle validation for unknown operations"""
        logger.warning(f"Unknown operation type: {access_request.operation_type}")
        
        # Perform basic subscription check
        subscription_validation = await self.subscription_guard.validate_subscription(
            access_request.organization_id
        )
        
        if subscription_validation.allowed:
            return SIAccessResponse(
                request_id=access_request.request_id,
                organization_id=access_request.organization_id,
                decision=SIAccessDecision.GRANTED,
                allowed=True,
                reason="Unknown operation - allowed with basic subscription",
                metadata={"unknown_operation": True}
            )
        else:
            return SIAccessResponse(
                request_id=access_request.request_id,
                organization_id=access_request.organization_id,
                decision=SIAccessDecision.SUBSCRIPTION_EXPIRED,
                allowed=False,
                reason=subscription_validation.reason
            )
    
    async def _validate_usage_requirements(
        self,
        organization_id: str,
        operation_config: Dict[str, Any],
        requested_resources: Dict[str, int]
    ) -> Dict[str, Any]:
        """Validate usage requirements for operation"""
        usage_validations = {}
        
        usage_types = operation_config.get("usage_types", [])
        usage_amounts = operation_config.get("usage_amounts", [])
        
        for i, usage_type in enumerate(usage_types):
            base_amount = usage_amounts[i] if i < len(usage_amounts) else 1
            
            # Apply resource multiplier if specified
            final_amount = base_amount
            if usage_type.value in requested_resources:
                final_amount *= requested_resources[usage_type.value]
            
            usage_check = await self.si_tier_manager.check_si_usage_limits(
                organization_id, usage_type, final_amount
            )
            
            usage_validations[usage_type.value] = usage_check
        
        return usage_validations
    
    async def _make_final_decision(
        self,
        access_request: SIAccessRequest,
        service_validation: Any,
        usage_validations: Dict[str, Any]
    ) -> SIAccessResponse:
        """Make final access decision based on all validations"""
        
        organization_id = access_request.organization_id
        request_id = access_request.request_id
        
        # Check if any usage validation failed
        failed_validations = [
            usage_type for usage_type, validation in usage_validations.items()
            if not validation.get("allowed", False)
        ]
        
        if failed_validations:
            # Check if overage billing can resolve the issue
            total_overage_cost = sum(
                float(validation.get("overage_cost", 0))
                for validation in usage_validations.values()
                if validation.get("overage_cost")
            )
            
            if total_overage_cost > 0 and self.enable_overage_billing:
                return SIAccessResponse(
                    request_id=request_id,
                    organization_id=organization_id,
                    decision=SIAccessDecision.OVERAGE_BILLING_APPLIED,
                    allowed=True,
                    reason=f"Usage limits exceeded - overage billing applied",
                    usage_info=usage_validations,
                    overage_cost=total_overage_cost,
                    recommended_actions=["Consider upgrading to avoid overage charges"]
                )
            else:
                # Hard limit reached
                next_reset = min(
                    validation.get("reset_time", datetime.now(timezone.utc) + timedelta(hours=1))
                    for validation in usage_validations.values()
                    if not validation.get("allowed", False)
                )
                
                return SIAccessResponse(
                    request_id=request_id,
                    organization_id=organization_id,
                    decision=SIAccessDecision.USAGE_LIMIT_EXCEEDED,
                    allowed=False,
                    reason=f"Usage limits exceeded for: {', '.join(failed_validations)}",
                    usage_info=usage_validations,
                    retry_after=next_reset,
                    recommended_actions=["Upgrade subscription tier for higher limits"]
                )
        
        # All validations passed
        return SIAccessResponse(
            request_id=request_id,
            organization_id=organization_id,
            decision=SIAccessDecision.GRANTED,
            allowed=True,
            reason="Access granted",
            current_tier=service_validation.current_tier,
            usage_info=usage_validations
        )
    
    async def _record_operation_usage(
        self,
        organization_id: str,
        operation_config: Dict[str, Any],
        requested_resources: Dict[str, int]
    ):
        """Record usage for the operation"""
        usage_types = operation_config.get("usage_types", [])
        usage_amounts = operation_config.get("usage_amounts", [])
        
        for i, usage_type in enumerate(usage_types):
            base_amount = usage_amounts[i] if i < len(usage_amounts) else 1
            
            # Apply resource multiplier if specified
            final_amount = base_amount
            if usage_type.value in requested_resources:
                final_amount *= requested_resources[usage_type.value]
            
            await self.si_usage_tracker.record_si_usage(
                organization_id, usage_type, final_amount
            )
    
    def _map_subscription_decision(self, validation_result: str) -> SIAccessDecision:
        """Map subscription validation result to SI access decision"""
        mapping = {
            "expired": SIAccessDecision.SUBSCRIPTION_EXPIRED,
            "trial_expired": SIAccessDecision.TRIAL_EXPIRED,
            "payment_required": SIAccessDecision.PAYMENT_OVERDUE,
            "suspended": SIAccessDecision.SUSPENDED,
            "invalid": SIAccessDecision.DENIED
        }
        return mapping.get(validation_result, SIAccessDecision.DENIED)
    
    def _map_validation_decision(self, validation_result: SIValidationResult) -> SIAccessDecision:
        """Map tier validation result to SI access decision"""
        mapping = {
            SIValidationResult.TIER_INSUFFICIENT: SIAccessDecision.TIER_UPGRADE_REQUIRED,
            SIValidationResult.USAGE_EXCEEDED: SIAccessDecision.USAGE_LIMIT_EXCEEDED,
            SIValidationResult.FEATURE_RESTRICTED: SIAccessDecision.FEATURE_NOT_AVAILABLE,
            SIValidationResult.SUBSCRIPTION_EXPIRED: SIAccessDecision.SUBSCRIPTION_EXPIRED,
            SIValidationResult.PAYMENT_REQUIRED: SIAccessDecision.PAYMENT_OVERDUE
        }
        return mapping.get(validation_result, SIAccessDecision.DENIED)
    
    def _generate_feasibility_recommendations(
        self,
        tier_config: SITierConfig,
        feasibility_checks: Dict[str, Any],
        total_overage_cost: float
    ) -> List[str]:
        """Generate recommendations for operation feasibility"""
        recommendations = []
        
        # Check for tier upgrade opportunities
        exceeded_limits = [
            usage_type for usage_type, check in feasibility_checks.items()
            if not check["allowed"]
        ]
        
        if exceeded_limits:
            recommendations.append(f"Upgrade from {tier_config.tier.value} tier for higher limits")
        
        if total_overage_cost > tier_config.monthly_price * 0.2:
            recommendations.append("Consider upgrading - overage costs are significant")
        
        # Check for optimization opportunities
        high_usage = [
            usage_type for usage_type, check in feasibility_checks.items()
            if check["current_usage"] / check["limit"] > 0.8
        ]
        
        if high_usage:
            recommendations.append("Usage is high - consider bulk operations for efficiency")
        
        return recommendations
    
    def _generate_access_recommendations(
        self,
        subscription_validation: Any,
        tier_config: Optional[SITierConfig],
        usage_analytics: Dict[str, Any]
    ) -> List[str]:
        """Generate access recommendations for organization"""
        recommendations = []
        
        if not subscription_validation.allowed:
            recommendations.append("Resolve subscription issues for full access")
            return recommendations
        
        if not tier_config:
            recommendations.append("Subscribe to SI plan for enhanced features")
            return recommendations
        
        # Analyze utilization
        utilization = usage_analytics.get("utilization", {})
        
        high_usage_metrics = [
            metric for metric, percentage in utilization.items()
            if percentage > 80
        ]
        
        if high_usage_metrics:
            recommendations.append(f"High usage detected: {', '.join(high_usage_metrics)} - consider upgrading")
        
        # Check for cost optimization
        overage_charges = usage_analytics.get("current_metrics", {}).get("overage_charges", 0)
        if overage_charges > 0:
            recommendations.append("Upgrade tier to avoid overage charges")
        
        # Growth recommendations
        trends = usage_analytics.get("trends", [])
        if len(trends) >= 2 and trends[-1]["usage"] > trends[-2]["usage"] * 1.3:
            recommendations.append("Rapid growth detected - plan for higher tier")
        
        return recommendations
    
    async def _record_access_metrics(
        self,
        access_request: SIAccessRequest,
        access_response: SIAccessResponse
    ):
        """Record access metrics for monitoring and analytics"""
        await self.metrics_collector.record_counter(
            "si_access_requests",
            tags={
                "organization_id": access_request.organization_id,
                "service_name": access_request.service_name,
                "operation_type": access_request.operation_type,
                "decision": access_response.decision.value,
                "allowed": str(access_response.allowed).lower()
            }
        )
        
        if not access_response.allowed:
            await self.metrics_collector.record_counter(
                "si_access_denials",
                tags={
                    "reason": access_response.decision.value,
                    "tier": access_response.current_tier or "unknown"
                }
            )