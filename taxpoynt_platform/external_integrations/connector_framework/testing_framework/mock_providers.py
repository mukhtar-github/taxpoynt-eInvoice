"""
Mock Financial Service Providers
===============================

Mock implementations for testing financial system connectors.
Provides realistic test data and behavior simulation.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import random
import json

from ..base_banking_connector import BaseBankingConnector, BankingTransaction, BankAccountInfo, AccountType, BankingChannel
from ..base_payment_connector import BasePaymentConnector, PaymentTransaction, PaymentStatus, PaymentChannel, PaymentType
from ..base_forex_connector import BaseForexConnector, ForexTransaction, CurrencyRate, ForexMarket, ForexTransactionType
from ..classification_engine.classification_models import TransactionClassificationResult, ClassificationMetadata

logger = logging.getLogger(__name__)

@dataclass
class MockConfig:
    """Configuration for mock providers"""
    
    # Response timing
    min_response_time_ms: int = 50
    max_response_time_ms: int = 500
    
    # Error simulation
    error_rate: float = 0.02  # 2% error rate
    timeout_rate: float = 0.01  # 1% timeout rate
    
    # Data generation
    transaction_count_range: tuple = (10, 1000)
    amount_range: tuple = (100, 1000000)
    
    # Nigerian-specific
    nigerian_names: List[str] = None
    nigerian_banks: List[str] = None
    business_keywords: List[str] = None
    
    def __post_init__(self):
        if self.nigerian_names is None:
            self.nigerian_names = [
                "Adebayo Johnson", "Fatima Abdullahi", "Chinedu Okafor", 
                "Aisha Musa", "Emeka Nwosu", "Kemi Adeyemi", "Ibrahim Hassan",
                "Blessing Okoli", "Yusuf Garba", "Funmi Ogundimu"
            ]
        
        if self.nigerian_banks is None:
            self.nigerian_banks = [
                "GTBank", "Access Bank", "Zenith Bank", "First Bank", "UBA",
                "Fidelity Bank", "Sterling Bank", "FCMB", "Union Bank", "Wema Bank"
            ]
        
        if self.business_keywords is None:
            self.business_keywords = [
                "payment for goods", "invoice settlement", "contract payment",
                "professional service", "consultation fee", "sales revenue",
                "business transaction", "service delivery", "supply payment"
            ]

class MockBankingProvider(BaseBankingConnector):
    """Mock banking provider for testing"""
    
    def __init__(self, config: Dict[str, Any], mock_config: MockConfig = None):
        """Initialize mock banking provider"""
        
        super().__init__(config)
        self.mock_config = mock_config or MockConfig()
        self.logger = logging.getLogger(f"{__name__}.MockBankingProvider")
        
        # Mock data storage
        self.mock_accounts: Dict[str, BankAccountInfo] = {}
        self.mock_transactions: Dict[str, List[BankingTransaction]] = {}
        
        # Generate default test accounts
        self._generate_test_accounts()
        
        self.logger.info("Mock banking provider initialized")
    
    async def get_account_info(self, account_number: str) -> BankAccountInfo:
        """Get mock account information"""
        
        await self._simulate_api_delay()
        await self._simulate_errors()
        
        if account_number not in self.mock_accounts:
            # Generate new test account
            self.mock_accounts[account_number] = self._generate_account_info(account_number)
        
        return self.mock_accounts[account_number]
    
    async def get_transactions(self,
                             account_number: str,
                             start_date: datetime,
                             end_date: Optional[datetime] = None,
                             limit: int = 100) -> List[BankingTransaction]:
        """Get mock transactions"""
        
        await self._simulate_api_delay()
        await self._simulate_errors()
        
        if end_date is None:
            end_date = datetime.utcnow()
        
        # Generate transactions if not exists
        if account_number not in self.mock_transactions:
            self.mock_transactions[account_number] = self._generate_transactions(
                account_number, start_date, end_date
            )
        
        # Filter by date range
        filtered_transactions = [
            t for t in self.mock_transactions[account_number]
            if start_date <= t.transaction_date <= end_date
        ]
        
        return filtered_transactions[:limit]
    
    async def validate_account(self, account_number: str) -> Dict[str, Any]:
        """Validate mock account"""
        
        await self._simulate_api_delay()
        
        # Simple validation logic
        is_valid = len(account_number) == 10 and account_number.isdigit()
        
        if is_valid:
            account_info = await self.get_account_info(account_number)
            return {
                'valid': True,
                'account_name': account_info.account_name,
                'account_type': account_info.account_type,
                'bank_name': 'Mock Bank'
            }
        else:
            return {
                'valid': False,
                'error': 'Invalid account number format'
            }
    
    async def get_account_statement(self,
                                  account_number: str,
                                  start_date: datetime,
                                  end_date: datetime,
                                  format_type: str = "pdf") -> Dict[str, Any]:
        """Generate mock account statement"""
        
        await self._simulate_api_delay()
        
        transactions = await self.get_transactions(account_number, start_date, end_date)
        account_info = await self.get_account_info(account_number)
        
        return {
            'statement_id': f"stmt_{account_number}_{int(datetime.utcnow().timestamp())}",
            'account_number': account_number,
            'account_name': account_info.account_name,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'transaction_count': len(transactions),
            'opening_balance': float(account_info.current_balance),
            'closing_balance': float(account_info.current_balance),
            'format': format_type,
            'download_url': f"https://mock-bank.com/statements/{account_number}.{format_type}"
        }
    
    def _generate_test_accounts(self):
        """Generate default test accounts"""
        
        test_accounts = [
            "1234567890", "2345678901", "3456789012", "4567890123", "5678901234"
        ]
        
        for account_number in test_accounts:
            self.mock_accounts[account_number] = self._generate_account_info(account_number)
    
    def _generate_account_info(self, account_number: str) -> BankAccountInfo:
        """Generate mock account information"""
        
        names = self.mock_config.nigerian_names
        account_types = list(AccountType)
        
        return BankAccountInfo(
            account_number=account_number,
            account_name=random.choice(names),
            account_type=random.choice(account_types),
            currency="NGN",
            current_balance=Decimal(random.randint(10000, 5000000)),
            available_balance=Decimal(random.randint(5000, 4000000)),
            institution_name="Mock Bank Nigeria",
            branch_code="001",
            bvn=f"{random.randint(10000000000, 99999999999)}",
            daily_withdrawal_limit=Decimal("200000"),
            daily_transfer_limit=Decimal("5000000"),
            is_active=True,
            is_frozen=False
        )
    
    def _generate_transactions(self,
                             account_number: str,
                             start_date: datetime,
                             end_date: datetime) -> List[BankingTransaction]:
        """Generate mock transactions"""
        
        transactions = []
        transaction_count = random.randint(*self.mock_config.transaction_count_range)
        
        for i in range(transaction_count):
            # Random date within range
            time_diff = end_date - start_date
            random_days = random.randint(0, time_diff.days)
            transaction_date = start_date + timedelta(days=random_days)
            
            # Random transaction details
            amount = Decimal(random.randint(*self.mock_config.amount_range))
            transaction_type = random.choice(list(TransactionType))
            channel = random.choice(list(BankingChannel))
            
            # Generate business-like narration
            if random.random() > 0.5:  # 50% business transactions
                narration = f"{random.choice(self.mock_config.business_keywords)} - {random.choice(self.mock_config.nigerian_names)}"
                is_business = True
                confidence = random.uniform(0.7, 0.95)
            else:
                personal_keywords = ["salary payment", "family support", "personal transfer", "allowance"]
                narration = f"{random.choice(personal_keywords)} - {random.choice(self.mock_config.nigerian_names)}"
                is_business = False
                confidence = random.uniform(0.6, 0.9)
            
            transaction = BankingTransaction(
                transaction_id=f"TXN{i:06d}",
                transaction_type=transaction_type,
                amount=amount,
                currency="NGN",
                narration=narration,
                transaction_date=transaction_date,
                account_number=account_number,
                counterparty_name=random.choice(self.mock_config.nigerian_names),
                counterparty_bank=random.choice(self.mock_config.nigerian_banks),
                channel=channel,
                reference=f"REF{random.randint(100000, 999999)}",
                is_business_income=is_business,
                confidence_score=confidence,
                stamp_duty_applied=amount >= Decimal("1000"),
                cot_applied=amount >= Decimal("10000")
            )
            
            transactions.append(transaction)
        
        return sorted(transactions, key=lambda x: x.transaction_date)
    
    async def _simulate_api_delay(self):
        """Simulate API response time"""
        delay_ms = random.randint(
            self.mock_config.min_response_time_ms,
            self.mock_config.max_response_time_ms
        )
        await asyncio.sleep(delay_ms / 1000)
    
    async def _simulate_errors(self):
        """Simulate API errors"""
        if random.random() < self.mock_config.error_rate:
            error_types = [
                "Connection timeout",
                "Invalid credentials", 
                "Rate limit exceeded",
                "Service unavailable"
            ]
            raise Exception(f"Mock API Error: {random.choice(error_types)}")

class MockPaymentProvider(BasePaymentConnector):
    """Mock payment provider for testing"""
    
    def __init__(self, config: Dict[str, Any], mock_config: MockConfig = None):
        """Initialize mock payment provider"""
        
        super().__init__(config)
        self.mock_config = mock_config or MockConfig()
        self.logger = logging.getLogger(f"{__name__}.MockPaymentProvider")
        
        # Mock data storage
        self.mock_payments: List[PaymentTransaction] = []
        self.payment_counter = 0
        
        self.logger.info("Mock payment provider initialized")
    
    async def initiate_payment(self,
                             amount: Decimal,
                             customer_email: str,
                             reference: str,
                             callback_url: Optional[str] = None,
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Initiate mock payment"""
        
        await self._simulate_api_delay()
        
        self.payment_counter += 1
        payment_id = f"pay_{self.payment_counter:06d}"
        
        # Simulate payment creation
        payment_url = f"https://mock-payment.com/pay/{payment_id}"
        
        return {
            'payment_id': payment_id,
            'reference': reference,
            'amount': float(amount),
            'currency': 'NGN',
            'customer_email': customer_email,
            'payment_url': payment_url,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat()
        }
    
    async def verify_payment(self, payment_reference: str) -> PaymentTransaction:
        """Verify mock payment"""
        
        await self._simulate_api_delay()
        
        # Find existing payment or create new one
        existing_payment = next(
            (p for p in self.mock_payments if p.reference == payment_reference),
            None
        )
        
        if existing_payment:
            return existing_payment
        
        # Create new payment transaction
        payment = self._generate_payment_transaction(payment_reference)
        self.mock_payments.append(payment)
        
        return payment
    
    async def get_payments(self,
                          start_date: datetime,
                          end_date: Optional[datetime] = None,
                          status: Optional[PaymentStatus] = None,
                          limit: int = 100) -> List[PaymentTransaction]:
        """Get mock payments"""
        
        await self._simulate_api_delay()
        
        if end_date is None:
            end_date = datetime.utcnow()
        
        # Generate payments if none exist
        if not self.mock_payments:
            self._generate_test_payments(start_date, end_date)
        
        # Filter payments
        filtered_payments = [
            p for p in self.mock_payments
            if start_date <= p.transaction_date <= end_date
        ]
        
        if status:
            filtered_payments = [p for p in filtered_payments if p.payment_status == status]
        
        return filtered_payments[:limit]
    
    async def process_webhook(self,
                            webhook_data: Dict[str, Any],
                            signature: str) -> Dict[str, Any]:
        """Process mock webhook"""
        
        await self._simulate_api_delay()
        
        # Simple webhook validation
        expected_signature = f"mock_signature_{hash(json.dumps(webhook_data, sort_keys=True))}"
        
        if signature != expected_signature:
            return {
                'status': 'error',
                'message': 'Invalid webhook signature'
            }
        
        # Process webhook event
        event_type = webhook_data.get('event', 'charge.success')
        
        return {
            'status': 'success',
            'event_type': event_type,
            'processed_at': datetime.utcnow().isoformat()
        }
    
    def _generate_payment_transaction(self, reference: str) -> PaymentTransaction:
        """Generate mock payment transaction"""
        
        # Simulate payment success/failure
        status = PaymentStatus.SUCCESS if random.random() > 0.1 else PaymentStatus.FAILED
        
        amount = Decimal(random.randint(500, 100000))
        channel = random.choice(list(PaymentChannel))
        
        # Generate business classification
        if random.random() > 0.4:  # 60% business payments
            is_business = True
            confidence = random.uniform(0.75, 0.95)
            narration = f"Payment for {random.choice(self.mock_config.business_keywords)}"
        else:
            is_business = False
            confidence = random.uniform(0.6, 0.85)
            narration = "Personal payment"
        
        return PaymentTransaction(
            transaction_id=f"txn_{reference}",
            transaction_type=TransactionType.PAYMENT,
            amount=amount,
            currency="NGN",
            narration=narration,
            transaction_date=datetime.utcnow(),
            payment_status=status,
            payment_channel=channel,
            customer_email=f"customer{random.randint(1,1000)}@example.com",
            customer_phone=f"+234{random.randint(7000000000, 9999999999)}",
            reference=reference,
            gateway_fee=amount * Decimal('0.015'),  # 1.5% fee
            settlement_amount=amount * Decimal('0.985'),  # Net settlement
            is_business_income=is_business,
            confidence_score=confidence
        )
    
    def _generate_test_payments(self, start_date: datetime, end_date: datetime):
        """Generate test payments"""
        
        payment_count = random.randint(50, 500)
        
        for i in range(payment_count):
            # Random date
            time_diff = end_date - start_date
            random_days = random.randint(0, time_diff.days)
            payment_date = start_date + timedelta(days=random_days)
            
            reference = f"test_ref_{i:06d}"
            payment = self._generate_payment_transaction(reference)
            payment.transaction_date = payment_date
            
            self.mock_payments.append(payment)
    
    async def _simulate_api_delay(self):
        """Simulate API response time"""
        delay_ms = random.randint(
            self.mock_config.min_response_time_ms,
            self.mock_config.max_response_time_ms
        )
        await asyncio.sleep(delay_ms / 1000)

