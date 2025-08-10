"""
Customer Matcher
================

Intelligent customer identification and matching system for banking transactions.
Uses multiple matching strategies to identify customers from transaction data.

Features:
- Account number matching
- Name-based matching with fuzzy logic
- Transaction pattern analysis
- Machine learning-based matching
- Confidence scoring
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
import logging
from decimal import Decimal
from datetime import datetime

from .....core.models.customer import CustomerInfo
from .....core.models.transaction import BankTransaction
from .....core.utils.text_matching import fuzzy_match, normalize_text
from .....core.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)


class MatchingStrategy(Enum):
    """Customer matching strategies."""
    ACCOUNT_NUMBER = "account_number"
    NAME_FUZZY = "name_fuzzy"
    REFERENCE_PATTERN = "reference_pattern"
    TRANSACTION_PATTERN = "transaction_pattern"
    COMBINED_SCORE = "combined_score"


@dataclass
class CustomerMatch:
    """Result of customer matching process."""
    matched: bool
    customer_info: Optional[CustomerInfo] = None
    confidence_score: float = 0.0
    matching_strategy: Optional[MatchingStrategy] = None
    matching_details: Dict[str, Any] = None
    alternative_matches: List['CustomerMatch'] = None


@dataclass
class MatchingRule:
    """Rules for customer matching."""
    strategy: MatchingStrategy
    weight: float = 1.0
    minimum_confidence: float = 0.7
    enabled: bool = True
    parameters: Dict[str, Any] = None


class CustomerMatcher:
    """
    Intelligent customer matcher for banking transactions.
    
    Uses multiple strategies to identify customers from transaction data,
    including fuzzy matching, pattern recognition, and ML-based approaches.
    """
    
    def __init__(
        self,
        customer_database: Any,  # Customer data source
        cache: Optional[RedisCache] = None,
        default_rules: Optional[List[MatchingRule]] = None
    ):
        self.customer_database = customer_database
        self.cache = cache
        self.default_rules = default_rules or self._create_default_rules()
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.max_alternatives = 5
        self.fuzzy_threshold = 0.8
        
        # Statistics
        self.stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'cache_hits': 0,
            'strategy_usage': {strategy.value: 0 for strategy in MatchingStrategy}
        }
        
        # Precompiled patterns
        self.patterns = {
            'account_number': re.compile(r'\b\d{10,12}\b'),
            'reference_code': re.compile(r'\b[A-Z]{2,4}\d{6,10}\b'),
            'tin': re.compile(r'\b\d{11}\b'),
            'phone': re.compile(r'\b\+?234\d{10}\b|\b0\d{10}\b')
        }
    
    async def match_transaction(
        self,
        transaction: BankTransaction,
        rules: Optional[List[MatchingRule]] = None
    ) -> CustomerMatch:
        """
        Match customer from banking transaction data.
        
        Args:
            transaction: Banking transaction to match
            rules: Custom matching rules (optional)
            
        Returns:
            CustomerMatch with matching results
        """
        try:
            logger.debug(f"Matching customer for transaction: {transaction.id}")
            
            # Check cache first
            cache_key = f"customer_match:{transaction.account_number}:{hash(transaction.description)}"
            if self.cache:
                cached_match = await self.cache.get(cache_key)
                if cached_match:
                    self.stats['cache_hits'] += 1
                    logger.debug("Found cached customer match")
                    return CustomerMatch(**cached_match)
            
            # Apply matching rules
            applicable_rules = rules or self.default_rules
            matches = []
            
            for rule in applicable_rules:
                if not rule.enabled:
                    continue
                
                match_result = await self._apply_matching_strategy(
                    transaction, rule.strategy, rule.parameters or {}
                )
                
                if match_result and match_result.confidence_score >= rule.minimum_confidence:
                    # Weight the confidence score
                    match_result.confidence_score *= rule.weight
                    matches.append(match_result)
                    
                    self.stats['strategy_usage'][rule.strategy.value] += 1
            
            # Combine matches and select best
            final_match = self._combine_matches(matches) if matches else CustomerMatch(matched=False)
            
            # Update statistics
            self.stats['total_matches'] += 1
            if final_match.matched:
                self.stats['successful_matches'] += 1
            
            # Cache result
            if self.cache and final_match.matched:
                await self.cache.set(
                    cache_key,
                    final_match.__dict__,
                    ttl=self.cache_ttl
                )
            
            logger.debug(f"Customer matching completed. Matched: {final_match.matched}")
            return final_match
            
        except Exception as e:
            logger.error(f"Customer matching failed for transaction {transaction.id}: {e}")
            return CustomerMatch(matched=False)
    
    async def match_batch_transactions(
        self,
        transactions: List[BankTransaction],
        rules: Optional[List[MatchingRule]] = None
    ) -> List[CustomerMatch]:
        """
        Match customers for multiple transactions in batch.
        
        Args:
            transactions: List of transactions to match
            rules: Custom matching rules
            
        Returns:
            List of CustomerMatch results
        """
        logger.info(f"Batch matching customers for {len(transactions)} transactions")
        
        matches = []
        for transaction in transactions:
            match = await self.match_transaction(transaction, rules)
            matches.append(match)
        
        match_rate = sum(1 for m in matches if m.matched) / len(matches) * 100
        logger.info(f"Batch matching completed. Success rate: {match_rate:.1f}%")
        
        return matches
    
    async def _apply_matching_strategy(
        self,
        transaction: BankTransaction,
        strategy: MatchingStrategy,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Apply specific matching strategy."""
        
        if strategy == MatchingStrategy.ACCOUNT_NUMBER:
            return await self._match_by_account_number(transaction, parameters)
        elif strategy == MatchingStrategy.NAME_FUZZY:
            return await self._match_by_name_fuzzy(transaction, parameters)
        elif strategy == MatchingStrategy.REFERENCE_PATTERN:
            return await self._match_by_reference_pattern(transaction, parameters)
        elif strategy == MatchingStrategy.TRANSACTION_PATTERN:
            return await self._match_by_transaction_pattern(transaction, parameters)
        elif strategy == MatchingStrategy.COMBINED_SCORE:
            return await self._match_by_combined_score(transaction, parameters)
        
        return None
    
    async def _match_by_account_number(
        self,
        transaction: BankTransaction,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Match customer by account number."""
        
        if not transaction.account_number:
            return None
        
        # Search customer database
        customer = await self.customer_database.find_by_account_number(
            transaction.account_number
        )
        
        if customer:
            return CustomerMatch(
                matched=True,
                customer_info=customer,
                confidence_score=1.0,  # Exact match
                matching_strategy=MatchingStrategy.ACCOUNT_NUMBER,
                matching_details={
                    'matched_account': transaction.account_number,
                    'match_type': 'exact'
                }
            )
        
        return None
    
    async def _match_by_name_fuzzy(
        self,
        transaction: BankTransaction,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Match customer using fuzzy name matching."""
        
        if not transaction.description:
            return None
        
        # Extract potential names from transaction description
        potential_names = self._extract_names_from_description(transaction.description)
        
        if not potential_names:
            return None
        
        best_match = None
        best_score = 0.0
        
        # Search customers with similar names
        for name in potential_names:
            customers = await self.customer_database.search_by_name(name)
            
            for customer in customers:
                # Calculate fuzzy match score
                score = fuzzy_match(
                    normalize_text(name),
                    normalize_text(customer.name)
                )
                
                if score > best_score and score >= self.fuzzy_threshold:
                    best_score = score
                    best_match = CustomerMatch(
                        matched=True,
                        customer_info=customer,
                        confidence_score=score,
                        matching_strategy=MatchingStrategy.NAME_FUZZY,
                        matching_details={
                            'matched_name': name,
                            'customer_name': customer.name,
                            'fuzzy_score': score
                        }
                    )
        
        return best_match
    
    async def _match_by_reference_pattern(
        self,
        transaction: BankTransaction,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Match customer by reference patterns."""
        
        if not transaction.reference:
            return None
        
        # Extract patterns from reference
        patterns = self._extract_reference_patterns(transaction.reference)
        
        for pattern_type, pattern_value in patterns.items():
            if pattern_type == 'tin':
                customer = await self.customer_database.find_by_tin(pattern_value)
                if customer:
                    return CustomerMatch(
                        matched=True,
                        customer_info=customer,
                        confidence_score=0.95,
                        matching_strategy=MatchingStrategy.REFERENCE_PATTERN,
                        matching_details={
                            'pattern_type': pattern_type,
                            'pattern_value': pattern_value
                        }
                    )
            
            elif pattern_type == 'reference_code':
                customer = await self.customer_database.find_by_reference_code(pattern_value)
                if customer:
                    return CustomerMatch(
                        matched=True,
                        customer_info=customer,
                        confidence_score=0.9,
                        matching_strategy=MatchingStrategy.REFERENCE_PATTERN,
                        matching_details={
                            'pattern_type': pattern_type,
                            'pattern_value': pattern_value
                        }
                    )
        
        return None
    
    async def _match_by_transaction_pattern(
        self,
        transaction: BankTransaction,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Match customer by transaction patterns."""
        
        # Find customers with similar transaction patterns
        similar_transactions = await self.customer_database.find_similar_transactions(
            amount_range=(transaction.amount * 0.9, transaction.amount * 1.1),
            category=transaction.category,
            time_window_days=parameters.get('time_window_days', 30)
        )
        
        if not similar_transactions:
            return None
        
        # Score customers based on pattern similarity
        customer_scores = {}
        
        for similar_tx in similar_transactions:
            customer_id = similar_tx.customer_id
            if customer_id not in customer_scores:
                customer_scores[customer_id] = {
                    'score': 0.0,
                    'transaction_count': 0,
                    'customer': similar_tx.customer
                }
            
            # Calculate pattern similarity score
            similarity = self._calculate_transaction_similarity(transaction, similar_tx)
            customer_scores[customer_id]['score'] += similarity
            customer_scores[customer_id]['transaction_count'] += 1
        
        # Find best match
        best_customer_id = None
        best_score = 0.0
        
        for customer_id, data in customer_scores.items():
            # Average score weighted by transaction count
            avg_score = data['score'] / data['transaction_count']
            weight = min(data['transaction_count'] / 10, 1.0)  # Cap at 10 transactions
            final_score = avg_score * weight
            
            if final_score > best_score:
                best_score = final_score
                best_customer_id = customer_id
        
        if best_customer_id and best_score >= 0.7:
            customer_data = customer_scores[best_customer_id]
            return CustomerMatch(
                matched=True,
                customer_info=customer_data['customer'],
                confidence_score=best_score,
                matching_strategy=MatchingStrategy.TRANSACTION_PATTERN,
                matching_details={
                    'pattern_score': best_score,
                    'similar_transactions': customer_data['transaction_count']
                }
            )
        
        return None
    
    async def _match_by_combined_score(
        self,
        transaction: BankTransaction,
        parameters: Dict[str, Any]
    ) -> Optional[CustomerMatch]:
        """Match using combined scoring from multiple strategies."""
        
        # This would implement a sophisticated ML-based approach
        # For now, return None to use other strategies
        return None
    
    def _combine_matches(self, matches: List[CustomerMatch]) -> CustomerMatch:
        """Combine multiple matches into final result."""
        
        if not matches:
            return CustomerMatch(matched=False)
        
        if len(matches) == 1:
            return matches[0]
        
        # Sort by confidence score
        matches.sort(key=lambda m: m.confidence_score, reverse=True)
        
        best_match = matches[0]
        alternatives = matches[1:self.max_alternatives]
        
        # If top matches have same customer, increase confidence
        if len(matches) > 1 and matches[1].customer_info:
            if (best_match.customer_info and 
                best_match.customer_info.id == matches[1].customer_info.id):
                best_match.confidence_score = min(
                    best_match.confidence_score * 1.2, 1.0
                )
        
        best_match.alternative_matches = alternatives
        return best_match
    
    def _extract_names_from_description(self, description: str) -> List[str]:
        """Extract potential customer names from transaction description."""
        
        # Clean and normalize description
        normalized = normalize_text(description)
        
        # Simple name extraction patterns
        names = []
        
        # Look for patterns like "FROM JOHN DOE" or "TO JANE SMITH"
        from_to_pattern = re.compile(r'\b(?:from|to|for)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', re.IGNORECASE)
        matches = from_to_pattern.findall(normalized)
        names.extend(matches)
        
        # Look for capitalized words (potential names)
        word_pattern = re.compile(r'\b[A-Z][a-z]+\b')
        words = word_pattern.findall(description)
        
        # Group consecutive capitalized words as potential names
        current_name = []
        for word in words:
            if word.lower() not in ['the', 'and', 'of', 'for', 'from', 'to', 'ltd', 'limited', 'inc']:
                current_name.append(word)
            else:
                if len(current_name) >= 2:
                    names.append(' '.join(current_name))
                current_name = []
        
        if len(current_name) >= 2:
            names.append(' '.join(current_name))
        
        return list(set(names))  # Remove duplicates
    
    def _extract_reference_patterns(self, reference: str) -> Dict[str, str]:
        """Extract structured patterns from transaction reference."""
        
        patterns = {}
        
        for pattern_name, pattern_regex in self.patterns.items():
            matches = pattern_regex.findall(reference)
            if matches:
                patterns[pattern_name] = matches[0]  # Take first match
        
        return patterns
    
    def _calculate_transaction_similarity(
        self,
        tx1: BankTransaction,
        tx2: BankTransaction
    ) -> float:
        """Calculate similarity score between two transactions."""
        
        score = 0.0
        
        # Amount similarity (higher weight for closer amounts)
        if tx1.amount and tx2.amount:
            amount_ratio = min(tx1.amount, tx2.amount) / max(tx1.amount, tx2.amount)
            score += amount_ratio * 0.4
        
        # Category similarity
        if tx1.category == tx2.category:
            score += 0.3
        
        # Description similarity
        if tx1.description and tx2.description:
            desc_similarity = fuzzy_match(
                normalize_text(tx1.description),
                normalize_text(tx2.description)
            )
            score += desc_similarity * 0.2
        
        # Time pattern similarity (day of week, time of month)
        if tx1.date and tx2.date:
            # Same day of week
            if tx1.date.weekday() == tx2.date.weekday():
                score += 0.05
            
            # Similar day of month
            day_diff = abs(tx1.date.day - tx2.date.day)
            if day_diff <= 2:
                score += 0.05
        
        return min(score, 1.0)
    
    def _create_default_rules(self) -> List[MatchingRule]:
        """Create default matching rules."""
        
        return [
            MatchingRule(
                strategy=MatchingStrategy.ACCOUNT_NUMBER,
                weight=1.0,
                minimum_confidence=1.0
            ),
            MatchingRule(
                strategy=MatchingStrategy.REFERENCE_PATTERN,
                weight=0.9,
                minimum_confidence=0.9
            ),
            MatchingRule(
                strategy=MatchingStrategy.NAME_FUZZY,
                weight=0.8,
                minimum_confidence=0.8
            ),
            MatchingRule(
                strategy=MatchingStrategy.TRANSACTION_PATTERN,
                weight=0.7,
                minimum_confidence=0.7
            )
        ]
    
    def get_matching_stats(self) -> Dict[str, Any]:
        """Get customer matching statistics."""
        stats = self.stats.copy()
        if stats['total_matches'] > 0:
            stats['success_rate'] = stats['successful_matches'] / stats['total_matches']
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_matches']
        else:
            stats['success_rate'] = 0.0
            stats['cache_hit_rate'] = 0.0
        
        return stats
    
    def reset_stats(self):
        """Reset matching statistics."""
        self.stats = {
            'total_matches': 0,
            'successful_matches': 0,
            'cache_hits': 0,
            'strategy_usage': {strategy.value: 0 for strategy in MatchingStrategy}
        }