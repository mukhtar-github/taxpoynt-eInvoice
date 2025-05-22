/**
 * Sample data utilities for FIRS API testing
 */

/**
 * Generate a sample Odoo invoice for testing
 * @param variant Variant number to create slightly different invoices (for batch testing)
 * @returns Sample invoice object
 */
export const getSampleInvoice = (variant = 1) => {
  const now = new Date();
  const invoiceDate = now.toISOString().split('T')[0];
  
  return {
    id: 12345 + variant,
    name: `INV/2025/0000${variant}`,
    invoice_date: invoiceDate,
    currency_id: { id: 1, name: "NGN" },
    amount_total: 1000.00 * variant,
    amount_untaxed: 900.00 * variant,
    amount_tax: 100.00 * variant,
    partner_id: {
      id: 1,
      name: "Test Customer",
      vat: "12345678901",
      street: "Test Street",
      city: "Test City"
    },
    company_id: {
      id: 1,
      name: "Test Company",
      vat: "98765432109",
    },
    invoice_line_ids: [
      {
        id: 1,
        name: "Test Product",
        quantity: 1.0 * variant,
        price_unit: 900.00,
        tax_ids: [{ id: 1, name: "VAT 7.5%", amount: 7.5 }],
        price_subtotal: 900.00 * variant,
        price_total: 1000.00 * variant
      }
    ]
  };
};

/**
 * Generate a sample company info object for testing
 * @returns Sample company info object
 */
export const getSampleCompany = () => {
  return {
    id: 1,
    name: "TaxPoynt Test Company Ltd",
    vat: "98765432109",
    street: "123 Company Street",
    city: "Lagos",
    state_id: { id: 1, name: "Lagos" },
    country_id: { id: 1, name: "Nigeria" },
    phone: "+234 1234567890",
    email: "info@testcompany.com",
    website: "https://testcompany.com",
    company_registry: "RC123456",
    currency_id: { id: 1, name: "NGN" }
  };
};
