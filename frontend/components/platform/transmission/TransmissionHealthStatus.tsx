import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Button } from '../../ui/Button';
import { Loader2, AlertTriangle, ShieldAlert, Activity, ThumbsUp, AlertCircle } from 'lucide-react';
import transmissionApiService from '../../../services/transmissionApiService';
import { useToast } from '../../ui/Toast';

interface TransmissionHealthStatusProps {
  refreshInterval?: number; // in milliseconds
  onRefresh?: () => void;
}

type HealthStatus = 'healthy' | 'degraded' | 'critical' | 'unknown';

interface HealthData {
  status: HealthStatus;
  indicators: {
    error_rate: number;
    circuit_breaks: number;
    active_batches: number;
    average_processing_time_ms: number;
  };
  queues: {
    pending: number;
    in_progress: number;
    failed: number;
    retrying: number;
  };
  last_updated: string;
}

const TransmissionHealthStatus: React.FC<TransmissionHealthStatusProps> = ({ 
  refreshInterval = 30000,
  onRefresh
}) => {
  const [health, setHealth] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const toast = useToast();

  const fetchHealthData = async () => {
    try {
      setLoading(true);
      const response = await transmissionApiService.getTransmissionHealth();
      
      if (response.error) {
        setError(response.error);
        return;
      }
      
      setHealth(response.data as HealthData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch transmission health data');
      console.error('Health status fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealthData();
    
    // Set up refresh interval if specified
    if (refreshInterval > 0) {
      const intervalId = setInterval(fetchHealthData, refreshInterval);
      return () => clearInterval(intervalId);
    }
  }, [refreshInterval]);

  const handleRefresh = () => {
    fetchHealthData();
    if (onRefresh) onRefresh();
  };

  const getStatusIcon = (status: HealthStatus) => {
    switch (status) {
      case 'healthy':
        return <ThumbsUp className="h-5 w-5 text-green-500" />;
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-amber-500" />;
      case 'critical':
        return <ShieldAlert className="h-5 w-5 text-red-500" />;
      default:
        return <AlertCircle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: HealthStatus) => {
    switch (status) {
      case 'healthy':
        return <Badge className="bg-green-100 text-green-800">Healthy</Badge>;
      case 'degraded':
        return <Badge className="bg-amber-100 text-amber-800">Performance Degraded</Badge>;
      case 'critical':
        return <Badge className="bg-red-100 text-red-800">Critical Issues</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  return (
    <Card className="shadow-md border-l-4 border-l-cyan-500">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Activity className="h-5 w-5 text-cyan-600" />
            <span>Transmission System Health</span>
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={handleRefresh}
            disabled={loading}
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              'Refresh'
            )}
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading && !health ? (
          <div className="flex justify-center items-center py-4">
            <Loader2 className="h-8 w-8 text-cyan-600 animate-spin" />
          </div>
        ) : error ? (
          <div className="text-red-500 py-2 text-center">
            <AlertTriangle className="h-5 w-5 inline-block mr-2" />
            {error}
          </div>
        ) : health ? (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                {getStatusIcon(health.status)}
                <span className="font-medium">System Status:</span>
                {getStatusBadge(health.status)}
              </div>
              <div className="text-sm text-gray-500">
                Updated: {new Date(health.last_updated).toLocaleTimeString()}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-3 mt-2">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Error Rate</div>
                <div className="text-xl font-semibold">
                  {health.indicators.error_rate.toFixed(1)}%
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Circuit Breaks</div>
                <div className="text-xl font-semibold">
                  {health.indicators.circuit_breaks}
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Active Batches</div>
                <div className="text-xl font-semibold">
                  {health.indicators.active_batches}
                </div>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="text-sm text-gray-500 mb-1">Avg. Processing Time</div>
                <div className="text-xl font-semibold">
                  {health.indicators.average_processing_time_ms.toFixed(0)} ms
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="text-sm font-medium mb-2">Queue Status</h4>
              <div className="flex space-x-2 text-sm">
                <div className="bg-blue-50 text-blue-800 px-2 py-1 rounded">
                  In Progress: {health.queues.in_progress}
                </div>
                <div className="bg-amber-50 text-amber-800 px-2 py-1 rounded">
                  Pending: {health.queues.pending}
                </div>
                <div className="bg-red-50 text-red-800 px-2 py-1 rounded">
                  Failed: {health.queues.failed}
                </div>
                <div className="bg-purple-50 text-purple-800 px-2 py-1 rounded">
                  Retrying: {health.queues.retrying}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="text-gray-500 py-2 text-center">
            No health data available
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TransmissionHealthStatus;
