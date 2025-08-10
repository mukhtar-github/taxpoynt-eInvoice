/**
 * Transmission Queue Component
 * ============================
 * 
 * Queue management interface for FIRS document transmission pipeline.
 * Provides priority-based queue monitoring and batch processing controls.
 * 
 * Features:
 * - Priority-based queue visualization
 * - Batch processing controls
 * - Queue health monitoring
 * - Throughput optimization
 * - Manual queue management
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Badge,
  Progress,
  ScrollArea,
  Alert,
  AlertDescription,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
  Slider
} from '@/components/ui';
import { 
  Play, 
  Pause, 
  SkipForward,
  AlertTriangle,
  Settings,
  BarChart3,
  Clock,
  Zap,
  Users,
  Activity,
  TrendingUp,
  RefreshCw
} from 'lucide-react';

import { TransmissionJob, QueueConfig } from '../../types';

interface QueueStatus {
  high_priority: {
    count: number;
    limit: number;
    processing: number;
    avg_wait_time: number;
  };
  normal_priority: {
    count: number;
    limit: number;
    processing: number;
    avg_wait_time: number;
  };
  low_priority: {
    count: number;
    limit: number;
    processing: number;
    avg_wait_time: number;
  };
  total_processing: number;
  max_concurrent: number;
  throughput_per_hour: number;
}

const mockQueueStatus: QueueStatus = {
  high_priority: {
    count: 12,
    limit: 50,
    processing: 3,
    avg_wait_time: 1.2
  },
  normal_priority: {
    count: 45,
    limit: 200,
    processing: 8,
    avg_wait_time: 4.5
  },
  low_priority: {
    count: 23,
    limit: 100,
    processing: 2,
    avg_wait_time: 12.3
  },
  total_processing: 13,
  max_concurrent: 20,
  throughput_per_hour: 450
};

export const TransmissionQueue: React.FC = () => {
  const [queueStatus, setQueueStatus] = useState<QueueStatus>(mockQueueStatus);
  const [isProcessingPaused, setIsProcessingPaused] = useState(false);
  const [autoScale, setAutoScale] = useState(true);
  const [maxConcurrent, setMaxConcurrent] = useState(20);
  const [batchSize, setBatchSize] = useState(10);

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'border-red-200 bg-red-50';
      case 'normal': return 'border-blue-200 bg-blue-50';
      case 'low': return 'border-gray-200 bg-gray-50';
      default: return 'border-gray-200 bg-gray-50';
    }
  };

  const getPriorityBadgeColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800 border-red-200';
      case 'normal': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'low': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getUtilizationColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 70) return 'text-yellow-600';
    return 'text-green-600';
  };

  const handlePauseProcessing = () => {
    setIsProcessingPaused(!isProcessingPaused);
    // In real implementation, this would call API to pause/resume processing
  };

  const handlePriorityBoost = (priority: string) => {
    console.log(`Boosting ${priority} priority queue`);
    // In real implementation, this would call API to boost queue priority
  };

  const handleFlushQueue = (priority: string) => {
    console.log(`Flushing ${priority} priority queue`);
    // In real implementation, this would call API to process all items in queue
  };

  return (
    <div className="space-y-6">
      {/* Queue Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Queue Controls
            </span>
            <div className="flex items-center gap-3">
              <Button
                variant={isProcessingPaused ? "default" : "outline"}
                size="sm"
                onClick={handlePauseProcessing}
              >
                {isProcessingPaused ? (
                  <><Play className="h-4 w-4 mr-2" />Resume</>
                ) : (
                  <><Pause className="h-4 w-4 mr-2" />Pause</>
                )}
              </Button>
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Configure
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2">Max Concurrent Processing</label>
              <div className="space-y-2">
                <Slider
                  value={[maxConcurrent]}
                  onValueChange={(value) => setMaxConcurrent(value[0])}
                  max={50}
                  min={5}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-600">
                  <span>5</span>
                  <span className="font-medium">{maxConcurrent}</span>
                  <span>50</span>
                </div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium mb-2">Batch Size</label>
              <div className="space-y-2">
                <Slider
                  value={[batchSize]}
                  onValueChange={(value) => setBatchSize(value[0])}
                  max={50}
                  min={1}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-sm text-gray-600">
                  <span>1</span>
                  <span className="font-medium">{batchSize}</span>
                  <span>50</span>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">Auto-scaling</label>
                <Switch
                  checked={autoScale}
                  onCheckedChange={setAutoScale}
                />
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="text-sm font-medium text-blue-900">Current Throughput</div>
                <div className="text-lg font-bold text-blue-700">
                  {queueStatus.throughput_per_hour}/hour
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queue Status Alert */}
      {(queueStatus.high_priority.count / queueStatus.high_priority.limit) > 0.8 && (
        <Alert className="border-orange-200 bg-orange-50">
          <AlertTriangle className="h-4 w-4 text-orange-600" />
          <AlertDescription>
            High priority queue is approaching capacity ({queueStatus.high_priority.count}/{queueStatus.high_priority.limit}). 
            Consider increasing processing capacity or reviewing queue limits.
          </AlertDescription>
        </Alert>
      )}

      {/* Queue Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* High Priority Queue */}
        <Card className={getPriorityColor('high')}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="h-5 w-5 text-red-600" />
                <span>High Priority</span>
              </div>
              <Badge variant="outline" className={getPriorityBadgeColor('high')}>
                {queueStatus.high_priority.processing} active
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-red-700">
                {queueStatus.high_priority.count}
              </span>
              <span className="text-sm text-gray-600">
                / {queueStatus.high_priority.limit} limit
              </span>
            </div>
            
            <Progress 
              value={(queueStatus.high_priority.count / queueStatus.high_priority.limit) * 100} 
              className="h-2"
            />

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Avg Wait Time</span>
                <div className="font-medium">{queueStatus.high_priority.avg_wait_time}min</div>
              </div>
              <div>
                <span className="text-gray-600">Processing</span>
                <div className="font-medium">{queueStatus.high_priority.processing}</div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handlePriorityBoost('high')}
              >
                <TrendingUp className="h-3 w-3 mr-1" />
                Boost
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handleFlushQueue('high')}
              >
                <SkipForward className="h-3 w-3 mr-1" />
                Flush
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Normal Priority Queue */}
        <Card className={getPriorityColor('normal')}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                <span>Normal Priority</span>
              </div>
              <Badge variant="outline" className={getPriorityBadgeColor('normal')}>
                {queueStatus.normal_priority.processing} active
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-blue-700">
                {queueStatus.normal_priority.count}
              </span>
              <span className="text-sm text-gray-600">
                / {queueStatus.normal_priority.limit} limit
              </span>
            </div>
            
            <Progress 
              value={(queueStatus.normal_priority.count / queueStatus.normal_priority.limit) * 100} 
              className="h-2"
            />

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Avg Wait Time</span>
                <div className="font-medium">{queueStatus.normal_priority.avg_wait_time}min</div>
              </div>
              <div>
                <span className="text-gray-600">Processing</span>
                <div className="font-medium">{queueStatus.normal_priority.processing}</div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handlePriorityBoost('normal')}
              >
                <TrendingUp className="h-3 w-3 mr-1" />
                Boost
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handleFlushQueue('normal')}
              >
                <SkipForward className="h-3 w-3 mr-1" />
                Flush
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Low Priority Queue */}
        <Card className={getPriorityColor('low')}>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-gray-600" />
                <span>Low Priority</span>
              </div>
              <Badge variant="outline" className={getPriorityBadgeColor('low')}>
                {queueStatus.low_priority.processing} active
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gray-700">
                {queueStatus.low_priority.count}
              </span>
              <span className="text-sm text-gray-600">
                / {queueStatus.low_priority.limit} limit
              </span>
            </div>
            
            <Progress 
              value={(queueStatus.low_priority.count / queueStatus.low_priority.limit) * 100} 
              className="h-2"
            />

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Avg Wait Time</span>
                <div className="font-medium">{queueStatus.low_priority.avg_wait_time}min</div>
              </div>
              <div>
                <span className="text-gray-600">Processing</span>
                <div className="font-medium">{queueStatus.low_priority.processing}</div>
              </div>
            </div>

            <div className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handlePriorityBoost('low')}
              >
                <TrendingUp className="h-3 w-3 mr-1" />
                Boost
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handleFlushQueue('low')}
              >
                <SkipForward className="h-3 w-3 mr-1" />
                Flush
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Processing Capacity */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Processing Capacity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600">
                {queueStatus.total_processing}
              </div>
              <div className="text-sm text-gray-600">Currently Processing</div>
              <Progress 
                value={(queueStatus.total_processing / queueStatus.max_concurrent) * 100} 
                className="mt-2"
              />
            </div>

            <div className="text-center">
              <div className={`text-3xl font-bold ${getUtilizationColor((queueStatus.total_processing / queueStatus.max_concurrent) * 100)}`}>
                {Math.round((queueStatus.total_processing / queueStatus.max_concurrent) * 100)}%
              </div>
              <div className="text-sm text-gray-600">Capacity Utilization</div>
              <div className="mt-2 text-xs text-gray-500">
                {queueStatus.total_processing} / {queueStatus.max_concurrent} slots
              </div>
            </div>

            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">
                {queueStatus.throughput_per_hour}
              </div>
              <div className="text-sm text-gray-600">Documents/Hour</div>
              <div className="mt-2 flex items-center justify-center gap-1 text-xs text-green-600">
                <TrendingUp className="h-3 w-3" />
                <span>Optimal</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Queue Health Status */}
      <Card>
        <CardHeader>
          <CardTitle>Queue Health Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium">Queue Processing</span>
              </div>
              <Badge variant="outline" className="bg-green-100 text-green-800">
                Healthy
              </Badge>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium">Worker Threads</span>
              </div>
              <Badge variant="outline" className="bg-green-100 text-green-800">
                {queueStatus.total_processing}/{queueStatus.max_concurrent} Active
              </Badge>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                <span className="font-medium">Memory Usage</span>
              </div>
              <Badge variant="outline" className="bg-yellow-100 text-yellow-800">
                68% Utilized
              </Badge>
            </div>

            <div className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                <span className="font-medium">FIRS Connectivity</span>
              </div>
              <Badge variant="outline" className="bg-green-100 text-green-800">
                Connected
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};