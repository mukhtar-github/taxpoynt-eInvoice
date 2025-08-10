"""
Stitch Open Banking Models
==========================

Enterprise-grade data models for Stitch API responses and requests.
These models support bulk operations, enhanced compliance features,
and enterprise-specific data structures.

Key Features:
- Enterprise account hierarchies and groupings
- Bulk operation result tracking
- Enhanced compliance metadata
- Audit trail support
- Multi-currency support for international operations
- Advanced risk scoring and categorization
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import uuid


class StitchAccountType(str, Enum):
    """Enhanced account types for enterprise customers"""
    CURRENT = "current"
    SAVINGS = "savings"
    FIXED_DEPOSIT = "fixed_deposit"
    FOREIGN_CURRENCY = "foreign_currency"
    ESCROW = "escrow"
    TRUST = "trust"
    CORPORATE_CURRENT = "corporate_current"
    CORPORATE_SAVINGS = "corporate_savings"
    TREASURY = "treasury"
    INVESTMENT = "investment"


class StitchTransactionType(str, Enum):
    """Enhanced transaction types for enterprise operations"""
    CREDIT = "credit"
    DEBIT = "debit"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    SALARY = "salary"
    TAX_PAYMENT = "tax_payment"
    LOAN_PAYMENT = "loan_payment"
    INVESTMENT = "investment"
    FOREX = "forex"
    BULK_PAYMENT = "bulk_payment"
    ESCROW_RELEASE = "escrow_release"


class StitchTransactionStatus(str, Enum):
    """Transaction processing status"""
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"
    REVERSED = "reversed"
    DISPUTED = "disputed"
    UNDER_REVIEW = "under_review"


class StitchComplianceLevel(str, Enum):
    """Compliance risk levels for transactions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StitchBulkOperationStatus(str, Enum):
    """Status of bulk operations"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


@dataclass
class StitchComplianceMetadata:
    """Enhanced compliance metadata for enterprise customers"""
    risk_level: StitchComplianceLevel
    aml_status: str
    kyc_verified: bool
    sanctions_check: bool
    pep_status: bool  # Politically Exposed Person
    compliance_score: float
    last_reviewed: datetime
    reviewer_id: Optional[str] = None
    compliance_notes: Optional[str] = None
    regulatory_flags: List[str] = None

    def __post_init__(self):
        if self.regulatory_flags is None:
            self.regulatory_flags = []


@dataclass
class StitchAuditTrail:
    """Comprehensive audit trail for enterprise compliance"""
    event_id: str
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    api_endpoint: str
    request_id: str
    response_status: int
    data_accessed: List[str]
    compliance_flags: List[str]
    retention_period: int  # days

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class StitchAccount:
    """Enhanced enterprise account model"""
    id: str
    name: str
    account_number: str
    bank_code: str
    bank_name: str
    account_type: StitchAccountType
    currency: str
    balance: Decimal
    available_balance: Decimal
    account_holder_name: str
    bvn: Optional[str] = None
    
    # Enterprise-specific fields
    account_group_id: Optional[str] = None
    parent_account_id: Optional[str] = None
    subsidiary_accounts: List[str] = None
    account_manager: Optional[str] = None
    account_tier: str = "standard"
    multi_currency_enabled: bool = False
    automated_sweeping_enabled: bool = False
    
    # Compliance and audit
    compliance_metadata: Optional[StitchComplianceMetadata] = None
    last_activity: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Risk and limits
    daily_transaction_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    risk_score: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.subsidiary_accounts is None:
            self.subsidiary_accounts = []
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'StitchAccount':
        """Create StitchAccount from API response"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', ''),
            account_number=data.get('accountNumber', ''),
            bank_code=data.get('bankCode', ''),
            bank_name=data.get('bankName', ''),
            account_type=StitchAccountType(data.get('accountType', 'current')),
            currency=data.get('currency', 'NGN'),
            balance=Decimal(str(data.get('balance', '0'))),
            available_balance=Decimal(str(data.get('availableBalance', '0'))),
            account_holder_name=data.get('accountHolderName', ''),
            bvn=data.get('bvn'),
            account_group_id=data.get('accountGroupId'),
            parent_account_id=data.get('parentAccountId'),
            subsidiary_accounts=data.get('subsidiaryAccounts', []),
            account_manager=data.get('accountManager'),
            account_tier=data.get('accountTier', 'standard'),
            multi_currency_enabled=data.get('multiCurrencyEnabled', False),
            automated_sweeping_enabled=data.get('automatedSweepingEnabled', False),
            last_activity=datetime.fromisoformat(data['lastActivity']) if data.get('lastActivity') else None,
            created_at=datetime.fromisoformat(data['createdAt']) if data.get('createdAt') else None,
            updated_at=datetime.fromisoformat(data['updatedAt']) if data.get('updatedAt') else None,
            daily_transaction_limit=Decimal(str(data['dailyTransactionLimit'])) if data.get('dailyTransactionLimit') else None,
            monthly_transaction_limit=Decimal(str(data['monthlyTransactionLimit'])) if data.get('monthlyTransactionLimit') else None,
            risk_score=float(data.get('riskScore', 0.0)),
            metadata=data.get('metadata', {})
        )


