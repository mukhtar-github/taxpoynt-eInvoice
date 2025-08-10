"""
Universal Transaction Model
===========================

Base transaction model that standardizes transaction data from all connector types.
This model serves as the input format for the universal transaction processing pipeline.

All external connectors (ERP, CRM, POS, E-commerce, Accounting, Banking) convert their
native transaction formats to this universal format before processing.

Features:
- Standardized field mapping across all business systems
- Flexible metadata storage for connector-specific data
- Source tracking for audit and debugging
- Validation-ready structure for Nigerian compliance
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass
class UniversalTransaction:
    """
    Universal transaction model for all connector types.
    
    This model provides a standardized representation of transaction data
    that works across ERP, CRM, POS, E-commerce, Accounting, and Banking systems.
    """
    
    # Core transaction fields (required)
    id: str                           # Unique transaction identifier
    amount: float                     # Transaction amount
    currency: str                     # Currency code (typically NGN)
    date: datetime                    # Transaction date
    description: str                  # Transaction description
    
    # Business context fields (optional but important)
    account_number: Optional[str] = None      # Customer/account identifier
    reference: Optional[str] = None           # Reference number (PO, Invoice, etc.)
    category: Optional[str] = None            # Transaction category/type
    
    # Connector-specific metadata
    erp_metadata: Dict[str, Any] = field(default_factory=dict)          # ERP-specific fields
    crm_metadata: Dict[str, Any] = field(default_factory=dict)          # CRM-specific fields
    pos_metadata: Dict[str, Any] = field(default_factory=dict)          # POS-specific fields
    ecommerce_metadata: Dict[str, Any] = field(default_factory=dict)    # E-commerce fields
    banking_metadata: Dict[str, Any] = field(default_factory=dict)      # Banking fields
    
    # Source tracking
    source_system: str = "unknown"           # Connector type identifier
    source_connector: str = "unknown"        # Specific connector instance
    source_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Raw data preservation
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Original transaction data
    
    # Processing hints
    processing_hints: Dict[str, Any] = field(default_factory=dict)      # Connector-specific processing guidance
    
    def __post_init__(self):
        """Post-initialization validation and normalization."""
        # Ensure amount is a valid number
        if not isinstance(self.amount, (int, float, Decimal)):
            raise ValueError(f"Invalid amount type: {type(self.amount)}")
        
        # Ensure currency is uppercase
        if self.currency:
            self.currency = self.currency.upper()
        
        # Ensure description is not empty
        if not self.description.strip():
            self.description = f"Transaction {self.id}"
        
        # Validate date
        if not isinstance(self.date, datetime):
            raise ValueError(f"Invalid date type: {type(self.date)}")
    
    @property
    def amount_decimal(self) -> Decimal:
        """Get amount as Decimal for precise calculations."""
        return Decimal(str(self.amount))
    
    @property
    def is_nigerian_transaction(self) -> bool:
        """Check if this is a Nigerian Naira transaction."""
        return self.currency == 'NGN'
    
    @property
    def is_foreign_currency(self) -> bool:
        """Check if this is a foreign currency transaction."""
        return self.currency != 'NGN'
    
    @property
    def connector_metadata(self) -> Dict[str, Any]:
        """Get connector-specific metadata based on source system."""
        if 'erp' in self.source_system.lower():
            return self.erp_metadata
        elif 'crm' in self.source_system.lower():
            return self.crm_metadata
        elif 'pos' in self.source_system.lower():
            return self.pos_metadata
        elif 'ecommerce' in self.source_system.lower():
            return self.ecommerce_metadata
        elif 'banking' in self.source_system.lower():
            return self.banking_metadata
        else:
            return {}
    
    def get_field_value(self, field_name: str, default: Any = None) -> Any:
        """
        Get field value with fallback to metadata and raw data.
        
        Args:
            field_name: Field name to retrieve
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        # Check direct attributes first
        if hasattr(self, field_name):
            value = getattr(self, field_name)
            if value is not None:
                return value
        
        # Check connector metadata
        connector_meta = self.connector_metadata
        if field_name in connector_meta:
            return connector_meta[field_name]
        
        # Check raw data
        if field_name in self.raw_data:
            return self.raw_data[field_name]
        
        # Check processing hints
        if field_name in self.processing_hints:
            return self.processing_hints[field_name]
        
        return default
    
    def add_processing_hint(self, key: str, value: Any):
        """Add a processing hint for the universal pipeline."""
        self.processing_hints[key] = value
    
    def update_metadata(self, metadata: Dict[str, Any]):
        """Update connector-specific metadata."""
        connector_meta = self.connector_metadata
        connector_meta.update(metadata)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'id': self.id,
            'amount': self.amount,
            'currency': self.currency,
            'date': self.date.isoformat(),
            'description': self.description,
            'account_number': self.account_number,
            'reference': self.reference,
            'category': self.category,
            'source_system': self.source_system,
            'source_connector': self.source_connector,
            'source_timestamp': self.source_timestamp.isoformat(),
            'erp_metadata': self.erp_metadata,
            'crm_metadata': self.crm_metadata,
            'pos_metadata': self.pos_metadata,
            'ecommerce_metadata': self.ecommerce_metadata,
            'banking_metadata': self.banking_metadata,
            'processing_hints': self.processing_hints,
            'raw_data': self.raw_data,
            'is_nigerian_transaction': self.is_nigerian_transaction,
            'is_foreign_currency': self.is_foreign_currency
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UniversalTransaction':
        """Create UniversalTransaction from dictionary."""
        # Parse datetime fields
        date = data.get('date')
        if isinstance(date, str):
            date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        
        source_timestamp = data.get('source_timestamp')
        if isinstance(source_timestamp, str):
            source_timestamp = datetime.fromisoformat(source_timestamp.replace('Z', '+00:00'))
        elif source_timestamp is None:
            source_timestamp = datetime.utcnow()
        
        return cls(
            id=data['id'],
            amount=data['amount'],
            currency=data['currency'],
            date=date,
            description=data['description'],
            account_number=data.get('account_number'),
            reference=data.get('reference'),
            category=data.get('category'),
            source_system=data.get('source_system', 'unknown'),
            source_connector=data.get('source_connector', 'unknown'),
            source_timestamp=source_timestamp,
            erp_metadata=data.get('erp_metadata', {}),
            crm_metadata=data.get('crm_metadata', {}),
            pos_metadata=data.get('pos_metadata', {}),
            ecommerce_metadata=data.get('ecommerce_metadata', {}),
            banking_metadata=data.get('banking_metadata', {}),
            processing_hints=data.get('processing_hints', {}),
            raw_data=data.get('raw_data', {})
        )
    
    @classmethod
    def from_erp_invoice(
        cls,
        invoice_data: Dict[str, Any],
        source_system: str,
        connector_name: str = "erp_connector"
    ) -> 'UniversalTransaction':
        """Create UniversalTransaction from ERP invoice data."""
        # Extract core fields with ERP-specific mapping
        transaction_id = (
            invoice_data.get('id') or 
            invoice_data.get('invoice_id') or 
            invoice_data.get('document_number') or 
            str(invoice_data.get('billing_document_id', 'unknown'))
        )
        
        amount = float(invoice_data.get('total_amount') or 
                      invoice_data.get('amount') or 
                      invoice_data.get('net_amount') or 0.0)
        
        # Parse date
        invoice_date = invoice_data.get('invoice_date') or invoice_data.get('document_date')
        if isinstance(invoice_date, str):
            try:
                invoice_date = datetime.fromisoformat(invoice_date.replace('Z', '+00:00'))
            except ValueError:
                invoice_date = datetime.utcnow()
        elif not isinstance(invoice_date, datetime):
            invoice_date = datetime.utcnow()
        
        description = (invoice_data.get('description') or
                      invoice_data.get('invoice_description') or
                      f"ERP Invoice {transaction_id}")
        
        return cls(
            id=transaction_id,
            amount=amount,
            currency=invoice_data.get('currency', 'NGN'),
            date=invoice_date,
            description=description,
            account_number=invoice_data.get('customer_account') or invoice_data.get('sold_to_party'),
            reference=invoice_data.get('reference_number') or invoice_data.get('purchase_order'),
            category=invoice_data.get('document_type', 'invoice'),
            source_system=source_system,
            source_connector=connector_name,
            erp_metadata={
                'invoice_number': invoice_data.get('invoice_number'),
                'customer_code': invoice_data.get('customer_code'),
                'cost_center': invoice_data.get('cost_center'),
                'profit_center': invoice_data.get('profit_center'),
                'company_code': invoice_data.get('company_code'),
                'document_type': invoice_data.get('document_type'),
                'posting_date': invoice_data.get('posting_date'),
                'due_date': invoice_data.get('due_date'),
                'payment_terms': invoice_data.get('payment_terms'),
                'tax_amount': invoice_data.get('tax_amount'),
                'vat_amount': invoice_data.get('vat_amount'),
                'line_items': invoice_data.get('line_items', [])
            },
            raw_data=invoice_data
        )
    
    @classmethod
    def from_crm_transaction(
        cls,
        transaction_data: Dict[str, Any],
        source_system: str,
        connector_name: str = "crm_connector"
    ) -> 'UniversalTransaction':
        """Create UniversalTransaction from CRM transaction data."""
        transaction_id = (
            transaction_data.get('id') or 
            transaction_data.get('deal_id') or 
            transaction_data.get('opportunity_id') or
            'unknown'
        )
        
        amount = float(transaction_data.get('amount') or 
                      transaction_data.get('deal_value') or 
                      transaction_data.get('revenue') or 0.0)
        
        # Parse date
        close_date = transaction_data.get('close_date') or transaction_data.get('created_date')
        if isinstance(close_date, str):
            try:
                close_date = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
            except ValueError:
                close_date = datetime.utcnow()
        elif not isinstance(close_date, datetime):
            close_date = datetime.utcnow()
        
        return cls(
            id=str(transaction_id),
            amount=amount,
            currency=transaction_data.get('currency', 'NGN'),
            date=close_date,
            description=transaction_data.get('description') or f"CRM Deal {transaction_id}",
            account_number=transaction_data.get('account_id') or transaction_data.get('company_id'),
            reference=transaction_data.get('reference') or transaction_data.get('deal_number'),
            category=transaction_data.get('stage') or 'service',
            source_system=source_system,
            source_connector=connector_name,
            crm_metadata={
                'deal_name': transaction_data.get('deal_name'),
                'stage': transaction_data.get('stage'),
                'probability': transaction_data.get('probability'),
                'owner': transaction_data.get('owner'),
                'account_name': transaction_data.get('account_name'),
                'contact_name': transaction_data.get('contact_name'),
                'service_type': transaction_data.get('service_type'),
                'project_id': transaction_data.get('project_id')
            },
            raw_data=transaction_data
        )
    
    @classmethod
    def from_pos_transaction(
        cls,
        transaction_data: Dict[str, Any],
        source_system: str,
        connector_name: str = "pos_connector"
    ) -> 'UniversalTransaction':
        """Create UniversalTransaction from POS transaction data."""
        transaction_id = (
            transaction_data.get('id') or 
            transaction_data.get('transaction_id') or 
            transaction_data.get('receipt_number') or
            'unknown'
        )
        
        amount = float(transaction_data.get('total') or 
                      transaction_data.get('amount') or 
                      transaction_data.get('grand_total') or 0.0)
        
        # Parse date
        transaction_date = transaction_data.get('transaction_date') or transaction_data.get('created_at')
        if isinstance(transaction_date, str):
            try:
                transaction_date = datetime.fromisoformat(transaction_date.replace('Z', '+00:00'))
            except ValueError:
                transaction_date = datetime.utcnow()
        elif not isinstance(transaction_date, datetime):
            transaction_date = datetime.utcnow()
        
        return cls(
            id=str(transaction_id),
            amount=amount,
            currency=transaction_data.get('currency', 'NGN'),
            date=transaction_date,
            description=transaction_data.get('description') or f"POS Sale {transaction_id}",
            account_number=transaction_data.get('customer_id'),
            reference=transaction_data.get('receipt_number'),
            category='retail',
            source_system=source_system,
            source_connector=connector_name,
            pos_metadata={
                'receipt_number': transaction_data.get('receipt_number'),
                'terminal_id': transaction_data.get('terminal_id'),
                'cashier_id': transaction_data.get('cashier_id'),
                'payment_method': transaction_data.get('payment_method'),
                'items': transaction_data.get('items', []),
                'tax_amount': transaction_data.get('tax_amount'),
                'discount_amount': transaction_data.get('discount_amount')
            },
            raw_data=transaction_data
        )