class MockForexProvider(BaseForexConnector):
    """Mock forex provider for testing"""
    
    def __init__(self, config: Dict[str, Any], mock_config: MockConfig = None):
        """Initialize mock forex provider"""
        
        super().__init__(config)
        self.mock_config = mock_config or MockConfig()
        self.logger = logging.getLogger(f"{__name__}.MockForexProvider")
        
        # Mock exchange rates
        self.base_rates = {
            'USD/NGN': Decimal('461.50'),
            'EUR/NGN': Decimal('501.75'),
            'GBP/NGN': Decimal('580.25'),
            'JPY/NGN': Decimal('3.45'),
            'CAD/NGN': Decimal('341.80'),
            'AUD/NGN': Decimal('308.90')
        }
        
        self.mock_forex_transactions: List[ForexTransaction] = []
        
        self.logger.info("Mock forex provider initialized")
    
    async def get_exchange_rate(self,
                              base_currency: str,
                              quote_currency: str,
                              market_type: ForexMarket = ForexMarket.INTERBANK) -> CurrencyRate:
        """Get mock exchange rate"""
        
        await self._simulate_api_delay()
        
        currency_pair = f"{base_currency}/{quote_currency}"
        
        # Get base rate or reverse
        if currency_pair in self.base_rates:
            base_rate = self.base_rates[currency_pair]
        elif f"{quote_currency}/{base_currency}" in self.base_rates:
            base_rate = Decimal('1') / self.base_rates[f"{quote_currency}/{base_currency}"]
        else:
            # Generate random rate
            base_rate = Decimal(random.uniform(0.1, 1000))
        
        # Add market volatility
        volatility = random.uniform(-0.02, 0.02)  # ±2%
        current_rate = base_rate * (Decimal('1') + Decimal(str(volatility)))
        
        # Calculate bid/ask spread
        spread = current_rate * Decimal('0.001')  # 0.1% spread
        bid_rate = current_rate - spread / 2
        ask_rate = current_rate + spread / 2
        
        return CurrencyRate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            rate=current_rate,
            bid_rate=bid_rate,
            ask_rate=ask_rate,
            mid_rate=current_rate,
            rate_timestamp=datetime.utcnow(),
            source="mock_provider",
            market_type=market_type
        )
    
    async def get_forex_transactions(self,
                                   start_date: datetime,
                                   end_date: Optional[datetime] = None,
                                   currency_pair: Optional[str] = None,
                                   limit: int = 100) -> List[ForexTransaction]:
        """Get mock forex transactions"""
        
        await self._simulate_api_delay()
        
        if not self.mock_forex_transactions:
            self._generate_test_forex_transactions(start_date, end_date or datetime.utcnow())
        
        # Filter transactions
        filtered = [
            t for t in self.mock_forex_transactions
            if start_date <= t.transaction_date <= (end_date or datetime.utcnow())
        ]
        
        if currency_pair:
            base_curr, quote_curr = currency_pair.split('/')
            filtered = [
                t for t in filtered
                if t.base_currency == base_curr and t.quote_currency == quote_curr
            ]
        
        return filtered[:limit]
    
    async def execute_forex_trade(self,
                                base_currency: str,
                                quote_currency: str,
                                amount: Decimal,
                                trade_type: ForexTransactionType,
                                purpose_code: str,
                                metadata: Optional[Dict[str, Any]] = None) -> ForexTransaction:
        """Execute mock forex trade"""
        
        await self._simulate_api_delay()
        
        # Get current rate
        rate = await self.get_exchange_rate(base_currency, quote_currency)
        
        # Create transaction
        transaction = ForexTransaction(
            transaction_id=f"fx_{int(datetime.utcnow().timestamp())}",
            transaction_type=TransactionType.TRANSFER,
            amount=amount,
            currency=base_currency,
            narration=f"FX {trade_type.value} - {purpose_code}",
            transaction_date=datetime.utcnow(),
            forex_type=trade_type,
            base_currency=base_currency,
            quote_currency=quote_currency,
            exchange_rate=rate.rate,
            base_amount=amount,
            quote_amount=amount * rate.rate,
            market_type=ForexMarket.INTERBANK,
            purpose_code=purpose_code,
            value_date=datetime.utcnow() + timedelta(days=2),
            settlement_date=datetime.utcnow() + timedelta(days=2),
            metadata=metadata or {}
        )
        
        self.mock_forex_transactions.append(transaction)
        return transaction
    
    def _generate_test_forex_transactions(self, start_date: datetime, end_date: datetime):
        """Generate test forex transactions"""
        
        transaction_count = random.randint(20, 200)
        
        for i in range(transaction_count):
            # Random date
            time_diff = end_date - start_date
            random_days = random.randint(0, time_diff.days)
            transaction_date = start_date + timedelta(days=random_days)
            
            # Random currency pair
            base_currency = random.choice(['USD', 'EUR', 'GBP'])
            quote_currency = 'NGN'
            amount = Decimal(random.randint(1000, 50000))
            
            # Generate rate
            currency_pair = f"{base_currency}/{quote_currency}"
            base_rate = self.base_rates.get(currency_pair, Decimal('400'))
            
            transaction = ForexTransaction(
                transaction_id=f"fx_test_{i:06d}",
                transaction_type=TransactionType.TRANSFER,
                amount=amount,
                currency=base_currency,
                narration=f"Foreign exchange - {random.choice(['import', 'export', 'personal', 'business'])}",
                transaction_date=transaction_date,
                forex_type=ForexTransactionType.SPOT_TRADE,
                base_currency=base_currency,
                quote_currency=quote_currency,
                exchange_rate=base_rate,
                base_amount=amount,
                quote_amount=amount * base_rate,
                market_type=ForexMarket.INTERBANK,
                purpose_code=random.choice(['import', 'export', 'tuition', 'medical'])
            )
            
            self.mock_forex_transactions.append(transaction)
    
    async def _simulate_api_delay(self):
        """Simulate API response time"""
        delay_ms = random.randint(
            self.mock_config.min_response_time_ms,
            self.mock_config.max_response_time_ms
        )
        await asyncio.sleep(delay_ms / 1000)

