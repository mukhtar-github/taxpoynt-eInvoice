"""
Data Retention Manager for FIRS Compliance
==========================================
Manages data retention policies according to FIRS 7-year requirement
and other regulatory compliance needs. Handles automated archival,
purging, and data lifecycle management.

Key Features:
- FIRS 7-year data retention compliance
- Automated data archival and purging
- Secure data storage and encryption
- Audit trails for data lifecycle
- Configurable retention policies
- Data recovery and restoration
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

from ....shared.logging import get_logger
from ....shared.exceptions import IntegrationError


class DataCategory(Enum):
    """Categories of data for retention management."""
    TRANSACTION_DATA = "transaction_data"
    ACCOUNT_DATA = "account_data"
    CUSTOMER_DATA = "customer_data"
    AUDIT_LOGS = "audit_logs"
    CONSENT_RECORDS = "consent_records"
    INVOICE_DATA = "invoice_data"
    TAX_RECORDS = "tax_records"
    COMPLIANCE_REPORTS = "compliance_reports"
    SECURITY_LOGS = "security_logs"


class ArchivalStatus(Enum):
    """Status of data archival."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    PURGED = "purged"
    PENDING_ARCHIVAL = "pending_archival"
    PENDING_PURGE = "pending_purge"
    RETENTION_HOLD = "retention_hold"
    LEGAL_HOLD = "legal_hold"


class StorageTier(Enum):
    """Storage tiers for cost optimization."""
    HOT = "hot"          # Immediate access
    WARM = "warm"        # Infrequent access
    COLD = "cold"        # Archive storage
    GLACIER = "glacier"  # Long-term archive


