"""
QR Code Generator

Handles generation of QR codes for invoice verification.
Creates QR codes containing IRN and invoice verification data.
"""

import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional, Union
import hashlib


class QRCodeGenerator:
    """Generate QR codes for invoice verification"""
    
    def __init__(self):
        self.qr_version = "1.0"
        self.max_data_size = 2048  # Maximum QR code data size
    
    def generate_qr_data(
        self,
        irn_value: str,
        verification_code: str,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate QR code data structure for invoice verification
        
        Args:
            irn_value: Generated IRN
            verification_code: IRN verification code
            invoice_data: Invoice details for QR code
            
        Returns:
            QR code data structure
        """
        # Extract essential invoice data for QR code
        qr_invoice_data = self._extract_qr_invoice_data(invoice_data)
        
        qr_data = {
            "version": self.qr_version,
            "irn": irn_value,
            "verification_code": verification_code,
            "timestamp": datetime.now().isoformat(),
            "invoice": qr_invoice_data,
            "checksum": ""
        }
        
        # Generate checksum for data integrity
        qr_data["checksum"] = self._generate_checksum(qr_data)
        
        return qr_data
    
    def generate_qr_string(
        self,
        irn_value: str,
        verification_code: str,
        invoice_data: Dict[str, Any],
        format_type: str = "json"
    ) -> str:
        """
        Generate QR code string in specified format
        
        Args:
            irn_value: Generated IRN
            verification_code: IRN verification code
            invoice_data: Invoice details
            format_type: Output format (json, compact, url)
            
        Returns:
            QR code string ready for encoding
        """
        qr_data = self.generate_qr_data(irn_value, verification_code, invoice_data)
        
        if format_type == "json":
            return json.dumps(qr_data, separators=(',', ':'))
        elif format_type == "compact":
            return self._generate_compact_format(qr_data)
        elif format_type == "url":
            return self._generate_url_format(qr_data)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def generate_qr_code_image(
        self,
        qr_string: str,
        size: int = 200,
        error_correction: str = "M"
    ) -> Dict[str, Any]:
        """
        Generate QR code image (placeholder - requires qrcode library)
        
        Args:
            qr_string: String to encode in QR code
            size: QR code size in pixels
            error_correction: Error correction level (L, M, Q, H)
            
        Returns:
            QR code image information
        """
        # TODO: Implement actual QR code generation using qrcode library
        # This is a placeholder implementation
        
        return {
            "qr_data": qr_string,
            "size": size,
            "error_correction": error_correction,
            "format": "PNG",
            "base64_image": self._generate_placeholder_qr_image(qr_string),
            "generated_at": datetime.now().isoformat()
        }
    
    def _extract_qr_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract essential invoice data for QR code"""
        return {
            "number": invoice_data.get("invoice_number", ""),
            "date": invoice_data.get("invoice_date", ""),
            "amount": invoice_data.get("total_amount", 0),
            "currency": invoice_data.get("currency", "NGN"),
            "customer": invoice_data.get("customer_name", ""),
            "tax_id": invoice_data.get("customer_tax_id", "")
        }
    
    def _generate_compact_format(self, qr_data: Dict[str, Any]) -> str:
        """Generate compact QR code format"""
        # Create pipe-separated format for smaller QR codes
        invoice = qr_data["invoice"]
        compact_parts = [
            qr_data["irn"],
            qr_data["verification_code"],
            invoice.get("number", ""),
            invoice.get("date", ""),
            str(invoice.get("amount", "")),
            invoice.get("currency", "NGN"),
            qr_data["checksum"][:8]  # Shortened checksum
        ]
        
        return "|".join(compact_parts)
    
    def _generate_url_format(self, qr_data: Dict[str, Any]) -> str:
        """Generate URL format for QR code"""
        # Create verification URL
        base_url = "https://verify.taxpoynt.com/irn/"
        params = {
            "irn": qr_data["irn"],
            "code": qr_data["verification_code"],
            "checksum": qr_data["checksum"][:12]
        }
        
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"
    
    def _generate_checksum(self, qr_data: Dict[str, Any]) -> str:
        """Generate checksum for QR data integrity"""
        # Create checksum without the checksum field itself
        data_copy = qr_data.copy()
        data_copy.pop("checksum", None)
        
        # Create deterministic string
        data_string = json.dumps(data_copy, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA256 hash
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    
    def _generate_placeholder_qr_image(self, qr_string: str) -> str:
        """Generate placeholder QR image as base64"""
        # This is a placeholder - real implementation would use qrcode library
        placeholder_data = f"QR_CODE_IMAGE_FOR:{qr_string[:50]}..."
        return base64.b64encode(placeholder_data.encode('utf-8')).decode('utf-8')
    
    def validate_qr_data(self, qr_data: Dict[str, Any]) -> bool:
        """Validate QR code data structure"""
        required_fields = ["version", "irn", "verification_code", "invoice", "checksum"]
        
        if not all(field in qr_data for field in required_fields):
            return False
        
        # Validate checksum
        expected_checksum = self._generate_checksum(qr_data)
        return qr_data["checksum"] == expected_checksum
    
    def parse_qr_string(self, qr_string: str, format_type: str = "json") -> Optional[Dict[str, Any]]:
        """Parse QR code string back to data structure"""
        try:
            if format_type == "json":
                return json.loads(qr_string)
            elif format_type == "compact":
                return self._parse_compact_format(qr_string)
            elif format_type == "url":
                return self._parse_url_format(qr_string)
            else:
                return None
        except (json.JSONDecodeError, ValueError):
            return None
    
    def _parse_compact_format(self, compact_string: str) -> Dict[str, Any]:
        """Parse compact format QR string"""
        parts = compact_string.split("|")
        if len(parts) < 7:
            raise ValueError("Invalid compact format")
        
        return {
            "irn": parts[0],
            "verification_code": parts[1],
            "invoice": {
                "number": parts[2],
                "date": parts[3],
                "amount": float(parts[4]) if parts[4] else 0,
                "currency": parts[5]
            },
            "checksum": parts[6]
        }
    
    def _parse_url_format(self, url_string: str) -> Dict[str, Any]:
        """Parse URL format QR string"""
        # Simple URL parameter parsing
        if "?" not in url_string:
            raise ValueError("Invalid URL format")
        
        params_string = url_string.split("?")[1]
        params = {}
        for param in params_string.split("&"):
            key, value = param.split("=")
            params[key] = value
        
        return {
            "irn": params.get("irn", ""),
            "verification_code": params.get("code", ""),
            "checksum": params.get("checksum", "")
        }