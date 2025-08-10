/**
 * E-commerce Dashboard Component
 * =============================
 * 
 * System Integrator interface for managing e-commerce platform connections.
 * Supports major platforms: Shopify, WooCommerce, Magento, BigCommerce, Jumia
 * 
 * Features:
 * - E-commerce platform connection status
 * - Order synchronization and processing
 * - Product catalog management
 * - Nigerian marketplace integrations
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface EcommerceSystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  orderCount?: number;
  productCount?: number;
  revenue?: number;
  isNigerian?: boolean;
}

interface EcommerceConnection {
  systemId: string;
  connectionId: string;
  storeUrl?: string;
  credentials: {
    apiKey?: string;
    apiSecret?: string;
    accessToken?: string;
    storeId?: string;
    webhookUrl?: string;
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number;
    lastSuccessfulSync?: string;
    syncedEntities: string[];
    orderStatuses: string[];
  };
}

const supportedEcommerceSystems: EcommerceSystem[] = [
  {
    id: 'shopify',
    name: 'Shopify',
    icon: '🛍️',
    description: 'Shopify Online Store',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'woocommerce',
    name: 'WooCommerce',
    icon: '🔵',
    description: 'WordPress WooCommerce',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'magento',
    name: 'Magento',
    icon: '🟠',
    description: 'Magento Commerce',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'bigcommerce',
    name: 'BigCommerce',
    icon: '🔷',
    description: 'BigCommerce Platform',
    status: 'disconnected',
    isNigerian: false
  },
  {
    id: 'jumia',
    name: 'Jumia',
    icon: '🇳🇬',
    description: 'Jumia Nigeria Marketplace',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'konga',
    name: 'Konga',
    icon: '🟣',
    description: 'Konga Nigeria E-commerce',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'jiji',
    name: 'Jiji',
    icon: '🟡',
    description: 'Jiji Nigeria Marketplace',
    status: 'disconnected',
    isNigerian: true
  },
  {
    id: 'payporte',
    name: 'PayPorte',
    icon: '💜',
    description: 'PayPorte Nigeria',
    status: 'disconnected',
    isNigerian: true
  }
];

interface EcommerceDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const EcommerceDashboard: React.FC<EcommerceDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [ecommerceSystems, setEcommerceSystems] = useState<EcommerceSystem[]>(supportedEcommerceSystems);
  const [connections, setConnections] = useState<EcommerceConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'nigerian' | 'international'>('all');

  // Load existing connections
  useEffect(() => {
    loadEcommerceConnections();
  }, [companyId]);

  const loadEcommerceConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/ecommerce/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses with mock data
        const updatedSystems = ecommerceSystems.map(system => {
          const connection = data.connections?.find((conn: EcommerceConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              orderCount: Math.floor(Math.random() * 500) + 50,
              productCount: Math.floor(Math.random() * 2000) + 100,
              revenue: Math.floor(Math.random() * 2000000) + 200000 // ₦200k - ₦2.2M
            };
          }
          return system;
        });
        setEcommerceSystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load e-commerce connections:', error);
    }
  };

  const handleConnectEcommerce = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/ecommerce/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            storeUrl: 'https://test-store.myshopify.com',
            apiKey: 'test_api_key'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('E-commerce connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('E-commerce connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSyncOrders = async (systemId: string) => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/ecommerce/sync-orders`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        // Update status to syncing
        const updatedSystems = ecommerceSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'syncing' as const }
            : system
        );
        setEcommerceSystems(updatedSystems);
        
        // Simulate sync completion
        setTimeout(() => {
          const finalSystems = updatedSystems.map(system => 
            system.id === systemId 
              ? { ...system, status: 'connected' as const, lastSync: new Date().toISOString() }
              : system
          );
          setEcommerceSystems(finalSystems);
        }, 3000);
        
        alert('Order sync started successfully');
      }
    } catch (error) {
      console.error('Failed to sync orders:', error);
      alert('Failed to sync orders');
    }
  };

  const handleDisconnectEcommerce = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this e-commerce platform?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/ecommerce/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        const updatedSystems = ecommerceSystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, orderCount: undefined, productCount: undefined, revenue: undefined }
            : system
        );
        setEcommerceSystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('E-commerce platform disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect e-commerce platform:', error);
      alert('Failed to disconnect e-commerce platform');
    }
  };

  const getStatusColor = (status: EcommerceSystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: EcommerceSystem['status']) => {
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

  const filteredSystems = ecommerceSystems.filter(system => {
    if (filter === 'nigerian') return system.isNigerian;
    if (filter === 'international') return !system.isNigerian;
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">E-commerce Platform Integration</h1>
        <p className="text-gray-600">
          Connect your online stores and marketplaces for automated order processing and invoice generation
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
              All Platforms ({ecommerceSystems.length})
            </button>
            <button
              onClick={() => setFilter('nigerian')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'nigerian'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🇳🇬 Nigerian Platforms ({ecommerceSystems.filter(s => s.isNigerian).length})
            </button>
            <button
              onClick={() => setFilter('international')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'international'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              🌍 International ({ecommerceSystems.filter(s => !s.isNigerian).length})
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
          <div className="text-sm text-gray-600">Connected Stores</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-600">
            {formatCurrency(filteredSystems.reduce((sum, sys) => sum + (sys.revenue || 0), 0))}
          </div>
          <div className="text-sm text-gray-600">Total Revenue</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.orderCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Orders</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.productCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Products</div>
        </div>
      </div>

      {/* E-commerce Systems Grid */}
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
                  <span>Revenue:</span>
                  <span className="font-medium text-green-600">{formatCurrency(system.revenue)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Orders:</span>
                  <span>{system.orderCount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Products:</span>
                  <span>{system.productCount?.toLocaleString()}</span>
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
                  onClick={() => handleConnectEcommerce(system.id)}
                  size="sm"
                  className="w-full"
                >
                  Connect Store
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    onClick={() => handleSyncOrders(system.id)}
                    disabled={system.status === 'syncing'}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {system.status === 'syncing' ? 'Syncing...' : '🛒 Sync Orders'}
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
                  onClick={() => handleDisconnectEcommerce(system.id)}
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
                Connect {ecommerceSystems.find(s => s.id === selectedSystem)?.name}
              </h3>
              <button
                onClick={() => setShowConnectionForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {/* Shopify specific fields */}
              {selectedSystem === 'shopify' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Store URL
                    </label>
                    <input
                      type="url"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="https://your-store.myshopify.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Key
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Shopify API Key"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Secret
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Shopify API Secret"
                    />
                  </div>
                </>
              )}

              {/* WooCommerce specific fields */}
              {selectedSystem === 'woocommerce' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Store URL
                    </label>
                    <input
                      type="url"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="https://your-store.com"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Consumer Key
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="WooCommerce Consumer Key"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Consumer Secret
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="WooCommerce Consumer Secret"
                    />
                  </div>
                </>
              )}

              {/* Nigerian marketplace specific fields */}
              {ecommerceSystems.find(s => s.id === selectedSystem)?.isNigerian && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Seller ID
                    </label>
                    <input
                      type="text"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="Your seller/merchant ID"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      API Token
                    </label>
                    <input
                      type="password"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="API access token"
                    />
                  </div>
                </>
              )}

              {/* Generic form for other platforms */}
              {!['shopify', 'woocommerce'].includes(selectedSystem || '') && 
               !ecommerceSystems.find(s => s.id === selectedSystem)?.isNigerian && (
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

      {/* E-commerce Features */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            🛒 Order Processing
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Automatically process orders and generate invoices for completed purchases
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span>Auto-process paid orders</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" defaultChecked />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Generate invoice on fulfillment</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" defaultChecked />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Include shipping in invoice</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📦 Product Sync
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Keep product information synchronized across platforms
          </p>
          <div className="space-y-2 text-sm">
            <div className="flex items-center justify-between">
              <span>Sync product prices</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" defaultChecked />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Sync inventory levels</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span>Sync product descriptions</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Nigerian E-commerce Benefits */}
      <div className="mt-6 bg-green-50 border border-green-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-green-900 mb-2">
          🇳🇬 Nigerian E-commerce Integration Benefits
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-green-800">
          <div>
            <h4 className="font-medium mb-2">Marketplace Advantages:</h4>
            <ul className="space-y-1">
              <li>• Direct integration with Jumia, Konga, Jiji</li>
              <li>• Automated FIRS compliance for online sales</li>
              <li>• Nigerian Naira currency handling</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Business Benefits:</h4>
            <ul className="space-y-1">
              <li>• Unified order management</li>
              <li>• Automated invoice generation</li>
              <li>• Real-time sales tracking</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-purple-50 border border-purple-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-purple-900 mb-2">
          Need Help with E-commerce Integration?
        </h3>
        <p className="text-purple-800 text-sm mb-4">
          Our e-commerce specialists can help you connect your online stores and marketplaces for seamless order processing and invoice automation.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Schedule E-commerce Setup
          </Button>
          <Button variant="outline" size="sm">
            📖 E-commerce Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with E-commerce Expert
          </Button>
        </div>
      </div>
    </div>
  );
};

export default EcommerceDashboard;