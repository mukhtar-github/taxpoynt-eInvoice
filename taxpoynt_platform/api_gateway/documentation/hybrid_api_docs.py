"""
Hybrid Role API Documentation Generator
======================================
Generates comprehensive API documentation for organizations that need both
System Integration (SI) and Access Point Provider (APP) capabilities.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from core_platform.authentication.role_manager import PlatformRole
from .si_api_docs import SIAPIDocumentationGenerator
from .app_api_docs import APPAPIDocumentationGenerator


class HybridAPIDocumentationGenerator:
    """Generates comprehensive documentation for Hybrid role users with both SI and APP capabilities."""
    
    def __init__(self):
        self.role = PlatformRole.HYBRID
        self.title = "TaxPoynt Hybrid API Documentation"
        self.description = """
        ## TaxPoynt Hybrid API Documentation
        
        Welcome to the comprehensive TaxPoynt Hybrid API documentation. As a Hybrid user, you have access to 
        **both System Integration (SI) and Access Point Provider (APP)** capabilities, providing end-to-end 
        e-invoicing solutions.
        
        ## Complete E-Invoicing Workflow
        
        ### 🔧 **System Integration Capabilities (SI)**
        - **Financial Systems Integration**: Connect payment processors (Paystack, Moniepoint, OPay, PalmPay, Interswitch, Flutterwave, Stripe)
        - **ERP/CRM Integration**: Sync with business systems (Odoo, SAP, Dynamics, NetSuite)
        - **Data Transformation**: Convert business data to e-invoice standards
        - **Document Generation**: Create UBL-compliant invoices and PDFs
        - **Certificate Management**: Handle digital certificates and security
        
        ### 🏛️ **Access Point Provider Capabilities (APP)**
        - **FIRS Integration**: Direct submission to FIRS systems
        - **Compliance Management**: Track regulatory compliance and reporting
        - **Taxpayer Services**: Manage multiple taxpayer organizations
        - **Status Monitoring**: Real-time submission tracking and acknowledgments
        - **Regulatory Reporting**: Generate compliance reports and analytics
        
        ## Target Users
        - Large enterprises with complex integration needs
        - Software vendors providing comprehensive tax solutions
        - Tax consulting firms managing multiple clients
        - Organizations requiring both data collection and FIRS submission
        
        ## Workflow Integration
        **Data Collection → Transformation → Generation → Submission → Monitoring**
        
        1. **Collect**: Use SI APIs to gather data from financial/business systems
        2. **Transform**: Convert data to compliance standards using SI transformation APIs
        3. **Generate**: Create compliant e-invoices using SI document APIs
        4. **Submit**: Send to FIRS using APP submission APIs
        5. **Monitor**: Track status and compliance using APP monitoring APIs
        """
        
        # Initialize component generators
        self.si_generator = SIAPIDocumentationGenerator()
        self.app_generator = APPAPIDocumentationGenerator()
        
        # Define hybrid-specific endpoints and workflows
        self.hybrid_endpoints = self._define_hybrid_endpoints()
        self.hybrid_workflows = self._define_hybrid_workflows()
        self.integration_examples = self._define_integration_examples()
    
    def _define_hybrid_endpoints(self) -> Dict[str, Any]:
        """Define hybrid-specific endpoint combinations and workflows."""
        return {
            "end_to_end_workflows": {
                "endpoints": [
                    {
                        "path": "/api/v1/hybrid/workflows/payment-to-firs",
                        "method": "POST",
                        "summary": "Complete payment-to-FIRS workflow",
                        "description": "End-to-end workflow: Collect payment data → Transform → Generate invoice → Submit to FIRS",
                        "tags": ["Hybrid Workflows"],
                        "request_body": {
                            "type": "object",
                            "required": ["payment_processor", "payment_transaction_ids", "taxpayer_tin"],
                            "properties": {
                                "payment_processor": {"type": "string", "enum": ["paystack", "moniepoint", "opay", "palmpay", "interswitch", "flutterwave", "stripe"]},
                                "payment_transaction_ids": {"type": "array", "items": {"type": "string"}},
                                "taxpayer_tin": {"type": "string"},
                                "transformation_template": {"type": "string"},
                                "document_template": {"type": "string"},
                                "auto_submit_to_firs": {"type": "boolean", "default": True},
                                "certificate_id": {"type": "string"}
                            }
                        },
                        "response": {
                            "type": "object",
                            "properties": {
                                "workflow_id": {"type": "string"},
                                "payment_data_collected": {"type": "integer"},
                                "invoices_generated": {"type": "integer"},
                                "firs_submissions": {"type": "array"},
                                "workflow_status": {"type": "string"},
                                "estimated_completion": {"type": "string", "format": "date-time"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/hybrid/workflows/erp-to-firs",
                        "method": "POST",
                        "summary": "Complete ERP-to-FIRS workflow",
                        "description": "End-to-end workflow: Sync ERP data → Transform → Generate invoices → Submit to FIRS",
                        "tags": ["Hybrid Workflows"],
                        "request_body": {
                            "type": "object",
                            "required": ["erp_connection_id", "sync_criteria", "taxpayer_tin"],
                            "properties": {
                                "erp_connection_id": {"type": "string"},
                                "sync_criteria": {
                                    "type": "object",
                                    "properties": {
                                        "date_range": {"type": "object"},
                                        "invoice_status": {"type": "array"},
                                        "customer_filter": {"type": "string"}
                                    }
                                },
                                "taxpayer_tin": {"type": "string"},
                                "batch_size": {"type": "integer", "default": 50},
                                "auto_submit_to_firs": {"type": "boolean", "default": True}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/hybrid/workflows/{workflow_id}/status",
                        "method": "GET",
                        "summary": "Get hybrid workflow status",
                        "description": "Track progress of end-to-end workflow execution",
                        "tags": ["Hybrid Workflows"],
                        "parameters": [
                            {"name": "workflow_id", "in": "path", "required": True, "type": "string"}
                        ],
                        "response": {
                            "type": "object",
                            "properties": {
                                "workflow_id": {"type": "string"},
                                "workflow_type": {"type": "string"},
                                "status": {"type": "string", "enum": ["running", "completed", "failed", "partial"]},
                                "progress": {
                                    "type": "object",
                                    "properties": {
                                        "data_collection": {"type": "object"},
                                        "transformation": {"type": "object"},
                                        "document_generation": {"type": "object"},
                                        "firs_submission": {"type": "object"}
                                    }
                                },
                                "results": {"type": "object"},
                                "errors": {"type": "array"}
                            }
                        }
                    }
                ]
            },
            "cross_role_management": {
                "endpoints": [
                    {
                        "path": "/api/v1/hybrid/organization/capabilities",
                        "method": "GET",
                        "summary": "Get organization capabilities",
                        "description": "Get comprehensive view of SI and APP capabilities for the organization",
                        "tags": ["Cross-Role Management"],
                        "response": {
                            "type": "object",
                            "properties": {
                                "si_capabilities": {
                                    "type": "object",
                                    "properties": {
                                        "payment_processors": {"type": "array"},
                                        "erp_connectors": {"type": "array"},
                                        "active_connections": {"type": "integer"},
                                        "transformation_templates": {"type": "integer"}
                                    }
                                },
                                "app_capabilities": {
                                    "type": "object",
                                    "properties": {
                                        "managed_taxpayers": {"type": "integer"},
                                        "firs_connectivity": {"type": "string"},
                                        "transmission_channels": {"type": "array"},
                                        "compliance_score": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    {
                        "path": "/api/v1/hybrid/organization/switch-context",
                        "method": "POST",
                        "summary": "Switch between SI and APP contexts",
                        "description": "Switch API context between SI and APP modes for role-specific operations",
                        "tags": ["Cross-Role Management"],
                        "request_body": {
                            "type": "object",
                            "required": ["target_role"],
                            "properties": {
                                "target_role": {"type": "string", "enum": ["SI", "APP"]},
                                "context_data": {"type": "object"},
                                "session_duration": {"type": "integer", "description": "Minutes", "default": 60}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/hybrid/analytics/cross-role",
                        "method": "GET",
                        "summary": "Get cross-role analytics",
                        "description": "Analytics showing how SI and APP capabilities work together",
                        "tags": ["Cross-Role Management"],
                        "parameters": [
                            {"name": "period", "in": "query", "type": "string", "default": "30d"},
                            {"name": "breakdown", "in": "query", "type": "string", "enum": ["daily", "weekly", "monthly"]}
                        ]
                    }
                ]
            },
            "unified_monitoring": {
                "endpoints": [
                    {
                        "path": "/api/v1/hybrid/monitoring/dashboard",
                        "method": "GET",
                        "summary": "Get unified hybrid dashboard",
                        "description": "Comprehensive dashboard showing both SI and APP activities",
                        "tags": ["Unified Monitoring"],
                        "response": {
                            "type": "object",
                            "properties": {
                                "si_overview": {"type": "object"},
                                "app_overview": {"type": "object"},
                                "integration_health": {"type": "object"},
                                "workflow_statistics": {"type": "object"},
                                "recent_activities": {"type": "array"},
                                "alerts": {"type": "array"}
                            }
                        }
                    },
                    {
                        "path": "/api/v1/hybrid/monitoring/health-check",
                        "method": "GET",
                        "summary": "Comprehensive health check",
                        "description": "Health status of all SI and APP components",
                        "tags": ["Unified Monitoring"]
                    },
                    {
                        "path": "/api/v1/hybrid/monitoring/alerts",
                        "method": "GET",
                        "summary": "Get unified alerts",
                        "description": "Get alerts from both SI and APP systems",
                        "tags": ["Unified Monitoring"],
                        "parameters": [
                            {"name": "severity", "in": "query", "type": "string"},
                            {"name": "category", "in": "query", "type": "string", "enum": ["si", "app", "workflow", "integration"]}
                        ]
                    }
                ]
            }
        }
    
    def _define_hybrid_workflows(self) -> Dict[str, Any]:
        """Define complete end-to-end workflows combining SI and APP capabilities."""
        return {
            "payment_to_firs_workflow": {
                "name": "Payment Processor to FIRS Workflow",
                "description": "Complete workflow from payment processor data to FIRS submission",
                "steps": [
                    {
                        "step": 1,
                        "name": "Payment Data Collection",
                        "role": "SI",
                        "description": "Collect transaction data from payment processors",
                        "api_calls": [
                            "GET /api/v1/si/payments/unified/transactions",
                            "GET /api/v1/si/payments/{processor}/transactions"
                        ]
                    },
                    {
                        "step": 2,
                        "name": "Data Transformation",
                        "role": "SI", 
                        "description": "Transform payment data to e-invoice format",
                        "api_calls": [
                            "POST /api/v1/si/transformation/validate",
                            "POST /api/v1/si/transformation/mappings"
                        ]
                    },
                    {
                        "step": 3,
                        "name": "Invoice Generation",
                        "role": "SI",
                        "description": "Generate UBL-compliant e-invoices",
                        "api_calls": [
                            "POST /api/v1/si/documents/generate",
                            "POST /api/v1/si/irn/generate"
                        ]
                    },
                    {
                        "step": 4,
                        "name": "FIRS Submission",
                        "role": "APP",
                        "description": "Submit generated invoices to FIRS",
                        "api_calls": [
                            "POST /api/v1/app/firs/submit",
                            "POST /api/v1/app/firs/batch-submit"
                        ]
                    },
                    {
                        "step": 5,
                        "name": "Status Monitoring",
                        "role": "APP",
                        "description": "Monitor submission status and handle responses",
                        "api_calls": [
                            "GET /api/v1/app/firs/status/{submission_id}",
                            "GET /api/v1/app/firs/acknowledgments"
                        ]
                    }
                ]
            },
            "erp_to_firs_workflow": {
                "name": "ERP System to FIRS Workflow", 
                "description": "Complete workflow from ERP system data to FIRS submission",
                "steps": [
                    {
                        "step": 1,
                        "name": "ERP Data Sync",
                        "role": "SI",
                        "description": "Synchronize invoice data from ERP systems",
                        "api_calls": [
                            "POST /api/v1/si/erp/connections/{connection_id}/sync",
                            "GET /api/v1/si/erp/data/invoices"
                        ]
                    },
                    {
                        "step": 2,
                        "name": "Field Mapping",
                        "role": "SI",
                        "description": "Apply field mappings for ERP-to-UBL conversion",
                        "api_calls": [
                            "GET /api/v1/si/transformation/mappings",
                            "POST /api/v1/si/transformation/validate"
                        ]
                    },
                    {
                        "step": 3,
                        "name": "Compliance Validation",
                        "role": "SI",
                        "description": "Validate data against business rules and schemas",
                        "api_calls": [
                            "POST /api/v1/si/validation/validate-invoice",
                            "GET /api/v1/si/validation/business-rules"
                        ]
                    },
                    {
                        "step": 4,
                        "name": "Document Creation",
                        "role": "SI",
                        "description": "Generate compliant e-invoice documents",
                        "api_calls": [
                            "POST /api/v1/si/documents/generate",
                            "GET /api/v1/si/documents/{document_id}/preview"
                        ]
                    },
                    {
                        "step": 5,
                        "name": "FIRS Submission",
                        "role": "APP",
                        "description": "Submit to FIRS with proper certificates",
                        "api_calls": [
                            "POST /api/v1/app/firs/submit",
                            "POST /api/v1/app/transmission/test-connection"
                        ]
                    },
                    {
                        "step": 6,
                        "name": "Compliance Tracking",
                        "role": "APP",
                        "description": "Track compliance and generate reports",
                        "api_calls": [
                            "GET /api/v1/app/reports/compliance-metrics",
                            "GET /api/v1/app/taxpayers/{taxpayer_id}/compliance-status"
                        ]
                    }
                ]
            }
        }
    
    def _define_integration_examples(self) -> Dict[str, Any]:
        """Define comprehensive integration examples for hybrid users."""
        return {
            "complete_payment_workflow": {
                "title": "Complete Payment-to-FIRS Workflow",
                "description": "End-to-end example: Paystack payment → e-invoice generation → FIRS submission",
                "code": """
