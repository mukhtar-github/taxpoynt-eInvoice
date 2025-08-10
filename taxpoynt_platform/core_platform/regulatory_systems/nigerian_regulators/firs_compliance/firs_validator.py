"""
FIRS Compliance Validator
========================
Comprehensive validator for FIRS (Federal Inland Revenue Service) e-invoicing compliance
with Nigerian tax regulations and business rules validation.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from decimal import Decimal

from .models import (
    FIRSValidationResult, NigerianTaxInfo, VATCalculation, TINValidationResult,
    FIRSComplianceStatus, EInvoiceSubmission, ComplianceLevel, TINValidationStatus,
    VATStatus, InvoiceType, TaxType, SubmissionStatus, FIRSBusinessRule
)

logger = logging.getLogger(__name__)

class FIRSValidator:
    """
    Comprehensive FIRS compliance validator for Nigerian e-invoicing requirements
    """
    
    def __init__(self):
        """Initialize FIRS validator with Nigerian tax rules"""
        self.logger = logging.getLogger(__name__)
        self.validation_rules = self._load_firs_business_rules()
        self.tax_offices = self._load_tax_office_codes()
        self.vat_rate = Decimal('7.5')  # Current Nigerian VAT rate
        self.wht_rates = self._load_withholding_tax_rates()
        
    def validate_invoice_compliance(self, invoice_data: Dict[str, Any]) -> FIRSValidationResult:
        """
        Validate invoice for FIRS compliance
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            FIRSValidationResult with detailed compliance assessment
        """
        try:
            self.logger.info(f"Starting FIRS compliance validation for invoice: {invoice_data.get('invoice_number', 'Unknown')}")
            
            # Initialize validation result
            result = FIRSValidationResult(
                is_compliant=True,
                compliance_level=ComplianceLevel.COMPLIANT,
                tin_validation=self._validate_tin_placeholder(),
                compliance_score=0.0
            )
            
            # Extract tax information
            tax_info = self._extract_tax_information(invoice_data)
            
            # Perform validation checks
            self._validate_mandatory_fields(invoice_data, result)
            self._validate_tin_information(tax_info, result)
            self._validate_vat_calculations(invoice_data, result)
            self._validate_business_rules(invoice_data, result)
            self._validate_invoice_format(invoice_data, result)
            self._validate_tax_office_requirements(tax_info, result)
            
            # Calculate compliance score
            result.compliance_score = self._calculate_compliance_score(result)
            
            # Determine final compliance status
            result.compliance_level = self._determine_compliance_level(result)
            result.is_compliant = result.compliance_level in [ComplianceLevel.COMPLIANT, ComplianceLevel.PARTIALLY_COMPLIANT]
            
            # Generate recommendations
            result.recommendations = self._generate_compliance_recommendations(result)
            
            self.logger.info(f"FIRS validation completed. Compliance score: {result.compliance_score}")
            return result
            
        except Exception as e:
            self.logger.error(f"FIRS validation failed: {str(e)}")
            return FIRSValidationResult(
                is_compliant=False,
                compliance_level=ComplianceLevel.CRITICAL_VIOLATION,
                tin_validation=self._validate_tin_placeholder(),
                errors=[f"Validation system error: {str(e)}"],
                compliance_score=0.0
            )
    
    def validate_tin(self, tin: str) -> TINValidationResult:
        """
        Validate Nigerian Tax Identification Number
        
        Args:
            tin: Tax Identification Number to validate
            
        Returns:
            TINValidationResult with validation details
        """
        try:
            self.logger.info(f"Validating TIN: {tin}")
            
            # Format validation
            if not self._validate_tin_format(tin):
                return TINValidationResult(
                    tin=tin,
                    is_valid=False,
                    status=TINValidationStatus.FORMAT_ERROR,
                    error_message="Invalid TIN format. Nigerian TIN must be 14 digits."
                )
            
            # Check TIN registry (placeholder for actual FIRS integration)
            registry_result = self._check_tin_registry(tin)
            
            return TINValidationResult(
                tin=tin,
                is_valid=registry_result['is_valid'],
                status=registry_result['status'],
                taxpayer_name=registry_result.get('taxpayer_name'),
                registration_date=registry_result.get('registration_date'),
                tax_office=registry_result.get('tax_office'),
                error_message=registry_result.get('error_message')
            )
            
        except Exception as e:
            self.logger.error(f"TIN validation failed: {str(e)}")
            return TINValidationResult(
                tin=tin,
                is_valid=False,
                status=TINValidationStatus.INVALID,
                error_message=f"TIN validation error: {str(e)}"
            )
    
    def calculate_nigerian_vat(self, amount: Decimal, is_vat_exempt: bool = False) -> VATCalculation:
        """
        Calculate Nigerian VAT according to FIRS rules
        
        Args:
            amount: Amount before VAT
            is_vat_exempt: VAT exemption status
            
        Returns:
            VATCalculation with detailed calculation
        """
        try:
            if is_vat_exempt:
                return VATCalculation(
                    amount_before_vat=amount,
                    vat_rate=Decimal('0'),
                    vat_amount=Decimal('0'),
                    total_amount=amount,
                    vat_status=VATStatus.EXEMPT,
                    is_vat_exempt=True
                )
            
            vat_amount = amount * (self.vat_rate / 100)
            total_amount = amount + vat_amount
            
            return VATCalculation(
                amount_before_vat=amount,
                vat_rate=self.vat_rate,
                vat_amount=vat_amount,
                total_amount=total_amount,
                vat_status=VATStatus.REGISTERED,
                is_vat_exempt=False
            )
            
        except Exception as e:
            self.logger.error(f"VAT calculation failed: {str(e)}")
            raise ValueError(f"VAT calculation error: {str(e)}")
    
    def validate_withholding_tax(self, amount: Decimal, service_type: str) -> Dict[str, Any]:
        """
        Validate withholding tax calculation according to Nigerian tax laws
        
        Args:
            amount: Service amount
            service_type: Type of service for WHT determination
            
        Returns:
            Dictionary with WHT validation results
        """
        try:
            wht_rate = self.wht_rates.get(service_type.lower(), Decimal('0'))
            
            if wht_rate > 0:
                wht_amount = amount * (wht_rate / 100)
                return {
                    'is_applicable': True,
                    'wht_rate': wht_rate,
                    'wht_amount': wht_amount,
                    'service_type': service_type,
                    'amount_after_wht': amount - wht_amount
                }
            
            return {
                'is_applicable': False,
                'wht_rate': Decimal('0'),
                'wht_amount': Decimal('0'),
                'service_type': service_type,
                'amount_after_wht': amount
            }
            
        except Exception as e:
            self.logger.error(f"WHT validation failed: {str(e)}")
            raise ValueError(f"WHT validation error: {str(e)}")
    
    def assess_compliance_status(self, entity_tin: str, assessment_period: str) -> FIRSComplianceStatus:
        """
        Assess overall FIRS compliance status for an entity
        
        Args:
            entity_tin: Entity TIN
            assessment_period: Assessment period (YYYY-MM)
            
        Returns:
            FIRSComplianceStatus with comprehensive compliance assessment
        """
        try:
            self.logger.info(f"Assessing FIRS compliance for TIN: {entity_tin}, Period: {assessment_period}")
            
            # Get entity submission history (placeholder for actual data retrieval)
            submission_data = self._get_entity_submission_history(entity_tin, assessment_period)
            
            # Calculate metrics
            total_submissions = submission_data['total_invoices_submitted']
            successful = submission_data['successful_submissions']
            rejected = submission_data['rejected_submissions']
            pending = submission_data['pending_submissions']
            
            success_rate = (successful / total_submissions * 100) if total_submissions > 0 else 0
            
            # Determine compliance level
            if success_rate >= 95:
                compliance_level = ComplianceLevel.COMPLIANT
            elif success_rate >= 80:
                compliance_level = ComplianceLevel.PARTIALLY_COMPLIANT
            elif success_rate >= 60:
                compliance_level = ComplianceLevel.REQUIRES_REVIEW
            else:
                compliance_level = ComplianceLevel.NON_COMPLIANT
            
            # Risk assessment
            risk_level, risk_factors = self._assess_compliance_risk(submission_data)
            
            return FIRSComplianceStatus(
                entity_tin=entity_tin,
                entity_name=submission_data.get('entity_name', 'Unknown'),
                compliance_level=compliance_level,
                last_assessment_date=datetime.now(),
                total_invoices_submitted=total_submissions,
                successful_submissions=successful,
                rejected_submissions=rejected,
                pending_submissions=pending,
                submission_success_rate=success_rate,
                average_processing_time=submission_data.get('avg_processing_time'),
                compliance_score=self._calculate_entity_compliance_score(submission_data),
                risk_level=risk_level,
                risk_factors=risk_factors,
                required_actions=self._generate_required_actions(compliance_level, submission_data),
                recommendations=self._generate_entity_recommendations(submission_data)
            )
            
        except Exception as e:
            self.logger.error(f"Compliance status assessment failed: {str(e)}")
            raise ValueError(f"Compliance assessment error: {str(e)}")
    
    # Private helper methods
    
    def _load_firs_business_rules(self) -> List[FIRSBusinessRule]:
        """Load FIRS business rules"""
        return [
            FIRSBusinessRule(
                rule_code="FIRS-001",
                rule_category="TIN_VALIDATION",
                rule_description="Supplier TIN must be valid and active",
                validation_logic="validate_tin_format_and_status",
                error_message="Supplier TIN is invalid or inactive",
                effective_date=date(2020, 1, 1)
            ),
            FIRSBusinessRule(
                rule_code="FIRS-002",
                rule_category="VAT_CALCULATION",
                rule_description="VAT calculation must be accurate (7.5%)",
                validation_logic="validate_vat_calculation_accuracy",
                error_message="VAT calculation is incorrect",
                effective_date=date(2020, 2, 1)
            ),
            FIRSBusinessRule(
                rule_code="FIRS-003",
                rule_category="INVOICE_FORMAT",
                rule_description="Invoice must contain all mandatory fields",
                validation_logic="validate_mandatory_invoice_fields",
                error_message="Invoice missing mandatory fields",
                effective_date=date(2020, 1, 1)
            ),
            FIRSBusinessRule(
                rule_code="FIRS-004",
                rule_category="CURRENCY",
                rule_description="Invoices must be in Nigerian Naira (NGN)",
                validation_logic="validate_currency_ngn",
                error_message="Invoice currency must be NGN",
                effective_date=date(2020, 1, 1)
            )
        ]
    
    def _load_tax_office_codes(self) -> Dict[str, str]:
        """Load Nigerian tax office codes"""
        return {
            'LAG001': 'Lagos Island Tax Office',
            'LAG002': 'Victoria Island Tax Office',
            'LAG003': 'Ikeja Tax Office',
            'ABJ001': 'Abuja Central Tax Office',
            'ABJ002': 'Garki Tax Office',
            'KAN001': 'Kano Central Tax Office',
            'PHC001': 'Port Harcourt Tax Office',
            'IBD001': 'Ibadan Tax Office',
            'BEN001': 'Benin Tax Office',
            'JOS001': 'Jos Tax Office'
        }
    
    def _load_withholding_tax_rates(self) -> Dict[str, Decimal]:
        """Load Nigerian withholding tax rates"""
        return {
            'professional_services': Decimal('5.0'),
            'technical_services': Decimal('5.0'),
            'management_services': Decimal('5.0'),
            'consultancy': Decimal('5.0'),
            'rent': Decimal('10.0'),
            'interest': Decimal('10.0'),
            'royalty': Decimal('10.0'),
            'commission': Decimal('5.0'),
            'construction': Decimal('5.0'),
            'haulage': Decimal('5.0'),
            'dividend': Decimal('10.0')
        }
    
    def _extract_tax_information(self, invoice_data: Dict[str, Any]) -> NigerianTaxInfo:
        """Extract tax information from invoice data"""
        return NigerianTaxInfo(
            supplier_tin=invoice_data.get('supplier_tin', ''),
            customer_tin=invoice_data.get('customer_tin'),
            tax_office_code=invoice_data.get('tax_office_code', 'LAG001'),
            vat_calculation=VATCalculation(
                amount_before_vat=Decimal(str(invoice_data.get('subtotal', 0))),
                vat_rate=Decimal(str(invoice_data.get('vat_rate', 7.5))),
                vat_amount=Decimal(str(invoice_data.get('vat_amount', 0))),
                total_amount=Decimal(str(invoice_data.get('total_amount', 0))),
                vat_status=VATStatus.REGISTERED
            ),
            withholding_tax=Decimal(str(invoice_data.get('withholding_tax', 0))) if invoice_data.get('withholding_tax') else None,
            stamp_duty=Decimal(str(invoice_data.get('stamp_duty', 0))) if invoice_data.get('stamp_duty') else None,
            currency_code=invoice_data.get('currency', 'NGN'),
            tax_period=invoice_data.get('tax_period', datetime.now().strftime('%Y-%m'))
        )
    
    def _validate_mandatory_fields(self, invoice_data: Dict[str, Any], result: FIRSValidationResult):
        """Validate mandatory invoice fields"""
        mandatory_fields = [
            'invoice_number', 'invoice_date', 'supplier_tin', 'supplier_name',
            'customer_name', 'subtotal', 'vat_amount', 'total_amount', 'currency'
        ]
        
        for field in mandatory_fields:
            if not invoice_data.get(field):
                result.failed_rules.append(f"FIRS-003: Missing mandatory field '{field}'")
                result.errors.append(f"Invoice must contain '{field}' field")
            else:
                result.passed_rules.append(f"FIRS-003: Field '{field}' present")
    
    def _validate_tin_information(self, tax_info: NigerianTaxInfo, result: FIRSValidationResult):
        """Validate TIN information"""
        tin_result = self.validate_tin(tax_info.supplier_tin)
        result.tin_validation = tin_result
        
        if tin_result.is_valid:
            result.passed_rules.append("FIRS-001: Supplier TIN is valid")
        else:
            result.failed_rules.append("FIRS-001: Supplier TIN validation failed")
            result.errors.append(tin_result.error_message or "Invalid supplier TIN")
    
    def _validate_vat_calculations(self, invoice_data: Dict[str, Any], result: FIRSValidationResult):
        """Validate VAT calculations"""
        try:
            subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
            vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
            total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
            
            # Calculate expected VAT
            expected_vat = subtotal * (self.vat_rate / 100)
            expected_total = subtotal + expected_vat
            
            # Check VAT calculation accuracy
            if abs(vat_amount - expected_vat) <= Decimal('0.01'):
                result.passed_rules.append("FIRS-002: VAT calculation is correct")
            else:
                result.failed_rules.append("FIRS-002: VAT calculation is incorrect")
                result.errors.append(f"Expected VAT: {expected_vat}, Actual: {vat_amount}")
            
            # Check total calculation
            if abs(total_amount - expected_total) <= Decimal('0.01'):
                result.passed_rules.append("FIRS-002: Total amount calculation is correct")
            else:
                result.failed_rules.append("FIRS-002: Total amount calculation is incorrect")
                result.errors.append(f"Expected total: {expected_total}, Actual: {total_amount}")
                
        except Exception as e:
            result.failed_rules.append("FIRS-002: VAT calculation validation failed")
            result.errors.append(f"VAT calculation error: {str(e)}")
    
    def _validate_business_rules(self, invoice_data: Dict[str, Any], result: FIRSValidationResult):
        """Validate FIRS business rules"""
        # Currency validation
        currency = invoice_data.get('currency', '')
        if currency == 'NGN':
            result.passed_rules.append("FIRS-004: Currency is NGN")
        else:
            result.failed_rules.append("FIRS-004: Currency must be NGN")
            result.errors.append(f"Invalid currency: {currency}. Must be NGN")
    
    def _validate_invoice_format(self, invoice_data: Dict[str, Any], result: FIRSValidationResult):
        """Validate invoice format requirements"""
        # Invoice number format
        invoice_number = invoice_data.get('invoice_number', '')
        if invoice_number and len(invoice_number) >= 3:
            result.passed_rules.append("FIRS-FORMAT-001: Invoice number format valid")
        else:
            result.failed_rules.append("FIRS-FORMAT-001: Invalid invoice number format")
            result.errors.append("Invoice number must be at least 3 characters")
    
    def _validate_tax_office_requirements(self, tax_info: NigerianTaxInfo, result: FIRSValidationResult):
        """Validate tax office requirements"""
        if tax_info.tax_office_code in self.tax_offices:
            result.passed_rules.append("FIRS-TAX-OFFICE-001: Valid tax office code")
        else:
            result.failed_rules.append("FIRS-TAX-OFFICE-001: Invalid tax office code")
            result.warnings.append(f"Unknown tax office code: {tax_info.tax_office_code}")
    
    def _validate_tin_format(self, tin: str) -> bool:
        """Validate TIN format"""
        if not tin or len(tin) != 14:
            return False
        return tin.isdigit()
    
    def _check_tin_registry(self, tin: str) -> Dict[str, Any]:
        """Check TIN against FIRS registry (placeholder)"""
        # This would integrate with actual FIRS TIN validation service
        # For now, return mock validation result
        return {
            'is_valid': True,
            'status': TINValidationStatus.VALID,
            'taxpayer_name': 'Sample Taxpayer',
            'registration_date': date(2020, 1, 1),
            'tax_office': 'Lagos Island Tax Office'
        }
    
    def _validate_tin_placeholder(self) -> TINValidationResult:
        """Create placeholder TIN validation result"""
        return TINValidationResult(
            tin="00000000000000",
            is_valid=False,
            status=TINValidationStatus.NOT_FOUND
        )
    
    def _calculate_compliance_score(self, result: FIRSValidationResult) -> float:
        """Calculate compliance score"""
        total_rules = len(result.passed_rules) + len(result.failed_rules)
        if total_rules == 0:
            return 0.0
        
        passed_rules = len(result.passed_rules)
        score = (passed_rules / total_rules) * 100
        
        # Penalty for critical errors
        if result.errors:
            score = max(0, score - (len(result.errors) * 10))
        
        return round(score, 2)
    
    def _determine_compliance_level(self, result: FIRSValidationResult) -> ComplianceLevel:
        """Determine compliance level based on validation results"""
        if result.errors:
            return ComplianceLevel.NON_COMPLIANT
        elif result.warnings:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        elif result.compliance_score >= 95:
            return ComplianceLevel.COMPLIANT
        elif result.compliance_score >= 80:
            return ComplianceLevel.PARTIALLY_COMPLIANT
        else:
            return ComplianceLevel.REQUIRES_REVIEW
    
    def _generate_compliance_recommendations(self, result: FIRSValidationResult) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        if result.errors:
            recommendations.append("Address all validation errors before submission")
        
        if result.warnings:
            recommendations.append("Review and resolve validation warnings")
        
        if result.compliance_score < 100:
            recommendations.append("Improve compliance score by addressing failed validation rules")
        
        if not result.tin_validation.is_valid:
            recommendations.append("Verify and correct TIN information")
        
        return recommendations
    
    def _get_entity_submission_history(self, entity_tin: str, period: str) -> Dict[str, Any]:
        """Get entity submission history (placeholder)"""
        # This would query actual submission database
        return {
            'entity_name': 'Sample Entity',
            'total_invoices_submitted': 100,
            'successful_submissions': 95,
            'rejected_submissions': 3,
            'pending_submissions': 2,
            'avg_processing_time': 24.5
        }
    
    def _assess_compliance_risk(self, submission_data: Dict[str, Any]) -> tuple:
        """Assess compliance risk level"""
        success_rate = (submission_data['successful_submissions'] / 
                       submission_data['total_invoices_submitted'] * 100) if submission_data['total_invoices_submitted'] > 0 else 0
        
        risk_factors = []
        
        if success_rate < 80:
            risk_factors.append("Low submission success rate")
        
        if submission_data['rejected_submissions'] > 10:
            risk_factors.append("High number of rejected submissions")
        
        if success_rate >= 95:
            risk_level = "low"
        elif success_rate >= 80:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        return risk_level, risk_factors
    
    def _calculate_entity_compliance_score(self, submission_data: Dict[str, Any]) -> float:
        """Calculate entity compliance score"""
        success_rate = (submission_data['successful_submissions'] / 
                       submission_data['total_invoices_submitted'] * 100) if submission_data['total_invoices_submitted'] > 0 else 0
        return round(success_rate, 2)
    
    def _generate_required_actions(self, compliance_level: ComplianceLevel, submission_data: Dict[str, Any]) -> List[str]:
        """Generate required compliance actions"""
        actions = []
        
        if compliance_level == ComplianceLevel.NON_COMPLIANT:
            actions.append("Immediate review of submission processes required")
            actions.append("Address all rejected submissions")
        
        if submission_data['pending_submissions'] > 0:
            actions.append("Follow up on pending submissions")
        
        return actions
    
    def _generate_entity_recommendations(self, submission_data: Dict[str, Any]) -> List[str]:
        """Generate entity-specific recommendations"""
        recommendations = []
        
        success_rate = (submission_data['successful_submissions'] / 
                       submission_data['total_invoices_submitted'] * 100) if submission_data['total_invoices_submitted'] > 0 else 0
        
        if success_rate < 95:
            recommendations.append("Implement pre-submission validation checks")
        
        if submission_data.get('avg_processing_time', 0) > 48:
            recommendations.append("Review submission timing and processes")
        
        return recommendations