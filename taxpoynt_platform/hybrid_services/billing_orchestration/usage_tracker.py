"""
Usage Tracker - Track usage vs tier limits
Real-time tracking of SI service usage against subscription tier limits with intelligent alerting and enforcement.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal

from core_platform.data_management.billing_repository import BillingRepository, SubscriptionTier
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class UsageMetric(str, Enum):
    """Usage metrics tracked by the system"""
    INVOICES_PROCESSED = "invoices_processed"
    API_CALLS = "api_calls"
    STORAGE_USAGE = "storage_usage"
    USER_ACCOUNTS = "user_accounts"
    WEBHOOK_CALLS = "webhook_calls"
    BATCH_OPERATIONS = "batch_operations"
    DATA_EXPORTS = "data_exports"


class UsageAlertType(str, Enum):
    """Types of usage alerts"""
    WARNING = "warning"          # 80% of limit
    CRITICAL = "critical"        # 95% of limit
    LIMIT_EXCEEDED = "limit_exceeded"  # 100%+ of limit
    OVERAGE = "overage"          # Billable overage charges


class UsageEnforcementAction(str, Enum):
    """Actions taken when limits are exceeded"""
    LOG_ONLY = "log_only"
    THROTTLE = "throttle"
    BLOCK = "block"
    CHARGE_OVERAGE = "charge_overage"
    UPGRADE_SUGGESTION = "upgrade_suggestion"


@dataclass
class UsageSnapshot:
    """Point-in-time usage snapshot"""
    snapshot_id: str
    tenant_id: UUID
    organization_id: UUID
    timestamp: datetime
    billing_period_start: datetime
    billing_period_end: datetime
    usage_data: Dict[UsageMetric, float]
    tier_limits: Dict[UsageMetric, float]
    usage_percentages: Dict[UsageMetric, float]
    overage_amounts: Dict[UsageMetric, float]
    projected_monthly_usage: Dict[UsageMetric, float]


@dataclass
class UsageAlert:
    """Usage limit alert"""
    alert_id: str
    tenant_id: UUID
    organization_id: UUID
    metric: UsageMetric
    alert_type: UsageAlertType
    current_usage: float
    limit: float
    percentage: float
    message: str
    enforcement_action: UsageEnforcementAction
    created_at: datetime
    resolved_at: Optional[datetime] = None


@dataclass
class UsageProjection:
    """Usage projection analytics"""
    tenant_id: UUID
    metric: UsageMetric
    current_usage: float
    current_limit: float
    projected_end_of_month: float
    projected_overage: float
    confidence_score: float
    recommended_tier: Optional[SubscriptionTier]
    estimated_overage_cost: Decimal
    calculated_at: datetime


class UsageTracker:
    """Real-time usage tracking and enforcement system"""
    
    def __init__(self):
        self.billing_repository = BillingRepository()
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Usage data registries
        self.usage_snapshots: Dict[str, UsageSnapshot] = {}
        self.usage_alerts: Dict[str, UsageAlert] = {}
        self.usage_projections: Dict[str, UsageProjection] = {}
        
        # Configuration
        self.config = {
            "alert_thresholds": {
                UsageAlertType.WARNING: 0.80,
                UsageAlertType.CRITICAL: 0.95,
                UsageAlertType.LIMIT_EXCEEDED: 1.00
            },
            "enforcement_rules": {
                UsageMetric.INVOICES_PROCESSED: UsageEnforcementAction.CHARGE_OVERAGE,
                UsageMetric.API_CALLS: UsageEnforcementAction.THROTTLE,
                UsageMetric.STORAGE_USAGE: UsageEnforcementAction.BLOCK,
                UsageMetric.USER_ACCOUNTS: UsageEnforcementAction.BLOCK,
                UsageMetric.WEBHOOK_CALLS: UsageEnforcementAction.THROTTLE,
                UsageMetric.BATCH_OPERATIONS: UsageEnforcementAction.CHARGE_OVERAGE,
                UsageMetric.DATA_EXPORTS: UsageEnforcementAction.THROTTLE
            },
            "snapshot_interval_minutes": 15,
            "projection_update_interval_hours": 6,
            "cache_ttl_seconds": 300  # 5 minutes
        }
    
    async def record_usage(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        metric: UsageMetric,
        amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record usage and check against limits"""
        try:
            # Get current subscription
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            # Record usage in billing repository
            usage_recorded = await self.billing_repository.record_usage(
                tenant_id=tenant_id,
                organization_id=organization_id,
                **{metric.value: amount},
                feature_usage=metadata or {}
            )
            
            if not usage_recorded:
                return {"status": "error", "message": "Failed to record usage"}
            
            # Get current usage totals
            current_usage = await self.get_current_usage(tenant_id)
            
            # Check limits and trigger alerts if needed
            limit_check_result = await self._check_usage_limits(
                tenant_id, organization_id, metric, current_usage
            )
            
            # Update cache
            await self._update_usage_cache(tenant_id, current_usage)
            
            # Emit usage event
            await self.event_bus.emit("usage_recorded", {
                "tenant_id": str(tenant_id),
                "organization_id": str(organization_id),
                "metric": metric.value,
                "amount": amount,
                "limit_check": limit_check_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.debug(f"Usage recorded for {tenant_id}: {metric.value} = {amount}")
            
            return {
                "status": "success",
                "usage_recorded": amount,
                "current_total": current_usage.get(metric.value, 0),
                "limit_check": limit_check_result
            }
            
        except Exception as e:
            self.logger.error(f"Error recording usage for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_current_usage(self, tenant_id: UUID) -> Dict[str, float]:
        """Get current billing period usage totals"""
        try:
            # Check cache first
            cache_key = f"current_usage:{tenant_id}"
            cached_usage = await self.cache_service.get(cache_key)
            if cached_usage:
                return cached_usage
            
            # Calculate current billing period
            billing_period = await self._get_current_billing_period(tenant_id)
            
            # Get usage statistics
            usage_stats = await self.billing_repository.get_usage_stats(
                tenant_id, 
                billing_period["start"], 
                billing_period["end"]
            )
            
            # Format usage data
            current_usage = {
                UsageMetric.INVOICES_PROCESSED.value: usage_stats.get("total_invoices", 0),
                UsageMetric.API_CALLS.value: usage_stats.get("total_api_calls", 0),
                UsageMetric.STORAGE_USAGE.value: usage_stats.get("avg_storage_usage", 0),
                UsageMetric.USER_ACCOUNTS.value: await self._get_user_count(tenant_id),
                UsageMetric.WEBHOOK_CALLS.value: await self._get_webhook_usage(tenant_id, billing_period),
                UsageMetric.BATCH_OPERATIONS.value: await self._get_batch_usage(tenant_id, billing_period),
                UsageMetric.DATA_EXPORTS.value: await self._get_export_usage(tenant_id, billing_period)
            }
            
            # Cache for 5 minutes
            await self.cache_service.set(cache_key, current_usage, ttl=self.config["cache_ttl_seconds"])
            
            return current_usage
            
        except Exception as e:
            self.logger.error(f"Error getting current usage for {tenant_id}: {str(e)}")
            return {}
    
    async def get_usage_snapshot(
        self, 
        tenant_id: UUID,
        organization_id: UUID
    ) -> Optional[UsageSnapshot]:
        """Generate comprehensive usage snapshot"""
        try:
            # Get subscription details
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return None
            
            tier = SubscriptionTier(subscription["subscription_tier"])
            tier_limits = self._get_tier_limits(tier)
            
            # Get current usage
            current_usage = await self.get_current_usage(tenant_id)
            
            # Calculate usage percentages
            usage_percentages = {}
            overage_amounts = {}
            for metric_str, usage_value in current_usage.items():
                metric = UsageMetric(metric_str)
                limit = tier_limits.get(metric, float('inf'))
                
                if limit > 0:
                    percentage = (usage_value / limit) * 100
                    overage = max(0, usage_value - limit)
                else:
                    percentage = 0
                    overage = 0
                
                usage_percentages[metric] = percentage
                overage_amounts[metric] = overage
            
            # Calculate projections
            projected_usage = await self._calculate_projected_usage(tenant_id, current_usage)
            
            # Get billing period
            billing_period = await self._get_current_billing_period(tenant_id)
            
            snapshot = UsageSnapshot(
                snapshot_id=str(uuid4()),
                tenant_id=tenant_id,
                organization_id=organization_id,
                timestamp=datetime.now(timezone.utc),
                billing_period_start=billing_period["start"],
                billing_period_end=billing_period["end"],
                usage_data={UsageMetric(k): v for k, v in current_usage.items()},
                tier_limits=tier_limits,
                usage_percentages=usage_percentages,
                overage_amounts=overage_amounts,
                projected_monthly_usage={UsageMetric(k): v for k, v in projected_usage.items()}
            )
            
            # Store snapshot
            self.usage_snapshots[snapshot.snapshot_id] = snapshot
            
            # Cache snapshot
            await self.cache_service.set(
                f"usage_snapshot:{tenant_id}",
                asdict(snapshot),
                ttl=self.config["snapshot_interval_minutes"] * 60
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error generating usage snapshot for {tenant_id}: {str(e)}")
            return None
    
    async def check_usage_compliance(self, tenant_id: UUID) -> Dict[str, Any]:
        """Check compliance with subscription tier limits"""
        try:
            snapshot = await self.get_usage_snapshot(tenant_id, None)  # Will get from subscription
            if not snapshot:
                return {"status": "error", "message": "Unable to generate usage snapshot"}
            
            compliance_results = {}
            violations = []
            warnings = []
            
            for metric, usage_pct in snapshot.usage_percentages.items():
                limit = snapshot.tier_limits.get(metric, float('inf'))
                current_usage = snapshot.usage_data.get(metric, 0)
                
                compliance_status = "compliant"
                if usage_pct >= 100:
                    compliance_status = "violation"
                    violations.append({
                        "metric": metric.value,
                        "usage": current_usage,
                        "limit": limit,
                        "percentage": usage_pct,
                        "overage": snapshot.overage_amounts.get(metric, 0)
                    })
                elif usage_pct >= 80:
                    compliance_status = "warning"
                    warnings.append({
                        "metric": metric.value,
                        "usage": current_usage,
                        "limit": limit,
                        "percentage": usage_pct
                    })
                
                compliance_results[metric.value] = {
                    "status": compliance_status,
                    "usage": current_usage,
                    "limit": limit,
                    "percentage": round(usage_pct, 2)
                }
            
            overall_compliance = "compliant"
            if violations:
                overall_compliance = "violation"
            elif warnings:
                overall_compliance = "warning"
            
            return {
                "status": "success",
                "overall_compliance": overall_compliance,
                "compliance_details": compliance_results,
                "violations": violations,
                "warnings": warnings,
                "snapshot_id": snapshot.snapshot_id,
                "checked_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error checking usage compliance for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_usage_projections(self, tenant_id: UUID) -> List[UsageProjection]:
        """Get usage projections for all metrics"""
        try:
            current_usage = await self.get_current_usage(tenant_id)
            subscription = await self.billing_repository.get_subscription(tenant_id)
            
            if not subscription:
                return []
            
            tier = SubscriptionTier(subscription["subscription_tier"])
            tier_limits = self._get_tier_limits(tier)
            
            projections = []
            
            for metric_str, current_value in current_usage.items():
                metric = UsageMetric(metric_str)
                limit = tier_limits.get(metric, float('inf'))
                
                # Calculate projection
                projection = await self._calculate_usage_projection(
                    tenant_id, metric, current_value, limit
                )
                
                if projection:
                    projections.append(projection)
                    self.usage_projections[f"{tenant_id}:{metric.value}"] = projection
            
            return projections
            
        except Exception as e:
            self.logger.error(f"Error getting usage projections for {tenant_id}: {str(e)}")
            return []
    
    async def enforce_usage_limits(
        self,
        tenant_id: UUID,
        metric: UsageMetric,
        current_usage: float,
        limit: float
    ) -> Dict[str, Any]:
        """Enforce usage limits based on configured rules"""
        try:
            enforcement_action = self.config["enforcement_rules"].get(
                metric, UsageEnforcementAction.LOG_ONLY
            )
            
            if current_usage <= limit:
                return {
                    "action_taken": "none",
                    "reason": "within_limits"
                }
            
            overage_amount = current_usage - limit
            
            if enforcement_action == UsageEnforcementAction.LOG_ONLY:
                self.logger.warning(f"Usage limit exceeded for {tenant_id}: {metric.value}")
                return {
                    "action_taken": "log_only",
                    "overage_amount": overage_amount
                }
            
            elif enforcement_action == UsageEnforcementAction.THROTTLE:
                # Implement throttling logic
                throttle_result = await self._apply_throttling(tenant_id, metric, overage_amount)
                return {
                    "action_taken": "throttle",
                    "throttle_config": throttle_result,
                    "overage_amount": overage_amount
                }
            
            elif enforcement_action == UsageEnforcementAction.BLOCK:
                # Block further usage
                block_result = await self._apply_blocking(tenant_id, metric)
                return {
                    "action_taken": "block",
                    "block_config": block_result,
                    "overage_amount": overage_amount
                }
            
            elif enforcement_action == UsageEnforcementAction.CHARGE_OVERAGE:
                # Calculate overage charges
                overage_cost = await self._calculate_overage_charges(tenant_id, metric, overage_amount)
                return {
                    "action_taken": "charge_overage",
                    "overage_amount": overage_amount,
                    "overage_cost": float(overage_cost)
                }
            
            elif enforcement_action == UsageEnforcementAction.UPGRADE_SUGGESTION:
                # Suggest upgrade
                upgrade_suggestion = await self._generate_upgrade_suggestion(tenant_id, metric, current_usage)
                return {
                    "action_taken": "upgrade_suggestion",
                    "suggestion": upgrade_suggestion,
                    "overage_amount": overage_amount
                }
            
            return {
                "action_taken": "unknown",
                "overage_amount": overage_amount
            }
            
        except Exception as e:
            self.logger.error(f"Error enforcing usage limits for {tenant_id}: {str(e)}")
            return {"action_taken": "error", "error": str(e)}
    
    async def get_usage_analytics(
        self, 
        tenant_id: UUID,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=time_range_days)
            
            # Get usage trends
            usage_trends = await self._calculate_usage_trends(tenant_id, start_date, end_date)
            
            # Get current snapshot
            snapshot = await self.get_usage_snapshot(tenant_id, None)
            
            # Get projections
            projections = await self.get_usage_projections(tenant_id)
            
            # Get recent alerts
            recent_alerts = await self._get_recent_alerts(tenant_id, 7)  # Last 7 days
            
            # Calculate efficiency metrics
            efficiency_metrics = await self._calculate_efficiency_metrics(tenant_id, usage_trends)
            
            return {
                "tenant_id": str(tenant_id),
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_range_days
                },
                "current_snapshot": asdict(snapshot) if snapshot else None,
                "usage_trends": usage_trends,
                "projections": [asdict(p) for p in projections],
                "recent_alerts": [asdict(a) for a in recent_alerts],
                "efficiency_metrics": efficiency_metrics,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating usage analytics for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # Private helper methods
    
    async def _check_usage_limits(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        metric: UsageMetric,
        current_usage: Dict[str, float]
    ) -> Dict[str, Any]:
        """Check if usage exceeds limits and trigger alerts"""
        try:
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {"status": "error", "message": "No subscription found"}
            
            tier = SubscriptionTier(subscription["subscription_tier"])
            tier_limits = self._get_tier_limits(tier)
            
            limit = tier_limits.get(metric, float('inf'))
            usage_value = current_usage.get(metric.value, 0)
            
            if limit == float('inf'):
                return {"status": "unlimited", "metric": metric.value}
            
            usage_percentage = (usage_value / limit) * 100
            
            # Check alert thresholds
            alerts_triggered = []
            
            for alert_type, threshold in self.config["alert_thresholds"].items():
                if usage_percentage >= (threshold * 100):
                    alert = await self._create_usage_alert(
                        tenant_id, organization_id, metric, alert_type,
                        usage_value, limit, usage_percentage
                    )
                    alerts_triggered.append(asdict(alert))
            
            # Apply enforcement if over limit
            enforcement_result = None
            if usage_percentage >= 100:
                enforcement_result = await self.enforce_usage_limits(
                    tenant_id, metric, usage_value, limit
                )
            
            return {
                "status": "checked",
                "metric": metric.value,
                "usage": usage_value,
                "limit": limit,
                "percentage": round(usage_percentage, 2),
                "alerts_triggered": alerts_triggered,
                "enforcement": enforcement_result
            }
            
        except Exception as e:
            self.logger.error(f"Error checking usage limits: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def _create_usage_alert(
        self,
        tenant_id: UUID,
        organization_id: UUID,
        metric: UsageMetric,
        alert_type: UsageAlertType,
        current_usage: float,
        limit: float,
        percentage: float
    ) -> UsageAlert:
        """Create and send usage alert"""
        try:
            alert = UsageAlert(
                alert_id=str(uuid4()),
                tenant_id=tenant_id,
                organization_id=organization_id,
                metric=metric,
                alert_type=alert_type,
                current_usage=current_usage,
                limit=limit,
                percentage=percentage,
                message=self._generate_alert_message(metric, alert_type, percentage),
                enforcement_action=self.config["enforcement_rules"].get(
                    metric, UsageEnforcementAction.LOG_ONLY
                ),
                created_at=datetime.now(timezone.utc)
            )
            
            # Store alert
            self.usage_alerts[alert.alert_id] = alert
            
            # Send notification
            await self.notification_service.send_system_notification(
                user_id=f"tenant:{tenant_id}",
                title=f"Usage Alert: {metric.value}",
                message=alert.message,
                priority="high" if alert_type == UsageAlertType.LIMIT_EXCEEDED else "medium",
                metadata={
                    "alert_id": alert.alert_id,
                    "metric": metric.value,
                    "alert_type": alert_type.value,
                    "usage_percentage": percentage
                }
            )
            
            # Emit event
            await self.event_bus.emit("usage_alert_created", {
                "alert_id": alert.alert_id,
                "tenant_id": str(tenant_id),
                "metric": metric.value,
                "alert_type": alert_type.value,
                "percentage": percentage,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return alert
            
        except Exception as e:
            self.logger.error(f"Error creating usage alert: {str(e)}")
            raise
    
    def _get_tier_limits(self, tier: SubscriptionTier) -> Dict[UsageMetric, float]:
        """Get usage limits for subscription tier"""
        plan = self.billing_repository.SUBSCRIPTION_TIERS[tier]
        
        return {
            UsageMetric.INVOICES_PROCESSED: plan.invoice_limit,
            UsageMetric.API_CALLS: plan.api_rate_limit * 30 * 24 * 60,  # Monthly limit
            UsageMetric.STORAGE_USAGE: plan.storage_gb * 1024,  # MB
            UsageMetric.USER_ACCOUNTS: plan.user_limit,
            UsageMetric.WEBHOOK_CALLS: plan.invoice_limit * 2,  # 2x invoice limit
            UsageMetric.BATCH_OPERATIONS: plan.invoice_limit // 10,  # 10% of invoice limit
            UsageMetric.DATA_EXPORTS: 50 if tier == SubscriptionTier.STARTER else 200  # Basic export limit
        }
    
    def _generate_alert_message(
        self, 
        metric: UsageMetric, 
        alert_type: UsageAlertType, 
        percentage: float
    ) -> str:
        """Generate user-friendly alert message"""
        metric_display = metric.value.replace('_', ' ').title()
        
        if alert_type == UsageAlertType.WARNING:
            return f"Warning: {metric_display} usage is at {percentage:.1f}% of your subscription limit."
        elif alert_type == UsageAlertType.CRITICAL:
            return f"Critical: {metric_display} usage is at {percentage:.1f}% of your subscription limit. Consider upgrading."
        elif alert_type == UsageAlertType.LIMIT_EXCEEDED:
            return f"Limit Exceeded: {metric_display} usage has exceeded your subscription limit ({percentage:.1f}%)."
        elif alert_type == UsageAlertType.OVERAGE:
            return f"Overage Charges: {metric_display} usage has exceeded limits and overage charges apply."
        else:
            return f"Usage Alert: {metric_display} - {percentage:.1f}% of limit"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for usage tracker"""
        try:
            return {
                "status": "healthy",
                "service": "usage_tracker",
                "usage_snapshots": len(self.usage_snapshots),
                "active_alerts": len([a for a in self.usage_alerts.values() if not a.resolved_at]),
                "projections": len(self.usage_projections),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "usage_tracker",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_usage_tracker() -> UsageTracker:
    """Create usage tracker instance"""
    return UsageTracker()