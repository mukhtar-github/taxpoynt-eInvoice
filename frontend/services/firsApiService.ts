/**
 * FIRS API Service for frontend components
 * Provides consistent API interactions with comprehensive error handling
 */
import axios, { AxiosError, AxiosResponse } from 'axios';
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
    return apiRequest<InvoiceSubmissionResponse>(
      'post',
      '/api/firs/submit-invoice',
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
    const params = useSandbox !== undefined ? `?use_sandbox=${useSandbox}` : '';
    return apiRequest<SubmissionStatusResponse>(
      'get',
      `/api/firs/submission-status/${submissionId}${params}`,
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
      '/health',
      undefined,
      { timeout: 5000 } // Short timeout for health check
    );
  }
};

export default firsApiService;
