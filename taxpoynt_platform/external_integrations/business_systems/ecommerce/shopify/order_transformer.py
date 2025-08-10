"""
Shopify E-commerce Order Transformer
Transforms Shopify orders to FIRS-compliant UBL BIS 3.0 invoices.
Handles Nigerian tax compliance and e-commerce specific requirements.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal
from uuid import uuid4

from ....connector_framework.base_ecommerce_connector import EcommerceOrder
from ....shared.models.invoice_models import (
    UBLInvoice,
    InvoiceHeader,
    InvoiceParty,
    InvoiceLine,
    TaxTotal,
    TaxSubtotal,
    MonetaryTotal,
    PaymentMeans,
    Address,
    Contact
)
from ....shared.utils.ubl_generator import UBLGenerator
from .exceptions import ShopifyTransformationError

logger = logging.getLogger(__name__)


class ShopifyOrderTransformer:
    """
    Shopify Order to UBL Invoice Transformer
    
    Converts Shopify e-commerce orders into FIRS-compliant UBL BIS 3.0 invoices
    with Nigerian tax compliance and e-commerce specific handling.
    """
    
    def __init__(self):
        """Initialize Shopify order transformer."""
        self.ubl_generator = UBLGenerator()
        
        # Nigerian compliance configuration
        self.nigerian_config = {
            'currency': 'NGN',
            'vat_rate': 0.075,  # 7.5% VAT
            'country_code': 'NG',
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Value Added Tax',
            'default_tin': '00000000-0001'
        }
        
        # Shopify specific configuration
        self.shopify_config = {
            'supplier_name': 'Shopify Store',
            'supplier_id': 'SHOPIFY-STORE',
            'scheme_id': 'SHOPIFY-ECOMMERCE',
            'invoice_type_code': '380'  # Commercial invoice
        }
        
        logger.info("Initialized Shopify order transformer")
    
    async def transform_order(
        self,
        order: EcommerceOrder,
        store_info: Dict[str, Any],
        shopify_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform Shopify order to UBL invoice.
        
        Args:
            order: Shopify e-commerce order
            store_info: Shopify store information
            shopify_metadata: Additional Shopify-specific metadata
            
        Returns:
            UBLInvoice: FIRS-compliant UBL invoice
            
        Raises:
            ShopifyTransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming Shopify order: {order.order_id}")
            
            # Generate unique invoice ID
            invoice_id = f"SHOPIFY-{order.order_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create invoice header
            header = self._create_invoice_header(order, invoice_id, shopify_metadata)
            
            # Create supplier party (Shopify Store)
            supplier_party = self._create_supplier_party(store_info)
            
            # Create customer party
            customer_party = self._create_customer_party(order)
            
            # Create invoice lines
            invoice_lines = self._create_invoice_lines(order)
            
            # Create tax totals
            tax_total = self._create_tax_total(order)
            
            # Create monetary totals
            legal_monetary_total = self._create_monetary_total(order)
            
            # Create payment means
            payment_means = self._create_payment_means(order)
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                supplier_party=supplier_party,
                customer_party=customer_party,
                invoice_lines=invoice_lines,
                tax_total=[tax_total] if tax_total else [],
                legal_monetary_total=legal_monetary_total,
                payment_means=payment_means,
                additional_document_references=[],
                delivery_terms=None
            )
            
            # Add Shopify-specific metadata to UBL
            if shopify_metadata:
                ubl_invoice.custom_metadata = {
                    'shopify_order_id': order.order_id,
                    'shopify_order_number': order.order_number,
                    'shopify_order_status_url': order.metadata.get('shopify_order_status_url'),
                    'shopify_tags': order.metadata.get('shopify_tags'),
                    'shopify_source_name': order.metadata.get('shopify_source_name'),
                    'shopify_referring_site': order.metadata.get('shopify_referring_site'),
                    'shop_name': order.metadata.get('shop_name'),
                    'ecommerce_platform': 'shopify',
                    'order_type': 'ecommerce',
                    'original_currency': order.currency_code,
                    'extraction_timestamp': shopify_metadata.get('extraction_timestamp')
                }
            
            logger.info(f"Successfully transformed Shopify order to UBL: {invoice_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform Shopify order {order.order_id}: {str(e)}")
            raise ShopifyTransformationError(
                f"Transformation failed: {str(e)}",
                order_id=order.order_id,
                order_number=order.order_number,
                details={'error': str(e), 'order_data': order.__dict__}
            )
    
    def _create_invoice_header(
        self,
        order: EcommerceOrder,
        invoice_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create invoice header for Shopify order."""
        
        # Determine invoice type based on order characteristics
        if order.metadata and order.metadata.get('shopify_tags'):
            tags = order.metadata.get('shopify_tags', '').lower()
            if 'subscription' in tags:
                invoice_type = 'Subscription Order'
            elif 'gift' in tags:
                invoice_type = 'Gift Order'
            elif 'digital' in tags:
                invoice_type = 'Digital Products Order'
            else:
                invoice_type = 'E-commerce Order'
        else:
            invoice_type = 'E-commerce Order'
        
        return InvoiceHeader(
            invoice_id=invoice_id,
            invoice_type_code=self.shopify_config['invoice_type_code'],
            invoice_date=order.order_date.date(),
            due_date=order.order_date.date(),  # E-commerce orders are typically immediate
            currency_code=order.currency_code,
            note=f"{invoice_type} via Shopify E-commerce Platform",
            order_reference=order.order_number,
            buyer_reference=order.customer_info.get('email', '') if order.customer_info else '',
            accounting_supplier_party_reference=self.shopify_config['supplier_id'],
            supplier_assigned_account_id=order.metadata.get('shop_name') if order.metadata else None
        )
    
    def _create_supplier_party(self, store_info: Dict[str, Any]) -> InvoiceParty:
        """Create supplier party from Shopify store information."""
        
        # Use store info from Shopify
        store_name = store_info.get('name', 'Shopify Store')
        store_id = str(store_info.get('id', 'SHOPIFY-STORE'))
        
        # Create address from store info
        store_address = store_info.get('address1', '')
        store_city = store_info.get('city', 'Lagos')  # Default to Lagos for Nigerian stores
        store_province = store_info.get('province', 'Lagos State')
        store_country = store_info.get('country_name', 'Nigeria')
        store_zip = store_info.get('zip', '100001')
        
        address = Address(
            street_name=store_address or 'Store Address',
            city_name=store_city,
            postal_zone=store_zip,
            country_subentity=store_province,
            country_identification_code=self.nigerian_config['country_code'],
            country_name=store_country
        )
        
        # Create contact from store info
        contact = Contact(
            name=store_info.get('shop_owner', store_name),
            telephone=store_info.get('phone', ''),
            electronic_mail=store_info.get('email', ''),
            note='Shopify E-commerce Store'
        )
        
        return InvoiceParty(
            party_name=store_name,
            party_identification=store_id,
            party_tax_scheme_id=store_info.get('tax_number', self.shopify_config['supplier_id']),
            party_tax_scheme_name=self.nigerian_config['tax_scheme_name'],
            postal_address=address,
            contact=contact,
            party_legal_entity_registration_name=store_name,
            party_legal_entity_company_id=store_id
        )
    
    def _create_customer_party(self, order: EcommerceOrder) -> InvoiceParty:
        """Create customer party from order customer info."""
        
        customer_info = order.customer_info or {}
        billing_address = order.billing_address or {}
        
        # Customer name
        first_name = customer_info.get('first_name', billing_address.get('first_name', ''))
        last_name = customer_info.get('last_name', billing_address.get('last_name', ''))
        customer_name = f"{first_name} {last_name}".strip() or 'Shopify Customer'
        
        # Customer contact info
        customer_email = customer_info.get('email', '')
        customer_phone = customer_info.get('phone', billing_address.get('phone', ''))
        
        # Create address from billing address
        address = Address(
            street_name=billing_address.get('address1', 'Customer Address'),
            additional_street_name=billing_address.get('address2', ''),
            city_name=billing_address.get('city', 'Lagos'),
            postal_zone=billing_address.get('zip', '100001'),
            country_subentity=billing_address.get('province', 'Lagos State'),
            country_identification_code=self.nigerian_config['country_code'],
            country_name=billing_address.get('country', 'Nigeria')
        )
        
        # Create contact
        contact = Contact(
            name=customer_name,
            telephone=customer_phone,
            electronic_mail=customer_email,
            note='Shopify E-commerce Customer'
        )
        
        return InvoiceParty(
            party_name=customer_name,
            party_identification=customer_email or customer_phone or 'SHOPIFY-CUSTOMER',
            party_tax_scheme_id=customer_info.get('tin', self.nigerian_config['default_tin']),
            party_tax_scheme_name=self.nigerian_config['tax_scheme_name'],
            postal_address=address,
            contact=contact,
            party_legal_entity_registration_name=customer_name,
            party_legal_entity_company_id=customer_email or 'SHOPIFY-CUSTOMER'
        )
    
    def _create_invoice_lines(self, order: EcommerceOrder) -> List[InvoiceLine]:
        """Create invoice lines from order line items."""
        
        invoice_lines = []
        
        if not order.line_items:
            # Create default line item for Shopify order
            line_item = InvoiceLine(
                line_id="1",
                item_name="Shopify E-commerce Order",
                item_description="E-commerce purchase via Shopify platform",
                quantity=Decimal('1'),
                unit_code='EA',  # Each
                price_amount=Decimal(str(order.subtotal)),
                line_extension_amount=Decimal(str(order.subtotal)),
                tax_total_amount=Decimal(str(order.tax_amount)),
                item_classification_code='48000000-8',  # Software and information services
                tax_category_id='S',  # Standard rate
                tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                tax_scheme_name=self.nigerian_config['tax_scheme_name']
            )
            invoice_lines.append(line_item)
        else:
            # Convert order line items
            for idx, item in enumerate(order.line_items, 1):
                # Calculate item tax amount
                item_tax_lines = item.get('tax_lines', [])
                item_tax_amount = sum(
                    float(tax_line.get('price', 0)) for tax_line in item_tax_lines
                )
                
                # Calculate line extension (price * quantity - discounts)
                item_price = float(item.get('price', 0))
                item_quantity = Decimal(str(item.get('quantity', 1)))
                item_discount = float(item.get('total_discount', 0))
                line_extension = (item_price * float(item_quantity)) - item_discount
                
                # Get product classification
                product_type = item.get('product_type', '')
                classification_code = self._get_product_classification_code(product_type)
                
                line_item = InvoiceLine(
                    line_id=str(idx),
                    item_name=item.get('title', 'Shopify Product'),
                    item_description=self._create_item_description(item),
                    quantity=item_quantity,
                    unit_code='EA',  # Each
                    price_amount=Decimal(str(item_price)),
                    line_extension_amount=Decimal(str(line_extension)),
                    tax_total_amount=Decimal(str(item_tax_amount)),
                    item_classification_code=classification_code,
                    tax_category_id='S',  # Standard rate
                    tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                    tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                    tax_scheme_name=self.nigerian_config['tax_scheme_name'],
                    additional_item_properties={
                        'shopify_product_id': str(item.get('product_id', '')),
                        'shopify_variant_id': str(item.get('variant_id', '')),
                        'sku': item.get('sku', ''),
                        'vendor': item.get('vendor', ''),
                        'variant_title': item.get('variant_title', ''),
                        'gift_card': item.get('gift_card', False),
                        'fulfillment_service': item.get('fulfillment_service', 'manual')
                    }
                )
                invoice_lines.append(line_item)
            
            # Add shipping as separate line item if applicable
            if order.shipping_amount > 0:
                shipping_line = InvoiceLine(
                    line_id=str(len(invoice_lines) + 1),
                    item_name="Shipping & Handling",
                    item_description="E-commerce order shipping and handling fees",
                    quantity=Decimal('1'),
                    unit_code='EA',
                    price_amount=Decimal(str(order.shipping_amount)),
                    line_extension_amount=Decimal(str(order.shipping_amount)),
                    tax_total_amount=Decimal('0'),  # Shipping usually not taxed
                    item_classification_code='64000000-4',  # Transport services
                    tax_category_id='Z',  # Zero rate
                    tax_category_percent=Decimal('0'),
                    tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                    tax_scheme_name=self.nigerian_config['tax_scheme_name']
                )
                invoice_lines.append(shipping_line)
        
        return invoice_lines
    
    def _create_item_description(self, item: Dict[str, Any]) -> str:
        """Create detailed item description."""
        description_parts = []
        
        title = item.get('title', '')
        if title:
            description_parts.append(title)
        
        variant_title = item.get('variant_title', '')
        if variant_title and variant_title != 'Default Title':
            description_parts.append(f"Variant: {variant_title}")
        
        sku = item.get('sku', '')
        if sku:
            description_parts.append(f"SKU: {sku}")
        
        vendor = item.get('vendor', '')
        if vendor:
            description_parts.append(f"Brand: {vendor}")
        
        return ' | '.join(description_parts) or 'Shopify Product'
    
    def _create_tax_total(self, order: EcommerceOrder) -> Optional[TaxTotal]:
        """Create tax total from order tax information."""
        
        if order.tax_amount <= 0:
            return None
        
        # Create tax subtotal
        tax_subtotal = TaxSubtotal(
            taxable_amount=Decimal(str(order.subtotal)),
            tax_amount=Decimal(str(order.tax_amount)),
            tax_category_id='S',  # Standard rate
            tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
            tax_scheme_id=self.nigerian_config['tax_scheme_id'],
            tax_scheme_name=self.nigerian_config['tax_scheme_name']
        )
        
        return TaxTotal(
            tax_amount=Decimal(str(order.tax_amount)),
            tax_subtotals=[tax_subtotal]
        )
    
    def _create_monetary_total(self, order: EcommerceOrder) -> MonetaryTotal:
        """Create monetary total from order amounts."""
        
        # Calculate line extension amount (subtotal before shipping)
        line_extension_amount = order.subtotal
        
        # Tax exclusive amount (line extension + shipping, before tax)
        tax_exclusive_amount = order.subtotal + order.shipping_amount
        
        return MonetaryTotal(
            line_extension_amount=Decimal(str(line_extension_amount)),
            tax_exclusive_amount=Decimal(str(tax_exclusive_amount)),
            tax_inclusive_amount=Decimal(str(order.total_amount)),
            allowance_total_amount=Decimal(str(order.discount_amount)),
            charge_total_amount=Decimal(str(order.shipping_amount)),
            payable_amount=Decimal(str(order.total_amount))
        )
    
    def _create_payment_means(self, order: EcommerceOrder) -> List[PaymentMeans]:
        """Create payment means from order payment info."""
        
        payment_info = order.payment_info
        if not payment_info:
            return []
        
        # Get payment gateway information
        gateway_names = payment_info.get('gateway_names', [])
        primary_gateway = gateway_names[0] if gateway_names else 'unknown'
        
        # Map Shopify payment gateway to UBL payment means code
        payment_means_code = self._get_payment_means_code(primary_gateway)
        
        # Get payment method name
        payment_method_name = self._get_payment_method_name(primary_gateway)
        
        payment_means = PaymentMeans(
            payment_means_code=payment_means_code,
            payment_due_date=order.order_date.date(),
            payment_channel_code='ONLINE',
            instruction_id=payment_info.get('payment_reference'),
            instruction_note=f"{payment_method_name} payment via Shopify",
            payment_id=payment_info.get('transaction_id') or payment_info.get('checkout_token'),
            payee_financial_account_id=order.metadata.get('shopify_order_id') if order.metadata else None,
            payee_financial_account_name='Shopify Merchant Account'
        )
        
        return [payment_means]
    
    def _get_product_classification_code(self, product_type: str) -> str:
        """Get UNSPSC classification code for product type."""
        
        classification_mapping = {
            'apparel': '53000000-5',  # Apparel and luggage and personal care products
            'clothing': '53000000-5',  # Apparel and luggage and personal care products
            'electronics': '43000000-4',  # Information technology broadcasting and telecommunications
            'books': '55000000-1',  # Printed matter and related products
            'home': '30000000-9',  # Manufacturing components and supplies
            'jewelry': '56000000-8',  # Furniture and furnishings
            'shoes': '53000000-5',  # Apparel and luggage and personal care products
            'bags': '53000000-5',  # Apparel and luggage and personal care products
            'toys': '60000000-2',  # Musical instruments games toys arts and crafts and educational equipment
            'sports': '49000000-2',  # Sports and recreational equipment and supplies
            'health': '51000000-1',  # Drugs and pharmaceutical products
            'beauty': '53000000-5',  # Apparel and luggage and personal care products
            'food': '50000000-4',  # Food beverage and tobacco products
            'automotive': '25000000-8',  # Commercial and military and private vehicles and their accessories and components
            'digital': '48000000-8',  # Software and information services
            'gift_card': '77000000-0',  # General services
            'default': '48000000-8'  # Software and information services
        }
        
        product_type_lower = product_type.lower() if product_type else ''
        
        # Try to match product type
        for key, code in classification_mapping.items():
            if key in product_type_lower:
                return code
        
        return classification_mapping['default']
    
    def _get_payment_means_code(self, gateway_name: str) -> str:
        """Get UBL payment means code for Shopify payment gateway."""
        
        payment_code_mapping = {
            'shopify_payments': '48',  # Bank card
            'stripe': '48',  # Bank card
            'paypal': '42',  # Payment to bank account
            'square': '48',  # Bank card
            'authorize_net': '48',  # Bank card
            'braintree': '48',  # Bank card
            'bogus': '10',  # Cash (for testing)
            'manual': '10',  # Cash
            'bank_transfer': '30',  # Credit transfer
            'wallet': '42',  # Payment to bank account
            'cryptocurrency': '97',  # Clearing between partners
            'default': '48'  # Bank card
        }
        
        gateway_lower = gateway_name.lower() if gateway_name else ''
        
        # Try to match gateway name
        for key, code in payment_code_mapping.items():
            if key in gateway_lower:
                return code
        
        return payment_code_mapping['default']
    
    def _get_payment_method_name(self, gateway_name: str) -> str:
        """Get human-readable payment method name."""
        
        method_names = {
            'shopify_payments': 'Shopify Payments',
            'stripe': 'Stripe Payment',
            'paypal': 'PayPal',
            'square': 'Square Payment',
            'authorize_net': 'Authorize.Net',
            'braintree': 'Braintree Payment',
            'bogus': 'Test Payment',
            'manual': 'Manual Payment',
            'bank_transfer': 'Bank Transfer',
            'wallet': 'Digital Wallet',
            'cryptocurrency': 'Cryptocurrency',
            'default': 'Online Payment'
        }
        
        gateway_lower = gateway_name.lower() if gateway_name else ''
        
        # Try to match gateway name
        for key, name in method_names.items():
            if key in gateway_lower:
                return name
        
        return method_names['default']
    
    async def transform_batch_orders(
        self,
        orders: List[EcommerceOrder],
        store_info: Dict[str, Any],
        shopify_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple Shopify orders to UBL invoices.
        
        Args:
            orders: List of Shopify orders
            store_info: Shopify store information
            shopify_metadata: Additional metadata
            
        Returns:
            List[UBLInvoice]: List of UBL invoices
        """
        try:
            logger.info(f"Transforming batch of {len(orders)} Shopify orders")
            
            invoices = []
            for order in orders:
                try:
                    invoice = await self.transform_order(
                        order,
                        store_info,
                        shopify_metadata
                    )
                    invoices.append(invoice)
                    
                except Exception as e:
                    logger.error(f"Failed to transform order {order.order_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully transformed {len(invoices)} Shopify orders")
            return invoices
            
        except Exception as e:
            logger.error(f"Batch transformation failed: {str(e)}")
            raise ShopifyTransformationError(f"Batch transformation failed: {str(e)}")
    
    def validate_ubl_invoice(self, invoice: UBLInvoice) -> bool:
        """
        Validate UBL invoice for FIRS compliance.
        
        Args:
            invoice: UBL invoice to validate
            
        Returns:
            bool: True if valid
        """
        try:
            # Basic validation checks
            if not invoice.header or not invoice.header.invoice_id:
                logger.error("Invoice missing header or invoice ID")
                return False
            
            if not invoice.supplier_party or not invoice.customer_party:
                logger.error("Invoice missing supplier or customer party")
                return False
            
            if not invoice.invoice_lines:
                logger.error("Invoice missing invoice lines")
                return False
            
            if not invoice.legal_monetary_total:
                logger.error("Invoice missing monetary totals")
                return False
            
            # E-commerce specific validation
            if not invoice.header.order_reference:
                logger.error("E-commerce invoice missing order reference")
                return False
            
            # Tax validation for Nigerian VAT (if applicable)
            if invoice.tax_total:
                for tax_total in invoice.tax_total:
                    for tax_subtotal in tax_total.tax_subtotals:
                        if tax_subtotal.tax_scheme_id != self.nigerian_config['tax_scheme_id']:
                            logger.error(f"Invalid tax scheme: {tax_subtotal.tax_scheme_id}")
                            return False
            
            logger.info(f"UBL invoice validation passed: {invoice.header.invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"UBL invoice validation failed: {str(e)}")
            return False