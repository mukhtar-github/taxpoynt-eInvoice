import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import IntegrationStatusMonitor from '../IntegrationStatusMonitor';

describe('IntegrationStatusMonitor', () => {
  // Test rendering different statuses
  test('renders configured status correctly', () => {
    render(<IntegrationStatusMonitor status="configured" />);
    
    expect(screen.getByText('Configured')).toBeInTheDocument();
    // Configured status should have green styling
    const statusBadge = screen.getByText('Configured').closest('span');
    expect(statusBadge).toHaveClass('bg-green-100');
    expect(statusBadge).toHaveClass('text-green-800');
  });

  test('renders error status correctly', () => {
    render(<IntegrationStatusMonitor status="error" errorMessage="Connection failed" />);
    
    expect(screen.getByText('Error')).toBeInTheDocument();
    // Error status should have red styling
    const statusBadge = screen.getByText('Error').closest('span');
    expect(statusBadge).toHaveClass('bg-red-100');
    expect(statusBadge).toHaveClass('text-red-800');
    
    // Should display the error message
    expect(screen.getByText('Connection failed')).toBeInTheDocument();
  });

  test('renders syncing status correctly', () => {
    render(<IntegrationStatusMonitor status="syncing" />);
    
    expect(screen.getByText('Syncing')).toBeInTheDocument();
    // Syncing status should have blue styling
    const statusBadge = screen.getByText('Syncing').closest('span');
    expect(statusBadge).toHaveClass('bg-blue-100');
    expect(statusBadge).toHaveClass('text-blue-800');
  });

  // Test last sync display
  test('displays last sync time when provided', () => {
    render(
      <IntegrationStatusMonitor 
        status="configured" 
        lastSync="2025-05-27T10:30:00Z" 
        showDetails={true}
      />
    );
    
    expect(screen.getByText(/Last Sync:/)).toBeInTheDocument();
  });

  // Test action buttons
  test('sync button calls onSyncClick when clicked', () => {
    const mockSyncClick = jest.fn();
    render(
      <IntegrationStatusMonitor 
        status="configured" 
        onSyncClick={mockSyncClick}
      />
    );
    
    const syncButton = screen.getByText('Sync');
    fireEvent.click(syncButton);
    
    expect(mockSyncClick).toHaveBeenCalledTimes(1);
  });

  test('retry button calls onRetryClick when clicked', () => {
    const mockRetryClick = jest.fn();
    render(
      <IntegrationStatusMonitor 
        status="error" 
        onRetryClick={mockRetryClick}
      />
    );
    
    const retryButton = screen.getByText('Retry');
    fireEvent.click(retryButton);
    
    expect(mockRetryClick).toHaveBeenCalledTimes(1);
  });

  // Test disabled states
  test('sync button is disabled when disableActions is true', () => {
    render(
      <IntegrationStatusMonitor 
        status="configured" 
        onSyncClick={jest.fn()} 
        disableActions={true}
      />
    );
    
    const syncButton = screen.getByText('Sync');
    expect(syncButton).toBeDisabled();
  });

  // Test conditional rendering
  test('does not show details when showDetails is false', () => {
    render(
      <IntegrationStatusMonitor 
        status="configured" 
        lastSync="2025-05-27T10:30:00Z" 
        showDetails={false}
      />
    );
    
    // Last sync should not be displayed
    expect(screen.queryByText(/Last Sync:/)).not.toBeInTheDocument();
  });
});