# Complete Hybrid Workflow Example
from taxpoynt_hybrid_sdk import TaxPoyntHybridClient

client = TaxPoyntHybridClient(api_key="your_hybrid_api_key")

# Step 1: Collect Payment Data (SI Role)
print("Step 1: Collecting payment data...")
transactions = client.si.payments.paystack.get_transactions(
    start_date="2024-01-01",
    end_date="2024-01-31",
    status="success"
)
print(f"Collected {len(transactions.data)} successful transactions")

# Step 2: Transform and Validate (SI Role)
print("Step 2: Transforming payment data to e-invoice format...")
transformed_invoices = []

for transaction in transactions.data:
    # Transform payment data to invoice format
    invoice_data = client.si.transformation.transform_payment_to_invoice(
        transaction_data=transaction,
        mapping_template="paystack_to_ubl",
        taxpayer_tin="12345678-001"
    )
    
    # Validate transformed data
    validation = client.si.validation.validate_invoice(invoice_data)
    if validation.is_valid:
        transformed_invoices.append(invoice_data)
    else:
        print(f"Validation failed for transaction {transaction.id}: {validation.errors}")

print(f"Successfully transformed {len(transformed_invoices)} invoices")

# Step 3: Generate Documents (SI Role)
print("Step 3: Generating e-invoice documents...")
generated_documents = []

