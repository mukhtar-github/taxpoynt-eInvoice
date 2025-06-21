/**
 * Week 3 UI/UX Implementation Showcase
 * 
 * Demonstrates all Week 3 components:
 * - Enhanced Integration Status Cards
 * - Setup Wizard with Progress Indicators  
 * - Enhanced Form Validation and Error States
 * - Loading States and Micro-animations
 * - Data Visualization Components
 */

import React, { useState } from 'react';
import { 
  Database, 
  Users, 
  FileText, 
  Settings, 
  Play,
  Pause,
  RotateCcw,
  CheckCircle,
  AlertCircle,
  Zap
} from 'lucide-react';

import DashboardLayout from '@/components/layouts/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

// Week 3 Components
import EnhancedIntegrationStatusCard, { IntegrationStatusGrid } from '@/components/integrations/EnhancedIntegrationStatusCard';
import EnhancedSetupWizard from '@/components/integrations/EnhancedSetupWizard';
import { EnhancedInput, EnhancedTextarea } from '@/components/ui/EnhancedFormField';
import { 
  LoadingSpinner, 
  LoadingButton, 
  ProgressBar, 
  CircularProgress, 
  PulseIndicator,
  LoadingOverlay,
  AnimatedState,
  IntegrationCardSkeleton
} from '@/components/ui/LoadingStates';
import { 
  IntegrationPerformanceChart, 
  SyncActivityMonitor, 
  IntegrationHealthDashboard 
} from '@/components/dashboard/IntegrationDataVisualization';

