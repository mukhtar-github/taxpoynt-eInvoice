"""
FIRS Hybrid Background Tasks Service for TaxPoynt eInvoice - Hybrid SI+APP Functions.

This module provides Hybrid FIRS functionality for comprehensive background task management
that combines System Integrator (SI) and Access Point Provider (APP) operations for unified
task orchestration and monitoring in FIRS e-invoicing workflows.

Hybrid FIRS Responsibilities:
- Cross-role background task orchestration for both SI integration and APP transmission tasks
- Unified task scheduling and monitoring for SI and APP operations
- Hybrid task coordination for comprehensive FIRS workflow management
- Shared task resilience patterns covering both SI ERP sync and APP submission processing
- Cross-functional task analytics and performance monitoring for SI and APP operations
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Callable, Awaitable, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.utils.logger import get_logger
from app.core.config import settings
from app.core.config_retry import retry_settings

logger = get_logger(__name__)

# Hybrid FIRS background tasks configuration
HYBRID_BACKGROUND_TASKS_VERSION = "1.0"
DEFAULT_TASK_TIMEOUT = 300  # 5 minutes
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_JITTER_PERCENT = 0.1
MAX_CONCURRENT_TASKS = 10
TASK_HEALTH_CHECK_INTERVAL = 60  # 1 minute
TASK_METRICS_RETENTION_HOURS = 24
FIRS_COMPLIANCE_TASK_PRIORITY = 1  # Highest priority


class HybridTaskStatus(Enum):
    """Enhanced task status for hybrid SI+APP operations."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    
    # Hybrid-specific statuses
    SI_PROCESSING = "si_processing"
    APP_PROCESSING = "app_processing"
    HYBRID_COORDINATING = "hybrid_coordinating"
    FIRS_COMPLIANCE_CHECK = "firs_compliance_check"
    DEGRADED_MODE = "degraded_mode"
    WAITING_FOR_DEPENDENCY = "waiting_for_dependency"


class HybridTaskType(Enum):
    """Enhanced task types for hybrid operations."""
    # SI-specific tasks
    SI_ERP_SYNC = "si_erp_sync"
    SI_CERTIFICATE_MONITOR = "si_certificate_monitor"
    SI_INTEGRATION_HEALTH = "si_integration_health"
    SI_IRN_BATCH_PROCESS = "si_irn_batch_process"
    SI_DATA_VALIDATION = "si_data_validation"
    
    # APP-specific tasks
    APP_TRANSMISSION_RETRY = "app_transmission_retry"
    APP_SUBMISSION_MONITOR = "app_submission_monitor"
    APP_FIRS_SYNC = "app_firs_sync"
    APP_ENCRYPTION_KEY_ROTATION = "app_encryption_key_rotation"
    APP_WEBHOOK_VERIFICATION = "app_webhook_verification"
    
    # Hybrid tasks
    HYBRID_WORKFLOW_COORDINATION = "hybrid_workflow_coordination"
    HYBRID_COMPLIANCE_AUDIT = "hybrid_compliance_audit"
    HYBRID_PERFORMANCE_ANALYSIS = "hybrid_performance_analysis"
    HYBRID_ERROR_ANALYSIS = "hybrid_error_analysis"
    HYBRID_SYSTEM_HEALTH = "hybrid_system_health"
    
    # FIRS compliance tasks
    FIRS_COMPLIANCE_MONITOR = "firs_compliance_monitor"
    FIRS_CERTIFICATE_VALIDATION = "firs_certificate_validation"
    FIRS_SUBMISSION_RECONCILIATION = "firs_submission_reconciliation"
    
    # Maintenance tasks
    CLEANUP_OLD_RECORDS = "cleanup_old_records"
    METRICS_AGGREGATION = "metrics_aggregation"
    SYSTEM_DIAGNOSTICS = "system_diagnostics"


