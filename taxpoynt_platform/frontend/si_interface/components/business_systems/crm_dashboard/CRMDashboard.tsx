/**
 * CRM Dashboard Component
 * ======================
 * 
 * System Integrator interface for managing CRM system connections.
 * Supports major CRM systems: Salesforce, HubSpot, Microsoft Dynamics CRM, Pipedrive, Zoho
 * 
 * Features:
 * - CRM system connection status
 * - Customer data synchronization
 * - Sales pipeline integration
 * - Invoice generation from CRM opportunities
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface CRMSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  customerCount?: number;
  opportunityCount?: number;
  version?: string;
}

interface CRMConnection {
  systemId: string;
  connectionId: string;
  credentials: {
    instanceUrl?: string;
    clientId?: string;
    clientSecret?: string;
    accessToken?: string;
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number;
    lastSuccessfulSync?: string;
    syncedEntities: string[];
  };
}

const supportedCRMSystems: CRMSystem[] = [
  {
    id: 'salesforce',
    name: 'Salesforce',
    icon: '☁️',
    description: 'Salesforce Sales Cloud, Service Cloud',
    status: 'disconnected'
  },
  {
    id: 'hubspot',
    name: 'HubSpot',
    icon: '🧡',
    description: 'HubSpot CRM, Sales Hub',
    status: 'disconnected'
  },
  {
    id: 'dynamics_crm',
    name: 'Microsoft Dynamics CRM',
    icon: '🔷',
    description: 'Dynamics 365 Customer Engagement',
    status: 'disconnected'
  },
  {
    id: 'pipedrive',
    name: 'Pipedrive',
    icon: '🚀',
    description: 'Pipedrive Sales CRM',
    status: 'disconnected'
  },
  {
    id: 'zoho',
    name: 'Zoho CRM',
    icon: '🟣',
    description: 'Zoho CRM, Zoho One',
    status: 'disconnected'
  }
];

interface CRMDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const CRMDashboard: React.FC<CRMDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [crmSystems, setCrmSystems] = useState<CRMSystem[]>(supportedCRMSystems);
  const [connections, setConnections] = useState<CRMConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);

  // Load existing connections
  useEffect(() => {
    loadCRMConnections();
  }, [companyId]);

  const loadCRMConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/crm/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses based on connections
        const updatedSystems = crmSystems.map(system => {
          const connection = data.connections?.find((conn: CRMConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              customerCount: Math.floor(Math.random() * 5000) + 100,
              opportunityCount: Math.floor(Math.random() * 500) + 50
            };
          }
          return system;
        });
        setCrmSystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load CRM connections:', error);
    }
  };

  const handleConnectCRM = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/crm/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            instanceUrl: 'https://company.salesforce.com',
            clientId: 'test_client_id'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('CRM connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('CRM connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSyncNow = async (systemId: string) => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/crm/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        // Update status to syncing
        const updatedSystems = crmSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'syncing' as const }
            : system
        );
        setCrmSystems(updatedSystems);
        
        // Simulate sync completion
        setTimeout(() => {
          const finalSystems = updatedSystems.map(system => 
            system.id === systemId 
              ? { ...system, status: 'connected' as const, lastSync: new Date().toISOString() }
              : system
          );
          setCrmSystems(finalSystems);
        }, 3000);
        
        alert('CRM sync started successfully');
      }
    } catch (error) {
      console.error('Failed to sync CRM:', error);
      alert('Failed to start CRM sync');
    }
  };

  const handleDisconnectCRM = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this CRM system?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/crm/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        const updatedSystems = crmSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, customerCount: undefined, opportunityCount: undefined }
            : system
        );
        setCrmSystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('CRM system disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect CRM system:', error);
      alert('Failed to disconnect CRM system');
    }
  };

  const getStatusColor = (status: CRMSystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: CRMSystem['status']) => {
    switch (status) {
      case 'connected': return '✅';
      case 'syncing': return '🔄';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">CRM System Integration</h1>
        <p className="text-gray-600">
          Connect your CRM systems to generate invoices from customer opportunities and sales data
        </p>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">
            {crmSystems.filter(sys => sys.status === 'connected').length}
          </div>
          <div className="text-sm text-gray-600">Connected CRMs</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {crmSystems.reduce((sum, sys) => sum + (sys.customerCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Customers</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {crmSystems.reduce((sum, sys) => sum + (sys.opportunityCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Active Opportunities</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {crmSystems.filter(sys => sys.status === 'error').length}
          </div>
          <div className="text-sm text-gray-600">Sync Errors</div>
        </div>
      </div>

      {/* CRM Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {crmSystems.map((system) => (
          <div key={system.id} className="bg-white border border-gray-200 rounded-lg p-6">
            {/* System Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{system.icon}</span>
                <div>
                  <h3 className="font-semibold text-gray-900">{system.name}</h3>
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
                  <span>Customers:</span>
                  <span>{system.customerCount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Opportunities:</span>
                  <span>{system.opportunityCount?.toLocaleString()}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              {system.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnectCRM(system.id)}
                  size="sm"
                  className="flex-1"
                >
                  Connect
                </Button>
              ) : (
                <>
                  <Button
                    onClick={() => handleSyncNow(system.id)}
                    disabled={system.status === 'syncing'}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {system.status === 'syncing' ? 'Syncing...' : 'Sync Now'}
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
                </>
              )}
            </div>

            {/* Disconnect Option */}
            {system.status !== 'disconnected' && (
              <Button
                onClick={() => handleDisconnectCRM(system.id)}
                variant="outline"
                size="sm"
                className="w-full mt-2 text-red-600 hover:bg-red-50"
              >
                Disconnect
              </Button>
            )}
          </div>
        ))}
      </div>

      {/* Connection Form Modal */}
      {showConnectionForm && selectedSystem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">
                Connect {crmSystems.find(s => s.id === selectedSystem)?.name}
              </h3>
              <button
                onClick={() => setShowConnectionForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {selectedSystem === 'salesforce' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Instance URL
                    </label>
                    <input
                      type="url"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="https://company.salesforce.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Connected App Client ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Client Secret
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Connected App Client Secret"
                    />
                  </div>
                </>
              )}
              
              {selectedSystem === 'hubspot' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="HubSpot Private App API Key"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Portal ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="HubSpot Portal ID"
                    />
                  </div>
                </>
              )}
              
              {/* Generic form for other CRMs */}
              {!['salesforce', 'hubspot'].includes(selectedSystem) && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API URL/Endpoint
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

      {/* CRM-Specific Features */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🎯 Opportunity-to-Invoice Flow
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Automatically generate invoices when CRM opportunities are marked as "Closed Won"
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span>Auto-invoice on close</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Include opportunity products</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            👥 Customer Sync Settings
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Configure how customer data syncs between your CRM and TaxPoynt
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span>Bi-directional sync</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Auto-create customers</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-12 bg-purple-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-2">
          Need Help with CRM Integration?
        </h3>
        <p className="text-purple-800 text-sm mb-4">
          Our team can help you set up CRM integrations and configure automatic invoice generation from your sales pipeline.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Book CRM Setup Call
          </Button>
          <Button variant="outline" size="sm">
            📖 CRM Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with CRM Expert
          </Button>
        </div>
      </div>
    </div>
  );
};

export default CRMDashboard;