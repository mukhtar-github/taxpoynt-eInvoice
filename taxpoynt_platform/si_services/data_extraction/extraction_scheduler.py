"""
Extraction Scheduler Service

This module handles scheduling and automation of data extraction jobs
with support for cron-like scheduling, job queuing, and dependency management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import croniter
from pathlib import Path

from .erp_data_extractor import ERPType, ERPDataExtractor, ExtractionFilter
from .batch_processor import BatchProcessor, BatchJob, BatchConfig, ProcessingPriority
from .incremental_sync import IncrementalSyncService, SyncConfig

logger = logging.getLogger(__name__)


class ScheduleType(Enum):
    """Types of schedule patterns"""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    DEPENDENCY = "dependency"


class JobType(Enum):
    """Types of scheduled jobs"""
    FULL_EXTRACTION = "full_extraction"
    INCREMENTAL_SYNC = "incremental_sync"
    BATCH_PROCESSING = "batch_processing"
    DATA_RECONCILIATION = "data_reconciliation"
    CLEANUP = "cleanup"
    HEALTH_CHECK = "health_check"


class JobStatus(Enum):
    """Status of scheduled jobs"""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    COMPLETED = "completed"
    FAILED = "failed"


class ExecutionStatus(Enum):
    """Status of job executions"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class ScheduleConfig:
    """Configuration for job scheduling"""
    schedule_type: ScheduleType
    cron_expression: Optional[str] = None
    interval_seconds: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    max_executions: Optional[int] = None
    timezone: str = "UTC"
    allow_overlap: bool = False
    max_runtime_seconds: int = 3600
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay_seconds: int = 60


@dataclass
class JobDependency:
    """Represents a job dependency"""
    dependent_job_id: str
    dependency_type: str = "completion"  # completion, success, failure
    wait_for_completion: bool = True
    timeout_seconds: int = 3600


@dataclass
class ScheduledJob:
    """Represents a scheduled job"""
    job_id: str
    job_name: str
    job_type: JobType
    erp_type: ERPType
    schedule_config: ScheduleConfig
    extraction_config: Optional[Dict[str, Any]] = None
    status: JobStatus = JobStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    last_execution: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    dependencies: List[JobDependency] = field(default_factory=list)
    notification_config: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobExecution:
    """Represents a job execution instance"""
    execution_id: str
    job_id: str
    status: ExecutionStatus
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None
    retry_count: int = 0
    logs: List[str] = field(default_factory=list)


@dataclass
class SchedulerConfig:
    """Configuration for the extraction scheduler"""
    max_concurrent_jobs: int = 5
    job_timeout_seconds: int = 3600
    cleanup_interval_hours: int = 24
    execution_history_days: int = 30
    enable_job_persistence: bool = True
    persistence_path: Optional[str] = None
    health_check_interval_seconds: int = 300
    enable_notifications: bool = False
    notification_handlers: List[Callable] = field(default_factory=list)


