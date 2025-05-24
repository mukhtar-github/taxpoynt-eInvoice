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
      success: true
    };
  } catch (error) {
    // Handle axios errors
    if (axios.isAxiosError(error) && error.response) {
      console.error('API Error:', error.response.data);
      
      // Return formatted error response
      return {
        data: error.response.data as T,
        status: error.response.status,
        success: false,
        error: formatApiError(error)
      };
    }
    
    // Handle non-axios errors
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    console.error('Non-Axios Error:', errorMessage);
    
    return {
      data: {} as T,
      status: 500,
      success: false,
      error: errorMessage
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
  submitInvoice: async (
    invoiceData: InvoiceSubmitRequest,
    options?: FirsApiRequestOptions
  ): Promise<ApiResponse<InvoiceSubmissionResponse>> => {
    // Log the request for debugging purposes
    console.log('Submitting invoice to FIRS API:', JSON.stringify(invoiceData, null, 2));
    
    // Get the correct API base URL based on environment
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/api/firs/submit-invoice`;
    
    console.log('Submission URL:', url);
    
    return apiRequest<InvoiceSubmissionResponse>(
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
    // Get the correct API base URL based on environment
    const baseUrl = getApiBaseUrl();
    const url = `${baseUrl}/health`;
    
    console.log('Testing connection to:', url);
    
    return apiRequest<{status: string}>(
      'get',
      url,
      undefined,
      { timeout: 5000 } // Short timeout for health check
    );
  }
};

export default firsApiService;
