"""
Duplicate Detector
==================

Prevents duplicate transaction processing using multiple detection strategies.
Essential for webhook-based integrations where duplicate events can occur.

Features:
- Multiple detection strategies (hash-based, field-based, time-window)
- Configurable duplicate resolution
- Performance optimized with caching
- Nigerian banking compliance
- Audit trail for duplicate handling
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import json
import logging
from collections import defaultdict

from ....connector_framework.base_banking_connector import BankTransaction
from .....core_platform.data_management import DatabaseAbstraction
from .....core_platform.messaging import CacheManager

logger = logging.getLogger(__name__)


class DuplicateStrategy(Enum):
    """Duplicate detection strategies."""
    HASH_BASED = "hash_based"           # Content hash comparison
    FIELD_BASED = "field_based"         # Specific field combination
    TIME_WINDOW = "time_window"         # Time-based deduplication
    COMPOSITE = "composite"             # Multiple strategies combined
    STRICT = "strict"                   # All fields must match exactly


class DuplicateAction(Enum):
    """Actions to take when duplicate is detected."""
    SKIP = "skip"                       # Skip processing duplicate
    MERGE = "merge"                     # Merge with existing transaction
    UPDATE = "update"                   # Update existing transaction
    FLAG = "flag"                       # Flag as duplicate but process
    ERROR = "error"                     # Raise error on duplicate


class DuplicateConfidence(Enum):
    """Confidence level of duplicate detection."""
    LOW = "low"                         # Possible duplicate
    MEDIUM = "medium"                   # Likely duplicate
    HIGH = "high"                       # Almost certain duplicate
    EXACT = "exact"                     # Exact duplicate


@dataclass
class DetectionRule:
    """Duplicate detection rule configuration."""
    name: str
    strategy: DuplicateStrategy
    fields: List[str]
    time_window_minutes: Optional[int] = None
    confidence_threshold: float = 0.9
    action: DuplicateAction = DuplicateAction.SKIP
    enabled: bool = True
    parameters: Dict[str, Any] = None


@dataclass
class DuplicateMatch:
    """Information about a duplicate match."""
    original_transaction_id: str
    duplicate_transaction_id: str
    confidence: DuplicateConfidence
    confidence_score: float
    matching_fields: List[str]
    detection_rule: str
    match_details: Dict[str, Any] = None


@dataclass
class DuplicateResult:
    """Result of duplicate detection."""
    transaction_id: str
    is_duplicate: bool
    matches: List[DuplicateMatch] = None
    recommended_action: DuplicateAction = DuplicateAction.SKIP
    detection_timestamp: datetime = None
    processing_notes: List[str] = None


class DuplicateDetector:
    """
    Advanced duplicate detector for banking transactions.
    
    Uses multiple strategies to identify and handle duplicate transactions
    from Open Banking providers, especially important for webhook integrations.
    """
    
    def __init__(
        self,
        database: DatabaseAbstraction,
        cache_manager: CacheManager,
        detection_rules: Optional[List[DetectionRule]] = None,
        strategy: DuplicateStrategy = DuplicateStrategy.HASH_BASED
    ):
        self.database = database
        self.cache_manager = cache_manager
        self.detection_rules = detection_rules or self._create_default_rules()
        self.default_strategy = strategy
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour cache
        self.max_matches_to_return = 10
        self.hash_algorithm = 'sha256'
        
        # In-memory caches for performance
        self.transaction_hashes: Set[str] = set()
        self.recent_transactions: Dict[str, List[BankTransaction]] = defaultdict(list)
        self.processed_ids: Set[str] = set()
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'duplicates_found': 0,
            'unique_transactions': 0,
            'cache_hits': 0,
            'strategy_usage': {strategy.value: 0 for strategy in DuplicateStrategy}
        }
    
    async def check_duplicate(
        self,
        transaction: BankTransaction,
        custom_rules: Optional[List[DetectionRule]] = None
    ) -> DuplicateResult:
        """
        Check if transaction is a duplicate.
        
        Args:
            transaction: Transaction to check
            custom_rules: Additional detection rules
            
        Returns:
            DuplicateResult with detection details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.debug(f"Checking for duplicates: {transaction.id}")
            
            # Initialize result
            result = DuplicateResult(
                transaction_id=transaction.id,
                is_duplicate=False,
                matches=[],
                detection_timestamp=start_time
            )
            
            # Quick cache check
            if await self._quick_cache_check(transaction.id):
                self.stats['cache_hits'] += 1
                result.is_duplicate = True
                result.recommended_action = DuplicateAction.SKIP
                result.processing_notes = ["Found in quick cache"]
                return result
            
            # Apply detection rules
            applicable_rules = self.detection_rules[:]
            if custom_rules:
                applicable_rules.extend(custom_rules)
            
            all_matches = []
            
            for rule in applicable_rules:
                if not rule.enabled:
                    continue
                
                try:
                    matches = await self._apply_detection_rule(transaction, rule)
                    if matches:
                        all_matches.extend(matches)
                        self.stats['strategy_usage'][rule.strategy.value] += 1
                        
                except Exception as e:
                    logger.error(f"Detection rule failed: {rule.name} - {e}")
            
            # Process matches
            if all_matches:
                # Sort by confidence score
                all_matches.sort(key=lambda m: m.confidence_score, reverse=True)
                
                # Take top matches
                result.matches = all_matches[:self.max_matches_to_return]
                result.is_duplicate = True
                
                # Determine recommended action
                result.recommended_action = self._determine_recommended_action(result.matches)
                
                # Log duplicate detection
                await self._log_duplicate_detection(transaction, result)
                
                self.stats['duplicates_found'] += 1
            else:
                # Mark as unique
                await self._mark_as_unique(transaction)
                self.stats['unique_transactions'] += 1
            
            # Update statistics
            self.stats['total_checks'] += 1
            
            logger.debug(f"Duplicate check completed: {transaction.id} - Duplicate: {result.is_duplicate}")
            return result
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {transaction.id} - {e}")
            
            return DuplicateResult(
                transaction_id=transaction.id,
                is_duplicate=False,
                detection_timestamp=start_time,
                processing_notes=[f"Detection error: {e}"]
            )
    
    async def check_batch_duplicates(
        self,
        transactions: List[BankTransaction],
        custom_rules: Optional[List[DetectionRule]] = None
    ) -> List[DuplicateResult]:
        """
        Check multiple transactions for duplicates in batch.
        
        Args:
            transactions: List of transactions to check
            custom_rules: Additional detection rules
            
        Returns:
            List of DuplicateResult objects
        """
        logger.info(f"Batch duplicate checking {len(transactions)} transactions")
        
        results = []
        
        # First pass: check against existing data
        for transaction in transactions:
            result = await self.check_duplicate(transaction, custom_rules)
            results.append(result)
        
        # Second pass: check within batch for internal duplicates
        await self._check_internal_batch_duplicates(transactions, results)
        
        # Log batch summary
        duplicate_count = sum(1 for r in results if r.is_duplicate)
        logger.info(f"Batch duplicate check completed. Duplicates: {duplicate_count}/{len(transactions)}")
        
        return results
    
    async def _apply_detection_rule(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Apply specific detection rule to find duplicates."""
        
        if rule.strategy == DuplicateStrategy.HASH_BASED:
            return await self._hash_based_detection(transaction, rule)
        elif rule.strategy == DuplicateStrategy.FIELD_BASED:
            return await self._field_based_detection(transaction, rule)
        elif rule.strategy == DuplicateStrategy.TIME_WINDOW:
            return await self._time_window_detection(transaction, rule)
        elif rule.strategy == DuplicateStrategy.COMPOSITE:
            return await self._composite_detection(transaction, rule)
        elif rule.strategy == DuplicateStrategy.STRICT:
            return await self._strict_detection(transaction, rule)
        
        return []
    
    async def _hash_based_detection(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Detect duplicates using content hash comparison."""
        
        # Generate transaction hash
        transaction_hash = self._generate_transaction_hash(transaction, rule.fields)
        
        # Check cache first
        cache_key = f"hash_duplicate:{transaction_hash}"
        cached_result = await self.cache_manager.get(cache_key)
        
        if cached_result:
            return [DuplicateMatch(
                original_transaction_id=cached_result,
                duplicate_transaction_id=transaction.id,
                confidence=DuplicateConfidence.HIGH,
                confidence_score=0.95,
                matching_fields=rule.fields,
                detection_rule=rule.name,
                match_details={'hash': transaction_hash}
            )]
        
        # Check database
        existing_transactions = await self.database.fetch_all(
            "SELECT id FROM transaction_hashes WHERE hash = ?",
            (transaction_hash,)
        )
        
        matches = []
        for row in existing_transactions:
            if row['id'] != transaction.id:
                matches.append(DuplicateMatch(
                    original_transaction_id=row['id'],
                    duplicate_transaction_id=transaction.id,
                    confidence=DuplicateConfidence.HIGH,
                    confidence_score=0.95,
                    matching_fields=rule.fields,
                    detection_rule=rule.name,
                    match_details={'hash': transaction_hash}
                ))
        
        # Cache the hash
        if not matches:
            await self.cache_manager.set(cache_key, transaction.id, ttl=self.cache_ttl)
            # Store in database
            await self.database.execute(
                "INSERT OR IGNORE INTO transaction_hashes (id, hash) VALUES (?, ?)",
                (transaction.id, transaction_hash)
            )
        
        return matches
    
    async def _field_based_detection(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Detect duplicates using specific field combinations."""
        
        # Build query conditions
        conditions = []
        parameters = []
        
        for field in rule.fields:
            field_value = getattr(transaction, field, None)
            if field_value is not None:
                conditions.append(f"{field} = ?")
                parameters.append(field_value)
        
        if not conditions:
            return []
        
        # Query database
        query = f"""
            SELECT id, {', '.join(rule.fields)} 
            FROM transactions 
            WHERE {' AND '.join(conditions)} AND id != ?
        """
        parameters.append(transaction.id)
        
        existing_transactions = await self.database.fetch_all(query, parameters)
        
        matches = []
        for row in existing_transactions:
            # Calculate confidence based on field matches
            confidence_score = self._calculate_field_confidence(
                transaction, dict(row), rule.fields
            )
            
            if confidence_score >= rule.confidence_threshold:
                confidence = self._score_to_confidence(confidence_score)
                
                matches.append(DuplicateMatch(
                    original_transaction_id=row['id'],
                    duplicate_transaction_id=transaction.id,
                    confidence=confidence,
                    confidence_score=confidence_score,
                    matching_fields=rule.fields,
                    detection_rule=rule.name,
                    match_details={field: getattr(transaction, field) for field in rule.fields}
                ))
        
        return matches
    
    async def _time_window_detection(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Detect duplicates within time window."""
        
        if not rule.time_window_minutes or not transaction.date:
            return []
        
        # Define time window
        window_start = transaction.date - timedelta(minutes=rule.time_window_minutes)
        window_end = transaction.date + timedelta(minutes=rule.time_window_minutes)
        
        # Query transactions in time window
        query = """
            SELECT id, date, amount, account_number, description
            FROM transactions 
            WHERE date BETWEEN ? AND ? 
            AND id != ?
            AND amount = ?
        """
        
        existing_transactions = await self.database.fetch_all(
            query,
            (window_start, window_end, transaction.id, transaction.amount)
        )
        
        matches = []
        for row in existing_transactions:
            # Calculate similarity
            similarity_score = self._calculate_transaction_similarity(
                transaction, dict(row)
            )
            
            if similarity_score >= rule.confidence_threshold:
                confidence = self._score_to_confidence(similarity_score)
                
                matches.append(DuplicateMatch(
                    original_transaction_id=row['id'],
                    duplicate_transaction_id=transaction.id,
                    confidence=confidence,
                    confidence_score=similarity_score,
                    matching_fields=['date', 'amount', 'account_number'],
                    detection_rule=rule.name,
                    match_details={
                        'time_window_minutes': rule.time_window_minutes,
                        'similarity_score': similarity_score
                    }
                ))
        
        return matches
    
    async def _composite_detection(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Detect duplicates using multiple strategies combined."""
        
        all_matches = []
        
        # Apply multiple sub-strategies
        sub_strategies = rule.parameters.get('sub_strategies', [
            DuplicateStrategy.HASH_BASED,
            DuplicateStrategy.FIELD_BASED
        ])
        
        for strategy in sub_strategies:
            sub_rule = DetectionRule(
                name=f"{rule.name}_{strategy.value}",
                strategy=strategy,
                fields=rule.fields,
                confidence_threshold=rule.confidence_threshold * 0.8,  # Lower threshold for sub-rules
                parameters=rule.parameters
            )
            
            matches = await self._apply_detection_rule(transaction, sub_rule)
            all_matches.extend(matches)
        
        # Merge and deduplicate matches
        unique_matches = {}
        for match in all_matches:
            key = match.original_transaction_id
            if key not in unique_matches or match.confidence_score > unique_matches[key].confidence_score:
                unique_matches[key] = match
                unique_matches[key].detection_rule = rule.name  # Update to composite rule
        
        return list(unique_matches.values())
    
    async def _strict_detection(
        self,
        transaction: BankTransaction,
        rule: DetectionRule
    ) -> List[DuplicateMatch]:
        """Detect exact duplicates with all fields matching."""
        
        # Get all transaction fields
        transaction_dict = transaction.__dict__
        
        # Build exact match query
        conditions = []
        parameters = []
        
        for field, value in transaction_dict.items():
            if field != 'id' and value is not None:
                conditions.append(f"{field} = ?")
                parameters.append(value)
        
        if not conditions:
            return []
        
        query = f"""
            SELECT id FROM transactions 
            WHERE {' AND '.join(conditions)} AND id != ?
        """
        parameters.append(transaction.id)
        
        existing_transactions = await self.database.fetch_all(query, parameters)
        
        matches = []
        for row in existing_transactions:
            matches.append(DuplicateMatch(
                original_transaction_id=row['id'],
                duplicate_transaction_id=transaction.id,
                confidence=DuplicateConfidence.EXACT,
                confidence_score=1.0,
                matching_fields=list(transaction_dict.keys()),
                detection_rule=rule.name,
                match_details={'match_type': 'exact'}
            ))
        
        return matches
    
    def _generate_transaction_hash(self, transaction: BankTransaction, fields: List[str]) -> str:
        """Generate hash for transaction based on specified fields."""
        
        # Extract field values
        hash_data = {}
        for field in fields:
            value = getattr(transaction, field, None)
            if value is not None:
                # Normalize value for consistent hashing
                if isinstance(value, datetime):
                    hash_data[field] = value.isoformat()
                else:
                    hash_data[field] = str(value).strip().lower()
        
        # Create hash
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.new(self.hash_algorithm, hash_string.encode()).hexdigest()
    
    def _calculate_field_confidence(
        self,
        transaction: BankTransaction,
        existing_transaction: Dict[str, Any],
        fields: List[str]
    ) -> float:
        """Calculate confidence score based on field matches."""
        
        total_fields = len(fields)
        if total_fields == 0:
            return 0.0
        
        matching_fields = 0
        
        for field in fields:
            current_value = getattr(transaction, field, None)
            existing_value = existing_transaction.get(field)
            
            if current_value == existing_value:
                matching_fields += 1
            elif current_value is not None and existing_value is not None:
                # Fuzzy matching for string fields
                if isinstance(current_value, str) and isinstance(existing_value, str):
                    similarity = self._string_similarity(current_value, existing_value)
                    if similarity > 0.9:
                        matching_fields += similarity
        
        return matching_fields / total_fields
    
    def _calculate_transaction_similarity(
        self,
        transaction: BankTransaction,
        existing_transaction: Dict[str, Any]
    ) -> float:
        """Calculate overall similarity between transactions."""
        
        similarity_factors = []
        
        # Amount similarity (exact match required)
        if transaction.amount == existing_transaction.get('amount'):
            similarity_factors.append(1.0)
        else:
            return 0.0  # No similarity if amounts don't match
        
        # Account similarity
        if transaction.account_number == existing_transaction.get('account_number'):
            similarity_factors.append(1.0)
        else:
            similarity_factors.append(0.0)
        
        # Description similarity
        desc_similarity = self._string_similarity(
            transaction.description or "",
            existing_transaction.get('description', "")
        )
        similarity_factors.append(desc_similarity)
        
        # Date proximity (within same day gets high score)
        date_similarity = self._date_similarity(
            transaction.date,
            existing_transaction.get('date')
        )
        similarity_factors.append(date_similarity)
        
        return sum(similarity_factors) / len(similarity_factors)
    
    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity (simple implementation)."""
        
        if not str1 and not str2:
            return 1.0
        if not str1 or not str2:
            return 0.0
        
        str1 = str1.lower().strip()
        str2 = str2.lower().strip()
        
        if str1 == str2:
            return 1.0
        
        # Simple character overlap ratio
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _date_similarity(self, date1: datetime, date2: datetime) -> float:
        """Calculate date similarity."""
        
        if not date1 or not date2:
            return 0.0
        
        time_diff = abs((date1 - date2).total_seconds())
        
        # Same minute: 1.0, same hour: 0.8, same day: 0.6, etc.
        if time_diff < 60:  # Same minute
            return 1.0
        elif time_diff < 3600:  # Same hour
            return 0.8
        elif time_diff < 86400:  # Same day
            return 0.6
        elif time_diff < 604800:  # Same week
            return 0.3
        else:
            return 0.0
    
    def _score_to_confidence(self, score: float) -> DuplicateConfidence:
        """Convert numeric score to confidence level."""
        
        if score >= 0.95:
            return DuplicateConfidence.EXACT
        elif score >= 0.85:
            return DuplicateConfidence.HIGH
        elif score >= 0.7:
            return DuplicateConfidence.MEDIUM
        else:
            return DuplicateConfidence.LOW
    
    def _determine_recommended_action(self, matches: List[DuplicateMatch]) -> DuplicateAction:
        """Determine recommended action based on matches."""
        
        if not matches:
            return DuplicateAction.SKIP
        
        best_match = matches[0]  # Highest confidence match
        
        if best_match.confidence == DuplicateConfidence.EXACT:
            return DuplicateAction.SKIP
        elif best_match.confidence == DuplicateConfidence.HIGH:
            return DuplicateAction.SKIP
        elif best_match.confidence == DuplicateConfidence.MEDIUM:
            return DuplicateAction.FLAG
        else:
            return DuplicateAction.FLAG
    
    async def _quick_cache_check(self, transaction_id: str) -> bool:
        """Quick cache check for known duplicates."""
        return transaction_id in self.processed_ids
    
    async def _mark_as_unique(self, transaction: BankTransaction):
        """Mark transaction as unique (not duplicate)."""
        self.processed_ids.add(transaction.id)
    
    async def _log_duplicate_detection(self, transaction: BankTransaction, result: DuplicateResult):
        """Log duplicate detection for audit trail."""
        
        try:
            await self.database.execute(
                """
                INSERT INTO duplicate_detections 
                (transaction_id, is_duplicate, matches_count, detection_timestamp, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transaction.id,
                    result.is_duplicate,
                    len(result.matches),
                    result.detection_timestamp,
                    json.dumps([match.__dict__ for match in result.matches])
                )
            )
        except Exception as e:
            logger.error(f"Failed to log duplicate detection: {e}")
    
    async def _check_internal_batch_duplicates(
        self,
        transactions: List[BankTransaction],
        results: List[DuplicateResult]
    ):
        """Check for duplicates within the batch itself."""
        
        transaction_map = {t.id: t for t in transactions}
        
        for i, transaction in enumerate(transactions):
            if results[i].is_duplicate:
                continue  # Already marked as duplicate
            
            # Check against other transactions in batch
            for j, other_transaction in enumerate(transactions):
                if i >= j:  # Only check forward to avoid double-checking
                    continue
                
                # Simple duplicate check within batch
                if self._transactions_are_identical(transaction, other_transaction):
                    # Mark later transaction as duplicate
                    results[j].is_duplicate = True
                    results[j].matches.append(DuplicateMatch(
                        original_transaction_id=transaction.id,
                        duplicate_transaction_id=other_transaction.id,
                        confidence=DuplicateConfidence.EXACT,
                        confidence_score=1.0,
                        matching_fields=['all'],
                        detection_rule='batch_internal',
                        match_details={'batch_position': j}
                    ))
    
    def _transactions_are_identical(self, tx1: BankTransaction, tx2: BankTransaction) -> bool:
        """Check if two transactions are identical."""
        
        # Compare key fields
        return (
            tx1.amount == tx2.amount and
            tx1.account_number == tx2.account_number and
            tx1.description == tx2.description and
            tx1.date == tx2.date and
            tx1.reference == tx2.reference
        )
    
    def _create_default_rules(self) -> List[DetectionRule]:
        """Create default duplicate detection rules."""
        
        return [
            # Hash-based detection (high priority)
            DetectionRule(
                name="hash_exact_match",
                strategy=DuplicateStrategy.HASH_BASED,
                fields=['amount', 'account_number', 'date', 'description'],
                confidence_threshold=0.95,
                action=DuplicateAction.SKIP
            ),
            
            # Field-based detection for core fields
            DetectionRule(
                name="core_fields_match",
                strategy=DuplicateStrategy.FIELD_BASED,
                fields=['amount', 'account_number', 'reference'],
                confidence_threshold=0.9,
                action=DuplicateAction.SKIP
            ),
            
            # Time window detection for similar amounts
            DetectionRule(
                name="time_window_similar",
                strategy=DuplicateStrategy.TIME_WINDOW,
                fields=['amount', 'account_number'],
                time_window_minutes=5,
                confidence_threshold=0.8,
                action=DuplicateAction.FLAG
            ),
            
            # Strict detection for exact matches
            DetectionRule(
                name="strict_exact_match",
                strategy=DuplicateStrategy.STRICT,
                fields=[],  # All fields
                confidence_threshold=1.0,
                action=DuplicateAction.SKIP
            )
        ]
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get duplicate detection statistics."""
        
        stats = self.stats.copy()
        
        if stats['total_checks'] > 0:
            stats['duplicate_rate'] = stats['duplicates_found'] / stats['total_checks']
            stats['unique_rate'] = stats['unique_transactions'] / stats['total_checks']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_checks']
        else:
            stats['duplicate_rate'] = 0.0
            stats['unique_rate'] = 0.0
            stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset detection statistics."""
        
        self.stats = {
            'total_checks': 0,
            'duplicates_found': 0,
            'unique_transactions': 0,
            'cache_hits': 0,
            'strategy_usage': {strategy.value: 0 for strategy in DuplicateStrategy}
        }


def create_duplicate_detector(
    database: DatabaseAbstraction,
    cache_manager: CacheManager,
    strategy: DuplicateStrategy = DuplicateStrategy.HASH_BASED,
    detection_rules: Optional[List[DetectionRule]] = None
) -> DuplicateDetector:
    """Factory function to create duplicate detector."""
    return DuplicateDetector(database, cache_manager, detection_rules, strategy)