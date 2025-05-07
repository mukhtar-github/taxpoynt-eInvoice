"""Permissions and RBAC (Role-Based Access Control) system."""
from enum import Enum, auto
from typing import List, Dict, Optional, Set

from app.models.user import UserRole


class Permission(str, Enum):
    """Permission enumeration for fine-grained access control."""
    # User management permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Organization management permissions
    ORG_CREATE = "org:create"
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    
    # Integration permissions
    INTEGRATION_CREATE = "integration:create"
    INTEGRATION_READ = "integration:read"
    INTEGRATION_UPDATE = "integration:update"
    INTEGRATION_DELETE = "integration:delete"
    
    # Credential management permissions
    CREDENTIAL_CREATE = "credential:create"
    CREDENTIAL_READ = "credential:read"
    CREDENTIAL_UPDATE = "credential:update"
    CREDENTIAL_DELETE = "credential:delete"
    
    # IRN permissions
    IRN_GENERATE = "irn:generate"
    IRN_READ = "irn:read"
    IRN_UPDATE = "irn:update"
    
    # API permissions
    API_KEY_MANAGE = "api_key:manage"
    API_ACCESS = "api:access"
    
    # Admin permissions
    ADMIN_FULL_ACCESS = "admin:full_access"


# Role-based permission mappings
ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.OWNER: [p for p in Permission],  # All permissions
    
    UserRole.ADMIN: [
        # User management
        Permission.USER_CREATE, Permission.USER_READ, 
        Permission.USER_UPDATE, Permission.USER_DELETE,
        
        # Organization management
        Permission.ORG_READ, Permission.ORG_UPDATE,
        
        # Integration management
        Permission.INTEGRATION_CREATE, Permission.INTEGRATION_READ,
        Permission.INTEGRATION_UPDATE, Permission.INTEGRATION_DELETE,
        
        # Credential management
        Permission.CREDENTIAL_CREATE, Permission.CREDENTIAL_READ,
        Permission.CREDENTIAL_UPDATE, Permission.CREDENTIAL_DELETE,
        
        # IRN management
        Permission.IRN_GENERATE, Permission.IRN_READ, Permission.IRN_UPDATE,
        
        # API management
        Permission.API_KEY_MANAGE, Permission.API_ACCESS,
    ],
    
    UserRole.MEMBER: [
        # User management (limited)
        Permission.USER_READ,
        
        # Organization management (limited)
        Permission.ORG_READ,
        
        # Integration management (limited)
        Permission.INTEGRATION_READ,
        
        # Credential management (limited)
        Permission.CREDENTIAL_READ,
        
        # IRN management
        Permission.IRN_GENERATE, Permission.IRN_READ,
        
        # API access
        Permission.API_ACCESS,
    ],
    
    UserRole.SI_USER: [
        # SI users have limited permissions
        Permission.USER_READ,
        Permission.ORG_READ,
        Permission.INTEGRATION_READ,
        Permission.CREDENTIAL_READ,
        Permission.IRN_GENERATE, Permission.IRN_READ,
        Permission.API_ACCESS,
    ],
}


def get_permissions_for_role(role: UserRole) -> Set[Permission]:
    """Get the set of permissions for a given role."""
    return set(ROLE_PERMISSIONS.get(role, []))


def user_has_permission(user_role: UserRole, required_permission: Permission) -> bool:
    """Check if a user role has a specific permission."""
    permissions = get_permissions_for_role(user_role)
    
    # Special case: ADMIN_FULL_ACCESS grants all permissions
    if Permission.ADMIN_FULL_ACCESS in permissions:
        return True
        
    return required_permission in permissions
