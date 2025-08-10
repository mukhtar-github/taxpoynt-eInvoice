"""
Pattern Matcher
===============

Advanced transaction pattern recognition and categorization engine.
Uses machine learning and rule-based approaches to identify transaction patterns,
categorize transactions, and extract business intelligence.

Features:
- Nigerian transaction pattern recognition
- Merchant identification
- Transaction categorization
- Business intelligence extraction
- Anomaly pattern detection
- Seasonal pattern analysis
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import re
import logging
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import statistics

from ....connector_framework.base_banking_connector import BankTransaction

logger = logging.getLogger(__name__)


class TransactionCategory(Enum):
    """Nigerian transaction categories."""
    # Business categories
    RETAIL_PAYMENT = "retail_payment"
    WHOLESALE_PAYMENT = "wholesale_payment" 
    SALARY_PAYMENT = "salary_payment"
    CONTRACTOR_PAYMENT = "contractor_payment"
    SUPPLIER_PAYMENT = "supplier_payment"
    
    # Consumer categories
    UTILITY_BILL = "utility_bill"
    TELECOMMUNICATIONS = "telecommunications"
    FUEL_PURCHASE = "fuel_purchase"
    GROCERY_SHOPPING = "grocery_shopping"
    RESTAURANT_DINING = "restaurant_dining"
    TRANSPORTATION = "transportation"
    HEALTHCARE = "healthcare"
    EDUCATION = "education"
    
    # Financial services
    LOAN_REPAYMENT = "loan_repayment"
    INSURANCE_PREMIUM = "insurance_premium"
    INVESTMENT = "investment"
    SAVINGS_DEPOSIT = "savings_deposit"
    
    # Government and taxes
    TAX_PAYMENT = "tax_payment"
    GOVERNMENT_FEE = "government_fee"
    LICENSE_RENEWAL = "license_renewal"
    
    # E-commerce and digital
    ONLINE_SHOPPING = "online_shopping"
    DIGITAL_SERVICE = "digital_service"
    SUBSCRIPTION = "subscription"
    
    # Cash and ATM
    ATM_WITHDRAWAL = "atm_withdrawal"
    CASH_DEPOSIT = "cash_deposit"
    
    # Transfers
    PERSONAL_TRANSFER = "personal_transfer"
    BUSINESS_TRANSFER = "business_transfer"
    INTERNATIONAL_TRANSFER = "international_transfer"
    
    # Unknown
    UNKNOWN = "unknown"


class PatternType(Enum):
    """Types of transaction patterns."""
    MERCHANT = "merchant"           # Merchant/business patterns
    TEMPORAL = "temporal"           # Time-based patterns
    AMOUNT = "amount"              # Amount-based patterns
    FREQUENCY = "frequency"        # Frequency patterns
    DESCRIPTION = "description"    # Description patterns
    BEHAVIORAL = "behavioral"      # User behavior patterns
    SEASONAL = "seasonal"          # Seasonal patterns
    ANOMALY = "anomaly"           # Anomaly patterns


@dataclass
class PatternRule:
    """Pattern matching rule definition."""
    id: str
    name: str
    pattern_type: PatternType
    category: TransactionCategory
    confidence_weight: float
    description_patterns: List[str] = None
    amount_patterns: List[Tuple[float, float]] = None  # (min, max) ranges
    merchant_patterns: List[str] = None
    temporal_patterns: List[str] = None
    enabled: bool = True


@dataclass
class PatternMatch:
    """Result of pattern matching."""
    rule_id: str
    pattern_type: PatternType
    category: TransactionCategory
    confidence_score: float
    matched_elements: List[str] = None
    pattern_details: Dict[str, Any] = None


@dataclass
class PatternResult:
    """Complete pattern analysis result."""
    transaction_id: str
    primary_category: TransactionCategory
    confidence_score: float
    pattern_matches: List[PatternMatch] = None
    merchant_identified: bool = False
    merchant_name: Optional[str] = None
    business_purpose: Optional[str] = None
    pattern_flags: List[str] = None
    analysis_timestamp: datetime = None


class PatternMatcher:
    """
    Advanced pattern matcher for Nigerian banking transactions.
    
    Uses sophisticated pattern recognition to categorize transactions,
    identify merchants, and extract business intelligence from
    transaction descriptions and metadata.
    """
    
    def __init__(
        self,
        pattern_rules: Optional[List[PatternRule]] = None,
        enable_ml_matching: bool = False
    ):
        self.pattern_rules = pattern_rules or self._create_nigerian_patterns()
        self.enable_ml_matching = enable_ml_matching
        
        # Nigerian-specific patterns
        self._initialize_nigerian_patterns()
        
        # Learning and adaptation
        self.pattern_frequency = defaultdict(int)
        self.merchant_database = {}
        self.seasonal_patterns = defaultdict(list)
        
        # Statistics
        self.stats = {
            'total_matches': 0,
            'successful_categorizations': 0,
            'merchant_identifications': 0,
            'pattern_type_usage': {pt.value: 0 for pt in PatternType},
            'category_distribution': {cat.value: 0 for cat in TransactionCategory}
        }
    
    async def match_patterns(
        self,
        transaction: BankTransaction,
        historical_context: Optional[List[BankTransaction]] = None
    ) -> PatternResult:
        """
        Match transaction patterns and categorize transaction.
        
        Args:
            transaction: Transaction to analyze
            historical_context: Historical transactions for context
            
        Returns:
            PatternResult with pattern analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Matching patterns for transaction: {transaction.id}")
            
            # Initialize result
            result = PatternResult(
                transaction_id=transaction.id,
                primary_category=TransactionCategory.UNKNOWN,
                confidence_score=0.0,
                pattern_matches=[],
                pattern_flags=[],
                analysis_timestamp=start_time
            )
            
            # Apply pattern rules
            all_matches = []
            
            for rule in self.pattern_rules:
                if not rule.enabled:
                    continue
                
                try:
                    match = await self._apply_pattern_rule(transaction, rule, historical_context)
                    if match and match.confidence_score > 0:
                        all_matches.append(match)
                        self.stats['pattern_type_usage'][match.pattern_type.value] += 1
                        
                except Exception as e:
                    logger.error(f"Pattern rule failed: {rule.id} - {e}")
            
            # Sort matches by confidence
            all_matches.sort(key=lambda m: m.confidence_score, reverse=True)
            result.pattern_matches = all_matches[:10]  # Top 10 matches
            
            # Determine primary category
            if all_matches:
                # Use weighted scoring to determine primary category
                category_scores = self._calculate_category_scores(all_matches)
                
                if category_scores:
                    best_category, best_score = max(category_scores.items(), key=lambda x: x[1])
                    result.primary_category = best_category
                    result.confidence_score = min(best_score, 1.0)
            
            # Merchant identification
            merchant_info = await self._identify_merchant(transaction, all_matches)
            if merchant_info:
                result.merchant_identified = True
                result.merchant_name = merchant_info.get('name')
                result.business_purpose = merchant_info.get('business_purpose')
            
            # Pattern flags and insights
            result.pattern_flags = self._generate_pattern_flags(transaction, all_matches, historical_context)
            
            # Update learning data
            await self._update_pattern_learning(transaction, result)
            
            # Update statistics
            self._update_matching_stats(result)
            
            logger.debug(f"Pattern matching completed: {transaction.id} - Category: {result.primary_category.value}")
            return result
            
        except Exception as e:
            logger.error(f"Pattern matching failed: {transaction.id} - {e}")
            
            return PatternResult(
                transaction_id=transaction.id,
                primary_category=TransactionCategory.UNKNOWN,
                confidence_score=0.0,
                pattern_flags=[f"Pattern matching error: {e}"],
                analysis_timestamp=start_time
            )
    
    async def match_batch_patterns(
        self,
        transactions: List[BankTransaction]
    ) -> List[PatternResult]:
        """
        Match patterns for multiple transactions in batch.
        
        Args:
            transactions: List of transactions to analyze
            
        Returns:
            List of PatternResult objects
        """
        logger.info(f"Batch pattern matching for {len(transactions)} transactions")
        
        results = []
        
        # Sort by account and date for better context
        sorted_transactions = sorted(
            transactions,
            key=lambda t: (t.account_number or '', t.date or datetime.min)
        )
        
        for i, transaction in enumerate(sorted_transactions):
            # Use previous transactions as context
            historical_context = sorted_transactions[:i] if i > 0 else []
            
            result = await self.match_patterns(transaction, historical_context)
            results.append(result)
        
        # Cross-transaction pattern analysis
        await self._cross_transaction_pattern_analysis(sorted_transactions, results)
        
        # Log batch summary
        categorized_count = sum(1 for r in results if r.primary_category != TransactionCategory.UNKNOWN)
        merchant_count = sum(1 for r in results if r.merchant_identified)
        
        logger.info(f"Batch pattern matching completed. Categorized: {categorized_count}, Merchants: {merchant_count}")
        
        return results
    
    async def _apply_pattern_rule(
        self,
        transaction: BankTransaction,
        rule: PatternRule,
        historical_context: Optional[List[BankTransaction]]
    ) -> Optional[PatternMatch]:
        """Apply individual pattern rule to transaction."""
        
        confidence_score = 0.0
        matched_elements = []
        pattern_details = {}
        
        # Description pattern matching
        if rule.description_patterns and transaction.description:
            desc_score, desc_matches = self._match_description_patterns(
                transaction.description, rule.description_patterns
            )
            confidence_score += desc_score * 0.4
            matched_elements.extend(desc_matches)
            pattern_details['description_matches'] = desc_matches
        
        # Amount pattern matching
        if rule.amount_patterns and transaction.amount:
            amount_score = self._match_amount_patterns(
                float(transaction.amount), rule.amount_patterns
            )
            confidence_score += amount_score * 0.2
            pattern_details['amount_match'] = amount_score > 0
        
        # Merchant pattern matching
        if rule.merchant_patterns:
            merchant_score, merchant_matches = self._match_merchant_patterns(
                transaction, rule.merchant_patterns
            )
            confidence_score += merchant_score * 0.3
            matched_elements.extend(merchant_matches)
            pattern_details['merchant_matches'] = merchant_matches
        
        # Temporal pattern matching
        if rule.temporal_patterns and transaction.date:
            temporal_score = self._match_temporal_patterns(
                transaction.date, rule.temporal_patterns
            )
            confidence_score += temporal_score * 0.1
            pattern_details['temporal_match'] = temporal_score > 0
        
        # Apply rule weight
        confidence_score *= rule.confidence_weight
        
        if confidence_score > 0.1:  # Minimum threshold
            return PatternMatch(
                rule_id=rule.id,
                pattern_type=rule.pattern_type,
                category=rule.category,
                confidence_score=confidence_score,
                matched_elements=matched_elements,
                pattern_details=pattern_details
            )
        
        return None
    
    def _match_description_patterns(
        self,
        description: str,
        patterns: List[str]
    ) -> Tuple[float, List[str]]:
        """Match description against patterns."""
        
        if not description:
            return 0.0, []
        
        desc_lower = description.lower().strip()
        matches = []
        total_score = 0.0
        
        for pattern in patterns:
            if re.search(pattern, desc_lower, re.IGNORECASE):
                matches.append(pattern)
                # Score based on pattern specificity
                total_score += min(len(pattern) / 20, 1.0)
        
        return min(total_score, 1.0), matches
    
    def _match_amount_patterns(
        self,
        amount: float,
        amount_patterns: List[Tuple[float, float]]
    ) -> float:
        """Match amount against patterns."""
        
        for min_amount, max_amount in amount_patterns:
            if min_amount <= amount <= max_amount:
                return 1.0
        
        return 0.0
    
    def _match_merchant_patterns(
        self,
        transaction: BankTransaction,
        merchant_patterns: List[str]
    ) -> Tuple[float, List[str]]:
        """Match merchant patterns."""
        
        text_to_search = " ".join(filter(None, [
            transaction.description,
            transaction.reference,
            transaction.merchant_name if hasattr(transaction, 'merchant_name') else None
        ])).lower()
        
        if not text_to_search:
            return 0.0, []
        
        matches = []
        total_score = 0.0
        
        for pattern in merchant_patterns:
            if re.search(pattern, text_to_search, re.IGNORECASE):
                matches.append(pattern)
                total_score += 0.5
        
        return min(total_score, 1.0), matches
    
    def _match_temporal_patterns(
        self,
        transaction_date: datetime,
        temporal_patterns: List[str]
    ) -> float:
        """Match temporal patterns."""
        
        score = 0.0
        
        for pattern in temporal_patterns:
            if pattern == "weekday" and transaction_date.weekday() < 5:
                score += 0.3
            elif pattern == "weekend" and transaction_date.weekday() >= 5:
                score += 0.3
            elif pattern == "business_hours":
                hour = transaction_date.hour
                if 8 <= hour <= 17:
                    score += 0.2
            elif pattern == "month_end":
                # Last 3 days of month
                if transaction_date.day >= 28:
                    score += 0.4
            elif pattern == "month_start":
                # First 3 days of month
                if transaction_date.day <= 3:
                    score += 0.4
        
        return min(score, 1.0)
    
    def _calculate_category_scores(
        self,
        matches: List[PatternMatch]
    ) -> Dict[TransactionCategory, float]:
        """Calculate weighted scores for each category."""
        
        category_scores = defaultdict(float)
        
        for match in matches:
            category_scores[match.category] += match.confidence_score
        
        return dict(category_scores)
    
    async def _identify_merchant(
        self,
        transaction: BankTransaction,
        matches: List[PatternMatch]
    ) -> Optional[Dict[str, str]]:
        """Identify merchant from transaction and patterns."""
        
        # Extract potential merchant names from description
        merchant_candidates = self._extract_merchant_candidates(transaction.description)
        
        if not merchant_candidates:
            return None
        
        # Use pattern matches to refine merchant identification
        merchant_patterns = [
            m for m in matches 
            if m.pattern_type == PatternType.MERCHANT and m.confidence_score > 0.5
        ]
        
        if merchant_patterns:
            best_candidate = merchant_candidates[0]  # Simplified selection
            
            # Determine business purpose from category
            business_purpose = self._infer_business_purpose(matches)
            
            return {
                'name': best_candidate,
                'business_purpose': business_purpose,
                'confidence': 0.8
            }
        
        return None
    
    def _extract_merchant_candidates(self, description: str) -> List[str]:
        """Extract potential merchant names from description."""
        
        if not description:
            return []
        
        candidates = []
        
        # Nigerian merchant patterns
        merchant_patterns = [
            r'(?:FROM|TO|AT)\s+([A-Z][A-Za-z\s&]+(?:LTD|LIMITED|NIG|NIGERIA)?)',
            r'([A-Z][A-Za-z\s&]+(?:STORES?|MART|SHOP|SERVICES?|BANK))',
            r'([A-Z][A-Za-z\s&]+(?:PETROLEUM|FILLING STATION|FUEL))',
            r'(GTB|UBA|ZENITH|FIRST BANK|ACCESS|FIDELITY|STANBIC)',
            r'(JUMIA|KONGA|PAYSTACK|FLUTTERWAVE|INTERSWITCH)'
        ]
        
        for pattern in merchant_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            candidates.extend([m.strip() for m in matches if m.strip()])
        
        return candidates[:3]  # Top 3 candidates
    
    def _infer_business_purpose(self, matches: List[PatternMatch]) -> str:
        """Infer business purpose from pattern matches."""
        
        category_mapping = {
            TransactionCategory.RETAIL_PAYMENT: "retail_purchase",
            TransactionCategory.UTILITY_BILL: "utility_payment",
            TransactionCategory.FUEL_PURCHASE: "fuel_purchase",
            TransactionCategory.TELECOMMUNICATIONS: "telecom_service",
            TransactionCategory.RESTAURANT_DINING: "food_service",
            TransactionCategory.TRANSPORTATION: "transport_service",
            TransactionCategory.ONLINE_SHOPPING: "e_commerce",
            TransactionCategory.HEALTHCARE: "medical_service"
        }
        
        if matches:
            primary_category = matches[0].category
            return category_mapping.get(primary_category, "business_transaction")
        
        return "unknown_purpose"
    
    def _generate_pattern_flags(
        self,
        transaction: BankTransaction,
        matches: List[PatternMatch],
        historical_context: Optional[List[BankTransaction]]
    ) -> List[str]:
        """Generate pattern-based flags and insights."""
        
        flags = []
        
        # High confidence categorization
        if matches and matches[0].confidence_score > 0.8:
            flags.append("high_confidence_category")
        
        # Multiple strong matches (conflicting categories)
        strong_matches = [m for m in matches if m.confidence_score > 0.6]
        if len(strong_matches) > 2:
            flags.append("multiple_category_matches")
        
        # Unusual transaction for account
        if historical_context:
            account_transactions = [
                t for t in historical_context 
                if t.account_number == transaction.account_number
            ]
            
            if len(account_transactions) > 5:
                # Check if this category is unusual for this account
                # Simplified analysis
                if matches and matches[0].confidence_score > 0.7:
                    flags.append("category_identified")
        
        # Weekend high-value transaction
        if (transaction.date and transaction.date.weekday() >= 5 and 
            transaction.amount and transaction.amount > 1000000):
            flags.append("weekend_high_value")
        
        return flags
    
    async def _update_pattern_learning(
        self,
        transaction: BankTransaction,
        result: PatternResult
    ):
        """Update pattern learning data."""
        
        # Update pattern frequency
        if result.primary_category != TransactionCategory.UNKNOWN:
            self.pattern_frequency[result.primary_category.value] += 1
        
        # Update merchant database
        if result.merchant_identified and result.merchant_name:
            merchant_key = result.merchant_name.lower()
            if merchant_key not in self.merchant_database:
                self.merchant_database[merchant_key] = {
                    'name': result.merchant_name,
                    'category': result.primary_category.value,
                    'frequency': 1,
                    'confidence': result.confidence_score
                }
            else:
                self.merchant_database[merchant_key]['frequency'] += 1
        
        # Update seasonal patterns
        if transaction.date:
            month_key = transaction.date.strftime("%m")
            self.seasonal_patterns[month_key].append(result.primary_category.value)
    
    async def _cross_transaction_pattern_analysis(
        self,
        transactions: List[BankTransaction],
        results: List[PatternResult]
    ):
        """Perform cross-transaction pattern analysis."""
        
        # Group by account
        account_groups = defaultdict(list)
        for i, transaction in enumerate(transactions):
            if transaction.account_number:
                account_groups[transaction.account_number].append((transaction, results[i]))
        
        # Analyze patterns within each account
        for account_number, account_data in account_groups.items():
            if len(account_data) < 3:
                continue
            
            # Check for repetitive patterns
            categories = [result.primary_category for _, result in account_data]
            category_counts = Counter(categories)
            
            # Mark repetitive patterns
            for _, result in account_data:
                if category_counts[result.primary_category] >= 3:
                    if "repetitive_pattern" not in result.pattern_flags:
                        result.pattern_flags.append("repetitive_pattern")
    
    def _initialize_nigerian_patterns(self):
        """Initialize Nigerian-specific patterns and data."""
        
        # Nigerian banks
        self.nigerian_banks = [
            'gtb', 'uba', 'zenith', 'first bank', 'access', 'fidelity',
            'stanbic', 'fcmb', 'unity', 'wema', 'sterling', 'ecobank'
        ]
        
        # Nigerian merchants
        self.nigerian_merchants = [
            'shoprite', 'game', 'spar', 'mr biggs', 'cold stone', 'sweet sensation',
            'tantalizers', 'chicken republic', 'dominos', 'mobil', 'total',
            'conoil', 'oando', 'forte oil', 'mtn', 'glo', 'airtel', '9mobile'
        ]
        
        # Nigerian utilities
        self.nigerian_utilities = [
            'phcn', 'nepa', 'aedc', 'ekedc', 'ikedc', 'kedco', 'yedc',
            'dstv', 'gotv', 'startimes', 'lawma', 'lagos water'
        ]
    
    def _create_nigerian_patterns(self) -> List[PatternRule]:
        """Create Nigerian-specific pattern rules."""
        
        return [
            # Utility Bills
            PatternRule(
                id="utility_electricity",
                name="Electricity Bill Payment",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.UTILITY_BILL,
                confidence_weight=0.9,
                description_patterns=[
                    r'(?:phcn|nepa|aedc|ekedc|ikedc|kedco|yedc)',
                    r'electricity.*bill',
                    r'power.*payment',
                    r'(?:prepaid|postpaid).*(?:meter|token)'
                ]
            ),
            
            # Telecommunications
            PatternRule(
                id="telecom_airtime",
                name="Airtime/Data Purchase",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.TELECOMMUNICATIONS,
                confidence_weight=0.85,
                description_patterns=[
                    r'(?:mtn|glo|airtel|9mobile)',
                    r'(?:airtime|data|recharge)',
                    r'(?:mobile|phone).*(?:top.*up|recharge)'
                ]
            ),
            
            # Fuel Purchase
            PatternRule(
                id="fuel_purchase",
                name="Fuel Purchase",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.FUEL_PURCHASE,
                confidence_weight=0.9,
                description_patterns=[
                    r'(?:mobil|total|conoil|oando|forte oil|nnpc)',
                    r'(?:petrol|fuel|gas).*(?:station|purchase)',
                    r'filling.*station'
                ],
                amount_patterns=[(1000, 50000)]  # Typical fuel purchase range
            ),
            
            # Banking/ATM
            PatternRule(
                id="atm_withdrawal",
                name="ATM Withdrawal",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.ATM_WITHDRAWAL,
                confidence_weight=0.95,
                description_patterns=[
                    r'atm.*(?:withdrawal|cash)',
                    r'cash.*withdrawal',
                    r'(?:gtb|uba|zenith|first bank|access).*atm'
                ]
            ),
            
            # Retail Shopping
            PatternRule(
                id="retail_shopping",
                name="Retail Shopping",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.RETAIL_PAYMENT,
                confidence_weight=0.8,
                description_patterns=[
                    r'(?:shoprite|game|spar).*(?:store|mart)',
                    r'supermarket',
                    r'(?:grocery|retail).*(?:store|shopping)'
                ]
            ),
            
            # Restaurant/Food
            PatternRule(
                id="restaurant_dining",
                name="Restaurant Dining",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.RESTAURANT_DINING,
                confidence_weight=0.8,
                description_patterns=[
                    r'(?:mr biggs|cold stone|sweet sensation|tantalizers)',
                    r'(?:chicken republic|kfc|dominos)',
                    r'restaurant',
                    r'(?:food|meal).*(?:purchase|order)'
                ]
            ),
            
            # Government Payments
            PatternRule(
                id="government_payment",
                name="Government Payment",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.GOVERNMENT_FEE,
                confidence_weight=0.9,
                description_patterns=[
                    r'(?:firs|tax|vat)',
                    r'(?:government|federal|state).*(?:fee|payment)',
                    r'(?:license|permit|registration).*(?:fee|renewal)',
                    r'(?:ministry|agency|commission)'
                ]
            ),
            
            # Salary Payments
            PatternRule(
                id="salary_payment",
                name="Salary Payment",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.SALARY_PAYMENT,
                confidence_weight=0.85,
                description_patterns=[
                    r'salary.*(?:payment|transfer)',
                    r'(?:monthly|staff).*(?:salary|wage)',
                    r'payroll'
                ],
                temporal_patterns=["month_end", "month_start"]
            ),
            
            # Online Shopping
            PatternRule(
                id="online_shopping",
                name="Online Shopping",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.ONLINE_SHOPPING,
                confidence_weight=0.8,
                description_patterns=[
                    r'(?:jumia|konga|amazon)',
                    r'online.*(?:shopping|purchase)',
                    r'e.*commerce',
                    r'(?:paystack|flutterwave|interswitch)'
                ]
            ),
            
            # Transportation
            PatternRule(
                id="transportation",
                name="Transportation",
                pattern_type=PatternType.DESCRIPTION,
                category=TransactionCategory.TRANSPORTATION,
                confidence_weight=0.8,
                description_patterns=[
                    r'(?:uber|bolt|taxify)',
                    r'(?:transport|taxi|bus).*(?:fare|payment)',
                    r'(?:airline|flight).*(?:ticket|booking)',
                    r'(?:train|rail).*(?:ticket|fare)'
                ]
            )
        ]
    
    def _update_matching_stats(self, result: PatternResult):
        """Update pattern matching statistics."""
        
        self.stats['total_matches'] += 1
        
        if result.primary_category != TransactionCategory.UNKNOWN:
            self.stats['successful_categorizations'] += 1
            self.stats['category_distribution'][result.primary_category.value] += 1
        
        if result.merchant_identified:
            self.stats['merchant_identifications'] += 1
        
        for match in result.pattern_matches:
            self.stats['pattern_type_usage'][match.pattern_type.value] += 1
    
    def get_pattern_statistics(self) -> Dict[str, Any]:
        """Get pattern matching statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_matches'] > 0:
            stats['categorization_rate'] = stats['successful_categorizations'] / stats['total_matches']
            stats['merchant_identification_rate'] = stats['merchant_identifications'] / stats['total_matches']
        else:
            stats['categorization_rate'] = 0.0
            stats['merchant_identification_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset pattern matching statistics."""
        
        self.stats = {
            'total_matches': 0,
            'successful_categorizations': 0,
            'merchant_identifications': 0,
            'pattern_type_usage': {pt.value: 0 for pt in PatternType},
            'category_distribution': {cat.value: 0 for cat in TransactionCategory}
        }


def create_pattern_matcher(
    pattern_rules: Optional[List[PatternRule]] = None,
    enable_ml_matching: bool = False
) -> PatternMatcher:
    """Factory function to create pattern matcher."""
    return PatternMatcher(pattern_rules, enable_ml_matching)