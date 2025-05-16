"""
IRN (Invoice Reference Number) generation module for FIRS e-Invoicing system.

This module implements the IRN generation algorithm according to FIRS specifications,
with added security features and compatibility with the Odoo to BIS Billing 3.0 
UBL mapping system.

FIRS Official Format:
- IRN Format: InvoiceNumber-ServiceID-YYYYMMDD
- Invoice Number: Alphanumeric identifier from the taxpayer's accounting system
- Service ID: 8-character alphanumeric identifier assigned by FIRS
- Date: YYYYMMDD format

Enhanced Security Features:
- Cryptographic hash of invoice data for verification
- Digital signature capability for integrity verification
- Secure unique identifier generation
"""

import uuid
import hashlib
import hmac
import base64
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List, Union

# Create a simple settings class for testing
class Settings:
    SECRET_KEY: str = "test_secret_key_for_development_only"

# Try to import settings from app.core.config, but fall back to the simple settings if not available
try:
    from app.core.config import settings
except ImportError:
    settings = Settings()

# Import these from irn.py for now, but we'll replace with our own implementations
try:
    from app.utils.irn import validate_invoice_number, validate_service_id, validate_timestamp
except ImportError:
    # Implement our own validation functions if irn.py is not available
    def validate_invoice_number(invoice_number: str) -> bool:
        """
        Validate an invoice number according to FIRS requirements.
        
        Args:
            invoice_number: Invoice number to validate
            
        Returns:
            True if valid, False otherwise
        
        FIRS Requirements:
        - Alphanumeric only
        - No special characters
        - Must not be empty
        - Maximum length of 50 characters (as per FIRS e-Invoicing guidelines)
        """
        # Check if empty
        if not invoice_number:
            return False
            
        # Check max length (as per FIRS guidelines)
        if len(invoice_number) > 50:
            return False
        
        # Alphanumeric only, no special characters
        pattern = re.compile(r'^[a-zA-Z0-9]+$')
        return bool(pattern.match(invoice_number))


    def validate_service_id(service_id: str) -> bool:
        """
        Validate a service ID according to FIRS requirements.
        
        Args:
            service_id: Service ID to validate
            
        Returns:
            True if valid, False otherwise
        
        FIRS Requirements:
        - 8 characters exactly
        - Alphanumeric only
        - No special characters
        """
        # Check length
        if len(service_id) != 8:
            return False
        
        # Alphanumeric only, no special characters
        pattern = re.compile(r'^[a-zA-Z0-9]+$')
        return bool(pattern.match(service_id))


    def validate_timestamp(timestamp: str) -> bool:
        """
        Validate a timestamp according to FIRS requirements.
        
        Args:
            timestamp: Timestamp to validate (YYYYMMDD format)
            
        Returns:
            True if valid, False otherwise
        
        FIRS Requirements:
        - 8-digit date in YYYYMMDD format
        - Must be a valid calendar date
        - Must not be a future date (as per FIRS e-Invoicing guidelines)
        """
        # Check format
        if not re.match(r'^\d{8}$', timestamp):
            return False
        
        # Check if it's a valid date
        try:
            date = datetime.strptime(timestamp, "%Y%m%d").date()
        except ValueError:
            return False
        
        # Check if it's not a future date
        today = datetime.now().date()
        if date > today:
            return False
        
        return True

logger = logging.getLogger(__name__)


