"""
Base Banking System Connector
=============================

Banking-specific base class for Nigerian and international banking integrations.
Handles account management, transaction processing, and regulatory compliance.
"""

import logging
from abc import abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from .base_financial_connector import (
    BaseFinancialConnector, 
    FinancialSystemType, 
    FinancialTransaction,
    AccountInfo,
    TransactionType
)

logger = logging.getLogger(__name__)

class BankingChannel(str, Enum):
    """Banking transaction channels"""
    BRANCH = "branch"
    ATM = "atm"
    INTERNET_BANKING = "internet_banking"
    MOBILE_BANKING = "mobile_banking"
    POS = "pos"
    USSD = "ussd"
    CARD = "card"
    TRANSFER = "transfer"

class AccountType(str, Enum):
    """Nigerian banking account types"""
    SAVINGS = "savings"
    CURRENT = "current"
    DOMICILIARY = "domiciliary"
    FIXED_DEPOSIT = "fixed_deposit"
    BUSINESS = "business"
    CORPORATE = "corporate"

@dataclass
class BankingTransaction(FinancialTransaction):
    """Banking-specific transaction model"""
    
    # Banking-specific fields
    channel: Optional[BankingChannel] = None
    terminal_id: Optional[str] = None
    institution_code: Optional[str] = None
    session_id: Optional[str] = None
    
    # Nigerian banking specifics
    stamp_duty_applied: bool = False
    cot_applied: bool = False  # Commission on Turnover
    vat_applied: bool = False
    
    # Additional banking metadata
    reversal_reference: Optional[str] = None
    is_reversal: bool = False
    original_transaction_id: Optional[str] = None

@dataclass
class BankAccountInfo(AccountInfo):
    """Banking-specific account information"""
    
    # Banking specifics
    account_type: AccountType
    bvn: Optional[str] = None  # Bank Verification Number
    account_officer: Optional[str] = None
    branch_name: Optional[str] = None
    
    # Limits and restrictions
    daily_withdrawal_limit: Optional[Decimal] = None
    daily_transfer_limit: Optional[Decimal] = None
    monthly_transaction_limit: Optional[Decimal] = None
    
    # Account status
    is_restricted: bool = False
    restriction_reason: Optional[str] = None
    last_transaction_date: Optional[datetime] = None

