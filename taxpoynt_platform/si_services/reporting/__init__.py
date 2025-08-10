"""
SI Reporting Package

This package provides comprehensive reporting capabilities for System Integrator (SI) services,
including integration status monitoring, data quality assessment, performance metrics tracking,
and regulatory compliance dashboards.

Components:
- integration_reports: Integration status reports and health monitoring
- data_quality_reports: Data quality metrics and assessment reports
- processing_metrics: Performance metrics tracking and analysis
- compliance_dashboard: SI-specific compliance monitoring and dashboards
"""

from .integration_reports import (
    IntegrationReportService,
    IntegrationReport,
    IntegrationStatus,
    ERPConnectionInfo,
    DataFlowMetrics,
    SyncStatusReport,
    IntegrationHealthScore,
    ReportConfig,
    ReportFormat,
    ReportPeriod,
    create_integration_report_service
)

from .data_quality_reports import (
    DataQualityService,
    DataQualityReport,
    DataQualityDimension,
    QualityScore,
    DataIssue,
    DataIssueType,
    FieldQualityMetrics,
    EntityQualityMetrics,
    SystemQualityMetrics,
    DataQualityRule,
    QualityConfig,
    create_data_quality_service
)

from .processing_metrics import (
    ProcessingMetricsService,
    PerformanceReport,
    MetricType,
    MetricUnit,
    ThroughputMetrics,
    LatencyMetrics,
    ErrorMetrics,
    SystemResourceMetrics,
    PerformanceAlert,
    AlertSeverity,
    MetricsConfig,
    create_processing_metrics_service
)

from .compliance_dashboard import (
    ComplianceDashboardService,
    ComplianceDashboard,
    ComplianceStatus,
    ComplianceCategory,
    ViolationSeverity,
    RegulatoryFramework,
    ComplianceRule,
    ComplianceViolation,
    ComplianceMetrics,
    CertificationStatus,
    DataIntegrityCheck,
    AuditEvent,
    DashboardConfig,
    create_compliance_dashboard_service
)

__all__ = [
    # Integration Reports
    "IntegrationReportService",
    "IntegrationReport",
    "IntegrationStatus",
    "ERPConnectionInfo",
    "DataFlowMetrics",
    "SyncStatusReport",
    "IntegrationHealthScore",
    "ReportConfig",
    "ReportFormat",
    "ReportPeriod",
    "create_integration_report_service",
    
    # Data Quality Reports
    "DataQualityService",
    "DataQualityReport",
    "DataQualityDimension",
    "QualityScore",
    "DataIssue",
    "DataIssueType",
    "FieldQualityMetrics",
    "EntityQualityMetrics",
    "SystemQualityMetrics",
    "DataQualityRule",
    "QualityConfig",
    "create_data_quality_service",
    
    # Processing Metrics
    "ProcessingMetricsService",
    "PerformanceReport",
    "MetricType",
    "MetricUnit",
    "ThroughputMetrics",
    "LatencyMetrics",
    "ErrorMetrics",
    "SystemResourceMetrics",
    "PerformanceAlert",
    "AlertSeverity",
    "MetricsConfig",
    "create_processing_metrics_service",
    
    # Compliance Dashboard
    "ComplianceDashboardService",
    "ComplianceDashboard",
    "ComplianceStatus",
    "ComplianceCategory",
    "ViolationSeverity",
    "RegulatoryFramework",
    "ComplianceRule",
    "ComplianceViolation",
    "ComplianceMetrics",
    "CertificationStatus",
    "DataIntegrityCheck",
    "AuditEvent",
    "DashboardConfig",
    "create_compliance_dashboard_service"
]

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Comprehensive reporting and monitoring system for SI services"