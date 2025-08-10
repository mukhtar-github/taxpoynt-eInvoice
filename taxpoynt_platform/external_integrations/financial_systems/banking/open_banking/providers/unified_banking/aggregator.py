"""
Unified Banking Aggregator
=========================
Central orchestrator for multiple open banking providers.
Provides unified interface for banking operations across different providers
with intelligent routing, failover, and load balancing capabilities.

Key Features:
- Multi-provider banking aggregation
- Intelligent provider selection and routing
- Automatic failover and redundancy
- Load balancing across providers
- Unified data models and responses
- Enterprise compliance and audit
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Type
from decimal import Decimal
from enum import Enum
from dataclasses import dataclass, field

from ..base import BaseBankingConnector
from ..providers.mono.connector import MonoBankingConnector
from ..providers.stitch.connector import StitchBankingConnector
from .models import (
    UnifiedAccount, UnifiedTransaction, UnifiedBalance,
    BankingProviderType, AggregatorConfig, ProviderStatus,
    UnifiedTransactionResponse, AggregatorMetrics
)
from .exceptions import (
    BankingAggregatorError, ProviderUnavailableError,
    NoProvidersAvailableError, DataConsistencyError
)

from .....shared.logging import get_logger
from .....shared.exceptions import IntegrationError
from .....shared.config import BaseConfig


class ProviderPriority(Enum):
    """Provider priority levels for intelligent routing."""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3
    EMERGENCY = 4


@dataclass
class ProviderConfig:
    """Configuration for individual banking provider."""
    provider_type: BankingProviderType
    connector_class: Type[BaseBankingConnector]
    config: Any
    priority: ProviderPriority = ProviderPriority.SECONDARY
    enabled: bool = True
    max_requests_per_minute: int = 100
    timeout_seconds: int = 30
    retry_attempts: int = 3
    health_check_interval: int = 300  # seconds


@dataclass
class RoutingRule:
    """Rules for intelligent provider routing."""
    account_type_patterns: List[str] = field(default_factory=list)
    bank_code_patterns: List[str] = field(default_factory=list)
    preferred_providers: List[BankingProviderType] = field(default_factory=list)
    excluded_providers: List[BankingProviderType] = field(default_factory=list)
    min_data_freshness: Optional[timedelta] = None
    require_real_time: bool = False


class UnifiedBankingAggregator:
    """
    Unified banking aggregator coordinating multiple open banking providers.
    
    This aggregator provides a single interface for banking operations while
    intelligently routing requests across multiple providers based on
    availability, performance, and business rules.
    """
    
    def __init__(self, config: AggregatorConfig):
        """
        Initialize unified banking aggregator.
        
        Args:
            config: Aggregator configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Provider management
        self.providers: Dict[BankingProviderType, BaseBankingConnector] = {}
        self.provider_configs: Dict[BankingProviderType, ProviderConfig] = {}
        self.provider_status: Dict[BankingProviderType, ProviderStatus] = {}
        
        # Routing and load balancing
        self.routing_rules: List[RoutingRule] = []
        self.request_counts: Dict[BankingProviderType, int] = {}
        self.last_health_checks: Dict[BankingProviderType, datetime] = {}
        
        # Aggregator state
        self.is_initialized = False
        self.metrics = AggregatorMetrics()
        
        self.logger.info("Initialized unified banking aggregator")
    
    async def initialize(self) -> None:
        """
        Initialize all configured banking providers.
        
        Raises:
            BankingAggregatorError: If initialization fails
        """
        try:
            self.logger.info("Initializing banking providers...")
            
            # Initialize configured providers
            await self._initialize_providers()
            
            # Set up default routing rules
            await self._setup_default_routing_rules()
            
            # Perform initial health checks
            await self._perform_initial_health_checks()
            
            self.is_initialized = True
            
            self.logger.info(
                f"Successfully initialized {len(self.providers)} banking providers"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to initialize aggregator: {str(e)}")
            raise BankingAggregatorError(f"Aggregator initialization failed: {str(e)}")
    
    async def get_accounts(
        self,
        customer_id: Optional[str] = None,
        bank_codes: Optional[List[str]] = None,
        account_types: Optional[List[str]] = None,
        include_inactive: bool = False
    ) -> List[UnifiedAccount]:
        """
        Retrieve banking accounts from all available providers.
        
        Args:
            customer_id: Optional customer identifier filter
            bank_codes: Optional bank code filters
            account_types: Optional account type filters
            include_inactive: Whether to include inactive accounts
            
        Returns:
            List of unified accounts from all providers
            
        Raises:
            BankingAggregatorError: If operation fails
        """
        await self._ensure_initialized()
        
        try:
            self.logger.info(
                f"Fetching accounts across providers for customer: {customer_id or 'all'}"
            )
            
            # Get accounts from all available providers
            all_accounts = []
            provider_results = {}
            
            for provider_type, provider in self.providers.items():
                if not await self._is_provider_healthy(provider_type):
                    continue
                
                try:
                    # Route request to specific provider
                    accounts = await self._get_accounts_from_provider(
                        provider=provider,
                        provider_type=provider_type,
                        customer_id=customer_id,
                        bank_codes=bank_codes,
                        account_types=account_types,
                        include_inactive=include_inactive
                    )
                    
                    provider_results[provider_type] = accounts
                    all_accounts.extend(accounts)
                    
                    self.metrics.successful_requests += 1
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to fetch accounts from {provider_type}: {str(e)}"
                    )
                    self.metrics.failed_requests += 1
                    continue
            
            # Deduplicate accounts across providers
            unified_accounts = await self._deduplicate_accounts(all_accounts)
            
            self.logger.info(
                f"Retrieved {len(unified_accounts)} unified accounts "
                f"from {len(provider_results)} providers"
            )
            
            return unified_accounts
            
        except Exception as e:
            self.logger.error(f"Failed to fetch accounts: {str(e)}")
            raise BankingAggregatorError(f"Account retrieval failed: {str(e)}")
    
    async def get_transactions(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: Optional[int] = None,
        provider_preference: Optional[BankingProviderType] = None
    ) -> UnifiedTransactionResponse:
        """
        Retrieve transactions for a specific account with intelligent routing.
        
        Args:
            account_id: Account identifier
            start_date: Start date for transaction search
            end_date: End date for transaction search
            limit: Maximum number of transactions
            provider_preference: Preferred provider for this request
            
        Returns:
            Unified transaction response
            
        Raises:
            BankingAggregatorError: If operation fails
        """
        await self._ensure_initialized()
        
        try:
            self.logger.info(
                f"Fetching transactions for account {account_id} "
                f"from {start_date} to {end_date}"
            )
            
            # Select optimal provider for this request
            selected_provider = await self._select_provider_for_transactions(
                account_id=account_id,
                preference=provider_preference
            )
            
            if not selected_provider:
                raise NoProvidersAvailableError(
                    "No healthy providers available for transaction retrieval"
                )
            
            provider_type, provider = selected_provider
            
            try:
                # Fetch transactions from selected provider
                response = await self._get_transactions_from_provider(
                    provider=provider,
                    provider_type=provider_type,
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit
                )
                
                self.metrics.successful_requests += 1
                self._update_provider_metrics(provider_type, success=True)
                
                self.logger.info(
                    f"Retrieved {len(response.transactions)} transactions "
                    f"from {provider_type} for account {account_id}"
                )
                
                return response
                
            except Exception as e:
                self.metrics.failed_requests += 1
                self._update_provider_metrics(provider_type, success=False)
                
                # Try failover to alternative provider
                return await self._failover_transaction_request(
                    account_id=account_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    failed_provider=provider_type,
                    original_error=e
                )
                
        except Exception as e:
            self.logger.error(f"Failed to fetch transactions: {str(e)}")
            raise BankingAggregatorError(f"Transaction retrieval failed: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check across all providers.
        
        Returns:
            Aggregated health status
        """
        try:
            health_results = {}
            overall_healthy = True
            
            for provider_type, provider in self.providers.items():
                try:
                    provider_health = await provider.health_check()
                    health_results[provider_type.value] = provider_health
                    
                    if not provider_health.get('healthy', False):
                        overall_healthy = False
                        
                except Exception as e:
                    health_results[provider_type.value] = {
                        'healthy': False,
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    overall_healthy = False
            
            return {
                'healthy': overall_healthy,
                'providers': health_results,
                'metrics': {
                    'total_requests': self.metrics.successful_requests + self.metrics.failed_requests,
                    'successful_requests': self.metrics.successful_requests,
                    'failed_requests': self.metrics.failed_requests,
                    'success_rate': self._calculate_success_rate()
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _initialize_providers(self) -> None:
        """Initialize all configured banking providers."""
        for provider_config in self.config.providers:
            try:
                # Create provider instance
                provider = provider_config.connector_class(provider_config.config)
                
                # Connect to provider
                await provider.connect()
                
                # Store provider
                self.providers[provider_config.provider_type] = provider
                self.provider_configs[provider_config.provider_type] = provider_config
                self.provider_status[provider_config.provider_type] = ProviderStatus.HEALTHY
                self.request_counts[provider_config.provider_type] = 0
                
                self.logger.info(f"Initialized provider: {provider_config.provider_type}")
                
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize {provider_config.provider_type}: {str(e)}"
                )
                self.provider_status[provider_config.provider_type] = ProviderStatus.UNHEALTHY
    
    async def _setup_default_routing_rules(self) -> None:
        """Set up default routing rules for provider selection."""
        # High-priority accounts prefer primary providers
        self.routing_rules.append(RoutingRule(
            account_type_patterns=['*PRIORITY*', '*VIP*'],
            preferred_providers=[BankingProviderType.STITCH],
            require_real_time=True
        ))
        
        # Standard accounts can use any provider
        self.routing_rules.append(RoutingRule(
            account_type_patterns=['*'],
            preferred_providers=[BankingProviderType.MONO, BankingProviderType.STITCH]
        ))
    
    async def _ensure_initialized(self) -> None:
        """Ensure aggregator is properly initialized."""
        if not self.is_initialized:
            raise BankingAggregatorError("Aggregator not initialized")
    
    async def _is_provider_healthy(self, provider_type: BankingProviderType) -> bool:
        """Check if a provider is healthy and available."""
        return (
            provider_type in self.provider_status and
            self.provider_status[provider_type] == ProviderStatus.HEALTHY and
            provider_type in self.providers
        )
    
    def _calculate_success_rate(self) -> float:
        """Calculate overall success rate."""
        total = self.metrics.successful_requests + self.metrics.failed_requests
        if total == 0:
            return 1.0
        return self.metrics.successful_requests / total
    
    def _update_provider_metrics(self, provider_type: BankingProviderType, success: bool) -> None:
        """Update metrics for a specific provider."""
        self.request_counts[provider_type] = self.request_counts.get(provider_type, 0) + 1