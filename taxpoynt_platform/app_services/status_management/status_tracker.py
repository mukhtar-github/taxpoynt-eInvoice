"""
Status Tracker Service for APP Role

This service tracks the status of all submissions to FIRS including:
- Real-time status tracking and updates
- Status history and lifecycle management
- Multi-stage submission workflow tracking
- Status persistence and recovery
- Performance metrics and analytics
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import uuid
import sqlite3
import aiosqlite

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubmissionStatus(Enum):
    """Submission status values"""
    PENDING = "pending"
    VALIDATING = "validating"
    VALIDATED = "validated"
    QUEUED = "queued"
    TRANSMITTING = "transmitting"
    TRANSMITTED = "transmitted"
    PROCESSING = "processing"
    ACKNOWLEDGED = "acknowledged"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    RETRY = "retry"


class SubmissionType(Enum):
    """Types of submissions"""
    INVOICE = "invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    CANCELLATION = "cancellation"
    BATCH = "batch"


class Priority(Enum):
    """Submission priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class StatusTransition:
    """Status transition record"""
    transition_id: str
    from_status: Optional[SubmissionStatus]
    to_status: SubmissionStatus
    timestamp: datetime
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None


@dataclass
class SubmissionRecord:
    """Comprehensive submission record"""
    submission_id: str
    document_id: str
    submission_type: SubmissionType
    current_status: SubmissionStatus
    priority: Priority
    created_at: datetime
    updated_at: datetime
    submitted_by: str
    organization_id: str
    
    # Status tracking
    status_history: List[StatusTransition] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # Timing information
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # FIRS information
    firs_reference: Optional[str] = None
    firs_timestamp: Optional[datetime] = None
    acknowledgment_code: Optional[str] = None
    
    # Document information
    document_hash: Optional[str] = None
    document_size: Optional[int] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatusQuery:
    """Query parameters for status search"""
    submission_ids: Optional[List[str]] = None
    document_ids: Optional[List[str]] = None
    submission_types: Optional[List[SubmissionType]] = None
    statuses: Optional[List[SubmissionStatus]] = None
    priorities: Optional[List[Priority]] = None
    organization_ids: Optional[List[str]] = None
    submitted_by: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = 100
    offset: int = 0


@dataclass
class StatusStatistics:
    """Status tracking statistics"""
    total_submissions: int
    status_counts: Dict[str, int]
    priority_counts: Dict[str, int]
    type_counts: Dict[str, int]
    average_processing_time: float
    success_rate: float
    retry_rate: float
    timeout_rate: float
    submissions_last_24h: int
    submissions_last_hour: int


