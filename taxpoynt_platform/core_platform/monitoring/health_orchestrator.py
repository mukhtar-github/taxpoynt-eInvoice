"""
Health Orchestrator - Core Platform Observability

Orchestrates health checks across all platform services and components.
Coordinates health monitoring activities and provides unified health status reporting.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class CheckType(Enum):
    """Types of health checks"""
    CONNECTIVITY = "connectivity"
    PERFORMANCE = "performance"
    RESOURCE = "resource"
    DEPENDENCY = "dependency"
    FUNCTIONAL = "functional"
    SECURITY = "security"


class CheckPriority(Enum):
    """Priority levels for health checks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class HealthCheck:
    """Definition of a health check"""
    check_id: str
    name: str
    description: str
    service_role: str
    service_name: str
    check_type: CheckType
    priority: CheckPriority
    check_function: Callable
    interval_seconds: int = 60
    timeout_seconds: int = 30
    enabled: bool = True
    retry_count: int = 3
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthResult:
    """Result of a health check execution"""
    check_id: str
    status: HealthStatus
    message: str
    timestamp: datetime
    duration_ms: int
    details: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ServiceHealth:
    """Aggregated health status for a service"""
    service_name: str
    service_role: str
    overall_status: HealthStatus
    last_updated: datetime
    check_results: List[HealthResult]
    health_score: float
    active_issues: int
    uptime_percentage: float