for invoice_data in transformed_invoices:
    # Generate IRN first
    irn = client.si.irn.generate(
        invoice_data=invoice_data,
        sequence_type="chronological"
    )
    
    # Generate document with IRN
    document = client.si.documents.generate(
        invoice_data={**invoice_data, "irn": irn.irn},
        document_type="both",  # UBL and PDF
        certificate_id="cert_123",
        template_id="standard_invoice"
    )
    
    generated_documents.append(document)

print(f"Generated {len(generated_documents)} compliant documents")

# Step 4: Submit to FIRS (APP Role)
print("Step 4: Submitting to FIRS...")
firs_submissions = []

# Switch to APP context
client.context.switch_to_app()

# Submit in batches
batch_size = 10
for i in range(0, len(generated_documents), batch_size):
    batch = generated_documents[i:i+batch_size]
    
    submission = client.app.firs.batch_submit(
        invoices=[doc.invoice_data for doc in batch],
        taxpayer_tin="12345678-001",
        batch_name=f"Paystack_Batch_{i//batch_size + 1}",
        certificate_id="cert_123"
    )
    
    firs_submissions.append(submission)
    print(f"Submitted batch {i//batch_size + 1}: {submission.firs_reference}")

# Step 5: Monitor Status (APP Role)
print("Step 5: Monitoring submission status...")
for submission in firs_submissions:
    status = client.app.firs.get_status(submission.submission_id)
    print(f"Submission {submission.submission_id}: {status.status}")
    
    if status.status == "rejected":
        print(f"Rejection reasons: {status.error_details}")
        
        # Resubmit with corrections if needed
        if status.error_details and "minor" in str(status.error_details).lower():
            resubmission = client.app.firs.resubmit(
                submission_id=submission.submission_id,
                correction_notes="Minor data corrections applied"
            )
            print(f"Resubmitted: {resubmission.submission_id}")

