import axios, { AxiosHeaders, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';

/**
 * Unified API client for TaxPoynt eInvoice
 * Combines features from both previous implementations:
 * - Basic authentication token handling
 * - Token refresh functionality
 * - Comprehensive error handling
 */
class ApiService {
  // Private to enforce encapsulation
  private instance: AxiosInstance;
  private isRefreshing = false;
  private refreshSubscribers: Array<(token: string) => void> = [];

  constructor() {
    this.instance = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Get the token from localStorage (only in browser environment)
        const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
        
        // If token exists, add it to the headers
        if (token) {
          // Make sure config.headers is an AxiosHeaders instance
          if (!config.headers) {
            config.headers = new AxiosHeaders();
          }
          config.headers.set('Authorization', `Bearer ${token}`);
        }
        
        return config;
      },
      (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Handle authentication errors (401)
        if (error.response?.status === 401 && !originalRequest._retry) {
          if (this.isRefreshing) {
            // If already refreshing, add request to queue
            return new Promise((resolve) => {
              this.refreshSubscribers.push((token: string) => {
                originalRequest.headers.set('Authorization', `Bearer ${token}`);
                resolve(this.instance(originalRequest));
              });
            });
          }

          originalRequest._retry = true;
          this.isRefreshing = true;
          
          try {
            // Attempt to refresh the token
            const refreshToken = localStorage.getItem('refreshToken');
            
            if (refreshToken) {
              const response = await axios.post(
                `${this.instance.defaults.baseURL}/auth/refresh-token`,
                { refresh_token: refreshToken }
              );
              
              // Get the new token
              const { access_token } = response.data;
              
              // Save the new token
              localStorage.setItem('token', access_token);
              
              // Update the original request with the new token
              if (!originalRequest.headers) {
                originalRequest.headers = new AxiosHeaders();
              }
              originalRequest.headers.set('Authorization', `Bearer ${access_token}`);
              
              // Notify all waiting requests
              this.refreshSubscribers.forEach(callback => callback(access_token));
              this.refreshSubscribers = [];
              
              // Retry the original request
              return this.instance(originalRequest);
            }
          } catch (err) {
            // If refresh token failed, logout the user
            this.handleLogout();
          } finally {
            this.isRefreshing = false;
          }
        }
        
        // Handle server errors (500+)
        if (error.response?.status >= 500) {
          console.error('Server error:', error.response.data);
          // Could add additional server error handling here
        }
        
        return Promise.reject(error);
      }
    );
  }

  // Helper method to handle logout
  private handleLogout(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    
    // Redirect to login page if in browser
    if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  // Public access to axios instance for compatibility
  public getAxiosInstance(): AxiosInstance {
    return this.instance;
  }

  // Public API methods
  public get<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.get<T>(url, config);
  }

  public post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.post<T>(url, data, config);
  }

  public put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.put<T>(url, data, config);
  }

  public delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.delete<T>(url, config);
  }

  public patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.instance.patch<T>(url, data, config);
  }
}

// Create and export a singleton instance
const apiService = new ApiService();
export default apiService;
