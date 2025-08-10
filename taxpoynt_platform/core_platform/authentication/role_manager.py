"""
Role Manager Service

This service manages SI/APP role assignments for users within the TaxPoynt platform,
providing hierarchical role management with support for multiple roles per user.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)


class PlatformRole(Enum):
    """Core platform roles"""
    SYSTEM_INTEGRATOR = "system_integrator"  # SI role
    ACCESS_POINT_PROVIDER = "access_point_provider"  # APP role
    HYBRID = "hybrid"  # Both SI and APP capabilities
    PLATFORM_ADMIN = "platform_admin"  # Platform administration
    TENANT_ADMIN = "tenant_admin"  # Tenant administration
    USER = "user"  # Regular user


class RoleScope(Enum):
    """Role scope definitions"""
    GLOBAL = "global"  # Platform-wide role
    TENANT = "tenant"  # Tenant-specific role
    SERVICE = "service"  # Service-specific role
    ENVIRONMENT = "environment"  # Environment-specific role


class RoleStatus(Enum):
    """Role assignment status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"
    EXPIRED = "expired"


class AssignmentType(Enum):
    """Role assignment type"""
    DIRECT = "direct"  # Directly assigned
    INHERITED = "inherited"  # Inherited from group/parent
    DELEGATED = "delegated"  # Delegated by admin
    TEMPORARY = "temporary"  # Temporary assignment


@dataclass
class Role:
    """Role definition"""
    role_id: str
    name: str
    platform_role: PlatformRole
    description: str
    scope: RoleScope
    permissions: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    is_system_role: bool = False
    hierarchical: bool = True
    delegatable: bool = False
    max_delegation_depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoleAssignment:
    """Role assignment to a user"""
    assignment_id: str
    user_id: str
    role_id: str
    scope: RoleScope
    status: RoleStatus = RoleStatus.ACTIVE
    assignment_type: AssignmentType = AssignmentType.DIRECT
    assigned_by: str = "system"
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    tenant_id: Optional[str] = None
    service_id: Optional[str] = None
    environment: Optional[str] = None
    conditions: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    delegation_source: Optional[str] = None  # Source assignment for delegated roles
    delegation_depth: int = 0


@dataclass
class UserRoleContext:
    """User's role context"""
    user_id: str
    active_roles: List[RoleAssignment] = field(default_factory=list)
    effective_permissions: Set[str] = field(default_factory=set)
    platform_roles: Set[PlatformRole] = field(default_factory=set)
    tenant_roles: Dict[str, List[RoleAssignment]] = field(default_factory=dict)
    service_roles: Dict[str, List[RoleAssignment]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoleHierarchy:
    """Role hierarchy definition"""
    parent_role_id: str
    child_role_id: str
    inheritance_type: str = "permissions"  # permissions, delegation
    conditions: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class RoleDelegation:
    """Role delegation tracking"""
    delegation_id: str
    delegator_id: str
    delegatee_id: str
    role_id: str
    scope: RoleScope
    delegated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    active: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)