# Step 6: Generate Compliance Report (APP Role)
print("Step 6: Generating compliance report...")
report = client.app.reports.get_submission_summary(
    period="monthly",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(f"Compliance Report:")
print(f"- Total Submissions: {report.summary.total_submissions}")
print(f"- Success Rate: {report.summary.success_rate}%")
print(f"- Average Processing Time: {report.summary.average_processing_time}s")

# Export detailed report
export = client.app.reports.export(
    report_type="submission_summary",
    format="pdf",
    filters={"period": "monthly", "start_date": "2024-01-01"},
    email_delivery=True,
    recipients=["compliance@yourcompany.com"]
)

print(f"Detailed report exported: {export.file_url}")
                """,
                "curl_example": """
# Complete workflow using the unified hybrid endpoint
curl -X POST "https://api.taxpoynt.com/api/v1/hybrid/workflows/payment-to-firs" \\
  -H "Authorization: Bearer YOUR_HYBRID_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "payment_processor": "paystack",
    "payment_transaction_ids": ["txn_1", "txn_2", "txn_3"],
    "taxpayer_tin": "12345678-001",
    "transformation_template": "paystack_to_ubl",
    "document_template": "standard_invoice",
    "auto_submit_to_firs": true,
    "certificate_id": "cert_123"
  }'
                """
            },
            "erp_integration_workflow": {
                "title": "Complete ERP-to-FIRS Integration",
                "description": "End-to-end example: Odoo ERP → data transformation → FIRS compliance",
                "code": """
# Complete ERP Integration Workflow
from taxpoynt_hybrid_sdk import TaxPoyntHybridClient

client = TaxPoyntHybridClient(api_key="your_hybrid_api_key")

