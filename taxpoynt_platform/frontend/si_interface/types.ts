/**
 * System Integrator (SI) Interface Types
 * =====================================
 * 
 * Comprehensive type definitions for the SI Interface components.
 * Covers integration, compliance, processing, and Nigerian business requirements.
 */

// Base Types
export type Status = 'active' | 'inactive' | 'pending' | 'error' | 'testing';
export type Priority = 'high' | 'medium' | 'low';
export type ComplianceLevel = 'compliant' | 'non_compliant' | 'pending' | 'warning';

// Integration Types
export interface IntegrationConfig {
  id: string;
  name: string;
  type: SystemType;
  status: Status;
  credentials: Record<string, any>;
  endpoints: IntegrationEndpoint[];
  settings: IntegrationSettings;
  created_at: Date;
  updated_at: Date;
}

export interface SystemConnection {
  id: string;
  system_type: SystemType;
  connection_string: string;
  credentials: ConnectionCredentials;
  status: ConnectionStatus;
  last_tested: Date;
  test_results?: TestResult[];
}

export interface ConnectionStatus {
  connected: boolean;
  last_ping: Date;
  response_time: number;
  error_message?: string;
  health_score: number;
}

export interface IntegrationEndpoint {
  name: string;
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  auth_required: boolean;
}

export interface IntegrationSettings {
  sync_frequency: number;
  batch_size: number;
  retry_attempts: number;
  timeout: number;
  enable_webhooks: boolean;
  webhook_url?: string;
}

export interface ConnectionCredentials {
  api_key?: string;
  secret_key?: string;
  username?: string;
  password?: string;
  oauth_token?: string;
  certificate?: string;
  additional_params?: Record<string, any>;
}

export interface TestResult {
  test_name: string;
  passed: boolean;
  message: string;
  timestamp: Date;
  duration: number;
}

// Business System Types
export type SystemType = 
  | 'erp'
  | 'crm' 
  | 'pos'
  | 'ecommerce'
  | 'accounting'
  | 'inventory'
  | 'banking'
  | 'payment_processor'
  | 'other';

export interface ERPSystem {
  id: string;
  name: string;
  vendor: 'SAP' | 'Oracle' | 'Microsoft' | 'Odoo' | 'NetSuite' | 'Other';
  version: string;
  modules: string[];
  connection: SystemConnection;
  data_mappings: DataMapping[];
}

export interface CRMSystem {
  id: string;
  name: string;
  vendor: 'Salesforce' | 'HubSpot' | 'Microsoft Dynamics' | 'Zoho' | 'Other';
  version: string;
  features: string[];
  connection: SystemConnection;
  sync_settings: CRMSyncSettings;
}

export interface POSSystem {
  id: string;
  name: string;
  vendor: 'Square' | 'Shopify' | 'Nigerian POS' | 'Other';
  hardware_type: string;
  locations: POSLocation[];
  connection: SystemConnection;
}

export interface EcommerceSystem {
  id: string;
  name: string;
  platform: 'Shopify' | 'WooCommerce' | 'Magento' | 'Jumia' | 'Konga' | 'Other';
  store_url: string;
  connection: SystemConnection;
  product_sync: boolean;
  order_sync: boolean;
}

export interface AccountingSystem {
  id: string;
  name: string;
  software: 'QuickBooks' | 'Xero' | 'Sage' | 'MYOB' | 'Other';
  chart_of_accounts: ChartOfAccount[];
  connection: SystemConnection;
  tax_settings: TaxSettings;
}

export interface InventorySystem {
  id: string;
  name: string;
  type: 'Warehouse Management' | 'Stock Control' | 'Multi-location' | 'Other';
  locations: InventoryLocation[];
  connection: SystemConnection;
  sync_frequency: number;
}

// Processing Types
export interface ProcessingJob {
  id: string;
  type: ProcessingType;
  status: ProcessingStatus;
  created_at: Date;
  started_at?: Date;
  completed_at?: Date;
  progress: number;
  total_records: number;
  processed_records: number;
  failed_records: number;
  error_logs: ErrorLog[];
  metadata: Record<string, any>;
}

export type ProcessingType = 
  | 'data_extraction'
  | 'document_transformation'
  | 'validation'
  | 'firs_submission'
  | 'bulk_processing'
  | 'sync_operation';

export type ProcessingStatus = 
  | 'queued'
  | 'running'
  | 'paused'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface DocumentBatch {
  id: string;
  name: string;
  documents: ProcessingDocument[];
  status: ProcessingStatus;
  created_by: string;
  processing_rules: ProcessingRule[];
  output_format: 'FIRS_XML' | 'UBL' | 'JSON' | 'PDF';
}

