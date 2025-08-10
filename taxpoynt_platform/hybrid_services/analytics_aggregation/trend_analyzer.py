"""
Hybrid Service: Trend Analyzer
Analyzes trends across SI and APP roles for predictive insights
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics
import math
import numpy as np
from scipy import stats

from core_platform.database import get_db_session
from core_platform.models.trends import TrendAnalysis, TrendPattern, TrendPrediction, TrendAlert
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

from .unified_metrics import UnifiedMetrics, MetricScope, MetricType, AggregatedMetric
from .kpi_calculator import KPICalculator, KPICalculation

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Trend direction"""
    UPWARD = "upward"
    DOWNWARD = "downward"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"


class TrendStrength(str, Enum):
    """Trend strength"""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    VERY_WEAK = "very_weak"


class TrendType(str, Enum):
    """Types of trends"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    POLYNOMIAL = "polynomial"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"
    IRREGULAR = "irregular"


class TrendSignificance(str, Enum):
    """Trend significance levels"""
    HIGHLY_SIGNIFICANT = "highly_significant"
    SIGNIFICANT = "significant"
    MODERATELY_SIGNIFICANT = "moderately_significant"
    NOT_SIGNIFICANT = "not_significant"


class PredictionConfidence(str, Enum):
    """Prediction confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


