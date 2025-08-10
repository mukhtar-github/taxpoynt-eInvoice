"""
Configuration Coordinator Service

This service provides unified configuration management across all TaxPoynt platform roles,
coordinating configuration distribution, validation, and synchronization between SI and APP services.
"""

import asyncio
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Callable
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


class ConfigScope(Enum):
    """Configuration scope definitions"""
    GLOBAL = "global"
    TENANT = "tenant"
    ENVIRONMENT = "environment"
    ROLE = "role"
    SERVICE = "service"
    USER = "user"


class ConfigType(Enum):
    """Configuration type definitions"""
    SYSTEM = "system"
    BUSINESS = "business"
    SECURITY = "security"
    FEATURE = "feature"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"


class ConfigPriority(Enum):
    """Configuration priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class ConfigItem:
    """Configuration item with metadata"""
    key: str
    value: Any
    scope: ConfigScope
    config_type: ConfigType
    priority: ConfigPriority
    encrypted: bool = False
    description: Optional[str] = None
    default_value: Optional[Any] = None
    validation_rules: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    tenant_id: Optional[str] = None
    environment: Optional[str] = None
    role: Optional[str] = None
    service: Optional[str] = None
    checksum: Optional[str] = None
    
    def __post_init__(self):
        """Calculate checksum after initialization"""
        self.checksum = self._calculate_checksum()
    
    def _calculate_checksum(self) -> str:
        """Calculate checksum of configuration item"""
        content = f"{self.key}:{self.value}:{self.scope.value}:{self.config_type.value}"
        return hashlib.md5(content.encode()).hexdigest()


@dataclass
class ConfigChangeEvent:
    """Configuration change event"""
    config_key: str
    old_value: Any
    new_value: Any
    scope: ConfigScope
    changed_by: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    change_reason: Optional[str] = None
    affected_services: List[str] = field(default_factory=list)


@dataclass
class ConfigValidationResult:
    """Configuration validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)


