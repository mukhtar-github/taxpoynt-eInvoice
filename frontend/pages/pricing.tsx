import React, { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { CheckCircleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { CurrencyDollarIcon, ShieldCheckIcon, BuildingOfficeIcon, DevicePhoneMobileIcon } from '@heroicons/react/24/solid';
import MainLayout from '../components/layouts/MainLayout';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';

interface PricingTier {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  limitations?: string[];
  recommended?: boolean;
  cta: string;
  ctaVariant: 'primary' | 'secondary' | 'outline';
}

interface ROIMetrics {
  monthlyInvoices: number;
  averageInvoiceValue: number;
  penaltyRisk: number;
  complianceCost: number;
  timeSavings: number;
}

const Pricing: React.FC = () => {
  const router = useRouter();
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [roiMetrics, setRoiMetrics] = useState<ROIMetrics>({
    monthlyInvoices: 100,
    averageInvoiceValue: 50000,
    penaltyRisk: 1000000,
    complianceCost: 200000,
    timeSavings: 40
  });

  const pricingTiers: PricingTier[] = [
    {
      name: 'Starter',
      price: billingCycle === 'monthly' ? '₦25,000' : '₦250,000',
      period: billingCycle === 'monthly' ? 'per month' : 'per year',
      description: 'Perfect for small businesses starting their FIRS compliance journey',
      features: [
        'Up to 100 invoices per month',
        'Basic FIRS compliance & IRN generation',
        '2 business system integrations (Odoo, QuickBooks)',
        'Digital invoice signing',
        'Email support',
        'FIRS penalty protection',
        'Nigerian bank USSD payment integration',
        'Basic compliance dashboard'
      ],
      limitations: [
        'Limited to 100 invoices/month',
        'No advanced integrations',
        'Standard support only'
      ],
      cta: 'Start Free Trial',
      ctaVariant: 'outline'
    },
    {
      name: 'Business',
      price: billingCycle === 'monthly' ? '₦75,000' : '₦750,000',
      period: billingCycle === 'monthly' ? 'per month' : 'per year',
      description: 'Ideal for growing businesses with complex integration needs',
      features: [
        'Up to 1,000 invoices per month',
        'Complete FIRS certification & compliance',
        '5 business system integrations',
        'CRM integrations (HubSpot, Salesforce)',
        'POS integrations (Square, Toast)',
        'Priority support & onboarding',
        'Advanced analytics dashboard',
        'Multi-currency support',
        'WhatsApp Business notifications',
        'Bulk invoice processing',
        'Nigerian language support (Hausa, Yoruba, Igbo)'
      ],
      recommended: true,
      cta: 'Start Business Trial',
      ctaVariant: 'primary'
    },
    {
      name: 'Enterprise',
      price: billingCycle === 'monthly' ? '₦150,000' : '₦1,500,000',
      period: billingCycle === 'monthly' ? 'per month' : 'per year',
      description: 'Complete solution for large enterprises with advanced requirements',
      features: [
        'Unlimited invoices',
        'All business system integrations',
        'Custom connector development',
        'Dedicated account manager',
        'API access & developer tools',
        'White-label solutions',
        'Advanced security & compliance',
        'Real-time monitoring & alerts',
        'Custom workflow automation',
        'Priority phone & email support',
        'SLA guarantees (99.9% uptime)',
        'Nigerian regulatory consulting'
      ],
      cta: 'Contact Sales',
      ctaVariant: 'secondary'
    },
    {
      name: 'Enterprise+',
      price: 'Custom',
      period: 'pricing',
      description: 'Tailored solutions for large corporations and government agencies',
      features: [
        'Multi-subsidiary support',
        'On-premise deployment options',
        'Custom development & integrations',
        'Advanced compliance reporting',
        'Government-grade security',
        'Dedicated infrastructure',
        '24/7 premium support',
        'Regulatory compliance consulting',
        'Training & certification programs',
        'Disaster recovery & backup',
        'NITDA accreditation support'
      ],
      cta: 'Schedule Consultation',
      ctaVariant: 'outline'
    }
  ];

  const calculateROI = () => {
    const monthlyRevenue = roiMetrics.monthlyInvoices * roiMetrics.averageInvoiceValue;
    const yearlyRevenue = monthlyRevenue * 12;
    const potentialPenalty = roiMetrics.penaltyRisk;
    const complianceCostSavings = roiMetrics.complianceCost * 12;
    const timeSavingsValue = (roiMetrics.timeSavings / 100) * yearlyRevenue * 0.1; // 10% of revenue for time value
    
    const totalSavings = potentialPenalty + complianceCostSavings + timeSavingsValue;
    const platformCost = 75000 * 12; // Business tier yearly cost
    const netROI = totalSavings - platformCost;
    const roiPercentage = ((netROI / platformCost) * 100).toFixed(0);

    return {
      totalSavings,
      platformCost,
      netROI,
      roiPercentage: parseInt(roiPercentage)
    };
  };

  const roi = calculateROI();

  const handleGetStarted = (tierName: string) => {
    if (tierName === 'Enterprise' || tierName === 'Enterprise+') {
      // Redirect to contact/sales page
      router.push('/contact?plan=' + tierName.toLowerCase());
    } else {
      // Redirect to signup with plan selected
      router.push('/auth/signup?plan=' + tierName.toLowerCase());
    }
  };

  return (
    <MainLayout>
      <Head>
        <title>Pricing - TaxPoynt eInvoice | FIRS Compliant Invoice Management</title>
        <meta 
          name="description" 
          content="Choose the perfect TaxPoynt eInvoice plan for your Nigerian business. FIRS compliant e-invoicing with transparent pricing starting at ₦25,000/month." 
        />
        <meta name="keywords" content="FIRS invoice pricing, Nigerian e-invoice cost, business compliance pricing" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-green-50">
        {/* Hero Section */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="text-center">
              <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                Simple, Transparent Pricing
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Choose the perfect plan for your Nigerian business. All plans include FIRS compliance, 
                digital signing, and protection from penalties. Start with a free trial.
              </p>
              
              {/* Billing Toggle */}
              <div className="flex items-center justify-center mb-12">
                <span className={`mr-3 ${billingCycle === 'monthly' ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                  Monthly
                </span>
                <button
                  onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'yearly' : 'monthly')}
                  className="relative inline-flex h-6 w-11 items-center rounded-full bg-gray-200 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      billingCycle === 'yearly' ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
                <span className={`ml-3 ${billingCycle === 'yearly' ? 'text-gray-900 font-medium' : 'text-gray-500'}`}>
                  Yearly
                </span>
                {billingCycle === 'yearly' && (
                  <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-sm font-medium rounded-full">
                    Save 17%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ROI Calculator Section */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <Card className="p-8 mb-16 bg-gradient-to-r from-blue-600 to-green-600 text-white">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-4">FIRS Compliance ROI Calculator</h2>
              <p className="text-blue-100">
                Calculate your potential savings with TaxPoynt eInvoice compliance
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              {/* Calculator Inputs */}
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium mb-2">Monthly Invoices</label>
                  <input
                    type="number"
                    value={roiMetrics.monthlyInvoices}
                    onChange={(e) => setRoiMetrics({...roiMetrics, monthlyInvoices: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-white/20 rounded-md bg-white/10 text-white placeholder-white/60"
                    placeholder="100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Average Invoice Value (₦)</label>
                  <input
                    type="number"
                    value={roiMetrics.averageInvoiceValue}
                    onChange={(e) => setRoiMetrics({...roiMetrics, averageInvoiceValue: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-white/20 rounded-md bg-white/10 text-white placeholder-white/60"
                    placeholder="50,000"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">FIRS Penalty Risk (₦)</label>
                  <input
                    type="number"
                    value={roiMetrics.penaltyRisk}
                    onChange={(e) => setRoiMetrics({...roiMetrics, penaltyRisk: parseInt(e.target.value) || 0})}
                    className="w-full px-3 py-2 border border-white/20 rounded-md bg-white/10 text-white placeholder-white/60"
                    placeholder="1,000,000"
                  />
                </div>
              </div>

              {/* ROI Results */}
              <div className="bg-white/10 rounded-lg p-6">
                <h3 className="text-xl font-bold mb-4">Your Annual Savings</h3>
                <div className="space-y-4">
                  <div className="flex justify-between">
                    <span>Potential FIRS Penalties Avoided:</span>
                    <span className="font-bold">₦{roiMetrics.penaltyRisk.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Manual Compliance Cost Savings:</span>
                    <span className="font-bold">₦{(roiMetrics.complianceCost * 12).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Time Savings Value:</span>
                    <span className="font-bold">₦{((roiMetrics.timeSavings/100) * roiMetrics.monthlyInvoices * roiMetrics.averageInvoiceValue * 12 * 0.1).toLocaleString()}</span>
                  </div>
                  <hr className="border-white/30" />
                  <div className="flex justify-between text-lg font-bold">
                    <span>Total Annual Savings:</span>
                    <span>₦{roi.totalSavings.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>TaxPoynt Annual Cost:</span>
                    <span>₦{roi.platformCost.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-xl font-bold text-yellow-300">
                    <span>Net ROI:</span>
                    <span>{roi.roiPercentage}% (₦{roi.netROI.toLocaleString()})</span>
                  </div>
                </div>
              </div>
            </div>
          </Card>

          {/* Pricing Cards */}
          <div className="grid lg:grid-cols-4 md:grid-cols-2 gap-6 mb-16">
            {pricingTiers.map((tier, index) => (
              <Card
                key={tier.name}
                className={`relative p-6 ${
                  tier.recommended 
                    ? 'ring-2 ring-blue-500 bg-blue-50 border-blue-200' 
                    : 'bg-white border-gray-200'
                } transition-all hover:shadow-lg`}
              >
                {tier.recommended && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Most Popular
                    </span>
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                  <div className="mb-4">
                    <span className="text-3xl font-bold text-gray-900">{tier.price}</span>
                    <span className="text-gray-600 ml-1">/{tier.period}</span>
                  </div>
                  <p className="text-gray-600 text-sm">{tier.description}</p>
                </div>

                <div className="mb-6">
                  <ul className="space-y-3">
                    {tier.features.map((feature, featureIndex) => (
                      <li key={featureIndex} className="flex items-start">
                        <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  
                  {tier.limitations && tier.limitations.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <ul className="space-y-2">
                        {tier.limitations.map((limitation, limitIndex) => (
                          <li key={limitIndex} className="flex items-start">
                            <XMarkIcon className="h-4 w-4 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                            <span className="text-xs text-gray-500">{limitation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <Button
                  variant={tier.ctaVariant}
                  className="w-full"
                  onClick={() => handleGetStarted(tier.name)}
                >
                  {tier.cta}
                </Button>
              </Card>
            ))}
          </div>

          {/* Features Comparison */}
          <Card className="p-8 mb-16">
            <h2 className="text-2xl font-bold text-center mb-8">Feature Comparison</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4">Feature</th>
                    <th className="text-center py-3 px-4">Starter</th>
                    <th className="text-center py-3 px-4">Business</th>
                    <th className="text-center py-3 px-4">Enterprise</th>
                    <th className="text-center py-3 px-4">Enterprise+</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  <tr className="border-b">
                    <td className="py-3 px-4 font-medium">Monthly Invoices</td>
                    <td className="text-center py-3 px-4">100</td>
                    <td className="text-center py-3 px-4">1,000</td>
                    <td className="text-center py-3 px-4">Unlimited</td>
                    <td className="text-center py-3 px-4">Unlimited</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4 font-medium">FIRS Compliance</td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4 font-medium">Business Integrations</td>
                    <td className="text-center py-3 px-4">2</td>
                    <td className="text-center py-3 px-4">5</td>
                    <td className="text-center py-3 px-4">All + Custom</td>
                    <td className="text-center py-3 px-4">All + Custom</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4 font-medium">API Access</td>
                    <td className="text-center py-3 px-4"><XMarkIcon className="h-5 w-5 text-gray-400 mx-auto" /></td>
                    <td className="text-center py-3 px-4">Basic</td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                    <td className="text-center py-3 px-4"><CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" /></td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-3 px-4 font-medium">Support Level</td>
                    <td className="text-center py-3 px-4">Email</td>
                    <td className="text-center py-3 px-4">Priority</td>
                    <td className="text-center py-3 px-4">Phone + Email</td>
                    <td className="text-center py-3 px-4">24/7 Premium</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          {/* Nigerian Benefits Section */}
          <Card className="p-8 mb-16 bg-green-50 border-green-200">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Built for Nigerian Businesses
              </h2>
              <p className="text-gray-600">
                TaxPoynt eInvoice is designed specifically for the Nigerian market with local expertise
              </p>
            </div>

            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <ShieldCheckIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-gray-900 mb-2">FIRS Certified</h3>
                <p className="text-sm text-gray-600">
                  Official FIRS certification with guaranteed compliance
                </p>
              </div>
              <div className="text-center">
                <CurrencyDollarIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-gray-900 mb-2">Naira Pricing</h3>
                <p className="text-sm text-gray-600">
                  Transparent pricing in Nigerian Naira with local payment methods
                </p>
              </div>
              <div className="text-center">
                <BuildingOfficeIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-gray-900 mb-2">Nigerian Banks</h3>
                <p className="text-sm text-gray-600">
                  USSD payment integration with 20+ Nigerian banks
                </p>
              </div>
              <div className="text-center">
                <DevicePhoneMobileIcon className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-gray-900 mb-2">Mobile First</h3>
                <p className="text-sm text-gray-600">
                  Optimized for Nigerian mobile networks and devices
                </p>
              </div>
            </div>
          </Card>

          {/* FAQ Section */}
          <Card className="p-8">
            <h2 className="text-2xl font-bold text-center mb-8">Frequently Asked Questions</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Is there a free trial?</h3>
                <p className="text-gray-600 text-sm mb-4">
                  Yes! All plans include a 14-day free trial with full access to features. No credit card required.
                </p>

                <h3 className="font-bold text-gray-900 mb-2">What happens if I exceed my invoice limit?</h3>
                <p className="text-gray-600 text-sm mb-4">
                  We'll notify you when you're approaching your limit. You can upgrade anytime or pay ₦50 per additional invoice.
                </p>

                <h3 className="font-bold text-gray-900 mb-2">Do you provide FIRS penalty protection?</h3>
                <p className="text-gray-600 text-sm">
                  Yes! All plans include FIRS penalty protection. If you receive a penalty due to our platform error, we'll cover it.
                </p>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">Can I change plans anytime?</h3>
                <p className="text-gray-600 text-sm mb-4">
                  Yes, you can upgrade or downgrade your plan anytime. Changes take effect immediately with prorated billing.
                </p>

                <h3 className="font-bold text-gray-900 mb-2">What payment methods do you accept?</h3>
                <p className="text-gray-600 text-sm mb-4">
                  We accept Nigerian bank transfers, USSD payments, Paystack, Flutterwave, and international credit cards.
                </p>

                <h3 className="font-bold text-gray-900 mb-2">Is my data secure?</h3>
                <p className="text-gray-600 text-sm">
                  Absolutely! We use bank-grade encryption, Nigerian data residency, and are NDPR compliant.
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="bg-gray-900 text-white py-16">
          <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold mb-4">
              Ready to Get FIRS Compliant?
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Join thousands of Nigerian businesses already using TaxPoynt eInvoice for FIRS compliance
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                variant="primary" 
                size="lg"
                onClick={() => router.push('/auth/signup')}
              >
                Start Free Trial
              </Button>
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => router.push('/contact')}
                className="border-white text-white hover:bg-white hover:text-gray-900"
              >
                Schedule Demo
              </Button>
            </div>
            <p className="text-sm text-gray-400 mt-4">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Pricing;