"""
API Gateway Monitoring System
============================
Comprehensive monitoring infrastructure for TaxPoynt's role-based API gateway.

This package provides:
- Role-specific metrics tracking (SI, APP, HYBRID)
- Performance monitoring and analysis
- Usage pattern analytics
- SLA compliance monitoring

Components:
- RoleMetricsCollector: Real-time metrics collection per role
- PerformanceTracker: API performance monitoring and alerting
- UsageAnalytics: Usage pattern analysis and insights
- SLAMonitor: SLA compliance tracking and reporting
"""

from .role_metrics import (
    RoleMetricsCollector,
    RoleMetricPoint,
    RoleMetricSummary,
    MetricType,
    TimeWindow,
    create_role_metrics_collector
)

from .performance_tracker import (
    PerformanceTracker,
    PerformanceDataPoint,
    PerformanceThreshold,
    PerformanceAlert,
    PerformanceSummary,
    PerformanceMetric,
    AlertSeverity,
    PerformanceTrend,
    PerformanceTrendAnalyzer,
    PerformanceBottleneckDetector,
    create_performance_tracker
)

from .usage_analytics import (
    UsageAnalytics,
    UsageDataPoint,
    UserUsageProfile,
    EndpointUsageAnalysis,
    UsageInsight,
    UsagePattern,
    UserBehavior,
    EndpointCategory,
    UsagePatternDetector,
    UserBehaviorAnalyzer,
    UsageInsightGenerator,
    create_usage_analytics
)

from .sla_monitor import (
    SLAMonitor,
    SLATarget,
    SLAMeasurement,
    SLAIncident,
    SLAReport,
    SLAMetricType,
    SLAStatus,
    IncidentSeverity,
    IncidentStatus,
    SLATrendAnalyzer,
    BusinessImpactCalculator,
    create_sla_monitor
)

__all__ = [
    # Role Metrics
    "RoleMetricsCollector",
    "RoleMetricPoint", 
    "RoleMetricSummary",
    "MetricType",
    "TimeWindow",
    "create_role_metrics_collector",
    
    # Performance Tracking
    "PerformanceTracker",
    "PerformanceDataPoint",
    "PerformanceThreshold",
    "PerformanceAlert",
    "PerformanceSummary",
    "PerformanceMetric",
    "AlertSeverity",
    "PerformanceTrend",
    "PerformanceTrendAnalyzer",
    "PerformanceBottleneckDetector",
    "create_performance_tracker",
    
    # Usage Analytics
    "UsageAnalytics",
    "UsageDataPoint",
    "UserUsageProfile",
    "EndpointUsageAnalysis",
    "UsageInsight",
    "UsagePattern",
    "UserBehavior",
    "EndpointCategory",
    "UsagePatternDetector",
    "UserBehaviorAnalyzer",
    "UsageInsightGenerator",
    "create_usage_analytics",
    
    # SLA Monitoring
    "SLAMonitor",
    "SLATarget",
    "SLAMeasurement", 
    "SLAIncident",
    "SLAReport",
    "SLAMetricType",
    "SLAStatus",
    "IncidentSeverity",
    "IncidentStatus",
    "SLATrendAnalyzer",
    "BusinessImpactCalculator",
    "create_sla_monitor",
]


