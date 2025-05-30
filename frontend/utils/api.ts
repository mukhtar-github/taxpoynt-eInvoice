/**
 * @deprecated This API client is deprecated in favor of apiService.
 * Please import from 'utils/apiService' instead.
 * This file is maintained for backward compatibility only.
 */

import apiService from './apiService';
import axios from 'axios';

// For backward compatibility, expose the axios instance directly
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Use the same interceptors as apiService
const axiosInstance = apiService.getAxiosInstance();
api.interceptors.request = axiosInstance.interceptors.request;
api.interceptors.response = axiosInstance.interceptors.response;

export default api;