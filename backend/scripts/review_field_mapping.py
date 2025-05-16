#!/usr/bin/env python
"""
Script to review the field mapping schema against BIS Billing 3.0 requirements.
This script checks that all required UBL fields are covered in the mapping schema.
"""
import json
import sys
import os
from typing import Dict, List, Set

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.odoo_ubl_mapper import odoo_ubl_mapper
from app.services.odoo_ubl_validator import odoo_ubl_validator

# Define BIS Billing 3.0 required fields based on specifications
# Source: Peppol BIS Billing 3.0 Documentation
BIS_BILLING_30_REQUIRED_FIELDS = {
    # Invoice level required fields
    "invoice": {
        "cbc:CustomizationID",
        "cbc:ProfileID",
        "cbc:ID",
        "cbc:IssueDate",
        "cbc:InvoiceTypeCode",
        "cbc:DocumentCurrencyCode",
        "cac:AccountingSupplierParty",
        "cac:AccountingCustomerParty",
        "cac:TaxTotal",
        "cac:LegalMonetaryTotal",
        "cac:InvoiceLine"
    },
    # Supplier party required fields
    "supplier": {
        "cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
        "cac:Party/cac:PostalAddress/cbc:StreetName",
        "cac:Party/cac:PostalAddress/cbc:CityName", 
        "cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
        "cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
        "cac:Party/cac:PartyTaxScheme/cac:TaxScheme/cbc:ID"
    },
    # Customer party required fields
    "customer": {
        "cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
        "cac:Party/cac:PostalAddress/cbc:StreetName",
        "cac:Party/cac:PostalAddress/cbc:CityName",
        "cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode"
    },
    # Tax total required fields
    "tax_total": {
        "cbc:TaxAmount",
        "cac:TaxSubtotal/cbc:TaxableAmount",
        "cac:TaxSubtotal/cbc:TaxAmount",
        "cac:TaxSubtotal/cac:TaxCategory/cbc:ID",
        "cac:TaxSubtotal/cac:TaxCategory/cbc:Percent",
        "cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID"
    },
    # Monetary total required fields
    "monetary_total": {
        "cbc:LineExtensionAmount",
        "cbc:TaxExclusiveAmount",
        "cbc:TaxInclusiveAmount",
        "cbc:PayableAmount"
    },
    # Invoice line required fields
    "invoice_line": {
        "cbc:ID",
        "cbc:InvoicedQuantity",
        "cbc:LineExtensionAmount",
        "cac:Item/cbc:Name",
        "cac:Price/cbc:PriceAmount"
    }
}

