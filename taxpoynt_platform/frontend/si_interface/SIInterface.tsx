/**
 * System Integrator (SI) Interface - Main Router Component
 * =======================================================
 * 
 * Main routing and navigation component for the System Integrator interface.
 * Provides comprehensive access to all SI tools, workflows, and dashboards.
 * 
 * Features:
 * - Tabbed navigation between main SI areas
 * - Context-aware sidebar navigation
 * - Real-time status indicators
 * - Nigerian compliance monitoring
 * - Role-based access control
 * 
 * Navigation Structure:
 * - Integration Hub: System setup and configuration
 * - Processing Center: Document processing and monitoring  
 * - Compliance Dashboard: Nigerian regulatory compliance
 * - Workflow Manager: Business process automation
 * - System Tools: Utilities and advanced features
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  CardContent, 
  CardHeader, 
  CardTitle,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Badge,
  ScrollArea,
  Separator,
  Alert,
  AlertDescription
} from '@/components/ui';
import { 
  Settings, 
  Monitor, 
  Shield, 
  Workflow, 
  Wrench,
  Bell,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
  Users,
  Building2,
  CreditCard,
  FileText,
  BarChart3,
  Globe,
  Zap
} from 'lucide-react';

// Import SI Interface Components
import IntegrationSetup from './pages/integration_setup';
import DataMapping from './pages/data_mapping';
import ProcessingMonitor from './pages/processing_monitor';
import ComplianceDashboard from './pages/compliance_dashboard';
import ERPOnboarding from './workflows/erp_onboarding';
import DocumentPreparation from './workflows/document_preparation';
import ValidationProcess from './workflows/validation_process';
import { CertificateManager } from './components/certificate_management/CertificateManager';
import { DataExtractor } from './components/data_extraction/DataExtractor';
import { DocumentProcessor } from './components/document_processing/DocumentProcessor';
import { SchemaValidator } from './components/schema_validation/SchemaValidator';
import { PaymentProcessorDashboard } from './components/financial_systems/payment_processors/PaymentProcessorDashboard';
import { FinancialValidator } from './components/financial_systems/validation_tools/FinancialValidator';

// Types
interface SIStatus {
  integrations: {
    total: number;
    active: number;
    errors: number;
  };
  processing: {
    jobs_running: number;
    jobs_queued: number;
    success_rate: number;
  };
  compliance: {
    firs_status: 'compliant' | 'warning' | 'error';
    certificate_expiry: number;
    outstanding_issues: number;
  };
  systems: {
    erp_connected: number;
    pos_connected: number;
    payment_gateways: number;
  };
}

interface NavigationItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
  description: string;
  category: 'integration' | 'processing' | 'compliance' | 'workflow' | 'tools';
  access_level: 'admin' | 'user' | 'viewer';
  status?: 'active' | 'beta' | 'coming_soon';
}

// Navigation Configuration
const SI_NAVIGATION: NavigationItem[] = [
  // Integration Hub
  {
    id: 'integration-setup',
    label: 'Integration Setup',
    icon: <Settings className="h-4 w-4" />,
    component: IntegrationSetup,
    description: 'Configure business system integrations',
    category: 'integration',
    access_level: 'admin',
    status: 'active'
  },
  {
    id: 'data-mapping',
    label: 'Data Mapping',
    icon: <FileText className="h-4 w-4" />,
    component: DataMapping,
    description: 'Map data fields between systems',
    category: 'integration',
    access_level: 'user',
    status: 'active'
  },
  
  // Processing Center
  {
    id: 'processing-monitor',
    label: 'Processing Monitor',
    icon: <Monitor className="h-4 w-4" />,
    component: ProcessingMonitor,
    description: 'Monitor real-time processing status',
    category: 'processing',
    access_level: 'user',
    status: 'active'
  },
  {
    id: 'document-processor',
    label: 'Document Processor',
    icon: <FileText className="h-4 w-4" />,
    component: DocumentProcessor,
    description: 'Process documents through FIRS pipeline',
    category: 'processing',
    access_level: 'user',
    status: 'active'
  },
  
  // Compliance Dashboard
  {
    id: 'compliance-dashboard',
    label: 'Compliance Dashboard',
    icon: <Shield className="h-4 w-4" />,
    component: ComplianceDashboard,
    description: 'Nigerian regulatory compliance monitoring',
    category: 'compliance',
    access_level: 'admin',
    status: 'active'
  },
  {
    id: 'financial-validator',
    label: 'Financial Validator',
    icon: <CreditCard className="h-4 w-4" />,
    component: FinancialValidator,
    description: 'Validate financial data compliance',
    category: 'compliance',
    access_level: 'user',
    status: 'active'
  },
  
  // Workflow Manager
  {
    id: 'erp-onboarding',
    label: 'ERP Onboarding',
    icon: <Users className="h-4 w-4" />,
    component: ERPOnboarding,
    description: 'Complete ERP integration workflow',
    category: 'workflow',
    access_level: 'admin',
    status: 'active'
  },
  {
    id: 'document-preparation',
    label: 'Document Preparation',
    icon: <FileText className="h-4 w-4" />,
    component: DocumentPreparation,
    description: 'Prepare documents for FIRS submission',
    category: 'workflow',
    access_level: 'user',
    status: 'active'
  },
  {
    id: 'validation-process',
    label: 'Validation Process',
    icon: <CheckCircle className="h-4 w-4" />,
    component: ValidationProcess,
    description: 'Multi-tier validation workflow',
    category: 'workflow',
    access_level: 'user',
    status: 'active'
  },
  
  // System Tools
  {
    id: 'certificate-manager',
    label: 'Certificate Manager',
    icon: <Shield className="h-4 w-4" />,
    component: CertificateManager,
    description: 'Manage digital certificates',
    category: 'tools',
    access_level: 'admin',
    status: 'active'
  },
  {
    id: 'data-extractor',
    label: 'Data Extractor',
    icon: <Activity className="h-4 w-4" />,
    component: DataExtractor,
    description: 'Extract data from business systems',
    category: 'tools',
    access_level: 'user',
    status: 'active'
  },
  {
    id: 'schema-validator',
    label: 'Schema Validator',
    icon: <CheckCircle className="h-4 w-4" />,
    component: SchemaValidator,
    description: 'Validate document schemas',
    category: 'tools',
    access_level: 'user',
    status: 'active'
  },
  {
    id: 'payment-processors',
    label: 'Payment Processors',
    icon: <CreditCard className="h-4 w-4" />,
    component: PaymentProcessorDashboard,
    description: 'Manage payment gateway integrations',
    category: 'tools',
    access_level: 'admin',
    status: 'active'
  }
];

// Mock status data
const mockSIStatus: SIStatus = {
  integrations: {
    total: 12,
    active: 10,
    errors: 1
  },
  processing: {
    jobs_running: 3,
    jobs_queued: 7,
    success_rate: 94.2
  },
  compliance: {
    firs_status: 'compliant',
    certificate_expiry: 45,
    outstanding_issues: 2
  },
  systems: {
    erp_connected: 2,
    pos_connected: 4,
    payment_gateways: 3
  }
};

export default function SIInterface() {
  const [activeTab, setActiveTab] = useState('integration');
  const [activeComponent, setActiveComponent] = useState('integration-setup');
  const [siStatus, setSiStatus] = useState<SIStatus>(mockSIStatus);
  const [userRole] = useState<'admin' | 'user' | 'viewer'>('admin'); // This would come from auth context

  // Filter navigation items by category and access level
  const getNavigationByCategory = (category: string) => {
    return SI_NAVIGATION.filter(item => 
      item.category === category && 
      hasAccess(item.access_level)
    );
  };

  const hasAccess = (requiredLevel: 'admin' | 'user' | 'viewer'): boolean => {
    const levels = { admin: 3, user: 2, viewer: 1 };
    return levels[userRole] >= levels[requiredLevel];
  };

  const getActiveComponent = () => {
    const item = SI_NAVIGATION.find(item => item.id === activeComponent);
    return item ? item.component : IntegrationSetup;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'bg-green-100 text-green-800 border-green-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const CategoryIcon = ({ category }: { category: string }) => {
    switch (category) {
      case 'integration': return <Building2 className="h-5 w-5" />;
      case 'processing': return <Activity className="h-5 w-5" />;
      case 'compliance': return <Shield className="h-5 w-5" />;
      case 'workflow': return <Workflow className="h-5 w-5" />;
      case 'tools': return <Wrench className="h-5 w-5" />;
      default: return <Settings className="h-5 w-5" />;
    }
  };

  const ActiveComponent = getActiveComponent();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Globe className="h-6 w-6 text-blue-600" />
              System Integrator Interface
            </h1>
            <p className="text-gray-600 mt-1">
              Comprehensive business system integration and compliance management
            </p>
          </div>
          <div className="flex items-center gap-4">
            <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
              🇳🇬 Nigerian Compliant
            </Badge>
            <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
              FIRS Certified
            </Badge>
            <Button variant="outline" size="sm">
              <Bell className="h-4 w-4 mr-2" />
              Notifications
            </Button>
          </div>
        </div>
      </div>

      {/* Status Overview */}
      <div className="px-6 py-4 bg-white border-b border-gray-200">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Active Integrations</p>
                <p className="text-xl font-bold text-blue-600">
                  {siStatus.integrations.active}/{siStatus.integrations.total}
                </p>
              </div>
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Processing Jobs</p>
                <p className="text-xl font-bold text-green-600">
                  {siStatus.processing.jobs_running} running
                </p>
              </div>
              <Activity className="h-8 w-8 text-green-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">FIRS Compliance</p>
                <Badge className={getStatusColor(siStatus.compliance.firs_status)}>
                  {siStatus.compliance.firs_status}
                </Badge>
              </div>
              <Shield className="h-8 w-8 text-purple-600" />
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Success Rate</p>
                <p className="text-xl font-bold text-orange-600">
                  {siStatus.processing.success_rate}%
                </p>
              </div>
              <BarChart3 className="h-8 w-8 text-orange-600" />
            </div>
          </Card>
        </div>
      </div>

      {/* Main Interface */}
      <div className="flex">
        {/* Sidebar Navigation */}
        <div className="w-80 bg-white border-r border-gray-200 h-[calc(100vh-140px)]">
          <div className="p-4">
            <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical">
              <TabsList className="grid w-full grid-cols-1 h-auto gap-1">
                <TabsTrigger value="integration" className="justify-start">
                  <Building2 className="h-4 w-4 mr-2" />
                  Integration Hub
                </TabsTrigger>
                <TabsTrigger value="processing" className="justify-start">
                  <Activity className="h-4 w-4 mr-2" />
                  Processing Center
                </TabsTrigger>
                <TabsTrigger value="compliance" className="justify-start">
                  <Shield className="h-4 w-4 mr-2" />
                  Compliance
                </TabsTrigger>
                <TabsTrigger value="workflow" className="justify-start">
                  <Workflow className="h-4 w-4 mr-2" />
                  Workflows
                </TabsTrigger>
                <TabsTrigger value="tools" className="justify-start">
                  <Wrench className="h-4 w-4 mr-2" />
                  System Tools
                </TabsTrigger>
              </TabsList>
            </Tabs>
          </div>

          <Separator />

          <ScrollArea className="h-[calc(100vh-240px)]">
            <div className="p-4">
              {/* Navigation Items */}
              {(['integration', 'processing', 'compliance', 'workflow', 'tools'] as const).map(category => (
                <div key={category} className={`mb-6 ${activeTab !== category ? 'hidden' : ''}`}>
                  <div className="flex items-center gap-2 mb-3">
                    <CategoryIcon category={category} />
                    <h3 className="font-medium text-gray-900 capitalize">
                      {category === 'integration' ? 'Integration Hub' :
                       category === 'processing' ? 'Processing Center' :
                       category}
                    </h3>
                  </div>
                  <div className="space-y-2">
                    {getNavigationByCategory(category).map(item => (
                      <button
                        key={item.id}
                        onClick={() => setActiveComponent(item.id)}
                        className={`w-full text-left p-3 rounded-lg border transition-colors ${
                          activeComponent === item.id
                            ? 'bg-blue-50 border-blue-200 text-blue-900'
                            : 'bg-white border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {item.icon}
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">{item.label}</span>
                              {item.status === 'beta' && (
                                <Badge variant="secondary" className="text-xs">Beta</Badge>
                              )}
                              {item.status === 'coming_soon' && (
                                <Badge variant="outline" className="text-xs">Soon</Badge>
                              )}
                            </div>
                            <p className="text-xs text-gray-600 mt-1">{item.description}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </div>

        {/* Main Content Area */}
        <div className="flex-1 p-6 h-[calc(100vh-140px)] overflow-auto">
          {siStatus.compliance.outstanding_issues > 0 && (
            <Alert className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                You have {siStatus.compliance.outstanding_issues} outstanding compliance issues that require attention.
              </AlertDescription>
            </Alert>
          )}

          <ActiveComponent />
        </div>
      </div>
    </div>
  );
}