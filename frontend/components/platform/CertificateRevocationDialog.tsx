import React, { useState } from 'react';
import { XCircle, AlertTriangle, CheckCircle, X } from 'lucide-react';
import Modal, { ModalFooter, ModalHeader, ModalBody } from '../ui/Modal';
import { Button } from '../ui/Button';
import { Textarea } from '../ui/Textarea';
import { Alert, AlertDescription } from '../ui/Alert';
import apiService from '../../utils/apiService';
import { Certificate } from '../../types/app';

interface CertificateRevocationDialogProps {
  certificate: Certificate;
  isOpen: boolean;
  onClose: () => void;
  onRevoked: () => void;
}

/**
 * Certificate Revocation Dialog Component
 * 
 * Implements a structured process for revoking certificates with
 * reason documentation, confirmation steps, and revocation status handling.
 */
const CertificateRevocationDialog: React.FC<CertificateRevocationDialogProps> = ({
  certificate,
  isOpen,
  onClose,
  onRevoked
}) => {
  const [step, setStep] = useState<'reason' | 'confirm' | 'processing' | 'complete'>(
    'reason'
  );
  const [reason, setReason] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [revocationDetails, setRevocationDetails] = useState<{
    revocationId: string;
    timestamp: string;
    status: string;
  } | null>(null);

  // Handle reason change
  const handleReasonChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setReason(e.target.value);
  };

  // Move to confirmation step
  const handleProceedToConfirm = () => {
    if (!reason.trim()) {
      setError('Please provide a reason for revocation');
      return;
    }
    setError(null);
    setStep('confirm');
  };

  // Process revocation
  const handleRevoke = async () => {
    setStep('processing');
    setError(null);

    try {
      const response = await apiService.post(`/api/v1/certificates/${certificate.id}/revoke`, {
        reason: reason.trim(),
        immediate: true
      });

      setRevocationDetails({
        revocationId: response.data.revocation_id,
        timestamp: response.data.timestamp,
        status: response.data.status
      });
      
      setStep('complete');
      
      // Callback to refresh certificates list
      if (response.data.status === 'revoked') {
        onRevoked();
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Failed to revoke certificate. Please try again.'
      );
      setStep('confirm');
    }
  };

  // Close dialog and reset state
  const handleClose = () => {
    // If revocation was successful, wait a moment before closing
    // to allow the user to see the success message
    if (step === 'complete' && !error) {
      setTimeout(() => {
        onClose();
        // Reset state after dialog is closed
        setTimeout(() => {
          setStep('reason');
          setReason('');
          setError(null);
          setRevocationDetails(null);
        }, 300);
      }, 1500);
    } else {
      onClose();
      // Reset state after dialog is closed
      setTimeout(() => {
        setStep('reason');
        setReason('');
        setError(null);
        setRevocationDetails(null);
      }, 300);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose}>
      <ModalBody className="sm:max-w-md">
        <ModalHeader>
          <div className="flex items-center text-lg font-semibold">
            <XCircle className="h-5 w-5 mr-2 text-red-500" />
            Revoke Certificate
          </div>
          <p className="text-sm text-gray-500 mt-1">
            Revoking a certificate will immediately invalidate it and prevent its use for any future operations.
          </p>
        </ModalHeader>

        {error && (
          <Alert variant="error" className="mt-2">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {step === 'reason' && (
          <div className="py-4">
            <div className="mb-4">
              <h3 className="text-sm font-medium mb-2">Certificate Details</h3>
              <div className="bg-gray-50 p-3 rounded-md text-sm">
                <p><span className="font-medium">Subject:</span> {certificate.subject}</p>
                <p><span className="font-medium">Serial Number:</span> {certificate.serial_number}</p>
                <p><span className="font-medium">Valid Until:</span> {new Date(certificate.valid_to).toLocaleDateString()}</p>
              </div>
            </div>
            
            <div className="mb-4">
              <label htmlFor="revocation-reason" className="block text-sm font-medium mb-2">
                Reason for Revocation*
              </label>
              <Textarea
                id="revocation-reason"
                value={reason}
                onChange={handleReasonChange}
                placeholder="Please provide a detailed reason for revoking this certificate..."
                className="w-full h-24"
              />
            </div>
          </div>
        )}

        {step === 'confirm' && (
          <div className="py-4">
            <Alert className="mb-4 bg-amber-50 border-amber-200">
              <AlertTriangle className="h-4 w-4 text-amber-500" />
              <AlertDescription className="text-amber-800">
                <span className="font-medium">Warning:</span> This action cannot be undone. The certificate will be
                permanently revoked and added to the Certificate Revocation List (CRL).
              </AlertDescription>
            </Alert>
            
            <div className="bg-gray-50 p-3 rounded-md text-sm mb-4">
              <h3 className="font-medium mb-2">Revocation Summary</h3>
              <p><span className="font-medium">Certificate:</span> {certificate.subject}</p>
              <p><span className="font-medium">Reason:</span> {reason}</p>
            </div>
          </div>
        )}

        {step === 'processing' && (
          <div className="py-8 flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyan-700 mb-4"></div>
            <p className="text-gray-600">Processing revocation...</p>
          </div>
        )}

        {step === 'complete' && !error && (
          <div className="py-4">
            <div className="flex items-center justify-center mb-4">
              <div className="bg-green-100 p-3 rounded-full">
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </div>
            
            <h3 className="text-center font-medium text-green-800 mb-2">
              Certificate Successfully Revoked
            </h3>
            
            <div className="bg-gray-50 p-3 rounded-md text-sm">
              <p><span className="font-medium">Revocation ID:</span> {revocationDetails?.revocationId}</p>
              <p><span className="font-medium">Timestamp:</span> {new Date(revocationDetails?.timestamp || '').toLocaleString()}</p>
              <p><span className="font-medium">Status:</span> {revocationDetails?.status}</p>
            </div>
          </div>
        )}

        <ModalFooter className="flex justify-between sm:justify-between">
          {step === 'reason' && (
            <>
              <Button variant="outline" onClick={handleClose}>
                Cancel
              </Button>
              <Button 
                onClick={handleProceedToConfirm}
                disabled={!reason.trim()}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                Continue
              </Button>
            </>
          )}
          
          {step === 'confirm' && (
            <>
              <Button variant="outline" onClick={() => setStep('reason')}>
                Back
              </Button>
              <Button 
                variant="destructive"
                onClick={handleRevoke}
              >
                Revoke Certificate
              </Button>
            </>
          )}
          
          {step === 'complete' && (
            <Button 
              onClick={handleClose}
              className="bg-cyan-600 hover:bg-cyan-700 ml-auto"
            >
              Close
            </Button>
          )}
        </ModalFooter>
      </ModalBody>
    </Modal>
  );
};

export default CertificateRevocationDialog;
