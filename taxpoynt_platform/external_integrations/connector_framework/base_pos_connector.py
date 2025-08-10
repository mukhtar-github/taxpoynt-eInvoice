"""
Base POS Connector for TaxPoynt eInvoice System
Provides a standardized interface for Point of Sale (POS) system integrations.
Self-contained architecture within taxpoynt_platform framework.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel

from .base_connector import BaseConnector, ConnectorType


class POSTransaction(BaseModel):
    """
    POS transaction model for taxpoynt_platform architecture.
    Designed for optimal FIRS compliance and Nigerian market requirements.
    """
    transaction_id: str
    location_id: Optional[str] = None
    amount: float
    currency: str = "NGN"
    payment_method: str
    timestamp: datetime
    items: List[Dict[str, Any]] = []
    customer_info: Optional[Dict[str, Any]] = None
    tax_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # FIRS compliance fields for Nigerian market
    tin_number: Optional[str] = None
    invoice_reference: Optional[str] = None
    firs_validated: bool = False
    irn_number: Optional[str] = None  # Invoice Reference Number for FIRS


class POSWebhookEvent(BaseModel):
    """
    Webhook event model for real-time POS updates in taxpoynt_platform.
    Self-contained design for event-driven architecture.
    """
    event_type: str
    event_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    signature: Optional[str] = None
    processed: bool = False


class POSLocation(BaseModel):
    """
    POS location/store model optimized for Nigerian business environments.
    Supports multi-location retail chains and franchise operations.
    """
    location_id: str
    name: str
    address: Optional[Dict[str, Any]] = None
    timezone: Optional[str] = "Africa/Lagos"
    currency: str = "NGN"
    tax_settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class POSPaymentMethod(BaseModel):
    """
    Payment method model specifically designed for Nigerian financial ecosystem.
    Supports local payment providers and digital payment innovations.
    """
    method_id: str
    name: str
    type: str  # CARD, CASH, TRANSFER, MOBILE_MONEY, USSD, QR_CODE, CRYPTO
    provider: Optional[str] = None  # Paystack, Flutterwave, Interswitch, Remita, etc.
    fees: Optional[Dict[str, Any]] = None
    processing_time: Optional[str] = None  # Instant, 24hrs, T+1, etc.
    limits: Optional[Dict[str, Any]] = None  # Daily/transaction limits
    enabled: bool = True
    nigerian_compliant: bool = True


class POSInventoryItem(BaseModel):
    """
    Inventory management model with Nigerian business considerations.
    Includes local tax rates, currency handling, and regulatory compliance.
    """
    item_id: str
    sku: Optional[str] = None
    name: str
    category: Optional[str] = None
    price: float
    currency: str = "NGN"
    stock_quantity: Optional[int] = None
    tax_rate: float = 0.075  # Nigerian VAT 7.5%
    metadata: Optional[Dict[str, Any]] = None


class POSRefund(BaseModel):
    """
    Refund/return model with Nigerian regulatory compliance.
    Supports partial refunds, exchange transactions, and audit trails.
    """
    refund_id: str
    original_transaction_id: str
    amount: float
    currency: str = "NGN"
    reason: Optional[str] = None
    timestamp: datetime
    approved_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BasePOSConnector(BaseConnector, ABC):
    """
    Abstract base class for Point of Sale (POS) system integrations in taxpoynt_platform.
    
    Self-contained architecture optimized for Nigerian market requirements:
    - Real-time transaction processing with FIRS compliance
    - Multi-currency support with NGN focus
    - Nigerian payment provider integrations
    - VAT and tax handling (7.5% Nigerian rate)
    - Multi-location retail chain support
    - Event-driven webhook architecture
    - Receipt and invoice generation
    - Inventory management capabilities
    - Comprehensive audit trails
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the POS connector.
        
        Args:
            config: Configuration dictionary containing POS-specific settings
        """
        super().__init__(config, ConnectorType.POS)
        self.logger = logging.getLogger(__name__)
        
        # POS-specific configuration
        self.webhook_url = config.get('webhook_url')
        self.webhook_secret = config.get('webhook_secret')
        self.default_location = config.get('default_location')
        self.currency = config.get('currency', 'NGN')
        self.tax_rate = config.get('tax_rate', 0.075)  # Nigerian VAT 7.5%
        
        # Nigerian market specific configurations
        self.firs_enabled = config.get('firs_enabled', True)
        self.tin_number = config.get('tin_number')
        self.cbn_compliant = config.get('cbn_compliant', True)  # Central Bank of Nigeria
        
        # Nigerian payment providers
        self.paystack_enabled = config.get('paystack_enabled', False)
        self.flutterwave_enabled = config.get('flutterwave_enabled', False)
        self.interswitch_enabled = config.get('interswitch_enabled', False)
        self.remita_enabled = config.get('remita_enabled', False)

    @abstractmethod
    async def get_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Retrieve transactions from the POS system.
        
        Args:
            filters: Filter criteria including:
                - location_id: Specific location/store
                - start_date: Start date for transaction range
                - end_date: End date for transaction range
                - payment_method: Filter by payment method
                - min_amount: Minimum transaction amount
                - max_amount: Maximum transaction amount
                - customer_id: Specific customer transactions
            limit: Maximum number of transactions to return
        
        Returns:
            List of POSTransaction objects
        """
        pass

    @abstractmethod
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve a specific transaction by ID.
        
        Args:
            transaction_id: Transaction identifier
        
        Returns:
            POSTransaction object or None if not found
        """
        pass

    @abstractmethod
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> POSWebhookEvent:
        """
        Process incoming webhook from POS system.
        
        Args:
            webhook_data: Raw webhook payload
        
        Returns:
            Processed POSWebhookEvent
        """
        pass

    @abstractmethod
    async def verify_webhook_signature(
        self, 
        payload: str, 
        signature: str
    ) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature to verify
        
        Returns:
            True if signature is valid, False otherwise
        """
        pass

    @abstractmethod
    async def get_locations(self) -> List[POSLocation]:
        """
        Retrieve all locations/stores from POS system.
        
        Returns:
            List of POSLocation objects
        """
        pass

    @abstractmethod
    async def get_payment_methods(self) -> List[POSPaymentMethod]:
        """
        Retrieve available payment methods.
        
        Returns:
            List of POSPaymentMethod objects
        """
        pass

    @abstractmethod
    async def transform_transaction_to_invoice(
        self,
        transaction_id: str,
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform POS transaction to FIRS-compliant invoice.
        
        Args:
            transaction_id: Transaction to transform
            transformation_options: Additional settings including:
                - issue_date: Invoice issue date
                - due_date: Invoice due date
                - invoice_number: Custom invoice number
                - customer_tin: Customer TIN number
                - include_tax_breakdown: Detailed tax information
        
        Returns:
            FIRS-compliant invoice data (UBL format)
        """
        pass

    # Optional methods for advanced POS features

    async def get_inventory(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[POSInventoryItem]:
        """
        Retrieve inventory items from POS system.
        
        Args:
            filters: Filter criteria for inventory items
        
        Returns:
            List of POSInventoryItem objects
        """
        # Default implementation returns empty list
        # Override in specific connectors that support inventory
        return []

    async def sync_inventory(
        self,
        items: List[POSInventoryItem]
    ) -> Dict[str, Any]:
        """
        Synchronize inventory items to POS system.
        
        Args:
            items: Inventory items to sync
        
        Returns:
            Sync results and status
        """
        # Default implementation
        return {
            'success': False,
            'message': 'Inventory sync not supported by this connector',
            'synced_count': 0
        }

    async def process_refund(
        self,
        refund_data: POSRefund
    ) -> Dict[str, Any]:
        """
        Process refund/return transaction.
        
        Args:
            refund_data: Refund information
        
        Returns:
            Refund processing result
        """
        # Default implementation
        return {
            'success': False,
            'message': 'Refund processing not supported by this connector',
            'refund_id': None
        }

    async def get_daily_summary(
        self,
        date: datetime,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get daily sales summary for reporting.
        
        Args:
            date: Date for summary
            location_id: Specific location (optional)
        
        Returns:
            Daily summary data
        """
        try:
            # Get transactions for the day
            filters = {
                'start_date': date.replace(hour=0, minute=0, second=0),
                'end_date': date.replace(hour=23, minute=59, second=59)
            }
            
            if location_id:
                filters['location_id'] = location_id
            
            transactions = await self.get_transactions(filters=filters)
            
            # Calculate summary
            total_sales = sum(t.amount for t in transactions)
            transaction_count = len(transactions)
            
            # Payment method breakdown
            payment_methods = {}
            for transaction in transactions:
                method = transaction.payment_method
                if method not in payment_methods:
                    payment_methods[method] = {'count': 0, 'amount': 0}
                payment_methods[method]['count'] += 1
                payment_methods[method]['amount'] += transaction.amount
            
            # Tax summary
            total_tax = sum(
                transaction.tax_info.get('amount', 0) 
                if transaction.tax_info else 0
                for transaction in transactions
            )
            
            return {
                'date': date.isoformat(),
                'location_id': location_id,
                'total_sales': total_sales,
                'total_tax': total_tax,
                'transaction_count': transaction_count,
                'payment_methods': payment_methods,
                'currency': self.currency
            }
            
        except Exception as e:
            self.logger.error(f"Error generating daily summary: {str(e)}")
            return {
                'error': str(e),
                'date': date.isoformat(),
                'location_id': location_id
            }

    async def sync_transactions(
        self,
        sync_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize transactions from POS system.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of transactions per batch
                - location_id: Specific location to sync
        
        Returns:
            Synchronization results
        """
        try:
            options = sync_options or {}
            batch_size = options.get('batch_size', 1000)
            
            self.logger.info(f"Starting transaction synchronization with options: {options}")
            
            # Build filter based on sync options
            filters = {}
            
            if options.get('location_id'):
                filters['location_id'] = options['location_id']
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                filters['start_date'] = options['last_sync_date']
            
            # Get all transactions matching criteria
            all_transactions = await self.get_transactions(filters=filters)
            
            # Process in batches
            batches = [all_transactions[i:i + batch_size] for i in range(0, len(all_transactions), batch_size)]
            processed_count = 0
            
            sync_results = {
                'total_records': len(all_transactions),
                'batches_processed': len(batches),
                'batch_size': batch_size,
                'processed_count': 0,
                'sync_timestamp': datetime.now().isoformat(),
                'transactions': all_transactions
            }
            
            for batch_index, batch in enumerate(batches):
                self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} records)")
                processed_count += len(batch)
                
                # Simulate batch processing delay for rate limiting
                await self._rate_limit_delay()
            
            sync_results['processed_count'] = processed_count
            
            self.logger.info(f"Synchronization completed: {processed_count} transactions processed")
            return sync_results
            
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            return {
                'error': str(e),
                'sync_timestamp': datetime.now().isoformat(),
                'processed_count': 0
            }

    def get_supported_features(self) -> List[str]:
        """
        Get list of features supported by this POS connector.
        
        Returns:
            List of supported feature names
        """
        return [
            'transaction_retrieval',
            'webhook_processing',
            'location_management',
            'payment_methods',
            'invoice_transformation',
            'firs_compliance',
            'nigerian_tax_handling',
            'daily_reporting',
            'transaction_sync',
            'multi_currency',
            'real_time_processing'
        ]

    def get_nigerian_payment_providers(self) -> List[str]:
        """
        Get comprehensive list of Nigerian payment providers and methods.
        Tailored for the Nigerian financial ecosystem and regulatory environment.
        
        Returns:
            List of Nigerian payment provider names
        """
        providers = ['CASH', 'CARD']
        
        # Nigerian fintech providers
        if self.paystack_enabled:
            providers.append('PAYSTACK')
        
        if self.flutterwave_enabled:
            providers.append('FLUTTERWAVE')
        
        if self.interswitch_enabled:
            providers.append('INTERSWITCH')
        
        if self.remita_enabled:
            providers.append('REMITA')
        
        # Additional Nigerian payment methods and providers
        providers.extend([
            'OPAY',
            'KUDA',
            'PALMPAY',
            'QUICKTELLER',
            'GTBANK_737',
            'ZENITH_BANK',
            'ACCESS_BANK',
            'UBA',
            'FIRST_BANK',
            'UNION_BANK',
            'STERLING_BANK',
            'FCMB',
            'USSD_PAYMENTS',
            'QR_CODE_PAYMENTS',
            'NFC_PAYMENTS',
            'CRYPTO_NAIRA'  # For future CBDC integration
        ])
        
        return providers

    async def validate_firs_compliance(
        self,
        transaction: POSTransaction
    ) -> Dict[str, Any]:
        """
        Validate transaction for FIRS compliance.
        
        Args:
            transaction: Transaction to validate
        
        Returns:
            Validation results
        """
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields for FIRS
        if not transaction.currency or transaction.currency != 'NGN':
            validation_results['warnings'].append('Currency should be NGN for FIRS compliance')
        
        if transaction.amount <= 0:
            validation_results['errors'].append('Transaction amount must be greater than zero')
            validation_results['valid'] = False
        
        # Check tax information
        if not transaction.tax_info:
            validation_results['warnings'].append('Tax information missing')
        elif transaction.tax_info.get('rate', 0) != self.tax_rate:
            validation_results['warnings'].append(f'Tax rate should be {self.tax_rate * 100}% for Nigerian VAT')
        
        # Check TIN if provided
        if transaction.tin_number and not self._validate_nigerian_tin(transaction.tin_number):
            validation_results['errors'].append('Invalid Nigerian TIN format')
            validation_results['valid'] = False
        
        return validation_results

    def _validate_nigerian_tin(self, tin: str) -> bool:
        """
        Validate Nigerian Tax Identification Number format.
        
        Args:
            tin: TIN to validate
        
        Returns:
            True if valid format, False otherwise
        """
        # Nigerian TIN format: 8 digits + 4 digits + 1 check digit
        # Example: 12345678-0001-9
        import re
        pattern = r'^\d{8}-\d{4}-\d{1}$'
        return bool(re.match(pattern, tin)) if tin else False