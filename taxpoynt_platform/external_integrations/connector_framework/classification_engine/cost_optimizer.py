"""
Cost Optimizer for Transaction Classification
============================================

Intelligent cost optimization for API-based classification.
Determines optimal classification method based on transaction complexity and user context.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from enum import Enum

from .classification_models import (
    TransactionClassificationRequest,
    ClassificationTier,
    UserContext,
    BusinessType
)

logger = logging.getLogger(__name__)

class OptimizationStrategy(str, Enum):
    """Cost optimization strategies"""
    AGGRESSIVE = "aggressive"      # Minimize costs, may sacrifice accuracy
    BALANCED = "balanced"          # Balance cost and accuracy
    ACCURACY_FIRST = "accuracy_first"  # Prioritize accuracy over cost
    ENTERPRISE = "enterprise"      # Enterprise-grade processing

class CostEstimate(dict):
    """Cost estimate for classification request"""
    
    def __init__(self, 
                 tier: ClassificationTier,
                 estimated_cost_ngn: Decimal,
                 confidence_estimate: float,
                 processing_time_estimate_ms: int,
                 reasoning: str):
        super().__init__({
            'tier': tier,
            'estimated_cost_ngn': estimated_cost_ngn,
            'confidence_estimate': confidence_estimate,
            'processing_time_estimate_ms': processing_time_estimate_ms,
            'reasoning': reasoning
        })
    
    @property
    def tier(self) -> ClassificationTier:
        return self['tier']
    
    @property
    def estimated_cost_ngn(self) -> Decimal:
        return self['estimated_cost_ngn']
    
    @property
    def confidence_estimate(self) -> float:
        return self['confidence_estimate']
    
    @property
    def processing_time_estimate_ms(self) -> int:
        return self['processing_time_estimate_ms']
    
    @property
    def reasoning(self) -> str:
        return self['reasoning']

class CostOptimizer:
    """
    Intelligent cost optimization for API-based classification
    """
    
    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        """Initialize cost optimizer with strategy"""
        self.strategy = strategy
        self.logger = logging.getLogger(f"{__name__}.CostOptimizer")
        
        # Cost estimates (in NGN)
        self.tier_costs = {
            ClassificationTier.RULE_BASED: Decimal('0.0'),      # Free
            ClassificationTier.API_LITE: Decimal('0.8'),        # GPT-3.5-turbo
            ClassificationTier.API_PREMIUM: Decimal('3.2'),     # GPT-4o-mini
            ClassificationTier.API_ADVANCED: Decimal('48.0')    # GPT-4
        }
        
        # Expected confidence scores
        self.tier_confidence = {
            ClassificationTier.RULE_BASED: 0.75,
            ClassificationTier.API_LITE: 0.85,
            ClassificationTier.API_PREMIUM: 0.92,
            ClassificationTier.API_ADVANCED: 0.95
        }
        
        # Processing time estimates (ms)
        self.tier_processing_time = {
            ClassificationTier.RULE_BASED: 50,
            ClassificationTier.API_LITE: 1500,
            ClassificationTier.API_PREMIUM: 2000,
            ClassificationTier.API_ADVANCED: 3000
        }
        
        self.logger.info(f"Cost optimizer initialized with {strategy} strategy")
    
    def determine_classification_tier(self, 
                                    request: TransactionClassificationRequest,
                                    user_context: UserContext) -> ClassificationTier:
        """
        Determines optimal classification method:
        - 'rule_based': Free rule-based for obvious cases
        - 'api_lite': GPT-3.5-turbo for simple cases  
        - 'api_premium': GPT-4o-mini for complex cases
        - 'api_advanced': GPT-4 for very complex cases
        """
        
        try:
            # Analyze transaction complexity
            complexity_score = self._calculate_complexity_score(request, user_context)
            
            # Get user tier preferences
            user_tier_preference = self._get_user_tier_preference(user_context)
            
            # Apply optimization strategy
            recommended_tier = self._apply_strategy(
                complexity_score, 
                user_tier_preference, 
                request, 
                user_context
            )
            
            self.logger.debug(f"Recommended tier: {recommended_tier} for request {request.request_id}")
            return recommended_tier
            
        except Exception as e:
            self.logger.error(f"Error determining classification tier: {e}")
            # Default to rule-based on error
            return ClassificationTier.RULE_BASED
    
    def get_cost_estimate(self, 
                         request: TransactionClassificationRequest,
                         user_context: UserContext,
                         tier: Optional[ClassificationTier] = None) -> CostEstimate:
        """Get cost estimate for classification request"""
        
        if tier is None:
            tier = self.determine_classification_tier(request, user_context)
        
        cost = self.tier_costs[tier]
        confidence = self.tier_confidence[tier]
        processing_time = self.tier_processing_time[tier]
        
        reasoning = self._get_tier_reasoning(tier, request, user_context)
        
        return CostEstimate(
            tier=tier,
            estimated_cost_ngn=cost,
            confidence_estimate=confidence,
            processing_time_estimate_ms=processing_time,
            reasoning=reasoning
        )
    
    def compare_tiers(self, 
                     request: TransactionClassificationRequest,
                     user_context: UserContext) -> Dict[ClassificationTier, CostEstimate]:
        """Compare all available tiers for the request"""
        
        estimates = {}
        
        for tier in ClassificationTier:
            estimates[tier] = self.get_cost_estimate(request, user_context, tier)
        
        return estimates
    
    def get_optimization_recommendation(self, 
                                      request: TransactionClassificationRequest,
                                      user_context: UserContext) -> Dict[str, Any]:
        """Get comprehensive optimization recommendation"""
        
        # Get all tier estimates
        tier_estimates = self.compare_tiers(request, user_context)
        
        # Recommended tier
        recommended_tier = self.determine_classification_tier(request, user_context)
        
        # Calculate potential savings
        premium_cost = tier_estimates[ClassificationTier.API_PREMIUM].estimated_cost_ngn
        recommended_cost = tier_estimates[recommended_tier].estimated_cost_ngn
        savings_ngn = premium_cost - recommended_cost
        
        # Build recommendation
        return {
            'recommended_tier': recommended_tier,
            'estimated_cost_ngn': float(recommended_cost),
            'estimated_confidence': tier_estimates[recommended_tier].confidence_estimate,
            'potential_savings_ngn': float(savings_ngn),
            'optimization_strategy': self.strategy,
            'tier_comparison': {
                tier.value: {
                    'cost_ngn': float(estimate.estimated_cost_ngn),
                    'confidence': estimate.confidence_estimate,
                    'processing_time_ms': estimate.processing_time_estimate_ms
                } for tier, estimate in tier_estimates.items()
            },
            'reasoning': tier_estimates[recommended_tier].reasoning
        }
    
    def _calculate_complexity_score(self, 
                                  request: TransactionClassificationRequest,
                                  user_context: UserContext) -> float:
        """Calculate transaction complexity score (0.0 to 1.0)"""
        
        score = 0.0
        
        # Narration complexity
        narration = request.narration.lower()
        
        # Simple cases (low complexity)
        simple_indicators = [
            'salary', 'allowance', 'family', 'personal', 'loan',
            'refund', 'reversal', 'airtime', 'data'
        ]
        if any(indicator in narration for indicator in simple_indicators):
            score -= 0.3
        
        # Clear business indicators (medium complexity)
        business_indicators = [
            'payment', 'invoice', 'goods', 'services', 'business'
        ]
        if any(indicator in narration for indicator in business_indicators):
            score += 0.2
        
        # Ambiguous narration (high complexity)
        if len(narration.split()) <= 3:  # Very short descriptions
            score += 0.3
        
        # Amount-based complexity
        amount = float(request.amount)
        if amount > 1_000_000:  # Large amounts need more careful analysis
            score += 0.2
        elif amount < 5_000:    # Small amounts might be personal
            score += 0.1
        
        # User history complexity
        if len(user_context.previous_classifications) < 10:
            score += 0.2  # New users need more careful analysis
        
        # Business context complexity
        if user_context.business_context.industry == BusinessType.GENERAL:
            score += 0.1  # Unknown industry increases complexity
        
        # Time-based complexity
        if not request.time:
            score += 0.1  # Missing time information
        
        # Normalize to 0.0-1.0 range
        return max(0.0, min(1.0, score + 0.5))
    
    def _get_user_tier_preference(self, user_context: UserContext) -> ClassificationTier:
        """Get user's tier preference based on subscription and history"""
        
        subscription_tier = user_context.subscription_tier.lower()
        
        # Map subscription tiers to classification tiers
        tier_mapping = {
            'starter': ClassificationTier.RULE_BASED,
            'professional': ClassificationTier.API_PREMIUM,
            'enterprise': ClassificationTier.API_PREMIUM,
            'scale': ClassificationTier.API_ADVANCED
        }
        
        return tier_mapping.get(subscription_tier, ClassificationTier.RULE_BASED)
    
    def _apply_strategy(self, 
                       complexity_score: float,
                       user_tier_preference: ClassificationTier,
                       request: TransactionClassificationRequest,
                       user_context: UserContext) -> ClassificationTier:
        """Apply optimization strategy to determine final tier"""
        
        if self.strategy == OptimizationStrategy.AGGRESSIVE:
            # Minimize costs aggressively
            if complexity_score < 0.3:
                return ClassificationTier.RULE_BASED
            elif complexity_score < 0.7:
                return ClassificationTier.API_LITE
            else:
                return ClassificationTier.API_PREMIUM
        
        elif self.strategy == OptimizationStrategy.BALANCED:
            # Balance cost and accuracy
            if complexity_score < 0.2:
                return ClassificationTier.RULE_BASED
            elif complexity_score < 0.5:
                return min(ClassificationTier.API_LITE, user_tier_preference)
            elif complexity_score < 0.8:
                return min(ClassificationTier.API_PREMIUM, user_tier_preference)
            else:
                return user_tier_preference
        
        elif self.strategy == OptimizationStrategy.ACCURACY_FIRST:
            # Prioritize accuracy
            if complexity_score < 0.1:
                return ClassificationTier.RULE_BASED
            elif complexity_score < 0.3:
                return ClassificationTier.API_LITE
            elif complexity_score < 0.6:
                return ClassificationTier.API_PREMIUM
            else:
                return ClassificationTier.API_ADVANCED
        
        else:  # ENTERPRISE
            # Enterprise-grade processing
            if complexity_score < 0.1 and user_context.trust_level > 0.9:
                return ClassificationTier.RULE_BASED
            else:
                return max(ClassificationTier.API_PREMIUM, user_tier_preference)
    
    def _get_tier_reasoning(self, 
                          tier: ClassificationTier,
                          request: TransactionClassificationRequest,
                          user_context: UserContext) -> str:
        """Get reasoning for tier selection"""
        
        complexity_score = self._calculate_complexity_score(request, user_context)
        
        reasons = []
        
        if tier == ClassificationTier.RULE_BASED:
            reasons.append("Simple transaction pattern detected")
            if complexity_score < 0.3:
                reasons.append("Low complexity score")
        
        elif tier == ClassificationTier.API_LITE:
            reasons.append("Moderate complexity requiring API assistance")
            reasons.append("Cost-optimized choice")
        
        elif tier == ClassificationTier.API_PREMIUM:
            reasons.append("Complex transaction requiring advanced analysis")
            if complexity_score > 0.6:
                reasons.append("High complexity score")
        
        elif tier == ClassificationTier.API_ADVANCED:
            reasons.append("Very complex transaction requiring highest accuracy")
            reasons.append("Enterprise-grade processing")
        
        # Add strategy context
        reasons.append(f"Strategy: {self.strategy}")
        
        # Add user context
        subscription = user_context.subscription_tier
        reasons.append(f"User subscription: {subscription}")
        
        return "; ".join(reasons)
    
    def get_monthly_cost_projection(self, 
                                  monthly_transactions: int,
                                  user_context: UserContext,
                                  tier_distribution: Optional[Dict[ClassificationTier, float]] = None) -> Dict[str, Any]:
        """Project monthly costs based on transaction volume and tier distribution"""
        
        if tier_distribution is None:
            # Default distribution based on strategy
            if self.strategy == OptimizationStrategy.AGGRESSIVE:
                tier_distribution = {
                    ClassificationTier.RULE_BASED: 0.6,
                    ClassificationTier.API_LITE: 0.3,
                    ClassificationTier.API_PREMIUM: 0.1,
                    ClassificationTier.API_ADVANCED: 0.0
                }
            elif self.strategy == OptimizationStrategy.BALANCED:
                tier_distribution = {
                    ClassificationTier.RULE_BASED: 0.4,
                    ClassificationTier.API_LITE: 0.2,
                    ClassificationTier.API_PREMIUM: 0.35,
                    ClassificationTier.API_ADVANCED: 0.05
                }
            else:  # ACCURACY_FIRST or ENTERPRISE
                tier_distribution = {
                    ClassificationTier.RULE_BASED: 0.2,
                    ClassificationTier.API_LITE: 0.1,
                    ClassificationTier.API_PREMIUM: 0.5,
                    ClassificationTier.API_ADVANCED: 0.2
                }
        
        # Calculate costs
        total_cost = Decimal('0.0')
        tier_breakdown = {}
        
        for tier, percentage in tier_distribution.items():
            tier_transactions = int(monthly_transactions * percentage)
            tier_cost = self.tier_costs[tier] * tier_transactions
            total_cost += tier_cost
            
            tier_breakdown[tier.value] = {
                'transactions': tier_transactions,
                'percentage': percentage * 100,
                'total_cost_ngn': float(tier_cost),
                'cost_per_transaction_ngn': float(self.tier_costs[tier])
            }
        
        return {
            'monthly_transactions': monthly_transactions,
            'total_monthly_cost_ngn': float(total_cost),
            'average_cost_per_transaction_ngn': float(total_cost / monthly_transactions) if monthly_transactions > 0 else 0.0,
            'optimization_strategy': self.strategy,
            'tier_breakdown': tier_breakdown,
            'cost_savings_vs_premium': float(
                (self.tier_costs[ClassificationTier.API_PREMIUM] * monthly_transactions) - total_cost
            )
        }