# Step 1: Setup ERP Connection (SI Role)
print("Step 1: Setting up ERP connection...")
erp_connection = client.si.erp.create_connection({
    "erp_type": "odoo",
    "connection_config": {
        "url": "https://your-odoo.com",
        "database": "your_database",
        "username": "api_user",
        "api_key": "your_odoo_api_key"
    },
    "sync_schedule": "0 */6 * * *",  # Every 6 hours
    "enabled_modules": ["account", "sale", "purchase"]
})

print(f"ERP connection created: {erp_connection.id}")

# Step 2: Sync ERP Data (SI Role)
print("Step 2: Syncing ERP data...")
sync_result = client.si.erp.sync_connection(
    connection_id=erp_connection.id,
    sync_criteria={
        "models": ["account.move"],
        "filters": {
            "move_type": "out_invoice",
            "state": "posted",
            "invoice_date": ">=2024-01-01"
        }
    }
)

print(f"Synced {sync_result.records_processed} invoice records")

# Step 3: Setup Field Mappings (SI Role)
print("Step 3: Creating field mappings...")
mappings = [
    {
        "source_field": "partner_id.name",
        "target_field": "AccountingCustomerParty.Party.PartyName.Name",
        "transformation_rule": {"type": "direct_mapping"}
    },
    {
        "source_field": "partner_id.vat",
        "target_field": "AccountingCustomerParty.Party.PartyTaxScheme.CompanyID",
        "transformation_rule": {"type": "direct_mapping"}
    },
    {
        "source_field": "amount_total",
        "target_field": "LegalMonetaryTotal.TaxInclusiveAmount",
        "transformation_rule": {"type": "currency_conversion", "target_currency": "NGN"}
    }
]

for mapping in mappings:
    client.si.transformation.create_mapping(mapping)

print("Field mappings created successfully")

# Step 4: Process Invoices (SI Role)
print("Step 4: Processing invoices...")
erp_invoices = client.si.erp.get_synced_data(
    connection_id=erp_connection.id,
    model="account.move"
)

processed_invoices = []
for erp_invoice in erp_invoices.data:
    # Transform ERP data to UBL format
    transformed = client.si.transformation.apply_mappings(
        source_data=erp_invoice,
        mapping_set="odoo_to_ubl"
    )
    
    # Validate transformed data
    validation = client.si.validation.validate_invoice(transformed)
    if validation.is_valid:
        # Generate document
        document = client.si.documents.generate(
            invoice_data=transformed,
            document_type="both"
        )
        processed_invoices.append(document)
    else:
        print(f"Validation failed for invoice {erp_invoice.id}: {validation.errors}")

print(f"Successfully processed {len(processed_invoices)} invoices")

# Step 5: Register Taxpayers (APP Role) 
print("Step 5: Managing taxpayers...")
client.context.switch_to_app()

# Register taxpayer if not exists
taxpayer = client.app.taxpayers.register({
    "tin": "12345678-001",
    "organization_name": "Your Company Ltd",
    "business_type": "Software Development",
    "contact_details": {
        "email": "admin@yourcompany.com",
        "phone": "+234-800-123-4567"
    },
    "service_level": "premium",
    "auto_submission": True
})

# Step 6: Submit to FIRS (APP Role)
print("Step 6: Submitting to FIRS...")
firs_submission = client.app.firs.batch_submit(
    invoices=[doc.invoice_data for doc in processed_invoices],
    taxpayer_tin="12345678-001",
    batch_name="ERP_Monthly_Submission"
)

print(f"Submitted to FIRS: {firs_submission.firs_reference}")

# Step 7: Monitor and Report (APP Role)
print("Step 7: Monitoring compliance...")
compliance_status = client.app.taxpayers.get_compliance_status(taxpayer.taxpayer_id)
print(f"Compliance Score: {compliance_status.compliance_score}")
print(f"Outstanding Issues: {len(compliance_status.outstanding_issues)}")

# Generate analytics
analytics = client.app.reports.get_taxpayer_analytics(
    taxpayer_id=taxpayer.taxpayer_id,
    analysis_type="compliance_trends"
)

print("Compliance trends:")
for trend in analytics.compliance_trends:
    print(f"  {trend.period}: {trend.compliance_score}")
                """,
                "curl_example": """
# Use the unified ERP-to-FIRS workflow endpoint
curl -X POST "https://api.taxpoynt.com/api/v1/hybrid/workflows/erp-to-firs" \\
  -H "Authorization: Bearer YOUR_HYBRID_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "erp_connection_id": "conn_odoo_123",
    "sync_criteria": {
      "date_range": {"start": "2024-01-01", "end": "2024-01-31"},
      "invoice_status": ["posted"],
      "customer_filter": null
    },
    "taxpayer_tin": "12345678-001", 
    "batch_size": 50,
    "auto_submit_to_firs": true
  }'
                """
            },
            "cross_role_monitoring": {
                "title": "Unified Monitoring and Analytics",
                "description": "Example of monitoring both SI and APP activities from a single dashboard",
                "code": """
