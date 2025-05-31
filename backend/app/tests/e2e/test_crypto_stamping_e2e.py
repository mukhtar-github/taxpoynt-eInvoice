"""
End-to-end test for the FIRS cryptographic stamping workflow.

This script demonstrates the complete flow:
1. Create test certificates
2. Generate cryptographic stamps for invoices
3. Verify the stamps
4. Test QR code generation and verification

Run this script with: pytest -xvs app/tests/e2e/test_crypto_stamping_e2e.py
"""
import os
import base64
import tempfile
import pytest
import json
from datetime import datetime

from app.utils.certificate_manager import CertificateManager
from app.utils.key_management import KeyManager
from app.services.cryptographic_stamping_service import CryptographicStampingService


@pytest.fixture
def test_environment():
    """Set up a test environment with temporary directories."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create subdirectories
        certs_dir = os.path.join(tmp_dir, "certificates")
        keys_dir = os.path.join(tmp_dir, "keys")
        os.makedirs(certs_dir, exist_ok=True)
        os.makedirs(keys_dir, exist_ok=True)
        
        # Initialize components
        key_manager = KeyManager(keys_dir=keys_dir)
        certificate_manager = CertificateManager(certs_dir=certs_dir)
        
        # Return the test environment
        yield {
            "temp_dir": tmp_dir,
            "certs_dir": certs_dir,
            "keys_dir": keys_dir,
            "key_manager": key_manager,
            "certificate_manager": certificate_manager
        }


@pytest.fixture
def test_invoice_data():
    """Sample invoice data for testing."""
    return {
        "invoice_number": "INV-2023-001",
        "date": "2023-10-15",
        "seller": {
            "name": "Test Company Ltd",
            "tax_id": "12345678901",
            "address": "123 Test Street, Lagos"
        },
        "buyer": {
            "name": "Test Customer",
            "tax_id": "98765432109",
            "address": "456 Sample Road, Abuja"
        },
        "items": [
            {
                "description": "Test Product 1",
                "quantity": 2,
                "unit_price": 5000.00,
                "total": 10000.00,
                "tax_rate": 7.5
            },
            {
                "description": "Test Service",
                "quantity": 1,
                "unit_price": 20000.00,
                "total": 20000.00,
                "tax_rate": 7.5
            }
        ],
        "total_amount": 30000.00,
        "total_tax": 2250.00,
        "currency": "NGN"
    }


def test_complete_stamping_flow(test_environment, test_invoice_data):
    """Test the complete cryptographic stamping flow."""
    key_manager = test_environment["key_manager"]
    certificate_manager = test_environment["certificate_manager"]
    
    # Step 1: Generate a self-signed certificate for testing
    print("\n1. Generating self-signed certificate...")
    cert_path, key_path = certificate_manager.create_self_signed_certificate(
        common_name="taxpoynt-test.ng",
        organization="TaxPoynt Test",
        country="NG",
        validity_days=365
    )
    
    # Validate the certificate
    is_valid, cert_info = certificate_manager.validate_certificate(cert_path)
    print(f"   Certificate valid: {is_valid}")
    print(f"   Subject: {cert_info.get('subject', {}).get('commonName')}")
    print(f"   Issuer: {cert_info.get('issuer', {}).get('commonName')}")
    print(f"   Valid until: {cert_info.get('valid_until')}")
    
    assert is_valid, "Certificate should be valid"
    
    # Step 2: Create a cryptographic stamping service
    print("\n2. Creating cryptographic stamping service...")
    stamping_service = CryptographicStampingService(
        key_manager=key_manager,
        certificate_manager=certificate_manager
    )
    
    # Step 3: Generate a CSID for the invoice
    print("\n3. Generating CSID for invoice...")
    csid, timestamp = stamping_service.generate_csid(test_invoice_data)
    print(f"   CSID: {csid[:20]}... (truncated)")
    print(f"   Timestamp: {timestamp}")
    
    assert csid, "CSID should be generated"
    assert timestamp, "Timestamp should be generated"
    
    # Step 4: Verify the CSID
    print("\n4. Verifying CSID...")
    is_valid, details = stamping_service.verify_csid(test_invoice_data, csid)
    print(f"   CSID valid: {is_valid}")
    if details:
        print(f"   Details: {details}")
    
    assert is_valid, "CSID verification should pass"
    
    # Step 5: Generate a QR code with CSID
    print("\n5. Generating QR code...")
    qr_data = {
        "invoice_number": test_invoice_data["invoice_number"],
        "total_amount": test_invoice_data["total_amount"],
        "currency": test_invoice_data["currency"],
        "csid": csid
    }
    qr_code = stamping_service.generate_qr_code(qr_data)
    print(f"   QR code generated, length: {len(qr_code)} bytes")
    
    assert qr_code, "QR code should be generated"
    
    # Step 6: Apply a complete cryptographic stamp to the invoice
    print("\n6. Applying cryptographic stamp to invoice...")
    stamped_invoice = stamping_service.stamp_invoice(test_invoice_data)
    
    # Check the stamped invoice
    assert "cryptographic_stamp" in stamped_invoice, "Invoice should have a cryptographic stamp"
    stamp = stamped_invoice["cryptographic_stamp"]
    print(f"   Stamp contains CSID: {stamp['csid'][:20]}... (truncated)")
    print(f"   Stamp timestamp: {stamp['timestamp']}")
    print(f"   Stamp algorithm: {stamp['algorithm']}")
    print(f"   QR code included: {'qr_code' in stamp}")
    
    # Step 7: Verify the complete stamp
    print("\n7. Verifying the cryptographic stamp...")
    stamp_data = stamped_invoice["cryptographic_stamp"]
    is_valid, details = stamping_service.verify_stamp(test_invoice_data, stamp_data)
    
    print(f"   Stamp valid: {is_valid}")
    if details:
        print(f"   Details: {details}")
    
    assert is_valid, "Stamp verification should pass"
    
    # Step 8: Test tampering detection
    print("\n8. Testing tampering detection...")
    
    # Tamper with the invoice
    tampered_invoice = test_invoice_data.copy()
    tampered_invoice["total_amount"] = 40000.00  # Change the total amount
    
    # Try to verify with tampered data
    is_valid, details = stamping_service.verify_stamp(tampered_invoice, stamp_data)
    
    print(f"   Tampered invoice verification: {is_valid} (should be False)")
    if details:
        print(f"   Details: {details}")
    
    assert not is_valid, "Verification should fail with tampered invoice"
    
    # Step 9: Export the data for potential manual inspection
    print("\n9. Exporting test data for manual inspection...")
    
    output_dir = os.path.join(test_environment["temp_dir"], "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Export the stamped invoice
    with open(os.path.join(output_dir, "stamped_invoice.json"), "w") as f:
        json.dump(stamped_invoice, f, indent=2)
    
    # Export the QR code to a file
    with open(os.path.join(output_dir, "qr_code.png"), "wb") as f:
        f.write(base64.b64decode(stamp_data["qr_code"]))
    
    print(f"   Data exported to: {output_dir}")
    
    print("\nE2E test completed successfully!")


if __name__ == "__main__":
    # This allows running the script directly, not just through pytest
    pytest.main(["-xvs", __file__])
