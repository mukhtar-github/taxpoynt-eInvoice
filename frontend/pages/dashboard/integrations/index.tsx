import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Link2, Database, RefreshCw } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import LoadingScreen from '@/components/common/LoadingScreen';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/utils/apiClient';
import { formatDate } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

// Define types for integrations
interface Integration {
  id: string;
  name: string;
  description: string;
  integration_type: string;
  status: string;
  created_at: string;
  last_sync?: string;
  config: Record<string, any>;
}

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
        const response = await apiClient.get(
          `/api/v1/organizations/${organization.id}/integrations`
        );
        setIntegrations(response.data);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch integrations:', err);
        setError(err.response?.data?.detail || 'Failed to fetch integrations');
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

  const handleSyncIntegration = async (id: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (!organization?.id) return;
    
    try {
      setLoading(true);
      await apiClient.post(
        `/api/v1/organizations/${organization.id}/integrations/${id}/odoo/sync`
      );
      
      // Refresh integrations list
      const response = await apiClient.get(
        `/api/v1/organizations/${organization.id}/integrations`
      );
      setIntegrations(response.data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync integration:', err);
      setError(err.response?.data?.detail || 'Failed to sync integration');
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

  const getStatusStyles = (status: string) => {
    switch (status) {
      case 'configured':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

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
              <div className="flex items-center px-6 pt-6 pb-2">
                {getIntegrationTypeIcon(integration.integration_type)}
                <span className="ml-3 text-lg font-semibold text-gray-900 flex-1">{integration.name}</span>
                <span className={`border px-2 py-0.5 rounded text-xs font-medium capitalize ${getStatusStyles(integration.status)}`}>
                  {integration.status}
                </span>
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
                <button
                  className="inline-flex items-center px-3 py-1 border border-blue-600 text-blue-700 rounded hover:bg-blue-50 text-xs font-medium transition"
                  onClick={e => handleSyncIntegration(integration.id, e)}
                  type="button"
                >
                  <RefreshCw className="w-4 h-4 mr-1" />
                  Sync
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </DashboardLayout>
  );
};

export default IntegrationsPage;
