/**
 * CRM Integration Service
 * 
 * This service provides a comprehensive API interface for CRM integrations,
 * including HubSpot connection management, deal processing, and OAuth flows.
 */

import apiService from '@/utils/apiService';
import {
  CRMConnection,
  CRMConnectionCreate,
  CRMConnectionUpdate,
  CRMConnectionsResponse,
  CRMConnectionResponse,
  CRMConnectionTestResult,
  CRMDeal,
  CRMDealsResponse,
  CRMDealResponse,
  DealProcessRequest,
  DealProcessResponse,
  ConnectionSyncResponse,
  DealFilters,
  PaginationMeta,
  CRMErrorResponse,
  HubSpotConnectionConfig,
  OAuthTokenResponse,
  CRMType
} from '@/types/crm';

/**
 * Centralized service for all CRM integration API calls
 */
export class CRMService {
  private static readonly BASE_PATH = '/api/v1/integrations/crm';

  // ==================== CONNECTION MANAGEMENT ====================

  /**
   * Connect to a CRM platform
   */
  static async connectPlatform(
    platform: string,
    connectionData: CRMConnectionCreate
  ): Promise<CRMConnection> {
    try {
      const response = await apiService.post<CRMConnectionResponse>(
        `${this.BASE_PATH}/${platform}/connect`,
        connectionData
      );
      return response.data.connection;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get all CRM connections with optional filters
   */
  static async getConnections(
    organizationId?: string,
    params?: {
      page?: number;
      page_size?: number;
      platform?: string;
      active_only?: boolean;
    }
  ): Promise<{ connections: CRMConnection[]; pagination: PaginationMeta }> {
    try {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.page_size) queryParams.append('page_size', params.page_size.toString());
      if (params?.platform) queryParams.append('platform', params.platform);
      if (params?.active_only !== undefined) queryParams.append('active_only', params.active_only.toString());

      const response = await apiService.get<CRMConnectionsResponse>(
        `${this.BASE_PATH}/connections?${queryParams.toString()}`
      );
      
      return {
        connections: response.data.connections.items,
        pagination: {
          page: response.data.connections.page,
          page_size: response.data.connections.page_size,
          total: response.data.connections.total,
          pages: response.data.connections.pages,
          has_next: response.data.connections.page < response.data.connections.pages,
          has_prev: response.data.connections.page > 1
        }
      };
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get a specific CRM connection by ID
   */
  static async getConnection(
    organizationId: string,
    connectionId: string
  ): Promise<{ connection: CRMConnection }> {
    try {
      const response = await apiService.get<CRMConnectionResponse>(
        `${this.BASE_PATH}/connections/${connectionId}`
      );
      return { connection: response.data.connection };
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Update an existing CRM connection
   */
  static async updateConnection(
    connectionId: string,
    updateData: CRMConnectionUpdate
  ): Promise<CRMConnection> {
    try {
      const response = await apiService.put<CRMConnectionResponse>(
        `${this.BASE_PATH}/connections/${connectionId}`,
        updateData
      );
      return response.data.connection;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Delete a CRM connection
   */
  static async deleteConnection(
    organizationId: string,
    connectionId: string
  ): Promise<void> {
    try {
      await apiService.delete(`${this.BASE_PATH}/connections/${connectionId}`);
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Test a CRM connection
   */
  static async testConnection(connectionId: string): Promise<CRMConnectionTestResult> {
    try {
      const response = await apiService.post<CRMConnectionTestResult>(
        `${this.BASE_PATH}/connections/${connectionId}/test`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  // ==================== DEAL MANAGEMENT ====================

  /**
   * Get deals from a CRM connection with filters and pagination
   */
  static async getDeals(
    connectionId: string,
    filters?: DealFilters,
    pagination?: { page?: number; page_size?: number }
  ): Promise<{ deals: CRMDeal[]; pagination: PaginationMeta }> {
    try {
      const queryParams = new URLSearchParams();
      
      // Add pagination params
      if (pagination?.page) queryParams.append('page', pagination.page.toString());
      if (pagination?.page_size) queryParams.append('page_size', pagination.page_size.toString());
      
      // Add filter params
      if (filters?.stage) queryParams.append('stage', filters.stage);
      if (filters?.invoice_status) queryParams.append('invoice_status', filters.invoice_status);
      if (filters?.search) queryParams.append('search', filters.search);
      if (filters?.sort_by) queryParams.append('sort_by', filters.sort_by);
      if (filters?.sort_order) queryParams.append('sort_order', filters.sort_order);

      const response = await apiService.get<CRMDealsResponse>(
        `${this.BASE_PATH}/connections/${connectionId}/deals?${queryParams.toString()}`
      );
      
      return {
        deals: response.data.deals.items,
        pagination: {
          page: response.data.deals.page,
          page_size: response.data.deals.page_size,
          total: response.data.deals.total,
          total_pages: response.data.deals.pages,
        } as PaginationMeta
      };
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Get a specific deal by ID
   */
  static async getDeal(connectionId: string, dealId: string): Promise<CRMDeal> {
    try {
      const response = await apiService.get<CRMDealResponse>(
        `${this.BASE_PATH}/connections/${connectionId}/deals/${dealId}`
      );
      return response.data.deal;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Process a CRM deal (sync, generate invoice, etc.)
   */
  static async processDeal(
    connectionId: string,
    dealId: string,
    processRequest: DealProcessRequest
  ): Promise<DealProcessResponse['result']> {
    try {
      const response = await apiService.post<DealProcessResponse>(
        `${this.BASE_PATH}/connections/${connectionId}/deals/${dealId}/process`,
        processRequest
      );
      return response.data.result;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Manually sync deals from CRM
   */
  static async syncConnection(
    connectionId: string,
    daysBack: number = 30
  ): Promise<ConnectionSyncResponse['result']> {
    try {
      const response = await apiService.post<ConnectionSyncResponse>(
        `${this.BASE_PATH}/connections/${connectionId}/sync`,
        null,
        { params: { days_back: daysBack } }
      );
      return response.data.result;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  // ==================== HUBSPOT SPECIFIC METHODS ====================

  /**
   * Initiate HubSpot OAuth flow
   */
  static initiateHubSpotOAuth(redirectUri: string, state?: string): string {
    const clientId = process.env.NEXT_PUBLIC_HUBSPOT_CLIENT_ID;
    if (!clientId) {
      throw new Error('HubSpot client ID not configured');
    }

    const scope = 'crm.objects.deals.read crm.objects.contacts.read crm.objects.companies.read';
    const authUrl = new URL('https://app.hubspot.com/oauth/authorize');
    
    authUrl.searchParams.append('client_id', clientId);
    authUrl.searchParams.append('redirect_uri', redirectUri);
    authUrl.searchParams.append('scope', scope);
    authUrl.searchParams.append('response_type', 'code');
    
    if (state) {
      authUrl.searchParams.append('state', state);
    }

    return authUrl.toString();
  }

  /**
   * Exchange OAuth code for tokens
   */
  static async exchangeHubSpotCode(
    code: string,
    redirectUri: string,
    state?: string
  ): Promise<OAuthTokenResponse> {
    try {
      const response = await apiService.post<OAuthTokenResponse>(
        `${this.BASE_PATH}/hubspot/oauth/token`,
        {
          code,
          redirect_uri: redirectUri,
          state
        }
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Test HubSpot connection with provided configuration
   */
  static async testHubSpotConnection(config: HubSpotConnectionConfig): Promise<CRMConnectionTestResult> {
    try {
      const response = await apiService.post<CRMConnectionTestResult>(
        `${this.BASE_PATH}/hubspot/test-connection`,
        config
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  // ==================== BATCH OPERATIONS ====================

  /**
   * Process multiple deals in batch
   */
  static async batchProcessDeals(
    connectionId: string,
    dealIds: string[],
    action: DealProcessRequest['action']
  ): Promise<Array<{ deal_id: string; success: boolean; result?: any; error?: string }>> {
    try {
      const response = await apiService.post(
        `${this.BASE_PATH}/connections/${connectionId}/deals/batch-process`,
        {
          deal_ids: dealIds,
          action
        }
      );
      return response.data.results;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  /**
   * Generate invoices for multiple deals
   */
  static async batchGenerateInvoices(
    connectionId: string,
    dealIds: string[]
  ): Promise<Array<{ deal_id: string; invoice_id?: string; success: boolean; error?: string }>> {
    try {
      const response = await apiService.post(
        `${this.BASE_PATH}/connections/${connectionId}/deals/batch-generate-invoices`,
        { deal_ids: dealIds }
      );
      return response.data.results;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }

  // ==================== UTILITY METHODS ====================

  /**
   * Get supported CRM platforms
   */
  static getSupportedPlatforms(): Array<{ value: CRMType; label: string; description: string }> {
    return [
      {
        value: 'hubspot',
        label: 'HubSpot',
        description: 'Connect to HubSpot CRM for deal and contact management'
      },
      {
        value: 'salesforce',
        label: 'Salesforce',
        description: 'Connect to Salesforce CRM (Coming Soon)'
      },
      {
        value: 'pipedrive',
        label: 'Pipedrive',
        description: 'Connect to Pipedrive CRM (Coming Soon)'
      },
      {
        value: 'zoho',
        label: 'Zoho CRM',
        description: 'Connect to Zoho CRM (Coming Soon)'
      }
    ];
  }

  /**
   * Format deal stage for display
   */
  static formatDealStage(stage: string): string {
    return stage
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }

  /**
   * Format currency amount
   */
  static formatCurrency(amount: number, currency: string = 'NGN'): string {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 2
    }).format(amount);
  }

  /**
   * Generate OAuth state parameter
   */
  static generateOAuthState(): string {
    return btoa(JSON.stringify({
      timestamp: Date.now(),
      random: Math.random().toString(36).substring(2)
    }));
  }

  /**
   * Validate OAuth state parameter
   */
  static validateOAuthState(state: string, maxAge: number = 600000): boolean {
    try {
      const parsed = JSON.parse(atob(state));
      const age = Date.now() - parsed.timestamp;
      return age <= maxAge;
    } catch {
      return false;
    }
  }

  // ==================== ERROR HANDLING ====================

  /**
   * Handle API errors with enhanced error information
   */
  private static handleApiError(error: any): void {
    console.error('CRM API Error:', error);
    
    if (error.response?.data) {
      const errorData = error.response.data as CRMErrorResponse;
      console.error('Error details:', errorData);
      
      // You can add custom error handling logic here
      // For example, show specific error messages for common scenarios
      if (error.response.status === 401) {
        // Handle authentication errors
        localStorage.removeItem('token');
        window.location.href = '/auth/login';
      }
    }
  }

  /**
   * Check if error is a specific CRM error
   */
  static isCRMError(error: any, errorCode?: string): boolean {
    const errorData = error.response?.data as CRMErrorResponse;
    if (!errorData || errorData.success !== false) {
      return false;
    }
    
    if (errorCode) {
      return errorData.errors?.some(err => err.code === errorCode) || false;
    }
    
    return true;
  }

  /**
   * Sync deals from CRM platform
   */
  static async syncDeals(connectionId: string): Promise<ConnectionSyncResponse> {
    try {
      const response = await apiService.post<ConnectionSyncResponse>(
        `${this.BASE_PATH}/connections/${connectionId}/sync-deals`
      );
      return response.data;
    } catch (error: any) {
      this.handleApiError(error);
      throw error;
    }
  }
}

export default CRMService;