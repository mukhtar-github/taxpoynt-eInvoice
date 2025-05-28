import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ERPCustomersTab from '../ERPCustomersTab';
import { IntegrationService } from '@/services/api/integrationService';

// Mock the IntegrationService
jest.mock('@/services/api/integrationService', () => ({
  IntegrationService: {
    getCustomers: jest.fn()
  }
}));

describe('ERPCustomersTab', () => {
  const mockProps = {
    organizationId: 'org-123',
    integrationId: 'int-456',
    erpType: 'odoo' as const,
    title: 'Test Customers'
  };
  
  const mockCustomers = [
    {
      id: '1',
      name: 'Test Customer',
      email: 'customer@example.com',
      phone: '+1234567890',
      vat: '123456789',
      address: '123 Test Street'
    },
    {
      id: '2',
      name: 'Another Customer',
      email: 'another@example.com',
      phone: '+0987654321',
      vat: '987654321',
      address: '456 Example Avenue'
    }
  ];
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation
    (IntegrationService.getCustomers as jest.Mock).mockResolvedValue({
      success: true,
      customers: mockCustomers,
      total: mockCustomers.length
    });
  });
  
  test('renders loading state initially', () => {
    render(<ERPCustomersTab {...mockProps} />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  test('renders customers when data is loaded', async () => {
    render(<ERPCustomersTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that customers are displayed
    expect(screen.getByText('Test Customer')).toBeInTheDocument();
    expect(screen.getByText('Another Customer')).toBeInTheDocument();
    expect(screen.getByText('customer@example.com')).toBeInTheDocument();
    expect(screen.getByText('+1234567890')).toBeInTheDocument();
  });
  
  test('displays empty state when no customers found', async () => {
    // Mock empty response
    (IntegrationService.getCustomers as jest.Mock).mockResolvedValueOnce({
      success: true,
      customers: [],
      total: 0
    });
    
    render(<ERPCustomersTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that empty state is displayed
    expect(screen.getByText(/no customers found/i)).toBeInTheDocument();
  });
  
  test('displays error message when API call fails', async () => {
    // Mock error response
    (IntegrationService.getCustomers as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch'));
    
    render(<ERPCustomersTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that error is displayed
    expect(screen.getByText(/failed to fetch customers/i)).toBeInTheDocument();
  });
  
  test('refreshes data when refresh button is clicked', async () => {
    render(<ERPCustomersTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Click refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should call getCustomers again
    expect(IntegrationService.getCustomers).toHaveBeenCalledTimes(2);
  });
  
  test('handles search functionality', async () => {
    render(<ERPCustomersTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Type in search input
    const searchInput = screen.getByPlaceholderText(/search customers/i);
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    // Submit the search form
    const searchForm = searchInput.closest('form');
    fireEvent.submit(searchForm!);
    
    // Should call getCustomers with search param
    expect(IntegrationService.getCustomers).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ search: 'test query' })
    );
  });
  
  test('renders pagination correctly', async () => {
    // Mock response with more customers
    (IntegrationService.getCustomers as jest.Mock).mockResolvedValueOnce({
      success: true,
      customers: mockCustomers,
      total: 25 // More than one page
    });
    
    render(<ERPCustomersTab {...mockProps} />);
    
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
    
    // Should call getCustomers with page=1 (2nd page, 0-indexed)
    expect(IntegrationService.getCustomers).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ page: 1 })
    );
  });
  
  test('uses custom mapper function when provided', async () => {
    const customMapper = jest.fn().mockReturnValue(mockCustomers);
    
    render(
      <ERPCustomersTab
        {...mockProps}
        mapResponseToCustomers={customMapper}
      />
    );
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(customMapper).toHaveBeenCalled();
    });
    
    expect(screen.getByText('Test Customer')).toBeInTheDocument();
  });
});
