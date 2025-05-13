import React, { useState, useEffect } from 'react';
import DashboardLayout from '../components/layouts/DashboardLayout';
import IRNStatusMonitor, { IRNStatusItem } from '../components/dashboard/IRNStatusMonitor';
import IntegrationStatus, { IntegrationItem } from '../components/dashboard/IntegrationStatus';
import TransactionMetrics, { TransactionMetricsData } from '../components/dashboard/TransactionMetrics';
import { createDataset } from '../components/ui/Charts';
import { Card, CardHeader, CardContent, CardTitle, CardDescription } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Download, Filter, RefreshCw, Link, BarChart, PieChart, FileBarChart, Activity } from 'lucide-react';
import { Select } from '../components/ui/Select';
import { fetchDashboardSummary, DashboardSummary } from '../services/dashboardService';
import B2BvsB2CMetricsCard from '../components/dashboard/B2BvsB2CMetricsCard';
import Head from 'next/head';
import EnhancedIRNMetricsCard from '../components/dashboard/EnhancedIRNMetricsCard';
import ValidationMetricsCard from '../components/dashboard/ValidationMetricsCard';
import OdooIntegrationMetricsCard from '../components/dashboard/OdooIntegrationMetricsCard';
import NextLink from 'next/link';
import axios, { AxiosError } from 'axios';

// Mock data for the dashboard
const mockIRNStatusData = {
  recentItems: [
    {
      id: '1',
      invoiceNumber: 'INV-3847',
      status: 'completed',
      timestamp: '10 minutes ago',
      businessName: 'TechNova Solutions',
    },
    {
      id: '2',
      invoiceNumber: 'INV-3846',
      status: 'failed',
      timestamp: '25 minutes ago',
      businessName: 'GlobeX Financials',
      errorMessage: 'Invalid invoice format: Missing required field "taxAmount"',
    },
    {
      id: '3',
      invoiceNumber: 'INV-3845',
      status: 'processing',
      timestamp: '30 minutes ago',
      businessName: 'Quantum Industries',
    },
    {
      id: '4',
      invoiceNumber: 'INV-3844',
      status: 'completed',
      timestamp: '45 minutes ago',
      businessName: 'Atlas Corp',
    },
    {
      id: '5',
      invoiceNumber: 'INV-3843',
      status: 'pending',
      timestamp: '1 hour ago',
      businessName: 'StellarWave Technologies',
    },
  ] as IRNStatusItem[],
  summary: {
    total: 245,
    pending: 18,
    processing: 12,
    completed: 198,
    failed: 17,
    successRate: 80.8,
  },
};

const mockIntegrationData = [
  {
    id: '1',
    name: 'Odoo ERP',
    description: 'Invoice source system integration',
    status: 'online',
    lastSyncTime: '5 minutes ago',
    responseTime: 428,
  },
  {
    id: '2',
    name: 'FIRS API',
    description: 'Nigerian tax authority integration',
    status: 'degraded',
    lastSyncTime: '15 minutes ago',
    responseTime: 1250,
    errorMessage: 'Intermittent timeout issues detected',
  },
  {
    id: '3',
    name: 'SAP Integration',
    description: 'Enterprise resource planning system',
    status: 'offline',
    lastSyncTime: '2 hours ago',
    errorMessage: 'Connection refused: Authentication failed',
  },
  {
    id: '4',
    name: 'QuickBooks',
    description: 'Financial management software',
    status: 'online',
    lastSyncTime: '30 minutes ago',
    responseTime: 312,
  },
] as IntegrationItem[];

const mockTransactionData: TransactionMetricsData = {
  daily: {
    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    datasets: [
      createDataset('Successful', [25, 32, 28, 42, 35, 18, 27], 'success'),
      createDataset('Failed', [5, 3, 2, 4, 3, 1, 2], 'danger'),
    ],
  },
  weekly: {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    datasets: [
      createDataset('Successful', [165, 178, 195, 187], 'success'),
      createDataset('Failed', [12, 15, 8, 10], 'danger'),
    ],
  },
  monthly: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [
      createDataset('Transactions', [580, 620, 750, 810, 925, 890], 'primary'),
    ],
  },
  summary: {
    totalCount: 2547,
    successCount: 2430,
    failureCount: 117,
    averagePerDay: 85,
    trend: 'up' as const,
    changePercentage: 12.5,
  },
};

