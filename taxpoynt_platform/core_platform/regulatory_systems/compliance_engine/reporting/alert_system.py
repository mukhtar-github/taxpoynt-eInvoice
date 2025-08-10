"""
Compliance Alert System
======================
Real-time compliance alerting system that monitors compliance status,
triggers alerts based on configurable rules, and manages alert lifecycle.
"""
import logging
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, asdict

from .models import (
    ComplianceStatus, RiskLevel, ReportFormat,
    ComplianceMetrics, AuditTrail
)
from ..orchestrator.models import (
    ComplianceRequest, ComplianceResult, ValidationResult
)

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """Types of compliance alerts."""
    VALIDATION_FAILURE = "validation_failure"
    COMPLIANCE_DEGRADATION = "compliance_degradation"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    DEADLINE_APPROACHING = "deadline_approaching"
    REGULATORY_CHANGE = "regulatory_change"
    SYSTEM_ANOMALY = "system_anomaly"
    AUDIT_REQUIRED = "audit_required"
    DOCUMENTATION_MISSING = "documentation_missing"
    CERTIFICATION_EXPIRING = "certification_expiring"
    THRESHOLD_BREACH = "threshold_breach"


class AlertStatus(Enum):
    """Alert status states."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ESCALATED = "escalated"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    SLACK = "slack"
    TEAMS = "teams"
    API = "api"


@dataclass
class AlertRule:
    """Configuration for compliance alert rules."""
    rule_id: str
    name: str
    description: str
    alert_type: AlertType
    severity: AlertSeverity
    condition: Dict[str, Any]  # JSON-based condition logic
    threshold: Optional[Union[float, int]] = None
    frameworks: Optional[List[str]] = None
    enabled: bool = True
    suppression_window: Optional[int] = None  # minutes
    escalation_time: Optional[int] = None  # minutes
    notification_channels: Optional[List[NotificationChannel]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Alert:
    """Compliance alert instance."""
    alert_id: str
    rule_id: str
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    organization_id: str
    framework: Optional[str] = None
    triggered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalated_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    escalated_to: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    remediation_suggestions: Optional[List[str]] = None
    related_alerts: Optional[List[str]] = None


@dataclass
class NotificationTemplate:
    """Notification message template."""
    template_id: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    format_type: str = "text"  # text, html, markdown


class ComplianceAlertSystem:
    """
    Comprehensive compliance alerting system with configurable rules,
    real-time monitoring, and multi-channel notifications.
    """

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.logger = logging.getLogger(f"{__name__}.{organization_id}")
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_templates = self._initialize_notification_templates()
        self.suppression_tracker: Dict[str, datetime] = {}
        self.escalation_tracker: Dict[str, datetime] = {}

    def _initialize_notification_templates(self) -> Dict[str, NotificationTemplate]:
        """Initialize default notification templates."""
        templates = {}
        
        # Email templates
        templates["validation_failure_email"] = NotificationTemplate(
            template_id="validation_failure_email",
            channel=NotificationChannel.EMAIL,
            subject_template="🚨 Compliance Validation Failure - {framework}",
            body_template="""
            <h2>Compliance Validation Failure Alert</h2>
            <p><strong>Organization:</strong> {organization_id}</p>
            <p><strong>Framework:</strong> {framework}</p>
            <p><strong>Severity:</strong> {severity}</p>
            <p><strong>Triggered:</strong> {triggered_at}</p>
            
            <h3>Alert Details</h3>
            <p>{message}</p>
            
            <h3>Recommended Actions</h3>
            <ul>
                {remediation_suggestions}
            </ul>
            
            <p>Please review and address this compliance issue promptly.</p>
            """,
            format_type="html"
        )
        
        templates["risk_threshold_email"] = NotificationTemplate(
            template_id="risk_threshold_email",
            channel=NotificationChannel.EMAIL,
            subject_template="⚠️ Risk Threshold Exceeded - {framework}",
            body_template="""
            <h2>Risk Threshold Exceeded Alert</h2>
            <p><strong>Organization:</strong> {organization_id}</p>
            <p><strong>Framework:</strong> {framework}</p>
            <p><strong>Current Risk Level:</strong> {risk_level}</p>
            <p><strong>Threshold:</strong> {threshold}</p>
            <p><strong>Triggered:</strong> {triggered_at}</p>
            
            <h3>Alert Details</h3>
            <p>{message}</p>
            
            <p>Immediate attention may be required to mitigate compliance risks.</p>
            """,
            format_type="html"
        )
        
        # Slack templates
        templates["validation_failure_slack"] = NotificationTemplate(
            template_id="validation_failure_slack",
            channel=NotificationChannel.SLACK,
            subject_template="Compliance Alert",
            body_template="""
            🚨 *Compliance Validation Failure*
            
            *Organization:* {organization_id}
            *Framework:* {framework}
            *Severity:* {severity}
            *Time:* {triggered_at}
            
            *Details:* {message}
            
            Please review and address this compliance issue.
            """,
            format_type="markdown"
        )
        
        return templates

    def add_alert_rule(self, alert_rule: AlertRule) -> None:
        """Add or update an alert rule."""
        try:
            alert_rule.created_at = alert_rule.created_at or datetime.now()
            alert_rule.updated_at = datetime.now()
            
            self.alert_rules[alert_rule.rule_id] = alert_rule
            
            self.logger.info(f"Alert rule added/updated: {alert_rule.rule_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding alert rule: {str(e)}")
            raise

    def remove_alert_rule(self, rule_id: str) -> bool:
        """Remove an alert rule."""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                self.logger.info(f"Alert rule removed: {rule_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing alert rule: {str(e)}")
            raise

    async def evaluate_compliance_result(self, compliance_result: ComplianceResult) -> List[Alert]:
        """
        Evaluate compliance result against alert rules and trigger alerts.
        
        Args:
            compliance_result: Compliance validation result
            
        Returns:
            List of triggered alerts
        """
        try:
            triggered_alerts = []
            
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # Check if rule applies to this result
                if rule.frameworks and not any(fw in compliance_result.framework_results 
                                             for fw in rule.frameworks):
                    continue
                
                # Check suppression window
                if self._is_rule_suppressed(rule_id):
                    continue
                
                # Evaluate rule condition
                if await self._evaluate_rule_condition(rule, compliance_result):
                    alert = await self._create_alert_from_rule(rule, compliance_result)
                    triggered_alerts.append(alert)
                    
                    # Update suppression tracker
                    if rule.suppression_window:
                        self.suppression_tracker[rule_id] = datetime.now()
            
            # Process triggered alerts
            for alert in triggered_alerts:
                await self._process_alert(alert)
            
            self.logger.info(f"Evaluated compliance result, triggered {len(triggered_alerts)} alerts")
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"Error evaluating compliance result: {str(e)}")
            raise

    async def evaluate_metrics(self, metrics: ComplianceMetrics) -> List[Alert]:
        """
        Evaluate compliance metrics against alert rules.
        
        Args:
            metrics: Compliance metrics to evaluate
            
        Returns:
            List of triggered alerts
        """
        try:
            triggered_alerts = []
            
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                if self._is_rule_suppressed(rule_id):
                    continue
                
                # Evaluate metrics-based rules
                if await self._evaluate_metrics_rule(rule, metrics):
                    alert = await self._create_alert_from_metrics(rule, metrics)
                    triggered_alerts.append(alert)
                    
                    if rule.suppression_window:
                        self.suppression_tracker[rule_id] = datetime.now()
            
            for alert in triggered_alerts:
                await self._process_alert(alert)
            
            self.logger.info(f"Evaluated metrics, triggered {len(triggered_alerts)} alerts")
            return triggered_alerts
            
        except Exception as e:
            self.logger.error(f"Error evaluating metrics: {str(e)}")
            raise

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an active alert.
        
        Args:
            alert_id: Alert identifier
            acknowledged_by: User acknowledging the alert
            
        Returns:
            True if successfully acknowledged
        """
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now()
                alert.acknowledged_by = acknowledged_by
                
                self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {str(e)}")
            raise

    async def resolve_alert(self, alert_id: str, resolved_by: str, resolution_note: Optional[str] = None) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert identifier
            resolved_by: User resolving the alert
            resolution_note: Optional resolution note
            
        Returns:
            True if successfully resolved
        """
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now()
                alert.resolved_by = resolved_by
                
                if resolution_note:
                    alert.metadata = alert.metadata or {}
                    alert.metadata["resolution_note"] = resolution_note
                
                # Move to history
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]
                
                self.logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error resolving alert: {str(e)}")
            raise

    async def escalate_alert(self, alert_id: str, escalated_to: str) -> bool:
        """
        Escalate an alert to higher priority.
        
        Args:
            alert_id: Alert identifier
            escalated_to: User/role to escalate to
            
        Returns:
            True if successfully escalated
        """
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ESCALATED
                alert.escalated_at = datetime.now()
                alert.escalated_to = escalated_to
                
                # Increase severity if not already critical
                if alert.severity != AlertSeverity.CRITICAL:
                    if alert.severity == AlertSeverity.LOW:
                        alert.severity = AlertSeverity.MEDIUM
                    elif alert.severity == AlertSeverity.MEDIUM:
                        alert.severity = AlertSeverity.HIGH
                    elif alert.severity == AlertSeverity.HIGH:
                        alert.severity = AlertSeverity.CRITICAL
                
                # Send escalation notifications
                await self._send_escalation_notifications(alert)
                
                self.logger.info(f"Alert escalated: {alert_id} to {escalated_to}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error escalating alert: {str(e)}")
            raise

    def get_active_alerts(
        self,
        severity_filter: Optional[List[AlertSeverity]] = None,
        framework_filter: Optional[List[str]] = None,
        alert_type_filter: Optional[List[AlertType]] = None
    ) -> List[Alert]:
        """
        Get active alerts with optional filtering.
        
        Args:
            severity_filter: Filter by severity levels
            framework_filter: Filter by frameworks
            alert_type_filter: Filter by alert types
            
        Returns:
            List of filtered active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if severity_filter:
            alerts = [a for a in alerts if a.severity in severity_filter]
        
        if framework_filter:
            alerts = [a for a in alerts if a.framework in framework_filter]
        
        if alert_type_filter:
            alerts = [a for a in alerts if a.alert_type in alert_type_filter]
        
        # Sort by severity and triggered time
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3
        }
        
        alerts.sort(key=lambda x: (severity_order[x.severity], x.triggered_at or datetime.min))
        
        return alerts

    def get_alert_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get alert statistics for the specified time period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Alert statistics dictionary
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Combine active and historical alerts
            all_alerts = list(self.active_alerts.values()) + [
                a for a in self.alert_history 
                if a.triggered_at and a.triggered_at >= cutoff_date
            ]
            
            # Calculate statistics
            total_alerts = len(all_alerts)
            
            # Count by severity
            severity_counts = {}
            for severity in AlertSeverity:
                severity_counts[severity.value] = len([a for a in all_alerts if a.severity == severity])
            
            # Count by type
            type_counts = {}
            for alert_type in AlertType:
                type_counts[alert_type.value] = len([a for a in all_alerts if a.alert_type == alert_type])
            
            # Count by status
            status_counts = {}
            for status in AlertStatus:
                status_counts[status.value] = len([a for a in all_alerts if a.status == status])
            
            # Count by framework
            framework_counts = {}
            for alert in all_alerts:
                if alert.framework:
                    framework_counts[alert.framework] = framework_counts.get(alert.framework, 0) + 1
            
            # Calculate resolution metrics
            resolved_alerts = [a for a in all_alerts if a.status == AlertStatus.RESOLVED and a.resolved_at]
            avg_resolution_time = 0
            if resolved_alerts:
                resolution_times = [
                    (a.resolved_at - a.triggered_at).total_seconds() / 3600  # hours
                    for a in resolved_alerts
                    if a.triggered_at and a.resolved_at
                ]
                avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
            
            return {
                "period_days": days,
                "total_alerts": total_alerts,
                "active_alerts": len(self.active_alerts),
                "severity_distribution": severity_counts,
                "type_distribution": type_counts,
                "status_distribution": status_counts,
                "framework_distribution": framework_counts,
                "resolution_metrics": {
                    "average_resolution_time_hours": round(avg_resolution_time, 2),
                    "resolved_count": len(resolved_alerts),
                    "resolution_rate": len(resolved_alerts) / total_alerts * 100 if total_alerts > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating alert statistics: {str(e)}")
            raise

    async def _evaluate_rule_condition(self, rule: AlertRule, compliance_result: ComplianceResult) -> bool:
        """Evaluate whether rule condition is met for compliance result."""
        try:
            condition = rule.condition
            
            if rule.alert_type == AlertType.VALIDATION_FAILURE:
                # Check if any validation failed
                failed_validations = [
                    r for r in compliance_result.framework_results.values()
                    if r.status == ComplianceStatus.FAILED
                ]
                return len(failed_validations) > 0
            
            elif rule.alert_type == AlertType.COMPLIANCE_DEGRADATION:
                # Check if compliance score is below threshold
                threshold = rule.threshold or condition.get("threshold", 80)
                return compliance_result.compliance_score < threshold
            
            elif rule.alert_type == AlertType.RISK_THRESHOLD_EXCEEDED:
                # Check if risk level exceeds threshold
                risk_levels = {
                    RiskLevel.LOW: 1,
                    RiskLevel.MEDIUM: 2,
                    RiskLevel.HIGH: 3,
                    RiskLevel.CRITICAL: 4
                }
                threshold = rule.threshold or condition.get("threshold", 3)
                current_risk = risk_levels.get(compliance_result.risk_level, 0)
                return current_risk >= threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating rule condition: {str(e)}")
            return False

    async def _evaluate_metrics_rule(self, rule: AlertRule, metrics: ComplianceMetrics) -> bool:
        """Evaluate rule condition against metrics."""
        try:
            condition = rule.condition
            
            if rule.alert_type == AlertType.THRESHOLD_BREACH:
                metric_path = condition.get("metric_path")
                threshold = rule.threshold or condition.get("threshold")
                operator = condition.get("operator", "greater_than")
                
                if metric_path and threshold is not None:
                    metric_value = self._get_metric_value(metrics, metric_path)
                    
                    if operator == "greater_than":
                        return metric_value > threshold
                    elif operator == "less_than":
                        return metric_value < threshold
                    elif operator == "equals":
                        return metric_value == threshold
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error evaluating metrics rule: {str(e)}")
            return False

    def _get_metric_value(self, metrics: ComplianceMetrics, path: str) -> Union[float, int]:
        """Extract metric value using dot notation path."""
        try:
            parts = path.split('.')
            value = asdict(metrics)
            
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return 0
            
            return float(value) if isinstance(value, (int, float, Decimal)) else 0
            
        except Exception:
            return 0

    async def _create_alert_from_rule(self, rule: AlertRule, compliance_result: ComplianceResult) -> Alert:
        """Create alert from rule and compliance result."""
        alert_id = str(uuid.uuid4())
        
        # Determine framework
        framework = None
        if rule.frameworks:
            framework = rule.frameworks[0]
        elif compliance_result.framework_results:
            framework = list(compliance_result.framework_results.keys())[0]
        
        # Generate message
        message = self._generate_alert_message(rule, compliance_result)
        
        # Generate remediation suggestions
        remediation = self._generate_remediation_suggestions(rule, compliance_result)
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            title=rule.name,
            message=message,
            organization_id=self.organization_id,
            framework=framework,
            triggered_at=datetime.now(),
            metadata={
                "compliance_score": compliance_result.compliance_score,
                "risk_level": compliance_result.risk_level.value,
                "execution_time_ms": compliance_result.execution_time_ms
            },
            remediation_suggestions=remediation
        )
        
        return alert

    async def _create_alert_from_metrics(self, rule: AlertRule, metrics: ComplianceMetrics) -> Alert:
        """Create alert from rule and metrics."""
        alert_id = str(uuid.uuid4())
        
        message = f"Metrics threshold exceeded for rule: {rule.name}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            alert_type=rule.alert_type,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            title=rule.name,
            message=message,
            organization_id=self.organization_id,
            triggered_at=datetime.now(),
            metadata={"metrics": asdict(metrics)}
        )
        
        return alert

    def _generate_alert_message(self, rule: AlertRule, compliance_result: ComplianceResult) -> str:
        """Generate human-readable alert message."""
        if rule.alert_type == AlertType.VALIDATION_FAILURE:
            failed_count = len([r for r in compliance_result.framework_results.values() 
                              if r.status == ComplianceStatus.FAILED])
            return f"Compliance validation failed for {failed_count} framework(s). Review and address validation errors."
        
        elif rule.alert_type == AlertType.COMPLIANCE_DEGRADATION:
            return f"Compliance score ({compliance_result.compliance_score:.1f}%) has fallen below acceptable threshold."
        
        elif rule.alert_type == AlertType.RISK_THRESHOLD_EXCEEDED:
            return f"Risk level ({compliance_result.risk_level.value}) has exceeded acceptable threshold."
        
        return rule.description

    def _generate_remediation_suggestions(self, rule: AlertRule, compliance_result: ComplianceResult) -> List[str]:
        """Generate remediation suggestions for alert."""
        suggestions = []
        
        if rule.alert_type == AlertType.VALIDATION_FAILURE:
            suggestions.extend([
                "Review failed validation results and identify root causes",
                "Update data or configuration to meet compliance requirements",
                "Consult regulatory documentation for specific requirements",
                "Contact compliance team for assistance if needed"
            ])
        
        elif rule.alert_type == AlertType.COMPLIANCE_DEGRADATION:
            suggestions.extend([
                "Analyze compliance gaps and prioritize high-impact issues",
                "Review recent changes that may have affected compliance",
                "Implement corrective measures for failing validation rules",
                "Schedule compliance review meeting with relevant stakeholders"
            ])
        
        return suggestions

    async def _process_alert(self, alert: Alert) -> None:
        """Process a triggered alert."""
        try:
            # Add to active alerts
            self.active_alerts[alert.alert_id] = alert
            
            # Send notifications
            await self._send_alert_notifications(alert)
            
            # Schedule escalation if configured
            rule = self.alert_rules.get(alert.rule_id)
            if rule and rule.escalation_time:
                self.escalation_tracker[alert.alert_id] = datetime.now() + timedelta(minutes=rule.escalation_time)
            
            self.logger.info(f"Alert processed: {alert.alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing alert: {str(e)}")
            raise

    async def _send_alert_notifications(self, alert: Alert) -> None:
        """Send alert notifications through configured channels."""
        try:
            rule = self.alert_rules.get(alert.rule_id)
            channels = rule.notification_channels if rule else [NotificationChannel.DASHBOARD]
            
            for channel in channels:
                await self._send_notification(alert, channel)
            
        except Exception as e:
            self.logger.error(f"Error sending alert notifications: {str(e)}")

    async def _send_notification(self, alert: Alert, channel: NotificationChannel) -> None:
        """Send notification through specific channel."""
        try:
            # In production, this would integrate with actual notification services
            self.logger.info(f"Sending {channel.value} notification for alert {alert.alert_id}")
            
            # Placeholder for actual notification implementation
            notification_data = {
                "alert_id": alert.alert_id,
                "channel": channel.value,
                "severity": alert.severity.value,
                "message": alert.message,
                "organization_id": alert.organization_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # This would be replaced with actual notification service calls
            self.logger.debug(f"Notification data: {json.dumps(notification_data, indent=2)}")
            
        except Exception as e:
            self.logger.error(f"Error sending {channel.value} notification: {str(e)}")

    async def _send_escalation_notifications(self, alert: Alert) -> None:
        """Send escalation notifications."""
        try:
            # Send to escalated recipient
            self.logger.info(f"Sending escalation notification for alert {alert.alert_id} to {alert.escalated_to}")
            
            # In production, would send to management/escalation channels
            
        except Exception as e:
            self.logger.error(f"Error sending escalation notification: {str(e)}")

    def _is_rule_suppressed(self, rule_id: str) -> bool:
        """Check if rule is in suppression window."""
        if rule_id not in self.suppression_tracker:
            return False
        
        rule = self.alert_rules.get(rule_id)
        if not rule or not rule.suppression_window:
            return False
        
        last_triggered = self.suppression_tracker[rule_id]
        suppression_end = last_triggered + timedelta(minutes=rule.suppression_window)
        
        return datetime.now() < suppression_end