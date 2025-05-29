import api from './api';

/**
 * @deprecated This utility integration service is deprecated. 
 * Please use the class-based IntegrationService from '/services/api/integrationService.ts' instead.
 * This file will be removed in a future update.
 */

// Types
export interface Integration {
  id: string;
  name: string;
  description?: string;
  client_id: string;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
  created_by?: string;
  last_tested?: string;
  status: string;
}

export interface IntegrationCreate {
  name: string;
  description?: string;
  client_id: string;
  config: Record<string, any>;
}

export interface IntegrationUpdate {
  name?: string;
  description?: string;
  config?: Record<string, any>;
  status?: string;
  change_reason?: string;
}

export interface IntegrationTestResult {
  success: boolean;
  message: string;
  details?: Record<string, any>;
}

// Get all integrations
export const getIntegrations = async () => {
  const response = await api.get<Integration[]>('/integrations');
  return response.data;
};

// Get integration by ID
export const getIntegration = async (id: string) => {
  const response = await api.get<Integration>(`/integrations/${id}`);
  return response.data;
};

// Create a new integration
export const createIntegration = async (integration: IntegrationCreate) => {
  const response = await api.post<Integration>('/integrations', integration);
  return response.data;
};

// Update an integration
export const updateIntegration = async (id: string, update: IntegrationUpdate) => {
  const response = await api.put<Integration>(`/integrations/${id}`, update);
  return response.data;
};

// Delete an integration
export const deleteIntegration = async (id: string) => {
  const response = await api.delete<Integration>(`/integrations/${id}`);
  return response.data;
};

// Test an integration
export const testIntegration = async (id: string) => {
  const response = await api.post<IntegrationTestResult>(`/integrations/${id}/test`);
  return response.data;
};

// Get integration history
export const getIntegrationHistory = async (id: string) => {
  const response = await api.get<any[]>(`/integrations/${id}/history`);
  return response.data;
}; 