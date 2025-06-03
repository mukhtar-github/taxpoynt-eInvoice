"""
Signature Caching Module for TaxPoynt eInvoice.

This module provides a caching layer for digital signatures:
- LRU cache for frequently used signatures
- Redis-based distributed cache for high volume environments
- Time-based expiration policies
- Cache invalidation based on certificate changes
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Union, Tuple
from functools import lru_cache
from datetime import datetime, timedelta
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings
from app.utils.crypto_signing import sign_invoice, CSIDVersion, SigningAlgorithm

logger = logging.getLogger(__name__)

# Local in-memory cache
_signature_cache = {}
_cache_lock = threading.RLock()
_cache_metrics = {
    'hits': 0,
    'misses': 0,
    'entries': 0,
}

# Default cache settings
DEFAULT_CACHE_SIZE = 1000
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds


def _generate_cache_key(invoice_data: Dict, algorithm: Any, version: Any) -> str:
    """
    Generate a unique cache key for invoice data.
    
    Args:
        invoice_data: Invoice data dictionary
        algorithm: Signing algorithm
        version: CSID version
    
    Returns:
        Unique hash for this invoice+algorithm+version combination
    """
    # Create a canonical representation of the invoice
    filtered_data = {k: v for k, v in invoice_data.items() if k not in 
                     ['signature', 'csid', 'cryptographic_stamp', 'digital_signature']}
    
    # Add algorithm and version to the key
    key_data = {
        'invoice': filtered_data,
        'algorithm': algorithm.value if hasattr(algorithm, 'value') else algorithm,
        'version': version.value if hasattr(version, 'value') else version
    }
    
    # Generate key as SHA-256 hash of canonical JSON
    canonical = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def get_cached_signature(
    invoice_data: Dict,
    algorithm: Any = SigningAlgorithm.RSA_PSS_SHA256,
    version: Any = CSIDVersion.V2_0,
    redis_client: Optional[Any] = None
) -> Optional[Dict]:
    """
    Get a cached signature for invoice if available.
    
    Args:
        invoice_data: Invoice data
        algorithm: Signing algorithm
        version: CSID version
        redis_client: Optional Redis client for distributed cache
        
    Returns:
        Cached signed invoice or None if not found
    """
    cache_key = _generate_cache_key(invoice_data, algorithm, version)
    
    # Try local cache first
    with _cache_lock:
        if cache_key in _signature_cache:
            entry = _signature_cache[cache_key]
            # Check if entry is still valid
            if entry['expiry'] > time.time():
                _cache_metrics['hits'] += 1
                # Return a deep copy to prevent cache corruption
                return json.loads(json.dumps(entry['data']))
            else:
                # Expired entry, remove it
                del _signature_cache[cache_key]
    
    # Try Redis if available
    if redis_client and REDIS_AVAILABLE:
        try:
            redis_key = f"signature_cache:{cache_key}"
            cached_data = redis_client.get(redis_key)
            if cached_data:
                _cache_metrics['hits'] += 1
                # Store in local cache for faster subsequent access
                with _cache_lock:
                    _signature_cache[cache_key] = {
                        'data': json.loads(cached_data),
                        'expiry': time.time() + DEFAULT_CACHE_TTL
                    }
                    _cache_metrics['entries'] = len(_signature_cache)
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Redis cache error: {str(e)}")
    
    _cache_metrics['misses'] += 1
    return None


def cache_signature(
    invoice_data: Dict,
    signed_invoice: Dict,
    algorithm: Any = SigningAlgorithm.RSA_PSS_SHA256,
    version: Any = CSIDVersion.V2_0,
    ttl: int = DEFAULT_CACHE_TTL,
    redis_client: Optional[Any] = None
) -> None:
    """
    Cache a signature for future use.
    
    Args:
        invoice_data: Original invoice data
        signed_invoice: Signed invoice data
        algorithm: Signing algorithm
        version: CSID version
        ttl: Time-to-live in seconds
        redis_client: Optional Redis client for distributed cache
    """
    cache_key = _generate_cache_key(invoice_data, algorithm, version)
    expiry = time.time() + ttl
    
    # Store in local cache
    with _cache_lock:
        # Check if we need to evict entries
        if len(_signature_cache) >= DEFAULT_CACHE_SIZE:
            # Simple LRU eviction - remove oldest entry
            oldest_key = min(_signature_cache.keys(), key=lambda k: _signature_cache[k]['expiry'])
            del _signature_cache[oldest_key]
        
        _signature_cache[cache_key] = {
            'data': signed_invoice,
            'expiry': expiry
        }
        _cache_metrics['entries'] = len(_signature_cache)
    
    # Store in Redis if available
    if redis_client and REDIS_AVAILABLE:
        try:
            redis_key = f"signature_cache:{cache_key}"
            redis_client.setex(
                redis_key,
                ttl,
                json.dumps(signed_invoice)
            )
        except Exception as e:
            logger.warning(f"Redis cache error: {str(e)}")


def cached_sign_invoice(
    invoice_data: Dict,
    algorithm: Any = SigningAlgorithm.RSA_PSS_SHA256,
    version: Any = CSIDVersion.V2_0,
    ttl: int = DEFAULT_CACHE_TTL,
    redis_client: Optional[Any] = None,
    skip_cache: bool = False
) -> Dict:
    """
    Sign an invoice with caching support.
    
    Args:
        invoice_data: Invoice data
        algorithm: Signing algorithm
        version: CSID version
        ttl: Cache time-to-live in seconds
        redis_client: Optional Redis client for distributed cache
        skip_cache: If True, bypass cache and generate new signature
        
    Returns:
        Signed invoice data
    """
    if not skip_cache:
        # Try to get from cache first
        cached = get_cached_signature(invoice_data, algorithm, version, redis_client)
        if cached:
            return cached
    
    # Generate new signature
    signed_invoice = sign_invoice(invoice_data, version, algorithm)
    
    # Cache the result
    cache_signature(invoice_data, signed_invoice, algorithm, version, ttl, redis_client)
    
    return signed_invoice


def get_cache_metrics() -> Dict[str, Any]:
    """
    Get current cache metrics.
    
    Returns:
        Dictionary with cache metrics
    """
    with _cache_lock:
        metrics = dict(_cache_metrics)
        
        # Calculate hit rate
        total_requests = metrics['hits'] + metrics['misses']
        if total_requests > 0:
            metrics['hit_rate'] = metrics['hits'] / total_requests
        else:
            metrics['hit_rate'] = 0
            
        return metrics


def clear_cache(redis_client: Optional[Any] = None) -> None:
    """
    Clear the signature cache.
    
    Args:
        redis_client: Optional Redis client for distributed cache
    """
    # Clear local cache
    with _cache_lock:
        _signature_cache.clear()
        _cache_metrics['entries'] = 0
    
    # Clear Redis cache if available
    if redis_client and REDIS_AVAILABLE:
        try:
            redis_client.delete("signature_cache:*")
        except Exception as e:
            logger.warning(f"Redis cache error during clear: {str(e)}")


def invalidate_cache_for_certificate(
    certificate_id: str,
    redis_client: Optional[Any] = None
) -> None:
    """
    Invalidate cache entries related to a specific certificate.
    Call this when a certificate is revoked or expired.
    
    Args:
        certificate_id: ID of the certificate
        redis_client: Optional Redis client for distributed cache
    """
    # Since we can't easily identify which entries use this certificate,
    # we'll just clear the entire cache for safety
    clear_cache(redis_client)
    logger.info(f"Cleared signature cache due to certificate change: {certificate_id}")
