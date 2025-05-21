"""
FIRS Integration Production Safeguards

This module implements safeguards for the FIRS e-Invoice integration to ensure
reliable operation in production environments. It provides validation, monitoring,
and batch tracking functionality.
"""

import os
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from uuid import UUID, uuid4
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.utils.logger import get_logger
from app.db.session import get_db
from app.models.irn import IRNRecord, IRNValidationRecord
from app.cache.irn_cache import IRNCache

logger = get_logger(__name__)

class FIRSSafeguards:
    """
    Production safeguards for FIRS e-Invoice integration.
    
    This class implements validation, monitoring, and tracking
    functionality to ensure reliable operation of the FIRS integration
    in production environments.
    """
    
    def __init__(self):
        """Initialize the safeguards system."""
        # Initialize the IRN cache for quick validation
        self.irn_cache = IRNCache()
        
        # Create transaction log directory if it doesn't exist
        self.transaction_log_dir = os.path.join(settings.LOG_DIR, 'firs_transactions')
        os.makedirs(self.transaction_log_dir, exist_ok=True)
        
        # Set up transaction logger
        self.transaction_logger = logging.getLogger("firs_transactions")
        self.transaction_logger.setLevel(logging.INFO)
        
        # Add file handler for transaction logs
        transaction_log_file = os.path.join(
            self.transaction_log_dir, 
            f"firs_transactions_{datetime.now().strftime('%Y%m%d')}.log"
        )
        handler = logging.FileHandler(transaction_log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        self.transaction_logger.addHandler(handler)
    
    def validate_invoice_before_submission(self, invoice_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an invoice before submission to FIRS.
        
        Args:
            invoice_data: The invoice data to validate
            
        Returns:
            Tuple containing (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = [
            'invoice_number', 
            'invoice_type', 
            'invoice_date', 
            'currency_code',
            'supplier',
            'customer',
            'items',
            'totals'
        ]
        
        for field in required_fields:
            if field not in invoice_data:
                errors.append(f"Missing required field: {field}")
        
        # Check supplier and customer information
        for party_type in ['supplier', 'customer']:
            if party_type in invoice_data:
                party = invoice_data[party_type]
                
                # TIN validation for Nigerian parties
                if party.get('address', {}).get('country', '') in ['NG', 'NGA', 'Nigeria']:
                    tin = party.get('tin', '')
                    if not tin:
                        errors.append(f"{party_type.capitalize()} TIN is required for Nigerian entities")
                    elif not self._is_valid_nigerian_tin(tin):
                        errors.append(f"Invalid Nigerian TIN format for {party_type}: {tin}")
        
        # Validate line items
        if 'items' in invoice_data and isinstance(invoice_data['items'], list):
            if not invoice_data['items']:
                errors.append("Invoice must have at least one line item")
            
            for i, item in enumerate(invoice_data['items']):
                if not item.get('description'):
                    errors.append(f"Item {i+1} missing description")
                
                if not isinstance(item.get('quantity'), (int, float)) or item.get('quantity') <= 0:
                    errors.append(f"Item {i+1} has invalid quantity")
                
                if not isinstance(item.get('unit_price'), (int, float)) or item.get('unit_price') < 0:
                    errors.append(f"Item {i+1} has invalid unit price")
        
        # Validate totals match the sum of line items
        if 'totals' in invoice_data and 'items' in invoice_data:
            items = invoice_data['items']
            totals = invoice_data['totals']
            
            calculated_subtotal = sum(item.get('subtotal', 0) for item in items)
            calculated_tax = sum(item.get('tax_amount', 0) for item in items)
            calculated_total = calculated_subtotal + calculated_tax
            
            # Allow small difference due to floating point calculations (0.01 precision)
            if abs(calculated_subtotal - totals.get('subtotal', 0)) > 0.01:
                errors.append(f"Subtotal mismatch: {totals.get('subtotal')} vs calculated {calculated_subtotal}")
            
            if abs(calculated_tax - totals.get('tax_total', 0)) > 0.01:
                errors.append(f"Tax total mismatch: {totals.get('tax_total')} vs calculated {calculated_tax}")
            
            if abs(calculated_total - totals.get('grand_total', 0)) > 0.01:
                errors.append(f"Grand total mismatch: {totals.get('grand_total')} vs calculated {calculated_total}")
        
        # Check for duplicate invoice
        if self._is_duplicate_invoice(invoice_data.get('invoice_number', ''), 
                                      invoice_data.get('supplier', {}).get('tin', '')):
            errors.append("Potential duplicate invoice detected - same invoice number used by supplier within 24h")
        
        return (len(errors) == 0, errors)
    
    def _is_valid_nigerian_tin(self, tin: str) -> bool:
        """
        Validate a Nigerian TIN format.
        
        Args:
            tin: The TIN to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Remove NG prefix if present
        if tin.upper().startswith('NG'):
            tin = tin[2:].strip()
        
        # Check for basic format (12345678-1234)
        import re
        pattern = r'^\d{8}-\d{4}$'
        
        # If pattern doesn't match, try to normalize and check again
        if not re.match(pattern, tin):
            # Try to normalize to 12345678-1234 format
            tin_digits = ''.join(c for c in tin if c.isdigit())
            if len(tin_digits) >= 12:
                tin = f"{tin_digits[:8]}-{tin_digits[8:12]}"
                return re.match(pattern, tin) is not None
            return False
        
        return True
    
    def _is_duplicate_invoice(self, invoice_number: str, supplier_tin: str) -> bool:
        """
        Check if an invoice is a potential duplicate.
        
        Args:
            invoice_number: The invoice number to check
            supplier_tin: The supplier's TIN
            
        Returns:
            True if potential duplicate, False otherwise
        """
        # Generate a unique key for the invoice
        invoice_key = f"{supplier_tin}:{invoice_number}"
        
        # Check in memory cache first
        if self.irn_cache.exists(invoice_key):
            return True
        
        # Check transaction logs for the past 24 hours
        log_files = self._get_recent_transaction_logs(1)
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if invoice_key in line and "SUBMITTED" in line:
                            return True
            except Exception as e:
                logger.error(f"Error checking transaction logs for duplicates: {str(e)}")
        
        return False
    
    def _get_recent_transaction_logs(self, days: int = 1) -> List[str]:
        """
        Get paths to recent transaction log files.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of file paths
        """
        log_files = []
        
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y%m%d')
            log_file = os.path.join(self.transaction_log_dir, f"firs_transactions_{date}.log")
            if os.path.exists(log_file):
                log_files.append(log_file)
        
        return log_files
    
    def log_transaction(self, transaction_type: str, payload: Dict[str, Any], response: Dict[str, Any]) -> None:
        """
        Log a FIRS API transaction.
        
        Args:
            transaction_type: Type of transaction (e.g., 'VALIDATE_IRN', 'SUBMIT_INVOICE')
            payload: The data sent to FIRS
            response: The response received from FIRS
        """
        # Create transaction record
        transaction_id = str(uuid4())
        timestamp = datetime.now().isoformat()
        
        # Extract key identifiers
        invoice_number = None
        supplier_tin = None
        irn = None
        submission_id = None
        status = "UNKNOWN"
        
        if transaction_type == 'SUBMIT_INVOICE':
            invoice_number = payload.get('invoice_number', 'UNKNOWN')
            supplier_tin = payload.get('supplier', {}).get('tin', 'UNKNOWN')
            status = "SUBMITTED" if response.get('success', False) else "FAILED"
            submission_id = response.get('submission_id', 'UNKNOWN')
        elif transaction_type == 'VALIDATE_IRN':
            irn = payload.get('irn', 'UNKNOWN')
            invoice_number = payload.get('invoice_reference', 'UNKNOWN')
            status = "VALID" if response.get('success', False) and response.get('status') == "VALID" else "INVALID"
        
        # Create transaction summary
        transaction_summary = {
            "transaction_id": transaction_id,
            "timestamp": timestamp,
            "type": transaction_type,
            "invoice_number": invoice_number,
            "supplier_tin": supplier_tin,
            "irn": irn,
            "submission_id": submission_id,
            "status": status
        }
        
        # Log the transaction
        self.transaction_logger.info(
            f"{transaction_id} | {transaction_type} | {status} | " +
            f"InvNum: {invoice_number} | SupplierTIN: {supplier_tin} | " +
            f"IRN: {irn} | SubmissionID: {submission_id}"
        )
        
        # Store full transaction details if detailed logging is enabled
        if settings.FIRS_DETAILED_TRANSACTION_LOGGING:
            transaction_detail_path = os.path.join(
                self.transaction_log_dir,
                f"transaction_{transaction_id}.json"
            )
            
            try:
                with open(transaction_detail_path, 'w') as f:
                    transaction_detail = {
                        "summary": transaction_summary,
                        "payload": self._sanitize_sensitive_data(payload),
                        "response": response
                    }
                    json.dump(transaction_detail, f, indent=2)
            except Exception as e:
                logger.error(f"Error storing transaction details: {str(e)}")
    
    def _sanitize_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive data from transaction logs.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        # Create a deep copy to avoid modifying the original
        import copy
        sanitized = copy.deepcopy(data)
        
        # List of sensitive fields to mask
        sensitive_fields = [
            'password', 'api_key', 'api_secret', 'access_token', 
            'secret', 'private_key', 'signature'
        ]
        
        def _sanitize_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    _sanitize_dict(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            _sanitize_dict(item)
                elif key.lower() in sensitive_fields:
                    d[key] = "***REDACTED***"
        
        _sanitize_dict(sanitized)
        return sanitized
    
    def monitor_batch_status(self, batch_id: str, db: Session) -> Dict[str, Any]:
        """
        Monitor the status of a batch submission.
        
        Args:
            batch_id: The batch ID to monitor
            db: Database session
            
        Returns:
            Batch status information
        """
        # Check transaction logs for this batch
        batch_invoices = []
        processed_count = 0
        success_count = 0
        failed_count = 0
        
        log_files = self._get_recent_transaction_logs(7)  # Check the last week for batch data
        
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if f"SubmissionID: {batch_id}" in line:
                            parts = line.split('|')
                            if len(parts) >= 3:
                                status = parts[2].strip()
                                if status == "SUBMITTED":
                                    processed_count += 1
                                    success_count += 1
                                elif status == "FAILED":
                                    processed_count += 1
                                    failed_count += 1
                                
                                # Extract invoice number if present
                                for part in parts:
                                    if "InvNum:" in part:
                                        inv_num = part.split("InvNum:")[1].strip()
                                        if inv_num and inv_num != "UNKNOWN":
                                            batch_invoices.append(inv_num)
            except Exception as e:
                logger.error(f"Error reading batch status from logs: {str(e)}")
        
        # Get detailed transaction data if available
        transaction_details = []
        for filename in os.listdir(self.transaction_log_dir):
            if filename.startswith("transaction_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(self.transaction_log_dir, filename), 'r') as f:
                        data = json.load(f)
                        if data.get("summary", {}).get("submission_id") == batch_id:
                            transaction_details.append(data)
                except Exception as e:
                    logger.error(f"Error reading transaction details: {str(e)}")
        
        # Compile batch status
        return {
            "batch_id": batch_id,
            "invoices_total": len(set(batch_invoices)),
            "invoices_processed": processed_count,
            "invoices_succeeded": success_count,
            "invoices_failed": failed_count,
            "success_percentage": (success_count / processed_count * 100) if processed_count > 0 else 0,
            "transaction_details": transaction_details if settings.FIRS_DETAILED_TRANSACTION_LOGGING else []
        }
    
    def check_environment_status(self) -> Dict[str, Any]:
        """
        Check the status of the FIRS integration environment.
        
        Returns:
            Environment status information
        """
        status = {
            "api_connection": "UNKNOWN",
            "reference_data": "UNKNOWN",
            "crypto_keys": "UNKNOWN",
            "recent_transactions": []
        }
        
        # Check API keys and credentials are configured
        if settings.FIRS_API_KEY and settings.FIRS_API_SECRET:
            status["api_credentials"] = "CONFIGURED"
        else:
            status["api_credentials"] = "MISSING"
        
        # Check crypto keys
        if os.path.exists(settings.FIRS_CERTIFICATE_PATH):
            status["crypto_keys"] = "AVAILABLE"
        else:
            status["crypto_keys"] = "MISSING"
        
        # Check reference data
        reference_files = [
            os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'invoice_types.json'),
            os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'currencies.json'),
            os.path.join(settings.REFERENCE_DATA_DIR, 'firs', 'vat_exemptions.json')
        ]
        
        missing_files = [f for f in reference_files if not os.path.exists(f)]
        
        if not missing_files:
            status["reference_data"] = "COMPLETE"
        elif len(missing_files) < len(reference_files):
            status["reference_data"] = "PARTIAL"
            status["missing_reference_files"] = missing_files
        else:
            status["reference_data"] = "MISSING"
        
        # Get recent transactions
        try:
            recent_logs = self._get_recent_transaction_logs(1)
            transactions = []
            
            for log_file in recent_logs:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    # Get the last 10 transactions
                    for line in lines[-10:]:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            transactions.append({
                                "id": parts[0].strip(),
                                "type": parts[1].strip(),
                                "status": parts[2].strip(),
                                "timestamp": line.split('-')[0].strip()
                            })
            
            status["recent_transactions"] = transactions
            
            # Determine API connection status from recent transactions
            if transactions:
                success_count = sum(1 for t in transactions if "SUBMITTED" in t["status"] or "VALID" in t["status"])
                if success_count > 0:
                    status["api_connection"] = "ACTIVE"
                else:
                    status["api_connection"] = "FAILING"
            else:
                status["api_connection"] = "NO_RECENT_ACTIVITY"
        except Exception as e:
            logger.error(f"Error getting recent transactions: {str(e)}")
            status["api_connection"] = "ERROR"
        
        return status

# Create a default instance for easy importing
firs_safeguards = FIRSSafeguards()