const Dashboard: React.FC = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [useRealData, setUseRealData] = useState(false);
  const [timeRange, setTimeRange] = useState('24h');
  const [selectedOrg, setSelectedOrg] = useState<string | undefined>(undefined);
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard summary data on component mount or when parameters change
  useEffect(() => {
    if (useRealData) {
      fetchDashboardData();
    }
  }, [useRealData, timeRange, selectedOrg]);

  const fetchDashboardData = async () => {
    if (!useRealData) return;
    
    try {
      setIsRefreshing(true);
      setError(null);
      const data = await fetchDashboardSummary(timeRange, selectedOrg);
      setDashboardSummary(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      if (axios.isAxiosError(err)) {
        const axiosError = err as AxiosError;
        setError((axiosError.response?.data as any)?.detail || 'Failed to load dashboard data');
      } else {
        setError('Failed to load dashboard data');
      }
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    
    if (useRealData) {
      await fetchDashboardData();
    } else {
      // Just simulate a delay for mock data refreshes
      setTimeout(() => {
        setLastUpdated(new Date());
        setIsRefreshing(false);
      }, 1500);
    }
  };
  
  const toggleDataSource = () => {
    setUseRealData(!useRealData);
  };
  
  const handleTimeRangeChange = (value: string) => {
    setTimeRange(value);
  };

  return (
    <>
      <Head>
        <title>FIRS e-Invoice Dashboard</title>
      </Head>
    
      <DashboardLayout>
        <div className="p-6">
          <header className="mb-8">
            <div className="flex justify-between items-center mb-4">
              <h1 className="text-2xl font-heading font-semibold">Monitoring Dashboard</h1>
              <div className="flex gap-3 flex-wrap justify-end">
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
                <Select 
                  className="w-[110px]"
                  value={timeRange}
                  onValueChange={(value) => handleTimeRangeChange(value)}
                >
                  <option value="24h">24 Hours</option>
                  <option value="7d">7 Days</option>
                  <option value="30d">30 Days</option>
                  <option value="all">All Time</option>
                </Select>
                <Button 
                  variant={useRealData ? "default" : "outline"}
                  size="sm"
                  className="flex items-center gap-1"
                  onClick={toggleDataSource}
                >
                  <Link size={14} />
                  <span>{useRealData ? 'Using API Data' : 'Using Mock Data'}</span>
                </Button>
                <NextLink href="/dashboard" passHref legacyBehavior>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex items-center gap-1"
                    asChild
                  >
                    <a>
                      <Activity size={14} />
                      <span>Dashboard Hub</span>
                    </a>
                  </Button>
                </NextLink>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">Last updated: {lastUpdated.toLocaleTimeString()}</Badge>
              <Badge variant="secondary">
                Time range: {timeRange === '24h' ? 'Last 24h' : timeRange === '7d' ? 'Last 7 days' : timeRange === '30d' ? 'Last 30 days' : 'All Time'}
              </Badge>
              <Badge variant="outline">Organization: {selectedOrg || 'All'}</Badge>
              <Badge variant={useRealData ? "success" : "secondary"}>{useRealData ? 'Live Data' : 'Mock Data'}</Badge>
            </div>
          </header>

          {error && (
            <div className="mb-6 p-4 border border-destructive/50 bg-destructive/10 rounded-md">
              <p className="text-destructive">{error}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6">
            <div className="md:col-span-8">
              <EnhancedIRNMetricsCard
                timeRange={timeRange}
                organizationId={selectedOrg}
                isLoading={isRefreshing && !useRealData}
                useRealData={useRealData}
                summaryData={dashboardSummary?.irn_summary}
              />
            </div>
            
            <div className="md:col-span-4">
              <ValidationMetricsCard
                timeRange={timeRange}
                organizationId={selectedOrg}
                isLoading={isRefreshing && !useRealData}
                useRealData={useRealData}
                summaryData={dashboardSummary?.validation_summary}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6">
            <div className="md:col-span-8">
              <Card className="h-full">
                <CardHeader>
                  <CardTitle>Transaction Metrics</CardTitle>
                  <CardDescription>API traffic and processing volume</CardDescription>
                </CardHeader>
                <CardContent>
                  <TransactionMetrics 
                    data={mockTransactionData} 
                    isLoading={isRefreshing && !useRealData}
                    useRealData={useRealData}
                    timeRange={timeRange}
                    refreshInterval={30000}
                    summaryData={dashboardSummary?.system_summary}
                  />
                </CardContent>
              </Card>
            </div>
            
            <div className="md:col-span-4">
              <B2BvsB2CMetricsCard 
                timeRange={timeRange}
                organizationId={selectedOrg}
                isLoading={isRefreshing && !useRealData}
                useRealData={useRealData}
                summaryData={dashboardSummary?.b2b_vs_b2c_summary}
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 mb-6">
            <div className="md:col-span-7">
              <IRNStatusMonitor 
                recentItems={useRealData ? undefined : mockIRNStatusData.recentItems} 
                summary={useRealData ? undefined : mockIRNStatusData.summary} 
                isLoading={isRefreshing && !useRealData}
                useRealData={useRealData}
                timeRange={timeRange}
                refreshInterval={30000}
                summaryData={dashboardSummary?.irn_summary}
              />
            </div>
            
            <div className="md:col-span-5">
              <OdooIntegrationMetricsCard
                timeRange={timeRange}
                organizationId={selectedOrg}
                isLoading={isRefreshing && !useRealData}
                useRealData={useRealData}
                summaryData={dashboardSummary?.odoo_summary}
              />
            </div>
          </div>
          
          <div className="mb-6">
            <IntegrationStatus 
              integrations={useRealData ? undefined : mockIntegrationData} 
              isLoading={isRefreshing && !useRealData}
              onRefresh={handleRefresh}
              useRealData={useRealData}
              timeRange={timeRange}
              refreshInterval={useRealData ? 30000 : 0}
              summaryData={dashboardSummary?.odoo_summary}
            />
          </div>
        </div>
      </DashboardLayout>
    </>
  );
};

export default Dashboard;