const Week3Showcase = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [showWizard, setShowWizard] = useState(false);
  const [progress, setProgress] = useState(65);
  const [formValue, setFormValue] = useState('');
  const [showAnimation, setShowAnimation] = useState(true);

  // Mock data for integrations
  const mockIntegrations = [
    {
      id: '1',
      name: 'Main ERP System',
      type: 'erp' as const,
      platform: 'odoo' as const,
      status: 'connected' as const,
      lastSync: '2 minutes ago',
      isRealtime: true,
      metrics: {
        totalRecords: 15420,
        syncedToday: 89,
        lastSyncDuration: '1.8s',
        avgResponseTime: '120ms',
        successRate: 98,
        errorCount: 0
      }
    },
    {
      id: '2',
      name: 'Sales CRM',
      type: 'crm' as const,
      platform: 'hubspot' as const,
      status: 'syncing' as const,
      lastSync: '5 minutes ago',
      isRealtime: false,
      metrics: {
        totalRecords: 8930,
        syncedToday: 45,
        lastSyncDuration: '3.2s',
        avgResponseTime: '250ms',
        successRate: 95,
        errorCount: 2
      }
    },
    {
      id: '3',
      name: 'Retail POS',
      type: 'pos' as const,
      platform: 'square' as const,
      status: 'warning' as const,
      lastSync: '1 hour ago',
      isRealtime: false,
      metrics: {
        totalRecords: 5240,
        syncedToday: 23,
        lastSyncDuration: '5.1s',
        avgResponseTime: '450ms',
        successRate: 87,
        errorCount: 8
      }
    }
  ];

  // Mock chart data
  const mockMetrics = mockIntegrations.map(integration => ({
    id: integration.id,
    name: integration.name,
    platform: integration.platform,
    type: integration.type,
    syncCount: integration.metrics?.syncedToday || 0,
    successRate: integration.metrics?.successRate || 0,
    avgResponseTime: parseInt(integration.metrics?.avgResponseTime || '150'),
    errorCount: integration.metrics?.errorCount || 0,
    lastSync: integration.lastSync || '',
    trend: 'up' as const
  }));

  const mockActivities = [
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 2).toISOString(),
      integration: 'Main ERP System',
      status: 'success' as const,
      recordsProcessed: 67,
      duration: 1800
    },
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 8).toISOString(),
      integration: 'Sales CRM',
      status: 'warning' as const,
      recordsProcessed: 23,
      duration: 3200
    },
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      integration: 'Retail POS',
      status: 'error' as const,
      recordsProcessed: 8,
      duration: 5100
    }
  ];

  // Validation example
  const validateEmail = (value: string) => {
    if (!value) return { isValid: false, message: 'Email is required', type: 'error' as const };
    if (!/\S+@\S+\.\S+/.test(value)) return { isValid: false, message: 'Invalid email format', type: 'error' as const };
    if (value.includes('test')) return { isValid: true, message: 'Test email detected', type: 'warning' as const };
    return { isValid: true, message: 'Valid email', type: 'success' as const };
  };

  const emailValidation = validateEmail(formValue);

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto p-6 space-y-12">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Week 3: Integration & Form Improvements
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Enhanced integration cards, setup wizards, form validation, loading states, and data visualization components
          </p>
        </div>

        {/* Integration Status Cards */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <Database className="w-6 h-6 text-primary" />
              Enhanced Integration Status Cards
            </h2>
            <p className="text-gray-600">
              Advanced integration cards with real-time status, metrics, and mobile-first design
            </p>
          </div>

          <IntegrationStatusGrid
            integrations={mockIntegrations}
            onConnect={(id) => console.log('Connect:', id)}
            onConfigure={(id) => console.log('Configure:', id)}
            onSync={(id) => console.log('Sync:', id)}
            onViewDetails={(id) => console.log('View details:', id)}
            className="mb-8"
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Loading States</h3>
              <div className="grid grid-cols-3 gap-4">
                {[1, 2, 3].map(i => <IntegrationCardSkeleton key={i} />)}
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold mb-4">Real-time Indicators</h3>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <PulseIndicator variant="success" />
                  <span>System Active</span>
                </div>
                <div className="flex items-center gap-3">
                  <PulseIndicator variant="warning" />
                  <span>Sync in Progress</span>
                </div>
                <div className="flex items-center gap-3">
                  <PulseIndicator variant="error" />
                  <span>Connection Error</span>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Setup Wizard */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <Settings className="w-6 h-6 text-primary" />
              Enhanced Setup Wizard
            </h2>
            <p className="text-gray-600">
              Multi-step configuration with progress indicators and platform-specific flows
            </p>
          </div>

          <div className="flex gap-4 mb-6">
            <Button onClick={() => setShowWizard(!showWizard)}>
              {showWizard ? 'Hide' : 'Show'} Setup Wizard
            </Button>
          </div>

          {showWizard && (
            <EnhancedSetupWizard
              type="erp"
              platform="odoo"
              organizationId="demo-org"
              onComplete={(data) => {
                console.log('Setup completed:', data);
                setShowWizard(false);
              }}
              onCancel={() => setShowWizard(false)}
              className="mb-8"
            />
          )}
        </section>

        {/* Enhanced Form Validation */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <CheckCircle className="w-6 h-6 text-primary" />
              Enhanced Form Validation
            </h2>
            <p className="text-gray-600">
              Real-time validation with multiple states and enhanced accessibility
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Input Validation States</h3>
              <div className="space-y-4">
                <EnhancedInput
                  label="Email Address"
                  type="email"
                  value={formValue}
                  onChange={(e) => setFormValue(e.target.value)}
                  validation={emailValidation}
                  showValidationIcon
                  helpText="Enter a valid email address"
                  required
                />

                <EnhancedInput
                  label="Password"
                  type="password"
                  showPasswordToggle
                  success
                  successMessage="Strong password"
                  helpText="Use at least 8 characters"
                />

                <EnhancedInput
                  label="Username"
                  error
                  errorMessage="Username already taken"
                  showCharacterCount
                  maxLength={20}
                />

                <EnhancedTextarea
                  label="Description"
                  rows={3}
                  autoResize
                  showCharacterCount
                  maxLength={500}
                  helpText="Describe your integration requirements"
                />
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold mb-4">Loading & Progress States</h3>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Progress Bar</label>
                  <ProgressBar value={progress} showPercentage animated />
                  <div className="flex gap-2 mt-2">
                    <Button size="sm" onClick={() => setProgress(Math.max(0, progress - 10))}>-10</Button>
                    <Button size="sm" onClick={() => setProgress(Math.min(100, progress + 10))}>+10</Button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Circular Progress</label>
                  <div className="flex gap-4">
                    <CircularProgress value={85} showPercentage />
                    <CircularProgress value={60} variant="warning" showPercentage />
                    <CircularProgress value={30} variant="error" showPercentage />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-2">Loading Buttons</label>
                  <div className="flex gap-2">
                    <LoadingButton
                      isLoading={isLoading}
                      onClick={() => {
                        setIsLoading(true);
                        setTimeout(() => setIsLoading(false), 3000);
                      }}
                    >
                      Save Changes
                    </LoadingButton>
                    
                    <LoadingButton
                      variant="outline"
                      isLoading={false}
                      loadingText="Syncing..."
                    >
                      Sync Data
                    </LoadingButton>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </section>

        {/* Loading States & Animations */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <Zap className="w-6 h-6 text-primary" />
              Loading States & Micro-animations
            </h2>
            <p className="text-gray-600">
              Advanced loading indicators and smooth state transitions
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card className="p-6">
              <h3 className="font-semibold mb-4">Spinner Variants</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <LoadingSpinner size="xs" />
                  <p className="text-xs mt-1">XS</p>
                </div>
                <div>
                  <LoadingSpinner size="sm" />
                  <p className="text-xs mt-1">SM</p>
                </div>
                <div>
                  <LoadingSpinner size="md" />
                  <p className="text-xs mt-1">MD</p>
                </div>
                <div>
                  <LoadingSpinner size="lg" />
                  <p className="text-xs mt-1">LG</p>
                </div>
                <div>
                  <LoadingSpinner size="xl" />
                  <p className="text-xs mt-1">XL</p>
                </div>
                <div>
                  <LoadingSpinner variant="success" />
                  <p className="text-xs mt-1">Success</p>
                </div>
              </div>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold mb-4">Loading Overlay</h3>
              <LoadingOverlay
                isLoading={isLoading}
                message="Processing data..."
                variant="dots"
              >
                <div className="h-32 bg-gray-100 rounded-lg flex items-center justify-center">
                  <p className="text-gray-600">Content area</p>
                </div>
              </LoadingOverlay>
              <Button 
                className="mt-4 w-full" 
                onClick={() => {
                  setIsLoading(true);
                  setTimeout(() => setIsLoading(false), 3000);
                }}
              >
                Trigger Loading
              </Button>
            </Card>

            <Card className="p-6">
              <h3 className="font-semibold mb-4">Animated States</h3>
              <div className="space-y-4">
                <AnimatedState 
                  isVisible={showAnimation}
                  animation="fade"
                  className="p-4 bg-blue-50 rounded-lg"
                >
                  <p className="text-blue-800">Fade Animation</p>
                </AnimatedState>

                <AnimatedState 
                  isVisible={showAnimation}
                  animation="slide-up"
                  delay={100}
                  className="p-4 bg-green-50 rounded-lg"
                >
                  <p className="text-green-800">Slide Up Animation</p>
                </AnimatedState>

                <AnimatedState 
                  isVisible={showAnimation}
                  animation="scale"
                  delay={200}
                  className="p-4 bg-purple-50 rounded-lg"
                >
                  <p className="text-purple-800">Scale Animation</p>
                </AnimatedState>

                <Button onClick={() => setShowAnimation(!showAnimation)}>
                  {showAnimation ? 'Hide' : 'Show'} Animations
                </Button>
              </div>
            </Card>
          </div>
        </section>

        {/* Data Visualization */}
        <section>
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-2 flex items-center gap-2">
              <FileText className="w-6 h-6 text-primary" />
              Data Visualization Components
            </h2>
            <p className="text-gray-600">
              Interactive charts and graphs for integration monitoring
            </p>
          </div>

          <div className="space-y-8">
            <IntegrationHealthDashboard
              integrations={mockMetrics}
              isLoading={false}
            />

            <IntegrationPerformanceChart
              integrations={mockMetrics}
              isLoading={false}
            />

            <SyncActivityMonitor
              activities={mockActivities}
              isLoading={false}
            />
          </div>
        </section>

        {/* Summary */}
        <section className="text-center">
          <Card className="p-8">
            <h2 className="text-2xl font-semibold mb-4">Week 3 Implementation Complete! ✨</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 text-center">
              <div>
                <Badge variant="success" className="mb-2">✓ Integration Cards</Badge>
                <p className="text-sm text-gray-600">Enhanced status cards with real-time metrics</p>
              </div>
              <div>
                <Badge variant="success" className="mb-2">✓ Setup Wizard</Badge>
                <p className="text-sm text-gray-600">Multi-step configuration with progress tracking</p>
              </div>
              <div>
                <Badge variant="success" className="mb-2">✓ Form Validation</Badge>
                <p className="text-sm text-gray-600">Real-time validation with enhanced UX</p>
              </div>
              <div>
                <Badge variant="success" className="mb-2">✓ Data Visualization</Badge>
                <p className="text-sm text-gray-600">Interactive charts and performance monitoring</p>
              </div>
            </div>
            
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <p className="text-blue-800 font-medium">
                🚀 Ready for Week 4: Mobile Optimization & Polish
              </p>
              <p className="text-blue-600 text-sm mt-1">
                Next: Responsive breakpoints, touch interactions, pull-to-refresh, and micro-interactions
              </p>
            </div>
          </Card>
        </section>
      </div>
    </DashboardLayout>
  );
};

export default Week3Showcase;