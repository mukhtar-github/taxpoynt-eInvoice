import React from 'react';
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
  ExternalLink 
} from 'lucide-react';

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
  integrations: IntegrationItem[];
  isLoading?: boolean;
  onRefresh?: () => void;
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
  integrations, 
  isLoading = false,
  onRefresh 
}) => {
  return (
    <Card className="shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Integration Status</CardTitle>
          <CardDescription>Current status of system integrations</CardDescription>
        </div>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onRefresh}
          disabled={isLoading}
          className="flex items-center gap-1"
        >
          <RefreshCw size={14} />
          <span>Refresh</span>
        </Button>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="py-4 text-center">Loading integration status...</div>
        ) : (
          <div className="space-y-4">
            {integrations.map((integration) => (
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
            
            {integrations.length === 0 && (
              <div className="text-center py-8 text-text-secondary">
                No integrations configured
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IntegrationStatus;
