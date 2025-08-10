"""
Compliance Reporting Data Models
===============================
Pydantic models for compliance reporting, dashboards, audit trails, and metrics.
"""

from datetime import datetime, date, time
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# Import from other modules
from ..orchestrator.models import ComplianceFramework, ComplianceStatus, ValidationSeverity
from ..validation_engine.models import ValidationResponse, AggregatedValidationResult

class ReportType(str, Enum):
    """Types of compliance reports"""
    EXECUTIVE_SUMMARY = "executive_summary"
    DETAILED_COMPLIANCE = "detailed_compliance"
    FRAMEWORK_SPECIFIC = "framework_specific"
    AUDIT_REPORT = "audit_report"
    TREND_ANALYSIS = "trend_analysis"
    REGULATORY_SUBMISSION = "regulatory_submission"
    CERTIFICATION_READINESS = "certification_readiness"
    RISK_ASSESSMENT = "risk_assessment"
    PERFORMANCE_METRICS = "performance_metrics"
    COMPARATIVE_ANALYSIS = "comparative_analysis"

class ReportFormat(str, Enum):
    """Report output formats"""
    PDF = "pdf"
    HTML = "html"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    WORD = "word"
    POWERPOINT = "powerpoint"

class ExportFormat(str, Enum):
    """Export format options"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"
    XML = "xml"
    HTML = "html"
    WORD = "word"
    POWERPOINT = "powerpoint"

class DashboardType(str, Enum):
    """Dashboard types"""
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    FRAMEWORK_SPECIFIC = "framework_specific"
    REAL_TIME = "real_time"
    HISTORICAL = "historical"
    COMPARATIVE = "comparative"

class WidgetType(str, Enum):
    """Dashboard widget types"""
    METRIC_CARD = "metric_card"
    CHART_LINE = "chart_line"
    CHART_BAR = "chart_bar"
    CHART_PIE = "chart_pie"
    CHART_DONUT = "chart_donut"
    TABLE = "table"
    GAUGE = "gauge"
    PROGRESS_BAR = "progress_bar"
    HEATMAP = "heatmap"
    SPARKLINE = "sparkline"
    ALERT_LIST = "alert_list"
    COMPLIANCE_MATRIX = "compliance_matrix"

class MetricType(str, Enum):
    """Compliance metric types"""
    SCORE = "score"
    COUNT = "count"
    PERCENTAGE = "percentage"
    RATIO = "ratio"
    TREND = "trend"
    DURATION = "duration"
    CURRENCY = "currency"
    BINARY = "binary"

class AuditAction(str, Enum):
    """Audit trail action types"""
    VALIDATION_EXECUTED = "validation_executed"
    REPORT_GENERATED = "report_generated"
    DASHBOARD_ACCESSED = "dashboard_accessed"
    EXPORT_PERFORMED = "export_performed"
    CONFIGURATION_CHANGED = "configuration_changed"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    FRAMEWORK_UPDATED = "framework_updated"
    RULE_MODIFIED = "rule_modified"
    ALERT_TRIGGERED = "alert_triggered"

class ReportScheduleFrequency(str, Enum):
    """Report scheduling frequencies"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ON_DEMAND = "on_demand"

