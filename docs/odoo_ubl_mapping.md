# Odoo to BIS Billing 3.0 UBL Field Mapping Documentation

## Overview

This document outlines the field mapping schema between Odoo invoice data and the BIS Billing 3.0 UBL (Universal Business Language) format required by the Federal Inland Revenue Service (FIRS) of Nigeria for electronic invoicing.

## Core Components

The mapping system consists of three main components:

1. **OdooUBLMapper** - Maps Odoo invoice fields to BIS Billing 3.0 UBL format
2. **OdooUBLValidator** - Validates the mapped fields against BIS Billing 3.0 requirements
3. **OdooUBLTransformer** - Transforms between Odoo data and UBL XML format

## Field Mapping Schema

### Invoice Header Fields

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| name | cbc:ID | Invoice number/identifier | Direct mapping |
| move_type | cbc:InvoiceTypeCode | Invoice type code | Mapped to UBL codes (380=invoice, 381=credit note) |
| invoice_date | cbc:IssueDate | Invoice issue date | Formatted as ISO date (YYYY-MM-DD) |
| invoice_date_due | cbc:DueDate | Payment due date | Formatted as ISO date (YYYY-MM-DD) |
| currency_id.name | cbc:DocumentCurrencyCode | Invoice currency code | Mapped to ISO 4217 code |
| ref | cbc:OrderReference/cbc:ID | Purchase order reference | Direct mapping |
| narration | cbc:Note | Invoice note/comments | Direct mapping |

### Supplier Party Fields (Company)

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| company.name | cac:AccountingSupplierParty/cac:Party/cac:PartyName/cbc:Name | Supplier name | Direct mapping |
| company.vat | cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID | Supplier VAT number | Direct mapping |
| company.street | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:StreetName | Supplier street address | Direct mapping |
| company.street2 | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:AdditionalStreetName | Supplier additional street | Direct mapping |
| company.city | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:CityName | Supplier city | Direct mapping |
| company.zip | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:PostalZone | Supplier postal code | Direct mapping |
| company.state_id.name | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:CountrySubentity | Supplier state/region | Direct mapping |
| company.country_id.code | cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode | Supplier country code | Mapped to ISO 3166-1 alpha-2 |
| company.name | cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName | Supplier legal name | Direct mapping |
| company.company_registry | cac:AccountingSupplierParty/cac:Party/cac:PartyLegalEntity/cbc:CompanyID | Supplier company ID | Direct mapping |
| company.phone | cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:Telephone | Supplier phone | Direct mapping |
| company.email | cac:AccountingSupplierParty/cac:Party/cac:Contact/cbc:ElectronicMail | Supplier email | Direct mapping |

### Customer Party Fields (Partner)

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| partner_id.name | cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name | Customer name | Direct mapping |
| partner_id.vat | cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID | Customer VAT number | Direct mapping |
| partner_id.street | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName | Customer street address | Direct mapping |
| partner_id.street2 | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:AdditionalStreetName | Customer additional street | Direct mapping |
| partner_id.city | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:CityName | Customer city | Direct mapping |
| partner_id.zip | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:PostalZone | Customer postal code | Direct mapping |
| partner_id.state_id.name | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:CountrySubentity | Customer state/region | Direct mapping |
| partner_id.country_id.code | cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode | Customer country code | Mapped to ISO 3166-1 alpha-2 |
| partner_id.name | cac:AccountingCustomerParty/cac:Party/cac:PartyLegalEntity/cbc:RegistrationName | Customer legal name | Direct mapping |
| partner_id.phone | cac:AccountingCustomerParty/cac:Party/cac:Contact/cbc:Telephone | Customer phone | Direct mapping |
| partner_id.email | cac:AccountingCustomerParty/cac:Party/cac:Contact/cbc:ElectronicMail | Customer email | Direct mapping |

### Invoice Line Fields

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| id | cac:InvoiceLine/cbc:ID | Line identifier | Cast to string |
| quantity | cac:InvoiceLine/cbc:InvoicedQuantity | Quantity | Cast to decimal |
| product_uom_id.name | cac:InvoiceLine/cbc:InvoicedQuantity/@unitCode | Unit of measure | Mapped to UBL codes |
| price_subtotal | cac:InvoiceLine/cbc:LineExtensionAmount | Net line amount | Cast to decimal |
| name | cac:InvoiceLine/cac:Item/cbc:Description | Line description | Direct mapping |
| product_id.name | cac:InvoiceLine/cac:Item/cbc:Name | Product name | Direct mapping, truncated to 100 chars |
| price_unit | cac:InvoiceLine/cac:Price/cbc:PriceAmount | Unit price | Cast to decimal |
| product_id.default_code | cac:InvoiceLine/cac:Item/cac:BuyersItemIdentification/cbc:ID | Buyer's item code | Direct mapping |
| product_id.id | cac:InvoiceLine/cac:Item/cac:SellersItemIdentification/cbc:ID | Seller's item code | Cast to string |

### Tax Information Fields

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| amount_tax | cac:TaxTotal/cbc:TaxAmount | Total tax amount | Cast to decimal |
| tax_ids.amount | cac:TaxTotal/cac:TaxSubtotal/cbc:Percent | Tax rate percentage | Cast to decimal |
| price_subtotal | cac:TaxTotal/cac:TaxSubtotal/cbc:TaxableAmount | Base amount for tax | Cast to decimal |
| tax_ids.amount * price_subtotal / 100 | cac:TaxTotal/cac:TaxSubtotal/cbc:TaxAmount | Tax amount | Calculated |
| tax_ids.name | cac:TaxTotal/cac:TaxSubtotal/cac:TaxCategory/cbc:ID | Tax category | Mapped to UBL tax categories |

### Document Totals Fields

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| amount_untaxed | cac:LegalMonetaryTotal/cbc:LineExtensionAmount | Sum of invoice line amounts | Cast to decimal |
| amount_untaxed | cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount | Total excluding tax | Cast to decimal |
| amount_total | cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount | Total including tax | Cast to decimal |
| amount_total | cac:LegalMonetaryTotal/cbc:PayableAmount | Amount due for payment | Cast to decimal |

### Payment Information Fields

| Odoo Field | UBL Field | Description | Transformation |
|------------|-----------|-------------|----------------|
| invoice_payment_term_id.name | cac:PaymentTerms/cbc:Note | Payment terms description | Direct mapping |
| invoice_date_due | cac:PaymentTerms/cbc:PaymentDueDate | Due date for payment | Formatted as ISO date |
| payment_method_id.name | cac:PaymentMeans/cbc:PaymentMeansCode | Payment method code | Mapped to UBL payment means codes |

## Code Mappings

### Invoice Type Codes

| Odoo Value | UBL Value | Description |
|------------|-----------|-------------|
| out_invoice | 380 | Commercial invoice |
| out_refund | 381 | Credit note |
| in_invoice | 380 | Commercial invoice |
| in_refund | 381 | Credit note |

### Tax Categories

| Odoo Tax Pattern | UBL Value | Description |
|------------------|-----------|-------------|
| vat | S | Standard rate |
| vat_0 | Z | Zero rated goods |
| exempt | E | Exempt from tax |
| export | G | Free export item, tax not charged |
| reverse | AE | VAT Reverse Charge |
| not_applicable | O | Services outside scope of tax |

### Unit Codes

| Odoo UoM | UBL Value | Description |
|----------|-----------|-------------|
| unit(s), units, ea, each | EA | Each (piece) |
| kg, kgs | KGM | Kilogram |
| l, ltr, litre | LTR | Litre |
| m, meter | MTR | Meter |
| hr, hour | HUR | Hour |
| day, days | DAY | Day |
| week, weeks | WEE | Week |
| month, months | MON | Month |

