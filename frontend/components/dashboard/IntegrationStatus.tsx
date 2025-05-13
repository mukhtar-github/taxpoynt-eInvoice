import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardHeader, 
  CardContent,
  CardTitle,
  CardDescription 
} from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Tooltip } from '../ui/Tooltip';
import { Button } from '../ui/Button';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  ExternalLink,
  Loader2 
} from 'lucide-react';
import { fetchOdooIntegrationMetrics } from '../../services/dashboardService';
import { formatDistanceToNow } from 'date-fns';

export type IntegrationStatusType = 'online' | 'offline' | 'degraded';

export interface IntegrationItem {
  id: string;
  name: string;
  description: string;
  status: IntegrationStatusType;
  lastSyncTime: string;
  errorMessage?: string;
  responseTime?: number; // in ms
}

interface IntegrationStatusProps {
  integrations?: IntegrationItem[];
  isLoading?: boolean;
  onRefresh?: () => void;
  useRealData?: boolean;
  timeRange?: string;
  organizationId?: string;
  refreshInterval?: number;
  summaryData?: any; // Added to match the prop passed from dashboard.tsx
}

// Helper to get status icon based on status
const getStatusIcon = (status: IntegrationStatusType) => {
  switch (status) {
    case 'online':
      return <CheckCircle className="text-success" size={18} />;
    case 'degraded':
      return <AlertTriangle className="text-warning" size={18} />;
    case 'offline':
      return <XCircle className="text-destructive" size={18} />;
    default:
      return null;
  }
};

// Helper to get response time indicator
const getResponseTimeIndicator = (responseTime?: number) => {
  if (!responseTime) return null;
  
  let color = 'text-success';
  if (responseTime > 1000) color = 'text-warning';
  if (responseTime > 3000) color = 'text-destructive';
  
  return (
    <Tooltip content={`Response time: ${responseTime}ms`}>
      <span className={`text-xs ${color}`}>{responseTime}ms</span>
    </Tooltip>
  );
};

const IntegrationStatus: React.FC<IntegrationStatusProps> = ({ 
  integrations: propIntegrations, 
  isLoading: propIsLoading = false,
  onRefresh,
  useRealData = false,
  timeRange = '24h',
  organizationId,
  refreshInterval = 30000
}) => {
  // State for real-time data
  const [localIntegrations, setLocalIntegrations] = useState<IntegrationItem[] | undefined>(propIntegrations);
  const [loading, setLoading] = useState<boolean>(propIsLoading);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  
  // Convert API data to component format
  const mapApiIntegrationsToComponentFormat = (apiData: any): IntegrationItem[] => {
    if (!apiData?.integration_statuses?.length) return [];
    
    return apiData.integration_statuses.map((integration: any) => {
      // Determine status based on active state and last validation success
      let status: IntegrationStatusType = 'offline';
      if (integration.is_active) {
        if (integration.last_validation_success === true) {
          status = 'online';
        } else if (integration.last_validation_success === false) {
          status = 'degraded';
        }
      }
      
      // Format last validated time
      let lastSyncTime = 'Never';
      if (integration.last_validated) {
        try {
          lastSyncTime = formatDistanceToNow(new Date(integration.last_validated), { addSuffix: true });
        } catch (e) {
          lastSyncTime = 'Unknown';
        }
      }
      
      return {
        id: integration.integration_id,
        name: integration.name,
        description: `Organization: ${integration.organization_id.substring(0, 8)}...`,
        status,
        lastSyncTime,
        errorMessage: integration.last_validation_success === false ? 'Last validation failed' : undefined
      };
    });
  };
  
  // Fetch real data from API
  const fetchRealTimeData = async () => {
    if (!useRealData) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const integrationMetrics = await fetchOdooIntegrationMetrics(timeRange, organizationId);
      const mappedIntegrations = mapApiIntegrationsToComponentFormat(integrationMetrics);
      
      setLocalIntegrations(mappedIntegrations);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching integration metrics:', err);
      setError('Failed to load integration data');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle refresh from parent or internal
  const handleRefresh = () => {
    if (useRealData) {
      fetchRealTimeData();
    } else if (onRefresh) {
      onRefresh();
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
  const displayIntegrations = localIntegrations || propIntegrations || [];
  const isLoadingData = loading || propIsLoading;
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-xl">Integration Status</CardTitle>
            <CardDescription>
              Current status of connected systems
              {useRealData && (
                <div className="text-xs text-muted-foreground mt-1">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </div>
              )}
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={loading}
          >
            <RefreshCw size={14} className={`mr-1 ${loading ? 'animate-spin' : ''}`} /> 
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {isLoadingData ? (
          <div className="flex justify-center items-center py-8">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <div className="text-center py-8 text-destructive">
            {error}
          </div>
        ) : displayIntegrations.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No integrations configured
          </div>
        ) : (
          <div className="space-y-4">
            {displayIntegrations.map((integration) => (
              <div 
                key={integration.id} 
                className="flex items-start justify-between p-4 bg-background-alt rounded-md"
              >
                <div className="flex-grow">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(integration.status)}
                    <span className="font-medium">{integration.name}</span>
                    {getResponseTimeIndicator(integration.responseTime)}
                  </div>
                  <p className="text-sm text-text-secondary mt-1">{integration.description}</p>
                  {integration.errorMessage && (
                    <div className="mt-2 p-2 bg-destructive/10 text-destructive text-sm rounded-md">
                      {integration.errorMessage}
                    </div>
                  )}
                </div>
                <div className="text-xs text-text-secondary">
                  <div className="mb-2 text-right">Last synced: {integration.lastSyncTime}</div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex items-center gap-1"
                  >
                    <span>Details</span>
                    <ExternalLink size={12} />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IntegrationStatus;
