"""
IRN caching mechanism for efficient IRN generation and validation.

This module provides caching functionality for Invoice Reference Numbers (IRNs)
to improve performance and reduce database load during high-volume operations.
"""
import json
import logging
import hashlib
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.models.irn import IRNRecord, IRNStatus

logger = logging.getLogger(__name__)

# Default cache expiry (12 hours)
DEFAULT_CACHE_EXPIRY = 60 * 60 * 12

# Try to connect to Redis if configured, but don't fail if it's not available
redis_client = None

# Disable Redis connection attempts to bypass startup issues
logger.warning("Redis connection disabled to allow application startup. IRN caching will use in-memory cache.")


class IRNCache:
    """
    Cache manager for Invoice Reference Numbers.
    
    This class provides methods to cache IRN data and check for cached IRNs
    to avoid unnecessary database queries and improve performance.
    """
    
    @staticmethod
    def _get_invoice_cache_key(odoo_invoice_id: int, integration_id: str) -> str:
        """Generate a cache key for an invoice."""
        return f"irn:invoice:{integration_id}:{odoo_invoice_id}"
    
    @staticmethod
    def _get_irn_cache_key(irn_value: str) -> str:
        """Generate a cache key for an IRN."""
        return f"irn:value:{irn_value}"
    
    @staticmethod
    def _get_bulk_cache_key(batch_id: str) -> str:
        """Generate a cache key for a bulk generation job."""
        return f"irn:bulk:{batch_id}"
    
    @staticmethod
    def cache_irn(irn_record: IRNRecord, expiry: int = DEFAULT_CACHE_EXPIRY) -> bool:
        """
        Cache an IRN record.
        
        Args:
            irn_record: The IRN record to cache
            expiry: Cache expiry time in seconds (default: 12 hours)
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not redis_client:
            return False
            
        try:
            # Create serializable data from the IRN record
            data = {
                "irn": irn_record.irn,
                "integration_id": irn_record.integration_id,
                "invoice_number": irn_record.invoice_number,
                "service_id": irn_record.service_id,
                "timestamp": irn_record.timestamp,
                "generated_at": irn_record.generated_at.isoformat() if irn_record.generated_at else None,
                "valid_until": irn_record.valid_until.isoformat() if irn_record.valid_until else None,
                "status": irn_record.status.value,
                "odoo_invoice_id": irn_record.odoo_invoice_id
            }
            
            # Cache by IRN value
            irn_key = IRNCache._get_irn_cache_key(irn_record.irn)
            redis_client.setex(irn_key, expiry, json.dumps(data))
            
            # Also cache by invoice ID if available
            if irn_record.odoo_invoice_id:
                invoice_key = IRNCache._get_invoice_cache_key(
                    irn_record.odoo_invoice_id, 
                    irn_record.integration_id
                )
                redis_client.setex(invoice_key, expiry, json.dumps(data))
                
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error caching IRN {irn_record.irn}: {str(e)}")
            return False
    
    @staticmethod
    def get_cached_irn(irn_value: str) -> Optional[Dict[str, Any]]:
        """
        Get an IRN record from cache.
        
        Args:
            irn_value: The IRN value to look up
            
        Returns:
            Optional dict with IRN data if found, None otherwise
        """
        if not redis_client:
            return None
            
        try:
            key = IRNCache._get_irn_cache_key(irn_value)
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, Exception) as e:
            logger.error(f"Error retrieving cached IRN {irn_value}: {str(e)}")
            return None
    
    @staticmethod
    def get_cached_irn_for_invoice(odoo_invoice_id: int, integration_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached IRN data for an invoice.
        
        Args:
            odoo_invoice_id: Odoo invoice ID
            integration_id: Integration ID
            
        Returns:
            Optional dict with IRN data if found, None otherwise
        """
        if not redis_client:
            return None
            
        try:
            key = IRNCache._get_invoice_cache_key(odoo_invoice_id, integration_id)
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, Exception) as e:
            logger.error(f"Error retrieving cached IRN for invoice {odoo_invoice_id}: {str(e)}")
            return None
    
    @staticmethod
    def invalidate_irn_cache(irn_value: str) -> bool:
        """
        Remove an IRN from cache.
        
        Args:
            irn_value: The IRN value to invalidate
            
        Returns:
            bool: True if invalidation was successful, False otherwise
        """
        if not redis_client:
            return False
            
        try:
            key = IRNCache._get_irn_cache_key(irn_value)
            redis_client.delete(key)
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error invalidating cached IRN {irn_value}: {str(e)}")
            return False
    
    @staticmethod
    def cache_bulk_irn_status(batch_id: str, status: Dict[str, Any], expiry: int = DEFAULT_CACHE_EXPIRY * 2) -> bool:
        """
        Cache status of a bulk IRN generation job.
        
        Args:
            batch_id: ID of the bulk generation batch
            status: Status information to cache
            expiry: Cache expiry time in seconds
            
        Returns:
            bool: True if caching was successful, False otherwise
        """
        if not redis_client:
            return False
            
        try:
            key = IRNCache._get_bulk_cache_key(batch_id)
            redis_client.setex(key, expiry, json.dumps(status))
            return True
        except (RedisError, Exception) as e:
            logger.error(f"Error caching bulk IRN status for batch {batch_id}: {str(e)}")
            return False
    
    @staticmethod
    def get_bulk_irn_status(batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a bulk IRN generation job.
        
        Args:
            batch_id: ID of the bulk generation batch
            
        Returns:
            Optional dict with status data if found, None otherwise
        """
        if not redis_client:
            return None
            
        try:
            key = IRNCache._get_bulk_cache_key(batch_id)
            data = redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except (RedisError, Exception) as e:
            logger.error(f"Error retrieving bulk IRN status for batch {batch_id}: {str(e)}")
            return None