export interface ProcessingDocument {
  id: string;
  filename: string;
  size: number;
  type: string;
  status: ProcessingStatus;
  validation_results?: ValidationResult[];
  transformation_results?: TransformationResult[];
}

export interface ProcessingRule {
  id: string;
  name: string;
  type: 'validation' | 'transformation' | 'enrichment';
  configuration: Record<string, any>;
  enabled: boolean;
}

export interface ValidationResult {
  rule_id: string;
  rule_name: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  field_path?: string;
  expected_value?: any;
  actual_value?: any;
  suggestion?: string;
}

export interface TransformationResult {
  source_field: string;
  target_field: string;
  transformation_type: string;
  success: boolean;
  original_value: any;
  transformed_value: any;
  error_message?: string;
}

export interface ErrorLog {
  timestamp: Date;
  level: 'error' | 'warning' | 'info';
  message: string;
  context?: Record<string, any>;
  stack_trace?: string;
}

// Compliance Types
export interface ComplianceStatus {
  overall_score: number;
  last_assessment: Date;
  compliance_areas: ComplianceArea[];
  action_items: ActionItem[];
  expiring_certificates: ExpiringCertificate[];
}

export interface ComplianceArea {
  name: string;
  regulation: string;
  status: ComplianceLevel;
  score: number;
  last_check: Date;
  requirements: ComplianceRequirement[];
}

export interface ComplianceRequirement {
  id: string;
  description: string;
  status: ComplianceLevel;
  evidence?: string;
  due_date?: Date;
}

export interface ActionItem {
  id: string;
  title: string;
  description: string;
  priority: Priority;
  due_date: Date;
  assigned_to?: string;
  status: 'open' | 'in_progress' | 'completed';
}

export interface ExpiringCertificate {
  name: string;
  expiry_date: Date;
  days_remaining: number;
  renewal_url?: string;
}

// Nigerian Compliance Types
export interface FIRSStatus {
  registration_status: 'registered' | 'pending' | 'expired';
  tin: string;
  certificate_status: CertificateStatus;
  last_submission: Date;
  submission_count: number;
  compliance_score: number;
  outstanding_issues: FIRSIssue[];
}

export interface VATCompliance {
  registration_number: string;
  status: ComplianceLevel;
  rate: number; // 7.5% for Nigeria
  last_filing: Date;
  next_filing: Date;
  outstanding_amount: number;
  exemptions: VATExemption[];
}

export interface CBNCompliance {
  compliance_areas: CBNComplianceArea[];
  forex_compliance: ForexCompliance;
  reporting_status: ReportingStatus;
  last_audit: Date;
}

export interface NDPRCompliance {
  data_protection_officer: string;
  privacy_policy_updated: Date;
  consent_management: ConsentStatus;
  data_breach_procedures: boolean;
  training_completed: boolean;
}

// Certificate Types
export interface Certificate {
  id: string;
  name: string;
  type: CertificateType;
  status: CertificateStatus;
  issuer: string;
  subject: string;
  valid_from: Date;
  valid_to: Date;
  serial_number: string;
  fingerprint: string;
  key_size: number;
  algorithm: string;
  usage: string[];
  file_path?: string;
}

export type CertificateType = 
  | 'FIRS_SIGNING'
  | 'SSL_TLS'
  | 'API_AUTH'
  | 'ENCRYPTION'
  | 'CODE_SIGNING';

export type CertificateStatus = 
  | 'valid'
  | 'expired'
  | 'revoked'
  | 'pending'
  | 'renewal_required';

export interface SecurityCredential {
  id: string;
  name: string;
  type: 'certificate' | 'api_key' | 'oauth_token' | 'password';
  status: Status;
  created_at: Date;
  expires_at?: Date;
  last_used?: Date;
  permissions: string[];
  metadata: Record<string, any>;
}

// Data Types
export interface DataMapping {
  id: string;
  name: string;
  source_system: string;
  target_schema: string;
  mappings: FieldMapping[];
  validation_rules: MappingValidationRule[];
  transformation_functions: TransformationFunction[];
}

export interface FieldMapping {
  source_field: string;
  target_field: string;
  data_type: DataType;
  required: boolean;
  default_value?: any;
  transformation?: string;
  validation_rules?: string[];
}

export type DataType = 
  | 'string'
  | 'number'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'email'
  | 'url'
  | 'currency'
  | 'percentage';

export interface DataExtraction {
  id: string;
  source: DataSource;
  extraction_type: ExtractionType;
  schedule: ExtractionSchedule;
  filters: DataFilter[];
  output_format: OutputFormat;
  last_extraction: Date;
  next_extraction: Date;
}

