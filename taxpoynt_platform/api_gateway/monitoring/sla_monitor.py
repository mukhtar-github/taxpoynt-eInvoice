"""
SLA Compliance Monitoring System
================================
Comprehensive SLA monitoring and compliance tracking for role-based APIs in TaxPoynt platform.
Monitors uptime, response time SLAs, availability targets, and generates compliance reports.
"""
import uuid
import logging
import asyncio
import statistics
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, DefaultDict
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json
import math

from ..role_routing.models import HTTPRoutingContext, PlatformRole, RouteType, HTTPMethod
from .role_metrics import TimeWindow, RoleMetricsCollector, RoleMetricPoint
from .performance_tracker import PerformanceTracker, PerformanceDataPoint
from ...core_platform.authentication.role_manager import ServiceRole

logger = logging.getLogger(__name__)


class SLAMetricType(Enum):
    """Types of SLA metrics to monitor."""
    UPTIME = "uptime"
    AVAILABILITY = "availability"
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    RECOVERY_TIME = "recovery_time"
    DATA_ACCURACY = "data_accuracy"
    SECURITY_COMPLIANCE = "security_compliance"


class SLAStatus(Enum):
    """SLA compliance status."""
    MEETING = "meeting"
    AT_RISK = "at_risk"
    BREACHED = "breached"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class IncidentSeverity(Enum):
    """Incident severity levels."""
    CRITICAL = "critical"  # Complete service outage
    HIGH = "high"         # Major functionality impacted
    MEDIUM = "medium"     # Minor functionality impacted
    LOW = "low"          # Minimal impact
    INFO = "info"        # Informational only


class IncidentStatus(Enum):
    """Incident status."""
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class SLATarget:
    """SLA target definition."""
    sla_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Scope
    role: PlatformRole
    route_type: RouteType
    endpoints: List[str] = field(default_factory=list)  # Empty means all endpoints
    
    # Metric definition
    metric_type: SLAMetricType
    target_value: float = 0.0
    unit: str = ""
    direction: str = "max"  # "max" for <= target, "min" for >= target
    
    # Evaluation configuration
    measurement_window: TimeWindow = TimeWindow.HOUR
    evaluation_frequency: int = 5  # minutes
    grace_period_minutes: int = 15
    
    # Thresholds
    warning_threshold: float = 0.0  # Percentage of target (e.g., 90% = 0.9)
    critical_threshold: float = 0.0  # Percentage of target (e.g., 80% = 0.8)
    
    # Business configuration
    business_hours_only: bool = False
    maintenance_windows: List[Dict[str, Any]] = field(default_factory=list)
    
    # Notification configuration
    notify_on_breach: bool = True
    notification_channels: List[str] = field(default_factory=list)
    escalation_chain: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class SLAMeasurement:
    """Single SLA measurement."""
    measurement_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # SLA reference
    sla_target: SLATarget
    
    # Measurement details
    measured_value: float = 0.0
    target_value: float = 0.0
    compliance_percentage: float = 100.0
    status: SLAStatus = SLAStatus.MEETING
    
    # Measurement context
    measurement_window_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    measurement_window_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sample_size: int = 0
    
    # Breach information
    breach_duration_minutes: float = 0.0
    breach_magnitude: float = 0.0  # How far from target
    
    # Supporting data
    supporting_metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SLAIncident:
    """SLA incident record."""
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Incident details
    title: str = ""
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    status: IncidentStatus = IncidentStatus.OPEN
    
    # SLA context
    affected_slas: List[str] = field(default_factory=list)  # SLA IDs
    affected_roles: List[PlatformRole] = field(default_factory=list)
    affected_endpoints: List[str] = field(default_factory=list)
    
    # Impact assessment
    estimated_affected_users: int = 0
    business_impact: str = "medium"
    revenue_impact: Optional[float] = None
    
    # Timeline
    detected_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Resolution details
    root_cause: str = ""
    resolution_summary: str = ""
    preventive_actions: List[str] = field(default_factory=list)
    
    # Communication
    status_updates: List[Dict[str, Any]] = field(default_factory=list)
    assigned_to: Optional[str] = None
    
    # Metrics
    detection_time_minutes: float = 0.0
    resolution_time_minutes: float = 0.0
    customer_impact_score: float = 0.0
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    external_references: List[str] = field(default_factory=list)


