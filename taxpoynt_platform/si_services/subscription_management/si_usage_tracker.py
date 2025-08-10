"""
SI Usage Tracker - Track SI-specific usage metrics

This module provides comprehensive usage tracking for SI services,
integrating with the platform usage tracker while adding SI-specific
metrics and business logic.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from decimal import Decimal

from .si_tier_manager import SIUsageType, SITierManager
from ...hybrid_services.billing_orchestration.usage_tracker import UsageTracker
from ...core_platform.monitoring import MetricsCollector
from ...core_platform.data_management.cache_manager import CacheManager

logger = logging.getLogger(__name__)


@dataclass
class SIUsageMetrics:
    """SI-specific usage metrics"""
    organization_id: str
    period_start: datetime
    period_end: datetime
    
    # Core metrics
    invoices_processed: int = 0
    api_calls_made: int = 0
    storage_used_gb: float = 0.0
    user_accounts_active: int = 0
    
    # SI-specific metrics
    erp_connections_active: int = 0
    certificate_requests_made: int = 0
    bulk_operations_performed: int = 0
    webhook_calls_sent: int = 0
    support_requests_opened: int = 0
    
    # Processing metrics
    successful_irn_generations: int = 0
    failed_irn_generations: int = 0
    data_extractions_performed: int = 0
    document_transformations: int = 0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    peak_concurrent_users: int = 0
    uptime_percentage: float = 100.0
    
    # Business metrics
    revenue_generated: Decimal = Decimal("0.00")
    overage_charges: Decimal = Decimal("0.00")
    cost_per_invoice: Decimal = Decimal("0.00")


@dataclass
class SIUsageAlert:
    """SI usage alert information"""
    alert_id: str
    organization_id: str
    usage_type: SIUsageType
    threshold_percentage: float
    current_usage: int
    limit: int
    alert_level: str  # warning, critical, exceeded
    triggered_at: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SIUsageTracker:
    """
    Comprehensive usage tracking for SI services with real-time monitoring,
    alerting, and integration with billing systems.
    """
    
    def __init__(
        self,
        si_tier_manager: SITierManager,
        usage_tracker: UsageTracker,
        metrics_collector: MetricsCollector,
        cache_manager: CacheManager,
        config: Optional[Dict[str, Any]] = None
    ):
        self.si_tier_manager = si_tier_manager
        self.usage_tracker = usage_tracker
        self.metrics_collector = metrics_collector
        self.cache_manager = cache_manager
        self.config = config or {}
        
        # Configuration
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5 minutes
        self.alert_thresholds = self.config.get("alert_thresholds", {
            "warning": 0.8,   # 80%
            "critical": 0.95, # 95%
            "exceeded": 1.0   # 100%
        })
        self.enable_real_time_alerts = self.config.get("enable_real_time_alerts", True)
        
        # Usage aggregation periods
        self.aggregation_periods = ["hour", "day", "week", "month"]
    
    async def record_si_usage(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        amount: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record SI-specific usage with real-time validation and alerting"""
        try:
            # Record in platform usage tracker
            await self.usage_tracker.record_usage(
                organization_id=organization_id,
                action=usage_type.value,
                resource="si_service",
                amount=amount,
                metadata=metadata or {}
            )
            
            # Update SI-specific usage cache
            await self._update_usage_cache(organization_id, usage_type, amount)
            
            # Check for usage threshold alerts
            if self.enable_real_time_alerts:
                await self._check_usage_alerts(organization_id, usage_type)
            
            # Record metrics
            await self.metrics_collector.record_counter(
                "si_usage_recorded",
                tags={
                    "organization_id": organization_id,
                    "usage_type": usage_type.value
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording SI usage for {organization_id}: {e}")
            return False
    
    async def get_current_usage(
        self,
        organization_id: str,
        usage_type: Optional[SIUsageType] = None,
        period: str = "month"
    ) -> Dict[str, Any]:
        """Get current usage for organization"""
        try:
            # Calculate period boundaries
            start_time, end_time = self._get_period_boundaries(period)
            
            if usage_type:
                # Get specific usage type
                usage = await self._get_usage_for_type(
                    organization_id, usage_type, start_time, end_time
                )
                return {usage_type.value: usage}
            else:
                # Get all usage types
                all_usage = {}
                for ut in SIUsageType:
                    usage = await self._get_usage_for_type(
                        organization_id, ut, start_time, end_time
                    )
                    all_usage[ut.value] = usage
                
                return all_usage
                
        except Exception as e:
            logger.error(f"Error getting current usage for {organization_id}: {e}")
            return {}
    
    async def get_usage_metrics(
        self,
        organization_id: str,
        period: str = "month"
    ) -> SIUsageMetrics:
        """Get comprehensive usage metrics for organization"""
        try:
            start_time, end_time = self._get_period_boundaries(period)
            
            # Get all usage data
            usage_data = await self.get_current_usage(organization_id, period=period)
            
            # Get tier config for cost calculations
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            
            # Calculate derived metrics
            total_invoices = usage_data.get(SIUsageType.INVOICES_PROCESSED.value, 0)
            total_api_calls = usage_data.get(SIUsageType.API_CALLS.value, 0)
            
            # Calculate costs
            revenue_generated = Decimal("0.00")
            overage_charges = Decimal("0.00")
            cost_per_invoice = Decimal("0.00")
            
            if tier_config and total_invoices > 0:
                base_revenue = tier_config.monthly_price
                
                # Calculate overage charges
                if total_invoices > tier_config.limits.invoices_per_month:
                    overage_amount = total_invoices - tier_config.limits.invoices_per_month
                    overage_charges = overage_amount * tier_config.overage_rate
                
                revenue_generated = base_revenue + overage_charges
                cost_per_invoice = revenue_generated / total_invoices if total_invoices > 0 else Decimal("0.00")
            
            # Get performance metrics
            performance_data = await self._get_performance_metrics(
                organization_id, start_time, end_time
            )
            
            return SIUsageMetrics(
                organization_id=organization_id,
                period_start=start_time,
                period_end=end_time,
                invoices_processed=usage_data.get(SIUsageType.INVOICES_PROCESSED.value, 0),
                api_calls_made=usage_data.get(SIUsageType.API_CALLS.value, 0),
                storage_used_gb=usage_data.get(SIUsageType.STORAGE_USAGE.value, 0) / 1024,  # Convert MB to GB
                user_accounts_active=usage_data.get(SIUsageType.USER_ACCOUNTS.value, 0),
                erp_connections_active=usage_data.get(SIUsageType.ERP_CONNECTIONS.value, 0),
                certificate_requests_made=usage_data.get(SIUsageType.CERTIFICATE_REQUESTS.value, 0),
                bulk_operations_performed=usage_data.get(SIUsageType.BULK_OPERATIONS.value, 0),
                webhook_calls_sent=usage_data.get(SIUsageType.WEBHOOK_CALLS.value, 0),
                support_requests_opened=usage_data.get(SIUsageType.SUPPORT_REQUESTS.value, 0),
                successful_irn_generations=performance_data.get("successful_irn", 0),
                failed_irn_generations=performance_data.get("failed_irn", 0),
                data_extractions_performed=performance_data.get("data_extractions", 0),
                document_transformations=performance_data.get("document_transforms", 0),
                average_processing_time_ms=performance_data.get("avg_processing_time", 0.0),
                peak_concurrent_users=performance_data.get("peak_users", 0),
                uptime_percentage=performance_data.get("uptime", 100.0),
                revenue_generated=revenue_generated,
                overage_charges=overage_charges,
                cost_per_invoice=cost_per_invoice
            )
            
        except Exception as e:
            logger.error(f"Error getting usage metrics for {organization_id}: {e}")
            return SIUsageMetrics(
                organization_id=organization_id,
                period_start=datetime.now(timezone.utc),
                period_end=datetime.now(timezone.utc)
            )
    
    async def get_usage_trends(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        periods: int = 12
    ) -> List[Dict[str, Any]]:
        """Get usage trends over multiple periods"""
        try:
            trends = []
            current_date = datetime.now(timezone.utc)
            
            for i in range(periods):
                # Calculate period start (going backwards)
                period_start = current_date.replace(day=1) - timedelta(days=32 * i)
                period_start = period_start.replace(day=1)
                
                # Calculate period end
                if period_start.month == 12:
                    period_end = period_start.replace(year=period_start.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=period_start.month + 1)
                
                # Get usage for this period
                usage = await self._get_usage_for_type(
                    organization_id, usage_type, period_start, period_end
                )
                
                trends.append({
                    "period": period_start.strftime("%Y-%m"),
                    "usage": usage,
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat()
                })
            
            # Reverse to get chronological order
            return list(reversed(trends))
            
        except Exception as e:
            logger.error(f"Error getting usage trends for {organization_id}: {e}")
            return []
    
    async def predict_usage(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        periods_ahead: int = 3
    ) -> List[Dict[str, Any]]:
        """Predict future usage based on historical trends"""
        try:
            # Get historical data
            historical_trends = await self.get_usage_trends(
                organization_id, usage_type, periods=6
            )
            
            if len(historical_trends) < 3:
                return []  # Not enough data for prediction
            
            # Simple linear regression for prediction
            usage_values = [trend["usage"] for trend in historical_trends]
            
            # Calculate trend
            if len(usage_values) >= 2:
                recent_avg = sum(usage_values[-3:]) / 3
                older_avg = sum(usage_values[:3]) / 3
                growth_rate = (recent_avg - older_avg) / len(usage_values) if older_avg > 0 else 0
            else:
                growth_rate = 0
            
            # Generate predictions
            predictions = []
            last_usage = usage_values[-1] if usage_values else 0
            
            for i in range(1, periods_ahead + 1):
                predicted_usage = max(0, int(last_usage + (growth_rate * i)))
                
                # Calculate period date
                current_date = datetime.now(timezone.utc)
                future_date = current_date + timedelta(days=30 * i)
                
                predictions.append({
                    "period": future_date.strftime("%Y-%m"),
                    "predicted_usage": predicted_usage,
                    "confidence": max(0.3, 1.0 - (i * 0.2)),  # Decreasing confidence
                    "growth_rate": growth_rate
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting usage for {organization_id}: {e}")
            return []
    
    async def get_usage_analytics(
        self,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive usage analytics and insights"""
        try:
            # Get current month metrics
            current_metrics = await self.get_usage_metrics(organization_id, "month")
            
            # Get tier configuration
            tier_config = await self.si_tier_manager.get_organization_si_tier(organization_id)
            
            if not tier_config:
                return {"error": "No tier configuration found"}
            
            # Calculate utilization percentages
            utilization = {
                "invoices": (current_metrics.invoices_processed / tier_config.limits.invoices_per_month) * 100,
                "api_calls": (current_metrics.api_calls_made / (tier_config.limits.api_calls_per_minute * 60 * 24 * 30)) * 100,
                "storage": (current_metrics.storage_used_gb / tier_config.limits.storage_gb) * 100,
                "users": (current_metrics.user_accounts_active / tier_config.limits.users) * 100,
                "erp_connections": (current_metrics.erp_connections_active / tier_config.limits.erp_connections) * 100
            }
            
            # Get usage trends
            invoice_trends = await self.get_usage_trends(
                organization_id, SIUsageType.INVOICES_PROCESSED, 6
            )
            
            # Get predictions
            invoice_predictions = await self.predict_usage(
                organization_id, SIUsageType.INVOICES_PROCESSED, 3
            )
            
            # Calculate insights
            insights = self._generate_usage_insights(
                current_metrics, tier_config, utilization, invoice_trends
            )
            
            return {
                "current_metrics": asdict(current_metrics),
                "tier_info": {
                    "tier": tier_config.tier.value,
                    "monthly_price": float(tier_config.monthly_price),
                    "limits": asdict(tier_config.limits)
                },
                "utilization": utilization,
                "trends": invoice_trends,
                "predictions": invoice_predictions,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Error getting usage analytics for {organization_id}: {e}")
            return {"error": f"Analytics error: {str(e)}"}
    
    async def _update_usage_cache(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        amount: int
    ):
        """Update usage cache for real-time tracking"""
        for period in self.aggregation_periods:
            cache_key = f"si_usage:{organization_id}:{usage_type.value}:{period}"
            
            # Get current cached value
            current_usage = await self.cache_manager.get(cache_key) or 0
            new_usage = current_usage + amount
            
            # Calculate TTL based on period
            ttl = self._get_cache_ttl(period)
            
            await self.cache_manager.set(cache_key, new_usage, ttl=ttl)
    
    async def _check_usage_alerts(
        self,
        organization_id: str,
        usage_type: SIUsageType
    ):
        """Check and trigger usage threshold alerts"""
        try:
            # Get current usage and limits
            usage_check = await self.si_tier_manager.check_si_usage_limits(
                organization_id, usage_type, 0
            )
            
            if not usage_check.get("limit"):
                return
            
            current_usage = usage_check.get("current_usage", 0)
            limit = usage_check.get("limit", 1)
            usage_percentage = current_usage / limit
            
            # Check thresholds
            alert_level = None
            if usage_percentage >= self.alert_thresholds["exceeded"]:
                alert_level = "exceeded"
            elif usage_percentage >= self.alert_thresholds["critical"]:
                alert_level = "critical"
            elif usage_percentage >= self.alert_thresholds["warning"]:
                alert_level = "warning"
            
            if alert_level:
                # Check if alert was already sent recently
                alert_cache_key = f"si_usage_alert:{organization_id}:{usage_type.value}:{alert_level}"
                if not await self.cache_manager.get(alert_cache_key):
                    
                    # Create and send alert
                    alert = SIUsageAlert(
                        alert_id=f"{organization_id}_{usage_type.value}_{int(datetime.now().timestamp())}",
                        organization_id=organization_id,
                        usage_type=usage_type,
                        threshold_percentage=usage_percentage * 100,
                        current_usage=current_usage,
                        limit=limit,
                        alert_level=alert_level,
                        triggered_at=datetime.now(timezone.utc)
                    )
                    
                    await self._send_usage_alert(alert)
                    
                    # Cache alert to prevent spam (5 minute cooldown)
                    await self.cache_manager.set(alert_cache_key, True, ttl=300)
                    
        except Exception as e:
            logger.error(f"Error checking usage alerts for {organization_id}: {e}")
    
    async def _get_usage_for_type(
        self,
        organization_id: str,
        usage_type: SIUsageType,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Get usage for specific type and time period"""
        # Try cache first for recent periods
        if (datetime.now(timezone.utc) - end_time).days <= 1:
            cache_key = f"si_usage:{organization_id}:{usage_type.value}:day"
            cached_usage = await self.cache_manager.get(cache_key)
            if cached_usage is not None:
                return int(cached_usage)
        
        # Get from usage tracker
        usage = await self.usage_tracker.get_usage_for_period(
            organization_id, usage_type.value, start_time, end_time
        )
        
        return usage or 0
    
    async def _get_performance_metrics(
        self,
        organization_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get performance metrics for the period"""
        # This would integrate with performance monitoring systems
        # For now, return default values
        return {
            "successful_irn": 0,
            "failed_irn": 0,
            "data_extractions": 0,
            "document_transforms": 0,
            "avg_processing_time": 0.0,
            "peak_users": 0,
            "uptime": 100.0
        }
    
    def _get_period_boundaries(self, period: str) -> tuple[datetime, datetime]:
        """Get start and end boundaries for period"""
        now = datetime.now(timezone.utc)
        
        if period == "hour":
            start = now.replace(minute=0, second=0, microsecond=0)
            end = start + timedelta(hours=1)
        elif period == "day":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "week":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start = start - timedelta(days=start.weekday())
            end = start + timedelta(weeks=1)
        elif period == "month":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        else:
            # Default to current day
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        
        return start, end
    
    def _get_cache_ttl(self, period: str) -> int:
        """Get cache TTL based on period"""
        ttl_mapping = {
            "hour": 3600,      # 1 hour
            "day": 86400,      # 1 day
            "week": 604800,    # 1 week
            "month": 2592000   # 30 days
        }
        return ttl_mapping.get(period, 3600)
    
    def _generate_usage_insights(
        self,
        metrics: SIUsageMetrics,
        tier_config: Any,
        utilization: Dict[str, float],
        trends: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate usage insights and recommendations"""
        insights = []
        
        # High utilization warnings
        for metric, percentage in utilization.items():
            if percentage > 90:
                insights.append(f"⚠️ {metric.title()} usage at {percentage:.1f}% - consider upgrading")
            elif percentage > 75:
                insights.append(f"📊 {metric.title()} usage at {percentage:.1f}% - approaching limit")
        
        # Growth trends
        if len(trends) >= 2:
            recent_usage = trends[-1]["usage"]
            previous_usage = trends[-2]["usage"]
            if recent_usage > previous_usage * 1.2:
                insights.append("📈 Invoice processing growing rapidly - plan for scaling")
        
        # Overage charges
        if metrics.overage_charges > 0:
            insights.append(f"💰 Overage charges: ${metrics.overage_charges} - upgrade to save money")
        
        # Performance insights
        if metrics.average_processing_time_ms > 5000:
            insights.append("⏱️ Processing times are high - contact support for optimization")
        
        # Efficiency insights
        if metrics.cost_per_invoice > Decimal("0.10"):
            insights.append("💡 High cost per invoice - bulk processing may be more efficient")
        
        return insights
    
    async def _send_usage_alert(self, alert: SIUsageAlert):
        """Send usage alert notification"""
        # This would integrate with notification service
        logger.info(f"Usage alert: {alert.organization_id} - {alert.usage_type.value} at {alert.threshold_percentage:.1f}%")
        
        # Record alert metric
        await self.metrics_collector.record_counter(
            "si_usage_alerts",
            tags={
                "organization_id": alert.organization_id,
                "usage_type": alert.usage_type.value,
                "alert_level": alert.alert_level
            }
        )