/**
 * Security Banking FAQ Page
 * ========================
 * 
 * Dedicated page route for the Banking Security FAQ component.
 * Accessible via /security/banking-faq route.
 */

import React from 'react';
import BankingSecurityFAQ from '../../business_interface/security_privacy/BankingSecurityFAQ';
import FooterNav from '../FooterNav';

const SecurityBankingFAQPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Breadcrumb */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <nav className="flex items-center space-x-2 text-sm text-gray-600">
            <a href="/" className="hover:text-blue-600">Home</a>
            <span>→</span>
            <a href="/security" className="hover:text-blue-600">Security</a>
            <span>→</span>
            <span className="text-gray-900 font-medium">Banking Security FAQ</span>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="py-8">
        <BankingSecurityFAQ />
      </div>

      {/* Footer */}
      <FooterNav />
    </div>
  );
};

export default SecurityBankingFAQPage;