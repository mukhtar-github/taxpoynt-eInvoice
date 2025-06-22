import { NextPage } from 'next';
import ProtectedRoute from '../../components/auth/ProtectedRoute';
import AppDashboardLayout from '../../components/layouts/AppDashboardLayout';
import ServiceSelectionHub from '../../components/dashboard/ServiceSelectionHub';
import Head from 'next/head';

const ServiceSelectionDashboard: NextPage = () => {

  return (
    <>
      <Head>
        <title>TaxPoynt eInvoice | Service Selection</title>
        <meta name="description" content="Choose between System Integration (SI) and Access Point Provider (APP) services for your e-invoicing needs" />
      </Head>
      <AppDashboardLayout>
        <div className="container mx-auto px-4 py-6">
          <ServiceSelectionHub />
        </div>
      </AppDashboardLayout>
    </>
  );
};

// Wrap the component with the ProtectedRoute component
const ProtectedServiceSelectionDashboard: NextPage = () => {
  return (
    <ProtectedRoute>
      <ServiceSelectionDashboard />
    </ProtectedRoute>
  );
};

export default ProtectedServiceSelectionDashboard;