@dataclass
class SLAReport:
    """SLA compliance report."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Report scope
    report_type: str = "compliance"  # compliance, incident, trend
    role: Optional[PlatformRole] = None
    period_start: datetime = field(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=30))
    period_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Overall compliance
    overall_compliance_percentage: float = 100.0
    total_slas_monitored: int = 0
    slas_meeting_target: int = 0
    slas_at_risk: int = 0
    slas_breached: int = 0
    
    # SLA-specific results
    sla_results: List[Dict[str, Any]] = field(default_factory=list)
    
    # Incident summary
    total_incidents: int = 0
    critical_incidents: int = 0
    average_resolution_time_hours: float = 0.0
    
    # Trend analysis
    compliance_trend: str = "stable"  # improving, degrading, stable
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metrics summary
    uptime_percentage: float = 100.0
    average_response_time_ms: float = 0.0
    error_rate_percentage: float = 0.0
    
    # Business impact
    estimated_downtime_cost: Optional[float] = None
    user_impact_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Report metadata
    generated_by: Optional[str] = None
    report_format: str = "json"
    distribution_list: List[str] = field(default_factory=list)


class SLAMonitor:
    """
    SLA Compliance Monitoring System
    ===============================
    
    **Core Features:**
    - Real-time SLA monitoring across all roles (SI, APP, HYBRID)
    - Automated compliance measurement and breach detection
    - Incident management with root cause analysis
    - Comprehensive reporting and trend analysis
    - Business impact assessment and cost calculation
    
    **SLA Categories:**
    - Availability SLAs: Uptime targets (99.9%, 99.95%, 99.99%)
    - Performance SLAs: Response time targets by role and endpoint
    - Quality SLAs: Error rate and data accuracy targets
    - Recovery SLAs: Incident detection and resolution times
    
    **Monitoring Capabilities:**
    - Continuous measurement with configurable windows
    - Predictive breach detection and early warnings
    - Automated incident creation and escalation
    - Historical compliance tracking and reporting
    """
    
    def __init__(
        self,
        metrics_collector: Optional[RoleMetricsCollector] = None,
        performance_tracker: Optional[PerformanceTracker] = None,
        enable_automated_incident_creation: bool = True,
        enable_predictive_monitoring: bool = False,
        default_measurement_interval_minutes: int = 5,
        breach_notification_delay_minutes: int = 15
    ):
        self.logger = logging.getLogger(__name__)
        
        # Dependencies
        self.metrics_collector = metrics_collector
        self.performance_tracker = performance_tracker
        
        # Configuration
        self.enable_automated_incident_creation = enable_automated_incident_creation
        self.enable_predictive_monitoring = enable_predictive_monitoring
        self.default_measurement_interval_minutes = default_measurement_interval_minutes
        self.breach_notification_delay_minutes = breach_notification_delay_minutes
        
        # SLA management
        self.sla_targets: Dict[str, SLATarget] = {}
        self.sla_measurements: DefaultDict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.active_incidents: Dict[str, SLAIncident] = {}
        self.incident_history: deque = deque(maxlen=50000)
        
        # Monitoring state
        self.monitoring_tasks: List[asyncio.Task] = []
        self.last_measurement_time: Dict[str, datetime] = {}
        self.breach_timers: Dict[str, datetime] = {}
        
        # Compliance tracking
        self.compliance_cache: Dict[str, Dict[str, Any]] = {}
        self.trend_analyzer = SLATrendAnalyzer()
        
        # Business impact calculator
        self.impact_calculator = BusinessImpactCalculator()
        
        # Initialize default SLAs
        self._initialize_default_slas()
        
        # Start monitoring
        self._start_monitoring()
        
        logger.info("SLAMonitor initialized")
    
    async def define_sla(
        self,
        name: str,
        role: PlatformRole,
        route_type: RouteType,
        metric_type: SLAMetricType,
        target_value: float,
        unit: str = "",
        **kwargs
    ) -> str:
        """Define a new SLA target."""
        
        sla_target = SLATarget(
            name=name,
            role=role,
            route_type=route_type,
            metric_type=metric_type,
            target_value=target_value,
            unit=unit,
            **kwargs
        )
        
        self.sla_targets[sla_target.sla_id] = sla_target
        
        # Start monitoring this SLA
        await self._start_sla_monitoring(sla_target)
        
        self.logger.info(f"Defined SLA: {name} for {role.value} - Target: {target_value} {unit}")
        return sla_target.sla_id
    
    async def measure_sla_compliance(
        self,
        sla_id: str,
        force_measurement: bool = False
    ) -> Optional[SLAMeasurement]:
        """Measure compliance for a specific SLA."""
        
        if sla_id not in self.sla_targets:
            self.logger.warning(f"Unknown SLA ID: {sla_id}")
            return None
        
        sla_target = self.sla_targets[sla_id]
        
        # Check if measurement is due
        last_measurement = self.last_measurement_time.get(sla_id)
        if not force_measurement and last_measurement:
            time_since_last = datetime.now(timezone.utc) - last_measurement
            if time_since_last.total_seconds() < sla_target.evaluation_frequency * 60:
                return None
        
        # Collect measurement data
        measurement_data = await self._collect_sla_measurement_data(sla_target)
        
        if not measurement_data:
            self.logger.warning(f"No data available for SLA measurement: {sla_id}")
            return None
        
        # Calculate measured value
        measured_value = await self._calculate_measured_value(sla_target, measurement_data)
        
        # Determine compliance status
        compliance_percentage, status = self._calculate_compliance_status(
            sla_target, measured_value
        )
        
        # Create measurement record
        measurement = SLAMeasurement(
            sla_target=sla_target,
            measured_value=measured_value,
            target_value=sla_target.target_value,
            compliance_percentage=compliance_percentage,
            status=status,
            measurement_window_start=measurement_data["window_start"],
            measurement_window_end=measurement_data["window_end"],
            sample_size=measurement_data["sample_size"],
            supporting_metrics=measurement_data.get("supporting_metrics", {})
        )
        
        # Store measurement
        self.sla_measurements[sla_id].append(measurement)
        self.last_measurement_time[sla_id] = datetime.now(timezone.utc)
        
        # Check for SLA breaches
        await self._check_sla_breach(measurement)
        
        # Update compliance cache
        await self._update_compliance_cache(sla_id, measurement)
        
        self.logger.debug(
            f"SLA measurement: {sla_target.name} - "
            f"Value: {measured_value} ({compliance_percentage:.1f}% compliant)"
        )
        
        return measurement
    
    async def get_sla_status(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.DAY
    ) -> Dict[str, Any]:
        """Get current SLA compliance status."""
        
        # Filter SLAs by role if specified
        target_slas = []
        for sla_target in self.sla_targets.values():
            if not role or sla_target.role == role:
                target_slas.append(sla_target)
        
        # Collect compliance data
        compliance_data = []
        for sla_target in target_slas:
            recent_measurements = await self._get_recent_measurements(
                sla_target.sla_id, time_window
            )
            
            if recent_measurements:
                latest_measurement = recent_measurements[-1]
                compliance_data.append({
                    "sla_id": sla_target.sla_id,
                    "name": sla_target.name,
                    "role": sla_target.role.value,
                    "metric_type": sla_target.metric_type.value,
                    "target_value": sla_target.target_value,
                    "current_value": latest_measurement.measured_value,
                    "compliance_percentage": latest_measurement.compliance_percentage,
                    "status": latest_measurement.status.value,
                    "last_measured": latest_measurement.timestamp.isoformat()
                })
        
        # Calculate overall compliance
        if compliance_data:
            overall_compliance = statistics.mean([
                item["compliance_percentage"] for item in compliance_data
            ])
            
            status_counts = defaultdict(int)
            for item in compliance_data:
                status_counts[item["status"]] += 1
        else:
            overall_compliance = 100.0
            status_counts = {}
        
        # Get active incidents
        active_incidents = [
            self._incident_to_dict(incident) 
            for incident in self.active_incidents.values()
            if incident.status != IncidentStatus.CLOSED
        ]
        
        return {
            "overall_compliance_percentage": overall_compliance,
            "total_slas": len(compliance_data),
            "status_distribution": dict(status_counts),
            "sla_details": compliance_data,
            "active_incidents": active_incidents,
            "analysis_metadata": {
                "role_filter": role.value if role else "all",
                "time_window": time_window.value,
                "analyzed_at": datetime.now(timezone.utc).isoformat()
            }
        }
    
    async def create_incident(
        self,
        title: str,
        description: str,
        severity: IncidentSeverity,
        affected_slas: List[str],
        **kwargs
    ) -> str:
        """Create a new SLA incident."""
        
        incident = SLAIncident(
            title=title,
            description=description,
            severity=severity,
            affected_slas=affected_slas,
            detected_at=datetime.now(timezone.utc),
            **kwargs
        )
        
        # Determine affected roles and endpoints
        affected_roles = set()
        affected_endpoints = set()
        
        for sla_id in affected_slas:
            if sla_id in self.sla_targets:
                sla_target = self.sla_targets[sla_id]
                affected_roles.add(sla_target.role)
                affected_endpoints.update(sla_target.endpoints)
        
        incident.affected_roles = list(affected_roles)
        incident.affected_endpoints = list(affected_endpoints)
        
        # Store incident
        self.active_incidents[incident.incident_id] = incident
        
        # Calculate business impact
        incident.business_impact = await self._calculate_incident_business_impact(incident)
        
        # Send notifications if configured
        await self._send_incident_notifications(incident, "created")
        
        self.logger.warning(f"SLA incident created: {title} (Severity: {severity.value})")
        return incident.incident_id
    
    async def update_incident(
        self,
        incident_id: str,
        status: Optional[IncidentStatus] = None,
        description_update: Optional[str] = None,
        **kwargs
    ) -> bool:
        """Update an existing incident."""
        
        if incident_id not in self.active_incidents:
            self.logger.warning(f"Unknown incident ID: {incident_id}")
            return False
        
        incident = self.active_incidents[incident_id]
        old_status = incident.status
        
        # Update incident fields
        if status:
            incident.status = status
            
            # Set timestamps based on status
            if status == IncidentStatus.INVESTIGATING and not incident.acknowledged_at:
                incident.acknowledged_at = datetime.now(timezone.utc)
            elif status == IncidentStatus.RESOLVED and not incident.resolved_at:
                incident.resolved_at = datetime.now(timezone.utc)
                incident.resolution_time_minutes = (
                    incident.resolved_at - incident.created_at
                ).total_seconds() / 60
            elif status == IncidentStatus.CLOSED and not incident.closed_at:
                incident.closed_at = datetime.now(timezone.utc)
                # Move to history
                self.incident_history.append(incident)
                del self.active_incidents[incident_id]
        
        if description_update:
            incident.status_updates.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "update": description_update,
                "updated_by": kwargs.get("updated_by", "system")
            })
        
        # Update other fields
        for key, value in kwargs.items():
            if hasattr(incident, key):
                setattr(incident, key, value)
        
        # Send notifications on status change
        if status and status != old_status:
            await self._send_incident_notifications(incident, "updated")
        
        self.logger.info(f"Incident updated: {incident_id} - Status: {status.value if status else 'unchanged'}")
        return True
    
    async def generate_sla_report(
        self,
        report_type: str = "compliance",
        role: Optional[PlatformRole] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
        **kwargs
    ) -> SLAReport:
        """Generate comprehensive SLA report."""
        
        if not period_end:
            period_end = datetime.now(timezone.utc)
        if not period_start:
            period_start = period_end - timedelta(days=30)
        
        report = SLAReport(
            report_type=report_type,
            role=role,
            period_start=period_start,
            period_end=period_end,
            **kwargs
        )
        
        # Collect SLA results for the period
        sla_results = []
        total_slas = 0
        meeting_target = 0
        at_risk = 0
        breached = 0
        
        for sla_target in self.sla_targets.values():
            if role and sla_target.role != role:
                continue
            
            total_slas += 1
            
            # Get measurements for the period
            period_measurements = await self._get_measurements_for_period(
                sla_target.sla_id, period_start, period_end
            )
            
            if period_measurements:
                # Calculate period compliance
                compliance_percentages = [m.compliance_percentage for m in period_measurements]
                avg_compliance = statistics.mean(compliance_percentages)
                
                # Determine period status
                if avg_compliance >= 95:
                    meeting_target += 1
                    period_status = "meeting"
                elif avg_compliance >= 85:
                    at_risk += 1
                    period_status = "at_risk"
                else:
                    breached += 1
                    period_status = "breached"
                
                sla_results.append({
                    "sla_id": sla_target.sla_id,
                    "name": sla_target.name,
                    "metric_type": sla_target.metric_type.value,
                    "target_value": sla_target.target_value,
                    "average_compliance": avg_compliance,
                    "period_status": period_status,
                    "measurement_count": len(period_measurements),
                    "trend": self.trend_analyzer.analyze_sla_trend(period_measurements)
                })
        
        # Update report statistics
        report.total_slas_monitored = total_slas
        report.slas_meeting_target = meeting_target
        report.slas_at_risk = at_risk
        report.slas_breached = breached
        report.overall_compliance_percentage = (meeting_target / total_slas * 100) if total_slas > 0 else 100
        report.sla_results = sla_results
        
        # Incident analysis for the period
        period_incidents = await self._get_incidents_for_period(period_start, period_end)
        report.total_incidents = len(period_incidents)
        report.critical_incidents = len([i for i in period_incidents if i.severity == IncidentSeverity.CRITICAL])
        
        if period_incidents:
            resolution_times = [
                i.resolution_time_minutes for i in period_incidents 
                if i.resolution_time_minutes > 0
            ]
            report.average_resolution_time_hours = statistics.mean(resolution_times) / 60 if resolution_times else 0
        
        # Generate insights and recommendations
        report.key_insights = await self._generate_report_insights(sla_results, period_incidents)
        report.recommendations = await self._generate_report_recommendations(sla_results, period_incidents)
        
        # Business impact analysis
        if report_type == "business_impact":
            report.estimated_downtime_cost = await self._calculate_period_downtime_cost(
                period_incidents, period_start, period_end
            )
            report.user_impact_summary = await self._calculate_user_impact_summary(
                period_incidents, role
            )
        
        self.logger.info(f"Generated SLA report: {report_type} for {role.value if role else 'all roles'}")
        return report
    
    async def get_uptime_statistics(
        self,
        role: Optional[PlatformRole] = None,
        time_window: TimeWindow = TimeWindow.DAY
    ) -> Dict[str, Any]:
        """Get uptime and availability statistics."""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - self._get_timedelta_for_window(time_window)
        
        # Collect uptime data
        uptime_data = await self._collect_uptime_data(role, start_time, end_time)
        
        # Calculate availability metrics
        total_time_minutes = (end_time - start_time).total_seconds() / 60
        downtime_minutes = uptime_data.get("total_downtime_minutes", 0)
        uptime_minutes = total_time_minutes - downtime_minutes
        
        availability_percentage = (uptime_minutes / total_time_minutes * 100) if total_time_minutes > 0 else 100
        
        # Calculate MTTR and MTBF
        incidents = uptime_data.get("incidents", [])
        if incidents:
            resolution_times = [i.get("resolution_time_minutes", 0) for i in incidents if i.get("resolution_time_minutes", 0) > 0]
            mttr_minutes = statistics.mean(resolution_times) if resolution_times else 0
            
            # Mean Time Between Failures
            if len(incidents) > 1:
                time_between_incidents = [
                    (incidents[i]["start_time"] - incidents[i-1]["end_time"]).total_seconds() / 60
                    for i in range(1, len(incidents))
                    if incidents[i-1].get("end_time")
                ]
                mtbf_minutes = statistics.mean(time_between_incidents) if time_between_incidents else 0
            else:
                mtbf_minutes = total_time_minutes
        else:
            mttr_minutes = 0
            mtbf_minutes = total_time_minutes
        
        return {
            "availability_percentage": availability_percentage,
            "uptime_minutes": uptime_minutes,
            "downtime_minutes": downtime_minutes,
            "total_incidents": len(incidents),
            "mttr_minutes": mttr_minutes,
            "mtbf_minutes": mtbf_minutes,
            "uptime_sla_target": self._get_uptime_sla_target(role),
            "sla_compliance": availability_percentage >= self._get_uptime_sla_target(role),
            "analysis_period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "window": time_window.value
            }
        }
    
    def _initialize_default_slas(self):
        """Initialize default SLA targets for all roles."""
        default_slas = [
            # Availability SLAs
            {
                "name": "SI API Availability",
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": SLAMetricType.AVAILABILITY,
                "target_value": 99.9,  # 99.9% uptime
                "unit": "%",
                "direction": "min",
                "warning_threshold": 0.95,  # 95% of target = 99.855%
                "critical_threshold": 0.90   # 90% of target = 99.81%
            },
            {
                "name": "APP API Availability", 
                "role": PlatformRole.ACCESS_POINT_PROVIDER,
                "route_type": RouteType.APP_ONLY,
                "metric_type": SLAMetricType.AVAILABILITY,
                "target_value": 99.95,  # 99.95% uptime
                "unit": "%",
                "direction": "min",
                "warning_threshold": 0.95,
                "critical_threshold": 0.90
            },
            # Response Time SLAs
            {
                "name": "SI API Response Time",
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": SLAMetricType.RESPONSE_TIME,
                "target_value": 2000,  # 2 seconds
                "unit": "ms",
                "direction": "max",
                "warning_threshold": 1.2,  # 120% of target = 2.4s
                "critical_threshold": 1.5   # 150% of target = 3s
            },
            {
                "name": "APP API Response Time",
                "role": PlatformRole.ACCESS_POINT_PROVIDER,
                "route_type": RouteType.APP_ONLY,
                "metric_type": SLAMetricType.RESPONSE_TIME,
                "target_value": 1000,  # 1 second
                "unit": "ms",
                "direction": "max",
                "warning_threshold": 1.2,
                "critical_threshold": 1.5
            },
            # Error Rate SLAs
            {
                "name": "SI API Error Rate",
                "role": PlatformRole.SYSTEM_INTEGRATOR,
                "route_type": RouteType.SI_ONLY,
                "metric_type": SLAMetricType.ERROR_RATE,
                "target_value": 1.0,  # 1% max error rate
                "unit": "%",
                "direction": "max",
                "warning_threshold": 1.5,  # 150% of target = 1.5%
                "critical_threshold": 2.0   # 200% of target = 2%
            }
        ]
        
        for sla_config in default_slas:
            sla_target = SLATarget(**sla_config)
            self.sla_targets[sla_target.sla_id] = sla_target
        
        self.logger.info(f"Initialized {len(default_slas)} default SLA targets")
    
    def _start_monitoring(self):
        """Start SLA monitoring background tasks."""
        # Start main monitoring loop
        task = asyncio.create_task(self._monitoring_loop())
        self.monitoring_tasks.append(task)
        
        # Start incident detection loop
        if self.enable_automated_incident_creation:
            task = asyncio.create_task(self._incident_detection_loop())
            self.monitoring_tasks.append(task)
        
        self.logger.info("SLA monitoring started")
    
    async def _monitoring_loop(self):
        """Main SLA monitoring loop."""
        while True:
            try:
                # Measure all enabled SLAs
                for sla_id, sla_target in self.sla_targets.items():
                    if sla_target.enabled:
                        await self.measure_sla_compliance(sla_id)
                
                # Wait for next iteration
                await asyncio.sleep(self.default_measurement_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"SLA monitoring loop error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _incident_detection_loop(self):
        """Automated incident detection loop."""
        while True:
            try:
                # Check for new incidents based on SLA breaches
                await self._detect_new_incidents()
                
                # Check for incident auto-resolution
                await self._check_incident_auto_resolution()
                
                # Wait for next check
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Incident detection loop error: {str(e)}")
                await asyncio.sleep(300)
    
    async def _collect_sla_measurement_data(self, sla_target: SLATarget) -> Optional[Dict[str, Any]]:
        """Collect data needed for SLA measurement."""
        
        end_time = datetime.now(timezone.utc)
        start_time = end_time - self._get_timedelta_for_window(sla_target.measurement_window)
        
        # Skip measurement during maintenance windows
        if self._is_in_maintenance_window(sla_target, end_time):
            return None
        
        # Skip if business hours only and currently outside business hours
        if sla_target.business_hours_only and not self._is_business_hours(end_time):
            return None
        
        measurement_data = {
            "window_start": start_time,
            "window_end": end_time,
            "sample_size": 0,
            "supporting_metrics": {}
        }
        
        # Collect data based on metric type
        if sla_target.metric_type == SLAMetricType.RESPONSE_TIME:
            data = await self._collect_response_time_data(sla_target, start_time, end_time)
        elif sla_target.metric_type == SLAMetricType.AVAILABILITY:
            data = await self._collect_availability_data(sla_target, start_time, end_time)
        elif sla_target.metric_type == SLAMetricType.ERROR_RATE:
            data = await self._collect_error_rate_data(sla_target, start_time, end_time)
        elif sla_target.metric_type == SLAMetricType.THROUGHPUT:
            data = await self._collect_throughput_data(sla_target, start_time, end_time)
        else:
            self.logger.warning(f"Unsupported SLA metric type: {sla_target.metric_type}")
            return None
        
        if data:
            measurement_data.update(data)
            return measurement_data
        
        return None
    
    async def _calculate_measured_value(self, sla_target: SLATarget, measurement_data: Dict[str, Any]) -> float:
        """Calculate the measured value for an SLA."""
        return measurement_data.get("measured_value", 0.0)
    
    def _calculate_compliance_status(self, sla_target: SLATarget, measured_value: float) -> Tuple[float, SLAStatus]:
        """Calculate compliance percentage and status."""
        
        target = sla_target.target_value
        
        if sla_target.direction == "min":
            # For minimum targets (e.g., availability), higher is better
            if measured_value >= target:
                compliance_percentage = 100.0
                status = SLAStatus.MEETING
            else:
                compliance_percentage = (measured_value / target) * 100
                if compliance_percentage >= target * sla_target.warning_threshold:
                    status = SLAStatus.AT_RISK
                else:
                    status = SLAStatus.BREACHED
        else:
            # For maximum targets (e.g., response time), lower is better
            if measured_value <= target:
                compliance_percentage = 100.0
                status = SLAStatus.MEETING
            else:
                compliance_percentage = max(0, 100 - ((measured_value - target) / target) * 100)
                if measured_value <= target * sla_target.warning_threshold:
                    status = SLAStatus.AT_RISK
                elif measured_value <= target * sla_target.critical_threshold:
                    status = SLAStatus.BREACHED
                else:
                    status = SLAStatus.CRITICAL
        
        return compliance_percentage, status
    
    async def _check_sla_breach(self, measurement: SLAMeasurement):
        """Check if measurement indicates an SLA breach and handle accordingly."""
        
        sla_id = measurement.sla_target.sla_id
        
        if measurement.status in [SLAStatus.BREACHED, SLAStatus.CRITICAL]:
            # Check if this is a new breach or continuation
            if sla_id not in self.breach_timers:
                # New breach detected
                self.breach_timers[sla_id] = measurement.timestamp
                self.logger.warning(f"SLA breach detected: {measurement.sla_target.name}")
            else:
                # Ongoing breach - check if grace period exceeded
                breach_duration = (measurement.timestamp - self.breach_timers[sla_id]).total_seconds() / 60
                
                if breach_duration >= measurement.sla_target.grace_period_minutes:
                    # Grace period exceeded - create incident if automated
                    if (self.enable_automated_incident_creation and 
                        not self._has_active_incident_for_sla(sla_id)):
                        
                        await self._create_automated_incident(measurement, breach_duration)
        else:
            # SLA is meeting target - clear breach timer
            if sla_id in self.breach_timers:
                del self.breach_timers[sla_id]
                self.logger.info(f"SLA breach resolved: {measurement.sla_target.name}")
    
    def _has_active_incident_for_sla(self, sla_id: str) -> bool:
        """Check if there's an active incident for this SLA."""
        for incident in self.active_incidents.values():
            if (sla_id in incident.affected_slas and 
                incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]):
                return True
        return False
    
    async def _create_automated_incident(self, measurement: SLAMeasurement, breach_duration: float):
        """Create an automated incident for SLA breach."""
        
        severity = IncidentSeverity.HIGH if measurement.status == SLAStatus.CRITICAL else IncidentSeverity.MEDIUM
        
        title = f"SLA Breach: {measurement.sla_target.name}"
        description = (
            f"SLA target breached for {breach_duration:.1f} minutes. "
            f"Target: {measurement.target_value} {measurement.sla_target.unit}, "
            f"Measured: {measurement.measured_value:.2f} {measurement.sla_target.unit} "
            f"({measurement.compliance_percentage:.1f}% compliant)"
        )
        
        incident_id = await self.create_incident(
            title=title,
            description=description,
            severity=severity,
            affected_slas=[measurement.sla_target.sla_id],
            detected_at=measurement.timestamp
        )
        
        self.logger.warning(f"Automated incident created: {incident_id}")
    
    # Placeholder methods for data collection (would integrate with actual metrics systems)
    async def _collect_response_time_data(self, sla_target: SLATarget, start_time: datetime, end_time: datetime) -> Optional[Dict[str, Any]]:
        """Collect response time data for SLA measurement."""
        # In production, this would query the performance tracker or metrics collector
        # For now, return simulated data
        import random
        
        # Simulate response time data
        simulated_times = [random.uniform(500, 3000) for _ in range(100)]
        avg_response_time = statistics.mean(simulated_times)
        
        return {
            "measured_value": avg_response_time,
            "sample_size": len(simulated_times),
            "supporting_metrics": {
                "p95_response_time": sorted(simulated_times)[94],
                "max_response_time": max(simulated_times),
                "min_response_time": min(simulated_times)
            }
        }
    
    async def _collect_availability_data(self, sla_target: SLATarget, start_time: datetime, end_time: datetime) -> Optional[Dict[str, Any]]:
        """Collect availability data for SLA measurement."""
        # Simulate availability calculation
        total_minutes = (end_time - start_time).total_seconds() / 60
        downtime_minutes = 5  # Simulate 5 minutes downtime
        availability = ((total_minutes - downtime_minutes) / total_minutes) * 100
        
        return {
            "measured_value": availability,
            "sample_size": int(total_minutes),
            "supporting_metrics": {
                "total_minutes": total_minutes,
                "downtime_minutes": downtime_minutes,
                "uptime_minutes": total_minutes - downtime_minutes
            }
        }
    
    async def _collect_error_rate_data(self, sla_target: SLATarget, start_time: datetime, end_time: datetime) -> Optional[Dict[str, Any]]:
        """Collect error rate data for SLA measurement."""
        # Simulate error rate calculation
        total_requests = 1000
        error_requests = 15
        error_rate = (error_requests / total_requests) * 100
        
        return {
            "measured_value": error_rate,
            "sample_size": total_requests,
            "supporting_metrics": {
                "total_requests": total_requests,
                "error_requests": error_requests,
                "success_requests": total_requests - error_requests
            }
        }
    
    async def _collect_throughput_data(self, sla_target: SLATarget, start_time: datetime, end_time: datetime) -> Optional[Dict[str, Any]]:
        """Collect throughput data for SLA measurement."""
        # Simulate throughput calculation
        total_requests = 1000
        time_span_seconds = (end_time - start_time).total_seconds()
        throughput_rps = total_requests / time_span_seconds
        
        return {
            "measured_value": throughput_rps,
            "sample_size": total_requests,
            "supporting_metrics": {
                "total_requests": total_requests,
                "time_span_seconds": time_span_seconds
            }
        }
    
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
    
    def _incident_to_dict(self, incident: SLAIncident) -> Dict[str, Any]:
        """Convert incident to dictionary representation."""
        return {
            "incident_id": incident.incident_id,
            "title": incident.title,
            "description": incident.description,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "created_at": incident.created_at.isoformat(),
            "affected_roles": [role.value for role in incident.affected_roles],
            "affected_slas": incident.affected_slas,
            "business_impact": incident.business_impact,
            "resolution_time_minutes": incident.resolution_time_minutes
        }
    
    # Additional placeholder methods
    async def _get_recent_measurements(self, sla_id: str, time_window: TimeWindow) -> List[SLAMeasurement]:
        """Get recent measurements for an SLA."""
        if sla_id not in self.sla_measurements:
            return []
        
        cutoff_time = datetime.now(timezone.utc) - self._get_timedelta_for_window(time_window)
        return [
            m for m in self.sla_measurements[sla_id]
            if m.timestamp > cutoff_time
        ]
    
    def _is_in_maintenance_window(self, sla_target: SLATarget, check_time: datetime) -> bool:
        """Check if current time is within a maintenance window."""
        # Implementation would check against configured maintenance windows
        return False
    
    def _is_business_hours(self, check_time: datetime) -> bool:
        """Check if current time is within business hours."""
        # Simple business hours check (9 AM to 5 PM, Monday to Friday)
        weekday = check_time.weekday()  # 0=Monday, 6=Sunday
        hour = check_time.hour
        return weekday < 5 and 9 <= hour < 17
    
    def _get_uptime_sla_target(self, role: Optional[PlatformRole]) -> float:
        """Get uptime SLA target for a role."""
        # Default uptime targets by role
        if role == PlatformRole.ACCESS_POINT_PROVIDER:
            return 99.95
        elif role == PlatformRole.SYSTEM_INTEGRATOR:
            return 99.9
        else:
            return 99.5


