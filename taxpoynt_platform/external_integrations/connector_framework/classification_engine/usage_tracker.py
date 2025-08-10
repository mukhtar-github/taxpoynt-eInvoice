"""
Classification Usage Tracker
============================

Comprehensive usage tracking and analytics for classification engine.
Monitors costs, performance, and provides business insights.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

from .classification_models import (
    TransactionClassificationRequest,
    TransactionClassificationResult,
    ClassificationTier,
    UserContext
)

logger = logging.getLogger(__name__)

class UsageMetricType(str, Enum):
    """Types of usage metrics to track"""
    CLASSIFICATION_REQUEST = "classification_request"
    API_CALL = "api_call" 
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    RULE_FALLBACK = "rule_fallback"
    USER_FEEDBACK = "user_feedback"
    COST_INCURRED = "cost_incurred"
    PROCESSING_TIME = "processing_time"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class UsageEvent:
    """Individual usage event"""
    
    event_id: str
    event_type: UsageMetricType
    user_id: str
    organization_id: str
    timestamp: datetime
    
    # Classification details
    request_id: Optional[str] = None
    classification_tier: Optional[ClassificationTier] = None
    confidence_score: Optional[float] = None
    is_business_income: Optional[bool] = None
    
    # Cost tracking
    cost_ngn: Decimal = Decimal('0.0')
    api_tokens_used: Optional[int] = None
    
    # Performance tracking
    processing_time_ms: Optional[int] = None
    cache_hit: bool = False
    
    # Quality tracking
    user_feedback_provided: bool = False
    user_agreed: Optional[bool] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UsageMetrics:
    """Aggregated usage metrics"""
    
    period_start: datetime
    period_end: datetime
    
    # Volume metrics
    total_classifications: int = 0
    successful_classifications: int = 0
    failed_classifications: int = 0
    
    # Tier distribution
    rule_based_count: int = 0
    api_lite_count: int = 0
    api_premium_count: int = 0
    api_advanced_count: int = 0
    
    # Performance metrics
    average_processing_time_ms: float = 0.0
    median_processing_time_ms: float = 0.0
    p95_processing_time_ms: float = 0.0
    
    # Cache metrics
    cache_hit_count: int = 0
    cache_miss_count: int = 0
    cache_hit_rate: float = 0.0
    
    # Cost metrics
    total_cost_ngn: Decimal = Decimal('0.0')
    average_cost_per_classification_ngn: Decimal = Decimal('0.0')
    cost_saved_from_cache_ngn: Decimal = Decimal('0.0')
    
    # Quality metrics
    average_confidence: float = 0.0
    business_income_percentage: float = 0.0
    human_review_percentage: float = 0.0
    user_agreement_rate: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    common_errors: List[str] = field(default_factory=list)

@dataclass
class CostAnalytics:
    """Cost analysis and projections"""
    
    current_period_cost_ngn: Decimal
    projected_monthly_cost_ngn: Decimal
    cost_trend_percentage: float
    
    # Breakdown by tier
    cost_by_tier: Dict[str, Decimal] = field(default_factory=dict)
    
    # Optimization opportunities
    potential_savings_ngn: Decimal = Decimal('0.0')
    optimization_recommendations: List[str] = field(default_factory=list)
    
    # Budget tracking
    budget_utilization_percentage: Optional[float] = None
    days_until_budget_exhausted: Optional[int] = None

class ClassificationUsageTracker:
    """
    Comprehensive usage tracking and analytics for classification engine
    """
    
    def __init__(self, 
                 database_connection: Optional[Any] = None,
                 storage_backend: str = "memory"):
        """Initialize usage tracker"""
        
        self.database_connection = database_connection
        self.storage_backend = storage_backend
        self.logger = logging.getLogger(f"{__name__}.ClassificationUsageTracker")
        
        # In-memory storage for development/testing
        self.usage_events: List[UsageEvent] = []
        
        # Tier cost mapping (NGN)
        self.tier_costs = {
            ClassificationTier.RULE_BASED: Decimal('0.0'),
            ClassificationTier.API_LITE: Decimal('0.8'),
            ClassificationTier.API_PREMIUM: Decimal('3.2'),
            ClassificationTier.API_ADVANCED: Decimal('48.0')
        }
        
        self.logger.info(f"Usage tracker initialized with {storage_backend} backend")
    
    async def track_classification_request(self, 
                                         request: TransactionClassificationRequest,
                                         result: TransactionClassificationResult) -> str:
        """Track a classification request and result"""
        
        event_id = f"cls_{int(datetime.utcnow().timestamp())}_{request.request_id}"
        
        # Determine cost
        cost = self.tier_costs.get(
            ClassificationTier(result.metadata.classification_method.split('_')[0] + '_' + 
                             result.metadata.classification_method.split('_')[1] 
                             if 'api' in result.metadata.classification_method else 'rule_based'),
            result.metadata.api_cost_estimate_ngn
        )
        
        event = UsageEvent(
            event_id=event_id,
            event_type=UsageMetricType.CLASSIFICATION_REQUEST,
            user_id=request.user_context.user_id,
            organization_id=request.user_context.organization_id,
            timestamp=datetime.utcnow(),
            request_id=request.request_id,
            classification_tier=request.classification_tier,
            confidence_score=result.confidence,
            is_business_income=result.is_business_income,
            cost_ngn=cost,
            api_tokens_used=result.metadata.prompt_tokens + result.metadata.completion_tokens if result.metadata.prompt_tokens else None,
            processing_time_ms=result.metadata.processing_time_ms,
            cache_hit=result.metadata.cache_hit,
            metadata={
                'classification_method': result.metadata.classification_method,
                'requires_human_review': result.requires_human_review,
                'nigerian_patterns_detected': result.metadata.nigerian_patterns_detected,
                'amount_category': result.metadata.amount_category
            }
        )
        
        await self._store_event(event)
        return event_id
    
    async def track_user_feedback(self, 
                                request_id: str,
                                user_id: str,
                                organization_id: str,
                                feedback_correct: bool) -> str:
        """Track user feedback on classification"""
        
        event_id = f"feedback_{int(datetime.utcnow().timestamp())}_{request_id}"
        
        event = UsageEvent(
            event_id=event_id,
            event_type=UsageMetricType.USER_FEEDBACK,
            user_id=user_id,
            organization_id=organization_id,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            user_feedback_provided=True,
            user_agreed=feedback_correct,
            metadata={'feedback_type': 'correctness_rating'}
        )
        
        await self._store_event(event)
        return event_id
    
    async def track_error(self, 
                         request: TransactionClassificationRequest,
                         error_type: str,
                         error_message: str) -> str:
        """Track classification errors"""
        
        event_id = f"error_{int(datetime.utcnow().timestamp())}_{request.request_id}"
        
        event = UsageEvent(
            event_id=event_id,
            event_type=UsageMetricType.ERROR_OCCURRED,
            user_id=request.user_context.user_id,
            organization_id=request.user_context.organization_id,
            timestamp=datetime.utcnow(),
            request_id=request.request_id,
            metadata={
                'error_type': error_type,
                'error_message': error_message,
                'classification_tier': request.classification_tier
            }
        )
        
        await self._store_event(event)
        return event_id
    
    async def get_usage_metrics(self, 
                              user_id: Optional[str] = None,
                              organization_id: Optional[str] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> UsageMetrics:
        """Get aggregated usage metrics for a period"""
        
        # Default to last 30 days if no dates provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Filter events
        filtered_events = await self._filter_events(
            user_id=user_id,
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate metrics
        metrics = await self._calculate_metrics(filtered_events, start_date, end_date)
        return metrics
    
    async def get_cost_analytics(self, 
                               organization_id: str,
                               period_days: int = 30) -> CostAnalytics:
        """Get cost analytics and projections"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        # Get cost events
        cost_events = await self._filter_events(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date,
            event_types=[UsageMetricType.CLASSIFICATION_REQUEST]
        )
        
        # Calculate current period cost
        current_cost = sum(event.cost_ngn for event in cost_events)
        
        # Project monthly cost
        daily_cost = current_cost / period_days
        projected_monthly_cost = daily_cost * 30
        
        # Calculate cost trend (compare with previous period)
        previous_start = start_date - timedelta(days=period_days)
        previous_events = await self._filter_events(
            organization_id=organization_id,
            start_date=previous_start,
            end_date=start_date,
            event_types=[UsageMetricType.CLASSIFICATION_REQUEST]
        )
        
        previous_cost = sum(event.cost_ngn for event in previous_events)
        cost_trend = ((current_cost - previous_cost) / max(previous_cost, Decimal('0.01'))) * 100
        
        # Cost breakdown by tier
        cost_by_tier = {}
        for tier in ClassificationTier:
            tier_cost = sum(
                event.cost_ngn for event in cost_events
                if event.classification_tier == tier
            )
            cost_by_tier[tier.value] = tier_cost
        
        # Optimization recommendations
        recommendations = await self._generate_optimization_recommendations(cost_events)
        
        # Calculate potential savings
        potential_savings = await self._calculate_potential_savings(cost_events)
        
        return CostAnalytics(
            current_period_cost_ngn=current_cost,
            projected_monthly_cost_ngn=projected_monthly_cost,
            cost_trend_percentage=float(cost_trend),
            cost_by_tier=cost_by_tier,
            potential_savings_ngn=potential_savings,
            optimization_recommendations=recommendations
        )
    
    async def get_performance_insights(self, 
                                     organization_id: str,
                                     period_days: int = 7) -> Dict[str, Any]:
        """Get performance insights and recommendations"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)
        
        events = await self._filter_events(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Performance analysis
        classification_events = [e for e in events if e.event_type == UsageMetricType.CLASSIFICATION_REQUEST]
        
        if not classification_events:
            return {'message': 'No classification activity in the specified period'}
        
        # Processing time analysis
        processing_times = [e.processing_time_ms for e in classification_events if e.processing_time_ms]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Confidence analysis
        confidences = [e.confidence_score for e in classification_events if e.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Cache performance
        cache_hits = sum(1 for e in classification_events if e.cache_hit)
        cache_hit_rate = (cache_hits / len(classification_events)) * 100
        
        # Business vs personal classification ratio
        business_classifications = sum(1 for e in classification_events if e.is_business_income)
        business_percentage = (business_classifications / len(classification_events)) * 100
        
        # Error analysis
        error_events = [e for e in events if e.event_type == UsageMetricType.ERROR_OCCURRED]
        error_rate = (len(error_events) / len(classification_events)) * 100
        
        return {
            'period_summary': {
                'total_classifications': len(classification_events),
                'period_days': period_days,
                'average_per_day': len(classification_events) / period_days
            },
            'performance_metrics': {
                'average_processing_time_ms': round(avg_processing_time, 2),
                'average_confidence': round(avg_confidence, 3),
                'cache_hit_rate_percent': round(cache_hit_rate, 2),
                'error_rate_percent': round(error_rate, 2)
            },
            'classification_insights': {
                'business_income_percentage': round(business_percentage, 2),
                'personal_transaction_percentage': round(100 - business_percentage, 2),
                'high_confidence_classifications': len([c for c in confidences if c > 0.8]),
                'low_confidence_classifications': len([c for c in confidences if c < 0.6])
            },
            'recommendations': await self._generate_performance_recommendations(
                avg_processing_time, avg_confidence, cache_hit_rate, error_rate
            )
        }
    
    async def _store_event(self, event: UsageEvent):
        """Store usage event"""
        
        try:
            if self.storage_backend == "database" and self.database_connection:
                # Store in database
                await self._store_event_in_database(event)
            else:
                # Store in memory (for development)
                self.usage_events.append(event)
                
                # Limit memory usage
                if len(self.usage_events) > 10000:
                    self.usage_events = self.usage_events[-5000:]  # Keep last 5000 events
            
            self.logger.debug(f"Usage event stored: {event.event_type}")
            
        except Exception as e:
            self.logger.error(f"Error storing usage event: {e}")
    
    async def _filter_events(self, 
                           user_id: Optional[str] = None,
                           organization_id: Optional[str] = None,
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           event_types: Optional[List[UsageMetricType]] = None) -> List[UsageEvent]:
        """Filter events based on criteria"""
        
        filtered = self.usage_events
        
        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]
        
        if organization_id:
            filtered = [e for e in filtered if e.organization_id == organization_id]
        
        if start_date:
            filtered = [e for e in filtered if e.timestamp >= start_date]
        
        if end_date:
            filtered = [e for e in filtered if e.timestamp <= end_date]
        
        if event_types:
            filtered = [e for e in filtered if e.event_type in event_types]
        
        return filtered
    
    async def _calculate_metrics(self, 
                               events: List[UsageEvent],
                               start_date: datetime,
                               end_date: datetime) -> UsageMetrics:
        """Calculate aggregated metrics from events"""
        
        classification_events = [e for e in events if e.event_type == UsageMetricType.CLASSIFICATION_REQUEST]
        
        # Basic counts
        total_classifications = len(classification_events)
        successful_classifications = len([e for e in classification_events if e.confidence_score and e.confidence_score > 0.5])
        failed_classifications = total_classifications - successful_classifications
        
        # Tier distribution
        tier_counts = {
            ClassificationTier.RULE_BASED: 0,
            ClassificationTier.API_LITE: 0,
            ClassificationTier.API_PREMIUM: 0,
            ClassificationTier.API_ADVANCED: 0
        }
        
        for event in classification_events:
            if event.classification_tier:
                tier_counts[event.classification_tier] += 1
        
        # Performance metrics
        processing_times = [e.processing_time_ms for e in classification_events if e.processing_time_ms]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0.0
        
        # Cache metrics
        cache_hits = sum(1 for e in classification_events if e.cache_hit)
        cache_misses = total_classifications - cache_hits
        cache_hit_rate = (cache_hits / max(1, total_classifications)) * 100
        
        # Cost metrics
        total_cost = sum(e.cost_ngn for e in classification_events)
        avg_cost = total_cost / max(1, total_classifications)
        
        # Quality metrics
        confidences = [e.confidence_score for e in classification_events if e.confidence_score]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        business_count = sum(1 for e in classification_events if e.is_business_income)
        business_percentage = (business_count / max(1, total_classifications)) * 100
        
        # User feedback metrics
        feedback_events = [e for e in events if e.event_type == UsageMetricType.USER_FEEDBACK]
        agreed_feedback = sum(1 for e in feedback_events if e.user_agreed)
        agreement_rate = (agreed_feedback / max(1, len(feedback_events))) * 100
        
        return UsageMetrics(
            period_start=start_date,
            period_end=end_date,
            total_classifications=total_classifications,
            successful_classifications=successful_classifications,
            failed_classifications=failed_classifications,
            rule_based_count=tier_counts[ClassificationTier.RULE_BASED],
            api_lite_count=tier_counts[ClassificationTier.API_LITE],
            api_premium_count=tier_counts[ClassificationTier.API_PREMIUM],
            api_advanced_count=tier_counts[ClassificationTier.API_ADVANCED],
            average_processing_time_ms=avg_processing_time,
            cache_hit_count=cache_hits,
            cache_miss_count=cache_misses,
            cache_hit_rate=cache_hit_rate,
            total_cost_ngn=total_cost,
            average_cost_per_classification_ngn=avg_cost,
            average_confidence=avg_confidence,
            business_income_percentage=business_percentage,
            user_agreement_rate=agreement_rate
        )
    
    async def _generate_optimization_recommendations(self, events: List[UsageEvent]) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        if not events:
            return recommendations
        
        # Analyze tier usage
        tier_costs = {}
        tier_counts = {}
        
        for event in events:
            tier = event.classification_tier or ClassificationTier.RULE_BASED
            tier_costs[tier] = tier_costs.get(tier, Decimal('0.0')) + event.cost_ngn
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Check for potential optimizations
        total_cost = sum(tier_costs.values())
        
        if tier_costs.get(ClassificationTier.API_ADVANCED, Decimal('0.0')) > total_cost * Decimal('0.5'):
            recommendations.append("Consider reducing API_ADVANCED usage - represents >50% of costs")
        
        if tier_counts.get(ClassificationTier.RULE_BASED, 0) < len(events) * 0.3:
            recommendations.append("Increase rule-based classification for obvious cases to reduce costs")
        
        # Cache optimization
        cache_hits = sum(1 for e in events if e.cache_hit)
        cache_hit_rate = cache_hits / len(events)
        
        if cache_hit_rate < 0.4:
            recommendations.append("Low cache hit rate - consider adjusting cache strategy")
        
        # Processing efficiency
        processing_times = [e.processing_time_ms for e in events if e.processing_time_ms]
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            if avg_time > 3000:  # 3 seconds
                recommendations.append("High processing times detected - review classification complexity")
        
        return recommendations
    
    async def _calculate_potential_savings(self, events: List[UsageEvent]) -> Decimal:
        """Calculate potential cost savings from optimization"""
        
        # Estimate savings from better caching and tier optimization
        total_cost = sum(e.cost_ngn for e in events)
        
        # Assume 20% savings from better optimization
        potential_savings = total_cost * Decimal('0.2')
        
        return potential_savings
    
    async def _generate_performance_recommendations(self, 
                                                  avg_processing_time: float,
                                                  avg_confidence: float,
                                                  cache_hit_rate: float,
                                                  error_rate: float) -> List[str]:
        """Generate performance improvement recommendations"""
        
        recommendations = []
        
        if avg_processing_time > 2000:
            recommendations.append("High processing times - consider caching optimization")
        
        if avg_confidence < 0.7:
            recommendations.append("Low average confidence - review classification patterns")
        
        if cache_hit_rate < 50:
            recommendations.append("Cache hit rate below 50% - adjust cache strategy")
        
        if error_rate > 5:
            recommendations.append("Error rate above 5% - review error handling")
        
        if not recommendations:
            recommendations.append("Performance metrics are healthy - continue current approach")
        
        return recommendations
    
    async def _store_event_in_database(self, event: UsageEvent):
        """Store event in database (placeholder for database implementation)"""
        
        # TODO: Implement database storage
        # This would use the actual database connection to store events
        # For now, this is a placeholder
        
        self.logger.debug(f"Database storage not implemented - event {event.event_id} would be stored here")
    
    async def get_daily_summary(self, 
                              organization_id: str,
                              date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get daily usage summary"""
        
        if not date:
            date = datetime.utcnow().date()
        
        start_date = datetime.combine(date, datetime.min.time())
        end_date = start_date + timedelta(days=1)
        
        events = await self._filter_events(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        classification_events = [e for e in events if e.event_type == UsageMetricType.CLASSIFICATION_REQUEST]
        
        return {
            'date': date.isoformat(),
            'total_classifications': len(classification_events),
            'total_cost_ngn': float(sum(e.cost_ngn for e in classification_events)),
            'business_classifications': sum(1 for e in classification_events if e.is_business_income),
            'average_confidence': (
                sum(e.confidence_score for e in classification_events if e.confidence_score) / 
                max(1, len([e for e in classification_events if e.confidence_score]))
            ),
            'cache_hit_rate': (
                sum(1 for e in classification_events if e.cache_hit) / max(1, len(classification_events)) * 100
            )
        }