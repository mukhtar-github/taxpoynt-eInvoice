"""
Integration Management Dependency Injector

Configures and wires dependencies between integration management components.
Implements dependency injection pattern to eliminate code duplication and
improve testability and maintainability.
"""

import logging
from typing import Dict, Any

from .config_manager import config_manager
from .connection_tester import connection_tester
from .metrics_collector import metrics_collector
from .integration_health_monitor import integration_health_monitor
from .lifecycle_manager import lifecycle_manager
from .connection_manager import connection_manager
from .auth_coordinator import auth_coordinator

logger = logging.getLogger(__name__)


class IntegrationDependencyInjector:
    """Manages dependency injection for integration management components"""
    
    def __init__(self):
        self.components_configured = False
    
    def configure_dependencies(self) -> bool:
        """
        Configure dependencies between all integration management components.
        
        Returns:
            Success status
        """
        try:
            logger.info("Configuring integration management dependencies...")
            
            # Configure Integration Health Monitor dependencies
            integration_health_monitor.set_connection_tester(connection_tester)
            
            # Configure Lifecycle Manager dependencies 
            lifecycle_manager.set_dependencies(
                config_manager=config_manager,
                connection_tester=connection_tester,
                status_monitor=integration_health_monitor,
                metrics_collector=metrics_collector
            )
            
            # Configure Connection Manager dependencies
            connection_manager.set_connection_tester(connection_tester)
            connection_manager.set_auth_coordinator(auth_coordinator)
            
            # Configure Auth Coordinator dependencies
            auth_coordinator.set_config_manager(config_manager)
            
            self.components_configured = True
            logger.info("Successfully configured integration management dependencies")
            return True
            
        except Exception as e:
            logger.error(f"Failed to configure dependencies: {e}")
            return False
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """
        Get the current dependency configuration status.
        
        Returns:
            Configuration status details
        """
        return {
            "configured": self.components_configured,
            "components": {
                "config_manager": "ready" if config_manager else "not_available",
                "connection_tester": "ready" if connection_tester else "not_available", 
                "metrics_collector": "ready" if metrics_collector else "not_available",
                "integration_health_monitor": "ready" if integration_health_monitor else "not_available",
                "lifecycle_manager": "ready" if lifecycle_manager else "not_available",
                "connection_manager": "ready" if connection_manager else "not_available",
                "auth_coordinator": "ready" if auth_coordinator else "not_available"
            },
            "dependency_status": {
                "lifecycle_manager_deps": {
                    "config_manager": bool(lifecycle_manager.config_manager),
                    "connection_tester": bool(lifecycle_manager.connection_tester),
                    "status_monitor": bool(lifecycle_manager.status_monitor),
                    "metrics_collector": bool(lifecycle_manager.metrics_collector)
                },
                "health_monitor_deps": {
                    "connection_tester": bool(integration_health_monitor.connection_tester)
                },
                "connection_manager_deps": {
                    "connection_tester": bool(connection_manager.connection_tester),
                    "auth_coordinator": bool(connection_manager.auth_coordinator)
                }
            }
        }
    
    def validate_configuration(self) -> bool:
        """
        Validate that all required dependencies are properly configured.
        
        Returns:
            Validation success status
        """
        if not self.components_configured:
            return False
        
        # Check critical dependencies
        if not lifecycle_manager.config_manager:
            logger.error("Lifecycle Manager missing Config Manager dependency")
            return False
        
        if not lifecycle_manager.connection_tester:
            logger.error("Lifecycle Manager missing Connection Tester dependency")
            return False
        
        if not integration_health_monitor.connection_tester:
            logger.error("Integration Health Monitor missing Connection Tester dependency")
            return False
        
        return True


# Global dependency injector instance
dependency_injector = IntegrationDependencyInjector()


def configure_integration_dependencies() -> bool:
    """
    Configure dependencies for all integration management components.
    
    Returns:
        Configuration success status
    """
    return dependency_injector.configure_dependencies()


def get_dependency_status() -> Dict[str, Any]:
    """
    Get current dependency configuration status.
    
    Returns:
        Status details
    """
    return dependency_injector.get_configuration_status()


def validate_dependencies() -> bool:
    """
    Validate that all dependencies are properly configured.
    
    Returns:
        Validation success status  
    """
    return dependency_injector.validate_configuration()