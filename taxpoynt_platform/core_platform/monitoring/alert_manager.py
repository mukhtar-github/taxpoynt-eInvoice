"""
Alert Manager - Core Platform Observability

Centralized alerting system for the entire TaxPoynt platform.
Manages alert routing, escalation, notification, and incident tracking across all services.
"""

import asyncio
import logging
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
import re

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert lifecycle status"""
    TRIGGERED = "triggered"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    EXPIRED = "expired"


class NotificationChannel(Enum):
    """Available notification channels"""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"
    DASHBOARD = "dashboard"
    LOG = "log"


class EscalationLevel(Enum):
    """Escalation levels"""
    L1 = "l1"  # First responder
    L2 = "l2"  # Team lead / Senior
    L3 = "l3"  # Manager / Director
    L4 = "l4"  # Executive


@dataclass
class AlertRule:
    """Configuration for alert rules"""
    rule_id: str
    name: str
    description: str
    condition: str  # Expression to evaluate
    severity: AlertSeverity
    service_filters: List[str] = field(default_factory=list)  # Service name patterns
    service_role_filters: List[str] = field(default_factory=list)  # Service role filters
    tags_filters: Dict[str, str] = field(default_factory=dict)  # Tag filters
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    escalation_policy: Optional[str] = None
    cooldown_minutes: int = 60  # Minimum time between identical alerts
    auto_resolve_minutes: Optional[int] = None  # Auto-resolve after N minutes
    enabled: bool = True


@dataclass
class EscalationPolicy:
    """Escalation policy configuration"""
    policy_id: str
    name: str
    description: str
    escalation_steps: List[Dict[str, Any]]  # [{level, delay_minutes, channels, contacts}]
    repeat_interval_minutes: int = 0  # 0 = no repeat
    max_escalations: int = 3


@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_id: str
    title: str
    description: str
    severity: AlertSeverity
    status: AlertStatus
    source: Dict[str, Any]  # Source information (service, metric, etc.)
    triggered_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    escalation_level: EscalationLevel = EscalationLevel.L1
    escalated_at: Optional[datetime] = None
    notification_history: List[Dict[str, Any]] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    suppressed_until: Optional[datetime] = None
    correlation_id: Optional[str] = None  # For grouping related alerts


@dataclass
class NotificationTemplate:
    """Template for notifications"""
    template_id: str
    name: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    enabled: bool = True


@dataclass
class NotificationEndpoint:
    """Configuration for notification endpoints"""
    endpoint_id: str
    name: str
    channel: NotificationChannel
    configuration: Dict[str, Any]  # Channel-specific config
    enabled: bool = True


class AlertManager:
    """
    Centralized alert management system for the TaxPoynt platform.
    
    Manages alerts from all platform components:
    - SI Services (ERP integration failures, certificate issues, etc.)
    - APP Services (FIRS communication errors, validation failures, etc.)
    - Hybrid Services (billing issues, workflow failures, etc.)
    - Core Platform (authentication failures, database issues, etc.)
    - External Integrations (third-party service outages, etc.)
    """
    
    def __init__(self):
        # Core data storage
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        self.notification_templates: Dict[str, NotificationTemplate] = {}
        self.notification_endpoints: Dict[str, NotificationEndpoint] = {}
        
        # Alert processing
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.processing_tasks: List[asyncio.Task] = []
        self.correlation_engine = AlertCorrelationEngine()
        
        # Suppression and throttling
        self.alert_cooldowns: Dict[str, datetime] = {}  # rule_id -> last_triggered
        self.suppression_rules: List[Dict[str, Any]] = []
        
        # Statistics and metrics
        self.stats = {
            "total_alerts": 0,
            "alerts_by_severity": {severity.value: 0 for severity in AlertSeverity},
            "alerts_by_status": {status.value: 0 for status in AlertStatus},
            "notifications_sent": 0,
            "escalations_triggered": 0,
            "avg_resolution_time_minutes": 0
        }
        
        # Background tasks
        self._running = False
        self._processor_task = None
        self._escalation_task = None
        self._cleanup_task = None
        
        # Event handlers
        self.alert_handlers: List[Callable] = []
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}
        
        # Dependencies
        self.metrics_aggregator = None
        self.health_orchestrator = None
    
    # === Dependency Injection ===
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    def set_health_orchestrator(self, health_orchestrator):
        """Inject health orchestrator dependency"""
        self.health_orchestrator = health_orchestrator
    
    # === Alert Rule Management ===
    
    def create_alert_rule(
        self,
        rule_id: str,
        name: str,
        description: str,
        condition: str,
        severity: AlertSeverity,
        notification_channels: List[NotificationChannel],
        service_filters: Optional[List[str]] = None,
        service_role_filters: Optional[List[str]] = None,
        tags_filters: Optional[Dict[str, str]] = None,
        escalation_policy: Optional[str] = None,
        cooldown_minutes: int = 60,
        auto_resolve_minutes: Optional[int] = None
    ) -> bool:
        """Create a new alert rule"""
        try:
            rule = AlertRule(
                rule_id=rule_id,
                name=name,
                description=description,
                condition=condition,
                severity=severity,
                service_filters=service_filters or [],
                service_role_filters=service_role_filters or [],
                tags_filters=tags_filters or {},
                notification_channels=notification_channels,
                escalation_policy=escalation_policy,
                cooldown_minutes=cooldown_minutes,
                auto_resolve_minutes=auto_resolve_minutes
            )
            
            self.alert_rules[rule_id] = rule
            logger.info(f"Created alert rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert rule {rule_id}: {e}")
            return False
    
    def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule"""
        try:
            if rule_id not in self.alert_rules:
                return False
            
            rule = self.alert_rules[rule_id]
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            logger.info(f"Updated alert rule: {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update alert rule {rule_id}: {e}")
            return False
    
    def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule"""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"Deleted alert rule: {rule_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete alert rule {rule_id}: {e}")
            return False
    
    def get_alert_rules(self, enabled_only: bool = True) -> List[AlertRule]:
        """Get all alert rules"""
        rules = list(self.alert_rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules
    
    # === Escalation Policy Management ===
    
    def create_escalation_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        escalation_steps: List[Dict[str, Any]],
        repeat_interval_minutes: int = 0,
        max_escalations: int = 3
    ) -> bool:
        """Create an escalation policy"""
        try:
            policy = EscalationPolicy(
                policy_id=policy_id,
                name=name,
                description=description,
                escalation_steps=escalation_steps,
                repeat_interval_minutes=repeat_interval_minutes,
                max_escalations=max_escalations
            )
            
            self.escalation_policies[policy_id] = policy
            logger.info(f"Created escalation policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create escalation policy {policy_id}: {e}")
            return False
    
    # === Notification Configuration ===
    
    def create_notification_template(
        self,
        template_id: str,
        name: str,
        channel: NotificationChannel,
        subject_template: str,
        body_template: str
    ) -> bool:
        """Create a notification template"""
        try:
            template = NotificationTemplate(
                template_id=template_id,
                name=name,
                channel=channel,
                subject_template=subject_template,
                body_template=body_template
            )
            
            self.notification_templates[template_id] = template
            logger.info(f"Created notification template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create notification template {template_id}: {e}")
            return False
    
    def create_notification_endpoint(
        self,
        endpoint_id: str,
        name: str,
        channel: NotificationChannel,
        configuration: Dict[str, Any]
    ) -> bool:
        """Create a notification endpoint"""
        try:
            endpoint = NotificationEndpoint(
                endpoint_id=endpoint_id,
                name=name,
                channel=channel,
                configuration=configuration
            )
            
            self.notification_endpoints[endpoint_id] = endpoint
            logger.info(f"Created notification endpoint: {endpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create notification endpoint {endpoint_id}: {e}")
            return False
    
    def register_notification_handler(self, channel: NotificationChannel, handler: Callable):
        """Register a handler for a notification channel"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for {channel.value}")
    
    # === Alert Processing ===
    
    async def trigger_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Trigger a new alert"""
        try:
            # Find matching rules
            matching_rules = self._find_matching_rules(alert_data)
            
            if not matching_rules:
                logger.debug(f"No matching rules found for alert: {alert_data.get('title', 'Unknown')}")
                return None
            
            # Use the highest severity rule
            rule = max(matching_rules, key=lambda r: self._severity_weight(r.severity))
            
            # Check cooldown
            if self._is_in_cooldown(rule.rule_id):
                logger.debug(f"Alert rule {rule.rule_id} is in cooldown")
                return None
            
            # Create alert
            alert = self._create_alert(rule, alert_data)
            
            # Check for correlation with existing alerts
            correlation_id = self.correlation_engine.correlate_alert(alert, list(self.alerts.values()))
            if correlation_id:
                alert.correlation_id = correlation_id
            
            # Store alert
            self.alerts[alert.alert_id] = alert
            
            # Update statistics
            self.stats["total_alerts"] += 1
            self.stats["alerts_by_severity"][alert.severity.value] += 1
            self.stats["alerts_by_status"][alert.status.value] += 1
            
            # Queue for processing
            await self.alert_queue.put(alert)
            
            # Update cooldown
            self.alert_cooldowns[rule.rule_id] = datetime.utcnow()
            
            # Notify handlers
            await self._notify_alert_handlers(alert)
            
            # Send metrics if available
            if self.metrics_aggregator:
                await self._send_alert_metrics(alert)
            
            logger.info(f"Alert triggered: {alert.alert_id} - {alert.title}")
            return alert.alert_id
            
        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")
            return None
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            
            if alert.status in [AlertStatus.RESOLVED, AlertStatus.EXPIRED]:
                return False
            
            # Update alert
            old_status = alert.status
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            
            # Update statistics
            self.stats["alerts_by_status"][old_status.value] -= 1
            self.stats["alerts_by_status"][alert.status.value] += 1
            
            # Add to notification history
            alert.notification_history.append({
                "action": "acknowledged",
                "timestamp": alert.acknowledged_at,
                "by": acknowledged_by
            })
            
            logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str, resolution_note: Optional[str] = None) -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            
            if alert.status == AlertStatus.RESOLVED:
                return False
            
            # Update alert
            old_status = alert.status
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            
            if resolution_note:
                alert.metadata["resolution_note"] = resolution_note
            
            # Calculate resolution time
            resolution_time = (alert.resolved_at - alert.triggered_at).total_seconds() / 60
            self._update_resolution_time(resolution_time)
            
            # Update statistics
            self.stats["alerts_by_status"][old_status.value] -= 1
            self.stats["alerts_by_status"][alert.status.value] += 1
            
            # Add to notification history
            alert.notification_history.append({
                "action": "resolved",
                "timestamp": alert.resolved_at,
                "by": resolved_by,
                "note": resolution_note
            })
            
            logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    async def suppress_alert(self, alert_id: str, suppress_until: datetime, reason: str) -> bool:
        """Suppress an alert for a specified time"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            
            # Update alert
            old_status = alert.status
            alert.status = AlertStatus.SUPPRESSED
            alert.suppressed_until = suppress_until
            alert.metadata["suppression_reason"] = reason
            
            # Update statistics
            self.stats["alerts_by_status"][old_status.value] -= 1
            self.stats["alerts_by_status"][alert.status.value] += 1
            
            logger.info(f"Alert suppressed: {alert_id} until {suppress_until}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to suppress alert {alert_id}: {e}")
            return False
    
    # === Alert Querying ===
    
    def get_alerts(
        self,
        status: Optional[AlertStatus] = None,
        severity: Optional[AlertSeverity] = None,
        service_name: Optional[str] = None,
        service_role: Optional[str] = None,
        hours: Optional[int] = None,
        limit: Optional[int] = None
    ) -> List[Alert]:
        """Get alerts with optional filtering"""
        alerts = list(self.alerts.values())
        
        # Apply filters
        if status:
            alerts = [a for a in alerts if a.status == status]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if service_name:
            alerts = [a for a in alerts if a.source.get("service_name") == service_name]
        
        if service_role:
            alerts = [a for a in alerts if a.source.get("service_role") == service_role]
        
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            alerts = [a for a in alerts if a.triggered_at >= cutoff_time]
        
        # Sort by triggered_at descending
        alerts.sort(key=lambda a: a.triggered_at, reverse=True)
        
        # Apply limit
        if limit:
            alerts = alerts[:limit]
        
        return alerts
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (non-resolved) alerts"""
        return self.get_alerts(status=AlertStatus.TRIGGERED) + \
               self.get_alerts(status=AlertStatus.ACKNOWLEDGED) + \
               self.get_alerts(status=AlertStatus.INVESTIGATING)
    
    def get_alert_by_id(self, alert_id: str) -> Optional[Alert]:
        """Get a specific alert by ID"""
        return self.alerts.get(alert_id)
    
    def get_correlated_alerts(self, correlation_id: str) -> List[Alert]:
        """Get all alerts with the same correlation ID"""
        return [alert for alert in self.alerts.values() if alert.correlation_id == correlation_id]
    
    # === Alert Analytics ===
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [a for a in self.alerts.values() if a.triggered_at >= cutoff_time]
        
        # Group by severity
        by_severity = defaultdict(int)
        for alert in recent_alerts:
            by_severity[alert.severity.value] += 1
        
        # Group by service role
        by_service_role = defaultdict(int)
        for alert in recent_alerts:
            service_role = alert.source.get("service_role", "unknown")
            by_service_role[service_role] += 1
        
        # Group by status
        by_status = defaultdict(int)
        for alert in recent_alerts:
            by_status[alert.status.value] += 1
        
        # Top alerting services
        service_counts = defaultdict(int)
        for alert in recent_alerts:
            service_name = alert.source.get("service_name", "unknown")
            service_counts[service_name] += 1
        
        top_services = sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "time_period_hours": hours,
            "total_alerts": len(recent_alerts),
            "active_alerts": len([a for a in recent_alerts if a.status in [AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]]),
            "by_severity": dict(by_severity),
            "by_status": dict(by_status),
            "by_service_role": dict(by_service_role),
            "top_alerting_services": top_services,
            "correlation_groups": len(set(a.correlation_id for a in recent_alerts if a.correlation_id)),
            "avg_resolution_time_minutes": self.stats["avg_resolution_time_minutes"]
        }
    
    def get_alert_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get alert trends over the specified period"""
        trends = {}
        
        for day in range(days):
            day_start = datetime.utcnow() - timedelta(days=day+1)
            day_end = day_start + timedelta(days=1)
            
            day_alerts = [
                a for a in self.alerts.values()
                if day_start <= a.triggered_at < day_end
            ]
            
            day_key = day_start.strftime("%Y-%m-%d")
            trends[day_key] = {
                "total": len(day_alerts),
                "critical": len([a for a in day_alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in day_alerts if a.severity == AlertSeverity.WARNING]),
                "resolved": len([a for a in day_alerts if a.status == AlertStatus.RESOLVED])
            }
        
        return {
            "period_days": days,
            "daily_trends": trends,
            "overall_trend": self._calculate_alert_trend(trends)
        }
    
    # === Background Tasks ===
    
    async def start_alert_processing(self):
        """Start background alert processing"""
        if self._running:
            return
        
        self._running = True
        
        # Start processor tasks
        self._processor_task = asyncio.create_task(self._process_alerts())
        self._escalation_task = asyncio.create_task(self._handle_escalations())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_alerts())
        
        logger.info("Alert processing started")
    
    async def stop_alert_processing(self):
        """Stop background alert processing"""
        self._running = False
        
        # Cancel tasks
        for task in [self._processor_task, self._escalation_task, self._cleanup_task]:
            if task:
                task.cancel()
        
        logger.info("Alert processing stopped")
    
    async def _process_alerts(self):
        """Main alert processing loop"""
        while self._running:
            try:
                # Get alert from queue with timeout
                alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                
                # Send notifications
                await self._send_notifications(alert)
                
                # Mark task as done
                self.alert_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing alert: {e}")
                await asyncio.sleep(1)
    
    async def _handle_escalations(self):
        """Handle alert escalations"""
        while self._running:
            try:
                current_time = datetime.utcnow()
                
                # Check for alerts that need escalation
                for alert in self.alerts.values():
                    if await self._should_escalate_alert(alert, current_time):
                        await self._escalate_alert(alert)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in escalation handler: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_alerts(self):
        """Clean up old resolved alerts"""
        while self._running:
            try:
                cutoff_time = datetime.utcnow() - timedelta(days=30)  # Keep 30 days
                
                alerts_to_remove = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if alert.status == AlertStatus.RESOLVED and alert.resolved_at and alert.resolved_at < cutoff_time
                ]
                
                for alert_id in alerts_to_remove:
                    del self.alerts[alert_id]
                
                if alerts_to_remove:
                    logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(3600)
    
    # === Utility Methods ===
    
    def _find_matching_rules(self, alert_data: Dict[str, Any]) -> List[AlertRule]:
        """Find alert rules that match the given alert data"""
        matching_rules = []
        
        for rule in self.get_alert_rules(enabled_only=True):
            if self._rule_matches_alert(rule, alert_data):
                matching_rules.append(rule)
        
        return matching_rules
    
    def _rule_matches_alert(self, rule: AlertRule, alert_data: Dict[str, Any]) -> bool:
        """Check if an alert rule matches the alert data"""
        # Check service filters
        if rule.service_filters:
            service_name = alert_data.get("service_name", "")
            if not any(re.search(pattern, service_name) for pattern in rule.service_filters):
                return False
        
        # Check service role filters
        if rule.service_role_filters:
            service_role = alert_data.get("service_role", "")
            if service_role not in rule.service_role_filters:
                return False
        
        # Check tag filters
        alert_tags = alert_data.get("tags", {})
        for tag_key, tag_value in rule.tags_filters.items():
            if alert_tags.get(tag_key) != tag_value:
                return False
        
        # TODO: Implement condition evaluation
        # For now, assume all rules match if filters pass
        
        return True
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if a rule is in cooldown period"""
        if rule_id not in self.alert_cooldowns:
            return False
        
        rule = self.alert_rules.get(rule_id)
        if not rule:
            return False
        
        last_triggered = self.alert_cooldowns[rule_id]
        cooldown_expires = last_triggered + timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.utcnow() < cooldown_expires
    
    def _create_alert(self, rule: AlertRule, alert_data: Dict[str, Any]) -> Alert:
        """Create an alert from rule and data"""
        alert_id = str(uuid.uuid4())
        
        return Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            title=alert_data.get("title", rule.name),
            description=alert_data.get("description", rule.description),
            severity=rule.severity,
            status=AlertStatus.TRIGGERED,
            source=alert_data,
            triggered_at=datetime.utcnow(),
            tags=alert_data.get("tags", {}),
            metadata=alert_data.get("metadata", {})
        )
    
    def _severity_weight(self, severity: AlertSeverity) -> int:
        """Get numeric weight for severity comparison"""
        weights = {
            AlertSeverity.INFO: 1,
            AlertSeverity.WARNING: 2,
            AlertSeverity.ERROR: 3,
            AlertSeverity.CRITICAL: 4
        }
        return weights.get(severity, 0)
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert"""
        rule = self.alert_rules.get(alert.rule_id)
        if not rule:
            return
        
        for channel in rule.notification_channels:
            try:
                if channel in self.notification_handlers:
                    handler = self.notification_handlers[channel]
                    await self._call_notification_handler(handler, alert, channel)
                else:
                    # Use default notification methods
                    await self._send_default_notification(alert, channel)
                
                # Record notification
                alert.notification_history.append({
                    "channel": channel.value,
                    "timestamp": datetime.utcnow(),
                    "status": "sent"
                })
                
                self.stats["notifications_sent"] += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification via {channel.value}: {e}")
                
                # Record failed notification
                alert.notification_history.append({
                    "channel": channel.value,
                    "timestamp": datetime.utcnow(),
                    "status": "failed",
                    "error": str(e)
                })
    
    async def _call_notification_handler(self, handler: Callable, alert: Alert, channel: NotificationChannel):
        """Call a notification handler"""
        if asyncio.iscoroutinefunction(handler):
            await handler(alert, channel)
        else:
            handler(alert, channel)
    
    async def _send_default_notification(self, alert: Alert, channel: NotificationChannel):
        """Send notification using default methods"""
        if channel == NotificationChannel.LOG:
            logger.warning(f"ALERT: {alert.title} - {alert.description}")
        elif channel == NotificationChannel.DASHBOARD:
            # Would integrate with dashboard system
            pass
        # Add other default notification methods as needed
    
    async def _should_escalate_alert(self, alert: Alert, current_time: datetime) -> bool:
        """Check if an alert should be escalated"""
        if alert.status in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED]:
            return False
        
        rule = self.alert_rules.get(alert.rule_id)
        if not rule or not rule.escalation_policy:
            return False
        
        policy = self.escalation_policies.get(rule.escalation_policy)
        if not policy:
            return False
        
        # Check if enough time has passed for escalation
        escalation_time = alert.escalated_at or alert.triggered_at
        next_escalation_level = min(alert.escalation_level.value[1:]) + 1
        
        if next_escalation_level > len(policy.escalation_steps):
            return False
        
        escalation_step = policy.escalation_steps[next_escalation_level - 1]
        delay_minutes = escalation_step.get("delay_minutes", 60)
        
        return current_time >= escalation_time + timedelta(minutes=delay_minutes)
    
    async def _escalate_alert(self, alert: Alert):
        """Escalate an alert to the next level"""
        try:
            # Update escalation level
            current_level_num = int(alert.escalation_level.value[1:])
            next_level_num = current_level_num + 1
            
            if next_level_num <= 4:  # Max L4
                alert.escalation_level = EscalationLevel(f"l{next_level_num}")
                alert.escalated_at = datetime.utcnow()
                
                # Send escalation notifications
                await self._send_escalation_notifications(alert)
                
                self.stats["escalations_triggered"] += 1
                
                logger.warning(f"Alert escalated to {alert.escalation_level.value}: {alert.alert_id}")
        
        except Exception as e:
            logger.error(f"Failed to escalate alert {alert.alert_id}: {e}")
    
    async def _send_escalation_notifications(self, alert: Alert):
        """Send notifications for alert escalation"""
        # This would implement escalation-specific notification logic
        logger.warning(f"ESCALATION: Alert {alert.alert_id} escalated to {alert.escalation_level.value}")
    
    async def _notify_alert_handlers(self, alert: Alert):
        """Notify registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def _send_alert_metrics(self, alert: Alert):
        """Send alert metrics to metrics aggregator"""
        try:
            # Send alert triggered metric
            await self.metrics_aggregator.collect_metric_point(
                name="alert_triggered",
                value=1,
                service_role=alert.source.get("service_role", "unknown"),
                service_name=alert.source.get("service_name", "unknown"),
                tags={
                    "severity": alert.severity.value,
                    "rule_id": alert.rule_id
                }
            )
        except Exception as e:
            logger.error(f"Error sending alert metrics: {e}")
    
    def _update_resolution_time(self, resolution_time_minutes: float):
        """Update average resolution time statistic"""
        current_avg = self.stats["avg_resolution_time_minutes"]
        resolved_count = self.stats["alerts_by_status"][AlertStatus.RESOLVED.value]
        
        if resolved_count == 1:
            self.stats["avg_resolution_time_minutes"] = resolution_time_minutes
        else:
            # Calculate running average
            self.stats["avg_resolution_time_minutes"] = (
                (current_avg * (resolved_count - 1) + resolution_time_minutes) / resolved_count
            )
    
    def _calculate_alert_trend(self, trends: Dict[str, Dict[str, int]]) -> str:
        """Calculate overall alert trend"""
        if len(trends) < 2:
            return "stable"
        
        dates = sorted(trends.keys())
        recent_total = trends[dates[-1]]["total"]
        older_total = trends[dates[0]]["total"]
        
        if recent_total > older_total * 1.2:
            return "increasing"
        elif recent_total < older_total * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    # === Health and Status ===
    
    def get_alert_manager_health(self) -> Dict[str, Any]:
        """Get health status of the alert manager"""
        return {
            "status": "running" if self._running else "stopped",
            "total_alerts": len(self.alerts),
            "active_alerts": len(self.get_active_alerts()),
            "alert_rules": len(self.alert_rules),
            "escalation_policies": len(self.escalation_policies),
            "notification_templates": len(self.notification_templates),
            "queue_size": self.alert_queue.qsize(),
            "statistics": self.stats.copy()
        }
    
    def add_alert_handler(self, handler: Callable):
        """Add an alert event handler"""
        self.alert_handlers.append(handler)


class AlertCorrelationEngine:
    """Engine for correlating related alerts"""
    
    def correlate_alert(self, new_alert: Alert, existing_alerts: List[Alert]) -> Optional[str]:
        """Find correlation ID for a new alert"""
        # Simple correlation based on service and time window
        time_window = timedelta(minutes=30)
        
        for existing_alert in existing_alerts:
            if (existing_alert.source.get("service_name") == new_alert.source.get("service_name") and
                existing_alert.triggered_at >= new_alert.triggered_at - time_window and
                existing_alert.status in [AlertStatus.TRIGGERED, AlertStatus.ACKNOWLEDGED]):
                
                return existing_alert.correlation_id or existing_alert.alert_id
        
        return None


# Global instance for platform-wide access
alert_manager = AlertManager()


# Setup functions for easy integration
async def setup_default_alert_rules():
    """Setup default alert rules for the platform"""
    
    # Critical health check failures
    alert_manager.create_alert_rule(
        rule_id="critical_health_check_failure",
        name="Critical Health Check Failure",
        description="A critical health check has failed",
        condition="health_check.status == 'critical'",
        severity=AlertSeverity.CRITICAL,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
        cooldown_minutes=30
    )
    
    # High error rates
    alert_manager.create_alert_rule(
        rule_id="high_error_rate",
        name="High Error Rate",
        description="Service error rate is above threshold",
        condition="error_rate > 10",
        severity=AlertSeverity.WARNING,
        notification_channels=[NotificationChannel.EMAIL],
        cooldown_minutes=60
    )
    
    # Service unavailability
    alert_manager.create_alert_rule(
        rule_id="service_unavailable",
        name="Service Unavailable",
        description="Service is not responding",
        condition="availability < 50",
        severity=AlertSeverity.CRITICAL,
        notification_channels=[NotificationChannel.EMAIL, NotificationChannel.SMS],
        escalation_policy="critical_escalation",
        cooldown_minutes=15
    )
    
    # Create escalation policy
    alert_manager.create_escalation_policy(
        policy_id="critical_escalation",
        name="Critical Issue Escalation",
        description="Escalation for critical platform issues",
        escalation_steps=[
            {"level": "l1", "delay_minutes": 15, "channels": ["email"]},
            {"level": "l2", "delay_minutes": 30, "channels": ["email", "sms"]},
            {"level": "l3", "delay_minutes": 60, "channels": ["email", "sms", "slack"]}
        ]
    )
    
    logger.info("Default alert rules setup completed")


async def shutdown_alert_management():
    """Shutdown alert management"""
    await alert_manager.stop_alert_processing()
    logger.info("Alert management shutdown completed")