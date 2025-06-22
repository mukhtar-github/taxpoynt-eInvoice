/**
 * Week 6 Day 3-4: Real-Time Dashboard Integration Demo
 * 
 * Features demonstrated:
 * - WebSocket service setup for live data
 * - Real-time metric updates without page refresh
 * - Live status indicators for integrations
 * - Notification system for critical events
 * - Auto-refresh mechanisms with user controls
 */

import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Switch } from '@/components/ui/Switch';
import RealTimeDashboard from '@/components/dashboard/RealTimeDashboard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { 
  Wifi, 
  WifiOff, 
  Zap, 
  Bell,
  Activity,
  BarChart3,
  Settings,
  RefreshCw,
  Server,
  Monitor,
  Smartphone
} from 'lucide-react';
import { cn } from '@/utils/cn';

const Week6RealTimeDashboardDemo = () => {
  const [selectedDemo, setSelectedDemo] = useState<'full' | 'activities' | 'metrics'>('full');
  const [notifications, setNotifications] = useState(0);
  
  // WebSocket connection for demo metrics
  const {
    isConnected,
    isConnecting,
    error,
    connectionCount,
    connect,
    disconnect,
    subscribe
  } = useWebSocket({
    autoConnect: false,
    subscriptions: ['metrics', 'activities', 'alerts']
  });

  // Simulate real-time notifications
  useEffect(() => {
    const interval = setInterval(() => {
      if (isConnected && Math.random() > 0.7) {
        setNotifications(prev => prev + 1);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isConnected]);

  const demoOptions = [
    {
      id: 'full',
      title: 'Full Real-Time Dashboard',
      description: 'Complete dashboard with all real-time features',
      icon: Monitor,
      color: 'border-blue-500'
    },
    {
      id: 'activities',
      title: 'Activities Only',
      description: 'Real-time activity feed with WebSocket',
      icon: Activity,
      color: 'border-green-500'
    },
    {
      id: 'metrics',
      title: 'Live Metrics',
      description: 'Real-time metrics updates and indicators',
      icon: BarChart3,
      color: 'border-purple-500'
    }
  ];

  const features = [
    {
      title: 'WebSocket Infrastructure',
      description: 'FastAPI WebSocket server with connection management',
      icon: Server,
      status: 'implemented',
      details: [
        'Multi-endpoint WebSocket support (/ws/dashboard, /ws/activities, /ws/integrations)',
        'JWT authentication for WebSocket connections',
        'Auto-reconnection with exponential backoff',
        'Connection pooling by organization'
      ]
    },
    {
      title: 'Real-Time Metric Updates',
      description: 'Live dashboard metrics without page refresh',
      icon: BarChart3,
      status: 'implemented',
      details: [
        'Dashboard summary metrics streaming',
        'IRN generation metrics updates',
        'Validation success rate monitoring',
        'Integration health status'
      ]
    },
    {
      title: 'Live Status Indicators',
      description: 'Real-time integration and system status',
      icon: Wifi,
      status: 'implemented',
      details: [
        'Connection status indicators',
        'Integration sync status',
        'Error rate monitoring',
        'Performance metrics display'
      ]
    },
    {
      title: 'Notification System',
      description: 'Critical events and alerts in real-time',
      icon: Bell,
      status: 'implemented',
      details: [
        'Browser push notifications',
        'In-app notification center',
        'Severity-based alerting',
        'Notification history tracking'
      ]
    },
    {
      title: 'Auto-Refresh Controls',
      description: 'User-configurable real-time updates',
      icon: RefreshCw,
      status: 'implemented',
      details: [
        'Toggle auto-refresh on/off',
        'Manual refresh triggers',
        'Configurable update intervals',
        'Connection management controls'
      ]
    },
    {
      title: 'Mobile Optimization',
      description: 'Responsive real-time dashboard',
      icon: Smartphone,
      status: 'implemented',
      details: [
        'Touch-optimized controls',
        'Responsive WebSocket indicators',
        'Mobile-friendly notifications',
        'Adaptive layout for all screens'
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2 text-3xl font-bold text-gray-900">
            <Zap className="w-8 h-8 text-primary" />
            Week 6 Day 3-4: Real-Time Dashboard Integration
          </div>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            WebSocket service setup, real-time metric updates, live status indicators, 
            notification system, and auto-refresh mechanisms with user controls.
          </p>
          
          {/* Connection Status */}
          <div className="flex items-center justify-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              {isConnected ? (
                <Wifi className="w-4 h-4 text-green-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-500" />
              )}
              <span className={isConnected ? 'text-green-600' : 'text-red-600'}>
                {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
              </span>
            </div>
            
            {connectionCount > 0 && (
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-blue-500" />
                <span className="text-blue-600">{connectionCount} Active Connections</span>
              </div>
            )}
            
            {notifications > 0 && (
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-orange-500" />
                <span className="text-orange-600">{notifications} Notifications</span>
              </div>
            )}
          </div>
        </div>

        {/* Demo Controls */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold">Demo Controls</h2>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={isConnected}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        connect();
                      } else {
                        disconnect();
                      }
                    }}
                  />
                  <span className="text-sm text-gray-600">
                    WebSocket Connection
                  </span>
                </div>
                
                {error && (
                  <Badge variant="destructive" className="text-xs">
                    {error}
                  </Badge>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-4">
              {demoOptions.map((option) => {
                const IconComponent = option.icon;
                return (
                  <button
                    key={option.id}
                    onClick={() => setSelectedDemo(option.id as any)}
                    className={cn(
                      'p-4 border-2 rounded-lg text-left hover:bg-gray-50 transition-colors',
                      selectedDemo === option.id ? option.color : 'border-gray-200'
                    )}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <IconComponent className="w-5 h-5 text-primary" />
                      <span className="font-medium">{option.title}</span>
                    </div>
                    <p className="text-sm text-gray-600">{option.description}</p>
                  </button>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Demo Content */}
        <div className="space-y-6">
          {selectedDemo === 'full' && (
            <RealTimeDashboard defaultAutoRefresh={isConnected} />
          )}
          
          {selectedDemo === 'activities' && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <Activity className="w-5 h-5" />
                  Real-Time Activities Only
                </h3>
              </CardHeader>
              <CardContent className="p-0">
                {/* This would show just the ConnectedActivityFeed with WebSocket */}
                <div className="p-6 text-center text-gray-500">
                  Real-time activity feed component would be displayed here
                </div>
              </CardContent>
            </Card>
          )}
          
          {selectedDemo === 'metrics' && (
            <Card>
              <CardHeader>
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <BarChart3 className="w-5 h-5" />
                  Live Metrics Only
                </h3>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {/* Mock live metrics */}
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <div className="text-2xl font-bold text-blue-600">1,234</div>
                    <div className="text-sm text-blue-800">Total IRNs</div>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-xs text-green-600">Live</span>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-green-50 rounded-lg">
                    <div className="text-2xl font-bold text-green-600">98.5%</div>
                    <div className="text-sm text-green-800">Success Rate</div>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-xs text-green-600">Live</span>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-purple-50 rounded-lg">
                    <div className="text-2xl font-bold text-purple-600">5</div>
                    <div className="text-sm text-purple-800">Integrations</div>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-xs text-green-600">Live</span>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <div className="text-2xl font-bold text-orange-600">2.1%</div>
                    <div className="text-sm text-orange-800">Error Rate</div>
                    <div className="flex items-center gap-1 mt-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-xs text-green-600">Live</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Implementation Features */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <Card key={index}>
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                      <IconComponent className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold">{feature.title}</h3>
                      <Badge variant="success" className="text-xs mt-1">
                        {feature.status}
                      </Badge>
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mb-3">{feature.description}</p>
                  <ul className="space-y-1">
                    {feature.details.map((detail, i) => (
                      <li key={i} className="text-xs text-gray-500 flex items-start gap-1">
                        <span className="w-1 h-1 bg-gray-400 rounded-full mt-1.5 flex-shrink-0" />
                        {detail}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Technical Implementation */}
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Technical Implementation Overview</h3>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Server className="w-4 h-4" />
                  Backend WebSocket Infrastructure
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• FastAPI WebSocket endpoints with JWT authentication</li>
                  <li>• Connection manager for organization-based broadcasting</li>
                  <li>• Activity service integration for real-time data</li>
                  <li>• Background updater for periodic metric streaming</li>
                  <li>• Subscription-based event filtering</li>
                </ul>
              </div>
              
              <div>
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Monitor className="w-4 h-4" />
                  Frontend Real-Time Features
                </h4>
                <ul className="space-y-2 text-sm text-gray-600">
                  <li>• useWebSocket hook with auto-reconnection</li>
                  <li>• Real-time dashboard component with live metrics</li>
                  <li>• WebSocket message subscription system</li>
                  <li>• Browser notification integration</li>
                  <li>• Connection status indicators and controls</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Week6RealTimeDashboardDemo;