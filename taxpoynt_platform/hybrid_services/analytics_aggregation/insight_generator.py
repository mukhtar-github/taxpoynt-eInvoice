"""
Hybrid Service: Insight Generator
Generates business insights from cross-role analytics data
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import statistics
import math

from core_platform.database import get_db_session
from core_platform.models.insights import BusinessInsight, InsightRule, InsightExecution, InsightReport
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.ai import AIService

from .unified_metrics import UnifiedMetrics, MetricScope, MetricType, AggregatedMetric
from .kpi_calculator import KPICalculator, KPICalculation, KPICategory
from .trend_analyzer import TrendAnalyzer, TrendAnalysis, TrendDirection, TrendStrength
from .cross_role_reporting import CrossRoleReporting

logger = logging.getLogger(__name__)


class InsightType(str, Enum):
    """Types of business insights"""
    PERFORMANCE = "performance"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    PREDICTIVE = "predictive"
    ANOMALY = "anomaly"
    OPPORTUNITY = "opportunity"
    RISK = "risk"
    RECOMMENDATION = "recommendation"
    STRATEGIC = "strategic"


class InsightSeverity(str, Enum):
    """Insight severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InsightCategory(str, Enum):
    """Insight categories"""
    IMMEDIATE_ACTION = "immediate_action"
    STRATEGIC_PLANNING = "strategic_planning"
    OPTIMIZATION = "optimization"
    MONITORING = "monitoring"
    FORECAST = "forecast"
    BENCHMARK = "benchmark"


class InsightConfidence(str, Enum):
    """Insight confidence levels"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class InsightStatus(str, Enum):
    """Insight status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    ACTED_UPON = "acted_upon"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


