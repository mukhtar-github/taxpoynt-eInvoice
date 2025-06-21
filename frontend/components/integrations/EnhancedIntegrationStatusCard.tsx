/**
 * Enhanced Integration Status Card Component
 * 
 * Week 3 Implementation: Enhanced integration cards with:
 * - Multiple connection states (connected, syncing, error, setup)
 * - Real-time status updates with micro-animations
 * - Mobile-first responsive design
 * - Touch-friendly interactions
 * - Loading states and progress indicators
 */

import React, { useState } from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Settings,
  Zap,
  Wifi,
  WifiOff,
  RefreshCw,
  Activity,
  AlertTriangle,
  Database,
  Users,
  FileText,
  TrendingUp,
  ExternalLink,
  MoreVertical
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export interface IntegrationMetrics {
  totalRecords?: number;
  syncedToday?: number;
  lastSyncDuration?: string;
  avgResponseTime?: string;
  successRate?: number;
  errorCount?: number;
}

export interface IntegrationStatusCardProps {
  integration: {
    id: string;
    name: string;
    type: 'erp' | 'crm' | 'pos';
    platform: 'odoo' | 'hubspot' | 'salesforce' | 'pipedrive' | 'square' | 'toast' | 'lightspeed';
    status: 'connected' | 'syncing' | 'error' | 'setup' | 'disconnected' | 'warning';
    lastSync?: string;
    nextSync?: string;
    isRealtime?: boolean;
    metrics?: IntegrationMetrics;
  };
  onConnect?: () => void;
  onConfigure?: () => void;
  onSync?: () => void;
  onDisconnect?: () => void;
  onViewDetails?: () => void;
  isLoading?: boolean;
  className?: string;
}

