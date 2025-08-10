"""
Nigerian Business Rules Engine
==============================

Comprehensive business rules engine that enforces Nigerian regulatory compliance
for different connector types. Each business system type has specific compliance
requirements that must be validated before invoice generation and FIRS submission.

This module implements the regulatory knowledge required for Nigerian e-invoicing
compliance across various business sectors and system types.

Nigerian Regulatory Framework:
- Federal Inland Revenue Service (FIRS) requirements
- Companies and Allied Matters Act (CAMA) compliance
- Value Added Tax (VAT) regulations
- Nigerian Accounting Standards
- Central Bank of Nigeria (CBN) guidelines (for financial data)
- Consumer Protection regulations
- Sector-specific compliance requirements
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime
import re

from ..connector_configs.connector_types import ConnectorType, ConnectorCategory


class ComplianceLevel(Enum):
    """Severity levels for compliance violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleCategory(Enum):
    """Categories of Nigerian business rules."""
    TAX_COMPLIANCE = "tax_compliance"
    ACCOUNTING_STANDARDS = "accounting_standards"
    DATA_QUALITY = "data_quality"
    CONSUMER_PROTECTION = "consumer_protection"
    FINANCIAL_REGULATIONS = "financial_regulations"
    SECTOR_SPECIFIC = "sector_specific"
    ANTI_FRAUD = "anti_fraud"


@dataclass
class BusinessRuleViolation:
    """Represents a business rule violation."""
    rule_id: str
    rule_name: str
    category: RuleCategory
    level: ComplianceLevel
    description: str
    field_name: Optional[str] = None
    current_value: Optional[Any] = None
    expected_value: Optional[Any] = None
    remediation_hint: Optional[str] = None


@dataclass
class BusinessRuleResult:
    """Result of business rule evaluation."""
    transaction_id: str
    connector_type: ConnectorType
    overall_compliance: bool
    violations: List[BusinessRuleViolation]
    warnings: List[BusinessRuleViolation]
    recommendations: List[str]
    
    @property
    def has_critical_violations(self) -> bool:
        """Check if there are critical compliance violations."""
        return any(v.level == ComplianceLevel.CRITICAL for v in self.violations)
    
    @property
    def has_error_violations(self) -> bool:
        """Check if there are error-level violations."""
        return any(v.level == ComplianceLevel.ERROR for v in self.violations)
    
    @property
    def violation_count_by_category(self) -> Dict[RuleCategory, int]:
        """Count violations by category."""
        counts = {}
        for violation in self.violations:
            counts[violation.category] = counts.get(violation.category, 0) + 1
        return counts


