"""
Paystack Payment Models
======================

Data models for Paystack payment processor integration.
Optimized for Nigerian market and FIRS compliance.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from decimal import Decimal

from ....connector_framework.base_payment_connector import (
    PaymentTransaction, PaymentCustomer, PaymentRefund, 
    PaymentStatus, PaymentMethod, TransactionType
)


class PaystackTransaction(PaymentTransaction):
    """
    Paystack-specific transaction model.
    Extends base PaymentTransaction with Paystack-specific fields.
    """
    
    # Paystack specific identifiers
    paystack_id: Optional[int] = None
    access_code: Optional[str] = None
    authorization_url: Optional[str] = None
    
    # Paystack payment details
    plan_code: Optional[str] = None  # For subscription payments
    invoice_code: Optional[str] = None  # For invoice payments
    split_code: Optional[str] = None  # For split payments
    
    # Paystack authorization details
    authorization: Optional[Dict[str, Any]] = None
    
    # Paystack fees breakdown
    paystack_fee: Optional[Decimal] = None
    
    # Paystack metadata
    paystack_metadata: Optional[Dict[str, Any]] = None
    
    # Nigerian banking specifics
    requested_amount: Optional[Decimal] = None  # Original amount before fees
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackCustomer(PaymentCustomer):
    """
    Paystack customer model with Nigerian market specifics.
    """
    
    # Paystack specific fields
    paystack_customer_code: Optional[str] = None
    integration: Optional[int] = None
    domain: Optional[str] = None
    
    # Nigerian specific details
    dedicated_account: Optional[Dict[str, Any]] = None  # DVA details
    
    # Customer analytics
    transactions_count: int = 0
    transactions_value: Decimal = Decimal('0.0')
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackRefund(PaymentRefund):
    """
    Paystack refund model.
    """
    
    # Paystack specific fields
    paystack_refund_id: Optional[int] = None
    refund_reference: Optional[str] = None
    
    # Refund details
    merchant_note: Optional[str] = None
    customer_note: Optional[str] = None
    
    # Refund timeline
    expected_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackPlan(BaseModel):
    """
    Paystack subscription plan model.
    """
    
    plan_code: str
    name: str
    amount: Decimal
    interval: str  # daily, weekly, monthly, quarterly, annually
    currency: str = "NGN"
    
    # Plan details
    description: Optional[str] = None
    send_invoices: bool = True
    send_sms: bool = True
    
    # Plan status
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackSubscription(BaseModel):
    """
    Paystack subscription model.
    """
    
    subscription_code: str
    customer_code: str
    plan_code: str
    
    # Subscription status
    status: str  # active, cancelled, completed
    amount: Decimal
    currency: str = "NGN"
    
    # Subscription timeline
    created_at: Optional[datetime] = None
    next_payment_date: Optional[datetime] = None
    
    # Email tokens for invoice links
    email_token: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackTransfer(BaseModel):
    """
    Paystack transfer/payout model.
    """
    
    transfer_code: str
    reference: str
    amount: Decimal
    currency: str = "NGN"
    
    # Transfer recipient
    recipient_code: str
    recipient_name: Optional[str] = None
    recipient_account: Optional[str] = None
    recipient_bank: Optional[str] = None
    
    # Transfer status
    status: str  # pending, success, failed, reversed
    reason: Optional[str] = None
    
    # Transfer details
    source: str = "balance"  # balance, bank
    transfer_date: Optional[datetime] = None
    
    # Fees
    fee: Optional[Decimal] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackSettlement(BaseModel):
    """
    Paystack settlement model.
    """
    
    settlement_id: int
    domain: str
    
    # Settlement amounts
    total_amount: Decimal
    settled_amount: Decimal
    settlement_date: datetime
    
    # Settlement details
    status: str  # success, pending, processing
    currency: str = "NGN"
    
    # Bank details
    bank_code: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    
    # Transaction breakdown
    transaction_count: int = 0
    transactions: List[int] = []  # Transaction IDs included
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackDispute(BaseModel):
    """
    Paystack dispute/chargeback model.
    """
    
    dispute_id: int
    transaction_id: int
    transaction_reference: str
    
    # Dispute details
    category: str  # chargeback, complaint, inquiry
    status: str  # awaiting-merchant-feedback, under-review, merchant-accepted, resolved
    amount: Decimal
    currency: str = "NGN"
    
    # Dispute timeline
    created_at: datetime
    due_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Evidence
    evidence: Optional[Dict[str, Any]] = None
    upload_url: Optional[str] = None
    
    # Dispute reason
    reason: Optional[str] = None
    bin: Optional[str] = None
    last4: Optional[str] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class PaystackWebhookEvent(BaseModel):
    """
    Paystack webhook event model.
    """
    
    event: str  # transaction.success, charge.success, etc.
    data: Dict[str, Any]
    
    # Event metadata
    created_at: datetime
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaystackApiResponse(BaseModel):
    """
    Standard Paystack API response wrapper.
    """
    
    status: bool
    message: str
    data: Optional[Any] = None
    
    # Pagination (for list responses)
    meta: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaystackBulkCharge(BaseModel):
    """
    Paystack bulk charge model for batch processing.
    """
    
    batch_code: str
    status: str  # pending, processing, paused, complete, failed
    
    # Batch details
    total_charges: int
    pending_charges: int
    successful_charges: int
    failed_charges: int
    
    # Batch amounts
    total_amount: Decimal
    currency: str = "NGN"
    
    # Batch timeline
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }