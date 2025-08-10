"""
FreshBooks UBL Transformer
Transforms FreshBooks invoice data to UBL 2.1 format for FIRS e-invoicing compliance.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid

from .exceptions import FreshBooksTransformationError, FreshBooksValidationError


logger = logging.getLogger(__name__)


class FreshBooksUBLTransformer:
    """
    Transforms FreshBooks invoice data to UBL 2.1 XML format.
    
    Handles FreshBooks REST API data structure and converts it to FIRS-compliant
    UBL 2.1 format for Nigerian e-invoicing requirements.
    """
    
    # Nigerian VAT rate (7.5%)
    NIGERIAN_VAT_RATE = Decimal("7.5")
    
    # Currency mappings
    CURRENCY_MAPPINGS = {
        "NGN": {"code": "566", "name": "Nigerian Naira"},
        "USD": {"code": "840", "name": "US Dollar"},
        "EUR": {"code": "978", "name": "Euro"},
        "GBP": {"code": "826", "name": "Pound Sterling"},
        "CAD": {"code": "124", "name": "Canadian Dollar"}
    }
    
    # FIRS tax categories
    FIRS_TAX_CATEGORIES = {
        "VAT": "S",      # Standard rated
        "EXEMPT": "E",   # Exempt
        "ZERO": "Z",     # Zero rated
        "NONE": "O"      # Out of scope
    }
    
    # FreshBooks line item types
    LINE_ITEM_TYPES = {
        0: "item",      # Item/Product
        1: "time",      # Time entry
        2: "expense"    # Expense
    }
    
    def __init__(self):
        """Initialize FreshBooks UBL transformer."""
        pass
    
    def transform_invoice_to_ubl(
        self,
        invoice_data: Dict[str, Any],
        account_data: Dict[str, Any],
        client_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform FreshBooks invoice data to UBL 2.1 format.
        
        Args:
            invoice_data: Normalized FreshBooks invoice data
            account_data: FreshBooks account information
            client_data: Additional client data (optional)
            
        Returns:
            UBL 2.1 compliant invoice structure
        """
        try:
            # Validate input data
            self._validate_invoice_data(invoice_data)
            self._validate_account_data(account_data)
            
            # Generate UBL invoice
            ubl_invoice = {
                "Invoice": {
                    "@xmlns": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
                    "@xmlns:cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
                    "@xmlns:cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
                    
                    # Invoice identification
                    "cbc:UBLVersionID": "2.1",
                    "cbc:CustomizationID": "urn:firs.gov.ng:einvoicing:ver1.0",
                    "cbc:ID": invoice_data.get("invoice_number"),
                    "cbc:IssueDate": self._format_date(invoice_data["dates"]["issue_date"]),
                    "cbc:DueDate": self._format_date(invoice_data["dates"]["due_date"]) if invoice_data["dates"].get("due_date") else None,
                    "cbc:InvoiceTypeCode": "380",  # Commercial invoice
                    "cbc:DocumentCurrencyCode": invoice_data["amounts"]["currency_code"],
                    
                    # Order reference (if available)
                    "cac:OrderReference": self._build_order_reference(invoice_data) if invoice_data.get("po_number") else None,
                    
                    # Period reference (if available)
                    "cac:InvoicePeriod": self._build_invoice_period(invoice_data) if self._has_period_dates(invoice_data) else None,
                    
                    # Supplier (account/business)
                    "cac:AccountingSupplierParty": self._build_supplier_party(account_data),
                    
                    # Customer (client)
                    "cac:AccountingCustomerParty": self._build_customer_party(invoice_data["client"], client_data),
                    
                    # Payment terms
                    "cac:PaymentTerms": self._build_payment_terms(invoice_data) if invoice_data.get("terms") else None,
                    
                    # Tax totals
                    "cac:TaxTotal": self._build_tax_totals(invoice_data),
                    
                    # Legal monetary total
                    "cac:LegalMonetaryTotal": self._build_monetary_total(invoice_data),
                    
                    # Invoice lines
                    "cac:InvoiceLine": self._build_invoice_lines(invoice_data["line_items"])
                }
            }
            
            # Remove None values
            self._clean_dict(ubl_invoice)
            
            logger.info(f"Successfully transformed FreshBooks invoice {invoice_data.get('invoice_number')} to UBL 2.1")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform invoice to UBL: {e}")
            raise FreshBooksTransformationError(f"UBL transformation failed: {str(e)}")
    
    def _validate_invoice_data(self, invoice_data: Dict[str, Any]) -> None:
        """Validate invoice data for UBL transformation."""
        required_fields = ["id", "invoice_number", "amounts", "line_items", "client", "dates"]
        
        for field in required_fields:
            if field not in invoice_data:
                raise FreshBooksValidationError(f"Missing required field: {field}")
        
        # Validate amounts
        amounts = invoice_data["amounts"]
        if not amounts.get("currency_code"):
            raise FreshBooksValidationError("Currency code is required")
        
        if amounts["currency_code"] not in self.CURRENCY_MAPPINGS:
            raise FreshBooksValidationError(f"Unsupported currency: {amounts['currency_code']}")
        
        # Validate line items
        if not invoice_data["line_items"]:
            raise FreshBooksValidationError("Invoice must have at least one line item")
    
    def _validate_account_data(self, account_data: Dict[str, Any]) -> None:
        """Validate account data for UBL transformation."""
        required_fields = ["name", "address"]
        
        for field in required_fields:
            if field not in account_data:
                raise FreshBooksValidationError(f"Missing required account field: {field}")
    
    def _format_date(self, date_str: Optional[str]) -> Optional[str]:
        """Format date string to ISO format."""
        if not date_str:
            return None
        
        try:
            # Handle various FreshBooks date formats
            if 'T' in date_str:
                # ISO format with time
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif '-' in date_str:
                # Date format YYYY-MM-DD
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            else:
                # Fallback to current format
                return date_str
            
            return dt.strftime("%Y-%m-%d")
        except Exception:
            logger.warning(f"Could not parse date: {date_str}")
            return date_str
    
    def _build_order_reference(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build order reference from PO number."""
        return {
            "cbc:ID": invoice_data.get("po_number")
        }
    
    def _has_period_dates(self, invoice_data: Dict[str, Any]) -> bool:
        """Check if invoice has period start/end dates."""
        dates = invoice_data.get("dates", {})
        return dates.get("period_start") and dates.get("period_end")
    
    def _build_invoice_period(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build invoice period information."""
        dates = invoice_data["dates"]
        return {
            "cbc:StartDate": self._format_date(dates.get("period_start")),
            "cbc:EndDate": self._format_date(dates.get("period_end"))
        }
    
    def _build_supplier_party(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build supplier party information."""
        address = account_data.get("address", {})
        
        supplier = {
            "cac:Party": {
                "cac:PartyName": {
                    "cbc:Name": account_data.get("name") or account_data.get("business_name")
                },
                "cac:PostalAddress": {
                    "cbc:StreetName": address.get("line1"),
                    "cbc:CityName": address.get("city"),
                    "cbc:PostalZone": address.get("postal_code"),
                    "cbc:CountrySubentity": address.get("province"),
                    "cac:Country": {
                        "cbc:IdentificationCode": address.get("country", "NG")
                    }
                }
            }
        }
        
        # Add business name if different from name
        if (account_data.get("business_name") and 
            account_data.get("business_name") != account_data.get("name")):
            supplier["cac:Party"]["cac:PartyLegalEntity"] = {
                "cbc:RegistrationName": account_data["business_name"]
            }
        
        # Add contact information
        if account_data.get("phone"):
            supplier["cac:Party"]["cac:Contact"] = {
                "cbc:Telephone": account_data["phone"]
            }
        
        return supplier
    
    def _build_customer_party(
        self,
        client_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build customer party information."""
        # Use additional data if provided, otherwise use basic client data
        if additional_data:
            address = additional_data.get("address", {})
            name = additional_data.get("display_name") or self._get_client_name(additional_data)
            email = additional_data.get("email") or client_data.get("email")
            phone = additional_data.get("phone", {})
        else:
            address = {}
            name = self._get_client_name(client_data)
            email = client_data.get("email")
            phone = {}
        
        customer = {
            "cac:Party": {
                "cac:PartyName": {
                    "cbc:Name": name
                },
                "cac:PostalAddress": {
                    "cbc:StreetName": address.get("line1"),
                    "cbc:AdditionalStreetName": address.get("line2"),
                    "cbc:CityName": address.get("city"),
                    "cbc:PostalZone": address.get("postal_code"),
                    "cbc:CountrySubentity": address.get("province"),
                    "cac:Country": {
                        "cbc:IdentificationCode": address.get("country", "NG")
                    }
                }
            }
        }
        
        # Add contact information if available
        contact_info = {}
        if email:
            contact_info["cbc:ElectronicMail"] = email
        
        if phone.get("business"):
            contact_info["cbc:Telephone"] = phone["business"]
        elif phone.get("mobile"):
            contact_info["cbc:Telephone"] = phone["mobile"]
        
        if contact_info:
            customer["cac:Party"]["cac:Contact"] = contact_info
        
        # Add organization name if it's a business client
        if additional_data and additional_data.get("organization"):
            customer["cac:Party"]["cac:PartyLegalEntity"] = {
                "cbc:RegistrationName": additional_data["organization"]
            }
        
        return customer
    
    def _build_payment_terms(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build payment terms information."""
        return {
            "cbc:Note": invoice_data.get("terms")
        }
    
    def _build_tax_totals(self, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build tax total information."""
        currency_code = invoice_data["amounts"]["currency_code"]
        tax_total_amount = Decimal(str(invoice_data["amounts"]["tax_total"]))
        
        # Group taxes by name and rate
        tax_groups = {}
        
        for line_item in invoice_data["line_items"]:
            for tax in line_item.get("taxes", []):
                tax_key = f"{tax.get('name', 'VAT')}_{tax.get('rate', 0)}"
                rate = Decimal(str(tax.get("rate", 0)))
                amount = Decimal(str(tax.get("amount", 0)))
                
                if tax_key not in tax_groups:
                    tax_groups[tax_key] = {
                        "name": tax.get("name", "VAT"),
                        "rate": rate,
                        "total_amount": Decimal("0"),
                        "taxable_amount": Decimal("0")
                    }
                
                tax_groups[tax_key]["total_amount"] += amount
                # Calculate taxable amount (reverse calculation)
                if rate > 0:
                    taxable_amount = amount * 100 / rate
                    tax_groups[tax_key]["taxable_amount"] += taxable_amount
        
        tax_subtotals = []
        for tax_key, group in tax_groups.items():
            # Determine tax category
            tax_category = self._get_tax_category(group["rate"])
            
            tax_subtotals.append({
                "cbc:TaxableAmount": {
                    "@currencyID": currency_code,
                    "#text": str(group["taxable_amount"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                },
                "cbc:TaxAmount": {
                    "@currencyID": currency_code,
                    "#text": str(group["total_amount"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                },
                "cac:TaxCategory": {
                    "cbc:ID": tax_category,
                    "cbc:Percent": str(group["rate"]),
                    "cac:TaxScheme": {
                        "cbc:ID": "VAT"
                    }
                }
            })
        
        return [{
            "cbc:TaxAmount": {
                "@currencyID": currency_code,
                "#text": str(tax_total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cac:TaxSubtotal": tax_subtotals
        }]
    
    def _build_monetary_total(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build legal monetary total."""
        amounts = invoice_data["amounts"]
        currency_code = amounts["currency_code"]
        
        subtotal = Decimal(str(amounts.get("subtotal", 0)))
        tax_total = Decimal(str(amounts["tax_total"]))
        total = Decimal(str(amounts["total"]))
        
        # Handle discount
        discount = invoice_data.get("discount", {})
        discount_amount = Decimal(str(discount.get("value", 0)))
        
        return {
            "cbc:LineExtensionAmount": {
                "@currencyID": currency_code,
                "#text": str(subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:TaxExclusiveAmount": {
                "@currencyID": currency_code,
                "#text": str((subtotal - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:TaxInclusiveAmount": {
                "@currencyID": currency_code,
                "#text": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:AllowanceTotalAmount": {
                "@currencyID": currency_code,
                "#text": str(discount_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            } if discount_amount > 0 else None,
            "cbc:PayableAmount": {
                "@currencyID": currency_code,
                "#text": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            }
        }
    
    def _build_invoice_lines(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build invoice line items."""
        ubl_lines = []
        
        for idx, item in enumerate(line_items, 1):
            quantity = Decimal(str(item.get("qty", 1)))
            unit_cost = Decimal(str(item.get("unit_cost", 0)))
            line_amount = Decimal(str(item.get("amount", 0)))
            
            # Build tax information for this line
            line_taxes = []
            for tax in item.get("taxes", []):
                rate = Decimal(str(tax.get("rate", 0)))
                tax_amount = Decimal(str(tax.get("amount", 0)))
                
                line_taxes.append({
                    "cbc:TaxAmount": {
                        "@currencyID": "NGN",  # Default to NGN for now
                        "#text": str(tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    },
                    "cac:TaxCategory": {
                        "cbc:ID": self._get_tax_category(rate),
                        "cbc:Percent": str(rate),
                        "cac:TaxScheme": {
                            "cbc:ID": "VAT"
                        }
                    }
                })
            
            # Determine unit code based on line item type
            unit_code = self._get_unit_code(item)
            
            ubl_line = {
                "cbc:ID": str(idx),
                "cbc:Note": self._get_line_note(item),
                "cbc:InvoicedQuantity": {
                    "@unitCode": unit_code,
                    "#text": str(quantity)
                },
                "cbc:LineExtensionAmount": {
                    "@currencyID": "NGN",
                    "#text": str(line_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                },
                "cac:TaxTotal": {
                    "cbc:TaxAmount": {
                        "@currencyID": "NGN",
                        "#text": str(sum(Decimal(str(tax.get("amount", 0))) for tax in item.get("taxes", [])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    },
                    "cac:TaxSubtotal": line_taxes
                } if line_taxes else None,
                "cac:Item": {
                    "cbc:Name": item.get("name") or item.get("description", "Service"),
                    "cbc:Description": item.get("description")
                },
                "cac:Price": {
                    "cbc:PriceAmount": {
                        "@currencyID": "NGN",
                        "#text": str(unit_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    }
                }
            }
            
            ubl_lines.append(ubl_line)
        
        return ubl_lines
    
    def _get_client_name(self, client_data: Dict[str, Any]) -> str:
        """Get client display name."""
        organization = client_data.get("organization", "").strip()
        first_name = client_data.get("first_name", "").strip()
        last_name = client_data.get("last_name", "").strip()
        
        if organization:
            return organization
        elif first_name and last_name:
            return f"{first_name} {last_name}"
        elif first_name:
            return first_name
        elif last_name:
            return last_name
        else:
            return "Customer"
    
    def _get_tax_category(self, rate: Decimal) -> str:
        """Get FIRS tax category based on rate."""
        if rate == 0:
            return self.FIRS_TAX_CATEGORIES["ZERO"]
        elif rate == self.NIGERIAN_VAT_RATE:
            return self.FIRS_TAX_CATEGORIES["VAT"]
        else:
            return self.FIRS_TAX_CATEGORIES["VAT"]  # Default to standard VAT
    
    def _get_unit_code(self, line_item: Dict[str, Any]) -> str:
        """Get appropriate unit code for line item."""
        item_type = line_item.get("type", 0)
        
        if item_type == 1:  # Time entry
            return "HUR"  # Hours
        elif item_type == 2:  # Expense
            return "EA"   # Each
        else:  # Item/Product
            return "EA"   # Each (default)
    
    def _get_line_note(self, line_item: Dict[str, Any]) -> Optional[str]:
        """Get note for line item based on type."""
        item_type = line_item.get("type", 0)
        type_name = self.LINE_ITEM_TYPES.get(item_type, "item")
        
        if type_name != "item":
            return f"FreshBooks {type_name}"
        
        return None
    
    def _clean_dict(self, data: Any) -> Any:
        """Remove None values from dictionary recursively."""
        if isinstance(data, dict):
            return {k: self._clean_dict(v) for k, v in data.items() if v is not None}
        elif isinstance(data, list):
            return [self._clean_dict(item) for item in data if item is not None]
        else:
            return data
    
    def get_supported_currencies(self) -> Dict[str, Dict[str, str]]:
        """Get supported currencies for UBL transformation."""
        return self.CURRENCY_MAPPINGS.copy()
    
    def validate_ubl_structure(self, ubl_data: Dict[str, Any]) -> List[str]:
        """
        Validate UBL structure for FIRS compliance.
        
        Args:
            ubl_data: UBL invoice data
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            invoice = ubl_data.get("Invoice", {})
            
            # Check required fields
            required_fields = [
                "cbc:ID", "cbc:IssueDate", "cbc:InvoiceTypeCode",
                "cbc:DocumentCurrencyCode", "cac:AccountingSupplierParty",
                "cac:AccountingCustomerParty", "cac:LegalMonetaryTotal"
            ]
            
            for field in required_fields:
                if field not in invoice:
                    errors.append(f"Missing required field: {field}")
            
            # Validate invoice lines
            if "cac:InvoiceLine" not in invoice:
                errors.append("Invoice must have at least one line item")
            elif not invoice["cac:InvoiceLine"]:
                errors.append("Invoice lines cannot be empty")
            
            # Validate currency
            currency = invoice.get("cbc:DocumentCurrencyCode")
            if currency and currency not in self.CURRENCY_MAPPINGS:
                errors.append(f"Unsupported currency: {currency}")
            
            # Validate supplier party
            supplier = invoice.get("cac:AccountingSupplierParty", {}).get("cac:Party", {})
            if not supplier.get("cac:PartyName", {}).get("cbc:Name"):
                errors.append("Supplier name is required")
            
            # Validate customer party
            customer = invoice.get("cac:AccountingCustomerParty", {}).get("cac:Party", {})
            if not customer.get("cac:PartyName", {}).get("cbc:Name"):
                errors.append("Customer name is required")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors