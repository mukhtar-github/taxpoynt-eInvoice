# Invoice Schema
This API’s helps in validating the content of the invoice to ensure all content are properly inoder before sending for signing
All data points follow the Universal Business Language (UBL) standard.
**Endpoint**: POST base_url/api/v1/invoice/validate

## Request
Field | Required | Type | Description | Example
business_id | Mandatory | UUID | Unique identification for the business that would be available on the user dashboard | "bb99420d-d6bb-422c-b371-b9f6d6009aae"
irn | Mandatory | String | Invoice Reference Number | "ITW001-B4B37F28-20240623"
issue_date | Mandatory | Date | Issue date of the invoice | "2024-05-14"
due_date | Optional | Date | Payment due date of the invoice | "2024-06-14"
issue_time | Optional | Time | Issue time of the invoice | "17:59:04"
invoice_type_code | Mandatory | String | Code for invoice type (e.g., credit note, commercial note) | "396"
payment_status | Optional | String | Invoice payment status | "PENDING"
note | Optional | String | Free-text note on the invoice | "This is a purchase order"
tax_point_date | Optional | Date | Value-added tax point date | "2024-05-14"
document_currency_code | Mandatory | String | Invoice currency code | "NGN"
tax_currency_code | Optional | String | VAT accounting currency code | "NGN"
accounting_cost | Optional | String | Buyer accounting reference | "2000 NGN"
buyer_reference | Optional | String | Identifier assigned by the buyer for internal routing purposes | "12345678-0001"
invoice_delivery_period | Optional | Object | Delivery or invoice period | { "start_date": "2024-06-14", "end_date": "2024-06-16" }
order_reference | Optional | String | Order and sales-order reference | "abc123"
billing_reference | Optional | Array | Preceding invoice references | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" }, … ]
dispatch_document_reference | Optional | Array | References to despatch advice documents | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" } ]
receipt_document_reference | Optional | Array | References to receipt advice documents | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" } ]
originator_document_reference | Optional | Array | References to the original document that initiated the invoice | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" } ]
contract_document_reference | Optional | Array | References to the contract governing the transaction | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" } ]
additional_document_reference | Optional | Array | General references to any related documents | [ { "irn": "ITW001-E9E0C0D3-20240619", "issue_date": "2024-05-14" } ]
accounting_customer_party | Optional | Object | Buyer/recipient details | { "party_name": "XYZ Construction Ltd", "postal_address": { … } }
accounting_supplier_party | Optional | Object | Supplier/issuer details | { "party_name": "Dangote Group", "postal_address": { … } }
actual_delivery_date | Optional | Date | Actual delivery date | "2024-05-14"
payment_means | Optional | Array | How and when payment is due | [ { "payment_means_code": 10, "payment_due_date": "2024-05-14" }, … ]
payment_terms_note | Optional | String | Terms and conditions of payment | "Payment due within 30 days of invoice issue."
allowance_charge | Optional | Array | Discounts (allowances) or extra charges (charges) | [ { "charge_indicator": true,  "amount": 800.6 }, { "charge_indicator": false, "amount": 10 } ]
tax_total | Optional | Array | Total tax charged | [ { "tax_amount": 56.07, "tax_subtotal": [ { "taxable_amount": 800, "tax_amount": 8, "tax_category": { "id": "LOCAL_SALES_TAX", "percent": 2.3 } } ] } ]
legal_monetary_total | Mandatory | Object | Total amount the buyer has to pay, including/excluding taxes | { "line_extension_amount": 340.5, "tax_exclusive_amount": 400, "tax_inclusive_amount": 430, "payable_amount": 30 }
invoice_line | Mandatory | Array | Details about each item or service being invoiced | [ { "hsn_code": "CC-001", …, "price": { "price_amount": 10, "base_quantity": 3, "price_unit": "NGN per 1" } }, … ]

## Request Example
{
"business_id": "{{TEST_BUSINESS_ID}}",
"irn": "IRN",
"issue_date": "2024-05-14",
"due_date": "2024-06-14", //optional
"issue_time": "17:59:04", //optional
"invoice_type_code": "396",
"payment_status": "PENDING", //optional, defaults to pending
"note": "dummy_note (will be encryted in storage)", //optional
"tax_point_date": "2024-05-14", //optional
"document_currency_code": "NGN",
"tax_currency_code": "NGN", //optional
"accounting_cost": "2000 NGN", //optional
"buyer_reference": "buyer REF IRN?", //optional
"invoice_delivery_period": {
"start_date": "2024-06-14",
"end_date": "2024-06-16"
}, //optional

## Response Body Fields
Parameter | Type | Description | Example
status | Boolean | Indicates success/failure of the API | true
message | String | Response message from the API | "success"

## Response Example
{
    "code": 201,
    "data": {
        "ok": true
    }