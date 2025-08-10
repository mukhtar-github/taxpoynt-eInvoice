/**
 * Banking Security FAQ Component
 * ==============================
 * 
 * Comprehensive FAQ addressing Nigerian users' concerns about Open Banking
 * and banking data security. Designed for users new to fintech integrations.
 */

import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { ShieldCheckIcon, BanknotesIcon, LockClosedIcon, UserGroupIcon } from '@heroicons/react/24/solid';

interface FAQItem {
  id: string;
  question: string;
  answer: string;
  category: 'security' | 'data' | 'control' | 'legal';
  icon: React.ComponentType<any>;
}

const BankingSecurityFAQ: React.FC = () => {
  const [openItems, setOpenItems] = useState<string[]>([]);

  const toggleItem = (id: string) => {
    setOpenItems(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    );
  };

  const faqItems: FAQItem[] = [
    {
      id: 'banking-details-storage',
      category: 'security',
      icon: LockClosedIcon,
      question: 'What does "Your banking details are never stored by TaxPoynt" mean?',
      answer: `Your banking login details (username, password, PIN) are NEVER sent to TaxPoynt servers. Here's exactly what happens:

1. **You enter bank details directly with Mono** - not with TaxPoynt
2. **Mono connects directly to your bank** - TaxPoynt is not involved in this connection
3. **TaxPoynt only receives transaction summaries** - like "₦50,000 received from ABC Company on Jan 15th"

Think of Mono as a secure messenger between your bank and TaxPoynt. We never see your banking passwords - only the business transaction information needed to generate FIRS-compliant invoices.`
    },
    {
      id: 'mono-safety',
      category: 'legal',
      icon: ShieldCheckIcon,
      question: 'Is Mono safe? What does "CBN licensed" mean?',
      answer: `Yes, Mono is very safe! Here's why:

**CBN License:**
- Mono is licensed by the Central Bank of Nigeria (CBN)
- They meet the same strict security standards as Nigerian banks
- CBN regularly audits and monitors their operations

**Same Technology Used By:**
- PiggyVest, Cowrywise, Carbon, Kuda Bank
- Major Nigerian fintech companies you already trust
- International standards used by banks worldwide

**Additional Safety Measures:**
- Your bank must approve every connection
- Encrypted data transmission (same as online banking)
- You can disconnect anytime through your bank's app`
    },
    {
      id: 'what-taxpoynt-sees',
      category: 'data',
      icon: BanknotesIcon,
      question: 'What exactly does TaxPoynt see from my bank account?',
      answer: `TaxPoynt only sees **business transaction data** needed for e-invoicing:

**✅ What We DO See:**
- All transactions from your connected bank account
- Transaction amounts, dates, descriptions

**❌ What We DON'T See:**
- Your banking login details (username, password, PIN)
- Other bank accounts not connected to TaxPoynt
- Your banking app activity

**🔄 How We Process Your Data:**
- Universal transaction aggregator analyzes all transactions
- System intelligently categorizes business-relevant transactions
- Only business transactions are used for FIRS compliance reporting

**Real Example:**
- We see: "₦100,000 received from XYZ Limited on Jan 20th for consulting services"
- We create: FIRS e-invoice for that business transaction
- We don't see: Your personal ATM withdrawals, family transfers, or other non-business activities`
    },
    {
      id: 'disconnect-control',
      category: 'control',
      icon: UserGroupIcon,
      question: 'Can I disconnect my bank account? How do I control access?',
      answer: `Yes! You have complete control over your banking connection:

**How to Disconnect:**
1. **Through TaxPoynt Dashboard:** Go to Banking Settings → Disconnect Account
2. **Through Mono Dashboard:** Visit mono.co → Login → Revoke TaxPoynt access
3. **Through Your Bank:** Most banks allow you to revoke third-party access

**What Happens When You Disconnect:**
- TaxPoynt loses access to new transactions immediately
- Previous invoices remain valid (FIRS requirement)
- You can reconnect anytime without losing data
- No fees or penalties for disconnecting

**Ongoing Control:**
- View exactly what data TaxPoynt accesses
- Set transaction limits and filters
- Receive notifications for data access
- Download your data anytime`
    },
    {
      id: 'nigerian-regulations',
      category: 'legal',
      icon: ShieldCheckIcon,
      question: 'Are there Nigerian laws protecting my banking data?',
      answer: `Yes! Multiple Nigerian laws protect your banking data:

**CBN Open Banking Framework (2021):**
- Strict rules for accessing banking data
- Banks must verify your identity before sharing data
- Regular security audits for all providers

**Nigeria Data Protection Regulation (NDPR):**
- Your explicit consent required for data access
- Right to know how your data is used
- Right to delete your data anytime

**Banking and Other Financial Institutions Act:**
- Bank secrecy protections apply to Open Banking
- Severe penalties for data misuse
- CBN oversight of all financial data sharing

**Your Rights:**
- Know what data is collected and why
- Control who accesses your data
- Get your data deleted
- Report any misuse to CBN or NITDA`
    },
    {
      id: 'common-concerns',
      category: 'security',
      icon: LockClosedIcon,
      question: 'I\'m worried about hackers. How is my data protected?',
      answer: `Your concerns are valid! Here's how your data is protected:

**Multiple Security Layers:**
1. **Bank-Level Encryption:** Same security as your bank's mobile app
2. **Mono Security:** Military-grade encryption, regular security audits
3. **TaxPoynt Security:** ISO 27001 compliance, encrypted data storage

**What If There's a Breach?**
- Mono notifies you immediately
- Your bank passwords are never at risk (not stored anywhere)
- You can instantly disconnect access
- Insurance coverage for data breaches

**Red Flags to Watch:**
- ❌ Never give banking details to unofficial apps
- ❌ Always verify CBN licensing before connecting
- ❌ Never use platforms that ask for your bank PIN directly
- ✅ TaxPoynt + Mono = CBN approved, bank-verified connection

**Additional Protection:**
- Two-factor authentication on all accounts
- Regular security updates and monitoring
- 24/7 fraud detection systems`
    },
    {
      id: 'alternatives',
      category: 'control',
      icon: UserGroupIcon,
      question: 'What if I don\'t want to connect my bank account?',
      answer: `No problem! TaxPoynt offers multiple ways to use our e-invoicing service:

**Manual Invoice Generation:**
- Upload transaction data via Excel/CSV
- Manual invoice creation through our dashboard
- Integration with accounting software (QuickBooks, Sage, etc.)

**Alternative Data Sources:**
- POS system integration (no banking required)
- ERP system connection (SAP, Oracle, Dynamics)
- API integration for custom solutions

**Hybrid Approach:**
- Connect some accounts, manual input for others
- Use banking for large transactions, manual for small ones
- Gradual adoption - start manual, connect banking later

**No Pressure Policy:**
- Banking connection is always optional
- Full e-invoicing service available without banking
- Same FIRS compliance whether manual or automated
- Upgrade to banking automation anytime`
    }
  ];

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'security': return LockClosedIcon;
      case 'data': return BanknotesIcon;
      case 'control': return UserGroupIcon;
      case 'legal': return ShieldCheckIcon;
      default: return ShieldCheckIcon;
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'security': return 'text-red-600 bg-red-50';
      case 'data': return 'text-blue-600 bg-blue-50';
      case 'control': return 'text-green-600 bg-green-50';
      case 'legal': return 'text-purple-600 bg-purple-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8 text-center">
        <ShieldCheckIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Banking Security FAQ
        </h1>
        <p className="text-lg text-gray-600">
          Everything you need to know about banking data security and Open Banking in Nigeria
        </p>
      </div>

      {/* Trust Badges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-green-50 p-4 rounded-lg text-center">
          <ShieldCheckIcon className="h-8 w-8 text-green-600 mx-auto mb-2" />
          <div className="text-sm font-semibold text-green-800">CBN Licensed</div>
          <div className="text-xs text-green-600">Central Bank Approved</div>
        </div>
        <div className="bg-blue-50 p-4 rounded-lg text-center">
          <LockClosedIcon className="h-8 w-8 text-blue-600 mx-auto mb-2" />
          <div className="text-sm font-semibold text-blue-800">Bank-Grade Security</div>
          <div className="text-xs text-blue-600">Military Encryption</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg text-center">
          <UserGroupIcon className="h-8 w-8 text-purple-600 mx-auto mb-2" />
          <div className="text-sm font-semibold text-purple-800">Your Control</div>
          <div className="text-xs text-purple-600">Disconnect Anytime</div>
        </div>
      </div>

      {/* FAQ Items */}
      <div className="space-y-4">
        {faqItems.map((item) => {
          const isOpen = openItems.includes(item.id);
          const IconComponent = getCategoryIcon(item.category);
          
          return (
            <div key={item.id} className="border border-gray-200 rounded-lg overflow-hidden">
              <button
                className="w-full px-6 py-4 text-left bg-gray-50 hover:bg-gray-100 transition-colors duration-200 flex items-center justify-between"
                onClick={() => toggleItem(item.id)}
              >
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-full ${getCategoryColor(item.category)}`}>
                    <IconComponent className="h-5 w-5" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">
                    {item.question}
                  </h3>
                </div>
                {isOpen ? (
                  <ChevronUpIcon className="h-5 w-5 text-gray-500" />
                ) : (
                  <ChevronDownIcon className="h-5 w-5 text-gray-500" />
                )}
              </button>
              
              {isOpen && (
                <div className="px-6 py-4 bg-white">
                  <div className="text-gray-700 whitespace-pre-line leading-relaxed">
                    {item.answer}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Contact Support */}
      <div className="mt-8 p-6 bg-blue-50 rounded-lg">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Still Have Questions?
        </h3>
        <p className="text-blue-700 mb-4">
          Our customer support team is here to help you understand banking security and Open Banking.
        </p>
        <div className="flex flex-col sm:flex-row gap-3">
          <button className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Chat with Support
          </button>
          <button className="border border-blue-600 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-600 hover:text-white transition-colors">
            Schedule a Call
          </button>
          <a 
            href="mailto:support@taxpoynt.com" 
            className="border border-blue-600 text-blue-600 px-4 py-2 rounded-lg hover:bg-blue-600 hover:text-white transition-colors text-center"
          >
            Email Us
          </a>
        </div>
      </div>
    </div>
  );
};

export default BankingSecurityFAQ;