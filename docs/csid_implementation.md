# CSID (Cryptographic Stamp ID) Implementation

## Overview

This document details the implementation of the Cryptographic Stamp ID (CSID) system for the TaxPoynt eInvoice platform, designed to meet FIRS e-invoicing requirements for cryptographic signing and verification of electronic invoices.

**Date:** May 16, 2025

## Introduction to CSID

The Cryptographic Stamp ID (CSID) is a tamper-proof digital signature that provides cryptographic evidence of:

1. **Invoice Authenticity**: Proof that the invoice was issued by the claimed entity
2. **Invoice Integrity**: Verification that the invoice content has not been altered
3. **Non-repudiation**: Evidence that cannot be denied by the issuer
4. **Compliance**: Fulfillment of FIRS e-invoicing security requirements

## Implementation Architecture

The CSID implementation consists of three primary components:

### 1. Key Management System (`app/utils/key_management.py`)

The key management system provides:

- **Key Generation**: Secure creation of cryptographic keys (RSA, Ed25519)
- **Key Storage**: Secure storage with proper file permissions
- **Key Rotation**: Automated key lifecycle management
- **Certificate Generation**: Self-signed X.509 certificates for key verification

### 2. CSID Generator (`app/utils/crypto_signing.py`)

The core CSID implementation includes:

- **CSIDGenerator Class**: Handles all aspects of CSID creation and verification
- **Multiple Algorithm Support**: RSA-PSS-SHA256, RSA-PKCS1-SHA256, ED25519
- **Versioned CSID Format**: Support for v1.0 (legacy) and v2.0 (enhanced)
- **Canonical Data Representation**: Ensures consistent hashing across systems

### 3. Signing Service Integration

Integration points with the broader invoice processing system:

- **Invoice Signing**: Simple API for adding CSID to invoices
- **Verification Workflow**: Validation of signed invoices
- **UBL Integration**: Compatible with the Odoo to BIS Billing 3.0 UBL mapping

## CSID Format Specification

The CSID is encoded as a Base64 string that contains a JSON structure with signature information.

### Version 1.0 (Legacy)

```json
{
  "csid": "<base64-encoded-signature>",
  "timestamp": 1621172409,
  "algorithm": "RSA-PSS-SHA256"
}
```

### Version 2.0 (Enhanced FIRS Compliance)

```json
{
  "version": "2.0",
  "signature_value": "<base64-encoded-signature>",
  "signature_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-05-16T09:13:07+01:00",
  "algorithm": "RSA-PSS-SHA256",
  "key_info": {
    "key_id": "signing_rsa-2048_20250516091307.key",
    "certificate": "signing_cert_20250516091307.crt"
  },
  "invoice_ref": {
    "id": "INV2025001",
    "hash_alg": "SHA-256",
    "hash_value": "<base64-encoded-hash>"
  }
}
```

## Supported Algorithms

| Algorithm ID | Description | Security Level | Use Case |
|--------------|-------------|---------------|----------|
| RSA-PSS-SHA256 | RSA with PSS padding, SHA-256 hash | High | Standard digital signatures |
| RSA-PKCS1-SHA256 | RSA with PKCS#1 padding, SHA-256 hash | High | Legacy system compatibility |
| ED25519 | Edwards-curve Digital Signature | Very High | High-security applications |

## Key Management

### Key Generation

Keys are generated with appropriate security parameters:

```python
# Generate RSA key pair
private_key_path, public_key_path = key_manager.generate_key_pair(
    key_type="signing",
    algorithm="rsa-2048"
)
```

### Key Storage

Keys are stored securely with appropriate permissions:

- Private keys: 0600 (read/write for owner only)
- Public keys: 0644 (read for all, write for owner)
- Keys directory: Configured via settings or environment variables

### Key Rotation

Keys can be rotated periodically to maintain security:

```python
# Rotate an existing key
new_key_path, archived_key_path = key_manager.rotate_key(
    key_path="/path/to/old/key.key"
)
```

### Certificate Management

Self-signed certificates are generated for key verification:

```python
# Generate a certificate for a key
cert_path = key_manager.generate_certificate(
    private_key_path="/path/to/private.key",
    subject_name={
        "country": "NG",
        "organization": "Company Name",
        "common_name": "company.com"
    },
    valid_days=365
)
```

## Signing Process

The signing process follows these steps:

1. **Canonical Representation**: The invoice data is converted to a canonical JSON format with sorted keys and consistent formatting to ensure reproducible hashing.

