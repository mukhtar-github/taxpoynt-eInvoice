"""
Load Balancer for Provider Distribution
======================================
Advanced load balancing system for distributing banking operations
across multiple providers. Implements various load balancing algorithms
with real-time metrics and adaptive distribution strategies.

Key Features:
- Multiple load balancing algorithms
- Real-time provider load monitoring
- Adaptive load distribution
- Performance-based weighting
- Geographic load balancing
- Request throttling and rate limiting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, field
import random
import hashlib
import time

from ...base import BaseBankingConnector
from .models import (
    BankingProviderType, ProviderStatus, LoadBalancingMetrics,
    LoadDistributionStats, ProviderLoad, WeightedProvider
)
from .exceptions import (
    LoadBalancingError, ProviderOverloadedError, NoCapacityAvailableError,
    LoadBalancerConfigError
)

from .....shared.logging import get_logger
from .....shared.exceptions import IntegrationError


class LoadBalancingAlgorithm(Enum):
    """Load balancing algorithms."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    WEIGHTED_RESPONSE_TIME = "weighted_response_time"
    RANDOM = "random"
    WEIGHTED_RANDOM = "weighted_random"
    CONSISTENT_HASH = "consistent_hash"
    GEOGRAPHIC = "geographic"
    ADAPTIVE = "adaptive"


@dataclass
class LoadBalancingConfig:
    """Configuration for load balancing behavior."""
    algorithm: LoadBalancingAlgorithm = LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN
    enable_health_checking: bool = True
    health_check_interval: int = 30  # seconds
    max_requests_per_provider: int = 100
    request_timeout: float = 30.0
    enable_rate_limiting: bool = True
    rate_limit_window: int = 60  # seconds
    enable_circuit_breaker: bool = True
    failure_threshold: int = 5
    recovery_time: int = 60  # seconds
    adaptive_weights: bool = True
    geographic_preference: bool = False


@dataclass
class ProviderWeight:
    """Weight configuration for a provider."""
    provider_type: BankingProviderType
    static_weight: float = 1.0
    dynamic_weight: float = 1.0
    capacity_weight: float = 1.0
    performance_weight: float = 1.0
    geographic_weight: float = 1.0
    
    @property
    def total_weight(self) -> float:
        """Calculate total effective weight."""
        return (
            self.static_weight * 
            self.dynamic_weight * 
            self.capacity_weight * 
            self.performance_weight * 
            self.geographic_weight
        )


@dataclass
class RequestContext:
    """Context for load balancing decisions."""
    operation_type: str
    account_id: Optional[str] = None
    customer_id: Optional[str] = None
    priority: str = "normal"
    geographic_region: Optional[str] = None
    requires_consistency: bool = False
    estimated_load: int = 1
    timeout: Optional[float] = None


