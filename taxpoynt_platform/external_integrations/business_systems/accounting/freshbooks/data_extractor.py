"""
FreshBooks Data Extractor
Extracts and normalizes invoice data from FreshBooks for e-invoicing compliance.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from .rest_client import FreshBooksRestClient
from .exceptions import (
    FreshBooksDataError,
    FreshBooksValidationError,
    FreshBooksAccountNotFoundError,
    FreshBooksClientNotFoundError,
    FreshBooksInvoiceNotFoundError
)


logger = logging.getLogger(__name__)


class FreshBooksDataExtractor:
    """
    Extracts and normalizes invoice data from FreshBooks.
    
    Handles FreshBooks REST API structure and converts it to standardized
    format for UBL transformation and FIRS e-invoicing compliance.
    """
    
    # FreshBooks invoice statuses
    VALID_INVOICE_STATUSES = {
        "draft", "sent", "viewed", "paid", "auto-paid", "retry", "failed", 
        "partial", "disputed", "resolved"
    }
    
    # Currency codes supported for Nigerian e-invoicing
    SUPPORTED_CURRENCIES = {"NGN", "USD", "EUR", "GBP", "CAD"}
    
    def __init__(self, rest_client: FreshBooksRestClient):
        """
        Initialize FreshBooks data extractor.
        
        Args:
            rest_client: FreshBooks REST client instance
        """
        self.rest_client = rest_client
    
    async def extract_account_info(self, account_id: str) -> Dict[str, Any]:
        """
        Extract account information from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            
        Returns:
            Normalized account information
        """
        try:
            # Get identity info which contains account details
            identity_data = await self.rest_client.auth_manager.get_identity_info()
            
            if "response" not in identity_data:
                raise FreshBooksDataError("Invalid identity response format")
            
            user_data = identity_data["response"]
            
            # Find the specific business account
            business_account = None
            memberships = user_data.get("business_memberships", [])
            
            for membership in memberships:
                business = membership.get("business", {})
                if business.get("account_id") == account_id:
                    business_account = business
                    break
            
            if not business_account:
                raise FreshBooksAccountNotFoundError(f"Account {account_id} not found")
            
            return {
                "id": business_account.get("account_id"),
                "name": business_account.get("name"),
                "business_name": business_account.get("business_name"),
                "account_uuid": business_account.get("account_uuid"),
                "currency": {
                    "code": business_account.get("currency_code", "USD"),
                    "symbol": self._get_currency_symbol(business_account.get("currency_code", "USD"))
                },
                "address": {
                    "line1": business_account.get("address"),
                    "city": business_account.get("city"),
                    "province": business_account.get("province"),
                    "country": business_account.get("country"),
                    "postal_code": business_account.get("postal_code")
                },
                "phone": business_account.get("phone_number"),
                "created_at": business_account.get("date_joined"),
                "plan": business_account.get("plan"),
                "status": business_account.get("account_status")
            }
            
        except Exception as e:
            logger.error(f"Failed to extract account info: {e}")
            raise FreshBooksDataError(f"Failed to extract account information: {str(e)}")
    
    async def extract_clients(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract clients from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            updated_since: Only return clients updated since this date
            limit: Maximum number of clients to return
            
        Returns:
            List of normalized client objects
        """
        clients = []
        page = 1
        
        try:
            while True:
                per_page = min(100, limit - len(clients)) if limit else 100
                if per_page <= 0:
                    break
                
                response = await self.rest_client.get_clients(
                    account_id=account_id,
                    per_page=per_page,
                    page=page,
                    updated_since=updated_since
                )
                
                for client in response.get("clients", []):
                    normalized_client = {
                        "id": str(client.get("id")),
                        "organization": client.get("organization"),
                        "first_name": client.get("fname"),
                        "last_name": client.get("lname"),
                        "email": client.get("email"),
                        "display_name": self._build_client_display_name(client),
                        "address": {
                            "line1": client.get("s_street"),
                            "line2": client.get("s_street2"),
                            "city": client.get("s_city"),
                            "province": client.get("s_province"),
                            "country": client.get("s_country"),
                            "postal_code": client.get("s_code")
                        },
                        "phone": {
                            "business": client.get("bus_phone"),
                            "home": client.get("home_phone"),
                            "mobile": client.get("mob_phone")
                        },
                        "fax": client.get("fax"),
                        "website": client.get("website"),
                        "currency_code": client.get("currency_code"),
                        "language": client.get("language"),
                        "note": client.get("note"),
                        "vat_name": client.get("vat_name"),
                        "vat_number": client.get("vat_number"),
                        "created_at": client.get("created_at"),
                        "updated_at": client.get("updated_at"),
                        "vis_state": client.get("vis_state", 0)  # 0=active, 1=deleted
                    }
                    
                    clients.append(normalized_client)
                
                # Check if there's more data
                if len(response.get("clients", [])) < per_page:
                    break
                
                if limit and len(clients) >= limit:
                    break
                
                page += 1
            
            # Filter active clients
            active_clients = [c for c in clients if c["vis_state"] == 0]
            
            logger.info(f"Extracted {len(active_clients)} active clients from FreshBooks")
            return active_clients
            
        except Exception as e:
            logger.error(f"Failed to extract clients: {e}")
            raise FreshBooksDataError(f"Failed to extract clients: {str(e)}")
    
    async def extract_items(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract items from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            updated_since: Only return items updated since this date
            limit: Maximum number of items to return
            
        Returns:
            List of normalized item objects
        """
        items = []
        page = 1
        
        try:
            while True:
                per_page = min(100, limit - len(items)) if limit else 100
                if per_page <= 0:
                    break
                
                response = await self.rest_client.get_items(
                    account_id=account_id,
                    per_page=per_page,
                    page=page,
                    updated_since=updated_since
                )
                
                for item in response.get("items", []):
                    # Parse monetary values
                    unit_cost = self._parse_money_amount(item.get("unit_cost", {}))
                    
                    normalized_item = {
                        "id": str(item.get("id")),
                        "name": item.get("name"),
                        "description": item.get("description"),
                        "unit_cost": float(unit_cost),
                        "quantity": float(item.get("qty", 0)),
                        "inventory": item.get("inventory"),
                        "sku": item.get("sku"),
                        "tax1": item.get("tax1"),
                        "tax2": item.get("tax2"),
                        "created_at": item.get("created_at"),
                        "updated_at": item.get("updated_at"),
                        "vis_state": item.get("vis_state", 0)  # 0=active, 1=deleted
                    }
                    
                    items.append(normalized_item)
                
                # Check if there's more data
                if len(response.get("items", [])) < per_page:
                    break
                
                if limit and len(items) >= limit:
                    break
                
                page += 1
            
            # Filter active items
            active_items = [i for i in items if i["vis_state"] == 0]
            
            logger.info(f"Extracted {len(active_items)} active items from FreshBooks")
            return active_items
            
        except Exception as e:
            logger.error(f"Failed to extract items: {e}")
            raise FreshBooksDataError(f"Failed to extract items: {str(e)}")
    
    async def extract_invoices(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract invoices from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            updated_since: Only return invoices updated since this date
            status_filter: Filter by invoice status
            limit: Maximum number of invoices to return
            
        Returns:
            List of normalized invoice objects
        """
        if status_filter and status_filter not in self.VALID_INVOICE_STATUSES:
            raise FreshBooksValidationError(f"Invalid status filter: {status_filter}")
        
        invoices = []
        page = 1
        
        try:
            while True:
                per_page = min(100, limit - len(invoices)) if limit else 100
                if per_page <= 0:
                    break
                
                response = await self.rest_client.get_invoices(
                    account_id=account_id,
                    per_page=per_page,
                    page=page,
                    updated_since=updated_since,
                    status=status_filter
                )
                
                for invoice in response.get("invoices", []):
                    normalized_invoice = await self._normalize_invoice(invoice)
                    invoices.append(normalized_invoice)
                
                # Check if there's more data
                if len(response.get("invoices", [])) < per_page:
                    break
                
                if limit and len(invoices) >= limit:
                    break
                
                page += 1
            
            # Filter active invoices
            active_invoices = [i for i in invoices if i["vis_state"] == 0]
            
            logger.info(f"Extracted {len(active_invoices)} active invoices from FreshBooks")
            return active_invoices
            
        except Exception as e:
            logger.error(f"Failed to extract invoices: {e}")
            raise FreshBooksDataError(f"Failed to extract invoices: {str(e)}")
    
    async def extract_invoice_by_id(
        self, 
        invoice_id: str, 
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract a specific invoice by ID.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID
            
        Returns:
            Normalized invoice object
        """
        try:
            response = await self.rest_client.get_invoice(invoice_id, account_id)
            
            if "invoice" not in response:
                raise FreshBooksInvoiceNotFoundError(f"Invoice {invoice_id} not found")
            
            invoice = response["invoice"]
            return await self._normalize_invoice(invoice)
            
        except FreshBooksInvoiceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract invoice {invoice_id}: {e}")
            raise FreshBooksDataError(f"Failed to extract invoice: {str(e)}")
    
    async def _normalize_invoice(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize FreshBooks invoice data to standard format.
        
        Args:
            invoice: Raw FreshBooks invoice data
            
        Returns:
            Normalized invoice object
        """
        try:
            # Extract monetary amounts
            amount = self._parse_money_amount(invoice.get("amount", {}))
            outstanding = self._parse_money_amount(invoice.get("outstanding", {}))
            paid = self._parse_money_amount(invoice.get("paid", {}))
            
            # Extract line items
            line_items = []
            for line in invoice.get("lines", []):
                line_amount = self._parse_money_amount(line.get("amount", {}))
                unit_cost = self._parse_money_amount(line.get("unit_cost", {}))
                
                # Extract taxes for line item
                line_taxes = []
                if line.get("tax1"):
                    line_taxes.append({
                        "name": line.get("tax1"),
                        "rate": float(line.get("tax1_percent", 0)),
                        "amount": float(line.get("tax1_amount", 0))
                    })
                
                if line.get("tax2"):
                    line_taxes.append({
                        "name": line.get("tax2"),
                        "rate": float(line.get("tax2_percent", 0)),
                        "amount": float(line.get("tax2_amount", 0))
                    })
                
                line_items.append({
                    "line_id": str(line.get("lineid")),
                    "type": line.get("type"),  # 0=item, 1=time, 2=expense
                    "description": line.get("description"),
                    "name": line.get("name"),
                    "qty": float(line.get("qty", 0)),
                    "unit_cost": float(unit_cost),
                    "amount": float(line_amount),
                    "taxes": line_taxes,
                    "tax1": line.get("tax1"),
                    "tax2": line.get("tax2")
                })
            
            # Get currency code
            currency_code = invoice.get("currency_code", "USD")
            
            # Validate currency
            if currency_code not in self.SUPPORTED_CURRENCIES:
                logger.warning(f"Unsupported currency: {currency_code}")
            
            # Calculate totals
            subtotal = sum(item["amount"] for item in line_items)
            tax_total = sum(
                sum(tax["amount"] for tax in item["taxes"])
                for item in line_items
            )
            
            normalized_invoice = {
                "id": str(invoice.get("id")),
                "invoice_number": invoice.get("invoice_number"),
                "invoice_id": str(invoice.get("invoiceid")),
                "po_number": invoice.get("po_number"),
                "template": invoice.get("template"),
                "client": {
                    "id": str(invoice.get("clientid")),
                    "organization": invoice.get("organization"),
                    "first_name": invoice.get("fname"),
                    "last_name": invoice.get("lname"),
                    "email": invoice.get("email")
                },
                "dates": {
                    "create_date": invoice.get("create_date"),
                    "issue_date": invoice.get("date"),
                    "due_date": invoice.get("due_date"),
                    "period_start": invoice.get("period_start"),
                    "period_end": invoice.get("period_end"),
                    "sent_at": invoice.get("sent_at"),
                    "paid_at": invoice.get("paid_date"),
                    "created_at": invoice.get("created_at"),
                    "updated_at": invoice.get("updated_at")
                },
                "amounts": {
                    "subtotal": subtotal,
                    "tax_total": tax_total,
                    "total": float(amount),
                    "outstanding": float(outstanding),
                    "paid": float(paid),
                    "currency_code": currency_code
                },
                "discount": {
                    "value": float(invoice.get("discount_value", 0)),
                    "percentage": float(invoice.get("discount_percentage", 0))
                },
                "line_items": line_items,
                "status": invoice.get("status"),
                "payment_status": invoice.get("payment_status"),
                "terms": invoice.get("terms"),
                "notes": invoice.get("notes"),
                "footer": invoice.get("footer"),
                "vis_state": invoice.get("vis_state", 0),
                "metadata": {
                    "freshbooks_id": str(invoice.get("id")),
                    "invoiceid": str(invoice.get("invoiceid")),
                    "extracted_at": datetime.utcnow().isoformat(),
                    "generation_date": invoice.get("generation_date"),
                    "language": invoice.get("language"),
                    "auto_bill": invoice.get("autobill"),
                    "last_order_status": invoice.get("last_order_status")
                }
            }
            
            return normalized_invoice
            
        except Exception as e:
            logger.error(f"Failed to normalize invoice: {e}")
            raise FreshBooksDataError(f"Failed to normalize invoice data: {str(e)}")
    
    async def extract_taxes(self, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Extract tax configurations from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID
            
        Returns:
            List of normalized tax objects
        """
        try:
            taxes = await self.rest_client.get_taxes(account_id)
            
            normalized_taxes = []
            for tax in taxes:
                normalized_taxes.append({
                    "id": str(tax.get("id")),
                    "name": tax.get("name"),
                    "rate": float(tax.get("percentage", 0)),
                    "number": tax.get("number"),
                    "compound": tax.get("compound", False),
                    "created_at": tax.get("created_at"),
                    "updated_at": tax.get("updated_at")
                })
            
            logger.info(f"Extracted {len(normalized_taxes)} taxes from FreshBooks")
            return normalized_taxes
            
        except Exception as e:
            logger.error(f"Failed to extract taxes: {e}")
            raise FreshBooksDataError(f"Failed to extract taxes: {str(e)}")
    
    def _parse_money_amount(self, amount_obj: Dict[str, Any]) -> Decimal:
        """
        Parse FreshBooks money amount object.
        
        Args:
            amount_obj: FreshBooks amount object with 'amount' and 'code' fields
            
        Returns:
            Decimal amount value
        """
        if not amount_obj:
            return Decimal("0")
        
        amount_str = amount_obj.get("amount", "0")
        try:
            return Decimal(str(amount_str))
        except (ValueError, TypeError):
            logger.warning(f"Invalid amount format: {amount_str}")
            return Decimal("0")
    
    def _get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol for currency code."""
        symbols = {
            "USD": "$", "CAD": "C$", "EUR": "€", "GBP": "£", 
            "NGN": "₦", "AUD": "A$", "JPY": "¥"
        }
        return symbols.get(currency_code, currency_code)
    
    def _build_client_display_name(self, client: Dict[str, Any]) -> str:
        """Build display name for client."""
        organization = client.get("organization", "").strip()
        first_name = client.get("fname", "").strip()
        last_name = client.get("lname", "").strip()
        
        if organization:
            return organization
        elif first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return f"Client {client.get('id', 'Unknown')}"
    
    async def validate_account_access(self, account_id: str) -> bool:
        """
        Validate that we have access to the specified account.
        
        Args:
            account_id: FreshBooks account ID
            
        Returns:
            True if access is valid
        """
        try:
            await self.extract_account_info(account_id)
            return True
        except FreshBooksAccountNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Failed to validate account access: {e}")
            raise FreshBooksDataError(f"Failed to validate account access: {str(e)}")
    
    def calculate_totals(self, line_items: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate invoice totals from line items.
        
        Args:
            line_items: List of normalized line items
            
        Returns:
            Dictionary with calculated totals
        """
        subtotal = sum(item.get("amount", 0) for item in line_items)
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
        Get list of valid FreshBooks invoice statuses.
        
        Returns:
            List of status values
        """
        return list(self.VALID_INVOICE_STATUSES)