import React, { useState } from 'react';
import { useRouter } from 'next/router';
import { ArrowLeft, Users, Link2 } from 'lucide-react';
import DashboardLayout from '@/components/layouts/DashboardLayout';
import PageHeader from '@/components/common/PageHeader';
import { Card, CardHeader, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import HubSpotConnector from '@/components/integrations/crm/HubSpotConnector';
import { useAuth } from '@/hooks/useAuth';
import { CRMConnection } from '@/types/crm';

const AddCRMConnectionPage = () => {
  const router = useRouter();
  const { organization } = useAuth();
  const [selectedCRM, setSelectedCRM] = useState<string | null>(null);

  const handleBackToList = () => {
    router.push('/dashboard/crm');
  };

  const handleConnectionSuccess = (connection: CRMConnection) => {
    // Navigate to the connection details page
    router.push(`/dashboard/crm/${connection.id}`);
  };

  const handleConnectionError = (error: string) => {
    console.error('Connection error:', error);
    // Error handling is done within the HubSpotConnector component
  };

  const crmOptions = [
    {
      id: 'hubspot',
      name: 'HubSpot',
      description: 'Connect your HubSpot CRM to sync deals and create invoices',
      icon: <Users className="w-8 h-8 text-orange-600" />,
      available: true
    },
    {
      id: 'salesforce',
      name: 'Salesforce',
      description: 'Connect your Salesforce CRM (Coming Soon)',
      icon: <Link2 className="w-8 h-8 text-blue-600" />,
      available: false
    },
    {
      id: 'pipedrive',
      name: 'Pipedrive',
      description: 'Connect your Pipedrive CRM (Coming Soon)',
      icon: <Link2 className="w-8 h-8 text-green-600" />,
      available: false
    }
  ];

  if (selectedCRM === 'hubspot') {
    return (
      <DashboardLayout>
        <PageHeader
          title="Connect HubSpot CRM"
          description="Set up your HubSpot integration to sync deals and generate invoices"
          actions={
            <Button variant="outline" onClick={() => setSelectedCRM(null)}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to CRM Options
            </Button>
          }
        />

        <div className="mt-6">
          <HubSpotConnector
            organizationId={organization?.id || ''}
            onConnectionSuccess={handleConnectionSuccess}
            onConnectionError={handleConnectionError}
            onCancel={() => setSelectedCRM(null)}
          />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <PageHeader
        title="Add CRM Connection"
        description="Choose a CRM system to integrate with your e-invoicing workflow"
        actions={
          <Button variant="outline" onClick={handleBackToList}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to CRM Integrations
          </Button>
        }
      />

      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {crmOptions.map((crm) => (
          <Card
            key={crm.id}
            className={`cursor-pointer transition-all hover:shadow-lg ${
              crm.available 
                ? 'hover:border-blue-300' 
                : 'opacity-60 cursor-not-allowed'
            }`}
            onClick={() => crm.available && setSelectedCRM(crm.id)}
          >
            <CardContent className="p-6">
              <div className="flex items-center mb-4">
                {crm.icon}
                <h3 className="ml-3 text-lg font-semibold text-gray-900">
                  {crm.name}
                </h3>
              </div>
              
              <p className="text-gray-600 text-sm mb-4">
                {crm.description}
              </p>

              {crm.available ? (
                <Button 
                  className="w-full"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedCRM(crm.id);
                  }}
                >
                  Connect {crm.name}
                </Button>
              ) : (
                <Button 
                  className="w-full" 
                  variant="outline" 
                  disabled
                >
                  Coming Soon
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {!selectedCRM && (
        <div className="mt-8">
          <Card>
            <CardHeader 
              title="Need a different CRM?"
              subtitle="We&apos;re constantly adding new integrations"
            />
            <CardContent>
              <p className="text-gray-600 mb-4">
                Don&apos;t see your CRM system listed? We&apos;re working on adding support for more platforms. 
                Contact our support team to request a new integration or learn about our API for custom connections.
              </p>
              <Button variant="outline">
                Request Integration
              </Button>
            </CardContent>
          </Card>
        </div>
      )}
    </DashboardLayout>
  );
};

export default AddCRMConnectionPage;