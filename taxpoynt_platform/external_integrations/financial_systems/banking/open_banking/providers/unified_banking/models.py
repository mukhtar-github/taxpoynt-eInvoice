"""
Unified Banking Models
=====================
Unified data models for multi-provider banking operations.
Provides consistent interfaces and data structures across
different banking providers with enterprise features.

Key Features:
- Provider-agnostic data models
- Enterprise compliance structures
- Load balancing configurations
- Failover and recovery models
- Aggregation metrics and reporting
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field
import uuid


class BankingProviderType(Enum):
    """Supported banking provider types."""
    MONO = "mono"
    STITCH = "stitch"
    OKRA = "okra"
    FLUTTERWAVE = "flutterwave"
    PAYSTACK = "paystack"


class ProviderStatus(Enum):
    """Provider health status."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class TransactionType(Enum):
    """Unified transaction types."""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    FEE = "fee"
    INTEREST = "interest"
    REVERSAL = "reversal"
    ADJUSTMENT = "adjustment"


class AccountType(Enum):
    """Unified account types."""
    CHECKING = "checking"
    SAVINGS = "savings"
    CREDIT = "credit"
    INVESTMENT = "investment"
    LOAN = "loan"
    BUSINESS = "business"
    CORPORATE = "corporate"
    JOINT = "joint"


@dataclass
class UnifiedAccount:
    """Unified account model across providers."""
    account_id: str
    provider_type: BankingProviderType
    provider_account_id: str
    account_number: str
    account_name: str
    account_type: AccountType
    bank_code: str
    bank_name: str
    currency: str = "NGN"
    balance: Optional[Decimal] = None
    available_balance: Optional[Decimal] = None
    account_holder_name: str = ""
    account_holder_id: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: List[str] = field(default_factory=list)


@dataclass
class UnifiedTransaction:
    """Unified transaction model across providers."""
    transaction_id: str
    provider_type: BankingProviderType
    provider_transaction_id: str
    account_id: str
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    description: str
    reference: Optional[str] = None
    transaction_date: Optional[datetime] = None
    value_date: Optional[datetime] = None
    balance_after: Optional[Decimal] = None
    counterparty_name: Optional[str] = None
    counterparty_account: Optional[str] = None
    counterparty_bank: Optional[str] = None
    category: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    compliance_flags: List[str] = field(default_factory=list)


@dataclass
class UnifiedBalance:
    """Unified balance model across providers."""
    account_id: str
    provider_type: BankingProviderType
    current_balance: Decimal
    available_balance: Decimal
    currency: str
    last_updated: datetime
    pending_transactions: Optional[Decimal] = None
    overdraft_limit: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedTransactionResponse:
    """Unified response for transaction queries."""
    account_id: str
    provider_type: BankingProviderType
    transactions: List[UnifiedTransaction]
    total_count: int
    has_more: bool = False
    next_cursor: Optional[str] = None
    page_info: Optional[Dict[str, Any]] = None
    query_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderMetrics:
    """Metrics for a specific provider."""
    provider_type: BankingProviderType
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    current_requests: int = 0
    average_response_time: float = 0.0
    response_time: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    last_health_check: Optional[datetime] = None
    uptime_percentage: float = 100.0
    rate_limit_remaining: Optional[int] = None


@dataclass
class ProviderLoad:
    """Load information for a provider."""
    provider_type: BankingProviderType
    current_load: int = 0
    max_capacity: int = 100
    requests_per_minute: int = 0
    connections_active: int = 0
    queue_size: int = 0
    response_time_p95: float = 0.0
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate utilization percentage."""
        return (self.current_load / self.max_capacity * 100) if self.max_capacity > 0 else 0


@dataclass
class AggregatorConfig:
    """Configuration for banking aggregator."""
    providers: List[Any] = field(default_factory=list)  # ProviderConfig list
    enable_failover: bool = True
    enable_load_balancing: bool = True
    default_timeout: float = 30.0
    max_retries: int = 3
    health_check_interval: int = 60
    compliance_mode: bool = True
    audit_logging: bool = True
    data_retention_days: int = 2555  # 7 years for compliance
    
    
@dataclass
class SelectionCriteria:
    """Criteria for provider selection."""
    operation_type: str
    performance_weight: float = 0.4
    reliability_weight: float = 0.3
    cost_weight: float = 0.2
    compliance_weight: float = 0.1
    geographic_preference: Optional[str] = None
    require_real_time: bool = False
    max_acceptable_latency: Optional[float] = None


@dataclass
class RoutingRule:
    """Rule for provider routing decisions."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_name: str = ""
    priority: int = 100
    conditions: Dict[str, Any] = field(default_factory=dict)
    preferred_providers: List[BankingProviderType] = field(default_factory=list)
    excluded_providers: List[BankingProviderType] = field(default_factory=list)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ProviderScore:
    """Score for provider selection."""
    provider_type: BankingProviderType
    health_score: float
    performance_score: float
    load_score: float
    compliance_score: float = 1.0
    total_score: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AggregatorMetrics:
    """Metrics for the aggregator system."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    provider_successes: Dict[BankingProviderType, int] = field(default_factory=dict)
    provider_failures: Dict[BankingProviderType, int] = field(default_factory=dict)
    average_response_time: float = 0.0
    uptime_percentage: float = 100.0
    last_health_check: Optional[datetime] = None


@dataclass
class LoadBalancingMetrics:
    """Metrics for load balancing operations."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    provider_distribution: Dict[BankingProviderType, int] = field(default_factory=dict)
    average_response_time: float = 0.0
    peak_load: int = 0
    load_distribution_efficiency: float = 0.0


