"""
Compliance Reporting Module
===========================
Comprehensive compliance reporting and dashboard system that provides unified reporting
across all regulatory frameworks with audit trails, metrics, and executive dashboards.

This reporting module serves as the presentation and analysis layer that:
- Generates compliance reports for all regulatory frameworks
- Provides executive dashboards with key compliance metrics
- Maintains comprehensive audit trails for compliance activities
- Offers trend analysis and predictive compliance insights
- Supports regulatory submission and certification reporting
- Handles multi-format report exports and real-time alerting

Core Components:
- compliance_reporter.py: Main reporting engine with report generation
- dashboard_generator.py: Executive and operational dashboard generation
- audit_tracker.py: Comprehensive audit logging and trail management
- metrics_calculator.py: Compliance metrics calculation and KPI tracking
- export_handler.py: Multi-format report export capabilities
- alert_system.py: Real-time compliance alerting system
- models.py: Reporting-specific data models and schemas
"""

from .compliance_reporter import ComplianceReporter
from .dashboard_generator import DashboardGenerator
from .audit_tracker import AuditTracker
from .metrics_calculator import MetricsCalculator
from .export_handler import ComplianceReportExporter
from .alert_system import ComplianceAlertSystem
from .models import (
    ComplianceReport, DashboardConfiguration, AuditTrail, ComplianceMetrics,
    ReportFormat, ReportSchedule, ComplianceStatus, RiskLevel
)

__all__ = [
    'ComplianceReporter',
    'DashboardGenerator', 
    'AuditTracker',
    'MetricsCalculator',
    'ComplianceReportExporter',
    'ComplianceAlertSystem',
    'ComplianceReport',
    'DashboardConfiguration',
    'AuditTrail',
    'ComplianceMetrics',
    'ReportFormat',
    'ReportSchedule',
    'ComplianceStatus',
    'RiskLevel'
]