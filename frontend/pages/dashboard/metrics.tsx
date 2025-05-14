import React, { useState, useEffect } from 'react';
import DashboardLayout from '../../components/layouts/DashboardLayout';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import EnhancedIRNMetricsCard from '../../components/dashboard/EnhancedIRNMetricsCard';
import ValidationMetricsCard from '../../components/dashboard/ValidationMetricsCard';
import B2BvsB2CMetricsCard from '../../components/dashboard/B2BvsB2CMetricsCard';
import OdooIntegrationMetricsCard from '../../components/dashboard/OdooIntegrationMetricsCard';
import { fetchDashboardSummary, DashboardSummary } from '../../services/dashboardService';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/Select';
import { Input } from '../../components/ui/Input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Download, Filter, RefreshCw, Search } from 'lucide-react';
import { format } from 'date-fns';
import Head from 'next/head';

// Mock organization data for filtering (in a real app, this would come from an API)
const organizations = [
  { id: '1', name: 'Organization 1' },
  { id: '2', name: 'Organization 2' },
  { id: '3', name: 'Organization 3' }
];

const MetricsDashboard: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedOrg, setSelectedOrg] = useState<string | undefined>(undefined);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());

  const fetchSummary = async () => {
    try {
      const data = await fetchDashboardSummary();
      setSummary(data);
    } catch (error) {
      console.error('Failed to fetch dashboard summary:', error);
    }
  };

  useEffect(() => {
    fetchSummary();
    
    // Set up an interval to update the summary every minute
    const intervalId = setInterval(fetchSummary, 60000);
    
    return () => clearInterval(intervalId);
  }, []);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    
    try {
      await fetchSummary();
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error refreshing dashboard data:', error);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
  };

  const handleOrgChange = (value: string) => {
    setSelectedOrg(value === 'all' ? undefined : value);
  };

  const toggleFilters = () => {
    setShowFilters(!showFilters);
  };
  
  const handleExport = () => {
    // Placeholder for export functionality
    alert('Export functionality would generate a report with current dashboard metrics');
  };
  
  // Time range options for the Select
  const timeRangeOptions = [
    { value: '24h', label: '24 Hours' },
    { value: '7d', label: '7 Days' },
    { value: '30d', label: '30 Days' },
    { value: 'all', label: 'All Time' }
  ];

  return (
    <>
      <Head>
        <title>FIRS e-Invoice Dashboard | Metrics</title>
      </Head>
      
      <DashboardLayout>
        <div className="p-6">
          <header className="mb-8">
            <div className="flex flex-wrap justify-between items-center mb-4 gap-4">
              <h1 className="text-2xl font-heading font-semibold">Monitoring Dashboard</h1>
              <div className="flex gap-3">
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={handleRefresh}
                  disabled={isRefreshing}
                >
                  <RefreshCw size={14} className={isRefreshing ? 'animate-spin' : ''} />
                  <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
                </Button>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={toggleFilters}
                >
                  <Filter size={14} />
                  <span>Filter</span>
                </Button>
                <Button 
                  variant="default" 
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={handleExport}
                >
                  <Download size={14} />
                  <span>Export</span>
                </Button>
              </div>
            </div>
            
            {showFilters && (
              <Card className="mb-4">
                <CardContent className="pt-6">
                  <div className="flex flex-wrap gap-4">
                    <div className="flex-1">
                      <label className="text-sm font-medium mb-1 block">Search</label>
                      <div className="relative">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                          placeholder="Search invoices, organizations..."
                          className="pl-8"
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                        />
                      </div>
                    </div>
                    <div className="w-40">
                      <label className="text-sm font-medium mb-1 block">Time Range</label>
                      <Select value={timeRange} onValueChange={handleTimeRangeChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select range" />
                        </SelectTrigger>
                        <SelectContent>
                          {timeRangeOptions.map(option => (
                            <SelectItem key={option.value} value={option.value}>{option.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="w-60">
                      <label className="text-sm font-medium mb-1 block">Organization</label>
                      <Select value={selectedOrg || 'all'} onValueChange={handleOrgChange}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select organization" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Organizations</SelectItem>
                          {organizations.map(org => (
                            <SelectItem key={org.id} value={org.id}>{org.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">Last updated: {format(lastUpdated, 'HH:mm:ss')}</Badge>
              <Badge variant="secondary">Time range: {timeRangeOptions.find(o => o.value === timeRange)?.label}</Badge>
              <Badge variant="outline">
                Organization: {selectedOrg ? organizations.find(o => o.id === selectedOrg)?.name : 'All'}
              </Badge>
            </div>
          </header>

          {/* Summary Stats Cards */}
          {summary && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Total IRNs</div>
                  <div className="text-2xl font-semibold">
                    {summary.irn_summary.total_irns.toLocaleString()}
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {summary.irn_summary.active_irns.toLocaleString()} active
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">Validation Success</div>
                  <div className="text-2xl font-semibold">
                    {summary.validation_summary.success_rate.toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {summary.validation_summary.total_validations.toLocaleString()} total validations
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">B2B vs B2C</div>
                  <div className="text-2xl font-semibold">
                    {summary.b2b_vs_b2c_summary.b2b_percentage.toFixed(1)}% / {summary.b2b_vs_b2c_summary.b2c_percentage.toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    B2B Success: {summary.b2b_vs_b2c_summary.b2b_success_rate.toFixed(1)}%
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="p-4">
                  <div className="text-sm text-muted-foreground">API Health</div>
                  <div className="text-2xl font-semibold">
                    {summary.system_summary.error_rate.toFixed(2)}% errors
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {summary.system_summary.avg_response_time.toFixed(0)}ms avg response
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tabs for different dashboard views */}
          <Tabs defaultValue="all" className="mb-8">
            <TabsList>
              <TabsTrigger value="all">All Metrics</TabsTrigger>
              <TabsTrigger value="validation">Validation</TabsTrigger>
              <TabsTrigger value="integration">Integration</TabsTrigger>
              <TabsTrigger value="irn">IRN Status</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all" className="mt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EnhancedIRNMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <ValidationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <OdooIntegrationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <B2BvsB2CMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
            
            <TabsContent value="validation" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <ValidationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
                <B2BvsB2CMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
            
            <TabsContent value="integration" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <OdooIntegrationMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                  refreshInterval={15000} // More frequent updates for integration status
                />
              </div>
            </TabsContent>
            
            <TabsContent value="irn" className="mt-6">
              <div className="grid grid-cols-1 gap-6">
                <EnhancedIRNMetricsCard 
                  timeRange={timeRange} 
                  organizationId={selectedOrg} 
                />
              </div>
            </TabsContent>
          </Tabs>
        </div>
      </DashboardLayout>
    </>
  );
};

// Wrap the component with ProtectedRoute
const ProtectedMetricsDashboard = () => {
  return (
    <ProtectedRoute>
      <MetricsDashboard />
    </ProtectedRoute>
  );
};

export default ProtectedMetricsDashboard;
