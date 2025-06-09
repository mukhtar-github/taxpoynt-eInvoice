import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  RefreshCw, 
  ArrowRight, 
  AlertTriangle 
} from 'lucide-react';
import { isFeatureEnabled } from '../../config/featureFlags';
import transmissionApiService, { TransmissionListItem } from '../../services/transmissionApiService';
import { cn } from '../../utils/cn';

interface TransmissionStatusVisualizationProps {
  organizationId: string;
  className?: string;
  limit?: number;
}

/**
 * Transmission Status Visualization Component
 * 
 * Displays a visual representation of recent transmission statuses
 * with color-coded indicators and basic metrics
 */
const TransmissionStatusVisualization: React.FC<TransmissionStatusVisualizationProps> = ({
  organizationId,
  className = '',
  limit = 5
}) => {
  const [transmissions, setTransmissions] = useState<TransmissionListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Only render if Platform transmission features are enabled
  if (!isFeatureEnabled('APP_UI_ELEMENTS')) {
    return null;
  }
  
  useEffect(() => {
    const fetchTransmissions = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await transmissionApiService.listTransmissions(
          organizationId,
          undefined, // certificate ID
          undefined, // submission ID
          undefined, // status
          0, // skip
          limit // show limited transmissions
        );
        
        // The response directly contains data and total properties
        setTransmissions(response.data || []);
      } catch (err: any) {
        console.error('Error fetching transmissions:', err);
        setError(err.message || 'Failed to load transmission data');
      } finally {
        setLoading(false);
      }
    };
    
    fetchTransmissions();
  }, [organizationId, limit]);
  
  // Calculate success rate
  const successCount = transmissions.filter(t => t.status === 'completed').length;
  const pendingCount = transmissions.filter(t => ['pending', 'processing'].includes(t.status)).length;
  const failedCount = transmissions.filter(t => ['failed', 'error'].includes(t.status)).length;
  
  const successRate = transmissions.length > 0 
    ? Math.round((successCount / transmissions.length) * 100) 
    : 0;
  
  // Get status badge style
  const getStatusBadge = (status: string) => {
    switch(status.toLowerCase()) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Completed</Badge>;
      case 'pending':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Pending</Badge>;
      case 'processing':
        return <Badge className="bg-indigo-100 text-indigo-800 border-indigo-200">Processing</Badge>;
      case 'failed':
      case 'error':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Failed</Badge>;
      case 'retrying':
        return <Badge className="bg-amber-100 text-amber-800 border-amber-200">Retrying</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800 border-gray-200">{status}</Badge>;
    }
  };
  
  // Format date
  const formatDate = (dateInput: string | Date | number) => {
    if (!dateInput) return 'N/A';
    const date = typeof dateInput === 'string' || typeof dateInput === 'number' 
      ? new Date(dateInput) 
      : dateInput;
    return date.toLocaleString();
  };
  
  if (loading) {
    return (
      <Card className={cn('border-l-4 border-cyan-500', className)}>
        <CardContent className="p-6">
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex items-center">
                  <div className="h-3 bg-gray-200 rounded-full w-6 mr-3"></div>
                  <div className="h-3 bg-gray-200 rounded w-full"></div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className={cn('border-l-4 border-red-500 bg-red-50', className)}>
        <CardContent className="p-6">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">Error loading transmission data: {error}</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  if (transmissions.length === 0) {
    return (
      <Card className={cn('border-l-4 border-cyan-500 bg-cyan-50', className)}>
        <CardContent className="p-6">
          <div className="flex items-center mb-2">
            <Clock className="h-5 w-5 text-cyan-600 mr-2" />
            <span className="font-medium text-cyan-800">No Recent Transmissions</span>
          </div>
          <p className="text-sm text-cyan-700">
            There are no recent transmissions to display. New transmissions will appear here once processed.
          </p>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className={cn('border-l-4 border-cyan-500', className)}>
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg">Transmission Status</CardTitle>
          <Link href="/dashboard/transmission" passHref>
            <Button variant="ghost" size="sm" className="text-cyan-600 flex items-center">
              <span>View All</span>
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {/* Transmission Stats */}
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="bg-green-50 p-3 rounded-md">
            <div className="flex items-center">
              <CheckCircle className="h-4 w-4 text-green-500 mr-2" />
              <span className="text-xs text-green-700">Completed</span>
            </div>
            <div className="mt-1 font-semibold text-lg">{successCount}</div>
          </div>
          <div className="bg-blue-50 p-3 rounded-md">
            <div className="flex items-center">
              <Clock className="h-4 w-4 text-blue-500 mr-2" />
              <span className="text-xs text-blue-700">Pending</span>
            </div>
            <div className="mt-1 font-semibold text-lg">{pendingCount}</div>
          </div>
          <div className="bg-red-50 p-3 rounded-md">
            <div className="flex items-center">
              <XCircle className="h-4 w-4 text-red-500 mr-2" />
              <span className="text-xs text-red-700">Failed</span>
            </div>
            <div className="mt-1 font-semibold text-lg">{failedCount}</div>
          </div>
        </div>
        
        {/* Success Rate Indicator */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm">Success Rate</span>
            <span className="text-sm font-medium">{successRate}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={cn(
                "h-2 rounded-full",
                successRate >= 90 ? "bg-green-500" : 
                successRate >= 70 ? "bg-amber-500" : "bg-red-500"
              )}
              style={{ width: `${successRate}%` }}
            ></div>
          </div>
        </div>
        
        {/* Recent Transmissions List */}
        <div className="mt-4">
          <h4 className="text-sm font-medium mb-2">Recent Transmissions</h4>
          <div className="space-y-2">
            {transmissions.map(transmission => (
              <Link 
                href={`/dashboard/transmission/${transmission.id}`} 
                key={transmission.id}
                className="block"
              >
                <div className="border border-gray-200 rounded-md p-3 hover:bg-gray-50 transition-colors">
                  <div className="flex justify-between items-center">
                    <div className="truncate flex-1">
                      <span className="text-sm font-medium">
                        {transmission.reference_id || transmission.id.substring(0, 8)}
                      </span>
                    </div>
                    <div>
                      {getStatusBadge(transmission.status)}
                    </div>
                  </div>
                  <div className="flex justify-between items-center mt-1">
                    <span className="text-xs text-gray-500">
                      {formatDate(transmission.created_at)}
                    </span>
                    {transmission.status === 'failed' && (
                      <span className="text-xs text-red-600 flex items-center">
                        <RefreshCw className="h-3 w-3 mr-1" />
                        Retry
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TransmissionStatusVisualization;
