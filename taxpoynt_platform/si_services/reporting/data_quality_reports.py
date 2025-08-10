"""
Data Quality Reports Service

This module generates comprehensive data quality metrics and reports for SI services,
tracking data completeness, accuracy, consistency, validity, and integrity across
all integrated ERP systems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import re
from pathlib import Path
from collections import defaultdict, Counter
from decimal import Decimal

logger = logging.getLogger(__name__)


class DataQualityDimension(Enum):
    """Data quality dimensions"""
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    TIMELINESS = "timeliness"
    INTEGRITY = "integrity"


class QualityScore(Enum):
    """Quality score categories"""
    EXCELLENT = "excellent"  # 95-100%
    GOOD = "good"           # 85-94%
    FAIR = "fair"           # 70-84%
    POOR = "poor"           # 50-69%
    CRITICAL = "critical"   # 0-49%


class DataIssueType(Enum):
    """Types of data quality issues"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    DUPLICATE_RECORD = "duplicate_record"
    INCONSISTENT_VALUE = "inconsistent_value"
    OUTDATED_RECORD = "outdated_record"
    INVALID_REFERENCE = "invalid_reference"
    RANGE_VIOLATION = "range_violation"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"


@dataclass
class DataQualityRule:
    """Defines a data quality validation rule"""
    rule_id: str
    rule_name: str
    dimension: DataQualityDimension
    field_name: str
    rule_type: str  # required, format, range, business_logic
    validation_expression: str
    error_message: str
    severity: str = "error"  # error, warning, info
    enabled: bool = True
    description: Optional[str] = None


@dataclass
class DataIssue:
    """Represents a data quality issue"""
    issue_id: str
    issue_type: DataIssueType
    severity: str
    dimension: DataQualityDimension
    entity_type: str
    entity_id: str
    field_name: str
    current_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    rule_violated: Optional[str] = None
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)
    source_system: Optional[str] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None


@dataclass
class FieldQualityMetrics:
    """Quality metrics for a specific field"""
    field_name: str
    total_records: int
    non_null_count: int
    valid_count: int
    invalid_count: int
    unique_count: int
    duplicate_count: int
    completeness_score: float
    validity_score: float
    uniqueness_score: float
    common_issues: List[str] = field(default_factory=list)
    sample_invalid_values: List[Any] = field(default_factory=list)


@dataclass
class EntityQualityMetrics:
    """Quality metrics for an entity type (e.g., invoices, customers)"""
    entity_type: str
    total_records: int
    valid_records: int
    invalid_records: int
    duplicate_records: int
    overall_quality_score: float
    dimension_scores: Dict[DataQualityDimension, float] = field(default_factory=dict)
    field_metrics: List[FieldQualityMetrics] = field(default_factory=list)
    critical_issues: int = 0
    warning_issues: int = 0
    info_issues: int = 0


