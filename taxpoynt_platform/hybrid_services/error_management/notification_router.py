"""
Hybrid Service: Notification Router
Routes error notifications to appropriate parties across the platform
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import re

from core_platform.database import get_db_session
from core_platform.models.notifications import NotificationRule, NotificationTarget, NotificationDelivery
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TEAMS = "teams"
    WEBHOOK = "webhook"
    PUSH_NOTIFICATION = "push_notification"
    PAGER_DUTY = "pager_duty"
    PHONE_CALL = "phone_call"
    DASHBOARD = "dashboard"
    MOBILE_APP = "mobile_app"


class NotificationPriority(str, Enum):
    """Notification priority levels"""
    IMMEDIATE = "immediate"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    BULK = "bulk"


class NotificationStatus(str, Enum):
    """Status of notification delivery"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    DELIVERED = "delivered"
    FAILED = "failed"
    REJECTED = "rejected"
    BOUNCED = "bounced"
    READ = "read"
    ACKNOWLEDGED = "acknowledged"


class RoutingStrategy(str, Enum):
    """Strategies for routing notifications"""
    ROLE_BASED = "role_based"
    SERVICE_BASED = "service_based"
    SEVERITY_BASED = "severity_based"
    TENANT_BASED = "tenant_based"
    USER_PREFERENCE = "user_preference"
    ESCALATION_BASED = "escalation_based"
    GEOGRAPHIC = "geographic"
    TIME_BASED = "time_based"


class DeliveryMode(str, Enum):
    """Delivery modes for notifications"""
    IMMEDIATE = "immediate"
    BATCHED = "batched"
    SCHEDULED = "scheduled"
    RATE_LIMITED = "rate_limited"
    DIGEST = "digest"


