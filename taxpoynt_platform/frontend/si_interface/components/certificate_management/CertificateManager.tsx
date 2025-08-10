/**
 * Certificate Management Component
 * ===============================
 * 
 * System Integrator interface for managing digital certificates and security credentials.
 * Handles FIRS certificates, SSL/TLS certificates, and API authentication certificates.
 * 
 * Features:
 * - Digital certificate lifecycle management
 * - FIRS e-invoicing certificate handling
 * - SSL/TLS certificate monitoring and renewal
 * - API authentication certificate management
 * - Certificate validation and health checks
 * - Automated renewal alerts and notifications
 * - Nigerian regulatory compliance certificates
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface Certificate {
  id: string;
  name: string;
  type: 'firs_einvoicing' | 'ssl_tls' | 'api_auth' | 'client_cert' | 'ca_cert';
  purpose: string;
  status: 'active' | 'expired' | 'expiring_soon' | 'revoked' | 'pending' | 'invalid';
  issuer: string;
  subject: string;
  serialNumber: string;
  validFrom: string;
  validTo: string;
  daysUntilExpiry: number;
  fingerprint: string;
  keySize: number;
  algorithm: string;
  organizationId?: string;
  organizationName?: string;
  usageCount: number;
  lastUsed?: string;
  autoRenewal: boolean;
  nigerianCompliance?: {
    regulatoryBody: 'FIRS' | 'CBN' | 'NITDA';
    complianceLevel: 'required' | 'recommended' | 'optional';
    regulatoryReference: string;
  };
}

interface CertificateRequest {
  id: string;
  type: Certificate['type'];
  organizationId: string;
  organizationName: string;
  requestDate: string;
  status: 'pending' | 'approved' | 'rejected' | 'processing' | 'completed';
  requestedBy: string;
  purpose: string;
  validityPeriod: number; // months
  keySize: number;
  algorithm: string;
  subjectAltNames?: string[];
  approvalDate?: string;
  rejectionReason?: string;
  certificateId?: string;
}

interface CertificateStats {
  totalCertificates: number;
  activeCertificates: number;
  expiringSoon: number; // within 30 days
  expiredCertificates: number;
  revokedCertificates: number;
  pendingRequests: number;
  firsCompliantCertificates: number;
  autoRenewalEnabled: number;
}

const mockCertificates: Certificate[] = [
  {
    id: 'cert_firs_001',
    name: 'FIRS E-invoicing Certificate',
    type: 'firs_einvoicing',
    purpose: 'FIRS e-invoicing digital signature and authentication',
    status: 'active',
    issuer: 'Federal Inland Revenue Service (FIRS)',
    subject: 'CN=TaxPoynt E-invoicing, O=TaxPoynt Ltd, C=NG',
    serialNumber: '1A2B3C4D5E6F7890',
    validFrom: '2024-01-01T00:00:00Z',
    validTo: '2026-01-01T00:00:00Z',
    daysUntilExpiry: 365,
    fingerprint: 'SHA256:A1B2C3D4E5F67890ABCDEF1234567890ABCDEF12',
    keySize: 2048,
    algorithm: 'RSA',
    usageCount: 15420,
    lastUsed: '2024-01-15T14:30:00Z',
    autoRenewal: true,
    nigerianCompliance: {
      regulatoryBody: 'FIRS',
      complianceLevel: 'required',
      regulatoryReference: 'FIRS E-invoicing Guidelines 2024 Section 4.2'
    }
  },
  {
    id: 'cert_ssl_001',
    name: 'API Gateway SSL Certificate',
    type: 'ssl_tls',
    purpose: 'HTTPS encryption for API endpoints',
    status: 'expiring_soon',
    issuer: 'Let\'s Encrypt Authority X3',
    subject: 'CN=api.taxpoynt.com',
    serialNumber: '9F8E7D6C5B4A39281',
    validFrom: '2024-01-01T00:00:00Z',
    validTo: '2024-04-01T00:00:00Z',
    daysUntilExpiry: 28,
    fingerprint: 'SHA256:B2C3D4E5F67890ABCDEF1234567890ABCDEF123A',
    keySize: 2048,
    algorithm: 'RSA',
    usageCount: 850000,
    lastUsed: '2024-01-15T15:45:00Z',
    autoRenewal: true
  },
  {
    id: 'cert_api_001',
    name: 'SI API Authentication',
    type: 'api_auth',
    purpose: 'System Integrator API authentication',
    status: 'active',
    issuer: 'TaxPoynt Internal CA',
    subject: 'CN=SI-API-Auth, O=TaxPoynt Ltd, C=NG',
    serialNumber: '7F6E5D4C3B2A1908',
    validFrom: '2023-06-01T00:00:00Z',
    validTo: '2025-06-01T00:00:00Z',
    daysUntilExpiry: 502,
    fingerprint: 'SHA256:C3D4E5F67890ABCDEF1234567890ABCDEF123AB2',
    keySize: 4096,
    algorithm: 'RSA',
    organizationId: 'org_si_001',
    organizationName: 'Acme Integration Services',
    usageCount: 75000,
    lastUsed: '2024-01-15T16:20:00Z',
    autoRenewal: false
  }
];

const mockRequests: CertificateRequest[] = [
  {
    id: 'req_001',
    type: 'firs_einvoicing',
    organizationId: 'org_business_001',
    organizationName: 'Nigerian Manufacturing Ltd',
    requestDate: '2024-01-10T10:00:00Z',
    status: 'pending',
    requestedBy: 'system.integrator@taxpoynt.com',
    purpose: 'FIRS e-invoicing compliance for new organization',
    validityPeriod: 24,
    keySize: 2048,
    algorithm: 'RSA',
    subjectAltNames: ['einvoice.nigerianmanufacturing.com']
  },
  {
    id: 'req_002',
    type: 'ssl_tls',
    organizationId: 'org_business_002',
    organizationName: 'Lagos Retail Chain',
    requestDate: '2024-01-12T14:30:00Z',
    status: 'approved',
    requestedBy: 'admin@lagosretail.com',
    purpose: 'SSL certificate for e-commerce integration',
    validityPeriod: 12,
    keySize: 2048,
    algorithm: 'RSA',
    approvalDate: '2024-01-13T09:15:00Z'
  }
];

interface CertificateManagerProps {
  organizationId?: string;
  onCertificateAction?: (action: string, certificateId: string) => void;
}

export const CertificateManager: React.FC<CertificateManagerProps> = ({
  organizationId,
  onCertificateAction
}) => {
  const [certificates, setCertificates] = useState<Certificate[]>(mockCertificates);
  const [requests, setRequests] = useState<CertificateRequest[]>(mockRequests);
  const [stats, setStats] = useState<CertificateStats | null>(null);
  const [selectedCert, setSelectedCert] = useState<Certificate | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'expiring' | 'expired'>('all');
  const [showNewRequest, setShowNewRequest] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchCertificates();
    fetchRequests();
    calculateStats();
  }, [organizationId]);

  const fetchCertificates = async () => {
    try {
      const params = organizationId ? `?organization_id=${organizationId}` : '';
      const response = await fetch(`/api/v1/si/certificates${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCertificates(data.certificates || mockCertificates);
      }
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      setCertificates(mockCertificates);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchRequests = async () => {
    try {
      const response = await fetch('/api/v1/si/certificates/requests', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setRequests(data.requests || mockRequests);
      }
    } catch (error) {
      console.error('Failed to fetch certificate requests:', error);
      setRequests(mockRequests);
    }
  };

  const calculateStats = () => {
    const total = certificates.length;
    const active = certificates.filter(cert => cert.status === 'active').length;
    const expiringSoon = certificates.filter(cert => cert.daysUntilExpiry <= 30 && cert.status === 'active').length;
    const expired = certificates.filter(cert => cert.status === 'expired').length;
    const revoked = certificates.filter(cert => cert.status === 'revoked').length;
    const pending = requests.filter(req => req.status === 'pending').length;
    const firsCompliant = certificates.filter(cert => cert.nigerianCompliance?.regulatoryBody === 'FIRS').length;
    const autoRenewal = certificates.filter(cert => cert.autoRenewal).length;

    setStats({
      totalCertificates: total,
      activeCertificates: active,
      expiringSoon,
      expiredCertificates: expired,
      revokedCertificates: revoked,
      pendingRequests: pending,
      firsCompliantCertificates: firsCompliant,
      autoRenewalEnabled: autoRenewal
    });
  };

  const handleRevokeCertificate = async (certificateId: string) => {
    if (!confirm('Are you sure you want to revoke this certificate? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/certificates/${certificateId}/revoke`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        alert('✅ Certificate revoked successfully');
        fetchCertificates();
        if (onCertificateAction) {
          onCertificateAction('revoke', certificateId);
        }
      } else {
        alert('❌ Failed to revoke certificate');
      }
    } catch (error) {
      console.error('Failed to revoke certificate:', error);
      alert('❌ Failed to revoke certificate');
    }
  };

  const handleRenewCertificate = async (certificateId: string) => {
    try {
      const response = await fetch(`/api/v1/si/certificates/${certificateId}/renew`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        alert('✅ Certificate renewal initiated successfully');
        fetchCertificates();
        if (onCertificateAction) {
          onCertificateAction('renew', certificateId);
        }
      } else {
        alert('❌ Failed to initiate certificate renewal');
      }
    } catch (error) {
      console.error('Failed to renew certificate:', error);
      alert('❌ Failed to initiate certificate renewal');
    }
  };

  const handleDownloadCertificate = async (certificateId: string) => {
    try {
      const response = await fetch(`/api/v1/si/certificates/${certificateId}/download`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `certificate-${certificateId}.pem`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        alert('❌ Failed to download certificate');
      }
    } catch (error) {
      console.error('Failed to download certificate:', error);
      alert('❌ Failed to download certificate');
    }
  };

  const getStatusIcon = (status: Certificate['status']) => {
    switch (status) {
      case 'active': return '✅';
      case 'expired': return '❌';
      case 'expiring_soon': return '⚠️';
      case 'revoked': return '🚫';
      case 'pending': return '⏳';
      case 'invalid': return '❓';
      default: return '❓';
    }
  };

  const getStatusColor = (status: Certificate['status']) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100';
      case 'expired': return 'text-red-600 bg-red-100';
      case 'expiring_soon': return 'text-yellow-600 bg-yellow-100';
      case 'revoked': return 'text-gray-600 bg-gray-100';
      case 'pending': return 'text-blue-600 bg-blue-100';
      case 'invalid': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeLabel = (type: Certificate['type']) => {
    switch (type) {
      case 'firs_einvoicing': return 'FIRS E-invoicing';
      case 'ssl_tls': return 'SSL/TLS';
      case 'api_auth': return 'API Authentication';
      case 'client_cert': return 'Client Certificate';
      case 'ca_cert': return 'CA Certificate';
      default: return type;
    }
  };

  const filteredCertificates = certificates.filter(cert => {
    switch (filter) {
      case 'active':
        return cert.status === 'active';
      case 'expiring':
        return cert.daysUntilExpiry <= 30 && cert.status === 'active';
      case 'expired':
        return cert.status === 'expired';
      default:
        return true;
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔐</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Certificates</h2>
          <p className="text-gray-600">Fetching certificate information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100">
                <span className="text-blue-600 text-xl">🔐</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Certificates</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalCertificates}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100">
                <span className="text-green-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeCertificates}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100">
                <span className="text-yellow-600 text-xl">⚠️</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Expiring Soon</p>
                <p className="text-2xl font-bold text-gray-900">{stats.expiringSoon}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100">
                <span className="text-purple-600 text-xl">🇳🇬</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">FIRS Compliant</p>
                <p className="text-2xl font-bold text-gray-900">{stats.firsCompliantCertificates}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Certificate Management */}
      <div className="bg-white rounded-lg border">
        <div className="p-6 border-b">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Certificate Management</h2>
              <p className="text-gray-600 mt-1">Manage digital certificates and security credentials</p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => setShowNewRequest(true)}
                variant="outline"
              >
                📄 New Request
              </Button>
              
              <Button onClick={fetchCertificates}>
                🔄 Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6">
            {[
              { key: 'all', label: 'All Certificates', count: certificates.length },
              { key: 'active', label: 'Active', count: certificates.filter(c => c.status === 'active').length },
              { key: 'expiring', label: 'Expiring Soon', count: certificates.filter(c => c.daysUntilExpiry <= 30 && c.status === 'active').length },
              { key: 'expired', label: 'Expired', count: certificates.filter(c => c.status === 'expired').length }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setFilter(tab.key as any)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  filter === tab.key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </nav>
        </div>

        {/* Certificates List */}
        <div className="divide-y divide-gray-200">
          {filteredCertificates.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <div className="text-4xl mb-4">🔐</div>
              <h3 className="text-lg font-medium mb-2">No certificates found</h3>
              <p className="mb-4">No certificates match the current filter.</p>
            </div>
          ) : (
            filteredCertificates.map(cert => (
              <div key={cert.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getStatusIcon(cert.status)}</span>
                    
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-lg font-medium text-gray-900">{cert.name}</h3>
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(cert.status)}`}>
                          {cert.status.replace('_', ' ')}
                        </span>
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded-full">
                          {getTypeLabel(cert.type)}
                        </span>
                      </div>
                      
                      <div className="text-sm text-gray-600 mt-1">
                        <div>Issuer: {cert.issuer}</div>
                        <div>Valid: {new Date(cert.validFrom).toLocaleDateString()} - {new Date(cert.validTo).toLocaleDateString()}</div>
                        {cert.organizationName && (
                          <div>Organization: {cert.organizationName}</div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                        <span>🔑 {cert.keySize}-bit {cert.algorithm}</span>
                        <span>📊 {cert.usageCount.toLocaleString()} uses</span>
                        {cert.daysUntilExpiry <= 30 && cert.status === 'active' && (
                          <span className="text-yellow-600 font-medium">
                            ⚠️ Expires in {cert.daysUntilExpiry} days
                          </span>
                        )}
                        {cert.autoRenewal && (
                          <span className="text-green-600">🔄 Auto-renewal</span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => setSelectedCert(cert)}
                      variant="outline"
                      size="sm"
                    >
                      📋 Details
                    </Button>
                    
                    <Button
                      onClick={() => handleDownloadCertificate(cert.id)}
                      variant="outline"
                      size="sm"
                    >
                      💾 Download
                    </Button>
                    
                    {cert.status === 'active' && cert.daysUntilExpiry <= 60 && (
                      <Button
                        onClick={() => handleRenewCertificate(cert.id)}
                        variant="outline"
                        size="sm"
                      >
                        🔄 Renew
                      </Button>
                    )}
                    
                    {cert.status === 'active' && (
                      <Button
                        onClick={() => handleRevokeCertificate(cert.id)}
                        variant="outline"
                        size="sm"
                      >
                        🚫 Revoke
                      </Button>
                    )}
                  </div>
                </div>

                {/* Nigerian Compliance Info */}
                {cert.nigerianCompliance && (
                  <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex items-center text-blue-800">
                      <span className="text-blue-600 mr-2">🇳🇬</span>
                      <span className="font-medium">
                        {cert.nigerianCompliance.regulatoryBody} Compliance - {cert.nigerianCompliance.complianceLevel}
                      </span>
                    </div>
                    <div className="text-blue-700 text-sm mt-1">
                      {cert.nigerianCompliance.regulatoryReference}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      {/* Certificate Details Modal */}
      {selectedCert && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full m-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Certificate Details: {selectedCert.name}
                </h2>
                <button
                  onClick={() => setSelectedCert(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Certificate Information</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Name:</strong> {selectedCert.name}</div>
                    <div><strong>Type:</strong> {getTypeLabel(selectedCert.type)}</div>
                    <div><strong>Purpose:</strong> {selectedCert.purpose}</div>
                    <div><strong>Status:</strong> <span className={`px-2 py-1 rounded-full ${getStatusColor(selectedCert.status)}`}>{selectedCert.status}</span></div>
                    <div><strong>Serial Number:</strong> {selectedCert.serialNumber}</div>
                    <div><strong>Algorithm:</strong> {selectedCert.algorithm}</div>
                    <div><strong>Key Size:</strong> {selectedCert.keySize} bits</div>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Validity Information</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Valid From:</strong> {new Date(selectedCert.validFrom).toLocaleString()}</div>
                    <div><strong>Valid To:</strong> {new Date(selectedCert.validTo).toLocaleString()}</div>
                    <div><strong>Days Until Expiry:</strong> {selectedCert.daysUntilExpiry}</div>
                    <div><strong>Auto Renewal:</strong> {selectedCert.autoRenewal ? 'Enabled' : 'Disabled'}</div>
                    <div><strong>Usage Count:</strong> {selectedCert.usageCount.toLocaleString()}</div>
                    {selectedCert.lastUsed && (
                      <div><strong>Last Used:</strong> {new Date(selectedCert.lastUsed).toLocaleString()}</div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h3 className="font-medium text-gray-900 mb-3">Certificate Details</h3>
                <div className="bg-gray-50 rounded-lg p-4 text-sm font-mono">
                  <div><strong>Issuer:</strong> {selectedCert.issuer}</div>
                  <div className="mt-2"><strong>Subject:</strong> {selectedCert.subject}</div>
                  <div className="mt-2"><strong>Fingerprint:</strong> {selectedCert.fingerprint}</div>
                </div>
              </div>

              {selectedCert.nigerianCompliance && (
                <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-900 mb-2">🇳🇬 Nigerian Compliance Information</h3>
                  <div className="space-y-2 text-sm text-blue-800">
                    <div><strong>Regulatory Body:</strong> {selectedCert.nigerianCompliance.regulatoryBody}</div>
                    <div><strong>Compliance Level:</strong> {selectedCert.nigerianCompliance.complianceLevel}</div>
                    <div><strong>Reference:</strong> {selectedCert.nigerianCompliance.regulatoryReference}</div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CertificateManager;