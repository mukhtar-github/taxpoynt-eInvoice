"""
Currency Converter Service

This service handles multi-currency transactions, exchange rate management,
and currency conversion for FIRS e-invoicing compliance.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)


class CurrencyCode(Enum):
    """Supported currency codes (ISO 4217)"""
    NGN = "NGN"  # Nigerian Naira
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro
    GBP = "GBP"  # British Pound
    JPY = "JPY"  # Japanese Yen
    CNY = "CNY"  # Chinese Yuan
    CAD = "CAD"  # Canadian Dollar
    AUD = "AUD"  # Australian Dollar
    CHF = "CHF"  # Swiss Franc
    ZAR = "ZAR"  # South African Rand


@dataclass
class ExchangeRate:
    """Exchange rate data structure"""
    from_currency: str
    to_currency: str
    rate: Decimal
    date: datetime
    source: str
    bid_rate: Optional[Decimal] = None
    ask_rate: Optional[Decimal] = None
    mid_rate: Optional[Decimal] = None


@dataclass
class CurrencyConversionResult:
    """Result of currency conversion"""
    original_amount: Decimal
    original_currency: str
    converted_amount: Decimal
    target_currency: str
    exchange_rate: Decimal
    conversion_date: datetime
    rate_source: str
    fees: Optional[Decimal] = None
    precision: int = 2


class ExchangeRateProvider:
    """Base class for exchange rate providers"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def get_rate(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> Optional[ExchangeRate]:
        """Get exchange rate between two currencies"""
        raise NotImplementedError
    
    async def get_multiple_rates(self, base_currency: str, target_currencies: List[str], date: Optional[datetime] = None) -> Dict[str, ExchangeRate]:
        """Get multiple exchange rates for a base currency"""
        rates = {}
        for target in target_currencies:
            rate = await self.get_rate(base_currency, target, date)
            if rate:
                rates[target] = rate
        return rates


