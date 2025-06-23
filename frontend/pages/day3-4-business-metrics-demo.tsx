/**
 * Day 3-4 Business Metrics Visualization Demo
 * 
 * Comprehensive showcase of business intelligence features:
 * - Revenue trends over time (line charts)
 * - Invoice status distribution (pie/donut charts)
 * - Integration performance metrics (bar charts)
 * - FIRS submission success rates (progress indicators)
 * - Geographic distribution visualization
 */

import React, { useState } from 'react';
import { BusinessMetricsVisualization } from '../components/dashboard/BusinessMetricsVisualization';
import { RevenueTrendsChart } from '../components/dashboard/RevenueTrendsChart';
import { InvoiceStatusDistribution } from '../components/dashboard/InvoiceStatusDistribution';
import { IntegrationPerformanceMetrics } from '../components/dashboard/IntegrationPerformanceMetrics';
import { FIRSSubmissionRates } from '../components/dashboard/FIRSSubmissionRates';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { 
  BarChart3, 
  LineChart, 
  PieChart, 
  TrendingUp, 
  Activity,
  DollarSign,
  FileText,
  Target,
  Monitor,
  Smartphone,
  Tablet,
  CheckCircle2
} from 'lucide-react';

const Day34BusinessMetricsDemo: React.FC = () => {
  const [activeView, setActiveView] = useState<'overview' | 'individual' | 'responsive'>('overview');
  const [timeRange, setTimeRange] = useState<'24h' | '7d' | '30d' | '90d' | '1y'>('30d');
  const [deviceView, setDeviceView] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');

  const getDeviceClass = () => {
    switch (deviceView) {
      case 'mobile':
        return 'max-w-sm mx-auto';
      case 'tablet':
        return 'max-w-3xl mx-auto';
      default:
        return 'max-w-7xl mx-auto';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Day 3-4: Business Metrics Visualization
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Comprehensive business intelligence dashboard with revenue trends, invoice analytics, 
            integration performance, and FIRS submission monitoring
          </p>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <Card className="p-4">
              <div className="flex items-center">
                <LineChart className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Revenue Trends</h3>
                  <p className="text-sm text-gray-600">Line charts</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <PieChart className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Status Distribution</h3>
                  <p className="text-sm text-gray-600">Pie/Donut charts</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-purple-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Integration Performance</h3>
                  <p className="text-sm text-gray-600">Bar charts</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <Target className="w-8 h-8 text-amber-500 mr-3" />
                <div>
                  <h3 className="font-semibold">FIRS Success Rates</h3>
                  <p className="text-sm text-gray-600">Progress indicators</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <Activity className="w-8 h-8 text-red-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Geographic Data</h3>
                  <p className="text-sm text-gray-600">Regional analysis</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Navigation */}
          <div className="flex flex-wrap gap-4">
            <div className="flex rounded-lg border border-gray-200 p-1">
              {(['overview', 'individual', 'responsive'] as const).map((view) => (
                <button
                  key={view}
                  onClick={() => setActiveView(view)}
                  className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeView === view
                      ? 'bg-blue-500 text-white'
                      : 'text-gray-600 hover:text-gray-800'
                  }`}
                >
                  {view.charAt(0).toUpperCase() + view.slice(1)}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Time Range:</span>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value as any)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="1y">Last Year</option>
              </select>
            </div>

            {activeView === 'responsive' && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-700">Device:</span>
                <div className="flex rounded-lg border border-gray-200 p-1">
                  {([
                    { key: 'desktop', icon: Monitor },
                    { key: 'tablet', icon: Tablet },
                    { key: 'mobile', icon: Smartphone }
                  ] as const).map(({ key, icon: Icon }) => (
                    <button
                      key={key}
                      onClick={() => setDeviceView(key)}
                      className={`p-2 rounded-md transition-colors ${
                        deviceView === key
                          ? 'bg-blue-500 text-white'
                          : 'text-gray-600 hover:text-gray-800'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Content based on active view */}
        <div className={activeView === 'responsive' ? getDeviceClass() : ''}>
          {activeView === 'overview' && (
            <div className="space-y-8">
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Complete Business Metrics Dashboard</h2>
                <BusinessMetricsVisualization 
                  timeRange={timeRange}
                  refreshInterval={300000}
                />
              </Card>
            </div>
          )}

          {activeView === 'individual' && (
            <div className="space-y-8">
              <Tabs defaultValue="revenue" className="w-full">
                <TabsList className="grid grid-cols-5 w-full">
                  <TabsTrigger value="revenue" className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4" />
                    Revenue
                  </TabsTrigger>
                  <TabsTrigger value="invoices" className="flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Invoices
                  </TabsTrigger>
                  <TabsTrigger value="integrations" className="flex items-center gap-2">
                    <BarChart3 className="w-4 h-4" />
                    Integrations
                  </TabsTrigger>
                  <TabsTrigger value="firs" className="flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    FIRS
                  </TabsTrigger>
                  <TabsTrigger value="comparison" className="flex items-center gap-2">
                    <Activity className="w-4 h-4" />
                    Compare
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="revenue" className="space-y-6">
                  <h2 className="text-xl font-semibold">Revenue Trends Analysis</h2>
                  <RevenueTrendsChart 
                    timeRange={timeRange}
                    showBreakdown={true}
                    chartType="area"
                  />
                </TabsContent>

                <TabsContent value="invoices" className="space-y-6">
                  <h2 className="text-xl font-semibold">Invoice Status Distribution</h2>
                  <InvoiceStatusDistribution 
                    timeRange={timeRange}
                    showDetails={true}
                    chartType="doughnut"
                  />
                </TabsContent>

                <TabsContent value="integrations" className="space-y-6">
                  <h2 className="text-xl font-semibold">Integration Performance Metrics</h2>
                  <IntegrationPerformanceMetrics 
                    timeRange={timeRange}
                    viewType="success-rate"
                    showDetails={true}
                  />
                </TabsContent>

                <TabsContent value="firs" className="space-y-6">
                  <h2 className="text-xl font-semibold">FIRS Submission Success Rates</h2>
                  <FIRSSubmissionRates 
                    timeRange={timeRange}
                    showDetails={true}
                    realTimeUpdates={true}
                  />
                </TabsContent>

                <TabsContent value="comparison" className="space-y-6">
                  <h2 className="text-xl font-semibold">Side-by-Side Comparison</h2>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <RevenueTrendsChart 
                      timeRange={timeRange}
                      showBreakdown={false}
                      chartType="line"
                    />
                    <InvoiceStatusDistribution 
                      timeRange={timeRange}
                      showDetails={false}
                      chartType="pie"
                    />
                  </div>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <IntegrationPerformanceMetrics 
                      timeRange={timeRange}
                      viewType="response-time"
                      showDetails={false}
                    />
                    <FIRSSubmissionRates 
                      timeRange={timeRange}
                      showDetails={false}
                      realTimeUpdates={false}
                    />
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          )}

          {activeView === 'responsive' && (
            <div className="space-y-6">
              <Card className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">
                    Responsive Business Metrics ({deviceView})
                  </h2>
                  <Badge variant="secondary">{deviceView}</Badge>
                </div>
                
                <div className="space-y-6">
                  {deviceView === 'mobile' ? (
                    // Mobile-optimized single column layout
                    <div className="space-y-4">
                      <RevenueTrendsChart 
                        timeRange={timeRange}
                        showBreakdown={false}
                        chartType="area"
                      />
                      <InvoiceStatusDistribution 
                        timeRange={timeRange}
                        showDetails={false}
                        chartType="doughnut"
                      />
                      <FIRSSubmissionRates 
                        timeRange={timeRange}
                        showDetails={false}
                        realTimeUpdates={true}
                      />
                    </div>
                  ) : deviceView === 'tablet' ? (
                    // Tablet-optimized two column layout
                    <div className="space-y-6">
                      <RevenueTrendsChart 
                        timeRange={timeRange}
                        showBreakdown={true}
                        chartType="area"
                      />
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <InvoiceStatusDistribution 
                          timeRange={timeRange}
                          showDetails={true}
                          chartType="doughnut"
                        />
                        <FIRSSubmissionRates 
                          timeRange={timeRange}
                          showDetails={false}
                          realTimeUpdates={true}
                        />
                      </div>
                    </div>
                  ) : (
                    // Desktop full layout
                    <BusinessMetricsVisualization 
                      timeRange={timeRange}
                      refreshInterval={300000}
                    />
                  )}
                </div>
              </Card>
            </div>
          )}
        </div>

        {/* Implementation Summary */}
        <Card className="mt-8 p-6">
          <h2 className="text-xl font-semibold mb-4">Day 3-4 Implementation Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                ✅ Revenue Trends
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Interactive line charts with time range selection</li>
                <li>• Revenue breakdown by source (invoices, fees, subscriptions)</li>
                <li>• Growth trend analysis with percentage changes</li>
                <li>• Export and real-time refresh capabilities</li>
                <li>• Mobile-responsive design with adaptive layouts</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                ✅ Invoice Status Distribution
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Pie and doughnut charts for status visualization</li>
                <li>• Detailed breakdown with percentages and counts</li>
                <li>• Status descriptions and error categorization</li>
                <li>• Interactive legends and tooltips</li>
                <li>• Real-time updates with success rate tracking</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                ✅ Integration Performance
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Bar charts for success rates and response times</li>
                <li>• Multi-metric view (success rate, volume, uptime)</li>
                <li>• Health status indicators and alerts</li>
                <li>• Integration type categorization (ERP, CRM, POS, API)</li>
                <li>• Detailed performance breakdown per integration</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                ✅ FIRS Submission Rates
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Progress indicators for submission pipeline stages</li>
                <li>• Real-time success rate monitoring</li>
                <li>• Error analysis and categorization</li>
                <li>• Performance insights and recommendations</li>
                <li>• Processing time and reliability metrics</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-green-600 mb-2 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                ✅ Geographic Distribution
              </h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Regional breakdown of invoice processing</li>
                <li>• Revenue distribution by geographic location</li>
                <li>• Success rates per region visualization</li>
                <li>• Responsive grid layout for regional data</li>
                <li>• Color-coded performance indicators</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-600 mb-2">🎯 Key Features</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Gradient-styled charts matching design system</li>
                <li>• Interactive tooltips with contextual data</li>
                <li>• Responsive layouts for all screen sizes</li>
                <li>• Real-time updates and refresh capabilities</li>
                <li>• Export functionality for all visualizations</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Day34BusinessMetricsDemo;