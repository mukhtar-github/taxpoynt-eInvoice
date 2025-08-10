"""
Access Point Provider (APP) API Documentation Generator
======================================================
Generates comprehensive API documentation specifically for Access Point Provider role users.
Focuses on FIRS submission, status management, and compliance reporting services.
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


class APPAPIDocumentationGenerator:
    """Generates role-specific documentation for Access Point Provider users."""
    
    def __init__(self):
        self.role = PlatformRole.ACCESS_POINT_PROVIDER
        self.title = "TaxPoynt Access Point Provider API"
        self.description = """
        ## TaxPoynt Access Point Provider API Documentation
        
        Welcome to the TaxPoynt Access Point Provider API documentation. This API enables you to:
        
        - **FIRS Integration**: Submit e-invoices directly to FIRS for compliance
        - **Status Management**: Track submission status and handle acknowledgments
        - **Secure Transmission**: Manage secure transmission protocols and certificates
        - **Taxpayer Services**: Onboard and manage taxpayer organizations
        - **Compliance Reporting**: Generate regulatory compliance reports and metrics
        - **Webhook Management**: Handle real-time FIRS notifications and updates
        
        ### Target Users
        - Compliance officers managing FIRS submissions
        - Tax consultants handling multiple organizations
        - Business administrators requiring e-invoicing services
        - Software vendors providing tax compliance solutions
        
        ### TaxPoynt as Your APP
        TaxPoynt acts as your certified Access Point Provider, handling all technical complexities
        of FIRS integration while you focus on your business operations.
        """
        
        self.app_endpoints = self._define_app_endpoints()
        self.app_schemas = self._define_app_schemas()
        self.integration_examples = self._define_integration_examples()
    
    def _define_app_endpoints(self) -> Dict[str, Any]:
        """Define APP-specific API endpoints."""
        return {
            "firs_integration": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/firs/submit",
                        "method": "POST",
                        "summary": "Submit e-invoice to FIRS",
                        "description": "Submit validated e-invoice documents directly to FIRS through TaxPoynt APP service",
                        "tags": ["FIRS Integration"],
                        "request_body": {
                            "type": "object",
                            "required": ["invoice_data", "taxpayer_tin"],
                            "properties": {
                                "invoice_data": {
                                    "type": "object",
                                    "description": "UBL-compliant invoice data"
                                },
                                "taxpayer_tin": {"type": "string"},
                                "submission_mode": {"type": "string", "enum": ["single", "batch"], "default": "single"},
                                "certificate_id": {"type": "string"},
                                "auto_retry": {"type": "boolean", "default": True}
                            }
                        },
                        "response": {
                            "type": "object",
                            "properties": {
                                "submission_id": {"type": "string"},
                                "firs_reference": {"type": "string"},
                                "status": {"type": "string"},
                                "submission_timestamp": {"type": "string", "format": "date-time"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/firs/batch-submit",
                        "method": "POST",
                        "summary": "Submit multiple e-invoices to FIRS",
                        "description": "Submit multiple e-invoices in a single batch to FIRS",
                        "tags": ["FIRS Integration"],
                        "request_body": {
                            "type": "object",
                            "required": ["invoices", "taxpayer_tin"],
                            "properties": {
                                "invoices": {
                                    "type": "array",
                                    "items": {"type": "object"},
                                    "maxItems": 100
                                },
                                "taxpayer_tin": {"type": "string"},
                                "batch_name": {"type": "string"},
                                "certificate_id": {"type": "string"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/firs/status/{submission_id}",
                        "method": "GET",
                        "summary": "Get FIRS submission status",
                        "description": "Retrieve current status of e-invoice submission to FIRS",
                        "tags": ["FIRS Integration"],
                        "parameters": [
                            {"name": "submission_id", "in": "path", "required": True, "type": "string"}
                        ],
                        "response": {
                            "type": "object",
                            "properties": {
                                "submission_id": {"type": "string"},
                                "firs_reference": {"type": "string"},
                                "status": {"type": "string", "enum": ["pending", "processing", "accepted", "rejected", "failed"]},
                                "firs_response": {"type": "object"},
                                "error_details": {"type": "array"},
                                "last_updated": {"type": "string", "format": "date-time"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/firs/acknowledgments",
                        "method": "GET",
                        "summary": "Get FIRS acknowledgments",
                        "description": "Retrieve acknowledgments and responses from FIRS for submitted invoices",
                        "tags": ["FIRS Integration"],
                        "parameters": [
                            {"name": "taxpayer_tin", "in": "query", "type": "string"},
                            {"name": "start_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "end_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "status", "in": "query", "type": "string"}
                        ]
                    },
                    {
                        "path": "/api/v1/app/firs/resubmit/{submission_id}",
                        "method": "POST",
                        "summary": "Resubmit failed invoice to FIRS",
                        "description": "Resubmit a previously failed or rejected invoice to FIRS after corrections",
                        "tags": ["FIRS Integration"],
                        "parameters": [
                            {"name": "submission_id", "in": "path", "required": True, "type": "string"}
                        ],
                        "request_body": {
                            "type": "object",
                            "properties": {
                                "corrected_invoice_data": {"type": "object"},
                                "correction_notes": {"type": "string"}
                            }
                        }
                    }
                ]
            },
            "transmission_management": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/transmission/secure-channels",
                        "method": "GET",
                        "summary": "List secure transmission channels",
                        "description": "Get available secure transmission channels to FIRS",
                        "tags": ["Transmission Management"]
                    },
                    {
                        "path": "/api/v1/app/transmission/certificates",
                        "method": "GET",
                        "summary": "List transmission certificates",
                        "description": "Get digital certificates used for secure transmission to FIRS",
                        "tags": ["Transmission Management"]
                    },
                    {
                        "path": "/api/v1/app/transmission/test-connection",
                        "method": "POST",
                        "summary": "Test FIRS connection",
                        "description": "Test connectivity and authentication with FIRS systems",
                        "tags": ["Transmission Management"],
                        "request_body": {
                            "type": "object",
                            "properties": {
                                "certificate_id": {"type": "string"},
                                "test_type": {"type": "string", "enum": ["basic", "full"], "default": "basic"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/transmission/queue",
                        "method": "GET",
                        "summary": "Get transmission queue status",
                        "description": "View current transmission queue and processing status",
                        "tags": ["Transmission Management"]
                    },
                    {
                        "path": "/api/v1/app/transmission/retry-failed",
                        "method": "POST",
                        "summary": "Retry failed transmissions",
                        "description": "Retry all failed transmissions in the queue",
                        "tags": ["Transmission Management"],
                        "request_body": {
                            "type": "object",
                            "properties": {
                                "submission_ids": {"type": "array", "items": {"type": "string"}},
                                "retry_all": {"type": "boolean", "default": False}
                            }
                        }
                    }
                ]
            },
            "taxpayer_management": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/taxpayers",
                        "method": "GET",
                        "summary": "List managed taxpayers",
                        "description": "Get list of taxpayer organizations under APP management",
                        "tags": ["Taxpayer Management"],
                        "parameters": [
                            {"name": "status", "in": "query", "type": "string"},
                            {"name": "registration_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "tin", "in": "query", "type": "string"}
                        ]
                    },
                    {
                        "path": "/api/v1/app/taxpayers",
                        "method": "POST",
                        "summary": "Register new taxpayer",
                        "description": "Register a new taxpayer organization for APP services",
                        "tags": ["Taxpayer Management"],
                        "request_body": {
                            "type": "object",
                            "required": ["tin", "organization_name", "contact_details"],
                            "properties": {
                                "tin": {"type": "string"},
                                "organization_name": {"type": "string"},
                                "business_type": {"type": "string"},
                                "contact_details": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string", "format": "email"},
                                        "phone": {"type": "string"},
                                        "address": {"type": "object"}
                                    }
                                },
                                "service_level": {"type": "string", "enum": ["basic", "standard", "premium"]},
                                "auto_submission": {"type": "boolean", "default": False}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/taxpayers/{taxpayer_id}",
                        "method": "GET",
                        "summary": "Get taxpayer details",
                        "description": "Retrieve detailed information about a specific taxpayer",
                        "tags": ["Taxpayer Management"],
                        "parameters": [
                            {"name": "taxpayer_id", "in": "path", "required": True, "type": "string"}
                        ]
                    },
                    {
                        "path": "/api/v1/app/taxpayers/{taxpayer_id}/compliance-status",
                        "method": "GET",
                        "summary": "Get taxpayer compliance status",
                        "description": "Get comprehensive compliance status for a taxpayer",
                        "tags": ["Taxpayer Management"],
                        "parameters": [
                            {"name": "taxpayer_id", "in": "path", "required": True, "type": "string"}
                        ],
                        "response": {
                            "type": "object",
                            "properties": {
                                "taxpayer_id": {"type": "string"},
                                "tin": {"type": "string"},
                                "compliance_score": {"type": "number"},
                                "submission_stats": {"type": "object"},
                                "outstanding_issues": {"type": "array"},
                                "last_submission": {"type": "string", "format": "date-time"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/taxpayers/{taxpayer_id}/suspend",
                        "method": "POST",
                        "summary": "Suspend taxpayer services",
                        "description": "Temporarily suspend APP services for a taxpayer",
                        "tags": ["Taxpayer Management"],
                        "request_body": {
                            "type": "object",
                            "required": ["reason"],
                            "properties": {
                                "reason": {"type": "string"},
                                "suspension_duration": {"type": "string"},
                                "notify_taxpayer": {"type": "boolean", "default": True}
                            }
                        }
                    }
                ]
            },
            "compliance_reporting": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/reports/submission-summary",
                        "method": "GET",
                        "summary": "Get submission summary report",
                        "description": "Generate summary report of all FIRS submissions",
                        "tags": ["Compliance Reporting"],
                        "parameters": [
                            {"name": "period", "in": "query", "type": "string", "enum": ["daily", "weekly", "monthly"], "default": "monthly"},
                            {"name": "taxpayer_tin", "in": "query", "type": "string"},
                            {"name": "start_date", "in": "query", "type": "string", "format": "date"},
                            {"name": "end_date", "in": "query", "type": "string", "format": "date"}
                        ]
                    },
                    {
                        "path": "/api/v1/app/reports/compliance-metrics",
                        "method": "GET",
                        "summary": "Get compliance metrics",
                        "description": "Retrieve detailed compliance metrics and KPIs",
                        "tags": ["Compliance Reporting"]
                    },
                    {
                        "path": "/api/v1/app/reports/firs-performance",
                        "method": "GET",
                        "summary": "Get FIRS performance metrics",
                        "description": "Get performance metrics for FIRS submissions and responses",
                        "tags": ["Compliance Reporting"]
                    },
                    {
                        "path": "/api/v1/app/reports/taxpayer-analytics",
                        "method": "GET",
                        "summary": "Get taxpayer analytics",
                        "description": "Generate analytics and insights for taxpayer compliance patterns",
                        "tags": ["Compliance Reporting"],
                        "parameters": [
                            {"name": "taxpayer_id", "in": "query", "type": "string"},
                            {"name": "analysis_type", "in": "query", "type": "string", "enum": ["submission_patterns", "compliance_trends", "risk_assessment"]}
                        ]
                    },
                    {
                        "path": "/api/v1/app/reports/export",
                        "method": "POST",
                        "summary": "Export compliance reports",
                        "description": "Export compliance reports in various formats (PDF, Excel, CSV)",
                        "tags": ["Compliance Reporting"],
                        "request_body": {
                            "type": "object",
                            "required": ["report_type", "format"],
                            "properties": {
                                "report_type": {"type": "string", "enum": ["submission_summary", "compliance_metrics", "taxpayer_analytics"]},
                                "format": {"type": "string", "enum": ["pdf", "excel", "csv"]},
                                "filters": {"type": "object"},
                                "email_delivery": {"type": "boolean", "default": False},
                                "recipients": {"type": "array", "items": {"type": "string", "format": "email"}}
                            }
                        }
                    }
                ]
            },
            "webhook_services": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/webhooks/firs-notifications",
                        "method": "GET",
                        "summary": "List FIRS notification webhooks",
                        "description": "Get configured webhook endpoints for FIRS notifications",
                        "tags": ["Webhook Services"]
                    },
                    {
                        "path": "/api/v1/app/webhooks/firs-notifications",
                        "method": "POST",
                        "summary": "Register FIRS notification webhook",
                        "description": "Register webhook endpoint to receive FIRS status notifications",
                        "tags": ["Webhook Services"],
                        "request_body": {
                            "type": "object",
                            "required": ["webhook_url", "events"],
                            "properties": {
                                "webhook_url": {"type": "string", "format": "uri"},
                                "events": {
                                    "type": "array",
                                    "items": {
                                        "type": "string",
                                        "enum": ["submission.accepted", "submission.rejected", "acknowledgment.received", "status.updated"]
                                    }
                                },
                                "secret": {"type": "string"},
                                "taxpayer_filter": {"type": "array", "items": {"type": "string"}},
                                "active": {"type": "boolean", "default": True}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/webhooks/{webhook_id}/test",
                        "method": "POST",
                        "summary": "Test webhook endpoint",
                        "description": "Send test notification to webhook endpoint",
                        "tags": ["Webhook Services"],
                        "parameters": [
                            {"name": "webhook_id", "in": "path", "required": True, "type": "string"}
                        ]
                    },
                    {
                        "path": "/api/v1/app/webhooks/delivery-logs",
                        "method": "GET",
                        "summary": "Get webhook delivery logs",
                        "description": "Retrieve logs of webhook delivery attempts and status",
                        "tags": ["Webhook Services"],
                        "parameters": [
                            {"name": "webhook_id", "in": "query", "type": "string"},
                            {"name": "status", "in": "query", "type": "string", "enum": ["success", "failed", "pending"]},
                            {"name": "start_date", "in": "query", "type": "string", "format": "date"}
                        ]
                    }
                ]
            },
            "status_management": {
                "endpoints": [
                    {
                        "path": "/api/v1/app/status/dashboard",
                        "method": "GET",
                        "summary": "Get APP service dashboard",
                        "description": "Get comprehensive dashboard view of APP service status and metrics",
                        "tags": ["Status Management"],
                        "response": {
                            "type": "object",
                            "properties": {
                                "service_status": {"type": "string"},
                                "firs_connectivity": {"type": "string"},
                                "pending_submissions": {"type": "integer"},
                                "recent_activity": {"type": "array"},
                                "alerts": {"type": "array"},
                                "performance_metrics": {"type": "object"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/app/status/firs-health",
                        "method": "GET",
                        "summary": "Get FIRS system health",
                        "description": "Check current health and availability of FIRS systems",
                        "tags": ["Status Management"]
                    },
                    {
                        "path": "/api/v1/app/status/alerts",
                        "method": "GET",
                        "summary": "Get system alerts",
                        "description": "Retrieve current system alerts and notifications",
                        "tags": ["Status Management"],
                        "parameters": [
                            {"name": "severity", "in": "query", "type": "string", "enum": ["low", "medium", "high", "critical"]},
                            {"name": "category", "in": "query", "type": "string", "enum": ["firs", "transmission", "taxpayer", "system"]}
                        ]
                    },
                    {
                        "path": "/api/v1/app/status/maintenance",
                        "method": "GET",
                        "summary": "Get maintenance schedule",
                        "description": "Get scheduled maintenance windows and system downtimes",
                        "tags": ["Status Management"]
                    }
                ]
            }
        }
    
    def _define_app_schemas(self) -> Dict[str, Any]:
        """Define APP-specific data schemas."""
        return {
            "FIRSSubmission": {
                "type": "object",
                "properties": {
                    "submission_id": {"type": "string"},
                    "firs_reference": {"type": "string"},
                    "taxpayer_tin": {"type": "string"},
                    "invoice_number": {"type": "string"},
                    "submission_type": {"type": "string", "enum": ["single", "batch"]},
                    "status": {"type": "string", "enum": ["pending", "processing", "accepted", "rejected", "failed"]},
                    "submitted_at": {"type": "string", "format": "date-time"},
                    "processed_at": {"type": "string", "format": "date-time"},
                    "firs_response": {"type": "object"},
                    "error_details": {"type": "array"},
                    "retry_count": {"type": "integer"},
                    "certificate_used": {"type": "string"},
                    "transmission_channel": {"type": "string"}
                }
            },
            "TaxpayerRecord": {
                "type": "object",
                "properties": {
                    "taxpayer_id": {"type": "string"},
                    "tin": {"type": "string"},
                    "organization_name": {"type": "string"},
                    "business_type": {"type": "string"},
                    "registration_date": {"type": "string", "format": "date"},
                    "status": {"type": "string", "enum": ["active", "suspended", "inactive"]},
                    "service_level": {"type": "string", "enum": ["basic", "standard", "premium"]},
                    "contact_details": {
                        "type": "object",
                        "properties": {
                            "email": {"type": "string", "format": "email"},
                            "phone": {"type": "string"},
                            "address": {"type": "object"}
                        }
                    },
                    "compliance_score": {"type": "number"},
                    "total_submissions": {"type": "integer"},
                    "successful_submissions": {"type": "integer"},
                    "last_submission_date": {"type": "string", "format": "date-time"},
                    "auto_submission_enabled": {"type": "boolean"}
                }
            },
            "ComplianceReport": {
                "type": "object",
                "properties": {
                    "report_id": {"type": "string"},
                    "report_type": {"type": "string"},
                    "period": {"type": "string"},
                    "generated_at": {"type": "string", "format": "date-time"},
                    "summary": {
                        "type": "object",
                        "properties": {
                            "total_submissions": {"type": "integer"},
                            "successful_submissions": {"type": "integer"},
                            "failed_submissions": {"type": "integer"},
                            "success_rate": {"type": "number"},
                            "average_processing_time": {"type": "number"}
                        }
                    },
                    "taxpayer_breakdown": {"type": "array"},
                    "compliance_metrics": {"type": "object"},
                    "recommendations": {"type": "array"}
                }
            },
            "FIRSNotificationWebhook": {
                "type": "object",
                "properties": {
                    "webhook_id": {"type": "string"},
                    "webhook_url": {"type": "string", "format": "uri"},
                    "events": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string", "enum": ["active", "inactive", "error"]},
                    "secret": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "last_delivery": {"type": "string", "format": "date-time"},
                    "delivery_count": {"type": "integer"},
                    "success_count": {"type": "integer"},
                    "failure_count": {"type": "integer"},
                    "taxpayer_filter": {"type": "array", "items": {"type": "string"}}
                }
            },
            "TransmissionChannel": {
                "type": "object",
                "properties": {
                    "channel_id": {"type": "string"},
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["secure_https", "sftp", "web_service"]},
                    "status": {"type": "string", "enum": ["active", "inactive", "maintenance"]},
                    "endpoint_url": {"type": "string", "format": "uri"},
                    "certificate_required": {"type": "boolean"},
                    "supported_formats": {"type": "array", "items": {"type": "string"}},
                    "rate_limit": {"type": "object"},
                    "health_check": {
                        "type": "object",
                        "properties": {
                            "last_check": {"type": "string", "format": "date-time"},
                            "status": {"type": "string"},
                            "response_time_ms": {"type": "number"}
                        }
                    }
                }
            },
            "APPDashboard": {
                "type": "object",
                "properties": {
                    "service_status": {"type": "string", "enum": ["operational", "degraded", "maintenance", "outage"]},
                    "firs_connectivity": {"type": "string", "enum": ["connected", "disconnected", "unstable"]},
                    "statistics": {
                        "type": "object",
                        "properties": {
                            "total_taxpayers": {"type": "integer"},
                            "active_taxpayers": {"type": "integer"},
                            "pending_submissions": {"type": "integer"},
                            "today_submissions": {"type": "integer"},
                            "success_rate_24h": {"type": "number"}
                        }
                    },
                    "recent_activity": {"type": "array"},
                    "alerts": {"type": "array"},
                    "system_health": {"type": "object"}
                }
            }
        }
    
    def _define_integration_examples(self) -> Dict[str, Any]:
        """Define integration examples and code samples for APP users."""
        return {
            "firs_submission_example": {
                "title": "Submitting E-Invoice to FIRS",
                "description": "Example of submitting a validated e-invoice to FIRS through TaxPoynt APP",
                "code": """
