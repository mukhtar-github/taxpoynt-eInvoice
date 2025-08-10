"""
Oracle FIRS Transformation Module
Handles transformation of Oracle invoice data to FIRS-compliant formats.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from ....connector_framework import ERPDataError
from .exceptions import OracleDataError

logger = logging.getLogger(__name__)


class OracleFIRSTransformer:
    """Handles transformation of Oracle data to FIRS-compliant formats."""
    
    def __init__(self, data_extractor):
        """Initialize with a data extractor instance."""
        self.data_extractor = data_extractor
    
    async def transform_to_firs_format(
        self,
        invoice_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform Oracle invoice data to FIRS-compliant format"""
        try:
            # Determine document type mapping
            firs_doc_type = self._map_oracle_transaction_type_to_firs(
                invoice_data.get('oracle_transaction_type', 
                               invoice_data.get('transaction_type', 'INVOICE'))
            )
            
            # Basic UBL BIS 3.0 transformation
            firs_invoice = {
                'invoice_type_code': firs_doc_type,
                'id': invoice_data.get('name', invoice_data.get('transaction_number', invoice_data.get('id', ''))),
                'issue_date': invoice_data.get('invoice_date', invoice_data.get('transaction_date', '')),
                'due_date': invoice_data.get('due_date', ''),  # May need additional API call for payment terms
                'document_currency_code': invoice_data.get('currency', 'USD'),
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': invoice_data.get('company', {}).get('name', 'Oracle Company')
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
                            'name': invoice_data.get('partner', {}).get('name', 'Oracle Customer')
                        },
                        'party_tax_scheme': {
                            'company_id': invoice_data.get('partner', {}).get('tax_number', ''),
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)),
                    'tax_exclusive_amount': invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)),
                    'tax_inclusive_amount': invoice_data.get('total_amount', invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0))),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': invoice_data.get('total_amount', invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)))
                },
                'invoice_line': []
            }
            
            # Transform invoice lines (if available)
            invoice_lines = invoice_data.get('invoice_lines', [])
            
            # If no line items available, create a summary line item
            if not invoice_lines:
                summary_line = {
                    'id': '1',
                    'invoiced_quantity': {
                        'quantity': 1,
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)),
                    'item': {
                        'description': f"Oracle {invoice_data.get('source', '')} - {invoice_data.get('name', 'Invoice')}",
                        'name': invoice_data.get('oracle_transaction_type', 'Service'),
                        'sellers_item_identification': {
                            'id': invoice_data.get('oracle_invoice_id', invoice_data.get('oracle_transaction_id', ''))
                        }
                    },
                    'price': {
                        'price_amount': invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                firs_invoice['invoice_line'].append(summary_line)
            else:
                # Transform actual line items
                for i, line in enumerate(invoice_lines):
                    firs_line = {
                        'id': str(line.get('id', i + 1)),
                        'invoiced_quantity': {
                            'quantity': line.get('quantity', 1),
                            'unit_code': line.get('unit_code', 'C62')
                        },
                        'line_extension_amount': line.get('amount', line.get('line_amount', 0)),
                        'item': {
                            'description': line.get('description', line.get('line_description', '')),
                            'name': line.get('product_name', line.get('item_name', '')),
                            'sellers_item_identification': {
                                'id': line.get('product_code', line.get('item_code', ''))
                            }
                        },
                        'price': {
                            'price_amount': line.get('unit_price', line.get('price_unit', 0)),
                            'base_quantity': {
                                'quantity': 1,
                                'unit_code': line.get('unit_code', 'C62')
                            }
                        }
                    }
                    
                    # Add tax information if available
                    tax_amount = line.get('tax_amount', 0)
                    if tax_amount > 0:
                        firs_line['tax_total'] = {
                            'tax_amount': tax_amount,
                            'tax_subtotal': [{
                                'taxable_amount': line.get('amount', line.get('line_amount', 0)),
                                'tax_amount': tax_amount,
                                'tax_category': {
                                    'id': 'S',  # Standard rate
                                    'percent': self._calculate_tax_rate(line.get('amount', line.get('line_amount', 0)), tax_amount),
                                    'tax_scheme': {
                                        'id': 'VAT'
                                    }
                                }
                            }]
                        }
                    
                    firs_invoice['invoice_line'].append(firs_line)
            
            # Add tax totals (estimate if not available)
            total_tax = self._calculate_total_tax(invoice_data)
            if total_tax > 0:
                firs_invoice['tax_total'] = {
                    'tax_amount': total_tax,
                    'tax_subtotal': [{
                        'taxable_amount': invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)),
                        'tax_amount': total_tax,
                        'tax_category': {
                            'id': 'S',
                            'percent': self._calculate_tax_rate(
                                invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0)), 
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
                'source_format': 'oracle_native',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_invoice_id': invoice_data.get('id'),
                    'oracle_transaction_type': invoice_data.get('oracle_transaction_type', ''),
                    'oracle_transaction_id': invoice_data.get('oracle_transaction_id', invoice_data.get('oracle_invoice_id', '')),
                    'erp_type': 'oracle',
                    'data_source': invoice_data.get('source', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming Oracle invoice to FIRS format: {str(e)}")
            raise ERPDataError(f"Error transforming Oracle invoice to FIRS format: {str(e)}")
    
    async def validate_invoice_data(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate Oracle invoice data before FIRS submission.
        
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
            date_fields = ['invoice_date', 'transaction_date']
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
                validation_result['errors'].append("No valid invoice/transaction date found")
                validation_result['is_valid'] = False
            
            # Amount validation
            amount_fields = ['invoice_amount', 'transaction_amount']
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
                    validation_result['warnings'].append("Partner/Customer name is missing")
                
                if not partner.get('id') and not partner.get('customer_number') and not partner.get('supplier_number'):
                    validation_result['warnings'].append("Partner/Customer identifier is missing")
            else:
                validation_result['warnings'].append("No partner/customer information available")
            
            # Currency validation
            currency = invoice_data.get('currency', '')
            if currency and len(currency) != 3:
                validation_result['warnings'].append("Currency code should be 3 characters (ISO 4217)")
            
            # Oracle-specific validations
            oracle_id_fields = ['oracle_invoice_id', 'oracle_transaction_id']
            has_oracle_id = any(invoice_data.get(field) for field in oracle_id_fields)
            
            if not has_oracle_id:
                validation_result['warnings'].append("No Oracle ID found - this may affect traceability")
            
            # Source validation
            if not invoice_data.get('source'):
                validation_result['warnings'].append("Data source not specified")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Oracle invoice data: {str(e)}")
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
        """Update invoice status in Oracle system"""
        try:
            # Oracle invoice status updates would require specific API calls
            # and may have restrictions based on approval workflows
            logger.info(f"Updating Oracle invoice {invoice_id} status: {status_data}")
            
            return {
                'success': True,
                'invoice_id': invoice_id,
                'status_updated': False,  # Would need actual API implementation
                'message': 'Oracle invoice status updates require specific API implementation',
                'new_status': status_data.get('status'),
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error updating Oracle invoice status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'invoice_id': invoice_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration from Oracle"""
        try:
            # In a real implementation, this would query Oracle tax configuration
            # For now, return common US/international tax settings
            return {
                'default_tax_rate': 10.0,  # Configurable default
                'supported_tax_types': ['SALES_TAX', 'VAT', 'GST'],
                'tax_codes': {
                    'VAT': 'Value Added Tax',
                    'SALES_TAX': 'Sales Tax',
                    'GST': 'Goods and Services Tax'
                },
                'supported_tax_schemes': ['VAT', 'SALES_TAX', 'GST'],
                'currency': 'USD',
                'country_codes': ['US', 'CA', 'GB', 'AU'],  # Common Oracle deployment countries
                'oracle_tax_jurisdictions': ['US', 'EU', 'APAC']
            }
            
        except Exception as e:
            logger.error(f"Error retrieving Oracle tax configuration: {str(e)}")
            raise OracleDataError(f"Error retrieving Oracle tax configuration: {str(e)}")
    
    def _map_oracle_transaction_type_to_firs(self, oracle_transaction_type: str) -> str:
        """
        Map Oracle transaction types to FIRS invoice type codes.
        
        Args:
            oracle_transaction_type: Oracle transaction type
            
        Returns:
            FIRS invoice type code
        """
        # Oracle transaction type mappings to UBL invoice type codes
        oracle_to_firs_mapping = {
            # Standard transaction types
            'INVOICE': '380',           # Standard Invoice
            'CREDIT_MEMO': '381',       # Credit Note
            'DEBIT_MEMO': '383',        # Debit Note
            'PREPAYMENT': '386',        # Prepayment Invoice
            'COMMERCIAL_INVOICE': '380', # Commercial Invoice
            'PROFORMA': '325',          # Proforma Invoice
            'TAX_INVOICE': '380',       # Tax Invoice
            
            # Oracle-specific types
            'Standard Invoice': '380',
            'Credit Memo': '381',
            'Debit Memo': '383',
            'Adjustment': '458',        # Adjustment
            'Guarantee': '389',         # Self-billed Invoice
            
            # Default fallback
            '': '380'                   # Standard Invoice
        }
        
        return oracle_to_firs_mapping.get(oracle_transaction_type, '380')
    
    def _calculate_total_tax(self, invoice_data: Dict[str, Any]) -> float:
        """Calculate total tax amount from invoice data."""
        # Check if tax amount is directly available
        tax_amount = invoice_data.get('tax_amount', 0)
        if tax_amount:
            return float(tax_amount)
        
        # Calculate from total and net amounts
        total_amount = invoice_data.get('total_amount', 0)
        net_amount = invoice_data.get('invoice_amount', invoice_data.get('transaction_amount', 0))
        
        if total_amount and net_amount:
            calculated_tax = float(total_amount) - float(net_amount)
            return max(0, calculated_tax)  # Ensure non-negative
        
        # Estimate based on common tax rates (last resort)
        if net_amount:
            estimated_tax_rate = 0.1  # 10% default
            return float(net_amount) * estimated_tax_rate
        
        return 0.0
    
    def _calculate_tax_rate(self, base_amount: float, tax_amount: float) -> float:
        """Calculate tax rate percentage from base and tax amounts."""
        try:
            if base_amount > 0 and tax_amount > 0:
                return round((tax_amount / base_amount) * 100, 2)
            return 0.0
        except (ZeroDivisionError, TypeError):
            return 0.0