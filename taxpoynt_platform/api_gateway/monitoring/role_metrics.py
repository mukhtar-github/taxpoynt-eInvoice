"""
Role-Specific API Metrics Tracking
==================================
Comprehensive metrics collection and analysis for role-based API usage in TaxPoynt platform.
Tracks metrics separately for SI, APP, and HYBRID API endpoints with detailed performance analysis.
"""
import uuid
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, DefaultDict
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import time

from ..role_routing.models import (
    HTTPRoutingContext, PlatformRole, RouteType, HTTPMethod, RouteMetrics
)
from ...core_platform.authentication.role_manager import RoleScope, ServiceRole

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics to track."""
    REQUEST_COUNT = "request_count"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    BANDWIDTH = "bandwidth"
    CONCURRENT_USERS = "concurrent_users"
    RATE_LIMIT_HITS = "rate_limit_hits"
    AUTHENTICATION_FAILURES = "auth_failures"
    AUTHORIZATION_FAILURES = "authz_failures"


class TimeWindow(Enum):
    """Time windows for metrics aggregation."""
    MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    HOUR = "1h"
    DAY = "1d"
    WEEK = "1w"
    MONTH = "1mo"


@dataclass
class RoleMetricPoint:
    """Single metric data point for a specific role."""
    metric_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    role: PlatformRole
    service_role: Optional[ServiceRole] = None
    route_type: RouteType
    endpoint: str = ""
    http_method: HTTPMethod = HTTPMethod.GET
    
    # Metric values
    metric_type: MetricType
    value: float = 0.0
    count: int = 1
    
    # Request context
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    
    # Performance data
    response_time_ms: Optional[float] = None
    request_size_bytes: Optional[int] = None
    response_size_bytes: Optional[int] = None
    status_code: Optional[int] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoleMetricSummary:
    """Aggregated metrics summary for a role."""
    role: PlatformRole
    route_type: RouteType
    time_window: TimeWindow
    window_start: datetime
    window_end: datetime
    
    # Request metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    error_rate: float = 0.0
    
    # Performance metrics
    avg_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    p50_response_time_ms: float = 0.0
    p95_response_time_ms: float = 0.0
    p99_response_time_ms: float = 0.0
    
    # Throughput metrics
    requests_per_minute: float = 0.0
    peak_throughput: float = 0.0
    avg_throughput: float = 0.0
    
    # Bandwidth metrics
    total_bytes_in: int = 0
    total_bytes_out: int = 0
    avg_request_size: float = 0.0
    avg_response_size: float = 0.0
    
    # Concurrency metrics
    peak_concurrent_users: int = 0
    avg_concurrent_users: float = 0.0
    unique_users: int = 0
    unique_organizations: int = 0
    
    # Error analysis
    status_code_distribution: Dict[int, int] = field(default_factory=dict)
    top_error_endpoints: List[Tuple[str, int]] = field(default_factory=list)
    
    # Top endpoints by usage
    top_endpoints: List[Tuple[str, int]] = field(default_factory=list)


class RoleMetricsCollector:
    """
    Role-Specific API Metrics Collector
    ==================================
    
    **Core Features:**
    - Real-time metrics collection per role (SI, APP, HYBRID)
    - Time-windowed aggregation (1m, 5m, 15m, 1h, 1d, 1w, 1mo)
    - Performance tracking (response times, throughput, errors)
    - Resource usage monitoring (bandwidth, concurrency)
    - Multi-dimensional analysis (role + endpoint + organization)
    
    **Metrics Categories:**
    - Request Metrics: Count, success rate, error patterns
    - Performance Metrics: Response times, percentiles, throughput
    - Resource Metrics: Bandwidth usage, concurrent sessions
    - Business Metrics: Organization usage, user patterns
    """
    
    def __init__(
        self,
        max_points_per_window: int = 10000,
        retention_days: int = 30,
        enable_real_time_aggregation: bool = True,
        enable_detailed_logging: bool = False
    ):
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.max_points_per_window = max_points_per_window
        self.retention_days = retention_days
        self.enable_real_time_aggregation = enable_real_time_aggregation
        self.enable_detailed_logging = enable_detailed_logging
        
        # In-memory storage for real-time metrics
        self.metric_points: DefaultDict[str, deque] = defaultdict(lambda: deque(maxlen=self.max_points_per_window))
        self.aggregated_metrics: Dict[str, RoleMetricSummary] = {}
        
        # Active session tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.concurrent_users: DefaultDict[PlatformRole, Set[str]] = defaultdict(set)
        
        # Rate limiting tracking
        self.rate_limit_hits: DefaultDict[str, int] = defaultdict(int)
        
        # Performance caches
        self.response_time_cache: DefaultDict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Background tasks
        self.aggregation_tasks: List[asyncio.Task] = []
        self.cleanup_tasks: List[asyncio.Task] = []
        
        # Metrics metadata
        self.collection_start_time = datetime.now(timezone.utc)
        self.last_aggregation_time = datetime.now(timezone.utc)
        
        logger.info("RoleMetricsCollector initialized")
    
    async def record_request_start(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        method: HTTPMethod,
        route_type: RouteType,
        request_size_bytes: Optional[int] = None
    ) -> str:
        """Record the start of an API request."""
        request_id = routing_context.request_id
        
        # Track active session
        self.active_sessions[request_id] = {
            "start_time": time.time(),
            "routing_context": routing_context,
            "endpoint": endpoint,
            "method": method,
            "route_type": route_type,
            "request_size_bytes": request_size_bytes or 0
        }
        
        # Track concurrent users
        if routing_context.user_id and routing_context.platform_role:
            self.concurrent_users[routing_context.platform_role].add(routing_context.user_id)
        
        # Record request count metric
        await self._record_metric_point(
            routing_context=routing_context,
            endpoint=endpoint,
            method=method,
            route_type=route_type,
            metric_type=MetricType.REQUEST_COUNT,
            value=1.0,
            request_size_bytes=request_size_bytes
        )
        
        if self.enable_detailed_logging:
            self.logger.debug(f"Request started: {request_id} - {routing_context.platform_role.value} - {endpoint}")
        
        return request_id
    
    async def record_request_end(
        self,
        request_id: str,
        status_code: int,
        response_size_bytes: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """Record the completion of an API request."""
        if request_id not in self.active_sessions:
            self.logger.warning(f"Unknown request ID: {request_id}")
            return
        
        session = self.active_sessions[request_id]
        end_time = time.time()
        response_time_ms = (end_time - session["start_time"]) * 1000
        
        routing_context = session["routing_context"]
        endpoint = session["endpoint"]
        method = session["method"]
        route_type = session["route_type"]
        
        # Record response time metric
        await self._record_metric_point(
            routing_context=routing_context,
            endpoint=endpoint,
            method=method,
            route_type=route_type,
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time_ms,
            response_time_ms=response_time_ms,
            request_size_bytes=session.get("request_size_bytes"),
            response_size_bytes=response_size_bytes,
            status_code=status_code
        )
        
        # Record error metrics if applicable
        if status_code >= 400:
            await self._record_metric_point(
                routing_context=routing_context,
                endpoint=endpoint,
                method=method,
                route_type=route_type,
                metric_type=MetricType.ERROR_RATE,
                value=1.0,
                status_code=status_code,
                metadata={"error_message": error_message} if error_message else {}
            )
        
        # Record bandwidth metrics
        if response_size_bytes:
            await self._record_metric_point(
                routing_context=routing_context,
                endpoint=endpoint,
                method=method,
                route_type=route_type,
                metric_type=MetricType.BANDWIDTH,
                value=float(response_size_bytes),
                response_size_bytes=response_size_bytes
            )
        
        # Cache response time for percentile calculations
        cache_key = f"{routing_context.platform_role.value}:{route_type.value}:{endpoint}"
        self.response_time_cache[cache_key].append(response_time_ms)
        
        # Clean up session
        del self.active_sessions[request_id]
        
        if self.enable_detailed_logging:
            self.logger.debug(f"Request completed: {request_id} - {status_code} - {response_time_ms:.2f}ms")
    
    async def record_rate_limit_hit(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        limit_type: str = "general"
    ):
        """Record a rate limit violation."""
        cache_key = f"{routing_context.platform_role.value}:{endpoint}:{limit_type}"
        self.rate_limit_hits[cache_key] += 1
        
        await self._record_metric_point(
            routing_context=routing_context,
            endpoint=endpoint,
            method=HTTPMethod.GET,  # Rate limits apply to all methods
            route_type=self._determine_route_type(endpoint),
            metric_type=MetricType.RATE_LIMIT_HITS,
            value=1.0,
            metadata={"limit_type": limit_type}
        )
    
    async def record_authentication_failure(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        failure_reason: str
    ):
        """Record an authentication failure."""
        await self._record_metric_point(
            routing_context=routing_context,
            endpoint=endpoint,
            method=HTTPMethod.GET,
            route_type=self._determine_route_type(endpoint),
            metric_type=MetricType.AUTHENTICATION_FAILURES,
            value=1.0,
            metadata={"failure_reason": failure_reason}
        )
    
    async def record_authorization_failure(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        failure_reason: str
    ):
        """Record an authorization failure."""
        await self._record_metric_point(
            routing_context=routing_context,
            endpoint=endpoint,
            method=HTTPMethod.GET,
            route_type=self._determine_route_type(endpoint),
            metric_type=MetricType.AUTHORIZATION_FAILURES,
            value=1.0,
            metadata={"failure_reason": failure_reason}
        )
    
    async def get_role_metrics(
        self,
        role: PlatformRole,
        route_type: Optional[RouteType] = None,
        time_window: TimeWindow = TimeWindow.HOUR,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> RoleMetricSummary:
        """Get aggregated metrics for a specific role."""
        
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            start_time = end_time - self._get_timedelta_for_window(time_window)
        
        # Generate cache key
        cache_key = f"{role.value}:{route_type.value if route_type else 'all'}:{time_window.value}:{start_time.isoformat()}:{end_time.isoformat()}"
        
        # Check if we have cached aggregated data
        if cache_key in self.aggregated_metrics:
            cached_summary = self.aggregated_metrics[cache_key]
            # Check if cache is still valid (within last 5 minutes)
            if (datetime.now(timezone.utc) - cached_summary.window_end).total_seconds() < 300:
                return cached_summary
        
        # Aggregate metrics in real-time
        summary = await self._aggregate_metrics_for_role(
            role=role,
            route_type=route_type,
            time_window=time_window,
            start_time=start_time,
            end_time=end_time
        )
        
        # Cache the summary
        self.aggregated_metrics[cache_key] = summary
        
        return summary
    
    async def get_comparative_role_metrics(
        self,
        roles: List[PlatformRole],
        time_window: TimeWindow = TimeWindow.HOUR
    ) -> Dict[PlatformRole, RoleMetricSummary]:
        """Get comparative metrics across multiple roles."""
        results = {}
        
        for role in roles:
            try:
                results[role] = await self.get_role_metrics(
                    role=role,
                    time_window=time_window
                )
            except Exception as e:
                self.logger.error(f"Failed to get metrics for role {role.value}: {str(e)}")
                # Create empty summary for failed role
                results[role] = RoleMetricSummary(
                    role=role,
                    route_type=RouteType.PUBLIC,
                    time_window=time_window,
                    window_start=datetime.now(timezone.utc) - self._get_timedelta_for_window(time_window),
                    window_end=datetime.now(timezone.utc)
                )
        
        return results
    
    async def get_endpoint_metrics_by_role(
        self,
        endpoint: str,
        time_window: TimeWindow = TimeWindow.HOUR
    ) -> Dict[PlatformRole, RoleMetricSummary]:
        """Get metrics for a specific endpoint across all roles."""
        results = {}
        
        for role in PlatformRole:
            # Filter metrics for this specific endpoint
            filtered_points = []
            role_key = role.value
            
            if role_key in self.metric_points:
                for point in self.metric_points[role_key]:
                    if isinstance(point, RoleMetricPoint) and point.endpoint == endpoint:
                        filtered_points.append(point)
            
            if filtered_points:
                # Create a temporary summary for this endpoint
                summary = await self._create_summary_from_points(
                    points=filtered_points,
                    role=role,
                    route_type=self._determine_route_type(endpoint),
                    time_window=time_window
                )
                results[role] = summary
        
        return results
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics across all roles."""
        now = datetime.now(timezone.utc)
        
        # Current concurrent users by role
        concurrent_stats = {}
        for role, users in self.concurrent_users.items():
            # Clean up old sessions (older than 30 minutes)
            active_users = set()
            for user_id in users:
                # In production, check last activity timestamp
                active_users.add(user_id)
            self.concurrent_users[role] = active_users
            concurrent_stats[role.value] = len(active_users)
        
        # Active requests
        active_requests = len(self.active_sessions)
        
        # Recent throughput (last 5 minutes)
        five_min_ago = now - timedelta(minutes=5)
        recent_requests = {}
        
        for role_key, points in self.metric_points.items():
            role_requests = 0
            for point in points:
                if isinstance(point, RoleMetricPoint) and point.timestamp > five_min_ago:
                    if point.metric_type == MetricType.REQUEST_COUNT:
                        role_requests += point.count
            recent_requests[role_key] = role_requests
        
        # Recent error rates
        recent_errors = {}
        for role_key, points in self.metric_points.items():
            role_errors = 0
            role_total = 0
            for point in points:
                if isinstance(point, RoleMetricPoint) and point.timestamp > five_min_ago:
                    if point.metric_type == MetricType.REQUEST_COUNT:
                        role_total += point.count
                    elif point.metric_type == MetricType.ERROR_RATE:
                        role_errors += point.count
            
            error_rate = (role_errors / role_total * 100) if role_total > 0 else 0
            recent_errors[role_key] = error_rate
        
        return {
            "timestamp": now.isoformat(),
            "concurrent_users_by_role": concurrent_stats,
            "active_requests": active_requests,
            "recent_requests_5min": recent_requests,
            "recent_error_rates_5min": recent_errors,
            "collection_uptime_hours": (now - self.collection_start_time).total_seconds() / 3600,
            "total_metric_points": sum(len(points) for points in self.metric_points.values()),
            "memory_usage": {
                "metric_points_count": sum(len(points) for points in self.metric_points.values()),
                "active_sessions_count": len(self.active_sessions),
                "aggregated_summaries_count": len(self.aggregated_metrics),
                "response_time_cache_size": sum(len(cache) for cache in self.response_time_cache.values())
            }
        }
    
    async def _record_metric_point(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        method: HTTPMethod,
        route_type: RouteType,
        metric_type: MetricType,
        value: float,
        count: int = 1,
        **kwargs
    ):
        """Record a single metric point."""
        point = RoleMetricPoint(
            timestamp=datetime.now(timezone.utc),
            role=routing_context.platform_role or PlatformRole.USER,
            service_role=routing_context.service_role,
            route_type=route_type,
            endpoint=endpoint,
            http_method=method,
            metric_type=metric_type,
            value=value,
            count=count,
            organization_id=routing_context.organization_id,
            tenant_id=routing_context.tenant_id,
            user_id=routing_context.user_id,
            **kwargs
        )
        
        # Store in role-specific collection
        role_key = point.role.value
        self.metric_points[role_key].append(point)
        
        # Trigger real-time aggregation if enabled
        if self.enable_real_time_aggregation:
            await self._trigger_real_time_aggregation(point)
    
    async def _aggregate_metrics_for_role(
        self,
        role: PlatformRole,
        route_type: Optional[RouteType],
        time_window: TimeWindow,
        start_time: datetime,
        end_time: datetime
    ) -> RoleMetricSummary:
        """Aggregate metrics for a specific role and time window."""
        
        # Filter relevant metric points
        role_key = role.value
        relevant_points = []
        
        if role_key in self.metric_points:
            for point in self.metric_points[role_key]:
                if isinstance(point, RoleMetricPoint):
                    # Time filter
                    if not (start_time <= point.timestamp <= end_time):
                        continue
                    
                    # Route type filter
                    if route_type and point.route_type != route_type:
                        continue
                    
                    relevant_points.append(point)
        
        return await self._create_summary_from_points(
            points=relevant_points,
            role=role,
            route_type=route_type or RouteType.PUBLIC,
            time_window=time_window,
            window_start=start_time,
            window_end=end_time
        )
    
    async def _create_summary_from_points(
        self,
        points: List[RoleMetricPoint],
        role: PlatformRole,
        route_type: RouteType,
        time_window: TimeWindow,
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None
    ) -> RoleMetricSummary:
        """Create a metrics summary from a list of metric points."""
        
        if not window_end:
            window_end = datetime.now(timezone.utc)
        if not window_start:
            window_start = window_end - self._get_timedelta_for_window(time_window)
        
        summary = RoleMetricSummary(
            role=role,
            route_type=route_type,
            time_window=time_window,
            window_start=window_start,
            window_end=window_end
        )
        
        if not points:
            return summary
        
        # Process points by metric type
        request_counts = []
        error_counts = []
        response_times = []
        bandwidth_values = []
        status_codes = defaultdict(int)
        endpoint_counts = defaultdict(int)
        user_ids = set()
        org_ids = set()
        
        for point in points:
            if point.metric_type == MetricType.REQUEST_COUNT:
                request_counts.append(point.count)
                endpoint_counts[point.endpoint] += point.count
                if point.user_id:
                    user_ids.add(point.user_id)
                if point.organization_id:
                    org_ids.add(point.organization_id)
            elif point.metric_type == MetricType.ERROR_RATE:
                error_counts.append(point.count)
                if point.status_code:
                    status_codes[point.status_code] += point.count
            elif point.metric_type == MetricType.RESPONSE_TIME:
                if point.response_time_ms:
                    response_times.append(point.response_time_ms)
            elif point.metric_type == MetricType.BANDWIDTH:
                bandwidth_values.append(point.value)
        
        # Calculate request metrics
        summary.total_requests = sum(request_counts)
        summary.failed_requests = sum(error_counts)
        summary.successful_requests = summary.total_requests - summary.failed_requests
        summary.error_rate = (summary.failed_requests / summary.total_requests * 100) if summary.total_requests > 0 else 0
        
        # Calculate performance metrics
        if response_times:
            response_times.sort()
            summary.avg_response_time_ms = sum(response_times) / len(response_times)
            summary.min_response_time_ms = min(response_times)
            summary.max_response_time_ms = max(response_times)
            summary.p50_response_time_ms = self._percentile(response_times, 50)
            summary.p95_response_time_ms = self._percentile(response_times, 95)
            summary.p99_response_time_ms = self._percentile(response_times, 99)
        
        # Calculate throughput metrics
        time_span_minutes = (window_end - window_start).total_seconds() / 60
        if time_span_minutes > 0:
            summary.requests_per_minute = summary.total_requests / time_span_minutes
            summary.avg_throughput = summary.requests_per_minute
        
        # Calculate bandwidth metrics
        if bandwidth_values:
            summary.total_bytes_out = sum(bandwidth_values)
            summary.avg_response_size = sum(bandwidth_values) / len(bandwidth_values)
        
        # User and organization metrics
        summary.unique_users = len(user_ids)
        summary.unique_organizations = len(org_ids)
        
        # Status code distribution
        summary.status_code_distribution = dict(status_codes)
        
        # Top endpoints
        summary.top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return summary
    
    def _determine_route_type(self, endpoint: str) -> RouteType:
        """Determine route type from endpoint path."""
        if "/si/" in endpoint or endpoint.startswith("/api/v1/si/"):
            return RouteType.SI_ONLY
        elif "/app/" in endpoint or endpoint.startswith("/api/v1/app/"):
            return RouteType.APP_ONLY
        elif "/hybrid/" in endpoint or endpoint.startswith("/api/v1/hybrid/"):
            return RouteType.HYBRID
        elif "/admin/" in endpoint:
            return RouteType.ADMIN
        elif "/health" in endpoint:
            return RouteType.HEALTH
        else:
            return RouteType.PUBLIC
    
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
    
    async def _trigger_real_time_aggregation(self, point: RoleMetricPoint):
        """Trigger real-time aggregation for immediate insights."""
        # This could trigger background aggregation tasks
        # For now, we'll just update some cached values
        pass
    
    async def cleanup_old_data(self):
        """Clean up old metric data beyond retention period."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.retention_days)
        
        # Clean up metric points
        for role_key in list(self.metric_points.keys()):
            points = self.metric_points[role_key]
            # Keep only points newer than cutoff
            filtered_points = deque([
                p for p in points 
                if isinstance(p, RoleMetricPoint) and p.timestamp > cutoff_time
            ], maxlen=self.max_points_per_window)
            self.metric_points[role_key] = filtered_points
        
        # Clean up aggregated metrics cache
        for cache_key in list(self.aggregated_metrics.keys()):
            summary = self.aggregated_metrics[cache_key]
            if summary.window_end < cutoff_time:
                del self.aggregated_metrics[cache_key]
        
        # Clean up response time cache
        for cache_key in list(self.response_time_cache.keys()):
            # Keep last 1000 response times per endpoint
            # This is already handled by deque maxlen, but we can trigger cleanup
            pass
        
        self.logger.info(f"Cleaned up metrics data older than {self.retention_days} days")
    
    async def get_metrics_export(
        self,
        role: PlatformRole,
        format_type: str = "json",
        time_window: TimeWindow = TimeWindow.DAY
    ) -> Dict[str, Any]:
        """Export metrics in various formats for external analysis."""
        summary = await self.get_role_metrics(role=role, time_window=time_window)
        real_time = await self.get_real_time_metrics()
        
        export_data = {
            "export_metadata": {
                "role": role.value,
                "time_window": time_window.value,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "format": format_type
            },
            "summary_metrics": {
                "total_requests": summary.total_requests,
                "successful_requests": summary.successful_requests,
                "failed_requests": summary.failed_requests,
                "error_rate": summary.error_rate,
                "avg_response_time_ms": summary.avg_response_time_ms,
                "p95_response_time_ms": summary.p95_response_time_ms,
                "p99_response_time_ms": summary.p99_response_time_ms,
                "requests_per_minute": summary.requests_per_minute,
                "unique_users": summary.unique_users,
                "unique_organizations": summary.unique_organizations
            },
            "real_time_metrics": real_time,
            "detailed_breakdown": {
                "status_code_distribution": summary.status_code_distribution,
                "top_endpoints": summary.top_endpoints,
                "bandwidth_metrics": {
                    "total_bytes_out": summary.total_bytes_out,
                    "avg_response_size": summary.avg_response_size
                }
            }
        }
        
        return export_data


# Factory function
def create_role_metrics_collector(**kwargs) -> RoleMetricsCollector:
    """Factory function to create RoleMetricsCollector."""
    return RoleMetricsCollector(**kwargs)