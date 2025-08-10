"""
Banking-to-FIRS Orchestrator
============================

Orchestrates the end-to-end flow from Open Banking transactions to FIRS submissions.
Uses existing APP services for FIRS communication and transmission.

Features:
- Automated invoice generation from banking transactions
- Integration with existing FIRS transmission services
- Comprehensive status tracking and monitoring
- Error handling and retry coordination
- Batch processing capabilities
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime, timedelta
import asyncio
import logging
import uuid

# Import existing APP services
from .....app_services.transmission import (
    SecureTransmitter, BatchTransmitter, TransmissionRequest, 
    BatchRequest, BatchItem, TransmissionStatus
)
from .....app_services.firs_communication import FIRSAPIClient
from .....app_services.validation import FIRSValidator

# Import banking integration components
from .auto_invoice_generator import AutoInvoiceGenerator, InvoiceGenerationResult
from .customer_matcher import CustomerMatcher
from .vat_calculator import VATCalculator
from .firs_formatter import FIRSFormatter, FormattingResult

# Import transaction processing components
from ..transaction_processing.processed_transaction import ProcessedTransaction
from ..transaction_processing.transaction_processor import TransactionProcessor

# Import core models
from .....core_platform.data_management import DatabaseAbstraction

logger = logging.getLogger(__name__)


class OrchestrationStatus(Enum):
    """Status of banking-to-FIRS orchestration."""
    PENDING = "pending"
    PROCESSING = "processing"
    INVOICE_GENERATED = "invoice_generated"
    FIRS_SUBMITTED = "firs_submitted"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class OrchestrationRequest:
    """Request for banking-to-FIRS orchestration."""
    request_id: str
    transactions: List[ProcessedTransaction]  # Now uses processed transactions
    priority: str = "normal"
    batch_processing: bool = False
    auto_submit: bool = True
    customer_validation: bool = True
    metadata: Dict[str, Any] = None


@dataclass
class OrchestrationResult:
    """Result of banking-to-FIRS orchestration."""
    request_id: str
    status: OrchestrationStatus
    total_transactions: int
    successful_invoices: int
    failed_invoices: int
    firs_submissions: int
    successful_submissions: int
    failed_submissions: int
    invoice_results: List[InvoiceGenerationResult] = None
    transmission_results: List[Any] = None
    errors: List[str] = None
    warnings: List[str] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = None


class BankingFIRSOrchestrator:
    """
    Orchestrates the complete flow from banking transactions to FIRS submissions.
    
    Coordinates between:
    - Banking transaction processing
    - Invoice generation automation
    - Existing APP services for FIRS submission
    """
    
    def __init__(
        self,
        transaction_processor: TransactionProcessor,  # Added transaction processor
        invoice_generator: AutoInvoiceGenerator,
        firs_formatter: FIRSFormatter,
        secure_transmitter: SecureTransmitter,
        batch_transmitter: BatchTransmitter,
        firs_client: FIRSAPIClient,
        validator: FIRSValidator,
        database: DatabaseAbstraction
    ):
        self.transaction_processor = transaction_processor
        self.invoice_generator = invoice_generator
        self.firs_formatter = firs_formatter
        self.secure_transmitter = secure_transmitter
        self.batch_transmitter = batch_transmitter
        self.firs_client = firs_client
        self.validator = validator
        self.database = database
        
        # Configuration
        self.max_concurrent_operations = 10
        self.batch_size = 50
        self.auto_retry_failures = True
        self.max_retry_attempts = 3
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_transactions_processed': 0,
            'total_invoices_generated': 0,
            'total_firs_submissions': 0,
            'average_processing_time': 0.0
        }
    
    async def orchestrate_banking_to_firs(
        self,
        request: OrchestrationRequest
    ) -> OrchestrationResult:
        """
        Orchestrate complete flow from banking transactions to FIRS submissions.
        
        Args:
            request: Orchestration request with transactions and configuration
            
        Returns:
            OrchestrationResult with complete processing details
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Starting banking-to-FIRS orchestration: {request.request_id}")
            logger.info(f"Processing {len(request.transactions)} transactions")
            
            # Initialize result
            result = OrchestrationResult(
                request_id=request.request_id,
                status=OrchestrationStatus.PROCESSING,
                total_transactions=len(request.transactions),
                successful_invoices=0,
                failed_invoices=0,
                firs_submissions=0,
                successful_submissions=0,
                failed_submissions=0,
                invoice_results=[],
                transmission_results=[],
                errors=[],
                warnings=[],
                metadata=request.metadata or {}
            )
            
            # Store request in database for tracking
            await self._store_orchestration_request(request, result)
            
            # Step 1: Generate invoices from processed transactions (already validated and enriched)
            logger.info("Step 1: Generating invoices from processed transactions")
            invoice_results = await self._generate_invoices_from_transactions(
                request.transactions, request.batch_processing
            )
            
            result.invoice_results = invoice_results
            result.successful_invoices = sum(1 for r in invoice_results if r.success)
            result.failed_invoices = len(invoice_results) - result.successful_invoices
            
            if result.successful_invoices == 0:
                result.status = OrchestrationStatus.FAILED
                result.errors.append("No invoices were successfully generated")
                return result
            
            result.status = OrchestrationStatus.INVOICE_GENERATED
            await self._update_orchestration_status(request.request_id, result)
            
            # Step 2: Submit invoices to FIRS (if auto_submit enabled)
            if request.auto_submit and result.successful_invoices > 0:
                logger.info("Step 2: Submitting invoices to FIRS")
                
                successful_invoices = [r for r in invoice_results if r.success]
                transmission_results = await self._submit_invoices_to_firs(
                    successful_invoices, request.batch_processing
                )
                
                result.transmission_results = transmission_results
                result.firs_submissions = len(transmission_results)
                result.successful_submissions = sum(
                    1 for r in transmission_results 
                    if r.status == TransmissionStatus.DELIVERED
                )
                result.failed_submissions = result.firs_submissions - result.successful_submissions
                
                result.status = OrchestrationStatus.FIRS_SUBMITTED
                await self._update_orchestration_status(request.request_id, result)
            
            # Determine final status
            if result.failed_invoices == 0 and result.failed_submissions == 0:
                result.status = OrchestrationStatus.COMPLETED
            elif result.successful_invoices > 0 or result.successful_submissions > 0:
                result.status = OrchestrationStatus.PARTIALLY_COMPLETED
            else:
                result.status = OrchestrationStatus.FAILED
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            result.processing_time = processing_time
            
            # Update final status
            await self._update_orchestration_status(request.request_id, result)
            
            # Update statistics
            self._update_orchestration_stats(result)
            
            logger.info(f"Orchestration completed: {request.request_id}")
            logger.info(f"Status: {result.status.value}, Processing time: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {request.request_id} - {e}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            error_result = OrchestrationResult(
                request_id=request.request_id,
                status=OrchestrationStatus.FAILED,
                total_transactions=len(request.transactions),
                successful_invoices=0,
                failed_invoices=0,
                firs_submissions=0,
                successful_submissions=0,
                failed_submissions=0,
                errors=[str(e)],
                processing_time=processing_time
            )
            
            await self._update_orchestration_status(request.request_id, error_result)
            self._update_orchestration_stats(error_result)
            
            return error_result
    
    async def orchestrate_batch_processing(
        self,
        transactions_batches: List[List[ProcessedTransaction]],
        batch_config: Optional[Dict[str, Any]] = None
    ) -> List[OrchestrationResult]:
        """
        Orchestrate multiple batches of transactions concurrently.
        
        Args:
            transactions_batches: List of transaction batches
            batch_config: Configuration for batch processing
            
        Returns:
            List of OrchestrationResult objects
        """
        logger.info(f"Starting batch orchestration for {len(transactions_batches)} batches")
        
        # Create orchestration requests for each batch
        requests = []
        for i, batch in enumerate(transactions_batches):
            request = OrchestrationRequest(
                request_id=f"batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{i}",
                transactions=batch,
                batch_processing=True,
                auto_submit=batch_config.get('auto_submit', True) if batch_config else True,
                metadata={'batch_index': i, 'total_batches': len(transactions_batches)}
            )
            requests.append(request)
        
        # Process batches concurrently with semaphore
        semaphore = asyncio.Semaphore(self.max_concurrent_operations)
        
        async def process_batch(request):
            async with semaphore:
                return await self.orchestrate_banking_to_firs(request)
        
        # Execute all batches
        results = await asyncio.gather(
            *[process_batch(req) for req in requests],
            return_exceptions=True
        )
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch {i} failed: {result}")
                error_result = OrchestrationResult(
                    request_id=requests[i].request_id,
                    status=OrchestrationStatus.FAILED,
                    total_transactions=len(requests[i].transactions),
                    successful_invoices=0,
                    failed_invoices=0,
                    firs_submissions=0,
                    successful_submissions=0,
                    failed_submissions=0,
                    errors=[str(result)]
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        # Log batch summary
        successful_batches = sum(1 for r in processed_results if r.status == OrchestrationStatus.COMPLETED)
        logger.info(f"Batch orchestration completed. Success: {successful_batches}/{len(transactions_batches)}")
        
        return processed_results
    
    async def _generate_invoices_from_transactions(
        self,
        transactions: List[ProcessedTransaction],
        batch_processing: bool = False
    ) -> List[InvoiceGenerationResult]:
        """Generate invoices from banking transactions."""
        
        if batch_processing and len(transactions) > 1:
            # Use batch generation
            from .auto_invoice_generator import InvoiceGenerationStrategy
            return await self.invoice_generator.generate_batch_invoices(
                transactions,
                strategy=InvoiceGenerationStrategy.DAILY_BATCH
            )
        else:
            # Generate individual invoices
            results = []
            for transaction in transactions:
                result = await self.invoice_generator.generate_from_transaction(transaction)
                results.append(result)
            return results
    
    async def _submit_invoices_to_firs(
        self,
        invoice_results: List[InvoiceGenerationResult],
        batch_processing: bool = False
    ) -> List[Any]:
        """Submit generated invoices to FIRS using existing APP services."""
        
        # Prepare invoices for FIRS submission
        invoices_to_submit = []
        formatting_results = []
        
        for invoice_result in invoice_results:
            if invoice_result.success and invoice_result.metadata.get('firs_data'):
                # Format invoice for FIRS using existing formatter
                firs_data = invoice_result.metadata['firs_data']
                invoices_to_submit.append(firs_data)
        
        if not invoices_to_submit:
            logger.warning("No invoices ready for FIRS submission")
            return []
        
        # Submit to FIRS using existing transmission services
        transmission_results = []
        
        if batch_processing and len(invoices_to_submit) > 1:
            # Use batch transmission
            batch_items = []
            for i, invoice_data in enumerate(invoices_to_submit):
                batch_item = BatchItem(
                    item_id=f"invoice_{i}",
                    document_type="INVOICE",
                    document_data=invoice_data,
                    priority="normal"
                )
                batch_items.append(batch_item)
            
            batch_request = BatchRequest(
                batch_id=f"invoice_batch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                batch_name="Banking Invoice Batch",
                items=batch_items,
                priority="normal"
            )
            
            batch_result = await self.batch_transmitter.transmit_batch(batch_request)
            transmission_results.extend(batch_result.item_results)
            
        else:
            # Use individual transmission
            for i, invoice_data in enumerate(invoices_to_submit):
                transmission_request = TransmissionRequest(
                    document_id=f"banking_invoice_{i}_{datetime.utcnow().timestamp()}",
                    document_type="INVOICE",
                    document_data=invoice_data,
                    destination_endpoint="/api/v1/documents/submit",
                    priority="normal"
                )
                
                result = await self.secure_transmitter.transmit(transmission_request)
                transmission_results.append(result)
        
        return transmission_results
    
    async def _store_orchestration_request(
        self,
        request: OrchestrationRequest,
        result: OrchestrationResult
    ):
        """Store orchestration request in database."""
        
        try:
            await self.database.execute(
                """
                INSERT INTO banking_firs_orchestration 
                (request_id, status, total_transactions, created_at, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    request.request_id,
                    result.status.value,
                    result.total_transactions,
                    datetime.utcnow(),
                    str(request.metadata) if request.metadata else None
                )
            )
        except Exception as e:
            logger.error(f"Failed to store orchestration request: {e}")
    
    async def _update_orchestration_status(
        self,
        request_id: str,
        result: OrchestrationResult
    ):
        """Update orchestration status in database."""
        
        try:
            await self.database.execute(
                """
                UPDATE banking_firs_orchestration 
                SET status = ?, successful_invoices = ?, failed_invoices = ?,
                    firs_submissions = ?, successful_submissions = ?, failed_submissions = ?,
                    processing_time = ?, updated_at = ?
                WHERE request_id = ?
                """,
                (
                    result.status.value,
                    result.successful_invoices,
                    result.failed_invoices,
                    result.firs_submissions,
                    result.successful_submissions,
                    result.failed_submissions,
                    result.processing_time,
                    datetime.utcnow(),
                    request_id
                )
            )
        except Exception as e:
            logger.error(f"Failed to update orchestration status: {e}")
    
    def _update_orchestration_stats(self, result: OrchestrationResult):
        """Update orchestration statistics."""
        
        self.stats['total_requests'] += 1
        
        if result.status == OrchestrationStatus.COMPLETED:
            self.stats['successful_requests'] += 1
        elif result.status == OrchestrationStatus.FAILED:
            self.stats['failed_requests'] += 1
        
        self.stats['total_transactions_processed'] += result.total_transactions
        self.stats['total_invoices_generated'] += result.successful_invoices
        self.stats['total_firs_submissions'] += result.successful_submissions
        
        # Update average processing time
        if result.processing_time:
            current_avg = self.stats['average_processing_time']
            total_requests = self.stats['total_requests']
            self.stats['average_processing_time'] = (
                (current_avg * (total_requests - 1) + result.processing_time) / total_requests
            )
    
    async def get_orchestration_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of an orchestration request."""
        
        try:
            result = await self.database.fetch_one(
                """
                SELECT * FROM banking_firs_orchestration 
                WHERE request_id = ?
                """,
                (request_id,)
            )
            
            if result:
                return dict(result)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get orchestration status: {e}")
            return None
    
    async def retry_failed_orchestration(
        self,
        request_id: str,
        retry_config: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """Retry a failed orchestration request."""
        
        # Get original request details
        status = await self.get_orchestration_status(request_id)
        if not status:
            raise ValueError(f"Orchestration request not found: {request_id}")
        
        # Create retry request
        retry_request = OrchestrationRequest(
            request_id=f"{request_id}_retry_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            transactions=[],  # Would need to fetch from storage
            priority="high",  # Higher priority for retries
            batch_processing=retry_config.get('batch_processing', True) if retry_config else True,
            auto_submit=retry_config.get('auto_submit', True) if retry_config else True,
            metadata={'original_request_id': request_id, 'retry_attempt': True}
        )
        
        # Execute retry
        return await self.orchestrate_banking_to_firs(retry_request)
    
    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """Get orchestration statistics."""
        
        stats = self.stats.copy()
        
        # Calculate additional metrics
        if stats['total_requests'] > 0:
            stats['success_rate'] = stats['successful_requests'] / stats['total_requests']
            stats['failure_rate'] = stats['failed_requests'] / stats['total_requests']
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        if stats['total_transactions_processed'] > 0:
            stats['invoice_generation_rate'] = (
                stats['total_invoices_generated'] / stats['total_transactions_processed']
            )
        else:
            stats['invoice_generation_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset orchestration statistics."""
        
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_transactions_processed': 0,
            'total_invoices_generated': 0,
            'total_firs_submissions': 0,
            'average_processing_time': 0.0
        }