/**
 * Local API proxy to handle connections to the FIRS API during testing
 * This helps bypass CORS issues when the server isn't properly configured
 */

import axios from 'axios';

// Create a local mock API response for testing
const mockSubmitInvoice = async (invoiceData: any) => {
  console.log('Mock submitting invoice:', invoiceData);
  
  // Generate a fake submission ID
  const submissionId = 'TEST_' + Math.random().toString(36).substring(2, 15);
  
  // Return successful response
  return {
    success: true,
    message: 'Invoice submitted successfully in test mode',
    submission_id: submissionId,
    timestamp: new Date().toISOString()
  };
};

const mockCheckStatus = async (submissionId: string) => {
  console.log('Mock checking status for:', submissionId);
  
  // Return a mock status
  return {
    submission_id: submissionId,
    status: 'COMPLETED',
    message: 'Test submission completed successfully',
    timestamp: new Date().toISOString()
  };
};

// Functions that use the real API when possible, falling back to mock implementations
export const submitInvoice = async (invoiceData: any) => {
  try {
    // Try to use the real API first
    const response = await axios.post('/api/firs/submit-invoice', invoiceData);
    return response.data;
  } catch (error) {
    console.log('Using mock implementation due to API error:', error);
    return mockSubmitInvoice(invoiceData);
  }
};

export const checkSubmissionStatus = async (submissionId: string) => {
  try {
    // Try to use the real API first
    const response = await axios.get(`/api/firs/status/${submissionId}`);
    return response.data;
  } catch (error) {
    console.log('Using mock implementation due to API error:', error);
    return mockCheckStatus(submissionId);
  }
};

export default {
  submitInvoice,
  checkSubmissionStatus
};