class StatusTracker:
    """
    Status tracker service for APP role
    
    Handles:
    - Real-time status tracking and updates
    - Status history and lifecycle management
    - Multi-stage submission workflow tracking
    - Status persistence and recovery
    - Performance metrics and analytics
    """
    
    def __init__(self,
                 database_path: str = "status_tracker.db",
                 default_timeout: int = 3600,  # 1 hour
                 cleanup_interval: int = 86400):  # 24 hours
        
        self.database_path = database_path
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        
        # In-memory storage for fast access
        self.active_submissions: Dict[str, SubmissionRecord] = {}
        self.status_listeners: Dict[str, List[Callable]] = defaultdict(list)
        
        # Database connection
        self.db_connection: Optional[aiosqlite.Connection] = None
        
        # Status workflow definitions
        self.status_workflows = {
            SubmissionType.INVOICE: [
                SubmissionStatus.PENDING,
                SubmissionStatus.VALIDATING,
                SubmissionStatus.VALIDATED,
                SubmissionStatus.QUEUED,
                SubmissionStatus.TRANSMITTING,
                SubmissionStatus.TRANSMITTED,
                SubmissionStatus.PROCESSING,
                SubmissionStatus.ACKNOWLEDGED,
                SubmissionStatus.ACCEPTED
            ],
            SubmissionType.BATCH: [
                SubmissionStatus.PENDING,
                SubmissionStatus.VALIDATING,
                SubmissionStatus.VALIDATED,
                SubmissionStatus.QUEUED,
                SubmissionStatus.TRANSMITTING,
                SubmissionStatus.TRANSMITTED,
                SubmissionStatus.PROCESSING,
                SubmissionStatus.ACKNOWLEDGED,
                SubmissionStatus.ACCEPTED
            ]
        }
        
        # Valid status transitions
        self.valid_transitions = {
            SubmissionStatus.PENDING: [SubmissionStatus.VALIDATING, SubmissionStatus.CANCELLED],
            SubmissionStatus.VALIDATING: [SubmissionStatus.VALIDATED, SubmissionStatus.FAILED, SubmissionStatus.RETRY],
            SubmissionStatus.VALIDATED: [SubmissionStatus.QUEUED, SubmissionStatus.FAILED],
            SubmissionStatus.QUEUED: [SubmissionStatus.TRANSMITTING, SubmissionStatus.CANCELLED],
            SubmissionStatus.TRANSMITTING: [SubmissionStatus.TRANSMITTED, SubmissionStatus.FAILED, SubmissionStatus.RETRY],
            SubmissionStatus.TRANSMITTED: [SubmissionStatus.PROCESSING, SubmissionStatus.TIMEOUT],
            SubmissionStatus.PROCESSING: [SubmissionStatus.ACKNOWLEDGED, SubmissionStatus.TIMEOUT, SubmissionStatus.FAILED],
            SubmissionStatus.ACKNOWLEDGED: [SubmissionStatus.ACCEPTED, SubmissionStatus.REJECTED],
            SubmissionStatus.RETRY: [SubmissionStatus.VALIDATING, SubmissionStatus.TRANSMITTING, SubmissionStatus.FAILED],
            SubmissionStatus.FAILED: [SubmissionStatus.RETRY, SubmissionStatus.CANCELLED],
            SubmissionStatus.TIMEOUT: [SubmissionStatus.RETRY, SubmissionStatus.FAILED]
        }
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.timeout_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Metrics
        self.metrics = {
            'total_submissions': 0,
            'status_transitions': 0,
            'successful_submissions': 0,
            'failed_submissions': 0,
            'retried_submissions': 0,
            'timeout_submissions': 0,
            'average_processing_time': 0.0,
            'status_counts': defaultdict(int),
            'type_counts': defaultdict(int),
            'priority_counts': defaultdict(int),
            'transitions_per_minute': deque(maxlen=60),
            'submissions_per_hour': deque(maxlen=24)
        }
    
    async def start(self):
        """Start the status tracker service"""
        self.running = True
        
        # Initialize database
        await self._init_database()
        
        # Load active submissions from database
        await self._load_active_submissions()
        
        # Start background tasks
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self.timeout_task = asyncio.create_task(self._check_timeouts())
        
        logger.info("Status tracker service started")
    
    async def stop(self):
        """Stop the status tracker service"""
        self.running = False
        
        # Cancel background tasks
        if self.cleanup_task:
            self.cleanup_task.cancel()
        if self.timeout_task:
            self.timeout_task.cancel()
        
        # Save active submissions to database
        await self._save_active_submissions()
        
        # Close database connection
        if self.db_connection:
            await self.db_connection.close()
        
        logger.info("Status tracker service stopped")
    
    async def create_submission(self,
                              document_id: str,
                              submission_type: SubmissionType,
                              submitted_by: str,
                              organization_id: str,
                              priority: Priority = Priority.NORMAL,
                              timeout_minutes: Optional[int] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create new submission tracking record
        
        Args:
            document_id: Document identifier
            submission_type: Type of submission
            submitted_by: User who submitted
            organization_id: Organization identifier
            priority: Submission priority
            timeout_minutes: Custom timeout in minutes
            metadata: Additional metadata
            
        Returns:
            Submission ID
        """
        submission_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Calculate timeout
        timeout_delta = timedelta(minutes=timeout_minutes or (self.default_timeout // 60))
        timeout_at = current_time + timeout_delta
        
        # Create submission record
        record = SubmissionRecord(
            submission_id=submission_id,
            document_id=document_id,
            submission_type=submission_type,
            current_status=SubmissionStatus.PENDING,
            priority=priority,
            created_at=current_time,
            updated_at=current_time,
            submitted_by=submitted_by,
            organization_id=organization_id,
            timeout_at=timeout_at,
            metadata=metadata or {}
        )
        
        # Add initial status transition
        initial_transition = StatusTransition(
            transition_id=str(uuid.uuid4()),
            from_status=None,
            to_status=SubmissionStatus.PENDING,
            timestamp=current_time,
            reason="Submission created"
        )
        record.status_history.append(initial_transition)
        
        # Store in memory and database
        self.active_submissions[submission_id] = record
        await self._save_submission_to_db(record)
        
        # Update metrics
        self.metrics['total_submissions'] += 1
        self.metrics['status_counts'][SubmissionStatus.PENDING.value] += 1
        self.metrics['type_counts'][submission_type.value] += 1
        self.metrics['priority_counts'][priority.value] += 1
        
        # Notify listeners
        await self._notify_status_change(submission_id, None, SubmissionStatus.PENDING)
        
        logger.info(f"Created submission tracking: {submission_id} for document {document_id}")
        
        return submission_id
    
    async def update_status(self,
                          submission_id: str,
                          new_status: SubmissionStatus,
                          reason: Optional[str] = None,
                          metadata: Optional[Dict[str, Any]] = None,
                          firs_reference: Optional[str] = None,
                          acknowledgment_code: Optional[str] = None) -> bool:
        """
        Update submission status
        
        Args:
            submission_id: Submission identifier
            new_status: New status to set
            reason: Reason for status change
            metadata: Additional metadata
            firs_reference: FIRS reference number
            acknowledgment_code: FIRS acknowledgment code
            
        Returns:
            True if status was updated successfully
        """
        if submission_id not in self.active_submissions:
            logger.warning(f"Submission not found: {submission_id}")
            return False
        
        record = self.active_submissions[submission_id]
        old_status = record.current_status
        
        # Validate transition
        if not self._is_valid_transition(old_status, new_status):
            logger.warning(f"Invalid status transition: {old_status.value} -> {new_status.value}")
            return False
        
        current_time = datetime.utcnow()
        
        # Calculate transition duration
        last_transition = record.status_history[-1] if record.status_history else None
        duration = (current_time - last_transition.timestamp).total_seconds() if last_transition else 0.0
        
        # Create status transition
        transition = StatusTransition(
            transition_id=str(uuid.uuid4()),
            from_status=old_status,
            to_status=new_status,
            timestamp=current_time,
            reason=reason,
            metadata=metadata or {},
            duration=duration
        )
        
        # Update record
        record.current_status = new_status
        record.updated_at = current_time
        record.status_history.append(transition)
        
        # Update FIRS information if provided
        if firs_reference:
            record.firs_reference = firs_reference
            record.firs_timestamp = current_time
        
        if acknowledgment_code:
            record.acknowledgment_code = acknowledgment_code
        
        # Update timestamps based on status
        if new_status == SubmissionStatus.TRANSMITTING and not record.started_at:
            record.started_at = current_time
        elif new_status in [SubmissionStatus.ACCEPTED, SubmissionStatus.REJECTED, SubmissionStatus.FAILED]:
            record.completed_at = current_time
        
        # Handle retry logic
        if new_status == SubmissionStatus.RETRY:
            record.retry_count += 1
            if record.retry_count >= record.max_retries:
                # Max retries reached, mark as failed
                await self.update_status(submission_id, SubmissionStatus.FAILED, "Maximum retries exceeded")
                return True
        
        # Update database
        await self._update_submission_in_db(record)
        
        # Update metrics
        self.metrics['status_transitions'] += 1
        self.metrics['status_counts'][old_status.value] -= 1
        self.metrics['status_counts'][new_status.value] += 1
        
        if new_status == SubmissionStatus.ACCEPTED:
            self.metrics['successful_submissions'] += 1
        elif new_status == SubmissionStatus.FAILED:
            self.metrics['failed_submissions'] += 1
        elif new_status == SubmissionStatus.RETRY:
            self.metrics['retried_submissions'] += 1
        elif new_status == SubmissionStatus.TIMEOUT:
            self.metrics['timeout_submissions'] += 1
        
        # Update average processing time for completed submissions
        if record.completed_at and record.started_at:
            processing_time = (record.completed_at - record.started_at).total_seconds()
            self._update_average_processing_time(processing_time)
        
        # Notify listeners
        await self._notify_status_change(submission_id, old_status, new_status)
        
        logger.info(f"Updated submission {submission_id}: {old_status.value} -> {new_status.value}")
        
        return True
    
    async def get_submission(self, submission_id: str) -> Optional[SubmissionRecord]:
        """Get submission record by ID"""
        if submission_id in self.active_submissions:
            return self.active_submissions[submission_id]
        
        # Try to load from database
        return await self._load_submission_from_db(submission_id)
    
    async def get_submission_status(self, submission_id: str) -> Optional[SubmissionStatus]:
        """Get current status of submission"""
        record = await self.get_submission(submission_id)
        return record.current_status if record else None
    
    async def query_submissions(self, query: StatusQuery) -> List[SubmissionRecord]:
        """
        Query submissions based on criteria
        
        Args:
            query: Query parameters
            
        Returns:
            List of matching submission records
        """
        # Start with active submissions
        results = []
        
        for record in self.active_submissions.values():
            if self._matches_query(record, query):
                results.append(record)
        
        # If we need more results, query database
        if len(results) < query.limit:
            db_results = await self._query_submissions_from_db(query, query.limit - len(results))
            results.extend(db_results)
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit and offset
        start = query.offset
        end = start + query.limit
        
        return results[start:end]
    
    async def get_submissions_by_document(self, document_id: str) -> List[SubmissionRecord]:
        """Get all submissions for a document"""
        query = StatusQuery(document_ids=[document_id])
        return await self.query_submissions(query)
    
    async def get_submissions_by_status(self, status: SubmissionStatus, limit: int = 100) -> List[SubmissionRecord]:
        """Get submissions by status"""
        query = StatusQuery(statuses=[status], limit=limit)
        return await self.query_submissions(query)
    
    async def add_status_listener(self, submission_id: str, callback: Callable):
        """Add status change listener for specific submission"""
        self.status_listeners[submission_id].append(callback)
    
    async def remove_status_listener(self, submission_id: str, callback: Callable):
        """Remove status change listener"""
        if submission_id in self.status_listeners:
            try:
                self.status_listeners[submission_id].remove(callback)
            except ValueError:
                pass
    
    async def cancel_submission(self, submission_id: str, reason: str = "User cancelled") -> bool:
        """Cancel submission"""
        return await self.update_status(submission_id, SubmissionStatus.CANCELLED, reason)
    
    async def retry_submission(self, submission_id: str, reason: str = "Manual retry") -> bool:
        """Retry failed submission"""
        record = await self.get_submission(submission_id)
        if not record:
            return False
        
        if record.current_status not in [SubmissionStatus.FAILED, SubmissionStatus.TIMEOUT]:
            logger.warning(f"Cannot retry submission {submission_id} with status {record.current_status.value}")
            return False
        
        return await self.update_status(submission_id, SubmissionStatus.RETRY, reason)
    
    def _is_valid_transition(self, from_status: SubmissionStatus, to_status: SubmissionStatus) -> bool:
        """Check if status transition is valid"""
        if from_status == to_status:
            return False
        
        valid_transitions = self.valid_transitions.get(from_status, [])
        return to_status in valid_transitions
    
    def _matches_query(self, record: SubmissionRecord, query: StatusQuery) -> bool:
        """Check if record matches query criteria"""
        if query.submission_ids and record.submission_id not in query.submission_ids:
            return False
        
        if query.document_ids and record.document_id not in query.document_ids:
            return False
        
        if query.submission_types and record.submission_type not in query.submission_types:
            return False
        
        if query.statuses and record.current_status not in query.statuses:
            return False
        
        if query.priorities and record.priority not in query.priorities:
            return False
        
        if query.organization_ids and record.organization_id not in query.organization_ids:
            return False
        
        if query.submitted_by and record.submitted_by not in query.submitted_by:
            return False
        
        if query.date_from and record.created_at < query.date_from:
            return False
        
        if query.date_to and record.created_at > query.date_to:
            return False
        
        return True
    
    async def _notify_status_change(self, submission_id: str, old_status: Optional[SubmissionStatus], new_status: SubmissionStatus):
        """Notify status change listeners"""
        listeners = self.status_listeners.get(submission_id, [])
        
        for callback in listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(submission_id, old_status, new_status)
                else:
                    callback(submission_id, old_status, new_status)
            except Exception as e:
                logger.error(f"Error notifying status listener: {e}")
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        current_avg = self.metrics['average_processing_time']
        completed_count = self.metrics['successful_submissions'] + self.metrics['failed_submissions']
        
        if completed_count > 0:
            self.metrics['average_processing_time'] = (
                (current_avg * (completed_count - 1) + processing_time) / completed_count
            )
    
    async def _check_timeouts(self):
        """Check for timed out submissions"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                timed_out_submissions = []
                
                for submission_id, record in self.active_submissions.items():
                    if (record.timeout_at and 
                        current_time > record.timeout_at and 
                        record.current_status not in [SubmissionStatus.ACCEPTED, SubmissionStatus.REJECTED, 
                                                    SubmissionStatus.FAILED, SubmissionStatus.CANCELLED]):
                        timed_out_submissions.append(submission_id)
                
                # Process timeouts
                for submission_id in timed_out_submissions:
                    await self.update_status(submission_id, SubmissionStatus.TIMEOUT, "Submission timeout")
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error checking timeouts: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of completed submissions"""
        while self.running:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Move completed submissions to archive
                completed_submissions = []
                for submission_id, record in list(self.active_submissions.items()):
                    if (record.completed_at and 
                        record.completed_at < cutoff_time and
                        record.current_status in [SubmissionStatus.ACCEPTED, SubmissionStatus.REJECTED, 
                                                SubmissionStatus.FAILED, SubmissionStatus.CANCELLED]):
                        completed_submissions.append(submission_id)
                
                # Archive completed submissions
                for submission_id in completed_submissions:
                    record = self.active_submissions.pop(submission_id, None)
                    if record:
                        await self._archive_submission(record)
                
                logger.info(f"Archived {len(completed_submissions)} completed submissions")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def _init_database(self):
        """Initialize database tables"""
        self.db_connection = await aiosqlite.connect(self.database_path)
        
        # Create tables
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                submission_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                submission_type TEXT NOT NULL,
                current_status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                submitted_by TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                started_at TEXT,
                completed_at TEXT,
                timeout_at TEXT,
                firs_reference TEXT,
                firs_timestamp TEXT,
                acknowledgment_code TEXT,
                document_hash TEXT,
                document_size INTEGER,
                validation_results TEXT,
                error_code TEXT,
                error_message TEXT,
                error_details TEXT,
                metadata TEXT
            )
        """)
        
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS status_transitions (
                transition_id TEXT PRIMARY KEY,
                submission_id TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                reason TEXT,
                metadata TEXT,
                duration REAL,
                FOREIGN KEY (submission_id) REFERENCES submissions (submission_id)
            )
        """)
        
        await self.db_connection.execute("""
            CREATE TABLE IF NOT EXISTS archived_submissions (
                submission_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                submission_type TEXT NOT NULL,
                final_status TEXT NOT NULL,
                priority TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                submitted_by TEXT NOT NULL,
                organization_id TEXT NOT NULL,
                processing_time REAL,
                retry_count INTEGER,
                firs_reference TEXT,
                acknowledgment_code TEXT,
                metadata TEXT,
                archived_at TEXT NOT NULL
            )
        """)
        
        # Create indexes
        await self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_submissions_document_id ON submissions(document_id)")
        await self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(current_status)")
        await self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_submissions_org_id ON submissions(organization_id)")
        await self.db_connection.execute("CREATE INDEX IF NOT EXISTS idx_transitions_submission_id ON status_transitions(submission_id)")
        
        await self.db_connection.commit()
        logger.info("Database initialized successfully")
    
    async def _save_submission_to_db(self, record: SubmissionRecord):
        """Save submission record to database"""
        if not self.db_connection:
            return
        
        await self.db_connection.execute("""
            INSERT OR REPLACE INTO submissions (
                submission_id, document_id, submission_type, current_status, priority,
                created_at, updated_at, submitted_by, organization_id, retry_count,
                max_retries, started_at, completed_at, timeout_at, firs_reference,
                firs_timestamp, acknowledgment_code, document_hash, document_size,
                validation_results, error_code, error_message, error_details, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.submission_id, record.document_id, record.submission_type.value,
            record.current_status.value, record.priority.value,
            record.created_at.isoformat(), record.updated_at.isoformat(),
            record.submitted_by, record.organization_id, record.retry_count,
            record.max_retries,
            record.started_at.isoformat() if record.started_at else None,
            record.completed_at.isoformat() if record.completed_at else None,
            record.timeout_at.isoformat() if record.timeout_at else None,
            record.firs_reference,
            record.firs_timestamp.isoformat() if record.firs_timestamp else None,
            record.acknowledgment_code, record.document_hash, record.document_size,
            json.dumps(record.validation_results), record.error_code,
            record.error_message, json.dumps(record.error_details),
            json.dumps(record.metadata)
        ))
        
        # Save status transitions
        for transition in record.status_history:
            await self.db_connection.execute("""
                INSERT OR REPLACE INTO status_transitions (
                    transition_id, submission_id, from_status, to_status,
                    timestamp, reason, metadata, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transition.transition_id, record.submission_id,
                transition.from_status.value if transition.from_status else None,
                transition.to_status.value, transition.timestamp.isoformat(),
                transition.reason, json.dumps(transition.metadata), transition.duration
            ))
        
        await self.db_connection.commit()
    
    async def _update_submission_in_db(self, record: SubmissionRecord):
        """Update submission record in database"""
        await self._save_submission_to_db(record)
    
    async def _load_submission_from_db(self, submission_id: str) -> Optional[SubmissionRecord]:
        """Load submission record from database"""
        if not self.db_connection:
            return None
        
        # Load submission
        cursor = await self.db_connection.execute(
            "SELECT * FROM submissions WHERE submission_id = ?", (submission_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            return None
        
        # Convert row to record
        record = self._row_to_submission_record(row)
        
        # Load status transitions
        cursor = await self.db_connection.execute(
            "SELECT * FROM status_transitions WHERE submission_id = ? ORDER BY timestamp",
            (submission_id,)
        )
        transitions = await cursor.fetchall()
        
        record.status_history = [self._row_to_status_transition(t) for t in transitions]
        
        return record
    
    async def _load_active_submissions(self):
        """Load active submissions from database"""
        if not self.db_connection:
            return
        
        cursor = await self.db_connection.execute("""
            SELECT * FROM submissions 
            WHERE current_status NOT IN ('accepted', 'rejected', 'failed', 'cancelled')
        """)
        rows = await cursor.fetchall()
        
        for row in rows:
            record = self._row_to_submission_record(row)
            
            # Load status transitions
            trans_cursor = await self.db_connection.execute(
                "SELECT * FROM status_transitions WHERE submission_id = ? ORDER BY timestamp",
                (record.submission_id,)
            )
            transitions = await trans_cursor.fetchall()
            record.status_history = [self._row_to_status_transition(t) for t in transitions]
            
            self.active_submissions[record.submission_id] = record
        
        logger.info(f"Loaded {len(self.active_submissions)} active submissions from database")
    
    async def _save_active_submissions(self):
        """Save active submissions to database"""
        for record in self.active_submissions.values():
            await self._save_submission_to_db(record)
    
    async def _archive_submission(self, record: SubmissionRecord):
        """Archive completed submission"""
        if not self.db_connection:
            return
        
        processing_time = None
        if record.completed_at and record.started_at:
            processing_time = (record.completed_at - record.started_at).total_seconds()
        
        await self.db_connection.execute("""
            INSERT INTO archived_submissions (
                submission_id, document_id, submission_type, final_status,
                priority, created_at, completed_at, submitted_by, organization_id,
                processing_time, retry_count, firs_reference, acknowledgment_code,
                metadata, archived_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.submission_id, record.document_id, record.submission_type.value,
            record.current_status.value, record.priority.value,
            record.created_at.isoformat(), record.completed_at.isoformat(),
            record.submitted_by, record.organization_id, processing_time,
            record.retry_count, record.firs_reference, record.acknowledgment_code,
            json.dumps(record.metadata), datetime.utcnow().isoformat()
        ))
        
        await self.db_connection.commit()
    
    def _row_to_submission_record(self, row) -> SubmissionRecord:
        """Convert database row to SubmissionRecord"""
        return SubmissionRecord(
            submission_id=row[0],
            document_id=row[1],
            submission_type=SubmissionType(row[2]),
            current_status=SubmissionStatus(row[3]),
            priority=Priority(row[4]),
            created_at=datetime.fromisoformat(row[5]),
            updated_at=datetime.fromisoformat(row[6]),
            submitted_by=row[7],
            organization_id=row[8],
            retry_count=row[9],
            max_retries=row[10],
            started_at=datetime.fromisoformat(row[11]) if row[11] else None,
            completed_at=datetime.fromisoformat(row[12]) if row[12] else None,
            timeout_at=datetime.fromisoformat(row[13]) if row[13] else None,
            firs_reference=row[14],
            firs_timestamp=datetime.fromisoformat(row[15]) if row[15] else None,
            acknowledgment_code=row[16],
            document_hash=row[17],
            document_size=row[18],
            validation_results=json.loads(row[19]) if row[19] else {},
            error_code=row[20],
            error_message=row[21],
            error_details=json.loads(row[22]) if row[22] else {},
            metadata=json.loads(row[23]) if row[23] else {}
        )
    
    def _row_to_status_transition(self, row) -> StatusTransition:
        """Convert database row to StatusTransition"""
        return StatusTransition(
            transition_id=row[0],
            from_status=SubmissionStatus(row[2]) if row[2] else None,
            to_status=SubmissionStatus(row[3]),
            timestamp=datetime.fromisoformat(row[4]),
            reason=row[5],
            metadata=json.loads(row[6]) if row[6] else {},
            duration=row[7]
        )
    
    async def _query_submissions_from_db(self, query: StatusQuery, limit: int) -> List[SubmissionRecord]:
        """Query submissions from database"""
        # This would implement database querying logic
        # For now, return empty list
        return []
    
    async def get_statistics(self) -> StatusStatistics:
        """Get status tracking statistics"""
        # Calculate success rate
        total_completed = (self.metrics['successful_submissions'] + 
                         self.metrics['failed_submissions'])
        success_rate = (self.metrics['successful_submissions'] / total_completed * 100 
                       if total_completed > 0 else 0.0)
        
        # Calculate retry rate
        retry_rate = (self.metrics['retried_submissions'] / 
                     max(self.metrics['total_submissions'], 1) * 100)
        
        # Calculate timeout rate
        timeout_rate = (self.metrics['timeout_submissions'] / 
                       max(self.metrics['total_submissions'], 1) * 100)
        
        # Recent submission counts
        current_time = datetime.utcnow()
        submissions_24h = sum(1 for record in self.active_submissions.values()
                            if (current_time - record.created_at).total_seconds() < 86400)
        submissions_1h = sum(1 for record in self.active_submissions.values()
                           if (current_time - record.created_at).total_seconds() < 3600)
        
        return StatusStatistics(
            total_submissions=self.metrics['total_submissions'],
            status_counts=dict(self.metrics['status_counts']),
            priority_counts=dict(self.metrics['priority_counts']),
            type_counts=dict(self.metrics['type_counts']),
            average_processing_time=self.metrics['average_processing_time'],
            success_rate=success_rate,
            retry_rate=retry_rate,
            timeout_rate=timeout_rate,
            submissions_last_24h=submissions_24h,
            submissions_last_hour=submissions_1h
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get status tracker metrics"""
        return {
            **self.metrics,
            'active_submissions': len(self.active_submissions),
            'status_listeners': sum(len(listeners) for listeners in self.status_listeners.values())
        }


# Factory functions for easy setup
def create_status_tracker(database_path: str = "status_tracker.db",
                        default_timeout: int = 3600) -> StatusTracker:
    """Create status tracker instance"""
    return StatusTracker(database_path=database_path, default_timeout=default_timeout)


def create_status_query(submission_ids: Optional[List[str]] = None,
                       statuses: Optional[List[SubmissionStatus]] = None,
                       **kwargs) -> StatusQuery:
    """Create status query"""
    return StatusQuery(submission_ids=submission_ids, statuses=statuses, **kwargs)


async def track_submission_lifecycle(document_id: str,
                                   submission_type: SubmissionType,
                                   submitted_by: str,
                                   organization_id: str,
                                   tracker: Optional[StatusTracker] = None) -> str:
    """Track complete submission lifecycle"""
    if not tracker:
        tracker = create_status_tracker()
        await tracker.start()
    
    try:
        return await tracker.create_submission(
            document_id=document_id,
            submission_type=submission_type,
            submitted_by=submitted_by,
            organization_id=organization_id
        )
    finally:
        if not tracker.running:
            await tracker.stop()


def get_status_summary(tracker: StatusTracker) -> Dict[str, Any]:
    """Get status tracker summary"""
    metrics = tracker.get_metrics()
    
    return {
        'total_submissions': metrics['total_submissions'],
        'active_submissions': metrics['active_submissions'],
        'successful_submissions': metrics['successful_submissions'],
        'failed_submissions': metrics['failed_submissions'],
        'average_processing_time': metrics['average_processing_time'],
        'status_distribution': dict(metrics['status_counts']),
        'type_distribution': dict(metrics['type_counts'])
    }