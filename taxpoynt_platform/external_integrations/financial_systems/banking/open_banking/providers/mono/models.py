"""
Mono API Data Models
====================

Pydantic models for Mono API requests and responses.
Based on official Mono API documentation: https://docs.mono.co/

Key API Endpoints:
- POST /v2/accounts/initiate - Initiate account linking
- GET /v2/accounts/{account_id} - Get account information
- GET /v2/accounts/{account_id}/transactions - Get transactions
- GET /v2/accounts/{account_id}/identity - Get account holder identity
- GET /v2/accounts/{account_id}/income - Get income analysis

Architecture consistent with existing TaxPoynt patterns.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, validator
from enum import Enum


class MonoAccountType(str, Enum):
    """Mono account types from Nigerian banks"""
    SAVINGS = "SAVINGS"
    CURRENT = "CURRENT"
    DOMICILIARY = "DOMICILIARY"
    FIXED_DEPOSIT = "FIXED_DEPOSIT"


class MonoTransactionType(str, Enum):
    """Mono transaction types"""
    CREDIT = "credit"
    DEBIT = "debit"


class MonoConnectionStatus(str, Enum):
    """Account connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    REAUTHORIZATION_REQUIRED = "reauthorization_required"


class MonoWebhookEventType(str, Enum):
    """Mono webhook event types"""
    ACCOUNT_CONNECTED = "account.connected"
    ACCOUNT_UPDATED = "account.updated"
    TRANSACTION_CREATED = "transaction.created"
    TRANSACTION_UPDATED = "transaction.updated"
    ACCOUNT_REAUTHORIZATION_REQUIRED = "account.reauthorization_required"
    ACCOUNT_DISCONNECTED = "account.disconnected"


# Request Models
class MonoAccountLinkingRequest(BaseModel):
    """Request model for initiating account linking"""
    customer: Dict[str, str] = Field(..., description="Customer information")
    scope: str = Field(default="auth", description="Access scope")
    redirect_url: str = Field(..., description="HTTPS redirect URL")
    meta: Dict[str, str] = Field(..., description="Metadata including ref")
    
    @validator('redirect_url')
    def validate_redirect_url(cls, v):
        if not v.startswith('https://'):
            raise ValueError('Redirect URL must use HTTPS')
        return v
    
    @validator('meta')
    def validate_meta_ref(cls, v):
        if 'ref' not in v or len(v['ref']) < 10:
            raise ValueError('meta.ref is required and must be at least 10 characters')
        return v


class MonoTransactionQuery(BaseModel):
    """Query parameters for transaction requests"""
    start: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    narration: Optional[str] = Field(None, description="Transaction description filter")
    type: Optional[MonoTransactionType] = Field(None, description="Transaction type filter") 
    paginate: Optional[bool] = Field(True, description="Enable pagination")
    limit: Optional[int] = Field(50, description="Results per page", le=100)


# Response Models
class MonoAccountLinkingResponse(BaseModel):
    """Response from account linking initiation"""
    mono_url: str = Field(..., description="URL for customer account linking")
    customer: str = Field(..., description="Generated customer identifier")
    id: str = Field(..., description="Linking session identifier")
    is_multi: bool = Field(..., description="Multiple account connections allowed")


class MonoInstitution(BaseModel):
    """Bank institution information"""
    name: str = Field(..., description="Bank name")
    bankCode: str = Field(..., description="Nigerian bank code")
    type: str = Field(..., description="Institution type")


class MonoAccount(BaseModel):
    """Mono account information"""
    id: str = Field(..., description="Mono account identifier")
    name: str = Field(..., description="Account holder name")
    accountNumber: str = Field(..., description="Bank account number")
    type: MonoAccountType = Field(..., description="Account type")
    balance: int = Field(..., description="Account balance in kobo")
    currency: str = Field(default="NGN", description="Account currency")
    bvn: Optional[str] = Field(None, description="Bank Verification Number")
    institution: MonoInstitution = Field(..., description="Bank institution details")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class MonoTransaction(BaseModel):
    """Mono transaction record"""
    id: str = Field(..., description="Transaction identifier")
    amount: int = Field(..., description="Transaction amount in kobo")
    date: date = Field(..., description="Transaction date")
    narration: str = Field(..., description="Transaction description")
    type: MonoTransactionType = Field(..., description="Transaction type (credit/debit)")
    category: str = Field(..., description="Transaction category")
    balance: int = Field(..., description="Account balance after transaction in kobo")
    
    @property
    def amount_naira(self) -> Decimal:
        """Convert amount from kobo to naira"""
        return Decimal(self.amount) / 100
    
    @property
    def balance_naira(self) -> Decimal:
        """Convert balance from kobo to naira"""
        return Decimal(self.balance) / 100