# Python SDK Example
from taxpoynt_app_sdk import TaxPoyntAPPClient

client = TaxPoyntAPPClient(api_key="your_app_api_key")

# Submit single invoice to FIRS
invoice_data = {
    "invoice_number": "INV-2024-001",
    "issue_date": "2024-01-15",
    "supplier": {
        "name": "Your Company Ltd",
        "tin": "12345678-001",
        "address": "123 Business Street, Lagos"
    },
    "customer": {
        "name": "Customer Company Ltd", 
        "tin": "87654321-001",
        "address": "456 Customer Ave, Abuja"
    },
    "invoice_lines": [{
        "description": "Professional Services",
        "quantity": 1,
        "unit_price": 1000000.00,
        "tax_amount": 75000.00
    }],
    "total_amount": 1075000.00
}

# Submit to FIRS
submission = client.firs.submit(
    invoice_data=invoice_data,
    taxpayer_tin="12345678-001",
    certificate_id="cert_123",
    auto_retry=True
)

print(f"Submission ID: {submission.submission_id}")
print(f"FIRS Reference: {submission.firs_reference}")
print(f"Status: {submission.status}")

# Check submission status
status = client.firs.get_status(submission.submission_id)
print(f"Current Status: {status.status}")
if status.status == "rejected":
    print(f"Rejection Reasons: {status.error_details}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/app/firs/submit" \\
  -H "Authorization: Bearer YOUR_APP_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "invoice_data": {
      "invoice_number": "INV-2024-001",
      "supplier": {
        "name": "Your Company Ltd",
        "tin": "12345678-001"
      },
      "total_amount": 1075000.00
    },
    "taxpayer_tin": "12345678-001",
    "certificate_id": "cert_123",
    "auto_retry": true
  }'
                """
            },
            "taxpayer_management_example": {
                "title": "Managing Taxpayer Organizations",
                "description": "Example of registering and managing taxpayer organizations under APP service",
                "code": """
