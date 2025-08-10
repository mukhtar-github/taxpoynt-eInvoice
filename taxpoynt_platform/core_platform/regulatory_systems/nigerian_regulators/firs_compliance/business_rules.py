"""
FIRS Business Rules Engine
=========================
Business rules and regulatory compliance engine for FIRS e-invoicing requirements.
Implements Nigerian tax law business logic and validation rules.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    FIRSBusinessRule, ComplianceLevel, TaxType, InvoiceType,
    VATStatus, TINValidationStatus
)

logger = logging.getLogger(__name__)

class FIRSBusinessRulesEngine:
    """
    FIRS business rules and compliance validation engine
    """
    
    def __init__(self):
        """Initialize FIRS business rules engine"""
        self.logger = logging.getLogger(__name__)
        
        # Load business rules
        self.mandatory_rules = self._load_mandatory_rules()
        self.conditional_rules = self._load_conditional_rules()
        self.validation_rules = self._load_validation_rules()
        self.calculation_rules = self._load_calculation_rules()
        
        # Nigerian regulatory constants
        self.minimum_invoice_amount = Decimal('1.00')
        self.maximum_cash_transaction = Decimal('5000000')  # N5M cash limit
        self.vat_registration_threshold = Decimal('25000000')  # N25M annual turnover
        self.large_transaction_threshold = Decimal('10000000')  # N10M reporting threshold
        
        # Valid Nigerian business registration types
        self.valid_business_types = [
            'RC', 'BN', 'IT', 'LLP', 'PLC', 'LTD', 'NGO', 'ASSOC'
        ]
        
    def validate_business_rules(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice against FIRS business rules
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Dictionary with business rule validation results
        """
        try:
            self.logger.info(f"Validating business rules for invoice: {invoice_data.get('invoice_number', 'Unknown')}")
            
            validation_result = {
                'is_compliant': True,
                'compliance_level': ComplianceLevel.COMPLIANT,
                'passed_rules': [],
                'failed_rules': [],
                'warnings': [],
                'errors': [],
                'rule_violations': [],
                'recommendations': []
            }
            
            # Apply mandatory rules
            self._apply_mandatory_rules(invoice_data, validation_result)
            
            # Apply conditional rules
            self._apply_conditional_rules(invoice_data, validation_result)
            
            # Apply validation rules
            self._apply_validation_rules(invoice_data, validation_result)
            
            # Apply calculation rules
            self._apply_calculation_rules(invoice_data, validation_result)
            
            # Determine final compliance status
            validation_result = self._determine_final_compliance(validation_result)
            
            self.logger.info(f"Business rules validation completed. Compliance: {validation_result['is_compliant']}")
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Business rules validation failed: {str(e)}")
            return {
                'is_compliant': False,
                'compliance_level': ComplianceLevel.CRITICAL_VIOLATION,
                'errors': [f"Business rules validation error: {str(e)}"],
                'passed_rules': [],
                'failed_rules': [],
                'warnings': [],
                'rule_violations': [],
                'recommendations': []
            }
    
    def validate_tin_business_rules(self, tin: str, entity_type: str = "company") -> Dict[str, Any]:
        """
        Validate TIN against business rules
        
        Args:
            tin: Tax Identification Number
            entity_type: Type of entity (company, individual, non_resident)
            
        Returns:
            Dictionary with TIN business rule validation
        """
        try:
            validation_result = {
                'is_valid': True,
                'rule_violations': [],
                'warnings': []
            }
            
            # TIN format validation
            if not self._validate_tin_format_business_rule(tin):
                validation_result['is_valid'] = False
                validation_result['rule_violations'].append({
                    'rule': 'TIN_FORMAT_001',
                    'message': 'TIN must be 14 digits',
                    'severity': 'error'
                })
            
            # TIN check digit validation
            if not self._validate_tin_check_digit(tin):
                validation_result['warnings'].append({
                    'rule': 'TIN_CHECK_001',
                    'message': 'TIN check digit validation failed',
                    'severity': 'warning'
                })
            
            # Entity type consistency
            if not self._validate_tin_entity_consistency(tin, entity_type):
                validation_result['warnings'].append({
                    'rule': 'TIN_ENTITY_001',
                    'message': f'TIN may not be consistent with entity type: {entity_type}',
                    'severity': 'warning'
                })
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"TIN business rules validation failed: {str(e)}")
            return {
                'is_valid': False,
                'rule_violations': [{'rule': 'TIN_ERROR', 'message': str(e), 'severity': 'error'}],
                'warnings': []
            }
    
    def validate_transaction_limits(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate transaction against Nigerian regulatory limits
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Dictionary with transaction limit validation
        """
        try:
            total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
            payment_method = invoice_data.get('payment_method', '').lower()
            
            validation_result = {
                'is_compliant': True,
                'violations': [],
                'warnings': [],
                'reporting_requirements': []
            }
            
            # Cash transaction limits
            if payment_method == 'cash' and total_amount > self.maximum_cash_transaction:
                validation_result['is_compliant'] = False
                validation_result['violations'].append({
                    'rule': 'CASH_LIMIT_001',
                    'message': f'Cash transaction exceeds limit of ₦{self.maximum_cash_transaction:,}',
                    'amount': total_amount,
                    'limit': self.maximum_cash_transaction
                })
            
            # Large transaction reporting
            if total_amount >= self.large_transaction_threshold:
                validation_result['reporting_requirements'].append({
                    'requirement': 'LARGE_TRANSACTION_REPORT',
                    'message': f'Transaction above ₦{self.large_transaction_threshold:,} requires additional reporting',
                    'amount': total_amount
                })
            
            # Minimum invoice amount
            if total_amount < self.minimum_invoice_amount:
                validation_result['warnings'].append({
                    'rule': 'MIN_AMOUNT_001',
                    'message': f'Invoice amount below recommended minimum of ₦{self.minimum_invoice_amount}',
                    'amount': total_amount
                })
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Transaction limits validation failed: {str(e)}")
            return {
                'is_compliant': False,
                'violations': [{'rule': 'LIMIT_ERROR', 'message': str(e)}],
                'warnings': [],
                'reporting_requirements': []
            }
    
    def validate_vat_business_rules(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate VAT application business rules
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Dictionary with VAT business rule validation
        """
        try:
            validation_result = {
                'is_compliant': True,
                'vat_applicable': True,
                'exemption_applicable': False,
                'zero_rating_applicable': False,
                'violations': [],
                'recommendations': []
            }
            
            supplier_tin = invoice_data.get('supplier_tin', '')
            customer_location = invoice_data.get('customer_country', 'NG').upper()
            item_description = invoice_data.get('description', '').lower()
            customer_type = invoice_data.get('customer_type', 'individual').lower()
            
            # Check VAT registration requirement
            annual_turnover = Decimal(str(invoice_data.get('annual_turnover', 0)))
            if annual_turnover >= self.vat_registration_threshold:
                if not self._is_vat_registered(supplier_tin):
                    validation_result['violations'].append({
                        'rule': 'VAT_REG_001',
                        'message': f'VAT registration required for turnover above ₦{self.vat_registration_threshold:,}',
                        'turnover': annual_turnover
                    })
            
            # Check export zero-rating
            if customer_location != 'NG':
                validation_result['zero_rating_applicable'] = True
                validation_result['recommendations'].append({
                    'rule': 'VAT_EXPORT_001',
                    'message': 'Export transaction may qualify for VAT zero-rating',
                    'details': 'Ensure proper export documentation'
                })
            
            # Check VAT exemptions
            if self._is_vat_exempt_service(item_description, customer_type):
                validation_result['exemption_applicable'] = True
                validation_result['vat_applicable'] = False
                validation_result['recommendations'].append({
                    'rule': 'VAT_EXEMPT_001',
                    'message': 'Service may qualify for VAT exemption',
                    'service_type': item_description
                })
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"VAT business rules validation failed: {str(e)}")
            return {
                'is_compliant': False,
                'violations': [{'rule': 'VAT_ERROR', 'message': str(e)}],
                'vat_applicable': True,
                'exemption_applicable': False,
                'zero_rating_applicable': False,
                'recommendations': []
            }
    
    def check_withholding_tax_applicability(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check withholding tax applicability based on business rules
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Dictionary with WHT applicability assessment
        """
        try:
            service_type = invoice_data.get('service_category', '').lower()
            payer_type = invoice_data.get('customer_type', 'individual').lower()
            payee_type = invoice_data.get('supplier_type', 'company').lower()
            amount = Decimal(str(invoice_data.get('subtotal', 0)))
            
            wht_result = {
                'is_applicable': False,
                'wht_rate': Decimal('0'),
                'exemption_reason': None,
                'business_rule': None,
                'recommendations': []
            }
            
            # WHT applicability matrix
            if payer_type in ['company', 'government'] and payee_type in ['individual', 'company']:
                if service_type in ['professional', 'technical', 'consultancy', 'construction']:
                    wht_result['is_applicable'] = True
                    wht_result['wht_rate'] = Decimal('5.0')
                    wht_result['business_rule'] = 'WHT_SERVICE_001'
                elif service_type in ['rent', 'interest', 'dividend']:
                    wht_result['is_applicable'] = True
                    wht_result['wht_rate'] = Decimal('10.0')
                    wht_result['business_rule'] = 'WHT_INVESTMENT_001'
            
            # Small amount exemption
            if amount < Decimal('1000000'):  # N1M threshold
                if wht_result['is_applicable']:
                    wht_result['recommendations'].append({
                        'rule': 'WHT_SMALL_001',
                        'message': 'Consider small amount WHT exemption policy',
                        'amount': amount
                    })
            
            return wht_result
            
        except Exception as e:
            self.logger.error(f"WHT applicability check failed: {str(e)}")
            return {
                'is_applicable': False,
                'wht_rate': Decimal('0'),
                'exemption_reason': f'Error: {str(e)}',
                'business_rule': None,
                'recommendations': []
            }
    
    # Private helper methods
    
    def _load_mandatory_rules(self) -> List[Dict[str, Any]]:
        """Load mandatory business rules"""
        return [
            {
                'rule_id': 'MAND_001',
                'name': 'Invoice Number Required',
                'field': 'invoice_number',
                'validation': 'required',
                'error_message': 'Invoice number is mandatory'
            },
            {
                'rule_id': 'MAND_002',
                'name': 'Invoice Date Required',
                'field': 'invoice_date',
                'validation': 'required',
                'error_message': 'Invoice date is mandatory'
            },
            {
                'rule_id': 'MAND_003',
                'name': 'Supplier TIN Required',
                'field': 'supplier_tin',
                'validation': 'required',
                'error_message': 'Supplier TIN is mandatory'
            },
            {
                'rule_id': 'MAND_004',
                'name': 'Supplier Name Required',
                'field': 'supplier_name',
                'validation': 'required',
                'error_message': 'Supplier name is mandatory'
            },
            {
                'rule_id': 'MAND_005',
                'name': 'Customer Information Required',
                'field': 'customer_name',
                'validation': 'required',
                'error_message': 'Customer name is mandatory'
            },
            {
                'rule_id': 'MAND_006',
                'name': 'Amount Fields Required',
                'fields': ['subtotal', 'total_amount'],
                'validation': 'required_numeric',
                'error_message': 'Amount fields are mandatory and must be numeric'
            },
            {
                'rule_id': 'MAND_007',
                'name': 'Currency Required',
                'field': 'currency',
                'validation': 'required',
                'expected_value': 'NGN',
                'error_message': 'Currency must be specified as NGN'
            }
        ]
    
    def _load_conditional_rules(self) -> List[Dict[str, Any]]:
        """Load conditional business rules"""
        return [
            {
                'rule_id': 'COND_001',
                'name': 'Customer TIN for B2B',
                'condition': 'customer_type == "company"',
                'field': 'customer_tin',
                'validation': 'required',
                'error_message': 'Customer TIN required for business customers'
            },
            {
                'rule_id': 'COND_002',
                'name': 'VAT Amount for Taxable Supply',
                'condition': 'vat_applicable == True',
                'field': 'vat_amount',
                'validation': 'required_positive',
                'error_message': 'VAT amount required for taxable supplies'
            },
            {
                'rule_id': 'COND_003',
                'name': 'Export Documentation',
                'condition': 'customer_country != "NG"',
                'fields': ['export_permit', 'shipping_document'],
                'validation': 'recommended',
                'error_message': 'Export documentation recommended for foreign customers'
            }
        ]
    
    def _load_validation_rules(self) -> List[Dict[str, Any]]:
        """Load validation business rules"""
        return [
            {
                'rule_id': 'VAL_001',
                'name': 'Invoice Date Validity',
                'field': 'invoice_date',
                'validation': 'date_range',
                'min_date': 'today - 12 months',
                'max_date': 'today + 30 days',
                'error_message': 'Invoice date must be within valid range'
            },
            {
                'rule_id': 'VAL_002',
                'name': 'TIN Format Validation',
                'field': 'supplier_tin',
                'validation': 'regex',
                'pattern': r'^\d{14}$',
                'error_message': 'TIN must be 14 digits'
            },
            {
                'rule_id': 'VAL_003',
                'name': 'Amount Precision',
                'fields': ['subtotal', 'vat_amount', 'total_amount'],
                'validation': 'decimal_places',
                'max_places': 2,
                'error_message': 'Amounts must have maximum 2 decimal places'
            },
            {
                'rule_id': 'VAL_004',
                'name': 'Positive Amount Validation',
                'fields': ['subtotal', 'total_amount'],
                'validation': 'positive',
                'error_message': 'Amounts must be positive'
            }
        ]
    
    def _load_calculation_rules(self) -> List[Dict[str, Any]]:
        """Load calculation validation rules"""
        return [
            {
                'rule_id': 'CALC_001',
                'name': 'VAT Calculation Accuracy',
                'validation': 'vat_calculation',
                'tolerance': Decimal('0.01'),
                'error_message': 'VAT calculation must be accurate'
            },
            {
                'rule_id': 'CALC_002',
                'name': 'Total Amount Calculation',
                'validation': 'total_calculation',
                'formula': 'subtotal + vat_amount + other_charges - discounts',
                'tolerance': Decimal('0.01'),
                'error_message': 'Total amount calculation must be accurate'
            },
            {
                'rule_id': 'CALC_003',
                'name': 'WHT Calculation Check',
                'validation': 'wht_calculation',
                'tolerance': Decimal('0.01'),
                'error_message': 'Withholding tax calculation should be verified'
            }
        ]
    
    def _apply_mandatory_rules(self, invoice_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply mandatory business rules"""
        for rule in self.mandatory_rules:
            try:
                if 'field' in rule:
                    field_value = invoice_data.get(rule['field'])
                    if not field_value or (isinstance(field_value, str) and not field_value.strip()):
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(rule['error_message'])
                        result['rule_violations'].append({
                            'rule_id': rule['rule_id'],
                            'rule_name': rule['name'],
                            'field': rule['field'],
                            'message': rule['error_message'],
                            'severity': 'error'
                        })
                    else:
                        # Additional validation for expected values
                        if 'expected_value' in rule and field_value != rule['expected_value']:
                            result['failed_rules'].append(rule['rule_id'])
                            result['errors'].append(f"{rule['error_message']} (Expected: {rule['expected_value']}, Got: {field_value})")
                        else:
                            result['passed_rules'].append(rule['rule_id'])
                
                elif 'fields' in rule:
                    missing_fields = []
                    for field in rule['fields']:
                        field_value = invoice_data.get(field)
                        if not field_value or (rule['validation'] == 'required_numeric' and not self._is_numeric(field_value)):
                            missing_fields.append(field)
                    
                    if missing_fields:
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(f"{rule['error_message']} (Missing: {', '.join(missing_fields)})")
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                        
            except Exception as e:
                result['errors'].append(f"Rule {rule['rule_id']} validation error: {str(e)}")
    
    def _apply_conditional_rules(self, invoice_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply conditional business rules"""
        for rule in self.conditional_rules:
            try:
                if self._evaluate_condition(rule['condition'], invoice_data):
                    if 'field' in rule:
                        field_value = invoice_data.get(rule['field'])
                        if rule['validation'] == 'required' and not field_value:
                            result['failed_rules'].append(rule['rule_id'])
                            result['errors'].append(rule['error_message'])
                        elif rule['validation'] == 'required_positive' and (not field_value or Decimal(str(field_value)) <= 0):
                            result['failed_rules'].append(rule['rule_id'])
                            result['errors'].append(rule['error_message'])
                        else:
                            result['passed_rules'].append(rule['rule_id'])
                    
                    elif 'fields' in rule and rule['validation'] == 'recommended':
                        missing_fields = [field for field in rule['fields'] if not invoice_data.get(field)]
                        if missing_fields:
                            result['warnings'].append(f"{rule['error_message']} (Missing: {', '.join(missing_fields)})")
                        else:
                            result['passed_rules'].append(rule['rule_id'])
                            
            except Exception as e:
                result['warnings'].append(f"Conditional rule {rule['rule_id']} evaluation error: {str(e)}")
    
    def _apply_validation_rules(self, invoice_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply validation business rules"""
        for rule in self.validation_rules:
            try:
                if rule['validation'] == 'date_range':
                    date_value = invoice_data.get(rule['field'])
                    if date_value and not self._validate_date_range(date_value, rule):
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(rule['error_message'])
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                
                elif rule['validation'] == 'regex':
                    field_value = str(invoice_data.get(rule['field'], ''))
                    if field_value and not re.match(rule['pattern'], field_value):
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(rule['error_message'])
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                
                elif rule['validation'] == 'decimal_places':
                    for field in rule['fields']:
                        field_value = invoice_data.get(field)
                        if field_value and not self._validate_decimal_places(field_value, rule['max_places']):
                            result['failed_rules'].append(rule['rule_id'])
                            result['errors'].append(f"{rule['error_message']} (Field: {field})")
                            break
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                
                elif rule['validation'] == 'positive':
                    for field in rule['fields']:
                        field_value = invoice_data.get(field)
                        if field_value and Decimal(str(field_value)) <= 0:
                            result['failed_rules'].append(rule['rule_id'])
                            result['errors'].append(f"{rule['error_message']} (Field: {field})")
                            break
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                        
            except Exception as e:
                result['warnings'].append(f"Validation rule {rule['rule_id']} error: {str(e)}")
    
    def _apply_calculation_rules(self, invoice_data: Dict[str, Any], result: Dict[str, Any]):
        """Apply calculation validation rules"""
        for rule in self.calculation_rules:
            try:
                if rule['validation'] == 'vat_calculation':
                    if not self._validate_vat_calculation_rule(invoice_data, rule['tolerance']):
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(rule['error_message'])
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                
                elif rule['validation'] == 'total_calculation':
                    if not self._validate_total_calculation_rule(invoice_data, rule['tolerance']):
                        result['failed_rules'].append(rule['rule_id'])
                        result['errors'].append(rule['error_message'])
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                
                elif rule['validation'] == 'wht_calculation':
                    wht_validation = self._validate_wht_calculation_rule(invoice_data, rule['tolerance'])
                    if not wht_validation['is_valid']:
                        result['warnings'].append(f"{rule['error_message']}: {wht_validation['message']}")
                    else:
                        result['passed_rules'].append(rule['rule_id'])
                        
            except Exception as e:
                result['warnings'].append(f"Calculation rule {rule['rule_id']} error: {str(e)}")
    
    def _determine_final_compliance(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final compliance status"""
        if result['errors']:
            result['is_compliant'] = False
            if len(result['errors']) > 5:
                result['compliance_level'] = ComplianceLevel.CRITICAL_VIOLATION
            else:
                result['compliance_level'] = ComplianceLevel.NON_COMPLIANT
        elif result['warnings']:
            result['compliance_level'] = ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            result['compliance_level'] = ComplianceLevel.COMPLIANT
        
        # Generate recommendations
        if result['errors']:
            result['recommendations'].append("Address all errors before invoice submission")
        if result['warnings']:
            result['recommendations'].append("Review and resolve warnings for full compliance")
        
        return result
    
    # Helper validation methods
    
    def _validate_tin_format_business_rule(self, tin: str) -> bool:
        """Validate TIN format according to business rules"""
        return bool(tin and len(tin) == 14 and tin.isdigit())
    
    def _validate_tin_check_digit(self, tin: str) -> bool:
        """Validate TIN check digit (simplified algorithm)"""
        if len(tin) != 14:
            return False
        
        # Simplified check digit validation
        # Real implementation would use FIRS algorithm
        weights = [2, 7, 6, 5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        total = sum(int(tin[i]) * weights[i] for i in range(13))
        check_digit = (11 - (total % 11)) % 11
        
        return int(tin[13]) == check_digit
    
    def _validate_tin_entity_consistency(self, tin: str, entity_type: str) -> bool:
        """Validate TIN consistency with entity type"""
        # Simplified validation - real implementation would check TIN prefix
        if entity_type == 'individual':
            return tin.startswith(('1', '2', '3'))
        elif entity_type == 'company':
            return tin.startswith(('4', '5', '6', '7', '8', '9'))
        return True
    
    def _is_vat_registered(self, tin: str) -> bool:
        """Check if entity is VAT registered (placeholder)"""
        # This would integrate with FIRS VAT registry
        return True  # Assume registered for now
    
    def _is_vat_exempt_service(self, service_description: str, customer_type: str) -> bool:
        """Check if service qualifies for VAT exemption"""
        exempt_services = [
            'medical', 'healthcare', 'hospital', 'education', 'school',
            'pharmaceutical', 'medicine', 'agricultural', 'export'
        ]
        
        return any(exempt_service in service_description for exempt_service in exempt_services)
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric"""
        try:
            Decimal(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate conditional rule (simplified)"""
        # In production, use a proper expression evaluator
        try:
            if 'customer_type == "company"' in condition:
                return data.get('customer_type', '').lower() == 'company'
            elif 'vat_applicable == True' in condition:
                return data.get('vat_applicable', True)
            elif 'customer_country != "NG"' in condition:
                return data.get('customer_country', 'NG').upper() != 'NG'
            return False
        except:
            return False
    
    def _validate_date_range(self, date_value: Any, rule: Dict[str, Any]) -> bool:
        """Validate date is within acceptable range"""
        try:
            if isinstance(date_value, str):
                invoice_date = datetime.strptime(date_value, '%Y-%m-%d').date()
            elif isinstance(date_value, datetime):
                invoice_date = date_value.date()
            elif isinstance(date_value, date):
                invoice_date = date_value
            else:
                return False
            
            today = date.today()
            min_date = today - timedelta(days=365)  # 12 months ago
            max_date = today + timedelta(days=30)   # 30 days in future
            
            return min_date <= invoice_date <= max_date
        except:
            return False
    
    def _validate_decimal_places(self, value: Any, max_places: int) -> bool:
        """Validate decimal places"""
        try:
            decimal_value = Decimal(str(value))
            return abs(decimal_value.as_tuple().exponent) <= max_places
        except:
            return False
    
    def _validate_vat_calculation_rule(self, data: Dict[str, Any], tolerance: Decimal) -> bool:
        """Validate VAT calculation accuracy"""
        try:
            subtotal = Decimal(str(data.get('subtotal', 0)))
            vat_amount = Decimal(str(data.get('vat_amount', 0)))
            vat_rate = Decimal('7.5')  # Nigerian VAT rate
            
            expected_vat = subtotal * (vat_rate / 100)
            return abs(vat_amount - expected_vat) <= tolerance
        except:
            return False
    
    def _validate_total_calculation_rule(self, data: Dict[str, Any], tolerance: Decimal) -> bool:
        """Validate total amount calculation"""
        try:
            subtotal = Decimal(str(data.get('subtotal', 0)))
            vat_amount = Decimal(str(data.get('vat_amount', 0)))
            total_amount = Decimal(str(data.get('total_amount', 0)))
            other_charges = Decimal(str(data.get('other_charges', 0)))
            discounts = Decimal(str(data.get('discounts', 0)))
            
            expected_total = subtotal + vat_amount + other_charges - discounts
            return abs(total_amount - expected_total) <= tolerance
        except:
            return False
    
    def _validate_wht_calculation_rule(self, data: Dict[str, Any], tolerance: Decimal) -> Dict[str, Any]:
        """Validate WHT calculation (advisory)"""
        try:
            wht_amount = Decimal(str(data.get('withholding_tax', 0)))
            
            # If no WHT claimed, that's acceptable
            if wht_amount == 0:
                return {'is_valid': True, 'message': 'No WHT applied'}
            
            # Basic validation - would need more sophisticated logic
            subtotal = Decimal(str(data.get('subtotal', 0)))
            service_type = data.get('service_category', '').lower()
            
            if 'professional' in service_type and wht_amount > 0:
                expected_wht = subtotal * Decimal('0.05')  # 5% rate
                if abs(wht_amount - expected_wht) <= tolerance:
                    return {'is_valid': True, 'message': 'WHT calculation appears correct'}
                else:
                    return {'is_valid': False, 'message': f'WHT calculation may be incorrect. Expected: ₦{expected_wht}, Actual: ₦{wht_amount}'}
            
            return {'is_valid': True, 'message': 'WHT validation passed'}
            
        except Exception as e:
            return {'is_valid': False, 'message': f'WHT validation error: {str(e)}'}