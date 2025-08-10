"""
Delivery Status Tracking Service for APP Role

This service tracks delivery status and confirmations with:
- Real-time delivery monitoring
- Confirmation receipt tracking
- Delivery analytics and reporting
- Status update notifications
- Delivery audit trail
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Union, AsyncIterator, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import aiohttp
import sqlite3
import aiosqlite
from pathlib import Path

from .secure_transmitter import (
    SecureTransmitter, TransmissionRequest, TransmissionResult,
    TransmissionStatus, SecurityLevel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeliveryStatus(Enum):
    """Delivery status types"""
    PENDING = "pending"
    TRANSMITTED = "transmitted"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"
    FAILED = "failed"
    EXPIRED = "expired"


class TrackingEventType(Enum):
    """Tracking event types"""
    TRANSMISSION_STARTED = "transmission_started"
    TRANSMISSION_COMPLETED = "transmission_completed"
    DELIVERY_INITIATED = "delivery_initiated"
    DELIVERY_CONFIRMED = "delivery_confirmed"
    ACKNOWLEDGMENT_RECEIVED = "acknowledgment_received"
    CONFIRMATION_RECEIVED = "confirmation_received"
    DELIVERY_FAILED = "delivery_failed"
    DELIVERY_EXPIRED = "delivery_expired"
    STATUS_UPDATED = "status_updated"


@dataclass
class DeliveryTrackingRequest:
    """Delivery tracking request"""
    tracking_id: str
    document_id: str
    transmission_id: str
    destination_endpoint: str
    document_type: str
    recipient_info: Dict[str, Any]
    expected_delivery_time: Optional[datetime] = None
    delivery_timeout: int = 3600  # 1 hour
    requires_confirmation: bool = False
    callback_url: Optional[str] = None
    webhook_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TrackingEvent:
    """Delivery tracking event"""
    event_id: str
    tracking_id: str
    event_type: TrackingEventType
    timestamp: datetime
    status: DeliveryStatus
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = "delivery_tracker"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryRecord:
    """Delivery record with full tracking history"""
    tracking_id: str
    document_id: str
    transmission_id: str
    current_status: DeliveryStatus
    destination_endpoint: str
    document_type: str
    recipient_info: Dict[str, Any]
    events: List[TrackingEvent] = field(default_factory=list)
    started_at: Optional[datetime] = None
    transmitted_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    delivery_time: Optional[float] = None
    confirmation_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeliveryAnalytics:
    """Delivery analytics data"""
    total_deliveries: int = 0
    successful_deliveries: int = 0
    failed_deliveries: int = 0
    pending_deliveries: int = 0
    average_delivery_time: float = 0.0
    average_confirmation_time: float = 0.0
    delivery_success_rate: float = 0.0
    confirmation_rate: float = 0.0
    endpoint_performance: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    document_type_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    hourly_delivery_stats: Dict[str, int] = field(default_factory=dict)
    daily_delivery_stats: Dict[str, int] = field(default_factory=dict)


class DeliveryTracker:
    """
    Delivery status tracking service for APP role
    
    Handles:
    - Real-time delivery monitoring
    - Confirmation receipt tracking
    - Delivery analytics and reporting
    - Status update notifications
    - Delivery audit trail
    """
    
    def __init__(self, 
                 secure_transmitter: SecureTransmitter,
                 database_path: str = "delivery_tracking.db",
                 polling_interval: int = 30,
                 cleanup_interval: int = 3600,
                 retention_days: int = 30):
        self.secure_transmitter = secure_transmitter
        self.database_path = database_path
        self.polling_interval = polling_interval
        self.cleanup_interval = cleanup_interval
        self.retention_days = retention_days
        
        # Internal state
        self._active_tracking: Dict[str, DeliveryTrackingRequest] = {}
        self._delivery_records: Dict[str, DeliveryRecord] = {}
        self._tracking_callbacks: Dict[str, Callable] = {}
        
        # Database connection
        self._db_connection: Optional[aiosqlite.Connection] = None
        
        # Control flags
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._polling_tasks: List[asyncio.Task] = []
        
        # Event queues
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._notification_queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        
        # Metrics and analytics
        self.analytics = DeliveryAnalytics()
        self._performance_metrics = {
            'events_processed': 0,
            'notifications_sent': 0,
            'database_operations': 0,
            'polling_requests': 0,
            'callback_invocations': 0
        }
        
        # Rate limiting
        self._endpoint_rate_limits: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    async def start(self):
        """Start the delivery tracker service"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Initialize database
        await self._init_database()
        
        # Start background tasks
        self._monitor_task = asyncio.create_task(self._monitor_deliveries())
        self._cleanup_task = asyncio.create_task(self._cleanup_old_records())
        
        # Start processors
        self._polling_tasks = [
            asyncio.create_task(self._event_processor()),
            asyncio.create_task(self._notification_processor())
        ]
        
        logger.info("Delivery tracker started")
    
    async def stop(self):
        """Stop the delivery tracker service"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel background tasks
        if self._monitor_task:
            self._monitor_task.cancel()
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        for task in self._polling_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        all_tasks = [self._monitor_task, self._cleanup_task] + self._polling_tasks
        await asyncio.gather(*all_tasks, return_exceptions=True)
        
        # Close database
        if self._db_connection:
            await self._db_connection.close()
        
        logger.info("Delivery tracker stopped")
    
    async def _init_database(self):
        """Initialize SQLite database for tracking"""
        self._db_connection = await aiosqlite.connect(self.database_path)
        
        # Create tables
        await self._db_connection.execute('''
            CREATE TABLE IF NOT EXISTS delivery_records (
                tracking_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                transmission_id TEXT NOT NULL,
                current_status TEXT NOT NULL,
                destination_endpoint TEXT NOT NULL,
                document_type TEXT NOT NULL,
                recipient_info TEXT NOT NULL,
                started_at TIMESTAMP,
                transmitted_at TIMESTAMP,
                delivered_at TIMESTAMP,
                confirmed_at TIMESTAMP,
                failed_at TIMESTAMP,
                processing_time REAL,
                delivery_time REAL,
                confirmation_time REAL,
                error_message TEXT,
                metadata TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await self._db_connection.execute('''
            CREATE TABLE IF NOT EXISTS tracking_events (
                event_id TEXT PRIMARY KEY,
                tracking_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                status TEXT NOT NULL,
                details TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tracking_id) REFERENCES delivery_records (tracking_id)
            )
        ''')
        
        # Create indexes
        await self._db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_delivery_records_status 
            ON delivery_records(current_status)
        ''')
        
        await self._db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_delivery_records_document_id 
            ON delivery_records(document_id)
        ''')
        
        await self._db_connection.execute('''
            CREATE INDEX IF NOT EXISTS idx_tracking_events_tracking_id 
            ON tracking_events(tracking_id)
        ''')
        
        await self._db_connection.commit()
        
        logger.info("Database initialized")
    
    async def start_tracking(self, request: DeliveryTrackingRequest) -> str:
        """
        Start tracking a delivery
        
        Args:
            request: Delivery tracking request
            
        Returns:
            Tracking ID for monitoring
        """
        tracking_id = request.tracking_id
        
        # Create delivery record
        record = DeliveryRecord(
            tracking_id=tracking_id,
            document_id=request.document_id,
            transmission_id=request.transmission_id,
            current_status=DeliveryStatus.PENDING,
            destination_endpoint=request.destination_endpoint,
            document_type=request.document_type,
            recipient_info=request.recipient_info,
            started_at=datetime.utcnow(),
            metadata=request.metadata
        )
        
        # Store in memory and database
        self._delivery_records[tracking_id] = record
        self._active_tracking[tracking_id] = request
        
        await self._save_delivery_record(record)
        
        # Create initial event
        event = TrackingEvent(
            event_id=str(uuid.uuid4()),
            tracking_id=tracking_id,
            event_type=TrackingEventType.TRANSMISSION_STARTED,
            timestamp=datetime.utcnow(),
            status=DeliveryStatus.PENDING,
            details={
                'document_id': request.document_id,
                'destination': request.destination_endpoint,
                'document_type': request.document_type
            }
        )
        
        await self._add_tracking_event(event)
        
        # Update analytics
        self.analytics.total_deliveries += 1
        self.analytics.pending_deliveries += 1
        
        logger.info(f"Started tracking delivery {tracking_id} for document {request.document_id}")
        
        return tracking_id
    
    async def update_delivery_status(self, 
                                   tracking_id: str,
                                   status: DeliveryStatus,
                                   details: Optional[Dict[str, Any]] = None,
                                   error_message: Optional[str] = None):
        """
        Update delivery status
        
        Args:
            tracking_id: Tracking ID
            status: New delivery status
            details: Additional details
            error_message: Error message if failed
        """
        record = self._delivery_records.get(tracking_id)
        if not record:
            logger.warning(f"No tracking record found for {tracking_id}")
            return
        
        # Update record
        previous_status = record.current_status
        record.current_status = status
        
        current_time = datetime.utcnow()
        
        # Update timestamps based on status
        if status == DeliveryStatus.TRANSMITTED:
            record.transmitted_at = current_time
            if record.started_at:
                record.processing_time = (current_time - record.started_at).total_seconds()
        
        elif status == DeliveryStatus.DELIVERED:
            record.delivered_at = current_time
            if record.transmitted_at:
                record.delivery_time = (current_time - record.transmitted_at).total_seconds()
        
        elif status == DeliveryStatus.CONFIRMED:
            record.confirmed_at = current_time
            if record.delivered_at:
                record.confirmation_time = (current_time - record.delivered_at).total_seconds()
        
        elif status == DeliveryStatus.FAILED:
            record.failed_at = current_time
            record.error_message = error_message
        
        # Save to database
        await self._save_delivery_record(record)
        
        # Create tracking event
        event_type = self._get_event_type_for_status(status)
        event = TrackingEvent(
            event_id=str(uuid.uuid4()),
            tracking_id=tracking_id,
            event_type=event_type,
            timestamp=current_time,
            status=status,
            details=details or {},
            metadata={'previous_status': previous_status.value}
        )
        
        if error_message:
            event.details['error_message'] = error_message
        
        await self._add_tracking_event(event)
        
        # Update analytics
        await self._update_analytics(previous_status, status, record)
        
        # Send notifications
        await self._send_status_notification(tracking_id, status, details)
        
        logger.info(f"Updated delivery {tracking_id} status: {previous_status.value} -> {status.value}")
    
    def _get_event_type_for_status(self, status: DeliveryStatus) -> TrackingEventType:
        """Get event type for delivery status"""
        mapping = {
            DeliveryStatus.TRANSMITTED: TrackingEventType.TRANSMISSION_COMPLETED,
            DeliveryStatus.DELIVERED: TrackingEventType.DELIVERY_CONFIRMED,
            DeliveryStatus.ACKNOWLEDGED: TrackingEventType.ACKNOWLEDGMENT_RECEIVED,
            DeliveryStatus.CONFIRMED: TrackingEventType.CONFIRMATION_RECEIVED,
            DeliveryStatus.FAILED: TrackingEventType.DELIVERY_FAILED,
            DeliveryStatus.EXPIRED: TrackingEventType.DELIVERY_EXPIRED
        }
        return mapping.get(status, TrackingEventType.STATUS_UPDATED)
    
    async def _add_tracking_event(self, event: TrackingEvent):
        """Add tracking event to record and database"""
        # Add to record
        tracking_id = event.tracking_id
        if tracking_id in self._delivery_records:
            self._delivery_records[tracking_id].events.append(event)
        
        # Save to database
        await self._db_connection.execute('''
            INSERT INTO tracking_events (
                event_id, tracking_id, event_type, timestamp, status,
                details, source, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event.event_id, event.tracking_id, event.event_type.value,
            event.timestamp, event.status.value,
            json.dumps(event.details), event.source,
            json.dumps(event.metadata)
        ))
        
        await self._db_connection.commit()
        
        # Add to event queue for processing
        try:
            await self._event_queue.put(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")
        
        self._performance_metrics['events_processed'] += 1
    
    async def _save_delivery_record(self, record: DeliveryRecord):
        """Save delivery record to database"""
        await self._db_connection.execute('''
            INSERT OR REPLACE INTO delivery_records (
                tracking_id, document_id, transmission_id, current_status,
                destination_endpoint, document_type, recipient_info,
                started_at, transmitted_at, delivered_at, confirmed_at, failed_at,
                processing_time, delivery_time, confirmation_time,
                error_message, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.tracking_id, record.document_id, record.transmission_id,
            record.current_status.value, record.destination_endpoint,
            record.document_type, json.dumps(record.recipient_info),
            record.started_at, record.transmitted_at, record.delivered_at,
            record.confirmed_at, record.failed_at,
            record.processing_time, record.delivery_time, record.confirmation_time,
            record.error_message, json.dumps(record.metadata)
        ))
        
        await self._db_connection.commit()
        self._performance_metrics['database_operations'] += 1
    
    async def _update_analytics(self, 
                              previous_status: DeliveryStatus,
                              new_status: DeliveryStatus,
                              record: DeliveryRecord):
        """Update analytics based on status change"""
        # Update pending count
        if previous_status == DeliveryStatus.PENDING:
            self.analytics.pending_deliveries -= 1
        
        # Update success/failure counts
        if new_status == DeliveryStatus.DELIVERED:
            self.analytics.successful_deliveries += 1
            
            # Update delivery time average
            if record.delivery_time:
                current_avg = self.analytics.average_delivery_time
                total_successful = self.analytics.successful_deliveries
                self.analytics.average_delivery_time = (
                    (current_avg * (total_successful - 1) + record.delivery_time) / total_successful
                )
        
        elif new_status == DeliveryStatus.CONFIRMED:
            # Update confirmation time average
            if record.confirmation_time:
                confirmed_deliveries = sum(
                    1 for r in self._delivery_records.values() 
                    if r.current_status == DeliveryStatus.CONFIRMED
                )
                
                if confirmed_deliveries > 0:
                    current_avg = self.analytics.average_confirmation_time
                    self.analytics.average_confirmation_time = (
                        (current_avg * (confirmed_deliveries - 1) + record.confirmation_time) / confirmed_deliveries
                    )
        
        elif new_status == DeliveryStatus.FAILED:
            self.analytics.failed_deliveries += 1
        
        # Update success rate
        total_completed = self.analytics.successful_deliveries + self.analytics.failed_deliveries
        if total_completed > 0:
            self.analytics.delivery_success_rate = (
                self.analytics.successful_deliveries / total_completed
            ) * 100
        
        # Update confirmation rate
        if self.analytics.successful_deliveries > 0:
            confirmed_count = sum(
                1 for r in self._delivery_records.values() 
                if r.current_status == DeliveryStatus.CONFIRMED
            )
            self.analytics.confirmation_rate = (
                confirmed_count / self.analytics.successful_deliveries
            ) * 100
        
        # Update endpoint performance
        endpoint = record.destination_endpoint
        if endpoint not in self.analytics.endpoint_performance:
            self.analytics.endpoint_performance[endpoint] = {
                'total_deliveries': 0,
                'successful_deliveries': 0,
                'failed_deliveries': 0,
                'average_delivery_time': 0.0,
                'success_rate': 0.0
            }
        
        ep_stats = self.analytics.endpoint_performance[endpoint]
        
        if new_status == DeliveryStatus.DELIVERED:
            ep_stats['successful_deliveries'] += 1
            if record.delivery_time:
                total_successful = ep_stats['successful_deliveries']
                ep_stats['average_delivery_time'] = (
                    (ep_stats['average_delivery_time'] * (total_successful - 1) + record.delivery_time) / total_successful
                )
        elif new_status == DeliveryStatus.FAILED:
            ep_stats['failed_deliveries'] += 1
        
        # Update endpoint success rate
        ep_total = ep_stats['successful_deliveries'] + ep_stats['failed_deliveries']
        if ep_total > 0:
            ep_stats['success_rate'] = (ep_stats['successful_deliveries'] / ep_total) * 100
        
        # Update document type stats
        doc_type = record.document_type
        if doc_type not in self.analytics.document_type_stats:
            self.analytics.document_type_stats[doc_type] = {
                'total_deliveries': 0,
                'successful_deliveries': 0,
                'failed_deliveries': 0,
                'success_rate': 0.0
            }
        
        dt_stats = self.analytics.document_type_stats[doc_type]
        
        if new_status == DeliveryStatus.DELIVERED:
            dt_stats['successful_deliveries'] += 1
        elif new_status == DeliveryStatus.FAILED:
            dt_stats['failed_deliveries'] += 1
        
        # Update document type success rate
        dt_total = dt_stats['successful_deliveries'] + dt_stats['failed_deliveries']
        if dt_total > 0:
            dt_stats['success_rate'] = (dt_stats['successful_deliveries'] / dt_total) * 100
        
        # Update hourly/daily stats
        current_hour = datetime.utcnow().strftime('%Y-%m-%d %H:00')
        current_day = datetime.utcnow().strftime('%Y-%m-%d')
        
        if new_status in [DeliveryStatus.DELIVERED, DeliveryStatus.FAILED]:
            self.analytics.hourly_delivery_stats[current_hour] = (
                self.analytics.hourly_delivery_stats.get(current_hour, 0) + 1
            )
            self.analytics.daily_delivery_stats[current_day] = (
                self.analytics.daily_delivery_stats.get(current_day, 0) + 1
            )
    
    async def _send_status_notification(self, 
                                      tracking_id: str,
                                      status: DeliveryStatus,
                                      details: Optional[Dict[str, Any]] = None):
        """Send status notification"""
        request = self._active_tracking.get(tracking_id)
        if not request:
            return
        
        # Create notification
        notification = {
            'tracking_id': tracking_id,
            'document_id': request.document_id,
            'status': status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'details': details or {},
            'callback_url': request.callback_url,
            'webhook_url': request.webhook_url
        }
        
        # Add to notification queue
        try:
            await self._notification_queue.put(notification)
        except asyncio.QueueFull:
            logger.warning("Notification queue full, dropping notification")
    
    async def _event_processor(self):
        """Process tracking events"""
        while self._is_running:
            try:
                event = await self._event_queue.get()
                
                # Process event (placeholder for custom logic)
                await self._process_tracking_event(event)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                await asyncio.sleep(1)
    
    async def _process_tracking_event(self, event: TrackingEvent):
        """Process a tracking event"""
        # Invoke callbacks if registered
        if event.tracking_id in self._tracking_callbacks:
            try:
                callback = self._tracking_callbacks[event.tracking_id]
                await callback(event)
                self._performance_metrics['callback_invocations'] += 1
            except Exception as e:
                logger.error(f"Error invoking callback for {event.tracking_id}: {e}")
    
    async def _notification_processor(self):
        """Process notifications"""
        while self._is_running:
            try:
                notification = await self._notification_queue.get()
                
                # Send webhook if configured
                if notification.get('webhook_url'):
                    await self._send_webhook_notification(notification)
                
                # Send callback if configured
                if notification.get('callback_url'):
                    await self._send_callback_notification(notification)
                
                self._performance_metrics['notifications_sent'] += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notification: {e}")
                await asyncio.sleep(1)
    
    async def _send_webhook_notification(self, notification: Dict[str, Any]):
        """Send webhook notification"""
        try:
            webhook_url = notification['webhook_url']
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=notification,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Webhook sent for {notification['tracking_id']}")
                    else:
                        logger.warning(f"Webhook failed: {response.status}")
                        
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
    
    async def _send_callback_notification(self, notification: Dict[str, Any]):
        """Send callback notification"""
        # Placeholder for callback implementation
        logger.debug(f"Callback notification for {notification['tracking_id']}")
    
    async def _monitor_deliveries(self):
        """Monitor active deliveries"""
        while self._is_running:
            try:
                current_time = datetime.utcnow()
                
                # Check for expired deliveries
                for tracking_id, request in list(self._active_tracking.items()):
                    if request.expected_delivery_time and current_time > request.expected_delivery_time:
                        await self.update_delivery_status(
                            tracking_id,
                            DeliveryStatus.EXPIRED,
                            details={'reason': 'Expected delivery time exceeded'}
                        )
                        
                        # Remove from active tracking
                        del self._active_tracking[tracking_id]
                
                # Poll for status updates (placeholder)
                await self._poll_delivery_status()
                
                # Sleep until next monitoring cycle
                await asyncio.sleep(self.polling_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in delivery monitor: {e}")
                await asyncio.sleep(5)
    
    async def _poll_delivery_status(self):
        """Poll external systems for delivery status"""
        # This would typically query FIRS or other external systems
        # For now, we'll just track the polling activity
        self._performance_metrics['polling_requests'] += len(self._active_tracking)
    
    async def _cleanup_old_records(self):
        """Clean up old delivery records"""
        while self._is_running:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
                
                # Clean up database records
                await self._db_connection.execute('''
                    DELETE FROM tracking_events 
                    WHERE created_at < ?
                ''', (cutoff_date,))
                
                await self._db_connection.execute('''
                    DELETE FROM delivery_records 
                    WHERE created_at < ?
                ''', (cutoff_date,))
                
                await self._db_connection.commit()
                
                # Clean up memory records
                to_remove = []
                for tracking_id, record in self._delivery_records.items():
                    if record.started_at and record.started_at < cutoff_date:
                        to_remove.append(tracking_id)
                
                for tracking_id in to_remove:
                    del self._delivery_records[tracking_id]
                    if tracking_id in self._active_tracking:
                        del self._active_tracking[tracking_id]
                
                logger.info(f"Cleaned up {len(to_remove)} old delivery records")
                
                # Sleep until next cleanup
                await asyncio.sleep(self.cleanup_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)
    
    async def get_delivery_status(self, tracking_id: str) -> Optional[DeliveryRecord]:
        """Get delivery status by tracking ID"""
        return self._delivery_records.get(tracking_id)
    
    async def get_delivery_history(self, tracking_id: str) -> List[TrackingEvent]:
        """Get delivery history for tracking ID"""
        record = self._delivery_records.get(tracking_id)
        return record.events if record else []
    
    async def search_deliveries(self, 
                              document_id: Optional[str] = None,
                              status: Optional[DeliveryStatus] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None,
                              limit: int = 100) -> List[DeliveryRecord]:
        """Search delivery records"""
        query = "SELECT * FROM delivery_records WHERE 1=1"
        params = []
        
        if document_id:
            query += " AND document_id = ?"
            params.append(document_id)
        
        if status:
            query += " AND current_status = ?"
            params.append(status.value)
        
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = await self._db_connection.execute(query, params)
        rows = await cursor.fetchall()
        
        # Convert to DeliveryRecord objects
        records = []
        for row in rows:
            record = DeliveryRecord(
                tracking_id=row[0],
                document_id=row[1],
                transmission_id=row[2],
                current_status=DeliveryStatus(row[3]),
                destination_endpoint=row[4],
                document_type=row[5],
                recipient_info=json.loads(row[6]),
                started_at=datetime.fromisoformat(row[7]) if row[7] else None,
                transmitted_at=datetime.fromisoformat(row[8]) if row[8] else None,
                delivered_at=datetime.fromisoformat(row[9]) if row[9] else None,
                confirmed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                failed_at=datetime.fromisoformat(row[11]) if row[11] else None,
                processing_time=row[12],
                delivery_time=row[13],
                confirmation_time=row[14],
                error_message=row[15],
                metadata=json.loads(row[16])
            )
            records.append(record)
        
        return records
    
    def register_tracking_callback(self, tracking_id: str, callback: Callable):
        """Register callback for tracking events"""
        self._tracking_callbacks[tracking_id] = callback
    
    def unregister_tracking_callback(self, tracking_id: str):
        """Unregister tracking callback"""
        if tracking_id in self._tracking_callbacks:
            del self._tracking_callbacks[tracking_id]
    
    def get_analytics(self) -> DeliveryAnalytics:
        """Get delivery analytics"""
        return self.analytics
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self._performance_metrics,
            'active_tracking': len(self._active_tracking),
            'delivery_records': len(self._delivery_records),
            'event_queue_size': self._event_queue.qsize(),
            'notification_queue_size': self._notification_queue.qsize()
        }


# Factory functions for easy setup
def create_delivery_tracking_request(document_id: str,
                                   transmission_id: str,
                                   destination_endpoint: str,
                                   document_type: str,
                                   recipient_info: Dict[str, Any],
                                   requires_confirmation: bool = False) -> DeliveryTrackingRequest:
    """Create delivery tracking request"""
    return DeliveryTrackingRequest(
        tracking_id=str(uuid.uuid4()),
        document_id=document_id,
        transmission_id=transmission_id,
        destination_endpoint=destination_endpoint,
        document_type=document_type,
        recipient_info=recipient_info,
        requires_confirmation=requires_confirmation
    )


async def create_delivery_tracker(secure_transmitter: SecureTransmitter,
                                database_path: str = "delivery_tracking.db") -> DeliveryTracker:
    """Create and start delivery tracker"""
    tracker = DeliveryTracker(secure_transmitter, database_path)
    await tracker.start()
    return tracker