# Register new taxpayer
taxpayer_data = {
    "tin": "98765432-001",
    "organization_name": "New Client Company Ltd",
    "business_type": "Manufacturing",
    "contact_details": {
        "email": "admin@newclient.com",
        "phone": "+234-800-123-4567",
        "address": {
            "street": "789 Industrial Road",
            "city": "Port Harcourt",
            "state": "Rivers",
            "country": "Nigeria"
        }
    },
    "service_level": "standard",
    "auto_submission": True
}

# Register taxpayer
taxpayer = client.taxpayers.register(taxpayer_data)
print(f"Taxpayer registered: {taxpayer.taxpayer_id}")

# Get compliance status
compliance = client.taxpayers.get_compliance_status(taxpayer.taxpayer_id)
print(f"Compliance Score: {compliance.compliance_score}")
print(f"Total Submissions: {compliance.submission_stats.total}")
print(f"Success Rate: {compliance.submission_stats.success_rate}%")

# List all managed taxpayers
taxpayers = client.taxpayers.list(status="active")
for tp in taxpayers.data:
    print(f"TIN: {tp.tin}, Name: {tp.organization_name}, Status: {tp.status}")
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/app/taxpayers" \\
  -H "Authorization: Bearer YOUR_APP_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "tin": "98765432-001",
    "organization_name": "New Client Company Ltd",
    "business_type": "Manufacturing",
    "contact_details": {
      "email": "admin@newclient.com",
      "phone": "+234-800-123-4567"
    },
    "service_level": "standard",
    "auto_submission": true
  }'
                """
            },
            "webhook_notifications_example": {
                "title": "Setting up FIRS Notification Webhooks",
                "description": "Example of configuring webhooks to receive real-time FIRS status updates",
                "code": """
