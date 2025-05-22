/**
 * Error handling utilities for TaxPoynt eInvoice frontend
 * Provides consistent error handling for API interactions
 */
import axios, { AxiosError } from 'axios';

/**
 * Format API errors into a consistent structure
 * Particularly focused on handling FIRS API errors
 * 
 * @param error - The error object from API call
 * @param fallbackMessage - Message to show if error cannot be parsed
 * @returns Formatted error or the fallback value
 */
export const handleApiError = (error: unknown, fallbackMessage: string = 'An error occurred') => {
  // Check for Axios errors
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<any>;
    
    // Check for response
    if (axiosError.response) {
      // Handle FIRS specific error format
      if (axiosError.response.data?.detail?.message) {
        console.error('API Error:', axiosError.response.data.detail.message);
        return {
          error: true,
          message: axiosError.response.data.detail.message
        };
      }
      
      // Handle validation errors (often returned as array or object)
      if (axiosError.response.data?.detail) {
        const detail = axiosError.response.data.detail;
        let message = '';
        
        if (Array.isArray(detail)) {
          message = detail.map(item => item.msg || item.message || JSON.stringify(item)).join('; ');
        } else if (typeof detail === 'object') {
          message = Object.values(detail).join('; ');
        } else {
          message = String(detail);
        }
        
        console.error('API Error:', message);
        return {
          error: true,
          message
        };
      }
      
      // Handle standard error responses
      const status = axiosError.response.status;
      const statusText = axiosError.response.statusText || 'Unknown error';
      const message = `Error ${status}: ${statusText}`;
      
      console.error('API Error:', message);
      return {
        error: true,
        message,
        status
      };
    }
    
    // Handle network errors
    if (axiosError.request) {
      const message = 'Network error: No response received from server';
      console.error('API Error:', message);
      return {
        error: true,
        message,
        isNetworkError: true
      };
    }
  }
  
  // Handle generic errors
  console.error('Unknown error:', error);
  return {
    error: true,
    message: fallbackMessage
  };
};

/**
 * Check if an error is related to authentication
 * 
 * @param error - Error object to check
 * @returns Boolean indicating if it's an auth error
 */
export const isAuthError = (error: unknown): boolean => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError;
    return axiosError.response?.status === 401 || axiosError.response?.status === 403;
  }
  return false;
};

/**
 * Handle authentication errors by redirecting to login
 * 
 * @param error - Error object to check
 */
export const handleAuthError = (error: unknown): void => {
  if (isAuthError(error)) {
    // Clear existing auth data
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    
    // Redirect to login
    const currentPath = window.location.pathname;
    window.location.href = `/auth/login?redirect=${encodeURIComponent(currentPath)}`;
  }
};
