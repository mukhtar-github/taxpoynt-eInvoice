import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Plus, Link2, Users } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import LoadingScreen from '@/components/common/LoadingScreen';
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';
import IntegrationStatusMonitor from '@/components/integrations/IntegrationStatusMonitor';
import CRMService from '@/services/crmService';
import { CRMConnection } from '@/types/crm';

const CRMIntegrationsPage = () => {
  const router = useRouter();
  const { user, organization } = useAuth();
  const [connections, setConnections] = useState<CRMConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConnections = async () => {
      if (!organization?.id) return;
      
      try {
        setLoading(true);
        const response = await CRMService.getConnections(organization.id);
        setConnections(response.connections || []);
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch CRM connections:', err);
        setError(err.message || 'Failed to fetch CRM connections');
      } finally {
        setLoading(false);
      }
    };

    fetchConnections();
  }, [organization]);

  const handleAddConnection = () => {
    router.push('/dashboard/crm/add');
  };

  const handleViewConnection = (id: string) => {
    router.push(`/dashboard/crm/${id}`);
  };

  const handleSyncConnection = async (connectionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!organization) return;
    
    try {
      setLoading(true);
      await CRMService.syncDeals(connectionId);
      
      // Refresh connections list
      const response = await CRMService.getConnections(organization.id);
      setConnections(response.connections || []);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync CRM connection:', err);
      setError(err.message || 'Failed to sync CRM connection');
    } finally {
      setLoading(false);
    }
  };

  const getCRMTypeIcon = (type: string) => {
    switch (type) {
      case 'hubspot':
        return <Users className="w-7 h-7 text-orange-600" />;
      case 'salesforce':
        return <Link2 className="w-7 h-7 text-blue-600" />;
      default:
        return <Link2 className="w-7 h-7 text-gray-500" />;
    }
  };

  const formatConnectionStatus = (status: string) => {
    switch (status) {
      case 'connected':
        return 'configured';
      case 'connecting':
        return 'syncing';
      case 'failed':
        return 'error';
      default:
        return 'pending';
    }
  };

  if (loading && connections.length === 0) {
    return <LoadingScreen />;
  }

  return (
    <DashboardLayout>
      <PageHeader
        title="CRM Integrations"
        description="Manage your Customer Relationship Management system integrations"
        actions={
          <button
            className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md shadow transition"
            onClick={handleAddConnection}
            type="button"
          >
            <Plus className="w-4 h-4 mr-2" />
            Add CRM Connection
          </button>
        }
      />

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connections.length === 0 ? (
          <div className="col-span-full text-center text-gray-500 py-12">
            No CRM connections found. Click <span className="font-semibold text-blue-600">Add CRM Connection</span> to get started.
          </div>
        ) : (
          connections.map((connection) => (
            <div
              key={connection.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition cursor-pointer border flex flex-col h-full"
              onClick={() => handleViewConnection(connection.id)}
            >
              <div className="flex justify-between items-center px-6 pt-6 pb-2">
                <div className="flex items-center">
                  {getCRMTypeIcon(connection.crm_type)}
                  <span className="ml-3 text-lg font-semibold text-gray-900">{connection.name}</span>
                </div>
                <IntegrationStatusMonitor 
                  status={formatConnectionStatus(connection.status)} 
                  showDetails={false} 
                />
              </div>
              <div className="px-6 pb-2 text-gray-600 text-sm">
                {connection.crm_type.charAt(0).toUpperCase() + connection.crm_type.slice(1)} CRM Integration
              </div>
              <div className="border-t mt-2" />
              <div className="flex items-center justify-between px-6 py-4">
                <div className="text-xs text-gray-500">
                  <div>Created: {formatDate(connection.created_at)}</div>
                  <div>Last Sync: {connection.last_sync ? formatDate(connection.last_sync) : '-'}</div>
                </div>
                <IntegrationStatusMonitor 
                  status={formatConnectionStatus(connection.status)} 
                  lastSync={connection.last_sync} 
                  showDetails={false} 
                  onSyncClick={e => handleSyncConnection(connection.id, e)}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </DashboardLayout>
  );
};

export default CRMIntegrationsPage;