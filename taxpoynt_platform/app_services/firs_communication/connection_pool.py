"""
FIRS Connection Pool Manager - APP Services

Advanced connection pool manager for FIRS API endpoints in the APP role.
Manages connection pooling, load balancing, failover, and connection health monitoring.

Features:
- Intelligent connection pooling with load balancing
- Automatic failover and retry mechanisms
- Connection health monitoring and circuit breaker
- Environment-specific endpoint management
- Rate limiting and quota management
- Performance metrics and monitoring
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import ssl
import certifi
from urllib.parse import urljoin
import random
import hashlib

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status states"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CIRCUIT_OPEN = "circuit_open"
    MAINTENANCE = "maintenance"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = "round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_RANDOM = "weighted_random"
    RESPONSE_TIME = "response_time"
    HEALTH_AWARE = "health_aware"


@dataclass
class FIRSEndpoint:
    """FIRS endpoint configuration"""
    id: str
    url: str
    weight: int = 1
    max_connections: int = 10
    timeout: int = 30
    environment: str = "sandbox"
    region: str = "default"
    
    # Health monitoring
    status: ConnectionStatus = ConnectionStatus.HEALTHY
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    average_response_time: float = 0.0
    
    # Circuit breaker
    circuit_breaker_open_until: Optional[datetime] = None
    failure_threshold: int = 5
    recovery_timeout: int = 60


@dataclass
class ConnectionMetrics:
    """Connection pool metrics"""
    total_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    peak_connections: int = 0
    connection_errors: int = 0
    timeout_errors: int = 0
    circuit_breaker_trips: int = 0


@dataclass
class PoolConfig:
    """Connection pool configuration"""
    max_pool_size: int = 100
    min_pool_size: int = 5
    max_connections_per_endpoint: int = 20
    connection_timeout: int = 30
    request_timeout: int = 60
    idle_timeout: int = 300  # 5 minutes
    
    # Health monitoring
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10
    max_consecutive_failures: int = 3
    
    # Circuit breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # Load balancing
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_AWARE
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_backoff_factor: float = 2.0


class FIRSConnectionPool:
    """
    Advanced connection pool manager for FIRS API endpoints.
    
    Provides intelligent connection pooling, load balancing, failover,
    and health monitoring for robust FIRS API communication.
    """
    
    def __init__(
        self,
        environment: str = "sandbox",
        config: Optional[PoolConfig] = None
    ):
        self.environment = environment
        self.config = config or PoolConfig()
        
        # Endpoint management
        self.endpoints: Dict[str, FIRSEndpoint] = {}
        self.endpoint_sessions: Dict[str, aiohttp.ClientSession] = {}
        
        # Load balancing state
        self.round_robin_index = 0
        self.endpoint_weights: Dict[str, float] = {}
        
        # Pool state
        self.is_running = False
        self.health_check_task: Optional[asyncio.Task] = None
        self.metrics = ConnectionMetrics()
        
        # SSL context
        self.ssl_context = self._create_ssl_context()
        
        # Request tracking
        self.active_requests: Set[str] = set()
        self.request_history: List[Dict[str, Any]] = []
    
    async def start(self) -> None:
        """Start the connection pool manager"""
        try:
            logger.info(f"Starting FIRS connection pool for {self.environment}")
            
            self.is_running = True
            
            # Initialize default endpoints
            await self._initialize_default_endpoints()
            
            # Create sessions for endpoints
            await self._create_endpoint_sessions()
            
            # Start health monitoring
            if self.config.health_check_interval > 0:
                self.health_check_task = asyncio.create_task(self._health_check_loop())
            
            logger.info("FIRS connection pool started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start connection pool: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the connection pool manager"""
        try:
            logger.info("Stopping FIRS connection pool")
            
            self.is_running = False
            
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass
            
            # Close all sessions
            for session in self.endpoint_sessions.values():
                if session and not session.closed:
                    await session.close()
            
            self.endpoint_sessions.clear()
            
            logger.info("FIRS connection pool stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping connection pool: {e}")
    
    async def add_endpoint(
        self,
        endpoint_id: str,
        url: str,
        weight: int = 1,
        max_connections: int = 10,
        **kwargs
    ) -> bool:
        """Add a new FIRS endpoint to the pool"""
        try:
            endpoint = FIRSEndpoint(
                id=endpoint_id,
                url=url,
                weight=weight,
                max_connections=max_connections,
                environment=self.environment,
                **kwargs
            )
            
            self.endpoints[endpoint_id] = endpoint
            self.endpoint_weights[endpoint_id] = float(weight)
            
            # Create session for the new endpoint
            if self.is_running:
                await self._create_session_for_endpoint(endpoint)
            
            logger.info(f"Added FIRS endpoint: {endpoint_id} -> {url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add endpoint {endpoint_id}: {e}")
            return False
    
    async def remove_endpoint(self, endpoint_id: str) -> bool:
        """Remove an endpoint from the pool"""
        try:
            if endpoint_id not in self.endpoints:
                logger.warning(f"Endpoint {endpoint_id} not found")
                return False
            
            # Close session
            if endpoint_id in self.endpoint_sessions:
                session = self.endpoint_sessions[endpoint_id]
                if session and not session.closed:
                    await session.close()
                del self.endpoint_sessions[endpoint_id]
            
            # Remove from tracking
            del self.endpoints[endpoint_id]
            if endpoint_id in self.endpoint_weights:
                del self.endpoint_weights[endpoint_id]
            
            logger.info(f"Removed FIRS endpoint: {endpoint_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove endpoint {endpoint_id}: {e}")
            return False
    
    async def make_request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retry_on_failure: bool = True
    ) -> Dict[str, Any]:
        """
        Make a request through the connection pool with load balancing and failover
        
        Args:
            method: HTTP method
            path: API path
            data: Request data
            headers: Request headers
            timeout: Request timeout
            retry_on_failure: Whether to retry on failure
            
        Returns:
            Response data with metadata
        """
        request_id = self._generate_request_id()
        start_time = time.time()
        
        try:
            self.active_requests.add(request_id)
            self.metrics.total_requests += 1
            
            # Select endpoint using load balancing
            endpoint = await self._select_endpoint()
            if not endpoint:
                raise Exception("No healthy endpoints available")
            
            # Get session for endpoint
            session = self.endpoint_sessions.get(endpoint.id)
            if not session or session.closed:
                await self._create_session_for_endpoint(endpoint)
                session = self.endpoint_sessions.get(endpoint.id)
            
            if not session:
                raise Exception(f"Failed to create session for endpoint {endpoint.id}")
            
            # Make request with retries
            response_data = await self._make_request_with_retries(
                session=session,
                endpoint=endpoint,
                method=method,
                path=path,
                data=data,
                headers=headers,
                timeout=timeout or self.config.request_timeout,
                max_retries=self.config.max_retries if retry_on_failure else 0,
                request_id=request_id
            )
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_endpoint_metrics(endpoint, True, response_time)
            self.metrics.successful_requests += 1
            
            # Update average response time
            total_time = self.metrics.average_response_time * (self.metrics.total_requests - 1)
            self.metrics.average_response_time = (total_time + response_time) / self.metrics.total_requests
            
            return response_data
            
        except Exception as e:
            # Update failure metrics
            response_time = time.time() - start_time
            if 'endpoint' in locals():
                self._update_endpoint_metrics(endpoint, False, response_time)
            
            self.metrics.failed_requests += 1
            
            logger.error(f"Request {request_id} failed: {e}")
            raise
            
        finally:
            self.active_requests.discard(request_id)
    
    async def _select_endpoint(self) -> Optional[FIRSEndpoint]:
        """Select an endpoint using the configured load balancing strategy"""
        try:
            healthy_endpoints = [
                ep for ep in self.endpoints.values()
                if ep.status in [ConnectionStatus.HEALTHY, ConnectionStatus.DEGRADED]
                and (ep.circuit_breaker_open_until is None or 
                     datetime.now() > ep.circuit_breaker_open_until)
            ]
            
            if not healthy_endpoints:
                logger.warning("No healthy endpoints available")
                return None
            
            if self.config.load_balancing_strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._select_round_robin(healthy_endpoints)
            elif self.config.load_balancing_strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._select_least_connections(healthy_endpoints)
            elif self.config.load_balancing_strategy == LoadBalancingStrategy.WEIGHTED_RANDOM:
                return self._select_weighted_random(healthy_endpoints)
            elif self.config.load_balancing_strategy == LoadBalancingStrategy.RESPONSE_TIME:
                return self._select_by_response_time(healthy_endpoints)
            elif self.config.load_balancing_strategy == LoadBalancingStrategy.HEALTH_AWARE:
                return self._select_health_aware(healthy_endpoints)
            else:
                return healthy_endpoints[0]
                
        except Exception as e:
            logger.error(f"Endpoint selection failed: {e}")
            return None
    
    def _select_round_robin(self, endpoints: List[FIRSEndpoint]) -> FIRSEndpoint:
        """Select endpoint using round-robin strategy"""
        endpoint = endpoints[self.round_robin_index % len(endpoints)]
        self.round_robin_index += 1
        return endpoint
    
    def _select_least_connections(self, endpoints: List[FIRSEndpoint]) -> FIRSEndpoint:
        """Select endpoint with least active connections"""
        # For simplicity, use the one with lowest total requests
        return min(endpoints, key=lambda ep: ep.total_requests)
    
    def _select_weighted_random(self, endpoints: List[FIRSEndpoint]) -> FIRSEndpoint:
        """Select endpoint using weighted random selection"""
        weights = [ep.weight for ep in endpoints]
        return random.choices(endpoints, weights=weights)[0]
    
    def _select_by_response_time(self, endpoints: List[FIRSEndpoint]) -> FIRSEndpoint:
        """Select endpoint with best average response time"""
        return min(endpoints, key=lambda ep: ep.average_response_time or float('inf'))
    
    def _select_health_aware(self, endpoints: List[FIRSEndpoint]) -> FIRSEndpoint:
        """Select endpoint using health-aware strategy"""
        # Score endpoints based on health, response time, and success rate
        scored_endpoints = []
        
        for ep in endpoints:
            health_score = 1.0 if ep.status == ConnectionStatus.HEALTHY else 0.5
            success_rate = ep.successful_requests / max(ep.total_requests, 1)
            response_time_score = 1.0 / (1.0 + ep.average_response_time)
            
            total_score = health_score * 0.4 + success_rate * 0.4 + response_time_score * 0.2
            scored_endpoints.append((ep, total_score))
        
        # Select endpoint with highest score
        return max(scored_endpoints, key=lambda x: x[1])[0]
    
    async def _make_request_with_retries(
        self,
        session: aiohttp.ClientSession,
        endpoint: FIRSEndpoint,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]],
        headers: Optional[Dict[str, str]],
        timeout: int,
        max_retries: int,
        request_id: str
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic"""
        url = urljoin(endpoint.url, path)
        retry_delay = self.config.retry_delay
        
        for attempt in range(max_retries + 1):
            try:
                async with session.request(
                    method=method,
                    url=url,
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    ssl=self.ssl_context
                ) as response:
                    
                    response_text = await response.text()
                    
                    # Parse response
                    try:
                        response_data = await response.json()
                    except Exception:
                        response_data = {'raw_response': response_text}
                    
                    # Check for success
                    if 200 <= response.status < 300:
                        return {
                            'status_code': response.status,
                            'headers': dict(response.headers),
                            'data': response_data,
                            'endpoint_id': endpoint.id,
                            'request_id': request_id,
                            'attempt': attempt + 1
                        }
                    elif response.status == 429:  # Rate limited
                        if attempt < max_retries:
                            # Exponential backoff for rate limiting
                            wait_time = retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                            await asyncio.sleep(wait_time)
                            continue
                    elif response.status >= 500:  # Server error
                        if attempt < max_retries:
                            logger.warning(f"Server error {response.status}, retrying in {retry_delay}s")
                            await asyncio.sleep(retry_delay)
                            retry_delay *= self.config.retry_backoff_factor
                            continue
                    
                    # Non-retryable error
                    return {
                        'status_code': response.status,
                        'headers': dict(response.headers),
                        'data': response_data,
                        'endpoint_id': endpoint.id,
                        'request_id': request_id,
                        'attempt': attempt + 1,
                        'error': f"HTTP {response.status}"
                    }
                    
            except asyncio.TimeoutError:
                self.metrics.timeout_errors += 1
                if attempt < max_retries:
                    logger.warning(f"Request timeout, retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= self.config.retry_backoff_factor
                    continue
                else:
                    raise Exception("Request timeout after all retries")
                    
            except Exception as e:
                self.metrics.connection_errors += 1
                if attempt < max_retries:
                    logger.warning(f"Request error: {e}, retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= self.config.retry_backoff_factor
                    continue
                else:
                    raise
        
        raise Exception("Request failed after all retries")
    
    def _update_endpoint_metrics(
        self,
        endpoint: FIRSEndpoint,
        success: bool,
        response_time: float
    ) -> None:
        """Update endpoint metrics after request"""
        try:
            endpoint.total_requests += 1
            
            if success:
                endpoint.successful_requests += 1
                endpoint.consecutive_failures = 0
            else:
                endpoint.consecutive_failures += 1
            
            # Update average response time
            if endpoint.total_requests == 1:
                endpoint.average_response_time = response_time
            else:
                # Exponential moving average
                alpha = 0.1  # Smoothing factor
                endpoint.average_response_time = (
                    alpha * response_time + 
                    (1 - alpha) * endpoint.average_response_time
                )
            
            # Check circuit breaker
            if (self.config.circuit_breaker_enabled and 
                endpoint.consecutive_failures >= self.config.circuit_breaker_threshold):
                self._trip_circuit_breaker(endpoint)
            
        except Exception as e:
            logger.error(f"Failed to update endpoint metrics: {e}")
    
    def _trip_circuit_breaker(self, endpoint: FIRSEndpoint) -> None:
        """Trip circuit breaker for endpoint"""
        try:
            endpoint.status = ConnectionStatus.CIRCUIT_OPEN
            endpoint.circuit_breaker_open_until = (
                datetime.now() + timedelta(seconds=self.config.circuit_breaker_timeout)
            )
            
            self.metrics.circuit_breaker_trips += 1
            
            logger.warning(f"Circuit breaker tripped for endpoint {endpoint.id}")
            
        except Exception as e:
            logger.error(f"Failed to trip circuit breaker: {e}")
    
    async def _health_check_loop(self) -> None:
        """Background health check loop"""
        while self.is_running:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(self.config.health_check_interval)
    
    async def _perform_health_checks(self) -> None:
        """Perform health checks on all endpoints"""
        try:
            health_check_tasks = []
            
            for endpoint in self.endpoints.values():
                task = asyncio.create_task(self._check_endpoint_health(endpoint))
                health_check_tasks.append(task)
            
            if health_check_tasks:
                await asyncio.gather(*health_check_tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Health check execution failed: {e}")
    
    async def _check_endpoint_health(self, endpoint: FIRSEndpoint) -> None:
        """Check health of a specific endpoint"""
        try:
            session = self.endpoint_sessions.get(endpoint.id)
            if not session or session.closed:
                endpoint.status = ConnectionStatus.UNHEALTHY
                return
            
            # Simple health check - HEAD request to health endpoint
            health_url = urljoin(endpoint.url, "/health")
            
            start_time = time.time()
            
            async with session.head(
                health_url,
                timeout=aiohttp.ClientTimeout(total=self.config.health_check_timeout),
                ssl=self.ssl_context
            ) as response:
                
                response_time = time.time() - start_time
                endpoint.last_health_check = datetime.now()
                
                if response.status == 200:
                    endpoint.status = ConnectionStatus.HEALTHY
                    endpoint.consecutive_failures = 0
                    
                    # Reset circuit breaker if it was open
                    if endpoint.circuit_breaker_open_until:
                        endpoint.circuit_breaker_open_until = None
                        logger.info(f"Circuit breaker reset for endpoint {endpoint.id}")
                        
                elif response.status in [503, 429]:
                    endpoint.status = ConnectionStatus.DEGRADED
                else:
                    endpoint.status = ConnectionStatus.UNHEALTHY
                    endpoint.consecutive_failures += 1
                    
        except Exception as e:
            logger.debug(f"Health check failed for endpoint {endpoint.id}: {e}")
            endpoint.status = ConnectionStatus.UNHEALTHY
            endpoint.consecutive_failures += 1
            endpoint.last_health_check = datetime.now()
    
    async def _initialize_default_endpoints(self) -> None:
        """Initialize default FIRS endpoints for the environment"""
        try:
            if self.environment == "production":
                await self.add_endpoint(
                    "firs_prod_primary",
                    "https://api.firs.gov.ng",
                    weight=3,
                    max_connections=20
                )
                await self.add_endpoint(
                    "firs_prod_secondary",
                    "https://api2.firs.gov.ng",
                    weight=2,
                    max_connections=15
                )
            else:
                await self.add_endpoint(
                    "firs_sandbox_primary",
                    "https://sandbox-api.firs.gov.ng",
                    weight=3,
                    max_connections=15
                )
                await self.add_endpoint(
                    "firs_sandbox_secondary",
                    "https://sandbox-api2.firs.gov.ng",
                    weight=2,
                    max_connections=10
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize default endpoints: {e}")
    
    async def _create_endpoint_sessions(self) -> None:
        """Create HTTP sessions for all endpoints"""
        try:
            for endpoint in self.endpoints.values():
                await self._create_session_for_endpoint(endpoint)
                
        except Exception as e:
            logger.error(f"Failed to create endpoint sessions: {e}")
    
    async def _create_session_for_endpoint(self, endpoint: FIRSEndpoint) -> None:
        """Create HTTP session for a specific endpoint"""
        try:
            # Close existing session if any
            if endpoint.id in self.endpoint_sessions:
                session = self.endpoint_sessions[endpoint.id]
                if session and not session.closed:
                    await session.close()
            
            # Create new session
            connector = aiohttp.TCPConnector(
                limit=endpoint.max_connections,
                limit_per_host=endpoint.max_connections,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=self.ssl_context
            )
            
            timeout = aiohttp.ClientTimeout(
                total=endpoint.timeout,
                connect=10,
                sock_read=endpoint.timeout
            )
            
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'TaxPoynt-APP-Pool/1.0',
                    'Accept': 'application/json'
                }
            )
            
            self.endpoint_sessions[endpoint.id] = session
            self.metrics.total_connections += 1
            
            logger.debug(f"Created session for endpoint {endpoint.id}")
            
        except Exception as e:
            logger.error(f"Failed to create session for endpoint {endpoint.id}: {e}")
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for secure connections"""
        try:
            context = ssl.create_default_context(cafile=certifi.where())
            
            # Force TLS 1.2+ for security
            if hasattr(ssl, 'TLSVersion'):
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            return ssl.create_default_context()
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        timestamp = str(int(time.time() * 1000))
        random_part = hashlib.md5(f"{timestamp}{random.random()}".encode()).hexdigest()[:8]
        return f"req_{timestamp}_{random_part}"
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics"""
        try:
            endpoint_status = {}
            for endpoint_id, endpoint in self.endpoints.items():
                endpoint_status[endpoint_id] = {
                    'url': endpoint.url,
                    'status': endpoint.status.value,
                    'weight': endpoint.weight,
                    'total_requests': endpoint.total_requests,
                    'successful_requests': endpoint.successful_requests,
                    'success_rate': endpoint.successful_requests / max(endpoint.total_requests, 1),
                    'average_response_time': endpoint.average_response_time,
                    'consecutive_failures': endpoint.consecutive_failures,
                    'last_health_check': endpoint.last_health_check.isoformat() if endpoint.last_health_check else None,
                    'circuit_breaker_open': endpoint.circuit_breaker_open_until is not None,
                    'has_session': endpoint.id in self.endpoint_sessions
                }
            
            return {
                'environment': self.environment,
                'is_running': self.is_running,
                'total_endpoints': len(self.endpoints),
                'healthy_endpoints': len([ep for ep in self.endpoints.values() if ep.status == ConnectionStatus.HEALTHY]),
                'active_requests': len(self.active_requests),
                'metrics': {
                    'total_connections': self.metrics.total_connections,
                    'total_requests': self.metrics.total_requests,
                    'successful_requests': self.metrics.successful_requests,
                    'failed_requests': self.metrics.failed_requests,
                    'success_rate': self.metrics.successful_requests / max(self.metrics.total_requests, 1),
                    'average_response_time': self.metrics.average_response_time,
                    'connection_errors': self.metrics.connection_errors,
                    'timeout_errors': self.metrics.timeout_errors,
                    'circuit_breaker_trips': self.metrics.circuit_breaker_trips
                },
                'endpoints': endpoint_status,
                'load_balancing_strategy': self.config.load_balancing_strategy.value
            }
            
        except Exception as e:
            logger.error(f"Failed to get pool status: {e}")
            return {'error': str(e)}


# Factory function for creating FIRS connection pool
def create_firs_connection_pool(
    environment: str = "sandbox",
    config: Optional[PoolConfig] = None
) -> FIRSConnectionPool:
    """
    Factory function to create FIRS connection pool
    
    Args:
        environment: FIRS environment
        config: Pool configuration
        
    Returns:
        Configured FIRS connection pool
    """
    return FIRSConnectionPool(environment=environment, config=config)