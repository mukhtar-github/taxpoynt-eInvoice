"""
VAT Calculator
==============

Nigerian VAT calculation engine for automated invoice generation.
Handles VAT rates, exemptions, and compliance with Nigerian tax regulations.

Features:
- Current VAT rates (7.5% standard rate)
- VAT exemptions and zero-rated items
- Customer type-based calculations
- Transaction category analysis
- Compliance validation
"""

from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

from .....core.exceptions import VATCalculationError, ValidationError

logger = logging.getLogger(__name__)


class VATRate(Enum):
    """Nigerian VAT rates."""
    STANDARD = Decimal('0.075')  # 7.5% standard rate
    ZERO_RATED = Decimal('0.000')  # 0% for exempt items
    EXEMPT = Decimal('0.000')      # Fully exempt from VAT


class CustomerType(Enum):
    """Customer types for VAT calculation."""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"
    GOVERNMENT = "government"
    NGO = "ngo"
    DIPLOMAT = "diplomat"


class TransactionCategory(Enum):
    """Transaction categories affecting VAT."""
    GOODS = "goods"
    SERVICES = "services"
    DIGITAL_SERVICES = "digital_services"
    FINANCIAL_SERVICES = "financial_services"
    MEDICAL_SERVICES = "medical_services"
    EDUCATIONAL_SERVICES = "educational_services"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    GOVERNMENT_FEES = "government_fees"
    DONATIONS = "donations"


@dataclass
class VATCalculationResult:
    """Result of VAT calculation."""
    gross_amount: Decimal
    net_amount: Decimal
    vat_amount: Decimal
    vat_rate: Decimal
    vat_category: str
    is_exempt: bool = False
    is_zero_rated: bool = False
    calculation_details: Dict[str, Any] = None
    warnings: List[str] = None


@dataclass
class VATRule:
    """VAT calculation rule."""
    category: str
    customer_type: Optional[str] = None
    vat_rate: Decimal = VATRate.STANDARD.value
    is_exempt: bool = False
    is_zero_rated: bool = False
    conditions: Dict[str, Any] = None
    description: str = ""


