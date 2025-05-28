import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Link2, Database } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import LoadingScreen from '@/components/common/LoadingScreen';
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';
import IntegrationStatusMonitor from '@/components/integrations/IntegrationStatusMonitor';
import { IntegrationService } from '@/services/api/integrationService';
import { Integration, IntegrationsResponse } from '@/services/api/types';

// Using Integration type from services/api/types.ts

const IntegrationsPage = () => {
  const router = useRouter();
  const { user, organization } = useAuth();
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  const handleSyncIntegration = async (integrationId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!organization) return;
    
    try {
      setLoading(true);
      // Sync integration using the service
      await IntegrationService.syncIntegration(organization.id, integrationId);
      
      // Refresh integrations list
      const response = await IntegrationService.getIntegrations(organization.id);
      setIntegrations(response.integrations || []);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync integration:', err);
      setError(err.error || 'Failed to sync integration');
    } finally {
      setLoading(false);
    }
  };

  const getIntegrationTypeIcon = (type: string) => {
    switch (type) {
      case 'odoo':
        return <Database className="w-7 h-7 text-blue-700" />;
      default:
        return <Link2 className="w-7 h-7 text-gray-500" />;
    }
  };

  // Status styles now handled by IntegrationStatusMonitor component

  if (loading && integrations.length === 0) {
    return <LoadingScreen />;
  }

  return (
    <DashboardLayout>
      <PageHeader
        title="ERP Integrations"
        description="Manage your ERP and accounting system integrations"
        actions={
          <button
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md shadow transition"
            onClick={handleAddIntegration}
            type="button"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </button>
        }
      />

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {integrations.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            No integrations found. Click <span className="font-semibold text-blue-600">Add Integration</span> to get started.
          </div>
        ) : (
          integrations.map((integration) => (
            <div
              key={integration.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer border flex flex-col h-full"
              onClick={() => handleViewIntegration(integration.id)}
            >
              <div className="flex justify-between items-center px-6 pt-6 pb-2">
                <div className="flex items-center">
                  {getIntegrationTypeIcon(integration.integration_type)}
                  <span className="ml-3 text-lg font-semibold text-gray-900">{integration.name}</span>
                </div>
                <IntegrationStatusMonitor 
                  status={integration.status} 
                  showDetails={false} 
                />
              </div>
              <div className="px-6 pb-2 text-gray-600 text-sm">
                {integration.description}
              </div>
              <div className="border-t mt-2" />
              <div className="flex items-center justify-between px-6 py-4">
                <div className="text-xs text-gray-500">
                  <div>Created: {formatDate(integration.created_at)}</div>
                  <div>Last Sync: {integration.last_sync ? formatDate(integration.last_sync) : '-'}</div>
                </div>
                <IntegrationStatusMonitor 
                  status={integration.status} 
                  lastSync={integration.last_sync} 
                  showDetails={false} 
                  onSyncClick={e => handleSyncIntegration(integration.id, e)}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </DashboardLayout>
  );
};

export default IntegrationsPage;
