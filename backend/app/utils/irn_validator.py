"""
IRN (Invoice Reference Number) validation module for FIRS e-Invoicing system.

This module provides comprehensive validation functions for IRN integrity,
complementing the IRN generator module. It focuses on:
1. Format compliance validation
2. Hash verification against invoice content
3. Testing with various invoice scenarios

All validators follow a consistent pattern of returning (is_valid, message)
tuples for uniform error handling.
"""

import re
import logging
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, List, Union
from enum import Enum
import json

from app.utils.irn_generator import (
    validate_invoice_number,
    validate_service_id,
    validate_timestamp,
    parse_irn,
    calculate_invoice_hash,
    extract_key_invoice_fields
)

# Try to import settings or use fallback
try:
    from app.core.config import settings
except ImportError:
    # Simple settings class for standalone testing
    class Settings:
        SECRET_KEY: str = "test_secret_key_for_development_only"
    settings = Settings()

logger = logging.getLogger(__name__)


class IRNValidationResult(Enum):
    """Enum for validation result types."""
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    INVALID_COMPONENT = "invalid_component"
    INVOICE_MISMATCH = "invoice_mismatch"
    HASH_MISMATCH = "hash_mismatch"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


def validate_irn_format(irn: str) -> Tuple[bool, str]:
    """
    Validate that an IRN follows the format required by FIRS.
    
    Args:
        irn: The IRN to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not irn:
        return False, "IRN cannot be null or empty"
    
    # Check for FIRS format: InvoiceNumber-ServiceID-YYYYMMDD
    pattern = re.compile(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$')
    if not pattern.match(irn):
        return False, f"Invalid IRN format: {irn}. Must be InvoiceNumber-ServiceID-YYYYMMDD"
    
    try:
        # Further validate each component
        invoice_number, service_id, timestamp = irn.split('-')
        
        if not validate_invoice_number(invoice_number):
            return False, f"Invalid invoice number format in IRN: {invoice_number}"
        
        if not validate_service_id(service_id):
            return False, f"Invalid service ID format in IRN: {service_id}"
        
        if not validate_timestamp(timestamp):
            return False, f"Invalid timestamp format in IRN: {timestamp}"
        
        return True, "IRN format is valid"
    
    except Exception as e:
        logger.error(f"Error validating IRN format: {e}")
        return False, f"Error validating IRN format: {str(e)}"


def validate_irn_against_invoice(
    irn: str,
    invoice_data: Dict[str, Any],
    verify_hash: bool = True,
    stored_hash: Optional[str] = None,
    stored_verification_code: Optional[str] = None
) -> Tuple[bool, str, dict]:
    """
    Comprehensive validation of an IRN against invoice data.
    
    Args:
        irn: The IRN to validate
        invoice_data: Invoice data to validate against
        verify_hash: Whether to verify the hash (may be false for legacy IRNs)
        stored_hash: Optional hash value stored in database to compare against
        stored_verification_code: Optional verification code stored in database
        
    Returns:
        Tuple of (is_valid, message, validation_details)
    """
    results = {
        "format_valid": False,
        "components_valid": False,
        "invoice_match": False,
        "hash_valid": None if not verify_hash else False,
        "verification_code_valid": None if not stored_verification_code else False
    }
    
    # Step 1: Validate IRN format
    format_valid, format_message = validate_irn_format(irn)
    results["format_valid"] = format_valid
    
    if not format_valid:
        return False, format_message, results
    
    try:
        # Step 2: Parse and validate components
        invoice_number, service_id, timestamp = parse_irn(irn)
        results["components_valid"] = True
        
        # Step 3: Match against invoice data
        formatted_invoice_number = invoice_data.get('invoice_number', '')
        if invoice_number != formatted_invoice_number:
            results["invoice_match"] = False
            return False, f"Invoice number mismatch: IRN has {invoice_number}, invoice has {formatted_invoice_number}", results
        
        results["invoice_match"] = True
        
        # Step 4: Verify hash if requested
        if verify_hash:
            # Generate a hash of the invoice data
            unique_id = invoice_data.get('unique_id', None)
            calculated_hash = calculate_invoice_hash(invoice_data, unique_id)
            
            # If stored hash is provided, compare with it
            if stored_hash:
                if calculated_hash != stored_hash:
                    results["hash_valid"] = False
                    return False, "Invoice content hash does not match stored hash", results
                results["hash_valid"] = True
            
            # Step 5: Verify verification code if provided
            if stored_verification_code:
                expected_code = hmac.new(
                    settings.SECRET_KEY.encode(),
                    calculated_hash.encode(),
                    hashlib.sha256
                ).hexdigest()[:12]
                
                if stored_verification_code != expected_code:
                    results["verification_code_valid"] = False
                    return False, "Verification code is invalid", results
                
                results["verification_code_valid"] = True
        
        return True, "IRN validation successful", results
    
    except Exception as e:
        logger.error(f"Error validating IRN against invoice: {e}")
        return False, f"Validation error: {str(e)}", results


def verify_irn_integrity(
    irn: str, 
    verification_code: str,
    hash_value: str,
    invoice_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    Verify the cryptographic integrity of an IRN.
    
    This function checks that the hash value correctly represents the invoice data
    and that the verification code is valid for the hash.
    
    Args:
        irn: The IRN to verify
        verification_code: The verification code (HMAC)
        hash_value: The hash value of the invoice data
        invoice_data: The invoice data to verify against
        
    Returns:
        Tuple of (is_valid, message)
    """
    try:
        # Step 1: Verify the hash matches the invoice data
        # Extract key fields from invoice data
        key_fields = extract_key_invoice_fields(invoice_data)
        
        # Calculate a fresh hash
        unique_id = invoice_data.get('unique_id', None)  
        calculated_hash = calculate_invoice_hash(invoice_data, unique_id)
        
        if hash_value != calculated_hash:
            return False, "Hash value does not match invoice data"
        
        # Step 2: Verify the verification code matches the hash
        expected_code = hmac.new(
            settings.SECRET_KEY.encode(),
            hash_value.encode(),
            hashlib.sha256
        ).hexdigest()[:12]
        
        if verification_code != expected_code:
            return False, "Verification code is invalid"
        
        # Step 3: Verify IRN format and content
        format_valid, _ = validate_irn_format(irn)
        if not format_valid:
            return False, "IRN format is invalid"
        
        # If we got here, the integrity checks passed
        return True, "IRN integrity verification successful"
        
    except Exception as e:
        logger.error(f"Error verifying IRN integrity: {e}")
        return False, f"Integrity verification error: {str(e)}"


