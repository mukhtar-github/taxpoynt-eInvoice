"""
Base Payment Processor Connector
===============================

Base class for payment processors (Paystack, Flutterwave, Interswitch, etc.)
Handles payment transactions, webhooks, and Nigerian payment regulations.
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

class PaymentStatus(str, Enum):
    """Payment transaction statuses"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REVERSED = "reversed"
    ABANDONED = "abandoned"

class PaymentChannel(str, Enum):
    """Nigerian payment channels"""
    CARD = "card"
    BANK_TRANSFER = "bank_transfer"
    USSD = "ussd"
    QR_CODE = "qr_code"
    MOBILE_MONEY = "mobile_money"
    BANK_BRANCH = "bank_branch"
    POS = "pos"
    VIRTUAL_ACCOUNT = "virtual_account"

class PaymentType(str, Enum):
    """Types of payments"""
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    SUBSCRIPTION = "subscription"
    SPLIT_PAYMENT = "split_payment"
    BULK_PAYMENT = "bulk_payment"

@dataclass
class PaymentTransaction(FinancialTransaction):
    """Payment processor transaction model"""
    
    # Payment-specific fields
    payment_status: PaymentStatus
    payment_channel: PaymentChannel
    payment_type: PaymentType = PaymentType.ONE_TIME
    
    # Customer information
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_id: Optional[str] = None
    
    # Payment details
    gateway_reference: Optional[str] = None
    authorization_code: Optional[str] = None
    card_last_four: Optional[str] = None
    card_type: Optional[str] = None
    bank_code: Optional[str] = None
    
    # Fees and charges
    gateway_fee: Optional[Decimal] = None
    processing_fee: Optional[Decimal] = None
    settlement_amount: Optional[Decimal] = None
    
    # Timeline
    initiated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    
    # Webhook and integration
    webhook_delivered: bool = False
    integration_attempts: int = 0

@dataclass
class CustomerInfo:
    """Payment customer information"""
    
    customer_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    # Business customer details
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    business_registration: Optional[str] = None
    
    # KYC status
    is_verified: bool = False
    kyc_level: Optional[str] = None
    
    # Statistics
    total_transactions: int = 0
    total_volume: Decimal = Decimal('0.0')
    first_transaction_date: Optional[datetime] = None
    last_transaction_date: Optional[datetime] = None

