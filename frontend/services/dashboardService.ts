import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const API_V1 = `${API_URL}/api/v1`;

export interface Integration {
  id: string;
  name: string;
  client: string;
  status: 'active' | 'configured' | 'error';
  lastSynced: string | null;
}

export interface TransactionMetrics {
  today: number;
  week: number;
  month: number;
  success: number;
}

// Dashboard metrics types based on backend schema
export interface TimeRange {
  value: '24h' | '7d' | '30d' | 'all';
  label: string;
}

export interface CommonError {
  error_code: string;
  count: number;
  percentage: number;
}

export interface HourlyGeneration {
  hour: number;
  timestamp: string;
  count: number;
}

export interface DailyGeneration {
  day: number;
  date: string;
  count: number;
}

export interface HourlyValidation {
  hour: number;
  timestamp: string;
  total: number;
  success: number;
  failure: number;
  success_rate: number;
}

export interface DailyB2BvsB2C {
  day: number;
  date: string;
  b2b_count: number;
  b2c_count: number;
  total: number;
}

export interface IntegrationStatus {
  integration_id: string;
  name: string;
  organization_id: string;
  is_active: boolean;
  created_at: string;
  last_validated: string | null;
  last_validation_success: boolean | null;
}

export interface HourlyCount {
  hour: number;
  timestamp: string;
  count: number;
}

export interface HourlyRequest {
  hour: number;
  timestamp: string;
  requests: number;
  errors: number;
  error_rate: number;
}

export interface EndpointPopularity {
  endpoint: string;
  count: number;
  percentage: number;
}

export interface IRNMetrics {
  total_count: number;
  status_counts: {
    unused: number;
    active: number;
    used: number;
    expired: number;
    cancelled: number;
  };
  hourly_generation: HourlyGeneration[];
  daily_generation: DailyGeneration[];
  time_range: string;
}

export interface ValidationMetrics {
  total_count: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  common_errors: CommonError[];
  hourly_validation: HourlyValidation[];
  time_range: string;
}

export interface B2BvsB2CMetrics {
  total_count: number;
  b2b_count: number;
  b2c_count: number;
  b2b_percentage: number;
  b2c_percentage: number;
  b2b_success_rate: number;
  b2c_success_rate: number;
  daily_breakdown: DailyB2BvsB2C[];
  time_range: string;
}

export interface OdooIntegrationMetrics {
  total_integrations: number;
  active_integrations: number;
  inactive_integrations: number;
  total_invoices: number;
  successful_invoices: number;
  success_rate: number;
  integration_statuses: IntegrationStatus[];
  hourly_counts: HourlyCount[];
  time_range: string;
}

export interface SystemHealthMetrics {
  total_requests: number;
  error_requests: number;
  error_rate: number;
  avg_response_time: number;
  hourly_requests: HourlyRequest[];
  endpoint_popularity: EndpointPopularity[];
  time_range: string;
}

export interface DashboardSummary {
  timestamp: string;
  irn_summary: {
    total_irns: number;
    active_irns: number;
    unused_irns: number;
    expired_irns: number;
  };
  validation_summary: {
    total_validations: number;
    success_rate: number;
    common_errors: CommonError[];
  };
  b2b_vs_b2c_summary: {
    b2b_percentage: number;
    b2c_percentage: number;
    b2b_success_rate: number;
    b2c_success_rate: number;
    b2b_count: number;
    b2c_count: number;
    daily_breakdown?: any[];
  };
  odoo_summary: {
    active_integrations: number;
    total_invoices: number;
    success_rate: number;
  };
  system_summary: {
    total_requests: number;
    error_rate: number;
    avg_response_time: number;
  };
}

export interface Transaction {
  id: string;
  type: 'irn_generation' | 'validation' | 'submission';
  status: 'success' | 'failed' | 'pending';
  integration: string;
  timestamp: string;
}

export interface DashboardData {
  integrations: Integration[];
  metrics: TransactionMetrics;
  recentTransactions: Transaction[];
}

