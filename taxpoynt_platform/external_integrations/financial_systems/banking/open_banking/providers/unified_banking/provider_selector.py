"""
Provider Selector for Intelligent Routing
=========================================
Intelligent provider selection system for banking operations.
Implements advanced routing algorithms based on provider health,
performance metrics, business rules, and enterprise requirements.

Key Features:
- Multi-criteria provider selection
- Performance-based routing
- Business rule-driven selection
- Real-time health monitoring
- Enterprise compliance routing
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import random

from ...base import BaseBankingConnector
from .models import (
    BankingProviderType, ProviderStatus, ProviderMetrics,
    SelectionCriteria, RoutingRule, ProviderScore
)
from .exceptions import (
    ProviderSelectionError, NoProvidersAvailableError,
    InsufficientProviderError
)

from .....shared.logging import get_logger
from .....shared.exceptions import IntegrationError


class SelectionStrategy(Enum):
    """Provider selection strategies."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    PERFORMANCE_BASED = "performance_based"
    LEAST_LOADED = "least_loaded"
    GEOGRAPHIC_PROXIMITY = "geographic_proximity"
    COST_OPTIMIZED = "cost_optimized"
    COMPLIANCE_FIRST = "compliance_first"


@dataclass
class ProviderCapability:
    """Capabilities and limitations of a provider."""
    max_requests_per_minute: int = 100
    max_concurrent_requests: int = 10
    supports_real_time: bool = True
    supports_bulk_operations: bool = True
    supports_webhooks: bool = True
    data_retention_days: int = 90
    compliance_certifications: List[str] = field(default_factory=list)
    geographic_coverage: List[str] = field(default_factory=list)
    account_types_supported: List[str] = field(default_factory=list)
    minimum_balance_required: Optional[float] = None


@dataclass
class SelectionContext:
    """Context information for provider selection."""
    operation_type: str
    account_id: Optional[str] = None
    account_type: Optional[str] = None
    bank_code: Optional[str] = None
    data_volume: int = 0
    requires_real_time: bool = False
    requires_bulk: bool = False
    compliance_level: str = "standard"
    geographic_region: Optional[str] = None
    priority_level: str = "normal"
    customer_tier: str = "standard"