@dataclass
class StitchTransaction:
    """Enhanced enterprise transaction model"""
    id: str
    account_id: str
    amount: Decimal
    currency: str
    transaction_type: StitchTransactionType
    status: StitchTransactionStatus
    date: datetime
    description: str
    reference: str
    
    # Enhanced transaction details
    counterparty_account: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_bank_code: Optional[str] = None
    
    # Enterprise features
    batch_id: Optional[str] = None
    bulk_operation_id: Optional[str] = None
    transaction_category: Optional[str] = None
    business_purpose: Optional[str] = None
    cost_center: Optional[str] = None
    department: Optional[str] = None
    project_code: Optional[str] = None
    
    # Compliance and risk
    compliance_metadata: Optional[StitchComplianceMetadata] = None
    audit_trail: List[StitchAuditTrail] = None
    risk_flags: List[str] = None
    
    # Processing metadata
    processed_at: Optional[datetime] = None
    processing_fee: Optional[Decimal] = None
    exchange_rate: Optional[Decimal] = None
    original_currency: Optional[str] = None
    original_amount: Optional[Decimal] = None
    
    # Additional fields
    balance_after: Optional[Decimal] = None
    balance_before: Optional[Decimal] = None
    transaction_code: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []
        if self.risk_flags is None:
            self.risk_flags = []
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> 'StitchTransaction':
        """Create StitchTransaction from API response"""
        return cls(
            id=data.get('id', ''),
            account_id=data.get('accountId', ''),
            amount=Decimal(str(data.get('amount', '0'))),
            currency=data.get('currency', 'NGN'),
            transaction_type=StitchTransactionType(data.get('type', 'debit')),
            status=StitchTransactionStatus(data.get('status', 'processed')),
            date=datetime.fromisoformat(data.get('date', datetime.now().isoformat())),
            description=data.get('description', ''),
            reference=data.get('reference', ''),
            counterparty_account=data.get('counterpartyAccount'),
            counterparty_name=data.get('counterpartyName'),
            counterparty_bank=data.get('counterpartyBank'),
            counterparty_bank_code=data.get('counterpartyBankCode'),
            batch_id=data.get('batchId'),
            bulk_operation_id=data.get('bulkOperationId'),
            transaction_category=data.get('transactionCategory'),
            business_purpose=data.get('businessPurpose'),
            cost_center=data.get('costCenter'),
            department=data.get('department'),
            project_code=data.get('projectCode'),
            processed_at=datetime.fromisoformat(data['processedAt']) if data.get('processedAt') else None,
            processing_fee=Decimal(str(data['processingFee'])) if data.get('processingFee') else None,
            exchange_rate=Decimal(str(data['exchangeRate'])) if data.get('exchangeRate') else None,
            original_currency=data.get('originalCurrency'),
            original_amount=Decimal(str(data['originalAmount'])) if data.get('originalAmount') else None,
            balance_after=Decimal(str(data['balanceAfter'])) if data.get('balanceAfter') else None,
            balance_before=Decimal(str(data['balanceBefore'])) if data.get('balanceBefore') else None,
            transaction_code=data.get('transactionCode'),
            channel=data.get('channel'),
            location=data.get('location'),
            metadata=data.get('metadata', {})
        )

    def to_universal_transaction(self) -> Dict[str, Any]:
        """Convert to universal transaction format for TaxPoynt processing"""
        return {
            'id': self.id,
            'amount': float(self.amount),
            'currency': self.currency,
            'date': self.date.isoformat(),
            'description': self.description,
            'reference': self.reference,
            'account_number': self.counterparty_account,
            'category': 'banking',
            'source_system': 'stitch',
            'raw_data': {
                'transaction_type': self.transaction_type.value,
                'status': self.status.value,
                'counterparty_name': self.counterparty_name,
                'counterparty_bank': self.counterparty_bank,
                'batch_id': self.batch_id,
                'business_purpose': self.business_purpose,
                'cost_center': self.cost_center,
                'department': self.department,
                'project_code': self.project_code,
                'metadata': self.metadata
            }
        }


