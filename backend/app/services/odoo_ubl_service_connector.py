"""
Service connector for integrating Odoo UBL mapping with other system components.

This module provides functions that enable other parts of the system to utilize
the Odoo to BIS Billing 3.0 UBL mapping functionality without direct API calls.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from app.services.odoo_service import fetch_odoo_invoices, search_odoo_invoices
from app.services.odoo_invoice_service import odoo_invoice_service
from app.services.integration_service import test_odoo_connection
from app.schemas.integration import OdooConnectionTestRequest


class OdooUblServiceConnector:
    """Service connector for Odoo UBL mapping functionality."""
    
    @staticmethod
    def test_connection(connection_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test connection to an Odoo server and verify UBL mapping capabilities.
        
        Args:
            connection_params: Dictionary containing connection parameters:
                - host: Odoo host URL
                - db: Odoo database name
                - user: Odoo username
                - password: Odoo password (optional)
                - api_key: Odoo API key (optional)
                
        Returns:
            Dict with connection test results and UBL mapping capabilities
        """
        # Create a proper connection test request
        conn_request = OdooConnectionTestRequest(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password'),
            api_key=connection_params.get('api_key')
        )
        
        # Use the existing test_odoo_connection service
        connection_result = test_odoo_connection(conn_request, current_user=None)
        
        # Add UBL mapping capabilities information
        result = connection_result.dict()
        result.update({
            "ubl_mapping_status": "available",
            "ubl_mapping_version": "BIS Billing 3.0",
            "ubl_schema_validation": True
        })
        
        return result
    
    @staticmethod
    def get_invoices(
        connection_params: Dict[str, Any],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        include_draft: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Get invoices from Odoo with UBL mapping capability information.
        
        Args:
            connection_params: Dictionary containing connection parameters
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            include_draft: Whether to include draft invoices
            page: Page number
            page_size: Number of items per page
                
        Returns:
            Dict with invoices, pagination info, and UBL mapping capabilities
        """
        # Get invoices using the existing service
        result = fetch_odoo_invoices(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password', ''),
            api_key=connection_params.get('api_key', ''),
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            page=page,
            page_size=page_size
        )
        
        # Add UBL mapping capability information to each invoice
        invoices = result.get('data', [])
        for invoice in invoices:
            invoice['ubl_mapping_available'] = True
            invoice['ubl_endpoints'] = {
                'details': f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}",
                'ubl': f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl",
                'xml': f"/api/v1/odoo-ubl/invoices/{invoice.get('id')}/ubl/xml"
            }
        
        return {
            'status': 'success',
            'data': invoices,
            'pagination': result.get('pagination', {}),
            'ubl_mapping': {
                'status': 'available',
                'version': 'BIS Billing 3.0'
            }
        }
    
    @staticmethod
    def get_invoice_details(
        connection_params: Dict[str, Any],
        invoice_id: int
    ) -> Dict[str, Any]:
        """
        Get details of a specific invoice from Odoo.
        
        Args:
            connection_params: Dictionary containing connection parameters
            invoice_id: ID of the invoice to retrieve
                
        Returns:
            Dict with invoice details and UBL mapping capabilities
        """
        # Get the invoice details
        search_result = search_odoo_invoices(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password', ''),
            api_key=connection_params.get('api_key', ''),
            invoice_ids=[invoice_id]
        )
        
        if not search_result or not search_result.get('data'):
            return {
                'status': 'error',
                'message': f'Invoice with ID {invoice_id} not found',
                'code': 'INVOICE_NOT_FOUND'
            }
        
        # Get the invoice data
        invoice_data = search_result.get('data')[0]
        
        # Add UBL mapping information
        return {
            'status': 'success',
            'data': invoice_data,
            'ubl_mapping': {
                'available': True,
                'endpoints': {
                    'ubl': f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl",
                    'xml': f"/api/v1/odoo-ubl/invoices/{invoice_id}/ubl/xml"
                }
            }
        }
    
    @staticmethod
    def map_invoice_to_ubl(
        connection_params: Dict[str, Any],
        invoice_id: int,
        validate_schema: bool = True
    ) -> Dict[str, Any]:
        """
        Map an Odoo invoice to BIS Billing 3.0 UBL format.
        
        Args:
            connection_params: Dictionary containing connection parameters
            invoice_id: ID of the invoice to map
            validate_schema: Whether to validate the UBL against schema
                
        Returns:
            Dict with UBL mapping results
        """
        # First get the invoice data
        search_result = search_odoo_invoices(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password', ''),
            api_key=connection_params.get('api_key', ''),
            invoice_ids=[invoice_id]
        )
        
        if not search_result or not search_result.get('data'):
            return {
                'status': 'error',
                'message': f'Invoice with ID {invoice_id} not found',
                'code': 'INVOICE_NOT_FOUND'
            }
        
        # Get invoice data and company info
        invoice_data = search_result.get('data')[0]
        
        # Test connection to get company info
        conn_request = OdooConnectionTestRequest(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password'),
            api_key=connection_params.get('api_key')
        )
        
        # Get company info from connection test
        connection_result = test_odoo_connection(conn_request, current_user=None)
        company_info = connection_result.data.get('company_info', {}) if connection_result.data else {}
        
        # Map the invoice to UBL
        result = odoo_invoice_service.process_invoice_data(
            invoice_data=invoice_data,
            company_info=company_info,
            save_ubl=False,
            validate_ubl=validate_schema
        )
        
        if not result.get('success'):
            return {
                'status': 'error',
                'message': 'Failed to map invoice to UBL format',
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', [])
            }
        
        return {
            'status': 'success',
            'data': result,
            'message': 'Invoice successfully mapped to UBL format'
        }
    
    @staticmethod
    def get_invoice_ubl_xml(
        connection_params: Dict[str, Any],
        invoice_id: int,
        validate_schema: bool = True
    ) -> Union[Dict[str, Any], Tuple[str, str]]:
        """
        Get the UBL XML for an Odoo invoice.
        
        Args:
            connection_params: Dictionary containing connection parameters
            invoice_id: ID of the invoice to convert to XML
            validate_schema: Whether to validate the UBL against schema
                
        Returns:
            Tuple of (xml_content, filename) if successful,
            Dict with error details if failed
        """
        # Use the map_invoice_to_ubl method to get UBL data
        result = OdooUblServiceConnector.map_invoice_to_ubl(
            connection_params=connection_params,
            invoice_id=invoice_id,
            validate_schema=validate_schema
        )
        
        if result.get('status') != 'success':
            return result
        
        # Extract the XML content
        ubl_data = result.get('data', {})
        xml_content = ubl_data.get('ubl_xml')
        
        if not xml_content:
            return {
                'status': 'error',
                'message': 'UBL XML generation failed: No XML content returned',
                'code': 'XML_GENERATION_ERROR'
            }
        
        # Generate a filename
        filename = f"invoice_{invoice_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xml"
        
        return xml_content, filename
    
    @staticmethod
    def batch_process_invoices(
        connection_params: Dict[str, Any],
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        include_draft: bool = False,
        page: int = 1,
        page_size: int = 10
    ) -> Dict[str, Any]:
        """
        Batch process multiple Odoo invoices, mapping them to UBL format.
        
        Args:
            connection_params: Dictionary containing connection parameters
            from_date: Start date in YYYY-MM-DD format
            to_date: End date in YYYY-MM-DD format
            include_draft: Whether to include draft invoices
            page: Page number
            page_size: Number of items per page
                
        Returns:
            Dict with batch processing results
        """
        # First get the invoices
        invoice_result = fetch_odoo_invoices(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password', ''),
            api_key=connection_params.get('api_key', ''),
            from_date=from_date,
            to_date=to_date,
            include_draft=include_draft,
            page=page,
            page_size=page_size
        )
        
        if not invoice_result or not invoice_result.get('data'):
            return {
                'status': 'success',
                'message': 'No invoices found matching the criteria',
                'processed_count': 0,
                'success_count': 0,
                'error_count': 0,
                'invoices': []
            }
        
        # Get company info
        conn_request = OdooConnectionTestRequest(
            host=connection_params.get('host'),
            db=connection_params.get('db'),
            user=connection_params.get('user'),
            password=connection_params.get('password'),
            api_key=connection_params.get('api_key')
        )
        
        connection_result = test_odoo_connection(conn_request, current_user=None)
        company_info = connection_result.data.get('company_info', {}) if connection_result.data else {}
        
        # Process each invoice
        invoices = invoice_result.get('data', [])
        results = []
        success_count = 0
        error_count = 0
        
        for invoice in invoices:
            try:
                # Process the invoice
                mapping_result = odoo_invoice_service.process_invoice_data(
                    invoice_data=invoice,
                    company_info=company_info,
                    save_ubl=False,
                    validate_ubl=True
                )
                
                # Add to results
                if mapping_result.get('success'):
                    success_count += 1
                else:
                    error_count += 1
                
                results.append({
                    'invoice_id': invoice.get('id'),
                    'invoice_number': invoice.get('number'),
                    'success': mapping_result.get('success', False),
                    'errors': mapping_result.get('errors', []),
                    'warnings': mapping_result.get('warnings', []),
                    'ubl_id': mapping_result.get('ubl_id') if mapping_result.get('success') else None
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'invoice_id': invoice.get('id'),
                    'invoice_number': invoice.get('number'),
                    'success': False,
                    'errors': [{
                        'code': 'PROCESSING_ERROR',
                        'message': str(e),
                        'field': None
                    }],
                    'warnings': [],
                    'ubl_id': None
                })
        
        return {
            'status': 'success' if error_count == 0 else 'partial',
            'processed_count': len(invoices),
            'success_count': success_count,
            'error_count': error_count,
            'message': f'Processed {len(invoices)} invoices: {success_count} successful, {error_count} failed',
            'invoices': results,
            'pagination': invoice_result.get('pagination', {})
        }


# Create a singleton instance for use throughout the application
odoo_ubl_connector = OdooUblServiceConnector()
