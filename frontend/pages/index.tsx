import React from 'react';
import Head from 'next/head';
import MetricsDashboard from '../components/dashboard/MetricsDashboard';

const Home: React.FC = () => {
  return (
    <>
      <Head>
        <title>TaxPoynt e-Invoice | Dashboard</title>
        <meta name="description" content="TaxPoynt e-Invoice dashboard for monitoring e-invoicing status and integrations" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <MetricsDashboard />
      </main>
    </>
  );
};

export default Home; 