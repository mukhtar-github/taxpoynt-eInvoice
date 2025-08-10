/**
 * NDPR Compliance Page
 * ===================
 * 
 * Nigerian Data Protection Regulation (NDPR) compliance information page.
 * Accessible via /legal/ndpr route.
 */
import React from 'react';
import FooterNav from '../FooterNav';

const NDPRCompliancePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NDPR Compliance</h1>
              <p className="text-gray-600">Nigerian Data Protection Regulation Compliance</p>
            </div>
          </div>
        </div>
      </div>

      {/* Breadcrumb */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <nav className="flex" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-4">
              <li>
                <div>
                  <a href="/" className="text-gray-400 hover:text-gray-500">
                    <svg className="flex-shrink-0 h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M10.707 2.293a1 1 0 00-1.414 0l-9 9a1 1 0 001.414 1.414L2 12.414V15a1 1 0 001 1h3a1 1 0 001-1v-3a1 1 0 011-1h2a1 1 0 011 1v3a1 1 0 001 1h3a1 1 0 001-1v-2.586l.293.293a1 1 0 001.414-1.414l-9-9z" />
                    </svg>
                    <span className="sr-only">Home</span>
                  </a>
                </div>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="flex-shrink-0 h-5 w-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
                  </svg>
                  <a href="/legal" className="ml-4 text-sm font-medium text-gray-500 hover:text-gray-700">
                    Legal
                  </a>
                </div>
              </li>
              <li>
                <div className="flex items-center">
                  <svg className="flex-shrink-0 h-5 w-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M5.555 17.776l8-16 .894.448-8 16-.894-.448z" />
                  </svg>
                  <span className="ml-4 text-sm font-medium text-gray-500">NDPR Compliance</span>
                </div>
              </li>
            </ol>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm border p-8">
          
          {/* Introduction */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">NDPR Compliance Overview</h2>
            <p className="text-gray-700 mb-4">
              TaxPoynt is fully compliant with the Nigerian Data Protection Regulation (NDPR) 2019, as administered by the 
              National Information Technology Development Agency (NITDA). We are committed to protecting the personal data 
              of all Nigerian citizens and residents.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center">
                <svg className="w-5 h-5 text-green-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-semibold text-green-800">NDPR Compliant</span>
              </div>
              <p className="text-green-700 mt-2">
                TaxPoynt maintains full compliance with NDPR requirements for data collection, processing, and storage.
              </p>
            </div>
          </div>

          {/* Legal Basis for Processing */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Legal Basis for Data Processing</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">Legitimate Business Interest</h3>
                <p className="text-gray-700">
                  Processing personal data for FIRS e-invoicing compliance, tax reporting, and business record maintenance 
                  as required by Nigerian tax law.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibent text-gray-800 mb-2">Consent</h3>
                <p className="text-gray-700">
                  Explicit consent obtained for financial data access through secure Open Banking integrations and 
                  business system connections.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibent text-gray-800 mb-2">Legal Obligation</h3>
                <p className="text-gray-700">
                  Compliance with FIRS regulations, CBN guidelines, and other Nigerian financial reporting requirements.
                </p>
              </div>
            </div>
          </div>

          {/* Data Subject Rights */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Your Data Protection Rights Under NDPR</h2>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="border-l-4 border-blue-500 pl-4">
                  <h3 className="font-semibold text-gray-800">Right to Access</h3>
                  <p className="text-gray-600 text-sm">Request access to your personal data we hold</p>
                </div>
                <div className="border-l-4 border-green-500 pl-4">
                  <h3 className="font-semibold text-gray-800">Right to Rectification</h3>
                  <p className="text-gray-600 text-sm">Request correction of inaccurate personal data</p>
                </div>
                <div className="border-l-4 border-yellow-500 pl-4">
                  <h3 className="font-semibold text-gray-800">Right to Erasure</h3>
                  <p className="text-gray-600 text-sm">Request deletion of personal data (subject to legal obligations)</p>
                </div>
              </div>
              <div className="space-y-4">
                <div className="border-l-4 border-purple-500 pl-4">
                  <h3 className="font-semibold text-gray-800">Right to Restrict Processing</h3>
                  <p className="text-gray-600 text-sm">Request limitation of data processing activities</p>
                </div>
                <div className="border-l-4 border-red-500 pl-4">
                  <h3 className="font-semibold text-gray-800">Right to Data Portability</h3>
                  <p className="text-gray-600 text-sm">Request transfer of data to another service provider</p>
                </div>
                <div className="border-l-4 border-gray-500 pl-4">
                  <h3 className="font-semibent text-gray-800">Right to Object</h3>
                  <p className="text-gray-600 text-sm">Object to processing based on legitimate interests</p>
                </div>
              </div>
            </div>
          </div>

          {/* Data Protection Measures */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Technical and Organizational Measures</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="bg-blue-50 rounded-lg p-6">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">Encryption</h3>
                <p className="text-gray-600 text-sm">
                  AES-256 encryption for data at rest, TLS 1.3 for data in transit
                </p>
              </div>
              <div className="bg-green-50 rounded-lg p-6">
                <div className="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-gray-800 mb-2">Access Controls</h3>
                <p className="text-gray-600 text-sm">
                  Role-based access control, multi-factor authentication, audit logging
                </p>
              </div>
              <div className="bg-purple-50 rounded-lg p-6">
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <h3 className="font-semibent text-gray-800 mb-2">Data Minimization</h3>
                <p className="text-gray-600 text-sm">
                  Only collect and process data necessary for e-invoicing compliance
                </p>
              </div>
            </div>
          </div>

          {/* Contact Information */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Data Protection Officer Contact</h2>
            <div className="bg-gray-50 rounded-lg p-6">
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibent text-gray-800 mb-2">Data Protection Officer</h3>
                  <p className="text-gray-700">TaxPoynt Data Protection Team</p>
                  <p className="text-gray-600 text-sm mt-2">
                    <strong>Email:</strong> dpo@taxpoynt.com<br/>
                    <strong>Phone:</strong> +234 (0) 1 454 0966<br/>
                    <strong>Address:</strong> Lagos, Nigeria
                  </p>
                </div>
                <div>
                  <h3 className="font-semibent text-gray-800 mb-2">NITDA Registration</h3>
                  <p className="text-gray-700">Registered Data Controller</p>
                  <p className="text-gray-600 text-sm mt-2">
                    <strong>Registration:</strong> Active<br/>
                    <strong>Compliance Status:</strong> Current<br/>
                    <strong>Last Updated:</strong> 2024
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Complaints Process */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Filing a Data Protection Complaint</h2>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibent">1</div>
                <div>
                  <h3 className="font-semibent text-gray-800">Contact Our DPO</h3>
                  <p className="text-gray-600 text-sm">Email dpo@taxpoynt.com with your complaint details</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibent">2</div>
                <div>
                  <h3 className="font-semibent text-gray-800">Investigation</h3>
                  <p className="text-gray-600 text-sm">We will investigate and respond within 30 days</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-semibent">3</div>
                <div>
                  <h3 className="font-semibent text-gray-800">NITDA Escalation</h3>
                  <p className="text-gray-600 text-sm">If unsatisfied, contact NITDA at info@nitda.gov.ng</p>
                </div>
              </div>
            </div>
          </div>

          {/* Retention Policy */}
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Data Retention Policy</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data Type</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retention Period</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Legal Basis</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Invoice Data</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">6 years</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">FIRS requirement</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Financial Records</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">7 years</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">CBN regulation</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">User Account Data</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2 years after closure</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Business records</td>
                  </tr>
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">Audit Logs</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">5 years</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Security requirements</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Updates */}
          <div className="border-t pt-6">
            <p className="text-gray-600 text-sm">
              <strong>Last Updated:</strong> January 2025<br/>
              <strong>Version:</strong> 2.0<br/>
              <strong>Next Review:</strong> January 2026
            </p>
          </div>
        </div>
      </div>

      <FooterNav />
    </div>
  );
};

export default NDPRCompliancePage;