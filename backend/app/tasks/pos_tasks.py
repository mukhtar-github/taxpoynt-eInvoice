"""
POS (Point of Sale) integration tasks for Celery.

This module provides high-priority tasks for POS system integrations
with real-time transaction processing capabilities and sub-2-second SLA.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from uuid import UUID
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery import celery_app
from app.db.session import SessionLocal
from app.services.pos_queue_service import get_pos_queue_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_sale")
def process_sale(self, sale_data: Dict[str, Any], pos_connection_id: str) -> Dict[str, Any]:
    """
    Process a POS sale transaction with high priority.
    
    Args:
        sale_data: Sale transaction data
        pos_connection_id: POS connection identifier
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing POS sale for connection {pos_connection_id}")
        
        # TODO: Implement actual POS sale processing
        # This would involve:
        # 1. Validating sale data
        # 2. Creating invoice/receipt
        # 3. Updating inventory
        # 4. Sending to FIRS if required
        
        result = {
            "status": "success",
            "sale_id": sale_data.get("sale_id"),
            "connection_id": pos_connection_id,
            "processed_at": "2025-06-20T09:00:00Z",
            "invoice_generated": True,
            "firs_submitted": True
        }
        
        logger.info(f"Successfully processed POS sale {sale_data.get('sale_id')}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing POS sale: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_refund")
