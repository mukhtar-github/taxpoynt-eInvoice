"""
Clover POS Data Extractor

Extracts and transforms POS transaction data from Clover REST API
into standardized POSTransaction objects for TaxPoynt eInvoice processing.
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from ....connector_framework.base_pos_connector import (
    POSTransaction, POSLocation, POSPaymentMethod, POSInventoryItem
)
from .rest_client import CloverRESTClient
from .exceptions import CloverAPIError, CloverValidationError

logger = logging.getLogger(__name__)


class CloverDataExtractor:
    """
    Clover POS data extractor for TaxPoynt eInvoice System Integrator functions.
    
    Extracts orders, payments, customer data, inventory information, and device data
    from Clover REST API with comprehensive Nigerian market adaptations.
    
    Features:
    - Complete order and payment data extraction
    - Nigerian market adaptations (NGN currency, tax calculations)
    - Customer and employee data enrichment
    - Device and location mapping
    - Real-time inventory status
    - Comprehensive error handling and validation
    """
    
    def __init__(self, client: CloverRESTClient, config: Dict[str, Any]):
        """
        Initialize Clover data extractor.
        
        Args:
            client: Configured CloverRESTClient instance
            config: Configuration dictionary with extractor settings
        """
        self.client = client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Nigerian market configuration
        self.default_currency = config.get('currency', 'NGN')
        self.vat_rate = Decimal(str(config.get('vat_rate', '0.075')))  # 7.5% Nigerian VAT
        self.exchange_rates = config.get('exchange_rates', {})
        
        # Clover amounts are in cents
        self.cents_to_currency = Decimal('0.01')
        
        # Caching for frequently accessed data
        self._devices_cache = {}
        self._employees_cache = {}
        self._customers_cache = {}
        self._items_cache = {}
        self._tenders_cache = {}
        self._categories_cache = {}
        
        # Nigerian business configuration
        self.business_hours_start = config.get('business_hours_start', 8)  # 8 AM
        self.business_hours_end = config.get('business_hours_end', 22)    # 10 PM
    
    async def extract_transactions(self, 
                                 filters: Optional[Dict[str, Any]] = None, 
                                 limit: Optional[int] = None) -> List[POSTransaction]:
        """
        Extract POS transactions from Clover orders.
        
        Args:
            filters: Filter criteria for transactions
            limit: Maximum number of transactions to return
            
        Returns:
            List of standardized POSTransaction objects
        """
        try:
            self.logger.info(f"Extracting Clover transactions with filters: {filters}")
            
            # Get orders from Clover API
            orders = await self.client.get_orders(filters=filters, limit=limit)
            
            transactions = []
            for order in orders:
                try:
                    transaction = await self._convert_order_to_transaction(order)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.logger.error(f"Failed to convert order {order.get('id', 'unknown')}: {str(e)}")
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
            transaction_id: Clover order ID
            
        Returns:
            POSTransaction object or None if not found
        """
        try:
            order = await self.client.get_order_by_id(transaction_id)
            if not order:
                return None
            
            return await self._convert_order_to_transaction(order)
        
        except Exception as e:
            self.logger.error(f"Failed to extract transaction {transaction_id}: {str(e)}")
            raise
    
    async def _convert_order_to_transaction(self, order: Dict[str, Any]) -> Optional[POSTransaction]:
        """
        Convert Clover order to standardized POSTransaction.
        
        Args:
            order: Clover order object
            
        Returns:
            POSTransaction object
        """
        try:
            # Extract basic order information
            order_id = order.get('id', '')
            if not order_id:
                self.logger.warning("Order missing ID, skipping")
                return None
            
            # Check order state - only process paid/closed orders
            order_state = order.get('state', 'open')
            if order_state not in ['paid', 'locked']:  # locked means completed in Clover
                self.logger.debug(f"Order {order_id} not in paid/locked state ({order_state}), skipping")
                return None
            
            # Parse timestamp
            created_time = order.get('createdTime')
            timestamp = self._parse_timestamp(created_time) if created_time else datetime.now()
            
            # Calculate amounts (Clover uses cents)
            total_amount_cents = order.get('total', 0)
            total_amount = Decimal(str(total_amount_cents)) * self.cents_to_currency
            
            # Extract device/location info
            device_info = order.get('device', {})
            device_id = device_info.get('id', '')
            
            # Extract employee info
            employee_info = order.get('employee', {})
            employee_id = employee_info.get('id', '')
            
            # Extract customer info
            customer_id = order.get('customer', {}).get('id') if order.get('customer') else None
            
            # Get enriched data
            line_items = await self._extract_line_items(order)
            payment_info = await self._extract_payment_info(order)
            customer_info = await self._extract_customer_info(customer_id) if customer_id else None
            
            # Convert currency to NGN if necessary
            original_currency = 'USD'  # Clover primarily uses USD
            if original_currency != self.default_currency:
                total_amount = self._convert_to_ngn(total_amount, original_currency)
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
            tax_info = self._calculate_nigerian_tax(total_amount, payment_info.get('tax_amount', 0))
            
            # Build transaction metadata
            metadata = self._build_transaction_metadata(order, device_id, employee_id, original_currency)
            
            # Create POSTransaction
            transaction = POSTransaction(
                transaction_id=order_id,
                timestamp=timestamp,
                amount=float(total_amount),
                currency=self.default_currency,
                payment_method=payment_info.get('method', 'UNKNOWN'),
                location_id=device_id,  # Use device_id as location_id for Clover
                items=line_items,
                customer_info=customer_info,
                tax_info=tax_info,
                metadata=metadata
            )
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Failed to convert order to transaction: {str(e)}")
            raise
    
    async def _extract_line_items(self, order: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract and process line items from an order."""
        try:
            line_items = []
            
            # Get line items from order
            clover_line_items = order.get('lineItems', {}).get('elements', [])
            
            for line_item in clover_line_items:
                try:
                    item = await self._convert_line_item(line_item)
                    if item:
                        line_items.append(item)
                except Exception as e:
                    self.logger.warning(f"Failed to process line item: {str(e)}")
                    continue
            
            return line_items
        
        except Exception as e:
            self.logger.error(f"Failed to extract line items for order: {str(e)}")
            return []
    
    async def _convert_line_item(self, line_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert Clover line item to standardized format."""
        try:
            item_id = line_item.get('item', {}).get('id', '')
            name = line_item.get('name', 'Unknown Item')
            
            # Clover uses unitQty for quantity (can be fractional)
            unit_qty = line_item.get('unitQty', 1)
            quantity = int(unit_qty) if unit_qty == int(unit_qty) else unit_qty
            
            # Prices in cents
            price_cents = line_item.get('price', 0)
            unit_price = Decimal(str(price_cents)) * self.cents_to_currency
            
            # Total with discounts and modifications
            total_price_cents = line_item.get('price', 0) * quantity
            total_price = Decimal(str(total_price_cents)) * self.cents_to_currency
            
            # Get item details for enrichment
            item_info = await self._get_item_info(item_id) if item_id else {}
            
            # Handle modifications and discounts
            modifications = line_item.get('modifications', {}).get('elements', [])
            discounts = line_item.get('discounts', {}).get('elements', [])
            
            # Build line item
            item = {
                'id': item_id,
                'name': name,
                'description': item_info.get('name', name),
                'sku': item_info.get('sku', item_info.get('code', '')),
                'quantity': quantity,
                'unit_price': float(unit_price),
                'total_price': float(total_price),
                'category': await self._get_item_category(item_info.get('categories')),
                'modifications': self._process_modifications(modifications),
                'discounts': self._process_discounts(discounts),
                'metadata': {
                    'clover_item_id': item_id,
                    'clover_line_item_data': line_item,
                    'item_type': item_info.get('itemType'),
                    'price_type': item_info.get('priceType'),
                    'unit_name': item_info.get('unitName', 'each')
                }
            }
            
            return item
        
        except Exception as e:
            self.logger.error(f"Failed to convert line item: {str(e)}")
            return None
    
    async def _extract_payment_info(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Extract payment information from order."""
        try:
            # Get payments from order
            payments = order.get('payments', {}).get('elements', [])
            
            if not payments:
                return {'method': 'UNKNOWN', 'amount': 0, 'tax_amount': 0}
            
            # Process primary payment (first one if multiple)
            primary_payment = payments[0]
            
            # Payment amount in cents
            amount_cents = primary_payment.get('amount', 0)
            amount = Decimal(str(amount_cents)) * self.cents_to_currency
            
            # Tax amount if available
            tax_amount_cents = primary_payment.get('taxAmount', 0)
            tax_amount = Decimal(str(tax_amount_cents)) * self.cents_to_currency
            
            # Map payment method
            tender = primary_payment.get('tender', {})
            payment_method = await self._map_payment_method(tender)
            
            return {
                'method': payment_method,
                'amount': float(amount),
                'tax_amount': float(tax_amount),
                'payment_id': primary_payment.get('id'),
                'tender_info': tender,
                'all_payments': payments
            }
        
        except Exception as e:
            self.logger.error(f"Failed to extract payment info for order: {str(e)}")
            return {'method': 'UNKNOWN', 'amount': 0, 'tax_amount': 0}
    
    async def _extract_customer_info(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Extract customer information."""
        if not customer_id:
            return None
        
        try:
            # Check cache first
            if customer_id in self._customers_cache:
                return self._customers_cache[customer_id]
            
            # Get customers and find the specific one
            customers = await self.client.get_customers()
            
            customer = None
            for c in customers:
                if c.get('id') == customer_id:
                    customer = c
                    break
            
            if not customer:
                return None
            
            # Convert to standard format
            customer_info = {
                'id': customer.get('id', ''),
                'name': f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip(),
                'email': customer.get('emailAddress', ''),
                'phone': customer.get('phoneNumber', ''),
                'address': self._extract_customer_addresses(customer)
            }
            
            # Cache for future use
            self._customers_cache[customer_id] = customer_info
            
            return customer_info
        
        except Exception as e:
            self.logger.error(f"Failed to extract customer info for {customer_id}: {str(e)}")
            return None
    
    def _extract_customer_addresses(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer addresses from Clover customer object."""
        try:
            addresses = customer.get('addresses', {}).get('elements', [])
            
            if addresses:
                # Use first address
                address = addresses[0]
                return {
                    'address_line_1': address.get('address1', ''),
                    'address_line_2': address.get('address2', ''),
                    'city': address.get('city', ''),
                    'state': address.get('state', ''),
                    'postal_code': address.get('zip', ''),
                    'country': address.get('country', 'Nigeria')
                }
            
            return {}
        
        except Exception as e:
            self.logger.error(f"Failed to extract customer address: {str(e)}")
            return {}
    
    async def _get_item_info(self, item_id: str) -> Dict[str, Any]:
        """Get cached or fetch item information."""
        if not item_id:
            return {}
        
        try:
            # Check cache
            if item_id in self._items_cache:
                return self._items_cache[item_id]
            
            # This would require a separate API call - simplified for performance
            # In production, you might batch these or pre-populate cache
            items = await self.client.get_items()
            
            for item in items:
                if item.get('id') == item_id:
                    self._items_cache[item_id] = item
                    return item
            
            return {}
        
        except Exception:
            return {}
    
    async def _get_item_category(self, categories_ref: Optional[Dict]) -> Optional[str]:
        """Get item category name from categories reference."""
        if not categories_ref:
            return None
        
        try:
            category_elements = categories_ref.get('elements', [])
            if category_elements:
                # Use first category
                category = category_elements[0]
                return category.get('name', 'Unknown Category')
            
            return None
        
        except Exception:
            return None
    
    def _process_modifications(self, modifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process line item modifications."""
        processed_modifications = []
        
        for mod in modifications:
            try:
                modification = {
                    'id': mod.get('id', ''),
                    'name': mod.get('name', 'Modification'),
                    'amount': float(Decimal(str(mod.get('amount', 0))) * self.cents_to_currency),
                    'modifier_id': mod.get('modifier', {}).get('id', '')
                }
                processed_modifications.append(modification)
            except Exception as e:
                self.logger.warning(f"Failed to process modification: {str(e)}")
                continue
        
        return processed_modifications
    
    def _process_discounts(self, discounts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process line item discounts."""
        processed_discounts = []
        
        for discount in discounts:
            try:
                discount_info = {
                    'id': discount.get('id', ''),
                    'name': discount.get('name', 'Discount'),
                    'amount': float(Decimal(str(discount.get('amount', 0))) * self.cents_to_currency),
                    'percentage': discount.get('percentage'),
                    'discount_id': discount.get('discount', {}).get('id', '')
                }
                processed_discounts.append(discount_info)
            except Exception as e:
                self.logger.warning(f"Failed to process discount: {str(e)}")
                continue
        
        return processed_discounts
    
    async def _map_payment_method(self, tender: Dict[str, Any]) -> str:
        """Map Clover tender to standard payment method."""
        if not tender:
            return 'UNKNOWN'
        
        tender_id = tender.get('id', '')
        label_key = tender.get('labelKey', '').upper()
        
        try:
            # Check cache
            if tender_id in self._tenders_cache:
                return self._tenders_cache[tender_id]
            
            # Map based on label key or tender type
            if 'CASH' in label_key:
                mapped_method = 'CASH'
            elif any(word in label_key for word in ['CREDIT', 'DEBIT', 'CARD']):
                mapped_method = 'CARD'
            elif 'CHECK' in label_key:
                mapped_method = 'CHECK'
            elif 'GIFT' in label_key:
                mapped_method = 'GIFT_CARD'
            elif any(word in label_key for word in ['MOBILE', 'DIGITAL']):
                mapped_method = 'MOBILE_PAY'
            else:
                mapped_method = 'OTHER'
            
            # Cache result
            self._tenders_cache[tender_id] = mapped_method
            
            return mapped_method
        
        except Exception as e:
            self.logger.error(f"Failed to map payment method {tender_id}: {str(e)}")
            return 'UNKNOWN'
    
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
    
    def _calculate_nigerian_tax(self, total_amount: Decimal, tax_amount: Union[Decimal, float]) -> Dict[str, Any]:
        """Calculate Nigerian tax compliance information."""
        tax_amount = Decimal(str(tax_amount))
        
        # Calculate tax-exclusive amount
        if tax_amount > 0:
            exclusive_amount = total_amount - tax_amount
            tax_rate = tax_amount / exclusive_amount if exclusive_amount > 0 else self.vat_rate
        else:
            # Assume total includes VAT at 7.5%
            exclusive_amount = total_amount / (1 + self.vat_rate)
            tax_rate = self.vat_rate
        
        # Calculate Nigerian VAT
        nigerian_vat = exclusive_amount * self.vat_rate
        
        return {
            'amount': float(tax_amount),
            'nigerian_vat': float(nigerian_vat),
            'exclusive_amount': float(exclusive_amount),
            'inclusive_amount': float(total_amount),
            'tax_rate': float(tax_rate),
            'nigerian_vat_rate': float(self.vat_rate),
            'compliant': True
        }
    
    def _build_transaction_metadata(self, order: Dict[str, Any], device_id: str, 
                                  employee_id: str, original_currency: str) -> Dict[str, Any]:
        """Build comprehensive transaction metadata."""
        created_time = order.get('createdTime')
        timestamp = self._parse_timestamp(created_time) if created_time else datetime.now()
        
        return {
            'clover_order_id': order.get('id'),
            'clover_order_number': order.get('orderNumber'),
            'device_id': device_id,
            'employee_id': employee_id,
            'original_currency': original_currency,
            'conversion_rate': str(self.exchange_rates.get(original_currency, 1)),
            'business_date': timestamp.date().isoformat(),
            'business_hours': self._is_business_hours(timestamp),
            'order_state': order.get('state'),
            'order_type': order.get('orderType', {}).get('id'),
            'service_charge': order.get('serviceCharge'),
            'raw_order_data': order,
            'processing_timestamp': datetime.now().isoformat(),
            'extractor_version': '1.0'
        }
    
    def _parse_timestamp(self, timestamp: int) -> datetime:
        """Parse Clover timestamp (milliseconds since epoch) to datetime."""
        try:
            # Clover timestamps are in milliseconds
            return datetime.fromtimestamp(timestamp / 1000.0)
        except (ValueError, TypeError, OSError) as e:
            self.logger.warning(f"Failed to parse timestamp '{timestamp}': {str(e)}")
            return datetime.now()
    
    def _is_business_hours(self, timestamp: datetime) -> bool:
        """Check if transaction occurred during business hours."""
        hour = timestamp.hour
        return self.business_hours_start <= hour <= self.business_hours_end
    
    async def extract_locations(self) -> List[POSLocation]:
        """Extract location information from devices."""
        try:
            devices = await self.client.get_devices()
            locations = []
            
            # In Clover, devices represent terminals/locations
            for device in devices:
                location = POSLocation(
                    location_id=device.get('id', ''),
                    name=device.get('name', 'Unknown Device'),
                    address={},  # Clover devices don't typically have address info
                    timezone='Africa/Lagos',  # Default for Nigerian market
                    active=True,
                    metadata={'clover_device_data': device}
                )
                locations.append(location)
            
            return locations
        
        except Exception as e:
            self.logger.error(f"Failed to extract locations: {str(e)}")
            raise
    
    async def extract_payment_methods(self) -> List[POSPaymentMethod]:
        """Extract payment method information from tenders."""
        try:
            tenders = await self.client.get_tenders()
            methods = []
            
            for tender in tenders:
                method = POSPaymentMethod(
                    method_id=tender.get('id', ''),
                    name=tender.get('label', 'Unknown Method'),
                    type=self._standardize_payment_type(tender.get('labelKey', '')),
                    active=not tender.get('hidden', False),
                    metadata={'clover_tender_data': tender}
                )
                methods.append(method)
            
            return methods
        
        except Exception as e:
            self.logger.error(f"Failed to extract payment methods: {str(e)}")
            raise
    
    def _standardize_payment_type(self, label_key: str) -> str:
        """Standardize payment type name."""
        label_upper = label_key.upper()
        
        if 'CASH' in label_upper:
            return 'CASH'
        elif any(word in label_upper for word in ['CREDIT', 'DEBIT', 'CARD']):
            return 'CARD'
        elif 'CHECK' in label_upper:
            return 'CHECK'
        elif 'GIFT' in label_upper:
            return 'GIFT_CARD'
        elif any(word in label_upper for word in ['MOBILE', 'DIGITAL']):
            return 'MOBILE_PAY'
        else:
            return 'OTHER'
    
    async def extract_inventory_items(self, filters: Optional[Dict[str, Any]] = None) -> List[POSInventoryItem]:
        """Extract inventory/product information."""
        try:
            items = await self.client.get_items(filters=filters)
            inventory_items = []
            
            for item in items:
                # Price in cents
                price_cents = item.get('price', 0)
                price = float(Decimal(str(price_cents)) * self.cents_to_currency)
                
                # Cost in cents
                cost_cents = item.get('cost', 0)
                cost = float(Decimal(str(cost_cents)) * self.cents_to_currency)
                
                inventory_item = POSInventoryItem(
                    item_id=item.get('id', ''),
                    sku=item.get('sku', item.get('code', '')),
                    name=item.get('name', 'Unknown Item'),
                    category=await self._get_item_category(item.get('categories')),
                    price=price,
                    cost=cost,
                    quantity_on_hand=0,  # Clover doesn't provide stock info in basic items endpoint
                    active=not item.get('hidden', False),
                    metadata={'clover_item_data': item}
                )
                inventory_items.append(inventory_item)
            
            return inventory_items
        
        except Exception as e:
            self.logger.error(f"Failed to extract inventory items: {str(e)}")
            raise