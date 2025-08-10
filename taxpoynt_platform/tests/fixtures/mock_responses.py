"""
Mock Responses and Test Utilities
================================
Mock HTTP responses, API responses, and test utilities for TaxPoynt platform testing.
Based on real FIRS API responses and Nigerian e-invoicing system interactions.

These mocks simulate various scenarios including success, failure, and edge cases
commonly encountered in production Nigerian e-invoicing integrations.
"""

from datetime import datetime, date
from typing import Dict, Any, List, Optional
from enum import Enum
import json


class MockResponseType(str, Enum):
    """Types of mock responses available"""
    FIRS_SUCCESS = "firs_success"
    FIRS_ERROR = "firs_error" 
    FIRS_TIMEOUT = "firs_timeout"
    CONNECTOR_SUCCESS = "connector_success"
    CONNECTOR_ERROR = "connector_error"
    WEBHOOK_SUCCESS = "webhook_success"
    WEBHOOK_ERROR = "webhook_error"
    VALIDATION_SUCCESS = "validation_success"
    VALIDATION_ERROR = "validation_error"


class FIRSMockResponses:
    """Mock responses for FIRS API interactions"""
    
    @staticmethod
    def successful_invoice_submission() -> Dict[str, Any]:
        """Successful FIRS invoice submission response"""
        return {
            "status": "success",
            "message": "Invoice submitted successfully",
            "data": {
                "invoice_reference": "FIRS-2025-INV-001234567",
                "submission_timestamp": datetime.now().isoformat(),
                "validation_status": "passed",
                "invoice_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAASwAAAEsCAYAAAB5fY51...",
                "invoice_number": "INV-NG-2025-001",
                "total_amount": 349375.00,
                "currency": "NGN",
                "taxpayer_tin": "12345678901",
                "submission_id": "SUB-2025-001234",
                "firs_invoice_id": "FIRS-INV-2025-001234567"
            },
            "compliance": {
                "bis_billing_compliant": True,
                "firs_compliant": True,
                "validation_errors": [],
                "validation_warnings": []
            }
        }
    
    @staticmethod
    def failed_invoice_submission() -> Dict[str, Any]:
        """Failed FIRS invoice submission response"""
        return {
            "status": "error",
            "message": "Invoice submission failed",
            "error_code": "FIRS_VALIDATION_FAILED",
            "data": {
                "invoice_number": "INV-NG-2025-001",
                "submission_timestamp": datetime.now().isoformat(),
                "validation_status": "failed"
            },
            "errors": [
                {
                    "field": "accounting_supplier_party.party_tax_scheme.taxid",
                    "error": "Invalid TIN format. Must be 11 digits",
                    "error_code": "INVALID_TIN"
                },
                {
                    "field": "tax_total.tax_amount",
                    "error": "Tax amount calculation incorrect",
                    "error_code": "TAX_CALCULATION_ERROR"
                }
            ]
        }
    
    @staticmethod
    def firs_service_unavailable() -> Dict[str, Any]:
        """FIRS service unavailable response"""
        return {
            "status": "error",
            "message": "FIRS service temporarily unavailable",
            "error_code": "SERVICE_UNAVAILABLE",
            "data": {
                "retry_after": 300,  # 5 minutes
                "maintenance_message": "Scheduled maintenance in progress"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def authentication_failed() -> Dict[str, Any]:
        """FIRS authentication failed response"""
        return {
            "status": "error",
            "message": "Authentication failed",
            "error_code": "AUTH_FAILED",
            "data": {
                "reason": "Invalid certificate or credentials",
                "required_action": "Renew certificate or verify credentials"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def certificate_status_response(status: str = "valid") -> Dict[str, Any]:
        """FIRS certificate status response"""
        return {
            "status": "success",
            "data": {
                "certificate_status": status,
                "certificate_serial": "ABC123456789",
                "issued_date": "2024-01-15T00:00:00Z",
                "expiry_date": "2025-01-15T00:00:00Z",
                "issuer": "FIRS Certificate Authority",
                "subject": "TaxPoynt Solutions Ltd",
                "validity_period_remaining": 180  # days
            }
        }
    
    @staticmethod
    def health_check_response(healthy: bool = True) -> Dict[str, Any]:
        """FIRS health check response"""
        return {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "invoice_submission": "operational" if healthy else "degraded",
                "certificate_validation": "operational" if healthy else "down",
                "taxpayer_lookup": "operational" if healthy else "operational"
            },
            "response_time_ms": 150 if healthy else 5000
        }


class ConnectorMockResponses:
    """Mock responses for ERP/Financial system connectors"""
    
    @staticmethod
    def odoo_invoice_fetch_success() -> Dict[str, Any]:
        """Successful Odoo invoice fetch response"""
        return {
            "status": "success",
            "data": {
                "invoices": [
                    {
                        "id": 12345,
                        "name": "INV/2025/0001",
                        "date_invoice": "2025-01-15",
                        "partner_id": [67, "Nigerian Enterprise Ltd"],
                        "amount_total": 349375.00,
                        "amount_untaxed": 325000.00,
                        "amount_tax": 24375.00,
                        "currency_id": [1, "NGN"],
                        "state": "open",
                        "invoice_line_ids": [
                            {
                                "id": 123,
                                "name": "Office Chair Premium",
                                "quantity": 50.0,
                                "price_unit": 5000.0,
                                "price_subtotal": 250000.0,
                                "product_id": [1, "Office Chair Premium"]
                            }
                        ]
                    }
                ],
                "total_count": 1,
                "fetched_at": datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def sap_connection_success() -> Dict[str, Any]:
        """Successful SAP connection response"""
        return {
            "status": "connected",
            "connection_id": "sap-conn-001",
            "system_info": {
                "system_id": "PRD",
                "client": "100",
                "version": "SAP ECC 6.0",
                "language": "EN"
            },
            "capabilities": [
                "invoice_read",
                "customer_read", 
                "tax_calculation",
                "real_time_sync"
            ],
            "connected_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def connector_authentication_failed() -> Dict[str, Any]:
        """Connector authentication failed response"""
        return {
            "status": "error",
            "error_code": "AUTH_FAILED",
            "message": "Unable to authenticate with ERP system",
            "details": {
                "system": "Odoo",
                "endpoint": "https://erp.example.com/api/v1",
                "reason": "Invalid API key or credentials expired"
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def connector_health_check(system: str, healthy: bool = True) -> Dict[str, Any]:
        """Connector health check response"""
        return {
            "system": system,
            "status": "healthy" if healthy else "unhealthy",
            "last_sync": datetime.now().isoformat() if healthy else None,
            "response_time_ms": 200 if healthy else None,
            "error_count_24h": 0 if healthy else 15,
            "available_operations": [
                "fetch_invoices",
                "fetch_customers",
                "validate_connection"
            ] if healthy else []
        }


class WebhookMockResponses:
    """Mock responses for webhook integrations"""
    
    @staticmethod
    def webhook_delivery_success() -> Dict[str, Any]:
        """Successful webhook delivery response"""
        return {
            "status": "delivered",
            "webhook_id": "wh-2025-001234",
            "event_type": "invoice.submitted",
            "delivery_timestamp": datetime.now().isoformat(),
            "response_code": 200,
            "response_body": {"status": "received", "processed": True},
            "delivery_attempts": 1,
            "endpoint": "https://client.example.com/webhooks/taxpoynt"
        }
    
    @staticmethod
    def webhook_delivery_failed() -> Dict[str, Any]:
        """Failed webhook delivery response"""
        return {
            "status": "failed",
            "webhook_id": "wh-2025-001235",
            "event_type": "invoice.failed",
            "delivery_timestamp": datetime.now().isoformat(),
            "response_code": 500,
            "response_body": {"error": "Internal server error"},
            "delivery_attempts": 3,
            "endpoint": "https://client.example.com/webhooks/taxpoynt",
            "next_retry": (datetime.now().timestamp() + 300) * 1000  # 5 minutes
        }
    
    @staticmethod
    def webhook_registration_success() -> Dict[str, Any]:
        """Successful webhook registration response"""
        return {
            "status": "registered",
            "webhook_id": "wh-reg-001234",
            "endpoint": "https://client.example.com/webhooks/taxpoynt",
            "events": [
                "invoice.submitted",
                "invoice.failed",
                "invoice.validated",
                "certificate.expiring"
            ],
            "secret": "wh_secret_abc123xyz789",
            "created_at": datetime.now().isoformat(),
            "active": True
        }


class ValidationMockResponses:
    """Mock responses for validation services"""
    
    @staticmethod
    def validation_success() -> Dict[str, Any]:
        """Successful validation response"""
        return {
            "valid": True,
            "invoice_number": "INV-NG-2025-001",
            "validation_timestamp": datetime.now().isoformat(),
            "errors": [],
            "warnings": [],
            "schema_version": "BIS Billing 3.0",
            "validation_rules_applied": 47,
            "validation_duration_ms": 150
        }
    
    @staticmethod
    def validation_failed() -> Dict[str, Any]:
        """Failed validation response"""
        return {
            "valid": False,
            "invoice_number": "INV-NG-2025-001",
            "validation_timestamp": datetime.now().isoformat(),
            "errors": [
                {
                    "field": "accounting_supplier_party.party_tax_scheme.taxid",
                    "error": "TIN must be exactly 11 digits",
                    "error_code": "INVALID_TIN_FORMAT"
                },
                {
                    "field": "invoice_date",
                    "error": "Invoice date cannot be in the future",
                    "error_code": "FUTURE_DATE_NOT_ALLOWED"
                }
            ],
            "warnings": [
                {
                    "field": "due_date",
                    "error": "Due date is more than 90 days from invoice date",
                    "error_code": "LONG_PAYMENT_TERM"
                }
            ],
            "schema_version": "BIS Billing 3.0"
        }


class TestUtilities:
    """Utilities for testing"""
    
    @staticmethod
    def create_http_response(status_code: int, body: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Create a mock HTTP response"""
        return {
            "status_code": status_code,
            "headers": headers or {"Content-Type": "application/json"},
            "body": body,
            "elapsed_ms": 200
        }
    
    @staticmethod
    def create_timeout_response() -> Dict[str, Any]:
        """Create a timeout response"""
        return {
            "status_code": None,
            "error": "timeout",
            "message": "Request timed out after 30 seconds",
            "elapsed_ms": 30000
        }
    
    @staticmethod
    def create_network_error() -> Dict[str, Any]:
        """Create a network error response"""
        return {
            "status_code": None,
            "error": "network_error",
            "message": "Failed to establish connection",
            "details": "Connection refused or DNS resolution failed"
        }
    
    @staticmethod
    def simulate_rate_limit() -> Dict[str, Any]:
        """Simulate rate limiting response"""
        return {
            "status_code": 429,
            "headers": {
                "Content-Type": "application/json",
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(datetime.now().timestamp()) + 3600),
                "Retry-After": "3600"
            },
            "body": {
                "error": "rate_limit_exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 3600
            }
        }


class ScenarioMockResponses:
    """Complete scenario mock responses for end-to-end testing"""
    
    @staticmethod
    def complete_invoice_flow_success() -> Dict[str, List[Dict[str, Any]]]:
        """Complete successful invoice flow responses"""
        return {
            "connector_fetch": [ConnectorMockResponses.odoo_invoice_fetch_success()],
            "validation": [ValidationMockResponses.validation_success()],
            "firs_submission": [FIRSMockResponses.successful_invoice_submission()],
            "webhook_delivery": [WebhookMockResponses.webhook_delivery_success()]
        }
    
    @staticmethod
    def complete_invoice_flow_failure() -> Dict[str, List[Dict[str, Any]]]:
        """Complete failed invoice flow responses"""
        return {
            "connector_fetch": [ConnectorMockResponses.odoo_invoice_fetch_success()],
            "validation": [ValidationMockResponses.validation_failed()],
            "firs_submission": [FIRSMockResponses.failed_invoice_submission()],
            "webhook_delivery": [WebhookMockResponses.webhook_delivery_failed()]
        }
    
    @staticmethod
    def system_degraded_scenario() -> Dict[str, List[Dict[str, Any]]]:
        """System degraded scenario with various issues"""
        return {
            "firs_health": [FIRSMockResponses.health_check_response(healthy=False)],
            "connector_health": [ConnectorMockResponses.connector_health_check("Odoo", healthy=False)],
            "service_unavailable": [FIRSMockResponses.firs_service_unavailable()],
            "timeout": [TestUtilities.create_timeout_response()]
        }


# Export commonly used mock responses
COMMON_MOCKS = {
    "firs_success": FIRSMockResponses.successful_invoice_submission(),
    "firs_error": FIRSMockResponses.failed_invoice_submission(),
    "connector_success": ConnectorMockResponses.odoo_invoice_fetch_success(),
    "connector_error": ConnectorMockResponses.connector_authentication_failed(),
    "validation_success": ValidationMockResponses.validation_success(),
    "validation_error": ValidationMockResponses.validation_failed(),
    "webhook_success": WebhookMockResponses.webhook_delivery_success(),
    "webhook_error": WebhookMockResponses.webhook_delivery_failed(),
    "timeout": TestUtilities.create_timeout_response(),
    "rate_limit": TestUtilities.simulate_rate_limit()
}

# Export scenario mocks for complex testing
SCENARIO_MOCKS = {
    "success_flow": ScenarioMockResponses.complete_invoice_flow_success(),
    "failure_flow": ScenarioMockResponses.complete_invoice_flow_failure(),
    "degraded_system": ScenarioMockResponses.system_degraded_scenario()
}