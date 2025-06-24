"""
Deployment monitoring and alerting service.

This service monitors deployment health and can trigger automatic rollbacks
based on error rates, response times, and other metrics.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
import json

from app.db.redis import get_redis_client
from app.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DeploymentMetrics:
    """Deployment health metrics."""
    deployment_id: str
    timestamp: datetime
    response_time_avg: float
    error_rate: float
    success_rate: float
    active_connections: int
    memory_usage: float
    cpu_usage: float
    queue_health: str
    database_health: str


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    metric_name: str
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq'
    duration_seconds: int
    severity: str  # 'warning', 'critical'


class DeploymentMonitor:
    """Monitor deployment health and trigger alerts/rollbacks."""
    
    def __init__(self):
        """Initialize deployment monitor."""
        self.redis_client = get_redis_client()
        self.monitoring_active = False
        self.current_deployment_id: Optional[str] = None
        
        # Default alert thresholds
        self.alert_thresholds = [
            AlertThreshold("error_rate", 5.0, "gt", 60, "warning"),
            AlertThreshold("error_rate", 10.0, "gt", 30, "critical"),
            AlertThreshold("response_time_avg", 2000.0, "gt", 120, "warning"),
            AlertThreshold("response_time_avg", 5000.0, "gt", 60, "critical"),
            AlertThreshold("success_rate", 95.0, "lt", 180, "warning"),
            AlertThreshold("success_rate", 90.0, "lt", 60, "critical"),
            AlertThreshold("memory_usage", 85.0, "gt", 300, "warning"),
            AlertThreshold("memory_usage", 95.0, "gt", 120, "critical"),
        ]
        
        # Callbacks for alerts and actions
        self.alert_callbacks: List[Callable] = []
        self.rollback_callbacks: List[Callable] = []
        
        # Metrics storage
        self.metrics_history: List[DeploymentMetrics] = []
        self.max_history_size = 1000  # Keep last 1000 metrics points
    
    async def start_monitoring(self, deployment_id: str) -> None:
        """
        Start monitoring a deployment.
        
        Args:
            deployment_id: ID of the deployment to monitor
        """
        self.current_deployment_id = deployment_id
        self.monitoring_active = True
        
        logger.info(f"Starting deployment monitoring for: {deployment_id}")
        
        # Store deployment start time
        await self._store_deployment_event("monitoring_started", {
            "deployment_id": deployment_id,
            "started_at": datetime.now().isoformat()
        })
        
        # Start monitoring loop
        asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """Stop monitoring the current deployment."""
        if self.current_deployment_id:
            logger.info(f"Stopping deployment monitoring for: {self.current_deployment_id}")
            
            await self._store_deployment_event("monitoring_stopped", {
                "deployment_id": self.current_deployment_id,
                "stopped_at": datetime.now().isoformat()
            })
        
        self.monitoring_active = False
        self.current_deployment_id = None
    
    async def collect_metrics(self) -> Optional[DeploymentMetrics]:
        """
        Collect current deployment metrics.
        
        Returns:
            Current deployment metrics or None if collection fails
        """
        if not self.current_deployment_id:
            return None
        
        try:
            # Collect various metrics
            metrics = DeploymentMetrics(
                deployment_id=self.current_deployment_id,
                timestamp=datetime.now(),
                response_time_avg=await self._get_response_time_avg(),
                error_rate=await self._get_error_rate(),
                success_rate=await self._get_success_rate(),
                active_connections=await self._get_active_connections(),
                memory_usage=await self._get_memory_usage(),
                cpu_usage=await self._get_cpu_usage(),
                queue_health=await self._get_queue_health(),
                database_health=await self._get_database_health()
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Trim history if too large
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history = self.metrics_history[-self.max_history_size:]
            
            # Store in Redis for external access
            await self._store_metrics(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect metrics: {str(e)}")
            return None
    
    async def check_alert_conditions(self, metrics: DeploymentMetrics) -> List[Dict[str, Any]]:
        """
        Check if any alert conditions are triggered.
        
        Args:
            metrics: Current deployment metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for threshold in self.alert_thresholds:
            try:
                # Get metric value
                metric_value = getattr(metrics, threshold.metric_name, None)
                if metric_value is None:
                    continue
                
                # Check if threshold is exceeded
                is_triggered = False
                
                if threshold.comparison == "gt" and metric_value > threshold.threshold_value:
                    is_triggered = True
                elif threshold.comparison == "lt" and metric_value < threshold.threshold_value:
                    is_triggered = True
                elif threshold.comparison == "eq" and metric_value == threshold.threshold_value:
                    is_triggered = True
                
                if is_triggered:
                    # Check if condition persists for required duration
                    if await self._check_threshold_duration(threshold, metrics):
                        alert = {
                            "metric": threshold.metric_name,
                            "current_value": metric_value,
                            "threshold_value": threshold.threshold_value,
                            "severity": threshold.severity,
                            "duration": threshold.duration_seconds,
                            "deployment_id": metrics.deployment_id,
                            "timestamp": metrics.timestamp.isoformat()
                        }
                        triggered_alerts.append(alert)
                        
                        # Store alert
                        await self._store_alert(alert)
                        
            except Exception as e:
                logger.error(f"Error checking threshold {threshold.metric_name}: {str(e)}")
        
        return triggered_alerts
    
    async def should_trigger_rollback(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Determine if a rollback should be triggered based on alerts.
        
        Args:
            alerts: List of current alerts
            
        Returns:
            True if rollback should be triggered
        """
        # Count critical alerts
        critical_alerts = [alert for alert in alerts if alert["severity"] == "critical"]
        
        # Rollback conditions
        if len(critical_alerts) >= 2:
            logger.warning(f"Multiple critical alerts detected: {len(critical_alerts)}")
            return True
        
        # Check for specific critical conditions
        for alert in critical_alerts:
            if alert["metric"] == "error_rate" and alert["current_value"] > 15.0:
                logger.warning(f"Critical error rate: {alert['current_value']}%")
                return True
            
            if alert["metric"] == "success_rate" and alert["current_value"] < 85.0:
                logger.warning(f"Critical success rate drop: {alert['current_value']}%")
                return True
        
        return False
    
    async def trigger_rollback(self, reason: str) -> bool:
        """
        Trigger deployment rollback.
        
        Args:
            reason: Reason for rollback
            
        Returns:
            True if rollback was triggered successfully
        """
        if not self.current_deployment_id:
            logger.error("Cannot trigger rollback: no active deployment")
            return False
        
        logger.warning(f"Triggering rollback for deployment {self.current_deployment_id}: {reason}")
        
        # Store rollback event
        await self._store_deployment_event("rollback_triggered", {
            "deployment_id": self.current_deployment_id,
            "reason": reason,
            "triggered_at": datetime.now().isoformat()
        })
        
        # Execute rollback callbacks
        rollback_success = True
        for callback in self.rollback_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(self.current_deployment_id, reason)
                else:
                    result = callback(self.current_deployment_id, reason)
                
                if not result:
                    rollback_success = False
                    
            except Exception as e:
                logger.error(f"Rollback callback failed: {str(e)}")
                rollback_success = False
        
        if rollback_success:
            await self._store_deployment_event("rollback_completed", {
                "deployment_id": self.current_deployment_id,
                "completed_at": datetime.now().isoformat()
            })
        else:
            await self._store_deployment_event("rollback_failed", {
                "deployment_id": self.current_deployment_id,
                "failed_at": datetime.now().isoformat()
            })
        
        return rollback_success
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """
        Get current deployment monitoring status.
        
        Returns:
            Current deployment status and metrics
        """
        if not self.monitoring_active or not self.current_deployment_id:
            return {
                "monitoring_active": False,
                "deployment_id": None,
                "status": "no_active_deployment"
            }
        
        # Get latest metrics
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        # Get recent alerts
        recent_alerts = await self._get_recent_alerts(minutes=30)
        
        return {
            "monitoring_active": True,
            "deployment_id": self.current_deployment_id,
            "status": "monitoring",
            "latest_metrics": latest_metrics.__dict__ if latest_metrics else None,
            "recent_alerts": recent_alerts,
            "metrics_history_size": len(self.metrics_history),
            "alert_thresholds": [
                {
                    "metric": t.metric_name,
                    "threshold": t.threshold_value,
                    "severity": t.severity
                }
                for t in self.alert_thresholds
            ]
        }
    
    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback function for alerts."""
        self.alert_callbacks.append(callback)
    
    def add_rollback_callback(self, callback: Callable) -> None:
        """Add callback function for rollbacks."""
        self.rollback_callbacks.append(callback)
    
    # Private helper methods
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring_active:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                if not metrics:
                    await asyncio.sleep(30)  # Wait 30s before retrying
                    continue
                
                # Check alert conditions
                alerts = await self.check_alert_conditions(metrics)
                
                # Execute alert callbacks
                for alert in alerts:
                    for callback in self.alert_callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(alert)
                            else:
                                callback(alert)
                        except Exception as e:
                            logger.error(f"Alert callback failed: {str(e)}")
                
                # Check if rollback should be triggered
                if await self.should_trigger_rollback(alerts):
                    await self.trigger_rollback("Alert threshold exceeded")
                    break  # Stop monitoring after rollback
                
                # Wait before next collection
                await asyncio.sleep(30)  # Collect metrics every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _get_response_time_avg(self) -> float:
        """Get average response time from Redis metrics."""
        try:
            # This would get actual response time metrics
            # For now, return a simulated value
            times = await self.redis_client.lrange("response_times", 0, 100)
            if times:
                avg_time = sum(float(t) for t in times) / len(times)
                return avg_time
            return 100.0  # Default value
        except:
            return 100.0
    
    async def _get_error_rate(self) -> float:
        """Get current error rate percentage."""
        try:
            errors = int(await self.redis_client.get("error_count") or 0)
            total = int(await self.redis_client.get("request_count") or 1)
            return (errors / total) * 100 if total > 0 else 0.0
        except:
            return 0.0
    
    async def _get_success_rate(self) -> float:
        """Get current success rate percentage."""
        return 100.0 - await self._get_error_rate()
    
    async def _get_active_connections(self) -> int:
        """Get number of active connections."""
        try:
            return int(await self.redis_client.get("active_connections") or 0)
        except:
            return 0
    
    async def _get_memory_usage(self) -> float:
        """Get memory usage percentage."""
        try:
            # Run psutil in thread pool to avoid blocking
            import asyncio
            import concurrent.futures
            import psutil
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                memory_percent = await loop.run_in_executor(
                    executor, lambda: psutil.virtual_memory().percent
                )
            return memory_percent
        except:
            return 50.0  # Default value
    
    async def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage."""
        try:
            # Run psutil in thread pool to avoid blocking
            import asyncio
            import concurrent.futures
            import psutil
            
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                cpu_percent = await loop.run_in_executor(
                    executor, lambda: psutil.cpu_percent(interval=1)
                )
            return cpu_percent
        except:
            return 30.0  # Default value
    
    async def _get_queue_health(self) -> str:
        """Get queue system health status."""
        try:
            from app.services.pos_queue_service import get_pos_queue_service
            queue_service = get_pos_queue_service()
            status = await queue_service.get_queue_status()
            
            critical_queues = [
                name for name, info in status.get("queues", {}).items()
                if info.get("status") == "critical"
            ]
            
            if critical_queues:
                return "critical"
            
            warning_queues = [
                name for name, info in status.get("queues", {}).items()
                if info.get("status") == "warning"
            ]
            
            return "warning" if warning_queues else "healthy"
        except:
            return "unknown"
    
    async def _get_database_health(self) -> str:
        """Get database health status."""
        try:
            from app.db.session import SessionLocal
            
            with SessionLocal() as db:
                start_time = time.time()
                db.execute("SELECT 1").scalar()
                response_time = time.time() - start_time
                
                if response_time > 2.0:
                    return "critical"
                elif response_time > 1.0:
                    return "warning"
                else:
                    return "healthy"
        except:
            return "critical"
    
    async def _check_threshold_duration(self, threshold: AlertThreshold, current_metrics: DeploymentMetrics) -> bool:
        """Check if threshold has been exceeded for required duration."""
        # Get historical metrics for the threshold duration
        cutoff_time = current_metrics.timestamp - timedelta(seconds=threshold.duration_seconds)
        
        relevant_metrics = [
            m for m in self.metrics_history
            if m.timestamp >= cutoff_time
        ]
        
        if len(relevant_metrics) < 2:  # Need at least 2 data points
            return False
        
        # Check if all relevant metrics exceed threshold
        for metrics in relevant_metrics:
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                return False
            
            if threshold.comparison == "gt" and metric_value <= threshold.threshold_value:
                return False
            elif threshold.comparison == "lt" and metric_value >= threshold.threshold_value:
                return False
            elif threshold.comparison == "eq" and metric_value != threshold.threshold_value:
                return False
        
        return True
    
    async def _store_metrics(self, metrics: DeploymentMetrics) -> None:
        """Store metrics in Redis."""
        try:
            key = f"deployment_metrics:{metrics.deployment_id}"
            data = {
                "timestamp": metrics.timestamp.isoformat(),
                "response_time_avg": metrics.response_time_avg,
                "error_rate": metrics.error_rate,
                "success_rate": metrics.success_rate,
                "active_connections": metrics.active_connections,
                "memory_usage": metrics.memory_usage,
                "cpu_usage": metrics.cpu_usage,
                "queue_health": metrics.queue_health,
                "database_health": metrics.database_health
            }
            
            await self.redis_client.lpush(key, json.dumps(data))
            await self.redis_client.ltrim(key, 0, 999)  # Keep last 1000 entries
            await self.redis_client.expire(key, 86400)  # Expire after 24 hours
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")
    
    async def _store_alert(self, alert: Dict[str, Any]) -> None:
        """Store alert in Redis."""
        try:
            key = "deployment_alerts"
            await self.redis_client.lpush(key, json.dumps(alert))
            await self.redis_client.ltrim(key, 0, 999)  # Keep last 1000 alerts
            await self.redis_client.expire(key, 604800)  # Expire after 7 days
            
        except Exception as e:
            logger.error(f"Failed to store alert: {str(e)}")
    
    async def _store_deployment_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Store deployment event in Redis."""
        try:
            key = "deployment_events"
            event = {
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                **data
            }
            
            await self.redis_client.lpush(key, json.dumps(event))
            await self.redis_client.ltrim(key, 0, 999)  # Keep last 1000 events
            await self.redis_client.expire(key, 2592000)  # Expire after 30 days
            
        except Exception as e:
            logger.error(f"Failed to store deployment event: {str(e)}")
    
    async def _get_recent_alerts(self, minutes: int = 30) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        try:
            alerts_data = await self.redis_client.lrange("deployment_alerts", 0, 100)
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            
            recent_alerts = []
            for alert_json in alerts_data:
                alert = json.loads(alert_json)
                alert_time = datetime.fromisoformat(alert["timestamp"])
                
                if alert_time >= cutoff_time:
                    recent_alerts.append(alert)
            
            return recent_alerts
            
        except Exception as e:
            logger.error(f"Failed to get recent alerts: {str(e)}")
            return []


# Global deployment monitor instance
_deployment_monitor = None


def get_deployment_monitor() -> DeploymentMonitor:
    """Get the global deployment monitor instance."""
    global _deployment_monitor
    if _deployment_monitor is None:
        _deployment_monitor = DeploymentMonitor()
    return _deployment_monitor