class SLATrendAnalyzer:
    """Analyzes SLA trends and patterns."""
    
    def analyze_sla_trend(self, measurements: List[SLAMeasurement]) -> str:
        """Analyze trend in SLA measurements."""
        if len(measurements) < 5:
            return "stable"
        
        # Simple trend analysis
        recent_compliance = [m.compliance_percentage for m in measurements[-5:]]
        earlier_compliance = [m.compliance_percentage for m in measurements[:5]]
        
        recent_avg = statistics.mean(recent_compliance)
        earlier_avg = statistics.mean(earlier_compliance)
        
        change_percent = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
        
        if change_percent > 5:
            return "improving"
        elif change_percent < -5:
            return "degrading"
        else:
            return "stable"


class BusinessImpactCalculator:
    """Calculates business impact of SLA breaches and incidents."""
    
    async def calculate_incident_impact(self, incident: SLAIncident) -> str:
        """Calculate business impact of an incident."""
        # Simple impact calculation based on severity and affected roles
        if incident.severity == IncidentSeverity.CRITICAL:
            return "high"
        elif incident.severity == IncidentSeverity.HIGH:
            return "medium"
        else:
            return "low"


# Factory function
def create_sla_monitor(**kwargs) -> SLAMonitor:
    """Factory function to create SLAMonitor."""
    return SLAMonitor(**kwargs)