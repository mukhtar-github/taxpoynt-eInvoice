/**
 * Footer Navigation Component
 * ==========================
 * 
 * Contains important links including banking security information
 * for the new TaxPoynt platform architecture.
 */

import React from 'react';
import { useRouter } from 'next/router';

interface FooterLink {
  label: string;
  href: string;
  external?: boolean;
}

const FooterNav: React.FC = () => {
  const router = useRouter();

  const handleNavigation = (href: string, external = false) => {
    if (external) {
      window.open(href, '_blank');
    } else {
      router.push(href);
    }
  };

  const companyLinks: FooterLink[] = [
    { label: 'About TaxPoynt', href: '/about' },
    { label: 'Contact Support', href: '/support' },
    { label: 'Nigerian Support', href: 'tel:0700-TAXPOYNT', external: true }
  ];

  const legalLinks: FooterLink[] = [
    { label: 'Privacy Policy', href: '/legal/privacy' },
    { label: 'Terms of Service', href: '/legal/terms' },
    { label: 'Banking Security FAQ', href: '/security/banking-faq' },
    { label: 'Data Protection (NDPR)', href: '/legal/ndpr' }
  ];

  const serviceLinks: FooterLink[] = [
    { label: 'System Integration', href: '/services/si' },
    { label: 'Access Point Provider', href: '/services/app' },
    { label: 'Nigerian Compliance', href: '/services/compliance' },
    { label: 'API Documentation', href: '/docs/api' }
  ];

  const complianceLinks: FooterLink[] = [
    { label: 'FIRS Compliance', href: '/compliance/firs' },
    { label: 'CBN Open Banking', href: '/compliance/cbn' },
    { label: 'NDPR Compliance', href: '/compliance/ndpr' },
    { label: 'Security Standards', href: '/security/standards' }
  ];

  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Company */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Company</h3>
            <ul className="space-y-2">
              {companyLinks.map((link) => (
                <li key={link.href}>
                  <button
                    onClick={() => handleNavigation(link.href, link.external)}
                    className="text-gray-300 hover:text-white transition-colors text-left"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal & Security */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Legal & Security</h3>
            <ul className="space-y-2">
              {legalLinks.map((link) => (
                <li key={link.href}>
                  <button
                    onClick={() => handleNavigation(link.href, link.external)}
                    className="text-gray-300 hover:text-white transition-colors text-left"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Services</h3>
            <ul className="space-y-2">
              {serviceLinks.map((link) => (
                <li key={link.href}>
                  <button
                    onClick={() => handleNavigation(link.href, link.external)}
                    className="text-gray-300 hover:text-white transition-colors text-left"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          {/* Compliance */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Nigerian Compliance</h3>
            <ul className="space-y-2">
              {complianceLinks.map((link) => (
                <li key={link.href}>
                  <button
                    onClick={() => handleNavigation(link.href, link.external)}
                    className="text-gray-300 hover:text-white transition-colors text-left"
                  >
                    {link.label}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="border-t border-gray-800 mt-8 pt-8">
          <div className="flex flex-col lg:flex-row justify-between items-center">
            <div className="flex items-center space-x-4 mb-4 lg:mb-0">
              <div className="text-2xl font-bold">TaxPoynt</div>
              <div className="text-sm text-gray-400">
                Nigeria's Universal E-Invoicing Platform
              </div>
            </div>
            
            {/* Trust Badges */}
            <div className="flex items-center space-x-6 text-sm text-gray-400">
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>FIRS Certified</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>CBN Licensed</span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-green-400">✓</span>
                <span>NDPR Compliant</span>
              </div>
            </div>
          </div>
          
          <div className="text-center text-gray-500 text-sm mt-4">
            © {new Date().getFullYear()} TaxPoynt Technologies. All rights reserved.
            <br />
            Built for Nigerian businesses, by Nigerian developers.
          </div>
        </div>
      </div>
    </footer>
  );
};

export default FooterNav;