class ProviderSelector:
    """
    Intelligent provider selector implementing advanced routing algorithms.
    
    This selector evaluates providers based on multiple criteria including
    health, performance, capabilities, business rules, and compliance
    requirements to make optimal routing decisions.
    """
    
    def __init__(self):
        """Initialize provider selector."""
        self.logger = get_logger(__name__)
        
        # Provider information
        self.providers: Dict[BankingProviderType, BaseBankingConnector] = {}
        self.provider_status: Dict[BankingProviderType, ProviderStatus] = {}
        self.provider_metrics: Dict[BankingProviderType, ProviderMetrics] = {}
        self.provider_capabilities: Dict[BankingProviderType, ProviderCapability] = {}
        
        # Selection state
        self.routing_rules: List[RoutingRule] = []
        self.selection_history: List[Tuple[datetime, BankingProviderType, str]] = []
        self.round_robin_index: Dict[str, int] = {}
        
        # Configuration
        self.default_strategy = SelectionStrategy.PERFORMANCE_BASED
        self.health_check_threshold = timedelta(minutes=5)
        self.performance_weight = 0.4
        self.health_weight = 0.3
        self.load_weight = 0.3
        
        self.logger.info("Initialized provider selector")
    
    def register_provider(
        self,
        provider_type: BankingProviderType,
        provider: BaseBankingConnector,
        capabilities: ProviderCapability
    ) -> None:
        """
        Register a provider with the selector.
        
        Args:
            provider_type: Type of banking provider
            provider: Provider connector instance
            capabilities: Provider capabilities and limitations
        """
        self.providers[provider_type] = provider
        self.provider_capabilities[provider_type] = capabilities
        self.provider_status[provider_type] = ProviderStatus.UNKNOWN
        self.provider_metrics[provider_type] = ProviderMetrics(
            provider_type=provider_type
        )
        
        self.logger.info(f"Registered provider: {provider_type}")
    
    def add_routing_rule(self, rule: RoutingRule) -> None:
        """
        Add a routing rule for provider selection.
        
        Args:
            rule: Routing rule to add
        """
        self.routing_rules.append(rule)
        self.logger.info(f"Added routing rule: {rule}")
    
    async def select_provider(
        self,
        context: SelectionContext,
        strategy: Optional[SelectionStrategy] = None,
        exclude_providers: Optional[List[BankingProviderType]] = None
    ) -> Optional[Tuple[BankingProviderType, BaseBankingConnector]]:
        """
        Select optimal provider for a given context.
        
        Args:
            context: Selection context with requirements
            strategy: Optional selection strategy override
            exclude_providers: Providers to exclude from selection
            
        Returns:
            Tuple of (provider_type, provider) if available
            
        Raises:
            ProviderSelectionError: If selection fails
        """
        try:
            strategy = strategy or self.default_strategy
            exclude_providers = exclude_providers or []
            
            self.logger.info(
                f"Selecting provider for {context.operation_type} "
                f"using {strategy.value} strategy"
            )
            
            # Get available providers
            available_providers = await self._get_available_providers(
                context, exclude_providers
            )
            
            if not available_providers:
                raise NoProvidersAvailableError(
                    f"No providers available for {context.operation_type}"
                )
            
            # Apply routing rules
            filtered_providers = await self._apply_routing_rules(
                available_providers, context
            )
            
            if not filtered_providers:
                self.logger.warning("No providers after routing rules, using available")
                filtered_providers = available_providers
            
            # Select based on strategy
            selected = await self._select_by_strategy(
                filtered_providers, strategy, context
            )
            
            if selected:
                # Record selection
                self.selection_history.append((
                    datetime.utcnow(),
                    selected[0],
                    context.operation_type
                ))
                
                # Update metrics
                await self._update_selection_metrics(selected[0], context)
                
                self.logger.info(
                    f"Selected provider {selected[0]} for {context.operation_type}"
                )
            
            return selected
            
        except Exception as e:
            self.logger.error(f"Provider selection failed: {str(e)}")
            raise ProviderSelectionError(f"Selection failed: {str(e)}")
    
    async def select_multiple_providers(
        self,
        context: SelectionContext,
        count: int,
        strategy: Optional[SelectionStrategy] = None
    ) -> List[Tuple[BankingProviderType, BaseBankingConnector]]:
        """
        Select multiple providers for load distribution.
        
        Args:
            context: Selection context
            count: Number of providers to select
            strategy: Selection strategy
            
        Returns:
            List of selected providers
            
        Raises:
            InsufficientProviderError: If not enough providers available
        """
        try:
            selected_providers = []
            excluded = []
            
            for i in range(count):
                provider = await self.select_provider(
                    context=context,
                    strategy=strategy,
                    exclude_providers=excluded
                )
                
                if provider:
                    selected_providers.append(provider)
                    excluded.append(provider[0])
                else:
                    break
            
            if len(selected_providers) < count:
                raise InsufficientProviderError(
                    f"Only {len(selected_providers)} providers available, {count} requested"
                )
            
            return selected_providers
            
        except Exception as e:
            self.logger.error(f"Multiple provider selection failed: {str(e)}")
            raise ProviderSelectionError(f"Multiple selection failed: {str(e)}")
    
    async def update_provider_status(
        self,
        provider_type: BankingProviderType,
        status: ProviderStatus,
        health_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update provider status and health information.
        
        Args:
            provider_type: Provider to update
            status: New status
            health_data: Optional health check data
        """
        self.provider_status[provider_type] = status
        
        if health_data and provider_type in self.provider_metrics:
            metrics = self.provider_metrics[provider_type]
            metrics.last_health_check = datetime.utcnow()
            metrics.response_time = health_data.get('response_time', metrics.response_time)
            metrics.success_rate = health_data.get('success_rate', metrics.success_rate)
            metrics.error_rate = health_data.get('error_rate', metrics.error_rate)
        
        self.logger.info(f"Updated {provider_type} status to {status}")
    
    async def get_provider_scores(
        self,
        context: SelectionContext
    ) -> Dict[BankingProviderType, ProviderScore]:
        """
        Calculate scores for all providers based on current context.
        
        Args:
            context: Selection context
            
        Returns:
            Dictionary mapping provider type to score
        """
        scores = {}
        
        for provider_type in self.providers:
            score = await self._calculate_provider_score(provider_type, context)
            scores[provider_type] = score
        
        return scores
    
    async def _get_available_providers(
        self,
        context: SelectionContext,
        exclude_providers: List[BankingProviderType]
    ) -> List[BankingProviderType]:
        """Get list of available providers for selection."""
        available = []
        
        for provider_type, provider in self.providers.items():
            if provider_type in exclude_providers:
                continue
            
            # Check basic availability
            if not await self._is_provider_available(provider_type, context):
                continue
            
            # Check capabilities
            if not await self._check_provider_capabilities(provider_type, context):
                continue
            
            available.append(provider_type)
        
        return available
    
    async def _apply_routing_rules(
        self,
        providers: List[BankingProviderType],
        context: SelectionContext
    ) -> List[BankingProviderType]:
        """Apply routing rules to filter providers."""
        filtered = providers.copy()
        
        for rule in self.routing_rules:
            if await self._rule_matches_context(rule, context):
                # Apply rule preferences and exclusions
                if rule.preferred_providers:
                    preferred = [p for p in filtered if p in rule.preferred_providers]
                    if preferred:
                        filtered = preferred
                
                if rule.excluded_providers:
                    filtered = [p for p in filtered if p not in rule.excluded_providers]
        
        return filtered
    
    async def _select_by_strategy(
        self,
        providers: List[BankingProviderType],
        strategy: SelectionStrategy,
        context: SelectionContext
    ) -> Optional[Tuple[BankingProviderType, BaseBankingConnector]]:
        """Select provider based on specified strategy."""
        if not providers:
            return None
        
        if strategy == SelectionStrategy.ROUND_ROBIN:
            return await self._select_round_robin(providers, context)
        elif strategy == SelectionStrategy.WEIGHTED_RANDOM:
            return await self._select_weighted_random(providers, context)
        elif strategy == SelectionStrategy.PERFORMANCE_BASED:
            return await self._select_performance_based(providers, context)
        elif strategy == SelectionStrategy.LEAST_LOADED:
            return await self._select_least_loaded(providers, context)
        elif strategy == SelectionStrategy.COMPLIANCE_FIRST:
            return await self._select_compliance_first(providers, context)
        else:
            # Default to performance-based
            return await self._select_performance_based(providers, context)
    
    async def _select_round_robin(
        self,
        providers: List[BankingProviderType],
        context: SelectionContext
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using round-robin strategy."""
        operation_key = context.operation_type
        
        if operation_key not in self.round_robin_index:
            self.round_robin_index[operation_key] = 0
        
        index = self.round_robin_index[operation_key] % len(providers)
        selected_type = providers[index]
        
        self.round_robin_index[operation_key] = (index + 1) % len(providers)
        
        return selected_type, self.providers[selected_type]
    
    async def _select_performance_based(
        self,
        providers: List[BankingProviderType],
        context: SelectionContext
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider based on performance metrics."""
        best_provider = None
        best_score = -1
        
        for provider_type in providers:
            score = await self._calculate_provider_score(provider_type, context)
            
            if score.total_score > best_score:
                best_score = score.total_score
                best_provider = provider_type
        
        return best_provider, self.providers[best_provider]
    
    async def _calculate_provider_score(
        self,
        provider_type: BankingProviderType,
        context: SelectionContext
    ) -> ProviderScore:
        """Calculate comprehensive score for a provider."""
        metrics = self.provider_metrics.get(provider_type)
        capabilities = self.provider_capabilities.get(provider_type)
        status = self.provider_status.get(provider_type, ProviderStatus.UNKNOWN)
        
        # Health score (0-1)
        health_score = 1.0 if status == ProviderStatus.HEALTHY else 0.0
        
        # Performance score (0-1)
        performance_score = 0.0
        if metrics:
            performance_score = (
                metrics.success_rate * 0.5 +
                (1.0 - min(metrics.response_time / 1000, 1.0)) * 0.3 +
                (1.0 - metrics.error_rate) * 0.2
            )
        
        # Load score (0-1) - inverse of current load
        load_score = 1.0
        if metrics:
            max_load = capabilities.max_requests_per_minute if capabilities else 100
            current_load = metrics.current_requests / max_load
            load_score = max(0.0, 1.0 - current_load)
        
        # Calculate total score
        total_score = (
            health_score * self.health_weight +
            performance_score * self.performance_weight +
            load_score * self.load_weight
        )
        
        return ProviderScore(
            provider_type=provider_type,
            health_score=health_score,
            performance_score=performance_score,
            load_score=load_score,
            total_score=total_score
        )
    
    async def _is_provider_available(
        self,
        provider_type: BankingProviderType,
        context: SelectionContext
    ) -> bool:
        """Check if provider is available for selection."""
        status = self.provider_status.get(provider_type, ProviderStatus.UNKNOWN)
        
        if status != ProviderStatus.HEALTHY:
            return False
        
        # Check if recent health check
        metrics = self.provider_metrics.get(provider_type)
        if metrics and metrics.last_health_check:
            time_since_check = datetime.utcnow() - metrics.last_health_check
            if time_since_check > self.health_check_threshold:
                return False
        
        return True
    
    async def _check_provider_capabilities(
        self,
        provider_type: BankingProviderType,
        context: SelectionContext
    ) -> bool:
        """Check if provider has required capabilities."""
        capabilities = self.provider_capabilities.get(provider_type)
        if not capabilities:
            return True  # Assume capable if no info
        
        # Check real-time requirement
        if context.requires_real_time and not capabilities.supports_real_time:
            return False
        
        # Check bulk operation requirement
        if context.requires_bulk and not capabilities.supports_bulk_operations:
            return False
        
        # Check account type support
        if (context.account_type and 
            capabilities.account_types_supported and
            context.account_type not in capabilities.account_types_supported):
            return False
        
        return True
    
    async def _rule_matches_context(
        self,
        rule: RoutingRule,
        context: SelectionContext
    ) -> bool:
        """Check if a routing rule matches the current context."""
        # Check account type patterns
        if rule.account_type_patterns and context.account_type:
            if not any(
                self._pattern_matches(pattern, context.account_type)
                for pattern in rule.account_type_patterns
            ):
                return False
        
        # Check bank code patterns
        if rule.bank_code_patterns and context.bank_code:
            if not any(
                self._pattern_matches(pattern, context.bank_code)
                for pattern in rule.bank_code_patterns
            ):
                return False
        
        # Check real-time requirement
        if rule.require_real_time and not context.requires_real_time:
            return False
        
        return True
    
    def _pattern_matches(self, pattern: str, value: str) -> bool:
        """Check if a pattern matches a value (simple wildcard support)."""
        if pattern == "*":
            return True
        
        if "*" in pattern:
            # Simple wildcard matching
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return value.startswith(prefix) and value.endswith(suffix)
        
        return pattern.lower() in value.lower()
    
    async def _update_selection_metrics(
        self,
        provider_type: BankingProviderType,
        context: SelectionContext
    ) -> None:
        """Update metrics after provider selection."""
        if provider_type in self.provider_metrics:
            metrics = self.provider_metrics[provider_type]
            metrics.total_requests += 1
            metrics.current_requests += 1