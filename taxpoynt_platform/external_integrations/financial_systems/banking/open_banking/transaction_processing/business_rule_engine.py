"""
Business Rule Engine
====================

Comprehensive business rule engine for Nigerian banking transactions.
Implements Nigerian banking regulations, compliance requirements, and business logic.

Features:
- Nigerian banking regulations compliance
- CBN (Central Bank of Nigeria) rules
- FIRS tax compliance rules
- Anti-money laundering (AML) rules
- Know Your Customer (KYC) requirements
- Business hour validations
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime, time, timedelta
import re
import logging

from ....connector_framework.base_banking_connector import BankTransaction

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Types of business rules."""
    REGULATORY = "regulatory"           # Regulatory compliance
    COMPLIANCE = "compliance"           # Business compliance
    OPERATIONAL = "operational"         # Operational rules
    SECURITY = "security"              # Security requirements
    BUSINESS_HOURS = "business_hours"   # Business hour restrictions
    AML = "aml"                        # Anti-money laundering
    KYC = "kyc"                        # Know Your Customer
    TAX = "tax"                        # Tax compliance


class RuleSeverity(Enum):
    """Severity levels for rule violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    REGULATORY_VIOLATION = "regulatory_violation"


class RuleStatus(Enum):
    """Status of rule evaluation."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NOT_APPLICABLE = "not_applicable"
    ERROR = "error"


@dataclass
class BusinessRule:
    """Individual business rule definition."""
    id: str
    name: str
    description: str
    rule_type: RuleType
    severity: RuleSeverity
    evaluation_function: Callable
    enabled: bool = True
    parameters: Dict[str, Any] = None
    error_message: str = ""
    warning_message: str = ""


@dataclass
class RuleResult:
    """Result of business rule evaluation."""
    rule_id: str
    rule_name: str
    status: RuleStatus
    severity: RuleSeverity
    message: str
    details: Dict[str, Any] = None
    evaluation_timestamp: datetime = None


@dataclass
class BusinessRuleEngineResult:
    """Result of complete business rule engine evaluation."""
    transaction_id: str
    overall_status: RuleStatus
    rule_results: List[RuleResult] = None
    regulatory_violations: List[RuleResult] = None
    critical_failures: List[RuleResult] = None
    warnings: List[RuleResult] = None
    evaluation_summary: Dict[str, Any] = None
    processing_time: float = 0.0


class NigerianBusinessRules:
    """
    Nigerian-specific business rules and regulations.
    
    Implements rules from:
    - Central Bank of Nigeria (CBN)
    - Federal Inland Revenue Service (FIRS) 
    - Nigerian Financial Intelligence Unit (NFIU)
    - Economic and Financial Crimes Commission (EFCC)
    """
    
    # CBN transaction limits
    CBN_INDIVIDUAL_DAILY_LIMIT = Decimal('5000000')      # 5M NGN
    CBN_CORPORATE_DAILY_LIMIT = Decimal('100000000')     # 100M NGN
    CBN_SINGLE_TRANSACTION_LIMIT = Decimal('50000000')   # 50M NGN
    
    # AML thresholds
    AML_CASH_TRANSACTION_LIMIT = Decimal('5000000')      # 5M NGN cash
    AML_SUSPICIOUS_AMOUNT = Decimal('10000000')          # 10M NGN
    AML_STRUCTURING_THRESHOLD = Decimal('10000')         # Under 10K to avoid reporting
    
    # Business hours (Nigerian time)
    BUSINESS_HOURS_START = time(8, 0)   # 8:00 AM
    BUSINESS_HOURS_END = time(18, 0)    # 6:00 PM
    WEEKEND_DAYS = [5, 6]               # Saturday, Sunday
    
    # Nigerian bank codes and patterns
    NIGERIAN_BANK_CODES = [
        '044', '023', '063', '050', '070', '011', '232', '033',
        '214', '215', '221', '058', '030', '082', '076'
    ]
    
    # Nigerian phone number pattern
    NIGERIAN_PHONE_PATTERN = re.compile(r'^(\+234|0)[7-9]\d{9}$')
    
    # BVN pattern
    BVN_PATTERN = re.compile(r'^\d{11}$')


