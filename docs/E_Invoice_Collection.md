# E-Invoice Collection

NB: Postman / Curl
You can use Postman/Curl to test your integration and the data sets that the FIRS MBS API offers.
Use environment variables to customize the requests that you send. This step is optional but can help you avoid mixing up environments and credentials. Read more in Postman's docs on managing environments.

Visit the FIRSMBS Dashboard to retrieve your API keys and add them as values for each environment's bearerToken.

Make sure that you store your base_url and bearerToken as initial values and current values.

## TaxPayer Authentication

1. POST TaxpayerLogin:
- {{HOST}}/api/v1/utilities/authenticate

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/utilities/authenticate' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data '{
    "email": "{{TAXPAYER_EMAIL}}",
    "password": "{{TAXPAYER_PASSWORD}}"
}'
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

c. PARAMS

d. Body raw (json)
```json
{
    "email": "{{TAXPAYER_EMAIL}}",
    "password": "{{TAXPAYER_PASSWORD}}"
}
```

## Entity
The API suite includes endpoints designed for managing entities within the E-invoice system.
1. GET GetEntity
- {{HOST}}/api/v1/entity/{{TEST_ENTITY_ID}}

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/entity/{{TEST_ENTITY_ID}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}


2. GET SearchEntity
- {{HOST}}/api/v1/entity?size=20&page=1&sort_by=created_at&sort_direction_desc=true&reference=

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/entity?size=20&page=1&sort_by=created_at&sort_direction_desc=true&reference=' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

c. PARAMS
    - size                      20
                                how many data per page
    - page                      1
                                what page in the pagination? page 1, 2, 3 or X depending on the totalPages
    - sort_by                   created_at
                                sort by the query param. i.e sort by 'created_at'
    - sort_direction_desc       true
                                sort the 'sort_by'
    - reference                 searching by a reference

## Resources
1. GET GetCountries
- {{HOST}}/api/v1/invoice/resources/countries

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/countries' \
--data ''
```

2. GET GetCurrencies
- {{HOST}}/api/v1/invoice/resources/currencies

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/currencies' \
--data ''
```

3. GET GetTaxCategories
- {{HOST}}/api/v1/invoice/resources/tax-categories

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/tax-categories'
```

4. GET GetPaymentmeans
- {{HOST}}/api/v1/invoice/resources/payment-means

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/payment-means'
```
5. GET GetInvoiceTypes
- {{HOST}}/api/v1/invoice/resources/invoice-types

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/invoice-types'
```

6. GET GetService Codes
- {{HOST}}/api/v1/invoice/resources/services-codes

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/services-codes'
```

7. GET GetVatExemptions
- {{HOST}}/api/v1/invoice/resources/vat-exemptions

### Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/resources/vat-exemptions' \
--data ''
```

## Invoice
This API suite is designed to perform a full range of invoice-related actions, offering endpoints that support the
validation, management, and processing of invoices within the E-invoice system. Each endpoint in this suite is
purpose-built to facilitate specific invoice workflows, ensuring seamless, secure, and efficient handling of all invoicing
tasks.
1. POST ValidateIRN
- {{HOST}}/api/v1/invoice/irn/validate
This API enables users validate IRN by just sending the invoice reference, business id and irn

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/irn/validate' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{IAPI_SECRET}}' \
--data '{
    "invoice_reference": "ITW001",
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "{{TEST_IRN}}"
}'
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{IAPI_SECRET}}

c. Body raw (json)
```json
{
    "invoice_reference": "ITW001",
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "{{TEST_IRN}}"
}
```

2. POST ValidateInvoice
- {{HOST}}/api/v1/invoice/validate
This API’s helps in validating the content of the invoice to ensure all content are properly in oder before sending for
signing.
All data points follow the Universal Business Language (UBL) standard.

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/validate' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{IAPI_SECRET}}' \
--data-raw '{
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "ITW20853450-6997D6BB-20240703",
    "issue_date": "2024-05-14",
    "due_date": "2024-06-14", //optional
    "issue_time": "17:59:04", //optional   
    "invoice_type_code": "396",
    "payment_status": "PENDING", //optional, defaults to pending  
    "note": "dummy_note (will be encryted in storage)", //optional
    "tax_point_date": "2024-05-14", //optional
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN", //optional
    "accounting_cost": "2000", //optional
    "buyer_reference": "buyer REF IRN?", //optional
    "invoice_delivery_period": {
        "start_date": "2024-06-14",
        "end_date": "2024-06-16"
    }, //optional
    "order_reference": "order REF IRN?", //optional
    "billing_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        },
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        } //optional - second value to ...x in array is always optional
    ], //optional
    "dispatch_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "receipt_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "originator_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, // optional
    "contract_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "_document_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        }
    ], //optional
    "accounting_supplier_party": {
        "party_name": "Test Pls", //optional if id is set    
        "tin": "TIN-0099990001",
        "email": "supplier_business@email.com",
        "telephone": "+23480254099000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", //optional if id is set
            "city_name": "Gwarikpa", //optional if id is set
            "postal_zone": "023401", //optional if id is set
            "country": "NG" //optional if id is set
        } //optional if id is set
    },
    "accounting_customer_party": {
        "party_name": "Test Pls", //optional if id is set
        "tin": "TIN-000001",
        "email": "business@email.com",
        "telephone": "+23480254000000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", //optional if id is set
            "city_name": "Gwarikpa", //optional if id is set
            "postal_zone": "023401", //optional if id is set
            "country": "NG" //optional if id is set
        } //optional if id is set
    },
    // "payee_party": {}, //optional (party object, just like accounting_customer_party)
    // "tax_representative_party": {}, //optional (party object, just like accounting_customer_party)
    "actual_delivery_date": "2024-05-14", //optional
    "payment_means": [
        {
            "payment_means_code": "10",
            "payment_due_date": "2024-05-14"
        },
        {
            "payment_means_code": "43",
            "payment_due_date": "2024-05-14"
        }//optional - second value to ...x in array is always optional
    ],//optional
    "payment_terms_note": "dummy payment terms note (will be encryted in storage)",//optional
    "allowance_charge": [
        {
            "charge_indicator": true, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 800.60
        },
        {
            "charge_indicator": false, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 10
        }//optional - second value to ...x in array is always optional
    ],//optional
    "tax_total": [
        {
            "tax_amount": 56.07,
            "tax_subtotal": [
                {
                    "taxable_amount": 800,
                    "tax_amount": 8,
                    "tax_category": {
                        "id": "LOCAL_SALES_TAX",
                        "percent": 2.3
                    }
                }
            ]
        }//second value to ...x in array is always optional if you want to add it
    ],//optional
    "legal_monetary_total": {
        "line_extension_amount": 340.50,
        "tax_exclusive_amount": 400,
        "tax_inclusive_amount": 430,
        "payable_amount": 30
    },
    "invoice_line": [
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item name",
                "description": "item description",
                "sellers_item_identification": "identified as spoon by the seller" //optional
            },
            "price": {
                "price_amount": 10,
                "base_quantity": 3,
                "price_unit": "NGN per 1"
            }
        },
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item nam 2",
                "description": "item description 2",
                "sellers_item_identification": "identified as shovel by the seller"
            },
            "price": {
                "price_amount": 20,
                "base_quantity": 5,
                "price_unit": "NGN per 1"
            }
        }//optional - second value to ...x in array is always optional
    ]
}
'
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{IAPI_SECRET}}

c. Body raw (json)
```json
{
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "ITW20853450-6997D6BB-20240703",
    "issue_date": "2024-05-14",
    "due_date": "2024-06-14", //optional
    "issue_time": "17:59:04", //optional   
    "invoice_type_code": "396",
    "payment_status": "PENDING", //optional, defaults to pending  
    "note": "dummy_note (will be encryted in storage)", //optional
    "tax_point_date": "2024-05-14", //optional
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN", //optional
    "accounting_cost": "2000", //optional
    "buyer_reference": "buyer REF IRN?", //optional
    "invoice_delivery_period": {
        "start_date": "2024-06-14",
        "end_date": "2024-06-16"
    }, //optional
    "order_reference": "order REF IRN?", //optional
    "billing_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        },
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        } //optional - second value to ...x in array is always optional
    ], //optional
    "dispatch_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "receipt_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "originator_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, // optional
    "contract_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "_document_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        }
    ], //optional
    "accounting_supplier_party": {
        "party_name": "Test Pls", //optional if id is set    
        "tin": "TIN-0099990001",
        "email": "supplier_business@email.com",
        "telephone": "+23480254099000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", //optional if id is set
            "city_name": "Gwarikpa", //optional if id is set
            "postal_zone": "023401", //optional if id is set
            "country": "NG" //optional if id is set
        } //optional if id is set
    },
    "accounting_customer_party": {
        "party_name": "Test Pls", //optional if id is set
        "tin": "TIN-000001",
        "email": "business@email.com",
        "telephone": "+23480254000000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", //optional if id is set
            "city_name": "Gwarikpa", //optional if id is set
            "postal_zone": "023401", //optional if id is set
            "country": "NG" //optional if id is set
        } //optional if id is set
    },
    // "payee_party": {}, //optional (party object, just like accounting_customer_party)
    // "tax_representative_party": {}, //optional (party object, just like accounting_customer_party)
    "actual_delivery_date": "2024-05-14", //optional
    "payment_means": [
        {
            "payment_means_code": "10",
            "payment_due_date": "2024-05-14"
        },
        {
            "payment_means_code": "43",
            "payment_due_date": "2024-05-14"
        }//optional - second value to ...x in array is always optional
    ],//optional
    "payment_terms_note": "dummy payment terms note (will be encryted in storage)",//optional
    "allowance_charge": [
        {
            "charge_indicator": true, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 800.60
        },
        {
            "charge_indicator": false, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 10
        }//optional - second value to ...x in array is always optional
    ],//optional
    "tax_total": [
        {
            "tax_amount": 56.07,
            "tax_subtotal": [
                {
                    "taxable_amount": 800,
                    "tax_amount": 8,
                    "tax_category": {
                        "id": "LOCAL_SALES_TAX",
                        "percent": 2.3
                    }
                }
            ]
        }//second value to ...x in array is always optional if you want to add it
    ],//optional
    "legal_monetary_total": {
        "line_extension_amount": 340.50,
        "tax_exclusive_amount": 400,
        "tax_inclusive_amount": 430,
        "payable_amount": 30
    },
    "invoice_line": [
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item name",
                "description": "item description",
                "sellers_item_identification": "identified as spoon by the seller" //optional
            },
            "price": {
                "price_amount": 10,
                "base_quantity": 3,
                "price_unit": "NGN per 1"
            }
        },
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item nam 2",
                "description": "item description 2",
                "sellers_item_identification": "identified as shovel by the seller"
            },
            "price": {
                "price_amount": 20,
                "base_quantity": 5,
                "price_unit": "NGN per 1"
            }
        }//optional - second value to ...x in array is always optional
    ]
}
```

3. POST SignInvoice
- {{HOST}}/api/v1/invoice/sign
    - This API enables users submit and sign an invoice
    - All datapoint should have been validated for errors
    - All datapoints follow the Universal Business Language (UBL) standard.

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/sign' \
--header 'x-api-key: {{IAPI_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data-raw '{
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "ITW20853450-6997D6BB-20240703",
    "issue_date": "2024-05-14",
    "due_date": "2024-06-14", //optional
    "issue_time": "17:59:04", //optional   
    "invoice_type_code": "396",
    "payment_status": "PENDING", //optional, defaults to pending  
    "note": "dummy_note (will be encryted in storage)", //optional
    "tax_point_date": "2024-05-14", //optional
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN", //optional
    "accounting_cost": "2000", //optional
    "buyer_reference": "buyer REF IRN?", //optional
    "invoice_delivery_period": {
        "start_date": "2024-06-14",
        "end_date": "2024-06-16"
    }, //optional
    "order_reference": "order REF IRN?", //optional
    "billing_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        },
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        } //optional - second value to ...x in array is always optional
    ], //optional
    "dispatch_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "receipt_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "originator_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, // optional
    "contract_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "_document_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        }
    ], //optional
    "accounting_supplier_party": {
        "party_name": "Test Pls",
        "tin": "TIN-0099990001",
        "email": "supplier_business@email.com",
        "telephone": "+23480254099000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", 
            "city_name": "Gwarikpa", 
            "postal_zone": "023401", 
            "country": "NG" 
        } 
    },
    "accounting_customer_party": {
        "party_name": "Test Pls",
        "tin": "TIN-000001",
        "email": "business@email.com",
        "telephone": "+23480254000000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", 
            "city_name": "Gwarikpa", 
            "postal_zone": "023401", 
            "country": "NG" 
        } 
    },
    // "payee_party": {}, //optional (party object, just like accounting_customer_party)
    // "tax_representative_party": {}, //optional (party object, just like accounting_customer_party)
    "actual_delivery_date": "2024-05-14", //optional
    "payment_means": [
        {
            "payment_means_code": "10",
            "payment_due_date": "2024-05-14"
        },
        {
            "payment_means_code": "43",
            "payment_due_date": "2024-05-14"
        }//optional - second value to ...x in array is always optional
    ],//optional
    "payment_terms_note": "dummy payment terms note (will be encryted in storage)",//optional
    "allowance_charge": [
        {
            "charge_indicator": true, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 800.60
        },
        {
            "charge_indicator": false, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 10
        }//optional - second value to ...x in array is always optional
    ],//optional
    "tax_total": [
        {
            "tax_amount": 56.07,
            "tax_subtotal": [
                {
                    "taxable_amount": 800,
                    "tax_amount": 8,
                    "tax_category": {
                        "id": "LOCAL_SALES_TAX",
                        "percent": 2.3
                    }
                }
            ]
        }//second value to ...x in array is always optional if you want to add it
    ],//optional
    "legal_monetary_total": {
        "line_extension_amount": 340.50,
        "tax_exclusive_amount": 400,
        "tax_inclusive_amount": 430,
        "payable_amount": 30
    },
    "invoice_line": [
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item name",
                "description": "item description",
                "sellers_item_identification": "identified as spoon by the seller" //optional
            },
            "price": {
                "price_amount": 10,
                "base_quantity": 3,
                "price_unit": "NGN per 1"
            }
        },
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item nam 2",
                "description": "item description 2",
                "sellers_item_identification": "identified as shovel by the seller"
            },
            "price": {
                "price_amount": 20,
                "base_quantity": 5,
                "price_unit": "NGN per 1"
            }
        }//optional - second value to ...x in array is always optional
    ]
}
'
```

