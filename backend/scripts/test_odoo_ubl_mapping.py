#!/usr/bin/env python
"""
Script to test the Odoo to UBL mapping with real Odoo invoice data.
This script connects to Odoo, retrieves an invoice, and tests the mapping to UBL.
"""
import sys
import os
import logging
import json
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.odoo_connector import OdooConnector
from app.services.odoo_ubl_mapper import odoo_ubl_mapper
from app.services.odoo_ubl_validator import odoo_ubl_validator
from app.services.odoo_ubl_transformer import odoo_ubl_transformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Test Odoo UBL mapping with a real Odoo invoice'
    )
    parser.add_argument(
        '--host', required=True,
        help='Odoo host URL (e.g., https://yourodoo.com)'
    )
    parser.add_argument(
        '--db', required=True,
        help='Odoo database name'
    )
    parser.add_argument(
        '--user', required=True,
        help='Odoo username or login'
    )
    parser.add_argument(
        '--password', required=False,
        help='Odoo password (use this or api_key)'
    )
    parser.add_argument(
        '--api_key', required=False,
        help='Odoo API key (use this or password)'
    )
    parser.add_argument(
        '--invoice_id', required=False, type=int,
        help='Specific invoice ID to test'
    )
    parser.add_argument(
        '--output', required=False, default='ubl_output.xml',
        help='Output file for the UBL XML (default: ubl_output.xml)'
    )
    parser.add_argument(
        '--validate', action='store_true',
        help='Validate the UBL XML against FIRS requirements'
    )
    
    return parser.parse_args()


def get_invoice_from_odoo(args) -> Dict[str, Any]:
    """Connect to Odoo and retrieve an invoice."""
    logger.info(f"Connecting to Odoo at {args.host}")
    
    try:
        # Create a connector instance
        connector = OdooConnector(
            host=args.host,
            db=args.db,
            user=args.user,
            password=args.password,
            api_key=args.api_key
        )
        
        # Authenticate with Odoo
        connector.authenticate()
        logger.info("Successfully connected to Odoo")
        
        # Get company information
        company_info = connector.get_user_company()
        logger.info(f"Retrieved company information: {company_info['name']}")
        
        # Get a specific invoice or the most recent one
        if args.invoice_id:
            invoice = connector.get_invoice_by_id(args.invoice_id)
            logger.info(f"Retrieved invoice with ID {args.invoice_id}")
        else:
            # Get the most recent invoice
            invoices, _ = connector.get_invoices(
                from_date=None, 
                to_date=None, 
                include_draft=False, 
                page=1, 
                page_size=1
            )
            
            if not invoices:
                raise ValueError("No invoices found in the Odoo system")
            
            invoice = invoices[0]
            logger.info(f"Retrieved most recent invoice: {invoice['name']}")
        
        return invoice, company_info
        
    except Exception as e:
        logger.error(f"Error connecting to Odoo: {str(e)}")
        raise


def test_ubl_mapping(invoice: Dict[str, Any], company_info: Dict[str, Any], output_file: str) -> bool:
    """Test the UBL mapping with the retrieved invoice."""
    logger.info("Testing UBL mapping with the retrieved invoice")
    
    try:
        # Step 1: Map Odoo invoice to UBL object
        logger.info("Mapping invoice to UBL format...")
        ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
            invoice, company_info
        )
        
        if validation_issues:
            logger.error(f"Validation issues detected in mapping:")
            for issue in validation_issues:
                logger.error(f"  {issue['field']}: {issue['message']} ({issue['code']})")
            return False
        
        logger.info("Invoice successfully mapped to UBL object")
        
        # Step 2: Transform UBL object to XML
        logger.info("Transforming to UBL XML...")
        ubl_xml, conversion_issues = odoo_ubl_transformer.ubl_object_to_xml(ubl_invoice)
        
        if conversion_issues:
            logger.error(f"Conversion issues detected in XML transformation:")
            for issue in conversion_issues:
                logger.error(f"  {issue['field']}: {issue['message']} ({issue['code']})")
            return False
        
        logger.info(f"Successfully transformed to UBL XML")
        
        # Save the XML to the output file
        with open(output_file, 'w') as f:
            f.write(ubl_xml)
        logger.info(f"Saved UBL XML to {output_file}")
        
        # Print a sample of the XML
        xml_preview = ubl_xml[:500] + "..." if len(ubl_xml) > 500 else ubl_xml
        logger.info(f"XML preview:\n{xml_preview}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in UBL mapping process: {str(e)}")
        return False


def validate_ubl_xml(output_file: str) -> bool:
    """Validate the UBL XML against FIRS requirements."""
    logger.info(f"Validating UBL XML against BIS Billing 3.0 schema")
    
    try:
        from app.services.ubl_validator import UBLValidator
        
        # Read the XML from file
        with open(output_file, 'r') as f:
            xml_content = f.read()
        
        # Create validator and validate
        validator = UBLValidator()
        valid, errors = validator.validate_against_schema(xml_content)
        
        if valid:
            logger.info("UBL XML validation successful!")
            return True
        else:
            logger.error(f"UBL XML validation failed with {len(errors)} errors:")
            for error in errors:
                logger.error(f"  {error.field}: {error.error}")
            return False
            
    except ImportError:
        logger.warning("UBLValidator not available - skipping validation")
        return True
    except Exception as e:
        logger.error(f"Error during UBL validation: {str(e)}")
        return False


def main():
    """Main function to run the test."""
    args = parse_args()
    
    # Check that either password or API key is provided
    if not args.password and not args.api_key:
        logger.error("Either --password or --api_key must be provided")
        sys.exit(1)
    
    try:
        # Get invoice from Odoo
        invoice, company_info = get_invoice_from_odoo(args)
        
        # Test UBL mapping
        if test_ubl_mapping(invoice, company_info, args.output):
            logger.info("UBL mapping test completed successfully")
            
            # Validate if requested
            if args.validate:
                if validate_ubl_xml(args.output):
                    logger.info("UBL XML validation passed")
                else:
                    logger.warning("UBL XML validation failed")
                    sys.exit(3)
                    
        else:
            logger.error("UBL mapping test failed")
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
