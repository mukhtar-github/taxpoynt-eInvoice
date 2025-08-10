/**
 * Access Point Provider (APP) Interface Types
 * ==========================================
 * 
 * Type definitions for APP Interface components focused on FIRS transmission,
 * security management, and compliance monitoring for Access Point Providers.
 */

// Base Types
export type TransmissionStatus = 'pending' | 'transmitting' | 'transmitted' | 'acknowledged' | 'failed' | 'retrying';
export type FIRSStatus = 'connected' | 'disconnected' | 'error' | 'maintenance';
export type ValidationSeverity = 'critical' | 'error' | 'warning' | 'info';
export type SecurityLevel = 'high' | 'medium' | 'low';

// Transmission Types
export interface TransmissionJob {
  id: string;
  document_id: string;
  document_type: 'invoice' | 'credit_note' | 'debit_note';
  status: TransmissionStatus;
  priority: 'high' | 'normal' | 'low';
  created_at: Date;
  submitted_at?: Date;
  acknowledged_at?: Date;
  retry_count: number;
  max_retries: number;
  transmission_metadata: TransmissionMetadata;
  error_details?: ErrorDetails;
}

export interface TransmissionMetadata {
  batch_id?: string;
  source_system: string;
  taxpayer_tin: string;
  document_reference: string;
  submission_method: 'real_time' | 'batch';
  transmission_id?: string;
  firs_reference?: string;
}

export interface TransmissionStats {
  total_submissions: number;
  successful_transmissions: number;
  failed_transmissions: number;
  pending_transmissions: number;
  success_rate: number;
  average_response_time: number;
  daily_volume: DailyVolume[];
  status_breakdown: StatusBreakdown[];
}

export interface DailyVolume {
  date: string;
  count: number;
  success_count: number;
  failure_count: number;
}

export interface StatusBreakdown {
  status: TransmissionStatus;
  count: number;
  percentage: number;
}

// FIRS Communication Types
export interface FIRSConnection {
  id: string;
  name: string;
  environment: 'sandbox' | 'production';
  status: FIRSStatus;
  endpoint_url: string;
  certificate_id: string;
  last_ping: Date;
  response_time: number;
  uptime_percentage: number;
  api_version: string;
  rate_limit: RateLimit;
}

export interface RateLimit {
  requests_per_minute: number;
  current_usage: number;
  reset_time: Date;
}

export interface FIRSResponse {
  request_id: string;
  status_code: number;
  response_time: number;
  timestamp: Date;
  response_body?: any;
  error_message?: string;
  firs_tracking_id?: string;
}

export interface FIRSHealthCheck {
  connection_id: string;
  timestamp: Date;
  status: 'healthy' | 'degraded' | 'unhealthy';
  response_time: number;
  error_message?: string;
  service_availability: ServiceAvailability[];
}

export interface ServiceAvailability {
  service: string;
  status: 'available' | 'unavailable' | 'degraded';
  last_check: Date;
}

// Validation Types
export interface ValidationRule {
  id: string;
  name: string;
  description: string;
  category: 'format' | 'business' | 'compliance' | 'security';
  severity: ValidationSeverity;
  active: boolean;
  rule_logic: string;
  error_message: string;
  suggestion?: string;
}

export interface ValidationResult {
  rule_id: string;
  rule_name: string;
  status: 'passed' | 'failed' | 'skipped';
  severity: ValidationSeverity;
  message: string;
  field_path?: string;
  expected_value?: any;
  actual_value?: any;
  suggestion?: string;
  documentation_link?: string;
}

export interface ValidationSession {
  id: string;
  document_id: string;
  document_type: string;
  timestamp: Date;
  status: 'running' | 'completed' | 'failed';
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
  warnings: number;
  overall_score: number;
  results: ValidationResult[];
  duration: number;
}

export interface ValidationConfig {
  id: string;
  name: string;
  description: string;
  document_types: string[];
  rules: string[];
  validation_level: 'strict' | 'standard' | 'permissive';
  auto_fix_enabled: boolean;
  stop_on_critical: boolean;
}

// Security Types
export interface Certificate {
  id: string;
  name: string;
  type: 'firs_signing' | 'ssl_tls' | 'client_auth';
  status: 'valid' | 'expired' | 'expiring_soon' | 'revoked';
  issuer: string;
  subject: string;
  serial_number: string;
  valid_from: Date;
  valid_to: Date;
  fingerprint: string;
  key_usage: string[];
  certificate_chain: string[];
  file_path?: string;
}

export interface SecurityAudit {
  id: string;
  timestamp: Date;
  audit_type: 'certificate' | 'access' | 'transmission' | 'configuration';
  severity: SecurityLevel;
  title: string;
  description: string;
  affected_resources: string[];
  recommendations: string[];
  status: 'open' | 'in_progress' | 'resolved' | 'acknowledged';
  assigned_to?: string;
}

export interface SecurityMetrics {
  certificate_status: CertificateStatusSummary;
  access_attempts: AccessAttemptsSummary;
  transmission_security: TransmissionSecuritySummary;
  vulnerability_summary: VulnerabilitySummary;
  compliance_score: number;
}

export interface CertificateStatusSummary {
  total: number;
  valid: number;
  expiring_soon: number;
  expired: number;
  revoked: number;
}

export interface AccessAttemptsSummary {
  total_attempts: number;
  successful_attempts: number;
  failed_attempts: number;
  blocked_attempts: number;
  suspicious_activities: number;
}

