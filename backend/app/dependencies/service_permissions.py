"""
Service-Based Permission Dependencies

This module provides dependency injection for service-based permissions,
allowing fine-grained access control across TaxPoynt services.
"""

from functools import wraps
from typing import Callable, Any

from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.dependencies.db import get_db
from app.models.user import User
from app.models.user_service_access import ServiceType, AccessLevel


def require_service_access(service: ServiceType, level: AccessLevel = AccessLevel.READ):
    """
    Decorator to require specific service access.
    
    Args:
        service: The service type required
        level: The minimum access level required (default: READ)
    
    Usage:
        @require_service_access(ServiceType.ACCESS_POINT_PROVIDER, AccessLevel.WRITE)
        async def generate_irn(current_user: User = Depends(get_current_user)):
            # Only users with APP write access can access this endpoint
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs (should be injected by get_current_user)
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not current_user.has_service_access(service, level):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: {service.value} service requires {level.value} permission"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Convenience decorators for common service access patterns
def require_app_access(level: AccessLevel = AccessLevel.READ):
    """Require Access Point Provider (e-invoicing) service access"""
    return require_service_access(ServiceType.ACCESS_POINT_PROVIDER, level)


def require_si_access(level: AccessLevel = AccessLevel.READ):
    """Require System Integration service access"""
    return require_service_access(ServiceType.SYSTEM_INTEGRATION, level)


def require_compliance_access(level: AccessLevel = AccessLevel.READ):
    """Require Nigerian Compliance service access"""
    return require_service_access(ServiceType.NIGERIAN_COMPLIANCE, level)


def require_org_management_access(level: AccessLevel = AccessLevel.READ):
    """Require Organization Management service access"""
    return require_service_access(ServiceType.ORGANIZATION_MANAGEMENT, level)


def require_owner_access():
    """
    Require owner-level access to any service.
    Used for platform-wide administrative functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = None
            for key, value in kwargs.items():
                if isinstance(value, User):
                    current_user = value
                    break
            
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user has owner access to any service
            has_owner_access = any(
                access.access_level == AccessLevel.OWNER 
                for access in current_user.service_access 
                if access.is_active and (
                    access.expires_at is None or 
                    access.expires_at > current_user.service_access[0].created_at.__class__.utcnow()
                )
            )
            
            if not has_owner_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Owner access required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Dependency functions for FastAPI dependency injection
async def get_current_user_with_app_access(
    level: AccessLevel = AccessLevel.READ,
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with APP service access validation"""
    if not current_user.has_service_access(ServiceType.ACCESS_POINT_PROVIDER, level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Point Provider service requires {level.value} permission"
        )
    return current_user


async def get_current_user_with_si_access(
    level: AccessLevel = AccessLevel.READ,
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with SI service access validation"""
    if not current_user.has_service_access(ServiceType.SYSTEM_INTEGRATION, level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"System Integration service requires {level.value} permission"
        )
    return current_user


async def get_current_user_with_compliance_access(
    level: AccessLevel = AccessLevel.READ,
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with Compliance service access validation"""
    if not current_user.has_service_access(ServiceType.NIGERIAN_COMPLIANCE, level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Nigerian Compliance service requires {level.value} permission"
        )
    return current_user


async def get_current_user_with_org_management_access(
    level: AccessLevel = AccessLevel.READ,
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user with Organization Management service access validation"""
    if not current_user.has_service_access(ServiceType.ORGANIZATION_MANAGEMENT, level):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization Management service requires {level.value} permission"
        )
    return current_user


async def get_current_owner_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user with owner access validation"""
    has_owner_access = any(
        access.access_level == AccessLevel.OWNER 
        for access in current_user.service_access 
        if access.is_active
    )
    
    if not has_owner_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner access required"
        )
    
    return current_user


# Utility function to check multiple service access
def check_multiple_service_access(
    user: User, 
    required_services: list[tuple[ServiceType, AccessLevel]]
) -> bool:
    """
    Check if user has access to multiple services with specified levels.
    
    Args:
        user: The user to check
        required_services: List of (service_type, access_level) tuples
    
    Returns:
        True if user has ALL required service access, False otherwise
    """
    for service_type, access_level in required_services:
        if not user.has_service_access(service_type, access_level):
            return False
    return True


def get_user_service_summary(user: User) -> dict:
    """
    Get a summary of user's service access for dashboard display.
    
    Returns:
        Dictionary with service access information
    """
    from app.models.user_service_access import SERVICE_DESCRIPTIONS
    
    accessible_services = user.get_accessible_services()
    
    summary = {
        "user_id": str(user.id),
        "total_services": len(accessible_services),
        "services": {}
    }
    
    for service in accessible_services:
        access_level = user.get_service_access_level(service)
        service_info = SERVICE_DESCRIPTIONS.get(service, {})
        
        summary["services"][service.value] = {
            "name": service_info.get("name", service.value.replace("_", " ").title()),
            "description": service_info.get("description", ""),
            "access_level": access_level,
            "features": service_info.get("features", [])
        }
    
    return summary