"""
Nigerian Rule-based Fallback System
===================================

Rule-based transaction classification system optimized for Nigerian business patterns.
Serves as fallback when API is unavailable and for obvious classification cases.
"""

import re
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Any, Set, Tuple
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass

from .classification_models import (
    TransactionClassificationRequest,
    TransactionClassificationResult,
    ClassificationMetadata,
    TaxCategory,
    UserContext,
    BusinessType
)

logger = logging.getLogger(__name__)

class BusinessIndicator(str, Enum):
    """Types of business indicators"""
    KEYWORD_MATCH = "keyword_match"
    AMOUNT_PATTERN = "amount_pattern"
    TIME_PATTERN = "time_pattern"
    LOCATION_PATTERN = "location_pattern"
    REPEAT_CUSTOMER = "repeat_customer"
    BUSINESS_HOURS = "business_hours"
    SEASONAL_PATTERN = "seasonal_pattern"

@dataclass
class PatternMatch:
    """Represents a pattern match with confidence"""
    
    indicator_type: BusinessIndicator
    match_text: str
    confidence: float
    weight: float
    reasoning: str

class PatternMatcher:
    """
    Advanced pattern matching for Nigerian business transactions
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatternMatcher")
        
        # Nigerian business patterns
        self.business_patterns = {
            'strong_business_keywords': {
                'keywords': [
                    'invoice', 'payment for goods', 'payment for services',
                    'contract payment', 'professional fee', 'consultation',
                    'commission', 'sales revenue', 'business income',
                    'service charge', 'delivery fee', 'installation'
                ],
                'weight': 0.8,
                'confidence': 0.9
            },
            'moderate_business_keywords': {
                'keywords': [
                    'payment', 'purchase', 'order', 'supply', 'delivery',
                    'work', 'job', 'project', 'service', 'goods',
                    'product', 'sales', 'revenue', 'income'
                ],
                'weight': 0.5,
                'confidence': 0.7
            },
            'weak_business_keywords': {
                'keywords': [
                    'transfer', 'money', 'cash', 'fund', 'deposit',
                    'credit', 'amount', 'sum', 'value'
                ],
                'weight': 0.2,
                'confidence': 0.4
            }
        }
        
        self.personal_patterns = {
            'strong_personal_keywords': {
                'keywords': [
                    'salary', 'wage', 'allowance', 'stipend', 'pension',
                    'family support', 'personal loan', 'gift', 'donation',
                    'pocket money', 'upkeep', 'maintenance', 'welfare'
                ],
                'weight': 0.9,
                'confidence': 0.95
            },
            'moderate_personal_keywords': {
                'keywords': [
                    'family', 'personal', 'loan', 'borrow', 'lend',
                    'refund', 'reversal', 'correction', 'return',
                    'airtime', 'data', 'recharge', 'top up'
                ],
                'weight': 0.6,
                'confidence': 0.8
            }
        }
        
        # Nigerian location patterns
        self.nigerian_business_locations = {
            'major_markets': [
                'alaba market', 'computer village', 'trade fair complex',
                'main market', 'central market', 'new market',
                'aba market', 'onitsha market', 'kurmi market',
                'wuse market', 'garki market', 'maitama market'
            ],
            'business_districts': [
                'victoria island', 'lagos island', 'ikoyi', 'lekki',
                'ikeja', 'surulere', 'yaba', 'apapa',
                'wuse', 'maitama', 'garki', 'central area',
                'port harcourt', 'aba', 'onitsha', 'enugu',
                'kano', 'kaduna', 'ibadan', 'jos'
            ],
            'industrial_areas': [
                'industrial estate', 'industrial layout',
                'manufacturing zone', 'factory', 'plant',
                'agbara', 'nnewi', 'aba industrial'
            ]
        }
        
        # Amount patterns for Nigerian market
        self.amount_patterns = {
            'round_amounts': {
                'divisors': [1000, 5000, 10000, 50000, 100000],
                'business_probability': 0.3,
                'reasoning': 'Round amounts often indicate business transactions'
            },
            'specific_amounts': {
                'ranges': [
                    (500, 2000, 'small_retail', 0.2),      # Small retail transactions
                    (2000, 10000, 'medium_retail', 0.4),   # Medium retail transactions  
                    (10000, 100000, 'business_service', 0.6),  # Business services
                    (100000, 1000000, 'major_business', 0.8),  # Major business transactions
                    (1000000, float('inf'), 'enterprise', 0.9)  # Enterprise transactions
                ]
            }
        }
        
        # Time patterns
        self.time_patterns = {
            'business_hours': {
                'weekday': (8, 18),      # 8 AM to 6 PM
                'saturday': (9, 16),     # 9 AM to 4 PM
                'sunday': (10, 14),      # Limited Sunday operations
                'weight': 0.3
            },
            'off_hours': {
                'late_night': (22, 6),   # 10 PM to 6 AM
                'early_morning': (5, 8), # 5 AM to 8 AM
                'weight': -0.2           # Negative weight for business probability
            }
        }
        
        self.logger.info("Pattern matcher initialized with Nigerian business patterns")
    
    def analyze_patterns(self, 
                        request: TransactionClassificationRequest) -> List[PatternMatch]:
        """Analyze transaction for pattern matches"""
        
        matches = []
        
        # Analyze narration patterns
        matches.extend(self._analyze_narration_patterns(request.narration))
        
        # Analyze amount patterns
        matches.extend(self._analyze_amount_patterns(request.amount))
        
        # Analyze time patterns
        matches.extend(self._analyze_time_patterns(request.time, request.date))
        
        # Analyze location patterns
        matches.extend(self._analyze_location_patterns(request.narration, request.user_context))
        
        # Analyze repeat customer patterns
        matches.extend(self._analyze_repeat_patterns(request))
        
        return matches
    
    def _analyze_narration_patterns(self, narration: str) -> List[PatternMatch]:
        """Analyze narration for business/personal patterns"""
        
        matches = []
        narration_lower = narration.lower()
        
        # Check business patterns
        for pattern_type, pattern_data in self.business_patterns.items():
            for keyword in pattern_data['keywords']:
                if keyword in narration_lower:
                    matches.append(PatternMatch(
                        indicator_type=BusinessIndicator.KEYWORD_MATCH,
                        match_text=keyword,
                        confidence=pattern_data['confidence'],
                        weight=pattern_data['weight'],
                        reasoning=f"Business keyword '{keyword}' found in narration"
                    ))
        
        # Check personal patterns (negative indicators for business)
        for pattern_type, pattern_data in self.personal_patterns.items():
            for keyword in pattern_data['keywords']:
                if keyword in narration_lower:
                    matches.append(PatternMatch(
                        indicator_type=BusinessIndicator.KEYWORD_MATCH,
                        match_text=keyword,
                        confidence=pattern_data['confidence'],
                        weight=-pattern_data['weight'],  # Negative weight
                        reasoning=f"Personal keyword '{keyword}' found in narration"
                    ))
        
        return matches
    
    def _analyze_amount_patterns(self, amount: Decimal) -> List[PatternMatch]:
        """Analyze amount for business patterns"""
        
        matches = []
        amount_float = float(amount)
        
        # Check for round amounts
        for divisor in self.amount_patterns['round_amounts']['divisors']:
            if amount_float % divisor == 0 and amount_float >= divisor:
                confidence = self.amount_patterns['round_amounts']['business_probability']
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.AMOUNT_PATTERN,
                    match_text=f"₦{amount_float:,.0f}",
                    confidence=confidence,
                    weight=0.2,
                    reasoning=f"Round amount (divisible by {divisor:,}) suggests business transaction"
                ))
                break  # Only count once per amount
        
        # Check amount ranges
        for min_amt, max_amt, category, probability in self.amount_patterns['specific_amounts']['ranges']:
            if min_amt <= amount_float < max_amt:
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.AMOUNT_PATTERN,
                    match_text=category,
                    confidence=probability,
                    weight=probability * 0.3,
                    reasoning=f"Amount ₦{amount_float:,.0f} in {category} range"
                ))
                break
        
        return matches
    
    def _analyze_time_patterns(self, 
                             transaction_time: Optional[str], 
                             transaction_date: datetime) -> List[PatternMatch]:
        """Analyze time patterns for business probability"""
        
        matches = []
        
        try:
            if not transaction_time or ':' not in transaction_time:
                return matches
            
            hour = int(transaction_time.split(':')[0])
            weekday = transaction_date.weekday()  # 0=Monday, 6=Sunday
            
            time_patterns = self.time_patterns
            
            # Check business hours
            if weekday < 5:  # Monday to Friday
                start, end = time_patterns['business_hours']['weekday']
                if start <= hour <= end:
                    matches.append(PatternMatch(
                        indicator_type=BusinessIndicator.BUSINESS_HOURS,
                        match_text=f"{hour}:00 on weekday",
                        confidence=0.7,
                        weight=time_patterns['business_hours']['weight'],
                        reasoning="Transaction during weekday business hours"
                    ))
            
            elif weekday == 5:  # Saturday
                start, end = time_patterns['business_hours']['saturday']
                if start <= hour <= end:
                    matches.append(PatternMatch(
                        indicator_type=BusinessIndicator.BUSINESS_HOURS,
                        match_text=f"{hour}:00 on Saturday",
                        confidence=0.5,
                        weight=time_patterns['business_hours']['weight'] * 0.7,
                        reasoning="Transaction during Saturday business hours"
                    ))
            
            else:  # Sunday
                start, end = time_patterns['business_hours']['sunday']
                if start <= hour <= end:
                    matches.append(PatternMatch(
                        indicator_type=BusinessIndicator.TIME_PATTERN,
                        match_text=f"{hour}:00 on Sunday",
                        confidence=0.3,
                        weight=0.1,
                        reasoning="Limited Sunday business operations"
                    ))
        
        except Exception as e:
            self.logger.warning(f"Error analyzing time patterns: {e}")
        
        return matches
    
    def _analyze_location_patterns(self, 
                                 narration: str, 
                                 user_context: UserContext) -> List[PatternMatch]:
        """Analyze location patterns in narration"""
        
        matches = []
        narration_lower = narration.lower()
        
        # Check for major markets
        for market in self.nigerian_business_locations['major_markets']:
            if market in narration_lower:
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.LOCATION_PATTERN,
                    match_text=market,
                    confidence=0.85,
                    weight=0.6,
                    reasoning=f"Transaction mentions major market: {market}"
                ))
        
        # Check for business districts
        for district in self.nigerian_business_locations['business_districts']:
            if district in narration_lower:
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.LOCATION_PATTERN,
                    match_text=district,
                    confidence=0.7,
                    weight=0.4,
                    reasoning=f"Transaction mentions business district: {district}"
                ))
        
        # Check for industrial areas
        for area in self.nigerian_business_locations['industrial_areas']:
            if area in narration_lower:
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.LOCATION_PATTERN,
                    match_text=area,
                    confidence=0.9,
                    weight=0.7,
                    reasoning=f"Transaction mentions industrial area: {area}"
                ))
        
        return matches
    
    def _analyze_repeat_patterns(self, request: TransactionClassificationRequest) -> List[PatternMatch]:
        """Analyze for repeat customer patterns"""
        
        matches = []
        
        # Check if sender appears in previous classifications
        if request.sender_name:
            previous_classifications = request.user_context.previous_classifications
            
            repeat_count = 0
            business_count = 0
            
            for prev in previous_classifications:
                if (prev.get('sender_name', '').lower() == request.sender_name.lower() or
                    prev.get('customer_name', '').lower() == request.sender_name.lower()):
                    repeat_count += 1
                    if prev.get('is_business_income', False):
                        business_count += 1
            
            if repeat_count > 0:
                business_probability = business_count / repeat_count
                matches.append(PatternMatch(
                    indicator_type=BusinessIndicator.REPEAT_CUSTOMER,
                    match_text=request.sender_name,
                    confidence=business_probability,
                    weight=0.5 * business_probability,
                    reasoning=f"Repeat sender: {business_count}/{repeat_count} previous business transactions"
                ))
        
        return matches

class NigerianRuleFallback:
    """
    Nigerian rule-based fallback classification system
    """
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
        self.logger = logging.getLogger(f"{__name__}.NigerianRuleFallback")
        
        # Classification thresholds
        self.thresholds = {
            'high_confidence_business': 0.8,
            'medium_confidence_business': 0.6,
            'low_confidence_business': 0.4,
            'human_review_threshold': 0.7
        }
        
        self.logger.info("Nigerian rule-based fallback system initialized")
    
    async def classify_transaction(self, 
                                 request: TransactionClassificationRequest) -> TransactionClassificationResult:
        """Classify transaction using rule-based system"""
        
        try:
            # Analyze patterns
            pattern_matches = self.pattern_matcher.analyze_patterns(request)
            
            # Calculate business probability score
            business_score = self._calculate_business_score(pattern_matches)
            
            # Determine classification
            is_business_income = business_score > 0.5
            confidence = self._calculate_confidence(business_score, pattern_matches)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(pattern_matches, business_score)
            
            # Determine if human review is needed
            requires_human_review = confidence < self.thresholds['human_review_threshold']
            
            # Extract business factors and risk factors
            business_factors, risk_factors = self._extract_factors(pattern_matches, is_business_income)
            
            # Build metadata
            metadata = ClassificationMetadata(
                classification_method="rule_based_nigerian",
                business_hours_factor=self._get_business_hours_factor(pattern_matches),
                amount_category=self._get_amount_category(pattern_matches),
                nigerian_patterns_detected=self._get_nigerian_patterns(pattern_matches),
                pattern_match_strength=business_score
            )
            
            # Build result
            result = TransactionClassificationResult(
                is_business_income=is_business_income,
                confidence=confidence,
                reasoning=reasoning,
                tax_category=TaxCategory.STANDARD_RATE if is_business_income else TaxCategory.UNKNOWN,
                vat_applicable=is_business_income,
                customer_name=self._extract_customer_name(request, pattern_matches),
                suggested_invoice_description=self._generate_invoice_description(request, pattern_matches),
                requires_human_review=requires_human_review,
                business_probability_factors=business_factors,
                risk_factors=risk_factors,
                similar_pattern_confidence=self._calculate_pattern_similarity(request),
                metadata=metadata,
                request_id=request.request_id
            )
            
            self.logger.debug(f"Rule-based classification completed: {is_business_income} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in rule-based classification: {e}")
            
            # Return safe default
            return self._get_safe_default_result(request)
    
    def _calculate_business_score(self, pattern_matches: List[PatternMatch]) -> float:
        """Calculate overall business probability score"""
        
        if not pattern_matches:
            return 0.5  # Neutral score
        
        # Weight and sum all matches
        weighted_sum = 0.0
        total_weight = 0.0
        
        for match in pattern_matches:
            weighted_sum += match.weight * match.confidence
            total_weight += abs(match.weight)
        
        if total_weight == 0:
            return 0.5
        
        # Normalize to 0-1 range
        normalized_score = (weighted_sum / total_weight + 1) / 2
        return max(0.0, min(1.0, normalized_score))
    
    def _calculate_confidence(self, 
                            business_score: float, 
                            pattern_matches: List[PatternMatch]) -> float:
        """Calculate confidence in the classification"""
        
        # Base confidence from business score
        if business_score > 0.8 or business_score < 0.2:
            base_confidence = 0.8  # High confidence for extreme scores
        elif 0.4 <= business_score <= 0.6:
            base_confidence = 0.4  # Low confidence for neutral scores
        else:
            base_confidence = 0.6  # Medium confidence
        
        # Adjust based on pattern strength
        strong_patterns = len([m for m in pattern_matches if m.confidence > 0.8])
        total_patterns = len(pattern_matches)
        
        if total_patterns > 0:
            pattern_strength = strong_patterns / total_patterns
            confidence = base_confidence + (pattern_strength * 0.2)
        else:
            confidence = base_confidence * 0.5  # Lower confidence with no patterns
        
        return max(0.1, min(0.9, confidence))
    
    def _generate_reasoning(self, 
                          pattern_matches: List[PatternMatch], 
                          business_score: float) -> str:
        """Generate human-readable reasoning for classification"""
        
        reasons = []
        
        # Summarize pattern matches
        business_patterns = [m for m in pattern_matches if m.weight > 0]
        personal_patterns = [m for m in pattern_matches if m.weight < 0]
        
        if business_patterns:
            business_indicators = [m.match_text for m in business_patterns[:3]]
            reasons.append(f"Business indicators: {', '.join(business_indicators)}")
        
        if personal_patterns:
            personal_indicators = [m.match_text for m in personal_patterns[:2]]
            reasons.append(f"Personal indicators: {', '.join(personal_indicators)}")
        
        # Add score summary
        reasons.append(f"Overall business probability: {business_score:.2f}")
        
        # Add methodology note
        reasons.append("Classification based on Nigerian business pattern analysis")
        
        return "; ".join(reasons)
    
    def _extract_factors(self, 
                        pattern_matches: List[PatternMatch], 
                        is_business: bool) -> Tuple[List[str], List[str]]:
        """Extract business probability factors and risk factors"""
        
        business_factors = []
        risk_factors = []
        
        for match in pattern_matches:
            if match.weight > 0 and match.confidence > 0.6:
                business_factors.append(f"{match.indicator_type.value}: {match.match_text}")
            elif match.weight < 0 and match.confidence > 0.6:
                risk_factors.append(f"Personal indicator: {match.match_text}")
        
        # Add general risk factors
        if len(pattern_matches) < 2:
            risk_factors.append("Limited pattern information available")
        
        total_confidence = sum(m.confidence for m in pattern_matches) / max(1, len(pattern_matches))
        if total_confidence < 0.6:
            risk_factors.append("Low overall pattern confidence")
        
        return business_factors, risk_factors
    
    def _get_business_hours_factor(self, pattern_matches: List[PatternMatch]) -> float:
        """Extract business hours factor from pattern matches"""
        
        for match in pattern_matches:
            if match.indicator_type == BusinessIndicator.BUSINESS_HOURS:
                return match.weight
        
        return 0.0
    
    def _get_amount_category(self, pattern_matches: List[PatternMatch]) -> str:
        """Extract amount category from pattern matches"""
        
        for match in pattern_matches:
            if match.indicator_type == BusinessIndicator.AMOUNT_PATTERN:
                return match.match_text
        
        return "unknown"
    
    def _get_nigerian_patterns(self, pattern_matches: List[PatternMatch]) -> List[str]:
        """Extract Nigerian-specific patterns from matches"""
        
        patterns = []
        
        for match in pattern_matches:
            if match.indicator_type == BusinessIndicator.LOCATION_PATTERN:
                patterns.append(f"Location: {match.match_text}")
            elif match.indicator_type == BusinessIndicator.KEYWORD_MATCH and match.weight > 0:
                patterns.append(f"Business keyword: {match.match_text}")
        
        return patterns
    
    def _extract_customer_name(self, 
                             request: TransactionClassificationRequest,
                             pattern_matches: List[PatternMatch]) -> Optional[str]:
        """Extract potential customer name"""
        
        # Use sender name if available and business transaction
        if request.sender_name:
            # Check if sender appears to be a business name
            sender_lower = request.sender_name.lower()
            business_terms = ['ltd', 'limited', 'company', 'enterprise', 'services', 'group']
            
            if any(term in sender_lower for term in business_terms):
                return None  # Don't use business names as customer names
            
            return request.sender_name
        
        return None
    
    def _generate_invoice_description(self, 
                                    request: TransactionClassificationRequest,
                                    pattern_matches: List[PatternMatch]) -> Optional[str]:
        """Generate suggested invoice description"""
        
        narration = request.narration.strip()
        
        # Clean up common bank transfer prefixes
        prefixes_to_remove = ['trf/', 'transfer/', 'payment/', 'pmt/']
        
        for prefix in prefixes_to_remove:
            if narration.lower().startswith(prefix):
                narration = narration[len(prefix):].strip()
        
        # If narration is very short or generic, create a generic description
        if len(narration) < 10 or narration.lower() in ['transfer', 'payment', 'deposit']:
            # Look for business patterns to create better description
            business_patterns = [m for m in pattern_matches if m.weight > 0]
            if business_patterns:
                return "Payment for goods/services"
            else:
                return "Business transaction"
        
        # Use cleaned narration
        return narration
    
    def _calculate_pattern_similarity(self, request: TransactionClassificationRequest) -> float:
        """Calculate similarity to previous patterns"""
        
        # Simplified similarity calculation
        # In a full implementation, this would compare to historical patterns
        
        previous_classifications = request.user_context.previous_classifications
        
        if not previous_classifications:
            return 0.0
        
        # Check for similar amounts, narrations, or senders
        similar_count = 0
        total_count = len(previous_classifications)
        
        for prev in previous_classifications:
            similarity_score = 0.0
            
            # Amount similarity
            prev_amount = prev.get('amount', 0)
            if prev_amount > 0:
                amount_ratio = min(float(request.amount) / prev_amount, prev_amount / float(request.amount))
                if amount_ratio > 0.8:  # Within 20% of each other
                    similarity_score += 0.3
            
            # Narration similarity (simplified)
            prev_narration = prev.get('narration', '').lower()
            current_narration = request.narration.lower()
            common_words = set(prev_narration.split()) & set(current_narration.split())
            if len(common_words) > 0:
                similarity_score += len(common_words) * 0.1
            
            # Sender similarity
            if (request.sender_name and 
                prev.get('sender_name', '').lower() == request.sender_name.lower()):
                similarity_score += 0.4
            
            if similarity_score > 0.5:
                similar_count += 1
        
        return similar_count / total_count if total_count > 0 else 0.0
    
    def _get_safe_default_result(self, request: TransactionClassificationRequest) -> TransactionClassificationResult:
        """Get safe default result when classification fails"""
        
        metadata = ClassificationMetadata(
            classification_method="rule_based_safe_default"
        )
        
        return TransactionClassificationResult(
            is_business_income=False,  # Conservative default
            confidence=0.1,
            reasoning="Classification failed - safe default applied",
            requires_human_review=True,
            risk_factors=["Classification system error"],
            metadata=metadata,
            request_id=request.request_id
        )