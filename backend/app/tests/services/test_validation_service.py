import pytest # type: ignore
from datetime import datetime

from app.schemas.validation import (
    Invoice,
    Party,
    PartyAddress,
    MonetaryTotal,
    InvoiceLine,
    ItemIdentification,
    Price,
    ValidationSeverity,
)
from app.services.validation_service import ValidationService


@pytest.fixture
def validation_service():
    return ValidationService()


@pytest.fixture
def valid_invoice():
    return Invoice(
        business_id="bb99420d-d6bb-422c-b371-b9f6d6009aae",
        irn="INV001-94ND90NR-20240611",
        issue_date="2024-06-11",
        due_date="2024-07-11",
        issue_time="17:59:04",
        invoice_type_code="381",
        payment_status="PENDING",
        document_currency_code="NGN",
        accounting_supplier_party=Party(
            party_name="ABC Company Ltd",
            postal_address=PartyAddress(
                tin="12345678-0001",
                email="business@email.com",
                telephone="+23480254099000",
                business_description="Sales of IT equipment",
                street_name="123 Lagos Street, Abuja",
                city_name="Abuja",
                postal_zone="900001",
                country="NG"
            )
        ),
        accounting_customer_party=Party(
            party_name="XYZ Corporation",
            postal_address=PartyAddress(
                tin="87654321-0001",
                email="buyer@email.com",
                telephone="+23480254099001",
                business_description="IT Consulting",
                street_name="456 Abuja Road, Lagos",
                city_name="Lagos",
                postal_zone="100001",
                country="NG"
            )
        ),
        legal_monetary_total=MonetaryTotal(
            line_extension_amount=40000.00,
            tax_exclusive_amount=40000.00,
            tax_inclusive_amount=43000.00,
            payable_amount=43000.00
        ),
        invoice_line=[
            InvoiceLine(
                hsn_code="8471.30",
                product_category="Electronics",
                invoiced_quantity=10,
                line_extension_amount=40000.00,
                item=ItemIdentification(
                    name="Laptop Computers",
                    description="15-inch Business Laptops",
                    sellers_item_identification="LP-2024-001"
                ),
                price=Price(
                    price_amount=4000.00,
                    base_quantity=1,
                    price_unit="NGN per 1"
                )
            )
        ],
        note="This is a commercial invoice"
    )


@pytest.fixture
def invalid_invoice(valid_invoice):
    # Make a copy with invalid fields
    invoice_dict = valid_invoice.dict()
    
    # Invalid IRN format
    invoice_dict["irn"] = "INVALID-IRN"
    
    # Invalid TIN format for supplier
    invoice_dict["accounting_supplier_party"]["postal_address"]["tin"] = "123456"
    
    # Invalid monetary totals (tax_inclusive < tax_exclusive)
    invoice_dict["legal_monetary_total"]["tax_inclusive_amount"] = 39000.00
    
    # Incorrect line extension amount (doesn't match sum of lines)
    invoice_dict["legal_monetary_total"]["line_extension_amount"] = 30000.00
    
    # Invalid date format
    invoice_dict["issue_date"] = "06/11/2024"
    
    return Invoice(**invoice_dict)


def test_validate_valid_invoice(validation_service, valid_invoice):
    result = validation_service.validate_invoice(valid_invoice)
    assert result.is_valid is True
    assert len(result.issues) == 0


def test_validate_invalid_invoice(validation_service, invalid_invoice):
    result = validation_service.validate_invoice(invalid_invoice)
    assert result.is_valid is False
    assert len(result.issues) > 0
    
    # Check that specific validation issues are present
    field_errors = {issue.field: issue for issue in result.issues}
    
    assert "irn" in field_errors
    assert "issue_date" in field_errors
    assert "accounting_supplier_party.postal_address.tin" in field_errors
    assert "legal_monetary_total.tax_inclusive_amount" in field_errors
    assert "legal_monetary_total.line_extension_amount" in field_errors
    
    # Check error severities
    for issue in result.issues:
        assert issue.severity == ValidationSeverity.ERROR