# Unified Monitoring Example
from taxpoynt_hybrid_sdk import TaxPoyntHybridClient

client = TaxPoyntHybridClient(api_key="your_hybrid_api_key")

# Get comprehensive dashboard
print("Getting unified dashboard...")
dashboard = client.hybrid.monitoring.get_dashboard()

print("=== SYSTEM INTEGRATION (SI) OVERVIEW ===")
si_overview = dashboard.si_overview
print(f"Active Connections:")
print(f"  - Payment Processors: {si_overview.payment_connections}")
print(f"  - ERP Systems: {si_overview.erp_connections}")
print(f"  - Total Data Sources: {si_overview.total_connections}")

print(f"\\nDocument Generation:")
print(f"  - Invoices Generated Today: {si_overview.documents_generated_today}")
print(f"  - Success Rate: {si_overview.generation_success_rate}%")

print("\\n=== ACCESS POINT PROVIDER (APP) OVERVIEW ===")
app_overview = dashboard.app_overview
print(f"FIRS Integration:")
print(f"  - Connectivity Status: {app_overview.firs_connectivity}")
print(f"  - Pending Submissions: {app_overview.pending_submissions}")
print(f"  - Success Rate (24h): {app_overview.success_rate_24h}%")

print(f"\\nTaxpayer Management:")
print(f"  - Total Taxpayers: {app_overview.total_taxpayers}")
print(f"  - Active This Month: {app_overview.active_taxpayers}")
print(f"  - Compliance Score: {app_overview.average_compliance_score}")

# Get cross-role analytics
print("\\n=== CROSS-ROLE ANALYTICS ===")
analytics = client.hybrid.analytics.get_cross_role(
    period="30d",
    breakdown="weekly"
)

print("Integration Efficiency:")
for week in analytics.weekly_breakdown:
    print(f"  Week {week.week}: {week.data_to_submission_ratio}% data→submission conversion")

# Check integration health
print("\\n=== INTEGRATION HEALTH ===")
health = client.hybrid.monitoring.health_check()

for component in health.components:
    status_icon = "✅" if component.status == "healthy" else "❌"
    print(f"{status_icon} {component.name}: {component.status}")
    if component.status != "healthy":
        print(f"    Issue: {component.issue_description}")

# Get alerts
print("\\n=== ACTIVE ALERTS ===")
alerts = client.hybrid.monitoring.get_alerts(severity="medium")

for alert in alerts.data:
    print(f"⚠️  {alert.category.upper()}: {alert.message}")
    print(f"    Severity: {alert.severity} | Time: {alert.created_at}")

# Workflow status
print("\\n=== ACTIVE WORKFLOWS ===")
workflows = client.hybrid.workflows.list_active()

for workflow in workflows.data:
    print(f"🔄 {workflow.workflow_type}")
    print(f"    Status: {workflow.status} | Progress: {workflow.progress_percentage}%")
    if workflow.status == "failed":
        print(f"    Error: {workflow.error_message}")
                """,
                "curl_example": """
