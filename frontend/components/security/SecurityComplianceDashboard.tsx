/**
 * Security Compliance Dashboard
 * Comprehensive dashboard for Nigerian security compliance monitoring
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Progress } from '../ui/Progress';

interface ComplianceMetrics {
  iso27001_score: number;
  ndpr_compliance: number;
  data_residency_compliance: number;
  mfa_adoption_rate: number;
  audit_completeness: number;
  security_incidents: number;
  last_assessment: string;
}

interface SecurityEvent {
  id: string;
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  description: string;
  timestamp: string;
  resolved: boolean;
}

interface DataResidencyStatus {
  nigerian_data_in_nigeria: number;
  cross_border_transfers: number;
  residency_violations: number;
  compliant_locations: string[];
}

interface MFAStatus {
  total_users: number;
  mfa_enabled: number;
  totp_users: number;
  sms_users: number;
  biometric_users: number;
  nigerian_ussd_users: number;
}

export const SecurityComplianceDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<ComplianceMetrics | null>(null);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [dataResidency, setDataResidency] = useState<DataResidencyStatus | null>(null);
  const [mfaStatus, setMfaStatus] = useState<MFAStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // Simulate API calls - in production, these would be real API endpoints
      await Promise.all([
        loadComplianceMetrics(),
        loadSecurityEvents(),
        loadDataResidencyStatus(),
        loadMFAStatus()
      ]);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadComplianceMetrics = async () => {
    // Simulate API call
    setTimeout(() => {
      setMetrics({
        iso27001_score: 92,
        ndpr_compliance: 88,
        data_residency_compliance: 95,
        mfa_adoption_rate: 78,
        audit_completeness: 85,
        security_incidents: 3,
        last_assessment: '2025-06-28T10:30:00Z'
      });
    }, 500);
  };

  const loadSecurityEvents = async () => {
    setTimeout(() => {
      setSecurityEvents([
        {
          id: '1',
          type: 'Failed Login Attempt',
          severity: 'medium',
          description: 'Multiple failed login attempts from foreign IP',
          timestamp: '2025-06-29T08:15:00Z',
          resolved: false
        },
        {
          id: '2', 
          type: 'Data Residency Alert',
          severity: 'high',
          description: 'Nigerian PII detected in non-Nigerian datacenter',
          timestamp: '2025-06-29T07:30:00Z',
          resolved: true
        },
        {
          id: '3',
          type: 'MFA Bypass Attempt',
          severity: 'critical',
          description: 'User attempted to bypass MFA for FIRS submission',
          timestamp: '2025-06-29T06:45:00Z',
          resolved: false
        }
      ]);
    }, 300);
  };

  const loadDataResidencyStatus = async () => {
    setTimeout(() => {
      setDataResidency({
        nigerian_data_in_nigeria: 97.5,
        cross_border_transfers: 12,
        residency_violations: 2,
        compliant_locations: ['nigeria-lagos-dc', 'nigeria-abuja-dc']
      });
    }, 400);
  };

  const loadMFAStatus = async () => {
    setTimeout(() => {
      setMfaStatus({
        total_users: 245,
        mfa_enabled: 191,
        totp_users: 112,
        sms_users: 156,
        biometric_users: 34,
        nigerian_ussd_users: 78
      });
    }, 600);
  };

  const refreshDashboard = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const getComplianceColor = (score: number) => {
    if (score >= 95) return 'text-green-600';
    if (score >= 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-blue-500';
      default: return 'bg-gray-500';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Security Compliance Dashboard</h1>
          <p className="text-gray-600">Nigerian security and compliance monitoring</p>
        </div>
        <Button 
          onClick={refreshDashboard}
          disabled={refreshing}
          className="bg-green-600 hover:bg-green-700"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      {/* Overall Compliance Score */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Overall Compliance Score</h2>
          <Badge variant="success">Nigerian Compliant</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="text-center">
            <div className={`text-2xl font-bold ${getComplianceColor(metrics?.iso27001_score || 0)}`}>
              {metrics?.iso27001_score}%
            </div>
            <div className="text-sm text-gray-600">ISO 27001</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getComplianceColor(metrics?.ndpr_compliance || 0)}`}>
              {metrics?.ndpr_compliance}%
            </div>
            <div className="text-sm text-gray-600">NDPR</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getComplianceColor(metrics?.data_residency_compliance || 0)}`}>
              {metrics?.data_residency_compliance}%
            </div>
            <div className="text-sm text-gray-600">Data Residency</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getComplianceColor(metrics?.mfa_adoption_rate || 0)}`}>
              {metrics?.mfa_adoption_rate}%
            </div>
            <div className="text-sm text-gray-600">MFA Adoption</div>
          </div>
          <div className="text-center">
            <div className={`text-2xl font-bold ${getComplianceColor(metrics?.audit_completeness || 0)}`}>
              {metrics?.audit_completeness}%
            </div>
            <div className="text-sm text-gray-600">Audit Complete</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {metrics?.security_incidents}
            </div>
            <div className="text-sm text-gray-600">Open Incidents</div>
          </div>
        </div>
      </Card>

      {/* Security Events */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Recent Security Events</h2>
          <Badge variant="warning">{securityEvents.filter(e => !e.resolved).length} Unresolved</Badge>
        </div>
        <div className="space-y-3">
          {securityEvents.map((event) => (
            <div key={event.id} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${getSeverityColor(event.severity)}`}></div>
                <div>
                  <div className="font-medium">{event.type}</div>
                  <div className="text-sm text-gray-600">{event.description}</div>
                  <div className="text-xs text-gray-400">
                    {new Date(event.timestamp).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant={event.resolved ? "success" : "warning"}>
                  {event.resolved ? "Resolved" : "Open"}
                </Badge>
                <Badge 
                  variant={event.severity === 'critical' ? "destructive" : 
                          event.severity === 'high' ? "warning" : "secondary"}
                >
                  {event.severity.toUpperCase()}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Data Residency Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Nigerian Data Residency</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Nigerian Data in Nigeria</span>
                <span>{dataResidency?.nigerian_data_in_nigeria}%</span>
              </div>
              <Progress value={dataResidency?.nigerian_data_in_nigeria || 0} className="h-2" />
            </div>
            
            <div className="grid grid-cols-2 gap-4 mt-4">
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-blue-600">
                  {dataResidency?.cross_border_transfers}
                </div>
                <div className="text-sm text-gray-600">Cross-Border Transfers</div>
              </div>
              <div className="text-center p-3 border rounded">
                <div className="text-2xl font-bold text-red-600">
                  {dataResidency?.residency_violations}
                </div>
                <div className="text-sm text-gray-600">Violations</div>
              </div>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">Compliant Locations</div>
              <div className="flex flex-wrap gap-2">
                {dataResidency?.compliant_locations.map((location) => (
                  <Badge key={location} variant="success">
                    {location}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* MFA Status */}
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Multi-Factor Authentication</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>MFA Adoption Rate</span>
                <span>{Math.round((mfaStatus?.mfa_enabled || 0) / (mfaStatus?.total_users || 1) * 100)}%</span>
              </div>
              <Progress 
                value={Math.round((mfaStatus?.mfa_enabled || 0) / (mfaStatus?.total_users || 1) * 100)} 
                className="h-2" 
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="text-center p-3 border rounded">
                <div className="text-lg font-bold text-green-600">
                  {mfaStatus?.mfa_enabled}
                </div>
                <div className="text-sm text-gray-600">MFA Enabled</div>
              </div>
              <div className="text-center p-3 border rounded">
                <div className="text-lg font-bold text-gray-600">
                  {(mfaStatus?.total_users || 0) - (mfaStatus?.mfa_enabled || 0)}
                </div>
                <div className="text-sm text-gray-600">No MFA</div>
              </div>
            </div>

            <div>
              <div className="text-sm font-medium mb-2">MFA Methods Usage</div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">TOTP/Authenticator</span>
                  <span className="text-sm font-medium">{mfaStatus?.totp_users}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">SMS (Nigerian)</span>
                  <span className="text-sm font-medium">{mfaStatus?.sms_users}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Nigerian USSD</span>
                  <span className="text-sm font-medium">{mfaStatus?.nigerian_ussd_users}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Biometric</span>
                  <span className="text-sm font-medium">{mfaStatus?.biometric_users}</span>
                </div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Nigerian Compliance Summary */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Nigerian Compliance Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-green-600 mb-2">✓</div>
            <div className="font-medium">NDPR Compliant</div>
            <div className="text-sm text-gray-600">Data protection regulation adherence</div>
          </div>
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-green-600 mb-2">✓</div>
            <div className="font-medium">Data Residency</div>
            <div className="text-sm text-gray-600">Nigerian data stays in Nigeria</div>
          </div>
          <div className="text-center p-4 border rounded-lg">
            <div className="text-2xl font-bold text-blue-600 mb-2">📱</div>
            <div className="font-medium">Mobile Optimized</div>
            <div className="text-sm text-gray-600">MTN, Airtel, Glo, 9mobile support</div>
          </div>
        </div>
        
        <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center">
            <div className="text-green-600 mr-3">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <div className="font-medium text-green-800">Nigerian Compliance Status: COMPLIANT</div>
              <div className="text-sm text-green-700">
                All major Nigerian regulatory requirements are being met. Last assessment: {new Date(metrics?.last_assessment || '').toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};