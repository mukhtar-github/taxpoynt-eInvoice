/**
 * ERP Dashboard Component
 * ======================
 * 
 * System Integrator interface for managing ERP system connections.
 * Supports major ERP systems: SAP, Oracle, Microsoft Dynamics, NetSuite, Odoo
 * 
 * Features:
 * - ERP system connection status
 * - Data synchronization monitoring
 * - Invoice generation from ERP data
 * - Real-time sync controls
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface ERPSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  recordCount?: number;
  apiEndpoint?: string;
  version?: string;
}

interface ERPConnection {
  systemId: string;
  connectionId: string;
  credentials: {
    server?: string;
    database?: string;
    username?: string;
    apiKey?: string;
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number; // in minutes
    lastSuccessfulSync?: string;
    syncedEntities: string[];
  };
}

const supportedERPSystems: ERPSystem[] = [
  {
    id: 'sap',
    name: 'SAP',
    icon: '🏢',
    description: 'SAP ERP, S/4HANA, Business One',
    status: 'disconnected'
  },
  {
    id: 'oracle',
    name: 'Oracle ERP Cloud',
    icon: '🔴',
    description: 'Oracle ERP Cloud, E-Business Suite',
    status: 'disconnected'
  },
  {
    id: 'dynamics',
    name: 'Microsoft Dynamics',
    icon: '🔷',
    description: 'Dynamics 365, NAV, GP',
    status: 'disconnected'
  },
  {
    id: 'netsuite',
    name: 'NetSuite',
    icon: '🌐',
    description: 'Oracle NetSuite ERP',
    status: 'disconnected'
  },
  {
    id: 'odoo',
    name: 'Odoo',
    icon: '🟣',
    description: 'Odoo Community & Enterprise',
    status: 'disconnected'
  }
];

interface ERPDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const ERPDashboard: React.FC<ERPDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [erpSystems, setErpSystems] = useState<ERPSystem[]>(supportedERPSystems);
  const [connections, setConnections] = useState<ERPConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);

  // Load existing connections
  useEffect(() => {
    loadERPConnections();
  }, [companyId]);

  const loadERPConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/erp/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses based on connections
        const updatedSystems = erpSystems.map(system => {
          const connection = data.connections?.find((conn: ERPConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              recordCount: Math.floor(Math.random() * 10000) // Mock data
            };
          }
          return system;
        });
        setErpSystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load ERP connections:', error);
    }
  };

  const handleConnectERP = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/erp/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            // Mock test parameters
            server: 'test.company.com',
            database: 'production'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('Connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnectERP = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this ERP system?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/erp/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        // Update local state
        const updatedSystems = erpSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, recordCount: undefined }
            : system
        );
        setErpSystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('ERP system disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect ERP system:', error);
      alert('Failed to disconnect ERP system');
    }
  };

  const getStatusColor = (status: ERPSystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: ERPSystem['status']) => {
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">ERP System Integration</h1>
        <p className="text-gray-600">
          Connect your ERP systems to automatically generate e-invoices from your business transactions
        </p>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-600">
            {erpSystems.filter(sys => sys.status === 'connected').length}
          </div>
          <div className="text-sm text-gray-600">Connected Systems</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {erpSystems.reduce((sum, sys) => sum + (sys.recordCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Records</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {erpSystems.filter(sys => sys.lastSync).length}
          </div>
          <div className="text-sm text-gray-600">Active Syncs</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {erpSystems.filter(sys => sys.status === 'error').length}
          </div>
          <div className="text-sm text-gray-600">Errors</div>
        </div>
      </div>

      {/* ERP Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {erpSystems.map((system) => (
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
                  <span>Records:</span>
                  <span>{system.recordCount?.toLocaleString()}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              {system.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnectERP(system.id)}
                  size="sm"
                  className="flex-1"
                >
                  Connect
                </Button>
              ) : (
                <>
                  <Button
                    onClick={() => handleTestConnection(system.id)}
                    disabled={isConnecting}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {isConnecting ? 'Testing...' : 'Test'}
                  </Button>
                  <Button
                    onClick={() => handleDisconnectERP(system.id)}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    Disconnect
                  </Button>
                </>
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
                Connect {erpSystems.find(s => s.id === selectedSystem)?.name}
              </h3>
              <button
                onClick={() => setShowConnectionForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Server/Host
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="server.company.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Database/Instance
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="production"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key/Username
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="API key or username"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Password/Secret
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Password or API secret"
                />
              </div>
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
                  // Mock connection success
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

      {/* Help Section */}
      <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Need Help with ERP Integration?
        </h3>
        <p className="text-blue-800 text-sm mb-4">
          Our Nigerian technical team can help you connect your ERP system and ensure smooth data synchronization.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Schedule Setup Call
          </Button>
          <Button variant="outline" size="sm">
            📖 View Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with Support
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ERPDashboard;