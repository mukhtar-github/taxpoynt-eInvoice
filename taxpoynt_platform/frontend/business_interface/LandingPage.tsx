/**
 * TaxPoynt Strategic Landing Page
 * ==============================
 * Simple but sophisticated landing page following Steve Jobs' principles.
 * Focuses on clear value proposition and strategic CTAs.
 * 
 * "Simplicity is the ultimate sophistication" - Steve Jobs
 */

import React from 'react';
import { useRouter } from 'next/router';
import { Button } from './design_system/components/Button';
import { colors } from './design_system/tokens';

export const LandingPage: React.FC = () => {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-white">
      
      {/* Navigation */}
      <nav className="px-6 py-4 border-b border-gray-200">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">T</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">TaxPoynt</h1>
              <p className="text-xs text-gray-500">E-Invoice Platform</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/auth/signin')}
              className="text-gray-600 hover:text-gray-900 font-medium"
            >
              Sign In
            </button>
            <Button
              variant="primary"
              onClick={() => router.push('/auth/signup')}
            >
              Get Started
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          
          {/* Badge */}
          <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium mb-8">
            <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            FIRS Certified Access Point Provider
          </div>

          {/* Headline with Prominent Tagline */}
          <div className="mb-8">
            <div className="inline-block bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2 rounded-full text-sm font-semibold mb-6">
              Nigeria's Premier Intelligent Universal E-Invoicing Platform
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 leading-tight">
              Connect Every System.
              <br />
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Automate Every Transaction.
              </span>
            </h1>
          </div>

          {/* Subtitle */}
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            Advanced technology that understands Nigerian business reality. Universal connectivity from SAP to Paystack. 
            From Lagos to Kano, from Computer Village to Alaba Market - built for how Nigeria actually works.
          </p>

          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
            <Button
              variant="primary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-lg px-8 py-4"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => {
                document.getElementById('services')?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="text-lg px-8 py-4"
            >
              Learn More
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600 mb-1">85%+</div>
              <div className="text-gray-600 text-sm">Transaction Classification Accuracy</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600 mb-1">2 min</div>
              <div className="text-gray-600 text-sm">ERP to FIRS Submission</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600 mb-1">8+</div>
              <div className="text-gray-600 text-sm">Global Compliance Standards</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-orange-600 mb-1">360°</div>
              <div className="text-gray-600 text-sm">Customer Intelligence</div>
            </div>
          </div>
        </div>
      </section>

      {/* Services Section */}
      <section id="services" className="px-6 py-20 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Service</h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Select the perfect solution for your e-invoicing needs
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* System Integrator */}
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">🔗</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">System Integrator</h3>
                <p className="text-gray-600 mb-6">
                  Connect 40+ business and financial systems for automated e-invoicing workflows
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    40+ Ready-made Integrations
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Multi-language SDKs (Python, JS, PHP)
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Custom API Development
                  </li>
                </ul>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => router.push('/auth/signup?role=si')}
                >
                  Choose SI Service
                </Button>
              </div>
            </div>

            {/* Access Point Provider */}
            <div className="bg-white rounded-2xl border-2 border-green-500 p-8 relative hover:shadow-lg transition-shadow">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-green-500 text-white px-4 py-1 text-sm font-medium rounded-full">
                  Recommended
                </span>
              </div>
              <div className="text-center">
                <div className="w-16 h-16 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">🚀</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Access Point Provider</h3>
                <p className="text-gray-600 mb-6">
                  Secure invoice transmission via TaxPoynt's certified APP service
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    FIRS Transmission
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Invoice Generation
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Secure Processing
                  </li>
                </ul>
                <Button
                  variant="success"
                  className="w-full"
                  onClick={() => router.push('/auth/signup?role=app')}
                >
                  Choose APP Service
                </Button>
              </div>
            </div>

            {/* Hybrid Premium */}
            <div className="bg-white rounded-2xl border border-gray-200 p-8 hover:shadow-lg transition-shadow">
              <div className="text-center">
                <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <span className="text-3xl">👑</span>
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-4">Hybrid Premium</h3>
                <p className="text-gray-600 mb-6">
                  Combined SI + APP with advanced features and premium support
                </p>
                <ul className="text-left space-y-2 mb-8">
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    All SI Features
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    All APP Features
                  </li>
                  <li className="flex items-center text-gray-700">
                    <span className="text-green-500 mr-2">✓</span>
                    Premium Support
                  </li>
                </ul>
                <Button
                  variant="outline"
                  className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                  onClick={() => router.push('/auth/signup?role=hybrid')}
                >
                  Choose Hybrid Service
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Developer Integration Section */}
      <section className="px-6 py-20 bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto">
          
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold mb-4">Three Ways to Integrate</h2>
            <p className="text-xl text-gray-300">
              Choose the integration method that works best for your team
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            
            {/* Ready-made Integrations */}
            <div className="bg-gray-800 rounded-2xl p-8">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">🔌</span>
              </div>
              <h3 className="text-xl font-bold mb-4 text-center">Ready-made Integrations</h3>
              <p className="text-gray-300 mb-6 text-center">
                Connect instantly to 40+ popular business systems
              </p>
              <div className="space-y-2 text-sm text-gray-400">
                <div>• SAP, Oracle, Dynamics, NetSuite</div>
                <div>• Salesforce, HubSpot, Zoho</div>
                <div>• QuickBooks, Xero, Sage</div>
                <div>• Shopify, WooCommerce, Jumia</div>
                <div>• Paystack, Moniepoint, OPay</div>
              </div>
            </div>

            {/* SDK Integration */}
            <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl p-8 relative">
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-yellow-400 text-gray-900 px-4 py-1 text-sm font-bold rounded-full">
                  Most Popular
                </span>
              </div>
              <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">💻</span>
              </div>
              <h3 className="text-xl font-bold mb-4 text-center">SDK Integration</h3>
              <p className="text-white/90 mb-6 text-center">
                Install our SDK and integrate in minutes
              </p>
              <div className="bg-gray-900 rounded-lg p-4 mb-4">
                <code className="text-green-400 text-sm">
                  pip install taxpoynt-sdk<br/>
                  npm install taxpoynt-sdk<br/>
                  composer require taxpoynt/sdk
                </code>
              </div>
              <div className="space-y-1 text-sm text-white/80">
                <div>• Python, JavaScript, PHP, Java, C#, Go</div>
                <div>• Auto-generated from OpenAPI specs</div>
                <div>• Type-safe with full documentation</div>
              </div>
            </div>

            {/* Custom API */}
            <div className="bg-gray-800 rounded-2xl p-8">
              <div className="w-16 h-16 bg-purple-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <span className="text-3xl">⚡</span>
              </div>
              <h3 className="text-xl font-bold mb-4 text-center">Custom API</h3>
              <p className="text-gray-300 mb-6 text-center">
                Build custom integrations with our REST API
              </p>
              <div className="space-y-2 text-sm text-gray-400">
                <div>• RESTful API with OpenAPI specs</div>
                <div>• Webhook support for real-time events</div>
                <div>• Role-based access (SI, APP, Hybrid)</div>
                <div>• Rate limiting & authentication</div>
                <div>• Comprehensive error handling</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why TaxPoynt - Unique Value Props */}
      <section className="px-6 py-20">
        <div className="max-w-6xl mx-auto text-center">
          
          <h2 className="text-3xl font-bold text-gray-900 mb-4">What Makes TaxPoynt Different?</h2>
          <p className="text-xl text-gray-600 mb-16 max-w-3xl mx-auto">
            The only platform built specifically for Nigerian business reality
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">🧠</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Nigerian Business Intelligence</h3>
              <p className="text-gray-700 text-sm">
                System trained on Nigerian patterns. Knows the difference between family support and business payment. 
                Understands Alaba Market operates differently from Victoria Island.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-green-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">🔗</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Universal Connectivity</h3>
              <p className="text-gray-700 text-sm">
                Single platform connects SAP, Salesforce, Paystack, Moniepoint, and 40+ other systems. 
                One integration handles everything.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-purple-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">⚡</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">End-to-End Automation</h3>
              <p className="text-gray-700 text-sm">
                From ERP sale to FIRS submission in under 2 minutes. 
                Zero manual intervention, complete workflow orchestration.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-orange-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">🎯</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">360° Customer Intelligence</h3>
              <p className="text-gray-700 text-sm">
                Matches customers across all systems. Know when your SAP customer John is the same person paying via Paystack.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-cyan-50 to-cyan-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-cyan-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">🌍</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Global Compliance Standards</h3>
              <p className="text-gray-700 text-sm">
                FIRS-ready AND PEPPOL-certified simultaneously. 
                8+ international frameworks in one compliance engine.
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-6">
              <div className="w-12 h-12 bg-red-600 rounded-xl flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-xl">💻</span>
              </div>
              <h3 className="font-bold text-gray-900 mb-3">Developer-First SDKs</h3>
              <p className="text-gray-700 text-sm">
                Python, JavaScript, PHP, Java, C#, Go SDKs. 
                Auto-generated from OpenAPI specs with full type safety.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="px-6 py-20 bg-blue-600">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your E-Invoicing?
          </h2>
          <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
            Join hundreds of Nigerian businesses saving time and ensuring compliance with TaxPoynt
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              variant="secondary"
              size="lg"
              onClick={() => router.push('/auth/signup')}
              className="text-lg px-8 py-4 bg-white text-blue-600 hover:bg-gray-50"
            >
              Start Free Trial
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={() => router.push('/contact')}
              className="text-lg px-8 py-4 border-white text-white hover:bg-white hover:text-blue-600"
            >
              Talk to Sales
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-6 py-12 bg-gray-900 text-white">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-3 mb-4 md:mb-0">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold">T</span>
              </div>
              <div>
                <div className="font-bold">TaxPoynt</div>
                <div className="text-xs text-gray-400">Nigeria's Premier E-Invoice Platform</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <a href="/privacy" className="hover:text-white">Privacy</a>
              <a href="/terms" className="hover:text-white">Terms</a>
              <a href="/support" className="hover:text-white">Support</a>
            </div>
          </div>
          
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm text-gray-400">
            <p>&copy; 2024 TaxPoynt. All rights reserved. FIRS Certified Access Point Provider.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};