const EnhancedIntegrationStatusCard: React.FC<IntegrationStatusCardProps> = ({
  integration,
  onConnect,
  onConfigure,
  onSync,
  onDisconnect,
  onViewDetails,
  isLoading = false,
  className = ''
}) => {
  const [showMetrics, setShowMetrics] = useState(false);

  // Enhanced status configuration with animations
  const statusConfig = {
    connected: {
      icon: <CheckCircle className="w-5 h-5" />,
      color: 'success' as const,
      label: 'Connected',
      bgColor: 'bg-success/10 border-success/20',
      description: 'Integration is active and syncing',
      pulse: false
    },
    syncing: {
      icon: <RefreshCw className="w-5 h-5 animate-spin" />,
      color: 'primary' as const,
      label: 'Syncing',
      bgColor: 'bg-primary/10 border-primary/20',
      description: 'Currently synchronizing data',
      pulse: true
    },
    error: {
      icon: <AlertCircle className="w-5 h-5" />,
      color: 'error' as const,
      label: 'Error',
      bgColor: 'bg-error/10 border-error/20',
      description: 'Integration needs attention',
      pulse: false
    },
    warning: {
      icon: <AlertTriangle className="w-5 h-5" />,
      color: 'warning' as const,
      label: 'Warning',
      bgColor: 'bg-warning/10 border-warning/20',
      description: 'Minor issues detected',
      pulse: false
    },
    setup: {
      icon: <Clock className="w-5 h-5" />,
      color: 'secondary' as const,
      label: 'Setup Required',
      bgColor: 'bg-secondary/10 border-secondary/20',
      description: 'Configuration incomplete',
      pulse: false
    },
    disconnected: {
      icon: <WifiOff className="w-5 h-5" />,
      color: 'secondary' as const,
      label: 'Disconnected',
      bgColor: 'bg-gray-50 border-gray-200',
      description: 'Not connected',
      pulse: false
    }
  };

  // Platform configuration with enhanced branding
  const platformConfig = {
    odoo: { name: 'Odoo', logo: '🏢', color: 'bg-purple-500' },
    hubspot: { name: 'HubSpot', logo: '🧡', color: 'bg-orange-500' },
    salesforce: { name: 'Salesforce', logo: '☁️', color: 'bg-blue-500' },
    pipedrive: { name: 'Pipedrive', logo: '📊', color: 'bg-green-500' },
    square: { name: 'Square', logo: '⬜', color: 'bg-black' },
    toast: { name: 'Toast', logo: '🍞', color: 'bg-red-500' },
    lightspeed: { name: 'Lightspeed', logo: '⚡', color: 'bg-blue-600' }
  };

  const typeConfig = {
    erp: { name: 'ERP System', icon: <Database className="w-4 h-4" /> },
    crm: { name: 'CRM System', icon: <Users className="w-4 h-4" /> },
    pos: { name: 'POS System', icon: <FileText className="w-4 h-4" /> }
  };

  const status = statusConfig[integration.status];
  const platform = platformConfig[integration.platform];
  const type = typeConfig[integration.type];
  const isConnected = integration.status === 'connected';
  const canSync = isConnected && integration.status !== 'syncing';

  return (
    <Card
      variant="interactive"
      statusColor={status.color}
      className={`${className} group relative overflow-hidden ${
        status.pulse ? 'animate-pulse-border' : ''
      }`}
    >
      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center z-10">
          <RefreshCw className="w-6 h-6 animate-spin text-primary" />
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Platform logo with enhanced hover effect */}
          <div className={`
            w-12 h-12 rounded-xl ${platform.color} 
            flex items-center justify-center text-white text-xl
            group-hover:scale-110 group-hover:rotate-3 
            transition-all duration-200 shadow-lg
          `}>
            {platform.logo}
          </div>
          
          <div>
            <h3 className="font-semibold text-lg text-text-primary flex items-center gap-2">
              {integration.name}
              {integration.isRealtime && (
                <Activity className="w-4 h-4 text-success animate-pulse" />
              )}
            </h3>
            <div className="flex items-center gap-2 text-sm text-text-secondary">
              {type.icon}
              <span>{platform.name} {type.name}</span>
            </div>
          </div>
        </div>

        {/* Status badge with enhanced styling */}
        <div className="flex items-center gap-2">
          <Badge 
            variant={status.color} 
            className={`flex items-center gap-1.5 ${
              status.pulse ? 'animate-pulse' : ''
            }`}
          >
            {status.icon}
            <span className="hidden sm:inline">{status.label}</span>
          </Badge>
          
          {/* More options button */}
          <Button
            variant="ghost"
            size="sm"
            className="opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={onViewDetails}
          >
            <MoreVertical className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Status description */}
      <p className="text-sm text-text-secondary mb-4">
        {status.description}
      </p>

      {/* Connection metrics (enhanced responsive layout) */}
      {isConnected && integration.metrics && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-text-primary">Metrics</span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowMetrics(!showMetrics)}
              className="text-xs"
            >
              {showMetrics ? 'Hide' : 'Show'} Details
            </Button>
          </div>
          
          <div className={`grid transition-all duration-200 ${
            showMetrics ? 'grid-cols-2 lg:grid-cols-4 gap-3' : 'grid-cols-3 gap-2'
          }`}>
            <div className="text-center p-3 bg-background-alt rounded-lg">
              <div className="text-xl font-semibold text-text-primary">
                {integration.metrics.totalRecords?.toLocaleString() || 0}
              </div>
              <div className="text-xs text-text-secondary">Total Records</div>
            </div>
            
            <div className="text-center p-3 bg-background-alt rounded-lg">
              <div className="text-xl font-semibold text-success">
                {integration.metrics.syncedToday || 0}
              </div>
              <div className="text-xs text-text-secondary">Synced Today</div>
            </div>

            <div className="text-center p-3 bg-background-alt rounded-lg">
              <div className="text-xl font-semibold text-text-primary">
                {integration.metrics.successRate || 0}%
              </div>
              <div className="text-xs text-text-secondary">Success Rate</div>
            </div>

            {showMetrics && (
              <div className="text-center p-3 bg-background-alt rounded-lg">
                <div className="text-xl font-semibold text-warning">
                  {integration.metrics.errorCount || 0}
                </div>
                <div className="text-xs text-text-secondary">Errors</div>
              </div>
            )}
          </div>

          {showMetrics && (
            <div className="mt-3 grid grid-cols-2 gap-3 text-xs text-text-secondary">
              <div>
                <span className="font-medium">Last Sync:</span> {integration.metrics.lastSyncDuration || 'N/A'}
              </div>
              <div>
                <span className="font-medium">Avg Response:</span> {integration.metrics.avgResponseTime || 'N/A'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sync information */}
      {isConnected && (
        <div className="mb-4 p-3 bg-background-alt rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <div>
              <span className="text-text-secondary">Last sync:</span>
              <span className="ml-2 text-text-primary">{integration.lastSync || 'Never'}</span>
            </div>
            {integration.isRealtime && (
              <Badge variant="success" className="text-xs">
                Real-time
              </Badge>
            )}
          </div>
          
          {integration.nextSync && !integration.isRealtime && (
            <div className="mt-1 text-xs text-text-secondary">
              Next sync: {integration.nextSync}
            </div>
          )}
        </div>
      )}

      {/* Action buttons with enhanced mobile experience */}
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3">
        {integration.status === 'disconnected' || integration.status === 'setup' ? (
          <Button
            onClick={onConnect}
            size="touch"
            className="w-full sm:w-auto flex items-center justify-center gap-2"
            disabled={isLoading}
          >
            <Zap className="w-4 h-4" />
            {integration.status === 'setup' ? 'Complete Setup' : 'Connect'}
          </Button>
        ) : (
          <>
            {canSync && (
              <Button
                variant="outline"
                onClick={onSync}
                size="touch"
                className="flex-1 sm:flex-none flex items-center justify-center gap-2"
                disabled={!canSync || isLoading}
              >
                <Wifi className="w-4 h-4" />
                <span className="sm:hidden">Sync</span>
                <span className="hidden sm:inline">Sync Now</span>
              </Button>
            )}
            
            <Button
              variant="secondary"
              onClick={onConfigure}
              size="touch"
              className="flex-1 sm:flex-none flex items-center justify-center gap-2"
              disabled={isLoading}
            >
              <Settings className="w-4 h-4" />
              <span className="sm:hidden">Setup</span>
              <span className="hidden sm:inline">Configure</span>
            </Button>

            {onViewDetails && (
              <Button
                variant="ghost"
                onClick={onViewDetails}
                size="touch"
                className="flex-1 sm:flex-none flex items-center justify-center gap-2"
              >
                <ExternalLink className="w-4 h-4" />
                <span className="sm:hidden">View</span>
                <span className="hidden sm:inline">View Details</span>
              </Button>
            )}
          </>
        )}
      </div>

      {/* Error/Warning details */}
      {(integration.status === 'error' || integration.status === 'warning') && integration.metrics?.errorCount && (
        <div className={`mt-4 p-3 rounded-lg border ${
          integration.status === 'error' 
            ? 'bg-error/5 border-error/20' 
            : 'bg-warning/5 border-warning/20'
        }`}>
          <div className="flex items-center gap-2 mb-1">
            {integration.status === 'error' ? (
              <AlertCircle className="w-4 h-4 text-error" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-warning" />
            )}
            <p className={`text-sm font-medium ${
              integration.status === 'error' ? 'text-error' : 'text-warning'
            }`}>
              {integration.metrics.errorCount} issue{integration.metrics.errorCount > 1 ? 's' : ''} found
            </p>
          </div>
          <p className="text-xs text-text-secondary">
            {integration.status === 'error' 
              ? 'Integration requires immediate attention'
              : 'Minor issues detected, sync may be affected'
            }
          </p>
        </div>
      )}

      {/* Real-time indicator */}
      {integration.isRealtime && isConnected && (
        <div className="absolute top-2 right-2 w-2 h-2 bg-success rounded-full animate-pulse"></div>
      )}
    </Card>
  );
};

export default EnhancedIntegrationStatusCard;

// Enhanced grid layout component
export const IntegrationStatusGrid: React.FC<{
  integrations: Array<IntegrationStatusCardProps['integration']>;
  onConnect: (id: string) => void;
  onConfigure: (id: string) => void;
  onSync: (id: string) => void;
  onViewDetails?: (id: string) => void;
  isLoading?: boolean;
  className?: string;
}> = ({ 
  integrations, 
  onConnect, 
  onConfigure, 
  onSync, 
  onViewDetails,
  isLoading = false,
  className = ''
}) => (
  <div className={`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 sm:gap-6 ${className}`}>
    {integrations.map((integration) => (
      <EnhancedIntegrationStatusCard
        key={integration.id}
        integration={integration}
        onConnect={() => onConnect(integration.id)}
        onConfigure={() => onConfigure(integration.id)}
        onSync={() => onSync(integration.id)}
        onViewDetails={onViewDetails ? () => onViewDetails(integration.id) : undefined}
        isLoading={isLoading}
      />
    ))}
  </div>
);

// Export types for use in other components
export type { IntegrationMetrics };