class BasePaymentConnector(BaseFinancialConnector):
    """
    Base connector for payment processors with Nigerian regulatory compliance
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize payment connector"""
        
        super().__init__(config, FinancialSystemType.PAYMENT_PROCESSOR)
        
        # Payment processor configurations
        self.processor_name = config.get('processor_name')
        self.merchant_id = config.get('merchant_id')
        self.webhook_secret = config.get('webhook_secret')
        
        # Nigerian payment regulations
        self.max_single_payment = Decimal(config.get('max_single_payment', '5000000'))  # ₦5M
        self.daily_payment_limit = Decimal(config.get('daily_payment_limit', '20000000'))  # ₦20M
        self.kyc_required_threshold = Decimal(config.get('kyc_required_threshold', '50000'))  # ₦50K
        
        # Fee configurations
        self.standard_fee_rate = Decimal(config.get('standard_fee_rate', '0.015'))  # 1.5%
        self.fee_cap = Decimal(config.get('fee_cap', '2000'))  # ₦2000
        
        self.logger.info(f"Payment connector initialized for {self.processor_name}")
    
    @abstractmethod
    async def initiate_payment(self, 
                             amount: Decimal,
                             customer_email: str,
                             reference: str,
                             callback_url: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiate a payment transaction"""
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_reference: str) -> PaymentTransaction:
        """Verify payment status"""
        pass
    
    @abstractmethod
    async def get_payments(self,
                          start_date: datetime,
                          end_date: Optional[datetime] = None,
                          status: Optional[PaymentStatus] = None,
                          limit: int = 100) -> List[PaymentTransaction]:
        """Get payment transactions"""
        pass
    
    @abstractmethod
    async def process_webhook(self, 
                            webhook_data: Dict[str, Any],
                            signature: str) -> Dict[str, Any]:
        """Process webhook notification"""
        pass
    
    async def get_customer_info(self, customer_identifier: str) -> CustomerInfo:
        """Get customer information (default implementation)"""
        
        # This is a base implementation - specific processors should override
        try:
            # Get recent payments for this customer
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)  # Last year
            
            payments = await self.get_payments(start_date, end_date, limit=1000)
            customer_payments = [
                p for p in payments 
                if p.customer_email == customer_identifier or p.customer_id == customer_identifier
            ]
            
            if not customer_payments:
                raise ValueError(f"Customer not found: {customer_identifier}")
            
            # Aggregate customer data
            total_volume = sum(p.amount for p in customer_payments)
            first_payment = min(customer_payments, key=lambda x: x.transaction_date)
            last_payment = max(customer_payments, key=lambda x: x.transaction_date)
            
            return CustomerInfo(
                customer_id=customer_identifier,
                email=first_payment.customer_email,
                phone=first_payment.customer_phone,
                total_transactions=len(customer_payments),
                total_volume=total_volume,
                first_transaction_date=first_payment.transaction_date,
                last_transaction_date=last_payment.transaction_date
            )
            
        except Exception as e:
            self.logger.error(f"Error getting customer info: {e}")
            raise
    
    async def get_settlement_report(self,
                                  start_date: datetime,
                                  end_date: datetime) -> Dict[str, Any]:
        """Get settlement report for the period"""
        
        try:
            payments = await self.get_payments(start_date, end_date, PaymentStatus.SUCCESS, limit=10000)
            
            # Calculate settlement metrics
            total_gross_volume = sum(p.amount for p in payments)
            total_fees = sum(p.gateway_fee or Decimal('0') for p in payments)
            total_settlement = sum(p.settlement_amount or p.amount for p in payments)
            
            # Channel breakdown
            channel_breakdown = {}
            for payment in payments:
                channel = payment.payment_channel
                if channel not in channel_breakdown:
                    channel_breakdown[channel] = {
                        'count': 0,
                        'volume': Decimal('0'),
                        'fees': Decimal('0')
                    }
                
                channel_breakdown[channel]['count'] += 1
                channel_breakdown[channel]['volume'] += payment.amount
                channel_breakdown[channel]['fees'] += payment.gateway_fee or Decimal('0')
            
            # Success rate analysis
            all_payments = await self.get_payments(start_date, end_date, limit=10000)
            success_rate = len(payments) / max(1, len(all_payments)) * 100
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'settlement_summary': {
                    'total_transactions': len(payments),
                    'gross_volume': float(total_gross_volume),
                    'total_fees': float(total_fees),
                    'net_settlement': float(total_settlement),
                    'average_transaction_size': float(total_gross_volume / max(1, len(payments)))
                },
                'channel_breakdown': {
                    channel.value: {
                        'count': data['count'],
                        'volume': float(data['volume']),
                        'fees': float(data['fees']),
                        'average_size': float(data['volume'] / max(1, data['count']))
                    }
                    for channel, data in channel_breakdown.items()
                },
                'performance_metrics': {
                    'success_rate_percent': round(success_rate, 2),
                    'failed_transactions': len(all_payments) - len(payments),
                    'fee_rate_percent': round(float(total_fees / max(total_gross_volume, Decimal('1'))) * 100, 2)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating settlement report: {e}")
            raise
    
    async def analyze_payment_patterns(self,
                                     period_days: int = 30,
                                     min_confidence: float = 0.7) -> Dict[str, Any]:
        """Analyze payment patterns for business insights"""
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=period_days)
            
            payments = await self.get_payments(start_date, end_date, PaymentStatus.SUCCESS, limit=10000)
            
            # Business vs personal classification
            business_payments = [p for p in payments if p.is_business_income and p.confidence_score >= min_confidence]
            personal_payments = [p for p in payments if p.is_business_income == False and p.confidence_score >= min_confidence]
            
            # Time pattern analysis
            hourly_distribution = {}
            for payment in payments:
                hour = payment.transaction_date.hour
                hourly_distribution[hour] = hourly_distribution.get(hour, 0) + 1
            
            # Day of week analysis
            daily_distribution = {}
            for payment in payments:
                day = payment.transaction_date.strftime('%A')
                daily_distribution[day] = daily_distribution.get(day, 0) + 1
            
            # Amount pattern analysis
            amount_ranges = {
                'micro': [p for p in payments if p.amount < Decimal('1000')],
                'small': [p for p in payments if Decimal('1000') <= p.amount < Decimal('10000')],
                'medium': [p for p in payments if Decimal('10000') <= p.amount < Decimal('100000')],
                'large': [p for p in payments if p.amount >= Decimal('100000')]
            }
            
            return {
                'analysis_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'total_payments': len(payments)
                },
                'business_classification': {
                    'business_payments': len(business_payments),
                    'personal_payments': len(personal_payments),
                    'business_volume': float(sum(p.amount for p in business_payments)),
                    'personal_volume': float(sum(p.amount for p in personal_payments)),
                    'business_percentage': round(len(business_payments) / max(1, len(payments)) * 100, 2)
                },
                'temporal_patterns': {
                    'hourly_distribution': hourly_distribution,
                    'daily_distribution': daily_distribution,
                    'peak_hour': max(hourly_distribution.items(), key=lambda x: x[1])[0] if hourly_distribution else None,
                    'peak_day': max(daily_distribution.items(), key=lambda x: x[1])[0] if daily_distribution else None
                },
                'amount_distribution': {
                    range_name: {
                        'count': len(range_payments),
                        'volume': float(sum(p.amount for p in range_payments)),
                        'percentage': round(len(range_payments) / max(1, len(payments)) * 100, 2)
                    }
                    for range_name, range_payments in amount_ranges.items()
                },
                'insights': self._generate_payment_insights(payments, business_payments)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing payment patterns: {e}")
            raise
    
    def _generate_payment_insights(self,
                                 all_payments: List[PaymentTransaction],
                                 business_payments: List[PaymentTransaction]) -> List[str]:
        """Generate business insights from payment patterns"""
        
        insights = []
        
        if not all_payments:
            return ["Insufficient data for insights generation"]
        
        # Business percentage insight
        business_percentage = len(business_payments) / len(all_payments) * 100
        if business_percentage > 70:
            insights.append("High business transaction ratio suggests B2B or service-oriented business")
        elif business_percentage < 30:
            insights.append("Low business transaction ratio suggests consumer-focused business")
        
        # Volume insights
        total_volume = sum(p.amount for p in all_payments)
        avg_transaction = total_volume / len(all_payments)
        
        if avg_transaction > Decimal('50000'):
            insights.append("High average transaction value indicates enterprise customers")
        elif avg_transaction < Decimal('5000'):
            insights.append("Low average transaction value suggests retail/consumer focus")
        
        # Channel insights
        channel_usage = {}
        for payment in all_payments:
            channel = payment.payment_channel
            channel_usage[channel] = channel_usage.get(channel, 0) + 1
        
        dominant_channel = max(channel_usage.items(), key=lambda x: x[1])[0]
        if dominant_channel == PaymentChannel.CARD:
            insights.append("Card payments dominate - good online presence")
        elif dominant_channel == PaymentChannel.BANK_TRANSFER:
            insights.append("Bank transfers dominate - indicates high-value transactions")
        
        # Success rate insights
        if hasattr(self, '_calculate_success_rate'):
            success_rate = self._calculate_success_rate(all_payments)
            if success_rate > 95:
                insights.append("Excellent payment success rate")
            elif success_rate < 85:
                insights.append("Payment success rate needs improvement")
        
        return insights
    
    async def get_risk_assessment(self,
                                customer_identifier: str,
                                transaction_amount: Decimal) -> Dict[str, Any]:
        """Assess transaction risk for fraud prevention"""
        
        try:
            customer_info = await self.get_customer_info(customer_identifier)
            
            risk_score = 0.0
            risk_factors = []
            
            # New customer risk
            if customer_info.total_transactions < 3:
                risk_score += 0.3
                risk_factors.append("New customer with limited transaction history")
            
            # High amount risk
            if transaction_amount > customer_info.total_volume / max(1, customer_info.total_transactions) * 5:
                risk_score += 0.4
                risk_factors.append("Transaction amount significantly higher than customer average")
            
            # Threshold-based risk
            if transaction_amount > self.kyc_required_threshold:
                risk_score += 0.2
                risk_factors.append("Transaction exceeds KYC threshold")
            
            # Time-based risk (off-hours)
            current_hour = datetime.utcnow().hour
            if current_hour < 6 or current_hour > 22:
                risk_score += 0.1
                risk_factors.append("Off-hours transaction")
            
            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "HIGH"
            elif risk_score >= 0.5:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return {
                'customer_id': customer_identifier,
                'transaction_amount': float(transaction_amount),
                'risk_assessment': {
                    'risk_score': round(risk_score, 2),
                    'risk_level': risk_level,
                    'risk_factors': risk_factors
                },
                'customer_profile': {
                    'total_transactions': customer_info.total_transactions,
                    'total_volume': float(customer_info.total_volume),
                    'is_verified': customer_info.is_verified
                },
                'recommendations': self._get_risk_recommendations(risk_level, risk_factors)
            }
            
        except Exception as e:
            self.logger.error(f"Error assessing transaction risk: {e}")
            raise
    
    def _get_risk_recommendations(self, risk_level: str, risk_factors: List[str]) -> List[str]:
        """Get risk mitigation recommendations"""
        
        recommendations = []
        
        if risk_level == "HIGH":
            recommendations.extend([
                "Require additional identity verification",
                "Consider manual review before processing",
                "Implement step-up authentication"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "Monitor transaction closely",
                "Consider additional verification for future transactions"
            ])
        
        if "New customer" in str(risk_factors):
            recommendations.append("Consider lower initial transaction limits")
        
        if "exceeds KYC threshold" in str(risk_factors):
            recommendations.append("Ensure KYC documentation is complete")
        
        return recommendations