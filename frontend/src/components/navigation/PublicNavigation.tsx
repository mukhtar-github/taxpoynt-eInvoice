import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { cn } from '../../utils/cn';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { Menu, X, ArrowRight, Shield, Database, Building } from 'lucide-react';

interface PublicNavItem {
  name: string;
  href: string;
  description?: string;
  children?: PublicNavItem[];
}

interface PublicNavigationProps {
  title?: string;
  className?: string;
}

// Public marketing navigation items (for unauthenticated users)
const publicNavItems: PublicNavItem[] = [
  {
    name: 'Services',
    href: '/services',
    children: [
      {
        name: 'Access Point Provider',
        href: '/services/access-point-provider',
        description: 'FIRS-certified e-invoicing services'
      },
      {
        name: 'System Integration',
        href: '/services/system-integration',
        description: 'ERP, CRM, and POS integrations'
      },
      {
        name: 'Nigerian Compliance',
        href: '/services/nigerian-compliance',
        description: 'Regulatory and tax compliance'
      }
    ]
  },
  {
    name: 'Solutions',
    href: '/solutions',
    children: [
      {
        name: 'For Enterprises',
        href: '/solutions/enterprise',
        description: 'Large-scale e-invoicing solutions'
      },
      {
        name: 'For SMEs',
        href: '/solutions/sme',
        description: 'Small and medium business solutions'
      },
      {
        name: 'For Developers',
        href: '/solutions/developers',
        description: 'API and integration solutions'
      }
    ]
  },
  {
    name: 'Pricing',
    href: '/pricing'
  },
  {
    name: 'Resources',
    href: '/resources',
    children: [
      {
        name: 'Documentation',
        href: '/docs',
        description: 'API docs and integration guides'
      },
      {
        name: 'Blog',
        href: '/blog',
        description: 'Industry insights and updates'
      },
      {
        name: 'Support',
        href: '/support',
        description: 'Help center and support'
      }
    ]
  },
  {
    name: 'Contact',
    href: '/contact'
  }
];

/**
 * PublicNavigation Component
 * 
 * Clean navigation component for marketing/landing pages.
 * Only shows appropriate items for unauthenticated users.
 */