# Utility functions for creating universal transactions

def create_universal_transaction_from_any_source(
    data: Dict[str, Any],
    source_system: str,
    connector_name: str = "unknown"
) -> UniversalTransaction:
    """
    Create a universal transaction from any source data.
    
    This function attempts to intelligently map fields based on common patterns.
    """
    # Try to determine source type from system name or data structure
    if 'erp' in source_system.lower() or any(field in data for field in ['invoice_number', 'document_number', 'billing_document']):
        return UniversalTransaction.from_erp_invoice(data, source_system, connector_name)
    elif 'crm' in source_system.lower() or any(field in data for field in ['deal_id', 'opportunity_id', 'deal_value']):
        return UniversalTransaction.from_crm_transaction(data, source_system, connector_name)
    elif 'pos' in source_system.lower() or any(field in data for field in ['receipt_number', 'terminal_id', 'cashier_id']):
        return UniversalTransaction.from_pos_transaction(data, source_system, connector_name)
    else:
        # Generic mapping for unknown sources
        return UniversalTransaction(
            id=str(data.get('id', 'unknown')),
            amount=float(data.get('amount', 0.0)),
            currency=data.get('currency', 'NGN'),
            date=datetime.utcnow(),
            description=data.get('description', f"Transaction from {source_system}"),
            source_system=source_system,
            source_connector=connector_name,
            raw_data=data
        )