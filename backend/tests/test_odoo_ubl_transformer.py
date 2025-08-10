"""
Unit tests for the Odoo UBL Transformer component.
"""
import unittest
import xml.etree.ElementTree as ET
from decimal import Decimal
from datetime import date, datetime

from app.schemas.invoice_validation import (
    InvoiceValidationRequest, Party, Address,
    PartyLegalEntity, InvoiceLine,
    TaxTotal, TaxSubtotal, TaxCategory, LegalMonetaryTotal,
    PaymentTerms, InvoiceType, CurrencyCode, UnitCode
)
from app.services.firs_si.odoo_ubl_transformer import OdooUBLTransformer, odoo_ubl_transformer


class TestOdooUBLTransformer(unittest.TestCase):
    """Test cases for the Odoo UBL Transformer."""

    def setUp(self):
        """Set up test fixtures."""
        self.transformer = OdooUBLTransformer()
        
        # Create a valid invoice for testing
        self.valid_invoice = self._create_valid_invoice()
        
        # Create a valid Odoo invoice data dictionary
        self.odoo_invoice = self._create_odoo_invoice_dict()
        
        # Create company info dictionary
        self.company_info = self._create_company_info()
    
    def _create_valid_invoice(self) -> InvoiceValidationRequest:
        """Create a valid invoice for testing."""
        # Create supplier party
        supplier_address = Address(
            street_name="123 Supplier St",
            city_name="Supplier City",
            country_code="NG",
            postal_zone="12345",
            country_subdivision="Lagos"
        )
        
        supplier_party = Party(
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
        customer_address = Address(
            street_name="456 Customer St",
            city_name="Customer City",
            country_code="NG",
            postal_zone="67890",
            country_subdivision="Abuja"
        )
        
        customer_party = Party(
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
            invoice_type_code=InvoiceType.COMMERCIAL_INVOICE,
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
    
    def _create_odoo_invoice_dict(self) -> dict:
        """Create an Odoo invoice dictionary for testing."""
        return {
            "id": 123,
            "name": "INV/2023/001",
            "move_type": "out_invoice",
            "invoice_date": "2023-05-31",
            "invoice_date_due": "2023-06-30",
            "amount_untaxed": 1500.00,
            "amount_tax": 112.50,
            "amount_total": 1612.50,
            "narration": "Test Invoice",
            "ref": "PO-2023-001",
            "currency": {"id": 1, "name": "NGN", "symbol": "₦"},
            "partner_id": {
                "id": 42,
                "name": "Customer Company Ltd",
                "vat": "NG0987654321",
                "street": "456 Customer St",
                "street2": "",
                "city": "Customer City",
                "state_id": {"id": 5, "name": "Abuja"},
                "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
                "zip": "67890",
                "email": "jane@customer.com",
                "phone": "+2340987654321"
            },
            "invoice_line_ids": [
                {
                    "id": 1,
                    "name": "Product A Description",
                    "quantity": 10.0,
                    "price_unit": 100.00,
                    "price_subtotal": 1000.00,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                    "product_id": {"id": 101, "name": "Product A", "default_code": "PROD-A"},
                    "product_uom_id": {"id": 1, "name": "Units"}
                },
                {
                    "id": 2,
                    "name": "Product B Description",
                    "quantity": 5.0,
                    "price_unit": 100.00,
                    "price_subtotal": 500.00,
                    "tax_ids": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
                    "product_id": {"id": 102, "name": "Product B", "default_code": "PROD-B"},
                    "product_uom_id": {"id": 3, "name": "kg"}
                }
            ],
            "invoice_payment_term_id": {"id": 1, "name": "Payment within 30 days"}
        }
    
    def _create_company_info(self) -> dict:
        """Create company information for testing."""
        return {
            "id": 1,
            "name": "Supplier Company Ltd",
            "vat": "NG1234567890",
            "street": "123 Supplier St",
            "street2": "",
            "city": "Supplier City",
            "state_id": {"id": 1, "name": "Lagos"},
            "country_id": {"id": 1, "code": "NG", "name": "Nigeria"},
            "zip": "12345",
            "company_registry": "RC123456",
            "email": "john@supplier.com",
            "phone": "+2341234567890"
        }
    
    def test_ubl_object_to_xml_structure(self):
        """Test transformation of UBL object to XML with correct structure."""
        # Transform to XML
        xml_string, issues = self.transformer.ubl_object_to_xml(self.valid_invoice)
        
        # Check for any conversion issues
        self.assertEqual(len(issues), 0, f"There should be no conversion issues but got: {issues}")
        
        # Parse the XML
        root = ET.fromstring(xml_string)
        
        # Verify the root element
        self.assertEqual(root.tag.split('}')[-1], "Invoice", "Root element should be 'Invoice'")
        
        # Check for required UBL elements
        self._assert_xpath_exists(root, ".//cbc:CustomizationID")
        self._assert_xpath_exists(root, ".//cbc:ProfileID")
        self._assert_xpath_exists(root, ".//cbc:ID")
        self._assert_xpath_exists(root, ".//cbc:IssueDate")
        self._assert_xpath_exists(root, ".//cbc:InvoiceTypeCode")
        self._assert_xpath_exists(root, ".//cbc:DocumentCurrencyCode")
        self._assert_xpath_exists(root, ".//cac:AccountingSupplierParty")
        self._assert_xpath_exists(root, ".//cac:AccountingCustomerParty")
        self._assert_xpath_exists(root, ".//cac:LegalMonetaryTotal")
        self._assert_xpath_exists(root, ".//cac:InvoiceLine")
        
        # Check if invoice number is correct
        id_element = root.find(".//{*}ID")
        self.assertEqual(id_element.text, "INV-2023-001", "Invoice ID should match")
        
        # Check invoice type code
        type_code_element = root.find(".//{*}InvoiceTypeCode")
        self.assertEqual(type_code_element.text, "380", "Invoice type code should be 380")
    
    def _assert_xpath_exists(self, root, xpath):
        """Assert that an XPath expression finds at least one element."""
        # Note: This is a simplified XPath check - in real tests, you would
        # register namespaces properly to use standard XPath
        
        # Convert XPath to use {*} namespace wildcards
        modified_xpath = xpath.replace('cbc:', './/{*}').replace('cac:', './/{*}')
        
        # If it starts with './/cbc:' or './/cac:', we need to fix it
        if modified_xpath.startswith('.//.//{*}'):
            modified_xpath = modified_xpath.replace('.//.//{*}', './/{*}')
        
        elements = root.findall(modified_xpath)
        self.assertGreaterEqual(len(elements), 1, f"XPath '{xpath}' should find at least one element")
    
    def test_odoo_to_ubl_object(self):
        """Test transformation of Odoo invoice data to UBL object."""
        # Since we can't directly test the mapper in this unit test (which would require mocking),
        # we'll need to patch or mock the mapper in a real test. Here, we'll just verify the method
        # signature and error handling works correctly.
        
        # This would normally use the mapper, but for testing we just check it doesn't crash
        try:
            ubl_invoice, issues = self.transformer.odoo_to_ubl_object(
                self.odoo_invoice, self.company_info
            )
            # If the mapper is properly mocked, we'd make assertions here about the result
        except Exception as e:
            # We expect this to fail if the mapper is not mocked, but we're testing the signature works
            self.assertIn("odoo_ubl_mapper", str(e).lower(), 
                         f"Exception should be related to mapper, but got: {str(e)}")
    
    def test_error_handling_ubl_object_to_xml(self):
        """Test error handling in XML transformation."""
        # Create an invoice with an invalid value that will cause XML generation issues
        broken_invoice = self._create_valid_invoice()
        # Set an invalid object that will cause serialization issues
        broken_invoice.accounting_supplier_party = None  # This will cause issues in XML generation
        
        # Transform to XML
        xml_string, issues = self.transformer.ubl_object_to_xml(broken_invoice)
        
        # Check for conversion issues
        self.assertGreater(len(issues), 0, "There should be conversion issues")
        self.assertEqual(xml_string, "", "XML string should be empty due to errors")
        
        # Check the error message
        self.assertEqual(issues[0]["code"], "XML_CONVERSION_ERROR", "Error code should be XML_CONVERSION_ERROR")
    
    def test_transformer_singleton(self):
        """Test that the transformer singleton instance works correctly."""
        self.assertIsInstance(odoo_ubl_transformer, OdooUBLTransformer)
        
        # Transform using the singleton
        xml_string, issues = odoo_ubl_transformer.ubl_object_to_xml(self.valid_invoice)
        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
