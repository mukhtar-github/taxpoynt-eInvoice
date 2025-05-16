"""
Unit tests for the Odoo UBL Validator component.
"""
import unittest
from decimal import Decimal
from datetime import date, datetime

from app.schemas.invoice_validation import (
    InvoiceValidationRequest, AccountingParty, PostalAddress,
    PartyTaxScheme, PartyLegalEntity, Contact, InvoiceLine,
    TaxTotal, TaxSubtotal, TaxCategory, LegalMonetaryTotal,
    PaymentTerms, InvoiceTypeCode, CurrencyCode, UnitCode
)
from app.services.odoo_ubl_validator import OdooUBLValidator, odoo_ubl_validator


class TestOdooUBLValidator(unittest.TestCase):
    """Test cases for the Odoo UBL Validator."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = OdooUBLValidator()
        
        # Create a valid invoice for testing
        self.valid_invoice = self._create_valid_invoice()
        
        # Create various invalid invoices for testing different validation failures
        self.invoice_missing_required = self._create_invalid_invoice_missing_required()
        self.invoice_with_total_mismatch = self._create_invoice_with_total_mismatch()
        self.invoice_with_invalid_dates = self._create_invoice_with_invalid_dates()
    
    def _create_valid_invoice(self) -> InvoiceValidationRequest:
        """Create a valid invoice for testing."""
        # Create supplier party
        supplier_address = PostalAddress(
            street_name="123 Supplier St",
            city_name="Supplier City",
            country_code="NG",
            postal_zone="12345",
            country_subdivision="Lagos"
        )
        
        supplier_party = AccountingParty(
            party_name="Supplier Company Ltd",
            postal_address=supplier_address,
            party_tax_scheme={"company_id": "NG1234567890", "tax_scheme_id": "VAT"},
            party_legal_entity=PartyLegalEntity(
                registration_name="Supplier Company Ltd",
                company_id="RC123456",
                company_id_scheme_id="NG-CAC"
            ),
            contact={"name": "John Supplier", "telephone": "+2341234567890", "email": "john@supplier.com"}
        )
        
        # Create customer party
        customer_address = PostalAddress(
            street_name="456 Customer St",
            city_name="Customer City",
            country_code="NG",
            postal_zone="67890",
            country_subdivision="Abuja"
        )
        
        customer_party = AccountingParty(
            party_name="Customer Company Ltd",
            postal_address=customer_address,
            party_tax_scheme={"company_id": "NG0987654321", "tax_scheme_id": "VAT"},
            party_legal_entity=PartyLegalEntity(
                registration_name="Customer Company Ltd",
                company_id="RC654321",
                company_id_scheme_id="NG-CAC"
            ),
            contact={"name": "Jane Customer", "telephone": "+2340987654321", "email": "jane@customer.com"}
        )
        
        # Create invoice lines
        line1 = InvoiceLine(
            id="1",
            invoiced_quantity=Decimal("10.0"),
            unit_code=UnitCode.PIECE,
            line_extension_amount=Decimal("1000.00"),
            item_description="Product A Description",
            item_name="Product A",
            price_amount=Decimal("100.00")
        )
        
        line2 = InvoiceLine(
            id="2",
            invoiced_quantity=Decimal("5.0"),
            unit_code=UnitCode.KILOGRAM,
            line_extension_amount=Decimal("500.00"),
            item_description="Product B Description",
            item_name="Product B",
            price_amount=Decimal("100.00")
        )
        
        # Create tax subtotal
        tax_subtotal = TaxSubtotal(
            taxable_amount=Decimal("1500.00"),
            tax_amount=Decimal("112.50"),
            tax_category=TaxCategory.STANDARD,
            tax_percent=Decimal("7.5")
        )
        
        # Create tax total
        tax_total = TaxTotal(
            tax_amount=Decimal("112.50"),
            tax_subtotals=[tax_subtotal]
        )
        
        # Create monetary total
        monetary_total = LegalMonetaryTotal(
            line_extension_amount=Decimal("1500.00"),
            tax_exclusive_amount=Decimal("1500.00"),
            tax_inclusive_amount=Decimal("1612.50"),
            payable_amount=Decimal("1612.50")
        )
        
        # Create payment terms
        payment_terms = PaymentTerms(
            note="Payment within 30 days",
            payment_due_date=date(2023, 6, 30)
        )
        
        # Create the invoice
        return InvoiceValidationRequest(
            invoice_number="INV-2023-001",
            invoice_type_code=InvoiceTypeCode.COMMERCIAL_INVOICE,
            invoice_date=date(2023, 5, 31),
            due_date=date(2023, 6, 30),
            currency_code=CurrencyCode.NGN,
            accounting_supplier_party=supplier_party,
            accounting_customer_party=customer_party,
            invoice_lines=[line1, line2],
            tax_total=tax_total,
            legal_monetary_total=monetary_total,
            payment_terms=payment_terms,
            note="Test Invoice"
        )
    
    def _create_invalid_invoice_missing_required(self) -> InvoiceValidationRequest:
        """Create an invalid invoice with missing required fields."""
        invoice = self._create_valid_invoice()
        
        # Create a customer with missing address fields
        customer_party = invoice.accounting_customer_party
        customer_party.postal_address.street_name = ""  # Empty required field
        customer_party.postal_address.city_name = None  # None required field
        
        # Create a line with missing required fields
        line = invoice.invoice_lines[0]
        line.item_name = ""  # Empty required field
        
        return invoice
    
    def _create_invoice_with_total_mismatch(self) -> InvoiceValidationRequest:
        """Create an invoice with mismatched totals."""
        invoice = self._create_valid_invoice()
        
        # Modify monetary totals to create a mismatch
        invoice.legal_monetary_total.line_extension_amount = Decimal("1600.00")  # Doesn't match sum of line amounts
        invoice.legal_monetary_total.tax_inclusive_amount = Decimal("1700.00")   # Doesn't match tax_exclusive + tax_amount
        
        return invoice
    
    def _create_invoice_with_invalid_dates(self) -> InvoiceValidationRequest:
        """Create an invoice with invalid dates."""
        invoice = self._create_valid_invoice()
        
        # Set due date earlier than invoice date
        invoice.due_date = date(2023, 5, 15)  # Earlier than invoice_date (May 31)
        
        return invoice
    
    def test_validate_valid_invoice(self):
        """Test validation of a valid invoice."""
        is_valid, errors = self.validator.validate_mapped_invoice(self.valid_invoice)
        
        self.assertTrue(is_valid, f"Valid invoice should pass validation, but got errors: {errors}")
        self.assertEqual(len(errors), 0, "There should be no validation errors")
    
    def test_validate_missing_required_fields(self):
        """Test validation of an invoice with missing required fields."""
        is_valid, errors = self.validator.validate_mapped_invoice(self.invoice_missing_required)
        
        self.assertFalse(is_valid, "Invalid invoice should fail validation")
        self.assertGreater(len(errors), 0, "There should be validation errors")
        
        # Check for specific error messages
        error_fields = [error.field for error in errors]
        self.assertIn("customer.postal_address.street_name", error_fields)
        self.assertIn("customer.postal_address.city_name", error_fields)
        self.assertIn("invoice_lines[0].item_name", error_fields)
    
    def test_validate_total_mismatch(self):
        """Test validation of an invoice with mismatched totals."""
        is_valid, errors = self.validator.validate_mapped_invoice(self.invoice_with_total_mismatch)
        
        self.assertFalse(is_valid, "Invoice with total mismatch should fail validation")
        self.assertGreater(len(errors), 0, "There should be validation errors")
        
        # Check for specific error messages
        error_codes = [error.error_code for error in errors]
        self.assertIn("TOTAL_MISMATCH", error_codes)
        self.assertIn("TAX_INCLUSIVE_MISMATCH", error_codes)
    
    def test_validate_invalid_dates(self):
        """Test validation of an invoice with invalid dates."""
        is_valid, errors = self.validator.validate_mapped_invoice(self.invoice_with_invalid_dates)
        
        self.assertFalse(is_valid, "Invoice with invalid dates should fail validation")
        self.assertGreater(len(errors), 0, "There should be validation errors")
        
        # Check for specific error messages
        error_codes = [error.error_code for error in errors]
        self.assertIn("INVALID_DUE_DATE", error_codes)
    
    def test_validator_singleton(self):
        """Test that the validator singleton instance works correctly."""
        self.assertIsInstance(odoo_ubl_validator, OdooUBLValidator)
        
        # Validate using the singleton
        is_valid, errors = odoo_ubl_validator.validate_mapped_invoice(self.valid_invoice)
        self.assertTrue(is_valid)


if __name__ == "__main__":
    unittest.main()
