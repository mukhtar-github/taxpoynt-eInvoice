/**
 * Sample data utilities for FIRS API testing
 * Updated to comply with FIRS e-Invoice UBL standards and UUID4 requirements
 * Based on test_firs_api_uuid.py implementation
 */

import { v4 as uuidv4 } from 'uuid';

// Configuration
const USER_TIN = "31569955-0001";
const SERVICE_ID = "94ND90NR"; // FIRS-assigned 8-character Service ID

// Get a UUID4 business ID (In production, this would be stored and associated with the TIN)
export const getBusinessId = () => {
  return uuidv4();
};

// Get the TIN for tax identification fields
export const getTin = () => {
  return USER_TIN;
};

// Generate IRN according to FIRS specifications: InvoiceNumber-ServiceID-YYYYMMDD
export const generateIrn = (invoiceNumber: string, invoiceDate: Date = new Date()) => {
  if (!invoiceNumber) {
    throw new Error('Invoice number is required for IRN generation');
  }
  
  // Validate invoice number (alphanumeric only)
  if (!/^[a-zA-Z0-9]+$/.test(invoiceNumber)) {
    throw new Error('Invoice number must contain only alphanumeric characters');
  }
  
  // Format date as YYYYMMDD
  const dateStr = invoiceDate.toISOString().split('T')[0].replace(/-/g, '');
  
  // Construct IRN
  return `${invoiceNumber}-${SERVICE_ID}-${dateStr}`;
};

// Validate that an IRN follows the FIRS format requirements
export const validateIrn = (irn: string): {valid: boolean, error?: string} => {
  // Check overall format with regex
  const pattern = /^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$/;
  if (!pattern.test(irn)) {
    return { valid: false, error: 'Invalid IRN format' };
  }
  
  // Split and validate components
  const [invoiceNumber, serviceId, timestamp] = irn.split('-');
  
  // Validate invoice number
  if (!/^[a-zA-Z0-9]+$/.test(invoiceNumber)) {
    return { valid: false, error: 'Invoice number must contain only alphanumeric characters' };
  }
  
  // Validate service ID
  if (serviceId.length !== 8 || !/^[a-zA-Z0-9]{8}$/.test(serviceId)) {
    return { valid: false, error: 'Service ID must be exactly 8 alphanumeric characters' };
  }
  
  // Validate timestamp
  if (!/^\d{8}$/.test(timestamp)) {
    return { valid: false, error: 'Timestamp must be 8 digits in YYYYMMDD format' };
  }
  
  // Check if date is valid
  const year = parseInt(timestamp.substring(0, 4));
  const month = parseInt(timestamp.substring(4, 6)) - 1; // JS months are 0-based
  const day = parseInt(timestamp.substring(6, 8));
  const date = new Date(year, month, day);
  
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month ||
    date.getDate() !== day
  ) {
    return { valid: false, error: 'Invalid date in IRN' };
  }
  
  // Ensure date isn't in the future
  if (date > new Date()) {
    return { valid: false, error: 'IRN date cannot be in the future' };
  }
  
  return { valid: true };
};

/**
 * Generate a sample Odoo invoice for testing
 * @param variant Variant number to create slightly different invoices (for batch testing)
 * @returns Sample invoice object
 */
/**
 * Generate a sample Odoo invoice for testing
 * Updated to match UBL standards and include UUID4 format
 * @param variant Variant number to create slightly different invoices (for batch testing)
 * @returns Sample invoice object formatted for Odoo source data
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
      vat: "12345678901", // Customer TIN
      street: "Test Street",
      city: "Test City",
      email: "customer@example.com"
    },
    company_id: {
      id: 1,
      name: "TaxPoynt Ltd",
      vat: USER_TIN, // Company TIN
      street: "123 Tax Avenue",
      city: "Lagos",
      email: "info@taxpoynt.com"
    },
    invoice_line_ids: [
      {
        id: 1,
        name: "Consulting Services",
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
 * Updated to include UUID4 business ID and TIN separation
 * @returns Sample company info object
 */
export const getSampleCompany = () => {
  return {
    id: 1,
    business_id: getBusinessId(), // UUID4 format for FIRS API
    name: "TaxPoynt Ltd",
    tin: USER_TIN, // TIN for tax identification
    street: "123 Tax Avenue",
    city: "Lagos",
    state_id: { id: 1, name: "Lagos" },
    country_id: { id: 1, name: "Nigeria" },
    phone: "+234 1234567890",
    email: "info@taxpoynt.com",
    website: "https://taxpoynt.com",
    company_registry: "RC123456",
    currency_id: { id: 1, name: "NGN" }
  };
};

/**
 * Generate a sample FIRS API payload formatted according to FIRS-MBS E-Invoicing Documentation
 * This matches the structure in test_firs_api_uuid.py with proper IRN format
 * @returns FIRS API formatted invoice payload
 */
export const getFirsFormattedInvoice = () => {
  const businessId = getBusinessId();
  const tin = getTin();
  const now = new Date();
  const invoiceDate = now.toISOString().split('T')[0];
  const invoiceNumber = "INV001";
  
  // Generate proper IRN according to FIRS specifications
  const irn = generateIrn(invoiceNumber, now);
  
  // Validate the generated IRN
  const irnValidation = validateIrn(irn);
  if (!irnValidation.valid) {
    console.error(`Invalid IRN generated: ${irnValidation.error}`);
    // Still proceed with the best effort IRN
  }
  
  return {
    business_id: businessId, // UUID4 format as required by API
    invoice_reference: invoiceNumber,
    irn: irn, // Properly formatted IRN: InvoiceNumber-ServiceID-YYYYMMDD
    invoice_date: invoiceDate,
    invoice_type_code: "380", // Commercial Invoice
    supplier: {
      id: businessId, // UUID4 format
      tin: tin, // TIN for tax identification
      name: "TaxPoynt Ltd",
      address: "123 Tax Avenue, Lagos",
      email: "info@taxpoynt.com"
    },
    customer: {
      id: uuidv4(), // UUID4 format for customer ID
      tin: "98765432-0001", // Sample customer TIN
      name: "Sample Customer Ltd",
      address: "456 Customer Street, Abuja",
      email: "customer@example.com"
    },
    invoice_items: [
      {
        id: "ITEM001",
        name: "Consulting Services",
        quantity: 1,
        unit_price: 50000.00,
        total_amount: 50000.00,
        vat_amount: 7500.00, // 7.5% VAT
        vat_rate: 7.5
      }
    ],
    total_amount: 50000.00,
    vat_amount: 7500.00,
    currency_code: "NGN"
  };
};
