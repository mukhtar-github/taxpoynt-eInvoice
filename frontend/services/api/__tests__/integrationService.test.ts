import { IntegrationService } from '../integrationService';
import { apiClient } from '@/utils/apiClient';

// Mock the apiClient
jest.mock('@/utils/apiClient', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn()
  }
}));

describe('IntegrationService', () => {
  const mockOrganizationId = 'org-123';
  const mockIntegrationId = 'int-456';
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  describe('getIntegrations', () => {
    test('calls the correct endpoint and returns data', async () => {
      const mockResponse = {
        data: {
          success: true,
          integrations: [
            { id: '1', name: 'Test Integration', integration_type: 'odoo', status: 'configured' }
          ]
        }
      };
      
      (apiClient.get as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const result = await IntegrationService.getIntegrations(mockOrganizationId);
      
      // Check the endpoint
      expect(apiClient.get).toHaveBeenCalledWith(
        `/api/v1/organizations/${mockOrganizationId}/integrations`
      );
      
      // Check the returned data
      expect(result).toEqual(mockResponse.data);
      expect(result.integrations).toHaveLength(1);
      expect(result.integrations[0].name).toBe('Test Integration');
    });
    
    test('throws an error when the API request fails', async () => {
      const mockError = new Error('Network error');
      (apiClient.get as jest.Mock).mockRejectedValueOnce(mockError);
      
      await expect(IntegrationService.getIntegrations(mockOrganizationId))
        .rejects.toThrow();
    });
  });
  
  describe('getIntegration', () => {
    test('calls the correct endpoint and returns data', async () => {
      const mockResponse = {
        data: {
          success: true,
          integration: { 
            id: mockIntegrationId, 
            name: 'Test Integration',
            integration_type: 'odoo',
            status: 'configured'
          }
        }
      };
      
      (apiClient.get as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const result = await IntegrationService.getIntegration(mockOrganizationId, mockIntegrationId);
      
      // Check the endpoint
      expect(apiClient.get).toHaveBeenCalledWith(
        `/api/v1/organizations/${mockOrganizationId}/integrations/${mockIntegrationId}`
      );
      
      // Check the returned data
      expect(result).toEqual(mockResponse.data);
      expect(result.integration.id).toBe(mockIntegrationId);
    });
  });
  
  describe('syncIntegration', () => {
    test('calls the correct endpoint and returns success response', async () => {
      const mockResponse = {
        data: {
          success: true,
          integration: {
            id: mockIntegrationId,
            status: 'syncing'
          }
        }
      };
      
      (apiClient.post as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const result = await IntegrationService.syncIntegration(mockOrganizationId, mockIntegrationId);
      
      // Check the endpoint
      expect(apiClient.post).toHaveBeenCalledWith(
        `/api/v1/organizations/${mockOrganizationId}/integrations/${mockIntegrationId}/sync`
      );
      
      // Check the returned data
      expect(result).toEqual(mockResponse.data);
      expect(result.integration.status).toBe('syncing');
    });
  });
  
  describe('deleteIntegration', () => {
    test('calls the correct endpoint', async () => {
      const mockResponse = { data: { success: true } };
      
      (apiClient.delete as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      await IntegrationService.deleteIntegration(mockOrganizationId, mockIntegrationId);
      
      // Check the endpoint
      expect(apiClient.delete).toHaveBeenCalledWith(
        `/api/v1/organizations/${mockOrganizationId}/integrations/${mockIntegrationId}`
      );
    });
  });
  
  describe('getInvoices', () => {
    test('calls the correct endpoint with query parameters', async () => {
      const mockResponse = {
        data: {
          success: true,
          invoices: [{ id: '1', name: 'INV-001' }],
          total: 1
        }
      };
      
      (apiClient.get as jest.Mock).mockResolvedValueOnce(mockResponse);
      
      const params = {
        page: 1,
        page_size: 10,
        include_draft: true,
        search: 'test'
      };
      
      await IntegrationService.getInvoices(mockOrganizationId, mockIntegrationId, 'odoo', params);
      
      // Check the endpoint with query string
      expect(apiClient.get).toHaveBeenCalledWith(
        expect.stringContaining(`/api/v1/organizations/${mockOrganizationId}/integrations/${mockIntegrationId}/odoo/invoices?`)
      );
      
      // Check query parameters
      const calledUrl = (apiClient.get as jest.Mock).mock.calls[0][0];
      expect(calledUrl).toContain('page=1');
      expect(calledUrl).toContain('page_size=10');
      expect(calledUrl).toContain('include_draft=true');
      expect(calledUrl).toContain('search=test');
    });
  });
});
