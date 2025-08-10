"""
Hybrid Service: Incident Tracker
Tracks incidents and their resolution across roles
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

from core_platform.database import get_db_session
from core_platform.models.incidents import Incident, IncidentUpdate, IncidentResolution
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class IncidentStatus(str, Enum):
    """Incident status levels"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class IncidentSeverity(str, Enum):
    """Incident severity levels"""
    SEV1_CRITICAL = "sev1_critical"
    SEV2_HIGH = "sev2_high"
    SEV3_MEDIUM = "sev3_medium"
    SEV4_LOW = "sev4_low"
    SEV5_INFO = "sev5_info"


class IncidentPriority(str, Enum):
    """Incident priority levels"""
    P1_CRITICAL = "p1_critical"
    P2_HIGH = "p2_high"
    P3_MEDIUM = "p3_medium"
    P4_LOW = "p4_low"
    P5_DEFERRED = "p5_deferred"


class IncidentType(str, Enum):
    """Types of incidents"""
    OUTAGE = "outage"
    DEGRADATION = "degradation"
    SECURITY = "security"
    DATA_LOSS = "data_loss"
    PERFORMANCE = "performance"
    INTEGRATION_FAILURE = "integration_failure"
    SERVICE_UNAVAILABLE = "service_unavailable"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_FAILURE = "dependency_failure"
    PLANNED_MAINTENANCE = "planned_maintenance"


class IncidentImpact(str, Enum):
    """Impact levels of incidents"""
    WIDESPREAD = "widespread"
    SIGNIFICANT = "significant"
    MODERATE = "moderate"
    MINIMAL = "minimal"
    NONE = "none"


class ResolutionType(str, Enum):
    """Types of incident resolution"""
    FIXED = "fixed"
    WORKAROUND = "workaround"
    DUPLICATE = "duplicate"
    NOT_REPRODUCIBLE = "not_reproducible"
    BY_DESIGN = "by_design"
    EXTERNAL_DEPENDENCY = "external_dependency"
    PLANNED_CHANGE = "planned_change"


