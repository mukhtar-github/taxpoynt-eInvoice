"""
Schema Transformer

Transforms data to FIRS-compliant formats and UBL schema structures.
Extracted from odoo_ubl_transformer.py - provides granular schema transformation.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)


class SchemaTransformer:
    """
    Transforms various data formats to FIRS-compliant UBL schema structures.
    Handles conversion from ERP formats (Odoo, SAP, etc.) to standardized UBL.
    """
    
    def __init__(self):
        self.transformation_mappings = self._load_transformation_mappings()
        self.default_values = self._load_default_values()
        self.field_normalizers = self._load_field_normalizers()
    
    def transform_to_ubl_invoice(
        self, 
        source_data: Dict[str, Any], 
        source_format: str = "odoo"
    ) -> Dict[str, Any]:
        """
        Transform source invoice data to UBL-compliant format.
        
        Args:
            source_data: Source invoice data
            source_format: Format of source data (odoo, sap, quickbooks, etc.)
            
        Returns:
            UBL-compliant invoice document
        """
        try:
            logger.info(f"Transforming {source_format} data to UBL format")
            
            # Get transformation mapping for source format
            mapping = self.transformation_mappings.get(source_format, {})
            
            # Transform main invoice structure
            ubl_invoice = self._transform_invoice_header(source_data, mapping)
            
            # Transform supplier party
            ubl_invoice["accounting_supplier_party"] = self._transform_supplier_party(
                source_data, mapping
            )
            
            # Transform customer party
            ubl_invoice["accounting_customer_party"] = self._transform_customer_party(
                source_data, mapping
            )
            
            # Transform invoice lines
            ubl_invoice["invoice_lines"] = self._transform_invoice_lines(
                source_data, mapping
            )
            
            # Transform tax information
            ubl_invoice["tax_total"] = self._transform_tax_total(
                source_data, mapping
            )
            
            # Transform monetary totals
            ubl_invoice["legal_monetary_total"] = self._transform_monetary_total(
                source_data, mapping
            )
            
            # Apply field normalizations
            ubl_invoice = self._normalize_fields(ubl_invoice)
            
            # Set FIRS-specific fields
            ubl_invoice = self._apply_firs_requirements(ubl_invoice)
            
            logger.info("Successfully transformed to UBL format")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Error transforming to UBL format: {e}")
            raise
    
    def transform_to_firs_format(self, ubl_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform UBL data to FIRS-specific format requirements.
        
        Args:
            ubl_data: UBL-compliant invoice data
            
        Returns:
            FIRS-compliant invoice document
        """
        try:
            logger.info("Transforming UBL data to FIRS format")
            
            firs_invoice = ubl_data.copy()
            
            # Apply FIRS-specific transformations
            firs_invoice = self._apply_firs_document_structure(firs_invoice)
            firs_invoice = self._apply_firs_tax_calculations(firs_invoice)
            firs_invoice = self._apply_firs_party_requirements(firs_invoice)
            firs_invoice = self._apply_firs_line_requirements(firs_invoice)
            
            # Add FIRS metadata
            firs_invoice["firs_metadata"] = self._generate_firs_metadata()
            
            logger.info("Successfully transformed to FIRS format")
            return firs_invoice
            
        except Exception as e:
            logger.error(f"Error transforming to FIRS format: {e}")
            raise
    
    def normalize_field_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize field values according to UBL standards.
        
        Args:
            data: Data to normalize
            
        Returns:
            Normalized data
        """
        return self._normalize_fields(data)
    
    def _transform_invoice_header(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform main invoice header information"""
        header = {}
        
        # Map basic invoice fields
        header_mapping = mapping.get("invoice_header", {})
        
        # Invoice number
        header["invoice_number"] = self._get_mapped_value(
            source_data, header_mapping.get("invoice_number", "number")
        )
        
        # Invoice type code (default to commercial invoice)
        header["invoice_type_code"] = self._get_mapped_value(
            source_data, 
            header_mapping.get("invoice_type_code"),
            default="380"  # Commercial Invoice
        )
        
        # Invoice date
        invoice_date = self._get_mapped_value(
            source_data, header_mapping.get("invoice_date", "date_invoice")
        )
        header["invoice_date"] = self._normalize_date(invoice_date)
        
        # Due date
        due_date = self._get_mapped_value(
            source_data, header_mapping.get("due_date", "date_due")
        )
        if due_date:
            header["due_date"] = self._normalize_date(due_date)
        
        # Currency code
        header["currency_code"] = self._get_mapped_value(
            source_data,
            header_mapping.get("currency_code", "currency_id.name"),
            default="NGN"
        )
        
        # Document references
        header["id"] = str(uuid.uuid4())
        header["uuid"] = header["id"]
        
        return header
    
    def _transform_supplier_party(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform supplier party information"""
        supplier_mapping = mapping.get("supplier", {})
        
        # Extract supplier data from source
        supplier_source = self._get_mapped_value(
            source_data, supplier_mapping.get("source_path", "company_id")
        )
        
        if not supplier_source:
            supplier_source = source_data  # Fallback to root level
        
        supplier = {
            "party": {
                "party_name": [
                    {
                        "name": self._get_mapped_value(
                            supplier_source, 
                            supplier_mapping.get("name", "name")
                        )
                    }
                ],
                "postal_address": self._transform_address(
                    supplier_source, supplier_mapping.get("address", {})
                ),
                "party_tax_scheme": [
                    {
                        "company_id": self._get_mapped_value(
                            supplier_source,
                            supplier_mapping.get("tax_id", "vat")
                        ),
                        "tax_scheme": {
                            "id": "VAT",
                            "name": "Value Added Tax"
                        }
                    }
                ],
                "party_legal_entity": [
                    {
                        "registration_name": self._get_mapped_value(
                            supplier_source,
                            supplier_mapping.get("legal_name", "name")
                        ),
                        "company_id": self._get_mapped_value(
                            supplier_source,
                            supplier_mapping.get("registration_id", "company_registry")
                        )
                    }
                ]
            }
        }
        
        return supplier
    
    def _transform_customer_party(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform customer party information"""
        customer_mapping = mapping.get("customer", {})
        
        # Extract customer data from source
        customer_source = self._get_mapped_value(
            source_data, customer_mapping.get("source_path", "partner_id")
        )
        
        if not customer_source:
            return {"party": {}}  # Return empty structure if no customer data
        
        customer = {
            "party": {
                "party_name": [
                    {
                        "name": self._get_mapped_value(
                            customer_source,
                            customer_mapping.get("name", "name")
                        )
                    }
                ],
                "postal_address": self._transform_address(
                    customer_source, customer_mapping.get("address", {})
                )
            }
        }
        
        # Add tax scheme if customer has tax ID
        customer_tax_id = self._get_mapped_value(
            customer_source, customer_mapping.get("tax_id", "vat")
        )
        if customer_tax_id:
            customer["party"]["party_tax_scheme"] = [
                {
                    "company_id": customer_tax_id,
                    "tax_scheme": {
                        "id": "VAT",
                        "name": "Value Added Tax"
                    }
                }
            ]
        
        return customer
    
    def _transform_invoice_lines(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform invoice line items"""
        lines_mapping = mapping.get("lines", {})
        
        # Extract lines from source data
        source_lines = self._get_mapped_value(
            source_data, lines_mapping.get("source_path", "invoice_line_ids")
        )
        
        if not source_lines:
            return []
        
        transformed_lines = []
        
        for i, line_data in enumerate(source_lines):
            transformed_line = {
                "id": str(i + 1),
                "invoiced_quantity": {
                    "value": self._normalize_decimal(
                        self._get_mapped_value(line_data, lines_mapping.get("quantity", "quantity"))
                    ),
                    "unit_code": self._get_mapped_value(
                        line_data, 
                        lines_mapping.get("unit_code", "uom_id.name"),
                        default="EA"  # Each
                    )
                },
                "line_extension_amount": {
                    "value": self._normalize_decimal(
                        self._get_mapped_value(line_data, lines_mapping.get("subtotal", "price_subtotal"))
                    ),
                    "currency_id": self._get_mapped_value(
                        source_data, "currency_id.name", default="NGN"
                    )
                },
                "item": {
                    "name": self._get_mapped_value(
                        line_data, lines_mapping.get("product_name", "product_id.name")
                    ),
                    "description": self._get_mapped_value(
                        line_data, lines_mapping.get("description", "name")
                    )
                },
                "price": {
                    "price_amount": {
                        "value": self._normalize_decimal(
                            self._get_mapped_value(line_data, lines_mapping.get("unit_price", "price_unit"))
                        ),
                        "currency_id": self._get_mapped_value(
                            source_data, "currency_id.name", default="NGN"
                        )
                    }
                }
            }
            
            # Add tax information for line
            line_tax = self._transform_line_tax(line_data, lines_mapping.get("tax", {}))
            if line_tax:
                transformed_line["tax_total"] = line_tax
            
            transformed_lines.append(transformed_line)
        
        return transformed_lines
    
    def _transform_tax_total(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform tax total information"""
        tax_mapping = mapping.get("tax", {})
        
        tax_total = {
            "tax_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(source_data, tax_mapping.get("total_amount", "amount_tax"))
                ),
                "currency_id": self._get_mapped_value(
                    source_data, "currency_id.name", default="NGN"
                )
            }
        }
        
        # Add tax subtotals if available
        tax_lines = self._get_mapped_value(source_data, tax_mapping.get("tax_lines", "tax_line_ids"))
        if tax_lines:
            tax_subtotals = []
            for tax_line in tax_lines:
                subtotal = {
                    "taxable_amount": {
                        "value": self._normalize_decimal(
                            self._get_mapped_value(tax_line, "base")
                        ),
                        "currency_id": self._get_mapped_value(
                            source_data, "currency_id.name", default="NGN"
                        )
                    },
                    "tax_amount": {
                        "value": self._normalize_decimal(
                            self._get_mapped_value(tax_line, "amount")
                        ),
                        "currency_id": self._get_mapped_value(
                            source_data, "currency_id.name", default="NGN"
                        )
                    },
                    "tax_category": {
                        "id": self._get_mapped_value(tax_line, "tax_id.name", default="VAT"),
                        "percent": self._normalize_decimal(
                            self._get_mapped_value(tax_line, "tax_id.amount")
                        ),
                        "tax_scheme": {
                            "id": "VAT",
                            "name": "Value Added Tax"
                        }
                    }
                }
                tax_subtotals.append(subtotal)
            
            tax_total["tax_subtotals"] = tax_subtotals
        
        return tax_total
    
    def _transform_monetary_total(self, source_data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform legal monetary total"""
        totals_mapping = mapping.get("totals", {})
        currency = self._get_mapped_value(source_data, "currency_id.name", default="NGN")
        
        return {
            "line_extension_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(source_data, totals_mapping.get("subtotal", "amount_untaxed"))
                ),
                "currency_id": currency
            },
            "tax_exclusive_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(source_data, totals_mapping.get("tax_exclusive", "amount_untaxed"))
                ),
                "currency_id": currency
            },
            "tax_inclusive_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(source_data, totals_mapping.get("tax_inclusive", "amount_total"))
                ),
                "currency_id": currency
            },
            "payable_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(source_data, totals_mapping.get("payable", "amount_total"))
                ),
                "currency_id": currency
            }
        }
    
    def _transform_address(self, source_data: Dict[str, Any], address_mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Transform address information"""
        return {
            "street_name": self._get_mapped_value(
                source_data, address_mapping.get("street", "street")
            ),
            "additional_street_name": self._get_mapped_value(
                source_data, address_mapping.get("street2", "street2")
            ),
            "city_name": self._get_mapped_value(
                source_data, address_mapping.get("city", "city")
            ),
            "postal_zone": self._get_mapped_value(
                source_data, address_mapping.get("zip", "zip")
            ),
            "country_subentity": self._get_mapped_value(
                source_data, address_mapping.get("state", "state_id.name")
            ),
            "country": {
                "identification_code": self._get_mapped_value(
                    source_data, 
                    address_mapping.get("country_code", "country_id.code"),
                    default="NG"
                ),
                "name": self._get_mapped_value(
                    source_data,
                    address_mapping.get("country_name", "country_id.name"),
                    default="Nigeria"
                )
            }
        }
    
    def _transform_line_tax(self, line_data: Dict[str, Any], tax_mapping: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Transform tax information for a line item"""
        tax_data = self._get_mapped_value(line_data, tax_mapping.get("source_path", "invoice_line_tax_ids"))
        
        if not tax_data:
            return None
        
        return {
            "tax_amount": {
                "value": self._normalize_decimal(
                    self._get_mapped_value(tax_data, tax_mapping.get("amount", "amount"))
                ),
                "currency_id": "NGN"
            }
        }
    
    def _apply_firs_requirements(self, ubl_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FIRS-specific requirements to UBL data"""
        # Ensure Nigerian currency if not specified
        if ubl_data.get("currency_code") != "NGN":
            logger.warning("Converting currency to NGN for FIRS compliance")
            ubl_data["currency_code"] = "NGN"
        
        # Add FIRS document type classification
        ubl_data["firs_document_type"] = "INVOICE"
        
        # Ensure supplier has Nigerian tax ID
        supplier = ubl_data.get("accounting_supplier_party", {}).get("party", {})
        tax_schemes = supplier.get("party_tax_scheme", [])
        if not any(scheme.get("company_id") for scheme in tax_schemes):
            logger.warning("Supplier missing required Nigerian tax ID")
        
        return ubl_data
    
    def _apply_firs_document_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FIRS document structure requirements"""
        # Ensure required FIRS fields are present
        if "profile_id" not in data:
            data["profile_id"] = "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0"
        
        if "customization_id" not in data:
            data["customization_id"] = "urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0"
        
        return data
    
    def _apply_firs_tax_calculations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FIRS tax calculation requirements"""
        # Ensure VAT calculations are correct for Nigeria
        tax_total = data.get("tax_total", {})
        if tax_total:
            # Verify Nigerian VAT rate (7.5%)
            subtotals = tax_total.get("tax_subtotals", [])
            for subtotal in subtotals:
                tax_category = subtotal.get("tax_category", {})
                if tax_category.get("id") == "VAT" and not tax_category.get("percent"):
                    tax_category["percent"] = 7.5  # Standard Nigerian VAT rate
        
        return data
    
    def _apply_firs_party_requirements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FIRS party information requirements"""
        # Ensure supplier has required business information
        supplier_party = data.get("accounting_supplier_party", {}).get("party", {})
        if supplier_party and not supplier_party.get("party_legal_entity"):
            supplier_party["party_legal_entity"] = [
                {
                    "registration_name": supplier_party.get("party_name", [{}])[0].get("name", ""),
                    "company_id": "Required but not provided"
                }
            ]
        
        return data
    
    def _apply_firs_line_requirements(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply FIRS line item requirements"""
        lines = data.get("invoice_lines", [])
        for line in lines:
            # Ensure each line has required Nigerian classifications
            item = line.get("item", {})
            if "commodity_classification" not in item:
                item["commodity_classification"] = [
                    {
                        "item_class_code": "GENERAL",
                        "list_id": "HS"  # Harmonized System
                    }
                ]
        
        return data
    
    def _generate_firs_metadata(self) -> Dict[str, Any]:
        """Generate FIRS-specific metadata"""
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "version": "1.0",
            "compliance_level": "FIRS_NG_2024",
            "transformation_engine": "TaxPoynt Schema Transformer"
        }
    
    def _normalize_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize field values according to standards"""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                normalizer = self.field_normalizers.get(key)
                if normalizer:
                    normalized[key] = normalizer(value)
                elif isinstance(value, (dict, list)):
                    normalized[key] = self._normalize_fields(value)
                else:
                    normalized[key] = value
            return normalized
        elif isinstance(data, list):
            return [self._normalize_fields(item) for item in data]
        else:
            return data
    
    def _get_mapped_value(self, source: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Get value from source using dot notation path"""
        if not path or not source:
            return default
        
        try:
            value = source
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            return value if value is not None else default
        except (KeyError, TypeError, AttributeError):
            return default
    
    def _normalize_date(self, date_value: Any) -> str:
        """Normalize date to ISO format"""
        if isinstance(date_value, datetime):
            return date_value.strftime('%Y-%m-%d')
        elif isinstance(date_value, str):
            try:
                dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                return dt.strftime('%Y-%m-%d')
            except ValueError:
                return str(date_value)
        else:
            return str(date_value) if date_value else ""
    
    def _normalize_decimal(self, value: Any) -> str:
        """Normalize decimal values"""
        if value is None:
            return "0.00"
        try:
            decimal_value = Decimal(str(value))
            return f"{decimal_value:.2f}"
        except (ValueError, TypeError):
            return "0.00"
    
    def _load_transformation_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load transformation mappings for different source formats"""
        return {
            "odoo": {
                "invoice_header": {
                    "invoice_number": "number",
                    "invoice_date": "date_invoice",
                    "due_date": "date_due",
                    "currency_code": "currency_id.name"
                },
                "supplier": {
                    "source_path": "company_id",
                    "name": "name",
                    "tax_id": "vat",
                    "address": {
                        "street": "street",
                        "street2": "street2",
                        "city": "city",
                        "zip": "zip",
                        "state": "state_id.name",
                        "country_code": "country_id.code"
                    }
                },
                "customer": {
                    "source_path": "partner_id",
                    "name": "name",
                    "tax_id": "vat",
                    "address": {
                        "street": "street",
                        "street2": "street2",
                        "city": "city",
                        "zip": "zip",
                        "state": "state_id.name",
                        "country_code": "country_id.code"
                    }
                },
                "lines": {
                    "source_path": "invoice_line_ids",
                    "quantity": "quantity",
                    "unit_price": "price_unit",
                    "subtotal": "price_subtotal",
                    "product_name": "product_id.name",
                    "description": "name"
                },
                "tax": {
                    "total_amount": "amount_tax",
                    "tax_lines": "tax_line_ids"
                },
                "totals": {
                    "subtotal": "amount_untaxed",
                    "tax_inclusive": "amount_total",
                    "payable": "amount_total"
                }
            }
        }
    
    def _load_default_values(self) -> Dict[str, Any]:
        """Load default values for missing fields"""
        return {
            "currency_code": "NGN",
            "country_code": "NG",
            "invoice_type_code": "380",
            "unit_code": "EA",
            "tax_scheme": "VAT"
        }
    
    def _load_field_normalizers(self) -> Dict[str, callable]:
        """Load field normalization functions"""
        return {
            "currency_code": lambda x: str(x).upper() if x else "NGN",
            "country_code": lambda x: str(x).upper() if x else "NG",
            "invoice_number": lambda x: str(x).strip() if x else "",
            "tax_id": lambda x: str(x).strip() if x else ""
        }


# Global instance for easy access
schema_transformer = SchemaTransformer()