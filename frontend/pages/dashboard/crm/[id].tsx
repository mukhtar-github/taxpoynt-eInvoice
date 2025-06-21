import React, { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, RefreshCw, Edit, Trash2, Loader2, Users, FileText } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ErrorAlert from '@/components/common/ErrorAlert';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import HubSpotDealsManager from '@/components/integrations/crm/HubSpotDealsManager';
import { useAuth } from '@/hooks/useAuth';
import { formatDate } from '@/utils/dateUtils';
import CRMService from '@/services/crmService';
import { CRMConnection } from '@/types/crm';

const CRMConnectionDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { organization } = useAuth();
  const [connection, setConnection] = useState<CRMConnection | null>(null);
  const [activeTab, setActiveTab] = useState('deals');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const fetchConnectionDetails = useCallback(async () => {
    if (!organization?.id || !id) return null;
    
    try {
      setLoading(true);
      const response = await CRMService.getConnection(organization.id, id as string);
      setConnection(response.connection);
      setError(null);
      return response.connection;
    } catch (err: any) {
      console.error('Failed to fetch CRM connection details:', err);
      const errorMessage = err.message || 'Failed to fetch CRM connection details';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [organization?.id, id]);

  useEffect(() => {
    if (organization?.id && id) {
      fetchConnectionDetails();
    }
  }, [organization?.id, id, fetchConnectionDetails]);

  const handleBackToList = () => {
    router.push('/dashboard/crm');
  };

  const handleEditConnection = () => {
    // Navigate to edit page (to be implemented)
    alert('Edit functionality will be implemented in a future update');
  };

  const handleDeleteConnection = async () => {
    if (!id || !organization?.id) return;
    
    try {
      await CRMService.deleteConnection(organization.id, id as string);
      router.push('/dashboard/crm');
    } catch (err: any) {
      console.error('Failed to delete CRM connection:', err);
      setError(err.message || 'Failed to delete CRM connection');
    }
    
    setDeleteDialogOpen(false);
  };

  const handleSyncData = async () => {
    if (!organization || !connection || syncing) return;
    
    try {
      setSyncing(true);
      await CRMService.syncDeals(connection.id);
      
      // Refresh connection data
      const response = await CRMService.getConnection(organization.id, connection.id);
      setConnection(response.connection);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync CRM connection:', err);
      setError(err.message || 'Failed to sync CRM connection');
    } finally {
      setSyncing(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'success';
      case 'connecting':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'secondary';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'connected':
        return 'Connected';
      case 'connecting':
        return 'Connecting...';
      case 'failed':
        return 'Connection Failed';
      default:
        return 'Pending';
    }
  };

  if (loading && !connection) {
    return (
      <DashboardLayout>
        <div className="flex justify-center mt-20">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (!connection) {
    return (
      <DashboardLayout>
        <PageHeader
          title="CRM Connection Not Found"
          description="The requested CRM connection could not be found"
          actions={
            <Button variant="outline" onClick={handleBackToList}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to CRM Integrations
            </Button>
          }
        />
        <div className="p-6 bg-white rounded-md shadow-sm text-center">
          <p className="text-gray-600">
            The CRM connection you are looking for may have been deleted or does not exist.
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageHeader
        title={connection.name}
        description={`${connection.crm_type.charAt(0).toUpperCase() + connection.crm_type.slice(1)} CRM Integration`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={handleBackToList}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
            <Button
              variant="outline"
              onClick={handleSyncData}
              disabled={syncing || connection.status !== 'connected'}
              loading={syncing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Data'}
            </Button>
            <Button variant="outline" onClick={handleEditConnection}>
              <Edit className="h-4 w-4 mr-2" />
              Edit
            </Button>
            <Button 
              variant="outline"
              onClick={() => setDeleteDialogOpen(true)}
              className="text-red-600 border-red-200 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </div>
        }
      />

      {error && <ErrorAlert message={error} onClose={() => setError(null)} className="mb-4" />}

      {/* Connection Info Card */}
      <Card className="mb-6">
        <CardHeader title="Connection Details" />
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <span className="text-sm text-gray-600">Status</span>
              <div className="mt-1">
                <Badge variant={getStatusColor(connection.status)}>
                  {getStatusText(connection.status)}
                </Badge>
              </div>
            </div>
            <div>
              <span className="text-sm text-gray-600">CRM Type</span>
              <p className="font-medium mt-1">
                {connection.crm_type.charAt(0).toUpperCase() + connection.crm_type.slice(1)}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Created</span>
              <p className="font-medium mt-1">{formatDate(connection.created_at)}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Last Sync</span>
              <p className="font-medium mt-1">
                {connection.last_sync ? formatDate(connection.last_sync) : 'Never'}
              </p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Total Deals Synced</span>
              <p className="font-medium mt-1">{connection.total_deals || 0}</p>
            </div>
            <div>
              <span className="text-sm text-gray-600">Invoices Generated</span>
              <p className="font-medium mt-1">{connection.total_invoices || 0}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs Navigation */}
      <div className="bg-white rounded-md shadow-sm mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={() => setActiveTab('deals')}
              className={`py-4 px-6 text-sm font-medium border-b-2 flex items-center ${
                activeTab === 'deals' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Users className="w-4 h-4 mr-2" />
              Deals
            </button>
            <button
              onClick={() => setActiveTab('invoices')}
              className={`py-4 px-6 text-sm font-medium border-b-2 flex items-center ${
                activeTab === 'invoices' 
                  ? 'border-blue-500 text-blue-600' 
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <FileText className="w-4 h-4 mr-2" />
              Generated Invoices
            </button>
          </nav>
        </div>
        
        <div className="p-6">
          {activeTab === 'deals' && connection.crm_type === 'hubspot' && (
            <HubSpotDealsManager 
              connection={connection}
              onDealsUpdate={() => fetchConnectionDetails()}
            />
          )}
          
          {activeTab === 'invoices' && (
            <div className="text-center text-gray-500 py-12">
              <FileText className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>Invoice tracking will be implemented in a future update.</p>
            </div>
          )}
          
          {connection.crm_type !== 'hubspot' && (
            <div className="text-center text-gray-500 py-12">
              <p>This CRM type is not yet fully supported.</p>
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete CRM Connection"
        content="Are you sure you want to delete this CRM connection? This action cannot be undone and all associated data will be lost."
        onConfirm={handleDeleteConnection}
        onCancel={() => setDeleteDialogOpen(false)}
      />
    </DashboardLayout>
  );
};

export default CRMConnectionDetailPage;