b. HEADERS
    - x-api-key         {{IAPI_KEY}}
    - x-api-secret      {{API_SECRET}}

c. Body raw (json)
```json
{
    "business_id": "{{TEST_BUSINESS_ID}}",
    "irn": "ITW20853450-6997D6BB-20240703",
    "issue_date": "2024-05-14",
    "due_date": "2024-06-14", //optional
    "issue_time": "17:59:04", //optional   
    "invoice_type_code": "396",
    "payment_status": "PENDING", //optional, defaults to pending  
    "note": "dummy_note (will be encryted in storage)", //optional
    "tax_point_date": "2024-05-14", //optional
    "document_currency_code": "NGN",
    "tax_currency_code": "NGN", //optional
    "accounting_cost": "2000", //optional
    "buyer_reference": "buyer REF IRN?", //optional
    "invoice_delivery_period": {
        "start_date": "2024-06-14",
        "end_date": "2024-06-16"
    }, //optional
    "order_reference": "order REF IRN?", //optional
    "billing_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        },
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        } //optional - second value to ...x in array is always optional
    ], //optional
    "dispatch_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "receipt_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "originator_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, // optional
    "contract_document_reference": {
        "irn": "ITW001-E9E0C0D3-20240619",
        "issue_date":"2024-05-14"
    }, //optional
    "_document_reference": [
        {
            "irn": "ITW001-E9E0C0D3-20240619",
            "issue_date":"2024-05-14"
        }
    ], //optional
    "accounting_supplier_party": {
        "party_name": "Test Pls",
        "tin": "TIN-0099990001",
        "email": "supplier_business@email.com",
        "telephone": "+23480254099000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", 
            "city_name": "Gwarikpa", 
            "postal_zone": "023401", 
            "country": "NG" 
        } 
    },
    "accounting_customer_party": {
        "party_name": "Test Pls",
        "tin": "TIN-000001",
        "email": "business@email.com",
        "telephone": "+23480254000000", //optional, must start with + (meaning country code) 
        "business_description": "this entity is into sales of Cement and building materials", //optional 
        "postal_address": {
            "street_name": "32, owonikoko street", 
            "city_name": "Gwarikpa", 
            "postal_zone": "023401", 
            "country": "NG" 
        } 
    },
    // "payee_party": {}, //optional (party object, just like accounting_customer_party)
    // "tax_representative_party": {}, //optional (party object, just like accounting_customer_party)
    "actual_delivery_date": "2024-05-14", //optional
    "payment_means": [
        {
            "payment_means_code": "10",
            "payment_due_date": "2024-05-14"
        },
        {
            "payment_means_code": "43",
            "payment_due_date": "2024-05-14"
        }//optional - second value to ...x in array is always optional
    ],//optional
    "payment_terms_note": "dummy payment terms note (will be encryted in storage)",//optional
    "allowance_charge": [
        {
            "charge_indicator": true, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 800.60
        },
        {
            "charge_indicator": false, //indicates whether the amount is a charge (true) or an allowance (false)
            "amount": 10
        }//optional - second value to ...x in array is always optional
    ],//optional
    "tax_total": [
        {
            "tax_amount": 56.07,
            "tax_subtotal": [
                {
                    "taxable_amount": 800,
                    "tax_amount": 8,
                    "tax_category": {
                        "id": "LOCAL_SALES_TAX",
                        "percent": 2.3
                    }
                }
            ]
        }//second value to ...x in array is always optional if you want to add it
    ],//optional
    "legal_monetary_total": {
        "line_extension_amount": 340.50,
        "tax_exclusive_amount": 400,
        "tax_inclusive_amount": 430,
        "payable_amount": 30
    },
    "invoice_line": [
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item name",
                "description": "item description",
                "sellers_item_identification": "identified as spoon by the seller" //optional
            },
            "price": {
                "price_amount": 10,
                "base_quantity": 3,
                "price_unit": "NGN per 1"
            }
        },
        {
            "hsn_code": "CC-001", // 
            "product_category": "Food and Beverages", // 
            "discount_rate": 2.01, // 
            "discount_amount": 3500, // 
            "fee_rate": 1.01, // 
            "fee_amount": 50, // 
            "invoiced_quantity": 15,
            "line_extension_amount": 30,
            "item": {
                "name": "item nam 2",
                "description": "item description 2",
                "sellers_item_identification": "identified as shovel by the seller"
            },
            "price": {
                "price_amount": 20,
                "base_quantity": 5,
                "price_unit": "NGN per 1"
            }
        }//optional - second value to ...x in array is always optional
    ]
}
```

