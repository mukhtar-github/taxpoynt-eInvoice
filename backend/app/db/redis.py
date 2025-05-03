"""Redis client for caching and token management."""
import redis # type: ignore
from functools import lru_cache

from app.core.config import settings

@lru_cache
def get_redis_client():
    """
    Get a Redis client instance.
    Uses connection pooling and caching for efficiency.
    """
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        decode_responses=True
    ) 