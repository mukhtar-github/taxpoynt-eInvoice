/**
 * Authentication service for TaxPoynt eInvoice frontend
 * Provides consistent authentication methods for API interactions
 */

/**
 * Get authentication headers for API requests
 * 
 * @returns Promise with authorization headers
 */
export const getAuthHeader = async (): Promise<Record<string, string>> => {
  // Get token from localStorage
  const token = localStorage.getItem('auth_token');
  
  if (!token) {
    console.warn('No authentication token found');
    return {};
  }
  
  return {
    Authorization: `Bearer ${token}`
  };
};

/**
 * Check if user is authenticated
 * 
 * @returns Boolean indicating if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  const token = localStorage.getItem('auth_token');
  return !!token;
};

/**
 * Get current user information
 * 
 * @returns User object or null if not authenticated
 */
export const getCurrentUser = () => {
  const userJson = localStorage.getItem('user');
  if (!userJson) return null;
  
  try {
    return JSON.parse(userJson);
  } catch (error) {
    console.error('Error parsing user data', error);
    return null;
  }
};

/**
 * Log out current user
 */
export const logout = () => {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user');
  
  // Redirect to login page
  window.location.href = '/auth/login';
};
