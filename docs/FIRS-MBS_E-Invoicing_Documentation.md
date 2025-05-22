# FIRS-MBS E-Invoicing Documentation 1.0.0 
FIRS-MBS E-Invoicing Documentation is a comprehensive collection of API endpoints that facilitate interaction with the core functionalities and server of the E-invoice system.This collection enables seamless integration with E-invoice operations, providing endpoints for efficient management, retrieval, and processing of electronic invoices. Visit the FIRS E-Invoice Web App to see it action.


## HealthCheck
HealthCheck endpoint verifies that the API and related system components are operational, responsive, and reachable.
1. **GET - /api - HealthCheck**
- Parameters - No parameters
- Responses:
    - Curl
        ```curl
        curl -X 'GET' \
          'https://eivc-k6z6d.ondigitalocean.app/api' \
          -H 'accept: */*'
        ```
    - Request URL
        https://eivc-k6z6d.ondigitalocean.app/api
    - Server response
    Code	                    Details
    200	                    Response body
                            {
                                "healthy": true
                            }
                            Response headers
                            cache-control: private 
                            content-length: 16 
                            content-type: application/json; charset=utf-8 
                            last-modified: Tue,20 May 2025 02:55:21 GMT 


## Search Entity And Business
The API suite includes endpoints designed for creating and managing entities within the E-invoice system.
Specifically, these APIs provide functionalities with the following endpoints.
2. **GET - /api/v1/entity - SearchEntity**

### Search for entity using parameters
- Parameters
**Name**                    **Description**
size                        how many data per page
string
(query)                     20

page	                        what page in the pagination? page 1, 2, 3 or X depending on the totalPages
string
(query)                     1

sort_by                     sort by the query param. i.e sort by 'created_at'
string
(query)                     created_at

sort_direction_desc         sort the 'sort_by'
string
(query)                     true

reference                   searching by a reference
string
(query)                     reference

x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Responses
    - Curl
    ```curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/entity?size=20&page=1&sort_by=created_at&sort_direction_desc=true' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'
    ```
    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/entity?size=20&page=1&sort_by=created_at&sort_direction_desc=true
    - Server response
    **Code**	            **Details**
    400                 Error: response status is 400
    Undocumented

    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "e879185c-2f48-4906-9e56-9e4699820e56",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

3. **GET - /api/v1/entity/{ENTITY_ID} - GetEntity**
### Fetch an entity using entity ID
- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

ENTITY_ID *required         ENTITY_ID=31569955-0001
string
(path)

- Responses
    - Curl
    ```curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/entity/31569955-0001' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'
    ```
    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/entity/31569955-0001
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "948f82c9-1e3a-436b-a460-166e93f6e95b",
        "handler": "entity_actions",
        "details": "invalid UUID length: 13",
        "public_message": "validation failed: we are unable to process your request. also confirm this is not a duplicate request"
      }
    }
    - Response headers
    cache-control: private 
    content-length: 294 
    content-type: application/json; charset=utf-8 


## Manage E-Invoice
Manage E-Invoice API endpoints is designed to perform a full range of invoice-related actions, offering endpoints that support the validation, management, and processing of invoices within the E-invoice system. Each endpoint in this suite is purpose-built to facilitate specific invoice workflows, ensuring seamless, secure, and efficient handling of all invoicing tasks.

4. **POST - /api/v1/invoice/irn/validate - ValidateIRN**

### ValidateIRN
- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body              application/json

- Examples: ValidateIRN
Example Value | Schema
{
  "business_id": "{{BUSINESS_ID}}",
  "invoice_reference": "ITW001",
  "irn": "ITW001-F3A3A0CF-20240619"
}

5. **POST - /api/v1/invoice/validate - ValidateInvoice**

### ValidateInvoice
- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body              application/json

- Examples: ValidateIRN
Example Value
"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"irn\": \"ITW006-F3A3A0CF-20240703\",\n    \"issue_date\": \"2024-05-14\",\n    \"due_date\": \"2024-06-14\", //optional\n    \"issue_time\": \"17:59:04\", //optional\n    \"invoice_type_code\": \"396\",\n    \"payment_status\": \"PENDING\", //optional, defaults to pending\n    \"note\": \"dummy_note (will be encryted in storage)\", //optional\n    \"tax_point_date\": \"2024-05-14\", //optional\n    \"document_currency_code\": \"NGN\",\n    \"tax_currency_code\": \"NGN\", //optional\n    \"accounting_cost\": \"2000 NGN\", //optional\n    \"buyer_reference\": \"buyer REF IRN?\", //optional\n    \"invoice_delivery_period\": {\n        \"start_date\": \"2024-06-14\",\n        \"end_date\": \"2024-06-16\"\n    }, //optional\n    \"order_reference\": \"order REF IRN?\", //optional\n    \"billing_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        },\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        } //optional - second value to ...x in array is always optional\n    ], //optional\n    \"dispatch_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"receipt_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"originator_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, // optional\n    \"contract_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"additional_document_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        }\n    ], //optional\n    \"accounting_supplier_party\": {\n        // \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        \"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-0099990001\", // now mandatory\n        \"email\": \"supplier_business@email.com\", // now mandatory\n        \"telephone\": \"+23480254099000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\" //optional\n        // \"postal_address\": {\n        //     \"street_name\": \"32, owonikoko street\", //optional if id is set\n        //     \"city_name\": \"Gwarikpa\", //optional if id is set\n        //     \"postal_zone\": \"023401\", //optional if id is set\n        //     \"country\": \"NG\" //optional if id is set\n        // } //optional if id is set\n    },\n    \"accounting_customer_party\": {\n        \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000001\", // now mandatory\n        \"email\": \"business@email.com\", // now mandatory\n        \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    // \"payee_party\": {}, //optional (party object, just like accounting_customer_party)\n    // \"tax_representative_party\": {}, //optional (party object, just like accounting_customer_party)\n    \"actual_delivery_date\": \"2024-05-14\", //optional\n    \"payment_means\": [\n        {\n            \"payment_means_code\": \"10\",\n            \"payment_due_date\": \"2024-05-14\"\n        },\n        {\n            \"payment_means_code\": \"43\",\n            \"payment_due_date\": \"2024-05-14\"\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"payment_terms_note\": \"dummy payment terms note (will be encryted in storage)\",//optional\n    \"allowance_charge\": [\n        {\n            \"charge_indicator\": true, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 800.60\n        },\n        {\n            \"charge_indicator\": false, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 10\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"tax_total\": [\n        {\n            \"tax_amount\": 56.07,\n            \"tax_subtotal\": [\n                {\n                    \"taxable_amount\": 800,\n                    \"tax_amount\": 8,\n                    \"tax_category\": {\n                        \"id\": \"LOCAL_SALES_TAX\",\n                        \"percent\": 2.3\n                    }\n                }\n            ]\n        }//second value to ...x in array is always optional if you want to add it\n    ],//optional\n    \"legal_monetary_total\": {\n        \"line_extension_amount\": 340.50,\n        \"tax_exclusive_amount\": 400,\n        \"tax_inclusive_amount\": 430,\n        \"payable_amount\": 30\n    },\n    \"invoice_line\": [\n        {\n            \"hsn_code\": \"CC-001\",\n            \"product_category\": \"Food and Beverages\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 15,\n            \"line_extension_amount\": 30,\n            \"item\": {\n                \"name\": \"item name\",\n                \"description\": \"item description\",\n                \"sellers_item_identification\": \"identified as spoon by the seller\" //optional\n            },\n            \"price\": {\n                \"price_amount\": 10,\n                \"base_quantity\": 3,\n                \"price_unit\": \"NGN per 1\"\n            }\n        },\n        {\n            \"hsn_code\": \"VV-AX-001\",\n            \"product_category\": \"Cars and Automobiles\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 2,\n            \"line_extension_amount\": 100,\n            \"item\": {\n                \"name\": \"item nam 2\",\n                \"description\": \"item description 2\",\n                \"sellers_item_identification\": \"identified as shovel by the seller\"\n            },\n            \"price\": {\n                \"price_amount\": 20,\n                \"base_quantity\": 5,\n                \"price_unit\": \"NGN per 1\"\n            }\n        }//optional - second value to ...x in array is always optional\n    ]\n}"

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/validate' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"irn\": \"ITW006-F3A3A0CF-20240703\",\n    \"issue_date\": \"2024-05-14\",\n    \"due_date\": \"2024-06-14\", //optional\n    \"issue_time\": \"17:59:04\", //optional\n    \"invoice_type_code\": \"396\",\n    \"payment_status\": \"PENDING\", //optional, defaults to pending\n    \"note\": \"dummy_note (will be encryted in storage)\", //optional\n    \"tax_point_date\": \"2024-05-14\", //optional\n    \"document_currency_code\": \"NGN\",\n    \"tax_currency_code\": \"NGN\", //optional\n    \"accounting_cost\": \"2000 NGN\", //optional\n    \"buyer_reference\": \"buyer REF IRN?\", //optional\n    \"invoice_delivery_period\": {\n        \"start_date\": \"2024-06-14\",\n        \"end_date\": \"2024-06-16\"\n    }, //optional\n    \"order_reference\": \"order REF IRN?\", //optional\n    \"billing_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        },\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        } //optional - second value to ...x in array is always optional\n    ], //optional\n    \"dispatch_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"receipt_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"originator_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, // optional\n    \"contract_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"additional_document_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        }\n    ], //optional\n    \"accounting_supplier_party\": {\n        // \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        \"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-0099990001\", // now mandatory\n        \"email\": \"supplier_business@email.com\", // now mandatory\n        \"telephone\": \"+23480254099000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\" //optional\n        // \"postal_address\": {\n        //     \"street_name\": \"32, owonikoko street\", //optional if id is set\n        //     \"city_name\": \"Gwarikpa\", //optional if id is set\n        //     \"postal_zone\": \"023401\", //optional if id is set\n        //     \"country\": \"NG\" //optional if id is set\n        // } //optional if id is set\n    },\n    \"accounting_customer_party\": {\n        \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000001\", // now mandatory\n        \"email\": \"business@email.com\", // now mandatory\n        \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    // \"payee_party\": {}, //optional (party object, just like accounting_customer_party)\n    // \"tax_representative_party\": {}, //optional (party object, just like accounting_customer_party)\n    \"actual_delivery_date\": \"2024-05-14\", //optional\n    \"payment_means\": [\n        {\n            \"payment_means_code\": \"10\",\n            \"payment_due_date\": \"2024-05-14\"\n        },\n        {\n            \"payment_means_code\": \"43\",\n            \"payment_due_date\": \"2024-05-14\"\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"payment_terms_note\": \"dummy payment terms note (will be encryted in storage)\",//optional\n    \"allowance_charge\": [\n        {\n            \"charge_indicator\": true, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 800.60\n        },\n        {\n            \"charge_indicator\": false, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 10\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"tax_total\": [\n        {\n            \"tax_amount\": 56.07,\n            \"tax_subtotal\": [\n                {\n                    \"taxable_amount\": 800,\n                    \"tax_amount\": 8,\n                    \"tax_category\": {\n                        \"id\": \"LOCAL_SALES_TAX\",\n                        \"percent\": 2.3\n                    }\n                }\n            ]\n        }//second value to ...x in array is always optional if you want to add it\n    ],//optional\n    \"legal_monetary_total\": {\n        \"line_extension_amount\": 340.50,\n        \"tax_exclusive_amount\": 400,\n        \"tax_inclusive_amount\": 430,\n        \"payable_amount\": 30\n    },\n    \"invoice_line\": [\n        {\n            \"hsn_code\": \"CC-001\",\n            \"product_category\": \"Food and Beverages\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 15,\n            \"line_extension_amount\": 30,\n            \"item\": {\n                \"name\": \"item name\",\n                \"description\": \"item description\",\n                \"sellers_item_identification\": \"identified as spoon by the seller\" //optional\n            },\n            \"price\": {\n                \"price_amount\": 10,\n                \"base_quantity\": 3,\n                \"price_unit\": \"NGN per 1\"\n            }\n        },\n        {\n            \"hsn_code\": \"VV-AX-001\",\n            \"product_category\": \"Cars and Automobiles\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 2,\n            \"line_extension_amount\": 100,\n            \"item\": {\n                \"name\": \"item nam 2\",\n                \"description\": \"item description 2\",\n                \"sellers_item_identification\": \"identified as shovel by the seller\"\n            },\n            \"price\": {\n                \"price_amount\": 20,\n                \"base_quantity\": 5,\n                \"price_unit\": \"NGN per 1\"\n            }\n        }//optional - second value to ...x in array is always optional\n    ]\n}"'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/validate

    - Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "4617ebc9-d0ce-4c0e-b836-d6dbc4e92d8f",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

6. **POST - /api/v1/invoice/sign - SignInvoice**

### SignInvoice
- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body              application/json
- Examples: SignInvoice
Example Value
"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"irn\": \"ITW011-38A7AB43-20241010\",\n    \"issue_date\": \"2024-05-14\",\n    \"due_date\": \"2024-06-14\", //optional\n    \"issue_time\": \"17:59:04\", //optional\n    \"invoice_type_code\": \"396\",\n    // \"payment_status\": \"PENDING\", //optional, defaults to pending\n    \"note\": \"dummy_note (will be encryted in storage)\", //optional\n    \"tax_point_date\": \"2024-05-14\", //optional\n    \"document_currency_code\": \"NGN\",\n    \"tax_currency_code\": \"NGN\", //optional\n    \"accounting_cost\": \"2000 NGN\", //optional\n    \"buyer_reference\": \"buyer REF IRN?\", //optional\n    \"invoice_delivery_period\": {\n        \"start_date\": \"2024-06-14\",\n        \"end_date\": \"2024-06-16\"\n    }, //optional\n    \"order_reference\": \"order REF IRN?\", //optional\n    \"billing_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        },\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        } //optional - second value to ...x in array is always optional\n    ], //optional\n    \"dispatch_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"receipt_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"originator_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, // optional\n    \"contract_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"additional_document_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        }\n    ], //optional\n    \"accounting_supplier_party\": {\n        // \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000001\", // now mandatory\n        \"email\": \"supplier_business@email.com\", // now mandatory\n        \"telephone\": \"+23480254099000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    \"accounting_customer_party\": {\n        \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Segsalerty R\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000002\", // now mandatory\n        \"email\": \"business@email.com\", // now mandatory\n        \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    // \"payee_party\": {}, //optional (party object, just like accounting_customer_party)\n    // \"tax_representative_party\": {}, //optional (party object, just like accounting_customer_party)\n    \"actual_delivery_date\": \"2024-05-14\", //optional\n    \"payment_means\": [\n        {\n            \"payment_means_code\": \"10\",\n            \"payment_due_date\": \"2024-05-14\"\n        },\n        {\n            \"payment_means_code\": \"43\",\n            \"payment_due_date\": \"2024-05-14\"\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"payment_terms_note\": \"dummy payment terms note (will be encryted in storage)\",//optional\n    \"allowance_charge\": [\n        {\n            \"charge_indicator\": true, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 800.60\n        },\n        {\n            \"charge_indicator\": false, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 10\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"tax_total\": [\n        {\n            \"tax_amount\": 56.07,\n            \"tax_subtotal\": [\n                {\n                    \"taxable_amount\": 800,\n                    \"tax_amount\": 8,\n                    \"tax_category\": {\n                        \"id\": \"LOCAL_SALES_TAX\",\n                        \"percent\": 2.3\n                    }\n                }\n            ]\n        }//second value to ...x in array is always optional if you want to add it\n    ],//optional\n    \"legal_monetary_total\": {\n        \"line_extension_amount\": 340.50,\n        \"tax_exclusive_amount\": 400,\n        \"tax_inclusive_amount\": 430,\n        \"payable_amount\": 30\n    },\n    \"invoice_line\": [\n        {\n            \"hsn_code\": \"CC-001\",\n            \"product_category\": \"Food and Beverages\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 15,\n            \"line_extension_amount\": 30,\n            \"item\": {\n                \"name\": \"item name\",\n                \"description\": \"item description\",\n                \"sellers_item_identification\": \"identified as spoon by the seller\" //optional\n            },\n            \"price\": {\n                \"price_amount\": 10,\n                \"base_quantity\": 3,\n                \"price_unit\": \"NGN per 1\"\n            }\n        },\n        {\n            \"hsn_code\": \"VV-AX-001\",\n            \"product_category\": \"Cars and Automobiles\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 2,\n            \"line_extension_amount\": 100,\n            \"item\": {\n                \"name\": \"item nam 2\",\n                \"description\": \"item description 2\",\n                \"sellers_item_identification\": \"identified as shovel by the seller\"\n            },\n            \"price\": {\n                \"price_amount\": 20,\n                \"base_quantity\": 5,\n                \"price_unit\": \"NGN per 1\"\n            }\n        }//optional - second value to ...x in array is always optional\n    ]\n}"

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/sign' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"irn\": \"ITW011-38A7AB43-20241010\",\n    \"issue_date\": \"2024-05-14\",\n    \"due_date\": \"2024-06-14\", //optional\n    \"issue_time\": \"17:59:04\", //optional\n    \"invoice_type_code\": \"396\",\n    // \"payment_status\": \"PENDING\", //optional, defaults to pending\n    \"note\": \"dummy_note (will be encryted in storage)\", //optional\n    \"tax_point_date\": \"2024-05-14\", //optional\n    \"document_currency_code\": \"NGN\",\n    \"tax_currency_code\": \"NGN\", //optional\n    \"accounting_cost\": \"2000 NGN\", //optional\n    \"buyer_reference\": \"buyer REF IRN?\", //optional\n    \"invoice_delivery_period\": {\n        \"start_date\": \"2024-06-14\",\n        \"end_date\": \"2024-06-16\"\n    }, //optional\n    \"order_reference\": \"order REF IRN?\", //optional\n    \"billing_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        },\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        } //optional - second value to ...x in array is always optional\n    ], //optional\n    \"dispatch_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"receipt_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"originator_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, // optional\n    \"contract_document_reference\": {\n        \"irn\": \"ITW001-E9E0C0D3-20240619\",\n        \"issue_date\":\"2024-05-14\"\n    }, //optional\n    \"additional_document_reference\": [\n        {\n            \"irn\": \"ITW001-E9E0C0D3-20240619\",\n            \"issue_date\":\"2024-05-14\"\n        }\n    ], //optional\n    \"accounting_supplier_party\": {\n        // \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Dangote Group\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000001\", // now mandatory\n        \"email\": \"supplier_business@email.com\", // now mandatory\n        \"telephone\": \"+23480254099000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    \"accounting_customer_party\": {\n        \"id\": \"{{PARTY_ID}}\", //optional if party_name and postal_address is set\n        \"party_name\": \"Segsalerty R\", //optional if id is set\n        //\"postal_address_id\": \"{{TEST_ADDRESS_ID}}\", //optional if postal_address is set\n        \"tin\": \"TIN-000002\", // now mandatory\n        \"email\": \"business@email.com\", // now mandatory\n        \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n        \"business_description\": \"this entity is into sales of Cement and building materials\", //optional\n        \"postal_address\": {\n            \"street_name\": \"32, owonikoko street\", //optional if id is set\n            \"city_name\": \"Gwarikpa\", //optional if id is set\n            \"postal_zone\": \"023401\", //optional if id is set\n            \"country\": \"NG\" //optional if id is set\n        } //optional if id is set\n    },\n    // \"payee_party\": {}, //optional (party object, just like accounting_customer_party)\n    // \"tax_representative_party\": {}, //optional (party object, just like accounting_customer_party)\n    \"actual_delivery_date\": \"2024-05-14\", //optional\n    \"payment_means\": [\n        {\n            \"payment_means_code\": \"10\",\n            \"payment_due_date\": \"2024-05-14\"\n        },\n        {\n            \"payment_means_code\": \"43\",\n            \"payment_due_date\": \"2024-05-14\"\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"payment_terms_note\": \"dummy payment terms note (will be encryted in storage)\",//optional\n    \"allowance_charge\": [\n        {\n            \"charge_indicator\": true, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 800.60\n        },\n        {\n            \"charge_indicator\": false, //indicates whether the amount is a charge (true) or an allowance (false)\n            \"amount\": 10\n        }//optional - second value to ...x in array is always optional\n    ],//optional\n    \"tax_total\": [\n        {\n            \"tax_amount\": 56.07,\n            \"tax_subtotal\": [\n                {\n                    \"taxable_amount\": 800,\n                    \"tax_amount\": 8,\n                    \"tax_category\": {\n                        \"id\": \"LOCAL_SALES_TAX\",\n                        \"percent\": 2.3\n                    }\n                }\n            ]\n        }//second value to ...x in array is always optional if you want to add it\n    ],//optional\n    \"legal_monetary_total\": {\n        \"line_extension_amount\": 340.50,\n        \"tax_exclusive_amount\": 400,\n        \"tax_inclusive_amount\": 430,\n        \"payable_amount\": 30\n    },\n    \"invoice_line\": [\n        {\n            \"hsn_code\": \"CC-001\",\n            \"product_category\": \"Food and Beverages\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 15,\n            \"line_extension_amount\": 30,\n            \"item\": {\n                \"name\": \"item name\",\n                \"description\": \"item description\",\n                \"sellers_item_identification\": \"identified as spoon by the seller\" //optional\n            },\n            \"price\": {\n                \"price_amount\": 10,\n                \"base_quantity\": 3,\n                \"price_unit\": \"NGN per 1\"\n            }\n        },\n        {\n            \"hsn_code\": \"VV-AX-001\",\n            \"product_category\": \"Cars and Automobiles\",\n            \"dicount_rate\": 2.01,\n            \"dicount_amount\": 3500,\n            \"fee_rate\": 1.01,\n            \"fee_amount\": 50,\n            \"invoiced_quantity\": 2,\n            \"line_extension_amount\": 100,\n            \"item\": {\n                \"name\": \"item nam 2\",\n                \"description\": \"item description 2\",\n                \"sellers_item_identification\": \"identified as shovel by the seller\"\n            },\n            \"price\": {\n                \"price_amount\": 20,\n                \"base_quantity\": 5,\n                \"price_unit\": \"NGN per 1\"\n            }\n        }//optional - second value to ...x in array is always optional\n    ]\n}"'

- Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/sign

    - Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
        {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "862bed30-db2c-4586-bf58-f216e658968c",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

7. **POST - /api/v1/invoice/party - CreateParty**

### CreateParty

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body              application/json

- Examples: CreateParty
Example Value
"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"party_name\": \"Dangote Group TMZ\",\n    \"postal_address_id\": \"940848d6-6c9d-44cc-851c-d1c69edcec95\", //optional if postal_address is set\n    \"tin\": \"TIN-000001\", // now mandatory\n    \"email\": \"business@email.com\", // now mandatory\n    \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n    \"business_description\": \"this entity is into sales of Cement and building materials\" //optional\n    // \"postal_address\": {\n    //     \"street_name\": \"91, owonikoko street\",\n    //     \"city_name\": \"Malta\",\n    //     \"postal_zone\": \"023401\",\n    //     \"country\": \"NG\"\n    // }\n}"

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/party' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '"{\n    \"business_id\": \"{{BUSINESS_ID}}\",\n    \"party_name\": \"Dangote Group TMZ\",\n    \"postal_address_id\": \"940848d6-6c9d-44cc-851c-d1c69edcec95\", //optional if postal_address is set\n    \"tin\": \"TIN-000001\", // now mandatory\n    \"email\": \"business@email.com\", // now mandatory\n    \"telephone\": \"+23480254000000\", //optional, must start with + (meaning country code)\n    \"business_description\": \"this entity is into sales of Cement and building materials\" //optional\n    // \"postal_address\": {\n    //     \"street_name\": \"91, owonikoko street\",\n    //     \"city_name\": \"Malta\",\n    //     \"postal_zone\": \"023401\",\n    //     \"country\": \"NG\"\n    // }\n}"'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/party

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "3efd9517-ef39-4eec-98c5-f96c1a3e71e5",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }
    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 

8. **GET - /api/v1/invoice/party/{BUSINESS_ID} - SearchParty**

### SearchParty
- Parameters
**Name**                    **Description**
size                        how many data per page
string
(query)                     20

page	                        what page in the pagination? page 1, 2, 3 or X depending on the totalPages
string
(query)                     1

sort_by                     sort by the query param. i.e sort by 'created_at'
string
(query)                     created_at

sort_direction_desc         sort the 'sort_by'
string
(query)                     true

party_name                  party_name
string
(query)

x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

BUSINESS_ID *               BUSINESS_ID=31569955-0001
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/party/31569955-0001?        size=20&page=1&sort_by=created_at&sort_direction_desc=true' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'
    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/party/31569955-0001?size=20&page=1&sort_by=created_at&sort_direction_desc=true

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "5b290d7d-9c59-41c8-9eb9-cf0a0cdaca61",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

9. **GET - /api/v1/invoice/confirm/{IRN} - ConfirmInvoice**

### ConfirmInvoice

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/confirm/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/confirm/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "0f91c8d4-951d-49e0-97f8-6dbff5c73f1a",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

10. **GET - /api/v1/invoice/download/{IRN} - DownloadInvoice**

### DownloadInvoice

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/download/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/download/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "5dfcd9fb-d968-4e82-9253-def9bbf605fa",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

11. **GET - /api/v1/invoice/{BUSINESS_ID} - SearchInvoice**

### SearchInvoice
- Parameters
**Name**                    **Description**
size                        20
string
(query)

page                        1
string
(query)

sort_by                     created_at
string
(query)

sort_direction_desc         true
string
(query)

irn                         ITW005-F3A3A0CF-20240703
string
(query)

payment_status              PENDING
string
(query)

entry_status                entry_status
string
(query)

invoice_type_code           invoice_type_code
string
(query)

issue_date                  issue_date
string
(query)

due_date                    due_date
string
(query)

tax_currency_code           tax_currency_code
string
(query)

document_currency_code      document_currency_code
string
(query)

x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

BUSINESS_ID *required       BUSINESS_ID=31569955-0001
string
(path)

- Request body              application/json
- Examples: SearchInvoice
Example Value
""
- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/31569955-0001?size=20&page=1&sort_by=created_at&sort_direction_desc=true&irn=ITW005-F3A3A0CF-20240703&payment_status=PENDING' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '""'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/31569955-0001?size=20&page=1&sort_by=created_at&sort_direction_desc=true&irn=ITW005-F3A3A0CF-20240703&payment_status=PENDING

- Server response
    - Server response
        **Code**	            **Details**
        400                 TypeError: Failed to execute 'fetch' on 'Window': Request with GET/HEAD method cannot have body.
        Undocumented

12. **PATCH - /api/v1/invoice/update/{IRN} - UpdateInvoice**

### UpdateInvoice

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Request body              application/json
- Examples: SearchInvoice
Example Value
"{\n    \"payment_status\": \"PAID\",\n    \"reference\": \"payment_reference_or_note\" //optional\n}"

- Responses
    - Curl
    curl -X 'PATCH' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/update/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '"{\n    \"payment_status\": \"PAID\",\n    \"reference\": \"payment_reference_or_note\" //optional\n}"'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/update/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "cccb3df3-1fca-4114-b5fd-6d17d7dbe759",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 


## Exchange E-Invoice
Exchange E-Invoice API endpoints is specifically designed to facilitate and streamline the secure transmission and management of invoices. It provides essential tools for searching, sending, receiving, and verifying invoice transmissions between parties, as well as robust debugging options for enhanced reliability and traceability.

13. **GET - /api/v1/invoice/transmit/lookup/{IRN} - LookupWithIRN**

### LookupWithIRN

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "253c7bd0-a1e6-40ca-a7be-c83917b7a58d",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 

14. **GET - /api/v1/invoice/transmit/lookup/tin/{PARTY_ID} - LookupWithTIN**

### LookupWithTIN

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

PARTY_ID *required       PARTY_ID=31569955-0001
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/tin/31569955-0001' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/tin/31569955-0001

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "be79776c-d9d7-4b02-92ee-35913177e2d5",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
    cache-control: private 
    content-length: 175 
    content-type: application/json; charset=utf-8 


15. **GET - /api/v1/invoice/transmit/lookup/party/{PARTY_ID} - LookupWithPartyID**

### LookupWithPartyID

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

PARTY_ID *required       PARTY_ID=31569955-0001
string
(path)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/party/31569955-0001' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/lookup/party/31569955-0001

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "67176eea-a9fc-455c-8e7e-139eea9a872d",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

- Responses
**Code**        	**Description**	    **Links**
200                                  No links


16. **POST - /api/v1/invoice/transmit/{IRN} - Transmit**

### Transmit

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Request body              application/json
- Examples: Transmit
Example Value
""

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '""'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "afd5c536-9a1a-4f67-8f5a-443413e5f509",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8


17. **PATCH - /api/v1/invoice/transmit/{IRN} - ConfirmReceipt**

### ConfirmReceipt

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

TEST_IRN *required          TEST_IRN=NG12345678901234567890123456789012345
string
(path)

- Request body              application/json
- Examples: ConfirmReceipt
Example Value
""

- Responses
    - Curl
    curl -X 'PATCH' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/{IRN}' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '""'
    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/{IRN}

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "32c98b0c-d166-4357-a982-20f4036792b6",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 


18. **GET - /api/v1/invoice/transmit/self-health-check - SelfCheck-Debug-Setup**

### SelfCheck-Debug-Setup

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/self-health-check' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/self-health-check

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "22a9735c-59c1-47cf-9334-9d6f1e200181",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 


19. **GET - /api/v1/invoice/transmit/pull - Pull**

### Pull

- Parameters
**Name**                    **Description**
confirmed                   true
string
(query)

from                        2023-01-11
string
(query)

to                          2025-01-10
string
(query)

x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/pull?confirmed=true&from=2023-01-11&to=2025-01-10' \
      -H 'accept: */*' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/transmit/pull?confirmed=true&from=2023-01-11&to=2025-01-10

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented
    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "901eced2-9637-4f66-8319-ff60594995f1",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 


## Report E-Invoice
Report invoice[s] to the FIRS einvoice team for financial actions.

20. **POST - /v1/vat/postPayment - Post transaction**

### Post transaction

- Parameters
**Name**                    **Description**
No parameters

- Request body                  application/json
- Examples: Post transaction
Example Value | Schema
{
  "agentTin": "1234458823",
  "baseAmount": "10.00",
  "beneficiaryTin": "1234458824",
  "currency": 1,
  "itemDescription": "Items",
  "otherTaxes": "1.95",
  "totalAmount": "20.00",
  "transDate": "2024-11-04",
  "vatCalculated": "12.45",
  "vatRate": "0.95",
  "vatStatus": 0,
  "vendorTransactionId": "12991209"
}

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/v1/vat/postPayment' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{
      "agentTin": "1234458823",
      "baseAmount": "10.00",
      "beneficiaryTin": "1234458824",
      "currency": 1,
      "itemDescription": "Items",
      "otherTaxes": "1.95",
      "totalAmount": "20.00",
      "transDate": "2024-11-04",
      "vatCalculated": "12.45",
      "vatRate": "0.95",
      "vatStatus": 0,
      "vendorTransactionId": "12991209"
    }'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/v1/vat/postPayment

- Server response
    - Server response
        **Code**	            **Details**
        404                 Error: response status is 404
        Undocumented
    - Response body
    {
      "code": 404,
      "data": null,
      "message": "no route found for this path. kindly check your request and try again"
    }

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 

    - Responses
    **Code**        	        **Description**	            **Links**
    200                     Successful operation         No links

    - Media type: application/json
    Controls Accept header.
    Example Value | Schema
    {
      "agentTin": "1234458823",
      "beneficiaryTin": "1234458824",
      "currency": 1,
      "transDate": "2024-11-04T00:00:00.000Z",
      "baseAmount": 10,
      "vatCalculated": 12.45,
      "totalAmount": 20,
      "otherTaxes": 1.95,
      "vatRate": 0.95,
      "vatStatus": false,
      "itemDescription": "Items",
      "vendorTransactionId": 1299120459,
      "userId": "6728c19460745b3d2d3bb23f",
      "createdAt": "2024-11-15T14:23:06.197Z",
      "id": "6737594a1465395a06699a81"
    }


## Utilities
Utilities are endpoints that provides additional functionalities around e-invoice and third-party services.

21. **POST - /api/v1/utilities/verify-tin/ - VerifyTin**

### VerifyTin

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body              application/json

- Examples: VerifyTin
Example Value | Schema
{
  "tin": "20198222-0002"
}

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/utilities/verify-tin/' \
      -H 'accept: application/json' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '{
      "tin": "20198222-0002"
    }'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/utilities/verify-tin/

- Server response
    - Server response
        **Code**	            **Details**
    Undocumented            Failed to fetch.
                            Possible Reasons:
                            - CORS
                            - Network Failure
                            - URL scheme must be "http" or "https" for CORS request.

- Responses
    **Code**        	        **Description**	            **Links**
    200                     	200-sample-response         No links

    - Media type - application/json     Examples - 200-sample-response
        Controls Accept header.
    
    Example Value | Schema
    {
      "code": 200,
      "data": {
        "address": "100th FLOOR, MILK STREET ABC",
        "email": "johndoe@gmail.com",
        "id": "4e892e8b-04a3-4a05-98ab-6ff5679295ff",
        "jtb_tin": "",
        "message": "TIN Information",
        "phone": "06012138317",
        "rc_number": "1401999",
        "status": "200 OK",
        "taxofficer_id": "23",
        "taxofficer_name": "MSTO JOHN DOE",
        "taxpayer_name": "ABC AND XYZ Company",
        "taxpayer_type": "C",
        "tin": "20198222-0002"
      }
    }

22. **POST - /api/v1/utilities/authenticate - AuthenticateTaxPayer**

### AuthenticateTaxPayer

- Parameters
**Name**                    **Description**
x-api-key                   {{API_KEY}}
string
(header)

x-api-secret                {{API_SECRET}}
string
(header)

- Request body                  application/json

- Examples: AuthenticateTaxPayer
Example Value | Schema
{
  "email": "johndoe@email.com",
  "password": "johdoespassword"
}

- Responses
    - Curl
    curl -X 'POST' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/utilities/authenticate' \
      -H 'accept: application/json' \
      -H 'x-api-key: {{API_KEY}}' \
      -H 'x-api-secret: {{API_SECRET}}' \
      -H 'Content-Type: application/json' \
      -d '{
      "email": "johndoe@email.com",
      "password": "johdoespassword"
    }'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/utilities/authenticate

- Server response
    - Server response
        **Code**	            **Details**
        400                 Error: response status is 400
        Undocumented

    - Response body
    {
      "code": 400,
      "data": null,
      "message": "error has occurred",
      "error": {
        "id": "d90f62f6-0ce2-455d-8b8d-012cd435892c",
        "handler": "handler",
        "public_message": "unable to validate api key"
      }
    }

    - Response headers
     cache-control: private 
     content-length: 175 
     content-type: application/json; charset=utf-8 

- Responses
    **Code**        	        **Description**	            **Links**
    200                     	200-sample-response         No links

    - Media type - application/json     Examples - 200-sample-response
        Controls Accept header.
    
    Example Value | Schema
    {
      "code": 200,
      "data": {
        "entity_id": "779b7ac1-f772-5da3-8ece-6y458a98dg12",
        "id": "812ac36c-8677-4e8b-bcb9-4c432ed7858f",
        "message": "User logged in",
        "received_at": "2024-11-18T13:54:54.932852472+01:00",
        "status": "200 OK"
      }
    }


## Resources
This section provides endpoints to retrieve utility data.

23. **GET - /api/v1/invoice/resources/countries - GetCountries**

### GetCountries

- Parameters
**Name**                    **Description**
No parameters

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/countries' \
      -H 'accept: */*'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/countries

