"""
Banking Compliance & Security Module
====================================
Comprehensive compliance management for TaxPoynt's banking operations.
Ensures adherence to Nigerian regulatory requirements including FIRS,
CBN guidelines, and international compliance standards.

Key Components:
- compliance_manager: Central compliance orchestration
- consent_manager: User consent handling (NDPR)
- data_retention: Data retention policies (7-year FIRS requirement)
- audit_logger: Comprehensive audit trails
- security_monitor: Security monitoring & alerts
- privacy_compliance: Nigerian privacy regulation compliance

Regulatory Frameworks Supported:
- FIRS Nigeria (Federal Inland Revenue Service)
- CBN Guidelines (Central Bank of Nigeria)
- NDPR (Nigeria Data Protection Regulation)
- PCI DSS (Payment Card Industry Data Security Standard)
- ISO 27001 (Information Security Management)
"""

from .compliance_manager import (
    ComplianceManager, ComplianceLevel, RegulatoryFramework,
    ComplianceRule, ComplianceViolation, DataRetentionPolicy
)
from .consent_manager import (
    ConsentManager, ConsentType, ConsentStatus, ConsentPurpose,
    ConsentRecord, ConsentAuditEntry
)
from .data_retention import (
    DataRetentionManager, RetentionPolicy, ArchivalStatus,
    DataCategory, StorageTier, DataRecord
)
from .audit_logger import (
    AuditLogger, AuditLevel, AuditCategory, AuditEventType,
    AuditRecord, AuditQuery
)
from .security_monitor import (
    SecurityMonitor, SecurityAlert, ThreatLevel, SecurityEventType,
    AlertStatus, ThreatPattern, SecurityMetrics
)
from .privacy_compliance import (
    PrivacyComplianceManager, DataSubjectRights, ProcessingLawfulBasis,
    DataSubjectRequest, DataProcessingActivity, PrivacyBreach
)

__all__ = [
    # Core compliance management
    'ComplianceManager',
    'ComplianceLevel',
    'RegulatoryFramework',
    'ComplianceRule',
    'ComplianceViolation',
    'DataRetentionPolicy',
    
    # Consent management
    'ConsentManager',
    'ConsentType',
    'ConsentStatus',
    'ConsentPurpose',
    'ConsentRecord',
    'ConsentAuditEntry',
    
    # Data retention
    'DataRetentionManager',
    'RetentionPolicy',
    'ArchivalStatus',
    'DataCategory',
    'StorageTier',
    'DataRecord',
    
    # Audit logging
    'AuditLogger',
    'AuditLevel',
    'AuditCategory',
    'AuditEventType',
    'AuditRecord',
    'AuditQuery',
    
    # Security monitoring
    'SecurityMonitor',
    'SecurityAlert',
    'ThreatLevel',
    'SecurityEventType',
    'AlertStatus',
    'ThreatPattern',
    'SecurityMetrics',
    
    # Privacy compliance
    'PrivacyComplianceManager',
    'DataSubjectRights',
    'ProcessingLawfulBasis',
    'DataSubjectRequest',
    'DataProcessingActivity',
    'PrivacyBreach'
]