class RoleManager(BaseService):
    """
    Role Manager Service
    
    Manages SI/APP role assignments for users within the TaxPoynt platform,
    providing hierarchical role management with support for multiple roles per user.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Role definitions
        self.roles: Dict[str, Role] = {}
        self.role_hierarchies: List[RoleHierarchy] = []
        
        # Role assignments
        self.assignments: Dict[str, RoleAssignment] = {}
        self.user_assignments: Dict[str, List[str]] = {}  # user_id -> assignment_ids
        
        # Role contexts (cached)
        self.user_contexts: Dict[str, UserRoleContext] = {}
        self.context_cache_ttl: timedelta = timedelta(minutes=15)
        self.context_timestamps: Dict[str, datetime] = {}
        
        # Delegations
        self.delegations: Dict[str, RoleDelegation] = {}
        
        # Role groups (for bulk management)
        self.role_groups: Dict[str, Set[str]] = {}  # group_id -> role_ids
        
        # Change tracking
        self.change_listeners: List = []
        self.audit_log: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            'roles_managed': 0,
            'assignments_managed': 0,
            'delegations_managed': 0,
            'context_cache_hits': 0,
            'context_cache_misses': 0,
            'role_evaluations': 0,
            'hierarchy_evaluations': 0
        }
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize role manager"""
        try:
            self.logger.info("Initializing RoleManager")
            
            # Load default roles
            await self._load_default_roles()
            
            # Set up role hierarchies
            await self._setup_default_hierarchies()
            
            # Start background workers
            await self._start_background_workers()
            
            self.logger.info("RoleManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RoleManager: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def create_role(
        self,
        role_id: str,
        name: str,
        platform_role: PlatformRole,
        description: str,
        scope: RoleScope,
        permissions: Optional[Set[str]] = None,
        hierarchical: bool = True,
        delegatable: bool = False,
        max_delegation_depth: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        created_by: str = "system"
    ) -> Role:
        """Create a new role"""
        try:
            # Validate role doesn't exist
            if role_id in self.roles:
                raise ValidationError(f"Role {role_id} already exists")
            
            # Create role
            role = Role(
                role_id=role_id,
                name=name,
                platform_role=platform_role,
                description=description,
                scope=scope,
                permissions=permissions or set(),
                hierarchical=hierarchical,
                delegatable=delegatable,
                max_delegation_depth=max_delegation_depth,
                metadata=metadata or {}
            )
            
            # Store role
            self.roles[role_id] = role
            
            # Log audit entry
            await self._log_audit_entry(
                action="create_role",
                actor=created_by,
                target=role_id,
                details={'platform_role': platform_role.value, 'scope': scope.value}
            )
            
            self.metrics['roles_managed'] += 1
            self.logger.info(f"Role created: {role_id} ({platform_role.value})")
            
            return role
            
        except Exception as e:
            self.logger.error(f"Failed to create role {role_id}: {str(e)}")
            raise AuthenticationError(f"Role creation failed: {str(e)}")
    
    async def assign_role(
        self,
        user_id: str,
        role_id: str,
        scope: RoleScope,
        assignment_type: AssignmentType = AssignmentType.DIRECT,
        assigned_by: str = "system",
        expires_at: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
        service_id: Optional[str] = None,
        environment: Optional[str] = None,
        conditions: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RoleAssignment:
        """Assign role to user"""
        try:
            # Validate role exists
            if role_id not in self.roles:
                raise ValidationError(f"Role {role_id} not found")
            
            role = self.roles[role_id]
            
            # Validate scope compatibility
            if role.scope != RoleScope.GLOBAL and role.scope != scope:
                raise ValidationError(f"Role {role_id} scope {role.scope.value} incompatible with assignment scope {scope.value}")
            
            # Check for existing assignment
            existing = await self._find_existing_assignment(user_id, role_id, scope, tenant_id, service_id, environment)
            if existing and existing.status == RoleStatus.ACTIVE:
                raise ValidationError(f"User {user_id} already has active assignment for role {role_id}")
            
            # Create assignment
            assignment_id = f"ra_{uuid.uuid4().hex[:12]}"
            assignment = RoleAssignment(
                assignment_id=assignment_id,
                user_id=user_id,
                role_id=role_id,
                scope=scope,
                assignment_type=assignment_type,
                assigned_by=assigned_by,
                expires_at=expires_at,
                tenant_id=tenant_id,
                service_id=service_id,
                environment=environment,
                conditions=conditions or {},
                metadata=metadata or {}
            )
            
            # Store assignment
            self.assignments[assignment_id] = assignment
            
            # Update user assignment index
            if user_id not in self.user_assignments:
                self.user_assignments[user_id] = []
            self.user_assignments[user_id].append(assignment_id)
            
            # Invalidate user context cache
            await self._invalidate_user_context(user_id)
            
            # Log audit entry
            await self._log_audit_entry(
                action="assign_role",
                actor=assigned_by,
                target=user_id,
                details={
                    'role_id': role_id,
                    'scope': scope.value,
                    'assignment_type': assignment_type.value,
                    'tenant_id': tenant_id,
                    'service_id': service_id,
                    'environment': environment
                }
            )
            
            # Notify change listeners
            await self._notify_change_listeners("role_assigned", user_id, assignment)
            
            self.metrics['assignments_managed'] += 1
            self.logger.info(f"Role assigned: {role_id} to {user_id} (scope: {scope.value})")
            
            return assignment
            
        except Exception as e:
            self.logger.error(f"Failed to assign role {role_id} to {user_id}: {str(e)}")
            raise AuthenticationError(f"Role assignment failed: {str(e)}")
    
    async def revoke_role(
        self,
        user_id: str,
        role_id: str,
        scope: RoleScope,
        revoked_by: str = "system",
        tenant_id: Optional[str] = None,
        service_id: Optional[str] = None,
        environment: Optional[str] = None
    ) -> bool:
        """Revoke role from user"""
        try:
            # Find assignment
            assignment = await self._find_existing_assignment(user_id, role_id, scope, tenant_id, service_id, environment)
            if not assignment or assignment.status != RoleStatus.ACTIVE:
                return False
            
            # Revoke assignment
            assignment.status = RoleStatus.INACTIVE
            assignment.updated_at = datetime.utcnow()
            
            # Invalidate user context cache
            await self._invalidate_user_context(user_id)
            
            # Log audit entry
            await self._log_audit_entry(
                action="revoke_role",
                actor=revoked_by,
                target=user_id,
                details={
                    'role_id': role_id,
                    'scope': scope.value,
                    'assignment_id': assignment.assignment_id
                }
            )
            
            # Notify change listeners
            await self._notify_change_listeners("role_revoked", user_id, assignment)
            
            self.logger.info(f"Role revoked: {role_id} from {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to revoke role {role_id} from {user_id}: {str(e)}")
            return False
    
    async def get_user_roles(
        self,
        user_id: str,
        scope: Optional[RoleScope] = None,
        tenant_id: Optional[str] = None,
        service_id: Optional[str] = None,
        environment: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[RoleAssignment]:
        """Get user's role assignments"""
        try:
            if user_id not in self.user_assignments:
                return []
            
            user_roles = []
            assignment_ids = self.user_assignments[user_id]
            
            for assignment_id in assignment_ids:
                if assignment_id not in self.assignments:
                    continue
                
                assignment = self.assignments[assignment_id]
                
                # Filter by status
                if not include_inactive and assignment.status != RoleStatus.ACTIVE:
                    continue
                
                # Filter by scope
                if scope and assignment.scope != scope:
                    continue
                
                # Filter by tenant
                if tenant_id and assignment.tenant_id != tenant_id:
                    continue
                
                # Filter by service
                if service_id and assignment.service_id != service_id:
                    continue
                
                # Filter by environment
                if environment and assignment.environment != environment:
                    continue
                
                # Check expiration
                if assignment.expires_at and datetime.utcnow() > assignment.expires_at:
                    assignment.status = RoleStatus.EXPIRED
                    continue
                
                user_roles.append(assignment)
            
            return user_roles
            
        except Exception as e:
            self.logger.error(f"Failed to get user roles for {user_id}: {str(e)}")
            return []
    
    async def get_user_context(
        self,
        user_id: str,
        force_refresh: bool = False
    ) -> UserRoleContext:
        """Get user's complete role context"""
        try:
            # Check cache first
            if not force_refresh and user_id in self.user_contexts:
                cached_context = self.user_contexts[user_id]
                timestamp = self.context_timestamps.get(user_id)
                
                if timestamp and datetime.utcnow() - timestamp < self.context_cache_ttl:
                    self.metrics['context_cache_hits'] += 1
                    return cached_context
            
            # Build fresh context
            context = UserRoleContext(user_id=user_id)
            
            # Get all active assignments
            all_assignments = await self.get_user_roles(user_id, include_inactive=False)
            context.active_roles = all_assignments
            
            # Extract platform roles
            for assignment in all_assignments:
                if assignment.role_id in self.roles:
                    role = self.roles[assignment.role_id]
                    context.platform_roles.add(role.platform_role)
            
            # Group by tenant and service
            for assignment in all_assignments:
                if assignment.tenant_id:
                    if assignment.tenant_id not in context.tenant_roles:
                        context.tenant_roles[assignment.tenant_id] = []
                    context.tenant_roles[assignment.tenant_id].append(assignment)
                
                if assignment.service_id:
                    if assignment.service_id not in context.service_roles:
                        context.service_roles[assignment.service_id] = []
                    context.service_roles[assignment.service_id].append(assignment)
            
            # Calculate effective permissions
            context.effective_permissions = await self._calculate_effective_permissions(user_id, all_assignments)
            
            # Cache context
            self.user_contexts[user_id] = context
            self.context_timestamps[user_id] = datetime.utcnow()
            
            self.metrics['context_cache_misses'] += 1
            return context
            
        except Exception as e:
            self.logger.error(f"Failed to get user context for {user_id}: {str(e)}")
            return UserRoleContext(user_id=user_id)
    
    async def has_platform_role(
        self,
        user_id: str,
        platform_role: PlatformRole,
        scope: Optional[RoleScope] = None,
        tenant_id: Optional[str] = None,
        service_id: Optional[str] = None,
        environment: Optional[str] = None
    ) -> bool:
        """Check if user has specific platform role"""
        try:
            user_roles = await self.get_user_roles(
                user_id, scope, tenant_id, service_id, environment
            )
            
            for assignment in user_roles:
                if assignment.role_id in self.roles:
                    role = self.roles[assignment.role_id]
                    if role.platform_role == platform_role:
                        self.metrics['role_evaluations'] += 1
                        return True
            
            self.metrics['role_evaluations'] += 1
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check platform role for {user_id}: {str(e)}")
            return False
    
    async def delegate_role(
        self,
        delegator_id: str,
        delegatee_id: str,
        role_id: str,
        scope: RoleScope,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict[str, Any]] = None
    ) -> RoleDelegation:
        """Delegate role from one user to another"""
        try:
            # Validate role exists and is delegatable
            if role_id not in self.roles:
                raise ValidationError(f"Role {role_id} not found")
            
            role = self.roles[role_id]
            if not role.delegatable:
                raise ValidationError(f"Role {role_id} is not delegatable")
            
            # Check if delegator has the role
            delegator_has_role = await self._user_has_role(delegator_id, role_id, scope)
            if not delegator_has_role:
                raise AuthorizationError(f"User {delegator_id} does not have role {role_id} to delegate")
            
            # Check delegation depth
            delegation_depth = await self._get_delegation_depth(delegator_id, role_id)
            if delegation_depth >= role.max_delegation_depth:
                raise ValidationError(f"Maximum delegation depth ({role.max_delegation_depth}) exceeded")
            
            # Create delegation
            delegation_id = f"rd_{uuid.uuid4().hex[:12]}"
            delegation = RoleDelegation(
                delegation_id=delegation_id,
                delegator_id=delegator_id,
                delegatee_id=delegatee_id,
                role_id=role_id,
                scope=scope,
                expires_at=expires_at,
                conditions=conditions or {}
            )
            
            # Store delegation
            self.delegations[delegation_id] = delegation
            
            # Create delegated assignment
            await self.assign_role(
                user_id=delegatee_id,
                role_id=role_id,
                scope=scope,
                assignment_type=AssignmentType.DELEGATED,
                assigned_by=delegator_id,
                expires_at=expires_at,
                metadata={'delegation_id': delegation_id}
            )
            
            # Log audit entry
            await self._log_audit_entry(
                action="delegate_role",
                actor=delegator_id,
                target=delegatee_id,
                details={
                    'role_id': role_id,
                    'scope': scope.value,
                    'delegation_id': delegation_id
                }
            )
            
            self.metrics['delegations_managed'] += 1
            self.logger.info(f"Role delegated: {role_id} from {delegator_id} to {delegatee_id}")
            
            return delegation
            
        except Exception as e:
            self.logger.error(f"Failed to delegate role {role_id}: {str(e)}")
            raise AuthenticationError(f"Role delegation failed: {str(e)}")
    
    async def create_role_hierarchy(
        self,
        parent_role_id: str,
        child_role_id: str,
        inheritance_type: str = "permissions",
        conditions: Optional[Dict[str, Any]] = None
    ) -> RoleHierarchy:
        """Create role hierarchy relationship"""
        try:
            # Validate roles exist
            if parent_role_id not in self.roles:
                raise ValidationError(f"Parent role {parent_role_id} not found")
            if child_role_id not in self.roles:
                raise ValidationError(f"Child role {child_role_id} not found")
            
            # Check for circular hierarchy
            if await self._would_create_circular_hierarchy(parent_role_id, child_role_id):
                raise ValidationError("Role hierarchy would create a circular dependency")
            
            # Create hierarchy
            hierarchy = RoleHierarchy(
                parent_role_id=parent_role_id,
                child_role_id=child_role_id,
                inheritance_type=inheritance_type,
                conditions=conditions or {}
            )
            
            self.role_hierarchies.append(hierarchy)
            
            # Invalidate all user contexts (hierarchy affects permissions)
            await self._invalidate_all_user_contexts()
            
            self.logger.info(f"Role hierarchy created: {parent_role_id} -> {child_role_id}")
            return hierarchy
            
        except Exception as e:
            self.logger.error(f"Failed to create role hierarchy: {str(e)}")
            raise AuthenticationError(f"Role hierarchy creation failed: {str(e)}")
    
    async def get_effective_roles(
        self,
        user_id: str,
        include_inherited: bool = True
    ) -> List[str]:
        """Get user's effective roles including inherited ones"""
        try:
            effective_roles = set()
            
            # Get direct assignments
            direct_assignments = await self.get_user_roles(user_id)
            for assignment in direct_assignments:
                effective_roles.add(assignment.role_id)
            
            # Get inherited roles if requested
            if include_inherited:
                for assignment in direct_assignments:
                    inherited_roles = await self._get_inherited_roles(assignment.role_id)
                    effective_roles.update(inherited_roles)
            
            return list(effective_roles)
            
        except Exception as e:
            self.logger.error(f"Failed to get effective roles for {user_id}: {str(e)}")
            return []
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get role manager health status"""
        try:
            # Calculate expired assignments
            expired_count = 0
            pending_count = 0
            active_count = 0
            
            for assignment in self.assignments.values():
                if assignment.status == RoleStatus.EXPIRED:
                    expired_count += 1
                elif assignment.status == RoleStatus.PENDING:
                    pending_count += 1
                elif assignment.status == RoleStatus.ACTIVE:
                    active_count += 1
            
            return {
                'service': 'RoleManager',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'roles': {
                    'total': len(self.roles),
                    'by_platform_role': {
                        role.value: len([r for r in self.roles.values() if r.platform_role == role])
                        for role in PlatformRole
                    },
                    'by_scope': {
                        scope.value: len([r for r in self.roles.values() if r.scope == scope])
                        for scope in RoleScope
                    }
                },
                'assignments': {
                    'total': len(self.assignments),
                    'active': active_count,
                    'pending': pending_count,
                    'expired': expired_count,
                    'users_with_roles': len(self.user_assignments)
                },
                'delegations': {
                    'total': len(self.delegations),
                    'active': len([d for d in self.delegations.values() if d.active])
                },
                'hierarchies': {
                    'total': len(self.role_hierarchies)
                },
                'cache': {
                    'user_contexts': len(self.user_contexts),
                    'hit_ratio': (
                        self.metrics['context_cache_hits'] / 
                        (self.metrics['context_cache_hits'] + self.metrics['context_cache_misses'])
                        if (self.metrics['context_cache_hits'] + self.metrics['context_cache_misses']) > 0
                        else 0
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'RoleManager',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_roles(self) -> None:
        """Load default platform roles"""
        default_roles = [
            {
                'role_id': 'si_admin',
                'name': 'System Integrator Administrator',
                'platform_role': PlatformRole.SYSTEM_INTEGRATOR,
                'description': 'Administrative access to SI services',
                'scope': RoleScope.GLOBAL,
                'permissions': {
                    'si:manage_all', 'si:configure', 'si:monitor',
                    'erp:integrate', 'invoice:generate', 'certificate:manage'
                },
                'is_system_role': True,
                'delegatable': True,
                'max_delegation_depth': 2
            },
            {
                'role_id': 'app_admin',
                'name': 'Access Point Provider Administrator',
                'platform_role': PlatformRole.ACCESS_POINT_PROVIDER,
                'description': 'Administrative access to APP services',
                'scope': RoleScope.GLOBAL,
                'permissions': {
                    'app:manage_all', 'app:configure', 'app:monitor',
                    'transmission:manage', 'validation:manage', 'crypto:manage'
                },
                'is_system_role': True,
                'delegatable': True,
                'max_delegation_depth': 2
            },
            {
                'role_id': 'hybrid_admin',
                'name': 'Hybrid Role Administrator',
                'platform_role': PlatformRole.HYBRID,
                'description': 'Administrative access to both SI and APP services',
                'scope': RoleScope.GLOBAL,
                'permissions': {
                    'si:manage_all', 'app:manage_all', 'hybrid:manage',
                    'platform:configure', 'platform:monitor'
                },
                'is_system_role': True,
                'delegatable': False
            },
            {
                'role_id': 'platform_admin',
                'name': 'Platform Administrator',
                'platform_role': PlatformRole.PLATFORM_ADMIN,
                'description': 'Full platform administrative access',
                'scope': RoleScope.GLOBAL,
                'permissions': {
                    'platform:manage_all', 'users:manage', 'roles:manage',
                    'tenants:manage', 'system:configure'
                },
                'is_system_role': True,
                'delegatable': False
            },
            {
                'role_id': 'tenant_admin',
                'name': 'Tenant Administrator',
                'platform_role': PlatformRole.TENANT_ADMIN,
                'description': 'Administrative access within tenant scope',
                'scope': RoleScope.TENANT,
                'permissions': {
                    'tenant:manage', 'tenant:configure', 'tenant:monitor',
                    'tenant_users:manage'
                },
                'delegatable': True,
                'max_delegation_depth': 1
            },
            {
                'role_id': 'user',
                'name': 'Regular User',
                'platform_role': PlatformRole.USER,
                'description': 'Standard user access',
                'scope': RoleScope.TENANT,
                'permissions': {
                    'invoices:view', 'invoices:create', 'profile:manage'
                },
                'delegatable': False
            }
        ]
        
        for role_data in default_roles:
            if role_data['role_id'] not in self.roles:
                await self.create_role(**role_data)
    
    async def _setup_default_hierarchies(self) -> None:
        """Setup default role hierarchies"""
        hierarchies = [
            ('platform_admin', 'si_admin'),
            ('platform_admin', 'app_admin'),
            ('platform_admin', 'tenant_admin'),
            ('hybrid_admin', 'si_admin'),
            ('hybrid_admin', 'app_admin'),
            ('tenant_admin', 'user')
        ]
        
        for parent, child in hierarchies:
            try:
                await self.create_role_hierarchy(parent, child)
            except Exception as e:
                self.logger.warning(f"Failed to create hierarchy {parent} -> {child}: {str(e)}")
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Expiration checker
        async def expiration_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Check every hour
                    await self._check_expired_assignments()
                except Exception as e:
                    self.logger.error(f"Expiration worker error: {str(e)}")
                    await asyncio.sleep(60)
        
        # Context cache cleanup
        async def cache_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    await self._cleanup_context_cache()
                except Exception as e:
                    self.logger.error(f"Cache cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        self.background_tasks['expiration'] = asyncio.create_task(expiration_worker())
        self.background_tasks['cache_cleanup'] = asyncio.create_task(cache_cleanup_worker())
    
    async def _find_existing_assignment(
        self,
        user_id: str,
        role_id: str,
        scope: RoleScope,
        tenant_id: Optional[str] = None,
        service_id: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Optional[RoleAssignment]:
        """Find existing role assignment"""
        if user_id not in self.user_assignments:
            return None
        
        for assignment_id in self.user_assignments[user_id]:
            if assignment_id not in self.assignments:
                continue
            
            assignment = self.assignments[assignment_id]
            
            if (assignment.role_id == role_id and 
                assignment.scope == scope and
                assignment.tenant_id == tenant_id and
                assignment.service_id == service_id and
                assignment.environment == environment):
                return assignment
        
        return None
    
    async def _calculate_effective_permissions(
        self,
        user_id: str,
        assignments: List[RoleAssignment]
    ) -> Set[str]:
        """Calculate user's effective permissions"""
        effective_permissions = set()
        
        for assignment in assignments:
            if assignment.role_id in self.roles:
                role = self.roles[assignment.role_id]
                effective_permissions.update(role.permissions)
                
                # Add inherited permissions
                if role.hierarchical:
                    inherited_permissions = await self._get_inherited_permissions(assignment.role_id)
                    effective_permissions.update(inherited_permissions)
        
        return effective_permissions
    
    async def _get_inherited_roles(self, role_id: str) -> Set[str]:
        """Get roles inherited from role hierarchy"""
        inherited = set()
        
        for hierarchy in self.role_hierarchies:
            if hierarchy.parent_role_id == role_id:
                inherited.add(hierarchy.child_role_id)
                # Recursively get inherited roles
                child_inherited = await self._get_inherited_roles(hierarchy.child_role_id)
                inherited.update(child_inherited)
        
        self.metrics['hierarchy_evaluations'] += 1
        return inherited
    
    async def _get_inherited_permissions(self, role_id: str) -> Set[str]:
        """Get permissions inherited from role hierarchy"""
        inherited_permissions = set()
        
        for hierarchy in self.role_hierarchies:
            if (hierarchy.parent_role_id == role_id and 
                hierarchy.inheritance_type == "permissions"):
                
                if hierarchy.child_role_id in self.roles:
                    child_role = self.roles[hierarchy.child_role_id]
                    inherited_permissions.update(child_role.permissions)
                    
                    # Recursively get inherited permissions
                    child_inherited = await self._get_inherited_permissions(hierarchy.child_role_id)
                    inherited_permissions.update(child_inherited)
        
        return inherited_permissions
    
    async def _user_has_role(
        self,
        user_id: str,
        role_id: str,
        scope: RoleScope
    ) -> bool:
        """Check if user has specific role"""
        user_roles = await self.get_user_roles(user_id, scope)
        return any(assignment.role_id == role_id for assignment in user_roles)
    
    async def _get_delegation_depth(self, user_id: str, role_id: str) -> int:
        """Get delegation depth for user's role"""
        # Find the assignment and check delegation chain
        user_roles = await self.get_user_roles(user_id)
        
        for assignment in user_roles:
            if assignment.role_id == role_id and assignment.assignment_type == AssignmentType.DELEGATED:
                return assignment.delegation_depth + 1
        
        return 0
    
    async def _would_create_circular_hierarchy(self, parent_role_id: str, child_role_id: str) -> bool:
        """Check if adding hierarchy would create circular dependency"""
        visited = set()
        
        def has_path(current: str, target: str) -> bool:
            if current == target:
                return True
            if current in visited:
                return False
            
            visited.add(current)
            
            for hierarchy in self.role_hierarchies:
                if hierarchy.parent_role_id == current:
                    if has_path(hierarchy.child_role_id, target):
                        return True
            
            return False
        
        return has_path(child_role_id, parent_role_id)
    
    async def _invalidate_user_context(self, user_id: str) -> None:
        """Invalidate user's cached context"""
        if user_id in self.user_contexts:
            del self.user_contexts[user_id]
        if user_id in self.context_timestamps:
            del self.context_timestamps[user_id]
    
    async def _invalidate_all_user_contexts(self) -> None:
        """Invalidate all cached user contexts"""
        self.user_contexts.clear()
        self.context_timestamps.clear()
    
    async def _check_expired_assignments(self) -> None:
        """Check and mark expired assignments"""
        now = datetime.utcnow()
        expired_count = 0
        
        for assignment in self.assignments.values():
            if (assignment.expires_at and 
                assignment.expires_at <= now and 
                assignment.status == RoleStatus.ACTIVE):
                
                assignment.status = RoleStatus.EXPIRED
                assignment.updated_at = now
                expired_count += 1
                
                # Invalidate user context
                await self._invalidate_user_context(assignment.user_id)
        
        if expired_count > 0:
            self.logger.info(f"Marked {expired_count} assignments as expired")
    
    async def _cleanup_context_cache(self) -> None:
        """Clean up expired context cache entries"""
        now = datetime.utcnow()
        expired_users = []
        
        for user_id, timestamp in self.context_timestamps.items():
            if now - timestamp > self.context_cache_ttl:
                expired_users.append(user_id)
        
        for user_id in expired_users:
            await self._invalidate_user_context(user_id)
        
        if expired_users:
            self.logger.debug(f"Cleaned up {len(expired_users)} expired context cache entries")
    
    async def _notify_change_listeners(self, event: str, user_id: str, assignment: RoleAssignment) -> None:
        """Notify change listeners"""
        for listener in self.change_listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event, user_id, assignment)
                else:
                    listener(event, user_id, assignment)
            except Exception as e:
                self.logger.error(f"Change listener error: {str(e)}")
    
    async def _log_audit_entry(
        self,
        action: str,
        actor: str,
        target: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit entry"""
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'actor': actor,
            'target': target,
            'details': details or {},
            'service': 'RoleManager'
        }
        
        self.audit_log.append(entry)
        
        # Limit audit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
    
    async def cleanup(self) -> None:
        """Cleanup role manager resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.user_contexts.clear()
            self.context_timestamps.clear()
            
            self.logger.info("RoleManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during RoleManager cleanup: {str(e)}")