/**
 * TaxPoynt Billing Management Page
 * ===============================
 * Strategic billing interface with full-page navigation (not modal/embedded).
 * Professional financial operations interface following Steve Jobs' principles.
 * 
 * User Flow: Package Selection → Billing Page (Full Navigation)
 */

import React, { useState } from 'react';
import { Button } from '../../design_system/components/Button';
import { colors } from '../../design_system/tokens';

interface BillingPageProps {
  selectedPackage: {
    id: string;
    name: string;
    price: { monthly: number; annual: number };
    features: string[];
  };
  currentRole: 'si' | 'app' | 'hybrid' | 'admin';
  userProfile: {
    companyName: string;
    email: string;
    phone: string;
  };
  onPaymentComplete: (paymentData: any) => void;
  onCancel: () => void;
}

interface PaymentMethod {
  id: string;
  type: 'card' | 'bank_transfer' | 'ussd';
  name: string;
  description: string;
  icon: string;
  processingTime: string;
}

const paymentMethods: PaymentMethod[] = [
  {
    id: 'card',
    type: 'card',
    name: 'Debit/Credit Card',
    description: 'Instant payment via Visa, Mastercard, or Verve',
    icon: '💳',
    processingTime: 'Instant'
  },
  {
    id: 'bank_transfer',
    type: 'bank_transfer',
    name: 'Bank Transfer',
    description: 'Direct transfer to TaxPoynt account',
    icon: '🏦',
    processingTime: '1-3 business days'
  },
  {
    id: 'ussd',
    type: 'ussd',
    name: 'USSD Payment',
    description: 'Pay with your mobile phone (*737#, *901#, etc.)',
    icon: '📱',
    processingTime: 'Instant'
  }
];

