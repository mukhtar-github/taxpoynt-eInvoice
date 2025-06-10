import React from 'react';
import { BarChart4, Clock, Database, RefreshCw, TrendingUp } from 'lucide-react';

import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Progress } from '../../ui/Progress';

// Define the performance data structure
interface PerformanceMetrics {
  generation: {
    total: number;
    avg_time: number;
    min_time: number;
    max_time: number;
    operations_per_minute: number;
  };
  cache: {
    hit_rate: number;
    hits: number;
    misses: number;
    entries: number;
    memory_usage: number;
  };
  verification: {
    total: number;
    success_rate: number;
    avg_time: number;
  };
}

interface SignaturePerformanceMonitorProps {
  metrics: PerformanceMetrics;
  isLoading: boolean;
  onRefresh: () => void;
}

/**
 * Component for monitoring signature performance metrics
 * 
 * Displays detailed statistics about signature generation,
 * verification, and caching with visual indicators and trends.
 */
const SignaturePerformanceMonitor: React.FC<SignaturePerformanceMonitorProps> = ({
  metrics,
  isLoading,
  onRefresh
}) => {
  return (
    <div className="space-y-6">
      {/* Generation Performance */}
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-cyan-600" />
              Signature Generation Performance
            </CardTitle>
            <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
              APP
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total Signatures */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-500 mb-1">Total Signatures</div>
              <div className="text-2xl font-bold">
                {isLoading ? '...' : metrics.generation.total.toLocaleString()}
              </div>
            </div>
            
            {/* Operations Per Minute */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-500 mb-1">Operations/min</div>
              <div className="text-2xl font-bold">
                {isLoading ? '...' : metrics.generation.operations_per_minute.toLocaleString()}
              </div>
            </div>
            
            {/* Average Time */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-500 mb-1">Average Time</div>
              <div className="text-2xl font-bold">
                {isLoading ? '...' : `${metrics.generation.avg_time.toFixed(2)}ms`}
              </div>
            </div>
          </div>
          
          <div className="mt-4 space-y-3">
            {/* Time Range */}
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span>Response Time Range</span>
                <span>
                  {isLoading 
                    ? '...' 
                    : `${metrics.generation.min_time.toFixed(2)}ms - ${metrics.generation.max_time.toFixed(2)}ms`}
                </span>
              </div>
              <div className="h-2 rounded-full bg-gray-100 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-400 to-cyan-600"
                  style={{ width: `${Math.min(100, metrics.generation.avg_time / 10)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Cache Performance */}
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4 text-cyan-600" />
              Signature Cache Performance
            </CardTitle>
            <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
              APP
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Hit Rate */}
            <div>
              <div className="flex justify-between mb-1">
                <div className="text-sm text-gray-500">Cache Hit Rate</div>
                <div className="text-sm font-medium">
                  {isLoading ? '...' : `${(metrics.cache.hit_rate * 100).toFixed(1)}%`}
                </div>
              </div>
              <Progress
                value={isLoading ? 0 : metrics.cache.hit_rate * 100}
                className="h-2"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>Hits: {isLoading ? '...' : metrics.cache.hits.toLocaleString()}</span>
                <span>Misses: {isLoading ? '...' : metrics.cache.misses.toLocaleString()}</span>
              </div>
            </div>
            
            {/* Entries */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="flex justify-between">
                <div className="text-sm text-gray-500">Cache Entries</div>
                <div className="text-sm">
                  {isLoading ? '...' : metrics.cache.entries.toLocaleString()}
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                Memory Usage: {isLoading ? '...' : `${(metrics.cache.memory_usage / 1024).toFixed(2)} KB`}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      
      {/* Verification Performance */}
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-cyan-600" />
              Verification Performance
            </CardTitle>
            <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
              APP
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-2">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Success Rate */}
            <div>
              <div className="flex justify-between mb-1">
                <div className="text-sm text-gray-500">Success Rate</div>
                <div className="text-sm font-medium">
                  {isLoading ? '...' : `${(metrics.verification.success_rate * 100).toFixed(1)}%`}
                </div>
              </div>
              <Progress
                value={isLoading ? 0 : metrics.verification.success_rate * 100}
                className="h-2"
              />
            </div>
            
            {/* Total Verifications */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-500 mb-1">Total Verifications</div>
              <div className="text-xl font-bold">
                {isLoading ? '...' : metrics.verification.total.toLocaleString()}
              </div>
            </div>
            
            {/* Average Time */}
            <div className="bg-gray-50 p-3 rounded-md">
              <div className="text-sm text-gray-500 mb-1">Average Time</div>
              <div className="text-xl font-bold">
                {isLoading ? '...' : `${metrics.verification.avg_time.toFixed(2)}ms`}
              </div>
            </div>
          </div>
        </CardContent>
        <CardFooter className="border-t pt-4">
          <div className="flex items-center text-xs text-gray-500">
            <RefreshCw className="h-3 w-3 mr-1" />
            Last updated: {new Date().toLocaleTimeString()}
          </div>
        </CardFooter>
      </Card>
    </div>
  );
};

export default SignaturePerformanceMonitor;
