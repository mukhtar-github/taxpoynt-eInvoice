from typing import Dict, Any, List, Optional, Tuple # type: ignore
from uuid import UUID # type: ignore
from datetime import datetime
import requests # type: ignore
from requests.exceptions import RequestException, Timeout, ConnectionError # type: ignore
import json
import jsonschema # type: ignore
from jsonschema import validate, ValidationError # type: ignore
import logging
import time
from sqlalchemy.orm import Session # type: ignore
import threading
from datetime import datetime, timedelta

from app import crud
from app.schemas.integration import IntegrationCreate, IntegrationUpdate, Integration, IntegrationTestResult # type: ignore
from app.utils.encryption import encrypt_sensitive_value, decrypt_sensitive_value, get_app_encryption_key # type: ignore


# List of config fields that should be encrypted
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


def encrypt_sensitive_config_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Encrypt sensitive fields in integration configuration.
    
    Args:
        config: The integration configuration dictionary
        
    Returns:
        Updated configuration with sensitive fields encrypted
    """
    if not config:
        return config
        
    encryption_key = get_app_encryption_key()
    encrypted_config = config.copy()
    
    # Encrypt top-level sensitive fields
    for field in SENSITIVE_CONFIG_FIELDS:
        if field in encrypted_config and encrypted_config[field]:
            encrypted_config[field] = encrypt_sensitive_value(
                str(encrypted_config[field]), 
                encryption_key
            )
    
    # Check for nested objects that might contain sensitive fields
    for key, value in encrypted_config.items():
        if isinstance(value, dict):
            encrypted_config[key] = encrypt_sensitive_config_fields(value)
            
    return encrypted_config


def decrypt_sensitive_config_fields(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Decrypt sensitive fields in integration configuration.
    
    Args:
        config: The integration configuration dictionary with encrypted fields
        
    Returns:
        Configuration with sensitive fields decrypted
    """
    if not config:
        return config
        
    encryption_key = get_app_encryption_key()
    decrypted_config = config.copy()
    
    # Decrypt top-level sensitive fields
    for field in SENSITIVE_CONFIG_FIELDS:
        if field in decrypted_config and decrypted_config[field]:
            try:
                decrypted_config[field] = decrypt_sensitive_value(
                    decrypted_config[field], 
                    encryption_key
                )
            except Exception:
                # If decryption fails, it might not be encrypted yet
                pass
    
    # Check for nested objects that might contain sensitive fields
    for key, value in decrypted_config.items():
        if isinstance(value, dict):
            decrypted_config[key] = decrypt_sensitive_config_fields(value)
            
    return decrypted_config


def create_integration(
    db: Session, 
    obj_in: IntegrationCreate, 
    user_id: UUID
) -> Integration:
    """
    Create a new integration with encrypted sensitive config fields.
    
    Args:
        db: Database session
        obj_in: Integration creation schema
        user_id: ID of the user creating the integration
        
    Returns:
        Created integration object
    """
    # Encrypt sensitive fields in config
    if obj_in.config:
        encrypted_config = encrypt_sensitive_config_fields(obj_in.config)
        # Create a new object with the updated config
        obj_in_data = obj_in.dict()
        obj_in_data["config"] = encrypted_config
        obj_in_encrypted = IntegrationCreate(**obj_in_data)
        integration = crud.integration.create(db=db, obj_in=obj_in_encrypted, user_id=user_id)
    else:
        integration = crud.integration.create(db=db, obj_in=obj_in, user_id=user_id)
    
    # Return integration with decrypted config
    return decrypt_integration_config(integration)


