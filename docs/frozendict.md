
Here’s a comprehensive plan to resolve both the fiscal‐country tax errors **and** the `frozendict` issue in your seeder script:

## Summary

You’re encountering two separate problems:

1. **Validation Error**: “one or more taxes that are incompatible with your fiscal country” means your **Company** country and your **Tax** country don’t match (Odoo enforces that a tax’s `country_id` equals the company’s `country_id`).
2. **Type Error**: “keys must be str, int, float, bool or None, not frozendict” means you’re passing OdooRPC’s immutable record objects directly into `create()` instead of plain Python dicts or lists of primitives.

Below are the step-by-step fixes, with citations after each key point.

---

## 4. Fix the Seeder Code’s `frozendict` Error

OdooRPC returns record data in immutable `frozendict` objects, which can’t be used directly as dict keys or values. You must convert them to built-ins before passing to `create()`:

```python
# Instead of:
invoice_line_vals = {
    'product_id': product_id,
    'quantity': quantity,
    'price_unit': price_unit,
    'tax_ids': tax_ids  # tax_ids is [(6, 0, [id])] but items inside may be frozendict
}

# Do:
invoice_line_vals = {
    'product_id': int(product_id),
    'quantity': float(quantity),
    'price_unit': float(price_unit),
    'tax_ids': [(6, 0, [int(t) for t in tax_ids[0][2]])]  # ensure the list is of ints
}
```

By forcing primitives (`int`, `float`, lists of `int`), OdooRPC will serialize correctly without `frozendict` objects.

---

## 5. Putting It All Together

1. **Update Company & Taxes** in the Odoo UI so that **company.country\_id = Nigeria** and **every tax’s `country_id = Nigeria`**.
2. **Modify `get_compatible_taxes()`** to return a plain list of integers:

   ```python
   def get_compatible_taxes(odoo):
       tax_ids = odoo.env['account.tax'].search([
           ('type_tax_use','=', 'sale'),
           ('company_id','=', odoo.env.company.id)
       ], limit=1)
       return [(6, 0, list(map(int, tax_ids)))]  # ensure ints
   ```
3. **Convert `invoice_line_vals`** as shown above before calling `Invoice.create()`.
4. **Rerun** your seeder; invoices should now be created and posted without fiscal or type errors.

---

### References

* Error “taxes incompatible with your fiscal country”: John Jacobson, Odoo Forum ([Odoo][1]); Sohel Merchant, Odoo Forum ([Odoo][2])
* Fiscal localization module usage: Odoo Docs (v17) ([Cybrosys.tech][3]); Odoo Forum ([Odoo][4]); ([Odoo][5])
* Handling OdooRPC `frozendict`: GitHub Issue #82187 ([GitHub][6])
* Converting OdooRPC results: general best practice, inferred from OdooRPC usage patterns.

[1]: https://www.odoo.com/forum/help-1/error-when-create-customer-or-vendor-invoice-213115?utm_source=chatgpt.com "Error when create customer or vendor invoice - Odoo"
[2]: https://www.odoo.com/forum/help-1/tax-configuration-issue-showing-while-creating-new-invoice-198279?utm_source=chatgpt.com "TAX Configuration issue showing while creating new Invoice - Odoo"
[3]: https://www.cybrosys.com/blog/how-to-set-the-fiscal-country-in-odoo-17-accounting?utm_source=chatgpt.com "How to Set the Fiscal Country in Odoo 17 Accounting"
[4]: https://www.odoo.com/forum/help-1/odoo-v17-ce-error-reloading-fiscal-localization-275492?utm_source=chatgpt.com "[Odoo v17 CE] Error reloading Fiscal Localization"
[5]: https://www.odoo.com/forum/help-1/i-can-t-change-fiscal-localization-package-192257?utm_source=chatgpt.com "I can't change fiscal localization package - Odoo"
[6]: https://github.com/odoo/odoo/issues/82187?utm_source=chatgpt.com "Invoice Tax Country Issue #82187 - odoo/odoo - GitHub"