@dataclass
class TrendDataPoint:
    """Individual trend data point"""
    timestamp: datetime
    value: float
    metric_id: str
    source_role: str
    dimensions: Dict[str, str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendPattern:
    """Detected trend pattern"""
    pattern_id: str
    pattern_type: TrendType
    direction: TrendDirection
    strength: TrendStrength
    significance: TrendSignificance
    start_time: datetime
    end_time: datetime
    duration: timedelta
    slope: float
    r_squared: float
    confidence_interval: Tuple[float, float]
    seasonal_components: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis"""
    analysis_id: str
    metric_id: str
    analysis_period: Tuple[datetime, datetime]
    data_points: List[TrendDataPoint]
    detected_patterns: List[TrendPattern]
    primary_trend: Optional[TrendPattern]
    anomalies: List[Dict[str, Any]]
    seasonality: Dict[str, Any]
    forecast_accuracy: float
    analysis_time: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendPrediction:
    """Trend prediction result"""
    prediction_id: str
    metric_id: str
    prediction_time: datetime
    prediction_horizon: timedelta
    predicted_values: List[Dict[str, Any]]
    confidence: PredictionConfidence
    prediction_interval: Tuple[float, float]
    model_type: str
    model_accuracy: float
    assumptions: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendAlert:
    """Trend-based alert"""
    alert_id: str
    metric_id: str
    alert_type: str
    severity: str
    title: str
    description: str
    triggered_time: datetime
    threshold_value: float
    current_value: float
    trend_data: Dict[str, Any]
    recommendations: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendComparison:
    """Comparison of trends across metrics or time periods"""
    comparison_id: str
    comparison_type: str
    metrics: List[str]
    time_periods: List[Tuple[datetime, datetime]]
    trend_correlations: Dict[str, float]
    similarity_scores: Dict[str, float]
    divergence_points: List[Dict[str, Any]]
    insights: List[str]
    comparison_time: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TrendAnalyzer:
    """
    Trend Analyzer service
    Analyzes trends across SI and APP roles for predictive insights
    """
    
    def __init__(self, unified_metrics: UnifiedMetrics = None, kpi_calculator: KPICalculator = None):
        """Initialize trend analyzer service"""
        self.unified_metrics = unified_metrics or UnifiedMetrics()
        self.kpi_calculator = kpi_calculator or KPICalculator()
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.trend_analyses: Dict[str, TrendAnalysis] = {}
        self.trend_predictions: Dict[str, TrendPrediction] = {}
        self.trend_alerts: Dict[str, TrendAlert] = {}
        self.trend_models: Dict[str, Any] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 1800  # 30 minutes
        self.min_data_points = 10
        self.max_prediction_horizon = 30  # days
        self.significance_threshold = 0.05
        self.analysis_interval = 3600  # 1 hour
        
        # Statistical thresholds
        self.correlation_threshold = 0.7
        self.r_squared_threshold = 0.5
        self.volatility_threshold = 0.2
    
    async def initialize(self):
        """Initialize the trend analyzer service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing trend analyzer service")
        
        try:
            # Initialize dependencies
            await self.unified_metrics.initialize()
            await self.kpi_calculator.initialize()
            await self.cache.initialize()
            
            # Start periodic analysis
            asyncio.create_task(self._periodic_analysis())
            
            # Register event handlers
            await self._register_event_handlers()
            
            self.is_initialized = True
            self.logger.info("Trend analyzer service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing trend analyzer service: {str(e)}")
            raise
    
    async def analyze_metric_trend(
        self,
        metric_id: str,
        time_range: Tuple[datetime, datetime],
        granularity: str = "hour"
    ) -> TrendAnalysis:
        """Analyze trend for a specific metric"""
        try:
            # Get metric data
            metric_trends = await self.unified_metrics.get_metric_trends(
                metric_id,
                time_range,
                granularity
            )
            
            if len(metric_trends) < self.min_data_points:
                raise ValueError(f"Insufficient data points for trend analysis: {len(metric_trends)}")
            
            # Convert to trend data points
            data_points = []
            for metric in metric_trends:
                data_point = TrendDataPoint(
                    timestamp=metric.timestamp,
                    value=metric.aggregated_value,
                    metric_id=metric_id,
                    source_role="unified",
                    dimensions=metric.dimensions,
                    metadata={"aggregation_method": metric.aggregation_method}
                )
                data_points.append(data_point)
            
            # Detect patterns
            detected_patterns = await self._detect_patterns(data_points)
            
            # Find primary trend
            primary_trend = self._find_primary_trend(detected_patterns)
            
            # Detect anomalies
            anomalies = await self._detect_anomalies(data_points, primary_trend)
            
            # Analyze seasonality
            seasonality = await self._analyze_seasonality(data_points)
            
            # Calculate forecast accuracy
            forecast_accuracy = await self._calculate_forecast_accuracy(data_points, primary_trend)
            
            # Create trend analysis
            trend_analysis = TrendAnalysis(
                analysis_id=str(uuid.uuid4()),
                metric_id=metric_id,
                analysis_period=time_range,
                data_points=data_points,
                detected_patterns=detected_patterns,
                primary_trend=primary_trend,
                anomalies=anomalies,
                seasonality=seasonality,
                forecast_accuracy=forecast_accuracy,
                analysis_time=datetime.now(timezone.utc),
                metadata={
                    "granularity": granularity,
                    "data_points_count": len(data_points),
                    "patterns_detected": len(detected_patterns)
                }
            )
            
            # Store analysis
            self.trend_analyses[trend_analysis.analysis_id] = trend_analysis
            
            # Cache results
            await self.cache.set(
                f"trend_analysis:{metric_id}",
                trend_analysis.to_dict(),
                ttl=self.cache_ttl
            )
            
            # Check for alerts
            await self._check_trend_alerts(trend_analysis)
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing metric trend: {str(e)}")
            raise
    
    async def predict_metric_trend(
        self,
        metric_id: str,
        historical_range: Tuple[datetime, datetime],
        prediction_horizon: int = 7,  # days
        model_type: str = "linear"
    ) -> TrendPrediction:
        """Predict future trend for a metric"""
        try:
            # Get historical trend analysis
            trend_analysis = await self.analyze_metric_trend(
                metric_id,
                historical_range,
                "hour"
            )
            
            if not trend_analysis.primary_trend:
                raise ValueError("No primary trend found for prediction")
            
            # Prepare data for prediction
            x_values = []
            y_values = []
            
            for i, data_point in enumerate(trend_analysis.data_points):
                x_values.append(i)
                y_values.append(data_point.value)
            
            # Create prediction model
            model = await self._create_prediction_model(
                x_values,
                y_values,
                model_type,
                trend_analysis.primary_trend
            )
            
            # Generate predictions
            prediction_start = len(x_values)
            prediction_end = prediction_start + (prediction_horizon * 24)  # hourly predictions
            
            predicted_values = []
            for i in range(prediction_start, prediction_end):
                predicted_value = await self._apply_prediction_model(model, i, model_type)
                
                prediction_time = historical_range[1] + timedelta(hours=(i - prediction_start))
                
                predicted_values.append({
                    "timestamp": prediction_time.isoformat(),
                    "predicted_value": predicted_value,
                    "confidence_lower": predicted_value * 0.9,  # Simple confidence interval
                    "confidence_upper": predicted_value * 1.1
                })
            
            # Calculate prediction confidence
            confidence = await self._calculate_prediction_confidence(
                trend_analysis,
                model,
                model_type
            )
            
            # Create prediction
            prediction = TrendPrediction(
                prediction_id=str(uuid.uuid4()),
                metric_id=metric_id,
                prediction_time=datetime.now(timezone.utc),
                prediction_horizon=timedelta(days=prediction_horizon),
                predicted_values=predicted_values,
                confidence=confidence,
                prediction_interval=(
                    min(pv["predicted_value"] for pv in predicted_values),
                    max(pv["predicted_value"] for pv in predicted_values)
                ),
                model_type=model_type,
                model_accuracy=trend_analysis.forecast_accuracy,
                assumptions=[
                    "Historical patterns continue",
                    "No external disruptions",
                    "Seasonal patterns persist"
                ],
                metadata={
                    "historical_range": {
                        "start": historical_range[0].isoformat(),
                        "end": historical_range[1].isoformat()
                    },
                    "prediction_points": len(predicted_values),
                    "primary_trend_strength": trend_analysis.primary_trend.strength if trend_analysis.primary_trend else "unknown"
                }
            )
            
            # Store prediction
            self.trend_predictions[prediction.prediction_id] = prediction
            
            # Cache results
            await self.cache.set(
                f"trend_prediction:{metric_id}",
                prediction.to_dict(),
                ttl=self.cache_ttl
            )
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error predicting metric trend: {str(e)}")
            raise
    
    async def compare_trends(
        self,
        metric_ids: List[str],
        time_range: Tuple[datetime, datetime],
        comparison_type: str = "correlation"
    ) -> TrendComparison:
        """Compare trends across multiple metrics"""
        try:
            # Get trend analyses for all metrics
            trend_analyses = {}
            for metric_id in metric_ids:
                try:
                    analysis = await self.analyze_metric_trend(metric_id, time_range)
                    trend_analyses[metric_id] = analysis
                except Exception as e:
                    self.logger.warning(f"Failed to analyze trend for {metric_id}: {str(e)}")
                    continue
            
            if len(trend_analyses) < 2:
                raise ValueError("Need at least 2 metrics for comparison")
            
            # Calculate correlations
            trend_correlations = {}
            for metric1 in metric_ids:
                for metric2 in metric_ids:
                    if metric1 != metric2 and metric1 in trend_analyses and metric2 in trend_analyses:
                        correlation = await self._calculate_trend_correlation(
                            trend_analyses[metric1],
                            trend_analyses[metric2]
                        )
                        trend_correlations[f"{metric1}_{metric2}"] = correlation
            
            # Calculate similarity scores
            similarity_scores = {}
            for metric1 in metric_ids:
                for metric2 in metric_ids:
                    if metric1 != metric2 and metric1 in trend_analyses and metric2 in trend_analyses:
                        similarity = await self._calculate_trend_similarity(
                            trend_analyses[metric1],
                            trend_analyses[metric2]
                        )
                        similarity_scores[f"{metric1}_{metric2}"] = similarity
            
            # Find divergence points
            divergence_points = await self._find_divergence_points(trend_analyses)
            
            # Generate insights
            insights = await self._generate_comparison_insights(
                trend_analyses,
                trend_correlations,
                similarity_scores,
                divergence_points
            )
            
            # Create comparison
            comparison = TrendComparison(
                comparison_id=str(uuid.uuid4()),
                comparison_type=comparison_type,
                metrics=metric_ids,
                time_periods=[time_range],
                trend_correlations=trend_correlations,
                similarity_scores=similarity_scores,
                divergence_points=divergence_points,
                insights=insights,
                comparison_time=datetime.now(timezone.utc),
                metadata={
                    "metrics_analyzed": len(trend_analyses),
                    "correlations_calculated": len(trend_correlations),
                    "time_range": {
                        "start": time_range[0].isoformat(),
                        "end": time_range[1].isoformat()
                    }
                }
            )
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"Error comparing trends: {str(e)}")
            raise
    
    async def detect_trend_anomalies(
        self,
        metric_id: str,
        time_range: Tuple[datetime, datetime],
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in trend data"""
        try:
            # Get trend analysis
            trend_analysis = await self.analyze_metric_trend(metric_id, time_range)
            
            # Use existing anomaly detection
            anomalies = trend_analysis.anomalies
            
            # Additional statistical anomaly detection
            values = [dp.value for dp in trend_analysis.data_points]
            
            if len(values) < 3:
                return anomalies
            
            # Calculate statistical thresholds
            mean_value = statistics.mean(values)
            std_value = statistics.stdev(values)
            
            lower_threshold = mean_value - (sensitivity * std_value)
            upper_threshold = mean_value + (sensitivity * std_value)
            
            # Find statistical anomalies
            for i, data_point in enumerate(trend_analysis.data_points):
                if data_point.value < lower_threshold or data_point.value > upper_threshold:
                    anomaly = {
                        "anomaly_id": str(uuid.uuid4()),
                        "timestamp": data_point.timestamp.isoformat(),
                        "value": data_point.value,
                        "expected_range": (lower_threshold, upper_threshold),
                        "anomaly_type": "statistical",
                        "severity": "high" if abs(data_point.value - mean_value) > 3 * std_value else "medium",
                        "deviation": abs(data_point.value - mean_value) / std_value
                    }
                    
                    # Check if not already in anomalies
                    if not any(a.get("timestamp") == anomaly["timestamp"] for a in anomalies):
                        anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting trend anomalies: {str(e)}")
            return []
    
    async def get_trend_insights(
        self,
        metric_id: str,
        time_range: Tuple[datetime, datetime]
    ) -> List[Dict[str, Any]]:
        """Get insights from trend analysis"""
        try:
            # Get trend analysis
            trend_analysis = await self.analyze_metric_trend(metric_id, time_range)
            
            insights = []
            
            # Primary trend insight
            if trend_analysis.primary_trend:
                primary_trend = trend_analysis.primary_trend
                
                insight = {
                    "insight_id": str(uuid.uuid4()),
                    "type": "primary_trend",
                    "title": f"Primary Trend: {primary_trend.direction.title()}",
                    "description": f"Metric shows {primary_trend.strength} {primary_trend.direction} trend",
                    "significance": primary_trend.significance,
                    "confidence": primary_trend.r_squared,
                    "recommendation": await self._generate_trend_recommendation(primary_trend)
                }
                insights.append(insight)
            
            # Seasonality insight
            if trend_analysis.seasonality.get("has_seasonality"):
                insight = {
                    "insight_id": str(uuid.uuid4()),
                    "type": "seasonality",
                    "title": "Seasonal Pattern Detected",
                    "description": f"Metric shows seasonal patterns with period {trend_analysis.seasonality.get('period', 'unknown')}",
                    "significance": "significant" if trend_analysis.seasonality.get("strength", 0) > 0.3 else "moderate",
                    "confidence": trend_analysis.seasonality.get("strength", 0),
                    "recommendation": "Consider seasonal adjustments in planning and forecasting"
                }
                insights.append(insight)
            
            # Anomaly insight
            if trend_analysis.anomalies:
                anomaly_count = len(trend_analysis.anomalies)
                insight = {
                    "insight_id": str(uuid.uuid4()),
                    "type": "anomalies",
                    "title": f"Anomalies Detected: {anomaly_count}",
                    "description": f"Found {anomaly_count} anomalous data points",
                    "significance": "high" if anomaly_count > 5 else "moderate",
                    "confidence": 0.8,
                    "recommendation": "Investigate root causes of anomalous behavior"
                }
                insights.append(insight)
            
            # Volatility insight
            values = [dp.value for dp in trend_analysis.data_points]
            if len(values) > 1:
                coefficient_of_variation = statistics.stdev(values) / statistics.mean(values)
                
                if coefficient_of_variation > self.volatility_threshold:
                    insight = {
                        "insight_id": str(uuid.uuid4()),
                        "type": "volatility",
                        "title": "High Volatility Detected",
                        "description": f"Metric shows high volatility (CV: {coefficient_of_variation:.2f})",
                        "significance": "high" if coefficient_of_variation > 0.5 else "moderate",
                        "confidence": 0.9,
                        "recommendation": "Consider implementing smoothing or stabilization measures"
                    }
                    insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting trend insights: {str(e)}")
            return []
    
    async def _detect_patterns(self, data_points: List[TrendDataPoint]) -> List[TrendPattern]:
        """Detect patterns in trend data"""
        try:
            patterns = []
            
            if len(data_points) < self.min_data_points:
                return patterns
            
            # Extract values and timestamps
            values = [dp.value for dp in data_points]
            timestamps = [dp.timestamp for dp in data_points]
            
            # Convert timestamps to numeric (hours since start)
            start_time = timestamps[0]
            x_values = [(ts - start_time).total_seconds() / 3600 for ts in timestamps]
            
            # Linear trend detection
            linear_pattern = await self._detect_linear_pattern(x_values, values, timestamps)
            if linear_pattern:
                patterns.append(linear_pattern)
            
            # Exponential trend detection
            exponential_pattern = await self._detect_exponential_pattern(x_values, values, timestamps)
            if exponential_pattern:
                patterns.append(exponential_pattern)
            
            # Seasonal pattern detection
            seasonal_pattern = await self._detect_seasonal_pattern(x_values, values, timestamps)
            if seasonal_pattern:
                patterns.append(seasonal_pattern)
            
            # Cyclical pattern detection
            cyclical_pattern = await self._detect_cyclical_pattern(x_values, values, timestamps)
            if cyclical_pattern:
                patterns.append(cyclical_pattern)
            
            return patterns
            
        except Exception as e:
            self.logger.error(f"Error detecting patterns: {str(e)}")
            return []
    
    async def _detect_linear_pattern(
        self,
        x_values: List[float],
        y_values: List[float],
        timestamps: List[datetime]
    ) -> Optional[TrendPattern]:
        """Detect linear trend pattern"""
        try:
            if len(x_values) < 3:
                return None
            
            # Calculate linear regression
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
            
            # Check significance
            if p_value > self.significance_threshold:
                return None
            
            # Determine direction
            if slope > 0.01:
                direction = TrendDirection.UPWARD
            elif slope < -0.01:
                direction = TrendDirection.DOWNWARD
            else:
                direction = TrendDirection.STABLE
            
            # Determine strength based on R-squared
            r_squared = r_value ** 2
            if r_squared >= 0.8:
                strength = TrendStrength.VERY_STRONG
            elif r_squared >= 0.6:
                strength = TrendStrength.STRONG
            elif r_squared >= 0.4:
                strength = TrendStrength.MODERATE
            elif r_squared >= 0.2:
                strength = TrendStrength.WEAK
            else:
                strength = TrendStrength.VERY_WEAK
            
            # Determine significance
            if p_value < 0.01:
                significance = TrendSignificance.HIGHLY_SIGNIFICANT
            elif p_value < 0.05:
                significance = TrendSignificance.SIGNIFICANT
            elif p_value < 0.1:
                significance = TrendSignificance.MODERATELY_SIGNIFICANT
            else:
                significance = TrendSignificance.NOT_SIGNIFICANT
            
            # Calculate confidence interval
            confidence_interval = (
                intercept - 1.96 * std_err,
                intercept + 1.96 * std_err
            )
            
            return TrendPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=TrendType.LINEAR,
                direction=direction,
                strength=strength,
                significance=significance,
                start_time=timestamps[0],
                end_time=timestamps[-1],
                duration=timestamps[-1] - timestamps[0],
                slope=slope,
                r_squared=r_squared,
                confidence_interval=confidence_interval,
                seasonal_components={},
                metadata={
                    "intercept": intercept,
                    "p_value": p_value,
                    "std_err": std_err,
                    "data_points": len(x_values)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting linear pattern: {str(e)}")
            return None
    
    async def _detect_exponential_pattern(
        self,
        x_values: List[float],
        y_values: List[float],
        timestamps: List[datetime]
    ) -> Optional[TrendPattern]:
        """Detect exponential trend pattern"""
        try:
            if len(x_values) < 3:
                return None
            
            # Transform to log space for exponential detection
            log_y_values = []
            for y in y_values:
                if y > 0:
                    log_y_values.append(math.log(y))
                else:
                    log_y_values.append(0)
            
            # Linear regression in log space
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, log_y_values)
            
            # Check significance and exponential nature
            if p_value > self.significance_threshold or abs(slope) < 0.01:
                return None
            
            r_squared = r_value ** 2
            if r_squared < 0.3:  # Higher threshold for exponential
                return None
            
            # Determine direction
            if slope > 0:
                direction = TrendDirection.UPWARD
            else:
                direction = TrendDirection.DOWNWARD
            
            # Determine strength
            if r_squared >= 0.8:
                strength = TrendStrength.VERY_STRONG
            elif r_squared >= 0.6:
                strength = TrendStrength.STRONG
            else:
                strength = TrendStrength.MODERATE
            
            return TrendPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=TrendType.EXPONENTIAL,
                direction=direction,
                strength=strength,
                significance=TrendSignificance.SIGNIFICANT,
                start_time=timestamps[0],
                end_time=timestamps[-1],
                duration=timestamps[-1] - timestamps[0],
                slope=slope,
                r_squared=r_squared,
                confidence_interval=(intercept - 1.96 * std_err, intercept + 1.96 * std_err),
                seasonal_components={},
                metadata={
                    "exponential_base": math.exp(intercept),
                    "growth_rate": slope,
                    "p_value": p_value
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting exponential pattern: {str(e)}")
            return None
    
    async def _detect_seasonal_pattern(
        self,
        x_values: List[float],
        y_values: List[float],
        timestamps: List[datetime]
    ) -> Optional[TrendPattern]:
        """Detect seasonal trend pattern"""
        try:
            if len(x_values) < 24:  # Need at least 24 data points for seasonality
                return None
            
            # Simple seasonal detection using autocorrelation
            # This is a simplified approach - in production, use more sophisticated methods
            
            # Calculate autocorrelation for different lags
            max_lag = min(len(y_values) // 2, 24)
            autocorrelations = []
            
            for lag in range(1, max_lag + 1):
                if len(y_values) > lag:
                    corr = np.corrcoef(y_values[:-lag], y_values[lag:])[0, 1]
                    if not np.isnan(corr):
                        autocorrelations.append((lag, corr))
            
            # Find strongest autocorrelation
            if not autocorrelations:
                return None
            
            strongest_lag, strongest_corr = max(autocorrelations, key=lambda x: abs(x[1]))
            
            # Check if correlation is significant
            if abs(strongest_corr) < 0.3:
                return None
            
            # Determine seasonal characteristics
            period = strongest_lag
            seasonal_strength = abs(strongest_corr)
            
            return TrendPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=TrendType.SEASONAL,
                direction=TrendDirection.SEASONAL,
                strength=TrendStrength.MODERATE if seasonal_strength > 0.5 else TrendStrength.WEAK,
                significance=TrendSignificance.SIGNIFICANT if seasonal_strength > 0.5 else TrendSignificance.MODERATELY_SIGNIFICANT,
                start_time=timestamps[0],
                end_time=timestamps[-1],
                duration=timestamps[-1] - timestamps[0],
                slope=0,
                r_squared=seasonal_strength,
                confidence_interval=(0, 0),
                seasonal_components={
                    "period": period,
                    "strength": seasonal_strength,
                    "autocorrelation": strongest_corr
                },
                metadata={
                    "detected_period": period,
                    "seasonal_strength": seasonal_strength,
                    "autocorrelations": autocorrelations[:5]  # Top 5
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting seasonal pattern: {str(e)}")
            return None
    
    async def _detect_cyclical_pattern(
        self,
        x_values: List[float],
        y_values: List[float],
        timestamps: List[datetime]
    ) -> Optional[TrendPattern]:
        """Detect cyclical trend pattern"""
        try:
            if len(x_values) < 20:
                return None
            
            # Simple cyclical detection using local maxima and minima
            local_maxima = []
            local_minima = []
            
            for i in range(1, len(y_values) - 1):
                if y_values[i] > y_values[i-1] and y_values[i] > y_values[i+1]:
                    local_maxima.append(i)
                elif y_values[i] < y_values[i-1] and y_values[i] < y_values[i+1]:
                    local_minima.append(i)
            
            # Need at least 2 cycles
            if len(local_maxima) < 2 or len(local_minima) < 2:
                return None
            
            # Calculate average cycle length
            if len(local_maxima) > 1:
                max_intervals = [local_maxima[i+1] - local_maxima[i] for i in range(len(local_maxima)-1)]
                avg_cycle_length = statistics.mean(max_intervals)
            else:
                return None
            
            # Check for regularity
            if len(max_intervals) > 1:
                cycle_regularity = 1 - (statistics.stdev(max_intervals) / statistics.mean(max_intervals))
            else:
                cycle_regularity = 0
            
            if cycle_regularity < 0.3:
                return None
            
            return TrendPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type=TrendType.CYCLICAL,
                direction=TrendDirection.CYCLICAL,
                strength=TrendStrength.MODERATE if cycle_regularity > 0.6 else TrendStrength.WEAK,
                significance=TrendSignificance.SIGNIFICANT if cycle_regularity > 0.6 else TrendSignificance.MODERATELY_SIGNIFICANT,
                start_time=timestamps[0],
                end_time=timestamps[-1],
                duration=timestamps[-1] - timestamps[0],
                slope=0,
                r_squared=cycle_regularity,
                confidence_interval=(0, 0),
                seasonal_components={
                    "cycle_length": avg_cycle_length,
                    "regularity": cycle_regularity,
                    "maxima_count": len(local_maxima),
                    "minima_count": len(local_minima)
                },
                metadata={
                    "local_maxima": local_maxima,
                    "local_minima": local_minima,
                    "cycle_intervals": max_intervals
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error detecting cyclical pattern: {str(e)}")
            return None
    
    def _find_primary_trend(self, patterns: List[TrendPattern]) -> Optional[TrendPattern]:
        """Find the primary trend from detected patterns"""
        try:
            if not patterns:
                return None
            
            # Score patterns based on significance and strength
            scored_patterns = []
            
            for pattern in patterns:
                score = 0
                
                # Significance score
                if pattern.significance == TrendSignificance.HIGHLY_SIGNIFICANT:
                    score += 4
                elif pattern.significance == TrendSignificance.SIGNIFICANT:
                    score += 3
                elif pattern.significance == TrendSignificance.MODERATELY_SIGNIFICANT:
                    score += 2
                
                # Strength score
                if pattern.strength == TrendStrength.VERY_STRONG:
                    score += 4
                elif pattern.strength == TrendStrength.STRONG:
                    score += 3
                elif pattern.strength == TrendStrength.MODERATE:
                    score += 2
                
                # R-squared score
                score += pattern.r_squared * 2
                
                # Prefer linear trends for primary trend
                if pattern.pattern_type == TrendType.LINEAR:
                    score += 1
                
                scored_patterns.append((pattern, score))
            
            # Return highest scored pattern
            return max(scored_patterns, key=lambda x: x[1])[0]
            
        except Exception as e:
            self.logger.error(f"Error finding primary trend: {str(e)}")
            return None
    
    async def _detect_anomalies(
        self,
        data_points: List[TrendDataPoint],
        primary_trend: Optional[TrendPattern]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in trend data"""
        try:
            anomalies = []
            
            if not data_points or len(data_points) < 3:
                return anomalies
            
            values = [dp.value for dp in data_points]
            
            # Statistical anomaly detection
            mean_value = statistics.mean(values)
            std_value = statistics.stdev(values) if len(values) > 1 else 0
            
            # Z-score based anomaly detection
            for i, data_point in enumerate(data_points):
                if std_value > 0:
                    z_score = abs(data_point.value - mean_value) / std_value
                    
                    if z_score > 2.5:  # Anomaly threshold
                        anomaly = {
                            "anomaly_id": str(uuid.uuid4()),
                            "timestamp": data_point.timestamp.isoformat(),
                            "value": data_point.value,
                            "z_score": z_score,
                            "anomaly_type": "statistical",
                            "severity": "high" if z_score > 3 else "medium",
                            "expected_value": mean_value,
                            "deviation": abs(data_point.value - mean_value)
                        }
                        anomalies.append(anomaly)
            
            # Trend-based anomaly detection
            if primary_trend and primary_trend.pattern_type == TrendType.LINEAR:
                slope = primary_trend.slope
                
                # Calculate expected values based on trend
                start_time = data_points[0].timestamp
                
                for i, data_point in enumerate(data_points):
                    hours_from_start = (data_point.timestamp - start_time).total_seconds() / 3600
                    expected_value = values[0] + (slope * hours_from_start)
                    
                    deviation = abs(data_point.value - expected_value)
                    threshold = std_value * 2  # Threshold for trend-based anomaly
                    
                    if deviation > threshold and std_value > 0:
                        anomaly = {
                            "anomaly_id": str(uuid.uuid4()),
                            "timestamp": data_point.timestamp.isoformat(),
                            "value": data_point.value,
                            "expected_value": expected_value,
                            "deviation": deviation,
                            "anomaly_type": "trend_based",
                            "severity": "high" if deviation > threshold * 1.5 else "medium"
                        }
                        
                        # Check if not duplicate
                        if not any(a.get("timestamp") == anomaly["timestamp"] for a in anomalies):
                            anomalies.append(anomaly)
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"Error detecting anomalies: {str(e)}")
            return []
    
    async def _analyze_seasonality(self, data_points: List[TrendDataPoint]) -> Dict[str, Any]:
        """Analyze seasonality in trend data"""
        try:
            if len(data_points) < 24:
                return {"has_seasonality": False, "reason": "insufficient_data"}
            
            values = [dp.value for dp in data_points]
            
            # Simple seasonality detection using hour of day
            hourly_averages = {}
            hourly_counts = {}
            
            for dp in data_points:
                hour = dp.timestamp.hour
                if hour not in hourly_averages:
                    hourly_averages[hour] = 0
                    hourly_counts[hour] = 0
                
                hourly_averages[hour] += dp.value
                hourly_counts[hour] += 1
            
            # Calculate average for each hour
            for hour in hourly_averages:
                if hourly_counts[hour] > 0:
                    hourly_averages[hour] /= hourly_counts[hour]
            
            # Check for significant hourly variation
            if len(hourly_averages) < 2:
                return {"has_seasonality": False, "reason": "insufficient_hourly_data"}
            
            hour_values = list(hourly_averages.values())
            overall_mean = statistics.mean(hour_values)
            hour_std = statistics.stdev(hour_values) if len(hour_values) > 1 else 0
            
            # Seasonality strength
            seasonality_strength = hour_std / overall_mean if overall_mean > 0 else 0
            
            # Day of week seasonality
            daily_averages = {}
            daily_counts = {}
            
            for dp in data_points:
                day = dp.timestamp.weekday()
                if day not in daily_averages:
                    daily_averages[day] = 0
                    daily_counts[day] = 0
                
                daily_averages[day] += dp.value
                daily_counts[day] += 1
            
            # Calculate average for each day
            for day in daily_averages:
                if daily_counts[day] > 0:
                    daily_averages[day] /= daily_counts[day]
            
            return {
                "has_seasonality": seasonality_strength > 0.1,
                "strength": seasonality_strength,
                "hourly_pattern": hourly_averages,
                "daily_pattern": daily_averages,
                "period": "daily" if seasonality_strength > 0.1 else "none",
                "analysis_type": "simple_statistical"
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing seasonality: {str(e)}")
            return {"has_seasonality": False, "error": str(e)}
    
    async def _calculate_forecast_accuracy(
        self,
        data_points: List[TrendDataPoint],
        primary_trend: Optional[TrendPattern]
    ) -> float:
        """Calculate forecast accuracy of the primary trend"""
        try:
            if not primary_trend or len(data_points) < 10:
                return 0.0
            
            # Use the last 20% of data for accuracy testing
            test_size = max(2, len(data_points) // 5)
            train_data = data_points[:-test_size]
            test_data = data_points[-test_size:]
            
            # Calculate predictions for test data
            train_values = [dp.value for dp in train_data]
            test_values = [dp.value for dp in test_data]
            
            if primary_trend.pattern_type == TrendType.LINEAR:
                # Linear prediction
                slope = primary_trend.slope
                start_time = train_data[0].timestamp
                
                predictions = []
                for dp in test_data:
                    hours_from_start = (dp.timestamp - start_time).total_seconds() / 3600
                    predicted_value = train_values[0] + (slope * hours_from_start)
                    predictions.append(predicted_value)
                
                # Calculate MAPE (Mean Absolute Percentage Error)
                mape = 0
                valid_predictions = 0
                
                for actual, predicted in zip(test_values, predictions):
                    if actual != 0:
                        mape += abs((actual - predicted) / actual)
                        valid_predictions += 1
                
                if valid_predictions > 0:
                    mape /= valid_predictions
                    accuracy = max(0, 1 - mape)  # Convert to accuracy
                    return min(1.0, accuracy)
            
            # Default accuracy based on R-squared
            return primary_trend.r_squared
            
        except Exception as e:
            self.logger.error(f"Error calculating forecast accuracy: {str(e)}")
            return 0.0
    
    async def _create_prediction_model(
        self,
        x_values: List[float],
        y_values: List[float],
        model_type: str,
        primary_trend: TrendPattern
    ) -> Dict[str, Any]:
        """Create prediction model"""
        try:
            if model_type == "linear":
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
                
                return {
                    "type": "linear",
                    "slope": slope,
                    "intercept": intercept,
                    "r_value": r_value,
                    "p_value": p_value,
                    "std_err": std_err
                }
            
            elif model_type == "exponential":
                # Transform to log space
                log_y_values = [math.log(max(y, 0.001)) for y in y_values]
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, log_y_values)
                
                return {
                    "type": "exponential",
                    "slope": slope,
                    "intercept": intercept,
                    "r_value": r_value,
                    "p_value": p_value,
                    "std_err": std_err
                }
            
            else:
                # Default to linear
                slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
                
                return {
                    "type": "linear",
                    "slope": slope,
                    "intercept": intercept,
                    "r_value": r_value,
                    "p_value": p_value,
                    "std_err": std_err
                }
                
        except Exception as e:
            self.logger.error(f"Error creating prediction model: {str(e)}")
            return {"type": "linear", "slope": 0, "intercept": 0}
    
    async def _apply_prediction_model(self, model: Dict[str, Any], x_value: float, model_type: str) -> float:
        """Apply prediction model to get predicted value"""
        try:
            if model["type"] == "linear":
                return model["slope"] * x_value + model["intercept"]
            
            elif model["type"] == "exponential":
                log_prediction = model["slope"] * x_value + model["intercept"]
                return math.exp(log_prediction)
            
            else:
                return model["slope"] * x_value + model["intercept"]
                
        except Exception as e:
            self.logger.error(f"Error applying prediction model: {str(e)}")
            return 0.0
    
    async def _calculate_prediction_confidence(
        self,
        trend_analysis: TrendAnalysis,
        model: Dict[str, Any],
        model_type: str
    ) -> PredictionConfidence:
        """Calculate prediction confidence"""
        try:
            # Base confidence on multiple factors
            confidence_score = 0
            
            # Factor 1: Primary trend strength
            if trend_analysis.primary_trend:
                if trend_analysis.primary_trend.strength == TrendStrength.VERY_STRONG:
                    confidence_score += 0.3
                elif trend_analysis.primary_trend.strength == TrendStrength.STRONG:
                    confidence_score += 0.25
                elif trend_analysis.primary_trend.strength == TrendStrength.MODERATE:
                    confidence_score += 0.15
            
            # Factor 2: R-squared value
            r_squared = model.get("r_value", 0) ** 2
            confidence_score += r_squared * 0.3
            
            # Factor 3: Data quality
            data_quality = len(trend_analysis.data_points) / 100  # Normalize
            confidence_score += min(data_quality, 0.2)
            
            # Factor 4: Forecast accuracy
            confidence_score += trend_analysis.forecast_accuracy * 0.2
            
            # Factor 5: Anomaly count (negative impact)
            anomaly_penalty = len(trend_analysis.anomalies) * 0.02
            confidence_score -= anomaly_penalty
            
            # Normalize to 0-1 range
            confidence_score = max(0, min(1, confidence_score))
            
            # Convert to confidence level
            if confidence_score >= 0.8:
                return PredictionConfidence.HIGH
            elif confidence_score >= 0.6:
                return PredictionConfidence.MEDIUM
            elif confidence_score >= 0.4:
                return PredictionConfidence.LOW
            else:
                return PredictionConfidence.VERY_LOW
                
        except Exception as e:
            self.logger.error(f"Error calculating prediction confidence: {str(e)}")
            return PredictionConfidence.VERY_LOW
    
    async def _calculate_trend_correlation(
        self,
        analysis1: TrendAnalysis,
        analysis2: TrendAnalysis
    ) -> float:
        """Calculate correlation between two trend analyses"""
        try:
            # Align data points by timestamp
            values1 = []
            values2 = []
            
            # Create timestamp-value maps
            map1 = {dp.timestamp: dp.value for dp in analysis1.data_points}
            map2 = {dp.timestamp: dp.value for dp in analysis2.data_points}
            
            # Find common timestamps
            common_timestamps = set(map1.keys()) & set(map2.keys())
            
            if len(common_timestamps) < 3:
                return 0.0
            
            # Extract values for common timestamps
            for timestamp in sorted(common_timestamps):
                values1.append(map1[timestamp])
                values2.append(map2[timestamp])
            
            # Calculate correlation
            correlation = np.corrcoef(values1, values2)[0, 1]
            
            return correlation if not np.isnan(correlation) else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating trend correlation: {str(e)}")
            return 0.0
    
    async def _calculate_trend_similarity(
        self,
        analysis1: TrendAnalysis,
        analysis2: TrendAnalysis
    ) -> float:
        """Calculate similarity between two trend analyses"""
        try:
            similarity_score = 0.0
            
            # Direction similarity
            if analysis1.primary_trend and analysis2.primary_trend:
                if analysis1.primary_trend.direction == analysis2.primary_trend.direction:
                    similarity_score += 0.3
                
                # Slope similarity (for linear trends)
                if (analysis1.primary_trend.pattern_type == TrendType.LINEAR and 
                    analysis2.primary_trend.pattern_type == TrendType.LINEAR):
                    
                    slope1 = analysis1.primary_trend.slope
                    slope2 = analysis2.primary_trend.slope
                    
                    if slope1 != 0 and slope2 != 0:
                        slope_similarity = 1 - abs(slope1 - slope2) / (abs(slope1) + abs(slope2))
                        similarity_score += slope_similarity * 0.3
            
            # Seasonality similarity
            if (analysis1.seasonality.get("has_seasonality") and 
                analysis2.seasonality.get("has_seasonality")):
                similarity_score += 0.2
            
            # Correlation factor
            correlation = await self._calculate_trend_correlation(analysis1, analysis2)
            similarity_score += abs(correlation) * 0.2
            
            return min(1.0, similarity_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating trend similarity: {str(e)}")
            return 0.0
    
    async def _find_divergence_points(self, trend_analyses: Dict[str, TrendAnalysis]) -> List[Dict[str, Any]]:
        """Find points where trends diverge"""
        try:
            divergence_points = []
            
            if len(trend_analyses) < 2:
                return divergence_points
            
            # Get all metric IDs
            metric_ids = list(trend_analyses.keys())
            
            # Compare each pair of metrics
            for i in range(len(metric_ids)):
                for j in range(i + 1, len(metric_ids)):
                    metric1 = metric_ids[i]
                    metric2 = metric_ids[j]
                    
                    analysis1 = trend_analyses[metric1]
                    analysis2 = trend_analyses[metric2]
                    
                    # Find timestamp ranges where trends differ significantly
                    if analysis1.primary_trend and analysis2.primary_trend:
                        if (analysis1.primary_trend.direction != analysis2.primary_trend.direction and
                            analysis1.primary_trend.direction != TrendDirection.STABLE and
                            analysis2.primary_trend.direction != TrendDirection.STABLE):
                            
                            divergence_point = {
                                "divergence_id": str(uuid.uuid4()),
                                "metric_pair": [metric1, metric2],
                                "divergence_type": "direction",
                                "metric1_direction": analysis1.primary_trend.direction,
                                "metric2_direction": analysis2.primary_trend.direction,
                                "divergence_strength": "high",
                                "time_range": {
                                    "start": max(analysis1.analysis_period[0], analysis2.analysis_period[0]).isoformat(),
                                    "end": min(analysis1.analysis_period[1], analysis2.analysis_period[1]).isoformat()
                                }
                            }
                            divergence_points.append(divergence_point)
            
            return divergence_points
            
        except Exception as e:
            self.logger.error(f"Error finding divergence points: {str(e)}")
            return []
    
    async def _generate_comparison_insights(
        self,
        trend_analyses: Dict[str, TrendAnalysis],
        correlations: Dict[str, float],
        similarities: Dict[str, float],
        divergences: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate insights from trend comparison"""
        try:
            insights = []
            
            # Correlation insights
            high_correlations = [k for k, v in correlations.items() if abs(v) > self.correlation_threshold]
            if high_correlations:
                insights.append(f"Strong correlations detected between {len(high_correlations)} metric pairs")
            
            # Similarity insights
            high_similarities = [k for k, v in similarities.items() if v > 0.7]
            if high_similarities:
                insights.append(f"High similarity found in {len(high_similarities)} trend patterns")
            
            # Divergence insights
            if divergences:
                insights.append(f"Trend divergences identified at {len(divergences)} points")
            
            # Overall trend insights
            upward_trends = sum(1 for analysis in trend_analyses.values() 
                              if analysis.primary_trend and analysis.primary_trend.direction == TrendDirection.UPWARD)
            downward_trends = sum(1 for analysis in trend_analyses.values() 
                                if analysis.primary_trend and analysis.primary_trend.direction == TrendDirection.DOWNWARD)
            
            if upward_trends > downward_trends:
                insights.append("Majority of metrics show upward trends")
            elif downward_trends > upward_trends:
                insights.append("Majority of metrics show downward trends")
            else:
                insights.append("Mixed trend directions across metrics")
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating comparison insights: {str(e)}")
            return []
    
    async def _generate_trend_recommendation(self, trend_pattern: TrendPattern) -> str:
        """Generate recommendation based on trend pattern"""
        try:
            if trend_pattern.direction == TrendDirection.UPWARD:
                if trend_pattern.strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                    return "Monitor for potential ceiling effects and prepare for capacity scaling"
                else:
                    return "Continue monitoring and consider factors driving the positive trend"
            
            elif trend_pattern.direction == TrendDirection.DOWNWARD:
                if trend_pattern.strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                    return "Immediate attention required - investigate root causes and implement corrective measures"
                else:
                    return "Monitor closely and investigate potential contributing factors"
            
            elif trend_pattern.direction == TrendDirection.STABLE:
                return "Stable performance - maintain current operations and monitor for changes"
            
            elif trend_pattern.direction == TrendDirection.VOLATILE:
                return "High volatility detected - investigate sources of instability and implement smoothing measures"
            
            elif trend_pattern.direction == TrendDirection.SEASONAL:
                return "Seasonal patterns detected - adjust planning and resource allocation accordingly"
            
            else:
                return "Continue monitoring and gather more data for better trend analysis"
                
        except Exception as e:
            self.logger.error(f"Error generating trend recommendation: {str(e)}")
            return "Monitor and analyze further"
    
    async def _check_trend_alerts(self, trend_analysis: TrendAnalysis):
        """Check for trend-based alerts"""
        try:
            alerts = []
            
            # Critical downward trend alert
            if (trend_analysis.primary_trend and 
                trend_analysis.primary_trend.direction == TrendDirection.DOWNWARD and
                trend_analysis.primary_trend.strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]):
                
                alert = TrendAlert(
                    alert_id=str(uuid.uuid4()),
                    metric_id=trend_analysis.metric_id,
                    alert_type="critical_downward_trend",
                    severity="critical",
                    title="Critical Downward Trend Detected",
                    description=f"Metric {trend_analysis.metric_id} shows strong downward trend",
                    triggered_time=datetime.now(timezone.utc),
                    threshold_value=0.0,
                    current_value=trend_analysis.primary_trend.slope,
                    trend_data=trend_analysis.primary_trend.to_dict(),
                    recommendations=[
                        "Immediate investigation required",
                        "Review operational processes",
                        "Consider emergency interventions"
                    ]
                )
                alerts.append(alert)
            
            # High volatility alert
            if len(trend_analysis.data_points) > 1:
                values = [dp.value for dp in trend_analysis.data_points]
                cv = statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) > 0 else 0
                
                if cv > self.volatility_threshold:
                    alert = TrendAlert(
                        alert_id=str(uuid.uuid4()),
                        metric_id=trend_analysis.metric_id,
                        alert_type="high_volatility",
                        severity="warning",
                        title="High Volatility Detected",
                        description=f"Metric {trend_analysis.metric_id} shows high volatility (CV: {cv:.2f})",
                        triggered_time=datetime.now(timezone.utc),
                        threshold_value=self.volatility_threshold,
                        current_value=cv,
                        trend_data={"coefficient_of_variation": cv},
                        recommendations=[
                            "Investigate sources of volatility",
                            "Consider implementing smoothing measures",
                            "Review data collection processes"
                        ]
                    )
                    alerts.append(alert)
            
            # Multiple anomalies alert
            if len(trend_analysis.anomalies) > 5:
                alert = TrendAlert(
                    alert_id=str(uuid.uuid4()),
                    metric_id=trend_analysis.metric_id,
                    alert_type="multiple_anomalies",
                    severity="warning",
                    title="Multiple Anomalies Detected",
                    description=f"Metric {trend_analysis.metric_id} has {len(trend_analysis.anomalies)} anomalies",
                    triggered_time=datetime.now(timezone.utc),
                    threshold_value=5,
                    current_value=len(trend_analysis.anomalies),
                    trend_data={"anomaly_count": len(trend_analysis.anomalies)},
                    recommendations=[
                        "Review data quality",
                        "Investigate anomaly causes",
                        "Consider data validation improvements"
                    ]
                )
                alerts.append(alert)
            
            # Store alerts and send notifications
            for alert in alerts:
                self.trend_alerts[alert.alert_id] = alert
                
                await self.notification_service.send_notification(
                    type="trend_alert",
                    data=alert.to_dict()
                )
            
        except Exception as e:
            self.logger.error(f"Error checking trend alerts: {str(e)}")
    
    async def _periodic_analysis(self):
        """Periodic trend analysis task"""
        while True:
            try:
                await asyncio.sleep(self.analysis_interval)
                
                # Get active metrics for analysis
                metrics_summary = await self.unified_metrics.get_metrics_summary()
                
                # Analyze trends for key metrics
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                
                for metric_id in list(self.unified_metrics.metric_definitions.keys())[:5]:  # Limit to 5 for demo
                    try:
                        await self.analyze_metric_trend(metric_id, (start_time, end_time))
                    except Exception as e:
                        self.logger.error(f"Error in periodic analysis for {metric_id}: {str(e)}")
                
            except Exception as e:
                self.logger.error(f"Error in periodic analysis: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "trend.alert_triggered",
                self._handle_trend_alert
            )
            
            await self.event_bus.subscribe(
                "metrics.updated",
                self._handle_metrics_updated
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_trend_alert(self, event_data: Dict[str, Any]):
        """Handle trend alert event"""
        try:
            alert_id = event_data.get("alert_id")
            self.logger.info(f"Trend alert triggered: {alert_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling trend alert: {str(e)}")
    
    async def _handle_metrics_updated(self, event_data: Dict[str, Any]):
        """Handle metrics updated event"""
        try:
            metric_id = event_data.get("metric_id")
            
            # Trigger trend analysis for updated metric
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=12)
            
            await self.analyze_metric_trend(metric_id, (start_time, end_time))
            
        except Exception as e:
            self.logger.error(f"Error handling metrics updated: {str(e)}")
    
    async def get_trend_summary(self) -> Dict[str, Any]:
        """Get trend analysis summary"""
        try:
            return {
                "total_analyses": len(self.trend_analyses),
                "total_predictions": len(self.trend_predictions),
                "total_alerts": len(self.trend_alerts),
                "active_alerts": len([a for a in self.trend_alerts.values() if a.severity in ["critical", "warning"]]),
                "trend_directions": {
                    "upward": len([a for a in self.trend_analyses.values() 
                                 if a.primary_trend and a.primary_trend.direction == TrendDirection.UPWARD]),
                    "downward": len([a for a in self.trend_analyses.values() 
                                   if a.primary_trend and a.primary_trend.direction == TrendDirection.DOWNWARD]),
                    "stable": len([a for a in self.trend_analyses.values() 
                                 if a.primary_trend and a.primary_trend.direction == TrendDirection.STABLE])
                },
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trend summary: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            unified_metrics_health = await self.unified_metrics.health_check()
            kpi_calculator_health = await self.kpi_calculator.health_check()
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "trend_analyzer",
                "components": {
                    "unified_metrics": unified_metrics_health,
                    "kpi_calculator": kpi_calculator_health,
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_analyses": len(self.trend_analyses),
                    "total_predictions": len(self.trend_predictions),
                    "total_alerts": len(self.trend_alerts)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "trend_analyzer",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Trend analyzer service cleanup initiated")
        
        try:
            # Clear caches
            self.trend_analyses.clear()
            self.trend_predictions.clear()
            self.trend_alerts.clear()
            self.trend_models.clear()
            
            # Cleanup dependencies
            await self.unified_metrics.cleanup()
            await self.kpi_calculator.cleanup()
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Trend analyzer service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_trend_analyzer(
    unified_metrics: UnifiedMetrics = None,
    kpi_calculator: KPICalculator = None
) -> TrendAnalyzer:
    """Create trend analyzer service"""
    return TrendAnalyzer(unified_metrics, kpi_calculator)