import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardLayout } from '../../../components/dashboard/DashboardLayout';

// Mock the next/router
jest.mock('next/router', () => ({
  useRouter() {
    return {
      route: '/',
      pathname: '',
      query: {},
      asPath: '',
      push: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn()
      },
      beforePopState: jest.fn(() => null),
      prefetch: jest.fn(() => null)
    };
  },
}));

// Mock the AuthContext
jest.mock('../../../context/AuthContext', () => ({
  useAuth: () => ({
    user: { id: '123', name: 'Test User' },
    isAuthenticated: true,
    logout: jest.fn(),
  }),
}));

describe('DashboardLayout Component', () => {
  const mockOrganization = {
    id: '123',
    name: 'MT Garba Global Ventures',
    tax_id: '12345678',
    logo_url: 'https://example.com/logo.png',
    branding_settings: {
      primary_color: '#1a73e8',
      theme: 'light'
    }
  };

  it('renders the dashboard layout with company logo and name', () => {
    render(
      <DashboardLayout 
        organization={mockOrganization}
      >
        <div data-testid="child-content">Dashboard Content</div>
      </DashboardLayout>
    );
    
    // Check that the company name is displayed
    expect(screen.getByText('MT Garba Global Ventures')).toBeInTheDocument();
    
    // Check that the logo is displayed
    const logo = screen.getByAltText('Company Logo');
    expect(logo).toBeInTheDocument();
    expect(logo).toHaveAttribute('src', 'https://example.com/logo.png');
    
    // Check that the child content is rendered
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('Dashboard Content')).toBeInTheDocument();
  });

  it('applies custom branding settings', () => {
    render(
      <DashboardLayout 
        organization={mockOrganization}
      >
        <div>Dashboard Content</div>
      </DashboardLayout>
    );
    
    // This test would need to be customized based on how branding is applied
    // For example, if branding is applied via CSS variables:
    const header = screen.getByRole('banner');
    expect(header).toHaveStyle(`--primary-color: ${mockOrganization.branding_settings.primary_color}`);
  });

  it('renders navigation sidebar with company-specific modules', () => {
    render(
      <DashboardLayout 
        organization={mockOrganization}
      >
        <div>Dashboard Content</div>
      </DashboardLayout>
    );
    
    // Check that the navigation sidebar is rendered
    expect(screen.getByRole('navigation')).toBeInTheDocument();
    
    // Check that company-specific modules are displayed
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();
    expect(screen.getByText('Invoices')).toBeInTheDocument();
  });

  it('renders without logo when logo_url is not provided', () => {
    const orgWithoutLogo = { ...mockOrganization, logo_url: null };
    
    render(
      <DashboardLayout 
        organization={orgWithoutLogo}
      >
        <div>Dashboard Content</div>
      </DashboardLayout>
    );
    
    // Check that a default placeholder is displayed instead of logo
    expect(screen.queryByAltText('Company Logo')).not.toBeInTheDocument();
    expect(screen.getByText(/MT/)).toBeInTheDocument(); // Expecting initials as fallback
  });
});
