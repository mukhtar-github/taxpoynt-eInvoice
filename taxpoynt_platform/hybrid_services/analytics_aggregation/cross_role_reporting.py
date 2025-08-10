"""
Hybrid Service: Cross-Role Reporting
Generates comprehensive reports across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import io
import csv
import statistics

from core_platform.database import get_db_session
from core_platform.models.reports import ReportDefinition, ReportExecution, ReportOutput
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.storage import FileStorage

from .unified_metrics import UnifiedMetrics, MetricScope, MetricType, AggregatedMetric

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Types of reports"""
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    BUSINESS = "business"
    TECHNICAL = "technical"
    REGULATORY = "regulatory"
    DASHBOARD = "dashboard"
    EXECUTIVE = "executive"


class ReportFormat(str, Enum):
    """Report output formats"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    HTML = "html"
    DASHBOARD = "dashboard"


class ReportScope(str, Enum):
    """Report scope"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    CROSS_ROLE = "cross_role"
    SYSTEM_WIDE = "system_wide"
    CUSTOM = "custom"


class ReportStatus(str, Enum):
    """Report generation status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ReportFrequency(str, Enum):
    """Report generation frequency"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    ON_DEMAND = "on_demand"


@dataclass
class ReportTemplate:
    """Report template definition"""
    template_id: str
    name: str
    description: str
    report_type: ReportType
    report_scope: ReportScope
    sections: List[Dict[str, Any]]
    data_sources: List[str]
    visualization_config: Dict[str, Any]
    filters: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportRequest:
    """Report generation request"""
    request_id: str
    template_id: str
    requested_by: str
    report_format: ReportFormat
    time_range: Tuple[datetime, datetime]
    filters: Dict[str, Any]
    parameters: Dict[str, Any]
    priority: str = "medium"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReportSection:
    """Report section with data and visualization"""
    section_id: str
    title: str
    description: str
    section_type: str
    data: List[Dict[str, Any]]
    visualization: Dict[str, Any]
    summary: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GeneratedReport:
    """Generated report with all sections"""
    report_id: str
    template_id: str
    report_type: ReportType
    report_scope: ReportScope
    generated_by: str
    generation_time: datetime
    time_range: Tuple[datetime, datetime]
    sections: List[ReportSection]
    summary: Dict[str, Any]
    file_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CrossRoleReporting:
    """
    Cross-role reporting service
    Generates comprehensive reports across SI and APP roles
    """
    
    def __init__(self, unified_metrics: UnifiedMetrics = None):
        """Initialize cross-role reporting service"""
        self.unified_metrics = unified_metrics or UnifiedMetrics()
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.file_storage = FileStorage()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.report_templates: Dict[str, ReportTemplate] = {}
        self.active_reports: Dict[str, Dict[str, Any]] = {}
        self.report_cache: Dict[str, GeneratedReport] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.max_report_age = 24 * 3600  # 24 hours
        
        # Initialize default templates
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default report templates"""
        default_templates = [
            # Operational dashboard
            ReportTemplate(
                template_id="operational_dashboard",
                name="Operational Dashboard",
                description="Real-time operational metrics across SI and APP",
                report_type=ReportType.OPERATIONAL,
                report_scope=ReportScope.CROSS_ROLE,
                sections=[
                    {
                        "section_id": "performance_overview",
                        "title": "Performance Overview",
                        "type": "metrics_summary",
                        "metrics": ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"],
                        "visualization": {"type": "dashboard_cards"}
                    },
                    {
                        "section_id": "throughput_trends",
                        "title": "Throughput Trends",
                        "type": "trend_analysis",
                        "metrics": ["unified_throughput"],
                        "visualization": {"type": "line_chart"}
                    },
                    {
                        "section_id": "error_analysis",
                        "title": "Error Analysis",
                        "type": "error_summary",
                        "metrics": ["error_rate", "error_distribution"],
                        "visualization": {"type": "pie_chart"}
                    }
                ],
                data_sources=["unified_metrics", "si_services", "app_services"],
                visualization_config={
                    "theme": "professional",
                    "color_scheme": "taxpoynt_blue",
                    "responsive": True
                },
                filters={
                    "time_range": "last_24_hours",
                    "service_roles": ["si", "app"],
                    "status": "active"
                }
            ),
            
            # Compliance report
            ReportTemplate(
                template_id="compliance_report",
                name="Compliance Report",
                description="Comprehensive compliance status across roles",
                report_type=ReportType.COMPLIANCE,
                report_scope=ReportScope.SYSTEM_WIDE,
                sections=[
                    {
                        "section_id": "compliance_overview",
                        "title": "Compliance Overview",
                        "type": "compliance_summary",
                        "metrics": ["unified_compliance_score", "regulatory_adherence"],
                        "visualization": {"type": "gauge_chart"}
                    },
                    {
                        "section_id": "regulatory_changes",
                        "title": "Regulatory Changes",
                        "type": "regulatory_updates",
                        "data_sources": ["regulatory_tracker"],
                        "visualization": {"type": "timeline"}
                    },
                    {
                        "section_id": "audit_findings",
                        "title": "Audit Findings",
                        "type": "audit_summary",
                        "data_sources": ["audit_coordinator"],
                        "visualization": {"type": "table"}
                    }
                ],
                data_sources=["compliance_coordination", "regulatory_tracker", "audit_coordinator"],
                visualization_config={
                    "theme": "compliance",
                    "highlight_issues": True,
                    "include_recommendations": True
                },
                filters={
                    "compliance_level": "all",
                    "time_range": "last_30_days",
                    "include_resolved": False
                }
            ),
            
            # Performance report
            ReportTemplate(
                template_id="performance_report",
                name="Performance Report",
                description="System performance analysis across SI and APP",
                report_type=ReportType.PERFORMANCE,
                report_scope=ReportScope.CROSS_ROLE,
                sections=[
                    {
                        "section_id": "latency_analysis",
                        "title": "Latency Analysis",
                        "type": "latency_metrics",
                        "metrics": ["e2e_processing_time", "si_processing_time", "app_processing_time"],
                        "visualization": {"type": "histogram"}
                    },
                    {
                        "section_id": "throughput_analysis",
                        "title": "Throughput Analysis",
                        "type": "throughput_metrics",
                        "metrics": ["unified_throughput", "peak_throughput"],
                        "visualization": {"type": "area_chart"}
                    },
                    {
                        "section_id": "resource_utilization",
                        "title": "Resource Utilization",
                        "type": "resource_metrics",
                        "metrics": ["cpu_usage", "memory_usage", "disk_usage"],
                        "visualization": {"type": "stacked_bar"}
                    }
                ],
                data_sources=["unified_metrics", "system_metrics"],
                visualization_config={
                    "theme": "performance",
                    "show_baselines": True,
                    "highlight_bottlenecks": True
                },
                filters={
                    "time_range": "last_7_days",
                    "granularity": "hourly",
                    "include_predictions": True
                }
            ),
            
            # Executive summary
            ReportTemplate(
                template_id="executive_summary",
                name="Executive Summary",
                description="High-level business metrics and KPIs",
                report_type=ReportType.EXECUTIVE,
                report_scope=ReportScope.SYSTEM_WIDE,
                sections=[
                    {
                        "section_id": "business_overview",
                        "title": "Business Overview",
                        "type": "business_metrics",
                        "metrics": ["transaction_volume", "revenue_impact", "customer_satisfaction"],
                        "visualization": {"type": "executive_dashboard"}
                    },
                    {
                        "section_id": "operational_health",
                        "title": "Operational Health",
                        "type": "health_metrics",
                        "metrics": ["system_availability", "success_rate", "error_rate"],
                        "visualization": {"type": "health_scorecard"}
                    },
                    {
                        "section_id": "strategic_insights",
                        "title": "Strategic Insights",
                        "type": "insights_summary",
                        "data_sources": ["insight_generator"],
                        "visualization": {"type": "insights_panel"}
                    }
                ],
                data_sources=["unified_metrics", "business_metrics", "insight_generator"],
                visualization_config={
                    "theme": "executive",
                    "high_level_view": True,
                    "include_trends": True
                },
                filters={
                    "time_range": "last_30_days",
                    "include_forecasts": True,
                    "focus_areas": ["performance", "compliance", "business"]
                }
            )
        ]
        
        for template in default_templates:
            self.report_templates[template.template_id] = template
    
    async def initialize(self):
        """Initialize the cross-role reporting service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing cross-role reporting service")
        
        try:
            # Initialize dependencies
            await self.unified_metrics.initialize()
            await self.cache.initialize()
            await self.file_storage.initialize()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start report cleanup task
            asyncio.create_task(self._cleanup_old_reports())
            
            self.is_initialized = True
            self.logger.info("Cross-role reporting service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing cross-role reporting service: {str(e)}")
            raise
    
    async def register_report_template(self, template: ReportTemplate):
        """Register a new report template"""
        try:
            self.report_templates[template.template_id] = template
            
            # Cache the template
            await self.cache.set(
                f"report_template:{template.template_id}",
                template.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Registered report template: {template.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering report template: {str(e)}")
            raise
    
    async def generate_report(self, report_request: ReportRequest) -> GeneratedReport:
        """Generate a report based on request"""
        try:
            if report_request.template_id not in self.report_templates:
                raise ValueError(f"Report template not found: {report_request.template_id}")
            
            template = self.report_templates[report_request.template_id]
            
            # Mark as active
            self.active_reports[report_request.request_id] = {
                "status": ReportStatus.RUNNING,
                "started_at": datetime.now(timezone.utc),
                "template_id": report_request.template_id
            }
            
            # Generate report sections
            sections = []
            for section_config in template.sections:
                section = await self._generate_section(
                    section_config,
                    report_request.time_range,
                    report_request.filters
                )
                sections.append(section)
            
            # Create report summary
            summary = await self._create_report_summary(sections, template)
            
            # Create generated report
            generated_report = GeneratedReport(
                report_id=report_request.request_id,
                template_id=template.template_id,
                report_type=template.report_type,
                report_scope=template.report_scope,
                generated_by=report_request.requested_by,
                generation_time=datetime.now(timezone.utc),
                time_range=report_request.time_range,
                sections=sections,
                summary=summary,
                metadata={
                    "format": report_request.report_format,
                    "filters": report_request.filters,
                    "parameters": report_request.parameters
                }
            )
            
            # Generate file if required
            if report_request.report_format != ReportFormat.DASHBOARD:
                file_path = await self._generate_report_file(
                    generated_report,
                    report_request.report_format
                )
                generated_report.file_path = file_path
            
            # Cache the report
            self.report_cache[report_request.request_id] = generated_report
            
            # Update active reports
            self.active_reports[report_request.request_id]["status"] = ReportStatus.COMPLETED
            self.active_reports[report_request.request_id]["completed_at"] = datetime.now(timezone.utc)
            
            # Send completion notification
            await self.notification_service.send_notification(
                type="report_generated",
                recipient=report_request.requested_by,
                data={
                    "report_id": generated_report.report_id,
                    "template_name": template.name,
                    "file_path": generated_report.file_path
                }
            )
            
            return generated_report
            
        except Exception as e:
            # Update active reports with error
            if report_request.request_id in self.active_reports:
                self.active_reports[report_request.request_id]["status"] = ReportStatus.FAILED
                self.active_reports[report_request.request_id]["error"] = str(e)
            
            self.logger.error(f"Error generating report: {str(e)}")
            raise
    
    async def get_report(self, report_id: str) -> Optional[GeneratedReport]:
        """Get a generated report by ID"""
        try:
            # Check cache first
            if report_id in self.report_cache:
                return self.report_cache[report_id]
            
            # Check persistent storage
            cached_report = await self.cache.get(f"report:{report_id}")
            if cached_report:
                return GeneratedReport(**cached_report)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting report: {str(e)}")
            return None
    
    async def list_reports(
        self,
        report_type: ReportType = None,
        requested_by: str = None,
        limit: int = 50
    ) -> List[GeneratedReport]:
        """List generated reports"""
        try:
            reports = list(self.report_cache.values())
            
            # Apply filters
            if report_type:
                reports = [r for r in reports if r.report_type == report_type]
            
            if requested_by:
                reports = [r for r in reports if r.generated_by == requested_by]
            
            # Sort by generation time (newest first)
            reports.sort(key=lambda x: x.generation_time, reverse=True)
            
            return reports[:limit]
            
        except Exception as e:
            self.logger.error(f"Error listing reports: {str(e)}")
            return []
    
    async def schedule_report(
        self,
        template_id: str,
        frequency: ReportFrequency,
        recipients: List[str],
        report_format: ReportFormat = ReportFormat.PDF,
        filters: Dict[str, Any] = None
    ) -> str:
        """Schedule recurring report generation"""
        try:
            schedule_id = str(uuid.uuid4())
            
            schedule_config = {
                "schedule_id": schedule_id,
                "template_id": template_id,
                "frequency": frequency,
                "recipients": recipients,
                "report_format": report_format,
                "filters": filters or {},
                "created_at": datetime.now(timezone.utc).isoformat(),
                "status": "active"
            }
            
            # Store schedule configuration
            await self.cache.set(
                f"report_schedule:{schedule_id}",
                schedule_config,
                ttl=None  # No expiration for schedules
            )
            
            self.logger.info(f"Scheduled report: {template_id} with frequency {frequency}")
            
            return schedule_id
            
        except Exception as e:
            self.logger.error(f"Error scheduling report: {str(e)}")
            raise
    
    async def get_dashboard_data(
        self,
        template_id: str,
        time_range: Tuple[datetime, datetime] = None,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Get real-time dashboard data"""
        try:
            if template_id not in self.report_templates:
                raise ValueError(f"Report template not found: {template_id}")
            
            template = self.report_templates[template_id]
            
            # Use last 24 hours if no time range specified
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                time_range = (start_time, end_time)
            
            # Generate dashboard sections
            dashboard_data = {
                "template_id": template_id,
                "template_name": template.name,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "sections": []
            }
            
            for section_config in template.sections:
                section_data = await self._generate_dashboard_section(
                    section_config,
                    time_range,
                    filters or {}
                )
                dashboard_data["sections"].append(section_data)
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {str(e)}")
            raise
    
    async def _generate_section(
        self,
        section_config: Dict[str, Any],
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> ReportSection:
        """Generate a report section"""
        try:
            section_id = section_config["section_id"]
            section_type = section_config["type"]
            
            # Get section data based on type
            if section_type == "metrics_summary":
                data = await self._get_metrics_summary_data(
                    section_config.get("metrics", []),
                    time_range,
                    filters
                )
            elif section_type == "trend_analysis":
                data = await self._get_trend_analysis_data(
                    section_config.get("metrics", []),
                    time_range,
                    filters
                )
            elif section_type == "compliance_summary":
                data = await self._get_compliance_summary_data(time_range, filters)
            elif section_type == "performance_metrics":
                data = await self._get_performance_metrics_data(time_range, filters)
            else:
                data = []
            
            # Create visualization config
            visualization = section_config.get("visualization", {})
            
            # Create section summary
            summary = await self._create_section_summary(data, section_type)
            
            return ReportSection(
                section_id=section_id,
                title=section_config["title"],
                description=section_config.get("description", ""),
                section_type=section_type,
                data=data,
                visualization=visualization,
                summary=summary,
                metadata={"filters": filters}
            )
            
        except Exception as e:
            self.logger.error(f"Error generating section: {str(e)}")
            raise
    
    async def _generate_dashboard_section(
        self,
        section_config: Dict[str, Any],
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate dashboard section data"""
        try:
            section = await self._generate_section(section_config, time_range, filters)
            
            # Format for dashboard
            dashboard_section = {
                "section_id": section.section_id,
                "title": section.title,
                "type": section.section_type,
                "data": section.data,
                "visualization": section.visualization,
                "summary": section.summary,
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
            return dashboard_section
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard section: {str(e)}")
            return {}
    
    async def _get_metrics_summary_data(
        self,
        metric_ids: List[str],
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get metrics summary data"""
        try:
            aggregated_metrics = await self.unified_metrics.aggregate_metrics(
                metric_ids,
                time_range,
                dimensions=filters.get("dimensions")
            )
            
            summary_data = []
            for metric in aggregated_metrics:
                summary_data.append({
                    "metric_id": metric.metric_id,
                    "value": metric.aggregated_value,
                    "unit": self.unified_metrics.metric_definitions[metric.metric_id].unit,
                    "confidence": metric.confidence_level,
                    "trend": await self._calculate_trend(metric.metric_id, time_range),
                    "threshold_status": await self._check_threshold_status(metric)
                })
            
            return summary_data
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary data: {str(e)}")
            return []
    
    async def _get_trend_analysis_data(
        self,
        metric_ids: List[str],
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get trend analysis data"""
        try:
            trend_data = []
            
            for metric_id in metric_ids:
                trends = await self.unified_metrics.get_metric_trends(
                    metric_id,
                    time_range,
                    granularity=filters.get("granularity", "hour")
                )
                
                trend_data.append({
                    "metric_id": metric_id,
                    "trends": [
                        {
                            "timestamp": trend.timestamp.isoformat(),
                            "value": trend.aggregated_value,
                            "period": trend.aggregation_period
                        }
                        for trend in trends
                    ]
                })
            
            return trend_data
            
        except Exception as e:
            self.logger.error(f"Error getting trend analysis data: {str(e)}")
            return []
    
    async def _get_compliance_summary_data(
        self,
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get compliance summary data"""
        try:
            # Get compliance metrics
            compliance_metrics = await self.unified_metrics.aggregate_metrics(
                ["unified_compliance_score"],
                time_range
            )
            
            compliance_data = []
            for metric in compliance_metrics:
                compliance_data.append({
                    "metric_id": metric.metric_id,
                    "score": metric.aggregated_value,
                    "status": "compliant" if metric.aggregated_value >= 85 else "non_compliant",
                    "breakdown": metric.breakdown,
                    "recommendations": await self._generate_compliance_recommendations(metric)
                })
            
            return compliance_data
            
        except Exception as e:
            self.logger.error(f"Error getting compliance summary data: {str(e)}")
            return []
    
    async def _get_performance_metrics_data(
        self,
        time_range: Tuple[datetime, datetime],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get performance metrics data"""
        try:
            performance_metrics = await self.unified_metrics.aggregate_metrics(
                ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"],
                time_range
            )
            
            performance_data = []
            for metric in performance_metrics:
                performance_data.append({
                    "metric_id": metric.metric_id,
                    "value": metric.aggregated_value,
                    "unit": self.unified_metrics.metric_definitions[metric.metric_id].unit,
                    "percentiles": await self._calculate_percentiles(metric),
                    "baseline_comparison": await self._compare_to_baseline(metric)
                })
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics data: {str(e)}")
            return []
    
    async def _calculate_trend(self, metric_id: str, time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Calculate trend for a metric"""
        try:
            # Get historical data
            historical_range = (
                time_range[0] - timedelta(days=7),
                time_range[0]
            )
            
            current_metrics = await self.unified_metrics.aggregate_metrics(
                [metric_id],
                time_range
            )
            
            historical_metrics = await self.unified_metrics.aggregate_metrics(
                [metric_id],
                historical_range
            )
            
            if not current_metrics or not historical_metrics:
                return {"direction": "unknown", "change": 0}
            
            current_value = current_metrics[0].aggregated_value
            historical_value = historical_metrics[0].aggregated_value
            
            if historical_value == 0:
                return {"direction": "unknown", "change": 0}
            
            change = ((current_value - historical_value) / historical_value) * 100
            
            return {
                "direction": "up" if change > 0 else "down" if change < 0 else "stable",
                "change": round(change, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating trend: {str(e)}")
            return {"direction": "unknown", "change": 0}
    
    async def _check_threshold_status(self, metric: AggregatedMetric) -> str:
        """Check threshold status for a metric"""
        try:
            if metric.metric_id not in self.unified_metrics.metric_definitions:
                return "unknown"
            
            metric_def = self.unified_metrics.metric_definitions[metric.metric_id]
            thresholds = metric_def.thresholds
            
            if "critical" in thresholds and metric.aggregated_value >= thresholds["critical"]:
                return "critical"
            elif "warning" in thresholds and metric.aggregated_value >= thresholds["warning"]:
                return "warning"
            else:
                return "normal"
                
        except Exception as e:
            self.logger.error(f"Error checking threshold status: {str(e)}")
            return "unknown"
    
    async def _generate_compliance_recommendations(self, metric: AggregatedMetric) -> List[str]:
        """Generate compliance recommendations"""
        try:
            recommendations = []
            
            if metric.aggregated_value < 70:
                recommendations.append("Critical: Immediate compliance review required")
                recommendations.append("Review and update compliance procedures")
                recommendations.append("Conduct emergency compliance audit")
            elif metric.aggregated_value < 85:
                recommendations.append("Warning: Compliance improvements needed")
                recommendations.append("Review recent regulatory changes")
                recommendations.append("Update compliance training")
            else:
                recommendations.append("Good: Maintain current compliance practices")
                recommendations.append("Continue monitoring regulatory changes")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating compliance recommendations: {str(e)}")
            return []
    
    async def _calculate_percentiles(self, metric: AggregatedMetric) -> Dict[str, float]:
        """Calculate percentiles for a metric"""
        try:
            # Extract values from breakdown
            if "value_distribution" in metric.breakdown:
                dist = metric.breakdown["value_distribution"]
                return {
                    "p50": dist.get("median", 0),
                    "p90": dist.get("p90", 0),
                    "p95": dist.get("p95", 0),
                    "p99": dist.get("p99", 0)
                }
            
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
            
        except Exception as e:
            self.logger.error(f"Error calculating percentiles: {str(e)}")
            return {"p50": 0, "p90": 0, "p95": 0, "p99": 0}
    
    async def _compare_to_baseline(self, metric: AggregatedMetric) -> Dict[str, Any]:
        """Compare metric to baseline"""
        try:
            # Simple baseline comparison (can be enhanced with ML models)
            baseline_value = metric.aggregated_value * 0.9  # 10% below current as baseline
            
            return {
                "baseline_value": baseline_value,
                "current_value": metric.aggregated_value,
                "difference": metric.aggregated_value - baseline_value,
                "percentage_change": ((metric.aggregated_value - baseline_value) / baseline_value) * 100 if baseline_value != 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing to baseline: {str(e)}")
            return {}
    
    async def _create_section_summary(self, data: List[Dict[str, Any]], section_type: str) -> Dict[str, Any]:
        """Create section summary"""
        try:
            summary = {
                "data_points": len(data),
                "section_type": section_type,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
            if section_type == "metrics_summary":
                summary["metrics_count"] = len(data)
                summary["critical_metrics"] = len([
                    d for d in data 
                    if d.get("threshold_status") == "critical"
                ])
            elif section_type == "trend_analysis":
                summary["trends_analyzed"] = len(data)
            elif section_type == "compliance_summary":
                summary["compliance_items"] = len(data)
                summary["compliant_items"] = len([
                    d for d in data 
                    if d.get("status") == "compliant"
                ])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error creating section summary: {str(e)}")
            return {}
    
    async def _create_report_summary(self, sections: List[ReportSection], template: ReportTemplate) -> Dict[str, Any]:
        """Create report summary"""
        try:
            return {
                "total_sections": len(sections),
                "template_name": template.name,
                "report_type": template.report_type,
                "report_scope": template.report_scope,
                "sections_summary": {
                    section.section_id: section.summary
                    for section in sections
                },
                "generation_time": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating report summary: {str(e)}")
            return {}
    
    async def _generate_report_file(self, report: GeneratedReport, format: ReportFormat) -> str:
        """Generate report file in specified format"""
        try:
            file_name = f"report_{report.report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            if format == ReportFormat.JSON:
                file_path = f"{file_name}.json"
                content = json.dumps(report.to_dict(), indent=2, default=str)
                
            elif format == ReportFormat.CSV:
                file_path = f"{file_name}.csv"
                content = await self._generate_csv_content(report)
                
            elif format == ReportFormat.HTML:
                file_path = f"{file_name}.html"
                content = await self._generate_html_content(report)
                
            else:
                # Default to JSON
                file_path = f"{file_name}.json"
                content = json.dumps(report.to_dict(), indent=2, default=str)
            
            # Save to file storage
            await self.file_storage.save_file(file_path, content)
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"Error generating report file: {str(e)}")
            raise
    
    async def _generate_csv_content(self, report: GeneratedReport) -> str:
        """Generate CSV content for report"""
        try:
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(["Report ID", "Template", "Generated By", "Generation Time"])
            writer.writerow([report.report_id, report.template_id, report.generated_by, report.generation_time])
            writer.writerow([])
            
            # Write sections
            for section in report.sections:
                writer.writerow([f"Section: {section.title}"])
                writer.writerow([f"Type: {section.section_type}"])
                writer.writerow([])
                
                # Write section data
                if section.data:
                    # Get headers from first data item
                    headers = list(section.data[0].keys())
                    writer.writerow(headers)
                    
                    for item in section.data:
                        row = [str(item.get(h, "")) for h in headers]
                        writer.writerow(row)
                
                writer.writerow([])
            
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Error generating CSV content: {str(e)}")
            return ""
    
    async def _generate_html_content(self, report: GeneratedReport) -> str:
        """Generate HTML content for report"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>TaxPoynt Report - {report.template_id}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background-color: #f0f0f0; padding: 20px; margin-bottom: 20px; }}
                    .section {{ margin-bottom: 30px; border: 1px solid #ddd; padding: 15px; }}
                    .section-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>TaxPoynt Report</h1>
                    <p><strong>Report ID:</strong> {report.report_id}</p>
                    <p><strong>Template:</strong> {report.template_id}</p>
                    <p><strong>Generated By:</strong> {report.generated_by}</p>
                    <p><strong>Generation Time:</strong> {report.generation_time}</p>
                </div>
            """
            
            # Add sections
            for section in report.sections:
                html_content += f"""
                <div class="section">
                    <div class="section-title">{section.title}</div>
                    <p>{section.description}</p>
                    <p><strong>Type:</strong> {section.section_type}</p>
                """
                
                # Add section data as table
                if section.data:
                    html_content += "<table>"
                    
                    # Headers
                    headers = list(section.data[0].keys())
                    html_content += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
                    
                    # Data rows
                    for item in section.data:
                        html_content += "<tr>" + "".join(f"<td>{item.get(h, '')}</td>" for h in headers) + "</tr>"
                    
                    html_content += "</table>"
                
                html_content += "</div>"
            
            html_content += """
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"Error generating HTML content: {str(e)}")
            return ""
    
    async def _cleanup_old_reports(self):
        """Cleanup old reports periodically"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.now(timezone.utc)
                
                # Remove old reports from cache
                to_remove = []
                for report_id, report in self.report_cache.items():
                    age = (current_time - report.generation_time).total_seconds()
                    if age > self.max_report_age:
                        to_remove.append(report_id)
                
                for report_id in to_remove:
                    del self.report_cache[report_id]
                
                self.logger.info(f"Cleaned up {len(to_remove)} old reports")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup old reports: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "report.requested",
                self._handle_report_requested
            )
            
            await self.event_bus.subscribe(
                "metrics.updated",
                self._handle_metrics_updated
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_report_requested(self, event_data: Dict[str, Any]):
        """Handle report requested event"""
        try:
            # Can be used for audit logging
            self.logger.info(f"Report requested: {event_data}")
            
        except Exception as e:
            self.logger.error(f"Error handling report requested event: {str(e)}")
    
    async def _handle_metrics_updated(self, event_data: Dict[str, Any]):
        """Handle metrics updated event"""
        try:
            # Invalidate relevant report caches
            affected_reports = []
            for report_id, report in self.report_cache.items():
                if any(section.section_type == "metrics_summary" for section in report.sections):
                    affected_reports.append(report_id)
            
            for report_id in affected_reports:
                if report_id in self.report_cache:
                    del self.report_cache[report_id]
            
        except Exception as e:
            self.logger.error(f"Error handling metrics updated event: {str(e)}")
    
    async def get_report_status(self, request_id: str) -> Dict[str, Any]:
        """Get report generation status"""
        try:
            if request_id in self.active_reports:
                return self.active_reports[request_id]
            
            return {"status": "not_found"}
            
        except Exception as e:
            self.logger.error(f"Error getting report status: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            unified_metrics_health = await self.unified_metrics.health_check()
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "cross_role_reporting",
                "components": {
                    "unified_metrics": unified_metrics_health,
                    "cache": cache_health,
                    "file_storage": {"status": "healthy"},
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_templates": len(self.report_templates),
                    "active_reports": len(self.active_reports),
                    "cached_reports": len(self.report_cache)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "cross_role_reporting",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Cross-role reporting service cleanup initiated")
        
        try:
            # Clear caches
            self.report_cache.clear()
            self.active_reports.clear()
            
            # Cleanup dependencies
            await self.unified_metrics.cleanup()
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Cross-role reporting service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_cross_role_reporting(unified_metrics: UnifiedMetrics = None) -> CrossRoleReporting:
    """Create cross-role reporting service"""
    return CrossRoleReporting(unified_metrics)