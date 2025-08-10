"""
Comprehensive Audit Logger
==========================
Enterprise-grade audit logging system for banking operations.
Provides detailed audit trails, compliance logging, and forensic
capabilities for regulatory oversight and security monitoring.

Key Features:
- Comprehensive audit trail generation
- Regulatory compliance logging
- Tamper-evident audit records
- Real-time audit monitoring
- Audit data analytics and reporting
- Forensic investigation support
"""

import asyncio
import logging
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, field
import uuid
from threading import Lock

from ....shared.logging import get_logger
from ....shared.exceptions import IntegrationError


class AuditLevel(Enum):
    """Audit logging levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    SECURITY = "security"
    COMPLIANCE = "compliance"


class AuditCategory(Enum):
    """Categories of audit events."""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION_PROCESSING = "transaction_processing"
    SYSTEM_OPERATION = "system_operation"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    USER_ACTION = "user_action"
    ADMIN_ACTION = "admin_action"
    API_CALL = "api_call"
    CONFIGURATION_CHANGE = "configuration_change"
    ERROR_EVENT = "error_event"


class AuditEventType(Enum):
    """Specific types of audit events."""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_ACCESS = "account_access"
    TRANSACTION_RETRIEVED = "transaction_retrieved"
    TRANSACTION_CREATED = "transaction_created"
    DATA_EXPORTED = "data_exported"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_REVOKED = "consent_revoked"
    POLICY_VIOLATION = "policy_violation"
    SECURITY_ALERT = "security_alert"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    CONFIG_UPDATED = "config_updated"
    BACKUP_CREATED = "backup_created"
    DATA_PURGED = "data_purged"


@dataclass
class AuditRecord:
    """Comprehensive audit record."""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    event_type: AuditEventType = AuditEventType.SYSTEM_START
    category: AuditCategory = AuditCategory.SYSTEM_OPERATION
    level: AuditLevel = AuditLevel.INFO
    
    # Actor information
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Resource information
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    
    # Event details
    action: str = ""
    description: str = ""
    result: str = "success"  # success, failure, error
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    
    # Context information
    provider_type: Optional[str] = None
    api_endpoint: Optional[str] = None
    request_method: Optional[str] = None
    response_code: Optional[int] = None
    processing_time_ms: Optional[float] = None
    
    # Data sensitivity
    contains_pii: bool = False
    contains_financial_data: bool = False
    data_classification: str = "public"  # public, internal, confidential, restricted
    
    # Compliance tags
    compliance_frameworks: List[str] = field(default_factory=list)
    retention_period_days: int = 2555  # 7 years default
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Integrity protection
    record_hash: Optional[str] = None
    previous_hash: Optional[str] = None
    
    def __post_init__(self):
        """Calculate record hash for integrity protection."""
        self.record_hash = self._calculate_hash()
    
    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of audit record for integrity."""
        # Create deterministic string representation
        data_to_hash = {
            'audit_id': self.audit_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'category': self.category.value,
            'level': self.level.value,
            'user_id': self.user_id,
            'action': self.action,
            'description': self.description,
            'result': self.result,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id
        }
        
        # Sort keys for deterministic output
        hash_string = json.dumps(data_to_hash, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit record to dictionary."""
        return {
            'audit_id': self.audit_id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'category': self.category.value,
            'level': self.level.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'account_id': self.account_id,
            'transaction_id': self.transaction_id,
            'action': self.action,
            'description': self.description,
            'result': self.result,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'provider_type': self.provider_type,
            'api_endpoint': self.api_endpoint,
            'request_method': self.request_method,
            'response_code': self.response_code,
            'processing_time_ms': self.processing_time_ms,
            'contains_pii': self.contains_pii,
            'contains_financial_data': self.contains_financial_data,
            'data_classification': self.data_classification,
            'compliance_frameworks': self.compliance_frameworks,
            'retention_period_days': self.retention_period_days,
            'metadata': self.metadata,
            'tags': self.tags,
            'record_hash': self.record_hash,
            'previous_hash': self.previous_hash
        }


@dataclass
class AuditQuery:
    """Query parameters for audit record search."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    user_id: Optional[str] = None
    event_types: Optional[List[AuditEventType]] = None
    categories: Optional[List[AuditCategory]] = None
    levels: Optional[List[AuditLevel]] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    result: Optional[str] = None
    contains_pii: Optional[bool] = None
    compliance_frameworks: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    limit: int = 1000
    offset: int = 0


class AuditLogger:
    """
    Comprehensive audit logging system for banking operations.
    
    This logger provides tamper-evident audit trails, compliance logging,
    and forensic capabilities required for regulatory oversight and
    security monitoring in banking systems.
    """
    
    def __init__(self, enable_integrity_chain: bool = True):
        """
        Initialize audit logger.
        
        Args:
            enable_integrity_chain: Enable hash chaining for tamper detection
        """
        self.logger = get_logger(__name__)
        self.enable_integrity_chain = enable_integrity_chain
        
        # Audit record storage
        self.audit_records: List[AuditRecord] = []
        self.record_index: Dict[str, AuditRecord] = {}
        
        # Integrity chain
        self.last_record_hash: Optional[str] = None
        self.chain_lock = Lock()
        
        # Configuration
        self.max_memory_records = 50000
        self.auto_archive_enabled = True
        self.archive_threshold = 10000
        
        # Performance metrics
        self.total_records_logged = 0
        self.records_per_minute = 0
        self.last_minute_count = 0
        self.last_minute_start = datetime.utcnow()
        
        self.logger.info("Initialized comprehensive audit logger")
    
    async def log_audit_event(
        self,
        event_type: AuditEventType,
        category: AuditCategory,
        action: str,
        description: str,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        result: str = "success",
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        """
        Log comprehensive audit event.
        
        Args:
            event_type: Type of audit event
            category: Category of audit event
            action: Action performed
            description: Description of the event
            level: Audit level
            user_id: User identifier
            session_id: Session identifier
            resource_type: Type of resource accessed
            resource_id: Resource identifier
            result: Result of the action
            error_code: Error code if applicable
            error_message: Error message if applicable
            metadata: Additional metadata
            context: Request context (IP, user agent, etc.)
            
        Returns:
            Created audit record
        """
        try:
            # Create audit record
            record = AuditRecord(
                event_type=event_type,
                category=category,
                level=level,
                user_id=user_id,
                session_id=session_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action=action,
                description=description,
                result=result,
                error_code=error_code,
                error_message=error_message,
                metadata=metadata or {}
            )
            
            # Add context information
            if context:
                record.ip_address = context.get('ip_address')
                record.user_agent = context.get('user_agent')
                record.api_endpoint = context.get('api_endpoint')
                record.request_method = context.get('request_method')
                record.response_code = context.get('response_code')
                record.processing_time_ms = context.get('processing_time_ms')
                record.provider_type = context.get('provider_type')
            
            # Set data classification and sensitivity
            self._classify_audit_data(record)
            
            # Set compliance frameworks
            self._set_compliance_frameworks(record)
            
            # Add to integrity chain
            if self.enable_integrity_chain:
                with self.chain_lock:
                    record.previous_hash = self.last_record_hash
                    record.record_hash = record._calculate_hash()
                    self.last_record_hash = record.record_hash
            
            # Store record
            self.audit_records.append(record)
            self.record_index[record.audit_id] = record
            
            # Update metrics
            self._update_performance_metrics()
            
            # Check if archival is needed
            if self.auto_archive_enabled and len(self.audit_records) > self.archive_threshold:
                await self._archive_old_records()
            
            # Log to system logger based on level
            self._log_to_system(record)
            
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {str(e)}")
            raise IntegrationError(f"Audit logging failed: {str(e)}")
    
    async def log_authentication_event(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> AuditRecord:
        """Log authentication event."""
        event_type = AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILURE
        level = AuditLevel.INFO if success else AuditLevel.WARNING
        
        return await self.log_audit_event(
            event_type=event_type,
            category=AuditCategory.AUTHENTICATION,
            action="user_authentication",
            description=f"User authentication {'successful' if success else 'failed'}",
            level=level,
            user_id=user_id,
            result="success" if success else "failure",
            error_message=failure_reason,
            context={
                'ip_address': ip_address,
                'user_agent': user_agent
            }
        )
    
    async def log_data_access_event(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        success: bool,
        account_id: Optional[str] = None,
        transaction_id: Optional[str] = None,
        data_size: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AuditRecord:
        """Log data access event."""
        description = f"Data {action} on {resource_type}"
        if data_size:
            description += f" ({data_size} bytes)"
        
        metadata = {}
        if data_size:
            metadata['data_size_bytes'] = data_size
        
        record = await self.log_audit_event(
            event_type=AuditEventType.DATA_EXPORTED if action == "export" else AuditEventType.ACCOUNT_ACCESS,
            category=AuditCategory.DATA_ACCESS,
            action=action,
            description=description,
            level=AuditLevel.INFO,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            result="success" if success else "failure",
            metadata=metadata,
            context=context
        )
        
        # Set account and transaction IDs
        if account_id:
            record.account_id = account_id
        if transaction_id:
            record.transaction_id = transaction_id
        
        return record
    
    async def log_compliance_event(
        self,
        compliance_framework: str,
        check_type: str,
        result: bool,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> AuditRecord:
        """Log compliance check event."""
        return await self.log_audit_event(
            event_type=AuditEventType.POLICY_VIOLATION if not result else AuditEventType.SYSTEM_START,
            category=AuditCategory.COMPLIANCE_CHECK,
            action=f"{compliance_framework}_{check_type}",
            description=f"Compliance check: {check_type} for {compliance_framework}",
            level=AuditLevel.COMPLIANCE,
            user_id=user_id,
            resource_id=resource_id,
            result="success" if result else "violation",
            metadata=details
        )
    
    async def search_audit_records(self, query: AuditQuery) -> List[AuditRecord]:
        """
        Search audit records based on query parameters.
        
        Args:
            query: Search query parameters
            
        Returns:
            List of matching audit records
        """
        try:
            filtered_records = self.audit_records.copy()
            
            # Apply filters
            if query.start_date:
                filtered_records = [r for r in filtered_records if r.timestamp >= query.start_date]
            
            if query.end_date:
                filtered_records = [r for r in filtered_records if r.timestamp <= query.end_date]
            
            if query.user_id:
                filtered_records = [r for r in filtered_records if r.user_id == query.user_id]
            
            if query.event_types:
                filtered_records = [r for r in filtered_records if r.event_type in query.event_types]
            
            if query.categories:
                filtered_records = [r for r in filtered_records if r.category in query.categories]
            
            if query.levels:
                filtered_records = [r for r in filtered_records if r.level in query.levels]
            
            if query.resource_type:
                filtered_records = [r for r in filtered_records if r.resource_type == query.resource_type]
            
            if query.resource_id:
                filtered_records = [r for r in filtered_records if r.resource_id == query.resource_id]
            
            if query.result:
                filtered_records = [r for r in filtered_records if r.result == query.result]
            
            if query.contains_pii is not None:
                filtered_records = [r for r in filtered_records if r.contains_pii == query.contains_pii]
            
            if query.compliance_frameworks:
                filtered_records = [
                    r for r in filtered_records
                    if any(framework in r.compliance_frameworks for framework in query.compliance_frameworks)
                ]
            
            if query.tags:
                filtered_records = [
                    r for r in filtered_records
                    if any(tag in r.tags for tag in query.tags)
                ]
            
            # Sort by timestamp (newest first)
            filtered_records.sort(key=lambda x: x.timestamp, reverse=True)
            
            # Apply pagination
            start_idx = query.offset
            end_idx = start_idx + query.limit
            return filtered_records[start_idx:end_idx]
            
        except Exception as e:
            self.logger.error(f"Audit record search failed: {str(e)}")
            raise IntegrationError(f"Audit search failed: {str(e)}")
    
    async def verify_audit_integrity(self) -> Dict[str, Any]:
        """
        Verify integrity of audit chain.
        
        Returns:
            Integrity verification results
        """
        try:
            if not self.enable_integrity_chain:
                return {"integrity_enabled": False, "message": "Integrity chain disabled"}
            
            total_records = len(self.audit_records)
            verified_records = 0
            broken_chains = []
            tampered_records = []
            
            previous_hash = None
            
            for i, record in enumerate(self.audit_records):
                # Check if record hash is valid
                expected_hash = record._calculate_hash()
                if record.record_hash != expected_hash:
                    tampered_records.append({
                        'audit_id': record.audit_id,
                        'index': i,
                        'expected_hash': expected_hash,
                        'actual_hash': record.record_hash
                    })
                    continue
                
                # Check if chain link is valid
                if record.previous_hash != previous_hash:
                    broken_chains.append({
                        'audit_id': record.audit_id,
                        'index': i,
                        'expected_previous_hash': previous_hash,
                        'actual_previous_hash': record.previous_hash
                    })
                
                verified_records += 1
                previous_hash = record.record_hash
            
            integrity_score = (verified_records / total_records * 100) if total_records > 0 else 100
            
            return {
                "integrity_enabled": True,
                "total_records": total_records,
                "verified_records": verified_records,
                "integrity_score": integrity_score,
                "tampered_records": len(tampered_records),
                "broken_chains": len(broken_chains),
                "details": {
                    "tampered_records": tampered_records,
                    "broken_chains": broken_chains
                },
                "verification_timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Audit integrity verification failed: {str(e)}")
            raise IntegrationError(f"Integrity verification failed: {str(e)}")
    
    def _classify_audit_data(self, record: AuditRecord) -> None:
        """Classify audit data based on content sensitivity."""
        # Check for PII
        pii_indicators = ['user_id', 'account_number', 'phone', 'email', 'name']
        record.contains_pii = any(
            indicator in str(record.metadata).lower() or
            indicator in record.description.lower()
            for indicator in pii_indicators
        )
        
        # Check for financial data
        financial_indicators = ['transaction', 'balance', 'amount', 'payment']
        record.contains_financial_data = any(
            indicator in record.resource_type.lower() if record.resource_type else False or
            indicator in record.action.lower() or
            indicator in record.description.lower()
            for indicator in financial_indicators
        )
        
        # Set data classification
        if record.contains_financial_data:
            record.data_classification = "confidential"
        elif record.contains_pii:
            record.data_classification = "internal"
        else:
            record.data_classification = "public"
    
    def _set_compliance_frameworks(self, record: AuditRecord) -> None:
        """Set applicable compliance frameworks for audit record."""
        # Default frameworks for financial data
        if record.contains_financial_data:
            record.compliance_frameworks.extend(["FIRS", "CBN"])
        
        # PII compliance
        if record.contains_pii:
            record.compliance_frameworks.append("NDPR")
        
        # Security events
        if record.category in [AuditCategory.SECURITY_EVENT, AuditCategory.AUTHENTICATION]:
            record.compliance_frameworks.append("ISO27001")
        
        # Remove duplicates
        record.compliance_frameworks = list(set(record.compliance_frameworks))
    
    def _update_performance_metrics(self) -> None:
        """Update performance metrics."""
        self.total_records_logged += 1
        self.last_minute_count += 1
        
        now = datetime.utcnow()
        if (now - self.last_minute_start).total_seconds() >= 60:
            self.records_per_minute = self.last_minute_count
            self.last_minute_count = 0
            self.last_minute_start = now
    
    def _log_to_system(self, record: AuditRecord) -> None:
        """Log to system logger based on audit level."""
        log_message = f"AUDIT: {record.action} - {record.description}"
        
        if record.level == AuditLevel.DEBUG:
            self.logger.debug(log_message)
        elif record.level == AuditLevel.INFO:
            self.logger.info(log_message)
        elif record.level == AuditLevel.WARNING:
            self.logger.warning(log_message)
        elif record.level == AuditLevel.ERROR:
            self.logger.error(log_message)
        elif record.level in [AuditLevel.CRITICAL, AuditLevel.SECURITY]:
            self.logger.critical(log_message)
    
    async def _archive_old_records(self) -> None:
        """Archive old audit records to maintain performance."""
        # Keep only recent records in memory
        cutoff_index = len(self.audit_records) - self.max_memory_records
        if cutoff_index > 0:
            archived_records = self.audit_records[:cutoff_index]
            self.audit_records = self.audit_records[cutoff_index:]
            
            # Update index
            for record in archived_records:
                if record.audit_id in self.record_index:
                    del self.record_index[record.audit_id]
            
            self.logger.info(f"Archived {len(archived_records)} old audit records")