# Get unified hybrid dashboard
curl -X GET "https://api.taxpoynt.com/api/v1/hybrid/monitoring/dashboard" \\
  -H "Authorization: Bearer YOUR_HYBRID_API_KEY"
                """
            }
        }
    
    def generate_unified_openapi_spec(self) -> Dict[str, Any]:
        """Generate unified OpenAPI specification combining SI, APP, and hybrid endpoints."""
        # Get individual specs
        si_spec = self.si_generator.generate_openapi_spec()
        app_spec = self.app_generator.generate_openapi_spec()
        
        # Create unified spec
        unified_spec = {
            "openapi": "3.0.2",
            "info": {
                "title": self.title,
                "description": self.description,
                "version": "1.0.0",
                "contact": {
                    "name": "TaxPoynt Hybrid Support",
                    "email": "info@taxpoynt.com",
                    "url": "https://docs.taxpoynt.com/hybrid"
                }
            },
            "servers": [
                {"url": "https://api.taxpoynt.com", "description": "Production"},
                {"url": "https://sandbox-api.taxpoynt.com", "description": "Sandbox"}
            ],
            "paths": {},
            "components": {
                "schemas": {},
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
                {"name": "Hybrid Workflows", "description": "End-to-end workflows combining SI and APP capabilities"},
                {"name": "Cross-Role Management", "description": "Management operations spanning SI and APP roles"},
                {"name": "Unified Monitoring", "description": "Unified monitoring and analytics for hybrid operations"},
                
                # Include SI tags
                {"name": "Financial Systems", "description": "Payment processor integration operations (SI)"},
                {"name": "ERP Integration", "description": "ERP system integration operations (SI)"},
                {"name": "Data Transformation", "description": "Data mapping and transformation (SI)"},
                {"name": "Certificate Management", "description": "Digital certificate operations (SI)"},
                {"name": "Document Processing", "description": "Document generation and processing (SI)"},
                {"name": "IRN/QR Generation", "description": "Invoice reference and QR code generation (SI)"},
                {"name": "Validation & Compliance", "description": "Data validation and compliance checking (SI)"},
                
                # Include APP tags
                {"name": "FIRS Integration", "description": "Direct submission and communication with FIRS (APP)"},
                {"name": "Transmission Management", "description": "Secure transmission channels and certificate management (APP)"},
                {"name": "Taxpayer Management", "description": "Taxpayer organization registration and management (APP)"},
                {"name": "Compliance Reporting", "description": "Compliance reports, metrics, and analytics (APP)"},
                {"name": "Webhook Services", "description": "Real-time notification and event handling (APP)"},
                {"name": "Status Management", "description": "System status, health monitoring, and alerts (APP)"}
            ]
        }
        
        # Merge schemas from SI and APP
        unified_spec["components"]["schemas"].update(si_spec["components"]["schemas"])
        unified_spec["components"]["schemas"].update(app_spec["components"]["schemas"])
        
        # Add hybrid-specific schemas
        hybrid_schemas = {
            "HybridWorkflow": {
                "type": "object",
                "properties": {
                    "workflow_id": {"type": "string"},
                    "workflow_type": {"type": "string", "enum": ["payment-to-firs", "erp-to-firs", "custom"]},
                    "status": {"type": "string", "enum": ["running", "completed", "failed", "partial"]},
                    "progress": {"type": "object"},
                    "si_operations": {"type": "array"},
                    "app_operations": {"type": "array"},
                    "results": {"type": "object"},
                    "created_at": {"type": "string", "format": "date-time"},
                    "estimated_completion": {"type": "string", "format": "date-time"}
                }
            },
            "OrganizationCapabilities": {
                "type": "object",
                "properties": {
                    "si_capabilities": {"type": "object"},
                    "app_capabilities": {"type": "object"},
                    "integration_status": {"type": "string"},
                    "total_connections": {"type": "integer"},
                    "active_workflows": {"type": "integer"}
                }
            },
            "HybridDashboard": {
                "type": "object",
                "properties": {
                    "si_overview": {"type": "object"},
                    "app_overview": {"type": "object"},
                    "integration_health": {"type": "object"},
                    "workflow_statistics": {"type": "object"},
                    "cross_role_metrics": {"type": "object"},
                    "recent_activities": {"type": "array"},
                    "alerts": {"type": "array"}
                }
            }
        }
        unified_spec["components"]["schemas"].update(hybrid_schemas)
        
        # Merge paths from SI and APP with role prefixes
        for path, methods in si_spec["paths"].items():
            unified_spec["paths"][path] = methods
            
        for path, methods in app_spec["paths"].items():
            unified_spec["paths"][path] = methods
        
        # Add hybrid-specific endpoints
        for category, endpoints_data in self.hybrid_endpoints.items():
            for endpoint in endpoints_data["endpoints"]:
                path = endpoint["path"]
                method = endpoint["method"].lower()
                
                if path not in unified_spec["paths"]:
                    unified_spec["paths"][path] = {}
                
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
                
                if "request_body" in endpoint:
                    operation["requestBody"] = {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": endpoint["request_body"]
                            }
                        }
                    }
                
                if "parameters" in endpoint:
                    operation["parameters"] = endpoint["parameters"]
                
                unified_spec["paths"][path][method] = operation
        
        return unified_spec
    
    def generate_html_documentation(self) -> str:
        """Generate comprehensive HTML documentation for hybrid users."""
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #1f2937 0%, #dc2626 100%); color: white; padding: 20px; margin: -20px -20px 20px -20px; }}
        .section {{ margin: 20px 0; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px; }}
        .workflow {{ background: #f0f9ff; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid #0ea5e9; }}
        .si-section {{ background: #f0fdf4; border-left: 4px solid #22c55e; }}
        .app-section {{ background: #fef2f2; border-left: 4px solid #dc2626; }}
        .hybrid-section {{ background: #faf5ff; border-left: 4px solid #8b5cf6; }}
        .step {{ background: white; padding: 10px; margin: 5px 0; border-radius: 4px; border: 1px solid #e5e7eb; }}
        .step-number {{ display: inline-block; background: #3b82f6; color: white; width: 24px; height: 24px; border-radius: 50%; text-align: center; line-height: 24px; font-weight: bold; margin-right: 10px; }}
        .role-badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .si-badge {{ background: #dcfce7; color: #166534; }}
        .app-badge {{ background: #fecaca; color: #991b1b; }}
        .code {{ background: #1f2937; color: #f9fafb; padding: 15px; border-radius: 6px; overflow-x: auto; }}
        .example {{ margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>Complete API documentation for Hybrid users with both SI and APP capabilities</p>
    </div>
    
    <div class="section">
        <h2>Hybrid Overview</h2>
        {description}
    </div>
    
    <div class="section hybrid-section">
        <h2>🔄 End-to-End Workflows</h2>
        {workflows_html}
    </div>
    
    <div class="section si-section">
        <h2>🔧 System Integration (SI) Capabilities</h2>
        <p>Use these APIs to collect, transform, and prepare data for e-invoicing:</p>
        <ul>
            <li><strong>Financial Systems:</strong> Payment processors (Paystack, Moniepoint, OPay, PalmPay, Interswitch, Flutterwave, Stripe)</li>
            <li><strong>ERP Integration:</strong> Business systems (Odoo, SAP, Dynamics, NetSuite)</li>
            <li><strong>Data Transformation:</strong> Convert data to e-invoice standards</li>
            <li><strong>Document Generation:</strong> Create UBL-compliant invoices</li>
        </ul>
    </div>
    
    <div class="section app-section">
        <h2>🏛️ Access Point Provider (APP) Capabilities</h2>
        <p>Use these APIs to submit to FIRS and manage compliance:</p>
        <ul>
            <li><strong>FIRS Integration:</strong> Direct submission to FIRS systems</li>
            <li><strong>Taxpayer Management:</strong> Register and manage taxpayer organizations</li>
            <li><strong>Compliance Reporting:</strong> Generate regulatory reports and analytics</li>
            <li><strong>Status Monitoring:</strong> Real-time submission tracking</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>Integration Examples</h2>
        {examples_html}
    </div>
    
    <div class="section">
        <h2>Support</h2>
        <p>For Hybrid API support, contact:</p>
        <ul>
            <li>Email: info@taxpoynt.com</li>
            <li>SI Support: info@taxpoynt.com</li>
            <li>APP Support: info@taxpoynt.com</li>
            <li>Documentation: https://docs.taxpoynt.com/hybrid</li>
        </ul>
    </div>
</body>
</html>
        """
        
        # Generate workflows HTML
        workflows_html = ""
        for workflow_key, workflow_data in self.hybrid_workflows.items():
            workflows_html += f'''
            <div class="workflow">
                <h3>{workflow_data["name"]}</h3>
                <p>{workflow_data["description"]}</p>
                <div class="steps">
            '''
            
            for step in workflow_data["steps"]:
                role_badge_class = "si-badge" if step["role"] == "SI" else "app-badge"
                workflows_html += f'''
                <div class="step">
                    <span class="step-number">{step["step"]}</span>
                    <span class="role-badge {role_badge_class}">{step["role"]}</span>
                    <strong>{step["name"]}</strong>
                    <p>{step["description"]}</p>
                    <small>API Calls: {", ".join(step["api_calls"])}</small>
                </div>
                '''
            
            workflows_html += "</div></div>"
        
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
            workflows_html=workflows_html,
            examples_html=examples_html
        )
    
    def export_documentation(self, output_dir: str) -> Dict[str, str]:
        """Export comprehensive hybrid documentation."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        files_created = {}
        
        # Export unified OpenAPI spec
        unified_spec = self.generate_unified_openapi_spec()
        openapi_file = output_path / "hybrid_api_openapi.json"
        with open(openapi_file, "w") as f:
            json.dump(unified_spec, f, indent=2)
        files_created["openapi"] = str(openapi_file)
        
        # Export HTML documentation
        html_doc = self.generate_html_documentation()
        html_file = output_path / "hybrid_api_documentation.html"
        with open(html_file, "w") as f:
            f.write(html_doc)
        files_created["html"] = str(html_file)
        
        # Export workflows
        workflows_file = output_path / "hybrid_workflows.json"
        with open(workflows_file, "w") as f:
            json.dump(self.hybrid_workflows, f, indent=2)
        files_created["workflows"] = str(workflows_file)
        
        # Export integration examples
        examples_file = output_path / "hybrid_integration_examples.json"
        with open(examples_file, "w") as f:
            json.dump(self.integration_examples, f, indent=2)
        files_created["examples"] = str(examples_file)
        
        return files_created


def generate_hybrid_api_docs(output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Generate complete hybrid API documentation."""
    generator = HybridAPIDocumentationGenerator()
    
    if output_dir:
        files = generator.export_documentation(output_dir)
        return {
            "status": "success",
            "files_created": files,
            "openapi_spec": generator.generate_unified_openapi_spec()
        }
    
    return {
        "status": "success",
        "openapi_spec": generator.generate_unified_openapi_spec(),
        "html_documentation": generator.generate_html_documentation(),
        "workflows": generator.hybrid_workflows,
        "integration_examples": generator.integration_examples
    }


# Export main functionality
__all__ = [
    "HybridAPIDocumentationGenerator",
    "generate_hybrid_api_docs"
]