import React, { useState } from 'react';
import { Save, Settings } from 'lucide-react';
import axios from 'axios';

import { Button } from '../../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';
import { Switch } from '../../ui/Switch';
import { Label } from '../../ui/Label';
import { Input } from '../../ui/Input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../ui/Select';

interface SignatureSettings {
  algorithm: string;
  version: string;
  enableCaching: boolean;
  cacheSize: number;
  cacheTtl: number;
  parallelProcessing: boolean;
  maxWorkers: number;
}

/**
 * Signature Settings Component
 * 
 * Allows users to configure:
 * - Default signing algorithm and version
 * - Caching parameters (enable/disable, size, TTL)
 * - Parallel processing options
 */
const SignatureSettings: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Settings state
  const [settings, setSettings] = useState<SignatureSettings>({
    algorithm: 'RSA-PSS-SHA256',
    version: '2.0',
    enableCaching: true,
    cacheSize: 1000,
    cacheTtl: 3600,
    parallelProcessing: true,
    maxWorkers: 4
  });
  
  // Handle settings changes
  const handleChange = (name: keyof SignatureSettings, value: string | boolean | number) => {
    setSettings(prev => ({ ...prev, [name]: value }));
    // Clear status messages when user makes changes
    setSuccess(false);
    setError(null);
  };
  
  // Save settings
  const handleSave = async () => {
    setIsLoading(true);
    setSuccess(false);
    setError(null);
    
    try {
      // API call to save settings
      await axios.post('/api/platform/signatures/settings', settings);
      setSuccess(true);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Failed to save settings');
      } else if (err instanceof Error) {
        setError(`Error: ${err.message}`);
      } else {
        setError('An unknown error occurred');
      }
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-5 w-5 text-cyan-600" />
            Signature Settings
          </CardTitle>
          <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
            APP
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Success message */}
        {success && (
          <Alert variant="success">
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>Settings have been saved successfully</AlertDescription>
          </Alert>
        )}
        
        {/* Error message */}
        {error && (
          <Alert variant="error">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {/* Algorithm Settings */}
        <div>
          <h3 className="text-sm font-medium mb-3 pb-1 border-b">
            Signature Algorithm Settings
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="algorithm">Default Algorithm</Label>
              <Select 
                value={settings.algorithm} 
                onValueChange={(value) => handleChange('algorithm', value)}
              >
                <SelectTrigger id="algorithm" className="w-full">
                  <SelectValue placeholder="Select algorithm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RSA-PSS-SHA256">RSA-PSS-SHA256</SelectItem>
                  <SelectItem value="RSA-PKCS1-SHA256">RSA-PKCS1-SHA256</SelectItem>
                  <SelectItem value="ED25519">ED25519</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                RSA-PSS-SHA256 is recommended for stronger security
              </p>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="version">CSID Version</Label>
              <Select 
                value={settings.version} 
                onValueChange={(value) => handleChange('version', value)}
              >
                <SelectTrigger id="version" className="w-full">
                  <SelectValue placeholder="Select version" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2.0">2.0 (Latest)</SelectItem>
                  <SelectItem value="1.0">1.0 (Legacy)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                Version 2.0 includes enhanced FIRS compliance features
              </p>
            </div>
          </div>
        </div>
        
        {/* Caching Settings */}
        <div>
          <h3 className="text-sm font-medium mb-3 pb-1 border-b">
            Caching Settings
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="enable-caching" className="mb-1 block">Enable Signature Caching</Label>
                <p className="text-xs text-gray-500">
                  Improves performance for high-volume processing
                </p>
              </div>
              <Switch 
                id="enable-caching" 
                checked={settings.enableCaching}
                onCheckedChange={(checked) => handleChange('enableCaching', checked)}
              />
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="cache-size">Cache Size (entries)</Label>
                <Input 
                  id="cache-size"
                  type="number"
                  min="100"
                  max="10000"
                  value={settings.cacheSize}
                  onChange={(e) => handleChange('cacheSize', parseInt(e.target.value, 10))}
                  disabled={!settings.enableCaching}
                />
                <p className="text-xs text-gray-500">
                  Maximum number of signatures to keep in memory
                </p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="cache-ttl">Cache TTL (seconds)</Label>
                <Input 
                  id="cache-ttl"
                  type="number"
                  min="60"
                  max="86400"
                  value={settings.cacheTtl}
                  onChange={(e) => handleChange('cacheTtl', parseInt(e.target.value, 10))}
                  disabled={!settings.enableCaching}
                />
                <p className="text-xs text-gray-500">
                  How long signatures remain valid in cache
                </p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Performance Settings */}
        <div>
          <h3 className="text-sm font-medium mb-3 pb-1 border-b">
            Performance Settings
          </h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <Label htmlFor="parallel-processing" className="mb-1 block">Enable Parallel Processing</Label>
                <p className="text-xs text-gray-500">
                  Uses multiple threads for batch signature operations
                </p>
              </div>
              <Switch 
                id="parallel-processing" 
                checked={settings.parallelProcessing}
                onCheckedChange={(checked) => handleChange('parallelProcessing', checked)}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="max-workers">Maximum Worker Threads</Label>
              <Input 
                id="max-workers"
                type="number"
                min="1"
                max="16"
                value={settings.maxWorkers}
                onChange={(e) => handleChange('maxWorkers', parseInt(e.target.value, 10))}
                disabled={!settings.parallelProcessing}
              />
              <p className="text-xs text-gray-500">
                Recommended: Use CPU core count (current system: {navigator.hardwareConcurrency || 4})
              </p>
            </div>
          </div>
        </div>
        
        {/* Save button */}
        <div className="pt-4 border-t">
          <Button
            onClick={handleSave}
            disabled={isLoading}
            className="bg-cyan-600 hover:bg-cyan-700 flex items-center gap-2"
          >
            <Save className="h-4 w-4" />
            {isLoading ? 'Saving...' : 'Save Settings'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default SignatureSettings;
