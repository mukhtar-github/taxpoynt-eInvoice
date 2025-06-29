import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { Progress } from '../ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import {
  Building,
  MapPin,
  Users,
  DollarSign,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  BarChart3,
  PieChart,
  FileText,
  Calendar,
  Target,
  Briefcase,
  Shield,
  Globe
} from 'lucide-react';

interface NigerianSubsidiary {
  id: string;
  subsidiary_name: string;
  cac_registration_number: string;
  operating_state: string;
  local_government_area: string;
  firs_tin: string;
  state_tax_id: string;
  local_government_tax_id: string;
  primary_location: {
    address: string;
    city: string;
    state: string;
    postal_code: string;
  };
  business_activities: string[];
  employee_count: number;
  annual_revenue_ngn: number;
  ownership_percentage: number;
  is_active: boolean;
  incorporation_date: string;
}

interface NigerianConglomerate {
  id: string;
  conglomerate_name: string;
  cac_group_registration: string;
  tax_consolidation_type: 'consolidated' | 'separate';
  primary_business_sector: string;
  total_subsidiaries: number;
  total_employees: number;
  consolidated_revenue_ngn: number;
  governance_model: string;
  subsidiaries: NigerianSubsidiary[];
}

interface TaxBreakdown {
  federal_taxes: Array<{
    type: string;
    rate: number;
    amount: number;
    authority: string;
    jurisdiction: string;
  }>;
  state_taxes: Array<{
    type: string;
    rate: number;
    amount: number;
    authority: string;
    jurisdiction: string;
  }>;
  local_taxes: Array<{
    type: string;
    rate: number;
    amount: number;
    authority: string;
    jurisdiction: string;
  }>;
  total_tax: number;
}

interface MultiSubsidiaryDashboardProps {
  organizationId: string;
  conglomerate?: NigerianConglomerate;
  onAddSubsidiary?: () => void;
  onViewSubsidiary?: (subsidiaryId: string) => void;
  onManageConsolidation?: () => void;
}

