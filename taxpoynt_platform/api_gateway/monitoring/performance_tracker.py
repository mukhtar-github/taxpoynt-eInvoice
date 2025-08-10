"""
API Performance Tracker by Role
===============================
Advanced performance monitoring and analysis for role-based API endpoints in TaxPoynt platform.
Tracks response times, throughput, resource utilization, and performance trends across SI, APP, and HYBRID roles.
"""
import uuid
import logging
import asyncio
import statistics
import psutil
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, DefaultDict, NamedTuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import threading
from concurrent.futures import ThreadPoolExecutor

from ..role_routing.models import HTTPRoutingContext, PlatformRole, RouteType, HTTPMethod
from .role_metrics import TimeWindow, RoleMetricsCollector
from ...core_platform.authentication.role_manager import ServiceRole

logger = logging.getLogger(__name__)


class PerformanceMetric(Enum):
    """Types of performance metrics to track."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    NETWORK_IO = "network_io"
    DISK_IO = "disk_io"
    CONNECTION_COUNT = "connection_count"
    QUEUE_LENGTH = "queue_length"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class PerformanceTrend(Enum):
    """Performance trend directions."""
    IMPROVING = "improving"
    DEGRADING = "degrading"
    STABLE = "stable"
    VOLATILE = "volatile"


@dataclass
class PerformanceDataPoint:
    """Single performance measurement."""
    measurement_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    role: PlatformRole
    route_type: RouteType
    endpoint: str
    
    # Performance measurements
    response_time_ms: float = 0.0
    throughput_rps: float = 0.0  # requests per second
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    network_in_bytes: int = 0
    network_out_bytes: int = 0
    disk_read_bytes: int = 0
    disk_write_bytes: int = 0
    active_connections: int = 0
    queue_length: int = 0
    
    # Context information
    concurrent_requests: int = 0
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    error_occurred: bool = False
    status_code: Optional[int] = None
    
    # System state
    system_load: float = 0.0
    available_memory_mb: float = 0.0
    cpu_cores: int = 0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration."""
    threshold_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: PlatformRole
    route_type: RouteType
    metric_type: PerformanceMetric
    
    # Threshold values
    warning_threshold: float = 0.0
    critical_threshold: float = 0.0
    
    # Evaluation configuration
    evaluation_window_minutes: int = 5
    consecutive_violations: int = 3
    enabled: bool = True
    
    # Alert configuration
    alert_severity: AlertSeverity = AlertSeverity.MEDIUM
    notification_channels: List[str] = field(default_factory=list)
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PerformanceAlert:
    """Performance alert notification."""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Alert details
    threshold: PerformanceThreshold
    current_value: float
    severity: AlertSeverity
    
    # Context
    affected_role: PlatformRole
    affected_endpoints: List[str] = field(default_factory=list)
    duration_minutes: float = 0.0
    
    # Status
    active: bool = True
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Additional data
    related_metrics: Dict[str, float] = field(default_factory=dict)
    suggested_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceSummary:
    """Performance summary for a role and time period."""
    role: PlatformRole
    route_type: RouteType
    time_window: TimeWindow
    window_start: datetime
    window_end: datetime
    
    # Response time statistics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p90_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    response_time_std_dev: float = 0.0
    
    # Throughput statistics
    avg_throughput_rps: float = 0.0
    peak_throughput_rps: float = 0.0
    min_throughput_rps: float = 0.0
    total_requests: int = 0
    
    # Resource utilization
    avg_cpu_usage: float = 0.0
    peak_cpu_usage: float = 0.0
    avg_memory_usage_mb: float = 0.0
    peak_memory_usage_mb: float = 0.0
    
    # Network performance
    total_network_in_mb: float = 0.0
    total_network_out_mb: float = 0.0
    avg_network_throughput_mbps: float = 0.0
    
    # Error analysis
    error_rate_percent: float = 0.0
    total_errors: int = 0
    availability_percent: float = 100.0
    
    # Performance trends
    response_time_trend: PerformanceTrend = PerformanceTrend.STABLE
    throughput_trend: PerformanceTrend = PerformanceTrend.STABLE
    error_rate_trend: PerformanceTrend = PerformanceTrend.STABLE
    
    # Top performance issues
    slowest_endpoints: List[Tuple[str, float]] = field(default_factory=list)
    highest_error_endpoints: List[Tuple[str, float]] = field(default_factory=list)
    resource_bottlenecks: List[str] = field(default_factory=list)


