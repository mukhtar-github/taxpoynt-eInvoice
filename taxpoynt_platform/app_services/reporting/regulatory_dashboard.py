"""
APP Service: Regulatory Dashboard
Provides comprehensive regulatory compliance dashboards and monitoring
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, Counter

from .transmission_reports import TransmissionReportGenerator, TransmissionSummary
from .compliance_metrics import ComplianceMetricsMonitor, ComplianceStatus, ComplianceCategory
from .performance_analytics import PerformanceAnalyzer, PerformanceStatus, AnalysisType


class DashboardType(str, Enum):
    """Types of regulatory dashboards"""
    EXECUTIVE = "executive"
    OPERATIONAL = "operational"
    COMPLIANCE = "compliance"
    TECHNICAL = "technical"
    AUDIT = "audit"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RegulatoryStatus(str, Enum):
    """Overall regulatory status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    AT_RISK = "at_risk"
    UNDER_REVIEW = "under_review"


@dataclass
class DashboardWidget:
    """Individual dashboard widget configuration"""
    widget_id: str
    title: str
    type: str  # chart, metric, table, alert, etc.
    data_source: str
    refresh_interval: int  # seconds
    position: Dict[str, int]  # x, y, width, height
    config: Dict[str, Any]
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RegulatoryAlert:
    """Regulatory compliance alert"""
    alert_id: str
    title: str
    description: str
    severity: AlertSeverity
    category: str
    triggered_at: datetime
    threshold_value: Optional[Union[float, str]] = None
    current_value: Optional[Union[float, str]] = None
    remediation_steps: Optional[List[str]] = None
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['triggered_at'] = self.triggered_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data


@dataclass
class DashboardData:
    """Complete dashboard data structure"""
    dashboard_id: str
    dashboard_type: DashboardType
    generated_at: datetime
    overall_status: RegulatoryStatus
    summary_metrics: Dict[str, Any]
    compliance_score: float
    performance_score: float
    alerts: List[RegulatoryAlert]
    widgets: List[DashboardWidget]
    recommendations: List[str]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['generated_at'] = self.generated_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data


