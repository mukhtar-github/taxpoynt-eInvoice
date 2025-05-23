"""
Odoo Integration Templates

This module provides templates and configuration options for Odoo integrations,
with specific support for Odoo 18+ and e-Invoicing capabilities.
"""
from typing import Dict, Any, List, Optional


# Standard Odoo 18+ Template with basic authentication
ODOO_18_TEMPLATE = {
    "name": "Odoo 18+ Standard",
    "description": "Standard template for Odoo 18+ ERP systems",
    "template_id": "odoo18_standard",
    "integration_type": "odoo",
    "config_schema": {
        "type": "object",
        "required": ["url", "database", "username", "auth_method"],
        "properties": {
            "url": {
                "type": "string",
                "format": "uri",
                "title": "Odoo Server URL",
                "description": "The base URL of your Odoo server (e.g., https://your-odoo-instance.com)"
            },
            "database": {
                "type": "string",
                "title": "Database Name",
                "description": "The name of your Odoo database"
            },
            "username": {
                "type": "string",
                "title": "Username",
                "description": "Username for authentication"
            },
            "auth_method": {
                "type": "string",
                "enum": ["password", "api_key"],
                "title": "Authentication Method",
                "description": "Choose whether to authenticate with a password or API key"
            },
            "password": {
                "type": "string",
                "format": "password",
                "title": "Password",
                "description": "Password for authentication (required if auth_method is 'password')"
            },
            "api_key": {
                "type": "string",
                "format": "password",
                "title": "API Key",
                "description": "API key for authentication (required if auth_method is 'api_key')"
            },
            "company_id": {
                "type": "integer",
                "title": "Company ID",
                "description": "The ID of the company in Odoo (optional, defaults to user's current company)"
            },
            "timeout": {
                "type": "integer",
                "title": "Connection Timeout",
                "description": "Connection timeout in seconds",
                "default": 30
            }
        },
        "dependencies": {
            "auth_method": {
                "oneOf": [
                    {
                        "properties": {
                            "auth_method": {"enum": ["password"]},
                            "password": {"type": "string"}
                        },
                        "required": ["password"]
                    },
                    {
                        "properties": {
                            "auth_method": {"enum": ["api_key"]},
                            "api_key": {"type": "string"}
                        },
                        "required": ["api_key"]
                    }
                ]
            }
        }
    },
    "ui_schema": {
        "auth_method": {
            "ui:widget": "radio"
        },
        "password": {
            "ui:widget": "password"
        },
        "api_key": {
            "ui:widget": "password"
        }
    },
    "default_values": {
        "auth_method": "password",
        "timeout": 30
    }
}


# Odoo 18+ template with e-Invoicing support
ODOO_18_EINVOICE_TEMPLATE = {
    "name": "Odoo 18+ E-Invoicing",
    "description": "Template for Odoo 18+ with E-Invoicing modules configured",
    "template_id": "odoo18_einvoice",
    "integration_type": "odoo",
    "config_schema": {
        "type": "object",
        "required": ["url", "database", "username", "auth_method", "einvoice_settings"],
        "properties": {
            "url": {
                "type": "string",
                "format": "uri",
                "title": "Odoo Server URL",
                "description": "The base URL of your Odoo server (e.g., https://your-odoo-instance.com)"
            },
            "database": {
                "type": "string",
                "title": "Database Name",
                "description": "The name of your Odoo database"
            },
            "username": {
                "type": "string",
                "title": "Username",
                "description": "Username for authentication"
            },
            "auth_method": {
                "type": "string",
                "enum": ["password", "api_key"],
                "title": "Authentication Method",
                "description": "Choose whether to authenticate with a password or API key"
            },
            "password": {
                "type": "string",
                "format": "password",
                "title": "Password",
                "description": "Password for authentication (required if auth_method is 'password')"
            },
            "api_key": {
                "type": "string",
                "format": "password",
                "title": "API Key",
                "description": "API key for authentication (required if auth_method is 'api_key')"
            },
            "company_id": {
                "type": "integer",
                "title": "Company ID",
                "description": "The ID of the company in Odoo (optional, defaults to user's current company)"
            },
            "timeout": {
                "type": "integer",
                "title": "Connection Timeout",
                "description": "Connection timeout in seconds",
                "default": 30
            },
            "einvoice_settings": {
                "type": "object",
                "title": "E-Invoicing Settings",
                "required": ["auto_submit", "sync_interval", "invoice_types"],
                "properties": {
                    "auto_submit": {
                        "type": "boolean",
                        "title": "Auto-Submit E-Invoices",
                        "description": "Automatically submit e-invoices to tax authority",
                        "default": False
                    },
                    "sync_interval": {
                        "type": "string",
                        "enum": ["realtime", "hourly", "daily"],
                        "title": "Synchronization Interval",
                        "description": "How frequently to sync invoices",
                        "default": "hourly"
                    },
                    "invoice_types": {
                        "type": "array",
                        "title": "Invoice Types",
                        "description": "Types of invoices to sync",
                        "items": {
                            "type": "string",
                            "enum": ["out_invoice", "out_refund"]
                        },
                        "default": ["out_invoice"]
                    },
                    "irn_field": {
                        "type": "string",
                        "title": "IRN Field Name",
                        "description": "Custom field in Odoo for storing IRN numbers",
                        "default": "l10n_ng_irn"
                    }
                }
            }
        },
        "dependencies": {
            "auth_method": {
                "oneOf": [
                    {
                        "properties": {
                            "auth_method": {"enum": ["password"]},
                            "password": {"type": "string"}
                        },
                        "required": ["password"]
                    },
                    {
                        "properties": {
                            "auth_method": {"enum": ["api_key"]},
                            "api_key": {"type": "string"}
                        },
                        "required": ["api_key"]
                    }
                ]
            }
        }
    },
    "ui_schema": {
        "auth_method": {
            "ui:widget": "radio"
        },
        "password": {
            "ui:widget": "password"
        },
        "api_key": {
            "ui:widget": "password"
        },
        "einvoice_settings": {
            "ui:object": "collapsible"
        }
    },
    "default_values": {
        "auth_method": "password",
        "timeout": 30,
        "einvoice_settings": {
            "auto_submit": False,
            "sync_interval": "hourly",
            "invoice_types": ["out_invoice"],
            "irn_field": "l10n_ng_irn"
        }
    }
}