class BusinessRuleEngine:
    """
    Comprehensive business rule engine for Nigerian banking transactions.
    
    Evaluates transactions against multiple rule categories including
    regulatory compliance, AML requirements, and operational rules.
    """
    
    def __init__(self, custom_rules: Optional[List[BusinessRule]] = None):
        self.rules = custom_rules or self._create_nigerian_rules()
        self.nigerian_rules = NigerianBusinessRules()
        
        # Rule execution settings
        self.fail_fast = False
        self.continue_on_error = True
        
        # Statistics
        self.stats = {
            'total_evaluations': 0,
            'passed_evaluations': 0,
            'failed_evaluations': 0,
            'regulatory_violations': 0,
            'rule_type_breakdown': {rule_type.value: 0 for rule_type in RuleType},
            'severity_breakdown': {severity.value: 0 for severity in RuleSeverity}
        }
    
    async def evaluate_transaction(
        self,
        transaction: BankTransaction,
        context: Optional[Dict[str, Any]] = None
    ) -> BusinessRuleEngineResult:
        """
        Evaluate transaction against all business rules.
        
        Args:
            transaction: Transaction to evaluate
            context: Additional context for rule evaluation
            
        Returns:
            BusinessRuleEngineResult with evaluation details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Evaluating business rules for transaction: {transaction.id}")
            
            # Initialize result
            result = BusinessRuleEngineResult(
                transaction_id=transaction.id,
                overall_status=RuleStatus.PASSED,
                rule_results=[],
                regulatory_violations=[],
                critical_failures=[],
                warnings=[]
            )
            
            # Evaluate each rule
            for rule in self.rules:
                if not rule.enabled:
                    continue
                
                try:
                    rule_result = await self._evaluate_rule(transaction, rule, context)
                    result.rule_results.append(rule_result)
                    
                    # Categorize results
                    if rule_result.status == RuleStatus.FAILED:
                        if rule_result.severity == RuleSeverity.REGULATORY_VIOLATION:
                            result.regulatory_violations.append(rule_result)
                        elif rule_result.severity == RuleSeverity.CRITICAL:
                            result.critical_failures.append(rule_result)
                    elif rule_result.status == RuleStatus.WARNING:
                        result.warnings.append(rule_result)
                    
                    # Update statistics
                    self.stats['rule_type_breakdown'][rule.rule_type.value] += 1
                    self.stats['severity_breakdown'][rule.severity.value] += 1
                    
                    # Fail fast if configured
                    if (self.fail_fast and 
                        rule_result.status == RuleStatus.FAILED and 
                        rule_result.severity in [RuleSeverity.CRITICAL, RuleSeverity.REGULATORY_VIOLATION]):
                        break
                        
                except Exception as e:
                    logger.error(f"Rule evaluation failed: {rule.id} - {e}")
                    
                    if not self.continue_on_error:
                        raise
                    
                    # Add error result
                    error_result = RuleResult(
                        rule_id=rule.id,
                        rule_name=rule.name,
                        status=RuleStatus.ERROR,
                        severity=RuleSeverity.CRITICAL,
                        message=f"Rule evaluation error: {e}",
                        evaluation_timestamp=datetime.utcnow()
                    )
                    result.rule_results.append(error_result)
                    result.critical_failures.append(error_result)
            
            # Determine overall status
            result.overall_status = self._determine_overall_status(result)
            
            # Generate evaluation summary
            result.evaluation_summary = self._generate_evaluation_summary(result)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Update statistics
            self._update_evaluation_stats(result)
            
            logger.debug(f"Business rule evaluation completed: {transaction.id} - Status: {result.overall_status.value}")
            return result
            
        except Exception as e:
            logger.error(f"Business rule evaluation failed: {transaction.id} - {e}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return BusinessRuleEngineResult(
                transaction_id=transaction.id,
                overall_status=RuleStatus.ERROR,
                rule_results=[RuleResult(
                    rule_id="system_error",
                    rule_name="System Error",
                    status=RuleStatus.ERROR,
                    severity=RuleSeverity.CRITICAL,
                    message=f"Rule engine error: {e}",
                    evaluation_timestamp=start_time
                )],
                critical_failures=[],
                processing_time=processing_time
            )
    
    async def evaluate_batch_transactions(
        self,
        transactions: List[BankTransaction],
        context: Optional[Dict[str, Any]] = None
    ) -> List[BusinessRuleEngineResult]:
        """
        Evaluate multiple transactions against business rules.
        
        Args:
            transactions: List of transactions to evaluate
            context: Additional context for rule evaluation
            
        Returns:
            List of BusinessRuleEngineResult objects
        """
        logger.info(f"Batch evaluating business rules for {len(transactions)} transactions")
        
        results = []
        for transaction in transactions:
            result = await self.evaluate_transaction(transaction, context)
            results.append(result)
        
        # Log batch summary
        failed_count = sum(1 for r in results if r.overall_status == RuleStatus.FAILED)
        violation_count = sum(len(r.regulatory_violations) for r in results)
        
        logger.info(f"Batch rule evaluation completed. Failed: {failed_count}, Violations: {violation_count}")
        
        return results
    
    async def _evaluate_rule(
        self,
        transaction: BankTransaction,
        rule: BusinessRule,
        context: Optional[Dict[str, Any]]
    ) -> RuleResult:
        """Evaluate individual business rule."""
        
        try:
            # Prepare rule context
            rule_context = {
                'transaction': transaction,
                'context': context or {},
                'parameters': rule.parameters or {},
                'nigerian_rules': self.nigerian_rules
            }
            
            # Execute rule function
            evaluation_result = rule.evaluation_function(**rule_context)
            
            # Handle different return types
            if isinstance(evaluation_result, bool):
                status = RuleStatus.PASSED if evaluation_result else RuleStatus.FAILED
                message = rule.error_message if not evaluation_result else "Rule passed"
            elif isinstance(evaluation_result, dict):
                status = evaluation_result.get('status', RuleStatus.ERROR)
                message = evaluation_result.get('message', 'No message provided')
            else:
                status = RuleStatus.ERROR
                message = f"Invalid rule return type: {type(evaluation_result)}"
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                status=status,
                severity=rule.severity,
                message=message,
                details=evaluation_result if isinstance(evaluation_result, dict) else None,
                evaluation_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Rule evaluation failed: {rule.id} - {e}")
            
            return RuleResult(
                rule_id=rule.id,
                rule_name=rule.name,
                status=RuleStatus.ERROR,
                severity=RuleSeverity.CRITICAL,
                message=f"Rule execution error: {e}",
                evaluation_timestamp=datetime.utcnow()
            )
    
    def _create_nigerian_rules(self) -> List[BusinessRule]:
        """Create Nigerian banking business rules."""
        
        return [
            # CBN Transaction Limits
            BusinessRule(
                id="cbn_single_transaction_limit",
                name="CBN Single Transaction Limit",
                description="Enforce CBN single transaction limits",
                rule_type=RuleType.REGULATORY,
                severity=RuleSeverity.REGULATORY_VIOLATION,
                evaluation_function=self._rule_cbn_single_transaction_limit,
                error_message="Transaction exceeds CBN single transaction limit"
            ),
            
            BusinessRule(
                id="cbn_daily_limit_individual",
                name="CBN Daily Limit (Individual)",
                description="Enforce CBN daily limits for individual accounts",
                rule_type=RuleType.REGULATORY,
                severity=RuleSeverity.REGULATORY_VIOLATION,
                evaluation_function=self._rule_cbn_daily_limit,
                parameters={'account_type': 'individual'},
                error_message="Transaction exceeds CBN daily limit for individual accounts"
            ),
            
            # AML Rules
            BusinessRule(
                id="aml_suspicious_amount",
                name="AML Suspicious Amount",
                description="Flag transactions above AML suspicious amount threshold",
                rule_type=RuleType.AML,
                severity=RuleSeverity.WARNING,
                evaluation_function=self._rule_aml_suspicious_amount,
                warning_message="Transaction amount flagged for AML review"
            ),
            
            BusinessRule(
                id="aml_structuring_detection",
                name="AML Structuring Detection",
                description="Detect potential structuring activities",
                rule_type=RuleType.AML,
                severity=RuleSeverity.ERROR,
                evaluation_function=self._rule_aml_structuring,
                error_message="Potential structuring activity detected"
            ),
            
            # Business Hours
            BusinessRule(
                id="business_hours_restriction",
                name="Business Hours Restriction",
                description="Restrict high-value transactions outside business hours",
                rule_type=RuleType.OPERATIONAL,
                severity=RuleSeverity.WARNING,
                evaluation_function=self._rule_business_hours,
                parameters={'high_value_threshold': Decimal('1000000')},
                warning_message="High-value transaction outside business hours"
            ),
            
            # KYC Requirements
            BusinessRule(
                id="kyc_customer_identification",
                name="KYC Customer Identification",
                description="Ensure customer identification for high-value transactions",
                rule_type=RuleType.KYC,
                severity=RuleSeverity.ERROR,
                evaluation_function=self._rule_kyc_customer_identification,
                parameters={'threshold': Decimal('500000')},
                error_message="Customer identification required for high-value transaction"
            ),
            
            # Currency Rules
            BusinessRule(
                id="nigerian_currency_compliance",
                name="Nigerian Currency Compliance",
                description="Ensure transactions use Nigerian Naira",
                rule_type=RuleType.COMPLIANCE,
                severity=RuleSeverity.WARNING,
                evaluation_function=self._rule_currency_compliance,
                warning_message="Non-NGN currency detected"
            ),
            
            # Account Number Validation  
            BusinessRule(
                id="nigerian_account_format",
                name="Nigerian Account Number Format",
                description="Validate Nigerian account number format",
                rule_type=RuleType.COMPLIANCE,
                severity=RuleSeverity.ERROR,
                evaluation_function=self._rule_account_format,
                error_message="Invalid Nigerian account number format"
            ),
            
            # Tax Compliance
            BusinessRule(
                id="tax_threshold_monitoring",
                name="Tax Threshold Monitoring",
                description="Monitor transactions for tax reporting thresholds",
                rule_type=RuleType.TAX,
                severity=RuleSeverity.INFO,
                evaluation_function=self._rule_tax_threshold,
                parameters={'annual_threshold': Decimal('25000000')},
                error_message="Transaction requires tax reporting"
            ),
            
            # Security Rules
            BusinessRule(
                id="weekend_transaction_monitoring",
                name="Weekend Transaction Monitoring",
                description="Enhanced monitoring for weekend transactions",
                rule_type=RuleType.SECURITY,
                severity=RuleSeverity.WARNING,
                evaluation_function=self._rule_weekend_monitoring,
                parameters={'high_value_threshold': Decimal('5000000')},
                warning_message="High-value weekend transaction requires review"
            )
        ]
    
    # Rule implementation functions
    
    def _rule_cbn_single_transaction_limit(self, **kwargs) -> bool:
        """CBN single transaction limit rule."""
        transaction = kwargs['transaction']
        nigerian_rules = kwargs['nigerian_rules']
        
        return transaction.amount <= nigerian_rules.CBN_SINGLE_TRANSACTION_LIMIT
    
    def _rule_cbn_daily_limit(self, **kwargs) -> bool:
        """CBN daily limit rule."""
        transaction = kwargs['transaction']
        parameters = kwargs['parameters']
        nigerian_rules = kwargs['nigerian_rules']
        
        account_type = parameters.get('account_type', 'individual')
        
        if account_type == 'individual':
            limit = nigerian_rules.CBN_INDIVIDUAL_DAILY_LIMIT
        else:
            limit = nigerian_rules.CBN_CORPORATE_DAILY_LIMIT
        
        # Simplified check - in reality would check daily accumulated amount
        return transaction.amount <= limit
    
    def _rule_aml_suspicious_amount(self, **kwargs) -> Dict[str, Any]:
        """AML suspicious amount rule."""
        transaction = kwargs['transaction']
        nigerian_rules = kwargs['nigerian_rules']
        
        is_suspicious = transaction.amount >= nigerian_rules.AML_SUSPICIOUS_AMOUNT
        
        return {
            'status': RuleStatus.WARNING if is_suspicious else RuleStatus.PASSED,
            'message': 'Amount flagged for AML review' if is_suspicious else 'Amount within normal range',
            'suspicious_amount': is_suspicious,
            'threshold': str(nigerian_rules.AML_SUSPICIOUS_AMOUNT)
        }
    
    def _rule_aml_structuring(self, **kwargs) -> bool:
        """AML structuring detection rule."""
        transaction = kwargs['transaction']
        nigerian_rules = kwargs['nigerian_rules']
        
        # Check if amount is just below structuring threshold
        threshold = nigerian_rules.AML_STRUCTURING_THRESHOLD
        return not (threshold - transaction.amount < Decimal('1000') and transaction.amount < threshold)
    
    def _rule_business_hours(self, **kwargs) -> Dict[str, Any]:
        """Business hours restriction rule."""
        transaction = kwargs['transaction']
        parameters = kwargs['parameters']
        nigerian_rules = kwargs['nigerian_rules']
        
        if not transaction.date:
            return {'status': RuleStatus.NOT_APPLICABLE, 'message': 'No transaction date'}
        
        high_value_threshold = parameters.get('high_value_threshold', Decimal('1000000'))
        
        # Check if high-value transaction
        if transaction.amount < high_value_threshold:
            return {'status': RuleStatus.NOT_APPLICABLE, 'message': 'Not high-value transaction'}
        
        # Check business hours
        tx_time = transaction.date.time()
        tx_weekday = transaction.date.weekday()
        
        is_business_hours = (
            tx_weekday not in nigerian_rules.WEEKEND_DAYS and
            nigerian_rules.BUSINESS_HOURS_START <= tx_time <= nigerian_rules.BUSINESS_HOURS_END
        )
        
        return {
            'status': RuleStatus.PASSED if is_business_hours else RuleStatus.WARNING,
            'message': 'Within business hours' if is_business_hours else 'Outside business hours',
            'transaction_time': tx_time.strftime('%H:%M'),
            'is_weekend': tx_weekday in nigerian_rules.WEEKEND_DAYS
        }
    
    def _rule_kyc_customer_identification(self, **kwargs) -> bool:
        """KYC customer identification rule."""
        transaction = kwargs['transaction']
        parameters = kwargs['parameters']
        
        threshold = parameters.get('threshold', Decimal('500000'))
        
        if transaction.amount < threshold:
            return True  # Below threshold, no KYC required
        
        # Check if customer information is available
        # In reality, this would check against customer database
        return bool(transaction.customer_name or transaction.customer_email)
    
    def _rule_currency_compliance(self, **kwargs) -> bool:
        """Nigerian currency compliance rule."""
        transaction = kwargs['transaction']
        
        # Default to NGN if no currency specified
        currency = transaction.currency or 'NGN'
        return currency.upper() == 'NGN'
    
    def _rule_account_format(self, **kwargs) -> bool:
        """Nigerian account number format rule."""
        transaction = kwargs['transaction']
        
        if not transaction.account_number:
            return False
        
        # Nigerian account numbers are typically 10 digits
        return len(transaction.account_number) == 10 and transaction.account_number.isdigit()
    
    def _rule_tax_threshold(self, **kwargs) -> Dict[str, Any]:
        """Tax threshold monitoring rule."""
        transaction = kwargs['transaction']
        parameters = kwargs['parameters']
        
        annual_threshold = parameters.get('annual_threshold', Decimal('25000000'))
        
        # Simplified check - in reality would check annual accumulated
        requires_reporting = transaction.amount >= annual_threshold / 365  # Daily equivalent
        
        return {
            'status': RuleStatus.INFO,
            'message': 'Tax reporting may be required' if requires_reporting else 'Below tax reporting threshold',
            'requires_reporting': requires_reporting,
            'annual_threshold': str(annual_threshold)
        }
    
    def _rule_weekend_monitoring(self, **kwargs) -> Dict[str, Any]:
        """Weekend transaction monitoring rule."""
        transaction = kwargs['transaction']
        parameters = kwargs['parameters']
        nigerian_rules = kwargs['nigerian_rules']
        
        if not transaction.date:
            return {'status': RuleStatus.NOT_APPLICABLE, 'message': 'No transaction date'}
        
        high_value_threshold = parameters.get('high_value_threshold', Decimal('5000000'))
        
        is_weekend = transaction.date.weekday() in nigerian_rules.WEEKEND_DAYS
        is_high_value = transaction.amount >= high_value_threshold
        
        requires_review = is_weekend and is_high_value
        
        return {
            'status': RuleStatus.WARNING if requires_review else RuleStatus.PASSED,
            'message': 'Weekend high-value transaction' if requires_review else 'Normal transaction',
            'is_weekend': is_weekend,
            'is_high_value': is_high_value
        }
    
    def _determine_overall_status(self, result: BusinessRuleEngineResult) -> RuleStatus:
        """Determine overall status from individual rule results."""
        
        if result.regulatory_violations:
            return RuleStatus.FAILED
        
        if result.critical_failures:
            return RuleStatus.FAILED
        
        if any(r.status == RuleStatus.ERROR for r in result.rule_results):
            return RuleStatus.ERROR
        
        if result.warnings:
            return RuleStatus.WARNING
        
        return RuleStatus.PASSED
    
    def _generate_evaluation_summary(self, result: BusinessRuleEngineResult) -> Dict[str, Any]:
        """Generate evaluation summary."""
        
        return {
            'total_rules_evaluated': len(result.rule_results),
            'passed_rules': len([r for r in result.rule_results if r.status == RuleStatus.PASSED]),
            'failed_rules': len([r for r in result.rule_results if r.status == RuleStatus.FAILED]),
            'warning_rules': len(result.warnings),
            'error_rules': len([r for r in result.rule_results if r.status == RuleStatus.ERROR]),
            'regulatory_violations_count': len(result.regulatory_violations),
            'critical_failures_count': len(result.critical_failures),
            'overall_compliance': result.overall_status == RuleStatus.PASSED
        }
    
    def _update_evaluation_stats(self, result: BusinessRuleEngineResult):
        """Update evaluation statistics."""
        
        self.stats['total_evaluations'] += 1
        
        if result.overall_status == RuleStatus.PASSED:
            self.stats['passed_evaluations'] += 1
        else:
            self.stats['failed_evaluations'] += 1
        
        if result.regulatory_violations:
            self.stats['regulatory_violations'] += len(result.regulatory_violations)
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """Get business rule evaluation statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_evaluations'] > 0:
            stats['pass_rate'] = stats['passed_evaluations'] / stats['total_evaluations']
            stats['failure_rate'] = stats['failed_evaluations'] / stats['total_evaluations']
            stats['violation_rate'] = stats['regulatory_violations'] / stats['total_evaluations']
        else:
            stats['pass_rate'] = 0.0
            stats['failure_rate'] = 0.0
            stats['violation_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset rule evaluation statistics."""
        
        self.stats = {
            'total_evaluations': 0,
            'passed_evaluations': 0,
            'failed_evaluations': 0,
            'regulatory_violations': 0,
            'rule_type_breakdown': {rule_type.value: 0 for rule_type in RuleType},
            'severity_breakdown': {severity.value: 0 for severity in RuleSeverity}
        }


def create_business_rule_engine(
    custom_rules: Optional[List[BusinessRule]] = None
) -> BusinessRuleEngine:
    """Factory function to create business rule engine."""
    return BusinessRuleEngine(custom_rules)