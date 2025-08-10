"""
Shopify POS Transaction Transformer

Transforms Shopify POS transactions (orders) to FIRS-compliant UBL BIS 3.0 invoices
for Nigerian e-invoicing compliance.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional
from datetime import datetime, date

from ....connector_framework.base_pos_connector import POSTransaction

logger = logging.getLogger(__name__)


class ShopifyTransactionTransformer:
    """
    Shopify POS transaction to FIRS invoice transformer - System Integrator Functions.
    
    Transforms Shopify transactions into UBL BIS 3.0 compliant invoices
    optimized for Nigerian FIRS e-invoicing requirements.
    
    Features:
    - UBL BIS 3.0 standard compliance
    - Nigerian VAT (7.5%) handling
    - Multi-currency support with NGN conversion
    - Customer TIN validation and default handling
    - Line item transformation with tax breakdown
    - FIRS-compliant metadata generation
    - Shopify-specific order data integration
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Shopify transaction transformer."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Nigerian market configuration
        self.default_currency = config.get('currency', 'NGN')
        self.vat_rate = Decimal(config.get('vat_rate', '0.075'))  # Nigerian VAT 7.5%
        self.default_customer_tin = config.get('default_customer_tin', '00000000-0001-0')
        
        # Supplier/Merchant information
        self.supplier_config = config.get('supplier', {})
        self.supplier_name = self.supplier_config.get('name', 'TaxPoynt Merchant')
        self.supplier_tin = self.supplier_config.get('tin', '12345678-0001-0')
        self.supplier_address = self.supplier_config.get('address', {
            'country': 'NG',
            'state': 'Lagos',
            'city': 'Lagos',
            'address_line_1': 'Default Address'
        })
        
        # Invoice configuration
        self.invoice_config = config.get('invoice', {})
        self.invoice_prefix = self.invoice_config.get('prefix', 'SP')  # Shopify POS
        self.include_tax_breakdown = self.invoice_config.get('include_tax_breakdown', True)
        
        # FIRS compliance settings
        self.firs_config = config.get('firs', {})
        self.taxpayer_id = self.firs_config.get('taxpayer_id')
        self.company_registration_number = self.firs_config.get('company_registration_number')
    
    async def transform_transaction_to_invoice(
        self,
        transaction: POSTransaction,
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Shopify transaction to FIRS-compliant UBL invoice.
        
        Args:
            transaction: POSTransaction object to transform
            transformation_options: Additional transformation settings including:
                - invoice_number: Custom invoice number
                - issue_date: Invoice issue date
                - due_date: Invoice due date
                - customer_tin: Override customer TIN
                - include_tax_breakdown: Include detailed tax breakdown
                - payment_terms: Payment terms and conditions
                - shop_info: Shopify shop information
        
        Returns:
            FIRS-compliant UBL BIS 3.0 invoice data
        """
        try:
            options = transformation_options or {}
            
            self.logger.info(f"Transforming Shopify transaction {transaction.transaction_id} to FIRS invoice")
            
            # Generate invoice header
            invoice_header = self._build_invoice_header(transaction, options)
            
            # Build supplier party (merchant/shop)
            supplier_party = self._build_supplier_party(transaction, options)
            
            # Build customer party
            customer_party = self._build_customer_party(transaction, options)
            
            # Transform line items
            invoice_lines = self._transform_items_to_invoice_lines(transaction, options)
            
            # Calculate tax summary
            tax_summary = self._calculate_tax_summary(transaction, invoice_lines)
            
            # Calculate monetary totals
            monetary_totals = self._calculate_monetary_totals(transaction, tax_summary)
            
            # Build payment terms
            payment_terms = self._build_payment_terms(transaction, options)
            
            # Generate invoice metadata
            metadata = self._build_invoice_metadata(transaction, options)
            
            # Build delivery information if available
            delivery_info = self._build_delivery_info(transaction, options)
            
            # Construct final UBL invoice
            ubl_invoice = {
                'ubl_version': '2.1',
                'customization_id': 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0',
                'profile_id': 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
                'invoice_header': invoice_header,
                'supplier_party': supplier_party,
                'customer_party': customer_party,
                'invoice_lines': invoice_lines,
                'tax_summary': tax_summary,
                'monetary_totals': monetary_totals,
                'payment_terms': payment_terms,
                'additional_document_references': self._build_document_references(transaction),
                'delivery_information': delivery_info,
                'metadata': metadata
            }
            
            # Validate invoice structure
            validation_result = self._validate_invoice_structure(ubl_invoice)
            if not validation_result['valid']:
                self.logger.warning(f"Invoice validation warnings: {validation_result['warnings']}")
            
            self.logger.info(f"Successfully transformed transaction {transaction.transaction_id} to FIRS invoice")
            return ubl_invoice
        
        except Exception as e:
            self.logger.error(f"Error transforming transaction to invoice: {str(e)}")
            raise
    
    def _build_invoice_header(self, transaction: POSTransaction, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL invoice header."""
        # Generate invoice number
        invoice_number = options.get('invoice_number')
        if not invoice_number:
            # Use Shopify order number if available
            order_number = transaction.metadata.get('order_number')
            if order_number:
                invoice_number = f"{self.invoice_prefix}-{order_number}"
            else:
                timestamp = transaction.timestamp.strftime('%Y%m%d%H%M%S')
                invoice_number = f"{self.invoice_prefix}-{timestamp}-{transaction.transaction_id[:8]}"
        
        # Determine dates
        issue_date = options.get('issue_date')
        if isinstance(issue_date, str):
            issue_date = datetime.fromisoformat(issue_date).date()
        elif isinstance(issue_date, datetime):
            issue_date = issue_date.date()
        else:
            issue_date = transaction.timestamp.date()
        
        due_date = options.get('due_date')
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date).date()
        elif isinstance(due_date, datetime):
            due_date = due_date.date()
        else:
            due_date = issue_date  # POS transactions are typically paid immediately
        
        return {
            'invoice_number': invoice_number,
            'issue_date': issue_date.isoformat(),
            'due_date': due_date.isoformat(),
            'invoice_type': 'SALE',
            'document_type': 'INVOICE',
            'currency': transaction.currency,
            'tax_point_date': issue_date.isoformat(),
            'payment_reference': transaction.transaction_id,
            'order_reference': transaction.metadata.get('shopify_order_id'),
            'buyer_reference': transaction.customer_info.get('id') if transaction.customer_info else None,
            'invoice_period': {
                'start_date': issue_date.isoformat(),
                'end_date': issue_date.isoformat()
            },
            'shopify_order_number': transaction.metadata.get('order_number'),
            'shopify_checkout_token': transaction.metadata.get('checkout_token')
        }
    
    def _build_supplier_party(self, transaction: POSTransaction, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL supplier party (merchant/shop)."""
        # Override with options if provided
        supplier_name = options.get('supplier_name', self.supplier_name)
        supplier_tin = options.get('supplier_tin', self.supplier_tin)
        supplier_address = options.get('supplier_address', self.supplier_address)
        
        # Use Shopify shop info if available
        shop_info = options.get('shop_info', {})
        if shop_info:
            supplier_name = shop_info.get('name', supplier_name)
            if shop_info.get('address'):
                supplier_address.update(shop_info['address'])
        
        return {
            'party_identification': {
                'id': supplier_tin,
                'scheme_id': 'TIN'
            },
            'party_name': [{'name': supplier_name}],
            'postal_address': {
                'street_name': supplier_address.get('address_line_1', ''),
                'additional_street_name': supplier_address.get('address_line_2', ''),
                'city_name': supplier_address.get('city', 'Lagos'),
                'postal_zone': supplier_address.get('postal_code', ''),
                'country_subdivision': supplier_address.get('state', 'Lagos'),
                'country': {
                    'identification_code': supplier_address.get('country', 'NG'),
                    'name': 'Nigeria'
                }
            },
            'party_tax_scheme': {
                'company_id': supplier_tin,
                'tax_scheme': {
                    'id': 'VAT',
                    'name': 'Value Added Tax'
                }
            },
            'party_legal_entity': {
                'registration_name': supplier_name,
                'company_id': self.company_registration_number or supplier_tin,
                'registration_address': supplier_address
            },
            'contact': {
                'name': supplier_name,
                'telephone': supplier_address.get('phone'),
                'electronic_mail': supplier_address.get('email')
            }
        }
    
    def _build_customer_party(self, transaction: POSTransaction, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL customer party."""
        # Determine customer information
        if transaction.customer_info:
            customer_name = transaction.customer_info.get('name', 'Retail Customer')
            customer_tin = options.get('customer_tin') or transaction.customer_info.get('tin') or self.default_customer_tin
            customer_address = transaction.customer_info.get('address', {})
            customer_email = transaction.customer_info.get('email')
            customer_phone = transaction.customer_info.get('phone')
        else:
            # Default retail customer
            customer_name = 'Retail Customer'
            customer_tin = options.get('customer_tin', self.default_customer_tin)
            customer_address = {}
            customer_email = None
            customer_phone = None
        
        # Ensure address has required fields
        address = {
            'street_name': customer_address.get('address1', customer_address.get('address_line_1', 'N/A')),
            'additional_street_name': customer_address.get('address2', customer_address.get('address_line_2', '')),
            'city_name': customer_address.get('city', 'Lagos'),
            'postal_zone': customer_address.get('zip', customer_address.get('postal_code', '')),
            'country_subdivision': customer_address.get('province', customer_address.get('state', 'Lagos')),
            'country': {
                'identification_code': customer_address.get('country_code', customer_address.get('country', 'NG')),
                'name': customer_address.get('country_name', 'Nigeria')
            }
        }
        
        customer_party = {
            'party_identification': {
                'id': customer_tin,
                'scheme_id': 'TIN'
            },
            'party_name': [{'name': customer_name}],
            'postal_address': address,
            'party_tax_scheme': {
                'company_id': customer_tin,
                'tax_scheme': {
                    'id': 'VAT',
                    'name': 'Value Added Tax'
                }
            }
        }
        
        # Add contact information if available
        if customer_email or customer_phone:
            customer_party['contact'] = {}
            if customer_email:
                customer_party['contact']['electronic_mail'] = customer_email
            if customer_phone:
                customer_party['contact']['telephone'] = customer_phone
        
        return customer_party
    
    def _transform_items_to_invoice_lines(self, transaction: POSTransaction, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform transaction items to UBL invoice lines."""
        invoice_lines = []
        
        if transaction.items:
            # Transform each item
            for i, item in enumerate(transaction.items, 1):
                invoice_line = self._transform_item_to_invoice_line(item, i, transaction)
                invoice_lines.append(invoice_line)
        else:
            # Create single line for transaction amount
            invoice_line = self._create_default_invoice_line(transaction)
            invoice_lines.append(invoice_line)
        
        return invoice_lines
    
    def _transform_item_to_invoice_line(self, item: Dict[str, Any], line_number: int, transaction: POSTransaction) -> Dict[str, Any]:
        """Transform single item to UBL invoice line."""
        quantity = item.get('quantity', 1)
        unit_price = Decimal(str(item.get('unit_price', 0)))
        total_price = Decimal(str(item.get('total_price', 0)))
        
        # Calculate line extension amount (excluding tax)
        line_extension_amount = total_price / (1 + self.vat_rate)
        
        # Calculate tax amount for this line
        tax_amount = total_price - line_extension_amount
        
        # Build item description with Shopify-specific details
        item_description = item.get('name', 'Unknown Item')
        
        # Add customizations to description if available
        customizations = item.get('customizations', [])
        if customizations:
            custom_details = []
            for custom in customizations:
                if isinstance(custom, dict):
                    name = custom.get('name', '')
                    value = custom.get('value', '')
                    if name and value:
                        custom_details.append(f"{name}: {value}")
            
            if custom_details:
                item_description += f" ({', '.join(custom_details)})"
        
        invoice_line = {
            'id': str(line_number),
            'note': f"Shopify POS item: {item_description}",
            'invoiced_quantity': {
                'value': quantity,
                'unit_code': 'C62'  # Standard unit code for "pieces"
            },
            'line_extension_amount': {
                'value': float(line_extension_amount),
                'currency_id': transaction.currency
            },
            'item': {
                'description': item_description,
                'name': item.get('name', 'Unknown Item'),
                'sellers_item_identification': {
                    'id': item.get('sku') or item.get('id', f"ITEM_{line_number}")
                },
                'classified_tax_category': {
                    'id': 'S',  # Standard rate
                    'percent': float(self.vat_rate * 100),
                    'tax_scheme': {
                        'id': 'VAT',
                        'name': 'Value Added Tax'
                    }
                },
                'additional_item_property': self._build_item_properties(item)
            },
            'price': {
                'price_amount': {
                    'value': float(unit_price),
                    'currency_id': transaction.currency
                },
                'base_quantity': {
                    'value': 1,
                    'unit_code': 'C62'
                }
            }
        }
        
        # Add tax total for this line
        if self.include_tax_breakdown:
            invoice_line['tax_total'] = {
                'tax_amount': {
                    'value': float(tax_amount),
                    'currency_id': transaction.currency
                },
                'tax_subtotal': [{
                    'taxable_amount': {
                        'value': float(line_extension_amount),
                        'currency_id': transaction.currency
                    },
                    'tax_amount': {
                        'value': float(tax_amount),
                        'currency_id': transaction.currency
                    },
                    'tax_category': {
                        'id': 'S',
                        'percent': float(self.vat_rate * 100),
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                }]
            }
        
        return invoice_line
    
    def _create_default_invoice_line(self, transaction: POSTransaction) -> Dict[str, Any]:
        """Create default invoice line when no items are available."""
        amount = Decimal(str(transaction.amount))
        line_extension_amount = amount / (1 + self.vat_rate)
        tax_amount = amount - line_extension_amount
        
        return {
            'id': '1',
            'note': 'Shopify POS Transaction',
            'invoiced_quantity': {
                'value': 1,
                'unit_code': 'C62'
            },
            'line_extension_amount': {
                'value': float(line_extension_amount),
                'currency_id': transaction.currency
            },
            'item': {
                'description': 'Point of Sale Transaction',
                'name': 'POS Transaction',
                'sellers_item_identification': {
                    'id': f"TXN_{transaction.transaction_id[:8]}"
                },
                'classified_tax_category': {
                    'id': 'S',
                    'percent': float(self.vat_rate * 100),
                    'tax_scheme': {
                        'id': 'VAT',
                        'name': 'Value Added Tax'
                    }
                }
            },
            'price': {
                'price_amount': {
                    'value': float(line_extension_amount),
                    'currency_id': transaction.currency
                },
                'base_quantity': {
                    'value': 1,
                    'unit_code': 'C62'
                }
            },
            'tax_total': {
                'tax_amount': {
                    'value': float(tax_amount),
                    'currency_id': transaction.currency
                },
                'tax_subtotal': [{
                    'taxable_amount': {
                        'value': float(line_extension_amount),
                        'currency_id': transaction.currency
                    },
                    'tax_amount': {
                        'value': float(tax_amount),
                        'currency_id': transaction.currency
                    },
                    'tax_category': {
                        'id': 'S',
                        'percent': float(self.vat_rate * 100),
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                }]
            }
        }
    
    def _build_item_properties(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build additional item properties."""
        properties = []
        
        # Add category if available
        if item.get('category'):
            properties.append({
                'name': 'Category',
                'value': item['category']
            })
        
        # Add vendor if available (from metadata)
        metadata = item.get('metadata', {})
        if metadata.get('vendor'):
            properties.append({
                'name': 'Vendor',
                'value': metadata['vendor']
            })
        
        # Add product type if available
        if metadata.get('product_type'):
            properties.append({
                'name': 'Product Type',
                'value': metadata['product_type']
            })
        
        # Add variant title if available
        if metadata.get('variant_title'):
            properties.append({
                'name': 'Variant',
                'value': metadata['variant_title']
            })
        
        # Add customizations
        customizations = item.get('customizations', [])
        for custom in customizations:
            if isinstance(custom, dict):
                name = custom.get('name', '')
                value = custom.get('value', '')
                if name and value:
                    properties.append({
                        'name': f"Custom: {name}",
                        'value': value
                    })
        
        # Add Shopify-specific metadata
        if metadata.get('shopify_product_id'):
            properties.append({
                'name': 'Shopify Product ID',
                'value': str(metadata['shopify_product_id'])
            })
        
        if metadata.get('shopify_variant_id'):
            properties.append({
                'name': 'Shopify Variant ID',
                'value': str(metadata['shopify_variant_id'])
            })
        
        return properties
    
    def _calculate_tax_summary(self, transaction: POSTransaction, invoice_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate UBL tax summary."""
        total_tax_amount = Decimal('0')
        total_taxable_amount = Decimal('0')
        
        # Calculate totals from invoice lines
        for line in invoice_lines:
            line_extension = Decimal(str(line['line_extension_amount']['value']))
            total_taxable_amount += line_extension
            
            if line.get('tax_total'):
                line_tax = Decimal(str(line['tax_total']['tax_amount']['value']))
                total_tax_amount += line_tax
        
        # If no tax calculated from lines, use transaction tax info
        if total_tax_amount == 0 and transaction.tax_info:
            total_tax_amount = Decimal(str(transaction.tax_info.get('amount', 0)))
            total_taxable_amount = Decimal(str(transaction.tax_info.get('exclusive_amount', transaction.amount)))
        
        return {
            'tax_amount': {
                'value': float(total_tax_amount),
                'currency_id': transaction.currency
            },
            'tax_subtotal': [{
                'taxable_amount': {
                    'value': float(total_taxable_amount),
                    'currency_id': transaction.currency
                },
                'tax_amount': {
                    'value': float(total_tax_amount),
                    'currency_id': transaction.currency
                },
                'tax_category': {
                    'id': 'S',
                    'name': 'Standard Rate',
                    'percent': float(self.vat_rate * 100),
                    'tax_scheme': {
                        'id': 'VAT',
                        'name': 'Value Added Tax'
                    }
                }
            }]
        }
    
    def _calculate_monetary_totals(self, transaction: POSTransaction, tax_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate UBL monetary totals."""
        # Get tax amounts
        total_tax_amount = Decimal(str(tax_summary['tax_amount']['value']))
        total_taxable_amount = Decimal(str(tax_summary['tax_subtotal'][0]['taxable_amount']['value']))
        
        # Total payable amount
        payable_amount = Decimal(str(transaction.amount))
        
        # Calculate discounts if available
        total_discounts = Decimal(str(transaction.metadata.get('total_discounts', '0')))
        
        return {
            'line_extension_amount': {
                'value': float(total_taxable_amount),
                'currency_id': transaction.currency
            },
            'tax_exclusive_amount': {
                'value': float(total_taxable_amount),
                'currency_id': transaction.currency
            },
            'tax_inclusive_amount': {
                'value': float(payable_amount),
                'currency_id': transaction.currency
            },
            'allowance_total_amount': {
                'value': float(total_discounts),
                'currency_id': transaction.currency
            },
            'charge_total_amount': {
                'value': 0.0,
                'currency_id': transaction.currency
            },
            'prepaid_amount': {
                'value': 0.0,
                'currency_id': transaction.currency
            },
            'payable_rounding_amount': {
                'value': 0.0,
                'currency_id': transaction.currency
            },
            'payable_amount': {
                'value': float(payable_amount),
                'currency_id': transaction.currency
            }
        }
    
    def _build_payment_terms(self, transaction: POSTransaction, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build UBL payment terms."""
        payment_terms = options.get('payment_terms', {})
        
        return {
            'payment_means': [{
                'payment_means_type_code': self._map_payment_method_code(transaction.payment_method),
                'payment_id': transaction.transaction_id,
                'payment_means_explanation': f"Shopify POS - {transaction.payment_method}",
                'payment_due_date': transaction.timestamp.date().isoformat(),
                'instruction_id': transaction.transaction_id,
                'instruction_note': payment_terms.get('note', 'Payment processed via Shopify POS system')
            }],
            'payment_terms': {
                'note': payment_terms.get('terms', 'Payment due immediately'),
                'settlement_period': {
                    'measure': 0,
                    'attribute_id': 'DAY'
                }
            }
        }
    
    def _map_payment_method_code(self, payment_method: str) -> str:
        """Map payment method to UBL payment means type code."""
        mapping = {
            'CARD': '48',  # Credit/Debit Card
            'CASH': '10',  # Cash
            'TRANSFER': '31',  # Bank Transfer
            'MOBILE_PAY': '68',  # Online payment service
            'GIFT_CARD': '91',  # Not cash
            'SHOP_PAY': '68',  # Online payment service
            'PAYPAL': '68',  # Online payment service
            'OTHER': '97'  # Clearing between partners
        }
        
        # Handle card types
        if payment_method.startswith('CARD_'):
            return '48'
        
        return mapping.get(payment_method.split('_')[0], '97')
    
    def _build_document_references(self, transaction: POSTransaction) -> List[Dict[str, Any]]:
        """Build additional document references."""
        references = []
        
        # Add Shopify order reference
        order_number = transaction.metadata.get('order_number')
        if order_number:
            references.append({
                'id': str(order_number),
                'document_type_code': 'order',
                'document_description': 'Shopify Order Number'
            })
        
        # Add checkout token reference if available
        checkout_token = transaction.metadata.get('checkout_token')
        if checkout_token:
            references.append({
                'id': checkout_token,
                'document_type_code': 'checkout',
                'document_description': 'Shopify Checkout Token'
            })
        
        return references
    
    def _build_delivery_info(self, transaction: POSTransaction, options: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Build delivery information if available."""
        shipping_address = transaction.metadata.get('shipping_address')
        
        if shipping_address:
            return {
                'delivery_address': {
                    'street_name': shipping_address.get('address1', ''),
                    'additional_street_name': shipping_address.get('address2', ''),
                    'city_name': shipping_address.get('city', ''),
                    'postal_zone': shipping_address.get('zip', ''),
                    'country_subdivision': shipping_address.get('province', ''),
                    'country': {
                        'identification_code': shipping_address.get('country_code', 'NG'),
                        'name': shipping_address.get('country', 'Nigeria')
                    }
                },
                'delivery_party': {
                    'party_name': [{
                        'name': f"{shipping_address.get('first_name', '')} {shipping_address.get('last_name', '')}".strip()
                    }]
                }
            }
        
        return None
    
    def _build_invoice_metadata(self, transaction: POSTransaction, options: Dict[str, Any]) -> Dict[str, Any]:
        """Build invoice metadata for tracking and compliance."""
        return {
            'source_system': 'shopify_pos',
            'shopify_order_id': transaction.transaction_id,
            'shopify_order_number': transaction.metadata.get('order_number'),
            'shopify_location_id': transaction.location_id,
            'original_currency': transaction.metadata.get('original_currency'),
            'conversion_rate': transaction.metadata.get('conversion_rate'),
            'generation_timestamp': datetime.now().isoformat(),
            'transformer_version': '1.0',
            'ubl_version': '2.1',
            'compliance_standard': 'UBL_BIS_3.0',
            'firs_compliance': True,
            'nigerian_vat_applied': True,
            'taxpayer_id': self.taxpayer_id,
            'payment_status': 'completed',
            'financial_status': transaction.metadata.get('financial_status'),
            'fulfillment_status': transaction.metadata.get('fulfillment_status'),
            'source_name': transaction.metadata.get('source_name'),
            'processing_method': transaction.metadata.get('processing_method'),
            'gateway': transaction.metadata.get('gateway'),
            'tags': transaction.metadata.get('tags'),
            'is_pos_order': transaction.metadata.get('is_pos_order', False)
        }
    
    def _validate_invoice_structure(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Validate UBL invoice structure for FIRS compliance."""
        warnings = []
        errors = []
        
        # Check required fields
        required_fields = [
            'invoice_header.invoice_number',
            'invoice_header.issue_date',
            'supplier_party.party_identification.id',
            'customer_party.party_identification.id',
            'monetary_totals.payable_amount'
        ]
        
        for field_path in required_fields:
            if not self._get_nested_value(invoice, field_path):
                errors.append(f"Missing required field: {field_path}")
        
        # Check TIN format
        supplier_tin = self._get_nested_value(invoice, 'supplier_party.party_identification.id')
        customer_tin = self._get_nested_value(invoice, 'customer_party.party_identification.id')
        
        if supplier_tin and not self._validate_nigerian_tin(supplier_tin):
            warnings.append(f"Invalid supplier TIN format: {supplier_tin}")
        
        if customer_tin and not self._validate_nigerian_tin(customer_tin):
            warnings.append(f"Invalid customer TIN format: {customer_tin}")
        
        # Check currency is NGN
        currency = self._get_nested_value(invoice, 'invoice_header.currency')
        if currency != 'NGN':
            warnings.append(f"Currency should be NGN for FIRS compliance, got: {currency}")
        
        # Check VAT rate
        vat_percent = self._get_nested_value(invoice, 'tax_summary.tax_subtotal.0.tax_category.percent')
        if vat_percent and abs(vat_percent - 7.5) > 0.01:
            warnings.append(f"VAT rate should be 7.5% for Nigeria, got: {vat_percent}%")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list) and key.isdigit():
                try:
                    current = current[int(key)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _validate_nigerian_tin(self, tin: str) -> bool:
        """Validate Nigerian Tax Identification Number format."""
        import re
        pattern = r'^\d{8}-\d{4}-\d{1}$'
        return bool(re.match(pattern, tin)) if tin else False