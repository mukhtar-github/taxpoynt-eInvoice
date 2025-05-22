import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, Button, Typography } from '@/components/ui';

const FIRSSettings: React.FC = () => {
  const [apiUrl, setApiUrl] = useState('/api/firs');
  const [timeout, setTimeout] = useState(30000);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    // Load settings from localStorage
    const savedApiUrl = localStorage.getItem('firs_api_url');
    const savedTimeout = localStorage.getItem('firs_timeout');
    
    if (savedApiUrl) {
      setApiUrl(savedApiUrl);
    }
    
    if (savedTimeout) {
      setTimeout(parseInt(savedTimeout, 10));
    }
  }, []);

  const saveSettings = () => {
    // Save settings to localStorage
    localStorage.setItem('firs_api_url', apiUrl);
    localStorage.setItem('firs_timeout', timeout.toString());
    
    // Show saved message
    setSaved(true);
    // Clear the saved message after 3 seconds
    window.setTimeout(() => setSaved(false), 3000);
  };

  return (
    <Card>
      <CardHeader className="bg-dark text-white">
        <Typography.Heading level="h3" className="text-white">
          API Settings
        </Typography.Heading>
      </CardHeader>
      <CardContent>
        <div className="mb-4">
          <label htmlFor="apiUrl" className="block mb-2">
            API Base URL
          </label>
          <input
            id="apiUrl"
            type="text"
            className="w-full p-2 border border-gray-300 rounded"
            value={apiUrl}
            onChange={(e) => setApiUrl(e.target.value)}
          />
          <Typography.Text className="text-gray-500 text-sm mt-1">
            The base URL for API requests (normally should not be changed)
          </Typography.Text>
        </div>
        
        <div className="mb-4">
          <label htmlFor="timeout" className="block mb-2">
            Request Timeout (ms)
          </label>
          <input
            id="timeout"
            type="number"
            className="w-full p-2 border border-gray-300 rounded"
            value={timeout}
            onChange={(e) => setTimeout(parseInt(e.target.value, 10) || 30000)}
            min={5000}
            max={120000}
            step={1000}
          />
          <Typography.Text className="text-gray-500 text-sm mt-1">
            How long to wait for API responses before timing out (in milliseconds)
          </Typography.Text>
        </div>
        
        <Button onClick={saveSettings}>
          Save Settings
        </Button>
        
        {saved && (
          <Typography.Text className="text-green-500 ml-4">
            Settings saved successfully!
          </Typography.Text>
        )}
      </CardContent>
    </Card>
  );
};

export default FIRSSettings;
