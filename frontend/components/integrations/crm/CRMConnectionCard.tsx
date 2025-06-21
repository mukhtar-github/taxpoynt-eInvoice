/**
 * CRM Connection Status Card Component
 * 
 * Demonstrates the enhanced design system applied to CRM features:
 * - Mobile-first responsive design
 * - Micro-animations and hover effects  
 * - Status indicators with color coding
 * - Touch-friendly button sizing
 */

import React from 'react';
import { 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  Settings,
  Zap,
  Wifi,
  WifiOff
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

interface CRMConnectionCardProps {
  connection: {
    id: string;
    name: string;
    type: 'hubspot' | 'salesforce' | 'pipedrive';
    status: 'connected' | 'syncing' | 'error' | 'disconnected';
    lastSync?: string;
    dealCount?: number;
    syncErrors?: number;
  };
  onConnect?: () => void;
  onConfigure?: () => void;
  onSync?: () => void;
  className?: string;
}

const CRMConnectionCard: React.FC<CRMConnectionCardProps> = ({
  connection,
  onConnect,
  onConfigure,
  onSync,
  className = ''
}) => {
  // Status configuration with enhanced visual feedback
  const statusConfig = {
    connected: {
      icon: <CheckCircle className="w-5 h-5" />,
      color: 'success' as const,
      text: 'Connected',
      bgColor: 'bg-success/10',
      borderColor: 'success' as const
    },
    syncing: {
      icon: <Clock className="w-5 h-5 animate-spin" />,
      color: 'warning' as const,
      text: 'Syncing...',
      bgColor: 'bg-warning/10',
      borderColor: 'warning' as const
    },
    error: {
      icon: <AlertCircle className="w-5 h-5" />,
      color: 'error' as const,
      text: 'Error',
      bgColor: 'bg-error/10',
      borderColor: 'error' as const
    },
    disconnected: {
      icon: <WifiOff className="w-5 h-5" />,
      color: 'primary' as const,
      text: 'Disconnected',
      bgColor: 'bg-gray-50',
      borderColor: 'primary' as const
    }
  };

  const status = statusConfig[connection.status];
  const isConnected = connection.status === 'connected';

  // CRM platform branding
  const platformConfig = {
    hubspot: {
      name: 'HubSpot',
      color: 'bg-orange-500',
      logo: '🔶'
    },
    salesforce: {
      name: 'Salesforce',
      color: 'bg-blue-500',
      logo: '☁️'
    },
    pipedrive: {
      name: 'Pipedrive',
      color: 'bg-green-500',
      logo: '📊'
    }
  };

  const platform = platformConfig[connection.type];

  return (
    <Card
      variant="interactive"
      statusColor={status.borderColor}
      className={`${className} group`}
    >
      {/* Header with platform branding and status */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          {/* Platform logo with enhanced mobile sizing */}
          <div className={`
            w-10 h-10 xs:w-12 xs:h-12 rounded-lg ${platform.color} 
            flex items-center justify-center text-white text-lg xs:text-xl
            group-hover:scale-110 transition-transform duration-200
          `}>
            {platform.logo}
          </div>
          
          <div>
            <h3 className="font-semibold text-base xs:text-lg text-text-primary">
              {connection.name}
            </h3>
            <p className="text-sm text-text-secondary">
              {platform.name} CRM
            </p>
          </div>
        </div>

        {/* Status badge with micro-animation */}
        <Badge 
          variant={status.color} 
          className="flex items-center gap-1.5 animate-fade-in"
        >
          {status.icon}
          <span className="hidden xs:inline">{status.text}</span>
        </Badge>
      </div>

      {/* Connection metrics (responsive layout) */}
      {isConnected && (
        <div className="grid grid-cols-2 xs:grid-cols-3 gap-3 xs:gap-4 mb-4">
          <div className="text-center p-2 xs:p-3 bg-background-alt rounded-lg">
            <div className="text-lg xs:text-xl font-semibold text-text-primary">
              {connection.dealCount || 0}
            </div>
            <div className="text-xs xs:text-sm text-text-secondary">
              Deals
            </div>
          </div>
          
          <div className="text-center p-2 xs:p-3 bg-background-alt rounded-lg">
            <div className="text-lg xs:text-xl font-semibold text-text-primary">
              {connection.syncErrors || 0}
            </div>
            <div className="text-xs xs:text-sm text-text-secondary">
              Errors
            </div>
          </div>

          <div className="col-span-2 xs:col-span-1 text-center p-2 xs:p-3 bg-background-alt rounded-lg">
            <div className="text-xs xs:text-sm font-medium text-text-primary">
              Last Sync
            </div>
            <div className="text-xs text-text-secondary">
              {connection.lastSync || 'Never'}
            </div>
          </div>
        </div>
      )}

      {/* Action buttons with enhanced mobile touch targets */}
      <div className="flex flex-col xs:flex-row gap-2 xs:gap-3">
        {!isConnected ? (
          <Button
            onClick={onConnect}
            size="touch" // Using our new touch-optimized size
            className="w-full xs:w-auto"
          >
            <Zap className="w-4 h-4 mr-2" />
            Connect
          </Button>
        ) : (
          <>
            <Button
              variant="outline"
              onClick={onSync}
              size="touch"
              className="flex-1 xs:flex-none"
              disabled={connection.status === 'syncing'}
            >
              <Wifi className={`w-4 h-4 mr-2 ${
                connection.status === 'syncing' ? 'animate-pulse' : ''
              }`} />
              <span className="xs:hidden">Sync</span>
              <span className="hidden xs:inline">Sync Now</span>
            </Button>
            
            <Button
              variant="secondary"
              onClick={onConfigure}
              size="touch"
              className="flex-1 xs:flex-none"
            >
              <Settings className="w-4 h-4 mr-2" />
              <span className="xs:hidden">Setup</span>
              <span className="hidden xs:inline">Configure</span>
            </Button>
          </>
        )}
      </div>

      {/* Error details (if any) */}
      {connection.status === 'error' && connection.syncErrors && connection.syncErrors > 0 && (
        <div className="mt-3 p-3 bg-error/5 border border-error/20 rounded-lg">
          <p className="text-sm text-error font-medium">
            {connection.syncErrors} sync error{connection.syncErrors > 1 ? 's' : ''} found
          </p>
          <p className="text-xs text-text-secondary mt-1">
            Check configuration or contact support
          </p>
        </div>
      )}
    </Card>
  );
};

export default CRMConnectionCard;

// Example usage component
export const CRMConnectionGrid: React.FC<{
  connections: Array<CRMConnectionCardProps['connection']>;
  onConnect: (id: string) => void;
  onConfigure: (id: string) => void;
  onSync: (id: string) => void;
}> = ({ connections, onConnect, onConfigure, onSync }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 xs:gap-6">
    {connections.map((connection) => (
      <CRMConnectionCard
        key={connection.id}
        connection={connection}
        onConnect={() => onConnect(connection.id)}
        onConfigure={() => onConfigure(connection.id)}
        onSync={() => onSync(connection.id)}
      />
    ))}
  </div>
);