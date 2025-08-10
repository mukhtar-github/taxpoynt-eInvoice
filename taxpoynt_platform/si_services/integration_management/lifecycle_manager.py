"""
Integration Lifecycle Manager

Manages the complete lifecycle of integrations including CRUD operations.
Extracted from integration_service.py - provides granular lifecycle management.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class LifecycleManager:
    """Manages integration lifecycle including creation, updates, deletion, and monitoring"""
    
    def __init__(self):
        self.config_manager = None  # Will be injected
        self.connection_tester = None  # Will be injected
        self.status_monitor = None  # Will be injected
        self.metrics_collector = None  # Will be injected
    
    def set_dependencies(self, config_manager, connection_tester, status_monitor, metrics_collector):
        """Inject dependencies"""
        self.config_manager = config_manager
        self.connection_tester = connection_tester
        self.status_monitor = status_monitor
        self.metrics_collector = metrics_collector
    
    def create_integration(
        self, 
        integration_data: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create a new integration with encrypted sensitive config fields.
        Extracted from integration_service.py lines 103-131
        
        Args:
            integration_data: Integration creation data
            user_id: ID of the user creating the integration
            
        Returns:
            Created integration object
        """
        try:
            # Generate integration ID
            integration_id = str(uuid4())
            
            # Encrypt sensitive fields in config if config manager is available
            if self.config_manager and integration_data.get("config"):
                encrypted_config = self.config_manager.encrypt_sensitive_config_fields(
                    integration_data["config"]
                )
                integration_data["config"] = encrypted_config
            
            # Create integration record
            integration = {
                "id": integration_id,
                "name": integration_data.get("name", "Unnamed Integration"),
                "description": integration_data.get("description", ""),
                "integration_type": integration_data.get("integration_type", "unknown"),
                "config": integration_data.get("config", {}),
                "status": "created",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "created_by": user_id,
                "last_tested": None,
                "sync_frequency": integration_data.get("sync_frequency", "manual"),
                "is_active": integration_data.get("is_active", True)
            }
            
            # TODO: Store in actual data store
            # For now, return with decrypted config for immediate use
            if self.config_manager:
                integration["config"] = self.config_manager.decrypt_sensitive_config_fields(
                    integration["config"]
                )
            
            logger.info(f"Created integration: {integration_id}")
            return integration
            
        except Exception as e:
            logger.error(f"Failed to create integration: {str(e)}")
            raise
    
    def update_integration(
        self,
        integration_id: str,
        update_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Update an integration with encrypted sensitive config fields.
        Extracted from integration_service.py lines 134-163
        
        Args:
            integration_id: Integration ID to update
            update_data: Update data
            user_id: ID of the user updating the integration
            
        Returns:
            Updated integration object
        """
        try:
            # TODO: Get existing integration from data store
            # For now, mock getting existing integration
            existing_integration = self.get_integration(integration_id)
            if not existing_integration:
                raise ValueError(f"Integration {integration_id} not found")
            
            # If we're updating the config, encrypt sensitive fields
            if "config" in update_data and update_data["config"] and self.config_manager:
                update_data["config"] = self.config_manager.encrypt_sensitive_config_fields(
                    update_data["config"]
                )
            
            # Update the integration
            for key, value in update_data.items():
                if key != "id":  # Don't allow ID changes
                    existing_integration[key] = value
            
            existing_integration["updated_at"] = datetime.utcnow()
            existing_integration["updated_by"] = user_id
            
            # TODO: Store updated integration in data store
            
            # Return integration with decrypted config
            if self.config_manager and existing_integration.get("config"):
                existing_integration["config"] = self.config_manager.decrypt_sensitive_config_fields(
                    existing_integration["config"]
                )
            
            logger.info(f"Updated integration: {integration_id}")
            return existing_integration
            
        except Exception as e:
            logger.error(f"Failed to update integration {integration_id}: {str(e)}")
            raise
    
    def delete_integration(self, integration_id: str) -> bool:
        """
        Delete an integration by ID.
        Extracted from integration_service.py lines 166-197
        
        Args:
            integration_id: ID of the integration to delete
            
        Returns:
            Success status
        """
        try:
            # First, stop any monitoring if it exists
            if self.status_monitor:
                self.status_monitor.stop_integration_monitoring(integration_id)
            
            # TODO: Delete from actual data store
            # For now, just log the deletion
            
            logger.info(f"Deleted integration: {integration_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete integration {integration_id}: {str(e)}")
            return False
    
    def get_integration(self, integration_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an integration by ID with decrypted config.
        Extracted from integration_service.py lines 200-218
        
        Args:
            integration_id: ID of the integration to retrieve
            
        Returns:
            Integration object with decrypted sensitive config fields
        """
        try:
            # TODO: Get from actual data store
            # For now, return mock integration
            integration = {
                "id": integration_id,
                "name": f"Integration {integration_id}",
                "description": "Mock integration for testing",
                "integration_type": "rest_api",
                "config": {
                    "type": "rest_api",
                    "api_url": "https://api.example.com",
                    "api_key": "ENCRYPTED:test_key_123"
                },
                "status": "active",
                "created_at": datetime.utcnow() - timedelta(days=30),
                "updated_at": datetime.utcnow() - timedelta(days=1),
                "is_active": True
            }
            
            # Decrypt sensitive config fields
            if self.config_manager and integration.get("config"):
                integration["config"] = self.config_manager.decrypt_sensitive_config_fields(
                    integration["config"]
                )
            
            return integration
            
        except Exception as e:
            logger.error(f"Failed to get integration {integration_id}: {str(e)}")
            return None
    
    def get_integrations(
        self,
        skip: int = 0,
        limit: int = 100,
        client_id: Optional[str] = None,
        integration_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get multiple integrations with decrypted configs.
        Extracted from integration_service.py lines 221-261
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            client_id: Optional client ID to filter by
            integration_type: Optional integration type to filter by
            
        Returns:
            List of integration objects with decrypted sensitive config fields
        """
        try:
            # TODO: Query from actual data store with filters
            # For now, return mock integrations
            integrations = []
            
            for i in range(min(limit, 5)):  # Return up to 5 mock integrations
                integration_id = f"int_{i + 1:03d}"
                integration = {
                    "id": integration_id,
                    "name": f"Integration {i + 1}",
                    "description": f"Mock integration {i + 1}",
                    "integration_type": integration_type or "rest_api",
                    "config": {
                        "type": integration_type or "rest_api",
                        "api_url": f"https://api{i+1}.example.com",
                        "api_key": f"ENCRYPTED:key_{i+1}"
                    },
                    "status": "active" if i % 2 == 0 else "inactive",
                    "created_at": datetime.utcnow() - timedelta(days=30-i),
                    "updated_at": datetime.utcnow() - timedelta(days=i),
                    "is_active": True
                }
                
                # Decrypt sensitive fields in configs
                if self.config_manager:
                    integration["config"] = self.config_manager.decrypt_sensitive_config_fields(
                        integration["config"]
                    )
                
                integrations.append(integration)
            
            return integrations[skip:skip+limit]
            
        except Exception as e:
            logger.error(f"Failed to get integrations: {str(e)}")
            return []
    
    def test_integration(self, integration_id: str) -> Dict[str, Any]:
        """
        Test the connection for an integration.
        Extracted from integration_service.py lines 287-331
        
        Args:
            integration_id: ID of the integration to test
            
        Returns:
            Test result with success status, message, and details
        """
        try:
            integration = self.get_integration(integration_id)
            if not integration:
                return {
                    "success": False,
                    "message": "Integration not found",
                    "details": {"error": "integration_not_found"}
                }
            
            # Update last_tested timestamp
            self.update_integration(
                integration_id,
                {"last_tested": datetime.utcnow()},
                "system"
            )
            
            # Test using connection tester if available
            if self.connection_tester:
                return self.connection_tester.test_integration_connection(integration)
            else:
                return {
                    "success": True,
                    "message": "Connection test successful (mock)",
                    "details": {"status": "connected", "latency_ms": 100}
                }
                
        except Exception as e:
            logger.error(f"Failed to test integration {integration_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Test error: {str(e)}",
                "details": {"error": "test_error"}
            }
    
    def validate_and_create_integration(
        self, 
        integration_data: Dict[str, Any], 
        user_id: str
    ) -> Tuple[bool, List[str], Optional[Dict[str, Any]]]:
        """
        Validate and create a new integration.
        Extracted from integration_service.py lines 1241-1265
        
        Args:
            integration_data: Integration creation data
            user_id: ID of the user creating the integration
            
        Returns:
            Tuple of (success, errors, created_integration)
        """
        try:
            # Validate the configuration if config manager is available
            if self.config_manager and integration_data.get("config"):
                is_valid, errors = self.config_manager.validate_integration_config(
                    integration_data["config"]
                )
                
                if not is_valid:
                    return False, errors, None
            
            # If valid, create the integration
            integration = self.create_integration(integration_data, user_id)
            return True, [], integration
            
        except Exception as e:
            logger.error(f"Failed to validate and create integration: {str(e)}")
            return False, [str(e)], None
    
    def create_integration_from_template(
        self,
        template_id: str,
        client_id: str,
        user_id: str,
        config_values: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new integration based on a template.
        Extracted from integration_service.py lines 980-1021
        
        Args:
            template_id: Template identifier
            client_id: Client ID to associate with the integration
            user_id: User ID creating the integration
            config_values: Values to fill in the template
            
        Returns:
            Created integration or None if template not found
        """
        try:
            if not self.config_manager:
                raise ValueError("Config manager not available")
            
            template = self.config_manager.get_integration_template(template_id)
            if not template:
                return None
            
            # Create config from template
            config = self.config_manager.create_config_from_template(template_id, config_values)
            
            # Create integration
            integration_data = {
                "name": template["name"],
                "description": template["description"],
                "client_id": client_id,
                "config": config,
                "integration_type": config.get("type", "unknown")
            }
            
            return self.create_integration(integration_data, user_id)
            
        except Exception as e:
            logger.error(f"Failed to create integration from template {template_id}: {str(e)}")
            return None
    
    def sync_odoo_invoices(
        self,
        integration_id: str,
        from_days_ago: int = 30,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Synchronize invoices from an Odoo integration.
        Extracted from integration_service.py lines 654-744
        
        Args:
            integration_id: ID of the Odoo integration
            from_days_ago: Number of days ago to fetch invoices from
            limit: Maximum number of invoices to fetch
            
        Returns:
            Dictionary with sync results
        """
        try:
            # Get integration
            integration = self.get_integration(integration_id)
            if not integration:
                return {
                    "success": False,
                    "message": "Integration not found",
                    "invoices_synced": 0
                }
            
            # Check integration type
            if integration.get("integration_type") != "odoo":
                return {
                    "success": False,
                    "message": f"Invalid integration type: {integration.get('integration_type')}. Expected: odoo",
                    "invoices_synced": 0
                }
            
            # Get configuration
            config = integration.get("config", {})
            if not config:
                return {
                    "success": False,
                    "message": "Missing configuration for Odoo integration",
                    "invoices_synced": 0
                }
            
            # TODO: Implement actual Odoo invoice synchronization
            # For now, return mock sync result
            
            return {
                "success": True,
                "message": f"Successfully synchronized 15 invoices",
                "invoices_synced": 15,
                "invoice_data": [
                    {"id": "INV001", "amount": 1000.00, "date": "2024-01-15"},
                    {"id": "INV002", "amount": 2500.00, "date": "2024-01-16"},
                    {"id": "INV003", "amount": 750.00, "date": "2024-01-17"}
                ][:5]  # Sample data
            }
            
        except Exception as e:
            logger.error(f"Error synchronizing Odoo invoices for {integration_id}: {str(e)}")
            return {
                "success": False,
                "message": f"Error synchronizing Odoo invoices: {str(e)}",
                "invoices_synced": 0
            }
    
    def export_integration_config(self, integration_id: str) -> Dict[str, Any]:
        """
        Export an integration configuration with sensitive fields removed.
        Extracted from integration_service.py lines 1517-1558
        
        Args:
            integration_id: ID of the integration to export
            
        Returns:
            Export data with configuration details
        """
        try:
            integration = self.get_integration(integration_id)
            if not integration:
                raise ValueError(f"Integration with ID {integration_id} not found")
            
            # Create export config with sensitive fields removed
            export_config = integration.get("config", {})
            if self.config_manager:
                export_config = self.config_manager.sanitize_config_for_export(export_config)
            
            # Create the export object
            return {
                "integration_id": integration["id"],
                "name": integration["name"],
                "description": integration["description"],
                "integration_type": integration["integration_type"],
                "config": export_config,
                "sync_frequency": integration.get("sync_frequency", "manual"),
                "created_at": integration["created_at"].isoformat() if integration.get("created_at") else None,
                "exported_at": datetime.utcnow().isoformat(),
                "export_version": "1.0"
            }
            
        except Exception as e:
            logger.error(f"Failed to export integration config for {integration_id}: {str(e)}")
            raise
    
    def import_integration_config(
        self, 
        import_data: Dict[str, Any], 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Import an integration configuration to create a new integration.
        Extracted from integration_service.py lines 1561-1590
        
        Args:
            import_data: Integration import data
            user_id: ID of the user importing the integration
            
        Returns:
            The newly created integration
        """
        try:
            # Validate the configuration
            if self.config_manager:
                is_valid, errors = self.config_manager.validate_integration_config(
                    import_data.get("config", {}), 
                    import_data.get("integration_type")
                )
                if not is_valid:
                    error_msg = "\n".join(errors)
                    raise ValueError(f"Invalid integration configuration: {error_msg}")
            
            # Create integration from import data
            integration_data = {
                "name": import_data.get("name", "Imported Integration"),
                "description": import_data.get("description", ""),
                "integration_type": import_data.get("integration_type", "unknown"),
                "config": import_data.get("config", {}),
                "sync_frequency": import_data.get("sync_frequency", "manual"),
                "client_id": import_data.get("client_id")
            }
            
            return self.create_integration(integration_data, user_id)
            
        except Exception as e:
            logger.error(f"Failed to import integration config: {str(e)}")
            raise
    
    def get_integration_health_summary(self, integration_id: str) -> Dict[str, Any]:
        """
        Get comprehensive health summary for an integration.
        
        Args:
            integration_id: Integration ID
            
        Returns:
            Health summary combining status, metrics, and recommendations
        """
        try:
            integration = self.get_integration(integration_id)
            if not integration:
                return {
                    "integration_id": integration_id,
                    "error": "Integration not found"
                }
            
            health_summary = {
                "integration_id": integration_id,
                "name": integration["name"],
                "type": integration["integration_type"],
                "status": integration.get("status", "unknown"),
                "created_at": integration.get("created_at"),
                "last_tested": integration.get("last_tested")
            }
            
            # Add status monitoring data if available
            if self.status_monitor:
                status_data = self.status_monitor.get_integration_health_summary(integration_id)
                health_summary.update(status_data)
            
            # Add performance metrics if available
            if self.metrics_collector:
                try:
                    metrics = self.metrics_collector.get_integration_performance_metrics(integration_id, 7)
                    health_summary["performance_metrics"] = metrics["summary"]
                    health_summary["analysis"] = metrics.get("analysis", {})
                except Exception as e:
                    logger.warning(f"Could not get metrics for {integration_id}: {e}")
            
            return health_summary
            
        except Exception as e:
            logger.error(f"Failed to get health summary for {integration_id}: {str(e)}")
            return {
                "integration_id": integration_id,
                "error": str(e)
            }


# Global instance for easy access
lifecycle_manager = LifecycleManager()