class VATCalculator:
    """
    Nigerian VAT calculator for automated invoice generation.
    
    Implements Nigerian VAT regulations including standard rates,
    exemptions, and special cases based on transaction categories
    and customer types.
    """
    
    def __init__(self, vat_rules: Optional[List[VATRule]] = None):
        self.vat_rules = vat_rules or self._create_default_vat_rules()
        
        # Nigerian VAT configuration
        self.standard_vat_rate = VATRate.STANDARD.value
        self.vat_registration_threshold = Decimal('25000000')  # N25M annual turnover
        self.small_company_threshold = Decimal('100000000')   # N100M annual turnover
        
        # Calculation settings
        self.decimal_places = 2
        self.rounding_mode = ROUND_HALF_UP
        
        # Statistics
        self.stats = {
            'calculations_performed': 0,
            'total_vat_calculated': Decimal('0'),
            'exempt_transactions': 0,
            'zero_rated_transactions': 0,
            'category_breakdown': {}
        }
    
    async def calculate_vat(
        self,
        amount: Decimal,
        transaction_type: str,
        customer_type: str = "individual",
        include_vat: bool = False,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> VATCalculationResult:
        """
        Calculate VAT for a transaction amount.
        
        Args:
            amount: Transaction amount
            transaction_type: Type of transaction/service
            customer_type: Type of customer
            include_vat: Whether amount already includes VAT
            additional_info: Additional context for calculation
            
        Returns:
            VATCalculationResult with calculation details
        """
        try:
            logger.debug(f"Calculating VAT for amount: {amount}, type: {transaction_type}")
            
            if amount <= 0:
                raise VATCalculationError("Amount must be positive")
            
            # Find applicable VAT rule
            vat_rule = self._find_applicable_vat_rule(
                transaction_type, customer_type, additional_info
            )
            
            # Calculate VAT based on rule
            if vat_rule.is_exempt:
                result = self._calculate_exempt_vat(amount, vat_rule)
            elif vat_rule.is_zero_rated:
                result = self._calculate_zero_rated_vat(amount, vat_rule)
            else:
                result = self._calculate_standard_vat(
                    amount, vat_rule.vat_rate, include_vat, vat_rule
                )
            
            # Add calculation metadata
            result.calculation_details = {
                'rule_applied': vat_rule.description,
                'calculation_timestamp': datetime.utcnow().isoformat(),
                'customer_type': customer_type,
                'transaction_type': transaction_type,
                'include_vat': include_vat
            }
            
            # Update statistics
            self._update_statistics(result, transaction_type)
            
            logger.debug(f"VAT calculation completed. VAT amount: {result.vat_amount}")
            return result
            
        except Exception as e:
            logger.error(f"VAT calculation failed: {e}")
            raise VATCalculationError(f"VAT calculation failed: {e}")
    
    async def calculate_bulk_vat(
        self,
        transactions: List[Dict[str, Any]]
    ) -> List[VATCalculationResult]:
        """
        Calculate VAT for multiple transactions in bulk.
        
        Args:
            transactions: List of transaction dictionaries
            
        Returns:
            List of VATCalculationResult objects
        """
        logger.info(f"Calculating VAT for {len(transactions)} transactions")
        
        results = []
        for transaction in transactions:
            try:
                result = await self.calculate_vat(
                    amount=transaction['amount'],
                    transaction_type=transaction['transaction_type'],
                    customer_type=transaction.get('customer_type', 'individual'),
                    include_vat=transaction.get('include_vat', False),
                    additional_info=transaction.get('additional_info')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to calculate VAT for transaction: {e}")
                # Create error result
                results.append(VATCalculationResult(
                    gross_amount=transaction['amount'],
                    net_amount=transaction['amount'],
                    vat_amount=Decimal('0'),
                    vat_rate=Decimal('0'),
                    vat_category="error",
                    warnings=[str(e)]
                ))
        
        return results
    
    def _find_applicable_vat_rule(
        self,
        transaction_type: str,
        customer_type: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> VATRule:
        """Find the applicable VAT rule for the transaction."""
        
        # First, try to find exact match
        for rule in self.vat_rules:
            if (rule.category == transaction_type and 
                (rule.customer_type is None or rule.customer_type == customer_type)):
                
                # Check additional conditions if any
                if rule.conditions and additional_info:
                    if self._check_rule_conditions(rule.conditions, additional_info):
                        return rule
                elif not rule.conditions:
                    return rule
        
        # If no exact match, try category-only match
        for rule in self.vat_rules:
            if rule.category == transaction_type and rule.customer_type is None:
                return rule
        
        # Default to standard VAT rule
        return VATRule(
            category="default",
            vat_rate=self.standard_vat_rate,
            description="Standard VAT rate applied"
        )
    
    def _check_rule_conditions(
        self,
        conditions: Dict[str, Any],
        additional_info: Dict[str, Any]
    ) -> bool:
        """Check if rule conditions are met."""
        
        for condition_key, condition_value in conditions.items():
            if condition_key not in additional_info:
                return False
            
            actual_value = additional_info[condition_key]
            
            if isinstance(condition_value, dict):
                # Handle range conditions
                if 'min' in condition_value and actual_value < condition_value['min']:
                    return False
                if 'max' in condition_value and actual_value > condition_value['max']:
                    return False
            elif actual_value != condition_value:
                return False
        
        return True
    
    def _calculate_standard_vat(
        self,
        amount: Decimal,
        vat_rate: Decimal,
        include_vat: bool,
        rule: VATRule
    ) -> VATCalculationResult:
        """Calculate standard VAT."""
        
        if include_vat:
            # Amount includes VAT, extract it
            gross_amount = amount
            net_amount = (amount / (Decimal('1') + vat_rate)).quantize(
                Decimal('0.01'), rounding=self.rounding_mode
            )
            vat_amount = gross_amount - net_amount
        else:
            # Amount excludes VAT, add it
            net_amount = amount
            vat_amount = (amount * vat_rate).quantize(
                Decimal('0.01'), rounding=self.rounding_mode
            )
            gross_amount = net_amount + vat_amount
        
        return VATCalculationResult(
            gross_amount=gross_amount,
            net_amount=net_amount,
            vat_amount=vat_amount,
            vat_rate=vat_rate,
            vat_category="standard"
        )
    
    def _calculate_exempt_vat(
        self,
        amount: Decimal,
        rule: VATRule
    ) -> VATCalculationResult:
        """Calculate VAT for exempt transactions."""
        
        return VATCalculationResult(
            gross_amount=amount,
            net_amount=amount,
            vat_amount=Decimal('0'),
            vat_rate=Decimal('0'),
            vat_category="exempt",
            is_exempt=True
        )
    
    def _calculate_zero_rated_vat(
        self,
        amount: Decimal,
        rule: VATRule
    ) -> VATCalculationResult:
        """Calculate VAT for zero-rated transactions."""
        
        return VATCalculationResult(
            gross_amount=amount,
            net_amount=amount,
            vat_amount=Decimal('0'),
            vat_rate=Decimal('0'),
            vat_category="zero_rated",
            is_zero_rated=True
        )
    
    def _create_default_vat_rules(self) -> List[VATRule]:
        """Create default Nigerian VAT rules."""
        
        return [
            # Exempt services
            VATRule(
                category="medical_services",
                is_exempt=True,
                description="Medical services are exempt from VAT"
            ),
            VATRule(
                category="educational_services",
                is_exempt=True,
                description="Educational services are exempt from VAT"
            ),
            VATRule(
                category="financial_services",
                is_exempt=True,
                description="Financial services are exempt from VAT"
            ),
            VATRule(
                category="government_fees",
                is_exempt=True,
                description="Government fees are exempt from VAT"
            ),
            VATRule(
                category="donations",
                is_exempt=True,
                description="Donations are exempt from VAT"
            ),
            
            # Zero-rated items
            VATRule(
                category="exports",
                is_zero_rated=True,
                description="Export services are zero-rated"
            ),
            VATRule(
                category="basic_food_items",
                is_zero_rated=True,
                description="Basic food items are zero-rated"
            ),
            VATRule(
                category="medical_equipment",
                is_zero_rated=True,
                description="Medical equipment is zero-rated"
            ),
            VATRule(
                category="educational_materials",
                is_zero_rated=True,
                description="Educational materials are zero-rated"
            ),
            
            # Special rates for different customer types
            VATRule(
                category="digital_services",
                customer_type="individual",
                vat_rate=self.standard_vat_rate,
                description="Digital services for individuals - standard rate"
            ),
            VATRule(
                category="digital_services",
                customer_type="corporate",
                vat_rate=self.standard_vat_rate,
                description="Digital services for corporates - standard rate"
            ),
            
            # Diplomatic exemptions
            VATRule(
                category="goods",
                customer_type="diplomat",
                is_exempt=True,
                description="Diplomatic purchases are exempt"
            ),
            VATRule(
                category="services",
                customer_type="diplomat",
                is_exempt=True,
                description="Diplomatic services are exempt"
            ),
            
            # Default standard rate
            VATRule(
                category="goods",
                vat_rate=self.standard_vat_rate,
                description="Standard VAT rate for goods"
            ),
            VATRule(
                category="services",
                vat_rate=self.standard_vat_rate,
                description="Standard VAT rate for services"
            ),
            VATRule(
                category="utilities",
                vat_rate=self.standard_vat_rate,
                description="Standard VAT rate for utilities"
            ),
            VATRule(
                category="transport",
                vat_rate=self.standard_vat_rate,
                description="Standard VAT rate for transport"
            )
        ]
    
    def _update_statistics(self, result: VATCalculationResult, transaction_type: str):
        """Update calculation statistics."""
        
        self.stats['calculations_performed'] += 1
        self.stats['total_vat_calculated'] += result.vat_amount
        
        if result.is_exempt:
            self.stats['exempt_transactions'] += 1
        elif result.is_zero_rated:
            self.stats['zero_rated_transactions'] += 1
        
        # Update category breakdown
        if transaction_type not in self.stats['category_breakdown']:
            self.stats['category_breakdown'][transaction_type] = {
                'count': 0,
                'total_vat': Decimal('0')
            }
        
        self.stats['category_breakdown'][transaction_type]['count'] += 1
        self.stats['category_breakdown'][transaction_type]['total_vat'] += result.vat_amount
    
    def validate_vat_registration(
        self,
        annual_turnover: Decimal,
        customer_type: str = "corporate"
    ) -> Dict[str, Any]:
        """
        Validate if a business needs VAT registration.
        
        Args:
            annual_turnover: Annual turnover amount
            customer_type: Type of customer/business
            
        Returns:
            Dictionary with registration requirements
        """
        
        result = {
            'registration_required': False,
            'registration_optional': False,
            'threshold_exceeded': False,
            'current_threshold': self.vat_registration_threshold,
            'annual_turnover': annual_turnover
        }
        
        if annual_turnover >= self.vat_registration_threshold:
            result['registration_required'] = True
            result['threshold_exceeded'] = True
        elif annual_turnover >= (self.vat_registration_threshold * Decimal('0.8')):
            # Close to threshold - optional registration
            result['registration_optional'] = True
        
        return result
    
    def get_applicable_rate(
        self,
        transaction_type: str,
        customer_type: str = "individual"
    ) -> Decimal:
        """
        Get applicable VAT rate for transaction type and customer.
        
        Args:
            transaction_type: Type of transaction
            customer_type: Type of customer
            
        Returns:
            Applicable VAT rate as decimal
        """
        
        rule = self._find_applicable_vat_rule(transaction_type, customer_type)
        
        if rule.is_exempt or rule.is_zero_rated:
            return Decimal('0')
        
        return rule.vat_rate
    
    def get_vat_breakdown(
        self,
        amounts: List[Tuple[Decimal, str, str]]
    ) -> Dict[str, Any]:
        """
        Get VAT breakdown for multiple amounts.
        
        Args:
            amounts: List of (amount, transaction_type, customer_type) tuples
            
        Returns:
            Dictionary with VAT breakdown by category
        """
        
        breakdown = {
            'total_net': Decimal('0'),
            'total_vat': Decimal('0'),
            'total_gross': Decimal('0'),
            'categories': {}
        }
        
        for amount, transaction_type, customer_type in amounts:
            rate = self.get_applicable_rate(transaction_type, customer_type)
            
            if transaction_type not in breakdown['categories']:
                breakdown['categories'][transaction_type] = {
                    'net_amount': Decimal('0'),
                    'vat_amount': Decimal('0'),
                    'vat_rate': rate,
                    'count': 0
                }
            
            vat_amount = (amount * rate).quantize(
                Decimal('0.01'), rounding=self.rounding_mode
            )
            
            breakdown['categories'][transaction_type]['net_amount'] += amount
            breakdown['categories'][transaction_type]['vat_amount'] += vat_amount
            breakdown['categories'][transaction_type]['count'] += 1
            
            breakdown['total_net'] += amount
            breakdown['total_vat'] += vat_amount
            breakdown['total_gross'] += amount + vat_amount
        
        return breakdown
    
    def get_calculation_stats(self) -> Dict[str, Any]:
        """Get VAT calculation statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset calculation statistics."""
        self.stats = {
            'calculations_performed': 0,
            'total_vat_calculated': Decimal('0'),
            'exempt_transactions': 0,
            'zero_rated_transactions': 0,
            'category_breakdown': {}
        }