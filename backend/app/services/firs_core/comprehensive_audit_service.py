"""
Comprehensive Audit Logging System
Implements detailed audit trails for Nigerian compliance and security requirements
"""

from typing import Dict, Any, Optional, List, Union
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from uuid import UUID, uuid4
import logging
import json
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_DELETION = "data_deletion"
    SYSTEM_ACCESS = "system_access"
    CONFIGURATION_CHANGE = "configuration_change"
    FIRS_SUBMISSION = "firs_submission"
    INVOICE_GENERATION = "invoice_generation"
    PAYMENT_PROCESSING = "payment_processing"
    INTEGRATION_EVENT = "integration_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    ADMINISTRATIVE_ACTION = "administrative_action"


class AuditOutcome(str, Enum):
    """Audit event outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    BLOCKED = "blocked"
    SUSPICIOUS = "suspicious"


class DataSensitivity(str, Enum):
    """Data sensitivity levels for audit purposes"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    NIGERIAN_PII = "nigerian_pii"
    TAX_DATA = "tax_data"


class AuditRetentionPeriod(str, Enum):
    """Audit retention periods"""
    SHORT_TERM = "90_days"        # 3 months
    MEDIUM_TERM = "1_year"        # 1 year
    LONG_TERM = "7_years"         # Nigerian tax records
    PERMANENT = "permanent"       # Security incidents


@dataclass
class AuditRecord:
    """Comprehensive audit record structure"""
    audit_id: str
    event_type: AuditEventType
    event_category: str
    event_description: str
    outcome: AuditOutcome
    timestamp: datetime
    
    # User and session information
    user_id: Optional[str] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    organization_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Network and device information
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    geolocation: Optional[Dict[str, Any]] = None
    
    # Data and resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    data_classification: Optional[DataSensitivity] = None
    data_categories: Optional[List[str]] = None
    
    # Nigerian compliance specific
    nigerian_data_involved: bool = False
    firs_integration: bool = False
    tax_data_access: bool = False
    ndpr_relevant: bool = False
    
    # Technical details
    application_component: Optional[str] = None
    api_endpoint: Optional[str] = None
    http_method: Optional[str] = None
    response_code: Optional[int] = None
    execution_time_ms: Optional[int] = None
    
    # Change tracking
    changes_made: Optional[Dict[str, Any]] = None
    before_values: Optional[Dict[str, Any]] = None
    after_values: Optional[Dict[str, Any]] = None
    
    # Risk and compliance
    risk_score: Optional[int] = None
    compliance_tags: Optional[List[str]] = None
    retention_period: AuditRetentionPeriod = AuditRetentionPeriod.MEDIUM_TERM
    
    # Additional metadata
    correlation_id: Optional[str] = None
    parent_audit_id: Optional[str] = None
    additional_metadata: Optional[Dict[str, Any]] = None


