"""
UBL Schema Validator

Validates documents against UBL (Universal Business Language) schemas.
Extracted from odoo_ubl_validator.py - provides granular UBL schema validation.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from decimal import Decimal
from datetime import datetime
import re

logger = logging.getLogger(__name__)


class UBLValidator:
    """
    Validates invoice documents against UBL schema requirements.
    Focuses specifically on BIS Billing 3.0 UBL format compliance.
    """
    
    def __init__(self):
        self.required_fields = self._get_required_fields()
        self.field_formats = self._get_field_formats()
        self.currency_codes = self._get_valid_currency_codes()
        self.country_codes = self._get_valid_country_codes()
    
    def validate_ubl_document(self, document: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        Validate a complete UBL document against schema requirements.
        
        Args:
            document: UBL document to validate
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        try:
            # Validate invoice structure
            invoice_errors = self._validate_invoice_structure(document)
            validation_errors.extend(invoice_errors)
            
            # Validate supplier party
            if "accounting_supplier_party" in document:
                supplier_errors = self._validate_supplier_party(document["accounting_supplier_party"])
                validation_errors.extend(supplier_errors)
            
            # Validate customer party
            if "accounting_customer_party" in document:
                customer_errors = self._validate_customer_party(document["accounting_customer_party"])
                validation_errors.extend(customer_errors)
            
            # Validate invoice lines
            if "invoice_lines" in document:
                line_errors = self._validate_invoice_lines(document["invoice_lines"])
                validation_errors.extend(line_errors)
            
            # Validate tax information
            if "tax_total" in document:
                tax_errors = self._validate_tax_total(document["tax_total"])
                validation_errors.extend(tax_errors)
            
            # Validate monetary totals
            if "legal_monetary_total" in document:
                total_errors = self._validate_monetary_total(document["legal_monetary_total"])
                validation_errors.extend(total_errors)
            
            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors
            
        except Exception as e:
            logger.error(f"Error validating UBL document: {e}")
            validation_errors.append({
                "field": "document",
                "error": "VALIDATION_ERROR",
                "message": f"Document validation failed: {str(e)}",
                "severity": "error"
            })
            return False, validation_errors
    
    def _validate_invoice_structure(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate main invoice structure and required fields"""
        errors = []
        required_invoice_fields = self.required_fields.get("invoice", [])
        
        for field in required_invoice_fields:
            if field not in document or document[field] is None:
                errors.append({
                    "field": field,
                    "error": "MISSING_REQUIRED_FIELD",
                    "message": f"Required field '{field}' is missing",
                    "severity": "error"
                })
        
        # Validate specific field formats
        if "invoice_number" in document:
            if not self._validate_invoice_number_format(document["invoice_number"]):
                errors.append({
                    "field": "invoice_number",
                    "error": "INVALID_FORMAT",
                    "message": "Invoice number format is invalid",
                    "severity": "error"
                })
        
        if "invoice_date" in document:
            if not self._validate_date_format(document["invoice_date"]):
                errors.append({
                    "field": "invoice_date",
                    "error": "INVALID_DATE_FORMAT",
                    "message": "Invoice date format is invalid (expected: YYYY-MM-DD)",
                    "severity": "error"
                })
        
        if "currency_code" in document:
            if document["currency_code"] not in self.currency_codes:
                errors.append({
                    "field": "currency_code",
                    "error": "INVALID_CURRENCY",
                    "message": f"Invalid currency code: {document['currency_code']}",
                    "severity": "error"
                })
        
        return errors
    
    def _validate_supplier_party(self, supplier: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate supplier party information"""
        errors = []
        required_supplier_fields = self.required_fields.get("supplier", [])
        
        for field in required_supplier_fields:
            if field not in supplier or supplier[field] is None:
                errors.append({
                    "field": f"supplier.{field}",
                    "error": "MISSING_REQUIRED_FIELD",
                    "message": f"Required supplier field '{field}' is missing",
                    "severity": "error"
                })
        
        # Validate party name
        if "party_name" in supplier:
            if not supplier["party_name"] or len(supplier["party_name"].strip()) == 0:
                errors.append({
                    "field": "supplier.party_name",
                    "error": "EMPTY_PARTY_NAME",
                    "message": "Supplier party name cannot be empty",
                    "severity": "error"
                })
        
        # Validate postal address
        if "postal_address" in supplier:
            address_errors = self._validate_postal_address(supplier["postal_address"], "supplier")
            errors.extend(address_errors)
        
        # Validate tax scheme
        if "party_tax_scheme" in supplier:
            tax_errors = self._validate_party_tax_scheme(supplier["party_tax_scheme"], "supplier")
            errors.extend(tax_errors)
        
        return errors
    
    def _validate_customer_party(self, customer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate customer party information"""
        errors = []
        required_customer_fields = self.required_fields.get("customer", [])
        
        for field in required_customer_fields:
            if field not in customer or customer[field] is None:
                errors.append({
                    "field": f"customer.{field}",
                    "error": "MISSING_REQUIRED_FIELD",
                    "message": f"Required customer field '{field}' is missing",
                    "severity": "error"
                })
        
        # Validate party name
        if "party_name" in customer:
            if not customer["party_name"] or len(customer["party_name"].strip()) == 0:
                errors.append({
                    "field": "customer.party_name",
                    "error": "EMPTY_PARTY_NAME",
                    "message": "Customer party name cannot be empty",
                    "severity": "error"
                })
        
        # Validate postal address
        if "postal_address" in customer:
            address_errors = self._validate_postal_address(customer["postal_address"], "customer")
            errors.extend(address_errors)
        
        return errors
    
    def _validate_invoice_lines(self, lines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate invoice line items"""
        errors = []
        
        if not lines or len(lines) == 0:
            errors.append({
                "field": "invoice_lines",
                "error": "NO_INVOICE_LINES",
                "message": "Invoice must contain at least one line item",
                "severity": "error"
            })
            return errors
        
        required_line_fields = self.required_fields.get("invoice_line", [])
        
        for i, line in enumerate(lines):
            line_prefix = f"line[{i}]"
            
            # Check required fields for each line
            for field in required_line_fields:
                if field not in line or line[field] is None:
                    errors.append({
                        "field": f"{line_prefix}.{field}",
                        "error": "MISSING_REQUIRED_FIELD",
                        "message": f"Required line field '{field}' is missing",
                        "severity": "error"
                    })
            
            # Validate quantity
            if "invoiced_quantity" in line:
                if not self._validate_decimal_positive(line["invoiced_quantity"]):
                    errors.append({
                        "field": f"{line_prefix}.invoiced_quantity",
                        "error": "INVALID_QUANTITY",
                        "message": "Invoiced quantity must be a positive number",
                        "severity": "error"
                    })
            
            # Validate price
            if "price" in line:
                if not self._validate_decimal_non_negative(line["price"]):
                    errors.append({
                        "field": f"{line_prefix}.price",
                        "error": "INVALID_PRICE",
                        "message": "Line price must be non-negative",
                        "severity": "error"
                    })
            
            # Validate line extension amount
            if "line_extension_amount" in line:
                if not self._validate_decimal_non_negative(line["line_extension_amount"]):
                    errors.append({
                        "field": f"{line_prefix}.line_extension_amount",
                        "error": "INVALID_AMOUNT",
                        "message": "Line extension amount must be non-negative",
                        "severity": "error"
                    })
        
        return errors
    
    def _validate_tax_total(self, tax_total: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate tax total information"""
        errors = []
        
        # Validate tax amount
        if "tax_amount" in tax_total:
            if not self._validate_decimal_non_negative(tax_total["tax_amount"]):
                errors.append({
                    "field": "tax_total.tax_amount",
                    "error": "INVALID_TAX_AMOUNT",
                    "message": "Tax amount must be non-negative",
                    "severity": "error"
                })
        
        # Validate tax subtotals
        if "tax_subtotals" in tax_total:
            for i, subtotal in enumerate(tax_total["tax_subtotals"]):
                if "taxable_amount" in subtotal:
                    if not self._validate_decimal_non_negative(subtotal["taxable_amount"]):
                        errors.append({
                            "field": f"tax_total.tax_subtotals[{i}].taxable_amount",
                            "error": "INVALID_TAXABLE_AMOUNT",
                            "message": "Taxable amount must be non-negative",
                            "severity": "error"
                        })
                
                if "tax_amount" in subtotal:
                    if not self._validate_decimal_non_negative(subtotal["tax_amount"]):
                        errors.append({
                            "field": f"tax_total.tax_subtotals[{i}].tax_amount",
                            "error": "INVALID_TAX_AMOUNT",
                            "message": "Tax amount must be non-negative",
                            "severity": "error"
                        })
        
        return errors
    
    def _validate_monetary_total(self, monetary_total: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate legal monetary total"""
        errors = []
        
        monetary_fields = ["line_extension_amount", "tax_exclusive_amount", "tax_inclusive_amount", "payable_amount"]
        
        for field in monetary_fields:
            if field in monetary_total:
                if not self._validate_decimal_non_negative(monetary_total[field]):
                    errors.append({
                        "field": f"legal_monetary_total.{field}",
                        "error": "INVALID_MONETARY_AMOUNT",
                        "message": f"{field} must be non-negative",
                        "severity": "error"
                    })
        
        return errors
    
    def _validate_postal_address(self, address: Dict[str, Any], party_type: str) -> List[Dict[str, Any]]:
        """Validate postal address structure"""
        errors = []
        
        required_address_fields = ["street_name", "city_name", "country"]
        
        for field in required_address_fields:
            if field not in address or not address[field]:
                errors.append({
                    "field": f"{party_type}.postal_address.{field}",
                    "error": "MISSING_ADDRESS_FIELD",
                    "message": f"Required address field '{field}' is missing",
                    "severity": "error"
                })
        
        # Validate country code
        if "country" in address and "identification_code" in address["country"]:
            country_code = address["country"]["identification_code"]
            if country_code not in self.country_codes:
                errors.append({
                    "field": f"{party_type}.postal_address.country.identification_code",
                    "error": "INVALID_COUNTRY_CODE",
                    "message": f"Invalid country code: {country_code}",
                    "severity": "error"
                })
        
        return errors
    
    def _validate_party_tax_scheme(self, tax_scheme: Dict[str, Any], party_type: str) -> List[Dict[str, Any]]:
        """Validate party tax scheme information"""
        errors = []
        
        # Validate company ID (TIN)
        if "company_id" not in tax_scheme or not tax_scheme["company_id"]:
            errors.append({
                "field": f"{party_type}.party_tax_scheme.company_id",
                "error": "MISSING_TAX_ID",
                "message": "Tax identification number (TIN) is required",
                "severity": "error"
            })
        elif not self._validate_tin_format(tax_scheme["company_id"]):
            errors.append({
                "field": f"{party_type}.party_tax_scheme.company_id",
                "error": "INVALID_TIN_FORMAT",
                "message": "Tax identification number format is invalid",
                "severity": "warning"
            })
        
        return errors
    
    def _validate_invoice_number_format(self, invoice_number: str) -> bool:
        """Validate invoice number format"""
        if not invoice_number or len(invoice_number.strip()) == 0:
            return False
        # Invoice number should be alphanumeric with allowed special characters
        pattern = r'^[A-Za-z0-9\-_/]+$'
        return bool(re.match(pattern, invoice_number.strip()))
    
    def _validate_date_format(self, date_value: Any) -> bool:
        """Validate date format (YYYY-MM-DD)"""
        if isinstance(date_value, datetime):
            return True
        if isinstance(date_value, str):
            try:
                datetime.strptime(date_value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False
    
    def _validate_decimal_positive(self, value: Any) -> bool:
        """Validate that value is a positive decimal"""
        try:
            decimal_value = Decimal(str(value))
            return decimal_value > 0
        except (ValueError, TypeError):
            return False
    
    def _validate_decimal_non_negative(self, value: Any) -> bool:
        """Validate that value is a non-negative decimal"""
        try:
            decimal_value = Decimal(str(value))
            return decimal_value >= 0
        except (ValueError, TypeError):
            return False
    
    def _validate_tin_format(self, tin: str) -> bool:
        """Validate Nigerian TIN format"""
        if not tin:
            return False
        # Nigerian TIN format: 8-14 digits
        pattern = r'^\d{8,14}$'
        return bool(re.match(pattern, tin.strip()))
    
    def _get_required_fields(self) -> Dict[str, List[str]]:
        """Get required fields for UBL document validation"""
        return {
            "invoice": [
                "invoice_number",
                "invoice_type_code", 
                "invoice_date",
                "currency_code",
                "accounting_supplier_party",
                "accounting_customer_party",
                "invoice_lines",
                "tax_total",
                "legal_monetary_total"
            ],
            "supplier": [
                "party_name",
                "postal_address",
                "party_tax_scheme",
                "party_legal_entity"
            ],
            "customer": [
                "party_name",
                "postal_address"
            ],
            "invoice_line": [
                "id",
                "invoiced_quantity",
                "line_extension_amount",
                "item",
                "price"
            ],
            "item": [
                "name"
            ]
        }
    
    def _get_field_formats(self) -> Dict[str, str]:
        """Get field format patterns"""
        return {
            "invoice_number": r'^[A-Za-z0-9\-_/]+$',
            "date": r'^\d{4}-\d{2}-\d{2}$',
            "tin": r'^\d{8,14}$',
            "decimal": r'^\d+(\.\d{1,2})?$'
        }
    
    def _get_valid_currency_codes(self) -> List[str]:
        """Get valid ISO currency codes"""
        return [
            "NGN",  # Nigerian Naira
            "USD",  # US Dollar
            "EUR",  # Euro
            "GBP",  # British Pound
            "CAD",  # Canadian Dollar
            "AUD",  # Australian Dollar
            "JPY",  # Japanese Yen
            "CHF",  # Swiss Franc
            "CNY",  # Chinese Yuan
            "INR"   # Indian Rupee
        ]
    
    def _get_valid_country_codes(self) -> List[str]:
        """Get valid ISO country codes"""
        return [
            "NG",  # Nigeria
            "US",  # United States
            "GB",  # United Kingdom
            "DE",  # Germany
            "FR",  # France
            "CA",  # Canada
            "AU",  # Australia
            "JP",  # Japan
            "CH",  # Switzerland
            "CN",  # China
            "IN"   # India
        ]


# Global instance for easy access
ubl_validator = UBLValidator()