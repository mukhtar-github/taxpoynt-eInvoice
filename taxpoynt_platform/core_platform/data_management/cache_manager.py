"""
Distributed Cache Manager for TaxPoynt Platform

Enterprise-grade caching with Redis integration, performance optimization,
and scalability patterns for high-volume invoice processing.
"""

import logging
import json
import pickle
import hashlib
import time
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable, Set, Tuple
from uuid import UUID
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum
import redis
from redis.sentinel import Sentinel
from redis.cluster import RedisCluster
import threading
from concurrent.futures import ThreadPoolExecutor, Future
import os

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy patterns."""
    WRITE_THROUGH = "write_through"      # Write to cache and database simultaneously
    WRITE_BEHIND = "write_behind"        # Write to cache first, database later
    WRITE_AROUND = "write_around"        # Write to database, invalidate cache
    REFRESH_AHEAD = "refresh_ahead"      # Proactively refresh before expiry


class CacheLevel(Enum):
    """Cache levels for different data types."""
    L1_MEMORY = "l1_memory"              # In-memory cache (fastest)
    L2_REDIS = "l2_redis"                # Redis cache (fast, persistent)
    L3_DATABASE = "l3_database"          # Database query cache


class SerializationFormat(Enum):
    """Serialization formats for cache data."""
    JSON = "json"                        # Human-readable, slower
    PICKLE = "pickle"                    # Faster, binary format
    MSGPACK = "msgpack"                  # Compact, fast
    COMPRESSED = "compressed"            # Gzip compressed JSON


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    default_ttl_seconds: int = 3600      # 1 hour default
    max_memory_cache_size: int = 1000    # Max items in memory cache
    redis_url: Optional[str] = None
    redis_cluster_nodes: Optional[List[str]] = None
    redis_sentinel_hosts: Optional[List[str]] = None
    enable_compression: bool = True
    compression_threshold: int = 1024    # Compress data > 1KB
    serialization_format: SerializationFormat = SerializationFormat.JSON
    cache_strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    enable_metrics: bool = True
    circuit_breaker_threshold: int = 10  # Failed operations before circuit break


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    writes: int = 0
    deletes: int = 0
    errors: int = 0
    total_operations: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    redis_memory_usage_mb: float = 0.0
    last_reset: datetime = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.utcnow()
    
    @property
    def hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        total_reads = self.hits + self.misses
        if total_reads == 0:
            return 0.0
        return (self.hits / total_reads) * 100


class CircuitBreaker:
    """Circuit breaker for cache operations."""
    
    def __init__(self, failure_threshold: int = 10, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self._lock:
            if self.state == "open":
                if self._should_attempt_reset():
                    self.state = "half-open"
                else:
                    raise Exception("Circuit breaker is open")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        return (datetime.utcnow() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = "closed"
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class MemoryCache:
    """Thread-safe in-memory LRU cache."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)
        self._access_order: List[str] = []
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key in self._cache:
                value, expiry = self._cache[key]
                
                # Check if expired
                if expiry > 0 and time.time() > expiry:
                    self._remove_key(key)
                    return None
                
                # Update access order for LRU
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                
                return value
            return None
    
    def set(self, key: str, value: Any, ttl: int = 0):
        """Set value in memory cache with optional TTL."""
        with self._lock:
            expiry = time.time() + ttl if ttl > 0 else 0
            
            # Remove if already exists
            if key in self._cache:
                self._access_order.remove(key)
            
            # Add new entry
            self._cache[key] = (value, expiry)
            self._access_order.append(key)
            
            # Evict oldest if over size limit
            while len(self._cache) > self.max_size:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]
    
    def delete(self, key: str):
        """Delete key from memory cache."""
        with self._lock:
            self._remove_key(key)
    
    def _remove_key(self, key: str):
        """Remove key from cache and access order."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


class CacheManager:
    """
    Enterprise cache manager with multi-level caching and Redis integration.
    
    Features:
    - Multi-level caching (Memory + Redis)
    - Circuit breaker for fault tolerance
    - Performance metrics and monitoring
    - Tenant-aware cache keys
    - Compression for large data
    - Async operations with thread pool
    - Redis cluster/sentinel support
    """
    
    def __init__(self, config: CacheConfig):
        """
        Initialize cache manager.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.metrics = CacheMetrics()
        
        # Initialize components
        self._memory_cache = MemoryCache(config.max_memory_cache_size)
        self._redis_client = self._initialize_redis()
        self._circuit_breaker = CircuitBreaker(config.circuit_breaker_threshold)
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="cache-mgr")
        
        # Thread-local tenant context
        self._local = threading.local()
        
        logger.info("Cache manager initialized successfully")
    
    def _initialize_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis client with proper configuration."""
        try:
            if self.config.redis_cluster_nodes:
                # Redis Cluster mode
                return RedisCluster(
                    startup_nodes=[{"host": node.split(":")[0], "port": int(node.split(":")[1])} 
                                 for node in self.config.redis_cluster_nodes],
                    decode_responses=False,
                    skip_full_coverage_check=True
                )
            
            elif self.config.redis_sentinel_hosts:
                # Redis Sentinel mode
                sentinel = Sentinel([
                    tuple(host.split(":")) for host in self.config.redis_sentinel_hosts
                ])
                return sentinel.master_for('mymaster', decode_responses=False)
            
            elif self.config.redis_url:
                # Single Redis instance
                return redis.from_url(
                    self.config.redis_url,
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            
            else:
                # Try to use environment variables
                redis_url = os.getenv("REDIS_URL")
                if redis_url:
                    return redis.from_url(
                        redis_url,
                        decode_responses=False,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                
                logger.warning("No Redis configuration provided, Redis caching disabled")
                return None
                
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            return None
    
    def set_tenant_context(self, tenant_id: UUID, organization_id: UUID):
        """Set tenant context for cache operations."""
        self._local.tenant_id = tenant_id
        self._local.organization_id = organization_id
    
    def _get_tenant_key(self, key: str) -> str:
        """Get tenant-prefixed cache key."""
        if hasattr(self._local, 'organization_id') and self._local.organization_id:
            return f"tenant:{self._local.organization_id}:{key}"
        return f"global:{key}"
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value based on configuration."""
        try:
            if self.config.serialization_format == SerializationFormat.JSON:
                serialized = json.dumps(value, default=str).encode('utf-8')
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                serialized = pickle.dumps(value)
            else:
                # Default to JSON
                serialized = json.dumps(value, default=str).encode('utf-8')
            
            # Apply compression if enabled and data is large enough
            if (self.config.enable_compression and 
                len(serialized) > self.config.compression_threshold):
                import gzip
                serialized = gzip.compress(serialized)
            
            return serialized
            
        except Exception as e:
            logger.error(f"Serialization failed: {e}")
            raise
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value based on configuration."""
        try:
            # Try decompression first
            if self.config.enable_compression:
                try:
                    import gzip
                    data = gzip.decompress(data)
                except:
                    pass  # Data might not be compressed
            
            if self.config.serialization_format == SerializationFormat.JSON:
                return json.loads(data.decode('utf-8'))
            elif self.config.serialization_format == SerializationFormat.PICKLE:
                return pickle.loads(data)
            else:
                # Default to JSON
                return json.loads(data.decode('utf-8'))
                
        except Exception as e:
            logger.error(f"Deserialization failed: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with multi-level fallback.
        
        Args:
            key: Cache key
            default: Default value if not found
            
        Returns:
            Cached value or default
        """
        start_time = time.time()
        tenant_key = self._get_tenant_key(key)
        
        try:
            # L1: Check memory cache first
            value = self._memory_cache.get(tenant_key)
            if value is not None:
                self._update_metrics("hit", start_time)
                return value
            
            # L2: Check Redis cache
            if self._redis_client:
                try:
                    redis_value = self._circuit_breaker.call(
                        self._redis_client.get, tenant_key
                    )
                    if redis_value is not None:
                        # Deserialize and populate memory cache
                        value = self._deserialize_value(redis_value)
                        self._memory_cache.set(tenant_key, value, self.config.default_ttl_seconds)
                        self._update_metrics("hit", start_time)
                        return value
                except Exception as e:
                    logger.warning(f"Redis get failed for key {tenant_key}: {e}")
            
            # Cache miss
            self._update_metrics("miss", start_time)
            return default
            
        except Exception as e:
            logger.error(f"Cache get failed for key {tenant_key}: {e}")
            self._update_metrics("error", start_time)
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with multi-level storage.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        tenant_key = self._get_tenant_key(key)
        cache_ttl = ttl or self.config.default_ttl_seconds
        
        try:
            # L1: Set in memory cache
            self._memory_cache.set(tenant_key, value, cache_ttl)
            
            # L2: Set in Redis cache
            if self._redis_client:
                try:
                    serialized_value = self._serialize_value(value)
                    success = self._circuit_breaker.call(
                        self._redis_client.setex,
                        tenant_key,
                        cache_ttl,
                        serialized_value
                    )
                    if not success:
                        logger.warning(f"Redis set failed for key {tenant_key}")
                except Exception as e:
                    logger.warning(f"Redis set failed for key {tenant_key}: {e}")
            
            self._update_metrics("write", start_time)
            return True
            
        except Exception as e:
            logger.error(f"Cache set failed for key {tenant_key}: {e}")
            self._update_metrics("error", start_time)
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from all cache levels.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        tenant_key = self._get_tenant_key(key)
        
        try:
            # L1: Delete from memory cache
            self._memory_cache.delete(tenant_key)
            
            # L2: Delete from Redis cache
            if self._redis_client:
                try:
                    self._circuit_breaker.call(
                        self._redis_client.delete, tenant_key
                    )
                except Exception as e:
                    logger.warning(f"Redis delete failed for key {tenant_key}: {e}")
            
            self._update_metrics("delete", start_time)
            return True
            
        except Exception as e:
            logger.error(f"Cache delete failed for key {tenant_key}: {e}")
            self._update_metrics("error", start_time)
            return False
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl: Optional[int] = None) -> Any:
        """
        Get value from cache or set using factory function.
        
        Args:
            key: Cache key
            factory: Function to generate value if not in cache
            ttl: Time to live in seconds
            
        Returns:
            Cached or generated value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Generate new value
        new_value = factory()
        self.set(key, new_value, ttl)
        return new_value
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """
        Increment numeric value in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment
            ttl: Time to live for new keys
            
        Returns:
            New value after increment
        """
        tenant_key = self._get_tenant_key(key)
        cache_ttl = ttl or self.config.default_ttl_seconds
        
        try:
            if self._redis_client:
                # Use Redis atomic increment
                result = self._circuit_breaker.call(
                    self._redis_client.incr, tenant_key, amount
                )
                # Set TTL if this is a new key
                if result == amount:
                    self._redis_client.expire(tenant_key, cache_ttl)
                return result
            else:
                # Fallback to get/set pattern
                current = self.get(key, 0)
                new_value = current + amount
                self.set(key, new_value, cache_ttl)
                return new_value
                
        except Exception as e:
            logger.error(f"Cache increment failed for key {tenant_key}: {e}")
            return 0
    
    def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary of key-value pairs
        """
        result = {}
        tenant_keys = [self._get_tenant_key(key) for key in keys]
        
        # Check memory cache first
        for i, tenant_key in enumerate(tenant_keys):
            value = self._memory_cache.get(tenant_key)
            if value is not None:
                result[keys[i]] = value
        
        # Get remaining keys from Redis
        missing_keys = [keys[i] for i, key in enumerate(keys) if key not in result]
        if missing_keys and self._redis_client:
            try:
                missing_tenant_keys = [self._get_tenant_key(key) for key in missing_keys]
                redis_values = self._circuit_breaker.call(
                    self._redis_client.mget, missing_tenant_keys
                )
                
                for i, redis_value in enumerate(redis_values):
                    if redis_value is not None:
                        try:
                            value = self._deserialize_value(redis_value)
                            key = missing_keys[i]
                            result[key] = value
                            # Populate memory cache
                            self._memory_cache.set(
                                missing_tenant_keys[i], 
                                value, 
                                self.config.default_ttl_seconds
                            )
                        except Exception as e:
                            logger.warning(f"Failed to deserialize value for key {missing_keys[i]}: {e}")
                            
            except Exception as e:
                logger.error(f"Redis mget failed: {e}")
        
        return result
    
    def set_many(self, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            data: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        cache_ttl = ttl or self.config.default_ttl_seconds
        
        try:
            # Set in memory cache
            for key, value in data.items():
                tenant_key = self._get_tenant_key(key)
                self._memory_cache.set(tenant_key, value, cache_ttl)
            
            # Set in Redis cache
            if self._redis_client:
                try:
                    # Prepare Redis pipeline
                    pipe = self._redis_client.pipeline()
                    for key, value in data.items():
                        tenant_key = self._get_tenant_key(key)
                        serialized_value = self._serialize_value(value)
                        pipe.setex(tenant_key, cache_ttl, serialized_value)
                    
                    self._circuit_breaker.call(pipe.execute)
                except Exception as e:
                    logger.warning(f"Redis mset failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set_many failed: {e}")
            return False
    
    def clear_tenant_cache(self, tenant_id: UUID):
        """Clear all cache entries for a specific tenant."""
        pattern = f"tenant:{tenant_id}:*"
        
        try:
            # Clear memory cache
            keys_to_delete = [key for key in self._memory_cache._cache.keys() 
                            if key.startswith(pattern.replace("*", ""))]
            for key in keys_to_delete:
                self._memory_cache.delete(key)
            
            # Clear Redis cache
            if self._redis_client:
                try:
                    keys = self._circuit_breaker.call(
                        self._redis_client.keys, pattern
                    )
                    if keys:
                        self._circuit_breaker.call(
                            self._redis_client.delete, *keys
                        )
                except Exception as e:
                    logger.warning(f"Redis clear tenant cache failed: {e}")
            
            logger.info(f"Cleared cache for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to clear tenant cache for {tenant_id}: {e}")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        health = {
            "memory_cache": {"status": "healthy", "size": self._memory_cache.size()},
            "redis_cache": {"status": "unknown"},
            "circuit_breaker": {"state": self._circuit_breaker.state},
            "metrics": asdict(self.metrics)
        }
        
        # Test Redis connectivity
        if self._redis_client:
            try:
                start_time = time.time()
                self._redis_client.ping()
                response_time = (time.time() - start_time) * 1000
                health["redis_cache"] = {
                    "status": "healthy",
                    "response_time_ms": round(response_time, 2)
                }
            except Exception as e:
                health["redis_cache"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        else:
            health["redis_cache"]["status"] = "disabled"
        
        return health
    
    def _update_metrics(self, operation: str, start_time: float):
        """Update cache metrics."""
        if not self.config.enable_metrics:
            return
        
        response_time = (time.time() - start_time) * 1000  # milliseconds
        
        if operation == "hit":
            self.metrics.hits += 1
        elif operation == "miss":
            self.metrics.misses += 1
        elif operation == "write":
            self.metrics.writes += 1
        elif operation == "delete":
            self.metrics.deletes += 1
        elif operation == "error":
            self.metrics.errors += 1
        
        self.metrics.total_operations += 1
        
        # Update rolling average response time
        if self.metrics.total_operations == 1:
            self.metrics.avg_response_time_ms = response_time
        else:
            self.metrics.avg_response_time_ms = (
                (self.metrics.avg_response_time_ms * (self.metrics.total_operations - 1) + response_time) 
                / self.metrics.total_operations
            )
    
    def get_metrics(self) -> CacheMetrics:
        """Get current cache metrics."""
        # Update memory usage
        self.metrics.memory_usage_mb = self._memory_cache.size() * 0.001  # Rough estimate
        
        # Get Redis memory usage if available
        if self._redis_client:
            try:
                info = self._redis_client.info('memory')
                self.metrics.redis_memory_usage_mb = info.get('used_memory', 0) / (1024 * 1024)
            except:
                pass
        
        return self.metrics
    
    def reset_metrics(self):
        """Reset cache metrics."""
        self.metrics = CacheMetrics()
    
    def close(self):
        """Cleanup resources."""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        self._memory_cache.clear()
        
        if self._redis_client:
            try:
                self._redis_client.close()
            except:
                pass


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> Optional[CacheManager]:
    """Get global cache manager instance."""
    return _cache_manager


def initialize_cache_manager(config: CacheConfig) -> CacheManager:
    """Initialize global cache manager."""
    global _cache_manager
    _cache_manager = CacheManager(config)
    return _cache_manager