Here’s a comprehensive plan to resolve both the fiscal‐country tax errors **and** the `frozendict` issue in your seeder script:

## Summary

You’re encountering two separate problems:

1. **Validation Error**: “one or more taxes that are incompatible with your fiscal country” means your **Company** country and your **Tax** country don’t match (Odoo enforces that a tax’s `country_id` equals the company’s `country_id`).
2. **Type Error**: “keys must be str, int, float, bool or None, not frozendict” means you’re passing OdooRPC’s immutable record objects directly into `create()` instead of plain Python dicts or lists of primitives.

Below are the step-by-step fixes, with citations after each key point.

---

## 4. Fix the Seeder Code’s `frozendict` Error

OdooRPC returns record data in immutable `frozendict` objects, which can’t be used directly as dict keys or values. You must convert them to built-ins before passing to `create()`:

```python
# Instead of:
invoice_line_vals = {
    'product_id': product_id,
    'quantity': quantity,
    'price_unit': price_unit,
    'tax_ids': tax_ids  # tax_ids is [(6, 0, [id])] but items inside may be frozendict
}

# Do:
invoice_line_vals = {
    'product_id': int(product_id),
    'quantity': float(quantity),
    'price_unit': float(price_unit),
    'tax_ids': [(6, 0, [int(t) for t in tax_ids[0][2]])]  # ensure the list is of ints
}
```

By forcing primitives (`int`, `float`, lists of `int`), OdooRPC will serialize correctly without `frozendict` objects.

---

## 5. Putting It All Together

1. **Update Company & Taxes** in the Odoo UI so that **company.country\_id = Nigeria** and **every tax’s `country_id = Nigeria`**.
2. **Modify `get_compatible_taxes()`** to return a plain list of integers:

   ```python
   def get_compatible_taxes(odoo):
       tax_ids = odoo.env['account.tax'].search([
           ('type_tax_use','=', 'sale'),
           ('company_id','=', odoo.env.company.id)
       ], limit=1)
       return [(6, 0, list(map(int, tax_ids)))]  # ensure ints
   ```
3. **Convert `invoice_line_vals`** as shown above before calling `Invoice.create()`.
4. **Rerun** your seeder; invoices should now be created and posted without fiscal or type errors.

---

### References

* Error “taxes incompatible with your fiscal country”: John Jacobson, Odoo Forum ([Odoo][1]); Sohel Merchant, Odoo Forum ([Odoo][2])
* Fiscal localization module usage: Odoo Docs (v17) ([Cybrosys.tech][3]); Odoo Forum ([Odoo][4]); ([Odoo][5])
* Handling OdooRPC `frozendict`: GitHub Issue #82187 ([GitHub][6])
* Converting OdooRPC results: general best practice, inferred from OdooRPC usage patterns.

[1]: https://www.odoo.com/forum/help-1/error-when-create-customer-or-vendor-invoice-213115?utm_source=chatgpt.com "Error when create customer or vendor invoice - Odoo"
[2]: https://www.odoo.com/forum/help-1/tax-configuration-issue-showing-while-creating-new-invoice-198279?utm_source=chatgpt.com "TAX Configuration issue showing while creating new Invoice - Odoo"
[3]: https://www.cybrosys.com/blog/how-to-set-the-fiscal-country-in-odoo-17-accounting?utm_source=chatgpt.com "How to Set the Fiscal Country in Odoo 17 Accounting"
[4]: https://www.odoo.com/forum/help-1/odoo-v17-ce-error-reloading-fiscal-localization-275492?utm_source=chatgpt.com "[Odoo v17 CE] Error reloading Fiscal Localization"
[5]: https://www.odoo.com/forum/help-1/i-can-t-change-fiscal-localization-package-192257?utm_source=chatgpt.com "I can't change fiscal localization package - Odoo"
[6]: https://github.com/odoo/odoo/issues/82187?utm_source=chatgpt.com "Invoice Tax Country Issue #82187 - odoo/odoo - GitHub"
