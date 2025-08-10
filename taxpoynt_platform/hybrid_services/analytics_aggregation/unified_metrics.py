"""
Hybrid Service: Unified Metrics
Aggregates SI and APP metrics for comprehensive analytics
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

from core_platform.database import get_db_session
from core_platform.models.metrics import MetricRecord, MetricAggregation, MetricSnapshot
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics"""
    PERFORMANCE = "performance"
    THROUGHPUT = "throughput"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    AVAILABILITY = "availability"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    BUSINESS = "business"
    OPERATIONAL = "operational"


class MetricScope(str, Enum):
    """Metric aggregation scope"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    CROSS_ROLE = "cross_role"
    SYSTEM_WIDE = "system_wide"


class AggregationMethod(str, Enum):
    """Aggregation methods"""
    SUM = "sum"
    AVERAGE = "average"
    COUNT = "count"
    MAX = "max"
    MIN = "min"
    MEDIAN = "median"
    PERCENTILE = "percentile"
    RATE = "rate"
    WEIGHTED_AVERAGE = "weighted_average"


class MetricStatus(str, Enum):
    """Metric status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    CALCULATED = "calculated"


@dataclass
class MetricDefinition:
    """Metric definition"""
    metric_id: str
    name: str
    description: str
    metric_type: MetricType
    metric_scope: MetricScope
    aggregation_method: AggregationMethod
    unit: str
    source_metrics: List[str]
    calculation_formula: str
    thresholds: Dict[str, float]
    tags: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricValue:
    """Metric value with context"""
    metric_id: str
    value: Union[int, float]
    timestamp: datetime
    source_role: str
    source_service: str
    dimensions: Dict[str, str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AggregatedMetric:
    """Aggregated metric result"""
    metric_id: str
    aggregated_value: Union[int, float]
    aggregation_method: AggregationMethod
    aggregation_period: str
    source_count: int
    confidence_level: float
    timestamp: datetime
    dimensions: Dict[str, str]
    breakdown: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MetricSnapshot:
    """Point-in-time metrics snapshot"""
    snapshot_id: str
    timestamp: datetime
    scope: MetricScope
    metrics: List[AggregatedMetric]
    summary: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UnifiedMetrics:
    """
    Unified metrics aggregation service
    Aggregates SI and APP metrics for comprehensive analytics
    """
    
    def __init__(self):
        """Initialize unified metrics service"""
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.metric_definitions: Dict[str, MetricDefinition] = {}
        self.active_aggregations: Dict[str, Dict[str, Any]] = {}
        self.metric_cache: Dict[str, List[MetricValue]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_cache_size = 10000
        self.aggregation_interval = 60  # 1 minute
        
        # Initialize default metrics
        self._initialize_default_metrics()
    
    def _initialize_default_metrics(self):
        """Initialize default metric definitions"""
        default_metrics = [
            # Performance metrics
            MetricDefinition(
                metric_id="e2e_processing_time",
                name="End-to-End Processing Time",
                description="Total time from SI to APP processing",
                metric_type=MetricType.PERFORMANCE,
                metric_scope=MetricScope.CROSS_ROLE,
                aggregation_method=AggregationMethod.AVERAGE,
                unit="milliseconds",
                source_metrics=["si_processing_time", "app_processing_time"],
                calculation_formula="si_processing_time + app_processing_time",
                thresholds={"warning": 5000, "critical": 10000},
                tags=["performance", "cross_role", "latency"]
            ),
            
            # Throughput metrics
            MetricDefinition(
                metric_id="unified_throughput",
                name="Unified System Throughput",
                description="Combined SI and APP throughput",
                metric_type=MetricType.THROUGHPUT,
                metric_scope=MetricScope.SYSTEM_WIDE,
                aggregation_method=AggregationMethod.SUM,
                unit="requests_per_second",
                source_metrics=["si_throughput", "app_throughput"],
                calculation_formula="si_throughput + app_throughput",
                thresholds={"warning": 100, "critical": 50},
                tags=["throughput", "system", "capacity"]
            ),
            
            # Success rate metrics
            MetricDefinition(
                metric_id="cross_role_success_rate",
                name="Cross-Role Success Rate",
                description="Success rate across SI and APP",
                metric_type=MetricType.SUCCESS_RATE,
                metric_scope=MetricScope.CROSS_ROLE,
                aggregation_method=AggregationMethod.WEIGHTED_AVERAGE,
                unit="percentage",
                source_metrics=["si_success_rate", "app_success_rate"],
                calculation_formula="weighted_average(si_success_rate, app_success_rate)",
                thresholds={"warning": 95, "critical": 90},
                tags=["success", "quality", "cross_role"]
            ),
            
            # Compliance metrics
            MetricDefinition(
                metric_id="unified_compliance_score",
                name="Unified Compliance Score",
                description="Overall compliance score across roles",
                metric_type=MetricType.COMPLIANCE,
                metric_scope=MetricScope.SYSTEM_WIDE,
                aggregation_method=AggregationMethod.WEIGHTED_AVERAGE,
                unit="percentage",
                source_metrics=["si_compliance_score", "app_compliance_score"],
                calculation_formula="weighted_average(si_compliance_score, app_compliance_score)",
                thresholds={"warning": 85, "critical": 70},
                tags=["compliance", "regulatory", "quality"]
            )
        ]
        
        for metric_def in default_metrics:
            self.metric_definitions[metric_def.metric_id] = metric_def
    
    async def initialize(self):
        """Initialize the unified metrics service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing unified metrics service")
        
        try:
            # Initialize cache
            await self.cache.initialize()
            
            # Start periodic aggregation
            asyncio.create_task(self._periodic_aggregation())
            
            # Register event handlers
            await self._register_event_handlers()
            
            self.is_initialized = True
            self.logger.info("Unified metrics service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing unified metrics service: {str(e)}")
            raise
    
    async def register_metric_definition(self, metric_definition: MetricDefinition):
        """Register a new metric definition"""
        try:
            self.metric_definitions[metric_definition.metric_id] = metric_definition
            
            # Cache the definition
            await self.cache.set(
                f"metric_def:{metric_definition.metric_id}",
                metric_definition.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Registered metric definition: {metric_definition.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering metric definition: {str(e)}")
            raise
    
    async def record_metric_value(self, metric_value: MetricValue):
        """Record a metric value"""
        try:
            # Add to cache
            cache_key = f"metric_values:{metric_value.metric_id}"
            
            if cache_key not in self.metric_cache:
                self.metric_cache[cache_key] = []
            
            self.metric_cache[cache_key].append(metric_value)
            
            # Limit cache size
            if len(self.metric_cache[cache_key]) > self.max_cache_size:
                self.metric_cache[cache_key] = self.metric_cache[cache_key][-self.max_cache_size:]
            
            # Trigger aggregation if needed
            if len(self.metric_cache[cache_key]) % 100 == 0:
                await self._trigger_aggregation(metric_value.metric_id)
            
            self.logger.debug(f"Recorded metric value: {metric_value.metric_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording metric value: {str(e)}")
            raise
    
    async def aggregate_metrics(
        self,
        metric_ids: List[str],
        time_range: Tuple[datetime, datetime],
        aggregation_method: AggregationMethod = None,
        dimensions: Dict[str, str] = None
    ) -> List[AggregatedMetric]:
        """Aggregate metrics over time range"""
        try:
            aggregated_metrics = []
            
            for metric_id in metric_ids:
                if metric_id not in self.metric_definitions:
                    self.logger.warning(f"Metric definition not found: {metric_id}")
                    continue
                
                metric_def = self.metric_definitions[metric_id]
                method = aggregation_method or metric_def.aggregation_method
                
                # Get metric values from cache
                cache_key = f"metric_values:{metric_id}"
                metric_values = self.metric_cache.get(cache_key, [])
                
                # Filter by time range
                filtered_values = [
                    mv for mv in metric_values
                    if time_range[0] <= mv.timestamp <= time_range[1]
                ]
                
                # Filter by dimensions if provided
                if dimensions:
                    filtered_values = [
                        mv for mv in filtered_values
                        if all(mv.dimensions.get(k) == v for k, v in dimensions.items())
                    ]
                
                if not filtered_values:
                    continue
                
                # Aggregate values
                aggregated_value = await self._aggregate_values(
                    filtered_values,
                    method,
                    metric_def
                )
                
                # Create aggregated metric
                aggregated_metric = AggregatedMetric(
                    metric_id=metric_id,
                    aggregated_value=aggregated_value,
                    aggregation_method=method,
                    aggregation_period=f"{time_range[0].isoformat()}_{time_range[1].isoformat()}",
                    source_count=len(filtered_values),
                    confidence_level=min(1.0, len(filtered_values) / 100),
                    timestamp=datetime.now(timezone.utc),
                    dimensions=dimensions or {},
                    breakdown=await self._create_breakdown(filtered_values, metric_def),
                    metadata={
                        "time_range": {
                            "start": time_range[0].isoformat(),
                            "end": time_range[1].isoformat()
                        }
                    }
                )
                
                aggregated_metrics.append(aggregated_metric)
            
            return aggregated_metrics
            
        except Exception as e:
            self.logger.error(f"Error aggregating metrics: {str(e)}")
            raise
    
    async def get_real_time_metrics(
        self,
        metric_ids: List[str] = None,
        scope: MetricScope = None
    ) -> List[AggregatedMetric]:
        """Get real-time metrics"""
        try:
            # Filter metrics by scope if provided
            target_metrics = []
            
            if metric_ids:
                target_metrics = metric_ids
            else:
                target_metrics = list(self.metric_definitions.keys())
                
                if scope:
                    target_metrics = [
                        mid for mid in target_metrics
                        if self.metric_definitions[mid].metric_scope == scope
                    ]
            
            # Get recent time range (last 5 minutes)
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            # Aggregate metrics
            real_time_metrics = await self.aggregate_metrics(
                target_metrics,
                (start_time, end_time)
            )
            
            return real_time_metrics
            
        except Exception as e:
            self.logger.error(f"Error getting real-time metrics: {str(e)}")
            raise
    
    async def create_metric_snapshot(
        self,
        scope: MetricScope,
        include_breakdown: bool = True
    ) -> MetricSnapshot:
        """Create a comprehensive metric snapshot"""
        try:
            # Get metrics for scope
            scope_metrics = [
                mid for mid, mdef in self.metric_definitions.items()
                if mdef.metric_scope == scope
            ]
            
            # Get aggregated metrics
            aggregated_metrics = await self.get_real_time_metrics(scope_metrics, scope)
            
            # Create summary
            summary = {
                "total_metrics": len(aggregated_metrics),
                "metric_types": list(set(
                    self.metric_definitions[am.metric_id].metric_type
                    for am in aggregated_metrics
                )),
                "average_confidence": statistics.mean([
                    am.confidence_level for am in aggregated_metrics
                ]) if aggregated_metrics else 0,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Add breakdown if requested
            if include_breakdown:
                summary["breakdown_by_type"] = {}
                for metric_type in summary["metric_types"]:
                    type_metrics = [
                        am for am in aggregated_metrics
                        if self.metric_definitions[am.metric_id].metric_type == metric_type
                    ]
                    summary["breakdown_by_type"][metric_type] = {
                        "count": len(type_metrics),
                        "avg_value": statistics.mean([am.aggregated_value for am in type_metrics]) if type_metrics else 0
                    }
            
            # Create snapshot
            snapshot = MetricSnapshot(
                snapshot_id=str(uuid.uuid4()),
                timestamp=datetime.now(timezone.utc),
                scope=scope,
                metrics=aggregated_metrics,
                summary=summary,
                metadata={"include_breakdown": include_breakdown}
            )
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"Error creating metric snapshot: {str(e)}")
            raise
    
    async def get_metric_trends(
        self,
        metric_id: str,
        time_range: Tuple[datetime, datetime],
        granularity: str = "hour"
    ) -> List[AggregatedMetric]:
        """Get metric trends over time"""
        try:
            if metric_id not in self.metric_definitions:
                raise ValueError(f"Metric definition not found: {metric_id}")
            
            # Calculate time buckets
            time_buckets = await self._calculate_time_buckets(
                time_range[0],
                time_range[1],
                granularity
            )
            
            trends = []
            
            for bucket_start, bucket_end in time_buckets:
                bucket_metrics = await self.aggregate_metrics(
                    [metric_id],
                    (bucket_start, bucket_end)
                )
                
                if bucket_metrics:
                    trends.append(bucket_metrics[0])
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting metric trends: {str(e)}")
            raise
    
    async def compare_metrics(
        self,
        metric_id: str,
        time_periods: List[Tuple[datetime, datetime]],
        dimensions: Dict[str, str] = None
    ) -> Dict[str, AggregatedMetric]:
        """Compare metrics across time periods"""
        try:
            comparisons = {}
            
            for i, time_period in enumerate(time_periods):
                period_metrics = await self.aggregate_metrics(
                    [metric_id],
                    time_period,
                    dimensions=dimensions
                )
                
                if period_metrics:
                    comparisons[f"period_{i}"] = period_metrics[0]
            
            return comparisons
            
        except Exception as e:
            self.logger.error(f"Error comparing metrics: {str(e)}")
            raise
    
    async def _aggregate_values(
        self,
        values: List[MetricValue],
        method: AggregationMethod,
        metric_def: MetricDefinition
    ) -> Union[int, float]:
        """Aggregate metric values using specified method"""
        try:
            if not values:
                return 0
            
            numeric_values = [v.value for v in values]
            
            if method == AggregationMethod.SUM:
                return sum(numeric_values)
            elif method == AggregationMethod.AVERAGE:
                return statistics.mean(numeric_values)
            elif method == AggregationMethod.COUNT:
                return len(numeric_values)
            elif method == AggregationMethod.MAX:
                return max(numeric_values)
            elif method == AggregationMethod.MIN:
                return min(numeric_values)
            elif method == AggregationMethod.MEDIAN:
                return statistics.median(numeric_values)
            elif method == AggregationMethod.PERCENTILE:
                # Default to 95th percentile
                return statistics.quantiles(numeric_values, n=20)[18]
            elif method == AggregationMethod.RATE:
                # Calculate rate per second
                time_span = (values[-1].timestamp - values[0].timestamp).total_seconds()
                return len(values) / max(time_span, 1)
            elif method == AggregationMethod.WEIGHTED_AVERAGE:
                # Use source count as weight
                weights = [1] * len(values)  # Default equal weights
                return sum(v * w for v, w in zip(numeric_values, weights)) / sum(weights)
            else:
                return statistics.mean(numeric_values)
                
        except Exception as e:
            self.logger.error(f"Error aggregating values: {str(e)}")
            return 0
    
    async def _create_breakdown(
        self,
        values: List[MetricValue],
        metric_def: MetricDefinition
    ) -> Dict[str, Any]:
        """Create breakdown analysis of metric values"""
        try:
            breakdown = {
                "by_source_role": {},
                "by_source_service": {},
                "by_dimensions": {},
                "value_distribution": {}
            }
            
            # Breakdown by source role
            for value in values:
                role = value.source_role
                if role not in breakdown["by_source_role"]:
                    breakdown["by_source_role"][role] = []
                breakdown["by_source_role"][role].append(value.value)
            
            # Breakdown by source service
            for value in values:
                service = value.source_service
                if service not in breakdown["by_source_service"]:
                    breakdown["by_source_service"][service] = []
                breakdown["by_source_service"][service].append(value.value)
            
            # Breakdown by dimensions
            for value in values:
                for dim_key, dim_value in value.dimensions.items():
                    if dim_key not in breakdown["by_dimensions"]:
                        breakdown["by_dimensions"][dim_key] = {}
                    if dim_value not in breakdown["by_dimensions"][dim_key]:
                        breakdown["by_dimensions"][dim_key][dim_value] = []
                    breakdown["by_dimensions"][dim_key][dim_value].append(value.value)
            
            # Value distribution
            numeric_values = [v.value for v in values]
            if numeric_values:
                breakdown["value_distribution"] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": statistics.mean(numeric_values),
                    "median": statistics.median(numeric_values),
                    "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
                }
            
            return breakdown
            
        except Exception as e:
            self.logger.error(f"Error creating breakdown: {str(e)}")
            return {}
    
    async def _calculate_time_buckets(
        self,
        start_time: datetime,
        end_time: datetime,
        granularity: str
    ) -> List[Tuple[datetime, datetime]]:
        """Calculate time buckets for trend analysis"""
        try:
            buckets = []
            
            if granularity == "minute":
                delta = timedelta(minutes=1)
            elif granularity == "hour":
                delta = timedelta(hours=1)
            elif granularity == "day":
                delta = timedelta(days=1)
            else:
                delta = timedelta(hours=1)
            
            current = start_time
            while current < end_time:
                bucket_end = min(current + delta, end_time)
                buckets.append((current, bucket_end))
                current = bucket_end
            
            return buckets
            
        except Exception as e:
            self.logger.error(f"Error calculating time buckets: {str(e)}")
            return []
    
    async def _periodic_aggregation(self):
        """Periodic aggregation task"""
        while True:
            try:
                await asyncio.sleep(self.aggregation_interval)
                
                # Trigger aggregation for all metrics
                for metric_id in self.metric_definitions.keys():
                    await self._trigger_aggregation(metric_id)
                
            except Exception as e:
                self.logger.error(f"Error in periodic aggregation: {str(e)}")
    
    async def _trigger_aggregation(self, metric_id: str):
        """Trigger aggregation for a specific metric"""
        try:
            if metric_id not in self.active_aggregations:
                self.active_aggregations[metric_id] = {
                    "last_aggregated": datetime.now(timezone.utc),
                    "aggregation_count": 0
                }
            
            # Get recent metrics
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(minutes=5)
            
            aggregated_metrics = await self.aggregate_metrics(
                [metric_id],
                (start_time, end_time)
            )
            
            # Update aggregation info
            self.active_aggregations[metric_id]["last_aggregated"] = datetime.now(timezone.utc)
            self.active_aggregations[metric_id]["aggregation_count"] += 1
            
            # Cache results
            if aggregated_metrics:
                await self.cache.set(
                    f"aggregated_metric:{metric_id}",
                    aggregated_metrics[0].to_dict(),
                    ttl=self.cache_ttl
                )
            
        except Exception as e:
            self.logger.error(f"Error triggering aggregation: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers for metric updates"""
        try:
            await self.event_bus.subscribe(
                "metric.recorded",
                self._handle_metric_recorded
            )
            
            await self.event_bus.subscribe(
                "metric.threshold_exceeded",
                self._handle_threshold_exceeded
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_metric_recorded(self, event_data: Dict[str, Any]):
        """Handle metric recorded event"""
        try:
            metric_id = event_data.get("metric_id")
            if metric_id in self.metric_definitions:
                await self._trigger_aggregation(metric_id)
                
        except Exception as e:
            self.logger.error(f"Error handling metric recorded event: {str(e)}")
    
    async def _handle_threshold_exceeded(self, event_data: Dict[str, Any]):
        """Handle threshold exceeded event"""
        try:
            metric_id = event_data.get("metric_id")
            threshold_type = event_data.get("threshold_type")
            
            await self.notification_service.send_notification(
                type="metric_threshold_exceeded",
                data={
                    "metric_id": metric_id,
                    "threshold_type": threshold_type,
                    "current_value": event_data.get("current_value"),
                    "threshold_value": event_data.get("threshold_value")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error handling threshold exceeded event: {str(e)}")
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            return {
                "total_metrics_defined": len(self.metric_definitions),
                "metrics_by_type": {
                    metric_type: len([
                        m for m in self.metric_definitions.values()
                        if m.metric_type == metric_type
                    ])
                    for metric_type in MetricType
                },
                "metrics_by_scope": {
                    scope: len([
                        m for m in self.metric_definitions.values()
                        if m.metric_scope == scope
                    ])
                    for scope in MetricScope
                },
                "active_aggregations": len(self.active_aggregations),
                "cache_size": len(self.metric_cache),
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "unified_metrics",
                "components": {
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"},
                    "metrics_collector": {"status": "healthy"}
                },
                "metrics": {
                    "total_definitions": len(self.metric_definitions),
                    "active_aggregations": len(self.active_aggregations),
                    "cache_size": len(self.metric_cache)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "unified_metrics",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Unified metrics service cleanup initiated")
        
        try:
            # Clear caches
            self.metric_cache.clear()
            self.active_aggregations.clear()
            
            # Cleanup cache service
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Unified metrics service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_unified_metrics() -> UnifiedMetrics:
    """Create unified metrics service"""
    return UnifiedMetrics()