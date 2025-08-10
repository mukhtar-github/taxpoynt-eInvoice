"""
System Integrator (SI) API Documentation Generator
=================================================
Generates comprehensive API documentation specifically for System Integrator role users.
Focuses on ERP/CRM integration, data transformation, and pre-submission services.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

from core_platform.authentication.role_manager import PlatformRole


class SIAPIDocumentationGenerator:
    """Generates role-specific documentation for System Integrator users."""
    
    def __init__(self):
        self.role = PlatformRole.SYSTEM_INTEGRATOR
        self.title = "TaxPoynt System Integrator API"
        self.description = """
        ## TaxPoynt System Integrator API Documentation
        
        Welcome to the TaxPoynt System Integrator API documentation. This API enables you to:
        
        - **Integrate Business Systems**: Connect your ERP, CRM, and POS systems with TaxPoynt
        - **Transform Data**: Convert business system data to e-invoice standards
        - **Manage Certificates**: Handle digital certificates for secure transactions
        - **Validate Compliance**: Ensure data meets regulatory requirements
        - **Generate Documents**: Create compliant e-invoices and supporting documents
        
        ### Target Users
        - Software developers integrating business systems
        - System administrators configuring ERP connections
        - Compliance officers ensuring data accuracy
        - Technical consultants implementing e-invoicing solutions
        """
        
        self.si_endpoints = self._define_si_endpoints()
        self.si_schemas = self._define_si_schemas()
        self.integration_examples = self._define_integration_examples()
    
    def _define_si_endpoints(self) -> Dict[str, Any]:
        """Define SI-specific API endpoints."""
        return {
            "financial_systems": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/payments/available-processors",
                        "method": "GET",
                        "summary": "Get available payment processors",
                        "description": "List all payment processors available for integration: Nigerian (Paystack, Moniepoint, OPay, PalmPay, Interswitch), African (Flutterwave), Global (Stripe)",
                        "tags": ["Financial Systems"],
                        "response": {
                            "type": "object",
                            "properties": {
                                "payment_processors": {
                                    "type": "object",
                                    "properties": {
                                        "nigerian": {
                                            "type": "object",
                                            "properties": {
                                                "processors": {"type": "array", "items": {"type": "string"}},
                                                "description": {"type": "string"},
                                                "features": {"type": "array"}
                                            }
                                        },
                                        "african": {"type": "object"},
                                        "global": {"type": "object"}
                                    }
                                },
                                "totals": {
                                    "type": "object",
                                    "properties": {
                                        "nigerian_processors": {"type": "integer"},
                                        "african_processors": {"type": "integer"},
                                        "global_processors": {"type": "integer"},
                                        "total_processors": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/payments/connections",
                        "method": "GET",
                        "summary": "List all payment processor connections",
                        "description": "Get all payment processor connections configured for your organization",
                        "tags": ["Financial Systems"]
                    },
                    {
                        "path": "/api/v1/si/payments/connections/summary",
                        "method": "GET",
                        "summary": "Get payment connections summary",
                        "description": "Get aggregated statistics of all payment processor connections",
                        "tags": ["Financial Systems"]
                    },
                    {
                        "path": "/api/v1/si/payments/nigerian/{processor}/connections",
                        "method": "POST",
                        "summary": "Create Nigerian payment processor connection",
                        "description": "Create connection to Nigerian payment processors (Paystack, Moniepoint, OPay, PalmPay, Interswitch)",
                        "tags": ["Financial Systems"],
                        "parameters": [
                            {"name": "processor", "in": "path", "required": True, "type": "string", "enum": ["paystack", "moniepoint", "opay", "palmpay", "interswitch"]}
                        ],
                        "request_body": {
                            "type": "object",
                            "required": ["organization_id", "connection_config"],
                            "properties": {
                                "organization_id": {"type": "string"},
                                "connection_config": {
                                    "type": "object",
                                    "properties": {
                                        "api_key": {"type": "string"},
                                        "secret_key": {"type": "string"},
                                        "environment": {"type": "string", "enum": ["sandbox", "production"]},
                                        "webhook_url": {"type": "string"}
                                    }
                                },
                                "enabled_features": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/payments/african/{processor}/connections",
                        "method": "POST",
                        "summary": "Create African payment processor connection",
                        "description": "Create connection to African payment processors (Flutterwave for 34+ countries)",
                        "tags": ["Financial Systems"],
                        "parameters": [
                            {"name": "processor", "in": "path", "required": True, "type": "string", "enum": ["flutterwave"]}
                        ]
                    },
                    {
                        "path": "/api/v1/si/payments/global/{processor}/connections",
                        "method": "POST",
                        "summary": "Create Global payment processor connection",
                        "description": "Create connection to global payment processors (Stripe for international transactions)",
                        "tags": ["Financial Systems"],
                        "parameters": [
                            {"name": "processor", "in": "path", "required": True, "type": "string", "enum": ["stripe"]}
                        ]
                    },
                    {
                        "path": "/api/v1/si/payments/unified/transactions",
                        "method": "GET",
                        "summary": "Get unified payment transactions",
                        "description": "Retrieve transactions from all connected payment processors in a unified format",
                        "tags": ["Financial Systems"],
                        "parameters": [
                            {"name": "start_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "end_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "processor", "in": "query", "type": "string"}
                        ]
                    },
                    {
                        "path": "/api/v1/si/payments/unified/summary",
                        "method": "GET",
                        "summary": "Get unified payment summary",
                        "description": "Get aggregated payment statistics across all connected processors",
                        "tags": ["Financial Systems"],
                        "parameters": [
                            {"name": "period", "in": "query", "type": "string", "default": "30d"}
                        ]
                    },
                    {
                        "path": "/api/v1/si/payments/transactions/process",
                        "method": "POST",
                        "summary": "Process payment transactions for e-invoicing",
                        "description": "Process transactions from payment processors to generate compliant e-invoices",
                        "tags": ["Financial Systems"],
                        "request_body": {
                            "type": "object",
                            "required": ["processor", "transaction_ids"],
                            "properties": {
                                "processor": {"type": "string"},
                                "transaction_ids": {"type": "array", "items": {"type": "string"}},
                                "invoice_template": {"type": "string"},
                                "auto_submit": {"type": "boolean", "default": False}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/payments/transactions/bulk-import",
                        "method": "POST",
                        "summary": "Bulk import payment transactions",
                        "description": "Import large volumes of transactions from payment processors",
                        "tags": ["Financial Systems"]
                    },
                    {
                        "path": "/api/v1/si/payments/webhooks/register",
                        "method": "POST",
                        "summary": "Register payment processor webhooks",
                        "description": "Register webhook endpoints to receive real-time payment notifications",
                        "tags": ["Financial Systems"],
                        "request_body": {
                            "type": "object",
                            "required": ["processor", "webhook_url", "events"],
                            "properties": {
                                "processor": {"type": "string"},
                                "webhook_url": {"type": "string", "format": "uri"},
                                "events": {"type": "array", "items": {"type": "string"}},
                                "secret": {"type": "string"}
                            }
                        }
                    }
                ]
            },
            "erp_integration": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/erp/connectors",
                        "method": "GET",
                        "summary": "List available ERP connectors",
                        "description": "Retrieve list of supported ERP systems and their integration capabilities",
                        "tags": ["ERP Integration"],
                        "response": {
                            "type": "object",
                            "properties": {
                                "connectors": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "version": {"type": "string"},
                                            "capabilities": {"type": "array"},
                                            "authentication_methods": {"type": "array"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/erp/connections",
                        "method": "POST",
                        "summary": "Create new ERP connection",
                        "description": "Establish connection to an ERP system for data extraction",
                        "tags": ["ERP Integration"],
                        "request_body": {
                            "type": "object",
                            "required": ["erp_type", "connection_config"],
                            "properties": {
                                "erp_type": {"type": "string", "enum": ["odoo", "sap", "dynamics", "netsuite"]},
                                "connection_config": {"type": "object"},
                                "credentials": {"type": "object"},
                                "sync_schedule": {"type": "string"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/erp/connections/{connection_id}/sync",
                        "method": "POST",
                        "summary": "Trigger data synchronization",
                        "description": "Manually trigger data sync from ERP system",
                        "tags": ["ERP Integration"],
                        "parameters": [
                            {"name": "connection_id", "in": "path", "required": True, "type": "string"}
                        ]
                    }
                ]
            },
            "data_transformation": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/transformation/mappings",
                        "method": "GET",
                        "summary": "Get field mapping configurations",
                        "description": "Retrieve data transformation mappings for ERP-to-e-invoice conversion",
                        "tags": ["Data Transformation"]
                    },
                    {
                        "path": "/api/v1/si/transformation/mappings",
                        "method": "POST",
                        "summary": "Create field mapping",
                        "description": "Create custom field mapping for data transformation",
                        "tags": ["Data Transformation"],
                        "request_body": {
                            "type": "object",
                            "required": ["source_field", "target_field", "transformation_rule"],
                            "properties": {
                                "source_field": {"type": "string"},
                                "target_field": {"type": "string"},
                                "transformation_rule": {"type": "object"},
                                "validation_rules": {"type": "array"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/transformation/validate",
                        "method": "POST",
                        "summary": "Validate transformed data",
                        "description": "Validate data after transformation but before submission",
                        "tags": ["Data Transformation"]
                    }
                ]
            },
            "certificate_management": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/certificates",
                        "method": "GET",
                        "summary": "List digital certificates",
                        "description": "Retrieve all digital certificates associated with the organization",
                        "tags": ["Certificate Management"]
                    },
                    {
                        "path": "/api/v1/si/certificates/upload",
                        "method": "POST",
                        "summary": "Upload digital certificate",
                        "description": "Upload a digital certificate for document signing",
                        "tags": ["Certificate Management"],
                        "request_body": {
                            "type": "object",
                            "required": ["certificate_file", "private_key", "password"],
                            "properties": {
                                "certificate_file": {"type": "string", "format": "binary"},
                                "private_key": {"type": "string", "format": "binary"},
                                "password": {"type": "string"},
                                "certificate_name": {"type": "string"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/certificates/{cert_id}/validate",
                        "method": "GET",
                        "summary": "Validate certificate status",
                        "description": "Check certificate validity and expiration status",
                        "tags": ["Certificate Management"]
                    }
                ]
            },
            "document_processing": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/documents/generate",
                        "method": "POST",
                        "summary": "Generate e-invoice document",
                        "description": "Generate compliant e-invoice from business data",
                        "tags": ["Document Processing"],
                        "request_body": {
                            "type": "object",
                            "required": ["invoice_data", "document_type"],
                            "properties": {
                                "invoice_data": {"type": "object"},
                                "document_type": {"type": "string", "enum": ["ubl", "pdf", "both"]},
                                "certificate_id": {"type": "string"},
                                "template_id": {"type": "string"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/documents/templates",
                        "method": "GET",
                        "summary": "List document templates",
                        "description": "Retrieve available document templates for invoice generation",
                        "tags": ["Document Processing"]
                    },
                    {
                        "path": "/api/v1/si/documents/{document_id}/preview",
                        "method": "GET",
                        "summary": "Preview generated document",
                        "description": "Preview document before final generation",
                        "tags": ["Document Processing"]
                    }
                ]
            },
            "irn_qr_generation": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/irn/generate",
                        "method": "POST",
                        "summary": "Generate Invoice Reference Number",
                        "description": "Generate IRN for invoice before submission to FIRS",
                        "tags": ["IRN/QR Generation"],
                        "request_body": {
                            "type": "object",
                            "required": ["invoice_data"],
                            "properties": {
                                "invoice_data": {"type": "object"},
                                "sequence_type": {"type": "string"},
                                "custom_prefix": {"type": "string"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/si/qr/generate",
                        "method": "POST",
                        "summary": "Generate QR code for invoice",
                        "description": "Generate QR code containing invoice verification data",
                        "tags": ["IRN/QR Generation"]
                    },
                    {
                        "path": "/api/v1/si/irn/validate",
                        "method": "POST",
                        "summary": "Validate IRN format",
                        "description": "Validate IRN format and uniqueness",
                        "tags": ["IRN/QR Generation"]
                    }
                ]
            },
            "validation_compliance": {
                "endpoints": [
                    {
                        "path": "/api/v1/si/validation/schemas",
                        "method": "GET",
                        "summary": "Get validation schemas",
                        "description": "Retrieve current UBL and regulatory validation schemas",
                        "tags": ["Validation & Compliance"]
                    },
                    {
                        "path": "/api/v1/si/validation/business-rules",
                        "method": "GET",
                        "summary": "Get business validation rules",
                        "description": "Retrieve business rules for invoice validation",
                        "tags": ["Validation & Compliance"]
                    },
                    {
                        "path": "/api/v1/si/validation/validate-invoice",
                        "method": "POST",
                        "summary": "Validate invoice data",
                        "description": "Comprehensive validation of invoice data against all rules",
                        "tags": ["Validation & Compliance"]
                    }
                ]
            }
        }
    
    def _define_si_schemas(self) -> Dict[str, Any]:
        """Define SI-specific data schemas."""
        return {
            "PaymentProcessorConnection": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "processor": {"type": "string", "enum": ["paystack", "moniepoint", "opay", "palmpay", "interswitch", "flutterwave", "stripe"]},
                    "region": {"type": "string", "enum": ["nigerian", "african", "global"]},
                    "organization_id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "inactive", "error", "pending"]},
                    "environment": {"type": "string", "enum": ["sandbox", "production"]},
                    "created_at": {"type": "string", "format": "date-time"},
                    "last_sync": {"type": "string", "format": "date-time"},
                    "transactions_synced": {"type": "integer"},
                    "features_enabled": {"type": "array", "items": {"type": "string"}},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "connection_health": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "last_check": {"type": "string", "format": "date-time"},
                            "response_time_ms": {"type": "number"},
                            "error_count": {"type": "integer"}
                        }
                    }
                }
            },
            "PaymentTransaction": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "processor": {"type": "string"},
                    "processor_transaction_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "success", "failed", "cancelled"]},
                    "customer_email": {"type": "string", "format": "email"},
                    "customer_name": {"type": "string"},
                    "transaction_date": {"type": "string", "format": "date-time"},
                    "reference": {"type": "string"},
                    "description": {"type": "string"},
                    "fees": {"type": "number"},
                    "metadata": {"type": "object"},
                    "invoice_generated": {"type": "boolean"},
                    "invoice_id": {"type": "string"},
                    "business_classification": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string"},
                            "subcategory": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                }
            },
            "UnifiedPaymentSummary": {
                "type": "object",
                "properties": {
                    "period": {"type": "string"},
                    "total_transactions": {"type": "integer"},
                    "total_amount": {"type": "number"},
                    "currency": {"type": "string"},
                    "successful_transactions": {"type": "integer"},
                    "failed_transactions": {"type": "integer"},
                    "average_transaction_amount": {"type": "number"},
                    "processor_breakdown": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "transaction_count": {"type": "integer"},
                                "total_amount": {"type": "number"},
                                "success_rate": {"type": "number"}
                            }
                        }
                    },
                    "daily_breakdown": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string", "format": "date"},
                                "transaction_count": {"type": "integer"},
                                "total_amount": {"type": "number"}
                            }
                        }
                    }
                }
            },
            "PaymentWebhook": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "processor": {"type": "string"},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "events": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string", "enum": ["active", "inactive", "error"]},
                    "secret": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "last_delivery": {"type": "string", "format": "date-time"},
                    "delivery_count": {"type": "integer"},
                    "success_count": {"type": "integer"},
                    "failure_count": {"type": "integer"}
                }
            },
            "ERPConnection": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "erp_type": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["active", "inactive", "error"]},
                    "last_sync": {"type": "string", "format": "date-time"},
                    "sync_schedule": {"type": "string"},
                    "records_synced": {"type": "integer"},
                    "connection_config": {"type": "object"}
                }
            },
            "TransformationMapping": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "source_field": {"type": "string"},
                    "target_field": {"type": "string"},
                    "transformation_type": {"type": "string"},
                    "transformation_rule": {"type": "object"},
                    "validation_rules": {"type": "array"},
                    "is_required": {"type": "boolean"}
                }
            },
            "DigitalCertificate": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "subject": {"type": "string"},
                    "issuer": {"type": "string"},
                    "valid_from": {"type": "string", "format": "date"},
                    "valid_to": {"type": "string", "format": "date"},
                    "status": {"type": "string", "enum": ["valid", "expired", "revoked"]},
                    "key_usage": {"type": "array"},
                    "thumbprint": {"type": "string"}
                }
            },
            "InvoiceDocument": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "irn": {"type": "string"},
                    "document_type": {"type": "string"},
                    "status": {"type": "string"},
                    "generated_at": {"type": "string", "format": "date-time"},
                    "file_url": {"type": "string"},
                    "file_hash": {"type": "string"},
                    "certificate_used": {"type": "string"}
                }
            },
            "ValidationResult": {
                "type": "object",
                "properties": {
                    "is_valid": {"type": "boolean"},
                    "errors": {"type": "array"},
                    "warnings": {"type": "array"},
                    "validation_timestamp": {"type": "string", "format": "date-time"},
                    "schema_version": {"type": "string"}
                }
            }
        }
    
    def _define_integration_examples(self) -> Dict[str, Any]:
        """Define integration examples and code samples."""
        return {
            "payment_processor_connection_example": {
                "title": "Setting up Paystack Payment Processor Connection",
                "description": "Example of connecting to Paystack for transaction data collection",
                "code": """
