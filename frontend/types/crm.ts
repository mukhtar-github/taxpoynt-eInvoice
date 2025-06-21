/**
 * TypeScript definitions for CRM integration features.
 * 
 * This module provides comprehensive type definitions for CRM integrations,
 * specifically focusing on HubSpot integration patterns and data structures.
 */

// ==================== BASE TYPES ====================

export interface APIResponse {
  success: boolean;
  message?: string;
  timestamp?: string;
}

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
  next_page?: number;
  prev_page?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
  next_page?: number;
  prev_page?: number;
}

// ==================== CRM CONNECTION TYPES ====================

export type CRMType = 'hubspot' | 'salesforce' | 'pipedrive' | 'zoho' | 'custom';

export interface CRMConnectionCreate {
  crm_type: CRMType;
  connection_name: string;
  credentials: Record<string, any>;
  connection_settings?: Record<string, any>;
  webhook_secret?: string;
}

export interface CRMConnectionUpdate {
  connection_name?: string;
  credentials?: Record<string, any>;
  connection_settings?: Record<string, any>;
  webhook_secret?: string;
  is_active?: boolean;
}

export interface CRMConnection {
  id: string;
  crm_type: CRMType;
  connection_name: string;
  name: string; // Alias for connection_name for compatibility
  is_active: boolean;
  status: 'connected' | 'connecting' | 'failed' | 'pending';
  last_sync_at?: string;
  last_sync?: string; // Alias for last_sync_at for compatibility
  created_at: string;
  updated_at?: string;
  webhook_url?: string;
  connection_settings?: Record<string, any>;
  total_deals?: number;
  total_invoices?: number;
}

export interface CRMConnectionTestResult {
  success: boolean;
  message: string;
  platform_info?: Record<string, any>;
  error_details?: Record<string, any>;
}

// ==================== CRM DEAL TYPES ====================

export interface CRMDeal {
  id: string;
  external_deal_id: string;
  deal_title?: string;
  deal_amount?: number;
  customer_data?: Record<string, any>;
  deal_stage?: string;
  expected_close_date?: string;
  invoice_generated: boolean;
  invoice_id?: string;
  deal_metadata?: Record<string, any>;
  created_at: string;
  updated_at?: string;
}

export interface DealProcessRequest {
  action: 'sync' | 'generate_invoice' | 'cancel';
  force?: boolean;
}

// ==================== HUBSPOT SPECIFIC TYPES ====================

export interface HubSpotCredentials {
  auth_type: 'oauth2';
  client_id: string;
  client_secret: string;
  refresh_token?: string;
  access_token?: string;
  token_expires_at?: string;
}

export interface HubSpotConnectionConfig {
  connection_id?: string;
  organization_id: string;
  user_id: string;
  connection_name?: string;
  auth: {
    auth_type: 'oauth2';
    token_url: string;
    scope: string;
    credentials: HubSpotCredentials;
  };
  settings?: {
    deal_stage_mapping?: Record<string, string>;
    auto_generate_invoice_on_creation?: boolean;
    sync_interval_hours?: number;
    webhook_events?: string[];
  };
}

export interface HubSpotDeal {
  id: string;
  deal_name: string;
  amount?: number;
  deal_stage: string;
  close_date?: string;
  create_date?: string;
  owner_id?: string;
  properties?: Record<string, any>;
}

export interface HubSpotCustomer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  is_company: boolean;
}

export interface HubSpotDealInvoice {
  deal_id: string;
  invoice_number: string;
  invoice_date: string;
  due_date?: string;
  amount: number;
  currency: string;
  customer: HubSpotCustomer;
  description?: string;
  line_items: Array<{
    description: string;
    quantity: number;
    unit_price: number;
    amount: number;
  }>;
  metadata?: Record<string, any>;
}

// ==================== OAUTH FLOW TYPES ====================

export interface OAuthState {
  state: string;
  redirect_uri: string;
  code_verifier?: string;
  connection_id?: string;
}

export interface OAuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  scope: string;
}

export interface OAuthError {
  error: string;
  error_description?: string;
  error_uri?: string;
}