def update_integration(
    db: Session,
    db_obj: Any,
    obj_in: IntegrationUpdate,
    user_id: UUID
) -> Integration:
    """
    Update an integration with encrypted sensitive config fields.
    
    Args:
        db: Database session
        db_obj: Existing integration object from database
        obj_in: Integration update schema
        user_id: ID of the user updating the integration
        
    Returns:
        Updated integration object
    """
    # If we're updating the config, encrypt sensitive fields
    update_data = obj_in.dict(exclude_unset=True)
    
    if "config" in update_data and update_data["config"]:
        update_data["config"] = encrypt_sensitive_config_fields(update_data["config"])
        obj_in_encrypted = IntegrationUpdate(**update_data)
        integration = crud.integration.update(db=db, db_obj=db_obj, obj_in=obj_in_encrypted, user_id=user_id)
    else:
        integration = crud.integration.update(db=db, db_obj=db_obj, obj_in=obj_in, user_id=user_id)
    
    # Return integration with decrypted config
    return decrypt_integration_config(integration)


def get_integration(
    db: Session,
    integration_id: UUID
) -> Optional[Integration]:
    """
    Get an integration by ID with decrypted config.
    
    Args:
        db: Database session
        integration_id: ID of the integration to retrieve
        
    Returns:
        Integration object with decrypted sensitive config fields
    """
    integration = crud.integration.get(db=db, integration_id=integration_id)
    if not integration:
        return None
        
    return decrypt_integration_config(integration)


def get_integrations(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Integration]:
    """
    Get multiple integrations with decrypted configs.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of integration objects with decrypted sensitive config fields
    """
    integrations = crud.integration.get_multi(db=db, skip=skip, limit=limit)
    return [decrypt_integration_config(integration) for integration in integrations]


def decrypt_integration_config(integration: Any) -> Any:
    """
    Decrypt sensitive fields in an integration's config.
    
    Args:
        integration: Integration object from database
        
    Returns:
        Integration with decrypted config
    """
    # Don't modify the original object
    integration_dict = {
        key: getattr(integration, key) 
        for key in integration.__dict__ 
        if not key.startswith('_')
    }
    
    if "config" in integration_dict and integration_dict["config"]:
        integration_dict["config"] = decrypt_sensitive_config_fields(integration_dict["config"])
        
    return Integration(**integration_dict)


def test_integration_connection(
    db: Session,
    integration_id: UUID
) -> IntegrationTestResult:
    """
    Test the connection for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to test
        
    Returns:
        Test result with success status, message, and details
    """
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        return IntegrationTestResult(
            success=False,
            message="Integration not found",
            details={"error": "integration_not_found"}
        )
    
    # Get the integration type from config
    integration_type = integration.config.get("type", "").lower()
    
    # Update last_tested timestamp
    now = datetime.utcnow()
    crud.integration.update(
        db=db, 
        db_obj=crud.integration.get(db=db, integration_id=integration_id),
        obj_in=IntegrationUpdate(last_tested=now),
        user_id=None
    )
    
    # Test based on integration type
    if integration_type == "rest_api":
        return _test_rest_api_connection(integration)
    elif integration_type == "soap":
        return _test_soap_connection(integration)
    elif integration_type == "database":
        return _test_database_connection(integration)
    elif integration_type == "file_system":
        return _test_file_system_connection(integration)
    elif integration_type == "erp":
        return _test_erp_connection(integration)
    else:
        return IntegrationTestResult(
            success=False,
            message=f"Unsupported integration type: {integration_type}",
            details={"error": "unsupported_type"}
        )