class BaseBankingConnector(BaseFinancialConnector):
    """
    Base connector for banking systems with Nigerian regulatory compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize banking connector"""
        
        super().__init__(config, FinancialSystemType.BANKING)
        
        # Banking-specific configurations
        self.bank_code = config.get('bank_code')
        self.bank_name = config.get('bank_name')
        self.regulatory_compliance = config.get('regulatory_compliance', True)
        
        # Nigerian banking regulations
        self.apply_stamp_duty = config.get('apply_stamp_duty', True)
        self.stamp_duty_threshold = Decimal(config.get('stamp_duty_threshold', '1000'))
        self.cot_rate = Decimal(config.get('cot_rate', '0.005'))  # 0.5%
        self.cot_cap = Decimal(config.get('cot_cap', '3000'))  # ₦3000 cap
        
        self.logger.info(f"Banking connector initialized for {self.bank_name} ({self.bank_code})")
    
    @abstractmethod
    async def get_account_info(self, account_number: str) -> BankAccountInfo:
        """Get banking account information"""
        pass
    
    @abstractmethod
    async def get_transactions(self, 
                             account_number: str,
                             start_date: datetime,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[BankingTransaction]:
        """Get banking transactions"""
        pass
    
    @abstractmethod
    async def validate_account(self, account_number: str) -> Dict[str, Any]:
        """Validate account number and get basic details"""
        pass
    
    @abstractmethod
    async def get_account_statement(self,
                                  account_number: str,
                                  start_date: datetime,
                                  end_date: datetime,
                                  format_type: str = "pdf") -> Dict[str, Any]:
        """Generate account statement"""
        pass
    
    async def get_business_transactions(self,
                                      account_number: str,
                                      start_date: datetime,
                                      end_date: Optional[datetime] = None,
                                      confidence_threshold: float = 0.7) -> List[BankingTransaction]:
        """Get transactions classified as business income"""
        
        try:
            transactions = await self.get_transactions(account_number, start_date, end_date, limit=5000)
            
            business_transactions = []
            for transaction in transactions:
                if (transaction.is_business_income == True and 
                    transaction.confidence_score and 
                    transaction.confidence_score >= confidence_threshold):
                    business_transactions.append(transaction)
            
            self.logger.info(f"Found {len(business_transactions)} business transactions")
            return business_transactions
            
        except Exception as e:
            self.logger.error(f"Error getting business transactions: {e}")
            raise
    
    async def calculate_tax_obligations(self,
                                      account_number: str,
                                      period_start: datetime,
                                      period_end: datetime) -> Dict[str, Any]:
        """Calculate tax obligations from business transactions"""
        
        try:
            business_transactions = await self.get_business_transactions(
                account_number, period_start, period_end
            )
            
            # Calculate totals
            total_business_income = sum(
                t.amount for t in business_transactions
                if t.transaction_type in [TransactionType.CREDIT, TransactionType.PAYMENT]
            )
            
            total_business_expenses = sum(
                t.amount for t in business_transactions
                if t.transaction_type in [TransactionType.DEBIT, TransactionType.TRANSFER]
            )
            
            # Nigerian tax calculations
            vat_applicable_income = total_business_income
            vat_amount = vat_applicable_income * Decimal('0.075')  # 7.5% VAT
            
            # Withholding tax (5% on services, varies by type)
            wht_amount = total_business_income * Decimal('0.05')
            
            return {
                'period': {
                    'start': period_start.isoformat(),
                    'end': period_end.isoformat()
                },
                'business_income': {
                    'total_credits': float(total_business_income),
                    'total_debits': float(total_business_expenses),
                    'net_income': float(total_business_income - total_business_expenses),
                    'transaction_count': len(business_transactions)
                },
                'tax_obligations': {
                    'vat_amount': float(vat_amount),
                    'wht_amount': float(wht_amount),
                    'total_tax_liability': float(vat_amount + wht_amount)
                },
                'compliance_notes': [
                    "Calculations based on automated transaction classification",
                    "Professional tax advice recommended for final filing",
                    "VAT rate: 7.5% (standard Nigerian rate)",
                    "WHT rate: 5% (estimated, varies by transaction type)"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating tax obligations: {e}")
            raise
    
    async def get_monthly_banking_summary(self,
                                        account_number: str,
                                        year: int,
                                        month: int) -> Dict[str, Any]:
        """Get comprehensive monthly banking summary"""
        
        try:
            # Calculate period dates
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Get account info and transactions
            account_info = await self.get_account_info(account_number)
            transactions = await self.get_transactions(account_number, start_date, end_date, limit=10000)
            
            # Categorize transactions
            credits = [t for t in transactions if t.transaction_type in [TransactionType.CREDIT, TransactionType.PAYMENT]]
            debits = [t for t in transactions if t.transaction_type in [TransactionType.DEBIT, TransactionType.TRANSFER]]
            
            # Calculate channel distribution
            channel_distribution = {}
            for transaction in transactions:
                channel = transaction.channel or BankingChannel.BRANCH
                channel_distribution[channel] = channel_distribution.get(channel, 0) + 1
            
            # Calculate fees
            total_stamp_duty = sum(
                Decimal('50') for t in transactions 
                if t.stamp_duty_applied and t.amount >= self.stamp_duty_threshold
            )
            
            total_cot = sum(
                min(t.amount * self.cot_rate, self.cot_cap) for t in transactions
                if t.cot_applied
            )
            
            return {
                'account_summary': {
                    'account_number': account_info.account_number,
                    'account_name': account_info.account_name,
                    'account_type': account_info.account_type,
                    'opening_balance': float(account_info.current_balance),
                    'closing_balance': float(account_info.current_balance)
                },
                'transaction_summary': {
                    'total_transactions': len(transactions),
                    'total_credits': float(sum(t.amount for t in credits)),
                    'total_debits': float(sum(t.amount for t in debits)),
                    'credit_count': len(credits),
                    'debit_count': len(debits)
                },
                'channel_distribution': {
                    channel.value: count for channel, count in channel_distribution.items()
                },
                'fee_summary': {
                    'stamp_duty_total': float(total_stamp_duty),
                    'cot_total': float(total_cot),
                    'total_fees': float(total_stamp_duty + total_cot)
                },
                'business_classification': {
                    'business_transactions': len([t for t in transactions if t.is_business_income]),
                    'personal_transactions': len([t for t in transactions if t.is_business_income == False]),
                    'unclassified_transactions': len([t for t in transactions if t.is_business_income is None])
                },
                'period': {
                    'year': year,
                    'month': month,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating monthly summary: {e}")
            raise
    
    async def check_regulatory_compliance(self, 
                                        account_number: str,
                                        period_days: int = 30) -> Dict[str, Any]:
        """Check regulatory compliance for Nigerian banking"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            account_info = await self.get_account_info(account_number)
            transactions = await self.get_transactions(account_number, start_date, end_date)
            
            compliance_report = {
                'compliance_status': 'compliant',
                'violations': [],
                'warnings': [],
                'recommendations': []
            }
            
            # Check BVN requirement
            if not account_info.bvn:
                compliance_report['violations'].append("BVN not linked to account")
                compliance_report['compliance_status'] = 'non_compliant'
            
            # Check transaction limits
            large_transactions = [t for t in transactions if t.amount > Decimal('5000000')]  # ₦5M
            if large_transactions:
                compliance_report['warnings'].append(
                    f"{len(large_transactions)} large transactions require additional reporting"
                )
            
            # Check single customer exposure
            daily_totals = {}
            for transaction in transactions:
                date_key = transaction.transaction_date.date()
                daily_totals[date_key] = daily_totals.get(date_key, Decimal('0')) + transaction.amount
            
            for date, total in daily_totals.items():
                if total > self.daily_transaction_limit:
                    compliance_report['warnings'].append(
                        f"Daily limit exceeded on {date}: ₦{total:,.2f}"
                    )
            
            # Check for suspicious patterns
            night_transactions = [
                t for t in transactions 
                if t.transaction_date.hour < 6 or t.transaction_date.hour > 22
            ]
            
            if len(night_transactions) > len(transactions) * 0.3:
                compliance_report['warnings'].append(
                    "High percentage of off-hours transactions detected"
                )
            
            return compliance_report
            
        except Exception as e:
            self.logger.error(f"Error checking regulatory compliance: {e}")
            raise
    
    async def generate_regulatory_report(self,
                                       account_number: str,
                                       start_date: datetime,
                                       end_date: datetime,
                                       report_type: str = "cbn_compliance") -> Dict[str, Any]:
        """Generate regulatory reports for CBN/FIRS compliance"""
        
        try:
            account_info = await self.get_account_info(account_number)
            transactions = await self.get_transactions(account_number, start_date, end_date, limit=50000)
            
            if report_type == "cbn_compliance":
                return await self._generate_cbn_report(account_info, transactions, start_date, end_date)
            elif report_type == "firs_compliance":
                return await self._generate_firs_report(account_info, transactions, start_date, end_date)
            else:
                raise ValueError(f"Unsupported report type: {report_type}")
                
        except Exception as e:
            self.logger.error(f"Error generating regulatory report: {e}")
            raise
    
    async def _generate_cbn_report(self,
                                 account_info: BankAccountInfo,
                                 transactions: List[BankingTransaction],
                                 start_date: datetime,
                                 end_date: datetime) -> Dict[str, Any]:
        """Generate CBN compliance report"""
        
        # Large transaction reporting (₦5M+ in a day)
        large_transactions = [t for t in transactions if t.amount >= Decimal('5000000')]
        
        # Cash transaction reporting (₦5M+ in cash)
        cash_transactions = [
            t for t in transactions 
            if t.channel in [BankingChannel.BRANCH, BankingChannel.ATM] and 
            t.amount >= Decimal('5000000')
        ]
        
        return {
            'report_type': 'cbn_compliance',
            'bank_code': self.bank_code,
            'bank_name': self.bank_name,
            'account_details': {
                'account_number': account_info.account_number,
                'account_name': account_info.account_name,
                'account_type': account_info.account_type,
                'bvn': account_info.bvn
            },
            'reporting_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'large_transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'date': t.transaction_date.isoformat(),
                    'amount': float(t.amount),
                    'counterparty': t.counterparty_name,
                    'narration': t.narration
                }
                for t in large_transactions
            ],
            'cash_transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'date': t.transaction_date.isoformat(),
                    'amount': float(t.amount),
                    'channel': t.channel
                }
                for t in cash_transactions
            ],
            'summary': {
                'total_transactions': len(transactions),
                'large_transaction_count': len(large_transactions),
                'cash_transaction_count': len(cash_transactions),
                'total_volume': float(sum(t.amount for t in transactions))
            }
        }
    
    async def _generate_firs_report(self,
                                  account_info: BankAccountInfo,
                                  transactions: List[BankingTransaction],
                                  start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Generate FIRS tax compliance report"""
        
        # Business transactions for tax reporting
        business_transactions = [t for t in transactions if t.is_business_income]
        
        # Calculate VAT and WHT
        total_business_income = sum(
            t.amount for t in business_transactions
            if t.transaction_type in [TransactionType.CREDIT, TransactionType.PAYMENT]
        )
        
        return {
            'report_type': 'firs_compliance',
            'taxpayer_details': {
                'account_number': account_info.account_number,
                'account_name': account_info.account_name,
                'bvn': account_info.bvn
            },
            'tax_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'business_transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'date': t.transaction_date.isoformat(),
                    'amount': float(t.amount),
                    'description': t.narration,
                    'counterparty': t.counterparty_name,
                    'confidence': t.confidence_score
                }
                for t in business_transactions
            ],
            'tax_summary': {
                'total_business_income': float(total_business_income),
                'vat_applicable': float(total_business_income * Decimal('0.075')),
                'wht_applicable': float(total_business_income * Decimal('0.05')),
                'transaction_count': len(business_transactions)
            },
            'classification_quality': {
                'high_confidence_transactions': len([
                    t for t in business_transactions if t.confidence_score and t.confidence_score > 0.8
                ]),
                'medium_confidence_transactions': len([
                    t for t in business_transactions if t.confidence_score and 0.6 <= t.confidence_score <= 0.8
                ]),
                'low_confidence_transactions': len([
                    t for t in business_transactions if t.confidence_score and t.confidence_score < 0.6
                ])
            }
        }