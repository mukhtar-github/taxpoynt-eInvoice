# Checking demo\_config setup

The user seems to be confirming if their demo\_config with credentials is set up correctly. I’m thinking the URL should exclude "/odoo" from the domain, like "taxpoyntcom2.odoo.com." Standard Odoo endpoints are XMLRPC paths at "/xmlrpc/2/common" and "/xmlrpc/2/object." If they're using OdooRPC, the host would be "taxpoyntcom2.odoo.com," port 443, with HTTPS. The config should also use the API key as the password. I need to look up specific OdooRPC documentation for more confirmation.

Your `demo_config` is almost right—but a few tweaks will make it work smoothly with OdooRPC’s expectations:

1. **URL should be the host (and optional base path), not including “/odoo”**
   OdooRPC expects you to supply the host (and port) and, if your instance is served under a URL prefix, pass that separately or include it as `base_url`. If you point `url` at `https://taxpoyntcom2.odoo.com/odoo`, RPC calls will try to reach `https://taxpoyntcom2.odoo.com/odoo/xmlrpc/...`, which often does **not** exist.

   * **Correct**:

     ```python
     demo_config = {
         "host": "taxpoyntcom2.odoo.com",       # your Odoo domain
         "port": 443,                           # default HTTPS port
         "protocol": "jsonrpc+ssl",             # or "xmlrpc+ssl"
         "base_url": "",                        # leave empty unless Odoo is under a path
         "database": "taxpoyntcom2",
         "username": "mukhtartanimu885@gmail.com",
         "password": "484d77d768223e891b233250941f95119054f035",
         "use_api_key": True
     }
     ```
   * **Why**: The typical endpoints are `https://<host>/xmlrpc/2/common` and `/xmlrpc/2/object` (or `/jsonrpc`), not under `/odoo/xmlrpc`. ([Odoo][1])

2. **Use API key correctly**
   Setting `use_api_key: True` means your “password” field **must** be the API key you generated in Odoo (which you already have). That part is correct.

   * When you call:

     ```python
     import odoorpc
     odoo = odoorpc.ODOO(
         demo_config["host"],
         protocol=demo_config["protocol"],
         port=demo_config["port"],
         base_url=demo_config["base_url"]
     )
     odoo.login(
         demo_config["database"],
         demo_config["username"],
         demo_config["password"]
     )
     ```
   * Under the hood this uses JSON-RPC over SSL with your API key as the password ([Python Hosted][2]).

3. **Summary of changes**

   * **Host vs URL**: Use `host`, `port` and optional `base_url` instead of a full `/odoo` path.
   * **Protocol**: Explicitly set `protocol="jsonrpc+ssl"` (or `xmlrpc+ssl`) for secure RPC.
   * **API key**: `password` remains your API key and `use_api_key=True` tells your code to treat it as such.

With those tweaks, your FastAPI backend will authenticate correctly and talk to Odoo’s External API.

[1]: https://www.odoo.com/documentation/18.0/developer/howtos/web_services.html?utm_source=chatgpt.com "Web Services — Odoo 18.0 documentation"
[2]: https://pythonhosted.org/OdooRPC/?utm_source=chatgpt.com "Welcome to OdooRPC's documentation! - Pythonhosted.org"
