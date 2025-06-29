/**
 * Nigerian Analytics Dashboard
 * 
 * Comprehensive analytics dashboard for Nigerian market features including
 * compliance metrics, regional performance, and cultural adoption analytics.
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { BarChart, LineChart, DoughnutChart, AreaChart } from '@/components/ui/Charts';
import {
  ShieldCheckIcon,
  UserShieldIcon,
  ExclamationTriangleIcon,
  MapPinIcon,
  GlobeIcon,
  TrendingUpIcon,
  CreditCardIcon,
  PhoneIcon,
  BuildingIcon,
  UsersIcon
} from '@heroicons/react/24/outline';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';
import { Badge } from '@/components/ui/Badge';
import { Progress } from '@/components/ui/Progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { RefreshCwIcon, CalendarIcon, DownloadIcon } from 'lucide-react';

interface NigerianAnalytics {
  nitda_status: string;
  nitda_expiry: string;
  ndpr_compliance_score: number;
  iso_status: string;
  next_audit_date: string;
  total_penalties: number;
  state_revenue: Array<{
    state: string;
    revenue: number;
    growth: number;
  }>;
  payment_methods: Array<{
    method: string;
    volume: number;
    value: number;
  }>;
  language_usage: Array<{
    language: string;
    users: number;
    percentage: number;
  }>;
  device_usage: Array<{
    device: string;
    users: number;
    sessions: number;
  }>;
  support_channels: Array<{
    channel: string;
    tickets: number;
    satisfaction: number;
  }>;
  compliance_timeline: Array<{
    month: string;
    nitda: number;
    ndpr: number;
    iso: number;
  }>;
  regional_metrics: Array<{
    region: string;
    businesses: number;
    transactions: number;
    compliance_rate: number;
  }>;
  cultural_adoption: Array<{
    feature: string;
    adoption_rate: number;
    satisfaction: number;
  }>;
}

interface ComplianceCardProps {
  title: string;
  status: string | number;
  expiry?: string;
  nextAudit?: string;
  percentage?: boolean;
  amount?: boolean;
  currency?: string;
  icon: React.ReactNode;
}

const ComplianceCard: React.FC<ComplianceCardProps> = ({
  title,
  status,
  expiry,
  nextAudit,
  percentage = false,
  amount = false,
  currency = '',
  icon
}) => {
  const getStatusColor = (value: string | number) => {
    if (typeof value === 'number') {
      if (value >= 90) return 'text-green-600';
      if (value >= 70) return 'text-yellow-600';
      return 'text-red-600';
    }
    
    if (value === 'Active' || value === 'Compliant') return 'text-green-600';
    if (value === 'Expiring Soon') return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatValue = (value: string | number) => {
    if (amount && typeof value === 'number') {
      return new Intl.NumberFormat('en-NG', {
        style: 'currency',
        currency: currency || 'NGN'
      }).format(value);
    }
    
    if (percentage && typeof value === 'number') {
      return `${value}%`;
    }
    
    return value;
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gray-100 rounded-lg">
              {icon}
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">{title}</p>
              <p className={`text-2xl font-bold ${getStatusColor(status)}`}>
                {formatValue(status)}
              </p>
              {expiry && (
                <p className="text-xs text-gray-500">Expires: {expiry}</p>
              )}
              {nextAudit && (
                <p className="text-xs text-gray-500">Next Audit: {nextAudit}</p>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const NigerianStateRevenueChart: React.FC<{ data: Array<any> }> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>;
  }

  const chartData = {
    labels: data.map(item => item.state),
    datasets: [
      {
        label: 'Revenue (₦M)',
        data: data.map(item => item.revenue / 1000000),
        backgroundColor: 'rgba(34, 197, 94, 0.6)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
      },
      {
        label: 'Growth (%)',
        data: data.map(item => item.growth),
        backgroundColor: 'rgba(59, 130, 246, 0.6)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
        yAxisID: 'y1',
      }
    ]
  };

  const options = {
    responsive: true,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Nigerian States'
        }
      },
      y: {
        type: 'linear' as const,
        display: true,
        position: 'left' as const,
        title: {
          display: true,
          text: 'Revenue (₦M)'
        }
      },
      y1: {
        type: 'linear' as const,
        display: true,
        position: 'right' as const,
        title: {
          display: true,
          text: 'Growth (%)'
        },
        grid: {
          drawOnChartArea: false,
        },
      },
    },
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Revenue by Nigerian State'
      }
    }
  };

  return <BarChart data={chartData} options={options} />;
};

const NigerianPaymentMethodChart: React.FC<{ data: Array<any> }> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>;
  }

  const chartData = {
    labels: data.map(item => item.method),
    datasets: [{
      data: data.map(item => item.volume),
      backgroundColor: [
        'rgba(34, 197, 94, 0.8)',
        'rgba(59, 130, 246, 0.8)',
        'rgba(251, 191, 36, 0.8)',
        'rgba(248, 113, 113, 0.8)',
        'rgba(168, 85, 247, 0.8)'
      ],
      borderColor: [
        'rgba(34, 197, 94, 1)',
        'rgba(59, 130, 246, 1)',
        'rgba(251, 191, 36, 1)',
        'rgba(248, 113, 113, 1)',
        'rgba(168, 85, 247, 1)'
      ],
      borderWidth: 2,
    }]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
      title: {
        display: true,
        text: 'Payment Method Distribution'
      }
    }
  };

  return <DoughnutChart data={chartData} options={options} />;
};

const LanguageDistributionChart: React.FC<{ data: Array<any> }> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>;
  }

  return (
    <div className="space-y-4">
      {data.map((lang, index) => (
        <div key={index} className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-3 h-3 rounded-full bg-green-500" />
            <span className="font-medium">{lang.language}</span>
          </div>
          <div className="flex items-center space-x-4">
            <div className="w-32">
              <Progress value={lang.percentage} className="h-2" />
            </div>
            <span className="text-sm text-gray-600 w-12">{lang.percentage}%</span>
          </div>
        </div>
      ))}
    </div>
  );
};

const DeviceUsageChart: React.FC<{ data: Array<any> }> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>;
  }

  const chartData = {
    labels: data.map(item => item.device),
    datasets: [{
      label: 'Users',
      data: data.map(item => item.users),
      backgroundColor: 'rgba(59, 130, 246, 0.6)',
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 2,
    }]
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Device Usage Distribution'
      }
    },
    scales: {
      y: {
        beginAtZero: true
      }
    }
  };

  return <BarChart data={chartData} options={options} />;
};

const SupportChannelChart: React.FC<{ data: Array<any> }> = ({ data }) => {
  if (!data || data.length === 0) {
    return <div className="h-64 flex items-center justify-center text-gray-500">No data available</div>;
  }

  return (
    <div className="space-y-4">
      {data.map((channel, index) => (
        <div key={index} className="p-4 border rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium">{channel.channel}</span>
            <Badge variant={channel.satisfaction >= 4 ? 'success' : channel.satisfaction >= 3 ? 'warning' : 'error'}>
              {channel.satisfaction}/5
            </Badge>
          </div>
          <div className="text-sm text-gray-600">
            {channel.tickets} tickets processed
          </div>
        </div>
      ))}
    </div>
  );
};

export const NigerianAnalyticsDashboard: React.FC = () => {
  const [analyticsData, setAnalyticsData] = useState<NigerianAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('30d');

  useEffect(() => {
    fetchAnalyticsData();
  }, [timeRange]);

  const fetchAnalyticsData = async () => {
    try {
      setLoading(true);
      // Replace with actual API call
      const response = await fetch(`/api/dashboard/nigerian-analytics?timeRange=${timeRange}`);
      const data = await response.json();
      setAnalyticsData(data);
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
      // Mock data for development
      setAnalyticsData({
        nitda_status: 'Active',
        nitda_expiry: '2025-12-31',
        ndpr_compliance_score: 95,
        iso_status: 'Certified',
        next_audit_date: '2025-03-15',
        total_penalties: 2500000,
        state_revenue: [
          { state: 'Lagos', revenue: 15000000000, growth: 12.5 },
          { state: 'Rivers', revenue: 8000000000, growth: 8.3 },
          { state: 'Kano', revenue: 6000000000, growth: 15.2 },
          { state: 'Ogun', revenue: 4500000000, growth: 9.7 },
          { state: 'FCT', revenue: 7200000000, growth: 11.8 }
        ],
        payment_methods: [
          { method: 'Bank Transfer', volume: 45, value: 12000000000 },
          { method: 'USSD', volume: 30, value: 3500000000 },
          { method: 'Card Payment', volume: 15, value: 2800000000 },
          { method: 'Mobile Money', volume: 8, value: 1200000000 },
          { method: 'Cash', volume: 2, value: 500000000 }
        ],
        language_usage: [
          { language: 'English', users: 12500, percentage: 62 },
          { language: 'Hausa', users: 4200, percentage: 21 },
          { language: 'Yoruba', users: 2800, percentage: 14 },
          { language: 'Igbo', users: 600, percentage: 3 }
        ],
        device_usage: [
          { device: 'Mobile', users: 14800, sessions: 45200 },
          { device: 'Desktop', users: 4200, sessions: 8900 },
          { device: 'Tablet', users: 1000, sessions: 1800 }
        ],
        support_channels: [
          { channel: 'WhatsApp Business', tickets: 1250, satisfaction: 4.8 },
          { channel: 'Phone Support', tickets: 890, satisfaction: 4.5 },
          { channel: 'Email', tickets: 560, satisfaction: 4.2 },
          { channel: 'In-App Chat', tickets: 340, satisfaction: 4.0 }
        ],
        compliance_timeline: [],
        regional_metrics: [],
        cultural_adoption: []
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalyticsData();
  };

  const handleExport = () => {
    // Implement export functionality
    console.log('Exporting Nigerian analytics data...');
  };

  if (loading) {
    return <LoadingSkeleton count={8} height="h-32" />;
  }

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Failed to load analytics data
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Nigerian Market Analytics</h1>
          <p className="text-gray-600">Comprehensive insights into Nigerian business operations</p>
        </div>
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center space-x-2"
          >
            <RefreshCwIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            className="flex items-center space-x-2"
          >
            <DownloadIcon className="h-4 w-4" />
            <span>Export</span>
          </Button>
        </div>
      </div>

      {/* Time Range Filter */}
      <div className="flex space-x-2">
        {['7d', '30d', '90d', '1y'].map((range) => (
          <Button
            key={range}
            variant={timeRange === range ? 'default' : 'outline'}
            size="sm"
            onClick={() => setTimeRange(range)}
          >
            {range === '7d' ? '7 Days' : range === '30d' ? '30 Days' : range === '90d' ? '90 Days' : '1 Year'}
          </Button>
        ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="compliance">Compliance</TabsTrigger>
          <TabsTrigger value="regional">Regional</TabsTrigger>
          <TabsTrigger value="cultural">Cultural</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Nigerian Compliance Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <ComplianceCard
              title="NITDA Accreditation"
              status={analyticsData.nitda_status}
              expiry={analyticsData.nitda_expiry}
              icon={<ShieldCheckIcon className="h-6 w-6 text-green-600" />}
            />
            <ComplianceCard
              title="NDPR Compliance"
              status={analyticsData.ndpr_compliance_score}
              percentage={true}
              icon={<UserShieldIcon className="h-6 w-6 text-blue-600" />}
            />
            <ComplianceCard
              title="ISO 27001 Status"
              status={analyticsData.iso_status}
              nextAudit={analyticsData.next_audit_date}
              icon={<ShieldCheckIcon className="h-6 w-6 text-purple-600" />}
            />
            <ComplianceCard
              title="FIRS Penalties"
              status={analyticsData.total_penalties}
              amount={true}
              currency="NGN"
              icon={<ExclamationTriangleIcon className="h-6 w-6 text-red-600" />}
            />
          </div>

          {/* Nigerian Market Performance */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MapPinIcon className="h-5 w-5" />
                  <span>Revenue by Nigerian State</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <NigerianStateRevenueChart data={analyticsData.state_revenue} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CreditCardIcon className="h-5 w-5" />
                  <span>Payment Method Distribution</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <NigerianPaymentMethodChart data={analyticsData.payment_methods} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="compliance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <GlobeIcon className="h-5 w-5" />
                  <span>User Language Preferences</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <LanguageDistributionChart data={analyticsData.language_usage} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <PhoneIcon className="h-5 w-5" />
                  <span>Device Usage Distribution</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <DeviceUsageChart data={analyticsData.device_usage} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <UsersIcon className="h-5 w-5" />
                  <span>Support Channel Performance</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SupportChannelChart data={analyticsData.support_channels} />
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="regional" className="space-y-6">
          <div className="text-center py-12">
            <MapPinIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Regional Analytics</h3>
            <p className="text-gray-600">Regional performance metrics coming soon</p>
          </div>
        </TabsContent>

        <TabsContent value="cultural" className="space-y-6">
          <div className="text-center py-12">
            <BuildingIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Cultural Analytics</h3>
            <p className="text-gray-600">Cultural adoption metrics coming soon</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};