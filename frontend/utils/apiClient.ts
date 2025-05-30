/**
 * @deprecated This API client is deprecated in favor of apiService.
 * Please import from 'utils/apiService' instead.
 * This file is maintained for backward compatibility only.
 */

import axios from 'axios';
import apiService from './apiService';

// Create an axios instance with default configuration
const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Use the same interceptors as apiService for consistent behavior
const axiosInstance = apiService.getAxiosInstance();
apiClient.interceptors.request = axiosInstance.interceptors.request;
apiClient.interceptors.response = axiosInstance.interceptors.response;

export { apiClient };