class CBNExchangeRateProvider(ExchangeRateProvider):
    """Central Bank of Nigeria exchange rate provider"""
    
    def __init__(self):
        super().__init__("CBN")
        self.base_url = "https://api.cbn.gov.ng/api/v1"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_rate(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> Optional[ExchangeRate]:
        """Get exchange rate from CBN API"""
        if not self.session:
            return None
        
        try:
            # CBN typically provides rates in NGN terms
            if from_currency == "NGN":
                # For NGN to other currencies, get the reciprocal
                endpoint = f"{self.base_url}/exchange-rates"
                params = {}
                if date:
                    params["date"] = date.strftime("%Y-%m-%d")
                
                async with self.session.get(endpoint, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Parse CBN response format
                        rate_data = self._parse_cbn_response(data, to_currency)
                        if rate_data:
                            return ExchangeRate(
                                from_currency=from_currency,
                                to_currency=to_currency,
                                rate=Decimal(str(rate_data["rate"])),
                                date=date or datetime.now(),
                                source="CBN",
                                bid_rate=Decimal(str(rate_data.get("bid_rate", 0))) if rate_data.get("bid_rate") else None,
                                ask_rate=Decimal(str(rate_data.get("ask_rate", 0))) if rate_data.get("ask_rate") else None
                            )
            
            elif to_currency == "NGN":
                # For other currencies to NGN
                endpoint = f"{self.base_url}/exchange-rates/{from_currency}"
                async with self.session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        rate_value = data.get("rate", 0)
                        return ExchangeRate(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            rate=Decimal(str(rate_value)),
                            date=date or datetime.now(),
                            source="CBN"
                        )
            
        except Exception as e:
            logger.error(f"CBN API error for {from_currency} to {to_currency}: {str(e)}")
        
        return None
    
    def _parse_cbn_response(self, data: Dict[str, Any], target_currency: str) -> Optional[Dict[str, Any]]:
        """Parse CBN API response"""
        # This would parse the actual CBN response format
        # Simulated for now
        rates = {
            "USD": {"rate": 0.0024, "bid_rate": 0.0023, "ask_rate": 0.0025},
            "EUR": {"rate": 0.0022, "bid_rate": 0.0021, "ask_rate": 0.0023},
            "GBP": {"rate": 0.0019, "bid_rate": 0.0018, "ask_rate": 0.0020}
        }
        return rates.get(target_currency)


class ExternalAPIProvider(ExchangeRateProvider):
    """External API exchange rate provider (e.g., Fixer.io, ExchangeRate-API)"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("ExternalAPI")
        self.api_key = api_key
        self.base_url = "https://api.exchangerate-api.com/v4/latest"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_rate(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> Optional[ExchangeRate]:
        """Get exchange rate from external API"""
        if not self.session:
            return None
        
        try:
            url = f"{self.base_url}/{from_currency}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = data.get("rates", {})
                    if to_currency in rates:
                        return ExchangeRate(
                            from_currency=from_currency,
                            to_currency=to_currency,
                            rate=Decimal(str(rates[to_currency])),
                            date=datetime.now(),
                            source="ExternalAPI"
                        )
        except Exception as e:
            logger.error(f"External API error for {from_currency} to {to_currency}: {str(e)}")
        
        return None


class DatabaseRateProvider(ExchangeRateProvider):
    """Database-stored exchange rates provider"""
    
    def __init__(self, db_connection=None):
        super().__init__("Database")
        self.db_connection = db_connection
    
    async def get_rate(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> Optional[ExchangeRate]:
        """Get exchange rate from database"""
        if not self.db_connection:
            return None
        
        try:
            # Query database for exchange rate
            query = """
            SELECT rate, bid_rate, ask_rate, rate_date, source
            FROM exchange_rates 
            WHERE from_currency = %s AND to_currency = %s
            AND rate_date <= %s
            ORDER BY rate_date DESC
            LIMIT 1
            """
            
            search_date = date or datetime.now()
            # Execute query (simulated)
            # result = await self.db_connection.fetch_one(query, from_currency, to_currency, search_date)
            
            # Simulated result
            result = {
                "rate": 415.0,
                "bid_rate": 414.0,
                "ask_rate": 416.0,
                "rate_date": search_date,
                "source": "Database"
            }
            
            if result:
                return ExchangeRate(
                    from_currency=from_currency,
                    to_currency=to_currency,
                    rate=Decimal(str(result["rate"])),
                    date=result["rate_date"],
                    source=result["source"],
                    bid_rate=Decimal(str(result["bid_rate"])) if result["bid_rate"] else None,
                    ask_rate=Decimal(str(result["ask_rate"])) if result["ask_rate"] else None
                )
                
        except Exception as e:
            logger.error(f"Database rate lookup error for {from_currency} to {to_currency}: {str(e)}")
        
        return None
    
    async def store_rate(self, rate: ExchangeRate) -> bool:
        """Store exchange rate in database"""
        if not self.db_connection:
            return False
        
        try:
            query = """
            INSERT INTO exchange_rates 
            (from_currency, to_currency, rate, bid_rate, ask_rate, rate_date, source)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (from_currency, to_currency, rate_date) 
            DO UPDATE SET rate = EXCLUDED.rate
            """
            
            # Execute query (simulated)
            # await self.db_connection.execute(query, 
            #     rate.from_currency, rate.to_currency, float(rate.rate),
            #     float(rate.bid_rate) if rate.bid_rate else None,
            #     float(rate.ask_rate) if rate.ask_rate else None,
            #     rate.date, rate.source)
            
            logger.info(f"Stored rate {rate.from_currency}/{rate.to_currency}: {rate.rate}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing rate: {str(e)}")
            return False


class CurrencyConverter:
    """Main currency conversion service"""
    
    def __init__(self, db_connection=None):
        self.providers: List[ExchangeRateProvider] = []
        self.cache: Dict[str, ExchangeRate] = {}
        self.cache_duration = timedelta(hours=1)
        self.db_provider = DatabaseRateProvider(db_connection)
        
        # Initialize providers in order of preference
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize exchange rate providers"""
        # Add providers in order of preference
        self.providers = [
            self.db_provider,  # Database first (fastest)
            # CBN and external providers would be added here
        ]
    
    def add_provider(self, provider: ExchangeRateProvider):
        """Add exchange rate provider"""
        self.providers.append(provider)
    
    def _get_cache_key(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> str:
        """Generate cache key for exchange rate"""
        date_str = date.strftime("%Y-%m-%d") if date else "current"
        return f"{from_currency}_{to_currency}_{date_str}"
    
    def _is_cache_valid(self, rate: ExchangeRate) -> bool:
        """Check if cached rate is still valid"""
        return datetime.now() - rate.date < self.cache_duration
    
    async def get_exchange_rate(self, from_currency: str, to_currency: str, date: Optional[datetime] = None) -> Optional[ExchangeRate]:
        """Get exchange rate between two currencies"""
        # Same currency
        if from_currency == to_currency:
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                rate=Decimal("1.0"),
                date=datetime.now(),
                source="identity"
            )
        
        # Check cache first
        cache_key = self._get_cache_key(from_currency, to_currency, date)
        if cache_key in self.cache:
            cached_rate = self.cache[cache_key]
            if self._is_cache_valid(cached_rate):
                return cached_rate
        
        # Try providers in order
        for provider in self.providers:
            try:
                if hasattr(provider, '__aenter__'):
                    async with provider as p:
                        rate = await p.get_rate(from_currency, to_currency, date)
                else:
                    rate = await provider.get_rate(from_currency, to_currency, date)
                
                if rate:
                    # Cache the rate
                    self.cache[cache_key] = rate
                    
                    # Store in database if not from database
                    if provider != self.db_provider:
                        await self.db_provider.store_rate(rate)
                    
                    return rate
                    
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {str(e)}")
                continue
        
        logger.error(f"No exchange rate found for {from_currency} to {to_currency}")
        return None
    
    async def convert_currency(self, amount: Decimal, from_currency: str, to_currency: str, 
                             date: Optional[datetime] = None, precision: int = 2) -> Optional[CurrencyConversionResult]:
        """Convert amount from one currency to another"""
        rate = await self.get_exchange_rate(from_currency, to_currency, date)
        if not rate:
            return None
        
        # Perform conversion
        converted_amount = amount * rate.rate
        
        # Apply precision
        converted_amount = converted_amount.quantize(
            Decimal(10) ** -precision, 
            rounding=ROUND_HALF_UP
        )
        
        return CurrencyConversionResult(
            original_amount=amount,
            original_currency=from_currency,
            converted_amount=converted_amount,
            target_currency=to_currency,
            exchange_rate=rate.rate,
            conversion_date=rate.date,
            rate_source=rate.source,
            precision=precision
        )
    
    async def convert_invoice_amounts(self, invoice_data: Dict[str, Any], target_currency: str) -> Dict[str, Any]:
        """Convert all amounts in an invoice to target currency"""
        converted_invoice = invoice_data.copy()
        original_currency = invoice_data.get("currency_code", "NGN")
        
        if original_currency == target_currency:
            return converted_invoice
        
        logger.info(f"Converting invoice from {original_currency} to {target_currency}")
        
        # Amount fields to convert
        amount_fields = [
            "total_amount", "tax_amount", "discount_amount", 
            "base_amount", "subtotal", "shipping_amount"
        ]
        
        # Convert main amounts
        for field in amount_fields:
            if field in invoice_data and invoice_data[field]:
                amount = Decimal(str(invoice_data[field]))
                result = await self.convert_currency(amount, original_currency, target_currency)
                if result:
                    converted_invoice[f"{field}_original"] = float(amount)
                    converted_invoice[field] = float(result.converted_amount)
        
        # Convert line item amounts
        if "line_items" in invoice_data:
            converted_items = []
            for item in invoice_data["line_items"]:
                converted_item = item.copy()
                
                line_amount_fields = ["unit_price", "total", "tax_amount", "subtotal"]
                for field in line_amount_fields:
                    if field in item and item[field]:
                        amount = Decimal(str(item[field]))
                        result = await self.convert_currency(amount, original_currency, target_currency)
                        if result:
                            converted_item[f"{field}_original"] = float(amount)
                            converted_item[field] = float(result.converted_amount)
                
                converted_items.append(converted_item)
            
            converted_invoice["line_items"] = converted_items
        
        # Update currency code and add conversion metadata
        converted_invoice["currency_code"] = target_currency
        converted_invoice["original_currency"] = original_currency
        converted_invoice["conversion_date"] = datetime.now().isoformat()
        
        # Get the exchange rate for metadata
        rate = await self.get_exchange_rate(original_currency, target_currency)
        if rate:
            converted_invoice["conversion_rate"] = float(rate.rate)
            converted_invoice["conversion_source"] = rate.source
        
        return converted_invoice
    
    async def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        return [currency.value for currency in CurrencyCode]
    
    async def validate_currency_code(self, currency_code: str) -> bool:
        """Validate currency code"""
        supported = await self.get_supported_currencies()
        return currency_code.upper() in supported
    
    async def get_currency_info(self, currency_code: str) -> Optional[Dict[str, Any]]:
        """Get information about a currency"""
        currency_info = {
            "NGN": {"name": "Nigerian Naira", "symbol": "₦", "decimal_places": 2},
            "USD": {"name": "US Dollar", "symbol": "$", "decimal_places": 2},
            "EUR": {"name": "Euro", "symbol": "€", "decimal_places": 2},
            "GBP": {"name": "British Pound", "symbol": "£", "decimal_places": 2},
            "JPY": {"name": "Japanese Yen", "symbol": "¥", "decimal_places": 0},
            "CNY": {"name": "Chinese Yuan", "symbol": "¥", "decimal_places": 2},
            "CAD": {"name": "Canadian Dollar", "symbol": "C$", "decimal_places": 2},
            "AUD": {"name": "Australian Dollar", "symbol": "A$", "decimal_places": 2},
            "CHF": {"name": "Swiss Franc", "symbol": "Fr", "decimal_places": 2},
            "ZAR": {"name": "South African Rand", "symbol": "R", "decimal_places": 2}
        }
        
        return currency_info.get(currency_code.upper())
    
    async def refresh_rates(self, base_currency: str = "NGN") -> Dict[str, bool]:
        """Refresh exchange rates for all supported currencies"""
        results = {}
        supported_currencies = await self.get_supported_currencies()
        
        for target_currency in supported_currencies:
            if target_currency != base_currency:
                try:
                    rate = await self.get_exchange_rate(base_currency, target_currency)
                    results[target_currency] = rate is not None
                except Exception as e:
                    logger.error(f"Error refreshing rate for {target_currency}: {str(e)}")
                    results[target_currency] = False
        
        return results
    
    def clear_cache(self):
        """Clear exchange rate cache"""
        self.cache.clear()
        logger.info("Exchange rate cache cleared")
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        now = datetime.now()
        valid_entries = sum(1 for rate in self.cache.values() if self._is_cache_valid(rate))
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_entries,
            "expired_entries": len(self.cache) - valid_entries,
            "cache_duration_hours": self.cache_duration.total_seconds() / 3600
        }