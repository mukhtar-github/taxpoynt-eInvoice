"""
Service Access Management API Routes

This module contains FastAPI routes for managing user service access permissions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.dependencies.service_permissions import require_owner_access, require_org_management_access
from app.models.user import User
from app.models.user_service_access import (
    UserServiceAccess, 
    ServiceAccessAuditLog,
    ServiceType, 
    AccessLevel,
    SERVICE_DESCRIPTIONS
)
from app.schemas.service_access import (
    ServiceAccessCreate,
    ServiceAccessResponse,
    ServiceAccessUpdate,
    ServiceSummaryResponse,
    UserServiceAccessListResponse,
    ServiceAccessAuditResponse
)

router = APIRouter(prefix="/service-access", tags=["Service Access Management"])


@router.post("/users/{user_id}/grant", response_model=ServiceAccessResponse)
async def grant_service_access(
    user_id: UUID,
    service_access_data: ServiceAccessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grant service access to a user."""
    # Check if current user has permission to grant access
    if not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN):
        # Allow owner access
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Owner access required to grant service access"
            )
    
    # Check if user exists
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if access already exists
    existing_access = db.query(UserServiceAccess).filter(
        and_(
            UserServiceAccess.user_id == user_id,
            UserServiceAccess.service_type == service_access_data.service_type,
            UserServiceAccess.is_active == True
        )
    ).first()
    
    if existing_access:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User already has active access to {service_access_data.service_type.value} service"
        )
    
    # Create new service access
    new_access = UserServiceAccess(
        user_id=user_id,
        service_type=service_access_data.service_type,
        access_level=service_access_data.access_level,
        granted_by=current_user.id,
        expires_at=service_access_data.expires_at,
        notes=service_access_data.notes
    )
    
    db.add(new_access)
    db.commit()
    db.refresh(new_access)
    
    # Create audit log
    audit_log = ServiceAccessAuditLog(
        user_service_access_id=new_access.id,
        action="granted",
        changed_by=current_user.id,
        change_reason=f"Access granted by {current_user.email}",
        new_values=f"service_type: {service_access_data.service_type.value}, access_level: {service_access_data.access_level.value}"
    )
    db.add(audit_log)
    db.commit()
    
    return ServiceAccessResponse(
        id=new_access.id,
        user_id=new_access.user_id,
        service_type=new_access.service_type.value,
        access_level=new_access.access_level.value,
        granted_by=new_access.granted_by,
        granted_at=new_access.granted_at,
        expires_at=new_access.expires_at,
        is_active=new_access.is_active,
        notes=new_access.notes
    )


@router.put("/users/{user_id}/access/{access_id}", response_model=ServiceAccessResponse)
async def update_service_access(
    user_id: UUID,
    access_id: UUID,
    update_data: ServiceAccessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update existing service access."""
    # Check permissions
    if not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN):
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Owner access required to update service access"
            )
    
    # Find the access record
    service_access = db.query(UserServiceAccess).filter(
        and_(
            UserServiceAccess.id == access_id,
            UserServiceAccess.user_id == user_id
        )
    ).first()
    
    if not service_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service access record not found"
        )
    
    # Store old values for audit
    old_values = f"access_level: {service_access.access_level.value}, expires_at: {service_access.expires_at}, is_active: {service_access.is_active}"
    
    # Update fields
    if update_data.access_level is not None:
        service_access.access_level = update_data.access_level
    if update_data.expires_at is not None:
        service_access.expires_at = update_data.expires_at
    if update_data.is_active is not None:
        service_access.is_active = update_data.is_active
    if update_data.notes is not None:
        service_access.notes = update_data.notes
    
    service_access.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(service_access)
    
    # Create audit log
    new_values = f"access_level: {service_access.access_level.value}, expires_at: {service_access.expires_at}, is_active: {service_access.is_active}"
    audit_log = ServiceAccessAuditLog(
        user_service_access_id=service_access.id,
        action="modified",
        changed_by=current_user.id,
        change_reason=f"Access updated by {current_user.email}",
        old_values=old_values,
        new_values=new_values
    )
    db.add(audit_log)
    db.commit()
    
    return ServiceAccessResponse(
        id=service_access.id,
        user_id=service_access.user_id,
        service_type=service_access.service_type.value,
        access_level=service_access.access_level.value,
        granted_by=service_access.granted_by,
        granted_at=service_access.granted_at,
        expires_at=service_access.expires_at,
        is_active=service_access.is_active,
        notes=service_access.notes
    )


@router.delete("/users/{user_id}/access/{access_id}")
async def revoke_service_access(
    user_id: UUID,
    access_id: UUID,
    reason: Optional[str] = Query(None, description="Reason for revoking access"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke service access from a user."""
    # Check permissions
    if not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN):
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Owner access required to revoke service access"
            )
    
    # Find the access record
    service_access = db.query(UserServiceAccess).filter(
        and_(
            UserServiceAccess.id == access_id,
            UserServiceAccess.user_id == user_id
        )
    ).first()
    
    if not service_access:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service access record not found"
        )
    
    # Deactivate instead of delete for audit trail
    service_access.is_active = False
    service_access.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Create audit log
    audit_log = ServiceAccessAuditLog(
        user_service_access_id=service_access.id,
        action="revoked",
        changed_by=current_user.id,
        change_reason=reason or f"Access revoked by {current_user.email}",
        old_values=f"is_active: true",
        new_values=f"is_active: false"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Service access revoked successfully"}


@router.get("/users/{user_id}", response_model=UserServiceAccessListResponse)
async def list_user_service_access(
    user_id: UUID,
    include_inactive: bool = Query(False, description="Include inactive access records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all service access for a user."""
    # Check if user can view this information
    if (user_id != current_user.id and 
        not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.READ)):
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other user's service access"
            )
    
    # Build query
    query = db.query(UserServiceAccess).filter(UserServiceAccess.user_id == user_id)
    
    if not include_inactive:
        query = query.filter(UserServiceAccess.is_active == True)
    
    access_records = query.all()
    
    # Convert to response format
    access_list = []
    for access in access_records:
        access_list.append(ServiceAccessResponse(
            id=access.id,
            user_id=access.user_id,
            service_type=access.service_type.value,
            access_level=access.access_level.value,
            granted_by=access.granted_by,
            granted_at=access.granted_at,
            expires_at=access.expires_at,
            is_active=access.is_active,
            notes=access.notes
        ))
    
    return UserServiceAccessListResponse(
        user_id=user_id,
        total_access_records=len(access_list),
        active_services=len([a for a in access_list if a.is_active]),
        access_records=access_list
    )


@router.get("/services/available", response_model=List[ServiceSummaryResponse])
async def list_available_services(current_user: User = Depends(get_current_user)):
    """List services available to the current user."""
    accessible_services = current_user.get_accessible_services()
    
    service_summaries = []
    for service in accessible_services:
        access_level = current_user.get_service_access_level(service)
        service_info = SERVICE_DESCRIPTIONS.get(service, {})
        
        service_summaries.append(ServiceSummaryResponse(
            service_type=service.value,
            name=service_info.get("name", service.value.replace("_", " ").title()),
            description=service_info.get("description", ""),
            access_level=access_level,
            features=service_info.get("features", [])
        ))
    
    return service_summaries


@router.get("/services/all", response_model=List[Dict[str, Any]])
async def list_all_services(current_user: User = Depends(get_current_user)):
    """List all available services (for admin users)."""
    # Check if user has admin access
    if not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN):
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or Owner access required to view all services"
            )
    
    all_services = []
    for service_type in ServiceType:
        service_info = SERVICE_DESCRIPTIONS.get(service_type, {})
        all_services.append({
            "service_type": service_type.value,
            "name": service_info.get("name", service_type.value.replace("_", " ").title()),
            "description": service_info.get("description", ""),
            "features": service_info.get("features", []),
            "available_access_levels": [level.value for level in AccessLevel]
        })
    
    return all_services


