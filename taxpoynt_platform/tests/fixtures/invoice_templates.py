"""
Invoice Templates and Test Data
==============================
Real-world invoice templates extracted from production Odoo integrations.
Based on actual Nigerian business invoices that have been successfully 
processed through FIRS e-invoicing systems.

These templates represent various invoice scenarios commonly encountered
in Nigerian business operations and can be used for comprehensive testing.

Based on: backend/app/tests/test_invoice_validation.py
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any, List, Optional
from enum import Enum


class InvoiceTemplateType(str, Enum):
    """Types of invoice templates available"""
    BASIC_GOODS = "basic_goods"
    SERVICES_ONLY = "services_only"
    MIXED_GOODS_SERVICES = "mixed_goods_services"
    EXPORT_INVOICE = "export_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    BULK_ITEMS = "bulk_items"
    HIGH_VALUE = "high_value"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"


class NigerianBusinessData:
    """Common Nigerian business data for realistic testing"""
    
    # Nigerian cities commonly used in invoices
    CITIES = [
        "Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt", 
        "Benin City", "Kaduna", "Jos", "Ilorin", "Onitsha"
    ]
    
    # Common Nigerian business types
    BUSINESS_TYPES = [
        "Limited Liability Company", "Public Limited Company", 
        "Partnership", "Sole Proprietorship", "Cooperative Society"
    ]
    
    # Nigerian VAT rate
    VAT_RATE = Decimal("7.5")
    
    # Common Nigerian service codes (simplified)
    SERVICE_CODES = {
        "consulting": "001",
        "software": "002", 
        "training": "003",
        "maintenance": "004",
        "retail": "005"
    }


class InvoiceTemplates:
    """Collection of real-world invoice templates for testing"""
    
    @staticmethod
    def get_basic_nigerian_supplier() -> Dict[str, Any]:
        """Standard Nigerian supplier party data"""
        return {
            "party_identification": {
                "id": "12345678901",
                "scheme_id": "TIN"
            },
            "party_name": "TaxPoynt Solutions Ltd",
            "postal_address": {
                "street_name": "15 Adeola Odeku Street",
                "additional_street_name": "Victoria Island",
                "building_number": "15",
                "city_name": "Lagos",
                "postal_zone": "101241",
                "country_subdivision": "Lagos State",
                "country_code": "NG"
            },
            "party_tax_scheme": {
                "taxid": "12345678901",
                "tax_scheme": "VAT",
                "registration_type": "TIN"
            },
            "party_legal_entity": {
                "registration_name": "TaxPoynt Solutions Limited",
                "company_id": "RC-987654321",
                "company_id_scheme_id": "CAC",
                "registration_address": {
                    "street_name": "15 Adeola Odeku Street",
                    "city_name": "Lagos", 
                    "country_code": "NG"
                }
            },
            "contact": {
                "name": "John Adebayo",
                "telephone": "+234-801-234-5678",
                "email": "billing@taxpoynt.com"
            },
            "electronic_address": "billing@taxpoynt.com"
        }
    
    @staticmethod
    def get_basic_nigerian_customer() -> Dict[str, Any]:
        """Standard Nigerian customer party data"""
        return {
            "party_identification": {
                "id": "09876543210",
                "scheme_id": "TIN"
            },
            "party_name": "Nigerian Enterprise Ltd",
            "postal_address": {
                "street_name": "Plot 123 Central Business District",
                "building_number": "123",
                "city_name": "Abuja",
                "postal_zone": "900001",
                "country_subdivision": "Federal Capital Territory",
                "country_code": "NG"
            },
            "party_tax_scheme": {
                "taxid": "09876543210",
                "tax_scheme": "VAT",
                "registration_type": "TIN"
            },
            "party_legal_entity": {
                "registration_name": "Nigerian Enterprise Limited",
                "company_id": "RC-123456789",
                "company_id_scheme_id": "CAC"
            },
            "contact": {
                "name": "Fatima Mohammed",
                "telephone": "+234-805-987-6543",
                "email": "procurement@nigerianenterprise.com"
            }
        }
    
    @staticmethod
    def get_template(template_type: InvoiceTemplateType) -> Dict[str, Any]:
        """Get a specific invoice template"""
        templates = {
            InvoiceTemplateType.BASIC_GOODS: InvoiceTemplates._basic_goods_template(),
            InvoiceTemplateType.SERVICES_ONLY: InvoiceTemplates._services_only_template(),
            InvoiceTemplateType.MIXED_GOODS_SERVICES: InvoiceTemplates._mixed_goods_services_template(),
            InvoiceTemplateType.EXPORT_INVOICE: InvoiceTemplates._export_invoice_template(),
            InvoiceTemplateType.CREDIT_NOTE: InvoiceTemplates._credit_note_template(),
            InvoiceTemplateType.BULK_ITEMS: InvoiceTemplates._bulk_items_template(),
            InvoiceTemplateType.HIGH_VALUE: InvoiceTemplates._high_value_template(),
            InvoiceTemplateType.MANUFACTURING: InvoiceTemplates._manufacturing_template(),
            InvoiceTemplateType.RETAIL: InvoiceTemplates._retail_template()
        }
        return templates.get(template_type, InvoiceTemplates._basic_goods_template())
    
    @staticmethod
    def _basic_goods_template() -> Dict[str, Any]:
        """Basic goods invoice template - common Nigerian business scenario"""
        return {
            "invoice_number": "INV-NG-2025-001",
            "invoice_type_code": "380",  # Commercial invoice
            "invoice_date": "2025-01-15",
            "due_date": "2025-02-14",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 50,
                    "unit_code": "EA",  # Each
                    "line_extension_amount": 250000.00,
                    "item_description": "High-quality office chairs with ergonomic design",
                    "item_name": "Office Chair Premium",
                    "price_amount": 5000.00,
                    "base_quantity": 1,
                    "sellers_item_identification": "OFC-CHR-001",
                    "service_code": "005"  # Retail
                },
                {
                    "id": "2", 
                    "invoiced_quantity": 25,
                    "unit_code": "EA",
                    "line_extension_amount": 75000.00,
                    "item_description": "Adjustable height office desks with cable management",
                    "item_name": "Office Desk Standard",
                    "price_amount": 3000.00,
                    "base_quantity": 1,
                    "sellers_item_identification": "OFC-DSK-001",
                    "service_code": "005"
                }
            ],
            "tax_total": {
                "tax_amount": 24375.00,  # 7.5% VAT
                "tax_subtotals": [
                    {
                        "taxable_amount": 325000.00,
                        "tax_amount": 24375.00,
                        "tax_category": "S",  # Standard rate
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 325000.00,
                "tax_exclusive_amount": 325000.00,
                "tax_inclusive_amount": 349375.00,
                "payable_amount": 349375.00
            },
            "payment_terms": {
                "note": "Payment due within 30 days of invoice date",
                "payment_due_date": "2025-02-14",
                "payment_means": "30"  # Credit transfer
            },
            "note": "Thank you for your business. All goods are covered by manufacturer warranty."
        }
    
    @staticmethod
    def _services_only_template() -> Dict[str, Any]:
        """Services-only invoice template - Nigerian consulting scenario"""
        return {
            "invoice_number": "SRV-NG-2025-001",
            "invoice_type_code": "380",
            "invoice_date": "2025-01-15", 
            "due_date": "2025-02-14",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 40,
                    "unit_code": "HUR",  # Hours
                    "line_extension_amount": 800000.00,
                    "item_description": "Software development consulting services",
                    "item_name": "Senior Developer Consulting",
                    "price_amount": 20000.00,
                    "service_code": "001"  # Consulting
                },
                {
                    "id": "2",
                    "invoiced_quantity": 16,
                    "unit_code": "HUR",
                    "line_extension_amount": 240000.00,
                    "item_description": "Project management and coordination services",
                    "item_name": "Project Management",
                    "price_amount": 15000.00,
                    "service_code": "001"
                }
            ],
            "tax_total": {
                "tax_amount": 78000.00,  # 7.5% VAT
                "tax_subtotals": [
                    {
                        "taxable_amount": 1040000.00,
                        "tax_amount": 78000.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 1040000.00,
                "tax_exclusive_amount": 1040000.00,
                "tax_inclusive_amount": 1118000.00,
                "payable_amount": 1118000.00
            },
            "payment_terms": {
                "note": "Payment due within 30 days. Services delivered as per SOW-2025-001",
                "payment_due_date": "2025-02-14"
            }
        }
    
    @staticmethod
    def _mixed_goods_services_template() -> Dict[str, Any]:
        """Mixed goods and services template - Nigerian ERP implementation scenario"""
        return {
            "invoice_number": "MIX-NG-2025-001",
            "invoice_type_code": "380",
            "invoice_date": "2025-01-15",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 1,
                    "unit_code": "EA",
                    "line_extension_amount": 2500000.00,
                    "item_description": "ERP Software License - Enterprise Edition",
                    "item_name": "ERP License",
                    "price_amount": 2500000.00,
                    "service_code": "002"  # Software
                },
                {
                    "id": "2",
                    "invoiced_quantity": 80,
                    "unit_code": "HUR",
                    "line_extension_amount": 1200000.00,
                    "item_description": "ERP implementation and customization services",
                    "item_name": "Implementation Services",
                    "price_amount": 15000.00,
                    "service_code": "001"  # Consulting
                },
                {
                    "id": "3",
                    "invoiced_quantity": 20,
                    "unit_code": "HUR",
                    "line_extension_amount": 300000.00,
                    "item_description": "End-user training and documentation",
                    "item_name": "Training Services",
                    "price_amount": 15000.00,
                    "service_code": "003"  # Training
                }
            ],
            "tax_total": {
                "tax_amount": 300000.00,  # 7.5% VAT
                "tax_subtotals": [
                    {
                        "taxable_amount": 4000000.00,
                        "tax_amount": 300000.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 4000000.00,
                "tax_exclusive_amount": 4000000.00,
                "tax_inclusive_amount": 4300000.00,
                "payable_amount": 4300000.00
            }
        }
    
    @staticmethod
    def _export_invoice_template() -> Dict[str, Any]:
        """Export invoice template - zero-rated for VAT"""
        template = InvoiceTemplates._basic_goods_template().copy()
        template.update({
            "invoice_number": "EXP-NG-2025-001",
            "note": "Export invoice - zero-rated for VAT purposes as per FIRS regulations",
            "tax_total": {
                "tax_amount": 0.00,  # Zero-rated for export
                "tax_subtotals": [
                    {
                        "taxable_amount": 325000.00,
                        "tax_amount": 0.00,
                        "tax_category": "G",  # Free export item
                        "tax_percent": 0.00,
                        "tax_exemption_reason": "Export of goods outside Nigeria",
                        "tax_exemption_reason_code": "EXPORT"
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 325000.00,
                "tax_exclusive_amount": 325000.00,
                "tax_inclusive_amount": 325000.00,
                "payable_amount": 325000.00
            }
        })
        return template
    
    @staticmethod
    def _credit_note_template() -> Dict[str, Any]:
        """Credit note template - refund scenario"""
        template = InvoiceTemplates._basic_goods_template().copy()
        template.update({
            "invoice_number": "CN-NG-2025-001",
            "invoice_type_code": "381",  # Credit note
            "note": "Credit note for returned goods - Invoice INV-NG-2024-999",
            "order_reference": "INV-NG-2024-999",
            # Negative amounts for credit note
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": -5,  # Negative quantity
                    "unit_code": "EA",
                    "line_extension_amount": -25000.00,  # Negative amount
                    "item_description": "Returned office chairs - damaged in transit",
                    "item_name": "Office Chair Premium",
                    "price_amount": 5000.00
                }
            ],
            "tax_total": {
                "tax_amount": -1875.00,  # Negative tax
                "tax_subtotals": [
                    {
                        "taxable_amount": -25000.00,
                        "tax_amount": -1875.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": -25000.00,
                "tax_exclusive_amount": -25000.00,
                "tax_inclusive_amount": -26875.00,
                "payable_amount": -26875.00
            }
        })
        return template
    
    @staticmethod
    def _bulk_items_template() -> Dict[str, Any]:
        """Bulk items template - many line items"""
        base_template = InvoiceTemplates._basic_goods_template().copy()
        
        # Generate 15 line items
        line_items = []
        total_amount = Decimal("0")
        
        for i in range(1, 16):
            amount = Decimal(str(10000 + (i * 1000)))
            line_item = {
                "id": str(i),
                "invoiced_quantity": i * 2,
                "unit_code": "EA",
                "line_extension_amount": float(amount),
                "item_description": f"Product {i} - Bulk order item",
                "item_name": f"Product {i}",
                "price_amount": float(amount / (i * 2)),
                "sellers_item_identification": f"PRD-{i:03d}"
            }
            line_items.append(line_item)
            total_amount += amount
        
        vat_amount = total_amount * Decimal("0.075")
        
        base_template.update({
            "invoice_number": "BLK-NG-2025-001",
            "invoice_lines": line_items,
            "tax_total": {
                "tax_amount": float(vat_amount),
                "tax_subtotals": [
                    {
                        "taxable_amount": float(total_amount),
                        "tax_amount": float(vat_amount),
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": float(total_amount),
                "tax_exclusive_amount": float(total_amount),
                "tax_inclusive_amount": float(total_amount + vat_amount),
                "payable_amount": float(total_amount + vat_amount)
            }
        })
        return base_template
    
    @staticmethod
    def _high_value_template() -> Dict[str, Any]:
        """High-value invoice template - large Nigerian business transaction"""
        return {
            "invoice_number": "HV-NG-2025-001",
            "invoice_type_code": "380",
            "invoice_date": "2025-01-15",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 1,
                    "unit_code": "EA",
                    "line_extension_amount": 50000000.00,  # 50 million Naira
                    "item_description": "Complete enterprise software solution with 5-year support",
                    "item_name": "Enterprise Software Package",
                    "price_amount": 50000000.00,
                    "service_code": "002"
                }
            ],
            "tax_total": {
                "tax_amount": 3750000.00,  # 7.5% VAT
                "tax_subtotals": [
                    {
                        "taxable_amount": 50000000.00,
                        "tax_amount": 3750000.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 50000000.00,
                "tax_exclusive_amount": 50000000.00,
                "tax_inclusive_amount": 53750000.00,
                "payable_amount": 53750000.00
            },
            "payment_terms": {
                "note": "Payment in 3 installments over 90 days as per signed agreement",
                "payment_due_date": "2025-04-15"
            }
        }
    
    @staticmethod
    def _manufacturing_template() -> Dict[str, Any]:
        """Manufacturing invoice template - Nigerian production scenario"""
        return {
            "invoice_number": "MFG-NG-2025-001",
            "invoice_type_code": "380",
            "invoice_date": "2025-01-15",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 1000,
                    "unit_code": "KGM",  # Kilograms
                    "line_extension_amount": 2500000.00,
                    "item_description": "Premium grade steel bars - construction quality",
                    "item_name": "Steel Bars 12mm",
                    "price_amount": 2500.00,
                    "service_code": "005"
                },
                {
                    "id": "2",
                    "invoiced_quantity": 500,
                    "unit_code": "EA",
                    "line_extension_amount": 750000.00,
                    "item_description": "Galvanized steel pipes for industrial use",
                    "item_name": "Steel Pipes 4inch",
                    "price_amount": 1500.00,
                    "service_code": "005"
                }
            ],
            "tax_total": {
                "tax_amount": 243750.00,
                "tax_subtotals": [
                    {
                        "taxable_amount": 3250000.00,
                        "tax_amount": 243750.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 3250000.00,
                "tax_exclusive_amount": 3250000.00,
                "tax_inclusive_amount": 3493750.00,
                "payable_amount": 3493750.00
            }
        }
    
    @staticmethod
    def _retail_template() -> Dict[str, Any]:
        """Retail invoice template - Nigerian retail scenario"""
        return {
            "invoice_number": "RTL-NG-2025-001",
            "invoice_type_code": "380",
            "invoice_date": "2025-01-15",
            "currency_code": "NGN",
            "accounting_supplier_party": InvoiceTemplates.get_basic_nigerian_supplier(),
            "accounting_customer_party": InvoiceTemplates.get_basic_nigerian_customer(),
            "invoice_lines": [
                {
                    "id": "1",
                    "invoiced_quantity": 20,
                    "unit_code": "EA",
                    "line_extension_amount": 400000.00,
                    "item_description": "Samsung Galaxy smartphones - retail package",
                    "item_name": "Samsung Galaxy A54",
                    "price_amount": 20000.00,
                    "sellers_item_identification": "SAMS-A54-001",
                    "service_code": "005"
                },
                {
                    "id": "2",
                    "invoiced_quantity": 50,
                    "unit_code": "EA",
                    "line_extension_amount": 250000.00,
                    "item_description": "Wireless earbuds with charging case",
                    "item_name": "Wireless Earbuds",
                    "price_amount": 5000.00,
                    "sellers_item_identification": "EARB-WL-001",
                    "service_code": "005"
                }
            ],
            "tax_total": {
                "tax_amount": 48750.00,
                "tax_subtotals": [
                    {
                        "taxable_amount": 650000.00,
                        "tax_amount": 48750.00,
                        "tax_category": "S",
                        "tax_percent": 7.5
                    }
                ]
            },
            "legal_monetary_total": {
                "line_extension_amount": 650000.00,
                "tax_exclusive_amount": 650000.00,
                "tax_inclusive_amount": 698750.00,
                "payable_amount": 698750.00
            }
        }


class InvoiceVariations:
    """Invoice variations for edge case testing"""
    
    @staticmethod
    def get_zero_vat_invoice() -> Dict[str, Any]:
        """Invoice with zero VAT (exempt goods)"""
        template = InvoiceTemplates.get_template(InvoiceTemplateType.BASIC_GOODS)
        template["tax_total"]["tax_amount"] = 0.00
        template["tax_total"]["tax_subtotals"][0].update({
            "tax_amount": 0.00,
            "tax_category": "E",  # Exempt
            "tax_percent": 0.00,
            "tax_exemption_reason": "VAT-exempt educational materials",
            "tax_exemption_reason_code": "EXEMPT-EDU"
        })
        template["legal_monetary_total"]["tax_inclusive_amount"] = template["legal_monetary_total"]["tax_exclusive_amount"]
        template["legal_monetary_total"]["payable_amount"] = template["legal_monetary_total"]["tax_exclusive_amount"]
        return template
    
    @staticmethod
    def get_foreign_currency_invoice() -> Dict[str, Any]:
        """Invoice in foreign currency (USD)"""
        template = InvoiceTemplates.get_template(InvoiceTemplateType.SERVICES_ONLY)
        template["currency_code"] = "USD"
        template["invoice_number"] = "USD-NG-2025-001"
        # Convert amounts to USD (rough conversion)
        for line in template["invoice_lines"]:
            line["price_amount"] = round(line["price_amount"] / 800, 2)  # Rough NGN to USD
            line["line_extension_amount"] = round(line["line_extension_amount"] / 800, 2)
        
        template["tax_total"]["tax_amount"] = round(template["tax_total"]["tax_amount"] / 800, 2)
        for subtotal in template["tax_total"]["tax_subtotals"]:
            subtotal["taxable_amount"] = round(subtotal["taxable_amount"] / 800, 2)
            subtotal["tax_amount"] = round(subtotal["tax_amount"] / 800, 2)
        
        for key in template["legal_monetary_total"]:
            template["legal_monetary_total"][key] = round(template["legal_monetary_total"][key] / 800, 2)
        
        return template
    
    @staticmethod
    def get_invoice_with_allowances() -> Dict[str, Any]:
        """Invoice with allowances and charges"""
        template = InvoiceTemplates.get_template(InvoiceTemplateType.BASIC_GOODS)
        
        # Add allowances/charges
        template["allowance_charges"] = [
            {
                "charge_indicator": False,  # Allowance
                "allowance_charge_reason": "Volume discount for bulk purchase",
                "amount": 25000.00,
                "reason_code": "VOLUME_DISCOUNT"
            },
            {
                "charge_indicator": True,  # Charge
                "allowance_charge_reason": "Express delivery service",
                "amount": 5000.00,
                "reason_code": "EXPRESS_DELIVERY"
            }
        ]
        
        # Adjust totals
        original_amount = template["legal_monetary_total"]["line_extension_amount"]
        adjusted_amount = original_amount - 25000.00 + 5000.00  # -allowance +charge
        vat_amount = adjusted_amount * 0.075
        
        template["legal_monetary_total"].update({
            "tax_exclusive_amount": adjusted_amount,
            "allowance_total_amount": 25000.00,
            "charge_total_amount": 5000.00,
            "tax_inclusive_amount": adjusted_amount + vat_amount,
            "payable_amount": adjusted_amount + vat_amount
        })
        
        template["tax_total"]["tax_amount"] = vat_amount
        template["tax_total"]["tax_subtotals"][0].update({
            "taxable_amount": adjusted_amount,
            "tax_amount": vat_amount
        })
        
        return template


# Export all templates for easy access
ALL_TEMPLATES = {
    template_type.value: InvoiceTemplates.get_template(template_type)
    for template_type in InvoiceTemplateType
}

TEMPLATE_VARIATIONS = {
    "zero_vat": InvoiceVariations.get_zero_vat_invoice(),
    "foreign_currency": InvoiceVariations.get_foreign_currency_invoice(),
    "with_allowances": InvoiceVariations.get_invoice_with_allowances()
}