class MonoTransactionsResponse(BaseModel):
    """Response containing transaction list"""
    paging: Dict[str, Any] = Field(..., description="Pagination information")
    data: List[MonoTransaction] = Field(..., description="Transaction records")


class MonoIdentity(BaseModel):
    """Account holder identity information"""
    full_name: str = Field(..., description="Account holder full name")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    gender: Optional[str] = Field(None, description="Gender")
    dob: Optional[date] = Field(None, description="Date of birth")
    bvn: Optional[str] = Field(None, description="Bank Verification Number")
    address: Optional[Dict[str, str]] = Field(None, description="Address information")


class MonoIncome(BaseModel):
    """Income analysis information"""
    type: str = Field(..., description="Income type")
    amount: int = Field(..., description="Income amount in kobo")
    period: str = Field(..., description="Income period")
    stability: str = Field(..., description="Income stability rating")
    data_availability: int = Field(..., description="Data availability months")
    
    @property
    def amount_naira(self) -> Decimal:
        """Convert amount from kobo to naira"""
        return Decimal(self.amount) / 100


# Webhook Models
class MonoWebhookPayload(BaseModel):
    """Mono webhook event payload"""
    event: MonoWebhookEventType = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    account: str = Field(..., description="Account identifier")
    timestamp: datetime = Field(..., description="Event timestamp")


class MonoWebhookVerification(BaseModel):
    """Webhook signature verification data"""
    signature: str = Field(..., description="Webhook signature")
    timestamp: str = Field(..., description="Request timestamp")
    payload: str = Field(..., description="Raw webhook payload")


# Error Models
class MonoError(BaseModel):
    """Mono API error response"""
    status: str = Field(..., description="Error status")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    type: Optional[str] = Field(None, description="Error type")


class MonoAccountConnectionStatus(BaseModel):
    """Account connection status information"""
    account_id: str = Field(..., description="Account identifier")
    status: MonoConnectionStatus = Field(..., description="Connection status")
    institution: MonoInstitution = Field(..., description="Bank institution")
    last_updated: datetime = Field(..., description="Last status update")
    reauth_required: bool = Field(default=False, description="Reauthorization required")


# Nigerian Banking Specific Models
class NigerianBankAccount(BaseModel):
    """Nigerian bank account with local context"""
    account_number: str = Field(..., description="10-digit account number")
    bank_code: str = Field(..., description="3-digit bank code")
    account_name: str = Field(..., description="Account holder name")
    bvn: Optional[str] = Field(None, description="11-digit BVN")
    phone_number: Optional[str] = Field(None, description="Registered phone number")
    
    @validator('account_number')
    def validate_account_number(cls, v):
        if len(v) != 10 or not v.isdigit():
            raise ValueError('Nigerian account number must be 10 digits')
        return v
    
    @validator('bank_code')
    def validate_bank_code(cls, v):
        if len(v) != 3 or not v.isdigit():
            raise ValueError('Nigerian bank code must be 3 digits')
        return v
    
    @validator('bvn')
    def validate_bvn(cls, v):
        if v is not None and (len(v) != 11 or not v.isdigit()):
            raise ValueError('BVN must be 11 digits')
        return v


class MonoBusinessAccount(BaseModel):
    """Business account information for invoice generation"""
    account_id: str = Field(..., description="Mono account ID")
    business_name: str = Field(..., description="Registered business name")
    business_email: str = Field(..., description="Business email address")
    business_phone: str = Field(..., description="Business phone number")
    business_address: Dict[str, str] = Field(..., description="Business address")
    tax_identification_number: Optional[str] = Field(None, description="TIN for FIRS")
    cac_registration_number: Optional[str] = Field(None, description="CAC registration")
    business_type: str = Field(..., description="Type of business")
    monthly_transaction_volume: Optional[int] = Field(None, description="Monthly volume in kobo")
    
    @validator('tax_identification_number')
    def validate_tin(cls, v):
        if v is not None and (len(v) != 11 or not v.isdigit()):
            raise ValueError('Nigerian TIN must be 11 digits')
        return v


# Export all models
__all__ = [
    # Enums
    "MonoAccountType", "MonoTransactionType", "MonoConnectionStatus", "MonoWebhookEventType",
    
    # Request Models
    "MonoAccountLinkingRequest", "MonoTransactionQuery",
    
    # Response Models  
    "MonoAccountLinkingResponse", "MonoInstitution", "MonoAccount", "MonoTransaction",
    "MonoTransactionsResponse", "MonoIdentity", "MonoIncome",
    
    # Webhook Models
    "MonoWebhookPayload", "MonoWebhookVerification",
    
    # Error Models
    "MonoError", "MonoAccountConnectionStatus",
    
    # Nigerian Specific Models
    "NigerianBankAccount", "MonoBusinessAccount"
]