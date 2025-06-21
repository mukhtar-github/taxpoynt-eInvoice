import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Database, BarChart3, TrendingUp } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import LoadingScreen from '@/components/common/LoadingScreen';
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

// Week 3 Enhanced Components (New)
import { IntegrationStatusGrid } from '@/components/integrations';
import { 
  IntegrationPerformanceChart, 
  SyncActivityMonitor, 
  IntegrationHealthDashboard 
} from '@/components/dashboard/IntegrationDataVisualization';
import { LoadingButton, IntegrationCardSkeleton, Button, Card } from '@/components/ui';

// Services
import { IntegrationService } from '@/services/api/integrationService';
import { Integration } from '@/services/api/types';

// Using Integration type from services/api/types.ts

const IntegrationsPage = () => {
  const router = useRouter();
  const { organization } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<'grid' | 'performance' | 'activity'>('grid');

  useEffect(() => {
    const fetchIntegrations = async () => {
      if (!organization?.id) return;
      
      try {
        setLoading(true);
        const response = await IntegrationService.getIntegrations(organization.id);
        setIntegrations(response.integrations || []);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch integrations:', err);
        setError(err.error || 'Failed to fetch integrations');
      } finally {
        setLoading(false);
      }
    };

    fetchIntegrations();
  }, [organization]);

  const handleAddIntegration = () => {
    router.push('/dashboard/integrations/add');
  };

  const handleViewIntegration = (id: string) => {
    router.push(`/dashboard/integrations/${id}`);
  };

  const handleSyncIntegration = async (integrationId: string) => {
    if (!organization) return;
    
    try {
      // Sync integration using the service
      await IntegrationService.syncIntegration(organization.id, integrationId);
      
      // Refresh integrations list
      const response = await IntegrationService.getIntegrations(organization.id);
      setIntegrations(response.integrations || []);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync integration:', err);
      setError(err.error || 'Failed to sync integration');
    }
  };

  const handleConfigureIntegration = (integrationId: string) => {
    router.push(`/dashboard/integrations/${integrationId}/configure`);
  };

  // Transform integrations data for enhanced components
  const enhancedIntegrations = integrations.map(integration => ({
    id: integration.id,
    name: integration.name,
    type: integration.integration_type === 'odoo' ? 'erp' as const : 'erp' as const,
    platform: integration.integration_type as 'odoo',
    status: integration.status as 'connected' | 'syncing' | 'error' | 'setup' | 'disconnected' | 'warning',
    lastSync: integration.last_sync ? formatDate(integration.last_sync) : undefined,
    nextSync: undefined, // Could be calculated based on sync schedule
    isRealtime: false, // Could be determined from integration config
    metrics: {
      totalRecords: Math.floor(Math.random() * 10000) + 1000, // Mock data
      syncedToday: Math.floor(Math.random() * 100) + 10,
      lastSyncDuration: '2.3s',
      avgResponseTime: '150ms',
      successRate: Math.floor(Math.random() * 20) + 80,
      errorCount: Math.floor(Math.random() * 5)
    }
  }));

  // Mock data for charts (replace with actual API data)
  const mockMetrics = enhancedIntegrations.map(integration => ({
    id: integration.id,
    name: integration.name,
    platform: integration.platform,
    type: integration.type,
    syncCount: integration.metrics?.syncedToday || 0,
    successRate: integration.metrics?.successRate || 0,
    avgResponseTime: 150,
    errorCount: integration.metrics?.errorCount || 0,
    lastSync: integration.lastSync || '',
    trend: 'up' as const
  }));

  const mockActivities = [
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
      integration: 'Odoo ERP',
      status: 'success' as const,
      recordsProcessed: 45,
      duration: 2300
    },
    {
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
      integration: 'HubSpot CRM',
      status: 'warning' as const,
      recordsProcessed: 12,
      duration: 5600
    }
  ];

  if (loading && integrations.length === 0) {
    return <LoadingScreen />;
  }

  return (
    <DashboardLayout>
      <PageHeader
        title="System Integrations"
        description="Manage your ERP, CRM, and POS system integrations"
        actions={
          <div className="flex gap-3">
            {/* View toggle buttons */}
            <div className="hidden sm:flex bg-gray-100 rounded-lg p-1">
              <Button
                variant={view === 'grid' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setView('grid')}
                className="px-3 py-1.5"
              >
                Grid
              </Button>
              <Button
                variant={view === 'performance' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setView('performance')}
                className="px-3 py-1.5"
              >
                <BarChart3 className="w-4 h-4 mr-1" />
                Performance
              </Button>
              <Button
                variant={view === 'activity' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setView('activity')}
                className="px-3 py-1.5"
              >
                <TrendingUp className="w-4 h-4 mr-1" />
                Activity
              </Button>
            </div>

            <LoadingButton
              onClick={handleAddIntegration}
              isLoading={false}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Integration
            </LoadingButton>
          </div>
        }
      />

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <div className="mt-6">
        {view === 'grid' && (
          <>
            {/* Integration Health Overview */}
            {integrations.length > 0 && (
              <div className="mb-8">
                <IntegrationHealthDashboard 
                  integrations={mockMetrics}
                  isLoading={loading}
                />
              </div>
            )}

            {/* Integration Cards Grid */}
            {loading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                {[1, 2, 3].map(i => <IntegrationCardSkeleton key={i} />)}
              </div>
            ) : integrations.length === 0 ? (
              <Card className="p-12 text-center">
                <Database className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No integrations yet</h3>
                <p className="text-gray-500 mb-6">
                  Connect your ERP, CRM, or POS systems to start managing invoices automatically.
                </p>
                <Button onClick={handleAddIntegration}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Your First Integration
                </Button>
              </Card>
            ) : (
              <IntegrationStatusGrid
                integrations={enhancedIntegrations}
                onConnect={(id) => router.push(`/dashboard/integrations/${id}/connect`)}
                onConfigure={handleConfigureIntegration}
                onSync={handleSyncIntegration}
                onViewDetails={handleViewIntegration}
                isLoading={loading}
              />
            )}
          </>
        )}

        {view === 'performance' && (
          <div className="space-y-8">
            <IntegrationPerformanceChart 
              integrations={mockMetrics}
              isLoading={loading}
            />
            <IntegrationHealthDashboard 
              integrations={mockMetrics}
              isLoading={loading}
            />
          </div>
        )}

        {view === 'activity' && (
          <div className="space-y-8">
            <SyncActivityMonitor 
              activities={mockActivities}
              isLoading={loading}
            />
            <IntegrationPerformanceChart 
              integrations={mockMetrics}
              isLoading={loading}
            />
          </div>
        )}
      </div>
    </DashboardLayout>
  );
};

export default IntegrationsPage;
