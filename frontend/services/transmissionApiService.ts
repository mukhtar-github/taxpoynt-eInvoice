/**
 * Transmission API Service for frontend components
 * Provides consistent API interactions for transmission tracking
 */
import axios, { AxiosError, AxiosResponse } from 'axios';
import { UUID } from 'crypto';

// Type definitions
export interface TransmissionStatus {
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
  retrying: number;
  canceled: number;
  success_rate: number;
  average_retries: number;
  signed_transmissions: number;
}

export interface TimelinePoint {
  period: string;
  total: number;
  pending: number;
  in_progress: number;
  completed: number;
  failed: number;
  retrying: number;
  cancelled: number;
}

export interface TransmissionTimeline {
  timeline: TimelinePoint[];
  interval: string;
  start_date?: string;
  end_date?: string;
}

export interface HistoryEvent {
  timestamp: string;
  event: string;
  status: string;
  details?: string;
}

export interface DebugInfo {
  encryption_metadata: Record<string, any>;
  response_data: Record<string, any>;
  retry_count: number;
  error_details: Record<string, any>;
}

export interface TransmissionDetail {
  updated_at: string;
  invoice_reference: string;
  created_at: string;
  last_retry_at?: string;
  metadata: any;
  debug_info: any;
  id: string;
  organization_id: string;
  certificate_id?: string;
  submission_id?: string;
  transmission_time: string;
  status: string;
  retry_count: number;
  last_retry_time?: string;
  created_by?: string;
  transmission_metadata?: Record<string, any>;
  encrypted_payload?: string;
  encryption_metadata?: Record<string, any>;
  response_data?: Record<string, any>;
}

export interface TransmissionHistory {
  transmission: TransmissionDetail;
  history: HistoryEvent[];
  debug_info: DebugInfo;
}

export interface TransmissionListItem {
  id: string;
  organization_id: string;
  certificate_id?: string;
  submission_id?: string;
  transmission_time: string;
  status: string;
  retry_count: number;
  created_at: string;
  reference_id?: string;
}

export interface TransmissionBatchUpdate {
  transmission_ids: string[];
  status?: string;
  response_data?: Record<string, any>;
  transmission_metadata?: Record<string, any>;
}

export interface TransmissionBatchUpdateResponse {
  updated: number;
  failed: number;
  errors: string[];
}

// For API requests, use backend endpoints - moved to service object

// Generic API response type
interface ApiResponse<T> {
  data: T | null;
  error: string | null;
  status: number;
}

// Dashboard analytics response type
interface AnalyticsResponse {
  total: number;
  totalChange: number;
  successful: number;
  successfulChange: number;
  failed: number;
  failedChange: number;
  pending: number;
  pendingChange: number;
  items: any;
}

// Error response from API
interface ApiErrorResponse {
  detail?: string;
  message?: string;
}

// API request options
interface ApiRequestOptions {
  headers?: Record<string, string>;
  params?: Record<string, any>;
}

// Format API error into a consistent structure
const formatApiError = (error: AxiosError<ApiErrorResponse>): string => {
  if (error.response) {
    const { data, status } = error.response;
    
    // Handle structured error responses
    if (data) {
      if (typeof data === 'string') {
        return data;
      }
      
      if (data.detail) {
        return data.detail;
      }
      
      if (data.message) {
        return data.message;
      }
    }
    
    // Default error message based on status
    return `Request failed with status ${status}`;
  }
  
  if (error.request) {
    return 'No response received from server. Please check your network connection.';
  }
  
  return error.message || 'Unknown error occurred';
};

