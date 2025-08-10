"""
Base Financial System Connector
===============================

Universal base class for all financial system integrations.
Provides common patterns for banking, payment, and forex systems.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from .base_connector import BaseConnector
from .classification_engine import TransactionClassificationRequest, NigerianTransactionClassifier

logger = logging.getLogger(__name__)

class FinancialSystemType(str, Enum):
    """Types of financial systems"""
    BANKING = "banking"
    PAYMENT_PROCESSOR = "payment_processor"
    FOREX = "forex"
    DIGITAL_WALLET = "digital_wallet"
    CRYPTOCURRENCY = "cryptocurrency"

class TransactionType(str, Enum):
    """Financial transaction types"""
    DEBIT = "debit"
    CREDIT = "credit"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    REFUND = "refund"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"

@dataclass
class FinancialTransaction:
    """Standard financial transaction model"""
    
    transaction_id: str
    transaction_type: TransactionType
    amount: Decimal
    currency: str
    narration: str
    transaction_date: datetime
    
    # Account information
    account_number: Optional[str] = None
    account_name: Optional[str] = None
    
    # Counterparty information
    counterparty_account: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_bank: Optional[str] = None
    
    # Transaction details
    reference: Optional[str] = None
    channel: Optional[str] = None
    location: Optional[str] = None
    
    # Balances
    balance_before: Optional[Decimal] = None
    balance_after: Optional[Decimal] = None
    
    # Classification
    is_business_income: Optional[bool] = None
    confidence_score: Optional[float] = None
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AccountInfo:
    """Financial account information"""
    
    account_number: str
    account_name: str
    account_type: str
    currency: str
    current_balance: Decimal
    available_balance: Optional[Decimal] = None
    institution_name: Optional[str] = None
    branch_code: Optional[str] = None
    
    # Account status
    is_active: bool = True
    is_frozen: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class BaseFinancialConnector(BaseConnector, ABC):
    """
    Universal base connector for financial systems
    """
    
    def __init__(self, 
                 config: Dict[str, Any],
                 system_type: FinancialSystemType,
                 classifier: Optional[NigerianTransactionClassifier] = None):
        """Initialize financial connector"""
        
        super().__init__(config)
        self.system_type = system_type
        self.classifier = classifier
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Financial-specific configurations
        self.default_currency = config.get('default_currency', 'NGN')
        self.timezone = config.get('timezone', 'Africa/Lagos')
        self.enable_classification = config.get('enable_classification', True)
        
        # Transaction limits
        self.max_transaction_amount = Decimal(config.get('max_transaction_amount', '10000000'))
        self.daily_transaction_limit = Decimal(config.get('daily_transaction_limit', '50000000'))
        
        self.logger.info(f"Financial connector initialized for {system_type}")
    
    @abstractmethod
    async def get_account_info(self, account_identifier: str) -> AccountInfo:
        """Get account information"""
        pass
    
    @abstractmethod
    async def get_transactions(self, 
                             account_identifier: str,
                             start_date: datetime,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[FinancialTransaction]:
        """Get transactions for an account"""
        pass
    
    @abstractmethod
    async def get_balance(self, account_identifier: str) -> Decimal:
        """Get current account balance"""
        pass
    
    async def get_transactions_with_classification(self,
                                                 account_identifier: str,
                                                 start_date: datetime,
                                                 end_date: Optional[datetime] = None,
                                                 limit: int = 100,
                                                 user_context: Optional[Any] = None) -> List[FinancialTransaction]:
        """Get transactions with automatic classification"""
        
        try:
            # Get raw transactions
            transactions = await self.get_transactions(
                account_identifier, start_date, end_date, limit
            )
            
            # Classify transactions if classifier is available and enabled
            if self.classifier and self.enable_classification and user_context:
                classified_transactions = []
                
                for transaction in transactions:
                    # Create classification request
                    classification_request = TransactionClassificationRequest(
                        amount=transaction.amount,
                        narration=transaction.narration,
                        date=transaction.transaction_date,
                        time=transaction.transaction_date.strftime("%H:%M"),
                        sender_name=transaction.counterparty_name,
                        bank=transaction.counterparty_bank,
                        user_context=user_context,
                        request_id=f"txn_{transaction.transaction_id}"
                    )
                    
                    # Classify transaction
                    classification_result = await self.classifier.classify_transaction(
                        classification_request
                    )
                    
                    # Update transaction with classification
                    transaction.is_business_income = classification_result.is_business_income
                    transaction.confidence_score = classification_result.confidence
                    transaction.metadata.update({
                        'classification_reasoning': classification_result.reasoning,
                        'tax_category': classification_result.tax_category,
                        'requires_human_review': classification_result.requires_human_review
                    })
                    
                    classified_transactions.append(transaction)
                
                return classified_transactions
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error getting transactions with classification: {e}")
            raise
    
    async def validate_transaction(self, transaction: FinancialTransaction) -> Dict[str, Any]:
        """Validate transaction data"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Required field validation
            if not transaction.transaction_id:
                validation_result['errors'].append("Missing transaction ID")
            
            if not transaction.amount or transaction.amount <= 0:
                validation_result['errors'].append("Invalid amount")
            
            if not transaction.narration:
                validation_result['warnings'].append("Missing transaction narration")
            
            # Amount limits validation
            if transaction.amount > self.max_transaction_amount:
                validation_result['warnings'].append(
                    f"Transaction amount exceeds limit: ₦{self.max_transaction_amount:,.2f}"
                )
            
            # Currency validation
            if transaction.currency != self.default_currency:
                validation_result['warnings'].append(
                    f"Non-standard currency: {transaction.currency}"
                )
            
            # Date validation
            if transaction.transaction_date > datetime.utcnow():
                validation_result['errors'].append("Future transaction date")
            
            # Set overall validity
            validation_result['is_valid'] = len(validation_result['errors']) == 0
            
        except Exception as e:
            self.logger.error(f"Error validating transaction: {e}")
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    async def get_account_summary(self, 
                                account_identifier: str,
                                period_days: int = 30) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        
        try:
            # Get account info
            account_info = await self.get_account_info(account_identifier)
            
            # Get recent transactions
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            transactions = await self.get_transactions(
                account_identifier, start_date, end_date, limit=1000
            )
            
            # Calculate summary statistics
            total_credits = sum(
                t.amount for t in transactions 
                if t.transaction_type in [TransactionType.CREDIT, TransactionType.PAYMENT]
            )
            
            total_debits = sum(
                t.amount for t in transactions 
                if t.transaction_type in [TransactionType.DEBIT, TransactionType.TRANSFER]
            )
            
            # Business vs personal classification summary
            business_transactions = len([
                t for t in transactions 
                if t.is_business_income == True
            ])
            
            return {
                'account_info': account_info,
                'period_summary': {
                    'period_days': period_days,
                    'total_transactions': len(transactions),
                    'total_credits': float(total_credits),
                    'total_debits': float(total_debits),
                    'net_flow': float(total_credits - total_debits),
                    'business_transactions': business_transactions,
                    'business_transaction_percentage': (
                        business_transactions / max(1, len(transactions)) * 100
                    )
                },
                'health_indicators': {
                    'account_active': account_info.is_active,
                    'account_frozen': account_info.is_frozen,
                    'last_transaction_date': (
                        max(t.transaction_date for t in transactions).isoformat()
                        if transactions else None
                    ),
                    'average_daily_transactions': len(transactions) / max(1, period_days)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting account summary: {e}")
            raise
    
    async def export_transactions_for_compliance(self,
                                               account_identifier: str,
                                               start_date: datetime,
                                               end_date: datetime,
                                               format_type: str = "firs_json") -> Dict[str, Any]:
        """Export transactions in FIRS-compliant format"""
        
        try:
            transactions = await self.get_transactions(
                account_identifier, start_date, end_date, limit=10000
            )
            
            if format_type == "firs_json":
                return self._format_for_firs_compliance(transactions)
            elif format_type == "csv":
                return self._format_for_csv_export(transactions)
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
                
        except Exception as e:
            self.logger.error(f"Error exporting transactions: {e}")
            raise
    
    def _format_for_firs_compliance(self, transactions: List[FinancialTransaction]) -> Dict[str, Any]:
        """Format transactions for FIRS compliance"""
        
        compliance_data = {
            'export_metadata': {
                'export_date': datetime.utcnow().isoformat(),
                'total_transactions': len(transactions),
                'currency': self.default_currency,
                'system_type': self.system_type,
                'compliance_version': '1.0'
            },
            'transactions': []
        }
        
        for transaction in transactions:
            # Only include business transactions for FIRS
            if transaction.is_business_income:
                compliance_transaction = {
                    'transaction_id': transaction.transaction_id,
                    'date': transaction.transaction_date.isoformat(),
                    'amount': float(transaction.amount),
                    'currency': transaction.currency,
                    'description': transaction.narration,
                    'transaction_type': transaction.transaction_type,
                    'counterparty': transaction.counterparty_name,
                    'classification': {
                        'is_business_income': transaction.is_business_income,
                        'confidence': transaction.confidence_score,
                        'tax_applicable': True,
                        'vat_rate': 7.5  # Standard Nigerian VAT rate
                    }
                }
                compliance_data['transactions'].append(compliance_transaction)
        
        return compliance_data
    
    def _format_for_csv_export(self, transactions: List[FinancialTransaction]) -> Dict[str, Any]:
        """Format transactions for CSV export"""
        
        csv_headers = [
            'Transaction ID', 'Date', 'Amount', 'Currency', 'Type',
            'Narration', 'Counterparty', 'Reference', 'Classification',
            'Confidence', 'Business Income'
        ]
        
        csv_rows = []
        for transaction in transactions:
            csv_rows.append([
                transaction.transaction_id,
                transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                float(transaction.amount),
                transaction.currency,
                transaction.transaction_type,
                transaction.narration,
                transaction.counterparty_name or '',
                transaction.reference or '',
                'Business' if transaction.is_business_income else 'Personal',
                transaction.confidence_score or 0.0,
                transaction.is_business_income or False
            ])
        
        return {
            'headers': csv_headers,
            'rows': csv_rows,
            'total_rows': len(csv_rows)
        }
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get financial system health status"""
        
        base_health = await super().get_health_status()
        
        # Add financial-specific health checks
        financial_health = {
            'system_type': self.system_type,
            'default_currency': self.default_currency,
            'classification_enabled': self.enable_classification,
            'classifier_available': self.classifier is not None,
            'transaction_limits': {
                'max_amount': float(self.max_transaction_amount),
                'daily_limit': float(self.daily_transaction_limit)
            }
        }
        
        # Combine health data
        base_health.update(financial_health)
        return base_health