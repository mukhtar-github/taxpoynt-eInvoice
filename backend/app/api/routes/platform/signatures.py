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
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.user import User
from app.utils.crypto_signing import verify_csid
from app.utils.signature_optimization import optimized_sign_invoice, batch_sign_invoices, get_metrics as get_optimization_metrics
from app.utils.signature_caching import cached_sign_invoice, get_cache_metrics, clear_cache
from app.utils.signature_event_tracker import signature_tracker, SignatureEventType
from app.crud import signature_settings as crud_signature_settings

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

# Legacy in-memory settings (used only as fallback)
legacy_settings = SignatureSettings()

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
    # Extract CSID and invoice identifier if present
    csid = invoice_data.get("csid") or invoice_data.get("cryptographic_stamp")
    invoice_id = invoice_data.get("invoice_number") or invoice_data.get("id") or "unknown"
    
    if not csid:
        # Track failed verification due to missing signature
        signature_tracker.track_event(
            event_type=SignatureEventType.VERIFICATION,
            user_id=str(current_user.id),
            invoice_id=invoice_id,
            success=False,
            error_message="No signature or CSID found in the provided invoice"
        )
        
        # Update legacy stats
        verification_stats["total"] += 1
        verification_stats["failure"] += 1
        
        return VerifyResponse(
            is_valid=False,
            message="No signature or CSID found in the provided invoice",
            details={}
        )
    
    # Use context manager to track verification performance
    with signature_tracker.track_operation(
        event_type=SignatureEventType.VERIFICATION,
        user_id=str(current_user.id),
        invoice_id=invoice_id,
        details={"source": "api", "method": "direct"}
    ):
        try:
            # Verify the signature
            is_valid, message, details = verify_csid(invoice_data, csid)
            
            # Track success/failure for detailed reporting
            signature_tracker.track_event(
                event_type=SignatureEventType.VERIFICATION,
                user_id=str(current_user.id),
                invoice_id=invoice_id,
                signature_id=details.get("signature_id"),
                success=is_valid,
                error_message=None if is_valid else message,
                details={
                    "algorithm": details.get("algorithm"),
                    "version": details.get("version")
                }
            )
            
            # Update legacy stats for backward compatibility
            verification_stats["total"] += 1
            if is_valid:
                verification_stats["success"] += 1
            else:
                verification_stats["failure"] += 1
                
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
    
    # Track file verification attempt
    file_name = file.filename or "unknown_file"
    
    with signature_tracker.track_operation(
        event_type=SignatureEventType.VERIFICATION,
        user_id=str(current_user.id),
        details={
            "source": "api", 
            "method": "file_upload",
            "file_name": file_name,
            "content_type": file.content_type
        }
    ):
        # Attempt to parse the file
        try:
            contents = await file.read()
            
            # First try to parse as JSON
            try:
                invoice_data = json.loads(contents.decode('utf-8'))
            except json.JSONDecodeError:
                # Track parsing error
                signature_tracker.track_event(
                    event_type=SignatureEventType.ERROR,
                    user_id=str(current_user.id),
                    error_message=f"Unsupported file format: {file.content_type}. Only JSON is currently supported.",
                    details={"file_name": file_name}
                )
                
                # If not JSON, try to parse as CSV or other formats
                return VerifyResponse(
                    is_valid=False,
                    message=f"Unsupported file format: {file.content_type}. Only JSON is currently supported.",
                    details={}
                )
                
            # Now verify using the standard verification function
            return await verify_signature(invoice_data, current_user)
        
        except Exception as e:
            logger.error(f"Error verifying file signature: {str(e)}")
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
    # Track metrics retrieval
    signature_tracker.track_event(
        event_type=SignatureEventType.VERIFICATION,
        user_id=str(current_user.id),
        details={"action": "metrics_retrieval"}
    )
    
    # Get event tracker metrics
    tracker_metrics = signature_tracker.get_metrics()
    
    # Get optimization metrics for backward compatibility
    optimization_metrics = get_optimization_metrics()
    
    # Get cache metrics
    cache_metrics = get_cache_metrics()
    
    # Format verification metrics, using event tracker data if available
    verification_metrics = {
        "total": tracker_metrics["verification"]["total"] or verification_stats["total"],
        "success": tracker_metrics["verification"]["success"] or verification_stats["success"],
        "failure": tracker_metrics["verification"]["failure"] or verification_stats["failure"],
        "avg_time": tracker_metrics["verification"]["avg_time"] or verification_stats["avg_time"],
        "success_rate": tracker_metrics["verification"]["success_rate"] or 
                       (verification_stats["success"] / verification_stats["total"] if verification_stats["total"] > 0 else 0)
    }
    
    # Format generation metrics
    generation_metrics = {
        "total": tracker_metrics["generation"]["total"] or optimization_metrics.get("total_signatures", 0),
        "avg_time": tracker_metrics["generation"]["avg_time"] or optimization_metrics.get("avg_time", 0),
        "min_time": optimization_metrics.get("min_time", 0),
        "max_time": optimization_metrics.get("max_time", 0),
        "operations_per_minute": (
            optimization_metrics.get("total_signatures", 0) / 
            (optimization_metrics.get("total_time", 0) / 60000)
        ) if optimization_metrics.get("total_time", 0) > 0 else 0
    }
    
    # Format cache metrics
    enhanced_cache_metrics = {
        "hits": tracker_metrics["cache"]["hits"] or cache_metrics.get("hits", 0),
        "misses": tracker_metrics["cache"]["misses"] or cache_metrics.get("misses", 0),
        "entries": cache_metrics.get("entries", 0),
        "memory_usage": cache_metrics.get("memory_usage", 0),
        "hit_rate": tracker_metrics["cache"]["hit_rate"] or cache_metrics.get("hit_rate", 0),
        "clear_count": tracker_metrics["cache"]["clear_count"] or 0
    }
    
    return {
        "generation": generation_metrics,
        "verification": verification_metrics,
        "cache": enhanced_cache_metrics
    }

