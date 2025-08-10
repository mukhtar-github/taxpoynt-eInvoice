"""
FIRS-Specific Validation Service for APP Role

This service handles FIRS-specific validation rules including:
- Nigerian tax compliance validation
- FIRS document format requirements
- Tax identification number validation
- Currency and amount validation
- Business registration validation
"""

import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from decimal import Decimal, InvalidOperation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class DocumentType(Enum):
    """FIRS document types"""
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    RECEIPT = "receipt"
    PROFORMA = "proforma"


class TaxType(Enum):
    """Nigerian tax types"""
    VAT = "vat"
    WHT = "wht"
    STAMP_DUTY = "stamp_duty"
    CUSTOM_DUTY = "custom_duty"
    EXCISE_DUTY = "excise_duty"


@dataclass
class ValidationResult:
    """Individual validation result"""
    rule_id: str
    field_name: str
    severity: ValidationSeverity
    message: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FIRSValidationReport:
    """FIRS validation report"""
    document_id: str
    document_type: DocumentType
    validation_timestamp: datetime
    is_valid: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: List[ValidationResult] = field(default_factory=list)
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    info: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class FIRSValidator:
    """
    FIRS-specific validation service for APP role
    
    Handles:
    - Nigerian tax compliance validation
    - FIRS document format requirements
    - Tax identification number validation
    - Currency and amount validation
    - Business registration validation
    """
    
    def __init__(self):
        # Nigerian-specific validation patterns
        self.patterns = {
            'tin': r'^\d{8}-\d{4}$',  # Tax Identification Number
            'vat_number': r'^\d{8}-\d{4}$',  # VAT Number
            'phone': r'^\+234[0-9]{10}$|^0[0-9]{10}$',  # Nigerian phone
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'postal_code': r'^\d{6}$',  # Nigerian postal code
            'bank_account': r'^\d{10}$',  # Nigerian bank account
            'currency_code': r'^NGN$',  # Nigerian Naira
            'amount': r'^\d+(\.\d{1,2})?$'  # Currency amount
        }
        
        # Nigerian states
        self.nigerian_states = {
            'AB': 'Abia', 'AD': 'Adamawa', 'AK': 'Akwa Ibom', 'AN': 'Anambra',
            'BA': 'Bauchi', 'BY': 'Bayelsa', 'BE': 'Benue', 'BO': 'Borno',
            'CR': 'Cross River', 'DE': 'Delta', 'EB': 'Ebonyi', 'ED': 'Edo',
            'EK': 'Ekiti', 'EN': 'Enugu', 'GO': 'Gombe', 'IM': 'Imo',
            'JI': 'Jigawa', 'KD': 'Kaduna', 'KN': 'Kano', 'KT': 'Katsina',
            'KE': 'Kebbi', 'KO': 'Kogi', 'KW': 'Kwara', 'LA': 'Lagos',
            'NA': 'Nasarawa', 'NI': 'Niger', 'OG': 'Ogun', 'ON': 'Ondo',
            'OS': 'Osun', 'OY': 'Oyo', 'PL': 'Plateau', 'RI': 'Rivers',
            'SO': 'Sokoto', 'TA': 'Taraba', 'YO': 'Yobe', 'ZA': 'Zamfara',
            'FC': 'Federal Capital Territory'
        }
        
        # VAT rates
        self.vat_rates = {
            'standard': Decimal('0.075'),  # 7.5%
            'zero_rated': Decimal('0.00'),  # 0%
            'exempt': None
        }
        
        # Withholding tax rates
        self.wht_rates = {
            'dividend': Decimal('0.10'),  # 10%
            'interest': Decimal('0.10'),  # 10%
            'rent': Decimal('0.10'),  # 10%
            'royalty': Decimal('0.10'),  # 10%
            'technical_service': Decimal('0.10'),  # 10%
            'professional_service': Decimal('0.05'),  # 5%
            'construction': Decimal('0.05'),  # 5%
            'consultancy': Decimal('0.05'),  # 5%
            'transport': Decimal('0.05'),  # 5%
            'commission': Decimal('0.05')  # 5%
        }
        
        # FIRS validation rules
        self.validation_rules = self._load_validation_rules()
        
        # Metrics
        self.metrics = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'validation_time': 0.0,
            'common_errors': {},
            'validation_history': []
        }
    
    def _load_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load FIRS validation rules"""
        return {
            'tin_validation': {
                'rule_id': 'FIRS_TIN_001',
                'description': 'Validate Tax Identification Number format',
                'pattern': self.patterns['tin'],
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'vat_number_validation': {
                'rule_id': 'FIRS_VAT_001',
                'description': 'Validate VAT Number format',
                'pattern': self.patterns['vat_number'],
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'currency_validation': {
                'rule_id': 'FIRS_CUR_001',
                'description': 'Validate currency is NGN',
                'pattern': self.patterns['currency_code'],
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'amount_validation': {
                'rule_id': 'FIRS_AMT_001',
                'description': 'Validate amount format',
                'pattern': self.patterns['amount'],
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'state_validation': {
                'rule_id': 'FIRS_STATE_001',
                'description': 'Validate Nigerian state code',
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'phone_validation': {
                'rule_id': 'FIRS_PHONE_001',
                'description': 'Validate Nigerian phone number',
                'pattern': self.patterns['phone'],
                'required': False,
                'severity': ValidationSeverity.WARNING
            },
            'email_validation': {
                'rule_id': 'FIRS_EMAIL_001',
                'description': 'Validate email format',
                'pattern': self.patterns['email'],
                'required': False,
                'severity': ValidationSeverity.WARNING
            },
            'vat_rate_validation': {
                'rule_id': 'FIRS_VAT_RATE_001',
                'description': 'Validate VAT rate is correct',
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'wht_rate_validation': {
                'rule_id': 'FIRS_WHT_RATE_001',
                'description': 'Validate WHT rate is correct',
                'required': False,
                'severity': ValidationSeverity.WARNING
            },
            'invoice_number_validation': {
                'rule_id': 'FIRS_INV_001',
                'description': 'Validate invoice number format',
                'required': True,
                'severity': ValidationSeverity.ERROR
            },
            'date_validation': {
                'rule_id': 'FIRS_DATE_001',
                'description': 'Validate date format and range',
                'required': True,
                'severity': ValidationSeverity.ERROR
            }
        }
    
    async def validate_document(self, document: Dict[str, Any]) -> FIRSValidationReport:
        """
        Validate document against FIRS-specific rules
        
        Args:
            document: Document data to validate
            
        Returns:
            FIRSValidationReport with validation results
        """
        start_time = asyncio.get_event_loop().time()
        
        # Determine document type
        document_type = self._determine_document_type(document)
        
        # Initialize validation report
        report = FIRSValidationReport(
            document_id=document.get('document_id', 'unknown'),
            document_type=document_type,
            validation_timestamp=datetime.utcnow(),
            is_valid=True,
            total_checks=0,
            passed_checks=0,
            failed_checks=0
        )
        
        try:
            # Run validation checks
            await self._run_validation_checks(document, report)
            
            # Categorize results
            self._categorize_results(report)
            
            # Determine overall validity
            report.is_valid = len(report.errors) == 0
            
            # Update metrics
            self.metrics['total_validations'] += 1
            if report.is_valid:
                self.metrics['successful_validations'] += 1
            else:
                self.metrics['failed_validations'] += 1
                
                # Track common errors
                for error in report.errors:
                    error_key = f"{error.rule_id}:{error.field_name}"
                    self.metrics['common_errors'][error_key] = (
                        self.metrics['common_errors'].get(error_key, 0) + 1
                    )
            
            # Update validation time
            validation_time = asyncio.get_event_loop().time() - start_time
            self.metrics['validation_time'] += validation_time
            
            logger.info(f"FIRS validation completed for {report.document_id}: "
                       f"{'VALID' if report.is_valid else 'INVALID'} "
                       f"({report.passed_checks}/{report.total_checks} checks passed)")
            
        except Exception as e:
            report.is_valid = False
            report.errors.append(ValidationResult(
                rule_id="FIRS_SYS_001",
                field_name="system",
                severity=ValidationSeverity.CRITICAL,
                message=f"Validation system error: {str(e)}"
            ))
            
            logger.error(f"FIRS validation error for {report.document_id}: {e}")
        
        return report
    
    def _determine_document_type(self, document: Dict[str, Any]) -> DocumentType:
        """Determine document type from document data"""
        doc_type = document.get('document_type', '').lower()
        
        type_mapping = {
            'invoice': DocumentType.INVOICE,
            'credit_note': DocumentType.CREDIT_NOTE,
            'debit_note': DocumentType.DEBIT_NOTE,
            'receipt': DocumentType.RECEIPT,
            'proforma': DocumentType.PROFORMA
        }
        
        return type_mapping.get(doc_type, DocumentType.INVOICE)
    
    async def _run_validation_checks(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Run all validation checks"""
        validation_tasks = [
            self._validate_tin(document, report),
            self._validate_vat_number(document, report),
            self._validate_currency(document, report),
            self._validate_amounts(document, report),
            self._validate_addresses(document, report),
            self._validate_contacts(document, report),
            self._validate_tax_calculations(document, report),
            self._validate_invoice_details(document, report),
            self._validate_dates(document, report),
            self._validate_items(document, report)
        ]
        
        await asyncio.gather(*validation_tasks)
    
    async def _validate_tin(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate Tax Identification Numbers"""
        # Validate supplier TIN
        supplier_tin = document.get('supplier', {}).get('tin')
        if supplier_tin:
            await self._validate_tin_format(supplier_tin, 'supplier.tin', report)
        else:
            report.results.append(ValidationResult(
                rule_id='FIRS_TIN_001',
                field_name='supplier.tin',
                severity=ValidationSeverity.ERROR,
                message='Supplier TIN is required'
            ))
        
        # Validate customer TIN (if applicable)
        customer_tin = document.get('customer', {}).get('tin')
        if customer_tin:
            await self._validate_tin_format(customer_tin, 'customer.tin', report)
        
        report.total_checks += 2
    
    async def _validate_tin_format(self, tin: str, field_name: str, report: FIRSValidationReport):
        """Validate TIN format"""
        if not re.match(self.patterns['tin'], tin):
            report.results.append(ValidationResult(
                rule_id='FIRS_TIN_001',
                field_name=field_name,
                severity=ValidationSeverity.ERROR,
                message='Invalid TIN format',
                expected_value='XXXXXXXX-XXXX format',
                actual_value=tin,
                suggestion='Use format: 12345678-0001'
            ))
        else:
            report.passed_checks += 1
    
    async def _validate_vat_number(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate VAT Numbers"""
        # Validate supplier VAT number
        supplier_vat = document.get('supplier', {}).get('vat_number')
        if supplier_vat:
            if not re.match(self.patterns['vat_number'], supplier_vat):
                report.results.append(ValidationResult(
                    rule_id='FIRS_VAT_001',
                    field_name='supplier.vat_number',
                    severity=ValidationSeverity.ERROR,
                    message='Invalid VAT number format',
                    expected_value='XXXXXXXX-XXXX format',
                    actual_value=supplier_vat,
                    suggestion='Use format: 12345678-0001'
                ))
            else:
                report.passed_checks += 1
        
        # Validate customer VAT number (if applicable)
        customer_vat = document.get('customer', {}).get('vat_number')
        if customer_vat:
            if not re.match(self.patterns['vat_number'], customer_vat):
                report.results.append(ValidationResult(
                    rule_id='FIRS_VAT_001',
                    field_name='customer.vat_number',
                    severity=ValidationSeverity.ERROR,
                    message='Invalid VAT number format',
                    expected_value='XXXXXXXX-XXXX format',
                    actual_value=customer_vat,
                    suggestion='Use format: 12345678-0001'
                ))
            else:
                report.passed_checks += 1
        
        report.total_checks += 2
    
    async def _validate_currency(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate currency is NGN"""
        currency = document.get('currency', '').upper()
        
        if currency != 'NGN':
            report.results.append(ValidationResult(
                rule_id='FIRS_CUR_001',
                field_name='currency',
                severity=ValidationSeverity.ERROR,
                message='Currency must be NGN (Nigerian Naira)',
                expected_value='NGN',
                actual_value=currency,
                suggestion='Set currency to NGN'
            ))
        else:
            report.passed_checks += 1
        
        report.total_checks += 1
    
    async def _validate_amounts(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate amount formats and calculations"""
        # Validate subtotal
        subtotal = document.get('subtotal')
        if subtotal is not None:
            await self._validate_amount_format(subtotal, 'subtotal', report)
        
        # Validate tax amount
        tax_amount = document.get('tax_amount')
        if tax_amount is not None:
            await self._validate_amount_format(tax_amount, 'tax_amount', report)
        
        # Validate total amount
        total_amount = document.get('total_amount')
        if total_amount is not None:
            await self._validate_amount_format(total_amount, 'total_amount', report)
        
        # Validate calculation consistency
        if subtotal is not None and tax_amount is not None and total_amount is not None:
            await self._validate_amount_calculation(subtotal, tax_amount, total_amount, report)
        
        report.total_checks += 4
    
    async def _validate_amount_format(self, amount: Union[str, float, int], field_name: str, report: FIRSValidationReport):
        """Validate amount format"""
        try:
            decimal_amount = Decimal(str(amount))
            if decimal_amount < 0:
                report.results.append(ValidationResult(
                    rule_id='FIRS_AMT_001',
                    field_name=field_name,
                    severity=ValidationSeverity.ERROR,
                    message='Amount cannot be negative',
                    actual_value=str(amount),
                    suggestion='Use positive amount'
                ))
            else:
                report.passed_checks += 1
        except (InvalidOperation, ValueError):
            report.results.append(ValidationResult(
                rule_id='FIRS_AMT_001',
                field_name=field_name,
                severity=ValidationSeverity.ERROR,
                message='Invalid amount format',
                actual_value=str(amount),
                suggestion='Use decimal number format'
            ))
    
    async def _validate_amount_calculation(self, subtotal: Union[str, float, int], 
                                         tax_amount: Union[str, float, int], 
                                         total_amount: Union[str, float, int], 
                                         report: FIRSValidationReport):
        """Validate amount calculation consistency"""
        try:
            subtotal_decimal = Decimal(str(subtotal))
            tax_decimal = Decimal(str(tax_amount))
            total_decimal = Decimal(str(total_amount))
            
            calculated_total = subtotal_decimal + tax_decimal
            
            if abs(calculated_total - total_decimal) > Decimal('0.01'):
                report.results.append(ValidationResult(
                    rule_id='FIRS_CALC_001',
                    field_name='total_amount',
                    severity=ValidationSeverity.ERROR,
                    message='Total amount calculation mismatch',
                    expected_value=str(calculated_total),
                    actual_value=str(total_decimal),
                    suggestion='Verify: total_amount = subtotal + tax_amount'
                ))
            else:
                report.passed_checks += 1
        except (InvalidOperation, ValueError):
            report.results.append(ValidationResult(
                rule_id='FIRS_CALC_001',
                field_name='amount_calculation',
                severity=ValidationSeverity.ERROR,
                message='Cannot validate amount calculation due to invalid format'
            ))
    
    async def _validate_addresses(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate address information"""
        # Validate supplier address
        supplier_address = document.get('supplier', {}).get('address', {})
        if supplier_address:
            await self._validate_address(supplier_address, 'supplier.address', report)
        
        # Validate customer address
        customer_address = document.get('customer', {}).get('address', {})
        if customer_address:
            await self._validate_address(customer_address, 'customer.address', report)
        
        report.total_checks += 2
    
    async def _validate_address(self, address: Dict[str, Any], field_prefix: str, report: FIRSValidationReport):
        """Validate address format"""
        # Validate state
        state = address.get('state', '').upper()
        if state and state not in self.nigerian_states:
            report.results.append(ValidationResult(
                rule_id='FIRS_STATE_001',
                field_name=f'{field_prefix}.state',
                severity=ValidationSeverity.ERROR,
                message='Invalid Nigerian state code',
                actual_value=state,
                suggestion=f'Use one of: {", ".join(self.nigerian_states.keys())}'
            ))
        else:
            report.passed_checks += 1
        
        # Validate postal code
        postal_code = address.get('postal_code', '')
        if postal_code and not re.match(self.patterns['postal_code'], postal_code):
            report.results.append(ValidationResult(
                rule_id='FIRS_POSTAL_001',
                field_name=f'{field_prefix}.postal_code',
                severity=ValidationSeverity.WARNING,
                message='Invalid postal code format',
                expected_value='6-digit number',
                actual_value=postal_code,
                suggestion='Use 6-digit postal code'
            ))
    
    async def _validate_contacts(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate contact information"""
        # Validate supplier contacts
        supplier = document.get('supplier', {})
        if supplier:
            await self._validate_contact_info(supplier, 'supplier', report)
        
        # Validate customer contacts
        customer = document.get('customer', {})
        if customer:
            await self._validate_contact_info(customer, 'customer', report)
        
        report.total_checks += 2
    
    async def _validate_contact_info(self, entity: Dict[str, Any], entity_type: str, report: FIRSValidationReport):
        """Validate contact information"""
        # Validate phone number
        phone = entity.get('phone')
        if phone:
            if not re.match(self.patterns['phone'], phone):
                report.results.append(ValidationResult(
                    rule_id='FIRS_PHONE_001',
                    field_name=f'{entity_type}.phone',
                    severity=ValidationSeverity.WARNING,
                    message='Invalid phone number format',
                    expected_value='+234XXXXXXXXXX or 0XXXXXXXXXX',
                    actual_value=phone,
                    suggestion='Use format: +234XXXXXXXXXX or 0XXXXXXXXXX'
                ))
            else:
                report.passed_checks += 1
        
        # Validate email
        email = entity.get('email')
        if email:
            if not re.match(self.patterns['email'], email):
                report.results.append(ValidationResult(
                    rule_id='FIRS_EMAIL_001',
                    field_name=f'{entity_type}.email',
                    severity=ValidationSeverity.WARNING,
                    message='Invalid email format',
                    actual_value=email,
                    suggestion='Use valid email format'
                ))
            else:
                report.passed_checks += 1
    
    async def _validate_tax_calculations(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate tax calculations"""
        # Validate VAT calculations
        vat_info = document.get('vat', {})
        if vat_info:
            await self._validate_vat_calculation(vat_info, document, report)
        
        # Validate WHT calculations
        wht_info = document.get('wht', {})
        if wht_info:
            await self._validate_wht_calculation(wht_info, document, report)
        
        report.total_checks += 2
    
    async def _validate_vat_calculation(self, vat_info: Dict[str, Any], document: Dict[str, Any], report: FIRSValidationReport):
        """Validate VAT calculation"""
        vat_rate = vat_info.get('rate')
        vat_amount = vat_info.get('amount')
        subtotal = document.get('subtotal')
        
        if vat_rate is not None and vat_amount is not None and subtotal is not None:
            try:
                vat_rate_decimal = Decimal(str(vat_rate))
                vat_amount_decimal = Decimal(str(vat_amount))
                subtotal_decimal = Decimal(str(subtotal))
                
                # Check if VAT rate is valid
                if vat_rate_decimal not in [Decimal('0.075'), Decimal('0.00')]:
                    report.results.append(ValidationResult(
                        rule_id='FIRS_VAT_RATE_001',
                        field_name='vat.rate',
                        severity=ValidationSeverity.ERROR,
                        message='Invalid VAT rate',
                        expected_value='0.075 (7.5%) or 0.00 (0%)',
                        actual_value=str(vat_rate),
                        suggestion='Use 7.5% standard rate or 0% for exempt items'
                    ))
                else:
                    # Calculate expected VAT amount
                    expected_vat = subtotal_decimal * vat_rate_decimal
                    
                    if abs(expected_vat - vat_amount_decimal) > Decimal('0.01'):
                        report.results.append(ValidationResult(
                            rule_id='FIRS_VAT_CALC_001',
                            field_name='vat.amount',
                            severity=ValidationSeverity.ERROR,
                            message='VAT amount calculation mismatch',
                            expected_value=str(expected_vat),
                            actual_value=str(vat_amount),
                            suggestion='Verify: vat_amount = subtotal * vat_rate'
                        ))
                    else:
                        report.passed_checks += 1
            except (InvalidOperation, ValueError):
                report.results.append(ValidationResult(
                    rule_id='FIRS_VAT_CALC_001',
                    field_name='vat',
                    severity=ValidationSeverity.ERROR,
                    message='Cannot validate VAT calculation due to invalid format'
                ))
    
    async def _validate_wht_calculation(self, wht_info: Dict[str, Any], document: Dict[str, Any], report: FIRSValidationReport):
        """Validate WHT calculation"""
        wht_rate = wht_info.get('rate')
        wht_amount = wht_info.get('amount')
        wht_type = wht_info.get('type')
        subtotal = document.get('subtotal')
        
        if wht_rate is not None and wht_amount is not None and subtotal is not None:
            try:
                wht_rate_decimal = Decimal(str(wht_rate))
                wht_amount_decimal = Decimal(str(wht_amount))
                subtotal_decimal = Decimal(str(subtotal))
                
                # Check if WHT rate is valid for type
                if wht_type and wht_type in self.wht_rates:
                    expected_rate = self.wht_rates[wht_type]
                    if wht_rate_decimal != expected_rate:
                        report.results.append(ValidationResult(
                            rule_id='FIRS_WHT_RATE_001',
                            field_name='wht.rate',
                            severity=ValidationSeverity.WARNING,
                            message=f'Unexpected WHT rate for {wht_type}',
                            expected_value=str(expected_rate),
                            actual_value=str(wht_rate),
                            suggestion=f'Standard rate for {wht_type} is {expected_rate}'
                        ))
                
                # Calculate expected WHT amount
                expected_wht = subtotal_decimal * wht_rate_decimal
                
                if abs(expected_wht - wht_amount_decimal) > Decimal('0.01'):
                    report.results.append(ValidationResult(
                        rule_id='FIRS_WHT_CALC_001',
                        field_name='wht.amount',
                        severity=ValidationSeverity.ERROR,
                        message='WHT amount calculation mismatch',
                        expected_value=str(expected_wht),
                        actual_value=str(wht_amount),
                        suggestion='Verify: wht_amount = subtotal * wht_rate'
                    ))
                else:
                    report.passed_checks += 1
            except (InvalidOperation, ValueError):
                report.results.append(ValidationResult(
                    rule_id='FIRS_WHT_CALC_001',
                    field_name='wht',
                    severity=ValidationSeverity.ERROR,
                    message='Cannot validate WHT calculation due to invalid format'
                ))
    
    async def _validate_invoice_details(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate invoice-specific details"""
        # Validate invoice number
        invoice_number = document.get('invoice_number')
        if not invoice_number:
            report.results.append(ValidationResult(
                rule_id='FIRS_INV_001',
                field_name='invoice_number',
                severity=ValidationSeverity.ERROR,
                message='Invoice number is required'
            ))
        else:
            report.passed_checks += 1
        
        # Validate invoice series/prefix
        invoice_series = document.get('invoice_series')
        if invoice_series and len(invoice_series) > 10:
            report.results.append(ValidationResult(
                rule_id='FIRS_INV_002',
                field_name='invoice_series',
                severity=ValidationSeverity.WARNING,
                message='Invoice series too long',
                actual_value=invoice_series,
                suggestion='Keep invoice series under 10 characters'
            ))
        
        report.total_checks += 2
    
    async def _validate_dates(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate date information"""
        # Validate invoice date
        invoice_date = document.get('invoice_date')
        if invoice_date:
            await self._validate_date_format(invoice_date, 'invoice_date', report)
        
        # Validate due date
        due_date = document.get('due_date')
        if due_date:
            await self._validate_date_format(due_date, 'due_date', report)
        
        # Validate date consistency
        if invoice_date and due_date:
            await self._validate_date_consistency(invoice_date, due_date, report)
        
        report.total_checks += 3
    
    async def _validate_date_format(self, date_value: str, field_name: str, report: FIRSValidationReport):
        """Validate date format"""
        try:
            parsed_date = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            
            # Check if date is not too far in the future
            if parsed_date > datetime.now() + timedelta(days=365):
                report.results.append(ValidationResult(
                    rule_id='FIRS_DATE_001',
                    field_name=field_name,
                    severity=ValidationSeverity.WARNING,
                    message='Date is too far in the future',
                    actual_value=date_value,
                    suggestion='Check date validity'
                ))
            else:
                report.passed_checks += 1
        except ValueError:
            report.results.append(ValidationResult(
                rule_id='FIRS_DATE_001',
                field_name=field_name,
                severity=ValidationSeverity.ERROR,
                message='Invalid date format',
                actual_value=date_value,
                suggestion='Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'
            ))
    
    async def _validate_date_consistency(self, invoice_date: str, due_date: str, report: FIRSValidationReport):
        """Validate date consistency"""
        try:
            invoice_dt = datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
            due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            
            if due_dt < invoice_dt:
                report.results.append(ValidationResult(
                    rule_id='FIRS_DATE_002',
                    field_name='due_date',
                    severity=ValidationSeverity.ERROR,
                    message='Due date cannot be before invoice date',
                    actual_value=due_date,
                    suggestion='Set due date after invoice date'
                ))
            else:
                report.passed_checks += 1
        except ValueError:
            pass  # Date format errors already handled
    
    async def _validate_items(self, document: Dict[str, Any], report: FIRSValidationReport):
        """Validate invoice items"""
        items = document.get('items', [])
        
        if not items:
            report.results.append(ValidationResult(
                rule_id='FIRS_ITEMS_001',
                field_name='items',
                severity=ValidationSeverity.ERROR,
                message='Invoice must have at least one item'
            ))
        else:
            for i, item in enumerate(items):
                await self._validate_item(item, i, report)
        
        report.total_checks += 1
    
    async def _validate_item(self, item: Dict[str, Any], item_index: int, report: FIRSValidationReport):
        """Validate individual item"""
        field_prefix = f'items[{item_index}]'
        
        # Validate required fields
        required_fields = ['description', 'quantity', 'unit_price', 'total_price']
        for field in required_fields:
            if field not in item or item[field] is None:
                report.results.append(ValidationResult(
                    rule_id='FIRS_ITEM_001',
                    field_name=f'{field_prefix}.{field}',
                    severity=ValidationSeverity.ERROR,
                    message=f'Item {field} is required'
                ))
            else:
                report.passed_checks += 1
        
        # Validate item calculation
        quantity = item.get('quantity')
        unit_price = item.get('unit_price')
        total_price = item.get('total_price')
        
        if quantity is not None and unit_price is not None and total_price is not None:
            try:
                quantity_decimal = Decimal(str(quantity))
                unit_price_decimal = Decimal(str(unit_price))
                total_price_decimal = Decimal(str(total_price))
                
                expected_total = quantity_decimal * unit_price_decimal
                
                if abs(expected_total - total_price_decimal) > Decimal('0.01'):
                    report.results.append(ValidationResult(
                        rule_id='FIRS_ITEM_CALC_001',
                        field_name=f'{field_prefix}.total_price',
                        severity=ValidationSeverity.ERROR,
                        message='Item total price calculation mismatch',
                        expected_value=str(expected_total),
                        actual_value=str(total_price),
                        suggestion='Verify: total_price = quantity * unit_price'
                    ))
                else:
                    report.passed_checks += 1
            except (InvalidOperation, ValueError):
                report.results.append(ValidationResult(
                    rule_id='FIRS_ITEM_CALC_001',
                    field_name=f'{field_prefix}',
                    severity=ValidationSeverity.ERROR,
                    message='Cannot validate item calculation due to invalid format'
                ))
        
        report.total_checks += 5  # Required fields + calculation
    
    def _categorize_results(self, report: FIRSValidationReport):
        """Categorize validation results by severity"""
        for result in report.results:
            if result.severity == ValidationSeverity.ERROR:
                report.errors.append(result)
                report.failed_checks += 1
            elif result.severity == ValidationSeverity.WARNING:
                report.warnings.append(result)
            elif result.severity == ValidationSeverity.INFO:
                report.info.append(result)
            else:  # CRITICAL
                report.errors.append(result)
                report.failed_checks += 1
    
    def get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all validation rules"""
        return self.validation_rules.copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get validation metrics"""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_validations'] / 
                max(self.metrics['total_validations'], 1)
            ) * 100,
            'average_validation_time': (
                self.metrics['validation_time'] / 
                max(self.metrics['total_validations'], 1)
            )
        }


# Factory functions for easy setup
def create_firs_validator() -> FIRSValidator:
    """Create FIRS validator instance"""
    return FIRSValidator()


async def validate_document_for_firs(document: Dict[str, Any]) -> FIRSValidationReport:
    """Validate document for FIRS compliance"""
    validator = create_firs_validator()
    return await validator.validate_document(document)