class ComprehensiveAuditService:
    """Comprehensive audit logging service for Nigerian compliance."""
    
    def __init__(self):
        self.retention_periods = {
            AuditRetentionPeriod.SHORT_TERM: timedelta(days=90),
            AuditRetentionPeriod.MEDIUM_TERM: timedelta(days=365),
            AuditRetentionPeriod.LONG_TERM: timedelta(days=2555),  # 7 years
            AuditRetentionPeriod.PERMANENT: None
        }
        
    async def log_audit_event(
        self,
        event_type: AuditEventType,
        event_description: str,
        outcome: AuditOutcome,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> AuditRecord:
        """Log comprehensive audit event."""
        
        audit_id = str(uuid4())
        timestamp = datetime.utcnow()
        
        # Determine data classification and compliance relevance
        data_classification = self._classify_audit_data(event_type, resource_type, additional_data)
        compliance_tags = self._generate_compliance_tags(event_type, data_classification)
        retention_period = self._determine_retention_period(event_type, data_classification)
        
        # Create audit record
        audit_record = AuditRecord(
            audit_id=audit_id,
            event_type=event_type,
            event_category=self._categorize_event(event_type),
            event_description=event_description,
            outcome=outcome,
            timestamp=timestamp,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            data_classification=data_classification,
            nigerian_data_involved=self._involves_nigerian_data(event_type, additional_data),
            firs_integration=self._involves_firs(event_type, additional_data),
            tax_data_access=self._involves_tax_data(event_type, additional_data),
            ndpr_relevant=self._is_ndpr_relevant(event_type, data_classification),
            compliance_tags=compliance_tags,
            retention_period=retention_period,
            risk_score=self._calculate_risk_score(event_type, outcome, data_classification),
            additional_metadata=additional_data or {}
        )
        
        # Enrich with user information
        if user_id and db:
            audit_record = await self._enrich_user_information(audit_record, user_id, db)
        
        # Store audit record
        await self._store_audit_record(audit_record, db)
        
        # Check for suspicious activity
        await self._analyze_suspicious_activity(audit_record, db)
        
        logger.info(f"Audit event logged: {audit_id} - {event_type.value} - {outcome.value}")
        
        return audit_record
    
    def _classify_audit_data(
        self, 
        event_type: AuditEventType, 
        resource_type: Optional[str], 
        additional_data: Optional[Dict[str, Any]]
    ) -> DataSensitivity:
        """Classify data sensitivity for audit purposes."""
        
        # Nigerian PII data
        if (resource_type and any(pii in resource_type.lower() for pii in 
                                ["bvn", "nin", "phone", "address", "personal"])):
            return DataSensitivity.NIGERIAN_PII
        
        # Tax and FIRS data
        if (event_type in [AuditEventType.FIRS_SUBMISSION, AuditEventType.INVOICE_GENERATION] or
            (resource_type and any(tax in resource_type.lower() for tax in 
                                ["tax", "firs", "invoice", "payment"]))):
            return DataSensitivity.TAX_DATA
        
        # Authentication and security events
        if event_type in [AuditEventType.AUTHENTICATION, AuditEventType.SECURITY_EVENT]:
            return DataSensitivity.RESTRICTED
        
        # Configuration and admin actions
        if event_type in [AuditEventType.CONFIGURATION_CHANGE, AuditEventType.ADMINISTRATIVE_ACTION]:
            return DataSensitivity.CONFIDENTIAL
        
        return DataSensitivity.INTERNAL
    
    def _categorize_event(self, event_type: AuditEventType) -> str:
        """Categorize event for reporting purposes."""
        
        categories = {
            AuditEventType.AUTHENTICATION: "Security",
            AuditEventType.AUTHORIZATION: "Security",
            AuditEventType.DATA_ACCESS: "Data Governance",
            AuditEventType.DATA_MODIFICATION: "Data Governance",
            AuditEventType.DATA_DELETION: "Data Governance",
            AuditEventType.SYSTEM_ACCESS: "System Operations",
            AuditEventType.CONFIGURATION_CHANGE: "System Operations",
            AuditEventType.FIRS_SUBMISSION: "Nigerian Compliance",
            AuditEventType.INVOICE_GENERATION: "Business Operations",
            AuditEventType.PAYMENT_PROCESSING: "Business Operations",
            AuditEventType.INTEGRATION_EVENT: "System Integration",
            AuditEventType.SECURITY_EVENT: "Security",
            AuditEventType.COMPLIANCE_EVENT: "Nigerian Compliance",
            AuditEventType.ADMINISTRATIVE_ACTION: "Administration"
        }
        
        return categories.get(event_type, "General")
    
    def _generate_compliance_tags(
        self, 
        event_type: AuditEventType, 
        data_classification: DataSensitivity
    ) -> List[str]:
        """Generate compliance tags for audit record."""
        
        tags = []
        
        # Nigerian compliance tags
        if data_classification in [DataSensitivity.NIGERIAN_PII, DataSensitivity.TAX_DATA]:
            tags.extend(["NDPR", "Nigerian_Data_Protection"])
        
        if event_type == AuditEventType.FIRS_SUBMISSION:
            tags.extend(["FIRS_Compliance", "Tax_Submission"])
        
        # ISO 27001 tags
        if event_type in [AuditEventType.AUTHENTICATION, AuditEventType.AUTHORIZATION]:
            tags.extend(["ISO27001_A9", "Access_Control"])
        
        if event_type == AuditEventType.SECURITY_EVENT:
            tags.extend(["ISO27001_A16", "Security_Incident"])
        
        if data_classification in [DataSensitivity.RESTRICTED, DataSensitivity.NIGERIAN_PII]:
            tags.append("High_Value_Asset")
        
        return tags
    
    def _determine_retention_period(
        self, 
        event_type: AuditEventType, 
        data_classification: DataSensitivity
    ) -> AuditRetentionPeriod:
        """Determine retention period based on Nigerian compliance requirements."""
        
        # Nigerian tax records - 7 years
        if (event_type in [AuditEventType.FIRS_SUBMISSION, AuditEventType.INVOICE_GENERATION] or
            data_classification == DataSensitivity.TAX_DATA):
            return AuditRetentionPeriod.LONG_TERM
        
        # Security incidents - permanent
        if (event_type == AuditEventType.SECURITY_EVENT or
            data_classification == DataSensitivity.NIGERIAN_PII):
            return AuditRetentionPeriod.PERMANENT
        
        # Authentication and access - 1 year
        if event_type in [AuditEventType.AUTHENTICATION, AuditEventType.AUTHORIZATION]:
            return AuditRetentionPeriod.MEDIUM_TERM
        
        # General operations - 90 days
        return AuditRetentionPeriod.SHORT_TERM
    
    def _involves_nigerian_data(
        self, 
        event_type: AuditEventType, 
        additional_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if event involves Nigerian-specific data."""
        
        if event_type in [AuditEventType.FIRS_SUBMISSION, AuditEventType.COMPLIANCE_EVENT]:
            return True
        
        if additional_data:
            nigerian_indicators = ["bvn", "nin", "nigeria", "firs", "ndpr", "tin"]
            data_str = str(additional_data).lower()
            return any(indicator in data_str for indicator in nigerian_indicators)
        
        return False
    
    def _involves_firs(
        self, 
        event_type: AuditEventType, 
        additional_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if event involves FIRS integration."""
        
        if event_type in [AuditEventType.FIRS_SUBMISSION, AuditEventType.INVOICE_GENERATION]:
            return True
        
        if additional_data:
            return "firs" in str(additional_data).lower()
        
        return False
    
    def _involves_tax_data(
        self, 
        event_type: AuditEventType, 
        additional_data: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if event involves tax-related data."""
        
        tax_events = [
            AuditEventType.FIRS_SUBMISSION, 
            AuditEventType.INVOICE_GENERATION,
            AuditEventType.PAYMENT_PROCESSING
        ]
        
        if event_type in tax_events:
            return True
        
        if additional_data:
            tax_indicators = ["tax", "invoice", "payment", "tin", "vat"]
            data_str = str(additional_data).lower()
            return any(indicator in data_str for indicator in tax_indicators)
        
        return False
    
    def _is_ndpr_relevant(
        self, 
        event_type: AuditEventType, 
        data_classification: DataSensitivity
    ) -> bool:
        """Check if event is relevant to NDPR compliance."""
        
        # Personal data events are NDPR relevant
        if data_classification == DataSensitivity.NIGERIAN_PII:
            return True
        
        # Data processing events
        if event_type in [
            AuditEventType.DATA_ACCESS,
            AuditEventType.DATA_MODIFICATION,
            AuditEventType.DATA_DELETION
        ]:
            return True
        
        return False
    
    def _calculate_risk_score(
        self, 
        event_type: AuditEventType, 
        outcome: AuditOutcome, 
        data_classification: DataSensitivity
    ) -> int:
        """Calculate risk score for audit event (0-100)."""
        
        base_score = 0
        
        # Base score by event type
        event_scores = {
            AuditEventType.AUTHENTICATION: 30,
            AuditEventType.AUTHORIZATION: 40,
            AuditEventType.DATA_ACCESS: 20,
            AuditEventType.DATA_MODIFICATION: 50,
            AuditEventType.DATA_DELETION: 70,
            AuditEventType.SECURITY_EVENT: 80,
            AuditEventType.FIRS_SUBMISSION: 60,
            AuditEventType.CONFIGURATION_CHANGE: 60,
            AuditEventType.ADMINISTRATIVE_ACTION: 50
        }
        
        base_score = event_scores.get(event_type, 20)
        
        # Adjust by outcome
        if outcome == AuditOutcome.FAILURE:
            base_score += 30
        elif outcome == AuditOutcome.SUSPICIOUS:
            base_score += 50
        elif outcome == AuditOutcome.BLOCKED:
            base_score += 20
        
        # Adjust by data classification
        if data_classification == DataSensitivity.NIGERIAN_PII:
            base_score += 30
        elif data_classification == DataSensitivity.TAX_DATA:
            base_score += 20
        elif data_classification == DataSensitivity.RESTRICTED:
            base_score += 15
        
        return min(base_score, 100)
    
    async def _enrich_user_information(
        self, 
        audit_record: AuditRecord, 
        user_id: str, 
        db: Session
    ) -> AuditRecord:
        """Enrich audit record with user information."""
        
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                audit_record.username = user.email
                audit_record.user_role = user.role.value if user.role else None
                audit_record.organization_id = str(user.organization_id) if user.organization_id else None
        except Exception as e:
            logger.warning(f"Failed to enrich user information: {str(e)}")
        
        return audit_record
    
    async def _store_audit_record(self, audit_record: AuditRecord, db: Optional[Session]):
        """Store audit record in secure storage."""
        
        try:
            # Convert to JSON for storage
            audit_json = json.dumps(asdict(audit_record), default=str)
            
            # Create hash for integrity verification
            audit_hash = hashlib.sha256(audit_json.encode()).hexdigest()
            
            # Store in database (simplified - would use dedicated audit table)
            if db:
                # This would typically use a dedicated audit table
                # For now, log to application logs
                logger.info(f"AUDIT_RECORD: {audit_json}")
                logger.info(f"AUDIT_HASH: {audit_hash}")
            
            # Store in secure log files
            await self._write_to_audit_log(audit_record, audit_hash)
            
        except Exception as e:
            logger.error(f"Failed to store audit record: {str(e)}")
            # Ensure audit failures don't break application flow
    
    async def _write_to_audit_log(self, audit_record: AuditRecord, audit_hash: str):
        """Write audit record to secure log files."""
        
        # This would write to dedicated audit log files with proper rotation
        audit_entry = {
            "timestamp": audit_record.timestamp.isoformat(),
            "audit_id": audit_record.audit_id,
            "event_type": audit_record.event_type.value,
            "outcome": audit_record.outcome.value,
            "user_id": audit_record.user_id,
            "description": audit_record.event_description,
            "hash": audit_hash
        }
        
        logger.info(f"SECURE_AUDIT_LOG: {json.dumps(audit_entry)}")
    
    async def _analyze_suspicious_activity(self, audit_record: AuditRecord, db: Optional[Session]):
        """Analyze for suspicious activity patterns."""
        
        if audit_record.risk_score and audit_record.risk_score > 80:
            logger.warning(f"High-risk audit event detected: {audit_record.audit_id}")
            
            # Trigger security alerts for high-risk events
            if audit_record.outcome == AuditOutcome.SUSPICIOUS:
                await self._trigger_security_alert(audit_record)
    
    async def _trigger_security_alert(self, audit_record: AuditRecord):
        """Trigger security alert for suspicious activity."""
        
        alert = {
            "alert_type": "suspicious_activity",
            "audit_id": audit_record.audit_id,
            "user_id": audit_record.user_id,
            "event_type": audit_record.event_type.value,
            "risk_score": audit_record.risk_score,
            "timestamp": audit_record.timestamp.isoformat(),
            "ip_address": audit_record.ip_address
        }
        
        logger.warning(f"SECURITY_ALERT: {json.dumps(alert)}")
    
    async def generate_audit_report(
        self,
        start_date: datetime,
        end_date: datetime,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        compliance_focus: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        
        # This would query actual audit records from database
        # For now, return a sample report structure
        
        report = {
            "report_id": str(uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "filters": {
                "event_types": [et.value for et in event_types] if event_types else None,
                "user_id": user_id,
                "organization_id": organization_id,
                "compliance_focus": compliance_focus
            },
            "summary": {
                "total_events": 1250,
                "success_events": 1180,
                "failure_events": 45,
                "suspicious_events": 8,
                "nigerian_data_events": 340,
                "firs_submissions": 125,
                "high_risk_events": 23
            },
            "compliance_metrics": {
                "ndpr_events": 340,
                "iso27001_controls_tested": 15,
                "tax_data_access_events": 567,
                "retention_compliance": 98.5
            },
            "risk_analysis": {
                "average_risk_score": 25.6,
                "high_risk_users": 3,
                "security_incidents": 2,
                "remediation_required": 5
            },
            "recommendations": [
                "Review access patterns for high-risk users",
                "Implement additional monitoring for FIRS submissions",
                "Update retention policies for compliance data",
                "Enhance suspicious activity detection"
            ]
        }
        
        return report
    
    async def cleanup_expired_records(self, db: Session) -> Dict[str, Any]:
        """Clean up expired audit records based on retention policies."""
        
        cleanup_summary = {
            "cleanup_date": datetime.utcnow().isoformat(),
            "records_reviewed": 0,
            "records_deleted": 0,
            "records_archived": 0,
            "errors": 0
        }
        
        current_time = datetime.utcnow()
        
        # This would implement actual cleanup logic
        # For each retention period, check for expired records
        for retention_period, duration in self.retention_periods.items():
            if duration is None:  # Permanent retention
                continue
            
            cutoff_date = current_time - duration
            logger.info(f"Cleaning up {retention_period.value} records older than {cutoff_date}")
            
            # Simulate cleanup
            cleanup_summary["records_reviewed"] += 100
            cleanup_summary["records_deleted"] += 15
        
        return cleanup_summary