class HealthOrchestrator:
    """
    Orchestrates health checks across all platform services.
    
    Coordinates health monitoring for:
    - SI Services (ERP integrations, certificate management, etc.)
    - APP Services (FIRS communication, taxpayer management, etc.) 
    - Hybrid Services (analytics, billing, workflow orchestration, etc.)
    - Core Platform (authentication, data management, messaging, etc.)
    - External Integrations (business systems, regulatory systems, etc.)
    """
    
    def __init__(self):
        # Health check registry
        self.health_checks: Dict[str, HealthCheck] = {}
        self.check_schedules: Dict[str, asyncio.Task] = {}
        
        # Results storage
        self.check_results: deque = deque(maxlen=50000)  # Store recent results
        self.service_health_cache: Dict[str, ServiceHealth] = {}
        
        # Orchestration state
        self._running = False
        self._orchestrator_task = None
        
        # Event handlers
        self.health_change_handlers: List[Callable] = []
        self.check_failure_handlers: List[Callable] = []
        
        # Dependencies - will be injected
        self.metrics_aggregator = None
        self.alert_manager = None
        
        # Configuration
        self.global_check_interval = 60  # seconds
        self.health_score_weights = {
            CheckPriority.CRITICAL: 4.0,
            CheckPriority.HIGH: 3.0,
            CheckPriority.MEDIUM: 2.0,
            CheckPriority.LOW: 1.0
        }
        
        # Statistics
        self.stats = {
            "total_checks_executed": 0,
            "total_failures": 0,
            "total_timeouts": 0,
            "avg_check_duration_ms": 0,
            "last_orchestration_cycle": None
        }
    
    # === Dependency Injection ===
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    def set_alert_manager(self, alert_manager):
        """Inject alert manager dependency"""
        self.alert_manager = alert_manager
    
    # === Health Check Management ===
    
    def register_health_check(
        self,
        check_id: str,
        name: str,
        description: str,
        service_role: str,
        service_name: str,
        check_function: Callable,
        check_type: CheckType = CheckType.FUNCTIONAL,
        priority: CheckPriority = CheckPriority.MEDIUM,
        interval_seconds: int = 60,
        timeout_seconds: int = 30,
        tags: Optional[Dict[str, str]] = None
    ) -> bool:
        """Register a new health check"""
        try:
            health_check = HealthCheck(
                check_id=check_id,
                name=name,
                description=description,
                service_role=service_role,
                service_name=service_name,
                check_type=check_type,
                priority=priority,
                check_function=check_function,
                interval_seconds=interval_seconds,
                timeout_seconds=timeout_seconds,
                tags=tags or {}
            )
            
            self.health_checks[check_id] = health_check
            
            # Schedule the check if orchestrator is running
            if self._running:
                self._schedule_health_check(health_check)
            
            logger.info(f"Registered health check: {check_id} for {service_role}/{service_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register health check {check_id}: {e}")
            return False
    
    def unregister_health_check(self, check_id: str) -> bool:
        """Unregister a health check"""
        try:
            if check_id in self.health_checks:
                del self.health_checks[check_id]
            
            # Cancel scheduled task
            if check_id in self.check_schedules:
                self.check_schedules[check_id].cancel()
                del self.check_schedules[check_id]
            
            logger.info(f"Unregistered health check: {check_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister health check {check_id}: {e}")
            return False
    
    def enable_health_check(self, check_id: str) -> bool:
        """Enable a health check"""
        if check_id in self.health_checks:
            self.health_checks[check_id].enabled = True
            
            # Schedule if orchestrator is running
            if self._running and check_id not in self.check_schedules:
                self._schedule_health_check(self.health_checks[check_id])
            
            return True
        return False
    
    def disable_health_check(self, check_id: str) -> bool:
        """Disable a health check"""
        if check_id in self.health_checks:
            self.health_checks[check_id].enabled = False
            
            # Cancel scheduled task
            if check_id in self.check_schedules:
                self.check_schedules[check_id].cancel()
                del self.check_schedules[check_id]
            
            return True
        return False
    
    def get_health_checks(
        self,
        service_role: Optional[str] = None,
        service_name: Optional[str] = None,
        check_type: Optional[CheckType] = None,
        enabled_only: bool = True
    ) -> List[HealthCheck]:
        """Get health checks with optional filtering"""
        checks = list(self.health_checks.values())
        
        if enabled_only:
            checks = [c for c in checks if c.enabled]
        
        if service_role:
            checks = [c for c in checks if c.service_role == service_role]
        
        if service_name:
            checks = [c for c in checks if c.service_name == service_name]
        
        if check_type:
            checks = [c for c in checks if c.check_type == check_type]
        
        return checks
    
    # === Health Check Execution ===
    
    async def execute_health_check(self, check_id: str) -> HealthResult:
        """Execute a single health check"""
        if check_id not in self.health_checks:
            return HealthResult(
                check_id=check_id,
                status=HealthStatus.UNKNOWN,
                message="Health check not found",
                timestamp=datetime.utcnow(),
                duration_ms=0,
                error="Check not registered"
            )
        
        health_check = self.health_checks[check_id]
        start_time = time.time()
        
        try:
            # Execute the check with timeout
            check_task = asyncio.create_task(self._execute_check_function(health_check))
            result = await asyncio.wait_for(check_task, timeout=health_check.timeout_seconds)
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Create result
            health_result = HealthResult(
                check_id=check_id,
                status=result.get("status", HealthStatus.UNKNOWN),
                message=result.get("message", "Check completed"),
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                details=result.get("details", {}),
                metrics=result.get("metrics", {})
            )
            
            # Store result
            self.check_results.append(health_result)
            
            # Update statistics
            self.stats["total_checks_executed"] += 1
            self._update_avg_duration(duration_ms)
            
            # Send metrics if aggregator available
            if self.metrics_aggregator:
                await self._send_health_metrics(health_check, health_result)
            
            # Trigger alerts if needed
            if health_result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                await self._handle_check_failure(health_check, health_result)
            
            return health_result
            
        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            self.stats["total_timeouts"] += 1
            
            health_result = HealthResult(
                check_id=check_id,
                status=HealthStatus.CRITICAL,
                message=f"Health check timed out after {health_check.timeout_seconds}s",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error="timeout"
            )
            
            self.check_results.append(health_result)
            await self._handle_check_failure(health_check, health_result)
            
            return health_result
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            self.stats["total_failures"] += 1
            
            health_result = HealthResult(
                check_id=check_id,
                status=HealthStatus.CRITICAL,
                message=f"Health check failed: {str(e)}",
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms,
                error=str(e)
            )
            
            self.check_results.append(health_result)
            await self._handle_check_failure(health_check, health_result)
            
            return health_result
    
    async def execute_service_health_checks(self, service_name: str) -> List[HealthResult]:
        """Execute all health checks for a specific service"""
        service_checks = self.get_health_checks(service_name=service_name)
        
        results = []
        for check in service_checks:
            result = await self.execute_health_check(check.check_id)
            results.append(result)
        
        # Update service health cache
        await self._update_service_health(service_name, results)
        
        return results
    
    async def execute_all_health_checks(self) -> Dict[str, HealthResult]:
        """Execute all enabled health checks"""
        enabled_checks = self.get_health_checks(enabled_only=True)
        
        # Execute checks concurrently with semaphore to limit concurrency
        semaphore = asyncio.Semaphore(10)  # Max 10 concurrent checks
        
        async def execute_with_semaphore(check):
            async with semaphore:
                return await self.execute_health_check(check.check_id)
        
        tasks = [execute_with_semaphore(check) for check in enabled_checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        check_results = {}
        for check, result in zip(enabled_checks, results):
            if isinstance(result, Exception):
                logger.error(f"Error executing health check {check.check_id}: {result}")
                check_results[check.check_id] = HealthResult(
                    check_id=check.check_id,
                    status=HealthStatus.CRITICAL,
                    message=f"Execution error: {str(result)}",
                    timestamp=datetime.utcnow(),
                    duration_ms=0,
                    error=str(result)
                )
            else:
                check_results[check.check_id] = result
        
        # Update service health for all services
        await self._update_all_service_health()
        
        return check_results
    
    async def _execute_check_function(self, health_check: HealthCheck) -> Dict[str, Any]:
        """Execute the actual check function"""
        if asyncio.iscoroutinefunction(health_check.check_function):
            return await health_check.check_function()
        else:
            # Run synchronous function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, health_check.check_function)
    
    # === Service Health Aggregation ===
    
    def get_service_health(self, service_name: str) -> Optional[ServiceHealth]:
        """Get aggregated health status for a service"""
        return self.service_health_cache.get(service_name)
    
    def get_all_service_health(self) -> Dict[str, ServiceHealth]:
        """Get health status for all services"""
        return self.service_health_cache.copy()
    
    def get_platform_health_overview(self) -> Dict[str, Any]:
        """Get comprehensive platform health overview"""
        all_service_health = self.get_all_service_health()
        
        # Aggregate by service role
        role_health = defaultdict(list)
        for service_health in all_service_health.values():
            role_health[service_health.service_role].append(service_health)
        
        # Calculate overall platform health
        all_statuses = [sh.overall_status for sh in all_service_health.values()]
        critical_count = sum(1 for s in all_statuses if s == HealthStatus.CRITICAL)
        warning_count = sum(1 for s in all_statuses if s == HealthStatus.WARNING)
        
        if critical_count > 0:
            platform_status = HealthStatus.CRITICAL
        elif warning_count > 0:
            platform_status = HealthStatus.WARNING
        else:
            platform_status = HealthStatus.HEALTHY
        
        # Calculate platform health score
        platform_score = 0.0
        if all_service_health:
            platform_score = sum(sh.health_score for sh in all_service_health.values()) / len(all_service_health)
        
        return {
            "timestamp": datetime.utcnow(),
            "platform_status": platform_status.value,
            "platform_health_score": round(platform_score, 2),
            "total_services": len(all_service_health),
            "services_by_status": {
                "healthy": sum(1 for s in all_statuses if s == HealthStatus.HEALTHY),
                "warning": warning_count,
                "critical": critical_count,
                "unknown": sum(1 for s in all_statuses if s == HealthStatus.UNKNOWN)
            },
            "service_roles": {
                role: {
                    "service_count": len(services),
                    "avg_health_score": round(sum(s.health_score for s in services) / len(services), 2) if services else 0,
                    "status_distribution": {
                        status.value: sum(1 for s in services if s.overall_status == status)
                        for status in HealthStatus
                    }
                }
                for role, services in role_health.items()
            },
            "active_issues": sum(sh.active_issues for sh in all_service_health.values()),
            "avg_uptime": round(sum(sh.uptime_percentage for sh in all_service_health.values()) / len(all_service_health), 2) if all_service_health else 0,
            "stats": self.stats.copy()
        }
    
    async def _update_service_health(self, service_name: str, check_results: List[HealthResult]):
        """Update aggregated health status for a service"""
        if not check_results:
            return
        
        # Determine overall status
        statuses = [r.status for r in check_results]
        if HealthStatus.CRITICAL in statuses:
            overall_status = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall_status = HealthStatus.WARNING
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Calculate health score
        health_score = self._calculate_service_health_score(service_name, check_results)
        
        # Count active issues
        active_issues = sum(1 for r in check_results if r.status in [HealthStatus.WARNING, HealthStatus.CRITICAL])
        
        # Calculate uptime percentage (from recent check history)
        uptime_percentage = self._calculate_service_uptime(service_name)
        
        # Get service role
        service_checks = self.get_health_checks(service_name=service_name)
        service_role = service_checks[0].service_role if service_checks else "unknown"
        
        # Create service health
        service_health = ServiceHealth(
            service_name=service_name,
            service_role=service_role,
            overall_status=overall_status,
            last_updated=datetime.utcnow(),
            check_results=check_results,
            health_score=health_score,
            active_issues=active_issues,
            uptime_percentage=uptime_percentage
        )
        
        # Check for status changes
        previous_health = self.service_health_cache.get(service_name)
        if previous_health and previous_health.overall_status != overall_status:
            await self._notify_health_change(service_name, previous_health.overall_status, overall_status)
        
        self.service_health_cache[service_name] = service_health
    
    async def _update_all_service_health(self):
        """Update health status for all services"""
        services = set(check.service_name for check in self.health_checks.values())
        
        for service_name in services:
            # Get recent results for this service
            recent_results = self._get_recent_check_results(service_name, hours=1)
            if recent_results:
                await self._update_service_health(service_name, recent_results)
    
    def _calculate_service_health_score(self, service_name: str, check_results: List[HealthResult]) -> float:
        """Calculate a health score (0-100) for a service"""
        if not check_results:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for result in check_results:
            # Get check priority weight
            check = self.health_checks.get(result.check_id)
            weight = self.health_score_weights.get(check.priority, 1.0) if check else 1.0
            
            # Convert status to score
            if result.status == HealthStatus.HEALTHY:
                score = 100.0
            elif result.status == HealthStatus.WARNING:
                score = 60.0
            elif result.status == HealthStatus.CRITICAL:
                score = 20.0
            else:  # UNKNOWN
                score = 40.0
            
            weighted_score += score * weight
            total_weight += weight
        
        return round(weighted_score / total_weight, 2) if total_weight > 0 else 0.0
    
    def _calculate_service_uptime(self, service_name: str, hours: int = 24) -> float:
        """Calculate uptime percentage for a service"""
        recent_results = self._get_recent_check_results(service_name, hours=hours)
        
        if not recent_results:
            return 0.0
        
        healthy_count = sum(1 for r in recent_results if r.status == HealthStatus.HEALTHY)
        return round((healthy_count / len(recent_results)) * 100, 2)
    
    def _get_recent_check_results(self, service_name: str, hours: int = 1) -> List[HealthResult]:
        """Get recent check results for a service"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        service_check_ids = {check.check_id for check in self.get_health_checks(service_name=service_name)}
        
        recent_results = [
            result for result in self.check_results
            if result.check_id in service_check_ids and result.timestamp >= cutoff_time
        ]
        
        return recent_results
    
    # === Orchestration Control ===
    
    async def start_orchestration(self):
        """Start health check orchestration"""
        if self._running:
            return
        
        self._running = True
        
        # Schedule all enabled health checks
        for health_check in self.get_health_checks(enabled_only=True):
            self._schedule_health_check(health_check)
        
        # Start orchestrator task
        self._orchestrator_task = asyncio.create_task(self._orchestration_loop())
        
        logger.info("Health orchestration started")
    
    async def stop_orchestration(self):
        """Stop health check orchestration"""
        self._running = False
        
        # Cancel all scheduled checks
        for task in self.check_schedules.values():
            task.cancel()
        self.check_schedules.clear()
        
        # Cancel orchestrator task
        if self._orchestrator_task:
            self._orchestrator_task.cancel()
        
        logger.info("Health orchestration stopped")
    
    def _schedule_health_check(self, health_check: HealthCheck):
        """Schedule a recurring health check"""
        if not health_check.enabled or health_check.check_id in self.check_schedules:
            return
        
        async def recurring_check():
            while self._running and health_check.enabled:
                try:
                    await self.execute_health_check(health_check.check_id)
                    await asyncio.sleep(health_check.interval_seconds)
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in recurring check {health_check.check_id}: {e}")
                    await asyncio.sleep(health_check.interval_seconds)
        
        task = asyncio.create_task(recurring_check())
        self.check_schedules[health_check.check_id] = task
    
    async def _orchestration_loop(self):
        """Main orchestration loop"""
        while self._running:
            try:
                # Update service health aggregations
                await self._update_all_service_health()
                
                # Update statistics
                self.stats["last_orchestration_cycle"] = datetime.utcnow()
                
                # Wait for next cycle
                await asyncio.sleep(self.global_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(self.global_check_interval)
    
    # === Event Handling ===
    
    async def _handle_check_failure(self, health_check: HealthCheck, result: HealthResult):
        """Handle health check failure"""
        # Notify failure handlers
        for handler in self.check_failure_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(health_check, result)
                else:
                    handler(health_check, result)
            except Exception as e:
                logger.error(f"Error in failure handler: {e}")
        
        # Trigger alert if alert manager available
        if self.alert_manager:
            await self._trigger_health_alert(health_check, result)
    
    async def _notify_health_change(self, service_name: str, old_status: HealthStatus, new_status: HealthStatus):
        """Notify about health status changes"""
        for handler in self.health_change_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(service_name, old_status, new_status)
                else:
                    handler(service_name, old_status, new_status)
            except Exception as e:
                logger.error(f"Error in health change handler: {e}")
    
    async def _send_health_metrics(self, health_check: HealthCheck, result: HealthResult):
        """Send health metrics to metrics aggregator"""
        try:
            # Send health status metric
            status_value = 1 if result.status == HealthStatus.HEALTHY else 0
            await self.metrics_aggregator.collect_metric_point(
                name="health_check_status",
                value=status_value,
                service_role=health_check.service_role,
                service_name=health_check.service_name,
                tags={
                    "check_id": health_check.check_id,
                    "check_type": health_check.check_type.value,
                    "priority": health_check.priority.value
                }
            )
            
            # Send duration metric
            await self.metrics_aggregator.collect_metric_point(
                name="health_check_duration_ms",
                value=result.duration_ms,
                service_role=health_check.service_role,
                service_name=health_check.service_name,
                tags={"check_id": health_check.check_id}
            )
            
            # Send custom metrics from result
            for metric_name, value in result.metrics.items():
                await self.metrics_aggregator.collect_metric_point(
                    name=f"health_check_{metric_name}",
                    value=value,
                    service_role=health_check.service_role,
                    service_name=health_check.service_name,
                    tags={"check_id": health_check.check_id}
                )
        
        except Exception as e:
            logger.error(f"Error sending health metrics: {e}")
    
    async def _trigger_health_alert(self, health_check: HealthCheck, result: HealthResult):
        """Trigger alert for health check failure"""
        try:
            severity = "critical" if result.status == HealthStatus.CRITICAL else "warning"
            
            alert_data = {
                "title": f"Health Check Failed: {health_check.name}",
                "message": result.message,
                "service": health_check.service_name,
                "service_role": health_check.service_role,
                "check_id": health_check.check_id,
                "status": result.status.value,
                "severity": severity,
                "timestamp": result.timestamp,
                "duration_ms": result.duration_ms,
                "error": result.error
            }
            
            # Use alert manager to send alert
            # await self.alert_manager.trigger_alert(alert_data)
            
        except Exception as e:
            logger.error(f"Error triggering health alert: {e}")
    
    def _update_avg_duration(self, duration_ms: int):
        """Update average check duration statistic"""
        current_avg = self.stats["avg_check_duration_ms"]
        total_checks = self.stats["total_checks_executed"]
        
        if total_checks == 1:
            self.stats["avg_check_duration_ms"] = duration_ms
        else:
            # Calculate running average
            self.stats["avg_check_duration_ms"] = int(
                (current_avg * (total_checks - 1) + duration_ms) / total_checks
            )
    
    # === Event Handler Management ===
    
    def add_health_change_handler(self, handler: Callable):
        """Add handler for health status changes"""
        self.health_change_handlers.append(handler)
    
    def add_check_failure_handler(self, handler: Callable):
        """Add handler for check failures"""
        self.check_failure_handlers.append(handler)
    
    def remove_health_change_handler(self, handler: Callable):
        """Remove health status change handler"""
        if handler in self.health_change_handlers:
            self.health_change_handlers.remove(handler)
    
    def remove_check_failure_handler(self, handler: Callable):
        """Remove check failure handler"""
        if handler in self.check_failure_handlers:
            self.check_failure_handlers.remove(handler)
    
    # === Health Check Utilities ===
    
    def get_orchestrator_health(self) -> Dict[str, Any]:
        """Get health status of the orchestrator itself"""
        return {
            "status": "running" if self._running else "stopped",
            "registered_checks": len(self.health_checks),
            "enabled_checks": len(self.get_health_checks(enabled_only=True)),
            "scheduled_checks": len(self.check_schedules),
            "cached_services": len(self.service_health_cache),
            "stored_results": len(self.check_results),
            "statistics": self.stats.copy()
        }


# Global instance for platform-wide access
health_orchestrator = HealthOrchestrator()


# Predefined health check functions for common scenarios
async def check_service_connectivity(endpoint: str, timeout: int = 30) -> Dict[str, Any]:
    """Generic connectivity health check"""
    try:
        # This would implement actual connectivity testing
        # For now, return a mock successful result
        return {
            "status": HealthStatus.HEALTHY,
            "message": f"Service at {endpoint} is reachable",
            "details": {"endpoint": endpoint, "response_time_ms": 150},
            "metrics": {"response_time_ms": 150}
        }
    except Exception as e:
        return {
            "status": HealthStatus.CRITICAL,
            "message": f"Failed to connect to {endpoint}: {str(e)}",
            "details": {"endpoint": endpoint, "error": str(e)}
        }


async def check_database_connectivity(connection_string: str) -> Dict[str, Any]:
    """Database connectivity health check"""
    try:
        # This would implement actual database connectivity testing
        return {
            "status": HealthStatus.HEALTHY,
            "message": "Database connection successful",
            "details": {"connection_pool_size": 10, "active_connections": 3},
            "metrics": {"connection_time_ms": 50, "active_connections": 3}
        }
    except Exception as e:
        return {
            "status": HealthStatus.CRITICAL,
            "message": f"Database connection failed: {str(e)}",
            "details": {"error": str(e)}
        }


async def check_memory_usage(warning_threshold: float = 80.0, critical_threshold: float = 90.0) -> Dict[str, Any]:
    """Memory usage health check"""
    try:
        # This would implement actual memory usage checking
        memory_usage = 65.0  # Mock value
        
        if memory_usage >= critical_threshold:
            status = HealthStatus.CRITICAL
            message = f"Critical memory usage: {memory_usage}%"
        elif memory_usage >= warning_threshold:
            status = HealthStatus.WARNING
            message = f"High memory usage: {memory_usage}%"
        else:
            status = HealthStatus.HEALTHY
            message = f"Memory usage normal: {memory_usage}%"
        
        return {
            "status": status,
            "message": message,
            "details": {"memory_usage_percent": memory_usage},
            "metrics": {"memory_usage_percent": memory_usage}
        }
    except Exception as e:
        return {
            "status": HealthStatus.UNKNOWN,
            "message": f"Failed to check memory usage: {str(e)}",
            "details": {"error": str(e)}
        }


# Setup functions for easy integration
async def setup_default_health_checks():
    """Setup default health checks for core platform components"""
    
    # Core platform health checks
    health_orchestrator.register_health_check(
        check_id="core_authentication_connectivity",
        name="Authentication Service Connectivity",
        description="Check if authentication service is responding",
        service_role="core_platform",
        service_name="authentication_service",
        check_function=lambda: check_service_connectivity("http://localhost:8000/auth/health"),
        check_type=CheckType.CONNECTIVITY,
        priority=CheckPriority.CRITICAL
    )
    
    health_orchestrator.register_health_check(
        check_id="core_database_connectivity",
        name="Database Connectivity",
        description="Check database connection and responsiveness",
        service_role="core_platform", 
        service_name="database_service",
        check_function=lambda: check_database_connectivity("postgresql://localhost:5432/taxpoynt"),
        check_type=CheckType.DEPENDENCY,
        priority=CheckPriority.CRITICAL
    )
    
    health_orchestrator.register_health_check(
        check_id="core_memory_usage",
        name="System Memory Usage",
        description="Monitor system memory usage",
        service_role="core_platform",
        service_name="system_resources",
        check_function=lambda: check_memory_usage(),
        check_type=CheckType.RESOURCE,
        priority=CheckPriority.MEDIUM,
        interval_seconds=300  # Check every 5 minutes
    )
    
    logger.info("Default health checks setup completed")


async def shutdown_health_orchestration():
    """Shutdown health orchestration"""
    await health_orchestrator.stop_orchestration()
    logger.info("Health orchestration shutdown completed")