"""
APP Service: Performance Analytics
Analyzes APP performance statistics and provides insights for optimization
"""

import asyncio
import json
import logging
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter, deque
import numpy as np


class PerformanceMetricType(str, Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"
    RESOURCE_UTILIZATION = "resource_utilization"
    LATENCY = "latency"
    CONCURRENT_USERS = "concurrent_users"
    QUEUE_SIZE = "queue_size"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class PerformanceStatus(str, Enum):
    """Performance status levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    CRITICAL = "critical"


class TrendDirection(str, Enum):
    """Trend direction indicators"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


class AnalysisType(str, Enum):
    """Types of performance analysis"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement"""
    metric_id: str
    metric_type: PerformanceMetricType
    value: float
    unit: str
    timestamp: datetime
    source: str
    labels: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric_type: PerformanceMetricType
    excellent_threshold: float
    good_threshold: float
    acceptable_threshold: float
    poor_threshold: float
    unit: str
    higher_is_better: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceInsight:
    """Performance insight and recommendation"""
    insight_id: str
    category: str
    title: str
    description: str
    severity: str
    impact: str
    recommendation: str
    affected_metrics: List[str]
    confidence: float
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations"""
    alert_id: str
    metric_type: PerformanceMetricType
    current_value: float
    threshold_value: float
    threshold_type: str
    severity: str
    message: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['triggered_at'] = self.triggered_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


@dataclass
class PerformanceAnalysis:
    """Comprehensive performance analysis result"""
    analysis_id: str
    analysis_type: AnalysisType
    period_start: datetime
    period_end: datetime
    metrics_analyzed: int
    overall_score: float
    status: PerformanceStatus
    trend: TrendDirection
    summary: Dict[str, Any]
    insights: List[PerformanceInsight]
    alerts: List[PerformanceAlert]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['period_start'] = self.period_start.isoformat()
        data['period_end'] = self.period_end.isoformat()
        return data


class PerformanceDataProvider:
    """Data provider for performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Mock data simulation
        self._metric_buffer = deque(maxlen=10000)
        self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate mock performance data"""
        import random
        
        now = datetime.now(timezone.utc)
        
        # Generate historical data for the last 24 hours
        for i in range(1440):  # 1440 minutes = 24 hours
            timestamp = now - timedelta(minutes=i)
            
            # Response time (varying throughout the day)
            base_response_time = 2.0 + 0.5 * np.sin(i / 60)  # Daily cycle
            response_time = max(0.1, base_response_time + random.gauss(0, 0.3))
            
            self._metric_buffer.append(PerformanceMetric(
                metric_id=f"response_time_{i}",
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                value=response_time,
                unit="seconds",
                timestamp=timestamp,
                source="firs_app"
            ))
            
            # Throughput (requests per minute)
            base_throughput = 50 + 20 * np.sin(i / 120)  # Business hour cycle
            throughput = max(5, base_throughput + random.gauss(0, 10))
            
            self._metric_buffer.append(PerformanceMetric(
                metric_id=f"throughput_{i}",
                metric_type=PerformanceMetricType.THROUGHPUT,
                value=throughput,
                unit="requests/minute",
                timestamp=timestamp,
                source="firs_app"
            ))
            
            # Error rate (percentage)
            base_error_rate = 0.5 + 0.3 * np.sin(i / 200)
            error_rate = max(0, base_error_rate + random.gauss(0, 0.2))
            
            self._metric_buffer.append(PerformanceMetric(
                metric_id=f"error_rate_{i}",
                metric_type=PerformanceMetricType.ERROR_RATE,
                value=error_rate,
                unit="percentage",
                timestamp=timestamp,
                source="firs_app"
            ))
            
            # CPU usage
            base_cpu = 40 + 15 * np.sin(i / 90)
            cpu_usage = max(5, min(95, base_cpu + random.gauss(0, 8)))
            
            self._metric_buffer.append(PerformanceMetric(
                metric_id=f"cpu_usage_{i}",
                metric_type=PerformanceMetricType.CPU_USAGE,
                value=cpu_usage,
                unit="percentage",
                timestamp=timestamp,
                source="system"
            ))
    
    async def get_metrics(self, 
                         start_date: datetime,
                         end_date: datetime,
                         metric_types: Optional[List[PerformanceMetricType]] = None) -> List[PerformanceMetric]:
        """Get performance metrics for specified time range"""
        filtered_metrics = []
        
        for metric in self._metric_buffer:
            if start_date <= metric.timestamp <= end_date:
                if not metric_types or metric.metric_type in metric_types:
                    filtered_metrics.append(metric)
        
        return filtered_metrics
    
    async def get_real_time_metrics(self) -> List[PerformanceMetric]:
        """Get current real-time performance metrics"""
        now = datetime.now(timezone.utc)
        last_minute = now - timedelta(minutes=1)
        
        return await self.get_metrics(last_minute, now)
    
    async def get_aggregated_metrics(self, 
                                   start_date: datetime,
                                   end_date: datetime,
                                   metric_type: PerformanceMetricType,
                                   aggregation_interval: str = "hourly") -> List[Dict[str, Any]]:
        """Get aggregated performance metrics"""
        metrics = await self.get_metrics(start_date, end_date, [metric_type])
        
        if not metrics:
            return []
        
        # Group by time interval
        if aggregation_interval == "hourly":
            interval_seconds = 3600
        elif aggregation_interval == "daily":
            interval_seconds = 86400
        else:
            interval_seconds = 3600
        
        grouped_metrics = defaultdict(list)
        for metric in metrics:
            # Round timestamp to interval
            timestamp_seconds = int(metric.timestamp.timestamp())
            interval_start = timestamp_seconds - (timestamp_seconds % interval_seconds)
            interval_datetime = datetime.fromtimestamp(interval_start, tz=timezone.utc)
            
            grouped_metrics[interval_datetime].append(metric.value)
        
        # Calculate aggregations
        aggregated = []
        for interval_time, values in grouped_metrics.items():
            aggregated.append({
                'timestamp': interval_time.isoformat(),
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'median': statistics.median(values),
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99)
            })
        
        return sorted(aggregated, key=lambda x: x['timestamp'])


class PerformanceThresholdManager:
    """Manages performance thresholds and alerting"""
    
    def __init__(self):
        self.thresholds = self._get_default_thresholds()
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: List[PerformanceAlert] = []
    
    def _get_default_thresholds(self) -> Dict[PerformanceMetricType, PerformanceThreshold]:
        """Get default performance thresholds"""
        return {
            PerformanceMetricType.RESPONSE_TIME: PerformanceThreshold(
                metric_type=PerformanceMetricType.RESPONSE_TIME,
                excellent_threshold=1.0,
                good_threshold=2.0,
                acceptable_threshold=5.0,
                poor_threshold=10.0,
                unit="seconds",
                higher_is_better=False
            ),
            PerformanceMetricType.THROUGHPUT: PerformanceThreshold(
                metric_type=PerformanceMetricType.THROUGHPUT,
                excellent_threshold=100.0,
                good_threshold=50.0,
                acceptable_threshold=20.0,
                poor_threshold=10.0,
                unit="requests/minute",
                higher_is_better=True
            ),
            PerformanceMetricType.ERROR_RATE: PerformanceThreshold(
                metric_type=PerformanceMetricType.ERROR_RATE,
                excellent_threshold=0.1,
                good_threshold=0.5,
                acceptable_threshold=1.0,
                poor_threshold=5.0,
                unit="percentage",
                higher_is_better=False
            ),
            PerformanceMetricType.CPU_USAGE: PerformanceThreshold(
                metric_type=PerformanceMetricType.CPU_USAGE,
                excellent_threshold=50.0,
                good_threshold=70.0,
                acceptable_threshold=85.0,
                poor_threshold=95.0,
                unit="percentage",
                higher_is_better=False
            )
        }
    
    def evaluate_metric(self, metric: PerformanceMetric) -> Tuple[PerformanceStatus, Optional[PerformanceAlert]]:
        """Evaluate metric against thresholds"""
        threshold = self.thresholds.get(metric.metric_type)
        if not threshold:
            return PerformanceStatus.ACCEPTABLE, None
        
        value = metric.value
        
        # Determine status
        if threshold.higher_is_better:
            if value >= threshold.excellent_threshold:
                status = PerformanceStatus.EXCELLENT
            elif value >= threshold.good_threshold:
                status = PerformanceStatus.GOOD
            elif value >= threshold.acceptable_threshold:
                status = PerformanceStatus.ACCEPTABLE
            elif value >= threshold.poor_threshold:
                status = PerformanceStatus.POOR
            else:
                status = PerformanceStatus.CRITICAL
        else:
            if value <= threshold.excellent_threshold:
                status = PerformanceStatus.EXCELLENT
            elif value <= threshold.good_threshold:
                status = PerformanceStatus.GOOD
            elif value <= threshold.acceptable_threshold:
                status = PerformanceStatus.ACCEPTABLE
            elif value <= threshold.poor_threshold:
                status = PerformanceStatus.POOR
            else:
                status = PerformanceStatus.CRITICAL
        
        # Generate alert if needed
        alert = None
        if status in [PerformanceStatus.POOR, PerformanceStatus.CRITICAL]:
            alert_id = f"ALERT_{metric.metric_type.value}_{int(metric.timestamp.timestamp())}"
            
            # Check if similar alert already exists
            existing_alert = None
            for existing_id, existing_alert_obj in self.active_alerts.items():
                if (existing_alert_obj.metric_type == metric.metric_type and 
                    not existing_alert_obj.resolved_at):
                    existing_alert = existing_alert_obj
                    break
            
            if not existing_alert:
                alert = PerformanceAlert(
                    alert_id=alert_id,
                    metric_type=metric.metric_type,
                    current_value=value,
                    threshold_value=threshold.poor_threshold,
                    threshold_type="poor" if status == PerformanceStatus.POOR else "critical",
                    severity="high" if status == PerformanceStatus.POOR else "critical",
                    message=f"{metric.metric_type.value} is {status.value}: {value} {threshold.unit}",
                    triggered_at=metric.timestamp
                )
                
                self.active_alerts[alert_id] = alert
        
        return status, alert


class PerformanceAnalyzer:
    """
    Comprehensive performance analyzer for APP services
    Provides detailed analytics, insights, and recommendations
    """
    
    def __init__(self, data_provider: Optional[PerformanceDataProvider] = None):
        self.data_provider = data_provider or PerformanceDataProvider()
        self.threshold_manager = PerformanceThresholdManager()
        self.logger = logging.getLogger(__name__)
        
        # Analysis cache
        self._analysis_cache: Dict[str, PerformanceAnalysis] = {}
        
        # Statistics
        self.stats = {
            'analyses_performed': 0,
            'insights_generated': 0,
            'alerts_triggered': 0,
            'last_analysis_at': None,
            'average_analysis_time': 0.0
        }
    
    async def analyze_performance(self, 
                                analysis_type: AnalysisType,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None,
                                metric_types: Optional[List[PerformanceMetricType]] = None) -> PerformanceAnalysis:
        """
        Perform comprehensive performance analysis
        
        Args:
            analysis_type: Type of analysis to perform
            start_date: Start date for analysis period
            end_date: End date for analysis period
            metric_types: Specific metric types to analyze
            
        Returns:
            Comprehensive performance analysis
        """
        start_time = datetime.now(timezone.utc)
        
        # Set default date range based on analysis type
        if not end_date:
            end_date = datetime.now(timezone.utc)
        
        if not start_date:
            if analysis_type == AnalysisType.REAL_TIME:
                start_date = end_date - timedelta(minutes=5)
            elif analysis_type == AnalysisType.HOURLY:
                start_date = end_date - timedelta(hours=1)
            elif analysis_type == AnalysisType.DAILY:
                start_date = end_date - timedelta(days=1)
            elif analysis_type == AnalysisType.WEEKLY:
                start_date = end_date - timedelta(weeks=1)
            elif analysis_type == AnalysisType.MONTHLY:
                start_date = end_date - timedelta(days=30)
            else:
                start_date = end_date - timedelta(days=1)
        
        self.logger.info(f"Starting performance analysis: {analysis_type.value} from {start_date} to {end_date}")
        
        try:
            # Get metrics
            metrics = await self.data_provider.get_metrics(start_date, end_date, metric_types)
            
            if not metrics:
                self.logger.warning("No metrics found for analysis period")
                return self._create_empty_analysis(analysis_type, start_date, end_date)
            
            # Analyze metrics
            metric_analysis = self._analyze_metrics(metrics)
            
            # Calculate overall score and status
            overall_score, status = self._calculate_overall_performance(metric_analysis)
            
            # Determine trend
            trend = await self._analyze_trend(metrics, start_date, end_date)
            
            # Generate insights
            insights = self._generate_insights(metric_analysis, trend)
            
            # Check for alerts
            alerts = self._check_alerts(metrics)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metric_analysis, insights, alerts)
            
            # Create analysis result
            analysis = PerformanceAnalysis(
                analysis_id=f"PERF_{analysis_type.value}_{int(start_time.timestamp())}",
                analysis_type=analysis_type,
                period_start=start_date,
                period_end=end_date,
                metrics_analyzed=len(metrics),
                overall_score=overall_score,
                status=status,
                trend=trend,
                summary=metric_analysis,
                insights=insights,
                alerts=alerts,
                recommendations=recommendations
            )
            
            # Cache analysis
            self._analysis_cache[analysis.analysis_id] = analysis
            
            # Update statistics
            analysis_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self._update_stats(analysis_time, len(insights), len(alerts))
            
            self.logger.info(
                f"Performance analysis completed: Score {overall_score:.1f}, "
                f"Status {status.value}, {len(insights)} insights, {len(alerts)} alerts"
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error during performance analysis: {str(e)}")
            raise
    
    def _create_empty_analysis(self, 
                              analysis_type: AnalysisType,
                              start_date: datetime,
                              end_date: datetime) -> PerformanceAnalysis:
        """Create empty analysis when no metrics are available"""
        return PerformanceAnalysis(
            analysis_id=f"EMPTY_{analysis_type.value}_{int(datetime.now(timezone.utc).timestamp())}",
            analysis_type=analysis_type,
            period_start=start_date,
            period_end=end_date,
            metrics_analyzed=0,
            overall_score=0.0,
            status=PerformanceStatus.CRITICAL,
            trend=TrendDirection.STABLE,
            summary={},
            insights=[],
            alerts=[],
            recommendations=["No metrics available for analysis period"]
        )
    
    def _analyze_metrics(self, metrics: List[PerformanceMetric]) -> Dict[str, Any]:
        """Analyze performance metrics and calculate statistics"""
        analysis = {}
        
        # Group metrics by type
        metric_groups = defaultdict(list)
        for metric in metrics:
            metric_groups[metric.metric_type].append(metric.value)
        
        # Calculate statistics for each metric type
        for metric_type, values in metric_groups.items():
            if not values:
                continue
            
            stats = {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'p95': np.percentile(values, 95),
                'p99': np.percentile(values, 99)
            }
            
            # Evaluate against thresholds
            threshold = self.threshold_manager.thresholds.get(metric_type)
            if threshold:
                if threshold.higher_is_better:
                    performance_score = min(100, (stats['avg'] / threshold.excellent_threshold) * 100)
                else:
                    performance_score = max(0, 100 - (stats['avg'] / threshold.excellent_threshold) * 100)
                
                stats['performance_score'] = performance_score
                stats['threshold'] = threshold.to_dict()
            
            analysis[metric_type.value] = stats
        
        return analysis
    
    def _calculate_overall_performance(self, metric_analysis: Dict[str, Any]) -> Tuple[float, PerformanceStatus]:
        """Calculate overall performance score and status"""
        if not metric_analysis:
            return 0.0, PerformanceStatus.CRITICAL
        
        # Weight different metrics
        metric_weights = {
            PerformanceMetricType.RESPONSE_TIME.value: 0.3,
            PerformanceMetricType.THROUGHPUT.value: 0.25,
            PerformanceMetricType.ERROR_RATE.value: 0.25,
            PerformanceMetricType.CPU_USAGE.value: 0.2
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for metric_type, analysis in metric_analysis.items():
            weight = metric_weights.get(metric_type, 0.1)
            score = analysis.get('performance_score', 50)
            
            weighted_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            overall_score = 0.0
        else:
            overall_score = weighted_score / total_weight
        
        # Determine status
        if overall_score >= 90:
            status = PerformanceStatus.EXCELLENT
        elif overall_score >= 75:
            status = PerformanceStatus.GOOD
        elif overall_score >= 60:
            status = PerformanceStatus.ACCEPTABLE
        elif overall_score >= 40:
            status = PerformanceStatus.POOR
        else:
            status = PerformanceStatus.CRITICAL
        
        return round(overall_score, 1), status
    
    async def _analyze_trend(self, 
                           metrics: List[PerformanceMetric],
                           start_date: datetime,
                           end_date: datetime) -> TrendDirection:
        """Analyze performance trend over the period"""
        if not metrics:
            return TrendDirection.STABLE
        
        # Sort metrics by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        
        # Group by metric type and calculate trend
        metric_trends = {}
        metric_groups = defaultdict(list)
        
        for metric in sorted_metrics:
            metric_groups[metric.metric_type].append(metric)
        
        for metric_type, type_metrics in metric_groups.items():
            if len(type_metrics) < 3:
                continue
            
            # Calculate trend using linear regression
            timestamps = [(m.timestamp - start_date).total_seconds() for m in type_metrics]
            values = [m.value for m in type_metrics]
            
            if len(timestamps) > 1:
                correlation = np.corrcoef(timestamps, values)[0, 1]
                
                if abs(correlation) < 0.1:
                    trend = TrendDirection.STABLE
                elif correlation > 0.3:
                    trend = TrendDirection.IMPROVING if self.threshold_manager.thresholds[metric_type].higher_is_better else TrendDirection.DECLINING
                elif correlation < -0.3:
                    trend = TrendDirection.DECLINING if self.threshold_manager.thresholds[metric_type].higher_is_better else TrendDirection.IMPROVING
                else:
                    trend = TrendDirection.VOLATILE
                
                metric_trends[metric_type] = trend
        
        # Determine overall trend
        if not metric_trends:
            return TrendDirection.STABLE
        
        trend_counts = Counter(metric_trends.values())
        
        if trend_counts[TrendDirection.IMPROVING] > trend_counts[TrendDirection.DECLINING]:
            return TrendDirection.IMPROVING
        elif trend_counts[TrendDirection.DECLINING] > trend_counts[TrendDirection.IMPROVING]:
            return TrendDirection.DECLINING
        elif trend_counts[TrendDirection.VOLATILE] > 0:
            return TrendDirection.VOLATILE
        else:
            return TrendDirection.STABLE
    
    def _generate_insights(self, 
                          metric_analysis: Dict[str, Any],
                          trend: TrendDirection) -> List[PerformanceInsight]:
        """Generate performance insights based on analysis"""
        insights = []
        now = datetime.now(timezone.utc)
        
        # Response time insights
        if PerformanceMetricType.RESPONSE_TIME.value in metric_analysis:
            rt_analysis = metric_analysis[PerformanceMetricType.RESPONSE_TIME.value]
            avg_response_time = rt_analysis['avg']
            
            if avg_response_time > 5.0:
                insights.append(PerformanceInsight(
                    insight_id=f"RT_HIGH_{int(now.timestamp())}",
                    category="response_time",
                    title="High Response Time Detected",
                    description=f"Average response time ({avg_response_time:.2f}s) exceeds acceptable threshold (5.0s)",
                    severity="high",
                    impact="User experience degradation, potential SLA violations",
                    recommendation="Investigate database queries, optimize API endpoints, consider caching",
                    affected_metrics=[PerformanceMetricType.RESPONSE_TIME.value],
                    confidence=0.9,
                    created_at=now
                ))
        
        # Throughput insights
        if PerformanceMetricType.THROUGHPUT.value in metric_analysis:
            tp_analysis = metric_analysis[PerformanceMetricType.THROUGHPUT.value]
            avg_throughput = tp_analysis['avg']
            
            if avg_throughput < 20:
                insights.append(PerformanceInsight(
                    insight_id=f"TP_LOW_{int(now.timestamp())}",
                    category="throughput",
                    title="Low Throughput Detected",
                    description=f"Average throughput ({avg_throughput:.1f} req/min) is below acceptable threshold (20 req/min)",
                    severity="medium",
                    impact="Reduced system capacity, potential bottlenecks",
                    recommendation="Scale up resources, optimize request processing, review queue management",
                    affected_metrics=[PerformanceMetricType.THROUGHPUT.value],
                    confidence=0.8,
                    created_at=now
                ))
        
        # Error rate insights
        if PerformanceMetricType.ERROR_RATE.value in metric_analysis:
            er_analysis = metric_analysis[PerformanceMetricType.ERROR_RATE.value]
            avg_error_rate = er_analysis['avg']
            
            if avg_error_rate > 1.0:
                insights.append(PerformanceInsight(
                    insight_id=f"ER_HIGH_{int(now.timestamp())}",
                    category="error_rate",
                    title="High Error Rate Detected",
                    description=f"Average error rate ({avg_error_rate:.2f}%) exceeds acceptable threshold (1.0%)",
                    severity="high",
                    impact="Service reliability issues, potential data loss",
                    recommendation="Review error logs, fix recurring issues, improve error handling",
                    affected_metrics=[PerformanceMetricType.ERROR_RATE.value],
                    confidence=0.95,
                    created_at=now
                ))
        
        # Trend-based insights
        if trend == TrendDirection.DECLINING:
            insights.append(PerformanceInsight(
                insight_id=f"TREND_DECLINING_{int(now.timestamp())}",
                category="trend",
                title="Performance Declining Trend",
                description="Overall performance shows declining trend over the analysis period",
                severity="medium",
                impact="Gradual performance degradation, potential future issues",
                recommendation="Investigate root causes, plan performance optimization, monitor closely",
                affected_metrics=list(metric_analysis.keys()),
                confidence=0.7,
                created_at=now
            ))
        
        return insights
    
    def _check_alerts(self, metrics: List[PerformanceMetric]) -> List[PerformanceAlert]:
        """Check metrics against thresholds and generate alerts"""
        alerts = []
        
        for metric in metrics:
            status, alert = self.threshold_manager.evaluate_metric(metric)
            if alert:
                alerts.append(alert)
        
        return alerts
    
    def _generate_recommendations(self, 
                                 metric_analysis: Dict[str, Any],
                                 insights: List[PerformanceInsight],
                                 alerts: List[PerformanceAlert]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []
        
        # High-level recommendations based on analysis
        if not metric_analysis:
            recommendations.append("Set up comprehensive performance monitoring with key metrics")
            return recommendations
        
        # Response time recommendations
        if PerformanceMetricType.RESPONSE_TIME.value in metric_analysis:
            rt_analysis = metric_analysis[PerformanceMetricType.RESPONSE_TIME.value]
            if rt_analysis['avg'] > 3.0:
                recommendations.extend([
                    "Implement response time optimization strategies",
                    "Review database query performance and add indexes",
                    "Consider implementing caching mechanisms",
                    "Optimize API endpoint logic and reduce processing time"
                ])
        
        # Throughput recommendations
        if PerformanceMetricType.THROUGHPUT.value in metric_analysis:
            tp_analysis = metric_analysis[PerformanceMetricType.THROUGHPUT.value]
            if tp_analysis['avg'] < 30:
                recommendations.extend([
                    "Scale up application resources to handle increased load",
                    "Implement load balancing across multiple instances",
                    "Optimize request processing pipeline",
                    "Review and tune connection pooling settings"
                ])
        
        # Error rate recommendations
        if PerformanceMetricType.ERROR_RATE.value in metric_analysis:
            er_analysis = metric_analysis[PerformanceMetricType.ERROR_RATE.value]
            if er_analysis['avg'] > 0.5:
                recommendations.extend([
                    "Implement comprehensive error tracking and monitoring",
                    "Review and improve error handling mechanisms",
                    "Investigate root causes of recurring errors",
                    "Implement circuit breakers for external service calls"
                ])
        
        # Alert-based recommendations
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        if critical_alerts:
            recommendations.append("Immediately address critical performance alerts to prevent service disruption")
        
        # Insight-based recommendations
        high_severity_insights = [i for i in insights if i.severity == "high"]
        if high_severity_insights:
            recommendations.append("Focus on high-severity performance insights for maximum impact")
        
        # General recommendations
        if not recommendations:
            recommendations.extend([
                "Continue monitoring performance metrics regularly",
                "Set up automated alerting for performance thresholds",
                "Plan capacity scaling based on usage patterns",
                "Implement performance testing in CI/CD pipeline"
            ])
        
        return recommendations
    
    def _update_stats(self, analysis_time: float, insights_count: int, alerts_count: int):
        """Update analyzer statistics"""
        self.stats['analyses_performed'] += 1
        self.stats['insights_generated'] += insights_count
        self.stats['alerts_triggered'] += alerts_count
        self.stats['last_analysis_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update average analysis time
        current_avg = self.stats['average_analysis_time']
        total_analyses = self.stats['analyses_performed']
        self.stats['average_analysis_time'] = (
            (current_avg * (total_analyses - 1) + analysis_time) / total_analyses
        )
    
    async def get_real_time_dashboard(self) -> Dict[str, Any]:
        """Get real-time performance dashboard data"""
        # Get last 5 minutes of data
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(minutes=5)
        
        # Perform real-time analysis
        analysis = await self.analyze_performance(
            analysis_type=AnalysisType.REAL_TIME,
            start_date=start_time,
            end_date=end_time
        )
        
        # Get current metrics
        current_metrics = await self.data_provider.get_real_time_metrics()
        
        # Calculate current values
        current_values = {}
        for metric_type in PerformanceMetricType:
            type_metrics = [m for m in current_metrics if m.metric_type == metric_type]
            if type_metrics:
                current_values[metric_type.value] = {
                    'value': statistics.mean([m.value for m in type_metrics]),
                    'unit': type_metrics[0].unit,
                    'status': self.threshold_manager.evaluate_metric(type_metrics[-1])[0].value
                }
        
        return {
            'timestamp': end_time.isoformat(),
            'overall_score': analysis.overall_score,
            'overall_status': analysis.status.value,
            'trend': analysis.trend.value,
            'current_metrics': current_values,
            'active_alerts': len(analysis.alerts),
            'insights_count': len(analysis.insights),
            'metrics_analyzed': analysis.metrics_analyzed
        }
    
    async def get_performance_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get performance trends over specified number of days"""
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        trends = {}
        
        for metric_type in PerformanceMetricType:
            try:
                aggregated = await self.data_provider.get_aggregated_metrics(
                    start_date, end_date, metric_type, "daily"
                )
                
                if aggregated:
                    trends[metric_type.value] = {
                        'data_points': aggregated,
                        'trend_direction': self._calculate_metric_trend(aggregated),
                        'latest_value': aggregated[-1]['avg'] if aggregated else 0,
                        'change_percentage': self._calculate_change_percentage(aggregated)
                    }
                    
            except Exception as e:
                self.logger.warning(f"Error getting trends for {metric_type.value}: {str(e)}")
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'trends': trends
        }
    
    def _calculate_metric_trend(self, aggregated_data: List[Dict[str, Any]]) -> str:
        """Calculate trend direction for aggregated metric data"""
        if len(aggregated_data) < 2:
            return "stable"
        
        values = [point['avg'] for point in aggregated_data]
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return "stable"
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        change_percentage = ((second_avg - first_avg) / first_avg) * 100
        
        if change_percentage > 5:
            return "improving"
        elif change_percentage < -5:
            return "declining"
        else:
            return "stable"
    
    def _calculate_change_percentage(self, aggregated_data: List[Dict[str, Any]]) -> float:
        """Calculate percentage change from first to last data point"""
        if len(aggregated_data) < 2:
            return 0.0
        
        first_value = aggregated_data[0]['avg']
        last_value = aggregated_data[-1]['avg']
        
        if first_value == 0:
            return 0.0
        
        return round(((last_value - first_value) / first_value) * 100, 1)
    
    async def health_check(self) -> Dict[str, Any]:
        """Get performance analyzer health status"""
        recent_metrics = await self.data_provider.get_real_time_metrics()
        active_alerts = len(self.threshold_manager.active_alerts)
        
        status = "healthy"
        if active_alerts > 10:
            status = "degraded"
        elif not recent_metrics:
            status = "no_data"
        
        return {
            'status': status,
            'service': 'performance_analytics',
            'active_alerts': active_alerts,
            'recent_metrics_count': len(recent_metrics),
            'cached_analyses': len(self._analysis_cache),
            'stats': self.stats.copy(),
            'supported_metrics': [metric.value for metric in PerformanceMetricType],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup performance analyzer resources"""
        self.logger.info("Performance analyzer cleanup initiated")
        
        # Clear cache
        self._analysis_cache.clear()
        
        # Log final statistics
        self.logger.info(f"Final performance analytics statistics: {self.stats}")
        
        self.logger.info("Performance analyzer cleanup completed")


# Factory functions
def create_performance_analyzer() -> PerformanceAnalyzer:
    """Create performance analyzer with standard configuration"""
    return PerformanceAnalyzer()


def create_custom_threshold(metric_type: PerformanceMetricType,
                          excellent: float,
                          good: float,
                          acceptable: float,
                          poor: float,
                          unit: str,
                          higher_is_better: bool = True) -> PerformanceThreshold:
    """Create custom performance threshold"""
    return PerformanceThreshold(
        metric_type=metric_type,
        excellent_threshold=excellent,
        good_threshold=good,
        acceptable_threshold=acceptable,
        poor_threshold=poor,
        unit=unit,
        higher_is_better=higher_is_better
    )