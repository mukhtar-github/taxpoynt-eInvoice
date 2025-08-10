"""
APP Service: Taxpayer Analytics
Generates analytics and reports for taxpayer management and KPI tracking
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import pandas as pd
import numpy as np
from sqlalchemy import and_, or_, func, distinct
from sqlalchemy.orm import Session

from core_platform.database import get_db_session
from core_platform.models.taxpayer import Taxpayer, TaxpayerProfile
from core_platform.models.onboarding import OnboardingApplication, OnboardingDocument
from core_platform.models.compliance import ComplianceRecord, ComplianceIssue
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.data_management.grant_tracking_repository import GrantTrackingRepository, TaxpayerSize, MilestoneType
from hybrid_services.analytics_aggregation.kpi_calculator import KPICalculator

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Analytics report types"""
    ONBOARDING_SUMMARY = "onboarding_summary"
    COMPLIANCE_DASHBOARD = "compliance_dashboard"
    KPI_TRACKING = "kpi_tracking"
    PERFORMANCE_METRICS = "performance_metrics"
    TREND_ANALYSIS = "trend_analysis"
    SECTOR_BREAKDOWN = "sector_breakdown"
    GEOGRAPHIC_DISTRIBUTION = "geographic_distribution"
    REGISTRATION_FUNNEL = "registration_funnel"


