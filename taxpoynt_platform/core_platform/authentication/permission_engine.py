"""
Permission Engine Service

This service implements role-based permission system for the TaxPoynt platform,
providing fine-grained access control and permission evaluation.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import re
import fnmatch

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError
)


class PermissionType(Enum):
    """Permission type definitions"""
    ACTION = "action"  # Specific action permission
    RESOURCE = "resource"  # Resource access permission
    ATTRIBUTE = "attribute"  # Attribute-level permission
    CONDITION = "condition"  # Conditional permission
    SCOPE = "scope"  # Scope-based permission


class AccessLevel(Enum):
    """Access level definitions"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    FULL = "full"


class PermissionEffect(Enum):
    """Permission effect"""
    ALLOW = "allow"
    DENY = "deny"


class ResourceType(Enum):
    """Resource type definitions"""
    INVOICE = "invoice"
    CERTIFICATE = "certificate"
    USER = "user"
    TENANT = "tenant"
    CONFIGURATION = "configuration"
    SECRET = "secret"
    AUDIT_LOG = "audit_log"
    SYSTEM = "system"


@dataclass
class Permission:
    """Permission definition"""
    permission_id: str
    name: str
    description: str
    permission_type: PermissionType
    resource_type: Optional[ResourceType] = None
    action: Optional[str] = None
    effect: PermissionEffect = PermissionEffect.ALLOW
    conditions: Dict[str, Any] = field(default_factory=dict)
    attributes: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionPolicy:
    """Permission policy definition"""
    policy_id: str
    name: str
    description: str
    rules: List[Dict[str, Any]] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class PermissionContext:
    """Context for permission evaluation"""
    user_id: str
    roles: Set[str] = field(default_factory=set)
    tenant_id: Optional[str] = None
    environment: Optional[str] = None
    service_id: Optional[str] = None
    resource_id: Optional[str] = None
    resource_type: Optional[ResourceType] = None
    action: Optional[str] = None
    request_time: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PermissionEvaluation:
    """Permission evaluation result"""
    granted: bool
    permission_id: str
    user_id: str
    resource_type: Optional[ResourceType] = None
    action: Optional[str] = None
    effect: PermissionEffect = PermissionEffect.ALLOW
    reason: str = "default"
    matched_policies: List[str] = field(default_factory=list)
    conditions_met: bool = True
    evaluation_time: datetime = field(default_factory=datetime.utcnow)
    cache_hit: bool = False


@dataclass
class ResourcePermission:
    """Resource-specific permission"""
    resource_id: str
    resource_type: ResourceType
    permissions: Dict[str, AccessLevel] = field(default_factory=dict)
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    shared_with: Set[str] = field(default_factory=set)
    public: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConditionRule:
    """Condition rule for permission evaluation"""
    rule_id: str
    name: str
    condition_type: str  # time, location, attribute, custom
    operator: str  # eq, ne, in, not_in, gt, lt, contains, regex
    value: Any
    description: str = ""
    active: bool = True


