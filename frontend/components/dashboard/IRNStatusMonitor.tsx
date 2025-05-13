import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent
} from '../../components/ui/Card';
import { Progress } from '../../components/ui/Progress';
import { Badge } from '../../components/ui/Badge';
import { Clock, AlertCircle, CheckCircle, Activity, Loader2 } from 'lucide-react';
import { fetchIRNMetrics } from '../../services/dashboardService';

// Types for IRN status data
export type IRNStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface IRNStatusItem {
  id: string;
  invoiceNumber: string;
  status: IRNStatus;
  timestamp: string;
  businessName: string;
  errorMessage?: string;
}

interface IRNStatusSummary {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  successRate: number;
}

interface IRNStatusMonitorProps {
  recentItems?: IRNStatusItem[];
  summary?: IRNStatusSummary;
  isLoading?: boolean;
  useRealData?: boolean;
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number;
  summaryData?: any; // API response for IRN summary data
}

// Helper function to get badge color based on status
const getStatusBadge = (status: IRNStatus) => {
  switch (status) {
    case 'pending':
      return <Badge variant="outline" className="flex items-center gap-1"><Clock size={12} /> Pending</Badge>;
    case 'processing':
      return <Badge variant="secondary" className="flex items-center gap-1"><Activity size={12} /> Processing</Badge>;
    case 'completed':
      return <Badge variant="success" className="flex items-center gap-1"><CheckCircle size={12} /> Completed</Badge>;
    case 'failed':
      return <Badge variant="destructive" className="flex items-center gap-1"><AlertCircle size={12} /> Failed</Badge>;
    default:
      return <Badge variant="outline">Unknown</Badge>;
  }
};

const IRNStatusMonitor: React.FC<IRNStatusMonitorProps> = ({ 
  recentItems: propRecentItems, 
  summary: propSummary,
  isLoading: propIsLoading = false,
  useRealData = false,
  timeRange = '24h',
  organizationId,
  refreshInterval = 30000
}) => {
  // State for real-time data
  const [localRecentItems, setLocalRecentItems] = useState<IRNStatusItem[] | undefined>(propRecentItems);
  const [localSummary, setLocalSummary] = useState<IRNStatusSummary | undefined>(propSummary);
  const [loading, setLoading] = useState<boolean>(propIsLoading);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Fetch real data from API
  const fetchRealTimeData = async () => {
    if (!useRealData) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const irnMetrics = await fetchIRNMetrics(timeRange, organizationId);
      
      // Transform API data to component format
      const newSummary: IRNStatusSummary = {
        total: irnMetrics.total_count,
        pending: irnMetrics.status_counts.unused,
        processing: irnMetrics.status_counts.active,
        completed: irnMetrics.status_counts.used,
        failed: irnMetrics.status_counts.expired + irnMetrics.status_counts.cancelled,
        successRate: ((irnMetrics.status_counts.used / irnMetrics.total_count) * 100) || 0
      };
      
      setLocalSummary(newSummary);
      setLastUpdated(new Date());
      
      // We don't get recent items from the API, so we'd keep the existing ones
      // In a real implementation, you would fetch these from another endpoint
    } catch (err) {
      console.error('Error fetching IRN metrics:', err);
      setError('Failed to load IRN data');
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    // Initial fetch
    if (useRealData) {
      fetchRealTimeData();
    }
    
    // Set up polling for real-time updates
    let intervalId: NodeJS.Timeout | undefined;
    
    if (useRealData && refreshInterval > 0) {
      intervalId = setInterval(fetchRealTimeData, refreshInterval);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [useRealData, timeRange, organizationId, refreshInterval]);
  
  // Use the prop values as fallback if real data isn't available
  const displayRecentItems = localRecentItems || propRecentItems || [];
  const displaySummary = localSummary || propSummary || {
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
    successRate: 0
  };
  const isLoadingData = loading || propIsLoading;
  return (
    <Card className="shadow-sm">
      <CardHeader>
        <h2 className="text-lg font-semibold">IRN Generation Status</h2>
      </CardHeader>
      <CardContent>
        {isLoadingData ? (
          <div className="flex items-center justify-center h-40">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-40 flex-col">
            <AlertCircle className="h-8 w-8 text-destructive mb-2" />
            <p className="text-destructive">{error}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Status summary section */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-background rounded-lg p-3 shadow-sm">
                <div className="text-sm text-muted-foreground">Total</div>
                <div className="text-2xl font-semibold">{displaySummary.total}</div>
              </div>
              <div className="bg-background rounded-lg p-3 shadow-sm">
                <div className="text-sm text-muted-foreground">Success Rate</div>
                <div className="text-2xl font-semibold text-green-500">{displaySummary.successRate.toFixed(1)}%</div>
              </div>
              <div className="bg-background rounded-lg p-3 shadow-sm">
                <div className="text-sm text-muted-foreground">In Progress</div>
                <div className="text-2xl font-semibold text-amber-500">{displaySummary.pending + displaySummary.processing}</div>
              </div>
              <div className="bg-background rounded-lg p-3 shadow-sm">
                <div className="text-sm text-muted-foreground">Failed</div>
                <div className="text-2xl font-semibold text-red-500">{displaySummary.failed}</div>
              </div>
            </div>

            {/* Progress indicators */}
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Success Rate</span>
                <span className="text-green-500">{displaySummary.successRate.toFixed(1)}%</span>
              </div>
              <Progress value={displaySummary.successRate} max={100} className="h-2" />
            </div>
            <div className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>Failure Rate</span>
                <span className="text-red-500">{((displaySummary.failed / displaySummary.total) * 100).toFixed(1)}%</span>
              </div>
              <Progress value={(displaySummary.failed / displaySummary.total) * 100} max={100} variant="destructive" className="h-2" />
            </div>

            {/* Recent status items */}
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Recent Activity</h4>
              <div className="space-y-3 max-h-[300px] overflow-y-auto">
                {displayRecentItems.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-6">
                    No recent activity found
                  </div>
                ) : displayRecentItems.map(item => (
                  <div 
                    key={item.id} 
                    className="flex items-center justify-between p-3 bg-background-alt rounded-md"
                  >
                    <div>
                      <div className="font-medium">{item.invoiceNumber}</div>
                      <div className="text-sm text-muted-foreground">{item.businessName}</div>
                      {item.errorMessage && (
                        <div className="text-sm text-destructive mt-1">
                          {item.errorMessage}
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      {getStatusBadge(item.status)}
                      <span className="text-xs text-muted-foreground">{item.timestamp}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IRNStatusMonitor;
