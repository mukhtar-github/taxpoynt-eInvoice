import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Separator } from '../ui/separator';
import { Progress } from '../ui/progress';
import {
  Building,
  Factory,
  Landmark,
  Truck,
  Smartphone,
  Cpu,
  Fuel,
  ShoppingBag,
  Users,
  Target,
  FileText,
  CheckCircle,
  Clock,
  DollarSign,
  Scale,
  Shield,
  Globe,
  Briefcase
} from 'lucide-react';

interface CorporateTemplate {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  sector: string;
  typical_structure: {
    parent_company: string;
    subsidiaries: string[];
    governance_model: 'traditional' | 'modern' | 'hybrid';
    tax_consolidation: 'consolidated' | 'separate';
  };
  approval_hierarchy: Array<{
    level: string;
    title: string;
    amount_limit_ngn: number;
    typical_roles: string[];
  }>;
  regulatory_requirements: string[];
  cultural_considerations: string[];
  estimated_setup_time: string;
  complexity_level: 'low' | 'medium' | 'high';
}

interface NigerianCorporateTemplatesProps {
  onSelectTemplate?: (template: CorporateTemplate) => void;
  onCustomSetup?: () => void;
}

const CORPORATE_TEMPLATES: CorporateTemplate[] = [
  {
    id: 'manufacturing-conglomerate',
    name: 'Manufacturing Conglomerate',
    description: 'Large-scale manufacturing operations with multiple production facilities across Nigeria',
    icon: <Factory className="w-8 h-8" />,
    sector: 'Manufacturing',
    typical_structure: {
      parent_company: 'Holding Company',
      subsidiaries: [
        'Primary Manufacturing Unit',
        'Secondary Processing Unit',
        'Distribution & Logistics',
        'Raw Materials Trading',
        'Equipment Maintenance Services'
      ],
      governance_model: 'traditional',
      tax_consolidation: 'consolidated'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Plant Supervisors',
        amount_limit_ngn: 50000,
        typical_roles: ['Production Supervisor', 'Shift Manager', 'Quality Controller']
      },
      {
        level: 'Level 2',
        title: 'Plant Managers',
        amount_limit_ngn: 500000,
        typical_roles: ['Plant Manager', 'Operations Manager', 'Safety Manager']
      },
      {
        level: 'Level 3',
        title: 'Regional Directors',
        amount_limit_ngn: 5000000,
        typical_roles: ['Regional Director', 'Business Unit Head', 'Technical Director']
      },
      {
        level: 'Level 4',
        title: 'Executive Management',
        amount_limit_ngn: 50000000,
        typical_roles: ['Managing Director', 'Executive Director', 'Chief Operating Officer']
      }
    ],
    regulatory_requirements: [
      'NAFDAC Registration for food/pharmaceutical products',
      'SON Standards compliance',
      'Environmental Impact Assessment (EIA)',
      'Factory Registration',
      'Industrial Training Fund (ITF) registration'
    ],
    cultural_considerations: [
      'Respect for traditional hierarchy in operations',
      'Community engagement and CSR programs',
      'Local employment prioritization',
      'Traditional greeting protocols in meetings',
      'Extended decision-making time for consensus'
    ],
    estimated_setup_time: '3-6 months',
    complexity_level: 'high'
  },
  {
    id: 'oil-gas-conglomerate',
    name: 'Oil & Gas Conglomerate',
    description: 'Integrated oil and gas operations including upstream, midstream, and downstream activities',
    icon: <Fuel className="w-8 h-8" />,
    sector: 'Oil & Gas',
    typical_structure: {
      parent_company: 'Energy Holdings Limited',
      subsidiaries: [
        'Exploration & Production',
        'Refining Operations',
        'Marketing & Distribution',
        'Petrochemicals',
        'Pipeline Operations',
        'Marine Services'
      ],
      governance_model: 'modern',
      tax_consolidation: 'separate'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Field Operations',
        amount_limit_ngn: 100000,
        typical_roles: ['Field Supervisor', 'Operations Coordinator', 'Safety Officer']
      },
      {
        level: 'Level 2',
        title: 'Asset Managers',
        amount_limit_ngn: 1000000,
        typical_roles: ['Asset Manager', 'Facility Manager', 'Production Manager']
      },
      {
        level: 'Level 3',
        title: 'Business Unit Heads',
        amount_limit_ngn: 10000000,
        typical_roles: ['Business Unit Manager', 'Regional Manager', 'Technical Director']
      },
      {
        level: 'Level 4',
        title: 'Executive Committee',
        amount_limit_ngn: 100000000,
        typical_roles: ['Managing Director', 'Executive Director', 'Chief Financial Officer']
      }
    ],
    regulatory_requirements: [
      'Department of Petroleum Resources (DPR) licenses',
      'Nigerian Content Development (NCD) compliance',
      'Environmental regulations compliance',
      'NNPC joint venture agreements',
      'Petroleum Industry Act compliance'
    ],
    cultural_considerations: [
      'Strong government relations focus',
      'Community development obligations',
      'Local content requirements adherence',
      'Traditional ruler engagement',
      'Multi-ethnic workforce management'
    ],
    estimated_setup_time: '6-12 months',
    complexity_level: 'high'
  },
  {
    id: 'telecommunications-group',
    name: 'Telecommunications Group',
    description: 'Telecommunications infrastructure and services across mobile, internet, and digital services',
    icon: <Smartphone className="w-8 h-8" />,
    sector: 'Telecommunications',
    typical_structure: {
      parent_company: 'Telecom Holdings Nigeria',
      subsidiaries: [
        'Mobile Network Operations',
        'Internet Service Provider',
        'Digital Payment Services',
        'Infrastructure Services',
        'Customer Service Centers'
      ],
      governance_model: 'modern',
      tax_consolidation: 'consolidated'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Team Leaders',
        amount_limit_ngn: 75000,
        typical_roles: ['Team Lead', 'Technical Specialist', 'Customer Service Manager']
      },
      {
        level: 'Level 2',
        title: 'Department Heads',
        amount_limit_ngn: 750000,
        typical_roles: ['Department Head', 'Network Manager', 'Sales Manager']
      },
      {
        level: 'Level 3',
        title: 'Directors',
        amount_limit_ngn: 7500000,
        typical_roles: ['Director of Operations', 'Commercial Director', 'Technology Director']
      },
      {
        level: 'Level 4',
        title: 'Executive Leadership',
        amount_limit_ngn: 75000000,
        typical_roles: ['Chief Executive Officer', 'Chief Technology Officer', 'Chief Commercial Officer']
      }
    ],
    regulatory_requirements: [
      'Nigerian Communications Commission (NCC) licenses',
      'Central Bank of Nigeria approval for payment services',
      'National Information Technology Development Agency registration',
      'Frequency spectrum allocation',
      'Universal Service Provision Fund contributions'
    ],
    cultural_considerations: [
      'Digital divide considerations',
      'Multi-language customer support',
      'Rural area service obligations',
      'Youth employment prioritization',
      'Technology adoption education'
    ],
    estimated_setup_time: '4-8 months',
    complexity_level: 'high'
  },
  {
    id: 'financial-services-group',
    name: 'Financial Services Group',
    description: 'Comprehensive financial services including banking, insurance, and investment management',
    icon: <Landmark className="w-8 h-8" />,
    sector: 'Financial Services',
    typical_structure: {
      parent_company: 'Financial Holdings Plc',
      subsidiaries: [
        'Commercial Banking',
        'Investment Banking',
        'Insurance Services',
        'Asset Management',
        'Microfinance Operations',
        'Digital Payment Platform'
      ],
      governance_model: 'modern',
      tax_consolidation: 'separate'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Branch Operations',
        amount_limit_ngn: 50000,
        typical_roles: ['Branch Manager', 'Relationship Manager', 'Operations Officer']
      },
      {
        level: 'Level 2',
        title: 'Regional Management',
        amount_limit_ngn: 1000000,
        typical_roles: ['Regional Manager', 'Area Manager', 'Credit Manager']
      },
      {
        level: 'Level 3',
        title: 'Senior Management',
        amount_limit_ngn: 15000000,
        typical_roles: ['General Manager', 'Deputy Managing Director', 'Chief Risk Officer']
      },
      {
        level: 'Level 4',
        title: 'Board Level',
        amount_limit_ngn: 200000000,
        typical_roles: ['Managing Director', 'Chairman', 'Independent Directors']
      }
    ],
    regulatory_requirements: [
      'Central Bank of Nigeria banking license',
      'National Insurance Commission registration',
      'Securities and Exchange Commission registration',
      'Financial Reporting Council compliance',
      'Nigeria Deposit Insurance Corporation membership'
    ],
    cultural_considerations: [
      'Islamic banking service requirements',
      'Trust-building in rural communities',
      'Cash-based transaction preferences',
      'Extended family financial obligations',
      'Religious compliance requirements'
    ],
    estimated_setup_time: '8-18 months',
    complexity_level: 'high'
  },
  {
    id: 'trading-distribution',
    name: 'Trading & Distribution Network',
    description: 'Import, distribution, and retail operations across consumer goods and commodities',
    icon: <Truck className="w-8 h-8" />,
    sector: 'Trading & Distribution',
    typical_structure: {
      parent_company: 'Distribution Holdings Limited',
      subsidiaries: [
        'Import & Logistics',
        'Wholesale Distribution',
        'Retail Operations',
        'Warehousing Services',
        'Transportation Fleet'
      ],
      governance_model: 'traditional',
      tax_consolidation: 'consolidated'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Store/Warehouse Managers',
        amount_limit_ngn: 100000,
        typical_roles: ['Store Manager', 'Warehouse Supervisor', 'Fleet Manager']
      },
      {
        level: 'Level 2',
        title: 'Regional Managers',
        amount_limit_ngn: 1000000,
        typical_roles: ['Regional Manager', 'Distribution Manager', 'Sales Manager']
      },
      {
        level: 'Level 3',
        title: 'General Managers',
        amount_limit_ngn: 10000000,
        typical_roles: ['General Manager', 'Operations Director', 'Commercial Director']
      },
      {
        level: 'Level 4',
        title: 'Executive Management',
        amount_limit_ngn: 50000000,
        typical_roles: ['Managing Director', 'Executive Chairman', 'Chief Operations Officer']
      }
    ],
    regulatory_requirements: [
      'Corporate Affairs Commission registration',
      'Nigeria Customs Service documentation',
      'Standards Organisation of Nigeria compliance',
      'State Internal Revenue Service registration',
      'Nigerian Ports Authority documentation'
    ],
    cultural_considerations: [
      'Market trader relationship building',
      'Regional distribution preferences',
      'Seasonal demand fluctuations',
      'Credit-based trading relationships',
      'Traditional market integration'
    ],
    estimated_setup_time: '2-4 months',
    complexity_level: 'medium'
  },
  {
    id: 'agribusiness-cooperative',
    name: 'Agribusiness Cooperative',
    description: 'Integrated agricultural operations including farming, processing, and distribution',
    icon: <ShoppingBag className="w-8 h-8" />,
    sector: 'Agriculture',
    typical_structure: {
      parent_company: 'Agribusiness Cooperative Society',
      subsidiaries: [
        'Crop Production',
        'Livestock Operations',
        'Food Processing',
        'Distribution Network',
        'Agricultural Equipment Leasing'
      ],
      governance_model: 'hybrid',
      tax_consolidation: 'separate'
    },
    approval_hierarchy: [
      {
        level: 'Level 1',
        title: 'Farm Supervisors',
        amount_limit_ngn: 25000,
        typical_roles: ['Farm Supervisor', 'Processing Unit Manager', 'Equipment Operator']
      },
      {
        level: 'Level 2',
        title: 'Cooperative Managers',
        amount_limit_ngn: 250000,
        typical_roles: ['Cooperative Manager', 'Extension Officer', 'Marketing Officer']
      },
      {
        level: 'Level 3',
        title: 'Board Members',
        amount_limit_ngn: 2500000,
        typical_roles: ['Board Member', 'Secretary', 'Treasurer']
      },
      {
        level: 'Level 4',
        title: 'Executive Committee',
        amount_limit_ngn: 10000000,
        typical_roles: ['Chairman', 'Vice Chairman', 'General Manager']
      }
    ],
    regulatory_requirements: [
      'Ministry of Agriculture registration',
      'Cooperative Societies registration',
      'NAFDAC registration for processed foods',
      'Agricultural Development Program participation',
      'Land Use Act compliance'
    ],
    cultural_considerations: [
      'Seasonal farming cycle respect',
      'Traditional farming practice integration',
      'Community ownership models',
      'Elder consultation requirements',
      'Harvest festival participation'
    ],
    estimated_setup_time: '3-6 months',
    complexity_level: 'medium'
  }
];

