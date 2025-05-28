import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, RefreshCw, Edit, Trash2, Loader2 } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import IntegrationInfo from '@/components/integrations/IntegrationInfo';
import OdooInvoicesTab from '@/components/integrations/OdooInvoicesTab';
import OdooCustomersTab from '@/components/integrations/OdooCustomersTab';
import OdooProductsTab from '@/components/integrations/OdooProductsTab';
import ConfirmDialog from '@/components/common/ConfirmDialog';
import ErrorAlert from '@/components/common/ErrorAlert';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/utils/apiClient';
import { formatDate } from '@/utils/dateUtils';

// Interface for the integration object
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

// Interface for company information
interface CompanyInfo {
  id: number;
  name: string;
  vat?: string;
  email?: string;
  phone?: string;
  website?: string;
  currency?: string;
  logo?: string;
  address?: {
    street?: string;
    city?: string;
    country?: string;
  };
}

const IntegrationDetailPage = () => {
  const router = useRouter();
  const { id } = router.query;
  const { organization } = useAuth();
  const [integration, setIntegration] = useState<Integration | null>(null);
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    if (!id || !organization?.id) return;
    
    const fetchIntegrationDetails = async () => {
      try {
        setLoading(true);
        // Fetch integration details
        const response = await apiClient.get(
          `/api/v1/organizations/${organization.id}/integrations/${id}`
        );
        setIntegration(response.data);
        
        // If it's an Odoo integration, fetch company info
        if (response.data.integration_type === 'odoo') {
          try {
            const companyResponse = await apiClient.get(
              `/api/v1/organizations/${organization.id}/integrations/${id}/odoo/company-info`
            );
            setCompanyInfo(companyResponse.data);
          } catch (err) {
            console.error('Failed to fetch Odoo company info:', err);
            // Continue even if company info fetch fails
          }
        }
        
        setError(null);
      } catch (err: any) {
        console.error('Failed to fetch integration details:', err);
        setError(err.response?.data?.detail || 'Failed to fetch integration details');
      } finally {
        setLoading(false);
      }
    };

    fetchIntegrationDetails();
  }, [id, organization?.id]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleBackToList = () => {
    router.push('/dashboard/integrations');
  };

  const handleEditIntegration = () => {
    // In a real implementation, this would navigate to an edit page
    alert('Edit functionality will be implemented in a future update');
  };

  const handleDeleteIntegration = async () => {
    if (!id || !organization?.id) return;
    
    try {
      await apiClient.delete(
        `/api/v1/organizations/${organization.id}/integrations/${id}`
      );
      router.push('/dashboard/integrations');
    } catch (err: any) {
      console.error('Failed to delete integration:', err);
      setError(err.response?.data?.detail || 'Failed to delete integration');
    }
    
    setDeleteDialogOpen(false);
  };

  const handleSyncData = async () => {
    if (!id || !organization?.id) return;
    
    try {
      setSyncing(true);
      await apiClient.post(
        `/api/v1/organizations/${organization.id}/integrations/${id}/odoo/sync`
      );
      
      // Refresh integration details to get updated last_sync
      const response = await apiClient.get(
        `/api/v1/organizations/${organization.id}/integrations/${id}`
      );
      setIntegration(response.data);
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to sync data:', err);
      setError(err.response?.data?.detail || 'Failed to sync data from Odoo');
    } finally {
      setSyncing(false);
    }
  };

  if (loading && !integration) {
    return (
      <DashboardLayout>
        <div className="flex justify-center mt-20">
          <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
        </div>
      </DashboardLayout>
    );
  }

  if (!integration) {
    return (
      <DashboardLayout>
        <PageHeader
          title="Integration Not Found"
          description="The requested integration could not be found"
          actions={
            <button
              className="flex items-center gap-1.5 px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
              onClick={handleBackToList}
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Integrations
            </button>
          }
        />
        <div className="p-6 bg-white rounded-md shadow-sm text-center">
          <p className="text-gray-600">
            The integration you are looking for may have been deleted or does not exist.
          </p>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageHeader
        title={integration.name}
        description={`${integration.integration_type.toUpperCase()} Integration`}
        actions={
          <div className="flex gap-2">
            <button
              className="flex items-center gap-1.5 px-4 py-2 border border-gray-300 rounded-md text-sm hover:bg-gray-50"
              onClick={handleBackToList}
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </button>
            <button
              className={`flex items-center gap-1.5 px-4 py-2 border rounded-md text-sm ${syncing || integration.status !== 'configured' ? 'border-gray-200 text-gray-400 cursor-not-allowed' : 'border-blue-500 text-blue-600 hover:bg-blue-50'}`}
              onClick={handleSyncData}
              disabled={syncing || integration.status !== 'configured'}
            >
              <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
              {syncing ? 'Syncing...' : 'Sync Data'}
            </button>
            <button
              className="flex items-center gap-1.5 px-4 py-2 border border-blue-500 text-blue-600 rounded-md text-sm hover:bg-blue-50"
              onClick={handleEditIntegration}
            >
              <Edit className="h-4 w-4" />
              Edit
            </button>
            <button
              className="flex items-center gap-1.5 px-4 py-2 border border-red-500 text-red-600 rounded-md text-sm hover:bg-red-50"
              onClick={() => setDeleteDialogOpen(true)}
            >
              <Trash2 className="h-4 w-4" />
              Delete
            </button>
          </div>
        }
      />

      {error && <ErrorAlert message={error} onClose={() => setError(null)} className="mb-4" />}

      <div className="bg-white rounded-md shadow-sm mb-6">
        <IntegrationInfo 
          integration={integration} 
          companyInfo={companyInfo}
        />
      </div>

      <div className="bg-white rounded-md shadow-sm mb-6">
        <div className="border-b border-gray-200">
          <nav className="flex -mb-px">
            <button
              onClick={(e) => handleTabChange(e, 0)}
              className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 0 ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              aria-current={activeTab === 0 ? 'page' : undefined}
            >
              Invoices
            </button>
            <button
              onClick={(e) => handleTabChange(e, 1)}
              className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 1 ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              aria-current={activeTab === 1 ? 'page' : undefined}
            >
              Customers
            </button>
            <button
              onClick={(e) => handleTabChange(e, 2)}
              className={`py-4 px-6 text-sm font-medium border-b-2 ${activeTab === 2 ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              aria-current={activeTab === 2 ? 'page' : undefined}
            >
              Products
            </button>
          </nav>
        </div>
        <div className="p-6">
          {activeTab === 0 && (
            <OdooInvoicesTab 
              organizationId={organization?.id} 
              integrationId={integration.id} 
            />
          )}
          {activeTab === 1 && (
            <OdooCustomersTab 
              organizationId={organization?.id} 
              integrationId={integration.id}
            />
          )}
          {activeTab === 2 && (
            <OdooProductsTab 
              organizationId={organization?.id} 
              integrationId={integration.id}
            />
          )}
        </div>
      </div>

      <ConfirmDialog
        open={deleteDialogOpen}
        title="Delete Integration"
        content="Are you sure you want to delete this integration? This action cannot be undone."
        onConfirm={handleDeleteIntegration}
        onCancel={() => setDeleteDialogOpen(false)}
      />
    </DashboardLayout>
  );
};

export default IntegrationDetailPage;