# Python SDK Example
from taxpoynt_si_sdk import TaxPoyntSIClient

client = TaxPoyntSIClient(api_key="your_api_key")

# Create Paystack connection
paystack_config = {
    "organization_id": "org_123456",
    "connection_config": {
        "api_key": "pk_test_your_paystack_public_key",
        "secret_key": "sk_test_your_paystack_secret_key",
        "environment": "sandbox",  # or "production"
        "webhook_url": "https://your-app.com/webhooks/paystack"
    },
    "enabled_features": ["transaction_data", "customer_data", "webhook_data"]
}

connection = client.payments.nigerian.paystack.create_connection(paystack_config)
print(f"Paystack connection created: {connection.id}")

# Test the connection
test_result = client.payments.test_connection(connection.id)
print(f"Connection test: {test_result.status}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/si/payments/nigerian/paystack/connections" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "organization_id": "org_123456",
    "connection_config": {
      "api_key": "pk_test_your_paystack_public_key",
      "secret_key": "sk_test_your_paystack_secret_key",
      "environment": "sandbox",
      "webhook_url": "https://your-app.com/webhooks/paystack"
    },
    "enabled_features": ["transaction_data", "customer_data", "webhook_data"]
  }'
                """
            },
            "unified_transactions_example": {
                "title": "Retrieving Unified Payment Transactions",
                "description": "Example of getting transactions from all connected payment processors",
                "code": """
