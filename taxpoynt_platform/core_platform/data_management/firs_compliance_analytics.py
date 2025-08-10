"""
FIRS Compliance Analytics and Reporting Dashboard

Builds upon existing architecture to provide comprehensive compliance
monitoring, analytics, and reporting for Nigerian tax regulations.

Transfers and enhances patterns from:
- backend/app/services/firs_monitoring.py
- backend/app/services/metrics_service.py
- backend/app/models/nigerian_compliance.py
- backend/app/routes/dashboard.py
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta, date
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum
import json
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func
from sqlalchemy import and_, or_, desc

# Import existing components
from .production_database_manager import ProductionDatabaseManager
from .cache_manager import CacheManager
from ..transaction_processing.universal_transaction_processor import UniversalTransactionProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.paystack.payment_processor import PaystackPaymentProcessor

logger = logging.getLogger(__name__)


class ComplianceStatus(Enum):
    """FIRS compliance status levels."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    NON_COMPLIANT = "non_compliant"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ReportPeriod(Enum):
    """Reporting period options."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class ComplianceMetrics:
    """Comprehensive FIRS compliance metrics."""
    # Transaction compliance
    total_transactions: int = 0
    compliant_transactions: int = 0
    non_compliant_transactions: int = 0
    pending_validation: int = 0
    
    # Invoice generation compliance
    invoices_generated: int = 0
    invoices_transmitted: int = 0
    invoices_acknowledged: int = 0
    invoices_rejected: int = 0
    
    # Timing compliance
    within_sla_submissions: int = 0
    overdue_submissions: int = 0
    avg_submission_time_hours: float = 0.0
    
    # Data quality metrics
    data_completeness_percent: float = 0.0
    validation_success_rate: float = 0.0
    error_rate_percent: float = 0.0
    
    # Penalty and risk metrics
    potential_penalties: float = 0.0
    risk_score: float = 0.0
    audit_readiness_score: float = 0.0
    
    # Coverage metrics
    processor_coverage_percent: float = 0.0
    transaction_coverage_percent: float = 0.0
    
    # Overall compliance status
    compliance_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    compliance_score: float = 0.0
    
    # Metadata
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    generated_at: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_derived_metrics(self):
        """Calculate derived compliance metrics."""
        if self.total_transactions > 0:
            self.data_completeness_percent = (
                self.compliant_transactions / self.total_transactions
            ) * 100
            
            self.validation_success_rate = (
                (self.total_transactions - self.non_compliant_transactions) / 
                self.total_transactions
            ) * 100
            
            self.error_rate_percent = (
                self.non_compliant_transactions / self.total_transactions
            ) * 100
        
        if self.invoices_generated > 0:
            transmission_rate = (self.invoices_transmitted / self.invoices_generated) * 100
            acknowledgment_rate = (self.invoices_acknowledged / self.invoices_transmitted) * 100 if self.invoices_transmitted > 0 else 0
            
            # Calculate overall compliance score
            self.compliance_score = (
                self.validation_success_rate * 0.3 +
                transmission_rate * 0.3 +
                acknowledgment_rate * 0.2 +
                self.data_completeness_percent * 0.2
            )
        
        # Determine compliance status
        if self.compliance_score >= 95:
            self.compliance_status = ComplianceStatus.COMPLIANT
        elif self.compliance_score >= 85:
            self.compliance_status = ComplianceStatus.WARNING
        elif self.compliance_score >= 70:
            self.compliance_status = ComplianceStatus.NON_COMPLIANT
        else:
            self.compliance_status = ComplianceStatus.CRITICAL


@dataclass
class ProcessorComplianceReport:
    """Compliance report for individual payment processor."""
    processor_name: str
    total_transactions: int
    successful_transmissions: int
    failed_transmissions: int
    avg_processing_time_ms: float
    compliance_score: float
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    last_successful_sync: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate transmission success rate."""
        if self.total_transactions == 0:
            return 0.0
        return (self.successful_transmissions / self.total_transactions) * 100


