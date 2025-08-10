"""
Hybrid Service: Escalation Manager
Manages error escalation workflows across the platform
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core_platform.database import get_db_session
from core_platform.models.escalation import EscalationPolicy, EscalationLevel, EscalationInstance
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class EscalationTrigger(str, Enum):
    """Triggers for escalation"""
    ERROR_FREQUENCY = "error_frequency"
    ERROR_SEVERITY = "error_severity"
    RECOVERY_FAILURE = "recovery_failure"
    MANUAL_REQUEST = "manual_request"
    TIME_THRESHOLD = "time_threshold"
    BUSINESS_IMPACT = "business_impact"
    SLA_BREACH = "sla_breach"
    PATTERN_DETECTED = "pattern_detected"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


class EscalationStatus(str, Enum):
    """Status of escalation"""
    PENDING = "pending"
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ESCALATED_FURTHER = "escalated_further"


class EscalationLevel(str, Enum):
    """Levels of escalation"""
    L1_AUTOMATED = "l1_automated"
    L2_TEAM_LEAD = "l2_team_lead"
    L3_SENIOR_ENGINEER = "l3_senior_engineer"
    L4_MANAGER = "l4_manager"
    L5_DIRECTOR = "l5_director"
    L6_EXECUTIVE = "l6_executive"
    EXTERNAL_VENDOR = "external_vendor"
    CUSTOMER_NOTIFICATION = "customer_notification"


class EscalationSeverity(str, Enum):
    """Severity levels for escalation"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class NotificationChannel(str, Enum):
    """Notification channels for escalation"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    PAGER_DUTY = "pager_duty"
    WEBHOOK = "webhook"
    PHONE_CALL = "phone_call"
    DASHBOARD = "dashboard"


@dataclass
class EscalationRule:
    """Rule defining when and how to escalate"""
    rule_id: str
    name: str
    description: str
    trigger: EscalationTrigger
    conditions: Dict[str, Any]
    target_level: EscalationLevel
    severity_threshold: EscalationSeverity
    time_threshold_minutes: int
    frequency_threshold: int
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationPolicy:
    """Policy defining escalation workflow"""
    policy_id: str
    name: str
    description: str
    service_scope: List[str]  # Services this policy applies to
    error_types: List[str]
    escalation_levels: List[Dict[str, Any]]  # Level definitions
    notification_channels: List[NotificationChannel]
    time_windows: Dict[str, Any]  # Business hours, weekends, etc.
    auto_escalation_enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationInstance:
    """Instance of an active escalation"""
    escalation_id: str
    error_id: str
    policy_id: str
    current_level: EscalationLevel
    severity: EscalationSeverity
    trigger: EscalationTrigger
    status: EscalationStatus
    created_at: datetime
    escalated_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    assignee: Optional[str]
    escalation_path: List[Dict[str, Any]]  # History of escalation steps
    context: Dict[str, Any]
    notifications_sent: List[Dict[str, Any]]
    sla_breach_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EscalationTarget:
    """Target for escalation notifications"""
    target_id: str
    name: str
    level: EscalationLevel
    contact_methods: List[Dict[str, Any]]  # Channel and contact info
    availability_schedule: Dict[str, Any]
    backup_targets: List[str]
    auto_acknowledge_timeout_minutes: int = 30
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EscalationManager:
    """
    Escalation Manager service
    Manages error escalation workflows across the platform
    """
    
    def __init__(self):
        """Initialize escalation manager service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.escalation_instances: Dict[str, EscalationInstance] = {}
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        self.escalation_rules: Dict[str, EscalationRule] = {}
        self.escalation_targets: Dict[str, EscalationTarget] = {}
        self.active_escalations: Dict[str, asyncio.Task] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 86400  # 24 hours
        self.sla_warning_threshold_minutes = 15
        self.auto_escalation_interval_minutes = 30
        self.max_escalation_level = EscalationLevel.L6_EXECUTIVE
        self.escalation_retention_days = 30
        
        # Initialize default components
        self._initialize_default_policies()
        self._initialize_default_rules()
        self._initialize_default_targets()
    
    def _initialize_default_policies(self):
        """Initialize default escalation policies"""
        default_policies = [
            # Critical error policy
            EscalationPolicy(
                policy_id="critical_error_policy",
                name="Critical Error Escalation",
                description="Escalation policy for critical errors",
                service_scope=["*"],
                error_types=["system", "database", "integration"],
                escalation_levels=[
                    {
                        "level": EscalationLevel.L1_AUTOMATED.value,
                        "timeout_minutes": 5,
                        "targets": ["automated_response"],
                        "actions": ["auto_recovery", "notification"]
                    },
                    {
                        "level": EscalationLevel.L2_TEAM_LEAD.value,
                        "timeout_minutes": 15,
                        "targets": ["team_lead_oncall"],
                        "actions": ["manual_intervention", "status_update"]
                    },
                    {
                        "level": EscalationLevel.L3_SENIOR_ENGINEER.value,
                        "timeout_minutes": 30,
                        "targets": ["senior_engineer_oncall"],
                        "actions": ["deep_investigation", "customer_communication"]
                    },
                    {
                        "level": EscalationLevel.L4_MANAGER.value,
                        "timeout_minutes": 60,
                        "targets": ["engineering_manager"],
                        "actions": ["executive_notification", "external_support"]
                    }
                ],
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK,
                    NotificationChannel.PAGER_DUTY
                ],
                time_windows={
                    "business_hours": {"start": "09:00", "end": "18:00"},
                    "weekend_multiplier": 2.0,
                    "holiday_multiplier": 2.0
                }
            ),
            
            # High severity policy
            EscalationPolicy(
                policy_id="high_severity_policy",
                name="High Severity Error Escalation",
                description="Escalation policy for high severity errors",
                service_scope=["si_*", "app_*"],
                error_types=["business_logic", "validation", "authentication"],
                escalation_levels=[
                    {
                        "level": EscalationLevel.L1_AUTOMATED.value,
                        "timeout_minutes": 10,
                        "targets": ["automated_response"],
                        "actions": ["auto_recovery", "logging"]
                    },
                    {
                        "level": EscalationLevel.L2_TEAM_LEAD.value,
                        "timeout_minutes": 30,
                        "targets": ["team_lead_oncall"],
                        "actions": ["investigation", "status_update"]
                    },
                    {
                        "level": EscalationLevel.L3_SENIOR_ENGINEER.value,
                        "timeout_minutes": 60,
                        "targets": ["senior_engineer_oncall"],
                        "actions": ["detailed_analysis", "fix_deployment"]
                    }
                ],
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.SLACK
                ],
                time_windows={
                    "business_hours": {"start": "08:00", "end": "20:00"}
                }
            ),
            
            # Business impact policy
            EscalationPolicy(
                policy_id="business_impact_policy",
                name="Business Impact Escalation",
                description="Escalation for errors with significant business impact",
                service_scope=["invoice_*", "payment_*", "firs_*"],
                error_types=["*"],
                escalation_levels=[
                    {
                        "level": EscalationLevel.L2_TEAM_LEAD.value,
                        "timeout_minutes": 10,
                        "targets": ["business_team_lead"],
                        "actions": ["impact_assessment", "customer_notification"]
                    },
                    {
                        "level": EscalationLevel.L4_MANAGER.value,
                        "timeout_minutes": 30,
                        "targets": ["business_manager"],
                        "actions": ["executive_briefing", "customer_communication"]
                    },
                    {
                        "level": EscalationLevel.CUSTOMER_NOTIFICATION.value,
                        "timeout_minutes": 60,
                        "targets": ["customer_success"],
                        "actions": ["customer_notification", "status_page_update"]
                    }
                ],
                notification_channels=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.TEAMS,
                    NotificationChannel.WEBHOOK
                ],
                time_windows={
                    "business_hours": {"start": "07:00", "end": "22:00"}
                }
            )
        ]
        
        for policy in default_policies:
            self.escalation_policies[policy.policy_id] = policy
    
    def _initialize_default_rules(self):
        """Initialize default escalation rules"""
        default_rules = [
            # Frequency-based escalation
            EscalationRule(
                rule_id="high_frequency_errors",
                name="High Frequency Error Escalation",
                description="Escalate when error frequency exceeds threshold",
                trigger=EscalationTrigger.ERROR_FREQUENCY,
                conditions={
                    "frequency_threshold": 10,
                    "time_window_minutes": 30,
                    "error_types": ["validation", "business_logic"]
                },
                target_level=EscalationLevel.L2_TEAM_LEAD,
                severity_threshold=EscalationSeverity.MEDIUM,
                time_threshold_minutes=30,
                frequency_threshold=10
            ),
            
            # Critical error immediate escalation
            EscalationRule(
                rule_id="critical_immediate_escalation",
                name="Critical Error Immediate Escalation",
                description="Immediately escalate critical errors",
                trigger=EscalationTrigger.ERROR_SEVERITY,
                conditions={
                    "severity": "critical",
                    "immediate": True
                },
                target_level=EscalationLevel.L3_SENIOR_ENGINEER,
                severity_threshold=EscalationSeverity.CRITICAL,
                time_threshold_minutes=0,
                frequency_threshold=1
            ),
            
            # Recovery failure escalation
            EscalationRule(
                rule_id="recovery_failure_escalation",
                name="Recovery Failure Escalation",
                description="Escalate when recovery attempts fail",
                trigger=EscalationTrigger.RECOVERY_FAILURE,
                conditions={
                    "max_recovery_attempts": 3,
                    "recovery_failure_rate": 0.8
                },
                target_level=EscalationLevel.L3_SENIOR_ENGINEER,
                severity_threshold=EscalationSeverity.HIGH,
                time_threshold_minutes=15,
                frequency_threshold=3
            ),
            
            # SLA breach escalation
            EscalationRule(
                rule_id="sla_breach_escalation",
                name="SLA Breach Escalation",
                description="Escalate when SLA thresholds are breached",
                trigger=EscalationTrigger.SLA_BREACH,
                conditions={
                    "sla_type": "response_time",
                    "breach_threshold_minutes": 60
                },
                target_level=EscalationLevel.L4_MANAGER,
                severity_threshold=EscalationSeverity.HIGH,
                time_threshold_minutes=60,
                frequency_threshold=1
            ),
            
            # Business hours pattern escalation
            EscalationRule(
                rule_id="business_hours_pattern_escalation",
                name="Business Hours Pattern Escalation",
                description="Escalate patterns during business hours",
                trigger=EscalationTrigger.PATTERN_DETECTED,
                conditions={
                    "pattern_frequency": 5,
                    "business_hours_only": True,
                    "customer_facing": True
                },
                target_level=EscalationLevel.L2_TEAM_LEAD,
                severity_threshold=EscalationSeverity.MEDIUM,
                time_threshold_minutes=20,
                frequency_threshold=5
            )
        ]
        
        for rule in default_rules:
            self.escalation_rules[rule.rule_id] = rule
    
    def _initialize_default_targets(self):
        """Initialize default escalation targets"""
        default_targets = [
            # Automated response
            EscalationTarget(
                target_id="automated_response",
                name="Automated Response System",
                level=EscalationLevel.L1_AUTOMATED,
                contact_methods=[
                    {"channel": NotificationChannel.WEBHOOK, "endpoint": "/api/automated-response"}
                ],
                availability_schedule={"24x7": True},
                backup_targets=[],
                auto_acknowledge_timeout_minutes=5
            ),
            
            # Team lead
            EscalationTarget(
                target_id="team_lead_oncall",
                name="Team Lead On-Call",
                level=EscalationLevel.L2_TEAM_LEAD,
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "teamlead-oncall@taxpoynt.com"},
                    {"channel": NotificationChannel.SLACK, "channel": "#oncall-alerts"},
                    {"channel": NotificationChannel.SMS, "number": "+1234567890"}
                ],
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "20:00"},
                    "on_call_rotation": True
                },
                backup_targets=["senior_engineer_oncall"],
                auto_acknowledge_timeout_minutes=15
            ),
            
            # Senior engineer
            EscalationTarget(
                target_id="senior_engineer_oncall",
                name="Senior Engineer On-Call",
                level=EscalationLevel.L3_SENIOR_ENGINEER,
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "senior-oncall@taxpoynt.com"},
                    {"channel": NotificationChannel.PAGER_DUTY, "service_key": "senior-engineer-service"},
                    {"channel": NotificationChannel.PHONE_CALL, "number": "+1234567891"}
                ],
                availability_schedule={"24x7": True},
                backup_targets=["engineering_manager"],
                auto_acknowledge_timeout_minutes=30
            ),
            
            # Engineering manager
            EscalationTarget(
                target_id="engineering_manager",
                name="Engineering Manager",
                level=EscalationLevel.L4_MANAGER,
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "eng-manager@taxpoynt.com"},
                    {"channel": NotificationChannel.TEAMS, "team": "engineering-leadership"},
                    {"channel": NotificationChannel.SMS, "number": "+1234567892"}
                ],
                availability_schedule={
                    "business_hours": {"start": "07:00", "end": "21:00"},
                    "emergency_contact": True
                },
                backup_targets=["engineering_director"],
                auto_acknowledge_timeout_minutes=60
            ),
            
            # Business team lead
            EscalationTarget(
                target_id="business_team_lead",
                name="Business Team Lead",
                level=EscalationLevel.L2_TEAM_LEAD,
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "business-lead@taxpoynt.com"},
                    {"channel": NotificationChannel.TEAMS, "team": "business-operations"}
                ],
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "18:00"}
                },
                backup_targets=["business_manager"],
                auto_acknowledge_timeout_minutes=30
            ),
            
            # Customer success
            EscalationTarget(
                target_id="customer_success",
                name="Customer Success Team",
                level=EscalationLevel.CUSTOMER_NOTIFICATION,
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "customer-success@taxpoynt.com"},
                    {"channel": NotificationChannel.WEBHOOK, "endpoint": "/api/customer-notification"}
                ],
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "18:00"}
                },
                backup_targets=[],
                auto_acknowledge_timeout_minutes=45
            )
        ]
        
        for target in default_targets:
            self.escalation_targets[target.target_id] = target
    
    async def initialize(self):
        """Initialize the escalation manager service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing escalation manager service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._escalation_monitor())
            asyncio.create_task(self._sla_monitor())
            asyncio.create_task(self._cleanup_old_escalations())
            
            self.is_initialized = True
            self.logger.info("Escalation manager service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing escalation manager service: {str(e)}")
            raise
    
    async def evaluate_escalation(
        self,
        error_id: str,
        error_data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Optional[str]:
        """Evaluate if an error should be escalated"""
        try:
            # Find applicable rules
            applicable_rules = await self._find_applicable_rules(error_data, context)
            
            if not applicable_rules:
                return None
            
            # Check if escalation criteria are met
            for rule in applicable_rules:
                if await self._check_escalation_criteria(rule, error_data, context):
                    # Create escalation instance
                    escalation_id = await self._create_escalation_instance(
                        error_id, rule, error_data, context
                    )
                    
                    if escalation_id:
                        # Start escalation process
                        await self._start_escalation(escalation_id)
                        return escalation_id
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error evaluating escalation: {str(e)}")
            return None
    
    async def _find_applicable_rules(
        self,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[EscalationRule]:
        """Find escalation rules applicable to the error"""
        try:
            applicable_rules = []
            
            error_type = error_data.get("error_type", "unknown")
            severity = error_data.get("severity", "medium")
            service_name = context.get("service_name", "") if context else ""
            
            for rule in self.escalation_rules.values():
                if not rule.enabled:
                    continue
                
                # Check trigger type
                if rule.trigger == EscalationTrigger.ERROR_SEVERITY:
                    if severity == "critical" and rule.severity_threshold == EscalationSeverity.CRITICAL:
                        applicable_rules.append(rule)
                
                elif rule.trigger == EscalationTrigger.ERROR_FREQUENCY:
                    # Check frequency conditions (would need historical data)
                    if await self._check_frequency_conditions(rule, error_data, context):
                        applicable_rules.append(rule)
                
                elif rule.trigger == EscalationTrigger.BUSINESS_IMPACT:
                    # Check business impact
                    if await self._check_business_impact(service_name, error_type):
                        applicable_rules.append(rule)
                
                elif rule.trigger == EscalationTrigger.SLA_BREACH:
                    # Check SLA conditions
                    if await self._check_sla_conditions(rule, context):
                        applicable_rules.append(rule)
            
            # Sort by severity and frequency threshold
            applicable_rules.sort(key=lambda r: (
                ["critical", "high", "medium", "low"].index(r.severity_threshold.value),
                r.frequency_threshold
            ))
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error(f"Error finding applicable rules: {str(e)}")
            return []
    
    async def _check_escalation_criteria(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if escalation criteria are met for a rule"""
        try:
            # Check basic conditions
            error_severity = error_data.get("severity", "medium")
            severity_order = ["info", "low", "medium", "high", "critical"]
            
            required_severity_index = severity_order.index(rule.severity_threshold.value)
            current_severity_index = severity_order.index(error_severity)
            
            if current_severity_index < required_severity_index:
                return False
            
            # Check trigger-specific conditions
            if rule.trigger == EscalationTrigger.ERROR_FREQUENCY:
                return await self._check_frequency_threshold(rule, error_data, context)
            
            elif rule.trigger == EscalationTrigger.TIME_THRESHOLD:
                return await self._check_time_threshold(rule, error_data, context)
            
            elif rule.trigger == EscalationTrigger.RECOVERY_FAILURE:
                return await self._check_recovery_failure(rule, error_data, context)
            
            elif rule.trigger == EscalationTrigger.PATTERN_DETECTED:
                return await self._check_pattern_conditions(rule, error_data, context)
            
            # Default to true for immediate escalation triggers
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking escalation criteria: {str(e)}")
            return False
    
    async def _check_frequency_conditions(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check frequency-based escalation conditions"""
        try:
            conditions = rule.conditions
            frequency_threshold = conditions.get("frequency_threshold", 10)
            time_window_minutes = conditions.get("time_window_minutes", 30)
            
            # Get error frequency from cache/database
            # This would typically query recent error history
            
            # Simplified check - assume frequency check passed
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking frequency conditions: {str(e)}")
            return False
    
    async def _check_business_impact(self, service_name: str, error_type: str) -> bool:
        """Check if error has significant business impact"""
        try:
            # Business-critical services
            critical_services = [
                "invoice_service",
                "payment_service", 
                "firs_transmission",
                "authentication_service"
            ]
            
            # Business-critical error types
            critical_error_types = [
                "payment_failure",
                "invoice_generation_failure",
                "firs_submission_failure",
                "authentication_failure"
            ]
            
            is_critical_service = any(critical in service_name.lower() for critical in critical_services)
            is_critical_error = error_type.lower() in critical_error_types
            
            return is_critical_service or is_critical_error
            
        except Exception as e:
            self.logger.error(f"Error checking business impact: {str(e)}")
            return False
    
    async def _check_sla_conditions(self, rule: EscalationRule, context: Dict[str, Any]) -> bool:
        """Check SLA breach conditions"""
        try:
            conditions = rule.conditions
            breach_threshold_minutes = conditions.get("breach_threshold_minutes", 60)
            
            # Check if operation has been running longer than SLA
            operation_start = context.get("operation_start_time") if context else None
            if operation_start:
                if isinstance(operation_start, str):
                    operation_start = datetime.fromisoformat(operation_start)
                
                duration_minutes = (datetime.now(timezone.utc) - operation_start).total_seconds() / 60
                return duration_minutes > breach_threshold_minutes
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking SLA conditions: {str(e)}")
            return False
    
    async def _check_frequency_threshold(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if error frequency exceeds threshold"""
        try:
            # This would check actual error frequency from stored data
            # For now, simulate frequency check
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking frequency threshold: {str(e)}")
            return False
    
    async def _check_time_threshold(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if time threshold for escalation is reached"""
        try:
            error_occurred_at = error_data.get("occurred_at")
            if isinstance(error_occurred_at, str):
                error_occurred_at = datetime.fromisoformat(error_occurred_at)
            
            if error_occurred_at:
                time_since_error = (datetime.now(timezone.utc) - error_occurred_at).total_seconds() / 60
                return time_since_error >= rule.time_threshold_minutes
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking time threshold: {str(e)}")
            return False
    
    async def _check_recovery_failure(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if recovery attempts have failed"""
        try:
            conditions = rule.conditions
            max_attempts = conditions.get("max_recovery_attempts", 3)
            failure_rate = conditions.get("recovery_failure_rate", 0.8)
            
            # Get recovery attempt data
            recovery_attempts = context.get("recovery_attempts", 0) if context else 0
            recovery_failures = context.get("recovery_failures", 0) if context else 0
            
            if recovery_attempts >= max_attempts:
                current_failure_rate = recovery_failures / recovery_attempts if recovery_attempts > 0 else 0
                return current_failure_rate >= failure_rate
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking recovery failure: {str(e)}")
            return False
    
    async def _check_pattern_conditions(
        self,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check pattern-based escalation conditions"""
        try:
            conditions = rule.conditions
            pattern_frequency = conditions.get("pattern_frequency", 5)
            business_hours_only = conditions.get("business_hours_only", False)
            
            # Check if we're in business hours (if required)
            if business_hours_only:
                current_hour = datetime.now(timezone.utc).hour
                if not (8 <= current_hour <= 18):  # Simple business hours check
                    return False
            
            # Check pattern frequency (simplified)
            error_fingerprint = error_data.get("fingerprint")
            if error_fingerprint:
                # In real implementation, this would check pattern frequency from cache
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking pattern conditions: {str(e)}")
            return False
    
    async def _create_escalation_instance(
        self,
        error_id: str,
        rule: EscalationRule,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Create a new escalation instance"""
        try:
            # Find applicable policy
            policy = await self._find_escalation_policy(error_data, context)
            
            if not policy:
                self.logger.warning(f"No escalation policy found for error {error_id}")
                return ""
            
            # Create escalation instance
            escalation = EscalationInstance(
                escalation_id=str(uuid.uuid4()),
                error_id=error_id,
                policy_id=policy.policy_id,
                current_level=rule.target_level,
                severity=EscalationSeverity(error_data.get("severity", "medium")),
                trigger=rule.trigger,
                status=EscalationStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                escalated_at=None,
                acknowledged_at=None,
                resolved_at=None,
                assignee=None,
                escalation_path=[],
                context=context or {},
                notifications_sent=[],
                metadata={
                    "rule_id": rule.rule_id,
                    "policy_id": policy.policy_id,
                    "initial_level": rule.target_level.value
                }
            )
            
            # Store escalation
            self.escalation_instances[escalation.escalation_id] = escalation
            
            # Cache escalation
            await self.cache.set(
                f"escalation:{escalation.escalation_id}",
                escalation.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit escalation created event
            await self.event_bus.emit(
                "escalation.created",
                {
                    "escalation_id": escalation.escalation_id,
                    "error_id": error_id,
                    "level": rule.target_level,
                    "severity": escalation.severity,
                    "trigger": rule.trigger
                }
            )
            
            self.logger.info(f"Escalation instance created: {escalation.escalation_id} for error {error_id}")
            
            return escalation.escalation_id
            
        except Exception as e:
            self.logger.error(f"Error creating escalation instance: {str(e)}")
            return ""
    
    async def _find_escalation_policy(
        self,
        error_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[EscalationPolicy]:
        """Find applicable escalation policy"""
        try:
            error_type = error_data.get("error_type", "unknown")
            service_name = context.get("service_name", "") if context else ""
            severity = error_data.get("severity", "medium")
            
            matching_policies = []
            
            for policy in self.escalation_policies.values():
                # Check service scope
                service_match = False
                for scope in policy.service_scope:
                    if scope == "*" or scope in service_name:
                        service_match = True
                        break
                
                if not service_match:
                    continue
                
                # Check error types
                error_type_match = False
                for et in policy.error_types:
                    if et == "*" or et == error_type:
                        error_type_match = True
                        break
                
                if error_type_match:
                    matching_policies.append(policy)
            
            if not matching_policies:
                return None
            
            # Return first matching policy (could implement priority-based selection)
            return matching_policies[0]
            
        except Exception as e:
            self.logger.error(f"Error finding escalation policy: {str(e)}")
            return None
    
    async def _start_escalation(self, escalation_id: str):
        """Start the escalation process"""
        try:
            if escalation_id not in self.escalation_instances:
                return
            
            escalation = self.escalation_instances[escalation_id]
            escalation.status = EscalationStatus.ACTIVE
            escalation.escalated_at = datetime.now(timezone.utc)
            
            # Find escalation targets for current level
            targets = await self._find_escalation_targets(escalation.current_level)
            
            if targets:
                # Send notifications to targets
                for target in targets:
                    await self._send_escalation_notification(escalation, target)
                
                # Add to escalation path
                escalation.escalation_path.append({
                    "level": escalation.current_level.value,
                    "targets": [t.target_id for t in targets],
                    "escalated_at": escalation.escalated_at.isoformat(),
                    "status": "notified"
                })
                
                # Start escalation monitoring task
                task = asyncio.create_task(self._monitor_escalation(escalation_id))
                self.active_escalations[escalation_id] = task
            
            # Emit escalation started event
            await self.event_bus.emit(
                "escalation.started",
                {
                    "escalation_id": escalation_id,
                    "level": escalation.current_level,
                    "targets_notified": len(targets) if targets else 0
                }
            )
            
            self.logger.info(f"Escalation started: {escalation_id} at level {escalation.current_level}")
            
        except Exception as e:
            self.logger.error(f"Error starting escalation: {str(e)}")
    
    async def _find_escalation_targets(self, level: EscalationLevel) -> List[EscalationTarget]:
        """Find targets for the given escalation level"""
        try:
            targets = []
            
            for target in self.escalation_targets.values():
                if target.level == level:
                    # Check availability
                    if await self._is_target_available(target):
                        targets.append(target)
            
            return targets
            
        except Exception as e:
            self.logger.error(f"Error finding escalation targets: {str(e)}")
            return []
    
    async def _is_target_available(self, target: EscalationTarget) -> bool:
        """Check if escalation target is available"""
        try:
            schedule = target.availability_schedule
            
            if schedule.get("24x7", False):
                return True
            
            # Check business hours
            current_time = datetime.now(timezone.utc)
            current_hour = current_time.hour
            
            business_hours = schedule.get("business_hours", {})
            if business_hours:
                start_hour = int(business_hours.get("start", "08:00").split(":")[0])
                end_hour = int(business_hours.get("end", "18:00").split(":")[0])
                
                if start_hour <= current_hour <= end_hour:
                    return True
            
            # Check emergency contact availability
            if schedule.get("emergency_contact", False):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking target availability: {str(e)}")
            return True  # Default to available
    
    async def _send_escalation_notification(
        self,
        escalation: EscalationInstance,
        target: EscalationTarget
    ):
        """Send escalation notification to target"""
        try:
            # Get policy for notification channels
            policy = self.escalation_policies.get(escalation.policy_id)
            if not policy:
                return
            
            notification_data = {
                "escalation_id": escalation.escalation_id,
                "error_id": escalation.error_id,
                "severity": escalation.severity,
                "level": escalation.current_level,
                "trigger": escalation.trigger,
                "target_name": target.name,
                "context": escalation.context,
                "escalated_at": escalation.escalated_at.isoformat()
            }
            
            # Send notifications via configured channels
            for contact_method in target.contact_methods:
                channel = contact_method.get("channel")
                
                if channel in policy.notification_channels:
                    try:
                        await self.notification_service.send_notification(
                            type="escalation_notification",
                            channel=channel,
                            data=notification_data,
                            contact_info=contact_method
                        )
                        
                        # Record notification sent
                        escalation.notifications_sent.append({
                            "target_id": target.target_id,
                            "channel": channel,
                            "sent_at": datetime.now(timezone.utc).isoformat(),
                            "contact_info": contact_method
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error sending notification via {channel}: {str(e)}")
            
            self.logger.info(f"Escalation notification sent to {target.name} for escalation {escalation.escalation_id}")
            
        except Exception as e:
            self.logger.error(f"Error sending escalation notification: {str(e)}")
    
    async def acknowledge_escalation(
        self,
        escalation_id: str,
        acknowledged_by: str,
        notes: str = None
    ) -> bool:
        """Acknowledge an escalation"""
        try:
            if escalation_id not in self.escalation_instances:
                return False
            
            escalation = self.escalation_instances[escalation_id]
            escalation.status = EscalationStatus.ACKNOWLEDGED
            escalation.acknowledged_at = datetime.now(timezone.utc)
            escalation.assignee = acknowledged_by
            escalation.metadata = escalation.metadata or {}
            escalation.metadata["acknowledgment_notes"] = notes
            
            # Update cache
            await self.cache.set(
                f"escalation:{escalation_id}",
                escalation.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Cancel auto-escalation monitoring
            if escalation_id in self.active_escalations:
                task = self.active_escalations[escalation_id]
                task.cancel()
                del self.active_escalations[escalation_id]
            
            # Emit acknowledgment event
            await self.event_bus.emit(
                "escalation.acknowledged",
                {
                    "escalation_id": escalation_id,
                    "acknowledged_by": acknowledged_by,
                    "notes": notes
                }
            )
            
            self.logger.info(f"Escalation acknowledged: {escalation_id} by {acknowledged_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error acknowledging escalation: {str(e)}")
            return False
    
    async def resolve_escalation(
        self,
        escalation_id: str,
        resolved_by: str,
        resolution_notes: str
    ) -> bool:
        """Resolve an escalation"""
        try:
            if escalation_id not in self.escalation_instances:
                return False
            
            escalation = self.escalation_instances[escalation_id]
            escalation.status = EscalationStatus.RESOLVED
            escalation.resolved_at = datetime.now(timezone.utc)
            escalation.metadata = escalation.metadata or {}
            escalation.metadata["resolved_by"] = resolved_by
            escalation.metadata["resolution_notes"] = resolution_notes
            
            # Update cache
            await self.cache.set(
                f"escalation:{escalation_id}",
                escalation.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Cancel monitoring task
            if escalation_id in self.active_escalations:
                task = self.active_escalations[escalation_id]
                task.cancel()
                del self.active_escalations[escalation_id]
            
            # Emit resolution event
            await self.event_bus.emit(
                "escalation.resolved",
                {
                    "escalation_id": escalation_id,
                    "resolved_by": resolved_by,
                    "resolution_notes": resolution_notes
                }
            )
            
            self.logger.info(f"Escalation resolved: {escalation_id} by {resolved_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving escalation: {str(e)}")
            return False
    
    async def escalate_further(self, escalation_id: str, reason: str = "timeout") -> bool:
        """Escalate to the next level"""
        try:
            if escalation_id not in self.escalation_instances:
                return False
            
            escalation = self.escalation_instances[escalation_id]
            policy = self.escalation_policies.get(escalation.policy_id)
            
            if not policy:
                return False
            
            # Find next level
            current_level_index = None
            for i, level_config in enumerate(policy.escalation_levels):
                if level_config["level"] == escalation.current_level.value:
                    current_level_index = i
                    break
            
            if current_level_index is None or current_level_index >= len(policy.escalation_levels) - 1:
                # Already at highest level
                escalation.status = EscalationStatus.ESCALATED_FURTHER
                escalation.metadata = escalation.metadata or {}
                escalation.metadata["escalation_complete"] = True
                escalation.metadata["reason"] = "maximum_level_reached"
                return False
            
            # Move to next level
            next_level_config = policy.escalation_levels[current_level_index + 1]
            next_level = EscalationLevel(next_level_config["level"])
            
            escalation.current_level = next_level
            escalation.status = EscalationStatus.ACTIVE
            
            # Add to escalation path
            escalation.escalation_path.append({
                "level": next_level.value,
                "escalated_from": policy.escalation_levels[current_level_index]["level"],
                "escalated_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "status": "escalated"
            })
            
            # Find targets for new level and notify
            targets = await self._find_escalation_targets(next_level)
            for target in targets:
                await self._send_escalation_notification(escalation, target)
            
            # Restart monitoring
            if escalation_id in self.active_escalations:
                self.active_escalations[escalation_id].cancel()
            
            task = asyncio.create_task(self._monitor_escalation(escalation_id))
            self.active_escalations[escalation_id] = task
            
            # Emit further escalation event
            await self.event_bus.emit(
                "escalation.escalated_further",
                {
                    "escalation_id": escalation_id,
                    "previous_level": policy.escalation_levels[current_level_index]["level"],
                    "new_level": next_level.value,
                    "reason": reason
                }
            )
            
            self.logger.warning(f"Escalation escalated further: {escalation_id} to level {next_level}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error escalating further: {str(e)}")
            return False
    
    async def _monitor_escalation(self, escalation_id: str):
        """Monitor escalation for timeout and auto-escalation"""
        try:
            escalation = self.escalation_instances.get(escalation_id)
            if not escalation:
                return
            
            policy = self.escalation_policies.get(escalation.policy_id)
            if not policy:
                return
            
            # Find timeout for current level
            timeout_minutes = self.auto_escalation_interval_minutes
            for level_config in policy.escalation_levels:
                if level_config["level"] == escalation.current_level.value:
                    timeout_minutes = level_config.get("timeout_minutes", timeout_minutes)
                    break
            
            # Wait for timeout
            await asyncio.sleep(timeout_minutes * 60)
            
            # Check if escalation is still active
            current_escalation = self.escalation_instances.get(escalation_id)
            if not current_escalation or current_escalation.status != EscalationStatus.ACTIVE:
                return
            
            # Auto-escalate if not acknowledged
            if not current_escalation.acknowledged_at:
                await self.escalate_further(escalation_id, "auto_escalation_timeout")
            
        except asyncio.CancelledError:
            # Task was cancelled (escalation was acknowledged/resolved)
            pass
        except Exception as e:
            self.logger.error(f"Error monitoring escalation {escalation_id}: {str(e)}")
    
    async def get_escalation_status(self, escalation_id: str) -> Dict[str, Any]:
        """Get status of an escalation"""
        try:
            if escalation_id not in self.escalation_instances:
                return {"status": "not_found"}
            
            escalation = self.escalation_instances[escalation_id]
            
            # Calculate duration
            duration_minutes = 0
            if escalation.escalated_at:
                end_time = escalation.resolved_at or datetime.now(timezone.utc)
                duration_minutes = (end_time - escalation.escalated_at).total_seconds() / 60
            
            # Check if SLA is at risk
            sla_at_risk = False
            if escalation.status == EscalationStatus.ACTIVE and escalation.escalated_at:
                time_since_escalation = (datetime.now(timezone.utc) - escalation.escalated_at).total_seconds() / 60
                sla_at_risk = time_since_escalation > self.sla_warning_threshold_minutes
            
            return {
                "escalation_id": escalation_id,
                "status": escalation.status,
                "current_level": escalation.current_level,
                "severity": escalation.severity,
                "trigger": escalation.trigger,
                "assignee": escalation.assignee,
                "duration_minutes": duration_minutes,
                "sla_at_risk": sla_at_risk,
                "notifications_sent": len(escalation.notifications_sent),
                "escalation_path": escalation.escalation_path,
                "created_at": escalation.created_at.isoformat(),
                "acknowledged_at": escalation.acknowledged_at.isoformat() if escalation.acknowledged_at else None,
                "resolved_at": escalation.resolved_at.isoformat() if escalation.resolved_at else None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting escalation status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_escalation_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get escalation summary statistics"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            recent_escalations = [
                e for e in self.escalation_instances.values()
                if e.created_at >= cutoff_time
            ]
            
            # Calculate statistics
            total_escalations = len(recent_escalations)
            active_escalations = len([e for e in recent_escalations if e.status == EscalationStatus.ACTIVE])
            resolved_escalations = len([e for e in recent_escalations if e.status == EscalationStatus.RESOLVED])
            
            # Resolution rate
            resolution_rate = (resolved_escalations / total_escalations) * 100 if total_escalations > 0 else 0
            
            # Level distribution
            level_distribution = {}
            for level in EscalationLevel:
                level_distribution[level.value] = len([e for e in recent_escalations if e.current_level == level])
            
            # Trigger distribution
            trigger_distribution = {}
            for trigger in EscalationTrigger:
                trigger_distribution[trigger.value] = len([e for e in recent_escalations if e.trigger == trigger])
            
            # Average resolution time
            resolved_with_time = [e for e in recent_escalations if e.status == EscalationStatus.RESOLVED and e.escalated_at and e.resolved_at]
            avg_resolution_minutes = 0
            if resolved_with_time:
                resolution_times = [(e.resolved_at - e.escalated_at).total_seconds() / 60 for e in resolved_with_time]
                avg_resolution_minutes = sum(resolution_times) / len(resolution_times)
            
            return {
                "time_range_hours": time_range_hours,
                "total_escalations": total_escalations,
                "active_escalations": active_escalations,
                "resolved_escalations": resolved_escalations,
                "resolution_rate": resolution_rate,
                "level_distribution": level_distribution,
                "trigger_distribution": trigger_distribution,
                "avg_resolution_minutes": avg_resolution_minutes,
                "policies_configured": len(self.escalation_policies),
                "rules_configured": len(self.escalation_rules),
                "targets_configured": len(self.escalation_targets)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting escalation summary: {str(e)}")
            return {}
    
    async def _escalation_monitor(self):
        """Background escalation monitoring task"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                # Check for escalations that need attention
                current_time = datetime.now(timezone.utc)
                
                for escalation in self.escalation_instances.values():
                    if escalation.status == EscalationStatus.ACTIVE:
                        # Check for SLA breach
                        if escalation.escalated_at:
                            time_since_escalation = (current_time - escalation.escalated_at).total_seconds() / 60
                            
                            if time_since_escalation > self.sla_warning_threshold_minutes and not escalation.sla_breach_time:
                                escalation.sla_breach_time = current_time
                                
                                await self.event_bus.emit(
                                    "escalation.sla_breach",
                                    {
                                        "escalation_id": escalation.escalation_id,
                                        "time_since_escalation": time_since_escalation
                                    }
                                )
                
            except Exception as e:
                self.logger.error(f"Error in escalation monitor: {str(e)}")
    
    async def _sla_monitor(self):
        """Background SLA monitoring task"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Monitor SLA compliance for active escalations
                # This would typically check against defined SLAs
                
            except Exception as e:
                self.logger.error(f"Error in SLA monitor: {str(e)}")
    
    async def _cleanup_old_escalations(self):
        """Cleanup old escalation records"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.escalation_retention_days)
                
                # Remove old resolved escalations
                old_escalations = [
                    e_id for e_id, e in self.escalation_instances.items()
                    if e.status in [EscalationStatus.RESOLVED, EscalationStatus.CLOSED] and e.resolved_at and e.resolved_at < cutoff_time
                ]
                
                for escalation_id in old_escalations:
                    del self.escalation_instances[escalation_id]
                
                self.logger.info(f"Cleaned up {len(old_escalations)} old escalations")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "error.pattern_escalation",
                self._handle_pattern_escalation
            )
            
            await self.event_bus.subscribe(
                "error.escalation_required",
                self._handle_escalation_required
            )
            
            await self.event_bus.subscribe(
                "recovery.execution_failed",
                self._handle_recovery_failure
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_pattern_escalation(self, event_data: Dict[str, Any]):
        """Handle pattern escalation event"""
        try:
            pattern_id = event_data.get("pattern_id")
            frequency = event_data.get("frequency", 0)
            
            if pattern_id and frequency >= 5:
                # Create escalation for pattern
                await self.evaluate_escalation(
                    error_id=f"pattern_{pattern_id}",
                    error_data={
                        "error_type": "pattern_detected",
                        "severity": "high",
                        "pattern_id": pattern_id,
                        "frequency": frequency
                    },
                    context={"trigger": "pattern_detection"}
                )
            
        except Exception as e:
            self.logger.error(f"Error handling pattern escalation: {str(e)}")
    
    async def _handle_escalation_required(self, event_data: Dict[str, Any]):
        """Handle escalation required event"""
        try:
            error_id = event_data.get("error_id")
            severity = event_data.get("severity", "high")
            
            if error_id:
                await self.evaluate_escalation(
                    error_id=error_id,
                    error_data={
                        "error_type": "manual_escalation",
                        "severity": severity
                    },
                    context=event_data
                )
            
        except Exception as e:
            self.logger.error(f"Error handling escalation required: {str(e)}")
    
    async def _handle_recovery_failure(self, event_data: Dict[str, Any]):
        """Handle recovery failure event"""
        try:
            session_id = event_data.get("session_id")
            error_id = event_data.get("error_id")
            
            if error_id:
                await self.evaluate_escalation(
                    error_id=error_id,
                    error_data={
                        "error_type": "recovery_failure",
                        "severity": "high",
                        "recovery_session_id": session_id
                    },
                    context={"trigger": "recovery_failure", "recovery_attempts": 3}
                )
            
        except Exception as e:
            self.logger.error(f"Error handling recovery failure: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            active_escalations_count = len([e for e in self.escalation_instances.values() if e.status == EscalationStatus.ACTIVE])
            critical_escalations = len([e for e in self.escalation_instances.values() if e.severity == EscalationSeverity.CRITICAL])
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "escalation_manager",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_escalations": len(self.escalation_instances),
                    "active_escalations": active_escalations_count,
                    "critical_escalations": critical_escalations,
                    "policies_configured": len(self.escalation_policies),
                    "rules_configured": len(self.escalation_rules),
                    "targets_configured": len(self.escalation_targets),
                    "monitoring_tasks": len(self.active_escalations)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "escalation_manager",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Escalation manager service cleanup initiated")
        
        try:
            # Cancel all monitoring tasks
            for task in self.active_escalations.values():
                task.cancel()
            
            # Clear all state
            self.escalation_instances.clear()
            self.active_escalations.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Escalation manager service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_escalation_manager() -> EscalationManager:
    """Create escalation manager service"""
    return EscalationManager()