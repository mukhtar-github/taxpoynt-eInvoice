"""
FIRS Certification API Service

This service extends the existing FIRS service with enhanced capabilities
for certification testing, implementing the complete invoice lifecycle
using the tested sandbox credentials and endpoints.
"""

import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from decimal import Decimal

from app.core.config import settings
from app.utils.logger import get_logger
from app.services.firs_service import FIRSService

logger = get_logger(__name__)


class FIRSCertificationService(FIRSService):
    """
    Enhanced FIRS service for certification testing.
    
    Extends the base FIRSService with complete invoice lifecycle
    management using tested sandbox credentials and endpoints.
    """
    
    def __init__(self):
        super().__init__()
        # Certification sandbox credentials
        self.sandbox_base_url = "https://eivc-k6z6d.ondigitalocean.app"
        self.sandbox_api_key = "8730fe74-0bec-479d-8c45-cb68a25a5ad5"
        self.sandbox_api_secret = "7a94pgjpMmfbUbDLSmE6WkA5fjxCIJpj9Vok2cKUQNQAkFZJVudTLTd11nmn1CMpmDrbBzIv93hnrG9g8VUkbhKLBdxXg9fc7Fts"
        
        # Test environment configuration
        self.business_id = "800a1faf-4b81-4b6e-bbe0-cfeb6ca31d4a"
        self.test_supplier_party_id = "3543c01a-cdc5-40be-8648-e0d1dc029eac"
        self.test_supplier_address_id = "00ac7af7-247b-44ca-b1ae-c20567c4287b"
        
    def _get_certification_headers(self) -> Dict[str, str]:
        """Get headers for FIRS certification API requests."""
        return {
            "accept": "*/*",
            "x-api-key": self.sandbox_api_key,
            "x-api-secret": self.sandbox_api_secret,
            "Content-Type": "application/json"
        }
    
    def generate_irn(self, invoice_reference: str) -> str:
        """Generate IRN following FIRS template format."""
        today = datetime.now().strftime("%Y%m%d")
        return f"{invoice_reference}-59854B81-{today}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check FIRS sandbox API health."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api",
                    headers=self._get_certification_headers(),
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"FIRS health check failed: {e}")
                return {"healthy": False, "error": str(e)}
    
    async def validate_irn(
        self, 
        business_id: str, 
        invoice_reference: str, 
        irn: str
    ) -> Dict[str, Any]:
        """Validate IRN with FIRS."""
        payload = {
            "business_id": business_id,
            "invoice_reference": invoice_reference,
            "irn": irn
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/invoice/irn/validate",
                    json=payload,
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"IRN validation failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def validate_complete_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate complete invoice structure with FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/invoice/validate",
                    json=invoice_data,
                    headers=self._get_certification_headers(),
                    timeout=120.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice validation failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def sign_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sign invoice with FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/invoice/sign",
                    json=invoice_data,
                    headers=self._get_certification_headers(),
                    timeout=120.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice signing failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def transmit_invoice(self, irn: str) -> Dict[str, Any]:
        """Transmit invoice to FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/invoice/transmit/{irn}",
                    headers=self._get_certification_headers(),
                    timeout=120.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice transmission failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def confirm_invoice(self, irn: str) -> Dict[str, Any]:
        """Confirm invoice receipt from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/confirm/{irn}",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice confirmation failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def download_invoice(self, irn: str) -> Dict[str, Any]:
        """Download invoice from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/download/{irn}",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice download failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def create_party(self, party_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create party in FIRS."""
        party_payload = {
            "business_id": self.business_id,
            **party_data
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/invoice/party",
                    json=party_payload,
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Party creation failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def search_parties(self, page: int = 1, size: int = 10) -> Dict[str, Any]:
        """Search parties for the business."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/party/{self.business_id}",
                    params={"page": page, "size": size, "sort_by": "created_at", "sort_direction_desc": "true"},
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Party search failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def verify_tin(self, tin: str) -> Dict[str, Any]:
        """Verify TIN with FIRS."""
        payload = {"tin": tin}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.sandbox_base_url}/api/v1/utilities/verify-tin/",
                    json=payload,
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"TIN verification failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def get_countries(self) -> Dict[str, Any]:
        """Get list of countries from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/resources/countries",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Countries fetch failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def get_invoice_types(self) -> Dict[str, Any]:
        """Get list of invoice types from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/resources/invoice-types",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Invoice types fetch failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def get_currencies(self) -> Dict[str, Any]:
        """Get list of currencies from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/resources/currencies",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Currencies fetch failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def get_vat_exemptions(self) -> Dict[str, Any]:
        """Get VAT exemption codes from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/resources/vat-exemptions",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"VAT exemptions fetch failed: {e}")
                return {"code": 500, "error": str(e)}
    
    async def get_service_codes(self) -> Dict[str, Any]:
        """Get service codes from FIRS."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.sandbox_base_url}/api/v1/invoice/resources/services-codes",
                    headers=self._get_certification_headers(),
                    timeout=60.0
                )
                return response.json()
            except httpx.RequestError as e:
                logger.error(f"Service codes fetch failed: {e}")
                return {"code": 500, "error": str(e)}
    
    def build_complete_invoice(
        self,
        invoice_reference: str,
        customer_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]],
        issue_date: Optional[date] = None,
        due_date: Optional[date] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build complete invoice structure for FIRS validation."""
        
        if issue_date is None:
            issue_date = date.today()
            
        # Calculate monetary totals
        line_extension_amount = sum(float(line["line_extension_amount"]) for line in invoice_lines)
        tax_amount = line_extension_amount * 0.075  # 7.5% VAT
        
        invoice = {
            "business_id": self.business_id,
            "irn": self.generate_irn(invoice_reference),
            "issue_date": issue_date.isoformat(),
            "invoice_type_code": "396",  # Invoice Request
            "document_currency_code": "NGN",
            "tax_currency_code": "NGN",
            "accounting_supplier_party": {
                "id": self.test_supplier_party_id,
                "postal_address_id": self.test_supplier_address_id
            },
            "accounting_customer_party": self._build_customer_party(customer_data),
            "legal_monetary_total": {
                "line_extension_amount": line_extension_amount,
                "tax_exclusive_amount": line_extension_amount,
                "tax_inclusive_amount": line_extension_amount + tax_amount,
                "payable_amount": line_extension_amount + tax_amount
            },
            "invoice_line": self._build_invoice_lines(invoice_lines)
        }
        
        # Add optional fields
        if due_date:
            invoice["due_date"] = due_date.isoformat()
        if kwargs.get("issue_time"):
            invoice["issue_time"] = kwargs["issue_time"]
        if kwargs.get("note"):
            invoice["note"] = kwargs["note"]
        if kwargs.get("payment_status"):
            invoice["payment_status"] = kwargs["payment_status"]
        else:
            invoice["payment_status"] = "PENDING"
            
        return invoice
    
    def _build_customer_party(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build customer party structure."""
        customer_party = {
            "party_name": customer_data["party_name"],
            "tin": customer_data["tin"],
            "email": customer_data["email"]
        }
        
        if customer_data.get("telephone"):
            customer_party["telephone"] = customer_data["telephone"]
        if customer_data.get("business_description"):
            customer_party["business_description"] = customer_data["business_description"]
            
        # Handle postal address
        if customer_data.get("postal_address_id"):
            customer_party["postal_address_id"] = customer_data["postal_address_id"]
        elif customer_data.get("postal_address"):
            customer_party["postal_address"] = customer_data["postal_address"]
        else:
            raise ValueError("Either postal_address_id or postal_address must be provided")
            
        return customer_party
    
    def _build_invoice_lines(self, invoice_lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build invoice lines structure."""
        built_lines = []
        
        for line in invoice_lines:
            built_line = {
                "hsn_code": line.get("hsn_code", "CC-001"),
                "product_category": line.get("product_category", "Technology Services"),
                "invoiced_quantity": line["invoiced_quantity"],
                "line_extension_amount": float(line["line_extension_amount"]),
                "item": {
                    "name": line["item"]["name"],
                    "description": line["item"]["description"]
                },
                "price": {
                    "price_amount": float(line["price"]["price_amount"]),
                    "base_quantity": line["price"]["base_quantity"],
                    "price_unit": line["price"]["price_unit"]
                }
            }
            
            # Add optional line fields
            if line.get("discount_rate"):
                built_line["discount_rate"] = line["discount_rate"]
            if line.get("discount_amount"):
                built_line["discount_amount"] = line["discount_amount"]
            if line.get("fee_rate"):
                built_line["fee_rate"] = line["fee_rate"]
            if line.get("fee_amount"):
                built_line["fee_amount"] = line["fee_amount"]
                
            built_lines.append(built_line)
            
        return built_lines


# Create service instance
firs_certification_service = FIRSCertificationService()