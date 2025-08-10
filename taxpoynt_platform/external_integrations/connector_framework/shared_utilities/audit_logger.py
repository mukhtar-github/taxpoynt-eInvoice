"""
Compliance and Audit Logging
============================

Comprehensive audit logging for financial service integrations.
Ensures regulatory compliance and provides detailed audit trails.
"""

import logging
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class AuditEventType(str, Enum):
    """Types of audit events"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_UPDATED = "transaction_updated"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    CLASSIFICATION_PERFORMED = "classification_performed"
    API_CALL = "api_call"
    CONFIGURATION_CHANGED = "configuration_changed"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_CHECK = "compliance_check"
    ERROR_OCCURRED = "error_occurred"

class ComplianceFramework(str, Enum):
    """Compliance frameworks"""
    NDPR = "ndpr"  # Nigeria Data Protection Regulation
    FIRS = "firs"  # Federal Inland Revenue Service
    CBN = "cbn"   # Central Bank of Nigeria
    PCI_DSS = "pci_dss"  # Payment Card Industry Data Security Standard
    SOX = "sox"   # Sarbanes-Oxley Act
    GDPR = "gdpr"  # General Data Protection Regulation

class AuditLevel(str, Enum):
    """Audit logging levels"""
    BASIC = "basic"
    DETAILED = "detailed"
    COMPREHENSIVE = "comprehensive"
    DEBUG = "debug"

@dataclass
class UserContext:
    """User context for audit logging"""
    
    user_id: str
    username: Optional[str] = None
    role: Optional[str] = None
    organization_id: Optional[str] = None
    
    # Session information
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Authentication
    authentication_method: Optional[str] = None
    mfa_enabled: bool = False

@dataclass
class SystemContext:
    """System context for audit logging"""
    
    service_name: str
    operation: str
    version: str = "1.0.0"
    
    # Infrastructure
    server_id: Optional[str] = None
    environment: str = "production"
    region: Optional[str] = None
    
    # Request tracking
    request_id: Optional[str] = None
    correlation_id: Optional[str] = None
    trace_id: Optional[str] = None

@dataclass
class DataContext:
    """Data context for audit logging"""
    
    # Data identification
    data_type: str
    record_id: Optional[str] = None
    table_name: Optional[str] = None
    
    # Data sensitivity
    contains_pii: bool = False
    contains_financial_data: bool = False
    data_classification: str = "internal"
    
    # Changes
    fields_modified: List[str] = field(default_factory=list)
    before_values: Dict[str, Any] = field(default_factory=dict)
    after_values: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditEvent:
    """Comprehensive audit event"""
    
    # Event identification
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    
    # Context
    user_context: Optional[UserContext] = None
    system_context: Optional[SystemContext] = None
    data_context: Optional[DataContext] = None
    
    # Event details
    description: str
    outcome: str = "success"  # success, failure, warning
    
    # Compliance
    compliance_frameworks: List[ComplianceFramework] = field(default_factory=list)
    retention_period_days: int = 2555  # 7 years default
    
    # Technical details
    request_payload: Optional[Dict[str, Any]] = None
    response_payload: Optional[Dict[str, Any]] = None
    error_details: Optional[Dict[str, Any]] = None
    
    # Security
    risk_score: int = 0  # 0-100
    security_flags: List[str] = field(default_factory=list)
    
    # Additional metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Integrity
    checksum: Optional[str] = None

class AuditLogger:
    """Main audit logging class"""
    
    def __init__(self, 
                 service_name: str,
                 audit_level: AuditLevel = AuditLevel.DETAILED,
                 log_file_path: Optional[str] = None,
                 enable_encryption: bool = True):
        
        self.service_name = service_name
        self.audit_level = audit_level
        self.enable_encryption = enable_encryption
        
        # Configure logger
        self.logger = logging.getLogger(f"audit.{service_name}")
        self.logger.setLevel(logging.INFO)
        
        # Setup file handler if path provided
        if log_file_path:
            self._setup_file_logging(log_file_path)
        
        # Event counter for unique IDs
        self.event_counter = 0
        
        # Compliance mappings
        self.compliance_mappings = {
            AuditEventType.DATA_ACCESS: [ComplianceFramework.NDPR, ComplianceFramework.GDPR],
            AuditEventType.DATA_MODIFICATION: [ComplianceFramework.NDPR, ComplianceFramework.GDPR],
            AuditEventType.TRANSACTION_CREATED: [ComplianceFramework.FIRS, ComplianceFramework.CBN],
            AuditEventType.PAYMENT_INITIATED: [ComplianceFramework.CBN, ComplianceFramework.PCI_DSS],
            AuditEventType.CLASSIFICATION_PERFORMED: [ComplianceFramework.FIRS],
        }
        
        self.logger.info(f"Audit logger initialized for {service_name}")
    
    def _setup_file_logging(self, log_file_path: str):
        """Setup file-based audit logging"""
        
        # Create directory if needed
        log_path = Path(log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    async def log_event(self, 
                       event_type: AuditEventType,
                       description: str,
                       user_context: Optional[UserContext] = None,
                       system_context: Optional[SystemContext] = None,
                       data_context: Optional[DataContext] = None,
                       outcome: str = "success",
                       **kwargs) -> str:
        """Log an audit event"""
        
        # Generate event ID
        self.event_counter += 1
        event_id = f"{self.service_name}_{int(datetime.utcnow().timestamp())}_{self.event_counter:06d}"
        
        # Create system context if not provided
        if system_context is None:
            system_context = SystemContext(
                service_name=self.service_name,
                operation=kwargs.get('operation', 'unknown')
            )
        
        # Determine compliance frameworks
        compliance_frameworks = self.compliance_mappings.get(event_type, [])
        
        # Create audit event
        audit_event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_context=user_context,
            system_context=system_context,
            data_context=data_context,
            description=description,
            outcome=outcome,
            compliance_frameworks=compliance_frameworks,
            **{k: v for k, v in kwargs.items() if k in AuditEvent.__dataclass_fields__}
        )
        
        # Calculate checksum for integrity
        audit_event.checksum = self._calculate_checksum(audit_event)
        
        # Log the event
        await self._write_audit_log(audit_event)
        
        return event_id
    
    async def log_user_login(self, 
                           user_context: UserContext,
                           success: bool = True,
                           failure_reason: Optional[str] = None) -> str:
        """Log user login event"""
        
        description = f"User {user_context.username or user_context.user_id} login attempt"
        outcome = "success" if success else "failure"
        
        error_details = None
        if not success and failure_reason:
            error_details = {"failure_reason": failure_reason}
        
        return await self.log_event(
            event_type=AuditEventType.USER_LOGIN,
            description=description,
            user_context=user_context,
            outcome=outcome,
            error_details=error_details,
            security_flags=[] if success else ["authentication_failure"]
        )
    
    async def log_data_access(self,
                            user_context: UserContext,
                            data_context: DataContext,
                            operation: str = "read") -> str:
        """Log data access event"""
        
        system_context = SystemContext(
            service_name=self.service_name,
            operation=operation
        )
        
        description = f"Data access: {data_context.data_type}"
        if data_context.record_id:
            description += f" (ID: {data_context.record_id})"
        
        # Calculate risk score
        risk_score = 0
        if data_context.contains_pii:
            risk_score += 30
        if data_context.contains_financial_data:
            risk_score += 40
        if data_context.data_classification == "confidential":
            risk_score += 20
        
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            description=description,
            user_context=user_context,
            system_context=system_context,
            data_context=data_context,
            risk_score=risk_score
        )
    
    async def log_transaction_event(self,
                                  user_context: UserContext,
                                  transaction_id: str,
                                  amount: Decimal,
                                  currency: str = "NGN",
                                  transaction_type: str = "payment",
                                  counterparty: Optional[str] = None) -> str:
        """Log transaction-related event"""
        
        system_context = SystemContext(
            service_name=self.service_name,
            operation="transaction_processing"
        )
        
        data_context = DataContext(
            data_type="financial_transaction",
            record_id=transaction_id,
            contains_financial_data=True,
            data_classification="confidential"
        )
        
        description = f"Transaction {transaction_type}: {currency} {amount}"
        if counterparty:
            description += f" to/from {counterparty}"
        
        metadata = {
            "transaction_id": transaction_id,
            "amount": str(amount),
            "currency": currency,
            "transaction_type": transaction_type,
            "counterparty": counterparty
        }
        
        return await self.log_event(
            event_type=AuditEventType.TRANSACTION_CREATED,
            description=description,
            user_context=user_context,
            system_context=system_context,
            data_context=data_context,
            risk_score=50,  # Financial transactions are medium risk
            metadata=metadata
        )
    
    async def log_classification_event(self,
                                     user_context: UserContext,
                                     transaction_data: Dict[str, Any],
                                     classification_result: Dict[str, Any],
                                     confidence_score: float) -> str:
        """Log transaction classification event"""
        
        system_context = SystemContext(
            service_name=self.service_name,
            operation="transaction_classification"
        )
        
        data_context = DataContext(
            data_type="transaction_classification",
            contains_financial_data=True,
            data_classification="internal"
        )
        
        description = f"Transaction classified as {'business' if classification_result.get('is_business_income') else 'personal'}"
        description += f" (confidence: {confidence_score:.2f})"
        
        # Sanitize transaction data for logging
        sanitized_data = self._sanitize_for_logging(transaction_data)
        
        metadata = {
            "classification_result": classification_result,
            "confidence_score": confidence_score,
            "transaction_data": sanitized_data
        }
        
        return await self.log_event(
            event_type=AuditEventType.CLASSIFICATION_PERFORMED,
            description=description,
            user_context=user_context,
            system_context=system_context,
            data_context=data_context,
            metadata=metadata
        )
    
    async def log_api_call(self,
                          user_context: Optional[UserContext],
                          endpoint: str,
                          method: str,
                          status_code: int,
                          response_time_ms: float,
                          request_size: Optional[int] = None,
                          response_size: Optional[int] = None) -> str:
        """Log API call event"""
        
        system_context = SystemContext(
            service_name=self.service_name,
            operation="api_call"
        )
        
        description = f"{method} {endpoint} -> {status_code} ({response_time_ms:.2f}ms)"
        outcome = "success" if 200 <= status_code < 400 else "failure"
        
        metadata = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "request_size": request_size,
            "response_size": response_size
        }
        
        return await self.log_event(
            event_type=AuditEventType.API_CALL,
            description=description,
            user_context=user_context,
            system_context=system_context,
            outcome=outcome,
            metadata=metadata
        )
    
    async def log_security_event(self,
                               event_description: str,
                               severity: str = "medium",
                               user_context: Optional[UserContext] = None,
                               threat_indicators: Optional[List[str]] = None) -> str:
        """Log security-related event"""
        
        system_context = SystemContext(
            service_name=self.service_name,
            operation="security_monitoring"
        )
        
        # Calculate risk score based on severity
        risk_scores = {
            "low": 25,
            "medium": 50,
            "high": 75,
            "critical": 100
        }
        risk_score = risk_scores.get(severity, 50)
        
        security_flags = [f"severity_{severity}"]
        if threat_indicators:
            security_flags.extend(threat_indicators)
        
        metadata = {
            "severity": severity,
            "threat_indicators": threat_indicators or []
        }
        
        return await self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            description=event_description,
            user_context=user_context,
            system_context=system_context,
            outcome="warning" if severity in ["medium", "high"] else "failure",
            risk_score=risk_score,
            security_flags=security_flags,
            metadata=metadata
        )
    
    async def _write_audit_log(self, audit_event: AuditEvent):
        """Write audit event to log"""
        
        # Convert to dictionary for logging
        event_dict = self._event_to_dict(audit_event)
        
        # Apply audit level filtering
        if self.audit_level == AuditLevel.BASIC:
            # Only include essential fields
            filtered_dict = {
                k: v for k, v in event_dict.items()
                if k in ['event_id', 'event_type', 'timestamp', 'description', 'outcome']
            }
        elif self.audit_level == AuditLevel.DETAILED:
            # Exclude debug information
            filtered_dict = {
                k: v for k, v in event_dict.items()
                if not k.startswith('_debug')
            }
        else:
            # Comprehensive - include everything
            filtered_dict = event_dict
        
        # Encrypt sensitive data if encryption enabled
        if self.enable_encryption:
            filtered_dict = self._encrypt_sensitive_data(filtered_dict)
        
        # Log as JSON
        log_message = json.dumps(filtered_dict, default=str, separators=(',', ':'))
        
        # Use appropriate log level
        if audit_event.outcome == "failure":
            self.logger.error(log_message)
        elif audit_event.outcome == "warning":
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _event_to_dict(self, audit_event: AuditEvent) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        
        result = {}
        
        # Basic event info
        result.update({
            'event_id': audit_event.event_id,
            'event_type': audit_event.event_type.value,
            'timestamp': audit_event.timestamp.isoformat(),
            'description': audit_event.description,
            'outcome': audit_event.outcome,
            'checksum': audit_event.checksum
        })
        
        # Context information
        if audit_event.user_context:
            result['user_context'] = asdict(audit_event.user_context)
        
        if audit_event.system_context:
            result['system_context'] = asdict(audit_event.system_context)
        
        if audit_event.data_context:
            result['data_context'] = asdict(audit_event.data_context)
        
        # Compliance and security
        if audit_event.compliance_frameworks:
            result['compliance_frameworks'] = [f.value for f in audit_event.compliance_frameworks]
        
        if audit_event.security_flags:
            result['security_flags'] = audit_event.security_flags
        
        if audit_event.risk_score > 0:
            result['risk_score'] = audit_event.risk_score
        
        # Additional data
        if audit_event.metadata:
            result['metadata'] = audit_event.metadata
        
        if audit_event.tags:
            result['tags'] = audit_event.tags
        
        return result
    
    def _calculate_checksum(self, audit_event: AuditEvent) -> str:
        """Calculate checksum for audit event integrity"""
        
        # Create a consistent string representation
        checksum_data = f"{audit_event.event_id}|{audit_event.event_type.value}|{audit_event.timestamp.isoformat()}|{audit_event.description}"
        
        # Add user context if present
        if audit_event.user_context:
            checksum_data += f"|{audit_event.user_context.user_id}"
        
        # Calculate SHA-256 hash
        return hashlib.sha256(checksum_data.encode('utf-8')).hexdigest()
    
    def _sanitize_for_logging(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize data for secure logging (remove/mask PII)"""
        
        sanitized = {}
        sensitive_fields = ['password', 'token', 'secret', 'key', 'ssn', 'account_number']
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_fields):
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str) and len(value) > 100:
                # Truncate very long strings
                sanitized[key] = value[:100] + "..."
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _encrypt_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive data fields (placeholder implementation)"""
        
        # In a real implementation, this would use proper encryption
        # For now, just mark encrypted fields
        
        sensitive_fields = ['user_context', 'request_payload', 'response_payload']
        
        for field in sensitive_fields:
            if field in data:
                # Placeholder: In reality, would encrypt the data
                data[f"{field}_encrypted"] = True
        
        return data
    
    async def query_audit_logs(self,
                             start_date: datetime,
                             end_date: Optional[datetime] = None,
                             event_types: Optional[List[AuditEventType]] = None,
                             user_id: Optional[str] = None,
                             limit: int = 100) -> List[Dict[str, Any]]:
        """Query audit logs (placeholder implementation)"""
        
        # In a real implementation, this would query the audit log storage
        # For now, return empty list with query parameters logged
        
        query_params = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat() if end_date else None,
            'event_types': [et.value for et in event_types] if event_types else None,
            'user_id': user_id,
            'limit': limit
        }
        
        self.logger.info(f"Audit log query: {query_params}")
        
        return []  # Placeholder return
    
    async def generate_compliance_report(self,
                                       framework: ComplianceFramework,
                                       start_date: datetime,
                                       end_date: datetime) -> Dict[str, Any]:
        """Generate compliance report for specific framework"""
        
        report = {
            'framework': framework.value,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'generated_at': datetime.utcnow().isoformat(),
            'service': self.service_name
        }
        
        # Framework-specific reporting
        if framework == ComplianceFramework.NDPR:
            report.update({
                'data_processing_activities': [],
                'consent_records': [],
                'data_subject_requests': [],
                'privacy_incidents': []
            })
        elif framework == ComplianceFramework.FIRS:
            report.update({
                'tax_transactions': [],
                'classification_activities': [],
                'revenue_calculations': []
            })
        elif framework == ComplianceFramework.CBN:
            report.update({
                'banking_transactions': [],
                'regulatory_filings': [],
                'compliance_violations': []
            })
        
        # Log report generation
        await self.log_event(
            event_type=AuditEventType.COMPLIANCE_CHECK,
            description=f"Generated {framework.value.upper()} compliance report",
            metadata={'framework': framework.value, 'period_days': (end_date - start_date).days}
        )
        
        return report
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics"""
        
        return {
            'service_name': self.service_name,
            'audit_level': self.audit_level.value,
            'events_logged': self.event_counter,
            'encryption_enabled': self.enable_encryption,
            'compliance_frameworks_supported': len(self.compliance_mappings),
            'log_handlers': len(self.logger.handlers)
        }