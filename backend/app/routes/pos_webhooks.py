"""
Square POS webhook handler for real-time transaction processing.

This module provides webhook endpoints for Square events including:
- Payment updates and completion
- Order creation and modification
- Real-time POS transaction synchronization with FIRS e-invoicing
"""

import json
import hmac
import hashlib
import base64
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Header, Request, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.pos_connection import POSConnection
from app.models.pos_transaction import POSTransaction, TransactionStatus
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks/pos", tags=["pos-webhooks"])


def verify_square_webhook_signature(
    payload: bytes, 
    signature: str, 
    webhook_signature_key: str,
    notification_url: str = ""
) -> bool:
    """
    Verify Square webhook signature according to Square's specification.
    
    Square webhook verification process:
    1. Combine notification URL + request body
    2. Create HMAC-SHA1 hash using webhook signature key  
    3. Base64 encode the hash
    4. Compare with provided signature using constant-time comparison
    
    Args:
        payload: Raw request body bytes
        signature: Signature from X-Square-Signature header
        webhook_signature_key: Square webhook signature key
        notification_url: Webhook notification URL (optional)
        
    Returns:
        bool: True if signature is valid
    """
    if not webhook_signature_key:
        logger.warning("No Square webhook signature key configured, skipping verification")
        return True
    
    try:
        # Step 1: Combine notification URL with request body
        request_body = payload.decode('utf-8')
        string_to_sign = notification_url + request_body
        
        # Step 2: Create HMAC-SHA1 hash
        computed_hash = hmac.new(
            webhook_signature_key.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Step 3: Base64 encode the hash
        computed_signature = base64.b64encode(computed_hash).decode('utf-8')
        
        # Step 4: Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, computed_signature)
        
    except Exception as e:
        logger.error(f"Error verifying Square webhook signature: {str(e)}")
        return False


async def get_pos_connection_by_signature_key(db: Session, webhook_signature_key: str) -> Optional[POSConnection]:
    """
    Retrieve POS connection by webhook signature key.
    
    Args:
        db: Database session
        webhook_signature_key: Webhook signature key to match
        
    Returns:
        POSConnection instance or None
    """
    return db.query(POSConnection).filter(
        POSConnection.connection_config.op('->')('webhook_signature_key').astext == webhook_signature_key,
        POSConnection.connection_type == "square",
        POSConnection.is_active == True
    ).first()


async def handle_payment_update(
    event_data: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    db: Session,
    connection: POSConnection
) -> Dict[str, Any]:
    """
    Handle Square payment.updated webhook event.
    
    Args:
        event_data: Square webhook event data
        background_tasks: FastAPI background tasks
        db: Database session
        connection: POS connection configuration
        
    Returns:
        Dict with processing result
    """
    try:
        # Extract payment data from event
        payment_data = event_data.get("data", {}).get("object", {}).get("payment", {})
        payment_id = payment_data.get("id")
        order_id = payment_data.get("order_id")
        status = payment_data.get("status", "").upper()
        
        if not payment_id:
            logger.warning("Payment update event missing payment ID")
            return {"status": "error", "message": "Missing payment ID"}
        
        logger.info(f"Processing payment update: {payment_id}, status: {status}")
        
        # Only process completed payments
        if status != "COMPLETED":
            logger.info(f"Ignoring payment {payment_id} with status {status}")
            return {"status": "ignored", "reason": f"payment_status_{status.lower()}"}
        
        # Check if we already have this transaction
        existing_transaction = db.query(POSTransaction).filter(
            POSTransaction.external_transaction_id == payment_id,
            POSTransaction.connection_id == connection.id
        ).first()
        
        if existing_transaction:
            logger.info(f"Payment {payment_id} already processed")
            return {"status": "duplicate", "transaction_id": str(existing_transaction.id)}
        
        # Create new transaction record
        transaction = POSTransaction(
            connection_id=connection.id,
            external_transaction_id=payment_id,
            external_order_id=order_id,
            transaction_data=payment_data,
            status=TransactionStatus.PENDING,
            amount=payment_data.get("amount_money", {}).get("amount", 0) / 100,  # Convert from cents
            currency=payment_data.get("amount_money", {}).get("currency", "USD"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # Schedule background processing for invoice generation
        from app.tasks.pos_tasks import process_pos_transaction_to_invoice
        background_tasks.add_task(
            process_pos_transaction_to_invoice,
            str(transaction.id)
        )
        
        logger.info(f"Created transaction {transaction.id} for payment {payment_id}")
        
        return {
            "status": "success",
            "message": "Payment processed",
            "transaction_id": str(transaction.id),
            "background_task_scheduled": True
        }
        
    except Exception as e:
        logger.error(f"Error handling payment update: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def handle_order_created(
    event_data: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    db: Session,
    connection: POSConnection
) -> Dict[str, Any]:
    """
    Handle Square order.created webhook event.
    
    Args:
        event_data: Square webhook event data
        background_tasks: FastAPI background tasks
        db: Database session
        connection: POS connection configuration
        
    Returns:
        Dict with processing result
    """
    try:
        # Extract order data from event
        order_data = event_data.get("data", {}).get("object", {}).get("order", {})
        order_id = order_data.get("id")
        order_state = order_data.get("state", "").upper()
        
        if not order_id:
            logger.warning("Order created event missing order ID")
            return {"status": "error", "message": "Missing order ID"}
        
        logger.info(f"Processing order created: {order_id}, state: {order_state}")
        
        # Only process orders that are ready for payment or completed
        if order_state not in ["OPEN", "COMPLETED"]:
            logger.info(f"Ignoring order {order_id} with state {order_state}")
            return {"status": "ignored", "reason": f"order_state_{order_state.lower()}"}
        
        # Store order data for potential future use
        # For now, we'll wait for the payment.updated event to create transactions
        logger.info(f"Order {order_id} created and tracked for future payment processing")
        
        return {
            "status": "success",
            "message": "Order created and tracked",
            "order_id": order_id,
            "order_state": order_state
        }
        
    except Exception as e:
        logger.error(f"Error handling order created: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


async def handle_inventory_adjustment(
    event_data: Dict[str, Any], 
    background_tasks: BackgroundTasks,
    db: Session,
    connection: POSConnection
) -> Dict[str, Any]:
    """
    Handle Square inventory.adjustment webhook event.
    
    Args:
        event_data: Square webhook event data
        background_tasks: FastAPI background tasks  
        db: Database session
        connection: POS connection configuration
        
    Returns:
        Dict with processing result
    """
    try:
        # Extract inventory data from event
        inventory_data = event_data.get("data", {}).get("object", {})
        adjustment_id = inventory_data.get("id")
        
        logger.info(f"Processing inventory adjustment: {adjustment_id}")
        
        # Log inventory changes for audit purposes
        # In a full implementation, this would sync with inventory management systems
        logger.info(f"Inventory adjustment {adjustment_id} logged for audit")
        
        return {
            "status": "success",
            "message": "Inventory adjustment logged",
            "adjustment_id": adjustment_id
        }
        
    except Exception as e:
        logger.error(f"Error handling inventory adjustment: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@router.post("/square", status_code=200)
async def square_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_square_signature: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Handle Square webhook events with signature verification and event routing.
    
    Supports the following Square webhook events:
    - payment.updated: Process completed payments and generate FIRS invoices
    - order.created: Track order creation for future payment processing
    - inventory.adjustment: Log inventory changes for audit
    
    Security:
    - Verifies Square webhook signature using HMAC-SHA1
    - Validates connection configuration
    - Implements idempotency for duplicate events
    """
    # Get raw request body for signature verification
    payload = await request.body()
    payload_str = payload.decode("utf-8")
    
    # Parse webhook payload
    try:
        event_data = json.loads(payload_str)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Square webhook payload: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    # Extract event type and basic info
    event_type = event_data.get("type", "").lower()
    event_id = event_data.get("event_id")
    merchant_id = event_data.get("merchant_id")
    
    logger.info(f"Received Square webhook: {event_type}, event_id: {event_id}, merchant: {merchant_id}")
    
    # Early validation of required fields
    if not event_type:
        logger.error("Missing event type in Square webhook")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing event type"
        )
    
    # Since we don't know the connection yet, we'll need to find it by merchant_id or signature
    # For now, we'll extract signature key from the first Square connection
    # In production, you'd want to have a better way to identify the connection
    connection = db.query(POSConnection).filter(
        POSConnection.connection_type == "square",
        POSConnection.is_active == True
    ).first()
    
    if not connection:
        logger.error("No active Square POS connection found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active Square connection configured"
        )
    
    # Verify webhook signature
    if x_square_signature and connection.connection_config.get("webhook_signature_key"):
        webhook_signature_key = connection.connection_config["webhook_signature_key"]
        notification_url = connection.connection_config.get("webhook_url", "")
        
        if not verify_square_webhook_signature(payload, x_square_signature, webhook_signature_key, notification_url):
            logger.warning("Invalid Square webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        logger.info("Square webhook signature verified successfully")
    else:
        logger.warning("Square webhook signature verification skipped - no signature provided or configured")
    
    # Route event to appropriate handler
    result = {"event_type": event_type, "event_id": event_id, "status": "unknown"}
    
    try:
        if event_type == "payment.updated":
            result = await handle_payment_update(event_data, background_tasks, db, connection)
        elif event_type == "order.created":
            result = await handle_order_created(event_data, background_tasks, db, connection)
        elif event_type == "inventory.adjustment":
            result = await handle_inventory_adjustment(event_data, background_tasks, db, connection)
        else:
            logger.info(f"Unhandled Square webhook event type: {event_type}")
            result = {"status": "ignored", "reason": "unhandled_event_type"}
    
    except Exception as e:
        logger.error(f"Error processing Square webhook event {event_type}: {str(e)}", exc_info=True)
        result = {"status": "error", "message": str(e)}
    
    # Add common fields to response
    result.update({
        "event_type": event_type,
        "event_id": event_id,
        "merchant_id": merchant_id,
        "processed_at": datetime.utcnow().isoformat()
    })
    
    logger.info(f"Square webhook processing completed: {result['status']}")
    
    return result


@router.get("/square/test", status_code=200)
async def test_square_webhook():
    """
    Test endpoint to verify Square webhook route is accessible.
    """
    return {
        "status": "ok",
        "message": "Square webhook endpoint is accessible",
        "webhook_url": "/webhooks/pos/square",
        "supported_events": [
            "payment.updated",
            "order.created", 
            "inventory.adjustment"
        ]
    }