const NAIRA_FORMATTER = new Intl.NumberFormat('en-NG', {
  style: 'currency',
  currency: 'NGN',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

const NIGERIAN_STATES = {
  'Lagos': { region: 'South West', color: 'bg-blue-500' },
  'Kano': { region: 'North West', color: 'bg-green-500' },
  'Rivers': { region: 'South South', color: 'bg-purple-500' },
  'Ogun': { region: 'South West', color: 'bg-orange-500' },
  'Kaduna': { region: 'North West', color: 'bg-red-500' },
  'Abuja': { region: 'North Central', color: 'bg-indigo-500' },
};

const SubsidiaryCard: React.FC<{
  subsidiary: NigerianSubsidiary;
  onView?: () => void;
}> = ({ subsidiary, onView }) => {
  const stateInfo = NIGERIAN_STATES[subsidiary.operating_state as keyof typeof NIGERIAN_STATES];
  
  const getStatusColor = (isActive: boolean) => 
    isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800';

  const getRevenueGrowth = () => {
    // Simulate growth calculation
    const growth = Math.random() * 20 - 10; // -10% to +10%
    return growth;
  };

  const growth = getRevenueGrowth();

  return (
    <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={onView}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg">{subsidiary.subsidiary_name}</CardTitle>
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <MapPin className="w-4 h-4" />
              <span>{subsidiary.operating_state}, {subsidiary.local_government_area}</span>
              {stateInfo && (
                <Badge variant="secondary" className="text-xs">
                  {stateInfo.region}
                </Badge>
              )}
            </div>
          </div>
          <Badge className={getStatusColor(subsidiary.is_active)}>
            {subsidiary.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-green-600" />
            <div>
              <p className="text-gray-600">Annual Revenue</p>
              <p className="font-semibold">{NAIRA_FORMATTER.format(subsidiary.annual_revenue_ngn)}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Users className="w-4 h-4 text-blue-600" />
            <div>
              <p className="text-gray-600">Employees</p>
              <p className="font-semibold">{subsidiary.employee_count}</p>
            </div>
          </div>
        </div>

        {/* Growth Indicator */}
        <div className="flex items-center space-x-2">
          {growth >= 0 ? (
            <TrendingUp className="w-4 h-4 text-green-600" />
          ) : (
            <TrendingDown className="w-4 h-4 text-red-600" />
          )}
          <span className={`text-sm font-medium ${growth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {growth >= 0 ? '+' : ''}{growth.toFixed(1)}% vs last year
          </span>
        </div>

        {/* Ownership */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Ownership</span>
            <span className="font-medium">{subsidiary.ownership_percentage}%</span>
          </div>
          <Progress value={subsidiary.ownership_percentage} className="h-2" />
        </div>

        {/* Tax IDs */}
        <div className="bg-gray-50 p-3 rounded-lg space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-gray-600">FIRS TIN:</span>
            <span className="font-mono">{subsidiary.firs_tin}</span>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-gray-600">State Tax ID:</span>
            <span className="font-mono">{subsidiary.state_tax_id}</span>
          </div>
        </div>

        {/* Business Activities */}
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Business Activities</p>
          <div className="flex flex-wrap gap-1">
            {subsidiary.business_activities.slice(0, 3).map((activity, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {activity}
              </Badge>
            ))}
            {subsidiary.business_activities.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{subsidiary.business_activities.length - 3} more
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const ConglomerateOverview: React.FC<{
  conglomerate: NigerianConglomerate;
}> = ({ conglomerate }) => {
  const totalRevenue = conglomerate.subsidiaries.reduce(
    (sum, sub) => sum + sub.annual_revenue_ngn, 0
  );
  
  const totalEmployees = conglomerate.subsidiaries.reduce(
    (sum, sub) => sum + sub.employee_count, 0
  );

  const stateDistribution = conglomerate.subsidiaries.reduce((acc, sub) => {
    acc[sub.operating_state] = (acc[sub.operating_state] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const activeSubsidiaries = conglomerate.subsidiaries.filter(sub => sub.is_active).length;
  const complianceRate = (activeSubsidiaries / conglomerate.subsidiaries.length) * 100;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{conglomerate.conglomerate_name}</h1>
          <p className="text-gray-600">Nigerian Business Conglomerate</p>
        </div>
        <Badge variant="outline" className="text-sm">
          {conglomerate.primary_business_sector}
        </Badge>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Building className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Subsidiaries</p>
                <p className="text-2xl font-bold text-gray-900">{conglomerate.subsidiaries.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-green-600">
                  {NAIRA_FORMATTER.format(totalRevenue)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <Users className="w-5 h-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Total Employees</p>
                <p className="text-2xl font-bold text-purple-600">{totalEmployees}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Compliance Rate</p>
                <p className="text-2xl font-bold text-green-600">{complianceRate.toFixed(0)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tax Consolidation Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="w-5 h-5" />
            <span>Tax Consolidation Status</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600 mb-2">Consolidation Type</p>
              <Badge variant={conglomerate.tax_consolidation_type === 'consolidated' ? 'default' : 'secondary'}>
                {conglomerate.tax_consolidation_type.toUpperCase()}
              </Badge>
            </div>
            <div>
              <p className="text-sm text-gray-600 mb-2">Governance Model</p>
              <Badge variant="outline">{conglomerate.governance_model}</Badge>
            </div>
          </div>
          
          {conglomerate.tax_consolidation_type === 'consolidated' && (
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <FileText className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-800">Consolidated Tax Filing</span>
              </div>
              <p className="text-sm text-blue-700 mt-1">
                All subsidiaries file taxes as a single consolidated group.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Geographic Distribution */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="w-5 h-5" />
            <span>Geographic Distribution</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {Object.entries(stateDistribution).map(([state, count]) => {
              const stateInfo = NIGERIAN_STATES[state as keyof typeof NIGERIAN_STATES];
              return (
                <div key={state} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`w-3 h-3 rounded-full ${stateInfo?.color || 'bg-gray-500'}`} />
                  <div>
                    <p className="font-medium text-sm">{state}</p>
                    <p className="text-xs text-gray-600">{count} subsidiaries</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const TaxJurisdictionAnalysis: React.FC<{
  subsidiaries: NigerianSubsidiary[];
}> = ({ subsidiaries }) => {
  // Simulate tax calculations for each subsidiary
  const [taxBreakdowns, setTaxBreakdowns] = useState<Record<string, TaxBreakdown>>({});

  useEffect(() => {
    // In a real implementation, this would fetch from the API
    const mockTaxBreakdowns: Record<string, TaxBreakdown> = {};
    
    subsidiaries.forEach(subsidiary => {
      const revenue = subsidiary.annual_revenue_ngn;
      const vatAmount = revenue * 0.075; // 7.5% VAT
      const citAmount = revenue * (revenue > 25000000 ? 0.30 : 0.20); // CIT
      const stateAmount = revenue * 0.015; // State tax
      const lgaAmount = revenue * 0.005; // LGA tax
      
      mockTaxBreakdowns[subsidiary.id] = {
        federal_taxes: [
          { type: 'VAT', rate: 0.075, amount: vatAmount, authority: 'FIRS', jurisdiction: 'Federal' },
          { type: 'CIT', rate: revenue > 25000000 ? 0.30 : 0.20, amount: citAmount, authority: 'FIRS', jurisdiction: 'Federal' }
        ],
        state_taxes: [
          { type: 'State Revenue Tax', rate: 0.015, amount: stateAmount, authority: `${subsidiary.operating_state} SIRS`, jurisdiction: 'State' }
        ],
        local_taxes: [
          { type: 'LGA Service Tax', rate: 0.005, amount: lgaAmount, authority: `${subsidiary.local_government_area} LGA`, jurisdiction: 'Local' }
        ],
        total_tax: vatAmount + citAmount + stateAmount + lgaAmount
      };
    });
    
    setTaxBreakdowns(mockTaxBreakdowns);
  }, [subsidiaries]);

  const totalTaxLiability = Object.values(taxBreakdowns).reduce(
    (sum, breakdown) => sum + breakdown.total_tax, 0
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Multi-Jurisdiction Tax Summary</CardTitle>
          <CardDescription>
            Tax obligations across Nigerian federal, state, and local jurisdictions
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-3xl font-bold text-red-600">
              {NAIRA_FORMATTER.format(totalTaxLiability)}
            </p>
            <p className="text-sm text-gray-600">Total Annual Tax Liability</p>
          </div>
        </CardContent>
      </Card>

      {subsidiaries.map(subsidiary => {
        const breakdown = taxBreakdowns[subsidiary.id];
        if (!breakdown) return null;

        return (
          <Card key={subsidiary.id}>
            <CardHeader>
              <CardTitle className="text-lg">{subsidiary.subsidiary_name}</CardTitle>
              <CardDescription>{subsidiary.operating_state}, {subsidiary.local_government_area}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-blue-600">Federal Taxes</h4>
                  {breakdown.federal_taxes.map((tax, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{tax.type} ({(tax.rate * 100).toFixed(1)}%)</span>
                      <span className="font-medium">{NAIRA_FORMATTER.format(tax.amount)}</span>
                    </div>
                  ))}
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-green-600">State Taxes</h4>
                  {breakdown.state_taxes.map((tax, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{tax.type} ({(tax.rate * 100).toFixed(1)}%)</span>
                      <span className="font-medium">{NAIRA_FORMATTER.format(tax.amount)}</span>
                    </div>
                  ))}
                </div>
                
                <div className="space-y-2">
                  <h4 className="font-medium text-sm text-purple-600">Local Taxes</h4>
                  {breakdown.local_taxes.map((tax, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{tax.type} ({(tax.rate * 100).toFixed(1)}%)</span>
                      <span className="font-medium">{NAIRA_FORMATTER.format(tax.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <Separator className="my-4" />
              
              <div className="flex justify-between font-semibold">
                <span>Total Tax Liability</span>
                <span className="text-red-600">{NAIRA_FORMATTER.format(breakdown.total_tax)}</span>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};

export const MultiSubsidiaryDashboard: React.FC<MultiSubsidiaryDashboardProps> = ({
  organizationId,
  conglomerate,
  onAddSubsidiary,
  onViewSubsidiary,
  onManageConsolidation
}) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);

  if (!conglomerate) {
    return (
      <Card className="w-full max-w-4xl mx-auto">
        <CardHeader>
          <CardTitle>Multi-Subsidiary Coordination</CardTitle>
          <CardDescription>
            Manage your Nigerian business conglomerate and subsidiaries
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-12">
            <Building className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No Conglomerate Structure Set Up
            </h3>
            <p className="text-gray-600 mb-6">
              Set up your Nigerian conglomerate structure to manage multiple subsidiaries, 
              coordinate tax obligations, and streamline operations across jurisdictions.
            </p>
            <Button onClick={onAddSubsidiary}>
              Set Up Conglomerate
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <TabsList className="grid w-full sm:w-auto grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="subsidiaries">Subsidiaries</TabsTrigger>
            <TabsTrigger value="tax-analysis">Tax Analysis</TabsTrigger>
          </TabsList>
          
          <div className="flex space-x-2">
            <Button variant="outline" onClick={onManageConsolidation}>
              <Target className="w-4 h-4 mr-2" />
              Manage Consolidation
            </Button>
            <Button onClick={onAddSubsidiary}>
              <Building className="w-4 h-4 mr-2" />
              Add Subsidiary
            </Button>
          </div>
        </div>

        <TabsContent value="overview" className="space-y-6">
          <ConglomerateOverview conglomerate={conglomerate} />
        </TabsContent>

        <TabsContent value="subsidiaries" className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Subsidiary Companies</h2>
              <p className="text-gray-600">Manage your subsidiary companies across Nigeria</p>
            </div>
            <Badge variant="outline">{conglomerate.subsidiaries.length} Total</Badge>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {conglomerate.subsidiaries.map((subsidiary) => (
              <SubsidiaryCard
                key={subsidiary.id}
                subsidiary={subsidiary}
                onView={() => onViewSubsidiary?.(subsidiary.id)}
              />
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tax-analysis" className="space-y-6">
          <TaxJurisdictionAnalysis subsidiaries={conglomerate.subsidiaries} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default MultiSubsidiaryDashboard;