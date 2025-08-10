"""
Zoho CRM Deal Transformation Module
Handles transformation of Zoho CRM deal data to invoice formats for FIRS compliance.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from ....connector_framework import CRMDataError


class ZohoCRMDealTransformer:
    """
    Transforms Zoho CRM deal data to invoice formats.
    Handles UBL BIS 3.0 compliance and FIRS e-invoicing requirements.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Zoho CRM deal transformer.
        
        Args:
            config: Transformation configuration including tax settings and compliance rules
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Tax configuration
        self.default_tax_rate = config.get('default_tax_rate', 0.075)  # 7.5% VAT in Nigeria
        self.tax_inclusive = config.get('tax_inclusive', False)
        
        # Invoice configuration
        self.invoice_prefix = config.get('invoice_prefix', 'ZHO')
        self.currency_code = config.get('default_currency', 'NGN')
        
        # Compliance settings
        self.firs_tin_required = config.get('firs_tin_required', True)
        self.validate_amounts = config.get('validate_amounts', True)

    def transform_deal_to_invoice(
        self,
        deal: Dict[str, Any],
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Zoho CRM deal to UBL BIS 3.0 compliant invoice.
        
        Args:
            deal: Zoho CRM deal data
            transformation_options: Additional transformation settings
        
        Returns:
            UBL BIS 3.0 compliant invoice data
        """
        try:
            options = transformation_options or {}
            
            # Extract basic deal information
            deal_id = deal.get('id')
            if not deal_id:
                raise CRMDataError("Deal ID is required for transformation")
            
            # Generate invoice number
            invoice_number = self._generate_invoice_number(deal, options)
            
            # Transform customer information
            customer_data = self._transform_customer_data(deal)
            
            # Transform line items
            line_items = self._transform_line_items(deal)
            
            # Calculate totals
            totals = self._calculate_totals(line_items, deal)
            
            # Transform currency information
            currency_data = self._transform_currency_data(deal)
            
            # Build UBL invoice structure
            invoice_data = {
                'ubl_version': '2.1',
                'customization_id': 'urn:cen.eu:en16931:2017#compliant#urn:fdc:peppol.eu:2017:poacc:billing:3.0',
                'profile_id': 'urn:fdc:peppol.eu:2017:poacc:billing:01:1.0',
                'id': invoice_number,
                'issue_date': options.get('issue_date', datetime.now().strftime('%Y-%m-%d')),
                'due_date': options.get('due_date', self._calculate_due_date()),
                'invoice_type_code': options.get('invoice_type_code', '380'),  # Commercial invoice
                'document_currency_code': currency_data['code'],
                'tax_currency_code': currency_data['code'],
                'buyer_reference': deal.get('name', ''),
                'order_reference': {
                    'id': deal_id
                },
                'accounting_supplier_party': self._get_supplier_party_data(options),
                'accounting_customer_party': customer_data,
                'payment_means': self._get_payment_means(options),
                'tax_total': totals['tax_total'],
                'legal_monetary_total': totals['monetary_total'],
                'invoice_lines': line_items,
                'additional_document_reference': [
                    {
                        'id': deal_id,
                        'document_type_code': 'CRM_DEAL',
                        'document_description': f"Zoho CRM Deal: {deal.get('name', '')}"
                    }
                ],
                'source_system': {
                    'name': 'Zoho CRM',
                    'version': 'API v2',
                    'deal_id': deal_id,
                    'deal_stage': deal.get('stage'),
                    'deal_url': f"https://crm.zoho.com/crm/org/deals/{deal_id}/view"
                }
            }
            
            # Add Nigerian-specific fields if configured
            if self.firs_tin_required:
                invoice_data['firs_metadata'] = self._get_firs_metadata(deal, options)
            
            # Validate the transformed invoice
            if self.validate_amounts:
                self._validate_invoice_amounts(invoice_data)
            
            self.logger.info(f"Successfully transformed Zoho CRM deal {deal_id} to invoice")
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"Error transforming deal to invoice: {str(e)}")
            raise CRMDataError(f"Failed to transform deal to invoice: {str(e)}")

    def _transform_customer_data(self, deal: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Zoho CRM customer data to UBL customer party format."""
        account_info = deal.get('account', {})
        contact_info = deal.get('contact', {})
        
        # Determine primary customer info
        customer_name = account_info.get('name') or contact_info.get('name')
        customer_id = account_info.get('id') or contact_info.get('id')
        
        if not customer_name:
            raise CRMDataError("Customer information is required for invoice transformation")
        
        # Build customer party
        customer_party = {
            'party': {
                'endpoint_id': {
                    'scheme_id': 'ZOHO_CRM_ID',
                    'value': customer_id or ''
                },
                'party_identification': [
                    {
                        'id': customer_id or '',
                        'scheme_id': 'ZOHO_CRM_ID'
                    }
                ],
                'party_name': [
                    {
                        'name': customer_name
                    }
                ],
                'postal_address': {
                    'street_name': '',
                    'city_name': '',
                    'postal_zone': '',
                    'country_subentity': '',
                    'country': {
                        'identification_code': 'NG',
                        'name': 'Nigeria'
                    }
                },
                'party_tax_scheme': [
                    {
                        'company_id': '',
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                ],
                'party_legal_entity': [
                    {
                        'registration_name': customer_name,
                        'company_id': ''
                    }
                ],
                'contact': {
                    'id': customer_id or '',
                    'name': customer_name,
                    'telephone': '',
                    'electronic_mail': ''
                }
            }
        }
        
        return customer_party

    def _transform_line_items(self, deal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Zoho CRM deal products to UBL invoice lines."""
        products = deal.get('products', [])
        
        if not products:
            # Create a single line item from deal amount
            return self._create_summary_line_item(deal)
        
        ubl_lines = []
        
        for index, product in enumerate(products):
            # Calculate line totals
            quantity = float(product.get('quantity', 1))
            unit_price = float(product.get('unit_price', 0))
            discount_amount = float(product.get('discount', 0))
            tax_amount = float(product.get('tax', 0))
            net_total = float(product.get('net_total', 0))
            
            # Calculate line extension amount
            line_extension_amount = quantity * unit_price - discount_amount
            
            # If no tax provided, calculate it
            if tax_amount == 0 and not self.tax_inclusive:
                tax_amount = line_extension_amount * self.default_tax_rate
            
            ubl_line = {
                'id': str(index + 1),
                'note': product.get('name', ''),
                'invoiced_quantity': {
                    'unit_code': 'C62',  # Default unit: piece
                    'value': quantity
                },
                'line_extension_amount': {
                    'currency_id': self.currency_code,
                    'value': round(line_extension_amount, 2)
                },
                'allowance_charge': [],
                'tax_total': [
                    {
                        'tax_amount': {
                            'currency_id': self.currency_code,
                            'value': round(tax_amount, 2)
                        },
                        'tax_subtotal': [
                            {
                                'taxable_amount': {
                                    'currency_id': self.currency_code,
                                    'value': round(line_extension_amount, 2)
                                },
                                'tax_amount': {
                                    'currency_id': self.currency_code,
                                    'value': round(tax_amount, 2)
                                },
                                'tax_category': {
                                    'id': 'S',  # Standard rate
                                    'percent': self.default_tax_rate * 100,
                                    'tax_scheme': {
                                        'id': 'VAT',
                                        'name': 'Value Added Tax'
                                    }
                                }
                            }
                        ]
                    }
                ],
                'item': {
                    'description': [product.get('name', '')],
                    'name': product.get('name', ''),
                    'sellers_item_identification': {
                        'id': product.get('id', '')
                    },
                    'classified_tax_category': [
                        {
                            'id': 'S',
                            'percent': self.default_tax_rate * 100,
                            'tax_scheme': {
                                'id': 'VAT',
                                'name': 'Value Added Tax'
                            }
                        }
                    ]
                },
                'price': {
                    'price_amount': {
                        'currency_id': self.currency_code,
                        'value': round(unit_price, 2)
                    },
                    'base_quantity': {
                        'unit_code': 'C62',
                        'value': 1
                    }
                }
            }
            
            # Add discount if present
            if discount_amount > 0:
                ubl_line['allowance_charge'].append({
                    'charge_indicator': False,  # False for allowance (discount)
                    'allowance_charge_reason_code': 'TD',  # Trade discount
                    'allowance_charge_reason': 'Deal Discount',
                    'amount': {
                        'currency_id': self.currency_code,
                        'value': round(discount_amount, 2)
                    }
                })
            
            ubl_lines.append(ubl_line)
        
        return ubl_lines

    def _create_summary_line_item(self, deal: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a summary line item when no products exist."""
        amount = float(deal.get('amount', 0))
        
        if amount <= 0:
            raise CRMDataError("Deal must have an amount greater than zero")
        
        # Calculate tax
        if self.tax_inclusive:
            line_extension_amount = amount / (1 + self.default_tax_rate)
            tax_amount = amount - line_extension_amount
        else:
            line_extension_amount = amount
            tax_amount = amount * self.default_tax_rate
        
        return [{
            'id': '1',
            'note': deal.get('description', ''),
            'invoiced_quantity': {
                'unit_code': 'C62',
                'value': 1
            },
            'line_extension_amount': {
                'currency_id': self.currency_code,
                'value': round(line_extension_amount, 2)
            },
            'tax_total': [
                {
                    'tax_amount': {
                        'currency_id': self.currency_code,
                        'value': round(tax_amount, 2)
                    },
                    'tax_subtotal': [
                        {
                            'taxable_amount': {
                                'currency_id': self.currency_code,
                                'value': round(line_extension_amount, 2)
                            },
                            'tax_amount': {
                                'currency_id': self.currency_code,
                                'value': round(tax_amount, 2)
                            },
                            'tax_category': {
                                'id': 'S',
                                'percent': self.default_tax_rate * 100,
                                'tax_scheme': {
                                    'id': 'VAT',
                                    'name': 'Value Added Tax'
                                }
                            }
                        }
                    ]
                }
            ],
            'item': {
                'description': [deal.get('description', deal.get('name', ''))],
                'name': deal.get('name', ''),
                'classified_tax_category': [
                    {
                        'id': 'S',
                        'percent': self.default_tax_rate * 100,
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                ]
            },
            'price': {
                'price_amount': {
                    'currency_id': self.currency_code,
                    'value': round(line_extension_amount, 2)
                },
                'base_quantity': {
                    'unit_code': 'C62',
                    'value': 1
                }
            }
        }]

    def _calculate_totals(self, line_items: List[Dict[str, Any]], deal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate invoice totals from line items."""
        line_extension_total = sum(
            float(line['line_extension_amount']['value']) 
            for line in line_items
        )
        
        tax_exclusive_amount = line_extension_total
        
        # Calculate total discounts
        total_allowance = sum(
            sum(float(charge['amount']['value']) for charge in line.get('allowance_charge', []) if not charge['charge_indicator'])
            for line in line_items
        )
        
        # Calculate total charges
        total_charge = sum(
            sum(float(charge['amount']['value']) for charge in line.get('allowance_charge', []) if charge['charge_indicator'])
            for line in line_items
        )
        
        # Calculate total tax
        total_tax = sum(
            float(line['tax_total'][0]['tax_amount']['value'])
            for line in line_items
        )
        
        tax_inclusive_amount = tax_exclusive_amount + total_tax
        
        return {
            'tax_total': [
                {
                    'tax_amount': {
                        'currency_id': self.currency_code,
                        'value': round(total_tax, 2)
                    },
                    'tax_subtotal': [
                        {
                            'taxable_amount': {
                                'currency_id': self.currency_code,
                                'value': round(tax_exclusive_amount, 2)
                            },
                            'tax_amount': {
                                'currency_id': self.currency_code,
                                'value': round(total_tax, 2)
                            },
                            'tax_category': {
                                'id': 'S',
                                'percent': self.default_tax_rate * 100,
                                'tax_scheme': {
                                    'id': 'VAT',
                                    'name': 'Value Added Tax'
                                }
                            }
                        }
                    ]
                }
            ],
            'monetary_total': {
                'line_extension_amount': {
                    'currency_id': self.currency_code,
                    'value': round(line_extension_total, 2)
                },
                'tax_exclusive_amount': {
                    'currency_id': self.currency_code,
                    'value': round(tax_exclusive_amount, 2)
                },
                'tax_inclusive_amount': {
                    'currency_id': self.currency_code,
                    'value': round(tax_inclusive_amount, 2)
                },
                'allowance_total_amount': {
                    'currency_id': self.currency_code,
                    'value': round(total_allowance, 2)
                },
                'charge_total_amount': {
                    'currency_id': self.currency_code,
                    'value': round(total_charge, 2)
                },
                'payable_amount': {
                    'currency_id': self.currency_code,
                    'value': round(tax_inclusive_amount, 2)
                }
            }
        }

    def _transform_currency_data(self, deal: Dict[str, Any]) -> Dict[str, str]:
        """Transform currency information."""
        currency = deal.get('currency', self.currency_code)
        exchange_rate = deal.get('exchange_rate', 1)
        
        return {
            'code': currency,
            'name': self._get_currency_name(currency),
            'symbol': self._get_currency_symbol(currency),
            'exchange_rate': exchange_rate
        }

    def _get_currency_name(self, currency_code: str) -> str:
        """Get currency name from code."""
        currency_names = {
            'NGN': 'Nigerian Naira',
            'USD': 'US Dollar',
            'EUR': 'Euro',
            'GBP': 'British Pound',
            'ZAR': 'South African Rand'
        }
        return currency_names.get(currency_code, currency_code)

    def _get_currency_symbol(self, currency_code: str) -> str:
        """Get currency symbol from code."""
        currency_symbols = {
            'NGN': '₦',
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'ZAR': 'R'
        }
        return currency_symbols.get(currency_code, currency_code)

    def _generate_invoice_number(self, deal: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Generate unique invoice number."""
        if 'invoice_number' in options:
            return options['invoice_number']
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        deal_id = deal.get('id', '')[:8]
        
        return f"{self.invoice_prefix}-{deal_id}-{timestamp}"

    def _calculate_due_date(self) -> str:
        """Calculate invoice due date."""
        from datetime import timedelta
        due_date = datetime.now() + timedelta(days=30)  # Default 30 days
        return due_date.strftime('%Y-%m-%d')

    def _get_supplier_party_data(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get supplier party data from configuration."""
        supplier_config = self.config.get('supplier_party', {})
        
        return {
            'party': {
                'endpoint_id': {
                    'scheme_id': 'TIN',
                    'value': supplier_config.get('tin', '')
                },
                'party_identification': [
                    {
                        'id': supplier_config.get('company_id', ''),
                        'scheme_id': 'COMPANY_ID'
                    }
                ],
                'party_name': [
                    {
                        'name': supplier_config.get('name', '')
                    }
                ],
                'postal_address': supplier_config.get('address', {}),
                'party_tax_scheme': [
                    {
                        'company_id': supplier_config.get('tin', ''),
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                ],
                'party_legal_entity': [
                    {
                        'registration_name': supplier_config.get('legal_name', supplier_config.get('name', '')),
                        'company_id': supplier_config.get('registration_number', '')
                    }
                ],
                'contact': supplier_config.get('contact', {})
            }
        }

    def _get_payment_means(self, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get payment means configuration."""
        payment_config = self.config.get('payment_means', {})
        
        return [
            {
                'payment_means_code': payment_config.get('code', '31'),  # Credit transfer
                'payment_due_date': options.get('due_date', self._calculate_due_date()),
                'payee_financial_account': {
                    'id': payment_config.get('account_number', ''),
                    'name': payment_config.get('account_name', ''),
                    'financial_institution_branch': {
                        'id': payment_config.get('bank_code', ''),
                        'name': payment_config.get('bank_name', '')
                    }
                }
            }
        ]

    def _get_firs_metadata(self, deal: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Get FIRS-specific metadata for Nigerian compliance."""
        return {
            'taxpayer_tin': self.config.get('supplier_party', {}).get('tin', ''),
            'invoice_category': 'STANDARD',
            'invoice_type': 'SALES',
            'currency_code': self.currency_code,
            'source_system': 'ZOHO_CRM',
            'validation_status': 'PENDING',
            'submission_id': f"ZHO-{deal.get('id', '')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    def _validate_invoice_amounts(self, invoice_data: Dict[str, Any]) -> None:
        """Validate invoice amounts for consistency."""
        monetary_total = invoice_data['legal_monetary_total']
        tax_total = invoice_data['tax_total'][0]
        
        # Validate tax calculation
        expected_tax = float(monetary_total['tax_exclusive_amount']['value']) * self.default_tax_rate
        actual_tax = float(tax_total['tax_amount']['value'])
        
        if abs(expected_tax - actual_tax) > 0.01:  # Allow for rounding differences
            self.logger.warning(f"Tax calculation mismatch: expected {expected_tax}, actual {actual_tax}")
        
        # Validate payable amount
        expected_payable = (
            float(monetary_total['tax_exclusive_amount']['value']) + 
            float(tax_total['tax_amount']['value'])
        )
        actual_payable = float(monetary_total['payable_amount']['value'])
        
        if abs(expected_payable - actual_payable) > 0.01:
            raise CRMDataError(f"Payable amount mismatch: expected {expected_payable}, actual {actual_payable}")