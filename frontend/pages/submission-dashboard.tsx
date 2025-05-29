import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { NextPage } from 'next';
import Head from 'next/head';

// This file exists for backward compatibility
// The dashboard has been moved to /dashboard/submission

const SubmissionDashboard: NextPage = () => {
  const router = useRouter();
  
  // Redirect to the new location
  useEffect(() => {
    router.replace('/dashboard/submission');
  }, [router]);

  // Simple loading state while redirecting
  return (
    <>
      <Head>
        <title>Redirecting... | TaxPoynt eInvoice</title>
      </Head>
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-500">Redirecting to submission dashboard...</p>
      </div>
    </>
  );
};

export default SubmissionDashboard;