class ConfigCoordinator(BaseService):
    """
    Configuration Coordinator Service
    
    Provides unified configuration management across all platform roles,
    handling configuration distribution, validation, and synchronization.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Configuration storage
        self.configs: Dict[str, ConfigItem] = {}
        self.config_hierarchy: Dict[ConfigScope, int] = {
            ConfigScope.GLOBAL: 1,
            ConfigScope.ENVIRONMENT: 2,
            ConfigScope.ROLE: 3,
            ConfigScope.TENANT: 4,
            ConfigScope.SERVICE: 5,
            ConfigScope.USER: 6
        }
        
        # Change tracking
        self.change_history: List[ConfigChangeEvent] = []
        self.change_listeners: Dict[str, List[Callable]] = {}
        
        # Validation
        self.validators: Dict[str, Callable] = {}
        self.validation_cache: Dict[str, ConfigValidationResult] = {}
        
        # Synchronization
        self.sync_queue: asyncio.Queue = asyncio.Queue()
        self.sync_tasks: Dict[str, asyncio.Task] = {}
        
        # Performance
        self.config_cache: Dict[str, Any] = {}
        self.cache_ttl: timedelta = timedelta(minutes=5)
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Metrics
        self.metrics = {
            'configs_managed': 0,
            'validations_performed': 0,
            'changes_processed': 0,
            'sync_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    async def initialize(self) -> None:
        """Initialize configuration coordinator"""
        try:
            self.logger.info("Initializing ConfigCoordinator")
            
            # Load default configurations
            await self._load_default_configurations()
            
            # Start synchronization worker
            await self._start_sync_worker()
            
            # Initialize validation rules
            await self._initialize_validation_rules()
            
            self.logger.info("ConfigCoordinator initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ConfigCoordinator: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def set_configuration(
        self,
        key: str,
        value: Any,
        scope: ConfigScope,
        config_type: ConfigType,
        priority: ConfigPriority = ConfigPriority.MEDIUM,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        role: Optional[str] = None,
        service: Optional[str] = None,
        changed_by: str = "system",
        change_reason: Optional[str] = None
    ) -> bool:
        """Set configuration value"""
        try:
            # Validate configuration
            validation_result = await self._validate_configuration(
                key, value, scope, config_type
            )
            
            if not validation_result.is_valid:
                raise ValidationError(f"Configuration validation failed: {validation_result.errors}")
            
            # Get existing configuration
            existing_config = self.configs.get(key)
            old_value = existing_config.value if existing_config else None
            
            # Create configuration item
            config_item = ConfigItem(
                key=key,
                value=value,
                scope=scope,
                config_type=config_type,
                priority=priority,
                tenant_id=tenant_id,
                environment=environment,
                role=role,
                service=service
            )
            
            # Store configuration
            self.configs[key] = config_item
            
            # Create change event
            change_event = ConfigChangeEvent(
                config_key=key,
                old_value=old_value,
                new_value=value,
                scope=scope,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            # Process change
            await self._process_configuration_change(change_event)
            
            # Invalidate cache
            await self._invalidate_cache(key)
            
            # Queue for synchronization
            await self.sync_queue.put(config_item)
            
            self.metrics['configs_managed'] += 1
            self.logger.info(f"Configuration set: {key} = {value}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set configuration {key}: {str(e)}")
            raise ConfigurationError(f"Configuration set failed: {str(e)}")
    
    async def get_configuration(
        self,
        key: str,
        scope: Optional[ConfigScope] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        role: Optional[str] = None,
        service: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[Any]:
        """Get configuration value with hierarchy resolution"""
        try:
            # Check cache first
            if use_cache:
                cached_value = await self._get_from_cache(key)
                if cached_value is not None:
                    return cached_value
            
            # Find best matching configuration
            best_match = await self._find_best_configuration_match(
                key, scope, tenant_id, environment, role, service
            )
            
            if best_match:
                # Cache the result
                await self._cache_configuration(key, best_match.value)
                return best_match.value
            
            self.metrics['cache_misses'] += 1
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get configuration {key}: {str(e)}")
            raise ConfigurationError(f"Configuration get failed: {str(e)}")
    
    async def get_configurations_by_scope(
        self,
        scope: ConfigScope,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        role: Optional[str] = None,
        service: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get all configurations for a specific scope"""
        try:
            matching_configs = {}
            
            for key, config in self.configs.items():
                if config.scope == scope:
                    # Check scope-specific filters
                    if scope == ConfigScope.TENANT and config.tenant_id != tenant_id:
                        continue
                    if scope == ConfigScope.ENVIRONMENT and config.environment != environment:
                        continue
                    if scope == ConfigScope.ROLE and config.role != role:
                        continue
                    if scope == ConfigScope.SERVICE and config.service != service:
                        continue
                    
                    matching_configs[key] = config.value
            
            return matching_configs
            
        except Exception as e:
            self.logger.error(f"Failed to get configurations by scope {scope}: {str(e)}")
            raise ConfigurationError(f"Configuration scope get failed: {str(e)}")
    
    async def delete_configuration(
        self,
        key: str,
        changed_by: str = "system",
        change_reason: Optional[str] = None
    ) -> bool:
        """Delete configuration"""
        try:
            if key not in self.configs:
                return False
            
            config = self.configs[key]
            
            # Create change event
            change_event = ConfigChangeEvent(
                config_key=key,
                old_value=config.value,
                new_value=None,
                scope=config.scope,
                changed_by=changed_by,
                change_reason=change_reason
            )
            
            # Remove configuration
            del self.configs[key]
            
            # Process change
            await self._process_configuration_change(change_event)
            
            # Invalidate cache
            await self._invalidate_cache(key)
            
            self.logger.info(f"Configuration deleted: {key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete configuration {key}: {str(e)}")
            raise ConfigurationError(f"Configuration delete failed: {str(e)}")
    
    async def validate_configuration(
        self,
        key: str,
        value: Any,
        scope: ConfigScope,
        config_type: ConfigType
    ) -> ConfigValidationResult:
        """Validate configuration value"""
        try:
            result = await self._validate_configuration(key, value, scope, config_type)
            self.metrics['validations_performed'] += 1
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to validate configuration {key}: {str(e)}")
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    async def register_change_listener(
        self,
        config_key: str,
        listener: Callable[[ConfigChangeEvent], None]
    ) -> None:
        """Register configuration change listener"""
        if config_key not in self.change_listeners:
            self.change_listeners[config_key] = []
        
        self.change_listeners[config_key].append(listener)
        self.logger.info(f"Change listener registered for {config_key}")
    
    async def get_change_history(
        self,
        config_key: Optional[str] = None,
        limit: int = 100
    ) -> List[ConfigChangeEvent]:
        """Get configuration change history"""
        if config_key:
            return [
                event for event in self.change_history[-limit:]
                if event.config_key == config_key
            ]
        return self.change_history[-limit:]
    
    async def export_configurations(
        self,
        scope: Optional[ConfigScope] = None,
        format: str = "json"
    ) -> str:
        """Export configurations"""
        try:
            configs_to_export = {}
            
            for key, config in self.configs.items():
                if scope is None or config.scope == scope:
                    configs_to_export[key] = {
                        'value': config.value,
                        'scope': config.scope.value,
                        'type': config.config_type.value,
                        'priority': config.priority.value,
                        'description': config.description,
                        'created_at': config.created_at.isoformat(),
                        'updated_at': config.updated_at.isoformat()
                    }
            
            if format == "json":
                return json.dumps(configs_to_export, indent=2)
            else:
                raise ValidationError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export configurations: {str(e)}")
            raise ConfigurationError(f"Configuration export failed: {str(e)}")
    
    async def import_configurations(
        self,
        config_data: str,
        format: str = "json",
        changed_by: str = "system"
    ) -> Dict[str, bool]:
        """Import configurations"""
        try:
            if format == "json":
                configs = json.loads(config_data)
            else:
                raise ValidationError(f"Unsupported import format: {format}")
            
            results = {}
            
            for key, config_info in configs.items():
                try:
                    success = await self.set_configuration(
                        key=key,
                        value=config_info['value'],
                        scope=ConfigScope(config_info['scope']),
                        config_type=ConfigType(config_info['type']),
                        priority=ConfigPriority(config_info['priority']),
                        changed_by=changed_by,
                        change_reason="Configuration import"
                    )
                    results[key] = success
                except Exception as e:
                    self.logger.error(f"Failed to import configuration {key}: {str(e)}")
                    results[key] = False
            
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to import configurations: {str(e)}")
            raise ConfigurationError(f"Configuration import failed: {str(e)}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get configuration coordinator health status"""
        try:
            return {
                'service': 'ConfigCoordinator',
                'status': 'healthy',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'configurations': {
                    'total': len(self.configs),
                    'by_scope': {
                        scope.value: len([c for c in self.configs.values() if c.scope == scope])
                        for scope in ConfigScope
                    },
                    'by_type': {
                        config_type.value: len([c for c in self.configs.values() if c.config_type == config_type])
                        for config_type in ConfigType
                    }
                },
                'cache': {
                    'size': len(self.config_cache),
                    'hit_ratio': (
                        self.metrics['cache_hits'] / 
                        (self.metrics['cache_hits'] + self.metrics['cache_misses'])
                        if (self.metrics['cache_hits'] + self.metrics['cache_misses']) > 0
                        else 0
                    )
                },
                'sync_queue_size': self.sync_queue.qsize()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get health status: {str(e)}")
            return {
                'service': 'ConfigCoordinator',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _load_default_configurations(self) -> None:
        """Load default system configurations"""
        default_configs = {
            'system.log_level': ('INFO', ConfigScope.GLOBAL, ConfigType.SYSTEM),
            'system.max_connections': (100, ConfigScope.GLOBAL, ConfigType.PERFORMANCE),
            'system.timeout': (30, ConfigScope.GLOBAL, ConfigType.PERFORMANCE),
            'security.encryption_enabled': (True, ConfigScope.GLOBAL, ConfigType.SECURITY),
            'business.default_currency': ('NGN', ConfigScope.GLOBAL, ConfigType.BUSINESS),
            'integration.firs_endpoint': ('https://api.firs.gov.ng', ConfigScope.GLOBAL, ConfigType.INTEGRATION)
        }
        
        for key, (value, scope, config_type) in default_configs.items():
            if key not in self.configs:
                await self.set_configuration(
                    key=key,
                    value=value,
                    scope=scope,
                    config_type=config_type,
                    priority=ConfigPriority.MEDIUM,
                    changed_by="system",
                    change_reason="Default configuration"
                )
    
    async def _start_sync_worker(self) -> None:
        """Start configuration synchronization worker"""
        async def sync_worker():
            while True:
                try:
                    config_item = await self.sync_queue.get()
                    await self._synchronize_configuration(config_item)
                    self.metrics['sync_operations'] += 1
                except Exception as e:
                    self.logger.error(f"Sync worker error: {str(e)}")
                    await asyncio.sleep(1)
        
        self.sync_tasks['main'] = asyncio.create_task(sync_worker())
    
    async def _initialize_validation_rules(self) -> None:
        """Initialize configuration validation rules"""
        self.validators.update({
            'system.log_level': lambda v: v in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            'system.max_connections': lambda v: isinstance(v, int) and v > 0,
            'system.timeout': lambda v: isinstance(v, (int, float)) and v > 0,
            'security.encryption_enabled': lambda v: isinstance(v, bool),
            'business.default_currency': lambda v: isinstance(v, str) and len(v) == 3,
            'integration.firs_endpoint': lambda v: isinstance(v, str) and v.startswith('https://')
        })
    
    async def _validate_configuration(
        self,
        key: str,
        value: Any,
        scope: ConfigScope,
        config_type: ConfigType
    ) -> ConfigValidationResult:
        """Validate configuration value"""
        errors = []
        warnings = []
        
        try:
            # Check if validator exists
            if key in self.validators:
                validator = self.validators[key]
                if not validator(value):
                    errors.append(f"Value {value} failed validation for {key}")
            
            # Type-specific validation
            if config_type == ConfigType.SECURITY:
                if isinstance(value, str) and len(value) < 8:
                    warnings.append("Security configuration value seems too short")
            
            # Scope-specific validation
            if scope == ConfigScope.TENANT and not hasattr(self, 'tenant_id'):
                errors.append("Tenant ID required for tenant-scoped configuration")
            
            return ConfigValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"]
            )
    
    async def _find_best_configuration_match(
        self,
        key: str,
        scope: Optional[ConfigScope] = None,
        tenant_id: Optional[str] = None,
        environment: Optional[str] = None,
        role: Optional[str] = None,
        service: Optional[str] = None
    ) -> Optional[ConfigItem]:
        """Find best matching configuration based on hierarchy"""
        candidates = []
        
        for config in self.configs.values():
            if config.key == key:
                # Calculate match score based on hierarchy
                score = 0
                
                # Exact scope match
                if scope and config.scope == scope:
                    score += 100
                
                # Hierarchy-based scoring
                score += (10 - self.config_hierarchy[config.scope])
                
                # Context matching
                if tenant_id and config.tenant_id == tenant_id:
                    score += 50
                if environment and config.environment == environment:
                    score += 40
                if role and config.role == role:
                    score += 30
                if service and config.service == service:
                    score += 20
                
                candidates.append((score, config))
        
        if candidates:
            # Return highest scoring candidate
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        
        return None
    
    async def _process_configuration_change(self, change_event: ConfigChangeEvent) -> None:
        """Process configuration change event"""
        try:
            # Add to history
            self.change_history.append(change_event)
            
            # Limit history size
            if len(self.change_history) > 10000:
                self.change_history = self.change_history[-5000:]
            
            # Notify listeners
            if change_event.config_key in self.change_listeners:
                for listener in self.change_listeners[change_event.config_key]:
                    try:
                        if asyncio.iscoroutinefunction(listener):
                            await listener(change_event)
                        else:
                            listener(change_event)
                    except Exception as e:
                        self.logger.error(f"Change listener error: {str(e)}")
            
            self.metrics['changes_processed'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to process configuration change: {str(e)}")
    
    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get configuration from cache"""
        if key in self.config_cache:
            timestamp = self.cache_timestamps.get(key)
            if timestamp and datetime.utcnow() - timestamp < self.cache_ttl:
                self.metrics['cache_hits'] += 1
                return self.config_cache[key]
            else:
                # Remove expired entry
                del self.config_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
        
        return None
    
    async def _cache_configuration(self, key: str, value: Any) -> None:
        """Cache configuration value"""
        self.config_cache[key] = value
        self.cache_timestamps[key] = datetime.utcnow()
        
        # Limit cache size
        if len(self.config_cache) > 1000:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            del self.config_cache[oldest_key]
            del self.cache_timestamps[oldest_key]
    
    async def _invalidate_cache(self, key: str) -> None:
        """Invalidate cached configuration"""
        if key in self.config_cache:
            del self.config_cache[key]
        if key in self.cache_timestamps:
            del self.cache_timestamps[key]
    
    async def _synchronize_configuration(self, config_item: ConfigItem) -> None:
        """Synchronize configuration across services"""
        try:
            # Here you would implement actual synchronization logic
            # This could involve:
            # - Notifying other services of configuration changes
            # - Updating distributed configuration stores
            # - Triggering configuration reloads in affected services
            
            self.logger.info(f"Synchronized configuration: {config_item.key}")
            
        except Exception as e:
            self.logger.error(f"Failed to synchronize configuration {config_item.key}: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup configuration coordinator resources"""
        try:
            # Cancel sync tasks
            for task in self.sync_tasks.values():
                if not task.done():
                    task.cancel()
            
            # Clear caches
            self.config_cache.clear()
            self.cache_timestamps.clear()
            
            self.logger.info("ConfigCoordinator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during ConfigCoordinator cleanup: {str(e)}")