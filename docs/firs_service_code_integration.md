# FIRS Service Code Integration

## Overview

This document summarizes the implementation of FIRS service code integration into the TaxPoynt eInvoice system. Service codes are required by the Federal Inland Revenue Service (FIRS) for proper classification of goods and services in electronic invoices. This implementation enhances the existing integration by adding service code support to the Odoo-to-FIRS transformation pipeline.

## Implementation Date

May 26, 2025

## Components

The integration consists of four main components:

1. **FIRS API Service Code Endpoint Integration**
2. **Odoo-FIRS Service Code Mapper**
3. **Odoo UBL Transformer Enhancement**
4. **Service Code Validation**

## Technical Implementation

### 1. FIRS API Service Code Endpoint

We implemented the `get_service_codes` method in the existing `FIRSService` class to retrieve service codes from the FIRS API:

```python
async def get_service_codes(self) -> List[Dict[str, Any]]:
    """Get list of service codes from FIRS API."""
    try:
        # Try to load from reference file first
        try:
            service_codes_file = os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'service_codes.json')
            if os.path.exists(service_codes_file):
                with open(service_codes_file, 'r') as f:
                    service_codes_data = json.load(f)
                    return service_codes_data.get('service_codes', [])
        except Exception as file_err:
            logger.warning(f"Could not load service codes from file: {str(file_err)}")
        
        # Fall back to API call
        url = f"{self.base_url}{self.endpoints['service_codes']}"
        response = requests.get(url, headers=self._get_default_headers(), timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            service_codes = result.get("data", [])
            
            # Cache for future use
            os.makedirs(os.path.dirname(service_codes_file), exist_ok=True)
            with open(service_codes_file, 'w') as f:
                json.dump({"service_codes": service_codes, "metadata": {
                    "retrieved_at": datetime.now().isoformat()
                }}, f, indent=2)
            
            return service_codes
        else:
            # Handle error
            raise HTTPException(...)
    except Exception as e:
        logger.error(f"Error retrieving service codes: {str(e)}")
        raise
```

Testing confirmed the endpoint successfully retrieves 419 service codes from the FIRS API.

### 2. Odoo-FIRS Service Code Mapper

A new service was created to map Odoo product categories to FIRS service codes:

```python
class OdooFIRSServiceCodeMapper:
    """Maps Odoo product categories to FIRS service codes."""
    
    async def suggest_service_code(
        self, 
        product_name: str, 
        category: str = "", 
        description: str = ""
    ) -> Optional[Dict[str, Any]]:
        """Suggest the best matching FIRS service code for an Odoo product."""
        # Implementation uses text similarity matching
        # and maintains custom mappings for frequent categories
```

Key features:
- Intelligent matching using text similarity algorithms
- Category mapping persistence
- Caching for performance
- Confidence scoring for suggested mappings

### 3. Odoo UBL Transformer Enhancement

The existing Odoo UBL mapper was updated to incorporate service code mapping:

```python
async def _map_invoice_lines_async(self, odoo_lines: List[Dict[str, Any]]) -> List[InvoiceLine]:
    """Map Odoo invoice lines to UBL invoice lines with service codes."""
    for i, line in enumerate(odoo_lines):
        # Existing code...
        
        # New service code mapping
        service_code = None
        try:
            service_code_data = await odoo_firs_service_code_mapper.suggest_service_code(
                product_name=product_name,
                category=product_category,
                description=product_description
            )
            
            if service_code_data and service_code_data.get("confidence", 0) > 0.4:
                service_code = service_code_data.get("code")
        except Exception as e:
            logger.warning(f"Error mapping service code: {str(e)}")
        
        # Create invoice line with service code
        ubl_line = InvoiceLine(
            # Existing fields...
            service_code=service_code,
            # More fields...
        )
```

### 4. Service Code Validation

A new validation service ensures that service codes meet FIRS requirements:

```python
class InvoiceServiceCodeValidator:
    """Validates service codes in invoices against FIRS requirements."""
    
    async def validate_service_codes(
        self, 
        invoice: InvoiceValidationRequest
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate service codes in an invoice."""
        # Implementation checks if codes are valid
        # and suggests alternatives for invalid codes
```

### 5. Schema Updates

The `InvoiceLine` schema was updated to include the service code field:

```python
class InvoiceLine(BaseModel):
    """Invoice line according to BIS Billing 3.0"""
    # Existing fields...
    service_code: Optional[str] = Field(
        None, 
        max_length=10, 
        description="FIRS service code for classification"
    )
    # More fields...
```

## Integration with Existing Architecture

This implementation integrates with the existing TaxPoynt eInvoice architecture:

1. **ERP-First Strategy**: Enhances the Odoo integration by providing intelligent mapping between Odoo product categories and FIRS service codes.

2. **Layered Architecture**:
   - Data layer: Added service code reference data
   - Service layer: Added mapping and validation services
   - Schema layer: Updated invoice schema to include service codes

3. **API Functionality**: Leverages the existing FIRS API connector to add service code support without duplicating code.

## Benefits

1. **Compliance**: Ensures invoices meet FIRS requirements for service code classification.

2. **Automation**: Reduces manual effort by intelligently suggesting appropriate service codes.

3. **Data Quality**: Validates service codes to prevent submission of invalid data.

4. **Caching**: Minimizes API calls by caching service codes and mappings.

5. **Backward Compatibility**: Maintains compatibility with existing code through careful design.

## Testing Results

Testing with real FIRS API data confirmed:

- Successful retrieval of 419 service codes
- Accurate mapping of test product categories
- Proper validation of service codes
- Seamless integration with the existing invoice processing pipeline

## Future Enhancements

1. **UI Integration**:
   - Add service code management to the FIRS Testing Dashboard
   - Create a mapping management interface for administrative users

2. **API Endpoints**:
   - Add endpoints for service code suggestions and validation
   - Create batch mapping functionality for existing products

3. **Reporting**:
   - Add service code distribution analytics
   - Track mapping confidence metrics

4. **Advanced Matching**:
   - Implement machine learning for improved mapping suggestions
   - Add support for industry-specific mapping rules

## Conclusion

The FIRS service code integration enhances the TaxPoynt eInvoice system by adding comprehensive support for service code classification in invoices. This implementation meets FIRS requirements while maintaining the system's ERP-first integration strategy and preserving backward compatibility.
