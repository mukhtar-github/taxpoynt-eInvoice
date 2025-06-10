import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { useToast } from '@/components/ui/Toast';
import Modal, { ModalHeader, ModalBody, ModalFooter } from '@/components/ui/Modal';
import { Loader2, Send, CheckCircle, Shield } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Badge } from '@/components/ui/Badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Label } from '@/components/ui/Label';
import axios from 'axios';
import TransmissionDetails from './TransmissionDetails';

interface Certificate {
  id: string;
  name: string;
  status: string;
}

interface InvoiceTransmitButtonProps {
  invoiceId: string;
  organizationId: string;
  invoiceNumber: string;
  certificates: Certificate[];
  disabled?: boolean;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg';
  onTransmissionComplete?: (transmissionId: string) => void;
}

const InvoiceTransmitButton: React.FC<InvoiceTransmitButtonProps> = ({
  invoiceId,
  organizationId,
  invoiceNumber,
  certificates,
  disabled = false,
  variant = 'default',
  size = 'default',
  onTransmissionComplete
}) => {
  const toast = useToast();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [transmissionId, setTransmissionId] = useState<string | null>(null);
  const [statusDetails, setStatusDetails] = useState<any>(null);

  const handleTransmit = async () => {
    setLoading(true);
    setError(null);
    setSuccess(false);
    setStatusDetails(null);
    
    try {
      const token = localStorage.getItem('token');
      
      // Make API call to transmit invoice
      const response = await axios.post('/api/v1/firs/transmit-invoice', {
        invoice_id: invoiceId,
        organization_id: organizationId,
        certificate_id: selectedCertificate || undefined
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      setSuccess(true);
      setTransmissionId(response.data.transmission_id);
      
      // Get initial status
      const statusResponse = await axios.get(`/api/v1/transmissions/${response.data.transmission_id}/status`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setStatusDetails(statusResponse.data);
      
      toast({
        title: 'Success',
        description: 'Invoice transmitted successfully',
        status: 'success',
      });
      
      // Notify parent component if callback provided
      if (onTransmissionComplete) {
        onTransmissionComplete(response.data.transmission_id);
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to transmit invoice';
        setError(errorMsg);
        toast({
          title: 'Error',
          description: errorMsg,
          status: 'error',
        });
      } else {
        setError('An unexpected error occurred');
        toast({
          title: 'Error',
          description: 'An unexpected error occurred',
          status: 'error',
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = async () => {
    if (!transmissionId) return;
    
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const statusResponse = await axios.get(`/api/v1/transmissions/${transmissionId}/status`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      setStatusDetails(statusResponse.data);
    } catch (err) {
      toast({
        title: 'Error',
        description: 'Failed to refresh transmission status',
        status: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        variant={variant}
        size={size}
        onClick={() => setIsModalOpen(true)}
        disabled={disabled}
        className={variant === 'default' ? 'bg-cyan-600 hover:bg-cyan-700' : ''}
      >
        <Send className="h-4 w-4 mr-2" />
        Transmit to FIRS
      </Button>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} size="lg">
        <div className="modal-content">
          <ModalHeader>
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold">Transmit Invoice to FIRS</h3>
              <Badge variant="outline" className="border-cyan-500 text-cyan-500">
                <Shield className="w-3 h-3 mr-1" /> APP
              </Badge>
            </div>
          </ModalHeader>
          
          <ModalBody>
            {!success ? (
              <div className="space-y-4">
                <p>
                  You are about to securely transmit invoice <span className="font-medium">{invoiceNumber}</span> to FIRS.
                  This process will:
                </p>
                
                <ul className="list-disc pl-6 space-y-1 text-sm">
                  <li>Encrypt the invoice data using RSA-OAEP with AES-256-GCM</li>
                  <li>Digitally sign the payload if a certificate is selected</li>
                  <li>Securely transmit to the FIRS API</li>
                  <li>Store a receipt upon successful transmission</li>
                </ul>
                
                {certificates.length > 0 && (
                  <div className="mt-4">
                    <Label htmlFor="certificate">Digital Certificate (Optional)</Label>
                    <Select value={selectedCertificate} onValueChange={setSelectedCertificate}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a certificate" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">No certificate</SelectItem>
                        {certificates.map(cert => (
                          <SelectItem key={cert.id} value={cert.id}>
                            {cert.name} {cert.status === 'active' ? '(Active)' : `(${cert.status})`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-gray-500 mt-1">
                      Select a certificate to sign the transmission payload
                    </p>
                  </div>
                )}

                {error && (
                  <Alert variant="error" className="mt-4">
                    <AlertTitle>Error</AlertTitle>
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-center p-4 bg-green-50 rounded-md">
                  <CheckCircle className="h-6 w-6 text-green-500 mr-2" />
                  <p className="text-green-700 font-medium">Transmission initiated successfully!</p>
                </div>
                
                {statusDetails && (
                  <div className="mt-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-md font-semibold">Transmission Status</h4>
                      <Button 
                        variant="outline" 
                        size="sm" 
                        onClick={refreshStatus}
                        disabled={loading}
                      >
                        {loading ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          "Refresh"
                        )}
                      </Button>
                    </div>
                    <TransmissionDetails status={statusDetails} />
                  </div>
                )}
              </div>
            )}
          </ModalBody>
          
          <ModalFooter>
            {!success ? (
              <>
                <Button
                  variant="outline"
                  onClick={() => setIsModalOpen(false)}
                  className="mr-2"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleTransmit}
                  disabled={loading}
                  className="bg-cyan-600 hover:bg-cyan-700"
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Send className="h-4 w-4 mr-2" />
                      Transmit Securely
                    </>
                  )}
                </Button>
              </>
            ) : (
              <Button
                variant="outline"
                onClick={() => {
                  setIsModalOpen(false);
                  // Reset state for next use
                  setSuccess(false);
                  setSelectedCertificate('');
                  setStatusDetails(null);
                  setTransmissionId(null);
                }}
              >
                Close
              </Button>
            )}
          </ModalFooter>
        </div>
      </Modal>
    </>
  );
};

export default InvoiceTransmitButton;
