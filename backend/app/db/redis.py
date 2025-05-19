"""Redis client for caching and token management."""
import redis # type: ignore
from functools import lru_cache

from app.core.config import settings

@lru_cache
def get_redis_client():
    """
    Get a Redis client instance.
    Uses connection pooling and caching for efficiency.
    Priority is given to REDIS_URL if available (for Railway integration).
    """
    if settings.REDIS_URL:
        # Use REDIS_URL from Railway or other cloud provider
        return redis.from_url(
            settings.REDIS_URL,
            decode_responses=True
        )
    
    # Fall back to individual connection parameters
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    )