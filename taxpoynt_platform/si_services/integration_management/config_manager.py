"""
Integration Configuration Manager

Handles configuration encryption, validation, and template management for integrations.
Extracted from integration_service.py - provides granular configuration management.
"""

from typing import Dict, Any, List, Optional, Tuple
import json
import jsonschema
from jsonschema import validate, ValidationError

# Note: These imports would need to be adapted for the new platform structure
# from app.utils.encryption import encrypt_sensitive_value, decrypt_sensitive_value, get_app_encryption_key
# from app.models.integration import IntegrationType


class ConfigManager:
    """Manages integration configuration encryption, validation, and templates"""
    
    # List of config fields that should be encrypted (extracted from integration_service.py)
    SENSITIVE_CONFIG_FIELDS = [
        "api_key", 
        "client_secret", 
        "secret_key", 
        "password", 
        "token",
        "auth_token",
        "access_token",
        "refresh_token",
        "private_key"
    ]
    
    def __init__(self):
        self.integration_templates = self._load_integration_templates()
    
    def encrypt_sensitive_config_fields(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt sensitive fields in integration configuration.
        Extracted from integration_service.py lines 35-64
        
        Args:
            config: The integration configuration dictionary
            
        Returns:
            Updated configuration with sensitive fields encrypted
        """
        if not config:
            return config
            
        # TODO: Adapt encryption for new platform
        # encryption_key = get_app_encryption_key()
        encrypted_config = config.copy()
        
        # Encrypt top-level sensitive fields
        for field in self.SENSITIVE_CONFIG_FIELDS:
            if field in encrypted_config and encrypted_config[field]:
                # TODO: Replace with platform-specific encryption
                # encrypted_config[field] = encrypt_sensitive_value(
                #     str(encrypted_config[field]), 
                #     encryption_key
                # )
                # For now, mark as encrypted
                encrypted_config[field] = f"ENCRYPTED:{encrypted_config[field]}"
        
        # Check for nested objects that might contain sensitive fields
        for key, value in encrypted_config.items():
            if isinstance(value, dict):
                encrypted_config[key] = self.encrypt_sensitive_config_fields(value)
                
        return encrypted_config

    def decrypt_sensitive_config_fields(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Decrypt sensitive fields in integration configuration.
        Extracted from integration_service.py lines 67-100
        
        Args:
            config: The integration configuration dictionary with encrypted fields
            
        Returns:
            Configuration with sensitive fields decrypted
        """
        if not config:
            return config
            
        # TODO: Adapt decryption for new platform
        # encryption_key = get_app_encryption_key()
        decrypted_config = config.copy()
        
        # Decrypt top-level sensitive fields
        for field in self.SENSITIVE_CONFIG_FIELDS:
            if field in decrypted_config and decrypted_config[field]:
                try:
                    # TODO: Replace with platform-specific decryption
                    # decrypted_config[field] = decrypt_sensitive_value(
                    #     decrypted_config[field], 
                    #     encryption_key
                    # )
                    # For now, handle mock encrypted values
                    if str(decrypted_config[field]).startswith("ENCRYPTED:"):
                        decrypted_config[field] = str(decrypted_config[field]).replace("ENCRYPTED:", "")
                except Exception:
                    # If decryption fails, it might not be encrypted yet
                    pass
        
        # Check for nested objects that might contain sensitive fields
        for key, value in decrypted_config.items():
            if isinstance(value, dict):
                decrypted_config[key] = self.decrypt_sensitive_config_fields(value)
                
        return decrypted_config

    def validate_integration_config(
        self, 
        config: Dict[str, Any], 
        integration_type: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Validate integration configuration against schema and business rules.
        Extracted from integration_service.py lines 1024-1101
        
        Args:
            config: The integration configuration to validate
            integration_type: Type of integration to validate against
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Basic validation - check if config is empty
        if not config:
            return False, ["Configuration cannot be empty"]
        
        # Determine integration type from config if not provided
        if not integration_type and "type" in config:
            integration_type = config.get("type", "").lower()
        
        # Define general schema that applies to all integration types
        general_schema = {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {"type": "string", "enum": ["rest_api", "soap", "database", "file_system", "erp", "odoo"]},
                "timeout": {"type": "number", "minimum": 1, "maximum": 300}
            }
        }
        
        # Try to validate against general schema
        try:
            validate(instance=config, schema=general_schema)
        except ValidationError as e:
            errors.append(f"General validation error: {e.message}")
        
        # Specific validation based on integration type
        if integration_type == "rest_api":
            errors.extend(self._validate_rest_api_config(config))
        elif integration_type == "soap":
            errors.extend(self._validate_soap_config(config))
        elif integration_type == "database":
            errors.extend(self._validate_database_config(config))
        elif integration_type == "file_system":
            errors.extend(self._validate_file_system_config(config))
        elif integration_type == "erp":
            errors.extend(self._validate_erp_config(config))
        elif integration_type == "odoo":
            errors.extend(self._validate_odoo_config(config))
        
        # Check for required fields based on config
        required_fields = config.get("required_fields", [])
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"Required field '{field}' is missing or empty")
        
        # Check for any unexpected top-level fields
        known_fields = [
            "type", "api_url", "service_url", "test_endpoint", "test_method", 
            "auth_type", "headers", "timeout", "required_fields", "endpoints",
            "database", "server", "port", "username", "password", "api_key",
            "client_id", "client_secret", "access_token", "refresh_token",
            "tenant_id", "organization_id", "account_id", "realm_id",
            "test_data", "api_key_name", "consumer_key", "consumer_secret",
            "token", "token_secret", "company_id", "company_db",
            "url", "auth_method", "version", "rpc_path", "sync_frequency",
            "invoice_filters", "field_mappings"
        ]
        
        for field in config:
            if field not in known_fields and not field.startswith("custom_"):
                errors.append(f"Unknown configuration field: '{field}'")
        
        return len(errors) == 0, errors

    def _validate_rest_api_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate REST API configuration. Extracted from integration_service.py lines 1104-1155"""
        errors = []
        
        # Schema for REST API
        rest_schema = {
            "type": "object",
            "required": ["api_url"],
            "properties": {
                "api_url": {"type": "string", "minLength": 1},
                "test_endpoint": {"type": "string"},
                "test_method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"]},
                "auth_type": {"type": "string", "enum": ["none", "basic", "header", "query", "bearer", "oauth1", "oauth2"]},
                "headers": {"type": "object"},
                "test_data": {"type": "object"}
            }
        }
        
        try:
            validate(instance=config, schema=rest_schema)
        except ValidationError as e:
            errors.append(f"REST API validation error: {e.message}")
        
        # Check if URL is valid
        api_url = config.get("api_url", "")
        if api_url and not (api_url.startswith("http://") or api_url.startswith("https://")):
            errors.append("API URL must start with http:// or https://")
        
        # Additional auth-specific validation
        auth_type = config.get("auth_type", "").lower()
        
        if auth_type == "basic":
            if "username" not in config or not config["username"]:
                errors.append("Basic auth requires 'username'")
            if "password" not in config and "api_key" not in config:
                errors.append("Basic auth requires either 'password' or 'api_key'")
        
        elif auth_type == "oauth1":
            for field in ["consumer_key", "consumer_secret", "token", "token_secret"]:
                if field not in config or not config[field]:
                    errors.append(f"OAuth1 requires '{field}'")
        
        elif auth_type == "oauth2":
            for field in ["client_id", "client_secret", "access_token"]:
                if field not in config or not config[field]:
                    errors.append(f"OAuth2 requires '{field}'")
        
        elif auth_type == "bearer" or auth_type == "header":
            if "api_key" not in config or not config["api_key"]:
                errors.append(f"{auth_type.capitalize()} auth requires 'api_key'")
        
        return errors

    def _validate_soap_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate SOAP configuration. Extracted from integration_service.py lines 1158-1183"""
        errors = []
        
        # Schema for SOAP
        soap_schema = {
            "type": "object",
            "required": ["service_url"],
            "properties": {
                "service_url": {"type": "string", "minLength": 1},
                "test_endpoint": {"type": "string"},
                "headers": {"type": "object"}
            }
        }
        
        try:
            validate(instance=config, schema=soap_schema)
        except ValidationError as e:
            errors.append(f"SOAP validation error: {e.message}")
        
        # Check if URL is valid
        service_url = config.get("service_url", "")
        if service_url and not (service_url.startswith("http://") or service_url.startswith("https://")):
            errors.append("Service URL must start with http:// or https://")
        
        return errors

    def _validate_database_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate database configuration. Extracted from integration_service.py lines 1186-1199"""
        errors = []
        
        # Required fields for database connection
        for field in ["database", "server"]:
            if field not in config or not config[field]:
                errors.append(f"Database connection requires '{field}'")
        
        # Must have either username/password or api_key
        if ("username" not in config or not config["username"]) and ("api_key" not in config or not config["api_key"]):
            errors.append("Database connection requires either 'username'/'password' or 'api_key'")
        
        return errors

    def _validate_file_system_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate file system configuration. Extracted from integration_service.py lines 1202-1210"""
        errors = []
        
        if "server" not in config or not config["server"]:
            errors.append("File system connection requires 'server'")
        
        return errors

    def _validate_erp_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate ERP configuration. Extracted from integration_service.py lines 1213-1222"""
        errors = []
        
        for field in ["server", "username"]:
            if field not in config or not config[field]:
                errors.append(f"ERP connection requires '{field}'")
        
        return errors

    def _validate_odoo_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate Odoo configuration. Extracted from integration_service.py lines 1225-1238"""
        errors = []
        
        # Required fields for Odoo connection
        for field in ["url", "database", "username", "auth_method"]:
            if field not in config or not config[field]:
                errors.append(f"Odoo connection requires '{field}'")
        
        # Must have either api_key or password
        if ("api_key" not in config or not config["api_key"]) and ("password" not in config or not config["password"]):
            errors.append("Odoo connection requires either 'api_key' or 'password'")
        
        return errors

    def get_integration_templates(self) -> Dict[str, Any]:
        """
        Get all available integration templates.
        Extracted from integration_service.py lines 957-964
        
        Returns:
            Dictionary of integration templates
        """
        return self.integration_templates

    def get_integration_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific integration template by ID.
        Extracted from integration_service.py lines 967-977
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template configuration or None if not found
        """
        return self.integration_templates.get(template_id)

    def create_config_from_template(self, template_id: str, config_values: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Create configuration from template with provided values.
        Extracted from integration_service.py lines 980-1021
        
        Args:
            template_id: Template identifier
            config_values: Values to fill in the template
            
        Returns:
            Complete configuration or None if template not found
        """
        template = self.get_integration_template(template_id)
        if not template:
            return None
        
        # Create a copy of the template config
        config = template["config"].copy()
        
        # Update with provided values
        if config_values:
            for key, value in config_values.items():
                if key in config:
                    config[key] = value
        
        return config

    def sanitize_config_for_export(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive fields from configuration for export.
        Extracted from integration_service.py lines 1517-1558
        
        Args:
            config: Configuration to sanitize
            
        Returns:
            Configuration with sensitive fields replaced with placeholders
        """
        if not config:
            return config
        
        # Create a copy of the config to modify
        export_config = config.copy()
        
        # Remove sensitive fields from the export
        for field in self.SENSITIVE_CONFIG_FIELDS:
            if field in export_config:
                # Replace with a placeholder to indicate this needs to be provided again
                export_config[field] = "<REQUIRES_INPUT>"
            
            # Also check for nested fields
            for key in list(export_config.keys()):
                if isinstance(export_config[key], dict) and field in export_config[key]:
                    export_config[key][field] = "<REQUIRES_INPUT>"
        
        return export_config

    def _load_integration_templates(self) -> Dict[str, Any]:
        """
        Load predefined integration templates.
        Extracted from integration_service.py lines 748-953
        """
        return {
            "quickbooks_online": {
                "name": "QuickBooks Online",
                "description": "Integration with QuickBooks Online for invoice and customer data",
                "config": {
                    "type": "rest_api",
                    "api_url": "https://quickbooks.api.intuit.com/v3",
                    "test_endpoint": "company/{realm_id}/companyinfo/{realm_id}",
                    "test_method": "GET",
                    "auth_type": "oauth2",
                    "headers": {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    "timeout": 30,
                    "required_fields": ["client_id", "client_secret", "realm_id", "access_token", "refresh_token"],
                    "endpoints": {
                        "invoices": "/company/{realm_id}/invoice",
                        "customers": "/company/{realm_id}/customer",
                        "payments": "/company/{realm_id}/payment"
                    }
                }
            },
            "xero": {
                "name": "Xero",
                "description": "Integration with Xero accounting software",
                "config": {
                    "type": "rest_api",
                    "api_url": "https://api.xero.com/api.xro/2.0",
                    "test_endpoint": "Organisation",
                    "test_method": "GET",
                    "auth_type": "oauth2",
                    "headers": {
                        "Accept": "application/json",
                        "Content-Type": "application/json"
                    },
                    "timeout": 30,
                    "required_fields": ["client_id", "client_secret", "tenant_id", "access_token", "refresh_token"],
                    "endpoints": {
                        "invoices": "/Invoices",
                        "contacts": "/Contacts",
                        "payments": "/Payments"
                    }
                }
            },
            "odoo": {
                "name": "Odoo",
                "description": "Integration with Odoo ERP for invoice and customer data using JSON-RPC",
                "config": {
                    "type": "odoo",
                    "url": "https://example.odoo.com",
                    "database": "your_odoo_database",
                    "username": "your_odoo_username",
                    "auth_method": "api_key",
                    "api_key": "",
                    "password": "",
                    "version": "16.0",
                    "rpc_path": "/jsonrpc",
                    "timeout": 30,
                    "sync_frequency": "hourly",
                    "invoice_filters": {
                        "include_draft": False,
                        "include_posted": True,
                        "from_days_ago": 30,
                        "batch_size": 100
                    },
                    "field_mappings": {
                        "invoice_number": "name",
                        "invoice_date": "invoice_date",
                        "partner_name": "partner_id.name",
                        "partner_vat": "partner_id.vat",
                        "total_amount": "amount_total",
                        "tax_amount": "amount_tax"
                    }
                }
            }
            # Note: Additional templates available in integration_service_legacy.py lines 748-953
        }


# Global instance for easy access
config_manager = ConfigManager()