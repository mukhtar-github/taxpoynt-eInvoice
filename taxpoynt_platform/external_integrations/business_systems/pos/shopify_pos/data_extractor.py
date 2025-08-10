"""
Shopify POS Data Extractor

Handles extraction and transformation of data from Shopify POS system including
orders/transactions, customers, products, and location data.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .rest_client import ShopifyRESTClient
from .exceptions import ShopifyAPIError, ShopifyNotFoundError
from ....connector_framework.base_pos_connector import (
    POSTransaction, POSLocation, POSPaymentMethod, POSInventoryItem
)

logger = logging.getLogger(__name__)


class ShopifyDataExtractor:
    """
    Shopify POS data extraction and transformation - System Integrator Functions.
    
    Handles extraction of:
    - Order/Transaction data (Shopify POS transactions are orders)
    - Location/Store information
    - Customer data
    - Product/Inventory items
    - Payment methods and processing info
    
    Optimized for Nigerian market requirements and FIRS compliance.
    """
    
    def __init__(self, rest_client: ShopifyRESTClient, config: Dict[str, Any]):
        """Initialize Shopify data extractor."""
        self.client = rest_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Nigerian market configuration
        self.default_currency = config.get('currency', 'NGN')
        self.ngn_conversion_rate = Decimal(config.get('ngn_conversion_rate', '800.0'))  # USD to NGN
        self.default_customer_tin = config.get('default_customer_tin', '00000000-0001-0')
        self.vat_rate = Decimal(config.get('vat_rate', '0.075'))  # Nigerian VAT 7.5%
        
        # Shopify-specific configuration
        self.pos_location_ids = config.get('pos_location_ids', [])  # Specific POS locations
        self.include_online_orders = config.get('include_online_orders', False)
        
        # Payment method mapping for Nigerian market
        self.payment_method_mapping = {
            'cash': 'CASH',
            'credit_card': 'CARD',
            'debit_card': 'CARD',
            'gift_card': 'GIFT_CARD',
            'shopify_payments': 'CARD',
            'manual': 'OTHER',
            'bank_transfer': 'TRANSFER',
            'paypal': 'PAYPAL',
            'apple_pay': 'MOBILE_PAY',
            'google_pay': 'MOBILE_PAY',
            'shop_pay': 'SHOP_PAY'
        }
    
    async def extract_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions from Shopify POS (orders).
        
        Args:
            filters: Transaction filters including:
                - location_id: Specific location
                - start_date: Start date for range
                - end_date: End date for range
                - payment_method: Filter by payment method
                - min_amount: Minimum amount
                - max_amount: Maximum amount
                - financial_status: Order financial status
                - fulfillment_status: Order fulfillment status
            limit: Maximum number of transactions
        
        Returns:
            List of extracted POSTransaction objects
        """
        try:
            self.logger.info(f"Extracting Shopify transactions with filters: {filters}")
            
            # Build Shopify API query parameters
            api_params = self._build_order_query_params(filters)
            
            transactions = []
            processed_count = 0
            max_limit = limit or 1000
            
            # Use pagination to get all orders
            while processed_count < max_limit:
                # Calculate batch size
                batch_limit = min(250, max_limit - processed_count)  # Shopify API limit
                api_params['limit'] = batch_limit
                
                # Get orders from Shopify
                orders_response = await self.client.get_orders(**api_params)
                orders = orders_response.get('orders', [])
                
                if not orders:
                    break
                
                # Process each order
                for order in orders:
                    try:
                        # Check if this is a POS order (if filtering for POS only)
                        if not self._is_pos_order(order) and not self.include_online_orders:
                            continue
                        
                        transaction = await self._extract_transaction_from_order(order)
                        if transaction:
                            transactions.append(transaction)
                            processed_count += 1
                            
                            if processed_count >= max_limit:
                                break
                    except Exception as e:
                        self.logger.error(f"Error processing order {order.get('id')}: {str(e)}")
                        continue
                
                # Set up for next page
                if orders and processed_count < max_limit:
                    last_order_id = orders[-1].get('id')
                    api_params['since_id'] = last_order_id
                else:
                    break
            
            self.logger.info(f"Extracted {len(transactions)} transactions from Shopify")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Error extracting transactions: {str(e)}")
            raise
    
    async def extract_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Extract specific transaction by ID (order ID in Shopify).
        
        Args:
            transaction_id: Shopify order ID
        
        Returns:
            POSTransaction object or None if not found
        """
        try:
            order = await self.client.get_order(transaction_id)
            if order:
                return await self._extract_transaction_from_order(order)
            return None
        except ShopifyNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error extracting transaction {transaction_id}: {str(e)}")
            raise
    
    def _build_order_query_params(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build Shopify order query parameters from filters."""
        params = {
            'status': 'any',  # Get all order statuses
            'financial_status': 'paid'  # Only paid orders for POS
        }
        
        if not filters:
            return params
        
        # Date range filters
        if filters.get('start_date'):
            start_date = filters['start_date']
            if isinstance(start_date, datetime):
                start_date = start_date.isoformat()
            params['created_at_min'] = start_date
        
        if filters.get('end_date'):
            end_date = filters['end_date']
            if isinstance(end_date, datetime):
                end_date = end_date.isoformat()
            params['created_at_max'] = end_date
        
        # Financial status filter
        if filters.get('financial_status'):
            params['financial_status'] = filters['financial_status']
        
        # Fulfillment status filter
        if filters.get('fulfillment_status'):
            params['fulfillment_status'] = filters['fulfillment_status']
        
        # Location filter (handled in order processing)
        # Note: Shopify doesn't have a direct location filter in orders API
        
        return params
    
    def _is_pos_order(self, order: Dict[str, Any]) -> bool:
        """Check if an order is from POS."""
        # Check source name
        source_name = order.get('source_name', '').lower()
        if 'pos' in source_name:
            return True
        
        # Check location ID if configured
        location_id = order.get('location_id')
        if self.pos_location_ids and location_id:
            return str(location_id) in [str(loc_id) for loc_id in self.pos_location_ids]
        
        # Check order tags for POS indicators
        tags = order.get('tags', '').lower()
        if 'pos' in tags or 'point-of-sale' in tags:
            return True
        
        # Check if order has POS-specific attributes
        # POS orders typically have immediate fulfillment
        fulfillment_status = order.get('fulfillment_status')
        if fulfillment_status == 'fulfilled':
            # Check if fulfilled quickly (same day as creation)
            created_at = order.get('created_at')
            updated_at = order.get('updated_at')
            if created_at and updated_at:
                try:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                    time_diff = (updated - created).total_seconds()
                    # If fulfilled within 1 hour, likely POS
                    if time_diff < 3600:
                        return True
                except:
                    pass
        
        return False
    
    async def _extract_transaction_from_order(self, order: Dict[str, Any]) -> Optional[POSTransaction]:
        """
        Extract POSTransaction from Shopify order data.
        
        Args:
            order: Shopify order object
        
        Returns:
            POSTransaction object
        """
        try:
            # Extract basic order info
            order_id = str(order.get('id'))
            location_id = order.get('location_id')
            
            # Extract amount
            total_price = Decimal(order.get('total_price', '0'))
            currency = order.get('currency', 'USD')
            
            # Convert to NGN if needed
            if currency != 'NGN':
                amount_ngn = total_price * self.ngn_conversion_rate
                final_currency = 'NGN'
                conversion_rate = float(self.ngn_conversion_rate)
            else:
                amount_ngn = total_price
                final_currency = 'NGN'
                conversion_rate = 1.0
            
            # Extract payment method
            payment_method = self._extract_payment_method(order)
            
            # Extract timestamp
            timestamp_str = order.get('created_at')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.now()
            
            # Extract line items
            items = self._extract_order_items(order, currency, conversion_rate)
            
            # Extract customer information
            customer_info = self._extract_customer_info_from_order(order)
            
            # Calculate tax information
            tax_info = self._calculate_tax_info(amount_ngn, order)
            
            # Build metadata
            metadata = {
                'original_currency': currency,
                'original_amount': float(total_price),
                'conversion_rate': conversion_rate,
                'shopify_order_id': order_id,
                'order_number': order.get('order_number'),
                'source_name': order.get('source_name'),
                'financial_status': order.get('financial_status'),
                'fulfillment_status': order.get('fulfillment_status'),
                'total_discounts': order.get('total_discounts'),
                'total_tax': order.get('total_tax'),
                'subtotal_price': order.get('subtotal_price'),
                'tags': order.get('tags'),
                'note': order.get('note'),
                'processing_method': order.get('processing_method'),
                'checkout_token': order.get('checkout_token'),
                'gateway': order.get('gateway'),
                'is_pos_order': self._is_pos_order(order)
            }
            
            # Add shipping information if available
            shipping_address = order.get('shipping_address')
            if shipping_address:
                metadata['shipping_address'] = shipping_address
            
            # Add billing information if available
            billing_address = order.get('billing_address')
            if billing_address:
                metadata['billing_address'] = billing_address
            
            # Build POSTransaction
            transaction = POSTransaction(
                transaction_id=order_id,
                location_id=str(location_id) if location_id else None,
                amount=float(amount_ngn),
                currency=final_currency,
                payment_method=payment_method,
                timestamp=timestamp,
                items=items,
                customer_info=customer_info,
                tax_info=tax_info,
                metadata=metadata,
                tin_number=self.default_customer_tin
            )
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Error extracting transaction from order: {str(e)}")
            return None
    
    def _extract_payment_method(self, order: Dict[str, Any]) -> str:
        """Extract and normalize payment method from Shopify order."""
        # Check gateway
        gateway = order.get('gateway', '').lower()
        if gateway:
            mapped_method = self.payment_method_mapping.get(gateway, 'OTHER')
            if mapped_method != 'OTHER':
                return mapped_method
        
        # Check processing method
        processing_method = order.get('processing_method', '').lower()
        if processing_method:
            mapped_method = self.payment_method_mapping.get(processing_method, 'OTHER')
            if mapped_method != 'OTHER':
                return mapped_method
        
        # Check payment details in transactions
        payment_details = order.get('payment_details', {})
        if payment_details:
            credit_card_number = payment_details.get('credit_card_number')
            if credit_card_number:
                return 'CARD'
            
            avs_result_code = payment_details.get('avs_result_code')
            cvv_result_code = payment_details.get('cvv_result_code')
            if avs_result_code or cvv_result_code:
                return 'CARD'
        
        # Check if cash on delivery or manual payment
        if order.get('financial_status') == 'pending':
            return 'CASH'
        
        # Default to OTHER if cannot determine
        return 'OTHER'
    
    def _extract_order_items(
        self, 
        order: Dict[str, Any], 
        original_currency: str, 
        conversion_rate: float
    ) -> List[Dict[str, Any]]:
        """Extract items from Shopify order."""
        items = []
        
        for line_item in order.get('line_items', []):
            # Extract item details
            quantity = int(line_item.get('quantity', 1))
            name = line_item.get('name', 'Unknown Item')
            title = line_item.get('title', name)
            
            # Extract pricing
            price = Decimal(line_item.get('price', '0'))
            total_price = price * quantity
            
            # Convert to NGN if needed
            if original_currency != 'NGN':
                unit_price_ngn = price * Decimal(str(conversion_rate))
                total_price_ngn = total_price * Decimal(str(conversion_rate))
            else:
                unit_price_ngn = price
                total_price_ngn = total_price
            
            # Extract product information
            product_id = line_item.get('product_id')
            variant_id = line_item.get('variant_id')
            sku = line_item.get('sku')
            
            # Extract tax information
            tax_lines = line_item.get('tax_lines', [])
            item_taxes = []
            for tax_line in tax_lines:
                tax_info = {
                    'title': tax_line.get('title', 'Tax'),
                    'rate': float(tax_line.get('rate', 0)),
                    'price': float(Decimal(tax_line.get('price', '0')) * Decimal(str(conversion_rate)))
                }
                item_taxes.append(tax_info)
            
            # Extract properties/customizations
            properties = line_item.get('properties', [])
            customizations = []
            for prop in properties:
                if isinstance(prop, dict):
                    customizations.append({
                        'name': prop.get('name', ''),
                        'value': prop.get('value', '')
                    })
            
            item = {
                'id': str(variant_id) if variant_id else str(product_id) if product_id else f"item_{len(items) + 1}",
                'name': title,
                'quantity': quantity,
                'unit_price': float(unit_price_ngn),
                'total_price': float(total_price_ngn),
                'currency': 'NGN',
                'sku': sku,
                'category': line_item.get('vendor'),  # Use vendor as category
                'taxes': item_taxes,
                'customizations': customizations,
                'metadata': {
                    'shopify_product_id': product_id,
                    'shopify_variant_id': variant_id,
                    'variant_title': line_item.get('variant_title'),
                    'vendor': line_item.get('vendor'),
                    'product_type': line_item.get('product_type'),
                    'fulfillment_service': line_item.get('fulfillment_service'),
                    'fulfillable_quantity': line_item.get('fulfillable_quantity'),
                    'grams': line_item.get('grams'),
                    'requires_shipping': line_item.get('requires_shipping'),
                    'taxable': line_item.get('taxable'),
                    'original_currency': original_currency,
                    'conversion_rate': conversion_rate
                }
            }
            
            items.append(item)
        
        return items
    
    def _extract_customer_info_from_order(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract customer information from Shopify order."""
        customer = order.get('customer')
        
        if customer:
            # Extract customer details
            first_name = customer.get('first_name', '')
            last_name = customer.get('last_name', '')
            email = customer.get('email')
            phone = customer.get('phone')
            
            name = f"{first_name} {last_name}".strip()
            if not name:
                name = email or 'Unknown Customer'
            
            # Extract address (prefer billing, fallback to shipping)
            billing_address = order.get('billing_address') or order.get('shipping_address')
            address = {}
            
            if billing_address:
                address = {
                    'first_name': billing_address.get('first_name', ''),
                    'last_name': billing_address.get('last_name', ''),
                    'company': billing_address.get('company', ''),
                    'address1': billing_address.get('address1', ''),
                    'address2': billing_address.get('address2', ''),
                    'city': billing_address.get('city', ''),
                    'province': billing_address.get('province', ''),
                    'country': billing_address.get('country', 'NG'),
                    'zip': billing_address.get('zip', ''),
                    'phone': billing_address.get('phone', '')
                }
            
            return {
                'id': str(customer.get('id')),
                'name': name,
                'type': 'individual',
                'email': email,
                'phone': phone,
                'tin': self.default_customer_tin,
                'address': address,
                'created_at': customer.get('created_at'),
                'updated_at': customer.get('updated_at'),
                'orders_count': customer.get('orders_count', 0),
                'total_spent': customer.get('total_spent', '0'),
                'verified_email': customer.get('verified_email', False),
                'tax_exempt': customer.get('tax_exempt', False)
            }
        else:
            # Return default retail customer info for Nigerian compliance
            return {
                'name': 'Retail Customer',
                'type': 'individual',
                'tin': self.default_customer_tin,
                'address': {
                    'country': 'NG',
                    'province': 'Lagos',
                    'city': 'Lagos'
                }
            }
    
    def _calculate_tax_info(self, amount: Decimal, order: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate Nigerian tax information for the transaction."""
        # Get tax information from Shopify order
        total_tax = Decimal(order.get('total_tax', '0'))
        tax_lines = order.get('tax_lines', [])
        
        # Convert tax to NGN if needed
        original_currency = order.get('currency', 'USD')
        if original_currency != 'NGN':
            total_tax_ngn = total_tax * self.ngn_conversion_rate
        else:
            total_tax_ngn = total_tax
        
        # If no tax from Shopify, calculate Nigerian VAT
        if total_tax_ngn == 0:
            vat_inclusive_amount = amount
            vat_exclusive_amount = vat_inclusive_amount / (1 + self.vat_rate)
            vat_amount = vat_inclusive_amount - vat_exclusive_amount
        else:
            vat_amount = total_tax_ngn
            vat_inclusive_amount = amount
            vat_exclusive_amount = vat_inclusive_amount - vat_amount
        
        # Build tax breakdown
        tax_breakdown = []
        for tax_line in tax_lines:
            tax_amount = Decimal(tax_line.get('price', '0'))
            if original_currency != 'NGN':
                tax_amount *= self.ngn_conversion_rate
            
            tax_breakdown.append({
                'title': tax_line.get('title', 'Tax'),
                'rate': float(tax_line.get('rate', self.vat_rate)),
                'amount': float(tax_amount)
            })
        
        if not tax_breakdown:
            tax_breakdown.append({
                'title': 'Nigerian VAT',
                'rate': float(self.vat_rate),
                'amount': float(vat_amount)
            })
        
        return {
            'rate': float(self.vat_rate),
            'amount': float(vat_amount),
            'type': 'VAT',
            'description': 'Nigerian Value Added Tax',
            'exclusive_amount': float(vat_exclusive_amount),
            'inclusive_amount': float(vat_inclusive_amount),
            'breakdown': tax_breakdown
        }
    
    async def extract_locations(self) -> List[POSLocation]:
        """
        Extract locations from Shopify.
        
        Returns:
            List of POSLocation objects
        """
        try:
            locations_response = await self.client.get_locations()
            locations_data = locations_response.get('locations', [])
            
            locations = []
            for location in locations_data:
                pos_location = POSLocation(
                    location_id=str(location.get('id')),
                    name=location.get('name', 'Unknown Location'),
                    address=self._extract_location_address(location),
                    timezone=location.get('timezone', 'Africa/Lagos'),
                    currency=self.default_currency,
                    tax_settings={
                        'vat_rate': float(self.vat_rate),
                        'tax_included': True,
                        'tax_type': 'VAT'
                    },
                    metadata={
                        'shopify_location_id': location.get('id'),
                        'active': location.get('active', True),
                        'legacy': location.get('legacy', False),
                        'phone': location.get('phone'),
                        'zip': location.get('zip'),
                        'city': location.get('city'),
                        'address1': location.get('address1'),
                        'address2': location.get('address2'),
                        'country_code': location.get('country_code'),
                        'country_name': location.get('country_name'),
                        'province_code': location.get('province_code'),
                        'province': location.get('province'),
                        'created_at': location.get('created_at'),
                        'updated_at': location.get('updated_at')
                    }
                )
                locations.append(pos_location)
            
            self.logger.info(f"Extracted {len(locations)} locations from Shopify")
            return locations
        
        except Exception as e:
            self.logger.error(f"Error extracting locations: {str(e)}")
            raise
    
    def _extract_location_address(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Extract address from Shopify location."""
        return {
            'address_line_1': location.get('address1', ''),
            'address_line_2': location.get('address2', ''),
            'city': location.get('city', ''),
            'province': location.get('province', ''),
            'postal_code': location.get('zip', ''),
            'country': location.get('country_name', 'Nigeria'),
            'country_code': location.get('country_code', 'NG')
        }
    
    async def extract_payment_methods(self) -> List[POSPaymentMethod]:
        """
        Extract available payment methods for Shopify POS.
        
        Returns:
            List of POSPaymentMethod objects
        """
        # Shopify POS supports various payment methods
        # These are based on typical Shopify POS capabilities
        
        payment_methods = [
            POSPaymentMethod(
                method_id='shopify_card',
                name='Credit/Debit Card',
                type='CARD',
                provider='SHOPIFY_PAYMENTS',
                fees={'processing_fee': '2.9% + ₦30'},
                processing_time='Instant',
                limits={
                    'min_amount': 100.0,  # ₦1.00
                    'max_amount': 10000000.0  # ₦100,000
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='shopify_cash',
                name='Cash Payment',
                type='CASH',
                provider='SHOPIFY_POS',
                fees={'processing_fee': '0%'},
                processing_time='Instant',
                limits={
                    'min_amount': 0.0,
                    'max_amount': 100000000.0  # ₦1,000,000
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='shopify_gift_card',
                name='Gift Card',
                type='GIFT_CARD',
                provider='SHOPIFY',
                fees={'processing_fee': '0%'},
                processing_time='Instant',
                limits={
                    'min_amount': 100.0,
                    'max_amount': 5000000.0  # ₦50,000
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='shop_pay',
                name='Shop Pay',
                type='MOBILE_PAY',
                provider='SHOPIFY',
                fees={'processing_fee': '2.9% + ₦30'},
                processing_time='Instant',
                limits={
                    'min_amount': 100.0,
                    'max_amount': 10000000.0
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='manual_payment',
                name='Manual Payment',
                type='OTHER',
                provider='SHOPIFY_POS',
                fees={'processing_fee': '0%'},
                processing_time='Manual',
                limits={
                    'min_amount': 0.0,
                    'max_amount': 100000000.0
                },
                enabled=True,
                nigerian_compliant=True
            )
        ]
        
        return payment_methods
    
    async def extract_inventory_items(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[POSInventoryItem]:
        """
        Extract inventory items from Shopify products.
        
        Args:
            filters: Inventory filters
            limit: Maximum number of items
        
        Returns:
            List of POSInventoryItem objects
        """
        try:
            # Build product query parameters
            api_params = {}
            
            if filters:
                if filters.get('vendor'):
                    api_params['vendor'] = filters['vendor']
                if filters.get('product_type'):
                    api_params['product_type'] = filters['product_type']
                if filters.get('collection_id'):
                    api_params['collection_id'] = filters['collection_id']
            
            items = []
            processed_count = 0
            max_limit = limit or 1000
            
            # Use pagination to get all products
            while processed_count < max_limit:
                batch_limit = min(250, max_limit - processed_count)
                api_params['limit'] = batch_limit
                
                products_response = await self.client.get_products(**api_params)
                products = products_response.get('products', [])
                
                if not products:
                    break
                
                for product in products:
                    try:
                        product_items = self._extract_inventory_items_from_product(product)
                        for item in product_items:
                            items.append(item)
                            processed_count += 1
                            
                            if processed_count >= max_limit:
                                break
                        
                        if processed_count >= max_limit:
                            break
                    except Exception as e:
                        self.logger.error(f"Error processing product {product.get('id')}: {str(e)}")
                        continue
                
                # Set up for next page
                if products and processed_count < max_limit:
                    last_product_id = products[-1].get('id')
                    api_params['since_id'] = last_product_id
                else:
                    break
            
            self.logger.info(f"Extracted {len(items)} inventory items from Shopify")
            return items
        
        except Exception as e:
            self.logger.error(f"Error extracting inventory items: {str(e)}")
            raise
    
    def _extract_inventory_items_from_product(self, product: Dict[str, Any]) -> List[POSInventoryItem]:
        """Extract POSInventoryItem objects from Shopify product."""
        items = []
        
        try:
            # Product-level information
            product_id = product.get('id')
            product_title = product.get('title', 'Unknown Product')
            product_type = product.get('product_type', '')
            vendor = product.get('vendor', '')
            
            # Process each variant
            variants = product.get('variants', [])
            for variant in variants:
                variant_id = variant.get('id')
                variant_title = variant.get('title', '')
                
                # Build item name
                if variant_title and variant_title != 'Default Title':
                    item_name = f"{product_title} - {variant_title}"
                else:
                    item_name = product_title
                
                # Extract pricing
                price = Decimal(variant.get('price', '0'))
                compare_at_price = variant.get('compare_at_price')
                
                # Convert to NGN if needed
                # Note: Shopify stores prices in shop currency
                currency = 'NGN'  # Assume NGN for Nigerian shops
                if currency != 'NGN':
                    price *= self.ngn_conversion_rate
                
                # Extract inventory information
                inventory_quantity = variant.get('inventory_quantity', 0)
                inventory_management = variant.get('inventory_management')
                
                item = POSInventoryItem(
                    item_id=str(variant_id),
                    sku=variant.get('sku'),
                    name=item_name,
                    category=product_type or vendor,
                    price=float(price),
                    currency='NGN',
                    stock_quantity=inventory_quantity if inventory_management else None,
                    tax_rate=float(self.vat_rate),
                    metadata={
                        'shopify_product_id': product_id,
                        'shopify_variant_id': variant_id,
                        'product_title': product_title,
                        'variant_title': variant_title,
                        'vendor': vendor,
                        'product_type': product_type,
                        'compare_at_price': float(Decimal(compare_at_price)) if compare_at_price else None,
                        'weight': variant.get('weight'),
                        'weight_unit': variant.get('weight_unit'),
                        'inventory_management': inventory_management,
                        'inventory_policy': variant.get('inventory_policy'),
                        'fulfillment_service': variant.get('fulfillment_service'),
                        'requires_shipping': variant.get('requires_shipping'),
                        'taxable': variant.get('taxable'),
                        'barcode': variant.get('barcode'),
                        'image_id': variant.get('image_id'),
                        'created_at': variant.get('created_at'),
                        'updated_at': variant.get('updated_at')
                    }
                )
                
                items.append(item)
        
        except Exception as e:
            self.logger.error(f"Error extracting inventory items from product: {str(e)}")
        
        return items