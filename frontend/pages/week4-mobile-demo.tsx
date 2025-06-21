/**
 * Week 4: Mobile Optimization & Polish Demo Page
 * 
 * Showcases all Week 4 enhancements:
 * - Enhanced responsive breakpoints
 * - Touch-first interactions
 * - Mobile-optimized data tables
 * - Pull-to-refresh functionality
 * - Micro-interactions and hover states
 * - Advanced mobile components
 */

import React, { useState } from 'react';
import { NextPage } from 'next';
import { 
  TrendingUp, 
  FileText, 
  Users, 
  Download,
  Eye,
  Edit,
  Trash2,
  Star,
  Heart,
  Share,
  Plus
} from 'lucide-react';
import AppDashboardLayout from '../components/layouts/AppDashboardLayout';
import { 
  ResponsiveContainer, 
  ResponsiveGrid, 
  ResponsiveText,
  ResponsiveShow,
  useBreakpoint,
  useDeviceDetection 
} from '../components/ui/ResponsiveUtilities';
import {
  SwipeGesture,
  SwipeableCard,
  PullToRefresh,
  LongPress,
  TouchActionButton,
  FloatingActionButton
} from '../components/ui/TouchInteractions';
import MobileDataTable from '../components/ui/MobileDataTable';
import {
  InteractiveButton,
  AnimatedCounter,
  AnimatedProgress,
  NotificationToast,
  Expandable,
  FloatingLabelInput,
  QuantitySelector
} from '../components/ui/MicroInteractions';
import { EnhancedMetricCard, MetricCardGrid } from '../components/dashboard/EnhancedMetricCard';

// Sample data for demonstrations
const sampleInvoices = [
  {
    id: 'INV-001',
    customer: 'Acme Corp',
    amount: 25000,
    status: 'paid',
    date: '2025-06-20',
    type: 'B2B'
  },
  {
    id: 'INV-002',
    customer: 'Beta Industries',
    amount: 18500,
    status: 'pending',
    date: '2025-06-19',
    type: 'B2C'
  },
  {
    id: 'INV-003',
    customer: 'Gamma Solutions',
    amount: 32000,
    status: 'overdue',
    date: '2025-06-18',
    type: 'B2B'
  },
  {
    id: 'INV-004',
    customer: 'Delta Services',
    amount: 12750,
    status: 'paid',
    date: '2025-06-17',
    type: 'B2C'
  },
  {
    id: 'INV-005',
    customer: 'Epsilon Technologies',
    amount: 45000,
    status: 'pending',
    date: '2025-06-16',
    type: 'B2B'
  }
];