def _test_rest_api_connection(integration: Integration) -> IntegrationTestResult:
    """Test connection to a REST API endpoint."""
    config = integration.config
    
    # Get required parameters
    base_url = config.get("api_url")
    test_endpoint = config.get("test_endpoint", "")
    method = config.get("test_method", "GET").upper()
    headers = config.get("headers", {})
    timeout = config.get("timeout", 10)
    
    # Add authentication if provided
    if "api_key" in config and config["api_key"]:
        api_key = config["api_key"]
        auth_type = config.get("auth_type", "header").lower()
        
        if auth_type == "header":
            key_name = config.get("api_key_name", "X-API-Key")
            headers[key_name] = api_key
        elif auth_type == "query":
            key_name = config.get("api_key_name", "api_key")
            if "?" in test_endpoint:
                test_endpoint += f"&{key_name}={api_key}"
            else:
                test_endpoint += f"?{key_name}={api_key}"
        elif auth_type == "bearer":
            headers["Authorization"] = f"Bearer {api_key}"
    
    url = f"{base_url.rstrip('/')}/{test_endpoint.lstrip('/')}"
    
    try:
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            test_data = config.get("test_data", {})
            response = requests.post(url, json=test_data, headers=headers, timeout=timeout)
        else:
            return IntegrationTestResult(
                success=False,
                message=f"Unsupported test method: {method}",
                details={"error": "unsupported_method"}
            )
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        # Check if response is successful
        if response.status_code < 400:
            return IntegrationTestResult(
                success=True,
                message=f"Connection successful (HTTP {response.status_code})",
                details={
                    "status_code": response.status_code,
                    "latency_ms": elapsed_ms,
                    "response_size": len(response.content)
                }
            )
        else:
            return IntegrationTestResult(
                success=False,
                message=f"API returned error: HTTP {response.status_code}",
                details={
                    "status_code": response.status_code,
                    "latency_ms": elapsed_ms,
                    "error": "api_error"
                }
            )
    
    except Timeout:
        return IntegrationTestResult(
            success=False,
            message="Connection timed out",
            details={"error": "timeout"}
        )
    except ConnectionError:
        return IntegrationTestResult(
            success=False,
            message="Failed to connect to API",
            details={"error": "connection_error"}
        )
    except RequestException as e:
        return IntegrationTestResult(
            success=False,
            message=f"Request error: {str(e)}",
            details={"error": "request_error"}
        )
    except Exception as e:
        logging.error(f"Unexpected error testing REST API connection: {str(e)}")
        return IntegrationTestResult(
            success=False,
            message="Unexpected error during connection test",
            details={"error": "unexpected_error"}
        )

def _test_soap_connection(integration: Integration) -> IntegrationTestResult:
    """Test connection to a SOAP service."""
    # Placeholder for SOAP connection test
    # In a real implementation, this would use a SOAP client library
    return IntegrationTestResult(
        success=True,
        message="SOAP connection test successful (simulated)",
        details={"status": "connected", "latency_ms": 50}
    )

def _test_database_connection(integration: Integration) -> IntegrationTestResult:
    """Test connection to a database."""
    # Placeholder for database connection test
    # In a real implementation, this would use appropriate database drivers
    return IntegrationTestResult(
        success=True,
        message="Database connection test successful (simulated)",
        details={"status": "connected", "latency_ms": 30}
    )

def _test_file_system_connection(integration: Integration) -> IntegrationTestResult:
    """Test connection to a file system."""
    # Placeholder for file system connection test
    return IntegrationTestResult(
        success=True,
        message="File system connection test successful (simulated)",
        details={"status": "connected", "latency_ms": 15}
    )

def _test_erp_connection(integration: Integration) -> IntegrationTestResult:
    """Test connection to an ERP system."""
    # Placeholder for ERP system connection test
    return IntegrationTestResult(
        success=True,
        message="ERP connection test successful (simulated)",
        details={"status": "connected", "latency_ms": 75}
    )

