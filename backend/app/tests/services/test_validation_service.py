import pytest # type: ignore
from datetime import datetime

from app.schemas.invoice_validation import (
    InvoiceValidationRequest as Invoice,
    Party,
    Address as PartyAddress,
    LegalMonetaryTotal as MonetaryTotal,
    InvoiceLine,
    ItemIdentification,
    Price,
    ValidationRule,
    ValidationSeverity
)
from app.services.invoice_validation_service import validate_invoice


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


def test_validate_valid_invoice(valid_invoice):
    result = validate_invoice(valid_invoice)
    assert result.is_valid is True
    assert len(result.issues) == 0


def test_validate_invalid_invoice(invalid_invoice):
    result = validate_invoice(invalid_invoice)
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


def test_validate_required_fields():
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
    
    result = validate_invoice(missing_fields_invoice)
    assert result.is_valid is False
    
    # Get fields with errors
    error_fields = [issue.field for issue in result.issues]
    
    # Check that specific required fields are in errors
    assert "business_id" in error_fields
    assert "due_date" in error_fields
    assert "issue_time" in error_fields


def test_validate_irn_format(valid_invoice):
    # Test invalid IRN format
    invalid_irn_invoice = valid_invoice.copy(update={"irn": "INVALID-FORMAT"})
    result = validate_invoice(invalid_irn_invoice)
    
    # Check that IRN validation fails
    assert result.is_valid is False
    assert any(issue.field == "irn" for issue in result.issues)
    
    # Test valid IRN format
    valid_irn_invoice = valid_invoice.copy(update={"irn": "INV001-94ND90NR-20240611"})
    result = validate_invoice(valid_irn_invoice)
    
    # No IRN errors should be present
    assert not any(issue.field == "irn" for issue in result.issues)


def test_validate_monetary_totals(valid_invoice):
    # Create invoice with inconsistent monetary totals
    inconsistent_totals_invoice = valid_invoice.copy(
        update={
            "legal_monetary_total": {
                "line_extension_amount": 1000.00,  # Different from sum of line amounts
                "tax_exclusive_amount": 1000.00,
                "tax_inclusive_amount": 1150.00,
                "allowance_total_amount": 0.00,
                "charge_total_amount": 0.00,
                "prepaid_amount": 0.00,
                "payable_amount": 1150.00
            }
        }
    )
    
    result = validate_invoice(inconsistent_totals_invoice)
    assert result.is_valid is False
    
    # Check that monetary total validation issues are present
    total_errors = [issue for issue in result.issues if issue.field.startswith("legal_monetary_total")]
    assert len(total_errors) > 0