import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MainNav } from '../MainNav';
import { useRouter } from 'next/router';

// Mock the useRouter hook
jest.mock('next/router', () => ({
  useRouter: jest.fn()
}));

describe('MainNav Component', () => {
  // Set up the router mock before each test
  beforeEach(() => {
    (useRouter as jest.MockedFunction<typeof useRouter>).mockImplementation(() => ({
      pathname: '/',
      route: '/',
      query: {},
      asPath: '/',
      push: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn()
      },
      isFallback: false,
      isReady: true,
      isPreview: false,
      basePath: '',
      isLocaleDomain: false
    }));
  });

  test('renders the main navigation with default props', () => {
    render(<MainNav />);
    
    // Check if the title is rendered
    expect(screen.getByText('Taxpoynt')).toBeInTheDocument();
    
    // Check if default navigation items are rendered
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();
    expect(screen.getByText('IRN Management')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  test('renders with custom title', () => {
    render(<MainNav title="Custom Title" />);
    expect(screen.getByText('Custom Title')).toBeInTheDocument();
  });

  test('displays user information correctly', () => {
    const userInfo = {
      name: 'Test User',
      email: 'test@example.com'
    };
    
    render(<MainNav userInfo={userInfo} />);
    
    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  test('toggles mobile menu when menu button is clicked', () => {
    render(<MainNav />);
    
    // Initially, mobile menu should be closed
    expect(screen.queryByText('Logout')).not.toBeVisible();
    
    // Click the menu button to open the menu
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    
    // Now the mobile menu should be visible
    expect(screen.getByText('Logout')).toBeVisible();
    
    // Click again to close
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    
    // Menu should be closed again
    expect(screen.queryByText('Logout')).not.toBeVisible();
  });

  test('highlights the active menu item based on current route', () => {
    // Set the current route to dashboard
    (useRouter as jest.Mock).mockImplementation(() => ({
      pathname: '/dashboard',
      route: '/dashboard',
      query: {},
      asPath: '/dashboard',
      push: jest.fn(),
      replace: jest.fn(),
      reload: jest.fn(),
      back: jest.fn(),
      forward: jest.fn(),
      prefetch: jest.fn(),
      beforePopState: jest.fn(),
      events: {
        on: jest.fn(),
        off: jest.fn(),
        emit: jest.fn()
      },
      isFallback: false,
      isReady: true,
      isPreview: false,
      basePath: '',
      isLocaleDomain: false
    }));
    
    render(<MainNav />);
    
    // Dashboard link should have an active class
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink).toHaveClass('text-primary');
    
    // Other links should not have active class
    const settingsLink = screen.getByText('Settings').closest('a');
    expect(settingsLink).not.toHaveClass('text-primary');
  });

  test('calls onLogout when logout button is clicked', () => {
    const onLogoutMock = jest.fn();
    render(<MainNav onLogout={onLogoutMock} />);
    
    // Open the mobile menu to access the logout button
    fireEvent.click(screen.getByLabelText('Toggle menu'));
    
    // Click the logout button
    fireEvent.click(screen.getByText('Logout'));
    
    // Check if the onLogout function was called
    expect(onLogoutMock).toHaveBeenCalledTimes(1);
  });
});