@dataclass
class IncidentMetrics:
    """Metrics for incident tracking"""
    incident_id: str
    detection_time: datetime
    acknowledgment_time: Optional[datetime]
    resolution_time: Optional[datetime]
    closure_time: Optional[datetime]
    mttr_minutes: Optional[float]  # Mean Time To Recovery
    mtta_minutes: Optional[float]  # Mean Time To Acknowledge
    affected_users: int
    affected_services: List[str]
    business_impact_score: float
    customer_impact: str
    escalation_count: int
    communication_count: int
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IncidentUpdate:
    """Update to an incident"""
    update_id: str
    incident_id: str
    timestamp: datetime
    author: str
    update_type: str  # status_change, investigation_update, communication, etc.
    title: str
    description: str
    status_change: Optional[Dict[str, str]]  # old_status -> new_status
    visibility: str  # internal, public, customer
    attachments: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Incident:
    """Comprehensive incident record"""
    incident_id: str
    title: str
    description: str
    incident_type: IncidentType
    severity: IncidentSeverity
    priority: IncidentPriority
    status: IncidentStatus
    impact: IncidentImpact
    affected_services: List[str]
    affected_components: List[str]
    root_cause: Optional[str]
    created_at: datetime
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    assignee: Optional[str]
    reporter: str
    related_errors: List[str]  # Error IDs
    related_escalations: List[str]  # Escalation IDs
    recovery_sessions: List[str]  # Recovery session IDs
    customer_communications: List[str]
    internal_updates: List[str]  # Update IDs
    metrics: Optional[IncidentMetrics]
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IncidentResolution:
    """Resolution details for an incident"""
    resolution_id: str
    incident_id: str
    resolution_type: ResolutionType
    resolution_summary: str
    detailed_resolution: str
    root_cause_analysis: str
    preventive_measures: List[str]
    lessons_learned: List[str]
    resolved_by: str
    verified_by: Optional[str]
    resolution_date: datetime
    verification_date: Optional[datetime]
    follow_up_actions: List[Dict[str, Any]]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IncidentTemplate:
    """Template for creating incidents"""
    template_id: str
    name: str
    description: str
    incident_type: IncidentType
    default_severity: IncidentSeverity
    default_priority: IncidentPriority
    affected_services: List[str]
    response_procedures: List[str]
    communication_templates: List[str]
    escalation_criteria: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IncidentTracker:
    """
    Incident Tracker service
    Tracks incidents and their resolution across roles
    """
    
    def __init__(self):
        """Initialize incident tracker service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.incidents: Dict[str, Incident] = {}
        self.incident_updates: Dict[str, IncidentUpdate] = {}
        self.incident_resolutions: Dict[str, IncidentResolution] = {}
        self.incident_templates: Dict[str, IncidentTemplate] = {}
        self.incident_metrics: Dict[str, IncidentMetrics] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 86400  # 24 hours
        self.sla_acknowledgment_minutes = 15
        self.sla_resolution_hours = {"sev1": 4, "sev2": 8, "sev3": 24, "sev4": 72}
        self.auto_close_resolved_days = 7
        self.incident_retention_days = 365
        
        # Initialize default templates
        self._initialize_incident_templates()
    
    def _initialize_incident_templates(self):
        """Initialize default incident templates"""
        default_templates = [
            # Service outage template
            IncidentTemplate(
                template_id="service_outage_template",
                name="Service Outage",
                description="Template for service outage incidents",
                incident_type=IncidentType.OUTAGE,
                default_severity=IncidentSeverity.SEV1_CRITICAL,
                default_priority=IncidentPriority.P1_CRITICAL,
                affected_services=["*"],
                response_procedures=[
                    "immediate_escalation",
                    "customer_notification",
                    "status_page_update",
                    "technical_investigation"
                ],
                communication_templates=[
                    "outage_initial_notification",
                    "outage_progress_update",
                    "outage_resolution_notification"
                ],
                escalation_criteria={
                    "immediate_escalation": True,
                    "escalation_levels": ["l3_senior_engineer", "l4_manager", "l5_director"]
                }
            ),
            
            # Performance degradation template
            IncidentTemplate(
                template_id="performance_degradation_template",
                name="Performance Degradation",
                description="Template for performance degradation incidents",
                incident_type=IncidentType.DEGRADATION,
                default_severity=IncidentSeverity.SEV2_HIGH,
                default_priority=IncidentPriority.P2_HIGH,
                affected_services=["api_services"],
                response_procedures=[
                    "performance_analysis",
                    "capacity_check",
                    "optimization_deployment"
                ],
                communication_templates=[
                    "degradation_notification",
                    "performance_update"
                ],
                escalation_criteria={
                    "escalation_threshold_minutes": 30,
                    "escalation_levels": ["l2_team_lead", "l3_senior_engineer"]
                }
            ),
            
            # Security incident template
            IncidentTemplate(
                template_id="security_incident_template",
                name="Security Incident",
                description="Template for security-related incidents",
                incident_type=IncidentType.SECURITY,
                default_severity=IncidentSeverity.SEV1_CRITICAL,
                default_priority=IncidentPriority.P1_CRITICAL,
                affected_services=["authentication", "authorization"],
                response_procedures=[
                    "security_assessment",
                    "threat_containment",
                    "forensic_analysis",
                    "security_notification"
                ],
                communication_templates=[
                    "security_breach_notification",
                    "security_update",
                    "security_resolution"
                ],
                escalation_criteria={
                    "immediate_escalation": True,
                    "escalation_levels": ["security_team", "l4_manager", "l5_director", "legal_team"]
                }
            ),
            
            # Integration failure template
            IncidentTemplate(
                template_id="integration_failure_template",
                name="Integration Failure",
                description="Template for external integration failures",
                incident_type=IncidentType.INTEGRATION_FAILURE,
                default_severity=IncidentSeverity.SEV3_MEDIUM,
                default_priority=IncidentPriority.P3_MEDIUM,
                affected_services=["firs_integration", "external_apis"],
                response_procedures=[
                    "integration_health_check",
                    "fallback_activation",
                    "vendor_communication"
                ],
                communication_templates=[
                    "integration_failure_notification",
                    "integration_recovery_update"
                ],
                escalation_criteria={
                    "escalation_threshold_minutes": 60,
                    "escalation_levels": ["integration_team", "l3_senior_engineer"]
                }
            ),
            
            # Data inconsistency template
            IncidentTemplate(
                template_id="data_inconsistency_template",
                name="Data Inconsistency",
                description="Template for data inconsistency incidents",
                incident_type=IncidentType.DATA_LOSS,
                default_severity=IncidentSeverity.SEV2_HIGH,
                default_priority=IncidentPriority.P2_HIGH,
                affected_services=["database", "sync_services"],
                response_procedures=[
                    "data_integrity_check",
                    "inconsistency_analysis",
                    "data_repair",
                    "sync_verification"
                ],
                communication_templates=[
                    "data_inconsistency_notification",
                    "data_repair_update"
                ],
                escalation_criteria={
                    "escalation_threshold_minutes": 30,
                    "escalation_levels": ["data_team", "l3_senior_engineer", "l4_manager"]
                }
            )
        ]
        
        for template in default_templates:
            self.incident_templates[template.template_id] = template
    
    async def initialize(self):
        """Initialize the incident tracker service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing incident tracker service")
        
        try:
            # Initialize dependencies
            await self.cache.initialize()
            await self.event_bus.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._incident_monitor())
            asyncio.create_task(self._sla_monitor())
            asyncio.create_task(self._auto_closer())
            asyncio.create_task(self._cleanup_old_incidents())
            
            self.is_initialized = True
            self.logger.info("Incident tracker service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing incident tracker service: {str(e)}")
            raise
    
    async def create_incident(
        self,
        title: str,
        description: str,
        incident_type: IncidentType,
        severity: IncidentSeverity,
        reporter: str,
        affected_services: List[str] = None,
        template_id: str = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Create a new incident"""
        try:
            # Use template if provided
            template = None
            if template_id and template_id in self.incident_templates:
                template = self.incident_templates[template_id]
            
            # Determine priority based on severity
            priority = self._determine_priority(severity)
            
            # Determine impact
            impact = self._determine_impact(affected_services, severity)
            
            # Create incident
            incident = Incident(
                incident_id=str(uuid.uuid4()),
                title=title,
                description=description,
                incident_type=incident_type,
                severity=severity,
                priority=priority,
                status=IncidentStatus.OPEN,
                impact=impact,
                affected_services=affected_services or [],
                affected_components=await self._identify_affected_components(affected_services),
                root_cause=None,
                created_at=datetime.now(timezone.utc),
                detected_at=datetime.now(timezone.utc),
                acknowledged_at=None,
                resolved_at=None,
                closed_at=None,
                assignee=None,
                reporter=reporter,
                related_errors=[],
                related_escalations=[],
                recovery_sessions=[],
                customer_communications=[],
                internal_updates=[],
                metrics=None,
                tags=template.metadata.get("tags", []) if template else [],
                metadata={
                    "template_id": template_id,
                    "context": context or {},
                    "auto_created": context.get("auto_created", False) if context else False
                }
            )
            
            # Store incident
            self.incidents[incident.incident_id] = incident
            
            # Cache incident
            await self.cache.set(
                f"incident:{incident.incident_id}",
                incident.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Create initial metrics
            metrics = IncidentMetrics(
                incident_id=incident.incident_id,
                detection_time=incident.detected_at,
                acknowledgment_time=None,
                resolution_time=None,
                closure_time=None,
                mttr_minutes=None,
                mtta_minutes=None,
                affected_users=await self._estimate_affected_users(affected_services),
                affected_services=affected_services or [],
                business_impact_score=self._calculate_business_impact_score(severity, impact),
                customer_impact=self._assess_customer_impact(affected_services, severity),
                escalation_count=0,
                communication_count=0
            )
            
            self.incident_metrics[incident.incident_id] = metrics
            incident.metrics = metrics
            
            # Add initial update
            initial_update = IncidentUpdate(
                update_id=str(uuid.uuid4()),
                incident_id=incident.incident_id,
                timestamp=incident.created_at,
                author=reporter,
                update_type="incident_created",
                title="Incident Created",
                description=f"Incident created: {title}",
                status_change=None,
                visibility="internal",
                metadata={"initial_update": True}
            )
            
            self.incident_updates[initial_update.update_id] = initial_update
            incident.internal_updates.append(initial_update.update_id)
            
            # Emit incident created event
            await self.event_bus.emit(
                "incident.created",
                {
                    "incident_id": incident.incident_id,
                    "severity": severity,
                    "incident_type": incident_type,
                    "affected_services": affected_services,
                    "reporter": reporter
                }
            )
            
            # Auto-assign if template specifies
            if template and template.escalation_criteria.get("immediate_escalation"):
                await self._auto_escalate_incident(incident)
            
            self.logger.info(f"Incident created: {incident.incident_id} - {title}")
            
            return incident.incident_id
            
        except Exception as e:
            self.logger.error(f"Error creating incident: {str(e)}")
            return ""
    
    def _determine_priority(self, severity: IncidentSeverity) -> IncidentPriority:
        """Determine priority based on severity"""
        mapping = {
            IncidentSeverity.SEV1_CRITICAL: IncidentPriority.P1_CRITICAL,
            IncidentSeverity.SEV2_HIGH: IncidentPriority.P2_HIGH,
            IncidentSeverity.SEV3_MEDIUM: IncidentPriority.P3_MEDIUM,
            IncidentSeverity.SEV4_LOW: IncidentPriority.P4_LOW,
            IncidentSeverity.SEV5_INFO: IncidentPriority.P5_DEFERRED
        }
        return mapping.get(severity, IncidentPriority.P3_MEDIUM)
    
    def _determine_impact(self, affected_services: List[str], severity: IncidentSeverity) -> IncidentImpact:
        """Determine impact based on affected services and severity"""
        try:
            if not affected_services:
                return IncidentImpact.MINIMAL
            
            # Critical services
            critical_services = ["invoice_service", "payment_service", "firs_transmission", "authentication"]
            
            critical_affected = any(
                any(critical in service for critical in critical_services)
                for service in affected_services
            )
            
            if critical_affected:
                if severity in [IncidentSeverity.SEV1_CRITICAL, IncidentSeverity.SEV2_HIGH]:
                    return IncidentImpact.WIDESPREAD
                else:
                    return IncidentImpact.SIGNIFICANT
            
            if len(affected_services) > 3:
                return IncidentImpact.SIGNIFICANT
            elif len(affected_services) > 1:
                return IncidentImpact.MODERATE
            else:
                return IncidentImpact.MINIMAL
                
        except Exception as e:
            self.logger.error(f"Error determining impact: {str(e)}")
            return IncidentImpact.MODERATE
    
    async def _identify_affected_components(self, affected_services: List[str]) -> List[str]:
        """Identify affected components based on services"""
        try:
            components = []
            
            if not affected_services:
                return components
            
            # Map services to components
            service_component_map = {
                "invoice_service": ["invoice_engine", "pdf_generator", "validation_service"],
                "payment_service": ["payment_processor", "transaction_manager", "payment_gateway"],
                "firs_transmission": ["firs_client", "encryption_service", "transmission_queue"],
                "authentication": ["auth_service", "token_service", "user_management"],
                "database": ["postgresql", "redis", "cache_layer"],
                "api_gateway": ["routing", "rate_limiting", "load_balancer"]
            }
            
            for service in affected_services:
                if service in service_component_map:
                    components.extend(service_component_map[service])
                else:
                    # Generic component mapping
                    components.append(f"{service}_component")
            
            return list(set(components))  # Remove duplicates
            
        except Exception as e:
            self.logger.error(f"Error identifying affected components: {str(e)}")
            return []
    
    async def _estimate_affected_users(self, affected_services: List[str]) -> int:
        """Estimate number of affected users"""
        try:
            if not affected_services:
                return 0
            
            # Service user impact estimates
            service_user_impact = {
                "invoice_service": 1000,
                "payment_service": 800,
                "authentication": 2000,
                "api_gateway": 2000,
                "firs_transmission": 500
            }
            
            max_impact = 0
            for service in affected_services:
                impact = service_user_impact.get(service, 100)
                max_impact = max(max_impact, impact)
            
            return max_impact
            
        except Exception as e:
            self.logger.error(f"Error estimating affected users: {str(e)}")
            return 0
    
    def _calculate_business_impact_score(self, severity: IncidentSeverity, impact: IncidentImpact) -> float:
        """Calculate business impact score (0-100)"""
        try:
            severity_scores = {
                IncidentSeverity.SEV1_CRITICAL: 100,
                IncidentSeverity.SEV2_HIGH: 75,
                IncidentSeverity.SEV3_MEDIUM: 50,
                IncidentSeverity.SEV4_LOW: 25,
                IncidentSeverity.SEV5_INFO: 10
            }
            
            impact_multipliers = {
                IncidentImpact.WIDESPREAD: 1.0,
                IncidentImpact.SIGNIFICANT: 0.8,
                IncidentImpact.MODERATE: 0.6,
                IncidentImpact.MINIMAL: 0.4,
                IncidentImpact.NONE: 0.1
            }
            
            base_score = severity_scores.get(severity, 50)
            multiplier = impact_multipliers.get(impact, 0.5)
            
            return base_score * multiplier
            
        except Exception as e:
            self.logger.error(f"Error calculating business impact score: {str(e)}")
            return 50.0
    
    def _assess_customer_impact(self, affected_services: List[str], severity: IncidentSeverity) -> str:
        """Assess customer impact level"""
        try:
            customer_facing_services = [
                "invoice_service", "payment_service", "api_gateway", "authentication"
            ]
            
            has_customer_impact = any(
                any(cf_service in service for cf_service in customer_facing_services)
                for service in affected_services or []
            )
            
            if not has_customer_impact:
                return "none"
            
            if severity in [IncidentSeverity.SEV1_CRITICAL, IncidentSeverity.SEV2_HIGH]:
                return "high"
            elif severity == IncidentSeverity.SEV3_MEDIUM:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            self.logger.error(f"Error assessing customer impact: {str(e)}")
            return "unknown"
    
    async def update_incident(
        self,
        incident_id: str,
        title: str,
        description: str,
        author: str,
        update_type: str = "investigation_update",
        status_change: Dict[str, str] = None,
        visibility: str = "internal"
    ) -> str:
        """Add an update to an incident"""
        try:
            if incident_id not in self.incidents:
                raise ValueError(f"Incident not found: {incident_id}")
            
            incident = self.incidents[incident_id]
            
            # Create update
            update = IncidentUpdate(
                update_id=str(uuid.uuid4()),
                incident_id=incident_id,
                timestamp=datetime.now(timezone.utc),
                author=author,
                update_type=update_type,
                title=title,
                description=description,
                status_change=status_change,
                visibility=visibility,
                metadata={"update_sequence": len(incident.internal_updates) + 1}
            )
            
            # Store update
            self.incident_updates[update.update_id] = update
            
            # Add to incident
            if visibility == "internal":
                incident.internal_updates.append(update.update_id)
            else:
                incident.customer_communications.append(update.update_id)
            
            # Handle status change
            if status_change:
                old_status = status_change.get("old_status")
                new_status = status_change.get("new_status")
                
                if new_status:
                    incident.status = IncidentStatus(new_status)
                    
                    # Update metrics based on status change
                    await self._update_incident_metrics(incident, new_status)
            
            # Cache update
            await self.cache.set(
                f"incident_update:{update.update_id}",
                update.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Update incident cache
            await self.cache.set(
                f"incident:{incident_id}",
                incident.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit update event
            await self.event_bus.emit(
                "incident.updated",
                {
                    "incident_id": incident_id,
                    "update_id": update.update_id,
                    "update_type": update_type,
                    "status_change": status_change,
                    "visibility": visibility
                }
            )
            
            self.logger.info(f"Incident updated: {incident_id} - {title}")
            
            return update.update_id
            
        except Exception as e:
            self.logger.error(f"Error updating incident: {str(e)}")
            return ""
    
    async def _update_incident_metrics(self, incident: Incident, new_status: str):
        """Update incident metrics based on status change"""
        try:
            if incident.incident_id not in self.incident_metrics:
                return
            
            metrics = self.incident_metrics[incident.incident_id]
            current_time = datetime.now(timezone.utc)
            
            if new_status == IncidentStatus.INVESTIGATING.value and not metrics.acknowledgment_time:
                metrics.acknowledgment_time = current_time
                
                # Calculate MTTA (Mean Time To Acknowledge)
                metrics.mtta_minutes = (current_time - metrics.detection_time).total_seconds() / 60
                
            elif new_status == IncidentStatus.RESOLVED.value and not metrics.resolution_time:
                metrics.resolution_time = current_time
                incident.resolved_at = current_time
                
                # Calculate MTTR (Mean Time To Recovery)
                metrics.mttr_minutes = (current_time - metrics.detection_time).total_seconds() / 60
                
            elif new_status == IncidentStatus.CLOSED.value and not metrics.closure_time:
                metrics.closure_time = current_time
                incident.closed_at = current_time
            
        except Exception as e:
            self.logger.error(f"Error updating incident metrics: {str(e)}")
    
    async def resolve_incident(
        self,
        incident_id: str,
        resolution_type: ResolutionType,
        resolution_summary: str,
        detailed_resolution: str,
        root_cause_analysis: str,
        resolved_by: str,
        preventive_measures: List[str] = None,
        lessons_learned: List[str] = None
    ) -> str:
        """Resolve an incident with detailed resolution information"""
        try:
            if incident_id not in self.incidents:
                raise ValueError(f"Incident not found: {incident_id}")
            
            incident = self.incidents[incident_id]
            
            # Create resolution record
            resolution = IncidentResolution(
                resolution_id=str(uuid.uuid4()),
                incident_id=incident_id,
                resolution_type=resolution_type,
                resolution_summary=resolution_summary,
                detailed_resolution=detailed_resolution,
                root_cause_analysis=root_cause_analysis,
                preventive_measures=preventive_measures or [],
                lessons_learned=lessons_learned or [],
                resolved_by=resolved_by,
                verified_by=None,
                resolution_date=datetime.now(timezone.utc),
                verification_date=None,
                follow_up_actions=[]
            )
            
            # Store resolution
            self.incident_resolutions[resolution.resolution_id] = resolution
            
            # Update incident
            incident.status = IncidentStatus.RESOLVED
            incident.resolved_at = resolution.resolution_date
            incident.root_cause = root_cause_analysis
            
            # Update metrics
            await self._update_incident_metrics(incident, IncidentStatus.RESOLVED.value)
            
            # Add resolution update
            await self.update_incident(
                incident_id=incident_id,
                title="Incident Resolved",
                description=resolution_summary,
                author=resolved_by,
                update_type="resolution",
                status_change={
                    "old_status": "investigating",
                    "new_status": "resolved"
                },
                visibility="public"
            )
            
            # Cache resolution
            await self.cache.set(
                f"incident_resolution:{resolution.resolution_id}",
                resolution.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Emit resolution event
            await self.event_bus.emit(
                "incident.resolved",
                {
                    "incident_id": incident_id,
                    "resolution_id": resolution.resolution_id,
                    "resolution_type": resolution_type,
                    "resolved_by": resolved_by,
                    "mttr_minutes": incident.metrics.mttr_minutes if incident.metrics else None
                }
            )
            
            self.logger.info(f"Incident resolved: {incident_id} by {resolved_by}")
            
            return resolution.resolution_id
            
        except Exception as e:
            self.logger.error(f"Error resolving incident: {str(e)}")
            return ""
    
    async def close_incident(
        self,
        incident_id: str,
        closed_by: str,
        closure_notes: str = None
    ) -> bool:
        """Close a resolved incident"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            
            if incident.status != IncidentStatus.RESOLVED:
                raise ValueError(f"Cannot close incident that is not resolved: {incident.status}")
            
            # Update incident
            incident.status = IncidentStatus.CLOSED
            incident.closed_at = datetime.now(timezone.utc)
            
            # Update metrics
            await self._update_incident_metrics(incident, IncidentStatus.CLOSED.value)
            
            # Add closure update
            await self.update_incident(
                incident_id=incident_id,
                title="Incident Closed",
                description=closure_notes or "Incident has been closed after verification.",
                author=closed_by,
                update_type="closure",
                status_change={
                    "old_status": "resolved",
                    "new_status": "closed"
                }
            )
            
            # Emit closure event
            await self.event_bus.emit(
                "incident.closed",
                {
                    "incident_id": incident_id,
                    "closed_by": closed_by,
                    "total_duration_minutes": incident.metrics.mttr_minutes if incident.metrics else None
                }
            )
            
            self.logger.info(f"Incident closed: {incident_id} by {closed_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error closing incident: {str(e)}")
            return False
    
    async def link_error_to_incident(self, incident_id: str, error_id: str) -> bool:
        """Link an error to an incident"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            
            if error_id not in incident.related_errors:
                incident.related_errors.append(error_id)
                
                # Update cache
                await self.cache.set(
                    f"incident:{incident_id}",
                    incident.to_dict(),
                    ttl=self.cache_ttl
                )
                
                # Emit linking event
                await self.event_bus.emit(
                    "incident.error_linked",
                    {
                        "incident_id": incident_id,
                        "error_id": error_id
                    }
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking error to incident: {str(e)}")
            return False
    
    async def link_escalation_to_incident(self, incident_id: str, escalation_id: str) -> bool:
        """Link an escalation to an incident"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            
            if escalation_id not in incident.related_escalations:
                incident.related_escalations.append(escalation_id)
                
                # Update escalation count in metrics
                if incident.incident_id in self.incident_metrics:
                    self.incident_metrics[incident.incident_id].escalation_count += 1
                
                # Update cache
                await self.cache.set(
                    f"incident:{incident_id}",
                    incident.to_dict(),
                    ttl=self.cache_ttl
                )
                
                # Emit linking event
                await self.event_bus.emit(
                    "incident.escalation_linked",
                    {
                        "incident_id": incident_id,
                        "escalation_id": escalation_id
                    }
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking escalation to incident: {str(e)}")
            return False
    
    async def link_recovery_to_incident(self, incident_id: str, recovery_session_id: str) -> bool:
        """Link a recovery session to an incident"""
        try:
            if incident_id not in self.incidents:
                return False
            
            incident = self.incidents[incident_id]
            
            if recovery_session_id not in incident.recovery_sessions:
                incident.recovery_sessions.append(recovery_session_id)
                
                # Update cache
                await self.cache.set(
                    f"incident:{incident_id}",
                    incident.to_dict(),
                    ttl=self.cache_ttl
                )
                
                # Emit linking event
                await self.event_bus.emit(
                    "incident.recovery_linked",
                    {
                        "incident_id": incident_id,
                        "recovery_session_id": recovery_session_id
                    }
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error linking recovery to incident: {str(e)}")
            return False
    
    async def get_incident_details(self, incident_id: str) -> Dict[str, Any]:
        """Get detailed information about an incident"""
        try:
            if incident_id not in self.incidents:
                return {"status": "not_found"}
            
            incident = self.incidents[incident_id]
            
            # Get related updates
            updates = []
            for update_id in incident.internal_updates + incident.customer_communications:
                if update_id in self.incident_updates:
                    updates.append(self.incident_updates[update_id].to_dict())
            
            # Sort updates by timestamp
            updates.sort(key=lambda x: x["timestamp"])
            
            # Get resolution if available
            resolution = None
            for res in self.incident_resolutions.values():
                if res.incident_id == incident_id:
                    resolution = res.to_dict()
                    break
            
            # Calculate current duration
            current_time = datetime.now(timezone.utc)
            total_duration_minutes = (current_time - incident.created_at).total_seconds() / 60
            
            # Check SLA status
            sla_status = await self._check_sla_status(incident)
            
            return {
                "incident": incident.to_dict(),
                "updates": updates,
                "resolution": resolution,
                "metrics": incident.metrics.to_dict() if incident.metrics else None,
                "sla_status": sla_status,
                "total_duration_minutes": total_duration_minutes,
                "update_count": len(updates),
                "related_items": {
                    "errors": len(incident.related_errors),
                    "escalations": len(incident.related_escalations),
                    "recovery_sessions": len(incident.recovery_sessions)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting incident details: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def _check_sla_status(self, incident: Incident) -> Dict[str, Any]:
        """Check SLA compliance for incident"""
        try:
            current_time = datetime.now(timezone.utc)
            sla_status = {
                "acknowledgment_sla": "met",
                "resolution_sla": "on_track",
                "acknowledgment_remaining_minutes": 0,
                "resolution_remaining_hours": 0
            }
            
            # Check acknowledgment SLA
            if not incident.acknowledged_at:
                time_since_detection = (current_time - incident.detected_at).total_seconds() / 60
                if time_since_detection > self.sla_acknowledgment_minutes:
                    sla_status["acknowledgment_sla"] = "breached"
                else:
                    sla_status["acknowledgment_remaining_minutes"] = self.sla_acknowledgment_minutes - time_since_detection
            
            # Check resolution SLA
            if incident.status != IncidentStatus.RESOLVED:
                severity_key = incident.severity.value.split("_")[0].lower()  # sev1, sev2, etc.
                resolution_sla_hours = self.sla_resolution_hours.get(severity_key, 24)
                
                time_since_detection_hours = (current_time - incident.detected_at).total_seconds() / 3600
                
                if time_since_detection_hours > resolution_sla_hours:
                    sla_status["resolution_sla"] = "breached"
                elif time_since_detection_hours > (resolution_sla_hours * 0.8):
                    sla_status["resolution_sla"] = "at_risk"
                else:
                    sla_status["resolution_remaining_hours"] = resolution_sla_hours - time_since_detection_hours
            
            return sla_status
            
        except Exception as e:
            self.logger.error(f"Error checking SLA status: {str(e)}")
            return {}
    
    async def get_incidents_summary(
        self,
        time_range_hours: int = 24,
        severity: IncidentSeverity = None,
        status: IncidentStatus = None
    ) -> Dict[str, Any]:
        """Get summary of incidents"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)
            recent_incidents = [
                i for i in self.incidents.values()
                if i.created_at >= cutoff_time
            ]
            
            # Apply filters
            if severity:
                recent_incidents = [i for i in recent_incidents if i.severity == severity]
            
            if status:
                recent_incidents = [i for i in recent_incidents if i.status == status]
            
            # Calculate statistics
            total_incidents = len(recent_incidents)
            open_incidents = len([i for i in recent_incidents if i.status != IncidentStatus.CLOSED])
            resolved_incidents = len([i for i in recent_incidents if i.status == IncidentStatus.RESOLVED])
            closed_incidents = len([i for i in recent_incidents if i.status == IncidentStatus.CLOSED])
            
            # Severity distribution
            severity_distribution = {}
            for sev in IncidentSeverity:
                severity_distribution[sev.value] = len([i for i in recent_incidents if i.severity == sev])
            
            # Type distribution
            type_distribution = {}
            for inc_type in IncidentType:
                type_distribution[inc_type.value] = len([i for i in recent_incidents if i.incident_type == inc_type])
            
            # Calculate MTTR for resolved incidents
            resolved_with_metrics = [
                i for i in recent_incidents
                if i.status == IncidentStatus.RESOLVED and i.metrics and i.metrics.mttr_minutes
            ]
            
            avg_mttr_minutes = 0
            if resolved_with_metrics:
                mttr_values = [i.metrics.mttr_minutes for i in resolved_with_metrics]
                avg_mttr_minutes = statistics.mean(mttr_values)
            
            # Calculate MTTA for acknowledged incidents
            acknowledged_with_metrics = [
                i for i in recent_incidents
                if i.acknowledged_at and i.metrics and i.metrics.mtta_minutes
            ]
            
            avg_mtta_minutes = 0
            if acknowledged_with_metrics:
                mtta_values = [i.metrics.mtta_minutes for i in acknowledged_with_metrics]
                avg_mtta_minutes = statistics.mean(mtta_values)
            
            # SLA compliance
            sla_breaches = len([
                i for i in recent_incidents
                if await self._is_sla_breached(i)
            ])
            
            return {
                "time_range_hours": time_range_hours,
                "total_incidents": total_incidents,
                "open_incidents": open_incidents,
                "resolved_incidents": resolved_incidents,
                "closed_incidents": closed_incidents,
                "severity_distribution": severity_distribution,
                "type_distribution": type_distribution,
                "avg_mttr_minutes": avg_mttr_minutes,
                "avg_mtta_minutes": avg_mtta_minutes,
                "sla_compliance_rate": ((total_incidents - sla_breaches) / total_incidents) * 100 if total_incidents > 0 else 100,
                "sla_breaches": sla_breaches,
                "templates_available": len(self.incident_templates)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting incidents summary: {str(e)}")
            return {}
    
    async def _is_sla_breached(self, incident: Incident) -> bool:
        """Check if incident has SLA breach"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Check acknowledgment SLA
            if not incident.acknowledged_at:
                time_since_detection = (current_time - incident.detected_at).total_seconds() / 60
                if time_since_detection > self.sla_acknowledgment_minutes:
                    return True
            
            # Check resolution SLA
            if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                severity_key = incident.severity.value.split("_")[0].lower()
                resolution_sla_hours = self.sla_resolution_hours.get(severity_key, 24)
                
                time_since_detection_hours = (current_time - incident.detected_at).total_seconds() / 3600
                if time_since_detection_hours > resolution_sla_hours:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking SLA breach: {str(e)}")
            return False
    
    async def _auto_escalate_incident(self, incident: Incident):
        """Auto-escalate incident based on template criteria"""
        try:
            template_id = incident.metadata.get("template_id")
            if not template_id or template_id not in self.incident_templates:
                return
            
            template = self.incident_templates[template_id]
            escalation_criteria = template.escalation_criteria
            
            if escalation_criteria.get("immediate_escalation"):
                # Emit escalation event
                await self.event_bus.emit(
                    "incident.auto_escalation",
                    {
                        "incident_id": incident.incident_id,
                        "escalation_levels": escalation_criteria.get("escalation_levels", []),
                        "severity": incident.severity,
                        "incident_type": incident.incident_type
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error auto-escalating incident: {str(e)}")
    
    async def _incident_monitor(self):
        """Background incident monitoring task"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                current_time = datetime.now(timezone.utc)
                
                # Check for incidents approaching SLA breach
                for incident in self.incidents.values():
                    if incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]:
                        sla_status = await self._check_sla_status(incident)
                        
                        if sla_status.get("resolution_sla") == "at_risk":
                            await self.event_bus.emit(
                                "incident.sla_at_risk",
                                {
                                    "incident_id": incident.incident_id,
                                    "severity": incident.severity,
                                    "remaining_hours": sla_status.get("resolution_remaining_hours", 0)
                                }
                            )
                
            except Exception as e:
                self.logger.error(f"Error in incident monitor: {str(e)}")
    
    async def _sla_monitor(self):
        """Background SLA monitoring task"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                
                # Monitor SLA compliance and emit alerts
                for incident in self.incidents.values():
                    if await self._is_sla_breached(incident):
                        await self.event_bus.emit(
                            "incident.sla_breached",
                            {
                                "incident_id": incident.incident_id,
                                "severity": incident.severity,
                                "breach_type": "resolution" if incident.resolved_at else "acknowledgment"
                            }
                        )
                
            except Exception as e:
                self.logger.error(f"Error in SLA monitor: {str(e)}")
    
    async def _auto_closer(self):
        """Background task to auto-close resolved incidents"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.auto_close_resolved_days)
                
                # Find resolved incidents older than threshold
                old_resolved = [
                    i for i in self.incidents.values()
                    if i.status == IncidentStatus.RESOLVED and i.resolved_at and i.resolved_at < cutoff_time
                ]
                
                for incident in old_resolved:
                    await self.close_incident(
                        incident.incident_id,
                        "auto_closer",
                        "Auto-closed after verification period"
                    )
                
                self.logger.info(f"Auto-closed {len(old_resolved)} resolved incidents")
                
            except Exception as e:
                self.logger.error(f"Error in auto closer: {str(e)}")
    
    async def _cleanup_old_incidents(self):
        """Cleanup old incident records"""
        while True:
            try:
                await asyncio.sleep(86400)  # Daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.incident_retention_days)
                
                # Archive old closed incidents
                old_incidents = [
                    i_id for i_id, i in self.incidents.items()
                    if i.status == IncidentStatus.CLOSED and i.closed_at and i.closed_at < cutoff_time
                ]
                
                for incident_id in old_incidents:
                    # In production, these would be archived to long-term storage
                    del self.incidents[incident_id]
                    if incident_id in self.incident_metrics:
                        del self.incident_metrics[incident_id]
                
                self.logger.info(f"Archived {len(old_incidents)} old incidents")
                
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
                "recovery.execution_completed",
                self._handle_recovery_completed
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_error_occurred(self, event_data: Dict[str, Any]):
        """Handle error occurred event"""
        try:
            error_id = event_data.get("error_id")
            error_type = event_data.get("error_type")
            severity = event_data.get("severity")
            
            # Check if we should create an incident for this error
            if severity in ["critical", "high"] and error_type in ["system", "database", "integration"]:
                # Check if there's already an open incident for this service
                service_name = event_data.get("context", {}).get("service_name", "unknown")
                existing_incident = await self._find_open_incident_for_service(service_name)
                
                if existing_incident:
                    # Link error to existing incident
                    await self.link_error_to_incident(existing_incident, error_id)
                else:
                    # Create new incident
                    incident_id = await self.create_incident(
                        title=f"{error_type.title()} Error in {service_name}",
                        description=f"Incident created for {severity} {error_type} error",
                        incident_type=IncidentType.OUTAGE if severity == "critical" else IncidentType.DEGRADATION,
                        severity=IncidentSeverity.SEV1_CRITICAL if severity == "critical" else IncidentSeverity.SEV2_HIGH,
                        reporter="error_coordinator",
                        affected_services=[service_name],
                        context={"auto_created": True, "source_error_id": error_id}
                    )
                    
                    if incident_id:
                        await self.link_error_to_incident(incident_id, error_id)
            
        except Exception as e:
            self.logger.error(f"Error handling error occurred: {str(e)}")
    
    async def _find_open_incident_for_service(self, service_name: str) -> Optional[str]:
        """Find open incident for a service"""
        try:
            for incident in self.incidents.values():
                if (incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED] and
                    service_name in incident.affected_services):
                    return incident.incident_id
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding open incident for service: {str(e)}")
            return None
    
    async def _handle_escalation_created(self, event_data: Dict[str, Any]):
        """Handle escalation created event"""
        try:
            escalation_id = event_data.get("escalation_id")
            error_id = event_data.get("error_id")
            
            # Find incident related to this error
            for incident in self.incidents.values():
                if error_id in incident.related_errors:
                    await self.link_escalation_to_incident(incident.incident_id, escalation_id)
                    break
            
        except Exception as e:
            self.logger.error(f"Error handling escalation created: {str(e)}")
    
    async def _handle_recovery_completed(self, event_data: Dict[str, Any]):
        """Handle recovery completion event"""
        try:
            session_id = event_data.get("session_id")
            success = event_data.get("success", False)
            
            # Find incident related to this recovery session
            for incident in self.incidents.values():
                if session_id in incident.recovery_sessions:
                    if success and incident.status != IncidentStatus.RESOLVED:
                        # Recovery successful - add update
                        await self.update_incident(
                            incident_id=incident.incident_id,
                            title="Recovery Completed Successfully",
                            description="Automated recovery completed successfully. Monitoring for stability.",
                            author="recovery_orchestrator",
                            update_type="recovery_update",
                            status_change={
                                "old_status": incident.status.value,
                                "new_status": IncidentStatus.MONITORING.value
                            }
                        )
                    break
            
        except Exception as e:
            self.logger.error(f"Error handling recovery completed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            open_incidents = len([i for i in self.incidents.values() if i.status != IncidentStatus.CLOSED])
            critical_incidents = len([i for i in self.incidents.values() if i.severity == IncidentSeverity.SEV1_CRITICAL and i.status != IncidentStatus.CLOSED])
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "incident_tracker",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_incidents": len(self.incidents),
                    "open_incidents": open_incidents,
                    "critical_incidents": critical_incidents,
                    "incident_updates": len(self.incident_updates),
                    "incident_resolutions": len(self.incident_resolutions),
                    "templates_configured": len(self.incident_templates)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "incident_tracker",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Incident tracker service cleanup initiated")
        
        try:
            # Clear all state
            self.incidents.clear()
            self.incident_updates.clear()
            self.incident_resolutions.clear()
            self.incident_metrics.clear()
            
            # Cleanup dependencies
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Incident tracker service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_incident_tracker() -> IncidentTracker:
    """Create incident tracker service"""
    return IncidentTracker()