export const BillingPage: React.FC<BillingPageProps> = ({
  selectedPackage,
  currentRole,
  userProfile,
  onPaymentComplete,
  onCancel
}) => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>('card');
  const [isProcessing, setIsProcessing] = useState(false);
  const [acceptedTerms, setAcceptedTerms] = useState(false);

  const price = selectedPackage.price[billingCycle];
  const savings = billingCycle === 'annual' 
    ? selectedPackage.price.monthly * 12 - selectedPackage.price.annual 
    : 0;

  const formatPrice = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount);
  };

  const handlePayment = async () => {
    if (!acceptedTerms) {
      alert('Please accept the terms and conditions to proceed.');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Strategic payment processing would go here
      // Integration with Nigerian payment processors (Paystack, etc.)
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing
      
      onPaymentComplete({
        packageId: selectedPackage.id,
        billingCycle,
        paymentMethod: selectedPaymentMethod,
        amount: price,
        currency: 'NGN'
      });
    } catch (error) {
      console.error('Payment failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Strategic Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Complete Your Subscription</h1>
              <p className="text-gray-600 mt-2">Secure billing for {userProfile.companyName}</p>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Order Summary - Left Column */}
          <div className="bg-white rounded-2xl border border-gray-200 p-8 h-fit">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Order Summary</h2>
            
            {/* Package Details */}
            <div className="border rounded-xl p-6 mb-6 bg-gray-50">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{selectedPackage.name}</h3>
                  <p className="text-gray-600">TaxPoynt eInvoice Platform</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">
                    {formatPrice(price)}
                  </div>
                  <div className="text-sm text-gray-500">
                    /{billingCycle === 'monthly' ? 'month' : 'year'}
                  </div>
                </div>
              </div>

              {/* Billing Cycle Toggle */}
              <div className="flex items-center justify-center py-4 border-t border-gray-200">
                <span className={`mr-3 text-sm ${billingCycle === 'monthly' ? 'font-semibold' : 'text-gray-500'}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
                  className={`
                    relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                    ${billingCycle === 'annual' ? 'bg-blue-600' : 'bg-gray-200'}
                  `}
                >
                  <span
                    className={`
                      inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                      ${billingCycle === 'annual' ? 'translate-x-6' : 'translate-x-1'}
                    `}
                  />
                </button>
                <span className={`ml-3 text-sm ${billingCycle === 'annual' ? 'font-semibold' : 'text-gray-500'}`}>
                  Annual
                </span>
                {billingCycle === 'annual' && (
                  <span className="ml-2 px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                    Save {formatPrice(savings)}
                  </span>
                )}
              </div>
            </div>

            {/* Key Features */}
            <div className="mb-6">
              <h4 className="font-semibold text-gray-900 mb-3">What's Included</h4>
              <ul className="space-y-2">
                {selectedPackage.features.slice(0, 5).map((feature, index) => (
                  <li key={index} className="flex items-start text-sm">
                    <svg
                      className="h-4 w-4 text-green-500 mr-2 mt-0.5 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Total */}
            <div className="border-t pt-6">
              <div className="flex justify-between items-center text-xl font-bold">
                <span>Total</span>
                <span className="text-blue-600">{formatPrice(price)}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                {billingCycle === 'annual' ? 'Billed annually' : 'Billed monthly'} • Nigerian Naira (NGN)
              </p>
            </div>
          </div>

          {/* Payment Form - Right Column */}
          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Payment Information</h2>

            {/* Company Information */}
            <div className="mb-6 p-4 bg-gray-50 rounded-xl">
              <h3 className="font-semibold text-gray-900 mb-2">Billing To</h3>
              <div className="text-sm text-gray-600 space-y-1">
                <div>{userProfile.companyName}</div>
                <div>{userProfile.email}</div>
                <div>{userProfile.phone}</div>
              </div>
            </div>

            {/* Payment Method Selection */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-4">Payment Method</h3>
              <div className="space-y-3">
                {paymentMethods.map((method) => (
                  <label key={method.id} className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="paymentMethod"
                      value={method.id}
                      checked={selectedPaymentMethod === method.id}
                      onChange={(e) => setSelectedPaymentMethod(e.target.value)}
                      className="h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                    />
                    <div className="ml-3 flex-1">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className="text-lg mr-2">{method.icon}</span>
                          <span className="font-medium text-gray-900">{method.name}</span>
                        </div>
                        <span className="text-xs text-green-600 font-medium">{method.processingTime}</span>
                      </div>
                      <p className="text-sm text-gray-600 ml-7">{method.description}</p>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Security Notice */}
            <div className="mb-6 p-4 bg-blue-50 rounded-xl border border-blue-200">
              <div className="flex items-start">
                <svg className="h-5 w-5 text-blue-600 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                <div>
                  <h4 className="font-medium text-blue-900">Secure Payment</h4>
                  <p className="text-sm text-blue-700">Your payment information is encrypted and protected with bank-level security.</p>
                </div>
              </div>
            </div>

            {/* Terms and Conditions */}
            <div className="mb-6">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={acceptedTerms}
                  onChange={(e) => setAcceptedTerms(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-0.5"
                />
                <span className="ml-2 text-sm text-gray-600">
                  I agree to the{' '}
                  <a href="/terms" className="text-blue-600 hover:text-blue-700 underline">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="/privacy" className="text-blue-600 hover:text-blue-700 underline">
                    Privacy Policy
                  </a>
                </span>
              </label>
            </div>

            {/* Payment Button */}
            <Button
              variant="primary"
              size="lg"
              role={currentRole}
              loading={isProcessing}
              disabled={!acceptedTerms}
              onClick={handlePayment}
              className="w-full"
            >
              {isProcessing ? 'Processing Payment...' : `Pay ${formatPrice(price)}`}
            </Button>

            {/* Security Badges */}
            <div className="mt-6 flex items-center justify-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center">
                <svg className="h-4 w-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
                SSL Secured
              </div>
              <div>256-bit Encryption</div>
              <div>PCI Compliant</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};