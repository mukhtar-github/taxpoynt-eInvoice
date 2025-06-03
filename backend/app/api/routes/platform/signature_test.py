"""
Test routes for signature functionality in the Platform layer.
These routes provide sample data for testing the frontend components.
"""

import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends

from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/platform/signatures/test", tags=["platform", "signatures", "test"])

@router.get("/sample-metrics")
async def get_sample_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get sample performance metrics for signature operations.
    This endpoint is for testing the frontend components.
    """
    # Generate realistic sample data
    total_signatures = random.randint(5000, 20000)
    avg_time = random.uniform(2.5, 15.0)
    min_time = avg_time * 0.6
    max_time = avg_time * 2.2
    operations_per_minute = total_signatures / (total_signatures * avg_time / 60000)
    
    # Cache metrics
    hits = random.randint(3000, 15000)
    misses = random.randint(500, 3000)
    hit_rate = hits / (hits + misses) if (hits + misses) > 0 else 0
    cache_entries = random.randint(500, 2000)
    
    # Verification metrics
    verification_total = random.randint(1000, 5000)
    verification_success_rate = random.uniform(0.92, 0.99)
    verification_avg_time = random.uniform(5.0, 20.0)
    
    return {
        "generation": {
            "total": total_signatures,
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "operations_per_minute": operations_per_minute
        },
        "cache": {
            "hit_rate": hit_rate,
            "hits": hits,
            "misses": misses,
            "entries": cache_entries,
            "memory_usage": cache_entries * 1024  # Rough estimate
        },
        "verification": {
            "total": verification_total,
            "success_rate": verification_success_rate,
            "avg_time": verification_avg_time
        }
    }

@router.get("/sample-verification")
async def get_sample_verification(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get sample verification result for an invoice.
    This endpoint is for testing the verification components.
    """
    # Random success/failure with high success rate
    is_valid = random.random() > 0.1
    
    details = {
        "algorithm": random.choice([
            "RSA-PSS-SHA256", 
            "RSA-PKCS1-SHA256", 
            "ED25519"
        ]),
        "version": random.choice(["1.0", "2.0"]),
        "timestamp": (datetime.now() - timedelta(minutes=random.randint(5, 60))).isoformat(),
        "signature_id": f"sig_{random.randint(10000, 99999)}_{int(time.time())}",
        "key_info": {
            "key_id": f"key_{random.randint(1000, 9999)}",
            "certificate": f"cert_{random.randint(1000, 9999)}.crt"
        }
    }
    
    if not is_valid:
        return {
            "is_valid": False,
            "message": random.choice([
                "Invalid signature - data mismatch",
                "Expired certificate",
                "Invalid certificate chain",
                "Signature format error"
            ]),
            "details": details
        }
    else:
        return {
            "is_valid": True,
            "message": "Signature verified successfully",
            "details": details
        }
