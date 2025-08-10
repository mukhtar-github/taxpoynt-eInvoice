"""
Amount Validator
================

Advanced amount validation and fraud detection for Nigerian banking transactions.
Implements sophisticated algorithms to detect suspicious amounts, patterns, and potential fraud.

Features:
- Multi-layered fraud detection
- Nigerian banking amount patterns
- Statistical anomaly detection
- Machine learning-based risk scoring
- Velocity checks and limits
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import statistics
import logging
from collections import defaultdict, deque

from ....connector_framework.base_banking_connector import BankTransaction

logger = logging.getLogger(__name__)


class FraudRisk(Enum):
    """Fraud risk levels for amounts."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"


class AmountFlag(Enum):
    """Types of amount validation flags."""
    ROUND_NUMBER = "round_number"           # Suspicious round numbers
    UNUSUAL_DECIMAL = "unusual_decimal"     # Strange decimal patterns
    VELOCITY_EXCEEDED = "velocity_exceeded" # Too many transactions
    LIMIT_EXCEEDED = "limit_exceeded"       # Amount limits exceeded
    PATTERN_ANOMALY = "pattern_anomaly"     # Unusual pattern detected
    STATISTICAL_OUTLIER = "statistical_outlier"  # Statistical anomaly
    SUSPECTED_STRUCTURING = "suspected_structuring"  # Possible structuring
    CURRENCY_MISMATCH = "currency_mismatch" # Currency inconsistencies


@dataclass
class AmountThreshold:
    """Amount validation threshold configuration."""
    name: str
    threshold_type: str
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    daily_limit: Optional[Decimal] = None
    monthly_limit: Optional[Decimal] = None
    transaction_count_limit: Optional[int] = None
    time_window_minutes: Optional[int] = None
    enabled: bool = True


@dataclass
class AmountValidationResult:
    """Result of amount validation and fraud detection."""
    transaction_id: str
    amount: Decimal
    is_valid: bool
    risk_level: FraudRisk
    risk_score: float  # 0.0 to 1.0
    flags: List[AmountFlag] = None
    warnings: List[str] = None
    fraud_indicators: Dict[str, Any] = None
    validation_timestamp: datetime = None
    processing_notes: List[str] = None


@dataclass
class VelocityMetrics:
    """Transaction velocity metrics for an account."""
    account_number: str
    transaction_count_1h: int = 0
    transaction_count_24h: int = 0
    transaction_count_7d: int = 0
    total_amount_1h: Decimal = Decimal('0')
    total_amount_24h: Decimal = Decimal('0')
    total_amount_7d: Decimal = Decimal('0')
    last_updated: datetime = None


