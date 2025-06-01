/**
 * Types for secure transmission functionality
 */

export interface TransmissionRecord {
  id: string;
  status: string;
  organization_id: string;
  transmission_time: string;
  destination: string;
  retry_count: number;
  last_retry_time?: string;
  destination_endpoint?: string;
  certificate_id?: string;
  submission_id?: string;
}

export interface TransmissionStatus {
  transmission_id: string;
  status: string;
  last_updated: string;
  retry_count?: number;
  retry_history?: Array<{
    attempt: number;
    timestamp: string;
    status: string;
    error?: string;
  }>;
  verification_status?: string;
  firs_status?: any;
  error?: string;
}

export interface TransmissionReceipt {
  receipt_id: string;
  transmission_id: string;
  timestamp: string;
  verification_status: string;
  receipt_data: any;
}

export interface TransmissionRequest {
  payload: any;
  organization_id: string;
  certificate_id?: string;
  submission_id?: string;
  metadata?: Record<string, any>;
}

export interface TransmissionResponse {
  transmission_id: string;
  status: string;
  message: string;
  details?: Record<string, any>;
}

export interface TransmissionRetryRequest {
  max_retries?: number;
  force?: boolean;
  immediate?: boolean;
  notes?: string;
}

export type TransmissionStatusType = 'pending' | 'in_progress' | 'completed' | 'failed' | 'retrying' | 'canceled';