# Register webhook for FIRS notifications
webhook_config = {
    "webhook_url": "https://your-app.com/webhooks/firs-notifications",
    "events": [
        "submission.accepted",
        "submission.rejected", 
        "acknowledgment.received",
        "status.updated"
    ],
    "secret": "your_webhook_secret_key",
    "taxpayer_filter": ["12345678-001", "98765432-001"],  # Optional: filter by specific TINs
    "active": True
}

# Register webhook
webhook = client.webhooks.register_firs_notifications(webhook_config)
print(f"Webhook registered: {webhook.webhook_id}")

# Test webhook endpoint
test_result = client.webhooks.test(webhook.webhook_id)
print(f"Webhook test: {test_result.status}")

# Get delivery logs
logs = client.webhooks.get_delivery_logs(webhook.webhook_id, status="failed")
for log in logs.data:
    print(f"Delivery attempt: {log.timestamp}, Status: {log.status}, Error: {log.error}")

# Example webhook handler (Flask)
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)

@app.route('/webhooks/firs-notifications', methods=['POST'])
def handle_firs_notification():
    # Verify webhook signature
    signature = request.headers.get('X-TaxPoynt-Signature')
    payload = request.get_data()
    expected_signature = hmac.new(
        webhook_config['secret'].encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected_signature):
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Process notification
    notification = request.json
    event_type = notification['event']
    submission_data = notification['data']
    
    if event_type == 'submission.accepted':
        print(f"Invoice {submission_data['invoice_number']} accepted by FIRS")
        # Update your local database, notify customer, etc.
    elif event_type == 'submission.rejected':
        print(f"Invoice {submission_data['invoice_number']} rejected: {submission_data['error_details']}")
        # Handle rejection, notify customer for corrections
    
    return jsonify({'status': 'received'}), 200
                """,
                "curl_example": """
