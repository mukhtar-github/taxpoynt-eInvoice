"""
Health Monitor - Universal Connector Framework
Comprehensive health monitoring and observability for external system connectors.
Provides health checks, performance metrics, alerting, and diagnostic capabilities.
"""

import asyncio
import logging
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric type enumeration."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheck:
    """Health check definition."""
    name: str
    check_function: Callable
    interval: int = 60  # seconds
    timeout: int = 30   # seconds
    critical: bool = False
    tags: Dict[str, str] = field(default_factory=dict)
    last_run: Optional[datetime] = None
    last_status: HealthStatus = HealthStatus.UNKNOWN
    last_result: Optional[Dict[str, Any]] = None
    consecutive_failures: int = 0
    enabled: bool = True


@dataclass
class Metric:
    """Metric data point."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None


@dataclass
class Alert:
    """Alert definition and state."""
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str = "warning"  # info, warning, error, critical
    message_template: str = "Alert triggered: {name}"
    cooldown: int = 300  # seconds
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    is_active: bool = False
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ConnectorStats:
    """Connector statistics."""
    connector_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)
    status: HealthStatus = HealthStatus.UNKNOWN
    error_rate: float = 0.0
    throughput: float = 0.0  # requests per second


class HealthMonitor:
    """
    Comprehensive health monitoring system for connectors.
    Provides health checks, metrics collection, alerting, and diagnostics.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize health monitor."""
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Health checks
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_scheduler_task: Optional[asyncio.Task] = None
        
        # Metrics
        self.metrics: List[Metric] = []
        self.metric_aggregations: Dict[str, List[float]] = {}
        self.max_metrics_history = self.config.get('max_metrics_history', 10000)
        
        # Alerts
        self.alerts: Dict[str, Alert] = {}
        self.alert_handlers: List[Callable] = []
        
        # Connector statistics
        self.connector_stats: Dict[str, ConnectorStats] = {}
        
        # Performance tracking
        self.response_times: Dict[str, List[float]] = {}
        self.max_response_time_history = self.config.get('max_response_time_history', 1000)
        
        # Circuit breaker states
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.start_time = datetime.now()
        
        # Configure default health checks
        self._configure_default_health_checks()
        
        # Configure default alerts
        self._configure_default_alerts()
    
    async def start_monitoring(self) -> None:
        """Start health monitoring."""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.start_time = datetime.now()
        
        # Start health check scheduler
        self.check_scheduler_task = asyncio.create_task(self._health_check_scheduler())
        
        self.logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self.is_monitoring = False
        
        if self.check_scheduler_task:
            self.check_scheduler_task.cancel()
            try:
                await self.check_scheduler_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Health monitoring stopped")
    
    def register_connector(self, connector_id: str) -> None:
        """Register a connector for monitoring."""
        if connector_id not in self.connector_stats:
            self.connector_stats[connector_id] = ConnectorStats(
                connector_id=connector_id
            )
            self.response_times[connector_id] = []
            
            # Initialize circuit breaker
            self.circuit_breakers[connector_id] = {
                'state': 'closed',  # closed, open, half_open
                'failure_count': 0,
                'last_failure_time': None,
                'next_attempt_time': None,
                'failure_threshold': self.config.get('circuit_breaker_failure_threshold', 5),
                'recovery_timeout': self.config.get('circuit_breaker_recovery_timeout', 60)
            }
            
            self.logger.info(f"Registered connector for monitoring: {connector_id}")
    
    def unregister_connector(self, connector_id: str) -> None:
        """Unregister a connector from monitoring."""
        self.connector_stats.pop(connector_id, None)
        self.response_times.pop(connector_id, None)
        self.circuit_breakers.pop(connector_id, None)
        
        self.logger.info(f"Unregistered connector from monitoring: {connector_id}")
    
    def record_request(self, connector_id: str, success: bool, response_time: float, 
                      error: Optional[str] = None) -> None:
        """Record a connector request for monitoring."""
        if connector_id not in self.connector_stats:
            self.register_connector(connector_id)
        
        stats = self.connector_stats[connector_id]
        stats.total_requests += 1
        stats.last_request_time = datetime.now()
        
        if success:
            stats.successful_requests += 1
            self._update_circuit_breaker_success(connector_id)
        else:
            stats.failed_requests += 1
            self._update_circuit_breaker_failure(connector_id)
        
        # Update response time
        response_times = self.response_times[connector_id]
        response_times.append(response_time)
        
        # Keep only recent response times
        if len(response_times) > self.max_response_time_history:
            response_times.pop(0)
        
        # Calculate averages
        if response_times:
            stats.avg_response_time = statistics.mean(response_times)
        
        # Calculate error rate
        if stats.total_requests > 0:
            stats.error_rate = stats.failed_requests / stats.total_requests
        
        # Calculate throughput (requests per second over last minute)
        recent_requests = self._count_recent_requests(connector_id, 60)
        stats.throughput = recent_requests / 60.0
        
        # Record metrics
        self._record_metric(f"connector.{connector_id}.response_time", response_time, 
                          MetricType.TIMER, {"connector_id": connector_id})
        self._record_metric(f"connector.{connector_id}.requests.total", 1, 
                          MetricType.COUNTER, {"connector_id": connector_id})
        
        if success:
            self._record_metric(f"connector.{connector_id}.requests.success", 1, 
                              MetricType.COUNTER, {"connector_id": connector_id, "status": "success"})
        else:
            self._record_metric(f"connector.{connector_id}.requests.failure", 1, 
                              MetricType.COUNTER, {"connector_id": connector_id, "status": "failure"})
    
    def add_health_check(self, health_check: HealthCheck) -> None:
        """Add a health check."""
        self.health_checks[health_check.name] = health_check
        self.logger.info(f"Added health check: {health_check.name}")
    
    def remove_health_check(self, name: str) -> None:
        """Remove a health check."""
        self.health_checks.pop(name, None)
        self.logger.info(f"Removed health check: {name}")
    
    async def run_health_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self.health_checks:
            raise ValueError(f"Health check not found: {name}")
        
        health_check = self.health_checks[name]
        
        if not health_check.enabled:
            return {
                'name': name,
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Health check disabled',
                'timestamp': datetime.now().isoformat()
            }
        
        start_time = time.time()
        
        try:
            # Run health check with timeout
            result = await asyncio.wait_for(
                health_check.check_function(),
                timeout=health_check.timeout
            )
            
            health_check.last_run = datetime.now()
            health_check.consecutive_failures = 0
            
            if isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                result = {'healthy': result}
            elif isinstance(result, dict):
                status = HealthStatus(result.get('status', HealthStatus.HEALTHY.value))
            else:
                status = HealthStatus.HEALTHY
                result = {'result': result}
            
            health_check.last_status = status
            health_check.last_result = result
            
            duration = time.time() - start_time
            
            return {
                'name': name,
                'status': status.value,
                'duration': duration,
                'timestamp': health_check.last_run.isoformat(),
                'result': result,
                'tags': health_check.tags
            }
            
        except asyncio.TimeoutError:
            health_check.consecutive_failures += 1
            health_check.last_status = HealthStatus.UNHEALTHY
            duration = time.time() - start_time
            
            return {
                'name': name,
                'status': HealthStatus.UNHEALTHY.value,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'error': 'Health check timeout',
                'tags': health_check.tags
            }
            
        except Exception as e:
            health_check.consecutive_failures += 1
            health_check.last_status = HealthStatus.UNHEALTHY
            duration = time.time() - start_time
            
            self.logger.error(f"Health check failed: {name} - {str(e)}")
            
            return {
                'name': name,
                'status': HealthStatus.UNHEALTHY.value,
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'tags': health_check.tags
            }
    
    async def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        if not self.health_checks:
            return {
                'status': HealthStatus.UNKNOWN.value,
                'message': 'No health checks configured',
                'timestamp': datetime.now().isoformat()
            }
        
        # Run all enabled health checks
        results = []
        for name, health_check in self.health_checks.items():
            if health_check.enabled:
                result = await self.run_health_check(name)
                results.append(result)
        
        # Determine overall status
        critical_unhealthy = any(
            result['status'] == HealthStatus.UNHEALTHY.value and 
            self.health_checks[result['name']].critical
            for result in results
        )
        
        any_unhealthy = any(
            result['status'] == HealthStatus.UNHEALTHY.value
            for result in results
        )
        
        any_degraded = any(
            result['status'] == HealthStatus.DEGRADED.value
            for result in results
        )
        
        if critical_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif any_unhealthy:
            overall_status = HealthStatus.DEGRADED
        elif any_degraded:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.now().isoformat(),
            'checks': results,
            'uptime': str(datetime.now() - self.start_time),
            'connector_count': len(self.connector_stats)
        }
    
    def add_alert(self, alert: Alert) -> None:
        """Add an alert."""
        self.alerts[alert.name] = alert
        self.logger.info(f"Added alert: {alert.name}")
    
    def remove_alert(self, name: str) -> None:
        """Remove an alert."""
        self.alerts.pop(name, None)
        self.logger.info(f"Removed alert: {name}")
    
    def add_alert_handler(self, handler: Callable) -> None:
        """Add an alert handler."""
        self.alert_handlers.append(handler)
    
    def get_connector_health(self, connector_id: str) -> Dict[str, Any]:
        """Get health status for a specific connector."""
        if connector_id not in self.connector_stats:
            return {
                'connector_id': connector_id,
                'status': HealthStatus.UNKNOWN.value,
                'message': 'Connector not registered'
            }
        
        stats = self.connector_stats[connector_id]
        circuit_breaker = self.circuit_breakers[connector_id]
        
        # Determine health status
        if circuit_breaker['state'] == 'open':
            status = HealthStatus.UNHEALTHY
        elif stats.error_rate > 0.5:  # 50% error rate
            status = HealthStatus.UNHEALTHY
        elif stats.error_rate > 0.1:  # 10% error rate
            status = HealthStatus.DEGRADED
        elif stats.avg_response_time > 5000:  # 5 second response time
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        stats.status = status
        
        uptime = datetime.now() - stats.uptime_start
        
        return {
            'connector_id': connector_id,
            'status': status.value,
            'total_requests': stats.total_requests,
            'successful_requests': stats.successful_requests,
            'failed_requests': stats.failed_requests,
            'error_rate': stats.error_rate,
            'avg_response_time': stats.avg_response_time,
            'throughput': stats.throughput,
            'last_request_time': stats.last_request_time.isoformat() if stats.last_request_time else None,
            'uptime': str(uptime),
            'circuit_breaker_state': circuit_breaker['state']
        }
    
    def get_all_connector_health(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all connectors."""
        return {
            connector_id: self.get_connector_health(connector_id)
            for connector_id in self.connector_stats.keys()
        }
    
    def get_metrics(self, name_pattern: Optional[str] = None, 
                   time_range: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get metrics, optionally filtered by name pattern and time range."""
        metrics = self.metrics
        
        if time_range:
            cutoff_time = datetime.now() - timedelta(seconds=time_range)
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]
        
        if name_pattern:
            metrics = [m for m in metrics if name_pattern in m.name]
        
        return [
            {
                'name': m.name,
                'value': m.value,
                'type': m.metric_type.value,
                'timestamp': m.timestamp.isoformat(),
                'tags': m.tags,
                'unit': m.unit
            }
            for m in metrics
        ]
    
    def is_circuit_breaker_open(self, connector_id: str) -> bool:
        """Check if circuit breaker is open for a connector."""
        if connector_id not in self.circuit_breakers:
            return False
        
        circuit_breaker = self.circuit_breakers[connector_id]
        
        if circuit_breaker['state'] == 'open':
            # Check if recovery timeout has passed
            if (circuit_breaker['next_attempt_time'] and 
                datetime.now() >= circuit_breaker['next_attempt_time']):
                circuit_breaker['state'] = 'half_open'
                return False
            return True
        
        return False
    
    async def get_diagnostics(self, connector_id: Optional[str] = None) -> Dict[str, Any]:
        """Get diagnostic information."""
        diagnostics = {
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.start_time),
            'monitoring_active': self.is_monitoring,
            'health_checks_count': len(self.health_checks),
            'alerts_count': len(self.alerts),
            'metrics_count': len(self.metrics),
            'connectors_count': len(self.connector_stats)
        }
        
        if connector_id:
            if connector_id in self.connector_stats:
                diagnostics['connector'] = self.get_connector_health(connector_id)
                diagnostics['recent_response_times'] = self.response_times.get(connector_id, [])[-10:]
            else:
                diagnostics['error'] = f"Connector not found: {connector_id}"
        else:
            diagnostics['connectors'] = self.get_all_connector_health()
        
        return diagnostics
    
    def _configure_default_health_checks(self) -> None:
        """Configure default health checks."""
        # System health check
        async def system_health_check():
            return {
                'status': HealthStatus.HEALTHY.value,
                'memory_usage': 'ok',  # Could add actual memory monitoring
                'cpu_usage': 'ok'      # Could add actual CPU monitoring
            }
        
        self.add_health_check(HealthCheck(
            name='system',
            check_function=system_health_check,
            interval=60,
            critical=True,
            tags={'type': 'system'}
        ))
    
    def _configure_default_alerts(self) -> None:
        """Configure default alerts."""
        # High error rate alert
        def high_error_rate_condition(stats):
            return any(
                connector_stats.error_rate > 0.2  # 20% error rate
                for connector_stats in stats.values()
            )
        
        self.add_alert(Alert(
            name='high_error_rate',
            condition=high_error_rate_condition,
            severity='warning',
            message_template='High error rate detected: {error_rate:.2%}',
            cooldown=300
        ))
        
        # Circuit breaker open alert
        def circuit_breaker_open_condition(stats):
            return any(
                cb['state'] == 'open'
                for cb in self.circuit_breakers.values()
            )
        
        self.add_alert(Alert(
            name='circuit_breaker_open',
            condition=circuit_breaker_open_condition,
            severity='error',
            message_template='Circuit breaker opened for connector',
            cooldown=600
        ))
    
    async def _health_check_scheduler(self) -> None:
        """Health check scheduler task."""
        while self.is_monitoring:
            try:
                current_time = datetime.now()
                
                for name, health_check in self.health_checks.items():
                    if not health_check.enabled:
                        continue
                    
                    # Check if it's time to run the health check
                    if (health_check.last_run is None or 
                        current_time >= health_check.last_run + timedelta(seconds=health_check.interval)):
                        
                        try:
                            await self.run_health_check(name)
                        except Exception as e:
                            self.logger.error(f"Error running health check {name}: {str(e)}")
                
                # Check alerts
                await self._check_alerts()
                
                # Wait before next iteration
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in health check scheduler: {str(e)}")
                await asyncio.sleep(30)  # Wait longer on error
    
    async def _check_alerts(self) -> None:
        """Check and trigger alerts."""
        current_time = datetime.now()
        
        for alert in self.alerts.values():
            if not alert.enabled:
                continue
            
            # Check cooldown
            if (alert.last_triggered and 
                current_time < alert.last_triggered + timedelta(seconds=alert.cooldown)):
                continue
            
            try:
                # Check alert condition
                should_trigger = alert.condition(self.connector_stats)
                
                if should_trigger and not alert.is_active:
                    # Trigger alert
                    alert.is_active = True
                    alert.last_triggered = current_time
                    
                    message = alert.message_template.format(
                        name=alert.name,
                        timestamp=current_time.isoformat()
                    )
                    
                    alert_data = {
                        'name': alert.name,
                        'severity': alert.severity,
                        'message': message,
                        'timestamp': current_time.isoformat(),
                        'tags': alert.tags
                    }
                    
                    # Send to alert handlers
                    for handler in self.alert_handlers:
                        try:
                            await handler(alert_data)
                        except Exception as e:
                            self.logger.error(f"Error in alert handler: {str(e)}")
                    
                    self.logger.warning(f"Alert triggered: {alert.name} - {message}")
                
                elif not should_trigger and alert.is_active:
                    # Clear alert
                    alert.is_active = False
                    self.logger.info(f"Alert cleared: {alert.name}")
                    
            except Exception as e:
                self.logger.error(f"Error checking alert {alert.name}: {str(e)}")
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, 
                      tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric."""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Keep only recent metrics
        if len(self.metrics) > self.max_metrics_history:
            self.metrics.pop(0)
        
        # Update aggregations for gauge metrics
        if metric_type == MetricType.GAUGE:
            if name not in self.metric_aggregations:
                self.metric_aggregations[name] = []
            
            aggregation = self.metric_aggregations[name]
            aggregation.append(value)
            
            # Keep only recent values
            if len(aggregation) > 100:
                aggregation.pop(0)
    
    def _update_circuit_breaker_success(self, connector_id: str) -> None:
        """Update circuit breaker on successful request."""
        circuit_breaker = self.circuit_breakers[connector_id]
        
        if circuit_breaker['state'] == 'half_open':
            # Reset circuit breaker
            circuit_breaker['state'] = 'closed'
            circuit_breaker['failure_count'] = 0
            circuit_breaker['last_failure_time'] = None
            circuit_breaker['next_attempt_time'] = None
        elif circuit_breaker['state'] == 'closed':
            # Reset failure count on success
            circuit_breaker['failure_count'] = 0
    
    def _update_circuit_breaker_failure(self, connector_id: str) -> None:
        """Update circuit breaker on failed request."""
        circuit_breaker = self.circuit_breakers[connector_id]
        current_time = datetime.now()
        
        circuit_breaker['failure_count'] += 1
        circuit_breaker['last_failure_time'] = current_time
        
        # Check if we should open the circuit breaker
        if (circuit_breaker['state'] in ['closed', 'half_open'] and
            circuit_breaker['failure_count'] >= circuit_breaker['failure_threshold']):
            
            circuit_breaker['state'] = 'open'
            circuit_breaker['next_attempt_time'] = (
                current_time + timedelta(seconds=circuit_breaker['recovery_timeout'])
            )
            
            self.logger.warning(f"Circuit breaker opened for connector: {connector_id}")
    
    def _count_recent_requests(self, connector_id: str, seconds: int) -> int:
        """Count requests in the last N seconds."""
        if connector_id not in self.connector_stats:
            return 0
        
        stats = self.connector_stats[connector_id]
        if not stats.last_request_time:
            return 0
        
        # This is a simplified implementation
        # In a real system, you'd track individual request timestamps
        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        
        if stats.last_request_time >= cutoff_time:
            # Estimate based on throughput
            return min(stats.total_requests, int(stats.throughput * seconds))
        
        return 0


# Example usage and health check implementations
async def example_database_health_check():
    """Example database health check."""
    try:
        # Simulate database ping
        await asyncio.sleep(0.1)
        return {
            'status': HealthStatus.HEALTHY.value,
            'connection_pool_size': 10,
            'active_connections': 3
        }
    except Exception as e:
        return {
            'status': HealthStatus.UNHEALTHY.value,
            'error': str(e)
        }


async def example_external_service_health_check():
    """Example external service health check."""
    try:
        # Simulate external service check
        await asyncio.sleep(0.2)
        return True  # Simple boolean result
    except Exception:
        return False


# Alert handler examples
async def log_alert_handler(alert_data: Dict[str, Any]) -> None:
    """Example alert handler that logs alerts."""
    logger = logging.getLogger(__name__)
    logger.warning(f"ALERT: {alert_data['severity'].upper()} - {alert_data['message']}")


async def email_alert_handler(alert_data: Dict[str, Any]) -> None:
    """Example alert handler that sends email notifications."""
    # This would integrate with an email service
    print(f"EMAIL ALERT: {alert_data['message']}")


if __name__ == "__main__":
    async def main():
        # Example usage
        monitor = HealthMonitor({
            'max_metrics_history': 5000,
            'circuit_breaker_failure_threshold': 3,
            'circuit_breaker_recovery_timeout': 30
        })
        
        # Add custom health checks
        monitor.add_health_check(HealthCheck(
            name='database',
            check_function=example_database_health_check,
            interval=30,
            critical=True,
            tags={'component': 'database'}
        ))
        
        monitor.add_health_check(HealthCheck(
            name='external_service',
            check_function=example_external_service_health_check,
            interval=60,
            tags={'component': 'external'}
        ))
        
        # Add alert handlers
        monitor.add_alert_handler(log_alert_handler)
        
        # Register connectors
        monitor.register_connector('erp_connector')
        monitor.register_connector('crm_connector')
        
        # Start monitoring
        await monitor.start_monitoring()
        
        # Simulate some activity
        for i in range(10):
            success = i % 3 != 0  # Simulate some failures
            response_time = 100 + (i * 50)  # Simulate varying response times
            
            monitor.record_request('erp_connector', success, response_time)
            await asyncio.sleep(1)
        
        # Get health status
        overall_health = await monitor.get_overall_health()
        print("Overall Health:", json.dumps(overall_health, indent=2))
        
        connector_health = monitor.get_connector_health('erp_connector')
        print("ERP Connector Health:", json.dumps(connector_health, indent=2))
        
        # Get diagnostics
        diagnostics = await monitor.get_diagnostics()
        print("Diagnostics:", json.dumps(diagnostics, indent=2))
        
        # Stop monitoring
        await monitor.stop_monitoring()
    
    asyncio.run(main())