@router.get("/audit/{user_id}", response_model=List[ServiceAccessAuditResponse])
async def get_service_access_audit_log(
    user_id: UUID,
    limit: int = Query(50, ge=1, le=1000, description="Number of audit records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit log for user's service access changes."""
    # Check permissions
    if (user_id != current_user.id and 
        not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, AccessLevel.ADMIN)):
        has_owner_access = any(
            access.access_level == AccessLevel.OWNER 
            for access in current_user.service_access 
            if access.is_active
        )
        if not has_owner_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot view other user's audit log"
            )
    
    # Get audit records for this user's service access
    audit_records = db.query(ServiceAccessAuditLog).join(UserServiceAccess).filter(
        UserServiceAccess.user_id == user_id
    ).order_by(ServiceAccessAuditLog.timestamp.desc()).limit(limit).all()
    
    audit_responses = []
    for record in audit_records:
        audit_responses.append(ServiceAccessAuditResponse(
            id=record.id,
            user_service_access_id=record.user_service_access_id,
            action=record.action,
            changed_by=record.changed_by,
            change_reason=record.change_reason,
            old_values=record.old_values,
            new_values=record.new_values,
            timestamp=record.timestamp
        ))
    
    return audit_responses


@router.post("/bulk-grant")
async def bulk_grant_service_access(
    user_ids: List[UUID],
    service_type: ServiceType,
    access_level: AccessLevel,
    expires_at: Optional[datetime] = None,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Grant service access to multiple users at once."""
    # Check permissions - only owners can do bulk operations
    has_owner_access = any(
        access.access_level == AccessLevel.OWNER 
        for access in current_user.service_access 
        if access.is_active
    )
    if not has_owner_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required for bulk operations"
        )
    
    results = {
        "successful": [],
        "failed": [],
        "already_exists": []
    }
    
    for user_id in user_ids:
        try:
            # Check if user exists
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                results["failed"].append({"user_id": str(user_id), "reason": "User not found"})
                continue
            
            # Check if access already exists
            existing_access = db.query(UserServiceAccess).filter(
                and_(
                    UserServiceAccess.user_id == user_id,
                    UserServiceAccess.service_type == service_type,
                    UserServiceAccess.is_active == True
                )
            ).first()
            
            if existing_access:
                results["already_exists"].append(str(user_id))
                continue
            
            # Create new access
            new_access = UserServiceAccess(
                user_id=user_id,
                service_type=service_type,
                access_level=access_level,
                granted_by=current_user.id,
                expires_at=expires_at,
                notes=notes or f"Bulk granted by {current_user.email}"
            )
            
            db.add(new_access)
            results["successful"].append(str(user_id))
            
        except Exception as e:
            results["failed"].append({"user_id": str(user_id), "reason": str(e)})
    
    db.commit()
    
    return {
        "message": f"Bulk operation completed. {len(results['successful'])} successful, {len(results['failed'])} failed, {len(results['already_exists'])} already existed",
        "results": results
    }