@dataclass
class NotificationTarget:
    """Target for notification delivery"""
    target_id: str
    name: str
    type: str  # user, group, service, external
    contact_methods: List[Dict[str, Any]]
    preferences: Dict[str, Any]
    availability_schedule: Dict[str, Any]
    rate_limits: Dict[str, Any]
    tags: List[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationRule:
    """Rule for notification routing"""
    rule_id: str
    name: str
    description: str
    conditions: Dict[str, Any]
    routing_strategy: RoutingStrategy
    target_selectors: List[Dict[str, Any]]
    channel_preferences: List[NotificationChannel]
    delivery_mode: DeliveryMode
    priority: NotificationPriority
    rate_limit: Optional[Dict[str, Any]]
    template_id: Optional[str]
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationRequest:
    """Request to send a notification"""
    request_id: str
    source_service: str
    notification_type: str
    priority: NotificationPriority
    data: Dict[str, Any]
    context: Dict[str, Any]
    delivery_mode: DeliveryMode
    preferred_channels: List[NotificationChannel]
    target_filters: Dict[str, Any]
    created_at: datetime
    expires_at: Optional[datetime] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationDelivery:
    """Record of notification delivery attempt"""
    delivery_id: str
    request_id: str
    target_id: str
    channel: NotificationChannel
    status: NotificationStatus
    message_content: Dict[str, Any]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    read_at: Optional[datetime]
    acknowledged_at: Optional[datetime]
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotificationTemplate:
    """Template for notification messages"""
    template_id: str
    name: str
    notification_type: str
    channel: NotificationChannel
    subject_template: str
    body_template: str
    variables: List[str]
    localization: Dict[str, Dict[str, str]]  # language -> {subject, body}
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NotificationRouter:
    """
    Notification Router service
    Routes error notifications to appropriate parties across the platform
    """
    
    def __init__(self):
        """Initialize notification router service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.notification_targets: Dict[str, NotificationTarget] = {}
        self.notification_rules: Dict[str, NotificationRule] = {}
        self.notification_templates: Dict[str, NotificationTemplate] = {}
        self.pending_requests: Dict[str, NotificationRequest] = {}
        self.delivery_records: Dict[str, NotificationDelivery] = {}
        self.rate_limit_counters: Dict[str, Dict[str, int]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 86400  # 24 hours
        self.default_retry_limit = 3
        self.rate_limit_window_minutes = 60
        self.batch_size = 50
        self.batch_interval_seconds = 30
        self.delivery_timeout_seconds = 300
        
        # Initialize default components
        self._initialize_default_targets()
        self._initialize_default_rules()
        self._initialize_default_templates()
    
    def _initialize_default_targets(self):
        """Initialize default notification targets"""
        default_targets = [
            # Development team
            NotificationTarget(
                target_id="dev_team_lead",
                name="Development Team Lead",
                type="user",
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "dev-lead@taxpoynt.com"},
                    {"channel": NotificationChannel.SLACK, "user_id": "@dev-lead", "channel": "#dev-alerts"},
                    {"channel": NotificationChannel.SMS, "number": "+1234567890"}
                ],
                preferences={
                    "immediate_notifications": [NotificationChannel.SLACK, NotificationChannel.SMS],
                    "digest_notifications": [NotificationChannel.EMAIL],
                    "quiet_hours": {"start": "22:00", "end": "08:00"}
                },
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "18:00"},
                    "on_call_rotation": True,
                    "timezone": "UTC"
                },
                rate_limits={
                    NotificationChannel.SMS.value: {"max_per_hour": 10},
                    NotificationChannel.EMAIL.value: {"max_per_hour": 50}
                },
                tags=["development", "technical", "lead"]
            ),
            
            # Operations team
            NotificationTarget(
                target_id="ops_team",
                name="Operations Team",
                type="group",
                contact_methods=[
                    {"channel": NotificationChannel.PAGER_DUTY, "service_key": "ops-service-key"},
                    {"channel": NotificationChannel.SLACK, "channel": "#ops-alerts"},
                    {"channel": NotificationChannel.EMAIL, "address": "ops-team@taxpoynt.com"}
                ],
                preferences={
                    "immediate_notifications": [NotificationChannel.PAGER_DUTY, NotificationChannel.SLACK],
                    "escalation_chain": True
                },
                availability_schedule={"24x7": True},
                rate_limits={
                    NotificationChannel.PAGER_DUTY.value: {"max_per_hour": 20}
                },
                tags=["operations", "infrastructure", "monitoring"]
            ),
            
            # Business team
            NotificationTarget(
                target_id="business_stakeholders",
                name="Business Stakeholders",
                type="group",
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "business-alerts@taxpoynt.com"},
                    {"channel": NotificationChannel.TEAMS, "team": "business-operations"},
                    {"channel": NotificationChannel.DASHBOARD, "dashboard_id": "business-dashboard"}
                ],
                preferences={
                    "business_hours_only": True,
                    "digest_notifications": [NotificationChannel.EMAIL],
                    "priority_threshold": NotificationPriority.HIGH.value
                },
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "17:00"},
                    "weekends": False
                },
                rate_limits={
                    NotificationChannel.EMAIL.value: {"max_per_day": 20}
                },
                tags=["business", "stakeholder", "management"]
            ),
            
            # Customer success
            NotificationTarget(
                target_id="customer_success",
                name="Customer Success Team",
                type="group",
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "customer-success@taxpoynt.com"},
                    {"channel": NotificationChannel.TEAMS, "team": "customer-success"},
                    {"channel": NotificationChannel.WEBHOOK, "endpoint": "/api/cs-notifications"}
                ],
                preferences={
                    "customer_impact_only": True,
                    "priority_threshold": NotificationPriority.HIGH.value
                },
                availability_schedule={
                    "business_hours": {"start": "08:00", "end": "18:00"}
                },
                rate_limits={},
                tags=["customer", "support", "external_facing"]
            ),
            
            # Security team
            NotificationTarget(
                target_id="security_team",
                name="Security Team",
                type="group",
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": "security@taxpoynt.com"},
                    {"channel": NotificationChannel.SLACK, "channel": "#security-alerts"},
                    {"channel": NotificationChannel.PAGER_DUTY, "service_key": "security-service-key"}
                ],
                preferences={
                    "security_events_only": True,
                    "immediate_notifications": [NotificationChannel.PAGER_DUTY, NotificationChannel.SLACK]
                },
                availability_schedule={"24x7": True},
                rate_limits={},
                tags=["security", "compliance", "incident_response"]
            ),
            
            # External webhook
            NotificationTarget(
                target_id="external_monitoring",
                name="External Monitoring System",
                type="external",
                contact_methods=[
                    {"channel": NotificationChannel.WEBHOOK, "endpoint": "https://monitoring.taxpoynt.com/api/alerts"},
                    {"channel": NotificationChannel.WEBHOOK, "endpoint": "https://status.taxpoynt.com/api/incidents"}
                ],
                preferences={
                    "all_errors": True,
                    "structured_format": True
                },
                availability_schedule={"24x7": True},
                rate_limits={
                    NotificationChannel.WEBHOOK.value: {"max_per_minute": 100}
                },
                tags=["external", "monitoring", "automation"]
            )
        ]
        
        for target in default_targets:
            self.notification_targets[target.target_id] = target
    
    def _initialize_default_rules(self):
        """Initialize default notification routing rules"""
        default_rules = [
            # Critical error rule
            NotificationRule(
                rule_id="critical_error_rule",
                name="Critical Error Notifications",
                description="Route critical errors to immediate response teams",
                conditions={
                    "severity": ["critical"],
                    "error_types": ["system", "database", "integration"]
                },
                routing_strategy=RoutingStrategy.SEVERITY_BASED,
                target_selectors=[
                    {"tags": ["development", "operations"], "type": "any"},
                    {"target_ids": ["ops_team", "dev_team_lead"]}
                ],
                channel_preferences=[
                    NotificationChannel.PAGER_DUTY,
                    NotificationChannel.SLACK,
                    NotificationChannel.SMS
                ],
                delivery_mode=DeliveryMode.IMMEDIATE,
                priority=NotificationPriority.IMMEDIATE,
                rate_limit=None,  # No rate limiting for critical errors
                template_id="critical_error_template"
            ),
            
            # Business impact rule
            NotificationRule(
                rule_id="business_impact_rule",
                name="Business Impact Notifications",
                description="Route business-impacting errors to stakeholders",
                conditions={
                    "business_impact": ["high", "critical"],
                    "services": ["invoice_*", "payment_*", "firs_*"]
                },
                routing_strategy=RoutingStrategy.SERVICE_BASED,
                target_selectors=[
                    {"tags": ["business", "stakeholder"]},
                    {"target_ids": ["business_stakeholders", "customer_success"]}
                ],
                channel_preferences=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.TEAMS,
                    NotificationChannel.DASHBOARD
                ],
                delivery_mode=DeliveryMode.IMMEDIATE,
                priority=NotificationPriority.HIGH,
                rate_limit={"max_per_hour": 10},
                template_id="business_impact_template"
            ),
            
            # Security event rule
            NotificationRule(
                rule_id="security_event_rule",
                name="Security Event Notifications",
                description="Route security-related errors to security team",
                conditions={
                    "error_types": ["authentication", "authorization", "security"],
                    "severity": ["medium", "high", "critical"]
                },
                routing_strategy=RoutingStrategy.ROLE_BASED,
                target_selectors=[
                    {"tags": ["security"]},
                    {"target_ids": ["security_team"]}
                ],
                channel_preferences=[
                    NotificationChannel.PAGER_DUTY,
                    NotificationChannel.SLACK,
                    NotificationChannel.EMAIL
                ],
                delivery_mode=DeliveryMode.IMMEDIATE,
                priority=NotificationPriority.HIGH,
                rate_limit=None,
                template_id="security_event_template"
            ),
            
            # Integration error rule
            NotificationRule(
                rule_id="integration_error_rule",
                name="Integration Error Notifications",
                description="Route integration errors to appropriate teams",
                conditions={
                    "error_types": ["integration", "external_api", "network"],
                    "severity": ["medium", "high"]
                },
                routing_strategy=RoutingStrategy.SERVICE_BASED,
                target_selectors=[
                    {"tags": ["development", "operations"]},
                    {"services": ["integration_*"]}
                ],
                channel_preferences=[
                    NotificationChannel.SLACK,
                    NotificationChannel.EMAIL
                ],
                delivery_mode=DeliveryMode.BATCHED,
                priority=NotificationPriority.MEDIUM,
                rate_limit={"max_per_hour": 20},
                template_id="integration_error_template"
            ),
            
            # General error rule
            NotificationRule(
                rule_id="general_error_rule",
                name="General Error Notifications",
                description="Route general errors for monitoring",
                conditions={
                    "severity": ["low", "medium"],
                    "exclude_types": ["validation"]
                },
                routing_strategy=RoutingStrategy.ROLE_BASED,
                target_selectors=[
                    {"target_ids": ["external_monitoring"]},
                    {"tags": ["monitoring"]}
                ],
                channel_preferences=[
                    NotificationChannel.WEBHOOK,
                    NotificationChannel.DASHBOARD
                ],
                delivery_mode=DeliveryMode.DIGEST,
                priority=NotificationPriority.LOW,
                rate_limit={"max_per_hour": 100},
                template_id="general_error_template"
            ),
            
            # User-specific rule
            NotificationRule(
                rule_id="user_specific_rule",
                name="User-Specific Notifications",
                description="Route errors to users based on preferences",
                conditions={
                    "has_user_context": True
                },
                routing_strategy=RoutingStrategy.USER_PREFERENCE,
                target_selectors=[
                    {"type": "user_context"}
                ],
                channel_preferences=[
                    NotificationChannel.EMAIL,
                    NotificationChannel.PUSH_NOTIFICATION,
                    NotificationChannel.MOBILE_APP
                ],
                delivery_mode=DeliveryMode.IMMEDIATE,
                priority=NotificationPriority.MEDIUM,
                rate_limit={"max_per_user_per_hour": 5},
                template_id="user_notification_template"
            )
        ]
        
        for rule in default_rules:
            self.notification_rules[rule.rule_id] = rule
    
    def _initialize_default_templates(self):
        """Initialize default notification templates"""
        default_templates = [
            # Critical error template
            NotificationTemplate(
                template_id="critical_error_template",
                name="Critical Error Notification",
                notification_type="critical_error",
                channel=NotificationChannel.EMAIL,
                subject_template="🚨 CRITICAL: {error_type} in {service_name}",
                body_template="""
Critical Error Detected:

Service: {service_name}
Error Type: {error_type}
Severity: {severity}
Time: {occurred_at}
Message: {error_message}

Context:
- User ID: {user_id}
- Operation: {operation_name}
- Trace ID: {trace_id}

Immediate action required!

Error ID: {error_id}
Escalation ID: {escalation_id}
                """,
                variables=["error_type", "service_name", "severity", "occurred_at", "error_message", "user_id", "operation_name", "trace_id", "error_id", "escalation_id"],
                localization={
                    "en": {
                        "subject": "🚨 CRITICAL: {error_type} in {service_name}",
                        "body": "Critical Error Detected..."
                    }
                }
            ),
            
            # Business impact template
            NotificationTemplate(
                template_id="business_impact_template",
                name="Business Impact Notification",
                notification_type="business_impact",
                channel=NotificationChannel.EMAIL,
                subject_template="⚠️  Business Impact: {error_type} affecting {service_name}",
                body_template="""
Business Impact Alert:

Service: {service_name}
Error Type: {error_type}
Business Impact: {business_impact}
Affected Users: {affected_users}
Time: {occurred_at}

Description: {error_message}

Impact Assessment:
- Revenue Impact: {revenue_impact}
- Customer Impact: {customer_impact}
- SLA Impact: {sla_impact}

Recovery Actions:
{recovery_actions}

Error ID: {error_id}
                """,
                variables=["error_type", "service_name", "business_impact", "affected_users", "occurred_at", "error_message", "revenue_impact", "customer_impact", "sla_impact", "recovery_actions", "error_id"],
                localization={}
            ),
            
            # Security event template
            NotificationTemplate(
                template_id="security_event_template",
                name="Security Event Notification",
                notification_type="security_event",
                channel=NotificationChannel.EMAIL,
                subject_template="🔒 Security Alert: {error_type}",
                body_template="""
Security Event Detected:

Event Type: {error_type}
Severity: {severity}
Source IP: {source_ip}
User ID: {user_id}
Time: {occurred_at}

Details: {error_message}

Security Context:
- Authentication Status: {auth_status}
- Authorization Level: {auth_level}
- Risk Level: {risk_level}

Recommended Actions:
{recommended_actions}

Event ID: {error_id}
                """,
                variables=["error_type", "severity", "source_ip", "user_id", "occurred_at", "error_message", "auth_status", "auth_level", "risk_level", "recommended_actions", "error_id"],
                localization={}
            ),
            
            # Integration error template
            NotificationTemplate(
                template_id="integration_error_template",
                name="Integration Error Notification",
                notification_type="integration_error",
                channel=NotificationChannel.SLACK,
                subject_template="Integration Error: {external_service}",
                body_template="""
🔌 Integration Error

External Service: {external_service}
Error Type: {error_type}
Status Code: {status_code}
Retry Count: {retry_count}
Time: {occurred_at}

Error: {error_message}

Recovery Status: {recovery_status}
Next Retry: {next_retry_time}

Error ID: {error_id}
                """,
                variables=["external_service", "error_type", "status_code", "retry_count", "occurred_at", "error_message", "recovery_status", "next_retry_time", "error_id"],
                localization={}
            ),
            
            # General error template
            NotificationTemplate(
                template_id="general_error_template",
                name="General Error Notification",
                notification_type="general_error",
                channel=NotificationChannel.WEBHOOK,
                subject_template="{error_type} in {service_name}",
                body_template="""
{
  "error_id": "{error_id}",
  "error_type": "{error_type}",
  "service_name": "{service_name}",
  "severity": "{severity}",
  "occurred_at": "{occurred_at}",
  "message": "{error_message}",
  "context": {
    "operation": "{operation_name}",
    "user_id": "{user_id}",
    "trace_id": "{trace_id}"
  },
  "metadata": {
    "source": "taxpoynt_platform",
    "version": "1.0.0"
  }
}
                """,
                variables=["error_id", "error_type", "service_name", "severity", "occurred_at", "error_message", "operation_name", "user_id", "trace_id"],
                localization={}
            ),
            
            # User notification template
            NotificationTemplate(
                template_id="user_notification_template",
                name="User Notification",
                notification_type="user_notification",
                channel=NotificationChannel.EMAIL,
                subject_template="TaxPoynt: Issue with {operation_name}",
                body_template="""
Dear {user_name},

We encountered an issue while processing your {operation_name} request.

Issue: {user_friendly_message}
Time: {occurred_at}
Reference: {error_id}

Our team has been notified and is working to resolve this issue.

We apologize for any inconvenience.

Best regards,
TaxPoynt Support Team
                """,
                variables=["user_name", "operation_name", "user_friendly_message", "occurred_at", "error_id"],
                localization={
                    "en": {
                        "subject": "TaxPoynt: Issue with {operation_name}",
                        "body": "Dear {user_name}..."
                    }
                }
            )
        ]
        
        for template in default_templates:
            self.notification_templates[template.template_id] = template
    
    async def initialize(self):
        """Initialize the notification router service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing notification router service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._notification_processor())
            asyncio.create_task(self._batch_processor())
            asyncio.create_task(self._digest_processor())
            asyncio.create_task(self._cleanup_old_records())
            
            self.is_initialized = True
            self.logger.info("Notification router service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing notification router service: {str(e)}")
            raise
    
    async def route_notification(
        self,
        notification_type: str,
        data: Dict[str, Any],
        context: Dict[str, Any] = None,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        preferred_channels: List[NotificationChannel] = None
    ) -> str:
        """Route a notification based on rules and context"""
        try:
            # Create notification request
            request = NotificationRequest(
                request_id=str(uuid.uuid4()),
                source_service=context.get("service_name", "unknown") if context else "unknown",
                notification_type=notification_type,
                priority=priority,
                data=data,
                context=context or {},
                delivery_mode=DeliveryMode.IMMEDIATE,
                preferred_channels=preferred_channels or [],
                target_filters={},
                created_at=datetime.now(timezone.utc),
                correlation_id=context.get("correlation_id") if context else None
            )
            
            # Store request
            self.pending_requests[request.request_id] = request
            
            # Find applicable routing rules
            applicable_rules = await self._find_applicable_rules(request)
            
            if not applicable_rules:
                self.logger.warning(f"No routing rules found for notification type: {notification_type}")
                return request.request_id
            
            # Process each applicable rule
            for rule in applicable_rules:
                await self._process_notification_rule(request, rule)
            
            # Emit routing event
            await self.event_bus.emit(
                "notification.routed",
                {
                    "request_id": request.request_id,
                    "notification_type": notification_type,
                    "priority": priority,
                    "rules_applied": len(applicable_rules)
                }
            )
            
            self.logger.info(f"Notification routed: {request.request_id} for type {notification_type}")
            
            return request.request_id
            
        except Exception as e:
            self.logger.error(f"Error routing notification: {str(e)}")
            return ""
    
    async def _find_applicable_rules(self, request: NotificationRequest) -> List[NotificationRule]:
        """Find notification rules applicable to the request"""
        try:
            applicable_rules = []
            
            for rule in self.notification_rules.values():
                if not rule.enabled:
                    continue
                
                if await self._check_rule_conditions(rule, request):
                    applicable_rules.append(rule)
            
            # Sort by priority
            priority_order = {
                NotificationPriority.IMMEDIATE: 5,
                NotificationPriority.HIGH: 4,
                NotificationPriority.MEDIUM: 3,
                NotificationPriority.LOW: 2,
                NotificationPriority.BULK: 1
            }
            
            applicable_rules.sort(key=lambda r: priority_order.get(r.priority, 0), reverse=True)
            
            return applicable_rules
            
        except Exception as e:
            self.logger.error(f"Error finding applicable rules: {str(e)}")
            return []
    
    async def _check_rule_conditions(self, rule: NotificationRule, request: NotificationRequest) -> bool:
        """Check if rule conditions match the notification request"""
        try:
            conditions = rule.conditions
            
            # Check severity
            if "severity" in conditions:
                required_severities = conditions["severity"]
                request_severity = request.data.get("severity")
                if request_severity not in required_severities:
                    return False
            
            # Check error types
            if "error_types" in conditions:
                required_types = conditions["error_types"]
                request_error_type = request.data.get("error_type")
                if request_error_type not in required_types:
                    return False
            
            # Check services
            if "services" in conditions:
                required_services = conditions["services"]
                request_service = request.source_service
                
                # Support wildcard matching
                service_match = False
                for service_pattern in required_services:
                    if service_pattern.endswith("*"):
                        if request_service.startswith(service_pattern[:-1]):
                            service_match = True
                            break
                    elif service_pattern == request_service:
                        service_match = True
                        break
                
                if not service_match:
                    return False
            
            # Check business impact
            if "business_impact" in conditions:
                required_impacts = conditions["business_impact"]
                request_impact = request.data.get("business_impact", "low")
                if request_impact not in required_impacts:
                    return False
            
            # Check user context
            if "has_user_context" in conditions:
                required_user_context = conditions["has_user_context"]
                has_user_context = bool(request.context.get("user_id"))
                if has_user_context != required_user_context:
                    return False
            
            # Check exclude types
            if "exclude_types" in conditions:
                excluded_types = conditions["exclude_types"]
                request_error_type = request.data.get("error_type")
                if request_error_type in excluded_types:
                    return False
            
            # Check time-based conditions
            if "business_hours_only" in conditions:
                if conditions["business_hours_only"]:
                    current_hour = datetime.now(timezone.utc).hour
                    if not (8 <= current_hour <= 18):
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking rule conditions: {str(e)}")
            return False
    
    async def _process_notification_rule(self, request: NotificationRequest, rule: NotificationRule):
        """Process a notification request using a specific rule"""
        try:
            # Find targets based on rule selectors
            targets = await self._find_notification_targets(rule, request)
            
            if not targets:
                self.logger.warning(f"No targets found for rule: {rule.rule_id}")
                return
            
            # Apply rate limiting
            if rule.rate_limit:
                targets = await self._apply_rate_limiting(targets, rule, request)
            
            # Create delivery records for each target
            for target in targets:
                await self._create_delivery_records(request, rule, target)
            
            self.logger.debug(f"Processed notification rule {rule.rule_id} for {len(targets)} targets")
            
        except Exception as e:
            self.logger.error(f"Error processing notification rule: {str(e)}")
    
    async def _find_notification_targets(
        self,
        rule: NotificationRule,
        request: NotificationRequest
    ) -> List[NotificationTarget]:
        """Find targets based on rule selectors"""
        try:
            targets = []
            
            for selector in rule.target_selectors:
                # Direct target IDs
                if "target_ids" in selector:
                    for target_id in selector["target_ids"]:
                        if target_id in self.notification_targets:
                            targets.append(self.notification_targets[target_id])
                
                # Tag-based selection
                if "tags" in selector:
                    required_tags = selector["tags"]
                    match_type = selector.get("type", "all")  # all or any
                    
                    for target in self.notification_targets.values():
                        target_tags = target.tags or []
                        
                        if match_type == "all":
                            if all(tag in target_tags for tag in required_tags):
                                targets.append(target)
                        else:  # any
                            if any(tag in target_tags for tag in required_tags):
                                targets.append(target)
                
                # Service-based selection
                if "services" in selector:
                    service_patterns = selector["services"]
                    request_service = request.source_service
                    
                    for pattern in service_patterns:
                        if pattern.endswith("*"):
                            if request_service.startswith(pattern[:-1]):
                                # Find targets for this service pattern
                                service_targets = await self._find_service_targets(pattern)
                                targets.extend(service_targets)
                
                # User context selection
                if "type" in selector and selector["type"] == "user_context":
                    user_id = request.context.get("user_id")
                    if user_id:
                        user_target = await self._find_user_target(user_id)
                        if user_target:
                            targets.append(user_target)
            
            # Remove duplicates
            unique_targets = []
            seen_ids = set()
            for target in targets:
                if target.target_id not in seen_ids:
                    unique_targets.append(target)
                    seen_ids.add(target.target_id)
            
            # Filter by availability
            available_targets = []
            for target in unique_targets:
                if await self._is_target_available(target):
                    available_targets.append(target)
            
            return available_targets
            
        except Exception as e:
            self.logger.error(f"Error finding notification targets: {str(e)}")
            return []
    
    async def _find_service_targets(self, service_pattern: str) -> List[NotificationTarget]:
        """Find targets responsible for specific services"""
        try:
            # This would typically query a service registry or configuration
            # For now, return default targets
            
            if service_pattern.startswith("firs_"):
                return [target for target in self.notification_targets.values() if "integration" in target.tags or []]
            elif service_pattern.startswith("invoice_"):
                return [target for target in self.notification_targets.values() if "business" in target.tags or []]
            else:
                return [target for target in self.notification_targets.values() if "development" in target.tags or []]
                
        except Exception as e:
            self.logger.error(f"Error finding service targets: {str(e)}")
            return []
    
    async def _find_user_target(self, user_id: str) -> Optional[NotificationTarget]:
        """Find notification target for specific user"""
        try:
            # This would typically query user preferences and contact information
            # For now, create a dynamic target
            
            return NotificationTarget(
                target_id=f"user_{user_id}",
                name=f"User {user_id}",
                type="user",
                contact_methods=[
                    {"channel": NotificationChannel.EMAIL, "address": f"{user_id}@taxpoynt.com"},
                    {"channel": NotificationChannel.PUSH_NOTIFICATION, "device_id": f"device_{user_id}"}
                ],
                preferences={
                    "immediate_notifications": [NotificationChannel.PUSH_NOTIFICATION],
                    "digest_notifications": [NotificationChannel.EMAIL]
                },
                availability_schedule={"24x7": True},
                rate_limits={
                    NotificationChannel.PUSH_NOTIFICATION.value: {"max_per_hour": 5}
                },
                tags=["user", "individual"]
            )
            
        except Exception as e:
            self.logger.error(f"Error finding user target: {str(e)}")
            return None
    
    async def _is_target_available(self, target: NotificationTarget) -> bool:
        """Check if target is available for notifications"""
        try:
            if not target.enabled:
                return False
            
            schedule = target.availability_schedule
            
            if schedule.get("24x7", False):
                return True
            
            current_time = datetime.now(timezone.utc)
            current_hour = current_time.hour
            current_weekday = current_time.weekday()  # 0 = Monday, 6 = Sunday
            
            # Check business hours
            business_hours = schedule.get("business_hours", {})
            if business_hours:
                start_hour = int(business_hours.get("start", "08:00").split(":")[0])
                end_hour = int(business_hours.get("end", "18:00").split(":")[0])
                
                if not (start_hour <= current_hour <= end_hour):
                    return False
            
            # Check weekends
            if schedule.get("weekends", True) is False:
                if current_weekday >= 5:  # Saturday or Sunday
                    return False
            
            # Check quiet hours
            preferences = target.preferences
            quiet_hours = preferences.get("quiet_hours", {})
            if quiet_hours:
                quiet_start = int(quiet_hours.get("start", "22:00").split(":")[0])
                quiet_end = int(quiet_hours.get("end", "08:00").split(":")[0])
                
                if quiet_start > quiet_end:  # Crosses midnight
                    if current_hour >= quiet_start or current_hour <= quiet_end:
                        return False
                else:
                    if quiet_start <= current_hour <= quiet_end:
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking target availability: {str(e)}")
            return True  # Default to available
    
    async def _apply_rate_limiting(
        self,
        targets: List[NotificationTarget],
        rule: NotificationRule,
        request: NotificationRequest
    ) -> List[NotificationTarget]:
        """Apply rate limiting to targets"""
        try:
            filtered_targets = []
            current_time = datetime.now(timezone.utc)
            window_key = current_time.strftime("%Y-%m-%d-%H")  # Hourly window
            
            for target in targets:
                # Check rule-level rate limits
                if rule.rate_limit:
                    max_per_hour = rule.rate_limit.get("max_per_hour")
                    if max_per_hour:
                        counter_key = f"rule_{rule.rule_id}_{target.target_id}_{window_key}"
                        current_count = self.rate_limit_counters.get(counter_key, 0)
                        
                        if current_count >= max_per_hour:
                            continue  # Skip this target due to rate limit
                
                # Check target-level rate limits
                target_rate_limits = target.rate_limits
                rate_limit_exceeded = False
                
                for channel in rule.channel_preferences:
                    channel_limits = target_rate_limits.get(channel.value, {})
                    max_per_hour = channel_limits.get("max_per_hour")
                    
                    if max_per_hour:
                        counter_key = f"target_{target.target_id}_{channel.value}_{window_key}"
                        current_count = self.rate_limit_counters.get(counter_key, 0)
                        
                        if current_count >= max_per_hour:
                            rate_limit_exceeded = True
                            break
                
                if not rate_limit_exceeded:
                    filtered_targets.append(target)
            
            return filtered_targets
            
        except Exception as e:
            self.logger.error(f"Error applying rate limiting: {str(e)}")
            return targets
    
    async def _create_delivery_records(
        self,
        request: NotificationRequest,
        rule: NotificationRule,
        target: NotificationTarget
    ):
        """Create delivery records for target notification"""
        try:
            # Determine channels to use
            channels_to_use = await self._select_notification_channels(rule, target, request)
            
            for channel in channels_to_use:
                # Get contact method for channel
                contact_method = self._get_contact_method(target, channel)
                if not contact_method:
                    continue
                
                # Create delivery record
                delivery = NotificationDelivery(
                    delivery_id=str(uuid.uuid4()),
                    request_id=request.request_id,
                    target_id=target.target_id,
                    channel=channel,
                    status=NotificationStatus.PENDING,
                    message_content=await self._prepare_message_content(request, rule, target, channel),
                    sent_at=None,
                    delivered_at=None,
                    max_retries=self.default_retry_limit,
                    metadata={
                        "rule_id": rule.rule_id,
                        "contact_method": contact_method,
                        "delivery_mode": rule.delivery_mode.value
                    }
                )
                
                # Store delivery record
                self.delivery_records[delivery.delivery_id] = delivery
                
                # Cache delivery record
                await self.cache.set(
                    f"delivery:{delivery.delivery_id}",
                    delivery.to_dict(),
                    ttl=self.cache_ttl
                )
                
                # Queue for delivery based on mode
                if rule.delivery_mode == DeliveryMode.IMMEDIATE:
                    asyncio.create_task(self._send_notification(delivery))
                elif rule.delivery_mode == DeliveryMode.BATCHED:
                    # Will be processed by batch processor
                    pass
                elif rule.delivery_mode == DeliveryMode.DIGEST:
                    # Will be processed by digest processor
                    pass
                
            self.logger.debug(f"Created {len(channels_to_use)} delivery records for target {target.target_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating delivery records: {str(e)}")
    
    async def _select_notification_channels(
        self,
        rule: NotificationRule,
        target: NotificationTarget,
        request: NotificationRequest
    ) -> List[NotificationChannel]:
        """Select appropriate notification channels"""
        try:
            # Start with rule's preferred channels
            candidate_channels = rule.channel_preferences.copy()
            
            # Consider request's preferred channels
            if request.preferred_channels:
                # Intersect with rule preferences
                candidate_channels = [ch for ch in candidate_channels if ch in request.preferred_channels]
            
            # Filter by target's available contact methods
            target_channels = set()
            for contact_method in target.contact_methods:
                channel = contact_method.get("channel")
                if channel:
                    target_channels.add(NotificationChannel(channel))
            
            available_channels = [ch for ch in candidate_channels if ch in target_channels]
            
            # Apply target preferences
            preferences = target.preferences
            
            # For immediate/high priority, use immediate notification channels
            if request.priority in [NotificationPriority.IMMEDIATE, NotificationPriority.HIGH]:
                immediate_channels = preferences.get("immediate_notifications", [])
                immediate_available = [ch for ch in available_channels if ch in immediate_channels]
                if immediate_available:
                    return immediate_available[:2]  # Limit to 2 immediate channels
            
            # For digest notifications
            if rule.delivery_mode == DeliveryMode.DIGEST:
                digest_channels = preferences.get("digest_notifications", [])
                digest_available = [ch for ch in available_channels if ch in digest_channels]
                if digest_available:
                    return digest_available[:1]  # One digest channel
            
            # Return first available channel if no specific preference
            return available_channels[:1] if available_channels else []
            
        except Exception as e:
            self.logger.error(f"Error selecting notification channels: {str(e)}")
            return []
    
    def _get_contact_method(self, target: NotificationTarget, channel: NotificationChannel) -> Optional[Dict[str, Any]]:
        """Get contact method for target and channel"""
        try:
            for contact_method in target.contact_methods:
                if contact_method.get("channel") == channel.value:
                    return contact_method
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting contact method: {str(e)}")
            return None
    
    async def _prepare_message_content(
        self,
        request: NotificationRequest,
        rule: NotificationRule,
        target: NotificationTarget,
        channel: NotificationChannel
    ) -> Dict[str, Any]:
        """Prepare message content for delivery"""
        try:
            # Get template
            template = self.notification_templates.get(rule.template_id)
            if not template:
                # Create basic template
                template = NotificationTemplate(
                    template_id="basic_template",
                    name="Basic Template",
                    notification_type=request.notification_type,
                    channel=channel,
                    subject_template="{notification_type}: {error_type}",
                    body_template="Error: {error_message}",
                    variables=["notification_type", "error_type", "error_message"]
                )
            
            # Prepare template variables
            variables = self._prepare_template_variables(request, target)
            
            # Render template
            subject = self._render_template(template.subject_template, variables)
            body = self._render_template(template.body_template, variables)
            
            return {
                "subject": subject,
                "body": body,
                "template_id": template.template_id,
                "variables": variables,
                "channel": channel.value
            }
            
        except Exception as e:
            self.logger.error(f"Error preparing message content: {str(e)}")
            return {
                "subject": f"Error Notification: {request.notification_type}",
                "body": json.dumps(request.data, indent=2),
                "channel": channel.value
            }
    
    def _prepare_template_variables(self, request: NotificationRequest, target: NotificationTarget) -> Dict[str, Any]:
        """Prepare variables for template rendering"""
        try:
            variables = {}
            
            # Add request data
            variables.update(request.data)
            
            # Add context data
            variables.update(request.context)
            
            # Add metadata
            variables.update({
                "request_id": request.request_id,
                "notification_type": request.notification_type,
                "priority": request.priority.value,
                "target_name": target.name,
                "created_at": request.created_at.isoformat()
            })
            
            # Add default values for common variables
            variables.setdefault("error_id", "N/A")
            variables.setdefault("error_type", "unknown")
            variables.setdefault("severity", "medium")
            variables.setdefault("service_name", "unknown")
            variables.setdefault("occurred_at", datetime.now(timezone.utc).isoformat())
            variables.setdefault("user_id", "N/A")
            variables.setdefault("operation_name", "N/A")
            variables.setdefault("trace_id", "N/A")
            
            return variables
            
        except Exception as e:
            self.logger.error(f"Error preparing template variables: {str(e)}")
            return {}
    
    def _render_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Render template with variables"""
        try:
            # Simple template rendering using string formatting
            # In production, consider using a proper template engine
            
            rendered = template
            for key, value in variables.items():
                placeholder = f"{{{key}}}"
                if placeholder in rendered:
                    rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            self.logger.error(f"Error rendering template: {str(e)}")
            return template
    
    async def _send_notification(self, delivery: NotificationDelivery):
        """Send a single notification"""
        try:
            delivery.status = NotificationStatus.SENDING
            delivery.sent_at = datetime.now(timezone.utc)
            
            # Get contact method from metadata
            contact_method = delivery.metadata.get("contact_method", {})
            
            # Send via notification service
            success = await self.notification_service.send_notification(
                type=delivery.channel.value,
                data=delivery.message_content,
                contact_info=contact_method
            )
            
            if success:
                delivery.status = NotificationStatus.DELIVERED
                delivery.delivered_at = datetime.now(timezone.utc)
                
                # Update rate limit counter
                await self._update_rate_limit_counter(delivery)
                
                # Emit delivery success event
                await self.event_bus.emit(
                    "notification.delivered",
                    {
                        "delivery_id": delivery.delivery_id,
                        "target_id": delivery.target_id,
                        "channel": delivery.channel.value
                    }
                )
                
            else:
                delivery.status = NotificationStatus.FAILED
                delivery.error_message = "Delivery service returned failure"
                
                # Retry if under limit
                if delivery.retry_count < delivery.max_retries:
                    delivery.retry_count += 1
                    delivery.status = NotificationStatus.PENDING
                    
                    # Schedule retry with exponential backoff
                    retry_delay = 2 ** delivery.retry_count * 60  # Minutes
                    await asyncio.sleep(retry_delay)
                    await self._send_notification(delivery)
            
            # Update cache
            await self.cache.set(
                f"delivery:{delivery.delivery_id}",
                delivery.to_dict(),
                ttl=self.cache_ttl
            )
            
        except Exception as e:
            self.logger.error(f"Error sending notification: {str(e)}")
            delivery.status = NotificationStatus.FAILED
            delivery.error_message = str(e)
    
    async def _update_rate_limit_counter(self, delivery: NotificationDelivery):
        """Update rate limit counters"""
        try:
            current_time = datetime.now(timezone.utc)
            window_key = current_time.strftime("%Y-%m-%d-%H")
            
            # Update target-channel counter
            counter_key = f"target_{delivery.target_id}_{delivery.channel.value}_{window_key}"
            if counter_key not in self.rate_limit_counters:
                self.rate_limit_counters[counter_key] = 0
            self.rate_limit_counters[counter_key] += 1
            
            # Update rule counter (if available)
            rule_id = delivery.metadata.get("rule_id")
            if rule_id:
                rule_counter_key = f"rule_{rule_id}_{delivery.target_id}_{window_key}"
                if rule_counter_key not in self.rate_limit_counters:
                    self.rate_limit_counters[rule_counter_key] = 0
                self.rate_limit_counters[rule_counter_key] += 1
            
        except Exception as e:
            self.logger.error(f"Error updating rate limit counter: {str(e)}")
    
    async def get_notification_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of notification request"""
        try:
            if request_id not in self.pending_requests:
                return {"status": "not_found"}
            
            request = self.pending_requests[request_id]
            
            # Get delivery records for this request
            deliveries = [
                d for d in self.delivery_records.values()
                if d.request_id == request_id
            ]
            
            # Calculate statistics
            total_deliveries = len(deliveries)
            delivered_count = len([d for d in deliveries if d.status == NotificationStatus.DELIVERED])
            failed_count = len([d for d in deliveries if d.status == NotificationStatus.FAILED])
            pending_count = len([d for d in deliveries if d.status in [NotificationStatus.PENDING, NotificationStatus.QUEUED]])
            
            return {
                "request_id": request_id,
                "notification_type": request.notification_type,
                "priority": request.priority,
                "created_at": request.created_at.isoformat(),
                "delivery_stats": {
                    "total": total_deliveries,
                    "delivered": delivered_count,
                    "failed": failed_count,
                    "pending": pending_count,
                    "success_rate": (delivered_count / total_deliveries) * 100 if total_deliveries > 0 else 0
                },
                "deliveries": [d.to_dict() for d in deliveries]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting notification status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_delivery_summary(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Get notification delivery summary"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            recent_deliveries = [
                d for d in self.delivery_records.values()
                if d.sent_at and d.sent_at >= cutoff_time
            ]
            
            # Calculate statistics
            total_deliveries = len(recent_deliveries)
            delivered_count = len([d for d in recent_deliveries if d.status == NotificationStatus.DELIVERED])
            failed_count = len([d for d in recent_deliveries if d.status == NotificationStatus.FAILED])
            
            # Channel distribution
            channel_distribution = {}
            for channel in NotificationChannel:
                channel_distribution[channel.value] = len([d for d in recent_deliveries if d.channel == channel])
            
            # Target distribution
            target_distribution = {}
            for delivery in recent_deliveries:
                target_id = delivery.target_id
                if target_id not in target_distribution:
                    target_distribution[target_id] = 0
                target_distribution[target_id] += 1
            
            # Average delivery time
            successful_deliveries = [d for d in recent_deliveries if d.status == NotificationStatus.DELIVERED and d.sent_at and d.delivered_at]
            avg_delivery_seconds = 0
            if successful_deliveries:
                delivery_times = [(d.delivered_at - d.sent_at).total_seconds() for d in successful_deliveries]
                avg_delivery_seconds = sum(delivery_times) / len(delivery_times)
            
            return {
                "time_range_hours": time_range_hours,
                "total_deliveries": total_deliveries,
                "delivered_count": delivered_count,
                "failed_count": failed_count,
                "success_rate": (delivered_count / total_deliveries) * 100 if total_deliveries > 0 else 0,
                "channel_distribution": channel_distribution,
                "target_distribution": target_distribution,
                "avg_delivery_seconds": avg_delivery_seconds,
                "rules_configured": len(self.notification_rules),
                "targets_configured": len(self.notification_targets),
                "templates_configured": len(self.notification_templates)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting delivery summary: {str(e)}")
            return {}
    
    async def _notification_processor(self):
        """Background notification processing task"""
        while True:
            try:
                await asyncio.sleep(10)  # Every 10 seconds
                
                # Process pending immediate deliveries
                pending_deliveries = [
                    d for d in self.delivery_records.values()
                    if d.status == NotificationStatus.PENDING and d.metadata.get("delivery_mode") == DeliveryMode.IMMEDIATE.value
                ]
                
                for delivery in pending_deliveries[:10]:  # Process up to 10 at a time
                    asyncio.create_task(self._send_notification(delivery))
                
            except Exception as e:
                self.logger.error(f"Error in notification processor: {str(e)}")
    
    async def _batch_processor(self):
        """Background batch notification processor"""
        while True:
            try:
                await asyncio.sleep(self.batch_interval_seconds)
                
                # Process batched deliveries
                batched_deliveries = [
                    d for d in self.delivery_records.values()
                    if d.status == NotificationStatus.PENDING and d.metadata.get("delivery_mode") == DeliveryMode.BATCHED.value
                ]
                
                # Group by target and channel
                batches = {}
                for delivery in batched_deliveries:
                    key = f"{delivery.target_id}_{delivery.channel.value}"
                    if key not in batches:
                        batches[key] = []
                    batches[key].append(delivery)
                
                # Send batches
                for batch in batches.values():
                    if len(batch) >= self.batch_size:
                        for delivery in batch:
                            asyncio.create_task(self._send_notification(delivery))
                
            except Exception as e:
                self.logger.error(f"Error in batch processor: {str(e)}")
    
    async def _digest_processor(self):
        """Background digest notification processor"""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                
                # Process digest deliveries
                # This would aggregate multiple notifications into digest format
                
            except Exception as e:
                self.logger.error(f"Error in digest processor: {str(e)}")
    
    async def _cleanup_old_records(self):
        """Cleanup old notification records"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=7)
                
                # Remove old delivery records
                old_deliveries = [
                    d_id for d_id, d in self.delivery_records.items()
                    if d.sent_at and d.sent_at < cutoff_time
                ]
                
                for delivery_id in old_deliveries:
                    del self.delivery_records[delivery_id]
                
                # Remove old requests
                old_requests = [
                    r_id for r_id, r in self.pending_requests.items()
                    if r.created_at < cutoff_time
                ]
                
                for request_id in old_requests:
                    del self.pending_requests[request_id]
                
                # Clean rate limit counters
                current_time = datetime.now(timezone.utc)
                old_windows = [
                    key for key in self.rate_limit_counters.keys()
                    if not key.endswith(current_time.strftime("%Y-%m-%d-%H"))
                ]
                
                for key in old_windows:
                    del self.rate_limit_counters[key]
                
                self.logger.info(f"Cleaned up {len(old_deliveries)} old deliveries, {len(old_requests)} old requests")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "error.occurred",
                self._handle_error_occurred
            )
            
            await self.event_bus.subscribe(
                "escalation.created",
                self._handle_escalation_created
            )
            
            await self.event_bus.subscribe(
                "recovery.execution_failed",
                self._handle_recovery_failed
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_error_occurred(self, event_data: Dict[str, Any]):
        """Handle error occurred event"""
        try:
            await self.route_notification(
                notification_type="error_occurred",
                data=event_data,
                context=event_data.get("context", {}),
                priority=NotificationPriority(event_data.get("severity", "medium"))
            )
            
        except Exception as e:
            self.logger.error(f"Error handling error occurred: {str(e)}")
    
    async def _handle_escalation_created(self, event_data: Dict[str, Any]):
        """Handle escalation created event"""
        try:
            await self.route_notification(
                notification_type="escalation_created",
                data=event_data,
                priority=NotificationPriority.HIGH
            )
            
        except Exception as e:
            self.logger.error(f"Error handling escalation created: {str(e)}")
    
    async def _handle_recovery_failed(self, event_data: Dict[str, Any]):
        """Handle recovery failure event"""
        try:
            await self.route_notification(
                notification_type="recovery_failed",
                data=event_data,
                priority=NotificationPriority.HIGH
            )
            
        except Exception as e:
            self.logger.error(f"Error handling recovery failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            pending_deliveries = len([d for d in self.delivery_records.values() if d.status == NotificationStatus.PENDING])
            failed_deliveries = len([d for d in self.delivery_records.values() if d.status == NotificationStatus.FAILED])
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "notification_router",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_targets": len(self.notification_targets),
                    "total_rules": len(self.notification_rules),
                    "total_templates": len(self.notification_templates),
                    "pending_requests": len(self.pending_requests),
                    "delivery_records": len(self.delivery_records),
                    "pending_deliveries": pending_deliveries,
                    "failed_deliveries": failed_deliveries
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "notification_router",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Notification router service cleanup initiated")
        
        try:
            # Clear all state
            self.pending_requests.clear()
            self.delivery_records.clear()
            self.rate_limit_counters.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Notification router service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_notification_router() -> NotificationRouter:
    """Create notification router service"""
    return NotificationRouter()