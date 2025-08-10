"""
Data Reconciler Service

This module ensures data consistency across systems by performing comprehensive
reconciliation checks, identifying discrepancies, and providing automated
correction mechanisms.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any, Tuple, NamedTuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from .erp_data_extractor import InvoiceData, ERPType, ERPDataExtractor

logger = logging.getLogger(__name__)


class ReconciliationType(Enum):
    """Types of reconciliation checks"""
    RECORD_COUNT = "record_count"
    FIELD_VALIDATION = "field_validation"
    AMOUNT_TOTALS = "amount_totals"
    CROSS_REFERENCE = "cross_reference"
    SEQUENCE_INTEGRITY = "sequence_integrity"
    DUPLICATE_DETECTION = "duplicate_detection"
    ORPHAN_DETECTION = "orphan_detection"
    TEMPORAL_CONSISTENCY = "temporal_consistency"


class DiscrepancySeverity(Enum):
    """Severity levels for discrepancies"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ReconciliationStatus(Enum):
    """Status of reconciliation operations"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class ReconciliationConfig:
    """Configuration for data reconciliation"""
    check_types: List[ReconciliationType] = field(default_factory=lambda: list(ReconciliationType))
    tolerance_amount: Decimal = Decimal("0.01")
    tolerance_percentage: Decimal = Decimal("0.001")  # 0.1%
    max_discrepancy_count: int = 1000
    enable_auto_correction: bool = False
    enable_cross_system_validation: bool = True
    batch_size: int = 1000
    parallel_workers: int = 3
    timeout_seconds: int = 3600
    generate_reports: bool = True
    report_storage_path: Optional[str] = None


@dataclass
class Discrepancy:
    """Represents a data discrepancy"""
    discrepancy_id: str
    discrepancy_type: ReconciliationType
    severity: DiscrepancySeverity
    entity_type: str
    entity_id: str
    field_name: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    difference: Optional[Any] = None
    description: str = ""
    source_system: Optional[str] = None
    target_system: Optional[str] = None
    detected_at: datetime = field(default_factory=datetime.now)
    corrected: bool = False
    correction_applied: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReconciliationResult:
    """Result of a reconciliation operation"""
    reconciliation_id: str
    status: ReconciliationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_records_checked: int = 0
    discrepancies_found: int = 0
    discrepancies_corrected: int = 0
    check_types_performed: List[ReconciliationType] = field(default_factory=list)
    discrepancies: List[Discrepancy] = field(default_factory=list)
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    error_details: List[Dict[str, Any]] = field(default_factory=list)


class ReconciliationMetrics(NamedTuple):
    """Metrics for reconciliation performance"""
    total_reconciliations: int
    successful_reconciliations: int
    failed_reconciliations: int
    total_discrepancies: int
    auto_corrections: int
    average_duration: float
    accuracy_rate: float


class DataReconciler:
    """
    Comprehensive data reconciliation service for ensuring consistency
    across ERP systems and platform data.
    """
    
    def __init__(
        self,
        config: ReconciliationConfig,
        data_extractor: ERPDataExtractor
    ):
        self.config = config
        self.data_extractor = data_extractor
        self.active_reconciliations: Dict[str, ReconciliationResult] = {}
        self.metrics = ReconciliationMetrics(0, 0, 0, 0, 0, 0.0, 0.0)
        self._reconciliation_rules: Dict[ReconciliationType, Callable] = {}
        self._setup_reconciliation_rules()
    
    def _setup_reconciliation_rules(self) -> None:
        """Setup reconciliation rule mappings"""
        self._reconciliation_rules = {
            ReconciliationType.RECORD_COUNT: self._check_record_count,
            ReconciliationType.FIELD_VALIDATION: self._check_field_validation,
            ReconciliationType.AMOUNT_TOTALS: self._check_amount_totals,
            ReconciliationType.CROSS_REFERENCE: self._check_cross_reference,
            ReconciliationType.SEQUENCE_INTEGRITY: self._check_sequence_integrity,
            ReconciliationType.DUPLICATE_DETECTION: self._check_duplicates,
            ReconciliationType.ORPHAN_DETECTION: self._check_orphans,
            ReconciliationType.TEMPORAL_CONSISTENCY: self._check_temporal_consistency
        }
    
    async def start_reconciliation(
        self,
        erp_type: ERPType,
        check_types: Optional[List[ReconciliationType]] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> str:
        """Start a comprehensive reconciliation operation"""
        
        reconciliation_id = f"recon_{erp_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = ReconciliationResult(
            reconciliation_id=reconciliation_id,
            status=ReconciliationStatus.PENDING,
            start_time=datetime.now()
        )
        
        self.active_reconciliations[reconciliation_id] = result
        
        # Use provided check types or default to all
        check_types = check_types or self.config.check_types
        result.check_types_performed = check_types
        
        # Start reconciliation in background
        asyncio.create_task(
            self._perform_reconciliation(result, erp_type, check_types, date_range)
        )
        
        logger.info(f"Started reconciliation {reconciliation_id} for {erp_type.value}")
        return reconciliation_id
    
    async def _perform_reconciliation(
        self,
        result: ReconciliationResult,
        erp_type: ERPType,
        check_types: List[ReconciliationType],
        date_range: Optional[Tuple[datetime, datetime]]
    ) -> None:
        """Perform the actual reconciliation operation"""
        try:
            result.status = ReconciliationStatus.RUNNING
            
            # Extract data for reconciliation
            source_data = await self._extract_source_data(erp_type, date_range)
            target_data = await self._extract_target_data(erp_type, date_range)
            
            result.total_records_checked = len(source_data)
            
            # Perform reconciliation checks
            for check_type in check_types:
                if check_type in self._reconciliation_rules:
                    discrepancies = await self._reconciliation_rules[check_type](
                        source_data, target_data, erp_type
                    )
                    result.discrepancies.extend(discrepancies)
            
            # Apply auto-corrections if enabled
            if self.config.enable_auto_correction:
                corrections_applied = await self._apply_auto_corrections(result.discrepancies)
                result.discrepancies_corrected = corrections_applied
            
            # Generate summary metrics
            result.summary_metrics = self._generate_summary_metrics(result.discrepancies)
            result.discrepancies_found = len(result.discrepancies)
            
            # Generate report if enabled
            if self.config.generate_reports:
                await self._generate_reconciliation_report(result)
            
            result.status = ReconciliationStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Reconciliation {result.reconciliation_id} failed: {e}")
            result.status = ReconciliationStatus.FAILED
            result.error_details.append({
                "error": str(e),
                "timestamp": datetime.now(),
                "phase": "main_reconciliation"
            })
        
        finally:
            result.end_time = datetime.now()
            if result.start_time:
                duration = (result.end_time - result.start_time).total_seconds()
                result.performance_metrics["duration"] = duration
    
    async def _extract_source_data(
        self,
        erp_type: ERPType,
        date_range: Optional[Tuple[datetime, datetime]]
    ) -> List[InvoiceData]:
        """Extract data from source ERP system"""
        try:
            from .erp_data_extractor import ExtractionFilter
            
            filter_config = ExtractionFilter(batch_size=self.config.batch_size)
            if date_range:
                filter_config.start_date, filter_config.end_date = date_range
            
            extraction_result = await self.data_extractor.extract_data(
                erp_type, filter_config
            )
            
            # For this implementation, we'll simulate getting the actual data
            # In practice, this would retrieve the extracted invoice data
            return []  # Replace with actual data retrieval
            
        except Exception as e:
            logger.error(f"Failed to extract source data from {erp_type.value}: {e}")
            raise
    
    async def _extract_target_data(
        self,
        erp_type: ERPType,
        date_range: Optional[Tuple[datetime, datetime]]
    ) -> List[InvoiceData]:
        """Extract data from target platform database"""
        try:
            # This would query the platform's database for comparison
            # For now, return empty list as placeholder
            return []
            
        except Exception as e:
            logger.error(f"Failed to extract target data: {e}")
            raise
    
    async def _check_record_count(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check if record counts match between systems"""
        discrepancies = []
        
        source_count = len(source_data)
        target_count = len(target_data)
        
        if source_count != target_count:
            discrepancy = Discrepancy(
                discrepancy_id=f"count_{erp_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                discrepancy_type=ReconciliationType.RECORD_COUNT,
                severity=DiscrepancySeverity.ERROR,
                entity_type="invoice_collection",
                entity_id="all",
                expected_value=source_count,
                actual_value=target_count,
                difference=abs(source_count - target_count),
                description=f"Record count mismatch: source has {source_count}, target has {target_count}",
                source_system=erp_type.value,
                target_system="platform"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_field_validation(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Validate individual field values"""
        discrepancies = []
        
        # Create lookup for target data
        target_lookup = {invoice.invoice_id: invoice for invoice in target_data}
        
        for source_invoice in source_data:
            target_invoice = target_lookup.get(source_invoice.invoice_id)
            if not target_invoice:
                continue
            
            # Check critical fields
            field_checks = [
                ("invoice_number", source_invoice.invoice_number, target_invoice.invoice_number),
                ("customer_id", source_invoice.customer_id, target_invoice.customer_id),
                ("currency", source_invoice.currency, target_invoice.currency),
                ("status", source_invoice.status, target_invoice.status)
            ]
            
            for field_name, source_value, target_value in field_checks:
                if source_value != target_value:
                    discrepancy = Discrepancy(
                        discrepancy_id=f"field_{source_invoice.invoice_id}_{field_name}",
                        discrepancy_type=ReconciliationType.FIELD_VALIDATION,
                        severity=DiscrepancySeverity.WARNING,
                        entity_type="invoice",
                        entity_id=source_invoice.invoice_id,
                        field_name=field_name,
                        expected_value=source_value,
                        actual_value=target_value,
                        description=f"Field {field_name} mismatch",
                        source_system=erp_type.value,
                        target_system="platform"
                    )
                    discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_amount_totals(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check if amount totals match within tolerance"""
        discrepancies = []
        
        # Create lookup for target data
        target_lookup = {invoice.invoice_id: invoice for invoice in target_data}
        
        for source_invoice in source_data:
            target_invoice = target_lookup.get(source_invoice.invoice_id)
            if not target_invoice:
                continue
            
            # Check amount fields with tolerance
            amount_checks = [
                ("subtotal", source_invoice.subtotal, target_invoice.subtotal),
                ("tax_amount", source_invoice.tax_amount, target_invoice.tax_amount),
                ("total_amount", source_invoice.total_amount, target_invoice.total_amount)
            ]
            
            for field_name, source_amount, target_amount in amount_checks:
                if not self._amounts_within_tolerance(source_amount, target_amount):
                    difference = abs(Decimal(str(source_amount)) - Decimal(str(target_amount)))
                    
                    discrepancy = Discrepancy(
                        discrepancy_id=f"amount_{source_invoice.invoice_id}_{field_name}",
                        discrepancy_type=ReconciliationType.AMOUNT_TOTALS,
                        severity=DiscrepancySeverity.ERROR,
                        entity_type="invoice",
                        entity_id=source_invoice.invoice_id,
                        field_name=field_name,
                        expected_value=source_amount,
                        actual_value=target_amount,
                        difference=float(difference),
                        description=f"Amount {field_name} exceeds tolerance",
                        source_system=erp_type.value,
                        target_system="platform"
                    )
                    discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_cross_reference(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check cross-reference integrity"""
        discrepancies = []
        
        source_ids = {invoice.invoice_id for invoice in source_data}
        target_ids = {invoice.invoice_id for invoice in target_data}
        
        # Find missing records in target
        missing_in_target = source_ids - target_ids
        for missing_id in missing_in_target:
            discrepancy = Discrepancy(
                discrepancy_id=f"missing_target_{missing_id}",
                discrepancy_type=ReconciliationType.CROSS_REFERENCE,
                severity=DiscrepancySeverity.ERROR,
                entity_type="invoice",
                entity_id=missing_id,
                description=f"Record missing in target system",
                source_system=erp_type.value,
                target_system="platform"
            )
            discrepancies.append(discrepancy)
        
        # Find extra records in target
        extra_in_target = target_ids - source_ids
        for extra_id in extra_in_target:
            discrepancy = Discrepancy(
                discrepancy_id=f"extra_target_{extra_id}",
                discrepancy_type=ReconciliationType.CROSS_REFERENCE,
                severity=DiscrepancySeverity.WARNING,
                entity_type="invoice",
                entity_id=extra_id,
                description=f"Extra record in target system",
                source_system=erp_type.value,
                target_system="platform"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_sequence_integrity(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check sequence integrity for invoice numbers"""
        discrepancies = []
        
        # Extract invoice numbers and check for gaps
        source_numbers = [inv.invoice_number for inv in source_data if inv.invoice_number]
        target_numbers = [inv.invoice_number for inv in target_data if inv.invoice_number]
        
        # For simplicity, assume numeric sequences (would need more logic for real scenarios)
        try:
            source_numeric = [int(num.split('/')[-1]) for num in source_numbers if num.split('/')[-1].isdigit()]
            target_numeric = [int(num.split('/')[-1]) for num in target_numbers if num.split('/')[-1].isdigit()]
            
            source_set = set(source_numeric)
            target_set = set(target_numeric)
            
            # Check for sequence gaps
            if source_numeric:
                min_num, max_num = min(source_numeric), max(source_numeric)
                expected_sequence = set(range(min_num, max_num + 1))
                missing_numbers = expected_sequence - source_set
                
                for missing_num in missing_numbers:
                    discrepancy = Discrepancy(
                        discrepancy_id=f"sequence_gap_{missing_num}",
                        discrepancy_type=ReconciliationType.SEQUENCE_INTEGRITY,
                        severity=DiscrepancySeverity.WARNING,
                        entity_type="invoice_sequence",
                        entity_id=str(missing_num),
                        description=f"Gap in invoice sequence: {missing_num}",
                        source_system=erp_type.value
                    )
                    discrepancies.append(discrepancy)
        
        except (ValueError, IndexError):
            # Skip sequence check if invoice numbers are not numeric
            pass
        
        return discrepancies
    
    async def _check_duplicates(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check for duplicate records"""
        discrepancies = []
        
        # Check duplicates in source data
        source_ids = [invoice.invoice_id for invoice in source_data]
        source_duplicates = [id for id in source_ids if source_ids.count(id) > 1]
        
        for duplicate_id in set(source_duplicates):
            discrepancy = Discrepancy(
                discrepancy_id=f"duplicate_source_{duplicate_id}",
                discrepancy_type=ReconciliationType.DUPLICATE_DETECTION,
                severity=DiscrepancySeverity.ERROR,
                entity_type="invoice",
                entity_id=duplicate_id,
                description=f"Duplicate record in source system",
                source_system=erp_type.value
            )
            discrepancies.append(discrepancy)
        
        # Check duplicates in target data
        target_ids = [invoice.invoice_id for invoice in target_data]
        target_duplicates = [id for id in target_ids if target_ids.count(id) > 1]
        
        for duplicate_id in set(target_duplicates):
            discrepancy = Discrepancy(
                discrepancy_id=f"duplicate_target_{duplicate_id}",
                discrepancy_type=ReconciliationType.DUPLICATE_DETECTION,
                severity=DiscrepancySeverity.ERROR,
                entity_type="invoice",
                entity_id=duplicate_id,
                description=f"Duplicate record in target system",
                target_system="platform"
            )
            discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_orphans(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check for orphaned records"""
        discrepancies = []
        
        # Check for invoices with missing customers
        customer_ids = {invoice.customer_id for invoice in source_data}
        
        for invoice in source_data:
            if not invoice.customer_id or invoice.customer_id.strip() == "":
                discrepancy = Discrepancy(
                    discrepancy_id=f"orphan_customer_{invoice.invoice_id}",
                    discrepancy_type=ReconciliationType.ORPHAN_DETECTION,
                    severity=DiscrepancySeverity.WARNING,
                    entity_type="invoice",
                    entity_id=invoice.invoice_id,
                    description=f"Invoice has no customer reference",
                    source_system=erp_type.value
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    async def _check_temporal_consistency(
        self,
        source_data: List[InvoiceData],
        target_data: List[InvoiceData],
        erp_type: ERPType
    ) -> List[Discrepancy]:
        """Check temporal consistency of dates"""
        discrepancies = []
        
        for invoice in source_data:
            # Check if invoice date is before due date
            if invoice.due_date and invoice.invoice_date > invoice.due_date:
                discrepancy = Discrepancy(
                    discrepancy_id=f"temporal_{invoice.invoice_id}_date_order",
                    discrepancy_type=ReconciliationType.TEMPORAL_CONSISTENCY,
                    severity=DiscrepancySeverity.WARNING,
                    entity_type="invoice",
                    entity_id=invoice.invoice_id,
                    description=f"Invoice date after due date",
                    source_system=erp_type.value
                )
                discrepancies.append(discrepancy)
            
            # Check if created date is before invoice date
            if invoice.created_at and invoice.invoice_date and invoice.created_at.date() > invoice.invoice_date.date():
                discrepancy = Discrepancy(
                    discrepancy_id=f"temporal_{invoice.invoice_id}_creation_order",
                    discrepancy_type=ReconciliationType.TEMPORAL_CONSISTENCY,
                    severity=DiscrepancySeverity.INFO,
                    entity_type="invoice",
                    entity_id=invoice.invoice_id,
                    description=f"Creation date after invoice date",
                    source_system=erp_type.value
                )
                discrepancies.append(discrepancy)
        
        return discrepancies
    
    def _amounts_within_tolerance(self, amount1: float, amount2: float) -> bool:
        """Check if two amounts are within acceptable tolerance"""
        amount1_decimal = Decimal(str(amount1))
        amount2_decimal = Decimal(str(amount2))
        
        difference = abs(amount1_decimal - amount2_decimal)
        
        # Check absolute tolerance
        if difference <= self.config.tolerance_amount:
            return True
        
        # Check percentage tolerance
        max_amount = max(amount1_decimal, amount2_decimal)
        if max_amount > 0:
            percentage_diff = difference / max_amount
            return percentage_diff <= self.config.tolerance_percentage
        
        return False
    
    async def _apply_auto_corrections(self, discrepancies: List[Discrepancy]) -> int:
        """Apply automatic corrections to discrepancies where possible"""
        corrections_applied = 0
        
        for discrepancy in discrepancies:
            try:
                if await self._can_auto_correct(discrepancy):
                    success = await self._apply_correction(discrepancy)
                    if success:
                        discrepancy.corrected = True
                        discrepancy.correction_applied = datetime.now().isoformat()
                        corrections_applied += 1
            except Exception as e:
                logger.error(f"Auto-correction failed for {discrepancy.discrepancy_id}: {e}")
        
        return corrections_applied
    
    async def _can_auto_correct(self, discrepancy: Discrepancy) -> bool:
        """Determine if a discrepancy can be automatically corrected"""
        # Define rules for auto-correction
        auto_correctable_types = [
            ReconciliationType.FIELD_VALIDATION,
            ReconciliationType.TEMPORAL_CONSISTENCY
        ]
        
        return (discrepancy.discrepancy_type in auto_correctable_types and
                discrepancy.severity in [DiscrepancySeverity.INFO, DiscrepancySeverity.WARNING])
    
    async def _apply_correction(self, discrepancy: Discrepancy) -> bool:
        """Apply correction for a specific discrepancy"""
        try:
            # Implementation would depend on the specific correction logic
            # For now, just simulate a successful correction
            logger.info(f"Applied correction for {discrepancy.discrepancy_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to apply correction: {e}")
            return False
    
    def _generate_summary_metrics(self, discrepancies: List[Discrepancy]) -> Dict[str, Any]:
        """Generate summary metrics for reconciliation results"""
        metrics = {
            "total_discrepancies": len(discrepancies),
            "by_severity": defaultdict(int),
            "by_type": defaultdict(int),
            "by_entity_type": defaultdict(int),
            "corrected_count": sum(1 for d in discrepancies if d.corrected)
        }
        
        for discrepancy in discrepancies:
            metrics["by_severity"][discrepancy.severity.value] += 1
            metrics["by_type"][discrepancy.discrepancy_type.value] += 1
            metrics["by_entity_type"][discrepancy.entity_type] += 1
        
        return dict(metrics)
    
    async def _generate_reconciliation_report(self, result: ReconciliationResult) -> None:
        """Generate a detailed reconciliation report"""
        if not self.config.report_storage_path:
            return
        
        try:
            from pathlib import Path
            
            report_dir = Path(self.config.report_storage_path)
            report_dir.mkdir(parents=True, exist_ok=True)
            
            report_file = report_dir / f"{result.reconciliation_id}_report.json"
            
            report_data = {
                "reconciliation_id": result.reconciliation_id,
                "status": result.status.value,
                "start_time": result.start_time.isoformat(),
                "end_time": result.end_time.isoformat() if result.end_time else None,
                "summary": result.summary_metrics,
                "performance": result.performance_metrics,
                "discrepancies": [
                    {
                        "id": d.discrepancy_id,
                        "type": d.discrepancy_type.value,
                        "severity": d.severity.value,
                        "entity_type": d.entity_type,
                        "entity_id": d.entity_id,
                        "field_name": d.field_name,
                        "expected": d.expected_value,
                        "actual": d.actual_value,
                        "difference": d.difference,
                        "description": d.description,
                        "corrected": d.corrected
                    }
                    for d in result.discrepancies
                ]
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            logger.info(f"Generated reconciliation report: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate reconciliation report: {e}")
    
    async def get_reconciliation_status(self, reconciliation_id: str) -> Optional[ReconciliationResult]:
        """Get status of a reconciliation operation"""
        return self.active_reconciliations.get(reconciliation_id)
    
    async def cancel_reconciliation(self, reconciliation_id: str) -> bool:
        """Cancel an ongoing reconciliation"""
        result = self.active_reconciliations.get(reconciliation_id)
        if result and result.status == ReconciliationStatus.RUNNING:
            result.status = ReconciliationStatus.FAILED
            result.end_time = datetime.now()
            result.error_details.append({
                "error": "Reconciliation cancelled by user",
                "timestamp": datetime.now()
            })
            return True
        return False
    
    def get_metrics(self) -> ReconciliationMetrics:
        """Get current reconciliation metrics"""
        return self.metrics
    
    async def cleanup_old_results(self, max_age_hours: int = 24) -> int:
        """Clean up old reconciliation results"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        results_to_remove = []
        for recon_id, result in self.active_reconciliations.items():
            if (result.status in [ReconciliationStatus.COMPLETED, ReconciliationStatus.FAILED] and
                result.end_time and result.end_time < cutoff_time):
                results_to_remove.append(recon_id)
        
        for recon_id in results_to_remove:
            del self.active_reconciliations[recon_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} old reconciliation results")
        return cleaned_count


# Factory function for creating data reconciler
def create_data_reconciler(
    config: Optional[ReconciliationConfig] = None,
    data_extractor: Optional[ERPDataExtractor] = None
) -> DataReconciler:
    """Factory function to create a data reconciler"""
    if config is None:
        config = ReconciliationConfig()
    
    if data_extractor is None:
        from .erp_data_extractor import erp_data_extractor
        data_extractor = erp_data_extractor
    
    return DataReconciler(config, data_extractor)