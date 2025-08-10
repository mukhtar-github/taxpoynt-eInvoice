/**
 * TaxPoynt Admin Grant Dashboard
 * =============================
 * Admin-only interface for tracking FIRS grant eligibility and compliance.
 * Used by TaxPoynt administrators to monitor grant milestones and show evidence to FIRS.
 * 
 * NOT for public consumption - Internal compliance tool only.
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface GrantMilestone {
  id: string;
  title: string;
  description: string;
  target: number;
  current: number;
  unit: string;
  deadline: string;
  status: 'completed' | 'in_progress' | 'at_risk' | 'overdue';
  evidenceDocuments: string[];
  firsVerified: boolean;
}

interface KPIMetric {
  id: string;
  name: string;
  value: number;
  target: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  trendPercentage: number;
  category: 'onboarding' | 'compliance' | 'performance' | 'revenue';
}

// Grant milestones (based on FIRS APP certification requirements)
const grantMilestones: GrantMilestone[] = [
  {
    id: 'taxpayer_onboarding_q1',
    title: 'Q1 Taxpayer Onboarding',
    description: 'Onboard 500 taxpayers to e-invoicing platform',
    target: 500,
    current: 387,
    unit: 'taxpayers',
    deadline: '2024-03-31',
    status: 'in_progress',
    evidenceDocuments: [
      'Q1_Onboarding_Report.pdf',
      'Taxpayer_Registration_Evidence.xlsx',
      'FIRS_Compliance_Verification.pdf'
    ],
    firsVerified: false
  },
  {
    id: 'compliance_rate_target',
    title: 'FIRS Compliance Rate',
    description: 'Maintain 99%+ FIRS compliance rate for all processed invoices',
    target: 99,
    current: 99.7,
    unit: '% compliance',
    deadline: '2024-12-31',
    status: 'completed',
    evidenceDocuments: [
      'Compliance_Rate_Report.pdf',
      'FIRS_Validation_Results.xlsx',
      'Error_Rate_Analysis.pdf'
    ],
    firsVerified: true
  },
  {
    id: 'integration_milestone',
    title: 'ERP Integration Target',
    description: 'Successfully integrate with 20 different ERP systems',
    target: 20,
    current: 15,
    unit: 'ERP systems',
    deadline: '2024-06-30',
    status: 'in_progress',
    evidenceDocuments: [
      'ERP_Integration_Matrix.xlsx',
      'Technical_Certification_Reports.pdf'
    ],
    firsVerified: false
  },
  {
    id: 'revenue_sharing_performance',
    title: 'Revenue Sharing Performance',
    description: 'Generate ₦50M in tax revenue for FIRS through platform',
    target: 50000000,
    current: 32500000,
    unit: '₦ tax revenue',
    deadline: '2024-12-31',
    status: 'in_progress',
    evidenceDocuments: [
      'Revenue_Impact_Analysis.pdf',
      'FIRS_Tax_Collection_Report.xlsx'
    ],
    firsVerified: false
  }
];

const kpiMetrics: KPIMetric[] = [
  {
    id: 'active_taxpayers',
    name: 'Active Taxpayers',
    value: 1247,
    target: 2000,
    unit: 'users',
    trend: 'up',
    trendPercentage: 12.5,
    category: 'onboarding'
  },
  {
    id: 'monthly_invoices',
    name: 'Monthly Invoices Processed',
    value: 45673,
    target: 60000,
    unit: 'invoices',
    trend: 'up',
    trendPercentage: 8.3,
    category: 'performance'
  },
  {
    id: 'compliance_rate',
    name: 'FIRS Compliance Rate',
    value: 99.7,
    target: 99.0,
    unit: '%',
    trend: 'stable',
    trendPercentage: 0.2,
    category: 'compliance'
  },
  {
    id: 'error_rate',
    name: 'Invoice Error Rate',
    value: 0.3,
    target: 1.0,
    unit: '%',
    trend: 'down',
    trendPercentage: -15.2,
    category: 'compliance'
  },
  {
    id: 'monthly_revenue',
    name: 'Monthly Revenue (SI)',
    value: 8750000,
    target: 12000000,
    unit: '₦',
    trend: 'up',
    trendPercentage: 18.7,
    category: 'revenue'
  },
  {
    id: 'grant_revenue',
    name: 'Grant Revenue (APP)',
    value: 3200000,
    target: 4000000,
    unit: '₦',
    trend: 'up',
    trendPercentage: 6.4,
    category: 'revenue'
  }
];

interface AdminGrantDashboardProps {
  currentUser: {
    role: 'admin';
    name: string;
    permissions: string[];
  };
}

export const AdminGrantDashboard: React.FC<AdminGrantDashboardProps> = ({ currentUser }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'milestones' | 'kpis' | 'evidence'>('overview');
  const [selectedMilestone, setSelectedMilestone] = useState<string | null>(null);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-NG').format(num);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'in_progress': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'at_risk': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'overdue': return 'bg-red-100 text-red-800 border-red-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      case 'stable': return '➡️';
      default: return '📊';
    }
  };

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Grant Status Summary */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">FIRS Grant Status Overview</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {grantMilestones.filter(m => m.status === 'completed').length}
            </div>
            <div className="text-sm text-gray-600">Completed Milestones</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {grantMilestones.filter(m => m.status === 'in_progress').length}
            </div>
            <div className="text-sm text-gray-600">In Progress</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {grantMilestones.filter(m => m.status === 'at_risk').length}
            </div>
            <div className="text-sm text-gray-600">At Risk</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">
              {grantMilestones.filter(m => m.firsVerified).length}/{grantMilestones.length}
            </div>
            <div className="text-sm text-gray-600">FIRS Verified</div>
          </div>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {kpiMetrics.map((metric) => (
          <div key={metric.id} className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900">{metric.name}</h4>
              <span className="text-2xl">{getTrendIcon(metric.trend)}</span>
            </div>
            
            <div className="mb-4">
              <div className="text-2xl font-bold text-gray-900">
                {metric.unit === '₦' ? formatCurrency(metric.value) : formatNumber(metric.value)}
                {metric.unit !== '₦' && <span className="text-sm text-gray-500 ml-1">{metric.unit}</span>}
              </div>
              <div className="text-sm text-gray-600">
                Target: {metric.unit === '₦' ? formatCurrency(metric.target) : formatNumber(metric.target)} {metric.unit !== '₦' && metric.unit}
              </div>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs text-gray-600 mb-1">
                <span>Progress</span>
                <span>{Math.round((metric.value / metric.target) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${Math.min((metric.value / metric.target) * 100, 100)}%` }}
                />
              </div>
            </div>

            {/* Trend */}
            <div className={`text-xs font-medium ${
              metric.trend === 'up' ? 'text-green-600' : 
              metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
            }`}>
              {metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'} 
              {Math.abs(metric.trendPercentage)}% vs last month
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderMilestones = () => (
    <div className="space-y-4">
      {grantMilestones.map((milestone) => (
        <div key={milestone.id} className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <div className="flex items-center mb-2">
                <h3 className="text-lg font-semibold text-gray-900 mr-3">{milestone.title}</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor(milestone.status)}`}>
                  {milestone.status.replace('_', ' ').toUpperCase()}
                </span>
                {milestone.firsVerified && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium">
                    ✅ FIRS Verified
                  </span>
                )}
              </div>
              <p className="text-gray-600 mb-3">{milestone.description}</p>
              <div className="text-sm text-gray-500">
                Deadline: {new Date(milestone.deadline).toLocaleDateString('en-NG')}
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="mb-4">
            <div className="flex justify-between text-sm mb-2">
              <span className="text-gray-700">Progress</span>
              <span className="font-medium">
                {formatNumber(milestone.current)} / {formatNumber(milestone.target)} {milestone.unit}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className={`h-3 rounded-full ${
                  milestone.status === 'completed' ? 'bg-green-500' :
                  milestone.status === 'at_risk' ? 'bg-yellow-500' :
                  milestone.status === 'overdue' ? 'bg-red-500' : 'bg-blue-500'
                }`}
                style={{ width: `${Math.min((milestone.current / milestone.target) * 100, 100)}%` }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {Math.round((milestone.current / milestone.target) * 100)}% complete
            </div>
          </div>

          {/* Evidence Documents */}
          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-2">Evidence Documents</h4>
            <div className="flex flex-wrap gap-2">
              {milestone.evidenceDocuments.map((doc, index) => (
                <span key={index} className="px-3 py-1 bg-blue-50 text-blue-700 text-xs rounded-full border border-blue-200">
                  📄 {doc}
                </span>
              ))}
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end mt-4 pt-4 border-t">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSelectedMilestone(milestone.id)}
              className="mr-2"
            >
              View Details
            </Button>
            {!milestone.firsVerified && milestone.status === 'completed' && (
              <Button
                variant="success"
                size="sm"
                role="admin"
              >
                Submit to FIRS
              </Button>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">FIRS Grant Dashboard</h1>
              <p className="text-gray-600 mt-2">
                Administrative interface for tracking grant milestones and compliance evidence
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-600">Admin: {currentUser.name}</span>
              <Button variant="outline" size="sm">
                Export Report
              </Button>
              <Button variant="primary" size="sm" role="admin">
                Generate FIRS Evidence Package
              </Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex space-x-6 mt-6 border-b border-gray-200">
            {[
              { id: 'overview', label: 'Overview' },
              { id: 'milestones', label: 'Grant Milestones' },
              { id: 'kpis', label: 'KPI Metrics' },
              { id: 'evidence', label: 'Evidence Management' }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`pb-3 px-1 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'milestones' && renderMilestones()}
        {activeTab === 'kpis' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {kpiMetrics.map((metric) => (
              <div key={metric.id} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">{metric.name}</h4>
                  <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
                    {metric.category}
                  </span>
                </div>
                
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {metric.unit === '₦' ? formatCurrency(metric.value) : formatNumber(metric.value)}
                  {metric.unit !== '₦' && <span className="text-sm text-gray-500 ml-1">{metric.unit}</span>}
                </div>

                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">
                    Target: {metric.unit === '₦' ? formatCurrency(metric.target) : formatNumber(metric.target)} {metric.unit !== '₦' && metric.unit}
                  </span>
                  <span className={`font-medium ${
                    metric.trend === 'up' ? 'text-green-600' : 
                    metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {metric.trend === 'up' ? '↗' : metric.trend === 'down' ? '↘' : '→'} 
                    {Math.abs(metric.trendPercentage)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
        {activeTab === 'evidence' && (
          <div className="bg-white rounded-xl border border-gray-200 p-8 text-center">
            <div className="text-6xl mb-4">📋</div>
            <h3 className="text-xl font-bold text-gray-900 mb-2">Evidence Management Center</h3>
            <p className="text-gray-600 mb-6">
              Comprehensive document management for FIRS compliance evidence
            </p>
            <Button variant="primary" size="lg" role="admin">
              Access Evidence Vault
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};