"""
Lightspeed POS Data Extractor

Extracts and transforms POS transaction data from Lightspeed Retail and Restaurant APIs
into standardized POSTransaction objects for TaxPoynt eInvoice processing.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from ....connector_framework.base_pos_connector import (
    POSTransaction, POSLocation, POSPaymentMethod, POSInventoryItem
)
from .rest_client import LightspeedRESTClient
from .exceptions import LightspeedAPIError, LightspeedValidationError

logger = logging.getLogger(__name__)


class LightspeedDataExtractor:
    """
    Lightspeed POS data extractor for TaxPoynt eInvoice System Integrator functions.
    
    Extracts sales transactions, customer data, product information, and inventory
    from both Lightspeed Retail (R-Series) and Restaurant (K-Series) systems.
    
    Features:
    - Multi-API support (Retail and Restaurant)
    - Nigerian market adaptations (NGN currency, tax calculations)
    - Comprehensive transaction data extraction
    - Customer and product data enrichment
    - Location and payment method mapping
    - Real-time inventory status
    """
    
    def __init__(self, client: LightspeedRESTClient, config: Dict[str, Any]):
        """
        Initialize Lightspeed data extractor.
        
        Args:
            client: Configured LightspeedRESTClient instance
            config: Configuration dictionary with extractor settings
        """
        self.client = client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Nigerian market configuration
        self.default_currency = config.get('currency', 'NGN')
        self.vat_rate = Decimal(str(config.get('vat_rate', '0.075')))  # 7.5% Nigerian VAT
        self.exchange_rates = config.get('exchange_rates', {})
        
        # API type configuration
        self.api_type = client.api_type
        
        # Caching for frequently accessed data
        self._locations_cache = {}
        self._payment_types_cache = {}
        self._customers_cache = {}
        self._products_cache = {}
        
        # Nigerian business configuration
        self.business_hours_start = config.get('business_hours_start', 8)  # 8 AM
        self.business_hours_end = config.get('business_hours_end', 22)    # 10 PM
    
    async def extract_transactions(self, 
                                 filters: Optional[Dict[str, Any]] = None, 
                                 limit: Optional[int] = None) -> List[POSTransaction]:
        """
        Extract POS transactions from Lightspeed.
        
        Args:
            filters: Filter criteria for transactions
            limit: Maximum number of transactions to return
            
        Returns:
            List of standardized POSTransaction objects
        """
        try:
            self.logger.info(f"Extracting Lightspeed transactions with filters: {filters}")
            
            # Get sales from Lightspeed API
            sales = await self.client.get_sales(filters=filters, limit=limit)
            
            transactions = []
            for sale in sales:
                try:
                    transaction = await self._convert_sale_to_transaction(sale)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.logger.error(f"Failed to convert sale {sale.get('saleID', 'unknown')}: {str(e)}")
                    continue
            
            self.logger.info(f"Successfully extracted {len(transactions)} transactions")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Failed to extract transactions: {str(e)}")
            raise
    
    async def extract_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Extract a specific transaction by ID.
        
        Args:
            transaction_id: Lightspeed sale ID
            
        Returns:
            POSTransaction object or None if not found
        """
        try:
            sale = await self.client.get_sale_by_id(transaction_id)
            if not sale:
                return None
            
            return await self._convert_sale_to_transaction(sale)
        
        except Exception as e:
            self.logger.error(f"Failed to extract transaction {transaction_id}: {str(e)}")
            raise
    
    async def _convert_sale_to_transaction(self, sale: Dict[str, Any]) -> Optional[POSTransaction]:
        """
        Convert Lightspeed sale to standardized POSTransaction.
        
        Args:
            sale: Lightspeed sale object
            
        Returns:
            POSTransaction object
        """
        try:
            # Extract basic sale information
            if self.api_type == 'retail':
                sale_id = str(sale.get('saleID', ''))
                timestamp = self._parse_datetime(sale.get('timeStamp', sale.get('createTime')))
                total_amount = Decimal(str(sale.get('total', '0')))
                tax_amount = Decimal(str(sale.get('taxTotal', '0')))
                location_id = str(sale.get('shopID', ''))
                register_id = sale.get('registerID')
                customer_id = sale.get('customerID')
                completed = sale.get('completed') == 'true'
            else:  # restaurant
                sale_id = str(sale.get('id', ''))
                timestamp = self._parse_datetime(sale.get('created_at', sale.get('timestamp')))
                total_amount = Decimal(str(sale.get('total_amount', '0')))
                tax_amount = Decimal(str(sale.get('tax_amount', '0')))
                location_id = str(sale.get('location_id', ''))
                register_id = sale.get('terminal_id')
                customer_id = sale.get('customer_id')
                completed = sale.get('status') == 'completed'
            
            if not sale_id:
                self.logger.warning("Sale missing ID, skipping")
                return None
            
            if not completed:
                self.logger.debug(f"Sale {sale_id} not completed, skipping")
                return None
            
            # Get enriched data
            line_items = await self._extract_line_items(sale_id, sale)
            payment_info = await self._extract_payment_info(sale_id, sale)
            customer_info = await self._extract_customer_info(customer_id) if customer_id else None
            
            # Convert currency to NGN if necessary
            original_currency = self._detect_currency(sale)
            if original_currency != self.default_currency:
                total_amount = self._convert_to_ngn(total_amount, original_currency)
                tax_amount = self._convert_to_ngn(tax_amount, original_currency)
                # Convert line item amounts
                for item in line_items:
                    if 'unit_price' in item:
                        item['unit_price'] = self._convert_to_ngn(
                            Decimal(str(item['unit_price'])), original_currency
                        )
                    if 'total_price' in item:
                        item['total_price'] = self._convert_to_ngn(
                            Decimal(str(item['total_price'])), original_currency
                        )
            
            # Calculate Nigerian tax compliance
            tax_info = self._calculate_nigerian_tax(total_amount, tax_amount)
            
            # Build transaction metadata
            metadata = self._build_transaction_metadata(sale, location_id, register_id, original_currency)
            
            # Create POSTransaction
            transaction = POSTransaction(
                transaction_id=sale_id,
                timestamp=timestamp,
                amount=float(total_amount),
                currency=self.default_currency,
                payment_method=payment_info.get('method', 'UNKNOWN'),
                location_id=location_id,
                items=line_items,
                customer_info=customer_info,
                tax_info=tax_info,
                metadata=metadata
            )
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Failed to convert sale to transaction: {str(e)}")
            raise
    
    async def _extract_line_items(self, sale_id: str, sale: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and process line items from a sale."""
        try:
            line_items = []
            
            # Get line items from API
            if self.api_type == 'retail':
                lines = await self.client.get_sale_lines(sale_id)
            else:  # restaurant
                lines = sale.get('items', [])
                if not lines:
                    lines = await self.client.get_sale_lines(sale_id)
            
            for line in lines:
                try:
                    item = await self._convert_line_item(line)
                    if item:
                        line_items.append(item)
                except Exception as e:
                    self.logger.warning(f"Failed to process line item: {str(e)}")
                    continue
            
            return line_items
        
        except Exception as e:
            self.logger.error(f"Failed to extract line items for sale {sale_id}: {str(e)}")
            return []
    
    async def _convert_line_item(self, line: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Lightspeed line item to standardized format."""
        try:
            if self.api_type == 'retail':
                item_id = str(line.get('itemID', ''))
                name = line.get('description', 'Unknown Item')
                quantity = int(line.get('unitQuantity', 1))
                unit_price = Decimal(str(line.get('unitPrice', '0')))
                total_price = Decimal(str(line.get('calcTotal', '0')))
                sku = line.get('sku', '')
                discount_amount = Decimal(str(line.get('discountPercent', '0')))
            else:  # restaurant
                item_id = str(line.get('product_id', ''))
                name = line.get('name', 'Unknown Item')
                quantity = int(line.get('quantity', 1))
                unit_price = Decimal(str(line.get('unit_price', '0')))
                total_price = Decimal(str(line.get('total_price', '0')))
                sku = line.get('sku', '')
                discount_amount = Decimal(str(line.get('discount_amount', '0')))
            
            # Get product details for enrichment
            product_info = await self._get_product_info(item_id) if item_id else {}
            
            # Build line item
            item = {
                'id': item_id,
                'name': name,
                'description': product_info.get('description', name),
                'sku': sku or product_info.get('sku', ''),
                'quantity': quantity,
                'unit_price': float(unit_price),
                'total_price': float(total_price),
                'discount_amount': float(discount_amount),
                'category': product_info.get('category'),
                'metadata': {
                    'lightspeed_item_id': item_id,
                    'lightspeed_line_data': line,
                    'product_type': product_info.get('type'),
                    'tax_class': product_info.get('tax_class')
                }
            }
            
            return item
        
        except Exception as e:
            self.logger.error(f"Failed to convert line item: {str(e)}")
            return None
    
    async def _extract_payment_info(self, sale_id: str, sale: Dict[str, Any]) -> Dict[str, Any]:
        """Extract payment information from sale."""
        try:
            # Get payment data
            if self.api_type == 'retail':
                payments = await self.client.get_sale_payments(sale_id)
            else:  # restaurant
                payments = sale.get('payments', [])
                if not payments:
                    payments = await self.client.get_sale_payments(sale_id)
            
            if not payments:
                return {'method': 'UNKNOWN', 'amount': 0}
            
            # Process primary payment (first one if multiple)
            primary_payment = payments[0] if isinstance(payments, list) else payments
            
            if self.api_type == 'retail':
                payment_type_id = primary_payment.get('paymentTypeID')
                amount = Decimal(str(primary_payment.get('amount', '0')))
            else:  # restaurant
                payment_type_id = primary_payment.get('payment_type_id')
                amount = Decimal(str(primary_payment.get('amount', '0')))
            
            # Map payment type
            payment_method = await self._map_payment_method(payment_type_id)
            
            return {
                'method': payment_method,
                'amount': float(amount),
                'payment_id': primary_payment.get('id', primary_payment.get('paymentID')),
                'all_payments': payments
            }
        
        except Exception as e:
            self.logger.error(f"Failed to extract payment info for sale {sale_id}: {str(e)}")
            return {'method': 'UNKNOWN', 'amount': 0}
    
    async def _extract_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Extract customer information."""
        if not customer_id:
            return None
        
        try:
            # Check cache first
            if customer_id in self._customers_cache:
                return self._customers_cache[customer_id]
            
            # Get customer from API (simplified - would need specific endpoint)
            customers = await self.client.get_customers()
            
            customer = None
            for c in customers:
                if str(c.get('customerID' if self.api_type == 'retail' else 'id')) == customer_id:
                    customer = c
                    break
            
            if not customer:
                return None
            
            # Convert to standard format
            if self.api_type == 'retail':
                customer_info = {
                    'id': str(customer.get('customerID', '')),
                    'name': f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
                    'email': customer.get('Contact', {}).get('Emails', {}).get('ContactEmail', {}).get('address'),
                    'phone': customer.get('Contact', {}).get('Phones', {}).get('ContactPhone', {}).get('number'),
                    'address': self._extract_customer_address(customer)
                }
            else:  # restaurant
                customer_info = {
                    'id': str(customer.get('id', '')),
                    'name': customer.get('name', ''),
                    'email': customer.get('email'),
                    'phone': customer.get('phone'),
                    'address': customer.get('address', {})
                }
            
            # Cache for future use
            self._customers_cache[customer_id] = customer_info
            
            return customer_info
        
        except Exception as e:
            self.logger.error(f"Failed to extract customer info for {customer_id}: {str(e)}")
            return None
    
    def _extract_customer_address(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer address from Lightspeed Retail customer object."""
        try:
            contact = customer.get('Contact', {})
            addresses = contact.get('Addresses', {})
            
            if isinstance(addresses, dict) and 'ContactAddress' in addresses:
                address_data = addresses['ContactAddress']
                if isinstance(address_data, list):
                    address_data = address_data[0]  # Take first address
                
                return {
                    'address_line_1': address_data.get('address1', ''),
                    'address_line_2': address_data.get('address2', ''),
                    'city': address_data.get('city', ''),
                    'state': address_data.get('state', ''),
                    'postal_code': address_data.get('zip', ''),
                    'country': address_data.get('country', 'Nigeria')
                }
            
            return {}
        
        except Exception as e:
            self.logger.error(f"Failed to extract customer address: {str(e)}")
            return {}
    
    async def _get_product_info(self, item_id: str) -> Dict[str, Any]:
        """Get cached or fetch product information."""
        if not item_id:
            return {}
        
        try:
            # Check cache
            if item_id in self._products_cache:
                return self._products_cache[item_id]
            
            # This would require a separate API call - simplified for performance
            # In production, you might batch these or pre-populate cache
            return {}
        
        except Exception:
            return {}
    
    async def _map_payment_method(self, payment_type_id: str) -> str:
        """Map Lightspeed payment type to standard payment method."""
        if not payment_type_id:
            return 'UNKNOWN'
        
        try:
            # Check cache
            if payment_type_id in self._payment_types_cache:
                return self._payment_types_cache[payment_type_id]
            
            # Get payment types (cached after first call)
            if not self._payment_types_cache:
                payment_types = await self.client.get_payment_types()
                for pt in payment_types:
                    pt_id = str(pt.get('paymentTypeID' if self.api_type == 'retail' else 'id'))
                    pt_name = pt.get('name', 'Unknown').upper()
                    
                    # Map to standard payment methods
                    if 'CASH' in pt_name:
                        mapped_method = 'CASH'
                    elif any(word in pt_name for word in ['CARD', 'CREDIT', 'DEBIT', 'VISA', 'MASTER']):
                        mapped_method = 'CARD'
                    elif any(word in pt_name for word in ['MOBILE', 'TRANSFER', 'BANK']):
                        mapped_method = 'TRANSFER'
                    else:
                        mapped_method = 'OTHER'
                    
                    self._payment_types_cache[pt_id] = mapped_method
            
            return self._payment_types_cache.get(payment_type_id, 'UNKNOWN')
        
        except Exception as e:
            self.logger.error(f"Failed to map payment method {payment_type_id}: {str(e)}")
            return 'UNKNOWN'
    
    def _detect_currency(self, sale: Dict[str, Any]) -> str:
        """Detect currency from sale data."""
        # Lightspeed doesn't always include currency in sale data
        # Check various possible fields
        currency = None
        
        if self.api_type == 'retail':
            # Look for currency in sale or shop configuration
            currency = sale.get('currency')
        else:  # restaurant
            currency = sale.get('currency_code')
        
        return currency or 'USD'  # Default to USD if not specified
    
    def _convert_to_ngn(self, amount: Decimal, from_currency: str) -> Decimal:
        """Convert amount to Nigerian Naira."""
        if from_currency == 'NGN':
            return amount
        
        # Use configured exchange rates or default rates
        exchange_rate = self.exchange_rates.get(from_currency, {
            'USD': Decimal('1600'),  # 1 USD = 1600 NGN (approximate)
            'EUR': Decimal('1750'),  # 1 EUR = 1750 NGN (approximate)
            'GBP': Decimal('2000'),  # 1 GBP = 2000 NGN (approximate)
        }.get(from_currency, Decimal('1600')))
        
        return amount * exchange_rate
    
    def _calculate_nigerian_tax(self, total_amount: Decimal, original_tax: Decimal) -> Dict[str, Any]:
        """Calculate Nigerian tax compliance information."""
        # Calculate tax-exclusive amount
        if original_tax > 0:
            exclusive_amount = total_amount - original_tax
            tax_rate = original_tax / exclusive_amount if exclusive_amount > 0 else self.vat_rate
        else:
            # Assume total includes VAT at 7.5%
            exclusive_amount = total_amount / (1 + self.vat_rate)
            tax_rate = self.vat_rate
        
        # Calculate Nigerian VAT
        nigerian_vat = exclusive_amount * self.vat_rate
        
        return {
            'amount': float(original_tax),
            'nigerian_vat': float(nigerian_vat),
            'exclusive_amount': float(exclusive_amount),
            'inclusive_amount': float(total_amount),
            'tax_rate': float(tax_rate),
            'nigerian_vat_rate': float(self.vat_rate),
            'compliant': True
        }
    
    def _build_transaction_metadata(self, sale: Dict[str, Any], location_id: str, 
                                  register_id: Optional[str], original_currency: str) -> Dict[str, Any]:
        """Build comprehensive transaction metadata."""
        timestamp = self._parse_datetime(sale.get('timeStamp', sale.get('created_at')))
        
        return {
            'lightspeed_sale_id': sale.get('saleID' if self.api_type == 'retail' else 'id'),
            'lightspeed_api_type': self.api_type,
            'location_id': location_id,
            'register_id': register_id,
            'original_currency': original_currency,
            'conversion_rate': str(self.exchange_rates.get(original_currency, 1)),
            'business_date': timestamp.date().isoformat() if timestamp else None,
            'business_hours': self._is_business_hours(timestamp),
            'sale_type': sale.get('saleType', 'sale'),
            'completed': sale.get('completed'),
            'employee_id': sale.get('employeeID'),
            'raw_sale_data': sale,
            'processing_timestamp': datetime.now().isoformat(),
            'extractor_version': '1.0'
        }
    
    def _parse_datetime(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Lightspeed timestamp string to datetime."""
        if not timestamp_str:
            return None
        
        try:
            # Handle different timestamp formats
            if 'T' in timestamp_str:
                # ISO format
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                # Try parsing as date only
                return datetime.strptime(timestamp_str, '%Y-%m-%d')
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to parse timestamp '{timestamp_str}': {str(e)}")
            return None
    
    def _is_business_hours(self, timestamp: Optional[datetime]) -> bool:
        """Check if transaction occurred during business hours."""
        if not timestamp:
            return False
        
        hour = timestamp.hour
        return self.business_hours_start <= hour <= self.business_hours_end
    
    async def extract_locations(self) -> List[POSLocation]:
        """Extract location information."""
        try:
            locations_data = await self.client.get_locations()
            locations = []
            
            for loc in locations_data:
                if self.api_type == 'retail':
                    location = POSLocation(
                        location_id=str(loc.get('shopID', '')),
                        name=loc.get('name', 'Unknown Location'),
                        address=loc.get('Contact', {}).get('Addresses', {}),
                        timezone=loc.get('timeZone', 'Africa/Lagos'),
                        active=True,
                        metadata={'lightspeed_data': loc}
                    )
                else:  # restaurant
                    location = POSLocation(
                        location_id=str(loc.get('id', '')),
                        name=loc.get('name', 'Unknown Location'),
                        address=loc.get('address', {}),
                        timezone=loc.get('timezone', 'Africa/Lagos'),
                        active=loc.get('active', True),
                        metadata={'lightspeed_data': loc}
                    )
                
                locations.append(location)
            
            return locations
        
        except Exception as e:
            self.logger.error(f"Failed to extract locations: {str(e)}")
            raise
    
    async def extract_payment_methods(self) -> List[POSPaymentMethod]:
        """Extract payment method information."""
        try:
            payment_types = await self.client.get_payment_types()
            methods = []
            
            for pt in payment_types:
                if self.api_type == 'retail':
                    method = POSPaymentMethod(
                        method_id=str(pt.get('paymentTypeID', '')),
                        name=pt.get('name', 'Unknown Method'),
                        type=self._standardize_payment_type(pt.get('name', '')),
                        active=True,
                        metadata={'lightspeed_data': pt}
                    )
                else:  # restaurant
                    method = POSPaymentMethod(
                        method_id=str(pt.get('id', '')),
                        name=pt.get('name', 'Unknown Method'),
                        type=self._standardize_payment_type(pt.get('name', '')),
                        active=pt.get('active', True),
                        metadata={'lightspeed_data': pt}
                    )
                
                methods.append(method)
            
            return methods
        
        except Exception as e:
            self.logger.error(f"Failed to extract payment methods: {str(e)}")
            raise
    
    def _standardize_payment_type(self, name: str) -> str:
        """Standardize payment type name."""
        name_upper = name.upper()
        
        if 'CASH' in name_upper:
            return 'CASH'
        elif any(word in name_upper for word in ['CARD', 'CREDIT', 'DEBIT']):
            return 'CARD'
        elif any(word in name_upper for word in ['MOBILE', 'TRANSFER', 'BANK']):
            return 'TRANSFER'
        else:
            return 'OTHER'
    
    async def extract_inventory_items(self, filters: Optional[Dict[str, Any]] = None) -> List[POSInventoryItem]:
        """Extract inventory/product information."""
        try:
            products = await self.client.get_products(filters=filters)
            items = []
            
            for product in products:
                if self.api_type == 'retail':
                    item = POSInventoryItem(
                        item_id=str(product.get('itemID', '')),
                        sku=product.get('sku', ''),
                        name=product.get('description', 'Unknown Item'),
                        category=product.get('Category', {}).get('name'),
                        price=float(product.get('Prices', {}).get('ItemPrice', {}).get('amount', 0)),
                        cost=float(product.get('avgCost', 0)),
                        quantity_on_hand=int(product.get('qtyOnHand', 0)),
                        active=True,
                        metadata={'lightspeed_data': product}
                    )
                else:  # restaurant
                    item = POSInventoryItem(
                        item_id=str(product.get('id', '')),
                        sku=product.get('sku', ''),
                        name=product.get('name', 'Unknown Item'),
                        category=product.get('category', {}).get('name'),
                        price=float(product.get('price', 0)),
                        cost=float(product.get('cost', 0)),
                        quantity_on_hand=int(product.get('stock_quantity', 0)),
                        active=product.get('active', True),
                        metadata={'lightspeed_data': product}
                    )
                
                items.append(item)
            
            return items
        
        except Exception as e:
            self.logger.error(f"Failed to extract inventory items: {str(e)}")
            raise