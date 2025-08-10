"""
Hybrid Service: Cache Coordinator
Coordinates caching strategies across SI and APP roles
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
import hashlib
import time
import statistics

from core_platform.database import get_db_session
from core_platform.models.cache import CacheEntry, CachePolicy, CacheStatistics
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService
from core_platform.messaging import MessageQueue

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """Cache strategies"""
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"
    READ_THROUGH = "read_through"
    CACHE_ASIDE = "cache_aside"
    REFRESH_AHEAD = "refresh_ahead"


class CacheLevel(str, Enum):
    """Cache levels"""
    L1_LOCAL = "l1_local"
    L2_DISTRIBUTED = "l2_distributed"
    L3_PERSISTENT = "l3_persistent"
    CDN = "cdn"


class CacheScope(str, Enum):
    """Cache scope"""
    SI_ONLY = "si_only"
    APP_ONLY = "app_only"
    CROSS_ROLE = "cross_role"
    GLOBAL = "global"


class EvictionPolicy(str, Enum):
    """Cache eviction policies"""
    LRU = "lru"
    LFU = "lfu"
    FIFO = "fifo"
    TTL = "ttl"
    RANDOM = "random"
    CUSTOM = "custom"


class CacheStatus(str, Enum):
    """Cache entry status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    EVICTED = "evicted"
    INVALIDATED = "invalidated"
    STALE = "stale"


class SyncMode(str, Enum):
    """Cache synchronization modes"""
    IMMEDIATE = "immediate"
    EVENTUAL = "eventual"
    PERIODIC = "periodic"
    ON_DEMAND = "on_demand"


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    entry_id: str
    key: str
    value: Any
    cache_level: CacheLevel
    cache_scope: CacheScope
    ttl: int
    created_at: datetime
    accessed_at: datetime
    updated_at: datetime
    access_count: int
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.ttl <= 0:
            return False
        return (datetime.now(timezone.utc) - self.created_at).total_seconds() > self.ttl


