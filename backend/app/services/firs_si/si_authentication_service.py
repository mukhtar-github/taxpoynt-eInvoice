"""
FIRS SI Authentication Service

This service implements System Integrator (SI) specific authentication
functionality for invoice origin verification and ERP system authentication.

SI Role Responsibilities:
- Authenticate invoice origins from ERP systems
- Validate ERP system credentials and connections
- Manage SI-specific authentication tokens
- Handle ERP system authentication protocols
- Verify invoice data integrity and authenticity
- Manage authentication for certificate-based signing

This service is part of the firs_si package and focuses on the SI's core
responsibility of authenticating invoice origins and data integrity.
"""

import logging
import hashlib
import hmac
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.models.api_credential import ApiCredential
from app.services.firs_core.audit_service import AuditService

logger = logging.getLogger(__name__)


class SIAuthenticationService:
    """Service for System Integrator authentication operations."""
    
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)
    
    def authenticate_invoice_origin(self, invoice_data: Dict[str, Any], 
                                   user_id: str) -> Dict[str, Any]:
        """
        Authenticate the origin of invoice data from ERP system.
        
        Args:
            invoice_data: Invoice data from ERP system
            user_id: User ID initiating the authentication
            
        Returns:
            Authentication result with status and verification details
        """
        try:
            # Generate authentication hash for invoice origin
            auth_hash = self._generate_origin_hash(invoice_data)
            
            # Verify invoice data integrity
            integrity_check = self._verify_data_integrity(invoice_data)
            
            # Log authentication attempt
            self.audit_service.log_authentication_attempt(
                user_id=user_id,
                authentication_type="invoice_origin",
                success=integrity_check,
                details={"auth_hash": auth_hash}
            )
            
            return {
                "authenticated": integrity_check,
                "auth_hash": auth_hash,
                "timestamp": datetime.utcnow().isoformat(),
                "verification_code": self._generate_verification_code(auth_hash)
            }
            
        except Exception as e:
            logger.error(f"Invoice origin authentication failed: {str(e)}")
            raise
    
    def authenticate_erp_connection(self, erp_credentials: Dict[str, Any]) -> bool:
        """
        Authenticate ERP system connection and credentials.
        
        Args:
            erp_credentials: ERP system connection credentials
            
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Validate ERP credentials format
            if not self._validate_erp_credentials(erp_credentials):
                return False
            
            # Test ERP connection
            connection_test = self._test_erp_connection(erp_credentials)
            
            # Log ERP authentication
            self.audit_service.log_erp_authentication(
                erp_system=erp_credentials.get("system_type"),
                success=connection_test,
                host=erp_credentials.get("host")
            )
            
            return connection_test
            
        except Exception as e:
            logger.error(f"ERP authentication failed: {str(e)}")
            return False
    
    def _generate_origin_hash(self, invoice_data: Dict[str, Any]) -> str:
        """Generate authentication hash for invoice origin."""
        # Create deterministic hash from invoice key fields
        key_fields = [
            str(invoice_data.get("invoice_number", "")),
            str(invoice_data.get("supplier_tin", "")),
            str(invoice_data.get("invoice_date", "")),
            str(invoice_data.get("total_amount", ""))
        ]
        
        combined_data = "|".join(key_fields)
        return hashlib.sha256(combined_data.encode()).hexdigest()
    
    def _verify_data_integrity(self, invoice_data: Dict[str, Any]) -> bool:
        """Verify invoice data integrity and completeness."""
        required_fields = [
            "invoice_number", "supplier_tin", "invoice_date", 
            "total_amount", "currency_code"
        ]
        
        # Check all required fields are present
        for field in required_fields:
            if field not in invoice_data or not invoice_data[field]:
                return False
        
        # Additional integrity checks
        try:
            # Validate amount is numeric
            float(invoice_data["total_amount"])
            
            # Validate TIN format (basic check)
            tin = invoice_data["supplier_tin"]
            if not tin.isdigit() or len(tin) < 8:
                return False
            
            return True
            
        except (ValueError, TypeError):
            return False
    
    def _validate_erp_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate ERP credentials format."""
        required_fields = ["system_type", "host", "username", "password"]
        return all(field in credentials and credentials[field] for field in required_fields)
    
    def _test_erp_connection(self, credentials: Dict[str, Any]) -> bool:
        """Test ERP system connection."""
        # This would implement actual ERP connection testing
        # For now, return True as placeholder
        return True
    
    def _generate_verification_code(self, auth_hash: str) -> str:
        """Generate verification code for authentication."""
        secret = settings.SECRET_KEY.encode()
        return hmac.new(secret, auth_hash.encode(), hashlib.sha256).hexdigest()[:8]