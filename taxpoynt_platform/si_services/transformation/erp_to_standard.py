"""
ERP to Standard Format Transformation Service

This service provides transformations from various ERP-specific data formats
to the standardized FIRS e-invoice format for consistent processing.
"""

from typing import Dict, Any, List, Optional, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ERPSystem(Enum):
    """Supported ERP systems"""
    ODOO = "odoo"
    SAP = "sap"
    GENERIC = "generic"
    QUICKBOOKS = "quickbooks"
    SAGE = "sage"


@dataclass
class StandardInvoiceFormat:
    """Standardized invoice format for FIRS compliance"""
    invoice_number: str
    invoice_date: str
    supplier_tin: str
    supplier_name: str
    supplier_address: Dict[str, str]
    customer_tin: Optional[str]
    customer_name: str
    customer_address: Dict[str, str]
    currency_code: str
    total_amount: float
    tax_amount: float
    discount_amount: float
    line_items: List[Dict[str, Any]]
    payment_terms: Optional[str]
    due_date: Optional[str]
    invoice_type: str
    exchange_rate: Optional[float]


class BaseERPTransformer(ABC):
    """Base class for ERP-specific transformers"""
    
    @abstractmethod
    def transform(self, erp_data: Dict[str, Any]) -> StandardInvoiceFormat:
        """Transform ERP-specific data to standard format"""
        pass
    
    @abstractmethod
    def validate_input(self, erp_data: Dict[str, Any]) -> bool:
        """Validate input data structure"""
        pass
    
    def normalize_currency(self, currency: str) -> str:
        """Normalize currency codes to ISO 4217"""
        currency_map = {
            "naira": "NGN",
            "₦": "NGN",
            "dollar": "USD",
            "$": "USD",
            "euro": "EUR",
            "€": "EUR"
        }
        return currency_map.get(currency.lower(), currency.upper())
    
    def parse_address(self, address_data: Any) -> Dict[str, str]:
        """Parse address from various formats"""
        if isinstance(address_data, str):
            return {"full_address": address_data}
        elif isinstance(address_data, dict):
            return {
                "street": address_data.get("street", ""),
                "city": address_data.get("city", ""),
                "state": address_data.get("state", ""),
                "country": address_data.get("country", "Nigeria"),
                "postal_code": address_data.get("postal_code", "")
            }
        return {"full_address": str(address_data)}


class OdooTransformer(BaseERPTransformer):
    """Transformer for Odoo ERP data"""
    
    def validate_input(self, erp_data: Dict[str, Any]) -> bool:
        """Validate Odoo data structure"""
        required_fields = ["name", "date_invoice", "partner_id", "invoice_line_ids"]
        return all(field in erp_data for field in required_fields)
    
    def transform(self, erp_data: Dict[str, Any]) -> StandardInvoiceFormat:
        """Transform Odoo invoice data to standard format"""
        if not self.validate_input(erp_data):
            raise ValueError("Invalid Odoo data structure")
        
        partner = erp_data.get("partner_id", {})
        company = erp_data.get("company_id", {})
        
        line_items = []
        for line in erp_data.get("invoice_line_ids", []):
            line_items.append({
                "description": line.get("name", ""),
                "quantity": line.get("quantity", 0),
                "unit_price": line.get("price_unit", 0),
                "tax_rate": sum(tax.get("amount", 0) for tax in line.get("invoice_line_tax_ids", [])),
                "total": line.get("price_subtotal", 0)
            })
        
        return StandardInvoiceFormat(
            invoice_number=erp_data["name"],
            invoice_date=erp_data["date_invoice"],
            supplier_tin=company.get("vat", ""),
            supplier_name=company.get("name", ""),
            supplier_address=self.parse_address(company.get("partner_id", {})),
            customer_tin=partner.get("vat"),
            customer_name=partner.get("name", ""),
            customer_address=self.parse_address(partner),
            currency_code=self.normalize_currency(erp_data.get("currency_id", {}).get("name", "NGN")),
            total_amount=erp_data.get("amount_total", 0),
            tax_amount=erp_data.get("amount_tax", 0),
            discount_amount=erp_data.get("amount_discount", 0),
            line_items=line_items,
            payment_terms=erp_data.get("payment_term_id", {}).get("name"),
            due_date=erp_data.get("date_due"),
            invoice_type=erp_data.get("type", "out_invoice"),
            exchange_rate=erp_data.get("currency_rate")
        )


