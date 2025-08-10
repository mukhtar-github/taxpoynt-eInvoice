"""
Compliance Manager for Banking Operations
========================================
Enterprise-grade compliance management system for banking operations.
Provides comprehensive audit trails, regulatory compliance monitoring,
and automated compliance reporting for TaxPoynt's e-invoicing platform.

Key Features:
- Real-time compliance monitoring
- Automated audit trail generation
- Regulatory compliance checks
- Data retention management
- Compliance reporting and analytics
- Risk assessment and alerting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib
import uuid

from .models import (
    BankingProviderType, UnifiedTransaction, UnifiedAccount,
    ComplianceReport, AuditEntry, ProviderStatus
)
from .exceptions import (
    ComplianceViolationError, AuditTrailError, ConfigurationError
)

from .....shared.logging import get_logger
from .....shared.exceptions import IntegrationError


class ComplianceLevel(Enum):
    """Compliance levels for different operations."""
    BASIC = "basic"
    STANDARD = "standard"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"


class RegulatoryFramework(Enum):
    """Supported regulatory frameworks."""
    FIRS_NIGERIA = "firs_nigeria"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    SOX = "sox"
    ISO_27001 = "iso_27001"
    BASEL_III = "basel_iii"
    CBN_GUIDELINES = "cbn_guidelines"


class ComplianceRuleType(Enum):
    """Types of compliance rules."""
    TRANSACTION_LIMIT = "transaction_limit"
    FREQUENCY_CHECK = "frequency_check"
    PATTERN_DETECTION = "pattern_detection"
    DATA_VALIDATION = "data_validation"
    AUTHORIZATION_CHECK = "authorization_check"
    RETENTION_POLICY = "retention_policy"
    ENCRYPTION_REQUIREMENT = "encryption_requirement"
    AUDIT_REQUIREMENT = "audit_requirement"


@dataclass
class ComplianceRule:
    """Definition of a compliance rule."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    rule_type: ComplianceRuleType = ComplianceRuleType.DATA_VALIDATION
    framework: RegulatoryFramework = RegulatoryFramework.FIRS_NIGERIA
    severity: str = "medium"
    description: str = ""
    conditions: Dict[str, Any] = field(default_factory=dict)
    actions: List[str] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    
@dataclass
class ComplianceViolation:
    """Record of a compliance violation."""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    rule_name: str = ""
    violation_type: str = ""
    severity: str = "medium"
    description: str = ""
    entity_type: str = ""  # transaction, account, provider, etc.
    entity_id: str = ""
    provider_type: Optional[BankingProviderType] = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    resolution: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataRetentionPolicy:
    """Data retention policy definition."""
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_type: str = ""
    retention_period_days: int = 2555  # 7 years default
    archive_after_days: int = 365
    purge_after_days: int = 2920  # 8 years
    encryption_required: bool = True
    backup_required: bool = True
    framework: RegulatoryFramework = RegulatoryFramework.FIRS_NIGERIA
    active: bool = True


