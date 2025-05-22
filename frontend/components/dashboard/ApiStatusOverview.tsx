import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Typography } from '../ui/Typography';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui/Tabs';
import { AlertCircle, CheckCircle2, AlertTriangle, Server, Database, RefreshCw } from 'lucide-react';
import { Button } from '../ui/Button';
import { Skeleton } from '../../components/ui/Skeleton';
import { IntegrationStatusResponse, fetchAllIntegrationStatus } from '../../services/integrationStatusService';

const ApiStatusOverview: React.FC = () => {
  const [integrationStatus, setIntegrationStatus] = useState<IntegrationStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefreshed, setLastRefreshed] = useState<Date>(new Date());

  // Fetch integration status data
  const fetchStatus = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAllIntegrationStatus();
      setIntegrationStatus(data);
      setLastRefreshed(new Date());
    } catch (err) {
      setError('Failed to fetch integration status');
      console.error('Error fetching integration status:', err);
    } finally {
      setLoading(false);
    }
  };

  // Initial fetch
  useEffect(() => {
    fetchStatus();
    
    // Set up auto-refresh every 5 minutes
    const intervalId = setInterval(fetchStatus, 5 * 60 * 1000);
    
    // Clean up on component unmount
    return () => clearInterval(intervalId);
  }, []);

  // Get status badge variant based on status
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'operational':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'error':
      case 'critical':
        return 'destructive';
      default:
        return 'secondary';
    }
  };

  // Get status icon based on status
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'operational':
        return <CheckCircle2 className="h-4 w-4 text-success-500" />;
      case 'degraded':
        return <AlertTriangle className="h-4 w-4 text-warning-500" />;
      case 'error':
      case 'critical':
        return <AlertCircle className="h-4 w-4 text-destructive-500" />;
      default:
        return <Server className="h-4 w-4 text-secondary-500" />;
    }
  };

  // Format percentage
  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  if (loading && !integrationStatus) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>API & Integration Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && !integrationStatus) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>API & Integration Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-destructive-50 p-4 rounded-md border border-destructive-200">
            <Typography.Text className="text-destructive-700">{error}</Typography.Text>
          </div>
          <Button
            variant="outline"
            className="mt-4"
            onClick={fetchStatus}
            disabled={loading}
          >
            Try Again
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>API & Integration Status</CardTitle>
        <div className="flex items-center space-x-2">
          <Typography.Text size="xs" variant="secondary">
            Last updated: {lastRefreshed.toLocaleTimeString()}
          </Typography.Text>
          <Button
            size="sm"
            variant="ghost"
            onClick={fetchStatus}
            disabled={loading}
            className="h-8 w-8 p-0"
            title="Refresh"
          >
            <RefreshCw className="h-4 w-4" />
            <span className="sr-only">Refresh</span>
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        ) : integrationStatus ? (
          <div className="space-y-6">
            {/* System Status Overview */}
            <div className="flex justify-between items-center">
              <div>
                <Typography.Text size="sm" variant="secondary">System Status</Typography.Text>
                <div className="flex items-center mt-1">
                  {getStatusIcon(integrationStatus.system_status)}
                  <Typography.Text size="lg" weight="medium" className="ml-1">
                    {integrationStatus.system_status.charAt(0).toUpperCase() + integrationStatus.system_status.slice(1)}
                  </Typography.Text>
                </div>
              </div>
              <Badge variant={getStatusBadgeVariant(integrationStatus.system_status)}>
                {integrationStatus.system_status === 'operational' ? 'All Systems Operational' : 
                 integrationStatus.system_status === 'degraded' ? 'Some Systems Degraded' : 
                 'System Issues Detected'}
              </Badge>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Odoo Integration Status */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Database className="h-5 w-5 text-primary-500 mr-2" />
                    <Typography.Text weight="medium">Odoo Integration</Typography.Text>
                  </div>
                  <Badge variant={getStatusBadgeVariant(integrationStatus.odoo_integration.status)}>
                    {integrationStatus.odoo_integration.status.charAt(0).toUpperCase() + 
                     integrationStatus.odoo_integration.status.slice(1)}
                  </Badge>
                </div>
                
                <div className="mt-3">
                  <Typography.Text size="sm" className="text-muted-foreground">
                    {integrationStatus.odoo_integration.message}
                  </Typography.Text>
                </div>

                {integrationStatus.odoo_integration.integrations.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <Typography.Text size="sm" weight="medium">Active Connections</Typography.Text>
                    {integrationStatus.odoo_integration.integrations.map((integration) => (
                      <div key={integration.id} className="flex justify-between items-center">
                        <Typography.Text size="sm">{integration.name}</Typography.Text>
                        <div className="flex items-center">
                          {getStatusIcon(integration.status)}
                          <Typography.Text size="sm" className="ml-1">
                            {integration.status === 'operational' && integration.submission_stats && 
                             `${formatPercentage(integration.submission_stats.success_rate)} Success Rate`}
                            {integration.status !== 'operational' && integration.error && 
                             `Error: ${integration.error.substring(0, 30)}${integration.error.length > 30 ? '...' : ''}`}
                          </Typography.Text>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* FIRS API Status */}
              <div className="border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Server className="h-5 w-5 text-primary-500 mr-2" />
                    <Typography.Text weight="medium">FIRS API</Typography.Text>
                  </div>
                  <Badge variant={getStatusBadgeVariant(integrationStatus.firs_api.status)}>
                    {integrationStatus.firs_api.status.charAt(0).toUpperCase() + 
                     integrationStatus.firs_api.status.slice(1)}
                  </Badge>
                </div>
                
                <div className="mt-2 grid grid-cols-2 gap-2">
                  <div className="p-2 bg-secondary-50 rounded-md">
                    <Typography.Text size="xs" variant="secondary">Sandbox</Typography.Text>
                    <div className="flex items-center mt-1">
                      {integrationStatus.firs_api.sandbox_available ? 
                        <CheckCircle2 className="h-4 w-4 text-success-500" /> : 
                        <AlertCircle className="h-4 w-4 text-destructive-500" />}
                      <Typography.Text size="sm" className="ml-1">
                        {integrationStatus.firs_api.sandbox_available ? 'Available' : 'Unavailable'}
                      </Typography.Text>
                    </div>
                  </div>
                  <div className="p-2 bg-secondary-50 rounded-md">
                    <Typography.Text size="xs" variant="secondary">Production</Typography.Text>
                    <div className="flex items-center mt-1">
                      {integrationStatus.firs_api.production_available ? 
                        <CheckCircle2 className="h-4 w-4 text-success-500" /> : 
                        <AlertCircle className="h-4 w-4 text-destructive-500" />}
                      <Typography.Text size="sm" className="ml-1">
                        {integrationStatus.firs_api.production_available ? 'Available' : 'Unavailable'}
                      </Typography.Text>
                    </div>
                  </div>
                </div>

                {integrationStatus.firs_api.submission_stats && (
                  <div className="mt-3">
                    <Typography.Text size="sm" weight="medium">Last 24 Hours</Typography.Text>
                    <div className="grid grid-cols-3 gap-2 mt-1">
                      <div className="p-2 bg-secondary-50 rounded-md">
                        <Typography.Text size="xs" variant="secondary">Total Submissions</Typography.Text>
                        <Typography.Text size="sm" weight="medium" className="block">
                          {integrationStatus.firs_api.submission_stats.total_24h}
                        </Typography.Text>
                      </div>
                      <div className="p-2 bg-success-50 rounded-md">
                        <Typography.Text size="xs" variant="secondary">Success</Typography.Text>
                        <Typography.Text size="sm" weight="medium" className="block">
                          {integrationStatus.firs_api.submission_stats.success_24h}
                        </Typography.Text>
                      </div>
                      <div className="p-2 bg-warning-50 rounded-md">
                        <Typography.Text size="xs" variant="secondary">Failed</Typography.Text>
                        <Typography.Text size="sm" weight="medium" className="block">
                          {integrationStatus.firs_api.submission_stats.failed_24h}
                        </Typography.Text>
                      </div>
                    </div>
                    <div className="mt-2">
                      <div className="w-full bg-secondary-100 rounded-full h-2.5">
                        <div 
                          className="bg-success-500 h-2.5 rounded-full" 
                          style={{ width: `${integrationStatus.firs_api.submission_stats.success_rate}%` }}
                        ></div>
                      </div>
                      <div className="flex justify-between mt-1">
                        <Typography.Text size="xs" variant="secondary">Success Rate</Typography.Text>
                        <Typography.Text size="xs" weight="medium">
                          {formatPercentage(integrationStatus.firs_api.submission_stats.success_rate)}
                        </Typography.Text>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Recent Errors Section */}
            {integrationStatus.firs_api.recent_errors && integrationStatus.firs_api.recent_errors.length > 0 && (
              <div className="mt-4">
                <Typography.Text size="sm" weight="medium" className="mb-2 block">Recent Errors</Typography.Text>
                <div className="border rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-secondary-200">
                    <thead className="bg-secondary-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500 tracking-wider">Timestamp</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500 tracking-wider">Status</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-secondary-500 tracking-wider">Error Message</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-secondary-100">
                      {integrationStatus.firs_api.recent_errors.map((error) => (
                        <tr key={error.id}>
                          <td className="px-4 py-2 text-xs text-secondary-500">
                            {new Date(error.timestamp).toLocaleString()}
                          </td>
                          <td className="px-4 py-2">
                            <Badge variant={error.status === 'failed' ? 'destructive' : 'warning'} className="capitalize">
                              {error.status}
                            </Badge>
                          </td>
                          <td className="px-4 py-2 text-xs text-secondary-700">
                            {error.error_message.substring(0, 50)}{error.error_message.length > 50 ? '...' : ''}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
};

export default ApiStatusOverview;