class LoadBalancer:
    """
    Advanced load balancer for distributing banking operations across providers.
    
    This load balancer implements multiple algorithms and strategies to optimally
    distribute requests across banking providers based on current load, performance,
    health, and business requirements.
    """
    
    def __init__(self, config: LoadBalancingConfig):
        """
        Initialize load balancer.
        
        Args:
            config: Load balancing configuration
        """
        self.config = config
        self.logger = get_logger(__name__)
        
        # Provider management
        self.providers: Dict[BankingProviderType, BaseBankingConnector] = {}
        self.provider_weights: Dict[BankingProviderType, ProviderWeight] = {}
        self.provider_loads: Dict[BankingProviderType, ProviderLoad] = {}
        self.provider_status: Dict[BankingProviderType, ProviderStatus] = {}
        
        # Load balancing state
        self.round_robin_index: int = 0
        self.request_counts: Dict[BankingProviderType, int] = {}
        self.rate_limit_windows: Dict[BankingProviderType, Dict[int, int]] = {}
        self.consistent_hash_ring: Dict[int, BankingProviderType] = {}
        
        # Metrics and monitoring
        self.metrics = LoadBalancingMetrics()
        self.health_check_tasks: Dict[BankingProviderType, asyncio.Task] = {}
        self.last_health_checks: Dict[BankingProviderType, datetime] = {}
        
        # Algorithm-specific state
        self.connection_counts: Dict[BankingProviderType, int] = {}
        self.response_times: Dict[BankingProviderType, List[float]] = {}
        
        self.logger.info(f"Initialized load balancer with {config.algorithm.value} algorithm")
    
    def register_provider(
        self,
        provider_type: BankingProviderType,
        provider: BaseBankingConnector,
        weight: float = 1.0,
        max_capacity: int = 100
    ) -> None:
        """
        Register a provider with the load balancer.
        
        Args:
            provider_type: Type of banking provider
            provider: Provider connector instance
            weight: Static weight for load balancing
            max_capacity: Maximum capacity for this provider
        """
        self.providers[provider_type] = provider
        self.provider_weights[provider_type] = ProviderWeight(
            provider_type=provider_type,
            static_weight=weight
        )
        self.provider_loads[provider_type] = ProviderLoad(
            provider_type=provider_type,
            max_capacity=max_capacity
        )
        self.provider_status[provider_type] = ProviderStatus.HEALTHY
        self.request_counts[provider_type] = 0
        self.connection_counts[provider_type] = 0
        self.response_times[provider_type] = []
        self.rate_limit_windows[provider_type] = {}
        
        # Update consistent hash ring
        self._update_consistent_hash_ring()
        
        # Start health monitoring
        if self.config.enable_health_checking:
            self._start_health_monitoring(provider_type)
        
        self.logger.info(f"Registered provider with load balancer: {provider_type}")
    
    async def select_provider(
        self,
        context: RequestContext
    ) -> Optional[Tuple[BankingProviderType, BaseBankingConnector]]:
        """
        Select optimal provider based on load balancing algorithm.
        
        Args:
            context: Request context for selection
            
        Returns:
            Tuple of (provider_type, provider) if available
            
        Raises:
            LoadBalancingError: If selection fails
        """
        try:
            # Get available providers
            available_providers = await self._get_available_providers(context)
            
            if not available_providers:
                raise NoCapacityAvailableError("No providers with available capacity")
            
            # Select based on algorithm
            selected = await self._select_by_algorithm(available_providers, context)
            
            if selected:
                provider_type, provider = selected
                
                # Update load tracking
                await self._increment_provider_load(provider_type, context)
                
                # Record selection
                self.metrics.total_requests += 1
                self.request_counts[provider_type] += 1
                
                self.logger.debug(f"Selected provider {provider_type} for {context.operation_type}")
                
                return selected
            
            return None
            
        except Exception as e:
            self.logger.error(f"Provider selection failed: {str(e)}")
            raise LoadBalancingError(f"Selection failed: {str(e)}")
    
    async def release_provider(
        self,
        provider_type: BankingProviderType,
        context: RequestContext,
        success: bool = True,
        response_time: Optional[float] = None
    ) -> None:
        """
        Release provider after operation completion.
        
        Args:
            provider_type: Provider that was used
            context: Request context
            success: Whether operation was successful
            response_time: Optional response time in seconds
        """
        try:
            # Update load tracking
            await self._decrement_provider_load(provider_type, context)
            
            # Update performance metrics
            if response_time is not None:
                await self._update_response_time(provider_type, response_time)
            
            # Update success/failure metrics
            if success:
                self.metrics.successful_requests += 1
            else:
                self.metrics.failed_requests += 1
                await self._handle_provider_failure(provider_type, context)
            
            # Update adaptive weights if enabled
            if self.config.adaptive_weights:
                await self._update_adaptive_weights(provider_type, success, response_time)
            
        except Exception as e:
            self.logger.error(f"Error releasing provider {provider_type}: {str(e)}")
    
    async def get_load_distribution(self) -> LoadDistributionStats:
        """
        Get current load distribution across providers.
        
        Returns:
            Load distribution statistics
        """
        provider_loads = {}
        total_load = 0
        
        for provider_type, load_info in self.provider_loads.items():
            current_load = load_info.current_load
            provider_loads[provider_type.value] = {
                'current_load': current_load,
                'max_capacity': load_info.max_capacity,
                'utilization': current_load / load_info.max_capacity if load_info.max_capacity > 0 else 0,
                'weight': self.provider_weights[provider_type].total_weight,
                'request_count': self.request_counts[provider_type],
                'average_response_time': self._calculate_average_response_time(provider_type)
            }
            total_load += current_load
        
        return LoadDistributionStats(
            total_load=total_load,
            provider_loads=provider_loads,
            algorithm=self.config.algorithm.value,
            timestamp=datetime.utcnow()
        )
    
    async def rebalance_load(self) -> None:
        """
        Perform load rebalancing across providers.
        """
        try:
            self.logger.info("Performing load rebalancing")
            
            # Update adaptive weights based on current performance
            if self.config.adaptive_weights:
                await self._update_all_adaptive_weights()
            
            # Redistribute consistent hash ring if using consistent hashing
            if self.config.algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
                self._update_consistent_hash_ring()
            
            # Reset round-robin if heavily skewed
            if self.config.algorithm in [
                LoadBalancingAlgorithm.ROUND_ROBIN,
                LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN
            ]:
                self._reset_round_robin_if_needed()
            
            self.logger.info("Load rebalancing completed")
            
        except Exception as e:
            self.logger.error(f"Load rebalancing failed: {str(e)}")
    
    async def _get_available_providers(
        self,
        context: RequestContext
    ) -> List[BankingProviderType]:
        """Get list of available providers for request."""
        available = []
        
        for provider_type, provider in self.providers.items():
            # Check health status
            if self.provider_status[provider_type] != ProviderStatus.HEALTHY:
                continue
            
            # Check capacity
            load_info = self.provider_loads[provider_type]
            if load_info.current_load >= load_info.max_capacity:
                continue
            
            # Check rate limits
            if self.config.enable_rate_limiting:
                if await self._is_rate_limited(provider_type):
                    continue
            
            # Check circuit breaker
            if self.config.enable_circuit_breaker:
                if await self._is_circuit_breaker_open(provider_type):
                    continue
            
            available.append(provider_type)
        
        return available
    
    async def _select_by_algorithm(
        self,
        providers: List[BankingProviderType],
        context: RequestContext
    ) -> Optional[Tuple[BankingProviderType, BaseBankingConnector]]:
        """Select provider based on configured algorithm."""
        if not providers:
            return None
        
        algorithm = self.config.algorithm
        
        if algorithm == LoadBalancingAlgorithm.ROUND_ROBIN:
            return await self._select_round_robin(providers)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_ROUND_ROBIN:
            return await self._select_weighted_round_robin(providers)
        elif algorithm == LoadBalancingAlgorithm.LEAST_CONNECTIONS:
            return await self._select_least_connections(providers)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_LEAST_CONNECTIONS:
            return await self._select_weighted_least_connections(providers)
        elif algorithm == LoadBalancingAlgorithm.LEAST_RESPONSE_TIME:
            return await self._select_least_response_time(providers)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_RESPONSE_TIME:
            return await self._select_weighted_response_time(providers)
        elif algorithm == LoadBalancingAlgorithm.RANDOM:
            return await self._select_random(providers)
        elif algorithm == LoadBalancingAlgorithm.WEIGHTED_RANDOM:
            return await self._select_weighted_random(providers)
        elif algorithm == LoadBalancingAlgorithm.CONSISTENT_HASH:
            return await self._select_consistent_hash(providers, context)
        elif algorithm == LoadBalancingAlgorithm.ADAPTIVE:
            return await self._select_adaptive(providers, context)
        else:
            # Default to weighted round robin
            return await self._select_weighted_round_robin(providers)
    
    async def _select_round_robin(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using round-robin algorithm."""
        selected_type = providers[self.round_robin_index % len(providers)]
        self.round_robin_index = (self.round_robin_index + 1) % len(providers)
        return selected_type, self.providers[selected_type]
    
    async def _select_weighted_round_robin(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using weighted round-robin algorithm."""
        # Create weighted list
        weighted_providers = []
        for provider_type in providers:
            weight = self.provider_weights[provider_type].total_weight
            weighted_providers.extend([provider_type] * max(1, int(weight * 10)))
        
        if weighted_providers:
            selected_type = weighted_providers[self.round_robin_index % len(weighted_providers)]
            self.round_robin_index = (self.round_robin_index + 1) % len(weighted_providers)
            return selected_type, self.providers[selected_type]
        
        return await self._select_round_robin(providers)
    
    async def _select_least_connections(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider with least current connections."""
        least_loaded = min(providers, key=lambda p: self.connection_counts[p])
        return least_loaded, self.providers[least_loaded]
    
    async def _select_weighted_least_connections(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using weighted least connections algorithm."""
        def weighted_load(provider_type):
            connections = self.connection_counts[provider_type]
            weight = self.provider_weights[provider_type].total_weight
            return connections / max(weight, 0.1)  # Avoid division by zero
        
        least_loaded = min(providers, key=weighted_load)
        return least_loaded, self.providers[least_loaded]
    
    async def _select_least_response_time(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider with least average response time."""
        def avg_response_time(provider_type):
            times = self.response_times[provider_type]
            return sum(times) / len(times) if times else 0
        
        fastest = min(providers, key=avg_response_time)
        return fastest, self.providers[fastest]
    
    async def _select_random(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider randomly."""
        selected_type = random.choice(providers)
        return selected_type, self.providers[selected_type]
    
    async def _select_weighted_random(
        self,
        providers: List[BankingProviderType]
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using weighted random algorithm."""
        weights = [self.provider_weights[p].total_weight for p in providers]
        selected_type = random.choices(providers, weights=weights)[0]
        return selected_type, self.providers[selected_type]
    
    async def _select_consistent_hash(
        self,
        providers: List[BankingProviderType],
        context: RequestContext
    ) -> Tuple[BankingProviderType, BaseBankingConnector]:
        """Select provider using consistent hashing."""
        # Create hash key from context
        hash_key = f"{context.account_id or context.customer_id or context.operation_type}"
        hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
        
        # Find closest provider in hash ring
        available_hashes = [h for h, p in self.consistent_hash_ring.items() if p in providers]
        
        if available_hashes:
            closest_hash = min(available_hashes, key=lambda h: abs(h - hash_value))
            selected_type = self.consistent_hash_ring[closest_hash]
            return selected_type, self.providers[selected_type]
        
        # Fallback to weighted random
        return await self._select_weighted_random(providers)
    
    async def _increment_provider_load(
        self,
        provider_type: BankingProviderType,
        context: RequestContext
    ) -> None:
        """Increment load for provider."""
        load_info = self.provider_loads[provider_type]
        load_info.current_load += context.estimated_load
        self.connection_counts[provider_type] += 1
    
    async def _decrement_provider_load(
        self,
        provider_type: BankingProviderType,
        context: RequestContext
    ) -> None:
        """Decrement load for provider."""
        load_info = self.provider_loads[provider_type]
        load_info.current_load = max(0, load_info.current_load - context.estimated_load)
        self.connection_counts[provider_type] = max(0, self.connection_counts[provider_type] - 1)
    
    async def _update_response_time(
        self,
        provider_type: BankingProviderType,
        response_time: float
    ) -> None:
        """Update response time metrics for provider."""
        times = self.response_times[provider_type]
        times.append(response_time)
        
        # Keep only recent measurements
        if len(times) > 100:
            times[:] = times[-50:]
    
    def _calculate_average_response_time(self, provider_type: BankingProviderType) -> float:
        """Calculate average response time for provider."""
        times = self.response_times[provider_type]
        return sum(times) / len(times) if times else 0.0
    
    def _update_consistent_hash_ring(self) -> None:
        """Update consistent hash ring for providers."""
        self.consistent_hash_ring.clear()
        
        for provider_type in self.providers:
            weight = self.provider_weights[provider_type].total_weight
            # Create multiple hash points based on weight
            points = max(1, int(weight * 100))
            
            for i in range(points):
                hash_key = f"{provider_type.value}:{i}"
                hash_value = int(hashlib.md5(hash_key.encode()).hexdigest(), 16)
                self.consistent_hash_ring[hash_value] = provider_type
    
    def _start_health_monitoring(self, provider_type: BankingProviderType) -> None:
        """Start background health monitoring for provider."""
        async def health_monitor():
            while provider_type in self.providers:
                try:
                    await asyncio.sleep(self.config.health_check_interval)
                    
                    provider = self.providers[provider_type]
                    health_status = await provider.health_check()
                    
                    if health_status.get('healthy', False):
                        self.provider_status[provider_type] = ProviderStatus.HEALTHY
                    else:
                        self.provider_status[provider_type] = ProviderStatus.UNHEALTHY
                    
                    self.last_health_checks[provider_type] = datetime.utcnow()
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Health check failed for {provider_type}: {str(e)}")
                    self.provider_status[provider_type] = ProviderStatus.UNHEALTHY
        
        task = asyncio.create_task(health_monitor())
        self.health_check_tasks[provider_type] = task