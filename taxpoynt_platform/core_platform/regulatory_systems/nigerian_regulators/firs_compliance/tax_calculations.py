"""
Nigerian Tax Calculation Engine
==============================
Comprehensive tax calculation and validation engine for Nigerian tax compliance
including VAT, Withholding Tax, and other Nigerian tax obligations.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

from .models import VATCalculation, VATStatus, TaxType

logger = logging.getLogger(__name__)

class NigerianTaxCalculator:
    """
    Nigerian tax calculation engine for FIRS compliance
    """
    
    def __init__(self):
        """Initialize Nigerian tax calculator"""
        self.logger = logging.getLogger(__name__)
        
        # Nigerian tax rates (as of 2024)
        self.vat_rate = Decimal('7.5')
        self.education_tax_rate = Decimal('2.0')  # On CIT
        self.national_housing_fund_rate = Decimal('2.5')  # Employee contribution
        
        # Load tax tables and rates
        self.withholding_tax_rates = self._load_withholding_tax_rates()
        self.personal_income_tax_bands = self._load_pit_bands()
        self.company_income_tax_rate = Decimal('30.0')  # Standard CIT rate
        self.stamp_duty_rates = self._load_stamp_duty_rates()
        self.customs_duty_rates = self._load_customs_duty_rates()
        
        # VAT exempt items
        self.vat_exempt_items = self._load_vat_exempt_items()
        self.vat_zero_rated_items = self._load_vat_zero_rated_items()
    
    def calculate_vat(
        self, 
        amount: Decimal, 
        item_description: str = "", 
        is_export: bool = False,
        customer_type: str = "individual"
    ) -> VATCalculation:
        """
        Calculate Nigerian VAT with exemptions and zero-rating
        
        Args:
            amount: Amount before VAT
            item_description: Description of item/service for exemption check
            is_export: Whether transaction is export (zero-rated)
            customer_type: Customer type (individual, company, government)
            
        Returns:
            VATCalculation with detailed calculation
        """
        try:
            self.logger.info(f"Calculating VAT for amount: {amount}")
            
            # Check for exemptions
            if self._is_vat_exempt(item_description, customer_type):
                return VATCalculation(
                    amount_before_vat=amount,
                    vat_rate=Decimal('0'),
                    vat_amount=Decimal('0'),
                    total_amount=amount,
                    vat_status=VATStatus.EXEMPT,
                    is_vat_exempt=True,
                    exemption_reason=f"VAT exempt: {item_description}"
                )
            
            # Check for zero-rating (exports, essential items)
            if is_export or self._is_vat_zero_rated(item_description):
                return VATCalculation(
                    amount_before_vat=amount,
                    vat_rate=Decimal('0'),
                    vat_amount=Decimal('0'),
                    total_amount=amount,
                    vat_status=VATStatus.ZERO_RATED,
                    is_vat_exempt=False,
                    exemption_reason="Zero-rated supply"
                )
            
            # Calculate standard VAT
            vat_amount = self._round_currency(amount * (self.vat_rate / 100))
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
    
    def calculate_withholding_tax(
        self, 
        amount: Decimal, 
        service_type: str,
        payer_type: str = "company",
        payee_type: str = "individual"
    ) -> Dict[str, Any]:
        """
        Calculate Nigerian withholding tax
        
        Args:
            amount: Service/payment amount
            service_type: Type of service/payment
            payer_type: Type of payer (company, government, individual)
            payee_type: Type of payee (company, individual, non-resident)
            
        Returns:
            Dictionary with WHT calculation details
        """
        try:
            self.logger.info(f"Calculating WHT for {service_type}: {amount}")
            
            # Get applicable WHT rate
            wht_rate = self._get_wht_rate(service_type, payer_type, payee_type)
            
            if wht_rate == Decimal('0'):
                return {
                    'is_applicable': False,
                    'wht_rate': Decimal('0'),
                    'wht_amount': Decimal('0'),
                    'net_amount': amount,
                    'service_type': service_type,
                    'exemption_reason': 'No WHT applicable for this transaction'
                }
            
            # Calculate WHT
            wht_amount = self._round_currency(amount * (wht_rate / 100))
            net_amount = amount - wht_amount
            
            return {
                'is_applicable': True,
                'wht_rate': wht_rate,
                'wht_amount': wht_amount,
                'net_amount': net_amount,
                'gross_amount': amount,
                'service_type': service_type,
                'payer_type': payer_type,
                'payee_type': payee_type,
                'tax_authority': 'FIRS'
            }
            
        except Exception as e:
            self.logger.error(f"WHT calculation failed: {str(e)}")
            raise ValueError(f"WHT calculation error: {str(e)}")
    
    def calculate_personal_income_tax(
        self, 
        annual_income: Decimal,
        allowances: Decimal = Decimal('0'),
        pension_contribution: Decimal = Decimal('0'),
        state: str = "lagos"
    ) -> Dict[str, Any]:
        """
        Calculate Nigerian Personal Income Tax (PIT)
        
        Args:
            annual_income: Annual gross income
            allowances: Total allowances and reliefs
            pension_contribution: Pension contribution
            state: State for state-specific rates
            
        Returns:
            Dictionary with PIT calculation details
        """
        try:
            self.logger.info(f"Calculating PIT for annual income: {annual_income}")
            
            # Calculate taxable income
            gross_income = annual_income
            total_reliefs = allowances + pension_contribution
            
            # Consolidated Relief Allowance (CRA) - higher of 1% of gross income or N200,000
            cra = max(gross_income * Decimal('0.01'), Decimal('200000'))
            total_reliefs += cra
            
            taxable_income = max(gross_income - total_reliefs, Decimal('0'))
            
            # Calculate tax using bands
            federal_tax = self._calculate_pit_bands(taxable_income)
            
            # State tax (typically 0% to 5% of federal tax or separate calculation)
            state_tax_rate = self._get_state_tax_rate(state)
            state_tax = federal_tax * (state_tax_rate / 100)
            
            total_tax = federal_tax + state_tax
            net_income = gross_income - total_tax
            
            return {
                'gross_income': gross_income,
                'total_reliefs': total_reliefs,
                'cra': cra,
                'taxable_income': taxable_income,
                'federal_tax': federal_tax,
                'state_tax': state_tax,
                'total_tax': total_tax,
                'net_income': net_income,
                'effective_tax_rate': (total_tax / gross_income * 100) if gross_income > 0 else Decimal('0'),
                'state': state
            }
            
        except Exception as e:
            self.logger.error(f"PIT calculation failed: {str(e)}")
            raise ValueError(f"PIT calculation error: {str(e)}")
    
    def calculate_company_income_tax(
        self, 
        profit_before_tax: Decimal,
        capital_allowances: Decimal = Decimal('0'),
        donations: Decimal = Decimal('0'),
        company_size: str = "large"
    ) -> Dict[str, Any]:
        """
        Calculate Nigerian Company Income Tax (CIT)
        
        Args:
            profit_before_tax: Company profit before tax
            capital_allowances: Capital allowances claimed
            donations: Qualifying donations
            company_size: Company size (small, medium, large)
            
        Returns:
            Dictionary with CIT calculation details
        """
        try:
            self.logger.info(f"Calculating CIT for profit: {profit_before_tax}, size: {company_size}")
            
            # Determine CIT rate based on company size
            cit_rate = self._get_cit_rate(company_size, profit_before_tax)
            
            # Calculate adjustments
            qualifying_donations = min(donations, profit_before_tax * Decimal('0.10'))  # Max 10% of profit
            
            # Calculate taxable profit
            taxable_profit = max(
                profit_before_tax - capital_allowances - qualifying_donations,
                Decimal('0')
            )
            
            # Calculate CIT
            cit_amount = self._round_currency(taxable_profit * (cit_rate / 100))
            
            # Calculate Education Tax (2% of CIT for companies with turnover > N100M)
            education_tax = Decimal('0')
            if company_size in ['medium', 'large']:
                education_tax = self._round_currency(cit_amount * (self.education_tax_rate / 100))
            
            total_tax = cit_amount + education_tax
            profit_after_tax = profit_before_tax - total_tax
            
            return {
                'profit_before_tax': profit_before_tax,
                'capital_allowances': capital_allowances,
                'qualifying_donations': qualifying_donations,
                'taxable_profit': taxable_profit,
                'cit_rate': cit_rate,
                'cit_amount': cit_amount,
                'education_tax': education_tax,
                'total_tax': total_tax,
                'profit_after_tax': profit_after_tax,
                'effective_tax_rate': (total_tax / profit_before_tax * 100) if profit_before_tax > 0 else Decimal('0'),
                'company_size': company_size
            }
            
        except Exception as e:
            self.logger.error(f"CIT calculation failed: {str(e)}")
            raise ValueError(f"CIT calculation error: {str(e)}")
    
    def calculate_stamp_duty(
        self, 
        document_type: str, 
        amount: Decimal,
        document_value: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate Nigerian stamp duty
        
        Args:
            document_type: Type of document
            amount: Transaction amount
            document_value: Document value if different from amount
            
        Returns:
            Dictionary with stamp duty calculation
        """
        try:
            value_for_calculation = document_value or amount
            stamp_duty_info = self.stamp_duty_rates.get(document_type.lower(), {})
            
            if not stamp_duty_info:
                return {
                    'is_applicable': False,
                    'stamp_duty': Decimal('0'),
                    'document_type': document_type,
                    'reason': 'No stamp duty applicable for this document type'
                }
            
            # Calculate stamp duty based on type
            if stamp_duty_info['type'] == 'fixed':
                stamp_duty = stamp_duty_info['amount']
            elif stamp_duty_info['type'] == 'percentage':
                stamp_duty = self._round_currency(
                    value_for_calculation * (stamp_duty_info['rate'] / 100)
                )
                # Apply minimum and maximum if specified
                if 'minimum' in stamp_duty_info:
                    stamp_duty = max(stamp_duty, stamp_duty_info['minimum'])
                if 'maximum' in stamp_duty_info:
                    stamp_duty = min(stamp_duty, stamp_duty_info['maximum'])
            else:
                stamp_duty = Decimal('0')
            
            return {
                'is_applicable': True,
                'stamp_duty': stamp_duty,
                'document_type': document_type,
                'calculation_basis': value_for_calculation,
                'rate_info': stamp_duty_info
            }
            
        except Exception as e:
            self.logger.error(f"Stamp duty calculation failed: {str(e)}")
            raise ValueError(f"Stamp duty calculation error: {str(e)}")
    
    def validate_tax_calculations(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all tax calculations in an invoice
        
        Args:
            invoice_data: Invoice data dictionary
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'calculations': {}
            }
            
            # Validate VAT calculation
            if 'vat_amount' in invoice_data:
                vat_validation = self._validate_vat_calculation(invoice_data)
                validation_results['calculations']['vat'] = vat_validation
                if not vat_validation['is_correct']:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(vat_validation['error_message'])
            
            # Validate WHT calculation
            if 'withholding_tax' in invoice_data:
                wht_validation = self._validate_wht_calculation(invoice_data)
                validation_results['calculations']['wht'] = wht_validation
                if not wht_validation['is_correct']:
                    validation_results['warnings'].append(wht_validation['warning_message'])
            
            # Validate total calculations
            total_validation = self._validate_total_calculation(invoice_data)
            validation_results['calculations']['total'] = total_validation
            if not total_validation['is_correct']:
                validation_results['is_valid'] = False
                validation_results['errors'].append(total_validation['error_message'])
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Tax validation failed: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Tax validation error: {str(e)}"],
                'warnings': [],
                'calculations': {}
            }
    
    # Private helper methods
    
    def _load_withholding_tax_rates(self) -> Dict[str, Decimal]:
        """Load withholding tax rates"""
        return {
            # Professional services
            'professional_services': Decimal('5.0'),
            'legal_services': Decimal('5.0'),
            'accounting_services': Decimal('5.0'),
            'consulting': Decimal('5.0'),
            'technical_services': Decimal('5.0'),
            'management_services': Decimal('5.0'),
            'advertising': Decimal('5.0'),
            
            # Construction and supplies
            'construction': Decimal('5.0'),
            'building_construction': Decimal('5.0'),
            'road_construction': Decimal('5.0'),
            'supplies': Decimal('5.0'),
            
            # Transport and logistics
            'haulage': Decimal('5.0'),
            'transportation': Decimal('5.0'),
            'logistics': Decimal('5.0'),
            
            # Financial services
            'interest': Decimal('10.0'),
            'banking': Decimal('10.0'),
            'finance': Decimal('10.0'),
            
            # Investment income
            'dividend': Decimal('10.0'),
            'rent': Decimal('10.0'),
            'royalty': Decimal('10.0'),
            'commission': Decimal('5.0'),
            
            # International transactions
            'non_resident_company': Decimal('10.0'),
            'non_resident_individual': Decimal('10.0'),
            'management_fees_foreign': Decimal('10.0'),
            
            # Specific sectors
            'telecommunications': Decimal('5.0'),
            'insurance': Decimal('10.0'),
            'pension': Decimal('10.0')
        }
    
    def _load_pit_bands(self) -> List[Dict[str, Any]]:
        """Load Personal Income Tax bands"""
        return [
            {'min': Decimal('0'), 'max': Decimal('300000'), 'rate': Decimal('7.0')},
            {'min': Decimal('300000'), 'max': Decimal('600000'), 'rate': Decimal('11.0')},
            {'min': Decimal('600000'), 'max': Decimal('1100000'), 'rate': Decimal('15.0')},
            {'min': Decimal('1100000'), 'max': Decimal('1600000'), 'rate': Decimal('19.0')},
            {'min': Decimal('1600000'), 'max': Decimal('3200000'), 'rate': Decimal('21.0')},
            {'min': Decimal('3200000'), 'max': None, 'rate': Decimal('24.0')}
        ]
    
    def _load_stamp_duty_rates(self) -> Dict[str, Dict[str, Any]]:
        """Load stamp duty rates"""
        return {
            'receipt': {
                'type': 'fixed',
                'amount': Decimal('50.0'),
                'threshold': Decimal('10000')  # Only if receipt is above N10,000
            },
            'agreement': {
                'type': 'percentage',
                'rate': Decimal('0.75'),
                'minimum': Decimal('500')
            },
            'lease': {
                'type': 'percentage',
                'rate': Decimal('0.75'),
                'minimum': Decimal('1000')
            },
            'loan_agreement': {
                'type': 'percentage',
                'rate': Decimal('1.5'),
                'minimum': Decimal('1000')
            },
            'share_transfer': {
                'type': 'percentage',
                'rate': Decimal('0.75'),
                'minimum': Decimal('500')
            }
        }
    
    def _load_customs_duty_rates(self) -> Dict[str, Decimal]:
        """Load customs duty rates (simplified)"""
        return {
            'essential_goods': Decimal('5.0'),
            'raw_materials': Decimal('10.0'),
            'intermediate_goods': Decimal('20.0'),
            'finished_goods': Decimal('35.0'),
            'luxury_goods': Decimal('70.0')
        }
    
    def _load_vat_exempt_items(self) -> List[str]:
        """Load VAT exempt items and services"""
        return [
            'medical services', 'healthcare', 'hospital services',
            'educational services', 'school fees', 'tuition',
            'basic food items', 'baby products', 'milk',
            'books', 'newspapers', 'magazines',
            'pharmaceutical products', 'medicine',
            'residential rent', 'house rent',
            'public transportation', 'commercial vehicles',
            'agricultural products', 'farming equipment',
            'export goods', 'goods in transit'
        ]
    
    def _load_vat_zero_rated_items(self) -> List[str]:
        """Load zero-rated VAT items"""
        return [
            'exports', 'export services',
            'goods in transit', 'transit goods',
            'aircraft', 'ships', 'international transport',
            'diplomatic goods', 'embassy supplies'
        ]
    
    def _is_vat_exempt(self, item_description: str, customer_type: str) -> bool:
        """Check if item is VAT exempt"""
        item_lower = item_description.lower()
        return any(exempt_item in item_lower for exempt_item in self.vat_exempt_items)
    
    def _is_vat_zero_rated(self, item_description: str) -> bool:
        """Check if item is zero-rated for VAT"""
        item_lower = item_description.lower()
        return any(zero_rated_item in item_lower for zero_rated_item in self.vat_zero_rated_items)
    
    def _get_wht_rate(self, service_type: str, payer_type: str, payee_type: str) -> Decimal:
        """Get applicable withholding tax rate"""
        service_lower = service_type.lower()
        
        # Non-resident rates are typically higher
        if payee_type == 'non_resident':
            return self.withholding_tax_rates.get(f"{service_lower}_foreign", 
                                                 self.withholding_tax_rates.get('non_resident_company', Decimal('10.0')))
        
        return self.withholding_tax_rates.get(service_lower, Decimal('0'))
    
    def _calculate_pit_bands(self, taxable_income: Decimal) -> Decimal:
        """Calculate PIT using tax bands"""
        total_tax = Decimal('0')
        remaining_income = taxable_income
        
        for band in self.personal_income_tax_bands:
            band_min = band['min']
            band_max = band['max']
            rate = band['rate']
            
            if remaining_income <= 0:
                break
            
            if band_max is None:
                # Top band
                taxable_in_band = remaining_income
            else:
                taxable_in_band = min(remaining_income, band_max - band_min)
            
            if taxable_in_band > 0:
                tax_in_band = self._round_currency(taxable_in_band * (rate / 100))
                total_tax += tax_in_band
                remaining_income -= taxable_in_band
        
        return total_tax
    
    def _get_state_tax_rate(self, state: str) -> Decimal:
        """Get state tax rate"""
        # State tax rates vary, typically 0% to 5% of federal tax
        state_rates = {
            'lagos': Decimal('0'),  # Lagos uses PAYE
            'abuja': Decimal('0'),
            'rivers': Decimal('5'),
            'ogun': Decimal('3'),
            'kano': Decimal('2')
        }
        return state_rates.get(state.lower(), Decimal('0'))
    
    def _get_cit_rate(self, company_size: str, profit: Decimal) -> Decimal:
        """Get CIT rate based on company size and profit"""
        if company_size == 'small' and profit <= Decimal('25000000'):  # N25M threshold
            return Decimal('20.0')  # Reduced rate for small companies
        elif company_size == 'medium':
            return Decimal('25.0')
        else:
            return self.company_income_tax_rate  # 30% standard rate
    
    def _round_currency(self, amount: Decimal) -> Decimal:
        """Round currency to 2 decimal places"""
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _validate_vat_calculation(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VAT calculation in invoice"""
        try:
            subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
            vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
            
            expected_vat = self._round_currency(subtotal * (self.vat_rate / 100))
            
            is_correct = abs(vat_amount - expected_vat) <= Decimal('0.01')
            
            return {
                'is_correct': is_correct,
                'expected_vat': expected_vat,
                'actual_vat': vat_amount,
                'difference': vat_amount - expected_vat,
                'error_message': f"VAT calculation incorrect. Expected: {expected_vat}, Actual: {vat_amount}" if not is_correct else None
            }
            
        except Exception as e:
            return {
                'is_correct': False,
                'error_message': f"VAT validation error: {str(e)}"
            }
    
    def _validate_wht_calculation(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate WHT calculation in invoice"""
        try:
            # This is a warning validation since WHT might not always be required
            amount = Decimal(str(invoice_data.get('subtotal', 0)))
            wht_amount = Decimal(str(invoice_data.get('withholding_tax', 0)))
            service_type = invoice_data.get('service_type', 'unknown')
            
            expected_wht_rate = self._get_wht_rate(service_type, 'company', 'individual')
            expected_wht = self._round_currency(amount * (expected_wht_rate / 100))
            
            is_correct = abs(wht_amount - expected_wht) <= Decimal('0.01') or wht_amount == Decimal('0')
            
            return {
                'is_correct': is_correct,
                'expected_wht': expected_wht,
                'actual_wht': wht_amount,
                'expected_rate': expected_wht_rate,
                'warning_message': f"WHT may be required. Expected rate: {expected_wht_rate}%, Amount: {expected_wht}" if not is_correct and expected_wht > 0 else None
            }
            
        except Exception as e:
            return {
                'is_correct': True,  # Don't fail validation for WHT errors
                'warning_message': f"WHT validation warning: {str(e)}"
            }
    
    def _validate_total_calculation(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate total amount calculation"""
        try:
            subtotal = Decimal(str(invoice_data.get('subtotal', 0)))
            vat_amount = Decimal(str(invoice_data.get('vat_amount', 0)))
            total_amount = Decimal(str(invoice_data.get('total_amount', 0)))
            
            expected_total = subtotal + vat_amount
            is_correct = abs(total_amount - expected_total) <= Decimal('0.01')
            
            return {
                'is_correct': is_correct,
                'expected_total': expected_total,
                'actual_total': total_amount,
                'difference': total_amount - expected_total,
                'error_message': f"Total calculation incorrect. Expected: {expected_total}, Actual: {total_amount}" if not is_correct else None
            }
            
        except Exception as e:
            return {
                'is_correct': False,
                'error_message': f"Total validation error: {str(e)}"
            }