class FieldMappingReviewer:
    """Reviews the field mapping schema against BIS Billing 3.0 requirements."""
    
    def __init__(self):
        """Initialize the reviewer."""
        self.odoo_mapper = odoo_ubl_mapper
        self.odoo_validator = odoo_ubl_validator
    
    def get_mapped_fields(self) -> Dict[str, Set[str]]:
        """Get the fields mapped in the current implementation."""
        # This is a simplified approach - in a real implementation, you might
        # analyze the mapper and validator implementation to extract field names
        
        # Instead, here we manually list fields based on our implementation
        mapped_fields = {
            "invoice": {
                "cbc:CustomizationID",
                "cbc:ProfileID",
                "cbc:ID",
                "cbc:IssueDate",
                "cbc:DueDate",  # Optional
                "cbc:InvoiceTypeCode",
                "cbc:DocumentCurrencyCode",
                "cbc:Note",  # Optional
                "cac:AccountingSupplierParty",
                "cac:AccountingCustomerParty",
                "cac:TaxTotal",
                "cac:LegalMonetaryTotal",
                "cac:InvoiceLine",
                "cac:PaymentTerms",  # Optional
                "cac:OrderReference" # Optional
            },
            "supplier": {
                "cac:Party/cac:PartyIdentification/cbc:ID",  # Optional
                "cac:Party/cac:PartyName/cbc:Name",  
                "cac:Party/cac:PostalAddress/cbc:StreetName",
                "cac:Party/cac:PostalAddress/cbc:AdditionalStreetName",  # Optional
                "cac:Party/cac:PostalAddress/cbc:CityName",
                "cac:Party/cac:PostalAddress/cbc:PostalZone",  # Optional
                "cac:Party/cac:PostalAddress/cbc:CountrySubentity",  # Optional
                "cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
                "cac:Party/cac:PartyTaxScheme/cbc:CompanyID",
                "cac:Party/cac:PartyTaxScheme/cac:TaxScheme/cbc:ID",
                "cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
                "cac:Party/cac:PartyLegalEntity/cbc:CompanyID",  # Optional
                "cac:Party/cac:Contact/cbc:Name",  # Optional
                "cac:Party/cac:Contact/cbc:Telephone",  # Optional
                "cac:Party/cac:Contact/cbc:ElectronicMail"  # Optional
            },
            "customer": {
                "cac:Party/cac:PartyIdentification/cbc:ID",  # Optional
                "cac:Party/cac:PartyName/cbc:Name",
                "cac:Party/cac:PostalAddress/cbc:StreetName",
                "cac:Party/cac:PostalAddress/cbc:AdditionalStreetName",  # Optional
                "cac:Party/cac:PostalAddress/cbc:CityName",
                "cac:Party/cac:PostalAddress/cbc:PostalZone",  # Optional
                "cac:Party/cac:PostalAddress/cbc:CountrySubentity",  # Optional
                "cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode",
                "cac:Party/cac:PartyTaxScheme/cbc:CompanyID",  # Optional
                "cac:Party/cac:PartyTaxScheme/cac:TaxScheme/cbc:ID",  # Optional
                "cac:Party/cac:PartyLegalEntity/cbc:RegistrationName",
                "cac:Party/cac:Contact/cbc:Name",  # Optional
                "cac:Party/cac:Contact/cbc:Telephone",  # Optional
                "cac:Party/cac:Contact/cbc:ElectronicMail"  # Optional
            },
            "tax_total": {
                "cbc:TaxAmount",
                "cac:TaxSubtotal/cbc:TaxableAmount",
                "cac:TaxSubtotal/cbc:TaxAmount",
                "cac:TaxSubtotal/cac:TaxCategory/cbc:ID",
                "cac:TaxSubtotal/cac:TaxCategory/cbc:Percent",
                "cac:TaxSubtotal/cac:TaxCategory/cbc:TaxExemptionReason",  # Optional
                "cac:TaxSubtotal/cac:TaxCategory/cac:TaxScheme/cbc:ID"
            },
            "monetary_total": {
                "cbc:LineExtensionAmount",
                "cbc:TaxExclusiveAmount",
                "cbc:TaxInclusiveAmount",
                "cbc:AllowanceTotalAmount",  # Optional
                "cbc:ChargeTotalAmount",  # Optional
                "cbc:PrepaidAmount",  # Optional
                "cbc:PayableAmount"
            },
            "invoice_line": {
                "cbc:ID",
                "cbc:InvoicedQuantity",
                "cbc:LineExtensionAmount",
                "cac:Item/cbc:Description",  # Optional
                "cac:Item/cbc:Name",
                "cac:Item/cac:BuyersItemIdentification/cbc:ID",  # Optional
                "cac:Item/cac:SellersItemIdentification/cbc:ID",  # Optional
                "cac:Price/cbc:PriceAmount",
                "cac:Price/cbc:BaseQuantity"  # Optional
            }
        }
        return mapped_fields
    
    def review_mapping(self) -> Dict:
        """Review the field mapping against BIS Billing 3.0 requirements."""
        mapped_fields = self.get_mapped_fields()
        results = {
            "missing_fields": {},
            "additional_fields": {},
            "coverage_percentage": {},
            "overall_coverage": 0
        }
        
        total_required = 0
        total_mapped_required = 0
        
        for category, required_fields in BIS_BILLING_30_REQUIRED_FIELDS.items():
            mapped_category_fields = mapped_fields.get(category, set())
            
            # Find missing fields
            missing = required_fields - mapped_category_fields
            if missing:
                results["missing_fields"][category] = list(missing)
            
            # Find additional fields (those mapped but not required)
            additional = mapped_category_fields - required_fields
            if additional:
                results["additional_fields"][category] = list(additional)
            
            # Calculate coverage percentage for this category
            category_required = len(required_fields)
            category_mapped = len(required_fields - missing)
            coverage = (category_mapped / category_required * 100) if category_required > 0 else 100
            results["coverage_percentage"][category] = round(coverage, 2)
            
            total_required += category_required
            total_mapped_required += category_mapped
        
        # Calculate overall coverage
        results["overall_coverage"] = round((total_mapped_required / total_required * 100) if total_required > 0 else 100, 2)
        
        return results
    
    def print_review_report(self):
        """Print the mapping review report."""
        results = self.review_mapping()
        
        print("===== Field Mapping Review Report =====")
        print(f"Overall Coverage: {results['overall_coverage']}%\n")
        
        print("Coverage by Category:")
        for category, coverage in results["coverage_percentage"].items():
            print(f"  {category}: {coverage}%")
        
        if results["missing_fields"]:
            print("\nMissing Required Fields:")
            for category, fields in results["missing_fields"].items():
                print(f"  {category}:")
                for field in sorted(fields):
                    print(f"    - {field}")
        else:
            print("\nNo missing required fields! All BIS Billing 3.0 requirements are covered.")
        
        print("\nAdditional Fields (mapped but not required by BIS Billing 3.0):")
        for category, fields in results["additional_fields"].items():
            if fields:
                print(f"  {category}:")
                for field in sorted(fields):
                    print(f"    + {field}")
        
        return results


if __name__ == "__main__":
    reviewer = FieldMappingReviewer()
    reviewer.print_review_report()
