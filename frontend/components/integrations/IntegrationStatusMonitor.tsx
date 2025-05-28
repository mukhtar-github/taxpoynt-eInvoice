import React from 'react';
import { AlertCircle, CheckCircle, Clock, RefreshCw, AlertTriangle } from 'lucide-react';
import { formatDate } from '@/utils/dateUtils';

interface IntegrationStatusMonitorProps {
  status: string;
  lastSync?: string;
  errorMessage?: string;
  onSyncClick?: (e: React.MouseEvent) => void;
  onRetryClick?: (e: React.MouseEvent) => void;
  disableActions?: boolean;
  showDetails?: boolean;
}

const IntegrationStatusMonitor: React.FC<IntegrationStatusMonitorProps> = ({
  status,
  lastSync,
  errorMessage,
  onSyncClick,
  onRetryClick,
  disableActions = false,
  showDetails = true
}) => {
  // Status style and icon mapping
  const getStatusInfo = (status: string) => {
    switch (status.toLowerCase()) {
      case 'configured':
        return {
          bgColor: 'bg-green-100',
          textColor: 'text-green-800',
          borderColor: 'border-green-200',
          icon: <CheckCircle className="w-4 h-4 mr-1" />,
          label: 'Configured'
        };
      case 'pending':
        return {
          bgColor: 'bg-yellow-100',
          textColor: 'text-yellow-800',
          borderColor: 'border-yellow-200',
          icon: <Clock className="w-4 h-4 mr-1" />,
          label: 'Pending'
        };
      case 'error':
        return {
          bgColor: 'bg-red-100',
          textColor: 'text-red-800',
          borderColor: 'border-red-200',
          icon: <AlertCircle className="w-4 h-4 mr-1" />,
          label: 'Error'
        };
      case 'syncing':
        return {
          bgColor: 'bg-blue-100',
          textColor: 'text-blue-800',
          borderColor: 'border-blue-200',
          icon: <RefreshCw className="w-4 h-4 mr-1 animate-spin" />,
          label: 'Syncing'
        };
      case 'warning':
        return {
          bgColor: 'bg-orange-100',
          textColor: 'text-orange-800',
          borderColor: 'border-orange-200',
          icon: <AlertTriangle className="w-4 h-4 mr-1" />,
          label: 'Warning'
        };
      default:
        return {
          bgColor: 'bg-gray-100',
          textColor: 'text-gray-800',
          borderColor: 'border-gray-200',
          icon: <Clock className="w-4 h-4 mr-1" />,
          label: status || 'Unknown'
        };
    }
  };

  const statusInfo = getStatusInfo(status);

  return (
    <div className="integration-status-monitor">
      {/* Status Badge */}
      <div className="flex flex-col">
        <span
          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium capitalize ${statusInfo.bgColor} ${statusInfo.textColor} border ${statusInfo.borderColor}`}
        >
          {statusInfo.icon}
          {statusInfo.label}
        </span>

        {/* Details Section (Last Sync, Error Message) */}
        {showDetails && (
          <div className="mt-2 text-xs">
            {lastSync && (
              <div className="text-gray-500 mb-1">
                Last Sync: {formatDate(lastSync)}
              </div>
            )}
            
            {errorMessage && status === 'error' && (
              <div className="text-red-600 mt-1 mb-2">
                {errorMessage}
              </div>
            )}
          </div>
        )}

        {/* Action Buttons */}
        {(onSyncClick || onRetryClick) && (
          <div className="mt-2 flex space-x-2">
            {onSyncClick && status === 'configured' && (
              <button
                onClick={onSyncClick}
                disabled={disableActions || status === 'configured'}
                className="inline-flex items-center px-3 py-1 border border-blue-600 text-blue-700 rounded hover:bg-blue-50 text-xs font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" />
                Sync
              </button>
            )}
            
            {onRetryClick && status === 'error' && (
              <button
                onClick={onRetryClick}
                disabled={disableActions}
                className="inline-flex items-center px-3 py-1 border border-red-600 text-red-700 rounded hover:bg-red-50 text-xs font-medium transition disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1" />
                Retry
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default IntegrationStatusMonitor;
