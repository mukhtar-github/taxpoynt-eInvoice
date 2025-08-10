"""
Wave Data Extractor
Extracts and normalizes invoice data from Wave Accounting for e-invoicing compliance.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from .rest_client import WaveRestClient
from .exceptions import (
    WaveDataError,
    WaveValidationError,
    WaveBusinessNotFoundError,
    WaveCustomerNotFoundError,
    WaveInvoiceNotFoundError
)


logger = logging.getLogger(__name__)


class WaveDataExtractor:
    """
    Extracts and normalizes invoice data from Wave Accounting.
    
    Handles Wave's GraphQL API structure and converts it to standardized
    format for UBL transformation and FIRS e-invoicing compliance.
    """
    
    # Wave invoice statuses
    VALID_INVOICE_STATUSES = {
        "DRAFT", "SENT", "VIEWED", "OVERDUE", "PAID", "PARTIALLY_PAID"
    }
    
    # Currency codes supported for Nigerian e-invoicing
    SUPPORTED_CURRENCIES = {"NGN", "USD", "EUR", "GBP"}
    
    def __init__(self, rest_client: WaveRestClient):
        """
        Initialize Wave data extractor.
        
        Args:
            rest_client: Wave REST client instance
        """
        self.rest_client = rest_client
    
    async def extract_business_info(self, business_id: str) -> Dict[str, Any]:
        """
        Extract business information from Wave.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            Normalized business information
        """
        try:
            business = await self.rest_client.get_business(business_id)
            
            # Extract address information
            address = business.get("address", {})
            
            return {
                "id": business.get("id"),
                "name": business.get("name"),
                "organization_name": business.get("organizationName"),
                "business_type": business.get("businessType"),
                "currency": {
                    "code": business.get("currency", {}).get("code"),
                    "symbol": business.get("currency", {}).get("symbol")
                },
                "address": {
                    "line1": address.get("addressLine1"),
                    "line2": address.get("addressLine2"),
                    "city": address.get("city"),
                    "postal_code": address.get("postalCode"),
                    "country_code": address.get("countryCode"),
                    "province_code": address.get("provinceCode")
                },
                "timezone": business.get("timezone"),
                "created_at": business.get("createdAt"),
                "modified_at": business.get("modifiedAt")
            }
            
        except Exception as e:
            logger.error(f"Failed to extract business info: {e}")
            raise WaveDataError(f"Failed to extract business information: {str(e)}")
    
    async def extract_customers(
        self,
        business_id: str,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract customers from Wave.
        
        Args:
            business_id: Wave business ID
            modified_since: Only return customers modified since this date
            limit: Maximum number of customers to return
            
        Returns:
            List of normalized customer objects
        """
        customers = []
        cursor = None
        
        try:
            while True:
                page_limit = min(50, limit - len(customers)) if limit else 50
                if page_limit <= 0:
                    break
                
                response = await self.rest_client.get_customers(
                    business_id=business_id,
                    limit=page_limit,
                    cursor=cursor,
                    modified_since=modified_since
                )
                
                for edge in response.get("edges", []):
                    customer = edge.get("node", {})
                    address = customer.get("address", {})
                    
                    normalized_customer = {
                        "id": customer.get("id"),
                        "name": customer.get("name"),
                        "display_id": customer.get("displayId"),
                        "email": customer.get("email"),
                        "first_name": customer.get("firstName"),
                        "last_name": customer.get("lastName"),
                        "address": {
                            "line1": address.get("addressLine1"),
                            "line2": address.get("addressLine2"),
                            "city": address.get("city"),
                            "postal_code": address.get("postalCode"),
                            "country_code": address.get("countryCode"),
                            "province_code": address.get("provinceCode")
                        },
                        "phone": customer.get("phone"),
                        "fax": customer.get("fax"),
                        "mobile": customer.get("mobile"),
                        "toll_free": customer.get("tollFree"),
                        "website": customer.get("website"),
                        "currency": {
                            "code": customer.get("currency", {}).get("code"),
                            "symbol": customer.get("currency", {}).get("symbol")
                        },
                        "created_at": customer.get("createdAt"),
                        "modified_at": customer.get("modifiedAt")
                    }
                    
                    customers.append(normalized_customer)
                
                # Check if there's more data
                page_info = response.get("pageInfo", {})
                if not page_info.get("hasNextPage") or (limit and len(customers) >= limit):
                    break
                
                cursor = page_info.get("endCursor")
            
            logger.info(f"Extracted {len(customers)} customers from Wave")
            return customers
            
        except Exception as e:
            logger.error(f"Failed to extract customers: {e}")
            raise WaveDataError(f"Failed to extract customers: {str(e)}")
    
    async def extract_products(
        self,
        business_id: str,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract products from Wave.
        
        Args:
            business_id: Wave business ID
            modified_since: Only return products modified since this date
            limit: Maximum number of products to return
            
        Returns:
            List of normalized product objects
        """
        products = []
        cursor = None
        
        try:
            while True:
                page_limit = min(50, limit - len(products)) if limit else 50
                if page_limit <= 0:
                    break
                
                response = await self.rest_client.get_products(
                    business_id=business_id,
                    limit=page_limit,
                    cursor=cursor,
                    modified_since=modified_since
                )
                
                for edge in response.get("edges", []):
                    product = edge.get("node", {})
                    
                    # Extract tax information
                    taxes = []
                    for tax in product.get("defaultSalesTaxes", []):
                        taxes.append({
                            "id": tax.get("id"),
                            "name": tax.get("name"),
                            "rate": float(tax.get("rate", 0))
                        })
                    
                    normalized_product = {
                        "id": product.get("id"),
                        "name": product.get("name"),
                        "description": product.get("description"),
                        "unit_price": float(product.get("unitPrice", 0)),
                        "default_taxes": taxes,
                        "is_archived": product.get("isArchived", False),
                        "created_at": product.get("createdAt"),
                        "modified_at": product.get("modifiedAt")
                    }
                    
                    products.append(normalized_product)
                
                # Check if there's more data
                page_info = response.get("pageInfo", {})
                if not page_info.get("hasNextPage") or (limit and len(products) >= limit):
                    break
                
                cursor = page_info.get("endCursor")
            
            logger.info(f"Extracted {len(products)} products from Wave")
            return products
            
        except Exception as e:
            logger.error(f"Failed to extract products: {e}")
            raise WaveDataError(f"Failed to extract products: {str(e)}")
    
    async def extract_invoices(
        self,
        business_id: str,
        modified_since: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract invoices from Wave.
        
        Args:
            business_id: Wave business ID
            modified_since: Only return invoices modified since this date
            status_filter: Filter by invoice status
            limit: Maximum number of invoices to return
            
        Returns:
            List of normalized invoice objects
        """
        if status_filter and status_filter not in self.VALID_INVOICE_STATUSES:
            raise WaveValidationError(f"Invalid status filter: {status_filter}")
        
        invoices = []
        cursor = None
        
        try:
            while True:
                page_limit = min(50, limit - len(invoices)) if limit else 50
                if page_limit <= 0:
                    break
                
                response = await self.rest_client.get_invoices(
                    business_id=business_id,
                    limit=page_limit,
                    cursor=cursor,
                    modified_since=modified_since,
                    status_filter=status_filter
                )
                
                for edge in response.get("edges", []):
                    invoice = edge.get("node", {})
                    normalized_invoice = await self._normalize_invoice(invoice)
                    invoices.append(normalized_invoice)
                
                # Check if there's more data
                page_info = response.get("pageInfo", {})
                if not page_info.get("hasNextPage") or (limit and len(invoices) >= limit):
                    break
                
                cursor = page_info.get("endCursor")
            
            logger.info(f"Extracted {len(invoices)} invoices from Wave")
            return invoices
            
        except Exception as e:
            logger.error(f"Failed to extract invoices: {e}")
            raise WaveDataError(f"Failed to extract invoices: {str(e)}")
    
    async def extract_invoice_by_id(self, business_id: str, invoice_id: str) -> Dict[str, Any]:
        """
        Extract a specific invoice by ID.
        
        Args:
            business_id: Wave business ID
            invoice_id: Wave invoice ID
            
        Returns:
            Normalized invoice object
        """
        try:
            # Since Wave's GraphQL doesn't have a direct invoice by ID query,
            # we'll search through recent invoices
            invoices = await self.extract_invoices(
                business_id=business_id,
                limit=100  # Search recent invoices
            )
            
            for invoice in invoices:
                if invoice["id"] == invoice_id:
                    return invoice
            
            raise WaveInvoiceNotFoundError(f"Invoice {invoice_id} not found")
            
        except WaveInvoiceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract invoice {invoice_id}: {e}")
            raise WaveDataError(f"Failed to extract invoice: {str(e)}")
    
    async def _normalize_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Wave invoice data to standard format.
        
        Args:
            invoice: Raw Wave invoice data
            
        Returns:
            Normalized invoice object
        """
        try:
            customer = invoice.get("customer", {})
            
            # Extract monetary amounts
            amount_due = invoice.get("amountDue", {})
            amount_paid = invoice.get("amountPaid", {})
            tax_total = invoice.get("taxTotal", {})
            total = invoice.get("total", {})
            
            # Extract line items
            line_items = []
            for item in invoice.get("items", []):
                product = item.get("product", {})
                subtotal = item.get("subtotal", {})
                item_total = item.get("total", {})
                
                # Extract item taxes
                item_taxes = []
                for tax in item.get("taxes", []):
                    sales_tax = tax.get("salesTax", {})
                    tax_amount = tax.get("amount", {})
                    
                    item_taxes.append({
                        "id": sales_tax.get("id"),
                        "name": sales_tax.get("name"),
                        "rate": float(sales_tax.get("rate", 0)),
                        "amount": float(tax_amount.get("value", 0))
                    })
                
                line_items.append({
                    "product_id": product.get("id"),
                    "product_name": product.get("name"),
                    "description": item.get("description"),
                    "quantity": float(item.get("quantity", 0)),
                    "unit_price": float(item.get("price", 0)),
                    "subtotal": float(subtotal.get("value", 0)),
                    "total": float(item_total.get("value", 0)),
                    "taxes": item_taxes
                })
            
            # Get currency code
            currency_code = total.get("currency", {}).get("code", "NGN")
            
            # Validate currency
            if currency_code not in self.SUPPORTED_CURRENCIES:
                logger.warning(f"Unsupported currency: {currency_code}")
            
            normalized_invoice = {
                "id": invoice.get("id"),
                "invoice_number": invoice.get("invoiceNumber"),
                "po_number": invoice.get("poNumber"),
                "title": invoice.get("title"),
                "subhead": invoice.get("subhead"),
                "customer": {
                    "id": customer.get("id"),
                    "name": customer.get("name"),
                    "email": customer.get("email")
                },
                "dates": {
                    "invoice_date": invoice.get("invoiceDate"),
                    "due_date": invoice.get("dueDate"),
                    "created_at": invoice.get("createdAt"),
                    "modified_at": invoice.get("modifiedAt")
                },
                "amounts": {
                    "subtotal": sum(item["subtotal"] for item in line_items),
                    "tax_total": float(tax_total.get("value", 0)),
                    "total": float(total.get("value", 0)),
                    "amount_due": float(amount_due.get("value", 0)),
                    "amount_paid": float(amount_paid.get("value", 0)),
                    "currency_code": currency_code
                },
                "exchange_rate": float(invoice.get("exchangeRate", 1.0)),
                "line_items": line_items,
                "status": invoice.get("status"),
                "metadata": {
                    "wave_id": invoice.get("id"),
                    "extracted_at": datetime.utcnow().isoformat()
                }
            }
            
            return normalized_invoice
            
        except Exception as e:
            logger.error(f"Failed to normalize invoice: {e}")
            raise WaveDataError(f"Failed to normalize invoice data: {str(e)}")
    
    async def extract_sales_taxes(self, business_id: str) -> List[Dict[str, Any]]:
        """
        Extract sales tax configurations from Wave.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            List of normalized sales tax objects
        """
        try:
            taxes = await self.rest_client.get_sales_taxes(business_id)
            
            normalized_taxes = []
            for tax in taxes:
                normalized_taxes.append({
                    "id": tax.get("id"),
                    "name": tax.get("name"),
                    "abbreviation": tax.get("abbreviation"),
                    "description": tax.get("description"),
                    "rate": float(tax.get("rate", 0)),
                    "is_compound": tax.get("isCompound", False),
                    "is_recoverable": tax.get("isRecoverable", False),
                    "show_tax_number": tax.get("showTaxNumberOnInvoices", False)
                })
            
            logger.info(f"Extracted {len(normalized_taxes)} sales taxes from Wave")
            return normalized_taxes
            
        except Exception as e:
            logger.error(f"Failed to extract sales taxes: {e}")
            raise WaveDataError(f"Failed to extract sales taxes: {str(e)}")
    
    async def validate_business_access(self, business_id: str) -> bool:
        """
        Validate that we have access to the specified business.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            True if access is valid
        """
        try:
            await self.rest_client.get_business(business_id)
            return True
        except WaveBusinessNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to validate business access: {e}")
            raise WaveDataError(f"Failed to validate business access: {str(e)}")
    
    def calculate_totals(self, line_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate invoice totals from line items.
        
        Args:
            line_items: List of normalized line items
            
        Returns:
            Dictionary with calculated totals
        """
        subtotal = sum(item.get("subtotal", 0) for item in line_items)
        tax_total = sum(
            sum(tax.get("amount", 0) for tax in item.get("taxes", []))
            for item in line_items
        )
        total = subtotal + tax_total
        
        return {
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": total
        }
    
    def get_supported_currencies(self) -> List[str]:
        """
        Get list of supported currencies for e-invoicing.
        
        Returns:
            List of currency codes
        """
        return list(self.SUPPORTED_CURRENCIES)
    
    def get_valid_invoice_statuses(self) -> List[str]:
        """
        Get list of valid Wave invoice statuses.
        
        Returns:
            List of status values
        """
        return list(self.VALID_INVOICE_STATUSES)