Great, I’ll evaluate the best Odoo version, integration method (XML-RPC vs REST), and invoice retrieval strategy that align with your FastAPI-based FIRS System Integrator implementation.

I’ll prioritize an approach that ensures full UBL-compliant invoice extraction, supports real-time or batch sync depending on FIRS sandbox/API constraints, and leverages secure, scalable API access via Odoo external APIs. I’ll also consider maintainability and future multi-ERP extensibility.

# Recommended Odoo Version

For a new e‑Invoicing SI, use the latest stable Odoo with long‑term support (e.g. **Odoo 16 or 17**, released 2022–2023). Newer releases include performance optimizations and up‑to‑date documentation. Importantly, Odoo 16+ has built‑in support for BIS Billing 3.0 (UBL) e‑invoices in its Accounting EDI module. This means customer invoices can be exported directly as UBL BIS 3.0 XML when confirmed. Older versions (14/15) can work, but they lack some of the modern conveniences (e.g. user‑generated API keys in the profile). In practice, choosing Odoo 16 or later gives the best maintainability, community support, and UBL/E‑Invoicing features for Nigeria’s FIRS requirements.

# Integration API Options

Odoo’s *official* external API is RPC‑based (XML-RPC or JSON-RPC). There is **no native REST API** – Odoo’s external interface is a generic RPC API. You can call it via XML‑RPC or JSON‑RPC calls; JSON‑RPC is simpler (it’s what Odoo’s web client uses internally) and is well supported in Python. For example, Python libraries like **OdooRPC** (OCA) provide a high‑level interface to make XML/JSON-RPC calls as if they were native methods. Using Odoo’s RPC means you rely on the stable, documented API and avoid having to write custom server endpoints. This approach is secure (over HTTPS) and scales well.

By contrast, “REST” or GraphQL interfaces for Odoo come from custom/community modules (e.g. OCA GraphQL, Odoo REST modules, or Odoo.sh data APIs). Those can work but add complexity and maintenance burden. They often lag behind core releases and require extra modules. For a lean MVP, it’s usually preferable to use Odoo’s built‑in RPC API with a dedicated system user (or OdooRPC library). That ensures the SI code remains compatible across Odoo upgrades. Third‑party connectors (Python packages like **ERPpeek**, **openerp-client-lib**, **OdooRPC**, etc.) exist to simplify RPC calls. For example, OdooRPC (Python) lets you do `odoo = odoorpc.ODOO(...); odoo.login(...); odoo.env['account.move'].search_read(...)` just like normal ORM calls.

If a REST-like interface is desired, one could deploy an Odoo module that exposes specific endpoints, but this means custom code. For most SI work, XML/JSON‑RPC is sufficiently performant and better documented. It also lets you use the same credentials and access controls as the Odoo UI. In summary, plan to integrate *from your FastAPI backend to Odoo’s RPC endpoint*. Use HTTPS, a read‑only integration user (possibly with an API key), and call `models.execute_kw()` or equivalent JSON calls to fetch invoices.

# Retrieving Invoice Data

Use Odoo’s ORM models for invoices (the `account.move` model). For example, to get all posted sales invoices (type `out_invoice`), call something like:

```python
ids = models.execute_kw(db, uid, pwd, 'account.move', 'search',
    [[['move_type','=', 'out_invoice'], ['state','=','posted']]])
data = models.execute_kw(db, uid, pwd, 'account.move', 'read',
    [ids], {'fields': ['name','invoice_date','partner_id','invoice_line_ids', ...]})
```

Or equivalently use `search_read` with a domain filter and a fields list. By default `search_read` returns up to 100 records, but you can override that with `limit` and use `offset` to page through results. For example:

```python
models.execute_kw(db, uid, pwd, 'res.partner', 'name_search', ['ABC'], {'limit': 10})
```

is how the Odoo docs show using limit. In practice, for incremental sync you would filter by date or a “not yet sent” flag (e.g. invoices created since the last sync).

Invoice lines and tax details can be obtained via the one2many fields (e.g. `invoice_line_ids`) or additional reads on `account.move.line`. The Odoo EDI module can actually *generate* the full BIS 3.0 XML for an invoice when you confirm it (if enabled). You could leverage that to validate your mapping. But for the SI, you will likely read fields (invoice number, date, currency, partner tax IDs, line details, totals, etc.) and then construct the UBL output. Importantly, Odoo’s built-in models already hold all the needed data (VAT numbers, product descriptions, line taxes) to map to the BIS 3.0 structure.

