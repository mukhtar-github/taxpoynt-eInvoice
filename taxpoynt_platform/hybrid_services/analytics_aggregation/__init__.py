"""
TaxPoynt Platform - Hybrid Services: Analytics Aggregation
Cross-role analytics and unified KPI calculation
"""

from .unified_metrics import (
    UnifiedMetrics,
    MetricType,
    MetricScope,
    AggregationMethod,
    MetricStatus,
    MetricDefinition,
    MetricValue,
    AggregatedMetric,
    MetricSnapshot,
    create_unified_metrics
)

from .cross_role_reporting import (
    CrossRoleReporting,
    ReportType,
    ReportFormat,
    ReportScope,
    ReportStatus,
    ReportFrequency,
    ReportTemplate,
    ReportRequest,
    ReportSection,
    GeneratedReport,
    create_cross_role_reporting
)

from .kpi_calculator import (
    KPICalculator,
    KPICategory,
    KPIType,
    KPIStatus,
    KPITrend,
    KPIFrequency,
    KPIDefinition,
    KPITarget,
    KPICalculation,
    KPIInsight,
    KPIDashboard,
    create_kpi_calculator
)

from .trend_analyzer import (
    TrendAnalyzer,
    TrendDirection,
    TrendStrength,
    TrendType,
    TrendSignificance,
    PredictionConfidence,
    TrendDataPoint,
    TrendPattern,
    TrendAnalysis,
    TrendPrediction,
    TrendAlert,
    TrendComparison,
    create_trend_analyzer
)

from .insight_generator import (
    InsightGenerator,
    InsightType,
    InsightSeverity,
    InsightCategory,
    InsightConfidence,
    InsightStatus,
    InsightRule,
    DataContext,
    BusinessInsight,
    InsightExecution,
    InsightReport,
    create_insight_generator
)

__version__ = "1.0.0"

__all__ = [
    # Unified Metrics
    "UnifiedMetrics",
    "MetricType",
    "MetricScope",
    "AggregationMethod",
    "MetricStatus",
    "MetricDefinition",
    "MetricValue",
    "AggregatedMetric",
    "MetricSnapshot",
    "create_unified_metrics",
    
    # Cross-Role Reporting
    "CrossRoleReporting",
    "ReportType",
    "ReportFormat",
    "ReportScope",
    "ReportStatus",
    "ReportFrequency",
    "ReportTemplate",
    "ReportRequest",
    "ReportSection",
    "GeneratedReport",
    "create_cross_role_reporting",
    
    # KPI Calculator
    "KPICalculator",
    "KPICategory",
    "KPIType",
    "KPIStatus",
    "KPITrend",
    "KPIFrequency",
    "KPIDefinition",
    "KPITarget",
    "KPICalculation",
    "KPIInsight",
    "KPIDashboard",
    "create_kpi_calculator",
    
    # Trend Analyzer
    "TrendAnalyzer",
    "TrendDirection",
    "TrendStrength",
    "TrendType",
    "TrendSignificance",
    "PredictionConfidence",
    "TrendDataPoint",
    "TrendPattern",
    "TrendAnalysis",
    "TrendPrediction",
    "TrendAlert",
    "TrendComparison",
    "create_trend_analyzer",
    
    # Insight Generator
    "InsightGenerator",
    "InsightType",
    "InsightSeverity",
    "InsightCategory",
    "InsightConfidence",
    "InsightStatus",
    "InsightRule",
    "DataContext",
    "BusinessInsight",
    "InsightExecution",
    "InsightReport",
    "create_insight_generator"
]


