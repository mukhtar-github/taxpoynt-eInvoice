"""
Odoo FIRS Transformation Module
Handles transformation of Odoo invoice data to FIRS-compliant formats.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from ....connector_framework import ERPDataError
from .exceptions import OdooDataError

logger = logging.getLogger(__name__)


class OdooFIRSTransformer:
    """Handles transformation of Odoo data to FIRS-compliant formats."""
    
    def __init__(self, data_extractor):
        """Initialize with a data extractor instance."""
        self.data_extractor = data_extractor
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform ERP invoice data to FIRS-compliant format"""
        try:
            # Basic UBL BIS 3.0 transformation
            firs_invoice = {
                'invoice_type_code': '380',  # Standard invoice
                'id': invoice_data.get('name', ''),
                'issue_date': invoice_data.get('invoice_date', ''),
                'due_date': invoice_data.get('invoice_date_due', ''),
                'document_currency_code': invoice_data.get('currency', 'NGN'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('company', {}).get('name', '')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('company', {}).get('vat', '')
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('partner', {}).get('name', '')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('partner', {}).get('vat', '')
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_exclusive_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_inclusive_amount': invoice_data.get('amount_total', 0),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data.get('amount_total', 0)
                },
                'invoice_line': []
            }
            
            # Transform invoice lines
            for line in invoice_data.get('invoice_lines', []):
                firs_line = {
                    'id': str(line.get('id', '')),
                    'invoiced_quantity': {
                        'quantity': line.get('quantity', 0),
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': line.get('price_subtotal', 0),
                    'item': {
                        'description': line.get('name', ''),
                        'name': line.get('product_name', ''),
                        'sellers_item_identification': {
                            'id': line.get('product_id', '')
                        }
                    },
                    'price': {
                        'price_amount': line.get('price_unit', 0),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                
                # Add tax information
                if line.get('tax_ids'):
                    tax_amount = line.get('price_total', 0) - line.get('price_subtotal', 0)
                    firs_line['tax_total'] = {
                        'tax_amount': tax_amount,
                        'tax_subtotal': [{
                            'taxable_amount': line.get('price_subtotal', 0),
                            'tax_amount': tax_amount,
                            'tax_category': {
                                'id': 'S',  # Standard rate
                                'percent': 7.5,  # Default Nigerian VAT rate
                                'tax_scheme': {
                                    'id': 'VAT'
                                }
                            }
                        }]
                    }
                
                firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals
            firs_invoice['tax_total'] = {
                'tax_amount': invoice_data.get('amount_tax', 0),
                'tax_subtotal': [{
                    'taxable_amount': invoice_data.get('amount_untaxed', 0),
                    'tax_amount': invoice_data.get('amount_tax', 0),
                    'tax_category': {
                        'id': 'S',
                        'percent': 7.5,  # Default Nigerian VAT rate
                        'tax_scheme': {
                            'id': 'VAT'
                        }
                    }
                }]
            }
            
            return {
                'firs_invoice': firs_invoice,
                'source_format': 'odoo_native',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('id'),
                    'erp_type': 'odoo',
                    'erp_version': self._get_odoo_version()
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming invoice to FIRS format: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate invoice data before FIRS submission.
        
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
            required_fields = [
                'name', 'invoice_date', 'partner', 'amount_total', 'invoice_lines'
            ]
            
            for field in required_fields:
                if not invoice_data.get(field):
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
            
            # Partner validation
            partner = invoice_data.get('partner', {})
            if partner:
                if not partner.get('name'):
                    validation_result['errors'].append("Customer name is required")
                    validation_result['is_valid'] = False
                
                if not partner.get('vat'):
                    validation_result['warnings'].append("Customer VAT number is missing")
            
            # Invoice lines validation
            invoice_lines = invoice_data.get('invoice_lines', [])
            if not invoice_lines:
                validation_result['errors'].append("Invoice must have at least one line item")
                validation_result['is_valid'] = False
            
            for i, line in enumerate(invoice_lines):
                if not line.get('name'):
                    validation_result['errors'].append(f"Line {i+1}: Product description is required")
                    validation_result['is_valid'] = False
                
                if line.get('quantity', 0) <= 0:
                    validation_result['errors'].append(f"Line {i+1}: Quantity must be greater than 0")
                    validation_result['is_valid'] = False
                
                if line.get('price_unit', 0) < 0:
                    validation_result['errors'].append(f"Line {i+1}: Unit price cannot be negative")
                    validation_result['is_valid'] = False
            
            # Amount validation
            if invoice_data.get('amount_total', 0) <= 0:
                validation_result['errors'].append("Invoice total must be greater than 0")
                validation_result['is_valid'] = False
            
            # Date validation
            if invoice_data.get('invoice_date'):
                try:
                    datetime.fromisoformat(invoice_data['invoice_date'].replace('Z', '+00:00'))
                except ValueError:
                    validation_result['errors'].append("Invalid invoice date format")
                    validation_result['is_valid'] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating invoice data: {str(e)}")
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
        """Update invoice status in the ERP system"""
        try:
            # For now, just log the status update
            # In a real implementation, this would update the invoice in Odoo
            logger.info(f"Updating invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': True,
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from Odoo"""
        try:
            # In a real implementation, this would query Odoo tax configuration
            return {
                'default_vat_rate': 7.5,
                'tax_codes': {
                    'VAT': 'Value Added Tax',
                    'WHT': 'Withholding Tax'
                },
                'supported_tax_schemes': ['VAT', 'WHT'],
                'currency': 'NGN'
            }
            
        except Exception as e:
            logger.error(f"Error retrieving tax configuration: {str(e)}")
            raise OdooDataError(f"Error retrieving tax configuration: {str(e)}")
    
    def _get_odoo_version(self) -> str:
        """Get Odoo version from authenticator."""
        try:
            if hasattr(self.data_extractor.authenticator, 'version_info'):
                version_info = self.data_extractor.authenticator.version_info
                return version_info.get('server_version', 'unknown')
            return 'unknown'
        except:
            return 'unknown'