### Payment Means

| Odoo Payment Method | UBL Value | Description |
|---------------------|-----------|-------------|
| bank_transfer | 30 | Credit transfer |
| direct_debit | 49 | Direct debit |
| cash | 10 | Cash |
| check, cheque | 20 | Cheque |
| card, bank_card | 48 | Bank card |
| bank_giro | 50 | Bank giro |
| standing_order | 56 | Standing order |

## Data Type Transformations

| Odoo Type | UBL Type | Transformation |
|-----------|----------|----------------|
| date | xs:date | ISO format (YYYY-MM-DD) |
| datetime | xs:dateTime | ISO format (YYYY-MM-DDThh:mm:ss) |
| float | xs:decimal | Rounded to 2 decimal places |
| int | xs:integer | Direct conversion |
| str | xs:string | Direct conversion |
| bool | xs:boolean | "true"/"false" |

## Validation Rules

The validation system ensures that:

1. All required fields are present and non-empty
2. Mapped fields conform to BIS Billing 3.0 UBL format requirements
3. Tax totals and invoice totals are correctly calculated
4. Due dates are not earlier than invoice dates
5. Line amounts are consistent with quantities and prices

## Usage Example

```python
from app.services.odoo_ubl_mapper import odoo_ubl_mapper
from app.services.odoo_ubl_validator import odoo_ubl_validator
from app.services.odoo_ubl_transformer import odoo_ubl_transformer

# Odoo invoice data from the API
odoo_invoice = {
    "invoice_number": "INV/2023/00123",
    "name": "INV/2023/00123",
    "move_type": "out_invoice",
    "invoice_date": "2023-05-15",
    "invoice_date_due": "2023-06-15",
    "amount_untaxed": 1000.00,
    "amount_tax": 75.00,
    "amount_total": 1075.00,
    "currency": {"id": 1, "name": "NGN", "symbol": "₦"},
    "partner": {
        "id": 42,
        "name": "ACME Corporation",
        "vat": "NG1234567890",
        "email": "billing@acme.com",
        "phone": "+234123456789"
    },
    "lines": [
        {
            "id": 1,
            "name": "Product A",
            "quantity": 5,
            "price_unit": 100.00,
            "price_subtotal": 500.00,
            "taxes": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
            "product": {"id": 101, "name": "Product A", "default_code": "PROD-A"}
        },
        {
            "id": 2,
            "name": "Service B",
            "quantity": 2,
            "price_unit": 250.00,
            "price_subtotal": 500.00,
            "taxes": [{"id": 1, "name": "VAT 7.5%", "amount": 7.5}],
            "product": {"id": 202, "name": "Service B", "default_code": "SERV-B"}
        }
    ]
}

# Company information
company_info = {
    "id": 1,
    "name": "TaxPoynt Nigeria Ltd",
    "vat": "NG9876543210",
    "street": "123 Lagos Street",
    "city": "Lagos",
    "country": {"code": "NG", "name": "Nigeria"},
    "phone": "+234987654321",
    "email": "info@taxpoynt.ng"
}

# Map Odoo invoice to UBL object
ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
    odoo_invoice, company_info
)

# If valid, transform to UBL XML
if not validation_issues:
    ubl_xml, conversion_issues = odoo_ubl_transformer.ubl_object_to_xml(ubl_invoice)
    
    if not conversion_issues:
        # Use the UBL XML for FIRS submission
        print(ubl_xml)
    else:
        print(f"XML conversion issues: {conversion_issues}")
else:
    print(f"Validation issues: {validation_issues}")
```

## BIS Billing 3.0 References

The field mapping implementation follows the BIS Billing 3.0 standard as referenced in:

- [Peppol BIS Billing 3.0 Documentation](https://docs.peppol.eu/poacc/billing/3.0/)
- FIRS e-Invoicing Guidelines

For more details on specific field requirements, refer to the FIRS e-Invoicing technical documentation.
