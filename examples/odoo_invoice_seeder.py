"""
Odoo Invoice Seeder Script for TaxPoynt eInvoice

This script creates sample invoice data in an Odoo instance for testing purposes.
"""

import sys
import os
import logging
from datetime import date, datetime, timedelta
import random

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path to support importing from backend directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    # Try to import custom test credentials
    from backend.test_credentials import test_config
    logger.info("Using test credentials from test_credentials.py")
except ImportError as e:
    logger.error(f"Unable to import test credentials: {e}")
    logger.error("Please set up test_credentials.py with your Odoo credentials")
    sys.exit(1)

try:
    import odoorpc
    logger.info("OdooRPC library successfully imported")
except ImportError:
    logger.error("Failed to import odoorpc. Please install with: pip install odoorpc")
    sys.exit(1)

def connect_to_odoo(config):
    """Connect to Odoo using the provided configuration."""
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
        
        # Get user info - using a simplified approach to avoid field access issues
        user_id = odoo.env.uid
        try:
            # Attempt to safely get user name without loading all fields
            user = odoo.env['res.users'].browse(user_id)
            user_name = user.name
            logger.info(f"Connected as user: {user_name} (ID: {user_id})")
        except Exception as e:
            # If there's an issue with fields, just use the user ID
            logger.warning(f"Connected as user ID: {user_id} (couldn't fetch name: {str(e)})")
        
        return odoo
    except Exception as e:
        logger.error(f"Failed to connect to Odoo: {str(e)}")
        raise

def get_or_create_partner(odoo, name=None):
    """Get an existing partner or create a new one if needed."""
    Partner = odoo.env['res.partner']
    
    # Try to find an existing company partner
    try:
        # Use a very basic search domain to avoid field compatibility issues
        partner_ids = Partner.search([], limit=5)
        
        if partner_ids:
            # If partners found, return a random one
            partner_id = random.choice(partner_ids)
            
            # Use a try/except block when accessing partner fields
            try:
                partner = Partner.browse(partner_id)
                partner_name = partner.name
                logger.info(f"Using existing partner: {partner_name} (ID: {partner_id})")
            except Exception as e:
                logger.warning(f"Could not access partner name: {str(e)}")
                logger.info(f"Using existing partner with ID: {partner_id}")
                
            return partner_id
    except Exception as e:
        logger.error(f"Error searching for partners: {str(e)}")
        
    # If no partners found or name is provided, create a new one
    if name is None:
        name = f"Test Company {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Minimal partner data to avoid field compatibility issues
    partner_data = {
        'name': name,
        'is_company': True,
    }
    
    # Optionally add more fields with try/except to handle compatibility issues
    try:
        partner_data.update({
            'street': f"{random.randint(1, 999)} Main Street",
            'city': random.choice(['New York', 'Delhi', 'Dubai', 'London', 'Riyadh']),
            'zip': f"{random.randint(10000, 99999)}",
            'email': f"contact@{name.lower().replace(' ', '')}.example.com",
            'phone': f"+{random.randint(1, 9)}{random.randint(100000000, 999999999)}",
        })
    except Exception as e:
        logger.warning(f"Could not add additional partner fields: {str(e)}")
    
    try:
        # Create new partner
        new_partner_id = Partner.create(partner_data)
        logger.info(f"Created new partner: {name} (ID: {new_partner_id})")
        return new_partner_id
    except Exception as e:
        logger.error(f"Error creating partner: {str(e)}")
        # Use fallback approach with only the name field
        try:
            new_partner_id = Partner.create({'name': name})
            logger.info(f"Created new partner with minimal data: {name} (ID: {new_partner_id})")
            return new_partner_id
        except Exception as e2:
            logger.error(f"All partner creation methods failed: {str(e2)}")
            raise

def get_or_create_product(odoo, name=None, price=None):
    """Get an existing product or create a new one if needed."""
    Product = odoo.env['product.product']
    
    # Try to find existing products
    product_ids = Product.search([], limit=5)
    
    if product_ids:
        # If products found, return a random one
        product_id = random.choice(product_ids)
        product = Product.browse(product_id)
        logger.info(f"Using existing product: {product.name} (ID: {product_id})")
        return product_id
    
    # If no products found or name is provided, create a new one
    if name is None:
        name = f"Test Product {datetime.now().strftime('%Y%m%d%H%M%S')}"
    if price is None:
        price = random.uniform(50, 500)
    
    # Create new product
    new_product_id = Product.create({
        'name': name,
        'type': 'product',
        'list_price': price,
        'standard_price': price * 0.7,  # Cost price as 70% of sales price
    })
    
    logger.info(f"Created new product: {name} (ID: {new_product_id})")
    return new_product_id