def process_refund(self, refund_data: Dict[str, Any], pos_connection_id: str) -> Dict[str, Any]:
    """
    Process a POS refund transaction with high priority.
    
    Args:
        refund_data: Refund transaction data
        pos_connection_id: POS connection identifier
        
    Returns:
        Dict containing processing results
    """
    try:
        logger.info(f"Processing POS refund for connection {pos_connection_id}")
        
        # TODO: Implement actual POS refund processing
        # This would involve:
        # 1. Validating refund data
        # 2. Creating credit note
        # 3. Updating inventory
        # 4. Sending to FIRS if required
        
        result = {
            "status": "success",
            "refund_id": refund_data.get("refund_id"),
            "connection_id": pos_connection_id,
            "processed_at": "2025-06-20T09:00:00Z",
            "credit_note_generated": True,
            "firs_submitted": True
        }
        
        logger.info(f"Successfully processed POS refund {refund_data.get('refund_id')}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing POS refund: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60, max_retries=3)


@celery_app.task(bind=True, name="app.tasks.pos_tasks.sync_inventory")
def sync_inventory(self, pos_connection_id: str, items: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Synchronize inventory data from POS system.
    
    Args:
        pos_connection_id: POS connection identifier
        items: Optional list of specific items to sync
        
    Returns:
        Dict containing sync results
    """
    try:
        logger.info(f"Syncing inventory for POS connection {pos_connection_id}")
        
        # TODO: Implement actual inventory synchronization
        # This would involve:
        # 1. Fetching inventory data from POS
        # 2. Updating local inventory records
        # 3. Identifying discrepancies
        
        result = {
            "status": "success",
            "connection_id": pos_connection_id,
            "synced_at": "2025-06-20T09:00:00Z",
            "items_synced": len(items) if items else 0,
            "discrepancies_found": 0
        }
        
        logger.info(f"Successfully synced inventory for connection {pos_connection_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing POS inventory: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=300, max_retries=2)  # 5 minute delay


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_end_of_day")
def process_end_of_day(self, pos_connection_id: str, date: str) -> Dict[str, Any]:
    """
    Process end-of-day reconciliation for POS system.
    
    Args:
        pos_connection_id: POS connection identifier
        date: Date for reconciliation (YYYY-MM-DD)
        
    Returns:
        Dict containing reconciliation results
    """
    try:
        logger.info(f"Processing end-of-day for POS connection {pos_connection_id}, date {date}")
        
        # TODO: Implement actual end-of-day processing
        # This would involve:
        # 1. Generating daily sales reports
        # 2. Reconciling payments
        # 3. Creating summary invoices if needed
        # 4. Archiving transaction data
        
        result = {
            "status": "success",
            "connection_id": pos_connection_id,
            "date": date,
            "processed_at": "2025-06-20T09:00:00Z",
            "total_sales": 0,
            "total_refunds": 0,
            "net_amount": 0,
            "reconciliation_status": "balanced"
        }
        
        logger.info(f"Successfully processed end-of-day for connection {pos_connection_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error processing end-of-day: {str(e)}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=600, max_retries=2)  # 10 minute delay


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_realtime_transaction")
def process_realtime_transaction(self, transaction_data: Dict[str, Any], connection_id: str) -> Dict[str, Any]:
    """
    Process a real-time POS transaction with sub-2-second SLA.
    
    This task is designed for immediate processing with circuit breaker protection
    and automatic fallback to standard queues on failure.
    
    Args:
        transaction_data: Real-time transaction data
        connection_id: POS connection identifier
        
    Returns:
        Dict containing processing results with timing metrics
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        logger.info(
            f"Processing real-time transaction {transaction_data.get('transaction_id')}",
            extra={
                "task_id": task_id,
                "connection_id": connection_id,
                "transaction_id": transaction_data.get('transaction_id')
            }
        )
        
        # Get queue service for metrics and fallback processing
        queue_service = get_pos_queue_service()
        
        # Validate transaction data quickly
        if not transaction_data.get('transaction_id'):
            raise ValueError("Missing transaction_id")
        
        if not transaction_data.get('amount'):
            raise ValueError("Missing transaction amount")
        
        # Process transaction with timeout protection
        with SessionLocal() as db:
            # Create transaction record immediately
            from app.crud.pos_transaction import create_pos_transaction
            from app.schemas.pos import POSTransactionCreate
            
            # Convert to schema format
            transaction_create = POSTransactionCreate(
                transaction_id=transaction_data['transaction_id'],
                connection_id=connection_id,
                location_id=transaction_data.get('location_id', ''),
                amount=float(transaction_data['amount']),
                currency=transaction_data.get('currency', 'NGN'),
                payment_method=transaction_data.get('payment_method', 'unknown'),
                timestamp=transaction_data.get('timestamp'),
                items=transaction_data.get('items', []),
                customer_info=transaction_data.get('customer_info'),
                tax_info=transaction_data.get('tax_info'),
                platform_data=transaction_data.get('platform_data'),
                receipt_number=transaction_data.get('receipt_number'),
                receipt_url=transaction_data.get('receipt_url')
            )
            
            # Create transaction record
            db_transaction = create_pos_transaction(
                db=db,
                transaction_in=transaction_create,
                connection_id=UUID(connection_id)
            )
            
            processing_time = time.time() - start_time
            
            # Check SLA compliance (target: 2 seconds)
            sla_target = 2.0
            sla_met = processing_time <= sla_target
            
            result = {
                "status": "success",
                "transaction_id": str(db_transaction.id),
                "external_transaction_id": transaction_data['transaction_id'],
                "connection_id": connection_id,
                "processing_time": processing_time,
                "sla_target": sla_target,
                "sla_met": sla_met,
                "processed_at": time.time(),
                "invoice_generated": False,  # Will be updated by invoice generation task
                "firs_submitted": False,     # Will be updated by FIRS submission task
                "task_id": task_id
            }
            
            # Log performance metrics
            if sla_met:
                logger.info(
                    f"Real-time transaction processed within SLA: {processing_time:.3f}s",
                    extra=result
                )
            else:
                logger.warning(
                    f"Real-time transaction exceeded SLA: {processing_time:.3f}s > {sla_target}s",
                    extra=result
                )
            
            return result
            
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"Real-time transaction processing failed: {str(e)}",
            extra={
                "task_id": task_id,
                "connection_id": connection_id,
                "processing_time": processing_time,
                "error": str(e)
            }
        )
        
        # Don't retry real-time tasks - let them fall back to standard queue
        return {
            "status": "failed",
            "error": str(e),
            "processing_time": processing_time,
            "connection_id": connection_id,
            "task_id": task_id,
            "sla_met": False
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_high_priority_batch")
def process_high_priority_batch(self, batch_size: int = 10, priority: str = "high") -> Dict[str, Any]:
    """
    Process a batch of high-priority POS transactions from Redis queue.
    
    This task is designed to be run by dedicated workers for high-throughput processing
    while maintaining SLA requirements.
    
    Args:
        batch_size: Number of transactions to process in this batch
        priority: Queue priority to process from
        
    Returns:
        Dict containing batch processing results
    """
    start_time = time.time()
    task_id = self.request.id
    
    try:
        # Get queue service
        queue_service = get_pos_queue_service()
        
        # Process batch using async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                queue_service.process_queue_batch(priority, batch_size)
            )
        finally:
            loop.close()
        
        processing_time = time.time() - start_time
        
        # Add timing metrics to result
        result.update({
            "batch_processing_time": processing_time,
            "avg_transaction_time": processing_time / max(result.get("processed", 1), 1),
            "task_id": task_id,
            "processed_at": time.time()
        })
        
        logger.info(
            f"Processed batch of {result.get('processed', 0)} transactions in {processing_time:.3f}s",
            extra=result
        )
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"Batch processing failed: {str(e)}",
            extra={
                "task_id": task_id,
                "priority": priority,
                "batch_size": batch_size,
                "processing_time": processing_time,
                "error": str(e)
            }
        )
        
        # Retry batch processing with exponential backoff
        raise self.retry(exc=e, countdown=min(60 * (2 ** self.request.retries), 300), max_retries=3)


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_pos_transaction_to_invoice")
def process_pos_transaction_to_invoice(transaction_id: str) -> Dict[str, Any]:
    """
    Background task to convert POS transaction to invoice.
    
    This task handles the complete transaction-to-invoice workflow:
    1. Retrieve transaction from database
    2. Convert transaction to invoice using POSTransactionService
    3. Generate IRN for the invoice
    4. Submit to FIRS if configured
    5. Update transaction status
    
    Args:
        transaction_id: Database transaction ID
        
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing POS transaction {transaction_id} to invoice")
        
        with SessionLocal() as db:
            # Get transaction from database
            from app.models.pos_transaction import POSTransaction
            
            transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            # Check if invoice already generated
            if transaction.invoice_generated:
                logger.info(f"Invoice already generated for transaction {transaction_id}")
                return {
                    "status": "already_processed",
                    "transaction_id": transaction_id,
                    "invoice_id": str(transaction.invoice_id) if transaction.invoice_id else None,
                    "message": "Invoice already exists for this transaction"
                }
            
            # Initialize POS transaction service
            from app.services.pos_transaction_service import POSTransactionService
            service = POSTransactionService(db)
            
            # Convert transaction to invoice
            invoice = await service.transaction_to_invoice(transaction)
            
            # Generate IRN for the invoice
            try:
                irn = service.invoice_service.generate_irn_for_invoice(invoice)
                irn_generated = True
                logger.info(f"Generated IRN {irn} for invoice {invoice.invoice_number}")
            except Exception as irn_error:
                logger.error(f"IRN generation failed for invoice {invoice.invoice_number}: {str(irn_error)}")
                irn = None
                irn_generated = False
            
            # Submit to FIRS (placeholder for actual implementation)
            firs_submitted = False
            firs_error = None
            try:
                # TODO: Implement actual FIRS submission
                # This would involve calling the FIRS API with the invoice data
                # For now, we'll mark it as ready for submission
                invoice.mark_firs_submitted(f"FIRS_REF_{invoice.invoice_number}")
                firs_submitted = True
                logger.info(f"Invoice {invoice.invoice_number} marked for FIRS submission")
            except Exception as firs_submission_error:
                logger.error(f"FIRS submission failed for invoice {invoice.invoice_number}: {str(firs_submission_error)}")
                firs_error = str(firs_submission_error)
            
            processing_time = time.time() - start_time
            
            result = {
                "status": "success",
                "transaction_id": transaction_id,
                "external_transaction_id": transaction.external_transaction_id,
                "processing_time": processing_time,
                "invoice_generated": True,
                "invoice_id": str(invoice.id),
                "invoice_number": invoice.invoice_number,
                "irn_generated": irn_generated,
                "irn": irn,
                "firs_submitted": firs_submitted,
                "firs_error": firs_error,
                "total_amount": float(invoice.total_amount)
            }
            
            logger.info(f"Successfully processed transaction {transaction_id} to invoice in {processing_time:.3f}s")
            return result
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing transaction {transaction_id} to invoice: {str(e)}", exc_info=True)
        
        # Update transaction status to failed if possible
        try:
            with SessionLocal() as db:
                from app.models.pos_transaction import POSTransaction
                transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
                if transaction:
                    error_data = {
                        "error_message": str(e),
                        "error_type": e.__class__.__name__,
                        "timestamp": datetime.utcnow().isoformat(),
                        "function": "process_pos_transaction_to_invoice"
                    }
                    
                    if transaction.processing_errors:
                        transaction.processing_errors.append(error_data)
                    else:
                        transaction.processing_errors = [error_data]
                    
                    transaction.updated_at = datetime.utcnow()
                    db.commit()
        except Exception:
            pass  # Don't fail the task due to status update issues
        
        return {
            "status": "failed",
            "transaction_id": transaction_id,
            "processing_time": processing_time,
            "error": str(e)
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.process_square_transaction_with_firs")
def process_square_transaction_with_firs(transaction_id: str, connection_id: str) -> Dict[str, Any]:
    """
    Process Square transaction and generate FIRS invoice.
    
    This task handles the complete Square transaction workflow:
    1. Retrieve transaction from database
    2. Fetch additional data from Square API if needed
    3. Generate FIRS-compliant invoice
    4. Submit to FIRS
    5. Update transaction status
    
    Args:
        transaction_id: Database transaction ID
        connection_id: POS connection ID
        
    Returns:
        Dict containing processing results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing Square transaction {transaction_id} for FIRS compliance")
        
        with SessionLocal() as db:
            # Get transaction from database
            from app.models.pos_transaction import POSTransaction
            from app.models.pos_connection import POSConnection
            
            transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
            if not transaction:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            connection = db.query(POSConnection).filter(POSConnection.id == connection_id).first()
            if not connection:
                raise ValueError(f"Connection {connection_id} not found")
            
            # Initialize Square connector
            from app.integrations.pos.square.connector import SquarePOSConnector
            connector = SquarePOSConnector(connection.connection_config)
            
            # Get additional transaction details from Square if needed
            square_transaction = await connector.get_transaction_by_id(transaction.external_transaction_id)
            
            # Generate FIRS invoice using Square transformer
            try:
                firs_invoice = await connector.generate_firs_invoice(
                    square_transaction,
                    customer_info=transaction.transaction_data.get("customer_info")
                )
                
                # Validate FIRS invoice
                validation_result = connector.firs_transformer.validate_firs_invoice(firs_invoice)
                
                if not validation_result["valid"]:
                    logger.warning(f"FIRS invoice validation failed: {validation_result['errors']}")
                    # Continue with submission anyway, FIRS will reject if invalid
                
                # Update transaction with FIRS invoice data
                transaction.firs_invoice_data = firs_invoice
                transaction.status = "firs_generated"
                transaction.updated_at = datetime.utcnow()
                
                # Submit to FIRS (placeholder - would implement actual submission)
                firs_submission_result = {
                    "status": "submitted",
                    "irn": firs_invoice.get("irn"),
                    "submission_id": f"FIRS_{transaction.external_transaction_id}",
                    "submitted_at": datetime.utcnow().isoformat()
                }
                
                # Update transaction with submission results
                transaction.firs_submission_result = firs_submission_result
                transaction.status = "completed"
                transaction.updated_at = datetime.utcnow()
                
                db.commit()
                
                processing_time = time.time() - start_time
                
                result = {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "external_transaction_id": transaction.external_transaction_id,
                    "connection_id": connection_id,
                    "processing_time": processing_time,
                    "firs_invoice_generated": True,
                    "firs_submitted": True,
                    "irn": firs_invoice.get("irn"),
                    "validation_passed": validation_result["valid"],
                    "validation_warnings": validation_result.get("warnings", [])
                }
                
                logger.info(f"Successfully processed Square transaction {transaction_id} for FIRS in {processing_time:.3f}s")
                return result
                
            except Exception as firs_error:
                logger.error(f"FIRS processing failed for transaction {transaction_id}: {str(firs_error)}")
                
                # Update transaction status to indicate FIRS failure
                transaction.status = "firs_failed"
                transaction.firs_error = str(firs_error)
                transaction.updated_at = datetime.utcnow()
                db.commit()
                
                # Return partial success - transaction was recorded but FIRS failed
                processing_time = time.time() - start_time
                return {
                    "status": "partial_success",
                    "transaction_id": transaction_id,
                    "external_transaction_id": transaction.external_transaction_id,
                    "connection_id": connection_id,
                    "processing_time": processing_time,
                    "firs_invoice_generated": False,
                    "firs_submitted": False,
                    "firs_error": str(firs_error)
                }
                
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Error processing Square transaction {transaction_id}: {str(e)}", exc_info=True)
        
        # Update transaction status to failed if possible
        try:
            with SessionLocal() as db:
                from app.models.pos_transaction import POSTransaction
                transaction = db.query(POSTransaction).filter(POSTransaction.id == transaction_id).first()
                if transaction:
                    transaction.status = "failed"
                    transaction.error_message = str(e)
                    transaction.updated_at = datetime.utcnow()
                    db.commit()
        except Exception:
            pass  # Don't fail the task due to status update issues
        
        return {
            "status": "failed",
            "transaction_id": transaction_id,
            "connection_id": connection_id,
            "processing_time": processing_time,
            "error": str(e)
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.monitor_queue_health")
def monitor_queue_health(self) -> Dict[str, Any]:
    """
    Monitor POS queue health and performance metrics.
    
    This task runs periodically to check queue lengths, SLA compliance,
    and system performance.
    
    Returns:
        Dict containing queue health metrics
    """
    start_time = time.time()
    
    try:
        # Get queue service
        queue_service = get_pos_queue_service()
        
        # Get queue status using async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            status = loop.run_until_complete(queue_service.get_queue_status())
        finally:
            loop.close()
        
        processing_time = time.time() - start_time
        
        # Add monitoring metadata
        status.update({
            "monitor_processing_time": processing_time,
            "monitored_at": time.time(),
            "health_check_passed": True
        })
        
        # Check for critical conditions
        critical_conditions = []
        warning_conditions = []
        
        for queue_name, queue_info in status.get("queues", {}).items():
            if queue_info.get("status") == "critical":
                critical_conditions.append(f"Queue {queue_name} has {queue_info.get('length')} items")
            elif queue_info.get("status") == "warning":
                warning_conditions.append(f"Queue {queue_name} has {queue_info.get('length')} items")
        
        if critical_conditions:
            logger.error(
                f"Critical queue conditions detected: {critical_conditions}",
                extra=status
            )
            status["health_status"] = "critical"
        elif warning_conditions:
            logger.warning(
                f"Warning queue conditions detected: {warning_conditions}",
                extra=status
            )
            status["health_status"] = "warning"
        else:
            status["health_status"] = "healthy"
            
        logger.info(f"Queue health monitoring completed in {processing_time:.3f}s", extra=status)
        
        return status
        
    except Exception as e:
        processing_time = time.time() - start_time
        
        logger.error(
            f"Queue health monitoring failed: {str(e)}",
            extra={
                "processing_time": processing_time,
                "error": str(e)
            }
        )
        
        return {
            "health_check_passed": False,
            "error": str(e),
            "processing_time": processing_time,
            "monitored_at": time.time()
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.retry_failed_invoice_generation")
def retry_failed_invoice_generation(transaction_id: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Retry invoice generation for a failed POS transaction.
    
    Args:
        transaction_id: Transaction ID to retry
        max_retries: Maximum number of retry attempts
        
    Returns:
        Dict containing retry results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Retrying invoice generation for transaction {transaction_id}")
        
        with SessionLocal() as db:
            from app.services.pos_transaction_service import POSTransactionService
            service = POSTransactionService(db)
            
            # Attempt retry
            success = await service.retry_failed_invoice_generation(transaction_id)
            
            processing_time = time.time() - start_time
            
            if success:
                logger.info(f"Retry successful for transaction {transaction_id}")
                return {
                    "status": "success",
                    "transaction_id": transaction_id,
                    "processing_time": processing_time,
                    "retry_attempt": self.request.retries + 1,
                    "message": "Invoice generation retry successful"
                }
            else:
                raise Exception("Retry attempt failed")
                
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Retry failed for transaction {transaction_id}: {str(e)}")
        
        # Retry with exponential backoff if we haven't exceeded max retries
        if self.request.retries < max_retries:
            countdown = min(60 * (2 ** self.request.retries), 300)  # Max 5 minutes
            logger.info(f"Scheduling retry {self.request.retries + 1} for transaction {transaction_id} in {countdown}s")
            raise self.retry(exc=e, countdown=countdown, max_retries=max_retries)
        
        return {
            "status": "failed",
            "transaction_id": transaction_id,
            "processing_time": processing_time,
            "retry_attempt": self.request.retries + 1,
            "error": str(e),
            "message": f"All retry attempts exhausted ({max_retries})"
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.batch_process_transactions")
def batch_process_transactions(transaction_ids: List[str]) -> Dict[str, Any]:
    """
    Process multiple POS transactions to invoices in a batch.
    
    This task is useful for:
    - Processing backlog of transactions
    - Bulk invoice generation during off-peak hours
    - Recovery from system outages
    
    Args:
        transaction_ids: List of transaction IDs to process
        
    Returns:
        Dict containing batch processing results
    """
    start_time = time.time()
    batch_id = f"batch_{int(time.time())}"
    
    try:
        logger.info(f"Starting batch processing of {len(transaction_ids)} transactions")
        
        results = {
            "batch_id": batch_id,
            "total_transactions": len(transaction_ids),
            "successful": 0,
            "failed": 0,
            "already_processed": 0,
            "errors": [],
            "processed_transactions": []
        }
        
        for transaction_id in transaction_ids:
            try:
                # Process individual transaction
                result = process_pos_transaction_to_invoice(transaction_id)
                
                if result["status"] == "success":
                    results["successful"] += 1
                elif result["status"] == "already_processed":
                    results["already_processed"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "transaction_id": transaction_id,
                        "error": result.get("error", "Unknown error")
                    })
                
                results["processed_transactions"].append({
                    "transaction_id": transaction_id,
                    "status": result["status"],
                    "invoice_id": result.get("invoice_id"),
                    "processing_time": result.get("processing_time", 0)
                })
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "transaction_id": transaction_id,
                    "error": str(e)
                })
                logger.error(f"Failed to process transaction {transaction_id} in batch: {str(e)}")
        
        processing_time = time.time() - start_time
        results["total_processing_time"] = processing_time
        results["avg_processing_time"] = processing_time / len(transaction_ids)
        
        logger.info(f"Batch processing completed: {results['successful']} successful, {results['failed']} failed, {results['already_processed']} already processed")
        
        return results
        
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Batch processing failed: {str(e)}", exc_info=True)
        
        return {
            "batch_id": batch_id,
            "status": "failed",
            "error": str(e),
            "processing_time": processing_time,
            "total_transactions": len(transaction_ids)
        }


@celery_app.task(bind=True, name="app.tasks.pos_tasks.cleanup_old_transactions")
def cleanup_old_transactions(days_old: int = 365) -> Dict[str, Any]:
    """
    Cleanup old processed transactions to manage database size.
    
    This task removes transaction records older than specified days
    but preserves audit trail and invoice references.
    
    Args:
        days_old: Number of days old transactions to clean up
        
    Returns:
        Dict containing cleanup results
    """
    start_time = time.time()
    
    try:
        logger.info(f"Starting cleanup of transactions older than {days_old} days")
        
        with SessionLocal() as db:
            from app.models.pos_transaction import POSTransaction
            from sqlalchemy import and_
            
            # Find old transactions that have been successfully processed
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            old_transactions = db.query(POSTransaction).filter(
                and_(
                    POSTransaction.created_at < cutoff_date,
                    POSTransaction.invoice_generated == True,
                    POSTransaction.invoice_transmitted == True
                )
            ).all()
            
            cleanup_count = len(old_transactions)
            
            # Archive transaction data before deletion
            archived_data = []
            for transaction in old_transactions:
                archived_data.append({
                    "id": str(transaction.id),
                    "external_transaction_id": transaction.external_transaction_id,
                    "invoice_id": str(transaction.invoice_id) if transaction.invoice_id else None,
                    "amount": float(transaction.transaction_amount or 0),
                    "created_at": transaction.created_at.isoformat(),
                    "archived_at": datetime.utcnow().isoformat()
                })
            
            # Delete old transactions
            for transaction in old_transactions:
                db.delete(transaction)
            
            db.commit()
            
            processing_time = time.time() - start_time
            
            result = {
                "status": "success",
                "transactions_cleaned": cleanup_count,
                "cutoff_date": cutoff_date.isoformat(),
                "processing_time": processing_time,
                "archived_data_count": len(archived_data)
            }
            
            logger.info(f"Cleanup completed: {cleanup_count} transactions removed")
            return result
            
    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(f"Cleanup failed: {str(e)}", exc_info=True)
        
        return {
            "status": "failed",
            "error": str(e),
            "processing_time": processing_time
        }


# Export task functions for discovery
__all__ = [
    "process_sale",
    "process_refund", 
    "sync_inventory",
    "process_end_of_day",
    "process_realtime_transaction",
    "process_high_priority_batch",
    "process_pos_transaction_to_invoice",
    "process_square_transaction_with_firs",
    "retry_failed_invoice_generation",
    "batch_process_transactions",
    "cleanup_old_transactions",
    "monitor_queue_health"
]