# Odoo 18+ REST API integration template
ODOO_18_REST_API_TEMPLATE = {
    "name": "Odoo 18+ REST API",
    "description": "Template for Odoo 18+ using the REST API interface",
    "template_id": "odoo18_rest_api",
    "integration_type": "odoo",
    "config_schema": {
        "type": "object",
        "required": ["url", "api_key"],
        "properties": {
            "url": {
                "type": "string",
                "format": "uri",
                "title": "Odoo REST API URL",
                "description": "The base URL of your Odoo REST API (e.g., https://your-odoo-instance.com/api/v1)"
            },
            "api_key": {
                "type": "string",
                "format": "password",
                "title": "API Key",
                "description": "REST API key for authentication"
            },
            "api_secret": {
                "type": "string",
                "format": "password",
                "title": "API Secret",
                "description": "REST API secret (if required by your Odoo REST API implementation)"
            },
            "company_id": {
                "type": "integer",
                "title": "Company ID",
                "description": "The ID of the company in Odoo"
            },
            "timeout": {
                "type": "integer",
                "title": "Connection Timeout",
                "description": "Connection timeout in seconds",
                "default": 30
            },
            "einvoice_settings": {
                "type": "object",
                "title": "E-Invoicing Settings",
                "required": ["auto_submit", "sync_interval", "invoice_types"],
                "properties": {
                    "auto_submit": {
                        "type": "boolean",
                        "title": "Auto-Submit E-Invoices",
                        "description": "Automatically submit e-invoices to tax authority",
                        "default": False
                    },
                    "sync_interval": {
                        "type": "string",
                        "enum": ["realtime", "hourly", "daily"],
                        "title": "Synchronization Interval",
                        "description": "How frequently to sync invoices",
                        "default": "hourly"
                    },
                    "invoice_types": {
                        "type": "array",
                        "title": "Invoice Types",
                        "description": "Types of invoices to sync",
                        "items": {
                            "type": "string",
                            "enum": ["out_invoice", "out_refund"]
                        },
                        "default": ["out_invoice"]
                    },
                    "irn_field": {
                        "type": "string",
                        "title": "IRN Field Name",
                        "description": "Custom field in Odoo for storing IRN numbers",
                        "default": "l10n_ng_irn"
                    }
                }
            }
        }
    },
    "ui_schema": {
        "api_key": {
            "ui:widget": "password"
        },
        "api_secret": {
            "ui:widget": "password"
        },
        "einvoice_settings": {
            "ui:object": "collapsible"
        }
    },
    "default_values": {
        "timeout": 30,
        "einvoice_settings": {
            "auto_submit": False,
            "sync_interval": "hourly",
            "invoice_types": ["out_invoice"],
            "irn_field": "l10n_ng_irn"
        }
    }
}


# Collection of all available Odoo templates
ODOO_TEMPLATES = {
    "odoo18_standard": ODOO_18_TEMPLATE,
    "odoo18_einvoice": ODOO_18_EINVOICE_TEMPLATE,
    "odoo18_rest_api": ODOO_18_REST_API_TEMPLATE
}


def get_odoo_templates() -> Dict[str, Any]:
    """
    Get all available Odoo integration templates.
    
    Returns:
        Dictionary of Odoo integration templates
    """
    return ODOO_TEMPLATES


def get_odoo_template(template_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific Odoo integration template by ID.
    
    Args:
        template_id: Template identifier
        
    Returns:
        Template configuration or None if not found
    """
    return ODOO_TEMPLATES.get(template_id)


def validate_odoo_config(config: Dict[str, Any], major_version: int = 18) -> List[str]:
    """
    Validate Odoo configuration against schema and business rules.
    
    Args:
        config: The Odoo configuration to validate
        major_version: Odoo major version (defaults to 18)
        
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Basic validation
    if not config.get("url"):
        errors.append("URL is required")
    
    # Authentication validation
    auth_method = config.get("auth_method")
    if auth_method == "password":
        if not config.get("password"):
            errors.append("Password is required when using password authentication")
    elif auth_method == "api_key":
        if not config.get("api_key"):
            errors.append("API key is required when using API key authentication")
    
    # For REST API configuration
    if config.get("url", "").endswith("/api") or config.get("url", "").endswith("/api/v1"):
        if not config.get("api_key"):
            errors.append("API key is required for REST API integration")
    
    # Odoo 18+ specific validation
    if major_version >= 18:
        # Check e-invoice settings if present
        if "einvoice_settings" in config:
            einvoice_settings = config.get("einvoice_settings", {})
            
            # Validate sync interval
            sync_interval = einvoice_settings.get("sync_interval")
            if sync_interval and sync_interval not in ["realtime", "hourly", "daily"]:
                errors.append(f"Invalid sync interval: {sync_interval}")
            
            # Validate invoice types
            invoice_types = einvoice_settings.get("invoice_types", [])
            valid_types = ["out_invoice", "out_refund"]
            for inv_type in invoice_types:
                if inv_type not in valid_types:
                    errors.append(f"Invalid invoice type: {inv_type}")
    
    return errors
