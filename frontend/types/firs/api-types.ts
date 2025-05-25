/**
 * TypeScript interfaces for FIRS API requests and responses
 */

// Common validation issue structure
export interface ValidationIssue {
  field: string;
  message: string;
  code: string;
  invoice_index?: number; // Optional: used in batch submissions
  odoo_invoice_id?: number; // Optional: references the source invoice 
  odoo_invoice_name?: string; // Optional: human-readable invoice identifier
}

// Base submission response structure
export interface BaseSubmissionResponse {
  success: boolean;
  message: string;
  validation_issues: ValidationIssue[];
  environment?: 'sandbox' | 'production';
}

// Invoice submission request
export interface InvoiceSubmitRequest {
  odoo_invoice: Record<string, any>; // Odoo invoice data
  company_info: Record<string, any>; // Company information
  sandbox_mode?: boolean; // Optional: override environment setting
}

// Invoice submission response
export interface InvoiceSubmissionResponse extends BaseSubmissionResponse {
  submission_id?: string; // Present only when success is true
  firs_response?: Record<string, any>; // Raw FIRS API response details
}

// Submission status response
export interface SubmissionStatusResponse {
  submission_id: string;
  status: SubmissionStatus;
  timestamp: string; // ISO format timestamp
  message: string;
  details?: Record<string, any>; // Additional status details
  environment?: 'sandbox' | 'production';
}

// Batch submission response
export interface BatchSubmissionResponse extends BaseSubmissionResponse {
  batch_id?: string; // Present only when success is true
  invoice_count?: number;
  success_count?: number;
  failed_count?: number;
  invoice_mapping?: Record<string, any>; // Maps UBL invoices to Odoo sources
  firs_response?: Record<string, any>; // Raw FIRS API response details
}

// Possible submission statuses
export type SubmissionStatus = 
  | 'PENDING'
  | 'PROCESSING' 
  | 'COMPLETED' 
  | 'REJECTED' 
  | 'FAILED' 
  | 'ERROR'
  | 'UNKNOWN';

// Error response from API
export interface ApiErrorResponse {
  detail: {
    message: string;
    errors?: ValidationIssue[];
    environment?: 'sandbox' | 'production';
    status_code?: number;
    retry_after?: string;
  }
}

// Request options
export interface FirsApiRequestOptions {
  timeout?: number;
  headers?: Record<string, string>;
  useSandbox?: boolean;
  useUUID4?: boolean;
}

// API Service response (for our frontend service wrapper)
export interface ApiResponse<T> {
  message: string;
  data: T;
  status: number;
  success: boolean;
  error?: string;
}

// Authentication credentials
export interface AuthCredentials {
  token: string;
  expiresAt: number; // Timestamp in milliseconds
}
