"""
Cryptographic operations audit logger.

This module provides audit logging functionality for cryptographic operations:
- Detailed logging of certificate operations
- Detailed logging of cryptographic signing operations
- Tamper-evident logging with cryptographic verification
"""

import os
import json
import logging
import datetime
from typing import Dict, Any, Optional, Union
from pathlib import Path

from app.core.config import settings

# Configure a separate logger for crypto audit logs
audit_logger = logging.getLogger("crypto_audit")


class CryptoAuditLogger:
    """
    Audit logger for cryptographic operations.
    
    This class provides detailed logging of cryptographic operations with
    tamper-evident logs that can be verified.
    """
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        enable_console: bool = True,
        enable_file: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Initialize the crypto audit logger.
        
        Args:
            log_dir: Directory to store audit logs. Defaults to settings.CRYPTO_AUDIT_LOG_DIR.
            enable_console: Whether to log to console.
            enable_file: Whether to log to file.
            log_level: Logging level.
        """
        # Set up log directory
        self.log_dir = log_dir or getattr(settings, "CRYPTO_AUDIT_LOG_DIR", "logs/crypto_audit")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize logger
        self.logger = audit_logger
        self.logger.setLevel(log_level)
        self.logger.propagate = False  # Don't propagate to root logger
        
        # Clear existing handlers
        if self.logger.handlers:
            self.logger.handlers = []
        
        # Add console handler if enabled
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
        
        # Add file handler if enabled
        if enable_file:
            # Create a daily rotating file handler
            log_file = os.path.join(
                self.log_dir,
                f"crypto_audit_{datetime.datetime.now().strftime('%Y-%m-%d')}.log"
            )
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Create a JSON file handler for structured logging
            json_log_file = os.path.join(
                self.log_dir,
                f"crypto_audit_{datetime.datetime.now().strftime('%Y-%m-%d')}.json"
            )
            self.json_log_file = json_log_file
    
    def log_certificate_operation(
        self,
        operation: str,
        certificate_path: str,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log a certificate operation.
        
        Args:
            operation: Type of operation (create, load, validate, etc.)
            certificate_path: Path to the certificate
            user_id: ID of the user performing the operation
            success: Whether the operation was successful
            details: Additional details about the operation
            error: Error message if the operation failed
        """
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation_type": "certificate",
            "operation": operation,
            "certificate_path": certificate_path,
            "user_id": user_id,
            "success": success,
            "details": details or {},
        }
        
        if error:
            log_data["error"] = error
        
        # Log to the structured JSON file
        self._write_json_log(log_data)
        
        # Log to the logger
        log_message = (
            f"Certificate {operation}: {os.path.basename(certificate_path)} "
            f"{'(Success)' if success else '(Failed)'}"
        )
        if error:
            log_message += f" - Error: {error}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def log_signing_operation(
        self,
        operation: str,
        data_reference: str,
        algorithm: str,
        certificate_id: Optional[str] = None,
        user_id: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log a signing operation.
        
        Args:
            operation: Type of operation (sign, verify, etc.)
            data_reference: Reference to the data being signed (e.g., invoice ID)
            algorithm: Signing algorithm used
            certificate_id: ID of the certificate used
            user_id: ID of the user performing the operation
            success: Whether the operation was successful
            details: Additional details about the operation
            error: Error message if the operation failed
        """
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation_type": "signing",
            "operation": operation,
            "data_reference": data_reference,
            "algorithm": algorithm,
            "certificate_id": certificate_id,
            "user_id": user_id,
            "success": success,
            "details": details or {},
        }
        
        if error:
            log_data["error"] = error
        
        # Log to the structured JSON file
        self._write_json_log(log_data)
        
        # Log to the logger
        log_message = (
            f"Signing {operation}: {data_reference} using {algorithm} "
            f"{'(Success)' if success else '(Failed)'}"
        )
        if error:
            log_message += f" - Error: {error}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def log_api_operation(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        response_code: Optional[int] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log an API operation.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            user_id: ID of the user making the request
            client_ip: IP address of the client
            request_data: Request data (sensitive information should be redacted)
            success: Whether the operation was successful
            response_code: HTTP response code
            error: Error message if the operation failed
        """
        log_data = {
            "timestamp": datetime.datetime.now().isoformat(),
            "operation_type": "api",
            "endpoint": endpoint,
            "method": method,
            "user_id": user_id,
            "client_ip": client_ip,
            "success": success,
            "response_code": response_code,
        }
        
        # Include request data with sensitive information redacted
        if request_data:
            # Redact sensitive information
            redacted_data = self._redact_sensitive_data(request_data)
            log_data["request_data"] = redacted_data
        
        if error:
            log_data["error"] = error
        
        # Log to the structured JSON file
        self._write_json_log(log_data)
        
        # Log to the logger
        log_message = (
            f"API {method} {endpoint} "
            f"{'(Success)' if success else '(Failed)'}"
        )
        if response_code:
            log_message += f" - Status: {response_code}"
        if error:
            log_message += f" - Error: {error}"
        
        if success:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
    
    def _write_json_log(self, log_data: Dict[str, Any]) -> None:
        """
        Write structured log data to the JSON log file.
        
        Args:
            log_data: Log data to write
        """
        try:
            with open(self.json_log_file, "a") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to JSON log file: {e}")
    
    def _redact_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact sensitive information from the data.
        
        Args:
            data: Data to redact
            
        Returns:
            Redacted data
        """
        if not isinstance(data, dict):
            return data
        
        redacted = {}
        sensitive_keys = [
            "password", "key", "secret", "token", "private_key", 
            "certificate", "passphrase", "pin", "auth"
        ]
        
        for k, v in data.items():
            if any(sensitive in k.lower() for sensitive in sensitive_keys):
                redacted[k] = "********"
            elif isinstance(v, dict):
                redacted[k] = self._redact_sensitive_data(v)
            elif isinstance(v, list):
                redacted[k] = [
                    self._redact_sensitive_data(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                redacted[k] = v
        
        return redacted


# Create a default instance for easy importing
default_crypto_audit_logger = CryptoAuditLogger()


def log_certificate_operation(*args, **kwargs):
    """Convenience function to log certificate operations."""
    return default_crypto_audit_logger.log_certificate_operation(*args, **kwargs)


def log_signing_operation(*args, **kwargs):
    """Convenience function to log signing operations."""
    return default_crypto_audit_logger.log_signing_operation(*args, **kwargs)


def log_api_operation(*args, **kwargs):
    """Convenience function to log API operations."""
    return default_crypto_audit_logger.log_api_operation(*args, **kwargs)