@dataclass
class StitchWebhookEvent:
    """Enhanced webhook event for enterprise notifications"""
    id: str
    event_type: str
    timestamp: datetime
    account_id: str
    data: Dict[str, Any]
    
    # Enterprise features
    tenant_id: Optional[str] = None
    organization_id: Optional[str] = None
    priority: str = "normal"  # normal, high, critical
    retry_count: int = 0
    max_retries: int = 3
    
    # Security and compliance
    signature: Optional[str] = None
    verified: bool = False
    audit_trail: List[StitchAuditTrail] = None
    
    # Processing status
    processed: bool = False
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.audit_trail is None:
            self.audit_trail = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StitchAccountLinkingResponse:
    """Enhanced account linking response for enterprise customers"""
    link_token: str
    account_id: str
    bank_name: str
    account_number: str
    account_name: str
    link_status: str
    expires_at: datetime
    
    # Enterprise features
    account_group_id: Optional[str] = None
    compliance_status: str = "pending"
    risk_assessment: Optional[Dict[str, Any]] = None
    onboarding_requirements: List[str] = None
    
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.onboarding_requirements is None:
            self.onboarding_requirements = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StitchBulkOperationResult:
    """Result of bulk operations for enterprise customers"""
    operation_id: str
    operation_type: str
    status: StitchBulkOperationStatus
    total_items: int
    processed_items: int
    failed_items: int
    
    # Detailed results
    successful_transactions: List[str] = None
    failed_transactions: List[Dict[str, Any]] = None
    
    # Timing and performance
    started_at: datetime = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    processing_duration: Optional[float] = None
    
    # Error handling
    error_summary: Optional[Dict[str, int]] = None
    retry_eligible_count: int = 0
    
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.successful_transactions is None:
            self.successful_transactions = []
        if self.failed_transactions is None:
            self.failed_transactions = []
        if self.error_summary is None:
            self.error_summary = {}
        if self.metadata is None:
            self.metadata = {}

    @property
    def success_rate(self) -> float:
        """Calculate success rate of the bulk operation"""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def is_completed(self) -> bool:
        """Check if operation is completed"""
        return self.status in [StitchBulkOperationStatus.COMPLETED, StitchBulkOperationStatus.FAILED]


@dataclass
class StitchEnterpriseMetrics:
    """Enterprise-level metrics and analytics"""
    organization_id: str
    reporting_period: str
    
    # Account metrics
    total_accounts: int
    active_accounts: int
    account_types: Dict[str, int]
    total_balance: Decimal
    average_balance: Decimal
    
    # Transaction metrics
    total_transactions: int
    transaction_volume: Decimal
    average_transaction_size: Decimal
    transaction_types: Dict[str, int]
    
    # Performance metrics
    api_calls_made: int
    successful_api_calls: int
    average_response_time: float
    uptime_percentage: float
    
    # Compliance metrics
    compliance_score: float
    aml_alerts: int
    kyc_completion_rate: float
    audit_events: int
    
    # Risk metrics
    high_risk_transactions: int
    risk_score_distribution: Dict[str, int]
    fraud_alerts: int
    
    generated_at: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}