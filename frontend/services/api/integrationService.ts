import { apiClient } from '@/utils/apiClient';
import {
  Integration,
  IntegrationsResponse,
  IntegrationResponse,
  CompanyInfoResponse,
  InvoicesResponse,
  CustomersResponse,
  ProductsResponse,
  APIErrorResponse
} from './types';

/**
 * Centralized service for all ERP integration API calls
 * Provides type-safe methods and standardized error handling
 */
export class IntegrationService {
  /**
   * Get all integrations for an organization
   */
  static async getIntegrations(organizationId: string): Promise<IntegrationsResponse> {
    try {
      const response = await apiClient.get(`/api/v1/organizations/${organizationId}/integrations`);
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get a specific integration by ID
   */
  static async getIntegration(organizationId: string, integrationId: string): Promise<IntegrationResponse> {
    try {
      const response = await apiClient.get(`/api/v1/organizations/${organizationId}/integrations/${integrationId}`);
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get company information for an integration
   */
  static async getCompanyInfo(organizationId: string, integrationId: string): Promise<CompanyInfoResponse> {
    try {
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/company`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Sync an integration (pull latest data from ERP)
   */
  static async syncIntegration(organizationId: string, integrationId: string): Promise<IntegrationResponse> {
    try {
      const response = await apiClient.post(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/sync`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Delete an integration
   */
  static async deleteIntegration(organizationId: string, integrationId: string): Promise<{ success: boolean }> {
    try {
      const response = await apiClient.delete(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}`
      );
      return { success: true };
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get invoices for an integration with pagination, search, and filtering
   */
  static async getInvoices(
    organizationId: string,
    integrationId: string,
    erpType: string,
    params: {
      page?: number;
      page_size?: number;
      include_draft?: boolean;
      search?: string;
    } = {}
  ): Promise<InvoicesResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', String(params.page));
      if (params.page_size) queryParams.append('page_size', String(params.page_size));
      if (params.include_draft !== undefined) queryParams.append('include_draft', String(params.include_draft));
      if (params.search) queryParams.append('search', params.search);
      
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/invoices${queryString}`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get customers for an integration with pagination and search
   */
  static async getCustomers(
    organizationId: string,
    integrationId: string,
    erpType: string,
    params: {
      page?: number;
      page_size?: number;
      search?: string;
    } = {}
  ): Promise<CustomersResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', String(params.page));
      if (params.page_size) queryParams.append('page_size', String(params.page_size));
      if (params.search) queryParams.append('search', params.search);
      
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/customers${queryString}`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get products for an integration with pagination, search, and filtering
   */
  static async getProducts(
    organizationId: string,
    integrationId: string,
    erpType: string,
    params: {
      page?: number;
      page_size?: number;
      search?: string;
      category?: string;
    } = {}
  ): Promise<ProductsResponse> {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.page) queryParams.append('page', String(params.page));
      if (params.page_size) queryParams.append('page_size', String(params.page_size));
      if (params.search) queryParams.append('search', params.search);
      if (params.category) queryParams.append('category', params.category);
      
      const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
      
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/products${queryString}`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Test a connection to an ERP system
   */
  static async testConnection(
    organizationId: string,
    integrationType: string,
    config: Record<string, any>
  ): Promise<{
    status: string; success: boolean; message: string 
}> {
    try {
      const response = await apiClient.post(
        `/api/v1/organizations/${organizationId}/integrations/test-connection`,
        {
          integration_type: integrationType,
          config
        }
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Create a new integration
   */
  static async createIntegration(
    organizationId: string,
    integration: {
      name: string;
      description: string;
      integration_type: string;
      config: Record<string, any>;
    }
  ): Promise<IntegrationResponse> {
    try {
      const response = await apiClient.post(
        `/api/v1/organizations/${organizationId}/integrations`,
        integration
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Standardized API error handling
   */
  private static handleApiError(error: any): never {
    console.error('API Error:', error);
    
    let errorResponse: APIErrorResponse = {
      success: false,
      error: 'Unknown error occurred'
    };
    
    if (error.response) {
      // The request was made and the server responded with a status code outside of 2xx
      errorResponse = {
        success: false,
        error: error.response.data.message || error.response.data.error || 'Server error',
        status_code: error.response.status,
        details: error.response.data
      };
    } else if (error.request) {
      // The request was made but no response was received
      errorResponse = {
        success: false,
        error: 'No response received from server. Please check your internet connection.'
      };
    } else {
      // Something happened in setting up the request
      errorResponse = {
        success: false,
        error: error.message || 'Error setting up request'
      };
    }
    
    throw errorResponse;
  }
}