class DashboardDataAggregator:
    """Aggregates data from various sources for dashboard display"""
    
    def __init__(self, 
                 transmission_reporter: Optional[TransmissionReportGenerator] = None,
                 compliance_monitor: Optional[ComplianceMetricsMonitor] = None,
                 performance_analyzer: Optional[PerformanceAnalyzer] = None):
        self.transmission_reporter = transmission_reporter
        self.compliance_monitor = compliance_monitor
        self.performance_analyzer = performance_analyzer
        self.logger = logging.getLogger(__name__)
    
    async def get_executive_summary(self) -> Dict[str, Any]:
        """Get executive-level summary data"""
        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)
        
        summary = {
            'timestamp': now.isoformat(),
            'period': '24 hours',
            'overall_status': 'compliant',
            'key_metrics': {},
            'alerts': [],
            'trends': {}
        }
        
        try:
            # Get transmission summary
            if self.transmission_reporter:
                transmission_config = type('Config', (), {
                    'start_date': last_24h,
                    'end_date': now,
                    'format': 'json',
                    'include_details': False
                })()
                
                transmission_report = await self.transmission_reporter.generate_report(transmission_config)
                transmission_summary = transmission_report['report_data']['summary']
                
                summary['key_metrics']['transmission'] = {
                    'total_transmissions': transmission_summary['total_transmissions'],
                    'success_rate': transmission_summary['success_rate'],
                    'average_processing_time': transmission_summary['average_processing_time']
                }
            
            # Get compliance status
            if self.compliance_monitor:
                compliance_report = await self.compliance_monitor.check_compliance(last_24h, now)
                
                summary['key_metrics']['compliance'] = {
                    'overall_score': compliance_report.overall_score,
                    'status': compliance_report.overall_status.value,
                    'violations_count': len(compliance_report.violations)
                }
                
                # Add critical violations as alerts
                for violation in compliance_report.violations:
                    if violation.severity.value in ['critical', 'high']:
                        summary['alerts'].append({
                            'id': violation.violation_id,
                            'title': violation.rule_name,
                            'severity': violation.severity.value,
                            'category': violation.category.value
                        })
            
            # Get performance metrics
            if self.performance_analyzer:
                performance_analysis = await self.performance_analyzer.analyze_performance(
                    AnalysisType.DAILY, last_24h, now
                )
                
                summary['key_metrics']['performance'] = {
                    'overall_score': performance_analysis.overall_score,
                    'status': performance_analysis.status.value,
                    'trend': performance_analysis.trend.value
                }
        
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {str(e)}")
            summary['error'] = str(e)
        
        return summary
    
    async def get_operational_metrics(self) -> Dict[str, Any]:
        """Get operational dashboard metrics"""
        now = datetime.now(timezone.utc)
        last_hour = now - timedelta(hours=1)
        
        metrics = {
            'timestamp': now.isoformat(),
            'real_time_metrics': {},
            'hourly_trends': {},
            'system_health': {},
            'active_issues': []
        }
        
        try:
            # Real-time performance metrics
            if self.performance_analyzer:
                dashboard_data = await self.performance_analyzer.get_real_time_dashboard()
                metrics['real_time_metrics'] = dashboard_data
            
            # System health checks
            health_checks = []
            if self.transmission_reporter:
                health_checks.append(await self.transmission_reporter.health_check())
            if self.compliance_monitor:
                health_checks.append(await self.compliance_monitor.health_check())
            if self.performance_analyzer:
                health_checks.append(await self.performance_analyzer.health_check())
            
            metrics['system_health'] = {
                'services': health_checks,
                'overall_status': 'healthy' if all(h.get('status') == 'healthy' for h in health_checks) else 'degraded'
            }
            
        except Exception as e:
            self.logger.error(f"Error generating operational metrics: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics
    
    async def get_compliance_dashboard(self) -> Dict[str, Any]:
        """Get compliance-focused dashboard data"""
        now = datetime.now(timezone.utc)
        last_week = now - timedelta(days=7)
        
        dashboard = {
            'timestamp': now.isoformat(),
            'compliance_overview': {},
            'category_breakdown': {},
            'violation_trends': {},
            'regulatory_requirements': {}
        }
        
        try:
            if self.compliance_monitor:
                # Get compliance report
                compliance_report = await self.compliance_monitor.check_compliance(last_week, now)
                
                dashboard['compliance_overview'] = {
                    'overall_score': compliance_report.overall_score,
                    'status': compliance_report.overall_status.value,
                    'total_violations': len(compliance_report.violations),
                    'critical_violations': len([v for v in compliance_report.violations if v.severity.value == 'critical'])
                }
                
                # Category breakdown
                category_stats = defaultdict(lambda: {'total': 0, 'violations': 0})
                for metric in compliance_report.metrics:
                    category_stats[metric.category.value]['total'] += 1
                    if metric.status != ComplianceStatus.COMPLIANT:
                        category_stats[metric.category.value]['violations'] += 1
                
                dashboard['category_breakdown'] = dict(category_stats)
                
                # Get trends
                trends = await self.compliance_monitor.get_compliance_trends(7)
                dashboard['violation_trends'] = trends
                
                # Regulatory requirements summary
                dashboard['regulatory_requirements'] = {
                    'firs_compliance': {
                        'transmission_rate': 'Must maintain >95% success rate',
                        'response_time': 'Must respond within 5 seconds',
                        'audit_retention': 'Must retain audit logs for 365 days',
                        'certificate_management': 'Must renew certificates before expiry'
                    }
                }
        
        except Exception as e:
            self.logger.error(f"Error generating compliance dashboard: {str(e)}")
            dashboard['error'] = str(e)
        
        return dashboard
    
    async def get_technical_metrics(self) -> Dict[str, Any]:
        """Get technical dashboard metrics"""
        now = datetime.now(timezone.utc)
        last_day = now - timedelta(days=1)
        
        metrics = {
            'timestamp': now.isoformat(),
            'system_performance': {},
            'transmission_details': {},
            'error_analysis': {},
            'capacity_planning': {}
        }
        
        try:
            # Performance analysis
            if self.performance_analyzer:
                performance_analysis = await self.performance_analyzer.analyze_performance(
                    AnalysisType.DAILY, last_day, now
                )
                
                metrics['system_performance'] = {
                    'overall_score': performance_analysis.overall_score,
                    'status': performance_analysis.status.value,
                    'insights': [insight.to_dict() for insight in performance_analysis.insights],
                    'recommendations': performance_analysis.recommendations
                }
                
                # Get performance trends
                trends = await self.performance_analyzer.get_performance_trends(7)
                metrics['capacity_planning'] = {
                    'trends': trends,
                    'recommendations': [
                        'Monitor response time trends for capacity planning',
                        'Plan scaling based on throughput patterns',
                        'Implement predictive alerting for resource usage'
                    ]
                }
            
            # Transmission details
            if self.transmission_reporter:
                transmission_trends = await self.transmission_reporter.get_transmission_trends(7)
                metrics['transmission_details'] = transmission_trends
        
        except Exception as e:
            self.logger.error(f"Error generating technical metrics: {str(e)}")
            metrics['error'] = str(e)
        
        return metrics


class RegulatoryDashboard:
    """
    Comprehensive regulatory compliance dashboard
    Provides real-time monitoring and reporting for FIRS compliance
    """
    
    def __init__(self,
                 transmission_reporter: Optional[TransmissionReportGenerator] = None,
                 compliance_monitor: Optional[ComplianceMetricsMonitor] = None,
                 performance_analyzer: Optional[PerformanceAnalyzer] = None):
        self.data_aggregator = DashboardDataAggregator(
            transmission_reporter, compliance_monitor, performance_analyzer
        )
        self.logger = logging.getLogger(__name__)
        
        # Dashboard configurations
        self.dashboard_configs = self._initialize_dashboard_configs()
        
        # Alert management
        self.active_alerts: Dict[str, RegulatoryAlert] = {}
        self.alert_history: List[RegulatoryAlert] = []
        
        # Dashboard statistics
        self.stats = {
            'dashboards_generated': 0,
            'alerts_triggered': 0,
            'alerts_resolved': 0,
            'last_update': None,
            'active_sessions': 0
        }
    
    def _initialize_dashboard_configs(self) -> Dict[DashboardType, List[DashboardWidget]]:
        """Initialize default dashboard configurations"""
        configs = {}
        
        # Executive Dashboard
        configs[DashboardType.EXECUTIVE] = [
            DashboardWidget(
                widget_id="exec_overview",
                title="Regulatory Compliance Overview",
                type="metric_cards",
                data_source="compliance_summary",
                refresh_interval=300,
                position={"x": 0, "y": 0, "width": 12, "height": 4},
                config={"metrics": ["overall_score", "success_rate", "violations_count"]}
            ),
            DashboardWidget(
                widget_id="exec_alerts",
                title="Critical Alerts",
                type="alert_list",
                data_source="active_alerts",
                refresh_interval=60,
                position={"x": 0, "y": 4, "width": 6, "height": 4},
                config={"severity_filter": ["critical", "high"]}
            ),
            DashboardWidget(
                widget_id="exec_trends",
                title="Compliance Trends",
                type="trend_chart",
                data_source="compliance_trends",
                refresh_interval=900,
                position={"x": 6, "y": 4, "width": 6, "height": 4},
                config={"period": "7_days"}
            )
        ]
        
        # Operational Dashboard
        configs[DashboardType.OPERATIONAL] = [
            DashboardWidget(
                widget_id="ops_realtime",
                title="Real-time Metrics",
                type="realtime_metrics",
                data_source="performance_realtime",
                refresh_interval=30,
                position={"x": 0, "y": 0, "width": 8, "height": 3},
                config={"metrics": ["response_time", "throughput", "error_rate"]}
            ),
            DashboardWidget(
                widget_id="ops_transmission",
                title="Transmission Status",
                type="status_chart",
                data_source="transmission_status",
                refresh_interval=120,
                position={"x": 8, "y": 0, "width": 4, "height": 3},
                config={"chart_type": "donut"}
            ),
            DashboardWidget(
                widget_id="ops_system_health",
                title="System Health",
                type="health_indicators",
                data_source="system_health",
                refresh_interval=60,
                position={"x": 0, "y": 3, "width": 12, "height": 2},
                config={"services": ["transmission", "compliance", "performance"]}
            )
        ]
        
        # Compliance Dashboard
        configs[DashboardType.COMPLIANCE] = [
            DashboardWidget(
                widget_id="comp_score",
                title="Compliance Score",
                type="gauge_chart",
                data_source="compliance_score",
                refresh_interval=300,
                position={"x": 0, "y": 0, "width": 4, "height": 3},
                config={"min": 0, "max": 100, "thresholds": [60, 80, 95]}
            ),
            DashboardWidget(
                widget_id="comp_categories",
                title="Compliance by Category",
                type="category_breakdown",
                data_source="compliance_categories",
                refresh_interval=300,
                position={"x": 4, "y": 0, "width": 8, "height": 3},
                config={"chart_type": "horizontal_bar"}
            ),
            DashboardWidget(
                widget_id="comp_violations",
                title="Violations Overview",
                type="violation_table",
                data_source="violations_list",
                refresh_interval=120,
                position={"x": 0, "y": 3, "width": 12, "height": 4},
                config={"show_resolved": False}
            )
        ]
        
        return configs
    
    async def generate_dashboard(self, dashboard_type: DashboardType) -> DashboardData:
        """
        Generate complete dashboard for specified type
        
        Args:
            dashboard_type: Type of dashboard to generate
            
        Returns:
            Complete dashboard data structure
        """
        start_time = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Generating {dashboard_type.value} dashboard")
            
            # Get appropriate data based on dashboard type
            if dashboard_type == DashboardType.EXECUTIVE:
                summary_data = await self.data_aggregator.get_executive_summary()
            elif dashboard_type == DashboardType.OPERATIONAL:
                summary_data = await self.data_aggregator.get_operational_metrics()
            elif dashboard_type == DashboardType.COMPLIANCE:
                summary_data = await self.data_aggregator.get_compliance_dashboard()
            elif dashboard_type == DashboardType.TECHNICAL:
                summary_data = await self.data_aggregator.get_technical_metrics()
            else:
                summary_data = await self.data_aggregator.get_executive_summary()
            
            # Calculate overall regulatory status
            overall_status = self._calculate_regulatory_status(summary_data)
            
            # Get compliance and performance scores
            compliance_score = summary_data.get('key_metrics', {}).get('compliance', {}).get('overall_score', 0)
            performance_score = summary_data.get('key_metrics', {}).get('performance', {}).get('overall_score', 0)
            
            # Process alerts
            alerts = self._process_alerts(summary_data)
            
            # Get widget configurations
            widgets = self.dashboard_configs.get(dashboard_type, [])
            
            # Generate recommendations
            recommendations = self._generate_dashboard_recommendations(summary_data, alerts)
            
            # Create dashboard data
            dashboard_data = DashboardData(
                dashboard_id=f"{dashboard_type.value}_{int(start_time.timestamp())}",
                dashboard_type=dashboard_type,
                generated_at=start_time,
                overall_status=overall_status,
                summary_metrics=summary_data,
                compliance_score=compliance_score,
                performance_score=performance_score,
                alerts=alerts,
                widgets=widgets,
                recommendations=recommendations,
                last_updated=start_time
            )
            
            # Update statistics
            self.stats['dashboards_generated'] += 1
            self.stats['last_update'] = start_time.isoformat()
            
            generation_time = (datetime.now(timezone.utc) - start_time).total_seconds()
            self.logger.info(
                f"Dashboard generated successfully: {dashboard_type.value} "
                f"in {generation_time:.2f}s, {len(alerts)} alerts"
            )
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating {dashboard_type.value} dashboard: {str(e)}")
            raise
    
    def _calculate_regulatory_status(self, summary_data: Dict[str, Any]) -> RegulatoryStatus:
        """Calculate overall regulatory status"""
        try:
            # Check for critical issues
            alerts = summary_data.get('alerts', [])
            critical_alerts = [a for a in alerts if a.get('severity') == 'critical']
            
            if critical_alerts:
                return RegulatoryStatus.NON_COMPLIANT
            
            # Check compliance score
            compliance_metrics = summary_data.get('key_metrics', {}).get('compliance', {})
            compliance_score = compliance_metrics.get('overall_score', 0)
            
            if compliance_score >= 95:
                return RegulatoryStatus.COMPLIANT
            elif compliance_score >= 80:
                return RegulatoryStatus.AT_RISK
            else:
                return RegulatoryStatus.NON_COMPLIANT
                
        except Exception as e:
            self.logger.warning(f"Error calculating regulatory status: {str(e)}")
            return RegulatoryStatus.UNDER_REVIEW
    
    def _process_alerts(self, summary_data: Dict[str, Any]) -> List[RegulatoryAlert]:
        """Process and convert alerts from summary data"""
        alerts = []
        
        # Process alerts from summary data
        raw_alerts = summary_data.get('alerts', [])
        
        for alert_data in raw_alerts:
            alert = RegulatoryAlert(
                alert_id=alert_data.get('id', f"alert_{len(alerts)}"),
                title=alert_data.get('title', 'Unknown Alert'),
                description=alert_data.get('description', ''),
                severity=AlertSeverity(alert_data.get('severity', 'medium')),
                category=alert_data.get('category', 'general'),
                triggered_at=datetime.now(timezone.utc),
                current_value=alert_data.get('current_value'),
                threshold_value=alert_data.get('threshold_value'),
                remediation_steps=alert_data.get('remediation_steps', [])
            )
            
            alerts.append(alert)
            
            # Track in active alerts
            self.active_alerts[alert.alert_id] = alert
        
        # Add system health alerts
        system_health = summary_data.get('system_health', {})
        if system_health.get('overall_status') == 'degraded':
            alert = RegulatoryAlert(
                alert_id=f"system_health_{int(datetime.now(timezone.utc).timestamp())}",
                title="System Health Degraded",
                description="One or more system components are not functioning optimally",
                severity=AlertSeverity.MEDIUM,
                category="system",
                triggered_at=datetime.now(timezone.utc),
                remediation_steps=[
                    "Check individual service health",
                    "Review system logs",
                    "Monitor resource utilization"
                ]
            )
            alerts.append(alert)
        
        return alerts
    
    def _generate_dashboard_recommendations(self, 
                                         summary_data: Dict[str, Any], 
                                         alerts: List[RegulatoryAlert]) -> List[str]:
        """Generate recommendations based on dashboard data"""
        recommendations = []
        
        # Critical alert recommendations
        critical_alerts = [a for a in alerts if a.severity == AlertSeverity.CRITICAL]
        if critical_alerts:
            recommendations.append("Immediately address critical compliance alerts to ensure regulatory compliance")
        
        # Compliance score recommendations
        compliance_score = summary_data.get('key_metrics', {}).get('compliance', {}).get('overall_score', 0)
        if compliance_score < 80:
            recommendations.extend([
                "Implement immediate compliance improvement measures",
                "Review and update compliance policies and procedures",
                "Conduct comprehensive compliance audit"
            ])
        elif compliance_score < 95:
            recommendations.extend([
                "Focus on areas with compliance gaps",
                "Implement preventive compliance measures",
                "Enhance monitoring and alerting"
            ])
        
        # Performance recommendations
        performance_score = summary_data.get('key_metrics', {}).get('performance', {}).get('overall_score', 0)
        if performance_score < 70:
            recommendations.extend([
                "Investigate performance bottlenecks",
                "Optimize system resources and configuration",
                "Implement performance monitoring improvements"
            ])
        
        # Transmission recommendations
        transmission_metrics = summary_data.get('key_metrics', {}).get('transmission', {})
        success_rate = transmission_metrics.get('success_rate', 0)
        if success_rate < 95:
            recommendations.extend([
                "Improve transmission reliability",
                "Implement robust error handling and retry mechanisms",
                "Monitor and optimize network connectivity"
            ])
        
        # General recommendations
        if not recommendations:
            recommendations.extend([
                "Maintain current compliance practices",
                "Continue regular monitoring and reporting",
                "Plan for future regulatory changes"
            ])
        
        return recommendations
    
    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary of all dashboard types"""
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'available_dashboards': [],
            'overall_status': RegulatoryStatus.COMPLIANT.value,
            'active_alerts': len(self.active_alerts),
            'stats': self.stats.copy()
        }
        
        # Get status for each dashboard type
        for dashboard_type in DashboardType:
            try:
                dashboard_data = await self.generate_dashboard(dashboard_type)
                summary['available_dashboards'].append({
                    'type': dashboard_type.value,
                    'status': dashboard_data.overall_status.value,
                    'compliance_score': dashboard_data.compliance_score,
                    'performance_score': dashboard_data.performance_score,
                    'alerts_count': len(dashboard_data.alerts),
                    'last_updated': dashboard_data.last_updated.isoformat()
                })
                
                # Update overall status (use worst status)
                if dashboard_data.overall_status == RegulatoryStatus.NON_COMPLIANT:
                    summary['overall_status'] = RegulatoryStatus.NON_COMPLIANT.value
                elif (dashboard_data.overall_status == RegulatoryStatus.AT_RISK and 
                      summary['overall_status'] != RegulatoryStatus.NON_COMPLIANT.value):
                    summary['overall_status'] = RegulatoryStatus.AT_RISK.value
                    
            except Exception as e:
                self.logger.error(f"Error getting summary for {dashboard_type.value}: {str(e)}")
                summary['available_dashboards'].append({
                    'type': dashboard_type.value,
                    'status': 'error',
                    'error': str(e)
                })
        
        return summary
    
    async def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Mark an alert as resolved"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts.pop(alert_id)
            alert.resolved = True
            alert.resolved_at = datetime.now(timezone.utc)
            
            self.alert_history.append(alert)
            self.stats['alerts_resolved'] += 1
            
            self.logger.info(f"Alert {alert_id} resolved: {resolution_notes}")
            return True
        
        return False
    
    async def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts"""
        active_alerts = list(self.active_alerts.values())
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'active_alerts': len(active_alerts),
            'alerts_by_severity': Counter(alert.severity.value for alert in active_alerts),
            'alerts_by_category': Counter(alert.category for alert in active_alerts),
            'recent_alerts': [alert.to_dict() for alert in sorted(
                active_alerts, key=lambda a: a.triggered_at, reverse=True
            )[:10]],
            'resolved_alerts_count': len(self.alert_history),
            'stats': self.stats.copy()
        }
    
    def add_custom_widget(self, dashboard_type: DashboardType, widget: DashboardWidget):
        """Add custom widget to dashboard"""
        if dashboard_type not in self.dashboard_configs:
            self.dashboard_configs[dashboard_type] = []
        
        self.dashboard_configs[dashboard_type].append(widget)
        self.logger.info(f"Added custom widget {widget.widget_id} to {dashboard_type.value} dashboard")
    
    def remove_widget(self, dashboard_type: DashboardType, widget_id: str) -> bool:
        """Remove widget from dashboard"""
        if dashboard_type in self.dashboard_configs:
            widgets = self.dashboard_configs[dashboard_type]
            self.dashboard_configs[dashboard_type] = [
                w for w in widgets if w.widget_id != widget_id
            ]
            self.logger.info(f"Removed widget {widget_id} from {dashboard_type.value} dashboard")
            return True
        
        return False
    
    async def export_dashboard_data(self, 
                                  dashboard_type: DashboardType,
                                  format: str = "json") -> Union[str, Dict[str, Any]]:
        """Export dashboard data in specified format"""
        dashboard_data = await self.generate_dashboard(dashboard_type)
        
        if format.lower() == "json":
            return dashboard_data.to_dict()
        elif format.lower() == "csv":
            # Convert to CSV format (simplified)
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write summary
            writer.writerow(["Dashboard Type", dashboard_type.value])
            writer.writerow(["Generated At", dashboard_data.generated_at.isoformat()])
            writer.writerow(["Overall Status", dashboard_data.overall_status.value])
            writer.writerow(["Compliance Score", dashboard_data.compliance_score])
            writer.writerow(["Performance Score", dashboard_data.performance_score])
            writer.writerow([""])
            
            # Write alerts
            writer.writerow(["Alerts"])
            writer.writerow(["ID", "Title", "Severity", "Category", "Triggered At"])
            for alert in dashboard_data.alerts:
                writer.writerow([
                    alert.alert_id, alert.title, alert.severity.value,
                    alert.category, alert.triggered_at.isoformat()
                ])
            
            return output.getvalue()
        else:
            return dashboard_data.to_dict()
    
    async def health_check(self) -> Dict[str, Any]:
        """Get regulatory dashboard health status"""
        active_alerts_count = len(self.active_alerts)
        critical_alerts = len([
            a for a in self.active_alerts.values() 
            if a.severity == AlertSeverity.CRITICAL
        ])
        
        status = "healthy"
        if critical_alerts > 0:
            status = "critical"
        elif active_alerts_count > 20:
            status = "degraded"
        
        return {
            'status': status,
            'service': 'regulatory_dashboard',
            'active_alerts': active_alerts_count,
            'critical_alerts': critical_alerts,
            'dashboard_types': len(self.dashboard_configs),
            'stats': self.stats.copy(),
            'supported_dashboards': [dt.value for dt in DashboardType],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def cleanup(self):
        """Cleanup dashboard resources"""
        self.logger.info("Regulatory dashboard cleanup initiated")
        
        # Log final statistics
        self.logger.info(f"Final dashboard statistics: {self.stats}")
        
        # Clear active alerts
        self.active_alerts.clear()
        
        self.logger.info("Regulatory dashboard cleanup completed")


# Factory functions
def create_regulatory_dashboard() -> RegulatoryDashboard:
    """Create regulatory dashboard with standard configuration"""
    return RegulatoryDashboard()


def create_custom_widget(widget_id: str,
                        title: str,
                        widget_type: str,
                        data_source: str,
                        position: Dict[str, int],
                        **config) -> DashboardWidget:
    """Create custom dashboard widget"""
    return DashboardWidget(
        widget_id=widget_id,
        title=title,
        type=widget_type,
        data_source=data_source,
        refresh_interval=config.get('refresh_interval', 300),
        position=position,
        config=config
    )


def get_dashboard_templates() -> Dict[str, Dict[str, Any]]:
    """Get predefined dashboard templates"""
    return {
        'executive': {
            'title': 'Executive Compliance Dashboard',
            'description': 'High-level compliance overview for executives',
            'widgets': ['overview_metrics', 'critical_alerts', 'compliance_trends'],
            'refresh_interval': 300
        },
        'operational': {
            'title': 'Operational Monitoring Dashboard',
            'description': 'Real-time operational metrics and system health',
            'widgets': ['realtime_metrics', 'transmission_status', 'system_health'],
            'refresh_interval': 60
        },
        'compliance': {
            'title': 'Regulatory Compliance Dashboard',
            'description': 'Detailed compliance metrics and violations',
            'widgets': ['compliance_score', 'category_breakdown', 'violations_table'],
            'refresh_interval': 300
        },
        'technical': {
            'title': 'Technical Performance Dashboard',
            'description': 'Technical metrics and system performance',
            'widgets': ['performance_metrics', 'error_analysis', 'capacity_planning'],
            'refresh_interval': 120
        }
    }