# Integration templates for common systems
INTEGRATION_TEMPLATES = {
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
    "sage": {
        "name": "Sage",
        "description": "Integration with Sage accounting software",
        "config": {
            "type": "rest_api",
            "api_url": "https://api.accounting.sage.com/v3.1",
            "test_endpoint": "businesses",
            "test_method": "GET",
            "auth_type": "oauth2",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 30,
            "required_fields": ["client_id", "client_secret", "access_token", "refresh_token"],
            "endpoints": {
                "invoices": "/sales_invoices",
                "customers": "/contacts",
                "payments": "/payments"
            }
        }
    },
    "zoho_books": {
        "name": "Zoho Books",
        "description": "Integration with Zoho Books accounting software",
        "config": {
            "type": "rest_api",
            "api_url": "https://books.zoho.com/api/v3",
            "test_endpoint": "organizations",
            "test_method": "GET",
            "auth_type": "oauth2",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 30,
            "required_fields": ["client_id", "client_secret", "organization_id", "access_token", "refresh_token"],
            "endpoints": {
                "invoices": "/invoices",
                "customers": "/contacts",
                "payments": "/customerpayments"
            }
        }
    },
    "dynamics_365": {
        "name": "Microsoft Dynamics 365",
        "description": "Integration with Microsoft Dynamics 365 Business Central",
        "config": {
            "type": "rest_api",
            "api_url": "https://{tenant}.api.crm.dynamics.com/api/data/v9.2",
            "test_endpoint": "WhoAmI",
            "test_method": "GET",
            "auth_type": "oauth2",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 45,
            "required_fields": ["client_id", "client_secret", "tenant", "access_token", "refresh_token"],
            "endpoints": {
                "invoices": "/invoices",
                "accounts": "/accounts",
                "contacts": "/contacts"
            }
        }
    },
    "sap_business_one": {
        "name": "SAP Business One",
        "description": "Integration with SAP Business One ERP",
        "config": {
            "type": "soap",
            "service_url": "https://{server}:{port}/b1s/v1",
            "test_endpoint": "Login",
            "test_method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "timeout": 60,
            "required_fields": ["company_db", "username", "password", "server", "port"],
            "endpoints": {
                "invoices": "/Invoices",
                "customers": "/BusinessPartners",
                "items": "/Items"
            }
        }
    },
    "oracle_netsuite": {
        "name": "Oracle NetSuite",
        "description": "Integration with Oracle NetSuite ERP",
        "config": {
            "type": "rest_api",
            "api_url": "https://{account_id}.suitetalk.api.netsuite.com/services/rest/record/v1",
            "test_endpoint": "company/{company_id}",
            "test_method": "GET",
            "auth_type": "oauth1",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 45,
            "required_fields": ["account_id", "consumer_key", "consumer_secret", "token", "token_secret", "company_id"],
            "endpoints": {
                "invoices": "/invoice",
                "customers": "/customer",
                "items": "/item"
            }
        }
    },
    "odoo": {
        "name": "Odoo",
        "description": "Integration with Odoo ERP",
        "config": {
            "type": "rest_api",
            "api_url": "https://{database}.odoo.com/api",
            "test_endpoint": "/version",
            "test_method": "GET",
            "auth_type": "basic",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 30,
            "required_fields": ["database", "api_key", "username"],
            "endpoints": {
                "invoices": "/account.invoice",
                "partners": "/res.partner",
                "products": "/product.product"
            }
        }
    },
    "custom_rest_api": {
        "name": "Custom REST API",
        "description": "Generic template for custom REST API integration",
        "config": {
            "type": "rest_api",
            "api_url": "",
            "test_endpoint": "",
            "test_method": "GET",
            "auth_type": "none",
            "headers": {
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            "timeout": 30,
            "required_fields": ["api_url", "test_endpoint"],
            "endpoints": {
                "invoices": "",
                "customers": "",
                "payments": ""
            }
        }
    }
}

def get_integration_templates() -> Dict[str, Any]:
    """
    Get all available integration templates.
    
    Returns:
        Dictionary of integration templates
    """
    return INTEGRATION_TEMPLATES

def get_integration_template(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific integration template by ID.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Template configuration or None if not found
    """
    return INTEGRATION_TEMPLATES.get(template_id)

def create_integration_from_template(
    db: Session, 
    template_id: str, 
    client_id: UUID,
    user_id: UUID,
    config_values: Dict[str, Any] = None
) -> Optional[Integration]:
    """
    Create a new integration based on a template.
    
    Args:
        db: Database session
        template_id: Template identifier
        client_id: Client ID to associate with the integration
        user_id: User ID creating the integration
        config_values: Values to fill in the template
        
    Returns:
        Created integration or None if template not found
    """
    template = get_integration_template(template_id)
    if not template:
        return None
    
    # Create a copy of the template config
    config = template["config"].copy()
    
    # Update with provided values
    if config_values:
        for key, value in config_values.items():
            if key in config:
                config[key] = value
    
    # Create integration
    integration_in = IntegrationCreate(
        name=template["name"],
        description=template["description"],
        client_id=client_id,
        config=config
    )
    
    return create_integration(db, integration_in, user_id)

def validate_integration_config(
    config: Dict[str, Any], 
    integration_type: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate integration configuration against schema and business rules.
    
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
            "type": {"type": "string", "enum": ["rest_api", "soap", "database", "file_system", "erp"]},
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
        errors.extend(_validate_rest_api_config(config))
    elif integration_type == "soap":
        errors.extend(_validate_soap_config(config))
    elif integration_type == "database":
        errors.extend(_validate_database_config(config))
    elif integration_type == "file_system":
        errors.extend(_validate_file_system_config(config))
    elif integration_type == "erp":
        errors.extend(_validate_erp_config(config))
    
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
        "token", "token_secret", "company_id", "company_db"
    ]
    
    for field in config:
        if field not in known_fields and not field.startswith("custom_"):
            errors.append(f"Unknown configuration field: '{field}'")
    
    return len(errors) == 0, errors

def _validate_rest_api_config(config: Dict[str, Any]) -> List[str]:
    """Validate REST API configuration."""
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

def _validate_soap_config(config: Dict[str, Any]) -> List[str]:
    """Validate SOAP configuration."""
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

def _validate_database_config(config: Dict[str, Any]) -> List[str]:
    """Validate database configuration."""
    errors = []
    
    # Required fields for database connection
    for field in ["database", "server"]:
        if field not in config or not config[field]:
            errors.append(f"Database connection requires '{field}'")
    
    # Must have either username/password or api_key
    if ("username" not in config or not config["username"]) and ("api_key" not in config or not config["api_key"]):
        errors.append("Database connection requires either 'username'/'password' or 'api_key'")
    
    return errors

def _validate_file_system_config(config: Dict[str, Any]) -> List[str]:
    """Validate file system configuration."""
    errors = []
    
    # Placeholder for file system validation
    if "server" not in config or not config["server"]:
        errors.append("File system connection requires 'server'")
    
    return errors

def _validate_erp_config(config: Dict[str, Any]) -> List[str]:
    """Validate ERP configuration."""
    errors = []
    
    # Placeholder for ERP system validation
    for field in ["server", "username"]:
        if field not in config or not config["field"]:
            errors.append(f"ERP connection requires '{field}'")
    
    return errors

def validate_and_create_integration(
    db: Session, 
    obj_in: IntegrationCreate, 
    user_id: UUID
) -> Tuple[bool, List[str], Optional[Integration]]:
    """
    Validate and create a new integration.
    
    Args:
        db: Database session
        obj_in: Integration creation schema
        user_id: ID of the user creating the integration
        
    Returns:
        Tuple of (success, errors, created_integration)
    """
    # Validate the configuration
    is_valid, errors = validate_integration_config(obj_in.config)
    
    if not is_valid:
        return False, errors, None
    
    # If valid, create the integration
    integration = create_integration(db, obj_in, user_id)
    return True, [], integration 

# Global dictionary to track integration status monitoring
_monitoring_threads = {}
_status_cache = {}

def get_integration_status(
    db: Session, 
    integration_id: UUID
) -> Dict[str, Any]:
    """
    Get the current status of an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration
        
    Returns:
        Dictionary with status information
    """
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        return {
            "status": "unknown",
            "last_checked": None,
            "message": "Integration not found"
        }
    
    # Get status from cache if available
    status_info = _status_cache.get(str(integration_id))
    
    if not status_info:
        # If not in cache, create basic status info
        status_info = {
            "status": integration.status,
            "last_checked": integration.last_tested,
            "message": "Status has not been checked yet",
            "details": {}
        }
        _status_cache[str(integration_id)] = status_info
    
    return status_info

def start_integration_monitoring(
    db: Session,
    integration_id: UUID,
    interval_minutes: int = 30
) -> bool:
    """
    Start background monitoring for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to monitor
        interval_minutes: Interval between checks in minutes
        
    Returns:
        True if monitoring started, False otherwise
    """
    integration = get_integration(db=db, integration_id=integration_id)
    if not integration:
        return False
    
    # Don't start a new thread if already monitoring
    str_id = str(integration_id)
    if str_id in _monitoring_threads and _monitoring_threads[str_id].is_alive():
        return True
    
    # Create and start monitoring thread
    monitor_thread = threading.Thread(
        target=_monitor_integration,
        args=(db, integration_id, interval_minutes),
        daemon=True
    )
    monitor_thread.start()
    
    _monitoring_threads[str_id] = monitor_thread
    
    # Update integration status
    update_integration(
        db=db,
        db_obj=integration,
        obj_in=IntegrationUpdate(status="monitoring"),
        user_id=None
    )
    
    return True

def stop_integration_monitoring(
    db: Session,
    integration_id: UUID
) -> bool:
    """
    Stop background monitoring for an integration.
    
    Args:
        db: Database session
        integration_id: ID of the integration to stop monitoring
        
    Returns:
        True if monitoring stopped, False otherwise
    """
    str_id = str(integration_id)
    
    # Check if monitoring thread exists
    if str_id not in _monitoring_threads:
        return False
    
    # Thread will terminate on its own (daemon)
    _monitoring_threads.pop(str_id, None)
    
    # Get the integration
    integration = get_integration(db=db, integration_id=integration_id)
    if integration:
        # Update status to paused
        update_integration(
            db=db,
            db_obj=integration,
            obj_in=IntegrationUpdate(status="paused"),
            user_id=None
        )
    
    return True

def get_all_monitored_integrations(db: Session) -> List[Dict[str, Any]]:
    """
    Get a list of all integrations being monitored.
    
    Args:
        db: Database session
        
    Returns:
        List of integration monitoring status dictionaries
    """
    result = []
    
    for integration_id in _monitoring_threads:
        thread = _monitoring_threads[integration_id]
        status = _status_cache.get(integration_id, {})
        
        # Only include active monitoring threads
        if thread.is_alive():
            integration = get_integration(db=db, integration_id=UUID(integration_id))
            if integration:
                result.append({
                    "integration_id": integration_id,
                    "name": integration.name,
                    "status": status.get("status", "unknown"),
                    "last_checked": status.get("last_checked"),
                    "message": status.get("message", ""),
                    "is_monitoring": True
                })
    
    return result

def _monitor_integration(db_session, integration_id: UUID, interval_minutes: int):
    """
    Background task to periodically check integration status.
    
    Args:
        db_session: SQLAlchemy session factory
        integration_id: ID of the integration to monitor
        interval_minutes: Interval between checks in minutes
    """
    str_id = str(integration_id)
    
    while str_id in _monitoring_threads:
        try:
            # Create new session for this thread
            db = db_session()
            
            # Test the integration
            result = test_integration_connection(db=db, integration_id=integration_id)
            
            # Update status cache
            _status_cache[str_id] = {
                "status": "active" if result.success else "failed",
                "last_checked": datetime.utcnow(),
                "message": result.message,
                "details": result.details or {}
            }
            
            # Update integration status in database
            integration = get_integration(db=db, integration_id=integration_id)
            if integration:
                update_integration(
                    db=db,
                    db_obj=integration,
                    obj_in=IntegrationUpdate(
                        status="active" if result.success else "failed"
                    ),
                    user_id=None
                )
            
            # Close session
            db.close()
            
            # Sleep until next check
            time.sleep(interval_minutes * 60)
            
        except Exception as e:
            logging.error(f"Error monitoring integration {integration_id}: {str(e)}")
            
            # Update status cache with error
            _status_cache[str_id] = {
                "status": "error",
                "last_checked": datetime.utcnow(),
                "message": f"Monitoring error: {str(e)}",
                "details": {"error": "monitoring_error"}
            }
            
            # Sleep before retry
            time.sleep(300)  # 5 minutes 