"""
Security Orchestrator - Core Platform Security

Coordinates security measures across all platform roles and services.
Provides unified security policy enforcement, threat correlation, and incident coordination.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class ServiceRole(Enum):
    """Service role types for security orchestration"""
    SI_SERVICES = "si_services"
    APP_SERVICES = "app_services"
    HYBRID_SERVICES = "hybrid_services"
    CORE_PLATFORM = "core_platform"
    EXTERNAL_INTEGRATIONS = "external_integrations"


class SecurityDomain(Enum):
    """Security domains for orchestration"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_PROTECTION = "data_protection"
    NETWORK_SECURITY = "network_security"
    THREAT_DETECTION = "threat_detection"
    INCIDENT_RESPONSE = "incident_response"
    COMPLIANCE = "compliance"
    VULNERABILITY_MANAGEMENT = "vulnerability_management"
    AUDIT_LOGGING = "audit_logging"
    ACCESS_CONTROL = "access_control"


class SecurityLevel(Enum):
    """Security levels for risk assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PolicyType(Enum):
    """Types of security policies"""
    AUTHENTICATION_POLICY = "authentication_policy"
    AUTHORIZATION_POLICY = "authorization_policy"
    DATA_PROTECTION_POLICY = "data_protection_policy"
    NETWORK_POLICY = "network_policy"
    THREAT_RESPONSE_POLICY = "threat_response_policy"
    COMPLIANCE_POLICY = "compliance_policy"
    INCIDENT_RESPONSE_POLICY = "incident_response_policy"


class SecurityEventType(Enum):
    """Types of security events"""
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_DENIAL = "authorization_denial"
    THREAT_DETECTED = "threat_detected"
    VULNERABILITY_FOUND = "vulnerability_found"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SECURITY_INCIDENT = "security_incident"
    POLICY_VIOLATION = "policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    policy_id: str
    name: str
    description: str
    policy_type: PolicyType
    service_roles: List[ServiceRole]
    security_domains: List[SecurityDomain]
    rules: List[Dict[str, Any]]
    enforcement_level: SecurityLevel
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"


@dataclass
class SecurityEvent:
    """Security event for cross-platform tracking"""
    event_id: str
    event_type: SecurityEventType
    source_service: str
    source_role: ServiceRole
    security_domain: SecurityDomain
    severity: SecurityLevel
    timestamp: datetime
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    affected_resources: List[str] = field(default_factory=list)
    user_context: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    remediation_actions: List[str] = field(default_factory=list)
    status: str = "open"


@dataclass
class SecurityMetric:
    """Security metrics for monitoring"""
    metric_id: str
    service_role: ServiceRole
    security_domain: SecurityDomain
    metric_name: str
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    threshold_breached: bool = False


@dataclass
class ThreatCorrelation:
    """Correlated threat information across services"""
    correlation_id: str
    threat_pattern: str
    severity: SecurityLevel
    affected_services: Set[str]
    service_roles: Set[ServiceRole]
    first_seen: datetime
    last_seen: datetime
    event_count: int
    confidence_score: float
    indicators: List[Dict[str, Any]] = field(default_factory=list)
    mitigation_status: str = "active"


class SecurityOrchestrator:
    """
    Central security orchestrator for the TaxPoynt platform.
    
    Coordinates security across all platform components:
    - SI Services (Certificate management, ERP integration security, etc.)
    - APP Services (FIRS communication security, taxpayer data protection, etc.)
    - Hybrid Services (Cross-service access control, billing security, etc.)
    - Core Platform (Authentication, authorization, data management security, etc.)
    - External Integrations (Third-party security, API security, etc.)
    """
    
    def __init__(self):
        # Security policies and rules
        self.security_policies: Dict[str, SecurityPolicy] = {}
        self.active_policies_by_role: Dict[ServiceRole, List[SecurityPolicy]] = defaultdict(list)
        self.policy_violations: deque = deque(maxlen=10000)
        
        # Security events and monitoring
        self.security_events: deque = deque(maxlen=50000)
        self.event_correlations: Dict[str, ThreatCorrelation] = {}
        self.security_metrics: deque = deque(maxlen=25000)
        
        # Service registration and health
        self.registered_services: Dict[str, Dict[str, Any]] = {}
        self.service_security_status: Dict[str, Dict[str, Any]] = {}
        
        # Processing queues
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.policy_enforcement_queue: asyncio.Queue = asyncio.Queue()
        self.correlation_queue: asyncio.Queue = asyncio.Queue()
        
        # Background tasks
        self._running = False
        self._event_processor_task = None
        self._policy_enforcer_task = None
        self._correlator_task = None
        self._metrics_collector_task = None
        
        # Dependencies - will be injected
        self.threat_intelligence = None
        self.vulnerability_scanner = None
        self.compliance_enforcer = None
        self.incident_responder = None
        self.metrics_aggregator = None
        self.alert_manager = None
        
        # Event handlers
        self.security_event_handlers: List[Callable] = []
        self.policy_violation_handlers: List[Callable] = []
        self.threat_correlation_handlers: List[Callable] = []
        
        # Configuration
        self.correlation_window_minutes = 30
        self.threat_confidence_threshold = 0.7
        self.auto_mitigation_enabled = True
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "policies_enforced": 0,
            "threats_correlated": 0,
            "incidents_triggered": 0,
            "vulnerabilities_found": 0,
            "compliance_checks": 0,
            "auto_mitigations": 0
        }
    
    # === Dependency Injection ===
    
    def set_threat_intelligence(self, threat_intelligence):
        """Inject threat intelligence dependency"""
        self.threat_intelligence = threat_intelligence
    
    def set_vulnerability_scanner(self, vulnerability_scanner):
        """Inject vulnerability scanner dependency"""
        self.vulnerability_scanner = vulnerability_scanner
    
    def set_compliance_enforcer(self, compliance_enforcer):
        """Inject compliance enforcer dependency"""
        self.compliance_enforcer = compliance_enforcer
    
    def set_incident_responder(self, incident_responder):
        """Inject incident responder dependency"""
        self.incident_responder = incident_responder
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    def set_alert_manager(self, alert_manager):
        """Inject alert manager dependency"""
        self.alert_manager = alert_manager
    
    # === Service Registration ===
    
    def register_security_service(
        self,
        service_name: str,
        service_role: ServiceRole,
        security_domains: List[SecurityDomain],
        capabilities: List[str],
        endpoint: Optional[str] = None,
        health_check_interval: int = 300
    ) -> bool:
        """Register a service for security orchestration"""
        try:
            service_info = {
                "service_name": service_name,
                "service_role": service_role,
                "security_domains": security_domains,
                "capabilities": capabilities,
                "endpoint": endpoint,
                "health_check_interval": health_check_interval,
                "registered_at": datetime.utcnow(),
                "last_health_check": None,
                "status": "active"
            }
            
            self.registered_services[service_name] = service_info
            
            # Initialize security status
            self.service_security_status[service_name] = {
                "overall_security_level": SecurityLevel.MEDIUM,
                "active_threats": 0,
                "vulnerabilities": 0,
                "compliance_score": 0.0,
                "last_assessment": datetime.utcnow(),
                "security_events_24h": 0
            }
            
            logger.info(f"Registered security service: {service_name} ({service_role.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register security service {service_name}: {e}")
            return False
    
    def unregister_security_service(self, service_name: str) -> bool:
        """Unregister a security service"""
        try:
            if service_name in self.registered_services:
                del self.registered_services[service_name]
            
            if service_name in self.service_security_status:
                del self.service_security_status[service_name]
            
            logger.info(f"Unregistered security service: {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister security service {service_name}: {e}")
            return False
    
    def get_registered_services(self, service_role: Optional[ServiceRole] = None) -> List[Dict[str, Any]]:
        """Get registered security services"""
        services = list(self.registered_services.values())
        
        if service_role:
            services = [s for s in services if s["service_role"] == service_role]
        
        return services
    
    # === Security Policy Management ===
    
    def create_security_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        policy_type: PolicyType,
        service_roles: List[ServiceRole],
        security_domains: List[SecurityDomain],
        rules: List[Dict[str, Any]],
        enforcement_level: SecurityLevel = SecurityLevel.MEDIUM
    ) -> bool:
        """Create a new security policy"""
        try:
            policy = SecurityPolicy(
                policy_id=policy_id,
                name=name,
                description=description,
                policy_type=policy_type,
                service_roles=service_roles,
                security_domains=security_domains,
                rules=rules,
                enforcement_level=enforcement_level
            )
            
            self.security_policies[policy_id] = policy
            
            # Update role-based policy mapping
            for role in service_roles:
                self.active_policies_by_role[role].append(policy)
            
            logger.info(f"Created security policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create security policy {policy_id}: {e}")
            return False
    
    def update_security_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing security policy"""
        try:
            if policy_id not in self.security_policies:
                return False
            
            policy = self.security_policies[policy_id]
            
            # Remove from old role mappings
            for role in policy.service_roles:
                if policy in self.active_policies_by_role[role]:
                    self.active_policies_by_role[role].remove(policy)
            
            # Update policy
            for key, value in updates.items():
                if hasattr(policy, key):
                    setattr(policy, key, value)
            
            policy.updated_at = datetime.utcnow()
            policy.version = f"{float(policy.version) + 0.1:.1f}"
            
            # Update role mappings
            for role in policy.service_roles:
                if policy not in self.active_policies_by_role[role]:
                    self.active_policies_by_role[role].append(policy)
            
            logger.info(f"Updated security policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update security policy {policy_id}: {e}")
            return False
    
    def get_security_policies(
        self,
        service_role: Optional[ServiceRole] = None,
        security_domain: Optional[SecurityDomain] = None,
        enabled_only: bool = True
    ) -> List[SecurityPolicy]:
        """Get security policies with optional filtering"""
        policies = list(self.security_policies.values())
        
        if enabled_only:
            policies = [p for p in policies if p.enabled]
        
        if service_role:
            policies = [p for p in policies if service_role in p.service_roles]
        
        if security_domain:
            policies = [p for p in policies if security_domain in p.security_domains]
        
        return policies
    
    # === Security Event Management ===
    
    async def report_security_event(
        self,
        event_type: SecurityEventType,
        source_service: str,
        source_role: ServiceRole,
        security_domain: SecurityDomain,
        severity: SecurityLevel,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        affected_resources: Optional[List[str]] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Report a security event for orchestration"""
        
        event_id = str(uuid.uuid4())
        
        security_event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            source_service=source_service,
            source_role=source_role,
            security_domain=security_domain,
            severity=severity,
            timestamp=datetime.utcnow(),
            description=description,
            details=details or {},
            affected_resources=affected_resources or [],
            user_context=user_context
        )
        
        # Store event
        self.security_events.append(security_event)
        
        # Queue for processing
        await self.event_queue.put(security_event)
        
        # Update service security status
        self._update_service_security_status(source_service, security_event)
        
        # Update statistics
        self.stats["events_processed"] += 1
        
        # Notify handlers
        await self._notify_security_event_handlers(security_event)
        
        logger.info(f"Security event reported: {event_id} from {source_service}")
        return event_id
    
    def get_security_events(
        self,
        service_name: Optional[str] = None,
        service_role: Optional[ServiceRole] = None,
        security_domain: Optional[SecurityDomain] = None,
        severity: Optional[SecurityLevel] = None,
        hours: Optional[int] = None,
        limit: int = 1000
    ) -> List[SecurityEvent]:
        """Get security events with filtering"""
        events = list(self.security_events)
        
        # Apply filters
        if service_name:
            events = [e for e in events if e.source_service == service_name]
        
        if service_role:
            events = [e for e in events if e.source_role == service_role]
        
        if security_domain:
            events = [e for e in events if e.security_domain == security_domain]
        
        if severity:
            events = [e for e in events if e.severity == severity]
        
        if hours:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            events = [e for e in events if e.timestamp >= cutoff_time]
        
        # Sort by timestamp descending
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        return events[:limit]
    
    # === Threat Correlation ===
    
    async def correlate_security_events(self) -> List[ThreatCorrelation]:
        """Correlate security events to identify threats"""
        correlations = []
        
        try:
            # Get recent events for correlation
            recent_events = self.get_security_events(hours=self.correlation_window_minutes / 60)
            
            if len(recent_events) < 2:
                return correlations
            
            # Group events by potential correlation patterns
            correlation_groups = self._group_events_for_correlation(recent_events)
            
            for pattern, events in correlation_groups.items():
                if len(events) >= 2:  # Minimum events for correlation
                    correlation = await self._analyze_correlation_pattern(pattern, events)
                    if correlation and correlation.confidence_score >= self.threat_confidence_threshold:
                        correlations.append(correlation)
                        
                        # Store correlation
                        self.event_correlations[correlation.correlation_id] = correlation
                        
                        # Update statistics
                        self.stats["threats_correlated"] += 1
                        
                        # Trigger incident response if critical
                        if correlation.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                            await self._trigger_incident_response(correlation)
            
            return correlations
            
        except Exception as e:
            logger.error(f"Error correlating security events: {e}")
            return correlations
    
    def _group_events_for_correlation(self, events: List[SecurityEvent]) -> Dict[str, List[SecurityEvent]]:
        """Group events by correlation patterns"""
        correlation_groups = defaultdict(list)
        
        for event in events:
            # Group by user context
            if event.user_context and event.user_context.get("user_id"):
                user_pattern = f"user_{event.user_context['user_id']}"
                correlation_groups[user_pattern].append(event)
            
            # Group by source IP
            if event.user_context and event.user_context.get("source_ip"):
                ip_pattern = f"ip_{event.user_context['source_ip']}"
                correlation_groups[ip_pattern].append(event)
            
            # Group by affected resources
            for resource in event.affected_resources:
                resource_pattern = f"resource_{resource}"
                correlation_groups[resource_pattern].append(event)
            
            # Group by event type and domain
            type_pattern = f"type_{event.event_type.value}_{event.security_domain.value}"
            correlation_groups[type_pattern].append(event)
        
        return correlation_groups
    
    async def _analyze_correlation_pattern(self, pattern: str, events: List[SecurityEvent]) -> Optional[ThreatCorrelation]:
        """Analyze correlation pattern and generate threat correlation"""
        try:
            # Calculate confidence score based on various factors
            confidence_score = self._calculate_correlation_confidence(events)
            
            if confidence_score < self.threat_confidence_threshold:
                return None
            
            # Determine severity
            max_severity = max(events, key=lambda e: self._severity_weight(e.severity)).severity
            
            # Determine affected services and roles
            affected_services = set(e.source_service for e in events)
            service_roles = set(e.source_role for e in events)
            
            # Generate correlation
            correlation_id = str(uuid.uuid4())
            
            correlation = ThreatCorrelation(
                correlation_id=correlation_id,
                threat_pattern=pattern,
                severity=max_severity,
                affected_services=affected_services,
                service_roles=service_roles,
                first_seen=min(e.timestamp for e in events),
                last_seen=max(e.timestamp for e in events),
                event_count=len(events),
                confidence_score=confidence_score,
                indicators=self._extract_threat_indicators(events)
            )
            
            return correlation
            
        except Exception as e:
            logger.error(f"Error analyzing correlation pattern {pattern}: {e}")
            return None
    
    def _calculate_correlation_confidence(self, events: List[SecurityEvent]) -> float:
        """Calculate confidence score for event correlation"""
        if len(events) < 2:
            return 0.0
        
        confidence = 0.0
        
        # Factor 1: Number of events (more events = higher confidence)
        event_factor = min(len(events) / 10, 1.0) * 0.3
        confidence += event_factor
        
        # Factor 2: Time clustering (events close in time = higher confidence)
        time_span = (max(e.timestamp for e in events) - min(e.timestamp for e in events)).total_seconds()
        time_factor = max(0, (1800 - time_span) / 1800) * 0.2  # 30 minutes window
        confidence += time_factor
        
        # Factor 3: Severity clustering (similar severity = higher confidence)
        severity_weights = [self._severity_weight(e.severity) for e in events]
        severity_variance = max(severity_weights) - min(severity_weights)
        severity_factor = max(0, (3 - severity_variance) / 3) * 0.2
        confidence += severity_factor
        
        # Factor 4: Domain clustering (same domain = higher confidence)
        domains = set(e.security_domain for e in events)
        domain_factor = (1.0 / len(domains)) * 0.15
        confidence += domain_factor
        
        # Factor 5: Pattern-specific factors
        pattern_factor = 0.15  # Base pattern factor
        confidence += pattern_factor
        
        return min(confidence, 1.0)
    
    def _severity_weight(self, severity: SecurityLevel) -> int:
        """Get numeric weight for severity"""
        weights = {
            SecurityLevel.LOW: 1,
            SecurityLevel.MEDIUM: 2,
            SecurityLevel.HIGH: 3,
            SecurityLevel.CRITICAL: 4
        }
        return weights.get(severity, 0)
    
    def _extract_threat_indicators(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Extract threat indicators from correlated events"""
        indicators = []
        
        # Extract common patterns
        user_ids = set()
        source_ips = set()
        resources = set()
        
        for event in events:
            if event.user_context:
                if event.user_context.get("user_id"):
                    user_ids.add(event.user_context["user_id"])
                if event.user_context.get("source_ip"):
                    source_ips.add(event.user_context["source_ip"])
            
            resources.update(event.affected_resources)
        
        # Create indicators
        if user_ids:
            indicators.append({
                "type": "user_id",
                "values": list(user_ids),
                "description": "User IDs involved in threat pattern"
            })
        
        if source_ips:
            indicators.append({
                "type": "source_ip",
                "values": list(source_ips),
                "description": "Source IPs involved in threat pattern"
            })
        
        if resources:
            indicators.append({
                "type": "resource",
                "values": list(resources),
                "description": "Resources affected by threat pattern"
            })
        
        return indicators
    
    # === Policy Enforcement ===
    
    async def enforce_security_policies(self, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Enforce security policies for an event"""
        enforcement_actions = []
        
        try:
            # Get applicable policies
            applicable_policies = self._get_applicable_policies(event)
            
            for policy in applicable_policies:
                actions = await self._enforce_policy(policy, event)
                enforcement_actions.extend(actions)
                
                if actions:
                    # Record policy enforcement
                    self.stats["policies_enforced"] += 1
                    
                    # Log policy violation if actions were taken
                    violation = {
                        "policy_id": policy.policy_id,
                        "event_id": event.event_id,
                        "service": event.source_service,
                        "violation_time": datetime.utcnow(),
                        "actions_taken": actions
                    }
                    self.policy_violations.append(violation)
                    
                    # Notify handlers
                    await self._notify_policy_violation_handlers(policy, event, actions)
            
            return enforcement_actions
            
        except Exception as e:
            logger.error(f"Error enforcing security policies: {e}")
            return enforcement_actions
    
    def _get_applicable_policies(self, event: SecurityEvent) -> List[SecurityPolicy]:
        """Get policies applicable to a security event"""
        applicable_policies = []
        
        # Get policies for the service role
        role_policies = self.active_policies_by_role.get(event.source_role, [])
        
        for policy in role_policies:
            if not policy.enabled:
                continue
            
            # Check if policy applies to the security domain
            if event.security_domain in policy.security_domains:
                applicable_policies.append(policy)
        
        return applicable_policies
    
    async def _enforce_policy(self, policy: SecurityPolicy, event: SecurityEvent) -> List[Dict[str, Any]]:
        """Enforce a specific policy against an event"""
        actions = []
        
        try:
            for rule in policy.rules:
                action = await self._evaluate_policy_rule(rule, event, policy)
                if action:
                    actions.append(action)
            
            return actions
            
        except Exception as e:
            logger.error(f"Error enforcing policy {policy.policy_id}: {e}")
            return actions
    
    async def _evaluate_policy_rule(self, rule: Dict[str, Any], event: SecurityEvent, policy: SecurityPolicy) -> Optional[Dict[str, Any]]:
        """Evaluate a policy rule against an event"""
        try:
            # Simple rule evaluation - can be extended with complex rule engine
            condition = rule.get("condition", {})
            action_config = rule.get("action", {})
            
            if self._rule_matches_event(condition, event):
                action = {
                    "policy_id": policy.policy_id,
                    "rule_id": rule.get("rule_id", "unknown"),
                    "action_type": action_config.get("type", "log"),
                    "action_details": action_config.get("details", {}),
                    "enforcement_level": policy.enforcement_level.value,
                    "timestamp": datetime.utcnow()
                }
                
                # Execute action if auto-mitigation is enabled
                if self.auto_mitigation_enabled:
                    await self._execute_policy_action(action, event)
                
                return action
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating policy rule: {e}")
            return None
    
    def _rule_matches_event(self, condition: Dict[str, Any], event: SecurityEvent) -> bool:
        """Check if a rule condition matches an event"""
        try:
            # Check event type
            if "event_type" in condition:
                if event.event_type.value not in condition["event_type"]:
                    return False
            
            # Check severity
            if "min_severity" in condition:
                min_severity = SecurityLevel(condition["min_severity"])
                if self._severity_weight(event.severity) < self._severity_weight(min_severity):
                    return False
            
            # Check security domain
            if "security_domain" in condition:
                if event.security_domain.value not in condition["security_domain"]:
                    return False
            
            # Check source service
            if "source_service" in condition:
                if event.source_service not in condition["source_service"]:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error matching rule condition: {e}")
            return False
    
    async def _execute_policy_action(self, action: Dict[str, Any], event: SecurityEvent):
        """Execute a policy enforcement action"""
        try:
            action_type = action["action_type"]
            
            if action_type == "block_user" and event.user_context:
                # Trigger user blocking
                await self._block_user(event.user_context.get("user_id"))
            
            elif action_type == "block_ip" and event.user_context:
                # Trigger IP blocking
                await self._block_ip(event.user_context.get("source_ip"))
            
            elif action_type == "alert":
                # Trigger alert
                await self._trigger_security_alert(action, event)
            
            elif action_type == "escalate":
                # Trigger incident escalation
                await self._escalate_security_incident(action, event)
            
            # Log action execution
            logger.info(f"Executed policy action: {action_type} for event {event.event_id}")
            self.stats["auto_mitigations"] += 1
            
        except Exception as e:
            logger.error(f"Error executing policy action: {e}")
    
    # === Security Assessment ===
    
    def get_platform_security_overview(self) -> Dict[str, Any]:
        """Get comprehensive platform security overview"""
        
        # Calculate overall security metrics
        current_time = datetime.utcnow()
        last_24h = current_time - timedelta(hours=24)
        
        recent_events = [e for e in self.security_events if e.timestamp >= last_24h]
        critical_events = [e for e in recent_events if e.severity == SecurityLevel.CRITICAL]
        high_events = [e for e in recent_events if e.severity == SecurityLevel.HIGH]
        
        # Service role breakdown
        events_by_role = defaultdict(int)
        for event in recent_events:
            events_by_role[event.source_role.value] += 1
        
        # Security domain breakdown
        events_by_domain = defaultdict(int)
        for event in recent_events:
            events_by_domain[event.security_domain.value] += 1
        
        # Threat correlation summary
        active_correlations = [c for c in self.event_correlations.values() if c.mitigation_status == "active"]
        critical_correlations = [c for c in active_correlations if c.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]]
        
        return {
            "timestamp": current_time,
            "overall_security_level": self._calculate_platform_security_level(),
            "registered_services": len(self.registered_services),
            "active_policies": len([p for p in self.security_policies.values() if p.enabled]),
            "events_24h": {
                "total": len(recent_events),
                "critical": len(critical_events),
                "high": len(high_events),
                "by_role": dict(events_by_role),
                "by_domain": dict(events_by_domain)
            },
            "threat_correlations": {
                "active": len(active_correlations),
                "critical": len(critical_correlations),
                "avg_confidence": sum(c.confidence_score for c in active_correlations) / len(active_correlations) if active_correlations else 0
            },
            "policy_enforcement": {
                "violations_24h": len([v for v in self.policy_violations if v["violation_time"] >= last_24h]),
                "auto_mitigations": self.stats["auto_mitigations"]
            },
            "statistics": self.stats.copy()
        }
    
    def get_service_security_assessment(self, service_name: str) -> Dict[str, Any]:
        """Get security assessment for a specific service"""
        if service_name not in self.service_security_status:
            return {"error": "Service not found"}
        
        service_info = self.registered_services.get(service_name, {})
        security_status = self.service_security_status[service_name]
        
        # Get recent events for this service
        recent_events = self.get_security_events(service_name=service_name, hours=24)
        
        # Get applicable policies
        service_role = service_info.get("service_role")
        applicable_policies = []
        if service_role:
            applicable_policies = self.active_policies_by_role.get(service_role, [])
        
        return {
            "service_name": service_name,
            "service_info": service_info,
            "security_status": security_status,
            "recent_events": len(recent_events),
            "applicable_policies": len(applicable_policies),
            "security_domains": service_info.get("security_domains", []),
            "last_assessment": security_status.get("last_assessment"),
            "recommendations": self._generate_security_recommendations(service_name, recent_events)
        }
    
    def _calculate_platform_security_level(self) -> str:
        """Calculate overall platform security level"""
        try:
            # Get recent critical and high severity events
            recent_events = self.get_security_events(hours=24)
            critical_count = len([e for e in recent_events if e.severity == SecurityLevel.CRITICAL])
            high_count = len([e for e in recent_events if e.severity == SecurityLevel.HIGH])
            
            # Get active critical correlations
            critical_correlations = len([
                c for c in self.event_correlations.values()
                if c.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL] and c.mitigation_status == "active"
            ])
            
            # Calculate security level
            if critical_count > 5 or critical_correlations > 2:
                return "critical"
            elif critical_count > 0 or high_count > 10 or critical_correlations > 0:
                return "high"
            elif high_count > 0:
                return "medium"
            else:
                return "low"
                
        except Exception:
            return "unknown"
    
    def _update_service_security_status(self, service_name: str, event: SecurityEvent):
        """Update security status for a service"""
        if service_name not in self.service_security_status:
            return
        
        status = self.service_security_status[service_name]
        
        # Update event count
        status["security_events_24h"] += 1
        
        # Update overall security level if event is severe
        if event.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
            if event.severity == SecurityLevel.CRITICAL:
                status["overall_security_level"] = SecurityLevel.CRITICAL
            elif status["overall_security_level"] not in [SecurityLevel.CRITICAL]:
                status["overall_security_level"] = SecurityLevel.HIGH
        
        status["last_assessment"] = datetime.utcnow()
    
    def _generate_security_recommendations(self, service_name: str, recent_events: List[SecurityEvent]) -> List[str]:
        """Generate security recommendations for a service"""
        recommendations = []
        
        if not recent_events:
            recommendations.append("No recent security events - maintain current security posture")
            return recommendations
        
        # Analyze event patterns
        event_types = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in recent_events:
            event_types[event.event_type.value] += 1
            severity_counts[event.severity.value] += 1
        
        # Generate recommendations based on patterns
        if event_types.get("authentication_failure", 0) > 5:
            recommendations.append("High authentication failures detected - review authentication mechanisms")
        
        if event_types.get("authorization_denial", 0) > 3:
            recommendations.append("Multiple authorization denials - review access control policies")
        
        if severity_counts.get("critical", 0) > 0:
            recommendations.append("Critical security events detected - immediate review required")
        
        if severity_counts.get("high", 0) > 5:
            recommendations.append("High severity events detected - security assessment recommended")
        
        if not recommendations:
            recommendations.append("Security posture is acceptable - continue monitoring")
        
        return recommendations
    
    # === Background Tasks ===
    
    async def start_security_orchestration(self):
        """Start security orchestration background tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._event_processor_task = asyncio.create_task(self._process_security_events())
        self._policy_enforcer_task = asyncio.create_task(self._enforce_policies())
        self._correlator_task = asyncio.create_task(self._correlate_threats())
        self._metrics_collector_task = asyncio.create_task(self._collect_security_metrics())
        
        logger.info("Security orchestration started")
    
    async def stop_security_orchestration(self):
        """Stop security orchestration background tasks"""
        self._running = False
        
        # Cancel tasks
        for task in [self._event_processor_task, self._policy_enforcer_task, 
                     self._correlator_task, self._metrics_collector_task]:
            if task:
                task.cancel()
        
        logger.info("Security orchestration stopped")
    
    async def _process_security_events(self):
        """Background task for processing security events"""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                
                # Process the event
                await self._process_single_event(event)
                
                # Mark task as done
                self.event_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing security event: {e}")
                await asyncio.sleep(1)
    
    async def _enforce_policies(self):
        """Background task for policy enforcement"""
        while self._running:
            try:
                # Get event from policy enforcement queue
                event = await asyncio.wait_for(self.policy_enforcement_queue.get(), timeout=1.0)
                
                # Enforce policies
                await self.enforce_security_policies(event)
                
                # Mark task as done
                self.policy_enforcement_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in policy enforcement: {e}")
                await asyncio.sleep(1)
    
    async def _correlate_threats(self):
        """Background task for threat correlation"""
        while self._running:
            try:
                # Run correlation every 5 minutes
                await self.correlate_security_events()
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in threat correlation: {e}")
                await asyncio.sleep(300)
    
    async def _collect_security_metrics(self):
        """Background task for collecting security metrics"""
        while self._running:
            try:
                # Collect metrics every minute
                await self._collect_platform_security_metrics()
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting security metrics: {e}")
                await asyncio.sleep(60)
    
    async def _process_single_event(self, event: SecurityEvent):
        """Process a single security event"""
        try:
            # Queue for policy enforcement
            await self.policy_enforcement_queue.put(event)
            
            # Queue for correlation
            await self.correlation_queue.put(event)
            
            # Send to threat intelligence if available
            if self.threat_intelligence:
                await self.threat_intelligence.analyze_security_event(event)
            
            # Send metrics if available
            if self.metrics_aggregator:
                await self._send_security_metrics(event)
            
        except Exception as e:
            logger.error(f"Error processing event {event.event_id}: {e}")
    
    async def _collect_platform_security_metrics(self):
        """Collect platform-wide security metrics"""
        try:
            current_time = datetime.utcnow()
            
            # Collect metrics for each service role
            for role in ServiceRole:
                role_services = [s for s in self.registered_services.values() if s["service_role"] == role]
                
                if role_services:
                    # Count recent events
                    recent_events = self.get_security_events(service_role=role, hours=1)
                    
                    metric = SecurityMetric(
                        metric_id=str(uuid.uuid4()),
                        service_role=role,
                        security_domain=SecurityDomain.THREAT_DETECTION,
                        metric_name="security_events_per_hour",
                        value=len(recent_events),
                        timestamp=current_time,
                        tags={"role": role.value}
                    )
                    
                    self.security_metrics.append(metric)
                    
                    # Send to metrics aggregator if available
                    if self.metrics_aggregator:
                        await self.metrics_aggregator.collect_metric_point(
                            name="security_events_per_hour",
                            value=len(recent_events),
                            service_role=role.value,
                            service_name="security_orchestrator",
                            tags={"domain": "security"}
                        )
            
        except Exception as e:
            logger.error(f"Error collecting security metrics: {e}")
    
    # === Action Execution ===
    
    async def _block_user(self, user_id: str):
        """Execute user blocking action"""
        # This would integrate with access control system
        logger.warning(f"User blocking triggered for user: {user_id}")
    
    async def _block_ip(self, source_ip: str):
        """Execute IP blocking action"""
        # This would integrate with network security system
        logger.warning(f"IP blocking triggered for IP: {source_ip}")
    
    async def _trigger_security_alert(self, action: Dict[str, Any], event: SecurityEvent):
        """Trigger security alert"""
        if self.alert_manager:
            await self.alert_manager.trigger_alert({
                "title": f"Security Policy Violation: {action['policy_id']}",
                "description": event.description,
                "service_name": event.source_service,
                "service_role": event.source_role.value,
                "severity": event.severity.value,
                "source": "security_orchestrator",
                "timestamp": event.timestamp
            })
    
    async def _escalate_security_incident(self, action: Dict[str, Any], event: SecurityEvent):
        """Escalate security incident"""
        if self.incident_responder:
            await self.incident_responder.escalate_incident({
                "event_id": event.event_id,
                "policy_id": action["policy_id"],
                "severity": event.severity.value,
                "escalation_reason": "Policy enforcement action",
                "event_details": event.details
            })
    
    async def _trigger_incident_response(self, correlation: ThreatCorrelation):
        """Trigger incident response for threat correlation"""
        if self.incident_responder:
            await self.incident_responder.handle_threat_correlation(correlation)
            self.stats["incidents_triggered"] += 1
    
    async def _send_security_metrics(self, event: SecurityEvent):
        """Send security event metrics"""
        try:
            if self.metrics_aggregator:
                await self.metrics_aggregator.collect_metric_point(
                    name="security_event",
                    value=1,
                    service_role=event.source_role.value,
                    service_name=event.source_service,
                    tags={
                        "event_type": event.event_type.value,
                        "severity": event.severity.value,
                        "domain": event.security_domain.value
                    }
                )
        except Exception as e:
            logger.error(f"Error sending security metrics: {e}")
    
    # === Event Handlers ===
    
    async def _notify_security_event_handlers(self, event: SecurityEvent):
        """Notify security event handlers"""
        for handler in self.security_event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in security event handler: {e}")
    
    async def _notify_policy_violation_handlers(self, policy: SecurityPolicy, event: SecurityEvent, actions: List[Dict[str, Any]]):
        """Notify policy violation handlers"""
        for handler in self.policy_violation_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(policy, event, actions)
                else:
                    handler(policy, event, actions)
            except Exception as e:
                logger.error(f"Error in policy violation handler: {e}")
    
    async def _notify_threat_correlation_handlers(self, correlation: ThreatCorrelation):
        """Notify threat correlation handlers"""
        for handler in self.threat_correlation_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(correlation)
                else:
                    handler(correlation)
            except Exception as e:
                logger.error(f"Error in threat correlation handler: {e}")
    
    # === Handler Management ===
    
    def add_security_event_handler(self, handler: Callable):
        """Add security event handler"""
        self.security_event_handlers.append(handler)
    
    def add_policy_violation_handler(self, handler: Callable):
        """Add policy violation handler"""
        self.policy_violation_handlers.append(handler)
    
    def add_threat_correlation_handler(self, handler: Callable):
        """Add threat correlation handler"""
        self.threat_correlation_handlers.append(handler)
    
    # === Health and Status ===
    
    def get_orchestrator_health(self) -> Dict[str, Any]:
        """Get health status of the security orchestrator"""
        return {
            "status": "running" if self._running else "stopped",
            "registered_services": len(self.registered_services),
            "active_policies": len([p for p in self.security_policies.values() if p.enabled]),
            "security_events": len(self.security_events),
            "active_correlations": len([c for c in self.event_correlations.values() if c.mitigation_status == "active"]),
            "queue_sizes": {
                "event_queue": self.event_queue.qsize(),
                "policy_enforcement_queue": self.policy_enforcement_queue.qsize(),
                "correlation_queue": self.correlation_queue.qsize()
            },
            "configuration": {
                "correlation_window_minutes": self.correlation_window_minutes,
                "threat_confidence_threshold": self.threat_confidence_threshold,
                "auto_mitigation_enabled": self.auto_mitigation_enabled
            },
            "statistics": self.stats.copy()
        }


# Global instance for platform-wide access
security_orchestrator = SecurityOrchestrator()


# Setup functions for easy integration
async def setup_default_security_policies():
    """Setup default security policies for the platform"""
    
    # Authentication security policy
    security_orchestrator.create_security_policy(
        policy_id="auth_security_policy",
        name="Authentication Security Policy",
        description="Enforce authentication security across all services",
        policy_type=PolicyType.AUTHENTICATION_POLICY,
        service_roles=[ServiceRole.SI_SERVICES, ServiceRole.APP_SERVICES, ServiceRole.HYBRID_SERVICES, ServiceRole.CORE_PLATFORM],
        security_domains=[SecurityDomain.AUTHENTICATION],
        rules=[
            {
                "rule_id": "auth_failure_threshold",
                "condition": {
                    "event_type": ["authentication_failure"],
                    "min_severity": "medium"
                },
                "action": {
                    "type": "alert",
                    "details": {"threshold": 5, "window": "5m"}
                }
            }
        ],
        enforcement_level=SecurityLevel.HIGH
    )
    
    # Threat detection policy
    security_orchestrator.create_security_policy(
        policy_id="threat_detection_policy", 
        name="Threat Detection Policy",
        description="Detect and respond to security threats",
        policy_type=PolicyType.THREAT_RESPONSE_POLICY,
        service_roles=[ServiceRole.SI_SERVICES, ServiceRole.APP_SERVICES, ServiceRole.HYBRID_SERVICES],
        security_domains=[SecurityDomain.THREAT_DETECTION, SecurityDomain.INCIDENT_RESPONSE],
        rules=[
            {
                "rule_id": "critical_threat_response",
                "condition": {
                    "event_type": ["threat_detected"],
                    "min_severity": "critical"
                },
                "action": {
                    "type": "escalate",
                    "details": {"auto_block": True}
                }
            }
        ],
        enforcement_level=SecurityLevel.CRITICAL
    )
    
    logger.info("Default security policies setup completed")


async def shutdown_security_orchestration():
    """Shutdown security orchestration"""
    await security_orchestrator.stop_security_orchestration()
    logger.info("Security orchestration shutdown completed")