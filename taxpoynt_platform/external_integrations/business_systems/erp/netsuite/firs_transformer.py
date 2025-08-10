"""
NetSuite FIRS Transformation Module
Handles transformation of NetSuite invoice data to FIRS-compliant formats.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from ....connector_framework import ERPDataError
from .exceptions import NetSuiteDataError

logger = logging.getLogger(__name__)


class NetSuiteFIRSTransformer:
    """Handles transformation of NetSuite data to FIRS-compliant formats."""
    
    def __init__(self, data_extractor):
        """Initialize with a data extractor instance."""
        self.data_extractor = data_extractor
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform NetSuite invoice data to FIRS-compliant format"""
        try:
            # Determine document type mapping
            firs_doc_type = self._map_netsuite_type_to_firs(
                invoice_data.get('move_type', 'out_invoice')
            )
            
            # Basic UBL BIS 3.0 transformation
            firs_invoice = {
                'invoice_type_code': firs_doc_type,
                'id': invoice_data.get('name', invoice_data.get('invoice_number', invoice_data.get('id', ''))),
                'issue_date': invoice_data.get('invoice_date', ''),
                'due_date': invoice_data.get('due_date', ''),
                'document_currency_code': invoice_data.get('currency', 'USD'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('company', {}).get('subsidiary_name', 'NetSuite Company')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('company', {}).get('tax_id', ''),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('partner', {}).get('name', 'NetSuite Customer')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('partner', {}).get('tax_registration_number', ''),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data.get('amount_excluding_tax', 0),
                    'tax_exclusive_amount': invoice_data.get('amount_excluding_tax', 0),
                    'tax_inclusive_amount': invoice_data.get('amount_including_tax', 0),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data.get('amount_including_tax', 0)
                },
                'invoice_line': []
            }
            
            # Transform invoice lines
            invoice_lines = invoice_data.get('invoice_lines', [])
            
            # If no line items available, create a summary line item
            if not invoice_lines:
                summary_line = {
                    'id': '1',
                    'invoiced_quantity': {
                        'quantity': 1,
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': invoice_data.get('amount_excluding_tax', 0),
                    'item': {
                        'description': f\"NetSuite {invoice_data.get('source', '')} - {invoice_data.get('name', 'Invoice')}\",
                        'name': invoice_data.get('netsuite_status', 'Service'),
                        'sellers_item_identification': {
                            'id': invoice_data.get('netsuite_invoice_id', '')
                        }
                    },
                    'price': {
                        'price_amount': invoice_data.get('amount_excluding_tax', 0),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                
                # Add tax information
                tax_amount = invoice_data.get('amount_tax', 0)
                if tax_amount > 0:
                    summary_line['tax_total'] = {
                        'tax_amount': tax_amount,
                        'tax_subtotal': [{
                            'taxable_amount': invoice_data.get('amount_excluding_tax', 0),
                            'tax_amount': tax_amount,
                            'tax_category': {
                                'id': 'S',  # Standard rate
                                'percent': self._calculate_tax_rate(
                                    invoice_data.get('amount_excluding_tax', 0), 
                                    tax_amount
                                ),
                                'tax_scheme': {
                                    'id': 'VAT'
                                }
                            }
                        }]
                    }
                
                firs_invoice['invoice_line'].append(summary_line)
            else:
                # Transform actual line items
                for line in invoice_lines:
                    firs_line = {
                        'id': str(line.get('id', line.get('line_number', 1))),
                        'invoiced_quantity': {
                            'quantity': line.get('quantity', 1),
                            'unit_code': 'C62'  # Default unit code
                        },
                        'line_extension_amount': line.get('line_amount', 0),
                        'item': {
                            'description': line.get('description', line.get('item_name', '')),
                            'name': line.get('item_name', line.get('item_id', '')),
                            'sellers_item_identification': {
                                'id': line.get('item_id', '')
                            }
                        },
                        'price': {
                            'price_amount': line.get('unit_price', 0),
                            'base_quantity': {
                                'quantity': 1,
                                'unit_code': 'C62'
                            }
                        }
                    }
                    
                    # Add tax information if available
                    tax_amount = line.get('tax_amount', 0)
                    if tax_amount > 0:
                        firs_line['tax_total'] = {
                            'tax_amount': tax_amount,
                            'tax_subtotal': [{
                                'taxable_amount': line.get('line_amount', 0),
                                'tax_amount': tax_amount,
                                'tax_category': {
                                    'id': 'S',  # Standard rate
                                    'percent': self._calculate_tax_rate(
                                        line.get('line_amount', 0), 
                                        tax_amount
                                    ),
                                    'tax_scheme': {
                                        'id': 'VAT'
                                    }
                                }
                            }]
                        }
                    
                    firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals
            total_tax = invoice_data.get('amount_tax', 0)
            if total_tax > 0:
                firs_invoice['tax_total'] = {
                    'tax_amount': total_tax,
                    'tax_subtotal': [{
                        'taxable_amount': invoice_data.get('amount_excluding_tax', 0),
                        'tax_amount': total_tax,
                        'tax_category': {
                            'id': 'S',
                            'percent': self._calculate_tax_rate(
                                invoice_data.get('amount_excluding_tax', 0), 
                                total_tax
                            ),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }]
                }
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'netsuite_native',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('id'),
                    'netsuite_invoice_id': invoice_data.get('netsuite_invoice_id', ''),
                    'netsuite_tran_id': invoice_data.get('netsuite_tran_id', ''),
                    'netsuite_status': invoice_data.get('netsuite_status', ''),
                    'erp_type': 'netsuite',
                    'data_source': invoice_data.get('source', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming NetSuite invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming NetSuite invoice to FIRS format: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate NetSuite invoice data before FIRS submission.
        
        Args:
            invoice_data: Invoice data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'invoice_id': invoice_data.get('id')
            }
            
            # Required field validations
            required_fields = ['id', 'name']
            
            for field in required_fields:
                if not invoice_data.get(field):
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
            
            # Date validation
            date_fields = ['invoice_date']
            has_valid_date = False
            
            for date_field in date_fields:
                date_value = invoice_data.get(date_field)
                if date_value:
                    try:
                        datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                        has_valid_date = True
                        break
                    except ValueError:
                        validation_result['warnings'].append(f"Invalid {date_field} format: {date_value}")
            
            if not has_valid_date:
                validation_result['errors'].append("No valid invoice date found")
                validation_result['is_valid'] = False
            
            # Amount validation
            amount_fields = ['amount_including_tax', 'amount_excluding_tax']
            has_valid_amount = False
            
            for amount_field in amount_fields:
                amount = invoice_data.get(amount_field)
                if amount is not None:
                    try:
                        amount_value = float(amount)
                        if amount_value > 0:
                            has_valid_amount = True
                            break
                        elif amount_value < 0:
                            validation_result['warnings'].append(f"Negative amount detected: {amount_value}")
                    except (ValueError, TypeError):
                        validation_result['warnings'].append(f"Invalid {amount_field} format: {amount}")
            
            if not has_valid_amount:
                validation_result['errors'].append("No valid positive amount found")
                validation_result['is_valid'] = False
            
            # Partner validation
            partner = invoice_data.get('partner', {})
            if partner:
                if not partner.get('name'):
                    validation_result['warnings'].append("Customer name is missing")
                
                if not partner.get('id') and not partner.get('netsuite_entity_id'):
                    validation_result['warnings'].append("Customer identifier is missing")
            else:
                validation_result['warnings'].append("No customer information available")
            
            # Currency validation
            currency = invoice_data.get('currency', '')
            if currency and len(currency) != 3:
                validation_result['warnings'].append("Currency code should be 3 characters (ISO 4217)")
            
            # NetSuite-specific validations
            netsuite_id = invoice_data.get('netsuite_invoice_id')
            if not netsuite_id:
                validation_result['warnings'].append("No NetSuite invoice ID found - this may affect traceability")
            
            # Source validation
            if not invoice_data.get('source'):
                validation_result['warnings'].append("Data source not specified")
            
            # Status validation
            netsuite_status = invoice_data.get('netsuite_status', '')
            if netsuite_status in ['Pending Approval', 'Pending Billing']:
                validation_result['warnings'].append("Invoice is in pending status - may not be ready for FIRS submission")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating NetSuite invoice data: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'invoice_id': invoice_data.get('id')
            }
    
    async def update_invoice_status(
        self,
        invoice_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update invoice status in NetSuite system"""
        try:
            # NetSuite invoice status updates would require specific API calls
            # and may have restrictions based on workflow states
            logger.info(f"Updating NetSuite invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': False,  # Would need actual API implementation
                'message': 'NetSuite invoice status updates require specific workflow API implementation',
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating NetSuite invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from NetSuite"""
        try:
            # In a real implementation, this would query NetSuite tax configuration
            # For now, return common US/international tax settings
            return {
                'default_tax_rate': 8.5,  # Common US sales tax rate
                'supported_tax_types': ['SALES_TAX', 'VAT', 'GST', 'USE_TAX'],
                'tax_codes': {
                    'VAT': 'Value Added Tax',
                    'SALES_TAX': 'Sales Tax',
                    'GST': 'Goods and Services Tax',
                    'USE_TAX': 'Use Tax'
                },
                'supported_tax_schemes': ['VAT', 'SALES_TAX', 'GST', 'USE_TAX'],
                'currency': 'USD',
                'country_codes': ['US', 'CA', 'GB', 'AU', 'NZ', 'IN'],  # Common NetSuite deployment countries
                'netsuite_tax_agencies': ['CALIFORNIA', 'NEW_YORK', 'TEXAS', 'UK_VAT', 'CANADA_GST']
            }
            
        except Exception as e:
            logger.error(f"Error retrieving NetSuite tax configuration: {str(e)}")
            raise NetSuiteDataError(f"Error retrieving NetSuite tax configuration: {str(e)}")
    
    def _map_netsuite_type_to_firs(self, netsuite_type: str) -> str:
        """
        Map NetSuite transaction types to FIRS invoice type codes.
        
        Args:
            netsuite_type: NetSuite transaction type
            
        Returns:
            FIRS invoice type code
        """
        # NetSuite transaction type mappings to UBL invoice type codes
        netsuite_to_firs_mapping = {
            # Standard transaction types
            'out_invoice': '380',       # Sales Invoice -> Standard Invoice
            'invoice': '380',           # Invoice -> Standard Invoice
            'creditmemo': '381',        # Credit Memo -> Credit Note
            'estimate': '325',          # Estimate -> Proforma Invoice
            'salesorder': '325',        # Sales Order -> Proforma Invoice
            'cashsale': '386',          # Cash Sale -> Prepayment Invoice
            
            # Default fallback
            '': '380'                   # Standard Invoice
        }
        
        return netsuite_to_firs_mapping.get(netsuite_type, '380')
    
    def _calculate_tax_rate(self, base_amount: float, tax_amount: float) -> float:
        """Calculate tax rate percentage from base and tax amounts."""
        try:
            if base_amount > 0 and tax_amount > 0:
                return round((tax_amount / base_amount) * 100, 2)
            return 0.0
        except (ZeroDivisionError, TypeError):
            return 0.0