# Accessing Odoo's External API

The user has provided a subscription code (M250502221895097) for Odoo's external API and is asking how to start using it. Based on the previous context, it seems they're referring to the Odoo external API after subscription. To begin, typically, you would need to authenticate with the API using your subscription details or create an online database for it. The next steps may involve extracting the relevant API documentation and following their guidelines for integration.

**Accessing Odoo API after Subscription**

To begin using the Odoo external API after subscription, follow these steps:

1. Retrieve the API key: Go to the Odoo UI, navigate to User > Preferences > API Keys.
2. Identify your Odoo host URL.
3. Use JSON-RPC for API calls: Endpoint example - `https://your-odoo.com/jsonrpc`.
4. Use `odoorpc` in Python for integration.
5. Example cURL command.
6. When using the subscription code (M250502221895097), ensure it's used as the database parameter or part of the URL, depending on your setup. If using Odoo.sh or SaaS, check for access to REST/GraphQL endpoints.


Once your subscription code is live, using Odoo’s “External API” is really just a matter of getting your Odoo-installed instance to expose its RPC interface over HTTPS and then authenticating with an API key. Here’s how to get started in 5 steps:

---

## 1. Enable & Locate Your Odoo Endpoint

1. **Ensure your Odoo instance is reachable over HTTPS.**
   If you’re on Odoo.sh or have your own server, make sure you’ve configured SSL (Let’s Encrypt, etc.) so that all RPC calls go to `https://your-odoo-domain.com`.
2. **Confirm the RPC paths:**

   * **Authentication (common):** `https://your-odoo-domain.com/xmlrpc/2/common`
   * **Object calls (models):** `https://your-odoo-domain.com/xmlrpc/2/object`
   * **Optional JSON-RPC:** `https://your-odoo-domain.com/jsonrpc`

---

## 2. Create an Odoo API Key

1. **Log into Odoo as the integration user** (or your own user if you prefer).
2. **Activate developer mode:**

   * Click your user name → Preferences → Activate the “Developer Mode” toggle.
3. **Generate an API Key:**

   * In Preferences (while in dev mode), scroll down to “API Keys” → click **“New”**.
   * Give it a name (“SI Integration Key”), then copy the generated key.
4. **Store the key** in your FastAPI app’s environment variables (`ODOO_API_KEY`)—never check it into source control.

---

## 3. Authenticate & Obtain a User ID

You need two pieces of info: the database name (e.g. `odoo_db`), your user’s login (email), and the API key as password.

### Example with Python + `xmlrpc.client`:

```python
import xmlrpc.client
import os

ODOO_URL    = "https://your-odoo-domain.com"
DB          = "odoo_db"
USERNAME    = "you@company.com"
API_KEY     = os.getenv("ODOO_API_KEY")  # your new key

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, API_KEY, {})
print("Authenticated, user ID =", uid)
```

If `uid` is non-zero, you’re good to go.

---

## 4. Call the “External API” to Read Invoices

Once you have `uid`, use the object endpoint to fetch `account.move` records:

```python
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# 1) Search for all posted customer invoices not yet sent to FIRS
invoice_ids = models.execute_kw(
    DB, uid, API_KEY,
    'account.move', 'search',
    [[
        ['move_type', '=', 'out_invoice'],
        ['state', '=', 'posted'],
        ['your_custom_flag', '=', False]  # e.g. not yet sent
    ]]
)

# 2) Read the details you need
invoices = models.execute_kw(
    DB, uid, API_KEY,
    'account.move', 'read',
    [invoice_ids],
    {
      'fields': [
        'name', 'invoice_date', 'invoice_line_ids',
        'partner_id', 'amount_total', 'currency_id', /* etc. */
      ]
    }
)

print(invoices)
```

You can then map that payload into your BIS 3.0 UBL XML and push it off to FIRS.

---

## 5. Test with cURL (Optional)

If you just want a quick sanity check, you can do:

```bash
curl -X POST https://your-odoo-domain.com/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "service": "common",
      "method": "authenticate",
      "args": ["odoo_db", "you@company.com", "M250502221895097", {}]
    },
    "id": 1
  }'
```

Replace `"M250502221895097"` with your API key. A valid response with a non-zero `result` is your user ID. Then switch `"service": "object"` and call methods like `search_read` for models.

---

### Next Steps

1. **Build your FastAPI wrappers** around these RPC calls.
2. **Schedule** a background job to poll new invoices (every 5–15 min for B2B, or nightly for B2C).
3. **Map** the invoice data to UBL and submit to the FIRS sandbox via your FIRS API client.
4. **Log** all responses (IRN, CSID) and mark invoices as “sent” in Odoo.

With those pieces in place, you’ll have “External API” access to Odoo and be ready to feed data into your FIRS e-invoicing pipeline.

## Web Services
In order to programmatically retrieve the list of the databases displayed in the database manager, call the method list of the model odoo.database via a Web Service call.

Inspired from the examples provided in the Web Services section, this is how to retrieve this list with the library xmlrpc.client:
```xml
import xmlrpc.client

USER = 'user@domain.tld'
APIKEY = 'your_apikey'

root = 'https://www.odoo.com/xmlrpc/'
uid = xmlrpc.client.ServerProxy(root + 'common').login('openerp', USER, APIKEY)
sock = xmlrpc.client.ServerProxy(root + 'object')
databases_list = sock.execute('openerp', uid, APIKEY, 'odoo.database', 'list')
```

### And here is the equivalent example with JSON-RPC:
```json
import json
import random
import urllib.request

USER = 'user@domain.tld'
APIKEY = 'your_apikey'

def json_rpc(url, method, params):
    data = {
        'jsonrpc': '2.0',
        'method': method,
        'params': params,
        'id': random.randint(0, 1000000000),
    }
    req = urllib.request.Request(url=url, data=json.dumps(data).encode(), headers={
        "Content-Type": "application/json",
    })
    reply = json.loads(urllib.request.urlopen(req).read().decode('UTF-8'))
    if reply.get('error'):
        raise Exception(reply['error'])
    return reply['result']

def call(url, service, method, *args):
    return json_rpc(url, 'call', {'service': service, 'method': method, 'args': args})

url = 'https://www.odoo.com/jsonrpc'
uid = call(url, 'common', 'login', 'openerp', USER, APIKEY)
databases_list = call(url, 'object', 'execute', 'openerp', uid, APIKEY, 'odoo.database', 'list')
```