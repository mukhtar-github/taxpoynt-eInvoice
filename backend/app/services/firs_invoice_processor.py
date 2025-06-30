"""
FIRS Invoice Processor for Complete Lifecycle Management

This service orchestrates the complete invoice lifecycle for FIRS certification:
validate → sign → transmit → confirm → download
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import logging

from app.services.firs_certification_service import firs_certification_service
from app.utils.logger import get_logger

logger = get_logger(__name__)


class FIRSInvoiceProcessor:
    """
    Complete invoice processor for FIRS certification workflow.
    
    Handles the end-to-end invoice processing lifecycle using the
    tested FIRS sandbox environment and credentials.
    """
    
    def __init__(self):
        self.firs_service = firs_certification_service
        
    async def process_complete_invoice_lifecycle(
        self,
        invoice_reference: str,
        customer_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]],
        issue_date: Optional[date] = None,
        due_date: Optional[date] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process complete invoice lifecycle: validate → sign → transmit → confirm.
        
        Args:
            invoice_reference: Unique invoice reference number
            customer_data: Customer/buyer information
            invoice_lines: List of invoice line items
            issue_date: Invoice issue date (defaults to today)
            due_date: Invoice due date (optional)
            **kwargs: Additional invoice parameters
            
        Returns:
            Dictionary containing complete processing results and status
        """
        
        results = {
            "invoice_reference": invoice_reference,
            "irn": None,
            "status": "initiated",
            "steps": {},
            "success": False,
            "errors": []
        }
        
        try:
            logger.info(f"Starting complete invoice lifecycle for: {invoice_reference}")
            
            # Step 1: Build complete invoice structure
            logger.info(f"Building invoice structure for: {invoice_reference}")
            invoice_data = self.firs_service.build_complete_invoice(
                invoice_reference=invoice_reference,
                customer_data=customer_data,
                invoice_lines=invoice_lines,
                issue_date=issue_date,
                due_date=due_date,
                **kwargs
            )
            
            results["irn"] = invoice_data["irn"]
            results["invoice_data"] = invoice_data
            results["status"] = "invoice_built"
            
            # Step 2: Validate IRN
            logger.info(f"Validating IRN: {invoice_data['irn']}")
            irn_validation = await self.firs_service.validate_irn(
                business_id=self.firs_service.business_id,
                invoice_reference=invoice_reference,
                irn=invoice_data["irn"]
            )
            results["steps"]["irn_validation"] = irn_validation
            
            if irn_validation.get("code") != 200:
                logger.warning(f"IRN validation issues: {irn_validation}")
                results["errors"].append(f"IRN validation: {irn_validation.get('message', 'Unknown error')}")
                # Continue with invoice validation even if IRN validation has issues
            
            # Step 3: Validate complete invoice
            logger.info(f"Validating complete invoice: {invoice_data['irn']}")
            invoice_validation = await self.firs_service.validate_complete_invoice(invoice_data)
            results["steps"]["invoice_validation"] = invoice_validation
            
            if invoice_validation.get("code") != 200:
                logger.error(f"Invoice validation failed: {invoice_validation}")
                results["errors"].append(f"Invoice validation: {invoice_validation.get('message', 'Unknown error')}")
                results["status"] = "validation_failed"
                return results
            
            results["status"] = "validated"
            
            # Step 4: Sign invoice
            logger.info(f"Signing invoice: {invoice_data['irn']}")
            invoice_signing = await self.firs_service.sign_invoice(invoice_data)
            results["steps"]["invoice_signing"] = invoice_signing
            
            if invoice_signing.get("code") != 200:
                logger.error(f"Invoice signing failed: {invoice_signing}")
                results["errors"].append(f"Invoice signing: {invoice_signing.get('message', 'Unknown error')}")
                results["status"] = "signing_failed"
                return results
            
            results["status"] = "signed"
            
            # Step 5: Transmit invoice
            logger.info(f"Transmitting invoice: {invoice_data['irn']}")
            invoice_transmission = await self.firs_service.transmit_invoice(invoice_data["irn"])
            results["steps"]["invoice_transmission"] = invoice_transmission
            
            if invoice_transmission.get("code") != 200:
                logger.error(f"Invoice transmission failed: {invoice_transmission}")
                results["errors"].append(f"Invoice transmission: {invoice_transmission.get('message', 'Unknown error')}")
                results["status"] = "transmission_failed"
                return results
            
            results["status"] = "transmitted"
            
            # Step 6: Confirm invoice
            logger.info(f"Confirming invoice: {invoice_data['irn']}")
            invoice_confirmation = await self.firs_service.confirm_invoice(invoice_data["irn"])
            results["steps"]["invoice_confirmation"] = invoice_confirmation
            
            if invoice_confirmation.get("code") != 200:
                logger.warning(f"Invoice confirmation issues: {invoice_confirmation}")
                results["errors"].append(f"Invoice confirmation: {invoice_confirmation.get('message', 'Unknown error')}")
                # Don't fail here as confirmation might be pending
            
            # Step 7: Download invoice (optional)
            logger.info(f"Downloading invoice: {invoice_data['irn']}")
            invoice_download = await self.firs_service.download_invoice(invoice_data["irn"])
            results["steps"]["invoice_download"] = invoice_download
            
            if invoice_download.get("code") != 200:
                logger.warning(f"Invoice download issues: {invoice_download}")
                results["errors"].append(f"Invoice download: {invoice_download.get('message', 'Unknown error')}")
                # Don't fail here as download might not be immediately available
            
            # Final status assessment
            if len(results["errors"]) == 0:
                results["status"] = "completed"
                results["success"] = True
            elif results["status"] in ["transmitted", "signed"]:
                results["status"] = "partially_completed"
                results["success"] = True
            else:
                results["status"] = "failed"
                results["success"] = False
            
            logger.info(f"Invoice lifecycle completed for {invoice_reference}: {results['status']}")
            
        except Exception as e:
            logger.error(f"Error processing invoice lifecycle: {str(e)}", exc_info=True)
            results["status"] = "error"
            results["success"] = False
            results["errors"].append(f"Processing error: {str(e)}")
        
        return results
    
    async def create_customer_party(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer party in FIRS if not exists."""
        party_data = {
            "party_name": customer_data["party_name"],
            "tin": customer_data["tin"],
            "email": customer_data["email"]
        }
        
        if customer_data.get("telephone"):
            party_data["telephone"] = customer_data["telephone"]
        if customer_data.get("business_description"):
            party_data["business_description"] = customer_data["business_description"]
        if customer_data.get("postal_address"):
            party_data["postal_address"] = customer_data["postal_address"]
            
        return await self.firs_service.create_party(party_data)
    
    async def verify_customer_tin(self, tin: str) -> Dict[str, Any]:
        """Verify customer TIN with FIRS."""
        return await self.firs_service.verify_tin(tin)
    
    async def get_invoice_resources(self) -> Dict[str, Any]:
        """Get all required resources for invoice creation."""
        try:
            # Fetch all resources in parallel would be ideal, but for simplicity doing sequentially
            countries = await self.firs_service.get_countries()
            invoice_types = await self.firs_service.get_invoice_types()
            currencies = await self.firs_service.get_currencies()
            vat_exemptions = await self.firs_service.get_vat_exemptions()
            service_codes = await self.firs_service.get_service_codes()
            
            return {
                "countries": countries,
                "invoice_types": invoice_types,
                "currencies": currencies,
                "vat_exemptions": vat_exemptions,
                "service_codes": service_codes
            }
        except Exception as e:
            logger.error(f"Error fetching invoice resources: {str(e)}")
            return {"error": str(e)}
    
    async def test_firs_connectivity(self) -> Dict[str, Any]:
        """Test FIRS API connectivity and configuration."""
        try:
            health_result = await self.firs_service.health_check()
            
            # Test basic resource access
            countries_test = await self.firs_service.get_countries()
            
            return {
                "health_check": health_result,
                "resource_access": {
                    "countries_available": countries_test.get("code") == 200,
                    "total_countries": len(countries_test.get("data", [])) if countries_test.get("code") == 200 else 0
                },
                "configuration": {
                    "base_url": self.firs_service.sandbox_base_url,
                    "business_id": self.firs_service.business_id,
                    "supplier_party_id": self.firs_service.test_supplier_party_id
                },
                "connectivity_status": "operational" if health_result.get("healthy") else "issues_detected"
            }
        except Exception as e:
            logger.error(f"FIRS connectivity test failed: {str(e)}")
            return {
                "connectivity_status": "failed",
                "error": str(e)
            }


# Create processor instance
firs_invoice_processor = FIRSInvoiceProcessor()


class FIRSErrorHandler:
    """Error handler for FIRS API responses."""
    
    @staticmethod
    def handle_firs_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """Handle and standardize FIRS API responses."""
        
        # Handle successful responses
        if response.get("code") == 200 or response.get("code") == 201:
            return {
                "success": True,
                "data": response.get("data"),
                "message": "Operation completed successfully"
            }
        
        # Handle error responses
        error_info = response.get("error", {})
        error_message = error_info.get("public_message", "Unknown error")
        error_details = error_info.get("details", "")
        
        # Map common errors to user-friendly messages
        user_message = FIRSErrorHandler._get_user_friendly_message(error_message, error_details)
        
        return {
            "success": False,
            "error": {
                "code": response.get("code"),
                "message": user_message,
                "details": error_details,
                "original_message": error_message,
                "error_id": error_info.get("id"),
                "handler": error_info.get("handler")
            }
        }
    
    @staticmethod
    def _get_user_friendly_message(error_message: str, details: str) -> str:
        """Convert FIRS error messages to user-friendly messages."""
        
        common_errors = {
            "unable to validate api key": "API credentials are invalid or expired",
            "irn validation failed": "IRN format doesn't match template requirements",
            "validation failed": "Required fields are missing or invalid",
            "webhook url is not setup": "Webhook configuration required for transmission"
        }
        
        for pattern, friendly_message in common_errors.items():
            if pattern.lower() in error_message.lower():
                return friendly_message
        
        # Handle specific validation errors
        if "required" in details.lower():
            return f"Required field missing: {details}"
        
        if "invalid" in details.lower():
            return f"Invalid data provided: {details}"
        
        return error_message
    
    @staticmethod
    def get_retry_recommendation(error: Dict[str, Any]) -> Optional[str]:
        """Get retry recommendations for specific errors."""
        error_code = error.get("code")
        error_message = error.get("message", "").lower()
        
        if error_code == 429:
            return "Rate limit exceeded. Wait before retrying."
        
        if error_code >= 500:
            return "Server error. Retry after a few minutes."
        
        if "webhook" in error_message:
            return "Configure webhook URLs before attempting transmission."
        
        if "required field" in error_message:
            return "Provide all required fields and retry."
        
        if "irn" in error_message:
            return "Check IRN format matches template: {{invoice_id}}-59854B81-{{YYYYMMDD}}"
        
        return None


# Create error handler instance
firs_error_handler = FIRSErrorHandler()