2. **Hash Calculation**: A SHA-256 hash is computed from the canonical representation.

3. **Digital Signature**: The hash is signed using the private key and chosen algorithm.

4. **CSID Creation**: A CSID structure is created with the signature, timestamp, and metadata.

5. **Encoding**: The CSID is encoded as Base64 for compact representation.

6. **Invoice Attachment**: The CSID is attached to the invoice in the `cryptographic_stamp` field.

```python
# Sign an invoice
signed_invoice = sign_invoice(
    invoice_data,
    version=CSIDVersion.V2_0,
    algorithm=SigningAlgorithm.RSA_PSS_SHA256
)
```

## Verification Process

The verification process mirrors the signing process:

1. **CSID Decoding**: The Base64-encoded CSID is decoded and parsed.

2. **Key Retrieval**: The public key is retrieved, either from a file or from a certificate.

3. **Canonical Representation**: The invoice data is converted to the same canonical format.

4. **Hash Calculation**: The SHA-256 hash is computed from the canonical representation.

5. **Signature Verification**: The digital signature is verified against the hash using the public key.

6. **Optional Hash Verification**: For V2.0, the stored hash is compared with the calculated hash.

```python
# Verify a signed invoice
is_valid, message, details = verify_csid(
    invoice_data,
    csid,
    public_key_path="/path/to/public.key"
)
```

## Integration with Invoice Processing

The CSID system integrates with the invoice processing workflow:

### Adding CSID to an Invoice

```python
from app.utils.crypto_signing import sign_invoice

# Original invoice data
invoice_data = {
    "invoice_number": "INV2025001",
    "invoice_date": "2025-05-16",
    # ... other invoice fields
}

# Sign the invoice
signed_invoice = sign_invoice(invoice_data)

# The signed_invoice now contains a cryptographic_stamp field
```

### Verifying an Invoice CSID

```python
from app.utils.crypto_signing import verify_csid

# Check if the CSID is valid
is_valid, message, details = verify_csid(
    invoice_data,
    invoice_data["cryptographic_stamp"]["csid"]
)

if is_valid:
    print("Invoice is authentic and has not been tampered with")
else:
    print(f"Invoice verification failed: {message}")
```

## Security Considerations

1. **Private Key Protection**: Private keys must never leave the server and should be stored with appropriate permissions.

2. **Key Rotation Schedule**: Keys should be rotated periodically (e.g., annually) to limit the impact of potential key compromise.

3. **Algorithm Selection**: Use RSA-PSS-SHA256 as the default, but allow for future algorithm upgrades.

4. **Timestamp Validation**: When verifying signatures, consider the timestamp to prevent replay attacks.

5. **Certificate Validation**: For enhanced security, implement certificate validation against a trusted root.

## Testing

A comprehensive test suite is provided in `backend/tests/test_crypto_signing.py`:

```bash
# Run CSID tests
python -m backend.tests.test_crypto_signing
```

The test suite covers:
- Key generation and loading
- CSID generation with different versions and algorithms
- Invoice signing and verification
- Tampered invoice detection

## Integration with UBL

The CSID implementation is designed to work with the Odoo to BIS Billing 3.0 UBL mapping system:

1. **UBL Signature Field**: The CSID can be mapped to the UBL `SignatureInformation` field.

2. **Certificate References**: The certificate information can be included in the UBL `CertificateReference` element.

3. **Signature Method**: The algorithm is mapped to the UBL `SignatureMethod` element.

## Best Practices

1. **Always verify before trusting**: Always verify CSID before accepting an invoice as authentic.

2. **Keep keys secure**: Implement proper access controls for cryptographic keys.

3. **Use Version 2.0**: The enhanced CSID format provides better security and more information.

4. **Log verification attempts**: Maintain an audit trail of verification attempts for forensic analysis.

5. **Regular key rotation**: Implement a regular key rotation schedule to maintain security.

---

## Appendix: FIRS Compliance Checklist

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| Digital signature of invoice content | CSID with RSA or ED25519 | ✅ |
| Timestamping | ISO 8601 timestamp in CSID | ✅ |
| Hash verification | SHA-256 with stored hash | ✅ |
| Key management | Secure key generation and storage | ✅ |
| Non-repudiation | Cryptographic signing with private key | ✅ |
| Tampering detection | Hash comparison | ✅ |
| Certificate support | X.509 certificate generation | ✅ |
