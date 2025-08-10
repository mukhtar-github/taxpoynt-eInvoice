"""
Hybrid Service: KPI Calculator
Calculates unified KPIs across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics
import math

from core_platform.database import get_db_session
from core_platform.models.kpi import KPIDefinition, KPICalculation, KPITarget, KPIHistory
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

from .unified_metrics import UnifiedMetrics, MetricScope, MetricType, AggregatedMetric

logger = logging.getLogger(__name__)


class KPICategory(str, Enum):
    """KPI categories"""
    FINANCIAL = "financial"
    OPERATIONAL = "operational"
    QUALITY = "quality"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    CUSTOMER = "customer"
    BUSINESS = "business"
    TECHNICAL = "technical"


class KPIType(str, Enum):
    """KPI types"""
    RATIO = "ratio"
    PERCENTAGE = "percentage"
    COUNT = "count"
    AVERAGE = "average"
    RATE = "rate"
    SCORE = "score"
    INDEX = "index"
    TREND = "trend"


class KPIStatus(str, Enum):
    """KPI status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class KPITrend(str, Enum):
    """KPI trend direction"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    UNKNOWN = "unknown"


class KPIFrequency(str, Enum):
    """KPI calculation frequency"""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


@dataclass
class KPIDefinition:
    """KPI definition with calculation logic"""
    kpi_id: str
    name: str
    description: str
    category: KPICategory
    kpi_type: KPIType
    calculation_method: str
    source_metrics: List[str]
    calculation_formula: str
    unit: str
    target_value: Optional[float]
    thresholds: Dict[str, float]
    frequency: KPIFrequency
    is_higher_better: bool
    tags: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KPITarget:
    """KPI target with time period"""
    target_id: str
    kpi_id: str
    target_value: float
    target_period: str
    target_type: str  # absolute, percentage, improvement
    set_by: str
    set_date: datetime
    effective_date: datetime
    expiry_date: Optional[datetime]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KPICalculation:
    """KPI calculation result"""
    calculation_id: str
    kpi_id: str
    calculated_value: float
    calculation_time: datetime
    calculation_period: str
    source_data: Dict[str, Any]
    status: KPIStatus
    trend: KPITrend
    target_comparison: Dict[str, Any]
    confidence_level: float
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KPIInsight:
    """KPI insight and recommendation"""
    insight_id: str
    kpi_id: str
    insight_type: str
    title: str
    description: str
    severity: str
    recommendations: List[str]
    impact_assessment: Dict[str, Any]
    generated_time: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KPIDashboard:
    """KPI dashboard with multiple KPIs"""
    dashboard_id: str
    name: str
    description: str
    kpi_calculations: List[KPICalculation]
    summary: Dict[str, Any]
    insights: List[KPIInsight]
    generated_time: datetime
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class KPICalculator:
    """
    KPI Calculator service
    Calculates unified KPIs across SI and APP roles
    """
    
    def __init__(self, unified_metrics: UnifiedMetrics = None):
        """Initialize KPI calculator service"""
        self.unified_metrics = unified_metrics or UnifiedMetrics()
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.kpi_definitions: Dict[str, KPIDefinition] = {}
        self.kpi_targets: Dict[str, List[KPITarget]] = {}
        self.kpi_calculators: Dict[str, Callable] = {}
        self.calculation_history: Dict[str, List[KPICalculation]] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 300  # 5 minutes
        self.max_history_size = 1000
        self.calculation_interval = 60  # 1 minute
        
        # Initialize default KPIs
        self._initialize_default_kpis()
        self._initialize_kpi_calculators()
    
    def _initialize_default_kpis(self):
        """Initialize default KPI definitions"""
        default_kpis = [
            # Financial KPIs
            KPIDefinition(
                kpi_id="revenue_per_transaction",
                name="Revenue per Transaction",
                description="Average revenue generated per transaction",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.AVERAGE,
                calculation_method="division",
                source_metrics=["total_revenue", "total_transactions"],
                calculation_formula="total_revenue / total_transactions",
                unit="currency",
                target_value=50.0,
                thresholds={"excellent": 60, "good": 50, "fair": 40, "poor": 30},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["financial", "revenue", "transactions"]
            ),
            
            # Operational KPIs
            KPIDefinition(
                kpi_id="system_efficiency",
                name="System Efficiency",
                description="Overall system efficiency across SI and APP",
                category=KPICategory.OPERATIONAL,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="weighted_average",
                source_metrics=["si_efficiency", "app_efficiency", "cross_role_success_rate"],
                calculation_formula="weighted_average(si_efficiency, app_efficiency, cross_role_success_rate)",
                unit="percentage",
                target_value=95.0,
                thresholds={"excellent": 98, "good": 95, "fair": 90, "poor": 85},
                frequency=KPIFrequency.HOURLY,
                is_higher_better=True,
                tags=["operational", "efficiency", "performance"]
            ),
            
            # Quality KPIs
            KPIDefinition(
                kpi_id="data_quality_score",
                name="Data Quality Score",
                description="Overall data quality across the platform",
                category=KPICategory.QUALITY,
                kpi_type=KPIType.SCORE,
                calculation_method="composite",
                source_metrics=["data_accuracy", "data_completeness", "data_consistency"],
                calculation_formula="(data_accuracy * 0.4) + (data_completeness * 0.3) + (data_consistency * 0.3)",
                unit="score",
                target_value=90.0,
                thresholds={"excellent": 95, "good": 90, "fair": 85, "poor": 80},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["quality", "data", "accuracy"]
            ),
            
            # Performance KPIs
            KPIDefinition(
                kpi_id="response_time_sla",
                name="Response Time SLA",
                description="Percentage of requests meeting SLA response times",
                category=KPICategory.PERFORMANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="sla_calculation",
                source_metrics=["response_times", "sla_threshold"],
                calculation_formula="(requests_under_sla / total_requests) * 100",
                unit="percentage",
                target_value=99.0,
                thresholds={"excellent": 99.5, "good": 99.0, "fair": 98.0, "poor": 95.0},
                frequency=KPIFrequency.HOURLY,
                is_higher_better=True,
                tags=["performance", "sla", "response_time"]
            ),
            
            # Compliance KPIs
            KPIDefinition(
                kpi_id="regulatory_compliance_rate",
                name="Regulatory Compliance Rate",
                description="Percentage of processes meeting regulatory requirements",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="compliance_rate",
                source_metrics=["compliant_processes", "total_processes"],
                calculation_formula="(compliant_processes / total_processes) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 98, "fair": 95, "poor": 90},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["compliance", "regulatory", "processes"]
            ),
            
            # FIRS Grant Milestone KPIs
            KPIDefinition(
                kpi_id="firs_milestone_1_progress",
                name="FIRS Milestone 1: 20 Taxpayers (80% Active)",
                description="Progress towards FIRS Milestone 1: 20 taxpayers with 80% transmission rate",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_calculation",
                source_metrics=["taxpayer_count", "transmission_rate"],
                calculation_formula="(taxpayer_count >= 20 AND transmission_rate >= 80) ? 100 : (taxpayer_count/20) * (transmission_rate/80) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 80, "fair": 60, "poor": 40},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["firs", "milestone", "app", "grant", "taxpayers"],
                metadata={"milestone_type": "milestone_1", "grant_amount": 50000, "requirements": {"taxpayer_count": 20, "transmission_rate": 80}}
            ),
            
            KPIDefinition(
                kpi_id="firs_milestone_2_progress",
                name="FIRS Milestone 2: 40 Taxpayers (Large + SME)",
                description="Progress towards FIRS Milestone 2: 40 taxpayers with Large + SME representation",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_calculation",
                source_metrics=["taxpayer_count", "large_taxpayer_count", "sme_taxpayer_count"],
                calculation_formula="(taxpayer_count >= 40 AND large_taxpayer_count > 0 AND sme_taxpayer_count > 0) ? 100 : (taxpayer_count/40) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 80, "fair": 60, "poor": 40},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["firs", "milestone", "app", "grant", "taxpayers", "large", "sme"],
                metadata={"milestone_type": "milestone_2", "grant_amount": 100000, "requirements": {"taxpayer_count": 40, "large_taxpayers": True, "sme_taxpayers": True}}
            ),
            
            KPIDefinition(
                kpi_id="firs_milestone_3_progress",
                name="FIRS Milestone 3: 60 Taxpayers (Cross-Sector)",
                description="Progress towards FIRS Milestone 3: 60 taxpayers with cross-sector representation",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_calculation",
                source_metrics=["taxpayer_count", "sector_count"],
                calculation_formula="(taxpayer_count >= 60 AND sector_count >= 2) ? 100 : (taxpayer_count/60) * (sector_count/2) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 80, "fair": 60, "poor": 40},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["firs", "milestone", "app", "grant", "taxpayers", "sectors"],
                metadata={"milestone_type": "milestone_3", "grant_amount": 200000, "requirements": {"taxpayer_count": 60, "sector_count": 2}}
            ),
            
            KPIDefinition(
                kpi_id="firs_milestone_4_progress",
                name="FIRS Milestone 4: 80 Taxpayers (Sustained Compliance)",
                description="Progress towards FIRS Milestone 4: 80 taxpayers with sustained compliance",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_calculation",
                source_metrics=["taxpayer_count", "compliance_sustained"],
                calculation_formula="(taxpayer_count >= 80 AND compliance_sustained = true) ? 100 : (taxpayer_count/80) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 80, "fair": 60, "poor": 40},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["firs", "milestone", "app", "grant", "taxpayers", "compliance"],
                metadata={"milestone_type": "milestone_4", "grant_amount": 400000, "requirements": {"taxpayer_count": 80, "compliance_sustained": True}}
            ),
            
            KPIDefinition(
                kpi_id="firs_milestone_5_progress",
                name="FIRS Milestone 5: 100 Taxpayers (Full Validation)",
                description="Progress towards FIRS Milestone 5: 100 taxpayers with full validation",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_calculation",
                source_metrics=["taxpayer_count", "full_validation_completed"],
                calculation_formula="(taxpayer_count >= 100 AND full_validation_completed = true) ? 100 : (taxpayer_count/100) * 100",
                unit="percentage",
                target_value=100.0,
                thresholds={"excellent": 100, "good": 80, "fair": 60, "poor": 40},
                frequency=KPIFrequency.DAILY,
                is_higher_better=True,
                tags=["firs", "milestone", "app", "grant", "taxpayers", "validation"],
                metadata={"milestone_type": "milestone_5", "grant_amount": 800000, "requirements": {"taxpayer_count": 100, "full_validation": True}}
            ),
            
            # SI Commercial Billing KPIs
            KPIDefinition(
                kpi_id="si_revenue_growth",
                name="SI Revenue Growth Rate",
                description="Monthly revenue growth rate for SI commercial subscriptions",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="growth_rate",
                source_metrics=["current_month_revenue", "previous_month_revenue"],
                calculation_formula="((current_month_revenue - previous_month_revenue) / previous_month_revenue) * 100",
                unit="percentage",
                target_value=15.0,
                thresholds={"excellent": 20, "good": 15, "fair": 10, "poor": 5},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["si", "revenue", "growth", "commercial", "billing"]
            ),
            
            KPIDefinition(
                kpi_id="si_customer_churn_rate",
                name="SI Customer Churn Rate",
                description="Monthly churn rate for SI commercial customers",
                category=KPICategory.CUSTOMER,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="churn_rate",
                source_metrics=["churned_customers", "total_customers_start_month"],
                calculation_formula="(churned_customers / total_customers_start_month) * 100",
                unit="percentage",
                target_value=2.0,
                thresholds={"excellent": 1, "good": 2, "fair": 5, "poor": 10},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=False,
                tags=["si", "churn", "customers", "commercial", "retention"]
            ),
            
            KPIDefinition(
                kpi_id="si_average_revenue_per_user",
                name="SI Average Revenue Per User (ARPU)",
                description="Average revenue per user for SI commercial customers",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.AVERAGE,
                calculation_method="division",
                source_metrics=["total_si_revenue", "total_si_customers"],
                calculation_formula="total_si_revenue / total_si_customers",
                unit="currency",
                target_value=300.0,
                thresholds={"excellent": 500, "good": 300, "fair": 200, "poor": 100},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["si", "arpu", "revenue", "commercial", "customers"]
            ),
            
            # Unified Revenue KPIs (Phase 4 Implementation)
            KPIDefinition(
                kpi_id="total_revenue",
                name="Total Revenue",
                description="SI + APP grant revenue combined across the platform",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.COUNT,
                calculation_method="addition",
                source_metrics=["si_revenue", "app_grant_revenue"],
                calculation_formula="si_revenue + app_grant_revenue",
                unit="currency",
                target_value=1000000.0,
                thresholds={"excellent": 1500000, "good": 1000000, "fair": 750000, "poor": 500000},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["revenue", "unified", "si", "app", "grants", "total"]
            ),
            
            KPIDefinition(
                kpi_id="si_revenue_contribution",
                name="SI Revenue Contribution",
                description="Percentage contribution from SI subscriptions to total revenue",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="si_contribution_percentage",
                source_metrics=["si_revenue", "app_grant_revenue"],
                calculation_formula="(si_revenue / (si_revenue + app_grant_revenue)) * 100",
                unit="percentage",
                target_value=60.0,
                thresholds={"excellent": 70, "good": 60, "fair": 50, "poor": 40},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["revenue", "si", "contribution", "percentage", "commercial"]
            ),
            
            KPIDefinition(
                kpi_id="app_grant_contribution",
                name="APP Grant Contribution",
                description="Percentage contribution from FIRS grants to total revenue",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="app_contribution_percentage",
                source_metrics=["si_revenue", "app_grant_revenue"],
                calculation_formula="(app_grant_revenue / (si_revenue + app_grant_revenue)) * 100",
                unit="percentage",
                target_value=40.0,
                thresholds={"excellent": 30, "good": 40, "fair": 50, "poor": 60},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=False,
                tags=["revenue", "app", "grants", "contribution", "percentage"]
            ),
            
            KPIDefinition(
                kpi_id="customer_acquisition_cost",
                name="Customer Acquisition Cost",
                description="SI customer acquisition cost analysis",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.AVERAGE,
                calculation_method="cac_calculation",
                source_metrics=["marketing_spend", "sales_spend", "new_customers_acquired"],
                calculation_formula="(marketing_spend + sales_spend) / new_customers_acquired",
                unit="currency",
                target_value=500.0,
                thresholds={"excellent": 300, "good": 500, "fair": 800, "poor": 1200},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=False,
                tags=["cac", "acquisition", "si", "customers", "cost"]
            ),
            
            KPIDefinition(
                kpi_id="grant_roi",
                name="Grant ROI",
                description="APP grant return on investment analysis",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.RATIO,
                calculation_method="grant_roi_calculation",
                source_metrics=["total_grants_received", "app_operational_costs", "taxpayer_onboarding_value"],
                calculation_formula="((total_grants_received + taxpayer_onboarding_value) - app_operational_costs) / app_operational_costs * 100",
                unit="percentage",
                target_value=200.0,
                thresholds={"excellent": 300, "good": 200, "fair": 150, "poor": 100},
                frequency=KPIFrequency.QUARTERLY,
                is_higher_better=True,
                tags=["roi", "grants", "app", "investment", "return"]
            ),
            
            KPIDefinition(
                kpi_id="revenue_per_user",
                name="Revenue Per User",
                description="Average revenue per user across all platform users",
                category=KPICategory.FINANCIAL,
                kpi_type=KPIType.AVERAGE,
                calculation_method="unified_rpu_calculation",
                source_metrics=["total_revenue", "total_active_users", "si_users", "app_taxpayers"],
                calculation_formula="total_revenue / (si_users + app_taxpayers)",
                unit="currency",
                target_value=250.0,
                thresholds={"excellent": 400, "good": 250, "fair": 150, "poor": 100},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["rpu", "revenue", "users", "average", "unified"]
            ),
            
            KPIDefinition(
                kpi_id="churn_rate_si",
                name="SI Customer Churn Rate",
                description="SI customer churn rate monitoring",
                category=KPICategory.CUSTOMER,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="churn_rate",
                source_metrics=["churned_si_customers", "total_si_customers_start_month"],
                calculation_formula="(churned_si_customers / total_si_customers_start_month) * 100",
                unit="percentage",
                target_value=2.0,
                thresholds={"excellent": 1, "good": 2, "fair": 5, "poor": 10},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=False,
                tags=["churn", "si", "customers", "retention", "commercial"]
            ),
            
            KPIDefinition(
                kpi_id="milestone_achievement_rate",
                name="Milestone Achievement Rate",
                description="APP milestone success rate tracking",
                category=KPICategory.COMPLIANCE,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="milestone_achievement_calculation",
                source_metrics=["milestones_achieved", "milestones_attempted", "milestone_timeline_performance"],
                calculation_formula="(milestones_achieved / milestones_attempted) * 100",
                unit="percentage",
                target_value=80.0,
                thresholds={"excellent": 90, "good": 80, "fair": 70, "poor": 60},
                frequency=KPIFrequency.QUARTERLY,
                is_higher_better=True,
                tags=["milestones", "achievement", "app", "grants", "success"]
            ),

            # Customer KPIs
            KPIDefinition(
                kpi_id="customer_satisfaction_index",
                name="Customer Satisfaction Index",
                description="Overall customer satisfaction with the platform",
                category=KPICategory.CUSTOMER,
                kpi_type=KPIType.INDEX,
                calculation_method="satisfaction_index",
                source_metrics=["satisfaction_ratings", "response_times", "error_rates"],
                calculation_formula="satisfaction_index(satisfaction_ratings, response_times, error_rates)",
                unit="index",
                target_value=4.5,
                thresholds={"excellent": 4.8, "good": 4.5, "fair": 4.0, "poor": 3.5},
                frequency=KPIFrequency.WEEKLY,
                is_higher_better=True,
                tags=["customer", "satisfaction", "service"]
            ),
            
            # Business KPIs
            KPIDefinition(
                kpi_id="platform_growth_rate",
                name="Platform Growth Rate",
                description="Rate of platform adoption and usage growth",
                category=KPICategory.BUSINESS,
                kpi_type=KPIType.RATE,
                calculation_method="growth_rate",
                source_metrics=["current_users", "previous_users", "transaction_volume"],
                calculation_formula="((current_period - previous_period) / previous_period) * 100",
                unit="percentage",
                target_value=15.0,
                thresholds={"excellent": 20, "good": 15, "fair": 10, "poor": 5},
                frequency=KPIFrequency.MONTHLY,
                is_higher_better=True,
                tags=["business", "growth", "adoption"]
            ),
            
            # Technical KPIs
            KPIDefinition(
                kpi_id="system_availability",
                name="System Availability",
                description="Percentage of time the system is available",
                category=KPICategory.TECHNICAL,
                kpi_type=KPIType.PERCENTAGE,
                calculation_method="availability",
                source_metrics=["uptime", "total_time"],
                calculation_formula="(uptime / total_time) * 100",
                unit="percentage",
                target_value=99.9,
                thresholds={"excellent": 99.95, "good": 99.9, "fair": 99.5, "poor": 99.0},
                frequency=KPIFrequency.HOURLY,
                is_higher_better=True,
                tags=["technical", "availability", "uptime"]
            )
        ]
        
        for kpi_def in default_kpis:
            self.kpi_definitions[kpi_def.kpi_id] = kpi_def
    
    def _initialize_kpi_calculators(self):
        """Initialize KPI calculation methods"""
        self.kpi_calculators = {
            "division": self._calculate_division,
            "weighted_average": self._calculate_weighted_average,
            "composite": self._calculate_composite,
            "sla_calculation": self._calculate_sla,
            "compliance_rate": self._calculate_compliance_rate,
            "satisfaction_index": self._calculate_satisfaction_index,
            "growth_rate": self._calculate_growth_rate,
            "availability": self._calculate_availability,
            "milestone_calculation": self._calculate_milestone_calculation,
            "addition": self._calculate_addition,
            "ratio": self._calculate_ratio,
            "churn_rate": self._calculate_churn_rate,
            # Phase 4 Unified Revenue KPI Calculators
            "si_contribution_percentage": self._calculate_si_contribution_percentage,
            "app_contribution_percentage": self._calculate_app_contribution_percentage,
            "cac_calculation": self._calculate_cac,
            "grant_roi_calculation": self._calculate_grant_roi,
            "unified_rpu_calculation": self._calculate_unified_rpu,
            "milestone_achievement_calculation": self._calculate_milestone_achievement_rate
        }
    
    async def initialize(self):
        """Initialize the KPI calculator service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing KPI calculator service")
        
        try:
            # Initialize dependencies
            await self.unified_metrics.initialize()
            await self.cache.initialize()
            
            # Start periodic calculation
            asyncio.create_task(self._periodic_calculation())
            
            # Register event handlers
            await self._register_event_handlers()
            
            self.is_initialized = True
            self.logger.info("KPI calculator service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing KPI calculator service: {str(e)}")
            raise
    
    async def register_kpi_definition(self, kpi_definition: KPIDefinition):
        """Register a new KPI definition"""
        try:
            self.kpi_definitions[kpi_definition.kpi_id] = kpi_definition
            
            # Cache the definition
            await self.cache.set(
                f"kpi_def:{kpi_definition.kpi_id}",
                kpi_definition.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Registered KPI definition: {kpi_definition.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering KPI definition: {str(e)}")
            raise
    
    async def set_kpi_target(self, kpi_target: KPITarget):
        """Set a target for a KPI"""
        try:
            if kpi_target.kpi_id not in self.kpi_targets:
                self.kpi_targets[kpi_target.kpi_id] = []
            
            self.kpi_targets[kpi_target.kpi_id].append(kpi_target)
            
            # Cache the target
            await self.cache.set(
                f"kpi_target:{kpi_target.target_id}",
                kpi_target.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Set KPI target: {kpi_target.kpi_id} = {kpi_target.target_value}")
            
        except Exception as e:
            self.logger.error(f"Error setting KPI target: {str(e)}")
            raise
    
    async def calculate_kpi(
        self,
        kpi_id: str,
        time_range: Tuple[datetime, datetime],
        calculation_period: str = "current"
    ) -> KPICalculation:
        """Calculate a specific KPI"""
        try:
            if kpi_id not in self.kpi_definitions:
                raise ValueError(f"KPI definition not found: {kpi_id}")
            
            kpi_def = self.kpi_definitions[kpi_id]
            
            # Get source metrics
            source_metrics = await self.unified_metrics.aggregate_metrics(
                kpi_def.source_metrics,
                time_range
            )
            
            # Prepare source data
            source_data = {}
            for metric in source_metrics:
                source_data[metric.metric_id] = metric.aggregated_value
            
            # Calculate KPI value
            calculated_value = await self._execute_calculation(
                kpi_def.calculation_method,
                source_data,
                kpi_def.calculation_formula
            )
            
            # Determine status
            status = self._determine_kpi_status(calculated_value, kpi_def)
            
            # Calculate trend
            trend = await self._calculate_kpi_trend(kpi_id, calculated_value, time_range)
            
            # Compare to target
            target_comparison = await self._compare_to_target(kpi_id, calculated_value)
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(source_metrics)
            
            # Create KPI calculation
            kpi_calculation = KPICalculation(
                calculation_id=str(uuid.uuid4()),
                kpi_id=kpi_id,
                calculated_value=calculated_value,
                calculation_time=datetime.now(timezone.utc),
                calculation_period=calculation_period,
                source_data=source_data,
                status=status,
                trend=trend,
                target_comparison=target_comparison,
                confidence_level=confidence_level,
                metadata={
                    "time_range": {
                        "start": time_range[0].isoformat(),
                        "end": time_range[1].isoformat()
                    },
                    "source_metrics": [m.metric_id for m in source_metrics]
                }
            )
            
            # Store in history
            if kpi_id not in self.calculation_history:
                self.calculation_history[kpi_id] = []
            
            self.calculation_history[kpi_id].append(kpi_calculation)
            
            # Limit history size
            if len(self.calculation_history[kpi_id]) > self.max_history_size:
                self.calculation_history[kpi_id] = self.calculation_history[kpi_id][-self.max_history_size:]
            
            # Cache the calculation
            await self.cache.set(
                f"kpi_calc:{kpi_id}",
                kpi_calculation.to_dict(),
                ttl=self.cache_ttl
            )
            
            return kpi_calculation
            
        except Exception as e:
            self.logger.error(f"Error calculating KPI: {str(e)}")
            raise
    
    async def calculate_multiple_kpis(
        self,
        kpi_ids: List[str],
        time_range: Tuple[datetime, datetime],
        calculation_period: str = "current"
    ) -> List[KPICalculation]:
        """Calculate multiple KPIs"""
        try:
            calculations = []
            
            for kpi_id in kpi_ids:
                try:
                    calculation = await self.calculate_kpi(kpi_id, time_range, calculation_period)
                    calculations.append(calculation)
                except Exception as e:
                    self.logger.error(f"Error calculating KPI {kpi_id}: {str(e)}")
                    continue
            
            return calculations
            
        except Exception as e:
            self.logger.error(f"Error calculating multiple KPIs: {str(e)}")
            raise
    
    async def get_kpi_dashboard(
        self,
        kpi_ids: List[str] = None,
        category: KPICategory = None,
        time_range: Tuple[datetime, datetime] = None
    ) -> KPIDashboard:
        """Get KPI dashboard"""
        try:
            # Use last 24 hours if no time range specified
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                time_range = (start_time, end_time)
            
            # Determine KPIs to include
            if kpi_ids:
                target_kpis = kpi_ids
            else:
                target_kpis = list(self.kpi_definitions.keys())
                
                if category:
                    target_kpis = [
                        kpi_id for kpi_id in target_kpis
                        if self.kpi_definitions[kpi_id].category == category
                    ]
            
            # Calculate KPIs
            kpi_calculations = await self.calculate_multiple_kpis(
                target_kpis,
                time_range,
                "dashboard"
            )
            
            # Create dashboard summary
            summary = await self._create_dashboard_summary(kpi_calculations)
            
            # Generate insights
            insights = await self._generate_kpi_insights(kpi_calculations)
            
            # Create dashboard
            dashboard = KPIDashboard(
                dashboard_id=str(uuid.uuid4()),
                name=f"KPI Dashboard - {category or 'All Categories'}",
                description="Unified KPI dashboard across SI and APP roles",
                kpi_calculations=kpi_calculations,
                summary=summary,
                insights=insights,
                generated_time=datetime.now(timezone.utc),
                metadata={
                    "time_range": {
                        "start": time_range[0].isoformat(),
                        "end": time_range[1].isoformat()
                    },
                    "category": category,
                    "kpi_count": len(kpi_calculations)
                }
            )
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error getting KPI dashboard: {str(e)}")
            raise
    
    async def get_kpi_trends(
        self,
        kpi_id: str,
        time_range: Tuple[datetime, datetime],
        granularity: str = "day"
    ) -> List[KPICalculation]:
        """Get KPI trends over time"""
        try:
            if kpi_id not in self.kpi_definitions:
                raise ValueError(f"KPI definition not found: {kpi_id}")
            
            # Calculate time buckets
            time_buckets = await self._calculate_time_buckets(
                time_range[0],
                time_range[1],
                granularity
            )
            
            trends = []
            
            for bucket_start, bucket_end in time_buckets:
                try:
                    calculation = await self.calculate_kpi(
                        kpi_id,
                        (bucket_start, bucket_end),
                        f"trend_{granularity}"
                    )
                    trends.append(calculation)
                except Exception as e:
                    self.logger.error(f"Error calculating trend bucket: {str(e)}")
                    continue
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting KPI trends: {str(e)}")
            raise
    
    async def compare_kpis(
        self,
        kpi_id: str,
        time_periods: List[Tuple[datetime, datetime]],
        comparison_type: str = "period_over_period"
    ) -> Dict[str, Any]:
        """Compare KPI across time periods"""
        try:
            comparisons = {}
            
            for i, time_period in enumerate(time_periods):
                calculation = await self.calculate_kpi(
                    kpi_id,
                    time_period,
                    f"comparison_{i}"
                )
                
                comparisons[f"period_{i}"] = calculation
            
            # Calculate comparison metrics
            comparison_analysis = await self._analyze_kpi_comparisons(comparisons, comparison_type)
            
            return {
                "kpi_id": kpi_id,
                "comparison_type": comparison_type,
                "periods": comparisons,
                "analysis": comparison_analysis,
                "generated_time": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing KPIs: {str(e)}")
            raise
    
    async def _execute_calculation(
        self,
        calculation_method: str,
        source_data: Dict[str, Any],
        formula: str
    ) -> float:
        """Execute KPI calculation"""
        try:
            if calculation_method in self.kpi_calculators:
                return await self.kpi_calculators[calculation_method](source_data, formula)
            else:
                # Fallback to simple formula evaluation
                return self._evaluate_formula(source_data, formula)
                
        except Exception as e:
            self.logger.error(f"Error executing calculation: {str(e)}")
            return 0.0
    
    async def _calculate_division(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate division KPI"""
        try:
            # Parse formula: "numerator / denominator"
            parts = formula.split(" / ")
            if len(parts) != 2:
                raise ValueError("Invalid division formula")
            
            numerator = source_data.get(parts[0].strip(), 0)
            denominator = source_data.get(parts[1].strip(), 1)
            
            if denominator == 0:
                return 0.0
            
            return numerator / denominator
            
        except Exception as e:
            self.logger.error(f"Error calculating division: {str(e)}")
            return 0.0
    
    async def _calculate_weighted_average(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate weighted average KPI"""
        try:
            # Extract metrics from formula
            metrics = []
            weights = []
            
            # Simple weighted average of available metrics
            for metric_name, value in source_data.items():
                metrics.append(value)
                weights.append(1.0)  # Equal weights for simplicity
            
            if not metrics:
                return 0.0
            
            weighted_sum = sum(m * w for m, w in zip(metrics, weights))
            total_weight = sum(weights)
            
            return weighted_sum / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating weighted average: {str(e)}")
            return 0.0
    
    async def _calculate_composite(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate composite KPI"""
        try:
            # Parse formula: "(metric1 * weight1) + (metric2 * weight2) + ..."
            # For simplicity, use predefined weights
            total_score = 0.0
            total_weight = 0.0
            
            for metric_name, value in source_data.items():
                weight = 1.0  # Default weight
                if "accuracy" in metric_name:
                    weight = 0.4
                elif "completeness" in metric_name:
                    weight = 0.3
                elif "consistency" in metric_name:
                    weight = 0.3
                
                total_score += value * weight
                total_weight += weight
            
            return total_score / total_weight if total_weight > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating composite: {str(e)}")
            return 0.0
    
    async def _calculate_sla(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate SLA KPI"""
        try:
            # Simplified SLA calculation
            requests_under_sla = source_data.get("requests_under_sla", 0)
            total_requests = source_data.get("total_requests", 1)
            
            if total_requests == 0:
                return 0.0
            
            return (requests_under_sla / total_requests) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating SLA: {str(e)}")
            return 0.0
    
    async def _calculate_compliance_rate(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate compliance rate KPI"""
        try:
            compliant_processes = source_data.get("compliant_processes", 0)
            total_processes = source_data.get("total_processes", 1)
            
            if total_processes == 0:
                return 0.0
            
            return (compliant_processes / total_processes) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance rate: {str(e)}")
            return 0.0
    
    async def _calculate_satisfaction_index(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate satisfaction index KPI"""
        try:
            # Composite satisfaction index
            satisfaction_ratings = source_data.get("satisfaction_ratings", 0)
            response_time_factor = max(0, 1 - (source_data.get("response_times", 0) / 1000))  # Normalize
            error_rate_factor = max(0, 1 - (source_data.get("error_rates", 0) / 100))  # Normalize
            
            # Weighted combination
            index = (satisfaction_ratings * 0.6) + (response_time_factor * 0.2) + (error_rate_factor * 0.2)
            
            return min(5.0, max(0.0, index))  # Clamp to 0-5 range
            
        except Exception as e:
            self.logger.error(f"Error calculating satisfaction index: {str(e)}")
            return 0.0
    
    async def _calculate_growth_rate(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate growth rate KPI"""
        try:
            current_value = source_data.get("current_users", 0)
            previous_value = source_data.get("previous_users", 0)
            
            if previous_value == 0:
                return 0.0
            
            growth_rate = ((current_value - previous_value) / previous_value) * 100
            
            return growth_rate
            
        except Exception as e:
            self.logger.error(f"Error calculating growth rate: {str(e)}")
            return 0.0
    
    async def _calculate_availability(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate availability KPI"""
        try:
            uptime = source_data.get("uptime", 0)
            total_time = source_data.get("total_time", 1)
            
            if total_time == 0:
                return 0.0
            
            return (uptime / total_time) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating availability: {str(e)}")
            return 0.0
    
    async def _calculate_milestone_calculation(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate FIRS milestone progress with enhanced grant eligibility tracking"""
        try:
            # Extract milestone requirements from the formula
            taxpayer_count = source_data.get("taxpayer_count", 0)
            transmission_rate = source_data.get("transmission_rate", 0.0)
            large_taxpayer_count = source_data.get("large_taxpayer_count", 0)
            sme_taxpayer_count = source_data.get("sme_taxpayer_count", 0)
            sector_count = source_data.get("sector_count", 0)
            compliance_sustained = source_data.get("compliance_sustained", False)
            full_validation_completed = source_data.get("full_validation_completed", False)
            tenant_id = source_data.get("tenant_id")
            
            milestone_achieved = False
            progress_percentage = 0.0
            achievement_details = {}
            
            # Determine milestone type based on formula keywords
            if "milestone_1" in formula or ("taxpayer_count >= 20" in formula and "transmission_rate >= 80" in formula):
                # Milestone 1: 20 taxpayers with 80% transmission rate
                if taxpayer_count >= 20 and transmission_rate >= 80.0:
                    milestone_achieved = True
                    progress_percentage = 100.0
                else:
                    # Calculate partial progress with weighted factors
                    taxpayer_progress = min(taxpayer_count / 20, 1.0)
                    transmission_progress = min(transmission_rate / 80.0, 1.0)
                    progress_percentage = taxpayer_progress * transmission_progress * 100
                
                achievement_details = {
                    "milestone": "milestone_1",
                    "taxpayer_requirement": {"current": taxpayer_count, "target": 20, "met": taxpayer_count >= 20},
                    "transmission_requirement": {"current": transmission_rate, "target": 80.0, "met": transmission_rate >= 80.0},
                    "grant_amount": 50000.0
                }
            
            elif "milestone_2" in formula or ("taxpayer_count >= 40" in formula and "large_taxpayer_count" in formula):
                # Milestone 2: 40 taxpayers with Large + SME representation
                if taxpayer_count >= 40 and large_taxpayer_count > 0 and sme_taxpayer_count > 0:
                    milestone_achieved = True
                    progress_percentage = 100.0
                else:
                    taxpayer_progress = min(taxpayer_count / 40, 1.0)
                    # Enhanced representation scoring
                    representation_score = 0.0
                    if large_taxpayer_count > 0:
                        representation_score += 0.5
                    if sme_taxpayer_count > 0:
                        representation_score += 0.5
                    progress_percentage = taxpayer_progress * representation_score * 100
                
                achievement_details = {
                    "milestone": "milestone_2",
                    "taxpayer_requirement": {"current": taxpayer_count, "target": 40, "met": taxpayer_count >= 40},
                    "large_taxpayer_requirement": {"current": large_taxpayer_count, "target": 1, "met": large_taxpayer_count > 0},
                    "sme_taxpayer_requirement": {"current": sme_taxpayer_count, "target": 1, "met": sme_taxpayer_count > 0},
                    "grant_amount": 100000.0
                }
            
            elif "milestone_3" in formula or ("taxpayer_count >= 60" in formula and "sector_count" in formula):
                # Milestone 3: 60 taxpayers with cross-sector representation
                if taxpayer_count >= 60 and sector_count >= 2:
                    milestone_achieved = True
                    progress_percentage = 100.0
                else:
                    taxpayer_progress = min(taxpayer_count / 60, 1.0)
                    sector_progress = min(sector_count / 2, 1.0)
                    # Bonus for sector diversity beyond minimum
                    sector_bonus = min((sector_count - 2) * 0.1, 0.2) if sector_count > 2 else 0.0
                    progress_percentage = taxpayer_progress * (sector_progress + sector_bonus) * 100
                
                achievement_details = {
                    "milestone": "milestone_3",
                    "taxpayer_requirement": {"current": taxpayer_count, "target": 60, "met": taxpayer_count >= 60},
                    "sector_requirement": {"current": sector_count, "target": 2, "met": sector_count >= 2},
                    "grant_amount": 200000.0
                }
            
            elif "milestone_4" in formula or ("taxpayer_count >= 80" in formula and "compliance_sustained" in formula):
                # Milestone 4: 80 taxpayers with sustained compliance
                if taxpayer_count >= 80 and compliance_sustained:
                    milestone_achieved = True
                    progress_percentage = 100.0
                else:
                    taxpayer_progress = min(taxpayer_count / 80, 1.0)
                    # Enhanced compliance scoring with partial credit for improvement
                    compliance_progress = 1.0 if compliance_sustained else min(transmission_rate / 80.0, 0.8)
                    progress_percentage = taxpayer_progress * compliance_progress * 100
                
                achievement_details = {
                    "milestone": "milestone_4",
                    "taxpayer_requirement": {"current": taxpayer_count, "target": 80, "met": taxpayer_count >= 80},
                    "compliance_requirement": {"current": compliance_sustained, "target": True, "met": compliance_sustained},
                    "grant_amount": 400000.0
                }
            
            elif "milestone_5" in formula or ("taxpayer_count >= 100" in formula and "full_validation" in formula):
                # Milestone 5: 100 taxpayers with full validation
                if taxpayer_count >= 100 and full_validation_completed:
                    milestone_achieved = True
                    progress_percentage = 100.0
                else:
                    taxpayer_progress = min(taxpayer_count / 100, 1.0)
                    # Enhanced validation scoring
                    validation_progress = 1.0 if full_validation_completed else min(taxpayer_progress * 0.9, 0.85)
                    progress_percentage = taxpayer_progress * validation_progress * 100
                
                achievement_details = {
                    "milestone": "milestone_5",
                    "taxpayer_requirement": {"current": taxpayer_count, "target": 100, "met": taxpayer_count >= 100},
                    "validation_requirement": {"current": full_validation_completed, "target": True, "met": full_validation_completed},
                    "grant_amount": 800000.0
                }
            
            # Trigger milestone achievement notification if achieved
            if milestone_achieved and tenant_id:
                await self._trigger_milestone_achievement_notification(tenant_id, achievement_details)
            
            # Store milestone progress for tracking
            if tenant_id:
                await self._store_milestone_progress(tenant_id, achievement_details, progress_percentage)
            
            # Grant eligibility tracking
            await self._track_grant_eligibility(source_data, achievement_details, progress_percentage)
            
            return progress_percentage
            
        except Exception as e:
            self.logger.error(f"Error calculating milestone progress: {str(e)}")
            return 0.0
    
    async def _calculate_addition(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate addition of multiple metrics"""
        try:
            total = 0.0
            for key, value in source_data.items():
                if isinstance(value, (int, float)):
                    total += value
            return total
            
        except Exception as e:
            self.logger.error(f"Error calculating addition: {str(e)}")
            return 0.0
    
    async def _calculate_ratio(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate ratio between metrics"""
        try:
            # Extract ratio calculation from formula
            if "si_revenue" in source_data and "app_grant_revenue" in source_data:
                si_revenue = source_data.get("si_revenue", 0)
                app_grant_revenue = source_data.get("app_grant_revenue", 0)
                total_revenue = si_revenue + app_grant_revenue
                
                if total_revenue > 0:
                    return (si_revenue / total_revenue) * 100
                else:
                    return 0.0
            
            # Generic ratio calculation for other cases
            values = [v for v in source_data.values() if isinstance(v, (int, float))]
            if len(values) >= 2:
                return (values[0] / values[1]) * 100 if values[1] != 0 else 0.0
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating ratio: {str(e)}")
            return 0.0
    
    async def _calculate_churn_rate(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate customer churn rate"""
        try:
            churned_customers = source_data.get("churned_customers", 0)
            total_customers_start_month = source_data.get("total_customers_start_month", 0)
            
            if total_customers_start_month == 0:
                return 0.0
            
            return (churned_customers / total_customers_start_month) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating churn rate: {str(e)}")
            return 0.0
    
    # Phase 4 Unified Revenue KPI Calculation Methods
    
    async def _calculate_si_contribution_percentage(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate SI revenue contribution percentage"""
        try:
            si_revenue = source_data.get("si_revenue", 0)
            app_grant_revenue = source_data.get("app_grant_revenue", 0)
            total_revenue = si_revenue + app_grant_revenue
            
            if total_revenue == 0:
                return 0.0
            
            return (si_revenue / total_revenue) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating SI contribution percentage: {str(e)}")
            return 0.0
    
    async def _calculate_app_contribution_percentage(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate APP grant contribution percentage"""
        try:
            si_revenue = source_data.get("si_revenue", 0)
            app_grant_revenue = source_data.get("app_grant_revenue", 0)
            total_revenue = si_revenue + app_grant_revenue
            
            if total_revenue == 0:
                return 0.0
            
            return (app_grant_revenue / total_revenue) * 100
            
        except Exception as e:
            self.logger.error(f"Error calculating APP contribution percentage: {str(e)}")
            return 0.0
    
    async def _calculate_cac(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate Customer Acquisition Cost"""
        try:
            marketing_spend = source_data.get("marketing_spend", 0)
            sales_spend = source_data.get("sales_spend", 0)
            new_customers_acquired = source_data.get("new_customers_acquired", 0)
            
            if new_customers_acquired == 0:
                return 0.0
            
            total_acquisition_cost = marketing_spend + sales_spend
            return total_acquisition_cost / new_customers_acquired
            
        except Exception as e:
            self.logger.error(f"Error calculating CAC: {str(e)}")
            return 0.0
    
    async def _calculate_grant_roi(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate Grant ROI for APP services"""
        try:
            total_grants_received = source_data.get("total_grants_received", 0)
            app_operational_costs = source_data.get("app_operational_costs", 1)  # Avoid division by zero
            taxpayer_onboarding_value = source_data.get("taxpayer_onboarding_value", 0)
            
            # Calculate total value generated
            total_value = total_grants_received + taxpayer_onboarding_value
            
            # Calculate ROI: ((Value - Cost) / Cost) * 100
            if app_operational_costs == 0:
                return 0.0
            
            roi = ((total_value - app_operational_costs) / app_operational_costs) * 100
            return max(roi, 0.0)  # Ensure non-negative ROI
            
        except Exception as e:
            self.logger.error(f"Error calculating grant ROI: {str(e)}")
            return 0.0
    
    async def _calculate_unified_rpu(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate unified Revenue Per User across SI and APP"""
        try:
            total_revenue = source_data.get("total_revenue", 0)
            si_users = source_data.get("si_users", 0)
            app_taxpayers = source_data.get("app_taxpayers", 0)
            
            total_users = si_users + app_taxpayers
            
            if total_users == 0:
                return 0.0
            
            return total_revenue / total_users
            
        except Exception as e:
            self.logger.error(f"Error calculating unified RPU: {str(e)}")
            return 0.0
    
    async def _calculate_milestone_achievement_rate(self, source_data: Dict[str, Any], formula: str) -> float:
        """Calculate milestone achievement rate for APP grants"""
        try:
            milestones_achieved = source_data.get("milestones_achieved", 0)
            milestones_attempted = source_data.get("milestones_attempted", 0)
            
            if milestones_attempted == 0:
                return 0.0
            
            achievement_rate = (milestones_achieved / milestones_attempted) * 100
            
            # Consider timeline performance as a factor
            timeline_performance = source_data.get("milestone_timeline_performance", 1.0)
            adjusted_rate = achievement_rate * timeline_performance
            
            return min(adjusted_rate, 100.0)  # Cap at 100%
            
        except Exception as e:
            self.logger.error(f"Error calculating milestone achievement rate: {str(e)}")
            return 0.0
    
    def _evaluate_formula(self, source_data: Dict[str, Any], formula: str) -> float:
        """Evaluate simple formula"""
        try:
            # Simple formula evaluation (security risk - use with caution)
            # Replace metric names with values
            evaluated_formula = formula
            for metric_name, value in source_data.items():
                evaluated_formula = evaluated_formula.replace(metric_name, str(value))
            
            # Basic mathematical evaluation
            try:
                return float(eval(evaluated_formula))
            except:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error evaluating formula: {str(e)}")
            return 0.0
    
    def _determine_kpi_status(self, value: float, kpi_def: KPIDefinition) -> KPIStatus:
        """Determine KPI status based on thresholds"""
        try:
            thresholds = kpi_def.thresholds
            
            if kpi_def.is_higher_better:
                if value >= thresholds.get("excellent", float('inf')):
                    return KPIStatus.EXCELLENT
                elif value >= thresholds.get("good", 0):
                    return KPIStatus.GOOD
                elif value >= thresholds.get("fair", 0):
                    return KPIStatus.FAIR
                elif value >= thresholds.get("poor", 0):
                    return KPIStatus.POOR
                else:
                    return KPIStatus.CRITICAL
            else:
                if value <= thresholds.get("excellent", 0):
                    return KPIStatus.EXCELLENT
                elif value <= thresholds.get("good", float('inf')):
                    return KPIStatus.GOOD
                elif value <= thresholds.get("fair", float('inf')):
                    return KPIStatus.FAIR
                elif value <= thresholds.get("poor", float('inf')):
                    return KPIStatus.POOR
                else:
                    return KPIStatus.CRITICAL
                    
        except Exception as e:
            self.logger.error(f"Error determining KPI status: {str(e)}")
            return KPIStatus.UNKNOWN
    
    async def _calculate_kpi_trend(
        self,
        kpi_id: str,
        current_value: float,
        time_range: Tuple[datetime, datetime]
    ) -> KPITrend:
        """Calculate KPI trend"""
        try:
            # Get historical data
            historical_range = (
                time_range[0] - timedelta(days=7),
                time_range[0]
            )
            
            if kpi_id in self.calculation_history:
                historical_calculations = [
                    calc for calc in self.calculation_history[kpi_id]
                    if historical_range[0] <= calc.calculation_time <= historical_range[1]
                ]
                
                if historical_calculations:
                    historical_value = statistics.mean([
                        calc.calculated_value for calc in historical_calculations
                    ])
                    
                    if current_value > historical_value * 1.05:
                        return KPITrend.IMPROVING
                    elif current_value < historical_value * 0.95:
                        return KPITrend.DECLINING
                    else:
                        return KPITrend.STABLE
            
            return KPITrend.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error calculating KPI trend: {str(e)}")
            return KPITrend.UNKNOWN
    
    async def _compare_to_target(self, kpi_id: str, current_value: float) -> Dict[str, Any]:
        """Compare KPI to target"""
        try:
            if kpi_id not in self.kpi_targets or not self.kpi_targets[kpi_id]:
                return {"has_target": False}
            
            # Get current target
            current_target = self.kpi_targets[kpi_id][-1]  # Most recent target
            
            target_value = current_target.target_value
            difference = current_value - target_value
            percentage_diff = (difference / target_value) * 100 if target_value != 0 else 0
            
            return {
                "has_target": True,
                "target_value": target_value,
                "current_value": current_value,
                "difference": difference,
                "percentage_difference": percentage_diff,
                "target_met": current_value >= target_value,
                "target_type": current_target.target_type
            }
            
        except Exception as e:
            self.logger.error(f"Error comparing to target: {str(e)}")
            return {"has_target": False}
    
    def _calculate_confidence_level(self, source_metrics: List[AggregatedMetric]) -> float:
        """Calculate confidence level based on source metrics"""
        try:
            if not source_metrics:
                return 0.0
            
            # Average confidence from source metrics
            confidence_sum = sum(metric.confidence_level for metric in source_metrics)
            return confidence_sum / len(source_metrics)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {str(e)}")
            return 0.0
    
    async def _create_dashboard_summary(self, kpi_calculations: List[KPICalculation]) -> Dict[str, Any]:
        """Create dashboard summary"""
        try:
            if not kpi_calculations:
                return {}
            
            status_counts = {}
            trend_counts = {}
            
            for calc in kpi_calculations:
                status_counts[calc.status] = status_counts.get(calc.status, 0) + 1
                trend_counts[calc.trend] = trend_counts.get(calc.trend, 0) + 1
            
            return {
                "total_kpis": len(kpi_calculations),
                "status_distribution": status_counts,
                "trend_distribution": trend_counts,
                "average_confidence": statistics.mean([
                    calc.confidence_level for calc in kpi_calculations
                ]),
                "critical_kpis": [
                    calc.kpi_id for calc in kpi_calculations
                    if calc.status == KPIStatus.CRITICAL
                ],
                "improving_kpis": [
                    calc.kpi_id for calc in kpi_calculations
                    if calc.trend == KPITrend.IMPROVING
                ],
                "declining_kpis": [
                    calc.kpi_id for calc in kpi_calculations
                    if calc.trend == KPITrend.DECLINING
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error creating dashboard summary: {str(e)}")
            return {}
    
    async def _generate_kpi_insights(self, kpi_calculations: List[KPICalculation]) -> List[KPIInsight]:
        """Generate insights from KPI calculations"""
        try:
            insights = []
            
            for calc in kpi_calculations:
                if calc.status == KPIStatus.CRITICAL:
                    insight = KPIInsight(
                        insight_id=str(uuid.uuid4()),
                        kpi_id=calc.kpi_id,
                        insight_type="critical_performance",
                        title=f"Critical Performance Issue: {calc.kpi_id}",
                        description=f"KPI {calc.kpi_id} is at critical level with value {calc.calculated_value}",
                        severity="critical",
                        recommendations=[
                            "Immediate investigation required",
                            "Review underlying processes",
                            "Consider emergency measures"
                        ],
                        impact_assessment={"business_impact": "high", "urgency": "immediate"},
                        generated_time=datetime.now(timezone.utc)
                    )
                    insights.append(insight)
                
                elif calc.trend == KPITrend.DECLINING:
                    insight = KPIInsight(
                        insight_id=str(uuid.uuid4()),
                        kpi_id=calc.kpi_id,
                        insight_type="declining_trend",
                        title=f"Declining Trend: {calc.kpi_id}",
                        description=f"KPI {calc.kpi_id} shows declining trend",
                        severity="warning",
                        recommendations=[
                            "Monitor closely",
                            "Analyze root causes",
                            "Implement corrective measures"
                        ],
                        impact_assessment={"business_impact": "medium", "urgency": "medium"},
                        generated_time=datetime.now(timezone.utc)
                    )
                    insights.append(insight)
                
                elif calc.status == KPIStatus.EXCELLENT and calc.trend == KPITrend.IMPROVING:
                    insight = KPIInsight(
                        insight_id=str(uuid.uuid4()),
                        kpi_id=calc.kpi_id,
                        insight_type="excellent_performance",
                        title=f"Excellent Performance: {calc.kpi_id}",
                        description=f"KPI {calc.kpi_id} is performing excellently with improving trend",
                        severity="info",
                        recommendations=[
                            "Maintain current practices",
                            "Document success factors",
                            "Consider replicating approach"
                        ],
                        impact_assessment={"business_impact": "positive", "urgency": "low"},
                        generated_time=datetime.now(timezone.utc)
                    )
                    insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating KPI insights: {str(e)}")
            return []
    
    async def _analyze_kpi_comparisons(
        self,
        comparisons: Dict[str, KPICalculation],
        comparison_type: str
    ) -> Dict[str, Any]:
        """Analyze KPI comparisons"""
        try:
            if len(comparisons) < 2:
                return {}
            
            values = [calc.calculated_value for calc in comparisons.values()]
            
            analysis = {
                "comparison_type": comparison_type,
                "min_value": min(values),
                "max_value": max(values),
                "average_value": statistics.mean(values),
                "value_range": max(values) - min(values),
                "coefficient_of_variation": statistics.stdev(values) / statistics.mean(values) if statistics.mean(values) != 0 else 0
            }
            
            # Period over period analysis
            if comparison_type == "period_over_period" and len(values) >= 2:
                current_value = values[-1]
                previous_value = values[-2]
                
                analysis["period_change"] = current_value - previous_value
                analysis["period_change_percentage"] = ((current_value - previous_value) / previous_value) * 100 if previous_value != 0 else 0
                analysis["improvement"] = current_value > previous_value
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing KPI comparisons: {str(e)}")
            return {}
    
    async def _calculate_time_buckets(
        self,
        start_time: datetime,
        end_time: datetime,
        granularity: str
    ) -> List[Tuple[datetime, datetime]]:
        """Calculate time buckets for trend analysis"""
        try:
            buckets = []
            
            if granularity == "hour":
                delta = timedelta(hours=1)
            elif granularity == "day":
                delta = timedelta(days=1)
            elif granularity == "week":
                delta = timedelta(weeks=1)
            elif granularity == "month":
                delta = timedelta(days=30)  # Approximate
            else:
                delta = timedelta(days=1)
            
            current = start_time
            while current < end_time:
                bucket_end = min(current + delta, end_time)
                buckets.append((current, bucket_end))
                current = bucket_end
            
            return buckets
            
        except Exception as e:
            self.logger.error(f"Error calculating time buckets: {str(e)}")
            return []
    
    async def _periodic_calculation(self):
        """Periodic KPI calculation task"""
        while True:
            try:
                await asyncio.sleep(self.calculation_interval)
                
                # Calculate all KPIs
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)
                
                for kpi_id in self.kpi_definitions.keys():
                    try:
                        await self.calculate_kpi(kpi_id, (start_time, end_time), "periodic")
                    except Exception as e:
                        self.logger.error(f"Error in periodic calculation for {kpi_id}: {str(e)}")
                        continue
                
            except Exception as e:
                self.logger.error(f"Error in periodic calculation: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "kpi.threshold_exceeded",
                self._handle_threshold_exceeded
            )
            
            await self.event_bus.subscribe(
                "metrics.updated",
                self._handle_metrics_updated
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_threshold_exceeded(self, event_data: Dict[str, Any]):
        """Handle threshold exceeded event"""
        try:
            kpi_id = event_data.get("kpi_id")
            threshold_type = event_data.get("threshold_type")
            
            await self.notification_service.send_notification(
                type="kpi_threshold_exceeded",
                data={
                    "kpi_id": kpi_id,
                    "threshold_type": threshold_type,
                    "current_value": event_data.get("current_value"),
                    "threshold_value": event_data.get("threshold_value")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error handling threshold exceeded event: {str(e)}")
    
    async def _handle_metrics_updated(self, event_data: Dict[str, Any]):
        """Handle metrics updated event"""
        try:
            # Trigger relevant KPI calculations
            metric_id = event_data.get("metric_id")
            
            # Find KPIs that use this metric
            relevant_kpis = [
                kpi_id for kpi_id, kpi_def in self.kpi_definitions.items()
                if metric_id in kpi_def.source_metrics
            ]
            
            # Trigger calculation for relevant KPIs
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=1)
            
            for kpi_id in relevant_kpis:
                try:
                    await self.calculate_kpi(kpi_id, (start_time, end_time), "metric_updated")
                except Exception as e:
                    self.logger.error(f"Error calculating KPI {kpi_id} after metric update: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error handling metrics updated event: {str(e)}")
    
    async def _trigger_milestone_achievement_notification(self, tenant_id: str, achievement_details: Dict[str, Any]):
        """Trigger notification when milestone is achieved"""
        try:
            milestone = achievement_details.get("milestone")
            grant_amount = achievement_details.get("grant_amount", 0)
            
            # Emit milestone achievement event
            await self.event_bus.emit("firs_milestone_achieved", {
                "tenant_id": tenant_id,
                "milestone": milestone,
                "grant_amount": grant_amount,
                "achievement_date": datetime.now(timezone.utc).isoformat(),
                "achievement_details": achievement_details
            })
            
            # Send notification
            await self.notification_service.send_notification(
                type="milestone_achievement",
                recipients=[tenant_id],
                data={
                    "title": f"FIRS {milestone.replace('_', ' ').title()} Achieved!",
                    "message": f"Congratulations! You have achieved {milestone.replace('_', ' ').title()} and are eligible for a grant of ₦{grant_amount:,}",
                    "milestone": milestone,
                    "grant_amount": grant_amount,
                    "achievement_details": achievement_details,
                    "next_steps": [
                        "Submit grant application to FIRS",
                        "Provide supporting documentation",
                        "Maintain compliance requirements"
                    ]
                }
            )
            
            self.logger.info(f"Milestone achievement notification sent for {milestone} to tenant {tenant_id}")
            
        except Exception as e:
            self.logger.error(f"Error triggering milestone achievement notification: {str(e)}")
    
    async def _store_milestone_progress(self, tenant_id: str, achievement_details: Dict[str, Any], progress_percentage: float):
        """Store milestone progress for historical tracking"""
        try:
            milestone_data = {
                "tenant_id": tenant_id,
                "milestone": achievement_details.get("milestone"),
                "progress_percentage": progress_percentage,
                "achievement_details": achievement_details,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "is_achieved": progress_percentage >= 100.0
            }
            
            # Cache milestone progress
            cache_key = f"milestone_progress:{tenant_id}:{achievement_details.get('milestone')}"
            await self.cache.set(cache_key, milestone_data, ttl=86400)  # 24 hours
            
            # Store in calculation history for trend analysis
            milestone_key = f"milestone_progress_{achievement_details.get('milestone')}"
            if milestone_key not in self.calculation_history:
                self.calculation_history[milestone_key] = []
            
            progress_calculation = KPICalculation(
                calculation_id=str(uuid.uuid4()),
                kpi_id=f"firs_{achievement_details.get('milestone')}_progress",
                calculated_value=progress_percentage,
                calculation_time=datetime.now(timezone.utc),
                calculation_period="milestone_tracking",
                source_data=achievement_details,
                status=KPIStatus.EXCELLENT if progress_percentage >= 100.0 else KPIStatus.GOOD if progress_percentage >= 80.0 else KPIStatus.FAIR,
                trend=KPITrend.IMPROVING if progress_percentage > 0 else KPITrend.STABLE,
                target_comparison={"target_value": 100.0, "current_value": progress_percentage},
                confidence_level=0.95,
                metadata={"tenant_id": tenant_id, "milestone_data": achievement_details}
            )
            
            self.calculation_history[milestone_key].append(progress_calculation)
            
            # Limit history size
            if len(self.calculation_history[milestone_key]) > 100:
                self.calculation_history[milestone_key] = self.calculation_history[milestone_key][-100:]
            
        except Exception as e:
            self.logger.error(f"Error storing milestone progress: {str(e)}")
    
    async def _track_grant_eligibility(self, source_data: Dict[str, Any], achievement_details: Dict[str, Any], progress_percentage: float):
        """Track grant eligibility status and requirements"""
        try:
            tenant_id = source_data.get("tenant_id")
            milestone = achievement_details.get("milestone")
            
            eligibility_data = {
                "tenant_id": tenant_id,
                "milestone": milestone,
                "eligibility_status": "eligible" if progress_percentage >= 100.0 else "in_progress",
                "progress_percentage": progress_percentage,
                "requirements_status": achievement_details,
                "grant_amount": achievement_details.get("grant_amount", 0),
                "assessment_date": datetime.now(timezone.utc).isoformat(),
                "next_requirements": self._get_next_requirements(milestone, achievement_details),
                "compliance_score": self._calculate_compliance_score(achievement_details),
                "risk_factors": self._identify_risk_factors(source_data, achievement_details)
            }
            
            # Cache eligibility data
            cache_key = f"grant_eligibility:{tenant_id}:{milestone}"
            await self.cache.set(cache_key, eligibility_data, ttl=3600)  # 1 hour
            
            # Emit grant eligibility event for downstream processing
            await self.event_bus.emit("grant_eligibility_updated", {
                "tenant_id": tenant_id,
                "eligibility_data": eligibility_data
            })
            
            # Track milestone approaching notifications (80% and 90% thresholds)
            if 80.0 <= progress_percentage < 100.0:
                await self._trigger_milestone_approaching_notification(tenant_id, milestone, progress_percentage, eligibility_data)
            
        except Exception as e:
            self.logger.error(f"Error tracking grant eligibility: {str(e)}")
    
    async def _trigger_milestone_approaching_notification(self, tenant_id: str, milestone: str, progress: float, eligibility_data: Dict[str, Any]):
        """Trigger notification when milestone is approaching"""
        try:
            if progress >= 90.0:
                notification_type = "milestone_nearly_achieved"
                message = f"You're almost there! {progress:.1f}% complete for {milestone.replace('_', ' ').title()}"
            elif progress >= 80.0:
                notification_type = "milestone_approaching"
                message = f"Great progress! {progress:.1f}% complete for {milestone.replace('_', ' ').title()}"
            else:
                return  # Don't send notification below 80%
            
            await self.notification_service.send_notification(
                type=notification_type,
                recipients=[tenant_id],
                data={
                    "title": f"FIRS {milestone.replace('_', ' ').title()} Progress Update",
                    "message": message,
                    "milestone": milestone,
                    "progress_percentage": progress,
                    "next_requirements": eligibility_data.get("next_requirements", []),
                    "recommendations": self._get_milestone_recommendations(milestone, eligibility_data)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error triggering milestone approaching notification: {str(e)}")
    
    def _get_next_requirements(self, milestone: str, achievement_details: Dict[str, Any]) -> List[str]:
        """Get next requirements for milestone completion"""
        requirements = []
        
        if milestone == "milestone_1":
            taxpayer_req = achievement_details.get("taxpayer_requirement", {})
            transmission_req = achievement_details.get("transmission_requirement", {})
            
            if not taxpayer_req.get("met", False):
                remaining = taxpayer_req.get("target", 20) - taxpayer_req.get("current", 0)
                requirements.append(f"Onboard {remaining} more taxpayers")
            
            if not transmission_req.get("met", False):
                current_rate = transmission_req.get("current", 0)
                requirements.append(f"Improve transmission rate from {current_rate:.1f}% to 80%")
        
        elif milestone == "milestone_2":
            taxpayer_req = achievement_details.get("taxpayer_requirement", {})
            large_req = achievement_details.get("large_taxpayer_requirement", {})
            sme_req = achievement_details.get("sme_taxpayer_requirement", {})
            
            if not taxpayer_req.get("met", False):
                remaining = taxpayer_req.get("target", 40) - taxpayer_req.get("current", 0)
                requirements.append(f"Onboard {remaining} more taxpayers")
            
            if not large_req.get("met", False):
                requirements.append("Onboard at least one large taxpayer")
            
            if not sme_req.get("met", False):
                requirements.append("Onboard at least one SME taxpayer")
        
        elif milestone == "milestone_3":
            taxpayer_req = achievement_details.get("taxpayer_requirement", {})
            sector_req = achievement_details.get("sector_requirement", {})
            
            if not taxpayer_req.get("met", False):
                remaining = taxpayer_req.get("target", 60) - taxpayer_req.get("current", 0)
                requirements.append(f"Onboard {remaining} more taxpayers")
            
            if not sector_req.get("met", False):
                current_sectors = sector_req.get("current", 0)
                requirements.append(f"Diversify across {2 - current_sectors} more economic sectors")
        
        # Add similar logic for milestones 4 and 5...
        
        return requirements
    
    def _calculate_compliance_score(self, achievement_details: Dict[str, Any]) -> float:
        """Calculate compliance score based on achievement details"""
        try:
            met_requirements = 0
            total_requirements = 0
            
            for key, requirement in achievement_details.items():
                if key.endswith("_requirement") and isinstance(requirement, dict):
                    total_requirements += 1
                    if requirement.get("met", False):
                        met_requirements += 1
            
            return (met_requirements / total_requirements * 100) if total_requirements > 0 else 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating compliance score: {str(e)}")
            return 0.0
    
    def _identify_risk_factors(self, source_data: Dict[str, Any], achievement_details: Dict[str, Any]) -> List[str]:
        """Identify risk factors that might impact milestone achievement"""
        risk_factors = []
        
        try:
            # Check transmission rate trends
            transmission_rate = source_data.get("transmission_rate", 0)
            if transmission_rate < 70.0:
                risk_factors.append("Low transmission rate may impact milestone 1 achievement")
            
            # Check sector diversity
            sector_count = source_data.get("sector_count", 0)
            if sector_count < 2:
                risk_factors.append("Limited sector diversity may impact milestone 3 achievement")
            
            # Check taxpayer mix
            large_count = source_data.get("large_taxpayer_count", 0)
            sme_count = source_data.get("sme_taxpayer_count", 0)
            
            if large_count == 0:
                risk_factors.append("No large taxpayers may impact milestone 2 achievement")
            
            if sme_count == 0:
                risk_factors.append("No SME taxpayers may impact milestone 2 achievement")
            
            # Check growth rate
            growth_rate = source_data.get("monthly_growth_rate", 0)
            if growth_rate < 5:
                risk_factors.append("Low growth rate may delay milestone completion")
            
        except Exception as e:
            self.logger.error(f"Error identifying risk factors: {str(e)}")
        
        return risk_factors
    
    def _get_milestone_recommendations(self, milestone: str, eligibility_data: Dict[str, Any]) -> List[str]:
        """Get actionable recommendations for milestone achievement"""
        recommendations = []
        
        try:
            progress = eligibility_data.get("progress_percentage", 0)
            
            if milestone == "milestone_1":
                if progress < 50:
                    recommendations.extend([
                        "Focus on aggressive taxpayer acquisition campaigns",
                        "Implement referral programs to accelerate onboarding",
                        "Provide training to improve taxpayer engagement"
                    ])
                elif progress < 80:
                    recommendations.extend([
                        "Optimize onboarding processes to reduce friction",
                        "Implement automated follow-up systems",
                        "Focus on improving transmission rate through user education"
                    ])
                else:
                    recommendations.extend([
                        "Maintain current strategies and monitor progress",
                        "Prepare documentation for grant application",
                        "Ensure consistent transmission rate maintenance"
                    ])
            
            # Add similar logic for other milestones...
            
        except Exception as e:
            self.logger.error(f"Error generating milestone recommendations: {str(e)}")
        
        return recommendations
    
    async def get_unified_revenue_dashboard(
        self,
        time_range: Tuple[datetime, datetime] = None,
        include_forecasting: bool = True
    ) -> Dict[str, Any]:
        """Get unified revenue dashboard combining SI and APP revenue streams"""
        try:
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=30)
                time_range = (start_time, end_time)
            
            # Calculate all unified revenue KPIs
            unified_revenue_kpis = [
                "total_revenue",
                "si_revenue_contribution", 
                "app_grant_contribution",
                "customer_acquisition_cost",
                "grant_roi",
                "revenue_per_user",
                "churn_rate_si",
                "milestone_achievement_rate"
            ]
            
            kpi_calculations = await self.calculate_multiple_kpis(
                unified_revenue_kpis,
                time_range,
                "unified_dashboard"
            )
            
            # Calculate business health metrics
            business_health = await self._calculate_business_health_metrics(kpi_calculations)
            
            # Generate revenue forecasting if requested
            forecasting_data = {}
            if include_forecasting:
                forecasting_data = await self._generate_revenue_forecasting(time_range)
            
            # Create revenue mix analysis
            revenue_mix_analysis = await self._analyze_revenue_mix(kpi_calculations)
            
            # Generate unified insights
            unified_insights = await self._generate_unified_revenue_insights(
                kpi_calculations, 
                business_health,
                revenue_mix_analysis
            )
            
            dashboard = {
                "dashboard_id": str(uuid.uuid4()),
                "dashboard_type": "unified_revenue",
                "name": "Unified Revenue Dashboard - SI & APP",
                "description": "Comprehensive revenue analytics across System Integrator and Access Point Provider services",
                "generated_time": datetime.now(timezone.utc),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "revenue_kpis": {
                    calc.kpi_id: {
                        "value": calc.calculated_value,
                        "status": calc.status,
                        "trend": calc.trend,
                        "target_comparison": calc.target_comparison,
                        "confidence_level": calc.confidence_level
                    }
                    for calc in kpi_calculations
                },
                "business_health": business_health,
                "revenue_mix_analysis": revenue_mix_analysis,
                "forecasting": forecasting_data,
                "unified_insights": unified_insights,
                "performance_summary": await self._create_revenue_performance_summary(kpi_calculations),
                "recommendations": await self._generate_revenue_optimization_recommendations(
                    kpi_calculations, 
                    business_health
                )
            }
            
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Error generating unified revenue dashboard: {str(e)}")
            return {}
    
    async def _calculate_business_health_metrics(self, kpi_calculations: List[KPICalculation]) -> Dict[str, Any]:
        """Calculate comprehensive business health metrics"""
        try:
            health_metrics = {
                "overall_health_score": 0.0,
                "revenue_health": {},
                "customer_health": {},
                "operational_health": {},
                "growth_health": {},
                "risk_factors": [],
                "health_trend": "unknown"
            }
            
            # Calculate revenue health
            total_revenue_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "total_revenue"), 
                None
            )
            si_contribution_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "si_revenue_contribution"), 
                None
            )
            app_contribution_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "app_grant_contribution"), 
                None
            )
            
            revenue_health_score = 0.0
            if total_revenue_calc:
                revenue_health_score += self._status_to_score(total_revenue_calc.status) * 0.4
            if si_contribution_calc:
                revenue_health_score += self._status_to_score(si_contribution_calc.status) * 0.3
            if app_contribution_calc:
                revenue_health_score += self._status_to_score(app_contribution_calc.status) * 0.3
            
            health_metrics["revenue_health"] = {
                "score": revenue_health_score,
                "revenue_diversification": self._calculate_revenue_diversification(si_contribution_calc, app_contribution_calc),
                "revenue_stability": self._assess_revenue_stability(kpi_calculations),
                "growth_trajectory": self._assess_growth_trajectory(kpi_calculations)
            }
            
            # Calculate customer health
            churn_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "churn_rate_si"), 
                None
            )
            cac_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "customer_acquisition_cost"), 
                None
            )
            rpu_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "revenue_per_user"), 
                None
            )
            
            customer_health_score = 0.0
            if churn_calc:
                # Lower churn is better, so invert the score
                customer_health_score += (100 - self._status_to_score(churn_calc.status)) * 0.4
            if cac_calc:
                customer_health_score += (100 - self._status_to_score(cac_calc.status)) * 0.3  # Lower CAC is better
            if rpu_calc:
                customer_health_score += self._status_to_score(rpu_calc.status) * 0.3
            
            health_metrics["customer_health"] = {
                "score": customer_health_score,
                "retention_quality": self._assess_retention_quality(churn_calc),
                "acquisition_efficiency": self._assess_acquisition_efficiency(cac_calc, rpu_calc),
                "customer_value": self._assess_customer_value(rpu_calc)
            }
            
            # Calculate operational health
            milestone_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "milestone_achievement_rate"), 
                None
            )
            grant_roi_calc = next(
                (calc for calc in kpi_calculations if calc.kpi_id == "grant_roi"), 
                None
            )
            
            operational_health_score = 0.0
            if milestone_calc:
                operational_health_score += self._status_to_score(milestone_calc.status) * 0.5
            if grant_roi_calc:
                operational_health_score += self._status_to_score(grant_roi_calc.status) * 0.5
            
            health_metrics["operational_health"] = {
                "score": operational_health_score,
                "grant_performance": self._assess_grant_performance(milestone_calc, grant_roi_calc),
                "process_efficiency": self._assess_process_efficiency(kpi_calculations),
                "compliance_status": self._assess_compliance_status(milestone_calc)
            }
            
            # Calculate overall health score
            health_metrics["overall_health_score"] = (
                health_metrics["revenue_health"]["score"] * 0.4 +
                health_metrics["customer_health"]["score"] * 0.35 +
                health_metrics["operational_health"]["score"] * 0.25
            )
            
            # Identify risk factors
            health_metrics["risk_factors"] = await self._identify_business_risk_factors(kpi_calculations)
            
            # Determine health trend
            health_metrics["health_trend"] = self._determine_health_trend(kpi_calculations)
            
            return health_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating business health metrics: {str(e)}")
            return {}
    
    async def _generate_revenue_forecasting(self, base_time_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Generate revenue forecasting using multiple algorithms"""
        try:
            forecasting_data = {
                "forecasting_period": "3_months",
                "confidence_level": 0.85,
                "algorithms_used": ["linear_regression", "exponential_smoothing", "trend_analysis"],
                "forecasts": {},
                "scenarios": {},
                "assumptions": []
            }
            
            # Get historical data for forecasting (last 6 months)
            historical_end = base_time_range[0]
            historical_start = historical_end - timedelta(days=180)
            
            # Calculate revenue trends for SI and APP
            si_revenue_trends = await self.get_kpi_trends(
                "si_revenue_contribution",
                (historical_start, historical_end),
                "month"
            )
            
            app_revenue_trends = await self.get_kpi_trends(
                "app_grant_contribution", 
                (historical_start, historical_end),
                "month"
            )
            
            total_revenue_trends = await self.get_kpi_trends(
                "total_revenue",
                (historical_start, historical_end),
                "month"
            )
            
            # Apply forecasting algorithms
            if total_revenue_trends:
                forecasting_data["forecasts"]["total_revenue"] = await self._apply_forecasting_algorithms(
                    total_revenue_trends, "total_revenue"
                )
            
            if si_revenue_trends:
                forecasting_data["forecasts"]["si_revenue"] = await self._apply_forecasting_algorithms(
                    si_revenue_trends, "si_revenue_contribution"
                )
            
            if app_revenue_trends:
                forecasting_data["forecasts"]["app_revenue"] = await self._apply_forecasting_algorithms(
                    app_revenue_trends, "app_grant_contribution"
                )
            
            # Generate scenario analysis
            forecasting_data["scenarios"] = {
                "optimistic": await self._generate_optimistic_scenario(forecasting_data["forecasts"]),
                "realistic": await self._generate_realistic_scenario(forecasting_data["forecasts"]),
                "pessimistic": await self._generate_pessimistic_scenario(forecasting_data["forecasts"])
            }
            
            # Add forecasting assumptions
            forecasting_data["assumptions"] = [
                "Historical trend patterns continue",
                "No major market disruptions",
                "Current growth strategies remain effective",
                "FIRS grant program continues as planned",
                "SI customer acquisition rates remain stable"
            ]
            
            return forecasting_data
            
        except Exception as e:
            self.logger.error(f"Error generating revenue forecasting: {str(e)}")
            return {}

    async def get_milestone_dashboard(self, tenant_id: str) -> Dict[str, Any]:
        """Get comprehensive milestone dashboard for APP tenant"""
        try:
            dashboard_data = {
                "tenant_id": tenant_id,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "milestones": {},
                "overall_progress": 0.0,
                "total_potential_grants": 1550000.0,  # Sum of all milestone grants
                "achieved_grants": 0.0,
                "next_milestone": None,
                "recommendations": []
            }
            
            milestone_kpis = [
                "firs_milestone_1_progress",
                "firs_milestone_2_progress", 
                "firs_milestone_3_progress",
                "firs_milestone_4_progress",
                "firs_milestone_5_progress"
            ]
            
            achieved_count = 0
            total_progress = 0.0
            
            for kpi_id in milestone_kpis:
                # Get latest calculation from cache
                cache_key = f"kpi_calc:{kpi_id}"
                kpi_data = await self.cache.get(cache_key)
                
                if kpi_data:
                    milestone_key = kpi_id.replace("firs_", "").replace("_progress", "")
                    progress = kpi_data.get("calculated_value", 0)
                    total_progress += progress
                    
                    if progress >= 100.0:
                        achieved_count += 1
                        milestone_grants = {
                            "milestone_1": 50000,
                            "milestone_2": 100000,
                            "milestone_3": 200000,
                            "milestone_4": 400000,
                            "milestone_5": 800000
                        }
                        dashboard_data["achieved_grants"] += milestone_grants.get(milestone_key, 0)
                    elif not dashboard_data["next_milestone"]:
                        dashboard_data["next_milestone"] = milestone_key
                    
                    dashboard_data["milestones"][milestone_key] = {
                        "progress_percentage": progress,
                        "status": kpi_data.get("status", "unknown"),
                        "trend": kpi_data.get("trend", "unknown"),
                        "achievement_date": kpi_data.get("metadata", {}).get("achievement_date"),
                        "is_achieved": progress >= 100.0
                    }
            
            dashboard_data["overall_progress"] = total_progress / len(milestone_kpis)
            
            # Generate overall recommendations
            dashboard_data["recommendations"] = await self._generate_dashboard_recommendations(dashboard_data)
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error generating milestone dashboard: {str(e)}")
            return {}
    
    async def _generate_dashboard_recommendations(self, dashboard_data: Dict[str, Any]) -> List[str]:
        """Generate dashboard-level recommendations"""
        recommendations = []
        
        try:
            overall_progress = dashboard_data.get("overall_progress", 0)
            next_milestone = dashboard_data.get("next_milestone")
            
            if overall_progress < 20:
                recommendations.extend([
                    "Focus on establishing strong foundation with initial taxpayer onboarding",
                    "Implement comprehensive taxpayer education programs",
                    "Build strategic partnerships to accelerate growth"
                ])
            elif overall_progress < 50:
                recommendations.extend([
                    "Scale onboarding processes and improve efficiency",
                    "Diversify taxpayer portfolio across sectors and sizes", 
                    "Implement performance monitoring and optimization"
                ])
            elif overall_progress < 80:
                recommendations.extend([
                    "Focus on compliance and sustainability measures",
                    "Prepare for grant application processes",
                    "Implement quality assurance and validation procedures"
                ])
            else:
                recommendations.extend([
                    "Maintain high performance standards",
                    "Complete final validation requirements",
                    "Prepare comprehensive grant documentation"
                ])
            
            if next_milestone:
                recommendations.append(f"Prioritize requirements for {next_milestone.replace('_', ' ').title()}")
            
        except Exception as e:
            self.logger.error(f"Error generating dashboard recommendations: {str(e)}")
        
        return recommendations
    
    # Phase 4 Helper Methods for Business Health Metrics and Forecasting
    
    def _status_to_score(self, status: KPIStatus) -> float:
        """Convert KPI status to numerical score"""
        status_scores = {
            KPIStatus.EXCELLENT: 100.0,
            KPIStatus.GOOD: 80.0,
            KPIStatus.FAIR: 60.0,
            KPIStatus.POOR: 40.0,
            KPIStatus.CRITICAL: 20.0,
            KPIStatus.UNKNOWN: 0.0
        }
        return status_scores.get(status, 0.0)
    
    def _calculate_revenue_diversification(self, si_calc: KPICalculation, app_calc: KPICalculation) -> Dict[str, Any]:
        """Calculate revenue diversification metrics"""
        try:
            if not si_calc or not app_calc:
                return {"score": 0.0, "status": "insufficient_data"}
            
            si_contribution = si_calc.calculated_value
            app_contribution = app_calc.calculated_value
            
            # Calculate diversification index (closer to 50/50 is better)
            ideal_ratio = 50.0
            si_deviation = abs(si_contribution - ideal_ratio)
            diversification_score = max(0, 100 - (si_deviation * 2))
            
            return {
                "score": diversification_score,
                "si_percentage": si_contribution,
                "app_percentage": app_contribution,
                "diversification_index": diversification_score,
                "status": "excellent" if diversification_score >= 80 else "good" if diversification_score >= 60 else "needs_improvement"
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating revenue diversification: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_revenue_stability(self, kpi_calculations: List[KPICalculation]) -> Dict[str, Any]:
        """Assess revenue stability based on trend analysis"""
        try:
            revenue_calcs = [calc for calc in kpi_calculations if "revenue" in calc.kpi_id]
            
            if not revenue_calcs:
                return {"score": 0.0, "status": "insufficient_data"}
            
            stability_factors = []
            for calc in revenue_calcs:
                if calc.trend == KPITrend.STABLE:
                    stability_factors.append(1.0)
                elif calc.trend == KPITrend.IMPROVING:
                    stability_factors.append(0.8)  # Growth is good but less stable
                elif calc.trend == KPITrend.DECLINING:
                    stability_factors.append(0.3)
                else:
                    stability_factors.append(0.5)
            
            stability_score = statistics.mean(stability_factors) * 100 if stability_factors else 0.0
            
            return {
                "score": stability_score,
                "trend_analysis": [calc.trend for calc in revenue_calcs],
                "volatility": self._calculate_volatility(revenue_calcs),
                "status": "stable" if stability_score >= 70 else "moderate" if stability_score >= 50 else "volatile"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing revenue stability: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_growth_trajectory(self, kpi_calculations: List[KPICalculation]) -> Dict[str, Any]:
        """Assess overall growth trajectory"""
        try:
            growth_indicators = [
                calc for calc in kpi_calculations 
                if calc.kpi_id in ["total_revenue", "revenue_per_user", "milestone_achievement_rate"]
            ]
            
            if not growth_indicators:
                return {"score": 0.0, "status": "insufficient_data"}
            
            improving_count = sum(1 for calc in growth_indicators if calc.trend == KPITrend.IMPROVING)
            stable_count = sum(1 for calc in growth_indicators if calc.trend == KPITrend.STABLE)
            declining_count = sum(1 for calc in growth_indicators if calc.trend == KPITrend.DECLINING)
            
            total_indicators = len(growth_indicators)
            growth_score = ((improving_count * 1.0) + (stable_count * 0.5) + (declining_count * 0.0)) / total_indicators * 100
            
            return {
                "score": growth_score,
                "improving_metrics": improving_count,
                "stable_metrics": stable_count,
                "declining_metrics": declining_count,
                "growth_momentum": "strong" if growth_score >= 75 else "moderate" if growth_score >= 50 else "weak"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing growth trajectory: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _calculate_volatility(self, calculations: List[KPICalculation]) -> float:
        """Calculate volatility metric from calculations"""
        try:
            if len(calculations) < 2:
                return 0.0
            
            values = [calc.calculated_value for calc in calculations]
            if not values or all(v == 0 for v in values):
                return 0.0
            
            mean_value = statistics.mean(values)
            if mean_value == 0:
                return 0.0
            
            variance = statistics.variance(values) if len(values) > 1 else 0.0
            volatility = (variance ** 0.5) / mean_value * 100  # Coefficient of variation as percentage
            
            return min(volatility, 100.0)  # Cap at 100%
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility: {str(e)}")
            return 0.0
    
    def _assess_retention_quality(self, churn_calc: KPICalculation) -> Dict[str, Any]:
        """Assess customer retention quality"""
        try:
            if not churn_calc:
                return {"score": 0.0, "status": "no_data"}
            
            churn_rate = churn_calc.calculated_value
            retention_rate = 100 - churn_rate
            
            quality_score = min(retention_rate, 100.0)
            
            return {
                "score": quality_score,
                "churn_rate": churn_rate,
                "retention_rate": retention_rate,
                "trend": churn_calc.trend,
                "quality_level": "excellent" if quality_score >= 95 else "good" if quality_score >= 90 else "needs_improvement"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing retention quality: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_acquisition_efficiency(self, cac_calc: KPICalculation, rpu_calc: KPICalculation) -> Dict[str, Any]:
        """Assess customer acquisition efficiency"""
        try:
            if not cac_calc or not rpu_calc:
                return {"score": 0.0, "status": "insufficient_data"}
            
            cac = cac_calc.calculated_value
            rpu = rpu_calc.calculated_value
            
            if cac == 0:
                return {"score": 100.0, "status": "excellent"}
            
            # Calculate CAC to RPU ratio (lower is better)
            cac_to_rpu_ratio = cac / rpu if rpu > 0 else float('inf')
            
            # Efficiency score: better when CAC is lower relative to RPU
            if cac_to_rpu_ratio <= 1.0:
                efficiency_score = 100.0
            elif cac_to_rpu_ratio <= 2.0:
                efficiency_score = 80.0
            elif cac_to_rpu_ratio <= 3.0:
                efficiency_score = 60.0
            elif cac_to_rpu_ratio <= 5.0:
                efficiency_score = 40.0
            else:
                efficiency_score = 20.0
            
            return {
                "score": efficiency_score,
                "cac": cac,
                "rpu": rpu,
                "cac_to_rpu_ratio": cac_to_rpu_ratio,
                "payback_period_months": cac_to_rpu_ratio,
                "efficiency_level": "excellent" if efficiency_score >= 80 else "good" if efficiency_score >= 60 else "needs_improvement"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing acquisition efficiency: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_customer_value(self, rpu_calc: KPICalculation) -> Dict[str, Any]:
        """Assess customer value metrics"""
        try:
            if not rpu_calc:
                return {"score": 0.0, "status": "no_data"}
            
            rpu = rpu_calc.calculated_value
            target_rpu = 250.0  # From KPI definition
            
            value_score = min((rpu / target_rpu) * 100, 150.0) if target_rpu > 0 else 0.0
            
            return {
                "score": min(value_score, 100.0),
                "current_rpu": rpu,
                "target_rpu": target_rpu,
                "performance_vs_target": (rpu / target_rpu * 100) if target_rpu > 0 else 0.0,
                "trend": rpu_calc.trend,
                "value_tier": "premium" if rpu >= 400 else "standard" if rpu >= 200 else "basic"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing customer value: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_grant_performance(self, milestone_calc: KPICalculation, roi_calc: KPICalculation) -> Dict[str, Any]:
        """Assess APP grant performance"""
        try:
            performance_data = {
                "score": 0.0,
                "milestone_progress": 0.0,
                "roi_performance": 0.0,
                "status": "insufficient_data"
            }
            
            if milestone_calc:
                performance_data["milestone_progress"] = milestone_calc.calculated_value
                performance_data["milestone_trend"] = milestone_calc.trend
            
            if roi_calc:
                performance_data["roi_performance"] = roi_calc.calculated_value
                performance_data["roi_trend"] = roi_calc.trend
            
            # Calculate combined performance score
            if milestone_calc and roi_calc:
                milestone_score = self._status_to_score(milestone_calc.status)
                roi_score = self._status_to_score(roi_calc.status)
                performance_data["score"] = (milestone_score * 0.6 + roi_score * 0.4)
                
                performance_data["status"] = (
                    "excellent" if performance_data["score"] >= 80 else
                    "good" if performance_data["score"] >= 60 else
                    "needs_improvement"
                )
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Error assessing grant performance: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_process_efficiency(self, kpi_calculations: List[KPICalculation]) -> Dict[str, Any]:
        """Assess overall process efficiency"""
        try:
            efficiency_indicators = [
                calc for calc in kpi_calculations 
                if calc.kpi_id in ["milestone_achievement_rate", "customer_acquisition_cost", "grant_roi"]
            ]
            
            if not efficiency_indicators:
                return {"score": 0.0, "status": "insufficient_data"}
            
            efficiency_scores = [self._status_to_score(calc.status) for calc in efficiency_indicators]
            average_efficiency = statistics.mean(efficiency_scores)
            
            return {
                "score": average_efficiency,
                "indicators_count": len(efficiency_indicators),
                "efficiency_distribution": {
                    status: sum(1 for calc in efficiency_indicators if calc.status == status)
                    for status in KPIStatus
                },
                "status": "efficient" if average_efficiency >= 75 else "moderate" if average_efficiency >= 50 else "inefficient"
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing process efficiency: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    def _assess_compliance_status(self, milestone_calc: KPICalculation) -> Dict[str, Any]:
        """Assess compliance status based on milestone achievement"""
        try:
            if not milestone_calc:
                return {"score": 0.0, "status": "no_data"}
            
            compliance_score = milestone_calc.calculated_value
            compliance_status = milestone_calc.status
            
            return {
                "score": compliance_score,
                "status": compliance_status,
                "trend": milestone_calc.trend,
                "compliance_level": (
                    "full_compliance" if compliance_score >= 90 else
                    "high_compliance" if compliance_score >= 75 else
                    "moderate_compliance" if compliance_score >= 50 else
                    "low_compliance"
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing compliance status: {str(e)}")
            return {"score": 0.0, "status": "error"}
    
    async def _identify_business_risk_factors(self, kpi_calculations: List[KPICalculation]) -> List[Dict[str, Any]]:
        """Identify business risk factors from KPI analysis"""
        try:
            risk_factors = []
            
            for calc in kpi_calculations:
                if calc.status == KPIStatus.CRITICAL:
                    risk_factors.append({
                        "type": "critical_performance",
                        "kpi": calc.kpi_id,
                        "severity": "high",
                        "description": f"Critical performance in {calc.kpi_id}",
                        "current_value": calc.calculated_value,
                        "impact": "immediate_attention_required"
                    })
                
                elif calc.trend == KPITrend.DECLINING:
                    risk_factors.append({
                        "type": "declining_trend",
                        "kpi": calc.kpi_id,
                        "severity": "medium",
                        "description": f"Declining trend in {calc.kpi_id}",
                        "current_value": calc.calculated_value,
                        "impact": "monitor_closely"
                    })
            
            # Add specific business logic risks
            churn_calc = next((calc for calc in kpi_calculations if calc.kpi_id == "churn_rate_si"), None)
            if churn_calc and churn_calc.calculated_value > 5.0:
                risk_factors.append({
                    "type": "high_customer_churn",
                    "kpi": "churn_rate_si",
                    "severity": "high",
                    "description": "High customer churn rate affecting revenue stability",
                    "current_value": churn_calc.calculated_value,
                    "impact": "revenue_risk"
                })
            
            cac_calc = next((calc for calc in kpi_calculations if calc.kpi_id == "customer_acquisition_cost"), None)
            rpu_calc = next((calc for calc in kpi_calculations if calc.kpi_id == "revenue_per_user"), None)
            if cac_calc and rpu_calc and cac_calc.calculated_value > rpu_calc.calculated_value * 3:
                risk_factors.append({
                    "type": "high_acquisition_cost",
                    "kpi": "customer_acquisition_cost",
                    "severity": "medium",
                    "description": "Customer acquisition cost is too high relative to revenue per user",
                    "current_value": cac_calc.calculated_value,
                    "impact": "profitability_risk"
                })
            
            return risk_factors
            
        except Exception as e:
            self.logger.error(f"Error identifying business risk factors: {str(e)}")
            return []
    
    def _determine_health_trend(self, kpi_calculations: List[KPICalculation]) -> str:
        """Determine overall business health trend"""
        try:
            if not kpi_calculations:
                return "unknown"
            
            improving_count = sum(1 for calc in kpi_calculations if calc.trend == KPITrend.IMPROVING)
            stable_count = sum(1 for calc in kpi_calculations if calc.trend == KPITrend.STABLE)
            declining_count = sum(1 for calc in kpi_calculations if calc.trend == KPITrend.DECLINING)
            
            total_count = len(kpi_calculations)
            
            improving_ratio = improving_count / total_count
            declining_ratio = declining_count / total_count
            
            if improving_ratio >= 0.6:
                return "improving"
            elif declining_ratio >= 0.6:
                return "declining"
            elif improving_ratio > declining_ratio:
                return "moderately_improving"
            elif declining_ratio > improving_ratio:
                return "moderately_declining"
            else:
                return "stable"
                
        except Exception as e:
            self.logger.error(f"Error determining health trend: {str(e)}")
            return "unknown"
    
    async def _apply_forecasting_algorithms(self, historical_data: List[KPICalculation], metric_name: str) -> Dict[str, Any]:
        """Apply multiple forecasting algorithms to historical data"""
        try:
            if len(historical_data) < 2:
                return {"error": "insufficient_data"}
            
            values = [calc.calculated_value for calc in historical_data]
            timestamps = [calc.calculation_time for calc in historical_data]
            
            # Linear regression forecast
            linear_forecast = self._linear_regression_forecast(values, 3)  # 3 months ahead
            
            # Exponential smoothing forecast
            exp_smoothing_forecast = self._exponential_smoothing_forecast(values, 3)
            
            # Trend analysis forecast
            trend_forecast = self._trend_analysis_forecast(values, 3)
            
            # Combine forecasts with weights
            combined_forecast = []
            for i in range(3):
                weighted_value = (
                    linear_forecast[i] * 0.4 +
                    exp_smoothing_forecast[i] * 0.4 +
                    trend_forecast[i] * 0.2
                )
                combined_forecast.append(weighted_value)
            
            return {
                "metric": metric_name,
                "historical_values": values,
                "forecasts": {
                    "linear_regression": linear_forecast,
                    "exponential_smoothing": exp_smoothing_forecast,
                    "trend_analysis": trend_forecast,
                    "combined": combined_forecast
                },
                "confidence_intervals": self._calculate_confidence_intervals(values, combined_forecast),
                "forecast_accuracy": self._estimate_forecast_accuracy(historical_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error applying forecasting algorithms: {str(e)}")
            return {"error": str(e)}
    
    def _linear_regression_forecast(self, values: List[float], periods: int) -> List[float]:
        """Simple linear regression forecast"""
        try:
            if len(values) < 2:
                return [values[-1]] * periods if values else [0.0] * periods
            
            n = len(values)
            x_vals = list(range(n))
            
            # Calculate slope and intercept
            x_mean = statistics.mean(x_vals)
            y_mean = statistics.mean(values)
            
            numerator = sum((x_vals[i] - x_mean) * (values[i] - y_mean) for i in range(n))
            denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))
            
            if denominator == 0:
                return [y_mean] * periods
            
            slope = numerator / denominator
            intercept = y_mean - slope * x_mean
            
            # Generate forecasts
            forecasts = []
            for i in range(periods):
                forecast_x = n + i
                forecast_y = slope * forecast_x + intercept
                forecasts.append(max(0, forecast_y))  # Ensure non-negative
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error in linear regression forecast: {str(e)}")
            return [values[-1] if values else 0.0] * periods
    
    def _exponential_smoothing_forecast(self, values: List[float], periods: int, alpha: float = 0.3) -> List[float]:
        """Exponential smoothing forecast"""
        try:
            if not values:
                return [0.0] * periods
            
            if len(values) == 1:
                return [values[0]] * periods
            
            # Calculate exponentially smoothed values
            smoothed = [values[0]]
            for i in range(1, len(values)):
                smoothed_value = alpha * values[i] + (1 - alpha) * smoothed[-1]
                smoothed.append(smoothed_value)
            
            # Forecast using last smoothed value
            last_smoothed = smoothed[-1]
            forecasts = [last_smoothed] * periods
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error in exponential smoothing forecast: {str(e)}")
            return [values[-1] if values else 0.0] * periods
    
    def _trend_analysis_forecast(self, values: List[float], periods: int) -> List[float]:
        """Trend analysis forecast based on recent growth rate"""
        try:
            if len(values) < 2:
                return [values[-1] if values else 0.0] * periods
            
            # Calculate recent growth rate (last 3 periods if available)
            recent_periods = min(3, len(values))
            recent_values = values[-recent_periods:]
            
            if len(recent_values) < 2:
                return [values[-1]] * periods
            
            # Calculate average growth rate
            growth_rates = []
            for i in range(1, len(recent_values)):
                if recent_values[i-1] != 0:
                    growth_rate = (recent_values[i] - recent_values[i-1]) / recent_values[i-1]
                    growth_rates.append(growth_rate)
            
            if not growth_rates:
                return [values[-1]] * periods
            
            avg_growth_rate = statistics.mean(growth_rates)
            
            # Generate forecasts
            forecasts = []
            current_value = values[-1]
            
            for _ in range(periods):
                forecast_value = current_value * (1 + avg_growth_rate)
                forecasts.append(max(0, forecast_value))
                current_value = forecast_value
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis forecast: {str(e)}")
            return [values[-1] if values else 0.0] * periods
    
    def _calculate_confidence_intervals(self, historical_values: List[float], forecasts: List[float]) -> Dict[str, List[float]]:
        """Calculate confidence intervals for forecasts"""
        try:
            if len(historical_values) < 2:
                return {"lower_bound": forecasts, "upper_bound": forecasts}
            
            # Calculate historical volatility
            volatility = self._calculate_volatility_from_values(historical_values)
            
            # Apply confidence intervals (±1.96 standard deviations for 95% confidence)
            confidence_factor = 1.96 * (volatility / 100)
            
            lower_bound = [max(0, forecast * (1 - confidence_factor)) for forecast in forecasts]
            upper_bound = [forecast * (1 + confidence_factor) for forecast in forecasts]
            
            return {
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence intervals: {str(e)}")
            return {"lower_bound": forecasts, "upper_bound": forecasts}
    
    def _calculate_volatility_from_values(self, values: List[float]) -> float:
        """Calculate volatility from list of values"""
        try:
            if len(values) < 2:
                return 0.0
            
            mean_value = statistics.mean(values)
            if mean_value == 0:
                return 0.0
            
            variance = statistics.variance(values)
            volatility = (variance ** 0.5) / mean_value * 100
            
            return min(volatility, 100.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility from values: {str(e)}")
            return 0.0
    
    def _estimate_forecast_accuracy(self, historical_data: List[KPICalculation]) -> Dict[str, float]:
        """Estimate forecast accuracy based on historical performance"""
        try:
            if len(historical_data) < 3:
                return {"accuracy": 0.7, "confidence": 0.5}
            
            # Simple accuracy estimation based on trend consistency
            trends = [calc.trend for calc in historical_data]
            confidence_levels = [calc.confidence_level for calc in historical_data]
            
            # Calculate trend consistency
            stable_trends = sum(1 for trend in trends if trend in [KPITrend.STABLE, KPITrend.IMPROVING])
            trend_consistency = stable_trends / len(trends)
            
            # Calculate average confidence
            avg_confidence = statistics.mean(confidence_levels)
            
            # Estimate accuracy based on consistency and confidence
            estimated_accuracy = (trend_consistency * 0.6 + avg_confidence * 0.4)
            
            return {
                "accuracy": min(max(estimated_accuracy, 0.5), 0.95),  # Between 50% and 95%
                "confidence": avg_confidence,
                "trend_consistency": trend_consistency
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating forecast accuracy: {str(e)}")
            return {"accuracy": 0.7, "confidence": 0.5}
    
    async def _generate_optimistic_scenario(self, forecasts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimistic scenario with 20% uplift"""
        return {
            metric: {
                "values": [value * 1.2 for value in data.get("forecasts", {}).get("combined", [])],
                "assumptions": ["Strong market conditions", "Accelerated growth", "Optimal performance"]
            }
            for metric, data in forecasts.items()
            if isinstance(data, dict) and "forecasts" in data
        }
    
    async def _generate_realistic_scenario(self, forecasts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic scenario using combined forecasts"""
        return {
            metric: {
                "values": data.get("forecasts", {}).get("combined", []),
                "assumptions": ["Current trends continue", "Moderate market conditions", "Steady growth"]
            }
            for metric, data in forecasts.items()
            if isinstance(data, dict) and "forecasts" in data
        }
    
    async def _generate_pessimistic_scenario(self, forecasts: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pessimistic scenario with 15% decline"""
        return {
            metric: {
                "values": [value * 0.85 for value in data.get("forecasts", {}).get("combined", [])],
                "assumptions": ["Market challenges", "Slower growth", "Conservative estimates"]
            }
            for metric, data in forecasts.items()
            if isinstance(data, dict) and "forecasts" in data
        }
    
    async def get_kpi_summary(self) -> Dict[str, Any]:
        """Get KPI summary"""
        try:
            return {
                "total_kpis_defined": len(self.kpi_definitions),
                "kpis_by_category": {
                    category: len([
                        kpi for kpi in self.kpi_definitions.values()
                        if kpi.category == category
                    ])
                    for category in KPICategory
                },
                "kpis_by_type": {
                    kpi_type: len([
                        kpi for kpi in self.kpi_definitions.values()
                        if kpi.kpi_type == kpi_type
                    ])
                    for kpi_type in KPIType
                },
                "total_targets_set": sum(len(targets) for targets in self.kpi_targets.values()),
                "calculation_history_size": sum(len(history) for history in self.calculation_history.values()),
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting KPI summary: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            unified_metrics_health = await self.unified_metrics.health_check()
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "kpi_calculator",
                "components": {
                    "unified_metrics": unified_metrics_health,
                    "cache": cache_health,
                    "event_bus": {"status": "healthy"}
                },
                "metrics": {
                    "total_kpis": len(self.kpi_definitions),
                    "total_targets": sum(len(targets) for targets in self.kpi_targets.values()),
                    "calculation_history": len(self.calculation_history)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "kpi_calculator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("KPI calculator service cleanup initiated")
        
        try:
            # Clear caches
            self.calculation_history.clear()
            self.kpi_targets.clear()
            
            # Cleanup dependencies
            await self.unified_metrics.cleanup()
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("KPI calculator service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_kpi_calculator(unified_metrics: UnifiedMetrics = None) -> KPICalculator:
    """Create KPI calculator service"""
    return KPICalculator(unified_metrics)