class ComplianceMetric(BaseModel):
    """Individual compliance metric model"""
    metric_id: str = Field(..., description="Unique metric identifier")
    metric_name: str = Field(..., description="Human-readable metric name")
    metric_type: MetricType = Field(..., description="Type of metric")
    value: Union[float, int, str, bool] = Field(..., description="Metric value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    
    # Context and categorization
    framework: Optional[ComplianceFramework] = Field(None, description="Associated framework")
    category: str = Field(..., description="Metric category")
    subcategory: Optional[str] = Field(None, description="Metric subcategory")
    
    # Temporal information
    measurement_timestamp: datetime = Field(default_factory=datetime.now)
    measurement_period_start: Optional[datetime] = Field(None, description="Period start")
    measurement_period_end: Optional[datetime] = Field(None, description="Period end")
    
    # Comparison and context
    previous_value: Optional[Union[float, int, str, bool]] = Field(None, description="Previous measurement")
    target_value: Optional[Union[float, int, str, bool]] = Field(None, description="Target value")
    benchmark_value: Optional[Union[float, int, str, bool]] = Field(None, description="Benchmark value")
    
    # Status and interpretation
    status: ComplianceStatus = Field(ComplianceStatus.COMPLIANT, description="Metric status")
    trend: Optional[str] = Field(None, description="Trend direction (improving, declining, stable)")
    interpretation: Optional[str] = Field(None, description="Metric interpretation")
    
    # Metadata
    data_source: str = Field("compliance_engine", description="Data source")
    calculation_method: Optional[str] = Field(None, description="How metric was calculated")
    confidence_level: float = Field(100.0, ge=0, le=100, description="Confidence in metric accuracy")

class DashboardWidget(BaseModel):
    """Dashboard widget configuration"""
    widget_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Widget identifier")
    widget_name: str = Field(..., description="Widget display name")
    widget_type: WidgetType = Field(..., description="Type of widget")
    
    # Layout and positioning
    position: Dict[str, int] = Field(..., description="Widget position (x, y, width, height)")
    order: int = Field(0, description="Display order")
    
    # Data configuration
    data_source: str = Field(..., description="Data source for widget")
    metrics: List[str] = Field(..., description="Metric IDs to display")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Data filters")
    
    # Visualization configuration
    chart_config: Dict[str, Any] = Field(default_factory=dict, description="Chart configuration")
    display_options: Dict[str, Any] = Field(default_factory=dict, description="Display options")
    refresh_interval: int = Field(300, description="Refresh interval in seconds")
    
    # Thresholds and alerts
    thresholds: Dict[str, float] = Field(default_factory=dict, description="Alert thresholds")
    alert_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Alert conditions")
    
    # Permissions and visibility
    visible: bool = Field(True, description="Widget visibility")
    permissions: List[str] = Field(default_factory=list, description="Required permissions")

class DashboardConfig(BaseModel):
    """Dashboard configuration model"""
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Dashboard identifier")
    dashboard_name: str = Field(..., description="Dashboard name")
    dashboard_type: DashboardType = Field(..., description="Dashboard type")
    description: Optional[str] = Field(None, description="Dashboard description")
    
    # Layout and design
    layout: Dict[str, Any] = Field(default_factory=dict, description="Dashboard layout configuration")
    theme: str = Field("default", description="Dashboard theme")
    widgets: List[DashboardWidget] = Field(default_factory=list, description="Dashboard widgets")
    
    # Configuration
    auto_refresh: bool = Field(True, description="Enable auto refresh")
    refresh_interval: int = Field(300, description="Auto refresh interval in seconds")
    time_range: Dict[str, Any] = Field(default_factory=dict, description="Default time range")
    
    # Access control
    owner: str = Field(..., description="Dashboard owner")
    shared_with: List[str] = Field(default_factory=list, description="Users with access")
    public: bool = Field(False, description="Public dashboard flag")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = Field(None, description="Last access timestamp")
    access_count: int = Field(0, description="Total access count", ge=0)

class ReportTemplate(BaseModel):
    """Report template configuration"""
    template_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Template identifier")
    template_name: str = Field(..., description="Template name")
    report_type: ReportType = Field(..., description="Type of report")
    description: Optional[str] = Field(None, description="Template description")
    
    # Template structure
    sections: List[Dict[str, Any]] = Field(..., description="Report sections configuration")
    header: Dict[str, Any] = Field(default_factory=dict, description="Report header configuration")
    footer: Dict[str, Any] = Field(default_factory=dict, description="Report footer configuration")
    
    # Styling and formatting
    styling: Dict[str, Any] = Field(default_factory=dict, description="Report styling configuration")
    page_settings: Dict[str, Any] = Field(default_factory=dict, description="Page settings")
    
    # Data requirements
    required_data: List[str] = Field(..., description="Required data sources")
    optional_data: List[str] = Field(default_factory=list, description="Optional data sources")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    
    # Output configuration
    supported_formats: List[ReportFormat] = Field(..., description="Supported output formats")
    default_format: ReportFormat = Field(ReportFormat.PDF, description="Default output format")
    
    # Metadata
    version: str = Field("1.0", description="Template version")
    author: str = Field(..., description="Template author")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Usage tracking
    usage_count: int = Field(0, description="Template usage count", ge=0)
    last_used: Optional[datetime] = Field(None, description="Last usage timestamp")

class ComplianceReport(BaseModel):
    """Generated compliance report model"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Report identifier")
    report_name: str = Field(..., description="Report name")
    report_type: ReportType = Field(..., description="Type of report")
    template_id: Optional[str] = Field(None, description="Template used")
    
    # Report metadata
    generated_at: datetime = Field(default_factory=datetime.now)
    generated_by: str = Field(..., description="Report generator (user or system)")
    report_period_start: datetime = Field(..., description="Report period start")
    report_period_end: datetime = Field(..., description="Report period end")
    
    # Content and data
    executive_summary: Dict[str, Any] = Field(..., description="Executive summary data")
    detailed_findings: List[Dict[str, Any]] = Field(..., description="Detailed findings")
    metrics: List[ComplianceMetric] = Field(..., description="Report metrics")
    framework_results: Dict[ComplianceFramework, Dict[str, Any]] = Field(
        default_factory=dict, description="Results by framework"
    )
    
    # Analysis and insights
    key_insights: List[str] = Field(default_factory=list, description="Key insights")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    action_items: List[Dict[str, Any]] = Field(default_factory=list, description="Action items")
    risk_assessment: Dict[str, Any] = Field(default_factory=dict, description="Risk assessment")
    
    # Quality and validation
    data_sources: List[str] = Field(..., description="Data sources used")
    data_quality_score: float = Field(100.0, ge=0, le=100, description="Data quality score")
    completeness_score: float = Field(100.0, ge=0, le=100, description="Report completeness score")
    validation_results: Optional[ValidationResponse] = Field(None, description="Source validation results")
    
    # Distribution and access
    distribution_list: List[str] = Field(default_factory=list, description="Report distribution list")
    access_permissions: List[str] = Field(default_factory=list, description="Access permissions")
    confidentiality_level: str = Field("internal", description="Confidentiality classification")
    
    # Output information
    available_formats: List[ReportFormat] = Field(..., description="Available output formats")
    file_paths: Dict[ReportFormat, str] = Field(default_factory=dict, description="Generated file paths")
    file_sizes: Dict[ReportFormat, int] = Field(default_factory=dict, description="File sizes in bytes")

class AuditEvent(BaseModel):
    """Audit trail event model"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Event identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    action: AuditAction = Field(..., description="Action performed")
    
    # User and session information
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    ip_address: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    # Action details
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: Optional[str] = Field(None, description="Resource identifier")
    action_description: str = Field(..., description="Detailed action description")
    
    # Context and metadata
    framework: Optional[ComplianceFramework] = Field(None, description="Associated framework")
    entity_id: Optional[str] = Field(None, description="Entity identifier")
    business_context: Optional[str] = Field(None, description="Business context")
    
    # Result and impact
    result: str = Field(..., description="Action result (success, failure, partial)")
    impact_level: ValidationSeverity = Field(ValidationSeverity.INFO, description="Impact severity")
    changes_made: Dict[str, Any] = Field(default_factory=dict, description="Changes made")
    
    # Before and after states
    previous_state: Optional[Dict[str, Any]] = Field(None, description="Previous state")
    new_state: Optional[Dict[str, Any]] = Field(None, description="New state")
    
    # Additional data
    additional_data: Dict[str, Any] = Field(default_factory=dict, description="Additional event data")
    tags: List[str] = Field(default_factory=list, description="Event tags")
    
    # Compliance and regulatory
    regulatory_significance: bool = Field(False, description="Regulatory significance flag")
    retention_period: Optional[int] = Field(None, description="Retention period in days")

class ReportSchedule(BaseModel):
    """Report scheduling configuration"""
    schedule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Schedule identifier")
    schedule_name: str = Field(..., description="Schedule name")
    report_template_id: str = Field(..., description="Report template to generate")
    
    # Scheduling configuration
    frequency: ReportScheduleFrequency = Field(..., description="Schedule frequency")
    start_date: date = Field(..., description="Schedule start date")
    end_date: Optional[date] = Field(None, description="Schedule end date")
    
    # Timing details
    time_of_day: time = Field(time(9, 0), description="Time of day to generate")
    timezone: str = Field("UTC", description="Timezone for scheduling")
    
    # Frequency-specific settings
    day_of_week: Optional[int] = Field(None, description="Day of week (0=Monday, 6=Sunday)")
    day_of_month: Optional[int] = Field(None, description="Day of month (1-31)")
    week_of_month: Optional[int] = Field(None, description="Week of month (1-4)")
    
    # Report configuration
    report_parameters: Dict[str, Any] = Field(default_factory=dict, description="Report parameters")
    output_formats: List[ReportFormat] = Field(..., description="Output formats to generate")
    
    # Distribution
    recipients: List[str] = Field(..., description="Report recipients")
    delivery_method: str = Field("email", description="Delivery method")
    delivery_settings: Dict[str, Any] = Field(default_factory=dict, description="Delivery settings")
    
    # Status and control
    is_active: bool = Field(True, description="Schedule active status")
    last_execution: Optional[datetime] = Field(None, description="Last execution timestamp")
    next_execution: Optional[datetime] = Field(None, description="Next execution timestamp")
    execution_count: int = Field(0, description="Total executions", ge=0)
    
    # Error handling
    max_retries: int = Field(3, description="Maximum retry attempts", ge=0)
    retry_count: int = Field(0, description="Current retry count", ge=0)
    last_error: Optional[str] = Field(None, description="Last error message")
    
    # Metadata
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class ComplianceAlertRule(BaseModel):
    """Compliance alert rule configuration"""
    rule_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Alert rule identifier")
    rule_name: str = Field(..., description="Alert rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    # Trigger conditions
    metric_id: str = Field(..., description="Metric to monitor")
    operator: str = Field(..., description="Comparison operator")
    threshold_value: Union[float, int, str] = Field(..., description="Threshold value")
    
    # Advanced conditions
    conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Additional conditions")
    evaluation_period: int = Field(300, description="Evaluation period in seconds")
    consecutive_violations: int = Field(1, description="Consecutive violations required", ge=1)
    
    # Severity and categorization
    severity: ValidationSeverity = Field(..., description="Alert severity")
    category: str = Field(..., description="Alert category")
    framework: Optional[ComplianceFramework] = Field(None, description="Associated framework")
    
    # Notification settings
    notification_channels: List[str] = Field(..., description="Notification channels")
    recipients: List[str] = Field(..., description="Alert recipients")
    message_template: str = Field(..., description="Alert message template")
    
    # Control settings
    is_active: bool = Field(True, description="Rule active status")
    cooldown_period: int = Field(3600, description="Cooldown period in seconds")
    max_alerts_per_hour: int = Field(10, description="Maximum alerts per hour", ge=1)
    
    # Metadata
    created_by: str = Field(..., description="Creator user ID")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Usage tracking
    triggered_count: int = Field(0, description="Times rule was triggered", ge=0)
    last_triggered: Optional[datetime] = Field(None, description="Last trigger timestamp")

class ReportExportRequest(BaseModel):
    """Report export request model"""
    export_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Export identifier")
    report_id: str = Field(..., description="Report to export")
    export_format: ExportFormat = Field(..., description="Desired export format")
    
    # Export configuration
    export_options: Dict[str, Any] = Field(default_factory=dict, description="Export-specific options")
    include_attachments: bool = Field(True, description="Include attachments")
    password_protect: bool = Field(False, description="Password protection")
    
    # Request metadata
    requested_by: str = Field(..., description="Requester user ID")
    requested_at: datetime = Field(default_factory=datetime.now)
    
    # Processing status
    status: str = Field("pending", description="Export status")
    progress_percentage: float = Field(0.0, ge=0, le=100, description="Export progress")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Result information
    file_path: Optional[str] = Field(None, description="Generated file path")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL")
    expiry_timestamp: Optional[datetime] = Field(None, description="Download URL expiry")

class ComplianceBenchmark(BaseModel):
    """Compliance benchmark data"""
    benchmark_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Benchmark identifier")
    benchmark_name: str = Field(..., description="Benchmark name")
    benchmark_type: str = Field(..., description="Benchmark type (industry, regulatory, internal)")
    
    # Benchmark data
    framework: ComplianceFramework = Field(..., description="Associated framework")
    metric_benchmarks: Dict[str, Union[float, int, str]] = Field(..., description="Metric benchmark values")
    
    # Context and categorization
    industry: Optional[str] = Field(None, description="Industry classification")
    company_size: Optional[str] = Field(None, description="Company size category")
    geographic_region: Optional[str] = Field(None, description="Geographic region")
    
    # Data quality and source
    data_source: str = Field(..., description="Benchmark data source")
    sample_size: Optional[int] = Field(None, description="Sample size")
    confidence_level: float = Field(95.0, ge=0, le=100, description="Statistical confidence level")
    
    # Temporal information
    benchmark_period_start: date = Field(..., description="Benchmark period start")
    benchmark_period_end: date = Field(..., description="Benchmark period end")
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Usage and validity
    is_active: bool = Field(True, description="Benchmark active status")
    validity_period: Optional[int] = Field(None, description="Validity period in days")
    usage_count: int = Field(0, description="Usage count", ge=0)