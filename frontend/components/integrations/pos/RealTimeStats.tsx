import React, { useEffect, useState } from 'react';
import { MetricCard } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { apiClient } from '../../../utils/apiClient';

interface RealTimeStatsData {
  totalTransactions: number;
  todayTransactions: number;
  totalRevenue: number;
  todayRevenue: number;
  averageTransactionValue: number;
  invoicesGenerated: number;
  invoicesTransmitted: number;
  successRate: number;
  peakHour: string;
  lastUpdated: string;
}

interface RealTimeStatsProps {
  refreshInterval?: number; // in seconds
  className?: string;
}

const RealTimeStats: React.FC<RealTimeStatsProps> = ({ 
  refreshInterval = 30,
  className 
}) => {
  const [stats, setStats] = useState<RealTimeStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/api/v1/pos/analytics/real-time');
      setStats(response.data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Failed to fetch real-time stats:', err);
      setError('Failed to load stats');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    
    const interval = setInterval(fetchStats, refreshInterval * 1000);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'success';
    if (rate >= 85) return 'warning';
    return 'error';
  };

  const formatLastUpdate = (): string => {
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - lastUpdate.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    return `${Math.floor(diffInSeconds / 3600)}h ago`;
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-4 ${className}`}>
        <h3 className="text-red-800 font-medium text-sm">Unable to load stats</h3>
        <p className="text-red-600 text-xs mt-1">{error}</p>
      </div>
    );
  }

  if (isLoading || !stats) {
    return (
      <div className={`grid grid-cols-2 gap-4 ${className}`}>
        {[...Array(4)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="bg-gray-200 rounded-lg h-24 w-full"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">Real-Time Stats</h3>
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-xs text-gray-500">Live</span>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <MetricCard
          title="Today's Transactions"
          value={formatNumber(stats.todayTransactions)}
          icon="📈"
          change={{
            value: `${stats.totalTransactions} total`,
            type: 'neutral'
          }}
        />
        
        <MetricCard
          title="Today's Revenue"
          value={formatCurrency(stats.todayRevenue)}
          icon="💰"
          change={{
            value: formatCurrency(stats.totalRevenue) + ' total',
            type: 'neutral'
          }}
        />
        
        <MetricCard
          title="Avg Transaction"
          value={formatCurrency(stats.averageTransactionValue)}
          icon="📊"
        />
        
        <MetricCard
          title="Success Rate"
          value={`${stats.successRate.toFixed(1)}%`}
          icon="✅"
          change={{
            value: `${stats.invoicesTransmitted}/${stats.invoicesGenerated} invoices`,
            type: stats.successRate >= 95 ? 'increase' : stats.successRate >= 85 ? 'neutral' : 'decrease'
          }}
        />
      </div>
      
      <div className="bg-gray-50 rounded-lg p-3">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div>
              <span className="text-gray-600">Peak Hour:</span>
              <span className="ml-1 font-medium">{stats.peakHour}</span>
            </div>
            <Badge variant={getSuccessRateColor(stats.successRate)}>
              {stats.successRate >= 95 ? 'Excellent' : stats.successRate >= 85 ? 'Good' : 'Needs Attention'}
            </Badge>
          </div>
          <span className="text-xs text-gray-500">
            Updated {formatLastUpdate()}
          </span>
        </div>
      </div>
    </div>
  );
};

export { RealTimeStats };