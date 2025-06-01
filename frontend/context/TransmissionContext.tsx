import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import transmissionService from '@/utils/transmissionService';
import { 
  TransmissionRecord,
  TransmissionStatus,
  TransmissionReceipt,
  TransmissionRequest,
  TransmissionResponse,
  TransmissionRetryRequest
} from '@/types/transmission';
import { useToast } from '@/components/ui/Toast';

interface TransmissionContextType {
  transmissions: TransmissionRecord[];
  loading: boolean;
  error: string | null;
  selectedTransmission: TransmissionRecord | null;
  statusDetails: TransmissionStatus | null;
  receiptDetails: TransmissionReceipt | null;
  fetchTransmissions: (organizationId: string) => Promise<void>;
  getTransmissionStatus: (transmissionId: string) => Promise<TransmissionStatus | null>;
  getTransmissionReceipt: (transmissionId: string) => Promise<TransmissionReceipt | null>;
  transmitData: (data: TransmissionRequest) => Promise<TransmissionResponse | null>;
  transmitFile: (file: File, organizationId: string, certificateId?: string) => Promise<TransmissionResponse | null>;
  transmitInvoice: (invoiceId: string, organizationId: string, certificateId?: string) => Promise<TransmissionResponse | null>;
  retryTransmission: (transmissionId: string, options?: TransmissionRetryRequest) => Promise<TransmissionResponse | null>;
  selectTransmission: (transmission: TransmissionRecord | null) => void;
  clearError: () => void;
}

const TransmissionContext = createContext<TransmissionContextType | undefined>(undefined);

export const useTransmission = (): TransmissionContextType => {
  const context = useContext(TransmissionContext);
  if (!context) {
    throw new Error('useTransmission must be used within a TransmissionProvider');
  }
  return context;
};

interface TransmissionProviderProps {
  children: ReactNode;
}