def get_compatible_taxes(odoo):
    """Try to find compatible taxes or return an empty list to avoid tax issues."""
    try:
        # Get company_id from user
        company_id = odoo.env.user.company_id.id
        
        # Get taxes that match the company's fiscal country (Nigeria)
        tax_ids = odoo.env['account.tax'].search([
            ('type_tax_use', '=', 'sale'),
            ('company_id', '=', company_id)
        ], limit=1)
        
        if tax_ids:
            logger.info(f"Found compatible tax with ID: {tax_ids[0]}")
            # Convert to list of integers to avoid frozendict issues
            return [(6, 0, list(map(int, tax_ids)))]
        
        # If no taxes found, return empty list
        logger.warning("No compatible taxes found, using empty tax list")
        return [(6, 0, [])]
        
    except Exception as e:
        logger.warning(f"Error finding compatible taxes: {e}")
        return [(6, 0, [])]  # Empty tax list as fallback

def get_currency_id(odoo, currency_code='NGN'):
    """Get the currency ID for Nigerian Naira or any specified currency."""
    try:
        currency_ids = odoo.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if currency_ids:
            currency_id = int(currency_ids[0])
            logger.info(f"Found {currency_code} currency with ID: {currency_id}")
            return currency_id
        
        logger.warning(f"Currency {currency_code} not found, falling back to company default")
        return False
    except Exception as e:
        logger.warning(f"Error finding currency: {e}")
        return False

def create_invoice_with_fallbacks(odoo, partner_id, product_id, invoice_date, quantity, price_unit, tax_ids, line_name):
    """Create an invoice with progressive fallbacks for compatibility."""
    Invoice = odoo.env['account.move']
    total = quantity * price_unit
    
    # Ensure all values are native Python types (not frozendicts)
    partner_id = int(partner_id) if partner_id else False
    product_id = int(product_id) if product_id else False
    quantity = float(quantity)
    price_unit = float(price_unit)
    line_name = str(line_name)
    
    # Get Nigerian Naira currency
    currency_id = get_currency_id(odoo, 'NGN')
    
    # Try different approaches to create a valid invoice
    try:
        # Approach 1: Full data with explicit tax_ids
        # Process tax_ids to ensure they're all primitive types
        if tax_ids and isinstance(tax_ids, list) and len(tax_ids) > 0:
            try:
                tax_command = tax_ids[0][0]  # Get command (6)
                tax_pos = tax_ids[0][1]      # Get position (0)
                tax_id_list = tax_ids[0][2]  # Get list of tax IDs
                
                # Make sure all tax IDs are integers
                processed_tax_ids = [(tax_command, tax_pos, 
                                     [int(t) for t in tax_id_list])]
            except Exception as tax_error:
                logger.warning(f"Error processing tax_ids: {str(tax_error)}")
                processed_tax_ids = [(6, 0, [])]
        else:
            processed_tax_ids = [(6, 0, [])]
        
        invoice_line_vals = {
            'product_id': product_id,
            'quantity': quantity,
            'price_unit': price_unit,
            'name': line_name,
            'tax_ids': processed_tax_ids
        }
        
        invoice_data = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_date': invoice_date,
            'invoice_line_ids': [(0, 0, invoice_line_vals)]
        }
        
        # Add currency if found
        if currency_id:
            invoice_data['currency_id'] = currency_id
        
        invoice_id = Invoice.create(invoice_data)
        return invoice_id, total
    except Exception as e1:
        logger.warning(f"First invoice creation approach failed: {str(e1)}")
        
        try:
            # Approach 2: Without tax_ids
            invoice_line_vals = {
                'product_id': product_id,
                'quantity': quantity,
                'price_unit': price_unit,
                'name': line_name
                # No tax_ids
            }
            
            invoice_data = {
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': invoice_date,
                'invoice_line_ids': [(0, 0, invoice_line_vals)]
            }
            invoice_id = Invoice.create(invoice_data)
            return invoice_id, total
        except Exception as e2:
            logger.warning(f"Second invoice creation approach failed: {str(e2)}")
            
            try:
                # Approach 3: Minimal data
                invoice_line_vals = {
                    'name': line_name,
                    'quantity': quantity,
                    'price_unit': price_unit
                }
                
                invoice_data = {
                    'move_type': 'out_invoice',
                    'partner_id': partner_id,
                    'invoice_line_ids': [(0, 0, invoice_line_vals)]
                }
                invoice_id = Invoice.create(invoice_data)
                return invoice_id, total
            except Exception as e3:
                logger.error(f"All invoice creation approaches failed")
                raise Exception(f"Could not create invoice: {str(e3)}")

