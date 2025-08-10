"""
Revenue Analytics - Comprehensive revenue analysis and insights
Advanced revenue analytics engine providing deep insights into SI commercial performance,
predictive analytics, cohort analysis, and revenue optimization recommendations.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID
from decimal import Decimal
import statistics
from collections import defaultdict

from core_platform.data_management.billing_repository import BillingRepository, SubscriptionTier
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from .subscription_manager import SubscriptionManager
from .billing_engine import BillingEngine
from .payment_processor import PaymentProcessor
from .usage_tracker import UsageTracker

logger = logging.getLogger(__name__)


class RevenueMetricType(str, Enum):
    """Types of revenue metrics"""
    MRR = "mrr"  # Monthly Recurring Revenue
    ARR = "arr"  # Annual Recurring Revenue
    ARPU = "arpu"  # Average Revenue Per User
    LTV = "ltv"  # Customer Lifetime Value
    CAC = "cac"  # Customer Acquisition Cost
    CHURN_RATE = "churn_rate"
    EXPANSION_REVENUE = "expansion_revenue"
    CONTRACTION_REVENUE = "contraction_revenue"


class RevenueSegment(str, Enum):
    """Revenue segmentation categories"""
    BY_TIER = "by_tier"
    BY_REGION = "by_region"
    BY_COHORT = "by_cohort"
    BY_ACQUISITION_CHANNEL = "by_acquisition_channel"
    BY_ORGANIZATION_SIZE = "by_organization_size"


class ForecastMethod(str, Enum):
    """Revenue forecasting methods"""
    LINEAR_REGRESSION = "linear_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    COHORT_BASED = "cohort_based"


@dataclass
class RevenueMetric:
    """Revenue metric data point"""
    metric_type: RevenueMetricType
    value: Decimal
    period_start: datetime
    period_end: datetime
    segment: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class CohortAnalysis:
    """Customer cohort analysis"""
    cohort_month: str
    customers_acquired: int
    initial_revenue: Decimal
    retention_rates: Dict[int, float]  # month -> retention rate
    revenue_retention: Dict[int, Decimal]  # month -> revenue
    ltv_estimate: Decimal
    payback_period_months: int


@dataclass
class RevenueSegmentAnalysis:
    """Revenue analysis by segment"""
    segment_type: RevenueSegment
    segment_value: str
    total_revenue: Decimal
    customer_count: int
    average_revenue_per_customer: Decimal
    growth_rate: float
    churn_rate: float
    expansion_rate: float


@dataclass
class RevenueForecast:
    """Revenue forecast data"""
    forecast_period: str
    method: ForecastMethod
    predicted_revenue: Decimal
    confidence_interval: Tuple[Decimal, Decimal]
    growth_rate: float
    assumptions: List[str]
    accuracy_score: Optional[float] = None


@dataclass
class RevenueInsight:
    """Revenue optimization insight"""
    insight_id: str
    category: str
    title: str
    description: str
    impact_estimate: Decimal
    confidence_level: float
    recommended_actions: List[str]
    priority: str
    data_points: Dict[str, Any]


class RevenueAnalytics:
    """Comprehensive Revenue Analytics Engine"""
    
    def __init__(self):
        self.billing_repository = BillingRepository()
        self.subscription_manager = SubscriptionManager()
        self.billing_engine = BillingEngine()
        self.payment_processor = PaymentProcessor()
        self.usage_tracker = UsageTracker()
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.logger = logging.getLogger(__name__)
        
        # Analytics data registries
        self.revenue_metrics: Dict[str, RevenueMetric] = {}
        self.cohort_analyses: Dict[str, CohortAnalysis] = {}
        self.segment_analyses: Dict[str, RevenueSegmentAnalysis] = {}
        self.forecasts: Dict[str, RevenueForecast] = {}
        self.insights: Dict[str, RevenueInsight] = {}
        
        # Configuration
        self.config = {
            "mrr_calculation_day": 1,  # Calculate MRR on 1st of each month
            "ltv_calculation_months": 24,  # 24 month LTV calculation
            "forecast_horizon_months": 12,  # 12 month forecast
            "cohort_retention_periods": 12,  # Track retention for 12 months
            "cache_ttl_hours": 6,  # Cache analytics for 6 hours
            "insight_confidence_threshold": 0.7,  # Minimum confidence for insights
            "growth_rate_periods": 3  # Calculate growth over 3 periods
        }
    
    async def calculate_revenue_metrics(
        self,
        tenant_id: Optional[UUID] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive revenue metrics"""
        try:
            # Set default period to current month
            if not period_end:
                period_end = datetime.now(timezone.utc)
            if not period_start:
                period_start = period_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            # Check cache
            cache_key = f"revenue_metrics:{tenant_id}:{period_start.date()}:{period_end.date()}"
            cached_metrics = await self.cache_service.get(cache_key)
            if cached_metrics:
                return cached_metrics
            
            # Calculate MRR (Monthly Recurring Revenue)
            mrr = await self._calculate_mrr(tenant_id, period_start, period_end)
            
            # Calculate ARR (Annual Recurring Revenue)
            arr = mrr * 12
            
            # Calculate ARPU (Average Revenue Per User)
            arpu = await self._calculate_arpu(tenant_id, period_start, period_end)
            
            # Calculate Customer LTV (Lifetime Value)
            ltv = await self._calculate_customer_ltv(tenant_id)
            
            # Calculate Churn Rate
            churn_rate = await self._calculate_churn_rate(tenant_id, period_start, period_end)
            
            # Calculate Expansion/Contraction Revenue
            expansion_revenue = await self._calculate_expansion_revenue(tenant_id, period_start, period_end)
            contraction_revenue = await self._calculate_contraction_revenue(tenant_id, period_start, period_end)
            
            # Net Revenue Retention
            net_revenue_retention = await self._calculate_net_revenue_retention(
                tenant_id, period_start, period_end
            )
            
            # Growth rates
            growth_rates = await self._calculate_growth_rates(tenant_id, period_end)
            
            metrics = {
                "period": {
                    "start": period_start.isoformat(),
                    "end": period_end.isoformat()
                },
                "core_metrics": {
                    "mrr": float(mrr),
                    "arr": float(arr),
                    "arpu": float(arpu),
                    "ltv": float(ltv),
                    "churn_rate": churn_rate,
                    "net_revenue_retention": net_revenue_retention
                },
                "revenue_changes": {
                    "expansion_revenue": float(expansion_revenue),
                    "contraction_revenue": float(contraction_revenue),
                    "net_expansion": float(expansion_revenue - contraction_revenue)
                },
                "growth_rates": growth_rates,
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "calculated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Cache results
            await self.cache_service.set(
                cache_key, metrics, 
                ttl=self.config["cache_ttl_hours"] * 3600
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating revenue metrics: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def perform_cohort_analysis(
        self,
        lookback_months: int = 12,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Perform customer cohort analysis"""
        try:
            cache_key = f"cohort_analysis:{tenant_id}:{lookback_months}"
            cached_analysis = await self.cache_service.get(cache_key)
            if cached_analysis:
                return cached_analysis
            
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=lookback_months * 30)
            
            # Get all subscriptions in the period
            subscriptions = await self._get_subscriptions_in_period(start_date, end_date, tenant_id)
            
            # Group by cohort month
            cohorts = defaultdict(list)
            for subscription in subscriptions:
                cohort_month = subscription["created_at"].strftime("%Y-%m")
                cohorts[cohort_month].append(subscription)
            
            cohort_analyses = []
            
            for cohort_month, cohort_subscriptions in cohorts.items():
                if not cohort_subscriptions:
                    continue
                
                # Calculate cohort metrics
                cohort_analysis = await self._analyze_cohort(
                    cohort_month, cohort_subscriptions, end_date
                )
                cohort_analyses.append(cohort_analysis)
                self.cohort_analyses[cohort_month] = cohort_analysis
            
            # Calculate aggregate metrics
            aggregate_metrics = await self._calculate_aggregate_cohort_metrics(cohort_analyses)
            
            result = {
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "months": lookback_months
                },
                "cohorts": [asdict(c) for c in cohort_analyses],
                "aggregate_metrics": aggregate_metrics,
                "insights": await self._generate_cohort_insights(cohort_analyses),
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Cache results
            await self.cache_service.set(cache_key, result, ttl=self.config["cache_ttl_hours"] * 3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error performing cohort analysis: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def generate_revenue_forecast(
        self,
        forecast_months: int = 12,
        method: ForecastMethod = ForecastMethod.LINEAR_REGRESSION,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Generate revenue forecast"""
        try:
            cache_key = f"revenue_forecast:{tenant_id}:{forecast_months}:{method.value}"
            cached_forecast = await self.cache_service.get(cache_key)
            if cached_forecast:
                return cached_forecast
            
            # Get historical revenue data
            historical_data = await self._get_historical_revenue_data(tenant_id, 24)  # 24 months history
            
            if len(historical_data) < 6:  # Need at least 6 months of data
                return {
                    "status": "error",
                    "message": "Insufficient historical data for forecasting (minimum 6 months required)"
                }
            
            # Generate forecast based on method
            if method == ForecastMethod.LINEAR_REGRESSION:
                forecast = await self._linear_regression_forecast(historical_data, forecast_months)
            elif method == ForecastMethod.EXPONENTIAL_SMOOTHING:
                forecast = await self._exponential_smoothing_forecast(historical_data, forecast_months)
            elif method == ForecastMethod.COHORT_BASED:
                forecast = await self._cohort_based_forecast(historical_data, forecast_months, tenant_id)
            else:
                forecast = await self._linear_regression_forecast(historical_data, forecast_months)  # Default
            
            # Calculate scenario analysis
            scenarios = await self._calculate_forecast_scenarios(forecast, historical_data)
            
            # Generate business insights
            insights = await self._generate_forecast_insights(forecast, historical_data)
            
            result = {
                "forecast_method": method.value,
                "forecast_horizon_months": forecast_months,
                "historical_data_points": len(historical_data),
                "forecast": asdict(forecast),
                "scenarios": scenarios,
                "insights": insights,
                "accuracy_validation": await self._validate_forecast_accuracy(method, historical_data),
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store forecast
            self.forecasts[f"{tenant_id}:{method.value}"] = forecast
            
            # Cache results
            await self.cache_service.set(cache_key, result, ttl=self.config["cache_ttl_hours"] * 3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating revenue forecast: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def analyze_revenue_segments(
        self,
        segment_type: RevenueSegment,
        period_months: int = 12,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Analyze revenue by segments"""
        try:
            cache_key = f"segment_analysis:{segment_type.value}:{tenant_id}:{period_months}"
            cached_analysis = await self.cache_service.get(cache_key)
            if cached_analysis:
                return cached_analysis
            
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=period_months * 30)
            
            # Get segmentation data
            if segment_type == RevenueSegment.BY_TIER:
                segments = await self._analyze_tier_segments(start_date, end_date, tenant_id)
            elif segment_type == RevenueSegment.BY_REGION:
                segments = await self._analyze_region_segments(start_date, end_date, tenant_id)
            elif segment_type == RevenueSegment.BY_COHORT:
                segments = await self._analyze_cohort_segments(start_date, end_date, tenant_id)
            elif segment_type == RevenueSegment.BY_ORGANIZATION_SIZE:
                segments = await self._analyze_organization_size_segments(start_date, end_date, tenant_id)
            else:
                return {"status": "error", "message": f"Unsupported segment type: {segment_type.value}"}
            
            # Calculate segment performance metrics
            segment_performance = await self._calculate_segment_performance(segments)
            
            # Generate segment insights
            segment_insights = await self._generate_segment_insights(segments, segment_type)
            
            result = {
                "segment_type": segment_type.value,
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "months": period_months
                },
                "segments": [asdict(s) for s in segments],
                "performance_summary": segment_performance,
                "insights": segment_insights,
                "recommendations": await self._generate_segment_recommendations(segments, segment_type),
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store segments
            for segment in segments:
                self.segment_analyses[f"{segment_type.value}:{segment.segment_value}"] = segment
            
            # Cache results
            await self.cache_service.set(cache_key, result, ttl=self.config["cache_ttl_hours"] * 3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing revenue segments: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def generate_revenue_insights(
        self,
        tenant_id: Optional[UUID] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate actionable revenue insights"""
        try:
            focus_areas = focus_areas or ["growth", "retention", "optimization", "risk"]
            
            insights = []
            
            # Growth insights
            if "growth" in focus_areas:
                growth_insights = await self._generate_growth_insights(tenant_id)
                insights.extend(growth_insights)
            
            # Retention insights
            if "retention" in focus_areas:
                retention_insights = await self._generate_retention_insights(tenant_id)
                insights.extend(retention_insights)
            
            # Optimization insights
            if "optimization" in focus_areas:
                optimization_insights = await self._generate_optimization_insights(tenant_id)
                insights.extend(optimization_insights)
            
            # Risk insights
            if "risk" in focus_areas:
                risk_insights = await self._generate_risk_insights(tenant_id)
                insights.extend(risk_insights)
            
            # Prioritize insights
            prioritized_insights = await self._prioritize_insights(insights)
            
            # Store insights
            for insight in prioritized_insights:
                self.insights[insight.insight_id] = insight
            
            return {
                "total_insights": len(prioritized_insights),
                "focus_areas": focus_areas,
                "insights": [asdict(i) for i in prioritized_insights],
                "summary": await self._generate_insights_summary(prioritized_insights),
                "action_plan": await self._generate_action_plan(prioritized_insights),
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating revenue insights: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_revenue_dashboard_data(
        self,
        tenant_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get comprehensive revenue dashboard data"""
        try:
            # Calculate current metrics
            current_metrics = await self.calculate_revenue_metrics(tenant_id)
            
            # Get trend data (last 12 months)
            trend_data = await self._get_revenue_trends(tenant_id, 12)
            
            # Get top performing segments
            top_segments = await self._get_top_performing_segments(tenant_id)
            
            # Get recent insights
            recent_insights = await self._get_recent_insights(tenant_id, 5)
            
            # Get forecast summary
            forecast_summary = await self._get_forecast_summary(tenant_id)
            
            # Calculate health score
            health_score = await self._calculate_revenue_health_score(tenant_id)
            
            return {
                "current_metrics": current_metrics,
                "trends": trend_data,
                "top_segments": top_segments,
                "recent_insights": recent_insights,
                "forecast_summary": forecast_summary,
                "health_score": health_score,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # Private helper methods
    
    async def _calculate_mrr(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> Decimal:
        """Calculate Monthly Recurring Revenue"""
        try:
            # Get all active subscriptions
            if tenant_id:
                subscriptions = [await self.billing_repository.get_subscription(tenant_id)]
                subscriptions = [s for s in subscriptions if s]
            else:
                # Would need to implement get_all_active_subscriptions in billing_repository
                subscriptions = []
            
            mrr = Decimal("0")
            for subscription in subscriptions:
                if subscription and subscription.get("status") == "active":
                    monthly_price = Decimal(str(subscription.get("monthly_price", 0)))
                    mrr += monthly_price
            
            return mrr
            
        except Exception as e:
            self.logger.error(f"Error calculating MRR: {str(e)}")
            return Decimal("0")
    
    async def _calculate_arpu(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> Decimal:
        """Calculate Average Revenue Per User"""
        try:
            # Get revenue and user count for period
            total_revenue = await self._get_total_revenue(tenant_id, period_start, period_end)
            user_count = await self._get_active_user_count(tenant_id, period_start, period_end)
            
            if user_count > 0:
                return total_revenue / Decimal(str(user_count))
            return Decimal("0")
            
        except Exception as e:
            self.logger.error(f"Error calculating ARPU: {str(e)}")
            return Decimal("0")
    
    async def _calculate_customer_ltv(self, tenant_id: Optional[UUID]) -> Decimal:
        """Calculate Customer Lifetime Value"""
        try:
            # Simple LTV calculation: ARPU / Churn Rate
            current_date = datetime.now(timezone.utc)
            period_start = current_date.replace(day=1)
            
            arpu = await self._calculate_arpu(tenant_id, period_start, current_date)
            churn_rate = await self._calculate_churn_rate(tenant_id, period_start, current_date)
            
            if churn_rate > 0:
                ltv = arpu / Decimal(str(churn_rate))
            else:
                ltv = arpu * 24  # Assume 24 month retention if no churn
            
            return ltv
            
        except Exception as e:
            self.logger.error(f"Error calculating LTV: {str(e)}")
            return Decimal("0")
    
    async def _calculate_churn_rate(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> float:
        """Calculate customer churn rate"""
        try:
            # This would need integration with subscription events
            # For now, return a placeholder based on industry averages
            return 0.05  # 5% monthly churn rate
            
        except Exception as e:
            self.logger.error(f"Error calculating churn rate: {str(e)}")
            return 0.0
    
    async def _calculate_expansion_revenue(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> Decimal:
        """Calculate expansion revenue from upgrades"""
        try:
            # This would track subscription tier upgrades
            # For now, return placeholder
            return Decimal("0")
            
        except Exception as e:
            self.logger.error(f"Error calculating expansion revenue: {str(e)}")
            return Decimal("0")
    
    async def _calculate_contraction_revenue(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> Decimal:
        """Calculate contraction revenue from downgrades"""
        try:
            # This would track subscription tier downgrades
            # For now, return placeholder
            return Decimal("0")
            
        except Exception as e:
            self.logger.error(f"Error calculating contraction revenue: {str(e)}")
            return Decimal("0")
    
    async def _calculate_net_revenue_retention(
        self, 
        tenant_id: Optional[UUID], 
        period_start: datetime, 
        period_end: datetime
    ) -> float:
        """Calculate Net Revenue Retention"""
        try:
            # NRR = (Starting MRR + Expansion - Contraction - Churn) / Starting MRR
            starting_mrr = await self._calculate_mrr(tenant_id, period_start, period_start)
            expansion = await self._calculate_expansion_revenue(tenant_id, period_start, period_end)
            contraction = await self._calculate_contraction_revenue(tenant_id, period_start, period_end)
            # Churn would be calculated from cancelled subscriptions
            
            if starting_mrr > 0:
                nrr = float((starting_mrr + expansion - contraction) / starting_mrr)
                return nrr
            return 1.0
            
        except Exception as e:
            self.logger.error(f"Error calculating NRR: {str(e)}")
            return 1.0
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for revenue analytics"""
        try:
            return {
                "status": "healthy",
                "service": "revenue_analytics",
                "revenue_metrics": len(self.revenue_metrics),
                "cohort_analyses": len(self.cohort_analyses),
                "forecasts": len(self.forecasts),
                "insights": len(self.insights),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "revenue_analytics",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_revenue_analytics() -> RevenueAnalytics:
    """Create revenue analytics instance"""
    return RevenueAnalytics()