class MonitoringStack:
    """
    Integrated Monitoring Stack
    ===========================
    
    Orchestrates all monitoring components for comprehensive API gateway monitoring.
    
    **Features:**
    - Unified monitoring interface
    - Cross-component data correlation
    - Integrated alerting and reporting
    - Performance optimization insights
    """
    
    def __init__(
        self,
        enable_role_metrics: bool = True,
        enable_performance_tracking: bool = True,
        enable_usage_analytics: bool = True,
        enable_sla_monitoring: bool = True,
        **kwargs
    ):
        self.components = {}
        
        # Initialize components based on configuration
        if enable_role_metrics:
            self.components["metrics"] = create_role_metrics_collector(**kwargs.get("metrics_config", {}))
        
        if enable_performance_tracking:
            perf_config = kwargs.get("performance_config", {})
            if "metrics_collector" not in perf_config and "metrics" in self.components:
                perf_config["metrics_collector"] = self.components["metrics"]
            self.components["performance"] = create_performance_tracker(**perf_config)
        
        if enable_usage_analytics:
            analytics_config = kwargs.get("analytics_config", {})
            if "metrics_collector" not in analytics_config and "metrics" in self.components:
                analytics_config["metrics_collector"] = self.components["metrics"]
            if "performance_tracker" not in analytics_config and "performance" in self.components:
                analytics_config["performance_tracker"] = self.components["performance"]
            self.components["analytics"] = create_usage_analytics(**analytics_config)
        
        if enable_sla_monitoring:
            sla_config = kwargs.get("sla_config", {})
            if "metrics_collector" not in sla_config and "metrics" in self.components:
                sla_config["metrics_collector"] = self.components["metrics"]
            if "performance_tracker" not in sla_config and "performance" in self.components:
                sla_config["performance_tracker"] = self.components["performance"]
            self.components["sla"] = create_sla_monitor(**sla_config)
    
    @property
    def metrics_collector(self) -> Optional[RoleMetricsCollector]:
        """Get the role metrics collector."""
        return self.components.get("metrics")
    
    @property
    def performance_tracker(self) -> Optional[PerformanceTracker]:
        """Get the performance tracker."""
        return self.components.get("performance")
    
    @property
    def usage_analytics(self) -> Optional[UsageAnalytics]:
        """Get the usage analytics component."""
        return self.components.get("analytics")
    
    @property
    def sla_monitor(self) -> Optional[SLAMonitor]:
        """Get the SLA monitor."""
        return self.components.get("sla")
    
    async def get_comprehensive_dashboard(self, role: Optional[PlatformRole] = None) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data."""
        dashboard = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role_filter": role.value if role else "all"
        }
        
        # Collect data from all components
        if self.metrics_collector:
            dashboard["real_time_metrics"] = await self.metrics_collector.get_real_time_metrics()
            if role:
                dashboard["role_metrics"] = await self.metrics_collector.get_role_metrics(role)
        
        if self.performance_tracker:
            if role:
                dashboard["performance_summary"] = await self.performance_tracker.get_performance_summary(role)
            dashboard["active_alerts"] = await self.performance_tracker.get_active_alerts(role)
        
        if self.usage_analytics:
            dashboard["real_time_usage"] = await self.usage_analytics.get_real_time_usage_dashboard()
            if role:
                dashboard["user_analytics"] = await self.usage_analytics.get_user_analytics(role=role)
        
        if self.sla_monitor:
            dashboard["sla_status"] = await self.sla_monitor.get_sla_status(role)
            dashboard["uptime_stats"] = await self.sla_monitor.get_uptime_statistics(role)
        
        return dashboard
    
    async def generate_comprehensive_report(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.WEEK
    ) -> Dict[str, Any]:
        """Generate comprehensive monitoring report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "role_filter": role.value if role else "all",
                "time_window": time_window.value
            }
        }
        
        # Collect reports from all components
        if self.metrics_collector and role:
            report["metrics_summary"] = await self.metrics_collector.get_role_metrics(role, time_window=time_window)
        
        if self.performance_tracker and role:
            report["performance_analysis"] = await self.performance_tracker.get_performance_summary(role, time_window=time_window)
            report["bottleneck_analysis"] = await self.performance_tracker.detect_performance_bottlenecks(role, time_window)
        
        if self.usage_analytics:
            report["usage_insights"] = await self.usage_analytics.get_business_intelligence(role, time_window)
            if role:
                report["user_behavior"] = await self.usage_analytics.get_user_analytics(role=role, time_window=time_window)
        
        if self.sla_monitor:
            report["sla_compliance"] = await self.sla_monitor.generate_sla_report(role=role)
        
        return report


def create_monitoring_stack(**kwargs) -> MonitoringStack:
    """Factory function to create integrated monitoring stack."""
    return MonitoringStack(**kwargs)


# For backward compatibility and easier imports
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Re-export commonly used enums and classes
from ..role_routing.models import PlatformRole