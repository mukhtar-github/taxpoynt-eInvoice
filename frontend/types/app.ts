/**
 * Type definitions for APP functionality
 */

export type CertificateType = 'access_point' | 'authentication' | 'signing';
export type CertificateStatus = 'active' | 'expired' | 'revoked' | 'pending';
export type CertificateRequestType = 'new' | 'renewal' | 'replacement' | 'revocation';
export type CertificateRequestStatus = 'pending' | 'approved' | 'rejected' | 'issued' | 'canceled' | 'error';
export type CSIDStatus = 'active' | 'revoked' | 'expired';
export type TransmissionStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'retrying' | 'canceled';

export interface Certificate {
  id: string;
  organization_id: string;
  certificate_type: CertificateType;
  status: CertificateStatus;
  subject: string;
  issuer: string;
  valid_from: string;
  valid_to: string;
  serial_number: string;
  fingerprint: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface CertificateRequest {
  subject: ReactNode;
  requestDate: string | number | Date;
  id: string;
  organization_id: string;
  request_type: CertificateRequestType;
  status: CertificateRequestStatus;
  subject_info: {
    common_name: string;
    organization: string;
    organizational_unit?: string;
    country: string;
    state?: string;
    locality?: string;
    email?: string;
  };
  certificate_type: CertificateType;
  key_size: number;
  key_algorithm: string;
  created_at: string;
  updated_at: string;
  comment?: string;
  certificate_id?: string;
  metadata?: Record<string, any>;
}

export interface CSID {
  id: string;
  organization_id: string;
  certificate_id: string;
  csid_value: string;
  status: CSIDStatus;
  valid_from: string;
  valid_to: string;
  created_at: string;
  updated_at: string;
  revocation_reason?: string;
  revoked_at?: string;
  metadata?: Record<string, any>;
}

export interface TransmissionRecord {
  id: string;
  organization_id: string;
  certificate_id: string;
  csid_id?: string;
  submission_id?: string;
  status: TransmissionStatus;
  payload_hash: string;
  transmission_date?: string;
  response_code?: string;
  response_message?: string;
  retry_count: number;
  max_retries: number;
  next_retry?: string;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface TransmissionRetry {
  max_retries?: number;
  retry_delay?: number;
  force?: boolean;
}

export interface TransmissionBatchStatus {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
  retrying: number;
  canceled: number;
  success_rate: number;
}
