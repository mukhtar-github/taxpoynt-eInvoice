"""
Hybrid Service: Synchronization Monitor
Monitors synchronization health across the platform
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics
import time

from core_platform.database import get_db_session
from core_platform.models.sync_monitoring import SyncHealth, SyncAlert, SyncMetrics
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Synchronization status types"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    CRITICAL = "critical"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class SyncIssueType(str, Enum):
    """Types of synchronization issues"""
    LAG = "lag"
    FAILURE = "failure"
    CONFLICT = "conflict"
    TIMEOUT = "timeout"
    CONNECTIVITY = "connectivity"
    CONSISTENCY = "consistency"
    PERFORMANCE = "performance"
    CAPACITY = "capacity"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealthLevel(str, Enum):
    """Health level indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class SyncMetrics:
    """Synchronization metrics data"""
    metric_id: str
    timestamp: datetime
    sync_source: str
    sync_target: str
    lag_seconds: float
    throughput_ops_per_sec: float
    error_rate: float
    success_rate: float
    conflicts_per_hour: int
    data_volume_mb: float
    response_time_ms: float
    queue_depth: int
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncHealth:
    """Overall synchronization health"""
    health_id: str
    timestamp: datetime
    overall_status: SyncStatus
    health_level: HealthLevel
    components: Dict[str, Dict[str, Any]]
    metrics_summary: Dict[str, Any]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    uptime_percentage: float
    last_successful_sync: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncAlert:
    """Synchronization alert"""
    alert_id: str
    alert_type: SyncIssueType
    severity: AlertSeverity
    title: str
    description: str
    source_component: str
    target_component: str
    detected_at: datetime
    threshold_value: Any
    current_value: Any
    impact_assessment: Dict[str, Any]
    suggested_actions: List[str]
    auto_resolved: bool = False
    acknowledged: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SyncThreshold:
    """Threshold configuration for monitoring"""
    threshold_id: str
    name: str
    metric_type: str
    warning_threshold: float
    critical_threshold: float
    comparison_operator: str  # >, <, >=, <=, ==, !=
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SyncMonitor:
    """
    Synchronization Monitor service
    Monitors synchronization health across the platform
    """
    
    def __init__(self):
        """Initialize sync monitor service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.sync_metrics: Dict[str, List[SyncMetrics]] = {}
        self.sync_health: Dict[str, SyncHealth] = {}
        self.active_alerts: Dict[str, SyncAlert] = {}
        self.thresholds: Dict[str, SyncThreshold] = {}
        self.component_status: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.metrics_retention_hours = 24
        self.health_check_interval = 60  # 1 minute
        self.alert_cooldown_minutes = 5
        self.performance_window_minutes = 15
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
    
    def _initialize_default_thresholds(self):
        """Initialize default monitoring thresholds"""
        default_thresholds = [
            # Lag thresholds
            SyncThreshold(
                threshold_id="sync_lag_warning",
                name="Sync Lag Warning",
                metric_type="lag_seconds",
                warning_threshold=30.0,
                critical_threshold=120.0,
                comparison_operator=">"
            ),
            
            # Error rate thresholds
            SyncThreshold(
                threshold_id="error_rate_warning",
                name="Error Rate Warning",
                metric_type="error_rate",
                warning_threshold=0.05,  # 5%
                critical_threshold=0.15,  # 15%
                comparison_operator=">"
            ),
            
            # Throughput thresholds
            SyncThreshold(
                threshold_id="throughput_warning",
                name="Low Throughput Warning",
                metric_type="throughput_ops_per_sec",
                warning_threshold=10.0,
                critical_threshold=5.0,
                comparison_operator="<"
            ),
            
            # Response time thresholds
            SyncThreshold(
                threshold_id="response_time_warning",
                name="High Response Time Warning",
                metric_type="response_time_ms",
                warning_threshold=1000.0,  # 1 second
                critical_threshold=5000.0,  # 5 seconds
                comparison_operator=">"
            ),
            
            # Conflict rate thresholds
            SyncThreshold(
                threshold_id="conflict_rate_warning",
                name="High Conflict Rate Warning",
                metric_type="conflicts_per_hour",
                warning_threshold=10,
                critical_threshold=50,
                comparison_operator=">"
            ),
            
            # Queue depth thresholds
            SyncThreshold(
                threshold_id="queue_depth_warning",
                name="Queue Depth Warning",
                metric_type="queue_depth",
                warning_threshold=100,
                critical_threshold=500,
                comparison_operator=">"
            )
        ]
        
        for threshold in default_thresholds:
            self.thresholds[threshold.threshold_id] = threshold
    
    async def initialize(self):
        """Initialize the sync monitor service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing sync monitor service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._health_monitor())
            asyncio.create_task(self._metrics_collector_task())
            asyncio.create_task(self._alert_processor())
            asyncio.create_task(self._cleanup_old_data())
            
            self.is_initialized = True
            self.logger.info("Sync monitor service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing sync monitor service: {str(e)}")
            raise
    
    async def record_sync_metrics(
        self,
        sync_source: str,
        sync_target: str,
        metrics_data: Dict[str, Any]
    ) -> str:
        """Record synchronization metrics"""
        try:
            metrics = SyncMetrics(
                metric_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                sync_source=sync_source,
                sync_target=sync_target,
                lag_seconds=metrics_data.get("lag_seconds", 0.0),
                throughput_ops_per_sec=metrics_data.get("throughput_ops_per_sec", 0.0),
                error_rate=metrics_data.get("error_rate", 0.0),
                success_rate=metrics_data.get("success_rate", 100.0),
                conflicts_per_hour=metrics_data.get("conflicts_per_hour", 0),
                data_volume_mb=metrics_data.get("data_volume_mb", 0.0),
                response_time_ms=metrics_data.get("response_time_ms", 0.0),
                queue_depth=metrics_data.get("queue_depth", 0),
                metadata=metrics_data.get("metadata", {})
            )
            
            # Store metrics
            sync_key = f"{sync_source}:{sync_target}"
            if sync_key not in self.sync_metrics:
                self.sync_metrics[sync_key] = []
            
            self.sync_metrics[sync_key].append(metrics)
            
            # Cache metrics
            await self.cache.set(
                f"sync_metrics:{metrics.metric_id}",
                metrics.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Check thresholds
            await self._check_thresholds(metrics)
            
            # Emit metrics event
            await self.event_bus.emit(
                "sync.metrics_recorded",
                {
                    "metric_id": metrics.metric_id,
                    "sync_source": sync_source,
                    "sync_target": sync_target,
                    "metrics": metrics_data
                }
            )
            
            self.logger.debug(f"Recorded sync metrics for {sync_source} -> {sync_target}")
            
            return metrics.metric_id
            
        except Exception as e:
            self.logger.error(f"Error recording sync metrics: {str(e)}")
            return ""
    
    async def get_sync_health(
        self,
        sync_source: str = None,
        sync_target: str = None
    ) -> Dict[str, Any]:
        """Get current synchronization health"""
        try:
            if sync_source and sync_target:
                # Get health for specific sync pair
                sync_key = f"{sync_source}:{sync_target}"
                return await self._calculate_sync_pair_health(sync_key)
            else:
                # Get overall health
                return await self._calculate_overall_health()
                
        except Exception as e:
            self.logger.error(f"Error getting sync health: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_sync_metrics(
        self,
        sync_source: str,
        sync_target: str,
        time_range_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Get synchronization metrics for a time range"""
        try:
            sync_key = f"{sync_source}:{sync_target}"
            
            if sync_key not in self.sync_metrics:
                return []
            
            # Filter by time range
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_range_minutes)
            recent_metrics = [
                m for m in self.sync_metrics[sync_key]
                if m.timestamp >= cutoff_time
            ]
            
            # Sort by timestamp
            recent_metrics.sort(key=lambda x: x.timestamp)
            
            return [m.to_dict() for m in recent_metrics]
            
        except Exception as e:
            self.logger.error(f"Error getting sync metrics: {str(e)}")
            return []
    
    async def get_active_alerts(
        self,
        severity: AlertSeverity = None,
        component: str = None
    ) -> List[Dict[str, Any]]:
        """Get active synchronization alerts"""
        try:
            alerts = list(self.active_alerts.values())
            
            # Filter by severity
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            # Filter by component
            if component:
                alerts = [a for a in alerts if component in [a.source_component, a.target_component]]
            
            # Sort by severity and timestamp
            severity_order = {
                AlertSeverity.CRITICAL: 5,
                AlertSeverity.HIGH: 4,
                AlertSeverity.MEDIUM: 3,
                AlertSeverity.LOW: 2,
                AlertSeverity.INFO: 1
            }
            
            alerts.sort(key=lambda x: (severity_order.get(x.severity, 0), x.detected_at), reverse=True)
            
            return [a.to_dict() for a in alerts]
            
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.metadata = alert.metadata or {}
            alert.metadata["acknowledged_by"] = acknowledged_by
            alert.metadata["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            
            # Update cache
            await self.cache.set(
                f"sync_alert:{alert_id}",
                alert.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit acknowledgment event
            await self.event_bus.emit(
                "sync.alert_acknowledged",
                {
                    "alert_id": alert_id,
                    "acknowledged_by": acknowledged_by
                }
            )
            
            self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {str(e)}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            alert.resolved_at = datetime.now(timezone.utc)
            alert.metadata = alert.metadata or {}
            alert.metadata["resolved_by"] = resolved_by
            
            # Move to resolved alerts
            await self.cache.set(
                f"resolved_alert:{alert_id}",
                alert.to_dict(),
                ttl=86400  # Keep resolved alerts for 24 hours
            )
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            # Emit resolution event
            await self.event_bus.emit(
                "sync.alert_resolved",
                {
                    "alert_id": alert_id,
                    "resolved_by": resolved_by
                }
            )
            
            self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving alert: {str(e)}")
            return False
    
    async def get_performance_summary(
        self,
        time_range_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get performance summary across all sync pairs"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=time_range_minutes)
            summary = {
                "time_range_minutes": time_range_minutes,
                "sync_pairs": {},
                "overall_stats": {
                    "avg_lag_seconds": 0.0,
                    "avg_throughput": 0.0,
                    "avg_error_rate": 0.0,
                    "avg_response_time": 0.0,
                    "total_conflicts": 0,
                    "total_data_volume_mb": 0.0
                }
            }
            
            all_metrics = []
            
            for sync_key, metrics_list in self.sync_metrics.items():
                recent_metrics = [m for m in metrics_list if m.timestamp >= cutoff_time]
                
                if recent_metrics:
                    sync_summary = await self._calculate_sync_pair_summary(recent_metrics)
                    summary["sync_pairs"][sync_key] = sync_summary
                    all_metrics.extend(recent_metrics)
            
            # Calculate overall statistics
            if all_metrics:
                summary["overall_stats"]["avg_lag_seconds"] = statistics.mean([m.lag_seconds for m in all_metrics])
                summary["overall_stats"]["avg_throughput"] = statistics.mean([m.throughput_ops_per_sec for m in all_metrics])
                summary["overall_stats"]["avg_error_rate"] = statistics.mean([m.error_rate for m in all_metrics])
                summary["overall_stats"]["avg_response_time"] = statistics.mean([m.response_time_ms for m in all_metrics])
                summary["overall_stats"]["total_conflicts"] = sum([m.conflicts_per_hour for m in all_metrics])
                summary["overall_stats"]["total_data_volume_mb"] = sum([m.data_volume_mb for m in all_metrics])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting performance summary: {str(e)}")
            return {}
    
    async def _calculate_sync_pair_health(self, sync_key: str) -> Dict[str, Any]:
        """Calculate health for specific sync pair"""
        try:
            if sync_key not in self.sync_metrics:
                return {
                    "sync_key": sync_key,
                    "status": SyncStatus.UNKNOWN,
                    "health_level": HealthLevel.POOR,
                    "last_seen": None
                }
            
            # Get recent metrics (last 15 minutes)
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.performance_window_minutes)
            recent_metrics = [m for m in self.sync_metrics[sync_key] if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {
                    "sync_key": sync_key,
                    "status": SyncStatus.OFFLINE,
                    "health_level": HealthLevel.CRITICAL,
                    "last_seen": max([m.timestamp for m in self.sync_metrics[sync_key]]).isoformat() if self.sync_metrics[sync_key] else None
                }
            
            # Calculate health metrics
            avg_lag = statistics.mean([m.lag_seconds for m in recent_metrics])
            avg_error_rate = statistics.mean([m.error_rate for m in recent_metrics])
            avg_response_time = statistics.mean([m.response_time_ms for m in recent_metrics])
            max_queue_depth = max([m.queue_depth for m in recent_metrics])
            
            # Determine status and health level
            status = SyncStatus.HEALTHY
            health_level = HealthLevel.EXCELLENT
            
            # Check critical conditions
            if avg_error_rate > 0.15 or avg_lag > 120 or avg_response_time > 5000:
                status = SyncStatus.CRITICAL
                health_level = HealthLevel.CRITICAL
            elif avg_error_rate > 0.05 or avg_lag > 30 or avg_response_time > 1000:
                status = SyncStatus.DEGRADED
                health_level = HealthLevel.POOR
            elif avg_error_rate > 0.01 or avg_lag > 10 or max_queue_depth > 100:
                status = SyncStatus.DEGRADED
                health_level = HealthLevel.FAIR
            elif avg_lag > 5 or max_queue_depth > 50:
                health_level = HealthLevel.GOOD
            
            return {
                "sync_key": sync_key,
                "status": status,
                "health_level": health_level,
                "metrics": {
                    "avg_lag_seconds": avg_lag,
                    "avg_error_rate": avg_error_rate,
                    "avg_response_time_ms": avg_response_time,
                    "max_queue_depth": max_queue_depth,
                    "data_points": len(recent_metrics)
                },
                "last_seen": max([m.timestamp for m in recent_metrics]).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating sync pair health: {str(e)}")
            return {"sync_key": sync_key, "status": SyncStatus.UNKNOWN, "error": str(e)}
    
    async def _calculate_overall_health(self) -> Dict[str, Any]:
        """Calculate overall synchronization health"""
        try:
            sync_pair_healths = []
            
            for sync_key in self.sync_metrics.keys():
                health = await self._calculate_sync_pair_health(sync_key)
                sync_pair_healths.append(health)
            
            if not sync_pair_healths:
                return {
                    "overall_status": SyncStatus.UNKNOWN,
                    "health_level": HealthLevel.POOR,
                    "sync_pairs_count": 0,
                    "active_alerts": len(self.active_alerts)
                }
            
            # Determine overall status (worst status wins)
            status_priority = {
                SyncStatus.CRITICAL: 5,
                SyncStatus.FAILING: 4,
                SyncStatus.DEGRADED: 3,
                SyncStatus.OFFLINE: 2,
                SyncStatus.HEALTHY: 1,
                SyncStatus.UNKNOWN: 0
            }
            
            worst_status = max(sync_pair_healths, key=lambda x: status_priority.get(x.get("status", SyncStatus.UNKNOWN), 0))
            overall_status = worst_status.get("status", SyncStatus.UNKNOWN)
            
            # Calculate health distribution
            health_distribution = {}
            for health_level in HealthLevel:
                health_distribution[health_level.value] = len([h for h in sync_pair_healths if h.get("health_level") == health_level])
            
            # Calculate average metrics
            all_metrics = []
            for metrics_list in self.sync_metrics.values():
                cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=self.performance_window_minutes)
                recent_metrics = [m for m in metrics_list if m.timestamp >= cutoff_time]
                all_metrics.extend(recent_metrics)
            
            avg_metrics = {}
            if all_metrics:
                avg_metrics = {
                    "avg_lag_seconds": statistics.mean([m.lag_seconds for m in all_metrics]),
                    "avg_error_rate": statistics.mean([m.error_rate for m in all_metrics]),
                    "avg_throughput": statistics.mean([m.throughput_ops_per_sec for m in all_metrics]),
                    "avg_response_time_ms": statistics.mean([m.response_time_ms for m in all_metrics])
                }
            
            return {
                "overall_status": overall_status,
                "health_level": worst_status.get("health_level", HealthLevel.POOR),
                "sync_pairs_count": len(sync_pair_healths),
                "healthy_pairs": len([h for h in sync_pair_healths if h.get("status") == SyncStatus.HEALTHY]),
                "degraded_pairs": len([h for h in sync_pair_healths if h.get("status") == SyncStatus.DEGRADED]),
                "critical_pairs": len([h for h in sync_pair_healths if h.get("status") == SyncStatus.CRITICAL]),
                "health_distribution": health_distribution,
                "active_alerts": len(self.active_alerts),
                "critical_alerts": len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL]),
                "average_metrics": avg_metrics,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating overall health: {str(e)}")
            return {"overall_status": SyncStatus.UNKNOWN, "error": str(e)}
    
    async def _calculate_sync_pair_summary(self, metrics: List[SyncMetrics]) -> Dict[str, Any]:
        """Calculate summary statistics for sync pair"""
        try:
            if not metrics:
                return {}
            
            return {
                "data_points": len(metrics),
                "time_span_minutes": (max([m.timestamp for m in metrics]) - min([m.timestamp for m in metrics])).total_seconds() / 60,
                "avg_lag_seconds": statistics.mean([m.lag_seconds for m in metrics]),
                "max_lag_seconds": max([m.lag_seconds for m in metrics]),
                "avg_throughput": statistics.mean([m.throughput_ops_per_sec for m in metrics]),
                "avg_error_rate": statistics.mean([m.error_rate for m in metrics]),
                "avg_response_time_ms": statistics.mean([m.response_time_ms for m in metrics]),
                "max_response_time_ms": max([m.response_time_ms for m in metrics]),
                "total_conflicts": sum([m.conflicts_per_hour for m in metrics]),
                "total_data_volume_mb": sum([m.data_volume_mb for m in metrics]),
                "avg_queue_depth": statistics.mean([m.queue_depth for m in metrics]),
                "max_queue_depth": max([m.queue_depth for m in metrics])
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating sync pair summary: {str(e)}")
            return {}
    
    async def _check_thresholds(self, metrics: SyncMetrics):
        """Check if metrics violate any thresholds"""
        try:
            for threshold in self.thresholds.values():
                if not threshold.enabled:
                    continue
                
                # Get metric value
                metric_value = getattr(metrics, threshold.metric_type, None)
                if metric_value is None:
                    continue
                
                # Check threshold violation
                violated = False
                if threshold.comparison_operator == ">":
                    violated = metric_value > threshold.critical_threshold
                elif threshold.comparison_operator == "<":
                    violated = metric_value < threshold.critical_threshold
                elif threshold.comparison_operator == ">=":
                    violated = metric_value >= threshold.critical_threshold
                elif threshold.comparison_operator == "<=":
                    violated = metric_value <= threshold.critical_threshold
                elif threshold.comparison_operator == "==":
                    violated = metric_value == threshold.critical_threshold
                elif threshold.comparison_operator == "!=":
                    violated = metric_value != threshold.critical_threshold
                
                if violated:
                    # Determine severity
                    severity = AlertSeverity.CRITICAL
                    if threshold.comparison_operator == ">":
                        if metric_value <= threshold.warning_threshold:
                            continue  # Below warning threshold
                        elif metric_value <= threshold.critical_threshold:
                            severity = AlertSeverity.HIGH
                    elif threshold.comparison_operator == "<":
                        if metric_value >= threshold.warning_threshold:
                            continue  # Above warning threshold
                        elif metric_value >= threshold.critical_threshold:
                            severity = AlertSeverity.HIGH
                    
                    await self._create_threshold_alert(threshold, metrics, metric_value, severity)
                    
        except Exception as e:
            self.logger.error(f"Error checking thresholds: {str(e)}")
    
    async def _create_threshold_alert(
        self,
        threshold: SyncThreshold,
        metrics: SyncMetrics,
        current_value: Any,
        severity: AlertSeverity
    ):
        """Create an alert for threshold violation"""
        try:
            # Check for alert cooldown
            alert_key = f"{threshold.threshold_id}:{metrics.sync_source}:{metrics.sync_target}"
            last_alert_time = await self.cache.get(f"alert_cooldown:{alert_key}")
            
            if last_alert_time:
                last_time = datetime.fromisoformat(last_alert_time)
                if (datetime.now(timezone.utc) - last_time).total_seconds() < (self.alert_cooldown_minutes * 60):
                    return  # Still in cooldown period
            
            # Create alert
            alert = SyncAlert(
                alert_id=str(uuid.uuid4()),
                alert_type=self._map_metric_to_issue_type(threshold.metric_type),
                severity=severity,
                title=f"{threshold.name} - {metrics.sync_source} to {metrics.sync_target}",
                description=f"{threshold.metric_type} value {current_value} violates threshold {threshold.critical_threshold}",
                source_component=metrics.sync_source,
                target_component=metrics.sync_target,
                detected_at=datetime.now(timezone.utc),
                threshold_value=threshold.critical_threshold,
                current_value=current_value,
                impact_assessment=await self._assess_alert_impact(threshold, metrics),
                suggested_actions=await self._generate_suggested_actions(threshold, metrics),
                metadata={
                    "threshold_id": threshold.threshold_id,
                    "metric_id": metrics.metric_id
                }
            )
            
            # Store alert
            self.active_alerts[alert.alert_id] = alert
            
            # Cache alert
            await self.cache.set(
                f"sync_alert:{alert.alert_id}",
                alert.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Set cooldown
            await self.cache.set(
                f"alert_cooldown:{alert_key}",
                datetime.now(timezone.utc).isoformat(),
                ttl=self.alert_cooldown_minutes * 60
            )
            
            # Emit alert event
            await self.event_bus.emit(
                "sync.alert_created",
                {
                    "alert_id": alert.alert_id,
                    "severity": severity,
                    "alert_type": alert.alert_type,
                    "source": metrics.sync_source,
                    "target": metrics.sync_target
                }
            )
            
            # Send notification for critical alerts
            if severity == AlertSeverity.CRITICAL:
                await self.notification_service.send_notification(
                    type="sync_alert",
                    data=alert.to_dict()
                )
            
            self.logger.warning(f"Sync alert created: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"Error creating threshold alert: {str(e)}")
    
    def _map_metric_to_issue_type(self, metric_type: str) -> SyncIssueType:
        """Map metric type to issue type"""
        mapping = {
            "lag_seconds": SyncIssueType.LAG,
            "error_rate": SyncIssueType.FAILURE,
            "response_time_ms": SyncIssueType.PERFORMANCE,
            "throughput_ops_per_sec": SyncIssueType.PERFORMANCE,
            "conflicts_per_hour": SyncIssueType.CONFLICT,
            "queue_depth": SyncIssueType.CAPACITY
        }
        return mapping.get(metric_type, SyncIssueType.PERFORMANCE)
    
    async def _assess_alert_impact(
        self,
        threshold: SyncThreshold,
        metrics: SyncMetrics
    ) -> Dict[str, Any]:
        """Assess the impact of an alert"""
        try:
            impact = {
                "business_operations": "medium",
                "data_consistency": "medium",
                "user_experience": "low",
                "system_performance": "medium"
            }
            
            metric_type = threshold.metric_type
            
            if metric_type in ["lag_seconds", "conflicts_per_hour"]:
                impact["data_consistency"] = "high"
            
            if metric_type in ["error_rate", "throughput_ops_per_sec"]:
                impact["business_operations"] = "high"
                impact["user_experience"] = "high"
            
            if metric_type in ["response_time_ms", "queue_depth"]:
                impact["system_performance"] = "high"
                impact["user_experience"] = "medium"
            
            # Assess based on sync pair importance
            if "invoice" in metrics.sync_source.lower() or "invoice" in metrics.sync_target.lower():
                impact["business_operations"] = "critical"
            
            return impact
            
        except Exception as e:
            self.logger.error(f"Error assessing alert impact: {str(e)}")
            return {}
    
    async def _generate_suggested_actions(
        self,
        threshold: SyncThreshold,
        metrics: SyncMetrics
    ) -> List[str]:
        """Generate suggested actions for an alert"""
        try:
            actions = []
            metric_type = threshold.metric_type
            
            if metric_type == "lag_seconds":
                actions.extend([
                    "Check network connectivity between sync endpoints",
                    "Verify sync service is running and responsive",
                    "Review sync queue depth and processing capacity",
                    "Consider increasing sync frequency or batch size"
                ])
            elif metric_type == "error_rate":
                actions.extend([
                    "Review error logs for sync failures",
                    "Check authentication and authorization status",
                    "Verify data schema compatibility",
                    "Test connectivity to target system"
                ])
            elif metric_type == "response_time_ms":
                actions.extend([
                    "Check system resource utilization (CPU, memory)",
                    "Review database performance and indexes",
                    "Consider optimizing sync query performance",
                    "Check for network latency issues"
                ])
            elif metric_type == "throughput_ops_per_sec":
                actions.extend([
                    "Review sync service capacity and scaling",
                    "Check for bottlenecks in data processing pipeline",
                    "Consider increasing sync worker threads",
                    "Optimize data transformation logic"
                ])
            elif metric_type == "conflicts_per_hour":
                actions.extend([
                    "Review conflict resolution strategies",
                    "Check for concurrent access patterns",
                    "Verify data locking mechanisms",
                    "Consider adjusting sync timing to reduce conflicts"
                ])
            elif metric_type == "queue_depth":
                actions.extend([
                    "Increase sync processing capacity",
                    "Check for stuck or failed sync jobs",
                    "Review queue management configuration",
                    "Consider implementing queue prioritization"
                ])
            
            return actions
            
        except Exception as e:
            self.logger.error(f"Error generating suggested actions: {str(e)}")
            return ["Review sync configuration and logs"]
    
    async def _health_monitor(self):
        """Background health monitoring task"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Calculate overall health
                overall_health = await self._calculate_overall_health()
                
                # Store health snapshot
                health_snapshot = SyncHealth(
                    health_id=str(uuid.uuid4()),
                    timestamp=datetime.now(timezone.utc),
                    overall_status=overall_health.get("overall_status", SyncStatus.UNKNOWN),
                    health_level=overall_health.get("health_level", HealthLevel.POOR),
                    components={},  # Will be populated with component details
                    metrics_summary=overall_health.get("average_metrics", {}),
                    issues=[],  # Will be populated with current issues
                    recommendations=await self._generate_health_recommendations(overall_health),
                    uptime_percentage=await self._calculate_uptime_percentage(),
                    last_successful_sync=await self._get_last_successful_sync()
                )
                
                # Store health data
                await self.cache.set(
                    "sync_health:current",
                    health_snapshot.to_dict(),
                    ttl=self.cache_ttl
                )
                
                # Emit health update event
                await self.event_bus.emit(
                    "sync.health_updated",
                    {
                        "health_id": health_snapshot.health_id,
                        "overall_status": health_snapshot.overall_status,
                        "health_level": health_snapshot.health_level
                    }
                )
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {str(e)}")
    
    async def _metrics_collector_task(self):
        """Background metrics collection task"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Collect metrics from various sources
                # This would typically poll sync services, databases, etc.
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
            except Exception as e:
                self.logger.error(f"Error in metrics collector: {str(e)}")
    
    async def _alert_processor(self):
        """Background alert processing task"""
        while True:
            try:
                await asyncio.sleep(120)  # Every 2 minutes
                
                # Process auto-resolution for alerts
                for alert_id, alert in list(self.active_alerts.items()):
                    if await self._check_alert_auto_resolution(alert):
                        alert.auto_resolved = True
                        await self.resolve_alert(alert_id, "auto_resolver")
                
            except Exception as e:
                self.logger.error(f"Error in alert processor: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Cleanup old metrics and resolved alerts"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                await self._cleanup_old_metrics()
                await self._cleanup_resolved_alerts()
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics data"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=self.metrics_retention_hours)
            
            for sync_key in self.sync_metrics:
                self.sync_metrics[sync_key] = [
                    m for m in self.sync_metrics[sync_key]
                    if m.timestamp >= cutoff_time
                ]
            
            self.logger.debug("Cleaned up old metrics data")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up metrics: {str(e)}")
    
    async def _cleanup_resolved_alerts(self):
        """Clean up old resolved alerts from cache"""
        try:
            # This would typically clean up resolved alerts older than 24 hours
            # Implementation depends on cache key patterns
            
            self.logger.debug("Cleaned up resolved alerts")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up resolved alerts: {str(e)}")
    
    async def _check_alert_auto_resolution(self, alert: SyncAlert) -> bool:
        """Check if alert can be auto-resolved"""
        try:
            # Check if the condition that triggered the alert is no longer present
            sync_key = f"{alert.source_component}:{alert.target_component}"
            
            if sync_key not in self.sync_metrics:
                return False
            
            # Get recent metrics
            cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)
            recent_metrics = [m for m in self.sync_metrics[sync_key] if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return False
            
            # Check if threshold violation is resolved
            threshold = self.thresholds.get(alert.metadata.get("threshold_id"))
            if not threshold:
                return False
            
            latest_metric = max(recent_metrics, key=lambda x: x.timestamp)
            metric_value = getattr(latest_metric, threshold.metric_type, None)
            
            if metric_value is None:
                return False
            
            # Check if back to normal
            if threshold.comparison_operator == ">":
                return metric_value <= threshold.warning_threshold
            elif threshold.comparison_operator == "<":
                return metric_value >= threshold.warning_threshold
            # Add other operators as needed
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking alert auto-resolution: {str(e)}")
            return False
    
    async def _generate_health_recommendations(self, health_data: Dict[str, Any]) -> List[str]:
        """Generate health improvement recommendations"""
        try:
            recommendations = []
            
            if health_data.get("critical_pairs", 0) > 0:
                recommendations.append("Immediate attention required for critical sync pairs")
                recommendations.append("Review and resolve critical alerts")
            
            if health_data.get("degraded_pairs", 0) > 0:
                recommendations.append("Monitor degraded sync pairs for potential issues")
            
            active_alerts = health_data.get("active_alerts", 0)
            if active_alerts > 10:
                recommendations.append("High number of active alerts - review alerting thresholds")
            
            avg_metrics = health_data.get("average_metrics", {})
            if avg_metrics.get("avg_error_rate", 0) > 0.05:
                recommendations.append("Error rate above 5% - investigate sync failures")
            
            if avg_metrics.get("avg_lag_seconds", 0) > 30:
                recommendations.append("Sync lag above 30 seconds - optimize sync performance")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def _calculate_uptime_percentage(self) -> float:
        """Calculate overall sync uptime percentage"""
        try:
            # This would calculate uptime based on metrics history
            # For now, return a calculated value based on error rates
            
            all_recent_metrics = []
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            for metrics_list in self.sync_metrics.values():
                recent_metrics = [m for m in metrics_list if m.timestamp >= cutoff_time]
                all_recent_metrics.extend(recent_metrics)
            
            if not all_recent_metrics:
                return 0.0
            
            avg_success_rate = statistics.mean([m.success_rate for m in all_recent_metrics])
            return avg_success_rate
            
        except Exception as e:
            self.logger.error(f"Error calculating uptime: {str(e)}")
            return 0.0
    
    async def _get_last_successful_sync(self) -> Optional[datetime]:
        """Get timestamp of last successful sync across all pairs"""
        try:
            last_successful = None
            
            for metrics_list in self.sync_metrics.values():
                successful_metrics = [m for m in metrics_list if m.success_rate > 90.0]
                if successful_metrics:
                    latest_successful = max(successful_metrics, key=lambda x: x.timestamp)
                    if not last_successful or latest_successful.timestamp > last_successful:
                        last_successful = latest_successful.timestamp
            
            return last_successful
            
        except Exception as e:
            self.logger.error(f"Error getting last successful sync: {str(e)}")
            return None
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "sync.operation_completed",
                self._handle_sync_operation
            )
            
            await self.event_bus.subscribe(
                "sync.operation_failed",
                self._handle_sync_failure
            )
            
            await self.event_bus.subscribe(
                "conflict.detected",
                self._handle_conflict_detected
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_sync_operation(self, event_data: Dict[str, Any]):
        """Handle sync operation completion event"""
        try:
            sync_source = event_data.get("sync_source")
            sync_target = event_data.get("sync_target")
            duration_ms = event_data.get("duration_ms", 0)
            data_volume = event_data.get("data_volume_mb", 0)
            
            if sync_source and sync_target:
                # Record metrics from event
                await self.record_sync_metrics(
                    sync_source,
                    sync_target,
                    {
                        "response_time_ms": duration_ms,
                        "data_volume_mb": data_volume,
                        "success_rate": 100.0,
                        "error_rate": 0.0
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error handling sync operation: {str(e)}")
    
    async def _handle_sync_failure(self, event_data: Dict[str, Any]):
        """Handle sync operation failure event"""
        try:
            sync_source = event_data.get("sync_source")
            sync_target = event_data.get("sync_target")
            error_type = event_data.get("error_type", "unknown")
            
            if sync_source and sync_target:
                # Record failure metrics
                await self.record_sync_metrics(
                    sync_source,
                    sync_target,
                    {
                        "success_rate": 0.0,
                        "error_rate": 100.0,
                        "metadata": {"error_type": error_type}
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error handling sync failure: {str(e)}")
    
    async def _handle_conflict_detected(self, event_data: Dict[str, Any]):
        """Handle conflict detection event"""
        try:
            entity_id = event_data.get("entity_id")
            conflict_type = event_data.get("conflict_type")
            
            # This could trigger specific monitoring or alerting
            self.logger.info(f"Conflict detected for entity {entity_id}: {conflict_type}")
            
        except Exception as e:
            self.logger.error(f"Error handling conflict detection: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            overall_health = await self._calculate_overall_health()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "sync_monitor",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "sync_pairs_monitored": len(self.sync_metrics),
                    "active_alerts": len(self.active_alerts),
                    "overall_sync_status": overall_health.get("overall_status", "unknown")
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "sync_monitor",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Sync monitor service cleanup initiated")
        
        try:
            # Clear all state
            self.sync_metrics.clear()
            self.sync_health.clear()
            self.active_alerts.clear()
            self.component_status.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Sync monitor service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_sync_monitor() -> SyncMonitor:
    """Create sync monitor service"""
    return SyncMonitor()