class ComplianceManager:
    """
    Comprehensive compliance management system for banking operations.
    
    This manager ensures all banking operations comply with relevant
    regulatory frameworks and maintains detailed audit trails for
    compliance reporting and regulatory oversight.
    """
    
    def __init__(self, compliance_level: ComplianceLevel = ComplianceLevel.ENTERPRISE):
        """
        Initialize compliance manager.
        
        Args:
            compliance_level: Level of compliance monitoring
        """
        self.compliance_level = compliance_level
        self.logger = get_logger(__name__)
        
        # Compliance configuration
        self.rules: Dict[str, ComplianceRule] = {}
        self.violations: List[ComplianceViolation] = []
        self.audit_entries: List[AuditEntry] = []
        self.retention_policies: Dict[str, DataRetentionPolicy] = {}
        
        # Compliance state
        self.enabled_frameworks: List[RegulatoryFramework] = [
            RegulatoryFramework.FIRS_NIGERIA,
            RegulatoryFramework.CBN_GUIDELINES
        ]
        self.compliance_score: float = 100.0
        self.last_compliance_check: Optional[datetime] = None
        
        # Monitoring configuration
        self.real_time_monitoring = True
        self.violation_threshold = 10
        self.alert_recipients: List[str] = []
        
        self.logger.info(f"Initialized compliance manager with {compliance_level.value} level")
        
        # Set up default compliance rules
        self._setup_default_compliance_rules()
        self._setup_default_retention_policies()
    
    async def validate_transaction_compliance(
        self,
        transaction: UnifiedTransaction,
        account: UnifiedAccount,
        context: Dict[str, Any]
    ) -> Tuple[bool, List[ComplianceViolation]]:
        """
        Validate transaction against compliance rules.
        
        Args:
            transaction: Transaction to validate
            account: Associated account
            context: Additional context for validation
            
        Returns:
            Tuple of (is_compliant, violations_list)
        """
        try:
            violations = []
            
            # Run all active compliance rules
            for rule in self.rules.values():
                if not rule.active:
                    continue
                
                violation = await self._check_rule_compliance(
                    rule, transaction, account, context
                )
                
                if violation:
                    violations.append(violation)
                    
                    # Log violation for audit
                    await self._log_compliance_violation(violation, transaction, context)
            
            is_compliant = len(violations) == 0
            
            # Create audit entry
            await self._create_audit_entry(
                operation_type="transaction_compliance_check",
                entity_type="transaction",
                entity_id=transaction.transaction_id,
                result="compliant" if is_compliant else "violations_found",
                details={
                    "transaction_amount": str(transaction.amount),
                    "transaction_type": transaction.transaction_type.value,
                    "violations_count": len(violations),
                    "provider_type": transaction.provider_type.value
                },
                compliance_tags=["transaction_validation", "real_time_check"]
            )
            
            return is_compliant, violations
            
        except Exception as e:
            self.logger.error(f"Transaction compliance validation failed: {str(e)}")
            raise ComplianceViolationError(f"Compliance validation failed: {str(e)}")
    
    async def validate_provider_compliance(
        self,
        provider_type: BankingProviderType,
        provider_status: ProviderStatus,
        context: Dict[str, Any]
    ) -> Tuple[bool, List[ComplianceViolation]]:
        """
        Validate provider compliance status.
        
        Args:
            provider_type: Type of banking provider
            provider_status: Current provider status
            context: Additional context for validation
            
        Returns:
            Tuple of (is_compliant, violations_list)
        """
        try:
            violations = []
            
            # Check provider-specific compliance rules
            provider_rules = [
                rule for rule in self.rules.values()
                if rule.active and "provider" in rule.conditions
            ]
            
            for rule in provider_rules:
                violation = await self._check_provider_rule_compliance(
                    rule, provider_type, provider_status, context
                )
                
                if violation:
                    violations.append(violation)
            
            is_compliant = len(violations) == 0
            
            # Create audit entry
            await self._create_audit_entry(
                operation_type="provider_compliance_check",
                entity_type="provider",
                entity_id=provider_type.value,
                result="compliant" if is_compliant else "violations_found",
                details={
                    "provider_status": provider_status.value,
                    "violations_count": len(violations)
                },
                compliance_tags=["provider_validation", "health_check"]
            )
            
            return is_compliant, violations
            
        except Exception as e:
            self.logger.error(f"Provider compliance validation failed: {str(e)}")
            raise ComplianceViolationError(f"Provider compliance validation failed: {str(e)}")
    
    async def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime,
        framework: Optional[RegulatoryFramework] = None,
        report_type: str = "comprehensive"
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            framework: Specific regulatory framework
            report_type: Type of report to generate
            
        Returns:
            Comprehensive compliance report
        """
        try:
            self.logger.info(f"Generating {report_type} compliance report")
            
            # Filter data by date range
            period_violations = [
                v for v in self.violations
                if start_date <= v.detected_at <= end_date
            ]
            
            period_audits = [
                a for a in self.audit_entries
                if start_date <= a.timestamp <= end_date
            ]
            
            # Filter by framework if specified
            if framework:
                period_violations = [
                    v for v in period_violations
                    if any(rule.framework == framework 
                          for rule in self.rules.values()
                          if rule.rule_id == v.rule_id)
                ]
            
            # Calculate compliance metrics
            total_operations = len(period_audits)
            violation_count = len(period_violations)
            compliance_rate = ((total_operations - violation_count) / total_operations * 100) if total_operations > 0 else 100
            
            # Categorize violations by severity
            violation_by_severity = {}
            for violation in period_violations:
                severity = violation.severity
                violation_by_severity[severity] = violation_by_severity.get(severity, 0) + 1
            
            # Generate summary
            summary = {
                "reporting_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "compliance_metrics": {
                    "total_operations": total_operations,
                    "violation_count": violation_count,
                    "compliance_rate": compliance_rate,
                    "violations_by_severity": violation_by_severity
                },
                "framework": framework.value if framework else "all",
                "report_type": report_type
            }
            
            # Generate detailed sections
            details = []
            
            # Violation details
            for violation in period_violations:
                details.append({
                    "section": "violations",
                    "violation_id": violation.violation_id,
                    "rule_name": violation.rule_name,
                    "severity": violation.severity,
                    "description": violation.description,
                    "detected_at": violation.detected_at.isoformat(),
                    "resolved": violation.resolved_at is not None,
                    "entity_type": violation.entity_type,
                    "entity_id": violation.entity_id
                })
            
            # Audit trail summary
            audit_summary = self._generate_audit_summary(period_audits)
            details.append({
                "section": "audit_summary",
                "data": audit_summary
            })
            
            # Data retention compliance
            retention_compliance = await self._check_retention_compliance()
            details.append({
                "section": "data_retention",
                "data": retention_compliance
            })
            
            # Calculate compliance score
            compliance_score = self._calculate_compliance_score(
                compliance_rate, violation_by_severity, total_operations
            )
            
            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                period_violations, compliance_score
            )
            
            report = ComplianceReport(
                report_type=report_type,
                provider_type=BankingProviderType.MONO,  # Default, should be configurable
                start_date=start_date,
                end_date=end_date,
                summary=summary,
                details=details,
                compliance_score=compliance_score,
                violations=[v.violation_type for v in period_violations],
                recommendations=recommendations
            )
            
            # Create audit entry for report generation
            await self._create_audit_entry(
                operation_type="compliance_report_generation",
                entity_type="system",
                entity_id=report.report_id,
                result="success",
                details={
                    "report_type": report_type,
                    "framework": framework.value if framework else "all",
                    "violations_found": len(period_violations),
                    "compliance_score": compliance_score
                },
                compliance_tags=["reporting", "compliance_audit"]
            )
            
            self.logger.info(f"Generated compliance report: {report.report_id}")
            return report
            
        except Exception as e:
            self.logger.error(f"Compliance report generation failed: {str(e)}")
            raise AuditTrailError(f"Report generation failed: {str(e)}")
    
    async def get_audit_trail(
        self,
        start_date: datetime,
        end_date: datetime,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        operation_type: Optional[str] = None
    ) -> List[AuditEntry]:
        """
        Retrieve audit trail for specified criteria.
        
        Args:
            start_date: Start date for audit trail
            end_date: End date for audit trail
            entity_type: Optional entity type filter
            entity_id: Optional entity ID filter
            operation_type: Optional operation type filter
            
        Returns:
            List of audit entries
        """
        try:
            # Filter audit entries
            filtered_entries = [
                entry for entry in self.audit_entries
                if start_date <= entry.timestamp <= end_date
            ]
            
            if entity_type:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.operation_type == entity_type
                ]
            
            if entity_id:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.account_id == entity_id or entry.transaction_id == entity_id
                ]
            
            if operation_type:
                filtered_entries = [
                    entry for entry in filtered_entries
                    if entry.operation_type == operation_type
                ]
            
            # Sort by timestamp
            filtered_entries.sort(key=lambda x: x.timestamp)
            
            return filtered_entries
            
        except Exception as e:
            self.logger.error(f"Audit trail retrieval failed: {str(e)}")
            raise AuditTrailError(f"Audit trail retrieval failed: {str(e)}")
    
    def _setup_default_compliance_rules(self) -> None:
        """Set up default compliance rules for TaxPoynt."""
        # FIRS Transaction Reporting Rule
        self.rules["firs_transaction_reporting"] = ComplianceRule(
            rule_name="FIRS Transaction Reporting",
            rule_type=ComplianceRuleType.AUDIT_REQUIREMENT,
            framework=RegulatoryFramework.FIRS_NIGERIA,
            severity="high",
            description="All transactions must be reported to FIRS for e-invoicing compliance",
            conditions={
                "min_amount": 1000,  # NGN
                "transaction_types": ["debit", "credit", "transfer"],
                "requires_audit": True
            },
            actions=["audit_log", "compliance_report", "firs_notification"]
        )
        
        # Large Transaction Monitoring
        self.rules["large_transaction_monitoring"] = ComplianceRule(
            rule_name="Large Transaction Monitoring",
            rule_type=ComplianceRuleType.TRANSACTION_LIMIT,
            framework=RegulatoryFramework.CBN_GUIDELINES,
            severity="critical",
            description="Monitor large transactions for compliance and reporting",
            conditions={
                "amount_threshold": 1000000,  # NGN 1M
                "requires_enhanced_verification": True,
                "notification_required": True
            },
            actions=["enhanced_audit", "immediate_alert", "manual_review"]
        )
        
        # Data Retention Compliance
        self.rules["data_retention_compliance"] = ComplianceRule(
            rule_name="Data Retention Compliance",
            rule_type=ComplianceRuleType.RETENTION_POLICY,
            framework=RegulatoryFramework.FIRS_NIGERIA,
            severity="high",
            description="Ensure data retention compliance for regulatory requirements",
            conditions={
                "retention_years": 7,
                "encryption_required": True,
                "backup_required": True
            },
            actions=["automated_archival", "compliance_verification"]
        )
    
    def _setup_default_retention_policies(self) -> None:
        """Set up default data retention policies."""
        # Transaction data retention
        self.retention_policies["transaction_data"] = DataRetentionPolicy(
            data_type="transaction_data",
            retention_period_days=2555,  # 7 years
            archive_after_days=365,
            framework=RegulatoryFramework.FIRS_NIGERIA
        )
        
        # Audit log retention
        self.retention_policies["audit_logs"] = DataRetentionPolicy(
            data_type="audit_logs",
            retention_period_days=2920,  # 8 years
            archive_after_days=1095,  # 3 years
            framework=RegulatoryFramework.FIRS_NIGERIA
        )
        
        # Account data retention
        self.retention_policies["account_data"] = DataRetentionPolicy(
            data_type="account_data",
            retention_period_days=2555,  # 7 years
            archive_after_days=730,  # 2 years
            framework=RegulatoryFramework.CBN_GUIDELINES
        )
    
    async def _check_rule_compliance(
        self,
        rule: ComplianceRule,
        transaction: UnifiedTransaction,
        account: UnifiedAccount,
        context: Dict[str, Any]
    ) -> Optional[ComplianceViolation]:
        """Check if transaction violates a specific rule."""
        # Implementation would check specific rule conditions
        # This is a simplified example
        
        if rule.rule_type == ComplianceRuleType.TRANSACTION_LIMIT:
            threshold = rule.conditions.get("amount_threshold", 0)
            if transaction.amount > threshold:
                return ComplianceViolation(
                    rule_id=rule.rule_id,
                    rule_name=rule.rule_name,
                    violation_type="transaction_limit_exceeded",
                    severity=rule.severity,
                    description=f"Transaction amount {transaction.amount} exceeds limit {threshold}",
                    entity_type="transaction",
                    entity_id=transaction.transaction_id,
                    provider_type=transaction.provider_type,
                    metadata={
                        "amount": str(transaction.amount),
                        "limit": str(threshold),
                        "account_id": account.account_id
                    }
                )
        
        return None
    
    async def _create_audit_entry(
        self,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        result: str,
        details: Dict[str, Any],
        compliance_tags: List[str],
        user_id: Optional[str] = None,
        account_id: Optional[str] = None,
        transaction_id: Optional[str] = None
    ) -> None:
        """Create audit entry for compliance tracking."""
        audit_entry = AuditEntry(
            provider_type=BankingProviderType.MONO,  # Default
            operation_type=operation_type,
            user_id=user_id,
            account_id=account_id,
            transaction_id=transaction_id,
            action=f"{entity_type}_{operation_type}",
            result=result,
            details=details,
            compliance_tags=compliance_tags
        )
        
        self.audit_entries.append(audit_entry)
        
        # Keep only recent audit entries in memory (for performance)
        if len(self.audit_entries) > 10000:
            self.audit_entries = self.audit_entries[-5000:]
    
    def _calculate_compliance_score(
        self,
        compliance_rate: float,
        violations_by_severity: Dict[str, int],
        total_operations: int
    ) -> float:
        """Calculate overall compliance score."""
        base_score = compliance_rate
        
        # Deduct points for violations by severity
        critical_violations = violations_by_severity.get("critical", 0)
        high_violations = violations_by_severity.get("high", 0)
        medium_violations = violations_by_severity.get("medium", 0)
        
        penalty = (
            critical_violations * 10 +
            high_violations * 5 +
            medium_violations * 2
        )
        
        final_score = max(0, base_score - penalty)
        return round(final_score, 2)