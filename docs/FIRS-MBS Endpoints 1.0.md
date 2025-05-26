# FIRS-MBS Endpoints 1.0.0

## HealthCheck

1. **GET - /api - HealthCheck**

## Search Entity And Business

2. **GET - /api/v1/entity - SearchEntity** _Search for entity using parameters_

3. **GET - /api/v1/entity/{ENTITY_ID} - GetEntity** _Fetch an entity using entity ID_

## Manage E-Invoice

4. **POST - /api/v1/invoice/irn/validate - ValidateIRN**

5. **POST - /api/v1/invoice/validate - ValidateInvoice**

6. **POST - /api/v1/invoice/sign - SignInvoice**

7. **POST - /api/v1/invoice/party - CreateParty**

8. **GET - /api/v1/invoice/party/{BUSINESS_ID} - SearchParty**

9. **GET - /api/v1/invoice/confirm/{IRN} - ConfirmInvoice**

10. **GET - /api/v1/invoice/download/{IRN} - DownloadInvoice**

11. **GET - /api/v1/invoice/{BUSINESS_ID} - SearchInvoice**

12. **PATCH - /api/v1/invoice/update/{IRN} - UpdateInvoice**

## Exchange E-Invoice

13. **GET - /api/v1/invoice/transmit/lookup/{IRN} - LookupWithIRN**

14. **GET - /api/v1/invoice/transmit/lookup/tin/{PARTY_ID} - LookupWithTIN**

15. **GET - /api/v1/invoice/transmit/lookup/party/{PARTY_ID} - LookupWithPartyID**

16. **POST - /api/v1/invoice/transmit/{IRN} - Transmit**

17. **PATCH - /api/v1/invoice/transmit/{IRN} - ConfirmReceipt**

18. **GET - /api/v1/invoice/transmit/self-health-check - SelfCheck-Debug-Setup**

19. **GET - /api/v1/invoice/transmit/pull - Pull**

## Report E-Invoice

20. **POST - /v1/vat/postPayment - Post transaction**

## Utilities
Utilities are endpoints that provides additional functionalities around e-invoice and third-party services.

21. **POST - /api/v1/utilities/verify-tin/ - VerifyTin**

22. **POST - /api/v1/utilities/authenticate - AuthenticateTaxPayer**

## Resources
This section provides endpoints to retrieve utility data.

23. **GET - /api/v1/invoice/resources/countries - GetCountries**

24. **GET - /api/v1/invoice/resources/invoice-types - GetInvoiceTypes**

25. **GET - /api/v1/invoice/resources/currencies - GetCurrencies**

26. **GET - /api/v1/invoice/resources/vat-exemptions - GetVatExemptions**

27. **GET - /api/v1/invoice/resources/services-codes - GetServicesCodes**




