/**
 * Compliance Dashboard Page
 * ========================
 * 
 * System Integrator interface for monitoring Nigerian tax compliance status,
 * FIRS submission tracking, and regulatory compliance reporting.
 * 
 * Features:
 * - FIRS e-invoicing compliance monitoring
 * - Nigerian VAT and tax compliance tracking
 * - CBN financial regulation compliance
 * - NDPR data protection compliance
 * - Compliance reports and analytics
 * - Alert system for compliance issues
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface ComplianceStatus {
  category: 'firs' | 'vat' | 'cbn' | 'ndpr' | 'general';
  title: string;
  status: 'compliant' | 'warning' | 'non_compliant' | 'pending';
  score: number; // 0-100
  lastChecked: string;
  issues: ComplianceIssue[];
  recommendations: string[];
  regulatoryBody: string;
}

interface ComplianceIssue {
  id: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  title: string;
  description: string;
  impact: string;
  remediation: string;
  dueDate?: string;
  organizationId?: string;
  organizationName?: string;
}

interface FIRSSubmission {
  id: string;
  organizationId: string;
  organizationName: string;
  submissionDate: string;
  invoiceCount: number;
  totalAmount: number;
  status: 'submitted' | 'accepted' | 'rejected' | 'pending';
  firsReference?: string;
  rejectionReason?: string;
  responseTime?: number; // minutes
}

interface ComplianceMetrics {
  overallScore: number;
  totalOrganizations: number;
  compliantOrganizations: number;
  pendingIssues: number;
  criticalIssues: number;
  firsSubmissions: {
    total: number;
    successful: number;
    pending: number;
    failed: number;
    successRate: number;
  };
  vatCompliance: {
    registeredOrganizations: number;
    compliantSubmissions: number;
    overdueReturns: number;
  };
}

const mockComplianceData: ComplianceStatus[] = [
  {
    category: 'firs',
    title: 'FIRS E-invoicing Compliance',
    status: 'compliant',
    score: 92,
    lastChecked: '2024-01-15T10:30:00Z',
    regulatoryBody: 'Federal Inland Revenue Service',
    issues: [
      {
        id: 'firs_001',
        severity: 'medium',
        category: 'Invoice Format',
        title: 'Missing VAT Breakdown',
        description: '3 organizations have invoices without proper VAT breakdown',
        impact: 'May result in FIRS rejection of invoice submissions',
        remediation: 'Update invoice templates to include detailed VAT calculations',
        dueDate: '2024-01-30T00:00:00Z'
      }
    ],
    recommendations: [
      'Implement automated VAT calculation validation',
      'Regular training on FIRS invoice format requirements',
      'Set up real-time FIRS API validation'
    ]
  },
  {
    category: 'vat',
    title: 'VAT Compliance',
    status: 'warning',
    score: 78,
    lastChecked: '2024-01-15T09:15:00Z',
    regulatoryBody: 'Federal Inland Revenue Service',
    issues: [
      {
        id: 'vat_001',
        severity: 'high',
        category: 'VAT Registration',
        title: 'Unregistered VAT Organizations',
        description: '5 organizations require VAT registration due to revenue threshold',
        impact: 'Non-compliance with Nigerian VAT laws',
        remediation: 'Initiate VAT registration process for affected organizations',
        dueDate: '2024-01-25T00:00:00Z'
      }
    ],
    recommendations: [
      'Monitor organization revenue thresholds',
      'Automated VAT registration alerts',
      'Quarterly VAT compliance reviews'
    ]
  },
  {
    category: 'cbn',
    title: 'CBN Financial Regulations',
    status: 'compliant',
    score: 95,
    lastChecked: '2024-01-15T08:45:00Z',
    regulatoryBody: 'Central Bank of Nigeria',
    issues: [],
    recommendations: [
      'Continue monitoring foreign exchange transactions',
      'Maintain current KYC compliance standards'
    ]
  },
  {
    category: 'ndpr',
    title: 'NDPR Data Protection',
    status: 'compliant',
    score: 88,
    lastChecked: '2024-01-15T11:00:00Z',
    regulatoryBody: 'National Information Technology Development Agency',
    issues: [
      {
        id: 'ndpr_001',
        severity: 'low',
        category: 'Data Retention',
        title: 'Data Retention Policy Updates',
        description: '2 organizations need updated data retention policies',
        impact: 'Minor NDPR compliance gap',
        remediation: 'Update data retention policies to current NDPR standards',
        dueDate: '2024-02-15T00:00:00Z'
      }
    ],
    recommendations: [
      'Annual NDPR compliance audit',
      'Staff training on data protection',
      'Regular policy updates'
    ]
  }
];

interface ComplianceDashboardProps {
  organizationId?: string;
}

export const ComplianceDashboard: React.FC<ComplianceDashboardProps> = ({
  organizationId
}) => {
  const [complianceData, setComplianceData] = useState<ComplianceStatus[]>(mockComplianceData);
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [firsSubmissions, setFirsSubmissions] = useState<FIRSSubmission[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showDetails, setShowDetails] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchComplianceData();
    fetchMetrics();
    fetchFIRSSubmissions();
  }, [organizationId]);

  const fetchComplianceData = async () => {
    try {
      const params = organizationId ? `?organization_id=${organizationId}` : '';
      const response = await fetch(`/api/v1/si/compliance/status${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setComplianceData(data.compliance_status || mockComplianceData);
      }
    } catch (error) {
      console.error('Failed to fetch compliance data:', error);
      setComplianceData(mockComplianceData);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch('/api/v1/si/compliance/metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics);
      }
    } catch (error) {
      console.error('Failed to fetch compliance metrics:', error);
    }
  };

  const fetchFIRSSubmissions = async () => {
    try {
      const response = await fetch('/api/v1/si/compliance/firs-submissions', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setFirsSubmissions(data.submissions || []);
      }
    } catch (error) {
      console.error('Failed to fetch FIRS submissions:', error);
    }
  };

  const getStatusColor = (status: ComplianceStatus['status']) => {
    switch (status) {
      case 'compliant':
        return 'text-green-800 bg-green-100 border-green-200';
      case 'warning':
        return 'text-yellow-800 bg-yellow-100 border-yellow-200';
      case 'non_compliant':
        return 'text-red-800 bg-red-100 border-red-200';
      case 'pending':
        return 'text-blue-800 bg-blue-100 border-blue-200';
      default:
        return 'text-gray-800 bg-gray-100 border-gray-200';
    }
  };

  const getStatusIcon = (status: ComplianceStatus['status']) => {
    switch (status) {
      case 'compliant':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'non_compliant':
        return '❌';
      case 'pending':
        return '⏳';
      default:
        return '❓';
    }
  };

  const getSeverityColor = (severity: ComplianceIssue['severity']) => {
    switch (severity) {
      case 'critical':
        return 'text-red-800 bg-red-100';
      case 'high':
        return 'text-orange-800 bg-orange-100';
      case 'medium':
        return 'text-yellow-800 bg-yellow-100';
      case 'low':
        return 'text-blue-800 bg-blue-100';
      default:
        return 'text-gray-800 bg-gray-100';
    }
  };

  const generateComplianceReport = async () => {
    try {
      const response = await fetch('/api/v1/si/compliance/reports/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_id: organizationId,
          report_type: 'comprehensive',
          include_recommendations: true
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `compliance-report-${new Date().toISOString().split('T')[0]}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('❌ Failed to generate compliance report');
      }
    } catch (error) {
      console.error('Failed to generate report:', error);
      alert('❌ Failed to generate compliance report');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Compliance Dashboard</h2>
          <p className="text-gray-600">Fetching compliance status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Compliance Dashboard</h1>
              <p className="text-gray-600 mt-2">
                Nigerian tax and regulatory compliance monitoring
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button onClick={generateComplianceReport} variant="outline">
                📄 Generate Report
              </Button>
              <Button onClick={fetchComplianceData}>
                🔄 Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-green-100">
                  <span className="text-green-600 text-xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Overall Score</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.overallScore}/100</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100">
                  <span className="text-blue-600 text-xl">🏢</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Organizations</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.compliantOrganizations}/{metrics.totalOrganizations}</p>
                  <p className="text-xs text-gray-500">compliant</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-yellow-100">
                  <span className="text-yellow-600 text-xl">⚠️</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending Issues</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.pendingIssues}</p>
                  <p className="text-xs text-red-500">{metrics.criticalIssues} critical</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100">
                  <span className="text-purple-600 text-xl">🇳🇬</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">FIRS Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{metrics.firsSubmissions.successRate.toFixed(1)}%</p>
                  <p className="text-xs text-gray-500">{metrics.firsSubmissions.successful}/{metrics.firsSubmissions.total} submissions</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Compliance Status */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-xl font-semibold text-gray-900">Compliance Status</h2>
                <p className="text-gray-600 mt-1">Nigerian regulatory compliance monitoring</p>
              </div>
              
              <div className="p-6 space-y-6">
                {complianceData.map(compliance => (
                  <div key={compliance.category} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{getStatusIcon(compliance.status)}</span>
                        <div>
                          <h3 className="font-semibold text-gray-900">{compliance.title}</h3>
                          <p className="text-sm text-gray-600">{compliance.regulatoryBody}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <div className="text-right">
                          <div className="text-2xl font-bold text-gray-900">{compliance.score}</div>
                          <div className="text-xs text-gray-500">Score</div>
                        </div>
                        <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(compliance.status)}`}>
                          {compliance.status.replace('_', ' ')}
                        </span>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                        <span>Compliance Score</span>
                        <span>{compliance.score}/100</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${
                            compliance.score >= 90 ? 'bg-green-500' :
                            compliance.score >= 70 ? 'bg-yellow-500' :
                            'bg-red-500'
                          }`}
                          style={{ width: `${compliance.score}%` }}
                        />
                      </div>
                    </div>

                    {/* Issues */}
                    {compliance.issues.length > 0 && (
                      <div className="mb-4">
                        <h4 className="font-medium text-gray-900 mb-2">Issues ({compliance.issues.length})</h4>
                        <div className="space-y-2">
                          {compliance.issues.slice(0, 2).map(issue => (
                            <div key={issue.id} className="bg-gray-50 rounded p-3">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2">
                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(issue.severity)}`}>
                                      {issue.severity}
                                    </span>
                                    <span className="font-medium text-gray-900">{issue.title}</span>
                                  </div>
                                  <p className="text-sm text-gray-600 mt-1">{issue.description}</p>
                                  {issue.dueDate && (
                                    <p className="text-xs text-gray-500 mt-1">
                                      Due: {new Date(issue.dueDate).toLocaleDateString()}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                          {compliance.issues.length > 2 && (
                            <button
                              onClick={() => setShowDetails(showDetails === compliance.category ? null : compliance.category)}
                              className="text-sm text-blue-600 hover:text-blue-800"
                            >
                              {showDetails === compliance.category ? 'Show less' : `View ${compliance.issues.length - 2} more issues`}
                            </button>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Expanded Issues */}
                    {showDetails === compliance.category && compliance.issues.length > 2 && (
                      <div className="mb-4 space-y-2">
                        {compliance.issues.slice(2).map(issue => (
                          <div key={issue.id} className="bg-gray-50 rounded p-3">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2">
                                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(issue.severity)}`}>
                                    {issue.severity}
                                  </span>
                                  <span className="font-medium text-gray-900">{issue.title}</span>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">{issue.description}</p>
                                <p className="text-sm text-blue-600 mt-2">{issue.remediation}</p>
                                {issue.dueDate && (
                                  <p className="text-xs text-gray-500 mt-1">
                                    Due: {new Date(issue.dueDate).toLocaleDateString()}
                                  </p>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Last Checked */}
                    <div className="text-xs text-gray-500">
                      Last checked: {new Date(compliance.lastChecked).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* FIRS Submissions */}
          <div>
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Recent FIRS Submissions</h2>
                <p className="text-gray-600 text-sm mt-1">Latest e-invoice submissions</p>
              </div>
              
              <div className="p-6">
                {firsSubmissions.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-4xl mb-2">📋</div>
                    <p>No recent submissions</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {firsSubmissions.slice(0, 5).map(submission => (
                      <div key={submission.id} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="font-medium text-gray-900">{submission.organizationName}</div>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            submission.status === 'accepted' ? 'bg-green-100 text-green-800' :
                            submission.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            submission.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            {submission.status}
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 space-y-1">
                          <div>📊 {submission.invoiceCount} invoices</div>
                          <div>💰 ₦{submission.totalAmount.toLocaleString()}</div>
                          <div>📅 {new Date(submission.submissionDate).toLocaleDateString()}</div>
                          {submission.firsReference && (
                            <div className="text-blue-600">🇳🇬 {submission.firsReference}</div>
                          )}
                        </div>

                        {submission.rejectionReason && (
                          <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                            ❌ {submission.rejectionReason}
                          </div>
                        )}
                      </div>
                    ))}
                    
                    {firsSubmissions.length > 5 && (
                      <button className="w-full text-sm text-blue-600 hover:text-blue-800 py-2">
                        View all submissions ({firsSubmissions.length})
                      </button>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="bg-white rounded-lg border mt-6">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
              </div>
              
              <div className="p-6 space-y-3">
                <Button className="w-full justify-start" variant="outline">
                  📊 Run Compliance Audit
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  🇳🇬 Check FIRS Status
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  📋 VAT Return Reminder
                </Button>
                <Button className="w-full justify-start" variant="outline">
                  🔔 Set Compliance Alerts
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceDashboard;