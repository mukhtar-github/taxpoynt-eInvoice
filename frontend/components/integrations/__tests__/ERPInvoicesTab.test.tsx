import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ERPInvoicesTab from '../ERPInvoicesTab';
import { IntegrationService } from '@/services/api/integrationService';

// Mock the IntegrationService
jest.mock('@/services/api/integrationService', () => ({
  IntegrationService: {
    getInvoices: jest.fn()
  }
}));

// Mock the utilities
jest.mock('@/utils/dateUtils', () => ({
  formatDate: jest.fn(date => 'formatted-date'),
  formatCurrency: jest.fn((amount, currency) => `${currency} ${amount}`)
}));

describe('ERPInvoicesTab', () => {
  const mockProps = {
    organizationId: 'org-123',
    integrationId: 'int-456',
    erpType: 'odoo' as const,
    title: 'Test Invoices',
    defaultCurrency: 'NGN'
  };
  
  const mockInvoices = [
    {
      id: '1',
      number: 'INV-001',
      customerName: 'Test Customer',
      date: '2025-05-25',
      amount: 1000,
      status: 'posted',
      currency: 'NGN'
    },
    {
      id: '2',
      number: 'INV-002',
      customerName: 'Another Customer',
      date: '2025-05-26',
      amount: 2000,
      status: 'draft',
      currency: 'NGN'
    }
  ];
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation
    (IntegrationService.getInvoices as jest.Mock).mockResolvedValue({
      success: true,
      invoices: mockInvoices,
      total: mockInvoices.length
    });
  });
  
  test('renders loading state initially', () => {
    render(<ERPInvoicesTab {...mockProps} />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  test('renders invoices when data is loaded', async () => {
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that invoices are displayed
    expect(screen.getByText('INV-001')).toBeInTheDocument();
    expect(screen.getByText('INV-002')).toBeInTheDocument();
    expect(screen.getByText('Test Customer')).toBeInTheDocument();
    expect(screen.getByText('Another Customer')).toBeInTheDocument();
  });
  
  test('displays empty state when no invoices found', async () => {
    // Mock empty response
    (IntegrationService.getInvoices as jest.Mock).mockResolvedValueOnce({
      success: true,
      invoices: [],
      total: 0
    });
    
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that empty state is displayed
    expect(screen.getByText(/no invoices found/i)).toBeInTheDocument();
  });
  
  test('displays error message when API call fails', async () => {
    // Mock error response
    (IntegrationService.getInvoices as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch'));
    
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that error is displayed
    expect(screen.getByText(/failed to fetch invoices/i)).toBeInTheDocument();
  });
  
  test('refreshes data when refresh button is clicked', async () => {
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Click refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should call getInvoices again
    expect(IntegrationService.getInvoices).toHaveBeenCalledTimes(2);
  });
  
  test('toggles draft invoices when button is clicked', async () => {
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Initially should call with include_draft=false (default)
    expect(IntegrationService.getInvoices).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ include_draft: false })
    );
    
    // Click show draft button
    const draftButton = screen.getByText(/show draft/i);
    fireEvent.click(draftButton);
    
    // Should call with include_draft=true
    expect(IntegrationService.getInvoices).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ include_draft: true })
    );
  });
  
  test('handles search functionality', async () => {
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Type in search input
    const searchInput = screen.getByPlaceholderText(/search invoices/i);
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    // Submit the search form
    const searchForm = searchInput.closest('form');
    fireEvent.submit(searchForm!);
    
    // Should call getInvoices with search param
    expect(IntegrationService.getInvoices).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ search: 'test query' })
    );
  });
  
  test('renders pagination correctly', async () => {
    // Mock response with more invoices
    (IntegrationService.getInvoices as jest.Mock).mockResolvedValueOnce({
      success: true,
      invoices: mockInvoices,
      total: 25 // More than one page
    });
    
    render(<ERPInvoicesTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check pagination text
    expect(screen.getByText(/1-2 of 25/i)).toBeInTheDocument();
    
    // Next page button should be enabled
    const nextButton = screen.getByRole('button', { name: /next/i });
    expect(nextButton).not.toBeDisabled();
    
    // Previous page button should be disabled (on first page)
    const prevButton = screen.getByRole('button', { name: /previous/i });
    expect(prevButton).toBeDisabled();
    
    // Click next page
    fireEvent.click(nextButton);
    
    // Should call getInvoices with page=1 (2nd page, 0-indexed)
    expect(IntegrationService.getInvoices).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ page: 1 })
    );
  });
  
  test('uses custom mapper function when provided', async () => {
    const customMapper = jest.fn().mockReturnValue(mockInvoices);
    
    render(
      <ERPInvoicesTab
        {...mockProps}
        mapResponseToInvoices={customMapper}
      />
    );
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(customMapper).toHaveBeenCalled();
    });
    
    expect(screen.getByText('INV-001')).toBeInTheDocument();
  });
});
