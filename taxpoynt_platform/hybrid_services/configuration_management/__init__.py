"""
Configuration Management Hybrid Services Package

This package provides unified configuration management services across the TaxPoynt platform,
coordinating configuration, feature flags, tenant settings, environment management, and secure secret handling
between SI and APP roles.

Components:
- ConfigCoordinator: Coordinates configuration across SI and APP roles
- FeatureFlagManager: Manages feature flags for gradual rollouts and A/B testing  
- TenantConfigurator: Handles multi-tenant configuration requirements
- EnvironmentManager: Manages environment-specific configurations
- SecretsCoordinator: Coordinates secure secret management and rotation
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from taxpoynt_platform.core_platform.shared.base_service import BaseService
from taxpoynt_platform.core_platform.shared.exceptions import ConfigurationError

from .config_coordinator import ConfigCoordinator
from .feature_flag_manager import FeatureFlagManager
from .tenant_configurator import TenantConfigurator
from .environment_manager import EnvironmentManager
from .secrets_coordinator import SecretsCoordinator


__all__ = [
    'ConfigCoordinator',
    'FeatureFlagManager', 
    'TenantConfigurator',
    'EnvironmentManager',
    'SecretsCoordinator',
    'ConfigurationManagementService'
]


class ConfigurationManagementService(BaseService):
    """
    Unified Configuration Management Service
    
    Orchestrates all configuration management components to provide a unified
    interface for configuration across the TaxPoynt platform.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Component services
        self.config_coordinator: Optional[ConfigCoordinator] = None
        self.feature_flag_manager: Optional[FeatureFlagManager] = None
        self.tenant_configurator: Optional[TenantConfigurator] = None
        self.environment_manager: Optional[EnvironmentManager] = None
        self.secrets_coordinator: Optional[SecretsCoordinator] = None
        
        # Service registry
        self.services: Dict[str, BaseService] = {}
        
        # Configuration state
        self.is_initialized = False
        
        # Metrics aggregation
        self.metrics = {
            'total_configurations': 0,
            'total_feature_flags': 0,
            'total_tenants': 0,
            'total_environments': 0,
            'total_secrets': 0,
            'initialization_time': None,
            'last_health_check': None
        }
    
    async def initialize(self) -> None:
        """Initialize all configuration management services"""
        try:
            start_time = datetime.utcnow()
            self.logger.info("Initializing ConfigurationManagementService")
            
            # Initialize config coordinator
            self.config_coordinator = ConfigCoordinator(self.config)
            await self.config_coordinator.initialize()
            self.services['config_coordinator'] = self.config_coordinator
            
            # Initialize feature flag manager
            self.feature_flag_manager = FeatureFlagManager(self.config)
            await self.feature_flag_manager.initialize()
            self.services['feature_flag_manager'] = self.feature_flag_manager
            
            # Initialize tenant configurator
            self.tenant_configurator = TenantConfigurator(self.config)
            await self.tenant_configurator.initialize()
            self.services['tenant_configurator'] = self.tenant_configurator
            
            # Initialize environment manager
            self.environment_manager = EnvironmentManager(self.config)
            await self.environment_manager.initialize()
            self.services['environment_manager'] = self.environment_manager
            
            # Initialize secrets coordinator
            self.secrets_coordinator = SecretsCoordinator(self.config)
            await self.secrets_coordinator.initialize()
            self.services['secrets_coordinator'] = self.secrets_coordinator
            
            # Set up inter-service integration
            await self._setup_service_integration()
            
            # Mark as initialized
            self.is_initialized = True
            end_time = datetime.utcnow()
            self.metrics['initialization_time'] = (end_time - start_time).total_seconds()
            
            self.logger.info("ConfigurationManagementService initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ConfigurationManagementService: {str(e)}")
            raise ConfigurationError(f"Initialization failed: {str(e)}")
    
    async def handle_platform_configuration(
        self,
        operation: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle unified platform configuration operations
        
        This is the main entry point for configuration management operations
        across the entire platform.
        """
        try:
            if not self.is_initialized:
                raise ConfigurationError("Configuration management service not initialized")
            
            operation_handlers = {
                'set_config': self._handle_set_configuration,
                'get_config': self._handle_get_configuration,
                'manage_feature_flag': self._handle_feature_flag_management,
                'manage_tenant': self._handle_tenant_management,
                'manage_environment': self._handle_environment_management,
                'manage_secret': self._handle_secret_management,
                'sync_configurations': self._handle_configuration_sync,
                'validate_configuration': self._handle_configuration_validation
            }
            
            if operation not in operation_handlers:
                raise ValueError(f"Unsupported operation: {operation}")
            
            handler = operation_handlers[operation]
            result = await handler(**kwargs)
            
            # Update metrics
            await self._update_metrics()
            
            return {
                'success': True,
                'operation': operation,
                'result': result,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to handle platform configuration operation {operation}: {str(e)}")
            return {
                'success': False,
                'operation': operation,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_unified_health_status(self) -> Dict[str, Any]:
        """Get unified health status of all configuration management services"""
        try:
            health_status = {
                'service': 'ConfigurationManagementService',
                'status': 'healthy' if self.is_initialized else 'initializing',
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': self.metrics,
                'components': {}
            }
            
            # Get health status from each component
            for service_name, service in self.services.items():
                try:
                    component_health = await service.get_health_status()
                    health_status['components'][service_name] = component_health
                except Exception as e:
                    health_status['components'][service_name] = {
                        'status': 'unhealthy',
                        'error': str(e)
                    }
            
            # Determine overall health
            component_statuses = [
                comp.get('status', 'unknown') 
                for comp in health_status['components'].values()
            ]
            
            if any(status == 'unhealthy' for status in component_statuses):
                health_status['status'] = 'degraded'
            elif any(status != 'healthy' for status in component_statuses):
                health_status['status'] = 'warning'
            
            self.metrics['last_health_check'] = datetime.utcnow().isoformat()
            return health_status
            
        except Exception as e:
            self.logger.error(f"Failed to get unified health status: {str(e)}")
            return {
                'service': 'ConfigurationManagementService',
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _setup_service_integration(self) -> None:
        """Setup integration between configuration management services"""
        try:
            # Set up configuration change propagation
            if self.config_coordinator and self.feature_flag_manager:
                # When configurations change, check if they affect feature flags
                await self.config_coordinator.register_change_listener(
                    'feature_flags.*',
                    self._handle_feature_flag_config_change
                )
            
            # Set up tenant configuration integration
            if self.tenant_configurator and self.environment_manager:
                # Sync tenant configurations across environments
                pass  # Implementation would depend on specific requirements
            
            # Set up secrets integration
            if self.secrets_coordinator and self.config_coordinator:
                # When secrets are rotated, update configurations that reference them
                pass  # Implementation would depend on specific requirements
            
            self.logger.info("Service integration setup completed")
            
        except Exception as e:
            self.logger.error(f"Failed to setup service integration: {str(e)}")
    
    async def _handle_set_configuration(self, **kwargs) -> Dict[str, Any]:
        """Handle set configuration operation"""
        if not self.config_coordinator:
            raise ConfigurationError("Config coordinator not available")
        
        success = await self.config_coordinator.set_configuration(**kwargs)
        return {'success': success}
    
    async def _handle_get_configuration(self, **kwargs) -> Dict[str, Any]:
        """Handle get configuration operation"""
        if not self.config_coordinator:
            raise ConfigurationError("Config coordinator not available")
        
        value = await self.config_coordinator.get_configuration(**kwargs)
        return {'value': value}
    
    async def _handle_feature_flag_management(self, **kwargs) -> Dict[str, Any]:
        """Handle feature flag management operation"""
        if not self.feature_flag_manager:
            raise ConfigurationError("Feature flag manager not available")
        
        action = kwargs.pop('action', 'evaluate')
        
        if action == 'evaluate':
            evaluation = await self.feature_flag_manager.evaluate_flag(**kwargs)
            return {'evaluation': evaluation}
        elif action == 'create':
            flag = await self.feature_flag_manager.create_flag(**kwargs)
            return {'flag': flag}
        elif action == 'update':
            flag = await self.feature_flag_manager.update_flag(**kwargs)
            return {'flag': flag}
        elif action == 'activate':
            success = await self.feature_flag_manager.activate_flag(**kwargs)
            return {'success': success}
        elif action == 'deactivate':
            success = await self.feature_flag_manager.deactivate_flag(**kwargs)
            return {'success': success}
        else:
            raise ValueError(f"Unsupported feature flag action: {action}")
    
    async def _handle_tenant_management(self, **kwargs) -> Dict[str, Any]:
        """Handle tenant management operation"""
        if not self.tenant_configurator:
            raise ConfigurationError("Tenant configurator not available")
        
        action = kwargs.pop('action', 'get_config')
        
        if action == 'create':
            tenant = await self.tenant_configurator.create_tenant(**kwargs)
            return {'tenant': tenant}
        elif action == 'update':
            tenant = await self.tenant_configurator.update_tenant(**kwargs)
            return {'tenant': tenant}
        elif action == 'set_config':
            config = await self.tenant_configurator.set_tenant_configuration(**kwargs)
            return {'config': config}
        elif action == 'get_config':
            value = await self.tenant_configurator.get_tenant_configuration(**kwargs)
            return {'value': value}
        elif action == 'enable_feature':
            success = await self.tenant_configurator.enable_feature(**kwargs)
            return {'success': success}
        elif action == 'disable_feature':
            success = await self.tenant_configurator.disable_feature(**kwargs)
            return {'success': success}
        else:
            raise ValueError(f"Unsupported tenant action: {action}")
    
    async def _handle_environment_management(self, **kwargs) -> Dict[str, Any]:
        """Handle environment management operation"""
        if not self.environment_manager:
            raise ConfigurationError("Environment manager not available")
        
        action = kwargs.pop('action', 'get_config')
        
        if action == 'create':
            environment = await self.environment_manager.create_environment(**kwargs)
            return {'environment': environment}
        elif action == 'set_config':
            config = await self.environment_manager.set_environment_configuration(**kwargs)
            return {'config': config}
        elif action == 'get_config':
            value = await self.environment_manager.get_environment_configuration(**kwargs)
            return {'value': value}
        elif action == 'set_variable':
            var = await self.environment_manager.set_environment_variable(**kwargs)
            return {'variable': var}
        elif action == 'get_variable':
            value = await self.environment_manager.get_environment_variable(**kwargs)
            return {'value': value}
        elif action == 'apply_template':
            success = await self.environment_manager.apply_template(**kwargs)
            return {'success': success}
        elif action == 'sync':
            success = await self.environment_manager.sync_environments(**kwargs)
            return {'success': success}
        elif action == 'promote':
            success = await self.environment_manager.promote_configuration(**kwargs)
            return {'success': success}
        else:
            raise ValueError(f"Unsupported environment action: {action}")
    
    async def _handle_secret_management(self, **kwargs) -> Dict[str, Any]:
        """Handle secret management operation"""
        if not self.secrets_coordinator:
            raise ConfigurationError("Secrets coordinator not available")
        
        action = kwargs.pop('action', 'get')
        
        if action == 'create':
            secret = await self.secrets_coordinator.create_secret(**kwargs)
            return {'secret': secret}
        elif action == 'get':
            value = await self.secrets_coordinator.get_secret(**kwargs)
            return {'value': value}
        elif action == 'update':
            success = await self.secrets_coordinator.update_secret(**kwargs)
            return {'success': success}
        elif action == 'delete':
            success = await self.secrets_coordinator.delete_secret(**kwargs)
            return {'success': success}
        elif action == 'rotate':
            success = await self.secrets_coordinator.rotate_secret(**kwargs)
            return {'success': success}
        elif action == 'grant_access':
            success = await self.secrets_coordinator.grant_access(**kwargs)
            return {'success': success}
        elif action == 'revoke_access':
            success = await self.secrets_coordinator.revoke_access(**kwargs)
            return {'success': success}
        elif action == 'generate':
            value = await self.secrets_coordinator.generate_secret(**kwargs)
            return {'value': value}
        elif action == 'get_metadata':
            metadata = await self.secrets_coordinator.get_secret_metadata(**kwargs)
            return {'metadata': metadata}
        elif action == 'list':
            secrets = await self.secrets_coordinator.list_secrets(**kwargs)
            return {'secrets': secrets}
        else:
            raise ValueError(f"Unsupported secret action: {action}")
    
    async def _handle_configuration_sync(self, **kwargs) -> Dict[str, Any]:
        """Handle configuration synchronization operation"""
        sync_type = kwargs.get('sync_type', 'environment')
        
        if sync_type == 'environment' and self.environment_manager:
            success = await self.environment_manager.sync_environments(**kwargs)
            return {'success': success}
        elif sync_type == 'tenant' and self.tenant_configurator:
            # Implement tenant sync logic
            return {'success': True, 'note': 'Tenant sync not yet implemented'}
        else:
            raise ValueError(f"Unsupported sync type: {sync_type}")
    
    async def _handle_configuration_validation(self, **kwargs) -> Dict[str, Any]:
        """Handle configuration validation operation"""
        validation_type = kwargs.get('validation_type', 'config')
        
        if validation_type == 'config' and self.config_coordinator:
            result = await self.config_coordinator.validate_configuration(**kwargs)
            return {'validation_result': result}
        elif validation_type == 'tenant' and self.tenant_configurator:
            # Implement tenant validation logic
            return {'validation_result': {'is_valid': True, 'note': 'Tenant validation not yet implemented'}}
        else:
            raise ValueError(f"Unsupported validation type: {validation_type}")
    
    async def _handle_feature_flag_config_change(self, change_event) -> None:
        """Handle configuration changes that affect feature flags"""
        try:
            # When feature flag configurations change, update the feature flag manager
            if self.feature_flag_manager and change_event.config_key.startswith('feature_flags.'):
                flag_key = change_event.config_key.replace('feature_flags.', '')
                # Update feature flag based on configuration change
                self.logger.info(f"Feature flag configuration changed: {flag_key}")
                
        except Exception as e:
            self.logger.error(f"Failed to handle feature flag config change: {str(e)}")
    
    async def _update_metrics(self) -> None:
        """Update aggregated metrics"""
        try:
            # Update configuration count
            if self.config_coordinator:
                self.metrics['total_configurations'] = len(self.config_coordinator.configs)
            
            # Update feature flag count
            if self.feature_flag_manager:
                self.metrics['total_feature_flags'] = len(self.feature_flag_manager.flags)
            
            # Update tenant count
            if self.tenant_configurator:
                self.metrics['total_tenants'] = len(self.tenant_configurator.tenants)
            
            # Update environment count
            if self.environment_manager:
                self.metrics['total_environments'] = len(self.environment_manager.environments)
            
            # Update secret count
            if self.secrets_coordinator:
                self.metrics['total_secrets'] = len(self.secrets_coordinator.secrets)
                
        except Exception as e:
            self.logger.error(f"Failed to update metrics: {str(e)}")
    
    async def cleanup(self) -> None:
        """Cleanup all configuration management services"""
        try:
            self.logger.info("Starting ConfigurationManagementService cleanup")
            
            # Cleanup all services
            cleanup_tasks = []
            for service_name, service in self.services.items():
                if hasattr(service, 'cleanup'):
                    cleanup_tasks.append(service.cleanup())
            
            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            # Clear service registry
            self.services.clear()
            
            # Reset state
            self.is_initialized = False
            
            self.logger.info("ConfigurationManagementService cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during ConfigurationManagementService cleanup: {str(e)}")


# Convenience functions for direct service access
async def get_configuration_service(config: Optional[Dict[str, Any]] = None) -> ConfigurationManagementService:
    """Get initialized configuration management service"""
    service = ConfigurationManagementService(config)
    await service.initialize()
    return service


async def handle_configuration_operation(operation: str, config: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
    """Handle a configuration operation with automatic service management"""
    service = await get_configuration_service(config)
    try:
        return await service.handle_platform_configuration(operation, **kwargs)
    finally:
        await service.cleanup()


# Service factory functions
def create_config_coordinator(config: Optional[Dict[str, Any]] = None) -> ConfigCoordinator:
    """Create and return a ConfigCoordinator instance"""
    return ConfigCoordinator(config)


def create_feature_flag_manager(config: Optional[Dict[str, Any]] = None) -> FeatureFlagManager:
    """Create and return a FeatureFlagManager instance"""
    return FeatureFlagManager(config)


def create_tenant_configurator(config: Optional[Dict[str, Any]] = None) -> TenantConfigurator:
    """Create and return a TenantConfigurator instance"""
    return TenantConfigurator(config)


def create_environment_manager(config: Optional[Dict[str, Any]] = None) -> EnvironmentManager:
    """Create and return an EnvironmentManager instance"""
    return EnvironmentManager(config)


def create_secrets_coordinator(config: Optional[Dict[str, Any]] = None) -> SecretsCoordinator:
    """Create and return a SecretsCoordinator instance"""
    return SecretsCoordinator(config)


# Package-level configuration
DEFAULT_CONFIG = {
    'config_coordinator': {
        'cache_ttl_minutes': 5,
        'max_configs': 10000,
        'enable_change_tracking': True
    },
    'feature_flag_manager': {
        'cache_ttl_seconds': 30,
        'max_flags': 1000,
        'enable_metrics': True
    },
    'tenant_configurator': {
        'cache_ttl_minutes': 5,
        'max_tenants': 1000,
        'enable_inheritance': True
    },
    'environment_manager': {
        'cache_ttl_minutes': 10,
        'auto_detect_environment': True,
        'enable_sync': True
    },
    'secrets_coordinator': {
        'enable_rotation': True,
        'default_rotation_days': 90,
        'enable_audit_logging': True,
        'max_secret_versions': 10
    }
}


def get_default_config() -> Dict[str, Any]:
    """Get default configuration for configuration management services"""
    return DEFAULT_CONFIG.copy()


# Package metadata
__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"
__description__ = "Unified configuration management services for the TaxPoynt platform"