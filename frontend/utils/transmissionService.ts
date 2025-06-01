import axios from 'axios';
import { 
  TransmissionRecord,
  TransmissionStatus,
  TransmissionReceipt,
  TransmissionRequest,
  TransmissionResponse,
  TransmissionRetryRequest
} from '@/types/transmission';

/**
 * Service for handling secure transmissions to FIRS API
 */
export const transmissionService = {
  /**
   * Get all transmissions for an organization
   */
  getTransmissions: async (organizationId: string): Promise<TransmissionRecord[]> => {
    const token = localStorage.getItem('token');
    const response = await axios.get(`/api/v1/transmissions?organization_id=${organizationId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  },

  /**
   * Get transmission status details
   */
  getTransmissionStatus: async (transmissionId: string): Promise<TransmissionStatus> => {
    const token = localStorage.getItem('token');
    const response = await axios.get(`/api/v1/transmissions/${transmissionId}/status`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  },

  /**
   * Get transmission receipt
   */
  getTransmissionReceipt: async (transmissionId: string): Promise<TransmissionReceipt> => {
    const token = localStorage.getItem('token');
    const response = await axios.get(`/api/v1/transmissions/${transmissionId}/receipt`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  },

  /**
   * Transmit data to FIRS
   */
  transmit: async (data: TransmissionRequest): Promise<TransmissionResponse> => {
    const token = localStorage.getItem('token');
    const response = await axios.post('/api/v1/firs/transmit', data, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  },

  /**
   * Transmit a file to FIRS
   */
  transmitFile: async (
    file: File, 
    organizationId: string, 
    certificateId?: string
  ): Promise<TransmissionResponse> => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);
    formData.append('organization_id', organizationId);
    
    if (certificateId) {
      formData.append('certificate_id', certificateId);
    }

    const response = await axios.post('/api/v1/firs/transmit-file', formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },

  /**
   * Transmit an invoice to FIRS
   */
  transmitInvoice: async (
    invoiceId: string, 
    organizationId: string, 
    certificateId?: string
  ): Promise<TransmissionResponse> => {
    const token = localStorage.getItem('token');
    const response = await axios.post('/api/v1/firs/transmit-invoice', {
      invoice_id: invoiceId,
      organization_id: organizationId,
      certificate_id: certificateId
    }, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  },

  /**
   * Retry a failed transmission
   */
  retryTransmission: async (
    transmissionId: string, 
    options?: TransmissionRetryRequest
  ): Promise<TransmissionResponse> => {
    const token = localStorage.getItem('token');
    const response = await axios.post(`/api/v1/transmissions/${transmissionId}/retry`, 
      options || {}, 
      {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  },

  /**
   * Get transmission statistics
   */
  getTransmissionStats: async (organizationId: string): Promise<any> => {
    const token = localStorage.getItem('token');
    const response = await axios.get(`/api/v1/transmissions/statistics?organization_id=${organizationId}`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  }
};

export default transmissionService;
