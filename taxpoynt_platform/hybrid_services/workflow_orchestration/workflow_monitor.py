"""
Hybrid Service: Workflow Monitor
Monitors workflow execution and provides real-time insights
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics

from core_platform.database import get_db_session
from core_platform.models.workflow import WorkflowExecution, WorkflowMetrics, WorkflowAlert
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class AlertType(str, Enum):
    """Alert types"""
    WORKFLOW_TIMEOUT = "workflow_timeout"
    WORKFLOW_FAILURE = "workflow_failure"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SLA_BREACH = "sla_breach"
    ANOMALY_DETECTION = "anomaly_detection"
    THRESHOLD_EXCEEDED = "threshold_exceeded"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class MonitoringStatus(str, Enum):
    """Monitoring status"""
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class WorkflowMetrics:
    """Workflow performance metrics"""
    workflow_id: str
    execution_count: int
    success_rate: float
    failure_rate: float
    average_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    p99_duration: float
    throughput: float
    active_executions: int
    last_execution: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    total_workflows: int
    active_executions: int
    total_executions_today: int
    success_rate_today: float
    average_response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    error_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class WorkflowAlert:
    """Workflow alert"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    workflow_id: Optional[str]
    execution_id: Optional[str]
    message: str
    details: Dict[str, Any]
    threshold: Optional[float]
    actual_value: Optional[float]
    created_at: datetime
    acknowledged: bool = False
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MonitoringRule:
    """Monitoring rule definition"""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str
    threshold: float
    alert_type: AlertType
    severity: AlertSeverity
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorkflowMonitor:
    """Workflow execution monitor"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Monitoring state
        self.monitoring_status = MonitoringStatus.STOPPED
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Monitoring rules
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        
        # Active alerts
        self.active_alerts: Dict[str, WorkflowAlert] = {}
        
        # Performance data
        self.performance_data: Dict[str, List[Dict[str, Any]]] = {}
        
        # Monitoring configuration
        self.monitoring_interval = 30  # seconds
        self.retention_period = 86400  # 24 hours in seconds
        
        # Initialize default monitoring rules
        self._initialize_default_rules()
    
    async def start_monitoring(self) -> bool:
        """Start workflow monitoring"""
        try:
            if self.monitoring_status == MonitoringStatus.ACTIVE:
                return True
            
            self.monitoring_status = MonitoringStatus.ACTIVE
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Emit event
            await self.event_bus.emit("workflow_monitoring_started", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitoring_interval": self.monitoring_interval
            })
            
            self.logger.info("Workflow monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting monitoring: {str(e)}")
            self.monitoring_status = MonitoringStatus.ERROR
            return False
    
    async def stop_monitoring(self) -> bool:
        """Stop workflow monitoring"""
        try:
            if self.monitoring_status == MonitoringStatus.STOPPED:
                return True
            
            self.monitoring_status = MonitoringStatus.STOPPED
            
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
                self.monitoring_task = None
            
            # Emit event
            await self.event_bus.emit("workflow_monitoring_stopped", {
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info("Workflow monitoring stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring: {str(e)}")
            return False
    
    async def pause_monitoring(self) -> bool:
        """Pause workflow monitoring"""
        try:
            if self.monitoring_status == MonitoringStatus.ACTIVE:
                self.monitoring_status = MonitoringStatus.PAUSED
                
                # Emit event
                await self.event_bus.emit("workflow_monitoring_paused", {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                self.logger.info("Workflow monitoring paused")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error pausing monitoring: {str(e)}")
            return False
    
    async def resume_monitoring(self) -> bool:
        """Resume workflow monitoring"""
        try:
            if self.monitoring_status == MonitoringStatus.PAUSED:
                self.monitoring_status = MonitoringStatus.ACTIVE
                
                # Emit event
                await self.event_bus.emit("workflow_monitoring_resumed", {
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                self.logger.info("Workflow monitoring resumed")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resuming monitoring: {str(e)}")
            return False
    
    async def get_workflow_metrics(self, workflow_id: str) -> WorkflowMetrics:
        """Get metrics for a specific workflow"""
        try:
            # Check cache first
            cached_metrics = await self.cache_service.get(f"workflow_metrics:{workflow_id}")
            if cached_metrics:
                return WorkflowMetrics(**cached_metrics)
            
            # Calculate metrics from database
            with get_db_session() as db:
                executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.workflow_id == workflow_id
                ).all()
                
                if not executions:
                    return WorkflowMetrics(
                        workflow_id=workflow_id,
                        execution_count=0,
                        success_rate=0.0,
                        failure_rate=0.0,
                        average_duration=0.0,
                        min_duration=0.0,
                        max_duration=0.0,
                        p95_duration=0.0,
                        p99_duration=0.0,
                        throughput=0.0,
                        active_executions=0,
                        last_execution=None
                    )
                
                # Calculate metrics
                execution_count = len(executions)
                successful_executions = len([e for e in executions if e.status == "completed"])
                failed_executions = len([e for e in executions if e.status == "failed"])
                
                success_rate = (successful_executions / execution_count) * 100
                failure_rate = (failed_executions / execution_count) * 100
                
                durations = [e.total_duration for e in executions if e.total_duration]
                if durations:
                    average_duration = statistics.mean(durations)
                    min_duration = min(durations)
                    max_duration = max(durations)
                    p95_duration = statistics.quantiles(durations, n=20)[18]  # 95th percentile
                    p99_duration = statistics.quantiles(durations, n=100)[98]  # 99th percentile
                else:
                    average_duration = min_duration = max_duration = p95_duration = p99_duration = 0.0
                
                # Calculate throughput (executions per hour)
                now = datetime.now(timezone.utc)
                one_hour_ago = now - timedelta(hours=1)
                recent_executions = [e for e in executions if e.started_at >= one_hour_ago]
                throughput = len(recent_executions)
                
                # Active executions
                active_executions = len([e for e in executions if e.status == "running"])
                
                # Last execution
                last_execution = max([e.started_at for e in executions]) if executions else None
                
                metrics = WorkflowMetrics(
                    workflow_id=workflow_id,
                    execution_count=execution_count,
                    success_rate=success_rate,
                    failure_rate=failure_rate,
                    average_duration=average_duration,
                    min_duration=min_duration,
                    max_duration=max_duration,
                    p95_duration=p95_duration,
                    p99_duration=p99_duration,
                    throughput=throughput,
                    active_executions=active_executions,
                    last_execution=last_execution
                )
                
                # Cache metrics
                await self.cache_service.set(
                    f"workflow_metrics:{workflow_id}",
                    metrics.to_dict(),
                    ttl=300  # 5 minutes
                )
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error getting workflow metrics: {str(e)}")
            raise
    
    async def get_system_metrics(self) -> SystemMetrics:
        """Get system-wide metrics"""
        try:
            # Check cache first
            cached_metrics = await self.cache_service.get("system_metrics")
            if cached_metrics:
                return SystemMetrics(**cached_metrics)
            
            # Calculate metrics
            with get_db_session() as db:
                # Total workflows
                total_workflows = db.query(WorkflowExecution.workflow_id).distinct().count()
                
                # Active executions
                active_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.status == "running"
                ).count()
                
                # Today's executions
                today = datetime.now(timezone.utc).date()
                today_start = datetime.combine(today, datetime.min.time(), timezone.utc)
                
                today_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.started_at >= today_start
                ).all()
                
                total_executions_today = len(today_executions)
                successful_today = len([e for e in today_executions if e.status == "completed"])
                success_rate_today = (successful_today / total_executions_today * 100) if total_executions_today > 0 else 0
                
                # Average response time
                recent_executions = db.query(WorkflowExecution).filter(
                    WorkflowExecution.started_at >= datetime.now(timezone.utc) - timedelta(hours=1)
                ).all()
                
                if recent_executions:
                    response_times = [e.total_duration for e in recent_executions if e.total_duration]
                    average_response_time = statistics.mean(response_times) if response_times else 0.0
                else:
                    average_response_time = 0.0
                
                # System resource metrics (mock values - would integrate with actual monitoring)
                cpu_usage = 65.0
                memory_usage = 70.0
                disk_usage = 45.0
                
                # Error rate
                failed_today = len([e for e in today_executions if e.status == "failed"])
                error_rate = (failed_today / total_executions_today * 100) if total_executions_today > 0 else 0
                
                metrics = SystemMetrics(
                    total_workflows=total_workflows,
                    active_executions=active_executions,
                    total_executions_today=total_executions_today,
                    success_rate_today=success_rate_today,
                    average_response_time=average_response_time,
                    cpu_usage=cpu_usage,
                    memory_usage=memory_usage,
                    disk_usage=disk_usage,
                    error_rate=error_rate
                )
                
                # Cache metrics
                await self.cache_service.set(
                    "system_metrics",
                    metrics.to_dict(),
                    ttl=60  # 1 minute
                )
                
                return metrics
                
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {str(e)}")
            raise
    
    async def get_active_alerts(self) -> List[WorkflowAlert]:
        """Get active alerts"""
        try:
            return list(self.active_alerts.values())
            
        except Exception as e:
            self.logger.error(f"Error getting active alerts: {str(e)}")
            return []
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.acknowledged = True
                
                # Emit event
                await self.event_bus.emit("alert_acknowledged", {
                    "alert_id": alert_id,
                    "acknowledged_by": acknowledged_by,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {str(e)}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                # Emit event
                await self.event_bus.emit("alert_resolved", {
                    "alert_id": alert_id,
                    "resolved_by": resolved_by,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving alert: {str(e)}")
            return False
    
    async def add_monitoring_rule(self, rule: MonitoringRule) -> bool:
        """Add a monitoring rule"""
        try:
            self.monitoring_rules[rule.rule_id] = rule
            
            # Emit event
            await self.event_bus.emit("monitoring_rule_added", {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "metric_name": rule.metric_name,
                "threshold": rule.threshold,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Monitoring rule added: {rule.rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding monitoring rule: {str(e)}")
            return False
    
    async def remove_monitoring_rule(self, rule_id: str) -> bool:
        """Remove a monitoring rule"""
        try:
            if rule_id in self.monitoring_rules:
                del self.monitoring_rules[rule_id]
                
                # Emit event
                await self.event_bus.emit("monitoring_rule_removed", {
                    "rule_id": rule_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                self.logger.info(f"Monitoring rule removed: {rule_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing monitoring rule: {str(e)}")
            return False
    
    async def get_performance_data(
        self,
        workflow_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance data"""
        try:
            if workflow_id:
                data = self.performance_data.get(workflow_id, [])
            else:
                data = []
                for workflow_data in self.performance_data.values():
                    data.extend(workflow_data)
            
            # Filter by time range
            if start_time or end_time:
                filtered_data = []
                for point in data:
                    timestamp = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
                    if start_time and timestamp < start_time:
                        continue
                    if end_time and timestamp > end_time:
                        continue
                    filtered_data.append(point)
                data = filtered_data
            
            return {"performance_data": data}
            
        except Exception as e:
            self.logger.error(f"Error getting performance data: {str(e)}")
            return {"performance_data": []}
    
    # Private methods
    
    def _initialize_default_rules(self):
        """Initialize default monitoring rules"""
        default_rules = [
            MonitoringRule(
                rule_id="workflow_timeout",
                name="Workflow Timeout",
                description="Alert when workflow execution exceeds timeout",
                metric_name="execution_duration",
                condition="greater_than",
                threshold=3600.0,  # 1 hour
                alert_type=AlertType.WORKFLOW_TIMEOUT,
                severity=AlertSeverity.HIGH
            ),
            MonitoringRule(
                rule_id="high_failure_rate",
                name="High Failure Rate",
                description="Alert when failure rate exceeds threshold",
                metric_name="failure_rate",
                condition="greater_than",
                threshold=10.0,  # 10%
                alert_type=AlertType.WORKFLOW_FAILURE,
                severity=AlertSeverity.MEDIUM
            ),
            MonitoringRule(
                rule_id="performance_degradation",
                name="Performance Degradation",
                description="Alert when response time degrades significantly",
                metric_name="average_response_time",
                condition="greater_than",
                threshold=30.0,  # 30 seconds
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                severity=AlertSeverity.MEDIUM
            ),
            MonitoringRule(
                rule_id="high_cpu_usage",
                name="High CPU Usage",
                description="Alert when CPU usage is high",
                metric_name="cpu_usage",
                condition="greater_than",
                threshold=90.0,  # 90%
                alert_type=AlertType.RESOURCE_EXHAUSTION,
                severity=AlertSeverity.HIGH
            )
        ]
        
        for rule in default_rules:
            self.monitoring_rules[rule.rule_id] = rule
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.monitoring_status in [MonitoringStatus.ACTIVE, MonitoringStatus.PAUSED]:
                if self.monitoring_status == MonitoringStatus.ACTIVE:
                    await self._collect_metrics()
                    await self._check_alerts()
                    await self._cleanup_old_data()
                
                await asyncio.sleep(self.monitoring_interval)
                
        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {str(e)}")
            self.monitoring_status = MonitoringStatus.ERROR
    
    async def _collect_metrics(self):
        """Collect performance metrics"""
        try:
            # Get system metrics
            system_metrics = await self.get_system_metrics()
            
            # Store system metrics
            timestamp = datetime.now(timezone.utc).isoformat()
            system_data = {
                "timestamp": timestamp,
                "metrics": system_metrics.to_dict()
            }
            
            if "system" not in self.performance_data:
                self.performance_data["system"] = []
            self.performance_data["system"].append(system_data)
            
            # Get workflow metrics for active workflows
            with get_db_session() as db:
                active_workflows = db.query(WorkflowExecution.workflow_id).filter(
                    WorkflowExecution.status == "running"
                ).distinct().all()
                
                for (workflow_id,) in active_workflows:
                    workflow_metrics = await self.get_workflow_metrics(workflow_id)
                    
                    workflow_data = {
                        "timestamp": timestamp,
                        "workflow_id": workflow_id,
                        "metrics": workflow_metrics.to_dict()
                    }
                    
                    if workflow_id not in self.performance_data:
                        self.performance_data[workflow_id] = []
                    self.performance_data[workflow_id].append(workflow_data)
                    
        except Exception as e:
            self.logger.error(f"Error collecting metrics: {str(e)}")
    
    async def _check_alerts(self):
        """Check for alert conditions"""
        try:
            # Get current system metrics
            system_metrics = await self.get_system_metrics()
            
            # Check system-level rules
            await self._check_system_rules(system_metrics)
            
            # Check workflow-level rules
            with get_db_session() as db:
                active_workflows = db.query(WorkflowExecution.workflow_id).distinct().all()
                
                for (workflow_id,) in active_workflows:
                    workflow_metrics = await self.get_workflow_metrics(workflow_id)
                    await self._check_workflow_rules(workflow_id, workflow_metrics)
                    
        except Exception as e:
            self.logger.error(f"Error checking alerts: {str(e)}")
    
    async def _check_system_rules(self, system_metrics: SystemMetrics):
        """Check system-level monitoring rules"""
        try:
            metrics_dict = system_metrics.to_dict()
            
            for rule in self.monitoring_rules.values():
                if not rule.enabled:
                    continue
                
                metric_value = metrics_dict.get(rule.metric_name)
                if metric_value is None:
                    continue
                
                # Check condition
                alert_triggered = False
                if rule.condition == "greater_than" and metric_value > rule.threshold:
                    alert_triggered = True
                elif rule.condition == "less_than" and metric_value < rule.threshold:
                    alert_triggered = True
                elif rule.condition == "equals" and metric_value == rule.threshold:
                    alert_triggered = True
                
                if alert_triggered:
                    await self._create_alert(
                        rule=rule,
                        workflow_id=None,
                        execution_id=None,
                        actual_value=metric_value,
                        message=f"System metric {rule.metric_name} ({metric_value}) exceeded threshold ({rule.threshold})"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking system rules: {str(e)}")
    
    async def _check_workflow_rules(self, workflow_id: str, workflow_metrics: WorkflowMetrics):
        """Check workflow-level monitoring rules"""
        try:
            metrics_dict = workflow_metrics.to_dict()
            
            for rule in self.monitoring_rules.values():
                if not rule.enabled:
                    continue
                
                metric_value = metrics_dict.get(rule.metric_name)
                if metric_value is None:
                    continue
                
                # Check condition
                alert_triggered = False
                if rule.condition == "greater_than" and metric_value > rule.threshold:
                    alert_triggered = True
                elif rule.condition == "less_than" and metric_value < rule.threshold:
                    alert_triggered = True
                elif rule.condition == "equals" and metric_value == rule.threshold:
                    alert_triggered = True
                
                if alert_triggered:
                    await self._create_alert(
                        rule=rule,
                        workflow_id=workflow_id,
                        execution_id=None,
                        actual_value=metric_value,
                        message=f"Workflow {workflow_id} metric {rule.metric_name} ({metric_value}) exceeded threshold ({rule.threshold})"
                    )
                    
        except Exception as e:
            self.logger.error(f"Error checking workflow rules: {str(e)}")
    
    async def _create_alert(
        self,
        rule: MonitoringRule,
        workflow_id: Optional[str],
        execution_id: Optional[str],
        actual_value: float,
        message: str
    ):
        """Create an alert"""
        try:
            alert_id = str(uuid.uuid4())
            
            # Check if similar alert already exists
            existing_alert = None
            for alert in self.active_alerts.values():
                if (alert.alert_type == rule.alert_type and 
                    alert.workflow_id == workflow_id and
                    not alert.resolved):
                    existing_alert = alert
                    break
            
            if existing_alert:
                # Update existing alert
                existing_alert.actual_value = actual_value
                existing_alert.details["last_updated"] = datetime.now(timezone.utc).isoformat()
                existing_alert.details["occurrence_count"] = existing_alert.details.get("occurrence_count", 1) + 1
                return
            
            # Create new alert
            alert = WorkflowAlert(
                alert_id=alert_id,
                alert_type=rule.alert_type,
                severity=rule.severity,
                workflow_id=workflow_id,
                execution_id=execution_id,
                message=message,
                details={
                    "rule_id": rule.rule_id,
                    "metric_name": rule.metric_name,
                    "condition": rule.condition,
                    "occurrence_count": 1
                },
                threshold=rule.threshold,
                actual_value=actual_value,
                created_at=datetime.now(timezone.utc)
            )
            
            # Add to active alerts
            self.active_alerts[alert_id] = alert
            
            # Send notification
            await self._send_alert_notification(alert)
            
            # Emit event
            await self.event_bus.emit("alert_created", {
                "alert_id": alert_id,
                "alert_type": rule.alert_type,
                "severity": rule.severity,
                "workflow_id": workflow_id,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {str(e)}")
    
    async def _send_alert_notification(self, alert: WorkflowAlert):
        """Send alert notification"""
        try:
            await self.notification_service.send_alert(
                alert_id=alert.alert_id,
                severity=alert.severity,
                message=alert.message,
                details=alert.details
            )
            
        except Exception as e:
            self.logger.error(f"Error sending alert notification: {str(e)}")
    
    async def _cleanup_old_data(self):
        """Clean up old performance data"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=self.retention_period)
            
            for workflow_id, data_points in self.performance_data.items():
                filtered_points = []
                for point in data_points:
                    timestamp = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
                    if timestamp >= cutoff_time:
                        filtered_points.append(point)
                
                self.performance_data[workflow_id] = filtered_points
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for workflow monitor"""
        try:
            return {
                "status": "healthy",
                "service": "workflow_monitor",
                "monitoring_status": self.monitoring_status,
                "active_alerts": len(self.active_alerts),
                "monitoring_rules": len(self.monitoring_rules),
                "performance_data_points": sum(len(data) for data in self.performance_data.values()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "workflow_monitor",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup monitor resources"""
        try:
            # Stop monitoring
            await self.stop_monitoring()
            
            # Clear data
            self.monitoring_rules.clear()
            self.active_alerts.clear()
            self.performance_data.clear()
            
            self.logger.info("Workflow monitor cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_workflow_monitor() -> WorkflowMonitor:
    """Create workflow monitor instance"""
    return WorkflowMonitor()