class AmountValidator:
    """
    Advanced amount validator with fraud detection capabilities.
    
    Analyzes transaction amounts using multiple techniques including
    statistical analysis, pattern recognition, and velocity checking
    to detect potentially fraudulent transactions.
    """
    
    def __init__(
        self,
        thresholds: Optional[List[AmountThreshold]] = None,
        enable_ml_scoring: bool = False
    ):
        self.thresholds = thresholds or self._create_default_thresholds()
        self.enable_ml_scoring = enable_ml_scoring
        
        # Nigerian banking configuration
        self.max_single_transaction = Decimal('50000000')  # 50M NGN
        self.daily_limit_individual = Decimal('5000000')   # 5M NGN
        self.daily_limit_corporate = Decimal('100000000')  # 100M NGN
        self.structuring_threshold = Decimal('10000')      # Structuring detection
        
        # Velocity tracking
        self.velocity_window = timedelta(hours=24)
        self.velocity_cache: Dict[str, VelocityMetrics] = {}
        self.transaction_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Pattern analysis
        self.suspicious_round_amounts = [
            Decimal('100000'), Decimal('500000'), Decimal('1000000'),
            Decimal('5000000'), Decimal('10000000')
        ]
        
        # Statistics tracking
        self.stats = {
            'total_validations': 0,
            'fraud_detected': 0,
            'risk_level_breakdown': {risk.value: 0 for risk in FraudRisk},
            'flag_breakdown': {flag.value: 0 for flag in AmountFlag}
        }
    
    async def validate_amount(
        self,
        transaction: BankTransaction,
        historical_context: Optional[List[BankTransaction]] = None
    ) -> AmountValidationResult:
        """
        Validate transaction amount and detect potential fraud.
        
        Args:
            transaction: Transaction to validate
            historical_context: Historical transactions for context
            
        Returns:
            AmountValidationResult with validation details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Validating amount for transaction: {transaction.id}")
            
            # Initialize result
            result = AmountValidationResult(
                transaction_id=transaction.id,
                amount=transaction.amount,
                is_valid=True,
                risk_level=FraudRisk.VERY_LOW,
                risk_score=0.0,
                flags=[],
                warnings=[],
                fraud_indicators={},
                validation_timestamp=start_time,
                processing_notes=[]
            )
            
            # Basic amount validation
            basic_flags = self._basic_amount_validation(transaction)
            result.flags.extend(basic_flags)
            
            # Threshold validation
            threshold_flags = await self._threshold_validation(transaction)
            result.flags.extend(threshold_flags)
            
            # Velocity validation
            velocity_flags = await self._velocity_validation(transaction)
            result.flags.extend(velocity_flags)
            
            # Pattern analysis
            pattern_flags = self._pattern_analysis(transaction, historical_context)
            result.flags.extend(pattern_flags)
            
            # Statistical analysis
            if historical_context:
                statistical_flags = self._statistical_analysis(transaction, historical_context)
                result.flags.extend(statistical_flags)
            
            # Structuring detection
            structuring_flags = await self._structuring_detection(transaction)
            result.flags.extend(structuring_flags)
            
            # Calculate risk score
            result.risk_score = self._calculate_risk_score(result.flags, transaction)
            result.risk_level = self._score_to_risk_level(result.risk_score)
            
            # Generate fraud indicators
            result.fraud_indicators = self._generate_fraud_indicators(result.flags, transaction)
            
            # Generate warnings
            result.warnings = self._generate_warnings(result.flags, result.risk_level)
            
            # Determine validity
            result.is_valid = self._determine_validity(result.risk_level, result.flags)
            
            # Update velocity tracking
            await self._update_velocity_tracking(transaction)
            
            # Update statistics
            self._update_validation_stats(result)
            
            logger.debug(f"Amount validation completed: {transaction.id} - Risk: {result.risk_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Amount validation failed: {transaction.id} - {e}")
            
            return AmountValidationResult(
                transaction_id=transaction.id,
                amount=transaction.amount,
                is_valid=False,
                risk_level=FraudRisk.CRITICAL,
                risk_score=1.0,
                warnings=[f"Validation error: {e}"],
                validation_timestamp=start_time
            )
    
    async def validate_batch_amounts(
        self,
        transactions: List[BankTransaction]
    ) -> List[AmountValidationResult]:
        """
        Validate multiple transaction amounts in batch.
        
        Args:
            transactions: List of transactions to validate
            
        Returns:
            List of AmountValidationResult objects
        """
        logger.info(f"Batch validating amounts for {len(transactions)} transactions")
        
        results = []
        
        # Sort by account and date for better context analysis
        sorted_transactions = sorted(
            transactions, 
            key=lambda t: (t.account_number or '', t.date or datetime.min)
        )
        
        for i, transaction in enumerate(sorted_transactions):
            # Use previous transactions as historical context
            historical_context = sorted_transactions[:i] if i > 0 else []
            
            result = await self.validate_amount(transaction, historical_context)
            results.append(result)
        
        # Cross-transaction analysis
        await self._cross_transaction_analysis(sorted_transactions, results)
        
        # Log batch summary
        fraud_count = sum(1 for r in results if r.risk_level in [FraudRisk.HIGH, FraudRisk.VERY_HIGH, FraudRisk.CRITICAL])
        logger.info(f"Batch amount validation completed. Potential fraud: {fraud_count}/{len(transactions)}")
        
        return results
    
    def _basic_amount_validation(self, transaction: BankTransaction) -> List[AmountFlag]:
        """Perform basic amount validation checks."""
        
        flags = []
        amount = transaction.amount
        
        if not amount or amount <= 0:
            # This should be caught by transaction validator, but double-check
            return flags
        
        # Check for suspicious round numbers
        if amount in self.suspicious_round_amounts:
            flags.append(AmountFlag.ROUND_NUMBER)
        elif amount % Decimal('100000') == 0 and amount >= Decimal('100000'):
            flags.append(AmountFlag.ROUND_NUMBER)
        
        # Check for unusual decimal patterns
        decimal_places = abs(amount.as_tuple().exponent)
        if decimal_places > 2:
            flags.append(AmountFlag.UNUSUAL_DECIMAL)
        elif decimal_places == 0 and amount >= Decimal('1000'):
            # Large amounts with no decimals can be suspicious
            flags.append(AmountFlag.UNUSUAL_DECIMAL)
        
        # Check against maximum limits
        if amount > self.max_single_transaction:
            flags.append(AmountFlag.LIMIT_EXCEEDED)
        
        return flags
    
    async def _threshold_validation(self, transaction: BankTransaction) -> List[AmountFlag]:
        """Validate against configured thresholds."""
        
        flags = []
        
        for threshold in self.thresholds:
            if not threshold.enabled:
                continue
            
            # Check amount range
            if threshold.min_amount and transaction.amount < threshold.min_amount:
                continue
            if threshold.max_amount and transaction.amount > threshold.max_amount:
                flags.append(AmountFlag.LIMIT_EXCEEDED)
                continue
            
            # Daily limit validation would require historical data
            # This is a simplified version
            if threshold.daily_limit and transaction.amount > threshold.daily_limit:
                flags.append(AmountFlag.LIMIT_EXCEEDED)
        
        return flags
    
    async def _velocity_validation(self, transaction: BankTransaction) -> List[AmountFlag]:
        """Validate transaction velocity patterns."""
        
        flags = []
        account_number = transaction.account_number
        
        if not account_number:
            return flags
        
        # Get or create velocity metrics
        velocity = self.velocity_cache.get(account_number)
        if not velocity:
            velocity = VelocityMetrics(account_number=account_number)
            self.velocity_cache[account_number] = velocity
        
        # Check velocity limits (simplified - would use real historical data)
        if velocity.transaction_count_1h > 50:  # More than 50 transactions per hour
            flags.append(AmountFlag.VELOCITY_EXCEEDED)
        
        if velocity.total_amount_1h > Decimal('10000000'):  # More than 10M NGN per hour
            flags.append(AmountFlag.VELOCITY_EXCEEDED)
        
        return flags
    
    def _pattern_analysis(
        self, 
        transaction: BankTransaction, 
        historical_context: Optional[List[BankTransaction]]
    ) -> List[AmountFlag]:
        """Analyze transaction patterns for anomalies."""
        
        flags = []
        
        if not historical_context:
            return flags
        
        # Filter transactions for same account
        account_transactions = [
            t for t in historical_context 
            if t.account_number == transaction.account_number
        ]
        
        if len(account_transactions) < 5:  # Need minimum history
            return flags
        
        # Analyze recent transactions
        recent_transactions = account_transactions[-10:]  # Last 10 transactions
        amounts = [t.amount for t in recent_transactions]
        
        # Check for identical amounts (possible automation/fraud)
        if amounts.count(transaction.amount) >= 3:
            flags.append(AmountFlag.PATTERN_ANOMALY)
        
        # Check for incremental patterns
        if len(amounts) >= 3:
            diffs = [amounts[i+1] - amounts[i] for i in range(len(amounts)-1)]
            if len(set(diffs)) == 1 and diffs[0] != 0:  # Same increment
                flags.append(AmountFlag.PATTERN_ANOMALY)
        
        return flags
    
    def _statistical_analysis(
        self, 
        transaction: BankTransaction, 
        historical_context: List[BankTransaction]
    ) -> List[AmountFlag]:
        """Perform statistical analysis on transaction amounts."""
        
        flags = []
        
        # Filter for same account
        account_transactions = [
            t for t in historical_context 
            if t.account_number == transaction.account_number
        ]
        
        if len(account_transactions) < 10:  # Need sufficient history
            return flags
        
        amounts = [float(t.amount) for t in account_transactions]
        current_amount = float(transaction.amount)
        
        try:
            # Calculate statistical measures
            mean_amount = statistics.mean(amounts)
            median_amount = statistics.median(amounts)
            
            if len(amounts) > 1:
                stdev_amount = statistics.stdev(amounts)
                
                # Z-score analysis
                if stdev_amount > 0:
                    z_score = abs(current_amount - mean_amount) / stdev_amount
                    
                    if z_score > 3:  # More than 3 standard deviations
                        flags.append(AmountFlag.STATISTICAL_OUTLIER)
                    elif z_score > 2:  # More than 2 standard deviations
                        flags.append(AmountFlag.PATTERN_ANOMALY)
                
                # Check against median (robust to outliers)
                median_ratio = current_amount / median_amount if median_amount > 0 else 0
                if median_ratio > 10 or median_ratio < 0.1:  # 10x larger or smaller
                    flags.append(AmountFlag.STATISTICAL_OUTLIER)
        
        except statistics.StatisticsError:
            # Not enough data for statistics
            pass
        
        return flags
    
    async def _structuring_detection(self, transaction: BankTransaction) -> List[AmountFlag]:
        """Detect potential structuring (breaking large amounts into smaller ones)."""
        
        flags = []
        
        # Check if amount is just below structuring threshold
        if (self.structuring_threshold - transaction.amount) < Decimal('1000') and \
           transaction.amount < self.structuring_threshold:
            flags.append(AmountFlag.SUSPECTED_STRUCTURING)
        
        # Additional structuring detection would require historical analysis
        # of multiple transactions by same account/customer within time window
        
        return flags
    
    def _calculate_risk_score(self, flags: List[AmountFlag], transaction: BankTransaction) -> float:
        """Calculate overall risk score based on flags."""
        
        risk_weights = {
            AmountFlag.ROUND_NUMBER: 0.1,
            AmountFlag.UNUSUAL_DECIMAL: 0.05,
            AmountFlag.VELOCITY_EXCEEDED: 0.3,
            AmountFlag.LIMIT_EXCEEDED: 0.4,
            AmountFlag.PATTERN_ANOMALY: 0.2,
            AmountFlag.STATISTICAL_OUTLIER: 0.25,
            AmountFlag.SUSPECTED_STRUCTURING: 0.35,
            AmountFlag.CURRENCY_MISMATCH: 0.15
        }
        
        # Base score from flags
        score = sum(risk_weights.get(flag, 0.1) for flag in flags)
        
        # Additional scoring factors
        
        # Large amounts inherently riskier
        if transaction.amount > Decimal('10000000'):  # > 10M NGN
            score += 0.1
        elif transaction.amount > Decimal('50000000'):  # > 50M NGN
            score += 0.2
        
        # Very small amounts can also be suspicious
        if transaction.amount < Decimal('100'):  # < 100 NGN
            score += 0.05
        
        # Cap at 1.0
        return min(score, 1.0)
    
    def _score_to_risk_level(self, score: float) -> FraudRisk:
        """Convert risk score to risk level."""
        
        if score >= 0.8:
            return FraudRisk.CRITICAL
        elif score >= 0.6:
            return FraudRisk.VERY_HIGH
        elif score >= 0.4:
            return FraudRisk.HIGH
        elif score >= 0.2:
            return FraudRisk.MEDIUM
        elif score >= 0.1:
            return FraudRisk.LOW
        else:
            return FraudRisk.VERY_LOW
    
    def _generate_fraud_indicators(
        self, 
        flags: List[AmountFlag], 
        transaction: BankTransaction
    ) -> Dict[str, Any]:
        """Generate detailed fraud indicators."""
        
        indicators = {
            'flags_count': len(flags),
            'amount_analysis': {
                'amount': str(transaction.amount),
                'is_round_number': AmountFlag.ROUND_NUMBER in flags,
                'decimal_places': abs(transaction.amount.as_tuple().exponent),
                'amount_category': self._categorize_amount(transaction.amount)
            },
            'risk_factors': [flag.value for flag in flags]
        }
        
        return indicators
    
    def _categorize_amount(self, amount: Decimal) -> str:
        """Categorize amount by size."""
        
        if amount < Decimal('1000'):
            return 'micro'
        elif amount < Decimal('10000'):
            return 'small'
        elif amount < Decimal('100000'):
            return 'medium'
        elif amount < Decimal('1000000'):
            return 'large'
        elif amount < Decimal('10000000'):
            return 'very_large'
        else:
            return 'extreme'
    
    def _generate_warnings(self, flags: List[AmountFlag], risk_level: FraudRisk) -> List[str]:
        """Generate human-readable warnings."""
        
        warnings = []
        
        if AmountFlag.LIMIT_EXCEEDED in flags:
            warnings.append("Transaction amount exceeds configured limits")
        
        if AmountFlag.VELOCITY_EXCEEDED in flags:
            warnings.append("Account shows high transaction velocity")
        
        if AmountFlag.STATISTICAL_OUTLIER in flags:
            warnings.append("Amount is statistical outlier compared to account history")
        
        if AmountFlag.SUSPECTED_STRUCTURING in flags:
            warnings.append("Possible structuring activity detected")
        
        if risk_level in [FraudRisk.HIGH, FraudRisk.VERY_HIGH, FraudRisk.CRITICAL]:
            warnings.append("High fraud risk - manual review recommended")
        
        return warnings
    
    def _determine_validity(self, risk_level: FraudRisk, flags: List[AmountFlag]) -> bool:
        """Determine if transaction amount is valid based on risk assessment."""
        
        # Critical risk = invalid
        if risk_level == FraudRisk.CRITICAL:
            return False
        
        # Hard limits
        if AmountFlag.LIMIT_EXCEEDED in flags:
            return False
        
        # Otherwise valid but may require review
        return True
    
    async def _update_velocity_tracking(self, transaction: BankTransaction):
        """Update velocity tracking metrics."""
        
        account_number = transaction.account_number
        if not account_number:
            return
        
        # Add to transaction history
        self.transaction_history[account_number].append({
            'amount': transaction.amount,
            'timestamp': transaction.date or datetime.utcnow()
        })
        
        # Update velocity metrics (simplified)
        if account_number in self.velocity_cache:
            velocity = self.velocity_cache[account_number]
            velocity.transaction_count_1h += 1
            velocity.transaction_count_24h += 1
            velocity.total_amount_1h += transaction.amount
            velocity.total_amount_24h += transaction.amount
            velocity.last_updated = datetime.utcnow()
    
    async def _cross_transaction_analysis(
        self, 
        transactions: List[BankTransaction], 
        results: List[AmountValidationResult]
    ):
        """Perform cross-transaction analysis for additional fraud detection."""
        
        # Group by account
        account_groups = defaultdict(list)
        for i, transaction in enumerate(transactions):
            if transaction.account_number:
                account_groups[transaction.account_number].append((transaction, results[i]))
        
        # Analyze each account's transactions
        for account_number, account_transactions in account_groups.items():
            if len(account_transactions) < 3:
                continue
            
            amounts = [tx.amount for tx, _ in account_transactions]
            
            # Check for suspicious patterns across the batch
            # All amounts identical
            if len(set(amounts)) == 1 and len(amounts) >= 5:
                for _, result in account_transactions:
                    if AmountFlag.PATTERN_ANOMALY not in result.flags:
                        result.flags.append(AmountFlag.PATTERN_ANOMALY)
                        result.risk_score = min(result.risk_score + 0.2, 1.0)
                        result.risk_level = self._score_to_risk_level(result.risk_score)
    
    def _create_default_thresholds(self) -> List[AmountThreshold]:
        """Create default amount validation thresholds for Nigerian banking."""
        
        return [
            # Individual transaction limits
            AmountThreshold(
                name="individual_single_transaction",
                threshold_type="single_transaction",
                max_amount=Decimal('5000000'),  # 5M NGN
                daily_limit=Decimal('10000000')  # 10M NGN
            ),
            
            # Corporate transaction limits
            AmountThreshold(
                name="corporate_single_transaction", 
                threshold_type="single_transaction",
                max_amount=Decimal('50000000'),  # 50M NGN
                daily_limit=Decimal('200000000')  # 200M NGN
            ),
            
            # Micro-transaction monitoring
            AmountThreshold(
                name="micro_transaction_monitoring",
                threshold_type="micro_monitoring",
                min_amount=Decimal('1'),
                max_amount=Decimal('100'),
                transaction_count_limit=50,
                time_window_minutes=60
            ),
            
            # High-value monitoring
            AmountThreshold(
                name="high_value_monitoring",
                threshold_type="high_value",
                min_amount=Decimal('1000000'),  # 1M NGN
                transaction_count_limit=10,
                time_window_minutes=1440  # 24 hours
            )
        ]
    
    def _update_validation_stats(self, result: AmountValidationResult):
        """Update validation statistics."""
        
        self.stats['total_validations'] += 1
        
        if result.risk_level in [FraudRisk.HIGH, FraudRisk.VERY_HIGH, FraudRisk.CRITICAL]:
            self.stats['fraud_detected'] += 1
        
        self.stats['risk_level_breakdown'][result.risk_level.value] += 1
        
        for flag in result.flags:
            self.stats['flag_breakdown'][flag.value] += 1
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get amount validation statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_validations'] > 0:
            stats['fraud_detection_rate'] = stats['fraud_detected'] / stats['total_validations']
        else:
            stats['fraud_detection_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset validation statistics."""
        
        self.stats = {
            'total_validations': 0,
            'fraud_detected': 0,
            'risk_level_breakdown': {risk.value: 0 for risk in FraudRisk},
            'flag_breakdown': {flag.value: 0 for flag in AmountFlag}
        }


def create_amount_validator(
    thresholds: Optional[List[AmountThreshold]] = None,
    enable_ml_scoring: bool = False
) -> AmountValidator:
    """Factory function to create amount validator."""
    return AmountValidator(thresholds, enable_ml_scoring)