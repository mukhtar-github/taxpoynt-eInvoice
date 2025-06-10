import React from 'react';
import { ShieldCheck } from 'lucide-react';
import Head from 'next/head';

import SignatureManagementDashboard from '../../components/platform/signature/SignatureManagementDashboard';

/**
 * Signature Management Page
 * 
 * APP interface for comprehensive management of 
 * digital signatures, performance monitoring, verification,
 * and configuration.
 */
const SignatureManagementPage: React.FC = () => {
  return (
    <>
      <Head>
        <title>Signature Management | TaxPoynt eInvoice APP</title>
      </Head>
      
      <div className="container py-6 max-w-7xl">
        <div className="flex items-center space-x-2 mb-8">
          <ShieldCheck className="h-6 w-6 text-cyan-600" />
          <h1 className="text-2xl font-bold tracking-tight">Signature Management</h1>
        </div>
        
        <SignatureManagementDashboard />
      </div>
    </>
  );
};

export default SignatureManagementPage;
