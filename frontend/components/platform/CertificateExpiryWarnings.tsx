import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, Bell, BellOff } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Alert, AlertDescription, AlertTitle } from '../ui/Alert';
import { Switch } from '../ui/Switch';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';
import { Certificate } from '../../types/app';

interface ExpiryWarningSettings {
  enabled: boolean;
  emailNotifications: boolean;
  warnDaysBeforeExpiry: number[];
  lastNotificationSent?: string;
}

interface CertificateExpiryWarningsProps {
  organizationId: string;
  certificates?: Certificate[];
  className?: string;
}

/**
 * Certificate Expiry Warnings Component
 * 
 * Displays automated warnings for certificates nearing expiration
 * and allows configuration of notification preferences.
 */
const CertificateExpiryWarnings: React.FC<CertificateExpiryWarningsProps> = ({
  organizationId,
  certificates = [],
  className = ''
}) => {
  const [settings, setSettings] = useState<ExpiryWarningSettings>({
    enabled: true,
    emailNotifications: true,
    warnDaysBeforeExpiry: [90, 60, 30, 14, 7, 3, 1]
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState<boolean>(false);
  
  // Filter certificates to find those expiring soon
  const getExpiringCertificates = () => {
    const now = new Date();
    return certificates.filter(cert => {
      if (cert.status !== 'active' || !cert.valid_to) return false;
      
      const expiryDate = new Date(cert.valid_to);
      const daysUntilExpiry = Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
      
      // Check if days until expiry matches any of our warning thresholds
      return settings.warnDaysBeforeExpiry.includes(daysUntilExpiry);
    });
  };
  
  // Calculate days until expiry for a certificate
  const getDaysUntilExpiry = (validTo: string) => {
    const now = new Date();
    const expiryDate = new Date(validTo);
    return Math.max(0, Math.floor((expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)));
  };
  
  // Load expiry warning settings
  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      try {
        const response = await apiService.get(`/api/v1/organizations/${organizationId}/certificate-expiry-settings`);
        setSettings(response.data);
      } catch (err: any) {
        console.error("Failed to load certificate expiry settings:", err);
        // Use default settings if API fails
        setSettings({
          enabled: true,
          emailNotifications: true,
          warnDaysBeforeExpiry: [90, 60, 30, 14, 7, 3, 1]
        });
      } finally {
        setLoading(false);
      }
    };
    
    fetchSettings();
  }, [organizationId]);
  
  // Save settings
  const saveSettings = async () => {
    setIsSaving(true);
    setError(null);
    
    try {
      await apiService.put(`/api/v1/organizations/${organizationId}/certificate-expiry-settings`, settings);
    } catch (err: any) {
      setError("Failed to save notification settings. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };
  
  // Handle toggle changes
  const handleToggleEnabled = () => {
    setSettings(prev => ({
      ...prev,
      enabled: !prev.enabled
    }));
  };
  
  const handleToggleEmailNotifications = () => {
    setSettings(prev => ({
      ...prev,
      emailNotifications: !prev.emailNotifications
    }));
  };
  
  // Get expiring certificates
  const expiringCertificates = getExpiringCertificates();
  
  // Show loading state
  if (loading) {
    return (
      <Card className={cn('border-l-4 border-cyan-500', className)}>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-cyan-500" />
            Certificate Expiry Warnings
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-700"></div>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card className={cn('border-l-4 border-cyan-500', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-cyan-500" />
            Certificate Expiry Warnings
          </div>
          <Badge 
            className={cn(
              "ml-2",
              settings.enabled 
                ? "bg-green-100 text-green-800" 
                : "bg-gray-100 text-gray-800"
            )}
          >
            {settings.enabled ? "Enabled" : "Disabled"}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="error" className="mb-4">
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {/* Expiring certificates warnings */}
        {expiringCertificates.length > 0 ? (
          <div className="space-y-3 mb-4">
            {expiringCertificates.map(cert => (
              <Alert 
                key={cert.id} 
                variant="warning"
                className="bg-amber-50 border-amber-200"
              >
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <div className="flex-1">
                  <div className="font-medium text-amber-800">
                    Certificate expiring soon
                  </div>
                  <AlertDescription className="text-amber-700">
                    {cert.subject} will expire in {getDaysUntilExpiry(cert.valid_to)} days.
                    Take action to renew this certificate.
                  </AlertDescription>
                </div>
              </Alert>
            ))}
          </div>
        ) : (
          settings.enabled && (
            <Alert className="mb-4 bg-green-50 border-green-200">
              <Clock className="h-4 w-4 text-green-500" />
              <AlertTitle className="text-green-800">No certificates expiring soon</AlertTitle>
              <AlertDescription className="text-green-700">
                All your active certificates are valid for the next {Math.min(...settings.warnDaysBeforeExpiry)} days.
              </AlertDescription>
            </Alert>
          )
        )}
        
        {/* Notification settings */}
        <div className="border rounded-md p-4 mt-4">
          <h3 className="text-md font-medium mb-4">Notification Settings</h3>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Enable expiry warnings</p>
                <p className="text-sm text-gray-500">Show warnings for certificates about to expire</p>
              </div>
              <Switch 
                checked={settings.enabled} 
                onCheckedChange={handleToggleEnabled}
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Email notifications</p>
                <p className="text-sm text-gray-500">Send email alerts when certificates are about to expire</p>
              </div>
              <Switch 
                checked={settings.emailNotifications} 
                onCheckedChange={handleToggleEmailNotifications}
                disabled={!settings.enabled}
              />
            </div>
            
            <div>
              <p className="font-medium mb-2">Warning schedule</p>
              <p className="text-sm text-gray-500 mb-2">
                Send warnings on these days before expiry:
              </p>
              <div className="flex flex-wrap gap-2">
                {settings.warnDaysBeforeExpiry.map(days => (
                  <Badge key={days} className="bg-cyan-100 text-cyan-800">
                    {days} days
                  </Badge>
                ))}
              </div>
            </div>
          </div>
          
          <div className="mt-4 flex justify-end">
            <Button 
              onClick={saveSettings} 
              disabled={isSaving}
              className="bg-cyan-600 hover:bg-cyan-700"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Saving...
                </>
              ) : (
                'Save Settings'
              )}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CertificateExpiryWarnings;
