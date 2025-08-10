"""
API Usage Analytics and Pattern Analysis
========================================
Comprehensive usage pattern analysis for role-based API endpoints in TaxPoynt platform.
Analyzes usage trends, user behavior, endpoint popularity, and provides insights for optimization.
"""
import uuid
import logging
import asyncio
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, DefaultDict
from dataclasses import dataclass, field
from collections import defaultdict, deque, Counter
from enum import Enum
import json
import math

from ..role_routing.models import HTTPRoutingContext, PlatformRole, RouteType, HTTPMethod
from .role_metrics import TimeWindow, RoleMetricsCollector, RoleMetricPoint
from .performance_tracker import PerformanceTracker
from ...core_platform.authentication.role_manager import ServiceRole

logger = logging.getLogger(__name__)


class UsagePattern(Enum):
    """Types of usage patterns."""
    PEAK_HOURS = "peak_hours"
    SEASONAL = "seasonal"
    BURST = "burst"
    STEADY = "steady"
    DECLINING = "declining"
    GROWING = "growing"
    IRREGULAR = "irregular"


class UserBehavior(Enum):
    """User behavior patterns."""
    HEAVY_USER = "heavy_user"
    MODERATE_USER = "moderate_user"
    LIGHT_USER = "light_user"
    POWER_USER = "power_user"
    OCCASIONAL_USER = "occasional_user"
    NEW_USER = "new_user"
    DORMANT_USER = "dormant_user"


class EndpointCategory(Enum):
    """Endpoint usage categories."""
    CRITICAL = "critical"
    HIGH_USAGE = "high_usage"
    MODERATE_USAGE = "moderate_usage"
    LOW_USAGE = "low_usage"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


@dataclass
class UsageDataPoint:
    """Single usage data point."""
    usage_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Request details
    role: PlatformRole
    route_type: RouteType
    endpoint: str
    http_method: HTTPMethod
    
    # User context
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Request characteristics
    request_size_bytes: int = 0
    response_size_bytes: int = 0
    response_time_ms: float = 0.0
    status_code: int = 200
    
    # Geographic and client info
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None
    geo_country: Optional[str] = None
    geo_region: Optional[str] = None
    
    # Feature usage
    features_used: List[str] = field(default_factory=list)
    api_version: Optional[str] = None
    
    # Business context
    business_operation: Optional[str] = None
    transaction_value: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserUsageProfile:
    """User usage behavior profile."""
    user_id: str
    role: PlatformRole
    organization_id: Optional[str] = None
    
    # Usage statistics
    total_requests: int = 0
    unique_endpoints: int = 0
    avg_requests_per_day: float = 0.0
    peak_requests_per_hour: int = 0
    
    # Temporal patterns
    most_active_hour: int = 12  # 24-hour format
    most_active_day: int = 1  # 1=Monday, 7=Sunday
    usage_consistency: float = 0.0  # 0-1, how consistent usage is
    
    # Behavior classification
    behavior_type: UserBehavior = UserBehavior.MODERATE_USER
    user_segment: str = "standard"
    
    # Feature adoption
    top_endpoints: List[Tuple[str, int]] = field(default_factory=list)
    feature_adoption_rate: float = 0.0
    advanced_features_usage: int = 0
    
    # Quality metrics
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    satisfaction_score: float = 0.0  # Derived from performance metrics
    
    # Trends
    usage_trend: str = "stable"  # growing, declining, stable
    last_active: Optional[datetime] = None
    days_since_first_use: int = 0
    
    # Analysis metadata
    profile_created: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EndpointUsageAnalysis:
    """Endpoint usage analysis results."""
    endpoint: str
    route_type: RouteType
    
    # Usage statistics
    total_requests: int = 0
    unique_users: int = 0
    unique_organizations: int = 0
    requests_per_day_avg: float = 0.0
    
    # Performance metrics
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    error_rate: float = 0.0
    success_rate: float = 100.0
    
    # User distribution
    role_distribution: Dict[str, int] = field(default_factory=dict)
    organization_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Temporal patterns
    peak_hour: int = 12
    peak_day: int = 1
    usage_pattern: UsagePattern = UsagePattern.STEADY
    
    # Business metrics
    category: EndpointCategory = EndpointCategory.MODERATE_USAGE
    business_value_score: float = 0.0
    adoption_rate: float = 0.0
    
    # Trends and insights
    growth_rate: float = 0.0
    usage_trend: str = "stable"
    optimization_opportunities: List[str] = field(default_factory=list)
    
    # Analysis metadata
    analysis_period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=7))
    analysis_period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    analyzed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UsageInsight:
    """Usage insight and recommendation."""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: str = ""
    title: str = ""
    description: str = ""
    
    # Context
    affected_roles: List[PlatformRole] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    
    # Metrics
    impact_score: float = 0.0  # 0-100
    confidence_level: float = 0.0  # 0-1
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    estimated_benefit: str = ""
    implementation_effort: str = "medium"
    
    # Supporting data
    supporting_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: str = "medium"
    tags: List[str] = field(default_factory=list)