# Mapping to BIS Billing 3.0 UBL

Nigeria’s FIRS e‑Invoice format is BIS Billing 3.0 (a UBL profile). Fortunately, Odoo already supports Peppol BIS 3.0 formats out of the box. The EDI export (under Accounting settings) can emit BIS 3.0 XML via Peppol access points. In your code, you have two choices: (a) rely on Odoo’s export by reading the XML attachment it creates, or (b) manually map fields. For an MVP, manually mapping is fine. The key fields are invoice header data (supplier/buyer info, invoice number/date, currency, total amounts), and each line’s details (item description, quantity, unit price, tax category, etc.). Odoo’s `res.partner.vat` can feed the tax ID fields, and `tax_line_ids` or `line_ids.tax_ids` give tax breakdowns. Ensure you include any Nigerian-specific tax fields required (e.g. VATIN). You may validate the output against the UBL schema.

Because Odoo’s model and form fields align with global e‑invoice standards, the mapping is straightforward. For example, Odoo’s partner country and VAT number map to UBL [cac\:PartyTaxScheme](cac:PartyTaxScheme) elements, and each account.move line becomes a [cac\:InvoiceLine](cac:InvoiceLine) with price, quantity, tax category, etc. The official Odoo docs and OCA examples (like the CBMS UBL module) can help verify that all fields are captured. In summary: use Odoo’s RPC to fetch invoices, then build the BIS 3.0 XML payload (or JSON if FIRS accepts JSON‑UBL) from those fields. Odoo’s own EDI code confirms that all required UBL elements are available in its `account.move` structure.

# Sync Strategy: Real‑Time vs Batch

**Clearance (B2B/B2G) vs Post‑Audit (B2C)**: Nigeria’s model uses a **real‑time clearance** approach for B2B/B2G invoices (CTC) – suppliers must submit each invoice to FIRS, which returns an IRN (Invoice Reference Number) and CSID (stamp) before delivery. B2C invoices can be reported up to 24h after issuance.  Therefore, in practice: for clearance invoices, strive for near-real‑time submission. For B2C, periodic batch submission is acceptable (e.g. hourly or daily).

**Odoo Performance**: Fetching a single invoice via RPC is quick; even hundreds per minute are feasible. For an MVP, a **short polling loop** (e.g. check for new invoices every 5–15 minutes) is simplest. Your FastAPI service can run a background task or cron that does `search_read` for recently posted invoices not yet sent. If pilot volume is low, this is more than sufficient.  In the future, you could refine with webhooks or OCA “outbound API” modules, but initially polling is easiest to implement and test.  Ensure to page through results if many invoices are found at once (use `offset`/`limit`).

**Error Recovery and Idempotency**: Make each invoice submission atomic – track success/failure per invoice (e.g. update an Odoo field or your DB flag). On failure, log the error (or FIRS rejection), and retry later. Use idempotent logic: don’t resubmit an invoice that already got an IRN. For clearance invoices, you may choose to block delivery until IRN is obtained, or send invoices marked “pending IRN” back to clients. Ensure your integrator records the IRN and stamp in your system after each successful submission. Robust logging and monitoring in your FastAPI layer will give SI observability (e.g. log every HTTP/JSON request to FIRS, responses, and any exceptions).

# Security and Authentication

**Odoo Side:** Always use HTTPS to connect. Create a dedicated Odoo user with minimum required rights (read access on invoices and related partners/products). Since Odoo 14, users can generate **Developer API Keys** in their profile (Account → Security) which can substitute as a password in RPC calls. Store that key securely in your FastAPI config. When calling `execute_kw`, pass the API key instead of the user password. This avoids using a real password in scripts. Odoo’s `xmlrpc/2/common` endpoint is used to authenticate (get a uid) and then `xmlrpc/2/object` for data calls. If you use OdooRPC, it handles the login step for you. Odoo Online or Odoo.sh instances may require an explicit password set on the user (as per Odoo’s docs) before allowing RPC access.

