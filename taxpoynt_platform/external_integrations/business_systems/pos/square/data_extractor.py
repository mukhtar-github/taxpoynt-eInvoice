"""
Square POS Data Extractor

Handles extraction and transformation of data from Square POS system including
transactions, orders, customers, inventory, and location data.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from .rest_client import SquareRESTClient
from .exceptions import SquareAPIError, SquareNotFoundError
from ....connector_framework.base_pos_connector import (
    POSTransaction, POSLocation, POSPaymentMethod, POSInventoryItem
)

logger = logging.getLogger(__name__)


class SquareDataExtractor:
    """
    Square POS data extraction and transformation - System Integrator Functions.
    
    Handles extraction of:
    - Transaction/Payment data with order details
    - Location/Store information
    - Customer data
    - Inventory/Catalog items
    - Payment methods and processing info
    
    Optimized for Nigerian market requirements and FIRS compliance.
    """
    
    def __init__(self, rest_client: SquareRESTClient, config: Dict[str, Any]):
        """Initialize Square data extractor."""
        self.client = rest_client
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Nigerian market configuration
        self.default_currency = config.get('currency', 'NGN')
        self.ngn_conversion_rate = Decimal(config.get('ngn_conversion_rate', '800.0'))  # USD to NGN
        self.default_customer_tin = config.get('default_customer_tin', '00000000-0001-0')
        self.vat_rate = Decimal(config.get('vat_rate', '0.075'))  # Nigerian VAT 7.5%
        
        # Payment method mapping for Nigerian market
        self.payment_method_mapping = {
            'CARD': 'CARD',
            'CASH': 'CASH',
            'BANK_ACCOUNT': 'TRANSFER',
            'WALLET': 'MOBILE_MONEY',
            'BUY_NOW_PAY_LATER': 'BNPL',
            'EXTERNAL': 'OTHER',
            'GIFT_CARD': 'GIFT_CARD'
        }
    
    async def extract_transactions(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions from Square POS.
        
        Args:
            filters: Transaction filters including:
                - location_id: Specific location
                - start_date: Start date for range
                - end_date: End date for range
                - payment_method: Filter by payment method
                - min_amount: Minimum amount
                - max_amount: Maximum amount
            limit: Maximum number of transactions
        
        Returns:
            List of extracted POSTransaction objects
        """
        try:
            self.logger.info(f"Extracting Square transactions with filters: {filters}")
            
            # Build Square API query
            query = self._build_payment_search_query(filters)
            
            transactions = []
            cursor = None
            extracted_count = 0
            max_limit = limit or 1000
            
            while extracted_count < max_limit:
                # Calculate batch size
                batch_limit = min(500, max_limit - extracted_count)  # Square API limit
                
                # Search payments
                search_result = await self.client.search_payments(
                    query=query,
                    cursor=cursor,
                    limit=batch_limit
                )
                
                payments = search_result.get('payments', [])
                if not payments:
                    break
                
                # Process each payment
                for payment in payments:
                    try:
                        transaction = await self._extract_transaction_from_payment(payment)
                        if transaction:
                            transactions.append(transaction)
                            extracted_count += 1
                            
                            if extracted_count >= max_limit:
                                break
                    except Exception as e:
                        self.logger.error(f"Error processing payment {payment.get('id')}: {str(e)}")
                        continue
                
                # Check for more results
                cursor = search_result.get('cursor')
                if not cursor or extracted_count >= max_limit:
                    break
            
            self.logger.info(f"Extracted {len(transactions)} transactions from Square")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Error extracting transactions: {str(e)}")
            raise
    
    async def extract_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Extract specific transaction by ID.
        
        Args:
            transaction_id: Square payment ID
        
        Returns:
            POSTransaction object or None if not found
        """
        try:
            payment = await self.client.get_payment(transaction_id)
            if payment:
                return await self._extract_transaction_from_payment(payment)
            return None
        except SquareNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error extracting transaction {transaction_id}: {str(e)}")
            raise
    
    async def _extract_transaction_from_payment(self, payment: Dict[str, Any]) -> Optional[POSTransaction]:
        """
        Extract POSTransaction from Square payment data.
        
        Args:
            payment: Square payment object
        
        Returns:
            POSTransaction object
        """
        try:
            # Extract basic payment info
            payment_id = payment.get('id')
            location_id = payment.get('location_id')
            
            # Extract amount (Square amounts are in cents)
            amount_money = payment.get('amount_money', {})
            amount = Decimal(amount_money.get('amount', 0)) / 100
            original_currency = amount_money.get('currency', 'USD')
            
            # Convert to NGN if needed
            if original_currency != 'NGN':
                amount_ngn = amount * self.ngn_conversion_rate
                currency = 'NGN'
                conversion_rate = float(self.ngn_conversion_rate)
            else:
                amount_ngn = amount
                currency = 'NGN'
                conversion_rate = 1.0
            
            # Extract payment method
            payment_method = self._extract_payment_method(payment)
            
            # Extract timestamp
            timestamp_str = payment.get('created_at')
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00')) if timestamp_str else datetime.now()
            
            # Extract order information if available
            order_id = payment.get('order_id')
            items = []
            customer_info = None
            
            if order_id:
                try:
                    order_data = await self.client.get_order(order_id)
                    if order_data:
                        items = self._extract_order_items(order_data, original_currency, conversion_rate)
                        customer_info = self._extract_customer_info_from_order(order_data)
                except Exception as e:
                    self.logger.warning(f"Could not extract order data for {order_id}: {str(e)}")
            
            # Calculate tax information
            tax_info = self._calculate_tax_info(amount_ngn, items)
            
            # Build metadata
            metadata = {
                'original_currency': original_currency,
                'original_amount': float(amount),
                'conversion_rate': conversion_rate,
                'square_payment_id': payment_id,
                'status': payment.get('status'),
                'source_type': payment.get('source_type'),
                'risk_evaluation': payment.get('risk_evaluation', {}),
                'processing_fee': self._extract_processing_fee(payment),
                'receipt_number': payment.get('receipt_number'),
                'receipt_url': payment.get('receipt_url')
            }
            
            # Add card details if available
            card_details = payment.get('card_details')
            if card_details:
                metadata['card_details'] = {
                    'status': card_details.get('status'),
                    'card_brand': card_details.get('card', {}).get('card_brand'),
                    'last_4': card_details.get('card', {}).get('last_4'),
                    'entry_method': card_details.get('entry_method'),
                    'cvv_status': card_details.get('cvv_status'),
                    'avs_status': card_details.get('avs_status')
                }
            
            # Build POSTransaction
            transaction = POSTransaction(
                transaction_id=payment_id,
                location_id=location_id,
                amount=float(amount_ngn),
                currency=currency,
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
            self.logger.error(f"Error extracting transaction from payment: {str(e)}")
            return None
    
    def _build_payment_search_query(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build Square payment search query from filters."""
        query = {}
        
        if not filters:
            return query
        
        # Location filter
        if filters.get('location_id'):
            query['filter'] = query.get('filter', {})
            query['filter']['location_ids'] = [filters['location_id']]
        
        # Date range filter
        if filters.get('start_date') or filters.get('end_date'):
            query['filter'] = query.get('filter', {})
            query['filter']['created_at'] = {}
            
            if filters.get('start_date'):
                start_date = filters['start_date']
                if isinstance(start_date, datetime):
                    start_date = start_date.isoformat()
                query['filter']['created_at']['start_at'] = start_date
            
            if filters.get('end_date'):
                end_date = filters['end_date']
                if isinstance(end_date, datetime):
                    end_date = end_date.isoformat()
                query['filter']['created_at']['end_at'] = end_date
        
        # Amount range filter
        if filters.get('min_amount') or filters.get('max_amount'):
            query['filter'] = query.get('filter', {})
            query['filter']['total'] = {}
            
            if filters.get('min_amount'):
                # Convert to cents
                min_amount_cents = int(float(filters['min_amount']) * 100)
                query['filter']['total']['min'] = min_amount_cents
            
            if filters.get('max_amount'):
                # Convert to cents
                max_amount_cents = int(float(filters['max_amount']) * 100)
                query['filter']['total']['max'] = max_amount_cents
        
        # Payment method filter (Square uses source_type)
        if filters.get('payment_method'):
            query['filter'] = query.get('filter', {})
            # Map our payment method to Square source type
            source_type_mapping = {v: k for k, v in self.payment_method_mapping.items()}
            source_type = source_type_mapping.get(filters['payment_method'])
            if source_type:
                query['filter']['source_type'] = source_type
        
        # Sort order (default to newest first)
        query['sort'] = {'order': 'DESC'}
        
        return query
    
    def _extract_payment_method(self, payment: Dict[str, Any]) -> str:
        """Extract and normalize payment method from Square payment."""
        source_type = payment.get('source_type', '').upper()
        
        # Map Square payment methods to standardized format
        base_method = self.payment_method_mapping.get(source_type, 'OTHER')
        
        # For card payments, get more specific information
        if source_type == 'CARD':
            card_details = payment.get('card_details', {})
            card_brand = card_details.get('card', {}).get('card_brand', '')
            if card_brand:
                return f"CARD_{card_brand}"
        
        return base_method
    
    def _extract_order_items(
        self, 
        order: Dict[str, Any], 
        original_currency: str, 
        conversion_rate: float
    ) -> List[Dict[str, Any]]:
        """Extract items from Square order."""
        items = []
        
        for line_item in order.get('line_items', []):
            # Extract item details
            quantity = int(line_item.get('quantity', '1'))
            name = line_item.get('name', 'Unknown Item')
            
            # Extract pricing (amounts in cents)
            base_price_money = line_item.get('base_price_money', {})
            base_price = Decimal(base_price_money.get('amount', 0)) / 100
            
            total_money = line_item.get('total_money', {})
            total_price = Decimal(total_money.get('amount', 0)) / 100
            
            # Convert to NGN if needed
            if original_currency != 'NGN':
                base_price *= Decimal(str(conversion_rate))
                total_price *= Decimal(str(conversion_rate))
            
            # Extract variations and modifiers
            variation_name = line_item.get('variation_name')
            modifiers = []
            for modifier in line_item.get('modifiers', []):
                modifier_info = {
                    'name': modifier.get('name', ''),
                    'base_price': float(Decimal(modifier.get('base_price_money', {}).get('amount', 0)) / 100 * Decimal(str(conversion_rate))),
                    'total_price': float(Decimal(modifier.get('total_price_money', {}).get('amount', 0)) / 100 * Decimal(str(conversion_rate)))
                }
                modifiers.append(modifier_info)
            
            # Extract taxes
            taxes = []
            for tax in line_item.get('applied_taxes', []):
                tax_info = {
                    'name': tax.get('tax_name', 'Tax'),
                    'rate': tax.get('percentage', '0'),
                    'amount': float(Decimal(tax.get('applied_money', {}).get('amount', 0)) / 100 * Decimal(str(conversion_rate)))
                }
                taxes.append(tax_info)
            
            item = {
                'id': line_item.get('uid'),
                'name': name,
                'quantity': quantity,
                'unit_price': float(base_price),
                'total_price': float(total_price),
                'currency': 'NGN',
                'sku': line_item.get('catalog_object_id'),
                'category': variation_name,
                'modifiers': modifiers,
                'taxes': taxes,
                'metadata': {
                    'square_item_id': line_item.get('catalog_object_id'),
                    'variation_id': line_item.get('catalog_version'),
                    'original_currency': original_currency,
                    'conversion_rate': conversion_rate
                }
            }
            
            items.append(item)
        
        return items
    
    def _extract_customer_info_from_order(self, order: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract customer information from Square order."""
        # Check if order has customer ID
        customer_id = order.get('customer_id')
        
        if customer_id:
            try:
                # Fetch customer details
                customer = self.client.get_customer(customer_id)
                if customer:
                    return self._extract_customer_data(customer)
            except Exception as e:
                self.logger.warning(f"Could not fetch customer {customer_id}: {str(e)}")
        
        # Return default retail customer info for Nigerian compliance
        return {
            'name': 'Retail Customer',
            'type': 'individual',
            'tin': self.default_customer_tin,
            'address': {
                'country': 'NG',
                'state': 'Lagos',
                'city': 'Lagos'
            }
        }
    
    def _extract_customer_data(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Extract customer data from Square customer object."""
        given_name = customer.get('given_name', '')
        family_name = customer.get('family_name', '')
        company_name = customer.get('company_name', '')
        
        # Determine name and type
        if company_name:
            name = company_name
            customer_type = 'business'
        else:
            name = f"{given_name} {family_name}".strip() or 'Unknown Customer'
            customer_type = 'individual'
        
        # Extract address
        address = {}
        addresses = customer.get('addresses', [])
        if addresses:
            primary_address = addresses[0]
            address = {
                'address_line_1': primary_address.get('address_line_1', ''),
                'address_line_2': primary_address.get('address_line_2', ''),
                'locality': primary_address.get('locality', ''),
                'administrative_district_level_1': primary_address.get('administrative_district_level_1', ''),
                'postal_code': primary_address.get('postal_code', ''),
                'country': primary_address.get('country', 'NG')
            }
        else:
            address = {
                'country': 'NG',
                'state': 'Lagos',
                'city': 'Lagos'
            }
        
        return {
            'id': customer.get('id'),
            'name': name,
            'type': customer_type,
            'email': customer.get('email_address'),
            'phone': customer.get('phone_number'),
            'tin': self.default_customer_tin,  # Use default TIN for retail customers
            'address': address,
            'created_at': customer.get('created_at'),
            'updated_at': customer.get('updated_at')
        }
    
    def _calculate_tax_info(self, amount: Decimal, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate Nigerian tax information for the transaction."""
        # Nigerian VAT rate: 7.5%
        vat_rate = self.vat_rate
        
        # Calculate VAT-exclusive amount
        vat_inclusive_amount = amount
        vat_exclusive_amount = vat_inclusive_amount / (1 + vat_rate)
        vat_amount = vat_inclusive_amount - vat_exclusive_amount
        
        return {
            'rate': float(vat_rate),
            'amount': float(vat_amount),
            'type': 'VAT',
            'description': 'Nigerian Value Added Tax',
            'exclusive_amount': float(vat_exclusive_amount),
            'inclusive_amount': float(vat_inclusive_amount),
            'breakdown': self._calculate_item_tax_breakdown(items)
        }
    
    def _calculate_item_tax_breakdown(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate tax breakdown per item."""
        breakdown = []
        
        for item in items:
            item_taxes = item.get('taxes', [])
            if item_taxes:
                # Use actual tax data from Square
                for tax in item_taxes:
                    breakdown.append({
                        'item_id': item.get('id'),
                        'item_name': item.get('name'),
                        'tax_name': tax.get('name'),
                        'tax_rate': float(tax.get('rate', '0')),
                        'tax_amount': tax.get('amount', 0)
                    })
            else:
                # Calculate default VAT
                item_total = item.get('total_price', 0)
                vat_amount = item_total * float(self.vat_rate) / (1 + float(self.vat_rate))
                
                breakdown.append({
                    'item_id': item.get('id'),
                    'item_name': item.get('name'),
                    'tax_name': 'Nigerian VAT',
                    'tax_rate': float(self.vat_rate),
                    'tax_amount': vat_amount
                })
        
        return breakdown
    
    def _extract_processing_fee(self, payment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract processing fee information."""
        processing_fee = payment.get('processing_fee')
        if processing_fee:
            fee_money = processing_fee.get('amount_money', {})
            fee_amount = Decimal(fee_money.get('amount', 0)) / 100
            
            return {
                'amount': float(fee_amount),
                'currency': fee_money.get('currency', 'USD'),
                'effective_at': processing_fee.get('effective_at')
            }
        return None
    
    async def extract_locations(self) -> List[POSLocation]:
        """
        Extract locations from Square.
        
        Returns:
            List of POSLocation objects
        """
        try:
            locations_data = await self.client.get_locations()
            
            locations = []
            for location in locations_data:
                pos_location = POSLocation(
                    location_id=location.get('id'),
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
                        'square_location_id': location.get('id'),
                        'status': location.get('status'),
                        'type': location.get('type'),
                        'phone_number': location.get('phone_number'),
                        'website_url': location.get('website_url'),
                        'business_name': location.get('business_name'),
                        'business_email': location.get('business_email'),
                        'capabilities': location.get('capabilities', [])
                    }
                )
                locations.append(pos_location)
            
            self.logger.info(f"Extracted {len(locations)} locations from Square")
            return locations
        
        except Exception as e:
            self.logger.error(f"Error extracting locations: {str(e)}")
            raise
    
    def _extract_location_address(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Extract address from Square location."""
        address_data = location.get('address', {})
        
        return {
            'address_line_1': address_data.get('address_line_1', ''),
            'address_line_2': address_data.get('address_line_2', ''),
            'locality': address_data.get('locality', ''),
            'administrative_district_level_1': address_data.get('administrative_district_level_1', ''),
            'postal_code': address_data.get('postal_code', ''),
            'country': address_data.get('country', 'NG')
        }
    
    async def extract_payment_methods(self) -> List[POSPaymentMethod]:
        """
        Extract available payment methods for Square.
        
        Returns:
            List of POSPaymentMethod objects
        """
        # Square payment methods are fairly standard
        # We'll return the supported methods based on Square's capabilities
        
        payment_methods = [
            POSPaymentMethod(
                method_id='square_card',
                name='Credit/Debit Card',
                type='CARD',
                provider='SQUARE',
                fees={'processing_fee': '2.6% + ₦30'},
                processing_time='Instant',
                limits={
                    'min_amount': 100.0,  # ₦1.00
                    'max_amount': 5000000.0  # ₦50,000
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='square_cash',
                name='Cash Payment',
                type='CASH',
                provider='SQUARE',
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
                method_id='square_gift_card',
                name='Gift Card',
                type='GIFT_CARD',
                provider='SQUARE',
                fees={'processing_fee': '0%'},
                processing_time='Instant',
                limits={
                    'min_amount': 100.0,
                    'max_amount': 1000000.0  # ₦10,000
                },
                enabled=True,
                nigerian_compliant=True
            ),
            POSPaymentMethod(
                method_id='square_ach',
                name='Bank Transfer (ACH)',
                type='TRANSFER',
                provider='SQUARE',
                fees={'processing_fee': '1% + ₦15'},
                processing_time='1-3 business days',
                limits={
                    'min_amount': 100.0,
                    'max_amount': 25000000.0  # ₦250,000
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
        Extract inventory items from Square catalog.
        
        Args:
            filters: Inventory filters
            limit: Maximum number of items
        
        Returns:
            List of POSInventoryItem objects
        """
        try:
            # Build catalog search query
            query = self._build_catalog_search_query(filters)
            
            items = []
            cursor = None
            extracted_count = 0
            max_limit = limit or 1000
            
            while extracted_count < max_limit:
                batch_limit = min(1000, max_limit - extracted_count)
                
                search_result = await self.client.search_catalog_objects(
                    query=query,
                    cursor=cursor,
                    limit=batch_limit
                )
                
                objects = search_result.get('objects', [])
                if not objects:
                    break
                
                for obj in objects:
                    if obj.get('type') == 'ITEM':
                        try:
                            item = self._extract_inventory_item(obj)
                            if item:
                                items.append(item)
                                extracted_count += 1
                                
                                if extracted_count >= max_limit:
                                    break
                        except Exception as e:
                            self.logger.error(f"Error processing catalog item {obj.get('id')}: {str(e)}")
                            continue
                
                cursor = search_result.get('cursor')
                if not cursor or extracted_count >= max_limit:
                    break
            
            self.logger.info(f"Extracted {len(items)} inventory items from Square")
            return items
        
        except Exception as e:
            self.logger.error(f"Error extracting inventory items: {str(e)}")
            raise
    
    def _build_catalog_search_query(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build Square catalog search query."""
        query = {
            'object_types': ['ITEM']
        }
        
        if not filters:
            return query
        
        # Add filters as needed
        if filters.get('category'):
            query['filter'] = {
                'text_filter': {
                    'any': [filters['category']]
                }
            }
        
        return query
    
    def _extract_inventory_item(self, catalog_object: Dict[str, Any]) -> Optional[POSInventoryItem]:
        """Extract POSInventoryItem from Square catalog object."""
        try:
            item_data = catalog_object.get('item_data', {})
            
            # Extract variations (Square items have variations for pricing)
            variations = item_data.get('variations', [])
            if variations:
                # Use first variation for pricing
                variation = variations[0]
                variation_data = variation.get('item_variation_data', {})
                
                # Extract price (in cents)
                price_money = variation_data.get('price_money', {})
                price_cents = price_money.get('amount', 0)
                price = Decimal(price_cents) / 100
                
                # Convert to NGN if needed
                currency = price_money.get('currency', 'USD')
                if currency != 'NGN':
                    price *= self.ngn_conversion_rate
                
                sku = variation_data.get('sku')
            else:
                price = Decimal('0')
                sku = None
            
            item = POSInventoryItem(
                item_id=catalog_object.get('id'),
                sku=sku,
                name=item_data.get('name', 'Unknown Item'),
                category=item_data.get('category_id'),
                price=float(price),
                currency='NGN',
                stock_quantity=None,  # Square inventory tracking is separate
                tax_rate=float(self.vat_rate),
                metadata={
                    'square_item_id': catalog_object.get('id'),
                    'description': item_data.get('description'),
                    'variations': [
                        {
                            'id': var.get('id'),
                            'name': var.get('item_variation_data', {}).get('name'),
                            'sku': var.get('item_variation_data', {}).get('sku'),
                            'price': float(Decimal(var.get('item_variation_data', {}).get('price_money', {}).get('amount', 0)) / 100)
                        }
                        for var in variations
                    ],
                    'categories': item_data.get('categories', []),
                    'product_type': item_data.get('product_type'),
                    'available_online': item_data.get('available_online', False),
                    'available_for_pickup': item_data.get('available_for_pickup', False),
                    'available_electronically': item_data.get('available_electronically', False)
                }
            )
            
            return item
        
        except Exception as e:
            self.logger.error(f"Error extracting inventory item: {str(e)}")
            return None