@dataclass
class InsightRule:
    """Rule for generating insights"""
    rule_id: str
    name: str
    description: str
    insight_type: InsightType
    category: InsightCategory
    conditions: List[Dict[str, Any]]
    threshold_conditions: Dict[str, Any]
    data_requirements: List[str]
    execution_frequency: str
    priority: int
    enabled: bool = True
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DataContext:
    """Context data for insight generation"""
    context_id: str
    metrics: Dict[str, AggregatedMetric]
    kpis: Dict[str, KPICalculation]
    trends: Dict[str, TrendAnalysis]
    time_range: Tuple[datetime, datetime]
    additional_data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessInsight:
    """Generated business insight"""
    insight_id: str
    insight_type: InsightType
    category: InsightCategory
    severity: InsightSeverity
    confidence: InsightConfidence
    title: str
    description: str
    supporting_data: Dict[str, Any]
    recommendations: List[str]
    potential_impact: Dict[str, Any]
    time_sensitivity: str
    generated_time: datetime
    source_rule: Optional[str] = None
    status: InsightStatus = InsightStatus.ACTIVE
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InsightExecution:
    """Insight generation execution record"""
    execution_id: str
    execution_time: datetime
    rules_executed: List[str]
    insights_generated: List[str]
    data_context: DataContext
    execution_duration: float
    success: bool
    errors: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InsightReport:
    """Comprehensive insight report"""
    report_id: str
    report_name: str
    generation_time: datetime
    time_range: Tuple[datetime, datetime]
    insights: List[BusinessInsight]
    summary: Dict[str, Any]
    key_findings: List[str]
    strategic_recommendations: List[str]
    next_steps: List[str]
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InsightGenerator:
    """
    Insight Generator service
    Generates business insights from cross-role analytics data
    """
    
    def __init__(
        self,
        unified_metrics: UnifiedMetrics = None,
        kpi_calculator: KPICalculator = None,
        trend_analyzer: TrendAnalyzer = None,
        cross_role_reporting: CrossRoleReporting = None
    ):
        """Initialize insight generator service"""
        self.unified_metrics = unified_metrics or UnifiedMetrics()
        self.kpi_calculator = kpi_calculator or KPICalculator()
        self.trend_analyzer = trend_analyzer or TrendAnalyzer()
        self.cross_role_reporting = cross_role_reporting or CrossRoleReporting()
        
        self.cache = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.ai_service = AIService()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.insight_rules: Dict[str, InsightRule] = {}
        self.generated_insights: Dict[str, BusinessInsight] = {}
        self.execution_history: List[InsightExecution] = []
        self.insight_reports: Dict[str, InsightReport] = {}
        self.is_initialized = False
        
        # Configuration
        self.cache_ttl = 3600  # 1 hour
        self.max_insights_per_execution = 50
        self.insight_retention_days = 30
        self.execution_interval = 1800  # 30 minutes
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default insight rules"""
        default_rules = [
            # Performance insights
            InsightRule(
                rule_id="performance_degradation",
                name="Performance Degradation Detection",
                description="Detect significant performance degradation across SI and APP",
                insight_type=InsightType.PERFORMANCE,
                category=InsightCategory.IMMEDIATE_ACTION,
                conditions=[
                    {"metric": "e2e_processing_time", "operator": "increase", "threshold": 20, "unit": "percentage"},
                    {"metric": "cross_role_success_rate", "operator": "decrease", "threshold": 5, "unit": "percentage"}
                ],
                threshold_conditions={
                    "time_window": "1h",
                    "min_data_points": 10,
                    "confidence_threshold": 0.8
                },
                data_requirements=["metrics", "trends"],
                execution_frequency="every_30_minutes",
                priority=1
            ),
            
            # Operational insights
            InsightRule(
                rule_id="capacity_utilization",
                name="Capacity Utilization Analysis",
                description="Analyze system capacity utilization and predict bottlenecks",
                insight_type=InsightType.OPERATIONAL,
                category=InsightCategory.OPTIMIZATION,
                conditions=[
                    {"metric": "unified_throughput", "operator": "above", "threshold": 80, "unit": "percentage"},
                    {"trend": "unified_throughput", "direction": "upward", "strength": "strong"}
                ],
                threshold_conditions={
                    "time_window": "4h",
                    "trend_confidence": 0.7
                },
                data_requirements=["metrics", "trends", "kpis"],
                execution_frequency="every_hour",
                priority=2
            ),
            
            # Financial insights
            InsightRule(
                rule_id="revenue_impact",
                name="Revenue Impact Analysis",
                description="Analyze revenue impact of performance and operational changes",
                insight_type=InsightType.FINANCIAL,
                category=InsightCategory.STRATEGIC_PLANNING,
                conditions=[
                    {"kpi": "revenue_per_transaction", "operator": "change", "threshold": 10, "unit": "percentage"},
                    {"metric": "transaction_volume", "operator": "change", "threshold": 15, "unit": "percentage"}
                ],
                threshold_conditions={
                    "time_window": "24h",
                    "significance_level": 0.05
                },
                data_requirements=["kpis", "metrics", "trends"],
                execution_frequency="every_4_hours",
                priority=3
            ),
            
            # Compliance insights
            InsightRule(
                rule_id="compliance_risk",
                name="Compliance Risk Assessment",
                description="Assess compliance risks and regulatory adherence",
                insight_type=InsightType.COMPLIANCE,
                category=InsightCategory.IMMEDIATE_ACTION,
                conditions=[
                    {"kpi": "regulatory_compliance_rate", "operator": "below", "threshold": 95, "unit": "percentage"},
                    {"metric": "unified_compliance_score", "operator": "below", "threshold": 85, "unit": "percentage"}
                ],
                threshold_conditions={
                    "time_window": "1h",
                    "min_violations": 1
                },
                data_requirements=["kpis", "metrics"],
                execution_frequency="every_15_minutes",
                priority=1
            ),
            
            # Predictive insights
            InsightRule(
                rule_id="predictive_scaling",
                name="Predictive Scaling Recommendations",
                description="Predict scaling needs based on trend analysis",
                insight_type=InsightType.PREDICTIVE,
                category=InsightCategory.STRATEGIC_PLANNING,
                conditions=[
                    {"trend": "unified_throughput", "direction": "upward", "strength": "strong"},
                    {"prediction": "unified_throughput", "horizon": "7d", "increase": 30, "unit": "percentage"}
                ],
                threshold_conditions={
                    "prediction_confidence": 0.8,
                    "time_horizon": "7d"
                },
                data_requirements=["trends", "predictions"],
                execution_frequency="every_12_hours",
                priority=2
            ),
            
            # Anomaly insights
            InsightRule(
                rule_id="anomaly_detection",
                name="System Anomaly Detection",
                description="Detect and analyze system anomalies",
                insight_type=InsightType.ANOMALY,
                category=InsightCategory.MONITORING,
                conditions=[
                    {"anomaly_count": "any_metric", "operator": "above", "threshold": 3, "unit": "count"},
                    {"anomaly_severity": "any_metric", "operator": "above", "threshold": "medium", "unit": "level"}
                ],
                threshold_conditions={
                    "time_window": "2h",
                    "anomaly_clustering": True
                },
                data_requirements=["trends", "anomalies"],
                execution_frequency="every_30_minutes",
                priority=2
            ),
            
            # Opportunity insights
            InsightRule(
                rule_id="optimization_opportunity",
                name="Optimization Opportunities",
                description="Identify opportunities for system optimization",
                insight_type=InsightType.OPPORTUNITY,
                category=InsightCategory.OPTIMIZATION,
                conditions=[
                    {"kpi": "system_efficiency", "operator": "below", "threshold": 90, "unit": "percentage"},
                    {"metric": "resource_utilization", "operator": "below", "threshold": 70, "unit": "percentage"}
                ],
                threshold_conditions={
                    "time_window": "6h",
                    "consistency_check": True
                },
                data_requirements=["kpis", "metrics"],
                execution_frequency="every_6_hours",
                priority=3
            ),
            
            # Risk insights
            InsightRule(
                rule_id="operational_risk",
                name="Operational Risk Assessment",
                description="Assess operational risks and vulnerabilities",
                insight_type=InsightType.RISK,
                category=InsightCategory.IMMEDIATE_ACTION,
                conditions=[
                    {"kpi": "system_availability", "operator": "below", "threshold": 99, "unit": "percentage"},
                    {"trend": "error_rate", "direction": "upward", "strength": "moderate"}
                ],
                threshold_conditions={
                    "time_window": "2h",
                    "risk_threshold": "medium"
                },
                data_requirements=["kpis", "trends", "metrics"],
                execution_frequency="every_hour",
                priority=1
            )
        ]
        
        for rule in default_rules:
            self.insight_rules[rule.rule_id] = rule
    
    async def initialize(self):
        """Initialize the insight generator service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing insight generator service")
        
        try:
            # Initialize dependencies
            await self.unified_metrics.initialize()
            await self.kpi_calculator.initialize()
            await self.trend_analyzer.initialize()
            await self.cross_role_reporting.initialize()
            await self.cache.initialize()
            await self.ai_service.initialize()
            
            # Start periodic insight generation
            asyncio.create_task(self._periodic_insight_generation())
            
            # Start cleanup task
            asyncio.create_task(self._cleanup_old_insights())
            
            # Register event handlers
            await self._register_event_handlers()
            
            self.is_initialized = True
            self.logger.info("Insight generator service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing insight generator service: {str(e)}")
            raise
    
    async def register_insight_rule(self, rule: InsightRule):
        """Register a new insight rule"""
        try:
            self.insight_rules[rule.rule_id] = rule
            
            # Cache the rule
            await self.cache.set(
                f"insight_rule:{rule.rule_id}",
                rule.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Registered insight rule: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"Error registering insight rule: {str(e)}")
            raise
    
    async def generate_insights(
        self,
        time_range: Tuple[datetime, datetime],
        rule_ids: List[str] = None,
        include_predictions: bool = True
    ) -> InsightExecution:
        """Generate insights based on rules and data"""
        try:
            execution_start = datetime.now(timezone.utc)
            
            # Determine rules to execute
            if rule_ids:
                rules_to_execute = [r for r in self.insight_rules.values() if r.rule_id in rule_ids]
            else:
                rules_to_execute = [r for r in self.insight_rules.values() if r.enabled]
            
            # Gather data context
            data_context = await self._gather_data_context(time_range, include_predictions)
            
            # Execute rules and generate insights
            generated_insights = []
            execution_errors = []
            
            for rule in rules_to_execute:
                try:
                    insights = await self._execute_rule(rule, data_context)
                    generated_insights.extend(insights)
                except Exception as e:
                    execution_errors.append(f"Rule {rule.rule_id}: {str(e)}")
                    self.logger.error(f"Error executing rule {rule.rule_id}: {str(e)}")
            
            # AI-enhanced insights
            if self.ai_service.is_available():
                try:
                    ai_insights = await self._generate_ai_insights(data_context)
                    generated_insights.extend(ai_insights)
                except Exception as e:
                    execution_errors.append(f"AI insights: {str(e)}")
                    self.logger.error(f"Error generating AI insights: {str(e)}")
            
            # Store insights
            for insight in generated_insights:
                self.generated_insights[insight.insight_id] = insight
            
            # Create execution record
            execution_duration = (datetime.now(timezone.utc) - execution_start).total_seconds()
            
            execution = InsightExecution(
                execution_id=str(uuid.uuid4()),
                execution_time=execution_start,
                rules_executed=[r.rule_id for r in rules_to_execute],
                insights_generated=[i.insight_id for i in generated_insights],
                data_context=data_context,
                execution_duration=execution_duration,
                success=len(execution_errors) == 0,
                errors=execution_errors,
                metadata={
                    "rules_count": len(rules_to_execute),
                    "insights_count": len(generated_insights),
                    "data_points": len(data_context.metrics) + len(data_context.kpis) + len(data_context.trends)
                }
            )
            
            self.execution_history.append(execution)
            
            # Send notifications for critical insights
            await self._send_critical_notifications(generated_insights)
            
            self.logger.info(f"Generated {len(generated_insights)} insights in {execution_duration:.2f}s")
            
            return execution
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {str(e)}")
            raise
    
    async def get_insights(
        self,
        insight_type: InsightType = None,
        category: InsightCategory = None,
        severity: InsightSeverity = None,
        time_range: Tuple[datetime, datetime] = None,
        limit: int = 50
    ) -> List[BusinessInsight]:
        """Get insights with filtering"""
        try:
            insights = list(self.generated_insights.values())
            
            # Apply filters
            if insight_type:
                insights = [i for i in insights if i.insight_type == insight_type]
            
            if category:
                insights = [i for i in insights if i.category == category]
            
            if severity:
                insights = [i for i in insights if i.severity == severity]
            
            if time_range:
                insights = [i for i in insights if time_range[0] <= i.generated_time <= time_range[1]]
            
            # Sort by generation time (newest first) and severity
            severity_order = {
                InsightSeverity.CRITICAL: 0,
                InsightSeverity.HIGH: 1,
                InsightSeverity.MEDIUM: 2,
                InsightSeverity.LOW: 3,
                InsightSeverity.INFO: 4
            }
            
            insights.sort(key=lambda x: (severity_order.get(x.severity, 5), x.generated_time), reverse=True)
            
            return insights[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting insights: {str(e)}")
            return []
    
    async def generate_insight_report(
        self,
        time_range: Tuple[datetime, datetime],
        report_name: str = "Business Insights Report"
    ) -> InsightReport:
        """Generate comprehensive insight report"""
        try:
            # Get insights for the time range
            insights = await self.get_insights(time_range=time_range, limit=100)
            
            # Create summary
            summary = await self._create_insight_summary(insights)
            
            # Extract key findings
            key_findings = await self._extract_key_findings(insights)
            
            # Generate strategic recommendations
            strategic_recommendations = await self._generate_strategic_recommendations(insights)
            
            # Define next steps
            next_steps = await self._define_next_steps(insights)
            
            # Create report
            report = InsightReport(
                report_id=str(uuid.uuid4()),
                report_name=report_name,
                generation_time=datetime.now(timezone.utc),
                time_range=time_range,
                insights=insights,
                summary=summary,
                key_findings=key_findings,
                strategic_recommendations=strategic_recommendations,
                next_steps=next_steps,
                metadata={
                    "insights_analyzed": len(insights),
                    "time_period": {
                        "start": time_range[0].isoformat(),
                        "end": time_range[1].isoformat(),
                        "duration_hours": (time_range[1] - time_range[0]).total_seconds() / 3600
                    }
                }
            )
            
            # Store report
            self.insight_reports[report.report_id] = report
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating insight report: {str(e)}")
            raise
    
    async def update_insight_status(self, insight_id: str, status: InsightStatus, notes: str = None):
        """Update insight status"""
        try:
            if insight_id not in self.generated_insights:
                raise ValueError(f"Insight not found: {insight_id}")
            
            insight = self.generated_insights[insight_id]
            insight.status = status
            
            if notes:
                if not insight.metadata:
                    insight.metadata = {}
                insight.metadata["status_notes"] = notes
                insight.metadata["status_updated"] = datetime.now(timezone.utc).isoformat()
            
            # Update cache
            await self.cache.set(
                f"insight:{insight_id}",
                insight.to_dict(),
                ttl=self.cache_ttl
            )
            
            self.logger.info(f"Updated insight {insight_id} status to {status}")
            
        except Exception as e:
            self.logger.error(f"Error updating insight status: {str(e)}")
            raise
    
    async def _gather_data_context(
        self,
        time_range: Tuple[datetime, datetime],
        include_predictions: bool
    ) -> DataContext:
        """Gather data context for insight generation"""
        try:
            # Get metrics
            metrics = {}
            real_time_metrics = await self.unified_metrics.get_real_time_metrics()
            for metric in real_time_metrics:
                metrics[metric.metric_id] = metric
            
            # Get KPIs
            kpis = {}
            kpi_dashboard = await self.kpi_calculator.get_kpi_dashboard(time_range=time_range)
            for kpi_calc in kpi_dashboard.kpi_calculations:
                kpis[kpi_calc.kpi_id] = kpi_calc
            
            # Get trends
            trends = {}
            for metric_id in list(metrics.keys())[:10]:  # Limit for performance
                try:
                    trend_analysis = await self.trend_analyzer.analyze_metric_trend(
                        metric_id,
                        time_range
                    )
                    trends[metric_id] = trend_analysis
                except Exception as e:
                    self.logger.debug(f"Could not analyze trend for {metric_id}: {str(e)}")
            
            # Get predictions if requested
            predictions = {}
            if include_predictions:
                for metric_id in list(metrics.keys())[:5]:  # Limit for performance
                    try:
                        prediction = await self.trend_analyzer.predict_metric_trend(
                            metric_id,
                            time_range
                        )
                        predictions[metric_id] = prediction
                    except Exception as e:
                        self.logger.debug(f"Could not predict trend for {metric_id}: {str(e)}")
            
            return DataContext(
                context_id=str(uuid.uuid4()),
                metrics=metrics,
                kpis=kpis,
                trends=trends,
                time_range=time_range,
                additional_data={"predictions": predictions},
                metadata={
                    "metrics_count": len(metrics),
                    "kpis_count": len(kpis),
                    "trends_count": len(trends),
                    "predictions_count": len(predictions)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error gathering data context: {str(e)}")
            raise
    
    async def _execute_rule(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Execute a single insight rule"""
        try:
            insights = []
            
            # Check if rule conditions are met
            if not await self._check_rule_conditions(rule, data_context):
                return insights
            
            # Generate insight based on rule type
            if rule.insight_type == InsightType.PERFORMANCE:
                insights = await self._generate_performance_insights(rule, data_context)
            elif rule.insight_type == InsightType.OPERATIONAL:
                insights = await self._generate_operational_insights(rule, data_context)
            elif rule.insight_type == InsightType.FINANCIAL:
                insights = await self._generate_financial_insights(rule, data_context)
            elif rule.insight_type == InsightType.COMPLIANCE:
                insights = await self._generate_compliance_insights(rule, data_context)
            elif rule.insight_type == InsightType.PREDICTIVE:
                insights = await self._generate_predictive_insights(rule, data_context)
            elif rule.insight_type == InsightType.ANOMALY:
                insights = await self._generate_anomaly_insights(rule, data_context)
            elif rule.insight_type == InsightType.OPPORTUNITY:
                insights = await self._generate_opportunity_insights(rule, data_context)
            elif rule.insight_type == InsightType.RISK:
                insights = await self._generate_risk_insights(rule, data_context)
            else:
                insights = await self._generate_generic_insights(rule, data_context)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error executing rule {rule.rule_id}: {str(e)}")
            return []
    
    async def _check_rule_conditions(self, rule: InsightRule, data_context: DataContext) -> bool:
        """Check if rule conditions are met"""
        try:
            for condition in rule.conditions:
                if not await self._check_condition(condition, data_context):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking rule conditions: {str(e)}")
            return False
    
    async def _check_condition(self, condition: Dict[str, Any], data_context: DataContext) -> bool:
        """Check a single condition"""
        try:
            condition_type = list(condition.keys())[0]
            
            if condition_type == "metric":
                metric_id = condition["metric"]
                operator = condition["operator"]
                threshold = condition["threshold"]
                
                if metric_id not in data_context.metrics:
                    return False
                
                metric = data_context.metrics[metric_id]
                current_value = metric.aggregated_value
                
                if operator == "above":
                    return current_value > threshold
                elif operator == "below":
                    return current_value < threshold
                elif operator == "increase":
                    # Check for increase (simplified)
                    return True  # Implement proper increase check
                elif operator == "decrease":
                    # Check for decrease (simplified)
                    return True  # Implement proper decrease check
                
            elif condition_type == "kpi":
                kpi_id = condition["kpi"]
                operator = condition["operator"]
                threshold = condition["threshold"]
                
                if kpi_id not in data_context.kpis:
                    return False
                
                kpi = data_context.kpis[kpi_id]
                current_value = kpi.calculated_value
                
                if operator == "above":
                    return current_value > threshold
                elif operator == "below":
                    return current_value < threshold
                elif operator == "change":
                    # Check for significant change (simplified)
                    return True  # Implement proper change check
                
            elif condition_type == "trend":
                trend_id = condition["trend"]
                direction = condition.get("direction")
                strength = condition.get("strength")
                
                if trend_id not in data_context.trends:
                    return False
                
                trend = data_context.trends[trend_id]
                
                if direction and trend.primary_trend:
                    if trend.primary_trend.direction.value != direction:
                        return False
                
                if strength and trend.primary_trend:
                    if trend.primary_trend.strength.value != strength:
                        return False
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking condition: {str(e)}")
            return False
    
    async def _generate_performance_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate performance-related insights"""
        try:
            insights = []
            
            # Check for performance degradation
            if rule.rule_id == "performance_degradation":
                for metric_id, metric in data_context.metrics.items():
                    if metric_id == "e2e_processing_time" and metric.aggregated_value > 5000:  # 5 seconds
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.PERFORMANCE,
                            category=InsightCategory.IMMEDIATE_ACTION,
                            severity=InsightSeverity.HIGH,
                            confidence=InsightConfidence.HIGH,
                            title="Performance Degradation Detected",
                            description=f"End-to-end processing time has increased to {metric.aggregated_value:.2f}ms",
                            supporting_data={
                                "metric_id": metric_id,
                                "current_value": metric.aggregated_value,
                                "expected_range": "< 5000ms",
                                "confidence_level": metric.confidence_level
                            },
                            recommendations=[
                                "Investigate bottlenecks in processing pipeline",
                                "Review resource allocation",
                                "Consider scaling infrastructure",
                                "Analyze recent system changes"
                            ],
                            potential_impact={
                                "business_impact": "High - Customer experience degradation",
                                "revenue_impact": "Medium - Potential customer churn",
                                "operational_impact": "High - System efficiency reduction"
                            },
                            time_sensitivity="Immediate",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating performance insights: {str(e)}")
            return []
    
    async def _generate_operational_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate operational insights"""
        try:
            insights = []
            
            # Check for capacity utilization
            if rule.rule_id == "capacity_utilization":
                for metric_id, metric in data_context.metrics.items():
                    if metric_id == "unified_throughput" and metric.aggregated_value > 80:  # 80% capacity
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.OPERATIONAL,
                            category=InsightCategory.OPTIMIZATION,
                            severity=InsightSeverity.MEDIUM,
                            confidence=InsightConfidence.HIGH,
                            title="High Capacity Utilization",
                            description=f"System capacity utilization is at {metric.aggregated_value:.1f}%",
                            supporting_data={
                                "metric_id": metric_id,
                                "current_utilization": metric.aggregated_value,
                                "threshold": 80,
                                "trend": data_context.trends.get(metric_id, {})
                            },
                            recommendations=[
                                "Prepare for capacity scaling",
                                "Optimize resource allocation",
                                "Review peak usage patterns",
                                "Consider load balancing improvements"
                            ],
                            potential_impact={
                                "business_impact": "Medium - Service quality risk",
                                "revenue_impact": "Low - Preventive measure",
                                "operational_impact": "High - System stability"
                            },
                            time_sensitivity="Short term",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating operational insights: {str(e)}")
            return []
    
    async def _generate_financial_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate financial insights"""
        try:
            insights = []
            
            # Check for revenue impact
            if rule.rule_id == "revenue_impact":
                for kpi_id, kpi in data_context.kpis.items():
                    if kpi_id == "revenue_per_transaction" and kpi.calculated_value < 40:  # Below threshold
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.FINANCIAL,
                            category=InsightCategory.STRATEGIC_PLANNING,
                            severity=InsightSeverity.HIGH,
                            confidence=InsightConfidence.MEDIUM,
                            title="Revenue per Transaction Below Target",
                            description=f"Revenue per transaction is {kpi.calculated_value:.2f}, below target of 50",
                            supporting_data={
                                "kpi_id": kpi_id,
                                "current_value": kpi.calculated_value,
                                "target_value": 50,
                                "trend": kpi.trend,
                                "confidence": kpi.confidence_level
                            },
                            recommendations=[
                                "Analyze transaction value distribution",
                                "Review pricing strategy",
                                "Investigate transaction processing costs",
                                "Consider value-added services"
                            ],
                            potential_impact={
                                "business_impact": "High - Revenue optimization needed",
                                "revenue_impact": "High - Direct revenue impact",
                                "operational_impact": "Medium - Process improvements needed"
                            },
                            time_sensitivity="Medium term",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating financial insights: {str(e)}")
            return []
    
    async def _generate_compliance_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate compliance insights"""
        try:
            insights = []
            
            # Check for compliance risk
            if rule.rule_id == "compliance_risk":
                for kpi_id, kpi in data_context.kpis.items():
                    if kpi_id == "regulatory_compliance_rate" and kpi.calculated_value < 95:
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.COMPLIANCE,
                            category=InsightCategory.IMMEDIATE_ACTION,
                            severity=InsightSeverity.CRITICAL,
                            confidence=InsightConfidence.HIGH,
                            title="Compliance Rate Below Threshold",
                            description=f"Regulatory compliance rate is {kpi.calculated_value:.1f}%, below required 95%",
                            supporting_data={
                                "kpi_id": kpi_id,
                                "current_rate": kpi.calculated_value,
                                "required_rate": 95,
                                "compliance_gaps": kpi.target_comparison,
                                "trend": kpi.trend
                            },
                            recommendations=[
                                "Immediate compliance audit required",
                                "Review recent regulatory changes",
                                "Update compliance procedures",
                                "Provide compliance training",
                                "Implement monitoring improvements"
                            ],
                            potential_impact={
                                "business_impact": "Critical - Regulatory exposure",
                                "revenue_impact": "High - Potential fines and penalties",
                                "operational_impact": "High - Process remediation needed"
                            },
                            time_sensitivity="Immediate",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating compliance insights: {str(e)}")
            return []
    
    async def _generate_predictive_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate predictive insights"""
        try:
            insights = []
            
            # Check for predictive scaling needs
            if rule.rule_id == "predictive_scaling":
                predictions = data_context.additional_data.get("predictions", {})
                
                for metric_id, prediction in predictions.items():
                    if metric_id == "unified_throughput" and prediction.confidence in [
                        "high", "medium"
                    ]:
                        # Check if prediction shows significant increase
                        if prediction.predicted_values:
                            current_value = data_context.metrics.get(metric_id, {}).get("aggregated_value", 0)
                            future_value = prediction.predicted_values[-1].get("predicted_value", 0)
                            
                            if future_value > current_value * 1.3:  # 30% increase
                                insight = BusinessInsight(
                                    insight_id=str(uuid.uuid4()),
                                    insight_type=InsightType.PREDICTIVE,
                                    category=InsightCategory.STRATEGIC_PLANNING,
                                    severity=InsightSeverity.MEDIUM,
                                    confidence=InsightConfidence.HIGH,
                                    title="Predicted Capacity Scaling Need",
                                    description=f"Throughput predicted to increase by {((future_value - current_value) / current_value * 100):.1f}% over next 7 days",
                                    supporting_data={
                                        "metric_id": metric_id,
                                        "current_value": current_value,
                                        "predicted_value": future_value,
                                        "prediction_confidence": prediction.confidence,
                                        "prediction_horizon": "7 days"
                                    },
                                    recommendations=[
                                        "Prepare infrastructure scaling plan",
                                        "Review resource allocation strategy",
                                        "Consider auto-scaling implementation",
                                        "Monitor prediction accuracy"
                                    ],
                                    potential_impact={
                                        "business_impact": "Medium - Proactive capacity planning",
                                        "revenue_impact": "Low - Cost optimization",
                                        "operational_impact": "High - System preparedness"
                                    },
                                    time_sensitivity="Short term",
                                    generated_time=datetime.now(timezone.utc),
                                    source_rule=rule.rule_id
                                )
                                insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating predictive insights: {str(e)}")
            return []
    
    async def _generate_anomaly_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate anomaly insights"""
        try:
            insights = []
            
            # Check for anomalies in trends
            if rule.rule_id == "anomaly_detection":
                for trend_id, trend in data_context.trends.items():
                    if trend.anomalies and len(trend.anomalies) > 3:
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.ANOMALY,
                            category=InsightCategory.MONITORING,
                            severity=InsightSeverity.MEDIUM,
                            confidence=InsightConfidence.HIGH,
                            title="Multiple Anomalies Detected",
                            description=f"Detected {len(trend.anomalies)} anomalies in {trend_id}",
                            supporting_data={
                                "metric_id": trend_id,
                                "anomaly_count": len(trend.anomalies),
                                "anomalies": trend.anomalies[:5],  # Top 5 anomalies
                                "time_range": {
                                    "start": trend.analysis_period[0].isoformat(),
                                    "end": trend.analysis_period[1].isoformat()
                                }
                            },
                            recommendations=[
                                "Investigate anomaly patterns",
                                "Review data collection processes",
                                "Check for external factors",
                                "Implement anomaly monitoring"
                            ],
                            potential_impact={
                                "business_impact": "Medium - Data quality concerns",
                                "revenue_impact": "Low - Indirect impact",
                                "operational_impact": "Medium - System monitoring needed"
                            },
                            time_sensitivity="Medium term",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating anomaly insights: {str(e)}")
            return []
    
    async def _generate_opportunity_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate opportunity insights"""
        try:
            insights = []
            
            # Check for optimization opportunities
            if rule.rule_id == "optimization_opportunity":
                for kpi_id, kpi in data_context.kpis.items():
                    if kpi_id == "system_efficiency" and kpi.calculated_value < 90:
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.OPPORTUNITY,
                            category=InsightCategory.OPTIMIZATION,
                            severity=InsightSeverity.LOW,
                            confidence=InsightConfidence.MEDIUM,
                            title="System Efficiency Optimization Opportunity",
                            description=f"System efficiency at {kpi.calculated_value:.1f}% presents optimization opportunity",
                            supporting_data={
                                "kpi_id": kpi_id,
                                "current_efficiency": kpi.calculated_value,
                                "target_efficiency": 95,
                                "potential_improvement": 95 - kpi.calculated_value,
                                "trend": kpi.trend
                            },
                            recommendations=[
                                "Analyze efficiency bottlenecks",
                                "Review process optimization opportunities",
                                "Implement performance monitoring",
                                "Consider automation improvements"
                            ],
                            potential_impact={
                                "business_impact": "Medium - Performance improvement",
                                "revenue_impact": "Medium - Cost reduction potential",
                                "operational_impact": "High - Process efficiency"
                            },
                            time_sensitivity="Long term",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating opportunity insights: {str(e)}")
            return []
    
    async def _generate_risk_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate risk insights"""
        try:
            insights = []
            
            # Check for operational risks
            if rule.rule_id == "operational_risk":
                for kpi_id, kpi in data_context.kpis.items():
                    if kpi_id == "system_availability" and kpi.calculated_value < 99:
                        insight = BusinessInsight(
                            insight_id=str(uuid.uuid4()),
                            insight_type=InsightType.RISK,
                            category=InsightCategory.IMMEDIATE_ACTION,
                            severity=InsightSeverity.HIGH,
                            confidence=InsightConfidence.HIGH,
                            title="System Availability Risk",
                            description=f"System availability at {kpi.calculated_value:.2f}% below SLA of 99%",
                            supporting_data={
                                "kpi_id": kpi_id,
                                "current_availability": kpi.calculated_value,
                                "sla_target": 99.0,
                                "availability_gap": 99.0 - kpi.calculated_value,
                                "trend": kpi.trend
                            },
                            recommendations=[
                                "Immediate system stability review",
                                "Implement redundancy measures",
                                "Review incident response procedures",
                                "Enhance monitoring and alerting"
                            ],
                            potential_impact={
                                "business_impact": "High - Service delivery risk",
                                "revenue_impact": "High - SLA penalties and customer loss",
                                "operational_impact": "Critical - System reliability"
                            },
                            time_sensitivity="Immediate",
                            generated_time=datetime.now(timezone.utc),
                            source_rule=rule.rule_id
                        )
                        insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating risk insights: {str(e)}")
            return []
    
    async def _generate_generic_insights(self, rule: InsightRule, data_context: DataContext) -> List[BusinessInsight]:
        """Generate generic insights"""
        try:
            insights = []
            
            # Generic insight generation based on rule conditions
            insight = BusinessInsight(
                insight_id=str(uuid.uuid4()),
                insight_type=rule.insight_type,
                category=rule.category,
                severity=InsightSeverity.MEDIUM,
                confidence=InsightConfidence.MEDIUM,
                title=f"Insight: {rule.name}",
                description=rule.description,
                supporting_data={"rule_conditions": rule.conditions},
                recommendations=["Review the conditions that triggered this insight"],
                potential_impact={
                    "business_impact": "Medium - Requires attention",
                    "revenue_impact": "Unknown - Needs assessment",
                    "operational_impact": "Medium - Process review needed"
                },
                time_sensitivity="Medium term",
                generated_time=datetime.now(timezone.utc),
                source_rule=rule.rule_id
            )
            insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating generic insights: {str(e)}")
            return []
    
    async def _generate_ai_insights(self, data_context: DataContext) -> List[BusinessInsight]:
        """Generate AI-enhanced insights"""
        try:
            insights = []
            
            # Prepare data for AI analysis
            ai_data = {
                "metrics": {k: v.to_dict() for k, v in data_context.metrics.items()},
                "kpis": {k: v.to_dict() for k, v in data_context.kpis.items()},
                "trends": {k: v.to_dict() for k, v in data_context.trends.items()}
            }
            
            # Generate AI insights
            ai_response = await self.ai_service.generate_insights(ai_data)
            
            # Process AI response and create insights
            for ai_insight in ai_response.get("insights", []):
                insight = BusinessInsight(
                    insight_id=str(uuid.uuid4()),
                    insight_type=InsightType.STRATEGIC,
                    category=InsightCategory.STRATEGIC_PLANNING,
                    severity=InsightSeverity.MEDIUM,
                    confidence=InsightConfidence.MEDIUM,
                    title=ai_insight.get("title", "AI-Generated Insight"),
                    description=ai_insight.get("description", ""),
                    supporting_data=ai_insight.get("supporting_data", {}),
                    recommendations=ai_insight.get("recommendations", []),
                    potential_impact=ai_insight.get("potential_impact", {}),
                    time_sensitivity=ai_insight.get("time_sensitivity", "Medium term"),
                    generated_time=datetime.now(timezone.utc),
                    source_rule="ai_generated",
                    metadata={"ai_confidence": ai_insight.get("confidence", 0.5)}
                )
                insights.append(insight)
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {str(e)}")
            return []
    
    async def _create_insight_summary(self, insights: List[BusinessInsight]) -> Dict[str, Any]:
        """Create summary of insights"""
        try:
            if not insights:
                return {"total_insights": 0}
            
            # Count by type
            type_counts = {}
            for insight in insights:
                type_counts[insight.insight_type] = type_counts.get(insight.insight_type, 0) + 1
            
            # Count by severity
            severity_counts = {}
            for insight in insights:
                severity_counts[insight.severity] = severity_counts.get(insight.severity, 0) + 1
            
            # Count by category
            category_counts = {}
            for insight in insights:
                category_counts[insight.category] = category_counts.get(insight.category, 0) + 1
            
            # Critical insights
            critical_insights = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
            high_priority_insights = [i for i in insights if i.severity in [InsightSeverity.CRITICAL, InsightSeverity.HIGH]]
            
            return {
                "total_insights": len(insights),
                "type_distribution": type_counts,
                "severity_distribution": severity_counts,
                "category_distribution": category_counts,
                "critical_insights_count": len(critical_insights),
                "high_priority_insights_count": len(high_priority_insights),
                "average_confidence": statistics.mean([
                    {"very_high": 0.9, "high": 0.8, "medium": 0.6, "low": 0.4, "very_low": 0.2}.get(i.confidence, 0.5)
                    for i in insights
                ]),
                "time_sensitivity": {
                    "immediate": len([i for i in insights if i.time_sensitivity == "Immediate"]),
                    "short_term": len([i for i in insights if i.time_sensitivity == "Short term"]),
                    "medium_term": len([i for i in insights if i.time_sensitivity == "Medium term"]),
                    "long_term": len([i for i in insights if i.time_sensitivity == "Long term"])
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error creating insight summary: {str(e)}")
            return {"total_insights": 0, "error": str(e)}
    
    async def _extract_key_findings(self, insights: List[BusinessInsight]) -> List[str]:
        """Extract key findings from insights"""
        try:
            key_findings = []
            
            # Critical findings
            critical_insights = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
            if critical_insights:
                key_findings.append(f"Critical issues identified: {len(critical_insights)} requiring immediate attention")
            
            # Performance findings
            performance_insights = [i for i in insights if i.insight_type == InsightType.PERFORMANCE]
            if performance_insights:
                key_findings.append(f"Performance issues detected in {len(performance_insights)} areas")
            
            # Compliance findings
            compliance_insights = [i for i in insights if i.insight_type == InsightType.COMPLIANCE]
            if compliance_insights:
                key_findings.append(f"Compliance concerns identified: {len(compliance_insights)} areas need attention")
            
            # Opportunity findings
            opportunity_insights = [i for i in insights if i.insight_type == InsightType.OPPORTUNITY]
            if opportunity_insights:
                key_findings.append(f"Optimization opportunities found: {len(opportunity_insights)} areas for improvement")
            
            # Risk findings
            risk_insights = [i for i in insights if i.insight_type == InsightType.RISK]
            if risk_insights:
                key_findings.append(f"Risk factors identified: {len(risk_insights)} areas requiring risk mitigation")
            
            return key_findings
            
        except Exception as e:
            self.logger.error(f"Error extracting key findings: {str(e)}")
            return []
    
    async def _generate_strategic_recommendations(self, insights: List[BusinessInsight]) -> List[str]:
        """Generate strategic recommendations"""
        try:
            recommendations = []
            
            # Immediate actions
            immediate_insights = [i for i in insights if i.time_sensitivity == "Immediate"]
            if immediate_insights:
                recommendations.append(f"Immediate action required for {len(immediate_insights)} critical issues")
            
            # Strategic planning
            strategic_insights = [i for i in insights if i.category == InsightCategory.STRATEGIC_PLANNING]
            if strategic_insights:
                recommendations.append("Review strategic planning based on identified trends and predictions")
            
            # Optimization
            optimization_insights = [i for i in insights if i.category == InsightCategory.OPTIMIZATION]
            if optimization_insights:
                recommendations.append("Implement optimization initiatives to improve system efficiency")
            
            # Monitoring
            monitoring_insights = [i for i in insights if i.category == InsightCategory.MONITORING]
            if monitoring_insights:
                recommendations.append("Enhance monitoring and alerting systems for proactive issue detection")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating strategic recommendations: {str(e)}")
            return []
    
    async def _define_next_steps(self, insights: List[BusinessInsight]) -> List[str]:
        """Define next steps based on insights"""
        try:
            next_steps = []
            
            # Critical issues
            critical_insights = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
            if critical_insights:
                next_steps.append("Address critical issues within 24 hours")
            
            # High priority
            high_priority_insights = [i for i in insights if i.severity == InsightSeverity.HIGH]
            if high_priority_insights:
                next_steps.append("Schedule high-priority issue resolution within 48 hours")
            
            # Process improvements
            next_steps.append("Review and update monitoring thresholds based on insights")
            next_steps.append("Implement recommended optimizations in order of priority")
            next_steps.append("Schedule regular insight review meetings")
            
            return next_steps
            
        except Exception as e:
            self.logger.error(f"Error defining next steps: {str(e)}")
            return []
    
    async def _send_critical_notifications(self, insights: List[BusinessInsight]):
        """Send notifications for critical insights"""
        try:
            critical_insights = [i for i in insights if i.severity == InsightSeverity.CRITICAL]
            
            for insight in critical_insights:
                await self.notification_service.send_notification(
                    type="critical_insight",
                    data={
                        "insight_id": insight.insight_id,
                        "title": insight.title,
                        "description": insight.description,
                        "recommendations": insight.recommendations,
                        "time_sensitivity": insight.time_sensitivity
                    }
                )
            
        except Exception as e:
            self.logger.error(f"Error sending critical notifications: {str(e)}")
    
    async def _periodic_insight_generation(self):
        """Periodic insight generation task"""
        while True:
            try:
                await asyncio.sleep(self.execution_interval)
                
                # Generate insights for the last 4 hours
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=4)
                
                await self.generate_insights((start_time, end_time))
                
            except Exception as e:
                self.logger.error(f"Error in periodic insight generation: {str(e)}")
    
    async def _cleanup_old_insights(self):
        """Cleanup old insights periodically"""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                
                cutoff_time = datetime.now(timezone.utc) - timedelta(days=self.insight_retention_days)
                
                # Remove old insights
                to_remove = []
                for insight_id, insight in self.generated_insights.items():
                    if insight.generated_time < cutoff_time:
                        to_remove.append(insight_id)
                
                for insight_id in to_remove:
                    del self.generated_insights[insight_id]
                
                # Remove old execution history
                self.execution_history = [
                    e for e in self.execution_history
                    if e.execution_time >= cutoff_time
                ]
                
                self.logger.info(f"Cleaned up {len(to_remove)} old insights")
                
            except Exception as e:
                self.logger.error(f"Error in cleanup old insights: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "insight.generated",
                self._handle_insight_generated
            )
            
            await self.event_bus.subscribe(
                "metrics.updated",
                self._handle_metrics_updated
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_insight_generated(self, event_data: Dict[str, Any]):
        """Handle insight generated event"""
        try:
            insight_id = event_data.get("insight_id")
            self.logger.info(f"Insight generated: {insight_id}")
            
        except Exception as e:
            self.logger.error(f"Error handling insight generated event: {str(e)}")
    
    async def _handle_metrics_updated(self, event_data: Dict[str, Any]):
        """Handle metrics updated event"""
        try:
            # Trigger insight generation if significant metrics update
            metric_id = event_data.get("metric_id")
            
            # Check if this is a critical metric
            critical_metrics = ["e2e_processing_time", "cross_role_success_rate", "unified_compliance_score"]
            
            if metric_id in critical_metrics:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=1)
                
                await self.generate_insights((start_time, end_time))
            
        except Exception as e:
            self.logger.error(f"Error handling metrics updated: {str(e)}")
    
    async def get_insight_summary(self) -> Dict[str, Any]:
        """Get insight generation summary"""
        try:
            return {
                "total_rules": len(self.insight_rules),
                "enabled_rules": len([r for r in self.insight_rules.values() if r.enabled]),
                "total_insights": len(self.generated_insights),
                "insights_by_type": {
                    insight_type: len([i for i in self.generated_insights.values() if i.insight_type == insight_type])
                    for insight_type in InsightType
                },
                "insights_by_severity": {
                    severity: len([i for i in self.generated_insights.values() if i.severity == severity])
                    for severity in InsightSeverity
                },
                "execution_history_count": len(self.execution_history),
                "reports_generated": len(self.insight_reports),
                "is_initialized": self.is_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting insight summary: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            unified_metrics_health = await self.unified_metrics.health_check()
            kpi_calculator_health = await self.kpi_calculator.health_check()
            trend_analyzer_health = await self.trend_analyzer.health_check()
            cache_health = await self.cache.health_check()
            
            return {
                "status": "healthy" if self.is_initialized else "initializing",
                "service": "insight_generator",
                "components": {
                    "unified_metrics": unified_metrics_health,
                    "kpi_calculator": kpi_calculator_health,
                    "trend_analyzer": trend_analyzer_health,
                    "cache": cache_health,
                    "ai_service": {"status": "healthy" if self.ai_service.is_available() else "unavailable"}
                },
                "metrics": {
                    "total_rules": len(self.insight_rules),
                    "total_insights": len(self.generated_insights),
                    "execution_history": len(self.execution_history)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "insight_generator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Insight generator service cleanup initiated")
        
        try:
            # Clear caches
            self.generated_insights.clear()
            self.execution_history.clear()
            self.insight_reports.clear()
            
            # Cleanup dependencies
            await self.unified_metrics.cleanup()
            await self.kpi_calculator.cleanup()
            await self.trend_analyzer.cleanup()
            await self.cross_role_reporting.cleanup()
            await self.cache.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Insight generator service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_insight_generator(
    unified_metrics: UnifiedMetrics = None,
    kpi_calculator: KPICalculator = None,
    trend_analyzer: TrendAnalyzer = None,
    cross_role_reporting: CrossRoleReporting = None
) -> InsightGenerator:
    """Create insight generator service"""
    return InsightGenerator(unified_metrics, kpi_calculator, trend_analyzer, cross_role_reporting)