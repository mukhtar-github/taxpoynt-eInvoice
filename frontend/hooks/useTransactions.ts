import React, { useState, useCallback } from 'react';
import { apiClient } from '../utils/apiClient';

interface Transaction {
  id: string;
  external_transaction_id: string;
  transaction_amount: number;
  tax_amount: number;
  transaction_timestamp: string;
  invoice_generated: boolean;
  invoice_transmitted: boolean;
  pos_type: string;
  status: 'pending' | 'processed' | 'failed';
  items?: any[];
  customer_data?: any;
  pos_connection_id: string;
  created_at: string;
}

interface UseTransactionsResult {
  transactions: Transaction[];
  isLoading: boolean;
  error: string | null;
  fetchTransactions: () => Promise<void>;
  refreshTransactions: () => Promise<void>;
  getTransaction: (id: string) => Promise<Transaction | null>;
}

interface FetchTransactionsParams {
  limit?: number;
  offset?: number;
  posType?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
}

export function useTransactions(
  params: FetchTransactionsParams = {}
): UseTransactionsResult {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      
      // Add parameters to query string
      if (params.limit) queryParams.append('limit', params.limit.toString());
      if (params.offset) queryParams.append('offset', params.offset.toString());
      if (params.posType) queryParams.append('pos_type', params.posType);
      if (params.status) queryParams.append('status', params.status);
      if (params.dateFrom) queryParams.append('date_from', params.dateFrom);
      if (params.dateTo) queryParams.append('date_to', params.dateTo);

      const url = `/api/v1/pos/transactions${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await apiClient.get(url);
      
      setTransactions(response.data.transactions || response.data || []);
    } catch (err: any) {
      console.error('Failed to fetch transactions:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to fetch transactions'
      );
    } finally {
      setIsLoading(false);
    }
  }, [params]);

  const refreshTransactions = useCallback(async () => {
    await fetchTransactions();
  }, [fetchTransactions]);

  const getTransaction = useCallback(async (id: string): Promise<Transaction | null> => {
    try {
      const response = await apiClient.get(`/api/v1/pos/transactions/${id}`);
      return response.data;
    } catch (err: any) {
      console.error('Failed to fetch transaction:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to fetch transaction'
      );
      return null;
    }
  }, []);

  return {
    transactions,
    isLoading,
    error,
    fetchTransactions,
    refreshTransactions,
    getTransaction
  };
}

// Hook for real-time transaction monitoring
interface UseRealTimeTransactionsResult extends UseTransactionsResult {
  connectionStatus: 'connected' | 'connecting' | 'disconnected';
  lastUpdateTime: Date | null;
}

export function useRealTimeTransactions(
  params: FetchTransactionsParams = {},
  refreshInterval: number = 30000 // 30 seconds
): UseRealTimeTransactionsResult {
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'connecting' | 'disconnected'>('disconnected');
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);
  
  const transactionsHook = useTransactions(params);

  // Enhanced fetch function with real-time tracking
  const fetchWithRealTime = useCallback(async () => {
    setConnectionStatus('connecting');
    try {
      await transactionsHook.fetchTransactions();
      setConnectionStatus('connected');
      setLastUpdateTime(new Date());
    } catch (err) {
      setConnectionStatus('disconnected');
    }
  }, [transactionsHook.fetchTransactions]);

  // Set up polling for real-time updates
  React.useEffect(() => {
    const interval = setInterval(fetchWithRealTime, refreshInterval);
    
    // Initial fetch
    fetchWithRealTime();
    
    return () => clearInterval(interval);
  }, [fetchWithRealTime, refreshInterval]);

  return {
    ...transactionsHook,
    fetchTransactions: fetchWithRealTime,
    connectionStatus,
    lastUpdateTime
  };
}

// Hook for transaction statistics
interface TransactionStats {
  totalCount: number;
  totalAmount: number;
  averageAmount: number;
  successRate: number;
  pendingCount: number;
  processedCount: number;
  failedCount: number;
}

interface UseTransactionStatsResult {
  stats: TransactionStats | null;
  isLoading: boolean;
  error: string | null;
  fetchStats: () => Promise<void>;
}

export function useTransactionStats(
  dateFrom?: string,
  dateTo?: string
): UseTransactionStatsResult {
  const [stats, setStats] = useState<TransactionStats | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const queryParams = new URLSearchParams();
      if (dateFrom) queryParams.append('date_from', dateFrom);
      if (dateTo) queryParams.append('date_to', dateTo);

      const url = `/api/v1/pos/analytics/stats${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
      const response = await apiClient.get(url);
      
      setStats(response.data);
    } catch (err: any) {
      console.error('Failed to fetch transaction stats:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to fetch transaction stats'
      );
    } finally {
      setIsLoading(false);
    }
  }, [dateFrom, dateTo]);

  return {
    stats,
    isLoading,
    error,
    fetchStats
  };
}