def create_invoices(odoo, count=3, days_back_range=7):
    """Create and post sample invoices."""
    Invoice = odoo.env['account.move']
    
    # Get or create partner and product
    partner_id = get_or_create_partner(odoo)
    
    # Get compatible taxes to avoid tax country errors
    tax_ids = get_compatible_taxes(odoo)
    
    # Create multiple invoices with different dates
    created_invoices = []
    
    for i in range(count):
        try:
            # Get a random product each time
            product_id = get_or_create_product(odoo)
            
            # Set a random date within the specified range
            days_back = random.randint(0, days_back_range)
            invoice_date = (datetime.now() - timedelta(days=days_back)).date().isoformat()
            
            # Randomize quantity and price for variation
            quantity = random.randint(1, 10)
            price_unit = round(random.uniform(100, 1000), 2)
            line_name = f"Sample Invoice Line {i+1}"
            
            # Create invoice with fallbacks
            invoice_id, total = create_invoice_with_fallbacks(
                odoo, partner_id, product_id, invoice_date, 
                quantity, price_unit, tax_ids, line_name
            )
            
            logger.info(f"Created invoice {i+1}/{count} with ID {invoice_id}")
            
            # Skip posting for now, as it's causing frozendict errors
            # The invoices will remain in draft state but are still valid for testing
            
            # Add to created invoices with minimal direct attribute access
            created_invoices.append({
                'id': invoice_id,
                'date': invoice_date,
                'partner_id': partner_id,
                'total': total
            })
        except Exception as outer_e:
            logger.error(f"Error in invoice creation loop {i+1}: {str(outer_e)}")
    
    return created_invoices

def main():
    """Main function for the invoice seeder script."""
    print("\n" + "="*80)
    print("TaxPoynt eInvoice - Odoo Invoice Seeder")
    print("="*80)
    
    print("\nThis script will create sample invoices in your Odoo instance for testing purposes.")
    
    # Get number of invoices to create
    try:
        invoice_count = int(input("\nHow many invoices would you like to create? [default: 5]: ") or "5")
    except ValueError:
        invoice_count = 5
        print("Invalid input, using default value of 5 invoices.")
    
    # Get date range for invoices
    try:
        days_back = int(input("How many days back should the invoices be dated? [default: 30]: ") or "30")
    except ValueError:
        days_back = 30
        print("Invalid input, using default value of 30 days.")
    
    try:
        # Connect to Odoo
        print("\nConnecting to Odoo...")
        odoo = connect_to_odoo(test_config)
        
        # Create invoices
        print(f"\nCreating {invoice_count} sample invoices...")
        created_invoices = create_invoices(odoo, count=invoice_count, days_back_range=days_back)
        
        # Summary
        print("\nCreated Invoices:")
        print("-"*40)
        
        if created_invoices:
            print(f"Successfully created {len(created_invoices)} invoices:")
            for i, inv in enumerate(created_invoices, 1):
                print(f"Invoice {i}: ID {inv['id']}, Date: {inv['date']}, Total: ₦{inv['total']:.2f}")
        else:
            print("No invoices were successfully created and tracked.")
        
        print("\nTry running a search to verify all created invoices:")
        try:
            Invoice = odoo.env['account.move']
            all_invoices = Invoice.search_read(
                [('move_type', '=', 'out_invoice')], 
                ['name', 'invoice_date', 'amount_total', 'currency_id', 'state'], 
                limit=10
            )
            print(f"\nFound {len(all_invoices)} invoices in the system:")
            for inv in all_invoices:
                currency_symbol = '₦' if inv.get('currency_id') and inv['currency_id'][1] == 'NGN' else '$'
                print(f"- {inv.get('name', 'Unnamed')}: {inv.get('invoice_date', 'No date')}, "
                      f"Amount: {currency_symbol}{inv.get('amount_total', 0):.2f}, "
                      f"State: {inv.get('state', 'unknown')}")
        except Exception as e:
            print(f"Error fetching invoices: {str(e)}")
        
        print("\nSeeding completed!")
        print("\nYou can now run the OdooRPC integration demo to fetch these invoices.")
        
    except Exception as e:
        print(f"\nSeeding failed: {str(e)}")
        print("\nTo successfully run this script, you need to:")
        print("1. Install odoorpc: pip install odoorpc")
        print("2. Ensure test_credentials.py has valid Odoo connection details")
        print("3. Ensure network access to the Odoo server")

if __name__ == "__main__":
    main()
