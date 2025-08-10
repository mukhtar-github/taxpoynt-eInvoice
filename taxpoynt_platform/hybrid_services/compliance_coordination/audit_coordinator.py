"""
Hybrid Service: Audit Coordinator
Coordinates audit activities across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib

from core_platform.database import get_db_session
from core_platform.models.audit import AuditTrail, AuditEvent, AuditSession, AuditReport
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class AuditType(str, Enum):
    """Types of audit activities"""
    COMPLIANCE_AUDIT = "compliance_audit"
    SECURITY_AUDIT = "security_audit"
    OPERATIONAL_AUDIT = "operational_audit"
    REGULATORY_AUDIT = "regulatory_audit"
    INTERNAL_AUDIT = "internal_audit"
    EXTERNAL_AUDIT = "external_audit"
    INCIDENT_AUDIT = "incident_audit"
    PERIODIC_AUDIT = "periodic_audit"


class AuditScope(str, Enum):
    """Audit scope"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    CROSS_ROLE = "cross_role"
    SYSTEM_WIDE = "system_wide"
    SPECIFIC_PROCESS = "specific_process"


class AuditStatus(str, Enum):
    """Audit status"""
    PLANNED = "planned"
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class AuditPriority(str, Enum):
    """Audit priority levels"""
    EMERGENCY = "emergency"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    ROUTINE = "routine"


class EventType(str, Enum):
    """Audit event types"""
    ACCESS_ATTEMPT = "access_attempt"
    DATA_MODIFICATION = "data_modification"
    SYSTEM_CONFIGURATION = "system_configuration"
    COMPLIANCE_CHECK = "compliance_check"
    SECURITY_INCIDENT = "security_incident"
    PROCESS_EXECUTION = "process_execution"
    ERROR_OCCURRENCE = "error_occurrence"
    PERFORMANCE_ANOMALY = "performance_anomaly"


