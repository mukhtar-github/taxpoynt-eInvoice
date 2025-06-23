"""
Salesforce Batch Processor for Historical Data Import.

This module provides batch processing capabilities for importing large volumes
of historical data from Salesforce with efficient memory usage and error handling.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from dataclasses import dataclass
from enum import Enum
import math

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.integrations.crm.salesforce.connector import SalesforceConnector
from app.integrations.crm.salesforce.sync_manager import SalesforceSyncManager, SyncResult
from app.models.crm import CRMConnection, CRMDeal
from app.core.database import get_async_db
from app.core.logging import get_logger

logger = get_logger(__name__)


class BatchStatus(str, Enum):
    """Batch processing status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchJob:
    """Batch processing job configuration."""
    job_id: str
    connection_id: str
    total_records: int
    batch_size: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    stage_filter: Optional[List[str]] = None
    status: BatchStatus = BatchStatus.PENDING
    progress: int = 0
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class BatchProgress:
    """Batch processing progress information."""
    job_id: str
    total_records: int
    processed_records: int
    successful_records: int
    failed_records: int
    current_batch: int
    total_batches: int
    progress_percentage: float
    estimated_completion: Optional[datetime]
    errors: List[str]


class SalesforceBatchProcessor:
    """Processes large volumes of Salesforce data in batches."""
    
    def __init__(self, connection: CRMConnection, db_session: AsyncSession):
        """
        Initialize the batch processor.
        
        Args:
            connection: CRM connection configuration
            db_session: Database session
        """
        self.connection = connection
        self.db_session = db_session
        self.connector = SalesforceConnector(connection.credentials)
        self.sync_manager = SalesforceSyncManager(connection, db_session)
        
        # Batch processing configuration
        self.default_batch_size = 50  # Smaller batches for stability
        self.max_parallel_batches = 3  # Limit concurrent processing
        self.rate_limit_delay = 2  # Seconds between batches
        self.retry_attempts = 3
        self.checkpoint_frequency = 10  # Save progress every N batches
        
        # In-memory job tracking
        self.active_jobs: Dict[str, BatchJob] = {}
        self.job_progress: Dict[str, BatchProgress] = {}
    
    async def start_historical_import(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        stage_filter: Optional[List[str]] = None,
        batch_size: Optional[int] = None,
        progress_callback: Optional[Callable[[BatchProgress], None]] = None
    ) -> str:
        """
        Start a historical data import job.
        
        Args:
            start_date: Start date for data import (default: 1 year ago)
            end_date: End date for data import (default: now)
            stage_filter: Filter by specific opportunity stages
            batch_size: Number of records per batch
            progress_callback: Callback function for progress updates
            
        Returns:
            Job ID for tracking progress
        """
        # Set default date range
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()
        
        if not batch_size:
            batch_size = self.default_batch_size
        
        # Generate job ID
        job_id = f"sf_import_{self.connection.id}_{int(datetime.now().timestamp())}"
        
        try:
            # Get total record count
            logger.info(f"Calculating total records for import job {job_id}")
            total_records = await self._get_total_record_count(start_date, end_date, stage_filter)
            
            if total_records == 0:
                logger.warning(f"No records found for import job {job_id}")
                raise ValueError("No records found for the specified criteria")
            
            # Create batch job
            job = BatchJob(
                job_id=job_id,
                connection_id=self.connection.id,
                total_records=total_records,
                batch_size=batch_size,
                start_date=start_date,
                end_date=end_date,
                stage_filter=stage_filter
            )
            
            self.active_jobs[job_id] = job
            
            # Initialize progress tracking
            total_batches = math.ceil(total_records / batch_size)
            self.job_progress[job_id] = BatchProgress(
                job_id=job_id,
                total_records=total_records,
                processed_records=0,
                successful_records=0,
                failed_records=0,
                current_batch=0,
                total_batches=total_batches,
                progress_percentage=0.0,
                estimated_completion=None,
                errors=[]
            )
            
            # Start the import process asynchronously
            asyncio.create_task(self._execute_import_job(job, progress_callback))
            
            logger.info(f"Started historical import job {job_id} for {total_records} records")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to start historical import: {str(e)}")
            if job_id in self.active_jobs:
                self.active_jobs[job_id].status = BatchStatus.FAILED
                self.active_jobs[job_id].error_message = str(e)
            raise
    
    async def _get_total_record_count(
        self,
        start_date: datetime,
        end_date: datetime,
        stage_filter: Optional[List[str]]
    ) -> int:
        """Get the total number of records to be processed."""
        try:
            # Build SOQL query for counting
            query = "SELECT COUNT() FROM Opportunity"
            where_conditions = []
            
            # Add date filter
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            where_conditions.append(f"LastModifiedDate >= {start_str}")
            where_conditions.append(f"LastModifiedDate <= {end_str}")
            
            # Add stage filter
            if stage_filter:
                quoted_stages = [f"'{stage}'" for stage in stage_filter]
                where_conditions.append(f"StageName IN ({', '.join(quoted_stages)})")
            
            if where_conditions:
                query += f" WHERE {' AND '.join(where_conditions)}"
            
            # Execute count query
            result = await self.connector._make_api_request("GET", "query", params={"q": query})
            return result.get("totalSize", 0)
            
        except Exception as e:
            logger.error(f"Failed to get record count: {str(e)}")
            # Fallback: estimate based on a sample query
            return 1000  # Conservative estimate
    
    async def _execute_import_job(
        self,
        job: BatchJob,
        progress_callback: Optional[Callable[[BatchProgress], None]]
    ):
        """Execute the import job."""
        try:
            job.status = BatchStatus.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Executing import job {job.job_id}")
            
            # Process data in batches
            async for batch_result in self._process_batches(job):
                # Update progress
                progress = self.job_progress[job.job_id]
                progress.processed_records += batch_result.records_processed
                progress.successful_records += batch_result.records_created + batch_result.records_updated
                progress.failed_records += batch_result.records_failed
                progress.current_batch += 1
                progress.progress_percentage = (progress.processed_records / progress.total_records) * 100
                progress.errors.extend(batch_result.errors)
                
                # Estimate completion time
                if progress.current_batch > 0:
                    elapsed_time = (datetime.now() - job.started_at).total_seconds()
                    avg_batch_time = elapsed_time / progress.current_batch
                    remaining_batches = progress.total_batches - progress.current_batch
                    estimated_seconds = remaining_batches * avg_batch_time
                    progress.estimated_completion = datetime.now() + timedelta(seconds=estimated_seconds)
                
                # Call progress callback if provided
                if progress_callback:
                    try:
                        progress_callback(progress)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {str(e)}")
                
                # Save checkpoint periodically
                if progress.current_batch % self.checkpoint_frequency == 0:
                    await self._save_checkpoint(job, progress)
                
                # Rate limiting
                await asyncio.sleep(self.rate_limit_delay)
            
            # Mark job as completed
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now()
            
            logger.info(f"Import job {job.job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Import job {job.job_id} failed: {str(e)}")
            job.status = BatchStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
    
    async def _process_batches(self, job: BatchJob) -> AsyncGenerator[SyncResult, None]:
        """Process data in batches."""
        total_batches = math.ceil(job.total_records / job.batch_size)
        
        for batch_num in range(total_batches):
            try:
                offset = batch_num * job.batch_size
                
                logger.debug(f"Processing batch {batch_num + 1}/{total_batches} for job {job.job_id}")
                
                # Get opportunities for this batch
                opportunities_result = await self.connector.get_opportunities(
                    limit=job.batch_size,
                    offset=offset,
                    modified_since=job.start_date,
                    stage_names=job.stage_filter
                )
                
                opportunities = opportunities_result.get("opportunities", [])
                
                if not opportunities:
                    # No more data
                    break
                
                # Process this batch
                batch_result = await self.sync_manager._process_opportunity_batch(opportunities)
                yield batch_result
                
            except Exception as e:
                logger.error(f"Batch {batch_num + 1} failed for job {job.job_id}: {str(e)}")
                # Yield a failed result
                yield SyncResult(
                    success=False,
                    records_processed=0,
                    records_created=0,
                    records_updated=0,
                    records_failed=job.batch_size,
                    errors=[str(e)],
                    duration_seconds=0.0,
                    sync_timestamp=datetime.now()
                )
    
    async def _save_checkpoint(self, job: BatchJob, progress: BatchProgress):
        """Save processing checkpoint."""
        try:
            # Update connection with current progress
            self.connection.last_sync = datetime.now()
            await self.db_session.flush()
            
            logger.debug(f"Saved checkpoint for job {job.job_id}: "
                        f"{progress.processed_records}/{progress.total_records} processed")
            
        except Exception as e:
            logger.warning(f"Failed to save checkpoint for job {job.job_id}: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch job."""
        if job_id not in self.active_jobs:
            return None
        
        job = self.active_jobs[job_id]
        progress = self.job_progress.get(job_id)
        
        return {
            "job_id": job.job_id,
            "connection_id": job.connection_id,
            "status": job.status,
            "total_records": job.total_records,
            "batch_size": job.batch_size,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "progress": {
                "processed_records": progress.processed_records if progress else 0,
                "successful_records": progress.successful_records if progress else 0,
                "failed_records": progress.failed_records if progress else 0,
                "current_batch": progress.current_batch if progress else 0,
                "total_batches": progress.total_batches if progress else 0,
                "progress_percentage": progress.progress_percentage if progress else 0.0,
                "estimated_completion": progress.estimated_completion.isoformat() if progress and progress.estimated_completion else None,
                "error_count": len(progress.errors) if progress else 0
            }
        }
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job."""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status == BatchStatus.RUNNING:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.now()
            logger.info(f"Cancelled batch job {job_id}")
            return True
        
        return False
    
    async def retry_failed_job(self, job_id: str) -> bool:
        """Retry a failed batch job."""
        if job_id not in self.active_jobs:
            return False
        
        job = self.active_jobs[job_id]
        
        if job.status == BatchStatus.FAILED:
            # Reset job status and restart
            job.status = BatchStatus.PENDING
            job.started_at = None
            job.completed_at = None
            job.error_message = None
            
            # Reset progress
            if job_id in self.job_progress:
                progress = self.job_progress[job_id]
                progress.processed_records = 0
                progress.successful_records = 0
                progress.failed_records = 0
                progress.current_batch = 0
                progress.progress_percentage = 0.0
                progress.estimated_completion = None
                progress.errors = []
            
            # Start the job again
            asyncio.create_task(self._execute_import_job(job, None))
            
            logger.info(f"Restarted batch job {job_id}")
            return True
        
        return False
    
    async def cleanup_completed_jobs(self, older_than_hours: int = 24):
        """Clean up completed jobs older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED] and
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
            if job_id in self.job_progress:
                del self.job_progress[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} completed batch jobs")
    
    async def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get status of all batch jobs."""
        jobs = []
        for job_id in self.active_jobs:
            job_status = await self.get_job_status(job_id)
            if job_status:
                jobs.append(job_status)
        
        return jobs
    
    async def estimate_import_time(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        stage_filter: Optional[List[str]] = None,
        batch_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """Estimate the time required for a historical import."""
        if not start_date:
            start_date = datetime.now() - timedelta(days=365)
        if not end_date:
            end_date = datetime.now()
        if not batch_size:
            batch_size = self.default_batch_size
        
        try:
            # Get total record count
            total_records = await self._get_total_record_count(start_date, end_date, stage_filter)
            
            if total_records == 0:
                return {
                    "total_records": 0,
                    "estimated_duration_hours": 0,
                    "estimated_completion": datetime.now().isoformat(),
                    "total_batches": 0
                }
            
            # Estimate processing time
            total_batches = math.ceil(total_records / batch_size)
            
            # Rough estimates based on API rate limits and processing time
            seconds_per_batch = 5  # Conservative estimate including rate limiting
            total_seconds = total_batches * seconds_per_batch
            total_hours = total_seconds / 3600
            
            estimated_completion = datetime.now() + timedelta(seconds=total_seconds)
            
            return {
                "total_records": total_records,
                "estimated_duration_hours": round(total_hours, 2),
                "estimated_completion": estimated_completion.isoformat(),
                "total_batches": total_batches,
                "batch_size": batch_size,
                "date_range": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate import time: {str(e)}")
            raise


async def create_batch_processor(connection_id: str) -> SalesforceBatchProcessor:
    """
    Create a batch processor for a specific connection.
    
    Args:
        connection_id: ID of the CRM connection
        
    Returns:
        SalesforceBatchProcessor instance
    """
    async with get_async_db() as db_session:
        # Get the connection
        result = await db_session.execute(
            select(CRMConnection).where(CRMConnection.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        if connection.crm_type != "salesforce":
            raise ValueError(f"Connection {connection_id} is not a Salesforce connection")
        
        return SalesforceBatchProcessor(connection, db_session)