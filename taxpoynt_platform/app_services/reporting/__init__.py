"""
TaxPoynt Platform - APP Services: Reporting
Comprehensive reporting and analytics suite for APP regulatory compliance
"""

from .transmission_reports import (
    TransmissionReportGenerator,
    TransmissionRecord,
    TransmissionSummary,
    ReportConfig,
    ReportFormat,
    ReportPeriod,
    TransmissionStatus,
    TransmissionDataProvider,
    create_transmission_report_generator,
    create_report_config
)

from .compliance_metrics import (
    ComplianceMetricsMonitor,
    ComplianceRule,
    ComplianceViolation,
    ComplianceMetric,
    ComplianceReport,
    ComplianceStatus,
    ComplianceCategory,
    AlertLevel,
    ComplianceDataProvider,
    FIRSComplianceRules,
    create_compliance_monitor,
    create_custom_rule
)

from .performance_analytics import (
    PerformanceAnalyzer,
    PerformanceMetric,
    PerformanceThreshold,
    PerformanceInsight,
    PerformanceAlert,
    PerformanceAnalysis,
    PerformanceMetricType,
    PerformanceStatus,
    TrendDirection,
    AnalysisType,
    PerformanceDataProvider,
    PerformanceThresholdManager,
    create_performance_analyzer,
    create_custom_threshold
)

from .regulatory_dashboard import (
    RegulatoryDashboard,
    DashboardWidget,
    RegulatoryAlert,
    DashboardData,
    DashboardType,
    AlertSeverity,
    RegulatoryStatus,
    DashboardDataAggregator,
    create_regulatory_dashboard,
    create_custom_widget,
    get_dashboard_templates
)

__version__ = "1.0.0"

__all__ = [
    # Transmission Reports
    "TransmissionReportGenerator",
    "TransmissionRecord",
    "TransmissionSummary",
    "ReportConfig",
    "ReportFormat",
    "ReportPeriod",
    "TransmissionStatus",
    "TransmissionDataProvider",
    "create_transmission_report_generator",
    "create_report_config",
    
    # Compliance Metrics
    "ComplianceMetricsMonitor",
    "ComplianceRule",
    "ComplianceViolation",
    "ComplianceMetric",
    "ComplianceReport",
    "ComplianceStatus",
    "ComplianceCategory",
    "AlertLevel",
    "ComplianceDataProvider",
    "FIRSComplianceRules",
    "create_compliance_monitor",
    "create_custom_rule",
    
    # Performance Analytics
    "PerformanceAnalyzer",
    "PerformanceMetric",
    "PerformanceThreshold",
    "PerformanceInsight",
    "PerformanceAlert",
    "PerformanceAnalysis",
    "PerformanceMetricType",
    "PerformanceStatus",
    "TrendDirection",
    "AnalysisType",
    "PerformanceDataProvider",
    "PerformanceThresholdManager",
    "create_performance_analyzer",
    "create_custom_threshold",
    
    # Regulatory Dashboard
    "RegulatoryDashboard",
    "DashboardWidget",
    "RegulatoryAlert",
    "DashboardData",
    "DashboardType",
    "AlertSeverity",
    "RegulatoryStatus",
    "DashboardDataAggregator",
    "create_regulatory_dashboard",
    "create_custom_widget",
    "get_dashboard_templates"
]


