/**
 * Banking Security Information Page
 * ================================
 * 
 * Dedicated page explaining banking security and data handling for Nigerian users.
 * Critical for building trust with users new to Open Banking concepts.
 * 
 * Key Purpose: Address common concerns about banking data security
 * Target Audience: Nigerian business owners unfamiliar with Open Banking
 */

import React from 'react';
import { Button } from '../../design_system/components/Button';

export const BankingSecurityPage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="text-center mb-12">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
          <span className="text-3xl">🔒</span>
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          How TaxPoynt Protects Your Banking Information
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Your banking security is our top priority. Here's exactly how we protect your information 
          and what we can and cannot see.
        </p>
      </div>

      {/* Key Promise */}
      <div className="bg-green-50 border-2 border-green-200 rounded-xl p-8 mb-12">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-green-900 mb-4">
            🇳🇬 Our Promise to Nigerian Businesses
          </h2>
          <p className="text-lg text-green-800 mb-6">
            <strong>TaxPoynt NEVER sees your banking passwords, PINs, or login details.</strong><br/>
            We only receive business transaction data to help you comply with FIRS e-invoicing requirements.
          </p>
          <div className="bg-white border border-green-300 rounded-lg p-4">
            <p className="text-green-900 font-medium">
              ✅ Licensed by CBN • ✅ NDPR Compliant • ✅ Bank-Grade Security
            </p>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
          How Banking Integration Actually Works
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Step 1 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🏦</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              1. You Connect to Your Bank
            </h3>
            <p className="text-gray-600">
              You enter your banking details directly with <strong>Mono</strong> (not TaxPoynt). 
              Mono is licensed by the Central Bank of Nigeria.
            </p>
          </div>

          {/* Step 2 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">🔗</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              2. Mono Securely Connects
            </h3>
            <p className="text-gray-600">
              Mono connects to your bank using the same security standards as your bank's mobile app. 
              <strong>Your login details stay with your bank.</strong>
            </p>
          </div>

          {/* Step 3 */}
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-2xl">📊</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">
              3. TaxPoynt Gets Business Data
            </h3>
            <p className="text-gray-600">
              We only receive your <strong>business transaction information</strong> to automatically 
              generate FIRS-compliant e-invoices.
            </p>
          </div>
        </div>
      </div>

      {/* What We See vs Don't See */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
        {/* What We DON'T See */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-red-900 mb-4 flex items-center">
            <span className="mr-2">❌</span>
            What TaxPoynt NEVER Sees
          </h3>
          <ul className="space-y-2 text-red-800">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Your banking username or password
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Your banking PIN or security questions
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Access to withdraw or move your money
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Your bank account login credentials
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Access to withdraw or move your money
            </li>
          </ul>
        </div>

        {/* What We DO See */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-green-900 mb-4 flex items-center">
            <span className="mr-2">✅</span>
            What TaxPoynt DOES See
          </h3>
          <ul className="space-y-2 text-green-800">
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Business payments received (amounts & dates)
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Customer names (for invoice generation)
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Transaction descriptions for business sales
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Account balance (to verify transactions)
            </li>
            <li className="flex items-start">
              <span className="mr-2">•</span>
              Business account holder name
            </li>
          </ul>
        </div>
      </div>

      {/* Real Example */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-8 mb-12">
        <h3 className="text-xl font-bold text-blue-900 mb-4 text-center">
          📝 Real Example: What Happens When You Get Paid
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">Your Bank Account</h4>
            <p className="text-sm text-blue-800">
              "ABC Company paid you ₦150,000 on January 15th for services"
            </p>
          </div>
          
          <div className="flex items-center justify-center">
            <span className="text-blue-600 text-2xl">→</span>
          </div>
          
          <div className="bg-white rounded-lg p-4 border border-blue-200">
            <h4 className="font-semibold text-blue-900 mb-2">TaxPoynt Receives</h4>
            <p className="text-sm text-blue-800">
              "₦150,000 from ABC Company on Jan 15th" → Automatically creates FIRS e-invoice
            </p>
          </div>
        </div>
        
        <p className="text-center text-blue-700 mt-4 text-sm">
          <strong>We never see:</strong> Your password, PIN, or how you accessed your account
        </p>
      </div>

      {/* Regulatory Compliance */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          🏛️ Nigerian Regulatory Compliance
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-3xl mb-3">🇳🇬</div>
            <h3 className="font-semibold text-gray-900 mb-2">Central Bank of Nigeria (CBN)</h3>
            <p className="text-sm text-gray-600">
              Mono is licensed by CBN under the Open Banking framework. 
              Same security standards as your bank.
            </p>
          </div>
          
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-3xl mb-3">🔐</div>
            <h3 className="font-semibold text-gray-900 mb-2">NDPR Compliance</h3>
            <p className="text-sm text-gray-600">
              Full compliance with Nigerian Data Protection Regulation. 
              Your data rights are protected.
            </p>
          </div>
          
          <div className="text-center p-6 border border-gray-200 rounded-lg">
            <div className="text-3xl mb-3">📋</div>
            <h3 className="font-semibold text-gray-900 mb-2">FIRS Requirements</h3>
            <p className="text-sm text-gray-600">
              We only collect data necessary for FIRS e-invoicing compliance. 
              Nothing more.
            </p>
          </div>
        </div>
      </div>

      {/* Your Control */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6 text-center">
          🎛️ You Have Complete Control
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">You Can Always:</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                Disconnect your bank account anytime
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                View exactly what data we access
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                Control which transactions generate invoices
              </li>
              <li className="flex items-start">
                <span className="text-green-600 mr-2">✓</span>
                Request deletion of your data
              </li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold text-gray-900 mb-3">How to Disconnect:</h3>
            <ul className="space-y-2 text-gray-700">
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">1.</span>
                Go to your TaxPoynt Banking Settings
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">2.</span>
                Click "Disconnect Bank Account"
              </li>
              <li className="flex items-start">
                <span className="text-blue-600 mr-2">3.</span>
                Or revoke access through your bank's app
              </li>
            </ul>
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="mb-12">
        <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
          ❓ Common Questions from Nigerian Businesses
        </h2>
        
        <div className="space-y-6">
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-2">
              "Can TaxPoynt steal money from my account?"
            </h3>
            <p className="text-gray-700">
              <strong>No.</strong> We only have "read-only" access through Mono. We cannot withdraw, 
              transfer, or move money from your account. We can only see transaction information.
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-2">
              "What if Mono gets hacked?"
            </h3>
            <p className="text-gray-700">
              Mono uses the same security standards as banks (256-bit encryption, multi-factor authentication). 
              Your banking passwords are never stored - they connect directly to your bank each time.
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-2">
              "Can I use TaxPoynt without connecting my bank?"
            </h3>
            <p className="text-gray-700">
              <strong>Yes!</strong> Banking integration is completely optional. You can use TaxPoynt 
              for e-invoicing by manually entering transaction data or connecting other business systems.
            </p>
          </div>
          
          <div className="border border-gray-200 rounded-lg p-6">
            <h3 className="font-semibold text-gray-900 mb-2">
              "Which Nigerian banks work with this?"
            </h3>
            <p className="text-gray-700">
              Most major Nigerian banks: GTBank, Access, Zenith, First Bank, UBA, Fidelity, 
              Union Bank, Wema, Sterling, and many others. Full list available during setup.
            </p>
          </div>
        </div>
      </div>

      {/* Contact */}
      <div className="text-center bg-blue-50 border border-blue-200 rounded-lg p-8">
        <h2 className="text-xl font-bold text-blue-900 mb-4">
          Still Have Questions?
        </h2>
        <p className="text-blue-800 mb-6">
          Our Nigerian support team is here to help you understand exactly how your data is protected.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <Button variant="primary">
            📞 Call Nigerian Support: 0700-TAXPOYNT
          </Button>
          <Button variant="outline">
            📧 Email: security@taxpoynt.ng
          </Button>
        </div>
        <p className="text-sm text-blue-700 mt-4">
          Available: Monday-Friday, 8AM-6PM WAT
        </p>
      </div>
    </div>
  );
};

export default BankingSecurityPage;