export interface TransmissionSecuritySummary {
  encrypted_transmissions: number;
  total_transmissions: number;
  encryption_rate: number;
  security_violations: number;
}

export interface VulnerabilitySummary {
  critical: number;
  high: number;
  medium: number;
  low: number;
  total: number;
}

// Status Tracking Types
export interface DocumentStatus {
  document_id: string;
  current_status: TransmissionStatus;
  status_history: StatusHistoryEntry[];
  milestones: Milestone[];
  estimated_completion?: Date;
  sla_status: 'on_track' | 'at_risk' | 'breached';
}

export interface StatusHistoryEntry {
  status: TransmissionStatus;
  timestamp: Date;
  duration?: number;
  notes?: string;
  user_id?: string;
  system_generated: boolean;
}

export interface Milestone {
  id: string;
  name: string;
  description: string;
  target_time: number; // minutes from submission
  actual_time?: number;
  status: 'pending' | 'completed' | 'overdue';
  critical: boolean;
}

export interface StatusAlert {
  id: string;
  type: 'sla_breach' | 'high_error_rate' | 'system_failure' | 'performance_degradation';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description: string;
  timestamp: Date;
  affected_documents: string[];
  resolution_steps: string[];
  status: 'active' | 'acknowledged' | 'resolved';
}

// Compliance & Reporting Types
export interface ComplianceReport {
  id: string;
  report_type: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'annual';
  period_start: Date;
  period_end: Date;
  generated_at: Date;
  status: 'generating' | 'completed' | 'failed';
  metrics: ComplianceMetrics;
  violations: ComplianceViolation[];
  recommendations: string[];
  file_path?: string;
}

export interface ComplianceMetrics {
  total_submissions: number;
  successful_submissions: number;
  compliance_rate: number;
  average_processing_time: number;
  sla_compliance: number;
  security_score: number;
  data_quality_score: number;
}

export interface ComplianceViolation {
  id: string;
  type: string;
  severity: ValidationSeverity;
  description: string;
  occurrence_count: number;
  first_occurrence: Date;
  last_occurrence: Date;
  affected_documents: string[];
  resolution_status: 'open' | 'resolved' | 'acknowledged';
}

// Error Handling Types
export interface ErrorDetails {
  error_code: string;
  error_message: string;
  error_category: 'network' | 'validation' | 'security' | 'business' | 'system';
  stack_trace?: string;
  context: Record<string, any>;
  resolution_suggestions: string[];
  documentation_links: string[];
}

export interface RetryConfiguration {
  max_retries: number;
  retry_delay: number; // seconds
  backoff_strategy: 'linear' | 'exponential' | 'fixed';
  retry_conditions: string[];
}

// Configuration Types
export interface APPConfiguration {
  transmission: TransmissionConfig;
  validation: ValidationConfig;
  security: SecurityConfig;
  monitoring: MonitoringConfig;
  firs_connection: FIRSConnectionConfig;
}

export interface TransmissionConfig {
  batch_size: number;
  retry_configuration: RetryConfiguration;
  transmission_timeout: number;
  queue_configuration: QueueConfig;
}

export interface QueueConfig {
  high_priority_limit: number;
  normal_priority_limit: number;
  low_priority_limit: number;
  processing_threads: number;
}

export interface SecurityConfig {
  certificate_auto_renewal: boolean;
  security_scanning_enabled: boolean;
  audit_log_retention_days: number;
  access_control_strict_mode: boolean;
}

export interface MonitoringConfig {
  health_check_interval: number;
  metrics_collection_interval: number;
  alert_thresholds: AlertThresholds;
  retention_policies: RetentionPolicies;
}

export interface AlertThresholds {
  error_rate_threshold: number;
  response_time_threshold: number;
  queue_size_threshold: number;
  certificate_expiry_warning_days: number;
}

export interface RetentionPolicies {
  transmission_logs_days: number;
  audit_logs_days: number;
  metrics_data_days: number;
  error_logs_days: number;
}

export interface FIRSConnectionConfig {
  primary_endpoint: string;
  backup_endpoint?: string;
  timeout_seconds: number;
  ssl_verification: boolean;
  api_version: string;
  rate_limiting: RateLimitConfig;
}

export interface RateLimitConfig {
  requests_per_minute: number;
  burst_limit: number;
  retry_after_seconds: number;
}

// API Response Types
export interface APPApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  metadata?: {
    total_count?: number;
    page?: number;
    per_page?: number;
    processing_time_ms?: number;
  };
}

// Real-time Event Types
export interface APPEvent {
  id: string;
  type: APPEventType;
  timestamp: Date;
  source: 'transmission' | 'validation' | 'security' | 'firs' | 'system';
  data: Record<string, any>;
  priority: 'high' | 'normal' | 'low';
}

export type APPEventType = 
  | 'transmission_started'
  | 'transmission_completed'
  | 'transmission_failed'
  | 'validation_completed'
  | 'certificate_expiring'
  | 'security_violation'
  | 'firs_connection_lost'
  | 'firs_connection_restored'
  | 'system_health_degraded'
  | 'compliance_violation';

// Dashboard Widget Types
export interface DashboardWidget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'status' | 'alert';
  title: string;
  size: 'small' | 'medium' | 'large' | 'full';
  position: { x: number; y: number };
  config: Record<string, any>;
  data_source: string;
  refresh_interval: number;
  visible: boolean;
}

export interface DashboardLayout {
  id: string;
  name: string;
  description: string;
  widgets: DashboardWidget[];
  shared: boolean;
  created_by: string;
  created_at: Date;
  updated_at: Date;
}