"""
Integration Reports Service

This module generates comprehensive integration status reports for SI services,
tracking ERP connections, data flow, sync status, and integration health metrics.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntegrationStatus(Enum):
    """Status of ERP integrations"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    DISCONNECTED = "disconnected"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class ReportFormat(Enum):
    """Supported report formats"""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    EXCEL = "excel"


class ReportPeriod(Enum):
    """Report time periods"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"


@dataclass
class ERPConnectionInfo:
    """Information about ERP connection"""
    erp_type: str
    erp_name: str
    connection_status: IntegrationStatus
    last_connected: Optional[datetime] = None
    last_sync: Optional[datetime] = None
    total_records: int = 0
    sync_frequency: str = "unknown"
    error_count: int = 0
    last_error: Optional[str] = None
    version: Optional[str] = None
    configuration: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DataFlowMetrics:
    """Metrics for data flow between systems"""
    source_system: str
    target_system: str
    total_records_processed: int = 0
    successful_transfers: int = 0
    failed_transfers: int = 0
    average_processing_time: float = 0.0
    last_transfer: Optional[datetime] = None
    throughput_per_hour: float = 0.0
    error_rate: float = 0.0
    data_volume_mb: float = 0.0


@dataclass
class SyncStatusReport:
    """Report on synchronization status"""
    sync_id: str
    erp_type: str
    sync_type: str  # full, incremental
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    records_synced: int = 0
    records_failed: int = 0
    conflicts_detected: int = 0
    conflicts_resolved: int = 0
    error_details: List[str] = field(default_factory=list)


@dataclass
class IntegrationHealthScore:
    """Overall health score for integrations"""
    overall_score: float  # 0-100
    connection_score: float
    data_quality_score: float
    performance_score: float
    reliability_score: float
    security_score: float
    recommendations: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)


@dataclass
class IntegrationReport:
    """Comprehensive integration status report"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    report_type: str
    erp_connections: List[ERPConnectionInfo] = field(default_factory=list)
    data_flows: List[DataFlowMetrics] = field(default_factory=list)
    sync_reports: List[SyncStatusReport] = field(default_factory=list)
    health_score: Optional[IntegrationHealthScore] = None
    summary_metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReportConfig:
    """Configuration for report generation"""
    include_connections: bool = True
    include_data_flows: bool = True
    include_sync_status: bool = True
    include_health_score: bool = True
    include_alerts: bool = True
    include_recommendations: bool = True
    detail_level: str = "standard"  # minimal, standard, detailed
    output_format: ReportFormat = ReportFormat.JSON
    output_path: Optional[str] = None
    auto_schedule: bool = False
    schedule_frequency: Optional[str] = None


