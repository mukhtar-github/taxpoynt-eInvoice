"""
ERP Data Processor Service

This module handles processing of extracted ERP data for SI workflows,
including data validation, normalization, enrichment, and preparation
for e-invoicing compliance.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

logger = logging.getLogger(__name__)


class ProcessingStatus(Enum):
    """Status of data processing operations"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"


class DataIssueType(Enum):
    """Types of data issues encountered during processing"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    DATA_INCONSISTENCY = "data_inconsistency"
    CALCULATION_ERROR = "calculation_error"
    REFERENCE_VALIDATION_FAILED = "reference_validation_failed"


class ProcessingPriority(Enum):
    """Priority levels for processing operations"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class ProcessingRule:
    """Defines a data processing rule"""
    rule_id: str
    rule_name: str
    rule_type: str  # validation, transformation, enrichment, calculation
    field_targets: List[str]
    condition: str
    action: str
    priority: int = 1
    enabled: bool = True
    description: Optional[str] = None


@dataclass
class DataIssue:
    """Represents a data processing issue"""
    issue_id: str
    issue_type: DataIssueType
    severity: str  # critical, high, medium, low
    field_name: str
    record_id: str
    description: str
    original_value: Optional[Any] = None
    suggested_value: Optional[Any] = None
    auto_correctable: bool = False
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingResult:
    """Result of data processing operation"""
    result_id: str
    status: ProcessingStatus
    total_records: int
    processed_records: int
    failed_records: int
    skipped_records: int
    start_time: datetime
    end_time: Optional[datetime] = None
    processing_duration: Optional[float] = None
    issues_detected: List[DataIssue] = field(default_factory=list)
    corrections_applied: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ERPRecord:
    """Standardized ERP record structure"""
    record_id: str
    record_type: str  # invoice, customer, product, etc.
    source_system: str
    raw_data: Dict[str, Any]
    processed_data: Dict[str, Any] = field(default_factory=dict)
    validation_status: str = "pending"
    enrichment_status: str = "pending"
    processing_notes: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProcessingConfig:
    """Configuration for ERP data processing"""
    enable_auto_correction: bool = True
    enable_data_enrichment: bool = True
    enable_business_validation: bool = True
    max_processing_threads: int = 5
    batch_size: int = 100
    timeout_seconds: int = 300
    retry_attempts: int = 3
    validation_rules_file: Optional[str] = None
    enrichment_sources: List[str] = field(default_factory=list)
    output_format: str = "standardized"
    preserve_original_data: bool = True


