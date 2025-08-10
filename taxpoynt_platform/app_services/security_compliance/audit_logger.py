"""
Security Audit Logger Service for APP Role

This service handles security audit logging including:
- Comprehensive security event logging
- Audit trail management and storage
- Compliance logging for regulations
- Real-time security monitoring
- Log integrity and tamper protection
"""

import json
import time
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import asyncio
from collections import defaultdict, deque
import threading
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AuditLevel(Enum):
    """Audit logging levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"


class EventCategory(Enum):
    """Event categories for audit logging"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ENCRYPTION = "encryption"
    NETWORK = "network"
    SYSTEM = "system"
    COMPLIANCE = "compliance"
    SECURITY_INCIDENT = "security_incident"
    CONFIGURATION = "configuration"


class ComplianceStandard(Enum):
    """Compliance standards"""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    FIRS = "firs"
    CUSTOM = "custom"


class LogFormat(Enum):
    """Log output formats"""
    JSON = "json"
    CEF = "cef"
    SYSLOG = "syslog"
    CSV = "csv"
    STRUCTURED = "structured"


@dataclass
class AuditContext:
    """Context information for audit events"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditEvent:
    """Audit event structure"""
    event_id: str
    timestamp: datetime
    level: AuditLevel
    category: EventCategory
    event_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    context: Optional[AuditContext] = None
    compliance_tags: List[ComplianceStandard] = field(default_factory=list)
    risk_score: int = 0
    severity: str = "medium"
    source_component: str = "unknown"
    outcome: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AuditFilter:
    """Filter for audit event queries"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    levels: Optional[List[AuditLevel]] = None
    categories: Optional[List[EventCategory]] = None
    event_types: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    ip_addresses: Optional[List[str]] = None
    compliance_standards: Optional[List[ComplianceStandard]] = None
    risk_score_min: Optional[int] = None
    risk_score_max: Optional[int] = None
    text_search: Optional[str] = None
    limit: int = 1000


@dataclass
class LogIntegrityCheck:
    """Log integrity verification data"""
    log_hash: str
    previous_hash: str
    block_number: int
    timestamp: datetime
    log_count: int
    checksum: str


@dataclass
class AuditReport:
    """Audit report structure"""
    report_id: str
    generated_at: datetime
    time_period: Dict[str, datetime]
    total_events: int
    events_by_level: Dict[str, int]
    events_by_category: Dict[str, int]
    top_event_types: List[Tuple[str, int]]
    compliance_events: Dict[str, int]
    security_incidents: int
    high_risk_events: int
    unique_users: int
    unique_ips: int
    summary: str
    recommendations: List[str] = field(default_factory=list)


