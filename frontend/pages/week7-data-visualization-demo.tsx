/**
 * Week 7 Data Visualization Integration Demo
 * 
 * Showcases the complete chart library integration with:
 * - Gradient-styled charts matching design system
 * - Responsive chart containers for mobile/desktop
 * - Interactive tooltips and data points
 * - Standardized chart types across platform
 */

import React, { useState } from 'react';
import { ChartVisualizationDashboard } from '../components/ui/ChartVisualizationDashboard';
import { 
  BusinessIntelligenceDashboard,
  RevenueChart,
  PerformanceChart,
  ComplianceChart,
  IntegrationChart,
  InvoiceProcessingChart,
  ChartGrid,
  ResponsiveChartWrapper
} from '../components/ui/charts';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { 
  BarChart3, 
  LineChart, 
  PieChart, 
  TrendingUp, 
  Activity,
  Smartphone,
  Monitor,
  Tablet
} from 'lucide-react';

// Demo data
const demoRevenueData = [
  { name: 'Jan', value: 4000 },
  { name: 'Feb', value: 3000 },
  { name: 'Mar', value: 5000 },
  { name: 'Apr', value: 4500 },
  { name: 'May', value: 6000 },
  { name: 'Jun', value: 5500 }
];

const demoPerformanceData = [
  { name: 'Odoo ERP', value: 98.5 },
  { name: 'FIRS API', value: 97.2 },
  { name: 'SAP', value: 99.1 },
  { name: 'QuickBooks', value: 96.8 }
];

const demoComplianceData = {
  labels: ['Compliant', 'Pending Review', 'Non-Compliant'],
  datasets: [{
    label: 'Compliance Status',
    data: [85, 12, 3],
    backgroundColor: [
      'rgba(16, 185, 129, 0.8)',
      'rgba(245, 158, 11, 0.8)', 
      'rgba(239, 68, 68, 0.8)'
    ]
  }]
};

const Week7DataVisualizationDemo: React.FC = () => {
  const [activeView, setActiveView] = useState<'overview' | 'individual' | 'responsive'>('overview');
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
            Week 7: Data Visualization Integration
          </h1>
          <p className="text-lg text-gray-600 mb-6">
            Business Intelligence & Analytics with gradient-styled charts, responsive containers, 
            and interactive data points
          </p>

          {/* Feature highlights */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <Card className="p-4">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-blue-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Gradient Charts</h3>
                  <p className="text-sm text-gray-600">Design system colors</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <Smartphone className="w-8 h-8 text-green-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Responsive</h3>
                  <p className="text-sm text-gray-600">Mobile/Desktop</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <Activity className="w-8 h-8 text-purple-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Interactive</h3>
                  <p className="text-sm text-gray-600">Enhanced tooltips</p>
                </div>
              </div>
            </Card>
            <Card className="p-4">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-amber-500 mr-3" />
                <div>
                  <h3 className="font-semibold">Standardized</h3>
                  <p className="text-sm text-gray-600">Consistent types</p>
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
                <h2 className="text-xl font-semibold mb-4">Complete Dashboard Integration</h2>
                <ChartVisualizationDashboard />
              </Card>
            </div>
          )}

          {activeView === 'individual' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-xl font-semibold mb-4">Individual Chart Components</h2>
                <ChartGrid columns={2} gap={6}>
                  <RevenueChart 
                    data={demoRevenueData}
                    type="area"
                    title="Revenue Trends"
                    subtitle="Monthly revenue with gradient styling"
                  />
                  <PerformanceChart 
                    data={demoPerformanceData}
                    title="System Performance"
                    subtitle="Integration success rates"
                  />
                </ChartGrid>
              </div>

              <div>
                <ChartGrid columns={3} gap={6}>
                  <ComplianceChart 
                    data={demoComplianceData}
                    title="Compliance Status"
                    subtitle="Current distribution"
                  />
                  <IntegrationChart 
                    data={demoPerformanceData}
                    title="Integration Health"
                    subtitle="Connected systems"
                  />
                  <InvoiceProcessingChart 
                    data={demoRevenueData}
                    type="bar"
                    title="Invoice Processing"
                    subtitle="Monthly processing volume"
                  />
                </ChartGrid>
              </div>
            </div>
          )}

          {activeView === 'responsive' && (
            <div className="space-y-6">
              <Card className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">
                    Responsive Design Demo ({deviceView})
                  </h2>
                  <Badge variant="secondary">{deviceView}</Badge>
                </div>
                
                <div className="space-y-4">
                  <ResponsiveChartWrapper
                    title="Revenue Analytics"
                    subtitle="Optimized for current viewport"
                    minHeight={deviceView === 'mobile' ? 200 : 300}
                    maxHeight={deviceView === 'desktop' ? 400 : 300}
                  >
                    <RevenueChart 
                      data={demoRevenueData}
                      type="area"
                    />
                  </ResponsiveChartWrapper>

                  <ChartGrid 
                    columns={deviceView === 'mobile' ? 1 : deviceView === 'tablet' ? 2 : 3} 
                    gap={4}
                  >
                    <PerformanceChart 
                      data={demoPerformanceData}
                      title="Performance"
                      subtitle="Responsive layout"
                    />
                    <ComplianceChart 
                      data={demoComplianceData}
                      title="Compliance"
                      subtitle="Mobile optimized"
                    />
                    {deviceView !== 'mobile' && (
                      <IntegrationChart 
                        data={demoPerformanceData}
                        title="Integration"
                        subtitle="Multi-device"
                      />
                    )}
                  </ChartGrid>
                </div>
              </Card>
            </div>
          )}
        </div>

        {/* Implementation Details */}
        <Card className="mt-8 p-6">
          <h2 className="text-xl font-semibold mb-4">Implementation Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div>
              <h3 className="font-semibold text-green-600 mb-2">✅ Completed</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Recharts/Chart.js setup and configuration</li>
                <li>• Gradient-styled charts matching design system</li>
                <li>• Responsive chart containers for mobile/desktop</li>
                <li>• Interactive tooltips and data points</li>
                <li>• Chart type standardization across platform</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-blue-600 mb-2">🔄 Features</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Design system color integration</li>
                <li>• Mobile-first responsive design</li>
                <li>• Enhanced tooltip system</li>
                <li>• Animated chart transitions</li>
                <li>• Cross-platform compatibility</li>
              </ul>
            </div>
            <div>
              <h3 className="font-semibold text-purple-600 mb-2">📊 Chart Types</h3>
              <ul className="space-y-1 text-sm text-gray-600">
                <li>• Revenue analytics (Area/Line)</li>
                <li>• Performance monitoring (Bar)</li>
                <li>• Compliance status (Doughnut)</li>
                <li>• Integration health (Horizontal Bar)</li>
                <li>• Processing trends (Multi-type)</li>
              </ul>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Week7DataVisualizationDemo;