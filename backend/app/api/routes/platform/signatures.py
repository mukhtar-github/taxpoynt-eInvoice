"""
API routes for signature management in the Platform layer.

These routes handle:
1. Signature verification
2. Performance metrics collection
3. Settings management
4. Batch operation support
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import get_current_active_user
from app.models.user import User
from app.utils.crypto_signing import verify_csid
from app.utils.signature_optimization import optimized_sign_invoice, batch_sign_invoices, get_metrics as get_optimization_metrics
from app.utils.signature_caching import cached_sign_invoice, get_cache_metrics, clear_cache

router = APIRouter(prefix="/platform/signatures", tags=["platform", "signatures"])
logger = logging.getLogger(__name__)

# Models
class SignatureSettings(BaseModel):
    algorithm: str = Field("RSA-PSS-SHA256", title="Default signing algorithm")
    version: str = Field("2.0", title="CSID version")
    enableCaching: bool = Field(True, title="Enable signature caching")
    cacheSize: int = Field(1000, title="Maximum cache size")
    cacheTtl: int = Field(3600, title="Cache TTL in seconds")
    parallelProcessing: bool = Field(True, title="Enable parallel processing")
    maxWorkers: int = Field(4, title="Maximum worker threads/processes")

class VerifyResponse(BaseModel):
    is_valid: bool = Field(..., title="Whether signature is valid")
    message: str = Field(..., title="Verification message")
    details: Dict[str, Any] = Field({}, title="Signature details")

# Current settings (in-memory for simplicity, in production would be in database)
current_settings = SignatureSettings()

# Verification statistics
verification_stats = {
    "total": 0,
    "success": 0,
    "failure": 0,
    "avg_time": 0,
    "total_time": 0,
}

@router.post("/verify", response_model=VerifyResponse)
async def verify_signature(
    invoice_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
) -> VerifyResponse:
    """
    Verify a signature in an invoice
    """
    start_time = time.time()
    
    # Update verification stats
    verification_stats["total"] += 1
    
    # Extract CSID if present
    csid = invoice_data.get("csid") or invoice_data.get("cryptographic_stamp")
    
    if not csid:
        verification_stats["failure"] += 1
        return VerifyResponse(
            is_valid=False,
            message="No signature or CSID found in the provided invoice",
            details={}
        )
    
    try:
        # Verify the signature
        is_valid, message, details = verify_csid(invoice_data, csid)
        
        # Update stats
        if is_valid:
            verification_stats["success"] += 1
        else:
            verification_stats["failure"] += 1
        
        # Update timing
        execution_time = time.time() - start_time
        verification_stats["total_time"] += execution_time
        verification_stats["avg_time"] = verification_stats["total_time"] / verification_stats["total"]
        
        return VerifyResponse(
            is_valid=is_valid,
            message=message,
            details=details
        )
    except Exception as e:
        logger.error(f"Error verifying signature: {str(e)}")
        verification_stats["failure"] += 1
        return VerifyResponse(
            is_valid=False,
            message=f"Verification error: {str(e)}",
            details={}
        )

@router.post("/verify-file", response_model=VerifyResponse)
async def verify_file_signature(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
) -> VerifyResponse:
    """
    Verify a signature in an uploaded invoice file
    """
    start_time = time.time()
    
    # Update verification stats
    verification_stats["total"] += 1
    
    try:
        # Read and parse the file
        content = await file.read()
        
        # Try to parse as JSON
        try:
            invoice_data = json.loads(content)
        except json.JSONDecodeError:
            # If not JSON, could be XML or other format - for now just return error
            verification_stats["failure"] += 1
            return VerifyResponse(
                is_valid=False,
                message="File format not supported or invalid JSON",
                details={}
            )
        
        # Extract CSID if present
        csid = invoice_data.get("csid") or invoice_data.get("cryptographic_stamp")
        
        if not csid:
            verification_stats["failure"] += 1
            return VerifyResponse(
                is_valid=False,
                message="No signature or CSID found in the provided file",
                details={}
            )
        
        # Verify the signature
        is_valid, message, details = verify_csid(invoice_data, csid)
        
        # Update stats
        if is_valid:
            verification_stats["success"] += 1
        else:
            verification_stats["failure"] += 1
        
        # Update timing
        execution_time = time.time() - start_time
        verification_stats["total_time"] += execution_time
        verification_stats["avg_time"] = verification_stats["total_time"] / verification_stats["total"]
        
        return VerifyResponse(
            is_valid=is_valid,
            message=message,
            details=details
        )
    except Exception as e:
        logger.error(f"Error verifying file signature: {str(e)}")
        verification_stats["failure"] += 1
        return VerifyResponse(
            is_valid=False,
            message=f"Verification error: {str(e)}",
            details={}
        )

@router.get("/metrics")
async def get_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get performance metrics for signature operations
    """
    # Get optimization metrics
    optimization_metrics = get_optimization_metrics()
    
    # Get cache metrics
    cache_metrics = get_cache_metrics()
    
    # Calculate verification success rate
    success_rate = 0
    if verification_stats["total"] > 0:
        success_rate = verification_stats["success"] / verification_stats["total"]
    
    # Combine all metrics
    return {
        "generation": {
            "total": optimization_metrics.get("total_signatures", 0),
            "avg_time": optimization_metrics.get("avg_time", 0),
            "min_time": optimization_metrics.get("min_time", 0) if optimization_metrics.get("min_time", float('inf')) != float('inf') else 0,
            "max_time": optimization_metrics.get("max_time", 0),
            "operations_per_minute": (optimization_metrics.get("total_signatures", 0) / 
                                     (optimization_metrics.get("total_time", 0) / 60)) if optimization_metrics.get("total_time", 0) > 0 else 0
        },
        "cache": {
            "hit_rate": cache_metrics.get("hit_rate", 0),
            "hits": cache_metrics.get("hits", 0),
            "misses": cache_metrics.get("misses", 0),
            "entries": cache_metrics.get("entries", 0),
            "memory_usage": cache_metrics.get("entries", 0) * 1024  # Rough estimate
        },
        "verification": {
            "total": verification_stats["total"],
            "success_rate": success_rate,
            "avg_time": verification_stats["avg_time"]
        }
    }

@router.post("/settings")
async def save_settings(
    settings: SignatureSettings,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Save signature settings
    """
    global current_settings
    current_settings = settings
    
    # In a real implementation, these would be saved to database
    
    # Clear cache if caching disabled
    if not settings.enableCaching:
        clear_cache()
    
    return {"status": "success", "message": "Settings saved successfully"}

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_active_user)
) -> SignatureSettings:
    """
    Get current signature settings
    """
    return current_settings

@router.post("/clear-cache")
async def clear_signature_cache(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Clear the signature cache
    """
    clear_cache()
    return {"status": "success", "message": "Cache cleared successfully"}
