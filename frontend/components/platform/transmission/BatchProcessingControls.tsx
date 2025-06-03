import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Slider } from '../../ui/Slider';
import { Badge } from '../../ui/Badge';
import { Checkbox } from '../../ui/Checkbox';
import { Label } from '../../ui/Label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/Select';
import { Loader2, ServerCrash, ListFilter, Settings, Play, Layers } from 'lucide-react';
import transmissionApiService from '../../../services/transmissionApiService';
import { useToast } from '../../ui/Toast';

interface BatchProcessingControlsProps {
  organizationId?: string;
  onBatchStarted?: (taskId: string) => void;
  onError?: (error: string) => void;
}

const BatchProcessingControls: React.FC<BatchProcessingControlsProps> = ({
  organizationId,
  onBatchStarted,
  onError
}) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [statusFilter, setStatusFilter] = useState<string[]>(['failed', 'pending']);
  const [batchSize, setBatchSize] = useState<number>(50);
  const [maxTransmissions, setMaxTransmissions] = useState<number>(100);
  const [maxConcurrentBatches, setMaxConcurrentBatches] = useState<number>(3);
  const [retryStrategy, setRetryStrategy] = useState<string>('exponential');
  const [prioritizeFailedChecked, setPrioritizeFailedChecked] = useState<boolean>(true);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState<boolean>(false);
  const toast = useToast();

  const statusOptions = [
    { label: 'Failed', value: 'failed' },
    { label: 'Pending', value: 'pending' },
    { label: 'Retrying', value: 'retrying' },
    { label: 'In Progress', value: 'in_progress' }
  ];

  const strategyOptions = [
    { label: 'Exponential Backoff', value: 'exponential' },
    { label: 'Linear Delay', value: 'linear' },
    { label: 'Random Jitter', value: 'random' }
  ];

  const toggleStatusFilter = (status: string) => {
    if (statusFilter.includes(status)) {
      setStatusFilter(statusFilter.filter(s => s !== status));
    } else {
      setStatusFilter([...statusFilter, status]);
    }
  };

  const handleStartBatchProcessing = async () => {
    if (statusFilter.length === 0) {
      toast({
        title: 'Status filter required',
        description: 'Please select at least one status to process',
        status: 'error'
      });
      return;
    }

    try {
      setLoading(true);
      
      const response = await transmissionApiService.batchProcessTransmissions({
        organization_id: organizationId,
        status_filter: statusFilter,
        max_transmissions: maxTransmissions,
        batch_size: batchSize,
        max_concurrent_batches: maxConcurrentBatches,
        retry_strategy: retryStrategy,
        prioritize_failed: prioritizeFailedChecked
      });
      
      if (response.error) {
        toast({
          title: 'Batch processing failed',
          description: response.error,
          status: 'error'
        });
        if (onError) onError(response.error);
        return;
      }
      
      toast({
        title: 'Batch processing started',
        description: `Task ID: ${response.data?.task_id}`,
        status: 'success'
      });
      
      if (onBatchStarted && response.data?.task_id) onBatchStarted(response.data.task_id);
      
    } catch (err) {
      console.error('Batch processing error:', err);
      const errorMessage = 'Failed to start batch processing';
      toast({
        title: 'Error',
        description: errorMessage,
        status: 'error'
      });
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="shadow-md border-l-4 border-l-cyan-500">
      <CardHeader className="pb-2">
        <div className="flex justify-between items-center">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Layers className="h-5 w-5 text-cyan-600" />
            <span>Batch Processing</span>
            <Badge variant="outline" className="ml-2 bg-cyan-50 text-cyan-800">Platform</Badge>
          </CardTitle>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
          >
            <Settings className="h-4 w-4 mr-1" />
            {showAdvancedSettings ? 'Hide' : 'Show'} Advanced
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div>
            <div className="flex items-center mb-2">
              <ListFilter className="h-4 w-4 mr-1 text-gray-500" />
              <h3 className="text-sm font-medium">Status Filter</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {statusOptions.map(option => (
                <div
                  key={option.value}
                  className={`
                    px-3 py-1.5 rounded-md cursor-pointer text-sm flex items-center space-x-1.5
                    ${statusFilter.includes(option.value) 
                      ? 'bg-cyan-100 text-cyan-800 border border-cyan-300' 
                      : 'bg-gray-100 text-gray-700 border border-gray-200'}
                  `}
                  onClick={() => toggleStatusFilter(option.value)}
                >
                  <div className="w-3 h-3 rounded-full 
                    ${option.value === 'failed' ? 'bg-red-500' : 
                      option.value === 'pending' ? 'bg-amber-500' : 
                      option.value === 'retrying' ? 'bg-purple-500' : 
                      'bg-blue-500'}"
                  />
                  <span>{option.label}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="maxTransmissions" className="text-sm font-medium flex items-center">
                <ServerCrash className="h-4 w-4 mr-1 text-gray-500" />
                Max Transmissions
              </Label>
              <div className="flex items-center space-x-2">
                <Slider
                  id="maxTransmissions"
                  value={[maxTransmissions]}
                  onValueChange={(value: React.SetStateAction<number>[]) => setMaxTransmissions(value[0])}
                  className="flex-1"
                />
                <Input 
                  type="number" 
                  value={maxTransmissions}
                  onChange={(e) => setMaxTransmissions(Number(e.target.value))}
                  className="w-16"
                  min={10}
                  max={1000}
                />
              </div>
            </div>
            
            <div>
              <Label htmlFor="retryStrategy" className="text-sm font-medium">Retry Strategy</Label>
              <Select value={retryStrategy} onValueChange={setRetryStrategy}>
                <SelectTrigger id="retryStrategy">
                  <SelectValue placeholder="Select a strategy" />
                </SelectTrigger>
                <SelectContent>
                  {strategyOptions.map(option => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Checkbox 
              id="prioritizeFailed" 
              checked={prioritizeFailedChecked}
              onCheckedChange={(checked: boolean) => setPrioritizeFailedChecked(checked as boolean)}
            />
            <Label htmlFor="prioritizeFailed" className="text-sm font-medium cursor-pointer">
              Prioritize failed transmissions
            </Label>
          </div>
          
          {showAdvancedSettings && (
            <div className="bg-gray-50 p-3 rounded-md mt-2 space-y-4">
              <h3 className="text-sm font-medium mb-2">Advanced Settings</h3>
              
              <div>
                <Label htmlFor="batchSize" className="text-sm">Batch Size</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="batchSize"
                    value={[batchSize]}
                    onValueChange={(value: React.SetStateAction<number>[]) => setBatchSize(value[0])}
                    className="flex-1"
                  />
                  <Input 
                    type="number" 
                    value={batchSize}
                    onChange={(e) => setBatchSize(Number(e.target.value))}
                    className="w-16"
                    min={10}
                    max={200}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Number of transmissions to process in each batch
                </p>
              </div>
              
              <div>
                <Label htmlFor="maxConcurrentBatches" className="text-sm">Max Concurrent Batches</Label>
                <div className="flex items-center space-x-2">
                  <Slider
                    id="maxConcurrentBatches"
                    value={[maxConcurrentBatches]}
                    onValueChange={(value: React.SetStateAction<number>[]) => setMaxConcurrentBatches(value[0])}
                    className="flex-1"
                  />
                  <Input 
                    type="number" 
                    value={maxConcurrentBatches}
                    onChange={(e) => setMaxConcurrentBatches(Number(e.target.value))}
                    className="w-16"
                    min={1}
                    max={10}
                  />
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Maximum number of batches to process concurrently
                </p>
              </div>
            </div>
          )}
          
          <div className="pt-2">
            <Button
              className="w-full"
              onClick={handleStartBatchProcessing}
              disabled={loading || statusFilter.length === 0}
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 mr-2" />
                  Start Batch Processing
                </>
              )}
            </Button>
          </div>
          
          <div className="text-xs text-gray-500 italic">
            Note: Processing large batches may take some time. You can monitor progress in the Transmission Dashboard.
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default BatchProcessingControls;
