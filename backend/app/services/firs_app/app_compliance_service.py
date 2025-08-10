"""
FIRS APP Compliance Service

This service implements Access Point Provider (APP) specific compliance
functionality for schema validation and FIRS submission requirements.

APP Role Responsibilities:
- Schema validation before FIRS submission
- Compliance checking for transmission requirements
- Cryptographic stamp validation
- Authentication seal verification
- Data format validation for FIRS API
- Transmission compliance monitoring

This service is part of the firs_app package and focuses on the APP's core
responsibility of ensuring compliance before data transmission to FIRS.
"""

import logging
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.validation import ValidationRule
from app.services.firs_core.audit_service import AuditService

logger = logging.getLogger(__name__)


class APPComplianceService:
    """Service for Access Point Provider compliance operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
    
    def validate_transmission_compliance(self, invoice_data: Dict[str, Any], 
                                       user_id: str) -> Dict[str, Any]:
        """
        Validate invoice data for FIRS transmission compliance.
        
        Args:
            invoice_data: Invoice data to validate
            user_id: User ID initiating validation
            
        Returns:
            Validation result with compliance status and details
        """
        try:
            validation_results = {
                "compliant": True,
                "errors": [],
                "warnings": [],
                "validations": []
            }
            
            # Schema validation
            schema_validation = self._validate_firs_schema(invoice_data)
            validation_results["validations"].append(schema_validation)
            
            # Cryptographic stamp validation
            crypto_validation = self._validate_cryptographic_stamp(invoice_data)
            validation_results["validations"].append(crypto_validation)
            
            # Authentication seal validation
            auth_validation = self._validate_authentication_seal(invoice_data)
            validation_results["validations"].append(auth_validation)
            
            # Data format validation
            format_validation = self._validate_data_format(invoice_data)
            validation_results["validations"].append(format_validation)
            
            # Aggregate results
            validation_results["compliant"] = all(
                v["valid"] for v in validation_results["validations"]
            )
            
            # Collect errors and warnings
            for validation in validation_results["validations"]:
                if not validation["valid"]:
                    validation_results["errors"].extend(validation.get("errors", []))
                validation_results["warnings"].extend(validation.get("warnings", []))
            
            # Log compliance check
            self.audit_service.log_compliance_check(
                user_id=user_id,
                compliance_type="transmission",
                compliant=validation_results["compliant"],
                details=validation_results
            )
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Transmission compliance validation failed: {str(e)}")
            raise
    
    def validate_authentication_seal(self, seal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate authentication seal for transmission.
        
        Args:
            seal_data: Authentication seal data
            
        Returns:
            Validation result for authentication seal
        """
        try:
            validation_result = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "seal_verified": False
            }
            
            # Check seal structure
            if not self._validate_seal_structure(seal_data):
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid seal structure")
                return validation_result
            
            # Verify seal signature
            if not self._verify_seal_signature(seal_data):
                validation_result["valid"] = False
                validation_result["errors"].append("Invalid seal signature")
                return validation_result
            
            # Check seal expiration
            if self._is_seal_expired(seal_data):
                validation_result["valid"] = False
                validation_result["errors"].append("Seal has expired")
                return validation_result
            
            validation_result["seal_verified"] = True
            return validation_result
            
        except Exception as e:
            logger.error(f"Authentication seal validation failed: {str(e)}")
            raise
    
    def _validate_firs_schema(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate invoice data against FIRS schema."""
        validation = {
            "type": "schema_validation",
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Required FIRS fields
        required_fields = [
            "invoice_number", "invoice_date", "supplier_tin", "customer_tin",
            "total_amount", "currency_code", "invoice_type", "line_items"
        ]
        
        for field in required_fields:
            if field not in invoice_data or not invoice_data[field]:
                validation["valid"] = False
                validation["errors"].append(f"Missing required field: {field}")
        
        # Validate line items structure
        if "line_items" in invoice_data:
            line_items_validation = self._validate_line_items(invoice_data["line_items"])
            if not line_items_validation["valid"]:
                validation["valid"] = False
                validation["errors"].extend(line_items_validation["errors"])
        
        return validation
    
    def _validate_cryptographic_stamp(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate cryptographic stamp."""
        validation = {
            "type": "cryptographic_stamp_validation",
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if stamp is present
        if "cryptographic_stamp" not in invoice_data:
            validation["valid"] = False
            validation["errors"].append("Missing cryptographic stamp")
            return validation
        
        # Validate stamp structure
        stamp = invoice_data["cryptographic_stamp"]
        if not isinstance(stamp, dict):
            validation["valid"] = False
            validation["errors"].append("Invalid stamp format")
            return validation
        
        # Check required stamp fields
        required_stamp_fields = ["signature", "timestamp", "certificate_id"]
        for field in required_stamp_fields:
            if field not in stamp:
                validation["valid"] = False
                validation["errors"].append(f"Missing stamp field: {field}")
        
        return validation
    
    def _validate_authentication_seal(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate authentication seal."""
        validation = {
            "type": "authentication_seal_validation",
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if seal is present
        if "authentication_seal" not in invoice_data:
            validation["valid"] = False
            validation["errors"].append("Missing authentication seal")
            return validation
        
        # Validate seal
        seal_validation = self.validate_authentication_seal(invoice_data["authentication_seal"])
        if not seal_validation["valid"]:
            validation["valid"] = False
            validation["errors"].extend(seal_validation["errors"])
        
        return validation
    
    def _validate_data_format(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data format for FIRS API."""
        validation = {
            "type": "data_format_validation",
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Validate numeric fields
        numeric_fields = ["total_amount", "tax_amount", "discount_amount"]
        for field in numeric_fields:
            if field in invoice_data:
                try:
                    float(invoice_data[field])
                except (ValueError, TypeError):
                    validation["valid"] = False
                    validation["errors"].append(f"Invalid numeric format for {field}")
        
        # Validate date fields
        date_fields = ["invoice_date", "due_date"]
        for field in date_fields:
            if field in invoice_data:
                if not self._validate_date_format(invoice_data[field]):
                    validation["valid"] = False
                    validation["errors"].append(f"Invalid date format for {field}")
        
        return validation
    
    def _validate_line_items(self, line_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate invoice line items."""
        validation = {
            "valid": True,
            "errors": []
        }
        
        if not isinstance(line_items, list) or not line_items:
            validation["valid"] = False
            validation["errors"].append("Line items must be a non-empty list")
            return validation
        
        required_line_fields = ["description", "quantity", "unit_price", "total_price"]
        for i, item in enumerate(line_items):
            for field in required_line_fields:
                if field not in item:
                    validation["valid"] = False
                    validation["errors"].append(f"Missing field '{field}' in line item {i+1}")
        
        return validation
    
    def _validate_seal_structure(self, seal_data: Dict[str, Any]) -> bool:
        """Validate authentication seal structure."""
        required_fields = ["signature", "timestamp", "issuer"]
        return all(field in seal_data for field in required_fields)
    
    def _verify_seal_signature(self, seal_data: Dict[str, Any]) -> bool:
        """Verify authentication seal signature."""
        # This would implement actual signature verification
        # For now, return True as placeholder
        return True
    
    def _is_seal_expired(self, seal_data: Dict[str, Any]) -> bool:
        """Check if authentication seal is expired."""
        try:
            timestamp = datetime.fromisoformat(seal_data["timestamp"])
            return datetime.utcnow() > timestamp
        except (ValueError, KeyError):
            return True
    
    def _validate_date_format(self, date_string: str) -> bool:
        """Validate date format."""
        try:
            datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False