export const TransmissionProvider: React.FC<TransmissionProviderProps> = ({ children }) => {
  const toast = useToast();
  const [transmissions, setTransmissions] = useState<TransmissionRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTransmission, setSelectedTransmission] = useState<TransmissionRecord | null>(null);
  const [statusDetails, setStatusDetails] = useState<TransmissionStatus | null>(null);
  const [receiptDetails, setReceiptDetails] = useState<TransmissionReceipt | null>(null);

  const handleError = useCallback((err: any, defaultMessage: string) => {
    if (axios.isAxiosError(err)) {
      const errorMsg = err.response?.data?.detail || defaultMessage;
      setError(errorMsg);
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
      });
      return errorMsg;
    } else if (err instanceof Error) {
      setError(err.message);
      toast({
        title: 'Error',
        description: err.message,
        status: 'error',
      });
      return err.message;
    } else {
      setError(defaultMessage);
      toast({
        title: 'Error',
        description: defaultMessage,
        status: 'error',
      });
      return defaultMessage;
    }
  }, [toast]);

  const fetchTransmissions = useCallback(async (organizationId: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await transmissionService.getTransmissions(organizationId);
      setTransmissions(data);
      return;
    } catch (err) {
      handleError(err, 'Failed to fetch transmissions');
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  const getTransmissionStatus = useCallback(async (transmissionId: string): Promise<TransmissionStatus | null> => {
    setLoading(true);
    
    try {
      const status = await transmissionService.getTransmissionStatus(transmissionId);
      setStatusDetails(status);
      return status;
    } catch (err) {
      handleError(err, 'Failed to fetch transmission status');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  const getTransmissionReceipt = useCallback(async (transmissionId: string): Promise<TransmissionReceipt | null> => {
    setLoading(true);
    
    try {
      const receipt = await transmissionService.getTransmissionReceipt(transmissionId);
      setReceiptDetails(receipt);
      return receipt;
    } catch (err) {
      handleError(err, 'Failed to fetch transmission receipt');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError]);

  const transmitData = useCallback(async (data: TransmissionRequest): Promise<TransmissionResponse | null> => {
    setLoading(true);
    
    try {
      const response = await transmissionService.transmit(data);
      
      // Add new transmission to the list
      if (response && response.transmission_id) {
        const newTransmission: TransmissionRecord = {
          id: response.transmission_id,
          status: response.status,
          organization_id: data.organization_id,
          transmission_time: new Date().toISOString(),
          destination: 'FIRS',
          retry_count: 0,
          certificate_id: data.certificate_id,
          submission_id: data.submission_id
        };
        
        setTransmissions(prev => [newTransmission, ...prev]);
      }
      
      toast({
        title: 'Success',
        description: 'Transmission initiated successfully',
        status: 'success',
      });
      
      return response;
    } catch (err) {
      handleError(err, 'Failed to transmit data');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError, toast]);

  const transmitFile = useCallback(async (
    file: File, 
    organizationId: string, 
    certificateId?: string
  ): Promise<TransmissionResponse | null> => {
    setLoading(true);
    
    try {
      const response = await transmissionService.transmitFile(file, organizationId, certificateId);
      
      if (response && response.transmission_id) {
        const newTransmission: TransmissionRecord = {
          id: response.transmission_id,
          status: response.status,
          organization_id: organizationId,
          transmission_time: new Date().toISOString(),
          destination: 'FIRS',
          retry_count: 0,
          certificate_id: certificateId
        };
        
        setTransmissions(prev => [newTransmission, ...prev]);
      }
      
      toast({
        title: 'Success',
        description: 'File transmission initiated successfully',
        status: 'success',
      });
      
      return response;
    } catch (err) {
      handleError(err, 'Failed to transmit file');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError, toast]);

  const transmitInvoice = useCallback(async (
    invoiceId: string, 
    organizationId: string, 
    certificateId?: string
  ): Promise<TransmissionResponse | null> => {
    setLoading(true);
    
    try {
      const response = await transmissionService.transmitInvoice(invoiceId, organizationId, certificateId);
      
      if (response && response.transmission_id) {
        const newTransmission: TransmissionRecord = {
          id: response.transmission_id,
          status: response.status,
          organization_id: organizationId,
          transmission_time: new Date().toISOString(),
          destination: 'FIRS',
          retry_count: 0,
          certificate_id: certificateId,
          submission_id: invoiceId
        };
        
        setTransmissions(prev => [newTransmission, ...prev]);
      }
      
      toast({
        title: 'Success',
        description: 'Invoice transmission initiated successfully',
        status: 'success',
      });
      
      return response;
    } catch (err) {
      handleError(err, 'Failed to transmit invoice');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError, toast]);

  const retryTransmission = useCallback(async (
    transmissionId: string, 
    options?: TransmissionRetryRequest
  ): Promise<TransmissionResponse | null> => {
    setLoading(true);
    
    try {
      const response = await transmissionService.retryTransmission(transmissionId, options);
      
      // Update transmission status in the list
      setTransmissions(prev => 
        prev.map(t => 
          t.id === transmissionId ? { ...t, status: 'retrying', retry_count: t.retry_count + 1 } : t
        )
      );
      
      toast({
        title: 'Success',
        description: 'Transmission retry initiated successfully',
        status: 'success',
      });
      
      return response;
    } catch (err) {
      handleError(err, 'Failed to retry transmission');
      return null;
    } finally {
      setLoading(false);
    }
  }, [handleError, toast]);

  const selectTransmission = useCallback((transmission: TransmissionRecord | null) => {
    setSelectedTransmission(transmission);
    setStatusDetails(null);
    setReceiptDetails(null);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value = {
    transmissions,
    loading,
    error,
    selectedTransmission,
    statusDetails,
    receiptDetails,
    fetchTransmissions,
    getTransmissionStatus,
    getTransmissionReceipt,
    transmitData,
    transmitFile,
    transmitInvoice,
    retryTransmission,
    selectTransmission,
    clearError
  };

  return (
    <TransmissionContext.Provider value={value}>
      {children}
    </TransmissionContext.Provider>
  );
};

// Fix for missing axios import
import axios from 'axios';

export default TransmissionProvider;
