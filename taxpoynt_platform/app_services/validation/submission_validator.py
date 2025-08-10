"""
Pre-Submission Validation Service for APP Role

This service performs comprehensive pre-submission checks including:
- Document readiness verification
- FIRS system compatibility checks
- Transmission prerequisites validation
- Security requirements verification
- Business rule compliance checks
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiohttp
from pathlib import Path

from .firs_validator import FIRSValidator, ValidationResult, ValidationSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubmissionReadiness(Enum):
    """Submission readiness levels"""
    READY = "ready"
    PENDING = "pending"
    REQUIRES_FIXES = "requires_fixes"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"


class CheckCategory(Enum):
    """Pre-submission check categories"""
    DOCUMENT_INTEGRITY = "document_integrity"
    FIRS_COMPLIANCE = "firs_compliance"
    TRANSMISSION_READY = "transmission_ready"
    SECURITY_READY = "security_ready"
    BUSINESS_RULES = "business_rules"
    SYSTEM_COMPATIBILITY = "system_compatibility"


class CheckStatus(Enum):
    """Individual check status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"


@dataclass
class SubmissionCheck:
    """Individual submission check"""
    check_id: str
    check_name: str
    category: CheckCategory
    status: CheckStatus
    severity: ValidationSeverity
    message: str
    details: Optional[str] = None
    suggestion: Optional[str] = None
    blocking: bool = False
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmissionValidationReport:
    """Comprehensive submission validation report"""
    document_id: str
    validation_id: str
    timestamp: datetime
    readiness: SubmissionReadiness
    overall_score: float
    checks: List[SubmissionCheck] = field(default_factory=list)
    passed_checks: int = 0
    failed_checks: int = 0
    warning_checks: int = 0
    blocking_issues: int = 0
    categories: Dict[CheckCategory, Dict[str, Any]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    estimated_fix_time: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubmissionContext:
    """Context for submission validation"""
    document_data: Dict[str, Any]
    submission_endpoint: str
    security_level: str
    transmission_mode: str
    user_permissions: List[str]
    organization_settings: Dict[str, Any]
    external_dependencies: Dict[str, Any] = field(default_factory=dict)
    validation_options: Dict[str, Any] = field(default_factory=dict)


class SubmissionValidator:
    """
    Pre-submission validation service for APP role
    
    Handles:
    - Document readiness verification
    - FIRS system compatibility checks
    - Transmission prerequisites validation
    - Security requirements verification
    - Business rule compliance checks
    """
    
    def __init__(self, 
                 firs_validator: Optional[FIRSValidator] = None,
                 external_service_timeout: int = 30):
        self.firs_validator = firs_validator or FIRSValidator()
        self.external_service_timeout = external_service_timeout
        
        # Check definitions
        self.check_definitions = self._load_check_definitions()
        
        # Scoring weights
        self.scoring_weights = {
            CheckCategory.DOCUMENT_INTEGRITY: 0.25,
            CheckCategory.FIRS_COMPLIANCE: 0.30,
            CheckCategory.TRANSMISSION_READY: 0.20,
            CheckCategory.SECURITY_READY: 0.15,
            CheckCategory.BUSINESS_RULES: 0.10,
            CheckCategory.SYSTEM_COMPATIBILITY: 0.05
        }
        
        # Metrics
        self.metrics = {
            'total_validations': 0,
            'ready_submissions': 0,
            'blocked_submissions': 0,
            'average_score': 0.0,
            'average_validation_time': 0.0,
            'common_issues': {},
            'category_performance': {}
        }
        
        # Cache for external service checks
        self._service_cache = {}
        self._cache_expiry = {}
    
    def _load_check_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-submission check definitions"""
        return {
            # Document Integrity Checks
            'document_structure': {
                'check_id': 'DOC_STRUCT_001',
                'name': 'Document Structure Validation',
                'category': CheckCategory.DOCUMENT_INTEGRITY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Validate document has required structure and fields'
            },
            'document_consistency': {
                'check_id': 'DOC_CONSIST_001',
                'name': 'Document Consistency Check',
                'category': CheckCategory.DOCUMENT_INTEGRITY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify internal document consistency'
            },
            'document_completeness': {
                'check_id': 'DOC_COMPLETE_001',
                'name': 'Document Completeness Check',
                'category': CheckCategory.DOCUMENT_INTEGRITY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Ensure all required fields are present'
            },
            
            # FIRS Compliance Checks
            'firs_format_compliance': {
                'check_id': 'FIRS_FORMAT_001',
                'name': 'FIRS Format Compliance',
                'category': CheckCategory.FIRS_COMPLIANCE,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Validate document meets FIRS format requirements'
            },
            'firs_tax_compliance': {
                'check_id': 'FIRS_TAX_001',
                'name': 'FIRS Tax Compliance',
                'category': CheckCategory.FIRS_COMPLIANCE,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify tax calculations and compliance'
            },
            'firs_entity_validation': {
                'check_id': 'FIRS_ENTITY_001',
                'name': 'FIRS Entity Validation',
                'category': CheckCategory.FIRS_COMPLIANCE,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Validate entity information against FIRS database'
            },
            
            # Transmission Ready Checks
            'transmission_format': {
                'check_id': 'TRANS_FORMAT_001',
                'name': 'Transmission Format Check',
                'category': CheckCategory.TRANSMISSION_READY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify document is in correct transmission format'
            },
            'transmission_size': {
                'check_id': 'TRANS_SIZE_001',
                'name': 'Transmission Size Check',
                'category': CheckCategory.TRANSMISSION_READY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Check document size within transmission limits'
            },
            'transmission_encoding': {
                'check_id': 'TRANS_ENCODE_001',
                'name': 'Transmission Encoding Check',
                'category': CheckCategory.TRANSMISSION_READY,
                'blocking': False,
                'severity': ValidationSeverity.WARNING,
                'description': 'Verify document encoding is transmission-compatible'
            },
            
            # Security Ready Checks
            'security_authentication': {
                'check_id': 'SEC_AUTH_001',
                'name': 'Security Authentication Check',
                'category': CheckCategory.SECURITY_READY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify authentication credentials are valid'
            },
            'security_encryption': {
                'check_id': 'SEC_ENCRYPT_001',
                'name': 'Security Encryption Check',
                'category': CheckCategory.SECURITY_READY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify encryption requirements are met'
            },
            'security_signing': {
                'check_id': 'SEC_SIGN_001',
                'name': 'Security Signing Check',
                'category': CheckCategory.SECURITY_READY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify document signing requirements'
            },
            
            # Business Rules Checks
            'business_approval': {
                'check_id': 'BIZ_APPROVAL_001',
                'name': 'Business Approval Check',
                'category': CheckCategory.BUSINESS_RULES,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify document has required business approvals'
            },
            'business_limits': {
                'check_id': 'BIZ_LIMITS_001',
                'name': 'Business Limits Check',
                'category': CheckCategory.BUSINESS_RULES,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Check document against business limits'
            },
            'business_workflow': {
                'check_id': 'BIZ_WORKFLOW_001',
                'name': 'Business Workflow Check',
                'category': CheckCategory.BUSINESS_RULES,
                'blocking': False,
                'severity': ValidationSeverity.WARNING,
                'description': 'Verify document follows business workflow'
            },
            
            # System Compatibility Checks
            'system_connectivity': {
                'check_id': 'SYS_CONNECT_001',
                'name': 'System Connectivity Check',
                'category': CheckCategory.SYSTEM_COMPATIBILITY,
                'blocking': True,
                'severity': ValidationSeverity.ERROR,
                'description': 'Verify connectivity to FIRS systems'
            },
            'system_version': {
                'check_id': 'SYS_VERSION_001',
                'name': 'System Version Check',
                'category': CheckCategory.SYSTEM_COMPATIBILITY,
                'blocking': False,
                'severity': ValidationSeverity.WARNING,
                'description': 'Check system version compatibility'
            },
            'system_capacity': {
                'check_id': 'SYS_CAPACITY_001',
                'name': 'System Capacity Check',
                'category': CheckCategory.SYSTEM_COMPATIBILITY,
                'blocking': False,
                'severity': ValidationSeverity.WARNING,
                'description': 'Verify system capacity for submission'
            }
        }
    
    async def validate_submission(self, context: SubmissionContext) -> SubmissionValidationReport:
        """
        Perform comprehensive pre-submission validation
        
        Args:
            context: Submission context with document and settings
            
        Returns:
            SubmissionValidationReport with detailed results
        """
        start_time = time.time()
        
        # Initialize report
        report = SubmissionValidationReport(
            document_id=context.document_data.get('document_id', 'unknown'),
            validation_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            readiness=SubmissionReadiness.PENDING,
            overall_score=0.0
        )
        
        try:
            # Run all validation checks
            await self._run_validation_checks(context, report)
            
            # Calculate scores and readiness
            await self._calculate_scores(report)
            
            # Generate recommendations
            await self._generate_recommendations(report)
            
            # Update metrics
            self._update_metrics(report, time.time() - start_time)
            
            logger.info(f"Submission validation completed for {report.document_id}: "
                       f"{report.readiness.value.upper()} "
                       f"(Score: {report.overall_score:.1f}%)")
            
        except Exception as e:
            report.readiness = SubmissionReadiness.BLOCKED
            report.checks.append(SubmissionCheck(
                check_id='SYS_ERROR_001',
                check_name='System Error',
                category=CheckCategory.SYSTEM_COMPATIBILITY,
                status=CheckStatus.FAILED,
                severity=ValidationSeverity.CRITICAL,
                message=f'Validation system error: {str(e)}',
                blocking=True
            ))
            
            logger.error(f"Submission validation error for {report.document_id}: {e}")
        
        return report
    
    async def _run_validation_checks(self, context: SubmissionContext, report: SubmissionValidationReport):
        """Run all validation checks"""
        # Group checks by category for parallel execution
        check_groups = {}
        for check_key, check_def in self.check_definitions.items():
            category = check_def['category']
            if category not in check_groups:
                check_groups[category] = []
            check_groups[category].append((check_key, check_def))
        
        # Run checks by category
        for category, checks in check_groups.items():
            category_tasks = []
            for check_key, check_def in checks:
                task = self._run_individual_check(check_key, check_def, context, report)
                category_tasks.append(task)
            
            # Execute category checks in parallel
            await asyncio.gather(*category_tasks, return_exceptions=True)
    
    async def _run_individual_check(self, check_key: str, check_def: Dict[str, Any], 
                                  context: SubmissionContext, report: SubmissionValidationReport):
        """Run individual validation check"""
        start_time = time.time()
        
        try:
            # Dispatch to appropriate check method
            if check_key == 'document_structure':
                result = await self._check_document_structure(context)
            elif check_key == 'document_consistency':
                result = await self._check_document_consistency(context)
            elif check_key == 'document_completeness':
                result = await self._check_document_completeness(context)
            elif check_key == 'firs_format_compliance':
                result = await self._check_firs_format_compliance(context)
            elif check_key == 'firs_tax_compliance':
                result = await self._check_firs_tax_compliance(context)
            elif check_key == 'firs_entity_validation':
                result = await self._check_firs_entity_validation(context)
            elif check_key == 'transmission_format':
                result = await self._check_transmission_format(context)
            elif check_key == 'transmission_size':
                result = await self._check_transmission_size(context)
            elif check_key == 'transmission_encoding':
                result = await self._check_transmission_encoding(context)
            elif check_key == 'security_authentication':
                result = await self._check_security_authentication(context)
            elif check_key == 'security_encryption':
                result = await self._check_security_encryption(context)
            elif check_key == 'security_signing':
                result = await self._check_security_signing(context)
            elif check_key == 'business_approval':
                result = await self._check_business_approval(context)
            elif check_key == 'business_limits':
                result = await self._check_business_limits(context)
            elif check_key == 'business_workflow':
                result = await self._check_business_workflow(context)
            elif check_key == 'system_connectivity':
                result = await self._check_system_connectivity(context)
            elif check_key == 'system_version':
                result = await self._check_system_version(context)
            elif check_key == 'system_capacity':
                result = await self._check_system_capacity(context)
            else:
                result = CheckStatus.SKIPPED, "Check not implemented", None
            
            # Create check result
            status, message, details = result
            check = SubmissionCheck(
                check_id=check_def['check_id'],
                check_name=check_def['name'],
                category=check_def['category'],
                status=status,
                severity=check_def['severity'],
                message=message,
                details=details,
                blocking=check_def['blocking'],
                execution_time=time.time() - start_time
            )
            
            report.checks.append(check)
            
            # Update counters
            if status == CheckStatus.PASSED:
                report.passed_checks += 1
            elif status == CheckStatus.FAILED:
                report.failed_checks += 1
                if check.blocking:
                    report.blocking_issues += 1
            elif status == CheckStatus.WARNING:
                report.warning_checks += 1
            
        except Exception as e:
            # Handle check execution error
            check = SubmissionCheck(
                check_id=check_def['check_id'],
                check_name=check_def['name'],
                category=check_def['category'],
                status=CheckStatus.FAILED,
                severity=ValidationSeverity.CRITICAL,
                message=f'Check execution error: {str(e)}',
                blocking=True,
                execution_time=time.time() - start_time
            )
            
            report.checks.append(check)
            report.failed_checks += 1
            report.blocking_issues += 1
            
            logger.error(f"Check {check_key} failed: {e}")
    
    # Document Integrity Checks
    async def _check_document_structure(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check document structure"""
        document = context.document_data
        
        # Check required top-level fields
        required_fields = ['document_id', 'document_type', 'supplier', 'customer', 'items']
        missing_fields = [field for field in required_fields if field not in document]
        
        if missing_fields:
            return CheckStatus.FAILED, f"Missing required fields: {', '.join(missing_fields)}", None
        
        # Check document type is valid
        valid_types = ['invoice', 'credit_note', 'debit_note', 'receipt', 'proforma']
        if document.get('document_type') not in valid_types:
            return CheckStatus.FAILED, f"Invalid document type: {document.get('document_type')}", None
        
        return CheckStatus.PASSED, "Document structure is valid", None
    
    async def _check_document_consistency(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check document consistency"""
        document = context.document_data
        
        # Check amount consistency
        items = document.get('items', [])
        if items:
            calculated_subtotal = sum(item.get('total_price', 0) for item in items)
            document_subtotal = document.get('subtotal', 0)
            
            if abs(calculated_subtotal - document_subtotal) > 0.01:
                return CheckStatus.FAILED, "Subtotal inconsistent with item totals", f"Calculated: {calculated_subtotal}, Document: {document_subtotal}"
        
        # Check date consistency
        invoice_date = document.get('invoice_date')
        due_date = document.get('due_date')
        
        if invoice_date and due_date:
            try:
                invoice_dt = datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
                due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                
                if due_dt < invoice_dt:
                    return CheckStatus.FAILED, "Due date is before invoice date", None
            except ValueError:
                return CheckStatus.FAILED, "Invalid date format", None
        
        return CheckStatus.PASSED, "Document is internally consistent", None
    
    async def _check_document_completeness(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check document completeness"""
        document = context.document_data
        
        # Check supplier completeness
        supplier = document.get('supplier', {})
        required_supplier_fields = ['name', 'tin', 'address']
        missing_supplier = [field for field in required_supplier_fields if field not in supplier]
        
        if missing_supplier:
            return CheckStatus.FAILED, f"Incomplete supplier information: {', '.join(missing_supplier)}", None
        
        # Check customer completeness
        customer = document.get('customer', {})
        required_customer_fields = ['name', 'address']
        missing_customer = [field for field in required_customer_fields if field not in customer]
        
        if missing_customer:
            return CheckStatus.FAILED, f"Incomplete customer information: {', '.join(missing_customer)}", None
        
        # Check items completeness
        items = document.get('items', [])
        for i, item in enumerate(items):
            required_item_fields = ['description', 'quantity', 'unit_price', 'total_price']
            missing_item = [field for field in required_item_fields if field not in item]
            
            if missing_item:
                return CheckStatus.FAILED, f"Incomplete item {i+1}: {', '.join(missing_item)}", None
        
        return CheckStatus.PASSED, "Document is complete", None
    
    # FIRS Compliance Checks
    async def _check_firs_format_compliance(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check FIRS format compliance"""
        # Use FIRS validator for comprehensive format check
        firs_report = await self.firs_validator.validate_document(context.document_data)
        
        if firs_report.is_valid:
            return CheckStatus.PASSED, "Document complies with FIRS format requirements", None
        else:
            error_count = len(firs_report.errors)
            return CheckStatus.FAILED, f"FIRS format compliance failed: {error_count} errors", f"Errors: {', '.join([e.message for e in firs_report.errors[:3]])}"
    
    async def _check_firs_tax_compliance(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check FIRS tax compliance"""
        document = context.document_data
        
        # Check VAT compliance
        vat_info = document.get('vat', {})
        if vat_info:
            vat_rate = vat_info.get('rate', 0)
            if vat_rate not in [0.0, 0.075]:  # 0% or 7.5%
                return CheckStatus.FAILED, f"Invalid VAT rate: {vat_rate}", "Use 0% or 7.5% VAT rate"
        
        # Check currency compliance
        currency = document.get('currency', '').upper()
        if currency != 'NGN':
            return CheckStatus.FAILED, f"Invalid currency: {currency}", "Use NGN (Nigerian Naira)"
        
        return CheckStatus.PASSED, "Document complies with FIRS tax requirements", None
    
    async def _check_firs_entity_validation(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check FIRS entity validation"""
        # This would typically validate against FIRS database
        # For now, we'll do basic format validation
        
        supplier = context.document_data.get('supplier', {})
        supplier_tin = supplier.get('tin')
        
        if not supplier_tin:
            return CheckStatus.FAILED, "Supplier TIN is required", None
        
        # Basic TIN format validation
        import re
        if not re.match(r'^\d{8}-\d{4}$', supplier_tin):
            return CheckStatus.FAILED, f"Invalid supplier TIN format: {supplier_tin}", "Use format: 12345678-0001"
        
        return CheckStatus.PASSED, "Entity validation passed", None
    
    # Transmission Ready Checks
    async def _check_transmission_format(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check transmission format"""
        document = context.document_data
        
        # Check if document can be serialized to JSON
        try:
            json.dumps(document)
        except TypeError as e:
            return CheckStatus.FAILED, f"Document not JSON serializable: {str(e)}", None
        
        # Check for problematic characters
        document_str = str(document)
        if any(ord(char) > 127 for char in document_str):
            return CheckStatus.WARNING, "Document contains non-ASCII characters", "May cause transmission issues"
        
        return CheckStatus.PASSED, "Document is transmission-ready", None
    
    async def _check_transmission_size(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check transmission size"""
        document_json = json.dumps(context.document_data)
        document_size = len(document_json.encode('utf-8'))
        
        # Check against transmission limits (example: 1MB)
        max_size = 1024 * 1024  # 1MB
        if document_size > max_size:
            return CheckStatus.FAILED, f"Document too large: {document_size} bytes", f"Maximum size: {max_size} bytes"
        
        # Warning for large documents
        if document_size > max_size * 0.8:
            return CheckStatus.WARNING, f"Document is large: {document_size} bytes", "Consider optimizing document size"
        
        return CheckStatus.PASSED, f"Document size acceptable: {document_size} bytes", None
    
    async def _check_transmission_encoding(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check transmission encoding"""
        # Check if document can be encoded as UTF-8
        try:
            document_json = json.dumps(context.document_data)
            document_json.encode('utf-8')
        except UnicodeEncodeError as e:
            return CheckStatus.FAILED, f"Document encoding error: {str(e)}", None
        
        return CheckStatus.PASSED, "Document encoding is compatible", None
    
    # Security Ready Checks
    async def _check_security_authentication(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check security authentication"""
        # Check if user has required permissions
        required_permissions = ['submit_documents', 'access_firs']
        missing_permissions = [perm for perm in required_permissions if perm not in context.user_permissions]
        
        if missing_permissions:
            return CheckStatus.FAILED, f"Missing permissions: {', '.join(missing_permissions)}", None
        
        return CheckStatus.PASSED, "Authentication requirements met", None
    
    async def _check_security_encryption(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check security encryption"""
        # Check if encryption is configured for the security level
        security_level = context.security_level.lower()
        
        if security_level in ['high', 'maximum']:
            # Check if encryption keys are available
            encryption_config = context.external_dependencies.get('encryption', {})
            if not encryption_config.get('encryption_key'):
                return CheckStatus.FAILED, "Encryption key not configured", "Configure encryption key for high security"
        
        return CheckStatus.PASSED, "Encryption requirements met", None
    
    async def _check_security_signing(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check security signing"""
        # Check if signing is configured
        signing_config = context.external_dependencies.get('signing', {})
        if not signing_config.get('signing_key'):
            return CheckStatus.FAILED, "Signing key not configured", "Configure signing key for document authentication"
        
        return CheckStatus.PASSED, "Signing requirements met", None
    
    # Business Rules Checks
    async def _check_business_approval(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check business approval"""
        document = context.document_data
        
        # Check if high-value documents require approval
        total_amount = document.get('total_amount', 0)
        approval_threshold = context.organization_settings.get('approval_threshold', 100000)
        
        if total_amount > approval_threshold:
            approval_status = document.get('approval_status')
            if approval_status != 'approved':
                return CheckStatus.FAILED, f"Document requires approval (Amount: {total_amount})", f"Threshold: {approval_threshold}"
        
        return CheckStatus.PASSED, "Business approval requirements met", None
    
    async def _check_business_limits(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check business limits"""
        document = context.document_data
        
        # Check daily submission limits
        daily_limit = context.organization_settings.get('daily_submission_limit', 1000)
        current_submissions = context.external_dependencies.get('daily_submissions', 0)
        
        if current_submissions >= daily_limit:
            return CheckStatus.FAILED, f"Daily submission limit exceeded: {current_submissions}/{daily_limit}", None
        
        return CheckStatus.PASSED, "Business limits complied", None
    
    async def _check_business_workflow(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check business workflow"""
        document = context.document_data
        
        # Check if document follows required workflow
        workflow_status = document.get('workflow_status')
        required_workflow = context.organization_settings.get('required_workflow', ['created', 'reviewed'])
        
        if workflow_status not in required_workflow:
            return CheckStatus.WARNING, f"Document workflow incomplete: {workflow_status}", f"Required: {required_workflow}"
        
        return CheckStatus.PASSED, "Business workflow complied", None
    
    # System Compatibility Checks
    async def _check_system_connectivity(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check system connectivity"""
        # Check FIRS system connectivity
        endpoint = context.submission_endpoint
        
        try:
            # Use cached result if available
            cache_key = f"connectivity_{endpoint}"
            if cache_key in self._service_cache:
                cache_time = self._cache_expiry.get(cache_key, datetime.min)
                if datetime.utcnow() < cache_time:
                    return self._service_cache[cache_key]
            
            # Make connectivity check
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(f"{endpoint}/health") as response:
                    if response.status == 200:
                        result = CheckStatus.PASSED, "FIRS system is accessible", None
                    else:
                        result = CheckStatus.FAILED, f"FIRS system not accessible: {response.status}", None
            
            # Cache result for 5 minutes
            self._service_cache[cache_key] = result
            self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(minutes=5)
            
            return result
            
        except Exception as e:
            return CheckStatus.FAILED, f"Connectivity check failed: {str(e)}", None
    
    async def _check_system_version(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check system version"""
        # Check if system version is compatible
        current_version = context.external_dependencies.get('system_version', '1.0.0')
        minimum_version = '1.0.0'
        
        # Simple version comparison
        if current_version < minimum_version:
            return CheckStatus.WARNING, f"System version may be outdated: {current_version}", f"Minimum: {minimum_version}"
        
        return CheckStatus.PASSED, f"System version compatible: {current_version}", None
    
    async def _check_system_capacity(self, context: SubmissionContext) -> Tuple[CheckStatus, str, Optional[str]]:
        """Check system capacity"""
        # Check system resource capacity
        cpu_usage = context.external_dependencies.get('cpu_usage', 0)
        memory_usage = context.external_dependencies.get('memory_usage', 0)
        
        if cpu_usage > 90 or memory_usage > 90:
            return CheckStatus.WARNING, f"High system resource usage: CPU {cpu_usage}%, Memory {memory_usage}%", "Consider optimizing system resources"
        
        return CheckStatus.PASSED, "System capacity adequate", None
    
    async def _calculate_scores(self, report: SubmissionValidationReport):
        """Calculate overall scores and readiness"""
        # Calculate category scores
        for category in CheckCategory:
            category_checks = [check for check in report.checks if check.category == category]
            if category_checks:
                passed = sum(1 for check in category_checks if check.status == CheckStatus.PASSED)
                total = len(category_checks)
                score = (passed / total) * 100 if total > 0 else 0
                
                report.categories[category] = {
                    'score': score,
                    'passed': passed,
                    'total': total,
                    'weight': self.scoring_weights[category]
                }
        
        # Calculate overall score
        weighted_score = 0
        total_weight = 0
        for category, data in report.categories.items():
            weight = self.scoring_weights[category]
            weighted_score += data['score'] * weight
            total_weight += weight
        
        report.overall_score = weighted_score / total_weight if total_weight > 0 else 0
        
        # Determine readiness
        if report.blocking_issues > 0:
            report.readiness = SubmissionReadiness.BLOCKED
        elif report.overall_score >= 95:
            report.readiness = SubmissionReadiness.READY
        elif report.overall_score >= 80:
            report.readiness = SubmissionReadiness.PENDING
        else:
            report.readiness = SubmissionReadiness.REQUIRES_FIXES
    
    async def _generate_recommendations(self, report: SubmissionValidationReport):
        """Generate recommendations based on validation results"""
        recommendations = []
        
        # Prioritize blocking issues
        blocking_checks = [check for check in report.checks if check.status == CheckStatus.FAILED and check.blocking]
        if blocking_checks:
            recommendations.append(f"Fix {len(blocking_checks)} blocking issues before submission")
        
        # Category-specific recommendations
        for category, data in report.categories.items():
            if data['score'] < 80:
                recommendations.append(f"Improve {category.value} compliance (Score: {data['score']:.1f}%)")
        
        # Specific recommendations for common issues
        failed_checks = [check for check in report.checks if check.status == CheckStatus.FAILED]
        for check in failed_checks:
            if check.suggestion:
                recommendations.append(check.suggestion)
        
        report.recommendations = recommendations[:10]  # Limit to top 10
        
        # Estimate fix time
        if report.readiness == SubmissionReadiness.BLOCKED:
            report.estimated_fix_time = 60  # 60 minutes
        elif report.readiness == SubmissionReadiness.REQUIRES_FIXES:
            report.estimated_fix_time = 30  # 30 minutes
        elif report.readiness == SubmissionReadiness.PENDING:
            report.estimated_fix_time = 15  # 15 minutes
    
    def _update_metrics(self, report: SubmissionValidationReport, validation_time: float):
        """Update validation metrics"""
        self.metrics['total_validations'] += 1
        self.metrics['average_validation_time'] = (
            (self.metrics['average_validation_time'] * (self.metrics['total_validations'] - 1) + validation_time) /
            self.metrics['total_validations']
        )
        
        # Update readiness metrics
        if report.readiness == SubmissionReadiness.READY:
            self.metrics['ready_submissions'] += 1
        elif report.readiness == SubmissionReadiness.BLOCKED:
            self.metrics['blocked_submissions'] += 1
        
        # Update average score
        self.metrics['average_score'] = (
            (self.metrics['average_score'] * (self.metrics['total_validations'] - 1) + report.overall_score) /
            self.metrics['total_validations']
        )
        
        # Track common issues
        for check in report.checks:
            if check.status == CheckStatus.FAILED:
                issue_key = f"{check.category.value}:{check.check_name}"
                self.metrics['common_issues'][issue_key] = (
                    self.metrics['common_issues'].get(issue_key, 0) + 1
                )
        
        # Update category performance
        for category, data in report.categories.items():
            cat_key = category.value
            if cat_key not in self.metrics['category_performance']:
                self.metrics['category_performance'][cat_key] = {'total_score': 0, 'count': 0}
            
            perf = self.metrics['category_performance'][cat_key]
            perf['total_score'] += data['score']
            perf['count'] += 1
            perf['average_score'] = perf['total_score'] / perf['count']
    
    def get_check_definitions(self) -> Dict[str, Dict[str, Any]]:
        """Get all check definitions"""
        return self.check_definitions.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return {
            **self.metrics,
            'readiness_rate': (
                self.metrics['ready_submissions'] / 
                max(self.metrics['total_validations'], 1)
            ) * 100,
            'blocked_rate': (
                self.metrics['blocked_submissions'] / 
                max(self.metrics['total_validations'], 1)
            ) * 100
        }


# Factory functions for easy setup
def create_submission_validator(firs_validator: Optional[FIRSValidator] = None) -> SubmissionValidator:
    """Create submission validator instance"""
    return SubmissionValidator(firs_validator)


def create_submission_context(document_data: Dict[str, Any],
                            submission_endpoint: str,
                            security_level: str = "standard",
                            transmission_mode: str = "sync",
                            user_permissions: Optional[List[str]] = None,
                            organization_settings: Optional[Dict[str, Any]] = None) -> SubmissionContext:
    """Create submission context"""
    return SubmissionContext(
        document_data=document_data,
        submission_endpoint=submission_endpoint,
        security_level=security_level,
        transmission_mode=transmission_mode,
        user_permissions=user_permissions or [],
        organization_settings=organization_settings or {}
    )


async def validate_document_submission(document_data: Dict[str, Any],
                                     submission_endpoint: str,
                                     **kwargs) -> SubmissionValidationReport:
    """Validate document for submission"""
    context = create_submission_context(document_data, submission_endpoint, **kwargs)
    validator = create_submission_validator()
    return await validator.validate_submission(context)