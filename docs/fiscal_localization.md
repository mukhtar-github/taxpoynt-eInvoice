# Searching for fiscal localization guidance

The user needs help resolving the fiscal country issue in Odoo, which is causing tax compatibility errors when creating invoices. The problem likely stems from incorrect data types being passed (frozen dict versus a tuple). I'll start by searching for relevant details on Odoo's fiscal country settings, focusing on how they impact taxes and invoicing. I’ll look for high-quality sources to clarify both fiscal country setup and fixing the error, aiming for at least 10 relevant references.


**Resolving frozendict in invoices**

When building invoice lines, it’s essential to convert frozendicts into regular dictionaries. This can be done using `dict()` or `Model.browse`. Each step should be properly cited for reference, with Odoo documentation being a reliable source for company settings. I’ll need to quickly search for specific guidance like "Odoo set company country" to ensure everything aligns with the best practices outlined in those resources.

**Fixing fiscal country errors in Odoo**

To resolve the "incompatible taxes" issue, the main fix is to ensure that the company's fiscal country matches the tax country. It seems the script might be defaulting to a country like the U.S. To address it, I’ll update the company's country to Nigeria via the Odoo UI. Additionally, tax country fields must be set to Nigeria, either by leaving them blank or adjusting the `country_id`. For the frozendict error, I should check for misused data types in the OdooRPC call.


Here’s how to resolve the “taxes incompatible with your fiscal country” error and get sample invoices created successfully:

As you saw, Odoo enforces that each tax’s **Country** (in its advanced settings) matches your **Company’s Fiscal Country**; if these differ, invoice creation will be blocked by a validation error.

## 1. Set Your Company’s Fiscal Country to Nigeria

You must ensure the company record itself is domiciled in Nigeria.

1. In Odoo’s top bar, go to **Settings → Users & Companies → Companies** and select your company.
2. Under **General Information**, set **Country** to **Nigeria** and save.

## 2. Configure Each Tax’s Country to Nigeria

Each tax used on invoice lines must also specify Nigeria as its country:

1. Navigate to **Accounting → Configuration → Taxes**.
2. Click **Edit** on the tax(s) you’re applying to your demo invoices.
3. In **Advanced Options**, set the **Country** field to **Nigeria** and save.

## 3. (Optional) Install or Verify Nigeria Fiscal Localization

For full compliance, install the Nigeria fiscal localization package:

1. Go to **Accounting → Configuration → Settings**.
2. Scroll to **Fiscal Localization** and click **Install More Packages**.
3. Search for and install the **Nigeria** localization module.
4. Back in **Fiscal Localization**, select the **Nigeria** package and save.

> ⚠️ You can only switch localization packages if **no** accounting entries have been posted yet.

## 4. Clear the frozendict Error When Passing Invoice Data

The “keys must be str… not frozendict” error comes from passing OdooRPC’s immutable record objects directly into your `create()` call. Convert each line’s data to a plain dict before creating the invoice:

```python
# Instead of passing amls.tax_ids (a frozendict), do:
line_vals = dict(line)  
# or explicitly build:
line_vals = {
    'product_id': product_id,
    'quantity': qty,
    'price_unit': unit_price,
    'tax_ids': [(6, 0, [tax_id])],
}
# then: 
Invoice.create({
    'move_type': 'out_invoice',
    'partner_id': partner_id,
    'invoice_date': date_str,
    'invoice_line_ids': [(0, 0, line_vals)],
})
```

Converting to a native `dict` ensures OdooRPC sends only basic types (str, int, etc.) and avoids frozendict issues.

---

Once your **Company Country** and **Tax Country** both read “Nigeria,” and your invoice‐line dicts are native Python dicts, you’ll no longer hit the fiscal‐compatibility or frozendict errors—and you can seed and post sample invoices as intended.