class ReportingServiceManager:
    """
    Comprehensive reporting service manager that coordinates all reporting services
    Provides unified interface for regulatory compliance reporting and analytics
    """
    
    def __init__(self):
        """Initialize reporting service manager with all components"""
        # Initialize core services
        self.transmission_reporter = create_transmission_report_generator()
        self.compliance_monitor = create_compliance_monitor()
        self.performance_analyzer = create_performance_analyzer()
        self.regulatory_dashboard = create_regulatory_dashboard()
        
        # Configure dashboard with data sources
        self.regulatory_dashboard.data_aggregator = DashboardDataAggregator(
            self.transmission_reporter,
            self.compliance_monitor,
            self.performance_analyzer
        )
        
        # Service state
        self.is_initialized = False
        self.logger = __import__('logging').getLogger(__name__)
    
    async def initialize_services(self):
        """Initialize all reporting services"""
        if self.is_initialized:
            return
        
        try:
            # Initialize any async components if needed
            self.logger.info("Initializing reporting services")
            
            # Services are primarily synchronous, but we can add async initialization here
            self.is_initialized = True
            
            self.logger.info("Reporting services initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing reporting services: {str(e)}")
            raise
    
    async def generate_comprehensive_report(self, 
                                          start_date: __import__('datetime').datetime,
                                          end_date: __import__('datetime').datetime,
                                          report_format: ReportFormat = ReportFormat.JSON) -> dict:
        """
        Generate comprehensive report combining all reporting services
        
        Args:
            start_date: Start date for report period
            end_date: End date for report period
            report_format: Format for the report
            
        Returns:
            Comprehensive report data
        """
        try:
            self.logger.info(f"Generating comprehensive report from {start_date} to {end_date}")
            
            # Generate transmission report
            transmission_config = create_report_config(
                start_date=start_date,
                end_date=end_date,
                format=report_format,
                include_details=True,
                include_charts=True
            )
            transmission_report = await self.transmission_reporter.generate_report(transmission_config)
            
            # Generate compliance report
            compliance_report = await self.compliance_monitor.check_compliance(start_date, end_date)
            
            # Generate performance analysis
            performance_analysis = await self.performance_analyzer.analyze_performance(
                AnalysisType.CUSTOM,
                start_date,
                end_date
            )
            
            # Generate executive dashboard
            executive_dashboard = await self.regulatory_dashboard.generate_dashboard(
                DashboardType.EXECUTIVE
            )
            
            # Combine all reports
            comprehensive_report = {
                'report_id': f"COMPREHENSIVE_{int(start_date.timestamp())}_{int(end_date.timestamp())}",
                'generated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'transmission_report': transmission_report,
                'compliance_report': compliance_report.to_dict(),
                'performance_analysis': performance_analysis.to_dict(),
                'executive_dashboard': executive_dashboard.to_dict(),
                'summary': {
                    'overall_status': executive_dashboard.overall_status.value,
                    'compliance_score': executive_dashboard.compliance_score,
                    'performance_score': executive_dashboard.performance_score,
                    'total_alerts': len(executive_dashboard.alerts),
                    'critical_alerts': len([a for a in executive_dashboard.alerts if a.severity == AlertSeverity.CRITICAL])
                }
            }
            
            self.logger.info("Comprehensive report generated successfully")
            return comprehensive_report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {str(e)}")
            raise
    
    async def get_real_time_dashboard(self) -> dict:
        """Get real-time dashboard data for immediate monitoring"""
        try:
            # Get operational dashboard (real-time focused)
            operational_dashboard = await self.regulatory_dashboard.generate_dashboard(
                DashboardType.OPERATIONAL
            )
            
            # Get real-time performance metrics
            performance_dashboard = await self.performance_analyzer.get_real_time_dashboard()
            
            # Get alert summary
            alert_summary = await self.regulatory_dashboard.get_alert_summary()
            
            return {
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'operational_dashboard': operational_dashboard.to_dict(),
                'performance_metrics': performance_dashboard,
                'alert_summary': alert_summary,
                'system_status': {
                    'overall_status': operational_dashboard.overall_status.value,
                    'active_alerts': len(operational_dashboard.alerts),
                    'compliance_score': operational_dashboard.compliance_score,
                    'performance_score': operational_dashboard.performance_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting real-time dashboard: {str(e)}")
            raise
    
    async def get_compliance_overview(self) -> dict:
        """Get comprehensive compliance overview"""
        try:
            # Get compliance dashboard
            compliance_dashboard = await self.regulatory_dashboard.generate_dashboard(
                DashboardType.COMPLIANCE
            )
            
            # Get recent compliance trends
            compliance_trends = await self.compliance_monitor.get_compliance_trends(30)
            
            # Get current compliance status
            now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            last_24h = now - __import__('datetime').timedelta(hours=24)
            current_compliance = await self.compliance_monitor.check_compliance(last_24h, now)
            
            return {
                'timestamp': now.isoformat(),
                'compliance_dashboard': compliance_dashboard.to_dict(),
                'compliance_trends': compliance_trends,
                'current_status': current_compliance.to_dict(),
                'summary': {
                    'overall_score': current_compliance.overall_score,
                    'status': current_compliance.overall_status.value,
                    'violations': len(current_compliance.violations),
                    'metrics_analyzed': len(current_compliance.metrics)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting compliance overview: {str(e)}")
            raise
    
    async def get_performance_insights(self) -> dict:
        """Get performance insights and recommendations"""
        try:
            # Get performance analysis for last 24 hours
            now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            last_24h = now - __import__('datetime').timedelta(hours=24)
            
            performance_analysis = await self.performance_analyzer.analyze_performance(
                AnalysisType.DAILY,
                last_24h,
                now
            )
            
            # Get performance trends
            performance_trends = await self.performance_analyzer.get_performance_trends(7)
            
            return {
                'timestamp': now.isoformat(),
                'performance_analysis': performance_analysis.to_dict(),
                'performance_trends': performance_trends,
                'insights': [insight.to_dict() for insight in performance_analysis.insights],
                'recommendations': performance_analysis.recommendations,
                'summary': {
                    'overall_score': performance_analysis.overall_score,
                    'status': performance_analysis.status.value,
                    'trend': performance_analysis.trend.value,
                    'insights_count': len(performance_analysis.insights)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance insights: {str(e)}")
            raise
    
    async def get_transmission_analytics(self, days: int = 7) -> dict:
        """Get transmission analytics and trends"""
        try:
            # Get transmission trends
            transmission_trends = await self.transmission_reporter.get_transmission_trends(days)
            
            # Generate recent transmission report
            now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc)
            start_date = now - __import__('datetime').timedelta(days=days)
            
            config = create_report_config(
                start_date=start_date,
                end_date=now,
                format=ReportFormat.JSON,
                include_details=False,
                include_charts=True
            )
            
            transmission_report = await self.transmission_reporter.generate_report(config)
            
            return {
                'timestamp': now.isoformat(),
                'period_days': days,
                'transmission_trends': transmission_trends,
                'transmission_report': transmission_report,
                'summary': {
                    'total_transmissions': transmission_report['report_data']['summary']['total_transmissions'],
                    'success_rate': transmission_report['report_data']['summary']['success_rate'],
                    'average_processing_time': transmission_report['report_data']['summary']['average_processing_time']
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting transmission analytics: {str(e)}")
            raise
    
    async def get_service_health(self) -> dict:
        """Get health status of all reporting services"""
        try:
            health_checks = []
            
            # Check each service
            services = [
                ('transmission_reporter', self.transmission_reporter),
                ('compliance_monitor', self.compliance_monitor),
                ('performance_analyzer', self.performance_analyzer),
                ('regulatory_dashboard', self.regulatory_dashboard)
            ]
            
            for service_name, service in services:
                try:
                    health_check = await service.health_check()
                    health_checks.append({
                        'service': service_name,
                        'status': health_check.get('status', 'unknown'),
                        'details': health_check
                    })
                except Exception as e:
                    health_checks.append({
                        'service': service_name,
                        'status': 'error',
                        'error': str(e)
                    })
            
            # Determine overall health
            overall_status = 'healthy'
            if any(check['status'] == 'error' for check in health_checks):
                overall_status = 'error'
            elif any(check['status'] in ['critical', 'degraded'] for check in health_checks):
                overall_status = 'degraded'
            
            return {
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'overall_status': overall_status,
                'is_initialized': self.is_initialized,
                'service_checks': health_checks,
                'summary': {
                    'total_services': len(services),
                    'healthy_services': len([c for c in health_checks if c['status'] == 'healthy']),
                    'error_services': len([c for c in health_checks if c['status'] == 'error'])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting service health: {str(e)}")
            return {
                'timestamp': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    async def cleanup(self):
        """Cleanup all reporting services"""
        self.logger.info("Reporting service manager cleanup initiated")
        
        try:
            # Cleanup individual services
            await self.transmission_reporter.cleanup()
            await self.compliance_monitor.cleanup()
            await self.performance_analyzer.cleanup()
            await self.regulatory_dashboard.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Reporting service manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_reporting_service_manager() -> ReportingServiceManager:
    """
    Create comprehensive reporting service manager with all components
    
    Returns:
        Configured ReportingServiceManager instance
    """
    return ReportingServiceManager()


def get_reporting_capabilities() -> dict:
    """Get overview of available reporting capabilities"""
    return {
        'services': [
            'transmission_reports',
            'compliance_metrics',
            'performance_analytics',
            'regulatory_dashboard'
        ],
        'report_formats': [format.value for format in ReportFormat],
        'dashboard_types': [dt.value for dt in DashboardType],
        'compliance_categories': [cc.value for cc in ComplianceCategory],
        'performance_metrics': [pm.value for pm in PerformanceMetricType],
        'analysis_types': [at.value for at in AnalysisType],
        'features': {
            'real_time_monitoring': True,
            'automated_reporting': True,
            'compliance_tracking': True,
            'performance_analytics': True,
            'dashboard_customization': True,
            'alert_management': True,
            'trend_analysis': True,
            'export_capabilities': True
        }
    }


def get_firs_compliance_requirements() -> dict:
    """Get FIRS compliance requirements and standards"""
    return {
        'transmission_requirements': {
            'success_rate': 'Minimum 95% transmission success rate',
            'response_time': 'Maximum 5 seconds average response time',
            'availability': 'Minimum 99.5% service availability',
            'data_format': 'UBL 2.1 XML format compliance'
        },
        'security_requirements': {
            'signature_validation': 'Digital signature validation for all transmissions',
            'certificate_management': 'Valid certificates with proper renewal',
            'timestamp_compliance': 'Accurate timestamps within 5-minute tolerance',
            'audit_trail': 'Complete audit trail for all operations'
        },
        'compliance_monitoring': {
            'real_time_alerts': 'Immediate alerts for compliance violations',
            'regular_reporting': 'Monthly compliance reports to regulatory body',
            'performance_metrics': 'Continuous performance monitoring',
            'audit_logs': 'Minimum 365 days audit log retention'
        },
        'reporting_standards': {
            'dashboard_updates': 'Real-time dashboard updates',
            'metric_collection': 'Comprehensive metric collection',
            'trend_analysis': 'Historical trend analysis and forecasting',
            'exception_reporting': 'Automated exception and error reporting'
        }
    }