import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { Progress } from '../../ui/Progress';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Shield, 
  RefreshCw, 
  FileText, 
  Calendar, 
  Award,
  HelpCircle,
  Loader2
} from 'lucide-react';
import { useToast } from '../../ui/Toast';
import ContextualHelp from '../common/ContextualHelp';
import apiService from '../../../utils/apiService';

interface ComplianceSummaryVisualizationProps {
  organizationId: string;
  refreshInterval?: number;
}

interface ComplianceStatus {
  overall: {
    score: number;
    status: 'compliant' | 'partial' | 'non-compliant';
    lastUpdated: string;
  };
  categories: Array<{
    id: string;
    name: string;
    status: 'compliant' | 'partial' | 'non-compliant';
    score: number;
    items: Array<{
      id: string;
      name: string;
      status: 'compliant' | 'partial' | 'non-compliant';
      message: string;
    }>;
  }>;
  recentChanges: Array<{
    id: string;
    date: string;
    category: string;
    description: string;
    impact: 'positive' | 'negative' | 'neutral';
  }>;
}

const ComplianceSummaryVisualization: React.FC<ComplianceSummaryVisualizationProps> = ({ 
  organizationId,
  refreshInterval = 60000 
}) => {
  const [complianceData, setComplianceData] = useState<ComplianceStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);
  const toast = useToast();
  
  // Help content for contextual help
  const complianceHelp = {
    overview: "The Compliance Summary visualizes your organization's adherence to FIRS e-invoicing regulations.",
    scoring: "Compliance scores are calculated based on certificate validity, transmission success rates, and regulatory adherence.",
    categories: "Each category represents a key area of compliance with detailed requirements.",
    actions: "Recommended actions help prioritize steps to improve compliance status."
  };
  
  useEffect(() => {
    fetchComplianceData();
    
    const timer = setInterval(() => {
      fetchComplianceData();
    }, refreshInterval);
    
    return () => clearInterval(timer);
  }, [organizationId, refreshInterval]);
  
  const fetchComplianceData = async () => {
    setLoading(true);
    
    try {
      const response = await apiService.get(`/api/v1/organizations/${organizationId}/compliance-status`);
      if (response.data) {
        setComplianceData(response.data);
      }
    } catch (err) {
      console.error('Error fetching compliance data:', err);
      setError('Failed to load compliance data. Please try again.');
      toast({
        title: 'Error',
        description: 'Failed to load compliance data',
        status: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleRefresh = () => {
    fetchComplianceData();
    toast({
      title: 'Refreshed',
      description: 'Compliance data has been refreshed',
      status: 'info'
    });
  };
  
  const toggleCategory = (categoryId: string) => {
    if (expandedCategory === categoryId) {
      setExpandedCategory(null);
    } else {
      setExpandedCategory(categoryId);
    }
  };
  
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'compliant':
        return 'bg-green-500';
      case 'partial':
        return 'bg-yellow-500';
      case 'non-compliant':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'partial':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'non-compliant':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return null;
    }
  };
  
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'compliant':
        return <Badge className="bg-green-100 text-green-800">Compliant</Badge>;
      case 'partial':
        return <Badge className="bg-yellow-100 text-yellow-800">Partially Compliant</Badge>;
      case 'non-compliant':
        return <Badge className="bg-red-100 text-red-800">Non-Compliant</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };
  
  // If we don't have real data yet, let's use a mock data for visualization
  const mockComplianceData: ComplianceStatus = {
    overall: {
      score: 85,
      status: 'partial',
      lastUpdated: new Date().toISOString()
    },
    categories: [
      {
        id: 'certificates',
        name: 'Digital Certificates',
        status: 'compliant',
        score: 100,
        items: [
          {
            id: 'cert-1',
            name: 'Valid signing certificate',
            status: 'compliant',
            message: 'Organization has a valid signing certificate'
          },
          {
            id: 'cert-2',
            name: 'Certificate not expired',
            status: 'compliant',
            message: 'Certificate is valid until 2026-01-15'
          }
        ]
      },
      {
        id: 'transmissions',
        name: 'Transmission Compliance',
        status: 'partial',
        score: 78,
        items: [
          {
            id: 'trans-1',
            name: 'Successful transmission rate',
            status: 'partial',
            message: '78% of transmissions successful in the last 30 days'
          },
          {
            id: 'trans-2',
            name: 'Error resolution time',
            status: 'partial',
            message: 'Average resolution time is 4.2 hours'
          }
        ]
      },
      {
        id: 'format',
        name: 'Invoice Format Compliance',
        status: 'compliant',
        score: 92,
        items: [
          {
            id: 'format-1',
            name: 'Required fields present',
            status: 'compliant',
            message: 'All invoices contain required fields'
          },
          {
            id: 'format-2',
            name: 'VAT calculation',
            status: 'compliant',
            message: 'VAT calculations are accurate'
          }
        ]
      },
      {
        id: 'reporting',
        name: 'Reporting & Auditing',
        status: 'non-compliant',
        score: 45,
        items: [
          {
            id: 'report-1',
            name: 'Monthly reports',
            status: 'non-compliant',
            message: 'Missing monthly reports for April and May'
          },
          {
            id: 'report-2',
            name: 'Audit trail',
            status: 'partial',
            message: 'Audit trail exists but is incomplete'
          }
        ]
      }
    ],
    recentChanges: [
      {
        id: 'change-1',
        date: new Date(Date.now() - 86400000).toISOString(),
        category: 'Transmission Compliance',
        description: 'Transmission success rate improved from 75% to 78%',
        impact: 'positive'
      },
      {
        id: 'change-2',
        date: new Date(Date.now() - 172800000).toISOString(),
        category: 'Reporting & Auditing',
        description: 'Missing monthly report for May',
        impact: 'negative'
      }
    ]
  };
  
  const displayData = complianceData || mockComplianceData;
  
  return (
    <div className="space-y-6">
      <Card className="border-l-4 border-l-cyan-500">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-center">
            <div className="flex items-center">
              <Shield className="h-5 w-5 text-cyan-600 mr-2" />
              <CardTitle>Compliance Summary</CardTitle>
              <ContextualHelp content={complianceHelp.overview}>
                <HelpCircle className="h-4 w-4 ml-2 text-gray-400" />
              </ContextualHelp>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              <span className="ml-1">Refresh</span>
            </Button>
          </div>
        </CardHeader>
        
        <CardContent>
          {loading && !displayData ? (
            <div className="flex justify-center items-center p-8">
              <Loader2 className="h-8 w-8 animate-spin text-cyan-600" />
            </div>
          ) : (
            <>
              <div className="mb-6">
                <div className="bg-white p-6 rounded-lg border shadow-sm">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">Overall Compliance Status</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Last updated: {new Date(displayData.overall.lastUpdated).toLocaleString()}
                      </p>
                    </div>
                    {getStatusBadge(displayData.overall.status)}
                  </div>
                  
                  <div className="mb-4">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium">Compliance Score</span>
                      <span className="text-sm font-medium">{displayData.overall.score}%</span>
                    </div>
                    <Progress value={displayData.overall.score} max={100} className="h-2" />
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
                    <div className="flex items-center p-3 rounded-md bg-green-50 border border-green-200">
                      <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
                      <div>
                        <p className="text-xs text-green-800 font-medium">Strengths</p>
                        <p className="text-sm text-green-700">Digital Certificates</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center p-3 rounded-md bg-yellow-50 border border-yellow-200">
                      <AlertTriangle className="h-5 w-5 text-yellow-500 mr-2" />
                      <div>
                        <p className="text-xs text-yellow-800 font-medium">Areas for Improvement</p>
                        <p className="text-sm text-yellow-700">Transmission Success Rate</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center p-3 rounded-md bg-red-50 border border-red-200">
                      <XCircle className="h-5 w-5 text-red-500 mr-2" />
                      <div>
                        <p className="text-xs text-red-800 font-medium">Critical Issues</p>
                        <p className="text-sm text-red-700">Missing Monthly Reports</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <h3 className="text-lg font-medium text-gray-900 mb-4">Compliance Categories</h3>
              
              <div className="space-y-3 mb-6">
                {displayData.categories.map(category => (
                  <div key={category.id} className="border rounded-lg overflow-hidden">
                    <div 
                      className="flex justify-between items-center p-4 cursor-pointer hover:bg-gray-50"
                      onClick={() => toggleCategory(category.id)}
                    >
                      <div className="flex items-center">
                        {getStatusIcon(category.status)}
                        <span className="font-medium ml-2">{category.name}</span>
                        <span className="ml-2">{getStatusBadge(category.status)}</span>
                      </div>
                      <div className="flex items-center">
                        <span className="text-sm font-medium mr-4">{category.score}%</span>
                        <svg 
                          className={`h-5 w-5 transition-transform ${expandedCategory === category.id ? 'transform rotate-180' : ''}`} 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </div>
                    </div>
                    
                    {expandedCategory === category.id && (
                      <div className="p-4 border-t bg-gray-50">
                        {category.items.map(item => (
                          <div key={item.id} className={`compliance-status-card compliance-status-${item.status}`}>
                            <div className="mr-3">
                              {getStatusIcon(item.status)}
                            </div>
                            <div>
                              <h4 className="text-sm font-medium">{item.name}</h4>
                              <p className="text-xs mt-1">{item.message}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              
              <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Compliance Changes</h3>
              
              <div className="space-y-3">
                {displayData.recentChanges.map(change => (
                  <div 
                    key={change.id} 
                    className={`p-3 rounded-md border ${
                      change.impact === 'positive' ? 'bg-green-50 border-green-200' : 
                      change.impact === 'negative' ? 'bg-red-50 border-red-200' : 
                      'bg-gray-50 border-gray-200'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex">
                        {change.impact === 'positive' ? (
                          <CheckCircle2 className="h-5 w-5 text-green-500 mr-2" />
                        ) : change.impact === 'negative' ? (
                          <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
                        ) : (
                          <Calendar className="h-5 w-5 text-gray-500 mr-2" />
                        )}
                        <div>
                          <p className="text-sm font-medium">{change.category}</p>
                          <p className="text-xs mt-1">{change.description}</p>
                        </div>
                      </div>
                      <span className="text-xs text-gray-500">
                        {new Date(change.date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="mt-6 p-4 bg-cyan-50 rounded-md border border-cyan-200">
                <div className="flex items-start">
                  <Award className="h-5 w-5 text-cyan-600 mr-3 mt-0.5" />
                  <div>
                    <h4 className="text-sm font-medium text-cyan-800">Compliance Recommendations</h4>
                    <p className="text-sm text-cyan-700 mt-1">
                      To improve your compliance score, focus on submitting missing monthly reports
                      and improving transmission success rates. Schedule regular certificate renewals
                      to maintain your current certification status.
                    </p>
                    <div className="mt-3">
                      <Button size="sm" className="bg-cyan-600 hover:bg-cyan-700">
                        <FileText className="h-4 w-4 mr-1" />
                        Generate Compliance Report
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ComplianceSummaryVisualization;
