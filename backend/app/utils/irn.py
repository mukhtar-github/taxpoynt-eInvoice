"""
IRN (Invoice Reference Number) generation utilities for FIRS e-Invoice system.

This module provides functions for generating and validating IRNs according
to FIRS requirements (InvoiceNumber-ServiceID-YYYYMMDD format).

FIRS Official Requirements:
- Invoice Number: Alphanumeric identifier from the taxpayer's accounting system (no special characters)
- Service ID: 8-character alphanumeric identifier assigned by FIRS
- Date: YYYYMMDD format

Example IRN: INV001-94ND90NR-20240611
"""

import datetime
import re
from typing import Optional, Tuple

from fastapi import HTTPException # type: ignore


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
    - 8-character alphanumeric
    - Assigned by FIRS to each taxpayer
    """
    # 8-character alphanumeric
    pattern = re.compile(r'^[a-zA-Z0-9]{8}$')
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
    # 8-digit date in YYYYMMDD format
    if not re.match(r'^\d{8}$', timestamp):
        return False
        
    # Check if it's a valid date
    try:
        year = int(timestamp[0:4])
        month = int(timestamp[4:6])
        day = int(timestamp[6:8])
        
        # Create date object to validate
        date_obj = datetime.date(year, month, day)
        
        # Ensure it's not a future date (as per FIRS guidelines)
        if date_obj > datetime.date.today():
            return False
            
        return True
    except ValueError:
        return False


def generate_irn(
    invoice_number: str,
    service_id: str,
    timestamp: Optional[str] = None
) -> str:
    """
    Generate an IRN according to FIRS requirements.
    
    Args:
        invoice_number: Invoice number from accounting system
        service_id: FIRS-assigned Service ID
        timestamp: Date in YYYYMMDD format (defaults to today)
        
    Returns:
        IRN in format InvoiceNumber-ServiceID-YYYYMMDD
        
    Raises:
        HTTPException: If any component is invalid
    
    FIRS Format:
    The IRN follows the format specified by FIRS:
    ```
    InvoiceNumber-ServiceID-YYYYMMDD
    ```
    Example: `INV001-94ND90NR-20240611`
    """
    # Validate invoice number
    if not validate_invoice_number(invoice_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid invoice number: must be alphanumeric with no special characters, maximum 50 characters"
        )
    
    # Validate service ID
    if not validate_service_id(service_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid service ID: must be 8 characters alphanumeric"
        )
    
    # If timestamp not provided, use today's date
    if not timestamp:
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
    
    # Validate timestamp
    if not validate_timestamp(timestamp):
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp: must be in YYYYMMDD format, be a valid date, and not in the future"
        )
    
    # Generate IRN
    return f"{invoice_number}-{service_id}-{timestamp}"


def parse_irn(irn: str) -> Tuple[str, str, str]:
    """
    Parse an IRN into its components.
    
    Args:
        irn: IRN in format InvoiceNumber-ServiceID-YYYYMMDD
        
    Returns:
        Tuple of (invoice_number, service_id, timestamp)
        
    Raises:
        HTTPException: If IRN format is invalid
    """
    # Check if IRN has the correct format
    pattern = re.compile(r'^(.+)-([a-zA-Z0-9]{8})-(\d{8})$')
    match = pattern.match(irn)
    
    if not match:
        raise HTTPException(
            status_code=400,
            detail="Invalid IRN format: must be InvoiceNumber-ServiceID-YYYYMMDD"
        )
    
    invoice_number, service_id, timestamp = match.groups()
    
    # Validate components
    if not validate_invoice_number(invoice_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid invoice number in IRN: must be alphanumeric with no special characters, maximum 50 characters"
        )
    
    if not validate_service_id(service_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid service ID in IRN: must be 8 characters alphanumeric"
        )
    
    if not validate_timestamp(timestamp):
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp in IRN: must be in YYYYMMDD format, be a valid date, and not in the future"
        )
    
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
        parse_irn(irn)
        return True
    except HTTPException:
        return False