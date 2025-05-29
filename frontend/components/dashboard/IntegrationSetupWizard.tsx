import React, { useState } from 'react';
import { useForm, Controller, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { CheckCircle, AlertCircle, AlertTriangle, Loader2 } from 'lucide-react';
import { IntegrationService } from '../../services/api/integrationService';
import { IntegrationResponse } from '../../services/api/types';
import { cn } from '../../utils/cn';

// Define step types
type WizardStep = 'connectionDetails' | 'testConnection' | 'configureSummary';

// Define connection form schema
const connectionDetailsSchema = yup.object<ConnectionFormData>().shape({
  url: yup.string().required('Odoo URL is required').url('Must be a valid URL'),
  database: yup.string().required('Database name is required'),
  auth_method: yup.string().required('Authentication method is required'),
  username: yup.string().when('auth_method', {
    is: (val: string | Array<string>) => val === 'password' || (Array.isArray(val) && val[0] === 'password'),
    then: () => yup.string().required('Username is required'),
    otherwise: () => yup.string().optional()
  }),
  password: yup.string().when('auth_method', {
    is: (val: string | Array<string>) => val === 'password' || (Array.isArray(val) && val[0] === 'password'),
    then: () => yup.string().required('Password is required'),
    otherwise: () => yup.string().optional()
  }),
  api_key: yup.string().when('auth_method', {
    is: (val: string | Array<string>) => val === 'api_key' || (Array.isArray(val) && val[0] === 'api_key'),
    then: () => yup.string().required('API key is required'),
    otherwise: () => yup.string().optional()
  })
}) as yup.ObjectSchema<ConnectionFormData>;

// Type for form data
type ConnectionFormData = {
  url: string;
  database: string;
  auth_method: string;
  username?: string;
  password?: string;
  api_key?: string;
};

// Integration setup wizard component props
interface IntegrationSetupWizardProps {
  organizationId: string;
  onComplete: () => void;
}

export const IntegrationSetupWizard: React.FC<IntegrationSetupWizardProps> = ({
  organizationId,
  onComplete
}) => {
  // State for the current wizard step
  const [currentStep, setCurrentStep] = useState<WizardStep>('connectionDetails');
  
  // State for form data
  const [formData, setFormData] = useState<ConnectionFormData | null>(null);
  
  // State for integration ID (after creation)
  const [integrationId, setIntegrationId] = useState<string | null>(null);
  
  // State for connection test results
  const [connectionTest, setConnectionTest] = useState<{
    status: 'pending' | 'success' | 'error';
    message: string;
  }>({
    status: 'pending',
    message: ''
  });

  // State for loading states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  
  // Initialize form
  const { register, handleSubmit, watch, formState: { errors } } = useForm<ConnectionFormData>({
    resolver: yupResolver(connectionDetailsSchema),
    defaultValues: {
      auth_method: 'password'
    }
  });
  
  // Watch authentication method to show/hide fields
  const authMethod = watch('auth_method');
  
  // Handle form submission for connection details
  const onSubmitConnectionDetails = (data: ConnectionFormData) => {
    setIsSubmitting(true);
    setFormData(data);
    
    // Fix for the expected 2 arguments error (ID: 4ccd6914-caef-4c9b-9343-5061cfaf6fbf)
    IntegrationService.createIntegration(organizationId, {
      name: 'Odoo Integration',
      description: 'Odoo Integration',
      integration_type: 'odoo',
      config: {
        url: data.url,
        database: data.database,
        auth_method: data.auth_method,
        ...(data.auth_method === 'password' && {
          username: data.username,
          password: data.password
        }),
        ...(data.auth_method === 'api_key' && {
          api_key: data.api_key
        })
      }
    })
      .then(response => {
        // Fix for property 'id' not existing on IntegrationResponse (ID: 615b668e-be6c-405e-9f38-5dc61791a1cb)
        setIntegrationId(response && typeof response === 'object' ? (response as any).id : null);
        setCurrentStep('testConnection');
      })
      .catch(error => {
        // Show error message
        console.error('Error creating integration:', error);
      })
      .finally(() => {
        setIsSubmitting(false);
      });
  };
  
  // Handle connection test
  const handleTestConnection = () => {
    if (!integrationId) return;
    
    setIsTesting(true);
    setConnectionTest({
      status: 'pending',
      message: 'Testing connection...'
    });
    
    // Fix for property 'testIntegration' not existing (ID: 33f4423a-0605-4a87-8627-a627e973e7c5)
    // The testConnection method requires organizationId, integrationType, and config parameters
    IntegrationService.testConnection(
      organizationId, 
      'odoo', // Assuming 'odoo' as the integration type based on our form
      formData || {}
    )
      .then(response => {
        setConnectionTest({
          status: response.status === 'success' ? 'success' : 'error',
          message: response.message
        });
      })
      .catch(error => {
        setConnectionTest({
          status: 'error',
          message: error.message || 'Failed to test connection'
        });
      })
      .finally(() => {
        setIsTesting(false);
      });
  };
  
  // Go to next step
  const handleNext = () => {
    if (currentStep === 'connectionDetails') {
      setCurrentStep('testConnection');
    } else if (currentStep === 'testConnection') {
      setCurrentStep('configureSummary');
    }
  };
  
  // Go to previous step
  const handleBack = () => {
    if (currentStep === 'testConnection') {
      setCurrentStep('connectionDetails');
    } else if (currentStep === 'configureSummary') {
      setCurrentStep('testConnection');
    }
  };
  
  // Complete the setup
  const handleFinish = () => {
    onComplete();
  };
  
  // Define the submit handler with proper typing
  const onSubmit: SubmitHandler<ConnectionFormData> = (data) => {
    onSubmitConnectionDetails(data);
  };
  
  // Render connection details step
  const renderConnectionDetailsStep = () => (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" data-cy="step-connection-details">
      <h2 className="text-xl font-semibold mb-4">Connection Details</h2>
      
      <div className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="url" className="block text-sm font-medium">
            Odoo URL
          </label>
          <input
            id="url"
            type="text"
            placeholder="https://example.odoo.com"
            className={cn(
              "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
              errors.url ? "border-red-500" : "border-gray-300"
            )}
            {...register('url')}
            data-cy="input-odoo-url"
          />
          {errors.url && (
            <p className="mt-1 text-sm text-red-500">{errors.url.message}</p>
          )}
        </div>
        
        <div className="space-y-2">
          <label htmlFor="database" className="block text-sm font-medium">
            Database Name
          </label>
          <input
            id="database"
            type="text"
            placeholder="your_database"
            className={cn(
              "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
              errors.database ? "border-red-500" : "border-gray-300"
            )}
            {...register('database')}
            data-cy="input-database"
          />
          {errors.database && (
            <p className="mt-1 text-sm text-red-500">{errors.database.message}</p>
          )}
        </div>
        
        <div className="space-y-2">
          <label htmlFor="auth_method" className="block text-sm font-medium">
            Authentication Method
          </label>
          <select
            id="auth_method"
            className={cn(
              "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
              errors.auth_method ? "border-red-500" : "border-gray-300"
            )}
            {...register('auth_method')}
            data-cy="select-auth-method"
          >
            <option value="password">Username & Password</option>
            <option value="api_key">API Key</option>
          </select>
          {errors.auth_method && (
            <p className="mt-1 text-sm text-red-500">{errors.auth_method.message}</p>
          )}
        </div>
        
        {authMethod === 'password' && (
          <>
            <div className="space-y-2">
              <label htmlFor="username" className="block text-sm font-medium">
                Username
              </label>
              <input
                id="username"
                type="text"
                className={cn(
                  "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                  errors.username ? "border-red-500" : "border-gray-300"
                )}
                {...register('username')}
                data-cy="input-username"
              />
              {errors.username && (
                <p className="mt-1 text-sm text-red-500">{errors.username.message}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <label htmlFor="password" className="block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                className={cn(
                  "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                  errors.password ? "border-red-500" : "border-gray-300"
                )}
                {...register('password')}
                data-cy="input-password"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-500">{errors.password.message}</p>
              )}
            </div>
          </>
        )}
        
        {authMethod === 'api_key' && (
          <div className="space-y-2">
            <label htmlFor="api_key" className="block text-sm font-medium">
              API Key
            </label>
            <input
              id="api_key"
              type="password"
              className={cn(
                "w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500",
                errors.api_key ? "border-red-500" : "border-gray-300"
              )}
              {...register('api_key')}
              data-cy="input-api-key"
            />
            {errors.api_key && (
              <p className="mt-1 text-sm text-red-500">{errors.api_key.message}</p>
            )}
          </div>
        )}
      </div>
      
      <div className="flex justify-end mt-6">
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          disabled={isSubmitting}
          data-cy="next-button"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : (
            'Next'
          )}
        </button>
      </div>
    </form>
  );
  
  // Render test connection step
  const renderTestConnectionStep = () => (
    <div className="space-y-6" data-cy="step-test-connection">
      <h2 className="text-xl font-semibold mb-4">Test Connection</h2>
      
      <p className="text-gray-600 mb-4">
        Test your connection to make sure everything is configured correctly.
      </p>
      
      {connectionTest.status === 'pending' && connectionTest.message && (
        <div className="p-4 border-l-4 border-blue-500 bg-blue-50 rounded" role="alert">
          <div className="flex">
            <Loader2 className="h-5 w-5 text-blue-500 mr-3 animate-spin" />
            <p className="text-sm text-blue-700">{connectionTest.message}</p>
          </div>
        </div>
      )}
      
      {connectionTest.status === 'success' && (
        <div className="p-4 border-l-4 border-green-500 bg-green-50 rounded" role="alert" data-cy="connection-success-message">
          <div className="flex">
            <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
            <div>
              <p className="font-medium text-green-800">Success!</p>
              <p className="text-sm text-green-700">{connectionTest.message}</p>
            </div>
          </div>
        </div>
      )}
      
      {connectionTest.status === 'error' && (
        <div className="p-4 border-l-4 border-red-500 bg-red-50 rounded" role="alert" data-cy="connection-error-message">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-red-500 mr-3" />
            <div>
              <p className="font-medium text-red-800">Error!</p>
              <p className="text-sm text-red-700">{connectionTest.message}</p>
            </div>
          </div>
        </div>
      )}
      
      <div className="flex justify-between mt-6">
        <button
          type="button"
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          onClick={handleBack}
          data-cy="back-button"
        >
          Back
        </button>
        
        <div className="space-x-2">
          <button
            type="button"
            className={cn(
              "px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50",
              connectionTest.status === 'success' ? "bg-gray-600 hover:bg-gray-700" : "bg-blue-600 hover:bg-blue-700"
            )}
            onClick={handleTestConnection}
            disabled={isTesting}
            data-cy="test-connection-button"
          >
            {isTesting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </button>
          
          {connectionTest.status === 'error' && (
            <button
              type="button"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
              onClick={handleTestConnection}
              data-cy="retry-button"
            >
              Retry
            </button>
          )}
          
          <button
            type="button"
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
            onClick={handleNext}
            disabled={connectionTest.status !== 'success'}
            data-cy="next-button"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
  
  // Render configuration summary step
  const renderConfigurationSummaryStep = () => (
    <div className="space-y-6" data-cy="step-configuration-summary">
      <h2 className="text-xl font-semibold mb-4">Configuration Summary</h2>
      
      <div className="p-4 border border-gray-200 rounded-md mb-6">
        <h3 className="font-semibold mb-2">Odoo Integration</h3>
        
        <dl className="divide-y divide-gray-200">
          <div className="py-2 grid grid-cols-3">
            <dt className="font-medium text-gray-700">URL:</dt>
            <dd className="col-span-2 text-gray-900">{formData?.url}</dd>
          </div>
          
          <div className="py-2 grid grid-cols-3">
            <dt className="font-medium text-gray-700">Database:</dt>
            <dd className="col-span-2 text-gray-900">{formData?.database}</dd>
          </div>
          
          <div className="py-2 grid grid-cols-3">
            <dt className="font-medium text-gray-700">Auth Method:</dt>
            <dd className="col-span-2 text-gray-900">
              {formData?.auth_method === 'password' ? 'Username & Password' : 'API Key'}
            </dd>
          </div>
          
          {formData?.auth_method === 'password' && (
            <div className="py-2 grid grid-cols-3">
              <dt className="font-medium text-gray-700">Username:</dt>
              <dd className="col-span-2 text-gray-900">{formData?.username}</dd>
            </div>
          )}
        </dl>
      </div>
      
      <div className="p-4 border-l-4 border-green-500 bg-green-50 rounded" role="alert">
        <div className="flex">
          <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
          <div>
            <p className="font-medium text-green-800">Connection Verified</p>
            <p className="text-sm text-green-700">
              Your Odoo connection has been successfully configured and tested.
            </p>
          </div>
        </div>
      </div>
      
      <div className="flex justify-between mt-6">
        <button
          type="button"
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          onClick={handleBack}
        >
          Back
        </button>
        
        <button
          type="button"
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          onClick={handleFinish}
          data-cy="finish-button"
        >
          Finish
        </button>
      </div>
    </div>
  );
  
  return (
    <div 
      className="max-w-3xl mx-auto p-6 border border-gray-200 rounded-lg shadow-sm bg-white"
      data-cy="integration-setup-wizard"
    >
      <h1 className="text-2xl font-bold mb-6">Connect to Odoo</h1>
      
      <div className="h-px bg-gray-200 mb-6"></div>
      
      {currentStep === 'connectionDetails' && renderConnectionDetailsStep()}
      {currentStep === 'testConnection' && renderTestConnectionStep()}
      {currentStep === 'configureSummary' && renderConfigurationSummaryStep()}
    </div>
  );
};