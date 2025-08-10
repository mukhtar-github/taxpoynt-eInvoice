"""
IRN Generator

Handles generation of unique Invoice Reference Numbers (IRNs).
Extracts core IRN generation logic from the monolithic service.
"""

import uuid
import hashlib
import hmac
import base64
import secrets
from datetime import datetime
from typing import Tuple, Dict, Any, Optional


class IRNGenerator:
    """Generate unique Invoice Reference Numbers"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.irn_prefix = "IRN"
    
    def generate_irn(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """
        Generate a unique Invoice Reference Number (IRN) based on invoice data.
        
        Args:
            invoice_data: Dictionary containing invoice details
            
        Returns:
            Tuple containing (irn_value, verification_code, hash_value)
        """
        # Create deterministic hash from invoice data
        invoice_hash = self._create_invoice_hash(invoice_data)
        
        # Generate unique IRN
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        unique_id = str(uuid.uuid4())[:8].upper()
        irn_value = f"{self.irn_prefix}{timestamp}{unique_id}"
        
        # Generate verification code
        verification_code = self._generate_verification_code(irn_value, invoice_hash)
        
        # Create final hash for integrity
        final_hash = self._create_final_hash(irn_value, verification_code)
        
        return irn_value, verification_code, final_hash
    
    def generate_simple_irn(self, invoice_id: str) -> str:
        """Generate simple IRN for basic use cases"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        invoice_hash = hashlib.md5(invoice_id.encode()).hexdigest()[:8].upper()
        return f"{self.irn_prefix}{timestamp}{invoice_hash}"
    
    def _create_invoice_hash(self, invoice_data: Dict[str, Any]) -> str:
        """Create deterministic hash from invoice data"""
        # Extract key fields for hashing
        key_fields = [
            str(invoice_data.get('customer_id', '')),
            str(invoice_data.get('invoice_number', '')),
            str(invoice_data.get('total_amount', '')),
            str(invoice_data.get('invoice_date', ''))
        ]
        
        # Create consistent string
        hash_string = '|'.join(key_fields)
        
        # Generate hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def _generate_verification_code(self, irn_value: str, invoice_hash: str) -> str:
        """Generate verification code using HMAC"""
        message = f"{irn_value}:{invoice_hash}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Return first 8 characters of base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')[:8]
    
    def _create_final_hash(self, irn_value: str, verification_code: str) -> str:
        """Create final hash for data integrity"""
        combined = f"{irn_value}:{verification_code}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def validate_irn_format(self, irn_value: str) -> bool:
        """Validate IRN format structure"""
        if not irn_value or not isinstance(irn_value, str):
            return False
        
        # Check prefix
        if not irn_value.startswith(self.irn_prefix):
            return False
        
        # Check length (IRN + 14 digit timestamp + 8 char unique ID)
        expected_length = len(self.irn_prefix) + 14 + 8
        if len(irn_value) != expected_length:
            return False
        
        return True
    
    def extract_timestamp_from_irn(self, irn_value: str) -> Optional[datetime]:
        """Extract timestamp from IRN"""
        if not self.validate_irn_format(irn_value):
            return None
        
        try:
            # Extract timestamp part (after prefix, 14 characters)
            prefix_len = len(self.irn_prefix)
            timestamp_str = irn_value[prefix_len:prefix_len + 14]
            return datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        except ValueError:
            return None