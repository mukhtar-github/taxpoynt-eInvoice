/**
 * Dashboard Preferences Component for Feed Customization
 * 
 * Features:
 * - Activity feed display preferences
 * - Dashboard layout customization
 * - Notification settings
 * - Refresh interval controls
 * - Theme and display options
 * - Data export preferences
 */

import React, { useState, useEffect } from 'react';
import { Save, Settings, Bell, Eye, EyeOff, RefreshCw, Download, Palette } from 'lucide-react';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '../ui/Alert';
import { Switch } from '../ui/Switch';
import { Label } from '../ui/Label';
import { Input } from '../ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/Select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/Tabs';
import { cn } from '../../utils/cn';

interface DashboardPreferences {
  // Activity Feed Settings
  activityFeed: {
    enabled: boolean;
    maxItems: number;
    showFilters: boolean;
    enablePullToRefresh: boolean;
    showTimestamps: boolean;
    autoRefresh: boolean;
    refreshInterval: number; // in seconds
    visibleActivityTypes: string[];
  };
  
  // Dashboard Layout Settings
  layout: {
    compactMode: boolean;
    showMetricTrends: boolean;
    showQuickActions: boolean;
    metricsPerRow: number;
    cardAnimations: boolean;
  };
  
  // Notification Settings
  notifications: {
    browserNotifications: boolean;
    criticalAlerts: boolean;
    successNotifications: boolean;
    errorNotifications: boolean;
    emailDigest: boolean;
    soundEnabled: boolean;
  };
  
  // Performance Settings
  performance: {
    enableRealTime: boolean;
    maxConcurrentConnections: number;
    cacheEnabled: boolean;
    preloadData: boolean;
  };
  
  // Display Settings
  display: {
    theme: 'light' | 'dark' | 'auto';
    reducedMotion: boolean;
    highContrast: boolean;
    fontSize: 'small' | 'medium' | 'large';
  };
}

const DEFAULT_PREFERENCES: DashboardPreferences = {
  activityFeed: {
    enabled: true,
    maxItems: 50,
    showFilters: true,
    enablePullToRefresh: true,
    showTimestamps: true,
    autoRefresh: true,
    refreshInterval: 30,
    visibleActivityTypes: ['all']
  },
  layout: {
    compactMode: false,
    showMetricTrends: true,
    showQuickActions: true,
    metricsPerRow: 4,
    cardAnimations: true
  },
  notifications: {
    browserNotifications: true,
    criticalAlerts: true,
    successNotifications: false,
    errorNotifications: true,
    emailDigest: false,
    soundEnabled: false
  },
  performance: {
    enableRealTime: true,
    maxConcurrentConnections: 5,
    cacheEnabled: true,
    preloadData: true
  },
  display: {
    theme: 'auto',
    reducedMotion: false,
    highContrast: false,
    fontSize: 'medium'
  }
};

const ACTIVITY_TYPES = [
  { value: 'all', label: 'All Activities' },
  { value: 'invoice_generated', label: 'Invoice Generated' },
  { value: 'integration_sync', label: 'Integration Sync' },
  { value: 'user_action', label: 'User Actions' },
  { value: 'system_event', label: 'System Events' },
  { value: 'error', label: 'Errors' },
  { value: 'submission', label: 'FIRS Submissions' }
];

