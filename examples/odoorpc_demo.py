"""
Demo script for OdooRPC integration in TaxPoynt eInvoice.

This script demonstrates how to use OdooRPC to connect to an Odoo instance
and fetch invoices. It does not require the full application context.
"""

import sys
import os
from pathlib import Path
import logging
from datetime import datetime, timedelta
from pprint import pprint
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import odoorpc
    logger.info("OdooRPC library successfully imported")
except ImportError:
    logger.error("Failed to import odoorpc. Please install with: pip install odoorpc")
    sys.exit(1)

def connect_to_odoo(config):
    """
    Connect to an Odoo instance using OdooRPC.
    
    Args:
        config: Dictionary with Odoo connection parameters
            - host: Odoo server hostname
            - port: Port number (default: 443 for SSL, 8069 for non-SSL)
            - protocol: Protocol to use (jsonrpc, jsonrpc+ssl, xmlrpc, xmlrpc+ssl)
            - database: Database name
            - username: Username (email)
            - password: Password or API key
            - use_api_key: Whether to use API key authentication
        
    Returns:
        OdooRPC connection object
    """
    logger.info(f"Connecting to Odoo at {config['host']} using {config['protocol']}")
    
    try:
        # Initialize OdooRPC connection
        odoo = odoorpc.ODOO(
            config["host"], 
            protocol=config["protocol"], 
            port=config["port"]
        )
        
        # Login to Odoo
        odoo.login(
            config["database"], 
            config["username"], 
            config["password"]
        )
        
        # Get user info
        user = odoo.env['res.users'].browse(odoo.env.uid)
        logger.info(f"Connected as user: {user.name} (ID: {odoo.env.uid})")
        
        return odoo
    except Exception as e:
        logger.error(f"Failed to connect to Odoo: {str(e)}")
        raise

def fetch_invoices(odoo, limit=5, from_days_ago=30):
    """
    Fetch invoices from Odoo.
    
    Args:
        odoo: OdooRPC connection
        limit: Maximum number of invoices to fetch
        from_days_ago: Fetch invoices from this many days ago
        
    Returns:
        List of invoice dictionaries
    """
    logger.info(f"Fetching up to {limit} invoices from the past {from_days_ago} days")
    
    # Calculate from_date
    from_date = (datetime.now() - timedelta(days=from_days_ago)).strftime('%Y-%m-%d')
    
    try:
        # Get the invoice model (account.move in Odoo 13+)
        Invoice = odoo.env['account.move']
        
        # Build search domain
        domain = [
            ('move_type', '=', 'out_invoice'),  # Only customer invoices
            ('invoice_date', '>=', from_date)   # Only recent invoices
        ]
        
        # First use search to get IDs
        invoice_ids = Invoice.search(domain, limit=limit)
        logger.info(f"Found {len(invoice_ids)} invoices")
        
        if not invoice_ids:
            return []
        
        # Use search_read instead of browse to avoid frozendict issues
        invoice_data = Invoice.search_read(
            [('id', 'in', invoice_ids)], 
            [
                'name', 'ref', 'invoice_date', 'amount_total', 
                'partner_id', 'invoice_line_ids', 'state', 'currency_id'
            ]
        )
        
        # Prepare results with native Python types
        invoices = []
        
        for invoice in invoice_data:
            # Safely handle partner data
            partner_id = False
            partner_name = "Unknown"
            
            if invoice.get('partner_id'):
                try:
                    partner_id = int(invoice['partner_id'][0])
                    partner_name = str(invoice['partner_id'][1])
                except (IndexError, TypeError):
                    pass
            
            # Get currency symbol
            currency_symbol = "₦"  # Default to Naira
            if invoice.get('currency_id'):
                try:
                    if invoice['currency_id'][1] == "USD":
                        currency_symbol = "$"
                    elif invoice['currency_id'][1] == "EUR":
                        currency_symbol = "€"
                except (IndexError, TypeError):
                    pass
            
            # Count invoice lines
            line_count = 0
            if invoice.get('invoice_line_ids'):
                line_count = len(invoice['invoice_line_ids'])
            
            # Format invoice data with primitive types only
            invoice_data = {
                "id": int(invoice['id']),
                "name": str(invoice.get('name', '')),
                "reference": str(invoice.get('ref', '') or ''),
                "invoice_date": invoice.get('invoice_date'),
                "amount_total": float(invoice.get('amount_total', 0.0)),
                "currency_symbol": currency_symbol,
                "partner": {
                    "id": partner_id,
                    "name": partner_name,
                },
                "line_count": line_count,
                "state": str(invoice.get('state', 'draft')),
            }
            
            invoices.append(invoice_data)
        
        return invoices
        
    except Exception as e:
        logger.error(f"Error fetching invoices: {str(e)}")
        raise

def main():
    """Main function for the demo script."""
    
    # Demo configuration (replace with real values)
    demo_config = {
        "host": "demo.odoo.com",           # Odoo server hostname
        "port": 443,                        # Default HTTPS port
        "protocol": "jsonrpc+ssl",          # Use SSL for security
        "database": "demo",                 # Demo database
        "username": "admin",                # Demo username
        "password": "admin",                # Demo password/API key
        "use_api_key": False                # Using password instead of API key for demo
    }
    
    # Try to import test credentials if available
    try:
        import sys
        import os
        # Add project root to path to support importing from backend directory
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        
        from backend.test_credentials import test_config
        print("Using test credentials from test_credentials.py")
        config = test_config
    except ImportError as e:
        print(f"Unable to import test credentials: {e}")
        print("Using demo configuration (likely to fail without real credentials)")
        config = demo_config
    
    print("\n" + "="*80)
    print("TaxPoynt eInvoice - OdooRPC Integration Demo")
    print("="*80)
    
    print("\nThis script demonstrates how to use OdooRPC to connect to an Odoo instance")
    print("and fetch invoice data. To use with a real Odoo instance, update the")
    print("configuration values in the script with your actual connection details.")
    print("\nNote: The demo is configured to use demo.odoo.com which may not allow")
    print("connections without proper credentials. You will need to provide valid")
    print("credentials to successfully run this demo.")
    
    try:
        # Connect to Odoo
        print("\nAttempting to connect to Odoo...")
        odoo = connect_to_odoo(config)
        
        # Fetch invoices
        print("\nFetching invoices...")
        invoices = fetch_invoices(odoo, limit=5, from_days_ago=30)
        
        # Display results
        print("\nFetched Invoices:")
        print("-"*40)
        
        if invoices:
            for i, invoice in enumerate(invoices, 1):
                print(f"Invoice {i}:")
                print(f"  ID: {invoice['id']}")
                print(f"  Name: {invoice['name']}")
                print(f"  Date: {invoice['invoice_date']}")
                print(f"  Customer: {invoice['partner']['name']}")
                print(f"  Amount: {invoice['currency_symbol']}{invoice['amount_total']:.2f}")
                print(f"  Status: {invoice['state']}")
                print(f"  Line Items: {invoice['line_count']}")
                print("-"*40)
        else:
            print("No invoices found in the specified date range.")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed: {str(e)}")
        print("\nTo successfully run this demo, you need to:")
        print("1. Install odoorpc: pip install odoorpc")
        print("2. Update the configuration with valid Odoo connection details")
        print("3. Ensure network access to the Odoo server")

if __name__ == "__main__":
    main()
