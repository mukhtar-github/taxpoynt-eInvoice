"""
HubSpot Deal Transformation Module
Handles transformation of HubSpot deal data to invoice formats for FIRS compliance.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Union

from ....connector_framework import CRMDataError
from .exceptions import HubSpotDataError

logger = logging.getLogger(__name__)


class HubSpotDealTransformer:
    """Handles transformation of HubSpot deal data to invoice-compliant formats."""
    
    def __init__(self, data_extractor):
        """Initialize with a data extractor instance."""
        self.data_extractor = data_extractor
    
    async def transform_deal_to_invoice(
        self,
        deal_data: Dict[str, Any],
        target_format: str = 'UBL_BIS_3.0'
    ) -> Dict[str, Any]:
        """Transform HubSpot deal data to invoice format"""
        try:
            # Basic UBL BIS 3.0 transformation for CRM deal
            invoice_data = {
                'invoice_type_code': '380',  # Standard Invoice
                'id': deal_data.get('name', deal_data.get('deal_name', deal_data.get('id', ''))),
                'issue_date': deal_data.get('close_date', datetime.now().isoformat()),
                'due_date': self._calculate_due_date(deal_data.get('close_date')),
                'document_currency_code': 'USD',  # Default currency
                'accounting_supplier_party': {
                    'party': {
                        'party_name': {
                            'name': deal_data.get('owner', {}).get('name', 'HubSpot Deal Owner')
                        },
                        'party_tax_scheme': {
                            'company_id': '',  # Would need to be configured
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'accounting_customer_party': {
                    'party': {
                        'party_name': {
                            'name': deal_data.get('company', {}).get('name', 'HubSpot Customer')
                        },
                        'party_tax_scheme': {
                            'company_id': '',  # Would need to be configured
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }
                },
                'legal_monetary_total': {
                    'line_extension_amount': deal_data.get('amount', 0),
                    'tax_exclusive_amount': deal_data.get('amount', 0),
                    'tax_inclusive_amount': self._calculate_tax_inclusive_amount(deal_data.get('amount', 0)),
                    'allowance_total_amount': 0,
                    'charge_total_amount': 0,
                    'prepaid_amount': 0,
                    'payable_amount': self._calculate_tax_inclusive_amount(deal_data.get('amount', 0))
                },
                'invoice_line': []
            }
            
            # Transform deal line items or create summary line
            line_items = deal_data.get('line_items', [])
            
            if not line_items:
                # Create summary line item from deal
                summary_line = {
                    'id': '1',
                    'invoiced_quantity': {
                        'quantity': 1,
                        'unit_code': 'C62'  # Default unit
                    },
                    'line_extension_amount': deal_data.get('amount', 0),
                    'item': {
                        'description': f"HubSpot Deal: {deal_data.get('name', 'Deal')}",
                        'name': deal_data.get('name', 'HubSpot Deal'),
                        'sellers_item_identification': {
                            'id': deal_data.get('hubspot_deal_id', '')
                        }
                    },
                    'price': {
                        'price_amount': deal_data.get('amount', 0),
                        'base_quantity': {
                            'quantity': 1,
                            'unit_code': 'C62'
                        }
                    }
                }
                
                # Add tax information
                tax_amount = self._calculate_tax_amount(deal_data.get('amount', 0))
                if tax_amount > 0:
                    summary_line['tax_total'] = {
                        'tax_amount': tax_amount,
                        'tax_subtotal': [{
                            'taxable_amount': deal_data.get('amount', 0),
                            'tax_amount': tax_amount,
                            'tax_category': {
                                'id': 'S',  # Standard rate
                                'percent': 10.0,  # Default tax rate
                                'tax_scheme': {
                                    'id': 'VAT'
                                }
                            }
                        }]
                    }
                
                invoice_data['invoice_line'].append(summary_line)
            else:
                # Transform actual line items
                for line in line_items:
                    invoice_line = {
                        'id': str(line.get('id', line.get('line_number', 1))),
                        'invoiced_quantity': {
                            'quantity': line.get('quantity', 1),
                            'unit_code': 'C62'  # Default unit code
                        },
                        'line_extension_amount': line.get('amount', 0),
                        'item': {
                            'description': line.get('name', ''),
                            'name': line.get('name', ''),
                            'sellers_item_identification': {
                                'id': line.get('product_id', '')
                            }
                        },
                        'price': {
                            'price_amount': line.get('price', 0),
                            'base_quantity': {
                                'quantity': 1,
                                'unit_code': 'C62'
                            }
                        }
                    }
                    
                    # Add tax information
                    tax_amount = self._calculate_tax_amount(line.get('amount', 0))
                    if tax_amount > 0:
                        invoice_line['tax_total'] = {
                            'tax_amount': tax_amount,
                            'tax_subtotal': [{
                                'taxable_amount': line.get('amount', 0),
                                'tax_amount': tax_amount,
                                'tax_category': {
                                    'id': 'S',  # Standard rate
                                    'percent': 10.0,  # Default tax rate
                                    'tax_scheme': {
                                        'id': 'VAT'
                                    }
                                }
                            }]
                        }
                    
                    invoice_data['invoice_line'].append(invoice_line)
            
            # Add tax totals
            total_tax = self._calculate_tax_amount(deal_data.get('amount', 0))
            if total_tax > 0:
                invoice_data['tax_total'] = {
                    'tax_amount': total_tax,
                    'tax_subtotal': [{
                        'taxable_amount': deal_data.get('amount', 0),
                        'tax_amount': total_tax,
                        'tax_category': {
                            'id': 'S',
                            'percent': 10.0,  # Default tax rate
                            'tax_scheme': {
                                'id': 'VAT'
                            }
                        }
                    }]
                }
            
            return {
                'invoice_data': invoice_data,
                'source_format': 'hubspot_deal',
                'target_format': target_format,
                'transformation_metadata': {
                    'transformation_date': datetime.utcnow().isoformat(),
                    'source_deal_id': deal_data.get('id'),
                    'hubspot_deal_id': deal_data.get('hubspot_deal_id', ''),
                    'hubspot_stage': deal_data.get('hubspot_deal_stage', ''),
                    'hubspot_pipeline': deal_data.get('hubspot_pipeline', ''),
                    'crm_type': 'hubspot',
                    'data_source': deal_data.get('source', 'unknown')
                }
            }
            
        except Exception as e:
            logger.error(f"Error transforming HubSpot deal to invoice format: {str(e)}")
            raise CRMDataError(f"Error transforming HubSpot deal to invoice format: {str(e)}")
    
    async def validate_deal_data(self, deal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate HubSpot deal data before invoice generation.
        
        Args:
            deal_data: Deal data to validate
            
        Returns:
            Validation result with errors and warnings
        """
        try:
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'deal_id': deal_data.get('id')
            }
            
            # Required field validations
            required_fields = ['id', 'name']
            
            for field in required_fields:
                if not deal_data.get(field):
                    validation_result['errors'].append(f"Missing required field: {field}")
                    validation_result['is_valid'] = False
            
            # Date validation
            close_date = deal_data.get('close_date')
            if close_date:
                try:
                    datetime.fromisoformat(close_date.replace('Z', '+00:00'))
                except ValueError:
                    validation_result['warnings'].append(f"Invalid close_date format: {close_date}")
            else:
                validation_result['warnings'].append("No close date found - using current date")
            
            # Amount validation
            amount = deal_data.get('amount')
            if amount is not None:
                try:
                    amount_value = float(amount)
                    if amount_value <= 0:
                        validation_result['errors'].append(f"Deal amount must be positive: {amount_value}")
                        validation_result['is_valid'] = False
                except (ValueError, TypeError):
                    validation_result['errors'].append(f"Invalid amount format: {amount}")
                    validation_result['is_valid'] = False
            else:
                validation_result['errors'].append("No deal amount found")
                validation_result['is_valid'] = False
            
            # Stage validation
            stage = deal_data.get('stage', '')
            closed_stages = ['closedwon', 'won']
            if stage.lower() not in closed_stages:
                validation_result['warnings'].append(f"Deal is in '{stage}' stage - may not be ready for invoicing")
            
            # Company validation
            company = deal_data.get('company', {})
            if not company.get('name') and not deal_data.get('companies'):
                validation_result['errors'].append("Company information is required for invoicing")
                validation_result['is_valid'] = False
            
            # Probability validation
            probability = deal_data.get('probability')
            if probability is not None:
                try:
                    prob_value = float(probability)
                    if prob_value < 80:
                        validation_result['warnings'].append(f"Deal probability is low ({prob_value}%) - consider if ready for invoicing")
                except (ValueError, TypeError):
                    validation_result['warnings'].append(f"Invalid probability format: {probability}")
            
            # Pipeline validation
            pipeline = deal_data.get('pipeline')
            if not pipeline:
                validation_result['warnings'].append("No pipeline information found")
            
            # HubSpot-specific validations
            hubspot_deal_id = deal_data.get('hubspot_deal_id')
            if not hubspot_deal_id:
                validation_result['warnings'].append("No HubSpot deal ID found - this may affect traceability")
            
            # Source validation
            if not deal_data.get('source'):
                validation_result['warnings'].append("Data source not specified")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating HubSpot deal data: {str(e)}")
            return {
                'is_valid': False,
                'errors': [f"Validation error: {str(e)}"],
                'warnings': [],
                'deal_id': deal_data.get('id')
            }
    
    async def update_deal_status(
        self,
        deal_id: Union[int, str],
        status_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update deal status in HubSpot system"""
        try:
            # Map status to HubSpot stage if needed
            new_stage = status_data.get('stage', status_data.get('status'))
            
            # Prepare update data for HubSpot
            update_data = {'properties': {}}
            
            if new_stage:
                # Map common statuses to HubSpot stages
                stage_mapping = {
                    'invoiced': 'closedwon',
                    'won': 'closedwon',
                    'lost': 'closedlost',
                    'proposal': 'presentationscheduled',
                    'negotiation': 'contractsent'
                }
                
                hubspot_stage = stage_mapping.get(new_stage, new_stage)
                update_data['properties']['dealstage'] = hubspot_stage
            
            if status_data.get('probability'):
                update_data['properties']['hs_deal_stage_probability'] = str(float(status_data['probability']))
            
            if status_data.get('description'):
                update_data['properties']['description'] = status_data['description']
            
            if status_data.get('close_date'):
                # Convert to HubSpot timestamp (milliseconds)
                close_date = datetime.fromisoformat(status_data['close_date'].replace('Z', '+00:00'))
                timestamp_ms = int(close_date.timestamp() * 1000)
                update_data['properties']['closedate'] = str(timestamp_ms)
            
            # Update the deal in HubSpot
            response = await self.data_extractor.rest_client.update_crm_object(
                'deals', str(deal_id), update_data
            )
            
            return {
                'success': response.get('success', False),
                'deal_id': deal_id,
                'status_updated': response.get('success', False),
                'message': 'Deal status updated in HubSpot' if response.get('success') else 'Failed to update deal status',
                'new_stage': update_data['properties'].get('dealstage'),
                'updated_at': datetime.utcnow().isoformat(),
                'hubspot_response': response
            }
            
        except Exception as e:
            logger.error(f"Error updating HubSpot deal status: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'deal_id': deal_id
            }
    
    async def get_tax_configuration(self) -> Dict[str, Any]:
        """Get tax configuration for HubSpot deals"""
        try:
            # In a real implementation, this might query HubSpot tax settings
            # For now, return common US/international tax settings
            return {
                'default_tax_rate': 10.0,  # Default tax rate
                'supported_tax_types': ['SALES_TAX', 'VAT', 'GST'],
                'tax_codes': {
                    'VAT': 'Value Added Tax',
                    'SALES_TAX': 'Sales Tax',
                    'GST': 'Goods and Services Tax'
                },
                'supported_tax_schemes': ['VAT', 'SALES_TAX', 'GST'],
                'currency': 'USD',
                'country_codes': ['US', 'CA', 'GB', 'AU', 'NZ'],  # Common HubSpot deployment countries
                'hubspot_tax_settings': {
                    'enable_tax_calculation': True,
                    'tax_inclusive_pricing': False,
                    'default_tax_treatment': 'taxable'
                }
            }
            
        except Exception as e:
            logger.error(f"Error retrieving HubSpot tax configuration: {str(e)}")
            raise HubSpotDataError(f"Error retrieving HubSpot tax configuration: {str(e)}")
    
    def _calculate_due_date(self, close_date: Optional[str], payment_terms_days: int = 30) -> str:
        """Calculate invoice due date based on close date."""
        try:
            if close_date:
                base_date = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
            else:
                base_date = datetime.now()
            
            # Add payment terms
            due_date = base_date.replace(day=base_date.day + payment_terms_days)
            return due_date.isoformat()
            
        except Exception:
            # Fallback to 30 days from now
            due_date = datetime.now().replace(day=datetime.now().day + payment_terms_days)
            return due_date.isoformat()
    
    def _calculate_tax_amount(self, base_amount: float, tax_rate: float = 10.0) -> float:
        """Calculate tax amount from base amount."""
        try:
            return round(base_amount * (tax_rate / 100), 2)
        except (ValueError, TypeError):
            return 0.0
    
    def _calculate_tax_inclusive_amount(self, base_amount: float, tax_rate: float = 10.0) -> float:
        """Calculate tax-inclusive amount."""
        try:
            return base_amount + self._calculate_tax_amount(base_amount, tax_rate)
        except (ValueError, TypeError):
            return base_amount