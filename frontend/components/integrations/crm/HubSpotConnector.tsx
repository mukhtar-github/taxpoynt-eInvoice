/**
 * HubSpot CRM Connection Component
 * 
 * This component provides a comprehensive interface for connecting to HubSpot CRM,
 * including OAuth flow initiation, connection testing, and configuration management.
 */

import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { ExternalLink, CheckCircle, AlertCircle, Loader2, Settings, Zap } from 'lucide-react';

import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { FormField } from '@/components/ui/FormField';
import { Switch } from '@/components/ui/Switch';
import { Alert } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Tabs } from '@/components/ui/Tabs';

import CRMService from '@/services/crmService';
import {
  CRMConnection,
  CRMConnectionTestResult,
  HubSpotConnectionConfig,
  ConnectionFormData
} from '@/types/crm';

// ==================== FORM VALIDATION SCHEMA ====================

const hubspotConnectionSchema = yup.object().shape({
  connection_name: yup
    .string()
    .required('Connection name is required')
    .min(3, 'Connection name must be at least 3 characters')
    .max(50, 'Connection name must not exceed 50 characters'),
  client_id: yup
    .string()
    .required('Client ID is required')
    .matches(/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i, 'Invalid HubSpot Client ID format'),
  client_secret: yup
    .string()
    .required('Client Secret is required')
    .min(32, 'Client Secret appears to be too short'),
  webhook_secret: yup
    .string()
    .optional()
    .min(16, 'Webhook secret should be at least 16 characters for security'),
  settings: yup.object().shape({
    auto_sync_deals: yup.boolean().default(true),
    sync_interval_hours: yup.number().min(1).max(24).default(6),
    auto_generate_invoice: yup.boolean().default(false),
    deal_stage_mapping: yup.object().optional()
  })
});

type HubSpotFormData = yup.InferType<typeof hubspotConnectionSchema>;

// ==================== COMPONENT PROPS ====================

interface HubSpotConnectorProps {
  organizationId: string;
  userId?: string;
  existingConnection?: CRMConnection;
  onConnectionSuccess?: (connection: CRMConnection) => void;
  onConnectionError?: (error: string) => void;
  onCancel?: () => void;
  className?: string;
}

// ==================== MAIN COMPONENT ====================

