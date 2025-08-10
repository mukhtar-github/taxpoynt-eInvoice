/**
 * Terms of Service Page
 * ====================
 * 
 * TaxPoynt Terms of Service page with Nigerian legal compliance.
 * Accessible via /legal/terms route.
 */

import React from 'react';
import FooterNav from '../FooterNav';

const TermsOfServicePage: React.FC = () => {
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
            <span className="text-gray-900 font-medium">Terms of Service</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg border border-gray-200 p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
            <p className="text-gray-600">
              Last updated: {new Date().toLocaleDateString()}
            </p>
            <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-2">
                <span className="text-blue-600">🇳🇬</span>
                <span className="text-sm font-medium text-blue-800">
                  These terms are governed by Nigerian law and FIRS e-invoicing regulations
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="prose max-w-none">
            <h2 className="text-xl font-bold text-gray-900 mb-4">1. Agreement to Terms</h2>
            <p className="text-gray-700 mb-6">
              By accessing or using TaxPoynt's e-invoicing platform and system integration services ("Services"), 
              you agree to be bound by these Terms of Service ("Terms"). If you do not agree to these Terms, 
              you may not access or use our Services.
            </p>

            <h2 className="text-xl font-bold text-gray-900 mb-4">2. Company Information</h2>
            <div className="mb-6 bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-gray-700">
                <strong>TaxPoynt Technologies Limited</strong><br/>
                Nigerian Company Registration: [RC Number]<br/>
                Registered Office: Lagos, Nigeria<br/>
                FIRS-Certified Access Point Provider (APP)<br/>
                Contact: legal@taxpoynt.com
              </p>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">3. Service Description</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">3.1 Core Services</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>System Integration (SI):</strong> Connect ERP, CRM, POS, accounting, and e-commerce systems</li>
                <li><strong>Access Point Provider (APP):</strong> FIRS-certified e-invoicing services</li>
                <li><strong>Nigerian Compliance:</strong> Tax law compliance and regulatory reporting</li>
                <li><strong>Financial System Integration:</strong> Banking and payment processor connections</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">3.2 TaxPoynt Role</h3>
              <p className="text-gray-700 mb-4">
                <strong>Important:</strong> TaxPoynt is NOT a payment processor. We are a data collector and invoice generator 
                for FIRS compliance purposes. As an Access Point Provider (APP), we are responsible for FIRS compliance 
                on behalf of our users.
              </p>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">4. User Eligibility and Registration</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">4.1 Eligibility</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Must be a registered Nigerian business with valid RC number</li>
                <li>Must have authority to bind your organization to these Terms</li>
                <li>Must comply with Nigerian tax laws and FIRS requirements</li>
                <li>Must provide accurate and complete registration information</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">4.2 Account Responsibilities</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Maintain confidentiality of account credentials</li>
                <li>Notify us immediately of unauthorized access</li>
                <li>Ensure all account information remains current and accurate</li>
                <li>Accept responsibility for all activities under your account</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">5. Data Processing and Banking Integration</h2>
            <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">5.1 Transaction Data Processing</h3>
              <p className="text-yellow-800 text-sm mb-3">
                <strong>By using our Services, you acknowledge and agree that:</strong>
              </p>
              <ul className="list-disc list-inside text-yellow-700 text-sm space-y-1">
                <li>When you connect banking via Mono, we receive ALL transactions from connected accounts</li>
                <li>Our universal transaction aggregator processes all transaction data</li>
                <li>We intelligently categorize transactions for business invoice generation</li>
                <li>We never store your banking login credentials or passwords</li>
                <li>You can disconnect banking integration at any time</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">6. FIRS Compliance and Regulatory Obligations</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">6.1 Our Obligations as APP</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Ensure all e-invoices meet FIRS technical specifications</li>
                <li>Transmit invoice data securely to FIRS systems</li>
                <li>Maintain audit trails for regulatory compliance</li>
                <li>Provide compliance reporting and documentation</li>
                <li>Update systems to reflect changes in FIRS requirements</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">6.2 Your Obligations</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Provide accurate and complete transaction data</li>
                <li>Maintain proper business records and documentation</li>
                <li>Comply with Nigerian tax laws and regulations</li>
                <li>Respond promptly to FIRS inquiries related to generated invoices</li>
                <li>Notify us of any changes to your business registration or tax status</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">7. System Integration and Third-Party Services</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibent text-gray-800 mb-2">7.1 Supported Integrations</h3>
              <p className="text-gray-700 mb-4">
                We integrate with various business and financial systems including but not limited to:
              </p>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li><strong>ERP Systems:</strong> SAP, Oracle, Microsoft Dynamics, NetSuite, Odoo</li>
                <li><strong>CRM Systems:</strong> Salesforce, HubSpot, Pipedrive, Zoho</li>
                <li><strong>POS Systems:</strong> Square, Clover, Lightspeed, OPay POS, Moniepoint POS, PalmPay POS, Quickteller POS</li>
                <li><strong>E-commerce:</strong> Shopify, WooCommerce, Magento, Jumia, Konga, Jiji, PayPorte</li>
                <li><strong>Accounting:</strong> QuickBooks, Xero, Sage, Wave, FreshBooks</li>
                <li><strong>Payment Processors:</strong> Paystack, Moniepoint, OPay, PalmPay, Interswitch, Flutterwave, Stripe</li>
                <li><strong>Banking:</strong> Mono Open Banking (CBN-licensed)</li>
                <li><strong>Inventory:</strong> TradeGecko, Fishbowl, Cin7, Unleashed, Zoho Inventory</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">7.2 Third-Party Dependencies</h3>
              <p className="text-gray-700 mb-4">
                Our Services depend on third-party systems and APIs. We are not responsible for:
              </p>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Downtime or failures of third-party systems</li>
                <li>Changes to third-party APIs or terms of service</li>
                <li>Data security within third-party systems</li>
                <li>Integration compatibility changes by third-party providers</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">8. Service Availability and Performance</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">8.1 Service Level Commitment</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>We strive for 99.5% uptime for core e-invoicing services</li>
                <li>Scheduled maintenance will be announced 48 hours in advance</li>
                <li>Critical FIRS-related services have priority in our incident response</li>
                <li>We maintain backup systems for business continuity</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">8.2 Service Limitations</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Services may be unavailable during system maintenance</li>
                <li>Performance may be affected during peak usage periods</li>
                <li>Integration speed depends on third-party system response times</li>
                <li>New feature rollouts may temporarily affect system performance</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">9. Fees and Payment Terms</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">9.1 Service Fees</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Fees are based on your selected service package and usage</li>
                <li>Pricing is available on our website and in your service agreement</li>
                <li>Fees are payable in Nigerian Naira unless otherwise agreed</li>
                <li>All fees are exclusive of applicable taxes (VAT, etc.)</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">9.2 Payment Terms</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Subscription fees are payable monthly or annually in advance</li>
                <li>Usage-based fees are billed monthly in arrears</li>
                <li>Payment is due within 30 days of invoice date</li>
                <li>Late payments may result in service suspension</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">10. Intellectual Property Rights</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">10.1 TaxPoynt IP</h3>
              <p className="text-gray-700 mb-4">
                The TaxPoynt platform, including software, algorithms, user interfaces, and documentation, 
                is owned by TaxPoynt Technologies Limited and protected by Nigerian and international 
                intellectual property laws.
              </p>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">10.2 Your Data</h3>
              <p className="text-gray-700 mb-4">
                You retain ownership of your business data. By using our Services, you grant us a license 
                to process, store, and transmit your data as necessary to provide our Services and comply 
                with FIRS requirements.
              </p>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">11. Limitation of Liability</h2>
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm mb-3">
                <strong>Important Liability Limitations:</strong>
              </p>
              <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
                <li>Our liability is limited to the fees paid by you in the 12 months preceding the claim</li>
                <li>We are not liable for indirect, consequential, or punitive damages</li>
                <li>We are not liable for losses caused by third-party system failures</li>
                <li>Business disruption claims are limited to direct service fees only</li>
                <li>Tax penalties or fines resulting from your data inaccuracies are your responsibility</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">12. Termination</h2>
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-2">12.1 Termination by You</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>You may terminate with 30 days written notice</li>
                <li>Prepaid fees are non-refundable except as required by law</li>
                <li>You remain responsible for completing FIRS compliance obligations</li>
                <li>Data export must be completed before account closure</li>
              </ul>

              <h3 className="text-lg font-semibold text-gray-800 mb-2">12.2 Termination by Us</h3>
              <ul className="list-disc list-inside text-gray-700 mb-4 space-y-1">
                <li>Immediate termination for material breach of Terms</li>
                <li>30 days notice for non-payment of fees</li>
                <li>Immediate termination for illegal activities or FIRS non-compliance</li>
                <li>We will provide reasonable assistance for data migration</li>
              </ul>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">13. Governing Law and Dispute Resolution</h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                These Terms are governed by the laws of the Federal Republic of Nigeria. Any disputes arising 
                from these Terms shall be resolved through:
              </p>
              <ol className="list-decimal list-inside text-gray-700 mb-4 space-y-1">
                <li>Good faith negotiation between the parties</li>
                <li>Mediation through the Lagos Chamber of Commerce</li>
                <li>Arbitration under Nigerian Arbitration and Conciliation Act</li>
                <li>Courts of competent jurisdiction in Lagos State, Nigeria</li>
              </ol>
            </div>

            <h2 className="text-xl font-bold text-gray-900 mb-4">14. Contact Information</h2>
            <div className="mb-6">
              <p className="text-gray-700 mb-4">
                For questions about these Terms or our Services:
              </p>
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <p className="text-gray-700"><strong>Legal Department:</strong> legal@taxpoynt.com</p>
                <p className="text-gray-700"><strong>Customer Support:</strong> 0700-TAXPOYNT</p>
                <p className="text-gray-700"><strong>Business Address:</strong> Lagos, Nigeria</p>
                <p className="text-gray-700"><strong>FIRS Compliance:</strong> compliance@taxpoynt.com</p>
              </div>
            </div>

            <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Legal Notice:</strong> These Terms of Service constitute the entire agreement between you and 
                TaxPoynt Technologies Limited regarding your use of our Services. They supersede all prior agreements 
                and understandings. By continuing to use our Services, you acknowledge that you have read, understood, 
                and agree to be bound by these Terms.
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

export default TermsOfServicePage;