class ExtractionScheduler:
    """
    Advanced scheduler for automating data extraction operations
    with support for cron scheduling, job dependencies, and monitoring.
    """
    
    def __init__(
        self,
        config: SchedulerConfig,
        data_extractor: ERPDataExtractor,
        batch_processor: Optional[BatchProcessor] = None,
        sync_service: Optional[IncrementalSyncService] = None
    ):
        self.config = config
        self.data_extractor = data_extractor
        self.batch_processor = batch_processor
        self.sync_service = sync_service
        
        self.scheduled_jobs: Dict[str, ScheduledJob] = {}
        self.job_executions: Dict[str, JobExecution] = {}
        self.active_executions: Dict[str, asyncio.Task] = {}
        
        self.is_running = False
        self.scheduler_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Setup persistence
        if config.persistence_path:
            self.persistence_path = Path(config.persistence_path)
            self.persistence_path.mkdir(parents=True, exist_ok=True)
        else:
            self.persistence_path = None
        
        # Load existing jobs
        asyncio.create_task(self._load_scheduled_jobs())
    
    async def start_scheduler(self) -> None:
        """Start the extraction scheduler"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting extraction scheduler")
        
        # Start scheduler loop
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        # Start cleanup task
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        # Start health check if batch processor is available
        if self.batch_processor:
            asyncio.create_task(self._health_check_loop())
    
    async def stop_scheduler(self) -> None:
        """Stop the extraction scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping extraction scheduler")
        
        # Cancel active executions
        for task in self.active_executions.values():
            task.cancel()
        
        # Cancel scheduler tasks
        if self.scheduler_task:
            self.scheduler_task.cancel()
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(
            *[t for t in [self.scheduler_task, self.cleanup_task] if t],
            return_exceptions=True
        )
        
        # Save jobs before stopping
        await self._save_scheduled_jobs()
    
    async def schedule_job(self, job: ScheduledJob) -> str:
        """Schedule a new job"""
        # Validate job configuration
        if not await self._validate_job(job):
            raise ValueError(f"Invalid job configuration: {job.job_id}")
        
        # Calculate next execution time
        job.next_execution = self._calculate_next_execution(job)
        
        # Add to scheduled jobs
        self.scheduled_jobs[job.job_id] = job
        
        # Save to persistence
        if self.config.enable_job_persistence:
            await self._save_job(job)
        
        logger.info(f"Scheduled job {job.job_id} ({job.job_name}) next execution: {job.next_execution}")
        return job.job_id
    
    async def unschedule_job(self, job_id: str) -> bool:
        """Remove a scheduled job"""
        if job_id not in self.scheduled_jobs:
            return False
        
        # Cancel active execution if running
        if job_id in self.active_executions:
            self.active_executions[job_id].cancel()
            del self.active_executions[job_id]
        
        # Remove from scheduled jobs
        del self.scheduled_jobs[job_id]
        
        # Remove from persistence
        if self.persistence_path:
            job_file = self.persistence_path / f"{job_id}.json"
            if job_file.exists():
                job_file.unlink()
        
        logger.info(f"Unscheduled job {job_id}")
        return True
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a scheduled job"""
        job = self.scheduled_jobs.get(job_id)
        if not job:
            return False
        
        job.status = JobStatus.PAUSED
        await self._save_job(job)
        
        logger.info(f"Paused job {job_id}")
        return True
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job"""
        job = self.scheduled_jobs.get(job_id)
        if not job or job.status != JobStatus.PAUSED:
            return False
        
        job.status = JobStatus.ACTIVE
        job.next_execution = self._calculate_next_execution(job)
        await self._save_job(job)
        
        logger.info(f"Resumed job {job_id}")
        return True
    
    async def trigger_job_now(self, job_id: str) -> Optional[str]:
        """Trigger a job to run immediately"""
        job = self.scheduled_jobs.get(job_id)
        if not job:
            return None
        
        execution_id = f"{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_manual"
        execution = JobExecution(
            execution_id=execution_id,
            job_id=job_id,
            status=ExecutionStatus.PENDING,
            scheduled_time=datetime.now()
        )
        
        self.job_executions[execution_id] = execution
        
        # Execute immediately
        task = asyncio.create_task(self._execute_job(job, execution))
        self.active_executions[execution_id] = task
        
        logger.info(f"Manually triggered job {job_id}")
        return execution_id
    
    async def _scheduler_loop(self) -> None:
        """Main scheduler loop"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # Check each scheduled job
                for job in list(self.scheduled_jobs.values()):
                    if (job.status == JobStatus.ACTIVE and
                        job.next_execution and
                        job.next_execution <= current_time):
                        
                        # Check if dependencies are satisfied
                        if await self._check_dependencies(job):
                            await self._schedule_execution(job)
                        else:
                            # Delay execution due to unmet dependencies
                            job.next_execution = current_time + timedelta(minutes=5)
                
                # Clean up completed tasks
                await self._cleanup_completed_executions()
                
                # Sleep before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _schedule_execution(self, job: ScheduledJob) -> None:
        """Schedule a job execution"""
        # Check concurrent execution limit
        if len(self.active_executions) >= self.config.max_concurrent_jobs:
            logger.warning(f"Concurrent job limit reached, delaying job {job.job_id}")
            job.next_execution = datetime.now() + timedelta(minutes=5)
            return
        
        # Check for overlapping execution
        if not job.schedule_config.allow_overlap:
            if any(exec_id.startswith(job.job_id) for exec_id in self.active_executions):
                logger.info(f"Job {job.job_id} already running, skipping execution")
                job.next_execution = self._calculate_next_execution(job)
                return
        
        # Create execution
        execution_id = f"{job.job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        execution = JobExecution(
            execution_id=execution_id,
            job_id=job.job_id,
            status=ExecutionStatus.PENDING,
            scheduled_time=job.next_execution
        )
        
        self.job_executions[execution_id] = execution
        
        # Start execution task
        task = asyncio.create_task(self._execute_job(job, execution))
        self.active_executions[execution_id] = task
        
        # Update job
        job.execution_count += 1
        job.last_execution = datetime.now()
        job.next_execution = self._calculate_next_execution(job)
        
        await self._save_job(job)
    
    async def _execute_job(self, job: ScheduledJob, execution: JobExecution) -> None:
        """Execute a scheduled job"""
        try:
            execution.status = ExecutionStatus.RUNNING
            execution.start_time = datetime.now()
            
            logger.info(f"Executing job {job.job_id} ({execution.execution_id})")
            
            # Execute based on job type
            if job.job_type == JobType.FULL_EXTRACTION:
                result = await self._execute_full_extraction(job, execution)
            elif job.job_type == JobType.INCREMENTAL_SYNC:
                result = await self._execute_incremental_sync(job, execution)
            elif job.job_type == JobType.BATCH_PROCESSING:
                result = await self._execute_batch_processing(job, execution)
            elif job.job_type == JobType.DATA_RECONCILIATION:
                result = await self._execute_data_reconciliation(job, execution)
            elif job.job_type == JobType.CLEANUP:
                result = await self._execute_cleanup(job, execution)
            elif job.job_type == JobType.HEALTH_CHECK:
                result = await self._execute_health_check(job, execution)
            else:
                raise ValueError(f"Unsupported job type: {job.job_type}")
            
            execution.result_data = result
            execution.status = ExecutionStatus.COMPLETED
            job.success_count += 1
            
            logger.info(f"Job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.job_id} failed: {e}")
            execution.status = ExecutionStatus.FAILED
            execution.error_details = str(e)
            job.failure_count += 1
            
            # Handle retries
            if (job.schedule_config.retry_on_failure and
                execution.retry_count < job.schedule_config.max_retries):
                
                execution.retry_count += 1
                retry_delay = job.schedule_config.retry_delay_seconds
                
                logger.info(f"Retrying job {job.job_id} in {retry_delay} seconds (attempt {execution.retry_count})")
                
                await asyncio.sleep(retry_delay)
                await self._execute_job(job, execution)
                return
        
        finally:
            execution.end_time = datetime.now()
            if execution.start_time:
                execution.duration_seconds = (execution.end_time - execution.start_time).total_seconds()
            
            # Remove from active executions
            if execution.execution_id in self.active_executions:
                del self.active_executions[execution.execution_id]
            
            # Send notifications if enabled
            if self.config.enable_notifications:
                await self._send_notifications(job, execution)
    
    async def _execute_full_extraction(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute a full data extraction"""
        config = job.extraction_config or {}
        
        from .erp_data_extractor import ExtractionFilter
        
        extraction_filter = ExtractionFilter(
            batch_size=config.get("batch_size", 1000),
            include_draft=config.get("include_draft", False),
            include_cancelled=config.get("include_cancelled", False)
        )
        
        result = await self.data_extractor.extract_data(job.erp_type, extraction_filter)
        
        return {
            "extraction_id": result.extraction_id,
            "status": result.status.value,
            "total_records": result.total_records,
            "extracted_records": result.extracted_records,
            "failed_records": result.failed_records
        }
    
    async def _execute_incremental_sync(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute an incremental sync"""
        if not self.sync_service:
            raise ValueError("Sync service not available")
        
        config = job.extraction_config or {}
        force_full_sync = config.get("force_full_sync", False)
        
        sync_id = await self.sync_service.start_incremental_sync(job.erp_type, force_full_sync)
        
        # Wait for sync completion (simplified)
        await asyncio.sleep(1)  # In practice, would poll for completion
        
        return {
            "sync_id": sync_id,
            "erp_type": job.erp_type.value,
            "force_full_sync": force_full_sync
        }
    
    async def _execute_batch_processing(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute batch processing"""
        if not self.batch_processor:
            raise ValueError("Batch processor not available")
        
        config = job.extraction_config or {}
        
        # Create batch job configuration
        from .batch_processor import BatchJob
        from .erp_data_extractor import ExtractionFilter
        
        batch_filter = ExtractionFilter(
            batch_size=config.get("batch_size", 1000),
            start_date=datetime.now() - timedelta(days=config.get("days_back", 1)),
            end_date=datetime.now()
        )
        
        batch_job = BatchJob(
            job_id=f"scheduled_{execution.execution_id}",
            erp_type=job.erp_type,
            filters=batch_filter,
            priority=ProcessingPriority.NORMAL
        )
        
        job_id = await self.batch_processor.submit_job(batch_job)
        
        return {
            "batch_job_id": job_id,
            "erp_type": job.erp_type.value
        }
    
    async def _execute_data_reconciliation(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute data reconciliation"""
        # Implementation would use data reconciler service
        # For now, return placeholder result
        return {
            "reconciliation_type": "scheduled",
            "erp_type": job.erp_type.value,
            "status": "completed"
        }
    
    async def _execute_cleanup(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute cleanup operations"""
        config = job.extraction_config or {}
        max_age_hours = config.get("max_age_hours", 24)
        
        cleaned_count = 0
        
        # Cleanup old executions
        cleaned_count += await self._cleanup_old_executions(max_age_hours)
        
        # Cleanup batch processor if available
        if self.batch_processor:
            cleaned_count += await self.batch_processor.cleanup_completed_jobs(max_age_hours)
        
        # Cleanup sync service if available
        if self.sync_service:
            cleaned_count += await self.sync_service.cleanup_old_syncs(max_age_hours)
        
        return {
            "cleanup_type": "scheduled",
            "items_cleaned": cleaned_count,
            "max_age_hours": max_age_hours
        }
    
    async def _execute_health_check(self, job: ScheduledJob, execution: JobExecution) -> Dict[str, Any]:
        """Execute health check"""
        health_status = {
            "scheduler_running": self.is_running,
            "active_executions": len(self.active_executions),
            "scheduled_jobs": len(self.scheduled_jobs),
            "data_extractor_adapters": len(self.data_extractor.adapters)
        }
        
        # Check ERP connections
        for erp_type, adapter in self.data_extractor.adapters.items():
            try:
                connection_ok = await adapter.test_connection()
                health_status[f"{erp_type.value}_connection"] = connection_ok
            except Exception as e:
                health_status[f"{erp_type.value}_connection"] = False
                health_status[f"{erp_type.value}_error"] = str(e)
        
        return health_status
    
    def _calculate_next_execution(self, job: ScheduledJob) -> Optional[datetime]:
        """Calculate the next execution time for a job"""
        config = job.schedule_config
        current_time = datetime.now()
        
        # Check if job has reached max executions
        if config.max_executions and job.execution_count >= config.max_executions:
            job.status = JobStatus.COMPLETED
            return None
        
        # Check if job has passed end time
        if config.end_time and current_time >= config.end_time:
            job.status = JobStatus.COMPLETED
            return None
        
        if config.schedule_type == ScheduleType.CRON:
            if config.cron_expression:
                cron = croniter.croniter(config.cron_expression, current_time)
                return cron.get_next(datetime)
        
        elif config.schedule_type == ScheduleType.INTERVAL:
            if config.interval_seconds:
                return current_time + timedelta(seconds=config.interval_seconds)
        
        elif config.schedule_type == ScheduleType.ONE_TIME:
            if config.start_time and config.start_time > current_time:
                return config.start_time
            else:
                job.status = JobStatus.COMPLETED
                return None
        
        return None
    
    async def _check_dependencies(self, job: ScheduledJob) -> bool:
        """Check if job dependencies are satisfied"""
        if not job.dependencies:
            return True
        
        for dependency in job.dependencies:
            dependent_job = self.scheduled_jobs.get(dependency.dependent_job_id)
            if not dependent_job:
                continue
            
            # Check dependency conditions
            if dependency.dependency_type == "completion":
                if dependent_job.last_execution is None:
                    return False
            elif dependency.dependency_type == "success":
                if dependent_job.success_count == 0:
                    return False
        
        return True
    
    async def _validate_job(self, job: ScheduledJob) -> bool:
        """Validate job configuration"""
        try:
            # Check if ERP adapter is available
            if job.erp_type not in self.data_extractor.adapters:
                return False
            
            # Validate schedule configuration
            config = job.schedule_config
            
            if config.schedule_type == ScheduleType.CRON:
                if not config.cron_expression:
                    return False
                # Validate cron expression
                try:
                    croniter.croniter(config.cron_expression)
                except Exception:
                    return False
            
            elif config.schedule_type == ScheduleType.INTERVAL:
                if not config.interval_seconds or config.interval_seconds <= 0:
                    return False
            
            elif config.schedule_type == ScheduleType.ONE_TIME:
                if not config.start_time:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Job validation failed: {e}")
            return False
    
    async def _cleanup_completed_executions(self) -> None:
        """Clean up completed execution tasks"""
        completed_executions = []
        
        for execution_id, task in self.active_executions.items():
            if task.done():
                completed_executions.append(execution_id)
        
        for execution_id in completed_executions:
            del self.active_executions[execution_id]
    
    async def _cleanup_loop(self) -> None:
        """Cleanup loop for old executions and data"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)
                await self._cleanup_old_executions(self.config.execution_history_days * 24)
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
    
    async def _cleanup_old_executions(self, max_age_hours: int) -> int:
        """Clean up old job executions"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        executions_to_remove = []
        for execution_id, execution in self.job_executions.items():
            if (execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED] and
                execution.end_time and execution.end_time < cutoff_time):
                executions_to_remove.append(execution_id)
        
        for execution_id in executions_to_remove:
            del self.job_executions[execution_id]
            cleaned_count += 1
        
        return cleaned_count
    
    async def _health_check_loop(self) -> None:
        """Health check loop"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.health_check_interval_seconds)
                
                # Check batch processor health
                if self.batch_processor and not self.batch_processor.is_running:
                    logger.warning("Batch processor is not running")
                
                # Check for stuck executions
                current_time = datetime.now()
                for execution_id, execution in self.job_executions.items():
                    if (execution.status == ExecutionStatus.RUNNING and
                        execution.start_time and
                        (current_time - execution.start_time).total_seconds() > self.config.job_timeout_seconds):
                        
                        logger.warning(f"Execution {execution_id} appears to be stuck")
                        
                        # Cancel stuck execution
                        if execution_id in self.active_executions:
                            self.active_executions[execution_id].cancel()
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    async def _send_notifications(self, job: ScheduledJob, execution: JobExecution) -> None:
        """Send notifications for job completion"""
        for handler in self.config.notification_handlers:
            try:
                await handler(job, execution)
            except Exception as e:
                logger.error(f"Notification handler failed: {e}")
    
    async def _load_scheduled_jobs(self) -> None:
        """Load scheduled jobs from persistence"""
        if not self.persistence_path:
            return
        
        try:
            for job_file in self.persistence_path.glob("*.json"):
                with open(job_file, 'r') as f:
                    job_data = json.load(f)
                    job = self._dict_to_scheduled_job(job_data)
                    self.scheduled_jobs[job.job_id] = job
            
            logger.info(f"Loaded {len(self.scheduled_jobs)} scheduled jobs")
        except Exception as e:
            logger.error(f"Failed to load scheduled jobs: {e}")
    
    async def _save_scheduled_jobs(self) -> None:
        """Save all scheduled jobs to persistence"""
        if not self.persistence_path:
            return
        
        try:
            for job in self.scheduled_jobs.values():
                await self._save_job(job)
        except Exception as e:
            logger.error(f"Failed to save scheduled jobs: {e}")
    
    async def _save_job(self, job: ScheduledJob) -> None:
        """Save a single job to persistence"""
        if not self.persistence_path:
            return
        
        try:
            job_data = self._scheduled_job_to_dict(job)
            job_file = self.persistence_path / f"{job.job_id}.json"
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save job {job.job_id}: {e}")
    
    def _dict_to_scheduled_job(self, data: Dict[str, Any]) -> ScheduledJob:
        """Convert dictionary to ScheduledJob object"""
        # Implementation for deserializing job data
        # This is a simplified version - full implementation would handle all fields
        job = ScheduledJob(
            job_id=data["job_id"],
            job_name=data["job_name"],
            job_type=JobType(data["job_type"]),
            erp_type=ERPType(data["erp_type"]),
            schedule_config=ScheduleConfig(
                schedule_type=ScheduleType(data["schedule_config"]["schedule_type"])
            )
        )
        return job
    
    def _scheduled_job_to_dict(self, job: ScheduledJob) -> Dict[str, Any]:
        """Convert ScheduledJob object to dictionary"""
        # Implementation for serializing job data
        # This is a simplified version - full implementation would handle all fields
        return {
            "job_id": job.job_id,
            "job_name": job.job_name,
            "job_type": job.job_type.value,
            "erp_type": job.erp_type.value,
            "schedule_config": {
                "schedule_type": job.schedule_config.schedule_type.value
            }
        }
    
    def get_scheduled_jobs(self) -> List[ScheduledJob]:
        """Get all scheduled jobs"""
        return list(self.scheduled_jobs.values())
    
    def get_job_executions(self, job_id: Optional[str] = None) -> List[JobExecution]:
        """Get job executions, optionally filtered by job ID"""
        executions = list(self.job_executions.values())
        if job_id:
            executions = [e for e in executions if e.job_id == job_id]
        return executions
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "scheduled_jobs": len(self.scheduled_jobs),
            "active_executions": len(self.active_executions),
            "total_executions": len(self.job_executions),
            "config": {
                "max_concurrent_jobs": self.config.max_concurrent_jobs,
                "job_timeout_seconds": self.config.job_timeout_seconds
            }
        }


# Factory function for creating extraction scheduler
def create_extraction_scheduler(
    config: Optional[SchedulerConfig] = None,
    data_extractor: Optional[ERPDataExtractor] = None,
    batch_processor: Optional[BatchProcessor] = None,
    sync_service: Optional[IncrementalSyncService] = None
) -> ExtractionScheduler:
    """Factory function to create an extraction scheduler"""
    if config is None:
        config = SchedulerConfig()
    
    if data_extractor is None:
        from .erp_data_extractor import erp_data_extractor
        data_extractor = erp_data_extractor
    
    return ExtractionScheduler(config, data_extractor, batch_processor, sync_service)