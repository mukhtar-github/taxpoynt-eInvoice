"""
Compliance Dashboard Generator
=============================
Generates interactive compliance dashboards with real-time metrics, charts, and KPIs
for executive and operational compliance monitoring.
"""
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from dataclasses import dataclass

from .models import (
    DashboardConfiguration, ComplianceMetrics, AuditTrail,
    ReportFormat, ComplianceStatus, RiskLevel
)
from ..orchestrator.models import (
    ComplianceRequest, ComplianceResult, ValidationResult
)

logger = logging.getLogger(__name__)


@dataclass
class ChartData:
    """Chart data structure for dashboard visualizations."""
    chart_type: str  # bar, line, pie, donut, gauge, scatter
    title: str
    data: List[Dict[str, Any]]
    labels: List[str]
    colors: Optional[List[str]] = None
    options: Optional[Dict[str, Any]] = None


@dataclass
class DashboardWidget:
    """Individual dashboard widget configuration."""
    widget_id: str
    widget_type: str  # chart, metric, table, alert, timeline
    title: str
    position: Dict[str, int]  # x, y, width, height
    data: Union[ChartData, Dict[str, Any]]
    refresh_interval: Optional[int] = None  # seconds
    permissions: Optional[List[str]] = None


class DashboardGenerator:
    """
    Generates comprehensive compliance dashboards with real-time monitoring,
    executive summaries, and operational metrics.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.widget_templates = self._initialize_widget_templates()
        self.dashboard_themes = self._initialize_dashboard_themes()

    def _initialize_widget_templates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize pre-built widget templates."""
        return {
            "compliance_score_gauge": {
                "type": "gauge",
                "config": {
                    "min": 0,
                    "max": 100,
                    "thresholds": [
                        {"value": 70, "color": "red"},
                        {"value": 85, "color": "yellow"},
                        {"value": 100, "color": "green"}
                    ]
                }
            },
            "framework_compliance_bar": {
                "type": "bar",
                "config": {
                    "orientation": "horizontal",
                    "show_values": True
                }
            },
            "risk_distribution_pie": {
                "type": "pie",
                "config": {
                    "show_legend": True,
                    "show_percentages": True
                }
            },
            "compliance_trends_line": {
                "type": "line",
                "config": {
                    "show_points": True,
                    "smooth": True,
                    "fill": False
                }
            },
            "audit_timeline": {
                "type": "timeline",
                "config": {
                    "show_time": True,
                    "group_by_date": True
                }
            }
        }

    def _initialize_dashboard_themes(self) -> Dict[str, Dict[str, Any]]:
        """Initialize dashboard themes and styling."""
        return {
            "executive": {
                "colors": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"],
                "background": "#ffffff",
                "text_color": "#333333",
                "grid_color": "#f0f0f0",
                "font_family": "Arial, sans-serif"
            },
            "operational": {
                "colors": ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#8B5A3C"],
                "background": "#f8f9fa",
                "text_color": "#212529",
                "grid_color": "#e9ecef", 
                "font_family": "Roboto, sans-serif"
            },
            "dark": {
                "colors": ["#8dd3c7", "#ffffb3", "#bebada", "#fb8072", "#80b1d3"],
                "background": "#2f3349",
                "text_color": "#ffffff",
                "grid_color": "#404560",
                "font_family": "Inter, sans-serif"
            }
        }

    async def generate_executive_dashboard(
        self,
        organization_id: str,
        date_range: Tuple[date, date],
        config: Optional[DashboardConfiguration] = None
    ) -> Dict[str, Any]:
        """
        Generate executive-level compliance dashboard with high-level KPIs and trends.
        
        Args:
            organization_id: Organization identifier
            date_range: Date range for dashboard data
            config: Dashboard configuration options
            
        Returns:
            Dict containing complete dashboard structure
        """
        try:
            self.logger.info(f"Generating executive dashboard for organization {organization_id}")
            
            dashboard_id = str(uuid.uuid4())
            start_date, end_date = date_range
            
            # Generate executive widgets
            widgets = []
            
            # Overall compliance score gauge
            compliance_score = await self._calculate_overall_compliance_score(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_compliance_score_widget(compliance_score))
            
            # Framework compliance overview
            framework_scores = await self._get_framework_compliance_scores(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_framework_overview_widget(framework_scores))
            
            # Risk level distribution
            risk_distribution = await self._get_risk_distribution(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_risk_distribution_widget(risk_distribution))
            
            # Compliance trends over time
            trends = await self._get_compliance_trends(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_trends_widget(trends))
            
            # Key metrics summary
            key_metrics = await self._get_key_metrics_summary(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_metrics_summary_widget(key_metrics))
            
            # Recent critical issues
            critical_issues = await self._get_recent_critical_issues(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_critical_issues_widget(critical_issues))
            
            dashboard = {
                "dashboard_id": dashboard_id,
                "type": "executive",
                "title": "Executive Compliance Dashboard",
                "organization_id": organization_id,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "theme": config.theme if config else "executive",
                "widgets": widgets,
                "layout": self._get_executive_layout(),
                "refresh_interval": 300,  # 5 minutes
                "permissions": ["executive", "compliance_manager"]
            }
            
            self.logger.info(f"Executive dashboard generated successfully: {dashboard_id}")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating executive dashboard: {str(e)}")
            raise

    async def generate_operational_dashboard(
        self,
        organization_id: str,
        date_range: Tuple[date, date],
        framework_focus: Optional[List[str]] = None,
        config: Optional[DashboardConfiguration] = None
    ) -> Dict[str, Any]:
        """
        Generate operational compliance dashboard with detailed metrics and drill-down capabilities.
        
        Args:
            organization_id: Organization identifier
            date_range: Date range for dashboard data
            framework_focus: Specific frameworks to focus on
            config: Dashboard configuration options
            
        Returns:
            Dict containing complete dashboard structure
        """
        try:
            self.logger.info(f"Generating operational dashboard for organization {organization_id}")
            
            dashboard_id = str(uuid.uuid4())
            start_date, end_date = date_range
            frameworks = framework_focus or ["FIRS", "CAC", "NDPA", "ISO27001", "UBL"]
            
            widgets = []
            
            # Framework-specific compliance scores
            for framework in frameworks:
                framework_data = await self._get_framework_detailed_metrics(
                    organization_id, framework, start_date, end_date
                )
                widgets.append(self._create_framework_detail_widget(framework, framework_data))
            
            # Validation results breakdown
            validation_breakdown = await self._get_validation_results_breakdown(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_validation_breakdown_widget(validation_breakdown))
            
            # Issue tracking and resolution
            issue_tracking = await self._get_issue_tracking_data(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_issue_tracking_widget(issue_tracking))
            
            # Audit activity timeline
            audit_activity = await self._get_audit_activity_timeline(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_audit_timeline_widget(audit_activity))
            
            # Performance metrics
            performance_metrics = await self._get_performance_metrics(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_performance_metrics_widget(performance_metrics))
            
            # Remediation planning
            remediation_plan = await self._get_remediation_planning_data(
                organization_id, start_date, end_date
            )
            widgets.append(self._create_remediation_planning_widget(remediation_plan))
            
            dashboard = {
                "dashboard_id": dashboard_id,
                "type": "operational",
                "title": "Operational Compliance Dashboard",
                "organization_id": organization_id,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "theme": config.theme if config else "operational",
                "frameworks": frameworks,
                "widgets": widgets,
                "layout": self._get_operational_layout(),
                "refresh_interval": 60,  # 1 minute
                "permissions": ["compliance_officer", "operational_manager"]
            }
            
            self.logger.info(f"Operational dashboard generated successfully: {dashboard_id}")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating operational dashboard: {str(e)}")
            raise

    async def generate_regulatory_dashboard(
        self,
        organization_id: str,
        regulatory_framework: str,
        date_range: Tuple[date, date],
        config: Optional[DashboardConfiguration] = None
    ) -> Dict[str, Any]:
        """
        Generate framework-specific regulatory compliance dashboard.
        
        Args:
            organization_id: Organization identifier
            regulatory_framework: Specific regulatory framework (FIRS, CAC, etc.)
            date_range: Date range for dashboard data
            config: Dashboard configuration options
            
        Returns:
            Dict containing framework-specific dashboard
        """
        try:
            self.logger.info(f"Generating {regulatory_framework} dashboard for organization {organization_id}")
            
            dashboard_id = str(uuid.uuid4())
            start_date, end_date = date_range
            
            widgets = []
            
            # Framework compliance score and trend
            framework_score = await self._get_framework_compliance_trend(
                organization_id, regulatory_framework, start_date, end_date
            )
            widgets.append(self._create_framework_score_trend_widget(regulatory_framework, framework_score))
            
            # Requirements compliance matrix
            requirements_matrix = await self._get_requirements_compliance_matrix(
                organization_id, regulatory_framework, start_date, end_date
            )
            widgets.append(self._create_requirements_matrix_widget(regulatory_framework, requirements_matrix))
            
            # Submission tracking
            submission_tracking = await self._get_submission_tracking(
                organization_id, regulatory_framework, start_date, end_date
            )
            widgets.append(self._create_submission_tracking_widget(regulatory_framework, submission_tracking))
            
            # Penalty and fine tracking
            penalty_tracking = await self._get_penalty_tracking(
                organization_id, regulatory_framework, start_date, end_date
            )
            widgets.append(self._create_penalty_tracking_widget(regulatory_framework, penalty_tracking))
            
            # Document management status
            document_status = await self._get_document_management_status(
                organization_id, regulatory_framework, start_date, end_date
            )
            widgets.append(self._create_document_status_widget(regulatory_framework, document_status))
            
            dashboard = {
                "dashboard_id": dashboard_id,
                "type": "regulatory",
                "title": f"{regulatory_framework} Compliance Dashboard",
                "organization_id": organization_id,
                "regulatory_framework": regulatory_framework,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "generated_at": datetime.now().isoformat(),
                "theme": config.theme if config else "operational",
                "widgets": widgets,
                "layout": self._get_regulatory_layout(),
                "refresh_interval": 120,  # 2 minutes
                "permissions": [f"{regulatory_framework.lower()}_specialist", "compliance_officer"]
            }
            
            self.logger.info(f"{regulatory_framework} dashboard generated successfully: {dashboard_id}")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating {regulatory_framework} dashboard: {str(e)}")
            raise

    def _create_compliance_score_widget(self, score_data: Dict[str, Any]) -> DashboardWidget:
        """Create compliance score gauge widget."""
        return DashboardWidget(
            widget_id=str(uuid.uuid4()),
            widget_type="gauge",
            title="Overall Compliance Score",
            position={"x": 0, "y": 0, "width": 4, "height": 3},
            data=ChartData(
                chart_type="gauge",
                title="Overall Compliance Score",
                data=[{"value": score_data["score"], "label": "Compliance %"}],
                labels=["Compliance Score"],
                options={
                    "min": 0,
                    "max": 100,
                    "thresholds": [
                        {"value": 70, "color": "#d62728"},
                        {"value": 85, "color": "#ff7f0e"}, 
                        {"value": 100, "color": "#2ca02c"}
                    ],
                    "show_value": True,
                    "show_title": True
                }
            ),
            refresh_interval=300
        )

    def _create_framework_overview_widget(self, framework_scores: Dict[str, float]) -> DashboardWidget:
        """Create framework compliance overview widget."""
        data = [{"framework": k, "score": v} for k, v in framework_scores.items()]
        
        return DashboardWidget(
            widget_id=str(uuid.uuid4()),
            widget_type="bar",
            title="Framework Compliance Scores",
            position={"x": 4, "y": 0, "width": 8, "height": 3},
            data=ChartData(
                chart_type="bar",
                title="Framework Compliance Scores",
                data=data,
                labels=list(framework_scores.keys()),
                options={
                    "orientation": "horizontal",
                    "show_values": True,
                    "color_threshold": True
                }
            ),
            refresh_interval=300
        )

    def _get_executive_layout(self) -> Dict[str, Any]:
        """Get executive dashboard layout configuration."""
        return {
            "grid_size": 12,
            "row_height": 100,
            "margin": [10, 10],
            "container_padding": [10, 10],
            "responsive_breakpoints": {
                "lg": 1200,
                "md": 996,
                "sm": 768,
                "xs": 480
            }
        }

    def _get_operational_layout(self) -> Dict[str, Any]:
        """Get operational dashboard layout configuration."""
        return {
            "grid_size": 12,
            "row_height": 80,
            "margin": [5, 5],
            "container_padding": [5, 5],
            "responsive_breakpoints": {
                "lg": 1200,
                "md": 996,
                "sm": 768,
                "xs": 480
            }
        }

    def _get_regulatory_layout(self) -> Dict[str, Any]:
        """Get regulatory dashboard layout configuration."""
        return {
            "grid_size": 12,
            "row_height": 90,
            "margin": [8, 8],
            "container_padding": [8, 8],
            "responsive_breakpoints": {
                "lg": 1200,
                "md": 996,
                "sm": 768,
                "xs": 480
            }
        }

    # Placeholder methods for data retrieval - would integrate with actual data sources
    async def _calculate_overall_compliance_score(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Calculate overall compliance score."""
        return {"score": 87.5, "trend": "+2.3%", "status": "improving"}

    async def _get_framework_compliance_scores(self, org_id: str, start: date, end: date) -> Dict[str, float]:
        """Get compliance scores by framework."""
        return {
            "FIRS": 92.1,
            "CAC": 85.7,
            "NDPA": 88.3,
            "ISO27001": 79.2,
            "UBL": 91.8
        }

    async def _get_risk_distribution(self, org_id: str, start: date, end: date) -> Dict[str, int]:
        """Get risk level distribution."""
        return {
            "Low": 45,
            "Medium": 32,
            "High": 18,
            "Critical": 5
        }

    async def _get_compliance_trends(self, org_id: str, start: date, end: date) -> List[Dict[str, Any]]:
        """Get compliance trends over time."""
        return [
            {"date": "2024-01-01", "score": 82.1},
            {"date": "2024-02-01", "score": 84.3},
            {"date": "2024-03-01", "score": 87.5}
        ]

    async def _get_key_metrics_summary(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Get key metrics summary."""
        return {
            "total_validations": 1247,
            "passed_validations": 1089,
            "failed_validations": 158,
            "compliance_rate": 87.3
        }

    async def _get_recent_critical_issues(self, org_id: str, start: date, end: date) -> List[Dict[str, Any]]:
        """Get recent critical compliance issues."""
        return [
            {
                "issue_id": "ISS-001",
                "description": "Missing FIRS e-invoice validation",
                "severity": "High",
                "created_at": "2024-07-28T10:30:00Z"
            }
        ]

    # Additional placeholder methods for operational and regulatory dashboards
    async def _get_framework_detailed_metrics(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get detailed metrics for specific framework."""
        return {"score": 85.7, "validations": 234, "issues": 12}

    async def _get_validation_results_breakdown(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Get validation results breakdown."""
        return {"passed": 1089, "failed": 158, "pending": 23}

    async def _get_issue_tracking_data(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Get issue tracking data."""
        return {"open": 45, "in_progress": 23, "resolved": 167}

    async def _get_audit_activity_timeline(self, org_id: str, start: date, end: date) -> List[Dict[str, Any]]:
        """Get audit activity timeline."""
        return []

    async def _get_performance_metrics(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Get performance metrics."""
        return {"avg_response_time": 245, "throughput": 1247}

    async def _get_remediation_planning_data(self, org_id: str, start: date, end: date) -> Dict[str, Any]:
        """Get remediation planning data."""
        return {"planned": 12, "in_progress": 8, "completed": 23}

    async def _get_framework_compliance_trend(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get framework compliance trend."""
        return {"current_score": 85.7, "trend": "+1.2%", "history": []}

    async def _get_requirements_compliance_matrix(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get requirements compliance matrix."""
        return {"total_requirements": 45, "compliant": 38, "non_compliant": 7}

    async def _get_submission_tracking(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get submission tracking data."""
        return {"submitted": 12, "pending": 3, "overdue": 1}

    async def _get_penalty_tracking(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get penalty and fine tracking."""
        return {"total_penalties": 2, "total_amount": 50000.0, "paid": 1}

    async def _get_document_management_status(self, org_id: str, framework: str, start: date, end: date) -> Dict[str, Any]:
        """Get document management status."""
        return {"total_docs": 156, "up_to_date": 142, "expiring_soon": 14}