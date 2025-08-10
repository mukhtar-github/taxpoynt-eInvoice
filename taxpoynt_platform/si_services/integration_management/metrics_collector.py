"""
Integration Metrics Collector

Collects and analyzes performance metrics for integrations.
Extracted from integration_status_service.py - provides granular metrics analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collects and analyzes performance metrics for integrations"""
    
    def __init__(self):
        self.metrics_cache = {}
        self.performance_thresholds = {
            "response_time_warning": 5000,  # 5 seconds
            "response_time_critical": 10000,  # 10 seconds
            "success_rate_warning": 90.0,  # 90%
            "success_rate_critical": 80.0,  # 80%
            "error_rate_warning": 5.0,  # 5%
            "error_rate_critical": 10.0  # 10%
        }
    
    def get_integration_performance_metrics(
        self, 
        integration_id: str, 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get detailed performance metrics for a specific integration - SI Role Function.
        Extracted from integration_status_service.py lines 255-336
        
        Provides comprehensive performance analysis for System Integrator monitoring
        and optimization of ERP/CRM integrations.
        
        Args:
            integration_id: ID of the integration to analyze
            days: Number of days to analyze (default: 7)
            
        Returns:
            Dictionary with detailed performance metrics
        """
        # Get time range
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # TODO: Query submissions for the integration from data store
        # submissions = db.query(SubmissionRecord).filter(
        #     SubmissionRecord.integration_id == integration_id,
        #     SubmissionRecord.created_at >= start_date
        # ).all()
        
        # Mock submissions data for now
        submissions = self._get_mock_submissions(integration_id, start_date, now)
        
        if not submissions:
            return {
                "integration_id": integration_id,
                "period_days": days,
                "no_data": True,
                "message": "No submissions found for the specified period"
            }
        
        # Calculate metrics
        total_submissions = len(submissions)
        successful = sum(1 for s in submissions if s.get("status") in ['accepted', 'signed'])
        failed = sum(1 for s in submissions if s.get("status") in ['failed', 'rejected', 'error'])
        pending = sum(1 for s in submissions if s.get("status") in ['pending', 'processing'])
        
        success_rate = (successful / total_submissions * 100) if total_submissions > 0 else 0
        failure_rate = (failed / total_submissions * 100) if total_submissions > 0 else 0
        
        # Daily breakdown
        daily_stats = {}
        for submission in submissions:
            day_key = submission["created_at"].strftime("%Y-%m-%d")
            if day_key not in daily_stats:
                daily_stats[day_key] = {"total": 0, "successful": 0, "failed": 0}
            
            daily_stats[day_key]["total"] += 1
            if submission["status"] in ['accepted', 'signed']:
                daily_stats[day_key]["successful"] += 1
            elif submission["status"] in ['failed', 'rejected', 'error']:
                daily_stats[day_key]["failed"] += 1
        
        # Average processing time (if available)
        processing_times = []
        for submission in submissions:
            if submission.get("processing_time"):
                processing_times.append(submission["processing_time"])
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else None
        
        # Generate performance analysis
        performance_analysis = self._analyze_performance_metrics(
            success_rate, failure_rate, avg_processing_time, daily_stats
        )
        
        metrics = {
            "integration_id": integration_id,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "summary": {
                "total_submissions": total_submissions,
                "successful": successful,
                "failed": failed,
                "pending": pending,
                "success_rate": round(success_rate, 2),
                "failure_rate": round(failure_rate, 2)
            },
            "daily_breakdown": daily_stats,
            "performance": {
                "avg_processing_time_seconds": avg_processing_time,
                "submissions_per_day": round(total_submissions / days, 2)
            },
            "analysis": performance_analysis
        }
        
        # Cache the metrics
        self.metrics_cache[integration_id] = {
            "metrics": metrics,
            "cached_at": datetime.utcnow(),
            "cache_expires": datetime.utcnow() + timedelta(hours=1)  # Cache for 1 hour
        }
        
        return metrics
    
    def get_system_wide_metrics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get system-wide performance metrics across all integrations.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with system-wide metrics
        """
        now = datetime.utcnow()
        start_date = now - timedelta(days=days)
        
        # TODO: Get all integrations and their submissions
        # For now, mock system-wide data
        
        system_metrics = {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat(),
            "overview": {
                "total_integrations": 5,
                "active_integrations": 4,
                "failed_integrations": 1,
                "total_submissions": 150,
                "successful_submissions": 135,
                "failed_submissions": 15,
                "system_success_rate": 90.0,
                "system_failure_rate": 10.0
            },
            "top_performing_integrations": [
                {"integration_id": "int_001", "success_rate": 98.5},
                {"integration_id": "int_002", "success_rate": 95.2},
                {"integration_id": "int_003", "success_rate": 92.1}
            ],
            "problematic_integrations": [
                {"integration_id": "int_004", "success_rate": 75.0, "issue": "High error rate"},
                {"integration_id": "int_005", "success_rate": 60.0, "issue": "Connection timeouts"}
            ],
            "trends": {
                "success_rate_trend": "stable",
                "submission_volume_trend": "increasing",
                "performance_trend": "improving"
            }
        }
        
        return system_metrics
    
    def get_integration_trends(self, integration_id: str, weeks: int = 4) -> Dict[str, Any]:
        """
        Get performance trends for an integration over time.
        
        Args:
            integration_id: Integration ID to analyze
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with trend analysis
        """
        weekly_data = []
        
        # Generate weekly metrics for the specified period
        for week in range(weeks):
            week_start = datetime.utcnow() - timedelta(weeks=week+1)
            week_end = week_start + timedelta(weeks=1)
            
            # TODO: Get actual data for this week
            # Mock weekly data
            weekly_metrics = {
                "week": f"Week {weeks - week}",
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "submissions": 20 + (week * 2),  # Simulate growth
                "success_rate": 85.0 + (week * 2.5),  # Simulate improvement
                "avg_response_time": 2000 - (week * 100)  # Simulate improvement
            }
            weekly_data.append(weekly_metrics)
        
        # Analyze trends
        trends = self._analyze_trends(weekly_data)
        
        return {
            "integration_id": integration_id,
            "analysis_period_weeks": weeks,
            "weekly_data": weekly_data,
            "trends": trends,
            "recommendations": self._get_trend_recommendations(trends)
        }
    
    def get_real_time_metrics(self, integration_id: str) -> Dict[str, Any]:
        """
        Get real-time metrics for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Real-time metrics
        """
        # Check cache first
        cached_data = self.metrics_cache.get(integration_id)
        if cached_data and datetime.utcnow() < cached_data["cache_expires"]:
            return {
                "integration_id": integration_id,
                "real_time": True,
                "cached": True,
                "last_updated": cached_data["cached_at"].isoformat(),
                "metrics": cached_data["metrics"]["summary"]
            }
        
        # TODO: Get real-time data from monitoring system
        # For now, return mock real-time data
        return {
            "integration_id": integration_id,
            "real_time": True,
            "cached": False,
            "last_updated": datetime.utcnow().isoformat(),
            "current_status": "active",
            "submissions_last_hour": 5,
            "success_rate_last_hour": 100.0,
            "avg_response_time_last_hour": 1500,
            "active_connections": 2,
            "queue_size": 0,
            "health_score": 95
        }
    
    def compare_integration_performance(
        self, 
        integration_ids: List[str], 
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Compare performance metrics across multiple integrations.
        
        Args:
            integration_ids: List of integration IDs to compare
            days: Number of days to analyze
            
        Returns:
            Comparison analysis
        """
        comparison_data = {}
        
        for integration_id in integration_ids:
            metrics = self.get_integration_performance_metrics(integration_id, days)
            comparison_data[integration_id] = {
                "success_rate": metrics["summary"]["success_rate"],
                "failure_rate": metrics["summary"]["failure_rate"],
                "total_submissions": metrics["summary"]["total_submissions"],
                "avg_processing_time": metrics["performance"]["avg_processing_time_seconds"],
                "submissions_per_day": metrics["performance"]["submissions_per_day"]
            }
        
        # Rank integrations by performance
        rankings = {
            "by_success_rate": sorted(
                comparison_data.items(), 
                key=lambda x: x[1]["success_rate"], 
                reverse=True
            ),
            "by_volume": sorted(
                comparison_data.items(), 
                key=lambda x: x[1]["total_submissions"], 
                reverse=True
            ),
            "by_response_time": sorted(
                comparison_data.items(), 
                key=lambda x: x[1]["avg_processing_time"] or 0
            )
        }
        
        return {
            "comparison_period_days": days,
            "integrations_compared": len(integration_ids),
            "comparison_data": comparison_data,
            "rankings": rankings,
            "insights": self._generate_comparison_insights(comparison_data)
        }
    
    def _get_mock_submissions(self, integration_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Generate mock submission data for testing"""
        submissions = []
        current_date = start_date
        
        while current_date < end_date:
            # Generate 2-5 submissions per day
            daily_submissions = 2 + (hash(integration_id + current_date.strftime("%Y%m%d")) % 4)
            
            for i in range(daily_submissions):
                submission_time = current_date + timedelta(
                    hours=hash(f"{integration_id}{i}") % 24,
                    minutes=hash(f"{integration_id}{i}") % 60
                )
                
                # 85% success rate
                status = "accepted" if hash(f"{integration_id}{i}") % 100 < 85 else "failed"
                
                submissions.append({
                    "id": f"sub_{integration_id}_{i}_{current_date.strftime('%Y%m%d')}",
                    "integration_id": integration_id,
                    "status": status,
                    "created_at": submission_time,
                    "processing_time": 1000 + (hash(f"{integration_id}{i}") % 3000)  # 1-4 seconds
                })
            
            current_date += timedelta(days=1)
        
        return submissions
    
    def _analyze_performance_metrics(
        self, 
        success_rate: float, 
        failure_rate: float, 
        avg_processing_time: Optional[float],
        daily_stats: Dict[str, Dict[str, int]]
    ) -> Dict[str, Any]:
        """Analyze performance metrics and provide insights"""
        analysis = {
            "overall_health": "excellent",
            "alerts": [],
            "insights": [],
            "recommendations": []
        }
        
        # Analyze success rate
        if success_rate < self.performance_thresholds["success_rate_critical"]:
            analysis["overall_health"] = "critical"
            analysis["alerts"].append(f"Critical: Success rate ({success_rate:.1f}%) is below critical threshold")
        elif success_rate < self.performance_thresholds["success_rate_warning"]:
            analysis["overall_health"] = "warning" if analysis["overall_health"] == "excellent" else analysis["overall_health"]
            analysis["alerts"].append(f"Warning: Success rate ({success_rate:.1f}%) is below warning threshold")
        
        # Analyze failure rate
        if failure_rate > self.performance_thresholds["error_rate_critical"]:
            analysis["overall_health"] = "critical"
            analysis["alerts"].append(f"Critical: Failure rate ({failure_rate:.1f}%) is above critical threshold")
        elif failure_rate > self.performance_thresholds["error_rate_warning"]:
            analysis["overall_health"] = "warning" if analysis["overall_health"] == "excellent" else analysis["overall_health"]
            analysis["alerts"].append(f"Warning: Failure rate ({failure_rate:.1f}%) is above warning threshold")
        
        # Analyze response time
        if avg_processing_time:
            avg_time_ms = avg_processing_time * 1000
            if avg_time_ms > self.performance_thresholds["response_time_critical"]:
                analysis["overall_health"] = "critical"
                analysis["alerts"].append(f"Critical: Average response time ({avg_time_ms:.0f}ms) is too high")
            elif avg_time_ms > self.performance_thresholds["response_time_warning"]:
                analysis["overall_health"] = "warning" if analysis["overall_health"] == "excellent" else analysis["overall_health"]
                analysis["alerts"].append(f"Warning: Average response time ({avg_time_ms:.0f}ms) is elevated")
        
        # Generate insights
        if success_rate > 95:
            analysis["insights"].append("Integration is performing excellently")
        
        if daily_stats:
            daily_volumes = [stats["total"] for stats in daily_stats.values()]
            if len(set(daily_volumes)) == 1:
                analysis["insights"].append("Consistent daily transaction volume")
            elif max(daily_volumes) > min(daily_volumes) * 2:
                analysis["insights"].append("Significant variation in daily transaction volume")
        
        # Generate recommendations
        if failure_rate > 5:
            analysis["recommendations"].append("Investigate error patterns and root causes")
        
        if avg_processing_time and avg_processing_time > 3:
            analysis["recommendations"].append("Consider optimizing response times")
        
        if not analysis["recommendations"]:
            analysis["recommendations"].append("Continue monitoring current performance levels")
        
        return analysis
    
    def _analyze_trends(self, weekly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trends in weekly data"""
        if len(weekly_data) < 2:
            return {"trend": "insufficient_data"}
        
        # Analyze success rate trend
        success_rates = [week["success_rate"] for week in weekly_data]
        if success_rates[-1] > success_rates[0]:
            success_trend = "improving"
        elif success_rates[-1] < success_rates[0]:
            success_trend = "declining"
        else:
            success_trend = "stable"
        
        # Analyze volume trend
        volumes = [week["submissions"] for week in weekly_data]
        if volumes[-1] > volumes[0] * 1.1:
            volume_trend = "increasing"
        elif volumes[-1] < volumes[0] * 0.9:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
        
        # Analyze response time trend
        response_times = [week["avg_response_time"] for week in weekly_data]
        if response_times[-1] < response_times[0] * 0.9:
            response_trend = "improving"
        elif response_times[-1] > response_times[0] * 1.1:
            response_trend = "degrading"
        else:
            response_trend = "stable"
        
        return {
            "success_rate_trend": success_trend,
            "volume_trend": volume_trend,
            "response_time_trend": response_trend,
            "overall_trend": self._determine_overall_trend(success_trend, volume_trend, response_trend)
        }
    
    def _determine_overall_trend(self, success_trend: str, volume_trend: str, response_trend: str) -> str:
        """Determine overall trend based on individual metrics"""
        improving_count = sum([
            1 for trend in [success_trend, volume_trend, response_trend] 
            if trend == "improving"
        ])
        
        declining_count = sum([
            1 for trend in [success_trend, volume_trend, response_trend] 
            if trend in ["declining", "degrading", "decreasing"]
        ])
        
        if improving_count >= 2:
            return "improving"
        elif declining_count >= 2:
            return "declining"
        else:
            return "stable"
    
    def _get_trend_recommendations(self, trends: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on trends"""
        recommendations = []
        
        if trends["success_rate_trend"] == "declining":
            recommendations.append("Investigate causes of declining success rate")
        
        if trends["volume_trend"] == "decreasing":
            recommendations.append("Monitor for integration usage issues")
        
        if trends["response_time_trend"] == "degrading":
            recommendations.append("Optimize integration performance")
        
        if trends["overall_trend"] == "improving":
            recommendations.append("Continue current operational practices")
        
        return recommendations
    
    def _generate_comparison_insights(self, comparison_data: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate insights from integration comparison"""
        insights = []
        
        success_rates = [data["success_rate"] for data in comparison_data.values()]
        if max(success_rates) - min(success_rates) > 20:
            insights.append("Significant performance variation across integrations")
        
        volumes = [data["total_submissions"] for data in comparison_data.values()]
        if max(volumes) > min(volumes) * 5:
            insights.append("Large variation in integration usage volumes")
        
        return insights


# Global instance for easy access
metrics_collector = MetricsCollector()