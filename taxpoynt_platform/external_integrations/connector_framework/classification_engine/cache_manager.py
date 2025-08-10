"""
Classification Cache Manager
===========================

Smart caching system with Redis integration for transaction classification.
Optimizes costs by caching similar transaction patterns and results.
"""

import json
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

try:
    import redis
    import redis.asyncio as aioredis
except ImportError:
    redis = None
    aioredis = None

from .classification_models import (
    TransactionClassificationRequest,
    TransactionClassificationResult,
    UserContext,
    PrivacyLevel
)

logger = logging.getLogger(__name__)

class CacheStrategy(str, Enum):
    """Cache strategy options"""
    CONSERVATIVE = "conservative"    # Cache only high-confidence results
    BALANCED = "balanced"           # Cache most results with reasonable confidence
    AGGRESSIVE = "aggressive"       # Cache all results for maximum cost savings

@dataclass
class CacheKey:
    """Cache key components for pattern matching"""
    
    amount_category: str
    narration_pattern: str
    time_category: str
    day_category: str
    business_context_hash: str
    privacy_level: str
    
    def __str__(self) -> str:
        """Generate cache key string"""
        key_components = [
            self.amount_category,
            self.narration_pattern,
            self.time_category,
            self.day_category,
            self.business_context_hash,
            self.privacy_level
        ]
        return f"tx_class:{':'.join(key_components)}"
    
    def __hash__(self) -> int:
        return hash(str(self))

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    
    cache_key: str
    result: TransactionClassificationResult
    created_at: datetime
    last_accessed: datetime
    access_count: int
    confidence_score: float
    user_confirmations: int
    user_corrections: int
    expires_at: Optional[datetime] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    @property
    def accuracy_score(self) -> float:
        """Calculate accuracy score based on user feedback"""
        total_feedback = self.user_confirmations + self.user_corrections
        if total_feedback == 0:
            return self.confidence_score
        return self.user_confirmations / total_feedback
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'cache_key': self.cache_key,
            'result': self.result.dict(),
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'confidence_score': self.confidence_score,
            'user_confirmations': self.user_confirmations,
            'user_corrections': self.user_corrections,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary"""
        result_data = data['result']
        result = TransactionClassificationResult(**result_data)
        
        return cls(
            cache_key=data['cache_key'],
            result=result,
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            access_count=data['access_count'],
            confidence_score=data['confidence_score'],
            user_confirmations=data['user_confirmations'],
            user_corrections=data['user_corrections'],
            expires_at=datetime.fromisoformat(data['expires_at']) if data['expires_at'] else None
        )

class ClassificationCacheManager:
    """
    Smart caching system for transaction classification results
    """
    
    def __init__(self, 
                 redis_url: Optional[str] = None,
                 strategy: CacheStrategy = CacheStrategy.BALANCED,
                 default_ttl_hours: int = 24,
                 max_cache_size: int = 100000):
        """Initialize cache manager"""
        
        self.strategy = strategy
        self.default_ttl_hours = default_ttl_hours
        self.max_cache_size = max_cache_size
        self.logger = logging.getLogger(f"{__name__}.ClassificationCacheManager")
        
        # Redis client setup
        self.redis_client = None
        self.async_redis_client = None
        
        if redis and redis_url:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.async_redis_client = aioredis.from_url(redis_url, decode_responses=True)
                self.redis_available = True
                self.logger.info("Redis cache initialized")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}. Using in-memory cache.")
                self.redis_available = False
        else:
            self.redis_available = False
            self.logger.info("Redis not available. Using in-memory cache.")
        
        # In-memory fallback cache
        self.memory_cache: Dict[str, CacheEntry] = {}
        
        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0,
            'total_cost_saved_ngn': Decimal('0.0')
        }
        
        self.logger.info(f"Cache manager initialized with {strategy} strategy")
    
    async def get_cached_result(self, 
                               request: TransactionClassificationRequest) -> Optional[TransactionClassificationResult]:
        """Get cached classification result if available"""
        
        try:
            # Generate cache key
            cache_key = await self._generate_cache_key(request)
            
            # Try to get from cache
            cache_entry = await self._get_cache_entry(str(cache_key))
            
            if cache_entry and not cache_entry.is_expired:
                # Update access statistics
                await self._update_access_stats(cache_entry)
                
                # Mark result as from cache
                result = cache_entry.result.copy(deep=True)
                result.metadata.cache_hit = True
                result.metadata.api_cost_estimate_ngn = Decimal('0.0')
                
                self.stats['hits'] += 1
                self.logger.debug(f"Cache hit for key: {cache_key}")
                
                return result
            
            self.stats['misses'] += 1
            self.logger.debug(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting cached result: {e}")
            return None
    
    async def cache_result(self, 
                          request: TransactionClassificationRequest,
                          result: TransactionClassificationResult) -> bool:
        """Cache classification result if it meets caching criteria"""
        
        try:
            # Check if result should be cached
            if not await self._should_cache_result(result):
                return False
            
            # Generate cache key
            cache_key = await self._generate_cache_key(request)
            
            # Create cache entry
            cache_entry = CacheEntry(
                cache_key=str(cache_key),
                result=result,
                created_at=datetime.utcnow(),
                last_accessed=datetime.utcnow(),
                access_count=1,
                confidence_score=result.confidence,
                user_confirmations=0,
                user_corrections=0,
                expires_at=datetime.utcnow() + timedelta(hours=self.default_ttl_hours)
            )
            
            # Store in cache
            success = await self._set_cache_entry(cache_entry)
            
            if success:
                self.stats['sets'] += 1
                self.logger.debug(f"Result cached with key: {cache_key}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error caching result: {e}")
            return False
    
    async def update_cache_with_feedback(self, 
                                       request: TransactionClassificationRequest,
                                       was_correct: bool) -> bool:
        """Update cache entry with user feedback"""
        
        try:
            cache_key = await self._generate_cache_key(request)
            cache_entry = await self._get_cache_entry(str(cache_key))
            
            if cache_entry:
                # Update feedback statistics
                if was_correct:
                    cache_entry.user_confirmations += 1
                else:
                    cache_entry.user_corrections += 1
                
                # If too many corrections, remove from cache
                if cache_entry.accuracy_score < 0.5:
                    await self._remove_cache_entry(str(cache_key))
                    self.logger.info(f"Removed low-accuracy cache entry: {cache_key}")
                    return True
                
                # Update cache entry
                await self._set_cache_entry(cache_entry)
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error updating cache with feedback: {e}")
            return False
    
    async def _generate_cache_key(self, request: TransactionClassificationRequest) -> CacheKey:
        """Generate cache key from transaction patterns"""
        
        # Categorize amount
        amount_category = self._categorize_amount(request.amount)
        
        # Extract narration pattern
        narration_pattern = self._extract_narration_pattern(request.narration)
        
        # Categorize time
        time_category = self._categorize_time(request.time, request.date)
        
        # Get day category
        day_category = self._get_day_category(request.date)
        
        # Hash business context
        business_context_hash = self._hash_business_context(request.user_context)
        
        # Privacy level
        privacy_level = request.privacy_level or PrivacyLevel.STANDARD
        
        return CacheKey(
            amount_category=amount_category,
            narration_pattern=narration_pattern,
            time_category=time_category,
            day_category=day_category,
            business_context_hash=business_context_hash,
            privacy_level=privacy_level.value
        )
    
    def _categorize_amount(self, amount: Decimal) -> str:
        """Categorize amount for cache key"""
        amount_float = float(amount)
        
        if amount_float < 5000:
            return "very_small"
        elif amount_float < 25000:
            return "small"
        elif amount_float < 100000:
            return "medium"
        elif amount_float < 500000:
            return "large"
        else:
            return "very_large"
    
    def _extract_narration_pattern(self, narration: str) -> str:
        """Extract pattern from narration for caching"""
        
        narration_lower = narration.lower().strip()
        
        # Business indicators
        business_keywords = [
            'payment', 'invoice', 'goods', 'services', 'business',
            'shop', 'market', 'contract', 'supply', 'delivery'
        ]
        
        # Personal indicators
        personal_keywords = [
            'salary', 'allowance', 'family', 'personal', 'loan',
            'refund', 'reversal', 'airtime', 'data'
        ]
        
        # Check for patterns
        business_count = sum(1 for keyword in business_keywords if keyword in narration_lower)
        personal_count = sum(1 for keyword in personal_keywords if keyword in narration_lower)
        
        if business_count > personal_count and business_count > 0:
            return "business_pattern"
        elif personal_count > business_count and personal_count > 0:
            return "personal_pattern"
        elif len(narration_lower.split()) <= 3:
            return "short_description"
        else:
            return "neutral_pattern"
    
    def _categorize_time(self, transaction_time: Optional[str], transaction_date: datetime) -> str:
        """Categorize time for cache key"""
        try:
            if not transaction_time or ':' not in transaction_time:
                return "unknown"
            
            hour = int(transaction_time.split(':')[0])
            
            if 8 <= hour <= 17:  # Business hours
                return "business_hours"
            elif 18 <= hour <= 22:  # Evening
                return "evening"
            else:  # Night/early morning
                return "off_hours"
        except Exception:
            return "unknown"
    
    def _get_day_category(self, transaction_date: datetime) -> str:
        """Get day category for cache key"""
        weekday = transaction_date.weekday()
        
        if weekday < 5:
            return "weekday"
        elif weekday == 5:
            return "saturday"
        else:
            return "sunday"
    
    def _hash_business_context(self, user_context: UserContext) -> str:
        """Generate hash of business context for cache key"""
        
        context_data = {
            'industry': user_context.business_context.industry,
            'business_size': user_context.business_context.business_size,
            'subscription_tier': user_context.subscription_tier
        }
        
        context_string = json.dumps(context_data, sort_keys=True)
        return hashlib.md5(context_string.encode()).hexdigest()[:8]
    
    async def _should_cache_result(self, result: TransactionClassificationResult) -> bool:
        """Determine if result should be cached based on strategy"""
        
        if self.strategy == CacheStrategy.CONSERVATIVE:
            # Cache only high-confidence results without human review flags
            return (result.confidence >= 0.8 and 
                   not result.requires_human_review and
                   len(result.risk_factors) == 0)
        
        elif self.strategy == CacheStrategy.BALANCED:
            # Cache most results with reasonable confidence
            return (result.confidence >= 0.6 and
                   len(result.risk_factors) <= 1)
        
        else:  # AGGRESSIVE
            # Cache all results for maximum cost savings
            return result.confidence >= 0.3
    
    async def _get_cache_entry(self, cache_key: str) -> Optional[CacheEntry]:
        """Get cache entry from storage"""
        
        try:
            if self.redis_available and self.async_redis_client:
                # Try Redis first
                data = await self.async_redis_client.get(cache_key)
                if data:
                    entry_dict = json.loads(data)
                    return CacheEntry.from_dict(entry_dict)
            
            # Fall back to memory cache
            return self.memory_cache.get(cache_key)
            
        except Exception as e:
            self.logger.error(f"Error getting cache entry: {e}")
            return None
    
    async def _set_cache_entry(self, cache_entry: CacheEntry) -> bool:
        """Set cache entry in storage"""
        
        try:
            entry_data = json.dumps(cache_entry.to_dict())
            
            if self.redis_available and self.async_redis_client:
                # Store in Redis with TTL
                ttl_seconds = self.default_ttl_hours * 3600
                await self.async_redis_client.setex(
                    cache_entry.cache_key, 
                    ttl_seconds, 
                    entry_data
                )
            
            # Also store in memory cache (with size limit)
            if len(self.memory_cache) >= self.max_cache_size:
                await self._evict_oldest_entries()
            
            self.memory_cache[cache_entry.cache_key] = cache_entry
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting cache entry: {e}")
            return False
    
    async def _remove_cache_entry(self, cache_key: str) -> bool:
        """Remove cache entry from storage"""
        
        try:
            if self.redis_available and self.async_redis_client:
                await self.async_redis_client.delete(cache_key)
            
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing cache entry: {e}")
            return False
    
    async def _update_access_stats(self, cache_entry: CacheEntry):
        """Update access statistics for cache entry"""
        
        cache_entry.last_accessed = datetime.utcnow()
        cache_entry.access_count += 1
        
        # Estimate cost savings (assuming ₦3.2 for premium API call)
        self.stats['total_cost_saved_ngn'] += Decimal('3.2')
    
    async def _evict_oldest_entries(self):
        """Evict oldest entries from memory cache"""
        
        if not self.memory_cache:
            return
        
        # Sort by last accessed time
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest 10% of entries
        evict_count = max(1, len(sorted_entries) // 10)
        
        for i in range(evict_count):
            cache_key = sorted_entries[i][0]
            del self.memory_cache[cache_key]
            self.stats['evictions'] += 1
        
        self.logger.debug(f"Evicted {evict_count} cache entries")
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / max(1, total_requests)) * 100
        
        memory_cache_size = len(self.memory_cache)
        
        # Redis cache size (if available)
        redis_cache_size = 0
        if self.redis_available and self.async_redis_client:
            try:
                # Count keys matching our pattern
                keys = await self.async_redis_client.keys("tx_class:*")
                redis_cache_size = len(keys)
            except Exception:
                pass
        
        return {
            'strategy': self.strategy,
            'hit_rate_percent': round(hit_rate, 2),
            'total_hits': self.stats['hits'],
            'total_misses': self.stats['misses'],
            'total_sets': self.stats['sets'],
            'total_evictions': self.stats['evictions'],
            'memory_cache_size': memory_cache_size,
            'redis_cache_size': redis_cache_size,
            'total_cost_saved_ngn': float(self.stats['total_cost_saved_ngn']),
            'average_cost_per_hit_ngn': (
                float(self.stats['total_cost_saved_ngn']) / max(1, self.stats['hits'])
            ),
            'redis_available': self.redis_available,
            'max_cache_size': self.max_cache_size,
            'default_ttl_hours': self.default_ttl_hours
        }
    
    async def clear_cache(self, pattern: Optional[str] = None) -> int:
        """Clear cache entries matching pattern"""
        
        cleared_count = 0
        
        try:
            if pattern:
                # Clear specific pattern
                if self.redis_available and self.async_redis_client:
                    keys = await self.async_redis_client.keys(f"tx_class:{pattern}*")
                    if keys:
                        await self.async_redis_client.delete(*keys)
                        cleared_count += len(keys)
                
                # Clear from memory cache
                keys_to_remove = [key for key in self.memory_cache.keys() if pattern in key]
                for key in keys_to_remove:
                    del self.memory_cache[key]
                    cleared_count += len(keys_to_remove)
            
            else:
                # Clear all cache
                if self.redis_available and self.async_redis_client:
                    keys = await self.async_redis_client.keys("tx_class:*")
                    if keys:
                        await self.async_redis_client.delete(*keys)
                        cleared_count += len(keys)
                
                cleared_count += len(self.memory_cache)
                self.memory_cache.clear()
            
            self.logger.info(f"Cleared {cleared_count} cache entries")
            return cleared_count
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return 0
    
    async def close(self):
        """Close cache connections"""
        
        try:
            if self.async_redis_client:
                await self.async_redis_client.close()
            
            self.logger.info("Cache manager closed")
            
        except Exception as e:
            self.logger.error(f"Error closing cache manager: {e}")