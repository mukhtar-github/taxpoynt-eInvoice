# Looking into OdooRPC

The user is asking about "OdooRPC for integration," which refers to the OdooRPC Python library, used for integrating with Odoo. It helps bridge the gap between Python and Odoo's API. I'll compose an explanation for the user, and because of guidelines, I need to gather the right citations. I'll grab details from my search for "OdooRPC library Python" and summarize the key information about this package, including its features, installation, and examples for usage. I'll be sure to cite the relevant sources in my response.

Here’s a concise overview of **OdooRPC**—a Python client library that makes integrating with Odoo’s RPC API effortless—and how you can use it in your FastAPI-based SI solution.

OdooRPC is an LGPL-licensed Python package authored by Sébastien Alix that wraps Odoo’s XML-RPC and JSON-RPC endpoints in a clean, ORM-like interface, letting you call model methods, browse records, and manage databases just like you would inside Odoo itself ([PyPI][1]). It supports named parameters, automatic user context (for translations), workflow execution, report downloads, and SSL-secured JSON-RPC calls ([Python Hosted][2]).

## Key Features

* **Full Model Access**: Call any model method—including `search`, `read`, `create`, `write`, and even `browse`—using a Pythonic API that mirrors the server side ([PyPI][1]).
* **Named Parameters & Context**: Pass parameters by name and have OdooRPC automatically include your user’s locale and language settings ([odoorpc.readthedocs.io][3]).
* **Database Management**: List, create, duplicate, or drop databases through the same interface you use for records ([PyPI][1]).
* **Workflow & Reports**: Execute Odoo workflow signals (`action_confirm`, etc.) and download PDF reports directly from Python ([PyPI][1]).
* **JSON-RPC Over SSL**: Use secure JSON-RPC (`jsonrpc+ssl` on port 443) when connecting to Odoo Online or self-hosted with HTTPS ([odoorpc.readthedocs.io][4]).

## Installation

Install from PyPI with pip:

```bash
pip install odoorpc
```

This pulls in no extra dependencies—just pure Python ([PyPI][1]).

## Basic Usage Example

```python
import odoorpc

# 1. Connect to your Odoo server
odoo = odoorpc.ODOO('your-odoo-domain.com', port=8069)

# 2. Authenticate
db, user, pwd = 'my_db', 'api_user@example.com', 'MY_API_KEY'
odoo.login(db, user, pwd)

# 3. Access models via odoo.env
#    e.g., fetch all posted customer invoices
Invoice = odoo.env['account.move']
ids     = Invoice.search([('move_type','=','out_invoice'), ('state','=','posted')])
invoices = Invoice.browse(ids)

for inv in invoices:
    print(inv.name, inv.invoice_date, inv.amount_total)
```

This code logs in, searches for all posted `out_invoice` records, and prints key fields ([PyPI][1]).

## Why Use OdooRPC in Your SI?

1. **Rapid Development**: No need to hand-craft XML-RPC calls or parse raw JSON; OdooRPC handles boilerplate.
2. **Maintainability**: The library closely follows Odoo’s data models—when you upgrade Odoo, your code remains readable.
3. **Security**: Supports SSL for JSON-RPC, and you can supply Odoo API keys just as you would passwords ([odoorpc.readthedocs.io][4]).
4. **Feature-Rich**: Everything from database listing to report downloads is one library—ideal for building robust integrations without plugin sprawl.

---

By integrating **OdooRPC** into your FastAPI backend, you’ll have a clean, maintainable bridge between Odoo and the FIRS e-Invoice workflow—ready to extract invoice data, map it to UBL, and push it through your SI’s IRN generation and validation pipeline.

[1]: https://pypi.org/project/OdooRPC/?utm_source=chatgpt.com "OdooRPC - PyPI"
[2]: https://pythonhosted.org/OdooRPC/?utm_source=chatgpt.com "Welcome to OdooRPC's documentation! - Pythonhosted.org"
[3]: https://odoorpc.readthedocs.io/en/latest/?utm_source=chatgpt.com "Welcome to OdooRPC's documentation! — OdooRPC 0.6.2 ..."
[4]: https://odoorpc.readthedocs.io/en/latest/faq.html?utm_source=chatgpt.com "Frequently Asked Questions (FAQ) — OdooRPC 0.6.2 documentation"
