"""
WooCommerce E-commerce Order Transformer
Transforms WooCommerce orders to FIRS-compliant UBL BIS 3.0 invoices.
Handles WordPress/WooCommerce specific data structures and Nigerian tax compliance.
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
from .exceptions import WooCommerceTransformationError

logger = logging.getLogger(__name__)


class WooCommerceOrderTransformer:
    """
    WooCommerce Order to UBL Invoice Transformer
    
    Converts WooCommerce e-commerce orders into FIRS-compliant UBL BIS 3.0 invoices
    with Nigerian tax compliance and WordPress/WooCommerce specific handling.
    """
    
    def __init__(self):
        """Initialize WooCommerce order transformer."""
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
        
        # WooCommerce specific configuration
        self.woocommerce_config = {
            'supplier_name': 'WooCommerce Store',
            'supplier_id': 'WOO-STORE',
            'scheme_id': 'WOOCOMMERCE-ECOMMERCE',
            'invoice_type_code': '380'  # Commercial invoice
        }
        
        logger.info("Initialized WooCommerce order transformer")
    
    async def transform_order(
        self,
        order: EcommerceOrder,
        store_info: Dict[str, Any],
        woocommerce_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform WooCommerce order to UBL invoice.
        
        Args:
            order: WooCommerce e-commerce order
            store_info: WooCommerce store information
            woocommerce_metadata: Additional WooCommerce-specific metadata
            
        Returns:
            UBLInvoice: FIRS-compliant UBL invoice
            
        Raises:
            WooCommerceTransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming WooCommerce order: {order.order_id}")
            
            # Generate unique invoice ID
            invoice_id = f"WOO-{order.order_number}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create invoice header
            header = self._create_invoice_header(order, invoice_id, woocommerce_metadata)
            
            # Create supplier party (WooCommerce Store)
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
            
            # Add WooCommerce-specific metadata to UBL
            if woocommerce_metadata:
                ubl_invoice.custom_metadata = {
                    'woocommerce_order_id': order.order_id,
                    'woocommerce_order_key': order.metadata.get('woocommerce_order_key'),
                    'woocommerce_status': order.metadata.get('woocommerce_status'),
                    'woocommerce_version': order.metadata.get('woocommerce_version'),
                    'woocommerce_created_via': order.metadata.get('woocommerce_created_via'),
                    'wordpress_integration': True,
                    'store_url': order.metadata.get('store_url'),
                    'ecommerce_platform': 'woocommerce',
                    'order_type': 'ecommerce',
                    'original_currency': order.currency_code,
                    'extraction_timestamp': woocommerce_metadata.get('extraction_timestamp')
                }
            
            logger.info(f"Successfully transformed WooCommerce order to UBL: {invoice_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform WooCommerce order {order.order_id}: {str(e)}")
            raise WooCommerceTransformationError(
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
        """Create invoice header for WooCommerce order."""
        
        # Determine invoice type based on order characteristics
        created_via = order.metadata.get('woocommerce_created_via', '') if order.metadata else ''
        
        if 'subscription' in created_via.lower():
            invoice_type = 'Subscription Order'
        elif 'admin' in created_via.lower():
            invoice_type = 'Admin Order'
        elif 'api' in created_via.lower():
            invoice_type = 'API Order'
        elif 'checkout' in created_via.lower():
            invoice_type = 'Checkout Order'
        else:
            invoice_type = 'WooCommerce Order'
        
        # Get WordPress/WooCommerce version info
        wc_version = order.metadata.get('woocommerce_version', '') if order.metadata else ''
        note_parts = [f"{invoice_type} via WooCommerce"]
        if wc_version:
            note_parts.append(f"WC v{wc_version}")
        
        return InvoiceHeader(
            invoice_id=invoice_id,
            invoice_type_code=self.woocommerce_config['invoice_type_code'],
            invoice_date=order.order_date.date(),
            due_date=order.order_date.date(),  # E-commerce orders are typically immediate
            currency_code=order.currency_code,
            note=' | '.join(note_parts),
            order_reference=order.order_number,
            buyer_reference=order.customer_info.get('email', '') if order.customer_info else '',
            accounting_supplier_party_reference=self.woocommerce_config['supplier_id'],
            supplier_assigned_account_id=order.metadata.get('store_url') if order.metadata else None
        )
    
    def _create_supplier_party(self, store_info: Dict[str, Any]) -> InvoiceParty:
        """Create supplier party from WooCommerce store information."""
        
        # Use store info from WooCommerce
        store_name = store_info.get('store_name', 'WooCommerce Store')
        store_url = store_info.get('store_url', '')
        
        # Extract domain as store ID
        store_id = 'WOO-STORE'
        if store_url:
            from urllib.parse import urlparse
            parsed = urlparse(store_url)
            store_id = f"WOO-{parsed.netloc.replace('.', '-').upper()}"
        
        # Create address from store info
        address = Address(
            street_name=store_info.get('address', 'Store Address'),
            city_name=store_info.get('city', 'Lagos'),  # Default to Lagos for Nigerian stores
            postal_zone=store_info.get('postcode', '100001'),
            country_subentity=store_info.get('state', 'Lagos State'),
            country_identification_code=self.nigerian_config['country_code'],
            country_name=store_info.get('country', 'Nigeria')
        )
        
        # Create contact from store info
        contact = Contact(
            name=store_name,
            telephone='',  # WooCommerce doesn't typically store store phone
            electronic_mail=store_info.get('admin_email', ''),
            note=f"WooCommerce Store (WC v{store_info.get('woocommerce_version', 'unknown')})"
        )
        
        return InvoiceParty(
            party_name=store_name,
            party_identification=store_id,
            party_tax_scheme_id=store_info.get('tax_number', self.woocommerce_config['supplier_id']),
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
        company = customer_info.get('company', billing_address.get('company', ''))
        
        # Use company name if available, otherwise personal name
        if company:
            customer_name = company
        else:
            customer_name = f"{first_name} {last_name}".strip() or 'WooCommerce Customer'
        
        # Customer contact info
        customer_email = customer_info.get('email', '')
        customer_phone = customer_info.get('phone', billing_address.get('phone', ''))
        
        # Create address from billing address
        address = Address(
            street_name=billing_address.get('address1', 'Customer Address'),
            additional_street_name=billing_address.get('address2', ''),
            city_name=billing_address.get('city', 'Lagos'),
            postal_zone=billing_address.get('postcode', '100001'),
            country_subentity=billing_address.get('state', 'Lagos State'),
            country_identification_code=self.nigerian_config['country_code'],
            country_name=billing_address.get('country', 'Nigeria')
        )
        
        # Create contact
        contact = Contact(
            name=customer_name,
            telephone=customer_phone,
            electronic_mail=customer_email,
            note='WooCommerce Customer'
        )
        
        return InvoiceParty(
            party_name=customer_name,
            party_identification=customer_email or customer_phone or f"WOO-CUSTOMER-{order.order_id}",
            party_tax_scheme_id=customer_info.get('tin', self.nigerian_config['default_tin']),
            party_tax_scheme_name=self.nigerian_config['tax_scheme_name'],
            postal_address=address,
            contact=contact,
            party_legal_entity_registration_name=customer_name,
            party_legal_entity_company_id=customer_email or f"WOO-CUSTOMER-{order.order_id}"
        )
    
    def _create_invoice_lines(self, order: EcommerceOrder) -> List[InvoiceLine]:
        """Create invoice lines from order line items."""
        
        invoice_lines = []
        
        if not order.line_items:
            # Create default line item for WooCommerce order
            line_item = InvoiceLine(
                line_id="1",
                item_name="WooCommerce E-commerce Order",
                item_description="E-commerce purchase via WooCommerce platform",
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
                # Calculate line extension (subtotal before tax)
                item_subtotal = float(item.get('subtotal', 0))
                item_tax = float(item.get('total_tax', 0))
                
                # Get product classification
                # WooCommerce doesn't have built-in product types like Shopify, 
                # so we'll use the product name to classify
                item_name = item.get('name', 'WooCommerce Product')
                classification_code = self._get_product_classification_code(item_name)
                
                # Handle product variations
                variation_id = item.get('variation_id')
                if variation_id:
                    item_description = self._create_variation_description(item)
                else:
                    item_description = self._create_item_description(item)
                
                line_item = InvoiceLine(
                    line_id=str(idx),
                    item_name=item_name,
                    item_description=item_description,
                    quantity=Decimal(str(item.get('quantity', 1))),
                    unit_code='EA',  # Each
                    price_amount=Decimal(str(item.get('price', 0))),
                    line_extension_amount=Decimal(str(item_subtotal)),
                    tax_total_amount=Decimal(str(item_tax)),
                    item_classification_code=classification_code,
                    tax_category_id='S',  # Standard rate
                    tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                    tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                    tax_scheme_name=self.nigerian_config['tax_scheme_name'],
                    additional_item_properties={
                        'woocommerce_item_id': str(item.get('id', '')),
                        'woocommerce_product_id': str(item.get('product_id', '')),
                        'woocommerce_variation_id': str(item.get('variation_id', '')),
                        'sku': item.get('sku', ''),
                        'parent_name': item.get('parent_name', ''),
                        'bundled_by': item.get('bundled_by', ''),
                        'meta_data': str(item.get('meta_data', []))
                    }
                )
                invoice_lines.append(line_item)
            
            # Add shipping as separate line item if applicable
            if order.shipping_amount > 0:
                shipping_method = order.shipping_info.get('shipping_method', 'Shipping') if order.shipping_info else 'Shipping'
                
                shipping_line = InvoiceLine(
                    line_id=str(len(invoice_lines) + 1),
                    item_name=f"Shipping: {shipping_method}",
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
                    tax_scheme_name=self.nigerian_config['tax_scheme_name'],
                    additional_item_properties={
                        'shipping_method_id': order.shipping_info.get('shipping_method_id', '') if order.shipping_info else '',
                        'shipping_lines': str(order.shipping_info.get('shipping_lines', [])) if order.shipping_info else ''
                    }
                )
                invoice_lines.append(shipping_line)
            
            # Add fees as separate line items if applicable
            if order.metadata and order.metadata.get('woocommerce_fee_lines'):
                fee_lines = order.metadata.get('woocommerce_fee_lines', [])
                for fee_idx, fee in enumerate(fee_lines, 1):
                    fee_line = InvoiceLine(
                        line_id=str(len(invoice_lines) + 1),
                        item_name=f"Fee: {fee.get('name', 'Additional Fee')}",
                        item_description="Additional fee or charge",
                        quantity=Decimal('1'),
                        unit_code='EA',
                        price_amount=Decimal(str(fee.get('total', 0))),
                        line_extension_amount=Decimal(str(fee.get('total', 0))),
                        tax_total_amount=Decimal(str(fee.get('total_tax', 0))),
                        item_classification_code='77000000-0',  # General services
                        tax_category_id='S',  # Standard rate
                        tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                        tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                        tax_scheme_name=self.nigerian_config['tax_scheme_name']
                    )
                    invoice_lines.append(fee_line)
        
        return invoice_lines
    
    def _create_item_description(self, item: Dict[str, Any]) -> str:
        """Create detailed item description."""
        description_parts = []
        
        name = item.get('name', '')
        if name:
            description_parts.append(name)
        
        sku = item.get('sku', '')
        if sku:
            description_parts.append(f"SKU: {sku}")
        
        # Add meta data information
        meta_data = item.get('meta_data', [])
        for meta in meta_data:
            if isinstance(meta, dict):
                key = meta.get('key', '')
                value = meta.get('value', '')
                if key and value and not key.startswith('_'):  # Skip private meta
                    description_parts.append(f"{key}: {value}")
        
        return ' | '.join(description_parts) or 'WooCommerce Product'
    
    def _create_variation_description(self, item: Dict[str, Any]) -> str:
        """Create description for product variation."""
        description_parts = []
        
        name = item.get('name', '')
        parent_name = item.get('parent_name', '')
        
        if parent_name:
            description_parts.append(f"Product: {parent_name}")
        
        if name:
            description_parts.append(f"Variation: {name}")
        
        sku = item.get('sku', '')
        if sku:
            description_parts.append(f"SKU: {sku}")
        
        variation_id = item.get('variation_id', '')
        if variation_id:
            description_parts.append(f"Variation ID: {variation_id}")
        
        return ' | '.join(description_parts) or 'WooCommerce Product Variation'
    
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
        
        # Calculate line extension amount (subtotal before shipping and tax)
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
        
        # Get payment method information
        payment_method = payment_info.get('payment_method', 'unknown')
        payment_method_title = payment_info.get('payment_method_title', payment_method)
        
        # Map WooCommerce payment method to UBL payment means code
        payment_means_code = self._get_payment_means_code(payment_method)
        
        payment_means = PaymentMeans(
            payment_means_code=payment_means_code,
            payment_due_date=order.order_date.date(),
            payment_channel_code='ONLINE',
            instruction_id=payment_info.get('payment_reference'),
            instruction_note=f"{payment_method_title} payment via WooCommerce",
            payment_id=payment_info.get('transaction_id') or order.order_number,
            payee_financial_account_id=order.metadata.get('woocommerce_order_id') if order.metadata else None,
            payee_financial_account_name='WooCommerce Merchant Account'
        )
        
        return [payment_means]
    
    def _get_product_classification_code(self, item_name: str) -> str:
        """Get UNSPSC classification code for product based on name."""
        
        # Basic classification based on product name keywords
        item_name_lower = item_name.lower() if item_name else ''
        
        # Clothing and apparel
        if any(keyword in item_name_lower for keyword in [
            'shirt', 'dress', 'pants', 'jeans', 'jacket', 'coat', 'sweater',
            'clothing', 'apparel', 'fashion', 'wear'
        ]):
            return '53000000-5'  # Apparel and luggage and personal care products
        
        # Electronics
        elif any(keyword in item_name_lower for keyword in [
            'phone', 'computer', 'laptop', 'tablet', 'electronics', 'gadget',
            'camera', 'headphone', 'speaker', 'tv', 'monitor'
        ]):
            return '43000000-4'  # Information technology broadcasting and telecommunications
        
        # Books and media
        elif any(keyword in item_name_lower for keyword in [
            'book', 'novel', 'guide', 'manual', 'ebook', 'magazine',
            'journal', 'publication'
        ]):
            return '55000000-1'  # Printed matter and related products
        
        # Home and furniture
        elif any(keyword in item_name_lower for keyword in [
            'furniture', 'chair', 'table', 'bed', 'sofa', 'home', 'decor',
            'kitchen', 'appliance'
        ]):
            return '56000000-8'  # Furniture and furnishings
        
        # Health and beauty
        elif any(keyword in item_name_lower for keyword in [
            'health', 'beauty', 'cosmetic', 'skincare', 'makeup', 'cream',
            'lotion', 'supplement', 'vitamin'
        ]):
            return '51000000-1'  # Drugs and pharmaceutical products
        
        # Sports and recreation
        elif any(keyword in item_name_lower for keyword in [
            'sport', 'fitness', 'exercise', 'gym', 'outdoor', 'recreation',
            'ball', 'equipment'
        ]):
            return '49000000-2'  # Sports and recreational equipment and supplies
        
        # Food and beverage
        elif any(keyword in item_name_lower for keyword in [
            'food', 'snack', 'drink', 'beverage', 'coffee', 'tea', 'juice',
            'organic', 'grocery'
        ]):
            return '50000000-4'  # Food beverage and tobacco products
        
        # Jewelry and accessories
        elif any(keyword in item_name_lower for keyword in [
            'jewelry', 'necklace', 'ring', 'bracelet', 'watch', 'accessory'
        ]):
            return '53000000-5'  # Apparel and luggage and personal care products
        
        # Automotive
        elif any(keyword in item_name_lower for keyword in [
            'car', 'auto', 'automotive', 'vehicle', 'tire', 'parts'
        ]):
            return '25000000-8'  # Commercial and military and private vehicles and their accessories and components
        
        # Digital products and services
        elif any(keyword in item_name_lower for keyword in [
            'digital', 'software', 'app', 'service', 'subscription',
            'license', 'download'
        ]):
            return '48000000-8'  # Software and information services
        
        # Default classification
        return '48000000-8'  # Software and information services
    
    def _get_payment_means_code(self, payment_method: str) -> str:
        """Get UBL payment means code for WooCommerce payment method."""
        
        payment_code_mapping = {
            'bacs': '30',  # Credit transfer (Bank transfer)
            'cheque': '20',  # Check
            'cod': '10',  # Cash on delivery
            'paypal': '42',  # Payment to bank account
            'stripe': '48',  # Bank card
            'square': '48',  # Bank card
            'razorpay': '48',  # Bank card
            'payu': '48',  # Bank card
            'paystack': '48',  # Bank card
            'flutterwave': '48',  # Bank card
            'payfast': '48',  # Bank card
            'bank_transfer': '30',  # Credit transfer
            'credit_card': '48',  # Bank card
            'debit_card': '48',  # Bank card
            'wallet': '42',  # Payment to bank account
            'mobile_money': '42',  # Payment to bank account
            'default': '48'  # Bank card
        }
        
        method_lower = payment_method.lower() if payment_method else ''
        
        # Try exact match first
        if method_lower in payment_code_mapping:
            return payment_code_mapping[method_lower]
        
        # Try partial matches
        for key, code in payment_code_mapping.items():
            if key in method_lower:
                return code
        
        return payment_code_mapping['default']
    
    async def transform_batch_orders(
        self,
        orders: List[EcommerceOrder],
        store_info: Dict[str, Any],
        woocommerce_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple WooCommerce orders to UBL invoices.
        
        Args:
            orders: List of WooCommerce orders
            store_info: WooCommerce store information
            woocommerce_metadata: Additional metadata
            
        Returns:
            List[UBLInvoice]: List of UBL invoices
        """
        try:
            logger.info(f"Transforming batch of {len(orders)} WooCommerce orders")
            
            invoices = []
            for order in orders:
                try:
                    invoice = await self.transform_order(
                        order,
                        store_info,
                        woocommerce_metadata
                    )
                    invoices.append(invoice)
                    
                except Exception as e:
                    logger.error(f"Failed to transform order {order.order_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully transformed {len(invoices)} WooCommerce orders")
            return invoices
            
        except Exception as e:
            logger.error(f"Batch transformation failed: {str(e)}")
            raise WooCommerceTransformationError(f"Batch transformation failed: {str(e)}")
    
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
            
            # WooCommerce specific validation
            if invoice.custom_metadata:
                if not invoice.custom_metadata.get('woocommerce_order_id'):
                    logger.warning("WooCommerce invoice missing order ID in metadata")
            
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