# Get transactions from all processors
transactions = client.payments.unified.get_transactions(
    start_date="2024-01-01",
    end_date="2024-01-31",
    processor=None  # Get from all processors
)

# Process transactions for e-invoicing
for transaction in transactions.data:
    if transaction.status == "success" and not transaction.invoice_generated:
        # Generate e-invoice from transaction
        invoice = client.documents.generate(
            invoice_data={
                "customer_name": transaction.customer_name,
                "customer_email": transaction.customer_email,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "transaction_reference": transaction.reference,
                "business_classification": transaction.business_classification
            },
            document_type="both",  # UBL and PDF
            template_id="default_payment_invoice"
        )
        print(f"Invoice generated: {invoice.id} for transaction: {transaction.id}")
                """,
                "curl_example": """
curl -X GET "https://api.taxpoynt.com/api/v1/si/payments/unified/transactions?start_date=2024-01-01&end_date=2024-01-31" \\
  -H "Authorization: Bearer YOUR_API_KEY"
                """
            },
            "payment_webhook_example": {
                "title": "Registering Payment Processor Webhooks",
                "description": "Example of setting up webhooks for real-time payment notifications",
                "code": """
# Register webhooks for multiple processors
webhook_configs = [
    {
        "processor": "paystack",
        "webhook_url": "https://your-app.com/webhooks/paystack",
        "events": ["charge.success", "transfer.success", "subscription.create"],
        "secret": "your_webhook_secret"
    },
    {
        "processor": "flutterwave",
        "webhook_url": "https://your-app.com/webhooks/flutterwave",
        "events": ["charge.completed", "transfer.completed"],
        "secret": "your_webhook_secret"
    }
]

