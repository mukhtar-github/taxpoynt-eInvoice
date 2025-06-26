"""
Payment gateway router for Nigerian payment integrations
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import json

from ...database import get_db
from ...core.auth import get_current_user
from ...models.user import User
from .paystack.connector import PaystackConnector
from .flutterwave.connector import FlutterwaveConnector
from .base import PaymentStatus, PaymentChannel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/payments", tags=["payments"])


def get_payment_connector(gateway: str, config: Dict[str, Any]):
    """Get payment connector instance"""
    if gateway == "paystack":
        return PaystackConnector(config)
    elif gateway == "flutterwave":
        return FlutterwaveConnector(config)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported payment gateway: {gateway}")


@router.post("/initialize")
async def initialize_payment(
    payment_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initialize payment transaction"""
    try:
        gateway = payment_data.get("gateway", "paystack")
        amount = payment_data.get("amount")
        email = payment_data.get("email") or current_user.email
        reference = payment_data.get("reference")
        metadata = payment_data.get("metadata", {})
        
        if not amount or not reference:
            raise HTTPException(status_code=400, detail="Amount and reference are required")
        
        # Get gateway configuration (in production, store in database/config)
        config = {
            "public_key": f"pk_test_example_{gateway}",
            "secret_key": f"sk_test_example_{gateway}",
            "webhook_secret": f"whsec_example_{gateway}"
        }
        
        connector = get_payment_connector(gateway, config)
        response = await connector.initialize_payment(amount, email, reference, metadata)
        
        # Log payment initialization
        logger.info(f"Payment initialized: {reference} for user {current_user.id}")
        
        return {
            "status": "success",
            "data": response.dict(),
            "gateway": gateway
        }
        
    except Exception as e:
        logger.error(f"Payment initialization failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify/{reference}")
async def verify_payment(
    reference: str,
    gateway: str = "paystack",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify payment transaction"""
    try:
        # Get gateway configuration
        config = {
            "public_key": f"pk_test_example_{gateway}",
            "secret_key": f"sk_test_example_{gateway}",
            "webhook_secret": f"whsec_example_{gateway}"
        }
        
        connector = get_payment_connector(gateway, config)
        response = await connector.verify_payment(reference)
        
        # Update invoice status if payment successful
        if response.status == PaymentStatus.SUCCESS:
            # TODO: Update invoice status in database
            logger.info(f"Payment verified successfully: {reference}")
        
        return {
            "status": "success",
            "data": response.dict(),
            "gateway": gateway
        }
        
    except Exception as e:
        logger.error(f"Payment verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/{gateway}")
async def handle_webhook(
    gateway: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle payment gateway webhooks"""
    try:
        # Get raw body for signature verification
        body = await request.body()
        headers = dict(request.headers)
        
        # Get gateway configuration
        config = {
            "public_key": f"pk_test_example_{gateway}",
            "secret_key": f"sk_test_example_{gateway}",
            "webhook_secret": f"whsec_example_{gateway}"
        }
        
        connector = get_payment_connector(gateway, config)
        
        # Verify webhook signature
        signature = headers.get("x-paystack-signature") or headers.get("verif-hash", "")
        if not connector.verify_webhook_signature(body.decode(), signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse webhook data
        webhook_data = json.loads(body.decode())
        
        # Process webhook in background
        background_tasks.add_task(process_webhook, connector, webhook_data, gateway, db)
        
        return {"status": "success", "message": "Webhook received"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_webhook(
    connector,
    webhook_data: Dict[str, Any],
    gateway: str,
    db: Session
):
    """Process webhook in background"""
    try:
        response = await connector.process_webhook(webhook_data)
        
        if response.processed and response.invoice_updated:
            # TODO: Update invoice in database
            logger.info(f"Invoice updated from {gateway} webhook: {response.reference}")
        
    except Exception as e:
        logger.error(f"Background webhook processing failed: {str(e)}")


@router.get("/channels/{gateway}")
async def get_payment_channels(
    gateway: str,
    current_user: User = Depends(get_current_user)
):
    """Get available payment channels for gateway"""
    try:
        config = {
            "public_key": f"pk_test_example_{gateway}",
            "secret_key": f"sk_test_example_{gateway}"
        }
        
        connector = get_payment_connector(gateway, config)
        channels = await connector.get_payment_channels()
        
        return {
            "status": "success",
            "channels": [channel.value for channel in channels],
            "gateway": gateway
        }
        
    except Exception as e:
        logger.error(f"Failed to get payment channels: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/banks/{gateway}")
async def get_supported_banks(
    gateway: str,
    current_user: User = Depends(get_current_user)
):
    """Get supported banks for gateway"""
    try:
        config = {
            "public_key": f"pk_test_example_{gateway}",
            "secret_key": f"sk_test_example_{gateway}"
        }
        
        connector = get_payment_connector(gateway, config)
        banks = await connector.get_supported_banks()
        
        return {
            "status": "success",
            "banks": banks,
            "gateway": gateway
        }
        
    except Exception as e:
        logger.error(f"Failed to get supported banks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfer/recipient")
async def create_transfer_recipient(
    recipient_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create transfer recipient (Paystack only)"""
    try:
        gateway = recipient_data.get("gateway", "paystack")
        
        if gateway != "paystack":
            raise HTTPException(status_code=400, detail="Transfer recipients only supported for Paystack")
        
        config = {
            "public_key": "pk_test_example_paystack",
            "secret_key": "sk_test_example_paystack"
        }
        
        connector = PaystackConnector(config)
        recipient = await connector.create_transfer_recipient(
            recipient_data["account_number"],
            recipient_data["bank_code"],
            recipient_data["name"]
        )
        
        return {
            "status": "success",
            "data": recipient
        }
        
    except Exception as e:
        logger.error(f"Failed to create transfer recipient: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/transfer")
async def initiate_transfer(
    transfer_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate transfer to recipient (Paystack only)"""
    try:
        gateway = transfer_data.get("gateway", "paystack")
        
        if gateway != "paystack":
            raise HTTPException(status_code=400, detail="Transfers only supported for Paystack")
        
        config = {
            "public_key": "pk_test_example_paystack",
            "secret_key": "sk_test_example_paystack"
        }
        
        connector = PaystackConnector(config)
        transfer = await connector.initiate_transfer(
            transfer_data["amount"],
            transfer_data["recipient_code"],
            transfer_data.get("reason", "Invoice payment")
        )
        
        return {
            "status": "success",
            "data": transfer
        }
        
    except Exception as e:
        logger.error(f"Failed to initiate transfer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))