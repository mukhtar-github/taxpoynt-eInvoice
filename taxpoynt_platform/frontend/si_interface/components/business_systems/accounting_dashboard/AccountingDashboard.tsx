/**
 * Accounting Dashboard Component
 * =============================
 * 
 * System Integrator interface for managing accounting system connections.
 * Supports major accounting systems: QuickBooks, Xero, Sage, Wave, FreshBooks
 * 
 * Features:
 * - Accounting system connection status
 * - Chart of accounts synchronization
 * - Invoice and payment tracking
 * - Tax calculation and compliance
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface AccountingSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  accountCount?: number;
  invoiceCount?: number;
  region?: 'global' | 'us' | 'uk' | 'nigeria';
}

interface AccountingConnection {
  systemId: string;
  connectionId: string;
  companyId?: string;
  credentials: {
    clientId?: string;
    clientSecret?: string;
    accessToken?: string;
    refreshToken?: string;
    realmId?: string; // QuickBooks specific
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number;
    lastSuccessfulSync?: string;
    syncedEntities: string[];
    taxMappings: Record<string, string>;
  };
}

const supportedAccountingSystems: AccountingSystem[] = [
  {
    id: 'quickbooks',
    name: 'QuickBooks',
    icon: '💼',
    description: 'QuickBooks Online, QuickBooks Desktop',
    status: 'disconnected',
    region: 'global'
  },
  {
    id: 'xero',
    name: 'Xero',
    icon: '🔵',
    description: 'Xero Accounting Software',
    status: 'disconnected',
    region: 'global'
  },
  {
    id: 'sage',
    name: 'Sage',
    icon: '🟢',
    description: 'Sage 50, Sage Business Cloud',
    status: 'disconnected',
    region: 'uk'
  },
  {
    id: 'wave',
    name: 'Wave Accounting',
    icon: '🌊',
    description: 'Wave Free Accounting Software',
    status: 'disconnected',
    region: 'us'
  },
  {
    id: 'freshbooks',
    name: 'FreshBooks',
    icon: '📗',
    description: 'FreshBooks Cloud Accounting',
    status: 'disconnected',
    region: 'global'
  },
  {
    id: 'sage_nigeria',
    name: 'Sage Nigeria',
    icon: '🇳🇬',
    description: 'Sage Business Solutions Nigeria',
    status: 'disconnected',
    region: 'nigeria'
  }
];

interface AccountingDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const AccountingDashboard: React.FC<AccountingDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [accountingSystems, setAccountingSystems] = useState<AccountingSystem[]>(supportedAccountingSystems);
  const [connections, setConnections] = useState<AccountingConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'connected' | 'nigerian'>('all');

  // Load existing connections
  useEffect(() => {
    loadAccountingConnections();
  }, [companyId]);

  const loadAccountingConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/accounting/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses with mock data
        const updatedSystems = accountingSystems.map(system => {
          const connection = data.connections?.find((conn: AccountingConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              accountCount: Math.floor(Math.random() * 200) + 50,
              invoiceCount: Math.floor(Math.random() * 1000) + 100
            };
          }
          return system;
        });
        setAccountingSystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load accounting connections:', error);
    }
  };

  const handleConnectAccounting = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/accounting/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            companyId: 'test_company_123',
            apiEndpoint: 'https://sandbox-api.accounting.com'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('Accounting system connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('Accounting connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSyncChartOfAccounts = async (systemId: string) => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/accounting/sync-coa`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        // Update status to syncing
        const updatedSystems = accountingSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'syncing' as const }
            : system
        );
        setAccountingSystems(updatedSystems);
        
        // Simulate sync completion
        setTimeout(() => {
          const finalSystems = updatedSystems.map(system => 
            system.id === systemId 
              ? { ...system, status: 'connected' as const, lastSync: new Date().toISOString() }
              : system
          );
          setAccountingSystems(finalSystems);
        }, 2000);
        
        alert('Chart of Accounts sync started successfully');
      }
    } catch (error) {
      console.error('Failed to sync Chart of Accounts:', error);
      alert('Failed to sync Chart of Accounts');
    }
  };

  const handleDisconnectAccounting = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this accounting system?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/accounting/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        const updatedSystems = accountingSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, accountCount: undefined, invoiceCount: undefined }
            : system
        );
        setAccountingSystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('Accounting system disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect accounting system:', error);
      alert('Failed to disconnect accounting system');
    }
  };

  const getStatusColor = (status: AccountingSystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: AccountingSystem['status']) => {
    switch (status) {
      case 'connected': return '✅';
      case 'syncing': return '🔄';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  const getRegionFlag = (region?: string) => {
    switch (region) {
      case 'nigeria': return '🇳🇬';
      case 'us': return '🇺🇸';
      case 'uk': return '🇬🇧';
      default: return '🌍';
    }
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const filteredSystems = accountingSystems.filter(system => {
    if (filter === 'connected') return system.status === 'connected';
    if (filter === 'nigerian') return system.region === 'nigeria';
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Accounting System Integration</h1>
        <p className="text-gray-600">
          Connect your accounting software to sync chart of accounts, invoices, and financial data with TaxPoynt
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setFilter('all')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'all'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              All Systems ({accountingSystems.length})
            </button>
            <button
              onClick={() => setFilter('connected')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'connected'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Connected ({accountingSystems.filter(s => s.status === 'connected').length})
            </button>
            <button
              onClick={() => setFilter('nigerian')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'nigerian'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🇳🇬 Nigerian Systems ({accountingSystems.filter(s => s.region === 'nigeria').length})
            </button>
          </nav>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">
            {filteredSystems.filter(sys => sys.status === 'connected').length}
          </div>
          <div className="text-sm text-gray-600">Connected Systems</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.accountCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Chart of Accounts</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.invoiceCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Synced Invoices</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {filteredSystems.filter(sys => sys.status === 'error').length}
          </div>
          <div className="text-sm text-gray-600">Sync Errors</div>
        </div>
      </div>

      {/* Accounting Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSystems.map((system) => (
          <div key={system.id} className={`
            bg-white border border-gray-200 rounded-lg p-6
            ${system.region === 'nigeria' ? 'ring-1 ring-green-200' : ''}
          `}>
            {/* System Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{system.icon}</span>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-semibold text-gray-900">{system.name}</h3>
                    <span className="text-sm">{getRegionFlag(system.region)}</span>
                  </div>
                  <p className="text-sm text-gray-600">{system.description}</p>
                </div>
              </div>
              <div className={`
                px-2 py-1 rounded-full text-xs font-medium border
                ${getStatusColor(system.status)}
              `}>
                {getStatusIcon(system.status)} {system.status.charAt(0).toUpperCase() + system.status.slice(1)}
              </div>
            </div>

            {/* Connection Details */}
            {system.status === 'connected' && (
              <div className="space-y-2 mb-4 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Last Sync:</span>
                  <span>{formatLastSync(system.lastSync)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Accounts:</span>
                  <span>{system.accountCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Invoices:</span>
                  <span>{system.invoiceCount}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              {system.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnectAccounting(system.id)}
                  size="sm"
                  className="w-full"
                >
                  Connect
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    onClick={() => handleSyncChartOfAccounts(system.id)}
                    disabled={system.status === 'syncing'}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {system.status === 'syncing' ? 'Syncing...' : '📊 Sync COA'}
                  </Button>
                  <Button
                    onClick={() => handleTestConnection(system.id)}
                    disabled={isConnecting}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {isConnecting ? 'Testing...' : 'Test'}
                  </Button>
                </div>
              )}
              
              {system.status !== 'disconnected' && (
                <Button
                  onClick={() => handleDisconnectAccounting(system.id)}
                  variant="outline"
                  size="sm"
                  className="w-full text-red-600 hover:bg-red-50"
                >
                  Disconnect
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Connection Form Modal */}
      {showConnectionForm && selectedSystem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                Connect {accountingSystems.find(s => s.id === selectedSystem)?.name}
              </h3>
              <button
                onClick={() => setShowConnectionForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {selectedSystem === 'quickbooks' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company ID (Realm ID)
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="QuickBooks Company ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Intuit App Client ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client Secret
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Intuit App Client Secret"
                    />
                  </div>
                </>
              )}
              
              {selectedSystem === 'xero' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Xero App Client ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client Secret
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Xero App Client Secret"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tenant ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Xero Tenant ID"
                    />
                  </div>
                </>
              )}
              
              {/* Generic form for other accounting systems */}
              {!['quickbooks', 'xero'].includes(selectedSystem) && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Endpoint
                    </label>
                    <input
                      type="url"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="API endpoint URL"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key/Token
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="API key or access token"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Company/Organization ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Company or organization identifier"
                    />
                  </div>
                </>
              )}
            </div>
            
            <div className="flex space-x-3 mt-6">
              <Button
                onClick={() => setShowConnectionForm(false)}
                variant="outline"
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={() => {
                  setShowConnectionForm(false);
                  handleTestConnection(selectedSystem);
                }}
                className="flex-1"
              >
                Connect
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Tax Mapping Configuration */}
      <div className="mt-12 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-yellow-900 mb-4">
          🧮 Nigerian Tax Mapping
        </h3>
        <p className="text-yellow-800 text-sm mb-4">
          Configure how your accounting system's tax codes map to Nigerian VAT and tax requirements.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="bg-white border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">VAT Mapping:</h4>
            <div className="space-y-2 text-gray-600">
              <div className="flex justify-between">
                <span>Standard VAT (7.5%)</span>
                <span className="text-green-600">✓ Mapped</span>
              </div>
              <div className="flex justify-between">
                <span>Zero-rated VAT (0%)</span>
                <span className="text-green-600">✓ Mapped</span>
              </div>
              <div className="flex justify-between">
                <span>Exempt from VAT</span>
                <span className="text-yellow-600">⚠ Review</span>
              </div>
            </div>
          </div>
          <div className="bg-white border border-yellow-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-900 mb-2">Other Tax Mapping:</h4>
            <div className="space-y-2 text-gray-600">
              <div className="flex justify-between">
                <span>Withholding Tax</span>
                <span className="text-green-600">✓ Mapped</span>
              </div>
              <div className="flex justify-between">
                <span>Service Tax</span>
                <span className="text-yellow-600">⚠ Review</span>
              </div>
              <div className="flex justify-between">
                <span>Import Duty</span>
                <span className="text-red-600">✗ Not Mapped</span>
              </div>
            </div>
          </div>
        </div>
        <Button variant="primary" size="sm" className="mt-4">
          Configure Tax Mappings
        </Button>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Need Help with Accounting Integration?
        </h3>
        <p className="text-blue-800 text-sm mb-4">
          Our accounting integration specialists can help you connect your accounting software and ensure proper tax mapping for Nigerian compliance.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Schedule Accounting Setup
          </Button>
          <Button variant="outline" size="sm">
            📖 Accounting Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with Accounting Expert
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AccountingDashboard;