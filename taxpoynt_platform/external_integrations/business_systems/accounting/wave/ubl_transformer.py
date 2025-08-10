"""
Wave UBL Transformer
Transforms Wave invoice data to UBL 2.1 format for FIRS e-invoicing compliance.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import uuid

from .exceptions import WaveTransformationError, WaveValidationError


logger = logging.getLogger(__name__)


class WaveUBLTransformer:
    """
    Transforms Wave Accounting invoice data to UBL 2.1 XML format.
    
    Handles Wave's GraphQL data structure and converts it to FIRS-compliant
    UBL 2.1 format for Nigerian e-invoicing requirements.
    """
    
    # Nigerian VAT rate (7.5%)
    NIGERIAN_VAT_RATE = Decimal("7.5")
    
    # Currency mappings
    CURRENCY_MAPPINGS = {
        "NGN": {"code": "566", "name": "Nigerian Naira"},
        "USD": {"code": "840", "name": "US Dollar"},
        "EUR": {"code": "978", "name": "Euro"},
        "GBP": {"code": "826", "name": "Pound Sterling"}
    }
    
    # FIRS tax categories
    FIRS_TAX_CATEGORIES = {
        "VAT": "S",      # Standard rated
        "EXEMPT": "E",   # Exempt
        "ZERO": "Z",     # Zero rated
        "NONE": "O"      # Out of scope
    }
    
    def __init__(self):
        """Initialize Wave UBL transformer."""
        pass
    
    def transform_invoice_to_ubl(
        self,
        invoice_data: Dict[str, Any],
        business_data: Dict[str, Any],
        customer_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Wave invoice data to UBL 2.1 format.
        
        Args:
            invoice_data: Normalized Wave invoice data
            business_data: Wave business information
            customer_data: Additional customer data (optional)
            
        Returns:
            UBL 2.1 compliant invoice structure
        """
        try:
            # Validate input data
            self._validate_invoice_data(invoice_data)
            self._validate_business_data(business_data)
            
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
                    "cbc:IssueDate": self._format_date(invoice_data["dates"]["invoice_date"]),
                    "cbc:DueDate": self._format_date(invoice_data["dates"]["due_date"]) if invoice_data["dates"].get("due_date") else None,
                    "cbc:InvoiceTypeCode": "380",  # Commercial invoice
                    "cbc:DocumentCurrencyCode": invoice_data["amounts"]["currency_code"],
                    
                    # Order reference (if available)
                    "cac:OrderReference": self._build_order_reference(invoice_data) if invoice_data.get("po_number") else None,
                    
                    # Supplier (business)
                    "cac:AccountingSupplierParty": self._build_supplier_party(business_data),
                    
                    # Customer
                    "cac:AccountingCustomerParty": self._build_customer_party(invoice_data["customer"], customer_data),
                    
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
            
            logger.info(f"Successfully transformed Wave invoice {invoice_data.get('invoice_number')} to UBL 2.1")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform invoice to UBL: {e}")
            raise WaveTransformationError(f"UBL transformation failed: {str(e)}")
    
    def _validate_invoice_data(self, invoice_data: Dict[str, Any]) -> None:
        """Validate invoice data for UBL transformation."""
        required_fields = ["id", "invoice_number", "amounts", "line_items", "customer", "dates"]
        
        for field in required_fields:
            if field not in invoice_data:
                raise WaveValidationError(f"Missing required field: {field}")
        
        # Validate amounts
        amounts = invoice_data["amounts"]
        if not amounts.get("currency_code"):
            raise WaveValidationError("Currency code is required")
        
        if amounts["currency_code"] not in self.CURRENCY_MAPPINGS:
            raise WaveValidationError(f"Unsupported currency: {amounts['currency_code']}")
        
        # Validate line items
        if not invoice_data["line_items"]:
            raise WaveValidationError("Invoice must have at least one line item")
    
    def _validate_business_data(self, business_data: Dict[str, Any]) -> None:
        """Validate business data for UBL transformation."""
        required_fields = ["name", "address"]
        
        for field in required_fields:
            if field not in business_data:
                raise WaveValidationError(f"Missing required business field: {field}")
    
    def _format_date(self, date_str: Optional[str]) -> Optional[str]:
        """Format date string to ISO format."""
        if not date_str:
            return None
        
        try:
            # Parse Wave date format and convert to ISO
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return date_str
    
    def _build_order_reference(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build order reference from PO number."""
        return {
            "cbc:ID": invoice_data.get("po_number")
        }
    
    def _build_supplier_party(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Build supplier party information."""
        address = business_data.get("address", {})
        
        supplier = {
            "cac:Party": {
                "cac:PartyName": {
                    "cbc:Name": business_data.get("name")
                },
                "cac:PostalAddress": {
                    "cbc:StreetName": address.get("line1"),
                    "cbc:AdditionalStreetName": address.get("line2"),
                    "cbc:CityName": address.get("city"),
                    "cbc:PostalZone": address.get("postal_code"),
                    "cbc:CountrySubentity": address.get("province_code"),
                    "cac:Country": {
                        "cbc:IdentificationCode": address.get("country_code", "NG")
                    }
                }
            }
        }
        
        # Add organization name if different from name
        if business_data.get("organization_name") and business_data["organization_name"] != business_data.get("name"):
            supplier["cac:Party"]["cac:PartyLegalEntity"] = {
                "cbc:RegistrationName": business_data["organization_name"]
            }
        
        return supplier
    
    def _build_customer_party(
        self,
        customer_data: Dict[str, Any],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build customer party information."""
        # Use additional data if provided, otherwise use basic customer data
        if additional_data:
            address = additional_data.get("address", {})
            name = additional_data.get("name") or customer_data.get("name")
            email = additional_data.get("email") or customer_data.get("email")
        else:
            address = {}
            name = customer_data.get("name")
            email = customer_data.get("email")
        
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
                    "cbc:CountrySubentity": address.get("province_code"),
                    "cac:Country": {
                        "cbc:IdentificationCode": address.get("country_code", "NG")
                    }
                }
            }
        }
        
        # Add contact information if available
        if email:
            customer["cac:Party"]["cac:Contact"] = {
                "cbc:ElectronicMail": email
            }
        
        return customer
    
    def _build_tax_totals(self, invoice_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build tax total information."""
        currency_code = invoice_data["amounts"]["currency_code"]
        tax_total_amount = Decimal(str(invoice_data["amounts"]["tax_total"]))
        
        # Group taxes by rate
        tax_groups = {}
        
        for line_item in invoice_data["line_items"]:
            for tax in line_item.get("taxes", []):
                rate = Decimal(str(tax.get("rate", 0)))
                amount = Decimal(str(tax.get("amount", 0)))
                
                if rate not in tax_groups:
                    tax_groups[rate] = {
                        "name": tax.get("name", "VAT"),
                        "total_amount": Decimal("0"),
                        "taxable_amount": Decimal("0")
                    }
                
                tax_groups[rate]["total_amount"] += amount
                # Calculate taxable amount (reverse calculation)
                if rate > 0:
                    taxable_amount = amount * 100 / rate
                    tax_groups[rate]["taxable_amount"] += taxable_amount
        
        tax_subtotals = []
        for rate, group in tax_groups.items():
            # Determine tax category
            tax_category = self._get_tax_category(rate)
            
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
                    "cbc:Percent": str(rate),
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
        
        return {
            "cbc:LineExtensionAmount": {
                "@currencyID": currency_code,
                "#text": str(subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:TaxExclusiveAmount": {
                "@currencyID": currency_code,
                "#text": str(subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:TaxInclusiveAmount": {
                "@currencyID": currency_code,
                "#text": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            },
            "cbc:PayableAmount": {
                "@currencyID": currency_code,
                "#text": str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
            }
        }
    
    def _build_invoice_lines(self, line_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build invoice line items."""
        ubl_lines = []
        
        for idx, item in enumerate(line_items, 1):
            quantity = Decimal(str(item.get("quantity", 1)))
            unit_price = Decimal(str(item.get("unit_price", 0)))
            line_total = Decimal(str(item.get("total", 0)))
            
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
            
            ubl_line = {
                "cbc:ID": str(idx),
                "cbc:InvoicedQuantity": {
                    "@unitCode": "EA",  # Each (default unit)
                    "#text": str(quantity)
                },
                "cbc:LineExtensionAmount": {
                    "@currencyID": "NGN",
                    "#text": str((quantity * unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                },
                "cac:TaxTotal": {
                    "cbc:TaxAmount": {
                        "@currencyID": "NGN",
                        "#text": str(sum(Decimal(str(tax.get("amount", 0))) for tax in item.get("taxes", [])).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    },
                    "cac:TaxSubtotal": line_taxes
                },
                "cac:Item": {
                    "cbc:Name": item.get("product_name") or item.get("description", "Product"),
                    "cbc:Description": item.get("description")
                },
                "cac:Price": {
                    "cbc:PriceAmount": {
                        "@currencyID": "NGN",
                        "#text": str(unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
                    }
                }
            }
            
            ubl_lines.append(ubl_line)
        
        return ubl_lines
    
    def _get_tax_category(self, rate: Decimal) -> str:
        """Get FIRS tax category based on rate."""
        if rate == 0:
            return self.FIRS_TAX_CATEGORIES["ZERO"]
        elif rate == self.NIGERIAN_VAT_RATE:
            return self.FIRS_TAX_CATEGORIES["VAT"]
        else:
            return self.FIRS_TAX_CATEGORIES["VAT"]  # Default to standard VAT
    
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
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors