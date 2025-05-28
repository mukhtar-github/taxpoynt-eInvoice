import React, { useState } from 'react';
import { useRouter } from 'next/router';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import OdooConnectionForm from '@/components/integrations/OdooConnectionForm';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/utils/apiClient';
import ErrorAlert from '@/components/common/ErrorAlert';
import { ArrowLeft } from 'lucide-react';
import Image from 'next/image';

// Integration type options
const integrationOptions = [
  {
    id: 'odoo',
    name: 'Odoo ERP',
    description: 'Connect to your Odoo ERP system to import invoices, customers, and products.',
    logo: '/images/integration-logos/odoo.png',
    comingSoon: false
  },
  {
    id: 'quickbooks',
    name: 'QuickBooks',
    description: 'Connect to QuickBooks for accounting and financial data integration.',
    logo: '/images/integration-logos/quickbooks.png',
    comingSoon: true
  },
  {
    id: 'sage',
    name: 'Sage',
    description: 'Connect to Sage for business management solutions.',
    logo: '/images/integration-logos/sage.png',
    comingSoon: true
  }
];

// Step labels for the integration setup process
const steps = ['Select Integration', 'Configure Connection', 'Verify Connection'];

const AddIntegrationPage = () => {
  const router = useRouter();
  const { organization } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [selectedIntegration, setSelectedIntegration] = useState<string | null>(null);
  const [connectionConfig, setConnectionConfig] = useState({
    name: '',
    description: '',
    url: '',
    database: '',
    username: '',
    password: '',
    auth_method: 'password'
  });
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [connectionTestResult, setConnectionTestResult] = useState<any>(null);

  const handleBack = () => {
    if (activeStep === 0) {
      router.push('/dashboard/integrations');
    } else {
      setActiveStep((prevActiveStep) => prevActiveStep - 1);
    }
  };

  const handleNext = async () => {
    if (activeStep === 1) {
      // Test connection before proceeding to final step
      await testConnection();
    } else if (activeStep === 2) {
      // Save integration
      await saveIntegration();
    } else {
      setActiveStep((prevActiveStep) => prevActiveStep + 1);
    }
  };

  const handleIntegrationSelect = (integrationId: string) => {
    if (integrationOptions.find(option => option.id === integrationId && option.comingSoon)) {
      return;
    }
    setSelectedIntegration(integrationId);
    setActiveStep(1);
  };

  const handleConnectionConfigChange = (field: string, value: string) => {
    setConnectionConfig(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const testConnection = async () => {
    if (!organization?.id) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await apiClient.post(
        `/api/v1/organizations/${organization.id}/integrations/test-odoo`,
        {
          url: connectionConfig.url,
          database: connectionConfig.database,
          username: connectionConfig.username,
          password: connectionConfig.password,
          auth_method: connectionConfig.auth_method
        }
      );

      setConnectionTestResult(response.data);
      setActiveStep(2);
    } catch (err: any) {
      console.error('Connection test failed:', err);
      setError(err.response?.data?.detail || 'Failed to test connection');
      setConnectionTestResult({
        status: 'error',
        message: err.response?.data?.detail || 'Connection test failed'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const saveIntegration = async () => {
    if (!organization?.id) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await apiClient.post(
        `/api/v1/organizations/${organization.id}/integrations/odoo`,
        {
          name: connectionConfig.name,
          description: connectionConfig.description,
          client_id: organization.id,
          config: {
            url: connectionConfig.url,
            database: connectionConfig.database,
            username: connectionConfig.username,
            password: connectionConfig.password,
            auth_method: connectionConfig.auth_method
          }
        }
      );

      // Redirect to the integration details page
      router.push(`/dashboard/integrations/${response.data.id}`);
    } catch (err: any) {
      console.error('Failed to save integration:', err);
      setError(err.response?.data?.detail || 'Failed to save integration');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {integrationOptions.map((option) => (
              <div
                key={option.id}
                className={`relative bg-white rounded-lg shadow-md flex flex-col h-full border transition duration-150 ${option.comingSoon ? 'opacity-60 cursor-not-allowed' : 'hover:shadow-lg cursor-pointer'}`}
                onClick={() => !option.comingSoon && handleIntegrationSelect(option.id)}
                aria-disabled={option.comingSoon}
                tabIndex={option.comingSoon ? -1 : 0}
                role="button"
              >
                {option.comingSoon && (
                  <span className="absolute top-4 right-4 bg-yellow-400 text-yellow-900 px-2 py-1 rounded text-xs font-bold z-10">
                    Coming Soon
                  </span>
                )}
                <div className="flex flex-col flex-1 p-6 items-center justify-center">
                  <div className="h-20 flex items-center justify-center mb-4 w-full">
                    <Image
                      src={option.logo}
                      alt={option.name}
                      width={80}
                      height={80}
                      className="object-contain max-h-20 max-w-full"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.src = '/images/integration-logos/default.png';
                      }}
                    />
                  </div>
                  <h3 className="text-lg font-semibold text-center mb-2">{option.name}</h3>
                  <p className="text-gray-600 text-center text-sm">{option.description}</p>
                </div>
              </div>
            ))}
          </div>
        );
      case 1:
        return (
          <OdooConnectionForm
            config={connectionConfig}
            onChange={handleConnectionConfigChange}
            isSubmitting={isSubmitting}
          />
        );
      case 2:
        return (
          <div>
            <div className="bg-white rounded-md shadow p-6 mb-6">
              <h2 className="text-lg font-semibold mb-4">Connection Test Results</h2>
              {connectionTestResult && (
                <>
                  <div
                    className={`flex items-center p-4 rounded mb-4 ${connectionTestResult.status === 'success' ? 'bg-green-50 border border-green-200 text-green-800' : 'bg-red-50 border border-red-200 text-red-800'}`}
                  >
                    <span className="font-medium">
                      {connectionTestResult.status === 'success'
                        ? 'Connection successful!'
                        : 'Connection failed.'}
                    </span>
                  </div>
                  {connectionTestResult.status === 'success' && connectionTestResult.company && (
                    <div className="mt-2">
                      <div className="font-medium mb-1">Connected to:</div>
                      <div><strong>Company:</strong> {connectionTestResult.company.name}</div>
                      {connectionTestResult.company.vat && (
                        <div><strong>VAT:</strong> {connectionTestResult.company.vat}</div>
                      )}
                      <div><strong>Database:</strong> {connectionConfig.database}</div>
                    </div>
                  )}
                  {connectionTestResult.message && (
                    <div className="text-gray-600 text-sm mt-2">{connectionTestResult.message}</div>
                  )}
                </>
              )}
            </div>
            <div className="mb-4">
              <div className="font-semibold mb-2">Connection Details</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm"><strong>Name:</strong> {connectionConfig.name}</div>
                  <div className="text-sm"><strong>URL:</strong> {connectionConfig.url}</div>
                  <div className="text-sm"><strong>Database:</strong> {connectionConfig.database}</div>
                </div>
                <div>
                  <div className="text-sm"><strong>Username:</strong> {connectionConfig.username}</div>
                  <div className="text-sm"><strong>Authentication:</strong> {connectionConfig.auth_method}</div>
                </div>
                {connectionConfig.description && (
                  <div className="md:col-span-2 text-sm"><strong>Description:</strong> {connectionConfig.description}</div>
                )}
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <DashboardLayout>
      <PageHeader
        title="Add Integration"
        description="Connect your ERP system to TaxPoynt"
        actions={
          <button
            className="inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-gray-700 rounded-md hover:bg-gray-50 transition text-sm font-medium"
            onClick={handleBack}
            type="button"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </button>
        }
      />

      {/* Stepper */}
      <div className="bg-white rounded-md shadow p-6 mb-6">
        <ol className="flex items-center w-full space-x-4">
          {steps.map((label, idx) => (
            <li key={label} className="flex-1 flex items-center">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 ${activeStep >= idx ? 'bg-blue-600 border-blue-600 text-white' : 'bg-white border-gray-300 text-gray-400'}`}>
                {idx + 1}
              </div>
              <span className={`ml-2 text-sm font-medium ${activeStep >= idx ? 'text-blue-700' : 'text-gray-500'}`}>{label}</span>
              {idx !== steps.length - 1 && <div className="flex-1 h-0.5 bg-gray-200 mx-2" />}
            </li>
          ))}
        </ol>
      </div>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} />}

      <div className="bg-white rounded-md shadow p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-2">{steps[activeStep]}</h2>
          <div className="h-px bg-gray-200 w-full" />
        </div>

        <div className="my-6">
          {renderStepContent()}
        </div>

        <div className="flex justify-end space-x-2">
          {activeStep !== 0 && (
            <button
              className="px-4 py-2 rounded-md border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 transition text-sm font-medium"
              onClick={handleBack}
              type="button"
            >
              Back
            </button>
          )}
          <button
            className={`px-4 py-2 rounded-md text-white text-sm font-medium transition ${((activeStep === 0 && !selectedIntegration) || (activeStep === 1 && (!connectionConfig.name || !connectionConfig.url || !connectionConfig.database || !connectionConfig.username || (!connectionConfig.password && connectionConfig.auth_method === 'password')) ) || isSubmitting) ? 'bg-gray-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
            onClick={handleNext}
            disabled={
              (activeStep === 0 && !selectedIntegration) ||
              (activeStep === 1 && (
                !connectionConfig.name || 
                !connectionConfig.url || 
                !connectionConfig.database || 
                !connectionConfig.username ||
                (!connectionConfig.password && connectionConfig.auth_method === 'password')
              )) ||
              isSubmitting
            }
            type="button"
          >
            {activeStep === steps.length - 1 ? 'Save Integration' : 'Next'}
          </button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default AddIntegrationPage;
