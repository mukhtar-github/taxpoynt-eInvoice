import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Badge } from '../../ui/Badge';
import { Select } from '../../ui/Select';

interface POSConnection {
  id: string;
  name: string;
  type: 'square' | 'toast' | 'lightspeed';
  status: 'connected' | 'disconnected' | 'connecting' | 'error';
  lastSync?: string;
  location?: string;
}

interface POSConnectorCardProps {
  connections?: POSConnection[];
  onConnect?: (posType: string) => void;
  onDisconnect?: (connectionId: string) => void;
}

const POSConnectorCard: React.FC<POSConnectorCardProps> = ({
  connections = [],
  onConnect,
  onDisconnect
}) => {
  const [selectedPOSType, setSelectedPOSType] = useState<string>('square');
  const [isConnecting, setIsConnecting] = useState(false);

  const posTypes = [
    { value: 'square', label: 'Square POS', icon: '⬜' },
    { value: 'toast', label: 'Toast POS', icon: '🍞' },
    { value: 'lightspeed', label: 'Lightspeed', icon: '⚡' }
  ];

  const getStatusBadge = (status: POSConnection['status']) => {
    switch (status) {
      case 'connected':
        return <Badge variant="success">Connected</Badge>;
      case 'connecting':
        return <Badge variant="warning">Connecting...</Badge>;
      case 'error':
        return <Badge variant="destructive">Error</Badge>;
      default:
        return <Badge variant="secondary">Disconnected</Badge>;
    }
  };

  const handleConnect = async () => {
    if (!onConnect) return;
    
    setIsConnecting(true);
    try {
      await onConnect(selectedPOSType);
    } finally {
      setIsConnecting(false);
    }
  };

  const handleDisconnect = async (connectionId: string) => {
    if (!onDisconnect) return;
    await onDisconnect(connectionId);
  };

  const formatLastSync = (lastSync: string): string => {
    const date = new Date(lastSync);
    const now = new Date();
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));
    
    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card variant="elevated" className="h-full">
      <CardHeader>
        <CardTitle>POS Connections</CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {connections.length === 0 ? (
          <div className="text-center py-6">
            <div className="text-4xl mb-2">🔌</div>
            <p className="text-gray-500 text-sm mb-4">
              No POS systems connected yet
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {connections.map((connection) => (
              <div key={connection.id} className="border border-gray-200 rounded-lg p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">
                      {posTypes.find(p => p.value === connection.type)?.icon}
                    </span>
                    <div>
                      <h4 className="font-medium text-sm">{connection.name}</h4>
                      {connection.location && (
                        <p className="text-xs text-gray-500">{connection.location}</p>
                      )}
                    </div>
                  </div>
                  {getStatusBadge(connection.status)}
                </div>
                
                {connection.lastSync && (
                  <p className="text-xs text-gray-500 mb-2">
                    Last sync: {formatLastSync(connection.lastSync)}
                  </p>
                )}
                
                <div className="flex space-x-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleDisconnect(connection.id)}
                    className="text-xs"
                  >
                    Disconnect
                  </Button>
                  <Button 
                    size="sm" 
                    variant="ghost"
                    className="text-xs"
                  >
                    Settings
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex-col space-y-3">
        <div className="w-full">
          <label className="block text-sm font-medium mb-2">Add POS System</label>
          <Select
            value={selectedPOSType}
            onValueChange={setSelectedPOSType}
            className="w-full"
          >
            {posTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.icon} {type.label}
              </option>
            ))}
          </Select>
        </div>
        
        <Button 
          onClick={handleConnect}
          loading={isConnecting}
          className="w-full"
          size="sm"
        >
          {isConnecting ? 'Connecting...' : 'Connect POS System'}
        </Button>
      </CardFooter>
    </Card>
  );
};

export { POSConnectorCard };