4. GET DownloadInvoice
- {{HOST}}/api/v1/invoice/download/{{TEST_IRN}}
    - This API enables users to download an invoice by just sending certain parameters

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/download/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

5. PATCH UpdateInvoice
- {{HOST}}/api/v1/invoice/update/{{TEST_IRN}}

a. Example Request
```curl
curl --location -g --request PATCH '{{HOST}}/api/v1/invoice/update/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data '{
    "payment_status": "CANCELED", // PENDING, PAID, CANCELED
    "reference": "payment_reference_or_note" //optional
}'
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

c. Body raw (json)
```json
{
    "payment_status": "CANCELED", // PENDING, PAID, CANCELED
    "reference": "payment_reference_or_note" //optional
}
```

6. GET ConfirmInvoice
- {{HOST}}/api/v1/invoice/confirm/{{TEST_IRN}}
    - This API enables users to confirm an invoice by just sending certain parameters

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/confirm/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

7. GET SearchInvoice
- {{HOST}}/api/v1/invoice/{{TEST_BUSINESS_ID}}?size=20&page=1&sort_by=created_at&sort_direction_desc=tr
ue&irn=ITW005-F3A3A0CF-20240703&payment_status=PENDING&invoice_type_code=396&issue_date=202
4-06-14&due_date=2024-06-14&tax_currency_code=NGN&document_currency_code=NGN
    - This API enables users to search an invoice by just sending certain parameters

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/{{TEST_BUSINESS_ID}}?size=20&page=1&sort_by=created_at&sort_direction_desc=true&irn=ITW005-F3A3A0CF-20240703&payment_status=PENDING&invoice_type_code=396&issue_date=2024-06-14&due_date=2024-06-14&tax_currency_code=NGN&document_currency_code=NGN' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

c. PARAMS
    - size                              20

    - page                              1

    - sort_by                           created_at

    - sort_direction_desc               true

    - irn                               ITW005-F3A3A0CF-20240703

    - payment_status                    PENDING

    - invoice_type_code                 396

    - issue_date                        2024-06-14

    - due_date                          2024-06-14

    - tax_currency_code                 NGN

    - document_currency_code            NGN

## Transmitting

1. GET LookupWithIRN
- {{HOST}}/api/v1/invoice/transmit/lookup/{{TEST_IRN}}

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/transmit/lookup/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

2. GET LookupWithTIN
- {{HOST}}/api/v1/invoice/transmit/lookup/{{TEST_IRN}}

a. Example Request
```curl
curl --location -g '{{HOST}}/api/v1/invoice/transmit/lookup/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

3. POST Transmit
- {{HOST}}/api/v1/invoice/transmit/{{TEST_IRN}}

a. Example Request
```curl
curl --location -g --request POST '{{HOST}}/api/v1/invoice/transmit/{{TEST_IRN}}' \
--header 'x-api-key: {{API_KEY}}' \
--header 'x-api-secret: {{API_SECRET}}' \
--data ''
```

b. HEADERS
    - x-api-key         {{API_KEY}}
    - x-api-secret      {{API_SECRET}}

4. GET HealthCheck
- {{HOST}}/api

a. Example Request
```curl
curl --location -g '{{HOST}}/api'
```
