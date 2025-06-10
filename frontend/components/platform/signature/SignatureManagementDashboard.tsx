import React, { useState, useEffect } from 'react';
import { BarChart4, BookOpen, RefreshCw, Settings, ShieldCheck, Sliders, Clock } from 'lucide-react';
import axios from 'axios';

import { Button } from '../../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Badge } from '../../ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';

import SignatureVerificationTool from './SignatureVerificationTool';
import SignatureVisualizer from './SignatureVisualizer';
import SignaturePerformanceMonitor from './SignaturePerformanceMonitor';
import SignatureSettings from './SignatureSettings';
import SignatureDocumentation from './SignatureDocumentation';
import SignatureEventsMonitor from './SignatureEventsMonitor';

/**
 * Comprehensive Signature Management Dashboard
 * 
 * Provides a centralized interface for:
 * - Performance monitoring of signature operations
 * - Verification tools for debugging and testing
 * - Detailed configuration and settings
 * - Best practices and documentation
 */
const SignatureManagementDashboard: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [performanceData, setPerformanceData] = useState<any>(null);
  
  // Fetch signature performance metrics
  const fetchPerformanceData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('/api/platform/signatures/metrics');
      setPerformanceData(response.data);
    } catch (err) {
      setError('Failed to load signature performance metrics');
      console.error('Error fetching signature metrics:', err);
    } finally {
      setIsLoading(false);
    }
  };
  
  useEffect(() => {
    // Load performance data on component mount
    fetchPerformanceData();
  }, []);
  
  // Sample signature data for visualization example
  const sampleSignature = {
    isValid: true,
    timestamp: new Date().toISOString(),
    algorithm: 'RSA-PSS-SHA256',
    version: '2.0',
    signatureId: 'f8e7d6c5-b4a3-1234-9876-0123456789ab',
    keyInfo: {
      keyId: 'signing_key_20230601',
      certificate: 'cert_20230601.crt'
    }
  };
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-semibold">Signature Management</h2>
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
            APP
          </Badge>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchPerformanceData}
            disabled={isLoading}
            className="flex items-center gap-1"
          >
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </Button>
        </div>
      </div>
      
      {/* Error message */}
      {error && (
        <Alert variant="error">
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {/* Main dashboard tabs */}
      <Tabs defaultValue="performance" className="w-full">
        <TabsList className="w-full justify-start mb-4">
          <TabsTrigger value="performance" className="flex items-center gap-2">
            <BarChart4 size={16} />
            Performance
          </TabsTrigger>
          <TabsTrigger value="events" className="flex items-center gap-2">
            <Clock size={16} />
            Events
          </TabsTrigger>
          <TabsTrigger value="verification" className="flex items-center gap-2">
            <ShieldCheck size={16} />
            Verification
          </TabsTrigger>
          <TabsTrigger value="visualization" className="flex items-center gap-2">
            <Sliders size={16} />
            Visualization
          </TabsTrigger>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings size={16} />
            Settings
          </TabsTrigger>
          <TabsTrigger value="documentation" className="flex items-center gap-2">
            <BookOpen size={16} />
            Documentation
          </TabsTrigger>
        </TabsList>
        
        {/* Performance monitoring tab */}
        <TabsContent value="performance">
          {performanceData ? (
            <SignaturePerformanceMonitor
              metrics={performanceData}
              isLoading={isLoading}
              onRefresh={fetchPerformanceData}
            />
          ) : (
            <Alert>
              <AlertTitle>Loading Performance Data</AlertTitle>
              <AlertDescription>
                {isLoading ? 'Loading performance metrics...' : 'No performance data available yet.'}
              </AlertDescription>
            </Alert>
          )}
        </TabsContent>
        
        {/* Events monitoring tab */}
        <TabsContent value="events">
          <SignatureEventsMonitor />
        </TabsContent>
        
        {/* Verification tools tab */}
        <TabsContent value="verification">
          <SignatureVerificationTool />
        </TabsContent>
        
        {/* Visualization demo tab */}
        <TabsContent value="visualization">
          <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
              <div>
                <h3 className="text-lg font-medium mb-4">Standard Visualization</h3>
                <SignatureVisualizer signatureData={sampleSignature} />
              </div>
              
              <div>
                <h3 className="text-lg font-medium mb-4">Compact Visualization</h3>
                <div className="p-6 border rounded-lg flex items-center space-x-4">
                  <span>Invoice #INV-001234</span>
                  <SignatureVisualizer signatureData={sampleSignature} compact={true} />
                </div>
                
                <div className="mt-4 p-6 border rounded-lg flex items-center space-x-4">
                  <span>Invoice #INV-005678</span>
                  <SignatureVisualizer 
                    signatureData={{ 
                      ...sampleSignature, 
                      isValid: false 
                    }} 
                    compact={true} 
                  />
                </div>
              </div>
            </div>
            
            <Card className="border-l-4 border-l-amber-500">
              <CardHeader>
                <CardTitle className="text-sm">Integration Example</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-gray-50 p-4 rounded-md overflow-x-auto text-xs">
                  {`import SignatureVisualizer from 'components/platform/signature/SignatureVisualizer';

// In your invoice component:
<div className="invoice-header">
  <h3>Invoice #{invoice.number}</h3>
  <SignatureVisualizer 
    signatureData={invoice.signature} 
    compact={true} 
  />
</div>`}
                </pre>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
        
        {/* Settings tab */}
        <TabsContent value="settings">
          <SignatureSettings />
        </TabsContent>
        
        {/* Documentation tab */}
        <TabsContent value="documentation">
          <SignatureDocumentation />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SignatureManagementDashboard;