class UsageAnalytics:
    """
    API Usage Analytics and Pattern Analysis
    ========================================
    
    **Core Capabilities:**
    - User behavior analysis and segmentation
    - Endpoint usage pattern identification
    - Temporal usage trend analysis
    - Feature adoption tracking
    - Business intelligence insights
    - Usage optimization recommendations
    
    **Analytics Categories:**
    - User Analytics: Behavior patterns, segmentation, lifecycle
    - Endpoint Analytics: Usage patterns, performance correlation
    - Temporal Analytics: Peak times, seasonal patterns, trends
    - Business Analytics: Feature adoption, ROI, optimization
    - Predictive Analytics: Usage forecasting, capacity planning
    """
    
    def __init__(
        self,
        metrics_collector: Optional[RoleMetricsCollector] = None,
        performance_tracker: Optional[PerformanceTracker] = None,
        enable_real_time_analytics: bool = True,
        enable_predictive_analytics: bool = False,
        analytics_retention_days: int = 90,
        min_data_points_for_analysis: int = 100
    ):
        self.logger = logging.getLogger(__name__)
        
        # Dependencies
        self.metrics_collector = metrics_collector
        self.performance_tracker = performance_tracker
        
        # Configuration
        self.enable_real_time_analytics = enable_real_time_analytics
        self.enable_predictive_analytics = enable_predictive_analytics
        self.analytics_retention_days = analytics_retention_days
        self.min_data_points_for_analysis = min_data_points_for_analysis
        
        # Usage data storage
        self.usage_data: DefaultDict[str, deque] = defaultdict(lambda: deque(maxlen=100000))
        self.user_profiles: Dict[str, UserUsageProfile] = {}
        self.endpoint_analyses: Dict[str, EndpointUsageAnalysis] = {}
        
        # Analytics caches
        self.usage_insights: List[UsageInsight] = []
        self.analytics_cache: Dict[str, Any] = {}
        self.real_time_stats: Dict[str, Any] = {}
        
        # Pattern detection
        self.pattern_detector = UsagePatternDetector()
        self.behavior_analyzer = UserBehaviorAnalyzer()
        self.insight_generator = UsageInsightGenerator()
        
        # Background analytics tasks
        self.analytics_tasks: List[asyncio.Task] = []
        
        # Initialize analytics
        self._initialize_analytics()
        
        logger.info("UsageAnalytics initialized")
    
    async def record_usage(
        self,
        routing_context: HTTPRoutingContext,
        endpoint: str,
        method: HTTPMethod,
        route_type: RouteType,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
        response_time_ms: float = 0.0,
        status_code: int = 200,
        features_used: Optional[List[str]] = None,
        business_context: Optional[Dict[str, Any]] = None
    ):
        """Record API usage for analytics."""
        
        usage_point = UsageDataPoint(
            timestamp=datetime.now(timezone.utc),
            role=routing_context.platform_role or PlatformRole.USER,
            route_type=route_type,
            endpoint=endpoint,
            http_method=method,
            user_id=routing_context.user_id,
            organization_id=routing_context.organization_id,
            tenant_id=routing_context.tenant_id,
            session_id=routing_context.session_id,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
            response_time_ms=response_time_ms,
            status_code=status_code,
            client_ip=routing_context.client_ip,
            user_agent=routing_context.user_agent,
            features_used=features_used or [],
            business_operation=business_context.get("operation") if business_context else None,
            transaction_value=business_context.get("value") if business_context else None
        )
        
        # Store usage data
        await self._store_usage_data(usage_point)
        
        # Update user profile if applicable
        if usage_point.user_id:
            await self._update_user_profile(usage_point)
        
        # Update real-time statistics
        if self.enable_real_time_analytics:
            await self._update_real_time_stats(usage_point)
        
        self.logger.debug(f"Recorded usage: {usage_point.role.value} - {endpoint}")
    
    async def get_user_analytics(
        self,
        user_id: Optional[str] = None,
        role: Optional[PlatformRole] = None,
        organization_id: Optional[str] = None,
        time_window: TimeWindow = TimeWindow.WEEK
    ) -> Dict[str, Any]:
        """Get user analytics and behavior insights."""
        
        # Filter users based on criteria
        target_users = []
        if user_id:
            if user_id in self.user_profiles:
                target_users = [self.user_profiles[user_id]]
        else:
            target_users = [
                profile for profile in self.user_profiles.values()
                if (not role or profile.role == role) and
                   (not organization_id or profile.organization_id == organization_id)
            ]
        
        if not target_users:
            return {"users": [], "summary": {}, "insights": []}
        
        # Analyze user behavior
        user_analytics = []
        for profile in target_users:
            analytics = await self._analyze_user_behavior(profile, time_window)
            user_analytics.append(analytics)
        
        # Generate summary statistics
        summary = self._generate_user_analytics_summary(user_analytics, role)
        
        # Generate insights
        insights = await self._generate_user_insights(user_analytics, time_window)
        
        return {
            "users": user_analytics,
            "summary": summary,
            "insights": insights,
            "analysis_metadata": {
                "total_users_analyzed": len(user_analytics),
                "time_window": time_window.value,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "role_filter": role.value if role else None,
                "organization_filter": organization_id
            }
        }
    
    async def get_endpoint_analytics(
        self,
        endpoint: Optional[str] = None,
        route_type: Optional[RouteType] = None,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.WEEK
    ) -> Dict[str, Any]:
        """Get endpoint usage analytics and optimization insights."""
        
        # Collect usage data for analysis
        usage_data = await self._collect_endpoint_usage_data(
            endpoint=endpoint,
            route_type=route_type,
            role=role,
            time_window=time_window
        )
        
        # Analyze endpoint usage patterns
        endpoint_analyses = []
        
        # Group by endpoint
        endpoint_groups = defaultdict(list)
        for point in usage_data:
            endpoint_groups[point.endpoint].extend([point])
        
        for endpoint_path, points in endpoint_groups.items():
            if len(points) >= self.min_data_points_for_analysis:
                analysis = await self._analyze_endpoint_usage(endpoint_path, points, time_window)
                endpoint_analyses.append(analysis)
        
        # Generate summary and insights
        summary = self._generate_endpoint_analytics_summary(endpoint_analyses)
        insights = await self._generate_endpoint_insights(endpoint_analyses)
        
        return {
            "endpoints": [self._endpoint_analysis_to_dict(analysis) for analysis in endpoint_analyses],
            "summary": summary,
            "insights": insights,
            "analysis_metadata": {
                "total_endpoints_analyzed": len(endpoint_analyses),
                "time_window": time_window.value,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
                "filters": {
                    "endpoint": endpoint,
                    "route_type": route_type.value if route_type else None,
                    "role": role.value if role else None
                }
            }
        }
    
    async def get_temporal_analytics(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.DAY,
        analysis_days: int = 30
    ) -> Dict[str, Any]:
        """Get temporal usage pattern analytics."""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=analysis_days)
        
        # Collect temporal usage data
        usage_data = await self._collect_usage_data_for_period(
            role=role,
            start_time=start_time,
            end_time=end_time
        )
        
        # Analyze temporal patterns
        temporal_analysis = {
            "hourly_patterns": self._analyze_hourly_patterns(usage_data),
            "daily_patterns": self._analyze_daily_patterns(usage_data),
            "weekly_patterns": self._analyze_weekly_patterns(usage_data),
            "seasonal_patterns": self._analyze_seasonal_patterns(usage_data),
            "peak_detection": self._detect_usage_peaks(usage_data),
            "trend_analysis": self._analyze_usage_trends(usage_data)
        }
        
        # Generate temporal insights
        insights = await self._generate_temporal_insights(temporal_analysis, role)
        
        return {
            "temporal_analysis": temporal_analysis,
            "insights": insights,
            "analysis_metadata": {
                "role": role.value if role else "all",
                "analysis_period_days": analysis_days,
                "data_points_analyzed": len(usage_data),
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def get_feature_adoption_analytics(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.MONTH
    ) -> Dict[str, Any]:
        """Get feature adoption and usage analytics."""
        
        # Collect feature usage data
        feature_data = await self._collect_feature_usage_data(role, time_window)
        
        # Analyze feature adoption
        adoption_analysis = {
            "feature_usage_summary": self._analyze_feature_usage(feature_data),
            "adoption_rates": self._calculate_adoption_rates(feature_data),
            "feature_correlation": self._analyze_feature_correlation(feature_data),
            "user_journey_analysis": self._analyze_user_journeys(feature_data),
            "feature_performance": await self._analyze_feature_performance(feature_data)
        }
        
        # Generate feature insights
        insights = await self._generate_feature_insights(adoption_analysis, role)
        
        return {
            "feature_adoption": adoption_analysis,
            "insights": insights,
            "analysis_metadata": {
                "role": role.value if role else "all",
                "time_window": time_window.value,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def get_business_intelligence(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.MONTH
    ) -> Dict[str, Any]:
        """Get business intelligence insights from usage analytics."""
        
        # Collect comprehensive usage data
        bi_data = await self._collect_business_intelligence_data(role, time_window)
        
        # Generate business insights
        business_analysis = {
            "user_engagement": self._analyze_user_engagement(bi_data),
            "feature_roi": self._analyze_feature_roi(bi_data),
            "capacity_planning": self._analyze_capacity_requirements(bi_data),
            "optimization_opportunities": await self._identify_optimization_opportunities(bi_data),
            "growth_analysis": self._analyze_growth_patterns(bi_data),
            "risk_assessment": self._assess_usage_risks(bi_data)
        }
        
        # Generate strategic insights
        strategic_insights = await self._generate_strategic_insights(business_analysis, role)
        
        return {
            "business_intelligence": business_analysis,
            "strategic_insights": strategic_insights,
            "recommendations": await self._generate_business_recommendations(business_analysis),
            "analysis_metadata": {
                "role": role.value if role else "all",
                "time_window": time_window.value,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def get_real_time_usage_dashboard(self) -> Dict[str, Any]:
        """Get real-time usage dashboard data."""
        
        current_time = datetime.now(timezone.utc)
        
        # Current activity
        current_activity = {
            "active_users_count": len(set(
                point.user_id for points in self.usage_data.values() 
                for point in list(points)[-100:] 
                if point.user_id and (current_time - point.timestamp).total_seconds() < 3600
            )),
            "requests_last_hour": sum(
                1 for points in self.usage_data.values() 
                for point in list(points)[-100:] 
                if (current_time - point.timestamp).total_seconds() < 3600
            ),
            "top_endpoints_now": self._get_current_top_endpoints(),
            "role_distribution": self._get_current_role_distribution(),
            "geographic_distribution": self._get_current_geographic_distribution()
        }
        
        # Performance correlations
        performance_correlation = await self._correlate_usage_with_performance()
        
        # Alerts and anomalies
        anomalies = await self._detect_usage_anomalies()
        
        return {
            "current_activity": current_activity,
            "performance_correlation": performance_correlation,
            "anomalies": anomalies,
            "real_time_insights": await self._generate_real_time_insights(),
            "dashboard_metadata": {
                "updated_at": current_time.isoformat(),
                "data_freshness_minutes": 1,
                "total_data_points": sum(len(points) for points in self.usage_data.values())
            }
        }
    
    async def _store_usage_data(self, usage_point: UsageDataPoint):
        """Store usage data point."""
        # Store by role for efficient querying
        role_key = usage_point.role.value
        self.usage_data[role_key].append(usage_point)
        
        # Store by endpoint for endpoint-specific analysis
        endpoint_key = f"endpoint:{usage_point.endpoint}"
        self.usage_data[endpoint_key].append(usage_point)
        
        # Store by user for user-specific analysis
        if usage_point.user_id:
            user_key = f"user:{usage_point.user_id}"
            self.usage_data[user_key].append(usage_point)
        
        # Store by organization for org-specific analysis
        if usage_point.organization_id:
            org_key = f"org:{usage_point.organization_id}"
            self.usage_data[org_key].append(usage_point)
    
    async def _update_user_profile(self, usage_point: UsageDataPoint):
        """Update or create user usage profile."""
        user_id = usage_point.user_id
        if not user_id:
            return
        
        # Get or create profile
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserUsageProfile(
                user_id=user_id,
                role=usage_point.role,
                organization_id=usage_point.organization_id
            )
        
        profile = self.user_profiles[user_id]
        
        # Update basic statistics
        profile.total_requests += 1
        profile.last_active = usage_point.timestamp
        profile.last_updated = datetime.now(timezone.utc)
        
        # Update endpoint usage
        endpoint_counter = dict(profile.top_endpoints)
        endpoint_counter[usage_point.endpoint] = endpoint_counter.get(usage_point.endpoint, 0) + 1
        profile.top_endpoints = sorted(endpoint_counter.items(), key=lambda x: x[1], reverse=True)[:10]
        profile.unique_endpoints = len(endpoint_counter)
        
        # Update temporal patterns
        hour = usage_point.timestamp.hour
        day_of_week = usage_point.timestamp.weekday() + 1  # 1=Monday
        
        # Simple heuristic for most active hour/day (could be improved with proper analysis)
        if not hasattr(profile, '_hourly_counts'):
            profile._hourly_counts = defaultdict(int)
            profile._daily_counts = defaultdict(int)
        
        profile._hourly_counts[hour] += 1
        profile._daily_counts[day_of_week] += 1
        
        profile.most_active_hour = max(profile._hourly_counts, key=profile._hourly_counts.get)
        profile.most_active_day = max(profile._daily_counts, key=profile._daily_counts.get)
        
        # Update behavior classification
        profile.behavior_type = self.behavior_analyzer.classify_user_behavior(profile)
    
    async def _analyze_user_behavior(self, profile: UserUsageProfile, time_window: TimeWindow) -> Dict[str, Any]:
        """Analyze individual user behavior."""
        user_data = []
        user_key = f"user:{profile.user_id}"
        
        if user_key in self.usage_data:
            cutoff_time = datetime.now(timezone.utc) - self._get_timedelta_for_window(time_window)
            user_data = [
                point for point in self.usage_data[user_key]
                if point.timestamp > cutoff_time
            ]
        
        analysis = {
            "user_id": profile.user_id,
            "role": profile.role.value,
            "behavior_type": profile.behavior_type.value,
            "activity_summary": {
                "total_requests": len(user_data),
                "unique_endpoints": len(set(point.endpoint for point in user_data)),
                "avg_response_time": statistics.mean([point.response_time_ms for point in user_data]) if user_data else 0,
                "error_rate": len([p for p in user_data if p.status_code >= 400]) / len(user_data) * 100 if user_data else 0
            },
            "usage_patterns": {
                "most_used_endpoints": self._get_top_endpoints_for_user(user_data),
                "temporal_patterns": self._analyze_user_temporal_patterns(user_data),
                "session_patterns": self._analyze_user_session_patterns(user_data)
            },
            "engagement_score": self._calculate_user_engagement_score(profile, user_data),
            "satisfaction_indicators": self._analyze_user_satisfaction(user_data)
        }
        
        return analysis
    
    async def _analyze_endpoint_usage(self, endpoint: str, usage_points: List[UsageDataPoint], time_window: TimeWindow) -> EndpointUsageAnalysis:
        """Analyze usage patterns for a specific endpoint."""
        
        analysis = EndpointUsageAnalysis(
            endpoint=endpoint,
            route_type=usage_points[0].route_type if usage_points else RouteType.PUBLIC,
            analysis_period_start=datetime.now(timezone.utc) - self._get_timedelta_for_window(time_window),
            analysis_period_end=datetime.now(timezone.utc)
        )
        
        if not usage_points:
            return analysis
        
        # Basic statistics
        analysis.total_requests = len(usage_points)
        analysis.unique_users = len(set(p.user_id for p in usage_points if p.user_id))
        analysis.unique_organizations = len(set(p.organization_id for p in usage_points if p.organization_id))
        
        # Performance metrics
        response_times = [p.response_time_ms for p in usage_points if p.response_time_ms > 0]
        if response_times:
            analysis.avg_response_time = statistics.mean(response_times)
            response_times.sort()
            analysis.p95_response_time = self._percentile(response_times, 95)
        
        # Error analysis
        errors = [p for p in usage_points if p.status_code >= 400]
        analysis.error_rate = len(errors) / len(usage_points) * 100
        analysis.success_rate = 100 - analysis.error_rate
        
        # Distribution analysis
        role_counter = Counter(p.role.value for p in usage_points)
        analysis.role_distribution = dict(role_counter)
        
        org_counter = Counter(p.organization_id for p in usage_points if p.organization_id)
        analysis.organization_distribution = dict(org_counter.most_common(10))
        
        # Temporal analysis
        analysis.peak_hour = self._find_peak_hour(usage_points)
        analysis.peak_day = self._find_peak_day(usage_points)
        analysis.usage_pattern = self.pattern_detector.detect_pattern(usage_points)
        
        # Business metrics
        analysis.category = self._categorize_endpoint_usage(analysis)
        analysis.business_value_score = self._calculate_business_value_score(analysis)
        analysis.adoption_rate = self._calculate_endpoint_adoption_rate(usage_points)
        
        # Trends
        analysis.growth_rate = self._calculate_endpoint_growth_rate(usage_points)
        analysis.usage_trend = self._determine_usage_trend(analysis.growth_rate)
        
        # Optimization opportunities
        analysis.optimization_opportunities = self._identify_endpoint_optimization_opportunities(analysis)
        
        return analysis
    
    def _analyze_hourly_patterns(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze hourly usage patterns."""
        hourly_counts = defaultdict(int)
        
        for point in usage_data:
            hour = point.timestamp.hour
            hourly_counts[hour] += 1
        
        # Find peak and low hours
        peak_hour = max(hourly_counts, key=hourly_counts.get) if hourly_counts else 12
        low_hour = min(hourly_counts, key=hourly_counts.get) if hourly_counts else 3
        
        # Calculate hourly distribution
        total_requests = sum(hourly_counts.values())
        hourly_distribution = {
            hour: (count / total_requests * 100) if total_requests > 0 else 0
            for hour, count in hourly_counts.items()
        }
        
        return {
            "hourly_distribution": dict(hourly_distribution),
            "peak_hour": peak_hour,
            "low_hour": low_hour,
            "peak_to_low_ratio": hourly_counts[peak_hour] / max(hourly_counts[low_hour], 1),
            "business_hours_percentage": sum(
                hourly_distribution.get(hour, 0) for hour in range(9, 17)
            )
        }
    
    def _analyze_daily_patterns(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze daily usage patterns."""
        daily_counts = defaultdict(int)
        
        for point in usage_data:
            day = point.timestamp.weekday()  # 0=Monday, 6=Sunday
            daily_counts[day] += 1
        
        # Convert to human-readable days
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        daily_distribution = {
            day_names[day]: count for day, count in daily_counts.items()
        }
        
        # Find peak day
        peak_day = max(daily_counts, key=daily_counts.get) if daily_counts else 0
        
        # Calculate weekday vs weekend split
        weekday_count = sum(daily_counts[day] for day in range(5))  # Mon-Fri
        weekend_count = sum(daily_counts[day] for day in range(5, 7))  # Sat-Sun
        total = weekday_count + weekend_count
        
        return {
            "daily_distribution": daily_distribution,
            "peak_day": day_names[peak_day],
            "weekday_percentage": (weekday_count / total * 100) if total > 0 else 0,
            "weekend_percentage": (weekend_count / total * 100) if total > 0 else 0
        }
    
    def _calculate_user_engagement_score(self, profile: UserUsageProfile, recent_data: List[UsageDataPoint]) -> float:
        """Calculate user engagement score (0-100)."""
        if not recent_data:
            return 0.0
        
        # Factors for engagement calculation
        request_frequency_score = min(len(recent_data) / 100, 1.0) * 30  # Max 30 points
        endpoint_diversity_score = min(len(set(p.endpoint for p in recent_data)) / 20, 1.0) * 25  # Max 25 points
        feature_usage_score = min(sum(len(p.features_used) for p in recent_data) / 50, 1.0) * 20  # Max 20 points
        
        # Performance-based engagement (lower response times = higher engagement)
        avg_response_time = statistics.mean([p.response_time_ms for p in recent_data if p.response_time_ms > 0])
        performance_score = max(0, 25 - (avg_response_time / 1000 * 5))  # Max 25 points
        
        return min(request_frequency_score + endpoint_diversity_score + feature_usage_score + performance_score, 100.0)
    
    def _generate_user_analytics_summary(self, user_analytics: List[Dict[str, Any]], role: Optional[PlatformRole]) -> Dict[str, Any]:
        """Generate summary statistics for user analytics."""
        if not user_analytics:
            return {}
        
        total_users = len(user_analytics)
        total_requests = sum(user["activity_summary"]["total_requests"] for user in user_analytics)
        
        # Engagement distribution
        engagement_scores = [user["engagement_score"] for user in user_analytics]
        high_engagement = len([score for score in engagement_scores if score > 70])
        medium_engagement = len([score for score in engagement_scores if 30 <= score <= 70])
        low_engagement = len([score for score in engagement_scores if score < 30])
        
        # Behavior distribution
        behavior_distribution = Counter(user["behavior_type"] for user in user_analytics)
        
        return {
            "total_users": total_users,
            "total_requests": total_requests,
            "avg_requests_per_user": total_requests / total_users if total_users > 0 else 0,
            "engagement_distribution": {
                "high_engagement": high_engagement,
                "medium_engagement": medium_engagement,
                "low_engagement": low_engagement,
                "avg_engagement_score": statistics.mean(engagement_scores) if engagement_scores else 0
            },
            "behavior_distribution": dict(behavior_distribution),
            "role_analyzed": role.value if role else "all"
        }
    
    def _initialize_analytics(self):
        """Initialize analytics components."""
        if self.enable_real_time_analytics:
            # Start real-time analytics background task
            task = asyncio.create_task(self._real_time_analytics_loop())
            self.analytics_tasks.append(task)
        
        self.logger.info("Analytics initialization completed")
    
    async def _real_time_analytics_loop(self):
        """Background loop for real-time analytics updates."""
        while True:
            try:
                # Update real-time statistics
                await self._update_all_real_time_stats()
                
                # Generate real-time insights
                if len(self.usage_data) > 0:
                    await self._refresh_real_time_insights()
                
                # Sleep for next iteration
                await asyncio.sleep(60)  # Update every minute
                
            except Exception as e:
                self.logger.error(f"Real-time analytics error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _update_real_time_stats(self, usage_point: UsageDataPoint):
        """Update real-time statistics with new usage point."""
        current_minute = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        minute_key = current_minute.isoformat()
        
        if minute_key not in self.real_time_stats:
            self.real_time_stats[minute_key] = {
                "requests": 0,
                "unique_users": set(),
                "endpoints": defaultdict(int),
                "roles": defaultdict(int),
                "errors": 0
            }
        
        stats = self.real_time_stats[minute_key]
        stats["requests"] += 1
        if usage_point.user_id:
            stats["unique_users"].add(usage_point.user_id)
        stats["endpoints"][usage_point.endpoint] += 1
        stats["roles"][usage_point.role.value] += 1
        if usage_point.status_code >= 400:
            stats["errors"] += 1
        
        # Clean up old stats (keep last 60 minutes)
        cutoff_time = current_minute - timedelta(minutes=60)
        old_keys = [key for key in self.real_time_stats.keys() if datetime.fromisoformat(key) < cutoff_time]
        for key in old_keys:
            del self.real_time_stats[key]
    
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
        return window_map.get(window, timedelta(days=7))
    
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
    
    def _endpoint_analysis_to_dict(self, analysis: EndpointUsageAnalysis) -> Dict[str, Any]:
        """Convert endpoint analysis to dictionary."""
        return {
            "endpoint": analysis.endpoint,
            "route_type": analysis.route_type.value,
            "total_requests": analysis.total_requests,
            "unique_users": analysis.unique_users,
            "unique_organizations": analysis.unique_organizations,
            "avg_response_time": analysis.avg_response_time,
            "p95_response_time": analysis.p95_response_time,
            "error_rate": analysis.error_rate,
            "success_rate": analysis.success_rate,
            "category": analysis.category.value,
            "business_value_score": analysis.business_value_score,
            "usage_pattern": analysis.usage_pattern.value,
            "growth_rate": analysis.growth_rate,
            "optimization_opportunities": analysis.optimization_opportunities
        }
    
    # Placeholder methods for advanced analytics features
    async def _collect_endpoint_usage_data(self, **kwargs) -> List[UsageDataPoint]:
        """Collect endpoint usage data for analysis."""
        # Implementation would collect and filter usage data
        return []
    
    async def _collect_usage_data_for_period(self, **kwargs) -> List[UsageDataPoint]:
        """Collect usage data for a specific time period."""
        # Implementation would collect usage data for temporal analysis
        return []
    
    async def _collect_feature_usage_data(self, role: Optional[PlatformRole], time_window: TimeWindow) -> List[UsageDataPoint]:
        """Collect feature usage data for analysis."""
        # Implementation would collect feature-specific usage data
        return []
    
    async def _collect_business_intelligence_data(self, role: Optional[PlatformRole], time_window: TimeWindow) -> Dict[str, Any]:
        """Collect comprehensive data for business intelligence."""
        # Implementation would collect BI-relevant data
        return {}
    
    # Additional placeholder methods for comprehensive analytics
    def _analyze_weekly_patterns(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze weekly usage patterns."""
        return {"weekly_trend": "stable"}
    
    def _analyze_seasonal_patterns(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze seasonal usage patterns."""
        return {"seasonal_trend": "stable"}
    
    def _detect_usage_peaks(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Detect usage peaks and anomalies."""
        return {"peaks_detected": []}
    
    def _analyze_usage_trends(self, usage_data: List[UsageDataPoint]) -> Dict[str, Any]:
        """Analyze overall usage trends."""
        return {"trend": "stable"}


class UsagePatternDetector:
    """Detects usage patterns in API data."""
    
    def detect_pattern(self, usage_points: List[UsageDataPoint]) -> UsagePattern:
        """Detect usage pattern from data points."""
        if len(usage_points) < 10:
            return UsagePattern.IRREGULAR
        
        # Simple pattern detection logic
        hourly_distribution = defaultdict(int)
        for point in usage_points:
            hourly_distribution[point.timestamp.hour] += 1
        
        # Check for peak hours pattern
        peak_hours = [hour for hour, count in hourly_distribution.items() if count > statistics.mean(hourly_distribution.values())]
        
        if len(peak_hours) >= 6 and all(9 <= hour <= 17 for hour in peak_hours):
            return UsagePattern.PEAK_HOURS
        
        # Check for steady pattern
        variance = statistics.variance(hourly_distribution.values()) if len(hourly_distribution) > 1 else 0
        if variance < statistics.mean(hourly_distribution.values()) * 0.2:
            return UsagePattern.STEADY
        
        return UsagePattern.IRREGULAR


class UserBehaviorAnalyzer:
    """Analyzes and classifies user behavior patterns."""
    
    def classify_user_behavior(self, profile: UserUsageProfile) -> UserBehavior:
        """Classify user behavior based on usage profile."""
        if profile.total_requests > 1000:
            return UserBehavior.HEAVY_USER
        elif profile.total_requests > 100:
            return UserBehavior.MODERATE_USER
        elif profile.total_requests > 10:
            return UserBehavior.LIGHT_USER
        else:
            return UserBehavior.OCCASIONAL_USER


class UsageInsightGenerator:
    """Generates actionable insights from usage analytics."""
    
    async def generate_insights(self, analytics_data: Dict[str, Any]) -> List[UsageInsight]:
        """Generate usage insights from analytics data."""
        insights = []
        
        # Example insight generation logic
        if analytics_data.get("error_rate", 0) > 5:
            insights.append(UsageInsight(
                insight_type="performance",
                title="High Error Rate Detected",
                description="API error rate is above acceptable threshold",
                impact_score=80.0,
                confidence_level=0.9,
                recommendations=["Investigate error causes", "Improve error handling"],
                priority="high"
            ))
        
        return insights


# Factory function
def create_usage_analytics(**kwargs) -> UsageAnalytics:
    """Factory function to create UsageAnalytics."""
    return UsageAnalytics(**kwargs)