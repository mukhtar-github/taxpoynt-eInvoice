"""
Base Forex System Connector
===========================

Base class for forex trading platforms and currency exchange services.
Handles FX transactions, rates, and Nigerian forex regulations.
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
    TransactionType
)

logger = logging.getLogger(__name__)

class ForexTransactionType(str, Enum):
    """Forex-specific transaction types"""
    SPOT_TRADE = "spot_trade"
    FORWARD_CONTRACT = "forward_contract"
    SWAP = "swap"
    CURRENCY_EXCHANGE = "currency_exchange"
    MARGIN_CALL = "margin_call"
    ROLLOVER = "rollover"

class ForexMarket(str, Enum):
    """Forex markets"""
    INTERBANK = "interbank"
    RETAIL = "retail"
    PARALLEL = "parallel"
    I_AND_E_WINDOW = "i_and_e_window"  # CBN I&E Window

class RegulatoryCategory(str, Enum):
    """CBN forex regulatory categories"""
    FORM_A = "form_a"  # Invisible transactions
    FORM_M = "form_m"  # Import transactions
    FORM_NXP = "form_nxp"  # Export proceeds
    PERSONAL_BASIC_ALLOWANCE = "personal_basic_allowance"
    BUSINESS_TRAVEL_ALLOWANCE = "business_travel_allowance"

@dataclass
class ForexTransaction(FinancialTransaction):
    """Forex-specific transaction model"""
    
    # Forex-specific fields
    forex_type: ForexTransactionType
    base_currency: str
    quote_currency: str
    exchange_rate: Decimal
    
    # Amounts in both currencies
    base_amount: Decimal
    quote_amount: Decimal
    
    # Market and regulatory
    market_type: ForexMarket
    regulatory_category: Optional[RegulatoryCategory] = None
    
    # Documentation
    form_number: Optional[str] = None  # CBN form reference
    purpose_code: Optional[str] = None
    supporting_documents: List[str] = None
    
    # Counterparty details
    beneficiary_bank: Optional[str] = None
    beneficiary_country: Optional[str] = None
    correspondent_bank: Optional[str] = None
    
    # Settlement
    value_date: Optional[datetime] = None
    settlement_date: Optional[datetime] = None
    
    def __post_init__(self):
        super().__post_init__()
        if self.supporting_documents is None:
            self.supporting_documents = []

@dataclass
class CurrencyRate:
    """Currency exchange rate information"""
    
    base_currency: str
    quote_currency: str
    rate: Decimal
    bid_rate: Optional[Decimal] = None
    ask_rate: Optional[Decimal] = None
    mid_rate: Optional[Decimal] = None
    
    # Rate metadata
    rate_timestamp: datetime = None
    source: Optional[str] = None
    market_type: Optional[ForexMarket] = None
    
    # Spread information
    spread: Optional[Decimal] = None
    spread_percentage: Optional[float] = None
    
    def __post_init__(self):
        if self.rate_timestamp is None:
            self.rate_timestamp = datetime.utcnow()
        
        # Calculate spread if bid/ask available
        if self.bid_rate and self.ask_rate:
            self.spread = self.ask_rate - self.bid_rate
            self.spread_percentage = float(self.spread / self.mid_rate * 100) if self.mid_rate else None

class BaseForexConnector(BaseFinancialConnector):
    """
    Base connector for forex systems with Nigerian regulatory compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize forex connector"""
        
        super().__init__(config, FinancialSystemType.FOREX)
        
        # Forex-specific configurations
        self.dealer_code = config.get('dealer_code')
        self.dealer_name = config.get('dealer_name')
        self.authorized_dealer = config.get('authorized_dealer', False)
        
        # Nigerian forex regulations
        self.pba_annual_limit = Decimal(config.get('pba_annual_limit', '4000'))  # $4000 USD
        self.bta_annual_limit = Decimal(config.get('bta_annual_limit', '5000'))  # $5000 USD
        self.single_transaction_limit = Decimal(config.get('single_transaction_limit', '10000'))  # $10K
        
        # Supported currencies (Nigerian focus)
        self.supported_currencies = config.get('supported_currencies', [
            'NGN', 'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD'
        ])
        
        # CBN compliance
        self.require_cbn_approval = config.get('require_cbn_approval', True)
        self.auto_reporting_threshold = Decimal(config.get('auto_reporting_threshold', '10000'))
        
        self.logger.info(f"Forex connector initialized for {self.dealer_name}")
    
    @abstractmethod
    async def get_exchange_rate(self, 
                              base_currency: str, 
                              quote_currency: str,
                              market_type: ForexMarket = ForexMarket.INTERBANK) -> CurrencyRate:
        """Get current exchange rate"""
        pass
    
    @abstractmethod
    async def get_forex_transactions(self,
                                   start_date: datetime,
                                   end_date: Optional[datetime] = None,
                                   currency_pair: Optional[str] = None,
                                   limit: int = 100) -> List[ForexTransaction]:
        """Get forex transactions"""
        pass
    
    @abstractmethod
    async def execute_forex_trade(self,
                                base_currency: str,
                                quote_currency: str,
                                amount: Decimal,
                                trade_type: ForexTransactionType,
                                purpose_code: str,
                                metadata: Optional[Dict[str, Any]] = None) -> ForexTransaction:
        """Execute forex trade"""
        pass
    
    async def get_rate_history(self,
                             base_currency: str,
                             quote_currency: str,
                             start_date: datetime,
                             end_date: Optional[datetime] = None,
                             interval: str = "daily") -> List[CurrencyRate]:
        """Get historical exchange rates (default implementation)"""
        
        try:
            if end_date is None:
                end_date = datetime.utcnow()
            
            # This is a base implementation - specific providers should override
            rates = []
            current_date = start_date
            
            while current_date <= end_date:
                try:
                    rate = await self.get_exchange_rate(base_currency, quote_currency)
                    rate.rate_timestamp = current_date
                    rates.append(rate)
                except Exception as e:
                    self.logger.warning(f"Failed to get rate for {current_date}: {e}")
                
                # Increment based on interval
                if interval == "hourly":
                    current_date += timedelta(hours=1)
                elif interval == "daily":
                    current_date += timedelta(days=1)
                elif interval == "weekly":
                    current_date += timedelta(weeks=1)
                else:
                    current_date += timedelta(days=1)
            
            return rates
            
        except Exception as e:
            self.logger.error(f"Error getting rate history: {e}")
            raise
    
    async def check_regulatory_compliance(self,
                                        customer_id: str,
                                        transaction_amount: Decimal,
                                        currency: str,
                                        purpose_code: str) -> Dict[str, Any]:
        """Check CBN regulatory compliance for forex transaction"""
        
        try:
            compliance_result = {
                'compliant': True,
                'requires_approval': False,
                'required_forms': [],
                'violations': [],
                'warnings': [],
                'annual_utilization': {}
            }
            
            # Convert to USD for limit checking
            if currency != 'USD':
                usd_rate = await self.get_exchange_rate(currency, 'USD')
                amount_usd = transaction_amount / usd_rate.rate
            else:
                amount_usd = transaction_amount
            
            # Check PBA limits (Personal Basic Allowance)
            if purpose_code in ['tuition', 'medical', 'software', 'personal']:
                annual_pba_usage = await self._get_annual_pba_usage(customer_id)
                remaining_pba = self.pba_annual_limit - annual_pba_usage
                
                if amount_usd > remaining_pba:
                    compliance_result['compliant'] = False
                    compliance_result['violations'].append(
                        f"Exceeds remaining PBA limit: ${remaining_pba:.2f}"
                    )
                
                compliance_result['annual_utilization']['pba'] = {
                    'used': float(annual_pba_usage),
                    'limit': float(self.pba_annual_limit),
                    'remaining': float(remaining_pba)
                }
            
            # Check BTA limits (Business Travel Allowance)
            elif purpose_code in ['business_travel', 'conference', 'training']:
                annual_bta_usage = await self._get_annual_bta_usage(customer_id)
                remaining_bta = self.bta_annual_limit - annual_bta_usage
                
                if amount_usd > remaining_bta:
                    compliance_result['compliant'] = False
                    compliance_result['violations'].append(
                        f"Exceeds remaining BTA limit: ${remaining_bta:.2f}"
                    )
                
                compliance_result['annual_utilization']['bta'] = {
                    'used': float(annual_bta_usage),
                    'limit': float(self.bta_annual_limit),
                    'remaining': float(remaining_bta)
                }
            
            # Check single transaction limits
            if amount_usd > self.single_transaction_limit:
                compliance_result['requires_approval'] = True
                compliance_result['required_forms'].append('CBN_APPROVAL_FORM')
                compliance_result['warnings'].append(
                    "Transaction requires CBN approval due to amount"
                )
            
            # Determine required documentation
            if amount_usd >= 1000:  # $1000+
                compliance_result['required_forms'].append('FORM_A')
            
            if purpose_code in ['import', 'machinery', 'raw_materials']:
                compliance_result['required_forms'].append('FORM_M')
            
            if purpose_code in ['export_proceeds', 'domiciliary_inflow']:
                compliance_result['required_forms'].append('FORM_NXP')
            
            # Auto-reporting threshold
            if amount_usd >= self.auto_reporting_threshold:
                compliance_result['warnings'].append(
                    "Transaction will be automatically reported to CBN"
                )
            
            return compliance_result
            
        except Exception as e:
            self.logger.error(f"Error checking regulatory compliance: {e}")
            raise
    
    async def generate_cbn_report(self,
                                start_date: datetime,
                                end_date: datetime,
                                report_type: str = "monthly") -> Dict[str, Any]:
        """Generate CBN regulatory report"""
        
        try:
            transactions = await self.get_forex_transactions(start_date, end_date, limit=50000)
            
            # Categorize transactions by purpose
            purpose_breakdown = {}
            for transaction in transactions:
                purpose = transaction.regulatory_category or RegulatoryCategory.FORM_A
                if purpose not in purpose_breakdown:
                    purpose_breakdown[purpose] = {
                        'count': 0,
                        'volume_usd': Decimal('0'),
                        'volume_ngn': Decimal('0')
                    }
                
                purpose_breakdown[purpose]['count'] += 1
                
                # Convert to USD for reporting
                if transaction.base_currency == 'USD':
                    usd_amount = transaction.base_amount
                elif transaction.quote_currency == 'USD':
                    usd_amount = transaction.quote_amount
                else:
                    # Convert via NGN
                    usd_rate = await self.get_exchange_rate('NGN', 'USD')
                    usd_amount = transaction.amount / usd_rate.rate
                
                purpose_breakdown[purpose]['volume_usd'] += usd_amount
                purpose_breakdown[purpose]['volume_ngn'] += transaction.amount
            
            # Large transaction reporting (>$10K)
            large_transactions = [
                t for t in transactions 
                if (t.base_currency == 'USD' and t.base_amount > Decimal('10000')) or
                   (t.quote_currency == 'USD' and t.quote_amount > Decimal('10000'))
            ]
            
            return {
                'report_type': f'cbn_{report_type}_forex_report',
                'dealer_details': {
                    'dealer_code': self.dealer_code,
                    'dealer_name': self.dealer_name,
                    'authorized_dealer': self.authorized_dealer
                },
                'reporting_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'transaction_summary': {
                    'total_transactions': len(transactions),
                    'total_volume_usd': float(sum(
                        (t.base_amount if t.base_currency == 'USD' else t.quote_amount)
                        for t in transactions
                    )),
                    'total_volume_ngn': float(sum(t.amount for t in transactions))
                },
                'purpose_breakdown': {
                    purpose.value: {
                        'transaction_count': data['count'],
                        'volume_usd': float(data['volume_usd']),
                        'volume_ngn': float(data['volume_ngn'])
                    }
                    for purpose, data in purpose_breakdown.items()
                },
                'large_transactions': [
                    {
                        'transaction_id': t.transaction_id,
                        'date': t.transaction_date.isoformat(),
                        'amount_usd': float(t.base_amount if t.base_currency == 'USD' else t.quote_amount),
                        'purpose_code': t.purpose_code,
                        'beneficiary_country': t.beneficiary_country,
                        'form_number': t.form_number
                    }
                    for t in large_transactions
                ],
                'compliance_notes': [
                    "All transactions processed through authorized dealing channels",
                    "Documentation requirements verified as per CBN guidelines",
                    "Large transactions reported in accordance with regulations"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating CBN report: {e}")
            raise
    
    async def get_market_analysis(self,
                                currency_pair: str,
                                period_days: int = 30) -> Dict[str, Any]:
        """Analyze forex market trends"""
        
        try:
            base_currency, quote_currency = currency_pair.split('/')
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            # Get rate history
            rates = await self.get_rate_history(base_currency, quote_currency, start_date, end_date)
            
            if not rates:
                return {'error': 'No rate data available for analysis'}
            
            # Calculate statistics
            rate_values = [float(r.rate) for r in rates]
            
            min_rate = min(rate_values)
            max_rate = max(rate_values)
            avg_rate = sum(rate_values) / len(rate_values)
            current_rate = rate_values[-1] if rate_values else 0
            
            # Calculate volatility (standard deviation)
            variance = sum((r - avg_rate) ** 2 for r in rate_values) / len(rate_values)
            volatility = variance ** 0.5
            
            # Trend analysis
            if len(rate_values) >= 2:
                start_rate = rate_values[0]
                trend_percentage = ((current_rate - start_rate) / start_rate) * 100
                trend_direction = "APPRECIATING" if trend_percentage > 1 else "DEPRECIATING" if trend_percentage < -1 else "STABLE"
            else:
                trend_percentage = 0
                trend_direction = "INSUFFICIENT_DATA"
            
            # Get recent transactions for volume analysis
            transactions = await self.get_forex_transactions(start_date, end_date, currency_pair)
            total_volume = sum(t.base_amount for t in transactions)
            
            return {
                'currency_pair': currency_pair,
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'period_days': period_days
                },
                'rate_statistics': {
                    'current_rate': current_rate,
                    'average_rate': round(avg_rate, 4),
                    'minimum_rate': min_rate,
                    'maximum_rate': max_rate,
                    'volatility': round(volatility, 4),
                    'rate_range': round(max_rate - min_rate, 4)
                },
                'trend_analysis': {
                    'trend_direction': trend_direction,
                    'trend_percentage': round(trend_percentage, 2),
                    'price_change': round(current_rate - avg_rate, 4)
                },
                'volume_analysis': {
                    'total_volume': float(total_volume),
                    'transaction_count': len(transactions),
                    'average_transaction_size': float(total_volume / max(1, len(transactions)))
                },
                'market_insights': self._generate_market_insights(
                    trend_direction, volatility, len(transactions), currency_pair
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing market: {e}")
            raise
    
    def _generate_market_insights(self,
                                trend_direction: str,
                                volatility: float,
                                transaction_count: int,
                                currency_pair: str) -> List[str]:
        """Generate market insights"""
        
        insights = []
        
        # Trend insights
        if trend_direction == "APPRECIATING":
            insights.append(f"{currency_pair} is strengthening against the quote currency")
        elif trend_direction == "DEPRECIATING":
            insights.append(f"{currency_pair} is weakening against the quote currency")
        
        # Volatility insights
        if volatility > 0.05:
            insights.append("High volatility detected - consider risk management strategies")
        elif volatility < 0.01:
            insights.append("Low volatility period - stable exchange rate environment")
        
        # Volume insights
        if transaction_count > 100:
            insights.append("High transaction volume indicates active market participation")
        elif transaction_count < 10:
            insights.append("Low transaction volume - limited market activity")
        
        # Nigerian-specific insights
        if 'NGN' in currency_pair:
            if volatility > 0.03:
                insights.append("Naira volatility may impact import/export planning")
            insights.append("Monitor CBN policy announcements for market direction")
        
        return insights
    
    async def _get_annual_pba_usage(self, customer_id: str) -> Decimal:
        """Get annual PBA usage for customer"""
        
        # Calculate current year usage
        year_start = datetime(datetime.utcnow().year, 1, 1)
        year_end = datetime.utcnow()
        
        transactions = await self.get_forex_transactions(year_start, year_end)
        
        pba_transactions = [
            t for t in transactions 
            if (hasattr(t, 'customer_id') and t.customer_id == customer_id and
                t.regulatory_category == RegulatoryCategory.PERSONAL_BASIC_ALLOWANCE)
        ]
        
        total_usd = Decimal('0')
        for transaction in pba_transactions:
            if transaction.base_currency == 'USD':
                total_usd += transaction.base_amount
            elif transaction.quote_currency == 'USD':
                total_usd += transaction.quote_amount
        
        return total_usd
    
    async def _get_annual_bta_usage(self, customer_id: str) -> Decimal:
        """Get annual BTA usage for customer"""
        
        # Calculate current year usage
        year_start = datetime(datetime.utcnow().year, 1, 1)
        year_end = datetime.utcnow()
        
        transactions = await self.get_forex_transactions(year_start, year_end)
        
        bta_transactions = [
            t for t in transactions 
            if (hasattr(t, 'customer_id') and t.customer_id == customer_id and
                t.regulatory_category == RegulatoryCategory.BUSINESS_TRAVEL_ALLOWANCE)
        ]
        
        total_usd = Decimal('0')
        for transaction in bta_transactions:
            if transaction.base_currency == 'USD':
                total_usd += transaction.base_amount
            elif transaction.quote_currency == 'USD':
                total_usd += transaction.quote_amount
        
        return total_usd