curl -X POST "https://api.taxpoynt.com/api/v1/app/webhooks/firs-notifications" \\
  -H "Authorization: Bearer YOUR_APP_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "webhook_url": "https://your-app.com/webhooks/firs-notifications",
    "events": ["submission.accepted", "submission.rejected"],
    "secret": "your_webhook_secret_key",
    "active": true
  }'
                """
            },
            "compliance_reporting_example": {
                "title": "Generating Compliance Reports",
                "description": "Example of generating and exporting compliance reports for regulatory purposes",
                "code": """
# Generate monthly compliance report
report = client.reports.get_submission_summary(
    period="monthly",
    start_date="2024-01-01", 
    end_date="2024-01-31"
)

print(f"Total Submissions: {report.summary.total_submissions}")
print(f"Success Rate: {report.summary.success_rate}%")
print(f"Average Processing Time: {report.summary.average_processing_time}s")

# Get detailed compliance metrics
metrics = client.reports.get_compliance_metrics()
print(f"Overall Compliance Score: {metrics.overall_score}")
print(f"FIRS Response Time: {metrics.firs_performance.average_response_time}ms")

# Export report to PDF
export_request = {
    "report_type": "submission_summary",
    "format": "pdf",
    "filters": {
        "period": "monthly",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31"
    },
    "email_delivery": True,
    "recipients": ["compliance@yourcompany.com", "manager@yourcompany.com"]
}

