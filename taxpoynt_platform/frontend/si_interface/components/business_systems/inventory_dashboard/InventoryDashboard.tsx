/**
 * Inventory Dashboard Component
 * ============================
 * 
 * System Integrator interface for managing inventory management system connections.
 * Supports major systems: TradeGecko, Fishbowl, Cin7, Unleashed, Zoho Inventory
 * 
 * Features:
 * - Inventory system connection status
 * - Stock level synchronization
 * - Warehouse management integration
 * - Cost tracking and valuation
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface InventorySystem {
  id: string;
  name: string;
  icon: string;
  description: string;
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  productCount?: number;
  warehouseCount?: number;
  totalValue?: number;
  lowStockItems?: number;
}

interface InventoryConnection {
  systemId: string;
  connectionId: string;
  warehouseIds?: string[];
  credentials: {
    apiKey?: string;
    apiSecret?: string;
    accessToken?: string;
    companyId?: string;
    baseUrl?: string;
  };
  syncSettings: {
    autoSync: boolean;
    syncInterval: number;
    lastSuccessfulSync?: string;
    syncedEntities: string[];
    stockThresholds: {
      lowStock: number;
      outOfStock: number;
    };
  };
}

const supportedInventorySystems: InventorySystem[] = [
  {
    id: 'tradegecko',
    name: 'TradeGecko',
    icon: '🦎',
    description: 'TradeGecko Inventory Management',
    status: 'disconnected'
  },
  {
    id: 'fishbowl',
    name: 'Fishbowl',
    icon: '🐠',
    description: 'Fishbowl Manufacturing & Warehouse',
    status: 'disconnected'
  },
  {
    id: 'cin7',
    name: 'Cin7',
    icon: '7️⃣',
    description: 'Cin7 Inventory Management',
    status: 'disconnected'
  },
  {
    id: 'unleashed',
    name: 'Unleashed',
    icon: '🚀',
    description: 'Unleashed Inventory Management',
    status: 'disconnected'
  },
  {
    id: 'zoho_inventory',
    name: 'Zoho Inventory',
    icon: '📦',
    description: 'Zoho Inventory Management',
    status: 'disconnected'
  },
  {
    id: 'orderhive',
    name: 'OrderHive',
    icon: '🐝',
    description: 'OrderHive Inventory & Order Management',
    status: 'disconnected'
  },
  {
    id: 'stockly',
    name: 'Stockly',
    icon: '📊',
    description: 'Stockly Inventory Optimization',
    status: 'disconnected'
  },
  {
    id: 'dear_inventory',
    name: 'DEAR Inventory',
    icon: '💎',
    description: 'DEAR Inventory Management',
    status: 'disconnected'
  }
];

interface InventoryDashboardProps {
  companyId?: string;
  onConnectionSuccess?: (systemId: string) => void;
}

export const InventoryDashboard: React.FC<InventoryDashboardProps> = ({
  companyId,
  onConnectionSuccess
}) => {
  const [inventorySystems, setInventorySystems] = useState<InventorySystem[]>(supportedInventorySystems);
  const [connections, setConnections] = useState<InventoryConnection[]>([]);
  const [selectedSystem, setSelectedSystem] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [showConnectionForm, setShowConnectionForm] = useState(false);
  const [filter, setFilter] = useState<'all' | 'connected' | 'warning'>('all');

  // Load existing connections
  useEffect(() => {
    loadInventoryConnections();
  }, [companyId]);

  const loadInventoryConnections = async () => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/inventory/connections`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setConnections(data.connections || []);
        
        // Update system statuses with mock data
        const updatedSystems = inventorySystems.map(system => {
          const connection = data.connections?.find((conn: InventoryConnection) => conn.systemId === system.id);
          if (connection) {
            return {
              ...system,
              status: 'connected' as const,
              lastSync: connection.syncSettings.lastSuccessfulSync,
              productCount: Math.floor(Math.random() * 5000) + 500,
              warehouseCount: Math.floor(Math.random() * 5) + 1,
              totalValue: Math.floor(Math.random() * 50000000) + 5000000, // ₦5M - ₦55M
              lowStockItems: Math.floor(Math.random() * 50) + 5
            };
          }
          return system;
        });
        setInventorySystems(updatedSystems);
      }
    } catch (error) {
      console.error('Failed to load inventory connections:', error);
    }
  };

  const handleConnectInventory = (systemId: string) => {
    setSelectedSystem(systemId);
    setShowConnectionForm(true);
  };

  const handleTestConnection = async (systemId: string) => {
    setIsConnecting(true);
    
    try {
      const response = await fetch(`/api/v1/si/business-systems/inventory/test-connection`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          systemId,
          testData: {
            apiKey: 'test_api_key',
            baseUrl: 'https://api.inventory-system.com'
          }
        })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('Inventory system connection test successful!');
          if (onConnectionSuccess) {
            onConnectionSuccess(systemId);
          }
        } else {
          alert('Connection test failed: ' + data.message);
        }
      }
    } catch (error) {
      console.error('Inventory connection test failed:', error);
      alert('Connection test failed. Please check your settings.');
    } finally {
      setIsConnecting(false);
    }
  };

  const handleSyncInventory = async (systemId: string) => {
    try {
      const response = await fetch(`/api/v1/si/business-systems/inventory/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        // Update status to syncing
        const updatedSystems = inventorySystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'syncing' as const }
            : system
        );
        setInventorySystems(updatedSystems);
        
        // Simulate sync completion
        setTimeout(() => {
          const finalSystems = updatedSystems.map(system => 
            system.id === systemId 
              ? { ...system, status: 'connected' as const, lastSync: new Date().toISOString() }
              : system
          );
          setInventorySystems(finalSystems);
        }, 4000);
        
        alert('Inventory sync started successfully');
      }
    } catch (error) {
      console.error('Failed to sync inventory:', error);
      alert('Failed to sync inventory');
    }
  };

  const handleDisconnectInventory = async (systemId: string) => {
    if (!confirm('Are you sure you want to disconnect this inventory system?')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/si/business-systems/inventory/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ systemId })
      });

      if (response.ok) {
        const updatedSystems = inventorySystems.map(system => 
          system.id === systemId 
            ? { ...system, status: 'disconnected' as const, lastSync: undefined, productCount: undefined, warehouseCount: undefined, totalValue: undefined, lowStockItems: undefined }
            : system
        );
        setInventorySystems(updatedSystems);
        
        setConnections(connections.filter(conn => conn.systemId !== systemId));
        
        alert('Inventory system disconnected successfully');
      }
    } catch (error) {
      console.error('Failed to disconnect inventory system:', error);
      alert('Failed to disconnect inventory system');
    }
  };

  const getStatusColor = (status: InventorySystem['status']) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'syncing': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status: InventorySystem['status']) => {
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

  const filteredSystems = inventorySystems.filter(system => {
    if (filter === 'connected') return system.status === 'connected';
    if (filter === 'warning') return (system.lowStockItems || 0) > 0;
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Inventory Management Integration</h1>
        <p className="text-gray-600">
          Connect your inventory management systems for real-time stock tracking, cost management, and automated reordering
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
              All Systems ({inventorySystems.length})
            </button>
            <button
              onClick={() => setFilter('connected')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'connected'
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Connected ({inventorySystems.filter(s => s.status === 'connected').length})
            </button>
            <button
              onClick={() => setFilter('warning')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                filter === 'warning'
                  ? 'border-orange-500 text-orange-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              ⚠️ Low Stock Alerts ({inventorySystems.filter(s => (s.lowStockItems || 0) > 0).length})
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
            {formatCurrency(filteredSystems.reduce((sum, sys) => sum + (sys.totalValue || 0), 0))}
          </div>
          <div className="text-sm text-gray-600">Total Inventory Value</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-purple-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.productCount || 0), 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-600">Total Products</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-2xl font-bold text-orange-600">
            {filteredSystems.reduce((sum, sys) => sum + (sys.lowStockItems || 0), 0)}
          </div>
          <div className="text-sm text-gray-600">Low Stock Items</div>
        </div>
      </div>

      {/* Inventory Systems Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSystems.map((system) => (
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
                  <span>Total Value:</span>
                  <span className="font-medium text-green-600">{formatCurrency(system.totalValue)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Products:</span>
                  <span>{system.productCount?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Warehouses:</span>
                  <span>{system.warehouseCount}</span>
                </div>
                <div className="flex justify-between">
                  <span>Low Stock:</span>
                  <span className={`${(system.lowStockItems || 0) > 0 ? 'text-orange-600 font-medium' : ''}`}>
                    {system.lowStockItems || 0} items
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Last Sync:</span>
                  <span>{formatLastSync(system.lastSync)}</span>
                </div>
              </div>
            )}

            {/* Low Stock Warning */}
            {system.status === 'connected' && (system.lowStockItems || 0) > 0 && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3 mb-4">
                <div className="flex items-center space-x-2 text-orange-700">
                  <span className="text-sm">⚠️</span>
                  <span className="text-sm font-medium">
                    {system.lowStockItems} items below threshold
                  </span>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="space-y-2">
              {system.status === 'disconnected' ? (
                <Button
                  onClick={() => handleConnectInventory(system.id)}
                  size="sm"
                  className="w-full"
                >
                  Connect System
                </Button>
              ) : (
                <div className="flex space-x-2">
                  <Button
                    onClick={() => handleSyncInventory(system.id)}
                    disabled={system.status === 'syncing'}
                    variant="outline"
                    size="sm"
                    className="flex-1"
                  >
                    {system.status === 'syncing' ? 'Syncing...' : '📦 Sync Stock'}
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
                  onClick={() => handleDisconnectInventory(system.id)}
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
                Connect {inventorySystems.find(s => s.id === selectedSystem)?.name}
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
                  API Endpoint/Base URL
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://api.inventory-system.com"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="API Key or Access Token"
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

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Warehouse IDs (Optional)
                </label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Comma-separated warehouse IDs"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Leave empty to sync all warehouses
                </p>
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

      {/* Inventory Management Features */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📊 Stock Monitoring
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Set up automated alerts and thresholds for inventory management
          </p>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Low Stock Threshold
              </label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                placeholder="10"
                defaultValue="10"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Out of Stock Threshold
              </label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                placeholder="0"
                defaultValue="0"
              />
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Email alerts for low stock</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" defaultChecked />
              </label>
            </div>
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            💰 Cost Tracking
          </h3>
          <p className="text-gray-600 text-sm mb-4">
            Track inventory costs and valuation methods for accurate financial reporting
          </p>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Valuation Method
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm">
                <option value="fifo">FIFO (First In, First Out)</option>
                <option value="lifo">LIFO (Last In, First Out)</option>
                <option value="weighted_average">Weighted Average</option>
                <option value="specific_identification">Specific Identification</option>
              </select>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Include shipping costs</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm">Track landed costs</span>
              <label className="inline-flex items-center">
                <input type="checkbox" className="form-checkbox" />
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Inventory Insights */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-4">
          📈 Inventory Insights
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
          <div className="bg-white border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Top Moving Items:</h4>
            <div className="space-y-1 text-blue-700">
              <div className="flex justify-between">
                <span>Product A</span>
                <span className="font-medium">150 units/month</span>
              </div>
              <div className="flex justify-between">
                <span>Product B</span>
                <span className="font-medium">120 units/month</span>
              </div>
              <div className="flex justify-between">
                <span>Product C</span>
                <span className="font-medium">95 units/month</span>
              </div>
            </div>
          </div>
          <div className="bg-white border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Slow Moving Items:</h4>
            <div className="space-y-1 text-blue-700">
              <div className="flex justify-between">
                <span>Product X</span>
                <span className="font-medium">2 units/month</span>
              </div>
              <div className="flex justify-between">
                <span>Product Y</span>
                <span className="font-medium">1 unit/month</span>
              </div>
              <div className="flex justify-between">
                <span>Product Z</span>
                <span className="font-medium">0 units/month</span>
              </div>
            </div>
          </div>
          <div className="bg-white border border-blue-200 rounded-lg p-4">
            <h4 className="font-medium text-blue-900 mb-2">Reorder Recommendations:</h4>
            <div className="space-y-1 text-blue-700">
              <div className="flex justify-between">
                <span>Product A</span>
                <span className="font-medium text-orange-600">Order Now</span>
              </div>
              <div className="flex justify-between">
                <span>Product D</span>
                <span className="font-medium text-yellow-600">Order Soon</span>
              </div>
              <div className="flex justify-between">
                <span>Product E</span>
                <span className="font-medium text-green-600">Stock OK</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Help Section */}
      <div className="mt-6 bg-orange-50 border border-orange-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-orange-900 mb-2">
          Need Help with Inventory Integration?
        </h3>
        <p className="text-orange-800 text-sm mb-4">
          Our inventory management specialists can help you connect your systems, set up optimal stock thresholds, and implement cost tracking strategies.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="primary" size="sm">
            📞 Schedule Inventory Setup
          </Button>
          <Button variant="outline" size="sm">
            📖 Inventory Integration Guide
          </Button>
          <Button variant="outline" size="sm">
            💬 Chat with Inventory Expert
          </Button>
        </div>
      </div>
    </div>
  );
};

export default InventoryDashboard;