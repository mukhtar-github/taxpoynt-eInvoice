import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { Select } from '../../ui/Select';
import { FormField } from '../../ui/FormField';
import { Alert } from '../../ui/Alert';
import { Badge } from '../../ui/Badge';
import { Spinner } from '../../ui/Spinner';

interface SquareLocation {
  id: string;
  name: string;
  address?: string;
  status: 'ACTIVE' | 'INACTIVE';
}

interface SquareConnectorProps {
  organizationId: string;
  onConnectionSuccess?: (connection: any) => void;
  onConnectionError?: (error: string) => void;
  className?: string;
}

const SquareConnector: React.FC<SquareConnectorProps> = ({
  organizationId,
  onConnectionSuccess,
  onConnectionError,
  className = ''
}) => {
  const [step, setStep] = useState<'initial' | 'locations' | 'webhooks' | 'complete'>('initial');
  const [isConnecting, setIsConnecting] = useState(false);
  const [isLoadingLocations, setIsLoadingLocations] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  
  // OAuth and connection state
  const [oauthState, setOauthState] = useState<string>('');
  const [accessToken, setAccessToken] = useState<string>('');
  const [merchantId, setMerchantId] = useState<string>('');
  
  // Location selection
  const [locations, setLocations] = useState<SquareLocation[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<string>('');
  
  // Webhook configuration
  const [webhookUrl, setWebhookUrl] = useState<string>('');
  const [isConfiguringWebhooks, setIsConfiguringWebhooks] = useState(false);

  useEffect(() => {
    // Check if we're returning from OAuth flow
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      setConnectionError(`OAuth error: ${error}`);
      setStep('initial');
    } else if (code && state) {
      handleOAuthCallback(code, state);
    }
  }, []);

  const generateOAuthState = (): string => {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  };

  const handleConnect = async () => {
    setIsConnecting(true);
    setConnectionError(null);
    
    try {
      const state = generateOAuthState();
      setOauthState(state);
      
      // Store state in sessionStorage for validation
      sessionStorage.setItem('square_oauth_state', state);
      
      // Redirect to Square OAuth
      const redirectUri = `${window.location.origin}/dashboard/integrations/square/callback`;
      const baseUrl = process.env.NODE_ENV === 'production' 
        ? 'https://connect.squareup.com' 
        : 'https://connect.squareupsandbox.com';
      
      const oauthUrl = new URL('/oauth2/authorize', baseUrl);
      oauthUrl.searchParams.append('client_id', process.env.NEXT_PUBLIC_SQUARE_APPLICATION_ID || '');
      oauthUrl.searchParams.append('response_type', 'code');
      oauthUrl.searchParams.append('scope', 'PAYMENTS_READ ORDERS_READ CUSTOMERS_READ INVENTORY_READ MERCHANT_PROFILE_READ ITEMS_READ');
      oauthUrl.searchParams.append('redirect_uri', redirectUri);
      oauthUrl.searchParams.append('state', state);
      
      window.location.href = oauthUrl.toString();
    } catch (error: any) {
      console.error('Failed to connect to Square', error);
      setConnectionError(error.message || 'Failed to initiate OAuth flow');
      setIsConnecting(false);
    }
  };

  const handleOAuthCallback = async (code: string, state: string) => {
    try {
      setIsConnecting(true);
      
      // Validate state parameter
      const storedState = sessionStorage.getItem('square_oauth_state');
      if (state !== storedState) {
        throw new Error('Invalid OAuth state parameter');
      }
      
      // Exchange code for access token
      const response = await fetch('/api/integrations/pos/square/oauth/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          code,
          state,
          organization_id: organizationId
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to exchange OAuth code');
      }
      
      const tokenData = await response.json();
      setAccessToken(tokenData.access_token);
      setMerchantId(tokenData.merchant_id);
      
      // Clean up
      sessionStorage.removeItem('square_oauth_state');
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Move to location selection
      setStep('locations');
      await loadLocations(tokenData.access_token);
      
    } catch (error: any) {
      console.error('OAuth callback error:', error);
      setConnectionError(error.message || 'OAuth flow failed');
      setStep('initial');
    } finally {
      setIsConnecting(false);
    }
  };

  const loadLocations = async (token: string) => {
    setIsLoadingLocations(true);
    try {
      const response = await fetch('/api/integrations/pos/square/locations', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to load Square locations');
      }
      
      const data = await response.json();
      setLocations(data.locations || []);
      
      // Auto-select if only one location
      if (data.locations?.length === 1) {
        setSelectedLocation(data.locations[0].id);
      }
    } catch (error: any) {
      console.error('Failed to load locations:', error);
      setConnectionError(error.message || 'Failed to load locations');
    } finally {
      setIsLoadingLocations(false);
    }
  };

  const handleLocationSelection = () => {
    if (!selectedLocation) {
      setConnectionError('Please select a location to continue');
      return;
    }
    
    setConnectionError(null);
    setStep('webhooks');
    
    // Set default webhook URL
    const defaultWebhookUrl = `${window.location.origin}/api/integrations/pos/square/webhook`;
    setWebhookUrl(defaultWebhookUrl);
  };

  const configureWebhooks = async () => {
    setIsConfiguringWebhooks(true);
    setConnectionError(null);
    
    try {
      const response = await fetch('/api/integrations/pos/square/webhooks', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          webhook_url: webhookUrl,
          location_id: selectedLocation,
          organization_id: organizationId
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to configure webhooks');
      }
      
      const webhookData = await response.json();
      
      // Create the complete connection
      await createConnection(webhookData);
      
    } catch (error: any) {
      console.error('Failed to configure webhooks:', error);
      setConnectionError(error.message || 'Failed to configure webhooks');
    } finally {
      setIsConfiguringWebhooks(false);
    }
  };

  const createConnection = async (webhookData: any) => {
    try {
      const connectionData = {
        organization_id: organizationId,
        connection_name: `Square POS - ${locations.find(l => l.id === selectedLocation)?.name || 'Location'}`,
        pos_type: 'square',
        credentials: {
          access_token: accessToken,
          merchant_id: merchantId,
          location_id: selectedLocation
        },
        webhook_config: {
          webhook_url: webhookUrl,
          webhook_signature_key: webhookData.signature_key,
          subscription_id: webhookData.subscription_id
        },
        settings: {
          auto_sync: true,
          auto_generate_invoice: false
        }
      };
      
      const response = await fetch('/api/integrations/pos/square/connect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(connectionData)
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create connection');
      }
      
      const connection = await response.json();
      setStep('complete');
      onConnectionSuccess?.(connection);
      
    } catch (error: any) {
      console.error('Failed to create connection:', error);
      setConnectionError(error.message || 'Failed to create connection');
    }
  };

  const renderInitialStep = () => (
    <div className="text-center py-6">
      <div className="text-6xl mb-4">⬜</div>
      <h3 className="text-lg font-medium mb-4">Connect Square POS</h3>
      <p className="text-gray-600 text-sm mb-6">
        Connect your Square POS system to automatically sync transactions and generate e-invoices for FIRS compliance.
      </p>
      
      {connectionError && (
        <Alert variant="destructive" className="mb-4">
          <div>
            <p className="font-medium">Connection Error</p>
            <p className="text-sm">{connectionError}</p>
          </div>
        </Alert>
      )}
      
      <Button 
        onClick={handleConnect}
        loading={isConnecting}
        className="bg-blue-600 hover:bg-blue-700 text-white"
      >
        {isConnecting ? 'Connecting...' : 'Connect to Square'}
      </Button>
    </div>
  );

  const renderLocationSelection = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium mb-2">Select Square Location</h3>
        <p className="text-gray-600 text-sm">
          Choose which Square location to connect for transaction syncing.
        </p>
      </div>
      
      {isLoadingLocations ? (
        <div className="text-center py-6">
          <Spinner className="mx-auto mb-2" />
          <p className="text-sm text-gray-600">Loading locations...</p>
        </div>
      ) : (
        <div className="space-y-4">
          <FormField label="Square Location" required>
            <Select
              value={selectedLocation}
              onValueChange={setSelectedLocation}
              className="w-full"
            >
              <option value="">Select a location</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {location.name} {location.address && `- ${location.address}`}
                </option>
              ))}
            </Select>
          </FormField>
          
          {connectionError && (
            <Alert variant="destructive">
              <div>
                <p className="font-medium">Selection Error</p>
                <p className="text-sm">{connectionError}</p>
              </div>
            </Alert>
          )}
          
          <Button 
            onClick={handleLocationSelection}
            disabled={!selectedLocation}
            className="w-full"
          >
            Continue to Webhook Setup
          </Button>
        </div>
      )}
    </div>
  );

  const renderWebhookConfiguration = () => (
    <div className="space-y-6">
      <div className="text-center">
        <h3 className="text-lg font-medium mb-2">Configure Webhooks</h3>
        <p className="text-gray-600 text-sm">
          Set up webhooks to receive real-time transaction updates from Square.
        </p>
      </div>
      
      <FormField 
        label="Webhook URL" 
        required
        description="This URL will receive transaction notifications from Square"
      >
        <Input
          value={webhookUrl}
          onChange={(e) => setWebhookUrl(e.target.value)}
          placeholder="https://your-domain.com/api/webhook"
          disabled={isConfiguringWebhooks}
        />
      </FormField>
      
      {connectionError && (
        <Alert variant="destructive">
          <div>
            <p className="font-medium">Configuration Error</p>
            <p className="text-sm">{connectionError}</p>
          </div>
        </Alert>
      )}
      
      <Button 
        onClick={configureWebhooks}
        loading={isConfiguringWebhooks}
        disabled={!webhookUrl}
        className="w-full"
      >
        {isConfiguringWebhooks ? 'Configuring...' : 'Complete Setup'}
      </Button>
    </div>
  );

  const renderCompleteStep = () => (
    <div className="text-center py-6">
      <div className="text-6xl mb-4">✅</div>
      <h3 className="text-lg font-medium mb-2">Square POS Connected!</h3>
      <p className="text-gray-600 text-sm mb-4">
        Your Square POS system is now connected and ready to sync transactions.
      </p>
      <Badge variant="success" className="mb-4">
        Connected to {locations.find(l => l.id === selectedLocation)?.name}
      </Badge>
      <div className="space-y-2 text-sm text-gray-600">
        <p>• Real-time transaction syncing enabled</p>
        <p>• FIRS e-invoice generation configured</p>
        <p>• Webhook notifications active</p>
      </div>
    </div>
  );

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>Square POS Integration</CardTitle>
      </CardHeader>
      
      <CardContent>
        {step === 'initial' && renderInitialStep()}
        {step === 'locations' && renderLocationSelection()}
        {step === 'webhooks' && renderWebhookConfiguration()}
        {step === 'complete' && renderCompleteStep()}
      </CardContent>
      
      {step !== 'initial' && step !== 'complete' && (
        <CardFooter>
          <Button 
            variant="outline" 
            onClick={() => {
              if (step === 'locations') setStep('initial');
              if (step === 'webhooks') setStep('locations');
            }}
            className="mr-auto"
          >
            Back
          </Button>
        </CardFooter>
      )}
    </Card>
  );
};

export { SquareConnector };