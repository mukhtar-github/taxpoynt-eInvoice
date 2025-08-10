"""
Batch Processor Service

This module handles large-scale batch processing of invoice data with optimized
memory usage, parallel processing, and robust error handling.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager
import json
import hashlib
from pathlib import Path

from .erp_data_extractor import InvoiceData, ExtractionFilter, ERPType, ERPDataExtractor

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Status of batch processing operations"""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ProcessingPriority(Enum):
    """Priority levels for batch processing"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class BatchConfig:
    """Configuration for batch processing"""
    batch_size: int = 1000
    max_concurrent_batches: int = 5
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout_seconds: int = 300
    enable_checkpoints: bool = True
    checkpoint_interval: int = 100
    memory_limit_mb: int = 512
    temp_storage_path: Optional[str] = None


@dataclass
class BatchJob:
    """Represents a batch processing job"""
    job_id: str
    erp_type: ERPType
    filters: ExtractionFilter
    priority: ProcessingPriority = ProcessingPriority.NORMAL
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_records: int = 0
    processed_records: int = 0
    failed_records: int = 0
    current_batch: int = 0
    total_batches: int = 0
    error_details: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    progress_callback: Optional[Callable] = None


@dataclass
class BatchResult:
    """Result of a batch processing operation"""
    job_id: str
    status: BatchStatus
    total_records: int
    processed_records: int
    failed_records: int
    processing_time: float
    throughput: float  # records per second
    error_summary: Dict[str, int]
    checkpoint_data: Optional[Dict[str, Any]] = None


@dataclass
class ProcessingMetrics:
    """Metrics for batch processing performance"""
    total_jobs: int = 0
    completed_jobs: int = 0
    failed_jobs: int = 0
    total_records_processed: int = 0
    average_throughput: float = 0.0
    peak_memory_usage: float = 0.0
    error_rate: float = 0.0


class BatchProcessor:
    """
    Advanced batch processor for handling large-scale invoice data processing
    with support for parallel processing, checkpointing, and recovery.
    """
    
    def __init__(self, config: BatchConfig, data_extractor: ERPDataExtractor):
        self.config = config
        self.data_extractor = data_extractor
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_queue: asyncio.Queue = asyncio.Queue()
        self.processing_semaphore = asyncio.Semaphore(config.max_concurrent_batches)
        self.metrics = ProcessingMetrics()
        self.is_running = False
        self.worker_tasks: List[asyncio.Task] = []
        
        # Setup temp storage
        if config.temp_storage_path:
            self.temp_storage = Path(config.temp_storage_path)
            self.temp_storage.mkdir(parents=True, exist_ok=True)
        else:
            self.temp_storage = None
    
    async def start_processing(self) -> None:
        """Start the batch processing workers"""
        if self.is_running:
            return
        
        self.is_running = True
        logger.info("Starting batch processing workers")
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_batches):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
    
    async def stop_processing(self) -> None:
        """Stop the batch processing workers"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping batch processing workers")
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
    
    async def submit_job(self, job: BatchJob) -> str:
        """Submit a batch job for processing"""
        # Generate job ID if not provided
        if not job.job_id:
            job.job_id = self._generate_job_id(job)
        
        # Validate job
        if not await self._validate_job(job):
            raise ValueError(f"Invalid job configuration: {job.job_id}")
        
        # Calculate total batches
        try:
            async with self.data_extractor.get_connection(job.erp_type) as adapter:
                total_records = await adapter.get_invoice_count(job.filters)
                job.total_records = total_records
                job.total_batches = (total_records + job.filters.batch_size - 1) // job.filters.batch_size
        except Exception as e:
            logger.error(f"Failed to calculate job size for {job.job_id}: {e}")
            raise
        
        # Add to active jobs and queue
        self.active_jobs[job.job_id] = job
        await self.job_queue.put(job)
        
        self.metrics.total_jobs += 1
        logger.info(f"Submitted batch job {job.job_id} with {job.total_records} records")
        
        return job.job_id
    
    async def get_job_status(self, job_id: str) -> Optional[BatchJob]:
        """Get the status of a batch job"""
        return self.active_jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a batch job"""
        job = self.active_jobs.get(job_id)
        if not job:
            return False
        
        if job.status in [BatchStatus.PENDING, BatchStatus.QUEUED]:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.now()
            return True
        elif job.status == BatchStatus.PROCESSING:
            job.status = BatchStatus.CANCELLED
            return True
        
        return False
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a batch job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == BatchStatus.PROCESSING:
            job.status = BatchStatus.PAUSED
            return True
        return False
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused batch job"""
        job = self.active_jobs.get(job_id)
        if job and job.status == BatchStatus.PAUSED:
            job.status = BatchStatus.QUEUED
            await self.job_queue.put(job)
            return True
        return False
    
    async def _worker(self, worker_name: str) -> None:
        """Worker coroutine for processing batch jobs"""
        logger.info(f"Starting worker: {worker_name}")
        
        while self.is_running:
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                
                if job.status == BatchStatus.CANCELLED:
                    continue
                
                # Process the job
                await self._process_job(job, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1.0)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_job(self, job: BatchJob, worker_name: str) -> None:
        """Process a single batch job"""
        async with self.processing_semaphore:
            try:
                job.status = BatchStatus.PROCESSING
                job.started_at = datetime.now()
                
                logger.info(f"Worker {worker_name} processing job {job.job_id}")
                
                # Process batches
                async for batch_result in self._process_batches(job):
                    if job.status == BatchStatus.CANCELLED:
                        break
                    
                    # Update progress
                    job.processed_records += batch_result['processed']
                    job.failed_records += batch_result['failed']
                    job.current_batch += 1
                    
                    # Call progress callback if provided
                    if job.progress_callback:
                        try:
                            await job.progress_callback(job)
                        except Exception as e:
                            logger.error(f"Progress callback error: {e}")
                    
                    # Create checkpoint
                    if self.config.enable_checkpoints and job.current_batch % self.config.checkpoint_interval == 0:
                        await self._create_checkpoint(job)
                
                # Finalize job
                if job.status != BatchStatus.CANCELLED:
                    job.status = BatchStatus.COMPLETED
                    self.metrics.completed_jobs += 1
                
                job.completed_at = datetime.now()
                
                # Calculate throughput
                processing_time = (job.completed_at - job.started_at).total_seconds()
                if processing_time > 0:
                    throughput = job.processed_records / processing_time
                    logger.info(f"Job {job.job_id} completed: {job.processed_records} records in {processing_time:.2f}s ({throughput:.2f} records/s)")
                
            except Exception as e:
                logger.error(f"Job {job.job_id} failed: {e}")
                job.status = BatchStatus.FAILED
                job.completed_at = datetime.now()
                job.error_details.append({
                    "error": str(e),
                    "timestamp": datetime.now(),
                    "worker": worker_name
                })
                self.metrics.failed_jobs += 1
    
    async def _process_batches(self, job: BatchJob) -> AsyncGenerator[Dict[str, Any], None]:
        """Process batches for a job"""
        batch_size = job.filters.batch_size
        
        for batch_num in range(job.current_batch, job.total_batches):
            if job.status in [BatchStatus.CANCELLED, BatchStatus.PAUSED]:
                break
            
            try:
                # Calculate batch offset
                offset = batch_num * batch_size
                
                # Create batch filter
                batch_filter = ExtractionFilter(
                    start_date=job.filters.start_date,
                    end_date=job.filters.end_date,
                    company_ids=job.filters.company_ids,
                    invoice_types=job.filters.invoice_types,
                    status_filter=job.filters.status_filter,
                    batch_size=batch_size,
                    include_draft=job.filters.include_draft,
                    include_cancelled=job.filters.include_cancelled
                )
                
                # Extract batch data
                batch_start = datetime.now()
                async with self.data_extractor.get_connection(job.erp_type) as adapter:
                    invoices = await adapter.extract_invoices(batch_filter)
                
                # Process batch
                processed_count, failed_count = await self._process_invoice_batch(invoices, job)
                
                batch_time = (datetime.now() - batch_start).total_seconds()
                
                yield {
                    "batch_num": batch_num,
                    "processed": processed_count,
                    "failed": failed_count,
                    "processing_time": batch_time,
                    "records": len(invoices)
                }
                
            except Exception as e:
                logger.error(f"Batch {batch_num} failed for job {job.job_id}: {e}")
                job.error_details.append({
                    "batch": batch_num,
                    "error": str(e),
                    "timestamp": datetime.now()
                })
                yield {
                    "batch_num": batch_num,
                    "processed": 0,
                    "failed": batch_size,
                    "processing_time": 0,
                    "records": 0
                }
    
    async def _process_invoice_batch(
        self,
        invoices: List[InvoiceData],
        job: BatchJob
    ) -> Tuple[int, int]:
        """Process a batch of invoices"""
        processed_count = 0
        failed_count = 0
        
        for invoice in invoices:
            try:
                # Process individual invoice
                success = await self._process_single_invoice(invoice, job)
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                logger.error(f"Failed to process invoice {invoice.invoice_id}: {e}")
                failed_count += 1
        
        return processed_count, failed_count
    
    async def _process_single_invoice(
        self,
        invoice: InvoiceData,
        job: BatchJob
    ) -> bool:
        """Process a single invoice"""
        try:
            # Add custom processing logic here
            # This could include validation, transformation, storage, etc.
            
            # For now, just log the processing
            logger.debug(f"Processing invoice {invoice.invoice_id}")
            
            # Simulate processing time
            await asyncio.sleep(0.01)
            
            return True
            
        except Exception as e:
            logger.error(f"Invoice processing failed {invoice.invoice_id}: {e}")
            return False
    
    async def _create_checkpoint(self, job: BatchJob) -> None:
        """Create a checkpoint for job recovery"""
        if not self.temp_storage:
            return
        
        try:
            checkpoint_data = {
                "job_id": job.job_id,
                "current_batch": job.current_batch,
                "processed_records": job.processed_records,
                "failed_records": job.failed_records,
                "timestamp": datetime.now().isoformat(),
                "metadata": job.metadata
            }
            
            checkpoint_file = self.temp_storage / f"{job.job_id}_checkpoint.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            logger.debug(f"Created checkpoint for job {job.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to create checkpoint for job {job.job_id}: {e}")
    
    async def load_checkpoint(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load checkpoint data for job recovery"""
        if not self.temp_storage:
            return None
        
        try:
            checkpoint_file = self.temp_storage / f"{job_id}_checkpoint.json"
            if checkpoint_file.exists():
                with open(checkpoint_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint for job {job_id}: {e}")
        
        return None
    
    def _generate_job_id(self, job: BatchJob) -> str:
        """Generate a unique job ID"""
        content = f"{job.erp_type.value}_{job.filters.start_date}_{job.filters.end_date}_{datetime.now()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _validate_job(self, job: BatchJob) -> bool:
        """Validate job configuration"""
        try:
            # Check if ERP adapter is available
            adapter = self.data_extractor.get_adapter(job.erp_type)
            if not adapter:
                return False
            
            # Validate filters
            if job.filters.batch_size <= 0:
                return False
            
            if job.filters.start_date and job.filters.end_date:
                if job.filters.start_date > job.filters.end_date:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Job validation failed: {e}")
            return False
    
    def get_metrics(self) -> ProcessingMetrics:
        """Get current processing metrics"""
        # Update calculated metrics
        if self.metrics.total_jobs > 0:
            self.metrics.error_rate = self.metrics.failed_jobs / self.metrics.total_jobs
        
        return self.metrics
    
    async def cleanup_completed_jobs(self, max_age_hours: int = 24) -> int:
        """Clean up completed jobs older than specified age"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cleaned_count = 0
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED] and
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            
            # Remove checkpoint files
            if self.temp_storage:
                checkpoint_file = self.temp_storage / f"{job_id}_checkpoint.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
            
            cleaned_count += 1
        
        logger.info(f"Cleaned up {cleaned_count} completed jobs")
        return cleaned_count


# Factory function for creating batch processor
def create_batch_processor(
    config: Optional[BatchConfig] = None,
    data_extractor: Optional[ERPDataExtractor] = None
) -> BatchProcessor:
    """Factory function to create a batch processor"""
    if config is None:
        config = BatchConfig()
    
    if data_extractor is None:
        from .erp_data_extractor import erp_data_extractor
        data_extractor = erp_data_extractor
    
    return BatchProcessor(config, data_extractor)