class FIRSComplianceAnalytics:
    """
    FIRS compliance analytics and reporting system.
    
    Provides comprehensive monitoring and reporting for Nigerian tax compliance
    requirements, building upon existing monitoring patterns.
    """
    
    def __init__(
        self,
        db_manager: ProductionDatabaseManager,
        cache_manager: CacheManager,
        universal_processor: UniversalTransactionProcessor
    ):
        """
        Initialize FIRS compliance analytics.
        
        Args:
            db_manager: Production database manager
            cache_manager: Cache manager instance
            universal_processor: Universal transaction processor
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.universal_processor = universal_processor
        
        # Compliance thresholds (configurable)
        self.compliance_thresholds = {
            'min_transmission_rate': 98.0,  # Minimum transmission success rate
            'max_submission_delay_hours': 24,  # Maximum delay for invoice submission  
            'min_data_completeness': 99.5,  # Minimum data completeness percentage
            'max_error_rate': 2.0,  # Maximum error rate percentage
            'min_audit_readiness': 95.0  # Minimum audit readiness score
        }
        
        # Nigerian payment processors for monitoring
        self.monitored_processors = [
            'paystack', 'moniepoint', 'opay', 'palmpay', 'interswitch'
        ]
        
        logger.info("FIRS Compliance Analytics initialized")
    
    async def generate_compliance_report(
        self,
        organization_id: UUID,
        period: ReportPeriod = ReportPeriod.MONTHLY,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> ComplianceMetrics:
        """
        Generate comprehensive FIRS compliance report.
        
        Args:
            organization_id: Organization to generate report for
            period: Reporting period
            start_date: Custom start date (for CUSTOM period)
            end_date: Custom end date (for CUSTOM period)
            
        Returns:
            Comprehensive compliance metrics
        """
        # Determine reporting period
        period_start, period_end = self._get_period_dates(period, start_date, end_date)
        
        logger.info(f"Generating FIRS compliance report for org {organization_id} from {period_start} to {period_end}")
        
        # Check cache first
        cache_key = f"compliance_report:{organization_id}:{period.value}:{period_start.date()}:{period_end.date()}"
        cached_report = self.cache_manager.get(cache_key)
        
        if cached_report:
            logger.debug(f"Returning cached compliance report for {organization_id}")
            return ComplianceMetrics(**cached_report)
        
        # Generate fresh report
        metrics = ComplianceMetrics(
            period_start=period_start,
            period_end=period_end
        )
        
        async with self.db_manager.get_session(tenant_id=organization_id) as session:
            # Transaction compliance metrics
            await self._collect_transaction_metrics(session, organization_id, period_start, period_end, metrics)
            
            # Invoice generation metrics
            await self._collect_invoice_metrics(session, organization_id, period_start, period_end, metrics)
            
            # Timing compliance metrics
            await self._collect_timing_metrics(session, organization_id, period_start, period_end, metrics)
            
            # Data quality metrics
            await self._collect_quality_metrics(session, organization_id, period_start, period_end, metrics)
            
            # Risk and penalty assessment
            await self._assess_risk_and_penalties(session, organization_id, period_start, period_end, metrics)
            
            # Coverage analysis
            await self._analyze_coverage(session, organization_id, period_start, period_end, metrics)
        
        # Calculate derived metrics
        metrics.calculate_derived_metrics()
        
        # Cache the report
        self.cache_manager.set(cache_key, metrics.__dict__, ttl=3600)  # Cache for 1 hour
        
        logger.info(f"Compliance report generated: {metrics.compliance_status.value} with score {metrics.compliance_score:.2f}")
        
        return metrics
    
    async def _collect_transaction_metrics(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Collect transaction-level compliance metrics."""
        transaction_query = text("""
            SELECT 
                COUNT(*) as total_count,
                COUNT(*) FILTER (WHERE upt.status = 'completed' AND upt.compliance_validated = true) as compliant_count,
                COUNT(*) FILTER (WHERE upt.status = 'failed' OR upt.compliance_validated = false) as non_compliant_count,
                COUNT(*) FILTER (WHERE upt.status = 'processing') as pending_count
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(transaction_query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date
        })
        
        row = result.fetchone()
        if row:
            metrics.total_transactions = row.total_count or 0
            metrics.compliant_transactions = row.compliant_count or 0
            metrics.non_compliant_transactions = row.non_compliant_count or 0
            metrics.pending_validation = row.pending_count or 0
    
    async def _collect_invoice_metrics(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Collect invoice generation and transmission metrics."""
        invoice_query = text("""
            SELECT 
                COUNT(*) as generated_count,
                COUNT(*) FILTER (WHERE sr.status IN ('accepted', 'completed')) as transmitted_count,
                COUNT(*) FILTER (WHERE sr.status = 'accepted') as acknowledged_count,
                COUNT(*) FILTER (WHERE sr.status = 'rejected') as rejected_count
            FROM irn_records ir
            LEFT JOIN submission_records sr ON ir.irn = sr.irn
            WHERE ir.organization_id = :org_id
            AND ir.generated_at BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(invoice_query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date
        })
        
        row = result.fetchone()
        if row:
            metrics.invoices_generated = row.generated_count or 0
            metrics.invoices_transmitted = row.transmitted_count or 0
            metrics.invoices_acknowledged = row.acknowledged_count or 0
            metrics.invoices_rejected = row.rejected_count or 0
    
    async def _collect_timing_metrics(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Collect timing compliance metrics."""
        timing_query = text("""
            SELECT 
                COUNT(*) FILTER (
                    WHERE EXTRACT(EPOCH FROM (sr.created_at - ir.generated_at)) / 3600 <= 24
                ) as within_sla_count,
                COUNT(*) FILTER (
                    WHERE EXTRACT(EPOCH FROM (sr.created_at - ir.generated_at)) / 3600 > 24
                ) as overdue_count,
                AVG(EXTRACT(EPOCH FROM (sr.created_at - ir.generated_at)) / 3600) as avg_submission_hours
            FROM irn_records ir
            LEFT JOIN submission_records sr ON ir.irn = sr.irn
            WHERE ir.organization_id = :org_id
            AND ir.generated_at BETWEEN :start_date AND :end_date
            AND sr.created_at IS NOT NULL
        """)
        
        result = await session.execute(timing_query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date
        })
        
        row = result.fetchone()
        if row:
            metrics.within_sla_submissions = row.within_sla_count or 0
            metrics.overdue_submissions = row.overdue_count or 0
            metrics.avg_submission_time_hours = float(row.avg_submission_hours or 0)
    
    async def _collect_quality_metrics(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Collect data quality metrics."""
        quality_query = text("""
            SELECT 
                COUNT(*) as total_validations,
                COUNT(*) FILTER (WHERE vr.is_valid = true) as successful_validations,
                COUNT(*) FILTER (WHERE vr.is_valid = false) as failed_validations
            FROM validation_records vr
            WHERE vr.organization_id = :org_id
            AND vr.created_at BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(quality_query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date
        })
        
        row = result.fetchone()
        if row and row.total_validations > 0:
            success_rate = (row.successful_validations / row.total_validations) * 100
            metrics.validation_success_rate = success_rate
            metrics.error_rate_percent = 100 - success_rate
    
    async def _assess_risk_and_penalties(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Assess compliance risk and potential penalties."""
        # Calculate potential penalties based on non-compliance
        base_penalty_per_transaction = 10000  # ₦10,000 per non-compliant transaction (example)
        
        metrics.potential_penalties = metrics.non_compliant_transactions * base_penalty_per_transaction
        
        # Calculate risk score (0-100)
        risk_factors = [
            (metrics.error_rate_percent / 100) * 30,  # Error rate impact (30%)
            (metrics.overdue_submissions / max(1, metrics.total_transactions)) * 25,  # Timing impact (25%)
            (metrics.invoices_rejected / max(1, metrics.invoices_generated)) * 25,  # Rejection impact (25%)
            (1 - (metrics.validation_success_rate / 100)) * 20  # Validation impact (20%)
        ]
        
        metrics.risk_score = min(100, sum(risk_factors))
        
        # Calculate audit readiness score
        audit_factors = [
            metrics.data_completeness_percent * 0.3,
            metrics.validation_success_rate * 0.3,
            (metrics.within_sla_submissions / max(1, metrics.total_transactions)) * 100 * 0.2,
            (metrics.invoices_acknowledged / max(1, metrics.invoices_generated)) * 100 * 0.2
        ]
        
        metrics.audit_readiness_score = sum(audit_factors)
    
    async def _analyze_coverage(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ComplianceMetrics
    ):
        """Analyze transaction coverage across processors."""
        coverage_query = text("""
            SELECT 
                upt.connector_type,
                COUNT(*) as transaction_count
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            GROUP BY upt.connector_type
        """)
        
        result = await session.execute(coverage_query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date
        })
        
        processor_counts = {row.connector_type: row.transaction_count for row in result}
        
        # Calculate processor coverage
        active_processors = len(processor_counts)
        expected_processors = len(self.monitored_processors)
        
        metrics.processor_coverage_percent = (active_processors / expected_processors) * 100
        
        # Transaction coverage is assumed to be 100% if we have any transactions
        metrics.transaction_coverage_percent = 100.0 if metrics.total_transactions > 0 else 0.0
    
    async def generate_processor_reports(
        self,
        organization_id: UUID,
        period: ReportPeriod = ReportPeriod.MONTHLY
    ) -> List[ProcessorComplianceReport]:
        """
        Generate compliance reports for individual payment processors.
        
        Args:
            organization_id: Organization ID
            period: Reporting period
            
        Returns:
            List of processor compliance reports
        """
        period_start, period_end = self._get_period_dates(period)
        reports = []
        
        async with self.db_manager.get_session(tenant_id=organization_id) as session:
            for processor_name in self.monitored_processors:
                report = await self._generate_single_processor_report(
                    session, organization_id, processor_name, period_start, period_end
                )
                reports.append(report)
        
        return reports
    
    async def _generate_single_processor_report(
        self,
        session: Session,
        organization_id: UUID,
        processor_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> ProcessorComplianceReport:
        """Generate compliance report for a single processor."""
        processor_query = text("""
            SELECT 
                COUNT(*) as total_transactions,
                COUNT(*) FILTER (WHERE upt.status = 'completed') as successful_count,
                COUNT(*) FILTER (WHERE upt.status = 'failed') as failed_count,
                AVG(upt.processing_time_ms) as avg_processing_time,
                MAX(upt.transaction_timestamp) as last_sync
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.connector_type = :processor_type
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
        """)
        
        result = await session.execute(processor_query, {
            'org_id': str(organization_id),
            'processor_type': processor_name,
            'start_date': start_date,
            'end_date': end_date
        })
        
        row = result.fetchone()
        
        if row:
            total_transactions = row.total_transactions or 0
            successful_transmissions = row.successful_count or 0
            failed_transmissions = row.failed_count or 0
            avg_processing_time = float(row.avg_processing_time or 0)
            last_sync = row.last_sync
            
            # Calculate compliance score for this processor
            compliance_score = 0.0
            if total_transactions > 0:
                success_rate = (successful_transmissions / total_transactions) * 100
                compliance_score = min(100, success_rate)
            
            # Identify issues
            issues = []
            recommendations = []
            
            if success_rate < 95:
                issues.append({
                    "type": "low_success_rate",
                    "severity": "high" if success_rate < 90 else "medium",
                    "value": success_rate,
                    "description": f"Success rate of {success_rate:.1f}% is below threshold"
                })
                recommendations.append("Review processor integration and error handling")
            
            if avg_processing_time > 5000:  # 5 seconds
                issues.append({
                    "type": "slow_processing",
                    "severity": "medium",
                    "value": avg_processing_time,
                    "description": f"Average processing time of {avg_processing_time:.0f}ms is high"
                })
                recommendations.append("Optimize processor integration for better performance")
        
        else:
            # No data for this processor
            total_transactions = 0
            successful_transmissions = 0
            failed_transmissions = 0
            avg_processing_time = 0.0
            compliance_score = 0.0
            last_sync = None
            
            issues = [{
                "type": "no_data",
                "severity": "critical",
                "description": f"No transaction data found for {processor_name}"
            }]
            recommendations = [
                f"Verify {processor_name} integration is properly configured",
                "Check processor connectivity and authentication"
            ]
        
        return ProcessorComplianceReport(
            processor_name=processor_name,
            total_transactions=total_transactions,
            successful_transmissions=successful_transmissions,
            failed_transmissions=failed_transmissions,
            avg_processing_time_ms=avg_processing_time,
            compliance_score=compliance_score,
            issues=issues,
            recommendations=recommendations,
            last_successful_sync=last_sync
        )
    
    def _get_period_dates(
        self,
        period: ReportPeriod,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[datetime, datetime]:
        """Get start and end dates for reporting period."""
        now = datetime.utcnow()
        
        if period == ReportPeriod.CUSTOM:
            if not start_date or not end_date:
                raise ValueError("Custom period requires start_date and end_date")
            return start_date, end_date
        
        elif period == ReportPeriod.DAILY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        
        elif period == ReportPeriod.WEEKLY:
            days_since_monday = now.weekday()
            start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        
        elif period == ReportPeriod.MONTHLY:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=start.month + 1)
        
        elif period == ReportPeriod.QUARTERLY:
            quarter = (now.month - 1) // 3 + 1
            start = now.replace(month=(quarter - 1) * 3 + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if quarter == 4:
                end = start.replace(year=start.year + 1, month=1)
            else:
                end = start.replace(month=quarter * 3 + 1)
        
        elif period == ReportPeriod.YEARLY:
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
        
        else:
            raise ValueError(f"Unsupported period: {period}")
        
        return start, end
    
    async def get_compliance_dashboard_data(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive compliance dashboard data.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dashboard data dictionary
        """
        # Generate reports for multiple periods
        daily_metrics = await self.generate_compliance_report(
            organization_id, ReportPeriod.DAILY
        )
        
        weekly_metrics = await self.generate_compliance_report(
            organization_id, ReportPeriod.WEEKLY
        )
        
        monthly_metrics = await self.generate_compliance_report(
            organization_id, ReportPeriod.MONTHLY
        )
        
        # Get processor reports
        processor_reports = await self.generate_processor_reports(
            organization_id, ReportPeriod.MONTHLY
        )
        
        # Get recent compliance trends
        trends = await self._get_compliance_trends(organization_id)
        
        return {
            "overview": {
                "daily": daily_metrics.__dict__,
                "weekly": weekly_metrics.__dict__,
                "monthly": monthly_metrics.__dict__
            },
            "processor_reports": [
                {
                    "processor_name": report.processor_name,
                    "success_rate": report.success_rate,
                    "compliance_score": report.compliance_score,
                    "total_transactions": report.total_transactions,
                    "issues_count": len(report.issues),
                    "last_sync": report.last_successful_sync.isoformat() if report.last_successful_sync else None
                }
                for report in processor_reports
            ],
            "trends": trends,
            "alerts": await self._get_compliance_alerts(organization_id),
            "recommendations": await self._get_compliance_recommendations(organization_id)
        }
    
    async def _get_compliance_trends(
        self,
        organization_id: UUID,
        days: int = 30
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get compliance trends over specified period."""
        trends = {
            "compliance_scores": [],
            "transaction_volumes": [],
            "error_rates": []
        }
        
        # Generate daily metrics for trend analysis
        for i in range(days):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            daily_metrics = await self.generate_compliance_report(
                organization_id,
                ReportPeriod.CUSTOM,
                day_start,
                day_end
            )
            
            trends["compliance_scores"].append({
                "date": day_start.date().isoformat(),
                "value": daily_metrics.compliance_score
            })
            
            trends["transaction_volumes"].append({
                "date": day_start.date().isoformat(),
                "value": daily_metrics.total_transactions
            })
            
            trends["error_rates"].append({
                "date": day_start.date().isoformat(),
                "value": daily_metrics.error_rate_percent
            })
        
        # Reverse to get chronological order
        for key in trends:
            trends[key].reverse()
        
        return trends
    
    async def _get_compliance_alerts(
        self,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get current compliance alerts."""
        alerts = []
        
        # Get current metrics
        current_metrics = await self.generate_compliance_report(
            organization_id, ReportPeriod.DAILY
        )
        
        # Check for threshold violations
        if current_metrics.error_rate_percent > self.compliance_thresholds['max_error_rate']:
            alerts.append({
                "type": "high_error_rate",
                "severity": "high",
                "message": f"Error rate of {current_metrics.error_rate_percent:.1f}% exceeds threshold",
                "value": current_metrics.error_rate_percent,
                "threshold": self.compliance_thresholds['max_error_rate']
            })
        
        if current_metrics.avg_submission_time_hours > self.compliance_thresholds['max_submission_delay_hours']:
            alerts.append({
                "type": "submission_delay",
                "severity": "medium",
                "message": f"Average submission time of {current_metrics.avg_submission_time_hours:.1f} hours exceeds SLA",
                "value": current_metrics.avg_submission_time_hours,
                "threshold": self.compliance_thresholds['max_submission_delay_hours']
            })
        
        if current_metrics.compliance_status == ComplianceStatus.CRITICAL:
            alerts.append({
                "type": "critical_compliance",
                "severity": "critical",
                "message": "Organization compliance status is critical",
                "value": current_metrics.compliance_score,
                "threshold": 70.0
            })
        
        return alerts
    
    async def _get_compliance_recommendations(
        self,
        organization_id: UUID
    ) -> List[str]:
        """Get compliance improvement recommendations."""
        recommendations = []
        
        # Get current metrics and processor reports
        current_metrics = await self.generate_compliance_report(
            organization_id, ReportPeriod.DAILY
        )
        
        processor_reports = await self.generate_processor_reports(
            organization_id, ReportPeriod.MONTHLY
        )
        
        # General recommendations based on metrics
        if current_metrics.compliance_score < 90:
            recommendations.append("Review and improve overall data quality processes")
        
        if current_metrics.error_rate_percent > 1:
            recommendations.append("Implement enhanced error handling and validation")
        
        if current_metrics.avg_submission_time_hours > 12:
            recommendations.append("Optimize invoice submission process for faster turnaround")
        
        # Processor-specific recommendations
        problematic_processors = [
            report for report in processor_reports
            if report.success_rate < 95 or len(report.issues) > 0
        ]
        
        if problematic_processors:
            recommendations.append(
                f"Address issues with {len(problematic_processors)} payment processor integrations"
            )
        
        # Coverage recommendations
        if current_metrics.processor_coverage_percent < 100:
            recommendations.append("Complete integration with all required payment processors")
        
        return recommendations
    
    async def export_compliance_report(
        self,
        organization_id: UUID,
        period: ReportPeriod = ReportPeriod.MONTHLY,
        format: str = "json"
    ) -> Union[Dict[str, Any], str]:
        """
        Export comprehensive compliance report.
        
        Args:
            organization_id: Organization ID
            period: Reporting period
            format: Export format (json, csv, pdf)
            
        Returns:
            Exported report data
        """
        # Generate comprehensive report
        metrics = await self.generate_compliance_report(organization_id, period)
        processor_reports = await self.generate_processor_reports(organization_id, period)
        
        report_data = {
            "organization_id": str(organization_id),
            "period": period.value,
            "generated_at": datetime.utcnow().isoformat(),
            "compliance_metrics": metrics.__dict__,
            "processor_reports": [
                {
                    "processor_name": report.processor_name,
                    "total_transactions": report.total_transactions,
                    "success_rate": report.success_rate,
                    "compliance_score": report.compliance_score,
                    "avg_processing_time_ms": report.avg_processing_time_ms,
                    "issues": report.issues,
                    "recommendations": report.recommendations
                }
                for report in processor_reports
            ]
        }
        
        if format.lower() == "json":
            return report_data
        
        elif format.lower() == "csv":
            # Convert to CSV format using pandas
            df = pd.DataFrame([{
                "Metric": "Compliance Score",
                "Value": metrics.compliance_score,
                "Status": metrics.compliance_status.value
            }, {
                "Metric": "Total Transactions",
                "Value": metrics.total_transactions,
                "Status": "N/A"
            }, {
                "Metric": "Error Rate %",
                "Value": metrics.error_rate_percent,
                "Status": "Alert" if metrics.error_rate_percent > 2 else "OK"
            }])
            
            return df.to_csv(index=False)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Factory function
def create_firs_compliance_analytics(
    db_manager: ProductionDatabaseManager,
    cache_manager: CacheManager,
    universal_processor: UniversalTransactionProcessor
) -> FIRSComplianceAnalytics:
    """
    Create FIRS compliance analytics instance.
    
    Args:
        db_manager: Production database manager
        cache_manager: Cache manager
        universal_processor: Universal transaction processor
        
    Returns:
        Configured FIRSComplianceAnalytics instance
    """
    return FIRSComplianceAnalytics(
        db_manager=db_manager,
        cache_manager=cache_manager,
        universal_processor=universal_processor
    )
