/**
 * Week 6: Activity Feed & Real-Time Dashboard Demo
 * 
 * Features demonstrated:
 * - Timeline-based activity feed with chronological display
 * - Event categorization (invoices, integrations, submissions)
 * - Real-time updates with polling integration
 * - Filtering and search capabilities
 * - Infinite scroll implementation
 * - Live data integration with backend APIs
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Select } from '@/components/ui/Select';
import ConnectedActivityFeed from '@/components/dashboard/ConnectedActivityFeed';
import { 
  Activity, 
  Clock, 
  Filter, 
  RefreshCw, 
  Zap,
  TrendingUp,
  Users,
  FileText
} from 'lucide-react';

const Week6ActivityFeedDemo = () => {
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [pollInterval, setPollInterval] = useState<number>(30000);

  const activityTypeOptions = [
    { value: 'all', label: 'All Activities' },
    { value: 'invoice_generated', label: 'Invoice Generated' },
    { value: 'integration_sync', label: 'Integration Sync' },
    { value: 'submission', label: 'FIRS Submission' },
    { value: 'user_action', label: 'User Actions' },
    { value: 'system_event', label: 'System Events' },
    { value: 'error', label: 'Errors' }
  ];

  const pollIntervalOptions = [
    { value: 10000, label: '10 seconds' },
    { value: 30000, label: '30 seconds' },
    { value: 60000, label: '1 minute' },
    { value: 300000, label: '5 minutes' }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2 text-3xl font-bold text-gray-900">
            <Activity className="w-8 h-8 text-primary" />
            Week 6: Activity Feed & Real-Time Dashboard
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Live data & user engagement with timeline-based activity feeds, real-time updates, 
            event categorization, and advanced filtering capabilities.
          </p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              Real-time updates
            </div>
            <div className="flex items-center gap-1">
              <Filter className="w-4 h-4" />
              Advanced filtering
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp className="w-4 h-4" />
              Infinite scroll
            </div>
            <div className="flex items-center gap-1">
              <Zap className="w-4 h-4" />
              Live data integration
            </div>
          </div>
        </div>

        {/* Demo Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border-primary/20">
            <CardContent className="p-6 text-center">
              <FileText className="w-8 h-8 text-primary mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Timeline Display</h3>
              <p className="text-sm text-gray-600">
                Chronological activity timeline with smooth animations and visual indicators
              </p>
            </CardContent>
          </Card>

          <Card className="border-info/20">
            <CardContent className="p-6 text-center">
              <Filter className="w-8 h-8 text-info mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Event Categorization</h3>
              <p className="text-sm text-gray-600">
                Organized by type: invoices, integrations, submissions, user actions
              </p>
            </CardContent>
          </Card>

          <Card className="border-success/20">
            <CardContent className="p-6 text-center">
              <RefreshCw className="w-8 h-8 text-success mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Real-time Updates</h3>
              <p className="text-sm text-gray-600">
                Live activity streaming with configurable polling intervals
              </p>
            </CardContent>
          </Card>

          <Card className="border-warning/20">
            <CardContent className="p-6 text-center">
              <TrendingUp className="w-8 h-8 text-warning mx-auto mb-3" />
              <h3 className="font-semibold mb-2">Infinite Scroll</h3>
              <p className="text-sm text-gray-600">
                Seamless pagination with load-more functionality and performance optimization
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Activity Feed Demo */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Activity Feed */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader className="border-b">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    <h2 className="text-xl font-semibold">Live Activity Feed</h2>
                  </div>
                  <Badge variant="success" className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    Live
                  </Badge>
                </div>
                <p className="text-gray-600">
                  Real-time activity stream with advanced filtering and categorization
                </p>
              </CardHeader>
              <CardContent className="p-0">
                <ConnectedActivityFeed
                  maxHeight="600px"
                  showFilter={true}
                  pollInterval={pollInterval}
                  pageSize={15}
                  activityType={selectedFilter === 'all' ? undefined : selectedFilter}
                />
              </CardContent>
            </Card>
          </div>

          {/* Controls & Configuration */}
          <div className="space-y-6">
            {/* Filter Controls */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Activity Filters
                </h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Activity Type
                  </label>
                  <Select
                    value={selectedFilter}
                    onValueChange={setSelectedFilter}
                    options={activityTypeOptions}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Update Interval
                  </label>
                  <Select
                    value={pollInterval.toString()}
                    onValueChange={(value) => setPollInterval(parseInt(value))}
                    options={pollIntervalOptions.map(opt => ({
                      value: opt.value.toString(),
                      label: opt.label
                    }))}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Activity Stats */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <TrendingUp className="w-5 h-5" />
                  Activity Statistics
                </h3>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-primary/5 rounded-lg">
                    <div className="text-2xl font-bold text-primary">28</div>
                    <div className="text-xs text-gray-600">Total Activities</div>
                  </div>
                  <div className="text-center p-3 bg-success/5 rounded-lg">
                    <div className="text-2xl font-bold text-success">92%</div>
                    <div className="text-xs text-gray-600">Success Rate</div>
                  </div>
                  <div className="text-center p-3 bg-info/5 rounded-lg">
                    <div className="text-2xl font-bold text-info">5</div>
                    <div className="text-xs text-gray-600">Active Integrations</div>
                  </div>
                  <div className="text-center p-3 bg-warning/5 rounded-lg">
                    <div className="text-2xl font-bold text-warning">2</div>
                    <div className="text-xs text-gray-600">Recent Errors</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Implementation Features */}
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Zap className="w-5 h-5" />
                  Implementation Features
                </h3>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full" />
                    Real-time polling integration
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full" />
                    Backend API integration
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full" />
                    Event categorization system
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full" />
                    Infinite scroll pagination
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full" />
                    Error handling & retry logic
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                    Mobile-responsive design
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Technical Implementation Notes */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Technical Implementation</h3>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-3">Backend Integration</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• ActivityService for data aggregation from audit logs</li>
                  <li>• RESTful API endpoint: <code className="bg-gray-100 px-1 rounded">/api/v1/dashboard/activities</code></li>
                  <li>• Support for filtering, pagination, and organization scoping</li>
                  <li>• Integration with transmission audit logs and IRN records</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-3">Frontend Features</h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• ConnectedActivityFeed component with real-time updates</li>
                  <li>• useApiPolling hook for configurable polling intervals</li>
                  <li>• Timeline component with smooth animations</li>
                  <li>• Error boundaries and retry mechanisms</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Week6ActivityFeedDemo;