for config in webhook_configs:
    webhook = client.payments.webhooks.register(config)
    print(f"Webhook registered for {config['processor']}: {webhook.id}")

# List all registered webhooks
webhooks = client.payments.webhooks.list()
for webhook in webhooks.data:
    print(f"Webhook: {webhook.processor} - Status: {webhook.status}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/si/payments/webhooks/register" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "processor": "paystack",
    "webhook_url": "https://your-app.com/webhooks/paystack",
    "events": ["charge.success", "transfer.success"],
    "secret": "your_webhook_secret"
  }'
                """
            },
            "erp_connection_example": {
                "title": "Setting up Odoo ERP Connection",
                "description": "Example of connecting to an Odoo ERP system",
                "code": """
# Python SDK Example
from taxpoynt_si_sdk import TaxPoyntSIClient

client = TaxPoyntSIClient(api_key="your_api_key")

# Create ERP connection
connection_config = {
    "erp_type": "odoo",
    "connection_config": {
        "url": "https://your-odoo.com",
        "database": "your_database",
        "username": "your_username",
        "api_key": "your_odoo_api_key"
    },
    "sync_schedule": "0 */6 * * *",  # Every 6 hours
    "enabled_modules": ["account", "sale", "purchase"]
}

connection = client.erp.create_connection(connection_config)
print(f"Connection created: {connection.id}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/si/erp/connections" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "erp_type": "odoo",
    "connection_config": {
      "url": "https://your-odoo.com",
      "database": "your_database"
    },
    "sync_schedule": "0 */6 * * *"
  }'
                """
            },
            "data_transformation_example": {
                "title": "Creating Custom Field Mapping",
                "description": "Example of mapping ERP fields to e-invoice standards",
                "code": """