def test_validate_required_fields(validation_service):
    # Create invoice missing required fields
    missing_fields_invoice = Invoice(
        business_id="",  # Empty business_id
        irn="INV001-94ND90NR-20240611",
        issue_date="2024-06-11",
        invoice_type_code="381",
        document_currency_code="NGN",
        accounting_supplier_party=Party(
            party_name="ABC Company Ltd",
            postal_address=PartyAddress(
                tin="12345678-0001",
                email="business@email.com",
                telephone="+23480254099000",
                business_description="Sales of IT equipment",
                street_name="123 Lagos Street, Abuja",
                city_name="Abuja",
                postal_zone="900001",
                country="NG"
            )
        ),
        accounting_customer_party=Party(
            party_name="XYZ Corporation",
            postal_address=PartyAddress(
                tin="87654321-0001",
                email="buyer@email.com",
                telephone="+23480254099001",
                business_description="IT Consulting",
                street_name="456 Abuja Road, Lagos",
                city_name="Lagos",
                postal_zone="100001",
                country="NG"
            )
        ),
        legal_monetary_total=MonetaryTotal(
            line_extension_amount=40000.00,
            tax_exclusive_amount=40000.00,
            tax_inclusive_amount=43000.00,
            payable_amount=43000.00
        ),
        invoice_line=[]  # Empty invoice_line
    )
    
    result = validation_service.validate_invoice(missing_fields_invoice)
    assert result.is_valid is False
    
    # Should have validation issues for business_id and invoice_line
    field_errors = {issue.field: issue for issue in result.issues}
    assert "business_id" in field_errors
    assert "invoice_line" in field_errors


def test_validate_irn_format(validation_service, valid_invoice):
    # Test various invalid IRN formats
    invalid_irn_formats = [
        "INV-001",  # Missing parts
        "INV001-94ND90NR-202406",  # Incomplete date
        "INV001-94ND90NR-20240632",  # Invalid date
        "INV001-94N-20240611",  # Invalid service ID
        "INV-001-94ND90NR-20240611"  # Special character in invoice number
    ]
    
    for invalid_irn in invalid_irn_formats:
        invoice_copy = valid_invoice.copy(deep=True)
        invoice_copy.irn = invalid_irn
        
        result = validation_service.validate_invoice(invoice_copy)
        assert result.is_valid is False
        
        # Should have validation issue for IRN
        field_errors = {issue.field: issue for issue in result.issues}
        assert "irn" in field_errors


def test_validate_monetary_totals(validation_service, valid_invoice):
    # Test various invalid monetary total scenarios
    
    # 1. Tax inclusive < tax exclusive
    invoice_copy = valid_invoice.copy(deep=True)
    invoice_copy.legal_monetary_total.tax_inclusive_amount = 39000.00
    
    result = validation_service.validate_invoice(invoice_copy)
    assert result.is_valid is False
    field_errors = {issue.field: issue for issue in result.issues}
    assert "legal_monetary_total.tax_inclusive_amount" in field_errors
    
    # 2. Payable amount != tax inclusive amount
    invoice_copy = valid_invoice.copy(deep=True)
    invoice_copy.legal_monetary_total.payable_amount = 45000.00
    
    result = validation_service.validate_invoice(invoice_copy)
    assert result.is_valid is False
    field_errors = {issue.field: issue for issue in result.issues}
    assert "legal_monetary_total.payable_amount" in field_errors
    
    # 3. Line extension amount doesn't match sum of line items
    invoice_copy = valid_invoice.copy(deep=True)
    invoice_copy.legal_monetary_total.line_extension_amount = 30000.00
    
    result = validation_service.validate_invoice(invoice_copy)
    assert result.is_valid is False
    field_errors = {issue.field: issue for issue in result.issues}
    assert "legal_monetary_total.line_extension_amount" in field_errors 