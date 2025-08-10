/**
 * Payment Processor Dashboard
 * ==========================
 * 
 * System Integrator interface for managing payment processor integrations.
 * Supports Nigerian payment providers and international gateways.
 * 
 * Features:
 * - Nigerian payment gateway integration (Paystack, Flutterwave, Interswitch)
 * - International payment processors (Stripe, PayPal, Square)
 * - Transaction monitoring and reconciliation
 * - Payment compliance and fraud detection
 * - Multi-currency support with NGN focus
 * - Real-time payment status tracking
 * 
 * Nigerian Payment Providers:
 * - Paystack (Nigerian-focused)
 * - Flutterwave (Pan-African)
 * - Interswitch (Nigerian banking)
 * - Remita (Government payments)
 * - GTBank Payment Gateway
 * - Access Bank Payment Gateway
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Badge,
  Progress,
  ScrollArea,
  Alert,
  AlertDescription,
  Input,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger
} from '@/components/ui';
import { 
  CreditCard, 
  DollarSign, 
  TrendingUp, 
  AlertCircle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Eye,
  Download,
  Upload,
  Zap,
  Shield,
  Globe,
  BarChart3,
  Users,
  Clock,
  Filter,
  Search
} from 'lucide-react';

// Types
interface PaymentProvider {
  id: string;
  name: string;
  type: 'nigerian' | 'international' | 'bank';
  logo: string;
  status: 'active' | 'inactive' | 'testing';
  features: string[];
  currencies: string[];
  fees: {
    domestic: number;
    international: number;
  };
  integration: {
    status: 'connected' | 'pending' | 'error';
    lastSync: Date;
    apiVersion: string;
  };
}

interface Transaction {
  id: string;
  reference: string;
  amount: number;
  currency: string;
  status: 'successful' | 'pending' | 'failed' | 'cancelled';
  provider: string;
  customer: {
    name: string;
    email: string;
    phone?: string;
  };
  timestamp: Date;
  fees: number;
  netAmount: number;
  invoice?: string;
}

interface PaymentAnalytics {
  totalVolume: number;
  totalTransactions: number;
  successRate: number;
  averageAmount: number;
  totalFees: number;
  topProvider: string;
  dailyVolume: { date: string; amount: number; count: number }[];
  providerBreakdown: { provider: string; volume: number; count: number }[];
}

// Nigerian Payment Providers Data
const NIGERIAN_PROVIDERS: PaymentProvider[] = [
  {
    id: 'paystack',
    name: 'Paystack',
    type: 'nigerian',
    logo: '/logos/paystack.png',
    status: 'active',
    features: ['Cards', 'Bank Transfer', 'USSD', 'QR Code', 'Mobile Money'],
    currencies: ['NGN', 'USD', 'GHS', 'ZAR'],
    fees: { domestic: 1.5, international: 3.9 },
    integration: {
      status: 'connected',
      lastSync: new Date(),
      apiVersion: 'v1'
    }
  },
  {
    id: 'flutterwave',
    name: 'Flutterwave',
    type: 'nigerian',
    logo: '/logos/flutterwave.png',
    status: 'active',
    features: ['Cards', 'Bank Transfer', 'Mobile Money', 'USSD', 'Barter'],
    currencies: ['NGN', 'USD', 'EUR', 'GBP', 'KES', 'GHS'],
    fees: { domestic: 1.4, international: 3.8 },
    integration: {
      status: 'connected',
      lastSync: new Date(),
      apiVersion: 'v3'
    }
  },
  {
    id: 'interswitch',
    name: 'Interswitch',
    type: 'nigerian',
    logo: '/logos/interswitch.png',
    status: 'testing',
    features: ['Verve Cards', 'WebPAY', 'InterswitchPAY', 'QR Code'],
    currencies: ['NGN'],
    fees: { domestic: 1.25, international: 0 },
    integration: {
      status: 'pending',
      lastSync: new Date(Date.now() - 86400000),
      apiVersion: 'v2'
    }
  },
  {
    id: 'remita',
    name: 'Remita',
    type: 'nigerian',
    logo: '/logos/remita.png',
    status: 'active',
    features: ['Bank Transfer', 'USSD', 'Government Payments', 'Salary Loans'],
    currencies: ['NGN'],
    fees: { domestic: 1.0, international: 0 },
    integration: {
      status: 'connected',
      lastSync: new Date(),
      apiVersion: 'v1.1'
    }
  }
];

const INTERNATIONAL_PROVIDERS: PaymentProvider[] = [
  {
    id: 'stripe',
    name: 'Stripe',
    type: 'international',
    logo: '/logos/stripe.png',
    status: 'active',
    features: ['Cards', 'Bank Transfer', 'Digital Wallets', 'Buy Now Pay Later'],
    currencies: ['USD', 'EUR', 'GBP', 'NGN'],
    fees: { domestic: 2.9, international: 3.9 },
    integration: {
      status: 'connected',
      lastSync: new Date(),
      apiVersion: '2020-08-27'
    }
  },
  {
    id: 'paypal',
    name: 'PayPal',
    type: 'international',
    logo: '/logos/paypal.png',
    status: 'inactive',
    features: ['PayPal Wallet', 'Cards', 'Bank Transfer', 'Express Checkout'],
    currencies: ['USD', 'EUR', 'GBP'],
    fees: { domestic: 2.9, international: 4.4 },
    integration: {
      status: 'error',
      lastSync: new Date(Date.now() - 172800000),
      apiVersion: 'v2'
    }
  }
];

// Mock data
const mockTransactions: Transaction[] = [
  {
    id: 'txn_001',
    reference: 'REF_2024_001',
    amount: 25000,
    currency: 'NGN',
    status: 'successful',
    provider: 'paystack',
    customer: { name: 'John Doe', email: 'john@example.com', phone: '+2348012345678' },
    timestamp: new Date(),
    fees: 375,
    netAmount: 24625,
    invoice: 'INV_001'
  },
  {
    id: 'txn_002',
    reference: 'REF_2024_002',
    amount: 15000,
    currency: 'NGN',
    status: 'pending',
    provider: 'flutterwave',
    customer: { name: 'Jane Smith', email: 'jane@example.com' },
    timestamp: new Date(Date.now() - 3600000),
    fees: 210,
    netAmount: 14790
  }
];

const mockAnalytics: PaymentAnalytics = {
  totalVolume: 2450000,
  totalTransactions: 156,
  successRate: 94.2,
  averageAmount: 15705,
  totalFees: 36750,
  topProvider: 'Paystack',
  dailyVolume: [
    { date: '2024-01-01', amount: 125000, count: 8 },
    { date: '2024-01-02', amount: 180000, count: 12 },
    { date: '2024-01-03', amount: 95000, count: 6 }
  ],
  providerBreakdown: [
    { provider: 'Paystack', volume: 1225000, count: 78 },
    { provider: 'Flutterwave', volume: 980000, count: 62 },
    { provider: 'Remita', volume: 245000, count: 16 }
  ]
};

export const PaymentProcessorDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedProvider, setSelectedProvider] = useState<PaymentProvider | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>(mockTransactions);
  const [analytics, setAnalytics] = useState<PaymentAnalytics>(mockAnalytics);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  const allProviders = [...NIGERIAN_PROVIDERS, ...INTERNATIONAL_PROVIDERS];
  const activeProviders = allProviders.filter(p => p.status === 'active');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'successful': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'pending': return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled': return <XCircle className="h-4 w-4 text-gray-500" />;
      default: return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'successful': return 'bg-green-100 text-green-800 border-green-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'cancelled': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatCurrency = (amount: number, currency: string = 'NGN') => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const filteredTransactions = transactions.filter(transaction => 
    (filterStatus === 'all' || transaction.status === filterStatus) &&
    (searchTerm === '' || 
     transaction.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
     transaction.customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
     transaction.customer.email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <CreditCard className="h-6 w-6 text-blue-600" />
            Payment Processors
          </h2>
          <p className="text-gray-600 mt-1">
            Manage payment gateway integrations and transaction processing
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            🇳🇬 Nigerian Focus
          </Badge>
          <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
            {activeProviders.length} Active
          </Badge>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="providers">Providers</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Volume</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(analytics.totalVolume)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-600" />
                </div>
                <div className="mt-2">
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    +12.5% from last month
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Transactions</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {analytics.totalTransactions.toLocaleString()}
                    </p>
                  </div>
                  <BarChart3 className="h-8 w-8 text-blue-600" />
                </div>
                <div className="mt-2">
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    +8.3% from last month
                  </Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Success Rate</p>
                    <p className="text-2xl font-bold text-purple-600">
                      {analytics.successRate}%
                    </p>
                  </div>
                  <TrendingUp className="h-8 w-8 text-purple-600" />
                </div>
                <div className="mt-2">
                  <Progress value={analytics.successRate} className="h-2" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Average Amount</p>
                    <p className="text-2xl font-bold text-orange-600">
                      {formatCurrency(analytics.averageAmount)}
                    </p>
                  </div>
                  <Users className="h-8 w-8 text-orange-600" />
                </div>
                <div className="mt-2">
                  <Badge variant="outline" className="bg-orange-50 text-orange-700">
                    +5.2% from last month
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Active Providers Overview */}
          <Card>
            <CardHeader>
              <CardTitle>Active Payment Providers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {activeProviders.map(provider => (
                  <div key={provider.id} className="p-4 border rounded-lg hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-3 mb-3">
                      <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                        <CreditCard className="h-5 w-5 text-gray-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{provider.name}</h4>
                        <Badge variant="outline" className={
                          provider.type === 'nigerian' ? 'bg-green-50 text-green-700' :
                          provider.type === 'international' ? 'bg-blue-50 text-blue-700' :
                          'bg-purple-50 text-purple-700'
                        }>
                          {provider.type}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Domestic Fee:</span>
                        <span className="font-medium">{provider.fees.domestic}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Integration:</span>
                        <Badge variant="outline" className={
                          provider.integration.status === 'connected' ? 'bg-green-50 text-green-700' :
                          provider.integration.status === 'pending' ? 'bg-yellow-50 text-yellow-700' :
                          'bg-red-50 text-red-700'
                        }>
                          {provider.integration.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Transactions */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {transactions.slice(0, 5).map(transaction => (
                  <div key={transaction.id} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(transaction.status)}
                      <div>
                        <p className="font-medium">{transaction.reference}</p>
                        <p className="text-sm text-gray-600">{transaction.customer.name}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-medium">{formatCurrency(transaction.amount, transaction.currency)}</p>
                      <p className="text-sm text-gray-600">{transaction.provider}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="providers" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Nigerian Providers */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  🇳🇬 Nigerian Providers
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    {NIGERIAN_PROVIDERS.length} Available
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {NIGERIAN_PROVIDERS.map(provider => (
                    <div key={provider.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                            <CreditCard className="h-6 w-6 text-gray-600" />
                          </div>
                          <div>
                            <h4 className="font-medium">{provider.name}</h4>
                            <Badge variant="outline" className={getStatusColor(provider.status)}>
                              {provider.status}
                            </Badge>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Domestic Fee:</span>
                          <span className="ml-2 font-medium">{provider.fees.domestic}%</span>
                        </div>
                        <div>
                          <span className="text-gray-600">API Version:</span>
                          <span className="ml-2 font-medium">{provider.integration.apiVersion}</span>
                        </div>
                      </div>
                      <div className="mt-3">
                        <p className="text-xs text-gray-600 mb-1">Supported Features:</p>
                        <div className="flex flex-wrap gap-1">
                          {provider.features.map(feature => (
                            <Badge key={feature} variant="secondary" className="text-xs">
                              {feature}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* International Providers */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  🌍 International Providers
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    {INTERNATIONAL_PROVIDERS.length} Available
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {INTERNATIONAL_PROVIDERS.map(provider => (
                    <div key={provider.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                            <Globe className="h-6 w-6 text-gray-600" />
                          </div>
                          <div>
                            <h4 className="font-medium">{provider.name}</h4>
                            <Badge variant="outline" className={getStatusColor(provider.status)}>
                              {provider.status}
                            </Badge>
                          </div>
                        </div>
                        <Button variant="outline" size="sm">
                          <Settings className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Domestic Fee:</span>
                          <span className="ml-2 font-medium">{provider.fees.domestic}%</span>
                        </div>
                        <div>
                          <span className="text-gray-600">International Fee:</span>
                          <span className="ml-2 font-medium">{provider.fees.international}%</span>
                        </div>
                      </div>
                      <div className="mt-3">
                        <p className="text-xs text-gray-600 mb-1">Supported Currencies:</p>
                        <div className="flex flex-wrap gap-1">
                          {provider.currencies.map(currency => (
                            <Badge key={currency} variant="secondary" className="text-xs">
                              {currency}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="transactions" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Transaction History</CardTitle>
              <div className="flex gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="Search transactions..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="max-w-sm"
                  />
                </div>
                <Select value={filterStatus} onValueChange={setFilterStatus}>
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="successful">Successful</SelectItem>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="failed">Failed</SelectItem>
                    <SelectItem value="cancelled">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Reference</TableHead>
                    <TableHead>Customer</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTransactions.map(transaction => (
                    <TableRow key={transaction.id}>
                      <TableCell className="font-medium">{transaction.reference}</TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{transaction.customer.name}</p>
                          <p className="text-sm text-gray-600">{transaction.customer.email}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <p className="font-medium">{formatCurrency(transaction.amount, transaction.currency)}</p>
                          <p className="text-sm text-gray-600">Fee: {formatCurrency(transaction.fees)}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className="capitalize">
                          {transaction.provider}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={getStatusColor(transaction.status)}>
                          {transaction.status}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {transaction.timestamp.toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm">
                            <Eye className="h-3 w-3" />
                          </Button>
                          <Button variant="outline" size="sm">
                            <Download className="h-3 w-3" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Provider Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {analytics.providerBreakdown.map(provider => (
                    <div key={provider.provider} className="space-y-2">
                      <div className="flex justify-between">
                        <span className="font-medium">{provider.provider}</span>
                        <span className="text-sm text-gray-600">
                          {formatCurrency(provider.volume)} ({provider.count} txns)
                        </span>
                      </div>
                      <Progress 
                        value={(provider.volume / analytics.totalVolume) * 100} 
                        className="h-2" 
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fee Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-600">Total Fees Paid</span>
                      <span className="font-bold text-red-600">{formatCurrency(analytics.totalFees)}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Average Fee Rate</span>
                      <span className="font-medium">
                        {((analytics.totalFees / analytics.totalVolume) * 100).toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    {NIGERIAN_PROVIDERS.filter(p => p.status === 'active').map(provider => (
                      <div key={provider.id} className="flex justify-between items-center p-2 border rounded">
                        <span className="text-sm">{provider.name}</span>
                        <div className="text-right">
                          <p className="text-sm font-medium">{provider.fees.domestic}%</p>
                          <p className="text-xs text-gray-600">domestic</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="settings" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Payment Processing Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-3">Default Currency</h4>
                <Select defaultValue="NGN">
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NGN">Nigerian Naira (NGN)</SelectItem>
                    <SelectItem value="USD">US Dollar (USD)</SelectItem>
                    <SelectItem value="EUR">Euro (EUR)</SelectItem>
                    <SelectItem value="GBP">British Pound (GBP)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <h4 className="font-medium mb-3">Notification Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Email notifications for failed transactions</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">SMS alerts for high-value transactions</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Daily transaction summary reports</span>
                  </label>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-3">Security Settings</h4>
                <div className="space-y-3">
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Require 2FA for provider configuration</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" defaultChecked className="rounded" />
                    <span className="text-sm">Enable fraud detection</span>
                  </label>
                  <label className="flex items-center space-x-3">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">Auto-suspend suspicious transactions</span>
                  </label>
                </div>
              </div>

              <div className="flex gap-3">
                <Button>Save Settings</Button>
                <Button variant="outline">Reset to Defaults</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};