class IntegrationReportService:
    """
    Service for generating comprehensive integration status reports
    """
    
    def __init__(self, config: ReportConfig):
        self.config = config
        self.report_cache: Dict[str, IntegrationReport] = {}
        self.metrics_store: Dict[str, Any] = defaultdict(list)
        
        # Setup output directory
        if config.output_path:
            self.output_path = Path(config.output_path)
            self.output_path.mkdir(parents=True, exist_ok=True)
        else:
            self.output_path = None
    
    async def generate_integration_report(
        self,
        period: ReportPeriod = ReportPeriod.DAILY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        erp_types: Optional[List[str]] = None
    ) -> IntegrationReport:
        """Generate a comprehensive integration status report"""
        
        # Calculate report period
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
            period_start, period_end = start_date, end_date
        else:
            period_start, period_end = self._calculate_period(period)
        
        report_id = f"integration_{period.value}_{period_start.strftime('%Y%m%d_%H%M%S')}"
        
        report = IntegrationReport(
            report_id=report_id,
            generated_at=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            report_type=f"integration_{period.value}"
        )
        
        try:
            # Gather ERP connection information
            if self.config.include_connections:
                report.erp_connections = await self._gather_erp_connections(
                    period_start, period_end, erp_types
                )
            
            # Gather data flow metrics
            if self.config.include_data_flows:
                report.data_flows = await self._gather_data_flows(
                    period_start, period_end, erp_types
                )
            
            # Gather sync status reports
            if self.config.include_sync_status:
                report.sync_reports = await self._gather_sync_reports(
                    period_start, period_end, erp_types
                )
            
            # Calculate health score
            if self.config.include_health_score:
                report.health_score = await self._calculate_health_score(report)
            
            # Generate alerts
            if self.config.include_alerts:
                report.alerts = await self._generate_alerts(report)
            
            # Calculate summary metrics
            report.summary_metrics = self._calculate_summary_metrics(report)
            
            # Cache the report
            self.report_cache[report_id] = report
            
            # Export if output path is configured
            if self.output_path:
                await self._export_report(report)
            
            logger.info(f"Generated integration report {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate integration report: {e}")
            raise
    
    async def _gather_erp_connections(
        self,
        start_date: datetime,
        end_date: datetime,
        erp_types: Optional[List[str]] = None
    ) -> List[ERPConnectionInfo]:
        """Gather ERP connection information"""
        connections = []
        
        try:
            # This would typically query the data extractor or database
            # For now, we'll simulate connection data
            
            erp_systems = [
                {"type": "odoo", "name": "Odoo Production", "status": IntegrationStatus.HEALTHY},
                {"type": "sap", "name": "SAP ERP Central", "status": IntegrationStatus.WARNING},
                {"type": "quickbooks", "name": "QuickBooks Online", "status": IntegrationStatus.HEALTHY},
            ]
            
            for erp in erp_systems:
                if erp_types and erp["type"] not in erp_types:
                    continue
                
                connection = ERPConnectionInfo(
                    erp_type=erp["type"],
                    erp_name=erp["name"],
                    connection_status=erp["status"],
                    last_connected=datetime.now() - timedelta(minutes=5),
                    last_sync=datetime.now() - timedelta(hours=1),
                    total_records=1500,
                    sync_frequency="hourly",
                    error_count=2 if erp["status"] == IntegrationStatus.WARNING else 0,
                    version="v2.1.0"
                )
                
                if erp["status"] == IntegrationStatus.WARNING:
                    connection.last_error = "Connection timeout during last sync"
                
                connections.append(connection)
            
        except Exception as e:
            logger.error(f"Failed to gather ERP connections: {e}")
        
        return connections
    
    async def _gather_data_flows(
        self,
        start_date: datetime,
        end_date: datetime,
        erp_types: Optional[List[str]] = None
    ) -> List[DataFlowMetrics]:
        """Gather data flow metrics"""
        data_flows = []
        
        try:
            # Simulate data flow metrics
            flows = [
                {
                    "source": "odoo",
                    "target": "taxpoynt_platform",
                    "processed": 1200,
                    "successful": 1180,
                    "failed": 20,
                    "avg_time": 2.5,
                    "throughput": 480.0
                },
                {
                    "source": "sap",
                    "target": "taxpoynt_platform", 
                    "processed": 800,
                    "successful": 750,
                    "failed": 50,
                    "avg_time": 4.1,
                    "throughput": 200.0
                }
            ]
            
            for flow in flows:
                if erp_types and flow["source"] not in erp_types:
                    continue
                
                data_flow = DataFlowMetrics(
                    source_system=flow["source"],
                    target_system=flow["target"],
                    total_records_processed=flow["processed"],
                    successful_transfers=flow["successful"],
                    failed_transfers=flow["failed"],
                    average_processing_time=flow["avg_time"],
                    last_transfer=datetime.now() - timedelta(minutes=30),
                    throughput_per_hour=flow["throughput"],
                    error_rate=flow["failed"] / flow["processed"] * 100,
                    data_volume_mb=flow["processed"] * 0.5  # Estimate 0.5MB per record
                )
                
                data_flows.append(data_flow)
            
        except Exception as e:
            logger.error(f"Failed to gather data flows: {e}")
        
        return data_flows
    
    async def _gather_sync_reports(
        self,
        start_date: datetime,
        end_date: datetime,
        erp_types: Optional[List[str]] = None
    ) -> List[SyncStatusReport]:
        """Gather synchronization status reports"""
        sync_reports = []
        
        try:
            # This would query sync service for actual sync reports
            # For now, simulate sync data
            
            syncs = [
                {
                    "id": "sync_odoo_20241201_120000",
                    "erp": "odoo",
                    "type": "incremental",
                    "status": "completed",
                    "records": 150,
                    "failed": 2,
                    "conflicts": 1,
                    "duration": 45.2
                },
                {
                    "id": "sync_sap_20241201_110000",
                    "erp": "sap",
                    "type": "full",
                    "status": "failed",
                    "records": 0,
                    "failed": 500,
                    "conflicts": 0,
                    "duration": 120.5
                }
            ]
            
            for sync in syncs:
                if erp_types and sync["erp"] not in erp_types:
                    continue
                
                sync_report = SyncStatusReport(
                    sync_id=sync["id"],
                    erp_type=sync["erp"],
                    sync_type=sync["type"],
                    status=sync["status"],
                    start_time=start_date + timedelta(hours=1),
                    end_time=start_date + timedelta(hours=1, seconds=sync["duration"]),
                    duration_seconds=sync["duration"],
                    records_synced=sync["records"],
                    records_failed=sync["failed"],
                    conflicts_detected=sync["conflicts"],
                    conflicts_resolved=sync["conflicts"]
                )
                
                if sync["status"] == "failed":
                    sync_report.error_details = ["Connection timeout", "Authentication failed"]
                
                sync_reports.append(sync_report)
            
        except Exception as e:
            logger.error(f"Failed to gather sync reports: {e}")
        
        return sync_reports
    
    async def _calculate_health_score(self, report: IntegrationReport) -> IntegrationHealthScore:
        """Calculate overall integration health score"""
        try:
            # Connection score based on active connections
            total_connections = len(report.erp_connections)
            healthy_connections = sum(
                1 for conn in report.erp_connections 
                if conn.connection_status == IntegrationStatus.HEALTHY
            )
            connection_score = (healthy_connections / total_connections * 100) if total_connections > 0 else 0
            
            # Data quality score based on success rates
            total_processed = sum(flow.total_records_processed for flow in report.data_flows)
            total_successful = sum(flow.successful_transfers for flow in report.data_flows)
            data_quality_score = (total_successful / total_processed * 100) if total_processed > 0 else 0
            
            # Performance score based on sync completion
            completed_syncs = sum(
                1 for sync in report.sync_reports 
                if sync.status == "completed"
            )
            total_syncs = len(report.sync_reports)
            performance_score = (completed_syncs / total_syncs * 100) if total_syncs > 0 else 0
            
            # Reliability score based on error rates
            total_errors = sum(conn.error_count for conn in report.erp_connections)
            reliability_score = max(0, 100 - (total_errors * 10))  # Reduce by 10 per error
            
            # Security score (simplified - would be more complex in practice)
            security_score = 95.0  # Placeholder
            
            # Overall score is weighted average
            overall_score = (
                connection_score * 0.25 +
                data_quality_score * 0.30 +
                performance_score * 0.25 +
                reliability_score * 0.15 +
                security_score * 0.05
            )
            
            # Generate recommendations
            recommendations = []
            critical_issues = []
            
            if connection_score < 80:
                recommendations.append("Check ERP connection configurations")
                if connection_score < 50:
                    critical_issues.append("Multiple ERP connections are down")
            
            if data_quality_score < 90:
                recommendations.append("Investigate data transfer failures")
                if data_quality_score < 70:
                    critical_issues.append("High data transfer failure rate")
            
            if performance_score < 80:
                recommendations.append("Review sync schedules and performance")
            
            if reliability_score < 85:
                recommendations.append("Address recurring errors in integrations")
            
            return IntegrationHealthScore(
                overall_score=overall_score,
                connection_score=connection_score,
                data_quality_score=data_quality_score,
                performance_score=performance_score,
                reliability_score=reliability_score,
                security_score=security_score,
                recommendations=recommendations,
                critical_issues=critical_issues
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return IntegrationHealthScore(
                overall_score=0,
                connection_score=0,
                data_quality_score=0,
                performance_score=0,
                reliability_score=0,
                security_score=0
            )
    
    async def _generate_alerts(self, report: IntegrationReport) -> List[Dict[str, Any]]:
        """Generate alerts based on report data"""
        alerts = []
        
        try:
            # Connection alerts
            for conn in report.erp_connections:
                if conn.connection_status == IntegrationStatus.ERROR:
                    alerts.append({
                        "type": "connection_error",
                        "severity": "critical",
                        "message": f"ERP connection {conn.erp_name} is down",
                        "erp_type": conn.erp_type,
                        "timestamp": datetime.now()
                    })
                elif conn.connection_status == IntegrationStatus.WARNING:
                    alerts.append({
                        "type": "connection_warning",
                        "severity": "warning",
                        "message": f"ERP connection {conn.erp_name} has issues",
                        "erp_type": conn.erp_type,
                        "details": conn.last_error,
                        "timestamp": datetime.now()
                    })
            
            # Data flow alerts
            for flow in report.data_flows:
                if flow.error_rate > 10:
                    alerts.append({
                        "type": "high_error_rate",
                        "severity": "warning" if flow.error_rate < 20 else "critical",
                        "message": f"High error rate ({flow.error_rate:.1f}%) in {flow.source_system}",
                        "source_system": flow.source_system,
                        "error_rate": flow.error_rate,
                        "timestamp": datetime.now()
                    })
                
                if flow.throughput_per_hour < 100:  # Low throughput threshold
                    alerts.append({
                        "type": "low_throughput",
                        "severity": "info",
                        "message": f"Low throughput ({flow.throughput_per_hour:.1f}/hr) from {flow.source_system}",
                        "source_system": flow.source_system,
                        "throughput": flow.throughput_per_hour,
                        "timestamp": datetime.now()
                    })
            
            # Sync alerts
            failed_syncs = [sync for sync in report.sync_reports if sync.status == "failed"]
            if failed_syncs:
                alerts.append({
                    "type": "sync_failures",
                    "severity": "critical",
                    "message": f"{len(failed_syncs)} sync operations failed",
                    "failed_syncs": len(failed_syncs),
                    "timestamp": datetime.now()
                })
            
            # Health score alerts
            if report.health_score and report.health_score.overall_score < 70:
                alerts.append({
                    "type": "low_health_score",
                    "severity": "warning" if report.health_score.overall_score > 50 else "critical",
                    "message": f"Integration health score is low ({report.health_score.overall_score:.1f}%)",
                    "health_score": report.health_score.overall_score,
                    "critical_issues": report.health_score.critical_issues,
                    "timestamp": datetime.now()
                })
            
        except Exception as e:
            logger.error(f"Failed to generate alerts: {e}")
        
        return alerts
    
    def _calculate_summary_metrics(self, report: IntegrationReport) -> Dict[str, Any]:
        """Calculate summary metrics for the report"""
        try:
            return {
                "total_erp_connections": len(report.erp_connections),
                "healthy_connections": sum(
                    1 for conn in report.erp_connections 
                    if conn.connection_status == IntegrationStatus.HEALTHY
                ),
                "total_records_processed": sum(
                    flow.total_records_processed for flow in report.data_flows
                ),
                "total_successful_transfers": sum(
                    flow.successful_transfers for flow in report.data_flows
                ),
                "total_failed_transfers": sum(
                    flow.failed_transfers for flow in report.data_flows
                ),
                "average_error_rate": sum(
                    flow.error_rate for flow in report.data_flows
                ) / len(report.data_flows) if report.data_flows else 0,
                "total_sync_operations": len(report.sync_reports),
                "completed_syncs": sum(
                    1 for sync in report.sync_reports 
                    if sync.status == "completed"
                ),
                "failed_syncs": sum(
                    1 for sync in report.sync_reports 
                    if sync.status == "failed"
                ),
                "total_alerts": len(report.alerts),
                "critical_alerts": sum(
                    1 for alert in report.alerts 
                    if alert.get("severity") == "critical"
                ),
                "overall_health_score": report.health_score.overall_score if report.health_score else 0,
                "report_period_hours": (report.period_end - report.period_start).total_seconds() / 3600
            }
        except Exception as e:
            logger.error(f"Failed to calculate summary metrics: {e}")
            return {}
    
    def _calculate_period(self, period: ReportPeriod) -> Tuple[datetime, datetime]:
        """Calculate start and end times for report period"""
        now = datetime.now()
        
        if period == ReportPeriod.HOURLY:
            start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            end = now.replace(minute=0, second=0, microsecond=0)
        elif period == ReportPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == ReportPeriod.WEEKLY:
            days_since_monday = now.weekday()
            start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_since_monday + 7)
            end = start + timedelta(days=7)
        elif period == ReportPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 1:
                start = start.replace(year=start.year - 1, month=12)
            else:
                start = start.replace(month=start.month - 1)
            end = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == ReportPeriod.QUARTERLY:
            current_quarter = (now.month - 1) // 3 + 1
            start_month = (current_quarter - 2) * 3 + 1
            if start_month <= 0:
                start_month += 12
                start_year = now.year - 1
            else:
                start_year = now.year
            start = datetime(start_year, start_month, 1)
            end_month = (current_quarter - 1) * 3 + 1
            end = datetime(now.year, end_month, 1)
        else:
            # Default to last 24 hours
            start = now - timedelta(days=1)
            end = now
        
        return start, end
    
    async def _export_report(self, report: IntegrationReport) -> None:
        """Export report to configured format and location"""
        if not self.output_path:
            return
        
        try:
            filename = f"{report.report_id}.{self.config.output_format.value}"
            filepath = self.output_path / filename
            
            if self.config.output_format == ReportFormat.JSON:
                await self._export_json(report, filepath)
            elif self.config.output_format == ReportFormat.CSV:
                await self._export_csv(report, filepath)
            elif self.config.output_format == ReportFormat.HTML:
                await self._export_html(report, filepath)
            else:
                logger.warning(f"Export format {self.config.output_format.value} not implemented")
            
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
    
    async def _export_json(self, report: IntegrationReport, filepath: Path) -> None:
        """Export report as JSON"""
        report_dict = self._report_to_dict(report)
        with open(filepath, 'w') as f:
            json.dump(report_dict, f, indent=2, default=str)
    
    async def _export_csv(self, report: IntegrationReport, filepath: Path) -> None:
        """Export report as CSV (simplified version)"""
        import csv
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write summary information
            writer.writerow(['Integration Report Summary'])
            writer.writerow(['Report ID', report.report_id])
            writer.writerow(['Generated At', report.generated_at])
            writer.writerow(['Period', f"{report.period_start} to {report.period_end}"])
            writer.writerow([])
            
            # Write ERP connections
            writer.writerow(['ERP Connections'])
            writer.writerow(['Type', 'Name', 'Status', 'Last Connected', 'Total Records', 'Errors'])
            for conn in report.erp_connections:
                writer.writerow([
                    conn.erp_type,
                    conn.erp_name,
                    conn.connection_status.value,
                    conn.last_connected,
                    conn.total_records,
                    conn.error_count
                ])
    
    async def _export_html(self, report: IntegrationReport, filepath: Path) -> None:
        """Export report as HTML"""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Integration Report - {report_id}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 10px; border: 1px solid #ddd; border-radius: 3px; }}
                .alert {{ padding: 10px; margin: 5px 0; border-radius: 3px; }}
                .critical {{ background: #ffebee; border-left: 4px solid #f44336; }}
                .warning {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
                .info {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
                table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Integration Report</h1>
                <p><strong>Report ID:</strong> {report_id}</p>
                <p><strong>Generated:</strong> {generated_at}</p>
                <p><strong>Period:</strong> {period_start} to {period_end}</p>
            </div>
            
            <div class="section">
                <h2>Summary Metrics</h2>
                <div class="metric">
                    <strong>Total Connections:</strong> {total_connections}
                </div>
                <div class="metric">
                    <strong>Healthy Connections:</strong> {healthy_connections}
                </div>
                <div class="metric">
                    <strong>Records Processed:</strong> {total_records}
                </div>
                <div class="metric">
                    <strong>Health Score:</strong> {health_score}%
                </div>
            </div>
            
            <div class="section">
                <h2>Alerts</h2>
                {alerts_html}
            </div>
            
            <div class="section">
                <h2>ERP Connections</h2>
                {connections_table}
            </div>
        </body>
        </html>
        """
        
        # Generate alerts HTML
        alerts_html = ""
        for alert in report.alerts:
            severity_class = alert.get("severity", "info")
            alerts_html += f'<div class="alert {severity_class}">{alert["message"]}</div>'
        
        # Generate connections table
        connections_table = "<table><tr><th>Type</th><th>Name</th><th>Status</th><th>Last Connected</th></tr>"
        for conn in report.erp_connections:
            connections_table += f"<tr><td>{conn.erp_type}</td><td>{conn.erp_name}</td><td>{conn.connection_status.value}</td><td>{conn.last_connected}</td></tr>"
        connections_table += "</table>"
        
        html_content = html_template.format(
            report_id=report.report_id,
            generated_at=report.generated_at,
            period_start=report.period_start,
            period_end=report.period_end,
            total_connections=len(report.erp_connections),
            healthy_connections=sum(1 for c in report.erp_connections if c.connection_status == IntegrationStatus.HEALTHY),
            total_records=sum(f.total_records_processed for f in report.data_flows),
            health_score=f"{report.health_score.overall_score:.1f}" if report.health_score else "N/A",
            alerts_html=alerts_html or "<p>No alerts</p>",
            connections_table=connections_table
        )
        
        with open(filepath, 'w') as f:
            f.write(html_content)
    
    def _report_to_dict(self, report: IntegrationReport) -> Dict[str, Any]:
        """Convert report to dictionary for JSON export"""
        return {
            "report_id": report.report_id,
            "generated_at": report.generated_at.isoformat(),
            "period_start": report.period_start.isoformat(),
            "period_end": report.period_end.isoformat(),
            "report_type": report.report_type,
            "erp_connections": [
                {
                    "erp_type": conn.erp_type,
                    "erp_name": conn.erp_name,
                    "connection_status": conn.connection_status.value,
                    "last_connected": conn.last_connected.isoformat() if conn.last_connected else None,
                    "last_sync": conn.last_sync.isoformat() if conn.last_sync else None,
                    "total_records": conn.total_records,
                    "sync_frequency": conn.sync_frequency,
                    "error_count": conn.error_count,
                    "last_error": conn.last_error,
                    "version": conn.version
                }
                for conn in report.erp_connections
            ],
            "data_flows": [
                {
                    "source_system": flow.source_system,
                    "target_system": flow.target_system,
                    "total_records_processed": flow.total_records_processed,
                    "successful_transfers": flow.successful_transfers,
                    "failed_transfers": flow.failed_transfers,
                    "average_processing_time": flow.average_processing_time,
                    "throughput_per_hour": flow.throughput_per_hour,
                    "error_rate": flow.error_rate,
                    "data_volume_mb": flow.data_volume_mb
                }
                for flow in report.data_flows
            ],
            "sync_reports": [
                {
                    "sync_id": sync.sync_id,
                    "erp_type": sync.erp_type,
                    "sync_type": sync.sync_type,
                    "status": sync.status,
                    "start_time": sync.start_time.isoformat(),
                    "end_time": sync.end_time.isoformat() if sync.end_time else None,
                    "duration_seconds": sync.duration_seconds,
                    "records_synced": sync.records_synced,
                    "records_failed": sync.records_failed,
                    "conflicts_detected": sync.conflicts_detected,
                    "conflicts_resolved": sync.conflicts_resolved,
                    "error_details": sync.error_details
                }
                for sync in report.sync_reports
            ],
            "health_score": {
                "overall_score": report.health_score.overall_score,
                "connection_score": report.health_score.connection_score,
                "data_quality_score": report.health_score.data_quality_score,
                "performance_score": report.health_score.performance_score,
                "reliability_score": report.health_score.reliability_score,
                "security_score": report.health_score.security_score,
                "recommendations": report.health_score.recommendations,
                "critical_issues": report.health_score.critical_issues
            } if report.health_score else None,
            "summary_metrics": report.summary_metrics,
            "alerts": report.alerts,
            "metadata": report.metadata
        }
    
    def get_cached_report(self, report_id: str) -> Optional[IntegrationReport]:
        """Get a cached report by ID"""
        return self.report_cache.get(report_id)
    
    def list_cached_reports(self) -> List[str]:
        """List all cached report IDs"""
        return list(self.report_cache.keys())
    
    async def cleanup_old_reports(self, max_age_hours: int = 168) -> int:  # Default 1 week
        """Clean up old cached reports"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        reports_to_remove = []
        for report_id, report in self.report_cache.items():
            if report.generated_at < cutoff_time:
                reports_to_remove.append(report_id)
        
        for report_id in reports_to_remove:
            del self.report_cache[report_id]
            cleaned_count += 1
        
        return cleaned_count


# Factory function for creating integration report service
def create_integration_report_service(config: Optional[ReportConfig] = None) -> IntegrationReportService:
    """Factory function to create an integration report service"""
    if config is None:
        config = ReportConfig()
    
    return IntegrationReportService(config)