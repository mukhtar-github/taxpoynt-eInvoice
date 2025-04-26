"""
IRN (Invoice Reference Number) generation utilities for FIRS e-Invoice system.

This module provides functions for generating and validating IRNs according
to FIRS requirements (InvoiceNumber-ServiceID-YYYYMMDD format).
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
    """
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
        datetime.date(year, month, day)
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
    """
    # Validate invoice number
    if not validate_invoice_number(invoice_number):
        raise HTTPException(
            status_code=400,
            detail="Invalid invoice number: must be alphanumeric with no special characters"
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
            detail="Invalid timestamp: must be in YYYYMMDD format"
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
            detail="Invalid invoice number in IRN"
        )
    
    if not validate_service_id(service_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid service ID in IRN"
        )
    
    if not validate_timestamp(timestamp):
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp in IRN"
        )
    
    return invoice_number, service_id, timestamp


def validate_irn(irn: str) -> bool:
    """
    Validate an IRN according to FIRS requirements.
    
    Args:
        irn: IRN to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        parse_irn(irn)
        return True
    except HTTPException:
        return False 