def extract_key_invoice_fields(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key fields from invoice data for IRN generation.
    
    Args:
        invoice_data: Complete invoice data dictionary
        
    Returns:
        Dictionary with essential fields for IRN generation
    """
    # Extract essential fields from the invoice data
    # These are the most important fields that uniquely identify an invoice
    essential_fields = {
        'invoice_number': invoice_data.get('invoice_number', ''),
        'invoice_date': invoice_data.get('invoice_date', ''),
        'seller_tax_id': invoice_data.get('seller_tax_id', invoice_data.get('supplier_tax_id', '')),
        'buyer_tax_id': invoice_data.get('buyer_tax_id', invoice_data.get('customer_tax_id', '')),
        'total_amount': str(invoice_data.get('total_amount', 0)),
        'currency_code': invoice_data.get('currency_code', 'NGN'),
    }
    
    return essential_fields


def calculate_invoice_hash(invoice_data: Dict[str, Any], unique_id: str = None) -> str:
    """
    Calculate a cryptographic hash of invoice data.
    
    Args:
        invoice_data: Invoice data dictionary
        unique_id: Optional unique identifier to include in the hash
        
    Returns:
        SHA-256 hash of the invoice data
    """
    # Extract essential fields
    key_fields = extract_key_invoice_fields(invoice_data)
    
    # Add a timestamp for entropy
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    # Add a unique ID if provided, or generate one
    uid = unique_id or str(uuid.uuid4())
    
    # Create a string to hash
    # Format: invoice_number|invoice_date|seller_tax_id|buyer_tax_id|total_amount|currency_code|timestamp|unique_id
    data_to_hash = f"{key_fields['invoice_number']}|{key_fields['invoice_date']}|{key_fields['seller_tax_id']}|" \
                  f"{key_fields['buyer_tax_id']}|{key_fields['total_amount']}|{key_fields['currency_code']}|{timestamp}|{uid}"
    
    # Calculate SHA-256 hash
    return hashlib.sha256(data_to_hash.encode()).hexdigest()


def generate_verification_code(hash_value: str, length: int = 12) -> str:
    """
    Generate a verification code using HMAC and the application secret.
    
    Args:
        hash_value: The hash value to generate a verification code for
        length: Length of the verification code
        
    Returns:
        HMAC-based verification code
    """
    # Generate HMAC using the application secret key
    verification_code = hmac.new(
        settings.SECRET_KEY.encode(),
        hash_value.encode(),
        hashlib.sha256
    ).hexdigest()[:length]
    
    return verification_code


def generate_service_id() -> str:
    """
    Generate a valid Service ID according to FIRS requirements.
    
    Returns:
        8-character alphanumeric Service ID
    """
    # Generate a random 8-character alphanumeric string
    # This would normally be assigned by FIRS, but we generate it here for testing
    alphabet = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    service_id = ''.join(secrets.choice(alphabet) for _ in range(8))
    
    return service_id


def format_invoice_number(invoice_number: str) -> str:
    """
    Format an invoice number to be FIRS-compliant.
    
    Args:
        invoice_number: Original invoice number
        
    Returns:
        FIRS-compliant invoice number
    """
    # Remove any special characters or spaces
    formatted = ''.join(c for c in invoice_number if c.isalnum())
    
    # Ensure it's not empty
    if not formatted:
        formatted = f"INV{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    # Truncate if too long (FIRS max length is 50)
    if len(formatted) > 50:
        formatted = formatted[:50]
    
    return formatted


def generate_firs_irn(
    invoice_data: Dict[str, Any],
    service_id: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a complete IRN according to FIRS specifications.
    
    Args:
        invoice_data: Dictionary containing invoice details
        service_id: FIRS-assigned Service ID (generates one if not provided)
        timestamp: Date in YYYYMMDD format (defaults to today)
        
    Returns:
        Dictionary containing all IRN components
    """
    # Extract or format invoice number
    invoice_number = format_invoice_number(invoice_data.get('invoice_number', ''))
    
    # Get or generate service ID
    sid = service_id or generate_service_id()
    
    # Use provided timestamp or today's date
    ts = timestamp or datetime.utcnow().strftime("%Y%m%d")
    
    # Validate components
    if not validate_invoice_number(invoice_number):
        logger.error(f"Invalid invoice number: {invoice_number}")
        raise ValueError("Invalid invoice number format for FIRS IRN")
    
    if not validate_service_id(sid):
        logger.error(f"Invalid service ID: {sid}")
        raise ValueError("Invalid service ID format for FIRS IRN")
    
    if not validate_timestamp(ts):
        logger.error(f"Invalid timestamp: {ts}")
        raise ValueError("Invalid timestamp format for FIRS IRN")
    
    # Generate unique ID
    unique_id = str(uuid.uuid4())
    
    # Calculate hash of invoice data
    hash_value = calculate_invoice_hash(invoice_data, unique_id)
    
    # Generate verification code
    verification_code = generate_verification_code(hash_value)
    
    # Construct the IRN according to FIRS format
    irn_value = f"{invoice_number}-{sid}-{ts}"
    
    # Return all components for complete traceability
    return {
        "irn": irn_value,
        "invoice_number": invoice_number,
        "service_id": sid,
        "timestamp": ts,
        "unique_id": unique_id,
        "hash_value": hash_value,
        "verification_code": verification_code
    }


def verify_irn(irn: str, invoice_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verify if an IRN is valid and matches the provided invoice data.
    
    Args:
        irn: IRN to verify
        invoice_data: Invoice data to verify against
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Parse the IRN components
        parts = irn.split('-')
        if len(parts) != 3:
            return False, "Invalid IRN format"
        
        invoice_number, service_id, timestamp = parts
        
        # Verify individual components
        if not validate_invoice_number(invoice_number):
            return False, "Invalid invoice number in IRN"
        
        if not validate_service_id(service_id):
            return False, "Invalid service ID in IRN"
        
        if not validate_timestamp(timestamp):
            return False, "Invalid timestamp in IRN"
        
        # Check if invoice number matches
        original_invoice_number = format_invoice_number(invoice_data.get('invoice_number', ''))
        if invoice_number != original_invoice_number:
            return False, "Invoice number does not match"
        
        # For additional security, we could also verify:
        # 1. If the service ID is valid for this organization
        # 2. If the timestamp is reasonable for this invoice
        # 3. Calculate and verify the hash
        
        return True, "IRN verification successful"
        
    except Exception as e:
        logger.error(f"Error verifying IRN: {e}")
        return False, f"Error verifying IRN: {str(e)}"


def parse_irn(irn: str) -> Tuple[str, str, str]:
    """
    Parse an IRN into its components.
    
    Args:
        irn: IRN in format InvoiceNumber-ServiceID-YYYYMMDD
        
    Returns:
        Tuple of (invoice_number, service_id, timestamp)
        
    Raises:
        ValueError: If IRN format is invalid
    """
    # Check if IRN is null or empty
    if not irn:
        raise ValueError("IRN cannot be null or empty")
    
    # Split IRN into components by dash
    parts = irn.split('-')
    
    # Verify that there are exactly 3 parts
    if len(parts) != 3:
        raise ValueError(f"Invalid IRN format: {irn}. IRN must be in format InvoiceNumber-ServiceID-YYYYMMDD")
    
    # Extract components
    invoice_number = parts[0]
    service_id = parts[1]
    timestamp = parts[2]
    
    # Validate each component
    if not validate_invoice_number(invoice_number):
        raise ValueError(f"Invalid invoice number in IRN: {invoice_number}")
    
    if not validate_service_id(service_id):
        raise ValueError(f"Invalid service ID in IRN: {service_id}")
    
    if not validate_timestamp(timestamp):
        raise ValueError(f"Invalid timestamp in IRN: {timestamp}")
    
    return invoice_number, service_id, timestamp


def validate_irn(irn: str) -> bool:
    """
    Validate an IRN according to FIRS requirements.
    
    Args:
        irn: IRN to validate
        
    Returns:
        True if valid, False otherwise
    
    FIRS Format:
    The IRN must follow the format: InvoiceNumber-ServiceID-YYYYMMDD
    - Invoice Number: Alphanumeric identifier, no special characters
    - Service ID: 8-character alphanumeric identifier
    - Date: YYYYMMDD format, valid date, not in future
    """
    try:
        # Attempt to parse the IRN - this will validate all components
        parse_irn(irn)
        return True
    except ValueError:
        return False


def generate_irn_for_ubl_invoice(ubl_invoice: Dict[str, Any], service_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate an IRN specifically for a UBL-mapped invoice.
    
    This function is designed to work with the Odoo to BIS Billing 3.0 UBL
    mapping system, extracting the necessary fields from a UBL-formatted invoice.
    
    Args:
        ubl_invoice: UBL-formatted invoice data
        service_id: FIRS-assigned Service ID (generates one if not provided)
        
    Returns:
        Dictionary containing all IRN components
    """
    # Extract key fields from UBL format to standard format
    invoice_data = {
        'invoice_number': ubl_invoice.get('ID', ubl_invoice.get('invoice_number', '')),
        'invoice_date': ubl_invoice.get('IssueDate', ubl_invoice.get('invoice_date', '')),
        'seller_tax_id': ubl_invoice.get('AccountingSupplierParty', {}).get('PartyTaxScheme', {}).get('CompanyID', ''),
        'buyer_tax_id': ubl_invoice.get('AccountingCustomerParty', {}).get('PartyTaxScheme', {}).get('CompanyID', ''),
        'total_amount': ubl_invoice.get('LegalMonetaryTotal', {}).get('PayableAmount', 
                        ubl_invoice.get('total_amount', 0)),
        'currency_code': ubl_invoice.get('DocumentCurrencyCode', ubl_invoice.get('currency_code', 'NGN')),
    }
    
    # Generate IRN using the standard function
    return generate_firs_irn(invoice_data, service_id)
