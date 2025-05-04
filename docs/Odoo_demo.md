# Considering Odoo demo options
Here’s how you can populate your demo database with sample invoices so your SI integration demo actually has data to fetch:

---

## Summary

Since the default demo database often comes with products and partners but no posted invoices, you have four easy options to get test invoices:

---

## Programmatic Invoice Generation via OdooRPC

Script sample invoices directly—ideal for embedding in your FastAPI demo:

```python
import odoorpc
from datetime import date

# 1) Connect
odoo = odoorpc.ODOO('your-odoo-domain.com', protocol='jsonrpc+ssl', port=443)
odoo.login('your_db', 'api_user@example.com', 'YOUR_API_KEY')

# 2) Prepare references
Partner = odoo.env['res.partner']
Product = odoo.env['product.product']
Invoice = odoo.env['account.move']

# 3) Pick a partner and product (or create them)
partner_ids = Partner.search([('is_company','=',True)], limit=1)
product_ids = Product.search([], limit=1)

# 4) Create and post 3 sample invoices
for i in range(1,4):
    inv_id = Invoice.create({
        'move_type': 'out_invoice',
        'partner_id': partner_ids[0],
        'invoice_date': date.today().isoformat(),
        'invoice_line_ids': [(0, 0, {
            'product_id': product_ids[0],
            'quantity': i,
            'price_unit': 150.0,
        })],
    })
    # post the invoice (change state from draft → posted)
    Invoice.browse(inv_id).action_post()
    print(f"Created and posted invoice ID {inv_id}")

# Now these invoices will appear when you fetch via your SI integration
```

**Why use this?**

* Fully repeatable and parameterized—ideal for demos.
* You control counts, dates, quantities, prices.
* No manual UI steps or CSV mess.

---

### Putting It Into Your Demo

* **On App Startup:** Have a “demo seed” endpoint in FastAPI that runs the above script, so clicking “Load Demo Invoices” populates your Odoo DB.
* **After Seeding:** Invoke your existing invoice‐fetch routine—now it will retrieve the new invoices and proceed through IRN generation and validation.

Choose the approach that best fits your demo flow. For a fast, hands-off setup, creating a fresh demo DB is unbeatable; for scriptable control, the OdooRPC method gives you precise test data every time.