/**
 * Fetch dashboard data including integrations, metrics, and recent transactions
 */
export const fetchDashboardData = async (): Promise<DashboardData> => {
  try {
    const response = await axios.get(`${API_V1}/dashboard/summary`);
    return {
      integrations: response.data.odoo_summary ? [
        { 
          id: '1', 
          name: 'Odoo Integration', 
          client: 'FIRS e-Invoice', 
          status: response.data.odoo_summary.active_integrations > 0 ? 'active' : 'error',
          lastSynced: response.data.timestamp
        },
      ] : [],
      metrics: {
        today: response.data.irn_summary?.total_irns || 0,
        week: response.data.validation_summary?.total_validations || 0,
        month: response.data.system_summary?.total_requests || 0,
        success: response.data.validation_summary?.success_rate || 0
      },
      recentTransactions: []
    };
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    
    // Return mock data for POC phase
    return {
      integrations: [
        { id: '1', name: 'ERP Integration', client: 'ABC Corp', status: 'active', lastSynced: '2025-04-26T06:30:00Z' },
        { id: '2', name: 'Accounting System', client: 'XYZ Ltd', status: 'configured', lastSynced: null },
        { id: '3', name: 'POS Integration', client: 'Retail Co', status: 'error', lastSynced: '2025-04-25T14:22:00Z' },
      ],
      metrics: {
        today: 124,
        week: 738,
        month: 2945,
        success: 95.8
      },
      recentTransactions: [
        { id: '1', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:45:12Z' },
        { id: '2', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:44:23Z' },
        { id: '3', type: 'submission', status: 'failed', integration: 'POS Integration', timestamp: '2025-04-26T06:22:58Z' },
        { id: '4', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:18:42Z' },
        { id: '5', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:15:19Z' },
      ]
    };
  }
};

/**
 * Fetch integration status data
 */
export const fetchIntegrationStatus = async (): Promise<Integration[]> => {
  try {
    const response = await axios.get(`${API_URL}/integrations`);
    return response.data;
  } catch (error) {
    console.error('Error fetching integration status:', error);
    
    // Return mock data for POC phase
    return [
      { id: '1', name: 'ERP Integration', client: 'ABC Corp', status: 'active', lastSynced: '2025-04-26T06:30:00Z' },
      { id: '2', name: 'Accounting System', client: 'XYZ Ltd', status: 'configured', lastSynced: null },
      { id: '3', name: 'POS Integration', client: 'Retail Co', status: 'error', lastSynced: '2025-04-25T14:22:00Z' },
    ];
  }
};

/**
 * Fetch transaction metrics data
 */
export const fetchTransactionMetrics = async (): Promise<TransactionMetrics> => {
  try {
    const response = await axios.get(`${API_URL}/dashboard/transactions`);
    return response.data;
  } catch (error) {
    console.error('Error fetching transaction metrics:', error);
    
    // Return mock data for POC phase
    return {
      today: 124,
      week: 738,
      month: 2945,
      success: 95.8
    };
  }
};

/**
 * Fetch recent transactions
 */
export const fetchRecentTransactions = async (limit: number = 5): Promise<Transaction[]> => {
  try {
    const response = await axios.get(`${API_URL}/dashboard/transactions/recent?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recent transactions:', error);
    
    // Return mock data for POC phase
    return [
      { id: '1', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:45:12Z' },
      { id: '2', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:44:23Z' },
      { id: '3', type: 'submission', status: 'failed', integration: 'POS Integration', timestamp: '2025-04-26T06:22:58Z' },
      { id: '4', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:18:42Z' },
      { id: '5', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:15:19Z' },
    ];
  }
}; 

/**
 * Fetch dashboard summary data with a consolidated view of all metrics
 */
export const fetchDashboardSummary = async (timeRange: string = '24h', organizationId?: string): Promise<DashboardSummary> => {
  try {
    let url = `${API_V1}/dashboard/summary?time_range=${timeRange}`;
    if (organizationId) {
      url += `&organization_id=${organizationId}`;
    }
    
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard summary:', error);
    
    // Return mock data for development and testing
    return {
      timestamp: new Date().toISOString(),
      irn_summary: {
        total_irns: 1245,
        active_irns: 956,
        unused_irns: 178,
        expired_irns: 111
      },
      validation_summary: {
        total_validations: 1187,
        success_rate: 94.6,
        common_errors: [
          { error_code: 'INVALID_FORMAT', count: 32, percentage: 45.7 },
          { error_code: 'MISSING_FIELD', count: 18, percentage: 25.7 },
          { error_code: 'DUPLICATE_IRN', count: 12, percentage: 17.1 },
          { error_code: 'AUTH_FAILURE', count: 8, percentage: 11.5 }
        ]
      },
      b2b_vs_b2c_summary: {
        b2b_percentage: 68.5,
        b2c_percentage: 31.5,
        b2b_success_rate: 96.8,
        b2c_success_rate: 89.2,
        b2b_count: 0,
        b2c_count: 0
      },
      odoo_summary: {
        active_integrations: 3,
        total_invoices: 1028,
        success_rate: 92.4
      },
      system_summary: {
        total_requests: 2456,
        error_rate: 3.2,
        avg_response_time: 253.8
      }
    };
  }
};

/**
 * Fetch IRN metrics data
 * @param timeRange Time range for the metrics (24h, 7d, 30d, all)
 * @param organizationId Optional organization ID to filter metrics
 * @returns IRN metrics data
 */
export const fetchIRNMetrics = async (timeRange: string = '24h', organizationId?: string): Promise<IRNMetrics> => {
  try {
    let url = `${API_V1}/dashboard/irn-metrics?time_range=${timeRange}`;
    if (organizationId) {
      url += `&organization_id=${organizationId}`;
    }
    
    const response = await axios.get(url);
    return response.data;
  } catch (error) {
    console.error('Error fetching IRN metrics:', error);
    
    // Generate timestamps for hourly data (last 24 hours)
    const hourlyData: HourlyGeneration[] = [];
    const now = new Date();
    for (let i = 0; i < 24; i++) {
      const timestamp = new Date(now);
      timestamp.setHours(now.getHours() - i);
      hourlyData.push({
        hour: timestamp.getHours(),
        timestamp: timestamp.toISOString(),
        count: Math.floor(Math.random() * 50) + 10 // Random count between 10-60
      });
    }
    
    // Generate timestamps for daily data (last 30 days)
    const dailyData: DailyGeneration[] = [];
    for (let i = 0; i < 30; i++) {
      const date = new Date(now);
      date.setDate(now.getDate() - i);
      dailyData.push({
        day: date.getDate(),
        date: date.toISOString().split('T')[0],
        count: Math.floor(Math.random() * 200) + 50 // Random count between 50-250
      });
    }
    
    // Return mock data for development and testing
    return {
      total_count: 1245,
      status_counts: {
        unused: 178,
        active: 956,
        used: 845,
        expired: 111,
        cancelled: 32
      },
      hourly_generation: hourlyData,
      daily_generation: dailyData,
      time_range: timeRange
    };
  }
};
/**
 * Fetch validation metrics data
 * @param timeRange Time range for the metrics (24h, 7d, 30d, all)
 * @param organizationId Optional organization ID to filter metrics
 * @returns Validation metrics data
 */
export const fetchValidationMetrics = async (timeRange: string = '24h', organizationId?: string): Promise<ValidationMetrics> => {
  try {
    // Add query parameters for time range and organization if provided
    const params = new URLSearchParams();
    params.append('time_range', timeRange);
    if (organizationId) {
      params.append('organization_id', organizationId);
    }
    
    const response = await axios.get(`${API_V1}/metrics/validation?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching validation metrics:', error);
    
    // Generate mock data for development and testing
    const hourlyData: HourlyValidation[] = [];
    const now = new Date();
    
    // Generate 24 hours of data for 24h, 7 days worth for 7d, etc.
    const hoursToGenerate = timeRange === '24h' ? 24 : timeRange === '7d' ? 168 : 30 * 24;
    
    for (let i = 0; i < hoursToGenerate; i++) {
      const timestamp = new Date(now.getTime() - (i * 60 * 60 * 1000));
      const total = Math.floor(Math.random() * 50) + 10;
      const success = Math.floor(Math.random() * total);
      const failure = total - success;
      const success_rate = (success / total) * 100;
      
      hourlyData.push({
        hour: timestamp.getHours(),
        timestamp: timestamp.toISOString(),
        total,
        success,
        failure,
        success_rate
      });
    }
    
    // Generate common error types
    const commonErrors: CommonError[] = [
      { error_code: 'INVALID_FORMAT', count: 45, percentage: 30 },
      { error_code: 'MISSING_FIELDS', count: 38, percentage: 25 },
      { error_code: 'CALCULATION_ERROR', count: 32, percentage: 20 },
      { error_code: 'INVALID_TAX', count: 24, percentage: 15 },
      { error_code: 'NETWORK_ERROR', count: 15, percentage: 10 }
    ];
    
    return {
      total_count: 1543,
      success_count: 1357,
      failure_count: 186,
      success_rate: 88,
      common_errors: commonErrors,
      hourly_validation: hourlyData,
      time_range: timeRange
    };
  }
};

/**
 * Fetch B2B vs B2C metrics data
 * @param timeRange Time range for the metrics (24h, 7d, 30d, all)
 * @param organizationId Optional organization ID to filter metrics
 * @returns B2B vs B2C metrics data
 */
export const fetchB2BVsB2CMetrics = async (
  timeRange: string = '24h',
  organizationId?: string
): Promise<B2BvsB2CMetrics> => {
  try {
    // Build query parameters
    const params: Record<string, string> = { time_range: timeRange };
    if (organizationId) {
      params.organization_id = organizationId;
    }

    // Make the API request
    const response = await axios.get(`${API_V1}/dashboard/metrics/b2b-vs-b2c`, { params });
    return response.data;
  } catch (error) {
    // Proper error handling with type assertion for Axios errors
    const axiosError = error as import('axios').AxiosError;
    console.error('Error fetching B2B vs B2C metrics:', axiosError.response?.data || axiosError.message);
    
    // Return default metrics in case of an error
    return {
      total_count: 0,
      b2b_count: 0,
      b2c_count: 0,
      b2b_percentage: 0,
      b2c_percentage: 0,
      b2b_success_rate: 0,
      b2c_success_rate: 0,
      daily_breakdown: [],
      time_range: timeRange
    };
  }
};
/**
 * Fetch Odoo integration metrics data
 * @param timeRange Time range for the metrics (24h, 7d, 30d, all)
 * @param organizationId Optional organization ID to filter metrics
 * @returns Odoo integration metrics data
 */
export const fetchOdooIntegrationMetrics = async (
  timeRange: string = '24h',
  organizationId?: string
): Promise<OdooIntegrationMetrics> => {
  try {
    // Build query parameters
    const params: Record<string, string> = { time_range: timeRange };
    if (organizationId) {
      params.organization_id = organizationId;
    }

    // Make the API request
    const response = await axios.get(`${API_V1}/dashboard/metrics/odoo`, { params });
    return response.data;
  } catch (error) {
    // Proper error handling with type assertion for Axios errors
    const axiosError = error as import('axios').AxiosError;
    console.error('Error fetching Odoo integration metrics:', axiosError.response?.data || axiosError.message);
    
    // Return default metrics in case of an error
    return {
      total_integrations: 0,
      active_integrations: 0,
      inactive_integrations: 0,
      total_invoices: 0,
      successful_invoices: 0,
      success_rate: 0,
      integration_statuses: [],
      hourly_counts: [],
      time_range: timeRange
    };
  }
};
