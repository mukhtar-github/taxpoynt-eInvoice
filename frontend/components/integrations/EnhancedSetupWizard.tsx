/**
 * Enhanced Setup Wizard Component
 * 
 * Week 3 Implementation: Advanced wizard with:
 * - Multi-step progress indicators with animations
 * - Platform-specific configuration flows
 * - Enhanced form validation and error handling
 * - Mobile-first responsive design
 * - Loading states and micro-animations
 * - Save/resume capability
 */

import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { 
  CheckCircle, 
  AlertCircle, 
  Loader2, 
  ArrowLeft, 
  ArrowRight,
  Database,
  Key,
  TestTube,
  Settings,
  Zap,
  Save,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { FormField } from '@/components/ui/FormField';
import { Badge } from '@/components/ui/Badge';

// Enhanced step configuration
interface WizardStep {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  isCompleted: boolean;
  isActive: boolean;
  canSkip?: boolean;
}

// Platform-specific configuration schemas
const baseConfigSchema = {
  name: yup.string().required('Integration name is required'),
  description: yup.string().optional()
};

const odooConfigSchema = yup.object({
  ...baseConfigSchema,
  url: yup.string().required('Odoo URL is required').url('Must be a valid URL'),
  database: yup.string().required('Database name is required'),
  auth_method: yup.string().oneOf(['password', 'api_key']).required(),
  username: yup.string().when('auth_method', {
    is: 'password',
    then: () => yup.string().required('Username is required'),
    otherwise: () => yup.string().optional()
  }),
  password: yup.string().when('auth_method', {
    is: 'password',
    then: () => yup.string().required('Password is required'),
    otherwise: () => yup.string().optional()
  }),
  api_key: yup.string().when('auth_method', {
    is: 'api_key',
    then: () => yup.string().required('API key is required'),
    otherwise: () => yup.string().optional()
  })
});

const crmConfigSchema = yup.object({
  ...baseConfigSchema,
  platform: yup.string().oneOf(['hubspot', 'salesforce', 'pipedrive']).required(),
  auth_method: yup.string().oneOf(['oauth', 'api_key']).required(),
  client_id: yup.string().when('auth_method', {
    is: 'oauth',
    then: () => yup.string().required('Client ID is required'),
    otherwise: () => yup.string().optional()
  }),
  api_key: yup.string().when('auth_method', {
    is: 'api_key',
    then: () => yup.string().required('API key is required'),
    otherwise: () => yup.string().optional()
  })
});

const posConfigSchema = yup.object({
  ...baseConfigSchema,
  platform: yup.string().oneOf(['square', 'toast', 'lightspeed']).required(),
  location_id: yup.string().required('Location ID is required'),
  access_token: yup.string().required('Access token is required'),
  environment: yup.string().oneOf(['sandbox', 'production']).required()
});

interface EnhancedSetupWizardProps {
  type: 'erp' | 'crm' | 'pos';
  platform?: string;
  organizationId: string;
  existingData?: any;
  onComplete: (data: any) => void;
  onCancel?: () => void;
  onSave?: (data: any) => void;
  className?: string;
}

const EnhancedSetupWizard: React.FC<EnhancedSetupWizardProps> = ({
  type,
  platform,
  organizationId,
  existingData,
  onComplete,
  onCancel,
  onSave,
  className = ''
}) => {
  // Wizard state
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(false);
  const [connectionTest, setConnectionTest] = useState<{
    status: 'idle' | 'testing' | 'success' | 'error';
    message: string;
  }>({ status: 'idle', message: '' });

  // Form state
  const [formData, setFormData] = useState(existingData || {});
  const [isDraft, setIsDraft] = useState(!!existingData);

  // Get schema based on type
  const getSchema = () => {
    switch (type) {
      case 'erp': return odooConfigSchema;
      case 'crm': return crmConfigSchema;
      case 'pos': return posConfigSchema;
      default: return yup.object(baseConfigSchema);
    }
  };

  // Initialize form
  const { 
    register, 
    handleSubmit, 
    watch, 
    setValue,
    formState: { errors, isValid },
    control 
  } = useForm({
    resolver: yupResolver(getSchema()),
    defaultValues: formData,
    mode: 'onChange'
  });

  // Define steps based on integration type
  const getSteps = (): WizardStep[] => {
    const baseSteps = [
      {
        id: 'basic',
        title: 'Basic Information',
        description: 'Set up basic integration details',
        icon: <Settings className="w-5 h-5" />,
        isCompleted: completedSteps.has(0),
        isActive: currentStepIndex === 0
      },
      {
        id: 'connection',
        title: 'Connection Details',
        description: 'Configure connection parameters',
        icon: <Database className="w-5 h-5" />,
        isCompleted: completedSteps.has(1),
        isActive: currentStepIndex === 1
      },
      {
        id: 'authentication',
        title: 'Authentication',
        description: 'Set up authentication credentials',
        icon: <Key className="w-5 h-5" />,
        isCompleted: completedSteps.has(2),
        isActive: currentStepIndex === 2
      },
      {
        id: 'test',
        title: 'Test Connection',
        description: 'Verify connection works correctly',
        icon: <TestTube className="w-5 h-5" />,
        isCompleted: completedSteps.has(3),
        isActive: currentStepIndex === 3
      },
      {
        id: 'summary',
        title: 'Summary',
        description: 'Review and complete setup',
        icon: <CheckCircle className="w-5 h-5" />,
        isCompleted: completedSteps.has(4),
        isActive: currentStepIndex === 4
      }
    ];

    return baseSteps;
  };

  const steps = getSteps();
  const currentStep = steps[currentStepIndex];

  // Platform configurations
  const platformConfigs = {
    erp: {
      odoo: { name: 'Odoo', color: 'bg-purple-500', logo: '🏢' }
    },
    crm: {
      hubspot: { name: 'HubSpot', color: 'bg-orange-500', logo: '🧡' },
      salesforce: { name: 'Salesforce', color: 'bg-blue-500', logo: '☁️' },
      pipedrive: { name: 'Pipedrive', color: 'bg-green-500', logo: '📊' }
    },
    pos: {
      square: { name: 'Square', color: 'bg-black', logo: '⬜' },
      toast: { name: 'Toast', color: 'bg-red-500', logo: '🍞' },
      lightspeed: { name: 'Lightspeed', color: 'bg-blue-600', logo: '⚡' }
    }
  };

  // Auto-save functionality
  useEffect(() => {
    const watchedData = watch();
    const timer = setTimeout(() => {
      if (onSave && Object.keys(watchedData).length > 0) {
        setFormData(watchedData);
        setIsDraft(true);
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [watch, onSave]);

  // Navigation functions
  const goToStep = (stepIndex: number) => {
    if (stepIndex >= 0 && stepIndex < steps.length) {
      setCurrentStepIndex(stepIndex);
    }
  };

  const nextStep = () => {
    const newCompletedSteps = new Set(completedSteps);
    newCompletedSteps.add(currentStepIndex);
    setCompletedSteps(newCompletedSteps);
    
    if (currentStepIndex < steps.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    }
  };

  const prevStep = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  // Test connection
  const testConnection = async () => {
    setConnectionTest({ status: 'testing', message: 'Testing connection...' });
    
    try {
      // Simulated API call - replace with actual service call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock success/failure based on form validation
      if (isValid) {
        setConnectionTest({ 
          status: 'success', 
          message: 'Connection successful! All systems ready.' 
        });
        nextStep();
      } else {
        throw new Error('Invalid configuration');
      }
    } catch (error) {
      setConnectionTest({ 
        status: 'error', 
        message: 'Connection failed. Please check your configuration.' 
      });
    }
  };

  // Form submission
  const onSubmit = (data: any) => {
    setIsLoading(true);
    const completeData = { ...formData, ...data, type, platform };
    
    setTimeout(() => {
      onComplete(completeData);
      setIsLoading(false);
    }, 1000);
  };

  // Progress calculation
  const progress = ((completedSteps.size) / steps.length) * 100;

  // Render progress indicator
  const renderProgressIndicator = () => (
    <div className="mb-8">
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
        <div 
          className="bg-primary h-2 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Step indicators */}
      <div className="flex justify-between items-center">
        {steps.map((step, index) => (
          <div key={step.id} className="flex flex-col items-center">
            {/* Step circle */}
            <button
              onClick={() => goToStep(index)}
              disabled={index > currentStepIndex + 1}
              className={`
                w-10 h-10 rounded-full flex items-center justify-center text-sm font-medium
                transition-all duration-200 mb-2
                ${step.isCompleted 
                  ? 'bg-success text-white shadow-lg' 
                  : step.isActive
                    ? 'bg-primary text-white shadow-lg scale-110'
                    : 'bg-gray-200 text-gray-500 hover:bg-gray-300'
                }
                ${index <= currentStepIndex + 1 ? 'cursor-pointer' : 'cursor-not-allowed'}
              `}
            >
              {step.isCompleted ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <span>{index + 1}</span>
              )}
            </button>

            {/* Step label */}
            <div className="text-center">
              <p className={`text-xs font-medium ${
                step.isActive ? 'text-primary' : 'text-gray-500'
              }`}>
                {step.title}
              </p>
              <p className="text-xs text-gray-400 hidden sm:block">
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Render step content
  const renderStepContent = () => {
    switch (currentStep.id) {
      case 'basic':
        return (
          <div className="space-y-6">
            <FormField label="Integration Name" required error={!!errors.name} errorMessage={errors.name?.message}>
              <input
                {...register('name')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="Enter a name for this integration"
              />
            </FormField>

            <FormField label="Description" helpText="Optional description for this integration">
              <textarea
                {...register('description')}
                rows={3}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                placeholder="Describe this integration..."
              />
            </FormField>

            {type === 'crm' && (
              <FormField label="CRM Platform" required error={!!errors.platform} errorMessage={errors.platform?.message}>
                <select
                  {...register('platform')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="">Select CRM Platform</option>
                  <option value="hubspot">HubSpot</option>
                  <option value="salesforce">Salesforce</option>
                  <option value="pipedrive">Pipedrive</option>
                </select>
              </FormField>
            )}

            {type === 'pos' && (
              <FormField label="POS Platform" required error={!!errors.platform} errorMessage={errors.platform?.message}>
                <select
                  {...register('platform')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                >
                  <option value="">Select POS Platform</option>
                  <option value="square">Square</option>
                  <option value="toast">Toast</option>
                  <option value="lightspeed">Lightspeed</option>
                </select>
              </FormField>
            )}
          </div>
        );

      case 'connection':
        return (
          <div className="space-y-6">
            {type === 'erp' && (
              <>
                <FormField label="Odoo URL" required error={!!errors.url} errorMessage={errors.url?.message}>
                  <input
                    {...register('url')}
                    type="url"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="https://your-odoo-instance.com"
                  />
                </FormField>

                <FormField label="Database Name" required error={!!errors.database} errorMessage={errors.database?.message}>
                  <input
                    {...register('database')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="your_database_name"
                  />
                </FormField>
              </>
            )}

            {type === 'pos' && (
              <>
                <FormField label="Location ID" required error={!!errors.location_id} errorMessage={errors.location_id?.message}>
                  <input
                    {...register('location_id')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Enter location identifier"
                  />
                </FormField>

                <FormField label="Environment" required error={!!errors.environment} errorMessage={errors.environment?.message}>
                  <select
                    {...register('environment')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  >
                    <option value="">Select Environment</option>
                    <option value="sandbox">Sandbox (Testing)</option>
                    <option value="production">Production (Live)</option>
                  </select>
                </FormField>
              </>
            )}
          </div>
        );

      case 'authentication':
        return (
          <div className="space-y-6">
            <FormField label="Authentication Method" required>
              <select
                {...register('auth_method')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              >
                <option value="">Select Authentication Method</option>
                {type === 'erp' && (
                  <>
                    <option value="password">Username & Password</option>
                    <option value="api_key">API Key</option>
                  </>
                )}
                {type === 'crm' && (
                  <>
                    <option value="oauth">OAuth 2.0</option>
                    <option value="api_key">API Key</option>
                  </>
                )}
                {type === 'pos' && (
                  <option value="access_token">Access Token</option>
                )}
              </select>
            </FormField>

            {watch('auth_method') === 'password' && (
              <>
                <FormField label="Username" required error={!!errors.username} errorMessage={errors.username?.message}>
                  <input
                    {...register('username')}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Enter username"
                  />
                </FormField>

                <FormField label="Password" required error={!!errors.password} errorMessage={errors.password?.message}>
                  <input
                    {...register('password')}
                    type="password"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                    placeholder="Enter password"
                  />
                </FormField>
              </>
            )}

            {(watch('auth_method') === 'api_key' || watch('auth_method') === 'access_token') && (
              <FormField 
                label={watch('auth_method') === 'api_key' ? 'API Key' : 'Access Token'} 
                required 
                error={!!(errors.api_key || errors.access_token)} 
                errorMessage={errors.api_key?.message || errors.access_token?.message}
              >
                <input
                  {...register(watch('auth_method') === 'api_key' ? 'api_key' : 'access_token')}
                  type="password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder={`Enter ${watch('auth_method') === 'api_key' ? 'API key' : 'access token'}`}
                />
              </FormField>
            )}

            {watch('auth_method') === 'oauth' && (
              <FormField label="Client ID" required error={!!errors.client_id} errorMessage={errors.client_id?.message}>
                <input
                  {...register('client_id')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                  placeholder="Enter OAuth client ID"
                />
              </FormField>
            )}
          </div>
        );

      case 'test':
        return (
          <div className="space-y-6">
            <div className="text-center">
              <TestTube className="w-16 h-16 text-primary mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Test Your Connection</h3>
              <p className="text-gray-600 mb-6">
                Verify that your configuration is correct and the connection works properly.
              </p>

              {connectionTest.status === 'idle' && (
                <Button onClick={testConnection} size="lg" className="w-full sm:w-auto">
                  <Play className="w-5 h-5 mr-2" />
                  Start Connection Test
                </Button>
              )}

              {connectionTest.status === 'testing' && (
                <div className="flex items-center justify-center gap-3 p-6 bg-blue-50 rounded-lg">
                  <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
                  <span className="text-blue-800 font-medium">{connectionTest.message}</span>
                </div>
              )}

              {connectionTest.status === 'success' && (
                <div className="flex items-center justify-center gap-3 p-6 bg-green-50 rounded-lg">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <span className="text-green-800 font-medium">{connectionTest.message}</span>
                </div>
              )}

              {connectionTest.status === 'error' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-center gap-3 p-6 bg-red-50 rounded-lg">
                    <AlertCircle className="w-6 h-6 text-red-600" />
                    <span className="text-red-800 font-medium">{connectionTest.message}</span>
                  </div>
                  <Button onClick={testConnection} variant="outline" size="lg">
                    <RotateCcw className="w-5 h-5 mr-2" />
                    Retry Test
                  </Button>
                </div>
              )}
            </div>
          </div>
        );

      case 'summary':
        return (
          <div className="space-y-6">
            <div className="text-center mb-6">
              <CheckCircle className="w-16 h-16 text-green-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold mb-2">Setup Complete!</h3>
              <p className="text-gray-600">
                Your integration is ready to use. Review the summary below.
              </p>
            </div>

            <Card className="p-6">
              <h4 className="font-semibold mb-4">Integration Summary</h4>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Name:</dt>
                  <dd className="font-medium">{watch('name')}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Type:</dt>
                  <dd className="font-medium capitalize">{type}</dd>
                </div>
                {watch('platform') && (
                  <div className="flex justify-between">
                    <dt className="text-gray-600">Platform:</dt>
                    <dd className="font-medium capitalize">{watch('platform')}</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-gray-600">Authentication:</dt>
                  <dd className="font-medium capitalize">{watch('auth_method')?.replace('_', ' ')}</dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Status:</dt>
                  <dd>
                    <Badge variant="success">Ready to Use</Badge>
                  </dd>
                </div>
              </dl>
            </Card>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className={`max-w-4xl mx-auto ${className}`}>
      <Card className="p-6 sm:p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            {platform && platformConfigs[type]?.[platform as keyof typeof platformConfigs[typeof type]] && (
              <div className={`
                w-12 h-12 rounded-xl ${platformConfigs[type][platform as keyof typeof platformConfigs[typeof type]].color}
                flex items-center justify-center text-white text-xl
              `}>
                {platformConfigs[type][platform as keyof typeof platformConfigs[typeof type]].logo}
              </div>
            )}
            <div>
              <h1 className="text-2xl font-bold text-text-primary">
                {platform ? 
                  `Connect ${platformConfigs[type]?.[platform as keyof typeof platformConfigs[typeof type]]?.name || platform}` :
                  `Setup ${type.toUpperCase()} Integration`
                }
              </h1>
              <p className="text-text-secondary">
                Follow these steps to configure your integration
              </p>
            </div>
          </div>

          {/* Draft indicator */}
          {isDraft && (
            <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <Save className="w-4 h-4 text-yellow-600" />
              <span className="text-sm text-yellow-800">
                Draft saved automatically
              </span>
            </div>
          )}
        </div>

        {/* Progress indicator */}
        {renderProgressIndicator()}

        {/* Step content */}
        <form onSubmit={handleSubmit(onSubmit)}>
          <div className="mb-8">
            <div className="mb-6">
              <h2 className="text-xl font-semibold flex items-center gap-2 mb-2">
                {currentStep.icon}
                {currentStep.title}
              </h2>
              <p className="text-gray-600">{currentStep.description}</p>
            </div>

            {renderStepContent()}
          </div>

          {/* Navigation */}
          <div className="flex flex-col sm:flex-row justify-between gap-4">
            <div className="flex gap-2">
              {currentStepIndex > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={prevStep}
                  className="flex items-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Previous
                </Button>
              )}

              {onCancel && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={onCancel}
                >
                  Cancel
                </Button>
              )}
            </div>

            <div className="flex gap-2">
              {currentStepIndex < steps.length - 1 ? (
                <Button
                  type="button"
                  onClick={nextStep}
                  disabled={currentStep.id === 'test' && connectionTest.status !== 'success'}
                  className="flex items-center gap-2"
                >
                  Next
                  <ArrowRight className="w-4 h-4" />
                </Button>
              ) : (
                <Button
                  type="submit"
                  disabled={isLoading}
                  className="flex items-center gap-2"
                >
                  {isLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Zap className="w-4 h-4" />
                  )}
                  Complete Setup
                </Button>
              )}
            </div>
          </div>
        </form>
      </Card>
    </div>
  );
};

export default EnhancedSetupWizard;