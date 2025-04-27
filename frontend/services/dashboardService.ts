import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Integration {
  id: string;
  name: string;
  client: string;
  status: 'active' | 'configured' | 'error';
  lastSynced: string | null;
}

export interface TransactionMetrics {
  today: number;
  week: number;
  month: number;
  success: number;
}

export interface Transaction {
  id: string;
  type: 'irn_generation' | 'validation' | 'submission';
  status: 'success' | 'failed' | 'pending';
  integration: string;
  timestamp: string;
}

export interface DashboardData {
  integrations: Integration[];
  metrics: TransactionMetrics;
  recentTransactions: Transaction[];
}

/**
 * Fetch dashboard data including integrations, metrics, and recent transactions
 */
export const fetchDashboardData = async (): Promise<DashboardData> => {
  try {
    const response = await axios.get(`${API_URL}/dashboard/metrics`);
    return response.data;
  } catch (error) {
    console.error('Error fetching dashboard data:', error);
    
    // Return mock data for POC phase
    return {
      integrations: [
        { id: '1', name: 'ERP Integration', client: 'ABC Corp', status: 'active', lastSynced: '2025-04-26T06:30:00Z' },
        { id: '2', name: 'Accounting System', client: 'XYZ Ltd', status: 'configured', lastSynced: null },
        { id: '3', name: 'POS Integration', client: 'Retail Co', status: 'error', lastSynced: '2025-04-25T14:22:00Z' },
      ],
      metrics: {
        today: 124,
        week: 738,
        month: 2945,
        success: 95.8
      },
      recentTransactions: [
        { id: '1', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:45:12Z' },
        { id: '2', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:44:23Z' },
        { id: '3', type: 'submission', status: 'failed', integration: 'POS Integration', timestamp: '2025-04-26T06:22:58Z' },
        { id: '4', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:18:42Z' },
        { id: '5', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:15:19Z' },
      ]
    };
  }
};

/**
 * Fetch integration status data
 */
export const fetchIntegrationStatus = async (): Promise<Integration[]> => {
  try {
    const response = await axios.get(`${API_URL}/integrations`);
    return response.data;
  } catch (error) {
    console.error('Error fetching integration status:', error);
    
    // Return mock data for POC phase
    return [
      { id: '1', name: 'ERP Integration', client: 'ABC Corp', status: 'active', lastSynced: '2025-04-26T06:30:00Z' },
      { id: '2', name: 'Accounting System', client: 'XYZ Ltd', status: 'configured', lastSynced: null },
      { id: '3', name: 'POS Integration', client: 'Retail Co', status: 'error', lastSynced: '2025-04-25T14:22:00Z' },
    ];
  }
};

/**
 * Fetch transaction metrics data
 */
export const fetchTransactionMetrics = async (): Promise<TransactionMetrics> => {
  try {
    const response = await axios.get(`${API_URL}/dashboard/transactions`);
    return response.data;
  } catch (error) {
    console.error('Error fetching transaction metrics:', error);
    
    // Return mock data for POC phase
    return {
      today: 124,
      week: 738,
      month: 2945,
      success: 95.8
    };
  }
};

/**
 * Fetch recent transactions
 */
export const fetchRecentTransactions = async (limit: number = 5): Promise<Transaction[]> => {
  try {
    const response = await axios.get(`${API_URL}/dashboard/transactions/recent?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching recent transactions:', error);
    
    // Return mock data for POC phase
    return [
      { id: '1', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:45:12Z' },
      { id: '2', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:44:23Z' },
      { id: '3', type: 'submission', status: 'failed', integration: 'POS Integration', timestamp: '2025-04-26T06:22:58Z' },
      { id: '4', type: 'irn_generation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:18:42Z' },
      { id: '5', type: 'validation', status: 'success', integration: 'ERP Integration', timestamp: '2025-04-26T06:15:19Z' },
    ];
  }
}; 