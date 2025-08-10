"""
Microsoft Dynamics CRM Deal Transformation Module
Handles transformation of Dynamics CRM opportunity data to invoice formats for FIRS compliance.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from ....connector_framework import CRMDataError


class DynamicsCRMDealTransformer:
    """
    Transforms Microsoft Dynamics CRM opportunity data to invoice formats.
    Handles UBL BIS 3.0 compliance and FIRS e-invoicing requirements.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Dynamics CRM deal transformer.
        
        Args:
            config: Transformation configuration including tax settings and compliance rules
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Tax configuration
        self.default_tax_rate = config.get('default_tax_rate', 0.075)  # 7.5% VAT in Nigeria
        self.tax_inclusive = config.get('tax_inclusive', False)
        
        # Invoice configuration
        self.invoice_prefix = config.get('invoice_prefix', 'DYN')
        self.currency_code = config.get('default_currency', 'NGN')
        
        # Compliance settings
        self.firs_tin_required = config.get('firs_tin_required', True)
        self.validate_amounts = config.get('validate_amounts', True)

    def transform_opportunity_to_invoice(
        self,
        opportunity: Dict[str, Any],
        transformation_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Transform Dynamics CRM opportunity to UBL BIS 3.0 compliant invoice.
        
        Args:
            opportunity: Dynamics CRM opportunity data
            transformation_options: Additional transformation settings
        
        Returns:
            UBL BIS 3.0 compliant invoice data
        """
        try:
            options = transformation_options or {}
            
            # Extract basic opportunity information
            opportunity_id = opportunity.get('opportunityid')
            if not opportunity_id:
                raise CRMDataError("Opportunity ID is required for transformation")
            
            # Generate invoice number
            invoice_number = self._generate_invoice_number(opportunity, options)
            
            # Transform customer information
            customer_data = self._transform_customer_data(opportunity)
            
            # Transform line items
            line_items = self._transform_line_items(opportunity)
            
            # Calculate totals
            totals = self._calculate_totals(line_items, opportunity)
            
            # Transform currency and exchange rate
            currency_data = self._transform_currency_data(opportunity)
            
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
                'buyer_reference': opportunity.get('name', ''),
                'order_reference': {
                    'id': opportunity_id
                },
                'accounting_supplier_party': self._get_supplier_party_data(options),
                'accounting_customer_party': customer_data,
                'payment_means': self._get_payment_means(options),
                'tax_total': totals['tax_total'],
                'legal_monetary_total': totals['monetary_total'],
                'invoice_lines': line_items,
                'additional_document_reference': [
                    {
                        'id': opportunity_id,
                        'document_type_code': 'CRM_OPPORTUNITY',
                        'document_description': f"Microsoft Dynamics CRM Opportunity: {opportunity.get('name', '')}"
                    }
                ],
                'source_system': {
                    'name': 'Microsoft Dynamics CRM',
                    'version': 'Web API v9.2',
                    'opportunity_id': opportunity_id,
                    'opportunity_url': f"{self.config.get('environment_url', '')}/main.aspx?etn=opportunity&id={opportunity_id}"
                }
            }
            
            # Add Nigerian-specific fields if configured
            if self.firs_tin_required:
                invoice_data['firs_metadata'] = self._get_firs_metadata(opportunity, options)
            
            # Validate the transformed invoice
            if self.validate_amounts:
                self._validate_invoice_amounts(invoice_data)
            
            self.logger.info(f"Successfully transformed Dynamics CRM opportunity {opportunity_id} to invoice")
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"Error transforming opportunity to invoice: {str(e)}")
            raise CRMDataError(f"Failed to transform opportunity to invoice: {str(e)}")

    def _transform_customer_data(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Dynamics CRM customer data to UBL customer party format."""
        customer_info = opportunity.get('customer', {})
        
        if not customer_info:
            raise CRMDataError("Customer information is required for invoice transformation")
        
        # Extract address information
        address_data = self._parse_address(customer_info.get('address', ''))
        
        customer_party = {
            'party': {
                'endpoint_id': {
                    'scheme_id': 'DYNAMICS_CRM_ID',
                    'value': customer_info.get('id', '')
                },
                'party_identification': [
                    {
                        'id': customer_info.get('id', ''),
                        'scheme_id': 'DYNAMICS_CRM_ID'
                    }
                ],
                'party_name': [
                    {
                        'name': customer_info.get('name', '')
                    }
                ],
                'postal_address': {
                    'street_name': address_data.get('street_name', ''),
                    'additional_street_name': address_data.get('additional_street', ''),
                    'city_name': address_data.get('city', ''),
                    'postal_zone': address_data.get('postal_code', ''),
                    'country_subentity': address_data.get('state', ''),
                    'country': {
                        'identification_code': address_data.get('country_code', 'NG'),
                        'name': address_data.get('country', 'Nigeria')
                    }
                },
                'party_tax_scheme': [
                    {
                        'company_id': customer_info.get('tax_id', ''),
                        'tax_scheme': {
                            'id': 'VAT',
                            'name': 'Value Added Tax'
                        }
                    }
                ],
                'party_legal_entity': [
                    {
                        'registration_name': customer_info.get('name', ''),
                        'company_id': customer_info.get('registration_number', '')
                    }
                ],
                'contact': {
                    'id': customer_info.get('id', ''),
                    'name': customer_info.get('name', ''),
                    'telephone': customer_info.get('phone', ''),
                    'electronic_mail': customer_info.get('email', '')
                }
            }
        }
        
        return customer_party

    def _transform_line_items(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Dynamics CRM opportunity line items to UBL invoice lines."""
        raw_line_items = opportunity.get('line_items', [])
        
        if not raw_line_items:
            # Create a single line item from opportunity total
            return self._create_summary_line_item(opportunity)
        
        ubl_lines = []
        
        for index, item in enumerate(raw_line_items):
            # Calculate line totals
            quantity = float(item.get('quantity', 1))
            unit_price = float(item.get('unit_price', 0))
            discount_amount = float(item.get('discount', 0))
            
            line_extension_amount = quantity * unit_price - discount_amount
            
            # Tax calculation
            tax_amount = float(item.get('tax', 0))
            if tax_amount == 0 and not self.tax_inclusive:
                tax_amount = line_extension_amount * self.default_tax_rate
            
            ubl_line = {
                'id': str(index + 1),
                'note': item.get('description', ''),
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
                    'description': [item.get('description', '')],
                    'name': item.get('product', {}).get('name', item.get('description', '')),
                    'sellers_item_identification': {
                        'id': item.get('product', {}).get('id', item.get('id', ''))
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
                    'allowance_charge_reason': 'Opportunity Discount',
                    'amount': {
                        'currency_id': self.currency_code,
                        'value': round(discount_amount, 2)
                    }
                })
            
            ubl_lines.append(ubl_line)
        
        return ubl_lines

    def _create_summary_line_item(self, opportunity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create a summary line item when no detailed line items exist."""
        total_amount = float(opportunity.get('total_amount', 0))
        
        if total_amount <= 0:
            raise CRMDataError("Opportunity must have a total amount greater than zero")
        
        # Calculate tax
        if self.tax_inclusive:
            line_extension_amount = total_amount / (1 + self.default_tax_rate)
            tax_amount = total_amount - line_extension_amount
        else:
            line_extension_amount = total_amount
            tax_amount = total_amount * self.default_tax_rate
        
        return [{
            'id': '1',
            'note': opportunity.get('description', ''),
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
                'description': [opportunity.get('description', opportunity.get('name', ''))],
                'name': opportunity.get('name', ''),
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

    def _calculate_totals(self, line_items: List[Dict[str, Any]], opportunity: Dict[str, Any]) -> Dict[str, Any]:
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

    def _transform_currency_data(self, opportunity: Dict[str, Any]) -> Dict[str, str]:
        """Transform currency information."""
        currency_info = opportunity.get('currency', {})
        
        return {
            'code': currency_info.get('name', self.currency_code),
            'name': currency_info.get('name', 'Nigerian Naira'),
            'symbol': currency_info.get('symbol', '₦'),
            'exchange_rate': currency_info.get('exchange_rate', 1)
        }

    def _generate_invoice_number(self, opportunity: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Generate unique invoice number."""
        if 'invoice_number' in options:
            return options['invoice_number']
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        opportunity_id = opportunity.get('opportunityid', '')[:8]
        
        return f"{self.invoice_prefix}-{opportunity_id}-{timestamp}"

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

    def _get_firs_metadata(self, opportunity: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Get FIRS-specific metadata for Nigerian compliance."""
        return {
            'taxpayer_tin': self.config.get('supplier_party', {}).get('tin', ''),
            'invoice_category': 'STANDARD',
            'invoice_type': 'SALES',
            'currency_code': self.currency_code,
            'source_system': 'DYNAMICS_CRM',
            'validation_status': 'PENDING',
            'submission_id': f"DYN-{opportunity.get('opportunityid', '')}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    def _parse_address(self, address_string: str) -> Dict[str, str]:
        """Parse address string into components."""
        if not address_string:
            return {}
        
        # Simple address parsing - can be enhanced based on format
        parts = address_string.split(',')
        
        return {
            'street_name': parts[0].strip() if len(parts) > 0 else '',
            'city': parts[-2].strip() if len(parts) > 1 else '',
            'state': parts[-1].strip() if len(parts) > 2 else '',
            'country': 'Nigeria',
            'country_code': 'NG'
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