import axios from 'axios';
import { getAuthHeader } from './authService';

// Define handleApiError inline until errorHandlers.ts is recognized by TypeScript
const handleApiError = <T>(error: unknown, fallbackMessage: string = 'An error occurred'): T => {
  console.error('API Error:', error);
  
  // For Odoo integration, provide more specific error logging
  if (axios.isAxiosError(error) && error.config?.url?.includes('odoo')) {
    console.error('Odoo Integration Error:', error.message);
  }
  
  // Create a basic fallback object with timestamp
  const fallback = {
    timestamp: new Date().toISOString(),
    error: true,
    message: fallbackMessage
  };
  
  // Show an alert for critical errors
  if (fallbackMessage.includes('critical') || fallbackMessage.includes('failed')) {
    alert(`Error: ${fallbackMessage}`);
  }
  
  // Return the fallback as the expected type
  return fallback as unknown as T;
};

// Base API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Type definitions for submission metrics
export interface ErrorTypeModel {
  error_type: string;
  count: number;
  percentage: number;
  severity: string;
}

export interface StatusBreakdownModel {
  status: string;
  count: number;
  percentage: number;
}

export interface HourlySubmissionModel {
  hour: number;
  timestamp: string;
  total: number;
  success: number;
  failed: number;
  pending: number;
  success_rate: number;
}

export interface DailySubmissionModel {
  day: number;
  date: string;
  total: number;
  success: number;
  failed: number;
  pending: number;
  success_rate: number;
}

export interface SubmissionSummary {
  total_submissions: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  success_rate: number;
  avg_processing_time: number;
  common_errors: ErrorTypeModel[];
}

export interface SubmissionMetrics {
  timestamp: string;
  summary: SubmissionSummary;
  status_breakdown: StatusBreakdownModel[];
  hourly_submissions: HourlySubmissionModel[];
  daily_submissions: DailySubmissionModel[];
  common_errors: ErrorTypeModel[];
  time_range: string;
  odoo_metrics?: {
    total_odoo_submissions: number;
    percentage_of_all_submissions: number;
  };
}

export interface RetryMetricsModel {
  total_retries: number;
  success_count: number;
  failed_count: number;
  pending_count: number;
  success_rate: number;
  avg_attempts: number;
  max_attempts_reached_count: number;
}

export interface RetryMetrics {
  timestamp: string;
  metrics: RetryMetricsModel;
  retry_breakdown_by_status: StatusBreakdownModel[];
  retry_breakdown_by_severity: StatusBreakdownModel[];
  time_range: string;
}

/**
 * Fetch submission metrics from the API
 * 
 * @param timeRange Time range for metrics (24h, 7d, 30d, all)
 * @param organizationId Optional filter by organization
 * @param integrationType Optional filter by integration type
 * @param statusFilter Optional filter by submission status
 * @returns Promise with submission metrics
 */
export const fetchSubmissionMetrics = async (
  timeRange: string = '24h',
  organizationId?: string,
  integrationType?: string,
  statusFilter?: string
): Promise<SubmissionMetrics> => {
  try {
    // Build query parameters
    const params: Record<string, string> = { time_range: timeRange };
    if (organizationId) params.organization_id = organizationId;
    if (integrationType) params.integration_type = integrationType;
    if (statusFilter) params.status_filter = statusFilter;

    // Make API request
    const response = await axios.get(
      `${API_URL}/dashboard/submission/metrics`,
      {
        headers: await getAuthHeader(),
        params
      }
    );

    return response.data;
  } catch (error) {
    return handleApiError(error, 'Failed to fetch submission metrics');
  }
};

/**
 * Fetch retry metrics from the API
 * 
 * @param timeRange Time range for metrics (24h, 7d, 30d, all)
 * @param organizationId Optional filter by organization
 * @returns Promise with retry metrics
 */
export const fetchRetryMetrics = async (
  timeRange: string = '24h',
  organizationId?: string
): Promise<RetryMetrics> => {
  try {
    // Build query parameters
    const params: Record<string, string> = { time_range: timeRange };
    if (organizationId) params.organization_id = organizationId;

    // Make API request
    const response = await axios.get(
      `${API_URL}/dashboard/submission/retry-metrics`,
      {
        headers: await getAuthHeader(),
        params
      }
    );

    return response.data;
  } catch (error) {
    return handleApiError(error, 'Failed to fetch retry metrics');
  }
};

/**
 * Fetch Odoo-specific submission metrics from the API
 * 
 * @param timeRange Time range for metrics (24h, 7d, 30d, all)
 * @returns Promise with Odoo submission metrics
 */
export const fetchOdooSubmissionMetrics = async (
  timeRange: string = '24h'
): Promise<SubmissionMetrics> => {
  try {
    // Make API request
    const response = await axios.get(
      `${API_URL}/dashboard/submission/odoo-metrics`,
      {
        headers: await getAuthHeader(),
        params: { time_range: timeRange }
      }
    );

    return response.data;
  } catch (error) {
    return handleApiError(error, 'Failed to fetch Odoo submission metrics');
  }
};