const TemplateCard: React.FC<{
  template: CorporateTemplate;
  onSelect: () => void;
  isSelected?: boolean;
}> = ({ template, onSelect, isSelected = false }) => {
  const getComplexityColor = (level: string) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-lg ${
        isSelected ? 'ring-2 ring-blue-500 shadow-lg' : ''
      }`}
      onClick={onSelect}
    >
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
              {template.icon}
            </div>
            <div>
              <CardTitle className="text-lg">{template.name}</CardTitle>
              <Badge variant="outline" className="mt-1">
                {template.sector}
              </Badge>
            </div>
          </div>
          <Badge className={getComplexityColor(template.complexity_level)}>
            {template.complexity_level} complexity
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <CardDescription className="text-sm">
          {template.description}
        </CardDescription>

        {/* Key Details */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <span>Setup: {template.estimated_setup_time}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Building className="w-4 h-4 text-gray-500" />
            <span>{template.typical_structure.subsidiaries.length} subsidiaries</span>
          </div>
        </div>

        {/* Structure Overview */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <h4 className="font-medium text-sm mb-2">Typical Structure</h4>
          <div className="space-y-1 text-xs">
            <div>
              <span className="text-gray-600">Parent:</span>
              <span className="ml-2 font-medium">{template.typical_structure.parent_company}</span>
            </div>
            <div>
              <span className="text-gray-600">Governance:</span>
              <span className="ml-2 font-medium capitalize">{template.typical_structure.governance_model}</span>
            </div>
            <div>
              <span className="text-gray-600">Tax:</span>
              <span className="ml-2 font-medium capitalize">{template.typical_structure.tax_consolidation}</span>
            </div>
          </div>
        </div>

        {/* Key Subsidiaries */}
        <div>
          <h4 className="font-medium text-sm mb-2">Key Subsidiaries</h4>
          <div className="flex flex-wrap gap-1">
            {template.typical_structure.subsidiaries.slice(0, 3).map((subsidiary, index) => (
              <Badge key={index} variant="outline" className="text-xs">
                {subsidiary}
              </Badge>
            ))}
            {template.typical_structure.subsidiaries.length > 3 && (
              <Badge variant="outline" className="text-xs">
                +{template.typical_structure.subsidiaries.length - 3} more
              </Badge>
            )}
          </div>
        </div>

        {/* Approval Levels */}
        <div>
          <h4 className="font-medium text-sm mb-2">Approval Hierarchy</h4>
          <div className="space-y-1">
            {template.approval_hierarchy.map((level, index) => (
              <div key={index} className="flex justify-between text-xs">
                <span className="text-gray-600">{level.title}</span>
                <span className="font-medium">
                  ₦{(level.amount_limit_ngn / 1000000).toFixed(level.amount_limit_ngn >= 1000000 ? 0 : 1)}
                  {level.amount_limit_ngn >= 1000000 ? 'M' : 'K'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Cultural Considerations Preview */}
        <div>
          <h4 className="font-medium text-sm mb-2">Cultural Considerations</h4>
          <div className="text-xs text-gray-600">
            {template.cultural_considerations.slice(0, 2).map((consideration, index) => (
              <div key={index} className="flex items-start space-x-1">
                <span>•</span>
                <span>{consideration}</span>
              </div>
            ))}
            {template.cultural_considerations.length > 2 && (
              <div className="text-blue-600 mt-1">
                +{template.cultural_considerations.length - 2} more considerations
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const TemplateDetailView: React.FC<{
  template: CorporateTemplate;
  onApplyTemplate: () => void;
  onBack: () => void;
}> = ({ template, onApplyTemplate, onBack }) => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Button variant="outline" onClick={onBack}>
            ← Back
          </Button>
          <div className="flex items-center space-x-3">
            <div className="p-3 bg-blue-100 rounded-lg text-blue-600">
              {template.icon}
            </div>
            <div>
              <h1 className="text-2xl font-bold">{template.name}</h1>
              <p className="text-gray-600">{template.description}</p>
            </div>
          </div>
        </div>
        <Button onClick={onApplyTemplate} size="lg">
          Apply This Template
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5 text-blue-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Setup Time</p>
                <p className="font-bold">{template.estimated_setup_time}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Building className="w-5 h-5 text-green-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Subsidiaries</p>
                <p className="font-bold">{template.typical_structure.subsidiaries.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Scale className="w-5 h-5 text-purple-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Approval Levels</p>
                <p className="font-bold">{template.approval_hierarchy.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Shield className="w-5 h-5 text-red-600" />
              <div>
                <p className="text-sm font-medium text-gray-600">Complexity</p>
                <p className="font-bold capitalize">{template.complexity_level}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Corporate Structure */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Building className="w-5 h-5" />
              <span>Corporate Structure</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">Parent Company</h4>
              <Badge variant="outline">{template.typical_structure.parent_company}</Badge>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Subsidiary Companies</h4>
              <div className="space-y-2">
                {template.typical_structure.subsidiaries.map((subsidiary, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-gray-50 rounded">
                    <Building className="w-4 h-4 text-gray-500" />
                    <span className="text-sm">{subsidiary}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium mb-1">Governance Model</h4>
                <Badge variant="secondary" className="capitalize">
                  {template.typical_structure.governance_model}
                </Badge>
              </div>
              <div>
                <h4 className="font-medium mb-1">Tax Consolidation</h4>
                <Badge variant="secondary" className="capitalize">
                  {template.typical_structure.tax_consolidation}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Approval Hierarchy */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Scale className="w-5 h-5" />
              <span>Approval Hierarchy</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {template.approval_hierarchy.map((level, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <h4 className="font-medium">{level.title}</h4>
                      <p className="text-sm text-gray-600">{level.level}</p>
                    </div>
                    <Badge variant="outline">
                      ₦{(level.amount_limit_ngn / 1000000).toFixed(level.amount_limit_ngn >= 1000000 ? 0 : 1)}
                      {level.amount_limit_ngn >= 1000000 ? 'M' : 'K'} limit
                    </Badge>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {level.typical_roles.map((role, roleIndex) => (
                      <Badge key={roleIndex} variant="outline" className="text-xs">
                        {role}
                      </Badge>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Regulatory Requirements */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5" />
              <span>Regulatory Requirements</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {template.regulatory_requirements.map((requirement, index) => (
                <div key={index} className="flex items-start space-x-2 p-2 bg-yellow-50 rounded">
                  <AlertTriangle className="w-4 h-4 text-yellow-600 mt-0.5" />
                  <span className="text-sm">{requirement}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Cultural Considerations */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Users className="w-5 h-5" />
              <span>Cultural Considerations</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {template.cultural_considerations.map((consideration, index) => (
                <div key={index} className="flex items-start space-x-2 p-2 bg-blue-50 rounded">
                  <Globe className="w-4 h-4 text-blue-600 mt-0.5" />
                  <span className="text-sm">{consideration}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export const NigerianCorporateTemplates: React.FC<NigerianCorporateTemplatesProps> = ({
  onSelectTemplate,
  onCustomSetup
}) => {
  const [selectedTemplate, setSelectedTemplate] = useState<CorporateTemplate | null>(null);
  const [viewMode, setViewMode] = useState<'browse' | 'detail'>('browse');
  const [filterSector, setFilterSector] = useState<string>('all');

  const sectors = ['all', ...new Set(CORPORATE_TEMPLATES.map(t => t.sector))];
  
  const filteredTemplates = CORPORATE_TEMPLATES.filter(template => 
    filterSector === 'all' || template.sector === filterSector
  );

  const handleSelectTemplate = (template: CorporateTemplate) => {
    setSelectedTemplate(template);
    setViewMode('detail');
  };

  const handleApplyTemplate = () => {
    if (selectedTemplate) {
      onSelectTemplate?.(selectedTemplate);
    }
  };

  const handleBack = () => {
    setViewMode('browse');
    setSelectedTemplate(null);
  };

  if (viewMode === 'detail' && selectedTemplate) {
    return (
      <TemplateDetailView
        template={selectedTemplate}
        onApplyTemplate={handleApplyTemplate}
        onBack={handleBack}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold">Nigerian Corporate Structure Templates</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Choose from pre-configured corporate structures designed for Nigerian business culture, 
          regulatory requirements, and operational excellence across different sectors.
        </p>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-4">
          <Label htmlFor="sector-filter">Filter by Sector:</Label>
          <Select value={filterSector} onValueChange={setFilterSector}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {sectors.map(sector => (
                <SelectItem key={sector} value={sector}>
                  {sector === 'all' ? 'All Sectors' : sector}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Button variant="outline" onClick={onCustomSetup}>
          <Briefcase className="w-4 h-4 mr-2" />
          Custom Setup
        </Button>
      </div>

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredTemplates.map((template) => (
          <TemplateCard
            key={template.id}
            template={template}
            onSelect={() => handleSelectTemplate(template)}
            isSelected={selectedTemplate?.id === template.id}
          />
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <Building className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No templates found
          </h3>
          <p className="text-gray-600 mb-4">
            No corporate templates match your selected sector filter.
          </p>
          <Button variant="outline" onClick={() => setFilterSector('all')}>
            Show All Templates
          </Button>
        </div>
      )}

      {/* Benefits Section */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold mb-4">Why Use Nigerian Corporate Templates?</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <h4 className="font-medium">Regulatory Compliance</h4>
                <p className="text-sm text-gray-600">Pre-configured to meet Nigerian regulatory requirements</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Users className="w-5 h-5 text-blue-600 mt-0.5" />
              <div>
                <h4 className="font-medium">Cultural Adaptation</h4>
                <p className="text-sm text-gray-600">Designed for Nigerian business culture and practices</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <Clock className="w-5 h-5 text-purple-600 mt-0.5" />
              <div>
                <h4 className="font-medium">Faster Setup</h4>
                <p className="text-sm text-gray-600">Reduce setup time with proven corporate structures</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default NigerianCorporateTemplates;