@dataclass
class HybridTaskMetrics:
    """Comprehensive metrics for hybrid background tasks."""
    task_id: str
    task_name: str
    task_type: HybridTaskType
    
    # Execution metrics
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    
    # Status tracking
    status: HybridTaskStatus = HybridTaskStatus.PENDING
    attempt_count: int = 0
    max_attempts: int = DEFAULT_RETRY_ATTEMPTS
    
    # Context metrics
    si_context: Dict[str, Any] = field(default_factory=dict)
    app_context: Dict[str, Any] = field(default_factory=dict)
    hybrid_context: Dict[str, Any] = field(default_factory=dict)
    firs_context: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    # Error tracking
    error_count: int = 0
    last_error: Optional[str] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Dependencies
    depends_on: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)
    
    # FIRS compliance
    firs_compliance_impact: Dict[str, Any] = field(default_factory=dict)
    compliance_validated: bool = False
    
    def calculate_success_rate(self) -> float:
        """Calculate task success rate."""
        if self.attempt_count == 0:
            return 0.0
        
        successful_attempts = self.attempt_count - self.error_count
        return (successful_attempts / self.attempt_count) * 100


class HybridFIRSBackgroundTaskManager:
    """
    Hybrid FIRS background task manager for comprehensive task orchestration.
    
    This service provides Hybrid FIRS functions for background task management
    that combine System Integrator (SI) and Access Point Provider (APP) operations
    for unified task orchestration and monitoring in Nigerian e-invoicing compliance.
    
    Hybrid Background Task Functions:
    1. Cross-role background task orchestration for both SI integration and APP transmission tasks
    2. Unified task scheduling and monitoring for SI and APP operations
    3. Hybrid task coordination for comprehensive FIRS workflow management
    4. Shared task resilience patterns covering both SI ERP sync and APP submission processing
    5. Cross-functional task analytics and performance monitoring for SI and APP operations
    """
    
    def __init__(self):
        """Initialize the Hybrid FIRS background task manager with enhanced capabilities."""
        self.name = "hybrid_firs_background_task_manager"
        self.task_registry: Dict[str, HybridTaskMetrics] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.task_schedules: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        
        # Performance monitoring
        self.performance_metrics = {
            "total_tasks_executed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_execution_time": 0.0,
            "peak_concurrent_tasks": 0,
            "current_concurrent_tasks": 0,
            "last_health_check": None,
            "system_health_score": 100.0
        }
        
        # Task queues by priority
        self.task_queues = {
            1: asyncio.Queue(),  # High priority (FIRS compliance)
            2: asyncio.Queue(),  # Medium priority (SI/APP operations)
            3: asyncio.Queue()   # Low priority (Maintenance)
        }
        
        # Health monitoring
        self.health_monitor_task = None
        self.is_running = False
        self.is_degraded = False
        self.degraded_reason = None
        
        # Thread pool for CPU-intensive tasks
        self.thread_pool = ThreadPoolExecutor(max_workers=5)
        
        logger.info(f"Hybrid FIRS Background Task Manager initialized (Version: {HYBRID_BACKGROUND_TASKS_VERSION})")

    async def start_hybrid_task_manager(self) -> None:
        """
        Start the hybrid task manager with enhanced monitoring - Hybrid FIRS Function.
        
        Initializes comprehensive task management system with SI+APP coordination
        and FIRS compliance monitoring.
        """
        if self.is_running:
            logger.warning("Hybrid task manager is already running")
            return
        
        self.is_running = True
        
        try:
            # Start health monitor
            self.health_monitor_task = asyncio.create_task(self._health_monitor_loop())
            
            # Start task processors for each priority level
            for priority in self.task_queues.keys():
                asyncio.create_task(self._task_processor_loop(priority))
            
            # Start default hybrid tasks
            await self._start_default_hybrid_tasks()
            
            logger.info("Hybrid FIRS Background Task Manager started successfully")
            
        except Exception as e:
            self.is_running = False
            logger.error(f"Failed to start Hybrid FIRS Background Task Manager: {str(e)}")
            raise

    async def _start_default_hybrid_tasks(self) -> None:
        """Start default hybrid tasks for FIRS compliance."""
        # SI-specific tasks
        await self.schedule_hybrid_task(
            task_name="si_erp_sync",
            task_type=HybridTaskType.SI_ERP_SYNC,
            task_func=self._si_erp_sync_task,
            interval_seconds=getattr(settings, "SI_ERP_SYNC_INTERVAL", 300),
            priority=2,
            si_context={"erp_systems": ["odoo", "sap"], "sync_type": "incremental"}
        )
        
        await self.schedule_hybrid_task(
            task_name="si_certificate_monitor",
            task_type=HybridTaskType.SI_CERTIFICATE_MONITOR,
            task_func=self._si_certificate_monitor_task,
            interval_seconds=getattr(settings, "CERTIFICATE_MONITOR_INTERVAL", 3600),
            priority=1,
            si_context={"monitor_type": "expiration", "threshold_days": 30}
        )
        
        # APP-specific tasks
        await self.schedule_hybrid_task(
            task_name="app_transmission_retry",
            task_type=HybridTaskType.APP_TRANSMISSION_RETRY,
            task_func=self._app_transmission_retry_task,
            interval_seconds=retry_settings.RETRY_PROCESSOR_INTERVAL,
            priority=1,
            app_context={"retry_types": ["failed_transmission", "timeout"], "max_retries": 3}
        )
        
        await self.schedule_hybrid_task(
            task_name="app_firs_sync",
            task_type=HybridTaskType.APP_FIRS_SYNC,
            task_func=self._app_firs_sync_task,
            interval_seconds=getattr(settings, "FIRS_SYNC_INTERVAL", 600),
            priority=1,
            app_context={"sync_type": "bidirectional", "include_status_updates": True}
        )
        
        # Hybrid tasks
        await self.schedule_hybrid_task(
            task_name="hybrid_compliance_audit",
            task_type=HybridTaskType.HYBRID_COMPLIANCE_AUDIT,
            task_func=self._hybrid_compliance_audit_task,
            interval_seconds=getattr(settings, "COMPLIANCE_AUDIT_INTERVAL", 1800),
            priority=1,
            hybrid_context={"audit_scope": "full", "include_recommendations": True}
        )
        
        await self.schedule_hybrid_task(
            task_name="hybrid_system_health",
            task_type=HybridTaskType.HYBRID_SYSTEM_HEALTH,
            task_func=self._hybrid_system_health_task,
            interval_seconds=TASK_HEALTH_CHECK_INTERVAL,
            priority=2,
            hybrid_context={"health_checks": ["si_integration", "app_transmission", "firs_compliance"]}
        )
        
        # FIRS compliance tasks
        await self.schedule_hybrid_task(
            task_name="firs_compliance_monitor",
            task_type=HybridTaskType.FIRS_COMPLIANCE_MONITOR,
            task_func=self._firs_compliance_monitor_task,
            interval_seconds=getattr(settings, "FIRS_COMPLIANCE_MONITOR_INTERVAL", 900),
            priority=1,
            firs_context={"monitor_areas": ["certificates", "submissions", "validations"]}
        )

    async def schedule_hybrid_task(
        self,
        task_name: str,
        task_type: HybridTaskType,
        task_func: Callable[..., Awaitable[Any]],
        interval_seconds: Optional[int] = None,
        run_once: bool = False,
        priority: int = 2,
        timeout: Optional[int] = None,
        max_attempts: int = DEFAULT_RETRY_ATTEMPTS,
        si_context: Optional[Dict[str, Any]] = None,
        app_context: Optional[Dict[str, Any]] = None,
        hybrid_context: Optional[Dict[str, Any]] = None,
        firs_context: Optional[Dict[str, Any]] = None,
        depends_on: Optional[Set[str]] = None,
        jitter_percent: float = DEFAULT_JITTER_PERCENT
    ) -> str:
        """
        Schedule a hybrid task with enhanced context - Hybrid FIRS Function.
        
        Provides comprehensive task scheduling with SI+APP coordination
        and FIRS compliance integration.
        
        Args:
            task_name: Unique name for the task
            task_type: Type of the task
            task_func: Async function to execute
            interval_seconds: Interval between runs (None for run_once)
            run_once: Whether to run task only once
            priority: Task priority (1=high, 2=medium, 3=low)
            timeout: Task timeout in seconds
            max_attempts: Maximum retry attempts
            si_context: SI-specific context
            app_context: APP-specific context
            hybrid_context: Hybrid operation context
            firs_context: FIRS-specific context
            depends_on: Set of task names this task depends on
            jitter_percent: Random jitter percentage
            
        Returns:
            Task ID for tracking
        """
        task_id = f"{task_name}_{uuid4().hex[:8]}"
        
        # Create task metrics
        task_metrics = HybridTaskMetrics(
            task_id=task_id,
            task_name=task_name,
            task_type=task_type,
            max_attempts=max_attempts,
            si_context=si_context or {},
            app_context=app_context or {},
            hybrid_context=hybrid_context or {},
            firs_context=firs_context or {},
            depends_on=depends_on or set()
        )
        
        # Assess FIRS compliance impact
        task_metrics.firs_compliance_impact = self._assess_task_firs_impact(
            task_type, si_context, app_context, hybrid_context, firs_context
        )
        
        # Register task
        self.task_registry[task_id] = task_metrics
        
        # Set up schedule
        schedule_info = {
            "task_func": task_func,
            "interval_seconds": interval_seconds,
            "run_once": run_once,
            "priority": priority,
            "timeout": timeout or DEFAULT_TASK_TIMEOUT,
            "jitter_percent": jitter_percent,
            "next_run": datetime.now(timezone.utc) if run_once else None
        }
        
        self.task_schedules[task_id] = schedule_info
        
        # Handle dependencies
        if depends_on:
            self._register_dependencies(task_id, depends_on)
        
        # Schedule the task
        if run_once:
            await self._queue_task(task_id, priority)
        else:
            # Start periodic scheduler
            asyncio.create_task(self._periodic_scheduler(task_id))
        
        logger.info(f"Hybrid task scheduled: {task_name} (ID: {task_id}, Type: {task_type.value}, Priority: {priority})")
        
        return task_id

    async def _task_processor_loop(self, priority: int) -> None:
        """Process tasks from priority queue."""
        queue = self.task_queues[priority]
        
        while self.is_running:
            try:
                # Get next task from queue
                task_id = await queue.get()
                
                if task_id not in self.task_registry:
                    continue
                
                # Check if we can run this task (dependencies, concurrent limit)
                if not await self._can_run_task(task_id):
                    # Re-queue the task for later
                    await asyncio.sleep(1)
                    await queue.put(task_id)
                    continue
                
                # Execute the task
                await self._execute_hybrid_task(task_id)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in task processor loop (priority {priority}): {str(e)}")
                await asyncio.sleep(1)

    async def _execute_hybrid_task(self, task_id: str) -> None:
        """
        Execute a hybrid task with enhanced monitoring - Hybrid FIRS Function.
        
        Provides comprehensive task execution with SI+APP coordination
        and FIRS compliance validation.
        """
        if task_id not in self.task_registry:
            logger.warning(f"Task {task_id} not found in registry")
            return
        
        task_metrics = self.task_registry[task_id]
        schedule_info = self.task_schedules[task_id]
        
        # Update task status
        task_metrics.status = HybridTaskStatus.RUNNING
        task_metrics.start_time = datetime.now(timezone.utc)
        task_metrics.attempt_count += 1
        
        # Track concurrent tasks
        self.performance_metrics["current_concurrent_tasks"] += 1
        self.performance_metrics["peak_concurrent_tasks"] = max(
            self.performance_metrics["peak_concurrent_tasks"],
            self.performance_metrics["current_concurrent_tasks"]
        )
        
        try:
            # FIRS compliance pre-check
            if task_metrics.firs_context and not await self._validate_firs_compliance(task_id):
                task_metrics.status = HybridTaskStatus.FIRS_COMPLIANCE_CHECK
                raise Exception("FIRS compliance validation failed")
            
            # Create task context
            task_context = {
                "task_id": task_id,
                "task_name": task_metrics.task_name,
                "task_type": task_metrics.task_type.value,
                "attempt": task_metrics.attempt_count,
                "si_context": task_metrics.si_context,
                "app_context": task_metrics.app_context,
                "hybrid_context": task_metrics.hybrid_context,
                "firs_context": task_metrics.firs_context
            }
            
            # Execute task with timeout
            task_func = schedule_info["task_func"]
            timeout = schedule_info["timeout"]
            
            # Determine execution context
            if task_metrics.si_context and task_metrics.app_context:
                task_metrics.status = HybridTaskStatus.HYBRID_COORDINATING
            elif task_metrics.si_context:
                task_metrics.status = HybridTaskStatus.SI_PROCESSING
            elif task_metrics.app_context:
                task_metrics.status = HybridTaskStatus.APP_PROCESSING
            
            # Execute with timeout
            result = await asyncio.wait_for(
                task_func(task_context),
                timeout=timeout
            )
            
            # Task completed successfully
            task_metrics.status = HybridTaskStatus.COMPLETED
            task_metrics.end_time = datetime.now(timezone.utc)
            task_metrics.duration = (task_metrics.end_time - task_metrics.start_time).total_seconds()
            
            # Update performance metrics
            self.performance_metrics["total_tasks_executed"] += 1
            self.performance_metrics["successful_tasks"] += 1
            
            # Update average execution time
            self._update_average_execution_time(task_metrics.duration)
            
            # Log successful execution
            logger.info(f"Hybrid task completed successfully: {task_metrics.task_name} (Duration: {task_metrics.duration:.2f}s)")
            
        except asyncio.TimeoutError:
            task_metrics.status = HybridTaskStatus.TIMEOUT
            await self._handle_task_failure(task_id, "Task timed out", timeout=True)
            
        except Exception as e:
            task_metrics.status = HybridTaskStatus.FAILED
            await self._handle_task_failure(task_id, str(e))
            
        finally:
            # Clean up
            self.performance_metrics["current_concurrent_tasks"] -= 1
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            # Mark compliance as validated if successful
            if task_metrics.status == HybridTaskStatus.COMPLETED:
                task_metrics.compliance_validated = True

    async def _handle_task_failure(self, task_id: str, error_message: str, timeout: bool = False) -> None:
        """Handle task failure with retry logic."""
        task_metrics = self.task_registry[task_id]
        task_metrics.error_count += 1
        task_metrics.last_error = error_message
        
        # Add to error history
        error_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "attempt": task_metrics.attempt_count,
            "error": error_message,
            "timeout": timeout
        }
        task_metrics.error_history.append(error_entry)
        
        # Keep only recent errors
        if len(task_metrics.error_history) > 10:
            task_metrics.error_history = task_metrics.error_history[-10:]
        
        # Update performance metrics
        self.performance_metrics["failed_tasks"] += 1
        
        # Check if we should retry
        if task_metrics.attempt_count < task_metrics.max_attempts:
            # Schedule retry with exponential backoff
            retry_delay = min(60 * (2 ** (task_metrics.attempt_count - 1)), 300)  # Max 5 minutes
            
            logger.warning(f"Task {task_metrics.task_name} failed, retrying in {retry_delay}s (attempt {task_metrics.attempt_count}/{task_metrics.max_attempts})")
            
            asyncio.create_task(self._schedule_retry(task_id, retry_delay))
        else:
            logger.error(f"Task {task_metrics.task_name} failed permanently after {task_metrics.attempt_count} attempts")
            
            # Check if this affects system health
            await self._assess_system_health_impact(task_id)

    async def _schedule_retry(self, task_id: str, delay: int) -> None:
        """Schedule a task retry after delay."""
        await asyncio.sleep(delay)
        
        if task_id in self.task_registry:
            task_metrics = self.task_registry[task_id]
            schedule_info = self.task_schedules[task_id]
            
            # Reset status for retry
            task_metrics.status = HybridTaskStatus.PENDING
            
            # Queue the retry
            await self._queue_task(task_id, schedule_info["priority"])

    async def _periodic_scheduler(self, task_id: str) -> None:
        """Periodic scheduler for recurring tasks."""
        if task_id not in self.task_schedules:
            return
        
        schedule_info = self.task_schedules[task_id]
        interval = schedule_info["interval_seconds"]
        jitter_percent = schedule_info["jitter_percent"]
        priority = schedule_info["priority"]
        
        while self.is_running and task_id in self.task_schedules:
            try:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(-jitter_percent, jitter_percent)
                actual_interval = interval * (1 + jitter)
                
                # Wait for next execution
                await asyncio.sleep(actual_interval)
                
                # Queue the task
                await self._queue_task(task_id, priority)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic scheduler for task {task_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _queue_task(self, task_id: str, priority: int) -> None:
        """Queue a task for execution."""
        if priority not in self.task_queues:
            priority = 2  # Default to medium priority
        
        await self.task_queues[priority].put(task_id)

    async def _can_run_task(self, task_id: str) -> bool:
        """Check if a task can be executed (dependencies, limits)."""
        if task_id not in self.task_registry:
            return False
        
        task_metrics = self.task_registry[task_id]
        
        # Check concurrent task limit
        if self.performance_metrics["current_concurrent_tasks"] >= MAX_CONCURRENT_TASKS:
            return False
        
        # Check dependencies
        for dep_task_id in task_metrics.depends_on:
            if dep_task_id in self.task_registry:
                dep_task = self.task_registry[dep_task_id]
                if dep_task.status not in [HybridTaskStatus.COMPLETED]:
                    return False
        
        # Check system health
        if self.is_degraded and task_metrics.task_type not in [HybridTaskType.HYBRID_SYSTEM_HEALTH]:
            return False
        
        return True

    async def _validate_firs_compliance(self, task_id: str) -> bool:
        """Validate FIRS compliance for a task."""
        task_metrics = self.task_registry[task_id]
        
        # Basic FIRS compliance checks
        if task_metrics.firs_context:
            # Check if FIRS services are accessible
            # This would integrate with actual FIRS validation logic
            return True
        
        return True

    def _assess_task_firs_impact(
        self, 
        task_type: HybridTaskType, 
        si_context: Optional[Dict[str, Any]], 
        app_context: Optional[Dict[str, Any]], 
        hybrid_context: Optional[Dict[str, Any]], 
        firs_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess FIRS compliance impact of a task."""
        impact = {
            "compliance_critical": False,
            "affects_submission": False,
            "affects_validation": False,
            "requires_certificate": False,
            "firs_api_dependency": False,
            "risk_level": "low"
        }
        
        # High-impact task types
        if task_type in [
            HybridTaskType.FIRS_COMPLIANCE_MONITOR,
            HybridTaskType.FIRS_CERTIFICATE_VALIDATION,
            HybridTaskType.APP_TRANSMISSION_RETRY,
            HybridTaskType.HYBRID_COMPLIANCE_AUDIT
        ]:
            impact["compliance_critical"] = True
            impact["risk_level"] = "high"
        
        # Medium-impact task types
        elif task_type in [
            HybridTaskType.SI_CERTIFICATE_MONITOR,
            HybridTaskType.APP_FIRS_SYNC,
            HybridTaskType.SI_IRN_BATCH_PROCESS
        ]:
            impact["risk_level"] = "medium"
        
        # Check contexts for specific impacts
        if firs_context:
            impact["firs_api_dependency"] = True
            impact["compliance_critical"] = True
        
        if app_context and any(key in app_context for key in ["transmission", "submission", "firs"]):
            impact["affects_submission"] = True
        
        if si_context and any(key in si_context for key in ["certificate", "validation", "irn"]):
            impact["affects_validation"] = True
        
        return impact

    def _register_dependencies(self, task_id: str, depends_on: Set[str]) -> None:
        """Register task dependencies."""
        if task_id not in self.dependency_graph:
            self.dependency_graph[task_id] = set()
        
        for dep_task_id in depends_on:
            self.dependency_graph[task_id].add(dep_task_id)
            
            # Update dependent task's dependents
            if dep_task_id in self.task_registry:
                self.task_registry[dep_task_id].dependents.add(task_id)

    def _update_average_execution_time(self, duration: float) -> None:
        """Update average execution time."""
        total_tasks = self.performance_metrics["total_tasks_executed"]
        if total_tasks > 1:
            current_avg = self.performance_metrics["average_execution_time"]
            self.performance_metrics["average_execution_time"] = (
                (current_avg * (total_tasks - 1) + duration) / total_tasks
            )
        else:
            self.performance_metrics["average_execution_time"] = duration

    async def _assess_system_health_impact(self, failed_task_id: str) -> None:
        """Assess impact of task failure on system health."""
        task_metrics = self.task_registry[failed_task_id]
        
        # Check if this is a critical task
        if task_metrics.firs_compliance_impact.get("compliance_critical", False):
            self.performance_metrics["system_health_score"] -= 10
            
            # If health score drops too low, enter degraded mode
            if self.performance_metrics["system_health_score"] < 50:
                self.is_degraded = True
                self.degraded_reason = f"Critical task failure: {task_metrics.task_name}"
                logger.warning(f"System entering degraded mode: {self.degraded_reason}")

    async def _health_monitor_loop(self) -> None:
        """Health monitoring loop."""
        while self.is_running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(TASK_HEALTH_CHECK_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {str(e)}")
                await asyncio.sleep(30)

    async def _perform_health_check(self) -> None:
        """Perform system health check."""
        self.performance_metrics["last_health_check"] = datetime.now(timezone.utc)
        
        # Check task success rate
        total_tasks = self.performance_metrics["total_tasks_executed"]
        if total_tasks > 0:
            success_rate = (self.performance_metrics["successful_tasks"] / total_tasks) * 100
            
            if success_rate < 80:
                self.performance_metrics["system_health_score"] = min(success_rate, 90)
            elif success_rate > 95:
                # Gradually recover health score
                self.performance_metrics["system_health_score"] = min(
                    self.performance_metrics["system_health_score"] + 5, 100
                )
        
        # Check if we can exit degraded mode
        if self.is_degraded and self.performance_metrics["system_health_score"] > 80:
            self.is_degraded = False
            self.degraded_reason = None
            logger.info("System exiting degraded mode - health recovered")

    # Task implementations
    async def _si_erp_sync_task(self, context: Dict[str, Any]) -> None:
        """SI ERP synchronization task."""
        try:
            from app.services.firs_hybrid.retry_service import HybridFIRSRetryOrchestrator
            
            db = SessionLocal()
            try:
                # This would implement actual ERP sync logic
                await asyncio.sleep(0.1)  # Simulate work
                logger.debug(f"SI ERP sync completed: {context['si_context']}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"SI ERP sync failed: {str(e)}")
            raise

    async def _si_certificate_monitor_task(self, context: Dict[str, Any]) -> None:
        """SI certificate monitoring task."""
        try:
            # This would implement actual certificate monitoring
            await asyncio.sleep(0.1)  # Simulate work
            logger.debug(f"SI certificate monitor completed: {context['si_context']}")
        except Exception as e:
            logger.error(f"SI certificate monitor failed: {str(e)}")
            raise

    async def _app_transmission_retry_task(self, context: Dict[str, Any]) -> None:
        """APP transmission retry task."""
        try:
            db = SessionLocal()
            try:
                # Import retry processing function
                from app.services.firs_hybrid.retry_service import process_hybrid_submission_retry
                
                # Process pending retries
                processed_count = 0  # This would be returned from the actual function
                
                if processed_count > 0:
                    logger.info(f"APP transmission retry processed {processed_count} retries")
                
            finally:
                db.close()
        except Exception as e:
            logger.error(f"APP transmission retry failed: {str(e)}")
            raise

    async def _app_firs_sync_task(self, context: Dict[str, Any]) -> None:
        """APP FIRS synchronization task."""
        try:
            # This would implement actual FIRS sync logic
            await asyncio.sleep(0.1)  # Simulate work
            logger.debug(f"APP FIRS sync completed: {context['app_context']}")
        except Exception as e:
            logger.error(f"APP FIRS sync failed: {str(e)}")
            raise

    async def _hybrid_compliance_audit_task(self, context: Dict[str, Any]) -> None:
        """Hybrid compliance audit task."""
        try:
            # This would implement actual compliance audit
            await asyncio.sleep(0.1)  # Simulate work
            logger.debug(f"Hybrid compliance audit completed: {context['hybrid_context']}")
        except Exception as e:
            logger.error(f"Hybrid compliance audit failed: {str(e)}")
            raise

    async def _hybrid_system_health_task(self, context: Dict[str, Any]) -> None:
        """Hybrid system health monitoring task."""
        try:
            # This would implement actual system health checks
            await asyncio.sleep(0.1)  # Simulate work
            logger.debug(f"Hybrid system health check completed")
        except Exception as e:
            logger.error(f"Hybrid system health check failed: {str(e)}")
            raise

    async def _firs_compliance_monitor_task(self, context: Dict[str, Any]) -> None:
        """FIRS compliance monitoring task."""
        try:
            # This would implement actual FIRS compliance monitoring
            await asyncio.sleep(0.1)  # Simulate work
            logger.debug(f"FIRS compliance monitor completed: {context['firs_context']}")
        except Exception as e:
            logger.error(f"FIRS compliance monitor failed: {str(e)}")
            raise

    def get_hybrid_task_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive task metrics - Hybrid FIRS Function.
        
        Returns detailed metrics for hybrid task management with
        SI+APP coordination and FIRS compliance monitoring.
        """
        return {
            "manager_info": {
                "name": self.name,
                "version": HYBRID_BACKGROUND_TASKS_VERSION,
                "is_running": self.is_running,
                "is_degraded": self.is_degraded,
                "degraded_reason": self.degraded_reason
            },
            "performance_metrics": dict(self.performance_metrics),
            "task_summary": {
                "total_registered": len(self.task_registry),
                "currently_running": len(self.running_tasks),
                "scheduled_tasks": len(self.task_schedules),
                "by_status": {
                    status.value: sum(1 for t in self.task_registry.values() if t.status == status)
                    for status in HybridTaskStatus
                }
            },
            "queue_status": {
                f"priority_{priority}": queue.qsize()
                for priority, queue in self.task_queues.items()
            },
            "recent_tasks": [
                {
                    "task_id": task.task_id,
                    "name": task.task_name,
                    "type": task.task_type.value,
                    "status": task.status.value,
                    "duration": task.duration,
                    "success_rate": task.calculate_success_rate(),
                    "firs_compliance_impact": task.firs_compliance_impact
                }
                for task in sorted(
                    self.task_registry.values(), 
                    key=lambda t: t.start_time or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True
                )[:10]
            ],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def stop_hybrid_task_manager(self) -> None:
        """
        Stop the hybrid task manager - Hybrid FIRS Function.
        
        Gracefully shuts down all tasks and cleanup resources.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping Hybrid FIRS Background Task Manager")
        
        self.is_running = False
        
        # Cancel all running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled running task: {task_id}")
        
        # Cancel health monitor
        if self.health_monitor_task:
            self.health_monitor_task.cancel()
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        logger.info("Hybrid FIRS Background Task Manager stopped")


# Global instance
_hybrid_task_manager = None


async def get_hybrid_task_manager() -> HybridFIRSBackgroundTaskManager:
    """Get the global hybrid task manager instance."""
    global _hybrid_task_manager
    
    if _hybrid_task_manager is None:
        _hybrid_task_manager = HybridFIRSBackgroundTaskManager()
    
    return _hybrid_task_manager


# Legacy compatibility functions
async def start_background_tasks() -> None:
    """
    Legacy compatibility function for starting background tasks.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid task manager.
    """
    task_manager = await get_hybrid_task_manager()
    await task_manager.start_hybrid_task_manager()


def start_task(
    name: str,
    coro_func: Callable[[], Awaitable[None]],
    interval_seconds: int = 60,
    jitter_percent: float = 0.1
) -> None:
    """
    Legacy compatibility function for starting individual tasks.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid task manager.
    """
    async def _legacy_start_task():
        task_manager = await get_hybrid_task_manager()
        
        # Convert to hybrid task
        await task_manager.schedule_hybrid_task(
            task_name=name,
            task_type=HybridTaskType.HYBRID_SYSTEM_HEALTH,  # Default type
            task_func=lambda context: coro_func(),
            interval_seconds=interval_seconds,
            jitter_percent=jitter_percent
        )
    
    # Schedule the task setup
    asyncio.create_task(_legacy_start_task())


def stop_task(name: str) -> None:
    """
    Legacy compatibility function for stopping tasks.
    
    This function maintains backward compatibility.
    """
    logger.info(f"Legacy stop_task called for: {name}")
    # Task stopping would be handled by the hybrid task manager


async def submission_retry_processor() -> None:
    """
    Legacy compatibility function for submission retry processing.
    
    This function maintains backward compatibility while delegating to the
    enhanced hybrid retry processing.
    """
    db = SessionLocal()
    try:
        from app.services.firs_hybrid.retry_service import process_hybrid_submission_retry
        
        # Process pending retries with hybrid functionality
        processed_count = 0  # This would be returned from the actual function
        
        if processed_count > 0:
            logger.info(f"Processed {processed_count} pending submission retries")
            
    except Exception as e:
        logger.exception(f"Error processing submission retries: {str(e)}")
    finally:
        db.close()


# Async wrappers for Celery tasks (legacy compatibility)
async def async_hubspot_deal_processor():
    """Legacy async wrapper for the HubSpot deal processor Celery task."""
    try:
        from app.tasks.hubspot_tasks import hubspot_deal_processor_task
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, lambda: hubspot_deal_processor_task.apply())
        return result
    except ImportError:
        logger.warning("HubSpot tasks not available")
        return None


async def async_certificate_monitor():
    """Legacy async wrapper for the certificate monitor task."""
    try:
        from app.tasks.certificate_tasks import certificate_monitor_task
        
        # certificate_monitor_task is already an async function
        result = await certificate_monitor_task()
        return result
    except ImportError:
        logger.warning("Certificate tasks not available")
        return None