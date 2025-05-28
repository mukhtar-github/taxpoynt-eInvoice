/**
 * Common API response types for the TaxPoynt eInvoice system
 */

// Base API response interface that all responses extend
export interface APIResponse {
  success: boolean;
  message?: string;
}

// Pagination metadata
export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

// Error response
export interface APIErrorResponse extends APIResponse {
  success: false;
  error: string;
  status_code?: number;
  details?: Record<string, any>;
}

// Integration objects
export interface Integration {
  id: string;
  name: string;
  description: string;
  integration_type: string;
  status: string;
  created_at: string;
  last_sync?: string;
  config: Record<string, any>;
}

export interface IntegrationsResponse extends APIResponse {
  success: true;
  integrations: Integration[];
  pagination?: PaginationMeta;
}

export interface IntegrationResponse extends APIResponse {
  success: true;
  integration: Integration;
}

// Company info
export interface CompanyInfo {
  id: number;
  name: string;
  vat?: string;
  phone?: string;
  email?: string;
  website?: string;
  street?: string;
  street2?: string;
  city?: string;
  state?: string;
  zip?: string;
  country?: string;
  currency?: string;
}

export interface CompanyInfoResponse extends APIResponse {
  success: true;
  company: CompanyInfo;
}

// Invoice interfaces
export interface Invoice {
  id: string | number;
  name: string;
  partner_id: {
    id: number;
    name: string;
  };
  date: string;
  amount_total: number;
  state: string;
  currency?: string;
}

export interface InvoicesResponse extends APIResponse {
  success: true;
  invoices: Invoice[];
  total: number;
  currency?: string;
  pagination?: PaginationMeta;
}

// Customer interfaces
export interface Customer {
  id: string | number;
  name: string;
  email?: string;
  phone?: string;
  street?: string;
  city?: string;
  state_id?: {
    id: number;
    name: string;
  };
  zip?: string;
  country_id?: {
    id: number;
    name: string;
  };
  vat?: string;
  is_company?: boolean;
  create_date?: string;
}

export interface CustomersResponse extends APIResponse {
  success: true;
  customers: Customer[];
  total: number;
  pagination?: PaginationMeta;
}

// Product interfaces
export interface Product {
  id: string | number;
  name: string;
  default_code?: string;
  description?: string;
  list_price: number;
  currency_id?: {
    id: number;
    name: string;
  };
  categ_id?: {
    id: number;
    name: string;
  };
  type?: string;
  taxes_id?: any[];
  qty_available?: number;
}

export interface ProductsResponse extends APIResponse {
  success: true;
  products: Product[];
  total: number;
  currency?: string;
  pagination?: PaginationMeta;
}

// Generic ERP interfaces for the common components
export interface GenericInvoice {
  id: string | number;
  number: string;
  customerName: string;
  date: string;
  amount: number;
  status: string;
  currency?: string;
  [key: string]: any;
}

export interface GenericCustomer {
  id: string | number;
  name: string;
  email?: string;
  phone?: string;
  address?: {
    street?: string;
    city?: string;
    state?: string;
    zip?: string;
    country?: string;
  };
  taxId?: string;
  type?: string;
  createdAt?: string;
  [key: string]: any;
}

export interface GenericProduct {
  id: string | number;
  name: string;
  code?: string;
  description?: string;
  price: number;
  currency?: string;
  category?: string;
  type?: string;
  taxRate?: number;
  taxable?: boolean;
  stockQuantity?: number;
  [key: string]: any;
}