@router.post("/settings")
async def save_settings(
    settings: SignatureSettings,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Save signature settings
    
    Persists the settings to the database and creates a new version
    when settings are updated.
    """
    # Get current settings for comparison
    current_db_settings = crud_signature_settings.get_active_settings_by_user(db, current_user.id)
    
    # Track settings change
    signature_tracker.track_event(
        event_type=SignatureEventType.SETTINGS_CHANGE,
        user_id=str(current_user.id),
        details={
            "old_settings": current_db_settings.to_dict() if current_db_settings else {},
            "new_settings": settings.dict()
        }
    )
    
    # Save to database
    db_settings = crud_signature_settings.create_settings(
        db=db,
        settings_data=settings.dict(),
        user_id=current_user.id
    )
    
    logger.info(f"User {current_user.email} updated signature settings: {settings.dict()}")
    
    return {
        "status": "success",
        "message": "Settings saved successfully",
        "settings": settings.dict(),
        "id": db_settings.id,
        "version": db_settings.version
    }

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current signature settings
    
    Retrieves user-specific settings or falls back to system defaults
    """
    # Track settings retrieval
    signature_tracker.track_event(
        event_type=SignatureEventType.SETTINGS_RETRIEVAL,
        user_id=str(current_user.id)
    )
    
    # Get from database
    settings_dict = crud_signature_settings.get_effective_settings(db, current_user)
    
    # Convert to model for response
    settings_model = SignatureSettings(**settings_dict)
    
    return settings_model

@router.get("/settings/history")
async def get_settings_history(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get history of signature settings changes
    """
    history = crud_signature_settings.get_settings_history(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )
    
    return {
        "history": [item.to_dict() for item in history],
        "total": len(history),
        "limit": limit,
        "skip": skip
    }

@router.post("/settings/rollback/{settings_id}")
async def rollback_settings(
    settings_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Rollback to a previous version of settings
    """
    # Get the specified settings version
    settings = crud_signature_settings.get_settings(db, settings_id)
    
    if not settings:
        raise HTTPException(status_code=404, detail="Settings version not found")
        
    if settings.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access these settings")
    
    # Track rollback event
    signature_tracker.track_event(
        event_type=SignatureEventType.SETTINGS_ROLLBACK,
        user_id=str(current_user.id),
        details={
            "rollback_to_version": settings.version,
            "settings_id": settings_id
        }
    )
    
    # Create a new version with the same settings
    settings_data = settings.to_dict()
    new_settings = crud_signature_settings.create_settings(
        db=db,
        settings_data=settings_data,
        user_id=current_user.id
    )
    
    return {
        "status": "success",
        "message": f"Settings rolled back to version {settings.version}",
        "new_version": new_settings.version,
        "settings": new_settings.to_dict()
    }

@router.post("/clear-cache")
async def clear_signature_cache(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Clear the signature cache
    """
    # Track cache clearing
    signature_tracker.track_event(
        event_type=SignatureEventType.CACHE_CLEAR,
        user_id=str(current_user.id)
    )
    
    clear_cache()
    return {
        "status": "success",
        "message": "Cache cleared successfully"
    }
