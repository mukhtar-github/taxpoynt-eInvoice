import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { IntegrationSetupWizard } from '../../../components/dashboard/IntegrationSetupWizard';
import { act } from 'react-dom/test-utils';

// Mock the API service
jest.mock('../../../services/api/integrationService', () => ({
  IntegrationService: {
    createIntegration: jest.fn().mockResolvedValue({ id: '123', name: 'Test Integration' }),
    testIntegration: jest.fn().mockResolvedValue({ status: 'success', message: 'Connection successful' })
  }
}));

describe('IntegrationSetupWizard Component', () => {
  const mockOrganizationId = '123';
  const mockOnComplete = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the setup wizard with all steps', () => {
    render(
      <IntegrationSetupWizard 
        organizationId={mockOrganizationId}
        onComplete={mockOnComplete}
      />
    );
    
    // Check that the wizard title is displayed
    expect(screen.getByText('Connect to Odoo')).toBeInTheDocument();
    
    // Check that the first step is displayed
    expect(screen.getByText('Connection Details')).toBeInTheDocument();
    
    // Check that the form fields are displayed
    expect(screen.getByLabelText('Odoo URL')).toBeInTheDocument();
    expect(screen.getByLabelText('Database Name')).toBeInTheDocument();
    expect(screen.getByLabelText('Authentication Method')).toBeInTheDocument();
  });

  it('validates form inputs and shows error messages', async () => {
    render(
      <IntegrationSetupWizard 
        organizationId={mockOrganizationId}
        onComplete={mockOnComplete}
      />
    );
    
    // Try to submit the form without filling in required fields
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    // Check that error messages are displayed
    await waitFor(() => {
      expect(screen.getByText('Odoo URL is required')).toBeInTheDocument();
      expect(screen.getByText('Database name is required')).toBeInTheDocument();
    });
  });

  it('allows users to navigate through all steps', async () => {
    const { integrationService } = require('../../../services/integrationService');
    integrationService.createIntegration.mockResolvedValue({ id: '123', name: 'Test Integration' });
    integrationService.testIntegrationConnection.mockResolvedValue({ status: 'success', message: 'Connection successful' });
    
    render(
      <IntegrationSetupWizard 
        organizationId={mockOrganizationId}
        onComplete={mockOnComplete}
      />
    );
    
    // Fill in the form fields
    fireEvent.change(screen.getByLabelText('Odoo URL'), { target: { value: 'https://example.odoo.com' } });
    fireEvent.change(screen.getByLabelText('Database Name'), { target: { value: 'test_db' } });
    
    // Select password authentication
    const authMethodSelect = screen.getByLabelText('Authentication Method');
    fireEvent.change(authMethodSelect, { target: { value: 'password' } });
    
    // Password fields should appear
    await waitFor(() => {
      expect(screen.getByLabelText('Username')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
    });
    
    // Fill in authentication details
    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'admin' } });
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'admin' } });
    
    // Go to next step
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    // Second step should be displayed (Test Connection)
    await waitFor(() => {
      expect(screen.getByText('Test Connection')).toBeInTheDocument();
    });
    
    // Test the connection
    const testButton = screen.getByText('Test Connection');
    await act(async () => {
      fireEvent.click(testButton);
    });
    
    // Success message should be displayed
    await waitFor(() => {
      expect(screen.getByText('Connection successful')).toBeInTheDocument();
    });
    
    // Go to next step
    const nextButton2 = screen.getByText('Next');
    fireEvent.click(nextButton2);
    
    // Final step should be displayed (Confirm)
    await waitFor(() => {
      expect(screen.getByText('Configuration Summary')).toBeInTheDocument();
    });
    
    // Complete the wizard
    const finishButton = screen.getByText('Finish');
    fireEvent.click(finishButton);
    
    // onComplete callback should be called
    await waitFor(() => {
      expect(mockOnComplete).toHaveBeenCalled();
    });
  });

  it('handles connection test failures gracefully', async () => {
    const { integrationService } = require('../../../services/integrationService');
    integrationService.testIntegrationConnection.mockResolvedValue({ 
      status: 'error', 
      message: 'Connection failed: Invalid credentials' 
    });
    
    render(
      <IntegrationSetupWizard 
        organizationId={mockOrganizationId}
        onComplete={mockOnComplete}
      />
    );
    
    // Fill in the form fields
    fireEvent.change(screen.getByLabelText('Odoo URL'), { target: { value: 'https://example.odoo.com' } });
    fireEvent.change(screen.getByLabelText('Database Name'), { target: { value: 'test_db' } });
    
    // Select password authentication
    const authMethodSelect = screen.getByLabelText('Authentication Method');
    fireEvent.change(authMethodSelect, { target: { value: 'password' } });
    
    // Fill in authentication details
    await waitFor(() => {
      fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'admin' } });
      fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong_password' } });
    });
    
    // Go to next step
    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);
    
    // Test the connection
    const testButton = screen.getByText('Test Connection');
    await act(async () => {
      fireEvent.click(testButton);
    });
    
    // Error message should be displayed
    await waitFor(() => {
      expect(screen.getByText('Connection failed: Invalid credentials')).toBeInTheDocument();
    });
  });
});
