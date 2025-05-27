import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import CompanyDashboardLayout from '../../components/layouts/CompanyDashboardLayout';
import { Typography } from '../../components/ui/Typography';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Input } from '../../components/ui/Input';
import { FormField } from '../../components/ui/FormField';
import { Spinner } from '../../components/ui/Spinner';
import { Badge } from '../../components/ui/Badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Database, RefreshCw, CheckCircle, AlertCircle } from 'lucide-react';

// Form validation schema
const odooConnectionSchema = yup.object().shape({
  url: yup.string().url('Must be a valid URL').required('URL is required'),
  database: yup.string().required('Database name is required'),
  username: yup.string().required('Username is required'),
  password: yup.string().required('Password is required'),
  auth_method: yup.string().oneOf(['password', 'api_key']).required(),
});

// Interface for Odoo connection form
interface OdooConnectionForm {
  url: string;
  database: string;
  username: string;
  password: string;
  auth_method: 'password' | 'api_key';
}

// Interface for connection status
interface ConnectionStatus {
  connected: boolean;
  last_sync: string | null;
  details: {
    company_name?: string;
    user_name?: string;
    version?: string;
    database?: string;
  };
  error?: string;
}

const ERPConnectionPage = () => {
  // State management
  const [activeTab, setActiveTab] = useState('odoo');
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testSuccess, setTestSuccess] = useState<boolean | null>(null);
  const [testMessage, setTestMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Mock connection status
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);

  // React Hook Form for Odoo connection
  const { 
    register, 
    handleSubmit, 
    formState: { errors }, 
    setValue,
    reset
  } = useForm<OdooConnectionForm>({
    resolver: yupResolver(odooConnectionSchema),
    defaultValues: {
      auth_method: 'password',
    }
  });

  // Check for existing connection on load
  useEffect(() => {
    const checkConnection = async () => {
      try {
        setIsLoading(true);
        
        // Simulate API call to check connection
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // For demo purposes - pretend we have a connection for MT Garba Global Ventures
        const mockConnection: ConnectionStatus = {
          connected: true,
          last_sync: "2025-05-26T14:30:00Z",
          details: {
            company_name: "MT Garba Global Ventures",
            user_name: "admin",
            version: "Odoo 16.0",
            database: "mtgarba_prod"
          }
        };
        
        setConnectionStatus(mockConnection);
        
        // Pre-fill the form with existing connection details
        setValue("url", "https://mtgarba.odoo.com");
        setValue("database", "mtgarba_prod");
        setValue("username", "admin");
        setValue("password", "********"); // Placeholder for security
        
      } catch (err) {
        console.error('Error checking connection:', err);
        setConnectionStatus(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkConnection();
  }, [setValue]);

  // Test connection
  const testConnection = async (data: OdooConnectionForm) => {
    try {
      setIsTesting(true);
      setTestSuccess(null);
      setTestMessage(null);
      
      // Simulate API call to test connection
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Simulate success (in a real app, this would be based on the API response)
      setTestSuccess(true);
      setTestMessage("Successfully connected to Odoo. Company: MT Garba Global Ventures");
      
    } catch (err) {
      console.error('Error testing connection:', err);
      setTestSuccess(false);
      setTestMessage("Connection failed. Please check your credentials.");
    } finally {
      setIsTesting(false);
    }
  };

  // Save connection
  const saveConnection = async (data: OdooConnectionForm) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call to save connection
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update connection status with new data
      setConnectionStatus({
        connected: true,
        last_sync: new Date().toISOString(),
        details: {
          company_name: "MT Garba Global Ventures",
          user_name: data.username,
          version: "Odoo 16.0",
          database: data.database
        }
      });
      
      // Show success message
      setSuccess("Odoo connection saved successfully!");
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error saving connection:', err);
      setError("Failed to save connection. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Sync data
  const syncData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Simulate API call to sync data
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Update last sync time
      setConnectionStatus(prev => prev ? {
        ...prev,
        last_sync: new Date().toISOString()
      } : null);
      
      // Show success message
      setSuccess("Data synchronized successfully!");
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error syncing data:', err);
      setError("Failed to synchronize data. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  // Format date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  return (
    <CompanyDashboardLayout title="ERP Connection | TaxPoynt eInvoice">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <Typography.Heading level="h1" className="mb-2">
              ERP Connection
            </Typography.Heading>
            <Typography.Text className="text-gray-500">
              Connect your ERP system to automatically sync invoices, customers, and products
            </Typography.Text>
          </div>
          
          {connectionStatus?.connected && (
            <Badge variant="success" className="text-sm">
              Connected
            </Badge>
          )}
        </div>
        
        {/* Error and success alerts */}
        {error && (
          <Alert variant="error" className="mb-6">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert variant="success" className="mb-6">
            {success}
          </Alert>
        )}
        
        {isLoading && !connectionStatus ? (
          <div className="flex justify-center items-center h-64">
            <Spinner size="lg" />
            <span className="ml-3">Checking connection status...</span>
          </div>
        ) : (
          <>
            {/* Current Connection Status */}
            {connectionStatus?.connected && (
              <Card className="mb-8">
                <CardContent className="p-6">
                  <div className="flex items-start space-x-4">
                    <div className="bg-green-100 p-3 rounded-full">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <Typography.Heading level="h2" className="mb-2">
                        Connected to {connectionStatus.details.company_name}
                      </Typography.Heading>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">Database: </span>
                          <span className="font-medium">{connectionStatus.details.database}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">User: </span>
                          <span className="font-medium">{connectionStatus.details.user_name}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Version: </span>
                          <span className="font-medium">{connectionStatus.details.version}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Last Sync: </span>
                          <span className="font-medium">{formatDate(connectionStatus.last_sync)}</span>
                        </div>
                      </div>
                      <div className="mt-4 flex space-x-3">
                        <Button
                          variant="default"
                          className="flex items-center"
                          onClick={syncData}
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <>
                              <Spinner size="sm" className="mr-2" />
                              Syncing...
                            </>
                          ) : (
                            <>
                              <RefreshCw className="h-4 w-4 mr-2" />
                              Sync Now
                            </>
                          )}
                        </Button>
                        <Button
                          variant="outline"
                          onClick={() => setConnectionStatus(null)}
                        >
                          Disconnect
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Connection Configuration */}
            <Tabs defaultValue="odoo" onValueChange={setActiveTab} value={activeTab}>
              <TabsList className="mb-6">
                <TabsTrigger value="odoo">Odoo</TabsTrigger>
                <TabsTrigger value="sap" disabled>SAP (Coming Soon)</TabsTrigger>
                <TabsTrigger value="quickbooks" disabled>QuickBooks (Coming Soon)</TabsTrigger>
              </TabsList>
              
              <TabsContent value="odoo">
                <Card>
                  <CardHeader>
                    <div className="flex items-center">
                      <Database className="h-5 w-5 mr-2 text-indigo-600" />
                      <Typography.Heading level="h2">
                        Odoo Connection
                      </Typography.Heading>
                    </div>
                    <Typography.Text className="text-gray-500">
                      Connect to your Odoo instance to synchronize data
                    </Typography.Text>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleSubmit(saveConnection)} className="space-y-6">
                      <FormField
                        label="Odoo URL"
                        error={!!errors.url}
                        errorMessage={errors.url?.message}
                      >
                        <Input
                          id="url"
                          placeholder="https://yourdomain.odoo.com"
                          {...register('url')}
                        />
                      </FormField>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <FormField
                          label="Database Name"
                          error={!!errors.database}
                          errorMessage={errors.database?.message}
                        >
                          <Input
                            id="database"
                            placeholder="production_db"
                            {...register('database')}
                          />
                        </FormField>
                        
                        <FormField
                          label="Authentication Method"
                          error={!!errors.auth_method}
                          errorMessage={errors.auth_method?.message}
                        >
                          <select
                            id="auth_method"
                            className="w-full px-3 py-2 border border-gray-300 rounded-md"
                            {...register('auth_method')}
                          >
                            <option value="password">Password</option>
                            <option value="api_key">API Key</option>
                          </select>
                        </FormField>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <FormField
                          label="Username"
                          error={!!errors.username}
                          errorMessage={errors.username?.message}
                        >
                          <Input
                            id="username"
                            placeholder="admin"
                            {...register('username')}
                          />
                        </FormField>
                        
                        <FormField
                          label="Password / API Key"
                          error={!!errors.password}
                          errorMessage={errors.password?.message}
                        >
                          <Input
                            id="password"
                            type="password"
                            placeholder="••••••••"
                            {...register('password')}
                          />
                        </FormField>
                      </div>
                      
                      {/* Test connection results */}
                      {testSuccess !== null && (
                        <div className={`p-4 rounded-lg ${testSuccess ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                          <div className="flex items-center">
                            {testSuccess ? (
                              <CheckCircle className="h-5 w-5 mr-2" />
                            ) : (
                              <AlertCircle className="h-5 w-5 mr-2" />
                            )}
                            <Typography.Text className="font-medium">
                              {testMessage}
                            </Typography.Text>
                          </div>
                        </div>
                      )}
                      
                      <div className="flex justify-end space-x-3">
                        <Button
                          type="button"
                          variant="outline"
                          onClick={handleSubmit(testConnection)}
                          disabled={isTesting}
                        >
                          {isTesting ? (
                            <>
                              <Spinner size="sm" className="mr-2" />
                              Testing...
                            </>
                          ) : (
                            'Test Connection'
                          )}
                        </Button>
                        
                        <Button
                          type="submit"
                          disabled={isLoading}
                        >
                          {isLoading ? (
                            <>
                              <Spinner size="sm" className="mr-2" />
                              Saving...
                            </>
                          ) : (
                            'Save Connection'
                          )}
                        </Button>
                      </div>
                    </form>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          </>
        )}
      </div>
    </CompanyDashboardLayout>
  );
};

export default ERPConnectionPage;
