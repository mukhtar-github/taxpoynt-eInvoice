import React, { useState, useEffect } from 'react';
import { useLocalization, useBusinessTerms, useCommonPhrases, useBusinessMessages } from '../../context/LocalizationContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { Progress } from '../ui/Progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { LanguageSwitcher } from '../localization/LanguageSwitcher';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Receipt, 
  Users, 
  AlertCircle,
  CheckCircle,
  Clock,
  FileText,
  Smartphone,
  Globe,
  Calendar,
  BarChart3,
  PieChart
} from 'lucide-react';

interface DashboardMetrics {
  total_revenue: number;
  total_invoices: number;
  paid_invoices: number;
  pending_invoices: number;
  overdue_invoices: number;
  total_customers: number;
  ussd_payments: number;
  sms_sent: number;
  monthly_growth: number;
  language_usage: Record<string, number>;
}

interface LocalizedDashboardProps {
  metrics: DashboardMetrics;
  companyName?: string;
  showLanguageSwitcher?: boolean;
}

export const LocalizedDashboard: React.FC<LocalizedDashboardProps> = ({
  metrics,
  companyName,
  showLanguageSwitcher = true
}) => {
  const { 
    currentLanguage, 
    formatCurrency, 
    formatNumber, 
    getCurrentGreeting,
    languageConfig
  } = useLocalization();
  const terms = useBusinessTerms();
  const phrases = useCommonPhrases();
  const messages = useBusinessMessages();

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 60000); // Update every minute

    return () => clearInterval(timer);
  }, []);

  const getLocalizedTitle = (key: string): string => {
    const titles: Record<string, Record<string, string>> = {
      'dashboard': {
        'en-NG': 'Dashboard',
        'ha-NG': 'Allon Baiyanai',
        'yo-NG': 'Pẹpẹ Iṣakoso',
        'ig-NG': 'Bọọdụ Njikwa'
      },
      'overview': {
        'en-NG': 'Overview',
        'ha-NG': 'Bayyani',
        'yo-NG': 'Akopọ',
        'ig-NG': 'Nchịkọta'
      },
      'revenue': {
        'en-NG': 'Revenue',
        'ha-NG': 'Kudaden shiga',
        'yo-NG': 'Owo wiwole',
        'ig-NG': 'Ego mbata'
      },
      'analytics': {
        'en-NG': 'Analytics',
        'ha-NG': 'Bincike',
        'yo-NG': 'Itupalẹ',
        'ig-NG': 'Nyocha'
      },
      'language_usage': {
        'en-NG': 'Language Usage',
        'ha-NG': 'Amfanin Harshe',
        'yo-NG': 'Lilo Ede',
        'ig-NG': 'Ojiji Asụsụ'
      },
      'payment_methods': {
        'en-NG': 'Payment Methods',
        'ha-NG': 'Hanyoyin Biya',
        'yo-NG': 'Awọn Ọna Sisanwo',
        'ig-NG': 'Ụzọ Ịkwụ Ụgwọ'
      },
      'ussd_transactions': {
        'en-NG': 'USSD Transactions',
        'ha-NG': 'Mu\'amalar USSD',
        'yo-NG': 'Awọn Iṣowo USSD',
        'ig-NG': 'Azụmahịa USSD'
      },
      'sms_notifications': {
        'en-NG': 'SMS Notifications',
        'ha-NG': 'Sanarwar SMS',
        'yo-NG': 'Awọn Ikede SMS',
        'ig-NG': 'Ọkwa SMS'
      },
      'this_month': {
        'en-NG': 'This Month',
        'ha-NG': 'Wannan Wata',
        'yo-NG': 'Oṣu Yii',
        'ig-NG': 'Ọnwa A'
      },
      'last_7_days': {
        'en-NG': 'Last 7 Days',
        'ha-NG': 'Kwanaki 7 Da Suka Wuce',
        'yo-NG': 'Ọjọ 7 Sẹhin',
        'ig-NG': 'Ụbọchị 7 Gara Aga'
      }
    };

    return titles[key]?.[currentLanguage] || titles[key]?.['en-NG'] || key;
  };

  const getWelcomeMessage = (): string => {
    const greeting = getCurrentGreeting();
    const company = companyName || 'TaxPoynt';
    
    const welcomeMessages: Record<string, string> = {
      'en-NG': `${greeting}! Welcome to ${company}`,
      'ha-NG': `${greeting}! Maraba zuwa ${company}`,
      'yo-NG': `${greeting}! Kaabo si ${company}`,
      'ig-NG': `${greeting}! Nnọọ na ${company}`
    };
    
    return welcomeMessages[currentLanguage] || welcomeMessages['en-NG'];
  };

  const getStatusLabel = (status: string): string => {
    const statusLabels: Record<string, Record<string, string>> = {
      'paid': {
        'en-NG': 'Paid',
        'ha-NG': 'An biya',
        'yo-NG': 'Ti san',
        'ig-NG': 'Akwụọla'
      },
      'pending': {
        'en-NG': 'Pending',
        'ha-NG': 'Ana jira',
        'yo-NG': 'Ti nduro',
        'ig-NG': 'Na-eche'
      },
      'overdue': {
        'en-NG': 'Overdue',
        'ha-NG': 'Ya wuce lokaci',
        'yo-NG': 'Ti koja akoko',
        'ig-NG': 'Agafela oge'
      }
    };

    return statusLabels[status]?.[currentLanguage] || status;
  };

  const formatTimeForLocale = (date: Date): string => {
    const timeFormats: Record<string, string> = {
      'en-NG': date.toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      }),
      'ha-NG': date.toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      }),
      'yo-NG': date.toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      }),
      'ig-NG': date.toLocaleTimeString('en-GB', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
      })
    };

    return timeFormats[currentLanguage] || timeFormats['en-NG'];
  };

  const renderMetricCard = (
    title: string, 
    value: string | number, 
    icon: React.ReactNode, 
    trend?: number,
    description?: string
  ) => (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold">{value}</p>
            {description && (
              <p className="text-xs text-gray-500 mt-1">{description}</p>
            )}
          </div>
          <div className="text-blue-600">{icon}</div>
        </div>
        {trend !== undefined && (
          <div className={`flex items-center mt-4 text-sm ${
            trend >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {trend >= 0 ? (
              <TrendingUp className="w-4 h-4 mr-1" />
            ) : (
              <TrendingDown className="w-4 h-4 mr-1" />
            )}
            <span>{Math.abs(trend)}%</span>
            <span className="ml-1 text-gray-500">
              {currentLanguage === 'ha-NG' && 'daga watan da ya wuce'}
              {currentLanguage === 'yo-NG' && 'lati osu to koja'}
              {currentLanguage === 'ig-NG' && 'site na ọnwa gara aga'}
              {currentLanguage === 'en-NG' && 'from last month'}
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderLanguageUsageChart = () => {
    const total = Object.values(metrics.language_usage).reduce((sum, count) => sum + count, 0);
    
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="w-5 h-5" />
            <span>{getLocalizedTitle('language_usage')}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {Object.entries(metrics.language_usage).map(([lang, count]) => {
              const percentage = total > 0 ? (count / total) * 100 : 0;
              const langNames: Record<string, string> = {
                'en-NG': 'English',
                'ha-NG': 'Hausa',
                'yo-NG': 'Yoruba',
                'ig-NG': 'Igbo'
              };
              
              return (
                <div key={lang} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{langNames[lang] || lang}</span>
                    <span>{formatNumber(count)} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <Progress value={percentage} className="h-2" />
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderInvoiceStatusBreakdown = () => {
    const total = metrics.total_invoices;
    const paidPercentage = total > 0 ? (metrics.paid_invoices / total) * 100 : 0;
    const pendingPercentage = total > 0 ? (metrics.pending_invoices / total) * 100 : 0;
    const overduePercentage = total > 0 ? (metrics.overdue_invoices / total) * 100 : 0;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="w-5 h-5" />
            <span>{terms.invoice} {terms.status}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <span className="text-sm">{getStatusLabel('paid')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">{formatNumber(metrics.paid_invoices)}</span>
                <Badge variant="secondary">{paidPercentage.toFixed(1)}%</Badge>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Clock className="w-4 h-4 text-yellow-600" />
                <span className="text-sm">{getStatusLabel('pending')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">{formatNumber(metrics.pending_invoices)}</span>
                <Badge variant="secondary">{pendingPercentage.toFixed(1)}%</Badge>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 text-red-600" />
                <span className="text-sm">{getStatusLabel('overdue')}</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">{formatNumber(metrics.overdue_invoices)}</span>
                <Badge variant="destructive">{overduePercentage.toFixed(1)}%</Badge>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {getLocalizedTitle('dashboard')}
          </h1>
          <p className="text-gray-600 mt-1">
            {getWelcomeMessage()}
          </p>
          <p className="text-sm text-gray-500">
            {currentTime.toLocaleDateString(currentLanguage, {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric'
            })} • {formatTimeForLocale(currentTime)}
          </p>
        </div>
        
        {showLanguageSwitcher && (
          <div className="flex items-center space-x-4">
            <LanguageSwitcher variant="compact" />
          </div>
        )}
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {renderMetricCard(
          getLocalizedTitle('revenue'),
          formatCurrency(metrics.total_revenue),
          <DollarSign className="w-6 h-6" />,
          metrics.monthly_growth,
          getLocalizedTitle('this_month')
        )}
        
        {renderMetricCard(
          terms.invoice,
          formatNumber(metrics.total_invoices),
          <Receipt className="w-6 h-6" />,
          undefined,
          getLocalizedTitle('this_month')
        )}
        
        {renderMetricCard(
          terms.customer,
          formatNumber(metrics.total_customers),
          <Users className="w-6 h-6" />
        )}
        
        {renderMetricCard(
          getLocalizedTitle('ussd_transactions'),
          formatNumber(metrics.ussd_payments),
          <Smartphone className="w-6 h-6" />,
          undefined,
          getLocalizedTitle('last_7_days')
        )}
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">{getLocalizedTitle('overview')}</TabsTrigger>
          <TabsTrigger value="invoices">{terms.invoice}</TabsTrigger>
          <TabsTrigger value="analytics">{getLocalizedTitle('analytics')}</TabsTrigger>
          <TabsTrigger value="mobile">{currentLanguage === 'ha-NG' ? 'Wayar hannu' : currentLanguage === 'yo-NG' ? 'Foonu alagbeka' : currentLanguage === 'ig-NG' ? 'Ekwentị mkpanaaka' : 'Mobile'}</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {renderInvoiceStatusBreakdown()}
            {renderLanguageUsageChart()}
          </div>
        </TabsContent>

        <TabsContent value="invoices" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{getStatusLabel('paid')}</p>
                    <p className="text-2xl font-bold text-green-600">{formatNumber(metrics.paid_invoices)}</p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{getStatusLabel('pending')}</p>
                    <p className="text-2xl font-bold text-yellow-600">{formatNumber(metrics.pending_invoices)}</p>
                  </div>
                  <Clock className="w-8 h-8 text-yellow-600" />
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">{getStatusLabel('overdue')}</p>
                    <p className="text-2xl font-bold text-red-600">{formatNumber(metrics.overdue_invoices)}</p>
                  </div>
                  <AlertCircle className="w-8 h-8 text-red-600" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="w-5 h-5" />
                  <span>{getLocalizedTitle('payment_methods')}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between text-sm">
                    <span>USSD</span>
                    <span>{formatNumber(metrics.ussd_payments)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Bank Transfer</span>
                    <span>{formatNumber(metrics.total_invoices - metrics.ussd_payments)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <PieChart className="w-5 h-5" />
                  <span>{getLocalizedTitle('sms_notifications')}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold">{formatNumber(metrics.sms_sent)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {currentLanguage === 'ha-NG' && 'SMS da aka aika'}
                    {currentLanguage === 'yo-NG' && 'SMS ti a fi ranṣẹ'}
                    {currentLanguage === 'ig-NG' && 'SMS ezigara'}
                    {currentLanguage === 'en-NG' && 'SMS sent'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="mobile" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Smartphone className="w-5 h-5" />
                  <span>{getLocalizedTitle('ussd_transactions')}</span>
                </CardTitle>
                <CardDescription>
                  {currentLanguage === 'ha-NG' && 'Biyan kuɗi ta wayar hannu mai sauki'}
                  {currentLanguage === 'yo-NG' && 'Sisanwo nipasẹ foonu ti ko ni internet'}
                  {currentLanguage === 'ig-NG' && 'Ịkwụ ụgwọ site na ekwentị nkịtị'}
                  {currentLanguage === 'en-NG' && 'Payments via basic mobile phones'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-blue-600">{formatNumber(metrics.ussd_payments)}</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {getLocalizedTitle('this_month')}
                  </p>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader>
                <CardTitle>{phrases.success} Rate</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center">
                  <p className="text-3xl font-bold text-green-600">94%</p>
                  <p className="text-sm text-gray-600 mt-1">
                    {currentLanguage === 'ha-NG' && 'Biyan kuɗi masu nasara'}
                    {currentLanguage === 'yo-NG' && 'Awọn sisanwo aṣeyọri'}
                    {currentLanguage === 'ig-NG' && 'Ịkwụ ụgwọ nke ọma'}
                    {currentLanguage === 'en-NG' && 'Successful payments'}
                  </p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LocalizedDashboard;