class MockOpenAIClient:
    """Mock OpenAI client for testing classification"""
    
    def __init__(self, mock_config: MockConfig = None):
        self.mock_config = mock_config or MockConfig()
        self.logger = logging.getLogger(f"{__name__}.MockOpenAIClient")
        
        # Mock response templates
        self.business_responses = [
            "Business transaction: Payment for professional services",
            "Commercial activity: Invoice settlement for goods supplied",
            "Business income: Contract payment received"
        ]
        
        self.personal_responses = [
            "Personal transaction: Family support payment",
            "Personal activity: Salary payment received",
            "Personal income: Allowance payment"
        ]
    
    async def chat_completions_create(self, **kwargs) -> Dict[str, Any]:
        """Mock OpenAI chat completion"""
        
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate API delay
        
        messages = kwargs.get('messages', [])
        prompt_content = messages[-1]['content'] if messages else ""
        
        # Analyze prompt for business indicators
        business_indicators = ['payment', 'invoice', 'business', 'service', 'goods', 'contract']
        personal_indicators = ['salary', 'family', 'personal', 'allowance', 'loan']
        
        prompt_lower = prompt_content.lower()
        business_score = sum(1 for word in business_indicators if word in prompt_lower)
        personal_score = sum(1 for word in personal_indicators if word in prompt_lower)
        
        # Determine classification
        if business_score > personal_score:
            is_business = True
            confidence = random.uniform(0.75, 0.95)
            reasoning = random.choice(self.business_responses)
        else:
            is_business = False
            confidence = random.uniform(0.65, 0.90)
            reasoning = random.choice(self.personal_responses)
        
        # Create mock response
        response_content = json.dumps({
            'is_business_income': is_business,
            'confidence': confidence,
            'reasoning': reasoning,
            'tax_category': 'standard_rate' if is_business else 'unknown',
            'vat_applicable': is_business,
            'requires_human_review': confidence < 0.7
        })
        
        return {
            'choices': [{
                'message': {
                    'content': response_content,
                    'role': 'assistant'
                },
                'finish_reason': 'stop'
            }],
            'usage': {
                'prompt_tokens': len(prompt_content.split()),
                'completion_tokens': len(response_content.split()),
                'total_tokens': len(prompt_content.split()) + len(response_content.split())
            },
            'model': 'gpt-4o-mini'
        }

