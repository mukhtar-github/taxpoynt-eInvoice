/**
 * Privacy Policy Page
 * ==================
 * 
 * TaxPoynt Privacy Policy page with NDPR compliance.
 * Accessible via /legal/privacy route.
 */

import React from 'react';
import FooterNav from '../FooterNav';

const PrivacyPolicyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Breadcrumb */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <nav className="flex items-center space-x-2 text-sm text-gray-600">
            <a href="/" className="hover:text-blue-600">Home</a>
            <span>→</span>
            <a href="/legal" className="hover:text-blue-600">Legal</a>
            <span>→</span>
            <span className="text-gray-900 font-medium">Privacy Policy</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
            <p className="text-gray-600">
              Last updated: {new Date().toLocaleDateString()}
            </p>
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <span className="text-green-600">🇳🇬</span>
                <span className="text-sm font-medium text-green-800">
                  This policy complies with the Nigerian Data Protection Regulation (NDPR) 2019
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose max-w-none">
            <h2 className="text-xl font-bold text-gray-900 mb-4">1. Introduction</h2>
            <p className="text-gray-700 mb-6">
              TaxPoynt Technologies Limited ("we," "our," or "us") is committed to protecting your privacy and personal data. 
              This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our 
              e-invoicing platform and system integration services.
            </p>

            <h2 className="text-xl font-bold text-gray-900 mb-4">2. Information We Collect</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">2.1 Business Information</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Company registration details (RC number, business address)</li>
                <li>Tax identification numbers (TIN)</li>
                <li>Business contact information</li>
                <li>Authorized representative details</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">2.2 Transaction Data</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Invoice and payment information</li>
                <li>Customer and supplier data</li>
                <li>Product and service details</li>
                <li>Banking transaction data (when connected via Mono Open Banking)</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">2.3 Technical Information</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>IP addresses and device information</li>
                <li>Usage analytics and platform interactions</li>
                <li>System integration logs</li>
                <li>API access patterns</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">3. How We Use Your Information</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">3.1 Core Services</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Generate FIRS-compliant e-invoices</li>
                <li>Process and transmit data to Federal Inland Revenue Service</li>
                <li>Facilitate system integrations (ERP, CRM, POS, accounting systems)</li>
                <li>Provide Access Point Provider (APP) services</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">3.2 Compliance and Legal</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Comply with Nigerian tax laws and FIRS requirements</li>
                <li>Meet Central Bank of Nigeria (CBN) financial reporting obligations</li>
                <li>Maintain audit trails for regulatory compliance</li>
                <li>Respond to lawful requests from authorities</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">3.3 Service Improvement</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Analyze usage patterns to improve platform performance</li>
                <li>Develop new features and integrations</li>
                <li>Provide customer support and technical assistance</li>
                <li>Send service updates and important notifications</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">4. Banking Data Processing</h2>
            <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Special Notice: Open Banking Integration</h3>
              <p className="text-blue-800 text-sm mb-3">
                When you connect your bank account via Mono Open Banking:
              </p>
              <ul className="list-disc list-inside text-blue-700 text-sm space-y-1">
                <li><strong>We receive:</strong> All transactions from your connected bank account</li>
                <li><strong>We process:</strong> Universal transaction aggregator analyzes all transactions</li>
                <li><strong>We use:</strong> Only business-relevant transactions for invoice generation</li>
                <li><strong>We never store:</strong> Your banking login credentials, passwords, or PINs</li>
                <li><strong>You control:</strong> You can disconnect banking access at any time</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">5. Data Sharing and Disclosure</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">5.1 Required Disclosures</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>FIRS:</strong> E-invoice data and tax compliance information</li>
                <li><strong>CBN:</strong> Financial transaction reporting (when applicable)</li>
                <li><strong>NITDA:</strong> Data protection compliance reporting</li>
                <li><strong>Legal Authorities:</strong> In response to lawful requests</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">5.2 Service Providers</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>Mono Technologies:</strong> Open Banking and financial data access</li>
                <li><strong>Cloud Infrastructure:</strong> Secure data hosting and processing</li>
                <li><strong>System Integration Partners:</strong> ERP, CRM, and POS connectivity</li>
                <li><strong>Technical Support:</strong> Customer service and system maintenance</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">6. Your Rights Under NDPR</h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                As a Nigerian data subject, you have the following rights:
              </p>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>Right to Information:</strong> Know what personal data we collect and how we use it</li>
                <li><strong>Right of Access:</strong> Request a copy of your personal data</li>
                <li><strong>Right to Rectification:</strong> Correct inaccurate or incomplete personal data</li>
                <li><strong>Right to Erasure:</strong> Request deletion of your personal data (subject to legal obligations)</li>
                <li><strong>Right to Restrict Processing:</strong> Limit how we process your personal data</li>
                <li><strong>Right to Data Portability:</strong> Transfer your data to another service provider</li>
                <li><strong>Right to Object:</strong> Object to certain types of processing</li>
                <li><strong>Right to Withdraw Consent:</strong> Withdraw consent for data processing activities</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">7. Data Security</h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                We implement comprehensive security measures to protect your data:
              </p>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>End-to-end encryption for data transmission</li>
                <li>Secure cloud infrastructure with regular security audits</li>
                <li>Access controls and authentication mechanisms</li>
                <li>Regular security training for our personnel</li>
                <li>Incident response and breach notification procedures</li>
                <li>Compliance with international security standards (ISO 27001)</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">8. Data Retention</h2>
            <div className="mb-6">
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>Transaction Data:</strong> 7 years (FIRS audit requirements)</li>
                <li><strong>Customer Data:</strong> Duration of service agreement + 2 years</li>
                <li><strong>Banking Data:</strong> Duration of service agreement + 7 years (FIRS compliance)</li>
                <li><strong>Technical Logs:</strong> 2 years maximum</li>
                <li><strong>Marketing Data:</strong> Until consent is withdrawn</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">9. International Transfers</h2>
            <p className="text-gray-700 mb-6">
              We primarily process data within Nigeria. When international transfers are necessary for service delivery, 
              we ensure adequate safeguards are in place, including contractual protections and compliance with NDPR 
              requirements for cross-border data transfers.
            </p>

            <h2 className="text-xl font-bold text-gray-900 mb-4">10. Contact Information</h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                For privacy-related inquiries, exercising your data rights, or reporting concerns:
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-gray-700"><strong>Data Protection Officer:</strong> privacy@taxpoynt.com</p>
                <p className="text-gray-700"><strong>Nigerian Office:</strong> Lagos, Nigeria</p>
                <p className="text-gray-700"><strong>Support:</strong> 0700-TAXPOYNT</p>
                <p className="text-gray-700"><strong>NITDA Complaints:</strong> You may also contact NITDA for data protection complaints</p>
              </div>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">11. Changes to This Policy</h2>
            <p className="text-gray-700 mb-6">
              We may update this Privacy Policy periodically to reflect changes in our practices or legal requirements. 
              We will notify you of material changes via email or platform notifications and update the "Last updated" 
              date at the top of this policy.
            </p>

            <div className="mt-8 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                <strong>Compliance Note:</strong> This Privacy Policy has been prepared to comply with the Nigerian Data Protection Regulation (NDPR) 2019, 
                the Nigerian Constitution, and other applicable Nigerian privacy laws. For questions about compliance, 
                contact our Data Protection Officer at privacy@taxpoynt.com.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <FooterNav />
    </div>
  );
};

export default PrivacyPolicyPage;