def run_irn_validation_test(
    test_cases: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Run a series of validation tests on IRNs with various scenarios.
    
    This function is useful for testing the validation logic with different
    edge cases and scenarios.
    
    Args:
        test_cases: List of test case dictionaries, each containing:
                   - irn: The IRN to test
                   - invoice_data: Invoice data to test against
                   - expected_result: True if test should pass, False otherwise
                   - scenario: Description of the test case
                   
    Returns:
        List of test results with pass/fail status and messages
    """
    results = []
    
    for idx, test_case in enumerate(test_cases):
        irn = test_case.get('irn', '')
        invoice_data = test_case.get('invoice_data', {})
        verify_hash = test_case.get('verify_hash', True)
        stored_hash = test_case.get('stored_hash', None)
        stored_verification_code = test_case.get('stored_verification_code', None)
        expected_result = test_case.get('expected_result', True)
        scenario = test_case.get('scenario', f"Test case {idx+1}")
        
        # Run validation
        is_valid, message, details = validate_irn_against_invoice(
            irn, 
            invoice_data,
            verify_hash,
            stored_hash,
            stored_verification_code
        )
        
        # Check if result matches expectation
        test_passed = (is_valid == expected_result)
        
        results.append({
            'scenario': scenario,
            'irn': irn,
            'is_valid': is_valid,
            'message': message,
            'details': details,
            'expected_result': expected_result,
            'test_passed': test_passed
        })
        
        # Log results
        if test_passed:
            logger.info(f"PASSED - {scenario}: {message}")
        else:
            logger.warning(f"FAILED - {scenario}: {message}")
    
    return results


def generate_validation_report(
    irn: str,
    invoice_data: Dict[str, Any],
    hash_value: Optional[str] = None,
    verification_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report for an IRN.
    
    This function runs all available checks and produces a detailed
    report of the IRN's validity.
    
    Args:
        irn: The IRN to validate
        invoice_data: Invoice data to validate against
        hash_value: Optional hash value for integrity check
        verification_code: Optional verification code for integrity check
        
    Returns:
        Dictionary with validation results
    """
    report = {
        "irn": irn,
        "timestamp": datetime.now().isoformat(),
        "validations": {}
    }
    
    # Format validation
    format_valid, format_message = validate_irn_format(irn)
    report["validations"]["format"] = {
        "is_valid": format_valid,
        "message": format_message
    }
    
    if not format_valid:
        report["overall_result"] = "INVALID"
        report["reason"] = format_message
        return report
    
    # Component validation
    try:
        invoice_number, service_id, timestamp = parse_irn(irn)
        report["validations"]["components"] = {
            "is_valid": True,
            "invoice_number": invoice_number,
            "service_id": service_id,
            "timestamp": timestamp
        }
    except ValueError as e:
        report["validations"]["components"] = {
            "is_valid": False,
            "message": str(e)
        }
        report["overall_result"] = "INVALID"
        report["reason"] = str(e)
        return report
    
    # Invoice data validation
    is_valid, message, details = validate_irn_against_invoice(
        irn, 
        invoice_data,
        verify_hash=(hash_value is not None),
        stored_hash=hash_value,
        stored_verification_code=verification_code
    )
    
    report["validations"]["invoice_match"] = {
        "is_valid": is_valid,
        "message": message,
        "details": details
    }
    
    # Integrity check if hash and verification code provided
    if hash_value and verification_code:
        integrity_valid, integrity_message = verify_irn_integrity(
            irn, verification_code, hash_value, invoice_data
        )
        report["validations"]["integrity"] = {
            "is_valid": integrity_valid,
            "message": integrity_message
        }
        
        if not integrity_valid:
            report["overall_result"] = "INVALID"
            report["reason"] = integrity_message
            return report
    
    # Set overall result
    if all(v.get("is_valid", False) for v in report["validations"].values()):
        report["overall_result"] = "VALID"
        report["reason"] = "All validations passed"
    else:
        report["overall_result"] = "INVALID"
        # Find the first validation that failed
        for key, validation in report["validations"].items():
            if not validation.get("is_valid", False):
                report["reason"] = f"{key}: {validation.get('message', 'Invalid')}"
                break
    
    return report
