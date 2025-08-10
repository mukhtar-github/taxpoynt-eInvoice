"""
Subscription Manager - SI Subscription Lifecycle Orchestration
Manages the complete lifecycle of SI subscriptions including provisioning, upgrades, downgrades, and cancellations.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4

from core_platform.data_management.billing_repository import BillingRepository, SubscriptionTier, PaymentStatus
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class SubscriptionAction(str, Enum):
    """Subscription lifecycle actions"""
    CREATE = "create"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    SUSPEND = "suspend"
    REACTIVATE = "reactivate"
    CANCEL = "cancel"
    RENEW = "renew"


class SubscriptionStatus(str, Enum):
    """Extended subscription status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    PENDING_PAYMENT = "pending_payment"
    TRIAL = "trial"
    EXPIRED = "expired"


@dataclass
class SubscriptionEvent:
    """Subscription lifecycle event"""
    event_id: str
    tenant_id: UUID
    organization_id: UUID
    action: SubscriptionAction
    from_tier: Optional[SubscriptionTier]
    to_tier: Optional[SubscriptionTier]
    effective_date: datetime
    reason: str
    triggered_by: str
    metadata: Dict[str, Any]
    created_at: datetime


@dataclass
class SubscriptionMetrics:
    """Subscription performance metrics"""
    tenant_id: UUID
    current_tier: SubscriptionTier
    months_subscribed: int
    total_revenue: float
    average_monthly_usage: Dict[str, float]
    satisfaction_score: Optional[float]
    churn_risk_score: float
    upgrade_probability: float
    last_updated: datetime


