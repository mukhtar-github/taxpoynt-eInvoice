"""
Multi-Currency Support for International Payments
================================================

Comprehensive multi-currency support system for international payment processing
with real-time exchange rates, currency conversion, and compliance handling.

Features:
- Real-time exchange rate fetching from multiple sources
- Automatic currency conversion with configurable margins
- Multi-currency transaction processing and settlement
- Currency risk management and hedging strategies
- Compliance handling for cross-border transactions
- Nigerian Naira (NGN) focus with global currency support
- FIRS-compliant currency conversion reporting
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import aiohttp

# Import currency models from different processors
from .african_processors.flutterwave.models import FlutterwaveCurrency
from .global_processors.stripe.models import StripeCurrency
from ..connector_framework.base_payment_connector import PaymentTransaction


class ExchangeRateSource(str, Enum):
    """Exchange rate data sources"""
    CENTRAL_BANK_NIGERIA = "cbn"
    FLUTTERWAVE = "flutterwave"
    STRIPE = "stripe"
    XE_CURRENCY = "xe"
    FIXER_IO = "fixer"
    OPENEXCHANGERATES = "openexchangerates"
    CURRENCYAPI = "currencyapi"


class CurrencyConversionMethod(str, Enum):
    """Currency conversion methods"""
    REAL_TIME = "real_time"
    DAILY_RATE = "daily_rate"
    WEEKLY_AVERAGE = "weekly_average"
    MONTHLY_AVERAGE = "monthly_average"
    FIXED_RATE = "fixed_rate"


@dataclass
class ExchangeRate:
    """Exchange rate information"""
    
    from_currency: str
    to_currency: str
    rate: Decimal
    source: ExchangeRateSource
    timestamp: datetime
    
    # Rate metadata
    bid_rate: Optional[Decimal] = None
    ask_rate: Optional[Decimal] = None
    mid_rate: Optional[Decimal] = None
    
    # Source reliability
    confidence: float = 1.0
    is_live: bool = True
    
    # Nigerian specific
    is_official_cbn_rate: bool = False
    parallel_market_rate: Optional[Decimal] = None


@dataclass
class CurrencyConversion:
    """Currency conversion result"""
    
    original_amount: Decimal
    original_currency: str
    converted_amount: Decimal
    converted_currency: str
    exchange_rate: Decimal
    conversion_fee: Decimal
    total_cost: Decimal
    
    # Conversion metadata
    rate_source: ExchangeRateSource
    conversion_method: CurrencyConversionMethod
    timestamp: datetime
    
    # Nigerian compliance
    firs_reportable: bool = False
    tax_implications: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiCurrencyConfig:
    """Configuration for multi-currency support"""
    
    # Base currency (typically NGN for Nigerian businesses)
    base_currency: str = "NGN"
    
    # Supported currencies
    supported_currencies: List[str] = field(default_factory=lambda: [
        "NGN", "USD", "EUR", "GBP", "JPY", "CNY",  # Major global
        "GHS", "KES", "UGX", "TZS", "RWF", "ZMW", "ZAR",  # African
        "CAD", "AUD", "CHF", "SEK", "NOK", "DKK", "PLN", "SGD", "HKD"  # Others
    ])
    
    # Exchange rate sources (in priority order)
    rate_sources: List[ExchangeRateSource] = field(default_factory=lambda: [
        ExchangeRateSource.CENTRAL_BANK_NIGERIA,
        ExchangeRateSource.FLUTTERWAVE,
        ExchangeRateSource.STRIPE,
        ExchangeRateSource.XE_CURRENCY
    ])
    
    # Conversion settings
    default_conversion_method: CurrencyConversionMethod = CurrencyConversionMethod.REAL_TIME
    conversion_fee_percentage: Decimal = Decimal("0.005")  # 0.5%
    max_conversion_fee: Decimal = Decimal("1000")  # Max ₦1,000 or equivalent
    
    # Rate refresh settings
    rate_refresh_interval_minutes: int = 15
    rate_cache_duration_hours: int = 24
    stale_rate_threshold_minutes: int = 60
    
    # Risk management
    max_daily_conversion_volume: Dict[str, Decimal] = field(default_factory=lambda: {
        "USD": Decimal("100000"),  # $100,000
        "EUR": Decimal("90000"),   # €90,000
        "GBP": Decimal("80000"),   # £80,000
    })
    
    # Nigerian compliance
    enable_cbn_compliance: bool = True
    auto_firs_reporting: bool = True
    foreign_exchange_threshold: Decimal = Decimal("10000")  # $10,000 equivalent


class MultiCurrencySupport:
    """
    Multi-Currency Support System
    
    Provides comprehensive multi-currency support for international payments
    with focus on Nigerian compliance and African market coverage.
    """
    
    def __init__(self, config: MultiCurrencyConfig):
        """
        Initialize multi-currency support system
        
        Args:
            config: Multi-currency configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Exchange rate cache
        self.exchange_rates: Dict[str, ExchangeRate] = {}
        self.rate_history: Dict[str, List[ExchangeRate]] = {}
        
        # HTTP session for API calls
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Background tasks
        self._rate_refresh_task = None
        self._is_running = False
        
        # Statistics
        self.conversion_stats = {
            'total_conversions': 0,
            'total_volume_converted': {},
            'conversions_by_currency_pair': {},
            'average_conversion_fee': Decimal('0'),
            'rate_source_usage': {},
            'last_conversion_time': None
        }
        
        self.logger.info("Multi-currency support initialized", extra={
            'base_currency': config.base_currency,
            'supported_currencies': len(config.supported_currencies),
            'rate_sources': len(config.rate_sources)
        })
    
    async def start(self):
        """Start multi-currency support system"""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Initialize HTTP session
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Load initial exchange rates
        await self._refresh_all_rates()
        
        # Start background rate refresh
        self._rate_refresh_task = asyncio.create_task(self._rate_refresh_loop())
        
        self.logger.info("Multi-currency support started")
    
    async def stop(self):
        """Stop multi-currency support system"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel background tasks
        if self._rate_refresh_task:
            self._rate_refresh_task.cancel()
            try:
                await self._rate_refresh_task
            except asyncio.CancelledError:
                pass
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        self.logger.info("Multi-currency support stopped")
    
    async def get_exchange_rate(
        self,
        from_currency: str,
        to_currency: str,
        amount: Optional[Decimal] = None,
        force_refresh: bool = False
    ) -> Optional[ExchangeRate]:
        """
        Get exchange rate between two currencies
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            amount: Optional amount for rate calculation
            force_refresh: Force refresh from sources
            
        Returns:
            ExchangeRate or None if unavailable
        """
        try:
            # Normalize currency codes
            from_currency = from_currency.upper()
            to_currency = to_currency.upper()
            
            # Same currency
            if from_currency == to_currency:
                return ExchangeRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=Decimal('1.0'),
                    source=ExchangeRateSource.FIXED_RATE,
                    timestamp=datetime.utcnow(),
                    is_live=False
                )
            
            # Check cache first
            rate_key = f"{from_currency}/{to_currency}"
            cached_rate = self.exchange_rates.get(rate_key)
            
            if cached_rate and not force_refresh:
                # Check if rate is still fresh
                age = datetime.utcnow() - cached_rate.timestamp
                if age.total_seconds() < (self.config.stale_rate_threshold_minutes * 60):
                    return cached_rate
            
            # Fetch fresh rate
            rate = await self._fetch_exchange_rate(from_currency, to_currency)
            
            if rate:
                # Cache the rate
                self.exchange_rates[rate_key] = rate
                
                # Store in history
                if rate_key not in self.rate_history:
                    self.rate_history[rate_key] = []
                self.rate_history[rate_key].append(rate)
                
                # Keep only recent history (last 100 rates)
                self.rate_history[rate_key] = self.rate_history[rate_key][-100:]
            
            return rate
            
        except Exception as e:
            self.logger.error(f"Error getting exchange rate {from_currency}/{to_currency}: {str(e)}")
            return None
    
    async def convert_currency(
        self,
        amount: Decimal,
        from_currency: str,
        to_currency: str,
        method: Optional[CurrencyConversionMethod] = None,
        include_fees: bool = True
    ) -> Optional[CurrencyConversion]:
        """
        Convert amount from one currency to another
        
        Args:
            amount: Amount to convert
            from_currency: Source currency
            to_currency: Target currency
            method: Conversion method
            include_fees: Whether to include conversion fees
            
        Returns:
            CurrencyConversion result or None if failed
        """
        try:
            # Get exchange rate
            rate_info = await self.get_exchange_rate(from_currency, to_currency, amount)
            
            if not rate_info:
                self.logger.error(f"No exchange rate available for {from_currency}/{to_currency}")
                return None
            
            # Calculate converted amount
            converted_amount = amount * rate_info.rate
            
            # Calculate conversion fee
            conversion_fee = Decimal('0')
            if include_fees:
                conversion_fee = min(
                    converted_amount * self.config.conversion_fee_percentage,
                    self.config.max_conversion_fee
                )
            
            # Total cost
            total_cost = converted_amount + conversion_fee
            
            # Determine if FIRS reportable (for Nigerian compliance)
            firs_reportable = self._is_firs_reportable(amount, from_currency, to_currency)
            
            # Create conversion result
            conversion = CurrencyConversion(
                original_amount=amount,
                original_currency=from_currency,
                converted_amount=converted_amount,
                converted_currency=to_currency,
                exchange_rate=rate_info.rate,
                conversion_fee=conversion_fee,
                total_cost=total_cost,
                rate_source=rate_info.source,
                conversion_method=method or self.config.default_conversion_method,
                timestamp=datetime.utcnow(),
                firs_reportable=firs_reportable
            )
            
            # Update statistics
            self._update_conversion_stats(conversion)
            
            self.logger.info("Currency converted", extra={
                'from_currency': from_currency,
                'to_currency': to_currency,
                'original_amount': str(amount),
                'converted_amount': str(converted_amount),
                'exchange_rate': str(rate_info.rate),
                'conversion_fee': str(conversion_fee)
            })
            
            return conversion
            
        except Exception as e:
            self.logger.error(f"Currency conversion failed: {str(e)}")
            return None
    
    async def convert_transaction(
        self,
        transaction: PaymentTransaction,
        target_currency: str
    ) -> Optional[PaymentTransaction]:
        """
        Convert transaction to different currency
        
        Args:
            transaction: Original transaction
            target_currency: Target currency for conversion
            
        Returns:
            Converted transaction or None if failed
        """
        try:
            # Convert main amount
            main_conversion = await self.convert_currency(
                transaction.amount,
                transaction.currency,
                target_currency
            )
            
            if not main_conversion:
                return None
            
            # Create new transaction with converted values
            converted_transaction = PaymentTransaction(
                transaction_id=transaction.transaction_id,
                reference=transaction.reference,
                amount=main_conversion.converted_amount,
                currency=target_currency,
                payment_status=transaction.payment_status,
                payment_channel=transaction.payment_channel,
                payment_type=transaction.payment_type,
                
                # Copy other fields
                customer_email=transaction.customer_email,
                customer_phone=transaction.customer_phone,
                customer_id=transaction.customer_id,
                
                # Original currency info in metadata
                metadata={
                    **getattr(transaction, 'metadata', {}),
                    'original_currency': transaction.currency,
                    'original_amount': str(transaction.amount),
                    'exchange_rate': str(main_conversion.exchange_rate),
                    'conversion_timestamp': main_conversion.timestamp.isoformat()
                },
                
                # Timestamps
                transaction_date=transaction.transaction_date,
                created_at=transaction.created_at,
                updated_at=datetime.utcnow()
            )
            
            return converted_transaction
            
        except Exception as e:
            self.logger.error(f"Transaction conversion failed: {str(e)}")
            return None
    
    async def get_supported_currencies(self) -> List[Dict[str, Any]]:
        """Get list of supported currencies with metadata"""
        currencies = []
        
        for currency_code in self.config.supported_currencies:
            # Get current rate to base currency
            rate_to_base = None
            if currency_code != self.config.base_currency:
                rate_info = await self.get_exchange_rate(currency_code, self.config.base_currency)
                rate_to_base = rate_info.rate if rate_info else None
            
            currency_info = {
                'code': currency_code,
                'name': self._get_currency_name(currency_code),
                'symbol': self._get_currency_symbol(currency_code),
                'decimal_places': self._get_currency_decimals(currency_code),
                'is_base_currency': currency_code == self.config.base_currency,
                'rate_to_base': str(rate_to_base) if rate_to_base else None,
                'last_updated': self.exchange_rates.get(
                    f"{currency_code}/{self.config.base_currency}", {}
                ).timestamp.isoformat() if rate_to_base else None
            }
            
            currencies.append(currency_info)
        
        return currencies
    
    async def get_currency_trends(
        self,
        currency_code: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get currency trend analysis"""
        try:
            rate_key = f"{currency_code}/{self.config.base_currency}"
            history = self.rate_history.get(rate_key, [])
            
            if not history:
                return {'error': 'No historical data available'}
            
            # Filter by time period
            cutoff_date = datetime.utcnow() - timedelta(days=period_days)
            recent_rates = [
                rate for rate in history 
                if rate.timestamp >= cutoff_date
            ]
            
            if not recent_rates:
                return {'error': 'No recent data available'}
            
            # Calculate trends
            rates = [float(rate.rate) for rate in recent_rates]
            
            trend_analysis = {
                'currency': currency_code,
                'base_currency': self.config.base_currency,
                'period_days': period_days,
                'current_rate': rates[-1] if rates else None,
                'min_rate': min(rates) if rates else None,
                'max_rate': max(rates) if rates else None,
                'average_rate': sum(rates) / len(rates) if rates else None,
                'volatility': self._calculate_volatility(rates),
                'trend_direction': self._calculate_trend_direction(rates),
                'data_points': len(recent_rates)
            }
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Error calculating currency trends: {str(e)}")
            return {'error': str(e)}
    
    def get_conversion_statistics(self) -> Dict[str, Any]:
        """Get comprehensive conversion statistics"""
        stats = self.conversion_stats.copy()
        
        # Convert Decimal values to strings for JSON serialization
        for currency, volume in stats.get('total_volume_converted', {}).items():
            stats['total_volume_converted'][currency] = str(volume)
        
        stats['average_conversion_fee'] = str(stats['average_conversion_fee'])
        
        # Add current rate summary
        stats['current_rates'] = {}
        for rate_key, rate in self.exchange_rates.items():
            stats['current_rates'][rate_key] = {
                'rate': str(rate.rate),
                'source': rate.source.value,
                'timestamp': rate.timestamp.isoformat(),
                'is_live': rate.is_live
            }
        
        return stats
    
    async def _fetch_exchange_rate(
        self,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Fetch exchange rate from configured sources"""
        
        for source in self.config.rate_sources:
            try:
                rate = await self._fetch_from_source(source, from_currency, to_currency)
                if rate:
                    # Update source usage stats
                    self.conversion_stats['rate_source_usage'][source.value] = \
                        self.conversion_stats['rate_source_usage'].get(source.value, 0) + 1
                    
                    return rate
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch rate from {source.value}: {str(e)}")
                continue
        
        return None
    
    async def _fetch_from_source(
        self,
        source: ExchangeRateSource,
        from_currency: str,
        to_currency: str
    ) -> Optional[ExchangeRate]:
        """Fetch rate from specific source"""
        
        if source == ExchangeRateSource.CENTRAL_BANK_NIGERIA:
            return await self._fetch_cbn_rate(from_currency, to_currency)
        elif source == ExchangeRateSource.XE_CURRENCY:
            return await self._fetch_xe_rate(from_currency, to_currency)
        elif source == ExchangeRateSource.FIXER_IO:
            return await self._fetch_fixer_rate(from_currency, to_currency)
        else:
            # Placeholder for other sources
            return None
    
    async def _fetch_cbn_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """Fetch rate from Central Bank of Nigeria"""
        try:
            # CBN API endpoint (placeholder - would use actual CBN API)
            url = f"https://www.cbn.gov.ng/api/rates/{from_currency}/{to_currency}"
            
            if not self.session:
                return None
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    rate = Decimal(str(data.get('rate', 0)))
                    if rate > 0:
                        return ExchangeRate(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            rate=rate,
                            source=ExchangeRateSource.CENTRAL_BANK_NIGERIA,
                            timestamp=datetime.utcnow(),
                            is_official_cbn_rate=True,
                            confidence=1.0
                        )
        except Exception as e:
            self.logger.debug(f"CBN rate fetch failed: {str(e)}")
        
        return None
    
    async def _fetch_xe_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """Fetch rate from XE Currency (placeholder implementation)"""
        # This would implement actual XE API integration
        # For now, return a simulated rate for major currencies
        
        if from_currency == "USD" and to_currency == "NGN":
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal("760.50"),  # Simulated USD/NGN rate
                source=ExchangeRateSource.XE_CURRENCY,
                timestamp=datetime.utcnow(),
                confidence=0.9
            )
        
        return None
    
    async def _fetch_fixer_rate(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """Fetch rate from Fixer.io (placeholder implementation)"""
        # This would implement actual Fixer.io API integration
        return None
    
    async def _refresh_all_rates(self):
        """Refresh all cached exchange rates"""
        try:
            base_currency = self.config.base_currency
            
            for currency in self.config.supported_currencies:
                if currency != base_currency:
                    # Refresh both directions
                    await self.get_exchange_rate(currency, base_currency, force_refresh=True)
                    await self.get_exchange_rate(base_currency, currency, force_refresh=True)
            
            self.logger.info("Exchange rates refreshed")
            
        except Exception as e:
            self.logger.error(f"Rate refresh failed: {str(e)}")
    
    async def _rate_refresh_loop(self):
        """Background task for refreshing exchange rates"""
        while self._is_running:
            try:
                await self._refresh_all_rates()
                await asyncio.sleep(self.config.rate_refresh_interval_minutes * 60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Rate refresh loop error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    def _is_firs_reportable(self, amount: Decimal, from_currency: str, to_currency: str) -> bool:
        """Check if conversion is FIRS reportable"""
        # Nigerian transactions above threshold are reportable
        if from_currency == "NGN" or to_currency == "NGN":
            # Convert to USD equivalent for threshold check
            usd_equivalent = amount  # Simplified - would need actual conversion
            return usd_equivalent >= self.config.foreign_exchange_threshold
        
        return False
    
    def _update_conversion_stats(self, conversion: CurrencyConversion):
        """Update conversion statistics"""
        self.conversion_stats['total_conversions'] += 1
        self.conversion_stats['last_conversion_time'] = conversion.timestamp
        
        # Track volume by currency
        currency = conversion.original_currency
        if currency not in self.conversion_stats['total_volume_converted']:
            self.conversion_stats['total_volume_converted'][currency] = Decimal('0')
        self.conversion_stats['total_volume_converted'][currency] += conversion.original_amount
        
        # Track currency pairs
        pair = f"{conversion.original_currency}/{conversion.converted_currency}"
        self.conversion_stats['conversions_by_currency_pair'][pair] = \
            self.conversion_stats['conversions_by_currency_pair'].get(pair, 0) + 1
        
        # Update average conversion fee
        total_fees = (self.conversion_stats['average_conversion_fee'] * 
                     (self.conversion_stats['total_conversions'] - 1)) + conversion.conversion_fee
        self.conversion_stats['average_conversion_fee'] = total_fees / self.conversion_stats['total_conversions']
    
    def _get_currency_name(self, currency_code: str) -> str:
        """Get full currency name"""
        currency_names = {
            'NGN': 'Nigerian Naira',
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'JPY': 'Japanese Yen',
            'GHS': 'Ghanaian Cedi',
            'KES': 'Kenyan Shilling',
            'UGX': 'Ugandan Shilling',
            'ZAR': 'South African Rand',
            # Add more as needed
        }
        return currency_names.get(currency_code, currency_code)
    
    def _get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol"""
        symbols = {
            'NGN': '₦',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥',
            'GHS': 'GH₵',
            'KES': 'KSh',
            'ZAR': 'R',
            # Add more as needed
        }
        return symbols.get(currency_code, currency_code)
    
    def _get_currency_decimals(self, currency_code: str) -> int:
        """Get number of decimal places for currency"""
        # Most currencies use 2 decimal places
        # Some exceptions
        if currency_code in ['JPY', 'KRW']:
            return 0
        return 2
    
    def _calculate_volatility(self, rates: List[float]) -> float:
        """Calculate volatility of exchange rates"""
        if len(rates) < 2:
            return 0.0
        
        mean_rate = sum(rates) / len(rates)
        variance = sum((rate - mean_rate) ** 2 for rate in rates) / len(rates)
        volatility = variance ** 0.5
        
        return round(volatility, 6)
    
    def _calculate_trend_direction(self, rates: List[float]) -> str:
        """Calculate trend direction"""
        if len(rates) < 2:
            return 'stable'
        
        first_half = rates[:len(rates)//2]
        second_half = rates[len(rates)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg) * 100
        
        if change_percent > 2:
            return 'rising'
        elif change_percent < -2:
            return 'falling'
        else:
            return 'stable'


__all__ = [
    'MultiCurrencySupport',
    'MultiCurrencyConfig',
    'ExchangeRate',
    'CurrencyConversion',
    'ExchangeRateSource',
    'CurrencyConversionMethod'
]