@dataclass
class LoadDistributionStats:
    """Statistics for load distribution."""
    total_load: int
    provider_loads: Dict[str, Dict[str, Any]]
    algorithm: str
    timestamp: datetime
    efficiency_score: float = 0.0
    balance_score: float = 0.0


@dataclass
class WeightedProvider:
    """Provider with weight information."""
    provider_type: BankingProviderType
    weight: float
    current_load: int
    max_capacity: int
    
    @property
    def load_ratio(self) -> float:
        """Calculate load ratio."""
        return self.current_load / self.max_capacity if self.max_capacity > 0 else 0


@dataclass
class FailoverPolicy:
    """Policy for failover operations."""
    max_attempts: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    health_check_timeout: float = 10.0
    recovery_timeout: float = 300.0
    enable_auto_recovery: bool = True


@dataclass
class FailoverEvent:
    """Event record for failover operations."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_provider: BankingProviderType
    to_provider: BankingProviderType
    reason: str
    timestamp: datetime
    operation_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    recovery_time: Optional[float] = None
    manual: bool = False


@dataclass
class RecoveryAttempt:
    """Record of provider recovery attempts."""
    attempt_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    provider_type: BankingProviderType
    timestamp: datetime
    successful: bool
    attempt_count: int = 1
    error: Optional[str] = None
    recovery_time: Optional[float] = None


@dataclass
class ComplianceReport:
    """Compliance reporting structure."""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_type: str
    provider_type: BankingProviderType
    start_date: datetime
    end_date: datetime
    generated_at: datetime = field(default_factory=datetime.utcnow)
    summary: Dict[str, Any] = field(default_factory=dict)
    details: List[Dict[str, Any]] = field(default_factory=list)
    compliance_score: float = 0.0
    violations: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AuditEntry:
    """Audit log entry for compliance."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    provider_type: BankingProviderType
    operation_type: str
    user_id: Optional[str] = None
    account_id: Optional[str] = None
    transaction_id: Optional[str] = None
    action: str
    result: str
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    compliance_tags: List[str] = field(default_factory=list)


@dataclass
class ProviderHealthStatus:
    """Comprehensive health status for a provider."""
    provider_type: BankingProviderType
    status: ProviderStatus
    last_check: datetime
    response_time: float
    success_rate: float
    error_count: int
    uptime_percentage: float
    api_version: Optional[str] = None
    rate_limit_status: Optional[Dict[str, Any]] = None
    maintenance_window: Optional[Dict[str, datetime]] = None
    alerts: List[str] = field(default_factory=list)
    metrics: Optional[ProviderMetrics] = None


@dataclass 
class TransactionFilter:
    """Filter for transaction queries."""
    account_ids: Optional[List[str]] = None
    transaction_types: Optional[List[TransactionType]] = None
    amount_min: Optional[Decimal] = None
    amount_max: Optional[Decimal] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description_contains: Optional[str] = None
    reference_contains: Optional[str] = None
    categories: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    compliance_flags: Optional[List[str]] = None


@dataclass
class BulkOperationRequest:
    """Request for bulk operations."""
    operation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    operation_type: str
    provider_type: BankingProviderType
    account_ids: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: str = "normal"
    timeout: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BulkOperationResult:
    """Result of bulk operations."""
    operation_id: str
    operation_type: str
    provider_type: BankingProviderType
    total_items: int
    successful_items: int
    failed_items: int
    results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration: Optional[float] = None
    status: str = "pending"