@dataclass
class CachePolicy:
    """Cache policy configuration"""
    policy_id: str
    name: str
    cache_strategy: CacheStrategy
    eviction_policy: EvictionPolicy
    max_size: int
    default_ttl: int
    max_ttl: int
    sync_mode: SyncMode
    applicable_scopes: List[CacheScope]
    compression_enabled: bool
    encryption_enabled: bool
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheOperation:
    """Cache operation record"""
    operation_id: str
    operation_type: str
    key: str
    cache_level: CacheLevel
    cache_scope: CacheScope
    executed_at: datetime
    execution_time: float
    success: bool
    result_size: int
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheStatistics:
    """Cache statistics"""
    cache_level: CacheLevel
    cache_scope: CacheScope
    total_entries: int
    total_size: int
    hit_count: int
    miss_count: int
    eviction_count: int
    hit_rate: float
    miss_rate: float
    avg_access_time: float
    peak_memory_usage: int
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheInvalidation:
    """Cache invalidation request"""
    invalidation_id: str
    pattern: str
    cache_levels: List[CacheLevel]
    cache_scopes: List[CacheScope]
    invalidation_type: str
    requested_by: str
    requested_at: datetime
    reason: str
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CacheCoordinator:
    """
    Cache Coordinator service
    Coordinates caching strategies across SI and APP roles
    """
    
    def __init__(self):
        """Initialize cache coordinator service"""
        self.cache_services: Dict[CacheLevel, CacheService] = {}
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.message_queue = MessageQueue()
        self.logger = logging.getLogger(__name__)
        
        # Service state
        self.cache_policies: Dict[str, CachePolicy] = {}
        self.cache_entries: Dict[str, Dict[str, CacheEntry]] = {}  # level -> {key: entry}
        self.cache_operations: List[CacheOperation] = []
        self.cache_statistics: Dict[Tuple[CacheLevel, CacheScope], CacheStatistics] = {}
        self.invalidation_requests: Dict[str, CacheInvalidation] = {}
        self.is_initialized = False
        
        # Configuration
        self.max_operation_history = 10000
        self.statistics_interval = 60  # seconds
        self.cleanup_interval = 300  # 5 minutes
        self.replication_factor = 3
        
        # Initialize cache levels
        self._initialize_cache_levels()
        self._initialize_default_policies()
    
    def _initialize_cache_levels(self):
        """Initialize cache levels"""
        self.cache_entries = {
            CacheLevel.L1_LOCAL: {},
            CacheLevel.L2_DISTRIBUTED: {},
            CacheLevel.L3_PERSISTENT: {},
            CacheLevel.CDN: {}
        }
    
    def _initialize_default_policies(self):
        """Initialize default cache policies"""
        default_policies = [
            CachePolicy(
                policy_id="session_cache",
                name="Session Cache Policy",
                cache_strategy=CacheStrategy.WRITE_THROUGH,
                eviction_policy=EvictionPolicy.TTL,
                max_size=1000,
                default_ttl=3600,  # 1 hour
                max_ttl=86400,  # 24 hours
                sync_mode=SyncMode.IMMEDIATE,
                applicable_scopes=[CacheScope.SI_ONLY, CacheScope.APP_ONLY],
                compression_enabled=False,
                encryption_enabled=True,
                metadata={"category": "session"}
            ),
            
            CachePolicy(
                policy_id="cross_role_cache",
                name="Cross-Role Cache Policy",
                cache_strategy=CacheStrategy.READ_THROUGH,
                eviction_policy=EvictionPolicy.LRU,
                max_size=5000,
                default_ttl=1800,  # 30 minutes
                max_ttl=7200,  # 2 hours
                sync_mode=SyncMode.EVENTUAL,
                applicable_scopes=[CacheScope.CROSS_ROLE],
                compression_enabled=True,
                encryption_enabled=False,
                metadata={"category": "cross_role"}
            ),
            
            CachePolicy(
                policy_id="global_cache",
                name="Global Cache Policy",
                cache_strategy=CacheStrategy.CACHE_ASIDE,
                eviction_policy=EvictionPolicy.LFU,
                max_size=10000,
                default_ttl=7200,  # 2 hours
                max_ttl=86400,  # 24 hours
                sync_mode=SyncMode.PERIODIC,
                applicable_scopes=[CacheScope.GLOBAL],
                compression_enabled=True,
                encryption_enabled=False,
                metadata={"category": "global"}
            ),
            
            CachePolicy(
                policy_id="cdn_cache",
                name="CDN Cache Policy",
                cache_strategy=CacheStrategy.WRITE_AROUND,
                eviction_policy=EvictionPolicy.TTL,
                max_size=50000,
                default_ttl=86400,  # 24 hours
                max_ttl=604800,  # 7 days
                sync_mode=SyncMode.ON_DEMAND,
                applicable_scopes=[CacheScope.GLOBAL],
                compression_enabled=True,
                encryption_enabled=False,
                metadata={"category": "cdn"}
            )
        ]
        
        for policy in default_policies:
            self.cache_policies[policy.policy_id] = policy
    
    async def initialize(self):
        """Initialize the cache coordinator service"""
        if self.is_initialized:
            return
        
        self.logger.info("Initializing cache coordinator service")
        
        try:
            # Initialize cache services for each level
            for level in CacheLevel:
                cache_service = CacheService(
                    namespace=f"cache_{level.value}",
                    default_ttl=3600
                )
                await cache_service.initialize()
                self.cache_services[level] = cache_service
            
            # Initialize other dependencies
            await self.event_bus.initialize()
            await self.message_queue.initialize()
            
            # Setup message queues
            await self._setup_message_queues()
            
            # Register event handlers
            await self._register_event_handlers()
            
            # Start background tasks
            asyncio.create_task(self._statistics_collector())
            asyncio.create_task(self._cache_maintenance())
            asyncio.create_task(self._sync_coordinator())
            
            self.is_initialized = True
            self.logger.info("Cache coordinator service initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing cache coordinator service: {str(e)}")
            raise
    
    async def set_cache_policy(self, policy: CachePolicy):
        """Set cache policy"""
        try:
            self.cache_policies[policy.policy_id] = policy
            
            # Notify about policy change
            await self.event_bus.emit(
                "cache.policy_changed",
                {
                    "policy_id": policy.policy_id,
                    "policy_name": policy.name,
                    "applicable_scopes": policy.applicable_scopes
                }
            )
            
            self.logger.info(f"Cache policy set: {policy.name}")
            
        except Exception as e:
            self.logger.error(f"Error setting cache policy: {str(e)}")
            raise
    
    async def put(
        self,
        key: str,
        value: Any,
        cache_level: CacheLevel = CacheLevel.L1_LOCAL,
        cache_scope: CacheScope = CacheScope.SI_ONLY,
        ttl: Optional[int] = None,
        policy_id: Optional[str] = None
    ) -> bool:
        """Put value in cache"""
        try:
            start_time = time.time()
            
            # Get applicable policy
            policy = await self._get_applicable_policy(cache_scope, policy_id)
            
            # Calculate TTL
            effective_ttl = ttl or policy.default_ttl
            if effective_ttl > policy.max_ttl:
                effective_ttl = policy.max_ttl
            
            # Serialize value
            serialized_value = await self._serialize_value(value, policy)
            
            # Calculate size and checksum
            size_bytes = len(json.dumps(serialized_value).encode())
            checksum = hashlib.sha256(json.dumps(serialized_value, sort_keys=True).encode()).hexdigest()
            
            # Create cache entry
            cache_entry = CacheEntry(
                entry_id=str(uuid.uuid4()),
                key=key,
                value=serialized_value,
                cache_level=cache_level,
                cache_scope=cache_scope,
                ttl=effective_ttl,
                created_at=datetime.now(timezone.utc),
                accessed_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                access_count=0,
                size_bytes=size_bytes,
                checksum=checksum,
                metadata={"policy_id": policy.policy_id}
            )
            
            # Store in cache level
            cache_service = self.cache_services[cache_level]
            success = await cache_service.set(key, serialized_value, ttl=effective_ttl)
            
            if success:
                # Store entry metadata
                self.cache_entries[cache_level][key] = cache_entry
                
                # Execute cache strategy
                await self._execute_cache_strategy(
                    policy.cache_strategy,
                    "put",
                    key,
                    serialized_value,
                    cache_level,
                    cache_scope,
                    policy
                )
                
                # Record operation
                operation = CacheOperation(
                    operation_id=str(uuid.uuid4()),
                    operation_type="put",
                    key=key,
                    cache_level=cache_level,
                    cache_scope=cache_scope,
                    executed_at=datetime.now(timezone.utc),
                    execution_time=time.time() - start_time,
                    success=True,
                    result_size=size_bytes,
                    metadata={"policy_id": policy.policy_id}
                )
                
                await self._record_operation(operation)
                
                # Emit cache event
                await self.event_bus.emit(
                    "cache.entry_created",
                    {
                        "key": key,
                        "cache_level": cache_level,
                        "cache_scope": cache_scope,
                        "size_bytes": size_bytes
                    }
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error putting cache entry: {str(e)}")
            
            # Record failed operation
            operation = CacheOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="put",
                key=key,
                cache_level=cache_level,
                cache_scope=cache_scope,
                executed_at=datetime.now(timezone.utc),
                execution_time=time.time() - start_time,
                success=False,
                result_size=0,
                error_message=str(e)
            )
            
            await self._record_operation(operation)
            return False
    
    async def get(
        self,
        key: str,
        cache_level: CacheLevel = CacheLevel.L1_LOCAL,
        cache_scope: CacheScope = CacheScope.SI_ONLY,
        policy_id: Optional[str] = None
    ) -> Optional[Any]:
        """Get value from cache"""
        try:
            start_time = time.time()
            
            # Get applicable policy
            policy = await self._get_applicable_policy(cache_scope, policy_id)
            
            # Try to get from specified cache level first
            cache_service = self.cache_services[cache_level]
            value = await cache_service.get(key)
            
            if value is not None:
                # Cache hit
                await self._record_cache_hit(key, cache_level, cache_scope)
                
                # Update access metadata
                if key in self.cache_entries[cache_level]:
                    entry = self.cache_entries[cache_level][key]
                    entry.accessed_at = datetime.now(timezone.utc)
                    entry.access_count += 1
                
                # Deserialize value
                deserialized_value = await self._deserialize_value(value, policy)
                
                # Record operation
                operation = CacheOperation(
                    operation_id=str(uuid.uuid4()),
                    operation_type="get_hit",
                    key=key,
                    cache_level=cache_level,
                    cache_scope=cache_scope,
                    executed_at=datetime.now(timezone.utc),
                    execution_time=time.time() - start_time,
                    success=True,
                    result_size=len(json.dumps(value).encode()) if value else 0,
                    metadata={"policy_id": policy.policy_id}
                )
                
                await self._record_operation(operation)
                
                return deserialized_value
            
            # Cache miss - try other levels if strategy allows
            if policy.cache_strategy == CacheStrategy.READ_THROUGH:
                return await self._read_through_cache(key, cache_level, cache_scope, policy)
            
            # Record cache miss
            await self._record_cache_miss(key, cache_level, cache_scope)
            
            operation = CacheOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="get_miss",
                key=key,
                cache_level=cache_level,
                cache_scope=cache_scope,
                executed_at=datetime.now(timezone.utc),
                execution_time=time.time() - start_time,
                success=True,
                result_size=0,
                metadata={"policy_id": policy.policy_id}
            )
            
            await self._record_operation(operation)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cache entry: {str(e)}")
            
            # Record failed operation
            operation = CacheOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="get_error",
                key=key,
                cache_level=cache_level,
                cache_scope=cache_scope,
                executed_at=datetime.now(timezone.utc),
                execution_time=time.time() - start_time,
                success=False,
                result_size=0,
                error_message=str(e)
            )
            
            await self._record_operation(operation)
            return None
    
    async def delete(
        self,
        key: str,
        cache_level: CacheLevel = CacheLevel.L1_LOCAL,
        cache_scope: CacheScope = CacheScope.SI_ONLY
    ) -> bool:
        """Delete value from cache"""
        try:
            start_time = time.time()
            
            # Delete from cache service
            cache_service = self.cache_services[cache_level]
            success = await cache_service.delete(key)
            
            # Remove from entries
            if key in self.cache_entries[cache_level]:
                del self.cache_entries[cache_level][key]
            
            # Record operation
            operation = CacheOperation(
                operation_id=str(uuid.uuid4()),
                operation_type="delete",
                key=key,
                cache_level=cache_level,
                cache_scope=cache_scope,
                executed_at=datetime.now(timezone.utc),
                execution_time=time.time() - start_time,
                success=success,
                result_size=0
            )
            
            await self._record_operation(operation)
            
            if success:
                # Emit cache event
                await self.event_bus.emit(
                    "cache.entry_deleted",
                    {
                        "key": key,
                        "cache_level": cache_level,
                        "cache_scope": cache_scope
                    }
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error deleting cache entry: {str(e)}")
            return False
    
    async def invalidate(
        self,
        pattern: str,
        cache_levels: List[CacheLevel] = None,
        cache_scopes: List[CacheScope] = None,
        reason: str = "manual"
    ) -> str:
        """Invalidate cache entries matching pattern"""
        try:
            if cache_levels is None:
                cache_levels = list(CacheLevel)
            if cache_scopes is None:
                cache_scopes = list(CacheScope)
            
            # Create invalidation request
            invalidation = CacheInvalidation(
                invalidation_id=str(uuid.uuid4()),
                pattern=pattern,
                cache_levels=cache_levels,
                cache_scopes=cache_scopes,
                invalidation_type="pattern",
                requested_by="system",
                requested_at=datetime.now(timezone.utc),
                reason=reason
            )
            
            self.invalidation_requests[invalidation.invalidation_id] = invalidation
            
            # Execute invalidation
            await self._execute_invalidation(invalidation)
            
            return invalidation.invalidation_id
            
        except Exception as e:
            self.logger.error(f"Error invalidating cache: {str(e)}")
            raise
    
    async def sync_across_roles(
        self,
        key: str,
        source_scope: CacheScope,
        target_scopes: List[CacheScope],
        sync_mode: SyncMode = SyncMode.EVENTUAL
    ) -> bool:
        """Synchronize cache entry across roles"""
        try:
            # Get value from source scope
            source_value = None
            
            # Find the cache level containing the key
            for level in CacheLevel:
                if key in self.cache_entries[level]:
                    entry = self.cache_entries[level][key]
                    if entry.cache_scope == source_scope:
                        source_value = entry.value
                        break
            
            if source_value is None:
                return False
            
            # Sync to target scopes
            sync_success = True
            
            for target_scope in target_scopes:
                try:
                    # Determine appropriate cache level for target scope
                    target_level = await self._determine_cache_level(target_scope)
                    
                    # Put value in target scope
                    success = await self.put(
                        key,
                        source_value,
                        cache_level=target_level,
                        cache_scope=target_scope
                    )
                    
                    if not success:
                        sync_success = False
                        
                except Exception as e:
                    self.logger.error(f"Error syncing to scope {target_scope}: {str(e)}")
                    sync_success = False
            
            # Emit sync event
            await self.event_bus.emit(
                "cache.synced",
                {
                    "key": key,
                    "source_scope": source_scope,
                    "target_scopes": target_scopes,
                    "sync_mode": sync_mode,
                    "success": sync_success
                }
            )
            
            return sync_success
            
        except Exception as e:
            self.logger.error(f"Error syncing across roles: {str(e)}")
            return False
    
    async def get_cache_statistics(
        self,
        cache_level: CacheLevel = None,
        cache_scope: CacheScope = None
    ) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            if cache_level and cache_scope:
                # Get specific statistics
                key = (cache_level, cache_scope)
                if key in self.cache_statistics:
                    return self.cache_statistics[key].to_dict()
                else:
                    return {}
            
            # Get all statistics
            all_stats = {}
            for (level, scope), stats in self.cache_statistics.items():
                key = f"{level.value}_{scope.value}"
                all_stats[key] = stats.to_dict()
            
            # Add global statistics
            all_stats["global"] = await self._calculate_global_statistics()
            
            return all_stats
            
        except Exception as e:
            self.logger.error(f"Error getting cache statistics: {str(e)}")
            return {}
    
    async def optimize_cache(
        self,
        cache_level: CacheLevel = None,
        optimization_type: str = "automatic"
    ) -> Dict[str, Any]:
        """Optimize cache performance"""
        try:
            optimization_results = {
                "optimization_type": optimization_type,
                "executed_at": datetime.now(timezone.utc).isoformat(),
                "optimizations": []
            }
            
            levels_to_optimize = [cache_level] if cache_level else list(CacheLevel)
            
            for level in levels_to_optimize:
                try:
                    # Get cache statistics for this level
                    stats = await self._calculate_level_statistics(level)
                    
                    # Determine optimization actions
                    optimizations = []
                    
                    # Check hit rate
                    if stats.hit_rate < 0.5:  # Less than 50% hit rate
                        optimizations.append({
                            "action": "adjust_ttl",
                            "reason": "low_hit_rate",
                            "current_hit_rate": stats.hit_rate
                        })
                    
                    # Check memory usage
                    if stats.total_size > 1000000:  # More than 1MB
                        optimizations.append({
                            "action": "evict_lru",
                            "reason": "high_memory_usage",
                            "current_size": stats.total_size
                        })
                    
                    # Check access patterns
                    if stats.avg_access_time > 100:  # More than 100ms
                        optimizations.append({
                            "action": "redistribute_entries",
                            "reason": "slow_access",
                            "current_avg_time": stats.avg_access_time
                        })
                    
                    # Execute optimizations
                    for optimization in optimizations:
                        await self._execute_optimization(level, optimization)
                    
                    optimization_results["optimizations"].append({
                        "cache_level": level,
                        "actions": optimizations
                    })
                    
                except Exception as e:
                    self.logger.error(f"Error optimizing cache level {level}: {str(e)}")
            
            return optimization_results
            
        except Exception as e:
            self.logger.error(f"Error optimizing cache: {str(e)}")
            return {}
    
    async def _get_applicable_policy(
        self,
        cache_scope: CacheScope,
        policy_id: Optional[str] = None
    ) -> CachePolicy:
        """Get applicable cache policy"""
        try:
            if policy_id and policy_id in self.cache_policies:
                return self.cache_policies[policy_id]
            
            # Find policy by scope
            for policy in self.cache_policies.values():
                if cache_scope in policy.applicable_scopes:
                    return policy
            
            # Default policy
            return CachePolicy(
                policy_id="default",
                name="Default Policy",
                cache_strategy=CacheStrategy.CACHE_ASIDE,
                eviction_policy=EvictionPolicy.LRU,
                max_size=1000,
                default_ttl=3600,
                max_ttl=86400,
                sync_mode=SyncMode.EVENTUAL,
                applicable_scopes=[cache_scope],
                compression_enabled=False,
                encryption_enabled=False
            )
            
        except Exception as e:
            self.logger.error(f"Error getting applicable policy: {str(e)}")
            raise
    
    async def _serialize_value(self, value: Any, policy: CachePolicy) -> Any:
        """Serialize value based on policy"""
        try:
            serialized = value
            
            # Apply compression if enabled
            if policy.compression_enabled:
                import gzip
                import base64
                
                json_str = json.dumps(value)
                compressed = gzip.compress(json_str.encode())
                serialized = base64.b64encode(compressed).decode()
            
            # Apply encryption if enabled
            if policy.encryption_enabled:
                # Simplified encryption - use proper encryption in production
                import base64
                encrypted = base64.b64encode(str(serialized).encode()).decode()
                serialized = encrypted
            
            return serialized
            
        except Exception as e:
            self.logger.error(f"Error serializing value: {str(e)}")
            return value
    
    async def _deserialize_value(self, value: Any, policy: CachePolicy) -> Any:
        """Deserialize value based on policy"""
        try:
            deserialized = value
            
            # Apply decryption if enabled
            if policy.encryption_enabled:
                import base64
                decrypted = base64.b64decode(value).decode()
                deserialized = decrypted
            
            # Apply decompression if enabled
            if policy.compression_enabled:
                import gzip
                import base64
                
                compressed = base64.b64decode(deserialized)
                json_str = gzip.decompress(compressed).decode()
                deserialized = json.loads(json_str)
            
            return deserialized
            
        except Exception as e:
            self.logger.error(f"Error deserializing value: {str(e)}")
            return value
    
    async def _execute_cache_strategy(
        self,
        strategy: CacheStrategy,
        operation: str,
        key: str,
        value: Any,
        cache_level: CacheLevel,
        cache_scope: CacheScope,
        policy: CachePolicy
    ):
        """Execute cache strategy"""
        try:
            if strategy == CacheStrategy.WRITE_THROUGH:
                # Write to all levels
                for level in CacheLevel:
                    if level != cache_level:
                        cache_service = self.cache_services[level]
                        await cache_service.set(key, value, ttl=policy.default_ttl)
            
            elif strategy == CacheStrategy.WRITE_BACK:
                # Write only to specified level, sync later
                pass
            
            elif strategy == CacheStrategy.WRITE_AROUND:
                # Skip cache, write directly to persistent storage
                pass
            
            elif strategy == CacheStrategy.READ_THROUGH:
                # Read from next level if miss
                pass
            
            elif strategy == CacheStrategy.CACHE_ASIDE:
                # Application manages cache
                pass
            
            elif strategy == CacheStrategy.REFRESH_AHEAD:
                # Refresh before expiry
                await self._schedule_refresh(key, cache_level, cache_scope, policy)
            
        except Exception as e:
            self.logger.error(f"Error executing cache strategy: {str(e)}")
    
    async def _read_through_cache(
        self,
        key: str,
        cache_level: CacheLevel,
        cache_scope: CacheScope,
        policy: CachePolicy
    ) -> Optional[Any]:
        """Read through cache levels"""
        try:
            # Try other cache levels
            for level in CacheLevel:
                if level != cache_level:
                    cache_service = self.cache_services[level]
                    value = await cache_service.get(key)
                    
                    if value is not None:
                        # Found in another level, populate current level
                        await self.put(key, value, cache_level, cache_scope)
                        return await self._deserialize_value(value, policy)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error in read through cache: {str(e)}")
            return None
    
    async def _execute_invalidation(self, invalidation: CacheInvalidation):
        """Execute cache invalidation"""
        try:
            invalidated_count = 0
            
            for cache_level in invalidation.cache_levels:
                cache_service = self.cache_services[cache_level]
                
                # Get all keys in this level
                keys_to_invalidate = []
                
                for key in self.cache_entries[cache_level]:
                    # Check if key matches pattern
                    if self._matches_pattern(key, invalidation.pattern):
                        # Check if scope matches
                        entry = self.cache_entries[cache_level][key]
                        if entry.cache_scope in invalidation.cache_scopes:
                            keys_to_invalidate.append(key)
                
                # Invalidate matching keys
                for key in keys_to_invalidate:
                    await cache_service.delete(key)
                    if key in self.cache_entries[cache_level]:
                        del self.cache_entries[cache_level][key]
                    invalidated_count += 1
            
            # Emit invalidation event
            await self.event_bus.emit(
                "cache.invalidated",
                {
                    "invalidation_id": invalidation.invalidation_id,
                    "pattern": invalidation.pattern,
                    "invalidated_count": invalidated_count
                }
            )
            
            self.logger.info(f"Invalidated {invalidated_count} cache entries")
            
        except Exception as e:
            self.logger.error(f"Error executing invalidation: {str(e)}")
    
    def _matches_pattern(self, key: str, pattern: str) -> bool:
        """Check if key matches pattern"""
        try:
            import re
            
            # Convert glob pattern to regex
            regex_pattern = pattern.replace('*', '.*').replace('?', '.')
            return bool(re.match(regex_pattern, key))
            
        except Exception as e:
            self.logger.error(f"Error matching pattern: {str(e)}")
            return False
    
    async def _determine_cache_level(self, cache_scope: CacheScope) -> CacheLevel:
        """Determine appropriate cache level for scope"""
        try:
            if cache_scope == CacheScope.SI_ONLY:
                return CacheLevel.L1_LOCAL
            elif cache_scope == CacheScope.APP_ONLY:
                return CacheLevel.L1_LOCAL
            elif cache_scope == CacheScope.CROSS_ROLE:
                return CacheLevel.L2_DISTRIBUTED
            elif cache_scope == CacheScope.GLOBAL:
                return CacheLevel.L3_PERSISTENT
            else:
                return CacheLevel.L1_LOCAL
                
        except Exception as e:
            self.logger.error(f"Error determining cache level: {str(e)}")
            return CacheLevel.L1_LOCAL
    
    async def _record_operation(self, operation: CacheOperation):
        """Record cache operation"""
        try:
            self.cache_operations.append(operation)
            
            # Limit operation history
            if len(self.cache_operations) > self.max_operation_history:
                self.cache_operations = self.cache_operations[-self.max_operation_history:]
            
            # Update metrics
            await self.metrics_collector.record_metric(
                "cache_operation",
                1,
                tags={
                    "operation_type": operation.operation_type,
                    "cache_level": operation.cache_level,
                    "cache_scope": operation.cache_scope,
                    "success": operation.success
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error recording operation: {str(e)}")
    
    async def _record_cache_hit(self, key: str, cache_level: CacheLevel, cache_scope: CacheScope):
        """Record cache hit"""
        try:
            stats_key = (cache_level, cache_scope)
            
            if stats_key not in self.cache_statistics:
                self.cache_statistics[stats_key] = CacheStatistics(
                    cache_level=cache_level,
                    cache_scope=cache_scope,
                    total_entries=0,
                    total_size=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    miss_rate=0.0,
                    avg_access_time=0.0,
                    peak_memory_usage=0,
                    last_updated=datetime.now(timezone.utc)
                )
            
            stats = self.cache_statistics[stats_key]
            stats.hit_count += 1
            stats.hit_rate = stats.hit_count / (stats.hit_count + stats.miss_count)
            stats.miss_rate = stats.miss_count / (stats.hit_count + stats.miss_count)
            stats.last_updated = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error recording cache hit: {str(e)}")
    
    async def _record_cache_miss(self, key: str, cache_level: CacheLevel, cache_scope: CacheScope):
        """Record cache miss"""
        try:
            stats_key = (cache_level, cache_scope)
            
            if stats_key not in self.cache_statistics:
                self.cache_statistics[stats_key] = CacheStatistics(
                    cache_level=cache_level,
                    cache_scope=cache_scope,
                    total_entries=0,
                    total_size=0,
                    hit_count=0,
                    miss_count=0,
                    eviction_count=0,
                    hit_rate=0.0,
                    miss_rate=0.0,
                    avg_access_time=0.0,
                    peak_memory_usage=0,
                    last_updated=datetime.now(timezone.utc)
                )
            
            stats = self.cache_statistics[stats_key]
            stats.miss_count += 1
            stats.hit_rate = stats.hit_count / (stats.hit_count + stats.miss_count)
            stats.miss_rate = stats.miss_count / (stats.hit_count + stats.miss_count)
            stats.last_updated = datetime.now(timezone.utc)
            
        except Exception as e:
            self.logger.error(f"Error recording cache miss: {str(e)}")
    
    async def _calculate_global_statistics(self) -> Dict[str, Any]:
        """Calculate global cache statistics"""
        try:
            total_entries = 0
            total_size = 0
            total_hits = 0
            total_misses = 0
            total_evictions = 0
            
            for stats in self.cache_statistics.values():
                total_entries += stats.total_entries
                total_size += stats.total_size
                total_hits += stats.hit_count
                total_misses += stats.miss_count
                total_evictions += stats.eviction_count
            
            total_requests = total_hits + total_misses
            
            return {
                "total_entries": total_entries,
                "total_size": total_size,
                "total_hits": total_hits,
                "total_misses": total_misses,
                "total_evictions": total_evictions,
                "global_hit_rate": (total_hits / total_requests) if total_requests > 0 else 0,
                "global_miss_rate": (total_misses / total_requests) if total_requests > 0 else 0,
                "cache_levels": len(CacheLevel),
                "cache_scopes": len(CacheScope),
                "total_policies": len(self.cache_policies)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating global statistics: {str(e)}")
            return {}
    
    async def _calculate_level_statistics(self, cache_level: CacheLevel) -> CacheStatistics:
        """Calculate statistics for a specific cache level"""
        try:
            entries = self.cache_entries[cache_level]
            
            total_entries = len(entries)
            total_size = sum(entry.size_bytes for entry in entries.values())
            
            # Calculate access times
            access_times = []
            for entry in entries.values():
                if entry.access_count > 0:
                    access_times.append(entry.access_count)
            
            avg_access_time = statistics.mean(access_times) if access_times else 0
            
            # Get aggregated statistics for this level
            level_stats = [
                stats for (level, scope), stats in self.cache_statistics.items()
                if level == cache_level
            ]
            
            total_hits = sum(stats.hit_count for stats in level_stats)
            total_misses = sum(stats.miss_count for stats in level_stats)
            total_evictions = sum(stats.eviction_count for stats in level_stats)
            
            total_requests = total_hits + total_misses
            
            return CacheStatistics(
                cache_level=cache_level,
                cache_scope=CacheScope.GLOBAL,  # Aggregated across all scopes
                total_entries=total_entries,
                total_size=total_size,
                hit_count=total_hits,
                miss_count=total_misses,
                eviction_count=total_evictions,
                hit_rate=(total_hits / total_requests) if total_requests > 0 else 0,
                miss_rate=(total_misses / total_requests) if total_requests > 0 else 0,
                avg_access_time=avg_access_time,
                peak_memory_usage=total_size,
                last_updated=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating level statistics: {str(e)}")
            return CacheStatistics(
                cache_level=cache_level,
                cache_scope=CacheScope.GLOBAL,
                total_entries=0,
                total_size=0,
                hit_count=0,
                miss_count=0,
                eviction_count=0,
                hit_rate=0.0,
                miss_rate=0.0,
                avg_access_time=0.0,
                peak_memory_usage=0,
                last_updated=datetime.now(timezone.utc)
            )
    
    async def _execute_optimization(self, cache_level: CacheLevel, optimization: Dict[str, Any]):
        """Execute cache optimization"""
        try:
            action = optimization["action"]
            
            if action == "adjust_ttl":
                # Adjust TTL for entries with low hit rates
                for key, entry in self.cache_entries[cache_level].items():
                    if entry.access_count < 2:  # Low access count
                        # Reduce TTL
                        new_ttl = max(300, entry.ttl // 2)  # Minimum 5 minutes
                        cache_service = self.cache_services[cache_level]
                        await cache_service.set(key, entry.value, ttl=new_ttl)
                        entry.ttl = new_ttl
            
            elif action == "evict_lru":
                # Evict least recently used entries
                entries = list(self.cache_entries[cache_level].values())
                entries.sort(key=lambda x: x.accessed_at)
                
                # Evict oldest 10%
                evict_count = max(1, len(entries) // 10)
                for i in range(evict_count):
                    entry = entries[i]
                    await self.delete(entry.key, cache_level, entry.cache_scope)
            
            elif action == "redistribute_entries":
                # Redistribute entries across cache levels
                entries = list(self.cache_entries[cache_level].items())
                
                # Move frequently accessed entries to higher levels
                for key, entry in entries:
                    if entry.access_count > 5:  # High access count
                        target_level = CacheLevel.L1_LOCAL
                        if target_level != cache_level:
                            await self.put(key, entry.value, target_level, entry.cache_scope)
                            await self.delete(key, cache_level, entry.cache_scope)
            
        except Exception as e:
            self.logger.error(f"Error executing optimization: {str(e)}")
    
    async def _schedule_refresh(
        self,
        key: str,
        cache_level: CacheLevel,
        cache_scope: CacheScope,
        policy: CachePolicy
    ):
        """Schedule cache refresh"""
        try:
            # Schedule refresh before TTL expires
            refresh_time = policy.default_ttl * 0.8  # Refresh at 80% of TTL
            
            await asyncio.sleep(refresh_time)
            
            # Refresh cache entry
            current_value = await self.get(key, cache_level, cache_scope)
            if current_value is not None:
                await self.put(key, current_value, cache_level, cache_scope)
            
        except Exception as e:
            self.logger.error(f"Error scheduling refresh: {str(e)}")
    
    async def _setup_message_queues(self):
        """Setup message queues for cache coordination"""
        try:
            # Create queues for cache coordination
            await self.message_queue.create_queue("cache_sync")
            await self.message_queue.create_queue("cache_invalidation")
            
            # Set up consumers
            await self.message_queue.subscribe(
                "cache_sync",
                self._handle_cache_sync_message
            )
            
            await self.message_queue.subscribe(
                "cache_invalidation",
                self._handle_cache_invalidation_message
            )
            
        except Exception as e:
            self.logger.error(f"Error setting up message queues: {str(e)}")
    
    async def _handle_cache_sync_message(self, message: Dict[str, Any]):
        """Handle cache sync message"""
        try:
            key = message.get("key")
            source_scope = CacheScope(message.get("source_scope"))
            target_scopes = [CacheScope(scope) for scope in message.get("target_scopes", [])]
            
            await self.sync_across_roles(key, source_scope, target_scopes)
            
        except Exception as e:
            self.logger.error(f"Error handling cache sync message: {str(e)}")
    
    async def _handle_cache_invalidation_message(self, message: Dict[str, Any]):
        """Handle cache invalidation message"""
        try:
            pattern = message.get("pattern")
            cache_levels = [CacheLevel(level) for level in message.get("cache_levels", [])]
            cache_scopes = [CacheScope(scope) for scope in message.get("cache_scopes", [])]
            reason = message.get("reason", "external")
            
            await self.invalidate(pattern, cache_levels, cache_scopes, reason)
            
        except Exception as e:
            self.logger.error(f"Error handling cache invalidation message: {str(e)}")
    
    async def _statistics_collector(self):
        """Background statistics collector"""
        while True:
            try:
                await asyncio.sleep(self.statistics_interval)
                
                # Update statistics for all cache levels and scopes
                for cache_level in CacheLevel:
                    for cache_scope in CacheScope:
                        stats_key = (cache_level, cache_scope)
                        
                        # Calculate current statistics
                        entries = [
                            entry for entry in self.cache_entries[cache_level].values()
                            if entry.cache_scope == cache_scope
                        ]
                        
                        total_entries = len(entries)
                        total_size = sum(entry.size_bytes for entry in entries)
                        
                        # Update statistics
                        if stats_key not in self.cache_statistics:
                            self.cache_statistics[stats_key] = CacheStatistics(
                                cache_level=cache_level,
                                cache_scope=cache_scope,
                                total_entries=total_entries,
                                total_size=total_size,
                                hit_count=0,
                                miss_count=0,
                                eviction_count=0,
                                hit_rate=0.0,
                                miss_rate=0.0,
                                avg_access_time=0.0,
                                peak_memory_usage=total_size,
                                last_updated=datetime.now(timezone.utc)
                            )
                        else:
                            stats = self.cache_statistics[stats_key]
                            stats.total_entries = total_entries
                            stats.total_size = total_size
                            stats.peak_memory_usage = max(stats.peak_memory_usage, total_size)
                            stats.last_updated = datetime.now(timezone.utc)
                            
                            # Calculate average access time
                            if entries:
                                access_times = [entry.access_count for entry in entries]
                                stats.avg_access_time = statistics.mean(access_times)
                
            except Exception as e:
                self.logger.error(f"Error in statistics collector: {str(e)}")
    
    async def _cache_maintenance(self):
        """Background cache maintenance"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Clean up expired entries
                for cache_level in CacheLevel:
                    expired_keys = []
                    
                    for key, entry in self.cache_entries[cache_level].items():
                        if entry.is_expired():
                            expired_keys.append(key)
                    
                    # Remove expired entries
                    for key in expired_keys:
                        await self.delete(key, cache_level)
                
                # Clean up old operations
                if len(self.cache_operations) > self.max_operation_history:
                    self.cache_operations = self.cache_operations[-self.max_operation_history:]
                
            except Exception as e:
                self.logger.error(f"Error in cache maintenance: {str(e)}")
    
    async def _sync_coordinator(self):
        """Background sync coordinator"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                
                # Check for entries that need synchronization
                for cache_level in CacheLevel:
                    for key, entry in self.cache_entries[cache_level].items():
                        # Check if entry needs cross-role sync
                        if entry.cache_scope == CacheScope.CROSS_ROLE:
                            # Check if sync is needed
                            time_since_update = (datetime.now(timezone.utc) - entry.updated_at).total_seconds()
                            
                            if time_since_update > 300:  # 5 minutes
                                # Sync to other scopes
                                await self.sync_across_roles(
                                    key,
                                    entry.cache_scope,
                                    [CacheScope.SI_ONLY, CacheScope.APP_ONLY]
                                )
                
            except Exception as e:
                self.logger.error(f"Error in sync coordinator: {str(e)}")
    
    async def _register_event_handlers(self):
        """Register event handlers"""
        try:
            await self.event_bus.subscribe(
                "cache.entry_created",
                self._handle_entry_created
            )
            
            await self.event_bus.subscribe(
                "cache.entry_deleted",
                self._handle_entry_deleted
            )
            
            await self.event_bus.subscribe(
                "cache.synced",
                self._handle_cache_synced
            )
            
        except Exception as e:
            self.logger.error(f"Error registering event handlers: {str(e)}")
    
    async def _handle_entry_created(self, event_data: Dict[str, Any]):
        """Handle cache entry created event"""
        try:
            key = event_data.get("key")
            cache_level = CacheLevel(event_data.get("cache_level"))
            cache_scope = CacheScope(event_data.get("cache_scope"))
            
            # Update statistics
            stats_key = (cache_level, cache_scope)
            if stats_key in self.cache_statistics:
                stats = self.cache_statistics[stats_key]
                stats.total_entries += 1
                stats.total_size += event_data.get("size_bytes", 0)
            
        except Exception as e:
            self.logger.error(f"Error handling entry created event: {str(e)}")
    
    async def _handle_entry_deleted(self, event_data: Dict[str, Any]):
        """Handle cache entry deleted event"""
        try:
            cache_level = CacheLevel(event_data.get("cache_level"))
            cache_scope = CacheScope(event_data.get("cache_scope"))
            
            # Update statistics
            stats_key = (cache_level, cache_scope)
            if stats_key in self.cache_statistics:
                stats = self.cache_statistics[stats_key]
                stats.total_entries = max(0, stats.total_entries - 1)
                stats.eviction_count += 1
            
        except Exception as e:
            self.logger.error(f"Error handling entry deleted event: {str(e)}")
    
    async def _handle_cache_synced(self, event_data: Dict[str, Any]):
        """Handle cache synced event"""
        try:
            self.logger.info(f"Cache synced: {event_data}")
            
        except Exception as e:
            self.logger.error(f"Error handling cache synced event: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get service health status"""
        try:
            # Check all cache services
            service_health = {}
            for level, service in self.cache_services.items():
                service_health[level.value] = await service.health_check()
            
            # Determine overall health
            overall_status = "healthy"
            for health in service_health.values():
                if health.get("status") == "error":
                    overall_status = "error"
                    break
                elif health.get("status") == "degraded":
                    overall_status = "degraded"
            
            return {
                "status": overall_status,
                "service": "cache_coordinator",
                "cache_services": service_health,
                "metrics": {
                    "total_entries": sum(len(entries) for entries in self.cache_entries.values()),
                    "total_policies": len(self.cache_policies),
                    "total_operations": len(self.cache_operations),
                    "active_invalidations": len(self.invalidation_requests)
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "cache_coordinator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self):
        """Cleanup service resources"""
        self.logger.info("Cache coordinator service cleanup initiated")
        
        try:
            # Clear all cache data
            for level in CacheLevel:
                self.cache_entries[level].clear()
            
            self.cache_operations.clear()
            self.cache_statistics.clear()
            self.invalidation_requests.clear()
            
            # Cleanup cache services
            for service in self.cache_services.values():
                await service.cleanup()
            
            self.is_initialized = False
            
            self.logger.info("Cache coordinator service cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_cache_coordinator() -> CacheCoordinator:
    """Create cache coordinator service"""
    return CacheCoordinator()