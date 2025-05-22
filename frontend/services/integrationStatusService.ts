import axios from 'axios';
import { getAuthHeader } from './authService';

// Base API URL
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Type definitions for integration status
export interface SubmissionStats {
  total_24h: number;
  success_24h: number;
  failed_24h: number;
  success_rate: number;
}

export interface OdooIntegrationStatus {
  id: string;
  name: string;
  status: 'operational' | 'degraded' | 'error' | 'not_configured';
  version?: string;
  last_submission?: string;
  submission_stats?: SubmissionStats;
  error?: string;
  last_successful_connection?: string;
}

export interface FirsApiStatus {
  status: 'operational' | 'degraded' | 'error' | 'unknown';
  sandbox_available: boolean;
  production_available: boolean;
  last_checked: string;
  submission_stats?: SubmissionStats;
  recent_errors?: Array<{
    id: string;
    timestamp: string;
    status: string;
    error_message: string;
  }>;
  error?: string;
}

export interface IntegrationStatusResponse {
  timestamp: string;
  system_status: 'operational' | 'degraded' | 'critical';
  odoo_integration: {
    status: 'operational' | 'degraded' | 'error' | 'not_configured';
    message: string;
    last_checked: string;
    integrations: OdooIntegrationStatus[];
  };
  firs_api: FirsApiStatus;
}

/**
 * Fetch Odoo integration status
 * 
 * @param integrationId Optional specific integration ID to check
 * @returns Promise with Odoo integration status
 */
export const fetchOdooStatus = async (integrationId?: string) => {
  try {
    // Build query parameters
    const params: Record<string, string> = {};
    if (integrationId) params.integration_id = integrationId;

    // Make API request
    const response = await axios.get(
      `${API_URL}/integration-status/odoo`,
      {
        headers: await getAuthHeader(),
        params
      }
    );

    return response.data;
  } catch (error) {
    console.error('Failed to fetch Odoo status:', error);
    return {
      status: 'error',
      message: 'Failed to fetch Odoo integration status',
      last_checked: new Date().toISOString(),
      integrations: []
    };
  }
};

/**
 * Fetch FIRS API status
 * 
 * @returns Promise with FIRS API status
 */
export const fetchFirsApiStatus = async () => {
  try {
    // Make API request
    const response = await axios.get(
      `${API_URL}/integration-status/firs`,
      {
        headers: await getAuthHeader()
      }
    );

    return response.data;
  } catch (error) {
    console.error('Failed to fetch FIRS API status:', error);
    return {
      status: 'error',
      error: 'Failed to fetch FIRS API status',
      last_checked: new Date().toISOString()
    };
  }
};

/**
 * Fetch status of all integrations
 * 
 * @returns Promise with status of all integrations
 */
export const fetchAllIntegrationStatus = async (): Promise<IntegrationStatusResponse> => {
  try {
    // Make API request
    const response = await axios.get(
      `${API_URL}/integration-status/all`,
      {
        headers: await getAuthHeader()
      }
    );

    return response.data;
  } catch (error) {
    console.error('Failed to fetch integration status:', error);
    return {
      timestamp: new Date().toISOString(),
      system_status: 'critical',
      odoo_integration: {
        status: 'error',
        message: 'Failed to fetch Odoo integration status',
        last_checked: new Date().toISOString(),
        integrations: []
      },
      firs_api: {
        status: 'error',
        error: 'Failed to fetch FIRS API status',
        sandbox_available: false,
        production_available: false,
        last_checked: new Date().toISOString()
      }
    };
  }
};