class NigerianBusinessRulesEngine:
    """
    Nigerian compliance business rules engine for different connector types.
    
    This engine implements comprehensive Nigerian regulatory requirements
    and adapts rule enforcement based on the source business system type.
    """
    
    def __init__(self):
        """Initialize the Nigerian business rules engine."""
        # VAT rate in Nigeria (as of 2024)
        self.current_vat_rate = Decimal('0.075')  # 7.5%
        
        # Currency code for Nigerian Naira
        self.nigerian_currency = 'NGN'
        
        # Initialize rule definitions
        self._initialize_rule_definitions()
    
    def _initialize_rule_definitions(self):
        """Initialize comprehensive rule definitions."""
        # This would typically be loaded from a configuration file or database
        # For now, we'll define them programmatically
        
        self.rule_definitions = {
            # Tax Compliance Rules
            'VAT_RATE_VALIDATION': {
                'category': RuleCategory.TAX_COMPLIANCE,
                'level': ComplianceLevel.ERROR,
                'description': 'VAT rate must comply with current Nigerian rate of 7.5%',
                'applicable_connectors': 'all'
            },
            
            'TIN_VALIDATION': {
                'category': RuleCategory.TAX_COMPLIANCE,
                'level': ComplianceLevel.CRITICAL,
                'description': 'Valid Tax Identification Number (TIN) is required',
                'applicable_connectors': 'all'
            },
            
            'VAT_EXEMPTION_VALIDATION': {
                'category': RuleCategory.TAX_COMPLIANCE,
                'level': ComplianceLevel.WARNING,
                'description': 'VAT exemptions must have valid justification',
                'applicable_connectors': 'all'
            },
            
            # Accounting Standards Rules
            'ACCOUNTING_PERIOD_VALIDATION': {
                'category': RuleCategory.ACCOUNTING_STANDARDS,
                'level': ComplianceLevel.ERROR,
                'description': 'Transaction dates must fall within valid accounting periods',
                'applicable_connectors': ['erp', 'accounting']
            },
            
            'CHART_OF_ACCOUNTS_VALIDATION': {
                'category': RuleCategory.ACCOUNTING_STANDARDS,
                'level': ComplianceLevel.WARNING,
                'description': 'Account codes should follow Nigerian chart of accounts standards',
                'applicable_connectors': ['erp', 'accounting']
            },
            
            'AUDIT_TRAIL_COMPLETENESS': {
                'category': RuleCategory.ACCOUNTING_STANDARDS,
                'level': ComplianceLevel.ERROR,
                'description': 'Complete audit trail information must be maintained',
                'applicable_connectors': ['erp', 'accounting']
            },
            
            # Data Quality Rules
            'MANDATORY_FIELDS_VALIDATION': {
                'category': RuleCategory.DATA_QUALITY,
                'level': ComplianceLevel.CRITICAL,
                'description': 'All mandatory fields must be present and valid',
                'applicable_connectors': 'all'
            },
            
            'AMOUNT_PRECISION_VALIDATION': {
                'category': RuleCategory.DATA_QUALITY,
                'level': ComplianceLevel.ERROR,
                'description': 'Monetary amounts must have appropriate precision (2 decimal places)',
                'applicable_connectors': 'all'
            },
            
            'DATE_FORMAT_VALIDATION': {
                'category': RuleCategory.DATA_QUALITY,
                'level': ComplianceLevel.ERROR,
                'description': 'Dates must be in valid format and within reasonable ranges',
                'applicable_connectors': 'all'
            },
            
            # Consumer Protection Rules
            'RECEIPT_COMPLETENESS': {
                'category': RuleCategory.CONSUMER_PROTECTION,
                'level': ComplianceLevel.ERROR,
                'description': 'Customer receipts must contain all required information',
                'applicable_connectors': ['pos', 'ecommerce']
            },
            
            'REFUND_POLICY_DISCLOSURE': {
                'category': RuleCategory.CONSUMER_PROTECTION,
                'level': ComplianceLevel.WARNING,
                'description': 'Refund policy must be clearly disclosed',
                'applicable_connectors': ['pos', 'ecommerce', 'crm']
            },
            
            # Financial Regulations Rules
            'TRANSACTION_LIMITS': {
                'category': RuleCategory.FINANCIAL_REGULATIONS,
                'level': ComplianceLevel.WARNING,
                'description': 'Large transactions may require additional documentation',
                'applicable_connectors': ['banking', 'financial']
            },
            
            'CURRENCY_COMPLIANCE': {
                'category': RuleCategory.FINANCIAL_REGULATIONS,
                'level': ComplianceLevel.ERROR,
                'description': 'Foreign currency transactions must comply with CBN regulations',
                'applicable_connectors': ['banking', 'financial', 'erp']
            },
            
            # Anti-Fraud Rules
            'UNUSUAL_TRANSACTION_PATTERNS': {
                'category': RuleCategory.ANTI_FRAUD,
                'level': ComplianceLevel.WARNING,
                'description': 'Unusual transaction patterns detected',
                'applicable_connectors': 'all'
            },
            
            'ROUND_AMOUNT_VALIDATION': {
                'category': RuleCategory.ANTI_FRAUD,
                'level': ComplianceLevel.INFO,
                'description': 'Unusually round amounts may indicate manual manipulation',
                'applicable_connectors': 'all'
            }
        }
    
    def evaluate_transaction(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> BusinessRuleResult:
        """
        Evaluate a transaction against Nigerian business rules.
        
        Args:
            transaction: Transaction to evaluate
            connector_type: Type of source connector
            
        Returns:
            Business rule evaluation result
        """
        violations = []
        warnings = []
        recommendations = []
        
        # Get transaction ID
        transaction_id = getattr(transaction, 'id', 'unknown')
        
        # Apply connector-specific rules
        if connector_type.value.startswith('erp_'):
            violations.extend(self._validate_erp_rules(transaction, connector_type))
        elif connector_type.value.startswith('crm_'):
            violations.extend(self._validate_crm_rules(transaction, connector_type))
        elif connector_type.value.startswith('pos_'):
            violations.extend(self._validate_pos_rules(transaction, connector_type))
        elif connector_type.value.startswith('ecommerce_'):
            violations.extend(self._validate_ecommerce_rules(transaction, connector_type))
        elif connector_type.value.startswith('accounting_'):
            violations.extend(self._validate_accounting_rules(transaction, connector_type))
        elif connector_type.value.startswith('banking_'):
            violations.extend(self._validate_banking_rules(transaction, connector_type))
        
        # Apply universal rules
        violations.extend(self._validate_universal_rules(transaction, connector_type))
        
        # Separate violations by severity
        critical_and_error_violations = [
            v for v in violations 
            if v.level in [ComplianceLevel.CRITICAL, ComplianceLevel.ERROR]
        ]
        
        warning_violations = [
            v for v in violations 
            if v.level == ComplianceLevel.WARNING
        ]
        
        # Generate recommendations
        recommendations = self._generate_recommendations(violations, connector_type)
        
        # Determine overall compliance
        overall_compliance = len(critical_and_error_violations) == 0
        
        return BusinessRuleResult(
            transaction_id=transaction_id,
            connector_type=connector_type,
            overall_compliance=overall_compliance,
            violations=critical_and_error_violations,
            warnings=warning_violations,
            recommendations=recommendations
        )
    
    def _validate_erp_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate ERP-specific Nigerian business rules."""
        violations = []
        
        # ERP systems should have structured accounting data
        if not hasattr(transaction, 'account_code') or not transaction.account_code:
            violations.append(BusinessRuleViolation(
                rule_id='ERP_ACCOUNT_CODE_REQUIRED',
                rule_name='Account Code Required',
                category=RuleCategory.ACCOUNTING_STANDARDS,
                level=ComplianceLevel.ERROR,
                description='ERP transactions must include valid account codes',
                field_name='account_code',
                current_value=getattr(transaction, 'account_code', None),
                remediation_hint='Ensure transaction includes proper chart of accounts mapping'
            ))
        
        # Validate cost center for larger organizations
        amount = getattr(transaction, 'amount', 0)
        if amount > 100000 and (not hasattr(transaction, 'cost_center') or not transaction.cost_center):
            violations.append(BusinessRuleViolation(
                rule_id='ERP_COST_CENTER_REQUIRED',
                rule_name='Cost Center Required for Large Transactions',
                category=RuleCategory.ACCOUNTING_STANDARDS,
                level=ComplianceLevel.WARNING,
                description='Large transactions should include cost center information',
                field_name='cost_center',
                current_value=getattr(transaction, 'cost_center', None),
                remediation_hint='Include cost center for transactions above ₦100,000'
            ))
        
        # Validate invoice numbering for ERP systems
        if hasattr(transaction, 'invoice_number') and transaction.invoice_number:
            if not self._validate_nigerian_invoice_numbering(transaction.invoice_number):
                violations.append(BusinessRuleViolation(
                    rule_id='ERP_INVOICE_NUMBERING',
                    rule_name='Invalid Invoice Numbering',
                    category=RuleCategory.ACCOUNTING_STANDARDS,
                    level=ComplianceLevel.ERROR,
                    description='Invoice numbering must follow Nigerian standards',
                    field_name='invoice_number',
                    current_value=transaction.invoice_number,
                    remediation_hint='Use sequential numbering with proper prefixes'
                ))
        
        return violations
    
    def _validate_crm_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate CRM-specific Nigerian business rules."""
        violations = []
        
        # CRM transactions often represent services
        if hasattr(transaction, 'service_type') and transaction.service_type:
            # Validate professional service billing requirements
            if transaction.service_type.lower() in ['consulting', 'legal', 'accounting', 'medical']:
                if not hasattr(transaction, 'professional_license') or not transaction.professional_license:
                    violations.append(BusinessRuleViolation(
                        rule_id='CRM_PROFESSIONAL_LICENSE',
                        rule_name='Professional License Required',
                        category=RuleCategory.SECTOR_SPECIFIC,
                        level=ComplianceLevel.WARNING,
                        description='Professional services should include license information',
                        field_name='professional_license',
                        remediation_hint='Include relevant professional license numbers'
                    ))
        
        # Validate customer information completeness
        if not hasattr(transaction, 'customer_name') or not transaction.customer_name:
            violations.append(BusinessRuleViolation(
                rule_id='CRM_CUSTOMER_REQUIRED',
                rule_name='Customer Information Required',
                category=RuleCategory.DATA_QUALITY,
                level=ComplianceLevel.ERROR,
                description='CRM transactions must include customer information',
                field_name='customer_name',
                remediation_hint='Ensure customer details are properly captured'
            ))
        
        return violations
    
    def _validate_pos_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate POS-specific Nigerian business rules."""
        violations = []
        
        # POS transactions must have receipt information
        if not hasattr(transaction, 'receipt_number') or not transaction.receipt_number:
            violations.append(BusinessRuleViolation(
                rule_id='POS_RECEIPT_REQUIRED',
                rule_name='Receipt Number Required',
                category=RuleCategory.CONSUMER_PROTECTION,
                level=ComplianceLevel.ERROR,
                description='POS transactions must generate receipt numbers',
                field_name='receipt_number',
                remediation_hint='Ensure POS system generates sequential receipt numbers'
            ))
        
        # Validate terminal ID for POS transactions
        if not hasattr(transaction, 'terminal_id') or not transaction.terminal_id:
            violations.append(BusinessRuleViolation(
                rule_id='POS_TERMINAL_ID_REQUIRED',
                rule_name='Terminal ID Required',
                category=RuleCategory.DATA_QUALITY,
                level=ComplianceLevel.ERROR,
                description='POS transactions must include terminal identification',
                field_name='terminal_id',
                remediation_hint='Include POS terminal ID in transaction data'
            ))
        
        # Check for cash transactions above certain limits
        amount = getattr(transaction, 'amount', 0)
        payment_method = getattr(transaction, 'payment_method', '').lower()
        if payment_method == 'cash' and amount > 500000:  # ₦500,000
            violations.append(BusinessRuleViolation(
                rule_id='POS_LARGE_CASH_TRANSACTION',
                rule_name='Large Cash Transaction Alert',
                category=RuleCategory.FINANCIAL_REGULATIONS,
                level=ComplianceLevel.WARNING,
                description='Large cash transactions may require additional documentation',
                field_name='payment_method',
                current_value=payment_method,
                remediation_hint='Consider documenting source of large cash payments'
            ))
        
        return violations
    
    def _validate_ecommerce_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate E-commerce-specific Nigerian business rules."""
        violations = []
        
        # E-commerce must have shipping information for physical goods
        if hasattr(transaction, 'product_type') and transaction.product_type == 'physical':
            if not hasattr(transaction, 'shipping_address') or not transaction.shipping_address:
                violations.append(BusinessRuleViolation(
                    rule_id='ECOMMERCE_SHIPPING_REQUIRED',
                    rule_name='Shipping Address Required',
                    category=RuleCategory.CONSUMER_PROTECTION,
                    level=ComplianceLevel.ERROR,
                    description='Physical goods must include shipping information',
                    field_name='shipping_address',
                    remediation_hint='Collect complete shipping address for physical products'
                ))
        
        # Validate digital product delivery confirmation
        if hasattr(transaction, 'product_type') and transaction.product_type == 'digital':
            if not hasattr(transaction, 'delivery_confirmation') or not transaction.delivery_confirmation:
                violations.append(BusinessRuleViolation(
                    rule_id='ECOMMERCE_DIGITAL_DELIVERY',
                    rule_name='Digital Delivery Confirmation',
                    category=RuleCategory.CONSUMER_PROTECTION,
                    level=ComplianceLevel.WARNING,
                    description='Digital products should have delivery confirmation',
                    field_name='delivery_confirmation',
                    remediation_hint='Implement delivery confirmation for digital products'
                ))
        
        # Validate payment gateway compliance
        if hasattr(transaction, 'payment_gateway'):
            if not self._validate_nigerian_payment_gateway(transaction.payment_gateway):
                violations.append(BusinessRuleViolation(
                    rule_id='ECOMMERCE_PAYMENT_GATEWAY',
                    rule_name='Payment Gateway Compliance',
                    category=RuleCategory.FINANCIAL_REGULATIONS,
                    level=ComplianceLevel.WARNING,
                    description='Payment gateway should be CBN-licensed',
                    field_name='payment_gateway',
                    current_value=transaction.payment_gateway,
                    remediation_hint='Use CBN-licensed payment gateways for Nigerian transactions'
                ))
        
        return violations
    
    def _validate_accounting_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate Accounting system-specific rules."""
        violations = []
        
        # Accounting systems must follow double-entry bookkeeping
        if hasattr(transaction, 'debit_account') and hasattr(transaction, 'credit_account'):
            if not transaction.debit_account or not transaction.credit_account:
                violations.append(BusinessRuleViolation(
                    rule_id='ACCOUNTING_DOUBLE_ENTRY',
                    rule_name='Double Entry Bookkeeping Required',
                    category=RuleCategory.ACCOUNTING_STANDARDS,
                    level=ComplianceLevel.ERROR,
                    description='Transactions must follow double-entry bookkeeping principles',
                    remediation_hint='Ensure both debit and credit accounts are specified'
                ))
        
        # Validate journal reference
        if not hasattr(transaction, 'journal_reference') or not transaction.journal_reference:
            violations.append(BusinessRuleViolation(
                rule_id='ACCOUNTING_JOURNAL_REF',
                rule_name='Journal Reference Required',
                category=RuleCategory.ACCOUNTING_STANDARDS,
                level=ComplianceLevel.WARNING,
                description='Accounting transactions should have journal references',
                field_name='journal_reference',
                remediation_hint='Include journal reference for audit trail'
            ))
        
        return violations
    
    def _validate_banking_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate Banking data-specific rules."""
        violations = []
        
        # Banking transactions must have proper identification
        if not hasattr(transaction, 'bank_reference') or not transaction.bank_reference:
            violations.append(BusinessRuleViolation(
                rule_id='BANKING_REFERENCE_REQUIRED',
                rule_name='Bank Reference Required',
                category=RuleCategory.FINANCIAL_REGULATIONS,
                level=ComplianceLevel.ERROR,
                description='Banking transactions must include bank reference numbers',
                field_name='bank_reference',
                remediation_hint='Ensure bank reference number is captured'
            ))
        
        # Validate account number format
        if hasattr(transaction, 'account_number') and transaction.account_number:
            if not self._validate_nigerian_account_number(transaction.account_number):
                violations.append(BusinessRuleViolation(
                    rule_id='BANKING_ACCOUNT_FORMAT',
                    rule_name='Invalid Account Number Format',
                    category=RuleCategory.DATA_QUALITY,
                    level=ComplianceLevel.ERROR,
                    description='Account number format is invalid',
                    field_name='account_number',
                    current_value=transaction.account_number,
                    remediation_hint='Verify account number format (typically 10 digits)'
                ))
        
        return violations
    
    def _validate_universal_rules(
        self,
        transaction: Any,
        connector_type: ConnectorType
    ) -> List[BusinessRuleViolation]:
        """Validate universal Nigerian business rules applicable to all connectors."""
        violations = []
        
        # Validate VAT calculations
        if hasattr(transaction, 'vat_amount') and hasattr(transaction, 'subtotal'):
            vat_amount = Decimal(str(transaction.vat_amount or 0))
            subtotal = Decimal(str(transaction.subtotal or 0))
            
            if subtotal > 0:
                calculated_vat = subtotal * self.current_vat_rate
                vat_difference = abs(vat_amount - calculated_vat)
                
                # Allow for small rounding differences
                if vat_difference > Decimal('0.01'):
                    violations.append(BusinessRuleViolation(
                        rule_id='UNIVERSAL_VAT_CALCULATION',
                        rule_name='VAT Calculation Error',
                        category=RuleCategory.TAX_COMPLIANCE,
                        level=ComplianceLevel.ERROR,
                        description=f'VAT amount {vat_amount} does not match calculated VAT {calculated_vat}',
                        field_name='vat_amount',
                        current_value=float(vat_amount),
                        expected_value=float(calculated_vat),
                        remediation_hint='Recalculate VAT using current rate of 7.5%'
                    ))
        
        # Validate transaction date is not in the future
        if hasattr(transaction, 'transaction_date') and transaction.transaction_date:
            if isinstance(transaction.transaction_date, datetime):
                if transaction.transaction_date > datetime.now():
                    violations.append(BusinessRuleViolation(
                        rule_id='UNIVERSAL_FUTURE_DATE',
                        rule_name='Future Transaction Date',
                        category=RuleCategory.DATA_QUALITY,
                        level=ComplianceLevel.ERROR,
                        description='Transaction date cannot be in the future',
                        field_name='transaction_date',
                        current_value=transaction.transaction_date.isoformat(),
                        remediation_hint='Verify transaction date is correct'
                    ))
        
        # Validate currency for Nigerian businesses
        if hasattr(transaction, 'currency') and transaction.currency:
            if transaction.currency != self.nigerian_currency:
                # Foreign currency transactions need special handling
                violations.append(BusinessRuleViolation(
                    rule_id='UNIVERSAL_FOREIGN_CURRENCY',
                    rule_name='Foreign Currency Transaction',
                    category=RuleCategory.FINANCIAL_REGULATIONS,
                    level=ComplianceLevel.WARNING,
                    description='Foreign currency transactions require CBN compliance',
                    field_name='currency',
                    current_value=transaction.currency,
                    expected_value=self.nigerian_currency,
                    remediation_hint='Ensure CBN foreign exchange regulations are followed'
                ))
        
        # Validate mandatory description
        if not hasattr(transaction, 'description') or not transaction.description:
            violations.append(BusinessRuleViolation(
                rule_id='UNIVERSAL_DESCRIPTION_REQUIRED',
                rule_name='Transaction Description Required',
                category=RuleCategory.DATA_QUALITY,
                level=ComplianceLevel.ERROR,
                description='All transactions must have meaningful descriptions',
                field_name='description',
                remediation_hint='Add descriptive information about the transaction'
            ))
        
        return violations
    
    def _validate_nigerian_invoice_numbering(self, invoice_number: str) -> bool:
        """Validate Nigerian invoice numbering standards."""
        # Nigerian invoice numbers should be sequential and may have prefixes
        # Example formats: INV-2024-001, 2024/001, etc.
        pattern = r'^[A-Z]*-?\d{4}[-/]?\d{3,6}$'
        return bool(re.match(pattern, invoice_number))
    
    def _validate_nigerian_account_number(self, account_number: str) -> bool:
        """Validate Nigerian bank account number format."""
        # Nigerian account numbers are typically 10 digits
        return bool(re.match(r'^\d{10}$', account_number))
    
    def _validate_nigerian_payment_gateway(self, gateway_name: str) -> bool:
        """Validate if payment gateway is CBN-licensed."""
        # List of major CBN-licensed payment gateways
        licensed_gateways = [
            'paystack', 'flutterwave', 'interswitch', 'remita',
            'payattitude', 'gtpay', 'etranzact', 'quickteller'
        ]
        return gateway_name.lower() in licensed_gateways
    
    def _generate_recommendations(
        self,
        violations: List[BusinessRuleViolation],
        connector_type: ConnectorType
    ) -> List[str]:
        """Generate actionable recommendations based on violations."""
        recommendations = []
        
        # Count violations by category
        violation_counts = {}
        for violation in violations:
            violation_counts[violation.category] = violation_counts.get(violation.category, 0) + 1
        
        # Generate recommendations based on violation patterns
        if violation_counts.get(RuleCategory.TAX_COMPLIANCE, 0) > 0:
            recommendations.append(
                "Review tax calculations and ensure VAT compliance with current Nigerian rates"
            )
        
        if violation_counts.get(RuleCategory.DATA_QUALITY, 0) > 2:
            recommendations.append(
                f"Improve data quality in {connector_type.value} system - multiple fields are missing or invalid"
            )
        
        if violation_counts.get(RuleCategory.ACCOUNTING_STANDARDS, 0) > 0:
            recommendations.append(
                "Ensure accounting practices align with Nigerian accounting standards"
            )
        
        if violation_counts.get(RuleCategory.CONSUMER_PROTECTION, 0) > 0:
            recommendations.append(
                "Enhance customer-facing documentation and receipt generation"
            )
        
        # Connector-specific recommendations
        if connector_type.value.startswith('erp_'):
            recommendations.append(
                "Configure ERP system to include all required Nigerian business fields"
            )
        elif connector_type.value.startswith('pos_'):
            recommendations.append(
                "Ensure POS system captures all required receipt and terminal information"
            )
        elif connector_type.value.startswith('ecommerce_'):
            recommendations.append(
                "Review e-commerce platform settings for Nigerian consumer protection compliance"
            )
        
        return recommendations


def create_nigerian_business_rules_engine() -> NigerianBusinessRulesEngine:
    """Factory function to create Nigerian business rules engine."""
    return NigerianBusinessRulesEngine()