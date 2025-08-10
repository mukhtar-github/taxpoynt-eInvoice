"""
Subscription Guard - Subscription validation and compliance

This module provides comprehensive subscription validation and compliance checking
that integrates with the existing tier manager and billing system to ensure proper
subscription-based access control and billing compliance across the TaxPoynt platform.

Integrates with:
- billing_orchestration/tier_manager.py for subscription management
- billing_orchestration/subscription_manager.py for subscription lifecycle
- Platform billing and payment processing
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

# Import existing platform services
from ...billing_orchestration.tier_manager import TierManager, AccessDecision
from ...billing_orchestration.subscription_manager import SubscriptionManager
from ....core_platform.monitoring import MetricsCollector
from ....core_platform.data_management.cache_manager import CacheManager
from ....core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class SubscriptionStatus(str, Enum):
    """Subscription status types"""
    ACTIVE = "active"
    TRIAL = "trial"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    PENDING = "pending"
    INCOMPLETE = "incomplete"


class ValidationResult(str, Enum):
    """Subscription validation results"""
    VALID = "valid"
    INVALID = "invalid"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    TRIAL_EXPIRED = "trial_expired"
    PAYMENT_REQUIRED = "payment_required"
    DOWNGRADE_REQUIRED = "downgrade_required"
    GRACE_PERIOD = "grace_period"


class ComplianceViolationType(str, Enum):
    """Types of compliance violations"""
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    PAYMENT_OVERDUE = "payment_overdue"
    TIER_VIOLATION = "tier_violation"
    USAGE_EXCEEDED = "usage_exceeded"
    FEATURE_UNAUTHORIZED = "feature_unauthorized"
    BILLING_FAILURE = "billing_failure"
    ACCOUNT_SUSPENDED = "account_suspended"


@dataclass
class SubscriptionInfo:
    """Comprehensive subscription information"""
    organization_id: str
    subscription_id: str
    tier: str
    status: SubscriptionStatus
    started_at: datetime
    expires_at: Optional[datetime]
    trial_end: Optional[datetime]
    billing_cycle: str
    billing_amount: Decimal
    currency: str
    next_billing_date: Optional[datetime]
    payment_method_valid: bool
    grace_period_end: Optional[datetime]
    auto_renew: bool
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def is_trial(self) -> bool:
        return self.status == SubscriptionStatus.TRIAL
    
    @property
    def is_active(self) -> bool:
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]
    
    @property
    def is_expired(self) -> bool:
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False
    
    @property
    def days_until_expiry(self) -> int:
        if self.expires_at:
            delta = self.expires_at - datetime.now(timezone.utc)
            return max(0, delta.days)
        return 999999  # No expiry
    
    @property
    def is_in_grace_period(self) -> bool:
        if self.grace_period_end:
            return datetime.now(timezone.utc) <= self.grace_period_end
        return False


@dataclass
class SubscriptionValidation:
    """Result of subscription validation"""
    organization_id: str
    validation_result: ValidationResult
    subscription_info: Optional[SubscriptionInfo]
    allowed: bool
    reason: str
    compliance_violations: List[ComplianceViolationType] = None
    grace_period_end: Optional[datetime] = None
    recommended_action: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.compliance_violations is None:
            self.compliance_violations = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ComplianceAlert:
    """Compliance alert information"""
    alert_id: str
    organization_id: str
    violation_type: ComplianceViolationType
    severity: str
    message: str
    detected_at: datetime
    expires_at: Optional[datetime] = None
    resolved: bool = False
    resolution_action: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SubscriptionGuard:
    """
    Comprehensive subscription validation and compliance system that ensures
    proper subscription-based access control, billing compliance, and proactive
    subscription management across the TaxPoynt platform.
    """
    
    def __init__(
        self,
        tier_manager: TierManager,
        subscription_manager: SubscriptionManager,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        notification_service: NotificationService,
        config: Optional[Dict[str, Any]] = None
    ):
        self.tier_manager = tier_manager
        self.subscription_manager = subscription_manager
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.notification_service = notification_service
        self.config = config or {}
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 900)  # 15 minutes
        self.grace_period_days = self.config.get("grace_period_days", 7)
        self.trial_warning_days = self.config.get("trial_warning_days", 3)
        self.expiry_warning_days = self.config.get("expiry_warning_days", 7)
        self.enable_auto_downgrade = self.config.get("enable_auto_downgrade", True)
        self.enable_grace_period = self.config.get("enable_grace_period", True)
        
        # Compliance rules
        self.compliance_rules = self._load_compliance_rules()
    
    def _load_compliance_rules(self) -> Dict[str, Any]:
        """Load compliance rules and validation criteria"""
        return {
            "trial_extension_limit": 2,  # Maximum trial extensions
            "grace_period_features": [   # Features allowed during grace period
                "firs_irn_generation",
                "basic_integration",
                "data_export"
            ],
            "suspension_thresholds": {
                "payment_overdue_days": 30,
                "compliance_violations": 5,
                "tier_violations": 3
            },
            "auto_downgrade_rules": {
                "downgrade_after_days": 14,
                "target_tier": "FREE",
                "preserve_data_days": 30
            }
        }
    
    async def validate_subscription(
        self,
        organization_id: str,
        required_tier: Optional[str] = None,
        required_features: Optional[List[str]] = None
    ) -> SubscriptionValidation:
        """
        Comprehensive subscription validation including tier compliance,
        payment status, and feature access validation.
        """
        try:
            # Check cache first
            cache_key = f"subscription_validation:{organization_id}"
            cached_validation = await self.cache_manager.get(cache_key)
            if cached_validation and not self._is_validation_expired(cached_validation):
                return SubscriptionValidation(**cached_validation)
            
            # Get subscription information
            subscription_info = await self._get_subscription_info(organization_id)
            
            if not subscription_info:
                return SubscriptionValidation(
                    organization_id=organization_id,
                    validation_result=ValidationResult.INVALID,
                    subscription_info=None,
                    allowed=False,
                    reason="No subscription found",
                    recommended_action="Please subscribe to a plan"
                )
            
            # Perform comprehensive validation
            validation = await self._perform_validation(
                subscription_info, required_tier, required_features
            )
            
            # Cache validation result
            if validation.allowed:
                await self.cache_manager.set(
                    cache_key,
                    asdict(validation),
                    ttl=self.cache_ttl
                )
            
            # Record metrics
            await self._record_validation_metrics(validation)
            
            # Check for proactive alerts
            await self._check_proactive_alerts(subscription_info)
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating subscription for {organization_id}: {e}")
            return SubscriptionValidation(
                organization_id=organization_id,
                validation_result=ValidationResult.INVALID,
                subscription_info=None,
                allowed=False,
                reason=f"Validation error: {str(e)}"
            )
    
    async def _get_subscription_info(self, organization_id: str) -> Optional[SubscriptionInfo]:
        """Get comprehensive subscription information"""
        try:
            # Get subscription from subscription manager
            subscription = await self.subscription_manager.get_organization_subscription(
                organization_id
            )
            
            if not subscription:
                return None
            
            # Get billing information
            billing_info = await self.subscription_manager.get_billing_info(
                organization_id
            )
            
            # Get payment method status
            payment_status = await self.subscription_manager.get_payment_method_status(
                organization_id
            )
            
            return SubscriptionInfo(
                organization_id=organization_id,
                subscription_id=subscription.id,
                tier=subscription.tier,
                status=SubscriptionStatus(subscription.status),
                started_at=subscription.created_at,
                expires_at=subscription.expires_at,
                trial_end=subscription.trial_end,
                billing_cycle=billing_info.get("cycle", "monthly"),
                billing_amount=billing_info.get("amount", Decimal("0")),
                currency=billing_info.get("currency", "USD"),
                next_billing_date=billing_info.get("next_billing_date"),
                payment_method_valid=payment_status.get("valid", False),
                grace_period_end=subscription.grace_period_end,
                auto_renew=subscription.auto_renew,
                metadata=subscription.metadata or {}
            )
            
        except Exception as e:
            logger.error(f"Error getting subscription info for {organization_id}: {e}")
            return None
    
    async def _perform_validation(
        self,
        subscription_info: SubscriptionInfo,
        required_tier: Optional[str],
        required_features: Optional[List[str]]
    ) -> SubscriptionValidation:
        """Perform comprehensive subscription validation"""
        
        violations = []
        validation_result = ValidationResult.VALID
        allowed = True
        reason = "Subscription valid"
        grace_period_end = None
        recommended_action = None
        
        # 1. Check subscription status
        if subscription_info.status == SubscriptionStatus.EXPIRED:
            violations.append(ComplianceViolationType.SUBSCRIPTION_EXPIRED)
            validation_result = ValidationResult.EXPIRED
            allowed = False
            reason = "Subscription expired"
            recommended_action = "Renew subscription"
        
        elif subscription_info.status == SubscriptionStatus.SUSPENDED:
            violations.append(ComplianceViolationType.ACCOUNT_SUSPENDED)
            validation_result = ValidationResult.SUSPENDED
            allowed = False
            reason = "Account suspended"
            recommended_action = "Contact support"
        
        elif subscription_info.status == SubscriptionStatus.CANCELED:
            violations.append(ComplianceViolationType.SUBSCRIPTION_EXPIRED)
            validation_result = ValidationResult.EXPIRED
            allowed = False
            reason = "Subscription canceled"
            recommended_action = "Reactivate subscription"
        
        elif subscription_info.status == SubscriptionStatus.PAST_DUE:
            violations.append(ComplianceViolationType.PAYMENT_OVERDUE)
            
            # Check grace period
            if self.enable_grace_period and subscription_info.is_in_grace_period:
                validation_result = ValidationResult.GRACE_PERIOD
                allowed = True  # Allow with restrictions
                reason = "In grace period due to payment issue"
                grace_period_end = subscription_info.grace_period_end
                recommended_action = "Update payment method"
            else:
                validation_result = ValidationResult.PAYMENT_REQUIRED
                allowed = False
                reason = "Payment overdue"
                recommended_action = "Update payment method and settle overdue amount"
        
        # 2. Check trial status
        if subscription_info.is_trial:
            if subscription_info.trial_end and datetime.now(timezone.utc) > subscription_info.trial_end:
                violations.append(ComplianceViolationType.SUBSCRIPTION_EXPIRED)
                validation_result = ValidationResult.TRIAL_EXPIRED
                allowed = False
                reason = "Trial period expired"
                recommended_action = "Upgrade to paid plan"
        
        # 3. Check expiry
        if subscription_info.is_expired and allowed:
            violations.append(ComplianceViolationType.SUBSCRIPTION_EXPIRED)
            validation_result = ValidationResult.EXPIRED
            allowed = False
            reason = "Subscription expired"
            recommended_action = "Renew subscription"
        
        # 4. Check tier requirements
        if required_tier and allowed:
            tier_check = await self._validate_tier_access(
                subscription_info.tier, required_tier
            )
            if not tier_check:
                violations.append(ComplianceViolationType.TIER_VIOLATION)
                validation_result = ValidationResult.DOWNGRADE_REQUIRED
                allowed = False
                reason = f"Required tier: {required_tier}, current: {subscription_info.tier}"
                recommended_action = f"Upgrade to {required_tier} or higher"
        
        # 5. Check feature requirements
        if required_features and allowed:
            feature_violations = await self._validate_feature_access(
                subscription_info.tier, required_features
            )
            if feature_violations:
                violations.extend([ComplianceViolationType.FEATURE_UNAUTHORIZED] * len(feature_violations))
                validation_result = ValidationResult.DOWNGRADE_REQUIRED
                allowed = False
                reason = f"Features not available in {subscription_info.tier} tier"
                recommended_action = "Upgrade to access required features"
        
        # 6. Check payment method
        if not subscription_info.payment_method_valid and subscription_info.status == SubscriptionStatus.ACTIVE:
            violations.append(ComplianceViolationType.BILLING_FAILURE)
            # Don't block immediately, but flag for attention
            if validation_result == ValidationResult.VALID:
                recommended_action = "Update payment method"
        
        # 7. Grace period feature restrictions
        if validation_result == ValidationResult.GRACE_PERIOD:
            if required_features:
                restricted_features = [
                    f for f in required_features 
                    if f not in self.compliance_rules["grace_period_features"]
                ]
                if restricted_features:
                    allowed = False
                    reason = "Feature not available during grace period"
                    recommended_action = "Update payment method to restore full access"
        
        return SubscriptionValidation(
            organization_id=subscription_info.organization_id,
            validation_result=validation_result,
            subscription_info=subscription_info,
            allowed=allowed,
            reason=reason,
            compliance_violations=violations,
            grace_period_end=grace_period_end,
            recommended_action=recommended_action,
            metadata={
                "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                "required_tier": required_tier,
                "required_features": required_features
            }
        )
    
    async def _validate_tier_access(self, current_tier: str, required_tier: str) -> bool:
        """Validate if current tier meets required tier"""
        tier_hierarchy = ["FREE", "STARTER", "PROFESSIONAL", "ENTERPRISE", "SCALE"]
        
        try:
            current_index = tier_hierarchy.index(current_tier)
            required_index = tier_hierarchy.index(required_tier)
            return current_index >= required_index
        except ValueError:
            # Unknown tier, default to deny
            return False
    
    async def _validate_feature_access(
        self,
        current_tier: str,
        required_features: List[str]
    ) -> List[str]:
        """Validate feature access and return unauthorized features"""
        unauthorized_features = []
        
        for feature in required_features:
            has_access = await self.tier_manager.check_feature_access(
                organization_id="",  # Not needed for tier-only check
                feature=feature,
                tier=current_tier
            )
            
            if has_access.decision != AccessDecision.GRANTED:
                unauthorized_features.append(feature)
        
        return unauthorized_features
    
    async def check_billing_compliance(self, organization_id: str) -> Dict[str, Any]:
        """Check comprehensive billing compliance"""
        try:
            subscription_info = await self._get_subscription_info(organization_id)
            if not subscription_info:
                return {
                    "compliant": False,
                    "violations": ["No subscription found"],
                    "recommended_actions": ["Subscribe to a plan"]
                }
            
            violations = []
            recommended_actions = []
            
            # Check payment status
            if not subscription_info.payment_method_valid:
                violations.append("Invalid payment method")
                recommended_actions.append("Update payment method")
            
            # Check overdue payments
            if subscription_info.status == SubscriptionStatus.PAST_DUE:
                violations.append("Payment overdue")
                recommended_actions.append("Settle overdue payments")
            
            # Check upcoming expiry
            if subscription_info.days_until_expiry <= self.expiry_warning_days:
                violations.append(f"Subscription expires in {subscription_info.days_until_expiry} days")
                recommended_actions.append("Renew subscription")
            
            # Check trial expiry
            if subscription_info.is_trial and subscription_info.trial_end:
                days_until_trial_end = (subscription_info.trial_end - datetime.now(timezone.utc)).days
                if days_until_trial_end <= self.trial_warning_days:
                    violations.append(f"Trial expires in {days_until_trial_end} days")
                    recommended_actions.append("Upgrade to paid plan")
            
            return {
                "compliant": len(violations) == 0,
                "violations": violations,
                "recommended_actions": recommended_actions,
                "subscription_info": asdict(subscription_info)
            }
            
        except Exception as e:
            logger.error(f"Error checking billing compliance for {organization_id}: {e}")
            return {
                "compliant": False,
                "violations": [f"Compliance check error: {str(e)}"],
                "recommended_actions": ["Contact support"]
            }
    
    async def handle_subscription_change(
        self,
        organization_id: str,
        old_tier: str,
        new_tier: str,
        change_type: str
    ):
        """Handle subscription tier changes and compliance updates"""
        try:
            # Clear cached validations
            cache_key = f"subscription_validation:{organization_id}"
            await self.cache_manager.delete(cache_key)
            
            # Log the change
            logger.info(f"Subscription change for {organization_id}: {old_tier} -> {new_tier} ({change_type})")
            
            # Handle tier-specific changes
            if change_type == "upgrade":
                await self._handle_upgrade(organization_id, old_tier, new_tier)
            elif change_type == "downgrade":
                await self._handle_downgrade(organization_id, old_tier, new_tier)
            elif change_type == "cancellation":
                await self._handle_cancellation(organization_id, old_tier)
            
            # Record metrics
            await self.metrics_collector.record_counter(
                "subscription_changes",
                tags={
                    "organization_id": organization_id,
                    "old_tier": old_tier,
                    "new_tier": new_tier,
                    "change_type": change_type
                }
            )
            
        except Exception as e:
            logger.error(f"Error handling subscription change for {organization_id}: {e}")
    
    async def _handle_upgrade(self, organization_id: str, old_tier: str, new_tier: str):
        """Handle subscription upgrade"""
        # Notify of new features available
        await self.notification_service.send_upgrade_notification(
            organization_id, old_tier, new_tier
        )
        
        # Update quota limits
        await self.tier_manager.update_organization_quotas(organization_id, new_tier)
    
    async def _handle_downgrade(self, organization_id: str, old_tier: str, new_tier: str):
        """Handle subscription downgrade"""
        # Check for feature usage that exceeds new tier limits
        usage_violations = await self._check_downgrade_violations(
            organization_id, new_tier
        )
        
        if usage_violations:
            # Notify about feature restrictions
            await self.notification_service.send_downgrade_warning(
                organization_id, usage_violations
            )
        
        # Update quota limits
        await self.tier_manager.update_organization_quotas(organization_id, new_tier)
    
    async def _handle_cancellation(self, organization_id: str, old_tier: str):
        """Handle subscription cancellation"""
        # Set grace period if enabled
        if self.enable_grace_period:
            grace_period_end = datetime.now(timezone.utc) + timedelta(days=self.grace_period_days)
            await self.subscription_manager.set_grace_period(
                organization_id, grace_period_end
            )
        
        # Schedule data retention policy
        if self.enable_auto_downgrade:
            await self._schedule_auto_downgrade(organization_id)
    
    async def _check_downgrade_violations(
        self,
        organization_id: str,
        new_tier: str
    ) -> List[str]:
        """Check for violations when downgrading to a lower tier"""
        violations = []
        
        # Check current usage against new tier limits
        current_usage = await self.tier_manager.get_organization_usage(organization_id)
        new_tier_limits = await self.tier_manager.get_tier_limits(new_tier)
        
        for metric, usage in current_usage.items():
            limit = new_tier_limits.get(metric, {}).get("limit", 0)
            if usage > limit:
                violations.append(f"{metric}: {usage} exceeds new limit of {limit}")
        
        return violations
    
    async def _schedule_auto_downgrade(self, organization_id: str):
        """Schedule automatic downgrade after cancellation"""
        downgrade_date = datetime.now(timezone.utc) + timedelta(
            days=self.compliance_rules["auto_downgrade_rules"]["downgrade_after_days"]
        )
        
        # This would typically schedule a background task
        logger.info(f"Scheduled auto-downgrade for {organization_id} on {downgrade_date}")
    
    async def _check_proactive_alerts(self, subscription_info: SubscriptionInfo):
        """Check for proactive alerts and notifications"""
        organization_id = subscription_info.organization_id
        
        # Trial expiry warning
        if subscription_info.is_trial and subscription_info.trial_end:
            days_until_expiry = (subscription_info.trial_end - datetime.now(timezone.utc)).days
            if days_until_expiry <= self.trial_warning_days:
                await self._send_trial_expiry_alert(subscription_info, days_until_expiry)
        
        # Subscription expiry warning
        if subscription_info.expires_at:
            days_until_expiry = subscription_info.days_until_expiry
            if days_until_expiry <= self.expiry_warning_days:
                await self._send_expiry_alert(subscription_info, days_until_expiry)
        
        # Payment method warning
        if not subscription_info.payment_method_valid:
            await self._send_payment_method_alert(subscription_info)
    
    async def _send_trial_expiry_alert(self, subscription_info: SubscriptionInfo, days: int):
        """Send trial expiry alert"""
        alert = ComplianceAlert(
            alert_id=f"trial_expiry_{subscription_info.organization_id}_{days}",
            organization_id=subscription_info.organization_id,
            violation_type=ComplianceViolationType.SUBSCRIPTION_EXPIRED,
            severity="warning",
            message=f"Trial expires in {days} days",
            detected_at=datetime.now(timezone.utc),
            expires_at=subscription_info.trial_end
        )
        
        await self.notification_service.send_compliance_alert(alert)
    
    async def _send_expiry_alert(self, subscription_info: SubscriptionInfo, days: int):
        """Send subscription expiry alert"""
        alert = ComplianceAlert(
            alert_id=f"subscription_expiry_{subscription_info.organization_id}_{days}",
            organization_id=subscription_info.organization_id,
            violation_type=ComplianceViolationType.SUBSCRIPTION_EXPIRED,
            severity="warning",
            message=f"Subscription expires in {days} days",
            detected_at=datetime.now(timezone.utc),
            expires_at=subscription_info.expires_at
        )
        
        await self.notification_service.send_compliance_alert(alert)
    
    async def _send_payment_method_alert(self, subscription_info: SubscriptionInfo):
        """Send payment method alert"""
        alert = ComplianceAlert(
            alert_id=f"payment_method_{subscription_info.organization_id}",
            organization_id=subscription_info.organization_id,
            violation_type=ComplianceViolationType.BILLING_FAILURE,
            severity="error",
            message="Payment method is invalid or expired",
            detected_at=datetime.now(timezone.utc)
        )
        
        await self.notification_service.send_compliance_alert(alert)
    
    def _is_validation_expired(self, cached_validation: Dict[str, Any]) -> bool:
        """Check if cached validation has expired"""
        validation_time = cached_validation.get("metadata", {}).get("validation_timestamp")
        if not validation_time:
            return True
        
        validation_datetime = datetime.fromisoformat(validation_time.replace('Z', '+00:00'))
        return datetime.now(timezone.utc) > validation_datetime + timedelta(seconds=self.cache_ttl)
    
    async def _record_validation_metrics(self, validation: SubscriptionValidation):
        """Record subscription validation metrics"""
        await self.metrics_collector.record_counter(
            "subscription_validations",
            tags={
                "result": validation.validation_result.value,
                "allowed": str(validation.allowed).lower(),
                "tier": validation.subscription_info.tier if validation.subscription_info else "none"
            }
        )
        
        if validation.compliance_violations:
            for violation in validation.compliance_violations:
                await self.metrics_collector.record_counter(
                    "compliance_violations",
                    tags={"violation_type": violation.value}
                )


# Decorator for subscription validation

def require_subscription(
    tier: Optional[str] = None,
    features: Optional[List[str]] = None,
    organization_attr: str = "organization_id"
):
    """
    Decorator to require valid subscription for FastAPI endpoints
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and organization from function parameters
            request = None
            organization_id = None
            
            for arg in args:
                if hasattr(arg, 'url') and hasattr(arg, 'headers'):  # FastAPI Request
                    request = arg
                    organization_id = getattr(request.state, organization_attr, None)
                    break
            
            if not request or not organization_id:
                raise HTTPException(
                    status_code=400,
                    detail="Subscription guard: Request or organization not found"
                )
            
            # Get subscription guard from request state
            subscription_guard = getattr(request.state, 'subscription_guard', None)
            if not subscription_guard:
                raise HTTPException(
                    status_code=500,
                    detail="Subscription guard not available"
                )
            
            # Validate subscription
            validation = await subscription_guard.validate_subscription(
                organization_id, tier, features
            )
            
            if not validation.allowed:
                headers = {}
                if validation.recommended_action:
                    headers["X-Recommended-Action"] = validation.recommended_action
                
                status_code = 402  # Payment Required
                if validation.validation_result == ValidationResult.SUSPENDED:
                    status_code = 403  # Forbidden
                elif validation.validation_result == ValidationResult.INVALID:
                    status_code = 401  # Unauthorized
                
                raise HTTPException(
                    status_code=status_code,
                    detail=f"Subscription validation failed: {validation.reason}",
                    headers=headers
                )
            
            # Store validation result for potential use
            request.state.subscription_validation = validation
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator