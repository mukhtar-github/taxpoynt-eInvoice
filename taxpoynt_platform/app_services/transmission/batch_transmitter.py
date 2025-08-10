"""
Batch Document Transmission Service for APP Role

This service handles batch transmission of multiple documents to FIRS with:
- Batch processing optimization
- Parallel transmission handling
- Batch validation and verification
- Progress tracking and monitoring
- Error handling and recovery
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
from concurrent.futures import ThreadPoolExecutor
import aiofiles
import tempfile
import os

from .secure_transmitter import (
    SecureTransmitter, TransmissionRequest, TransmissionResult,
    TransmissionStatus, SecurityLevel, SecurityContext
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch transmission status"""
    PENDING = "pending"
    VALIDATING = "validating"
    PROCESSING = "processing"
    TRANSMITTING = "transmitting"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class BatchStrategy(Enum):
    """Batch processing strategy"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    OPTIMIZED = "optimized"
    PRIORITY_BASED = "priority_based"


@dataclass
class BatchItem:
    """Individual item in a batch"""
    item_id: str
    document_id: str
    document_type: str
    document_data: Dict[str, Any]
    destination_endpoint: str
    security_level: SecurityLevel = SecurityLevel.STANDARD
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_transmission_request(self) -> TransmissionRequest:
        """Convert to transmission request"""
        return TransmissionRequest(
            document_id=self.document_id,
            document_type=self.document_type,
            document_data=self.document_data,
            destination_endpoint=self.destination_endpoint,
            security_level=self.security_level,
            priority=self.priority,
            metadata=self.metadata
        )


@dataclass
class BatchRequest:
    """Batch transmission request"""
    batch_id: str
    batch_name: str
    items: List[BatchItem]
    strategy: BatchStrategy = BatchStrategy.OPTIMIZED
    max_parallel: int = 10
    batch_size: int = 100
    timeout: int = 300
    retry_failed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


@dataclass
class BatchItemResult:
    """Result of batch item transmission"""
    item_id: str
    document_id: str
    status: TransmissionStatus
    transmission_result: Optional[TransmissionResult] = None
    error_message: Optional[str] = None
    attempts: int = 0
    transmitted_at: Optional[datetime] = None


@dataclass
class BatchResult:
    """Batch transmission result"""
    batch_id: str
    batch_name: str
    status: BatchStatus
    total_items: int
    successful_items: int
    failed_items: int
    item_results: List[BatchItemResult]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchTransmitter:
    """
    Batch document transmission service for APP role
    
    Handles:
    - Batch processing optimization
    - Parallel transmission management
    - Progress tracking and monitoring
    - Error recovery and retry logic
    - Performance optimization
    """
    
    def __init__(self, 
                 secure_transmitter: SecureTransmitter,
                 max_concurrent_batches: int = 5,
                 max_batch_size: int = 1000,
                 default_timeout: int = 600):
        self.secure_transmitter = secure_transmitter
        self.max_concurrent_batches = max_concurrent_batches
        self.max_batch_size = max_batch_size
        self.default_timeout = default_timeout
        
        # Internal state
        self._active_batches: Dict[str, BatchRequest] = {}
        self._batch_results: Dict[str, BatchResult] = {}
        self._batch_semaphore = asyncio.Semaphore(max_concurrent_batches)
        self._executor = ThreadPoolExecutor(max_workers=10)
        
        # Metrics
        self.metrics = {
            'total_batches': 0,
            'successful_batches': 0,
            'failed_batches': 0,
            'total_items_processed': 0,
            'successful_items': 0,
            'failed_items': 0,
            'average_batch_size': 0.0,
            'average_processing_time': 0.0
        }
    
    async def start(self):
        """Start the batch transmitter service"""
        logger.info("Batch transmitter started")
    
    async def stop(self):
        """Stop the batch transmitter service"""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        logger.info("Batch transmitter stopped")
    
    async def transmit_batch(self, batch_request: BatchRequest) -> BatchResult:
        """
        Transmit a batch of documents to FIRS
        
        Args:
            batch_request: Batch transmission request
            
        Returns:
            BatchResult with transmission outcome
        """
        # Validate batch request
        if len(batch_request.items) > self.max_batch_size:
            raise ValueError(f"Batch size {len(batch_request.items)} exceeds maximum {self.max_batch_size}")
        
        # Acquire batch semaphore
        async with self._batch_semaphore:
            return await self._process_batch(batch_request)
    
    async def _process_batch(self, batch_request: BatchRequest) -> BatchResult:
        """Process a batch of documents"""
        batch_id = batch_request.batch_id
        start_time = time.time()
        
        # Initialize batch result
        batch_result = BatchResult(
            batch_id=batch_id,
            batch_name=batch_request.batch_name,
            status=BatchStatus.PENDING,
            total_items=len(batch_request.items),
            successful_items=0,
            failed_items=0,
            item_results=[],
            started_at=datetime.utcnow()
        )
        
        # Store active batch
        self._active_batches[batch_id] = batch_request
        
        try:
            # Step 1: Validate batch
            batch_result.status = BatchStatus.VALIDATING
            validation_result = await self._validate_batch(batch_request)
            
            if not validation_result['valid']:
                batch_result.status = BatchStatus.FAILED
                batch_result.error_message = validation_result['error']
                return batch_result
            
            # Step 2: Process batch based on strategy
            batch_result.status = BatchStatus.PROCESSING
            
            if batch_request.strategy == BatchStrategy.SEQUENTIAL:
                item_results = await self._process_sequential(batch_request)
            elif batch_request.strategy == BatchStrategy.PARALLEL:
                item_results = await self._process_parallel(batch_request)
            elif batch_request.strategy == BatchStrategy.PRIORITY_BASED:
                item_results = await self._process_priority_based(batch_request)
            else:  # OPTIMIZED
                item_results = await self._process_optimized(batch_request)
            
            # Step 3: Update batch result
            batch_result.item_results = item_results
            batch_result.successful_items = sum(
                1 for r in item_results 
                if r.status == TransmissionStatus.DELIVERED
            )
            batch_result.failed_items = len(item_results) - batch_result.successful_items
            
            # Determine batch status
            if batch_result.successful_items == batch_result.total_items:
                batch_result.status = BatchStatus.COMPLETED
            elif batch_result.successful_items > 0:
                batch_result.status = BatchStatus.PARTIALLY_COMPLETED
            else:
                batch_result.status = BatchStatus.FAILED
            
            # Update metrics
            self.metrics['total_batches'] += 1
            self.metrics['total_items_processed'] += batch_result.total_items
            self.metrics['successful_items'] += batch_result.successful_items
            self.metrics['failed_items'] += batch_result.failed_items
            
            if batch_result.status == BatchStatus.COMPLETED:
                self.metrics['successful_batches'] += 1
            else:
                self.metrics['failed_batches'] += 1
            
            # Update averages
            self._update_averages()
            
            logger.info(f"Batch {batch_id} completed: {batch_result.successful_items}/{batch_result.total_items} successful")
            
        except Exception as e:
            batch_result.status = BatchStatus.FAILED
            batch_result.error_message = str(e)
            
            self.metrics['total_batches'] += 1
            self.metrics['failed_batches'] += 1
            
            logger.error(f"Batch {batch_id} failed: {e}")
        
        finally:
            # Finalize batch result
            batch_result.completed_at = datetime.utcnow()
            batch_result.processing_time = time.time() - start_time
            
            # Store result and cleanup
            self._batch_results[batch_id] = batch_result
            if batch_id in self._active_batches:
                del self._active_batches[batch_id]
        
        return batch_result
    
    async def _validate_batch(self, batch_request: BatchRequest) -> Dict[str, Any]:
        """Validate batch request"""
        try:
            # Check batch size
            if len(batch_request.items) == 0:
                return {'valid': False, 'error': 'Batch cannot be empty'}
            
            # Check for duplicate document IDs
            document_ids = [item.document_id for item in batch_request.items]
            if len(document_ids) != len(set(document_ids)):
                return {'valid': False, 'error': 'Duplicate document IDs in batch'}
            
            # Validate each item
            for item in batch_request.items:
                if not item.document_id or not item.document_type:
                    return {'valid': False, 'error': f'Invalid item: {item.item_id}'}
                
                if not item.document_data:
                    return {'valid': False, 'error': f'Empty document data: {item.item_id}'}
            
            return {'valid': True}
            
        except Exception as e:
            return {'valid': False, 'error': f'Validation error: {str(e)}'}
    
    async def _process_sequential(self, batch_request: BatchRequest) -> List[BatchItemResult]:
        """Process batch items sequentially"""
        item_results = []
        
        for item in batch_request.items:
            result = await self._process_item(item, batch_request)
            item_results.append(result)
            
            # Log progress
            progress = len(item_results) / len(batch_request.items) * 100
            if len(item_results) % 10 == 0:
                logger.info(f"Batch {batch_request.batch_id} progress: {progress:.1f}%")
        
        return item_results
    
    async def _process_parallel(self, batch_request: BatchRequest) -> List[BatchItemResult]:
        """Process batch items in parallel"""
        # Create semaphore for parallel processing
        semaphore = asyncio.Semaphore(batch_request.max_parallel)
        
        async def process_with_semaphore(item):
            async with semaphore:
                return await self._process_item(item, batch_request)
        
        # Process all items in parallel
        tasks = [process_with_semaphore(item) for item in batch_request.items]
        item_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(item_results):
            if isinstance(result, Exception):
                final_results.append(BatchItemResult(
                    item_id=batch_request.items[i].item_id,
                    document_id=batch_request.items[i].document_id,
                    status=TransmissionStatus.FAILED,
                    error_message=str(result)
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def _process_priority_based(self, batch_request: BatchRequest) -> List[BatchItemResult]:
        """Process batch items based on priority"""
        # Sort items by priority (higher priority first)
        sorted_items = sorted(batch_request.items, key=lambda x: x.priority, reverse=True)
        
        item_results = []
        
        # Process high priority items first
        for item in sorted_items:
            result = await self._process_item(item, batch_request)
            item_results.append(result)
            
            # Log progress for high priority items
            if item.priority > 5:
                logger.info(f"High priority item {item.item_id} processed: {result.status.value}")
        
        return item_results
    
    async def _process_optimized(self, batch_request: BatchRequest) -> List[BatchItemResult]:
        """Process batch items with optimized strategy"""
        # Group items by destination endpoint and security level
        groups = {}
        
        for item in batch_request.items:
            key = (item.destination_endpoint, item.security_level)
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        # Process each group in parallel
        group_tasks = []
        for group_items in groups.values():
            if len(group_items) <= 5:
                # Small groups: process in parallel
                semaphore = asyncio.Semaphore(len(group_items))
                tasks = [self._process_item_with_semaphore(item, batch_request, semaphore) 
                        for item in group_items]
                group_tasks.append(asyncio.gather(*tasks))
            else:
                # Large groups: process sequentially
                group_tasks.append(self._process_group_sequential(group_items, batch_request))
        
        # Wait for all groups to complete
        group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
        
        # Flatten results
        item_results = []
        for group_result in group_results:
            if isinstance(group_result, Exception):
                logger.error(f"Group processing failed: {group_result}")
                continue
            
            if isinstance(group_result, list):
                item_results.extend(group_result)
        
        return item_results
    
    async def _process_item_with_semaphore(self, 
                                         item: BatchItem,
                                         batch_request: BatchRequest,
                                         semaphore: asyncio.Semaphore) -> BatchItemResult:
        """Process item with semaphore"""
        async with semaphore:
            return await self._process_item(item, batch_request)
    
    async def _process_group_sequential(self, 
                                      group_items: List[BatchItem],
                                      batch_request: BatchRequest) -> List[BatchItemResult]:
        """Process a group of items sequentially"""
        results = []
        for item in group_items:
            result = await self._process_item(item, batch_request)
            results.append(result)
        return results
    
    async def _process_item(self, 
                          item: BatchItem,
                          batch_request: BatchRequest) -> BatchItemResult:
        """Process a single batch item"""
        item_result = BatchItemResult(
            item_id=item.item_id,
            document_id=item.document_id,
            status=TransmissionStatus.PENDING
        )
        
        max_attempts = 3 if batch_request.retry_failed else 1
        
        for attempt in range(max_attempts):
            try:
                item_result.attempts = attempt + 1
                
                # Create transmission request
                transmission_request = item.to_transmission_request()
                
                # Transmit document
                transmission_result = await self.secure_transmitter.transmit_document(
                    transmission_request
                )
                
                # Update item result
                item_result.transmission_result = transmission_result
                item_result.status = transmission_result.status
                
                if transmission_result.status == TransmissionStatus.DELIVERED:
                    item_result.transmitted_at = datetime.utcnow()
                    break
                else:
                    item_result.error_message = transmission_result.error_message
                    
                    # Wait before retry
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                item_result.error_message = str(e)
                
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    item_result.status = TransmissionStatus.FAILED
        
        return item_result
    
    def _update_averages(self):
        """Update average metrics"""
        if self.metrics['total_batches'] > 0:
            self.metrics['average_batch_size'] = (
                self.metrics['total_items_processed'] / 
                self.metrics['total_batches']
            )
    
    async def get_batch_status(self, batch_id: str) -> Optional[BatchResult]:
        """Get batch status by ID"""
        return self._batch_results.get(batch_id)
    
    async def get_active_batches(self) -> List[BatchRequest]:
        """Get list of active batches"""
        return list(self._active_batches.values())
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """Cancel an active batch"""
        if batch_id in self._active_batches:
            del self._active_batches[batch_id]
            logger.info(f"Batch {batch_id} cancelled")
            return True
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get batch transmission metrics"""
        return {
            **self.metrics,
            'active_batches': len(self._active_batches),
            'completed_batches': len(self._batch_results),
            'batch_success_rate': (
                self.metrics['successful_batches'] / 
                max(self.metrics['total_batches'], 1)
            ) * 100,
            'item_success_rate': (
                self.metrics['successful_items'] / 
                max(self.metrics['total_items_processed'], 1)
            ) * 100
        }


# Factory functions for easy setup
def create_batch_item(item_id: str,
                     document_id: str,
                     document_type: str,
                     document_data: Dict[str, Any],
                     destination_endpoint: str,
                     security_level: SecurityLevel = SecurityLevel.STANDARD,
                     priority: int = 1) -> BatchItem:
    """Create batch item"""
    return BatchItem(
        item_id=item_id,
        document_id=document_id,
        document_type=document_type,
        document_data=document_data,
        destination_endpoint=destination_endpoint,
        security_level=security_level,
        priority=priority
    )


def create_batch_request(batch_name: str,
                        items: List[BatchItem],
                        strategy: BatchStrategy = BatchStrategy.OPTIMIZED,
                        max_parallel: int = 10) -> BatchRequest:
    """Create batch request"""
    return BatchRequest(
        batch_id=str(uuid.uuid4()),
        batch_name=batch_name,
        items=items,
        strategy=strategy,
        max_parallel=max_parallel
    )


async def create_batch_transmitter(secure_transmitter: SecureTransmitter) -> BatchTransmitter:
    """Create and start batch transmitter"""
    transmitter = BatchTransmitter(secure_transmitter)
    await transmitter.start()
    return transmitter