- Server response
    - Server response
        **Code**	            **Details**
        200

    - Response body
    {
  "code": 200,
  "data": [
    {
      "name": "Afghanistan",
      "alpha_2": "AF",
      "alpha_3": "AFG",
      "country_code": "004",
      "iso_3166_2": "ISO 3166-2:AF",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Åland Islands",
      "alpha_2": "AX",
      "alpha_3": "ALA",
      "country_code": "248",
      "iso_3166_2": "ISO 3166-2:AX",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Albania",
      "alpha_2": "AL",
      "alpha_3": "ALB",
      "country_code": "008",
      "iso_3166_2": "ISO 3166-2:AL",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Algeria",
      "alpha_2": "DZ",
      "alpha_3": "DZA",
      "country_code": "012",
      "iso_3166_2": "ISO 3166-2:DZ",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "American Samoa",
      "alpha_2": "AS",
      "alpha_3": "ASM",
      "country_code": "016",
      "iso_3166_2": "ISO 3166-2:AS",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Andorra",
      "alpha_2": "AD",
      "alpha_3": "AND",
      "country_code": "020",
      "iso_3166_2": "ISO 3166-2:AD",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Angola",
      "alpha_2": "AO",
      "alpha_3": "AGO",
      "country_code": "024",
      "iso_3166_2": "ISO 3166-2:AO",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Anguilla",
      "alpha_2": "AI",
      "alpha_3": "AIA",
      "country_code": "660",
      "iso_3166_2": "ISO 3166-2:AI",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Antarctica",
      "alpha_2": "AQ",
      "alpha_3": "ATA",
      "country_code": "010",
      "iso_3166_2": "ISO 3166-2:AQ",
      "region": "",
      "sub_region": "",
      "intermediate_region": "",
      "region_code": "",
      "sub_region_code": "",
      "intermediate_region_code": ""
    },
    {
      "name": "Antigua and Barbuda",
      "alpha_2": "AG",
      "alpha_3": "ATG",
      "country_code": "028",
      "iso_3166_2": "ISO 3166-2:AG",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Argentina",
      "alpha_2": "AR",
      "alpha_3": "ARG",
      "country_code": "032",
      "iso_3166_2": "ISO 3166-2:AR",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Armenia",
      "alpha_2": "AM",
      "alpha_3": "ARM",
      "country_code": "051",
      "iso_3166_2": "ISO 3166-2:AM",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Aruba",
      "alpha_2": "AW",
      "alpha_3": "ABW",
      "country_code": "533",
      "iso_3166_2": "ISO 3166-2:AW",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Australia",
      "alpha_2": "AU",
      "alpha_3": "AUS",
      "country_code": "036",
      "iso_3166_2": "ISO 3166-2:AU",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "Austria",
      "alpha_2": "AT",
      "alpha_3": "AUT",
      "country_code": "040",
      "iso_3166_2": "ISO 3166-2:AT",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Azerbaijan",
      "alpha_2": "AZ",
      "alpha_3": "AZE",
      "country_code": "031",
      "iso_3166_2": "ISO 3166-2:AZ",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Bahamas",
      "alpha_2": "BS",
      "alpha_3": "BHS",
      "country_code": "044",
      "iso_3166_2": "ISO 3166-2:BS",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Bahrain",
      "alpha_2": "BH",
      "alpha_3": "BHR",
      "country_code": "048",
      "iso_3166_2": "ISO 3166-2:BH",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Bangladesh",
      "alpha_2": "BD",
      "alpha_3": "BGD",
      "country_code": "050",
      "iso_3166_2": "ISO 3166-2:BD",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Barbados",
      "alpha_2": "BB",
      "alpha_3": "BRB",
      "country_code": "052",
      "iso_3166_2": "ISO 3166-2:BB",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Belarus",
      "alpha_2": "BY",
      "alpha_3": "BLR",
      "country_code": "112",
      "iso_3166_2": "ISO 3166-2:BY",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Belgium",
      "alpha_2": "BE",
      "alpha_3": "BEL",
      "country_code": "056",
      "iso_3166_2": "ISO 3166-2:BE",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Belize",
      "alpha_2": "BZ",
      "alpha_3": "BLZ",
      "country_code": "084",
      "iso_3166_2": "ISO 3166-2:BZ",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Benin",
      "alpha_2": "BJ",
      "alpha_3": "BEN",
      "country_code": "204",
      "iso_3166_2": "ISO 3166-2:BJ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Bermuda",
      "alpha_2": "BM",
      "alpha_3": "BMU",
      "country_code": "060",
      "iso_3166_2": "ISO 3166-2:BM",
      "region": "Americas",
      "sub_region": "Northern America",
      "intermediate_region": "",
      "region_code": "019",
      "sub_region_code": "021",
      "intermediate_region_code": ""
    },
    {
      "name": "Bhutan",
      "alpha_2": "BT",
      "alpha_3": "BTN",
      "country_code": "064",
      "iso_3166_2": "ISO 3166-2:BT",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Bolivia (Plurinational State of)",
      "alpha_2": "BO",
      "alpha_3": "BOL",
      "country_code": "068",
      "iso_3166_2": "ISO 3166-2:BO",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Bonaire, Sint Eustatius and Saba",
      "alpha_2": "BQ",
      "alpha_3": "BES",
      "country_code": "535",
      "iso_3166_2": "ISO 3166-2:BQ",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Bosnia and Herzegovina",
      "alpha_2": "BA",
      "alpha_3": "BIH",
      "country_code": "070",
      "iso_3166_2": "ISO 3166-2:BA",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Botswana",
      "alpha_2": "BW",
      "alpha_3": "BWA",
      "country_code": "072",
      "iso_3166_2": "ISO 3166-2:BW",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Southern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "018"
    },
    {
      "name": "Bouvet Island",
      "alpha_2": "BV",
      "alpha_3": "BVT",
      "country_code": "074",
      "iso_3166_2": "ISO 3166-2:BV",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Brazil",
      "alpha_2": "BR",
      "alpha_3": "BRA",
      "country_code": "076",
      "iso_3166_2": "ISO 3166-2:BR",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "British Indian Ocean Territory",
      "alpha_2": "IO",
      "alpha_3": "IOT",
      "country_code": "086",
      "iso_3166_2": "ISO 3166-2:IO",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Brunei Darussalam",
      "alpha_2": "BN",
      "alpha_3": "BRN",
      "country_code": "096",
      "iso_3166_2": "ISO 3166-2:BN",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Bulgaria",
      "alpha_2": "BG",
      "alpha_3": "BGR",
      "country_code": "100",
      "iso_3166_2": "ISO 3166-2:BG",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Burkina Faso",
      "alpha_2": "BF",
      "alpha_3": "BFA",
      "country_code": "854",
      "iso_3166_2": "ISO 3166-2:BF",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Burundi",
      "alpha_2": "BI",
      "alpha_3": "BDI",
      "country_code": "108",
      "iso_3166_2": "ISO 3166-2:BI",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Cabo Verde",
      "alpha_2": "CV",
      "alpha_3": "CPV",
      "country_code": "132",
      "iso_3166_2": "ISO 3166-2:CV",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Cambodia",
      "alpha_2": "KH",
      "alpha_3": "KHM",
      "country_code": "116",
      "iso_3166_2": "ISO 3166-2:KH",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Cameroon",
      "alpha_2": "CM",
      "alpha_3": "CMR",
      "country_code": "120",
      "iso_3166_2": "ISO 3166-2:CM",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Canada",
      "alpha_2": "CA",
      "alpha_3": "CAN",
      "country_code": "124",
      "iso_3166_2": "ISO 3166-2:CA",
      "region": "Americas",
      "sub_region": "Northern America",
      "intermediate_region": "",
      "region_code": "019",
      "sub_region_code": "021",
      "intermediate_region_code": ""
    },
    {
      "name": "Cayman Islands",
      "alpha_2": "KY",
      "alpha_3": "CYM",
      "country_code": "136",
      "iso_3166_2": "ISO 3166-2:KY",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Central African Republic",
      "alpha_2": "CF",
      "alpha_3": "CAF",
      "country_code": "140",
      "iso_3166_2": "ISO 3166-2:CF",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Chad",
      "alpha_2": "TD",
      "alpha_3": "TCD",
      "country_code": "148",
      "iso_3166_2": "ISO 3166-2:TD",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Chile",
      "alpha_2": "CL",
      "alpha_3": "CHL",
      "country_code": "152",
      "iso_3166_2": "ISO 3166-2:CL",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "China",
      "alpha_2": "CN",
      "alpha_3": "CHN",
      "country_code": "156",
      "iso_3166_2": "ISO 3166-2:CN",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Christmas Island",
      "alpha_2": "CX",
      "alpha_3": "CXR",
      "country_code": "162",
      "iso_3166_2": "ISO 3166-2:CX",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "Cocos (Keeling) Islands",
      "alpha_2": "CC",
      "alpha_3": "CCK",
      "country_code": "166",
      "iso_3166_2": "ISO 3166-2:CC",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "Colombia",
      "alpha_2": "CO",
      "alpha_3": "COL",
      "country_code": "170",
      "iso_3166_2": "ISO 3166-2:CO",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Comoros",
      "alpha_2": "KM",
      "alpha_3": "COM",
      "country_code": "174",
      "iso_3166_2": "ISO 3166-2:KM",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Congo",
      "alpha_2": "CG",
      "alpha_3": "COG",
      "country_code": "178",
      "iso_3166_2": "ISO 3166-2:CG",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Congo, Democratic Republic of the",
      "alpha_2": "CD",
      "alpha_3": "COD",
      "country_code": "180",
      "iso_3166_2": "ISO 3166-2:CD",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Cook Islands",
      "alpha_2": "CK",
      "alpha_3": "COK",
      "country_code": "184",
      "iso_3166_2": "ISO 3166-2:CK",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Costa Rica",
      "alpha_2": "CR",
      "alpha_3": "CRI",
      "country_code": "188",
      "iso_3166_2": "ISO 3166-2:CR",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Côte d'Ivoire",
      "alpha_2": "CI",
      "alpha_3": "CIV",
      "country_code": "384",
      "iso_3166_2": "ISO 3166-2:CI",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Croatia",
      "alpha_2": "HR",
      "alpha_3": "HRV",
      "country_code": "191",
      "iso_3166_2": "ISO 3166-2:HR",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Cuba",
      "alpha_2": "CU",
      "alpha_3": "CUB",
      "country_code": "192",
      "iso_3166_2": "ISO 3166-2:CU",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Curaçao",
      "alpha_2": "CW",
      "alpha_3": "CUW",
      "country_code": "531",
      "iso_3166_2": "ISO 3166-2:CW",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Cyprus",
      "alpha_2": "CY",
      "alpha_3": "CYP",
      "country_code": "196",
      "iso_3166_2": "ISO 3166-2:CY",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Czechia",
      "alpha_2": "CZ",
      "alpha_3": "CZE",
      "country_code": "203",
      "iso_3166_2": "ISO 3166-2:CZ",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Denmark",
      "alpha_2": "DK",
      "alpha_3": "DNK",
      "country_code": "208",
      "iso_3166_2": "ISO 3166-2:DK",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Djibouti",
      "alpha_2": "DJ",
      "alpha_3": "DJI",
      "country_code": "262",
      "iso_3166_2": "ISO 3166-2:DJ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Dominica",
      "alpha_2": "DM",
      "alpha_3": "DMA",
      "country_code": "212",
      "iso_3166_2": "ISO 3166-2:DM",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Dominican Republic",
      "alpha_2": "DO",
      "alpha_3": "DOM",
      "country_code": "214",
      "iso_3166_2": "ISO 3166-2:DO",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Ecuador",
      "alpha_2": "EC",
      "alpha_3": "ECU",
      "country_code": "218",
      "iso_3166_2": "ISO 3166-2:EC",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Egypt",
      "alpha_2": "EG",
      "alpha_3": "EGY",
      "country_code": "818",
      "iso_3166_2": "ISO 3166-2:EG",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "El Salvador",
      "alpha_2": "SV",
      "alpha_3": "SLV",
      "country_code": "222",
      "iso_3166_2": "ISO 3166-2:SV",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Equatorial Guinea",
      "alpha_2": "GQ",
      "alpha_3": "GNQ",
      "country_code": "226",
      "iso_3166_2": "ISO 3166-2:GQ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Eritrea",
      "alpha_2": "ER",
      "alpha_3": "ERI",
      "country_code": "232",
      "iso_3166_2": "ISO 3166-2:ER",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Estonia",
      "alpha_2": "EE",
      "alpha_3": "EST",
      "country_code": "233",
      "iso_3166_2": "ISO 3166-2:EE",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Eswatini",
      "alpha_2": "SZ",
      "alpha_3": "SWZ",
      "country_code": "748",
      "iso_3166_2": "ISO 3166-2:SZ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Southern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "018"
    },
    {
      "name": "Ethiopia",
      "alpha_2": "ET",
      "alpha_3": "ETH",
      "country_code": "231",
      "iso_3166_2": "ISO 3166-2:ET",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Falkland Islands (Malvinas)",
      "alpha_2": "FK",
      "alpha_3": "FLK",
      "country_code": "238",
      "iso_3166_2": "ISO 3166-2:FK",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Faroe Islands",
      "alpha_2": "FO",
      "alpha_3": "FRO",
      "country_code": "234",
      "iso_3166_2": "ISO 3166-2:FO",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Fiji",
      "alpha_2": "FJ",
      "alpha_3": "FJI",
      "country_code": "242",
      "iso_3166_2": "ISO 3166-2:FJ",
      "region": "Oceania",
      "sub_region": "Melanesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "054",
      "intermediate_region_code": ""
    },
    {
      "name": "Finland",
      "alpha_2": "FI",
      "alpha_3": "FIN",
      "country_code": "246",
      "iso_3166_2": "ISO 3166-2:FI",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "France",
      "alpha_2": "FR",
      "alpha_3": "FRA",
      "country_code": "250",
      "iso_3166_2": "ISO 3166-2:FR",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "French Guiana",
      "alpha_2": "GF",
      "alpha_3": "GUF",
      "country_code": "254",
      "iso_3166_2": "ISO 3166-2:GF",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "French Polynesia",
      "alpha_2": "PF",
      "alpha_3": "PYF",
      "country_code": "258",
      "iso_3166_2": "ISO 3166-2:PF",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "French Southern Territories",
      "alpha_2": "TF",
      "alpha_3": "ATF",
      "country_code": "260",
      "iso_3166_2": "ISO 3166-2:TF",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Gabon",
      "alpha_2": "GA",
      "alpha_3": "GAB",
      "country_code": "266",
      "iso_3166_2": "ISO 3166-2:GA",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Gambia",
      "alpha_2": "GM",
      "alpha_3": "GMB",
      "country_code": "270",
      "iso_3166_2": "ISO 3166-2:GM",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Georgia",
      "alpha_2": "GE",
      "alpha_3": "GEO",
      "country_code": "268",
      "iso_3166_2": "ISO 3166-2:GE",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Germany",
      "alpha_2": "DE",
      "alpha_3": "DEU",
      "country_code": "276",
      "iso_3166_2": "ISO 3166-2:DE",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Ghana",
      "alpha_2": "GH",
      "alpha_3": "GHA",
      "country_code": "288",
      "iso_3166_2": "ISO 3166-2:GH",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Gibraltar",
      "alpha_2": "GI",
      "alpha_3": "GIB",
      "country_code": "292",
      "iso_3166_2": "ISO 3166-2:GI",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Greece",
      "alpha_2": "GR",
      "alpha_3": "GRC",
      "country_code": "300",
      "iso_3166_2": "ISO 3166-2:GR",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Greenland",
      "alpha_2": "GL",
      "alpha_3": "GRL",
      "country_code": "304",
      "iso_3166_2": "ISO 3166-2:GL",
      "region": "Americas",
      "sub_region": "Northern America",
      "intermediate_region": "",
      "region_code": "019",
      "sub_region_code": "021",
      "intermediate_region_code": ""
    },
    {
      "name": "Grenada",
      "alpha_2": "GD",
      "alpha_3": "GRD",
      "country_code": "308",
      "iso_3166_2": "ISO 3166-2:GD",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Guadeloupe",
      "alpha_2": "GP",
      "alpha_3": "GLP",
      "country_code": "312",
      "iso_3166_2": "ISO 3166-2:GP",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Guam",
      "alpha_2": "GU",
      "alpha_3": "GUM",
      "country_code": "316",
      "iso_3166_2": "ISO 3166-2:GU",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Guatemala",
      "alpha_2": "GT",
      "alpha_3": "GTM",
      "country_code": "320",
      "iso_3166_2": "ISO 3166-2:GT",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Guernsey",
      "alpha_2": "GG",
      "alpha_3": "GGY",
      "country_code": "831",
      "iso_3166_2": "ISO 3166-2:GG",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "Channel Islands",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": "830"
    },
    {
      "name": "Guinea",
      "alpha_2": "GN",
      "alpha_3": "GIN",
      "country_code": "324",
      "iso_3166_2": "ISO 3166-2:GN",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Guinea-Bissau",
      "alpha_2": "GW",
      "alpha_3": "GNB",
      "country_code": "624",
      "iso_3166_2": "ISO 3166-2:GW",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Guyana",
      "alpha_2": "GY",
      "alpha_3": "GUY",
      "country_code": "328",
      "iso_3166_2": "ISO 3166-2:GY",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Haiti",
      "alpha_2": "HT",
      "alpha_3": "HTI",
      "country_code": "332",
      "iso_3166_2": "ISO 3166-2:HT",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Heard Island and McDonald Islands",
      "alpha_2": "HM",
      "alpha_3": "HMD",
      "country_code": "334",
      "iso_3166_2": "ISO 3166-2:HM",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "Holy See",
      "alpha_2": "VA",
      "alpha_3": "VAT",
      "country_code": "336",
      "iso_3166_2": "ISO 3166-2:VA",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Honduras",
      "alpha_2": "HN",
      "alpha_3": "HND",
      "country_code": "340",
      "iso_3166_2": "ISO 3166-2:HN",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Hong Kong",
      "alpha_2": "HK",
      "alpha_3": "HKG",
      "country_code": "344",
      "iso_3166_2": "ISO 3166-2:HK",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Hungary",
      "alpha_2": "HU",
      "alpha_3": "HUN",
      "country_code": "348",
      "iso_3166_2": "ISO 3166-2:HU",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Iceland",
      "alpha_2": "IS",
      "alpha_3": "ISL",
      "country_code": "352",
      "iso_3166_2": "ISO 3166-2:IS",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "India",
      "alpha_2": "IN",
      "alpha_3": "IND",
      "country_code": "356",
      "iso_3166_2": "ISO 3166-2:IN",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Indonesia",
      "alpha_2": "ID",
      "alpha_3": "IDN",
      "country_code": "360",
      "iso_3166_2": "ISO 3166-2:ID",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Iran (Islamic Republic of)",
      "alpha_2": "IR",
      "alpha_3": "IRN",
      "country_code": "364",
      "iso_3166_2": "ISO 3166-2:IR",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Iraq",
      "alpha_2": "IQ",
      "alpha_3": "IRQ",
      "country_code": "368",
      "iso_3166_2": "ISO 3166-2:IQ",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Ireland",
      "alpha_2": "IE",
      "alpha_3": "IRL",
      "country_code": "372",
      "iso_3166_2": "ISO 3166-2:IE",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Isle of Man",
      "alpha_2": "IM",
      "alpha_3": "IMN",
      "country_code": "833",
      "iso_3166_2": "ISO 3166-2:IM",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Israel",
      "alpha_2": "IL",
      "alpha_3": "ISR",
      "country_code": "376",
      "iso_3166_2": "ISO 3166-2:IL",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Italy",
      "alpha_2": "IT",
      "alpha_3": "ITA",
      "country_code": "380",
      "iso_3166_2": "ISO 3166-2:IT",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Jamaica",
      "alpha_2": "JM",
      "alpha_3": "JAM",
      "country_code": "388",
      "iso_3166_2": "ISO 3166-2:JM",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Japan",
      "alpha_2": "JP",
      "alpha_3": "JPN",
      "country_code": "392",
      "iso_3166_2": "ISO 3166-2:JP",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Jersey",
      "alpha_2": "JE",
      "alpha_3": "JEY",
      "country_code": "832",
      "iso_3166_2": "ISO 3166-2:JE",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "Channel Islands",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": "830"
    },
    {
      "name": "Jordan",
      "alpha_2": "JO",
      "alpha_3": "JOR",
      "country_code": "400",
      "iso_3166_2": "ISO 3166-2:JO",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Kazakhstan",
      "alpha_2": "KZ",
      "alpha_3": "KAZ",
      "country_code": "398",
      "iso_3166_2": "ISO 3166-2:KZ",
      "region": "Asia",
      "sub_region": "Central Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "143",
      "intermediate_region_code": ""
    },
    {
      "name": "Kenya",
      "alpha_2": "KE",
      "alpha_3": "KEN",
      "country_code": "404",
      "iso_3166_2": "ISO 3166-2:KE",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Kiribati",
      "alpha_2": "KI",
      "alpha_3": "KIR",
      "country_code": "296",
      "iso_3166_2": "ISO 3166-2:KI",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Korea (Democratic People's Republic of)",
      "alpha_2": "KP",
      "alpha_3": "PRK",
      "country_code": "408",
      "iso_3166_2": "ISO 3166-2:KP",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Korea, Republic of",
      "alpha_2": "KR",
      "alpha_3": "KOR",
      "country_code": "410",
      "iso_3166_2": "ISO 3166-2:KR",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Kuwait",
      "alpha_2": "KW",
      "alpha_3": "KWT",
      "country_code": "414",
      "iso_3166_2": "ISO 3166-2:KW",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Kyrgyzstan",
      "alpha_2": "KG",
      "alpha_3": "KGZ",
      "country_code": "417",
      "iso_3166_2": "ISO 3166-2:KG",
      "region": "Asia",
      "sub_region": "Central Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "143",
      "intermediate_region_code": ""
    },
    {
      "name": "Lao People's Democratic Republic",
      "alpha_2": "LA",
      "alpha_3": "LAO",
      "country_code": "418",
      "iso_3166_2": "ISO 3166-2:LA",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Latvia",
      "alpha_2": "LV",
      "alpha_3": "LVA",
      "country_code": "428",
      "iso_3166_2": "ISO 3166-2:LV",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Lebanon",
      "alpha_2": "LB",
      "alpha_3": "LBN",
      "country_code": "422",
      "iso_3166_2": "ISO 3166-2:LB",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Lesotho",
      "alpha_2": "LS",
      "alpha_3": "LSO",
      "country_code": "426",
      "iso_3166_2": "ISO 3166-2:LS",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Southern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "018"
    },
    {
      "name": "Liberia",
      "alpha_2": "LR",
      "alpha_3": "LBR",
      "country_code": "430",
      "iso_3166_2": "ISO 3166-2:LR",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Libya",
      "alpha_2": "LY",
      "alpha_3": "LBY",
      "country_code": "434",
      "iso_3166_2": "ISO 3166-2:LY",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "Liechtenstein",
      "alpha_2": "LI",
      "alpha_3": "LIE",
      "country_code": "438",
      "iso_3166_2": "ISO 3166-2:LI",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Lithuania",
      "alpha_2": "LT",
      "alpha_3": "LTU",
      "country_code": "440",
      "iso_3166_2": "ISO 3166-2:LT",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Luxembourg",
      "alpha_2": "LU",
      "alpha_3": "LUX",
      "country_code": "442",
      "iso_3166_2": "ISO 3166-2:LU",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Macao",
      "alpha_2": "MO",
      "alpha_3": "MAC",
      "country_code": "446",
      "iso_3166_2": "ISO 3166-2:MO",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Madagascar",
      "alpha_2": "MG",
      "alpha_3": "MDG",
      "country_code": "450",
      "iso_3166_2": "ISO 3166-2:MG",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Malawi",
      "alpha_2": "MW",
      "alpha_3": "MWI",
      "country_code": "454",
      "iso_3166_2": "ISO 3166-2:MW",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Malaysia",
      "alpha_2": "MY",
      "alpha_3": "MYS",
      "country_code": "458",
      "iso_3166_2": "ISO 3166-2:MY",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Maldives",
      "alpha_2": "MV",
      "alpha_3": "MDV",
      "country_code": "462",
      "iso_3166_2": "ISO 3166-2:MV",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Mali",
      "alpha_2": "ML",
      "alpha_3": "MLI",
      "country_code": "466",
      "iso_3166_2": "ISO 3166-2:ML",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Malta",
      "alpha_2": "MT",
      "alpha_3": "MLT",
      "country_code": "470",
      "iso_3166_2": "ISO 3166-2:MT",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Marshall Islands",
      "alpha_2": "MH",
      "alpha_3": "MHL",
      "country_code": "584",
      "iso_3166_2": "ISO 3166-2:MH",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Martinique",
      "alpha_2": "MQ",
      "alpha_3": "MTQ",
      "country_code": "474",
      "iso_3166_2": "ISO 3166-2:MQ",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Mauritania",
      "alpha_2": "MR",
      "alpha_3": "MRT",
      "country_code": "478",
      "iso_3166_2": "ISO 3166-2:MR",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Mauritius",
      "alpha_2": "MU",
      "alpha_3": "MUS",
      "country_code": "480",
      "iso_3166_2": "ISO 3166-2:MU",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Mayotte",
      "alpha_2": "YT",
      "alpha_3": "MYT",
      "country_code": "175",
      "iso_3166_2": "ISO 3166-2:YT",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Mexico",
      "alpha_2": "MX",
      "alpha_3": "MEX",
      "country_code": "484",
      "iso_3166_2": "ISO 3166-2:MX",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Micronesia (Federated States of)",
      "alpha_2": "FM",
      "alpha_3": "FSM",
      "country_code": "583",
      "iso_3166_2": "ISO 3166-2:FM",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Moldova, Republic of",
      "alpha_2": "MD",
      "alpha_3": "MDA",
      "country_code": "498",
      "iso_3166_2": "ISO 3166-2:MD",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Monaco",
      "alpha_2": "MC",
      "alpha_3": "MCO",
      "country_code": "492",
      "iso_3166_2": "ISO 3166-2:MC",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Mongolia",
      "alpha_2": "MN",
      "alpha_3": "MNG",
      "country_code": "496",
      "iso_3166_2": "ISO 3166-2:MN",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Montenegro",
      "alpha_2": "ME",
      "alpha_3": "MNE",
      "country_code": "499",
      "iso_3166_2": "ISO 3166-2:ME",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Montserrat",
      "alpha_2": "MS",
      "alpha_3": "MSR",
      "country_code": "500",
      "iso_3166_2": "ISO 3166-2:MS",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Morocco",
      "alpha_2": "MA",
      "alpha_3": "MAR",
      "country_code": "504",
      "iso_3166_2": "ISO 3166-2:MA",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "Mozambique",
      "alpha_2": "MZ",
      "alpha_3": "MOZ",
      "country_code": "508",
      "iso_3166_2": "ISO 3166-2:MZ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Myanmar",
      "alpha_2": "MM",
      "alpha_3": "MMR",
      "country_code": "104",
      "iso_3166_2": "ISO 3166-2:MM",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Namibia",
      "alpha_2": "NA",
      "alpha_3": "NAM",
      "country_code": "516",
      "iso_3166_2": "ISO 3166-2:NA",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Southern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "018"
    },
    {
      "name": "Nauru",
      "alpha_2": "NR",
      "alpha_3": "NRU",
      "country_code": "520",
      "iso_3166_2": "ISO 3166-2:NR",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Nepal",
      "alpha_2": "NP",
      "alpha_3": "NPL",
      "country_code": "524",
      "iso_3166_2": "ISO 3166-2:NP",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Netherlands",
      "alpha_2": "NL",
      "alpha_3": "NLD",
      "country_code": "528",
      "iso_3166_2": "ISO 3166-2:NL",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "New Caledonia",
      "alpha_2": "NC",
      "alpha_3": "NCL",
      "country_code": "540",
      "iso_3166_2": "ISO 3166-2:NC",
      "region": "Oceania",
      "sub_region": "Melanesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "054",
      "intermediate_region_code": ""
    },
    {
      "name": "New Zealand",
      "alpha_2": "NZ",
      "alpha_3": "NZL",
      "country_code": "554",
      "iso_3166_2": "ISO 3166-2:NZ",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "Nicaragua",
      "alpha_2": "NI",
      "alpha_3": "NIC",
      "country_code": "558",
      "iso_3166_2": "ISO 3166-2:NI",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Niger",
      "alpha_2": "NE",
      "alpha_3": "NER",
      "country_code": "562",
      "iso_3166_2": "ISO 3166-2:NE",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Nigeria",
      "alpha_2": "NG",
      "alpha_3": "NGA",
      "country_code": "566",
      "iso_3166_2": "ISO 3166-2:NG",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Niue",
      "alpha_2": "NU",
      "alpha_3": "NIU",
      "country_code": "570",
      "iso_3166_2": "ISO 3166-2:NU",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Norfolk Island",
      "alpha_2": "NF",
      "alpha_3": "NFK",
      "country_code": "574",
      "iso_3166_2": "ISO 3166-2:NF",
      "region": "Oceania",
      "sub_region": "Australia and New Zealand",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "053",
      "intermediate_region_code": ""
    },
    {
      "name": "North Macedonia",
      "alpha_2": "MK",
      "alpha_3": "MKD",
      "country_code": "807",
      "iso_3166_2": "ISO 3166-2:MK",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Northern Mariana Islands",
      "alpha_2": "MP",
      "alpha_3": "MNP",
      "country_code": "580",
      "iso_3166_2": "ISO 3166-2:MP",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Norway",
      "alpha_2": "NO",
      "alpha_3": "NOR",
      "country_code": "578",
      "iso_3166_2": "ISO 3166-2:NO",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Oman",
      "alpha_2": "OM",
      "alpha_3": "OMN",
      "country_code": "512",
      "iso_3166_2": "ISO 3166-2:OM",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Pakistan",
      "alpha_2": "PK",
      "alpha_3": "PAK",
      "country_code": "586",
      "iso_3166_2": "ISO 3166-2:PK",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Palau",
      "alpha_2": "PW",
      "alpha_3": "PLW",
      "country_code": "585",
      "iso_3166_2": "ISO 3166-2:PW",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Palestine, State of",
      "alpha_2": "PS",
      "alpha_3": "PSE",
      "country_code": "275",
      "iso_3166_2": "ISO 3166-2:PS",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Panama",
      "alpha_2": "PA",
      "alpha_3": "PAN",
      "country_code": "591",
      "iso_3166_2": "ISO 3166-2:PA",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Central America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "013"
    },
    {
      "name": "Papua New Guinea",
      "alpha_2": "PG",
      "alpha_3": "PNG",
      "country_code": "598",
      "iso_3166_2": "ISO 3166-2:PG",
      "region": "Oceania",
      "sub_region": "Melanesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "054",
      "intermediate_region_code": ""
    },
    {
      "name": "Paraguay",
      "alpha_2": "PY",
      "alpha_3": "PRY",
      "country_code": "600",
      "iso_3166_2": "ISO 3166-2:PY",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Peru",
      "alpha_2": "PE",
      "alpha_3": "PER",
      "country_code": "604",
      "iso_3166_2": "ISO 3166-2:PE",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Philippines",
      "alpha_2": "PH",
      "alpha_3": "PHL",
      "country_code": "608",
      "iso_3166_2": "ISO 3166-2:PH",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Pitcairn",
      "alpha_2": "PN",
      "alpha_3": "PCN",
      "country_code": "612",
      "iso_3166_2": "ISO 3166-2:PN",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Poland",
      "alpha_2": "PL",
      "alpha_3": "POL",
      "country_code": "616",
      "iso_3166_2": "ISO 3166-2:PL",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Portugal",
      "alpha_2": "PT",
      "alpha_3": "PRT",
      "country_code": "620",
      "iso_3166_2": "ISO 3166-2:PT",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Puerto Rico",
      "alpha_2": "PR",
      "alpha_3": "PRI",
      "country_code": "630",
      "iso_3166_2": "ISO 3166-2:PR",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Qatar",
      "alpha_2": "QA",
      "alpha_3": "QAT",
      "country_code": "634",
      "iso_3166_2": "ISO 3166-2:QA",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Réunion",
      "alpha_2": "RE",
      "alpha_3": "REU",
      "country_code": "638",
      "iso_3166_2": "ISO 3166-2:RE",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Romania",
      "alpha_2": "RO",
      "alpha_3": "ROU",
      "country_code": "642",
      "iso_3166_2": "ISO 3166-2:RO",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Russian Federation",
      "alpha_2": "RU",
      "alpha_3": "RUS",
      "country_code": "643",
      "iso_3166_2": "ISO 3166-2:RU",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Rwanda",
      "alpha_2": "RW",
      "alpha_3": "RWA",
      "country_code": "646",
      "iso_3166_2": "ISO 3166-2:RW",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Saint Barthélemy",
      "alpha_2": "BL",
      "alpha_3": "BLM",
      "country_code": "652",
      "iso_3166_2": "ISO 3166-2:BL",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Saint Helena, Ascension and Tristan da Cunha",
      "alpha_2": "SH",
      "alpha_3": "SHN",
      "country_code": "654",
      "iso_3166_2": "ISO 3166-2:SH",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Saint Kitts and Nevis",
      "alpha_2": "KN",
      "alpha_3": "KNA",
      "country_code": "659",
      "iso_3166_2": "ISO 3166-2:KN",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Saint Lucia",
      "alpha_2": "LC",
      "alpha_3": "LCA",
      "country_code": "662",
      "iso_3166_2": "ISO 3166-2:LC",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Saint Martin (French part)",
      "alpha_2": "MF",
      "alpha_3": "MAF",
      "country_code": "663",
      "iso_3166_2": "ISO 3166-2:MF",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Saint Pierre and Miquelon",
      "alpha_2": "PM",
      "alpha_3": "SPM",
      "country_code": "666",
      "iso_3166_2": "ISO 3166-2:PM",
      "region": "Americas",
      "sub_region": "Northern America",
      "intermediate_region": "",
      "region_code": "019",
      "sub_region_code": "021",
      "intermediate_region_code": ""
    },
    {
      "name": "Saint Vincent and the Grenadines",
      "alpha_2": "VC",
      "alpha_3": "VCT",
      "country_code": "670",
      "iso_3166_2": "ISO 3166-2:VC",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Samoa",
      "alpha_2": "WS",
      "alpha_3": "WSM",
      "country_code": "882",
      "iso_3166_2": "ISO 3166-2:WS",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "San Marino",
      "alpha_2": "SM",
      "alpha_3": "SMR",
      "country_code": "674",
      "iso_3166_2": "ISO 3166-2:SM",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Sao Tome and Principe",
      "alpha_2": "ST",
      "alpha_3": "STP",
      "country_code": "678",
      "iso_3166_2": "ISO 3166-2:ST",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Middle Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "017"
    },
    {
      "name": "Saudi Arabia",
      "alpha_2": "SA",
      "alpha_3": "SAU",
      "country_code": "682",
      "iso_3166_2": "ISO 3166-2:SA",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Senegal",
      "alpha_2": "SN",
      "alpha_3": "SEN",
      "country_code": "686",
      "iso_3166_2": "ISO 3166-2:SN",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Serbia",
      "alpha_2": "RS",
      "alpha_3": "SRB",
      "country_code": "688",
      "iso_3166_2": "ISO 3166-2:RS",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Seychelles",
      "alpha_2": "SC",
      "alpha_3": "SYC",
      "country_code": "690",
      "iso_3166_2": "ISO 3166-2:SC",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Sierra Leone",
      "alpha_2": "SL",
      "alpha_3": "SLE",
      "country_code": "694",
      "iso_3166_2": "ISO 3166-2:SL",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Singapore",
      "alpha_2": "SG",
      "alpha_3": "SGP",
      "country_code": "702",
      "iso_3166_2": "ISO 3166-2:SG",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Sint Maarten (Dutch part)",
      "alpha_2": "SX",
      "alpha_3": "SXM",
      "country_code": "534",
      "iso_3166_2": "ISO 3166-2:SX",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Slovakia",
      "alpha_2": "SK",
      "alpha_3": "SVK",
      "country_code": "703",
      "iso_3166_2": "ISO 3166-2:SK",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "Slovenia",
      "alpha_2": "SI",
      "alpha_3": "SVN",
      "country_code": "705",
      "iso_3166_2": "ISO 3166-2:SI",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Solomon Islands",
      "alpha_2": "SB",
      "alpha_3": "SLB",
      "country_code": "090",
      "iso_3166_2": "ISO 3166-2:SB",
      "region": "Oceania",
      "sub_region": "Melanesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "054",
      "intermediate_region_code": ""
    },
    {
      "name": "Somalia",
      "alpha_2": "SO",
      "alpha_3": "SOM",
      "country_code": "706",
      "iso_3166_2": "ISO 3166-2:SO",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "South Africa",
      "alpha_2": "ZA",
      "alpha_3": "ZAF",
      "country_code": "710",
      "iso_3166_2": "ISO 3166-2:ZA",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Southern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "018"
    },
    {
      "name": "South Georgia and the South Sandwich Islands",
      "alpha_2": "GS",
      "alpha_3": "SGS",
      "country_code": "239",
      "iso_3166_2": "ISO 3166-2:GS",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "South Sudan",
      "alpha_2": "SS",
      "alpha_3": "SSD",
      "country_code": "728",
      "iso_3166_2": "ISO 3166-2:SS",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Spain",
      "alpha_2": "ES",
      "alpha_3": "ESP",
      "country_code": "724",
      "iso_3166_2": "ISO 3166-2:ES",
      "region": "Europe",
      "sub_region": "Southern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "039",
      "intermediate_region_code": ""
    },
    {
      "name": "Sri Lanka",
      "alpha_2": "LK",
      "alpha_3": "LKA",
      "country_code": "144",
      "iso_3166_2": "ISO 3166-2:LK",
      "region": "Asia",
      "sub_region": "Southern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "034",
      "intermediate_region_code": ""
    },
    {
      "name": "Sudan",
      "alpha_2": "SD",
      "alpha_3": "SDN",
      "country_code": "729",
      "iso_3166_2": "ISO 3166-2:SD",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "Suriname",
      "alpha_2": "SR",
      "alpha_3": "SUR",
      "country_code": "740",
      "iso_3166_2": "ISO 3166-2:SR",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Svalbard and Jan Mayen",
      "alpha_2": "SJ",
      "alpha_3": "SJM",
      "country_code": "744",
      "iso_3166_2": "ISO 3166-2:SJ",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Sweden",
      "alpha_2": "SE",
      "alpha_3": "SWE",
      "country_code": "752",
      "iso_3166_2": "ISO 3166-2:SE",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "Switzerland",
      "alpha_2": "CH",
      "alpha_3": "CHE",
      "country_code": "756",
      "iso_3166_2": "ISO 3166-2:CH",
      "region": "Europe",
      "sub_region": "Western Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "155",
      "intermediate_region_code": ""
    },
    {
      "name": "Syrian Arab Republic",
      "alpha_2": "SY",
      "alpha_3": "SYR",
      "country_code": "760",
      "iso_3166_2": "ISO 3166-2:SY",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Taiwan, Province of China",
      "alpha_2": "TW",
      "alpha_3": "TWN",
      "country_code": "158",
      "iso_3166_2": "ISO 3166-2:TW",
      "region": "Asia",
      "sub_region": "Eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "030",
      "intermediate_region_code": ""
    },
    {
      "name": "Tajikistan",
      "alpha_2": "TJ",
      "alpha_3": "TJK",
      "country_code": "762",
      "iso_3166_2": "ISO 3166-2:TJ",
      "region": "Asia",
      "sub_region": "Central Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "143",
      "intermediate_region_code": ""
    },
    {
      "name": "Tanzania, United Republic of",
      "alpha_2": "TZ",
      "alpha_3": "TZA",
      "country_code": "834",
      "iso_3166_2": "ISO 3166-2:TZ",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Thailand",
      "alpha_2": "TH",
      "alpha_3": "THA",
      "country_code": "764",
      "iso_3166_2": "ISO 3166-2:TH",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Timor-Leste",
      "alpha_2": "TL",
      "alpha_3": "TLS",
      "country_code": "626",
      "iso_3166_2": "ISO 3166-2:TL",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Togo",
      "alpha_2": "TG",
      "alpha_3": "TGO",
      "country_code": "768",
      "iso_3166_2": "ISO 3166-2:TG",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Western Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "011"
    },
    {
      "name": "Tokelau",
      "alpha_2": "TK",
      "alpha_3": "TKL",
      "country_code": "772",
      "iso_3166_2": "ISO 3166-2:TK",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Tonga",
      "alpha_2": "TO",
      "alpha_3": "TON",
      "country_code": "776",
      "iso_3166_2": "ISO 3166-2:TO",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Trinidad and Tobago",
      "alpha_2": "TT",
      "alpha_3": "TTO",
      "country_code": "780",
      "iso_3166_2": "ISO 3166-2:TT",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Tunisia",
      "alpha_2": "TN",
      "alpha_3": "TUN",
      "country_code": "788",
      "iso_3166_2": "ISO 3166-2:TN",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "Turkey",
      "alpha_2": "TR",
      "alpha_3": "TUR",
      "country_code": "792",
      "iso_3166_2": "ISO 3166-2:TR",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Turkmenistan",
      "alpha_2": "TM",
      "alpha_3": "TKM",
      "country_code": "795",
      "iso_3166_2": "ISO 3166-2:TM",
      "region": "Asia",
      "sub_region": "Central Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "143",
      "intermediate_region_code": ""
    },
    {
      "name": "Turks and Caicos Islands",
      "alpha_2": "TC",
      "alpha_3": "TCA",
      "country_code": "796",
      "iso_3166_2": "ISO 3166-2:TC",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Tuvalu",
      "alpha_2": "TV",
      "alpha_3": "TUV",
      "country_code": "798",
      "iso_3166_2": "ISO 3166-2:TV",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Uganda",
      "alpha_2": "UG",
      "alpha_3": "UGA",
      "country_code": "800",
      "iso_3166_2": "ISO 3166-2:UG",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Ukraine",
      "alpha_2": "UA",
      "alpha_3": "UKR",
      "country_code": "804",
      "iso_3166_2": "ISO 3166-2:UA",
      "region": "Europe",
      "sub_region": "Eastern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "151",
      "intermediate_region_code": ""
    },
    {
      "name": "United Arab Emirates",
      "alpha_2": "AE",
      "alpha_3": "ARE",
      "country_code": "784",
      "iso_3166_2": "ISO 3166-2:AE",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "United Kingdom of Great Britain and Northern Ireland",
      "alpha_2": "GB",
      "alpha_3": "GBR",
      "country_code": "826",
      "iso_3166_2": "ISO 3166-2:GB",
      "region": "Europe",
      "sub_region": "Northern Europe",
      "intermediate_region": "",
      "region_code": "150",
      "sub_region_code": "154",
      "intermediate_region_code": ""
    },
    {
      "name": "United States of America",
      "alpha_2": "US",
      "alpha_3": "USA",
      "country_code": "840",
      "iso_3166_2": "ISO 3166-2:US",
      "region": "Americas",
      "sub_region": "Northern America",
      "intermediate_region": "",
      "region_code": "019",
      "sub_region_code": "021",
      "intermediate_region_code": ""
    },
    {
      "name": "United States Minor Outlying Islands",
      "alpha_2": "UM",
      "alpha_3": "UMI",
      "country_code": "581",
      "iso_3166_2": "ISO 3166-2:UM",
      "region": "Oceania",
      "sub_region": "Micronesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "057",
      "intermediate_region_code": ""
    },
    {
      "name": "Uruguay",
      "alpha_2": "UY",
      "alpha_3": "URY",
      "country_code": "858",
      "iso_3166_2": "ISO 3166-2:UY",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Uzbekistan",
      "alpha_2": "UZ",
      "alpha_3": "UZB",
      "country_code": "860",
      "iso_3166_2": "ISO 3166-2:UZ",
      "region": "Asia",
      "sub_region": "Central Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "143",
      "intermediate_region_code": ""
    },
    {
      "name": "Vanuatu",
      "alpha_2": "VU",
      "alpha_3": "VUT",
      "country_code": "548",
      "iso_3166_2": "ISO 3166-2:VU",
      "region": "Oceania",
      "sub_region": "Melanesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "054",
      "intermediate_region_code": ""
    },
    {
      "name": "Venezuela (Bolivarian Republic of)",
      "alpha_2": "VE",
      "alpha_3": "VEN",
      "country_code": "862",
      "iso_3166_2": "ISO 3166-2:VE",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "South America",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "005"
    },
    {
      "name": "Viet Nam",
      "alpha_2": "VN",
      "alpha_3": "VNM",
      "country_code": "704",
      "iso_3166_2": "ISO 3166-2:VN",
      "region": "Asia",
      "sub_region": "South-eastern Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "035",
      "intermediate_region_code": ""
    },
    {
      "name": "Virgin Islands (British)",
      "alpha_2": "VG",
      "alpha_3": "VGB",
      "country_code": "092",
      "iso_3166_2": "ISO 3166-2:VG",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Virgin Islands (U.S.)",
      "alpha_2": "VI",
      "alpha_3": "VIR",
      "country_code": "850",
      "iso_3166_2": "ISO 3166-2:VI",
      "region": "Americas",
      "sub_region": "Latin America and the Caribbean",
      "intermediate_region": "Caribbean",
      "region_code": "019",
      "sub_region_code": "419",
      "intermediate_region_code": "029"
    },
    {
      "name": "Wallis and Futuna",
      "alpha_2": "WF",
      "alpha_3": "WLF",
      "country_code": "876",
      "iso_3166_2": "ISO 3166-2:WF",
      "region": "Oceania",
      "sub_region": "Polynesia",
      "intermediate_region": "",
      "region_code": "009",
      "sub_region_code": "061",
      "intermediate_region_code": ""
    },
    {
      "name": "Western Sahara",
      "alpha_2": "EH",
      "alpha_3": "ESH",
      "country_code": "732",
      "iso_3166_2": "ISO 3166-2:EH",
      "region": "Africa",
      "sub_region": "Northern Africa",
      "intermediate_region": "",
      "region_code": "002",
      "sub_region_code": "015",
      "intermediate_region_code": ""
    },
    {
      "name": "Yemen",
      "alpha_2": "YE",
      "alpha_3": "YEM",
      "country_code": "887",
      "iso_3166_2": "ISO 3166-2:YE",
      "region": "Asia",
      "sub_region": "Western Asia",
      "intermediate_region": "",
      "region_code": "142",
      "sub_region_code": "145",
      "intermediate_region_code": ""
    },
    {
      "name": "Zambia",
      "alpha_2": "ZM",
      "alpha_3": "ZMB",
      "country_code": "894",
      "iso_3166_2": "ISO 3166-2:ZM",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    },
    {
      "name": "Zimbabwe",
      "alpha_2": "ZW",
      "alpha_3": "ZWE",
      "country_code": "716",
      "iso_3166_2": "ISO 3166-2:ZW",
      "region": "Africa",
      "sub_region": "Sub-Saharan Africa",
      "intermediate_region": "Eastern Africa",
      "region_code": "002",
      "sub_region_code": "202",
      "intermediate_region_code": "014"
    }
  ]
}

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 
     last-modified: Wed,21 May 2025 10:51:36 GMT 

- Responses
**Code**            **Description**             **Links**
200                                             No links


24. **GET - /api/v1/invoice/resources/invoice-types - GetInvoiceTypes**

### GetInvoiceTypes

- Parameters
**Name**                    **Description**
No parameters

- Responses
    - Curl
    curl -X 'GET' \
      'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/invoice-types' \
      -H 'accept: */*'
    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/invoice-types

- Server response
        **Code**	            **Details**
        200

    - Response body
    {
  "code": 200,
  "data": [
    {
      "code": "380",
      "value": "Credit Note"
    },
    {
      "code": "381",
      "value": "Commercial Invoice"
    },
    {
      "code": "384",
      "value": "Debit Note"
    },
    {
      "code": "385",
      "value": "Self Billed Invoice"
    },
    {
      "code": "386",
      "value": "Factored Invoice"
    },
    {
      "code": "388",
      "value": "Statement of Account"
    },
    {
      "code": "389",
      "value": "Purchase Order"
    },
    {
      "code": "390",
      "value": "Proforma Invoice"
    },
    {
      "code": "392",
      "value": "Consignment Invoice"
    },
    {
      "code": "393",
      "value": "Self-billed Credit Note"
    },
    {
      "code": "394",
      "value": "Self-billed Invoice"
    },
    {
      "code": "395",
      "value": "Credit Note Request"
    },
    {
      "code": "396",
      "value": "Invoice Request"
    },
    {
      "code": "397",
      "value": "Final Settlement"
    },
    {
      "code": "399",
      "value": "Bill of Lading"
    },
    {
      "code": "400",
      "value": "Waybill"
    },
    {
      "code": "402",
      "value": "Shipping Instructions"
    },
    {
      "code": "404",
      "value": "Certificate of Origin"
    },
    {
      "code": "406",
      "value": "Customs Declaration"
    },
    {
      "code": "408",
      "value": "Packing List"
    }
  ]
}

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 
     last-modified: Wed,21 May 2025 11:11:51 GMT 

- Responses
**Code**            **Description**             **Links**
200 


25. **GET - /api/v1/invoice/resources/currencies - GetCurrencies**

### GetCurrencies

- Parameters
**Name**                    **Description**
No parameters

- Responses
    - Curl
    curl -X 'GET' \
  'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/currencies' \
  -H 'accept: */*'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/currencies

- Server response
        **Code**	            **Details**
        200

    - Response body
    {
  "code": 200,
  "data": [
    {
      "symbol": "$",
      "name": "US Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "USD",
      "name_plural": "US dollars"
    },
    {
      "symbol": "CA$",
      "name": "Canadian Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "CAD",
      "name_plural": "Canadian dollars"
    },
    {
      "symbol": "€",
      "name": "Euro",
      "symbol_native": "€",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "EUR",
      "name_plural": "euros"
    },
    {
      "symbol": "AED",
      "name": "United Arab Emirates Dirham",
      "symbol_native": "د.إ.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "AED",
      "name_plural": "UAE dirhams"
    },
    {
      "symbol": "Af",
      "name": "Afghan Afghani",
      "symbol_native": "؋",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "AFN",
      "name_plural": "Afghan Afghanis"
    },
    {
      "symbol": "ALL",
      "name": "Albanian Lek",
      "symbol_native": "Lek",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "ALL",
      "name_plural": "Albanian lekë"
    },
    {
      "symbol": "AMD",
      "name": "Armenian Dram",
      "symbol_native": "դր.",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "AMD",
      "name_plural": "Armenian drams"
    },
    {
      "symbol": "AR$",
      "name": "Argentine Peso",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "ARS",
      "name_plural": "Argentine pesos"
    },
    {
      "symbol": "AU$",
      "name": "Australian Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "AUD",
      "name_plural": "Australian dollars"
    },
    {
      "symbol": "man.",
      "name": "Azerbaijani Manat",
      "symbol_native": "ман.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "AZN",
      "name_plural": "Azerbaijani manats"
    },
    {
      "symbol": "KM",
      "name": "Bosnia-Herzegovina Convertible Mark",
      "symbol_native": "KM",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BAM",
      "name_plural": "Bosnia-Herzegovina convertible marks"
    },
    {
      "symbol": "Tk",
      "name": "Bangladeshi Taka",
      "symbol_native": "৳",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BDT",
      "name_plural": "Bangladeshi takas"
    },
    {
      "symbol": "BGN",
      "name": "Bulgarian Lev",
      "symbol_native": "лв.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BGN",
      "name_plural": "Bulgarian leva"
    },
    {
      "symbol": "BD",
      "name": "Bahraini Dinar",
      "symbol_native": "د.ب.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "BHD",
      "name_plural": "Bahraini dinars"
    },
    {
      "symbol": "FBu",
      "name": "Burundian Franc",
      "symbol_native": "FBu",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "BIF",
      "name_plural": "Burundian francs"
    },
    {
      "symbol": "BN$",
      "name": "Brunei Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BND",
      "name_plural": "Brunei dollars"
    },
    {
      "symbol": "Bs",
      "name": "Bolivian Boliviano",
      "symbol_native": "Bs",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BOB",
      "name_plural": "Bolivian bolivianos"
    },
    {
      "symbol": "R$",
      "name": "Brazilian Real",
      "symbol_native": "R$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BRL",
      "name_plural": "Brazilian reals"
    },
    {
      "symbol": "BWP",
      "name": "Botswanan Pula",
      "symbol_native": "P",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BWP",
      "name_plural": "Botswanan pulas"
    },
    {
      "symbol": "BYR",
      "name": "Belarusian Ruble",
      "symbol_native": "BYR",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "BYR",
      "name_plural": "Belarusian rubles"
    },
    {
      "symbol": "BZ$",
      "name": "Belize Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "BZD",
      "name_plural": "Belize dollars"
    },
    {
      "symbol": "CDF",
      "name": "Congolese Franc",
      "symbol_native": "FrCD",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "CDF",
      "name_plural": "Congolese francs"
    },
    {
      "symbol": "CHF",
      "name": "Swiss Franc",
      "symbol_native": "CHF",
      "decimal_digits": 2,
      "rounding": 0.05,
      "code": "CHF",
      "name_plural": "Swiss francs"
    },
    {
      "symbol": "CL$",
      "name": "Chilean Peso",
      "symbol_native": "$",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "CLP",
      "name_plural": "Chilean pesos"
    },
    {
      "symbol": "CN¥",
      "name": "Chinese Yuan",
      "symbol_native": "CN¥",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "CNY",
      "name_plural": "Chinese yuan"
    },
    {
      "symbol": "CO$",
      "name": "Colombian Peso",
      "symbol_native": "$",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "COP",
      "name_plural": "Colombian pesos"
    },
    {
      "symbol": "₡",
      "name": "Costa Rican Colón",
      "symbol_native": "₡",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "CRC",
      "name_plural": "Costa Rican colóns"
    },
    {
      "symbol": "CV$",
      "name": "Cape Verdean Escudo",
      "symbol_native": "CV$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "CVE",
      "name_plural": "Cape Verdean escudos"
    },
    {
      "symbol": "Kč",
      "name": "Czech Republic Koruna",
      "symbol_native": "Kč",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "CZK",
      "name_plural": "Czech Republic korunas"
    },
    {
      "symbol": "Fdj",
      "name": "Djiboutian Franc",
      "symbol_native": "Fdj",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "DJF",
      "name_plural": "Djiboutian francs"
    },
    {
      "symbol": "Dkr",
      "name": "Danish Krone",
      "symbol_native": "kr",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "DKK",
      "name_plural": "Danish kroner"
    },
    {
      "symbol": "RD$",
      "name": "Dominican Peso",
      "symbol_native": "RD$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "DOP",
      "name_plural": "Dominican pesos"
    },
    {
      "symbol": "DA",
      "name": "Algerian Dinar",
      "symbol_native": "د.ج.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "DZD",
      "name_plural": "Algerian dinars"
    },
    {
      "symbol": "Ekr",
      "name": "Estonian Kroon",
      "symbol_native": "kr",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "EEK",
      "name_plural": "Estonian kroons"
    },
    {
      "symbol": "EGP",
      "name": "Egyptian Pound",
      "symbol_native": "ج.م.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "EGP",
      "name_plural": "Egyptian pounds"
    },
    {
      "symbol": "Nfk",
      "name": "Eritrean Nakfa",
      "symbol_native": "Nfk",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "ERN",
      "name_plural": "Eritrean nakfas"
    },
    {
      "symbol": "Br",
      "name": "Ethiopian Birr",
      "symbol_native": "Br",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "ETB",
      "name_plural": "Ethiopian birrs"
    },
    {
      "symbol": "£",
      "name": "British Pound Sterling",
      "symbol_native": "£",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "GBP",
      "name_plural": "British pounds sterling"
    },
    {
      "symbol": "GEL",
      "name": "Georgian Lari",
      "symbol_native": "GEL",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "GEL",
      "name_plural": "Georgian laris"
    },
    {
      "symbol": "GH₵",
      "name": "Ghanaian Cedi",
      "symbol_native": "GH₵",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "GHS",
      "name_plural": "Ghanaian cedis"
    },
    {
      "symbol": "FG",
      "name": "Guinean Franc",
      "symbol_native": "FG",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "GNF",
      "name_plural": "Guinean francs"
    },
    {
      "symbol": "GTQ",
      "name": "Guatemalan Quetzal",
      "symbol_native": "Q",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "GTQ",
      "name_plural": "Guatemalan quetzals"
    },
    {
      "symbol": "HK$",
      "name": "Hong Kong Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "HKD",
      "name_plural": "Hong Kong dollars"
    },
    {
      "symbol": "HNL",
      "name": "Honduran Lempira",
      "symbol_native": "L",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "HNL",
      "name_plural": "Honduran lempiras"
    },
    {
      "symbol": "kn",
      "name": "Croatian Kuna",
      "symbol_native": "kn",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "HRK",
      "name_plural": "Croatian kunas"
    },
    {
      "symbol": "Ft",
      "name": "Hungarian Forint",
      "symbol_native": "Ft",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "HUF",
      "name_plural": "Hungarian forints"
    },
    {
      "symbol": "Rp",
      "name": "Indonesian Rupiah",
      "symbol_native": "Rp",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "IDR",
      "name_plural": "Indonesian rupiahs"
    },
    {
      "symbol": "₪",
      "name": "Israeli New Sheqel",
      "symbol_native": "₪",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "ILS",
      "name_plural": "Israeli new sheqels"
    },
    {
      "symbol": "Rs",
      "name": "Indian Rupee",
      "symbol_native": "টকা",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "INR",
      "name_plural": "Indian rupees"
    },
    {
      "symbol": "IQD",
      "name": "Iraqi Dinar",
      "symbol_native": "د.ع.‏",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "IQD",
      "name_plural": "Iraqi dinars"
    },
    {
      "symbol": "IRR",
      "name": "Iranian Rial",
      "symbol_native": "﷼",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "IRR",
      "name_plural": "Iranian rials"
    },
    {
      "symbol": "Ikr",
      "name": "Icelandic Króna",
      "symbol_native": "kr",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "ISK",
      "name_plural": "Icelandic krónur"
    },
    {
      "symbol": "J$",
      "name": "Jamaican Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "JMD",
      "name_plural": "Jamaican dollars"
    },
    {
      "symbol": "JD",
      "name": "Jordanian Dinar",
      "symbol_native": "د.أ.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "JOD",
      "name_plural": "Jordanian dinars"
    },
    {
      "symbol": "¥",
      "name": "Japanese Yen",
      "symbol_native": "￥",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "JPY",
      "name_plural": "Japanese yen"
    },
    {
      "symbol": "Ksh",
      "name": "Kenyan Shilling",
      "symbol_native": "Ksh",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "KES",
      "name_plural": "Kenyan shillings"
    },
    {
      "symbol": "KHR",
      "name": "Cambodian Riel",
      "symbol_native": "៛",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "KHR",
      "name_plural": "Cambodian riels"
    },
    {
      "symbol": "CF",
      "name": "Comorian Franc",
      "symbol_native": "FC",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "KMF",
      "name_plural": "Comorian francs"
    },
    {
      "symbol": "₩",
      "name": "South Korean Won",
      "symbol_native": "₩",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "KRW",
      "name_plural": "South Korean won"
    },
    {
      "symbol": "KD",
      "name": "Kuwaiti Dinar",
      "symbol_native": "د.ك.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "KWD",
      "name_plural": "Kuwaiti dinars"
    },
    {
      "symbol": "KZT",
      "name": "Kazakhstani Tenge",
      "symbol_native": "тңг.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "KZT",
      "name_plural": "Kazakhstani tenges"
    },
    {
      "symbol": "LB£",
      "name": "Lebanese Pound",
      "symbol_native": "ل.ل.‏",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "LBP",
      "name_plural": "Lebanese pounds"
    },
    {
      "symbol": "SLRs",
      "name": "Sri Lankan Rupee",
      "symbol_native": "SL Re",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "LKR",
      "name_plural": "Sri Lankan rupees"
    },
    {
      "symbol": "Lt",
      "name": "Lithuanian Litas",
      "symbol_native": "Lt",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "LTL",
      "name_plural": "Lithuanian litai"
    },
    {
      "symbol": "Ls",
      "name": "Latvian Lats",
      "symbol_native": "Ls",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "LVL",
      "name_plural": "Latvian lati"
    },
    {
      "symbol": "LD",
      "name": "Libyan Dinar",
      "symbol_native": "د.ل.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "LYD",
      "name_plural": "Libyan dinars"
    },
    {
      "symbol": "MAD",
      "name": "Moroccan Dirham",
      "symbol_native": "د.م.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MAD",
      "name_plural": "Moroccan dirhams"
    },
    {
      "symbol": "MDL",
      "name": "Moldovan Leu",
      "symbol_native": "MDL",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MDL",
      "name_plural": "Moldovan lei"
    },
    {
      "symbol": "MGA",
      "name": "Malagasy Ariary",
      "symbol_native": "MGA",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "MGA",
      "name_plural": "Malagasy Ariaries"
    },
    {
      "symbol": "MKD",
      "name": "Macedonian Denar",
      "symbol_native": "MKD",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MKD",
      "name_plural": "Macedonian denari"
    },
    {
      "symbol": "MMK",
      "name": "Myanma Kyat",
      "symbol_native": "K",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "MMK",
      "name_plural": "Myanma kyats"
    },
    {
      "symbol": "MOP$",
      "name": "Macanese Pataca",
      "symbol_native": "MOP$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MOP",
      "name_plural": "Macanese patacas"
    },
    {
      "symbol": "MURs",
      "name": "Mauritian Rupee",
      "symbol_native": "MURs",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "MUR",
      "name_plural": "Mauritian rupees"
    },
    {
      "symbol": "MX$",
      "name": "Mexican Peso",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MXN",
      "name_plural": "Mexican pesos"
    },
    {
      "symbol": "RM",
      "name": "Malaysian Ringgit",
      "symbol_native": "RM",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MYR",
      "name_plural": "Malaysian ringgits"
    },
    {
      "symbol": "MTn",
      "name": "Mozambican Metical",
      "symbol_native": "MTn",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "MZN",
      "name_plural": "Mozambican meticals"
    },
    {
      "symbol": "N$",
      "name": "Namibian Dollar",
      "symbol_native": "N$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NAD",
      "name_plural": "Namibian dollars"
    },
    {
      "symbol": "₦",
      "name": "Nigerian Naira",
      "symbol_native": "₦",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NGN",
      "name_plural": "Nigerian nairas"
    },
    {
      "symbol": "C$",
      "name": "Nicaraguan Córdoba",
      "symbol_native": "C$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NIO",
      "name_plural": "Nicaraguan córdobas"
    },
    {
      "symbol": "Nkr",
      "name": "Norwegian Krone",
      "symbol_native": "kr",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NOK",
      "name_plural": "Norwegian kroner"
    },
    {
      "symbol": "NPRs",
      "name": "Nepalese Rupee",
      "symbol_native": "नेरू",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NPR",
      "name_plural": "Nepalese rupees"
    },
    {
      "symbol": "NZ$",
      "name": "New Zealand Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "NZD",
      "name_plural": "New Zealand dollars"
    },
    {
      "symbol": "OMR",
      "name": "Omani Rial",
      "symbol_native": "ر.ع.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "OMR",
      "name_plural": "Omani rials"
    },
    {
      "symbol": "B/.",
      "name": "Panamanian Balboa",
      "symbol_native": "B/.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "PAB",
      "name_plural": "Panamanian balboas"
    },
    {
      "symbol": "S/.",
      "name": "Peruvian Nuevo Sol",
      "symbol_native": "S/.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "PEN",
      "name_plural": "Peruvian nuevos soles"
    },
    {
      "symbol": "₱",
      "name": "Philippine Peso",
      "symbol_native": "₱",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "PHP",
      "name_plural": "Philippine pesos"
    },
    {
      "symbol": "PKRs",
      "name": "Pakistani Rupee",
      "symbol_native": "₨",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "PKR",
      "name_plural": "Pakistani rupees"
    },
    {
      "symbol": "zł",
      "name": "Polish Zloty",
      "symbol_native": "zł",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "PLN",
      "name_plural": "Polish zlotys"
    },
    {
      "symbol": "₲",
      "name": "Paraguayan Guarani",
      "symbol_native": "₲",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "PYG",
      "name_plural": "Paraguayan guaranis"
    },
    {
      "symbol": "QR",
      "name": "Qatari Rial",
      "symbol_native": "ر.ق.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "QAR",
      "name_plural": "Qatari rials"
    },
    {
      "symbol": "RON",
      "name": "Romanian Leu",
      "symbol_native": "RON",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "RON",
      "name_plural": "Romanian lei"
    },
    {
      "symbol": "din.",
      "name": "Serbian Dinar",
      "symbol_native": "дин.",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "RSD",
      "name_plural": "Serbian dinars"
    },
    {
      "symbol": "RUB",
      "name": "Russian Ruble",
      "symbol_native": "руб.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "RUB",
      "name_plural": "Russian rubles"
    },
    {
      "symbol": "RWF",
      "name": "Rwandan Franc",
      "symbol_native": "FR",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "RWF",
      "name_plural": "Rwandan francs"
    },
    {
      "symbol": "SR",
      "name": "Saudi Riyal",
      "symbol_native": "ر.س.‏",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "SAR",
      "name_plural": "Saudi riyals"
    },
    {
      "symbol": "SDG",
      "name": "Sudanese Pound",
      "symbol_native": "SDG",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "SDG",
      "name_plural": "Sudanese pounds"
    },
    {
      "symbol": "Skr",
      "name": "Swedish Krona",
      "symbol_native": "kr",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "SEK",
      "name_plural": "Swedish kronor"
    },
    {
      "symbol": "S$",
      "name": "Singapore Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "SGD",
      "name_plural": "Singapore dollars"
    },
    {
      "symbol": "Ssh",
      "name": "Somali Shilling",
      "symbol_native": "Ssh",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "SOS",
      "name_plural": "Somali shillings"
    },
    {
      "symbol": "SY£",
      "name": "Syrian Pound",
      "symbol_native": "ل.س.‏",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "SYP",
      "name_plural": "Syrian pounds"
    },
    {
      "symbol": "฿",
      "name": "Thai Baht",
      "symbol_native": "฿",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "THB",
      "name_plural": "Thai baht"
    },
    {
      "symbol": "DT",
      "name": "Tunisian Dinar",
      "symbol_native": "د.ت.‏",
      "decimal_digits": 3,
      "rounding": 0,
      "code": "TND",
      "name_plural": "Tunisian dinars"
    },
    {
      "symbol": "T$",
      "name": "Tongan Paʻanga",
      "symbol_native": "T$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "TOP",
      "name_plural": "Tongan paʻanga"
    },
    {
      "symbol": "TL",
      "name": "Turkish Lira",
      "symbol_native": "TL",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "TRY",
      "name_plural": "Turkish Lira"
    },
    {
      "symbol": "TT$",
      "name": "Trinidad and Tobago Dollar",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "TTD",
      "name_plural": "Trinidad and Tobago dollars"
    },
    {
      "symbol": "NT$",
      "name": "New Taiwan Dollar",
      "symbol_native": "NT$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "TWD",
      "name_plural": "New Taiwan dollars"
    },
    {
      "symbol": "TSh",
      "name": "Tanzanian Shilling",
      "symbol_native": "TSh",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "TZS",
      "name_plural": "Tanzanian shillings"
    },
    {
      "symbol": "₴",
      "name": "Ukrainian Hryvnia",
      "symbol_native": "₴",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "UAH",
      "name_plural": "Ukrainian hryvnias"
    },
    {
      "symbol": "USh",
      "name": "Ugandan Shilling",
      "symbol_native": "USh",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "UGX",
      "name_plural": "Ugandan shillings"
    },
    {
      "symbol": "$U",
      "name": "Uruguayan Peso",
      "symbol_native": "$",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "UYU",
      "name_plural": "Uruguayan pesos"
    },
    {
      "symbol": "UZS",
      "name": "Uzbekistan Som",
      "symbol_native": "UZS",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "UZS",
      "name_plural": "Uzbekistan som"
    },
    {
      "symbol": "Bs.F.",
      "name": "Venezuelan Bolívar",
      "symbol_native": "Bs.F.",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "VEF",
      "name_plural": "Venezuelan bolívars"
    },
    {
      "symbol": "₫",
      "name": "Vietnamese Dong",
      "symbol_native": "₫",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "VND",
      "name_plural": "Vietnamese dong"
    },
    {
      "symbol": "FCFA",
      "name": "CFA Franc BEAC",
      "symbol_native": "FCFA",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "XAF",
      "name_plural": "CFA francs BEAC"
    },
    {
      "symbol": "CFA",
      "name": "CFA Franc BCEAO",
      "symbol_native": "CFA",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "XOF",
      "name_plural": "CFA francs BCEAO"
    },
    {
      "symbol": "YR",
      "name": "Yemeni Rial",
      "symbol_native": "ر.ي.‏",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "YER",
      "name_plural": "Yemeni rials"
    },
    {
      "symbol": "R",
      "name": "South African Rand",
      "symbol_native": "R",
      "decimal_digits": 2,
      "rounding": 0,
      "code": "ZAR",
      "name_plural": "South African rand"
    },
    {
      "symbol": "ZK",
      "name": "Zambian Kwacha",
      "symbol_native": "ZK",
      "decimal_digits": 0,
      "rounding": 0,
      "code": "ZMK",
      "name_plural": "Zambian kwachas"
    }
  ]
}

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 
     last-modified: Wed,21 May 2025 11:22:27 GMT 

- Responses
**Code**            **Description**             **Links**
200


26. **GET - /api/v1/invoice/resources/vat-exemptions - GetVatExemptions**

### GetVatExemptions

- Parameters
**Name**                    **Description**
No parameters

- Responses
    - Curl
    curl -X 'GET' \
  'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/vat-exemptions' \
  -H 'accept: */*'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/vat-exemptions

- Server response
        **Code**	            **Details**
        200

    - Response body
    {
  "code": 200,
  "data": [
    {
      "heading_no": "29.15",
      "harmonized_system_code": "2915.3100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ethyl acetate",
      "description": "Saturated acyclic monocarboxylic acids and their derivatives."
    },
    {
      "heading_no": "29.16",
      "harmonized_system_code": "2916.3900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "unsaturated Acyclic monocarboxylic acids"
    },
    {
      "heading_no": "29.24",
      "harmonized_system_code": "2924.2900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Other",
      "description": "Carboxyamide function compounds"
    },
    {
      "heading_no": "29.28",
      "harmonized_system_code": "2928.0000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Organic derivatives of hydrazine or hydroxylamide",
      "description": "Carboxyamide function compounds"
    },
    {
      "heading_no": "29.33",
      "harmonized_system_code": "2933.1100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Phenazone and its derivatives",
      "description": "Heterocyclic Compounds with nitrogen hetero-atoms(s) only"
    },
    {
      "heading_no": "29.33",
      "harmonized_system_code": "2933.1900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Hydation and its derivatives",
      "description": "Heterocyclic Compounds with nitrogen hetero-atoms(s) only"
    },
    {
      "heading_no": "29.33",
      "harmonized_system_code": "2933.2900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Heterocyclic Compounds with nitrogen hetero-atoms(s) only"
    },
    {
      "heading_no": "29.33",
      "harmonized_system_code": "2933.4000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Compounds containing a quinoline or is quinoline ring system",
      "description": "Heterocyclic Compounds with nitrogen hetero-atoms(s) only"
    },
    {
      "heading_no": "29.35",
      "harmonized_system_code": "2935.0000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Sulphonamides",
      "description": "Heterocyclic Compounds with nitrogen hetero-atoms(s) only"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.2100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Quinine and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.2900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.3000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Caffeine and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.4100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ephedrine and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.6100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ergometrin (INN) and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.6200",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ergotamine (INN) and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.39",
      "harmonized_system_code": "2939.7000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Nicotine and its salts",
      "description": "Vegetable alkaloids, natural or reproduced by synthesis"
    },
    {
      "heading_no": "29.41",
      "harmonized_system_code": "2941.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "penicillins and their derivatives with a penicillanic acid structure; salts thereof",
      "description": "Antibiotics"
    },
    {
      "heading_no": "29.41",
      "harmonized_system_code": "2941.3000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Tetracycline and their derivatives; Salts thereof",
      "description": "Antibiotics"
    },
    {
      "heading_no": "29.41",
      "harmonized_system_code": "2941.4000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Chloramphenicol and its derivatives; salts thereof",
      "description": "Antibiotics"
    },
    {
      "heading_no": "29.41",
      "harmonized_system_code": "2941.9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Antibiotics"
    },
    {
      "heading_no": "30.01",
      "harmonized_system_code": "3002.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Antisera and other blood fractions and modified immunological products",
      "description": "Glands and other organs for organotherapeutic uses"
    },
    {
      "heading_no": "30.01",
      "harmonized_system_code": "3002.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Vaccines for human medicine",
      "description": "Glands and other organs for organotherapeutic uses"
    },
    {
      "heading_no": "30.01",
      "harmonized_system_code": "3002.3000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Vaccines for veterinary medicine",
      "description": "Glands and other organs for organotherapeutic uses"
    },
    {
      "heading_no": "30.01",
      "harmonized_system_code": "3002.9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Glands and other organs for organotherapeutic uses"
    },
    {
      "heading_no": "30.03",
      "harmonized_system_code": "3003.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing peniclline derivatives as thereof, with a penicilli acid structure, or streptomycin or their derivatives",
      "description": "Medicaments (excluding goods of heading No.3002.02, 30.05 or 30.06)"
    },
    {
      "heading_no": "30.03",
      "harmonized_system_code": "3003.2000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing other antibiotics",
      "description": "Medicaments (excluding goods of heading No.3002.02, 30.05 or 30.06)"
    },
    {
      "heading_no": "30.03",
      "harmonized_system_code": "3003.3100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing insulin",
      "description": "Medicaments (excluding goods of heading No.3002.02, 30.05 or 30.06)"
    },
    {
      "heading_no": "30.03",
      "harmonized_system_code": "3003.3200",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Medicaments (excluding goods of heading No.3002.02, 30.05 or 30.06)"
    },
    {
      "heading_no": "30.03",
      "harmonized_system_code": "3003.4000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing alkaloids or derivatives Thereof or antibiotics",
      "description": "Medicaments (excluding goods of heading No.3002.02, 30.05 or 30.06)"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing penecillins or derivative thereof, with a penicillianic acid structure, or streptomycin or their derivatives.",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.2000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing others antibiotics",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.3200",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing insulin.",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.3900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.4000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Containing alkaloids or derivatives thereof not containing hormones, other products of healing No 29.37 or antibiotics",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.5000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Other medicament containing vitamin and other products of healing No 20",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.04",
      "harmonized_system_code": "3004.9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Other life saving drug and medicaments.",
      "description": "Medicaments (excluding goods of heading No. 30.02, 30.05 or 30.06) consisting of mixed or unmixed products for therapeutic uses"
    },
    {
      "heading_no": "30.05",
      "harmonized_system_code": "3005.100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Adhesive dressings and other articles having an adhesive layer",
      "description": "Wadding, gauze, bandages and similar articles (for example dressings, adhesive plasters, poultics), impregnated or coated with pharmaceutical substance or put up in forms or packing for retail sale for medical, surgical, dental or veterinary purposes."
    },
    {
      "heading_no": "30.05",
      "harmonized_system_code": "3005.9100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "bandages and swabs",
      "description": "Wadding, gauze, bandages and similar articles (for example dressings, adhesive plasters, poultics), impregnated or coated with pharmaceutical substance or put up in forms or packing for retail sale for medical, surgical, dental or veterinary purposes."
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Sterile surgical castut, similar sterile suture materials and sterile tissue adhesives for surgical wound closure, sterile laminaria and sterile absorbable surgical or dental haemostatic.",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.2000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Blood-grouping reagent",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.3000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Opacifying preparations for X-ray examinations; diagnostic reagents designed to be administered to the patient",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.4000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Dental cements and other dental fillings; bone reconstruction cements",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.5000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "First-aid boxes and kits",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "30.06",
      "harmonized_system_code": "3006.6000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Chemical contraceptive preparations based on hormones or spermicides.",
      "description": "Pharmaceutical goods"
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.110",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Electro-cardiographs",
      "description": "Instruments and appliance used in medical, surgical dental or veterinary sciences, including scintigraphy apparatus, other electro-medical apparatus and sight-testing instruments."
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.2000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ultra-Violet or infra-red ray apparatus",
      "description": "Instruments and appliance used in medical, surgical dental or veterinary sciences, including scintigraphy apparatus, other electro-medical apparatus and sight-testing instruments."
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.3100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Syringes metal needles and needles for sutures",
      "description": "Instruments and appliance used in medical, surgical dental or veterinary sciences, including scintigraphy apparatus, other electro-medical apparatus and sight-testing instruments."
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.3900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Instruments and appliance used in medical, surgical dental or veterinary sciences, including scintigraphy apparatus, other electro-medical apparatus and sight-testing instruments."
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Other instruments and appliances",
      "description": "Instruments and appliance used in medical, surgical dental or veterinary sciences, including scintigraphy apparatus, other electro-medical apparatus and sight-testing instruments."
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.4100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Dental drill engines, whether or not combined on a single base with other dental equipment",
      "description": "Instruments and appliance used in dental sciences"
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.4900",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others",
      "description": "Instruments and appliance used in dental sciences"
    },
    {
      "heading_no": "90.18",
      "harmonized_system_code": "9018.5000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ophthalmic instruments and appliances",
      "description": "Instruments and appliance used in dental sciences"
    },
    {
      "heading_no": "90.19",
      "harmonized_system_code": "9019.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Mechano-Therapy appliances; message apparatus; psychological aptitude testing apparatus.",
      "description": "Mechano-therapy appliances; message apparatus; Psychological aptitude testing apparatus. Ozone therapy, oxygen therapy, erosoltherapy, artificial respiration or other therapeutic respiration apparatus."
    },
    {
      "heading_no": "90.19",
      "harmonized_system_code": "9019.200",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Ozone therapy, oxygen therapy, aerosol therapy, artificial respiration or other therapeutic respiration apparatus.",
      "description": "Mechano-therapy appliances; message apparatus; Psychological aptitude testing apparatus. Ozone therapy, oxygen therapy, erosoltherapy, artificial respiration or other therapeutic respiration apparatus."
    },
    {
      "heading_no": "90.21",
      "harmonized_system_code": "9021.1100-9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "",
      "description": "Orthopaedic appliance, including crutches, surgical belt and trusses; splints and other fracture appliances, artificial parts of the body, hearing aids other appliances which are worn or carried, or implanted in the body, to compensate for a defect or disability."
    },
    {
      "heading_no": "90.22",
      "harmonized_system_code": "9022.1300",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others, for dental uses",
      "description": "Apparatus based on the used of X-Rays or alpha, beta or gamma radiations, whether or not for medical, surgical, dental or veterinary uses, including radiography or radiotherapy apparatus, X-Ray tubes and other X-Ray generators, high tension generators, control panels and desks, screens, examination or treatment tables, chair and the like."
    },
    {
      "heading_no": "90.22",
      "harmonized_system_code": "9022.1400",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Others for medical, surgical, or veterinary uses",
      "description": "Apparatus based on the used of X-Rays or alpha, beta or gamma radiations, whether or not for medical, surgical, dental or veterinary uses, including radiography or radiotherapy apparatus, X-Ray tubes and other X-Ray generators, high tension generators, control panels and desks, screens, examination or treatment tables, chair and the like."
    },
    {
      "heading_no": "90.22",
      "harmonized_system_code": "9022.2100",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "for medical, surgical, dental or veterinary uses.",
      "description": "Apparatus based on the used of X-Rays or alpha, beta or gamma radiations, whether or not for medical, surgical, dental or veterinary uses, including radiography or radiotherapy apparatus, X-Ray tubes and other X-Ray generators, high tension generators, control panels and desks, screens, examination or treatment tables, chair and the like."
    },
    {
      "heading_no": "94.02",
      "harmonized_system_code": "9402.1000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Dentists, or similar chairs and parts thereof.",
      "description": "Medical, surgical, dental or veterinary furniture"
    },
    {
      "heading_no": "94.02",
      "harmonized_system_code": "9402.9000",
      "tariff_category": "MEDICAL, VENTIRINARY AND PHARMACEUTICAL RAW MATERIALS AND PRODUCTS",
      "tariff": "Other",
      "description": "Medical, surgical, dental or veterinary furniture"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.1000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Carcasses and half carcasses of lamb, fresh or chilled",
      "description": "Meat of sheep or goats, fresh, chilled or frozen."
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.2100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Other meat of sheep, fresh or chilled",
      "description": "Other meat of sheep, fresh or chilled"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.3000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Boneless",
      "description": "Other meat of sheep, fresh or chilled"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.3000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Carcasses and half-carcasses of lamb, frozen",
      "description": "Other meat of sheep, fresh or chilled"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.4100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Carcasses and half carcasses",
      "description": "Other meat of sheep, frozen"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.4200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Other cuts with bone",
      "description": "Other meat of sheep, frozen"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.4300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Boneless",
      "description": "Other meat of sheep, frozen"
    },
    {
      "heading_no": "02.04",
      "harmonized_system_code": "0204.5000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Meat of goats",
      "description": "Other meat of sheep, frozen"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.1100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, fresh or chilled",
      "description": "Of fowls of the species Gallus Domesticus "
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.1200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, frozen",
      "description": "Of fowls of the species Gallus Domesticus "
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.1300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cuts and offal, fresh or chilled",
      "description": "Of fowls of the species Gallus Domesticus "
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.1400",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cuts and offal, frozen",
      "description": "Of fowls of the species Gallus Domesticus "
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.2400",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, fresh and chilled",
      "description": "Of Turkeys"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.2500",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, frozen",
      "description": "Of Turkeys"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.2600",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cuts and offal, fresh or chilled",
      "description": "Of Turkeys"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.3200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, fresh or chilled",
      "description": "Of ducks, gesse or guinea fowl"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.330",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Not cut in pieces, frozen",
      "description": "Of ducks, gesse or guinea fowl"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.3500",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Other, fresh or chilled",
      "description": "Of ducks, gesse or guinea fowl"
    },
    {
      "heading_no": "02.07",
      "harmonized_system_code": "0207.3600",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Other, frozen",
      "description": "Of ducks, gesse or guinea fowl"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.1100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Trout",
      "description": "Salmonidase, excluding livers and roes"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.1200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Pacific Salmon, Altantic Salmon and Danube Salmon",
      "description": "Salmonidase, excluding livers and roes"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.2100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Halibut",
      "description": " Flat fish (excluding livers and roes)"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.2200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Plaice",
      "description": " Flat fish (excluding livers and roes)"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.2300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Sole",
      "description": " Flat fish (excluding livers and roes)"
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.3100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Albacore or longfinned tunas",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.3200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Yellow fin tunas",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.3300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Skip-jack or stripe-bellied bonito",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.4000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Herrings (excluding living and roes)",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.5000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cod (excluding living and roes)",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Sardines (brisling or sprats)",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Haddock",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Coalfish",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6400",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Mackerel",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6500",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Dogfish and other sharks",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.6600",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Eels",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.02",
      "harmonized_system_code": "0302.7000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Livers Roes",
      "description": "Tunas, skip jacks or stripe bellied bonito (excluding liver and Roes)."
    },
    {
      "heading_no": "03.03",
      "harmonized_system_code": "303.8000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "All details as above",
      "description": "Fish, frozen, excluding fish fill fillets and other fish meat and heading No. 03.04."
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.1000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Fish meal fit for human consumption",
      "description": "Fish, dried, salted, or in brine smoke fish, whether or not cooked before or during the smoking process; fish meal fit human consumption."
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.2000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Livers and roes, dried smoked, or in brine",
      "description": "Fish, dried, salted, or in brine smoke fish, whether or not cooked before or during the smoking process; fish meal fit human consumption."
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.3000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Fish fillets, dried, salted or in but not smoked",
      "description": "Fish, dried, salted, or in brine smoke fish, whether or not cooked before or during the smoking process; fish meal fit human consumption."
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.4200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Pacific salmon, atlantic salmon and Danube salmon",
      "description": "Smoked fish, including fillets"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.4200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Herrings",
      "description": "Smoked fish, including fillets"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.5100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Dried fish whether or not salted but not smoked",
      "description": "Smoked fish, including fillets"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.5100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cod",
      "description": "Smoked fish, including fillets"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.5900",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Others",
      "description": "Smoked fish, including fillets"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.6100",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Herrings",
      "description": "Fish, salted but not dried or smoked and fish in brine"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.6200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Cod",
      "description": "Fish, salted but not dried or smoked and fish in brine"
    },
    {
      "heading_no": "03.05",
      "harmonized_system_code": "0305.6300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Anchovies",
      "description": "Fish, salted but not dried or smoked and fish in brine"
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.1000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Peas (Pisum sativum)",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.2000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Chickpeas (garbanzos) & Beans",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.3200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "beans of the species Vigna Mungo (L), hepper or Vigna radiate (L).",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.3200",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Small red (Adzuki) beans.",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.3300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Kidney beans, including white pea beans.",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.4000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Lentils",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.9000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Broad beans and horse beans.",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.13",
      "harmonized_system_code": "0713.9000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Others",
      "description": "Dried leguminous vegetables, shelled, whether or not skinned or split."
    },
    {
      "heading_no": "07.14",
      "harmonized_system_code": "0714.1000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Manioc (Cassava)",
      "description": "Manioc, arrowroot, salep, Jerusalem artichokes, sweet potatoes and similar roots an tubers."
    },
    {
      "heading_no": "07.14",
      "harmonized_system_code": "0714.2000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Sweet potatoes",
      "description": "Manioc, arrowroot, salep, Jerusalem artichokes, sweet potatoes and similar roots an tubers."
    },
    {
      "heading_no": "07.14",
      "harmonized_system_code": "0714.9000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Others",
      "description": "Manioc, arrowroot, salep, Jerusalem artichokes, sweet potatoes and similar roots an tubers."
    },
    {
      "heading_no": "10.06",
      "harmonized_system_code": "1006.1000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Rice in the husk (paddy or rough)",
      "description": "Rice"
    },
    {
      "heading_no": "10.06",
      "harmonized_system_code": "1006.2000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Husked (brown) rice",
      "description": "Rice"
    },
    {
      "heading_no": "10.06",
      "harmonized_system_code": "1006.3000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Semi-milled or wholly milled or whether or not polished or glaze",
      "description": "Rice"
    },
    {
      "heading_no": "10.06",
      "harmonized_system_code": "1006.4000",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Broken rice",
      "description": "Rice"
    },
    {
      "heading_no": "11.04",
      "harmonized_system_code": "1104.1900",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Rolled or flaked grains Of other cereals",
      "description": "Cereal grains otherwise work except rice of heading No.10.06"
    },
    {
      "heading_no": "11.04",
      "harmonized_system_code": "1104.2300",
      "tariff_category": "BASIC FOOD ITEMS",
      "tariff": "Rolled or flaked grains of maize (corn)",
      "description": "Cereal grains otherwise work except rice of heading No.10.06"
    },
    {
      "heading_no": "19.01",
      "harmonized_system_code": "1901.1000",
      "tariff_category": "INFANT FOOD",
      "tariff": "Preparations for infant use, put up for retail sale",
      "description": "Malt extract, food preparations of flour, meal, starch or malt extract, not containing Cocoa powder or containing Cocoa powder or containing cocoa powdered in proportion by weight less than 50% not elsewhere specified or included; Food preparation of goods of heading Nos. 04.01 to 04.04, not containing Cocoa powder in a proportion by weight of less than 10% not elsewhere specified or included."
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4802.5100",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Weighing less than 40g/m2",
      "description": "Uncoated paper and paperboard, of a kind used for writing, printing etc."
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4802.5300",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Weighing more than 150 g/m2",
      "description": "Uncoated paper and paperboard, of a kind used for writing, printing etc."
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4810.1100",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Weighing not more than 150 g/m2",
      "description": "Paper and paperboard, of a kind used for writing, printing or other graphic purposes whether or not containing fibre obtained by a mechanical process or of which not more than 100% by weight of the total fibre content consist of such fibres"
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4810.1200",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Weighing more than 150 g/m2",
      "description": "Paper and paperboard, of a kind used for writing, printing or other graphic purposes whether or not containing fibre obtained by a mechanical process or of which not more than 100% by weight of the total fibre content consist of such fibres"
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "44810.2100",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Light weight coated paper. 5",
      "description": "Paper and paperboard, of a kind used for writing, printing or other graphic purposes whether or not containing fibre obtained by a mechanical process or of which not more than 100% by weight of the total fibre content consist of such fibres"
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4810.2900",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Others",
      "description": "Paper and paperboard, of a kind used for writing, printing or other graphic purposes whether or not containing fibre obtained by a mechanical process or of which not more than 100% by weight of the total fibre content consist of such fibres"
    },
    {
      "heading_no": "48.20",
      "harmonized_system_code": "4820.2000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Exercise Books ",
      "description": "Other Articles of Stationery"
    },
    {
      "heading_no": "49.01",
      "harmonized_system_code": "4901.1000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "In single sheets, whether or not folded",
      "description": "Printed books, brochures, leaflets and similar printed matter whether or not in single sheets."
    },
    {
      "heading_no": "49.01",
      "harmonized_system_code": "4901.9100",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Dictionaries and encyclopedias, and serial installments thereof",
      "description": "Printed books, brochures, leaflets and similar printed matter whether or not in single sheets."
    },
    {
      "heading_no": "49.01",
      "harmonized_system_code": "4901.9900",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Others (restricted to educational textbooks)",
      "description": "Printed books, brochures, leaflets and similar printed matter whether or not in single sheets."
    },
    {
      "heading_no": "49.02",
      "harmonized_system_code": "4902.1000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Appearing at least four times a week",
      "description": "Newspapers, journals and periodicals, whether or not illustrated or containing advertising materials."
    },
    {
      "heading_no": "49.02",
      "harmonized_system_code": "4902.9900",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Others",
      "description": "Newspapers, journals and periodicals, whether or not illustrated or containing advertising materials."
    },
    {
      "heading_no": "49.03",
      "harmonized_system_code": "4903.0000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Children’s picture, drawing or colouring books",
      "description": "Newspapers, journals and periodicals, whether or not illustrated or containing advertising materials."
    },
    {
      "heading_no": "49.04",
      "harmonized_system_code": "4904.0000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Music, printed or in manuscript whether or not bound or illustrated",
      "description": "Newspapers, journals and periodicals, whether or not illustrated or containing advertising materials."
    },
    {
      "heading_no": "49.05",
      "harmonized_system_code": "4905.1000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "Globes",
      "description": "Newspapers, journals and periodicals, whether or not illustrated or containing advertising materials."
    },
    {
      "heading_no": "49.06",
      "harmonized_system_code": "4906.0000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "",
      "description": "Plans and drawings for architectural, engineering, industrial, commercial, topographical or similar purposes, being originals drawn by hand, hand written texts."
    },
    {
      "heading_no": "49.07",
      "harmonized_system_code": "4907.0000",
      "tariff_category": "BOOKS, NEWSPAPERS AND MAGAZINES",
      "tariff": "",
      "description": "Unused postage, revenue or similar stamps of current or new issue in the country to which they are destined; stamp impressed paper; cheque forms, bank notes, stock, share or bond certificates and similar document of title."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.1100",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Instantaneous and water heater",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.2000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Medical, surgical or laboratory sterilizers",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.3100",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "For agricultural products",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.3200",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "for wood, paper pulp, paper or paperboard",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.4000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Distilling or rectifying plant.",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.5000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Heat exchange units",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.6000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Machinery for liquefying air or gas ",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.8100",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "For making hot drinks or for cooking or heating food. ",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "84.19",
      "harmonized_system_code": "8419.9000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Parts of the above.",
      "description": "Machinery, plant or laboratory equipment, whether or not electrically heated, for the treatment of materials by a process involving a change of temperature such as heating cooking, roasting, distilling, rectifying, sterlising, pasteurizing, steaming, drying, evaporating, vaporizing, condensing or cooling, other than machinery or plant of a kind used for domestic purposes, instantaneous storage water heaters and electrics."
    },
    {
      "heading_no": "90.17",
      "harmonized_system_code": "9017.1000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Drafting tables and machines, whether or not automatic",
      "description": "Drawing, marking-out or mathematical calculating instruments (for example, drafting machines, Pantographs, protractors, drawing sets, slide rules, disc calculators); instruments for measuring length for use in the hand (for example measuring rods and tapes, micrometers, calipers), not specified or included elsewhere in this chapter."
    },
    {
      "heading_no": "90.17",
      "harmonized_system_code": "9017.2000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Other drawing, marking-out or mathematical calculating instruments ",
      "description": "Drawing, marking-out or mathematical calculating instruments (for example, drafting machines, Pantographs, protractors, drawing sets, slide rules, disc calculators); instruments for measuring length for use in the hand (for example measuring rods and tapes, micrometers, calipers), not specified or included elsewhere in this chapter."
    },
    {
      "heading_no": "90.17",
      "harmonized_system_code": "9017.3000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Micrometers, calipers and gauges",
      "description": "Drawing, marking-out or mathematical calculating instruments (for example, drafting machines, Pantographs, protractors, drawing sets, slide rules, disc calculators); instruments for measuring length for use in the hand (for example measuring rods and tapes, micrometers, calipers), not specified or included elsewhere in this chapter."
    },
    {
      "heading_no": "90.17",
      "harmonized_system_code": "9017.8000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Other instruments",
      "description": "Drawing, marking-out or mathematical calculating instruments (for example, drafting machines, Pantographs, protractors, drawing sets, slide rules, disc calculators); instruments for measuring length for use in the hand (for example measuring rods and tapes, micrometers, calipers), not specified or included elsewhere in this chapter."
    },
    {
      "heading_no": "90.17",
      "harmonized_system_code": "9017.9000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "Parts and accessories",
      "description": "Drawing, marking-out or mathematical calculating instruments (for example, drafting machines, Pantographs, protractors, drawing sets, slide rules, disc calculators); instruments for measuring length for use in the hand (for example measuring rods and tapes, micrometers, calipers), not specified or included elsewhere in this chapter."
    },
    {
      "heading_no": "90.23",
      "harmonized_system_code": "9023.0000",
      "tariff_category": "EDUCATIONAL MATERIALS (Laboratory Equipment)",
      "tariff": "",
      "description": "Instruments apparatus and models (for demonstrational purpose for example, in education or exhibitions), unsuitable for other uses."
    },
    {
      "heading_no": "39.23",
      "harmonized_system_code": "3923.3000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "Feeding bottles and related products for babies use",
      "description": ""
    },
    {
      "heading_no": "48.18",
      "harmonized_system_code": "4818.4000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "Sanitary towels and tampons napkins and napkin liners for babies and sanitary articles",
      "description": ""
    },
    {
      "heading_no": "61.11",
      "harmonized_system_code": "6111.1000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "of wool or fine animal hairs",
      "description": "Babies garments and clothing accessories knitted or crotched"
    },
    {
      "heading_no": "61.11",
      "harmonized_system_code": "6111.2000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "of cotton",
      "description": "Babies garments and clothing accessories knitted or crotched"
    },
    {
      "heading_no": "61.11",
      "harmonized_system_code": "6111.3000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "of synthetic fibres",
      "description": "Babies garments and clothing accessories knitted or crotched"
    },
    {
      "heading_no": "61.11",
      "harmonized_system_code": "6111.9000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": " of other textile materials",
      "description": "Babies garments and clothing accessories knitted or crotched"
    },
    {
      "heading_no": "62.09",
      "harmonized_system_code": "6209.1000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": " of wool of fine animal hair",
      "description": "Babies garments and clothing accessories "
    },
    {
      "heading_no": "62.09",
      "harmonized_system_code": "6209.2000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": " of cotton",
      "description": "Babies garments and clothing accessories "
    },
    {
      "heading_no": "62.09",
      "harmonized_system_code": "6209.3000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": " of synthetic fibres",
      "description": "Babies garments and clothing accessories "
    },
    {
      "heading_no": "62.09",
      "harmonized_system_code": "6209.9000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": " of other textile materials",
      "description": "Babies garments and clothing accessories "
    },
    {
      "heading_no": "87.15",
      "harmonized_system_code": "8715.0000",
      "tariff_category": "BABY PRODUCTS",
      "tariff": "",
      "description": "Baby carriages and parts."
    },
    {
      "heading_no": "86.05",
      "harmonized_system_code": "8605.0000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Railway or tramway passenger vans",
      "description": "Definition of commercial vehicles has been restricted to those vehicles designed for the transport of persons while spare parts are also restricted to engines, gears, brakes and brakes linings."
    },
    {
      "heading_no": "86.06",
      "harmonized_system_code": "8606.1000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Railway or trayway goods van; tank wagons and the like",
      "description": "Definition of commercial vehicles has been restricted to those vehicles designed for the transport of persons while spare parts are also restricted to engines, gears, brakes and brakes linings."
    },
    {
      "heading_no": "86.07",
      "harmonized_system_code": "8607.1100",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Driving bogies and bissel – bogies",
      "description": "Definition of commercial vehicles has been restricted to those vehicles designed for the transport of persons while spare parts are also restricted to engines, gears, brakes and brakes linings."
    },
    {
      "heading_no": "86.07",
      "harmonized_system_code": "8607.2100",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Air brakes and parts",
      "description": "Definition of commercial vehicles has been restricted to those vehicles designed for the transport of persons while spare parts are also restricted to engines, gears, brakes and brakes linings."
    },
    {
      "heading_no": "86.07",
      "harmonized_system_code": "8607.9100",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Of locomotives",
      "description": "Definition of commercial vehicles has been restricted to those vehicles designed for the transport of persons while spare parts are also restricted to engines, gears, brakes and brakes linings."
    },
    {
      "heading_no": "87.01",
      "harmonized_system_code": "8701.1000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Pedestrian controlled tractors",
      "description": "Tractors (other than tractor of heading No. 87.09)"
    },
    {
      "heading_no": "87.01",
      "harmonized_system_code": "8701.2000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Road tractors for semi-trailers",
      "description": "Tractors (other than tractor of heading No. 87.09)"
    },
    {
      "heading_no": "87.01",
      "harmonized_system_code": "8701.3000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Track-laying tractors",
      "description": "Tractors (other than tractor of heading No. 87.09)"
    },
    {
      "heading_no": "87.02",
      "harmonized_system_code": "8702.1000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "With compression-ignition interior combustion piston engine (diesel semi-diesel semi-diesel i..e vehicle capable of carrying not less than nine passengers).",
      "description": "Public transport type passenger vehicles "
    },
    {
      "heading_no": "87.02",
      "harmonized_system_code": "8702.1900",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Others",
      "description": "Public transport type passenger vehicles "
    },
    {
      "heading_no": "87.04",
      "harmonized_system_code": "8704.2290",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Dumpers, designed for off-highway use",
      "description": "Motor vehicles for the transport of goods."
    },
    {
      "heading_no": "87.04",
      "harmonized_system_code": "8704.2290",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Other (not exceeding 20 tonnes) ",
      "description": "Motor vehicles for the transport of goods."
    },
    {
      "heading_no": "87.04",
      "harmonized_system_code": "8704.3290",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Other (exceeding 5 tonnes)",
      "description": "Motor vehicles for the transport of goods."
    },
    {
      "heading_no": "87.05",
      "harmonized_system_code": "8705.3000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Fire Fighting vehicles, parts and accessories",
      "description": "Special Purpose Motor Vehicles."
    },
    {
      "heading_no": "87.05",
      "harmonized_system_code": "8707.9000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Others",
      "description": "Special Purpose Motor Vehicles."
    },
    {
      "heading_no": "87.08",
      "harmonized_system_code": "8708.3100",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Brakes and servo-brakes and parts thereof: Mounted brake linings ",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.08",
      "harmonized_system_code": "8708.3900 ",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Others ",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.08",
      "harmonized_system_code": "8708.4000 ",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": " Gear boxes ",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.08",
      "harmonized_system_code": "8708.5000 ",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": " Drive boxes",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.08",
      "harmonized_system_code": "8708.6000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Non-driving axles ",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.10",
      "harmonized_system_code": "8710.0000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Tanks and others armoured fighting vehicles motorized",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.11",
      "harmonized_system_code": "8711.1000-2000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Motorcycles (including mopeds) and cycles fitted with an auxiliary motors",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.12",
      "harmonized_system_code": "8712.0000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Bicycle and other cycles (including delivery tricycles), not motorized",
      "description": "Parts and accessories of commercial vehicles. (all tyres and tubes regardless of usage are vatable"
    },
    {
      "heading_no": "87.13",
      "harmonized_system_code": "8713.1000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Not mechanically propelled",
      "description": "Invalid carriage whether or not motorised or otherwise mechanically propelled"
    },
    {
      "heading_no": "87.13",
      "harmonized_system_code": "8713.9000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Others",
      "description": "Invalid carriage whether or not motorised or otherwise mechanically propelled, others."
    },
    {
      "heading_no": "87.14",
      "harmonized_system_code": "8714.9300",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Hubs and hub brakes.",
      "description": "Parts and accessories of vehicles of heading Nos. 87.11 to 87.13."
    },
    {
      "heading_no": "87.14",
      "harmonized_system_code": "8714.9400",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Brakes and hub brakes",
      "description": "Parts and accessories of vehicles of heading Nos. 87.11 to 87.13."
    },
    {
      "heading_no": "87.14",
      "harmonized_system_code": "8714.9600",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Pedals ·and crank - gear.",
      "description": "Parts and accessories of vehicles of heading Nos. 87.11 to 87.13."
    },
    {
      "heading_no": "87.16",
      "harmonized_system_code": "8716.2000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Trailers and semi-trailer for agricultural purposes",
      "description": "Self-loading or self-unloading"
    },
    {
      "heading_no": "88.02",
      "harmonized_system_code": "8802.2000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Aeroplanes and other aircraft, of an unladen weight not exceeding 2,000kg.",
      "description": "Aeroplanes and other aircraft"
    },
    {
      "heading_no": "88.02",
      "harmonized_system_code": "8802.3000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Aeroplanes and other aircraft, of an unladen weight exceeding 2,000kg but not exceeding 15,000kg ",
      "description": "Aeroplanes and other aircraft"
    },
    {
      "heading_no": "88.02",
      "harmonized_system_code": "8802.4000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Aeroplanes and other aircraft, of an unladen weight exceeding 15,000kg.",
      "description": "Aeroplanes and other aircraft"
    },
    {
      "heading_no": "88.03",
      "harmonized_system_code": "8803.1000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Propellers and rotors and parts thereof",
      "description": "Parts of goods of heading No. 88.01 or 88.02."
    },
    {
      "heading_no": "88.03",
      "harmonized_system_code": "8803.2000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Under carriages and parts thereoff",
      "description": "Parts of goods of heading No. 88.01 or 88.02."
    },
    {
      "heading_no": "89.01",
      "harmonized_system_code": "8901.3000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "Refrigerated vessels other than those of sub-heading No. 8901.2000. ",
      "description": "Cruise ships, excursion boats, ferry-boats, cargo ships barges and similar vessels for the transport of persons or goods."
    },
    {
      "heading_no": "89.01",
      "harmonized_system_code": "8901.9000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "ther vessels for the transport of goods and other. vessels for the transport of both persons and goods ",
      "description": "Cruise ships, excursion boats, ferry-boats, cargo ships barges and similar vessels for the transport of persons or goods."
    },
    {
      "heading_no": "98.02",
      "harmonized_system_code": "8902.0000",
      "tariff_category": "COMMERCIAL VEHICLES AND SPARE PARTS",
      "tariff": "",
      "description": "Fishing vessels; factory ship and other vessels for processing or preserving fishery products"
    },
    {
      "heading_no": "38.08",
      "harmonized_system_code": "3808.1200",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Agricultural Insecticides",
      "description": "Insecticides, rodenticides, fungicides, herbicides, anti-sprouting products and plant growth regulator disinfectants and similar products."
    },
    {
      "heading_no": "38.08",
      "harmonized_system_code": "3808.2000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Fungicides",
      "description": "Insecticides, rodenticides, fungicides, herbicides, anti-sprouting products and plant growth regulator disinfectants and similar products."
    },
    {
      "heading_no": "38.08",
      "harmonized_system_code": "3808.3000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Herbicides, anti-sprouting products and plant-growth regulators",
      "description": "Insecticides, rodenticides, fungicides, herbicides, anti-sprouting products and plant growth regulator disinfectants and similar products."
    },
    {
      "heading_no": "84.24",
      "harmonized_system_code": "8424.8100",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Appliances for agricultural or horticultural purpose.",
      "description": "Mechanical appliances (whether or not hand-operated) for projecting, dispersing or spraying liquids or powders."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.1000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Ploughs",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.2100",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Harrows, scarifiers, cultivator weeders and hoes",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.3000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Disc harrows",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.4000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Seeders, planters and transplanters",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.5000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Manure spreaders and fertilizer distributors",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.32",
      "harmonized_system_code": "8432.5000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Parts of 8437.1000",
      "description": "Agricultural, horticultural or forestry machinery for soil preparation or cultivation; Lawn or sport-ground roller."
    },
    {
      "heading_no": "84.33",
      "harmonized_system_code": "8433.5100",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Other harvesting machinery threshing machinery",
      "description": "Harvesting of threshing machinery, including straw or fodder balers, grass or hay movers; machines for cleaning, sorting or grading eggs, fruit or other agricultural produce."
    },
    {
      "heading_no": "84.33",
      "harmonized_system_code": "8433.5200",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Combine harvester-threshers",
      "description": "Harvesting of threshing machinery, including straw or fodder balers, grass or hay movers; machines for cleaning, sorting or grading eggs, fruit or other agricultural produce."
    },
    {
      "heading_no": "84.33",
      "harmonized_system_code": "8433.5300",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Root or other harvesting machineries",
      "description": "Harvesting of threshing machinery, including straw or fodder balers, grass or hay movers; machines for cleaning, sorting or grading eggs, fruit or other agricultural produce."
    },
    {
      "heading_no": "84.33",
      "harmonized_system_code": "8433.6000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Machine for cleaning, sorting or grading eggs, fruit or other agricultural produce.",
      "description": "Harvesting of threshing machinery, including straw or fodder balers, grass or hay movers; machines for cleaning, sorting or grading eggs, fruit or other agricultural produce."
    },
    {
      "heading_no": "84.33",
      "harmonized_system_code": "8433.900",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Parts of 8433.5100, 84333.5300 and 8433.6000",
      "description": "Harvesting of threshing machinery, including straw or fodder balers, grass or hay movers; machines for cleaning, sorting or grading eggs, fruit or other agricultural produce."
    },
    {
      "heading_no": "84.34",
      "harmonized_system_code": "8434.1000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Milking machines",
      "description": "Milking machines and dairy machinery."
    },
    {
      "heading_no": "84.34",
      "harmonized_system_code": "8434.2000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Dairy machinery",
      "description": "Milking machines and dairy machinery."
    },
    {
      "heading_no": "84.34",
      "harmonized_system_code": "8434.9000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Parts of 8434 .1000 and 8432 .2000 .",
      "description": "Milking machines and dairy machinery."
    },
    {
      "heading_no": "84.36",
      "harmonized_system_code": "8436.1000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Machinery for preparing animal feeding stuffs",
      "description": "Agricultural, horticutural forestry poultry -keeping or bee -keeping machinery, including germination plant fitted with mechanical or thermal equipment poultry incubators and brooders."
    },
    {
      "heading_no": "84.36",
      "harmonized_system_code": "8436.2100",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Poultry incubators and brooders",
      "description": "Agricultural, horticutural forestry poultry -keeping or bee -keeping machinery, including germination plant fitted with mechanical or thermal equipment poultry incubators and brooders."
    },
    {
      "heading_no": "84.36",
      "harmonized_system_code": "8436.9100",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Parts of poultry -keeping machinery or poultry incubators and brooders.",
      "description": "Agricultural, horticutural forestry poultry -keeping or bee -keeping machinery, including germination plant fitted with mechanical or thermal equipment poultry incubators and brooders."
    },
    {
      "heading_no": "84.37",
      "harmonized_system_code": "8437.1000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Machines for cleaning, sorting or grading seed, grain or dried leguminous vegetables",
      "description": "Machines for cleaning, sorting or grading seed, grain or dried Leguminous vegetables, machinery used in the milling industry or for the working of cereals or dried leguminous vegetable other than farm -type machinery."
    },
    {
      "heading_no": "84.37",
      "harmonized_system_code": "8437.9000",
      "tariff_category": "AGRICULTURAL EQUIPMENT & PRODUCTS",
      "tariff": "Parts of 8437.1000",
      "description": "Machines for cleaning, sorting or grading seed, grain or dried Leguminous vegetables, machinery used in the milling industry or for the working of cereals or dried leguminous vegetable other than farm -type machinery."
    },
    {
      "heading_no": "31.01",
      "harmonized_system_code": "3101.0000",
      "tariff_category": "FERTILIZER",
      "tariff": "Animal or vegetable fertilizers, whether or not mixed together or chemically treated. Produced by the mixing or chemical treatment of animal or vegetable products.",
      "description": ""
    },
    {
      "heading_no": "31.02",
      "harmonized_system_code": "3102.9000",
      "tariff_category": "FERTILIZER",
      "tariff": "Mineral or chemical fertilizers nitrogenous",
      "description": ""
    },
    {
      "heading_no": "31.04",
      "harmonized_system_code": "3104.1000-3000",
      "tariff_category": "FERTILIZER",
      "tariff": "Mineral or chemical fertilizers potassic",
      "description": ""
    },
    {
      "heading_no": "31.05",
      "harmonized_system_code": "3105.1000-6000",
      "tariff_category": "FERTILIZER",
      "tariff": "Mineral or chemical fertilizers containing two or three of the fertilizing elements, nitrogen phosphorous and potassium.",
      "description": ""
    },
    {
      "heading_no": "28.01",
      "harmonized_system_code": "2801.100",
      "tariff_category": "WATER TREATMENT CHEMICALS",
      "tariff": "Chlorines",
      "description": ""
    },
    {
      "heading_no": "28.28",
      "harmonized_system_code": "2828.1000",
      "tariff_category": "WATER TREATMENT CHEMICALS",
      "tariff": "Calcium Hypochlorite and others",
      "description": ""
    },
    {
      "heading_no": "28.33",
      "harmonized_system_code": "2833.3000",
      "tariff_category": "WATER TREATMENT CHEMICALS",
      "tariff": "Alums",
      "description": ""
    }
  ]
}

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 
     last-modified: Wed,21 May 2025 11:31:32 GMT 

- Responses
**Code**            **Description**             **Links**
200


27. **GET - /api/v1/invoice/resources/services-codes - GetServicesCodes**

### GetServicesCodes

- Parameters
**Name**                    **Description**
No parameters

- Responses
    - Curl
    curl -X 'GET' \
  'https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/services-codes' \
  -H 'accept: */*'

    - Request URL
    https://eivc-k6z6d.ondigitalocean.app/api/v1/invoice/resources/services-codes

- Server response
        **Code**	            **Details**
        200

    - Response body
    {
  "code": 200,
  "data": [
    {
      "description": "Growing of cereals (except rice), leguminous crops and oil seeds",
      "code": "0111"
    },
    {
      "description": "Growing of rice",
      "code": "0112"
    },
    {
      "description": "Growing of vegetables and melons, roots and tubers",
      "code": "0113"
    },
    {
      "description": "Growing of sugar cane",
      "code": "0114"
    },
    {
      "description": "Growing of tobacco",
      "code": "0115"
    },
    {
      "description": "Growing of fibre crops",
      "code": "0116"
    },
    {
      "description": "Growing of other non-perennial crops",
      "code": "0119"
    },
    {
      "description": "Growing of grapes",
      "code": "0121"
    },
    {
      "description": "Growing of tropical and subtropical fruits",
      "code": "0122"
    },
    {
      "description": "Growing of citrus fruits",
      "code": "0123"
    },
    {
      "description": "Growing of pome fruits and stone fruits",
      "code": "0124"
    },
    {
      "description": "Growing of other tree and bush fruits and nuts",
      "code": "0125"
    },
    {
      "description": "Growing of oleaginous fruits",
      "code": "0126"
    },
    {
      "description": "Growing of beverage crops",
      "code": "0127"
    },
    {
      "description": "Growing of spices, aromatic, drug and pharmaceutical crops",
      "code": "0128"
    },
    {
      "description": "Growing of other perennial crops",
      "code": "0129"
    },
    {
      "description": "Plant propagation",
      "code": "0130"
    },
    {
      "description": "Raising of cattle and buffaloes",
      "code": "0141"
    },
    {
      "description": "Raising of horses and other equines",
      "code": "0142"
    },
    {
      "description": "Raising of camels and camelids",
      "code": "0143"
    },
    {
      "description": "Raising of sheep and goats",
      "code": "0144"
    },
    {
      "description": "Raising of swine/pigs",
      "code": "0145"
    },
    {
      "description": "Raising of poultry",
      "code": "0146"
    },
    {
      "description": "Raising of other animals",
      "code": "0149"
    },
    {
      "description": "Mixed farming",
      "code": "0150"
    },
    {
      "description": "Support activities for crop production",
      "code": "0161"
    },
    {
      "description": "Support activities for animal production",
      "code": "0162"
    },
    {
      "description": "Post-harvest crop activities",
      "code": "0163"
    },
    {
      "description": "Seed processing for propagation",
      "code": "0164"
    },
    {
      "description": "Hunting, trapping and related service activities",
      "code": "0170"
    },
    {
      "description": "Silviculture and other forestry activities",
      "code": "0210"
    },
    {
      "description": "Logging",
      "code": "0220"
    },
    {
      "description": "Gathering of non-wood forest products",
      "code": "0230"
    },
    {
      "description": "Support services to forestry",
      "code": "0240"
    },
    {
      "description": "Marine fishing",
      "code": "0311"
    },
    {
      "description": "Freshwater fishing",
      "code": "0312"
    },
    {
      "description": "Marine aquaculture",
      "code": "0321"
    },
    {
      "description": "Freshwater aquaculture",
      "code": "0322"
    },
    {
      "description": "Mining of hard coal",
      "code": "0510"
    },
    {
      "description": "Mining of lignite",
      "code": "0520"
    },
    {
      "description": "Extraction of crude petroleum",
      "code": "0610"
    },
    {
      "description": "Extraction of natural gas",
      "code": "0620"
    },
    {
      "description": "Mining of iron ores",
      "code": "0710"
    },
    {
      "description": "Mining of uranium and thorium ores",
      "code": "0721"
    },
    {
      "description": "Mining of other non-ferrous metal ores",
      "code": "0729"
    },
    {
      "description": "Quarrying of stone, sand and clay",
      "code": "0810"
    },
    {
      "description": "Mining of chemical and fertilizer minerals",
      "code": "0891"
    },
    {
      "description": "Extraction of peat",
      "code": "0892"
    },
    {
      "description": "Extraction of salt",
      "code": "0893"
    },
    {
      "description": "Other mining and quarrying n.e.c.",
      "code": "0899"
    },
    {
      "description": "Support activities for petroleum and natural gas extraction",
      "code": "0910"
    },
    {
      "description": "Support activities for other mining and quarrying",
      "code": "0990"
    },
    {
      "description": "Processing and preserving of meat",
      "code": "1010"
    },
    {
      "description": "Processing and preserving of fish, crustaceans and molluscs",
      "code": "1020"
    },
    {
      "description": "Processing and preserving of fruit and vegetables",
      "code": "1030"
    },
    {
      "description": "Manufacture of vegetable and animal oils and fats",
      "code": "1040"
    },
    {
      "description": "Manufacture of dairy products",
      "code": "1050"
    },
    {
      "description": "Manufacture of grain mill products",
      "code": "1061"
    },
    {
      "description": "Manufacture of starches and starch products",
      "code": "1062"
    },
    {
      "description": "Manufacture of bakery products",
      "code": "1071"
    },
    {
      "description": "Manufacture of sugar",
      "code": "1072"
    },
    {
      "description": "Manufacture of cocoa, chocolate and sugar confectionery",
      "code": "1073"
    },
    {
      "description": "Manufacture of macaroni, noodles, couscous and similar farinaceous products",
      "code": "1074"
    },
    {
      "description": "Manufacture of prepared meals and dishes",
      "code": "1075"
    },
    {
      "description": "Manufacture of other food products n.e.c.",
      "code": "1079"
    },
    {
      "description": "Manufacture of prepared animal feeds",
      "code": "1080"
    },
    {
      "description": "Distilling, rectifying and blending of spirits",
      "code": "1101"
    },
    {
      "description": "Manufacture of wines",
      "code": "1102"
    },
    {
      "description": "Manufacture of malt liquors and malt",
      "code": "1103"
    },
    {
      "description": "Manufacture of soft drinks; production of mineral waters and other bottled waters",
      "code": "1104"
    },
    {
      "description": "Manufacture of tobacco products",
      "code": "1200"
    },
    {
      "description": "Preparation and spinning of textile fibres",
      "code": "1311"
    },
    {
      "description": "Weaving of textiles",
      "code": "1312"
    },
    {
      "description": "Finishing of textiles",
      "code": "1313"
    },
    {
      "description": "Manufacture of knitted and crocheted fabrics",
      "code": "1391"
    },
    {
      "description": "Manufacture of made-up textile articles, except apparel",
      "code": "1392"
    },
    {
      "description": "Manufacture of carpets and rugs",
      "code": "1393"
    },
    {
      "description": "Manufacture of cordage, rope, twine and netting",
      "code": "1394"
    },
    {
      "description": "Manufacture of other textiles n.e.c.",
      "code": "1399"
    },
    {
      "description": "Manufacture of wearing apparel, except fur apparel",
      "code": "1410"
    },
    {
      "description": "Manufacture of articles of fur",
      "code": "1420"
    },
    {
      "description": "Manufacture of knitted and crocheted apparel",
      "code": "1430"
    },
    {
      "description": "Tanning and dressing of leather; dressing and dyeing of fur",
      "code": "1511"
    },
    {
      "description": "Manufacture of luggage, handbags and the like, saddlery and harness",
      "code": "1512"
    },
    {
      "description": "Manufacture of footwear",
      "code": "1520"
    },
    {
      "description": "Sawmilling and planing of wood",
      "code": "1610"
    },
    {
      "description": "Manufacture of veneer sheets and wood-based panels",
      "code": "1621"
    },
    {
      "description": "Manufacture of builders’ carpentry and joinery",
      "code": "1622"
    },
    {
      "description": "Manufacture of wooden containers",
      "code": "1623"
    },
    {
      "description": "Manufacture of other products of wood; manufacture of articles of cork, straw and plaiting materials",
      "code": "1629"
    },
    {
      "description": "Manufacture of pulp, paper and paperboard",
      "code": "1701"
    },
    {
      "description": "Manufacture of corrugated paper and paperboard and of containers of paper and paperboard",
      "code": "1702"
    },
    {
      "description": "Manufacture of other articles of paper and paperboard",
      "code": "1709"
    },
    {
      "description": "Printing",
      "code": "1811"
    },
    {
      "description": "Service activities related to printing",
      "code": "1812"
    },
    {
      "description": "Reproduction of recorded media",
      "code": "1820"
    },
    {
      "description": "Manufacture of coke oven products",
      "code": "1910"
    },
    {
      "description": "Manufacture of refined petroleum products",
      "code": "1920"
    },
    {
      "description": "Manufacture of basic chemicals",
      "code": "2011"
    },
    {
      "description": "Manufacture of fertilizers and nitrogen compounds",
      "code": "2012"
    },
    {
      "description": "Manufacture of plastics and synthetic rubber in primary forms",
      "code": "2013"
    },
    {
      "description": "Manufacture of pesticides and other agrochemical products",
      "code": "2021"
    },
    {
      "description": "Manufacture of paints, varnishes and similar coatings, printing ink and mastics",
      "code": "2022"
    },
    {
      "description": "Manufacture of soap and detergents, cleaning and polishing preparations, perfumes and toilet preparations",
      "code": "2023"
    },
    {
      "description": "Manufacture of other chemical products n.e.c.",
      "code": "2029"
    },
    {
      "description": "Manufacture of man-made fibres",
      "code": "2030"
    },
    {
      "description": "Manufacture of pharmaceuticals, medicinal chemical and botanical products",
      "code": "2100"
    },
    {
      "description": "Manufacture of rubber tyres and tubes; retreading and rebuilding of rubber tyres",
      "code": "2211"
    },
    {
      "description": "Manufacture of other rubber products",
      "code": "2219"
    },
    {
      "description": "Manufacture of plastics products",
      "code": "2220"
    },
    {
      "description": "Manufacture of glass and glass products",
      "code": "2310"
    },
    {
      "description": "Manufacture of refractory products",
      "code": "2391"
    },
    {
      "description": "Manufacture of clay building materials",
      "code": "2392"
    },
    {
      "description": "Manufacture of other porcelain and ceramic products",
      "code": "2393"
    },
    {
      "description": "Manufacture of cement, lime and plaster",
      "code": "2394"
    },
    {
      "description": "Manufacture of articles of concrete, cement and plaster",
      "code": "2395"
    },
    {
      "description": "Cutting, shaping and finishing of stone",
      "code": "2396"
    },
    {
      "description": "Manufacture of other non-metallic mineral products n.e.c.",
      "code": "2399"
    },
    {
      "description": "Manufacture of basic iron and steel",
      "code": "2410"
    },
    {
      "description": "Manufacture of basic precious and other non-ferrous metals",
      "code": "2420"
    },
    {
      "description": "Casting of iron and steel",
      "code": "2431"
    },
    {
      "description": "Casting of non-ferrous metals",
      "code": "2432"
    },
    {
      "description": "Manufacture of structural metal products",
      "code": "2511"
    },
    {
      "description": "Manufacture of tanks, reservoirs and containers of metal",
      "code": "2512"
    },
    {
      "description": "Manufacture of steam generators, except central heating hot water boilers",
      "code": "2513"
    },
    {
      "description": "Manufacture of weapons and ammunition",
      "code": "2520"
    },
    {
      "description": "Forging, pressing, stamping and roll-forming of metal; powder metallurgy",
      "code": "2591"
    },
    {
      "description": "Treatment and coating of metals; machining",
      "code": "2592"
    },
    {
      "description": "Manufacture of cutlery, hand tools and general hardware",
      "code": "2593"
    },
    {
      "description": "Manufacture of other fabricated metal products n.e.c.",
      "code": "2599"
    },
    {
      "description": "Manufacture of electronic components and boards",
      "code": "2610"
    },
    {
      "description": "Manufacture of computers and peripheral equipment",
      "code": "2620"
    },
    {
      "description": "Manufacture of communication equipment",
      "code": "2630"
    },
    {
      "description": "Manufacture of consumer electronics",
      "code": "2640"
    },
    {
      "description": "Manufacture of measuring, testing, navigating and control equipment",
      "code": "2651"
    },
    {
      "description": "Manufacture of watches and clocks",
      "code": "2652"
    },
    {
      "description": "Manufacture of irradiation, electromedical and electrotherapeutic equipment",
      "code": "2660"
    },
    {
      "description": "Manufacture of optical instruments and photographic equipment",
      "code": "2670"
    },
    {
      "description": "Manufacture of magnetic and optical media",
      "code": "2680"
    },
    {
      "description": "Manufacture of electric motors, generators, transformers and electricity distribution and control apparatus",
      "code": "2710"
    },
    {
      "description": "Manufacture of batteries and accumulators",
      "code": "2720"
    },
    {
      "description": "Manufacture of fibre optic cables",
      "code": "2731"
    },
    {
      "description": "Manufacture of other electronic and electric wires and cables",
      "code": "2732"
    },
    {
      "description": "Manufacture of wiring devices",
      "code": "2733"
    },
    {
      "description": "Manufacture of electric lighting equipment",
      "code": "2740"
    },
    {
      "description": "Manufacture of domestic appliances",
      "code": "2750"
    },
    {
      "description": "Manufacture of other electrical equipment",
      "code": "2790"
    },
    {
      "description": "Manufacture of engines and turbines, except aircraft, vehicle and cycle engines",
      "code": "2811"
    },
    {
      "description": "Manufacture of fluid power equipment",
      "code": "2812"
    },
    {
      "description": "Manufacture of other pumps, compressors, taps and valves",
      "code": "2813"
    },
    {
      "description": "Manufacture of bearings, gears, gearing and driving elements",
      "code": "2814"
    },
    {
      "description": "Manufacture of ovens, furnaces and furnace burners",
      "code": "2815"
    },
    {
      "description": "Manufacture of lifting and handling equipment",
      "code": "2816"
    },
    {
      "description": "Manufacture of office machinery and equipment (except computers and peripheral equipment)",
      "code": "2817"
    },
    {
      "description": "Manufacture of power-driven hand tools",
      "code": "2818"
    },
    {
      "description": "Manufacture of other general-purpose machinery",
      "code": "2819"
    },
    {
      "description": "Manufacture of agricultural and forestry machinery",
      "code": "2821"
    },
    {
      "description": "Manufacture of metal-forming machinery and machine tools",
      "code": "2822"
    },
    {
      "description": "Manufacture of machinery for metallurgy",
      "code": "2823"
    },
    {
      "description": "Manufacture of machinery for mining, quarrying and construction",
      "code": "2824"
    },
    {
      "description": "Manufacture of machinery for food, beverage and tobacco processing",
      "code": "2825"
    },
    {
      "description": "Manufacture of machinery for textile, apparel and leather production",
      "code": "2826"
    },
    {
      "description": "Manufacture of other special-purpose machinery",
      "code": "2829"
    },
    {
      "description": "Manufacture of motor vehicles",
      "code": "2910"
    },
    {
      "description": "Manufacture of bodies (coachwork) for motor vehicles; manufacture of trailers and semi-trailers",
      "code": "2920"
    },
    {
      "description": "Manufacture of parts and accessories for motor vehicles",
      "code": "2930"
    },
    {
      "description": "Building of ships and floating structures",
      "code": "3011"
    },
    {
      "description": "Building of pleasure and sporting boats",
      "code": "3012"
    },
    {
      "description": "Manufacture of railway locomotives and rolling stock",
      "code": "3020"
    },
    {
      "description": "Manufacture of air and spacecraft and related machinery",
      "code": "3030"
    },
    {
      "description": "Manufacture of military fighting vehicles",
      "code": "3040"
    },
    {
      "description": "Manufacture of motorcycles",
      "code": "3091"
    },
    {
      "description": "Manufacture of bicycles and invalid carriages",
      "code": "3092"
    },
    {
      "description": "Manufacture of other transport equipment n.e.c.",
      "code": "3099"
    },
    {
      "description": "Manufacture of furniture",
      "code": "3100"
    },
    {
      "description": "Manufacture of jewellery and related articles",
      "code": "3211"
    },
    {
      "description": "Manufacture of imitation jewellery and related articles",
      "code": "3212"
    },
    {
      "description": "Manufacture of musical instruments",
      "code": "3220"
    },
    {
      "description": "Manufacture of sports goods",
      "code": "3230"
    },
    {
      "description": "Manufacture of games and toys",
      "code": "3240"
    },
    {
      "description": "Manufacture of medical and dental instruments and supplies",
      "code": "3250"
    },
    {
      "description": "Other manufacturing n.e.c.",
      "code": "3290"
    },
    {
      "description": "Repair of fabricated metal products",
      "code": "3311"
    },
    {
      "description": "Repair of machinery",
      "code": "3312"
    },
    {
      "description": "Repair of electronic and optical equipment",
      "code": "3313"
    },
    {
      "description": "Repair of electrical equipment",
      "code": "3314"
    },
    {
      "description": "Repair of transport equipment, except motor vehicles",
      "code": "3315"
    },
    {
      "description": "Repair of other equipment",
      "code": "3319"
    },
    {
      "description": "Installation of industrial machinery and equipment",
      "code": "3320"
    },
    {
      "description": "Electric power generation, transmission and distribution",
      "code": "3510"
    },
    {
      "description": "Manufacture of gas; distribution of gaseous fuels through mains",
      "code": "3520"
    },
    {
      "description": "Steam and air conditioning supply",
      "code": "3530"
    },
    {
      "description": "Water collection, treatment and supply",
      "code": "3600"
    },
    {
      "description": "Sewerage",
      "code": "3700"
    },
    {
      "description": "Collection of non-hazardous waste",
      "code": "3811"
    },
    {
      "description": "Collection of hazardous waste",
      "code": "3812"
    },
    {
      "description": "Treatment and disposal of non-hazardous waste",
      "code": "3821"
    },
    {
      "description": "Treatment and disposal of hazardous waste",
      "code": "3822"
    },
    {
      "description": "Materials recovery",
      "code": "3830"
    },
    {
      "description": "Remediation activities and other waste management services",
      "code": "3900"
    },
    {
      "description": "Construction of buildings",
      "code": "4100"
    },
    {
      "description": "Construction of roads and railways",
      "code": "4210"
    },
    {
      "description": "Construction of utility projects",
      "code": "4220"
    },
    {
      "description": "Construction of other civil engineering projects",
      "code": "4290"
    },
    {
      "description": "Demolition",
      "code": "4311"
    },
    {
      "description": "Site preparation",
      "code": "4312"
    },
    {
      "description": "Electrical installation",
      "code": "4321"
    },
    {
      "description": "Plumbing, heat and air-conditioning installation",
      "code": "4322"
    },
    {
      "description": "Other construction installation",
      "code": "4329"
    },
    {
      "description": "Building completion and finishing",
      "code": "4330"
    },
    {
      "description": "Other specialized construction activities",
      "code": "4390"
    },
    {
      "description": "Sale of motor vehicles",
      "code": "4510"
    },
    {
      "description": "Maintenance and repair of motor vehicles",
      "code": "4520"
    },
    {
      "description": "Sale of motor vehicle parts and accessories",
      "code": "4530"
    },
    {
      "description": "Sale, maintenance and repair of motorcycles and related parts and accessories",
      "code": "4540"
    },
    {
      "description": "Wholesale on a fee or contract basis",
      "code": "4610"
    },
    {
      "description": "Wholesale of agricultural raw materials and live animals",
      "code": "4620"
    },
    {
      "description": "Wholesale of food, beverages and tobacco",
      "code": "4630"
    },
    {
      "description": "Wholesale of textiles, clothing and footwear",
      "code": "4641"
    },
    {
      "description": "Wholesale of other household goods",
      "code": "4649"
    },
    {
      "description": "Wholesale of computers, computer peripheral equipment and software",
      "code": "4651"
    },
    {
      "description": "Wholesale of electronic and telecommunications equipment and parts",
      "code": "4652"
    },
    {
      "description": "Wholesale of agricultural machinery, equipment and supplies",
      "code": "4653"
    },
    {
      "description": "Wholesale of other machinery and equipment",
      "code": "4659"
    },
    {
      "description": "Wholesale of solid, liquid and gaseous fuels and related products",
      "code": "4661"
    },
    {
      "description": "Wholesale of metals and metal ores",
      "code": "4662"
    },
    {
      "description": "Wholesale of construction materials, hardware, plumbing and heating equipment and supplies",
      "code": "4663"
    },
    {
      "description": "Wholesale of waste and scrap and other products n.e.c.",
      "code": "4669"
    },
    {
      "description": "Non-specialized wholesale trade",
      "code": "4690"
    },
    {
      "description": "Retail sale in non-specialized stores with food, beverages or tobacco predominating",
      "code": "4711"
    },
    {
      "description": "Other retail sale in non-specialized stores",
      "code": "4719"
    },
    {
      "description": "Retail sale of food in specialized stores",
      "code": "4721"
    },
    {
      "description": "Retail sale of beverages in specialized stores",
      "code": "4722"
    },
    {
      "description": "Retail sale of tobacco products in specialized stores",
      "code": "4723"
    },
    {
      "description": "Retail sale of automotive fuel in specialized stores",
      "code": "4730"
    },
    {
      "description": "Retail sale of computers, peripheral units, software and telecommunications equipment in specialized stores",
      "code": "4741"
    },
    {
      "description": "Retail sale of audio and video equipment in specialized stores",
      "code": "4742"
    },
    {
      "description": "Retail sale of textiles in specialized stores",
      "code": "4751"
    },
    {
      "description": "Retail sale of hardware, paints and glass in specialized stores",
      "code": "4752"
    },
    {
      "description": "Retail sale of carpets, rugs, wall and floor coverings in specialized stores",
      "code": "4753"
    },
    {
      "description": "Retail sale of electrical household appliances, furniture, lighting equipment and other household articles in specialized stores",
      "code": "4759"
    },
    {
      "description": "Retail sale of books, newspapers and stationary in specialized stores",
      "code": "4761"
    },
    {
      "description": "Retail sale of music and video recordings in specialized stores",
      "code": "4762"
    },
    {
      "description": "Retail sale of sporting equipment in specialized stores",
      "code": "4763"
    },
    {
      "description": "Retail sale of games and toys in specialized stores",
      "code": "4764"
    },
    {
      "description": "Retail sale of clothing, footwear and leather articles in specialized stores",
      "code": "4771"
    },
    {
      "description": "Retail sale of pharmaceutical and medical goods, cosmetic and toilet articles in specialized stores",
      "code": "4772"
    },
    {
      "description": "Other retail sale of new goods in specialized stores",
      "code": "4773"
    },
    {
      "description": "Retail sale of second-hand goods",
      "code": "4774"
    },
    {
      "description": "Retail sale via stalls and markets of food, beverages and tobacco products",
      "code": "4781"
    },
    {
      "description": "Retail sale via stalls and markets of textiles, clothing and footwear",
      "code": "4782"
    },
    {
      "description": "Retail sale via stalls and markets of other goods",
      "code": "4789"
    },
    {
      "description": "Retail sale via mail order houses or via Internet",
      "code": "4791"
    },
    {
      "description": "Other retail sale not in stores, stalls or markets",
      "code": "4799"
    },
    {
      "description": "Passenger rail transport, interurban",
      "code": "4911"
    },
    {
      "description": "Freight rail transport",
      "code": "4912"
    },
    {
      "description": "Urban and suburban passenger land transport",
      "code": "4921"
    },
    {
      "description": "Other passenger land transport",
      "code": "4922"
    },
    {
      "description": "Freight transport by road",
      "code": "4923"
    },
    {
      "description": "Transport via pipeline",
      "code": "4930"
    },
    {
      "description": "Sea and coastal passenger water transport",
      "code": "5011"
    },
    {
      "description": "Sea and coastal freight water transport",
      "code": "5012"
    },
    {
      "description": "Inland passenger water transport",
      "code": "5021"
    },
    {
      "description": "Inland freight water transport",
      "code": "5022"
    },
    {
      "description": "Passenger air transport",
      "code": "5110"
    },
    {
      "description": "Freight air transport",
      "code": "5120"
    },
    {
      "description": "Warehousing and storage",
      "code": "5210"
    },
    {
      "description": "Service activities incidental to land transportation",
      "code": "5221"
    },
    {
      "description": "Service activities incidental to water transportation",
      "code": "5222"
    },
    {
      "description": "Service activities incidental to air transportation",
      "code": "5223"
    },
    {
      "description": "Cargo handling",
      "code": "5224"
    },
    {
      "description": "Other transportation support activities",
      "code": "5229"
    },
    {
      "description": "Postal activities",
      "code": "5310"
    },
    {
      "description": "Courier activities",
      "code": "5320"
    },
    {
      "description": "Short term accommodation activities",
      "code": "5510"
    },
    {
      "description": "Camping grounds, recreational vehicle parks and trailer parks",
      "code": "5520"
    },
    {
      "description": "Other accommodation",
      "code": "5590"
    },
    {
      "description": "Restaurants and mobile food service activities",
      "code": "5610"
    },
    {
      "description": "Event catering",
      "code": "5621"
    },
    {
      "description": "Other food service activities",
      "code": "5629"
    },
    {
      "description": "Beverage serving activities",
      "code": "5630"
    },
    {
      "description": "Book publishing",
      "code": "5811"
    },
    {
      "description": "Publishing of directories and mailing lists",
      "code": "5812"
    },
    {
      "description": "Publishing of newspapers, journals and periodicals",
      "code": "5813"
    },
    {
      "description": "Other publishing activities",
      "code": "5819"
    },
    {
      "description": "Software publishing",
      "code": "5820"
    },
    {
      "description": "Motion picture, video and television programme production activities",
      "code": "5911"
    },
    {
      "description": "Motion picture, video and television programme post-production activities",
      "code": "5912"
    },
    {
      "description": "Motion picture, video and television programme distribution activities",
      "code": "5913"
    },
    {
      "description": "Motion picture projection activities",
      "code": "5914"
    },
    {
      "description": "Sound recording and music publishing activities",
      "code": "5920"
    },
    {
      "description": "Radio broadcasting",
      "code": "6010"
    },
    {
      "description": "Television programming and broadcasting activities",
      "code": "6020"
    },
    {
      "description": "Wired telecommunications activities",
      "code": "6110"
    },
    {
      "description": "Wireless telecommunications activities",
      "code": "6120"
    },
    {
      "description": "Satellite telecommunications activities",
      "code": "6130"
    },
    {
      "description": "Other telecommunications activities",
      "code": "6190"
    },
    {
      "description": "Computer programming activities",
      "code": "6201"
    },
    {
      "description": "Computer consultancy and computer facilities management activities",
      "code": "6202"
    },
    {
      "description": "Other information technology and computer service activities",
      "code": "6209"
    },
    {
      "description": "Data processing, hosting and related activities",
      "code": "6311"
    },
    {
      "description": "Web portals",
      "code": "6312"
    },
    {
      "description": "News agency activities",
      "code": "6391"
    },
    {
      "description": "Other information service activities n.e.c.",
      "code": "6399"
    },
    {
      "description": "Central banking",
      "code": "6411"
    },
    {
      "description": "Other monetary intermediation",
      "code": "6419"
    },
    {
      "description": "Activities of holding companies",
      "code": "6420"
    },
    {
      "description": "Trusts, funds and similar financial entities",
      "code": "6430"
    },
    {
      "description": "Financial leasing",
      "code": "6491"
    },
    {
      "description": "Other credit granting",
      "code": "6492"
    },
    {
      "description": "Other financial service activities, except insurance and pension funding activities, n.e.c.",
      "code": "6499"
    },
    {
      "description": "Life insurance",
      "code": "6511"
    },
    {
      "description": "Non-life insurance",
      "code": "6512"
    },
    {
      "description": "Reinsurance",
      "code": "6520"
    },
    {
      "description": "Pension funding",
      "code": "6530"
    },
    {
      "description": "Administration of financial markets",
      "code": "6611"
    },
    {
      "description": "Security and commodity contracts brokerage",
      "code": "6612"
    },
    {
      "description": "Other activities auxiliary to financial service activities",
      "code": "6619"
    },
    {
      "description": "Risk and damage evaluation",
      "code": "6621"
    },
    {
      "description": "Activities of insurance agents and brokers",
      "code": "6622"
    },
    {
      "description": "Other activities auxiliary to insurance and pension funding",
      "code": "6629"
    },
    {
      "description": "Fund management activities",
      "code": "6630"
    },
    {
      "description": "Real estate activities with own or leased property",
      "code": "6810"
    },
    {
      "description": "Real estate activities on a fee or contract basis",
      "code": "6820"
    },
    {
      "description": "Legal activities",
      "code": "6910"
    },
    {
      "description": "Accounting, bookkeeping and auditing activities; tax consultancy",
      "code": "6920"
    },
    {
      "description": "Activities of head offices",
      "code": "7010"
    },
    {
      "description": "Management consultancy activities",
      "code": "7020"
    },
    {
      "description": "Architectural and engineering activities and related technical consultancy",
      "code": "7110"
    },
    {
      "description": "Technical testing and analysis",
      "code": "7120"
    },
    {
      "description": "Research and experimental development on natural sciences and engineering",
      "code": "7210"
    },
    {
      "description": "Research and experimental development on social sciences and humanities",
      "code": "7220"
    },
    {
      "description": "Advertising",
      "code": "7310"
    },
    {
      "description": "Market research and public opinion polling",
      "code": "7320"
    },
    {
      "description": "Specialized design activities",
      "code": "7410"
    },
    {
      "description": "Photographic activities",
      "code": "7420"
    },
    {
      "description": "Other professional, scientific and technical activities n.e.c.",
      "code": "7490"
    },
    {
      "description": "Veterinary activities",
      "code": "7500"
    },
    {
      "description": "Renting and leasing of motor vehicles",
      "code": "7710"
    },
    {
      "description": "Renting and leasing of recreational and sports goods",
      "code": "7721"
    },
    {
      "description": "Renting of video tapes and disks",
      "code": "7722"
    },
    {
      "description": "Renting and leasing of other personal and household goods",
      "code": "7729"
    },
    {
      "description": "Renting and leasing of other machinery, equipment and tangible goods",
      "code": "7730"
    },
    {
      "description": "Leasing of intellectual property and similar products, except copyrighted works",
      "code": "7740"
    },
    {
      "description": "Activities of employment placement agencies",
      "code": "7810"
    },
    {
      "description": "Temporary employment agency activities",
      "code": "7820"
    },
    {
      "description": "Other human resources provision",
      "code": "7830"
    },
    {
      "description": "Travel agency activities",
      "code": "7911"
    },
    {
      "description": "Tour operator activities",
      "code": "7912"
    },
    {
      "description": "Other reservation service and related activities",
      "code": "7990"
    },
    {
      "description": "Private security activities",
      "code": "8010"
    },
    {
      "description": "Security systems service activities",
      "code": "8020"
    },
    {
      "description": "Investigation activities",
      "code": "8030"
    },
    {
      "description": "Combined facilities support activities",
      "code": "8110"
    },
    {
      "description": "General cleaning of buildings",
      "code": "8121"
    },
    {
      "description": "Other building and industrial cleaning activities",
      "code": "8129"
    },
    {
      "description": "Landscape care and maintenance service activities",
      "code": "8130"
    },
    {
      "description": "Combined office administrative service activities",
      "code": "8211"
    },
    {
      "description": "Photocopying, document preparation and other specialized office support activities",
      "code": "8219"
    },
    {
      "description": "Activities of call centres",
      "code": "8220"
    },
    {
      "description": "Organization of conventions and trade shows",
      "code": "8230"
    },
    {
      "description": "Activities of collection agencies and credit bureaus",
      "code": "8291"
    },
    {
      "description": "Packaging activities",
      "code": "8292"
    },
    {
      "description": "Other business support service activities n.e.c.",
      "code": "8299"
    },
    {
      "description": "General public administration activities",
      "code": "8411"
    },
    {
      "description": "Regulation of the activities of providing health care, education, cultural services and other social services, excluding social security",
      "code": "8412"
    },
    {
      "description": "Regulation of and contribution to more efficient operation of businesses",
      "code": "8413"
    },
    {
      "description": "Foreign affairs",
      "code": "8421"
    },
    {
      "description": "Defence activities",
      "code": "8422"
    },
    {
      "description": "Public order and safety activities",
      "code": "8423"
    },
    {
      "description": "Compulsory social security activities",
      "code": "8430"
    },
    {
      "description": "Pre-primary and primary education",
      "code": "8510"
    },
    {
      "description": "General secondary education",
      "code": "8521"
    },
    {
      "description": "Technical and vocational secondary education",
      "code": "8522"
    },
    {
      "description": "Higher education",
      "code": "8530"
    },
    {
      "description": "Sports and recreation education",
      "code": "8541"
    },
    {
      "description": "Cultural education",
      "code": "8542"
    },
    {
      "description": "Other education n.e.c.",
      "code": "8549"
    },
    {
      "description": "Educational support activities",
      "code": "8550"
    },
    {
      "description": "Hospital activities",
      "code": "8610"
    },
    {
      "description": "Medical and dental practice activities",
      "code": "8620"
    },
    {
      "description": "Other human health activities",
      "code": "8690"
    },
    {
      "description": "Residential nursing care facilities",
      "code": "8710"
    },
    {
      "description": "Residential care activities for mental retardation, mental health and substance abuse",
      "code": "8720"
    },
    {
      "description": "Residential care activities for the elderly and disabled",
      "code": "8730"
    },
    {
      "description": "Other residential care activities",
      "code": "8790"
    },
    {
      "description": "Social work activities without accommodation for the elderly and disabled",
      "code": "8810"
    },
    {
      "description": "Other social work activities without accommodation",
      "code": "8890"
    },
    {
      "description": "Creative, arts and entertainment activities",
      "code": "9000"
    },
    {
      "description": "Library and archives activities",
      "code": "9101"
    },
    {
      "description": "Museums activities and operation of historical sites and buildings",
      "code": "9102"
    },
    {
      "description": "Botanical and zoological gardens and nature reserves activities",
      "code": "9103"
    },
    {
      "description": "Gambling and betting activities",
      "code": "9200"
    },
    {
      "description": "Operation of sports facilities",
      "code": "9311"
    },
    {
      "description": "Activities of sports clubs",
      "code": "9312"
    },
    {
      "description": "Other sports activities",
      "code": "9319"
    },
    {
      "description": "Activities of amusement parks and theme parks",
      "code": "9321"
    },
    {
      "description": "Other amusement and recreation activities n.e.c.",
      "code": "9329"
    },
    {
      "description": "Activities of business and employers membership organizations",
      "code": "9411"
    },
    {
      "description": "Activities of professional membership organizations",
      "code": "9412"
    },
    {
      "description": "Activities of trade unions",
      "code": "9420"
    },
    {
      "description": "Activities of religious organizations",
      "code": "9491"
    },
    {
      "description": "Activities of political organizations",
      "code": "9492"
    },
    {
      "description": "Activities of other membership organizations n.e.c.",
      "code": "9499"
    },
    {
      "description": "Repair of computers and peripheral equipment",
      "code": "9511"
    },
    {
      "description": "Repair of communication equipment",
      "code": "9512"
    },
    {
      "description": "Repair of consumer electronics",
      "code": "9521"
    },
    {
      "description": "Repair of household appliances and home and garden equipment",
      "code": "9522"
    },
    {
      "description": "Repair of footwear and leather goods",
      "code": "9523"
    },
    {
      "description": "Repair of furniture and home furnishings",
      "code": "9524"
    },
    {
      "description": "Repair of other personal and household goods",
      "code": "9529"
    },
    {
      "description": "Washing and (dry-) cleaning of textile and fur products",
      "code": "9601"
    },
    {
      "description": "Hairdressing and other beauty treatment",
      "code": "9602"
    },
    {
      "description": "Funeral and related activities",
      "code": "9603"
    },
    {
      "description": "Other personal service activities n.e.c.",
      "code": "9609"
    },
    {
      "description": "Activities of households as employers of domestic personnel",
      "code": "9700"
    },
    {
      "description": "Undifferentiated goods-producing activities of private households for own use",
      "code": "9810"
    },
    {
      "description": "Undifferentiated service-producing activities of private households for own use",
      "code": "9820"
    },
    {
      "description": "Activities of extraterritorial organizations and bodies",
      "code": "9900"
    }
  ]
}

    - Response headers
     cache-control: private 
     content-type: application/json; charset=utf-8 
     last-modified: Wed,21 May 2025 14:11:15 GMT 

- Responses
**Code**            **Description**             **Links**
200