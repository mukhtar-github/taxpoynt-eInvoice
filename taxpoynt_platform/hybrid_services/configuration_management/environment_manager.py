"""
Environment Manager Service

This service manages environment-specific configurations across the TaxPoynt platform,
providing isolated configuration management for different deployment environments.
"""

import asyncio
import json
import hashlib
import os
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


class Environment(Enum):
    """Environment types"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"
    SANDBOX = "sandbox"


class ConfigurationLevel(Enum):
    """Configuration hierarchy levels"""
    GLOBAL = "global"
    ENVIRONMENT = "environment"
    SERVICE = "service"
    INSTANCE = "instance"


class DeploymentMode(Enum):
    """Deployment modes"""
    SINGLE_TENANT = "single_tenant"
    MULTI_TENANT = "multi_tenant"
    HYBRID = "hybrid"


@dataclass
class EnvironmentProfile:
    """Environment profile definition"""
    environment: Environment
    name: str
    description: str
    deployment_mode: DeploymentMode
    is_production: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    region: Optional[str] = None
    cluster: Optional[str] = None
    namespace: Optional[str] = None
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    maintenance_window: Optional[Dict[str, str]] = None
    auto_scaling: bool = False
    monitoring_enabled: bool = True
    logging_level: str = "INFO"


@dataclass
class EnvironmentConfiguration:
    """Environment-specific configuration"""
    environment: Environment
    key: str
    value: Any
    level: ConfigurationLevel
    encrypted: bool = False
    description: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"
    updated_by: str = "system"
    version: int = 1
    service: Optional[str] = None
    instance: Optional[str] = None
    sensitive: bool = False
    override_allowed: bool = True
    validation_rules: Optional[Dict[str, Any]] = None


@dataclass
class EnvironmentVariable:
    """Environment variable definition"""
    name: str
    value: str
    environment: Environment
    encrypted: bool = False
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[str] = None
    pattern: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConfigurationTemplate:
    """Configuration template for environments"""
    template_id: str
    name: str
    description: str
    target_environments: Set[Environment] = field(default_factory=set)
    configurations: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: str = "system"


@dataclass
class EnvironmentSync:
    """Environment synchronization tracking"""
    source_environment: Environment
    target_environment: Environment
    sync_rules: Dict[str, Any] = field(default_factory=dict)
    last_sync: Optional[datetime] = None
    sync_enabled: bool = True
    sync_conflicts: List[str] = field(default_factory=list)


class EnvironmentManager(BaseService):
    """
    Environment Manager Service
    
    Manages environment-specific configurations across the TaxPoynt platform,
    providing isolated configuration management for different deployment environments.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Environment management
        self.environments: Dict[Environment, EnvironmentProfile] = {}
        self.env_configs: Dict[Environment, Dict[str, EnvironmentConfiguration]] = {}
        self.env_variables: Dict[Environment, Dict[str, EnvironmentVariable]] = {}
        
        # Template management
        self.templates: Dict[str, ConfigurationTemplate] = {}
        
        # Synchronization
        self.sync_relationships: Dict[str, EnvironmentSync] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        
        # Configuration hierarchy
        self.hierarchy_cache: Dict[str, Any] = {}
        self.cache_ttl: timedelta = timedelta(minutes=10)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Current environment detection
        self.current_environment: Optional[Environment] = None
        
        # Validation and security
        self.validators: Dict[str, Any] = {}
        self.encryption_key: Optional[str] = None
        
        # Change tracking
        self.change_listeners: Dict[str, List] = {}
        self.audit_log: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.metrics = {
            'environments_managed': 0,
            'configurations_managed': 0,
            'variables_managed': 0,
            'sync_operations': 0,
            'template_applications': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validations_performed': 0
        }
    
    async def initialize(self) -> None:
        """Initialize environment manager"""
        try:
            self.logger.info("Initializing EnvironmentManager")
            
            # Detect current environment
            await self._detect_current_environment()
            
            # Load default environments
            await self._load_default_environments()
            
            # Load configuration templates
            await self._load_default_templates()
            
            # Initialize validation rules
            await self._initialize_validation_rules()
            
            # Start synchronization worker
            await self._start_sync_worker()
            
            self.logger.info("EnvironmentManager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize EnvironmentManager: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def create_environment(
        self,
        environment: Environment,
        name: str,
        description: str,
        deployment_mode: DeploymentMode,
        is_production: bool = False,
        region: Optional[str] = None,
        cluster: Optional[str] = None,
        namespace: Optional[str] = None,
        created_by: str = "system"
    ) -> EnvironmentProfile:
        """Create new environment profile"""
        try:
            # Validate environment doesn't exist
            if environment in self.environments:
                raise ValidationError(f"Environment {environment.value} already exists")
            
            # Create environment profile
            profile = EnvironmentProfile(
                environment=environment,
                name=name,
                description=description,
                deployment_mode=deployment_mode,
                is_production=is_production,
                region=region,
                cluster=cluster,
                namespace=namespace
            )
            
            # Store environment
            self.environments[environment] = profile
            self.env_configs[environment] = {}
            self.env_variables[environment] = {}
            
            # Initialize default configurations
            await self._initialize_environment_defaults(environment)
            
            self.metrics['environments_managed'] += 1
            self.logger.info(f"Environment created: {environment.value}")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to create environment {environment.value}: {str(e)}")
            raise ConfigurationError(f"Environment creation failed: {str(e)}")
    
    async def set_environment_configuration(
        self,
        environment: Environment,
        key: str,
        value: Any,
        level: ConfigurationLevel = ConfigurationLevel.ENVIRONMENT,
        encrypted: bool = False,
        description: Optional[str] = None,
        service: Optional[str] = None,
        instance: Optional[str] = None,
        sensitive: bool = False,
        override_allowed: bool = True,
        updated_by: str = "system"
    ) -> EnvironmentConfiguration:
        """Set environment-specific configuration"""
        try:
            # Validate environment exists
            if environment not in self.environments:
                raise ValidationError(f"Environment {environment.value} not found")
            
            # Validate configuration
            await self._validate_environment_configuration(environment, key, value)
            
            # Encrypt value if needed
            if encrypted and self.encryption_key:
                value = await self._encrypt_value(str(value))
            
            # Create configuration
            config = EnvironmentConfiguration(
                environment=environment,
                key=key,
                value=value,
                level=level,
                encrypted=encrypted,
                description=description,
                service=service,
                instance=instance,
                sensitive=sensitive,
                override_allowed=override_allowed,
                updated_by=updated_by
            )
            
            # Store configuration
            self.env_configs[environment][key] = config
            
            # Invalidate cache
            await self._invalidate_hierarchy_cache(environment, key)
            
            # Trigger synchronization if needed
            await self._trigger_environment_sync(environment, key, value)
            
            # Log change
            await self._log_configuration_change(environment, key, value, updated_by)
            
            self.metrics['configurations_managed'] += 1
            self.logger.info(f"Environment configuration set: {environment.value}.{key}")
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to set environment configuration {environment.value}.{key}: {str(e)}")
            raise ConfigurationError(f"Configuration set failed: {str(e)}")
    
    async def get_environment_configuration(
        self,
        environment: Environment,
        key: str,
        service: Optional[str] = None,
        instance: Optional[str] = None,
        use_hierarchy: bool = True,
        use_cache: bool = True,
        decrypt: bool = True
    ) -> Optional[Any]:
        """Get environment configuration with hierarchy resolution"""
        try:
            # Check cache first
            if use_cache:
                cached_value = await self._get_from_hierarchy_cache(environment, key, service, instance)
                if cached_value is not None:
                    return cached_value
            
            # Use hierarchy resolution
            if use_hierarchy:
                value = await self._resolve_configuration_hierarchy(
                    environment, key, service, instance
                )
            else:
                # Direct lookup
                if environment in self.env_configs and key in self.env_configs[environment]:
                    config = self.env_configs[environment][key]
                    value = config.value
                else:
                    value = None
            
            # Decrypt if needed
            if value is not None and decrypt:
                value = await self._decrypt_if_encrypted(environment, key, value)
            
            # Cache result
            if use_cache and value is not None:
                await self._cache_hierarchy_result(environment, key, service, instance, value)
            
            return value
            
        except Exception as e:
            self.logger.error(f"Failed to get environment configuration {environment.value}.{key}: {str(e)}")
            return None
    
    async def set_environment_variable(
        self,
        environment: Environment,
        name: str,
        value: str,
        encrypted: bool = False,
        description: Optional[str] = None,
        required: bool = True,
        pattern: Optional[str] = None,
        updated_by: str = "system"
    ) -> EnvironmentVariable:
        """Set environment variable"""
        try:
            # Validate environment exists
            if environment not in self.environments:
                raise ValidationError(f"Environment {environment.value} not found")
            
            # Validate variable
            await self._validate_environment_variable(name, value, pattern)
            
            # Encrypt value if needed
            if encrypted and self.encryption_key:
                value = await self._encrypt_value(value)
            
            # Create environment variable
            env_var = EnvironmentVariable(
                name=name,
                value=value,
                environment=environment,
                encrypted=encrypted,
                description=description,
                required=required,
                pattern=pattern
            )
            
            # Store variable
            self.env_variables[environment][name] = env_var
            
            # Apply to system environment if current environment
            if environment == self.current_environment:
                os.environ[name] = value
            
            self.metrics['variables_managed'] += 1
            self.logger.info(f"Environment variable set: {environment.value}.{name}")
            
            return env_var
            
        except Exception as e:
            self.logger.error(f"Failed to set environment variable {environment.value}.{name}: {str(e)}")
            raise ConfigurationError(f"Environment variable set failed: {str(e)}")
    
    async def get_environment_variable(
        self,
        environment: Environment,
        name: str,
        decrypt: bool = True,
        fallback_to_system: bool = True
    ) -> Optional[str]:
        """Get environment variable"""
        try:
            # Check environment-specific variables first
            if environment in self.env_variables and name in self.env_variables[environment]:
                env_var = self.env_variables[environment][name]
                value = env_var.value
                
                # Decrypt if needed
                if decrypt and env_var.encrypted and self.encryption_key:
                    value = await self._decrypt_value(value)
                
                return value
            
            # Fallback to system environment if allowed
            if fallback_to_system:
                return os.environ.get(name)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get environment variable {environment.value}.{name}: {str(e)}")
            return None
    
    async def apply_template(
        self,
        template_id: str,
        environment: Environment,
        variable_overrides: Optional[Dict[str, str]] = None,
        applied_by: str = "system"
    ) -> bool:
        """Apply configuration template to environment"""
        try:
            # Validate template exists
            if template_id not in self.templates:
                raise ValidationError(f"Template {template_id} not found")
            
            # Validate environment exists
            if environment not in self.environments:
                raise ValidationError(f"Environment {environment.value} not found")
            
            template = self.templates[template_id]
            
            # Check if template targets this environment
            if template.target_environments and environment not in template.target_environments:
                raise ValidationError(f"Template {template_id} not applicable to {environment.value}")
            
            # Prepare variables
            variables = template.variables.copy()
            if variable_overrides:
                variables.update(variable_overrides)
            
            # Apply configurations
            applied_count = 0
            for key, value in template.configurations.items():
                # Substitute variables
                if isinstance(value, str):
                    for var_name, var_value in variables.items():
                        value = value.replace(f"${{{var_name}}}", var_value)
                
                # Apply configuration
                await self.set_environment_configuration(
                    environment=environment,
                    key=key,
                    value=value,
                    updated_by=applied_by
                )
                applied_count += 1
            
            self.metrics['template_applications'] += 1
            self.logger.info(f"Template applied: {template_id} to {environment.value} ({applied_count} configs)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to apply template {template_id} to {environment.value}: {str(e)}")
            return False
    
    async def sync_environments(
        self,
        source_environment: Environment,
        target_environment: Environment,
        keys: Optional[List[str]] = None,
        sync_rules: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Synchronize configurations between environments"""
        try:
            # Validate environments exist
            if source_environment not in self.environments:
                raise ValidationError(f"Source environment {source_environment.value} not found")
            if target_environment not in self.environments:
                raise ValidationError(f"Target environment {target_environment.value} not found")
            
            # Get configurations to sync
            source_configs = self.env_configs.get(source_environment, {})
            
            if keys:
                configs_to_sync = {k: v for k, v in source_configs.items() if k in keys}
            else:
                configs_to_sync = source_configs
            
            # Apply sync rules
            if sync_rules:
                configs_to_sync = await self._apply_sync_rules(configs_to_sync, sync_rules)
            
            # Sync configurations
            synced_count = 0
            conflicts = []
            
            for key, config in configs_to_sync.items():
                try:
                    # Check if override is allowed
                    if (target_environment in self.env_configs and 
                        key in self.env_configs[target_environment]):
                        target_config = self.env_configs[target_environment][key]
                        if not target_config.override_allowed:
                            conflicts.append(f"Override not allowed for {key}")
                            continue
                    
                    # Sync configuration
                    await self.set_environment_configuration(
                        environment=target_environment,
                        key=key,
                        value=config.value,
                        level=config.level,
                        encrypted=config.encrypted,
                        description=f"Synced from {source_environment.value}",
                        service=config.service,
                        instance=config.instance,
                        updated_by=f"sync_from_{source_environment.value}"
                    )
                    synced_count += 1
                    
                except Exception as e:
                    conflicts.append(f"Failed to sync {key}: {str(e)}")
            
            # Update sync tracking
            sync_key = f"{source_environment.value}->{target_environment.value}"
            if sync_key not in self.sync_relationships:
                self.sync_relationships[sync_key] = EnvironmentSync(
                    source_environment=source_environment,
                    target_environment=target_environment
                )
            
            sync_rel = self.sync_relationships[sync_key]
            sync_rel.last_sync = datetime.utcnow()
            sync_rel.sync_conflicts = conflicts
            
            self.metrics['sync_operations'] += 1
            self.logger.info(f"Environment sync completed: {source_environment.value} -> {target_environment.value} ({synced_count} configs)")
            
            return len(conflicts) == 0
            
        except Exception as e:
            self.logger.error(f"Failed to sync environments {source_environment.value} -> {target_environment.value}: {str(e)}")
            return False
    
    async def promote_configuration(
        self,
        key: str,
        from_environment: Environment,
        to_environment: Environment,
        promoted_by: str = "system"
    ) -> bool:
        """Promote configuration from one environment to another"""
        try:
            # Get source configuration
            source_value = await self.get_environment_configuration(
                from_environment, key, decrypt=False
            )
            
            if source_value is None:
                raise ValidationError(f"Configuration {key} not found in {from_environment.value}")
            
            # Get source configuration object for metadata
            source_config = self.env_configs[from_environment].get(key)
            if not source_config:
                raise ValidationError(f"Configuration object {key} not found in {from_environment.value}")
            
            # Promote configuration
            await self.set_environment_configuration(
                environment=to_environment,
                key=key,
                value=source_value,
                level=source_config.level,
                encrypted=source_config.encrypted,
                description=f"Promoted from {from_environment.value}",
                service=source_config.service,
                instance=source_config.instance,
                sensitive=source_config.sensitive,
                updated_by=promoted_by
            )
            
            self.logger.info(f"Configuration promoted: {key} from {from_environment.value} to {to_environment.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to promote configuration {key}: {str(e)}")
            return False
    
    async def get_all_environment_configurations(
        self,
        environment: Environment,
        level: Optional[ConfigurationLevel] = None,
        service: Optional[str] = None,
        decrypt_sensitive: bool = False
    ) -> Dict[str, Any]:
        """Get all configurations for an environment"""
        try:
            if environment not in self.env_configs:
                return {}
            
            configurations = {}
            
            for key, config in self.env_configs[environment].items():
                # Apply filters
                if level and config.level != level:
                    continue
                if service and config.service != service:
                    continue
                
                # Get value
                value = config.value
                
                # Decrypt if needed and allowed
                if decrypt_sensitive and config.encrypted and self.encryption_key:
                    try:
                        value = await self._decrypt_value(value)
                    except Exception:
                        value = "[ENCRYPTED]"
                elif config.sensitive and not decrypt_sensitive:
                    value = "[SENSITIVE]"
                
                configurations[key] = value
            
            return configurations
            
        except Exception as e:
            self.logger.error(f"Failed to get all configurations for {environment.value}: {str(e)}")
            return {}
    
    async def export_environment_configuration(
        self,
        environment: Environment,
        include_sensitive: bool = False,
        format: str = "json"
    ) -> str:
        """Export environment configuration"""
        try:
            if environment not in self.environments:
                raise ValidationError(f"Environment {environment.value} not found")
            
            profile = self.environments[environment]
            configurations = await self.get_all_environment_configurations(
                environment, decrypt_sensitive=include_sensitive
            )
            
            variables = {}
            if environment in self.env_variables:
                for name, env_var in self.env_variables[environment].items():
                    if include_sensitive or not env_var.encrypted:
                        variables[name] = env_var.value
                    else:
                        variables[name] = "[ENCRYPTED]"
            
            export_data = {
                'environment_profile': {
                    'environment': environment.value,
                    'name': profile.name,
                    'description': profile.description,
                    'deployment_mode': profile.deployment_mode.value,
                    'is_production': profile.is_production,
                    'region': profile.region,
                    'cluster': profile.cluster,
                    'namespace': profile.namespace,
                    'tags': list(profile.tags),
                    'metadata': profile.metadata
                },
                'configurations': configurations,
                'environment_variables': variables,
                'exported_at': datetime.utcnow().isoformat(),
                'include_sensitive': include_sensitive
            }
            
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            else:
                raise ValidationError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export environment configuration {environment.value}: {str(e)}")
            raise ConfigurationError(f"Export failed: {str(e)}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get environment manager health status"""
        try:
            return {
                'service': 'EnvironmentManager',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'current_environment': self.current_environment.value if self.current_environment else None,
                'metrics': self.metrics,
                'environments': {
                    'total': len(self.environments),
                    'by_type': {
                        env.value: len([e for e in self.environments.keys() if e == env])
                        for env in Environment
                    },
                    'production_count': len([e for e in self.environments.values() if e.is_production])
                },
                'configurations': {
                    'total': sum(len(configs) for configs in self.env_configs.values()),
                    'environments_with_configs': len(self.env_configs)
                },
                'variables': {
                    'total': sum(len(vars) for vars in self.env_variables.values()),
                    'environments_with_vars': len(self.env_variables)
                },
                'templates': {
                    'total': len(self.templates)
                },
                'sync_relationships': {
                    'total': len(self.sync_relationships)
                },
                'cache': {
                    'size': len(self.hierarchy_cache),
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
                'service': 'EnvironmentManager',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _detect_current_environment(self) -> None:
        """Detect current environment from system"""
        env_indicators = {
            'NODE_ENV': {
                'development': Environment.DEVELOPMENT,
                'dev': Environment.DEVELOPMENT,
                'test': Environment.TESTING,
                'testing': Environment.TESTING,
                'staging': Environment.STAGING,
                'stage': Environment.STAGING,
                'production': Environment.PRODUCTION,
                'prod': Environment.PRODUCTION
            },
            'ENVIRONMENT': {
                'development': Environment.DEVELOPMENT,
                'testing': Environment.TESTING,
                'staging': Environment.STAGING,
                'production': Environment.PRODUCTION,
                'local': Environment.LOCAL,
                'sandbox': Environment.SANDBOX
            },
            'TAXPOYNT_ENV': {
                'development': Environment.DEVELOPMENT,
                'testing': Environment.TESTING,
                'staging': Environment.STAGING,
                'production': Environment.PRODUCTION,
                'local': Environment.LOCAL,
                'sandbox': Environment.SANDBOX
            }
        }
        
        for env_var, mappings in env_indicators.items():
            value = os.environ.get(env_var, '').lower()
            if value in mappings:
                self.current_environment = mappings[value]
                self.logger.info(f"Current environment detected: {self.current_environment.value} (from {env_var})")
                return
        
        # Default to development if not detected
        self.current_environment = Environment.DEVELOPMENT
        self.logger.info("Current environment defaulted to: development")
    
    async def _load_default_environments(self) -> None:
        """Load default environment profiles"""
        default_environments = [
            (Environment.DEVELOPMENT, "Development", "Development environment", DeploymentMode.SINGLE_TENANT, False),
            (Environment.TESTING, "Testing", "Testing environment", DeploymentMode.SINGLE_TENANT, False),
            (Environment.STAGING, "Staging", "Staging environment", DeploymentMode.MULTI_TENANT, False),
            (Environment.PRODUCTION, "Production", "Production environment", DeploymentMode.MULTI_TENANT, True),
            (Environment.LOCAL, "Local", "Local development environment", DeploymentMode.SINGLE_TENANT, False),
            (Environment.SANDBOX, "Sandbox", "Sandbox environment", DeploymentMode.SINGLE_TENANT, False)
        ]
        
        for env, name, desc, mode, is_prod in default_environments:
            if env not in self.environments:
                await self.create_environment(env, name, desc, mode, is_prod)
    
    async def _load_default_templates(self) -> None:
        """Load default configuration templates"""
        templates = [
            ConfigurationTemplate(
                template_id="basic_config",
                name="Basic Configuration",
                description="Basic configuration template for all environments",
                target_environments={Environment.DEVELOPMENT, Environment.TESTING},
                configurations={
                    'log_level': 'DEBUG',
                    'database_pool_size': 5,
                    'cache_ttl': 300,
                    'api_timeout': 30
                },
                variables={
                    'app_name': 'taxpoynt',
                    'version': '1.0.0'
                }
            ),
            ConfigurationTemplate(
                template_id="production_config",
                name="Production Configuration",
                description="Production-ready configuration template",
                target_environments={Environment.STAGING, Environment.PRODUCTION},
                configurations={
                    'log_level': 'INFO',
                    'database_pool_size': 20,
                    'cache_ttl': 3600,
                    'api_timeout': 60,
                    'monitoring_enabled': True,
                    'ssl_enabled': True
                },
                variables={
                    'app_name': 'taxpoynt',
                    'version': '1.0.0'
                }
            )
        ]
        
        for template in templates:
            self.templates[template.template_id] = template
    
    async def _initialize_validation_rules(self) -> None:
        """Initialize configuration validation rules"""
        self.validators = {
            'log_level': lambda v: v in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'database_pool_size': lambda v: isinstance(v, int) and v > 0,
            'cache_ttl': lambda v: isinstance(v, int) and v >= 0,
            'api_timeout': lambda v: isinstance(v, (int, float)) and v > 0,
            'ssl_enabled': lambda v: isinstance(v, bool),
            'monitoring_enabled': lambda v: isinstance(v, bool)
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
    
    async def _initialize_environment_defaults(self, environment: Environment) -> None:
        """Initialize default configurations for environment"""
        defaults = {
            'environment_name': environment.value,
            'created_at': datetime.utcnow().isoformat(),
            'timezone': 'UTC',
            'log_format': 'json'
        }
        
        # Environment-specific defaults
        if environment == Environment.PRODUCTION:
            defaults.update({
                'log_level': 'INFO',
                'debug_mode': False,
                'monitoring_enabled': True
            })
        elif environment in [Environment.DEVELOPMENT, Environment.LOCAL]:
            defaults.update({
                'log_level': 'DEBUG',
                'debug_mode': True,
                'monitoring_enabled': False
            })
        else:
            defaults.update({
                'log_level': 'INFO',
                'debug_mode': False,
                'monitoring_enabled': True
            })
        
        for key, value in defaults.items():
            await self.set_environment_configuration(
                environment=environment,
                key=key,
                value=value,
                level=ConfigurationLevel.ENVIRONMENT,
                updated_by="system_defaults"
            )
    
    async def _validate_environment_configuration(
        self,
        environment: Environment,
        key: str,
        value: Any
    ) -> None:
        """Validate environment configuration"""
        # Check validator
        if key in self.validators:
            validator = self.validators[key]
            if not validator(value):
                raise ValidationError(f"Value {value} failed validation for {key}")
        
        # Production-specific validations
        if environment == Environment.PRODUCTION:
            if key == 'debug_mode' and value is True:
                raise ValidationError("Debug mode should not be enabled in production")
            if key == 'log_level' and value == 'DEBUG':
                raise ValidationError("Debug log level should not be used in production")
        
        self.metrics['validations_performed'] += 1
    
    async def _validate_environment_variable(
        self,
        name: str,
        value: str,
        pattern: Optional[str] = None
    ) -> None:
        """Validate environment variable"""
        import re
        
        # Check pattern if provided
        if pattern:
            if not re.match(pattern, value):
                raise ValidationError(f"Value {value} does not match pattern {pattern}")
        
        # Common validations
        if name.endswith('_URL') and not value.startswith(('http://', 'https://')):
            raise ValidationError(f"URL variable {name} must start with http:// or https://")
        
        if name.endswith('_PORT'):
            try:
                port = int(value)
                if not 1 <= port <= 65535:
                    raise ValidationError(f"Port {name} must be between 1 and 65535")
            except ValueError:
                raise ValidationError(f"Port variable {name} must be a valid integer")
    
    async def _resolve_configuration_hierarchy(
        self,
        environment: Environment,
        key: str,
        service: Optional[str] = None,
        instance: Optional[str] = None
    ) -> Optional[Any]:
        """Resolve configuration using hierarchy"""
        # Check instance level first (most specific)
        if instance and service:
            config = await self._find_config_by_level(
                environment, key, ConfigurationLevel.INSTANCE, service, instance
            )
            if config:
                return config.value
        
        # Check service level
        if service:
            config = await self._find_config_by_level(
                environment, key, ConfigurationLevel.SERVICE, service
            )
            if config:
                return config.value
        
        # Check environment level
        config = await self._find_config_by_level(
            environment, key, ConfigurationLevel.ENVIRONMENT
        )
        if config:
            return config.value
        
        # Check global level
        config = await self._find_config_by_level(
            environment, key, ConfigurationLevel.GLOBAL
        )
        if config:
            return config.value
        
        return None
    
    async def _find_config_by_level(
        self,
        environment: Environment,
        key: str,
        level: ConfigurationLevel,
        service: Optional[str] = None,
        instance: Optional[str] = None
    ) -> Optional[EnvironmentConfiguration]:
        """Find configuration by specific level"""
        if environment not in self.env_configs:
            return None
        
        for config_key, config in self.env_configs[environment].items():
            if (config_key == key and 
                config.level == level and
                (service is None or config.service == service) and
                (instance is None or config.instance == instance)):
                return config
        
        return None
    
    async def _encrypt_value(self, value: str) -> str:
        """Encrypt sensitive value"""
        # Implementation would use actual encryption
        # For demo purposes, return base64 encoded
        import base64
        return base64.b64encode(value.encode()).decode()
    
    async def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt encrypted value"""
        # Implementation would use actual decryption
        # For demo purposes, return base64 decoded
        import base64
        return base64.b64decode(encrypted_value.encode()).decode()
    
    async def _decrypt_if_encrypted(
        self,
        environment: Environment,
        key: str,
        value: Any
    ) -> Any:
        """Decrypt value if it's encrypted"""
        if environment in self.env_configs and key in self.env_configs[environment]:
            config = self.env_configs[environment][key]
            if config.encrypted and self.encryption_key:
                try:
                    return await self._decrypt_value(str(value))
                except Exception:
                    self.logger.warning(f"Failed to decrypt value for {key}")
                    return value
        
        return value
    
    async def _trigger_environment_sync(
        self,
        environment: Environment,
        key: str,
        value: Any
    ) -> None:
        """Trigger synchronization after configuration change"""
        # Check if there are sync relationships for this environment
        for sync_key, sync_rel in self.sync_relationships.items():
            if (sync_rel.source_environment == environment and 
                sync_rel.sync_enabled):
                # Queue for synchronization
                await self.sync_queue.put({
                    'source': environment,
                    'target': sync_rel.target_environment,
                    'key': key,
                    'value': value
                })
    
    async def _apply_sync_rules(
        self,
        configs: Dict[str, EnvironmentConfiguration],
        sync_rules: Dict[str, Any]
    ) -> Dict[str, EnvironmentConfiguration]:
        """Apply synchronization rules to configurations"""
        filtered_configs = {}
        
        # Include rules
        if 'include' in sync_rules:
            include_patterns = sync_rules['include']
            for key, config in configs.items():
                for pattern in include_patterns:
                    if key.startswith(pattern) or key == pattern:
                        filtered_configs[key] = config
                        break
        else:
            filtered_configs = configs.copy()
        
        # Exclude rules
        if 'exclude' in sync_rules:
            exclude_patterns = sync_rules['exclude']
            for pattern in exclude_patterns:
                keys_to_remove = [
                    key for key in filtered_configs.keys()
                    if key.startswith(pattern) or key == pattern
                ]
                for key in keys_to_remove:
                    del filtered_configs[key]
        
        # Transform rules
        if 'transforms' in sync_rules:
            transforms = sync_rules['transforms']
            for key, config in list(filtered_configs.items()):
                for transform in transforms:
                    if transform.get('key_pattern') in key:
                        # Apply transformation
                        if 'value_transform' in transform:
                            # Apply value transformation logic
                            pass
        
        return filtered_configs
    
    async def _get_from_hierarchy_cache(
        self,
        environment: Environment,
        key: str,
        service: Optional[str] = None,
        instance: Optional[str] = None
    ) -> Optional[Any]:
        """Get configuration from hierarchy cache"""
        cache_key = f"{environment.value}:{key}:{service or 'none'}:{instance or 'none'}"
        
        if cache_key in self.hierarchy_cache:
            timestamp = self.cache_timestamps.get(cache_key)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                return self.hierarchy_cache[cache_key]
            else:
                # Remove expired entry
                del self.hierarchy_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
        
        self.metrics['cache_misses'] += 1
        return None
    
    async def _cache_hierarchy_result(
        self,
        environment: Environment,
        key: str,
        service: Optional[str],
        instance: Optional[str],
        value: Any
    ) -> None:
        """Cache hierarchy resolution result"""
        cache_key = f"{environment.value}:{key}:{service or 'none'}:{instance or 'none'}"
        self.hierarchy_cache[cache_key] = value
        self.cache_timestamps[cache_key] = datetime.utcnow()
        
        # Limit cache size
        if len(self.hierarchy_cache) > 5000:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            del self.hierarchy_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
    
    async def _invalidate_hierarchy_cache(
        self,
        environment: Environment,
        key: Optional[str] = None
    ) -> None:
        """Invalidate hierarchy cache"""
        if key:
            # Invalidate specific key patterns
            prefix = f"{environment.value}:{key}:"
            keys_to_remove = [
                cache_key for cache_key in self.hierarchy_cache.keys()
                if cache_key.startswith(prefix)
            ]
        else:
            # Invalidate all for environment
            prefix = f"{environment.value}:"
            keys_to_remove = [
                cache_key for cache_key in self.hierarchy_cache.keys()
                if cache_key.startswith(prefix)
            ]
        
        for cache_key in keys_to_remove:
            del self.hierarchy_cache[cache_key]
            if cache_key in self.cache_timestamps:
                del self.cache_timestamps[cache_key]
    
    async def _log_configuration_change(
        self,
        environment: Environment,
        key: str,
        value: Any,
        changed_by: str
    ) -> None:
        """Log configuration change"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': environment.value,
            'configuration_key': key,
            'new_value': value if not isinstance(value, str) or len(str(value)) < 100 else '[LARGE_VALUE]',
            'changed_by': changed_by,
            'type': 'environment_configuration_change'
        }
        
        self.audit_log.append(log_entry)
        
        # Limit log size
        if len(self.audit_log) > 10000:
            self.audit_log = self.audit_log[-5000:]
    
    async def cleanup(self) -> None:
        """Cleanup environment manager resources"""
        try:
            # Cancel sync tasks
            for task in self.sync_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.hierarchy_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("EnvironmentManager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during EnvironmentManager cleanup: {str(e)}")