class PermissionEngine(BaseService):
    """
    Permission Engine Service
    
    Implements role-based permission system for the TaxPoynt platform,
    providing fine-grained access control and permission evaluation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Permission definitions
        self.permissions: Dict[str, Permission] = {}
        self.policies: Dict[str, PermissionPolicy] = {}
        self.condition_rules: Dict[str, ConditionRule] = {}
        
        # Resource permissions
        self.resource_permissions: Dict[str, ResourcePermission] = {}
        
        # Role-permission mappings
        self.role_permissions: Dict[str, Set[str]] = {}  # role_id -> permission_ids
        
        # Permission hierarchy
        self.permission_hierarchy: Dict[str, Set[str]] = {}  # parent -> children
        
        # Evaluation cache
        self.evaluation_cache: Dict[str, PermissionEvaluation] = {}
        self.cache_ttl: timedelta = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Condition evaluators
        self.condition_evaluators: Dict[str, Callable] = {}
        
        # Permission templates
        self.permission_templates: Dict[str, Dict[str, Any]] = {}
        
        # Audit and monitoring
        self.evaluation_log: List[Dict[str, Any]] = []
        self.access_patterns: Dict[str, int] = {}
        
        # Performance metrics
        self.metrics = {
            'permissions_managed': 0,
            'policies_managed': 0,
            'evaluations_performed': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'policy_matches': 0,
            'condition_evaluations': 0,
            'access_granted': 0,
            'access_denied': 0
        }
        
        # Background tasks
        self.background_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize permission engine"""
        try:
            self.logger.info("Initializing PermissionEngine")
            
            # Load default permissions
            await self._load_default_permissions()
            
            # Load default policies
            await self._load_default_policies()
            
            # Initialize condition evaluators
            await self._initialize_condition_evaluators()
            
            # Load permission templates
            await self._load_permission_templates()
            
            # Start background workers
            await self._start_background_workers()
            
            self.logger.info("PermissionEngine initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize PermissionEngine: {str(e)}")
            raise AuthenticationError(f"Initialization failed: {str(e)}")
    
    async def create_permission(
        self,
        permission_id: str,
        name: str,
        description: str,
        permission_type: PermissionType,
        resource_type: Optional[ResourceType] = None,
        action: Optional[str] = None,
        effect: PermissionEffect = PermissionEffect.ALLOW,
        conditions: Optional[Dict[str, Any]] = None,
        attributes: Optional[Set[str]] = None,
        created_by: str = "system"
    ) -> Permission:
        """Create a new permission"""
        try:
            # Validate permission doesn't exist
            if permission_id in self.permissions:
                raise ValidationError(f"Permission {permission_id} already exists")
            
            # Create permission
            permission = Permission(
                permission_id=permission_id,
                name=name,
                description=description,
                permission_type=permission_type,
                resource_type=resource_type,
                action=action,
                effect=effect,
                conditions=conditions or {},
                attributes=attributes or set(),
                created_by=created_by
            )
            
            # Store permission
            self.permissions[permission_id] = permission
            
            self.metrics['permissions_managed'] += 1
            self.logger.info(f"Permission created: {permission_id}")
            
            return permission
            
        except Exception as e:
            self.logger.error(f"Failed to create permission {permission_id}: {str(e)}")
            raise AuthenticationError(f"Permission creation failed: {str(e)}")
    
    async def create_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        rules: List[Dict[str, Any]],
        conditions: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        created_by: str = "system"
    ) -> PermissionPolicy:
        """Create a new permission policy"""
        try:
            # Validate policy doesn't exist
            if policy_id in self.policies:
                raise ValidationError(f"Policy {policy_id} already exists")
            
            # Validate rules
            await self._validate_policy_rules(rules)
            
            # Create policy
            policy = PermissionPolicy(
                policy_id=policy_id,
                name=name,
                description=description,
                rules=rules,
                conditions=conditions or {},
                priority=priority,
                created_by=created_by
            )
            
            # Store policy
            self.policies[policy_id] = policy
            
            self.metrics['policies_managed'] += 1
            self.logger.info(f"Policy created: {policy_id}")
            
            return policy
            
        except Exception as e:
            self.logger.error(f"Failed to create policy {policy_id}: {str(e)}")
            raise AuthenticationError(f"Policy creation failed: {str(e)}")
    
    async def assign_permission_to_role(
        self,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Assign permission to role"""
        try:
            # Validate permission exists
            if permission_id not in self.permissions:
                raise ValidationError(f"Permission {permission_id} not found")
            
            # Add to role permissions
            if role_id not in self.role_permissions:
                self.role_permissions[role_id] = set()
            
            self.role_permissions[role_id].add(permission_id)
            
            # Clear evaluation cache for this role
            await self._clear_role_cache(role_id)
            
            self.logger.info(f"Permission {permission_id} assigned to role {role_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to assign permission {permission_id} to role {role_id}: {str(e)}")
            return False
    
    async def revoke_permission_from_role(
        self,
        role_id: str,
        permission_id: str
    ) -> bool:
        """Revoke permission from role"""
        try:
            if role_id in self.role_permissions:
                self.role_permissions[role_id].discard(permission_id)
                
                # Clear evaluation cache for this role
                await self._clear_role_cache(role_id)
                
                self.logger.info(f"Permission {permission_id} revoked from role {role_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke permission {permission_id} from role {role_id}: {str(e)}")
            return False
    
    async def evaluate_permission(
        self,
        context: PermissionContext,
        permission_id: str,
        use_cache: bool = True
    ) -> PermissionEvaluation:
        """Evaluate permission for given context"""
        try:
            # Check cache first
            if use_cache:
                cached_result = await self._get_from_cache(context, permission_id)
                if cached_result:
                    cached_result.cache_hit = True
                    return cached_result
            
            # Validate permission exists
            if permission_id not in self.permissions:
                return PermissionEvaluation(
                    granted=False,
                    permission_id=permission_id,
                    user_id=context.user_id,
                    reason="permission_not_found"
                )
            
            permission = self.permissions[permission_id]
            
            # Check if user has permission through roles
            has_permission = await self._check_role_permission(context.roles, permission_id)
            if not has_permission:
                result = PermissionEvaluation(
                    granted=False,
                    permission_id=permission_id,
                    user_id=context.user_id,
                    resource_type=context.resource_type,
                    action=context.action,
                    reason="role_permission_denied"
                )
                await self._cache_evaluation(context, permission_id, result)
                self.metrics['access_denied'] += 1
                return result
            
            # Evaluate policies
            policy_result = await self._evaluate_policies(context, permission)
            if not policy_result['granted']:
                result = PermissionEvaluation(
                    granted=False,
                    permission_id=permission_id,
                    user_id=context.user_id,
                    resource_type=context.resource_type,
                    action=context.action,
                    reason=policy_result['reason'],
                    matched_policies=policy_result['matched_policies']
                )
                await self._cache_evaluation(context, permission_id, result)
                self.metrics['access_denied'] += 1
                return result
            
            # Evaluate conditions
            conditions_result = await self._evaluate_conditions(context, permission)
            if not conditions_result['met']:
                result = PermissionEvaluation(
                    granted=False,
                    permission_id=permission_id,
                    user_id=context.user_id,
                    resource_type=context.resource_type,
                    action=context.action,
                    effect=permission.effect,
                    reason=conditions_result['reason'],
                    conditions_met=False
                )
                await self._cache_evaluation(context, permission_id, result)
                self.metrics['access_denied'] += 1
                return result
            
            # Check resource-specific permissions
            if context.resource_id and context.resource_type:
                resource_allowed = await self._check_resource_permission(
                    context.user_id, context.resource_id, context.resource_type, context.action
                )
                if not resource_allowed:
                    result = PermissionEvaluation(
                        granted=False,
                        permission_id=permission_id,
                        user_id=context.user_id,
                        resource_type=context.resource_type,
                        action=context.action,
                        reason="resource_permission_denied"
                    )
                    await self._cache_evaluation(context, permission_id, result)
                    self.metrics['access_denied'] += 1
                    return result
            
            # Permission granted
            result = PermissionEvaluation(
                granted=True,
                permission_id=permission_id,
                user_id=context.user_id,
                resource_type=context.resource_type,
                action=context.action,
                effect=permission.effect,
                reason="permission_granted",
                matched_policies=policy_result['matched_policies'],
                conditions_met=True
            )
            
            # Cache result
            await self._cache_evaluation(context, permission_id, result)
            
            # Log evaluation
            await self._log_evaluation(context, result)
            
            self.metrics['evaluations_performed'] += 1
            self.metrics['access_granted'] += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to evaluate permission {permission_id}: {str(e)}")
            return PermissionEvaluation(
                granted=False,
                permission_id=permission_id,
                user_id=context.user_id,
                reason=f"evaluation_error: {str(e)}"
            )
    
    async def check_action_permission(
        self,
        user_id: str,
        action: str,
        resource_type: Optional[ResourceType] = None,
        resource_id: Optional[str] = None,
        roles: Optional[Set[str]] = None,
        tenant_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if user has permission for specific action"""
        try:
            # Create context
            context = PermissionContext(
                user_id=user_id,
                roles=roles or set(),
                tenant_id=tenant_id,
                resource_id=resource_id,
                resource_type=resource_type,
                action=action,
                additional_context=additional_context or {}
            )
            
            # Find relevant permissions for this action/resource
            relevant_permissions = await self._find_relevant_permissions(action, resource_type)
            
            # Evaluate each permission
            for permission_id in relevant_permissions:
                evaluation = await self.evaluate_permission(context, permission_id)
                if evaluation.granted:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to check action permission for {user_id}: {str(e)}")
            return False
    
    async def get_user_permissions(
        self,
        user_id: str,
        roles: Set[str],
        tenant_id: Optional[str] = None,
        resource_type: Optional[ResourceType] = None
    ) -> Set[str]:
        """Get all permissions for user"""
        try:
            user_permissions = set()
            
            # Get permissions from roles
            for role_id in roles:
                if role_id in self.role_permissions:
                    role_perms = self.role_permissions[role_id]
                    
                    # Filter by resource type if specified
                    if resource_type:
                        filtered_perms = set()
                        for perm_id in role_perms:
                            if perm_id in self.permissions:
                                perm = self.permissions[perm_id]
                                if not perm.resource_type or perm.resource_type == resource_type:
                                    filtered_perms.add(perm_id)
                        user_permissions.update(filtered_perms)
                    else:
                        user_permissions.update(role_perms)
            
            # Add inherited permissions
            inherited_permissions = await self._get_inherited_permissions(user_permissions)
            user_permissions.update(inherited_permissions)
            
            return user_permissions
            
        except Exception as e:
            self.logger.error(f"Failed to get user permissions for {user_id}: {str(e)}")
            return set()
    
    async def create_resource_permission(
        self,
        resource_id: str,
        resource_type: ResourceType,
        owner_id: str,
        tenant_id: Optional[str] = None,
        permissions: Optional[Dict[str, AccessLevel]] = None
    ) -> ResourcePermission:
        """Create resource-specific permission"""
        try:
            resource_permission = ResourcePermission(
                resource_id=resource_id,
                resource_type=resource_type,
                owner_id=owner_id,
                tenant_id=tenant_id,
                permissions=permissions or {}
            )
            
            self.resource_permissions[resource_id] = resource_permission
            
            self.logger.info(f"Resource permission created: {resource_id}")
            return resource_permission
            
        except Exception as e:
            self.logger.error(f"Failed to create resource permission {resource_id}: {str(e)}")
            raise AuthenticationError(f"Resource permission creation failed: {str(e)}")
    
    async def grant_resource_access(
        self,
        resource_id: str,
        user_id: str,
        access_level: AccessLevel,
        granted_by: str
    ) -> bool:
        """Grant user access to specific resource"""
        try:
            if resource_id not in self.resource_permissions:
                raise ValidationError(f"Resource {resource_id} not found")
            
            resource_perm = self.resource_permissions[resource_id]
            resource_perm.permissions[user_id] = access_level
            resource_perm.updated_at = datetime.utcnow()
            
            # Clear cache for this resource
            await self._clear_resource_cache(resource_id)
            
            self.logger.info(f"Resource access granted: {resource_id} to {user_id} ({access_level.value})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to grant resource access: {str(e)}")
            return False
    
    async def revoke_resource_access(
        self,
        resource_id: str,
        user_id: str,
        revoked_by: str
    ) -> bool:
        """Revoke user access from specific resource"""
        try:
            if resource_id not in self.resource_permissions:
                return False
            
            resource_perm = self.resource_permissions[resource_id]
            if user_id in resource_perm.permissions:
                del resource_perm.permissions[user_id]
                resource_perm.updated_at = datetime.utcnow()
                
                # Clear cache for this resource
                await self._clear_resource_cache(resource_id)
                
                self.logger.info(f"Resource access revoked: {resource_id} from {user_id}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to revoke resource access: {str(e)}")
            return False
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get permission engine health status"""
        try:
            return {
                'service': 'PermissionEngine',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'permissions': {
                    'total': len(self.permissions),
                    'by_type': {
                        perm_type.value: len([p for p in self.permissions.values() if p.permission_type == perm_type])
                        for perm_type in PermissionType
                    },
                    'by_resource_type': {
                        res_type.value: len([p for p in self.permissions.values() if p.resource_type == res_type])
                        for res_type in ResourceType
                    }
                },
                'policies': {
                    'total': len(self.policies),
                    'active': len([p for p in self.policies.values() if p.active])
                },
                'role_permissions': {
                    'roles_with_permissions': len(self.role_permissions),
                    'total_mappings': sum(len(perms) for perms in self.role_permissions.values())
                },
                'resource_permissions': {
                    'total': len(self.resource_permissions),
                    'by_type': {
                        res_type.value: len([r for r in self.resource_permissions.values() if r.resource_type == res_type])
                        for res_type in ResourceType
                    }
                },
                'cache': {
                    'size': len(self.evaluation_cache),
                    'hit_ratio': (
                        self.metrics['cache_hits'] / 
                        (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
                        else 0
                    )
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'PermissionEngine',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_permissions(self) -> None:
        """Load default system permissions"""
        default_permissions = [
            # SI Permissions
            {
                'permission_id': 'si:invoice:create',
                'name': 'Create Invoice (SI)',
                'description': 'Create invoices through SI services',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.INVOICE,
                'action': 'create'
            },
            {
                'permission_id': 'si:certificate:manage',
                'name': 'Manage Certificates (SI)',
                'description': 'Manage digital certificates',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.CERTIFICATE,
                'action': 'manage'
            },
            {
                'permission_id': 'si:erp:integrate',
                'name': 'ERP Integration',
                'description': 'Integrate with ERP systems',
                'permission_type': PermissionType.ACTION,
                'action': 'integrate'
            },
            
            # APP Permissions
            {
                'permission_id': 'app:transmission:manage',
                'name': 'Manage Transmission (APP)',
                'description': 'Manage secure transmission',
                'permission_type': PermissionType.ACTION,
                'action': 'transmit'
            },
            {
                'permission_id': 'app:validation:perform',
                'name': 'Perform Validation (APP)',
                'description': 'Perform data validation',
                'permission_type': PermissionType.ACTION,
                'action': 'validate'
            },
            {
                'permission_id': 'app:crypto:manage',
                'name': 'Manage Cryptography (APP)',
                'description': 'Manage cryptographic operations',
                'permission_type': PermissionType.ACTION,
                'action': 'crypto_manage'
            },
            
            # Platform Permissions
            {
                'permission_id': 'platform:users:manage',
                'name': 'Manage Users',
                'description': 'Manage platform users',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.USER,
                'action': 'manage'
            },
            {
                'permission_id': 'platform:tenants:manage',
                'name': 'Manage Tenants',
                'description': 'Manage platform tenants',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.TENANT,
                'action': 'manage'
            },
            {
                'permission_id': 'platform:config:manage',
                'name': 'Manage Configuration',
                'description': 'Manage platform configuration',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.CONFIGURATION,
                'action': 'manage'
            },
            {
                'permission_id': 'platform:secrets:manage',
                'name': 'Manage Secrets',
                'description': 'Manage platform secrets',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.SECRET,
                'action': 'manage'
            },
            
            # Tenant Permissions
            {
                'permission_id': 'tenant:invoices:view',
                'name': 'View Invoices',
                'description': 'View tenant invoices',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.INVOICE,
                'action': 'view'
            },
            {
                'permission_id': 'tenant:profile:manage',
                'name': 'Manage Profile',
                'description': 'Manage user profile',
                'permission_type': PermissionType.ACTION,
                'resource_type': ResourceType.USER,
                'action': 'profile_manage'
            }
        ]
        
        for perm_data in default_permissions:
            if perm_data['permission_id'] not in self.permissions:
                await self.create_permission(**perm_data)
    
    async def _load_default_policies(self) -> None:
        """Load default permission policies"""
        default_policies = [
            {
                'policy_id': 'si_access_policy',
                'name': 'SI Access Policy',
                'description': 'Policy for SI service access',
                'rules': [
                    {
                        'effect': 'allow',
                        'permissions': ['si:*'],
                        'conditions': {
                            'role': ['system_integrator', 'hybrid', 'platform_admin']
                        }
                    }
                ],
                'priority': 100
            },
            {
                'policy_id': 'app_access_policy',
                'name': 'APP Access Policy',
                'description': 'Policy for APP service access',
                'rules': [
                    {
                        'effect': 'allow',
                        'permissions': ['app:*'],
                        'conditions': {
                            'role': ['access_point_provider', 'hybrid', 'platform_admin']
                        }
                    }
                ],
                'priority': 100
            },
            {
                'policy_id': 'tenant_isolation_policy',
                'name': 'Tenant Isolation Policy',
                'description': 'Ensure tenant data isolation',
                'rules': [
                    {
                        'effect': 'deny',
                        'permissions': ['tenant:*'],
                        'conditions': {
                            'tenant_mismatch': True
                        }
                    }
                ],
                'priority': 200
            },
            {
                'policy_id': 'time_based_policy',
                'name': 'Time-based Access Policy',
                'description': 'Restrict access based on time',
                'rules': [
                    {
                        'effect': 'deny',
                        'permissions': ['platform:*'],
                        'conditions': {
                            'time_restriction': {
                                'start_time': '22:00',
                                'end_time': '06:00',
                                'timezone': 'UTC',
                                'exclude_roles': ['platform_admin']
                            }
                        }
                    }
                ],
                'priority': 150
            }
        ]
        
        for policy_data in default_policies:
            if policy_data['policy_id'] not in self.policies:
                await self.create_policy(**policy_data)
    
    async def _initialize_condition_evaluators(self) -> None:
        """Initialize condition evaluators"""
        self.condition_evaluators = {
            'role': self._evaluate_role_condition,
            'tenant_mismatch': self._evaluate_tenant_mismatch_condition,
            'time_restriction': self._evaluate_time_restriction_condition,
            'ip_whitelist': self._evaluate_ip_whitelist_condition,
            'resource_owner': self._evaluate_resource_owner_condition,
            'custom': self._evaluate_custom_condition
        }
    
    async def _load_permission_templates(self) -> None:
        """Load permission templates"""
        self.permission_templates = {
            'crud_template': {
                'create': AccessLevel.WRITE,
                'read': AccessLevel.READ,
                'update': AccessLevel.WRITE,
                'delete': AccessLevel.DELETE
            },
            'admin_template': {
                'manage': AccessLevel.ADMIN,
                'configure': AccessLevel.ADMIN,
                'monitor': AccessLevel.READ
            },
            'user_template': {
                'view': AccessLevel.READ,
                'edit_own': AccessLevel.WRITE
            }
        }
    
    async def _start_background_workers(self) -> None:
        """Start background worker tasks"""
        # Cache cleanup worker
        async def cache_cleanup_worker():
            while True:
                try:
                    await asyncio.sleep(1800)  # Check every 30 minutes
                    await self._cleanup_evaluation_cache()
                except Exception as e:
                    self.logger.error(f"Cache cleanup worker error: {str(e)}")
                    await asyncio.sleep(300)
        
        # Access pattern analysis worker
        async def pattern_analysis_worker():
            while True:
                try:
                    await asyncio.sleep(3600)  # Analyze every hour
                    await self._analyze_access_patterns()
                except Exception as e:
                    self.logger.error(f"Pattern analysis worker error: {str(e)}")
                    await asyncio.sleep(600)
        
        self.background_tasks['cache_cleanup'] = asyncio.create_task(cache_cleanup_worker())
        self.background_tasks['pattern_analysis'] = asyncio.create_task(pattern_analysis_worker())
    
    async def _validate_policy_rules(self, rules: List[Dict[str, Any]]) -> None:
        """Validate policy rules"""
        for rule in rules:
            if 'effect' not in rule or rule['effect'] not in ['allow', 'deny']:
                raise ValidationError("Policy rule must have valid effect (allow/deny)")
            
            if 'permissions' not in rule:
                raise ValidationError("Policy rule must specify permissions")
    
    async def _check_role_permission(self, roles: Set[str], permission_id: str) -> bool:
        """Check if any of the roles have the permission"""
        for role_id in roles:
            if role_id in self.role_permissions:
                if permission_id in self.role_permissions[role_id]:
                    return True
                
                # Check for wildcard permissions
                for perm in self.role_permissions[role_id]:
                    if self._matches_wildcard_permission(perm, permission_id):
                        return True
        
        return False
    
    async def _evaluate_policies(self, context: PermissionContext, permission: Permission) -> Dict[str, Any]:
        """Evaluate policies for permission"""
        matched_policies = []
        final_decision = True
        reason = "policy_allowed"
        
        # Sort policies by priority (higher priority first)
        sorted_policies = sorted(
            self.policies.values(),
            key=lambda p: p.priority,
            reverse=True
        )
        
        for policy in sorted_policies:
            if not policy.active:
                continue
            
            # Check if policy applies to this permission
            if await self._policy_applies_to_permission(policy, permission.permission_id):
                matched_policies.append(policy.policy_id)
                
                # Evaluate policy rules
                for rule in policy.rules:
                    if await self._evaluate_policy_rule(rule, context, permission):
                        if rule['effect'] == 'deny':
                            final_decision = False
                            reason = f"denied_by_policy_{policy.policy_id}"
                            break
                        elif rule['effect'] == 'allow':
                            # Allow continues evaluation
                            pass
                
                # If denied by a policy, stop evaluation
                if not final_decision:
                    break
        
        self.metrics['policy_matches'] += len(matched_policies)
        
        return {
            'granted': final_decision,
            'reason': reason,
            'matched_policies': matched_policies
        }
    
    async def _evaluate_conditions(self, context: PermissionContext, permission: Permission) -> Dict[str, Any]:
        """Evaluate permission conditions"""
        if not permission.conditions:
            return {'met': True, 'reason': 'no_conditions'}
        
        for condition_type, condition_value in permission.conditions.items():
            if condition_type in self.condition_evaluators:
                evaluator = self.condition_evaluators[condition_type]
                result = await evaluator(context, condition_value)
                
                if not result:
                    self.metrics['condition_evaluations'] += 1
                    return {'met': False, 'reason': f'condition_failed_{condition_type}'}
        
        self.metrics['condition_evaluations'] += 1
        return {'met': True, 'reason': 'conditions_satisfied'}
    
    async def _check_resource_permission(
        self,
        user_id: str,
        resource_id: str,
        resource_type: ResourceType,
        action: Optional[str]
    ) -> bool:
        """Check resource-specific permission"""
        if resource_id not in self.resource_permissions:
            return True  # No specific resource permissions, allow
        
        resource_perm = self.resource_permissions[resource_id]
        
        # Check if user is owner
        if resource_perm.owner_id == user_id:
            return True
        
        # Check if resource is public
        if resource_perm.public:
            return True
        
        # Check explicit permissions
        if user_id in resource_perm.permissions:
            user_access = resource_perm.permissions[user_id]
            return self._access_level_allows_action(user_access, action)
        
        # Check if user is in shared list
        if user_id in resource_perm.shared_with:
            return True
        
        return False
    
    async def _find_relevant_permissions(
        self,
        action: str,
        resource_type: Optional[ResourceType]
    ) -> Set[str]:
        """Find permissions relevant to action and resource type"""
        relevant = set()
        
        for perm_id, permission in self.permissions.items():
            # Check action match
            if permission.action:
                if permission.action == action or self._matches_wildcard_permission(permission.action, action):
                    relevant.add(perm_id)
            
            # Check resource type match
            if resource_type and permission.resource_type == resource_type:
                relevant.add(perm_id)
            
            # Check wildcard permissions
            if permission.action == '*' or perm_id.endswith(':*'):
                relevant.add(perm_id)
        
        return relevant
    
    async def _get_inherited_permissions(self, base_permissions: Set[str]) -> Set[str]:
        """Get inherited permissions from hierarchy"""
        inherited = set()
        
        for perm_id in base_permissions:
            if perm_id in self.permission_hierarchy:
                inherited.update(self.permission_hierarchy[perm_id])
        
        return inherited
    
    async def _policy_applies_to_permission(self, policy: PermissionPolicy, permission_id: str) -> bool:
        """Check if policy applies to permission"""
        for rule in policy.rules:
            permissions = rule.get('permissions', [])
            for perm_pattern in permissions:
                if self._matches_wildcard_permission(perm_pattern, permission_id):
                    return True
        
        return False
    
    async def _evaluate_policy_rule(
        self,
        rule: Dict[str, Any],
        context: PermissionContext,
        permission: Permission
    ) -> bool:
        """Evaluate individual policy rule"""
        conditions = rule.get('conditions', {})
        
        for condition_type, condition_value in conditions.items():
            if condition_type in self.condition_evaluators:
                evaluator = self.condition_evaluators[condition_type]
                if not await evaluator(context, condition_value):
                    return False
        
        return True
    
    async def _evaluate_role_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate role-based condition"""
        required_roles = condition_value if isinstance(condition_value, list) else [condition_value]
        return any(role in context.roles for role in required_roles)
    
    async def _evaluate_tenant_mismatch_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate tenant mismatch condition"""
        if condition_value and context.tenant_id:
            # Check if user's tenant matches resource tenant
            # This would require additional context about user's tenant
            return False  # For safety, assume mismatch
        return True
    
    async def _evaluate_time_restriction_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate time-based condition"""
        if not isinstance(condition_value, dict):
            return True
        
        start_time = condition_value.get('start_time')
        end_time = condition_value.get('end_time')
        exclude_roles = condition_value.get('exclude_roles', [])
        
        # Check if user has excluded role
        if any(role in context.roles for role in exclude_roles):
            return True
        
        # Check time restriction
        if start_time and end_time:
            current_time = context.request_time.strftime('%H:%M')
            if start_time <= current_time <= end_time:
                return False  # Restricted time
        
        return True
    
    async def _evaluate_ip_whitelist_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate IP whitelist condition"""
        if not context.ip_address:
            return False
        
        allowed_ips = condition_value if isinstance(condition_value, list) else [condition_value]
        return context.ip_address in allowed_ips
    
    async def _evaluate_resource_owner_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate resource owner condition"""
        if not context.resource_id:
            return True
        
        if context.resource_id in self.resource_permissions:
            resource_perm = self.resource_permissions[context.resource_id]
            return resource_perm.owner_id == context.user_id
        
        return True
    
    async def _evaluate_custom_condition(self, context: PermissionContext, condition_value: Any) -> bool:
        """Evaluate custom condition"""
        # Implement custom condition logic based on condition_value
        return True
    
    def _matches_wildcard_permission(self, pattern: str, permission: str) -> bool:
        """Check if permission matches wildcard pattern"""
        return fnmatch.fnmatch(permission, pattern)
    
    def _access_level_allows_action(self, access_level: AccessLevel, action: Optional[str]) -> bool:
        """Check if access level allows action"""
        if access_level == AccessLevel.FULL:
            return True
        
        action_mappings = {
            'read': [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
            'view': [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ADMIN],
            'create': [AccessLevel.WRITE, AccessLevel.ADMIN],
            'update': [AccessLevel.WRITE, AccessLevel.ADMIN],
            'delete': [AccessLevel.DELETE, AccessLevel.ADMIN],
            'manage': [AccessLevel.ADMIN]
        }
        
        if action and action in action_mappings:
            return access_level in action_mappings[action]
        
        return access_level != AccessLevel.NONE
    
    async def _get_from_cache(self, context: PermissionContext, permission_id: str) -> Optional[PermissionEvaluation]:
        """Get evaluation from cache"""
        cache_key = self._get_cache_key(context, permission_id)
        
        if cache_key in self.evaluation_cache:
            timestamp = self.cache_timestamps.get(cache_key)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                return self.evaluation_cache[cache_key]
            else:
                # Remove expired entry
                del self.evaluation_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
        
        self.metrics['cache_misses'] += 1
        return None
    
    async def _cache_evaluation(
        self,
        context: PermissionContext,
        permission_id: str,
        evaluation: PermissionEvaluation
    ) -> None:
        """Cache evaluation result"""
        cache_key = self._get_cache_key(context, permission_id)
        self.evaluation_cache[cache_key] = evaluation
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size
        if len(self.evaluation_cache) > 10000:
            # Remove oldest entries
            sorted_items = sorted(
                self.cache_timestamps.items(),
                key=lambda x: x[1]
            )
            for old_key, _ in sorted_items[:5000]:
                if old_key in self.evaluation_cache:
                    del self.evaluation_cache[old_key]
                del self.cache_timestamps[old_key]
    
    def _get_cache_key(self, context: PermissionContext, permission_id: str) -> str:
        """Generate cache key for evaluation"""
        roles_str = ':'.join(sorted(context.roles))
        return f"{context.user_id}:{permission_id}:{roles_str}:{context.tenant_id}:{context.resource_id}:{context.action}"
    
    async def _clear_role_cache(self, role_id: str) -> None:
        """Clear cache for specific role"""
        keys_to_remove = []
        for cache_key in self.evaluation_cache.keys():
            if f":{role_id}:" in cache_key or cache_key.endswith(f":{role_id}"):
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            if key in self.evaluation_cache:
                del self.evaluation_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
    
    async def _clear_resource_cache(self, resource_id: str) -> None:
        """Clear cache for specific resource"""
        keys_to_remove = []
        for cache_key in self.evaluation_cache.keys():
            if f":{resource_id}:" in cache_key:
                keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            if key in self.evaluation_cache:
                del self.evaluation_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]
    
    async def _cleanup_evaluation_cache(self) -> None:
        """Clean up expired cache entries"""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if now - timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.evaluation_cache:
                del self.evaluation_cache[key]
            del self.cache_timestamps[key]
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    async def _log_evaluation(self, context: PermissionContext, evaluation: PermissionEvaluation) -> None:
        """Log permission evaluation"""
        log_entry = {
            'timestamp': evaluation.evaluation_time.isoformat(),
            'user_id': context.user_id,
            'permission_id': evaluation.permission_id,
            'granted': evaluation.granted,
            'reason': evaluation.reason,
            'resource_type': context.resource_type.value if context.resource_type else None,
            'action': context.action,
            'tenant_id': context.tenant_id,
            'ip_address': context.ip_address
        }
        
        self.evaluation_log.append(log_entry)
        
        # Limit log size
        if len(self.evaluation_log) > 50000:
            self.evaluation_log = self.evaluation_log[-25000:]
    
    async def _analyze_access_patterns(self) -> None:
        """Analyze access patterns for security insights"""
        # Implement access pattern analysis
        # This could include detecting unusual access patterns, 
        # frequent denials, etc.
        pass
    
    async def cleanup(self) -> None:
        """Cleanup permission engine resources"""
        try:
            # Cancel background tasks
            for task in self.background_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.evaluation_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("PermissionEngine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during PermissionEngine cleanup: {str(e)}")