const DashboardPreferences: React.FC = () => {
  const [preferences, setPreferences] = useState<DashboardPreferences>(DEFAULT_PREFERENCES);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preferences from localStorage on mount
  useEffect(() => {
    const loadPreferences = () => {
      try {
        const stored = localStorage.getItem('dashboard_preferences');
        if (stored) {
          const parsed = JSON.parse(stored);
          setPreferences({ ...DEFAULT_PREFERENCES, ...parsed });
        }
      } catch (err) {
        console.error('Error loading preferences:', err);
        setError('Failed to load saved preferences');
      }
    };

    loadPreferences();
  }, []);

  // Handle preference changes
  const handleChange = (section: keyof DashboardPreferences, key: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
    
    // Clear status messages
    setSuccess(false);
    setError(null);
  };

  // Handle activity type selection
  const handleActivityTypeChange = (activityType: string, enabled: boolean) => {
    setPreferences(prev => {
      const currentTypes = prev.activityFeed.visibleActivityTypes;
      let newTypes: string[];
      
      if (activityType === 'all') {
        newTypes = enabled ? ['all'] : [];
      } else {
        if (enabled) {
          newTypes = currentTypes.includes('all') 
            ? [activityType]
            : [...currentTypes.filter(t => t !== 'all'), activityType];
        } else {
          newTypes = currentTypes.filter(t => t !== activityType);
        }
      }
      
      return {
        ...prev,
        activityFeed: {
          ...prev.activityFeed,
          visibleActivityTypes: newTypes
        }
      };
    });
  };

  // Save preferences
  const handleSave = async () => {
    setIsSaving(true);
    setSuccess(false);
    setError(null);

    try {
      // Save to localStorage
      localStorage.setItem('dashboard_preferences', JSON.stringify(preferences));
      
      // Simulate API call (replace with actual API when available)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess(true);
      
      // Apply preferences immediately
      applyPreferences();
      
    } catch (err) {
      setError('Failed to save preferences');
      console.error('Error saving preferences:', err);
    } finally {
      setIsSaving(false);
    }
  };

  // Apply preferences to the application
  const applyPreferences = () => {
    // Apply theme
    const root = document.documentElement;
    if (preferences.display.theme === 'dark') {
      root.classList.add('dark');
    } else if (preferences.display.theme === 'light') {
      root.classList.remove('dark');
    } else {
      // Auto theme based on system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', prefersDark);
    }

    // Apply font size
    root.style.fontSize = {
      small: '14px',
      medium: '16px',
      large: '18px'
    }[preferences.display.fontSize];

    // Apply reduced motion
    if (preferences.display.reducedMotion) {
      root.style.setProperty('--animation-duration', '0ms');
    } else {
      root.style.removeProperty('--animation-duration');
    }

    // Dispatch custom event for other components to listen to
    window.dispatchEvent(new CustomEvent('dashboardPreferencesChanged', {
      detail: preferences
    }));
  };

  // Reset to defaults
  const handleReset = () => {
    setPreferences(DEFAULT_PREFERENCES);
    setSuccess(false);
    setError(null);
  };

  return (
    <Card className="border-l-4 border-l-primary">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-primary" />
            Dashboard Preferences
          </CardTitle>
          <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
            User Settings
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Status Messages */}
        {success && (
          <Alert variant="success">
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>Preferences have been saved and applied successfully</AlertDescription>
          </Alert>
        )}

        {error && (
          <Alert variant="error">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="activity-feed" className="w-full">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-5">
            <TabsTrigger value="activity-feed">Activity Feed</TabsTrigger>
            <TabsTrigger value="layout">Layout</TabsTrigger>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="performance">Performance</TabsTrigger>
            <TabsTrigger value="display">Display</TabsTrigger>
          </TabsList>

          {/* Activity Feed Settings */}
          <TabsContent value="activity-feed" className="space-y-4">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label className="text-base font-medium">Enable Activity Feed</Label>
                  <p className="text-sm text-gray-600">Show recent activity timeline on dashboard</p>
                </div>
                <Switch
                  checked={preferences.activityFeed.enabled}
                  onCheckedChange={(checked) => handleChange('activityFeed', 'enabled', checked)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max-items">Maximum Items</Label>
                  <Input
                    id="max-items"
                    type="number"
                    min="10"
                    max="200"
                    value={preferences.activityFeed.maxItems}
                    onChange={(e) => handleChange('activityFeed', 'maxItems', parseInt(e.target.value, 10))}
                    disabled={!preferences.activityFeed.enabled}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="refresh-interval">Refresh Interval (seconds)</Label>
                  <Input
                    id="refresh-interval"
                    type="number"
                    min="5"
                    max="300"
                    value={preferences.activityFeed.refreshInterval}
                    onChange={(e) => handleChange('activityFeed', 'refreshInterval', parseInt(e.target.value, 10))}
                    disabled={!preferences.activityFeed.enabled || !preferences.activityFeed.autoRefresh}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-base font-medium">Activity Feed Options</Label>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="show-filters">Show Filter Controls</Label>
                    <Switch
                      id="show-filters"
                      checked={preferences.activityFeed.showFilters}
                      onCheckedChange={(checked) => handleChange('activityFeed', 'showFilters', checked)}
                      disabled={!preferences.activityFeed.enabled}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="auto-refresh">Auto Refresh</Label>
                    <Switch
                      id="auto-refresh"
                      checked={preferences.activityFeed.autoRefresh}
                      onCheckedChange={(checked) => handleChange('activityFeed', 'autoRefresh', checked)}
                      disabled={!preferences.activityFeed.enabled}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="show-timestamps">Show Timestamps</Label>
                    <Switch
                      id="show-timestamps"
                      checked={preferences.activityFeed.showTimestamps}
                      onCheckedChange={(checked) => handleChange('activityFeed', 'showTimestamps', checked)}
                      disabled={!preferences.activityFeed.enabled}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="pull-refresh">Pull to Refresh</Label>
                    <Switch
                      id="pull-refresh"
                      checked={preferences.activityFeed.enablePullToRefresh}
                      onCheckedChange={(checked) => handleChange('activityFeed', 'enablePullToRefresh', checked)}
                      disabled={!preferences.activityFeed.enabled}
                    />
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <Label className="text-base font-medium">Visible Activity Types</Label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {ACTIVITY_TYPES.map(type => (
                    <div key={type.value} className="flex items-center space-x-2">
                      <Switch
                        id={`activity-${type.value}`}
                        checked={preferences.activityFeed.visibleActivityTypes.includes(type.value)}
                        onCheckedChange={(checked) => handleActivityTypeChange(type.value, checked)}
                        disabled={!preferences.activityFeed.enabled}
                      />
                      <Label htmlFor={`activity-${type.value}`} className="text-sm">
                        {type.label}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Layout Settings */}
          <TabsContent value="layout" className="space-y-4">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Compact Mode</Label>
                    <p className="text-xs text-gray-600">Reduce spacing and padding</p>
                  </div>
                  <Switch
                    checked={preferences.layout.compactMode}
                    onCheckedChange={(checked) => handleChange('layout', 'compactMode', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Show Metric Trends</Label>
                    <p className="text-xs text-gray-600">Display trend arrows on metrics</p>
                  </div>
                  <Switch
                    checked={preferences.layout.showMetricTrends}
                    onCheckedChange={(checked) => handleChange('layout', 'showMetricTrends', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Show Quick Actions</Label>
                    <p className="text-xs text-gray-600">Display floating action button</p>
                  </div>
                  <Switch
                    checked={preferences.layout.showQuickActions}
                    onCheckedChange={(checked) => handleChange('layout', 'showQuickActions', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Card Animations</Label>
                    <p className="text-xs text-gray-600">Enable hover and loading animations</p>
                  </div>
                  <Switch
                    checked={preferences.layout.cardAnimations}
                    onCheckedChange={(checked) => handleChange('layout', 'cardAnimations', checked)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="metrics-per-row">Metrics Per Row (Desktop)</Label>
                <Select 
                  value={preferences.layout.metricsPerRow.toString()} 
                  onValueChange={(value) => handleChange('layout', 'metricsPerRow', parseInt(value, 10))}
                >
                  <SelectTrigger id="metrics-per-row">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2">2 per row</SelectItem>
                    <SelectItem value="3">3 per row</SelectItem>
                    <SelectItem value="4">4 per row</SelectItem>
                    <SelectItem value="5">5 per row</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </TabsContent>

          {/* Notification Settings */}
          <TabsContent value="notifications" className="space-y-4">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Browser Notifications</Label>
                    <p className="text-xs text-gray-600">Show desktop notifications</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.browserNotifications}
                    onCheckedChange={(checked) => handleChange('notifications', 'browserNotifications', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Critical Alerts</Label>
                    <p className="text-xs text-gray-600">System failures and errors</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.criticalAlerts}
                    onCheckedChange={(checked) => handleChange('notifications', 'criticalAlerts', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Success Notifications</Label>
                    <p className="text-xs text-gray-600">Successful operations</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.successNotifications}
                    onCheckedChange={(checked) => handleChange('notifications', 'successNotifications', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Error Notifications</Label>
                    <p className="text-xs text-gray-600">Failed operations</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.errorNotifications}
                    onCheckedChange={(checked) => handleChange('notifications', 'errorNotifications', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Email Digest</Label>
                    <p className="text-xs text-gray-600">Daily summary email</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.emailDigest}
                    onCheckedChange={(checked) => handleChange('notifications', 'emailDigest', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Sound Notifications</Label>
                    <p className="text-xs text-gray-600">Audio alerts</p>
                  </div>
                  <Switch
                    checked={preferences.notifications.soundEnabled}
                    onCheckedChange={(checked) => handleChange('notifications', 'soundEnabled', checked)}
                  />
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Performance Settings */}
          <TabsContent value="performance" className="space-y-4">
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Enable Real-Time Updates</Label>
                    <p className="text-xs text-gray-600">WebSocket connections for live data</p>
                  </div>
                  <Switch
                    checked={preferences.performance.enableRealTime}
                    onCheckedChange={(checked) => handleChange('performance', 'enableRealTime', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Cache Enabled</Label>
                    <p className="text-xs text-gray-600">Store data locally for faster loading</p>
                  </div>
                  <Switch
                    checked={preferences.performance.cacheEnabled}
                    onCheckedChange={(checked) => handleChange('performance', 'cacheEnabled', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>Preload Data</Label>
                    <p className="text-xs text-gray-600">Load data in background</p>
                  </div>
                  <Switch
                    checked={preferences.performance.preloadData}
                    onCheckedChange={(checked) => handleChange('performance', 'preloadData', checked)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="max-connections">Max WebSocket Connections</Label>
                <Input
                  id="max-connections"
                  type="number"
                  min="1"
                  max="10"
                  value={preferences.performance.maxConcurrentConnections}
                  onChange={(e) => handleChange('performance', 'maxConcurrentConnections', parseInt(e.target.value, 10))}
                  disabled={!preferences.performance.enableRealTime}
                />
                <p className="text-xs text-gray-600">
                  Higher values may improve responsiveness but use more resources
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Display Settings */}
          <TabsContent value="display" className="space-y-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="theme">Theme</Label>
                <Select 
                  value={preferences.display.theme} 
                  onValueChange={(value: any) => handleChange('display', 'theme', value)}
                >
                  <SelectTrigger id="theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="auto">Auto (System)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="font-size">Font Size</Label>
                <Select 
                  value={preferences.display.fontSize} 
                  onValueChange={(value: any) => handleChange('display', 'fontSize', value)}
                >
                  <SelectTrigger id="font-size">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="small">Small</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="large">Large</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Reduced Motion</Label>
                    <p className="text-xs text-gray-600">Minimize animations</p>
                  </div>
                  <Switch
                    checked={preferences.display.reducedMotion}
                    onCheckedChange={(checked) => handleChange('display', 'reducedMotion', checked)}
                  />
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <Label>High Contrast</Label>
                    <p className="text-xs text-gray-600">Improve visual accessibility</p>
                  </div>
                  <Switch
                    checked={preferences.display.highContrast}
                    onCheckedChange={(checked) => handleChange('display', 'highContrast', checked)}
                  />
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-6 border-t">
          <Button
            variant="outline"
            onClick={handleReset}
            disabled={isSaving}
          >
            Reset to Defaults
          </Button>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => {
                const dataStr = JSON.stringify(preferences, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'dashboard-preferences.json';
                link.click();
                URL.revokeObjectURL(url);
              }}
              disabled={isSaving}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>

            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              {isSaving ? 'Saving...' : 'Save Preferences'}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default DashboardPreferences;