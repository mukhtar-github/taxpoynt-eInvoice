"""
Unified Banking Module
=====================
Multi-provider interface for open banking operations.
Provides unified access to multiple banking providers with intelligent
routing, failover, and load balancing capabilities.

Key Components:
- aggregator: Provider aggregation logic
- provider_selector: Intelligent provider selection
- failover_manager: Provider failover handling
- load_balancer: Provider load balancing
- models: Unified data models and structures
- exceptions: Comprehensive error handling
"""

from .aggregator import UnifiedBankingAggregator
from .provider_selector import ProviderSelector, SelectionStrategy, SelectionContext
from .failover_manager import FailoverManager, FailoverStrategy
from .load_balancer import LoadBalancer, LoadBalancingAlgorithm, RequestContext
from .models import (
    # Core unified models
    UnifiedAccount, UnifiedTransaction, UnifiedBalance, UnifiedTransactionResponse,
    
    # Provider and system models
    BankingProviderType, ProviderStatus, ProviderMetrics, ProviderLoad,
    
    # Configuration models
    AggregatorConfig, SelectionCriteria, RoutingRule, FailoverPolicy,
    
    # Metrics and monitoring
    AggregatorMetrics, LoadBalancingMetrics, LoadDistributionStats,
    ProviderScore, ProviderHealthStatus,
    
    # Compliance and audit
    ComplianceReport, AuditEntry,
    
    # Operation models
    TransactionFilter, BulkOperationRequest, BulkOperationResult,
    
    # Enums
    TransactionType, AccountType, CircuitBreakerState
)
from .exceptions import (
    # Base exceptions
    BankingError, BankingAggregatorError,
    
    # Provider exceptions
    ProviderUnavailableError, NoProvidersAvailableError, ProviderSelectionError,
    ProviderOverloadedError, ProviderAuthenticationError, ProviderAuthorizationError,
    ProviderRateLimitError, ProviderNetworkError, ProviderTimeoutError,
    ProviderDataError,
    
    # Load balancing exceptions
    LoadBalancingError, NoCapacityAvailableError, LoadBalancerConfigError,
    
    # Failover exceptions
    FailoverError, CircuitBreakerOpenError, NoHealthyProvidersError,
    FailoverTimeoutError, MaxRetriesExceededError,
    
    # Data and compliance exceptions
    DataConsistencyError, ComplianceViolationError, AuditTrailError,
    BusinessRuleViolationError, ConfigurationError, BankingSecurityError,
    
    # Utility functions
    create_provider_error, handle_provider_exception
)

__all__ = [
    # Core components
    'UnifiedBankingAggregator',
    'ProviderSelector',
    'FailoverManager', 
    'LoadBalancer',
    
    # Strategy and context classes
    'SelectionStrategy',
    'SelectionContext',
    'FailoverStrategy',
    'LoadBalancingAlgorithm',
    'RequestContext',
    
    # Core unified models
    'UnifiedAccount',
    'UnifiedTransaction',
    'UnifiedBalance',
    'UnifiedTransactionResponse',
    
    # Provider and system models
    'BankingProviderType',
    'ProviderStatus',
    'ProviderMetrics',
    'ProviderLoad',
    
    # Configuration models
    'AggregatorConfig',
    'SelectionCriteria',
    'RoutingRule',
    'FailoverPolicy',
    
    # Metrics and monitoring
    'AggregatorMetrics',
    'LoadBalancingMetrics',
    'LoadDistributionStats',
    'ProviderScore',
    'ProviderHealthStatus',
    
    # Compliance and audit
    'ComplianceReport',
    'AuditEntry',
    
    # Operation models
    'TransactionFilter',
    'BulkOperationRequest',
    'BulkOperationResult',
    
    # Enums
    'TransactionType',
    'AccountType',
    'CircuitBreakerState',
    
    # Base exceptions
    'BankingError',
    'BankingAggregatorError',
    
    # Provider exceptions
    'ProviderUnavailableError',
    'NoProvidersAvailableError',
    'ProviderSelectionError',
    'ProviderOverloadedError',
    'ProviderAuthenticationError',
    'ProviderAuthorizationError',
    'ProviderRateLimitError',
    'ProviderNetworkError',
    'ProviderTimeoutError',
    'ProviderDataError',
    
    # Load balancing exceptions
    'LoadBalancingError',
    'NoCapacityAvailableError',
    'LoadBalancerConfigError',
    
    # Failover exceptions
    'FailoverError',
    'CircuitBreakerOpenError',
    'NoHealthyProvidersError',
    'FailoverTimeoutError',
    'MaxRetriesExceededError',
    
    # Data and compliance exceptions
    'DataConsistencyError',
    'ComplianceViolationError',
    'AuditTrailError',
    'BusinessRuleViolationError',
    'ConfigurationError',
    'BankingSecurityError',
    
    # Utility functions
    'create_provider_error',
    'handle_provider_exception'
]