const HubSpotConnector: React.FC<HubSpotConnectorProps> = ({
  organizationId,
  userId,
  existingConnection,
  onConnectionSuccess,
  onConnectionError,
  onCancel,
  className = ''
}) => {
  // ==================== STATE MANAGEMENT ====================
  
  const [isConnecting, setIsConnecting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<CRMConnectionTestResult | null>(null);
  const [oauthStep, setOauthStep] = useState<'config' | 'oauth' | 'complete'>('config');
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('basic');

  // ==================== FORM SETUP ====================

  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    watch,
    setValue,
    getValues
  } = useForm<HubSpotFormData>({
    resolver: yupResolver(hubspotConnectionSchema),
    defaultValues: {
      connection_name: existingConnection?.connection_name || 'HubSpot CRM',
      client_id: '',
      client_secret: '',
      webhook_secret: '',
      settings: {
        auto_sync_deals: true,
        sync_interval_hours: 6,
        auto_generate_invoice: false,
        deal_stage_mapping: {}
      }
    },
    mode: 'onChange'
  });

  // ==================== EFFECT HOOKS ====================

  useEffect(() => {
    // Check if we're returning from OAuth flow
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      setConnectionError(`OAuth error: ${error}`);
      setOauthStep('config');
    } else if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, []);

  // ==================== OAUTH FLOW HANDLERS ====================

  const initiateOAuthFlow = () => {
    const state = CRMService.generateOAuthState();
    const redirectUri = `${window.location.origin}/dashboard/integrations/hubspot/callback`;
    
    // Store form data temporarily
    sessionStorage.setItem('hubspot_form_data', JSON.stringify(getValues()));
    sessionStorage.setItem('hubspot_oauth_state', state);
    
    // Redirect to HubSpot OAuth
    const oauthUrl = CRMService.initiateHubSpotOAuth(redirectUri, state);
    window.location.href = oauthUrl;
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    try {
      setIsConnecting(true);
      setOauthStep('oauth');

      // Validate state
      const storedState = sessionStorage.getItem('hubspot_oauth_state');
      if (state !== storedState) {
        throw new Error('Invalid OAuth state parameter');
      }

      // Restore form data
      const storedFormData = sessionStorage.getItem('hubspot_form_data');
      if (storedFormData) {
        const formData = JSON.parse(storedFormData);
        Object.entries(formData).forEach(([key, value]) => {
          setValue(key as keyof HubSpotFormData, value);
        });
      }

      // Exchange code for tokens
      const redirectUri = `${window.location.origin}/dashboard/integrations/hubspot/callback`;
      const tokens = await CRMService.exchangeHubSpotCode(code, redirectUri, state);

      // Create connection with tokens
      await createConnection(tokens);

      // Clean up
      sessionStorage.removeItem('hubspot_form_data');
      sessionStorage.removeItem('hubspot_oauth_state');
      
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);

    } catch (error: any) {
      console.error('OAuth callback error:', error);
      setConnectionError(error.message || 'OAuth flow failed');
      setOauthStep('config');
    } finally {
      setIsConnecting(false);
    }
  };

  // ==================== CONNECTION HANDLERS ====================

  const createConnection = async (tokens?: any) => {
    try {
      setIsConnecting(true);
      setConnectionError(null);

      const formData = getValues();
      
      const connectionData = {
        crm_type: 'hubspot' as const,
        connection_name: formData.connection_name,
        credentials: {
          auth_type: 'oauth2',
          client_id: formData.client_id,
          client_secret: formData.client_secret,
          ...(tokens && {
            access_token: tokens.access_token,
            refresh_token: tokens.refresh_token,
            token_expires_at: new Date(Date.now() + tokens.expires_in * 1000).toISOString()
          })
        },
        connection_settings: formData.settings,
        webhook_secret: formData.webhook_secret
      };

      const connection = await CRMService.connectPlatform('hubspot', connectionData);
      
      setOauthStep('complete');
      onConnectionSuccess?.(connection);

    } catch (error: any) {
      console.error('Connection creation error:', error);
      const errorMessage = error.response?.data?.message || error.message || 'Failed to create connection';
      setConnectionError(errorMessage);
      onConnectionError?.(errorMessage);
    } finally {
      setIsConnecting(false);
    }
  };

  const testConnection = async () => {
    try {
      setIsTesting(true);
      setTestResult(null);

      const formData = getValues();
      
      const config: HubSpotConnectionConfig = {
        organization_id: organizationId,
        user_id: userId,
        connection_name: formData.connection_name,
        auth: {
          auth_type: 'oauth2',
          token_url: 'https://api.hubapi.com/oauth/v1/token',
          scope: 'crm.objects.deals.read crm.objects.contacts.read crm.objects.companies.read',
          credentials: {
            auth_type: 'oauth2',
            client_id: formData.client_id,
            client_secret: formData.client_secret
          }
        },
        settings: formData.settings
      };

      const result = await CRMService.testHubSpotConnection(config);
      setTestResult(result);

    } catch (error: any) {
      console.error('Connection test error:', error);
      setTestResult({
        success: false,
        message: error.response?.data?.message || error.message || 'Connection test failed',
        error_details: error.response?.data
      });
    } finally {
      setIsTesting(false);
    }
  };

  // ==================== FORM SUBMISSION ====================

  const onSubmit = (data: HubSpotFormData) => {
    if (existingConnection) {
      // Update existing connection
      // This would call CRMService.updateConnection()
      console.log('Update connection:', data);
    } else {
      // Start OAuth flow for new connection
      initiateOAuthFlow();
    }
  };

  // ==================== RENDER HELPERS ====================

  const renderBasicConfig = () => (
    <div className="space-y-6">
      <FormField
        label="Connection Name"
        error={errors.connection_name?.message}
        required
      >
        <Controller
          name="connection_name"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              placeholder="My HubSpot CRM"
              disabled={isConnecting}
            />
          )}
        />
      </FormField>

      <FormField
        label="HubSpot Client ID"
        error={errors.client_id?.message}
        required
        description="Found in your HubSpot app settings"
      >
        <Controller
          name="client_id"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              type="password"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              disabled={isConnecting}
            />
          )}
        />
      </FormField>

      <FormField
        label="HubSpot Client Secret"
        error={errors.client_secret?.message}
        required
        description="Keep this secret secure"
      >
        <Controller
          name="client_secret"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              type="password"
              placeholder="Enter your client secret"
              disabled={isConnecting}
            />
          )}
        />
      </FormField>

      <div className="flex gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={testConnection}
          disabled={!isValid || isTesting || isConnecting}
          loading={isTesting}
        >
          {isTesting ? 'Testing...' : 'Test Connection'}
        </Button>
        
        {testResult && (
          <div className="flex items-center gap-2">
            {testResult.success ? (
              <Badge variant="success" className="flex items-center gap-1">
                <CheckCircle className="w-3 h-3" />
                Connected
              </Badge>
            ) : (
              <Badge variant="error" className="flex items-center gap-1">
                <AlertCircle className="w-3 h-3" />
                Failed
              </Badge>
            )}
          </div>
        )}
      </div>

      {testResult && !testResult.success && (
        <Alert variant="error">
          <AlertCircle className="w-4 h-4" />
          <div>
            <p className="font-medium">Connection Test Failed</p>
            <p className="text-sm">{testResult.message}</p>
          </div>
        </Alert>
      )}
    </div>
  );

  const renderAdvancedSettings = () => (
    <div className="space-y-6">
      <FormField
        label="Webhook Secret"
        error={errors.webhook_secret?.message}
        description="Optional secret for webhook verification"
      >
        <Controller
          name="webhook_secret"
          control={control}
          render={({ field }) => (
            <Input
              {...field}
              type="password"
              placeholder="Enter webhook secret (optional)"
              disabled={isConnecting}
            />
          )}
        />
      </FormField>

      <div className="space-y-4">
        <h4 className="font-medium text-sm">Synchronization Settings</h4>
        
        <FormField label="Auto-sync deals">
          <Controller
            name="settings.auto_sync_deals"
            control={control}
            render={({ field: { value, onChange } }) => (
              <Switch
                checked={value}
                onCheckedChange={onChange}
                disabled={isConnecting}
              />
            )}
          />
        </FormField>

        <FormField
          label="Sync Interval (hours)"
          description="How often to sync deals from HubSpot"
        >
          <Controller
            name="settings.sync_interval_hours"
            control={control}
            render={({ field }) => (
              <Input
                {...field}
                type="number"
                min="1"
                max="24"
                disabled={isConnecting}
              />
            )}
          />
        </FormField>

        <FormField label="Auto-generate invoices">
          <Controller
            name="settings.auto_generate_invoice"
            control={control}
            render={({ field: { value, onChange } }) => (
              <Switch
                checked={value}
                onCheckedChange={onChange}
                disabled={isConnecting}
              />
            )}
          />
        </FormField>
      </div>
    </div>
  );

  // ==================== MAIN RENDER ====================

  if (oauthStep === 'oauth') {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">Completing HubSpot Connection</h3>
          <p className="text-sm text-gray-600">
            Processing OAuth authorization...
          </p>
        </CardContent>
      </Card>
    );
  }

  if (oauthStep === 'complete') {
    return (
      <Card className={className}>
        <CardContent className="text-center py-8">
          <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2">HubSpot Connected Successfully!</h3>
          <p className="text-sm text-gray-600 mb-4">
            Your HubSpot CRM is now connected and ready to sync deals.
          </p>
          <Button onClick={() => setOauthStep('config')}>
            Configure Settings
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader
        title="Connect to HubSpot CRM"
        subtitle="Integrate with HubSpot to sync deals and generate invoices automatically"
        action={
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-orange-500" />
            <span className="text-sm font-medium text-orange-600">OAuth 2.0</span>
          </div>
        }
      />

      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <Tabs
            value={activeTab}
            onValueChange={setActiveTab}
            tabs={[
              { id: 'basic', label: 'Basic Configuration' },
              { id: 'advanced', label: 'Advanced Settings' }
            ]}
          >
            <div className="mt-6">
              {activeTab === 'basic' && renderBasicConfig()}
              {activeTab === 'advanced' && renderAdvancedSettings()}
            </div>
          </Tabs>

          {connectionError && (
            <Alert variant="error">
              <AlertCircle className="w-4 h-4" />
              <div>
                <p className="font-medium">Connection Error</p>
                <p className="text-sm">{connectionError}</p>
              </div>
            </Alert>
          )}
        </form>
      </CardContent>

      <CardFooter>
        <div className="flex justify-between w-full">
          <Button
            variant="outline"
            onClick={() => window.open('https://developers.hubspot.com/docs/api/crm/deals', '_blank')}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            HubSpot Docs
          </Button>
          
          <Button
            onClick={handleSubmit(onSubmit)}
            disabled={!isValid || isConnecting}
            loading={isConnecting}
          >
            {existingConnection ? 'Update Connection' : 'Connect to HubSpot'}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
};

export default HubSpotConnector;