// ==================== UI COMPONENT TYPES ====================

export interface ConnectionFormData {
  connection_name: string;
  crm_type: CRMType;
  auth_method: 'oauth2' | 'api_key';
  client_id?: string;
  client_secret?: string;
  api_key?: string;
  webhook_secret?: string;
  settings?: {
    auto_sync_deals?: boolean;
    sync_interval_hours?: number;
    deal_stage_mapping?: Record<string, string>;
    auto_generate_invoice?: boolean;
  };
}

export interface DealFilters {
  stage?: string;
  invoice_status?: 'generated' | 'pending' | 'all';
  date_range?: {
    start_date?: string;
    end_date?: string;
  };
  search?: string;
  sort_by?: 'created_at' | 'amount' | 'close_date' | 'deal_title';
  sort_order?: 'asc' | 'desc';
}

export interface DealListItem {
  id: string;
  external_deal_id: string;
  deal_title: string;
  deal_amount: number;
  deal_stage: string;
  customer_name?: string;
  expected_close_date?: string;
  invoice_generated: boolean;
  invoice_id?: string;
  created_at: string;
  connection_name: string;
}

// ==================== API RESPONSE TYPES ====================

export interface CRMConnectionsResponse extends APIResponse {
  success: true;
  connections: PaginatedResponse<CRMConnection>;
}

export interface CRMConnectionResponse extends APIResponse {
  success: true;
  connection: CRMConnection;
}

export interface CRMDealsResponse extends APIResponse {
  success: true;
  deals: PaginatedResponse<CRMDeal>;
}

export interface CRMDealResponse extends APIResponse {
  success: true;
  deal: CRMDeal;
}

export interface DealProcessResponse extends APIResponse {
  success: true;
  result: {
    deal_id: string;
    connection_id: string;
    action: string;
    processed_at: string;
    invoice_generated?: boolean;
    invoice_id?: string;
  };
}

export interface ConnectionSyncResponse extends APIResponse {
  success: true;
  result: {
    connection_id: string;
    platform: string;
    deals_processed: number;
    invoices_generated: number;
    synced_at: string;
  };
}

// ==================== ERROR TYPES ====================

export interface CRMError {
  code: string;
  message: string;
  details?: Record<string, any>;
  field?: string;
}

export interface CRMErrorResponse extends APIResponse {
  success: false;
  error: string;
  errors?: CRMError[];
  status_code?: number;
}

// ==================== COMPONENT STATE TYPES ====================

export interface ConnectionState {
  isLoading: boolean;
  isConnecting: boolean;
  isTesting: boolean;
  connections: CRMConnection[];
  selectedConnection?: CRMConnection;
  error?: string;
  testResult?: CRMConnectionTestResult;
}

export interface DealState {
  isLoading: boolean;
  isProcessing: boolean;
  deals: CRMDeal[];
  selectedDeals: string[];
  filters: DealFilters;
  pagination: PaginationMeta;
  error?: string;
}

export interface InvoiceGenerationState {
  isGenerating: boolean;
  generationProgress?: {
    current: number;
    total: number;
    status: string;
  };
  generatedInvoices: Array<{
    deal_id: string;
    invoice_id: string;
    status: 'success' | 'error';
    error?: string;
  }>;
  error?: string;
}

// ==================== EVENT TYPES ====================

export interface CRMEvent {
  type: 'connection_created' | 'connection_updated' | 'deal_synced' | 'invoice_generated';
  timestamp: string;
  data: Record<string, any>;
}

export interface WebhookEvent {
  event_id: string;
  event_type: string;
  object_id: string;
  connection_id: string;
  timestamp: string;
  data: Record<string, any>;
}

// ==================== FORM VALIDATION SCHEMAS ====================

export interface ValidationSchema {
  connection_name: {
    required: boolean;
    min_length: number;
    max_length: number;
  };
  crm_type: {
    required: boolean;
    allowed_values: CRMType[];
  };
  credentials: {
    required: boolean;
    fields: Record<string, {
      required: boolean;
      type: 'string' | 'number' | 'boolean';
      validation?: RegExp;
    }>;
  };
}