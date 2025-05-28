import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ERPProductsTab from '../ERPProductsTab';
import { IntegrationService } from '@/services/api/integrationService';

// Mock the IntegrationService
jest.mock('@/services/api/integrationService', () => ({
  IntegrationService: {
    getProducts: jest.fn()
  }
}));

// Mock the utilities
jest.mock('@/utils/dateUtils', () => ({
  formatDate: jest.fn(date => 'formatted-date'),
  formatCurrency: jest.fn((amount, currency) => `${currency} ${amount}`)
}));

describe('ERPProductsTab', () => {
  const mockProps = {
    organizationId: 'org-123',
    integrationId: 'int-456',
    erpType: 'odoo' as const,
    title: 'Test Products',
    defaultCurrency: 'NGN'
  };
  
  const mockProducts = [
    {
      id: '1',
      name: 'Test Product',
      code: 'TP001',
      description: 'This is a test product',
      price: 1000,
      currency: 'NGN',
      taxRate: 7.5
    },
    {
      id: '2',
      name: 'Another Product',
      code: 'AP002',
      description: 'This is another test product',
      price: 2000,
      currency: 'NGN',
      taxRate: 7.5
    }
  ];
  
  beforeEach(() => {
    jest.clearAllMocks();
    
    // Default mock implementation
    (IntegrationService.getProducts as jest.Mock).mockResolvedValue({
      success: true,
      products: mockProducts,
      total: mockProducts.length
    });
  });
  
  test('renders loading state initially', () => {
    render(<ERPProductsTab {...mockProps} />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
  
  test('renders products when data is loaded', async () => {
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that products are displayed
    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('Another Product')).toBeInTheDocument();
    expect(screen.getByText('TP001')).toBeInTheDocument();
    expect(screen.getByText('AP002')).toBeInTheDocument();
  });
  
  test('displays empty state when no products found', async () => {
    // Mock empty response
    (IntegrationService.getProducts as jest.Mock).mockResolvedValueOnce({
      success: true,
      products: [],
      total: 0
    });
    
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that empty state is displayed
    expect(screen.getByText(/no products found/i)).toBeInTheDocument();
  });
  
  test('displays error message when API call fails', async () => {
    // Mock error response
    (IntegrationService.getProducts as jest.Mock).mockRejectedValueOnce(new Error('Failed to fetch'));
    
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Check that error is displayed
    expect(screen.getByText(/failed to fetch products/i)).toBeInTheDocument();
  });
  
  test('refreshes data when refresh button is clicked', async () => {
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Click refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Should call getProducts again
    expect(IntegrationService.getProducts).toHaveBeenCalledTimes(2);
  });
  
  test('handles search functionality', async () => {
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Type in search input
    const searchInput = screen.getByPlaceholderText(/search products/i);
    fireEvent.change(searchInput, { target: { value: 'test query' } });
    
    // Submit the search form
    const searchForm = searchInput.closest('form');
    fireEvent.submit(searchForm!);
    
    // Should call getProducts with search param
    expect(IntegrationService.getProducts).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ search: 'test query' })
    );
  });
  
  test('renders pagination correctly', async () => {
    // Mock response with more products
    (IntegrationService.getProducts as jest.Mock).mockResolvedValueOnce({
      success: true,
      products: mockProducts,
      total: 25 // More than one page
    });
    
    render(<ERPProductsTab {...mockProps} />);
    
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
    
    // Should call getProducts with page=1 (2nd page, 0-indexed)
    expect(IntegrationService.getProducts).toHaveBeenCalledWith(
      expect.anything(),
      expect.anything(),
      expect.anything(),
      expect.objectContaining({ page: 1 })
    );
  });
  
  test('displays product prices correctly', async () => {
    render(<ERPProductsTab {...mockProps} />);
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    });
    
    // Price formatting should be called
    expect(screen.getAllByText('NGN 1000')).toHaveLength(1);
    expect(screen.getAllByText('NGN 2000')).toHaveLength(1);
  });
  
  test('uses custom mapper function when provided', async () => {
    const customMapper = jest.fn().mockReturnValue(mockProducts);
    
    render(
      <ERPProductsTab
        {...mockProps}
        mapResponseToProducts={customMapper}
      />
    );
    
    // Wait for loading to complete
    await waitFor(() => {
      expect(customMapper).toHaveBeenCalled();
    });
    
    expect(screen.getByText('Test Product')).toBeInTheDocument();
  });
});
