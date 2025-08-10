/**
 * Hybrid Interface Types
 * ======================
 * 
 * Type definitions for the Hybrid Interface that combines both
 * System Integrator (SI) and Access Point Provider (APP) capabilities.
 * 
 * Features:
 * - Unified dashboard metrics
 * - Cross-role analytics and reporting
 * - Workflow orchestration across SI and APP functions
 * - Comprehensive compliance management
 * - End-to-end process monitoring
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Import existing types from SI and APP interfaces
import type { 
  SystemType, 
  IntegrationConfig, 
  ComplianceLevel,
  ProcessingJob,
  DataMapping 
} from '../si_interface/types';

import type { 
  TransmissionStatus, 
  TransmissionJob, 
  FIRSConnection,
  SecurityAudit,
  ComplianceReport 
} from '../app_interface/types';

// Hybrid Base Types
export type HybridRole = 'si_user' | 'app_user' | 'hybrid_user' | 'platform_admin';
export type ProcessStage = 'data_extraction' | 'validation' | 'transformation' | 'transmission' | 'acknowledgment' | 'completed' | 'failed';
export type WorkflowStatus = 'draft' | 'active' | 'paused' | 'completed' | 'failed' | 'archived';
export type AnalyticsGranularity = 'hourly' | 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';

// Unified Dashboard Types
export interface UnifiedDashboardMetrics {
  si_metrics: SIMetricsSummary;
  app_metrics: APPMetricsSummary;
  hybrid_metrics: HybridMetricsSummary;
  cross_role_metrics: CrossRoleMetrics;
  timestamp: Date;
}

export interface SIMetricsSummary {
  total_integrations: number;
  active_connections: number;
  failed_connections: number;
  documents_processed_today: number;
  processing_success_rate: number;
  average_processing_time: number;
  compliance_score: number;
}

export interface APPMetricsSummary {
  total_transmissions: number;
  successful_transmissions: number;
  failed_transmissions: number;
  pending_transmissions: number;
  firs_connection_status: 'connected' | 'disconnected' | 'error';
  transmission_success_rate: number;
  average_response_time: number;
  security_score: number;
}

export interface HybridMetricsSummary {
  end_to_end_completion_rate: number;
  cross_role_workflow_count: number;
  unified_compliance_score: number;
  total_documents_in_pipeline: number;
  average_end_to_end_time: number;
  bottleneck_stage?: ProcessStage;
}

export interface CrossRoleMetrics {
  si_to_app_handoffs: number;
  successful_handoffs: number;
  failed_handoffs: number;
  handoff_success_rate: number;
  integration_to_transmission_time: number;
  workflow_orchestration_efficiency: number;
}

// Workflow Orchestration Types
export interface CrossRoleWorkflow {
  id: string;
  name: string;
  description: string;
  type: WorkflowType;
  status: WorkflowStatus;
  stages: WorkflowStage[];
  triggers: WorkflowTrigger[];
  current_stage?: string;
  created_by: string;
  created_at: Date;
  updated_at: Date;
  execution_history: WorkflowExecution[];
}

export type WorkflowType = 
  | 'end_to_end_invoice' 
  | 'compliance_check' 
  | 'data_sync' 
  | 'error_resolution'
  | 'batch_processing'
  | 'emergency_response';

export interface WorkflowStage {
  id: string;
  name: string;
  description: string;
  stage_type: ProcessStage;
  role_responsible: 'si' | 'app' | 'hybrid' | 'system';
  required_permissions: string[];
  estimated_duration: number; // minutes
  dependencies: string[]; // stage IDs
  actions: WorkflowAction[];
  validation_rules: string[];
  error_handling: ErrorHandlingRule[];
}

export interface WorkflowAction {
  id: string;
  name: string;
  type: 'api_call' | 'data_transform' | 'validation' | 'notification' | 'manual_review';
  config: Record<string, any>;
  required: boolean;
  timeout: number;
  retry_config?: RetryConfig;
}

export interface WorkflowTrigger {
  id: string;
  name: string;
  type: 'schedule' | 'event' | 'manual' | 'condition';
  config: TriggerConfig;
  enabled: boolean;
}

export interface TriggerConfig {
  schedule?: string; // cron format
  event_type?: string;
  condition?: string; // expression
  manual_trigger_roles?: HybridRole[];
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: 'running' | 'completed' | 'failed' | 'paused' | 'cancelled';
  started_at: Date;
  completed_at?: Date;
  triggered_by: string;
  stage_executions: StageExecution[];
  total_duration?: number;
  error_message?: string;
  metrics: ExecutionMetrics;
}

export interface StageExecution {
  stage_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  started_at?: Date;
  completed_at?: Date;
  duration?: number;
  output_data?: Record<string, any>;
  error_message?: string;
  retry_count: number;
}

export interface ExecutionMetrics {
  total_documents_processed: number;
  successful_documents: number;
  failed_documents: number;
  data_volume: number; // bytes
  api_calls_made: number;
  cache_hits: number;
  performance_score: number;
}

export interface ErrorHandlingRule {
  error_type: string;
  action: 'retry' | 'skip' | 'pause' | 'escalate' | 'rollback';
  max_retries?: number;
  escalation_roles?: HybridRole[];
  notification_config?: NotificationConfig;
}

export interface RetryConfig {
  max_attempts: number;
  delay_seconds: number;
  backoff_multiplier: number;
  max_delay_seconds: number;
}

export interface NotificationConfig {
  channels: ('email' | 'sms' | 'webhook' | 'dashboard')[];
  recipients: string[];
  template: string;
  urgent: boolean;
}

// Cross-Role Analytics Types
export interface CrossRoleAnalytics {
  id: string;
  report_name: string;
  report_type: AnalyticsReportType;
  granularity: AnalyticsGranularity;
  date_range: DateRange;
  data_sources: DataSource[];
  metrics: AnalyticsMetric[];
  visualizations: VisualizationConfig[];
  generated_at: Date;
  generated_by: string;
}

export type AnalyticsReportType = 
  | 'performance_overview'
  | 'compliance_summary'
  | 'integration_health'
  | 'transmission_analysis'
  | 'workflow_efficiency'
  | 'security_audit'
  | 'business_insights'
  | 'trend_analysis';

export interface DateRange {
  start_date: Date;
  end_date: Date;
  timezone: string;
}

export interface DataSource {
  source_id: string;
  source_type: 'si_interface' | 'app_interface' | 'hybrid_workflows' | 'external_api';
  connection_config: Record<string, any>;
  data_filters?: Record<string, any>;
  refresh_rate: number; // minutes
}

export interface AnalyticsMetric {
  metric_id: string;
  name: string;
  description: string;
  data_type: 'number' | 'percentage' | 'currency' | 'duration' | 'count';
  calculation_method: string;
  target_value?: number;
  warning_threshold?: number;
  critical_threshold?: number;
  trend_direction?: 'up' | 'down' | 'stable';
}

export interface VisualizationConfig {
  chart_id: string;
  chart_type: 'line' | 'bar' | 'pie' | 'area' | 'gauge' | 'table' | 'heatmap';
  title: string;
  metrics: string[]; // metric IDs
  dimensions: string[];
  filters: Record<string, any>;
  display_options: ChartDisplayOptions;
}

export interface ChartDisplayOptions {
  width?: number;
  height?: number;
  color_scheme?: string[];
  show_legend?: boolean;
  show_grid?: boolean;
  animation_enabled?: boolean;
  interactive?: boolean;
  export_options?: ('png' | 'pdf' | 'csv' | 'excel')[];
}

// Unified Compliance Types
export interface UnifiedComplianceStatus {
  overall_score: number;
  compliance_categories: ComplianceCategory[];
  recent_violations: ComplianceViolation[];
  upcoming_deadlines: ComplianceDeadline[];
  compliance_trends: ComplianceTrend[];
  recommendations: ComplianceRecommendation[];
}

export interface ComplianceCategory {
  category_id: string;
  name: string;
  description: string;
  score: number;
  weight: number; // percentage of overall score
  status: ComplianceLevel;
  last_assessed: Date;
  requirements: ComplianceRequirement[];
}

export interface ComplianceRequirement {
  requirement_id: string;
  name: string;
  description: string;
  regulatory_body: 'FIRS' | 'CBN' | 'NITDA' | 'NAICOM' | 'SEC' | 'CAC';
  compliance_status: ComplianceLevel;
  evidence_required: string[];
  evidence_provided: EvidenceDocument[];
  due_date?: Date;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
}

export interface ComplianceViolation {
  violation_id: string;
  requirement_id: string;
  severity: 'minor' | 'major' | 'critical';
  description: string;
  detected_at: Date;
  status: 'open' | 'investigating' | 'resolved' | 'accepted';
  resolution_steps: string[];
  assigned_to?: string;
  resolved_at?: Date;
}

export interface ComplianceDeadline {
  deadline_id: string;
  requirement_id: string;
  title: string;
  due_date: Date;
  priority: 'low' | 'medium' | 'high' | 'critical';
  progress_percentage: number;
  assigned_roles: HybridRole[];
  estimated_hours: number;
}

export interface ComplianceTrend {
  period: string;
  score: number;
  improvement: number; // percentage change
  key_factors: string[];
}

export interface ComplianceRecommendation {
  recommendation_id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  estimated_impact: number; // score improvement
  estimated_effort: number; // hours
  recommended_actions: string[];
  deadline?: Date;
}

export interface EvidenceDocument {
  document_id: string;
  name: string;
  type: string;
  upload_date: Date;
  uploaded_by: string;
  file_path: string;
  verified: boolean;
  verified_by?: string;
  verified_at?: Date;
}

// End-to-End Process Types
export interface EndToEndProcess {
  process_id: string;
  name: string;
  description: string;
  document_reference: string;
  customer_reference?: string;
  current_stage: ProcessStage;
  status: 'active' | 'completed' | 'failed' | 'on_hold';
  progress_percentage: number;
  started_at: Date;
  estimated_completion: Date;
  actual_completion?: Date;
  sla_status: 'on_track' | 'at_risk' | 'breached';
  
  // SI Stage Information
  si_integration_id?: string;
  data_extraction_status?: 'pending' | 'in_progress' | 'completed' | 'failed';
  validation_results?: ValidationSummary;
  
  // APP Stage Information
  app_transmission_id?: string;
  transmission_status?: TransmissionStatus;
  firs_reference?: string;
  
  // Performance Metrics
  stage_durations: Record<ProcessStage, number>; // minutes
  total_duration?: number;
  bottlenecks: ProcessBottleneck[];
  efficiency_score: number;
}

export interface ValidationSummary {
  total_rules_checked: number;
  rules_passed: number;
  rules_failed: number;
  warnings: number;
  critical_errors: number;
  overall_score: number;
}

export interface ProcessBottleneck {
  stage: ProcessStage;
  expected_duration: number;
  actual_duration: number;
  delay_percentage: number;
  root_causes: string[];
  recommended_actions: string[];
}

// Troubleshooting Types
export interface TroubleshootingCase {
  case_id: string;
  title: string;
  description: string;
  category: TroubleshootingCategory;
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  affected_processes: string[];
  affected_systems: SystemType[];
  symptoms: string[];
  diagnosis: DiagnosisResult[];
  resolution_steps: ResolutionStep[];
  created_by: string;
  assigned_to?: string;
  created_at: Date;
  resolved_at?: Date;
  resolution_time?: number; // minutes
}

export type TroubleshootingCategory = 
  | 'integration_failure'
  | 'transmission_error' 
  | 'validation_issues'
  | 'security_incident'
  | 'performance_degradation'
  | 'compliance_violation'
  | 'system_outage';

export interface DiagnosisResult {
  test_name: string;
  test_type: 'connectivity' | 'authentication' | 'data_integrity' | 'performance' | 'compliance';
  result: 'passed' | 'failed' | 'warning';
  details: string;
  recommendations?: string[];
  evidence?: string[];
}

export interface ResolutionStep {
  step_number: number;
  description: string;
  responsible_role: HybridRole;
  estimated_time: number; // minutes
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  started_at?: Date;
  completed_at?: Date;
  notes?: string;
}

// Role Switching and Permissions
export interface HybridUserSession {
  user_id: string;
  session_id: string;
  active_role: HybridRole;
  available_roles: HybridRole[];
  permissions: string[];
  role_switched_at?: Date;
  session_started: Date;
  last_activity: Date;
  context: SessionContext;
}

export interface SessionContext {
  current_interface: 'si' | 'app' | 'hybrid';
  active_workspaces: string[];
  recent_activities: RecentActivity[];
  preferences: UserPreferences;
}

export interface RecentActivity {
  activity_id: string;
  type: string;
  description: string;
  timestamp: Date;
  interface: 'si' | 'app' | 'hybrid';
  resource_id?: string;
}

export interface UserPreferences {
  default_interface: 'si' | 'app' | 'hybrid';
  dashboard_layout: 'unified' | 'tabbed' | 'side_by_side';
  notification_settings: NotificationPreferences;
  theme: 'light' | 'dark' | 'auto';
  timezone: string;
  language: string;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  browser_notifications: boolean;
  sms_notifications: boolean;
  notification_types: string[];
  quiet_hours?: {
    start_time: string;
    end_time: string;
    timezone: string;
  };
}

// API Response Types for Hybrid Interface
export interface HybridApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  errors?: string[];
  metadata?: {
    source_interfaces?: ('si' | 'app' | 'hybrid')[];
    aggregation_time_ms?: number;
    cache_status?: 'hit' | 'miss' | 'partial';
    data_freshness?: Date;
    total_count?: number;
    page?: number;
    per_page?: number;
  };
}

// Real-time Event Types for Hybrid Interface
export interface HybridEvent {
  event_id: string;
  type: HybridEventType;
  timestamp: Date;
  source: 'si_interface' | 'app_interface' | 'hybrid_orchestrator' | 'external_system';
  data: Record<string, any>;
  priority: 'low' | 'medium' | 'high' | 'critical';
  target_roles: HybridRole[];
  correlation_id?: string; // for tracking related events
}

export type HybridEventType = 
  | 'workflow_stage_completed'
  | 'cross_role_handoff'
  | 'end_to_end_process_completed'
  | 'compliance_violation_detected'
  | 'system_integration_restored'
  | 'performance_threshold_exceeded'
  | 'security_incident_detected'
  | 'data_synchronization_completed'
  | 'user_role_switched'
  | 'troubleshooting_case_created';

// Export utility types for component props
export interface BaseComponentProps {
  className?: string;
  style?: React.CSSProperties;
  loading?: boolean;
  error?: string | null;
  onError?: (error: Error) => void;
  testId?: string;
}

export interface DashboardComponentProps extends BaseComponentProps {
  refreshInterval?: number;
  autoRefresh?: boolean;
  onRefresh?: () => void;
  dateRange?: DateRange;
  filters?: Record<string, any>;
}

export interface WorkflowComponentProps extends BaseComponentProps {
  workflowId?: string;
  executionId?: string;
  readOnly?: boolean;
  onWorkflowChange?: (workflow: CrossRoleWorkflow) => void;
  onExecutionUpdate?: (execution: WorkflowExecution) => void;
}

export interface AnalyticsComponentProps extends BaseComponentProps {
  reportType?: AnalyticsReportType;
  granularity?: AnalyticsGranularity;
  dateRange?: DateRange;
  dataSourceFilters?: Record<string, any>;
  onReportGenerated?: (report: CrossRoleAnalytics) => void;
}

// Type guards and utility functions
export const isHybridUser = (role: string): role is HybridRole => {
  return ['si_user', 'app_user', 'hybrid_user', 'platform_admin'].includes(role);
};

export const canAccessInterface = (userRole: HybridRole, interfaceType: 'si' | 'app' | 'hybrid'): boolean => {
  const accessMatrix: Record<HybridRole, ('si' | 'app' | 'hybrid')[]> = {
    'si_user': ['si'],
    'app_user': ['app'],
    'hybrid_user': ['si', 'app', 'hybrid'],
    'platform_admin': ['si', 'app', 'hybrid']
  };
  
  return accessMatrix[userRole]?.includes(interfaceType) ?? false;
};