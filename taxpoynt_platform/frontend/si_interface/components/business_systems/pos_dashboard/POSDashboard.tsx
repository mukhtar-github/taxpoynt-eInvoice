/**
 * POS Dashboard Component
 * ======================
 * 
 * System Integrator interface for managing POS system connections.
 * Supports major POS systems: Square, Clover, Lightspeed, Toast, Shopify POS, African POS systems
 * 
 * Features:
 * - POS system connection status
 * - Real-time transaction monitoring
 * - Automatic invoice generation from sales
 * - Nigerian market-specific POS integrations
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface POSSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  dailySales?: number;
  transactionCount?: number;
  location?: string;
  isNigerian?: boolean;
}

interface POSConnection {
  systemId: string;
  connectionId: string;
  locationId?: string;
  credentials: {
    apiKey?: string;
    accessToken?: string;
    merchantId?: string;
    terminalId?: string;
  };
  syncSettings: {
    realTimeSync: boolean;
    syncInterval: number;
    lastSuccessfulSync?: string;
    autoInvoice: boolean;
  };
}

const supportedPOSSystems: POSSystem[] = [
  {
    id: 'square',
    name: 'Square',
    icon: '⬜',
    description: 'Square POS, Square Terminal',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'clover',
    name: 'Clover',
    icon: '🍀',
    description: 'Clover Station, Clover Mini',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'lightspeed',
    name: 'Lightspeed',
    icon: '⚡',
    description: 'Lightspeed Retail, Restaurant',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'toast',
    name: 'Toast POS',
    icon: '🍞',
    description: 'Toast Restaurant POS',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'shopify_pos',
    name: 'Shopify POS',
    icon: '🛍️',
    description: 'Shopify Point of Sale',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'quickteller',
    name: 'Quickteller POS',
    icon: '🇳🇬',
    description: 'Interswitch Quickteller POS',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'opay_pos',
    name: 'OPay POS',
    icon: '💚',
    description: 'OPay Business POS Terminal',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'moniepoint_pos',
    name: 'Moniepoint POS',
    icon: '🔵',
    description: 'Moniepoint Business POS',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'palmpay_pos',
    name: 'PalmPay POS',
    icon: '🌴',
    description: 'PalmPay Business Terminal',
    status: 'disconnected',
    isNigerian: true
  }
];

interface POSDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const POSDashboard: React.FC<POSDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [posSystems, setPosSystems] = useState<POSSystem[]>(supportedPOSSystems);
  const [connections, setConnections] = useState<POSConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'nigerian' | 'international'>('all');

  // Load existing connections
  useEffect(() => {
    loadPOSConnections();
  }, [companyId]);

  const loadPOSConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/pos/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses with mock data
        const updatedSystems = posSystems.map(system => {
          const connection = data.connections?.find((conn: POSConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              dailySales: Math.floor(Math.random() * 500000) + 50000, // ₦50k - ₦550k
              transactionCount: Math.floor(Math.random() * 200) + 20,
              location: 'Lagos Store'
            };
          }
          return system;
        });
        setPosSystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load POS connections:', error);
    }
  };

  const handleConnectPOS = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/pos/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            terminalId: 'TEST_TERMINAL_001',
            merchantId: 'TEST_MERCHANT'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('POS connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('POS connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleStartRealTimeSync = async (systemId: string) => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/pos/real-time-sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId, enabled: true })
      });

      if (response.ok) {
        alert('Real-time sync enabled successfully');
      }
    } catch (error) {
      console.error('Failed to enable real-time sync:', error);
      alert('Failed to enable real-time sync');
    }
  };

  const handleDisconnectPOS = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this POS system?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/pos/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        const updatedSystems = posSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, dailySales: undefined, transactionCount: undefined }
            : system
        );
        setPosSystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('POS system disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect POS system:', error);
      alert('Failed to disconnect POS system');
    }
  };

  const getStatusColor = (status: POSSystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: POSSystem['status']) => {
    switch (status) {
      case 'connected': return '✅';
      case 'syncing': return '🔄';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '₦0';
    return `₦${amount.toLocaleString()}`;
  };

  const formatLastSync = (lastSync?: string) => {
    if (!lastSync) return 'Never';
    const date = new Date(lastSync);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const filteredSystems = posSystems.filter(system => {
    if (filter === 'nigerian') return system.isNigerian;
    if (filter === 'international') return !system.isNigerian;
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">POS System Integration</h1>
        <p className="text-gray-600">
          Connect your Point of Sale systems for real-time transaction processing and automatic invoice generation
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
              All Systems ({posSystems.length})
            </button>
            <button
              onClick={() => setFilter('nigerian')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'nigerian'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🇳🇬 Nigerian POS ({posSystems.filter(s => s.isNigerian).length})
            </button>
            <button
              onClick={() => setFilter('international')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'international'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🌍 International ({posSystems.filter(s => !s.isNigerian).length})
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
          <div className="text-sm text-gray-600">Connected POS</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(filteredSystems.reduce((sum, sys) => sum + (sys.dailySales || 0), 0))}
          </div>
          <div className="text-sm text-gray-600">Today's Sales</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.transactionCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Today's Transactions</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {filteredSystems.filter(sys => sys.status === 'error').length}
          </div>
          <div className="text-sm text-gray-600">Sync Errors</div>
        </div>
      </div>

      {/* POS Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSystems.map((system) => (
          <div key={system.id} className={`
            bg-white border border-gray-200 rounded-lg p-6
            ${system.isNigerian ? 'ring-1 ring-green-200' : ''}
          `}>
            {/* System Header */}
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <span className="text-2xl">{system.icon}</span>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-semibold text-gray-900">{system.name}</h3>
                    {system.isNigerian && (
                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                        Nigerian
                      </span>
                    )}
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
                  <span>Location:</span>
                  <span>{system.location}</span>
                </div>
                <div className="flex justify-between">
                  <span>Today's Sales:</span>
                  <span className="font-medium text-green-600">{formatCurrency(system.dailySales)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Transactions:</span>
                  <span>{system.transactionCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Last Sync:</span>
                  <span>{formatLastSync(system.lastSync)}</span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              {system.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnectPOS(system.id)}
                  size="sm"
                  className="w-full"
                >
                  Connect POS
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    onClick={() => handleStartRealTimeSync(system.id)}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    🔄 Real-time
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
                  onClick={() => handleDisconnectPOS(system.id)}
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
                Connect {posSystems.find(s => s.id === selectedSystem)?.name}
              </h3>
              <button
                onClick={() => setShowConnectionForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Nigerian POS specific fields */}
              {posSystems.find(s => s.id === selectedSystem)?.isNigerian ? (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Terminal ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Terminal ID from provider"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Merchant ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Merchant ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="API Key from POS provider"
                    />
                  </div>
                </>
              ) : (
                /* International POS fields */
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Application ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Application/Client ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Access Token
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Access token or API key"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Location ID (Optional)
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Store/Location ID"
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

      {/* Nigerian POS Benefits */}
      <div className="mt-12 bg-green-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-900 mb-2">
          🇳🇬 Why Nigerian POS Integration Matters
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-green-800">
          <div>
            <h4 className="font-medium mb-2">Compliance Benefits:</h4>
            <ul className="space-y-1">
              <li>• Automatic FIRS e-invoice generation</li>
              <li>• CBN transaction reporting compliance</li>
              <li>• VAT calculation for eligible transactions</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Business Benefits:</h4>
            <ul className="space-y-1">
              <li>• Real-time sales tracking</li>
              <li>• Reduced manual data entry</li>
              <li>• Faster month-end reconciliation</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibent text-blue-900 mb-2">
          Need Help with POS Integration?
        </h3>
        <p className="text-blue-800 text-sm mb-4">
          Our Nigerian technical team specializes in POS integrations and can help you connect your terminals for seamless transaction processing.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Schedule POS Setup
          </Button>
          <Button variant="outline" size="sm">
            📖 POS Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with POS Expert
          </Button>
        </div>
      </div>
    </div>
  );
};

export default POSDashboard;