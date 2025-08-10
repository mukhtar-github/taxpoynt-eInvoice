"""
Incident Responder - Core Platform Security
Comprehensive security incident response system for the TaxPoynt platform.
Provides automated incident detection, response coordination, and recovery management.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class IncidentSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    CONTAINED = "contained"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"
    CLOSED = "closed"
    FALSE_POSITIVE = "false_positive"

class IncidentCategory(Enum):
    MALWARE = "malware"
    PHISHING = "phishing"
    DDoS = "ddos"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SYSTEM_COMPROMISE = "system_compromise"
    INSIDER_THREAT = "insider_threat"
    COMPLIANCE_VIOLATION = "compliance_violation"
    AVAILABILITY_ISSUE = "availability_issue"
    INTEGRITY_VIOLATION = "integrity_violation"
    CONFIDENTIALITY_BREACH = "confidentiality_breach"
    UNKNOWN = "unknown"

class ResponseAction(Enum):
    ISOLATE = "isolate"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    MONITOR = "monitor"
    ALERT = "alert"
    ESCALATE = "escalate"
    INVESTIGATE = "investigate"
    CONTAIN = "contain"
    MITIGATE = "mitigate"
    RECOVER = "recover"
    DOCUMENT = "document"

@dataclass
class IncidentEvidence:
    id: str
    incident_id: str
    evidence_type: str
    source: str
    data: Dict[str, Any]
    hash_value: str
    collected_at: datetime = field(default_factory=datetime.utcnow)
    collected_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IncidentAction:
    id: str
    incident_id: str
    action_type: ResponseAction
    description: str
    executed_by: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IncidentTimeline:
    id: str
    incident_id: str
    timestamp: datetime
    event_type: str
    description: str
    actor: str
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityIncident:
    id: str
    title: str
    description: str
    category: IncidentCategory
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    affected_systems: List[str]
    indicators: Dict[str, Any]
    evidence: List[IncidentEvidence] = field(default_factory=list)
    actions: List[IncidentAction] = field(default_factory=list)
    timeline: List[IncidentTimeline] = field(default_factory=list)
    assignee: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResponsePlaybook:
    id: str
    name: str
    description: str
    category: IncidentCategory
    severity_threshold: IncidentSeverity
    automated_actions: List[Dict[str, Any]]
    manual_procedures: List[str]
    escalation_criteria: Dict[str, Any]
    success_criteria: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResponseHandler(ABC):
    @abstractmethod
    async def execute_action(self, action: IncidentAction, incident: SecurityIncident) -> Dict[str, Any]:
        pass

class IsolationHandler(ResponseHandler):
    async def execute_action(self, action: IncidentAction, incident: SecurityIncident) -> Dict[str, Any]:
        try:
            target = action.parameters.get('target')
            isolation_type = action.parameters.get('type', 'network')
            
            if isolation_type == 'network':
                result = await self._isolate_network(target)
            elif isolation_type == 'system':
                result = await self._isolate_system(target)
            else:
                result = {'success': False, 'error': 'Unknown isolation type'}
            
            return result
        except Exception as e:
            logger.error(f"Isolation action failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _isolate_network(self, target: str) -> Dict[str, Any]:
        # Simulate network isolation
        logger.info(f"Isolating network access for {target}")
        return {
            'success': True,
            'action': 'network_isolation',
            'target': target,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _isolate_system(self, target: str) -> Dict[str, Any]:
        # Simulate system isolation
        logger.info(f"Isolating system {target}")
        return {
            'success': True,
            'action': 'system_isolation',
            'target': target,
            'timestamp': datetime.utcnow().isoformat()
        }

class BlockingHandler(ResponseHandler):
    async def execute_action(self, action: IncidentAction, incident: SecurityIncident) -> Dict[str, Any]:
        try:
            target = action.parameters.get('target')
            block_type = action.parameters.get('type', 'ip')
            duration = action.parameters.get('duration', 3600)
            
            if block_type == 'ip':
                result = await self._block_ip(target, duration)
            elif block_type == 'domain':
                result = await self._block_domain(target, duration)
            elif block_type == 'user':
                result = await self._block_user(target, duration)
            else:
                result = {'success': False, 'error': 'Unknown block type'}
            
            return result
        except Exception as e:
            logger.error(f"Blocking action failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _block_ip(self, ip: str, duration: int) -> Dict[str, Any]:
        # Simulate IP blocking
        logger.info(f"Blocking IP {ip} for {duration} seconds")
        return {
            'success': True,
            'action': 'ip_block',
            'target': ip,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _block_domain(self, domain: str, duration: int) -> Dict[str, Any]:
        # Simulate domain blocking
        logger.info(f"Blocking domain {domain} for {duration} seconds")
        return {
            'success': True,
            'action': 'domain_block',
            'target': domain,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _block_user(self, user: str, duration: int) -> Dict[str, Any]:
        # Simulate user blocking
        logger.info(f"Blocking user {user} for {duration} seconds")
        return {
            'success': True,
            'action': 'user_block',
            'target': user,
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat()
        }

class QuarantineHandler(ResponseHandler):
    async def execute_action(self, action: IncidentAction, incident: SecurityIncident) -> Dict[str, Any]:
        try:
            target = action.parameters.get('target')
            quarantine_type = action.parameters.get('type', 'file')
            
            if quarantine_type == 'file':
                result = await self._quarantine_file(target)
            elif quarantine_type == 'process':
                result = await self._quarantine_process(target)
            elif quarantine_type == 'system':
                result = await self._quarantine_system(target)
            else:
                result = {'success': False, 'error': 'Unknown quarantine type'}
            
            return result
        except Exception as e:
            logger.error(f"Quarantine action failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _quarantine_file(self, file_path: str) -> Dict[str, Any]:
        # Simulate file quarantine
        logger.info(f"Quarantining file {file_path}")
        return {
            'success': True,
            'action': 'file_quarantine',
            'target': file_path,
            'quarantine_location': f"/quarantine/{hashlib.md5(file_path.encode()).hexdigest()}",
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _quarantine_process(self, process_id: str) -> Dict[str, Any]:
        # Simulate process quarantine
        logger.info(f"Quarantining process {process_id}")
        return {
            'success': True,
            'action': 'process_quarantine',
            'target': process_id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _quarantine_system(self, system_id: str) -> Dict[str, Any]:
        # Simulate system quarantine
        logger.info(f"Quarantining system {system_id}")
        return {
            'success': True,
            'action': 'system_quarantine',
            'target': system_id,
            'timestamp': datetime.utcnow().isoformat()
        }

class AlertHandler(ResponseHandler):
    async def execute_action(self, action: IncidentAction, incident: SecurityIncident) -> Dict[str, Any]:
        try:
            alert_type = action.parameters.get('type', 'email')
            recipients = action.parameters.get('recipients', [])
            message = action.parameters.get('message', f"Security incident: {incident.title}")
            
            if alert_type == 'email':
                result = await self._send_email_alert(recipients, message, incident)
            elif alert_type == 'sms':
                result = await self._send_sms_alert(recipients, message, incident)
            elif alert_type == 'webhook':
                result = await self._send_webhook_alert(action.parameters.get('webhook_url'), incident)
            else:
                result = {'success': False, 'error': 'Unknown alert type'}
            
            return result
        except Exception as e:
            logger.error(f"Alert action failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _send_email_alert(self, recipients: List[str], message: str, incident: SecurityIncident) -> Dict[str, Any]:
        # Simulate email alert
        logger.info(f"Sending email alert to {len(recipients)} recipients")
        return {
            'success': True,
            'action': 'email_alert',
            'recipients': recipients,
            'incident_id': incident.id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _send_sms_alert(self, recipients: List[str], message: str, incident: SecurityIncident) -> Dict[str, Any]:
        # Simulate SMS alert
        logger.info(f"Sending SMS alert to {len(recipients)} recipients")
        return {
            'success': True,
            'action': 'sms_alert',
            'recipients': recipients,
            'incident_id': incident.id,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _send_webhook_alert(self, webhook_url: str, incident: SecurityIncident) -> Dict[str, Any]:
        # Simulate webhook alert
        logger.info(f"Sending webhook alert to {webhook_url}")
        return {
            'success': True,
            'action': 'webhook_alert',
            'webhook_url': webhook_url,
            'incident_id': incident.id,
            'timestamp': datetime.utcnow().isoformat()
        }

class IncidentResponder:
    def __init__(self):
        self.incidents: Dict[str, SecurityIncident] = {}
        self.playbooks: Dict[str, ResponsePlaybook] = {}
        self.handlers: Dict[ResponseAction, ResponseHandler] = {}
        self.escalation_rules: Dict[str, Dict[str, Any]] = {}
        self.response_metrics: Dict[str, Any] = {}
        
        # Initialize handlers
        self._initialize_handlers()
        
        # Load default playbooks
        self._load_default_playbooks()
    
    def _initialize_handlers(self):
        """Initialize response handlers"""
        self.handlers = {
            ResponseAction.ISOLATE: IsolationHandler(),
            ResponseAction.BLOCK: BlockingHandler(),
            ResponseAction.QUARANTINE: QuarantineHandler(),
            ResponseAction.ALERT: AlertHandler()
        }
    
    def _load_default_playbooks(self):
        """Load default response playbooks"""
        default_playbooks = [
            ResponsePlaybook(
                id="malware_response",
                name="Malware Incident Response",
                description="Automated response to malware incidents",
                category=IncidentCategory.MALWARE,
                severity_threshold=IncidentSeverity.MEDIUM,
                automated_actions=[
                    {
                        'action': ResponseAction.QUARANTINE.value,
                        'parameters': {'type': 'file'},
                        'condition': 'malware_detected'
                    },
                    {
                        'action': ResponseAction.ISOLATE.value,
                        'parameters': {'type': 'system'},
                        'condition': 'system_infected'
                    },
                    {
                        'action': ResponseAction.ALERT.value,
                        'parameters': {'type': 'email'},
                        'condition': 'always'
                    }
                ],
                manual_procedures=[
                    "Analyze malware sample",
                    "Check for lateral movement",
                    "Update security signatures",
                    "Conduct forensic analysis"
                ],
                escalation_criteria={
                    'time_threshold': 1800,  # 30 minutes
                    'spread_threshold': 5,   # 5 or more systems
                    'severity_threshold': IncidentSeverity.HIGH.value
                },
                success_criteria=[
                    "Malware contained",
                    "Infected systems cleaned",
                    "No further propagation",
                    "Root cause identified"
                ]
            ),
            ResponsePlaybook(
                id="data_breach_response",
                name="Data Breach Response",
                description="Response to data breach incidents",
                category=IncidentCategory.DATA_BREACH,
                severity_threshold=IncidentSeverity.HIGH,
                automated_actions=[
                    {
                        'action': ResponseAction.ISOLATE.value,
                        'parameters': {'type': 'network'},
                        'condition': 'breach_confirmed'
                    },
                    {
                        'action': ResponseAction.ALERT.value,
                        'parameters': {'type': 'email', 'priority': 'urgent'},
                        'condition': 'always'
                    },
                    {
                        'action': ResponseAction.BLOCK.value,
                        'parameters': {'type': 'user'},
                        'condition': 'insider_threat_suspected'
                    }
                ],
                manual_procedures=[
                    "Assess data exposure scope",
                    "Notify regulatory authorities",
                    "Prepare breach notifications",
                    "Conduct forensic investigation",
                    "Implement containment measures"
                ],
                escalation_criteria={
                    'time_threshold': 900,   # 15 minutes
                    'data_sensitivity': 'high',
                    'record_count_threshold': 1000
                },
                success_criteria=[
                    "Breach contained",
                    "Data exposure minimized",
                    "Authorities notified",
                    "Affected parties informed"
                ]
            ),
            ResponsePlaybook(
                id="ddos_response",
                name="DDoS Attack Response",
                description="Response to distributed denial of service attacks",
                category=IncidentCategory.DDoS,
                severity_threshold=IncidentSeverity.MEDIUM,
                automated_actions=[
                    {
                        'action': ResponseAction.BLOCK.value,
                        'parameters': {'type': 'ip'},
                        'condition': 'attack_detected'
                    },
                    {
                        'action': ResponseAction.ALERT.value,
                        'parameters': {'type': 'webhook'},
                        'condition': 'always'
                    }
                ],
                manual_procedures=[
                    "Analyze attack patterns",
                    "Implement rate limiting",
                    "Contact ISP for upstream filtering",
                    "Monitor service availability"
                ],
                escalation_criteria={
                    'traffic_threshold': '10x_normal',
                    'service_impact': 'critical',
                    'duration_threshold': 300  # 5 minutes
                },
                success_criteria=[
                    "Attack traffic blocked",
                    "Service availability restored",
                    "Attack source identified"
                ]
            )
        ]
        
        for playbook in default_playbooks:
            self.playbooks[playbook.id] = playbook
    
    async def create_incident(self, incident_data: Dict[str, Any]) -> SecurityIncident:
        """Create a new security incident"""
        try:
            incident_id = f"inc_{int(time.time())}_{hashlib.md5(str(incident_data).encode()).hexdigest()[:8]}"
            
            incident = SecurityIncident(
                id=incident_id,
                title=incident_data.get('title', 'Security Incident'),
                description=incident_data.get('description', ''),
                category=IncidentCategory(incident_data.get('category', IncidentCategory.UNKNOWN.value)),
                severity=IncidentSeverity(incident_data.get('severity', IncidentSeverity.MEDIUM.value)),
                status=IncidentStatus.OPEN,
                source=incident_data.get('source', 'system'),
                affected_systems=incident_data.get('affected_systems', []),
                indicators=incident_data.get('indicators', {}),
                metadata=incident_data.get('metadata', {})
            )
            
            self.incidents[incident_id] = incident
            
            # Add to timeline
            await self._add_timeline_event(
                incident,
                "incident_created",
                f"Incident created: {incident.title}",
                "system"
            )
            
            # Trigger automated response
            await self._trigger_automated_response(incident)
            
            logger.info(f"Created security incident: {incident_id}")
            return incident
        except Exception as e:
            logger.error(f"Failed to create incident: {e}")
            return None
    
    async def _trigger_automated_response(self, incident: SecurityIncident):
        """Trigger automated response based on playbooks"""
        try:
            applicable_playbooks = [
                playbook for playbook in self.playbooks.values()
                if (playbook.category == incident.category and 
                    self._severity_meets_threshold(incident.severity, playbook.severity_threshold))
            ]
            
            for playbook in applicable_playbooks:
                await self._execute_playbook(incident, playbook)
                
            logger.info(f"Triggered automated response for incident: {incident.id}")
        except Exception as e:
            logger.error(f"Failed to trigger automated response: {e}")
    
    def _severity_meets_threshold(self, incident_severity: IncidentSeverity, threshold: IncidentSeverity) -> bool:
        """Check if incident severity meets playbook threshold"""
        severity_order = {
            IncidentSeverity.INFO: 1,
            IncidentSeverity.LOW: 2,
            IncidentSeverity.MEDIUM: 3,
            IncidentSeverity.HIGH: 4,
            IncidentSeverity.CRITICAL: 5
        }
        
        return severity_order[incident_severity] >= severity_order[threshold]
    
    async def _execute_playbook(self, incident: SecurityIncident, playbook: ResponsePlaybook):
        """Execute a response playbook"""
        try:
            for action_config in playbook.automated_actions:
                if await self._evaluate_condition(incident, action_config.get('condition', 'always')):
                    action = IncidentAction(
                        id=f"action_{int(time.time())}_{len(incident.actions)}",
                        incident_id=incident.id,
                        action_type=ResponseAction(action_config['action']),
                        description=f"Automated action from playbook: {playbook.name}",
                        executed_by="system",
                        parameters=action_config.get('parameters', {})
                    )
                    
                    await self._execute_action(incident, action)
                    
            logger.info(f"Executed playbook {playbook.id} for incident {incident.id}")
        except Exception as e:
            logger.error(f"Failed to execute playbook: {e}")
    
    async def _evaluate_condition(self, incident: SecurityIncident, condition: str) -> bool:
        """Evaluate action condition"""
        if condition == 'always':
            return True
        elif condition == 'malware_detected':
            return incident.category == IncidentCategory.MALWARE
        elif condition == 'breach_confirmed':
            return incident.category == IncidentCategory.DATA_BREACH
        elif condition == 'attack_detected':
            return incident.category == IncidentCategory.DDoS
        elif condition == 'system_infected':
            return len(incident.affected_systems) > 0
        elif condition == 'insider_threat_suspected':
            return 'insider_threat' in incident.indicators
        else:
            return False
    
    async def _execute_action(self, incident: SecurityIncident, action: IncidentAction):
        """Execute a response action"""
        try:
            action.started_at = datetime.utcnow()
            action.status = "executing"
            incident.actions.append(action)
            
            # Add to timeline
            await self._add_timeline_event(
                incident,
                "action_started",
                f"Started action: {action.action_type.value}",
                action.executed_by
            )
            
            if action.action_type in self.handlers:
                handler = self.handlers[action.action_type]
                result = await handler.execute_action(action, incident)
                
                action.result = result
                action.completed_at = datetime.utcnow()
                action.status = "completed" if result.get('success') else "failed"
                
                # Add to timeline
                await self._add_timeline_event(
                    incident,
                    "action_completed",
                    f"Completed action: {action.action_type.value} - {action.status}",
                    action.executed_by
                )
            else:
                action.status = "not_supported"
                action.completed_at = datetime.utcnow()
                
            logger.info(f"Executed action {action.id} for incident {incident.id}")
        except Exception as e:
            logger.error(f"Failed to execute action: {e}")
            action.status = "error"
            action.completed_at = datetime.utcnow()
            action.result = {'success': False, 'error': str(e)}
    
    async def _add_timeline_event(self, incident: SecurityIncident, event_type: str, description: str, actor: str):
        """Add event to incident timeline"""
        try:
            event = IncidentTimeline(
                id=f"timeline_{int(time.time())}_{len(incident.timeline)}",
                incident_id=incident.id,
                timestamp=datetime.utcnow(),
                event_type=event_type,
                description=description,
                actor=actor
            )
            
            incident.timeline.append(event)
            incident.updated_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to add timeline event: {e}")
    
    async def add_evidence(self, incident_id: str, evidence_data: Dict[str, Any]) -> IncidentEvidence:
        """Add evidence to an incident"""
        try:
            if incident_id not in self.incidents:
                return None
            
            incident = self.incidents[incident_id]
            
            evidence = IncidentEvidence(
                id=f"evidence_{int(time.time())}_{len(incident.evidence)}",
                incident_id=incident_id,
                evidence_type=evidence_data.get('type', 'unknown'),
                source=evidence_data.get('source', 'unknown'),
                data=evidence_data.get('data', {}),
                hash_value=hashlib.sha256(json.dumps(evidence_data.get('data', {}), sort_keys=True).encode()).hexdigest(),
                collected_by=evidence_data.get('collected_by', 'system'),
                metadata=evidence_data.get('metadata', {})
            )
            
            incident.evidence.append(evidence)
            
            # Add to timeline
            await self._add_timeline_event(
                incident,
                "evidence_added",
                f"Added evidence: {evidence.evidence_type}",
                evidence.collected_by
            )
            
            logger.info(f"Added evidence to incident: {incident_id}")
            return evidence
        except Exception as e:
            logger.error(f"Failed to add evidence: {e}")
            return None
    
    async def update_incident_status(self, incident_id: str, status: IncidentStatus, notes: str = "") -> bool:
        """Update incident status"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            old_status = incident.status
            incident.status = status
            incident.updated_at = datetime.utcnow()
            
            if status == IncidentStatus.RESOLVED:
                incident.resolved_at = datetime.utcnow()
            
            # Add to timeline
            await self._add_timeline_event(
                incident,
                "status_changed",
                f"Status changed from {old_status.value} to {status.value}. {notes}",
                "system"
            )
            
            # Check escalation criteria
            await self._check_escalation(incident)
            
            logger.info(f"Updated incident status: {incident_id} -> {status.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update incident status: {e}")
            return False
    
    async def _check_escalation(self, incident: SecurityIncident):
        """Check if incident should be escalated"""
        try:
            escalation_rules = self.escalation_rules.get(incident.category.value, {})
            
            # Check time-based escalation
            time_threshold = escalation_rules.get('time_threshold', 3600)
            incident_age = (datetime.utcnow() - incident.created_at).total_seconds()
            
            if incident_age > time_threshold and incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                await self._escalate_incident(incident, "time_threshold_exceeded")
            
            # Check severity escalation
            if incident.severity == IncidentSeverity.CRITICAL and incident.status == IncidentStatus.OPEN:
                await self._escalate_incident(incident, "critical_severity")
                
        except Exception as e:
            logger.error(f"Failed to check escalation: {e}")
    
    async def _escalate_incident(self, incident: SecurityIncident, reason: str):
        """Escalate an incident"""
        try:
            # Create escalation action
            action = IncidentAction(
                id=f"escalation_{int(time.time())}",
                incident_id=incident.id,
                action_type=ResponseAction.ESCALATE,
                description=f"Incident escalated: {reason}",
                executed_by="system",
                parameters={'reason': reason}
            )
            
            # Send escalation alert
            alert_action = IncidentAction(
                id=f"escalation_alert_{int(time.time())}",
                incident_id=incident.id,
                action_type=ResponseAction.ALERT,
                description="Escalation alert",
                executed_by="system",
                parameters={
                    'type': 'email',
                    'priority': 'urgent',
                    'message': f"Incident {incident.id} has been escalated: {reason}"
                }
            )
            
            await self._execute_action(incident, action)
            await self._execute_action(incident, alert_action)
            
            logger.info(f"Escalated incident {incident.id}: {reason}")
        except Exception as e:
            logger.error(f"Failed to escalate incident: {e}")
    
    async def assign_incident(self, incident_id: str, assignee: str) -> bool:
        """Assign incident to a responder"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            old_assignee = incident.assignee
            incident.assignee = assignee
            incident.updated_at = datetime.utcnow()
            
            # Add to timeline
            await self._add_timeline_event(
                incident,
                "assignment_changed",
                f"Assigned to {assignee} (previously: {old_assignee or 'unassigned'})",
                "system"
            )
            
            logger.info(f"Assigned incident {incident_id} to {assignee}")
            return True
        except Exception as e:
            logger.error(f"Failed to assign incident: {e}")
            return False
    
    def get_incident_statistics(self) -> Dict[str, Any]:
        """Get incident response statistics"""
        try:
            total_incidents = len(self.incidents)
            
            # Status distribution
            status_counts = {}
            for status in IncidentStatus:
                status_counts[status.value] = len([
                    inc for inc in self.incidents.values()
                    if inc.status == status
                ])
            
            # Severity distribution
            severity_counts = {}
            for severity in IncidentSeverity:
                severity_counts[severity.value] = len([
                    inc for inc in self.incidents.values()
                    if inc.severity == severity
                ])
            
            # Category distribution
            category_counts = {}
            for category in IncidentCategory:
                category_counts[category.value] = len([
                    inc for inc in self.incidents.values()
                    if inc.category == category
                ])
            
            # Response time metrics
            resolved_incidents = [
                inc for inc in self.incidents.values()
                if inc.status == IncidentStatus.RESOLVED and inc.resolved_at
            ]
            
            avg_response_time = 0
            if resolved_incidents:
                total_response_time = sum([
                    (inc.resolved_at - inc.created_at).total_seconds()
                    for inc in resolved_incidents
                ])
                avg_response_time = total_response_time / len(resolved_incidents)
            
            return {
                'total_incidents': total_incidents,
                'status_distribution': status_counts,
                'severity_distribution': severity_counts,
                'category_distribution': category_counts,
                'average_response_time': avg_response_time,
                'resolved_incidents': len(resolved_incidents),
                'open_incidents': len([
                    inc for inc in self.incidents.values()
                    if inc.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
                ])
            }
        except Exception as e:
            logger.error(f"Failed to get incident statistics: {e}")
            return {}
    
    async def start_monitoring(self, interval: int = 300):
        """Start continuous incident monitoring"""
        try:
            logger.info("Starting incident response monitoring")
            
            while True:
                # Check for escalations
                for incident in self.incidents.values():
                    if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                        await self._check_escalation(incident)
                
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Incident monitoring failed: {e}")

# Global incident responder instance
incident_responder = IncidentResponder()

async def initialize_incident_responder():
    """Initialize the incident responder"""
    try:
        # Set escalation rules
        incident_responder.escalation_rules = {
            'malware': {
                'time_threshold': 1800,  # 30 minutes
                'spread_threshold': 5
            },
            'data_breach': {
                'time_threshold': 900,   # 15 minutes
                'severity_threshold': 'high'
            },
            'ddos': {
                'time_threshold': 300,   # 5 minutes
                'impact_threshold': 'critical'
            }
        }
        
        logger.info("Incident responder initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize incident responder: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_incident_responder()
        
        # Example usage
        incident_data = {
            'title': 'Suspected Malware Detection',
            'description': 'Malicious file detected on user workstation',
            'category': 'malware',
            'severity': 'high',
            'source': 'antivirus_scanner',
            'affected_systems': ['workstation-001'],
            'indicators': {
                'file_hash': 'abc123def456',
                'file_path': '/tmp/malicious.exe',
                'detection_signature': 'Trojan.Generic'
            }
        }
        
        incident = await incident_responder.create_incident(incident_data)
        print(f"Created incident: {incident.id}")
        
        # Add evidence
        evidence_data = {
            'type': 'file_hash',
            'source': 'antivirus',
            'data': {
                'hash': 'abc123def456',
                'algorithm': 'SHA-256'
            }
        }
        
        evidence = await incident_responder.add_evidence(incident.id, evidence_data)
        print(f"Added evidence: {evidence.id}")
        
        # Get statistics
        stats = incident_responder.get_incident_statistics()
        print(f"Incident statistics: {stats}")
    
    asyncio.run(main())