export = client.reports.export(export_request)
print(f"Report exported: {export.file_url}")

# Get taxpayer analytics
analytics = client.reports.get_taxpayer_analytics(
    analysis_type="compliance_trends"
)

for trend in analytics.compliance_trends:
    print(f"Period: {trend.period}, Score: {trend.compliance_score}")
                """,
                "curl_example": """
curl -X GET "https://api.taxpoynt.com/api/v1/app/reports/submission-summary?period=monthly&start_date=2024-01-01&end_date=2024-01-31" \\
  -H "Authorization: Bearer YOUR_APP_API_KEY"
                """
            }
        }
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI specification for APP endpoints."""
        openapi_spec = {
            "openapi": "3.0.2",
            "info": {
                "title": self.title,
                "description": self.description,
                "version": "1.0.0",
                "contact": {
                    "name": "TaxPoynt APP Support",
                    "email": "info@taxpoynt.com",
                    "url": "https://docs.taxpoynt.com/app"
                }
            },
            "servers": [
                {"url": "https://api.taxpoynt.com", "description": "Production"},
                {"url": "https://sandbox-api.taxpoynt.com", "description": "Sandbox"}
            ],
            "paths": {},
            "components": {
                "schemas": self.app_schemas,
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
                {"name": "FIRS Integration", "description": "Direct submission and communication with FIRS"},
                {"name": "Transmission Management", "description": "Secure transmission channels and certificate management"},
                {"name": "Taxpayer Management", "description": "Taxpayer organization registration and management"},
                {"name": "Compliance Reporting", "description": "Compliance reports, metrics, and analytics"},
                {"name": "Webhook Services", "description": "Real-time notification and event handling"},
                {"name": "Status Management", "description": "System status, health monitoring, and alerts"}
            ]
        }
        
        # Add all APP endpoints to the OpenAPI spec
        for category, endpoints_data in self.app_endpoints.items():
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
                        "404": {"description": "Not Found"},
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
        """Generate HTML documentation for APP APIs."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; }}
        .header {{ background: #dc2626; color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }}
        .endpoint {{ background: #fef2f2; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #dc2626; }}
        .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; color: white; }}
        .get {{ background: #10b981; }}
        .post {{ background: #3b82f6; }}
        .put {{ background: #f59e0b; }}
        .delete {{ background: #ef4444; }}
        .code {{ background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 6px; overflow-x: auto; }}
        .example {{ margin: 15px 0; }}
        .firs-highlight {{ background: #fef2f2; border: 1px solid #fecaca; padding: 10px; border-radius: 4px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Comprehensive API documentation for Access Point Provider role</p>
    </div>
    
    <div class="section">
        <h2>Overview</h2>
        {description}
        
        <div class="firs-highlight">
            <strong>🏛️ TaxPoynt as Your Certified APP:</strong><br>
            TaxPoynt is your certified Access Point Provider to FIRS. We handle all technical complexities
            of secure transmission, certificate management, and FIRS protocol compliance so you can focus
            on your business operations and taxpayer services.
        </div>
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
        <p>For APP API support, contact:</p>
        <ul>
            <li>Email: info@taxpoynt.com</li>
            <li>Documentation: https://docs.taxpoynt.com/app</li>
            <li>FIRS Support Hotline: +234-1-TAXPOYNT</li>
        </ul>
    </div>
</body>
</html>
        """
        
        # Generate endpoints HTML
        endpoints_html = ""
        for category, endpoints_data in self.app_endpoints.items():
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
        openapi_file = output_path / "app_api_openapi.json"
        with open(openapi_file, "w") as f:
            json.dump(openapi_spec, f, indent=2)
        files_created["openapi"] = str(openapi_file)
        
        # Export HTML documentation
        html_doc = self.generate_html_documentation()
        html_file = output_path / "app_api_documentation.html"
        with open(html_file, "w") as f:
            f.write(html_doc)
        files_created["html"] = str(html_file)
        
        # Export integration examples
        examples_file = output_path / "app_integration_examples.json"
        with open(examples_file, "w") as f:
            json.dump(self.integration_examples, f, indent=2)
        files_created["examples"] = str(examples_file)
        
        return files_created


def generate_app_api_docs(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate complete APP API documentation."""
    generator = APPAPIDocumentationGenerator()
    
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
    "APPAPIDocumentationGenerator",
    "generate_app_api_docs"
]