@dataclass
class SystemQualityMetrics:
    """Quality metrics for an entire ERP system"""
    system_name: str
    system_type: str
    overall_quality_score: float
    total_records: int
    valid_records: int
    total_issues: int
    entity_metrics: List[EntityQualityMetrics] = field(default_factory=list)
    trend_data: Dict[str, List[float]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DataQualityReport:
    """Comprehensive data quality report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    overall_quality_score: float
    system_metrics: List[SystemQualityMetrics] = field(default_factory=list)
    dimension_scores: Dict[DataQualityDimension, float] = field(default_factory=dict)
    top_issues: List[DataIssue] = field(default_factory=list)
    quality_trends: Dict[str, List[Tuple[datetime, float]]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    summary_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityConfig:
    """Configuration for data quality assessment"""
    enable_completeness_check: bool = True
    enable_validity_check: bool = True
    enable_consistency_check: bool = True
    enable_uniqueness_check: bool = True
    enable_timeliness_check: bool = True
    enable_integrity_check: bool = True
    completeness_threshold: float = 0.95
    validity_threshold: float = 0.90
    consistency_threshold: float = 0.95
    sample_size_for_analysis: int = 10000
    max_issues_per_report: int = 1000
    quality_rules_file: Optional[str] = None
    output_path: Optional[str] = None


class DataQualityService:
    """
    Service for assessing and reporting data quality across SI integrations
    """
    
    def __init__(self, config: QualityConfig):
        self.config = config
        self.quality_rules: Dict[str, List[DataQualityRule]] = {}
        self.quality_cache: Dict[str, DataQualityReport] = {}
        self.issue_tracker: Dict[str, List[DataIssue]] = defaultdict(list)
        
        # Setup output directory
        if config.output_path:
            self.output_path = Path(config.output_path)
            self.output_path.mkdir(parents=True, exist_ok=True)
        else:
            self.output_path = None
        
        # Load quality rules
        asyncio.create_task(self._load_quality_rules())
    
    async def generate_quality_report(
        self,
        systems: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> DataQualityReport:
        """Generate a comprehensive data quality report"""
        
        if not start_date:
            start_date = datetime.now() - timedelta(days=1)
        if not end_date:
            end_date = datetime.now()
        
        report_id = f"quality_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        
        report = DataQualityReport(
            report_id=report_id,
            generated_at=datetime.now(),
            period_start=start_date,
            period_end=end_date,
            overall_quality_score=0.0
        )
        
        try:
            # Assess quality for each system
            target_systems = systems or self._get_available_systems()
            
            for system_name in target_systems:
                system_metrics = await self._assess_system_quality(
                    system_name, start_date, end_date
                )
                report.system_metrics.append(system_metrics)
            
            # Calculate overall scores
            report.overall_quality_score = self._calculate_overall_score(report.system_metrics)
            report.dimension_scores = self._calculate_dimension_scores(report.system_metrics)
            
            # Identify top issues
            report.top_issues = await self._identify_top_issues(target_systems, start_date, end_date)
            
            # Generate quality trends
            report.quality_trends = await self._generate_quality_trends(target_systems)
            
            # Generate recommendations
            report.recommendations = self._generate_recommendations(report)
            
            # Calculate summary statistics
            report.summary_stats = self._calculate_summary_stats(report)
            
            # Cache the report
            self.quality_cache[report_id] = report
            
            # Export if configured
            if self.output_path:
                await self._export_quality_report(report)
            
            logger.info(f"Generated data quality report {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate quality report: {e}")
            raise
    
    async def _assess_system_quality(
        self,
        system_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> SystemQualityMetrics:
        """Assess data quality for a specific system"""
        
        system_metrics = SystemQualityMetrics(
            system_name=system_name,
            system_type=self._get_system_type(system_name),
            overall_quality_score=0.0,
            total_records=0,
            valid_records=0,
            total_issues=0
        )
        
        try:
            # Get entity types for this system
            entity_types = await self._get_entity_types(system_name)
            
            for entity_type in entity_types:
                entity_metrics = await self._assess_entity_quality(
                    system_name, entity_type, start_date, end_date
                )
                system_metrics.entity_metrics.append(entity_metrics)
                
                # Aggregate metrics
                system_metrics.total_records += entity_metrics.total_records
                system_metrics.valid_records += entity_metrics.valid_records
                system_metrics.total_issues += (
                    entity_metrics.critical_issues +
                    entity_metrics.warning_issues +
                    entity_metrics.info_issues
                )
            
            # Calculate overall system quality score
            if system_metrics.entity_metrics:
                system_metrics.overall_quality_score = sum(
                    em.overall_quality_score for em in system_metrics.entity_metrics
                ) / len(system_metrics.entity_metrics)
            
            # Generate trend data
            system_metrics.trend_data = await self._generate_system_trends(system_name)
            
        except Exception as e:
            logger.error(f"Failed to assess quality for system {system_name}: {e}")
        
        return system_metrics
    
    async def _assess_entity_quality(
        self,
        system_name: str,
        entity_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> EntityQualityMetrics:
        """Assess data quality for a specific entity type"""
        
        entity_metrics = EntityQualityMetrics(
            entity_type=entity_type,
            total_records=0,
            valid_records=0,
            invalid_records=0,
            duplicate_records=0,
            overall_quality_score=0.0
        )
        
        try:
            # Get sample data for analysis
            sample_data = await self._get_sample_data(system_name, entity_type, start_date, end_date)
            entity_metrics.total_records = len(sample_data)
            
            if not sample_data:
                return entity_metrics
            
            # Get field definitions
            field_definitions = self._get_field_definitions(entity_type)
            
            # Assess each field
            for field_name in field_definitions:
                field_metrics = await self._assess_field_quality(
                    field_name, sample_data, entity_type
                )
                entity_metrics.field_metrics.append(field_metrics)
            
            # Calculate dimension scores
            entity_metrics.dimension_scores = await self._calculate_entity_dimension_scores(
                entity_metrics.field_metrics, sample_data, entity_type
            )
            
            # Calculate overall entity score
            entity_metrics.overall_quality_score = sum(
                entity_metrics.dimension_scores.values()
            ) / len(entity_metrics.dimension_scores)
            
            # Count valid/invalid records
            entity_metrics.valid_records = sum(
                1 for record in sample_data 
                if self._is_record_valid(record, entity_type)
            )
            entity_metrics.invalid_records = entity_metrics.total_records - entity_metrics.valid_records
            
            # Count duplicates
            entity_metrics.duplicate_records = await self._count_duplicates(sample_data, entity_type)
            
            # Count issues by severity
            issues = await self._get_entity_issues(system_name, entity_type, start_date, end_date)
            entity_metrics.critical_issues = sum(1 for i in issues if i.severity == "critical")
            entity_metrics.warning_issues = sum(1 for i in issues if i.severity == "warning")
            entity_metrics.info_issues = sum(1 for i in issues if i.severity == "info")
            
        except Exception as e:
            logger.error(f"Failed to assess entity quality for {entity_type}: {e}")
        
        return entity_metrics
    
    async def _assess_field_quality(
        self,
        field_name: str,
        sample_data: List[Dict],
        entity_type: str
    ) -> FieldQualityMetrics:
        """Assess quality metrics for a specific field"""
        
        total_records = len(sample_data)
        field_values = [record.get(field_name) for record in sample_data]
        
        # Count non-null values
        non_null_values = [v for v in field_values if v is not None and v != ""]
        non_null_count = len(non_null_values)
        
        # Validate values against rules
        valid_values = []
        invalid_values = []
        
        for value in non_null_values:
            if await self._validate_field_value(field_name, value, entity_type):
                valid_values.append(value)
            else:
                invalid_values.append(value)
        
        valid_count = len(valid_values)
        invalid_count = len(invalid_values)
        
        # Count unique values
        unique_values = set(str(v) for v in non_null_values if v is not None)
        unique_count = len(unique_values)
        duplicate_count = non_null_count - unique_count
        
        # Calculate scores
        completeness_score = (non_null_count / total_records * 100) if total_records > 0 else 0
        validity_score = (valid_count / non_null_count * 100) if non_null_count > 0 else 0
        uniqueness_score = (unique_count / non_null_count * 100) if non_null_count > 0 else 100
        
        # Identify common issues
        common_issues = await self._identify_field_issues(field_name, invalid_values, entity_type)
        
        return FieldQualityMetrics(
            field_name=field_name,
            total_records=total_records,
            non_null_count=non_null_count,
            valid_count=valid_count,
            invalid_count=invalid_count,
            unique_count=unique_count,
            duplicate_count=duplicate_count,
            completeness_score=completeness_score,
            validity_score=validity_score,
            uniqueness_score=uniqueness_score,
            common_issues=common_issues,
            sample_invalid_values=invalid_values[:10]  # Sample of invalid values
        )
    
    async def _validate_field_value(
        self,
        field_name: str,
        value: Any,
        entity_type: str
    ) -> bool:
        """Validate a field value against quality rules"""
        
        try:
            # Get rules for this field
            rules = self.quality_rules.get(entity_type, [])
            field_rules = [r for r in rules if r.field_name == field_name]
            
            for rule in field_rules:
                if not rule.enabled:
                    continue
                
                if rule.rule_type == "required":
                    if value is None or str(value).strip() == "":
                        return False
                
                elif rule.rule_type == "format":
                    if not self._validate_format(value, rule.validation_expression):
                        return False
                
                elif rule.rule_type == "range":
                    if not self._validate_range(value, rule.validation_expression):
                        return False
                
                elif rule.rule_type == "business_logic":
                    if not await self._validate_business_logic(value, rule.validation_expression):
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Validation failed for field {field_name}: {e}")
            return False
    
    def _validate_format(self, value: Any, pattern: str) -> bool:
        """Validate value against format pattern"""
        try:
            if pattern.startswith("regex:"):
                regex_pattern = pattern[6:]
                return bool(re.match(regex_pattern, str(value)))
            elif pattern == "email":
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                return bool(re.match(email_pattern, str(value)))
            elif pattern == "phone":
                phone_pattern = r'^\+?[\d\s\-\(\)]{10,}$'
                return bool(re.match(phone_pattern, str(value)))
            elif pattern == "numeric":
                try:
                    float(value)
                    return True
                except ValueError:
                    return False
            elif pattern == "integer":
                try:
                    int(value)
                    return True
                except ValueError:
                    return False
            elif pattern == "date":
                try:
                    datetime.fromisoformat(str(value))
                    return True
                except ValueError:
                    return False
            else:
                return True
        except Exception:
            return False
    
    def _validate_range(self, value: Any, range_expression: str) -> bool:
        """Validate value against range constraints"""
        try:
            if range_expression.startswith("min:"):
                min_val = float(range_expression[4:])
                return float(value) >= min_val
            elif range_expression.startswith("max:"):
                max_val = float(range_expression[4:])
                return float(value) <= max_val
            elif "," in range_expression:
                min_val, max_val = map(float, range_expression.split(","))
                val = float(value)
                return min_val <= val <= max_val
            else:
                return True
        except (ValueError, TypeError):
            return False
    
    async def _validate_business_logic(self, value: Any, logic_expression: str) -> bool:
        """Validate value against business logic rules"""
        try:
            # This would implement specific business logic validation
            # For now, return True as placeholder
            return True
        except Exception:
            return False
    
    async def _identify_field_issues(
        self,
        field_name: str,
        invalid_values: List[Any],
        entity_type: str
    ) -> List[str]:
        """Identify common issues for a field"""
        issues = []
        
        if not invalid_values:
            return issues
        
        # Analyze invalid values to identify patterns
        value_counter = Counter(str(v) for v in invalid_values)
        most_common = value_counter.most_common(3)
        
        for value, count in most_common:
            if count > 1:
                issues.append(f"Common invalid value: '{value}' ({count} occurrences)")
        
        # Check for specific issue types
        if any(str(v).strip() == "" for v in invalid_values):
            issues.append("Empty string values found")
        
        if any(v is None for v in invalid_values):
            issues.append("Null values found")
        
        # Field-specific checks
        if field_name.lower().endswith("email"):
            issues.append("Invalid email format")
        elif field_name.lower().endswith("phone"):
            issues.append("Invalid phone number format")
        elif field_name.lower().endswith("amount"):
            issues.append("Invalid amount format")
        
        return issues
    
    def _calculate_overall_score(self, system_metrics: List[SystemQualityMetrics]) -> float:
        """Calculate overall quality score across all systems"""
        if not system_metrics:
            return 0.0
        
        total_records = sum(sm.total_records for sm in system_metrics)
        if total_records == 0:
            return 0.0
        
        weighted_score = sum(
            sm.overall_quality_score * sm.total_records 
            for sm in system_metrics
        )
        
        return weighted_score / total_records
    
    def _calculate_dimension_scores(
        self,
        system_metrics: List[SystemQualityMetrics]
    ) -> Dict[DataQualityDimension, float]:
        """Calculate scores for each quality dimension"""
        dimension_scores = {}
        
        for dimension in DataQualityDimension:
            total_records = 0
            weighted_score = 0.0
            
            for system_metric in system_metrics:
                for entity_metric in system_metric.entity_metrics:
                    if dimension in entity_metric.dimension_scores:
                        weighted_score += (
                            entity_metric.dimension_scores[dimension] * 
                            entity_metric.total_records
                        )
                        total_records += entity_metric.total_records
            
            dimension_scores[dimension] = (
                weighted_score / total_records if total_records > 0 else 0.0
            )
        
        return dimension_scores
    
    async def _calculate_entity_dimension_scores(
        self,
        field_metrics: List[FieldQualityMetrics],
        sample_data: List[Dict],
        entity_type: str
    ) -> Dict[DataQualityDimension, float]:
        """Calculate dimension scores for an entity"""
        scores = {}
        
        if not field_metrics:
            return scores
        
        # Completeness: average completeness across all fields
        completeness_scores = [fm.completeness_score for fm in field_metrics]
        scores[DataQualityDimension.COMPLETENESS] = sum(completeness_scores) / len(completeness_scores)
        
        # Validity: average validity across all fields
        validity_scores = [fm.validity_score for fm in field_metrics]
        scores[DataQualityDimension.VALIDITY] = sum(validity_scores) / len(validity_scores)
        
        # Uniqueness: based on duplicate detection
        uniqueness_scores = [fm.uniqueness_score for fm in field_metrics]
        scores[DataQualityDimension.UNIQUENESS] = sum(uniqueness_scores) / len(uniqueness_scores)
        
        # Consistency: check for data consistency across records
        scores[DataQualityDimension.CONSISTENCY] = await self._calculate_consistency_score(
            sample_data, entity_type
        )
        
        # Timeliness: check for outdated records
        scores[DataQualityDimension.TIMELINESS] = await self._calculate_timeliness_score(
            sample_data, entity_type
        )
        
        # Integrity: check referential integrity
        scores[DataQualityDimension.INTEGRITY] = await self._calculate_integrity_score(
            sample_data, entity_type
        )
        
        # Accuracy: overall accuracy assessment
        scores[DataQualityDimension.ACCURACY] = (
            scores[DataQualityDimension.VALIDITY] + 
            scores[DataQualityDimension.CONSISTENCY]
        ) / 2
        
        return scores
    
    async def _calculate_consistency_score(self, sample_data: List[Dict], entity_type: str) -> float:
        """Calculate consistency score for entity data"""
        if not sample_data:
            return 100.0
        
        consistency_issues = 0
        total_checks = 0
        
        try:
            # Check for consistent formats in similar fields
            for record in sample_data[:100]:  # Sample for performance
                # Check date format consistency
                date_fields = [k for k in record.keys() if 'date' in k.lower()]
                for field in date_fields:
                    if record.get(field):
                        total_checks += 1
                        # Simple date format check
                        try:
                            datetime.fromisoformat(str(record[field]))
                        except ValueError:
                            consistency_issues += 1
                
                # Check amount format consistency
                amount_fields = [k for k in record.keys() if 'amount' in k.lower() or 'price' in k.lower()]
                for field in amount_fields:
                    if record.get(field):
                        total_checks += 1
                        try:
                            Decimal(str(record[field]))
                        except (ValueError, TypeError):
                            consistency_issues += 1
            
            if total_checks == 0:
                return 100.0
            
            return max(0, (total_checks - consistency_issues) / total_checks * 100)
            
        except Exception as e:
            logger.error(f"Failed to calculate consistency score: {e}")
            return 0.0
    
    async def _calculate_timeliness_score(self, sample_data: List[Dict], entity_type: str) -> float:
        """Calculate timeliness score for entity data"""
        if not sample_data:
            return 100.0
        
        try:
            outdated_records = 0
            current_time = datetime.now()
            
            for record in sample_data:
                # Check creation/update timestamps
                created_at = record.get('created_at') or record.get('creation_date')
                updated_at = record.get('updated_at') or record.get('modification_date')
                
                timestamp = updated_at or created_at
                if timestamp:
                    try:
                        record_time = datetime.fromisoformat(str(timestamp))
                        # Consider records older than 30 days as potentially outdated
                        if (current_time - record_time).days > 30:
                            outdated_records += 1
                    except ValueError:
                        # Invalid timestamp format
                        outdated_records += 1
            
            return max(0, (len(sample_data) - outdated_records) / len(sample_data) * 100)
            
        except Exception as e:
            logger.error(f"Failed to calculate timeliness score: {e}")
            return 0.0
    
    async def _calculate_integrity_score(self, sample_data: List[Dict], entity_type: str) -> float:
        """Calculate referential integrity score"""
        if not sample_data:
            return 100.0
        
        try:
            integrity_violations = 0
            total_references = 0
            
            for record in sample_data:
                # Check for orphaned references (simplified)
                customer_id = record.get('customer_id')
                if customer_id:
                    total_references += 1
                    # In a real implementation, you would check if customer exists
                    # For now, assume 5% have integrity issues
                    if hash(str(customer_id)) % 20 == 0:
                        integrity_violations += 1
            
            if total_references == 0:
                return 100.0
            
            return max(0, (total_references - integrity_violations) / total_references * 100)
            
        except Exception as e:
            logger.error(f"Failed to calculate integrity score: {e}")
            return 0.0
    
    def _is_record_valid(self, record: Dict, entity_type: str) -> bool:
        """Check if a record is valid based on quality rules"""
        try:
            rules = self.quality_rules.get(entity_type, [])
            
            for rule in rules:
                if not rule.enabled or rule.severity == "info":
                    continue
                
                field_value = record.get(rule.field_name)
                
                if rule.rule_type == "required" and (field_value is None or str(field_value).strip() == ""):
                    return False
                
                if field_value and rule.rule_type == "format":
                    if not self._validate_format(field_value, rule.validation_expression):
                        return False
            
            return True
            
        except Exception:
            return False
    
    async def _count_duplicates(self, sample_data: List[Dict], entity_type: str) -> int:
        """Count duplicate records in the sample"""
        try:
            # Create signatures for records (simplified)
            signatures = []
            
            for record in sample_data:
                # Use key fields to create signature
                key_fields = self._get_key_fields(entity_type)
                signature = tuple(str(record.get(field, "")) for field in key_fields)
                signatures.append(signature)
            
            # Count duplicates
            signature_counter = Counter(signatures)
            duplicates = sum(count - 1 for count in signature_counter.values() if count > 1)
            
            return duplicates
            
        except Exception as e:
            logger.error(f"Failed to count duplicates: {e}")
            return 0
    
    def _get_key_fields(self, entity_type: str) -> List[str]:
        """Get key fields for duplicate detection"""
        key_field_mapping = {
            "invoice": ["invoice_number", "customer_id", "invoice_date"],
            "customer": ["customer_id", "email", "phone"],
            "product": ["product_code", "name"],
            "payment": ["payment_id", "invoice_id", "amount"]
        }
        
        return key_field_mapping.get(entity_type, ["id"])
    
    async def _identify_top_issues(
        self,
        systems: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> List[DataIssue]:
        """Identify top data quality issues"""
        all_issues = []
        
        for system in systems:
            system_issues = await self._get_system_issues(system, start_date, end_date)
            all_issues.extend(system_issues)
        
        # Sort by severity and frequency
        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        sorted_issues = sorted(
            all_issues,
            key=lambda x: (severity_order.get(x.severity, 4), x.detected_at),
            reverse=True
        )
        
        return sorted_issues[:self.config.max_issues_per_report]
    
    async def _generate_quality_trends(self, systems: List[str]) -> Dict[str, List[Tuple[datetime, float]]]:
        """Generate quality trend data"""
        trends = {}
        
        try:
            # Generate trend data for the last 30 days
            end_date = datetime.now()
            
            for i in range(30):
                date = end_date - timedelta(days=i)
                
                # Simulate quality scores for trend analysis
                for system in systems:
                    if system not in trends:
                        trends[system] = []
                    
                    # Simulate some variation in quality scores
                    base_score = 85.0
                    variation = (hash(f"{system}_{date.strftime('%Y%m%d')}") % 20) - 10
                    score = max(60.0, min(100.0, base_score + variation))
                    
                    trends[system].append((date, score))
            
            # Sort by date
            for system in trends:
                trends[system].sort(key=lambda x: x[0])
            
        except Exception as e:
            logger.error(f"Failed to generate quality trends: {e}")
        
        return trends
    
    def _generate_recommendations(self, report: DataQualityReport) -> List[str]:
        """Generate recommendations based on report findings"""
        recommendations = []
        
        try:
            # Overall score recommendations
            if report.overall_quality_score < 70:
                recommendations.append("Overall data quality is below acceptable threshold. Immediate action required.")
            elif report.overall_quality_score < 85:
                recommendations.append("Data quality needs improvement. Review validation rules and data entry processes.")
            
            # Dimension-specific recommendations
            for dimension, score in report.dimension_scores.items():
                if score < 80:
                    if dimension == DataQualityDimension.COMPLETENESS:
                        recommendations.append("Improve data completeness by making required fields mandatory in source systems.")
                    elif dimension == DataQualityDimension.VALIDITY:
                        recommendations.append("Implement stricter validation rules to improve data validity.")
                    elif dimension == DataQualityDimension.CONSISTENCY:
                        recommendations.append("Standardize data formats across all integrated systems.")
                    elif dimension == DataQualityDimension.UNIQUENESS:
                        recommendations.append("Implement duplicate detection and prevention mechanisms.")
                    elif dimension == DataQualityDimension.TIMELINESS:
                        recommendations.append("Increase sync frequency to improve data timeliness.")
                    elif dimension == DataQualityDimension.INTEGRITY:
                        recommendations.append("Strengthen referential integrity constraints.")
            
            # System-specific recommendations
            for system_metric in report.system_metrics:
                if system_metric.overall_quality_score < 75:
                    recommendations.append(f"Focus on improving data quality for {system_metric.system_name} system.")
            
            # Issue-based recommendations
            critical_issues = [issue for issue in report.top_issues if issue.severity == "critical"]
            if len(critical_issues) > 10:
                recommendations.append("High number of critical issues detected. Immediate remediation required.")
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
        
        return recommendations
    
    def _calculate_summary_stats(self, report: DataQualityReport) -> Dict[str, Any]:
        """Calculate summary statistics for the report"""
        try:
            total_records = sum(sm.total_records for sm in report.system_metrics)
            total_valid_records = sum(sm.valid_records for sm in report.system_metrics)
            total_issues = sum(sm.total_issues for sm in report.system_metrics)
            
            critical_issues = sum(1 for issue in report.top_issues if issue.severity == "critical")
            warning_issues = sum(1 for issue in report.top_issues if issue.severity == "warning")
            
            return {
                "total_records_analyzed": total_records,
                "total_valid_records": total_valid_records,
                "total_invalid_records": total_records - total_valid_records,
                "validity_percentage": (total_valid_records / total_records * 100) if total_records > 0 else 0,
                "total_quality_issues": total_issues,
                "critical_issues": critical_issues,
                "warning_issues": warning_issues,
                "systems_analyzed": len(report.system_metrics),
                "quality_score_category": self._get_quality_category(report.overall_quality_score),
                "trend_direction": self._calculate_trend_direction(report.quality_trends),
                "data_volume_gb": total_records * 0.001,  # Rough estimate
            }
        except Exception as e:
            logger.error(f"Failed to calculate summary stats: {e}")
            return {}
    
    def _get_quality_category(self, score: float) -> str:
        """Get quality category based on score"""
        if score >= 95:
            return QualityScore.EXCELLENT.value
        elif score >= 85:
            return QualityScore.GOOD.value
        elif score >= 70:
            return QualityScore.FAIR.value
        elif score >= 50:
            return QualityScore.POOR.value
        else:
            return QualityScore.CRITICAL.value
    
    def _calculate_trend_direction(self, trends: Dict[str, List[Tuple[datetime, float]]]) -> str:
        """Calculate overall trend direction"""
        try:
            if not trends:
                return "stable"
            
            overall_trends = []
            for system_trends in trends.values():
                if len(system_trends) >= 2:
                    recent_scores = [score for _, score in system_trends[-7:]]  # Last 7 data points
                    if len(recent_scores) >= 2:
                        trend = (recent_scores[-1] - recent_scores[0]) / len(recent_scores)
                        overall_trends.append(trend)
            
            if not overall_trends:
                return "stable"
            
            avg_trend = sum(overall_trends) / len(overall_trends)
            
            if avg_trend > 2:
                return "improving"
            elif avg_trend < -2:
                return "declining"
            else:
                return "stable"
                
        except Exception:
            return "unknown"
    
    # Placeholder methods for data access (would be implemented based on actual data sources)
    
    def _get_available_systems(self) -> List[str]:
        """Get list of available systems"""
        return ["odoo", "sap", "quickbooks"]
    
    def _get_system_type(self, system_name: str) -> str:
        """Get system type"""
        return system_name.upper()
    
    async def _get_entity_types(self, system_name: str) -> List[str]:
        """Get entity types for a system"""
        return ["invoice", "customer", "product", "payment"]
    
    async def _get_sample_data(
        self,
        system_name: str,
        entity_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """Get sample data for analysis"""
        # This would query the actual data source
        # For now, return mock data
        return [
            {
                "id": f"{i}",
                "invoice_number": f"INV-{i:04d}",
                "customer_id": f"CUST-{i % 100}",
                "amount": 100.0 + i,
                "invoice_date": datetime.now() - timedelta(days=i % 30),
                "status": "posted" if i % 10 != 0 else "",  # Simulate missing data
                "created_at": datetime.now() - timedelta(days=i % 60)
            }
            for i in range(min(self.config.sample_size_for_analysis, 1000))
        ]
    
    def _get_field_definitions(self, entity_type: str) -> List[str]:
        """Get field definitions for an entity type"""
        field_definitions = {
            "invoice": ["id", "invoice_number", "customer_id", "amount", "invoice_date", "status", "created_at"],
            "customer": ["id", "name", "email", "phone", "address", "created_at"],
            "product": ["id", "code", "name", "price", "category", "created_at"],
            "payment": ["id", "invoice_id", "amount", "payment_date", "method", "created_at"]
        }
        return field_definitions.get(entity_type, [])
    
    async def _get_entity_issues(
        self,
        system_name: str,
        entity_type: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[DataIssue]:
        """Get quality issues for an entity"""
        # This would query actual issue tracking
        # For now, return mock issues
        return [
            DataIssue(
                issue_id=f"issue_{i}",
                issue_type=DataIssueType.MISSING_REQUIRED_FIELD,
                severity="warning",
                dimension=DataQualityDimension.COMPLETENESS,
                entity_type=entity_type,
                entity_id=f"record_{i}",
                field_name="customer_id",
                description="Missing customer ID",
                source_system=system_name
            )
            for i in range(5)  # Mock 5 issues
        ]
    
    async def _get_system_issues(
        self,
        system_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[DataIssue]:
        """Get all issues for a system"""
        issues = []
        entity_types = await self._get_entity_types(system_name)
        
        for entity_type in entity_types:
            entity_issues = await self._get_entity_issues(system_name, entity_type, start_date, end_date)
            issues.extend(entity_issues)
        
        return issues
    
    async def _generate_system_trends(self, system_name: str) -> Dict[str, List[float]]:
        """Generate trend data for a system"""
        # Mock trend data
        return {
            "quality_score": [85.2, 86.1, 84.8, 87.3, 88.1, 86.9, 87.7],
            "completeness": [92.1, 93.2, 91.8, 94.1, 94.8, 93.7, 94.2],
            "validity": [88.7, 89.3, 87.9, 90.1, 91.2, 89.8, 90.5]
        }
    
    async def _load_quality_rules(self) -> None:
        """Load quality rules from configuration"""
        try:
            if self.config.quality_rules_file:
                rules_file = Path(self.config.quality_rules_file)
                if rules_file.exists():
                    with open(rules_file, 'r') as f:
                        rules_data = json.load(f)
                        self._parse_quality_rules(rules_data)
            else:
                # Load default rules
                self._load_default_rules()
                
        except Exception as e:
            logger.error(f"Failed to load quality rules: {e}")
            self._load_default_rules()
    
    def _parse_quality_rules(self, rules_data: Dict) -> None:
        """Parse quality rules from configuration data"""
        for entity_type, rules_list in rules_data.items():
            self.quality_rules[entity_type] = []
            for rule_data in rules_list:
                rule = DataQualityRule(**rule_data)
                self.quality_rules[entity_type].append(rule)
    
    def _load_default_rules(self) -> None:
        """Load default quality rules"""
        default_rules = {
            "invoice": [
                DataQualityRule(
                    rule_id="inv_001",
                    rule_name="Invoice Number Required",
                    dimension=DataQualityDimension.COMPLETENESS,
                    field_name="invoice_number",
                    rule_type="required",
                    validation_expression="",
                    error_message="Invoice number is required"
                ),
                DataQualityRule(
                    rule_id="inv_002",
                    rule_name="Amount Format",
                    dimension=DataQualityDimension.VALIDITY,
                    field_name="amount",
                    rule_type="format",
                    validation_expression="numeric",
                    error_message="Amount must be numeric"
                )
            ]
        }
        self.quality_rules.update(default_rules)
    
    async def _export_quality_report(self, report: DataQualityReport) -> None:
        """Export quality report to file"""
        if not self.output_path:
            return
        
        try:
            filename = f"{report.report_id}.json"
            filepath = self.output_path / filename
            
            report_dict = self._quality_report_to_dict(report)
            with open(filepath, 'w') as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            logger.info(f"Exported quality report to {filepath}")
            
        except Exception as e:
            logger.error(f"Failed to export quality report: {e}")
    
    def _quality_report_to_dict(self, report: DataQualityReport) -> Dict[str, Any]:
        """Convert quality report to dictionary"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "overall_quality_score": report.overall_quality_score,
            "dimension_scores": {d.value: s for d, s in report.dimension_scores.items()},
            "system_metrics": [
                {
                    "system_name": sm.system_name,
                    "system_type": sm.system_type,
                    "overall_quality_score": sm.overall_quality_score,
                    "total_records": sm.total_records,
                    "valid_records": sm.valid_records,
                    "total_issues": sm.total_issues
                }
                for sm in report.system_metrics
            ],
            "top_issues": [
                {
                    "issue_id": issue.issue_id,
                    "issue_type": issue.issue_type.value,
                    "severity": issue.severity,
                    "entity_type": issue.entity_type,
                    "field_name": issue.field_name,
                    "description": issue.description,
                    "source_system": issue.source_system
                }
                for issue in report.top_issues
            ],
            "recommendations": report.recommendations,
            "summary_stats": report.summary_stats
        }
    
    def get_cached_report(self, report_id: str) -> Optional[DataQualityReport]:
        """Get a cached quality report"""
        return self.quality_cache.get(report_id)
    
    def list_cached_reports(self) -> List[str]:
        """List all cached report IDs"""
        return list(self.quality_cache.keys())


# Factory function for creating data quality service
def create_data_quality_service(config: Optional[QualityConfig] = None) -> DataQualityService:
    """Factory function to create a data quality service"""
    if config is None:
        config = QualityConfig()
    
    return DataQualityService(config)