@dataclass
class AuditEvent:
    """Audit event record"""
    event_id: str
    event_type: EventType
    service_role: str
    service_name: str
    user_id: Optional[str]
    action: str
    resource: str
    details: Dict[str, Any]
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditTrail:
    """Audit trail record"""
    trail_id: str
    audit_session_id: str
    events: List[AuditEvent]
    start_time: datetime
    end_time: Optional[datetime]
    checksum: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditSession:
    """Audit session"""
    session_id: str
    audit_type: AuditType
    audit_scope: AuditScope
    initiated_by: str
    target_services: List[str]
    objectives: List[str]
    status: AuditStatus
    priority: AuditPriority
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    findings: List[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditFinding:
    """Audit finding"""
    finding_id: str
    session_id: str
    finding_type: str
    severity: str
    title: str
    description: str
    evidence: List[str]
    impact: str
    recommendation: str
    service_role: str
    detected_at: datetime
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AuditReport:
    """Audit report"""
    report_id: str
    session_id: str
    report_type: str
    title: str
    executive_summary: str
    detailed_findings: List[AuditFinding]
    recommendations: List[str]
    compliance_status: str
    generated_by: str
    generated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AuditCoordinator:
    """Audit coordination service"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Active audit sessions
        self.active_sessions: Dict[str, AuditSession] = {}
        
        # Audit trails
        self.audit_trails: Dict[str, AuditTrail] = {}
        
        # Event buffer
        self.event_buffer: List[AuditEvent] = []
        
        # Audit configurations
        self.audit_configurations: Dict[str, Dict[str, Any]] = {}
        
        # Session history
        self.session_history: List[AuditSession] = []
        
        # Initialize default configurations
        self._initialize_default_configurations()
    
    async def initiate_audit_session(
        self,
        audit_type: AuditType,
        audit_scope: AuditScope,
        initiated_by: str,
        target_services: List[str],
        objectives: List[str],
        priority: AuditPriority = AuditPriority.MEDIUM
    ) -> AuditSession:
        """Initiate an audit session"""
        session_id = str(uuid.uuid4())
        
        try:
            # Create audit session
            session = AuditSession(
                session_id=session_id,
                audit_type=audit_type,
                audit_scope=audit_scope,
                initiated_by=initiated_by,
                target_services=target_services,
                objectives=objectives,
                status=AuditStatus.INITIATED,
                priority=priority,
                start_time=datetime.now(timezone.utc),
                end_time=None,
                duration=0.0,
                findings=[],
                recommendations=[]
            )
            
            # Add to active sessions
            self.active_sessions[session_id] = session
            
            # Create audit trail
            trail = AuditTrail(
                trail_id=f"trail_{session_id}",
                audit_session_id=session_id,
                events=[],
                start_time=datetime.now(timezone.utc),
                end_time=None,
                checksum="",
                metadata={
                    "audit_type": audit_type,
                    "audit_scope": audit_scope,
                    "initiated_by": initiated_by
                }
            )
            
            self.audit_trails[session_id] = trail
            
            # Log audit initiation
            await self._log_audit_event(
                session_id=session_id,
                event_type=EventType.PROCESS_EXECUTION,
                service_role="hybrid",
                service_name="audit_coordinator",
                user_id=initiated_by,
                action="audit_session_initiated",
                resource=f"audit_session:{session_id}",
                details={
                    "audit_type": audit_type,
                    "audit_scope": audit_scope,
                    "target_services": target_services,
                    "objectives": objectives
                }
            )
            
            # Emit event
            await self.event_bus.emit("audit_session_initiated", {
                "session_id": session_id,
                "audit_type": audit_type,
                "audit_scope": audit_scope,
                "initiated_by": initiated_by,
                "target_services": target_services,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Start audit collection
            await self._start_audit_collection(session)
            
            self.logger.info(f"Audit session initiated: {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error initiating audit session: {str(e)}")
            raise
    
    async def log_audit_event(
        self,
        event_type: EventType,
        service_role: str,
        service_name: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> str:
        """Log an audit event"""
        try:
            event_id = str(uuid.uuid4())
            
            # Create audit event
            event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                service_role=service_role,
                service_name=service_name,
                user_id=user_id,
                action=action,
                resource=resource,
                details=details,
                timestamp=datetime.now(timezone.utc),
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id
            )
            
            # Add to event buffer
            self.event_buffer.append(event)
            
            # Add to active audit trails
            for trail in self.audit_trails.values():
                if self._event_matches_trail(event, trail):
                    trail.events.append(event)
                    trail.checksum = self._calculate_trail_checksum(trail)
            
            # Store event
            await self._store_audit_event(event)
            
            # Check for audit triggers
            await self._check_audit_triggers(event)
            
            # Process event buffer periodically
            if len(self.event_buffer) >= 100:  # Process every 100 events
                await self._process_event_buffer()
            
            return event_id
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {str(e)}")
            raise
    
    async def complete_audit_session(
        self,
        session_id: str,
        findings: List[Dict[str, Any]],
        recommendations: List[str]
    ) -> AuditSession:
        """Complete an audit session"""
        try:
            if session_id not in self.active_sessions:
                raise ValueError(f"Audit session not found: {session_id}")
            
            session = self.active_sessions[session_id]
            
            # Update session
            session.status = AuditStatus.COMPLETED
            session.end_time = datetime.now(timezone.utc)
            session.duration = (session.end_time - session.start_time).total_seconds()
            session.findings = findings
            session.recommendations = recommendations
            
            # Complete audit trail
            if session_id in self.audit_trails:
                trail = self.audit_trails[session_id]
                trail.end_time = datetime.now(timezone.utc)
                trail.checksum = self._calculate_trail_checksum(trail)
                
                # Store audit trail
                await self._store_audit_trail(trail)
            
            # Log completion
            await self._log_audit_event(
                session_id=session_id,
                event_type=EventType.PROCESS_EXECUTION,
                service_role="hybrid",
                service_name="audit_coordinator",
                user_id=session.initiated_by,
                action="audit_session_completed",
                resource=f"audit_session:{session_id}",
                details={
                    "findings_count": len(findings),
                    "recommendations_count": len(recommendations),
                    "duration": session.duration
                }
            )
            
            # Move to history
            self.session_history.append(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Store session
            await self._store_audit_session(session)
            
            # Emit event
            await self.event_bus.emit("audit_session_completed", {
                "session_id": session_id,
                "status": session.status,
                "findings_count": len(findings),
                "recommendations_count": len(recommendations),
                "duration": session.duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Audit session completed: {session_id}")
            return session
            
        except Exception as e:
            self.logger.error(f"Error completing audit session: {str(e)}")
            raise
    
    async def cancel_audit_session(self, session_id: str, reason: str) -> bool:
        """Cancel an audit session"""
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Update session
            session.status = AuditStatus.CANCELLED
            session.end_time = datetime.now(timezone.utc)
            session.duration = (session.end_time - session.start_time).total_seconds()
            
            # Log cancellation
            await self._log_audit_event(
                session_id=session_id,
                event_type=EventType.PROCESS_EXECUTION,
                service_role="hybrid",
                service_name="audit_coordinator",
                user_id=session.initiated_by,
                action="audit_session_cancelled",
                resource=f"audit_session:{session_id}",
                details={"reason": reason}
            )
            
            # Move to history
            self.session_history.append(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            
            # Store session
            await self._store_audit_session(session)
            
            # Emit event
            await self.event_bus.emit("audit_session_cancelled", {
                "session_id": session_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling audit session: {str(e)}")
            return False
    
    async def get_audit_session(self, session_id: str) -> Optional[AuditSession]:
        """Get audit session"""
        try:
            # Check active sessions
            if session_id in self.active_sessions:
                return self.active_sessions[session_id]
            
            # Check history
            for session in self.session_history:
                if session.session_id == session_id:
                    return session
            
            # Check database
            return await self._get_stored_audit_session(session_id)
            
        except Exception as e:
            self.logger.error(f"Error getting audit session: {str(e)}")
            return None
    
    async def get_audit_trail(self, session_id: str) -> Optional[AuditTrail]:
        """Get audit trail for session"""
        try:
            # Check active trails
            if session_id in self.audit_trails:
                return self.audit_trails[session_id]
            
            # Check database
            return await self._get_stored_audit_trail(session_id)
            
        except Exception as e:
            self.logger.error(f"Error getting audit trail: {str(e)}")
            return None
    
    async def search_audit_events(
        self,
        filters: Dict[str, Any],
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """Search audit events"""
        try:
            # This would implement complex search logic
            # For now, return recent events from buffer
            filtered_events = self.event_buffer
            
            # Apply filters
            if "event_type" in filters:
                filtered_events = [
                    e for e in filtered_events
                    if e.event_type == filters["event_type"]
                ]
            
            if "service_role" in filters:
                filtered_events = [
                    e for e in filtered_events
                    if e.service_role == filters["service_role"]
                ]
            
            if "user_id" in filters:
                filtered_events = [
                    e for e in filtered_events
                    if e.user_id == filters["user_id"]
                ]
            
            if "start_time" in filters:
                start_time = datetime.fromisoformat(filters["start_time"])
                filtered_events = [
                    e for e in filtered_events
                    if e.timestamp >= start_time
                ]
            
            if "end_time" in filters:
                end_time = datetime.fromisoformat(filters["end_time"])
                filtered_events = [
                    e for e in filtered_events
                    if e.timestamp <= end_time
                ]
            
            # Apply pagination
            return filtered_events[offset:offset + limit]
            
        except Exception as e:
            self.logger.error(f"Error searching audit events: {str(e)}")
            return []
    
    async def generate_audit_report(
        self,
        session_id: str,
        report_type: str = "detailed",
        include_recommendations: bool = True
    ) -> AuditReport:
        """Generate audit report"""
        try:
            # Get audit session
            session = await self.get_audit_session(session_id)
            if not session:
                raise ValueError(f"Audit session not found: {session_id}")
            
            # Get audit trail
            trail = await self.get_audit_trail(session_id)
            
            # Analyze findings
            detailed_findings = await self._analyze_audit_findings(session, trail)
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(session, detailed_findings)
            
            # Compile recommendations
            recommendations = session.recommendations if include_recommendations else []
            
            # Determine compliance status
            compliance_status = await self._determine_compliance_status(detailed_findings)
            
            # Create report
            report = AuditReport(
                report_id=f"audit_report_{session_id}_{int(datetime.now().timestamp())}",
                session_id=session_id,
                report_type=report_type,
                title=f"Audit Report - {session.audit_type.value}",
                executive_summary=executive_summary,
                detailed_findings=detailed_findings,
                recommendations=recommendations,
                compliance_status=compliance_status,
                generated_by="audit_coordinator",
                generated_at=datetime.now(timezone.utc)
            )
            
            # Store report
            await self._store_audit_report(report)
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating audit report: {str(e)}")
            raise
    
    async def get_audit_metrics(
        self,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        audit_type: Optional[AuditType] = None
    ) -> Dict[str, Any]:
        """Get audit metrics"""
        try:
            # Filter sessions
            filtered_sessions = self.session_history
            
            if time_range:
                start_time, end_time = time_range
                filtered_sessions = [
                    session for session in filtered_sessions
                    if start_time <= session.start_time <= end_time
                ]
            
            if audit_type:
                filtered_sessions = [
                    session for session in filtered_sessions
                    if session.audit_type == audit_type
                ]
            
            # Calculate metrics
            total_sessions = len(filtered_sessions)
            completed_sessions = len([s for s in filtered_sessions if s.status == AuditStatus.COMPLETED])
            failed_sessions = len([s for s in filtered_sessions if s.status == AuditStatus.FAILED])
            cancelled_sessions = len([s for s in filtered_sessions if s.status == AuditStatus.CANCELLED])
            
            # Calculate success rate
            success_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            # Calculate average duration
            durations = [s.duration for s in filtered_sessions if s.duration > 0]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Count findings
            total_findings = sum(len(s.findings) for s in filtered_sessions)
            
            # Event metrics
            total_events = len(self.event_buffer)
            
            # Active sessions
            active_sessions = len(self.active_sessions)
            
            return {
                "total_sessions": total_sessions,
                "completed_sessions": completed_sessions,
                "failed_sessions": failed_sessions,
                "cancelled_sessions": cancelled_sessions,
                "success_rate": success_rate,
                "average_duration": avg_duration,
                "total_findings": total_findings,
                "total_events": total_events,
                "active_sessions": active_sessions,
                "audit_type": audit_type.value if audit_type else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting audit metrics: {str(e)}")
            raise
    
    async def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List active audit sessions"""
        try:
            active_list = []
            
            for session_id, session in self.active_sessions.items():
                active_list.append({
                    "session_id": session_id,
                    "audit_type": session.audit_type,
                    "audit_scope": session.audit_scope,
                    "status": session.status,
                    "priority": session.priority,
                    "initiated_by": session.initiated_by,
                    "start_time": session.start_time.isoformat(),
                    "target_services": session.target_services,
                    "duration": (datetime.now(timezone.utc) - session.start_time).total_seconds()
                })
            
            return active_list
            
        except Exception as e:
            self.logger.error(f"Error listing active sessions: {str(e)}")
            return []
    
    async def configure_audit_parameters(
        self,
        audit_type: AuditType,
        configuration: Dict[str, Any]
    ) -> bool:
        """Configure audit parameters"""
        try:
            self.audit_configurations[audit_type] = configuration
            
            # Cache configuration
            await self.cache_service.set(
                f"audit_config:{audit_type}",
                configuration,
                ttl=86400  # 24 hours
            )
            
            self.logger.info(f"Audit configuration updated: {audit_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring audit parameters: {str(e)}")
            return False
    
    # Private helper methods
    
    async def _log_audit_event(
        self,
        session_id: str,
        event_type: EventType,
        service_role: str,
        service_name: str,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any]
    ) -> None:
        """Log audit event for session"""
        try:
            await self.log_audit_event(
                event_type=event_type,
                service_role=service_role,
                service_name=service_name,
                action=action,
                resource=resource,
                details=details,
                user_id=user_id,
                session_id=session_id
            )
            
        except Exception as e:
            self.logger.error(f"Error logging audit event: {str(e)}")
    
    async def _start_audit_collection(self, session: AuditSession) -> None:
        """Start audit collection for session"""
        try:
            # This would start collecting audit events for the session
            # Based on the audit type and scope
            
            if session.audit_type == AuditType.COMPLIANCE_AUDIT:
                await self._start_compliance_audit_collection(session)
            elif session.audit_type == AuditType.SECURITY_AUDIT:
                await self._start_security_audit_collection(session)
            elif session.audit_type == AuditType.OPERATIONAL_AUDIT:
                await self._start_operational_audit_collection(session)
            
        except Exception as e:
            self.logger.error(f"Error starting audit collection: {str(e)}")
    
    async def _start_compliance_audit_collection(self, session: AuditSession) -> None:
        """Start compliance audit collection"""
        try:
            # Start collecting compliance-related events
            pass
            
        except Exception as e:
            self.logger.error(f"Error starting compliance audit collection: {str(e)}")
    
    async def _start_security_audit_collection(self, session: AuditSession) -> None:
        """Start security audit collection"""
        try:
            # Start collecting security-related events
            pass
            
        except Exception as e:
            self.logger.error(f"Error starting security audit collection: {str(e)}")
    
    async def _start_operational_audit_collection(self, session: AuditSession) -> None:
        """Start operational audit collection"""
        try:
            # Start collecting operational events
            pass
            
        except Exception as e:
            self.logger.error(f"Error starting operational audit collection: {str(e)}")
    
    def _event_matches_trail(self, event: AuditEvent, trail: AuditTrail) -> bool:
        """Check if event matches audit trail"""
        try:
            # Check if event is relevant to the audit trail
            # This would implement complex matching logic
            return True  # For now, include all events
            
        except Exception as e:
            self.logger.error(f"Error checking event match: {str(e)}")
            return False
    
    def _calculate_trail_checksum(self, trail: AuditTrail) -> str:
        """Calculate audit trail checksum"""
        try:
            # Create checksum data
            checksum_data = {
                "trail_id": trail.trail_id,
                "session_id": trail.audit_session_id,
                "event_count": len(trail.events),
                "start_time": trail.start_time.isoformat(),
                "end_time": trail.end_time.isoformat() if trail.end_time else None
            }
            
            # Add event checksums
            event_checksums = []
            for event in trail.events:
                event_data = {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "action": event.action,
                    "resource": event.resource
                }
                event_checksum = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()
                event_checksums.append(event_checksum)
            
            checksum_data["event_checksums"] = event_checksums
            
            # Generate checksum
            checksum_string = json.dumps(checksum_data, sort_keys=True)
            return hashlib.sha256(checksum_string.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating trail checksum: {str(e)}")
            return ""
    
    async def _store_audit_event(self, event: AuditEvent) -> None:
        """Store audit event"""
        try:
            # Store in database
            with get_db_session() as db:
                db_event = AuditEvent(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    service_role=event.service_role,
                    service_name=event.service_name,
                    user_id=event.user_id,
                    action=event.action,
                    resource=event.resource,
                    details=event.details,
                    timestamp=event.timestamp,
                    ip_address=event.ip_address,
                    user_agent=event.user_agent,
                    session_id=event.session_id
                )
                db.add(db_event)
                db.commit()
            
            # Cache event
            await self.cache_service.set(
                f"audit_event:{event.event_id}",
                event.to_dict(),
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            self.logger.error(f"Error storing audit event: {str(e)}")
    
    async def _store_audit_trail(self, trail: AuditTrail) -> None:
        """Store audit trail"""
        try:
            # Store in database
            with get_db_session() as db:
                db_trail = AuditTrail(
                    trail_id=trail.trail_id,
                    audit_session_id=trail.audit_session_id,
                    events=[event.to_dict() for event in trail.events],
                    start_time=trail.start_time,
                    end_time=trail.end_time,
                    checksum=trail.checksum,
                    metadata=trail.metadata
                )
                db.add(db_trail)
                db.commit()
            
            # Cache trail
            await self.cache_service.set(
                f"audit_trail:{trail.trail_id}",
                trail.to_dict(),
                ttl=86400 * 7  # 7 days
            )
            
        except Exception as e:
            self.logger.error(f"Error storing audit trail: {str(e)}")
    
    async def _store_audit_session(self, session: AuditSession) -> None:
        """Store audit session"""
        try:
            # Store in database
            with get_db_session() as db:
                db_session = AuditSession(
                    session_id=session.session_id,
                    audit_type=session.audit_type,
                    audit_scope=session.audit_scope,
                    initiated_by=session.initiated_by,
                    target_services=session.target_services,
                    objectives=session.objectives,
                    status=session.status,
                    priority=session.priority,
                    start_time=session.start_time,
                    end_time=session.end_time,
                    duration=session.duration,
                    findings=session.findings,
                    recommendations=session.recommendations
                )
                db.add(db_session)
                db.commit()
            
            # Cache session
            await self.cache_service.set(
                f"audit_session:{session.session_id}",
                session.to_dict(),
                ttl=86400  # 24 hours
            )
            
        except Exception as e:
            self.logger.error(f"Error storing audit session: {str(e)}")
    
    async def _store_audit_report(self, report: AuditReport) -> None:
        """Store audit report"""
        try:
            # Store in database
            with get_db_session() as db:
                db_report = AuditReport(
                    report_id=report.report_id,
                    session_id=report.session_id,
                    report_type=report.report_type,
                    title=report.title,
                    executive_summary=report.executive_summary,
                    detailed_findings=[finding.to_dict() for finding in report.detailed_findings],
                    recommendations=report.recommendations,
                    compliance_status=report.compliance_status,
                    generated_by=report.generated_by,
                    generated_at=report.generated_at
                )
                db.add(db_report)
                db.commit()
            
            # Cache report
            await self.cache_service.set(
                f"audit_report:{report.report_id}",
                report.to_dict(),
                ttl=86400 * 30  # 30 days
            )
            
        except Exception as e:
            self.logger.error(f"Error storing audit report: {str(e)}")
    
    async def _get_stored_audit_session(self, session_id: str) -> Optional[AuditSession]:
        """Get stored audit session"""
        try:
            # Check cache first
            cached_session = await self.cache_service.get(f"audit_session:{session_id}")
            if cached_session:
                return AuditSession(**cached_session)
            
            # Check database
            with get_db_session() as db:
                db_session = db.query(AuditSession).filter(
                    AuditSession.session_id == session_id
                ).first()
                
                if db_session:
                    return AuditSession(
                        session_id=db_session.session_id,
                        audit_type=AuditType(db_session.audit_type),
                        audit_scope=AuditScope(db_session.audit_scope),
                        initiated_by=db_session.initiated_by,
                        target_services=db_session.target_services,
                        objectives=db_session.objectives,
                        status=AuditStatus(db_session.status),
                        priority=AuditPriority(db_session.priority),
                        start_time=db_session.start_time,
                        end_time=db_session.end_time,
                        duration=db_session.duration,
                        findings=db_session.findings,
                        recommendations=db_session.recommendations
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored audit session: {str(e)}")
            return None
    
    async def _get_stored_audit_trail(self, session_id: str) -> Optional[AuditTrail]:
        """Get stored audit trail"""
        try:
            # Check cache first
            cached_trail = await self.cache_service.get(f"audit_trail:trail_{session_id}")
            if cached_trail:
                return AuditTrail(**cached_trail)
            
            # Check database
            with get_db_session() as db:
                db_trail = db.query(AuditTrail).filter(
                    AuditTrail.audit_session_id == session_id
                ).first()
                
                if db_trail:
                    return AuditTrail(
                        trail_id=db_trail.trail_id,
                        audit_session_id=db_trail.audit_session_id,
                        events=[AuditEvent(**event) for event in db_trail.events],
                        start_time=db_trail.start_time,
                        end_time=db_trail.end_time,
                        checksum=db_trail.checksum,
                        metadata=db_trail.metadata
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored audit trail: {str(e)}")
            return None
    
    async def _check_audit_triggers(self, event: AuditEvent) -> None:
        """Check for audit triggers"""
        try:
            # Check if event triggers automatic audit
            if event.event_type == EventType.SECURITY_INCIDENT:
                await self._trigger_security_audit(event)
            elif event.event_type == EventType.COMPLIANCE_CHECK and event.details.get("status") == "failed":
                await self._trigger_compliance_audit(event)
            
        except Exception as e:
            self.logger.error(f"Error checking audit triggers: {str(e)}")
    
    async def _trigger_security_audit(self, event: AuditEvent) -> None:
        """Trigger security audit"""
        try:
            # Automatically initiate security audit
            await self.initiate_audit_session(
                audit_type=AuditType.SECURITY_AUDIT,
                audit_scope=AuditScope.SYSTEM_WIDE,
                initiated_by="system",
                target_services=[event.service_name],
                objectives=[f"Investigate security incident: {event.event_id}"],
                priority=AuditPriority.HIGH
            )
            
        except Exception as e:
            self.logger.error(f"Error triggering security audit: {str(e)}")
    
    async def _trigger_compliance_audit(self, event: AuditEvent) -> None:
        """Trigger compliance audit"""
        try:
            # Automatically initiate compliance audit
            await self.initiate_audit_session(
                audit_type=AuditType.COMPLIANCE_AUDIT,
                audit_scope=AuditScope.SPECIFIC_PROCESS,
                initiated_by="system",
                target_services=[event.service_name],
                objectives=[f"Investigate compliance failure: {event.event_id}"],
                priority=AuditPriority.MEDIUM
            )
            
        except Exception as e:
            self.logger.error(f"Error triggering compliance audit: {str(e)}")
    
    async def _process_event_buffer(self) -> None:
        """Process event buffer"""
        try:
            # Process events in buffer
            # This could include analysis, pattern detection, etc.
            
            # Clear processed events (keep recent ones)
            if len(self.event_buffer) > 1000:
                self.event_buffer = self.event_buffer[-500:]  # Keep last 500 events
            
        except Exception as e:
            self.logger.error(f"Error processing event buffer: {str(e)}")
    
    async def _analyze_audit_findings(
        self,
        session: AuditSession,
        trail: Optional[AuditTrail]
    ) -> List[AuditFinding]:
        """Analyze audit findings"""
        try:
            findings = []
            
            # Convert session findings to AuditFinding objects
            for i, finding in enumerate(session.findings):
                audit_finding = AuditFinding(
                    finding_id=f"finding_{session.session_id}_{i}",
                    session_id=session.session_id,
                    finding_type=finding.get("type", "general"),
                    severity=finding.get("severity", "medium"),
                    title=finding.get("title", "Audit Finding"),
                    description=finding.get("description", ""),
                    evidence=finding.get("evidence", []),
                    impact=finding.get("impact", ""),
                    recommendation=finding.get("recommendation", ""),
                    service_role=finding.get("service_role", "unknown"),
                    detected_at=datetime.now(timezone.utc)
                )
                findings.append(audit_finding)
            
            return findings
            
        except Exception as e:
            self.logger.error(f"Error analyzing audit findings: {str(e)}")
            return []
    
    async def _generate_executive_summary(
        self,
        session: AuditSession,
        findings: List[AuditFinding]
    ) -> str:
        """Generate executive summary"""
        try:
            # Count findings by severity
            critical_count = len([f for f in findings if f.severity == "critical"])
            high_count = len([f for f in findings if f.severity == "high"])
            medium_count = len([f for f in findings if f.severity == "medium"])
            low_count = len([f for f in findings if f.severity == "low"])
            
            # Generate summary
            summary = f"""
            Audit Summary for {session.audit_type.value}
            
            Audit Period: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')} to {session.end_time.strftime('%Y-%m-%d %H:%M:%S') if session.end_time else 'Ongoing'}
            Audit Scope: {session.audit_scope.value}
            Target Services: {', '.join(session.target_services)}
            
            Total Findings: {len(findings)}
            - Critical: {critical_count}
            - High: {high_count}
            - Medium: {medium_count}
            - Low: {low_count}
            
            Recommendations: {len(session.recommendations)}
            """
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
            return "Error generating summary"
    
    async def _determine_compliance_status(self, findings: List[AuditFinding]) -> str:
        """Determine compliance status"""
        try:
            critical_findings = [f for f in findings if f.severity == "critical"]
            high_findings = [f for f in findings if f.severity == "high"]
            
            if critical_findings:
                return "non_compliant"
            elif high_findings:
                return "partially_compliant"
            elif findings:
                return "compliant_with_recommendations"
            else:
                return "fully_compliant"
                
        except Exception as e:
            self.logger.error(f"Error determining compliance status: {str(e)}")
            return "unknown"
    
    def _initialize_default_configurations(self):
        """Initialize default audit configurations"""
        try:
            # Default configurations for different audit types
            self.audit_configurations = {
                AuditType.COMPLIANCE_AUDIT: {
                    "auto_trigger": True,
                    "retention_period": 365,  # days
                    "notification_threshold": "high",
                    "include_evidence": True
                },
                AuditType.SECURITY_AUDIT: {
                    "auto_trigger": True,
                    "retention_period": 730,  # days
                    "notification_threshold": "medium",
                    "include_evidence": True
                },
                AuditType.OPERATIONAL_AUDIT: {
                    "auto_trigger": False,
                    "retention_period": 90,  # days
                    "notification_threshold": "low",
                    "include_evidence": False
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing default configurations: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for audit coordinator"""
        try:
            return {
                "status": "healthy",
                "service": "audit_coordinator",
                "active_sessions": len(self.active_sessions),
                "event_buffer_size": len(self.event_buffer),
                "audit_trails": len(self.audit_trails),
                "session_history_size": len(self.session_history),
                "configurations": len(self.audit_configurations),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "audit_coordinator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup audit coordinator resources"""
        try:
            # Complete active sessions
            for session_id in list(self.active_sessions.keys()):
                await self.cancel_audit_session(session_id, "Service cleanup")
            
            # Clear registries
            self.active_sessions.clear()
            self.audit_trails.clear()
            self.event_buffer.clear()
            self.audit_configurations.clear()
            self.session_history.clear()
            
            self.logger.info("Audit coordinator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_audit_coordinator() -> AuditCoordinator:
    """Create audit coordinator instance"""
    return AuditCoordinator()