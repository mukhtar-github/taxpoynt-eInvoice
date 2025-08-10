"""
Data Completeness Verification Service for APP Role

This service verifies data completeness including:
- Required field presence validation
- Data relationship completeness
- Cross-reference validation
- Contextual completeness checks
- Business logic completeness
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompletenessLevel(Enum):
    """Completeness check levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    STRICT = "strict"


class CompletionStatus(Enum):
    """Completion status for fields"""
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    MISSING = "missing"
    INVALID = "invalid"
    CONDITIONAL = "conditional"


class CompletionSeverity(Enum):
    """Completion check severity"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class CompletenessRule:
    """Completeness validation rule"""
    rule_id: str
    field_path: str
    rule_type: str
    severity: CompletionSeverity
    description: str
    condition: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    business_rule: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletenessResult:
    """Individual completeness check result"""
    rule_id: str
    field_path: str
    status: CompletionStatus
    severity: CompletionSeverity
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    suggestion: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletenessReport:
    """Data completeness verification report"""
    document_id: str
    document_type: str
    completeness_level: CompletenessLevel
    validation_timestamp: datetime
    overall_completion: float
    is_complete: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[CompletenessResult] = field(default_factory=list)
    missing_fields: List[CompletenessResult] = field(default_factory=list)
    incomplete_fields: List[CompletenessResult] = field(default_factory=list)
    conditional_fields: List[CompletenessResult] = field(default_factory=list)
    category_completion: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CompletenessChecker:
    """
    Data completeness verification service for APP role
    
    Handles:
    - Required field presence validation
    - Data relationship completeness
    - Cross-reference validation
    - Contextual completeness checks
    - Business logic completeness
    """
    
    def __init__(self, completeness_level: CompletenessLevel = CompletenessLevel.STANDARD):
        self.completeness_level = completeness_level
        
        # Load completeness rules
        self.rules = self._load_completeness_rules()
        
        # Field categories
        self.field_categories = {
            'document_metadata': ['document_id', 'document_type', 'creation_date'],
            'invoice_details': ['invoice_number', 'invoice_date', 'due_date', 'currency'],
            'supplier_info': ['supplier.name', 'supplier.tin', 'supplier.address'],
            'customer_info': ['customer.name', 'customer.address'],
            'financial_data': ['subtotal', 'tax_amount', 'total_amount'],
            'item_details': ['items', 'items[].description', 'items[].quantity', 'items[].unit_price'],
            'tax_information': ['vat.rate', 'vat.amount'],
            'payment_details': ['payment_terms', 'payment_method'],
            'additional_info': ['notes', 'references']
        }
        
        # Business logic dependencies
        self.dependencies = {
            'due_date': ['invoice_date'],
            'total_amount': ['subtotal', 'tax_amount'],
            'vat.amount': ['subtotal', 'vat.rate'],
            'wht.amount': ['subtotal', 'wht.rate'],
            'customer.tin': ['total_amount'],  # Required for high-value invoices
            'payment_method': ['payment_terms']
        }
        
        # Contextual completeness rules
        self.contextual_rules = {
            'high_value_invoice': {
                'condition': 'total_amount > 1000000',
                'required_fields': ['customer.tin', 'supplier.vat_number', 'approval_reference']
            },
            'export_invoice': {
                'condition': 'customer.address.country != "NG"',
                'required_fields': ['export_permit', 'customs_declaration']
            },
            'vat_applicable': {
                'condition': 'vat.rate > 0',
                'required_fields': ['supplier.vat_number', 'vat.amount']
            },
            'wht_applicable': {
                'condition': 'wht.rate > 0',
                'required_fields': ['wht.type', 'wht.amount']
            }
        }
        
        # Metrics
        self.metrics = {
            'total_checks': 0,
            'complete_documents': 0,
            'incomplete_documents': 0,
            'average_completion': 0.0,
            'common_missing_fields': {},
            'category_performance': {}
        }
    
    def _load_completeness_rules(self) -> Dict[str, CompletenessRule]:
        """Load completeness validation rules"""
        rules = {}
        
        # Basic required fields
        basic_rules = [
            ('DOC_ID_001', 'document_id', 'required', CompletionSeverity.CRITICAL, 'Document ID is required'),
            ('DOC_TYPE_001', 'document_type', 'required', CompletionSeverity.CRITICAL, 'Document type is required'),
            ('INV_NUM_001', 'invoice_number', 'required', CompletionSeverity.CRITICAL, 'Invoice number is required'),
            ('INV_DATE_001', 'invoice_date', 'required', CompletionSeverity.CRITICAL, 'Invoice date is required'),
            ('CURRENCY_001', 'currency', 'required', CompletionSeverity.CRITICAL, 'Currency is required'),
            ('SUPPLIER_001', 'supplier.name', 'required', CompletionSeverity.CRITICAL, 'Supplier name is required'),
            ('SUPPLIER_002', 'supplier.tin', 'required', CompletionSeverity.CRITICAL, 'Supplier TIN is required'),
            ('SUPPLIER_003', 'supplier.address', 'required', CompletionSeverity.CRITICAL, 'Supplier address is required'),
            ('CUSTOMER_001', 'customer.name', 'required', CompletionSeverity.CRITICAL, 'Customer name is required'),
            ('CUSTOMER_002', 'customer.address', 'required', CompletionSeverity.CRITICAL, 'Customer address is required'),
            ('ITEMS_001', 'items', 'required', CompletionSeverity.CRITICAL, 'Items are required'),
            ('TOTAL_001', 'total_amount', 'required', CompletionSeverity.CRITICAL, 'Total amount is required')
        ]
        
        for rule_id, field_path, rule_type, severity, description in basic_rules:
            rules[rule_id] = CompletenessRule(
                rule_id=rule_id,
                field_path=field_path,
                rule_type=rule_type,
                severity=severity,
                description=description
            )
        
        # Standard level additional rules
        if self.completeness_level in [CompletenessLevel.STANDARD, CompletenessLevel.COMPREHENSIVE, CompletenessLevel.STRICT]:
            standard_rules = [
                ('DUE_DATE_001', 'due_date', 'conditional', CompletionSeverity.WARNING, 'Due date recommended for payment tracking'),
                ('SUBTOTAL_001', 'subtotal', 'required', CompletionSeverity.ERROR, 'Subtotal is required'),
                ('TAX_AMT_001', 'tax_amount', 'conditional', CompletionSeverity.WARNING, 'Tax amount recommended'),
                ('SUPPLIER_004', 'supplier.phone', 'recommended', CompletionSeverity.WARNING, 'Supplier phone recommended'),
                ('SUPPLIER_005', 'supplier.email', 'recommended', CompletionSeverity.WARNING, 'Supplier email recommended'),
                ('CUSTOMER_003', 'customer.phone', 'recommended', CompletionSeverity.WARNING, 'Customer phone recommended'),
                ('CUSTOMER_004', 'customer.email', 'recommended', CompletionSeverity.WARNING, 'Customer email recommended'),
                ('PAYMENT_001', 'payment_terms', 'recommended', CompletionSeverity.WARNING, 'Payment terms recommended')
            ]
            
            for rule_id, field_path, rule_type, severity, description in standard_rules:
                rules[rule_id] = CompletenessRule(
                    rule_id=rule_id,
                    field_path=field_path,
                    rule_type=rule_type,
                    severity=severity,
                    description=description
                )
        
        # Comprehensive level additional rules
        if self.completeness_level in [CompletenessLevel.COMPREHENSIVE, CompletenessLevel.STRICT]:
            comprehensive_rules = [
                ('VAT_001', 'vat.rate', 'conditional', CompletionSeverity.WARNING, 'VAT rate required for taxable items'),
                ('VAT_002', 'vat.amount', 'conditional', CompletionSeverity.WARNING, 'VAT amount required when VAT rate > 0'),
                ('ITEM_UNIT_001', 'items[].unit', 'recommended', CompletionSeverity.WARNING, 'Item unit recommended'),
                ('NOTES_001', 'notes', 'recommended', CompletionSeverity.INFO, 'Notes recommended for clarity'),
                ('REFERENCE_001', 'reference', 'recommended', CompletionSeverity.INFO, 'Reference recommended for tracking')
            ]
            
            for rule_id, field_path, rule_type, severity, description in comprehensive_rules:
                rules[rule_id] = CompletenessRule(
                    rule_id=rule_id,
                    field_path=field_path,
                    rule_type=rule_type,
                    severity=severity,
                    description=description
                )
        
        # Strict level additional rules
        if self.completeness_level == CompletenessLevel.STRICT:
            strict_rules = [
                ('SUPPLIER_006', 'supplier.vat_number', 'conditional', CompletionSeverity.ERROR, 'Supplier VAT number required for VAT-registered businesses'),
                ('CUSTOMER_005', 'customer.tin', 'conditional', CompletionSeverity.ERROR, 'Customer TIN required for high-value transactions'),
                ('APPROVAL_001', 'approval_reference', 'conditional', CompletionSeverity.ERROR, 'Approval reference required for high-value invoices'),
                ('WORKFLOW_001', 'workflow_status', 'required', CompletionSeverity.ERROR, 'Workflow status required'),
                ('CREATED_BY_001', 'created_by', 'required', CompletionSeverity.ERROR, 'Created by information required')
            ]
            
            for rule_id, field_path, rule_type, severity, description in strict_rules:
                rules[rule_id] = CompletenessRule(
                    rule_id=rule_id,
                    field_path=field_path,
                    rule_type=rule_type,
                    severity=severity,
                    description=description
                )
        
        return rules
    
    async def check_completeness(self, document: Dict[str, Any]) -> CompletenessReport:
        """
        Check data completeness of document
        
        Args:
            document: Document data to check
            
        Returns:
            CompletenessReport with completeness results
        """
        # Initialize report
        report = CompletenessReport(
            document_id=document.get('document_id', 'unknown'),
            document_type=document.get('document_type', 'unknown'),
            completeness_level=self.completeness_level,
            validation_timestamp=datetime.utcnow(),
            overall_completion=0.0,
            is_complete=False,
            total_checks=0,
            passed_checks=0,
            failed_checks=0
        )
        
        try:
            # Run completeness checks
            await self._run_completeness_checks(document, report)
            
            # Check contextual completeness
            await self._check_contextual_completeness(document, report)
            
            # Check business logic completeness
            await self._check_business_logic_completeness(document, report)
            
            # Check data relationships
            await self._check_data_relationships(document, report)
            
            # Calculate completion scores
            await self._calculate_completion_scores(report)
            
            # Generate recommendations
            await self._generate_recommendations(report)
            
            # Update metrics
            self._update_metrics(report)
            
            logger.info(f"Completeness check completed for {report.document_id}: "
                       f"{report.overall_completion:.1f}% complete "
                       f"({report.passed_checks}/{report.total_checks} checks passed)")
            
        except Exception as e:
            report.results.append(CompletenessResult(
                rule_id='SYS_ERROR_001',
                field_path='system',
                status=CompletionStatus.INVALID,
                severity=CompletionSeverity.CRITICAL,
                message=f'Completeness check system error: {str(e)}'
            ))
            
            logger.error(f"Completeness check error for {report.document_id}: {e}")
        
        return report
    
    async def _run_completeness_checks(self, document: Dict[str, Any], report: CompletenessReport):
        """Run basic completeness checks"""
        for rule in self.rules.values():
            await self._check_field_completeness(document, rule, report)
    
    async def _check_field_completeness(self, document: Dict[str, Any], rule: CompletenessRule, report: CompletenessReport):
        """Check completeness of individual field"""
        field_path = rule.field_path
        
        # Handle array notation
        if '[' in field_path and ']' in field_path:
            await self._check_array_field_completeness(document, rule, report)
            return
        
        # Get field value
        field_value = self._get_nested_value(document, field_path)
        
        # Check field presence and validity
        status = self._determine_completion_status(field_value, rule)
        
        # Create result
        result = CompletenessResult(
            rule_id=rule.rule_id,
            field_path=field_path,
            status=status,
            severity=rule.severity,
            message=self._get_completion_message(field_path, status, rule),
            actual_value=str(field_value) if field_value is not None else None,
            dependencies=rule.depends_on,
            alternatives=rule.alternatives
        )
        
        # Add suggestions
        if status in [CompletionStatus.MISSING, CompletionStatus.INCOMPLETE]:
            result.suggestion = self._get_completion_suggestion(field_path, status, rule)
        
        report.results.append(result)
        report.total_checks += 1
        
        # Update counters
        if status == CompletionStatus.COMPLETE:
            report.passed_checks += 1
        else:
            report.failed_checks += 1
            
            # Categorize incomplete fields
            if status == CompletionStatus.MISSING:
                report.missing_fields.append(result)
            elif status == CompletionStatus.INCOMPLETE:
                report.incomplete_fields.append(result)
            elif status == CompletionStatus.CONDITIONAL:
                report.conditional_fields.append(result)
    
    async def _check_array_field_completeness(self, document: Dict[str, Any], rule: CompletenessRule, report: CompletenessReport):
        """Check completeness of array fields"""
        field_path = rule.field_path
        
        # Parse array notation (e.g., "items[].description")
        if '[].' in field_path:
            array_path, item_field = field_path.split('[].')
            array_value = self._get_nested_value(document, array_path)
            
            if not isinstance(array_value, list):
                result = CompletenessResult(
                    rule_id=rule.rule_id,
                    field_path=field_path,
                    status=CompletionStatus.MISSING,
                    severity=rule.severity,
                    message=f'Array field {array_path} is missing or not an array',
                    suggestion=f'Provide {array_path} as an array'
                )
                report.results.append(result)
                report.total_checks += 1
                report.failed_checks += 1
                return
            
            # Check each item in array
            for i, item in enumerate(array_value):
                item_field_path = f"{array_path}[{i}].{item_field}"
                item_value = self._get_nested_value(item, item_field)
                
                status = self._determine_completion_status(item_value, rule)
                
                result = CompletenessResult(
                    rule_id=f"{rule.rule_id}_{i}",
                    field_path=item_field_path,
                    status=status,
                    severity=rule.severity,
                    message=self._get_completion_message(item_field_path, status, rule),
                    actual_value=str(item_value) if item_value is not None else None
                )
                
                if status in [CompletionStatus.MISSING, CompletionStatus.INCOMPLETE]:
                    result.suggestion = self._get_completion_suggestion(item_field_path, status, rule)
                
                report.results.append(result)
                report.total_checks += 1
                
                if status == CompletionStatus.COMPLETE:
                    report.passed_checks += 1
                else:
                    report.failed_checks += 1
                    
                    if status == CompletionStatus.MISSING:
                        report.missing_fields.append(result)
                    elif status == CompletionStatus.INCOMPLETE:
                        report.incomplete_fields.append(result)
    
    async def _check_contextual_completeness(self, document: Dict[str, Any], report: CompletenessReport):
        """Check contextual completeness based on business rules"""
        for context_name, context_rule in self.contextual_rules.items():
            condition = context_rule['condition']
            required_fields = context_rule['required_fields']
            
            # Evaluate condition
            if self._evaluate_condition(document, condition):
                # Check required fields for this context
                for field_path in required_fields:
                    field_value = self._get_nested_value(document, field_path)
                    status = self._determine_completion_status(field_value, None)
                    
                    if status != CompletionStatus.COMPLETE:
                        result = CompletenessResult(
                            rule_id=f"CONTEXT_{context_name.upper()}_{field_path.replace('.', '_').upper()}",
                            field_path=field_path,
                            status=status,
                            severity=CompletionSeverity.ERROR,
                            message=f'Field {field_path} is required for {context_name}',
                            suggestion=f'Provide {field_path} as required by {context_name} context'
                        )
                        
                        report.results.append(result)
                        report.total_checks += 1
                        report.failed_checks += 1
                        
                        if status == CompletionStatus.MISSING:
                            report.missing_fields.append(result)
    
    async def _check_business_logic_completeness(self, document: Dict[str, Any], report: CompletenessReport):
        """Check business logic completeness"""
        # Check amount calculations
        await self._check_amount_calculation_completeness(document, report)
        
        # Check tax information completeness
        await self._check_tax_information_completeness(document, report)
        
        # Check date consistency completeness
        await self._check_date_completeness(document, report)
    
    async def _check_amount_calculation_completeness(self, document: Dict[str, Any], report: CompletenessReport):
        """Check completeness of amount calculations"""
        subtotal = self._get_nested_value(document, 'subtotal')
        tax_amount = self._get_nested_value(document, 'tax_amount')
        total_amount = self._get_nested_value(document, 'total_amount')
        
        # Check if all required amounts are present
        if total_amount is not None and subtotal is None:
            result = CompletenessResult(
                rule_id='CALC_001',
                field_path='subtotal',
                status=CompletionStatus.MISSING,
                severity=CompletionSeverity.ERROR,
                message='Subtotal is required when total amount is provided',
                suggestion='Provide subtotal for amount calculation verification'
            )
            report.results.append(result)
            report.total_checks += 1
            report.failed_checks += 1
            report.missing_fields.append(result)
        
        # Check items total consistency
        items = self._get_nested_value(document, 'items')
        if isinstance(items, list) and items:
            items_missing_amounts = []
            for i, item in enumerate(items):
                if not all(key in item for key in ['quantity', 'unit_price', 'total_price']):
                    items_missing_amounts.append(f"items[{i}]")
            
            if items_missing_amounts:
                result = CompletenessResult(
                    rule_id='CALC_002',
                    field_path='items',
                    status=CompletionStatus.INCOMPLETE,
                    severity=CompletionSeverity.ERROR,
                    message=f'Items missing amount fields: {", ".join(items_missing_amounts)}',
                    suggestion='Provide quantity, unit_price, and total_price for all items'
                )
                report.results.append(result)
                report.total_checks += 1
                report.failed_checks += 1
                report.incomplete_fields.append(result)
    
    async def _check_tax_information_completeness(self, document: Dict[str, Any], report: CompletenessReport):
        """Check completeness of tax information"""
        # Check VAT completeness
        vat_info = self._get_nested_value(document, 'vat')
        if isinstance(vat_info, dict):
            vat_rate = vat_info.get('rate')
            vat_amount = vat_info.get('amount')
            
            if vat_rate is not None and vat_rate > 0:
                if vat_amount is None:
                    result = CompletenessResult(
                        rule_id='TAX_001',
                        field_path='vat.amount',
                        status=CompletionStatus.MISSING,
                        severity=CompletionSeverity.ERROR,
                        message='VAT amount is required when VAT rate is specified',
                        suggestion='Provide VAT amount calculation'
                    )
                    report.results.append(result)
                    report.total_checks += 1
                    report.failed_checks += 1
                    report.missing_fields.append(result)
                
                # Check supplier VAT number
                supplier_vat = self._get_nested_value(document, 'supplier.vat_number')
                if not supplier_vat:
                    result = CompletenessResult(
                        rule_id='TAX_002',
                        field_path='supplier.vat_number',
                        status=CompletionStatus.MISSING,
                        severity=CompletionSeverity.WARNING,
                        message='Supplier VAT number recommended when VAT is applicable',
                        suggestion='Provide supplier VAT number for VAT compliance'
                    )
                    report.results.append(result)
                    report.total_checks += 1
                    report.failed_checks += 1
                    report.missing_fields.append(result)
        
        # Check WHT completeness
        wht_info = self._get_nested_value(document, 'wht')
        if isinstance(wht_info, dict):
            wht_rate = wht_info.get('rate')
            wht_amount = wht_info.get('amount')
            wht_type = wht_info.get('type')
            
            if wht_rate is not None and wht_rate > 0:
                if wht_amount is None:
                    result = CompletenessResult(
                        rule_id='TAX_003',
                        field_path='wht.amount',
                        status=CompletionStatus.MISSING,
                        severity=CompletionSeverity.ERROR,
                        message='WHT amount is required when WHT rate is specified',
                        suggestion='Provide WHT amount calculation'
                    )
                    report.results.append(result)
                    report.total_checks += 1
                    report.failed_checks += 1
                    report.missing_fields.append(result)
                
                if not wht_type:
                    result = CompletenessResult(
                        rule_id='TAX_004',
                        field_path='wht.type',
                        status=CompletionStatus.MISSING,
                        severity=CompletionSeverity.ERROR,
                        message='WHT type is required when WHT rate is specified',
                        suggestion='Specify WHT type (e.g., professional_service, consultancy)'
                    )
                    report.results.append(result)
                    report.total_checks += 1
                    report.failed_checks += 1
                    report.missing_fields.append(result)
    
    async def _check_date_completeness(self, document: Dict[str, Any], report: CompletenessReport):
        """Check completeness of date information"""
        invoice_date = self._get_nested_value(document, 'invoice_date')
        due_date = self._get_nested_value(document, 'due_date')
        
        # Check due date presence for credit terms
        payment_terms = self._get_nested_value(document, 'payment_terms')
        if payment_terms and 'credit' in str(payment_terms).lower():
            if not due_date:
                result = CompletenessResult(
                    rule_id='DATE_001',
                    field_path='due_date',
                    status=CompletionStatus.MISSING,
                    severity=CompletionSeverity.WARNING,
                    message='Due date is recommended for credit payment terms',
                    suggestion='Provide due date for credit payment terms'
                )
                report.results.append(result)
                report.total_checks += 1
                report.failed_checks += 1
                report.missing_fields.append(result)
    
    async def _check_data_relationships(self, document: Dict[str, Any], report: CompletenessReport):
        """Check data relationships completeness"""
        for field_path, dependencies in self.dependencies.items():
            field_value = self._get_nested_value(document, field_path)
            
            if field_value is not None:
                # Check if dependencies are present
                missing_deps = []
                for dep_path in dependencies:
                    dep_value = self._get_nested_value(document, dep_path)
                    if dep_value is None:
                        missing_deps.append(dep_path)
                
                if missing_deps:
                    result = CompletenessResult(
                        rule_id=f"DEP_{field_path.replace('.', '_').upper()}",
                        field_path=field_path,
                        status=CompletionStatus.INCOMPLETE,
                        severity=CompletionSeverity.WARNING,
                        message=f'Field {field_path} depends on missing fields: {", ".join(missing_deps)}',
                        suggestion=f'Provide dependencies: {", ".join(missing_deps)}',
                        dependencies=missing_deps
                    )
                    report.results.append(result)
                    report.total_checks += 1
                    report.failed_checks += 1
                    report.incomplete_fields.append(result)
    
    async def _calculate_completion_scores(self, report: CompletenessReport):
        """Calculate completion scores"""
        # Overall completion percentage
        if report.total_checks > 0:
            report.overall_completion = (report.passed_checks / report.total_checks) * 100
        else:
            report.overall_completion = 0.0
        
        # Determine if document is complete
        critical_errors = len([r for r in report.results if r.severity == CompletionSeverity.CRITICAL and r.status != CompletionStatus.COMPLETE])
        error_count = len([r for r in report.results if r.severity == CompletionSeverity.ERROR and r.status != CompletionStatus.COMPLETE])
        
        report.is_complete = critical_errors == 0 and error_count == 0
        
        # Calculate category completion scores
        for category, fields in self.field_categories.items():
            category_checks = [r for r in report.results if any(r.field_path.startswith(field) for field in fields)]
            if category_checks:
                category_passed = len([r for r in category_checks if r.status == CompletionStatus.COMPLETE])
                category_total = len(category_checks)
                report.category_completion[category] = (category_passed / category_total) * 100
    
    async def _generate_recommendations(self, report: CompletenessReport):
        """Generate recommendations for improving completeness"""
        recommendations = []
        
        # Priority recommendations for missing critical fields
        critical_missing = [r for r in report.missing_fields if r.severity == CompletionSeverity.CRITICAL]
        if critical_missing:
            recommendations.append(f"Provide {len(critical_missing)} critical missing fields: {', '.join([r.field_path for r in critical_missing[:3]])}")
        
        # Error-level missing fields
        error_missing = [r for r in report.missing_fields if r.severity == CompletionSeverity.ERROR]
        if error_missing:
            recommendations.append(f"Provide {len(error_missing)} required fields: {', '.join([r.field_path for r in error_missing[:3]])}")
        
        # Category-specific recommendations
        for category, completion in report.category_completion.items():
            if completion < 80:
                recommendations.append(f"Improve {category} completeness (Currently {completion:.1f}%)")
        
        # Conditional field recommendations
        if report.conditional_fields:
            recommendations.append(f"Review {len(report.conditional_fields)} conditional fields based on business rules")
        
        # Relationship recommendations
        incomplete_relationships = [r for r in report.incomplete_fields if r.dependencies]
        if incomplete_relationships:
            recommendations.append(f"Complete {len(incomplete_relationships)} field relationships")
        
        report.recommendations = recommendations[:10]  # Limit to top 10
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get nested value from object using dot notation"""
        if not path:
            return obj
        
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _determine_completion_status(self, value: Any, rule: Optional[CompletenessRule]) -> CompletionStatus:
        """Determine completion status of a value"""
        if value is None:
            return CompletionStatus.MISSING
        
        if isinstance(value, str) and not value.strip():
            return CompletionStatus.MISSING
        
        if isinstance(value, list) and not value:
            return CompletionStatus.MISSING
        
        if isinstance(value, dict) and not value:
            return CompletionStatus.MISSING
        
        # Check for incomplete data
        if isinstance(value, str) and len(value.strip()) < 2:
            return CompletionStatus.INCOMPLETE
        
        # Check rule-specific conditions
        if rule and rule.rule_type == 'conditional':
            return CompletionStatus.CONDITIONAL
        
        return CompletionStatus.COMPLETE
    
    def _get_completion_message(self, field_path: str, status: CompletionStatus, rule: CompletenessRule) -> str:
        """Get completion message for field"""
        if status == CompletionStatus.MISSING:
            return f'Field {field_path} is missing'
        elif status == CompletionStatus.INCOMPLETE:
            return f'Field {field_path} is incomplete'
        elif status == CompletionStatus.CONDITIONAL:
            return f'Field {field_path} may be required based on conditions'
        elif status == CompletionStatus.INVALID:
            return f'Field {field_path} has invalid value'
        else:
            return f'Field {field_path} is complete'
    
    def _get_completion_suggestion(self, field_path: str, status: CompletionStatus, rule: CompletenessRule) -> str:
        """Get completion suggestion for field"""
        if status == CompletionStatus.MISSING:
            return f'Provide value for {field_path}'
        elif status == CompletionStatus.INCOMPLETE:
            return f'Complete the value for {field_path}'
        elif status == CompletionStatus.CONDITIONAL:
            return f'Review business rules for {field_path}'
        else:
            return f'Correct the value for {field_path}'
    
    def _evaluate_condition(self, document: Dict[str, Any], condition: str) -> bool:
        """Evaluate a condition string against document"""
        try:
            # Simple condition evaluation
            if 'total_amount > 1000000' in condition:
                total_amount = self._get_nested_value(document, 'total_amount')
                return total_amount is not None and float(total_amount) > 1000000
            
            if 'customer.address.country != "NG"' in condition:
                country = self._get_nested_value(document, 'customer.address.country')
                return country is not None and country != 'NG'
            
            if 'vat.rate > 0' in condition:
                vat_rate = self._get_nested_value(document, 'vat.rate')
                return vat_rate is not None and float(vat_rate) > 0
            
            if 'wht.rate > 0' in condition:
                wht_rate = self._get_nested_value(document, 'wht.rate')
                return wht_rate is not None and float(wht_rate) > 0
            
            return False
            
        except Exception:
            return False
    
    def _update_metrics(self, report: CompletenessReport):
        """Update completeness metrics"""
        self.metrics['total_checks'] += 1
        
        if report.is_complete:
            self.metrics['complete_documents'] += 1
        else:
            self.metrics['incomplete_documents'] += 1
        
        # Update average completion
        total_documents = self.metrics['complete_documents'] + self.metrics['incomplete_documents']
        if total_documents > 0:
            self.metrics['average_completion'] = (
                (self.metrics['average_completion'] * (total_documents - 1) + report.overall_completion) / total_documents
            )
        
        # Track common missing fields
        for missing_field in report.missing_fields:
            field_path = missing_field.field_path
            self.metrics['common_missing_fields'][field_path] = (
                self.metrics['common_missing_fields'].get(field_path, 0) + 1
            )
        
        # Update category performance
        for category, completion in report.category_completion.items():
            if category not in self.metrics['category_performance']:
                self.metrics['category_performance'][category] = {'total_score': 0, 'count': 0}
            
            perf = self.metrics['category_performance'][category]
            perf['total_score'] += completion
            perf['count'] += 1
            perf['average_score'] = perf['total_score'] / perf['count']
    
    def get_completeness_rules(self) -> Dict[str, CompletenessRule]:
        """Get all completeness rules"""
        return self.rules.copy()
    
    def get_field_categories(self) -> Dict[str, List[str]]:
        """Get field categories"""
        return self.field_categories.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get completeness metrics"""
        return {
            **self.metrics,
            'completion_rate': (
                self.metrics['complete_documents'] / 
                max(self.metrics['complete_documents'] + self.metrics['incomplete_documents'], 1)
            ) * 100
        }


# Factory functions for easy setup
def create_completeness_checker(level: CompletenessLevel = CompletenessLevel.STANDARD) -> CompletenessChecker:
    """Create completeness checker instance"""
    return CompletenessChecker(level)


async def check_document_completeness(document: Dict[str, Any], 
                                    level: CompletenessLevel = CompletenessLevel.STANDARD) -> CompletenessReport:
    """Check document completeness"""
    checker = create_completeness_checker(level)
    return await checker.check_completeness(document)


def get_completeness_summary(report: CompletenessReport) -> Dict[str, Any]:
    """Get completeness summary"""
    return {
        'document_id': report.document_id,
        'overall_completion': report.overall_completion,
        'is_complete': report.is_complete,
        'missing_fields_count': len(report.missing_fields),
        'incomplete_fields_count': len(report.incomplete_fields),
        'recommendations_count': len(report.recommendations),
        'category_completion': report.category_completion
    }