@dataclass
class RetentionPolicy:
    """Data retention policy definition."""
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_name: str = ""
    data_category: DataCategory = DataCategory.TRANSACTION_DATA
    retention_period_days: int = 2555  # 7 years for FIRS
    archive_after_days: int = 365
    purge_after_days: int = 2920  # 8 years (1 year grace period)
    encryption_required: bool = True
    backup_required: bool = True
    legal_hold_supported: bool = True
    storage_tier_progression: List[Tuple[int, StorageTier]] = field(default_factory=lambda: [
        (0, StorageTier.HOT),
        (90, StorageTier.WARM),
        (365, StorageTier.COLD),
        (1095, StorageTier.GLACIER)
    ])
    compliance_frameworks: List[str] = field(default_factory=lambda: ["FIRS", "CBN"])
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DataRecord:
    """Record of data subject to retention policies."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_category: DataCategory = DataCategory.TRANSACTION_DATA
    entity_id: str = ""  # transaction_id, account_id, etc.
    entity_type: str = ""
    data_size: int = 0  # bytes
    created_at: datetime = field(default_factory=datetime.utcnow)
    status: ArchivalStatus = ArchivalStatus.ACTIVE
    current_storage_tier: StorageTier = StorageTier.HOT
    archive_date: Optional[datetime] = None
    purge_date: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    encryption_key_id: Optional[str] = None
    backup_locations: List[str] = field(default_factory=list)
    legal_holds: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchivalOperation:
    """Record of archival/purge operations."""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str = ""  # archive, purge, restore
    record_ids: List[str] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    error_message: Optional[str] = None
    records_processed: int = 0
    total_size_processed: int = 0  # bytes
    target_storage_tier: Optional[StorageTier] = None


@dataclass
class RetentionAuditEntry:
    """Audit entry for retention operations."""
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    record_id: str = ""
    operation_type: str = ""
    previous_status: Optional[ArchivalStatus] = None
    new_status: ArchivalStatus = ArchivalStatus.ACTIVE
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    performed_by: str = "system"
    details: Dict[str, Any] = field(default_factory=dict)


class DataRetentionManager:
    """
    Comprehensive data retention management system.
    
    This manager handles the complete data lifecycle from creation
    to purging, ensuring compliance with FIRS 7-year requirements
    and other regulatory obligations.
    """
    
    def __init__(self):
        """Initialize data retention manager."""
        self.logger = get_logger(__name__)
        
        # Storage
        self.policies: Dict[str, RetentionPolicy] = {}
        self.data_records: Dict[str, DataRecord] = {}
        self.operations: Dict[str, ArchivalOperation] = {}
        self.audit_trail: List[RetentionAuditEntry] = []
        
        # Configuration
        self.auto_archival_enabled = True
        self.auto_purge_enabled = False  # Requires manual approval for FIRS compliance
        self.encryption_enabled = True
        self.backup_enabled = True
        
        # FIRS specific settings
        self.firs_retention_days = 2555  # 7 years
        self.firs_grace_period_days = 365  # 1 year grace period
        self.minimum_retention_days = 2190  # 6 years minimum
        
        self.logger.info("Initialized FIRS-compliant data retention manager")
        
        # Set up default retention policies
        self._setup_default_policies()
    
    def register_data_record(
        self,
        entity_id: str,
        entity_type: str,
        data_category: DataCategory,
        data_size: int = 0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DataRecord:
        """
        Register new data record for retention management.
        
        Args:
            entity_id: Unique identifier for the data entity
            entity_type: Type of entity (transaction, account, etc.)
            data_category: Category of data
            data_size: Size of data in bytes
            metadata: Additional metadata
            
        Returns:
            Created data record
        """
        try:
            # Find applicable retention policy
            policy = self._find_applicable_policy(data_category)
            
            if not policy:
                self.logger.warning(f"No retention policy found for {data_category}")
                policy = self._get_default_policy()
            
            # Create data record
            record = DataRecord(
                entity_id=entity_id,
                entity_type=entity_type,
                data_category=data_category,
                data_size=data_size,
                metadata=metadata or {}
            )
            
            # Calculate future dates based on policy
            if policy:
                record.archive_date = record.created_at + timedelta(days=policy.archive_after_days)
                record.purge_date = record.created_at + timedelta(days=policy.purge_after_days)
            
            # Store record
            self.data_records[record.record_id] = record
            
            # Create audit entry
            self._create_audit_entry(
                record.record_id,
                "data_registered",
                None,
                ArchivalStatus.ACTIVE,
                f"Data record registered for {entity_type}",
                details={
                    "entity_id": entity_id,
                    "data_category": data_category.value,
                    "data_size": data_size
                }
            )
            
            self.logger.info(f"Registered data record: {record.record_id}")
            return record
            
        except Exception as e:
            self.logger.error(f"Failed to register data record: {str(e)}")
            raise IntegrationError(f"Data registration failed: {str(e)}")
    
    async def process_archival_queue(self) -> Dict[str, Any]:
        """
        Process pending archival operations.
        
        Returns:
            Summary of archival operations performed
        """
        try:
            self.logger.info("Processing archival queue")
            
            # Find records eligible for archival
            now = datetime.utcnow()
            eligible_records = [
                record for record in self.data_records.values()
                if (record.status == ArchivalStatus.ACTIVE and
                    record.archive_date and
                    record.archive_date <= now and
                    len(record.legal_holds) == 0)  # No legal holds
            ]
            
            if not eligible_records:
                return {"archived_count": 0, "message": "No records eligible for archival"}
            
            # Group by data category for batch processing
            records_by_category = {}
            for record in eligible_records:
                category = record.data_category
                if category not in records_by_category:
                    records_by_category[category] = []
                records_by_category[category].append(record)
            
            archived_count = 0
            operations_summary = []
            
            # Process each category
            for category, records in records_by_category.items():
                operation_result = await self._archive_records_batch(records)
                operations_summary.append(operation_result)
                archived_count += operation_result.get('records_processed', 0)
            
            self.logger.info(f"Archived {archived_count} records")
            
            return {
                "archived_count": archived_count,
                "operations": operations_summary,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Archival queue processing failed: {str(e)}")
            raise IntegrationError(f"Archival processing failed: {str(e)}")
    
    async def process_purge_queue(
        self,
        require_manual_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Process pending purge operations.
        
        Args:
            require_manual_approval: Whether manual approval is required
            
        Returns:
            Summary of purge operations
        """
        try:
            if not self.auto_purge_enabled and require_manual_approval:
                return {"message": "Auto-purge disabled, manual approval required"}
            
            self.logger.info("Processing purge queue")
            
            # Find records eligible for purging
            now = datetime.utcnow()
            eligible_records = [
                record for record in self.data_records.values()
                if (record.status == ArchivalStatus.ARCHIVED and
                    record.purge_date and
                    record.purge_date <= now and
                    len(record.legal_holds) == 0 and
                    not self._has_retention_hold(record))
            ]
            
            if not eligible_records:
                return {"purged_count": 0, "message": "No records eligible for purging"}
            
            # Additional safety check for FIRS compliance
            firs_compliant_records = [
                record for record in eligible_records
                if self._is_firs_purge_compliant(record)
            ]
            
            if len(firs_compliant_records) != len(eligible_records):
                self.logger.warning(
                    f"Some records not FIRS-compliant for purging: "
                    f"{len(eligible_records) - len(firs_compliant_records)} excluded"
                )
            
            purged_count = 0
            operations_summary = []
            
            # Process purging in batches
            for i in range(0, len(firs_compliant_records), 100):
                batch = firs_compliant_records[i:i+100]
                operation_result = await self._purge_records_batch(batch)
                operations_summary.append(operation_result)
                purged_count += operation_result.get('records_processed', 0)
            
            self.logger.info(f"Purged {purged_count} records")
            
            return {
                "purged_count": purged_count,
                "operations": operations_summary,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Purge queue processing failed: {str(e)}")
            raise IntegrationError(f"Purge processing failed: {str(e)}")
    
    async def apply_legal_hold(
        self,
        record_ids: List[str],
        hold_reason: str,
        hold_reference: str
    ) -> int:
        """
        Apply legal hold to prevent purging of records.
        
        Args:
            record_ids: List of record IDs to hold
            hold_reason: Reason for legal hold
            hold_reference: Reference identifier for the hold
            
        Returns:
            Number of records with hold applied
        """
        try:
            applied_count = 0
            
            for record_id in record_ids:
                record = self.data_records.get(record_id)
                if not record:
                    continue
                
                # Add legal hold
                hold_info = f"{hold_reference}:{hold_reason}"
                if hold_info not in record.legal_holds:
                    record.legal_holds.append(hold_info)
                    applied_count += 1
                    
                    # Create audit entry
                    self._create_audit_entry(
                        record_id,
                        "legal_hold_applied",
                        record.status,
                        ArchivalStatus.LEGAL_HOLD,
                        f"Legal hold applied: {hold_reason}",
                        details={
                            "hold_reference": hold_reference,
                            "hold_reason": hold_reason
                        }
                    )
            
            self.logger.info(f"Applied legal hold to {applied_count} records")
            return applied_count
            
        except Exception as e:
            self.logger.error(f"Failed to apply legal hold: {str(e)}")
            raise IntegrationError(f"Legal hold application failed: {str(e)}")
    
    async def generate_retention_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate comprehensive retention compliance report.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Retention compliance report
        """
        try:
            # Filter records by date range
            period_records = [
                record for record in self.data_records.values()
                if start_date <= record.created_at <= end_date
            ]
            
            # Calculate statistics
            total_records = len(period_records)
            active_records = len([r for r in period_records if r.status == ArchivalStatus.ACTIVE])
            archived_records = len([r for r in period_records if r.status == ArchivalStatus.ARCHIVED])
            purged_records = len([r for r in period_records if r.status == ArchivalStatus.PURGED])
            
            # Storage tier distribution
            tier_distribution = {}
            for record in period_records:
                tier = record.current_storage_tier.value
                tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
            
            # Data category breakdown
            category_breakdown = {}
            for record in period_records:
                category = record.data_category.value
                category_breakdown[category] = category_breakdown.get(category, 0) + 1
            
            # Compliance status
            firs_compliant_records = len([
                r for r in period_records
                if self._is_firs_retention_compliant(r)
            ])
            
            compliance_rate = (firs_compliant_records / total_records * 100) if total_records > 0 else 100
            
            # Upcoming actions
            now = datetime.utcnow()
            upcoming_archive = len([
                r for r in self.data_records.values()
                if (r.status == ArchivalStatus.ACTIVE and
                    r.archive_date and
                    r.archive_date <= now + timedelta(days=30))
            ])
            
            upcoming_purge = len([
                r for r in self.data_records.values()
                if (r.status == ArchivalStatus.ARCHIVED and
                    r.purge_date and
                    r.purge_date <= now + timedelta(days=30))
            ])
            
            report = {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                },
                "summary": {
                    "total_records": total_records,
                    "active_records": active_records,
                    "archived_records": archived_records,
                    "purged_records": purged_records,
                    "firs_compliance_rate": compliance_rate
                },
                "storage_distribution": tier_distribution,
                "category_breakdown": category_breakdown,
                "upcoming_actions": {
                    "records_due_for_archival": upcoming_archive,
                    "records_due_for_purge": upcoming_purge
                },
                "policies_active": len([p for p in self.policies.values() if p.active]),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Retention report generation failed: {str(e)}")
            raise IntegrationError(f"Report generation failed: {str(e)}")
    
    def _setup_default_policies(self) -> None:
        """Set up default FIRS-compliant retention policies."""
        # Transaction data policy
        self.policies["firs_transaction_policy"] = RetentionPolicy(
            policy_name="FIRS Transaction Data Retention",
            data_category=DataCategory.TRANSACTION_DATA,
            retention_period_days=self.firs_retention_days,
            archive_after_days=365,
            purge_after_days=self.firs_retention_days + self.firs_grace_period_days
        )
        
        # Invoice data policy
        self.policies["firs_invoice_policy"] = RetentionPolicy(
            policy_name="FIRS Invoice Data Retention",
            data_category=DataCategory.INVOICE_DATA,
            retention_period_days=self.firs_retention_days,
            archive_after_days=730,  # 2 years
            purge_after_days=self.firs_retention_days + self.firs_grace_period_days
        )
        
        # Audit logs policy
        self.policies["audit_logs_policy"] = RetentionPolicy(
            policy_name="Audit Logs Retention",
            data_category=DataCategory.AUDIT_LOGS,
            retention_period_days=2920,  # 8 years
            archive_after_days=1095,  # 3 years
            purge_after_days=2920
        )
    
    def _find_applicable_policy(self, data_category: DataCategory) -> Optional[RetentionPolicy]:
        """Find applicable retention policy for data category."""
        for policy in self.policies.values():
            if policy.data_category == data_category and policy.active:
                return policy
        return None
    
    def _get_default_policy(self) -> RetentionPolicy:
        """Get default retention policy."""
        return RetentionPolicy(
            policy_name="Default FIRS Policy",
            retention_period_days=self.firs_retention_days,
            archive_after_days=365,
            purge_after_days=self.firs_retention_days + self.firs_grace_period_days
        )
    
    def _is_firs_retention_compliant(self, record: DataRecord) -> bool:
        """Check if record meets FIRS retention requirements."""
        age_days = (datetime.utcnow() - record.created_at).days
        
        # Must be retained for at least 6 years
        if age_days < self.minimum_retention_days and record.status == ArchivalStatus.PURGED:
            return False
        
        # Should not be purged before 7 years + grace period
        if record.purge_date and record.purge_date < record.created_at + timedelta(days=self.firs_retention_days):
            return False
        
        return True
    
    def _is_firs_purge_compliant(self, record: DataRecord) -> bool:
        """Check if record can be purged according to FIRS requirements."""
        age_days = (datetime.utcnow() - record.created_at).days
        return age_days >= self.firs_retention_days
    
    def _has_retention_hold(self, record: DataRecord) -> bool:
        """Check if record has any retention holds."""
        return record.status == ArchivalStatus.RETENTION_HOLD or len(record.legal_holds) > 0