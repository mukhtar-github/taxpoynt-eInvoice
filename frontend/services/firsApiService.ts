/**
 * FIRS API Service for frontend components
 * Provides consistent API interactions with comprehensive error handling
 */
import axios, { AxiosError, AxiosResponse } from 'axios';

// For FIRS testing, use local backend which has whitelisted IP
// In development mode (localhost), use relative paths which go to the same origin
// In production, explicitly target the local development server if in test mode
const getApiBaseUrl = () => {
  // Check if we're in development mode (running on localhost)
  const isDevelopment = typeof window !== 'undefined' && 
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
  
  // In development, use relative paths
  if (isDevelopment) {
    return '';
  }
  
  // In FIRS test mode, use the local backend even in production
  const isFirsTestMode = typeof window !== 'undefined' && 
    window.location.pathname.includes('/firs-test');
    
  if (isFirsTestMode) {
    return 'http://localhost:8000';
  }
  
  // Default - use environment variable or empty string (relative URL)
  return process.env.NEXT_PUBLIC_API_URL || '';
};
import { 
  ApiResponse, 
  ApiErrorResponse, 
  FirsApiRequestOptions,
  InvoiceSubmitRequest,
  InvoiceSubmissionResponse,
  SubmissionStatusResponse,
  BatchSubmissionResponse
} from '../types/firs/api-types';

// Default request timeout (30 seconds)
const DEFAULT_TIMEOUT = 30000;

/**
 * Format an API error into a consistent structure
 */
const formatApiError = (error: AxiosError<ApiErrorResponse>): string => {
  // Check if response exists
  if (error.response) {
    // FIRS API specific error format
    if (error.response.data?.detail?.message) {
      return error.response.data.detail.message;
    }
    
    // Generic error message with status
    return `Error ${error.response.status}: ${error.response.statusText || 'Unknown error'}`;
  }
  
  // Network error (no response)
  if (error.request) {
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again later.';
    }
    return 'Network error. Please check your connection and try again.';
  }
  
  // Request setup error
  return error.message || 'An unknown error occurred';
};

/**
 * Generic API request handler with consistent error handling
 */
const apiRequest = async <T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  data?: any,
  options: FirsApiRequestOptions = {}
): Promise<ApiResponse<T>> => {
  try {
    // Get settings from localStorage if not provided
    const timeout = options.timeout || 
      parseInt(localStorage.getItem('firs_timeout') || '', 10) || 
      DEFAULT_TIMEOUT;
    
    // Get authorization from localStorage if available
    let headers = options.headers || {};
    const token = localStorage.getItem('auth_token');
    if (token) {
      headers = { ...headers, Authorization: `Bearer ${token}` };
    }
    
    // Make the request
    const response: AxiosResponse<T> = await axios({
      method,
      url,
      data,
      headers,
      timeout
    });
    
    return {
      data: response.data,
      status: response.status,
      success: true,
      message: "Request successful" // Add missing message property required by ApiResponse<T>
    };
  } catch (error) {
    // Handle axios errors
    if (axios.isAxiosError(error) && error.response) {
      console.error('API Error:', error.response.data);
      
      // Return formatted error response
      const errorMessage = formatApiError(error);
      return {
        data: error.response.data as T,
        status: error.response.status,
        success: false,
        error: errorMessage,
        message: errorMessage // Add missing message property required by ApiResponse<T>
      };
    }
    
    // Handle non-axios errors
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Non-Axios Error:', errorMessage);
    
    return {
      data: {} as T,
      status: 500,
      success: false,
      error: errorMessage,
      message: errorMessage // Add missing message property required by ApiResponse<T>
    };
  }
};

/**
 * FIRS API Service
 */
const firsApiService = {
  /**
   * Submit an Odoo invoice to FIRS
   */
  submitInvoice(
    invoiceData: InvoiceSubmitRequest,
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<InvoiceSubmissionResponse>> {
    const { useSandbox = true, useUUID4 = true, ...restOptions } = options || {};
    
    // Construct URL with appropriate query parameters
    let url = `/api/firs/submit`;
    const params: string[] = [];
    if (useSandbox) params.push('sandbox=true');
    if (useUUID4) params.push('uuid4=true');
    if (params.length > 0) url += `?${params.join('&')}`;
    
    return apiRequest(
      'post',
      url,
      invoiceData,
      options
    );
  },
  
  /**
   * Check the status of a FIRS submission
   */
  checkSubmissionStatus: async (
    submissionId: string,
    useSandbox?: boolean,
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<SubmissionStatusResponse>> => {
    // Log the request for debugging
    console.log('Checking FIRS submission status for ID:', submissionId);
    
    // Get the correct API base URL based on environment
    const baseUrl = getApiBaseUrl();
    const params = useSandbox !== undefined ? `?use_sandbox=${useSandbox}` : '';
    const url = `${baseUrl}/api/firs/submission-status/${submissionId}${params}`;
    
    console.log('Status check URL:', url);
    
    return apiRequest<SubmissionStatusResponse>(
      'get',
      url,
      undefined,
      options
    );
  },
  
  /**
   * Submit a batch of invoices to FIRS
   */
  submitBatch: async (
    batchData: InvoiceSubmitRequest[],
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<BatchSubmissionResponse>> => {
    // Add extended timeout for batch submissions
    const batchOptions = { 
      ...options,
      timeout: (options?.timeout || DEFAULT_TIMEOUT) + (batchData.length * 5000)
    };
    
    return apiRequest<BatchSubmissionResponse>(
      'post',
      '/api/firs/batch-submit',
      batchData,
      batchOptions
    );
  },
  
  /**
   * Test connection to the API server
   */
  testConnection: async (): Promise<ApiResponse<{status: string}>> => {
    return apiRequest<{status: string}>(
      'get',
      '/api/firs/status',
      undefined,
      { timeout: 10000 } // Use shorter timeout for connection test
    );
  },
  
  /**
   * Connect to Odoo and fetch invoice data
   */
  fetchOdooInvoices: async (
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<any[]>> => {
    const baseUrl = getApiBaseUrl();
    return apiRequest<any[]>(
      'get',
      `${baseUrl}/api/odoo/invoices`,
      undefined,
      options
    );
  },
  
  /**
   * Convert Odoo invoice to FIRS format with UUID4
   */
  convertOdooInvoice: async (
    invoiceId: string,
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<any>> => {
    const baseUrl = getApiBaseUrl();
    const { useSandbox = true, useUUID4 = true, ...restOptions } = options || {};
    
    // Construct URL with appropriate query parameters
    let url = `${baseUrl}/api/odoo/convert-invoice/${invoiceId}`;
    const params: string[] = [];
    if (useSandbox) params.push('sandbox=true');
    if (useUUID4) params.push('uuid4=true');
    if (params.length > 0) url += `?${params.join('&')}`;
    
    return apiRequest<any>(
      'get',
      url,
      undefined,
      restOptions
    );
  }
};

export default firsApiService;
