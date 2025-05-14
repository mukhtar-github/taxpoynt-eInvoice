import React, { useState } from 'react';
import { AlertCircle, CheckCircle, Loader } from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import axios, { AxiosError } from 'axios';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '../ui/Card';
import { Input } from '../ui/Input';
import { Label } from '../ui/Label';
import { LegacySelect } from '../ui/Select';
import { Switch } from '../ui/Switch';
import { Divider } from '../ui/Divider';

type OdooAuthMethod = 'password' | 'api_key';
type SyncFrequency = 'realtime' | 'hourly' | 'daily' | 'weekly';

interface OdooConfig {
  url: string;
  database: string;
  username: string;
  auth_method: OdooAuthMethod;
  password?: string;
  api_key?: string;
  version: string;
  rpc_path: string;
  timeout: number;
  sync_frequency: SyncFrequency;
}

interface OdooIntegrationFormProps {
  clientId: string;
  onSuccess?: (integration: any) => void;
  onCancel?: () => void;
}

const OdooIntegrationForm: React.FC<OdooIntegrationFormProps> = ({
  clientId,
  onSuccess,
  onCancel,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{
    success: boolean;
    message: string;
    details?: any;
  } | null>(null);

  const { register, handleSubmit, watch, control, formState: { errors } } = useForm<{
    name: string;
    description: string;
    odoo_config: OdooConfig;
  }>({
    defaultValues: {
      name: '',
      description: '',
      odoo_config: {
        url: '',
        database: '',
        username: '',
        auth_method: 'api_key',
        password: '',
        api_key: '',
        version: '16.0',
        rpc_path: '/jsonrpc',
        timeout: 30,
        sync_frequency: 'hourly',
      },
    },
  });

  const authMethod = watch('odoo_config.auth_method');

  const onSubmit = async (data: any) => {
    try {
      setIsLoading(true);
      
      // Prepare the payload
      const payload = {
        client_id: clientId,
        name: data.name,
        description: data.description,
        odoo_config: data.odoo_config,
        sync_frequency: data.odoo_config.sync_frequency,
      };
      
      // Send API request to create integration
      const response = await axios.post('/api/v1/integrations/odoo', payload);
      
      // Show success notification
      showNotification('Integration created', 'Odoo integration was created successfully.', 'success');
      
      // Call success callback if provided
      if (onSuccess) {
        onSuccess(response.data);
      }
    } catch (error: unknown) {
      console.error('Error creating integration:', error);
      // Show error notification
      const errorMessage = 
        error instanceof AxiosError 
          ? error.response?.data?.detail || 'Failed to create integration.'
          : 'Failed to create integration.';
      showNotification('Error', errorMessage, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Helper function for notifications since we don't have Chakra's useToast
  const showNotification = (title: string, message: string, type: 'success' | 'error') => {
    // This would be replaced with your preferred notification system
    // For now we'll just log to console
    console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
    // You might want to implement a toast/notification system here
  };

  const testConnection = async () => {
    try {
      setIsTesting(true);
      setTestResult(null);
      
      const formData = watch();
      
      // Prepare test connection payload
      const payload = {
        url: formData.odoo_config.url,
        database: formData.odoo_config.database,
        username: formData.odoo_config.username,
        auth_method: formData.odoo_config.auth_method,
        password: formData.odoo_config.auth_method === 'password' ? formData.odoo_config.password : undefined,
        api_key: formData.odoo_config.auth_method === 'api_key' ? formData.odoo_config.api_key : undefined,
      };
      
      // Send API request to test connection
      const response = await axios.post('/api/v1/integrations/odoo/test-connection', payload);
      
      setTestResult(response.data);
      
      // Show notification
      showNotification(
        response.data.success ? 'Connection Successful' : 'Connection Failed',
        response.data.message,
        response.data.success ? 'success' : 'error'
      );
    } catch (error) {
      console.error('Error testing connection:', error);
      const axiosError = error as AxiosError;
      setTestResult({
        success: false,
        message: (axiosError.response?.data as any)?.detail || 'Failed to test connection.',
      });
      
      // Show error notification
      showNotification('Error', (axiosError.response?.data as any)?.detail || 'Failed to test connection.', 'error');
    } finally {
      setIsTesting(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>New Odoo Integration</CardTitle>
        <CardDescription>
          Connect to your Odoo instance using JSON-RPC to synchronize invoices for e-Invoicing.
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)}>
        <CardContent className="space-y-4">
          <Divider />
          
          <div className="space-y-2">
            <Label htmlFor="name" isRequired>Integration Name</Label>
            <Input
              id="name"
              {...register('name', { required: 'Name is required' })}
              placeholder="e.g., Company Odoo"
              error={!!errors.name}
            />
            {errors.name && (
              <p className="text-sm text-error mt-1">{errors.name.message}</p>
            )}
            <p className="text-sm text-text-secondary">
              A descriptive name for this integration
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Input
              id="description"
              {...register('description')}
              placeholder="e.g., Production Odoo instance for invoice synchronization"
            />
            <p className="text-sm text-text-secondary">
              Optional description for this integration
            </p>
          </div>
          
          <div>
            <Divider />
            <h3 className="text-lg font-semibold mt-4">Odoo Connection Details</h3>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="url" isRequired>Odoo URL</Label>
            <Input
              id="url"
              {...register('odoo_config.url', { required: 'URL is required' })}
              placeholder="https://example.odoo.com"
              error={!!errors.odoo_config?.url}
            />
            {errors.odoo_config?.url && (
              <p className="text-sm text-error mt-1">{errors.odoo_config.url.message}</p>
            )}
            <p className="text-sm text-text-secondary">
              The URL of your Odoo instance
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="database" isRequired>Database Name</Label>
            <Input
              id="database"
              {...register('odoo_config.database', { required: 'Database name is required' })}
              placeholder="your-database"
              error={!!errors.odoo_config?.database}
            />
            {errors.odoo_config?.database && (
              <p className="text-sm text-error mt-1">{errors.odoo_config.database.message}</p>
            )}
            <p className="text-sm text-text-secondary">
              The database name of your Odoo instance
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="username" isRequired>Username</Label>
            <Input
              id="username"
              {...register('odoo_config.username', { required: 'Username is required' })}
              placeholder="admin@example.com"
              error={!!errors.odoo_config?.username}
            />
            {errors.odoo_config?.username && (
              <p className="text-sm text-error mt-1">{errors.odoo_config.username.message}</p>
            )}
            <p className="text-sm text-text-secondary">
              Username (usually email) for authentication
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="auth_method" isRequired>Authentication Method</Label>
            <Controller
              name="odoo_config.auth_method"
              control={control}
              render={({ field }) => (
                <LegacySelect id="auth_method" {...field}>
                  <option value="api_key">API Key (Recommended)</option>
                  <option value="password">Password</option>
                </LegacySelect>
              )}
            />
            <p className="text-sm text-text-secondary">
              Select how to authenticate with Odoo
            </p>
          </div>
          
          {authMethod === 'password' ? (
            <div className="space-y-2">
              <Label htmlFor="password" isRequired>Password</Label>
              <Input
                id="password"
                type="password"
                {...register('odoo_config.password', {
                  required: authMethod === 'password' ? 'Password is required' : false,
                })}
                error={!!errors.odoo_config?.password}
              />
              {errors.odoo_config?.password && (
                <p className="text-sm text-error mt-1">{errors.odoo_config.password.message}</p>
              )}
              <p className="text-sm text-text-secondary">
                Your Odoo user password
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <Label htmlFor="api_key" isRequired>API Key</Label>
              <Input
                id="api_key"
                type="password"
                {...register('odoo_config.api_key', {
                  required: authMethod === 'api_key' ? 'API key is required' : false,
                })}
                error={!!errors.odoo_config?.api_key}
              />
              {errors.odoo_config?.api_key && (
                <p className="text-sm text-error mt-1">{errors.odoo_config.api_key.message}</p>
              )}
              <p className="text-sm text-text-secondary">
                API key generated from your Odoo user profile (Settings → Account Security → API Keys)
              </p>
            </div>
          )}
          
          <div>
            <Divider />
            <h3 className="text-lg font-semibold mt-4">Advanced Settings</h3>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="version">Odoo Version</Label>
            <Controller
              name="odoo_config.version"
              control={control}
              render={({ field }) => (
                <LegacySelect id="version" {...field}>
                  <option value="17.0">17.0</option>
                  <option value="16.0">16.0</option>
                  <option value="15.0">15.0</option>
                  <option value="14.0">14.0</option>
                </LegacySelect>
              )}
            />
            <p className="text-sm text-text-secondary">
              The version of your Odoo instance
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="rpc_path">RPC Path</Label>
            <Controller
              name="odoo_config.rpc_path"
              control={control}
              render={({ field }) => (
                <LegacySelect id="rpc_path" {...field}>
                  <option value="/jsonrpc">JSON-RPC (/jsonrpc)</option>
                  <option value="/xmlrpc/2/common">XML-RPC (/xmlrpc/2/common)</option>
                </LegacySelect>
              )}
            />
            <p className="text-sm text-text-secondary">
              The RPC endpoint path
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="sync_frequency">Sync Frequency</Label>
            <Controller
              name="odoo_config.sync_frequency"
              control={control}
              render={({ field }) => (
                <LegacySelect id="sync_frequency" {...field}>
                  <option value="realtime">Near Real-time (every 15 minutes)</option>
                  <option value="hourly">Hourly</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </LegacySelect>
              )}
            />
            <p className="text-sm text-text-secondary">
              How frequently invoices should be synced from Odoo
            </p>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="timeout">Connection Timeout (seconds)</Label>
            <Input
              id="timeout"
              type="number"
              {...register('odoo_config.timeout', {
                valueAsNumber: true,
                min: 5,
                max: 120,
              })}
              defaultValue={30}
            />
            <p className="text-sm text-text-secondary">
              Timeout for API requests in seconds
            </p>
          </div>
          
          {testResult && (
            <div
              className={`mt-4 p-4 rounded-md ${
                testResult.success 
                  ? 'bg-success bg-opacity-10 border border-success'
                  : 'bg-error bg-opacity-10 border border-error'
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                {testResult.success ? (
                  <CheckCircle className="h-5 w-5 text-success" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-error" />
                )}
                <h4 className="text-base font-medium">
                  {testResult.success ? 'Connection Successful' : 'Connection Failed'}
                </h4>
              </div>
              <p className="text-sm">
                {testResult.message}
              </p>
              {testResult.details && (
                <div className="mt-2 text-sm">
                  <p className="font-medium">Details:</p>
                  <pre className="bg-background-alt p-2 rounded-sm mt-1 overflow-x-auto">
                    {JSON.stringify(testResult.details, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </CardContent>
        
        <CardFooter className="flex flex-col sm:flex-row sm:justify-between gap-4">
          <Button
            variant="outline"
            type="button"
            onClick={testConnection}
            disabled={isTesting}
            className="w-full sm:w-auto"
          >
            {isTesting ? (
              <>
                <Loader className="mr-2 h-4 w-4 animate-spin" />
                Testing...
              </>
            ) : (
              'Test Connection'
            )}
          </Button>
          
          <div className="flex gap-2 w-full sm:w-auto">
            <Button
              variant="ghost"
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1 sm:flex-none"
            >
              Cancel
            </Button>
            
            <Button
              type="submit"
              disabled={isLoading || !testResult?.success}
              className="flex-1 sm:flex-none"
            >
              {isLoading ? (
                <>
                  <Loader className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Integration'
              )}
            </Button>
          </div>
        </CardFooter>
      </form>
    </Card>
  );
};

export default OdooIntegrationForm;
