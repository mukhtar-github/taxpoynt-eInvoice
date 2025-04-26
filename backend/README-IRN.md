# Invoice Reference Number (IRN) Generation

This module implements the FIRS-compliant Invoice Reference Number generation system.

## IRN Format

The IRN follows the format specified by FIRS:

```
InvoiceNumber-ServiceID-YYYYMMDD
```

Where:
- **InvoiceNumber**: Alphanumeric identifier from the taxpayer's accounting system (no special characters)
- **ServiceID**: 8-character alphanumeric identifier assigned by FIRS
- **YYYYMMDD**: Date in the specified format

Example: `INV001-94ND90NR-20240611`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /irn/generate | Generate a single IRN |
| POST | /irn/generate-batch | Generate multiple IRNs in batch |
| GET | /irn/{irn} | Validate and get IRN details |
| GET | /irn | List IRNs with filtering options |
| POST | /irn/{irn}/status | Update IRN status |
| GET | /irn/metrics | Get IRN usage metrics |

## Implementation Details

### 1. Validation
IRN components are validated according to FIRS requirements:
- Invoice number: Alphanumeric, no special characters
- Service ID: 8-character alphanumeric
- Timestamp: YYYYMMDD format

### 2. Storage
IRNs are stored in the database with the following attributes:
- IRN value
- Associated integration
- Invoice number
- Service ID
- Timestamp
- Generation date
- Expiration date
- Status (unused, used, expired)

### 3. Lifecycle
- IRNs are generated with "unused" status
- When used for an invoice, status changes to "used"
- IRNs expire after a configurable period (default: 7 days)

## Testing

Run the tests for IRN generation:

```
pytest app/tests/test_irn_generation.py -v
```

## Future Enhancements

- Integrate with client's accounting systems to automate IRN assignment
- Implement IRN quota management
- Add QR code generation for IRNs
- Integrate with FIRS API for real-time validation 