class PerformanceTracker:
    """
    API Performance Tracker by Role
    ===============================
    
    **Core Capabilities:**
    - Real-time performance monitoring per role (SI, APP, HYBRID)
    - Response time analysis with percentiles and trends
    - Throughput tracking and capacity planning
    - Resource utilization monitoring (CPU, Memory, Network, Disk)
    - Performance threshold management and alerting
    - Automated performance degradation detection
    - Comparative performance analysis across roles
    
    **Advanced Features:**
    - Predictive performance analytics
    - Performance bottleneck identification
    - Capacity planning recommendations
    - Performance regression detection
    - Custom performance metrics and dashboards
    """
    
    def __init__(
        self,
        metrics_collector: Optional[RoleMetricsCollector] = None,
        enable_system_monitoring: bool = True,
        enable_predictive_analysis: bool = False,
        monitoring_interval_seconds: int = 30,
        max_data_points: int = 50000,
        enable_alerting: bool = True
    ):
        self.logger = logging.getLogger(__name__)
        
        # Dependencies
        self.metrics_collector = metrics_collector
        
        # Configuration
        self.enable_system_monitoring = enable_system_monitoring
        self.enable_predictive_analysis = enable_predictive_analysis
        self.monitoring_interval_seconds = monitoring_interval_seconds
        self.max_data_points = max_data_points
        self.enable_alerting = enable_alerting
        
        # Performance data storage
        self.performance_data: DefaultDict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.max_data_points)
        )
        self.performance_summaries: Dict[str, PerformanceSummary] = {}
        
        # Threshold management
        self.performance_thresholds: Dict[str, PerformanceThreshold] = {}
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        
        # Real-time tracking
        self.active_requests: Dict[str, Dict[str, Any]] = {}
        self.endpoint_performance: DefaultDict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        
        # System monitoring
        self.system_stats: Dict[str, Any] = {}
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_stop_event = threading.Event()
        
        # Performance analysis
        self.trend_analyzer = PerformanceTrendAnalyzer()
        self.bottleneck_detector = PerformanceBottleneckDetector()
        
        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="perf_tracker")
        
        # Initialize default thresholds
        self._initialize_default_thresholds()
        
        # Start system monitoring if enabled
        if self.enable_system_monitoring:
            self._start_system_monitoring()
        
        logger.info("PerformanceTracker initialized")
    
    async def track_request_performance(
        self,
        request_id: str,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        method: HTTPMethod,
        route_type: RouteType
    ):
        """Start tracking performance for a request."""
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc)
        
        # Get current system stats
        system_stats = self._get_current_system_stats() if self.enable_system_monitoring else {}
        
        # Store request tracking data
        self.active_requests[request_id] = {
            "start_time": start_time,
            "start_timestamp": start_timestamp,
            "routing_context": routing_context,
            "endpoint": endpoint,
            "method": method,
            "route_type": route_type,
            "system_stats_start": system_stats,
            "concurrent_requests": len(self.active_requests)
        }
        
        # Log start if detailed logging enabled
        self.logger.debug(f"Started tracking performance for request {request_id}")
    
    async def complete_request_performance(
        self,
        request_id: str,
        status_code: int,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        error_occurred: bool = False
    ):
        """Complete performance tracking for a request."""
        if request_id not in self.active_requests:
            self.logger.warning(f"Unknown request ID for performance tracking: {request_id}")
            return
        
        request_data = self.active_requests[request_id]
        end_time = time.time()
        end_timestamp = datetime.now(timezone.utc)
        
        # Calculate response time
        response_time_ms = (end_time - request_data["start_time"]) * 1000
        
        # Get current system stats
        system_stats_end = self._get_current_system_stats() if self.enable_system_monitoring else {}
        
        # Create performance data point
        data_point = PerformanceDataPoint(
            timestamp=end_timestamp,
            role=request_data["routing_context"].platform_role or PlatformRole.USER,
            route_type=request_data["route_type"],
            endpoint=request_data["endpoint"],
            response_time_ms=response_time_ms,
            throughput_rps=self._calculate_current_throughput(request_data["routing_context"].platform_role),
            cpu_usage_percent=system_stats_end.get("cpu_percent", 0.0),
            memory_usage_mb=system_stats_end.get("memory_mb", 0.0),
            network_in_bytes=system_stats_end.get("network_in", 0),
            network_out_bytes=system_stats_end.get("network_out", 0),
            concurrent_requests=request_data["concurrent_requests"],
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            error_occurred=error_occurred,
            status_code=status_code,
            system_load=system_stats_end.get("load_avg", 0.0),
            available_memory_mb=system_stats_end.get("available_memory_mb", 0.0),
            cpu_cores=system_stats_end.get("cpu_cores", 1)
        )
        
        # Store performance data
        await self._store_performance_data(data_point)
        
        # Update endpoint-specific performance tracking
        endpoint_key = f"{data_point.role.value}:{data_point.endpoint}"
        self.endpoint_performance[endpoint_key].append({
            "timestamp": end_timestamp,
            "response_time_ms": response_time_ms,
            "error": error_occurred,
            "status_code": status_code
        })
        
        # Check performance thresholds
        if self.enable_alerting:
            await self._check_performance_thresholds(data_point)
        
        # Clean up request tracking
        del self.active_requests[request_id]
        
        self.logger.debug(f"Completed performance tracking for request {request_id}: {response_time_ms:.2f}ms")
    
    async def get_performance_summary(
        self,
        role: PlatformRole,
        route_type: Optional[RouteType] = None,
        time_window: TimeWindow = TimeWindow.HOUR,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PerformanceSummary:
        """Get performance summary for a role and time period."""
        
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            start_time = end_time - self._get_timedelta_for_window(time_window)
        
        # Generate cache key
        cache_key = f"{role.value}:{route_type.value if route_type else 'all'}:{time_window.value}:{start_time.isoformat()}"
        
        # Check cache
        if cache_key in self.performance_summaries:
            cached_summary = self.performance_summaries[cache_key]
            # Return cached if recent (within 5 minutes)
            if (datetime.now(timezone.utc) - cached_summary.window_end).total_seconds() < 300:
                return cached_summary
        
        # Collect relevant data points
        data_points = await self._collect_performance_data(
            role=role,
            route_type=route_type,
            start_time=start_time,
            end_time=end_time
        )
        
        # Generate summary
        summary = await self._generate_performance_summary(
            role=role,
            route_type=route_type or RouteType.PUBLIC,
            time_window=time_window,
            window_start=start_time,
            window_end=end_time,
            data_points=data_points
        )
        
        # Cache summary
        self.performance_summaries[cache_key] = summary
        
        return summary
    
    async def get_comparative_performance(
        self,
        roles: List[PlatformRole],
        time_window: TimeWindow = TimeWindow.HOUR
    ) -> Dict[PlatformRole, PerformanceSummary]:
        """Get comparative performance across multiple roles."""
        results = {}
        
        # Use thread pool for parallel processing
        tasks = []
        for role in roles:
            task = asyncio.create_task(
                self.get_performance_summary(role=role, time_window=time_window)
            )
            tasks.append((role, task))
        
        # Collect results
        for role, task in tasks:
            try:
                results[role] = await task
            except Exception as e:
                self.logger.error(f"Failed to get performance summary for role {role.value}: {str(e)}")
                # Create empty summary for failed role
                results[role] = PerformanceSummary(
                    role=role,
                    route_type=RouteType.PUBLIC,
                    time_window=time_window,
                    window_start=datetime.now(timezone.utc) - self._get_timedelta_for_window(time_window),
                    window_end=datetime.now(timezone.utc)
                )
        
        return results
    
    async def get_performance_trends(
        self,
        role: PlatformRole,
        metric_type: PerformanceMetric,
        time_window: TimeWindow = TimeWindow.DAY,
        trend_periods: int = 7
    ) -> Dict[str, Any]:
        """Analyze performance trends over multiple time periods."""
        trends_data = []
        end_time = datetime.now(timezone.utc)
        window_delta = self._get_timedelta_for_window(time_window)
        
        # Collect data for multiple periods
        for i in range(trend_periods):
            period_end = end_time - (window_delta * i)
            period_start = period_end - window_delta
            
            data_points = await self._collect_performance_data(
                role=role,
                start_time=period_start,
                end_time=period_end
            )
            
            # Calculate average for the metric
            metric_values = self._extract_metric_values(data_points, metric_type)
            avg_value = statistics.mean(metric_values) if metric_values else 0.0
            
            trends_data.append({
                "period": i,
                "start_time": period_start.isoformat(),
                "end_time": period_end.isoformat(),
                "avg_value": avg_value,
                "data_points": len(metric_values)
            })
        
        # Analyze trend direction
        values = [period["avg_value"] for period in trends_data if period["avg_value"] > 0]
        trend_direction = self.trend_analyzer.analyze_trend(values)
        
        return {
            "role": role.value,
            "metric_type": metric_type.value,
            "time_window": time_window.value,
            "trend_periods": trend_periods,
            "trend_direction": trend_direction.value,
            "periods_data": list(reversed(trends_data)),  # Most recent first
            "analysis": {
                "improvement_rate": self.trend_analyzer.calculate_improvement_rate(values),
                "volatility": self.trend_analyzer.calculate_volatility(values),
                "prediction": self.trend_analyzer.predict_next_value(values) if self.enable_predictive_analysis else None
            }
        }
    
    async def detect_performance_bottlenecks(
        self,
        role: PlatformRole,
        time_window: TimeWindow = TimeWindow.HOUR
    ) -> Dict[str, Any]:
        """Detect performance bottlenecks for a role."""
        summary = await self.get_performance_summary(role=role, time_window=time_window)
        
        bottlenecks = self.bottleneck_detector.detect_bottlenecks(summary)
        
        return {
            "role": role.value,
            "time_window": time_window.value,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "bottlenecks": bottlenecks,
            "recommendations": self._generate_performance_recommendations(bottlenecks, summary),
            "severity": self._assess_bottleneck_severity(bottlenecks)
        }
    
    async def set_performance_threshold(
        self,
        role: PlatformRole,
        route_type: RouteType,
        metric_type: PerformanceMetric,
        warning_threshold: float,
        critical_threshold: float,
        **kwargs
    ) -> str:
        """Set a performance threshold for monitoring."""
        threshold = PerformanceThreshold(
            role=role,
            route_type=route_type,
            metric_type=metric_type,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            **kwargs
        )
        
        threshold_key = f"{role.value}:{route_type.value}:{metric_type.value}"
        self.performance_thresholds[threshold_key] = threshold
        
        self.logger.info(f"Set performance threshold: {threshold_key}")
        return threshold.threshold_id
    
    async def get_active_alerts(
        self,
        role: Optional[PlatformRole] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[PerformanceAlert]:
        """Get active performance alerts."""
        alerts = []
        
        for alert in self.active_alerts.values():
            if alert.active and not alert.resolved:
                # Filter by role if specified
                if role and alert.affected_role != role:
                    continue
                
                # Filter by severity if specified
                if severity and alert.severity != severity:
                    continue
                
                alerts.append(alert)
        
        # Sort by severity and timestamp
        severity_order = {
            AlertSeverity.CRITICAL: 0,
            AlertSeverity.HIGH: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.LOW: 3,
            AlertSeverity.INFO: 4
        }
        
        alerts.sort(key=lambda a: (severity_order[a.severity], a.timestamp), reverse=True)
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge a performance alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.metadata["acknowledged_by"] = acknowledged_by
            alert.metadata["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
            
            self.logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
        
        return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve a performance alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            alert.metadata["resolved_by"] = resolved_by
            
            # Move to history
            self.alert_history.append(alert)
            
            self.logger.info(f"Alert {alert_id} resolved by {resolved_by}")
            return True
        
        return False
    
    def _initialize_default_thresholds(self):
        """Initialize default performance thresholds."""
        default_thresholds = [
            # Response time thresholds
            {
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": PerformanceMetric.RESPONSE_TIME,
                "warning_threshold": 1000.0,  # 1 second
                "critical_threshold": 5000.0,  # 5 seconds
                "description": "SI API response time threshold"
            },
            {
                "role": PlatformRole.ACCESS_POINT_PROVIDER,
                "route_type": RouteType.APP_ONLY,
                "metric_type": PerformanceMetric.RESPONSE_TIME,
                "warning_threshold": 500.0,  # 500ms
                "critical_threshold": 2000.0,  # 2 seconds
                "description": "APP API response time threshold"
            },
            {
                "role": PlatformRole.HYBRID,
                "route_type": RouteType.HYBRID,
                "metric_type": PerformanceMetric.RESPONSE_TIME,
                "warning_threshold": 750.0,  # 750ms
                "critical_threshold": 3000.0,  # 3 seconds
                "description": "Hybrid API response time threshold"
            },
            # Error rate thresholds
            {
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": PerformanceMetric.ERROR_RATE,
                "warning_threshold": 5.0,  # 5%
                "critical_threshold": 10.0,  # 10%
                "description": "SI API error rate threshold"
            },
            # CPU usage thresholds
            {
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": PerformanceMetric.CPU_USAGE,
                "warning_threshold": 70.0,  # 70%
                "critical_threshold": 90.0,  # 90%
                "description": "CPU usage threshold for SI operations"
            }
        ]
        
        for threshold_config in default_thresholds:
            asyncio.create_task(self.set_performance_threshold(**threshold_config))
    
    async def _store_performance_data(self, data_point: PerformanceDataPoint):
        """Store performance data point."""
        role_key = data_point.role.value
        self.performance_data[role_key].append(data_point)
    
    async def _collect_performance_data(
        self,
        role: PlatformRole,
        route_type: Optional[RouteType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceDataPoint]:
        """Collect performance data points for analysis."""
        role_key = role.value
        data_points = []
        
        if role_key in self.performance_data:
            for point in self.performance_data[role_key]:
                # Time filter
                if start_time and point.timestamp < start_time:
                    continue
                if end_time and point.timestamp > end_time:
                    continue
                
                # Route type filter
                if route_type and point.route_type != route_type:
                    continue
                
                data_points.append(point)
        
        return data_points
    
    async def _generate_performance_summary(
        self,
        role: PlatformRole,
        route_type: RouteType,
        time_window: TimeWindow,
        window_start: datetime,
        window_end: datetime,
        data_points: List[PerformanceDataPoint]
    ) -> PerformanceSummary:
        """Generate performance summary from data points."""
        summary = PerformanceSummary(
            role=role,
            route_type=route_type,
            time_window=time_window,
            window_start=window_start,
            window_end=window_end
        )
        
        if not data_points:
            return summary
        
        # Response time analysis
        response_times = [p.response_time_ms for p in data_points if p.response_time_ms > 0]
        if response_times:
            response_times.sort()
            summary.avg_response_time_ms = statistics.mean(response_times)
            summary.min_response_time_ms = min(response_times)
            summary.max_response_time_ms = max(response_times)
            summary.p50_response_time_ms = self._percentile(response_times, 50)
            summary.p90_response_time_ms = self._percentile(response_times, 90)
            summary.p95_response_time_ms = self._percentile(response_times, 95)
            summary.p99_response_time_ms = self._percentile(response_times, 99)
            summary.response_time_std_dev = statistics.stdev(response_times) if len(response_times) > 1 else 0.0
        
        # Throughput analysis
        throughput_values = [p.throughput_rps for p in data_points if p.throughput_rps > 0]
        if throughput_values:
            summary.avg_throughput_rps = statistics.mean(throughput_values)
            summary.peak_throughput_rps = max(throughput_values)
            summary.min_throughput_rps = min(throughput_values)
        
        # Request counts
        summary.total_requests = len(data_points)
        error_count = sum(1 for p in data_points if p.error_occurred)
        summary.total_errors = error_count
        summary.error_rate_percent = (error_count / len(data_points) * 100) if data_points else 0
        summary.availability_percent = 100 - summary.error_rate_percent
        
        # Resource utilization
        cpu_values = [p.cpu_usage_percent for p in data_points if p.cpu_usage_percent > 0]
        if cpu_values:
            summary.avg_cpu_usage = statistics.mean(cpu_values)
            summary.peak_cpu_usage = max(cpu_values)
        
        memory_values = [p.memory_usage_mb for p in data_points if p.memory_usage_mb > 0]
        if memory_values:
            summary.avg_memory_usage_mb = statistics.mean(memory_values)
            summary.peak_memory_usage_mb = max(memory_values)
        
        # Network analysis
        network_in = sum(p.network_in_bytes for p in data_points)
        network_out = sum(p.network_out_bytes for p in data_points)
        summary.total_network_in_mb = network_in / (1024 * 1024)
        summary.total_network_out_mb = network_out / (1024 * 1024)
        
        # Analyze trends
        if len(response_times) > 5:
            summary.response_time_trend = self.trend_analyzer.analyze_trend(response_times[-20:])
        if len(throughput_values) > 5:
            summary.throughput_trend = self.trend_analyzer.analyze_trend(throughput_values[-20:])
        
        # Endpoint analysis
        endpoint_times = defaultdict(list)
        endpoint_errors = defaultdict(int)
        
        for point in data_points:
            endpoint_times[point.endpoint].append(point.response_time_ms)
            if point.error_occurred:
                endpoint_errors[point.endpoint] += 1
        
        # Slowest endpoints
        avg_times = {
            endpoint: statistics.mean(times) 
            for endpoint, times in endpoint_times.items()
        }
        summary.slowest_endpoints = sorted(avg_times.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Highest error endpoints
        error_rates = {
            endpoint: (errors / len(endpoint_times[endpoint]) * 100)
            for endpoint, errors in endpoint_errors.items()
            if endpoint in endpoint_times
        }
        summary.highest_error_endpoints = sorted(error_rates.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return summary
    
    async def _check_performance_thresholds(self, data_point: PerformanceDataPoint):
        """Check if performance data point violates any thresholds."""
        # Check relevant thresholds for this data point
        threshold_keys = [
            f"{data_point.role.value}:{data_point.route_type.value}:{PerformanceMetric.RESPONSE_TIME.value}",
            f"{data_point.role.value}:{data_point.route_type.value}:{PerformanceMetric.CPU_USAGE.value}",
            f"{data_point.role.value}:{data_point.route_type.value}:{PerformanceMetric.MEMORY_USAGE.value}",
        ]
        
        for threshold_key in threshold_keys:
            if threshold_key in self.performance_thresholds:
                threshold = self.performance_thresholds[threshold_key]
                if not threshold.enabled:
                    continue
                
                # Get the metric value to check
                metric_value = self._get_metric_value_from_data_point(data_point, threshold.metric_type)
                if metric_value is None:
                    continue
                
                # Check if threshold is violated
                severity = None
                if metric_value >= threshold.critical_threshold:
                    severity = AlertSeverity.CRITICAL
                elif metric_value >= threshold.warning_threshold:
                    severity = AlertSeverity.HIGH
                
                if severity:
                    await self._create_performance_alert(
                        threshold=threshold,
                        current_value=metric_value,
                        severity=severity,
                        data_point=data_point
                    )
    
    def _get_metric_value_from_data_point(self, data_point: PerformanceDataPoint, metric_type: PerformanceMetric) -> Optional[float]:
        """Extract specific metric value from data point."""
        metric_map = {
            PerformanceMetric.RESPONSE_TIME: data_point.response_time_ms,
            PerformanceMetric.CPU_USAGE: data_point.cpu_usage_percent,
            PerformanceMetric.MEMORY_USAGE: data_point.memory_usage_mb,
            PerformanceMetric.THROUGHPUT: data_point.throughput_rps,
            PerformanceMetric.ERROR_RATE: 100.0 if data_point.error_occurred else 0.0,
        }
        return metric_map.get(metric_type)
    
    async def _create_performance_alert(
        self,
        threshold: PerformanceThreshold,
        current_value: float,
        severity: AlertSeverity,
        data_point: PerformanceDataPoint
    ):
        """Create a performance alert."""
        alert = PerformanceAlert(
            threshold=threshold,
            current_value=current_value,
            severity=severity,
            affected_role=data_point.role,
            affected_endpoints=[data_point.endpoint],
            related_metrics={
                "response_time_ms": data_point.response_time_ms,
                "cpu_usage": data_point.cpu_usage_percent,
                "memory_usage_mb": data_point.memory_usage_mb,
                "throughput_rps": data_point.throughput_rps
            }
        )
        
        # Store alert
        self.active_alerts[alert.alert_id] = alert
        
        self.logger.warning(
            f"Performance alert created: {severity.value} - "
            f"{threshold.metric_type.value} = {current_value} "
            f"(threshold: {threshold.critical_threshold if severity == AlertSeverity.CRITICAL else threshold.warning_threshold})"
        )
    
    def _get_current_system_stats(self) -> Dict[str, Any]:
        """Get current system performance statistics."""
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=None),
                "memory_mb": psutil.virtual_memory().used / (1024 * 1024),
                "available_memory_mb": psutil.virtual_memory().available / (1024 * 1024),
                "network_in": psutil.net_io_counters().bytes_recv,
                "network_out": psutil.net_io_counters().bytes_sent,
                "disk_read": psutil.disk_io_counters().read_bytes,
                "disk_write": psutil.disk_io_counters().write_bytes,
                "load_avg": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0,
                "cpu_cores": psutil.cpu_count(),
                "connections": len(psutil.net_connections())
            }
        except Exception as e:
            self.logger.error(f"Failed to get system stats: {str(e)}")
            return {}
    
    def _calculate_current_throughput(self, role: PlatformRole) -> float:
        """Calculate current throughput for a role."""
        # Count requests in the last minute
        one_minute_ago = datetime.now(timezone.utc) - timedelta(minutes=1)
        recent_count = 0
        
        role_key = role.value
        if role_key in self.performance_data:
            for point in list(self.performance_data[role_key])[-100:]:  # Check last 100 points
                if point.timestamp > one_minute_ago:
                    recent_count += 1
        
        return recent_count / 60.0  # requests per second
    
    def _start_system_monitoring(self):
        """Start background system monitoring."""
        def monitor_system():
            while not self.monitoring_stop_event.is_set():
                try:
                    self.system_stats = self._get_current_system_stats()
                    time.sleep(self.monitoring_interval_seconds)
                except Exception as e:
                    self.logger.error(f"System monitoring error: {str(e)}")
                    time.sleep(self.monitoring_interval_seconds)
        
        self.monitoring_thread = threading.Thread(target=monitor_system, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("System monitoring started")
    
    def _extract_metric_values(self, data_points: List[PerformanceDataPoint], metric_type: PerformanceMetric) -> List[float]:
        """Extract specific metric values from data points."""
        values = []
        for point in data_points:
            value = self._get_metric_value_from_data_point(point, metric_type)
            if value is not None and value > 0:
                values.append(value)
        return values
    
    def _generate_performance_recommendations(self, bottlenecks: List[str], summary: PerformanceSummary) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if "response_time" in bottlenecks:
            recommendations.append("Consider optimizing database queries and adding caching")
            recommendations.append("Review endpoint implementation for performance improvements")
        
        if "cpu_usage" in bottlenecks:
            recommendations.append("Consider horizontal scaling or CPU optimization")
            recommendations.append("Review resource-intensive operations")
        
        if "memory_usage" in bottlenecks:
            recommendations.append("Investigate memory leaks and optimize data structures")
            recommendations.append("Consider increasing available memory or implementing memory pooling")
        
        if "error_rate" in bottlenecks:
            recommendations.append("Investigate and fix underlying causes of errors")
            recommendations.append("Implement better error handling and retry mechanisms")
        
        return recommendations
    
    def _assess_bottleneck_severity(self, bottlenecks: List[str]) -> str:
        """Assess overall severity of detected bottlenecks."""
        if len(bottlenecks) >= 3:
            return "critical"
        elif len(bottlenecks) >= 2:
            return "high"
        elif len(bottlenecks) >= 1:
            return "medium"
        else:
            return "low"
    
    def _get_timedelta_for_window(self, window: TimeWindow) -> timedelta:
        """Convert time window enum to timedelta."""
        window_map = {
            TimeWindow.MINUTE: timedelta(minutes=1),
            TimeWindow.FIVE_MINUTES: timedelta(minutes=5),
            TimeWindow.FIFTEEN_MINUTES: timedelta(minutes=15),
            TimeWindow.HOUR: timedelta(hours=1),
            TimeWindow.DAY: timedelta(days=1),
            TimeWindow.WEEK: timedelta(weeks=1),
            TimeWindow.MONTH: timedelta(days=30)
        }
        return window_map.get(window, timedelta(hours=1))
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a sorted list."""
        if not data:
            return 0.0
        
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(data):
            return data[f] + c * (data[f + 1] - data[f])
        else:
            return data[f]


class PerformanceTrendAnalyzer:
    """Analyzes performance trends and patterns."""
    
    def analyze_trend(self, values: List[float]) -> PerformanceTrend:
        """Analyze trend direction from a series of values."""
        if len(values) < 3:
            return PerformanceTrend.STABLE
        
        # Calculate moving averages
        window_size = min(5, len(values) // 2)
        if window_size < 2:
            return PerformanceTrend.STABLE
        
        recent_avg = statistics.mean(values[-window_size:])
        earlier_avg = statistics.mean(values[:window_size])
        
        change_percent = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        
        # Assess volatility
        volatility = self.calculate_volatility(values)
        
        if volatility > 30:  # High volatility threshold
            return PerformanceTrend.VOLATILE
        elif change_percent > 10:  # 10% improvement
            return PerformanceTrend.IMPROVING
        elif change_percent < -10:  # 10% degradation
            return PerformanceTrend.DEGRADING
        else:
            return PerformanceTrend.STABLE
    
    def calculate_improvement_rate(self, values: List[float]) -> float:
        """Calculate the rate of improvement (positive) or degradation (negative)."""
        if len(values) < 2:
            return 0.0
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        if not first_half or not second_half:
            return 0.0
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        return ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0.0
    
    def calculate_volatility(self, values: List[float]) -> float:
        """Calculate volatility (coefficient of variation) as a percentage."""
        if len(values) < 2:
            return 0.0
        
        mean_value = statistics.mean(values)
        if mean_value == 0:
            return 0.0
        
        std_dev = statistics.stdev(values)
        return (std_dev / mean_value * 100)
    
    def predict_next_value(self, values: List[float]) -> Optional[float]:
        """Simple linear prediction of next value."""
        if len(values) < 3:
            return None
        
        # Simple linear regression for trend prediction
        x_values = list(range(len(values)))
        n = len(values)
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        next_x = len(values)
        return slope * next_x + intercept


class PerformanceBottleneckDetector:
    """Detects performance bottlenecks from metrics."""
    
    def detect_bottlenecks(self, summary: PerformanceSummary) -> List[str]:
        """Detect performance bottlenecks from a performance summary."""
        bottlenecks = []
        
        # Response time bottlenecks
        if summary.avg_response_time_ms > 2000:  # > 2 seconds
            bottlenecks.append("response_time")
        
        # Error rate bottlenecks
        if summary.error_rate_percent > 5:  # > 5% error rate
            bottlenecks.append("error_rate")
        
        # CPU usage bottlenecks
        if summary.avg_cpu_usage > 80:  # > 80% CPU
            bottlenecks.append("cpu_usage")
        
        # Memory usage bottlenecks
        if summary.avg_memory_usage_mb > 1000:  # > 1GB average usage
            bottlenecks.append("memory_usage")
        
        # Throughput bottlenecks
        if summary.avg_throughput_rps < 10 and summary.total_requests > 100:  # Low throughput with sufficient requests
            bottlenecks.append("throughput")
        
        # Trend-based bottlenecks
        if summary.response_time_trend == PerformanceTrend.DEGRADING:
            bottlenecks.append("response_time_degrading")
        
        if summary.error_rate_trend == PerformanceTrend.DEGRADING:
            bottlenecks.append("error_rate_increasing")
        
        return bottlenecks


# Factory function
def create_performance_tracker(**kwargs) -> PerformanceTracker:
    """Factory function to create PerformanceTracker."""
    return PerformanceTracker(**kwargs)