class AnalyticsAggregationService:
    """
    Comprehensive analytics aggregation service
    Integrates all analytics components for unified cross-role analytics
    """
    
    def __init__(self):
        """Initialize analytics aggregation service"""
        self.unified_metrics = create_unified_metrics()
        self.cross_role_reporting = create_cross_role_reporting(self.unified_metrics)
        self.kpi_calculator = create_kpi_calculator(self.unified_metrics)
        self.trend_analyzer = create_trend_analyzer(self.unified_metrics, self.kpi_calculator)
        self.insight_generator = create_insight_generator(
            self.unified_metrics,
            self.kpi_calculator,
            self.trend_analyzer,
            self.cross_role_reporting
        )
        
        import logging
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.is_initialized = False
        self.components_initialized = {
            "unified_metrics": False,
            "cross_role_reporting": False,
            "kpi_calculator": False,
            "trend_analyzer": False,
            "insight_generator": False
        }
    
    async def initialize(self):
        """Initialize all analytics components"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing analytics aggregation service")
        
        try:
            # Initialize components in dependency order
            await self.unified_metrics.initialize()
            self.components_initialized["unified_metrics"] = True
            
            await self.kpi_calculator.initialize()
            self.components_initialized["kpi_calculator"] = True
            
            await self.trend_analyzer.initialize()
            self.components_initialized["trend_analyzer"] = True
            
            await self.cross_role_reporting.initialize()
            self.components_initialized["cross_role_reporting"] = True
            
            await self.insight_generator.initialize()
            self.components_initialized["insight_generator"] = True
            
            self.is_initialized = True
            self.logger.info("Analytics aggregation service initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing analytics aggregation service: {str(e)}")
            raise
    
    async def get_unified_dashboard(
        self,
        time_range: tuple = None,
        include_predictions: bool = True,
        include_insights: bool = True
    ) -> dict:
        """Get unified analytics dashboard"""
        try:
            from datetime import datetime, timezone, timedelta
            
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=24)
                time_range = (start_time, end_time)
            
            dashboard_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                }
            }
            
            # Get metrics snapshot
            metrics_snapshot = await self.unified_metrics.create_metric_snapshot(
                MetricScope.SYSTEM_WIDE,
                include_breakdown=True
            )
            dashboard_data["metrics_snapshot"] = metrics_snapshot.to_dict()
            
            # Get KPI dashboard
            kpi_dashboard = await self.kpi_calculator.get_kpi_dashboard(
                time_range=time_range
            )
            dashboard_data["kpi_dashboard"] = kpi_dashboard.to_dict()
            
            # Get trend analysis for key metrics
            key_metrics = ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"]
            trend_analyses = {}
            
            for metric_id in key_metrics:
                try:
                    trend_analysis = await self.trend_analyzer.analyze_metric_trend(
                        metric_id,
                        time_range
                    )
                    trend_analyses[metric_id] = trend_analysis.to_dict()
                except Exception as e:
                    self.logger.debug(f"Could not analyze trend for {metric_id}: {str(e)}")
            
            dashboard_data["trend_analyses"] = trend_analyses
            
            # Get predictions if requested
            if include_predictions:
                predictions = {}
                for metric_id in key_metrics[:3]:  # Limit predictions
                    try:
                        prediction = await self.trend_analyzer.predict_metric_trend(
                            metric_id,
                            time_range,
                            prediction_horizon=7
                        )
                        predictions[metric_id] = prediction.to_dict()
                    except Exception as e:
                        self.logger.debug(f"Could not predict trend for {metric_id}: {str(e)}")
                
                dashboard_data["predictions"] = predictions
            
            # Get insights if requested
            if include_insights:
                insights = await self.insight_generator.get_insights(
                    time_range=time_range,
                    limit=10
                )
                dashboard_data["insights"] = [i.to_dict() for i in insights]
            
            # Get reports dashboard data
            dashboard_report = await self.cross_role_reporting.get_dashboard_data(
                "operational_dashboard",
                time_range
            )
            dashboard_data["operational_dashboard"] = dashboard_report
            
            return dashboard_data
            
        except Exception as e:
            self.logger.error(f"Error getting unified dashboard: {str(e)}")
            raise
    
    async def generate_comprehensive_report(
        self,
        report_type: str = "comprehensive",
        time_range: tuple = None,
        include_predictions: bool = True,
        include_insights: bool = True
    ) -> dict:
        """Generate comprehensive analytics report"""
        try:
            from datetime import datetime, timezone, timedelta
            
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=7)
                time_range = (start_time, end_time)
            
            # Generate report using cross-role reporting
            report_request = ReportRequest(
                request_id=str(__import__('uuid').uuid4()),
                template_id="executive_summary",
                requested_by="analytics_aggregation_service",
                report_format=ReportFormat.JSON,
                time_range=time_range,
                filters={"include_predictions": include_predictions, "include_insights": include_insights},
                parameters={"report_type": report_type}
            )
            
            generated_report = await self.cross_role_reporting.generate_report(report_request)
            
            # Enhance with additional analytics
            enhanced_report = generated_report.to_dict()
            
            # Add KPI analysis
            kpi_dashboard = await self.kpi_calculator.get_kpi_dashboard(time_range=time_range)
            enhanced_report["kpi_analysis"] = kpi_dashboard.to_dict()
            
            # Add trend comparisons
            key_metrics = ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"]
            trend_comparison = await self.trend_analyzer.compare_trends(
                key_metrics,
                time_range
            )
            enhanced_report["trend_comparison"] = trend_comparison.to_dict()
            
            # Add insights report
            if include_insights:
                insight_report = await self.insight_generator.generate_insight_report(
                    time_range,
                    f"Analytics Insights - {report_type.title()}"
                )
                enhanced_report["insight_report"] = insight_report.to_dict()
            
            return enhanced_report
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {str(e)}")
            raise
    
    async def execute_analytics_pipeline(
        self,
        time_range: tuple = None,
        generate_predictions: bool = True,
        generate_insights: bool = True
    ) -> dict:
        """Execute complete analytics pipeline"""
        try:
            from datetime import datetime, timezone, timedelta
            
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=6)
                time_range = (start_time, end_time)
            
            pipeline_results = {
                "execution_time": datetime.now(timezone.utc).isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "pipeline_steps": []
            }
            
            # Step 1: Metrics aggregation
            step_start = datetime.now(timezone.utc)
            metrics_snapshot = await self.unified_metrics.create_metric_snapshot(
                MetricScope.SYSTEM_WIDE
            )
            pipeline_results["pipeline_steps"].append({
                "step": "metrics_aggregation",
                "duration": (datetime.now(timezone.utc) - step_start).total_seconds(),
                "metrics_count": len(metrics_snapshot.metrics),
                "status": "completed"
            })
            
            # Step 2: KPI calculation
            step_start = datetime.now(timezone.utc)
            kpi_dashboard = await self.kpi_calculator.get_kpi_dashboard(time_range=time_range)
            pipeline_results["pipeline_steps"].append({
                "step": "kpi_calculation",
                "duration": (datetime.now(timezone.utc) - step_start).total_seconds(),
                "kpis_calculated": len(kpi_dashboard.kpi_calculations),
                "status": "completed"
            })
            
            # Step 3: Trend analysis
            step_start = datetime.now(timezone.utc)
            key_metrics = ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"]
            trend_analyses = {}
            
            for metric_id in key_metrics:
                try:
                    trend_analysis = await self.trend_analyzer.analyze_metric_trend(
                        metric_id,
                        time_range
                    )
                    trend_analyses[metric_id] = trend_analysis
                except Exception as e:
                    self.logger.debug(f"Could not analyze trend for {metric_id}: {str(e)}")
            
            pipeline_results["pipeline_steps"].append({
                "step": "trend_analysis",
                "duration": (datetime.now(timezone.utc) - step_start).total_seconds(),
                "trends_analyzed": len(trend_analyses),
                "status": "completed"
            })
            
            # Step 4: Predictions (if requested)
            if generate_predictions:
                step_start = datetime.now(timezone.utc)
                predictions = {}
                
                for metric_id in key_metrics[:3]:  # Limit for performance
                    try:
                        prediction = await self.trend_analyzer.predict_metric_trend(
                            metric_id,
                            time_range,
                            prediction_horizon=7
                        )
                        predictions[metric_id] = prediction
                    except Exception as e:
                        self.logger.debug(f"Could not predict trend for {metric_id}: {str(e)}")
                
                pipeline_results["pipeline_steps"].append({
                    "step": "prediction_generation",
                    "duration": (datetime.now(timezone.utc) - step_start).total_seconds(),
                    "predictions_generated": len(predictions),
                    "status": "completed"
                })
            
            # Step 5: Insight generation (if requested)
            if generate_insights:
                step_start = datetime.now(timezone.utc)
                insight_execution = await self.insight_generator.generate_insights(
                    time_range,
                    include_predictions=generate_predictions
                )
                
                pipeline_results["pipeline_steps"].append({
                    "step": "insight_generation",
                    "duration": (datetime.now(timezone.utc) - step_start).total_seconds(),
                    "insights_generated": len(insight_execution.insights_generated),
                    "rules_executed": len(insight_execution.rules_executed),
                    "status": "completed" if insight_execution.success else "failed"
                })
            
            # Pipeline summary
            total_duration = sum(step["duration"] for step in pipeline_results["pipeline_steps"])
            pipeline_results["summary"] = {
                "total_duration": total_duration,
                "steps_completed": len(pipeline_results["pipeline_steps"]),
                "overall_status": "completed"
            }
            
            return pipeline_results
            
        except Exception as e:
            self.logger.error(f"Error executing analytics pipeline: {str(e)}")
            raise
    
    async def get_cross_role_analytics(
        self,
        si_metrics: list = None,
        app_metrics: list = None,
        time_range: tuple = None
    ) -> dict:
        """Get cross-role analytics comparison"""
        try:
            from datetime import datetime, timezone, timedelta
            
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=12)
                time_range = (start_time, end_time)
            
            # Default metrics if not provided
            if not si_metrics:
                si_metrics = ["si_processing_time", "si_throughput", "si_success_rate"]
            if not app_metrics:
                app_metrics = ["app_processing_time", "app_throughput", "app_success_rate"]
            
            cross_role_analytics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "time_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "si_analytics": {},
                "app_analytics": {},
                "cross_role_comparison": {},
                "unified_metrics": {}
            }
            
            # Get SI metrics
            si_aggregated = await self.unified_metrics.aggregate_metrics(
                si_metrics,
                time_range
            )
            cross_role_analytics["si_analytics"] = {
                metric.metric_id: metric.to_dict() for metric in si_aggregated
            }
            
            # Get APP metrics
            app_aggregated = await self.unified_metrics.aggregate_metrics(
                app_metrics,
                time_range
            )
            cross_role_analytics["app_analytics"] = {
                metric.metric_id: metric.to_dict() for metric in app_aggregated
            }
            
            # Get unified cross-role metrics
            unified_metrics = ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"]
            unified_aggregated = await self.unified_metrics.aggregate_metrics(
                unified_metrics,
                time_range
            )
            cross_role_analytics["unified_metrics"] = {
                metric.metric_id: metric.to_dict() for metric in unified_aggregated
            }
            
            # Generate cross-role comparison
            all_metrics = si_metrics + app_metrics + unified_metrics
            trend_comparison = await self.trend_analyzer.compare_trends(
                all_metrics,
                time_range
            )
            cross_role_analytics["cross_role_comparison"] = trend_comparison.to_dict()
            
            return cross_role_analytics
            
        except Exception as e:
            self.logger.error(f"Error getting cross-role analytics: {str(e)}")
            raise
    
    async def get_predictive_analytics(
        self,
        metrics: list = None,
        time_range: tuple = None,
        prediction_horizon: int = 7
    ) -> dict:
        """Get predictive analytics"""
        try:
            from datetime import datetime, timezone, timedelta
            
            if not time_range:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(days=14)
                time_range = (start_time, end_time)
            
            if not metrics:
                metrics = ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"]
            
            predictive_analytics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "historical_range": {
                    "start": time_range[0].isoformat(),
                    "end": time_range[1].isoformat()
                },
                "prediction_horizon_days": prediction_horizon,
                "predictions": {},
                "trend_analyses": {},
                "forecast_summary": {}
            }
            
            # Generate predictions for each metric
            for metric_id in metrics:
                try:
                    # Get trend analysis
                    trend_analysis = await self.trend_analyzer.analyze_metric_trend(
                        metric_id,
                        time_range
                    )
                    predictive_analytics["trend_analyses"][metric_id] = trend_analysis.to_dict()
                    
                    # Generate prediction
                    prediction = await self.trend_analyzer.predict_metric_trend(
                        metric_id,
                        time_range,
                        prediction_horizon=prediction_horizon
                    )
                    predictive_analytics["predictions"][metric_id] = prediction.to_dict()
                    
                except Exception as e:
                    self.logger.debug(f"Could not generate prediction for {metric_id}: {str(e)}")
            
            # Generate forecast summary
            predictive_analytics["forecast_summary"] = {
                "total_predictions": len(predictive_analytics["predictions"]),
                "high_confidence_predictions": len([
                    p for p in predictive_analytics["predictions"].values()
                    if p.get("confidence") in ["high", "very_high"]
                ]),
                "trend_directions": {
                    "upward": len([
                        t for t in predictive_analytics["trend_analyses"].values()
                        if t.get("primary_trend", {}).get("direction") == "upward"
                    ]),
                    "downward": len([
                        t for t in predictive_analytics["trend_analyses"].values()
                        if t.get("primary_trend", {}).get("direction") == "downward"
                    ]),
                    "stable": len([
                        t for t in predictive_analytics["trend_analyses"].values()
                        if t.get("primary_trend", {}).get("direction") == "stable"
                    ])
                }
            }
            
            return predictive_analytics
            
        except Exception as e:
            self.logger.error(f"Error getting predictive analytics: {str(e)}")
            raise
    
    async def get_service_summary(self) -> dict:
        """Get comprehensive service summary"""
        try:
            return {
                "service": "analytics_aggregation",
                "is_initialized": self.is_initialized,
                "components": self.components_initialized,
                "unified_metrics": await self.unified_metrics.get_metrics_summary(),
                "kpi_calculator": await self.kpi_calculator.get_kpi_summary(),
                "trend_analyzer": await self.trend_analyzer.get_trend_summary(),
                "insight_generator": await self.insight_generator.get_insight_summary(),
                "cross_role_reporting": {
                    "status": "healthy" if self.components_initialized["cross_role_reporting"] else "not_initialized"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting service summary: {str(e)}")
            return {"error": str(e)}
    
    async def health_check(self) -> dict:
        """Get comprehensive health check"""
        try:
            health_checks = {}
            
            # Check all components
            health_checks["unified_metrics"] = await self.unified_metrics.health_check()
            health_checks["kpi_calculator"] = await self.kpi_calculator.health_check()
            health_checks["trend_analyzer"] = await self.trend_analyzer.health_check()
            health_checks["insight_generator"] = await self.insight_generator.health_check()
            health_checks["cross_role_reporting"] = await self.cross_role_reporting.health_check()
            
            # Determine overall health
            overall_status = "healthy"
            component_statuses = [hc.get("status") for hc in health_checks.values()]
            
            if "error" in component_statuses:
                overall_status = "error"
            elif "degraded" in component_statuses:
                overall_status = "degraded"
            elif "initializing" in component_statuses:
                overall_status = "initializing"
            
            return {
                "status": overall_status,
                "service": "analytics_aggregation",
                "is_initialized": self.is_initialized,
                "components": health_checks,
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "analytics_aggregation",
                "error": str(e),
                "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup all analytics components"""
        self.logger.info("Analytics aggregation service cleanup initiated")
        
        try:
            # Cleanup all components
            await self.unified_metrics.cleanup()
            await self.kpi_calculator.cleanup()
            await self.trend_analyzer.cleanup()
            await self.insight_generator.cleanup()
            await self.cross_role_reporting.cleanup()
            
            # Reset state
            self.is_initialized = False
            self.components_initialized = {key: False for key in self.components_initialized}
            
            self.logger.info("Analytics aggregation service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_analytics_aggregation_service() -> AnalyticsAggregationService:
    """Create analytics aggregation service with all components"""
    return AnalyticsAggregationService()


# Common analytics patterns
def get_common_analytics_patterns() -> dict:
    """Get common analytics patterns for reuse"""
    return {
        "performance_monitoring": {
            "description": "Monitor system performance across SI and APP",
            "metrics": ["e2e_processing_time", "unified_throughput", "cross_role_success_rate"],
            "kpis": ["system_efficiency", "response_time_sla"],
            "insights": ["performance_degradation", "capacity_utilization"]
        },
        "business_intelligence": {
            "description": "Business intelligence and financial analytics",
            "metrics": ["transaction_volume", "revenue_metrics"],
            "kpis": ["revenue_per_transaction", "customer_satisfaction_index"],
            "insights": ["revenue_impact", "optimization_opportunity"]
        },
        "operational_excellence": {
            "description": "Operational excellence and process optimization",
            "metrics": ["resource_utilization", "error_rates"],
            "kpis": ["operational_efficiency", "system_availability"],
            "insights": ["operational_risk", "process_improvement"]
        },
        "compliance_monitoring": {
            "description": "Regulatory compliance and risk management",
            "metrics": ["compliance_score", "audit_findings"],
            "kpis": ["regulatory_compliance_rate", "compliance_gap_score"],
            "insights": ["compliance_risk", "regulatory_changes"]
        },
        "predictive_analytics": {
            "description": "Predictive analytics and forecasting",
            "metrics": ["trend_indicators", "seasonal_patterns"],
            "kpis": ["forecast_accuracy", "prediction_confidence"],
            "insights": ["predictive_scaling", "demand_forecasting"]
        }
    }


# Analytics utilities
def create_analytics_context(
    metrics: list,
    kpis: list,
    time_range: tuple,
    metadata: dict = None
) -> dict:
    """Create analytics context with standard structure"""
    return {
        "context_id": str(__import__('uuid').uuid4()),
        "metrics": metrics,
        "kpis": kpis,
        "time_range": {
            "start": time_range[0].isoformat(),
            "end": time_range[1].isoformat()
        },
        "metadata": metadata or {},
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }


def create_dashboard_config(
    dashboard_type: str,
    metrics: list,
    kpis: list,
    include_predictions: bool = True,
    include_insights: bool = True
) -> dict:
    """Create dashboard configuration with standard structure"""
    return {
        "dashboard_type": dashboard_type,
        "metrics": metrics,
        "kpis": kpis,
        "features": {
            "include_predictions": include_predictions,
            "include_insights": include_insights,
            "real_time_updates": True,
            "interactive_charts": True
        },
        "refresh_interval": 300,  # 5 minutes
        "data_retention": 30,  # 30 days
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }


def create_analytics_pipeline_config(
    pipeline_type: str,
    steps: list,
    schedule: str = "hourly",
    metadata: dict = None
) -> dict:
    """Create analytics pipeline configuration"""
    return {
        "pipeline_type": pipeline_type,
        "steps": steps,
        "schedule": schedule,
        "retry_policy": {
            "max_retries": 3,
            "retry_delay": 300
        },
        "notification_settings": {
            "on_success": False,
            "on_failure": True,
            "on_critical_insights": True
        },
        "metadata": metadata or {},
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()
    }