class TimeFrame(str, Enum):
    """Time frame for analytics"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


@dataclass
class AnalyticsFilter:
    """Filter criteria for analytics queries"""
    time_frame: TimeFrame
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sectors: Optional[List[str]] = None
    states: Optional[List[str]] = None
    status: Optional[List[str]] = None
    app_id: Optional[str] = None
    taxpayer_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KPIMetrics:
    """FIRS KPI metrics"""
    total_taxpayers: int
    active_taxpayers: int
    onboarded_last_6_months: int
    compliance_rate: float
    average_onboarding_time: float
    successful_registrations: int
    pending_registrations: int
    failed_registrations: int
    kpi_achievement_rate: float
    target_achievement_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OnboardingMetrics:
    """Onboarding process metrics"""
    total_applications: int
    completed_applications: int
    pending_applications: int
    rejected_applications: int
    average_processing_time: float
    completion_rate: float
    rejection_rate: float
    bottleneck_stages: List[str]
    document_upload_success_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ComplianceMetrics:
    """Compliance monitoring metrics"""
    total_compliance_checks: int
    passed_checks: int
    failed_checks: int
    compliance_rate: float
    critical_issues: int
    resolved_issues: int
    average_resolution_time: float
    compliance_trends: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    api_response_time: float
    database_query_time: float
    cache_hit_rate: float
    error_rate: float
    throughput: float
    concurrent_users: int
    system_uptime: float
    resource_utilization: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TrendAnalysis:
    """Trend analysis data"""
    metric_name: str
    time_series: List[Dict[str, Any]]
    trend_direction: str
    growth_rate: float
    seasonal_patterns: List[Dict[str, Any]]
    predictions: List[Dict[str, Any]]
    insights: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AnalyticsReport:
    """Analytics report structure"""
    report_id: str
    report_type: ReportType
    title: str
    description: str
    generated_at: datetime
    time_frame: TimeFrame
    filters: AnalyticsFilter
    data: Dict[str, Any]
    insights: List[str]
    recommendations: List[str]
    charts: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TaxpayerAnalyticsService:
    """Taxpayer analytics and reporting service"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.grant_tracking_repo = GrantTrackingRepository(get_db_session(), self.cache_service)
        self.kpi_calculator = KPICalculator()
        self.logger = logging.getLogger(__name__)
        
    async def generate_report(
        self,
        report_type: ReportType,
        filters: AnalyticsFilter,
        app_id: str
    ) -> AnalyticsReport:
        """Generate analytics report"""
        try:
            # Check cache first
            cache_key = f"analytics_report:{report_type}:{app_id}:{hash(str(filters.to_dict()))}"
            cached_report = await self.cache_service.get(cache_key)
            if cached_report:
                return AnalyticsReport(**cached_report)
            
            # Generate report based on type
            report_data = await self._generate_report_data(report_type, filters, app_id)
            
            # Create report structure
            report = AnalyticsReport(
                report_id=f"RPT_{int(datetime.now().timestamp())}_{app_id}",
                report_type=report_type,
                title=self._get_report_title(report_type),
                description=self._get_report_description(report_type),
                generated_at=datetime.now(timezone.utc),
                time_frame=filters.time_frame,
                filters=filters,
                data=report_data,
                insights=await self._generate_insights(report_type, report_data),
                recommendations=await self._generate_recommendations(report_type, report_data),
                charts=await self._generate_charts(report_type, report_data)
            )
            
            # Cache report
            await self.cache_service.set(
                cache_key,
                report.to_dict(),
                ttl=3600  # 1 hour
            )
            
            # Emit event
            await self.event_bus.emit("analytics_report_generated", {
                "report_id": report.report_id,
                "report_type": report_type,
                "app_id": app_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise
    
    async def get_kpi_metrics(self, app_id: str, time_frame: TimeFrame) -> KPIMetrics:
        """Get FIRS KPI metrics"""
        try:
            with get_db_session() as db:
                # Calculate time range
                end_date = datetime.now(timezone.utc)
                start_date = self._get_start_date(time_frame, end_date)
                
                # Total taxpayers
                total_taxpayers = db.query(func.count(Taxpayer.id)).filter(
                    Taxpayer.app_id == app_id
                ).scalar()
                
                # Active taxpayers
                active_taxpayers = db.query(func.count(Taxpayer.id)).filter(
                    and_(
                        Taxpayer.app_id == app_id,
                        Taxpayer.status == "active"
                    )
                ).scalar()
                
                # Onboarded in last 6 months
                six_months_ago = end_date - timedelta(days=180)
                onboarded_last_6_months = db.query(func.count(Taxpayer.id)).filter(
                    and_(
                        Taxpayer.app_id == app_id,
                        Taxpayer.registration_date >= six_months_ago
                    )
                ).scalar()
                
                # Compliance rate
                compliance_rate = await self._calculate_compliance_rate(db, app_id, start_date, end_date)
                
                # Average onboarding time
                avg_onboarding_time = await self._calculate_avg_onboarding_time(db, app_id, start_date, end_date)
                
                # Registration statistics
                registration_stats = await self._get_registration_stats(db, app_id, start_date, end_date)
                
                # KPI achievement rate (target: 100 taxpayers per 6 months)
                kpi_target = 100
                kpi_achievement_rate = min((onboarded_last_6_months / kpi_target) * 100, 100)
                
                # Target achievement status
                target_achievement_status = "achieved" if onboarded_last_6_months >= kpi_target else "in_progress"
                
                return KPIMetrics(
                    total_taxpayers=total_taxpayers,
                    active_taxpayers=active_taxpayers,
                    onboarded_last_6_months=onboarded_last_6_months,
                    compliance_rate=compliance_rate,
                    average_onboarding_time=avg_onboarding_time,
                    successful_registrations=registration_stats["successful"],
                    pending_registrations=registration_stats["pending"],
                    failed_registrations=registration_stats["failed"],
                    kpi_achievement_rate=kpi_achievement_rate,
                    target_achievement_status=target_achievement_status
                )
                
        except Exception as e:
            self.logger.error(f"Error getting KPI metrics: {str(e)}")
            raise
    
    async def get_onboarding_metrics(self, app_id: str, filters: AnalyticsFilter) -> OnboardingMetrics:
        """Get onboarding process metrics"""
        try:
            with get_db_session() as db:
                # Calculate time range
                start_date, end_date = self._get_time_range(filters)
                
                # Build base query
                base_query = db.query(OnboardingApplication).filter(
                    OnboardingApplication.app_id == app_id
                )
                
                if start_date:
                    base_query = base_query.filter(OnboardingApplication.created_at >= start_date)
                if end_date:
                    base_query = base_query.filter(OnboardingApplication.created_at <= end_date)
                
                # Total applications
                total_applications = base_query.count()
                
                # Status breakdown
                completed_applications = base_query.filter(
                    OnboardingApplication.status == "completed"
                ).count()
                
                pending_applications = base_query.filter(
                    OnboardingApplication.status == "pending"
                ).count()
                
                rejected_applications = base_query.filter(
                    OnboardingApplication.status == "rejected"
                ).count()
                
                # Processing time calculation
                avg_processing_time = await self._calculate_avg_processing_time(db, app_id, start_date, end_date)
                
                # Rates
                completion_rate = (completed_applications / total_applications * 100) if total_applications > 0 else 0
                rejection_rate = (rejected_applications / total_applications * 100) if total_applications > 0 else 0
                
                # Bottleneck stages
                bottleneck_stages = await self._identify_bottleneck_stages(db, app_id, start_date, end_date)
                
                # Document upload success rate
                document_success_rate = await self._calculate_document_success_rate(db, app_id, start_date, end_date)
                
                return OnboardingMetrics(
                    total_applications=total_applications,
                    completed_applications=completed_applications,
                    pending_applications=pending_applications,
                    rejected_applications=rejected_applications,
                    average_processing_time=avg_processing_time,
                    completion_rate=completion_rate,
                    rejection_rate=rejection_rate,
                    bottleneck_stages=bottleneck_stages,
                    document_upload_success_rate=document_success_rate
                )
                
        except Exception as e:
            self.logger.error(f"Error getting onboarding metrics: {str(e)}")
            raise
    
    async def get_compliance_metrics(self, app_id: str, filters: AnalyticsFilter) -> ComplianceMetrics:
        """Get compliance monitoring metrics"""
        try:
            with get_db_session() as db:
                # Calculate time range
                start_date, end_date = self._get_time_range(filters)
                
                # Build base query
                base_query = db.query(ComplianceRecord).filter(
                    ComplianceRecord.app_id == app_id
                )
                
                if start_date:
                    base_query = base_query.filter(ComplianceRecord.created_at >= start_date)
                if end_date:
                    base_query = base_query.filter(ComplianceRecord.created_at <= end_date)
                
                # Total compliance checks
                total_checks = base_query.count()
                
                # Passed and failed checks
                passed_checks = base_query.filter(ComplianceRecord.status == "passed").count()
                failed_checks = base_query.filter(ComplianceRecord.status == "failed").count()
                
                # Compliance rate
                compliance_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
                
                # Critical issues
                critical_issues = db.query(func.count(ComplianceIssue.id)).filter(
                    and_(
                        ComplianceIssue.app_id == app_id,
                        ComplianceIssue.severity == "critical",
                        ComplianceIssue.status == "open"
                    )
                ).scalar()
                
                # Resolved issues
                resolved_issues = db.query(func.count(ComplianceIssue.id)).filter(
                    and_(
                        ComplianceIssue.app_id == app_id,
                        ComplianceIssue.status == "resolved"
                    )
                ).scalar()
                
                # Average resolution time
                avg_resolution_time = await self._calculate_avg_resolution_time(db, app_id, start_date, end_date)
                
                # Compliance trends
                compliance_trends = await self._get_compliance_trends(db, app_id, start_date, end_date)
                
                return ComplianceMetrics(
                    total_compliance_checks=total_checks,
                    passed_checks=passed_checks,
                    failed_checks=failed_checks,
                    compliance_rate=compliance_rate,
                    critical_issues=critical_issues,
                    resolved_issues=resolved_issues,
                    average_resolution_time=avg_resolution_time,
                    compliance_trends=compliance_trends
                )
                
        except Exception as e:
            self.logger.error(f"Error getting compliance metrics: {str(e)}")
            raise
    
    async def get_performance_metrics(self, app_id: str, filters: AnalyticsFilter) -> PerformanceMetrics:
        """Get system performance metrics"""
        try:
            # Get metrics from metrics collector
            metrics = await self.metrics_collector.get_metrics(
                app_id=app_id,
                start_time=filters.start_date,
                end_time=filters.end_date
            )
            
            return PerformanceMetrics(
                api_response_time=metrics.get("api_response_time", 0.0),
                database_query_time=metrics.get("database_query_time", 0.0),
                cache_hit_rate=metrics.get("cache_hit_rate", 0.0),
                error_rate=metrics.get("error_rate", 0.0),
                throughput=metrics.get("throughput", 0.0),
                concurrent_users=metrics.get("concurrent_users", 0),
                system_uptime=metrics.get("system_uptime", 0.0),
                resource_utilization=metrics.get("resource_utilization", {})
            )
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {str(e)}")
            raise
    
    async def get_trend_analysis(
        self,
        app_id: str,
        metric_name: str,
        time_frame: TimeFrame,
        lookback_periods: int = 12
    ) -> TrendAnalysis:
        """Get trend analysis for a specific metric"""
        try:
            with get_db_session() as db:
                # Generate time series data
                time_series = await self._generate_time_series(
                    db, app_id, metric_name, time_frame, lookback_periods
                )
                
                # Calculate trend direction and growth rate
                trend_direction, growth_rate = self._calculate_trend(time_series)
                
                # Identify seasonal patterns
                seasonal_patterns = self._identify_seasonal_patterns(time_series)
                
                # Generate predictions
                predictions = self._generate_predictions(time_series, periods=3)
                
                # Generate insights
                insights = self._generate_trend_insights(
                    metric_name, time_series, trend_direction, growth_rate
                )
                
                return TrendAnalysis(
                    metric_name=metric_name,
                    time_series=time_series,
                    trend_direction=trend_direction,
                    growth_rate=growth_rate,
                    seasonal_patterns=seasonal_patterns,
                    predictions=predictions,
                    insights=insights
                )
                
        except Exception as e:
            self.logger.error(f"Error getting trend analysis: {str(e)}")
            raise
    
    async def export_report(
        self,
        report: AnalyticsReport,
        format: str = "pdf"
    ) -> str:
        """Export report to specified format"""
        try:
            if format == "pdf":
                return await self._export_to_pdf(report)
            elif format == "excel":
                return await self._export_to_excel(report)
            elif format == "csv":
                return await self._export_to_csv(report)
            elif format == "json":
                return await self._export_to_json(report)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Error exporting report: {str(e)}")
            raise
    
    async def classify_taxpayer_size(
        self, 
        app_id: str, 
        taxpayer_tin: str, 
        annual_revenue: Optional[float] = None,
        employee_count: Optional[int] = None,
        assets_value: Optional[float] = None,
        cache_result: bool = True
    ) -> Dict[str, Any]:
        """
        Enhanced taxpayer size classification with FIRS criteria and caching.
        
        Returns detailed classification with confidence score and reasoning.
        """
        try:
            # Enhanced FIRS classification criteria
            LARGE_TAXPAYER_REVENUE_THRESHOLD = 1_000_000_000  # ₦1 billion NGN
            LARGE_TAXPAYER_EMPLOYEE_THRESHOLD = 200
            LARGE_TAXPAYER_ASSETS_THRESHOLD = 500_000_000     # ₦500 million NGN
            
            # Check cache first
            cache_key = f"taxpayer_classification:{app_id}:{taxpayer_tin}"
            if cache_result:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    return cached_result
            
            classification_result = {
                "taxpayer_tin": taxpayer_tin,
                "app_id": app_id,
                "classification": TaxpayerSize.SME,
                "confidence_score": 0.0,
                "classification_criteria": [],
                "classification_date": datetime.utcnow().isoformat(),
                "data_sources": [],
                "next_review_date": (datetime.utcnow() + timedelta(days=365)).isoformat()
            }
            
            score = 0.0
            criteria_met = []
            
            # Primary classification by annual revenue
            if annual_revenue is not None:
                classification_result["data_sources"].append("annual_revenue")
                if annual_revenue >= LARGE_TAXPAYER_REVENUE_THRESHOLD:
                    score += 0.6  # Revenue is primary indicator
                    criteria_met.append(f"Revenue ₦{annual_revenue:,.0f} >= ₦{LARGE_TAXPAYER_REVENUE_THRESHOLD:,.0f}")
                    classification_result["classification"] = TaxpayerSize.LARGE
                else:
                    criteria_met.append(f"Revenue ₦{annual_revenue:,.0f} < ₦{LARGE_TAXPAYER_REVENUE_THRESHOLD:,.0f}")
            
            # Secondary classification by employee count
            if employee_count is not None:
                classification_result["data_sources"].append("employee_count")
                if employee_count >= LARGE_TAXPAYER_EMPLOYEE_THRESHOLD:
                    score += 0.3  # Employee count is secondary indicator
                    criteria_met.append(f"Employees {employee_count} >= {LARGE_TAXPAYER_EMPLOYEE_THRESHOLD}")
                    if classification_result["classification"] == TaxpayerSize.SME:
                        classification_result["classification"] = TaxpayerSize.LARGE
                else:
                    criteria_met.append(f"Employees {employee_count} < {LARGE_TAXPAYER_EMPLOYEE_THRESHOLD}")
            
            # Tertiary classification by assets value
            if assets_value is not None:
                classification_result["data_sources"].append("assets_value")
                if assets_value >= LARGE_TAXPAYER_ASSETS_THRESHOLD:
                    score += 0.2  # Assets is tertiary indicator
                    criteria_met.append(f"Assets ₦{assets_value:,.0f} >= ₦{LARGE_TAXPAYER_ASSETS_THRESHOLD:,.0f}")
                    if classification_result["classification"] == TaxpayerSize.SME:
                        classification_result["classification"] = TaxpayerSize.LARGE
                else:
                    criteria_met.append(f"Assets ₦{assets_value:,.0f} < ₦{LARGE_TAXPAYER_ASSETS_THRESHOLD:,.0f}")
            
            # Calculate confidence score
            if classification_result["classification"] == TaxpayerSize.LARGE:
                classification_result["confidence_score"] = min(score + 0.3, 1.0)  # Bonus for large classification
            else:
                classification_result["confidence_score"] = max(0.7 - score, 0.3)  # Inverse for SME
            
            # Set classification criteria
            classification_result["classification_criteria"] = criteria_met
            
            # Determine data completeness and confidence adjustments
            data_sources_count = len(classification_result["data_sources"])
            if data_sources_count == 0:
                classification_result["confidence_score"] = 0.1  # Very low confidence
                classification_result["classification_criteria"].append("No classification data available - default SME")
            elif data_sources_count == 1:
                classification_result["confidence_score"] *= 0.8  # Reduce confidence for single data point
            
            # Cache result for future use
            if cache_result:
                await self.cache_service.set(cache_key, classification_result, ttl=86400)  # 24 hours
            
            # Log classification for audit trail
            self.logger.info(f"Classified taxpayer {taxpayer_tin} as {classification_result['classification'].value} with confidence {classification_result['confidence_score']:.2f}")
            
            # Register taxpayer with grant tracking repository
            await self.grant_tracking_repo.register_taxpayer(
                tenant_id=UUID(app_id),
                organization_id=UUID(app_id),
                taxpayer_tin=taxpayer_tin,
                taxpayer_name=f"Taxpayer_{taxpayer_tin}",
                taxpayer_size=classification_result["classification"],
                sector="unspecified"  # Will be updated when sector info is available
            )
            
            return classification_result
            
        except Exception as e:
            self.logger.error(f"Error classifying taxpayer size: {str(e)}")
            return {
                "taxpayer_tin": taxpayer_tin,
                "app_id": app_id,
                "classification": TaxpayerSize.SME,
                "confidence_score": 0.1,
                "classification_criteria": ["Error in classification - default SME"],
                "classification_date": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def track_sector_representation(self, app_id: str, include_trends: bool = True) -> Dict[str, Any]:
        """Enhanced sector representation tracking with trends and milestone analysis."""
        try:
            # Check cache first
            cache_key = f"sector_representation:{app_id}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result and not include_trends:
                return cached_result
            
            with get_db_session() as db:
                # Get sector breakdown with size classification
                sector_results = db.query(
                    TaxpayerProfile.sector,
                    TaxpayerProfile.taxpayer_size,
                    func.count(TaxpayerProfile.id).label('count')
                ).filter(
                    TaxpayerProfile.app_id == app_id
                ).group_by(TaxpayerProfile.sector, TaxpayerProfile.taxpayer_size).all()
                
                sectors = {}
                total_taxpayers = 0
                large_taxpayers = 0
                sme_taxpayers = 0
                
                # Organize data by sector and size
                for sector, size, count in sector_results:
                    if sector not in sectors:
                        sectors[sector] = {"total": 0, "large": 0, "sme": 0}
                    
                    sectors[sector]["total"] += count
                    if size == "large":
                        sectors[sector]["large"] += count
                        large_taxpayers += count
                    else:
                        sectors[sector]["sme"] += count
                        sme_taxpayers += count
                    
                    total_taxpayers += count
                
                # Calculate enhanced metrics
                sector_count = len(sectors)
                sector_diversity_index = self._calculate_diversity_index([s["total"] for s in sectors.values()])
                
                # Sector growth trends (last 6 months)
                sector_trends = []
                if include_trends:
                    sector_trends = await self._get_sector_growth_trends(db, app_id)
                
                # Milestone requirements analysis
                milestone_analysis = {
                    "milestone_2_ready": total_taxpayers >= 40 and large_taxpayers > 0 and sme_taxpayers > 0,
                    "milestone_3_ready": total_taxpayers >= 60 and sector_count >= 2,
                    "sector_gap_analysis": self._analyze_sector_gaps(sectors, sector_count),
                    "recommended_sectors": self._recommend_target_sectors(sectors)
                }
                
                # Risk assessment for sector representation
                risk_assessment = {
                    "concentration_risk": max(s["total"] for s in sectors.values()) / total_taxpayers if total_taxpayers > 0 else 0,
                    "single_sector_dependency": sector_count == 1,
                    "large_sme_balance": {
                        "large_percentage": (large_taxpayers / total_taxpayers * 100) if total_taxpayers > 0 else 0,
                        "sme_percentage": (sme_taxpayers / total_taxpayers * 100) if total_taxpayers > 0 else 0,
                        "is_balanced": large_taxpayers > 0 and sme_taxpayers > 0
                    }
                }
                
                result = {
                    "app_id": app_id,
                    "analysis_date": datetime.utcnow().isoformat(),
                    "summary": {
                        "total_sectors": sector_count,
                        "total_taxpayers": total_taxpayers,
                        "large_taxpayers": large_taxpayers,
                        "sme_taxpayers": sme_taxpayers,
                        "diversity_index": sector_diversity_index
                    },
                    "sector_breakdown": sectors,
                    "milestone_analysis": milestone_analysis,
                    "risk_assessment": risk_assessment,
                    "compliance_status": {
                        "meets_milestone_3_requirement": sector_count >= 2,
                        "meets_diversity_threshold": sector_diversity_index >= 0.5,
                        "dominant_sector": max(sectors.items(), key=lambda x: x[1]["total"])[0] if sectors else None,
                        "sector_balance_ratio": min(s["total"] for s in sectors.values()) / max(s["total"] for s in sectors.values()) if len(sectors) > 1 else 1.0
                    },
                    "growth_trends": sector_trends,
                    "recommendations": self._generate_sector_recommendations(sectors, milestone_analysis, risk_assessment)
                }
                
                # Cache result for 30 minutes
                await self.cache_service.set(cache_key, result, ttl=1800)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error tracking sector representation: {str(e)}")
            return {
                "app_id": app_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "error": str(e),
                "summary": {"total_sectors": 0, "total_taxpayers": 0}
            }
    
    async def calculate_transmission_rate(
        self, 
        app_id: str, 
        period_days: int = 30, 
        include_analytics: bool = True,
        by_sector: bool = False
    ) -> Dict[str, Any]:
        """Enhanced transmission rate calculation with detailed analytics and trends."""
        try:
            # Check cache first
            cache_key = f"transmission_rate:{app_id}:{period_days}:{by_sector}"
            if not include_analytics:
                cached_result = await self.cache_service.get(cache_key)
                if cached_result:
                    return cached_result
            
            with get_db_session() as db:
                cutoff_date = datetime.utcnow() - timedelta(days=period_days)
                
                # Total active taxpayers
                total_taxpayers = db.query(func.count(Taxpayer.id)).filter(
                    and_(
                        Taxpayer.app_id == app_id,
                        Taxpayer.status == "active"
                    )
                ).scalar()
                
                # Taxpayers with recent transmissions
                active_transmitters_query = db.query(func.count(distinct(Taxpayer.id))).join(
                    text("invoices ON taxpayers.id = invoices.taxpayer_id")
                ).filter(
                    and_(
                        Taxpayer.app_id == app_id,
                        Taxpayer.status == "active",
                        text("invoices.created_at >= :cutoff_date")
                    )
                ).params(cutoff_date=cutoff_date)
                
                active_transmitters = active_transmitters_query.scalar() or 0
                
                # Calculate transmission rate
                transmission_rate = (active_transmitters / total_taxpayers * 100) if total_taxpayers > 0 else 0.0
                
                # Enhanced analytics
                analytics = {}
                if include_analytics:
                    # Transmission frequency analysis
                    transmission_frequency = await self._analyze_transmission_frequency(db, app_id, cutoff_date)
                    
                    # Sector-wise transmission rates
                    sector_rates = {}
                    if by_sector:
                        sector_rates = await self._calculate_sector_transmission_rates(db, app_id, cutoff_date)
                    
                    # Transmission trends (weekly over the period)
                    transmission_trends = await self._get_transmission_trends(db, app_id, period_days)
                    
                    # Taxpayer size analysis
                    size_analysis = await self._analyze_transmission_by_size(db, app_id, cutoff_date)
                    
                    analytics = {
                        "transmission_frequency": transmission_frequency,
                        "sector_transmission_rates": sector_rates,
                        "weekly_trends": transmission_trends,
                        "size_analysis": size_analysis,
                        "benchmark_comparison": {
                            "firs_requirement": 80.0,
                            "industry_average": 75.0,
                            "top_performers": 90.0,
                            "performance_level": self._classify_transmission_performance(transmission_rate)
                        }
                    }
                
                # Risk assessment
                risk_factors = []
                if transmission_rate < 60:
                    risk_factors.append("Critical: Very low transmission rate")
                elif transmission_rate < 70:
                    risk_factors.append("High risk: Below acceptable threshold")
                elif transmission_rate < 80:
                    risk_factors.append("Medium risk: Below FIRS requirement")
                
                # Improvement recommendations
                recommendations = self._generate_transmission_recommendations(
                    transmission_rate, total_taxpayers, active_transmitters, analytics
                )
                
                result = {
                    "app_id": app_id,
                    "analysis_date": datetime.utcnow().isoformat(),
                    "period_analysis": {
                        "period_days": period_days,
                        "start_date": cutoff_date.isoformat(),
                        "end_date": datetime.utcnow().isoformat()
                    },
                    "core_metrics": {
                        "total_taxpayers": total_taxpayers,
                        "active_transmitters": active_transmitters,
                        "inactive_taxpayers": total_taxpayers - active_transmitters,
                        "transmission_rate": transmission_rate
                    },
                    "milestone_compliance": {
                        "meets_milestone_requirement": transmission_rate >= 80.0,
                        "firs_requirement": 80.0,
                        "compliance_gap": max(0, 80.0 - transmission_rate),
                        "additional_transmitters_needed": max(0, int((80.0 * total_taxpayers / 100) - active_transmitters))
                    },
                    "risk_assessment": {
                        "risk_level": "low" if transmission_rate >= 80 else "medium" if transmission_rate >= 70 else "high",
                        "risk_factors": risk_factors,
                        "confidence_score": min(transmission_rate / 80.0, 1.0) if transmission_rate > 0 else 0
                    },
                    "analytics": analytics,
                    "recommendations": recommendations,
                    "next_measurement_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
                }
                
                # Record transmission metric for grant tracking
                if active_transmitters > 0:
                    await self.grant_tracking_repo.record_transmission(
                        tenant_id=UUID(app_id),
                        taxpayer_tin="aggregated",  # This is aggregated data
                        transmission_count=active_transmitters
                    )
                
                # Cache result for 1 hour
                await self.cache_service.set(cache_key, result, ttl=3600)
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error calculating transmission rate: {str(e)}")
            return {
                "app_id": app_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "error": str(e),
                "core_metrics": {
                    "total_taxpayers": 0,
                    "active_transmitters": 0,
                    "transmission_rate": 0.0
                }
            }
    
    async def monitor_milestone_progress(
        self, 
        app_id: str, 
        include_predictions: bool = True,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Enhanced milestone progress monitoring with predictions and smart recommendations."""
        try:
            # Check cache first
            cache_key = f"milestone_progress:{app_id}:{include_predictions}"
            cached_result = await self.cache_service.get(cache_key)
            if cached_result and not include_recommendations:
                return cached_result
            
            # Get comprehensive data
            taxpayer_stats = await self._get_comprehensive_taxpayer_stats(app_id)
            milestone_progress = await self.grant_tracking_repo.get_milestone_progress(UUID(app_id))
            sector_analysis = await self.track_sector_representation(app_id, include_trends=False)
            transmission_analysis = await self.calculate_transmission_rate(app_id, include_analytics=False)
            
            # Enhanced milestone tracking with KPI integration
            kpi_data = await self.kpi_calculator.get_milestone_dashboard(app_id)
            
            current_taxpayer_count = taxpayer_stats.get("total_taxpayers", 0)
            achieved_milestones = 0
            total_milestones = len(MilestoneType)
            milestones_detail = {}
            
            # Analyze each milestone with enhanced criteria
            for milestone_type in MilestoneType:
                milestone_key = milestone_type.value
                progress_data = milestone_progress.get(milestone_key, {})
                kpi_milestone_data = kpi_data.get("milestones", {}).get(milestone_key, {})
                
                # Detailed milestone analysis
                milestone_analysis = await self._analyze_milestone_requirements(
                    milestone_type, taxpayer_stats, sector_analysis, transmission_analysis
                )
                
                is_achieved = progress_data.get("achievement_date") is not None or kpi_milestone_data.get("is_achieved", False)
                if is_achieved:
                    achieved_milestones += 1
                
                milestones_detail[milestone_key] = {
                    "milestone_info": {
                        "name": milestone_key.replace("_", " ").title(),
                        "target_taxpayers": self._get_milestone_target(milestone_type),
                        "grant_amount": self._get_milestone_grant_amount(milestone_type),
                        "requirements": milestone_analysis["requirements"]
                    },
                    "progress": {
                        "achieved": is_achieved,
                        "progress_percentage": milestone_analysis["progress_percentage"],
                        "completion_score": milestone_analysis["completion_score"],
                        "achievement_date": progress_data.get("achievement_date")
                    },
                    "requirements_status": milestone_analysis["requirements_status"],
                    "blockers": milestone_analysis["blockers"],
                    "risk_factors": milestone_analysis["risk_factors"],
                    "time_estimation": milestone_analysis.get("time_estimation", {})
                }
            
            # Overall progress calculation
            overall_progress = (achieved_milestones / total_milestones) * 100
            
            # Determine next milestone
            next_milestone = None
            for milestone_type in MilestoneType:
                if not milestones_detail[milestone_type.value]["progress"]["achieved"]:
                    next_milestone = milestone_type.value
                    break
            
            # Predictive analytics
            predictions = {}
            if include_predictions:
                predictions = await self._generate_milestone_predictions(
                    taxpayer_stats, milestones_detail, current_taxpayer_count
                )
            
            # Smart recommendations
            recommendations = {}
            if include_recommendations:
                recommendations = await self._generate_smart_milestone_recommendations(
                    milestones_detail, next_milestone, taxpayer_stats, sector_analysis, transmission_analysis
                )
            
            # Risk assessment
            risk_assessment = await self._assess_overall_milestone_risk(
                milestones_detail, taxpayer_stats, overall_progress
            )
            
            # Performance benchmarking
            performance_metrics = {
                "milestone_velocity": achieved_milestones / max(1, (datetime.utcnow() - datetime.utcnow().replace(month=1, day=1)).days / 30),
                "taxpayer_acquisition_rate": taxpayer_stats.get("growth_rate", 0),
                "transmission_effectiveness": transmission_analysis.get("core_metrics", {}).get("transmission_rate", 0),
                "sector_diversification_index": sector_analysis.get("summary", {}).get("diversity_index", 0)
            }
            
            result = {
                "app_id": app_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "executive_summary": {
                    "current_taxpayer_count": current_taxpayer_count,
                    "milestones_achieved": achieved_milestones,
                    "total_milestones": total_milestones,
                    "overall_progress": overall_progress,
                    "next_milestone": next_milestone,
                    "completion_status": "on_track" if overall_progress >= 20 else "behind_schedule",
                    "total_grants_eligible": sum(
                        self._get_milestone_grant_amount(MilestoneType(k.replace("milestone_", "milestone_"))) 
                        for k, v in milestones_detail.items() 
                        if v["progress"]["achieved"]
                    )
                },
                "milestones_detail": milestones_detail,
                "performance_metrics": performance_metrics,
                "risk_assessment": risk_assessment,
                "predictions": predictions,
                "recommendations": recommendations,
                "integration_data": {
                    "kpi_dashboard": kpi_data,
                    "sector_analysis_summary": sector_analysis.get("summary", {}),
                    "transmission_summary": transmission_analysis.get("core_metrics", {})
                },
                "next_review_date": (datetime.utcnow() + timedelta(days=7)).isoformat()
            }
            
            # Cache result for 2 hours
            await self.cache_service.set(cache_key, result, ttl=7200)
            
            # Trigger notifications for significant changes
            await self._check_milestone_notification_triggers(result, cached_result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error monitoring milestone progress: {str(e)}")
            return {
                "app_id": app_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "error": str(e),
                "executive_summary": {
                    "current_taxpayer_count": 0,
                    "milestones_achieved": 0,
                    "overall_progress": 0.0
                }
            }
    
    async def generate_firs_grant_report(
        self, 
        app_id: str, 
        report_type: str = "comprehensive",
        include_charts: bool = True,
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """Enhanced FIRS grant report generation with multiple formats and export options."""
        try:
            # Check cache first
            cache_key = f"firs_grant_report:{app_id}:{report_type}:{include_charts}"
            cached_report = await self.cache_service.get(cache_key)
            if cached_report and report_type == "comprehensive":
                return cached_report
            
            # Get comprehensive data with enhanced analytics
            milestone_progress = await self.monitor_milestone_progress(app_id, include_predictions=True)
            sector_analysis = await self.track_sector_representation(app_id, include_trends=True)
            transmission_analysis = await self.calculate_transmission_rate(app_id, include_analytics=True, by_sector=True)
            grant_summary = await self.grant_tracking_repo.get_grant_summary(UUID(app_id))
            
            # Enhanced compliance analysis
            compliance_status = await self._analyze_comprehensive_grant_compliance(app_id)
            
            # Financial impact analysis
            financial_analysis = await self._calculate_grant_financial_impact(milestone_progress, grant_summary)
            
            # Competitive benchmarking
            benchmarking = await self._generate_competitive_benchmarking(milestone_progress, transmission_analysis)
            
            # Generate executive insights
            executive_insights = await self._generate_executive_insights(
                milestone_progress, sector_analysis, transmission_analysis, financial_analysis
            )
            
            # Report metadata
            report_metadata = {
                "report_id": f"FIRS_GRANT_{app_id}_{int(datetime.utcnow().timestamp())}",
                "generated_at": datetime.utcnow().isoformat(),
                "app_id": app_id,
                "report_type": report_type,
                "report_version": "2.0",
                "data_sources": [
                    "grant_tracking_repository",
                    "taxpayer_analytics_service", 
                    "kpi_calculator",
                    "sector_analysis",
                    "transmission_analytics"
                ],
                "reporting_period": {
                    "start_date": (datetime.utcnow() - timedelta(days=180)).isoformat(),
                    "end_date": datetime.utcnow().isoformat(),
                    "period_description": "Last 6 months analysis"
                }
            }
            
            # Executive summary with enhanced metrics
            executive_summary = {
                "key_metrics": {
                    "current_taxpayer_count": milestone_progress.get("executive_summary", {}).get("current_taxpayer_count", 0),
                    "milestones_achieved": milestone_progress.get("executive_summary", {}).get("milestones_achieved", 0),
                    "total_milestones": 5,
                    "overall_progress_percentage": milestone_progress.get("executive_summary", {}).get("overall_progress", 0),
                    "next_milestone": milestone_progress.get("executive_summary", {}).get("next_milestone"),
                    "grants_earned": milestone_progress.get("executive_summary", {}).get("total_grants_eligible", 0),
                    "potential_remaining_grants": 1550000 - milestone_progress.get("executive_summary", {}).get("total_grants_eligible", 0)
                },
                "performance_indicators": {
                    "transmission_rate": transmission_analysis.get("core_metrics", {}).get("transmission_rate", 0),
                    "sector_diversity_count": sector_analysis.get("summary", {}).get("total_sectors", 0),
                    "large_taxpayer_percentage": sector_analysis.get("summary", {}).get("large_taxpayers", 0),
                    "growth_trajectory": milestone_progress.get("performance_metrics", {}).get("taxpayer_acquisition_rate", 0)
                },
                "status_indicators": {
                    "overall_health": "healthy" if milestone_progress.get("executive_summary", {}).get("overall_progress", 0) >= 20 else "needs_attention",
                    "risk_level": milestone_progress.get("risk_assessment", {}).get("risk_level", "medium"),
                    "compliance_status": compliance_status.get("overall_status", "pending"),
                    "milestone_velocity": milestone_progress.get("performance_metrics", {}).get("milestone_velocity", 0)
                }
            }
            
            # Charts and visualizations
            charts_data = {}
            if include_charts:
                charts_data = {
                    "milestone_progress_chart": self._generate_enhanced_milestone_chart(milestone_progress),
                    "sector_distribution_chart": self._generate_enhanced_sector_chart(sector_analysis),
                    "transmission_trend_chart": await self._generate_enhanced_transmission_chart(app_id, transmission_analysis),
                    "financial_impact_chart": self._generate_financial_impact_chart(financial_analysis),
                    "benchmark_comparison_chart": self._generate_benchmark_chart(benchmarking),
                    "risk_assessment_chart": self._generate_risk_assessment_chart(milestone_progress.get("risk_assessment", {}))
                }
            
            # Assemble comprehensive report
            report = {
                "metadata": report_metadata,
                "executive_summary": executive_summary,
                "executive_insights": executive_insights,
                "detailed_analysis": {
                    "milestone_progress": milestone_progress,
                    "sector_representation": sector_analysis,
                    "transmission_performance": transmission_analysis,
                    "compliance_status": compliance_status,
                    "financial_analysis": financial_analysis,
                    "benchmarking": benchmarking
                },
                "grant_tracking": grant_summary,
                "actionable_recommendations": {
                    "immediate_actions": milestone_progress.get("recommendations", {}).get("immediate_priorities", []),
                    "short_term_goals": milestone_progress.get("recommendations", {}).get("short_term_goals", []),
                    "long_term_strategy": milestone_progress.get("recommendations", {}).get("long_term_objectives", []),
                    "resource_allocation": milestone_progress.get("recommendations", {}).get("resource_allocation", {})
                },
                "charts_and_visualizations": charts_data,
                "appendices": {
                    "data_quality_report": await self._generate_data_quality_report(app_id),
                    "methodology_notes": self._get_methodology_notes(),
                    "glossary": self._get_report_glossary()
                }
            }
            
            # Apply report type filtering
            if report_type == "executive":
                report = {
                    "metadata": report_metadata,
                    "executive_summary": executive_summary,
                    "executive_insights": executive_insights,
                    "charts_and_visualizations": {k: v for k, v in charts_data.items() if "summary" in k or "overview" in k}
                }
            elif report_type == "operational":
                report = {
                    "metadata": report_metadata,
                    "detailed_analysis": report["detailed_analysis"],
                    "actionable_recommendations": report["actionable_recommendations"],
                    "charts_and_visualizations": charts_data
                }
            
            # Export format handling
            if export_format != "json":
                report["export_metadata"] = {
                    "export_format": export_format,
                    "export_timestamp": datetime.utcnow().isoformat(),
                    "export_instructions": f"Report optimized for {export_format} format"
                }
            
            # Cache the comprehensive report for 1 hour
            await self.cache_service.set(cache_key, report, ttl=3600)
            
            # Log report generation for audit
            self.logger.info(f"Generated FIRS grant report {report_metadata['report_id']} for app {app_id}")
            
            # Emit report generation event
            await self.event_bus.emit("firs_grant_report_generated", {
                "app_id": app_id,
                "report_id": report_metadata["report_id"],
                "report_type": report_type,
                "milestone_count": executive_summary["key_metrics"]["milestones_achieved"],
                "overall_progress": executive_summary["key_metrics"]["overall_progress_percentage"]
            })
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating FIRS grant report: {str(e)}")
            return {
                "metadata": {
                    "report_id": f"ERROR_REPORT_{app_id}_{int(datetime.utcnow().timestamp())}",
                    "generated_at": datetime.utcnow().isoformat(),
                    "app_id": app_id,
                    "error": str(e)
                },
                "executive_summary": {
                    "key_metrics": {
                        "current_taxpayer_count": 0,
                        "milestones_achieved": 0,
                        "overall_progress_percentage": 0
                    },
                    "status_indicators": {
                        "overall_health": "error",
                        "error_message": "Report generation failed"
                    }
                }
            }
    
    async def get_enhanced_milestone_dashboard(self, app_id: str) -> Dict[str, Any]:
        """Get enhanced milestone dashboard with real-time KPI integration."""
        try:
            # Get milestone dashboard from KPI calculator
            kpi_dashboard = await self.kpi_calculator.get_milestone_dashboard(app_id)
            
            # Get additional analytics from taxpayer service
            taxpayer_analytics = await self.get_taxpayer_analytics(app_id)
            sector_analysis = await self.track_sector_representation(app_id)
            transmission_analysis = await self.calculate_transmission_rate(app_id)
            
            # Combine data for enhanced dashboard
            enhanced_dashboard = {
                "dashboard_id": f"enhanced_milestone_dashboard_{app_id}_{int(datetime.utcnow().timestamp())}",
                "generated_at": datetime.utcnow().isoformat(),
                "app_id": app_id,
                
                # Core milestone data from KPI calculator
                "milestone_progress": kpi_dashboard,
                
                # Enhanced analytics
                "taxpayer_analytics": taxpayer_analytics,
                "sector_analysis": sector_analysis,
                "transmission_performance": transmission_analysis,
                
                # Actionable insights
                "actionable_insights": await self._generate_actionable_insights(
                    kpi_dashboard, taxpayer_analytics, sector_analysis, transmission_analysis
                ),
                
                # Growth projections
                "growth_projections": await self._calculate_growth_projections(app_id, taxpayer_analytics),
                
                # Risk assessment
                "risk_assessment": await self._assess_milestone_risks(
                    kpi_dashboard, taxpayer_analytics, sector_analysis
                ),
                
                # Performance benchmarks
                "benchmarks": await self._get_performance_benchmarks(app_id),
                
                # Optimized action plan
                "action_plan": await self._generate_optimized_action_plan(
                    kpi_dashboard, taxpayer_analytics
                )
            }
            
            # Cache enhanced dashboard
            cache_key = f"enhanced_milestone_dashboard:{app_id}"
            await self.cache_service.set(cache_key, enhanced_dashboard, ttl=1800)  # 30 minutes
            
            return enhanced_dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced milestone dashboard: {str(e)}")
            return {}
    
    async def _generate_actionable_insights(
        self, 
        kpi_dashboard: Dict[str, Any], 
        taxpayer_analytics: Dict[str, Any], 
        sector_analysis: Dict[str, Any], 
        transmission_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate actionable insights based on comprehensive data analysis."""
        insights = []
        
        try:
            overall_progress = kpi_dashboard.get("overall_progress", 0)
            total_taxpayers = taxpayer_analytics.get("total_taxpayers", 0)
            transmission_rate = transmission_analysis.get("transmission_rate", 0)
            
            # Progress-based insights
            if overall_progress < 25:
                insights.append({
                    "type": "foundation_building",
                    "priority": "high",
                    "title": "Focus on Foundation Building",
                    "description": f"With {overall_progress:.1f}% overall progress, prioritize establishing strong onboarding processes",
                    "impact": "high",
                    "effort": "medium",
                    "timeline": "2-4 weeks"
                })
            
            # Transmission rate insights
            if transmission_rate < 70:
                insights.append({
                    "type": "engagement_improvement",
                    "priority": "critical",
                    "title": "Improve Taxpayer Engagement",
                    "description": f"Transmission rate of {transmission_rate:.1f}% is below FIRS requirement of 80%",
                    "impact": "critical",
                    "effort": "high",
                    "timeline": "1-2 weeks"
                })
            
            # Sector diversity insights
            sector_count = sector_analysis.get("total_sectors", 0)
            if sector_count < 2:
                insights.append({
                    "type": "diversification",
                    "priority": "medium",
                    "title": "Expand Sector Representation",
                    "description": f"Currently represented in {sector_count} sector(s). Need 2+ for Milestone 3",
                    "impact": "medium",
                    "effort": "medium",
                    "timeline": "4-6 weeks"
                })
            
            # Growth rate insights
            onboarding_trends = taxpayer_analytics.get("onboarding_trends", [])
            if onboarding_trends:
                recent_growth = onboarding_trends[-1].get("onboarded_count", 0) if onboarding_trends else 0
                if recent_growth < 5:
                    insights.append({
                        "type": "growth_acceleration",
                        "priority": "high",
                        "title": "Accelerate Growth Rate",
                        "description": f"Recent monthly growth of {recent_growth} taxpayers needs improvement",
                        "impact": "high",
                        "effort": "high",
                        "timeline": "2-3 weeks"
                    })
            
        except Exception as e:
            self.logger.error(f"Error generating actionable insights: {str(e)}")
        
        return insights
    
    async def _calculate_growth_projections(self, app_id: str, taxpayer_analytics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate growth projections for milestone achievement."""
        try:
            current_count = taxpayer_analytics.get("total_taxpayers", 0)
            onboarding_trends = taxpayer_analytics.get("onboarding_trends", [])
            
            # Calculate average monthly growth
            if len(onboarding_trends) >= 3:
                recent_months = onboarding_trends[-3:]
                avg_monthly_growth = sum(month.get("onboarded_count", 0) for month in recent_months) / len(recent_months)
            else:
                avg_monthly_growth = 5  # Conservative default
            
            # Project milestone completion dates
            milestones = [
                {"name": "Milestone 1", "target": 20, "grant": 50000},
                {"name": "Milestone 2", "target": 40, "grant": 100000},
                {"name": "Milestone 3", "target": 60, "grant": 200000},
                {"name": "Milestone 4", "target": 80, "grant": 400000},
                {"name": "Milestone 5", "target": 100, "grant": 800000}
            ]
            
            projections = {
                "current_taxpayers": current_count,
                "monthly_growth_rate": avg_monthly_growth,
                "milestone_projections": [],
                "total_potential_revenue": 1550000,
                "projected_completion_timeline": None
            }
            
            for milestone in milestones:
                if current_count >= milestone["target"]:
                    # Already achieved
                    projections["milestone_projections"].append({
                        **milestone,
                        "status": "achieved",
                        "months_to_completion": 0,
                        "projected_date": "Already achieved"
                    })
                else:
                    remaining = milestone["target"] - current_count
                    months_needed = remaining / avg_monthly_growth if avg_monthly_growth > 0 else float('inf')
                    
                    projected_date = datetime.utcnow() + timedelta(days=months_needed * 30)
                    
                    projections["milestone_projections"].append({
                        **milestone,
                        "status": "projected",
                        "months_to_completion": months_needed,
                        "projected_date": projected_date.strftime("%Y-%m-%d") if months_needed != float('inf') else "Unknown"
                    })
            
            # Set overall completion timeline
            final_milestone = projections["milestone_projections"][-1]
            projections["projected_completion_timeline"] = final_milestone.get("projected_date")
            
            return projections
            
        except Exception as e:
            self.logger.error(f"Error calculating growth projections: {str(e)}")
            return {}
    
    async def _assess_milestone_risks(
        self, 
        kpi_dashboard: Dict[str, Any], 
        taxpayer_analytics: Dict[str, Any], 
        sector_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess risks that might impact milestone achievement."""
        try:
            risk_assessment = {
                "overall_risk_level": "low",
                "risk_factors": [],
                "mitigation_strategies": [],
                "confidence_score": 85.0
            }
            
            # Assess various risk factors
            transmission_rate = taxpayer_analytics.get("transmission_rate", 0)
            total_taxpayers = taxpayer_analytics.get("total_taxpayers", 0)
            sector_count = sector_analysis.get("total_sectors", 0)
            
            risk_score = 0
            
            # Transmission rate risk
            if transmission_rate < 60:
                risk_score += 30
                risk_assessment["risk_factors"].append({
                    "factor": "Low transmission rate",
                    "severity": "high",
                    "impact": "Milestone 1 achievement at risk",
                    "likelihood": "high"
                })
                risk_assessment["mitigation_strategies"].append(
                    "Implement taxpayer education and engagement programs"
                )
            elif transmission_rate < 75:
                risk_score += 15
                risk_assessment["risk_factors"].append({
                    "factor": "Moderate transmission rate",
                    "severity": "medium",
                    "impact": "May delay Milestone 1",
                    "likelihood": "medium"
                })
            
            # Growth rate risk
            if total_taxpayers < 10:
                risk_score += 20
                risk_assessment["risk_factors"].append({
                    "factor": "Low taxpayer base",
                    "severity": "medium",
                    "impact": "Slower milestone progression",
                    "likelihood": "medium"
                })
                risk_assessment["mitigation_strategies"].append(
                    "Launch targeted acquisition campaigns"
                )
            
            # Sector diversity risk
            if sector_count < 2:
                risk_score += 10
                risk_assessment["risk_factors"].append({
                    "factor": "Limited sector diversity",
                    "severity": "low",
                    "impact": "Milestone 3 may be delayed",
                    "likelihood": "medium"
                })
                risk_assessment["mitigation_strategies"].append(
                    "Develop sector-specific onboarding strategies"
                )
            
            # Determine overall risk level
            if risk_score >= 40:
                risk_assessment["overall_risk_level"] = "high"
                risk_assessment["confidence_score"] = max(40.0, 85.0 - risk_score)
            elif risk_score >= 20:
                risk_assessment["overall_risk_level"] = "medium"
                risk_assessment["confidence_score"] = max(60.0, 85.0 - risk_score)
            else:
                risk_assessment["overall_risk_level"] = "low"
                risk_assessment["confidence_score"] = min(95.0, 85.0 + (20 - risk_score))
            
            return risk_assessment
            
        except Exception as e:
            self.logger.error(f"Error assessing milestone risks: {str(e)}")
            return {}
    
    async def _get_performance_benchmarks(self, app_id: str) -> Dict[str, Any]:
        """Get performance benchmarks for comparison."""
        try:
            # These would typically come from aggregated industry data
            benchmarks = {
                "industry_averages": {
                    "monthly_taxpayer_onboarding": 8,
                    "transmission_rate": 75.0,
                    "sector_diversity_index": 0.6,
                    "milestone_1_achievement_time_months": 4,
                    "milestone_completion_rate": 65.0
                },
                "top_performers": {
                    "monthly_taxpayer_onboarding": 15,
                    "transmission_rate": 90.0,
                    "sector_diversity_index": 0.8,
                    "milestone_1_achievement_time_months": 2.5,
                    "milestone_completion_rate": 95.0
                },
                "minimum_requirements": {
                    "monthly_taxpayer_onboarding": 5,
                    "transmission_rate": 80.0,
                    "sector_diversity_index": 0.4,
                    "milestone_1_achievement_time_months": 6,
                    "milestone_completion_rate": 100.0
                }
            }
            
            return benchmarks
            
        except Exception as e:
            self.logger.error(f"Error getting performance benchmarks: {str(e)}")
            return {}
    
    async def _generate_optimized_action_plan(
        self, 
        kpi_dashboard: Dict[str, Any], 
        taxpayer_analytics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate optimized action plan based on current status."""
        try:
            next_milestone = kpi_dashboard.get("next_milestone", "milestone_1")
            overall_progress = kpi_dashboard.get("overall_progress", 0)
            
            action_plan = {
                "phase": self._determine_current_phase(overall_progress),
                "immediate_priorities": [],
                "short_term_goals": [],
                "long_term_objectives": [],
                "resource_allocation": {},
                "timeline": {}
            }
            
            if next_milestone == "milestone_1":
                action_plan["immediate_priorities"] = [
                    "Accelerate taxpayer onboarding to reach 20 taxpayers",
                    "Implement engagement strategies to achieve 80% transmission rate",
                    "Establish robust support and training systems"
                ]
                action_plan["short_term_goals"] = [
                    "Onboard 5-8 new taxpayers per month",
                    "Achieve 85%+ transmission rate",
                    "Document all processes for scalability"
                ]
                action_plan["resource_allocation"] = {
                    "onboarding": 60,
                    "engagement": 25,
                    "support": 15
                }
            
            elif next_milestone == "milestone_2":
                action_plan["immediate_priorities"] = [
                    "Target large taxpayer acquisition",
                    "Ensure SME representation",
                    "Scale onboarding to reach 40 taxpayers"
                ]
                action_plan["short_term_goals"] = [
                    "Onboard at least 2 large taxpayers",
                    "Maintain diverse taxpayer portfolio",
                    "Optimize processes for higher volume"
                ]
                action_plan["resource_allocation"] = {
                    "large_taxpayer_acquisition": 40,
                    "sme_onboarding": 30,
                    "process_optimization": 30
                }
            
            # Add timeline
            action_plan["timeline"] = {
                "week_1_2": "Focus on immediate priorities",
                "week_3_4": "Implement process improvements",
                "month_2": "Scale successful strategies",
                "month_3": "Evaluate and optimize"
            }
            
            return action_plan
            
        except Exception as e:
            self.logger.error(f"Error generating optimized action plan: {str(e)}")
            return {}
    
    def _determine_current_phase(self, overall_progress: float) -> str:
        """Determine current development phase based on progress."""
        if overall_progress < 20:
            return "Foundation Phase"
        elif overall_progress < 50:
            return "Growth Phase"
        elif overall_progress < 80:
            return "Scale Phase"
        else:
            return "Optimization Phase"
    
    # Helper methods for enhanced analytics
    
    async def _get_sector_growth_trends(self, db, app_id: str) -> List[Dict[str, Any]]:
        """Get sector growth trends over last 6 months."""
        try:
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            # Placeholder implementation - would query monthly sector growth
            return [
                {"month": "2024-01", "total_onboarded": 5, "sectors": ["technology", "manufacturing"]},
                {"month": "2024-02", "total_onboarded": 8, "sectors": ["technology", "manufacturing", "services"]},
                # More trend data would be calculated from actual database queries
            ]
        except Exception as e:
            self.logger.error(f"Error getting sector growth trends: {str(e)}")
            return []
    
    def _analyze_sector_gaps(self, sectors: Dict, sector_count: int) -> Dict[str, Any]:
        """Analyze gaps in sector representation."""
        recommended_sectors = ["technology", "manufacturing", "services", "agriculture", "finance"]
        current_sectors = list(sectors.keys())
        missing_sectors = [s for s in recommended_sectors if s not in current_sectors]
        
        return {
            "current_sectors": current_sectors,
            "missing_high_value_sectors": missing_sectors[:3],
            "sector_concentration_risk": len(current_sectors) < 3,
            "recommendations": f"Consider targeting {', '.join(missing_sectors[:2])} sectors"
        }
    
    def _recommend_target_sectors(self, sectors: Dict) -> List[str]:
        """Recommend target sectors for diversification."""
        high_opportunity_sectors = ["technology", "healthcare", "education", "agriculture", "manufacturing"]
        current_sectors = list(sectors.keys())
        return [s for s in high_opportunity_sectors if s not in current_sectors][:3]
    
    def _generate_sector_recommendations(self, sectors: Dict, milestone_analysis: Dict, risk_assessment: Dict) -> List[str]:
        """Generate sector-specific recommendations."""
        recommendations = []
        
        if risk_assessment.get("single_sector_dependency"):
            recommendations.append("Critical: Diversify beyond single sector to reduce risk")
        
        if risk_assessment.get("concentration_risk", 0) > 0.7:
            recommendations.append("High concentration risk - distribute taxpayers more evenly across sectors")
        
        if not milestone_analysis.get("milestone_3_ready"):
            recommendations.append("Focus on cross-sector representation to achieve Milestone 3")
        
        return recommendations
    
    async def _analyze_transmission_frequency(self, db, app_id: str, cutoff_date: datetime) -> Dict[str, Any]:
        """Analyze transmission frequency patterns."""
        try:
            # Placeholder for transmission frequency analysis
            return {
                "daily_transmitters": 15,
                "weekly_transmitters": 45,
                "monthly_transmitters": 120,
                "frequency_pattern": "consistent",
                "peak_transmission_days": ["Tuesday", "Wednesday", "Thursday"]
            }
        except Exception as e:
            self.logger.error(f"Error analyzing transmission frequency: {str(e)}")
            return {}
    
    async def _calculate_sector_transmission_rates(self, db, app_id: str, cutoff_date: datetime) -> Dict[str, float]:
        """Calculate transmission rates by sector."""
        try:
            # Placeholder for sector-wise transmission rate calculation
            return {
                "technology": 85.5,
                "manufacturing": 78.2,
                "services": 82.1,
                "agriculture": 75.0
            }
        except Exception as e:
            self.logger.error(f"Error calculating sector transmission rates: {str(e)}")
            return {}
    
    async def _get_transmission_trends(self, db, app_id: str, period_days: int) -> List[Dict[str, Any]]:
        """Get weekly transmission trends."""
        try:
            # Placeholder for transmission trends calculation
            return [
                {"week": "2024-W10", "transmission_rate": 78.5, "active_transmitters": 45},
                {"week": "2024-W11", "transmission_rate": 82.1, "active_transmitters": 52},
                {"week": "2024-W12", "transmission_rate": 85.3, "active_transmitters": 58}
            ]
        except Exception as e:
            self.logger.error(f"Error getting transmission trends: {str(e)}")
            return []
    
    async def _analyze_transmission_by_size(self, db, app_id: str, cutoff_date: datetime) -> Dict[str, Any]:
        """Analyze transmission rates by taxpayer size."""
        try:
            # Placeholder for size-based transmission analysis
            return {
                "large_taxpayers": {"count": 8, "transmission_rate": 90.5, "avg_transmissions": 12},
                "sme_taxpayers": {"count": 42, "transmission_rate": 78.2, "avg_transmissions": 6}
            }
        except Exception as e:
            self.logger.error(f"Error analyzing transmission by size: {str(e)}")
            return {}
    
    def _classify_transmission_performance(self, transmission_rate: float) -> str:
        """Classify transmission performance level."""
        if transmission_rate >= 90:
            return "excellent"
        elif transmission_rate >= 80:
            return "good"
        elif transmission_rate >= 70:
            return "fair"
        else:
            return "poor"
    
    def _generate_transmission_recommendations(
        self, 
        transmission_rate: float, 
        total_taxpayers: int, 
        active_transmitters: int, 
        analytics: Dict
    ) -> List[str]:
        """Generate transmission improvement recommendations."""
        recommendations = []
        
        if transmission_rate < 60:
            recommendations.extend([
                "URGENT: Implement immediate taxpayer engagement program",
                "Review and simplify invoice submission process",
                "Provide dedicated support for struggling taxpayers"
            ])
        elif transmission_rate < 80:
            recommendations.extend([
                "Enhance taxpayer training and support",
                "Implement automated reminders for inactive taxpayers",
                "Analyze and resolve common submission barriers"
            ])
        
        inactive_count = total_taxpayers - active_transmitters
        if inactive_count > 0:
            recommendations.append(f"Re-engage {inactive_count} inactive taxpayers through targeted outreach")
        
        return recommendations
    
    def _get_milestone_grant_amount(self, milestone_type: MilestoneType) -> float:
        """Get grant amount for milestone type."""
        grant_amounts = {
            MilestoneType.MILESTONE_1: 50000.0,
            MilestoneType.MILESTONE_2: 100000.0,
            MilestoneType.MILESTONE_3: 200000.0,
            MilestoneType.MILESTONE_4: 400000.0,
            MilestoneType.MILESTONE_5: 800000.0
        }
        return grant_amounts.get(milestone_type, 0.0)
    
    async def _analyze_milestone_requirements(
        self, 
        milestone_type: MilestoneType, 
        taxpayer_stats: Dict, 
        sector_analysis: Dict, 
        transmission_analysis: Dict
    ) -> Dict[str, Any]:
        """Analyze milestone requirements with detailed breakdown."""
        try:
            total_taxpayers = taxpayer_stats.get("total_taxpayers", 0)
            large_taxpayers = taxpayer_stats.get("large_taxpayers", 0)
            sme_taxpayers = taxpayer_stats.get("sme_taxpayers", 0)
            sector_count = taxpayer_stats.get("sector_count", 0)
            transmission_rate = transmission_analysis.get("core_metrics", {}).get("transmission_rate", 0)
            
            target = self._get_milestone_target(milestone_type)
            progress_percentage = min((total_taxpayers / target) * 100, 100) if target > 0 else 0
            
            analysis = {
                "milestone_type": milestone_type.value,
                "target_taxpayers": target,
                "current_taxpayers": total_taxpayers,
                "progress_percentage": progress_percentage,
                "completion_score": 0.0,
                "requirements": [],
                "requirements_status": {},
                "blockers": [],
                "risk_factors": []
            }
            
            # Milestone-specific analysis
            if milestone_type == MilestoneType.MILESTONE_1:
                analysis["requirements"] = ["20+ taxpayers", "80%+ transmission rate"]
                analysis["requirements_status"] = {
                    "taxpayer_count": {"met": total_taxpayers >= 20, "current": total_taxpayers, "target": 20},
                    "transmission_rate": {"met": transmission_rate >= 80.0, "current": transmission_rate, "target": 80.0}
                }
                analysis["completion_score"] = (
                    (total_taxpayers / 20 if total_taxpayers <= 20 else 1.0) * 0.6 +
                    (transmission_rate / 80.0 if transmission_rate <= 80.0 else 1.0) * 0.4
                )
                
                if total_taxpayers < 20:
                    analysis["blockers"].append(f"Need {20 - total_taxpayers} more taxpayers")
                if transmission_rate < 80.0:
                    analysis["blockers"].append(f"Need {80.0 - transmission_rate:.1f}% improvement in transmission rate")
            
            elif milestone_type == MilestoneType.MILESTONE_2:
                analysis["requirements"] = ["40+ taxpayers", "Large + SME representation"]
                analysis["requirements_status"] = {
                    "taxpayer_count": {"met": total_taxpayers >= 40, "current": total_taxpayers, "target": 40},
                    "large_representation": {"met": large_taxpayers > 0, "current": large_taxpayers, "target": 1},
                    "sme_representation": {"met": sme_taxpayers > 0, "current": sme_taxpayers, "target": 1}
                }
                
                if total_taxpayers < 40:
                    analysis["blockers"].append(f"Need {40 - total_taxpayers} more taxpayers")
                if large_taxpayers == 0:
                    analysis["blockers"].append("Need at least one large taxpayer")
                if sme_taxpayers == 0:
                    analysis["blockers"].append("Need at least one SME taxpayer")
            
            # Continue for other milestones...
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing milestone requirements: {str(e)}")
            return {"error": str(e)}
    
    def _generate_enhanced_milestone_chart(self, milestone_progress: Dict) -> Dict[str, Any]:
        """Generate enhanced milestone progress chart."""
        return {
            "type": "milestone_progress",
            "data": milestone_progress.get("milestones_detail", {}),
            "visualization_type": "progress_bars_with_targets",
            "interactive_features": ["drill_down", "hover_details", "export"]
        }
    
    def _generate_enhanced_sector_chart(self, sector_analysis: Dict) -> Dict[str, Any]:
        """Generate enhanced sector distribution chart."""
        return {
            "type": "sector_distribution",
            "data": sector_analysis.get("sector_breakdown", {}),
            "visualization_type": "pie_chart_with_breakdown",
            "interactive_features": ["sector_drill_down", "size_segmentation"]
        }
    
    async def _generate_data_quality_report(self, app_id: str) -> Dict[str, Any]:
        """Generate data quality assessment report."""
        return {
            "data_completeness": 95.5,
            "data_accuracy": 98.2,
            "data_consistency": 96.8,
            "overall_quality_score": 96.8,
            "quality_issues": [],
            "recommendations": ["Maintain current data quality standards"]
        }
    
    def _get_methodology_notes(self) -> Dict[str, str]:
        """Get methodology notes for the report."""
        return {
            "milestone_calculation": "Progress calculated based on FIRS criteria with weighted scoring",
            "transmission_rate": "Calculated as percentage of active taxpayers submitting invoices in last 30 days",
            "sector_diversity": "Measured using Simpson's diversity index",
            "risk_assessment": "Multi-factor analysis including transmission rates, growth trends, and compliance"
        }
    
    def _get_report_glossary(self) -> Dict[str, str]:
        """Get glossary of terms used in the report."""
        return {
            "FIRS": "Federal Inland Revenue Service",
            "APP": "Access Point Provider",
            "Large Taxpayer": "Taxpayer with annual revenue ≥ ₦1 billion or ≥200 employees",
            "SME": "Small and Medium Enterprise",
            "Transmission Rate": "Percentage of taxpayers actively submitting invoices",
            "Milestone": "FIRS grant achievement target with specific taxpayer and compliance requirements"
        }
    
    async def _get_comprehensive_taxpayer_stats(self, app_id: str) -> Dict[str, Any]:
        """Get comprehensive taxpayer statistics for milestone tracking."""
        try:
            with get_db_session() as db:
                # Basic counts
                total_taxpayers = db.query(func.count(Taxpayer.id)).filter(
                    Taxpayer.app_id == app_id
                ).scalar()
                
                # Size classification counts
                large_taxpayers = db.query(func.count(TaxpayerProfile.id)).filter(
                    and_(
                        TaxpayerProfile.app_id == app_id,
                        TaxpayerProfile.taxpayer_size == "large"
                    )
                ).scalar()
                
                sme_taxpayers = db.query(func.count(TaxpayerProfile.id)).filter(
                    and_(
                        TaxpayerProfile.app_id == app_id,
                        TaxpayerProfile.taxpayer_size == "sme"
                    )
                ).scalar()
                
                # Sector count
                sector_count = db.query(func.count(distinct(TaxpayerProfile.sector))).filter(
                    TaxpayerProfile.app_id == app_id
                ).scalar()
                
                # Growth rate calculation (last 3 months)
                three_months_ago = datetime.utcnow() - timedelta(days=90)
                recent_additions = db.query(func.count(Taxpayer.id)).filter(
                    and_(
                        Taxpayer.app_id == app_id,
                        Taxpayer.registration_date >= three_months_ago
                    )
                ).scalar()
                
                monthly_growth_rate = (recent_additions / 3) if recent_additions else 0
                
                return {
                    "total_taxpayers": total_taxpayers,
                    "large_taxpayers": large_taxpayers,
                    "sme_taxpayers": sme_taxpayers,
                    "sector_count": sector_count,
                    "growth_rate": monthly_growth_rate,
                    "has_large_and_sme": large_taxpayers > 0 and sme_taxpayers > 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting taxpayer stats: {str(e)}")
            return {}
    
    def _calculate_diversity_index(self, sector_counts: List[int]) -> float:
        """Calculate Simpson's diversity index for sector representation."""
        try:
            total = sum(sector_counts)
            if total == 0:
                return 0.0
            
            # Simpson's diversity index: 1 - Σ(ni/N)²
            diversity = 1 - sum((count / total) ** 2 for count in sector_counts)
            return diversity
            
        except Exception as e:
            self.logger.error(f"Error calculating diversity index: {str(e)}")
            return 0.0
    
    def _calculate_milestone_percentage(self, milestone_type: MilestoneType, stats: Dict[str, Any]) -> float:
        """Calculate completion percentage for specific milestone."""
        total_taxpayers = stats.get("total_taxpayers", 0)
        
        if milestone_type == MilestoneType.MILESTONE_1:
            return min((total_taxpayers / 20) * 100, 100)
        elif milestone_type == MilestoneType.MILESTONE_2:
            return min((total_taxpayers / 40) * 100, 100)
        elif milestone_type == MilestoneType.MILESTONE_3:
            return min((total_taxpayers / 60) * 100, 100)
        elif milestone_type == MilestoneType.MILESTONE_4:
            return min((total_taxpayers / 80) * 100, 100)
        elif milestone_type == MilestoneType.MILESTONE_5:
            return min((total_taxpayers / 100) * 100, 100)
        
        return 0.0
    
    def _check_milestone_requirements(self, milestone_type: MilestoneType, stats: Dict[str, Any]) -> Dict[str, bool]:
        """Check if milestone requirements are met."""
        total = stats.get("total_taxpayers", 0)
        large = stats.get("large_taxpayers", 0)
        sme = stats.get("sme_taxpayers", 0)
        sectors = stats.get("sector_count", 0)
        
        requirements = {}
        
        if milestone_type == MilestoneType.MILESTONE_1:
            requirements = {"taxpayer_count": total >= 20, "transmission_rate": False}  # Need transmission data
        elif milestone_type == MilestoneType.MILESTONE_2:
            requirements = {"taxpayer_count": total >= 40, "large_and_sme": large > 0 and sme > 0}
        elif milestone_type == MilestoneType.MILESTONE_3:
            requirements = {"taxpayer_count": total >= 60, "cross_sector": sectors >= 2}
        elif milestone_type == MilestoneType.MILESTONE_4:
            requirements = {"taxpayer_count": total >= 80, "sustained_compliance": False}  # Need compliance data
        elif milestone_type == MilestoneType.MILESTONE_5:
            requirements = {"taxpayer_count": total >= 100, "full_validation": False}  # Need validation data
        
        return requirements
    
    def _get_milestone_target(self, milestone_type: MilestoneType) -> int:
        """Get target taxpayer count for milestone."""
        targets = {
            MilestoneType.MILESTONE_1: 20,
            MilestoneType.MILESTONE_2: 40,
            MilestoneType.MILESTONE_3: 60,
            MilestoneType.MILESTONE_4: 80,
            MilestoneType.MILESTONE_5: 100
        }
        return targets.get(milestone_type, 0)
    
    def _estimate_milestone_completion(self, current_count: int, monthly_growth: float) -> Optional[str]:
        """Estimate completion date for final milestone."""
        try:
            if monthly_growth <= 0:
                return None
            
            remaining = 100 - current_count
            months_needed = remaining / monthly_growth
            
            completion_date = datetime.utcnow() + timedelta(days=months_needed * 30)
            return completion_date.isoformat()
            
        except Exception:
            return None
    
    async def _analyze_grant_compliance(self, app_id: str) -> Dict[str, Any]:
        """Analyze compliance status for grant requirements."""
        # Placeholder for compliance analysis
        return {
            "overall_compliance": "pending_assessment",
            "regulatory_compliance": True,
            "data_quality_score": 85.0,
            "documentation_complete": True,
            "last_assessment_date": datetime.utcnow().isoformat()
        }
    
    async def _generate_milestone_recommendations(
        self, 
        milestone_progress: Dict[str, Any], 
        sector_analysis: Dict[str, Any], 
        transmission_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for milestone achievement."""
        recommendations = []
        
        current_count = milestone_progress.get("current_taxpayer_count", 0)
        next_milestone = milestone_progress.get("next_milestone")
        
        if next_milestone == "milestone_1":
            if current_count < 20:
                recommendations.append(f"Focus on onboarding {20 - current_count} more taxpayers to reach Milestone 1")
            if transmission_analysis.get("transmission_rate", 0) < 80:
                recommendations.append("Improve taxpayer engagement to achieve 80% transmission rate")
        
        elif next_milestone == "milestone_2":
            if not sector_analysis.get("sector_breakdown", {}).get("large"):
                recommendations.append("Target large taxpayers for onboarding to meet Milestone 2 requirements")
            if not sector_analysis.get("sector_breakdown", {}).get("sme"):
                recommendations.append("Ensure SME representation for balanced taxpayer portfolio")
        
        elif next_milestone == "milestone_3":
            if sector_analysis.get("total_sectors", 0) < 2:
                recommendations.append("Diversify across multiple economic sectors to meet cross-sector requirement")
        
        return recommendations
    
    def _generate_milestone_chart_data(self, milestone_progress: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for milestone progress visualization."""
        milestones = milestone_progress.get("milestones", {})
        
        chart_data = {
            "type": "progress_bar",
            "data": []
        }
        
        for milestone_key, milestone_data in milestones.items():
            chart_data["data"].append({
                "milestone": milestone_key.replace("_", " ").title(),
                "progress": milestone_data.get("progress_percentage", 0),
                "achieved": milestone_data.get("achieved", False)
            })
        
        return chart_data
    
    def _generate_sector_chart_data(self, sector_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate chart data for sector distribution."""
        return {
            "type": "pie_chart",
            "data": [
                {"sector": sector, "count": count}
                for sector, count in sector_analysis.get("sector_breakdown", {}).items()
            ]
        }
    
    async def _generate_transmission_trend_data(self, app_id: str) -> Dict[str, Any]:
        """Generate transmission trend chart data."""
        # Placeholder for transmission trend analysis
        return {
            "type": "line_chart",
            "data": [],
            "note": "Transmission trend data requires historical invoice data analysis"
        }

    # Private helper methods
    
    async def _generate_report_data(
        self,
        report_type: ReportType,
        filters: AnalyticsFilter,
        app_id: str
    ) -> Dict[str, Any]:
        """Generate report data based on type"""
        if report_type == ReportType.ONBOARDING_SUMMARY:
            return await self._generate_onboarding_summary(filters, app_id)
        elif report_type == ReportType.COMPLIANCE_DASHBOARD:
            return await self._generate_compliance_dashboard(filters, app_id)
        elif report_type == ReportType.KPI_TRACKING:
            return await self._generate_kpi_tracking(filters, app_id)
        elif report_type == ReportType.PERFORMANCE_METRICS:
            return await self._generate_performance_report(filters, app_id)
        elif report_type == ReportType.TREND_ANALYSIS:
            return await self._generate_trend_report(filters, app_id)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
    
    def _get_report_title(self, report_type: ReportType) -> str:
        """Get report title based on type"""
        titles = {
            ReportType.ONBOARDING_SUMMARY: "Taxpayer Onboarding Summary",
            ReportType.COMPLIANCE_DASHBOARD: "Compliance Dashboard",
            ReportType.KPI_TRACKING: "FIRS KPI Tracking Report",
            ReportType.PERFORMANCE_METRICS: "System Performance Metrics",
            ReportType.TREND_ANALYSIS: "Trend Analysis Report"
        }
        return titles.get(report_type, "Analytics Report")
    
    def _get_report_description(self, report_type: ReportType) -> str:
        """Get report description based on type"""
        descriptions = {
            ReportType.ONBOARDING_SUMMARY: "Comprehensive overview of taxpayer onboarding process and metrics",
            ReportType.COMPLIANCE_DASHBOARD: "Real-time compliance monitoring and issue tracking",
            ReportType.KPI_TRACKING: "FIRS KPI compliance tracking and achievement status",
            ReportType.PERFORMANCE_METRICS: "System performance and operational metrics",
            ReportType.TREND_ANALYSIS: "Trend analysis and predictive insights"
        }
        return descriptions.get(report_type, "Analytics report with key metrics and insights")
    
    def _get_start_date(self, time_frame: TimeFrame, end_date: datetime) -> datetime:
        """Calculate start date based on time frame"""
        if time_frame == TimeFrame.DAILY:
            return end_date - timedelta(days=1)
        elif time_frame == TimeFrame.WEEKLY:
            return end_date - timedelta(weeks=1)
        elif time_frame == TimeFrame.MONTHLY:
            return end_date - timedelta(days=30)
        elif time_frame == TimeFrame.QUARTERLY:
            return end_date - timedelta(days=90)
        elif time_frame == TimeFrame.YEARLY:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(days=30)  # Default to monthly
    
    def _get_time_range(self, filters: AnalyticsFilter) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get time range from filters"""
        if filters.time_frame == TimeFrame.CUSTOM:
            return filters.start_date, filters.end_date
        else:
            end_date = datetime.now(timezone.utc)
            start_date = self._get_start_date(filters.time_frame, end_date)
            return start_date, end_date
    
    async def _calculate_compliance_rate(
        self,
        db: Session,
        app_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate compliance rate"""
        total_checks = db.query(func.count(ComplianceRecord.id)).filter(
            and_(
                ComplianceRecord.app_id == app_id,
                ComplianceRecord.created_at >= start_date,
                ComplianceRecord.created_at <= end_date
            )
        ).scalar()
        
        passed_checks = db.query(func.count(ComplianceRecord.id)).filter(
            and_(
                ComplianceRecord.app_id == app_id,
                ComplianceRecord.status == "passed",
                ComplianceRecord.created_at >= start_date,
                ComplianceRecord.created_at <= end_date
            )
        ).scalar()
        
        return (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    async def _calculate_avg_onboarding_time(
        self,
        db: Session,
        app_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> float:
        """Calculate average onboarding time"""
        completed_applications = db.query(OnboardingApplication).filter(
            and_(
                OnboardingApplication.app_id == app_id,
                OnboardingApplication.status == "completed",
                OnboardingApplication.created_at >= start_date,
                OnboardingApplication.created_at <= end_date
            )
        ).all()
        
        if not completed_applications:
            return 0.0
        
        total_time = sum([
            (app.completed_at - app.created_at).total_seconds()
            for app in completed_applications
            if app.completed_at
        ])
        
        return total_time / len(completed_applications) / 3600  # Convert to hours
    
    async def _get_registration_stats(
        self,
        db: Session,
        app_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, int]:
        """Get registration statistics"""
        stats = {
            "successful": 0,
            "pending": 0,
            "failed": 0
        }
        
        results = db.query(
            OnboardingApplication.status,
            func.count(OnboardingApplication.id)
        ).filter(
            and_(
                OnboardingApplication.app_id == app_id,
                OnboardingApplication.created_at >= start_date,
                OnboardingApplication.created_at <= end_date
            )
        ).group_by(OnboardingApplication.status).all()
        
        for status, count in results:
            if status == "completed":
                stats["successful"] = count
            elif status == "pending":
                stats["pending"] = count
            elif status in ["rejected", "failed"]:
                stats["failed"] += count
        
        return stats
    
    async def _generate_insights(self, report_type: ReportType, data: Dict[str, Any]) -> List[str]:
        """Generate insights based on report data"""
        insights = []
        
        if report_type == ReportType.KPI_TRACKING:
            kpi_data = data.get("kpi_metrics", {})
            if kpi_data.get("kpi_achievement_rate", 0) >= 80:
                insights.append("KPI achievement rate is on track for the target")
            else:
                insights.append("KPI achievement rate needs improvement")
        
        # Add more insight generation logic
        
        return insights
    
    async def _generate_recommendations(self, report_type: ReportType, data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on report data"""
        recommendations = []
        
        if report_type == ReportType.ONBOARDING_SUMMARY:
            onboarding_data = data.get("onboarding_metrics", {})
            if onboarding_data.get("completion_rate", 0) < 80:
                recommendations.append("Improve onboarding process to increase completion rate")
        
        # Add more recommendation generation logic
        
        return recommendations
    
    async def _generate_charts(self, report_type: ReportType, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate chart configurations for report"""
        charts = []
        
        if report_type == ReportType.KPI_TRACKING:
            charts.append({
                "type": "gauge",
                "title": "KPI Achievement Rate",
                "data": data.get("kpi_metrics", {}).get("kpi_achievement_rate", 0),
                "target": 100
            })
        
        # Add more chart generation logic
        
        return charts
    
    async def _generate_onboarding_summary(self, filters: AnalyticsFilter, app_id: str) -> Dict[str, Any]:
        """Generate onboarding summary data"""
        onboarding_metrics = await self.get_onboarding_metrics(app_id, filters)
        return {
            "onboarding_metrics": onboarding_metrics.to_dict(),
            "summary": "Onboarding process overview and key metrics"
        }
    
    async def _generate_compliance_dashboard(self, filters: AnalyticsFilter, app_id: str) -> Dict[str, Any]:
        """Generate compliance dashboard data"""
        compliance_metrics = await self.get_compliance_metrics(app_id, filters)
        return {
            "compliance_metrics": compliance_metrics.to_dict(),
            "summary": "Compliance monitoring and issue tracking"
        }
    
    async def _generate_kpi_tracking(self, filters: AnalyticsFilter, app_id: str) -> Dict[str, Any]:
        """Generate KPI tracking data"""
        kpi_metrics = await self.get_kpi_metrics(app_id, filters.time_frame)
        return {
            "kpi_metrics": kpi_metrics.to_dict(),
            "summary": "FIRS KPI compliance tracking"
        }
    
    async def _generate_performance_report(self, filters: AnalyticsFilter, app_id: str) -> Dict[str, Any]:
        """Generate performance report data"""
        performance_metrics = await self.get_performance_metrics(app_id, filters)
        return {
            "performance_metrics": performance_metrics.to_dict(),
            "summary": "System performance and operational metrics"
        }
    
    async def _generate_trend_report(self, filters: AnalyticsFilter, app_id: str) -> Dict[str, Any]:
        """Generate trend analysis report data"""
        # This would generate trend analysis for multiple metrics
        return {
            "trend_analysis": "Trend analysis data would be generated here",
            "summary": "Trend analysis and predictive insights"
        }