class MockRedisClient:
    """Mock Redis client for testing caching"""
    
    def __init__(self):
        self.data_store: Dict[str, str] = {}
        self.expiry_store: Dict[str, datetime] = {}
        self.logger = logging.getLogger(f"{__name__}.MockRedisClient")
    
    async def get(self, key: str) -> Optional[str]:
        """Mock Redis GET"""
        await asyncio.sleep(0.001)  # Minimal delay
        
        # Check expiry
        if key in self.expiry_store and datetime.utcnow() > self.expiry_store[key]:
            del self.data_store[key]
            del self.expiry_store[key]
            return None
        
        return self.data_store.get(key)
    
    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        """Mock Redis SET"""
        await asyncio.sleep(0.001)
        
        self.data_store[key] = value
        
        if ex:
            self.expiry_store[key] = datetime.utcnow() + timedelta(seconds=ex)
        
        return True
    
    async def setex(self, key: str, time: int, value: str) -> bool:
        """Mock Redis SETEX"""
        return await self.set(key, value, ex=time)
    
    async def delete(self, *keys: str) -> int:
        """Mock Redis DELETE"""
        await asyncio.sleep(0.001)
        
        deleted_count = 0
        for key in keys:
            if key in self.data_store:
                del self.data_store[key]
                deleted_count += 1
            if key in self.expiry_store:
                del self.expiry_store[key]
        
        return deleted_count
    
    async def keys(self, pattern: str) -> List[str]:
        """Mock Redis KEYS"""
        await asyncio.sleep(0.001)
        
        # Simple pattern matching (only supports * wildcard)
        if '*' not in pattern:
            return [pattern] if pattern in self.data_store else []
        
        # Convert pattern to regex-like matching
        pattern_prefix = pattern.replace('*', '')
        matching_keys = [
            key for key in self.data_store.keys()
            if key.startswith(pattern_prefix)
        ]
        
        return matching_keys
    
    async def close(self):
        """Mock Redis close"""
        self.logger.info("Mock Redis client closed")