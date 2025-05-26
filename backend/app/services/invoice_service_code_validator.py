"""
FIRS Service Code Validation Service.

This module provides validation functionality for service codes in invoices,
ensuring they conform to FIRS requirements.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio

from app.schemas.invoice_validation import (
    InvoiceValidationRequest, InvoiceLine, ValidationError
)
from app.services.odoo_firs_service_code_mapper import odoo_firs_service_code_mapper
from app.services.firs_service import firs_service

logger = logging.getLogger(__name__)


class InvoiceServiceCodeValidator:
    """
    Validator for FIRS service codes in invoices.
    
    This class provides methods to:
    1. Validate service codes against FIRS requirements
    2. Suggest appropriate service codes for invoice lines
    3. Apply validation rules for service code correctness
    """
    
    def __init__(self):
        """Initialize the service code validator."""
        pass
    
    async def validate_service_codes(
        self, 
        invoice: InvoiceValidationRequest
    ) -> Tuple[List[ValidationError], List[ValidationError]]:
        """
        Validate service codes in an invoice against FIRS requirements.
        
        Args:
            invoice: The invoice to validate
            
        Returns:
            Tuple[List[ValidationError], List[ValidationError]]: (errors, warnings)
        """
        errors = []
        warnings = []
        
        # Ensure service codes are loaded
        await odoo_firs_service_code_mapper._ensure_service_codes_loaded()
        
        # Check if we have service codes available
        if not odoo_firs_service_code_mapper.service_codes:
            warnings.append(
                ValidationError(
                    field="invoice",
                    error="Could not load FIRS service codes for validation",
                    error_code="SERVICE_CODES_UNAVAILABLE"
                )
            )
            return errors, warnings
        
        # Validate each invoice line
        for i, line in enumerate(invoice.invoice_lines):
            line_path = f"invoice_lines[{i}]"
            
            # Check if service code is provided
            if not line.service_code:
                warnings.append(
                    ValidationError(
                        field=f"{line_path}.service_code",
                        error="Missing service code for invoice line",
                        error_code="MISSING_SERVICE_CODE"
                    )
                )
                continue
            
            # Validate service code against FIRS codes
            if line.service_code not in odoo_firs_service_code_mapper.service_codes:
                errors.append(
                    ValidationError(
                        field=f"{line_path}.service_code",
                        error=f"Invalid FIRS service code: {line.service_code}",
                        error_code="INVALID_SERVICE_CODE"
                    )
                )
                
                # Try to suggest alternatives
                suggestion = await self._suggest_service_code_for_line(line)
                if suggestion:
                    warnings.append(
                        ValidationError(
                            field=f"{line_path}.service_code",
                            error=f"Suggested service code: {suggestion['code']} ({suggestion['name']})",
                            error_code="SERVICE_CODE_SUGGESTION"
                        )
                    )
        
        return errors, warnings
    
    async def _suggest_service_code_for_line(
        self, 
        line: InvoiceLine
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest a service code for an invoice line based on its description.
        
        Args:
            line: The invoice line to suggest a service code for
            
        Returns:
            Optional[Dict[str, Any]]: Suggested service code details or None
        """
        try:
            # Use item name and description for suggestion
            return await odoo_firs_service_code_mapper.suggest_service_code(
                product_name=line.item_name,
                description=line.item_description
            )
        except Exception as e:
            logger.error(f"Error suggesting service code: {str(e)}")
            return None
    
    async def get_service_code_details(self, code: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a service code.
        
        Args:
            code: The service code to get details for
            
        Returns:
            Optional[Dict[str, Any]]: Service code details or None
        """
        # Ensure service codes are loaded
        await odoo_firs_service_code_mapper._ensure_service_codes_loaded()
        
        return odoo_firs_service_code_mapper.get_service_code_details(code)


# Create singleton instance for reuse
invoice_service_code_validator = InvoiceServiceCodeValidator()