class SubscriptionManager:
    """SI Subscription Lifecycle Manager"""
    
    def __init__(self):
        self.billing_repository = BillingRepository()
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Subscription events registry
        self.subscription_events: Dict[str, SubscriptionEvent] = {}
        
        # Configuration
        self.config = {
            "trial_period_days": 14,
            "grace_period_days": 7,
            "auto_downgrade_enabled": True,
            "upgrade_immediate": True,
            "cancellation_feedback_required": True
        }
    
    async def create_subscription(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        tier: SubscriptionTier,
        start_date: Optional[datetime] = None,
        trial_mode: bool = False,
        triggered_by: str = "system"
    ) -> Dict[str, Any]:
        """Create new SI subscription with full lifecycle management"""
        try:
            start_date = start_date or datetime.now(timezone.utc)
            
            # Validate subscription requirements
            validation_result = await self._validate_subscription_requirements(
                tenant_id, organization_id, tier
            )
            if not validation_result["valid"]:
                return {
                    "status": "error",
                    "message": validation_result["message"]
                }
            
            # Create subscription in billing repository
            subscription_result = await self.billing_repository.create_subscription(
                tenant_id=tenant_id,
                organization_id=organization_id,
                tier=tier,
                start_date=start_date
            )
            
            if subscription_result["status"] != "success":
                return subscription_result
            
            # Set trial status if applicable
            if trial_mode:
                await self._activate_trial_period(tenant_id, self.config["trial_period_days"])
            
            # Provision subscription services
            provisioning_result = await self._provision_subscription_services(
                tenant_id, organization_id, tier
            )
            
            # Record subscription event
            event = await self._record_subscription_event(
                tenant_id=tenant_id,
                organization_id=organization_id,
                action=SubscriptionAction.CREATE,
                from_tier=None,
                to_tier=tier,
                reason=f"New subscription created ({'trial' if trial_mode else 'paid'})",
                triggered_by=triggered_by,
                metadata={
                    "trial_mode": trial_mode,
                    "start_date": start_date.isoformat(),
                    "provisioning_result": provisioning_result
                }
            )
            
            # Send welcome notification
            await self._send_subscription_notification(
                tenant_id, "subscription_created", {
                    "tier": tier.value,
                    "trial_mode": trial_mode,
                    "subscription_id": subscription_result["subscription_id"]
                }
            )
            
            # Emit event
            await self.event_bus.emit("subscription_created", {
                "tenant_id": str(tenant_id),
                "organization_id": str(organization_id),
                "tier": tier.value,
                "trial_mode": trial_mode,
                "event_id": event.event_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Subscription created for tenant {tenant_id}, tier: {tier.value}")
            
            return {
                "status": "success",
                "subscription_id": subscription_result["subscription_id"],
                "event_id": event.event_id,
                "tier": tier.value,
                "trial_mode": trial_mode,
                "provisioning": provisioning_result
            }
            
        except Exception as e:
            self.logger.error(f"Error creating subscription for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def upgrade_subscription(
        self,
        tenant_id: UUID,
        new_tier: SubscriptionTier,
        effective_date: Optional[datetime] = None,
        triggered_by: str = "customer"
    ) -> Dict[str, Any]:
        """Upgrade subscription to higher tier"""
        try:
            # Get current subscription
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            current_tier = SubscriptionTier(current_subscription["subscription_tier"])
            
            # Validate upgrade path
            if not await self._validate_tier_upgrade(current_tier, new_tier):
                return {"status": "error", "message": "Invalid upgrade path"}
            
            effective_date = effective_date or datetime.now(timezone.utc)
            
            # Calculate prorated charges
            prorated_amount = await self._calculate_prorated_upgrade_cost(
                tenant_id, current_tier, new_tier, effective_date
            )
            
            # Process upgrade
            upgrade_result = await self._process_subscription_change(
                tenant_id, new_tier, effective_date, prorated_amount
            )
            
            if upgrade_result["status"] != "success":
                return upgrade_result
            
            # Update service provisioning
            await self._update_service_provisioning(tenant_id, current_tier, new_tier)
            
            # Record event
            event = await self._record_subscription_event(
                tenant_id=tenant_id,
                organization_id=UUID(current_subscription["organization_id"]),
                action=SubscriptionAction.UPGRADE,
                from_tier=current_tier,
                to_tier=new_tier,
                reason=f"Tier upgrade from {current_tier.value} to {new_tier.value}",
                triggered_by=triggered_by,
                metadata={
                    "prorated_amount": float(prorated_amount),
                    "effective_date": effective_date.isoformat()
                }
            )
            
            # Send notification
            await self._send_subscription_notification(
                tenant_id, "subscription_upgraded", {
                    "from_tier": current_tier.value,
                    "to_tier": new_tier.value,
                    "prorated_amount": float(prorated_amount)
                }
            )
            
            # Emit event
            await self.event_bus.emit("subscription_upgraded", {
                "tenant_id": str(tenant_id),
                "from_tier": current_tier.value,
                "to_tier": new_tier.value,
                "event_id": event.event_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Subscription upgraded for tenant {tenant_id}: {current_tier.value} → {new_tier.value}")
            
            return {
                "status": "success",
                "event_id": event.event_id,
                "from_tier": current_tier.value,
                "to_tier": new_tier.value,
                "prorated_amount": float(prorated_amount),
                "effective_date": effective_date.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error upgrading subscription for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def downgrade_subscription(
        self,
        tenant_id: UUID,
        new_tier: SubscriptionTier,
        effective_date: Optional[datetime] = None,
        triggered_by: str = "customer",
        reason: str = "customer_request"
    ) -> Dict[str, Any]:
        """Downgrade subscription to lower tier"""
        try:
            # Get current subscription
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            current_tier = SubscriptionTier(current_subscription["subscription_tier"])
            
            # Validate downgrade impact
            impact_assessment = await self._assess_downgrade_impact(tenant_id, current_tier, new_tier)
            
            effective_date = effective_date or datetime.now(timezone.utc)
            
            # Calculate credit for unused service
            credit_amount = await self._calculate_downgrade_credit(
                tenant_id, current_tier, new_tier, effective_date
            )
            
            # Process downgrade
            downgrade_result = await self._process_subscription_change(
                tenant_id, new_tier, effective_date, -credit_amount
            )
            
            if downgrade_result["status"] != "success":
                return downgrade_result
            
            # Update service provisioning with data migration if needed
            migration_result = await self._handle_downgrade_data_migration(
                tenant_id, current_tier, new_tier, impact_assessment
            )
            
            # Record event
            event = await self._record_subscription_event(
                tenant_id=tenant_id,
                organization_id=UUID(current_subscription["organization_id"]),
                action=SubscriptionAction.DOWNGRADE,
                from_tier=current_tier,
                to_tier=new_tier,
                reason=f"Tier downgrade: {reason}",
                triggered_by=triggered_by,
                metadata={
                    "credit_amount": float(credit_amount),
                    "impact_assessment": impact_assessment,
                    "migration_result": migration_result,
                    "effective_date": effective_date.isoformat()
                }
            )
            
            # Send notification with impact warning
            await self._send_subscription_notification(
                tenant_id, "subscription_downgraded", {
                    "from_tier": current_tier.value,
                    "to_tier": new_tier.value,
                    "credit_amount": float(credit_amount),
                    "impact_assessment": impact_assessment
                }
            )
            
            # Emit event
            await self.event_bus.emit("subscription_downgraded", {
                "tenant_id": str(tenant_id),
                "from_tier": current_tier.value,
                "to_tier": new_tier.value,
                "event_id": event.event_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Subscription downgraded for tenant {tenant_id}: {current_tier.value} → {new_tier.value}")
            
            return {
                "status": "success",
                "event_id": event.event_id,
                "from_tier": current_tier.value,
                "to_tier": new_tier.value,
                "credit_amount": float(credit_amount),
                "impact_assessment": impact_assessment,
                "migration_result": migration_result
            }
            
        except Exception as e:
            self.logger.error(f"Error downgrading subscription for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def suspend_subscription(
        self,
        tenant_id: UUID,
        reason: str,
        suspension_duration: Optional[int] = None,  # days
        triggered_by: str = "system"
    ) -> Dict[str, Any]:
        """Suspend subscription temporarily"""
        try:
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            # Suspend services while preserving data
            suspension_result = await self._suspend_subscription_services(tenant_id, suspension_duration)
            
            # Record event
            event = await self._record_subscription_event(
                tenant_id=tenant_id,
                organization_id=UUID(current_subscription["organization_id"]),
                action=SubscriptionAction.SUSPEND,
                from_tier=SubscriptionTier(current_subscription["subscription_tier"]),
                to_tier=None,
                reason=f"Subscription suspended: {reason}",
                triggered_by=triggered_by,
                metadata={
                    "suspension_duration": suspension_duration,
                    "suspension_result": suspension_result
                }
            )
            
            # Send notification
            await self._send_subscription_notification(
                tenant_id, "subscription_suspended", {
                    "reason": reason,
                    "suspension_duration": suspension_duration,
                    "reactivation_info": suspension_result.get("reactivation_info")
                }
            )
            
            self.logger.info(f"Subscription suspended for tenant {tenant_id}: {reason}")
            
            return {
                "status": "success",
                "event_id": event.event_id,
                "suspension_result": suspension_result
            }
            
        except Exception as e:
            self.logger.error(f"Error suspending subscription for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def cancel_subscription(
        self,
        tenant_id: UUID,
        cancellation_date: Optional[datetime] = None,
        reason: str = "customer_request",
        feedback: Optional[str] = None,
        triggered_by: str = "customer"
    ) -> Dict[str, Any]:
        """Cancel subscription with proper cleanup"""
        try:
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            cancellation_date = cancellation_date or datetime.now(timezone.utc)
            
            # Calculate final billing and refunds
            final_billing = await self._calculate_final_billing(tenant_id, cancellation_date)
            
            # Initiate data export for customer
            export_result = await self._initiate_data_export(tenant_id)
            
            # Schedule service deprovisioning
            deprovisioning_result = await self._schedule_service_deprovisioning(
                tenant_id, cancellation_date
            )
            
            # Record event
            event = await self._record_subscription_event(
                tenant_id=tenant_id,
                organization_id=UUID(current_subscription["organization_id"]),
                action=SubscriptionAction.CANCEL,
                from_tier=SubscriptionTier(current_subscription["subscription_tier"]),
                to_tier=None,
                reason=f"Subscription cancelled: {reason}",
                triggered_by=triggered_by,
                metadata={
                    "cancellation_date": cancellation_date.isoformat(),
                    "feedback": feedback,
                    "final_billing": final_billing,
                    "export_result": export_result,
                    "deprovisioning_schedule": deprovisioning_result
                }
            )
            
            # Send cancellation confirmation
            await self._send_subscription_notification(
                tenant_id, "subscription_cancelled", {
                    "cancellation_date": cancellation_date.isoformat(),
                    "final_billing": final_billing,
                    "data_export": export_result
                }
            )
            
            # Emit event
            await self.event_bus.emit("subscription_cancelled", {
                "tenant_id": str(tenant_id),
                "reason": reason,
                "event_id": event.event_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Subscription cancelled for tenant {tenant_id}: {reason}")
            
            return {
                "status": "success",
                "event_id": event.event_id,
                "cancellation_date": cancellation_date.isoformat(),
                "final_billing": final_billing,
                "data_export": export_result
            }
            
        except Exception as e:
            self.logger.error(f"Error cancelling subscription for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_subscription_lifecycle(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get complete subscription lifecycle history and current status"""
        try:
            # Get current subscription
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return {"status": "error", "message": "No subscription found"}
            
            # Get subscription events
            events = [
                event for event in self.subscription_events.values()
                if event.tenant_id == tenant_id
            ]
            events.sort(key=lambda x: x.created_at, reverse=True)
            
            # Get subscription metrics
            metrics = await self.get_subscription_metrics(tenant_id)
            
            # Get billing history
            billing_history = await self.billing_repository.get_billing_history(tenant_id)
            
            # Calculate lifecycle metrics
            lifecycle_stats = await self._calculate_lifecycle_stats(tenant_id, events)
            
            return {
                "status": "success",
                "current_subscription": current_subscription,
                "lifecycle_events": [asdict(event) for event in events],
                "metrics": metrics,
                "billing_history": billing_history,
                "lifecycle_stats": lifecycle_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting subscription lifecycle for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_subscription_metrics(self, tenant_id: UUID) -> SubscriptionMetrics:
        """Get comprehensive subscription metrics"""
        try:
            current_subscription = await self.billing_repository.get_subscription(tenant_id)
            if not current_subscription:
                return None
            
            # Calculate metrics
            creation_date = current_subscription["created_at"]
            months_subscribed = (datetime.now(timezone.utc) - creation_date).days // 30
            
            # Get revenue data
            billing_history = await self.billing_repository.get_billing_history(tenant_id)
            total_revenue = sum(float(bill["total_amount"]) for bill in billing_history)
            
            # Get usage analytics
            subscription_analytics = await self.billing_repository.get_subscription_metrics(tenant_id)
            
            # Calculate churn risk and upgrade probability
            churn_risk = await self._calculate_churn_risk(tenant_id, subscription_analytics)
            upgrade_probability = await self._calculate_upgrade_probability(tenant_id, subscription_analytics)
            
            metrics = SubscriptionMetrics(
                tenant_id=tenant_id,
                current_tier=SubscriptionTier(current_subscription["subscription_tier"]),
                months_subscribed=months_subscribed,
                total_revenue=total_revenue,
                average_monthly_usage=subscription_analytics.get("current_usage", {}),
                satisfaction_score=None,  # Would be populated from surveys
                churn_risk_score=churn_risk,
                upgrade_probability=upgrade_probability,
                last_updated=datetime.now(timezone.utc)
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating subscription metrics for {tenant_id}: {str(e)}")
            return None
    
    # Private helper methods
    
    async def _validate_subscription_requirements(
        self, 
        tenant_id: UUID, 
        organization_id: UUID, 
        tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """Validate subscription creation requirements"""
        try:
            # Check for existing active subscription
            existing_subscription = await self.billing_repository.get_subscription(tenant_id)
            if existing_subscription:
                return {
                    "valid": False,
                    "message": "Active subscription already exists"
                }
            
            # Validate organization exists and is active
            # This would integrate with organization management
            
            # Validate tier availability
            if tier not in self.billing_repository.SUBSCRIPTION_TIERS:
                return {
                    "valid": False,
                    "message": f"Invalid subscription tier: {tier.value}"
                }
            
            return {"valid": True, "message": "Validation passed"}
            
        except Exception as e:
            self.logger.error(f"Error validating subscription requirements: {str(e)}")
            return {"valid": False, "message": str(e)}
    
    async def _record_subscription_event(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        action: SubscriptionAction,
        from_tier: Optional[SubscriptionTier],
        to_tier: Optional[SubscriptionTier],
        reason: str,
        triggered_by: str,
        metadata: Dict[str, Any]
    ) -> SubscriptionEvent:
        """Record subscription lifecycle event"""
        try:
            event = SubscriptionEvent(
                event_id=str(uuid4()),
                tenant_id=tenant_id,
                organization_id=organization_id,
                action=action,
                from_tier=from_tier,
                to_tier=to_tier,
                effective_date=datetime.now(timezone.utc),
                reason=reason,
                triggered_by=triggered_by,
                metadata=metadata,
                created_at=datetime.now(timezone.utc)
            )
            
            # Store event
            self.subscription_events[event.event_id] = event
            
            # Cache event
            await self.cache_service.set(
                f"subscription_event:{event.event_id}",
                asdict(event),
                ttl=86400 * 30  # 30 days
            )
            
            return event
            
        except Exception as e:
            self.logger.error(f"Error recording subscription event: {str(e)}")
            raise
    
    async def _send_subscription_notification(
        self,
        tenant_id: UUID,
        notification_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Send subscription lifecycle notification"""
        try:
            await self.notification_service.send_system_notification(
                user_id=f"tenant:{tenant_id}",
                title=f"Subscription {notification_type.replace('_', ' ').title()}",
                message=self._generate_notification_message(notification_type, data),
                priority="high" if notification_type in ["subscription_suspended", "subscription_cancelled"] else "medium",
                metadata={
                    "notification_type": notification_type,
                    "tenant_id": str(tenant_id),
                    **data
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending subscription notification: {str(e)}")
    
    def _generate_notification_message(self, notification_type: str, data: Dict[str, Any]) -> str:
        """Generate user-friendly notification messages"""
        if notification_type == "subscription_created":
            return f"Welcome! Your {data['tier']} subscription is now active."
        elif notification_type == "subscription_upgraded":
            return f"Your subscription has been upgraded from {data['from_tier']} to {data['to_tier']}."
        elif notification_type == "subscription_downgraded":
            return f"Your subscription has been changed from {data['from_tier']} to {data['to_tier']}."
        elif notification_type == "subscription_suspended":
            return f"Your subscription has been temporarily suspended: {data['reason']}"
        elif notification_type == "subscription_cancelled":
            return f"Your subscription has been cancelled. Data export will be available for download."
        else:
            return f"Subscription update: {notification_type}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for subscription manager"""
        try:
            return {
                "status": "healthy",
                "service": "subscription_manager",
                "subscription_events": len(self.subscription_events),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "subscription_manager",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_subscription_manager() -> SubscriptionManager:
    """Create subscription manager instance"""
    return SubscriptionManager()