export const PublicNavigation: React.FC<PublicNavigationProps> = ({
  title = 'TaxPoynt eInvoice',
  className
}) => {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(prev => !prev);
  };

  const handleDropdownToggle = (name: string) => {
    setOpenDropdown(curr => curr === name ? null : name);
  };

  const isActive = (href: string) => {
    return router.pathname === href || router.pathname.startsWith(`${href}/`);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
    setOpenDropdown(null);
  };

  return (
    <header className={cn("bg-white border-b border-gray-200 sticky top-0 z-50", className)}>
      <div className="container mx-auto px-4 max-w-7xl">
        {/* Desktop Navigation */}
        <div className="hidden lg:flex h-16 items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <div className="relative w-8 h-8">
                <Image 
                  src="/logo.svg" 
                  alt="TaxPoynt Logo" 
                  fill 
                  className="object-contain" 
                  priority 
                />
              </div>
              <Typography.Text className="text-lg font-bold text-gray-900">
                {title}
              </Typography.Text>
            </Link>
          </div>

          {/* Desktop Navigation Links */}
          <nav className="hidden lg:flex items-center space-x-8">
            {publicNavItems.map((item) => (
              <div key={item.name} className="relative group">
                {item.children ? (
                  <button 
                    onMouseEnter={() => setOpenDropdown(item.name)}
                    onMouseLeave={() => setOpenDropdown(null)}
                    className={cn(
                      "flex items-center px-3 py-2 text-sm font-medium transition-colors rounded-md",
                      isActive(item.href) 
                        ? "text-blue-600 bg-blue-50" 
                        : "text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                    )}
                  >
                    {item.name}
                    <svg className="ml-1 h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                ) : (
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center px-3 py-2 text-sm font-medium transition-colors rounded-md",
                      isActive(item.href) 
                        ? "text-blue-600 bg-blue-50" 
                        : "text-gray-700 hover:text-blue-600 hover:bg-gray-50"
                    )}
                  >
                    {item.name}
                  </Link>
                )}

                {/* Dropdown Menu */}
                {item.children && openDropdown === item.name && (
                  <div 
                    className="absolute left-0 mt-2 w-72 rounded-lg shadow-lg bg-white ring-1 ring-gray-200 z-10"
                    onMouseEnter={() => setOpenDropdown(item.name)}
                    onMouseLeave={() => setOpenDropdown(null)}
                  >
                    <div className="p-4 space-y-2">
                      {item.children.map((child) => (
                        <Link
                          key={child.name}
                          href={child.href}
                          className={cn(
                            "block p-3 rounded-md hover:bg-gray-50 transition-colors",
                            isActive(child.href) ? "bg-blue-50" : ""
                          )}
                        >
                          <div className="font-medium text-gray-900">{child.name}</div>
                          {child.description && (
                            <div className="text-sm text-gray-500 mt-1">{child.description}</div>
                          )}
                        </Link>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </nav>

          {/* CTA Buttons */}
          <div className="hidden lg:flex items-center space-x-4">
            <Link href="/auth/login">
              <Button variant="ghost" size="sm">
                Sign In
              </Button>
            </Link>
            <Link href="/auth/register">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                Get Started
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>

        {/* Mobile Navigation */}
        <div className="lg:hidden flex h-14 items-center justify-between">
          {/* Mobile Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="relative w-7 h-7">
                <Image 
                  src="/logo.svg" 
                  alt="TaxPoynt Logo" 
                  fill 
                  className="object-contain" 
                  priority 
                />
              </div>
              <Typography.Text className="text-base font-bold text-gray-900">
                TaxPoynt
              </Typography.Text>
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleMobileMenu}
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {isMobileMenuOpen && (
        <div className="lg:hidden bg-white border-t border-gray-200">
          <div className="container mx-auto px-4 py-4 space-y-4">
            {/* Navigation Links */}
            <nav className="space-y-2">
              {publicNavItems.map((item) => (
                <div key={item.name}>
                  {item.children ? (
                    <>
                      <button 
                        onClick={() => handleDropdownToggle(item.name)}
                        className="flex items-center justify-between w-full px-3 py-2 text-base font-medium text-gray-900 rounded-md hover:bg-gray-50"
                      >
                        {item.name}
                        <svg 
                          className={cn(
                            "h-5 w-5 transition-transform",
                            openDropdown === item.name && "transform rotate-180"
                          )} 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>

                      {openDropdown === item.name && (
                        <div className="pl-4 space-y-1 mt-2">
                          {item.children.map((child) => (
                            <Link
                              key={child.name}
                              href={child.href}
                              onClick={closeMobileMenu}
                              className={cn(
                                "block p-3 rounded-md transition-colors",
                                isActive(child.href) 
                                  ? "bg-blue-50 text-blue-600" 
                                  : "text-gray-700 hover:bg-gray-50"
                              )}
                            >
                              <div className="font-medium">{child.name}</div>
                              {child.description && (
                                <div className="text-sm text-gray-500 mt-1">{child.description}</div>
                              )}
                            </Link>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <Link
                      href={item.href}
                      onClick={closeMobileMenu}
                      className={cn(
                        "block px-3 py-2 text-base font-medium rounded-md transition-colors",
                        isActive(item.href) 
                          ? "bg-blue-50 text-blue-600" 
                          : "text-gray-900 hover:bg-gray-50"
                      )}
                    >
                      {item.name}
                    </Link>
                  )}
                </div>
              ))}
            </nav>

            {/* Mobile CTA Buttons */}
            <div className="pt-4 border-t border-gray-200 space-y-3">
              <Link href="/auth/login" onClick={closeMobileMenu} className="block">
                <Button variant="outline" size="sm" className="w-full">
                  Sign In
                </Button>
              </Link>
              <Link href="/auth/register" onClick={closeMobileMenu} className="block">
                <Button size="sm" className="w-full bg-blue-600 hover:bg-blue-700">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

export default PublicNavigation;