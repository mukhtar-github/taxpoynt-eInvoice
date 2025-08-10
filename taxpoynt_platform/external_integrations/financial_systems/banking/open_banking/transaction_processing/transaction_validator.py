"""
Transaction Validator
=====================

Validates banking transaction data integrity and format compliance.
Ensures transaction data meets quality standards before further processing.

Features:
- Multi-level validation rules
- Field-specific validation
- Data type and format checking
- Nigerian banking standards compliance
- Configurable validation severity
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, InvalidOperation
import re
import logging
from datetime import datetime

from ....connector_framework.base_banking_connector import BankTransaction

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ValidationType(Enum):
    """Types of validation checks."""
    REQUIRED_FIELD = "required_field"
    DATA_TYPE = "data_type"
    FORMAT = "format"
    RANGE = "range"
    BUSINESS_RULE = "business_rule"
    CONSISTENCY = "consistency"


@dataclass
class ValidationRule:
    """Individual validation rule definition."""
    name: str
    validation_type: ValidationType
    severity: ValidationSeverity
    field_name: str
    description: str
    validator_function: callable
    parameters: Dict[str, Any] = None
    enabled: bool = True


@dataclass
class ValidationIssue:
    """Individual validation issue found."""
    rule_name: str
    field_name: str
    severity: ValidationSeverity
    message: str
    current_value: Any = None
    expected_value: Any = None


@dataclass
class ValidationResult:
    """Result of transaction validation."""
    is_valid: bool
    transaction_id: str
    issues: List[ValidationIssue] = None
    warnings_count: int = 0
    errors_count: int = 0
    critical_count: int = 0
    validation_timestamp: datetime = None
    processing_time: float = 0.0


class TransactionValidator:
    """
    Comprehensive transaction validator for banking data.
    
    Validates transaction integrity, format compliance, and
    adherence to Nigerian banking standards.
    """
    
    def __init__(self, validation_rules: Optional[List[ValidationRule]] = None):
        self.validation_rules = validation_rules or self._create_default_rules()
        
        # Validation configuration
        self.strict_mode = False
        self.fail_on_critical = True
        self.fail_on_error = False
        
        # Nigerian banking patterns
        self.account_number_pattern = re.compile(r'^\d{10}$')
        self.bvn_pattern = re.compile(r'^\d{11}$')
        self.phone_pattern = re.compile(r'^(\+234|0)[7-9]\d{9}$')
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # Statistics
        self.stats = {
            'total_validations': 0,
            'valid_transactions': 0,
            'invalid_transactions': 0,
            'total_issues': 0,
            'issue_breakdown': {severity.value: 0 for severity in ValidationSeverity}
        }
    
    async def validate_transaction(
        self,
        transaction: BankTransaction,
        custom_rules: Optional[List[ValidationRule]] = None
    ) -> ValidationResult:
        """
        Validate a single banking transaction.
        
        Args:
            transaction: Transaction to validate
            custom_rules: Additional validation rules
            
        Returns:
            ValidationResult with validation details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Validating transaction: {transaction.id}")
            
            # Initialize result
            result = ValidationResult(
                is_valid=True,
                transaction_id=transaction.id,
                issues=[],
                validation_timestamp=start_time
            )
            
            # Apply validation rules
            applicable_rules = self.validation_rules[:]
            if custom_rules:
                applicable_rules.extend(custom_rules)
            
            for rule in applicable_rules:
                if not rule.enabled:
                    continue
                
                try:
                    issue = await self._apply_validation_rule(transaction, rule)
                    if issue:
                        result.issues.append(issue)
                        
                        # Update issue counts
                        if issue.severity == ValidationSeverity.WARNING:
                            result.warnings_count += 1
                        elif issue.severity == ValidationSeverity.ERROR:
                            result.errors_count += 1
                        elif issue.severity == ValidationSeverity.CRITICAL:
                            result.critical_count += 1
                        
                except Exception as e:
                    logger.error(f"Validation rule failed: {rule.name} - {e}")
                    # Add validation error as critical issue
                    result.issues.append(ValidationIssue(
                        rule_name=rule.name,
                        field_name=rule.field_name,
                        severity=ValidationSeverity.CRITICAL,
                        message=f"Validation rule execution failed: {e}"
                    ))
                    result.critical_count += 1
            
            # Determine overall validity
            result.is_valid = self._determine_validity(result)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Update statistics
            self._update_validation_stats(result)
            
            logger.debug(f"Validation completed: {transaction.id} - Valid: {result.is_valid}")
            return result
            
        except Exception as e:
            logger.error(f"Transaction validation failed: {transaction.id} - {e}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return ValidationResult(
                is_valid=False,
                transaction_id=transaction.id,
                issues=[ValidationIssue(
                    rule_name="validation_system",
                    field_name="system",
                    severity=ValidationSeverity.CRITICAL,
                    message=f"Validation system error: {e}"
                )],
                critical_count=1,
                validation_timestamp=start_time,
                processing_time=processing_time
            )
    
    async def validate_batch_transactions(
        self,
        transactions: List[BankTransaction],
        custom_rules: Optional[List[ValidationRule]] = None
    ) -> List[ValidationResult]:
        """
        Validate multiple transactions in batch.
        
        Args:
            transactions: List of transactions to validate
            custom_rules: Additional validation rules
            
        Returns:
            List of ValidationResult objects
        """
        logger.info(f"Batch validating {len(transactions)} transactions")
        
        results = []
        for transaction in transactions:
            result = await self.validate_transaction(transaction, custom_rules)
            results.append(result)
        
        # Log batch summary
        valid_count = sum(1 for r in results if r.is_valid)
        logger.info(f"Batch validation completed. Valid: {valid_count}/{len(transactions)}")
        
        return results
    
    async def _apply_validation_rule(
        self,
        transaction: BankTransaction,
        rule: ValidationRule
    ) -> Optional[ValidationIssue]:
        """Apply individual validation rule to transaction."""
        
        try:
            # Get field value
            field_value = getattr(transaction, rule.field_name, None)
            
            # Apply validator function
            is_valid = rule.validator_function(
                field_value, 
                transaction, 
                rule.parameters or {}
            )
            
            if not is_valid:
                return ValidationIssue(
                    rule_name=rule.name,
                    field_name=rule.field_name,
                    severity=rule.severity,
                    message=rule.description,
                    current_value=field_value
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Rule application failed: {rule.name} - {e}")
            return ValidationIssue(
                rule_name=rule.name,
                field_name=rule.field_name,
                severity=ValidationSeverity.CRITICAL,
                message=f"Rule execution error: {e}",
                current_value=None
            )
    
    def _create_default_rules(self) -> List[ValidationRule]:
        """Create default validation rules for Nigerian banking."""
        
        return [
            # Required field validations
            ValidationRule(
                name="transaction_id_required",
                validation_type=ValidationType.REQUIRED_FIELD,
                severity=ValidationSeverity.CRITICAL,
                field_name="id",
                description="Transaction ID is required",
                validator_function=self._validate_required_field
            ),
            
            ValidationRule(
                name="amount_required",
                validation_type=ValidationType.REQUIRED_FIELD,
                severity=ValidationSeverity.CRITICAL,
                field_name="amount",
                description="Transaction amount is required",
                validator_function=self._validate_required_field
            ),
            
            ValidationRule(
                name="date_required",
                validation_type=ValidationType.REQUIRED_FIELD,
                severity=ValidationSeverity.ERROR,
                field_name="date",
                description="Transaction date is required",
                validator_function=self._validate_required_field
            ),
            
            ValidationRule(
                name="account_number_required",
                validation_type=ValidationType.REQUIRED_FIELD,
                severity=ValidationSeverity.ERROR,
                field_name="account_number",
                description="Account number is required",
                validator_function=self._validate_required_field
            ),
            
            # Data type validations
            ValidationRule(
                name="amount_is_decimal",
                validation_type=ValidationType.DATA_TYPE,
                severity=ValidationSeverity.CRITICAL,
                field_name="amount",
                description="Transaction amount must be a valid decimal",
                validator_function=self._validate_decimal_type
            ),
            
            ValidationRule(
                name="date_is_datetime",
                validation_type=ValidationType.DATA_TYPE,
                severity=ValidationSeverity.ERROR,
                field_name="date",
                description="Transaction date must be a valid datetime",
                validator_function=self._validate_datetime_type
            ),
            
            # Format validations
            ValidationRule(
                name="account_number_format",
                validation_type=ValidationType.FORMAT,
                severity=ValidationSeverity.ERROR,
                field_name="account_number",
                description="Account number must be 10 digits",
                validator_function=self._validate_account_number_format
            ),
            
            ValidationRule(
                name="email_format",
                validation_type=ValidationType.FORMAT,
                severity=ValidationSeverity.WARNING,
                field_name="customer_email",
                description="Email must be valid format if provided",
                validator_function=self._validate_email_format
            ),
            
            ValidationRule(
                name="phone_format",
                validation_type=ValidationType.FORMAT,
                severity=ValidationSeverity.WARNING,
                field_name="customer_phone",
                description="Phone must be valid Nigerian format if provided",
                validator_function=self._validate_phone_format
            ),
            
            # Range validations
            ValidationRule(
                name="amount_positive",
                validation_type=ValidationType.RANGE,
                severity=ValidationSeverity.CRITICAL,
                field_name="amount",
                description="Transaction amount must be positive",
                validator_function=self._validate_positive_amount
            ),
            
            ValidationRule(
                name="amount_reasonable",
                validation_type=ValidationType.RANGE,
                severity=ValidationSeverity.WARNING,
                field_name="amount",
                description="Transaction amount seems unusually high",
                validator_function=self._validate_reasonable_amount,
                parameters={'max_amount': Decimal('100000000')}  # 100M NGN
            ),
            
            ValidationRule(
                name="date_not_future",
                validation_type=ValidationType.RANGE,
                severity=ValidationSeverity.ERROR,
                field_name="date",
                description="Transaction date cannot be in the future",
                validator_function=self._validate_date_not_future
            ),
            
            ValidationRule(
                name="date_not_too_old",
                validation_type=ValidationType.RANGE,
                severity=ValidationSeverity.WARNING,
                field_name="date",
                description="Transaction date is very old",
                validator_function=self._validate_date_not_too_old,
                parameters={'max_days_old': 365}  # 1 year
            ),
            
            # Business rule validations
            ValidationRule(
                name="currency_is_ngn",
                validation_type=ValidationType.BUSINESS_RULE,
                severity=ValidationSeverity.WARNING,
                field_name="currency",
                description="Transaction currency should be NGN for Nigerian banks",
                validator_function=self._validate_nigerian_currency
            ),
            
            # Consistency validations
            ValidationRule(
                name="description_consistency",
                validation_type=ValidationType.CONSISTENCY,
                severity=ValidationSeverity.WARNING,
                field_name="description",
                description="Transaction description should be meaningful",
                validator_function=self._validate_meaningful_description
            )
        ]
    
    # Validator functions
    
    def _validate_required_field(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that required field is present and not empty."""
        return value is not None and str(value).strip() != ""
    
    def _validate_decimal_type(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that value is a valid decimal."""
        if value is None:
            return True  # Required field validation handles None
        
        try:
            if isinstance(value, (int, float)):
                Decimal(str(value))
                return True
            elif isinstance(value, Decimal):
                return True
            elif isinstance(value, str):
                Decimal(value)
                return True
            return False
        except (InvalidOperation, TypeError, ValueError):
            return False
    
    def _validate_datetime_type(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that value is a valid datetime."""
        return isinstance(value, datetime) or value is None
    
    def _validate_account_number_format(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate Nigerian account number format (10 digits)."""
        if value is None:
            return True
        return bool(self.account_number_pattern.match(str(value)))
    
    def _validate_email_format(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate email format."""
        if value is None or str(value).strip() == "":
            return True
        return bool(self.email_pattern.match(str(value)))
    
    def _validate_phone_format(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate Nigerian phone number format."""
        if value is None or str(value).strip() == "":
            return True
        return bool(self.phone_pattern.match(str(value)))
    
    def _validate_positive_amount(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that amount is positive."""
        if value is None:
            return True
        try:
            amount = Decimal(str(value))
            return amount > 0
        except (InvalidOperation, TypeError, ValueError):
            return False
    
    def _validate_reasonable_amount(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that amount is within reasonable range."""
        if value is None:
            return True
        try:
            amount = Decimal(str(value))
            max_amount = params.get('max_amount', Decimal('100000000'))
            return amount <= max_amount
        except (InvalidOperation, TypeError, ValueError):
            return False
    
    def _validate_date_not_future(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that date is not in the future."""
        if value is None:
            return True
        if not isinstance(value, datetime):
            return False
        return value <= datetime.utcnow()
    
    def _validate_date_not_too_old(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that date is not too old."""
        if value is None:
            return True
        if not isinstance(value, datetime):
            return False
        max_days_old = params.get('max_days_old', 365)
        cutoff_date = datetime.utcnow() - timedelta(days=max_days_old)
        return value >= cutoff_date
    
    def _validate_nigerian_currency(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that currency is NGN for Nigerian transactions."""
        if value is None:
            return True  # Default to NGN
        return str(value).upper() == "NGN"
    
    def _validate_meaningful_description(self, value: Any, transaction: BankTransaction, params: Dict) -> bool:
        """Validate that description is meaningful."""
        if value is None or str(value).strip() == "":
            return False
        
        description = str(value).strip().lower()
        
        # Check for meaningless descriptions
        meaningless_patterns = [
            r'^transfer$',
            r'^payment$',
            r'^deposit$',
            r'^withdrawal$',
            r'^\d+$',  # Just numbers
            r'^[a-z]{1,3}$',  # Very short abbreviations
        ]
        
        for pattern in meaningless_patterns:
            if re.match(pattern, description):
                return False
        
        return len(description) >= 5  # At least 5 characters
    
    def _determine_validity(self, result: ValidationResult) -> bool:
        """Determine overall transaction validity based on issues."""
        
        if self.fail_on_critical and result.critical_count > 0:
            return False
        
        if self.fail_on_error and result.errors_count > 0:
            return False
        
        if self.strict_mode and (result.warnings_count > 0 or result.errors_count > 0):
            return False
        
        return result.critical_count == 0
    
    def _update_validation_stats(self, result: ValidationResult):
        """Update validation statistics."""
        
        self.stats['total_validations'] += 1
        
        if result.is_valid:
            self.stats['valid_transactions'] += 1
        else:
            self.stats['invalid_transactions'] += 1
        
        self.stats['total_issues'] += len(result.issues)
        
        for issue in result.issues:
            self.stats['issue_breakdown'][issue.severity.value] += 1
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_validations'] > 0:
            stats['validation_success_rate'] = (
                stats['valid_transactions'] / stats['total_validations']
            )
            stats['average_issues_per_transaction'] = (
                stats['total_issues'] / stats['total_validations']
            )
        else:
            stats['validation_success_rate'] = 0.0
            stats['average_issues_per_transaction'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset validation statistics."""
        
        self.stats = {
            'total_validations': 0,
            'valid_transactions': 0,
            'invalid_transactions': 0,
            'total_issues': 0,
            'issue_breakdown': {severity.value: 0 for severity in ValidationSeverity}
        }


def create_validator(validation_rules: Optional[List[ValidationRule]] = None) -> TransactionValidator:
    """Factory function to create transaction validator."""
    return TransactionValidator(validation_rules)