// Generic API request handler with consistent error handling
const apiRequest = async <T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  data?: any,
  options: ApiRequestOptions = {}
): Promise<ApiResponse<T>> => {
  try {
    const baseURL = getApiBaseUrl();
    const fullUrl = `${baseURL}/api/v1${url}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      params: options.params
    };
    
    let response: AxiosResponse<T>;
    
    switch (method) {
      case 'get':
        response = await axios.get<T>(fullUrl, config);
        break;
      case 'post':
        response = await axios.post<T>(fullUrl, data, config);
        break;
      case 'put':
        response = await axios.put<T>(fullUrl, data, config);
        break;
      case 'delete':
        response = await axios.delete<T>(fullUrl, config);
        break;
      default:
        throw new Error(`Unsupported method: ${method}`);
    }
    
    return {
      data: response.data,
      error: null,
      status: response.status
    };
  } catch (err) {
    const error = err as AxiosError<ApiErrorResponse>;
    return {
      data: null,
      error: formatApiError(error),
      status: error.response?.status || 500
    };
  }
};

/**
 * Transmission API Service
 */
// API interfaces for enhanced transmission API
export interface BatchProcessingOptions {
  organization_id?: string;
  status_filter?: string[];
  max_transmissions?: number;
  batch_size?: number;
  max_concurrent_batches?: number;
  retry_strategy?: string;
  prioritize_failed?: boolean;
}

export interface BatchProcessingResponse {
  task_id: string;
  status: string;
  message: string;
  config: {
    batch_size: number;
    max_concurrent_batches: number;
    retry_strategy: string;
    status_filter: string[];
    max_transmissions: number;
  };
}

export interface BatchMetrics {
  total_transmissions: number;
  successful_transmissions: number;
  failed_transmissions: number;
  average_processing_time_ms: number;
  circuit_breaks: number;
  active_jobs: number;
  batch_sizes: number[];
  retry_counts: Record<string, number>;
  success_rates: Record<string, number>;
}

export interface AnalyticsOptions {
  start_date?: Date;
  end_date?: Date;
  organization_id?: string;
  interval?: 'hour' | 'day' | 'week' | 'month';
  metrics?: string[];
}

export interface TransmissionAnalyticsData {
  analytics: {
    volume?: any;
    success_rate?: any;
    performance?: any;
    retries?: any;
    errors?: any;
  };
  metadata: {
    start_date: string;
    end_date: string;
    interval: string;
    organization_id?: string;
  };
}

export interface TransmissionHealthData {
  status: 'healthy' | 'degraded' | 'critical';
  indicators: {
    error_rate: number;
    circuit_breaks: number;
    active_batches: number;
    average_processing_time_ms: number;
  };
  queues: {
    pending: number;
    in_progress: number;
    failed: number;
    retrying: number;
  };
  last_updated: string;
}

export interface RetryStrategyOptions {
  strategy: string;
  max_retries?: number;
  base_delay_ms?: number;
  force?: boolean;
}

const transmissionApiService = {
  /**
   * Get the API base URL based on environment
   */
  getApiBaseUrl: () => {
    // Check if we're in development mode
    const isDevelopment = typeof window !== 'undefined' && 
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
    
    // In development, use relative paths
    if (isDevelopment) {
      return '';
    }
    
    // Default - use environment variable or empty string (relative URL)
    return process.env.NEXT_PUBLIC_API_URL || '';
  },
  /**
   * Get transmission statistics
   */
  getStatistics: async (
    organizationId?: string,
    startDate?: Date,
    endDate?: Date,
    options?: ApiRequestOptions
  ): Promise<AnalyticsResponse> => {
    const params: Record<string, any> = {};
    
    if (organizationId) {
      params.organization_id = organizationId;
    }
    
    if (startDate) {
      params.start_date = startDate.toISOString();
    }
    
    if (endDate) {
      params.end_date = endDate.toISOString();
    }
    
    const response = await apiRequest<TransmissionStatus>(
      'get',
      '/transmissions/statistics',
      undefined,
      { ...options, params }
    );
    
    // Transform the raw API response into the AnalyticsResponse format
    if (response.data) {
      return {
        total: response.data.total || 0,
        totalChange: 0, // We'll calculate this if backend doesn't provide
        successful: response.data.completed || 0,
        successfulChange: 0,
        failed: response.data.failed || 0,
        failedChange: 0,
        pending: response.data.pending || 0,
        pendingChange: 0,
        items: null
      };
    }
    
    // Return default values if response has no data
    return {
      total: 0,
      totalChange: 0,
      successful: 0,
      successfulChange: 0,
      failed: 0,
      failedChange: 0,
      pending: 0,
      pendingChange: 0,
      items: null
    };
  },
  
  /**
   * Get transmission timeline data
   */
  getTimeline: (
    organizationId?: string,
    startDate?: Date,
    endDate?: Date,
    interval: 'hour' | 'day' | 'week' | 'month' = 'day',
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionTimeline>> => {
    const params: Record<string, any> = {
      interval
    };
    
    if (organizationId) {
      params.organization_id = organizationId;
    }
    
    if (startDate) {
      params.start_date = startDate.toISOString();
    }
    
    if (endDate) {
      params.end_date = endDate.toISOString();
    }
    
    return apiRequest<TransmissionTimeline>(
      'get',
      '/transmissions/timeline',
      undefined,
      { ...options, params }
    );
  },
  
  /**
   * List all transmissions with optional filtering
   */
  listTransmissions: async (
    organizationId?: string,
    certificateId?: string,
    submissionId?: string,
    status?: string,
    skip: number = 0,
    limit: number = 20,
    options?: ApiRequestOptions
  ): Promise<{ data: TransmissionListItem[], total: number }> => {
    const params: Record<string, any> = {
      skip,
      limit
    };
    
    if (organizationId) {
      params.organization_id = organizationId;
    }
    
    if (certificateId) {
      params.certificate_id = certificateId;
    }
    
    if (submissionId) {
      params.submission_id = submissionId;
    }
    
    if (status) {
      params.status = status;
    }
    
    const response = await apiRequest<TransmissionListItem[]>(
      'get',
      '/transmissions',
      undefined,
      { ...options, params }
    );
    
    // Return structured response
    return {
      data: response.data || [],
      total: Array.isArray(response.data) ? response.data.length : 0
    };
  },
  
  /**
   * Get detailed information for a specific transmission
   */
  getTransmission: (
    transmissionId: string,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionDetail>> => {
    return apiRequest<TransmissionDetail>(
      'get',
      `/transmissions/${transmissionId}`,
      undefined,
      options
    );
  },
  
  /**
   * Get detailed history for a specific transmission
   */
  getTransmissionHistory: (
    transmissionId: string,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionHistory>> => {
    return apiRequest<TransmissionHistory>(
      'get',
      `/transmissions/${transmissionId}/history`,
      undefined,
      options
    );
  },
  
  /**
   * Retry a failed transmission
   */
  retryTransmission: (
    transmissionId: string,
    maxRetries?: number,
    retryDelay?: number,
    force: boolean = false,
    notes?: string,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionDetail>> => {
    const data: Record<string, any> = {
      force
    };
    
    if (maxRetries !== undefined) {
      data.max_retries = maxRetries;
    }
    
    if (retryDelay !== undefined) {
      data.retry_delay = retryDelay;
    }
    
    if (notes) {
      data.notes = notes;
    }
    
    return apiRequest<TransmissionDetail>(
      'post',
      `/transmissions/${transmissionId}/retry`,
      data,
      options
    );
  },
  
  /**
   * Update multiple transmissions in a batch
   */
  batchUpdateTransmissions: (
    transmissionIds: string[],
    status?: string,
    responseData?: Record<string, any>,
    metadata?: Record<string, any>,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionBatchUpdateResponse>> => {
    const data: TransmissionBatchUpdate = {
      transmission_ids: transmissionIds
    };
    
    if (status) {
      data.status = status;
    }
    
    if (responseData) {
      data.response_data = responseData;
    }
    
    if (metadata) {
      data.transmission_metadata = metadata;
    }
    
    return apiRequest<TransmissionBatchUpdateResponse>(
      'post',
      '/transmissions/batch',
      data,
      options
    );
  },
  
  /**
   * Create a new transmission
   */
  createTransmission: (
    organizationId: string,
    certificateId: string,
    submissionId?: string,
    payload?: Record<string, any>,
    encryptPayload: boolean = true,
    retryStrategy?: Record<string, any>,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionDetail>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/transmission`;
    const data = {
      organization_id: organizationId,
      certificate_id: certificateId,
      submission_id: submissionId,
      payload,
      encrypt_payload: encryptPayload,
      retry_strategy: retryStrategy
    };

    return apiRequest<TransmissionDetail>(
      'post',
      url,
      data,
      options
    );
  },

  /**
   * Start batch processing of transmissions
   */
  batchProcessTransmissions: (
    batchOptions: BatchProcessingOptions,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<BatchProcessingResponse>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/platform/transmission/batch-process`;
    
    return apiRequest<BatchProcessingResponse>(
      'post',
      url,
      batchOptions,
      options
    );
  },

  /**
   * Get batch processing metrics
   */
  getBatchMetrics: (
    options?: ApiRequestOptions
  ): Promise<ApiResponse<BatchMetrics>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/platform/transmission/batch-metrics`;
    
    return apiRequest<BatchMetrics>(
      'get',
      url,
      undefined,
      options
    );
  },

  /**
   * Apply advanced retry strategy to a transmission
   */
  applyRetryStrategy: (
    transmissionId: string,
    retryOptions: RetryStrategyOptions,
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionDetail>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/platform/transmission/retry-strategies/${transmissionId}`;
    
    const params = {
      strategy: retryOptions.strategy,
      max_retries: retryOptions.max_retries,
      base_delay_ms: retryOptions.base_delay_ms,
      force: retryOptions.force
    };
    
    const reqOptions = {
      ...options,
      params
    };
    
    return apiRequest<TransmissionDetail>(
      'post',
      url,
      undefined,
      reqOptions
    );
  },

  /**
   * Get transmission analytics data
   */
  getTransmissionAnalytics: (
    startDate?: Date,
    endDate?: Date,
    organizationId?: string,
    interval: 'hour' | 'day' | 'week' | 'month' = 'day',
    metrics: string[] = ['volume', 'success_rate', 'performance'],
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionAnalyticsData>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/platform/transmission/analytics`;
    
    const params: Record<string, any> = {
      interval,
      metrics: metrics.join(',')
    };
    
    if (startDate) {
      params.start_date = startDate.toISOString();
    }
    
    if (endDate) {
      params.end_date = endDate.toISOString();
    }
    
    if (organizationId) {
      params.organization_id = organizationId;
    }
    
    const reqOptions = {
      ...options,
      params
    };
    
    return apiRequest<TransmissionAnalyticsData>(
      'get',
      url,
      undefined,
      reqOptions
    );
  },

  /**
   * Get transmission system health status
   */
  getTransmissionHealth: (
    options?: ApiRequestOptions
  ): Promise<ApiResponse<TransmissionHealthData>> => {
    const url = `${transmissionApiService.getApiBaseUrl()}/platform/transmission/health`;
    
    return apiRequest<TransmissionHealthData>(
      'get',
      url,
      undefined,
      options
    );
  }
};



export default transmissionApiService;
function getApiBaseUrl() {
  throw new Error('Function not implemented.');
}