class ERPDataProcessor:
    """
    Service for processing ERP data in SI workflows with validation,
    normalization, enrichment, and compliance preparation.
    """
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.processing_rules: Dict[str, ProcessingRule] = {}
        self.active_operations: Dict[str, ProcessingResult] = {}
        self.enrichment_cache: Dict[str, Any] = {}
        
        # Load processing rules
        asyncio.create_task(self._load_processing_rules())
    
    async def process_erp_data(
        self,
        records: List[ERPRecord],
        processing_options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """Process a batch of ERP records"""
        
        result_id = f"proc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        result = ProcessingResult(
            result_id=result_id,
            status=ProcessingStatus.PROCESSING,
            total_records=len(records),
            processed_records=0,
            failed_records=0,
            skipped_records=0,
            start_time=datetime.now()
        )
        
        self.active_operations[result_id] = result
        
        try:
            # Process records in batches
            batch_size = processing_options.get("batch_size", self.config.batch_size)
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                batch_result = await self._process_batch(batch, processing_options)
                
                # Aggregate results
                result.processed_records += batch_result.processed_records
                result.failed_records += batch_result.failed_records
                result.skipped_records += batch_result.skipped_records
                result.issues_detected.extend(batch_result.issues_detected)
                result.corrections_applied += batch_result.corrections_applied
            
            result.status = ProcessingStatus.COMPLETED
            
        except Exception as e:
            logger.error(f"Processing failed for {result_id}: {e}")
            result.status = ProcessingStatus.FAILED
            result.metadata["error"] = str(e)
        
        finally:
            result.end_time = datetime.now()
            result.processing_duration = (result.end_time - result.start_time).total_seconds()
        
        logger.info(f"Completed processing {result_id}: {result.processed_records}/{result.total_records} records")
        return result
    
    async def _process_batch(
        self,
        records: List[ERPRecord],
        processing_options: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """Process a batch of records"""
        
        batch_result = ProcessingResult(
            result_id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            status=ProcessingStatus.PROCESSING,
            total_records=len(records),
            processed_records=0,
            failed_records=0,
            skipped_records=0,
            start_time=datetime.now()
        )
        
        # Process each record
        tasks = []
        semaphore = asyncio.Semaphore(self.config.max_processing_threads)
        
        for record in records:
            task = asyncio.create_task(
                self._process_single_record(record, processing_options, semaphore)
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_result.failed_records += 1
                issue = DataIssue(
                    issue_id=f"proc_error_{i}",
                    issue_type=DataIssueType.DATA_INCONSISTENCY,
                    severity="high",
                    field_name="processing",
                    record_id=records[i].record_id,
                    description=str(result)
                )
                batch_result.issues_detected.append(issue)
            elif result:
                record_result, issues, corrections = result
                if record_result:
                    batch_result.processed_records += 1
                else:
                    batch_result.failed_records += 1
                
                batch_result.issues_detected.extend(issues)
                batch_result.corrections_applied += corrections
        
        batch_result.end_time = datetime.now()
        batch_result.status = ProcessingStatus.COMPLETED
        
        return batch_result
    
    async def _process_single_record(
        self,
        record: ERPRecord,
        processing_options: Optional[Dict[str, Any]],
        semaphore: asyncio.Semaphore
    ) -> Tuple[bool, List[DataIssue], int]:
        """Process a single ERP record"""
        
        async with semaphore:
            issues = []
            corrections = 0
            
            try:
                # Step 1: Validate record
                validation_issues = await self._validate_record(record)
                issues.extend(validation_issues)
                
                # Step 2: Apply auto-corrections if enabled
                if self.config.enable_auto_correction:
                    corrections = await self._apply_auto_corrections(record, validation_issues)
                
                # Step 3: Transform and normalize data
                await self._transform_record_data(record)
                
                # Step 4: Enrich data if enabled
                if self.config.enable_data_enrichment:
                    await self._enrich_record_data(record)
                
                # Step 5: Apply business validation
                if self.config.enable_business_validation:
                    business_issues = await self._validate_business_rules(record)
                    issues.extend(business_issues)
                
                # Step 6: Calculate derived fields
                await self._calculate_derived_fields(record)
                
                # Step 7: Finalize processing
                await self._finalize_record_processing(record)
                
                record.validation_status = "completed" if not issues else "issues_detected"
                record.updated_at = datetime.now()
                
                return True, issues, corrections
                
            except Exception as e:
                logger.error(f"Failed to process record {record.record_id}: {e}")
                issue = DataIssue(
                    issue_id=f"proc_{record.record_id}",
                    issue_type=DataIssueType.DATA_INCONSISTENCY,
                    severity="critical",
                    field_name="processing",
                    record_id=record.record_id,
                    description=str(e)
                )
                return False, [issue], corrections
    
    async def _validate_record(self, record: ERPRecord) -> List[DataIssue]:
        """Validate record against processing rules"""
        issues = []
        
        try:
            # Get validation rules for this record type
            validation_rules = [
                rule for rule in self.processing_rules.values()
                if rule.rule_type == "validation" and rule.enabled
            ]
            
            for rule in validation_rules:
                rule_issues = await self._apply_validation_rule(record, rule)
                issues.extend(rule_issues)
            
        except Exception as e:
            logger.error(f"Validation failed for record {record.record_id}: {e}")
        
        return issues
    
    async def _apply_validation_rule(
        self,
        record: ERPRecord,
        rule: ProcessingRule
    ) -> List[DataIssue]:
        """Apply a specific validation rule to a record"""
        issues = []
        
        try:
            for field_name in rule.field_targets:
                field_value = record.raw_data.get(field_name)
                
                # Check if field is required
                if rule.condition == "required" and (field_value is None or str(field_value).strip() == ""):
                    issue = DataIssue(
                        issue_id=f"val_{record.record_id}_{field_name}",
                        issue_type=DataIssueType.MISSING_REQUIRED_FIELD,
                        severity="high",
                        field_name=field_name,
                        record_id=record.record_id,
                        description=f"Required field {field_name} is missing or empty",
                        original_value=field_value,
                        auto_correctable=False
                    )
                    issues.append(issue)
                
                # Check field format
                elif rule.condition.startswith("format:") and field_value:
                    format_type = rule.condition.split(":")[1]
                    if not self._validate_field_format(field_value, format_type):
                        issue = DataIssue(
                            issue_id=f"fmt_{record.record_id}_{field_name}",
                            issue_type=DataIssueType.INVALID_FORMAT,
                            severity="medium",
                            field_name=field_name,
                            record_id=record.record_id,
                            description=f"Field {field_name} has invalid format (expected: {format_type})",
                            original_value=field_value,
                            auto_correctable=True
                        )
                        issues.append(issue)
                
                # Check value range
                elif rule.condition.startswith("range:") and field_value:
                    range_spec = rule.condition.split(":")[1]
                    if not self._validate_field_range(field_value, range_spec):
                        issue = DataIssue(
                            issue_id=f"rng_{record.record_id}_{field_name}",
                            issue_type=DataIssueType.BUSINESS_RULE_VIOLATION,
                            severity="medium",
                            field_name=field_name,
                            record_id=record.record_id,
                            description=f"Field {field_name} is outside valid range ({range_spec})",
                            original_value=field_value,
                            auto_correctable=False
                        )
                        issues.append(issue)
        
        except Exception as e:
            logger.error(f"Failed to apply validation rule {rule.rule_id}: {e}")
        
        return issues
    
    def _validate_field_format(self, value: Any, format_type: str) -> bool:
        """Validate field format"""
        try:
            if format_type == "email":
                import re
                pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return bool(re.match(pattern, str(value)))
            
            elif format_type == "phone":
                import re
                pattern = r'^\+?[\d\s\-\(\)]{10,}$'
                return bool(re.match(pattern, str(value)))
            
            elif format_type == "decimal":
                try:
                    Decimal(str(value))
                    return True
                except:
                    return False
            
            elif format_type == "integer":
                try:
                    int(value)
                    return True
                except:
                    return False
            
            elif format_type == "date":
                try:
                    datetime.fromisoformat(str(value))
                    return True
                except:
                    return False
            
            elif format_type == "tin":
                # Nigerian TIN format validation
                import re
                pattern = r'^\d{8}-\d{4}$'
                return bool(re.match(pattern, str(value)))
            
            return True
            
        except Exception:
            return False
    
    def _validate_field_range(self, value: Any, range_spec: str) -> bool:
        """Validate field range"""
        try:
            if "," in range_spec:
                min_val, max_val = map(float, range_spec.split(","))
                val = float(value)
                return min_val <= val <= max_val
            elif range_spec.startswith("min:"):
                min_val = float(range_spec[4:])
                return float(value) >= min_val
            elif range_spec.startswith("max:"):
                max_val = float(range_spec[4:])
                return float(value) <= max_val
            
            return True
            
        except Exception:
            return False
    
    async def _apply_auto_corrections(
        self,
        record: ERPRecord,
        issues: List[DataIssue]
    ) -> int:
        """Apply automatic corrections to record"""
        corrections = 0
        
        try:
            for issue in issues:
                if issue.auto_correctable:
                    corrected = await self._apply_single_correction(record, issue)
                    if corrected:
                        corrections += 1
        
        except Exception as e:
            logger.error(f"Auto-correction failed for record {record.record_id}: {e}")
        
        return corrections
    
    async def _apply_single_correction(
        self,
        record: ERPRecord,
        issue: DataIssue
    ) -> bool:
        """Apply a single correction to a record"""
        try:
            field_name = issue.field_name
            original_value = issue.original_value
            
            if issue.issue_type == DataIssueType.INVALID_FORMAT:
                # Try to correct format issues
                if "decimal" in issue.description.lower():
                    try:
                        # Clean decimal value
                        cleaned = str(original_value).replace(",", "").strip()
                        corrected_value = Decimal(cleaned)
                        record.raw_data[field_name] = str(corrected_value)
                        issue.suggested_value = str(corrected_value)
                        record.processing_notes.append(f"Auto-corrected {field_name} format")
                        return True
                    except:
                        pass
                
                elif "phone" in issue.description.lower():
                    # Clean phone number
                    import re
                    cleaned = re.sub(r'[^\d\+]', '', str(original_value))
                    if len(cleaned) >= 10:
                        record.raw_data[field_name] = cleaned
                        issue.suggested_value = cleaned
                        record.processing_notes.append(f"Auto-corrected {field_name} format")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to apply correction for {issue.issue_id}: {e}")
            return False
    
    async def _transform_record_data(self, record: ERPRecord) -> None:
        """Transform record data to standardized format"""
        try:
            # Initialize processed data
            record.processed_data = record.raw_data.copy()
            
            # Apply transformation rules
            transformation_rules = [
                rule for rule in self.processing_rules.values()
                if rule.rule_type == "transformation" and rule.enabled
            ]
            
            for rule in transformation_rules:
                await self._apply_transformation_rule(record, rule)
            
            # Standardize common fields
            await self._standardize_common_fields(record)
            
        except Exception as e:
            logger.error(f"Transformation failed for record {record.record_id}: {e}")
    
    async def _apply_transformation_rule(
        self,
        record: ERPRecord,
        rule: ProcessingRule
    ) -> None:
        """Apply a transformation rule to a record"""
        try:
            if rule.action == "normalize_currency":
                for field_name in rule.field_targets:
                    if field_name in record.processed_data:
                        value = record.processed_data[field_name]
                        normalized = await self._normalize_currency_value(value)
                        record.processed_data[field_name] = normalized
            
            elif rule.action == "standardize_date":
                for field_name in rule.field_targets:
                    if field_name in record.processed_data:
                        value = record.processed_data[field_name]
                        standardized = await self._standardize_date_value(value)
                        record.processed_data[field_name] = standardized
            
            elif rule.action == "uppercase":
                for field_name in rule.field_targets:
                    if field_name in record.processed_data:
                        value = record.processed_data[field_name]
                        record.processed_data[field_name] = str(value).upper()
            
            elif rule.action == "trim_whitespace":
                for field_name in rule.field_targets:
                    if field_name in record.processed_data:
                        value = record.processed_data[field_name]
                        record.processed_data[field_name] = str(value).strip()
        
        except Exception as e:
            logger.error(f"Failed to apply transformation rule {rule.rule_id}: {e}")
    
    async def _standardize_common_fields(self, record: ERPRecord) -> None:
        """Standardize common fields across all record types"""
        try:
            # Standardize amount fields
            amount_fields = ["amount", "total", "subtotal", "tax_amount", "discount"]
            for field in amount_fields:
                if field in record.processed_data:
                    value = record.processed_data[field]
                    if value is not None:
                        record.processed_data[field] = float(Decimal(str(value)).quantize(
                            Decimal('0.01'), rounding=ROUND_HALF_UP
                        ))
            
            # Standardize date fields
            date_fields = ["date", "created_at", "updated_at", "due_date", "invoice_date"]
            for field in date_fields:
                if field in record.processed_data:
                    value = record.processed_data[field]
                    if value:
                        standardized = await self._standardize_date_value(value)
                        record.processed_data[field] = standardized
            
            # Standardize text fields
            text_fields = ["description", "notes", "comments"]
            for field in text_fields:
                if field in record.processed_data:
                    value = record.processed_data[field]
                    if value:
                        record.processed_data[field] = str(value).strip()
        
        except Exception as e:
            logger.error(f"Failed to standardize common fields for {record.record_id}: {e}")
    
    async def _normalize_currency_value(self, value: Any) -> float:
        """Normalize currency value"""
        try:
            if value is None:
                return 0.0
            
            # Remove currency symbols and commas
            cleaned = str(value).replace(",", "").replace("$", "").replace("₦", "").strip()
            return float(Decimal(cleaned).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        except Exception:
            return 0.0
    
    async def _standardize_date_value(self, value: Any) -> Optional[str]:
        """Standardize date value to ISO format"""
        try:
            if not value:
                return None
            
            # Try to parse various date formats
            date_formats = [
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y",
                "%m/%d/%Y",
                "%d-%m-%Y",
                "%Y/%m/%d"
            ]
            
            date_str = str(value).strip()
            
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.isoformat()
                except ValueError:
                    continue
            
            # Try ISO format directly
            try:
                parsed_date = datetime.fromisoformat(date_str)
                return parsed_date.isoformat()
            except ValueError:
                pass
            
            return None
        
        except Exception:
            return None
    
    async def _enrich_record_data(self, record: ERPRecord) -> None:
        """Enrich record with additional data"""
        try:
            # Enrich customer data
            if "customer_id" in record.processed_data:
                customer_data = await self._get_customer_enrichment(
                    record.processed_data["customer_id"]
                )
                if customer_data:
                    record.processed_data.update(customer_data)
            
            # Enrich product data
            if "product_id" in record.processed_data:
                product_data = await self._get_product_enrichment(
                    record.processed_data["product_id"]
                )
                if product_data:
                    record.processed_data.update(product_data)
            
            # Enrich with tax information
            await self._enrich_tax_information(record)
            
            record.enrichment_status = "completed"
        
        except Exception as e:
            logger.error(f"Enrichment failed for record {record.record_id}: {e}")
            record.enrichment_status = "failed"
    
    async def _get_customer_enrichment(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get customer enrichment data"""
        try:
            # Check cache first
            cache_key = f"customer_{customer_id}"
            if cache_key in self.enrichment_cache:
                return self.enrichment_cache[cache_key]
            
            # Mock enrichment - in practice, this would query external sources
            enrichment_data = {
                "customer_tin_verified": True,
                "customer_category": "business",
                "tax_exempt": False
            }
            
            # Cache the result
            self.enrichment_cache[cache_key] = enrichment_data
            return enrichment_data
        
        except Exception as e:
            logger.error(f"Failed to enrich customer {customer_id}: {e}")
            return None
    
    async def _get_product_enrichment(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product enrichment data"""
        try:
            # Check cache first
            cache_key = f"product_{product_id}"
            if cache_key in self.enrichment_cache:
                return self.enrichment_cache[cache_key]
            
            # Mock enrichment - in practice, this would query external sources
            enrichment_data = {
                "product_category": "goods",
                "tax_category": "standard",
                "hscode": "8471.30.00"
            }
            
            # Cache the result
            self.enrichment_cache[cache_key] = enrichment_data
            return enrichment_data
        
        except Exception as e:
            logger.error(f"Failed to enrich product {product_id}: {e}")
            return None
    
    async def _enrich_tax_information(self, record: ERPRecord) -> None:
        """Enrich record with tax information"""
        try:
            # Calculate tax rates based on product category and location
            if "amount" in record.processed_data:
                amount = float(record.processed_data["amount"])
                
                # Default VAT rate for Nigeria
                vat_rate = 0.075  # 7.5%
                
                if "tax_amount" not in record.processed_data:
                    record.processed_data["tax_amount"] = amount * vat_rate
                
                if "total_amount" not in record.processed_data:
                    tax_amount = record.processed_data.get("tax_amount", 0)
                    record.processed_data["total_amount"] = amount + tax_amount
        
        except Exception as e:
            logger.error(f"Failed to enrich tax information for {record.record_id}: {e}")
    
    async def _validate_business_rules(self, record: ERPRecord) -> List[DataIssue]:
        """Validate record against business rules"""
        issues = []
        
        try:
            # Business rule: Invoice total should equal sum of line items
            if record.record_type == "invoice":
                issues.extend(await self._validate_invoice_totals(record))
            
            # Business rule: Dates should be logical
            issues.extend(await self._validate_date_logic(record))
            
            # Business rule: Required fields for tax compliance
            issues.extend(await self._validate_tax_compliance(record))
        
        except Exception as e:
            logger.error(f"Business validation failed for {record.record_id}: {e}")
        
        return issues
    
    async def _validate_invoice_totals(self, record: ERPRecord) -> List[DataIssue]:
        """Validate invoice total calculations"""
        issues = []
        
        try:
            data = record.processed_data
            
            if "line_items" in data and "total_amount" in data:
                line_total = sum(
                    float(item.get("total", 0)) 
                    for item in data["line_items"] 
                    if isinstance(item, dict)
                )
                
                invoice_total = float(data["total_amount"])
                
                # Allow small rounding differences
                if abs(line_total - invoice_total) > 0.02:
                    issue = DataIssue(
                        issue_id=f"total_{record.record_id}",
                        issue_type=DataIssueType.CALCULATION_ERROR,
                        severity="high",
                        field_name="total_amount",
                        record_id=record.record_id,
                        description=f"Invoice total ({invoice_total}) doesn't match line items total ({line_total})",
                        original_value=invoice_total,
                        suggested_value=line_total,
                        auto_correctable=True
                    )
                    issues.append(issue)
        
        except Exception as e:
            logger.error(f"Failed to validate invoice totals: {e}")
        
        return issues
    
    async def _validate_date_logic(self, record: ERPRecord) -> List[DataIssue]:
        """Validate date logic"""
        issues = []
        
        try:
            data = record.processed_data
            
            # Check if due date is after invoice date
            if "invoice_date" in data and "due_date" in data:
                try:
                    invoice_date = datetime.fromisoformat(data["invoice_date"])
                    due_date = datetime.fromisoformat(data["due_date"])
                    
                    if due_date < invoice_date:
                        issue = DataIssue(
                            issue_id=f"date_logic_{record.record_id}",
                            issue_type=DataIssueType.BUSINESS_RULE_VIOLATION,
                            severity="medium",
                            field_name="due_date",
                            record_id=record.record_id,
                            description="Due date is before invoice date",
                            auto_correctable=False
                        )
                        issues.append(issue)
                
                except ValueError:
                    pass  # Date validation already handled elsewhere
        
        except Exception as e:
            logger.error(f"Failed to validate date logic: {e}")
        
        return issues
    
    async def _validate_tax_compliance(self, record: ERPRecord) -> List[DataIssue]:
        """Validate tax compliance requirements"""
        issues = []
        
        try:
            data = record.processed_data
            
            # Check for required tax fields
            required_tax_fields = ["tax_amount", "customer_tin"]
            
            for field in required_tax_fields:
                if field not in data or not data[field]:
                    issue = DataIssue(
                        issue_id=f"tax_{field}_{record.record_id}",
                        issue_type=DataIssueType.MISSING_REQUIRED_FIELD,
                        severity="critical",
                        field_name=field,
                        record_id=record.record_id,
                        description=f"Tax compliance field {field} is required",
                        auto_correctable=False
                    )
                    issues.append(issue)
        
        except Exception as e:
            logger.error(f"Failed to validate tax compliance: {e}")
        
        return issues
    
    async def _calculate_derived_fields(self, record: ERPRecord) -> None:
        """Calculate derived fields"""
        try:
            data = record.processed_data
            
            # Calculate subtotal if missing
            if "subtotal" not in data and "total_amount" in data and "tax_amount" in data:
                total = float(data["total_amount"])
                tax = float(data["tax_amount"])
                data["subtotal"] = total - tax
            
            # Calculate tax percentage
            if "tax_amount" in data and "subtotal" in data:
                tax_amount = float(data["tax_amount"])
                subtotal = float(data["subtotal"])
                if subtotal > 0:
                    data["tax_percentage"] = (tax_amount / subtotal) * 100
            
            # Generate processing metadata
            data["processing_metadata"] = {
                "processed_at": datetime.now().isoformat(),
                "processor_version": "1.0.0",
                "validation_status": record.validation_status,
                "enrichment_status": record.enrichment_status
            }
        
        except Exception as e:
            logger.error(f"Failed to calculate derived fields for {record.record_id}: {e}")
    
    async def _finalize_record_processing(self, record: ERPRecord) -> None:
        """Finalize record processing"""
        try:
            # Set final processing status
            if record.validation_status == "completed" and record.enrichment_status == "completed":
                record.processed_data["processing_status"] = "ready_for_submission"
            else:
                record.processed_data["processing_status"] = "requires_review"
            
            # Add processing summary
            record.processed_data["processing_summary"] = {
                "original_fields": len(record.raw_data),
                "processed_fields": len(record.processed_data),
                "notes_count": len(record.processing_notes),
                "processing_duration": (datetime.now() - record.created_at).total_seconds()
            }
            
            # Mark as updated
            record.updated_at = datetime.now()
        
        except Exception as e:
            logger.error(f"Failed to finalize processing for {record.record_id}: {e}")
    
    async def _load_processing_rules(self) -> None:
        """Load processing rules from configuration"""
        try:
            # Load default processing rules
            default_rules = [
                ProcessingRule(
                    rule_id="REQ_001",
                    rule_name="Invoice Number Required",
                    rule_type="validation",
                    field_targets=["invoice_number"],
                    condition="required",
                    action="validate_required",
                    priority=1
                ),
                ProcessingRule(
                    rule_id="FMT_001",
                    rule_name="Amount Format",
                    rule_type="validation",
                    field_targets=["amount", "total_amount", "tax_amount"],
                    condition="format:decimal",
                    action="validate_format",
                    priority=2
                ),
                ProcessingRule(
                    rule_id="TXF_001",
                    rule_name="Normalize Currency",
                    rule_type="transformation",
                    field_targets=["amount", "total_amount", "tax_amount", "subtotal"],
                    condition="always",
                    action="normalize_currency",
                    priority=1
                ),
                ProcessingRule(
                    rule_id="TXF_002",
                    rule_name="Standardize Dates",
                    rule_type="transformation",
                    field_targets=["invoice_date", "due_date", "created_at"],
                    condition="always",
                    action="standardize_date",
                    priority=1
                )
            ]
            
            for rule in default_rules:
                self.processing_rules[rule.rule_id] = rule
            
            logger.info(f"Loaded {len(default_rules)} processing rules")
        
        except Exception as e:
            logger.error(f"Failed to load processing rules: {e}")
    
    def get_processing_status(self, result_id: str) -> Optional[ProcessingResult]:
        """Get status of a processing operation"""
        return self.active_operations.get(result_id)
    
    def get_active_operations(self) -> List[str]:
        """Get list of active operation IDs"""
        return list(self.active_operations.keys())
    
    async def cleanup_completed_operations(self, max_age_hours: int = 24) -> int:
        """Clean up completed operations"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        operations_to_remove = []
        for op_id, result in self.active_operations.items():
            if (result.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED] and
                result.end_time and result.end_time < cutoff_time):
                operations_to_remove.append(op_id)
        
        for op_id in operations_to_remove:
            del self.active_operations[op_id]
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} completed operations")
        return cleaned_count


# Factory function for creating ERP data processor
def create_erp_data_processor(config: Optional[ProcessingConfig] = None) -> ERPDataProcessor:
    """Factory function to create an ERP data processor"""
    if config is None:
        config = ProcessingConfig()
    
    return ERPDataProcessor(config)