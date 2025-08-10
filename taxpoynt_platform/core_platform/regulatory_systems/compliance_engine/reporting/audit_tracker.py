"""
Compliance Audit Tracker
========================
Comprehensive audit trail tracking system that maintains detailed logs of all compliance
activities, changes, and regulatory interactions for audit and forensic purposes.
"""
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

from .models import (
    AuditTrail, AuditEvent, ComplianceStatus, RiskLevel,
    ReportFormat, ComplianceMetrics
)
from ..orchestrator.models import (
    ComplianceRequest, ComplianceResult, ValidationResult
)

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Types of audit events."""
    VALIDATION_PERFORMED = "validation_performed"
    COMPLIANCE_CHECK = "compliance_check"
    FRAMEWORK_UPDATE = "framework_update"
    POLICY_CHANGE = "policy_change"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"
    DATA_MODIFICATION = "data_modification"
    ACCESS_ATTEMPT = "access_attempt"
    CONFIGURATION_CHANGE = "configuration_change"
    EXCEPTION_OCCURRED = "exception_occurred"
    REPORT_GENERATED = "report_generated"
    ALERT_TRIGGERED = "alert_triggered"


class AuditSeverity(Enum):
    """Audit event severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    DEBUG = "debug"


@dataclass
class AuditContext:
    """Context information for audit events."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    organization_id: Optional[str] = None
    framework: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class AuditRecord:
    """Detailed audit record with full context."""
    record_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    title: str
    description: str
    context: AuditContext
    data_before: Optional[Dict[str, Any]] = None
    data_after: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    checksum: Optional[str] = None
    tags: Optional[List[str]] = None


class AuditTracker:
    """
    Comprehensive audit tracking system that maintains detailed compliance audit trails
    with forensic-quality logging and change tracking.
    """

    def __init__(self, organization_id: str):
        self.organization_id = organization_id
        self.logger = logging.getLogger(f"{__name__}.{organization_id}")
        self.audit_records: List[AuditRecord] = []
        self.checksum_enabled = True
        self.retention_days = 2555  # 7 years default retention

    def track_validation_event(
        self,
        validation_request: ComplianceRequest,
        validation_result: ComplianceResult,
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Track validation event with complete audit trail.
        
        Args:
            validation_request: Original validation request
            validation_result: Validation result
            context: Audit context information
            
        Returns:
            Audit record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            # Determine severity based on result
            severity = AuditSeverity.INFO
            if validation_result.overall_status == ComplianceStatus.FAILED:
                severity = AuditSeverity.ERROR
            elif validation_result.overall_status == ComplianceStatus.WARNING:
                severity = AuditSeverity.WARNING
            elif validation_result.risk_level == RiskLevel.CRITICAL:
                severity = AuditSeverity.CRITICAL
            
            # Extract key validation metrics
            metadata = {
                "frameworks": validation_request.frameworks,
                "validation_count": len(validation_result.framework_results),
                "passed_validations": len([r for r in validation_result.framework_results.values() 
                                         if r.status == ComplianceStatus.PASSED]),
                "failed_validations": len([r for r in validation_result.framework_results.values() 
                                         if r.status == ComplianceStatus.FAILED]),
                "execution_time_ms": validation_result.execution_time_ms,
                "confidence_score": validation_result.confidence_score
            }
            
            # Create audit record
            audit_record = AuditRecord(
                record_id=record_id,
                event_type=AuditEventType.VALIDATION_PERFORMED,
                severity=severity,
                timestamp=datetime.now(),
                title=f"Compliance Validation - {validation_result.overall_status.value}",
                description=f"Validation performed for frameworks: {', '.join(validation_request.frameworks)}",
                context=context or AuditContext(organization_id=self.organization_id),
                data_before={"request": asdict(validation_request)},
                data_after={"result": asdict(validation_result)},
                metadata=metadata,
                tags=["compliance", "validation"] + validation_request.frameworks
            )
            
            # Add checksum if enabled
            if self.checksum_enabled:
                audit_record.checksum = self._calculate_checksum(audit_record)
            
            # Store audit record
            self.audit_records.append(audit_record)
            
            self.logger.info(f"Validation event tracked: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Error tracking validation event: {str(e)}")
            raise

    def track_compliance_check(
        self,
        framework: str,
        check_type: str,
        result: Dict[str, Any],
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Track compliance check event.
        
        Args:
            framework: Regulatory framework name
            check_type: Type of compliance check
            result: Check result data
            context: Audit context information
            
        Returns:
            Audit record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            # Determine severity based on result
            severity = AuditSeverity.INFO
            if result.get("status") == "failed":
                severity = AuditSeverity.ERROR
            elif result.get("warnings"):
                severity = AuditSeverity.WARNING
            
            audit_record = AuditRecord(
                record_id=record_id,
                event_type=AuditEventType.COMPLIANCE_CHECK,
                severity=severity,
                timestamp=datetime.now(),
                title=f"{framework} Compliance Check - {check_type}",
                description=f"Compliance check performed for {framework} framework",
                context=context or AuditContext(
                    organization_id=self.organization_id,
                    framework=framework
                ),
                data_after={"result": result},
                metadata={
                    "framework": framework,
                    "check_type": check_type,
                    "status": result.get("status"),
                    "score": result.get("score")
                },
                tags=["compliance", "check", framework.lower()]
            )
            
            if self.checksum_enabled:
                audit_record.checksum = self._calculate_checksum(audit_record)
            
            self.audit_records.append(audit_record)
            
            self.logger.info(f"Compliance check tracked: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Error tracking compliance check: {str(e)}")
            raise

    def track_data_modification(
        self,
        entity_type: str,
        entity_id: str,
        operation: str,
        data_before: Optional[Dict[str, Any]],
        data_after: Optional[Dict[str, Any]],
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Track data modification event with before/after snapshots.
        
        Args:
            entity_type: Type of entity modified
            entity_id: Entity identifier
            operation: Operation performed (create, update, delete)
            data_before: Data state before modification
            data_after: Data state after modification
            context: Audit context information
            
        Returns:
            Audit record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            # Calculate change summary
            changes = self._calculate_changes(data_before, data_after)
            
            audit_record = AuditRecord(
                record_id=record_id,
                event_type=AuditEventType.DATA_MODIFICATION,
                severity=AuditSeverity.INFO,
                timestamp=datetime.now(),
                title=f"Data {operation.title()} - {entity_type}",
                description=f"{operation.title()} operation on {entity_type} {entity_id}",
                context=context or AuditContext(organization_id=self.organization_id),
                data_before=data_before,
                data_after=data_after,
                metadata={
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "operation": operation,
                    "changes_count": len(changes),
                    "changed_fields": list(changes.keys()) if changes else []
                },
                tags=["data", "modification", operation, entity_type.lower()]
            )
            
            if self.checksum_enabled:
                audit_record.checksum = self._calculate_checksum(audit_record)
            
            self.audit_records.append(audit_record)
            
            self.logger.info(f"Data modification tracked: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Error tracking data modification: {str(e)}")
            raise

    def track_user_action(
        self,
        action: str,
        resource: str,
        outcome: str,
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Track user action event.
        
        Args:
            action: Action performed
            resource: Resource accessed/modified
            outcome: Action outcome
            context: Audit context information
            
        Returns:
            Audit record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            # Determine severity based on outcome
            severity = AuditSeverity.INFO
            if outcome.lower() in ["failed", "denied", "error"]:
                severity = AuditSeverity.WARNING
            elif outcome.lower() in ["unauthorized", "forbidden"]:
                severity = AuditSeverity.ERROR
            
            audit_record = AuditRecord(
                record_id=record_id,
                event_type=AuditEventType.USER_ACTION,
                severity=severity,
                timestamp=datetime.now(),
                title=f"User Action - {action}",
                description=f"User performed {action} on {resource}",
                context=context or AuditContext(organization_id=self.organization_id),
                metadata={
                    "action": action,
                    "resource": resource,
                    "outcome": outcome
                },
                tags=["user", "action", action.lower()]
            )
            
            if self.checksum_enabled:
                audit_record.checksum = self._calculate_checksum(audit_record)
            
            self.audit_records.append(audit_record)
            
            self.logger.info(f"User action tracked: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Error tracking user action: {str(e)}")
            raise

    def track_system_event(
        self,
        event_name: str,
        description: str,
        event_data: Optional[Dict[str, Any]] = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        context: Optional[AuditContext] = None
    ) -> str:
        """
        Track system event.
        
        Args:
            event_name: Name of the system event
            description: Event description
            event_data: Additional event data
            severity: Event severity level
            context: Audit context information
            
        Returns:
            Audit record ID
        """
        try:
            record_id = str(uuid.uuid4())
            
            audit_record = AuditRecord(
                record_id=record_id,
                event_type=AuditEventType.SYSTEM_EVENT,
                severity=severity,
                timestamp=datetime.now(),
                title=f"System Event - {event_name}",
                description=description,
                context=context or AuditContext(organization_id=self.organization_id),
                data_after=event_data,
                metadata={
                    "event_name": event_name,
                    "system_generated": True
                },
                tags=["system", "event", event_name.lower().replace(" ", "_")]
            )
            
            if self.checksum_enabled:
                audit_record.checksum = self._calculate_checksum(audit_record)
            
            self.audit_records.append(audit_record)
            
            self.logger.info(f"System event tracked: {record_id}")
            return record_id
            
        except Exception as e:
            self.logger.error(f"Error tracking system event: {str(e)}")
            raise

    def get_audit_trail(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        event_types: Optional[List[AuditEventType]] = None,
        severity_levels: Optional[List[AuditSeverity]] = None,
        frameworks: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> List[AuditRecord]:
        """
        Retrieve audit trail with filtering options.
        
        Args:
            start_date: Filter from date
            end_date: Filter to date
            event_types: Filter by event types
            severity_levels: Filter by severity levels
            frameworks: Filter by frameworks
            user_id: Filter by user ID
            tags: Filter by tags
            limit: Limit number of results
            
        Returns:
            List of filtered audit records
        """
        try:
            filtered_records = self.audit_records.copy()
            
            # Apply date filters
            if start_date:
                start_datetime = datetime.combine(start_date, datetime.min.time())
                filtered_records = [r for r in filtered_records if r.timestamp >= start_datetime]
            
            if end_date:
                end_datetime = datetime.combine(end_date, datetime.max.time())
                filtered_records = [r for r in filtered_records if r.timestamp <= end_datetime]
            
            # Apply event type filter
            if event_types:
                filtered_records = [r for r in filtered_records if r.event_type in event_types]
            
            # Apply severity filter
            if severity_levels:
                filtered_records = [r for r in filtered_records if r.severity in severity_levels]
            
            # Apply framework filter
            if frameworks:
                filtered_records = [r for r in filtered_records 
                                  if r.context.framework in frameworks or 
                                  any(fw in (r.tags or []) for fw in frameworks)]
            
            # Apply user filter
            if user_id:
                filtered_records = [r for r in filtered_records if r.context.user_id == user_id]
            
            # Apply tags filter
            if tags:
                filtered_records = [r for r in filtered_records 
                                  if r.tags and any(tag in r.tags for tag in tags)]
            
            # Sort by timestamp (newest first)
            filtered_records.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply limit
            if limit:
                filtered_records = filtered_records[:limit]
            
            self.logger.info(f"Retrieved {len(filtered_records)} audit records")
            return filtered_records
            
        except Exception as e:
            self.logger.error(f"Error retrieving audit trail: {str(e)}")
            raise

    def generate_audit_report(
        self,
        start_date: date,
        end_date: date,
        report_format: ReportFormat = ReportFormat.JSON,
        include_data: bool = False
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            report_format: Report format
            include_data: Whether to include full data snapshots
            
        Returns:
            Audit report data
        """
        try:
            self.logger.info(f"Generating audit report from {start_date} to {end_date}")
            
            # Get audit records for date range
            audit_records = self.get_audit_trail(start_date=start_date, end_date=end_date)
            
            # Calculate summary statistics
            total_events = len(audit_records)
            event_type_counts = {}
            severity_counts = {}
            framework_counts = {}
            user_activity = {}
            
            for record in audit_records:
                # Count by event type
                event_type_counts[record.event_type.value] = event_type_counts.get(record.event_type.value, 0) + 1
                
                # Count by severity
                severity_counts[record.severity.value] = severity_counts.get(record.severity.value, 0) + 1
                
                # Count by framework
                if record.context.framework:
                    framework_counts[record.context.framework] = framework_counts.get(record.context.framework, 0) + 1
                
                # Count by user
                if record.context.user_id:
                    user_activity[record.context.user_id] = user_activity.get(record.context.user_id, 0) + 1
            
            # Prepare audit records for report
            report_records = []
            for record in audit_records:
                report_record = {
                    "record_id": record.record_id,
                    "event_type": record.event_type.value,
                    "severity": record.severity.value,
                    "timestamp": record.timestamp.isoformat(),
                    "title": record.title,
                    "description": record.description,
                    "context": asdict(record.context),
                    "metadata": record.metadata,
                    "tags": record.tags,
                    "checksum": record.checksum
                }
                
                # Include data snapshots if requested
                if include_data:
                    report_record["data_before"] = record.data_before
                    report_record["data_after"] = record.data_after
                
                report_records.append(report_record)
            
            # Generate report
            audit_report = {
                "report_id": str(uuid.uuid4()),
                "organization_id": self.organization_id,
                "report_type": "audit_trail",
                "generated_at": datetime.now().isoformat(),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "summary": {
                    "total_events": total_events,
                    "event_types": event_type_counts,
                    "severity_distribution": severity_counts,
                    "framework_activity": framework_counts,
                    "user_activity": user_activity,
                    "data_included": include_data
                },
                "audit_records": report_records,
                "format": report_format.value,
                "checksum_verification": self._verify_checksums(audit_records)
            }
            
            self.logger.info(f"Audit report generated with {total_events} events")
            return audit_report
            
        except Exception as e:
            self.logger.error(f"Error generating audit report: {str(e)}")
            raise

    def _calculate_checksum(self, audit_record: AuditRecord) -> str:
        """Calculate checksum for audit record integrity."""
        try:
            # Create record copy without checksum for calculation
            record_dict = asdict(audit_record)
            record_dict.pop("checksum", None)
            
            # Convert to JSON string (sorted keys for consistency)
            record_json = json.dumps(record_dict, sort_keys=True, default=str)
            
            # Calculate SHA-256 hash
            return hashlib.sha256(record_json.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating checksum: {str(e)}")
            return ""

    def _verify_checksums(self, audit_records: List[AuditRecord]) -> Dict[str, Any]:
        """Verify checksums for audit record integrity."""
        try:
            total_records = len(audit_records)
            verified_count = 0
            failed_verifications = []
            
            for record in audit_records:
                if not record.checksum:
                    continue
                
                # Recalculate checksum
                calculated_checksum = self._calculate_checksum(record)
                
                if calculated_checksum == record.checksum:
                    verified_count += 1
                else:
                    failed_verifications.append({
                        "record_id": record.record_id,
                        "expected": record.checksum,
                        "calculated": calculated_checksum
                    })
            
            return {
                "verification_performed": True,
                "total_records": total_records,
                "verified_records": verified_count,
                "failed_verifications": len(failed_verifications),
                "integrity_percentage": (verified_count / total_records * 100) if total_records > 0 else 0,
                "failed_records": failed_verifications
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying checksums: {str(e)}")
            return {"verification_performed": False, "error": str(e)}

    def _calculate_changes(
        self,
        data_before: Optional[Dict[str, Any]],
        data_after: Optional[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate changes between before and after data snapshots."""
        if not data_before and not data_after:
            return {}
        
        if not data_before:
            return {k: {"action": "added", "new_value": v} for k, v in (data_after or {}).items()}
        
        if not data_after:
            return {k: {"action": "removed", "old_value": v} for k, v in data_before.items()}
        
        changes = {}
        all_keys = set(data_before.keys()) | set(data_after.keys())
        
        for key in all_keys:
            if key not in data_before:
                changes[key] = {"action": "added", "new_value": data_after[key]}
            elif key not in data_after:
                changes[key] = {"action": "removed", "old_value": data_before[key]}
            elif data_before[key] != data_after[key]:
                changes[key] = {
                    "action": "modified",
                    "old_value": data_before[key],
                    "new_value": data_after[key]
                }
        
        return changes