const tableColumns = [
  {
    id: 'id',
    header: 'Invoice ID',
    accessor: 'id' as keyof typeof sampleInvoices[0],
    priority: 'high' as const,
    mobileLabel: 'Invoice'
  },
  {
    id: 'customer',
    header: 'Customer',
    accessor: 'customer' as keyof typeof sampleInvoices[0],
    priority: 'high' as const
  },
  {
    id: 'amount',
    header: 'Amount',
    accessor: (row: typeof sampleInvoices[0]) => `₦${row.amount.toLocaleString()}`,
    priority: 'high' as const,
    align: 'right' as const
  },
  {
    id: 'status',
    header: 'Status',
    accessor: (row: typeof sampleInvoices[0]) => (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
        row.status === 'paid' ? 'bg-green-100 text-green-800' :
        row.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
        'bg-red-100 text-red-800'
      }`}>
        {row.status.charAt(0).toUpperCase() + row.status.slice(1)}
      </span>
    ),
    priority: 'medium' as const
  },
  {
    id: 'date',
    header: 'Date',
    accessor: 'date' as keyof typeof sampleInvoices[0],
    priority: 'low' as const
  },
  {
    id: 'type',
    header: 'Type',
    accessor: 'type' as keyof typeof sampleInvoices[0],
    priority: 'low' as const
  }
];

const rowActions = [
  {
    id: 'view',
    label: 'View',
    icon: <Eye className="w-4 h-4" />,
    onClick: (row: any) => alert(`Viewing ${row.id}`),
    showOnMobile: true
  },
  {
    id: 'edit',
    label: 'Edit',
    icon: <Edit className="w-4 h-4" />,
    onClick: (row: any) => alert(`Editing ${row.id}`),
    showOnMobile: true
  },
  {
    id: 'delete',
    label: 'Delete',
    icon: <Trash2 className="w-4 h-4" />,
    onClick: (row: any) => alert(`Deleting ${row.id}`),
    variant: 'destructive' as const,
    showOnMobile: false
  }
];

const Week4DemoPage: NextPage = () => {
  const [toastVisible, setToastVisible] = useState(false);
  const [toastType, setToastType] = useState<'success' | 'error' | 'warning' | 'info'>('success');
  const [quantity, setQuantity] = useState(1);
  const [floatingInput, setFloatingInput] = useState('');
  const [refreshCount, setRefreshCount] = useState(0);
  
  const isMobile = !useBreakpoint('md');
  const deviceInfo = useDeviceDetection();

  // Sample refresh function
  const handleRefresh = async () => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    setRefreshCount(prev => prev + 1);
  };

  const showToast = (type: typeof toastType) => {
    setToastType(type);
    setToastVisible(true);
  };

  return (
    <AppDashboardLayout title="Week 4: Mobile Optimization Demo">
      <div className="space-y-8">
        {/* Header Section */}
        <ResponsiveContainer>
          <div className="text-center mb-8">
            <ResponsiveText size="3xl" className="font-bold text-gray-900 mb-4">
              Week 4: Mobile Optimization & Polish
            </ResponsiveText>
            <ResponsiveText size="lg" className="text-gray-600">
              Enhanced responsive design, touch interactions, and micro-animations
            </ResponsiveText>
            
            {/* Device Info */}
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold text-blue-900 mb-2">Device Detection</h3>
              <div className="text-sm text-blue-800 space-y-1">
                <p>Mobile: {deviceInfo.isMobile ? 'Yes' : 'No'}</p>
                <p>Tablet: {deviceInfo.isTablet ? 'Yes' : 'No'}</p>
                <p>Desktop: {deviceInfo.isDesktop ? 'Yes' : 'No'}</p>
                <p>Touch Device: {deviceInfo.isTouch ? 'Yes' : 'No'}</p>
                <p>Current Breakpoint: {isMobile ? 'Mobile' : 'Desktop'}</p>
              </div>
            </div>
          </div>
        </ResponsiveContainer>

        {/* Enhanced Metrics Section */}
        <ResponsiveContainer>
          <h2 className="text-2xl font-bold mb-6">Enhanced Responsive Metrics</h2>
          <MetricCardGrid>
            <EnhancedMetricCard
              title="Total Revenue"
              value={125000}
              previousValue={118000}
              prefix="₦"
              countUp={true}
              icon={<TrendingUp />}
            />
            <EnhancedMetricCard
              title="Active Invoices"
              value={342}
              previousValue={320}
              countUp={true}
              icon={<FileText />}
            />
            <EnhancedMetricCard
              title="Customers"
              value={1250}
              previousValue={1180}
              countUp={true}
              icon={<Users />}
            />
            <EnhancedMetricCard
              title="Success Rate"
              value={95.5}
              previousValue={92.3}
              suffix="%"
              precision={1}
              countUp={true}
              icon={<Star />}
            />
          </MetricCardGrid>
        </ResponsiveContainer>

        {/* Touch Interactions Demo */}
        <ResponsiveContainer>
          <h2 className="text-2xl font-bold mb-6">Touch Interactions</h2>
          
          {/* Swipe Gesture Demo */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Swipe Gestures</h3>
            <SwipeGesture
              onSwipeLeft={() => alert('Swiped left!')}
              onSwipeRight={() => alert('Swiped right!')}
              className="p-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg text-center"
            >
              <p className="text-lg font-medium">
                {isMobile ? 'Swipe left or right on this card' : 'Use touch to swipe on mobile'}
              </p>
            </SwipeGesture>
          </div>

          {/* Swipeable Cards */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Swipeable Action Cards</h3>
            <div className="space-y-4">
              {sampleInvoices.slice(0, 3).map((invoice) => (
                <SwipeableCard
                  key={invoice.id}
                  leftAction={{
                    icon: <Trash2 className="w-5 h-5" />,
                    label: 'Delete',
                    color: 'bg-red-500',
                    action: () => alert(`Deleting ${invoice.id}`)
                  }}
                  rightAction={{
                    icon: <Heart className="w-5 h-5" />,
                    label: 'Favorite',
                    color: 'bg-green-500',
                    action: () => alert(`Favorited ${invoice.id}`)
                  }}
                >
                  <div className="p-4 bg-white border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold">{invoice.id}</h4>
                        <p className="text-gray-600">{invoice.customer}</p>
                      </div>
                      <div className="text-right">
                        <p className="font-bold">₦{invoice.amount.toLocaleString()}</p>
                        <span className={`px-2 py-1 rounded-full text-xs ${
                          invoice.status === 'paid' ? 'bg-green-100 text-green-800' :
                          invoice.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {invoice.status}
                        </span>
                      </div>
                    </div>
                  </div>
                </SwipeableCard>
              ))}
            </div>
          </div>

          {/* Touch Action Buttons */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Touch-Friendly Buttons</h3>
            <ResponsiveGrid columns={{ xs: 1, sm: 2, md: 3 }} gap="md">
              <TouchActionButton
                icon={<Download />}
                label="Download Report"
                onClick={() => showToast('success')}
                variant="primary"
                size="lg"
              />
              <TouchActionButton
                icon={<Share />}
                label="Share Data"
                onClick={() => showToast('info')}
                variant="secondary"
                size="lg"
              />
              <TouchActionButton
                icon={<Trash2 />}
                label="Delete Items"
                onClick={() => showToast('warning')}
                variant="error"
                size="lg"
              />
            </ResponsiveGrid>
          </div>

          {/* Long Press Demo */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Long Press Interaction</h3>
            <LongPress onLongPress={() => alert('Long press detected!')}>
              <div className="p-6 bg-yellow-100 border-2 border-dashed border-yellow-300 rounded-lg text-center">
                <p className="text-yellow-800">
                  {isMobile ? 'Long press this area' : 'Click and hold this area'}
                </p>
              </div>
            </LongPress>
          </div>
        </ResponsiveContainer>

        {/* Pull to Refresh Demo */}
        <ResponsiveShow below="md">
          <ResponsiveContainer>
            <h2 className="text-2xl font-bold mb-6">Pull to Refresh</h2>
            <PullToRefresh onRefresh={handleRefresh}>
              <div className="bg-white border border-gray-200 rounded-lg p-6 min-h-[300px]">
                <h3 className="text-lg font-semibold mb-4">Refreshable Content</h3>
                <p className="text-gray-600 mb-4">
                  Pull down to refresh this content. Refresh count: {refreshCount}
                </p>
                <div className="space-y-2">
                  {Array.from({ length: 5 }, (_, i) => (
                    <div key={i} className="p-3 bg-gray-50 rounded">
                      Item {i + 1} - Last updated: {new Date().toLocaleTimeString()}
                    </div>
                  ))}
                </div>
              </div>
            </PullToRefresh>
          </ResponsiveContainer>
        </ResponsiveShow>

        {/* Mobile Data Table */}
        <ResponsiveContainer>
          <h2 className="text-2xl font-bold mb-6">Mobile-Optimized Data Table</h2>
          <MobileDataTable
            data={sampleInvoices}
            columns={tableColumns}
            rowActions={rowActions}
            onRowClick={(row) => alert(`Clicked ${row.id}`)}
            mobileCardKey="id"
            searchPlaceholder="Search invoices..."
            onSearch={(query) => console.log('Search:', query)}
            emptyMessage="No invoices found"
          />
        </ResponsiveContainer>

        {/* Micro-Interactions Demo */}
        <ResponsiveContainer>
          <h2 className="text-2xl font-bold mb-6">Micro-Interactions</h2>
          
          {/* Interactive Buttons */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Interactive Buttons with Ripple Effects</h3>
            <ResponsiveGrid columns={{ xs: 2, sm: 4 }} gap="md">
              <InteractiveButton onClick={() => showToast('success')} variant="primary">
                Success Toast
              </InteractiveButton>
              <InteractiveButton onClick={() => showToast('error')} variant="error">
                Error Toast
              </InteractiveButton>
              <InteractiveButton onClick={() => showToast('warning')} variant="warning">
                Warning Toast
              </InteractiveButton>
              <InteractiveButton onClick={() => showToast('info')} variant="secondary">
                Info Toast
              </InteractiveButton>
            </ResponsiveGrid>
          </div>

          {/* Animated Counters */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Animated Counters</h3>
            <ResponsiveGrid columns={{ xs: 2, md: 4 }} gap="lg">
              <div className="text-center p-4 bg-white border border-gray-200 rounded-lg">
                <AnimatedCounter value={12345} prefix="₦" className="text-2xl text-primary" />
                <p className="text-sm text-gray-600 mt-2">Revenue</p>
              </div>
              <div className="text-center p-4 bg-white border border-gray-200 rounded-lg">
                <AnimatedCounter value={98.7} suffix="%" precision={1} className="text-2xl text-success" />
                <p className="text-sm text-gray-600 mt-2">Success Rate</p>
              </div>
              <div className="text-center p-4 bg-white border border-gray-200 rounded-lg">
                <AnimatedCounter value={1524} className="text-2xl text-warning" />
                <p className="text-sm text-gray-600 mt-2">Active Users</p>
              </div>
              <div className="text-center p-4 bg-white border border-gray-200 rounded-lg">
                <AnimatedCounter value={847} className="text-2xl text-error" />
                <p className="text-sm text-gray-600 mt-2">Pending Tasks</p>
              </div>
            </ResponsiveGrid>
          </div>

          {/* Progress Bars */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Animated Progress Indicators</h3>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium mb-2">Processing invoices</p>
                <AnimatedProgress value={75} showLabel={true} color="bg-blue-500" />
              </div>
              <div>
                <p className="text-sm font-medium mb-2">FIRS submissions</p>
                <AnimatedProgress value={90} showLabel={true} color="bg-green-500" />
              </div>
              <div>
                <p className="text-sm font-medium mb-2">Data validation</p>
                <AnimatedProgress value={60} showLabel={true} color="bg-yellow-500" />
              </div>
            </div>
          </div>

          {/* Expandable Sections */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Expandable Content</h3>
            <div className="space-y-4">
              <Expandable title="Invoice Processing Details">
                <p className="text-gray-600 mb-4">
                  Detailed information about invoice processing workflow and current status.
                </p>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded">
                    <p className="font-medium">Processed Today</p>
                    <p className="text-2xl font-bold text-primary">247</p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded">
                    <p className="font-medium">Success Rate</p>
                    <p className="text-2xl font-bold text-success">96.5%</p>
                  </div>
                </div>
              </Expandable>
              
              <Expandable title="FIRS Integration Status">
                <p className="text-gray-600 mb-4">
                  Current status of FIRS API integration and submission statistics.
                </p>
                <AnimatedProgress value={85} showLabel={true} color="bg-green-500" />
              </Expandable>
            </div>
          </div>

          {/* Form Controls */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold mb-4">Enhanced Form Controls</h3>
            <ResponsiveGrid columns={{ xs: 1, md: 2 }} gap="lg">
              <FloatingLabelInput
                label="Invoice Number"
                value={floatingInput}
                onChange={setFloatingInput}
                required
              />
              <div className="flex items-center justify-between">
                <span className="font-medium">Quantity:</span>
                <QuantitySelector
                  value={quantity}
                  onChange={setQuantity}
                  min={1}
                  max={100}
                />
              </div>
            </ResponsiveGrid>
          </div>
        </ResponsiveContainer>

        {/* Responsive Visibility Demo */}
        <ResponsiveContainer>
          <h2 className="text-2xl font-bold mb-6">Responsive Visibility</h2>
          <div className="space-y-4">
            <ResponsiveShow above="md">
              <div className="p-4 bg-blue-100 border border-blue-300 rounded-lg">
                <p className="text-blue-800">This content is only visible on desktop (md and above)</p>
              </div>
            </ResponsiveShow>
            
            <ResponsiveShow below="md">
              <div className="p-4 bg-green-100 border border-green-300 rounded-lg">
                <p className="text-green-800">This content is only visible on mobile (below md)</p>
              </div>
            </ResponsiveShow>
            
            <ResponsiveShow only="lg">
              <div className="p-4 bg-purple-100 border border-purple-300 rounded-lg">
                <p className="text-purple-800">This content is only visible on large screens</p>
              </div>
            </ResponsiveShow>
          </div>
        </ResponsiveContainer>

        {/* Floating Action Button */}
        <FloatingActionButton
          icon={<Plus className="w-6 h-6" />}
          onClick={() => showToast('success')}
          position="bottom-right"
          size="lg"
        />

        {/* Toast Notifications */}
        <NotificationToast
          type={toastType}
          title="Action Completed"
          message="Your action has been successfully processed."
          visible={toastVisible}
          onClose={() => setToastVisible(false)}
          autoClose={3000}
        />
      </div>
    </AppDashboardLayout>
  );
};

export default Week4DemoPage;