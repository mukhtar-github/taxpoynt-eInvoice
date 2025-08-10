"""
Tenant Configurator Service

This service manages multi-tenant configuration requirements, providing isolated
configuration management for different tenants across the TaxPoynt platform.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import (
    ConfigurationError,
    ValidationError,
    SecurityError
)


class TenantStatus(Enum):
    """Tenant status definitions"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    ARCHIVED = "archived"


class ConfigurationScope(Enum):
    """Configuration scope for tenant"""
    TENANT = "tenant"
    TENANT_USER = "tenant_user"
    TENANT_SERVICE = "tenant_service"
    TENANT_ENVIRONMENT = "tenant_environment"


class TenantTier(Enum):
    """Tenant tier levels"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class TenantProfile:
    """Tenant profile information"""
    tenant_id: str
    name: str
    display_name: str
    tier: TenantTier
    status: TenantStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    domain: Optional[str] = None
    contact_email: Optional[str] = None
    timezone: str = "UTC"
    locale: str = "en_US"
    currency: str = "NGN"
    features: Set[str] = field(default_factory=set)
    limits: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_tenant_id: Optional[str] = None
    child_tenants: Set[str] = field(default_factory=set)


@dataclass
class TenantConfiguration:
    """Tenant-specific configuration"""
    tenant_id: str
    key: str
    value: Any
    scope: ConfigurationScope
    encrypted: bool = False
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    version: int = 1
    environment: Optional[str] = None
    service: Optional[str] = None
    user_id: Optional[str] = None
    inheritable: bool = True
    override_allowed: bool = True


@dataclass
class TenantTemplate:
    """Template for tenant configuration"""
    template_id: str
    name: str
    description: str
    tier: TenantTier
    configurations: Dict[str, Any] = field(default_factory=dict)
    features: Set[str] = field(default_factory=set)
    limits: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class ConfigurationInheritance:
    """Configuration inheritance tracking"""
    child_tenant_id: str
    parent_tenant_id: str
    inherited_keys: Set[str] = field(default_factory=set)
    overridden_keys: Set[str] = field(default_factory=set)
    inheritance_enabled: bool = True
    last_sync: Optional[datetime] = None


class TenantConfigurator(BaseService):
    """
    Tenant Configurator Service
    
    Manages multi-tenant configuration requirements, providing isolated
    configuration management for different tenants.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Tenant management
        self.tenants: Dict[str, TenantProfile] = {}
        self.tenant_configs: Dict[str, Dict[str, TenantConfiguration]] = {}
        self.tenant_templates: Dict[str, TenantTemplate] = {}
        
        # Inheritance management
        self.inheritance_tree: Dict[str, ConfigurationInheritance] = {}
        
        # Configuration caching
        self.config_cache: Dict[str, Any] = {}
        self.cache_ttl: timedelta = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Validation and limits
        self.tenant_limits: Dict[str, Dict[str, Any]] = {}
        self.feature_registry: Dict[str, Dict[str, Any]] = {}
        
        # Change tracking
        self.change_listeners: Dict[str, List] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            'tenants_managed': 0,
            'configurations_managed': 0,
            'inheritance_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_checks': 0
        }
        
        # Synchronization
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.sync_tasks: Dict[str, asyncio.Task] = {}
    
    async def initialize(self) -> None:
        """Initialize tenant configurator"""
        try:
            self.logger.info("Initializing TenantConfigurator")
            
            # Load default tenant templates
            await self._load_default_templates()
            
            # Initialize feature registry
            await self._initialize_feature_registry()
            
            # Start synchronization worker
            await self._start_sync_worker()
            
            self.logger.info("TenantConfigurator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TenantConfigurator: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def create_tenant(
        self,
        tenant_id: str,
        name: str,
        display_name: str,
        tier: TenantTier,
        template_id: Optional[str] = None,
        parent_tenant_id: Optional[str] = None,
        domain: Optional[str] = None,
        contact_email: Optional[str] = None,
        created_by: str = "system"
    ) -> TenantProfile:
        """Create new tenant with configuration"""
        try:
            # Validate tenant doesn't exist
            if tenant_id in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} already exists")
            
            # Validate parent tenant if specified
            if parent_tenant_id and parent_tenant_id not in self.tenants:
                raise ValidationError(f"Parent tenant {parent_tenant_id} not found")
            
            # Create tenant profile
            tenant = TenantProfile(
                tenant_id=tenant_id,
                name=name,
                display_name=display_name,
                tier=tier,
                status=TenantStatus.ACTIVE,
                domain=domain,
                contact_email=contact_email,
                parent_tenant_id=parent_tenant_id
            )
            
            # Apply template if specified
            if template_id and template_id in self.tenant_templates:
                template = self.tenant_templates[template_id]
                tenant.features = template.features.copy()
                tenant.limits = template.limits.copy()
                
                # Apply template configurations
                await self._apply_template_configurations(tenant_id, template)
            
            # Set up inheritance if parent specified
            if parent_tenant_id:
                await self._setup_inheritance(tenant_id, parent_tenant_id)
                
                # Add to parent's children
                if parent_tenant_id in self.tenants:
                    self.tenants[parent_tenant_id].child_tenants.add(tenant_id)
            
            # Store tenant
            self.tenants[tenant_id] = tenant
            self.tenant_configs[tenant_id] = {}
            
            # Initialize default configurations
            await self._initialize_tenant_defaults(tenant_id)
            
            self.metrics['tenants_managed'] += 1
            self.logger.info(f"Tenant created: {tenant_id}")
            
            return tenant
            
        except Exception as e:
            self.logger.error(f"Failed to create tenant {tenant_id}: {str(e)}")
            raise ConfigurationError(f"Tenant creation failed: {str(e)}")
    
    async def update_tenant(
        self,
        tenant_id: str,
        name: Optional[str] = None,
        display_name: Optional[str] = None,
        tier: Optional[TenantTier] = None,
        status: Optional[TenantStatus] = None,
        domain: Optional[str] = None,
        contact_email: Optional[str] = None,
        timezone: Optional[str] = None,
        locale: Optional[str] = None,
        currency: Optional[str] = None,
        updated_by: str = "system"
    ) -> TenantProfile:
        """Update tenant profile"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            tenant = self.tenants[tenant_id]
            
            # Update fields
            if name is not None:
                tenant.name = name
            if display_name is not None:
                tenant.display_name = display_name
            if tier is not None:
                tenant.tier = tier
            if status is not None:
                tenant.status = status
            if domain is not None:
                tenant.domain = domain
            if contact_email is not None:
                tenant.contact_email = contact_email
            if timezone is not None:
                tenant.timezone = timezone
            if locale is not None:
                tenant.locale = locale
            if currency is not None:
                tenant.currency = currency
            
            tenant.updated_at = datetime.utcnow()
            
            # Log change
            await self._log_tenant_change(tenant_id, "updated", updated_by)
            
            self.logger.info(f"Tenant updated: {tenant_id}")
            return tenant
            
        except Exception as e:
            self.logger.error(f"Failed to update tenant {tenant_id}: {str(e)}")
            raise ConfigurationError(f"Tenant update failed: {str(e)}")
    
    async def set_tenant_configuration(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        scope: ConfigurationScope = ConfigurationScope.TENANT,
        encrypted: bool = False,
        description: Optional[str] = None,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        user_id: Optional[str] = None,
        inheritable: bool = True,
        override_allowed: bool = True,
        updated_by: str = "system"
    ) -> TenantConfiguration:
        """Set tenant-specific configuration"""
        try:
            # Validate tenant exists
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            # Validate configuration limits
            await self._validate_tenant_limits(tenant_id, key, value)
            
            # Create configuration
            config = TenantConfiguration(
                tenant_id=tenant_id,
                key=key,
                value=value,
                scope=scope,
                encrypted=encrypted,
                description=description,
                environment=environment,
                service=service,
                user_id=user_id,
                inheritable=inheritable,
                override_allowed=override_allowed,
                updated_by=updated_by
            )
            
            # Store configuration
            if tenant_id not in self.tenant_configs:
                self.tenant_configs[tenant_id] = {}
            
            self.tenant_configs[tenant_id][key] = config
            
            # Handle inheritance propagation
            if inheritable:
                await self._propagate_configuration_to_children(tenant_id, config)
            
            # Invalidate cache
            await self._invalidate_tenant_cache(tenant_id, key)
            
            # Log change
            await self._log_configuration_change(tenant_id, key, value, updated_by)
            
            self.metrics['configurations_managed'] += 1
            self.logger.info(f"Tenant configuration set: {tenant_id}.{key} = {value}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to set tenant configuration {tenant_id}.{key}: {str(e)}")
            raise ConfigurationError(f"Configuration set failed: {str(e)}")
    
    async def get_tenant_configuration(
        self,
        tenant_id: str,
        key: str,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        user_id: Optional[str] = None,
        use_inheritance: bool = True,
        use_cache: bool = True
    ) -> Optional[Any]:
        """Get tenant configuration with inheritance support"""
        try:
            # Check cache first
            if use_cache:
                cached_value = await self._get_from_tenant_cache(tenant_id, key)
                if cached_value is not None:
                    return cached_value
            
            # Look for direct configuration
            config = await self._find_tenant_configuration(
                tenant_id, key, environment, service, user_id
            )
            
            if config:
                await self._cache_tenant_configuration(tenant_id, key, config.value)
                return config.value
            
            # Check inheritance if enabled
            if use_inheritance and tenant_id in self.inheritance_tree:
                inheritance = self.inheritance_tree[tenant_id]
                if inheritance.inheritance_enabled and key in inheritance.inherited_keys:
                    parent_value = await self.get_tenant_configuration(
                        inheritance.parent_tenant_id, key, environment, service, user_id, True, use_cache
                    )
                    if parent_value is not None:
                        return parent_value
            
            self.metrics['cache_misses'] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get tenant configuration {tenant_id}.{key}: {str(e)}")
            return None
    
    async def get_all_tenant_configurations(
        self,
        tenant_id: str,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        include_inherited: bool = True
    ) -> Dict[str, Any]:
        """Get all configurations for a tenant"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            configurations = {}
            
            # Get direct configurations
            if tenant_id in self.tenant_configs:
                for key, config in self.tenant_configs[tenant_id].items():
                    # Apply environment/service filters
                    if environment and config.environment and config.environment != environment:
                        continue
                    if service and config.service and config.service != service:
                        continue
                    
                    configurations[key] = config.value
            
            # Get inherited configurations
            if include_inherited and tenant_id in self.inheritance_tree:
                inheritance = self.inheritance_tree[tenant_id]
                if inheritance.inheritance_enabled:
                    parent_configs = await self.get_all_tenant_configurations(
                        inheritance.parent_tenant_id, environment, service, True
                    )
                    
                    # Only include inherited keys not overridden
                    for key, value in parent_configs.items():
                        if (key in inheritance.inherited_keys and 
                            key not in inheritance.overridden_keys and 
                            key not in configurations):
                            configurations[key] = value
            
            return configurations
            
        except Exception as e:
            self.logger.error(f"Failed to get all tenant configurations for {tenant_id}: {str(e)}")
            return {}
    
    async def delete_tenant_configuration(
        self,
        tenant_id: str,
        key: str,
        updated_by: str = "system"
    ) -> bool:
        """Delete tenant configuration"""
        try:
            if tenant_id not in self.tenant_configs or key not in self.tenant_configs[tenant_id]:
                return False
            
            # Remove configuration
            del self.tenant_configs[tenant_id][key]
            
            # Update inheritance tracking
            if tenant_id in self.inheritance_tree:
                inheritance = self.inheritance_tree[tenant_id]
                inheritance.overridden_keys.discard(key)
            
            # Invalidate cache
            await self._invalidate_tenant_cache(tenant_id, key)
            
            # Log change
            await self._log_configuration_change(tenant_id, key, None, updated_by)
            
            self.logger.info(f"Tenant configuration deleted: {tenant_id}.{key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete tenant configuration {tenant_id}.{key}: {str(e)}")
            return False
    
    async def enable_feature(
        self,
        tenant_id: str,
        feature_name: str,
        updated_by: str = "system"
    ) -> bool:
        """Enable feature for tenant"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            # Validate feature exists
            if feature_name not in self.feature_registry:
                raise ValidationError(f"Feature {feature_name} not found")
            
            # Check tier limitations
            feature_info = self.feature_registry[feature_name]
            tenant = self.tenants[tenant_id]
            
            if 'allowed_tiers' in feature_info:
                if tenant.tier not in feature_info['allowed_tiers']:
                    raise ValidationError(f"Feature {feature_name} not available for tier {tenant.tier}")
            
            # Enable feature
            tenant.features.add(feature_name)
            tenant.updated_at = datetime.utcnow()
            
            # Apply feature configurations
            if 'default_configurations' in feature_info:
                for key, value in feature_info['default_configurations'].items():
                    await self.set_tenant_configuration(
                        tenant_id, key, value, updated_by=updated_by
                    )
            
            self.logger.info(f"Feature enabled for tenant {tenant_id}: {feature_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to enable feature {feature_name} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def disable_feature(
        self,
        tenant_id: str,
        feature_name: str,
        updated_by: str = "system"
    ) -> bool:
        """Disable feature for tenant"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            tenant = self.tenants[tenant_id]
            
            if feature_name in tenant.features:
                tenant.features.remove(feature_name)
                tenant.updated_at = datetime.utcnow()
                
                self.logger.info(f"Feature disabled for tenant {tenant_id}: {feature_name}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to disable feature {feature_name} for tenant {tenant_id}: {str(e)}")
            return False
    
    async def set_tenant_limit(
        self,
        tenant_id: str,
        limit_name: str,
        limit_value: Any,
        updated_by: str = "system"
    ) -> bool:
        """Set tenant limit"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            tenant = self.tenants[tenant_id]
            tenant.limits[limit_name] = limit_value
            tenant.updated_at = datetime.utcnow()
            
            self.logger.info(f"Tenant limit set: {tenant_id}.{limit_name} = {limit_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set tenant limit {tenant_id}.{limit_name}: {str(e)}")
            return False
    
    async def setup_inheritance(
        self,
        child_tenant_id: str,
        parent_tenant_id: str,
        inherited_keys: Optional[Set[str]] = None
    ) -> bool:
        """Setup configuration inheritance between tenants"""
        try:
            # Validate tenants exist
            if child_tenant_id not in self.tenants:
                raise ValidationError(f"Child tenant {child_tenant_id} not found")
            if parent_tenant_id not in self.tenants:
                raise ValidationError(f"Parent tenant {parent_tenant_id} not found")
            
            # Prevent circular inheritance
            if await self._would_create_inheritance_cycle(child_tenant_id, parent_tenant_id):
                raise ValidationError("Inheritance would create a cycle")
            
            # Create inheritance relationship
            inheritance = ConfigurationInheritance(
                child_tenant_id=child_tenant_id,
                parent_tenant_id=parent_tenant_id,
                inherited_keys=inherited_keys or set(),
                inheritance_enabled=True
            )
            
            self.inheritance_tree[child_tenant_id] = inheritance
            
            # Update tenant relationships
            self.tenants[child_tenant_id].parent_tenant_id = parent_tenant_id
            self.tenants[parent_tenant_id].child_tenants.add(child_tenant_id)
            
            # Sync inherited configurations
            await self._sync_inherited_configurations(child_tenant_id)
            
            self.metrics['inheritance_operations'] += 1
            self.logger.info(f"Inheritance setup: {child_tenant_id} inherits from {parent_tenant_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup inheritance {child_tenant_id} -> {parent_tenant_id}: {str(e)}")
            return False
    
    async def get_tenant_hierarchy(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant hierarchy information"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            tenant = self.tenants[tenant_id]
            
            hierarchy = {
                'tenant_id': tenant_id,
                'parent': None,
                'children': [],
                'inheritance_enabled': False,
                'inherited_keys': set(),
                'overridden_keys': set()
            }
            
            # Get parent information
            if tenant.parent_tenant_id:
                hierarchy['parent'] = tenant.parent_tenant_id
                
                if tenant_id in self.inheritance_tree:
                    inheritance = self.inheritance_tree[tenant_id]
                    hierarchy['inheritance_enabled'] = inheritance.inheritance_enabled
                    hierarchy['inherited_keys'] = inheritance.inherited_keys
                    hierarchy['overridden_keys'] = inheritance.overridden_keys
            
            # Get children information
            for child_id in tenant.child_tenants:
                child_info = await self.get_tenant_hierarchy(child_id)
                hierarchy['children'].append(child_info)
            
            return hierarchy
            
        except Exception as e:
            self.logger.error(f"Failed to get tenant hierarchy for {tenant_id}: {str(e)}")
            return {}
    
    async def export_tenant_configuration(
        self,
        tenant_id: str,
        include_inherited: bool = False,
        format: str = "json"
    ) -> str:
        """Export tenant configuration"""
        try:
            if tenant_id not in self.tenants:
                raise ValidationError(f"Tenant {tenant_id} not found")
            
            tenant = self.tenants[tenant_id]
            configurations = await self.get_all_tenant_configurations(
                tenant_id, include_inherited=include_inherited
            )
            
            export_data = {
                'tenant_profile': {
                    'tenant_id': tenant.tenant_id,
                    'name': tenant.name,
                    'display_name': tenant.display_name,
                    'tier': tenant.tier.value,
                    'status': tenant.status.value,
                    'features': list(tenant.features),
                    'limits': tenant.limits,
                    'metadata': tenant.metadata
                },
                'configurations': configurations,
                'exported_at': datetime.utcnow().isoformat(),
                'include_inherited': include_inherited
            }
            
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValidationError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export tenant configuration {tenant_id}: {str(e)}")
            raise ConfigurationError(f"Export failed: {str(e)}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get tenant configurator health status"""
        try:
            return {
                'service': 'TenantConfigurator',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'tenants': {
                    'total': len(self.tenants),
                    'by_status': {
                        status.value: len([t for t in self.tenants.values() if t.status == status])
                        for status in TenantStatus
                    },
                    'by_tier': {
                        tier.value: len([t for t in self.tenants.values() if t.tier == tier])
                        for tier in TenantTier
                    }
                },
                'configurations': {
                    'total': sum(len(configs) for configs in self.tenant_configs.values()),
                    'tenants_with_configs': len(self.tenant_configs)
                },
                'inheritance': {
                    'relationships': len(self.inheritance_tree),
                    'templates': len(self.tenant_templates)
                },
                'cache': {
                    'size': len(self.config_cache),
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
                'service': 'TenantConfigurator',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_templates(self) -> None:
        """Load default tenant templates"""
        templates = [
            TenantTemplate(
                template_id="basic_template",
                name="Basic Template",
                description="Basic tenant configuration template",
                tier=TenantTier.BASIC,
                configurations={
                    'max_users': 10,
                    'max_invoices_per_month': 100,
                    'storage_limit_mb': 1000,
                    'api_rate_limit': 100
                },
                features={'basic_invoicing', 'basic_reporting'},
                limits={
                    'max_users': 10,
                    'max_invoices_per_month': 100,
                    'storage_limit_mb': 1000
                }
            ),
            TenantTemplate(
                template_id="enterprise_template",
                name="Enterprise Template",
                description="Enterprise tenant configuration template",
                tier=TenantTier.ENTERPRISE,
                configurations={
                    'max_users': -1,  # Unlimited
                    'max_invoices_per_month': -1,
                    'storage_limit_mb': -1,
                    'api_rate_limit': 1000
                },
                features={
                    'advanced_invoicing', 'advanced_reporting', 
                    'bulk_operations', 'api_access', 'sso_integration'
                },
                limits={
                    'max_users': -1,
                    'max_invoices_per_month': -1,
                    'storage_limit_mb': -1
                }
            )
        ]
        
        for template in templates:
            self.tenant_templates[template.template_id] = template
    
    async def _initialize_feature_registry(self) -> None:
        """Initialize feature registry"""
        self.feature_registry = {
            'basic_invoicing': {
                'name': 'Basic Invoicing',
                'description': 'Basic invoice creation and management',
                'allowed_tiers': [TenantTier.BASIC, TenantTier.STANDARD, TenantTier.PREMIUM, TenantTier.ENTERPRISE],
                'default_configurations': {
                    'invoice_templates': ['basic_template'],
                    'auto_numbering': True
                }
            },
            'advanced_invoicing': {
                'name': 'Advanced Invoicing',
                'description': 'Advanced invoice features and automation',
                'allowed_tiers': [TenantTier.PREMIUM, TenantTier.ENTERPRISE],
                'default_configurations': {
                    'invoice_templates': ['basic_template', 'advanced_template'],
                    'auto_numbering': True,
                    'bulk_operations': True,
                    'custom_fields': True
                }
            },
            'api_access': {
                'name': 'API Access',
                'description': 'Access to REST API',
                'allowed_tiers': [TenantTier.STANDARD, TenantTier.PREMIUM, TenantTier.ENTERPRISE],
                'default_configurations': {
                    'api_enabled': True,
                    'rate_limit': 1000
                }
            },
            'sso_integration': {
                'name': 'SSO Integration',
                'description': 'Single Sign-On integration',
                'allowed_tiers': [TenantTier.ENTERPRISE],
                'default_configurations': {
                    'sso_enabled': True,
                    'saml_enabled': True
                }
            }
        }
    
    async def _start_sync_worker(self) -> None:
        """Start synchronization worker"""
        async def sync_worker():
            while True:
                try:
                    await asyncio.sleep(1)
                    # Process sync queue if needed
                except Exception as e:
                    self.logger.error(f"Sync worker error: {str(e)}")
                    await asyncio.sleep(5)
        
        self.sync_tasks['main'] = asyncio.create_task(sync_worker())
    
    async def _setup_inheritance(self, child_tenant_id: str, parent_tenant_id: str) -> None:
        """Setup inheritance relationship"""
        await self.setup_inheritance(child_tenant_id, parent_tenant_id)
    
    async def _apply_template_configurations(self, tenant_id: str, template: TenantTemplate) -> None:
        """Apply template configurations to tenant"""
        for key, value in template.configurations.items():
            await self.set_tenant_configuration(
                tenant_id=tenant_id,
                key=key,
                value=value,
                updated_by="template_application"
            )
    
    async def _initialize_tenant_defaults(self, tenant_id: str) -> None:
        """Initialize default configurations for tenant"""
        defaults = {
            'timezone': 'UTC',
            'locale': 'en_US',
            'currency': 'NGN',
            'date_format': 'YYYY-MM-DD',
            'time_format': '24h'
        }
        
        for key, value in defaults.items():
            await self.set_tenant_configuration(
                tenant_id=tenant_id,
                key=key,
                value=value,
                updated_by="system_defaults"
            )
    
    async def _validate_tenant_limits(self, tenant_id: str, key: str, value: Any) -> None:
        """Validate configuration against tenant limits"""
        if tenant_id not in self.tenants:
            return
        
        tenant = self.tenants[tenant_id]
        
        # Check configuration count limits
        if key == 'max_configurations':
            current_count = len(self.tenant_configs.get(tenant_id, {}))
            if isinstance(value, int) and current_count >= value:
                raise ValidationError(f"Configuration limit exceeded: {current_count}/{value}")
        
        # Check tier-specific limits
        tier_limits = {
            TenantTier.BASIC: {'max_custom_configs': 50},
            TenantTier.STANDARD: {'max_custom_configs': 200},
            TenantTier.PREMIUM: {'max_custom_configs': 500},
            TenantTier.ENTERPRISE: {'max_custom_configs': -1}  # Unlimited
        }
        
        if tenant.tier in tier_limits:
            limits = tier_limits[tenant.tier]
            for limit_key, limit_value in limits.items():
                if limit_value > 0:  # -1 means unlimited
                    # Apply specific limit checks based on limit_key
                    pass
        
        self.metrics['validation_checks'] += 1
    
    async def _find_tenant_configuration(
        self,
        tenant_id: str,
        key: str,
        environment: Optional[str] = None,
        service: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Optional[TenantConfiguration]:
        """Find best matching tenant configuration"""
        if tenant_id not in self.tenant_configs:
            return None
        
        configs = self.tenant_configs[tenant_id]
        
        # Look for exact match first
        if key in configs:
            config = configs[key]
            
            # Check context filters
            if environment and config.environment and config.environment != environment:
                return None
            if service and config.service and config.service != service:
                return None
            if user_id and config.user_id and config.user_id != user_id:
                return None
            
            return config
        
        return None
    
    async def _propagate_configuration_to_children(
        self,
        tenant_id: str,
        config: TenantConfiguration
    ) -> None:
        """Propagate inheritable configuration to child tenants"""
        if not config.inheritable:
            return
        
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return
        
        for child_id in tenant.child_tenants:
            if child_id in self.inheritance_tree:
                inheritance = self.inheritance_tree[child_id]
                if inheritance.inheritance_enabled:
                    # Add to inherited keys if not overridden
                    if config.key not in inheritance.overridden_keys:
                        inheritance.inherited_keys.add(config.key)
                        inheritance.last_sync = datetime.utcnow()
                        
                        # Recursively propagate to grandchildren
                        await self._propagate_configuration_to_children(child_id, config)
    
    async def _would_create_inheritance_cycle(
        self,
        child_tenant_id: str,
        parent_tenant_id: str
    ) -> bool:
        """Check if inheritance would create a cycle"""
        visited = set()
        current = parent_tenant_id
        
        while current and current not in visited:
            visited.add(current)
            
            if current == child_tenant_id:
                return True
            
            # Move to parent
            if current in self.tenants and self.tenants[current].parent_tenant_id:
                current = self.tenants[current].parent_tenant_id
            else:
                break
        
        return False
    
    async def _sync_inherited_configurations(self, tenant_id: str) -> None:
        """Sync inherited configurations for tenant"""
        if tenant_id not in self.inheritance_tree:
            return
        
        inheritance = self.inheritance_tree[tenant_id]
        parent_id = inheritance.parent_tenant_id
        
        if parent_id not in self.tenant_configs:
            return
        
        parent_configs = self.tenant_configs[parent_id]
        
        for key, config in parent_configs.items():
            if config.inheritable and key not in inheritance.overridden_keys:
                inheritance.inherited_keys.add(key)
        
        inheritance.last_sync = datetime.utcnow()
        self.metrics['inheritance_operations'] += 1
    
    async def _get_from_tenant_cache(self, tenant_id: str, key: str) -> Optional[Any]:
        """Get configuration from tenant cache"""
        cache_key = f"{tenant_id}:{key}"
        
        if cache_key in self.config_cache:
            timestamp = self.cache_timestamps.get(cache_key)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                return self.config_cache[cache_key]
            else:
                # Remove expired entry
                del self.config_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
        
        return None
    
    async def _cache_tenant_configuration(self, tenant_id: str, key: str, value: Any) -> None:
        """Cache tenant configuration"""
        cache_key = f"{tenant_id}:{key}"
        self.config_cache[cache_key] = value
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size
        if len(self.config_cache) > 5000:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            del self.config_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
    
    async def _invalidate_tenant_cache(self, tenant_id: str, key: Optional[str] = None) -> None:
        """Invalidate tenant cache"""
        if key:
            cache_key = f"{tenant_id}:{key}"
            if cache_key in self.config_cache:
                del self.config_cache[cache_key]
            if cache_key in self.cache_timestamps:
                del self.cache_timestamps[cache_key]
        else:
            # Invalidate all configurations for tenant
            keys_to_remove = [
                cache_key for cache_key in self.config_cache.keys()
                if cache_key.startswith(f"{tenant_id}:")
            ]
            for cache_key in keys_to_remove:
                del self.config_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
    
    async def _log_tenant_change(self, tenant_id: str, action: str, changed_by: str) -> None:
        """Log tenant change"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': tenant_id,
            'action': action,
            'changed_by': changed_by,
            'type': 'tenant_change'
        }
        
        self.audit_log.append(log_entry)
        
        # Limit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
    
    async def _log_configuration_change(
        self,
        tenant_id: str,
        key: str,
        value: Any,
        changed_by: str
    ) -> None:
        """Log configuration change"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'tenant_id': tenant_id,
            'configuration_key': key,
            'new_value': value,
            'changed_by': changed_by,
            'type': 'configuration_change'
        }
        
        self.audit_log.append(log_entry)
        
        # Limit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
    
    async def cleanup(self) -> None:
        """Cleanup tenant configurator resources"""
        try:
            # Cancel sync tasks
            for task in self.sync_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.config_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("TenantConfigurator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during TenantConfigurator cleanup: {str(e)}")