**FIRS Side:** Your FastAPI will call the FIRS/MBS APIs. Those will likely require OAuth or API tokens (details will come from FIRS). For now assume a secured REST/JSON API. Store those credentials safely. Because BIS 3.0 is XML, ensure you also handle HTTPS certificate validation. Plan for testing against FIRS’s sandbox environment before go-live.

Note: Odoo has no built‑in OAuth2 for its API; any OAuth2 support is via extra modules. For MVP, basic auth with API key (per above) is sufficient. In summary, secure both ends: use SSL/TLS, limited‑scope integration accounts, and rotation of keys/passwords as per best practice.

# Data Limits and Pagination

Odoo’s API enforces a default limit of 100 records per `search_read` call. In practice, always specify a reasonable `limit` (e.g. 500 or 1000) and use `offset` to page if more rows match. Also leverage domain filters to only retrieve needed invoices (e.g. by date range or status). Sorting is done by `order` parameter if needed (e.g. `order=[('invoice_date','asc')]`). If there are thousands of invoices per sync, break the job into pages. This prevents timeouts or memory issues. The Odoo documentation explicitly shows using `limit` and `offset` on RPC calls to manage large sets.

# Recommendation Summary

For a lightweight MVP integration to Nigeria’s FIRS e‑Invoicing:

* **Odoo Version:** Use Odoo 16 or newer (current stable), which has the best API and built-in BIS 3.0 EDI support.
* **API Approach:** Use Odoo’s standard XML/JSON‑RPC API from your FastAPI service. JSON‑RPC (via `execute_kw`) is recommended. Employ a Python connector library (e.g. OdooRPC) for convenience. Avoid custom REST or GraphQL modules for the MVP – they add complexity without significant benefit.
* **Invoice Extraction:** In each sync, call `account.move.search_read` (or search + read) for posted customer invoices (`move_type='out_invoice'`) that haven’t been sent yet. Retrieve all relevant fields (invoice header, line items, taxes, partner VAT, etc.) and map them into the BIS 3.0 XML structure. Note that Odoo can auto-generate BIS 3.0 XML if you enable its EDI formats, which can guide your mapping.
* **Sync Mode:** For B2B/B2G invoices (clearance model), submit them in near-real time. In practice, running the sync every few minutes is usually sufficient to meet “pre‑validation” needs. For B2C (post-audit), schedule a periodic batch (e.g. end‑of‑day or every few hours) since FIRS allows up to 24h delay. Use unique invoice IDs to avoid double‑posting.
* **Error Handling:** Log all submissions and responses. On failure (network issue or FIRS rejection), retry automatically and/or alert SI engineers. Store the FIRS IRN/CSID from successful submissions in your database. Design the process idempotently (mark each invoice as “Sent” once done) to simplify retries.
* **Security:** Connect to Odoo over HTTPS. Use a dedicated integration user with an Odoo API key (instead of password) for RPC authentication. Likewise, use secure credentials for FIRS. Keep keys and tokens out of source code (use environment variables or a secrets manager).
* **Pagination:** Always use `limit` (and optionally `offset`/`order`) on Odoo RPC calls to page through data. This prevents hitting default caps and allows large data sets (useful in heavier syncs or full history pulls).
* **MVP Focus:** For the Minimum Viable Product, a simple FastAPI service with scheduled polling of Odoo is sufficient. It can first work with Odoo’s BIS 3.0 XML export (for sanity checking) and then call the FIRS sandbox APIs to generate IRNs and validate invoices. This aligns with the SI roadmap (FIRS certification, IRN issuance, validation, sandbox tests). Once stable on Odoo, the architecture (ERP data → UBL → FIRS) can be generalized to other ERPs as planned.

**Sources:** Odoo’s developer docs and community Q\&A clearly state that the external API is RPC-based (no native REST), and list tools like *OdooRPC* for integration. Odoo’s accounting docs confirm built‑in support for BIS 3.0 (Peppol) e‑invoices. FIRS guidance (via Sovos and stakeholder publications) outlines the clearance vs post‑audit models, driving the sync strategy. And Odoo forums note the RPC call limits and API key use. These confirm that using the standard Odoo RPC API (with pagination and secure auth) is the most practical and maintainable approach for the SI MVP.