class AuditLogger:
    """
    Security audit logger service for APP role
    
    Handles:
    - Comprehensive security event logging
    - Audit trail management and storage
    - Compliance logging for regulations
    - Real-time security monitoring
    - Log integrity and tamper protection
    """
    
    def __init__(self, 
                 log_directory: str = "audit_logs",
                 log_format: LogFormat = LogFormat.JSON,
                 max_log_size: int = 100 * 1024 * 1024,  # 100MB
                 max_log_files: int = 100,
                 enable_compression: bool = True,
                 enable_integrity_check: bool = True,
                 buffer_size: int = 1000,
                 flush_interval: int = 60):
        
        self.log_directory = Path(log_directory)
        self.log_format = log_format
        self.max_log_size = max_log_size
        self.max_log_files = max_log_files
        self.enable_compression = enable_compression
        self.enable_integrity_check = enable_integrity_check
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Create log directory
        self.log_directory.mkdir(exist_ok=True, parents=True)
        
        # Event storage
        self.event_buffer: deque = deque(maxlen=buffer_size)
        self.event_storage: List[AuditEvent] = []
        
        # Integrity chain
        self.integrity_chain: List[LogIntegrityCheck] = []
        self.last_hash = "genesis"
        
        # Event handlers
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        
        # Real-time monitoring
        self.real_time_alerts: List[Dict[str, Any]] = []
        
        # Compliance mappings
        self.compliance_mappings = {
            ComplianceStandard.GDPR: [
                EventCategory.DATA_ACCESS,
                EventCategory.DATA_MODIFICATION,
                EventCategory.AUTHENTICATION
            ],
            ComplianceStandard.SOX: [
                EventCategory.DATA_MODIFICATION,
                EventCategory.AUTHORIZATION,
                EventCategory.CONFIGURATION
            ],
            ComplianceStandard.PCI_DSS: [
                EventCategory.DATA_ACCESS,
                EventCategory.ENCRYPTION,
                EventCategory.NETWORK,
                EventCategory.AUTHENTICATION
            ],
            ComplianceStandard.FIRS: [
                EventCategory.DATA_ACCESS,
                EventCategory.DATA_MODIFICATION,
                EventCategory.COMPLIANCE,
                EventCategory.NETWORK
            ]
        }
        
        # Background tasks
        self.flush_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Metrics
        self.metrics = {
            'total_events': 0,
            'events_by_level': defaultdict(int),
            'events_by_category': defaultdict(int),
            'events_by_compliance': defaultdict(int),
            'security_incidents': 0,
            'high_risk_events': 0,
            'log_files_created': 0,
            'log_files_compressed': 0,
            'integrity_checks': 0,
            'buffer_flushes': 0,
            'alerts_triggered': 0
        }
        
        # Current log file
        self.current_log_file: Optional[str] = None
        self.current_log_size = 0
        
        logger.info(f"Audit logger initialized with directory: {self.log_directory}")
    
    async def start(self):
        """Start the audit logger service"""
        self.running = True
        
        # Start background flush task
        self.flush_task = asyncio.create_task(self._periodic_flush())
        
        logger.info("Audit logger service started")
    
    async def stop(self):
        """Stop the audit logger service"""
        self.running = False
        
        # Cancel flush task
        if self.flush_task:
            self.flush_task.cancel()
        
        # Flush remaining events
        await self._flush_buffer()
        
        logger.info("Audit logger service stopped")
    
    async def log_event(self, 
                       level: AuditLevel,
                       category: EventCategory,
                       event_type: str,
                       message: str,
                       details: Optional[Dict[str, Any]] = None,
                       context: Optional[AuditContext] = None,
                       compliance_tags: Optional[List[ComplianceStandard]] = None,
                       risk_score: int = 0,
                       severity: str = "medium",
                       source_component: str = "unknown") -> str:
        """
        Log audit event
        
        Args:
            level: Audit level
            category: Event category
            event_type: Specific event type
            message: Event message
            details: Additional event details
            context: Audit context
            compliance_tags: Compliance standards tags
            risk_score: Risk score (0-100)
            severity: Event severity
            source_component: Source component
            
        Returns:
            Event ID
        """
        event_id = f"{event_type}_{int(time.time() * 1000000)}"
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            timestamp=datetime.utcnow(),
            level=level,
            category=category,
            event_type=event_type,
            message=message,
            details=details or {},
            context=context,
            compliance_tags=compliance_tags or [],
            risk_score=risk_score,
            severity=severity,
            source_component=source_component,
            outcome="logged"
        )
        
        # Add to buffer
        self.event_buffer.append(event)
        
        # Update metrics
        self.metrics['total_events'] += 1
        self.metrics['events_by_level'][level.value] += 1
        self.metrics['events_by_category'][category.value] += 1
        
        for compliance_tag in compliance_tags or []:
            self.metrics['events_by_compliance'][compliance_tag.value] += 1
        
        if level == AuditLevel.SECURITY or category == EventCategory.SECURITY_INCIDENT:
            self.metrics['security_incidents'] += 1
        
        if risk_score >= 80:
            self.metrics['high_risk_events'] += 1
        
        # Trigger real-time monitoring
        await self._process_real_time_monitoring(event)
        
        # Trigger event handlers
        await self._trigger_event_handlers(event)
        
        # Auto-flush if buffer is full
        if len(self.event_buffer) >= self.buffer_size:
            await self._flush_buffer()
        
        return event_id
    
    async def log_authentication_event(self,
                                     event_type: str,
                                     user_id: str,
                                     success: bool,
                                     context: Optional[AuditContext] = None,
                                     details: Optional[Dict[str, Any]] = None):
        """Log authentication event"""
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        risk_score = 20 if success else 60
        
        message = f"Authentication {event_type} {'successful' if success else 'failed'} for user {user_id}"
        
        event_details = {
            'user_id': user_id,
            'success': success,
            'event_subtype': event_type,
            **(details or {})
        }
        
        return await self.log_event(
            level=level,
            category=EventCategory.AUTHENTICATION,
            event_type=f"auth_{event_type}",
            message=message,
            details=event_details,
            context=context,
            compliance_tags=[ComplianceStandard.GDPR, ComplianceStandard.FIRS],
            risk_score=risk_score,
            severity="low" if success else "medium",
            source_component="authentication"
        )
    
    async def log_data_access_event(self,
                                  resource: str,
                                  operation: str,
                                  user_id: str,
                                  context: Optional[AuditContext] = None,
                                  details: Optional[Dict[str, Any]] = None):
        """Log data access event"""
        message = f"Data access: {operation} on {resource} by user {user_id}"
        
        event_details = {
            'resource': resource,
            'operation': operation,
            'user_id': user_id,
            'access_time': datetime.utcnow().isoformat(),
            **(details or {})
        }
        
        return await self.log_event(
            level=AuditLevel.INFO,
            category=EventCategory.DATA_ACCESS,
            event_type="data_access",
            message=message,
            details=event_details,
            context=context,
            compliance_tags=[ComplianceStandard.GDPR, ComplianceStandard.FIRS, ComplianceStandard.SOX],
            risk_score=30,
            severity="low",
            source_component="data_layer"
        )
    
    async def log_encryption_event(self,
                                 operation: str,
                                 algorithm: str,
                                 key_id: str,
                                 document_id: Optional[str] = None,
                                 context: Optional[AuditContext] = None):
        """Log encryption event"""
        message = f"Encryption operation: {operation} using {algorithm} with key {key_id}"
        
        event_details = {
            'operation': operation,
            'algorithm': algorithm,
            'key_id': key_id,
            'document_id': document_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return await self.log_event(
            level=AuditLevel.INFO,
            category=EventCategory.ENCRYPTION,
            event_type="encryption_operation",
            message=message,
            details=event_details,
            context=context,
            compliance_tags=[ComplianceStandard.PCI_DSS, ComplianceStandard.FIRS],
            risk_score=10,
            severity="low",
            source_component="encryption"
        )
    
    async def log_security_incident(self,
                                  incident_type: str,
                                  severity: str,
                                  description: str,
                                  context: Optional[AuditContext] = None,
                                  details: Optional[Dict[str, Any]] = None):
        """Log security incident"""
        risk_score_map = {
            "low": 40,
            "medium": 70,
            "high": 90,
            "critical": 100
        }
        
        risk_score = risk_score_map.get(severity.lower(), 70)
        
        message = f"Security incident: {incident_type} - {description}"
        
        event_details = {
            'incident_type': incident_type,
            'description': description,
            'severity': severity,
            'detected_at': datetime.utcnow().isoformat(),
            **(details or {})
        }
        
        return await self.log_event(
            level=AuditLevel.SECURITY,
            category=EventCategory.SECURITY_INCIDENT,
            event_type="security_incident",
            message=message,
            details=event_details,
            context=context,
            compliance_tags=[ComplianceStandard.ISO_27001],
            risk_score=risk_score,
            severity=severity,
            source_component="security_monitor"
        )
    
    async def log_compliance_event(self,
                                 compliance_standard: ComplianceStandard,
                                 event_type: str,
                                 description: str,
                                 context: Optional[AuditContext] = None,
                                 details: Optional[Dict[str, Any]] = None):
        """Log compliance event"""
        message = f"Compliance event ({compliance_standard.value}): {event_type} - {description}"
        
        event_details = {
            'compliance_standard': compliance_standard.value,
            'event_type': event_type,
            'description': description,
            'compliance_timestamp': datetime.utcnow().isoformat(),
            **(details or {})
        }
        
        return await self.log_event(
            level=AuditLevel.INFO,
            category=EventCategory.COMPLIANCE,
            event_type=f"compliance_{event_type}",
            message=message,
            details=event_details,
            context=context,
            compliance_tags=[compliance_standard],
            risk_score=20,
            severity="medium",
            source_component="compliance_monitor"
        )
    
    async def query_events(self, filter_criteria: AuditFilter) -> List[AuditEvent]:
        """
        Query audit events based on filter criteria
        
        Args:
            filter_criteria: Filter criteria for events
            
        Returns:
            List of matching audit events
        """
        # In a real implementation, this would query a database
        # For now, we'll filter the in-memory storage
        
        events = list(self.event_storage)
        
        # Apply filters
        if filter_criteria.start_time:
            events = [e for e in events if e.timestamp >= filter_criteria.start_time]
        
        if filter_criteria.end_time:
            events = [e for e in events if e.timestamp <= filter_criteria.end_time]
        
        if filter_criteria.levels:
            events = [e for e in events if e.level in filter_criteria.levels]
        
        if filter_criteria.categories:
            events = [e for e in events if e.category in filter_criteria.categories]
        
        if filter_criteria.event_types:
            events = [e for e in events if e.event_type in filter_criteria.event_types]
        
        if filter_criteria.user_ids and filter_criteria.user_ids:
            events = [e for e in events if e.context and e.context.user_id in filter_criteria.user_ids]
        
        if filter_criteria.risk_score_min is not None:
            events = [e for e in events if e.risk_score >= filter_criteria.risk_score_min]
        
        if filter_criteria.risk_score_max is not None:
            events = [e for e in events if e.risk_score <= filter_criteria.risk_score_max]
        
        if filter_criteria.text_search:
            search_text = filter_criteria.text_search.lower()
            events = [e for e in events if search_text in e.message.lower() or 
                     search_text in json.dumps(e.details).lower()]
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x.timestamp, reverse=True)
        
        # Apply limit
        return events[:filter_criteria.limit]
    
    async def generate_compliance_report(self,
                                       compliance_standard: ComplianceStandard,
                                       start_time: datetime,
                                       end_time: datetime) -> AuditReport:
        """Generate compliance audit report"""
        filter_criteria = AuditFilter(
            start_time=start_time,
            end_time=end_time,
            compliance_standards=[compliance_standard],
            limit=10000
        )
        
        events = await self.query_events(filter_criteria)
        
        # Generate statistics
        events_by_level = defaultdict(int)
        events_by_category = defaultdict(int)
        event_type_counts = defaultdict(int)
        unique_users = set()
        unique_ips = set()
        security_incidents = 0
        high_risk_events = 0
        
        for event in events:
            events_by_level[event.level.value] += 1
            events_by_category[event.category.value] += 1
            event_type_counts[event.event_type] += 1
            
            if event.context:
                if event.context.user_id:
                    unique_users.add(event.context.user_id)
                if event.context.ip_address:
                    unique_ips.add(event.context.ip_address)
            
            if event.level == AuditLevel.SECURITY:
                security_incidents += 1
            
            if event.risk_score >= 80:
                high_risk_events += 1
        
        # Top event types
        top_event_types = sorted(event_type_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Generate summary
        summary = (f"Compliance report for {compliance_standard.value.upper()} "
                  f"from {start_time.isoformat()} to {end_time.isoformat()}. "
                  f"Total events: {len(events)}, "
                  f"Security incidents: {security_incidents}, "
                  f"High risk events: {high_risk_events}")
        
        # Generate recommendations
        recommendations = []
        if security_incidents > 0:
            recommendations.append("Review and investigate security incidents")
        if high_risk_events > 10:
            recommendations.append("Implement additional security controls for high-risk activities")
        if len(unique_ips) > 100:
            recommendations.append("Monitor IP address diversity for potential security risks")
        
        report_id = f"compliance_{compliance_standard.value}_{int(time.time())}"
        
        return AuditReport(
            report_id=report_id,
            generated_at=datetime.utcnow(),
            time_period={'start': start_time, 'end': end_time},
            total_events=len(events),
            events_by_level=dict(events_by_level),
            events_by_category=dict(events_by_category),
            top_event_types=top_event_types,
            compliance_events={compliance_standard.value: len(events)},
            security_incidents=security_incidents,
            high_risk_events=high_risk_events,
            unique_users=len(unique_users),
            unique_ips=len(unique_ips),
            summary=summary,
            recommendations=recommendations
        )
    
    async def _flush_buffer(self):
        """Flush event buffer to storage"""
        if not self.event_buffer:
            return
        
        # Move events from buffer to storage
        events_to_flush = list(self.event_buffer)
        self.event_buffer.clear()
        
        # Add to storage
        self.event_storage.extend(events_to_flush)
        
        # Write to log file
        await self._write_to_log_file(events_to_flush)
        
        # Update integrity chain
        if self.enable_integrity_check:
            await self._update_integrity_chain(events_to_flush)
        
        self.metrics['buffer_flushes'] += 1
        
        logger.debug(f"Flushed {len(events_to_flush)} events to storage")
    
    async def _write_to_log_file(self, events: List[AuditEvent]):
        """Write events to log file"""
        # Get current log file
        log_file_path = await self._get_current_log_file()
        
        # Serialize events based on format
        serialized_events = []
        for event in events:
            if self.log_format == LogFormat.JSON:
                serialized_events.append(json.dumps(asdict(event), default=str))
            elif self.log_format == LogFormat.CEF:
                serialized_events.append(self._format_cef(event))
            elif self.log_format == LogFormat.SYSLOG:
                serialized_events.append(self._format_syslog(event))
            else:
                serialized_events.append(json.dumps(asdict(event), default=str))
        
        # Write to file
        log_content = '\n'.join(serialized_events) + '\n'
        
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write(log_content)
        
        self.current_log_size += len(log_content.encode('utf-8'))
        
        # Check if we need to rotate log file
        if self.current_log_size >= self.max_log_size:
            await self._rotate_log_file()
    
    async def _get_current_log_file(self) -> str:
        """Get current log file path"""
        if not self.current_log_file:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            self.current_log_file = str(self.log_directory / f"audit_{timestamp}.log")
            self.current_log_size = 0
            
            # Create log file
            Path(self.current_log_file).touch()
            self.metrics['log_files_created'] += 1
        
        return self.current_log_file
    
    async def _rotate_log_file(self):
        """Rotate log file"""
        if self.current_log_file:
            # Compress old log file if enabled
            if self.enable_compression:
                await self._compress_log_file(self.current_log_file)
            
            # Create new log file
            self.current_log_file = None
            await self._get_current_log_file()
            
            # Clean up old log files
            await self._cleanup_old_log_files()
    
    async def _compress_log_file(self, log_file_path: str):
        """Compress log file"""
        try:
            compressed_path = f"{log_file_path}.gz"
            
            with open(log_file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    f_out.write(f_in.read())
            
            # Remove original file
            os.remove(log_file_path)
            
            self.metrics['log_files_compressed'] += 1
            logger.debug(f"Compressed log file: {log_file_path}")
            
        except Exception as e:
            logger.error(f"Failed to compress log file {log_file_path}: {e}")
    
    async def _cleanup_old_log_files(self):
        """Clean up old log files"""
        try:
            log_files = list(self.log_directory.glob("audit_*.log*"))
            log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Keep only max_log_files
            for log_file in log_files[self.max_log_files:]:
                log_file.unlink()
                logger.debug(f"Deleted old log file: {log_file}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old log files: {e}")
    
    async def _update_integrity_chain(self, events: List[AuditEvent]):
        """Update integrity chain for tamper protection"""
        # Calculate hash of events
        events_data = json.dumps([asdict(event) for event in events], default=str, sort_keys=True)
        events_hash = hashlib.sha256(events_data.encode()).hexdigest()
        
        # Create integrity check
        integrity_check = LogIntegrityCheck(
            log_hash=events_hash,
            previous_hash=self.last_hash,
            block_number=len(self.integrity_chain),
            timestamp=datetime.utcnow(),
            log_count=len(events),
            checksum=hashlib.sha256(f"{events_hash}{self.last_hash}".encode()).hexdigest()
        )
        
        self.integrity_chain.append(integrity_check)
        self.last_hash = integrity_check.checksum
        self.metrics['integrity_checks'] += 1
    
    async def _process_real_time_monitoring(self, event: AuditEvent):
        """Process real-time monitoring for events"""
        # Check for high-risk events
        if event.risk_score >= 80:
            alert = {
                'alert_id': f"alert_{int(time.time())}",
                'event_id': event.event_id,
                'severity': 'high',
                'message': f"High-risk event detected: {event.message}",
                'timestamp': datetime.utcnow().isoformat(),
                'details': event.details
            }
            self.real_time_alerts.append(alert)
            self.metrics['alerts_triggered'] += 1
        
        # Check for security incidents
        if event.level == AuditLevel.SECURITY:
            alert = {
                'alert_id': f"security_alert_{int(time.time())}",
                'event_id': event.event_id,
                'severity': 'critical',
                'message': f"Security incident: {event.message}",
                'timestamp': datetime.utcnow().isoformat(),
                'details': event.details
            }
            self.real_time_alerts.append(alert)
            self.metrics['alerts_triggered'] += 1
    
    async def _trigger_event_handlers(self, event: AuditEvent):
        """Trigger registered event handlers"""
        # Trigger handlers for specific event types
        if event.event_type in self.event_handlers:
            for handler in self.event_handlers[event.event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Event handler failed for {event.event_type}: {e}")
        
        # Trigger handlers for event categories
        category_key = f"category_{event.category.value}"
        if category_key in self.event_handlers:
            for handler in self.event_handlers[category_key]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Category handler failed for {event.category.value}: {e}")
    
    def _format_cef(self, event: AuditEvent) -> str:
        """Format event as CEF (Common Event Format)"""
        # CEF format: CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|[Extension]
        return (f"CEF:0|TaxPoynt|APP|1.0|{event.event_type}|{event.message}|{event.severity}|"
                f"src={event.context.ip_address if event.context else 'unknown'} "
                f"duser={event.context.user_id if event.context else 'unknown'} "
                f"rt={int(event.timestamp.timestamp() * 1000)}")
    
    def _format_syslog(self, event: AuditEvent) -> str:
        """Format event as Syslog"""
        facility = 16  # Local use 0
        severity_map = {
            'low': 6,     # Info
            'medium': 4,  # Warning
            'high': 3,    # Error
            'critical': 2 # Critical
        }
        severity = severity_map.get(event.severity, 6)
        priority = facility * 8 + severity
        
        timestamp = event.timestamp.strftime("%b %d %H:%M:%S")
        return f"<{priority}>{timestamp} taxpoynt-app {event.source_component}: {event.message}"
    
    async def _periodic_flush(self):
        """Periodic flush of event buffer"""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic flush: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register event handler for specific event type"""
        self.event_handlers[event_type].append(handler)
    
    def register_category_handler(self, category: EventCategory, handler: Callable):
        """Register event handler for event category"""
        self.event_handlers[f"category_{category.value}"].append(handler)
    
    def get_real_time_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent real-time alerts"""
        return self.real_time_alerts[-limit:]
    
    def verify_integrity(self) -> bool:
        """Verify log integrity chain"""
        if not self.integrity_chain:
            return True
        
        previous_hash = "genesis"
        for check in self.integrity_chain:
            expected_checksum = hashlib.sha256(f"{check.log_hash}{previous_hash}".encode()).hexdigest()
            if check.checksum != expected_checksum:
                return False
            previous_hash = check.checksum
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get audit logger metrics"""
        return {
            **self.metrics,
            'buffer_size': len(self.event_buffer),
            'storage_size': len(self.event_storage),
            'integrity_chain_length': len(self.integrity_chain),
            'active_alerts': len(self.real_time_alerts),
            'current_log_size_mb': self.current_log_size / (1024 * 1024),
            'event_handlers': sum(len(handlers) for handlers in self.event_handlers.values()),
            'integrity_verified': self.verify_integrity()
        }


# Factory functions for easy setup
def create_audit_logger(log_directory: str = "audit_logs",
                       log_format: LogFormat = LogFormat.JSON,
                       enable_compression: bool = True) -> AuditLogger:
    """Create audit logger instance"""
    return AuditLogger(
        log_directory=log_directory,
        log_format=log_format,
        enable_compression=enable_compression
    )


def create_audit_context(user_id: Optional[str] = None,
                        session_id: Optional[str] = None,
                        ip_address: Optional[str] = None,
                        **kwargs) -> AuditContext:
    """Create audit context"""
    return AuditContext(
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        **kwargs
    )


def create_audit_filter(start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None,
                       levels: Optional[List[AuditLevel]] = None,
                       **kwargs) -> AuditFilter:
    """Create audit filter"""
    return AuditFilter(
        start_time=start_time,
        end_time=end_time,
        levels=levels,
        **kwargs
    )


async def log_security_event(event_type: str,
                           message: str,
                           severity: str = "medium",
                           details: Optional[Dict[str, Any]] = None) -> str:
    """Log security event"""
    logger_instance = create_audit_logger()
    await logger_instance.start()
    
    try:
        return await logger_instance.log_security_incident(
            incident_type=event_type,
            severity=severity,
            description=message,
            details=details
        )
    finally:
        await logger_instance.stop()


def get_audit_summary(audit_logger: AuditLogger) -> Dict[str, Any]:
    """Get audit logger summary"""
    metrics = audit_logger.get_metrics()
    
    return {
        'total_events': metrics['total_events'],
        'security_incidents': metrics['security_incidents'],
        'high_risk_events': metrics['high_risk_events'],
        'log_files_created': metrics['log_files_created'],
        'buffer_flushes': metrics['buffer_flushes'],
        'alerts_triggered': metrics['alerts_triggered'],
        'integrity_verified': metrics['integrity_verified'],
        'storage_size': metrics['storage_size'],
        'current_log_size_mb': metrics['current_log_size_mb']
    }