"""
Health monitoring for integration connectors.

This module provides monitoring capabilities for integration connectors,
tracking metrics, health status, and providing observability.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Integration health status enum."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    UNKNOWN = "unknown"


class OperationMetrics(BaseModel):
    """Metrics for integration operations."""
    operation_name: str
    success_count: int = 0
    failure_count: int = 0
    total_duration_ms: float = 0
    last_execution_time: Optional[datetime] = None
    last_status: bool = False
    last_error: Optional[str] = None
    
    @property
    def avg_duration_ms(self) -> float:
        """Calculate average operation duration in milliseconds."""
        total_ops = self.success_count + self.failure_count
        if total_ops > 0:
            return self.total_duration_ms / total_ops
        return 0
    
    @property
    def success_rate(self) -> float:
        """Calculate operation success rate."""
        total_ops = self.success_count + self.failure_count
        if total_ops > 0:
            return self.success_count / total_ops
        return 1.0  # Default to 100% if no operations


class IntegrationHealth(BaseModel):
    """Integration health status and metrics."""
    integration_type: str
    integration_name: str
    connection_id: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_check: Optional[datetime] = None
    metrics: Dict[str, OperationMetrics] = Field(default_factory=dict)
    health_history: List[Dict[str, Any]] = Field(default_factory=list)


class IntegrationMonitor:
    """Monitor for integration connectors."""
    
    def __init__(self, integration_type: str, integration_name: str, connection_id: str):
        """
        Initialize the integration monitor.
        
        Args:
            integration_type: Type of integration (CRM, POS, ERP)
            integration_name: Name of the integration (HubSpot, Square, etc.)
            connection_id: Unique identifier for this connection
        """
        self.integration_type = integration_type
        self.integration_name = integration_name
        self.connection_id = connection_id
        self.health = IntegrationHealth(
            integration_type=integration_type,
            integration_name=integration_name,
            connection_id=connection_id
        )
        logger.info(
            f"Initialized monitoring for {integration_type}/{integration_name} "
            f"(connection_id: {connection_id})"
        )
    
    def record_operation(self, operation_name: str, success: bool, 
                         duration_ms: float, error: Optional[str] = None) -> None:
        """
        Record metrics for an integration operation.
        
        Args:
            operation_name: Name of the operation
            success: Whether the operation was successful
            duration_ms: Duration of the operation in milliseconds
            error: Error message if operation failed
        """
        if operation_name not in self.health.metrics:
            self.health.metrics[operation_name] = OperationMetrics(operation_name=operation_name)
            
        metrics = self.health.metrics[operation_name]
        
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
            metrics.last_error = error
            
        metrics.total_duration_ms += duration_ms
        metrics.last_execution_time = datetime.now()
        metrics.last_status = success
        
        # Update overall health status based on recent operations
        self._update_health_status()
        
        # Log significant events
        if not success:
            logger.warning(
                f"{self.integration_type}/{self.integration_name} operation '{operation_name}' "
                f"failed in {duration_ms:.2f}ms: {error}"
            )
        
    def _update_health_status(self) -> None:
        """Update the overall health status based on recent metrics."""
        # Set default status
        status = HealthStatus.UNKNOWN
        
        # Only evaluate status if we have metrics
        if self.health.metrics:
            # Calculate overall success rate
            total_success = sum(m.success_count for m in self.health.metrics.values())
            total_failures = sum(m.failure_count for m in self.health.metrics.values())
            total_ops = total_success + total_failures
            
            if total_ops > 0:
                success_rate = total_success / total_ops
                
                # Set status based on success rate
                if success_rate >= 0.95:  # 95% or higher
                    status = HealthStatus.HEALTHY
                elif success_rate >= 0.80:  # 80-95%
                    status = HealthStatus.DEGRADED
                else:  # Below 80%
                    status = HealthStatus.FAILING
            
            # Check for recent failures
            recent_failures = False
            for metrics in self.health.metrics.values():
                if (metrics.last_execution_time and 
                    not metrics.last_status and
                    metrics.last_execution_time > datetime.now() - timedelta(minutes=5)):
                    recent_failures = True
                    break
                    
            # Recent failures override healthy status
            if status == HealthStatus.HEALTHY and recent_failures:
                status = HealthStatus.DEGRADED
        
        # Update status and last check time
        previous_status = self.health.status
        self.health.status = status
        self.health.last_check = datetime.now()
        
        # Record status change in history
        if status != previous_status:
            self.health.health_history.append({
                "timestamp": self.health.last_check,
                "previous_status": previous_status,
                "new_status": status
            })
            
            # Log status change
            logger.info(
                f"{self.integration_type}/{self.integration_name} health status "
                f"changed: {previous_status} → {status}"
            )
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive health report for the integration.
        
        Returns:
            Dict containing health status and metrics
        """
        # Update health status before reporting
        self._update_health_status()
        
        # Calculate performance metrics
        total_ops = sum(
            m.success_count + m.failure_count for m in self.health.metrics.values()
        )
        total_success = sum(m.success_count for m in self.health.metrics.values())
        avg_duration = (
            sum(m.total_duration_ms for m in self.health.metrics.values()) / total_ops
            if total_ops > 0 else 0
        )
        
        # Prepare operation-specific metrics
        operation_metrics = {}
        for op_name, metrics in self.health.metrics.items():
            operation_metrics[op_name] = {
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "success_rate": metrics.success_rate,
                "avg_duration_ms": metrics.avg_duration_ms,
                "last_execution": metrics.last_execution_time.isoformat() if metrics.last_execution_time else None,
                "last_status": "success" if metrics.last_status else "failure",
                "last_error": metrics.last_error
            }
        
        # Build health report
        return {
            "integration_type": self.integration_type,
            "integration_name": self.integration_name,
            "connection_id": self.connection_id,
            "health_status": self.health.status,
            "last_check": self.health.last_check.isoformat() if self.health.last_check else None,
            "overall_metrics": {
                "total_operations": total_ops,
                "total_successful": total_success,
                "success_rate": total_success / total_ops if total_ops > 0 else 1.0,
                "avg_duration_ms": avg_duration
            },
            "operation_metrics": operation_metrics,
            "status_history": [
                {
                    "timestamp": entry["timestamp"].isoformat(),
                    "previous_status": entry["previous_status"],
                    "new_status": entry["new_status"]
                }
                for entry in self.health.health_history[-5:]  # Last 5 status changes
            ]
        }


class OperationTimer:
    """Context manager for timing integration operations."""
    
    def __init__(self, monitor: IntegrationMonitor, operation_name: str):
        """
        Initialize the operation timer.
        
        Args:
            monitor: IntegrationMonitor instance
            operation_name: Name of the operation being timed
        """
        self.monitor = monitor
        self.operation_name = operation_name
        self.start_time = None
        self.success = True
        self.error = None
        
    def __enter__(self):
        """Start timing the operation."""
        self.start_time = time.time()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Record operation metrics when exiting context.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        # Calculate duration in milliseconds
        duration_ms = (time.time() - self.start_time) * 1000
        
        # Set success status and error message
        self.success = exc_type is None
        self.error = str(exc_val) if exc_val else None
        
        # Record the operation in the monitor
        self.monitor.record_operation(
            self.operation_name,
            self.success,
            duration_ms,
            self.error
        )
        
        # Don't suppress exceptions
        return False
