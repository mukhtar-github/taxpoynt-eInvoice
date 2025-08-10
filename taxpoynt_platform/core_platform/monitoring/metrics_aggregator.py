"""
Metrics Aggregator - Core Platform Observability

Aggregates and consolidates metrics from all platform components across SI, APP, and Hybrid services.
Provides centralized metrics collection, processing, and analysis for the entire TaxPoynt platform.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
from abc import ABC, abstractmethod
import json
import statistics

logger = logging.getLogger(__name__)


class ServiceRole(Enum):
    """Service role types for role-aware metrics aggregation"""
    SI_SERVICES = "si_services"
    APP_SERVICES = "app_services"
    HYBRID_SERVICES = "hybrid_services"
    CORE_PLATFORM = "core_platform"
    EXTERNAL_INTEGRATIONS = "external_integrations"


class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    DISTRIBUTION = "distribution"


class AggregationMethod(Enum):
    """Methods for aggregating metrics"""
    SUM = "sum"
    AVERAGE = "average"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    PERCENTILE = "percentile"
    RATE = "rate"


@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: Union[int, float]
    timestamp: datetime
    service_role: ServiceRole
    service_name: str
    metric_type: MetricType
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetric:
    """Aggregated metric result"""
    name: str
    aggregated_value: Union[int, float]
    aggregation_method: AggregationMethod
    service_role: Optional[ServiceRole]
    time_range: Dict[str, datetime]
    sample_count: int
    contributing_services: Set[str] = field(default_factory=set)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSource:
    """Configuration for a metric source"""
    service_name: str
    service_role: ServiceRole
    endpoint: Optional[str] = None
    collector_function: Optional[Callable] = None
    collection_interval: int = 60  # seconds
    enabled: bool = True


class MetricCollector(ABC):
    """Abstract base class for metric collectors"""
    
    @abstractmethod
    async def collect_metrics(self) -> List[MetricPoint]:
        """Collect metrics from a specific source"""
        pass


class MetricsAggregator:
    """
    Central metrics aggregation system for the TaxPoynt platform.
    
    Aggregates metrics from all platform components including:
    - SI Services (ERP integrations, certificate management, etc.)
    - APP Services (FIRS communication, taxpayer management, etc.)
    - Hybrid Services (analytics, billing, workflow orchestration, etc.)
    - Core Platform (authentication, data management, messaging, etc.)
    - External Integrations (business systems, regulatory systems, etc.)
    """
    
    def __init__(self, retention_hours: int = 168):  # 1 week default
        # Core data storage
        self.raw_metrics: deque = deque(maxlen=100000)  # Raw metric points
        self.aggregated_metrics: Dict[str, List[AggregatedMetric]] = defaultdict(list)
        self.retention_hours = retention_hours
        
        # Metric sources and collectors
        self.metric_sources: Dict[str, MetricSource] = {}
        self.collectors: Dict[str, MetricCollector] = {}
        
        # Aggregation configuration
        self.aggregation_rules: Dict[str, Dict[str, Any]] = {}
        self.default_aggregations = [
            AggregationMethod.SUM,
            AggregationMethod.AVERAGE,
            AggregationMethod.MAX,
            AggregationMethod.MIN
        ]
        
        # Performance tracking
        self.collection_stats = {
            "total_metrics_collected": 0,
            "collection_errors": 0,
            "last_collection": None,
            "collection_duration_ms": 0
        }
        
        # Event handlers
        self.metric_handlers: List[Callable] = []
        
        # Background tasks
        self._collection_task = None
        self._aggregation_task = None
        self._cleanup_task = None
        self._running = False
    
    # === Metric Source Management ===
    
    def register_metric_source(
        self,
        source_name: str,
        service_role: ServiceRole,
        service_name: str,
        collector: Optional[MetricCollector] = None,
        endpoint: Optional[str] = None,
        collection_interval: int = 60
    ) -> bool:
        """Register a new metric source"""
        try:
            source = MetricSource(
                service_name=service_name,
                service_role=service_role,
                endpoint=endpoint,
                collection_interval=collection_interval
            )
            
            self.metric_sources[source_name] = source
            
            if collector:
                self.collectors[source_name] = collector
            
            logger.info(f"Registered metric source: {source_name} ({service_role.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register metric source {source_name}: {e}")
            return False
    
    def unregister_metric_source(self, source_name: str) -> bool:
        """Unregister a metric source"""
        try:
            if source_name in self.metric_sources:
                del self.metric_sources[source_name]
            
            if source_name in self.collectors:
                del self.collectors[source_name]
            
            logger.info(f"Unregistered metric source: {source_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister metric source {source_name}: {e}")
            return False
    
    def get_metric_sources(self, service_role: Optional[ServiceRole] = None) -> List[MetricSource]:
        """Get registered metric sources, optionally filtered by role"""
        sources = list(self.metric_sources.values())
        
        if service_role:
            sources = [s for s in sources if s.service_role == service_role]
        
        return sources
    
    # === Metric Collection ===
    
    async def collect_metric_point(
        self,
        name: str,
        value: Union[int, float],
        service_role: ServiceRole,
        service_name: str,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Collect a single metric point"""
        try:
            metric_point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                service_role=service_role,
                service_name=service_name,
                metric_type=metric_type,
                tags=tags or {},
                metadata=metadata or {}
            )
            
            self.raw_metrics.append(metric_point)
            self.collection_stats["total_metrics_collected"] += 1
            
            # Notify handlers
            await self._notify_metric_handlers(metric_point)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to collect metric {name}: {e}")
            self.collection_stats["collection_errors"] += 1
            return False
    
    async def collect_metrics_batch(self, metrics: List[Dict[str, Any]]) -> int:
        """Collect multiple metrics in batch"""
        collected_count = 0
        
        for metric_data in metrics:
            try:
                success = await self.collect_metric_point(
                    name=metric_data["name"],
                    value=metric_data["value"],
                    service_role=ServiceRole(metric_data["service_role"]),
                    service_name=metric_data["service_name"],
                    metric_type=MetricType(metric_data.get("metric_type", "gauge")),
                    tags=metric_data.get("tags"),
                    metadata=metric_data.get("metadata")
                )
                
                if success:
                    collected_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to collect metric in batch: {e}")
                self.collection_stats["collection_errors"] += 1
        
        return collected_count
    
    async def collect_from_all_sources(self) -> Dict[str, int]:
        """Collect metrics from all registered sources"""
        collection_results = {}
        start_time = time.time()
        
        for source_name, collector in self.collectors.items():
            try:
                source = self.metric_sources[source_name]
                
                if not source.enabled:
                    continue
                
                metrics = await collector.collect_metrics()
                collection_results[source_name] = len(metrics)
                
                # Add metrics to storage
                for metric in metrics:
                    self.raw_metrics.append(metric)
                    self.collection_stats["total_metrics_collected"] += 1
                
                logger.debug(f"Collected {len(metrics)} metrics from {source_name}")
                
            except Exception as e:
                logger.error(f"Error collecting from {source_name}: {e}")
                self.collection_stats["collection_errors"] += 1
                collection_results[source_name] = 0
        
        # Update collection stats
        self.collection_stats["last_collection"] = datetime.utcnow()
        self.collection_stats["collection_duration_ms"] = int((time.time() - start_time) * 1000)
        
        return collection_results
    
    # === Metric Aggregation ===
    
    def aggregate_metrics(
        self,
        metric_name: str,
        time_range: Optional[Dict[str, datetime]] = None,
        service_role: Optional[ServiceRole] = None,
        service_names: Optional[List[str]] = None,
        aggregation_methods: Optional[List[AggregationMethod]] = None
    ) -> List[AggregatedMetric]:
        """Aggregate metrics based on specified criteria"""
        
        # Default time range (last hour)
        if not time_range:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            time_range = {"start": start_time, "end": end_time}
        
        # Filter metrics
        filtered_metrics = self._filter_metrics(
            metric_name=metric_name,
            time_range=time_range,
            service_role=service_role,
            service_names=service_names
        )
        
        if not filtered_metrics:
            return []
        
        # Apply aggregations
        aggregation_methods = aggregation_methods or self.default_aggregations
        aggregated_results = []
        
        for method in aggregation_methods:
            try:
                aggregated_value = self._apply_aggregation(filtered_metrics, method)
                contributing_services = {m.service_name for m in filtered_metrics}
                
                aggregated_metric = AggregatedMetric(
                    name=metric_name,
                    aggregated_value=aggregated_value,
                    aggregation_method=method,
                    service_role=service_role,
                    time_range=time_range,
                    sample_count=len(filtered_metrics),
                    contributing_services=contributing_services
                )
                
                aggregated_results.append(aggregated_metric)
                
            except Exception as e:
                logger.error(f"Error aggregating {metric_name} with {method}: {e}")
        
        # Cache results
        cache_key = f"{metric_name}_{service_role}_{time_range['start']}_{time_range['end']}"
        self.aggregated_metrics[cache_key] = aggregated_results
        
        return aggregated_results
    
    def get_platform_overview_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive platform metrics overview"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        time_range = {"start": start_time, "end": end_time}
        
        overview = {
            "time_range": time_range,
            "generated_at": end_time,
            "service_roles": {},
            "cross_platform": {},
            "performance_summary": {}
        }
        
        # Aggregate by service role
        for role in ServiceRole:
            role_metrics = self._get_role_metrics(role, time_range)
            overview["service_roles"][role.value] = role_metrics
        
        # Cross-platform aggregations
        overview["cross_platform"] = self._get_cross_platform_metrics(time_range)
        
        # Performance summary
        overview["performance_summary"] = self._get_performance_summary(time_range)
        
        return overview
    
    def get_service_metrics(
        self,
        service_name: str,
        hours: int = 24,
        metric_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get detailed metrics for a specific service"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        service_metrics = self._filter_metrics(
            time_range={"start": start_time, "end": end_time},
            service_names=[service_name]
        )
        
        if metric_names:
            service_metrics = [m for m in service_metrics if m.name in metric_names]
        
        # Group by metric name
        metrics_by_name = defaultdict(list)
        for metric in service_metrics:
            metrics_by_name[metric.name].append(metric)
        
        # Aggregate each metric
        aggregated_by_name = {}
        for name, metrics in metrics_by_name.items():
            aggregated_by_name[name] = {
                "count": len(metrics),
                "sum": sum(m.value for m in metrics),
                "average": statistics.mean(m.value for m in metrics),
                "min": min(m.value for m in metrics),
                "max": max(m.value for m in metrics),
                "latest": max(metrics, key=lambda m: m.timestamp).value,
                "trend": self._calculate_trend(metrics)
            }
        
        return {
            "service_name": service_name,
            "time_range": {"start": start_time, "end": end_time},
            "total_metrics": len(service_metrics),
            "unique_metric_names": len(metrics_by_name),
            "metrics": aggregated_by_name
        }
    
    def get_real_time_metrics(self, minutes: int = 5) -> Dict[str, Any]:
        """Get real-time metrics for the last N minutes"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        recent_metrics = self._filter_metrics(
            time_range={"start": start_time, "end": end_time}
        )
        
        # Group by service role and name
        by_role = defaultdict(lambda: defaultdict(list))
        for metric in recent_metrics:
            by_role[metric.service_role][metric.service_name].append(metric)
        
        real_time_data = {
            "time_range": {"start": start_time, "end": end_time},
            "total_metrics": len(recent_metrics),
            "services_reporting": len(set(m.service_name for m in recent_metrics)),
            "by_role": {},
            "top_metrics": self._get_top_metrics(recent_metrics, limit=10)
        }
        
        for role, services in by_role.items():
            real_time_data["by_role"][role.value] = {
                "service_count": len(services),
                "total_metrics": sum(len(metrics) for metrics in services.values()),
                "services": {
                    name: {
                        "metric_count": len(metrics),
                        "last_reported": max(m.timestamp for m in metrics)
                    }
                    for name, metrics in services.items()
                }
            }
        
        return real_time_data
    
    # === Analysis and Insights ===
    
    def analyze_metric_trends(
        self,
        metric_name: str,
        days: int = 7,
        service_role: Optional[ServiceRole] = None
    ) -> Dict[str, Any]:
        """Analyze trends for a specific metric over time"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get daily aggregations
        daily_data = []
        for day in range(days):
            day_start = start_time + timedelta(days=day)
            day_end = day_start + timedelta(days=1)
            
            day_metrics = self._filter_metrics(
                metric_name=metric_name,
                time_range={"start": day_start, "end": day_end},
                service_role=service_role
            )
            
            if day_metrics:
                daily_value = statistics.mean(m.value for m in day_metrics)
                daily_data.append({
                    "date": day_start.date(),
                    "value": daily_value,
                    "count": len(day_metrics)
                })
        
        if len(daily_data) < 2:
            return {"trend": "insufficient_data", "data": daily_data}
        
        # Calculate trend
        values = [d["value"] for d in daily_data]
        trend_direction = "stable"
        
        if values[-1] > values[0] * 1.1:
            trend_direction = "increasing"
        elif values[-1] < values[0] * 0.9:
            trend_direction = "decreasing"
        
        return {
            "metric_name": metric_name,
            "service_role": service_role.value if service_role else "all",
            "analysis_period_days": days,
            "trend_direction": trend_direction,
            "data_points": len(daily_data),
            "daily_data": daily_data,
            "summary": {
                "min_value": min(values),
                "max_value": max(values),
                "avg_value": statistics.mean(values),
                "change_percent": ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
            }
        }
    
    def detect_anomalies(
        self,
        metric_name: str,
        threshold_multiplier: float = 2.0,
        window_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in metric values"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=window_hours)
        
        metrics = self._filter_metrics(
            metric_name=metric_name,
            time_range={"start": start_time, "end": end_time}
        )
        
        if len(metrics) < 10:  # Need sufficient data
            return []
        
        values = [m.value for m in metrics]
        mean_value = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        threshold = std_dev * threshold_multiplier
        anomalies = []
        
        for metric in metrics:
            if abs(metric.value - mean_value) > threshold:
                anomalies.append({
                    "timestamp": metric.timestamp,
                    "value": metric.value,
                    "expected_range": {
                        "min": mean_value - threshold,
                        "max": mean_value + threshold
                    },
                    "deviation": abs(metric.value - mean_value),
                    "service_name": metric.service_name,
                    "service_role": metric.service_role.value
                })
        
        return sorted(anomalies, key=lambda x: x["deviation"], reverse=True)
    
    # === Utility Methods ===
    
    def _filter_metrics(
        self,
        metric_name: Optional[str] = None,
        time_range: Optional[Dict[str, datetime]] = None,
        service_role: Optional[ServiceRole] = None,
        service_names: Optional[List[str]] = None
    ) -> List[MetricPoint]:
        """Filter metrics based on criteria"""
        filtered = list(self.raw_metrics)
        
        if metric_name:
            filtered = [m for m in filtered if m.name == metric_name]
        
        if time_range:
            start_time = time_range["start"]
            end_time = time_range["end"]
            filtered = [m for m in filtered if start_time <= m.timestamp <= end_time]
        
        if service_role:
            filtered = [m for m in filtered if m.service_role == service_role]
        
        if service_names:
            filtered = [m for m in filtered if m.service_name in service_names]
        
        return filtered
    
    def _apply_aggregation(self, metrics: List[MetricPoint], method: AggregationMethod) -> float:
        """Apply aggregation method to metrics"""
        values = [m.value for m in metrics]
        
        if method == AggregationMethod.SUM:
            return sum(values)
        elif method == AggregationMethod.AVERAGE:
            return statistics.mean(values)
        elif method == AggregationMethod.MIN:
            return min(values)
        elif method == AggregationMethod.MAX:
            return max(values)
        elif method == AggregationMethod.COUNT:
            return len(values)
        else:
            return statistics.mean(values)  # Default to average
    
    def _get_role_metrics(self, role: ServiceRole, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Get aggregated metrics for a service role"""
        role_metrics = self._filter_metrics(
            time_range=time_range,
            service_role=role
        )
        
        if not role_metrics:
            return {"metric_count": 0, "services": []}
        
        services = set(m.service_name for m in role_metrics)
        metric_names = set(m.name for m in role_metrics)
        
        return {
            "metric_count": len(role_metrics),
            "unique_services": len(services),
            "unique_metrics": len(metric_names),
            "services": list(services),
            "metric_names": list(metric_names),
            "avg_value": statistics.mean(m.value for m in role_metrics),
            "last_reported": max(m.timestamp for m in role_metrics)
        }
    
    def _get_cross_platform_metrics(self, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Get cross-platform aggregated metrics"""
        all_metrics = self._filter_metrics(time_range=time_range)
        
        if not all_metrics:
            return {}
        
        return {
            "total_metrics": len(all_metrics),
            "reporting_services": len(set(m.service_name for m in all_metrics)),
            "metric_types": {
                metric_type.value: len([m for m in all_metrics if m.metric_type == metric_type])
                for metric_type in MetricType
            },
            "service_role_distribution": {
                role.value: len([m for m in all_metrics if m.service_role == role])
                for role in ServiceRole
            }
        }
    
    def _get_performance_summary(self, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """Get performance summary metrics"""
        performance_metrics = self._filter_metrics(
            time_range=time_range
        )
        
        # Look for common performance metric patterns
        response_time_metrics = [m for m in performance_metrics if "response_time" in m.name.lower()]
        error_rate_metrics = [m for m in performance_metrics if "error" in m.name.lower()]
        throughput_metrics = [m for m in performance_metrics if any(term in m.name.lower() for term in ["throughput", "requests", "transactions"])]
        
        summary = {
            "response_times": {
                "count": len(response_time_metrics),
                "avg": statistics.mean(m.value for m in response_time_metrics) if response_time_metrics else 0
            },
            "error_rates": {
                "count": len(error_rate_metrics),
                "avg": statistics.mean(m.value for m in error_rate_metrics) if error_rate_metrics else 0
            },
            "throughput": {
                "count": len(throughput_metrics),
                "total": sum(m.value for m in throughput_metrics) if throughput_metrics else 0
            }
        }
        
        return summary
    
    def _get_top_metrics(self, metrics: List[MetricPoint], limit: int = 10) -> List[Dict[str, Any]]:
        """Get top metrics by value"""
        sorted_metrics = sorted(metrics, key=lambda m: m.value, reverse=True)
        
        return [
            {
                "name": m.name,
                "value": m.value,
                "service": m.service_name,
                "role": m.service_role.value,
                "timestamp": m.timestamp
            }
            for m in sorted_metrics[:limit]
        ]
    
    def _calculate_trend(self, metrics: List[MetricPoint]) -> str:
        """Calculate trend direction for metrics"""
        if len(metrics) < 2:
            return "stable"
        
        # Sort by timestamp
        sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
        first_half = sorted_metrics[:len(sorted_metrics)//2]
        second_half = sorted_metrics[len(sorted_metrics)//2:]
        
        first_avg = statistics.mean(m.value for m in first_half)
        second_avg = statistics.mean(m.value for m in second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    async def _notify_metric_handlers(self, metric: MetricPoint):
        """Notify registered metric handlers"""
        for handler in self.metric_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(metric)
                else:
                    handler(metric)
            except Exception as e:
                logger.error(f"Error in metric handler: {e}")
    
    # === Background Tasks ===
    
    async def start_background_tasks(self):
        """Start background collection and aggregation tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start collection task
        self._collection_task = asyncio.create_task(self._background_collection())
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._background_cleanup())
        
        logger.info("Started metrics aggregator background tasks")
    
    async def stop_background_tasks(self):
        """Stop background tasks"""
        self._running = False
        
        if self._collection_task:
            self._collection_task.cancel()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        logger.info("Stopped metrics aggregator background tasks")
    
    async def _background_collection(self):
        """Background task for periodic metric collection"""
        while self._running:
            try:
                await self.collect_from_all_sources()
                await asyncio.sleep(60)  # Collect every minute
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background collection: {e}")
                await asyncio.sleep(60)
    
    async def _background_cleanup(self):
        """Background task for cleaning up old metrics"""
        while self._running:
            try:
                await self._cleanup_old_metrics()
                await asyncio.sleep(3600)  # Cleanup every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
                await asyncio.sleep(3600)
    
    async def _cleanup_old_metrics(self):
        """Clean up metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        # Clean raw metrics (automatically handled by deque maxlen)
        original_count = len(self.raw_metrics)
        
        # Clean aggregated metrics cache
        cache_keys_to_remove = []
        for cache_key, aggregated_list in self.aggregated_metrics.items():
            # Remove old aggregated metrics
            self.aggregated_metrics[cache_key] = [
                agg for agg in aggregated_list
                if agg.time_range["end"] >= cutoff_time
            ]
            
            # Remove empty cache entries
            if not self.aggregated_metrics[cache_key]:
                cache_keys_to_remove.append(cache_key)
        
        for cache_key in cache_keys_to_remove:
            del self.aggregated_metrics[cache_key]
        
        logger.debug(f"Cleaned up metrics. Raw metrics: {original_count} -> {len(self.raw_metrics)}")
    
    # === Health and Status ===
    
    def get_aggregator_health(self) -> Dict[str, Any]:
        """Get health status of the metrics aggregator"""
        return {
            "status": "healthy" if self._running else "stopped",
            "raw_metrics_count": len(self.raw_metrics),
            "aggregated_cache_size": len(self.aggregated_metrics),
            "registered_sources": len(self.metric_sources),
            "active_collectors": len(self.collectors),
            "collection_stats": self.collection_stats.copy(),
            "retention_hours": self.retention_hours,
            "background_tasks_running": self._running
        }
    
    def add_metric_handler(self, handler: Callable):
        """Add a metric event handler"""
        self.metric_handlers.append(handler)
    
    def remove_metric_handler(self, handler: Callable):
        """Remove a metric event handler"""
        if handler in self.metric_handlers:
            self.metric_handlers.remove(handler)


# Convenience collector implementations for existing components
class SIMetricsCollector(MetricCollector):
    """Collector for SI Services metrics"""
    
    def __init__(self, metrics_collector_instance=None):
        # Reference to existing si_services metrics_collector
        self.si_metrics_collector = metrics_collector_instance
    
    async def collect_metrics(self) -> List[MetricPoint]:
        """Collect metrics from SI services"""
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            if self.si_metrics_collector:
                # Get system-wide metrics from existing collector
                system_metrics = self.si_metrics_collector.get_system_wide_metrics()
                
                # Convert to MetricPoint format
                overview = system_metrics.get("overview", {})
                for key, value in overview.items():
                    if isinstance(value, (int, float)):
                        metric = MetricPoint(
                            name=f"si_system_{key}",
                            value=value,
                            timestamp=timestamp,
                            service_role=ServiceRole.SI_SERVICES,
                            service_name="si_integration_management",
                            metric_type=MetricType.GAUGE
                        )
                        metrics.append(metric)
        
        except Exception as e:
            logger.error(f"Error collecting SI metrics: {e}")
        
        return metrics


class HealthMonitorCollector(MetricCollector):
    """Collector for health monitoring metrics"""
    
    def __init__(self, health_monitor_instance=None):
        self.health_monitor = health_monitor_instance
    
    async def collect_metrics(self) -> List[MetricPoint]:
        """Collect health monitoring metrics"""
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            if self.health_monitor:
                # Get all monitored integrations
                monitored = self.health_monitor.get_all_monitored_integrations()
                
                # Create health metrics
                for integration in monitored:
                    status_value = 1 if integration["status"] == "active" else 0
                    
                    metric = MetricPoint(
                        name="integration_health_status",
                        value=status_value,
                        timestamp=timestamp,
                        service_role=ServiceRole.SI_SERVICES,
                        service_name="integration_health_monitor",
                        metric_type=MetricType.GAUGE,
                        tags={"integration_id": integration["integration_id"]}
                    )
                    metrics.append(metric)
        
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
        
        return metrics


# Global instance for platform-wide access
metrics_aggregator = MetricsAggregator()


# Integration functions for easy setup
async def setup_metrics_aggregation():
    """Setup default metric sources and collectors"""
    
    # Register core platform sources
    metrics_aggregator.register_metric_source(
        "core_authentication",
        ServiceRole.CORE_PLATFORM,
        "authentication_service"
    )
    
    metrics_aggregator.register_metric_source(
        "core_messaging",
        ServiceRole.CORE_PLATFORM,
        "messaging_service"
    )
    
    # Register SI services sources
    metrics_aggregator.register_metric_source(
        "si_integration_management",
        ServiceRole.SI_SERVICES,
        "integration_management"
    )
    
    # Register APP services sources
    metrics_aggregator.register_metric_source(
        "app_firs_communication",
        ServiceRole.APP_SERVICES,
        "firs_communication"
    )
    
    # Register hybrid services sources
    metrics_aggregator.register_metric_source(
        "hybrid_analytics",
        ServiceRole.HYBRID_SERVICES,
        "analytics_aggregation"
    )
    
    # Start background tasks
    await metrics_aggregator.start_background_tasks()
    
    logger.info("Metrics aggregation setup completed")


async def shutdown_metrics_aggregation():
    """Shutdown metrics aggregation"""
    await metrics_aggregator.stop_background_tasks()
    logger.info("Metrics aggregation shutdown completed")