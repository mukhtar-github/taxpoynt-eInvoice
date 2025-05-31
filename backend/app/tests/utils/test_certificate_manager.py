"""
Unit tests for certificate manager functionality.
"""
import os
import tempfile
import pytest
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from app.utils.certificate_manager import CertificateManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def certificate_manager(temp_dir):
    """Create a certificate manager instance with a temporary directory."""
    cert_dir = os.path.join(temp_dir, "certificates")
    os.makedirs(cert_dir, exist_ok=True)
    return CertificateManager(certs_dir=cert_dir)


@pytest.fixture
def test_certificate_data():
    """Generate test certificate data."""
    # Generate a private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Create a self-signed certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "NG"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Organization"),
        x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName("test.example.com")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    cert_pem = cert.public_bytes(serialization.Encoding.PEM)
    key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    return {
        "certificate": cert_pem,
        "private_key": key_pem,
        "public_key": private_key.public_key()
    }


def test_certificate_store_and_load(certificate_manager, test_certificate_data):
    """Test storing and loading a certificate."""
    cert_data = test_certificate_data["certificate"]
    
    # Store the certificate
    cert_path = certificate_manager.store_certificate(cert_data, "test_cert.crt")
    
    # Verify the file exists
    assert os.path.exists(cert_path)
    
    # Load the certificate
    loaded_cert = certificate_manager.load_certificate(cert_path)
    
    # Verify it's the same certificate
    assert loaded_cert.public_bytes(serialization.Encoding.PEM) == cert_data


def test_certificate_validation(certificate_manager, test_certificate_data):
    """Test certificate validation."""
    cert_data = test_certificate_data["certificate"]
    
    # Store the certificate
    cert_path = certificate_manager.store_certificate(cert_data, "test_cert.crt")
    
    # Validate the certificate
    is_valid, cert_info = certificate_manager.validate_certificate(cert_path)
    
    # Check that validation passed
    assert is_valid
    assert cert_info is not None
    assert "subject" in cert_info
    assert "issuer" in cert_info
    assert "valid_from" in cert_info
    assert "valid_until" in cert_info


def test_extract_public_key(certificate_manager, test_certificate_data):
    """Test extracting public key from certificate."""
    cert_data = test_certificate_data["certificate"]
    
    # Store the certificate
    cert_path = certificate_manager.store_certificate(cert_data, "test_cert.crt")
    
    # Extract public key
    public_key = certificate_manager.extract_public_key(cert_path)
    
    # Test encryption/decryption to verify it's a valid key
    test_data = b"Test message"
    
    # Encrypt with the extracted public key
    encrypted_data = public_key.encrypt(
        test_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Decrypt with the original private key
    original_private_key = serialization.load_pem_private_key(
        test_certificate_data["private_key"],
        password=None,
    )
    
    decrypted_data = original_private_key.decrypt(
        encrypted_data,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    
    # Verify decryption worked
    assert decrypted_data == test_data


def test_create_self_signed_certificate(certificate_manager):
    """Test creating a self-signed certificate."""
    # Create a self-signed certificate
    cert_path, key_path = certificate_manager.create_self_signed_certificate(
        common_name="test.example.com",
        organization="Test Org",
        country="NG",
        validity_days=365
    )
    
    # Verify files exist
    assert os.path.exists(cert_path)
    assert os.path.exists(key_path)
    
    # Validate the certificate
    is_valid, cert_info = certificate_manager.validate_certificate(cert_path)
    
    # Check validation results
    assert is_valid
    assert cert_info["subject"]["commonName"] == "test.example.com"
    assert cert_info["subject"]["organizationName"] == "Test Org"
    assert cert_info["subject"]["countryName"] == "NG"


def test_invalid_certificate(certificate_manager, temp_dir):
    """Test handling invalid certificates."""
    # Create an invalid certificate file
    invalid_cert_path = os.path.join(temp_dir, "invalid_cert.crt")
    with open(invalid_cert_path, "w") as f:
        f.write("This is not a valid certificate")
    
    # Validate should fail
    is_valid, cert_info = certificate_manager.validate_certificate(invalid_cert_path)
    
    assert not is_valid
    assert "error" in cert_info