class SAPTransformer(BaseERPTransformer):
    """Transformer for SAP ERP data"""
    
    def validate_input(self, erp_data: Dict[str, Any]) -> bool:
        """Validate SAP data structure"""
        required_fields = ["VBELN", "FKDAT", "KUNAG", "VBTYP"]
        return all(field in erp_data for field in required_fields)
    
    def transform(self, erp_data: Dict[str, Any]) -> StandardInvoiceFormat:
        """Transform SAP invoice data to standard format"""
        if not self.validate_input(erp_data):
            raise ValueError("Invalid SAP data structure")
        
        line_items = []
        for line in erp_data.get("items", []):
            line_items.append({
                "description": line.get("ARKTX", ""),
                "quantity": line.get("FKIMG", 0),
                "unit_price": line.get("NETPR", 0),
                "tax_rate": line.get("MWSKZ", 0),
                "total": line.get("NETWR", 0)
            })
        
        return StandardInvoiceFormat(
            invoice_number=erp_data["VBELN"],
            invoice_date=erp_data["FKDAT"],
            supplier_tin=erp_data.get("BUKRS_VAT", ""),
            supplier_name=erp_data.get("BUKRS_NAME", ""),
            supplier_address=self.parse_address(erp_data.get("supplier_address", {})),
            customer_tin=erp_data.get("KUNAG_VAT"),
            customer_name=erp_data.get("KUNAG_NAME", ""),
            customer_address=self.parse_address(erp_data.get("customer_address", {})),
            currency_code=self.normalize_currency(erp_data.get("WAERK", "NGN")),
            total_amount=erp_data.get("NETWR", 0),
            tax_amount=erp_data.get("MWSBP", 0),
            discount_amount=erp_data.get("KZWI1", 0),
            line_items=line_items,
            payment_terms=erp_data.get("ZTERM"),
            due_date=erp_data.get("ZFBDT"),
            invoice_type=erp_data.get("VBTYP", "F"),
            exchange_rate=erp_data.get("UKURS")
        )


class GenericTransformer(BaseERPTransformer):
    """Generic transformer for common ERP formats"""
    
    def validate_input(self, erp_data: Dict[str, Any]) -> bool:
        """Validate generic data structure"""
        required_fields = ["invoice_number", "invoice_date", "customer", "total"]
        return all(field in erp_data for field in required_fields)
    
    def transform(self, erp_data: Dict[str, Any]) -> StandardInvoiceFormat:
        """Transform generic invoice data to standard format"""
        if not self.validate_input(erp_data):
            raise ValueError("Invalid generic data structure")
        
        customer = erp_data.get("customer", {})
        supplier = erp_data.get("supplier", {})
        
        line_items = []
        for line in erp_data.get("line_items", []):
            line_items.append({
                "description": line.get("description", ""),
                "quantity": line.get("quantity", 0),
                "unit_price": line.get("unit_price", 0),
                "tax_rate": line.get("tax_rate", 0),
                "total": line.get("total", 0)
            })
        
        return StandardInvoiceFormat(
            invoice_number=erp_data["invoice_number"],
            invoice_date=erp_data["invoice_date"],
            supplier_tin=supplier.get("tin", ""),
            supplier_name=supplier.get("name", ""),
            supplier_address=self.parse_address(supplier.get("address", {})),
            customer_tin=customer.get("tin"),
            customer_name=customer.get("name", ""),
            customer_address=self.parse_address(customer.get("address", {})),
            currency_code=self.normalize_currency(erp_data.get("currency", "NGN")),
            total_amount=erp_data.get("total", 0),
            tax_amount=erp_data.get("tax_amount", 0),
            discount_amount=erp_data.get("discount", 0),
            line_items=line_items,
            payment_terms=erp_data.get("payment_terms"),
            due_date=erp_data.get("due_date"),
            invoice_type=erp_data.get("invoice_type", "invoice"),
            exchange_rate=erp_data.get("exchange_rate")
        )


class ERPToStandardTransformer:
    """Main service for transforming ERP data to standard format"""
    
    def __init__(self):
        self.transformers: Dict[ERPSystem, BaseERPTransformer] = {
            ERPSystem.ODOO: OdooTransformer(),
            ERPSystem.SAP: SAPTransformer(),
            ERPSystem.GENERIC: GenericTransformer()
        }
    
    def register_transformer(self, erp_system: ERPSystem, transformer: BaseERPTransformer):
        """Register a new transformer for an ERP system"""
        self.transformers[erp_system] = transformer
    
    def transform(self, erp_data: Dict[str, Any], erp_system: ERPSystem) -> StandardInvoiceFormat:
        """Transform ERP data to standard format"""
        transformer = self.transformers.get(erp_system)
        if not transformer:
            raise ValueError(f"No transformer available for ERP system: {erp_system}")
        
        try:
            logger.info(f"Transforming {erp_system.value} data to standard format")
            result = transformer.transform(erp_data)
            logger.info(f"Successfully transformed invoice {result.invoice_number}")
            return result
        except Exception as e:
            logger.error(f"Failed to transform {erp_system.value} data: {str(e)}")
            raise
    
    def auto_detect_and_transform(self, erp_data: Dict[str, Any]) -> StandardInvoiceFormat:
        """Auto-detect ERP system and transform data"""
        for erp_system, transformer in self.transformers.items():
            try:
                if transformer.validate_input(erp_data):
                    logger.info(f"Auto-detected ERP system: {erp_system.value}")
                    return transformer.transform(erp_data)
            except Exception:
                continue
        
        logger.warning("Could not auto-detect ERP system, using generic transformer")
        return self.transformers[ERPSystem.GENERIC].transform(erp_data)
    
    def get_supported_systems(self) -> List[str]:
        """Get list of supported ERP systems"""
        return [system.value for system in self.transformers.keys()]