import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '@/hooks/useAuth';
import Head from 'next/head';
import SecureTransmissionManager from '@/components/platform/transmission/SecureTransmissionManager';
import NewTransmission from '@/components/platform/transmission/NewTransmission';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Shield, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface Certificate {
  id: string;
  name: string;
  status: string;
  type: string;
  expiry_date: string;
}

const FIRSTransmissionPage: React.FC = () => {
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<string>('manage');
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If auth is loaded and user is not authenticated, redirect to login
    if (!authLoading && !user) {
      router.push('/login?redirect=firs-transmission');
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      fetchCertificates();
    }
  }, [user]);

  const fetchCertificates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`/api/v1/certificates?organization_id=${user?.organization_id}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setCertificates(response.data.filter((cert: Certificate) => 
        cert.status === 'active' && cert.type.includes('signing')
      ));
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to fetch certificates';
        setError(errorMsg);
      } else {
        setError('An unexpected error occurred while fetching certificates');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleTransmissionCreated = () => {
    setActiveTab('manage');
  };

  if (authLoading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>;
  }

  if (!user) {
    return null; // Will redirect to login via useEffect
  }

  return (
    <>
      <Head>
        <title>FIRS Secure Transmission | TaxPoynt eInvoice</title>
        <meta name="description" content="Manage secure transmissions to FIRS" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8 border-b pb-4">
          <h1 className="text-3xl font-bold">FIRS Secure Transmission</h1>
          <p className="text-gray-500">
            Securely transmit invoices and documents to FIRS with encryption and digital signatures
          </p>
        </div>

        {error && (
          <Alert variant="error" className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-8">
            <TabsTrigger value="manage">
              Manage Transmissions
            </TabsTrigger>
            <TabsTrigger value="new">
              New Transmission
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="manage" className="mt-0">
            {user && (
              <SecureTransmissionManager organizationId={user.organization_id} />
            )}
          </TabsContent>
          
          <TabsContent value="new" className="mt-0">
            {user && (
              <NewTransmission 
                organizationId={user.organization_id}
                certificates={certificates}
                onTransmissionCreated={handleTransmissionCreated}
              />
            )}
          </TabsContent>
        </Tabs>
        
        <Card className="mt-8 bg-gray-50">
          <CardHeader>
            <div className="flex items-center">
              <Shield className="w-5 h-5 mr-2 text-cyan-500" />
              <CardTitle className="text-lg">About Secure Transmission</CardTitle>
            </div>
            <CardDescription>
              Understanding the secure transmission process
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4 text-sm">
              <p>
                <strong>Secure Transmission</strong> ensures that your sensitive invoice data is safely
                delivered to FIRS using industry-standard encryption and digital signature technologies:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>
                  <strong>RSA-OAEP with AES-256-GCM Encryption:</strong> Your data is encrypted using
                  a hybrid approach that combines the security of RSA public-key encryption with the
                  performance of AES symmetric encryption.
                </li>
                <li>
                  <strong>Digital Signatures:</strong> Optional digital signing of payloads using your
                  organization's certificates ensures non-repudiation and data integrity.
                </li>
                <li>
                  <strong>Automated Retry:</strong> Failed transmissions are automatically retried with
                  exponential backoff to ensure delivery even in unstable network conditions.
                </li>
                <li>
                  <strong>Transmission Receipts:</strong> Each successful transmission generates a
                  receipt that serves as proof of submission to FIRS.
                </li>
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  );
};

export default FIRSTransmissionPage;