# Create field mapping for customer information
mapping_config = {
    "source_field": "partner_id.name",
    "target_field": "AccountingCustomerParty.Party.PartyName.Name",
    "transformation_rule": {
        "type": "direct_mapping",
        "validation": {
            "required": True,
            "max_length": 100
        }
    }
}

mapping = client.transformation.create_mapping(mapping_config)
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/si/transformation/mappings" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "source_field": "partner_id.name",
    "target_field": "AccountingCustomerParty.Party.PartyName.Name",
    "transformation_rule": {
      "type": "direct_mapping"
    }
  }'
                """
            },
            "certificate_upload_example": {
                "title": "Uploading Digital Certificate",
                "description": "Example of uploading a digital certificate for document signing",
                "code": """
# Upload certificate for document signing
with open("certificate.p12", "rb") as cert_file:
    certificate = client.certificates.upload(
        certificate_file=cert_file,
        password="certificate_password",
        name="Company Signing Certificate"
    )

print(f"Certificate uploaded: {certificate.id}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/si/certificates/upload" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -F "certificate_file=@certificate.p12" \\
  -F "password=your_password" \\
  -F "certificate_name=Company Certificate"
                """
            }
        }
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification for SI endpoints."""
        openapi_spec = {
            "openapi": "3.0.2",
            "info": {
                "title": self.title,
                "description": self.description,
                "version": "1.0.0",
                "contact": {
                    "name": "TaxPoynt SI Support",
                    "email": "info@taxpoynt.com",
                    "url": "https://docs.taxpoynt.com/si"
                }
            },
            "servers": [
                {"url": "https://api.taxpoynt.com", "description": "Production"},
                {"url": "https://sandbox-api.taxpoynt.com", "description": "Sandbox"}
            ],
            "paths": {},
            "components": {
                "schemas": self.si_schemas,
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    },
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            },
            "security": [
                {"ApiKeyAuth": []},
                {"BearerAuth": []}
            ],
            "tags": [
                {"name": "Financial Systems", "description": "Payment processor integration operations (Nigerian, African, Global)"},
                {"name": "ERP Integration", "description": "ERP system integration operations"},
                {"name": "Data Transformation", "description": "Data mapping and transformation"},
                {"name": "Certificate Management", "description": "Digital certificate operations"},
                {"name": "Document Processing", "description": "Document generation and processing"},
                {"name": "IRN/QR Generation", "description": "Invoice reference and QR code generation"},
                {"name": "Validation & Compliance", "description": "Data validation and compliance checking"}
            ]
        }
        
        # Add all SI endpoints to the OpenAPI spec
        for category, endpoints_data in self.si_endpoints.items():
            for endpoint in endpoints_data["endpoints"]:
                path = endpoint["path"]
                method = endpoint["method"].lower()
                
                if path not in openapi_spec["paths"]:
                    openapi_spec["paths"][path] = {}
                
                operation = {
                    "summary": endpoint["summary"],
                    "description": endpoint.get("description", ""),
                    "tags": endpoint.get("tags", []),
                    "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": endpoint.get("response", {"type": "object"})
                                }
                            }
                        },
                        "400": {"description": "Bad Request"},
                        "401": {"description": "Unauthorized"},
                        "403": {"description": "Forbidden"},
                        "500": {"description": "Internal Server Error"}
                    }
                }
                
                # Add request body if present
                if "request_body" in endpoint:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": endpoint["request_body"]
                            }
                        }
                    }
                
                # Add parameters if present
                if "parameters" in endpoint:
                    operation["parameters"] = endpoint["parameters"]
                
                openapi_spec["paths"][path][method] = operation
        
        return openapi_spec
    
    def generate_html_documentation(self) -> str:
        """Generate HTML documentation for SI APIs."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; }}
        .header {{ background: #1f2937; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }}
        .endpoint {{ background: #f9fafb; padding: 15px; margin: 10px 0; border-radius: 6px; }}
        .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: white; }}
        .get {{ background: #10b981; }}
        .post {{ background: #3b82f6; }}
        .put {{ background: #f59e0b; }}
        .delete {{ background: #ef4444; }}
        .code {{ background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 6px; overflow-x: auto; }}
        .example {{ margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Comprehensive API documentation for System Integrator role</p>
    </div>
    
    <div class="section">
        <h2>Overview</h2>
        {description}
    </div>
    
    <div class="section">
        <h2>Authentication</h2>
        <p>All API requests require authentication using either:</p>
        <ul>
            <li><strong>API Key:</strong> Include <code>X-API-Key</code> header</li>
            <li><strong>JWT Token:</strong> Include <code>Authorization: Bearer &lt;token&gt;</code> header</li>
        </ul>
    </div>
    
    {endpoints_html}
    
    <div class="section">
        <h2>Integration Examples</h2>
        {examples_html}
    </div>
    
    <div class="section">
        <h2>Support</h2>
        <p>For SI API support, contact:</p>
        <ul>
            <li>Email: info@taxpoynt.com</li>
            <li>Documentation: https://docs.taxpoynt.com/si</li>
            <li>Community: https://community.taxpoynt.com</li>
        </ul>
    </div>
</body>
</html>
        """
        
        # Generate endpoints HTML
        endpoints_html = ""
        for category, endpoints_data in self.si_endpoints.items():
            endpoints_html += f'<div class="section"><h2>{category.replace("_", " ").title()}</h2>'
            
            for endpoint in endpoints_data["endpoints"]:
                method_class = endpoint["method"].lower()
                endpoints_html += f'''
                <div class="endpoint">
                    <span class="method {method_class}">{endpoint["method"]}</span>
                    <strong>{endpoint["path"]}</strong>
                    <p>{endpoint["summary"]}</p>
                    <p><em>{endpoint.get("description", "")}</em></p>
                </div>
                '''
            
            endpoints_html += "</div>"
        
        # Generate examples HTML
        examples_html = ""
        for example_key, example_data in self.integration_examples.items():
            examples_html += f'''
            <div class="example">
                <h3>{example_data["title"]}</h3>
                <p>{example_data["description"]}</p>
                <h4>Python SDK:</h4>
                <pre class="code">{example_data["code"]}</pre>
                <h4>cURL:</h4>
                <pre class="code">{example_data["curl_example"]}</pre>
            </div>
            '''
        
        return html_template.format(
            title=self.title,
            description=self.description.replace('\n', '<br>'),
            endpoints_html=endpoints_html,
            examples_html=examples_html
        )
    
    def export_documentation(self, output_dir: str) -> Dict[str, str]:
        """Export documentation in multiple formats."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Export OpenAPI spec
        openapi_spec = self.generate_openapi_spec()
        openapi_file = output_path / "si_api_openapi.json"
        with open(openapi_file, "w") as f:
            json.dump(openapi_spec, f, indent=2)
        files_created["openapi"] = str(openapi_file)
        
        # Export HTML documentation
        html_doc = self.generate_html_documentation()
        html_file = output_path / "si_api_documentation.html"
        with open(html_file, "w") as f:
            f.write(html_doc)
        files_created["html"] = str(html_file)
        
        # Export integration examples
        examples_file = output_path / "si_integration_examples.json"
        with open(examples_file, "w") as f:
            json.dump(self.integration_examples, f, indent=2)
        files_created["examples"] = str(examples_file)
        
        return files_created


def generate_si_api_docs(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate complete SI API documentation."""
    generator = SIAPIDocumentationGenerator()
    
    if output_dir:
        files = generator.export_documentation(output_dir)
        return {
            "status": "success",
            "files_created": files,
            "openapi_spec": generator.generate_openapi_spec()
        }
    
    return {
        "status": "success",
        "openapi_spec": generator.generate_openapi_spec(),
        "html_documentation": generator.generate_html_documentation(),
        "integration_examples": generator.integration_examples
    }


# Export main functionality
__all__ = [
    "SIAPIDocumentationGenerator",
    "generate_si_api_docs"
]