export interface DataSource {
  type: 'database' | 'api' | 'file' | 'webhook';
  connection_string: string;
  credentials: ConnectionCredentials;
  configuration: Record<string, any>;
}

export type ExtractionType = 'full' | 'incremental' | 'delta' | 'on_demand';

export interface ExtractionSchedule {
  frequency: 'real_time' | 'hourly' | 'daily' | 'weekly' | 'monthly';
  time?: string;
  timezone: string;
  enabled: boolean;
}

export interface DataFilter {
  field: string;
  operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'between';
  value: any;
}

export type OutputFormat = 'json' | 'xml' | 'csv' | 'excel' | 'pdf';

export interface SchemaDefinition {
  id: string;
  name: string;
  version: string;
  description: string;
  schema_type: 'FIRS' | 'UBL' | 'Custom';
  fields: SchemaField[];
  validation_rules: ValidationRule[];
  compliance_tags: string[];
}

export interface SchemaField {
  name: string;
  type: DataType;
  required: boolean;
  description: string;
  constraints?: FieldConstraints;
  examples?: any[];
}

export interface FieldConstraints {
  min_length?: number;
  max_length?: number;
  pattern?: string;
  min_value?: number;
  max_value?: number;
  allowed_values?: any[];
}

export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  rule_type: ValidationRuleType;
  severity: 'critical' | 'error' | 'warning' | 'info';
  field_path: string;
  condition: ValidationCondition;
  error_message: string;
  suggestion?: string;
}

export type ValidationRuleType = 
  | 'required'
  | 'format'
  | 'range'
  | 'pattern'
  | 'custom'
  | 'business_rule';

export interface ValidationCondition {
  operator: string;
  value?: any;
  custom_function?: string;
}

// Additional Supporting Types
export interface CRMSyncSettings {
  sync_contacts: boolean;
  sync_companies: boolean;
  sync_deals: boolean;
  sync_activities: boolean;
  sync_frequency: number;
  field_mappings: FieldMapping[];
}

export interface POSLocation {
  id: string;
  name: string;
  address: string;
  timezone: string;
  active: boolean;
}

export interface ChartOfAccount {
  account_code: string;
  account_name: string;
  account_type: string;
  balance: number;
  currency: string;
}

export interface TaxSettings {
  vat_rate: number;
  vat_registration: string;
  tax_year_end: string;
  currency: string;
}

export interface InventoryLocation {
  id: string;
  name: string;
  address: string;
  type: 'warehouse' | 'store' | 'office';
  active: boolean;
}

export interface MappingValidationRule {
  field: string;
  rule: string;
  message: string;
}

export interface TransformationFunction {
  name: string;
  input_fields: string[];
  output_field: string;
  function_code: string;
  description: string;
}

export interface FIRSIssue {
  issue_type: string;
  description: string;
  severity: Priority;
  due_date?: Date;
  resolution_steps: string[];
}

export interface VATExemption {
  item_category: string;
  exemption_reason: string;
  effective_date: Date;
  expiry_date?: Date;
}

export interface CBNComplianceArea {
  area: string;
  status: ComplianceLevel;
  last_check: Date;
  requirements: string[];
}

export interface ForexCompliance {
  license_status: Status;
  transaction_limits: Record<string, number>;
  reporting_requirements: string[];
  last_report: Date;
}

export interface ReportingStatus {
  monthly_returns: ComplianceLevel;
  quarterly_returns: ComplianceLevel;
  annual_returns: ComplianceLevel;
  ad_hoc_reports: ComplianceLevel;
}

export interface ConsentStatus {
  consent_mechanism: boolean;
  consent_records: number;
  withdrawal_mechanism: boolean;
  consent_audit_trail: boolean;
}

// Event Types for Real-time Updates
export interface SIEvent {
  id: string;
  type: SIEventType;
  timestamp: Date;
  source: string;
  data: Record<string, any>;
  user_id?: string;
}

export type SIEventType = 
  | 'integration_status_change'
  | 'processing_job_update'
  | 'compliance_alert'
  | 'certificate_expiry_warning'
  | 'system_health_update'
  | 'data_sync_completion';

// API Response Types
export interface APIResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  metadata?: {
    total_count?: number;
    page?: number;
    per_page?: number;
    has_more?: boolean;
  };
}

export interface PaginatedResponse<T> extends APIResponse<T[]> {
  metadata: {
    total_count: number;
    page: number;
    per_page: number;
    has_more: boolean;
    total_pages: number;
  };
}