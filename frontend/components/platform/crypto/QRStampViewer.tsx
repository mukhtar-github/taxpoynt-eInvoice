import React, { useState, useRef } from 'react';
import { cn } from '../../../utils/cn';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  Heading,
  Text,
  Badge,
  Spinner,
  useToast,
} from '../../../components/ui';
import { Modal, ModalHeader, ModalBody, ModalFooter } from '../../../components/ui/Modal';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/Table';
import { Alert, AlertDescription } from '../../../components/ui/Alert';
import { CheckIcon, AlertTriangle, Plus, Upload } from 'lucide-react';
import axios, { AxiosError } from 'axios';

interface QRVerificationResult {
  is_valid: boolean;
  csid?: string;
  timestamp?: string;
  invoice_number?: string;
  issuer?: string;
  error?: string;
  [key: string]: any;
}

const QRStampViewer: React.FC = () => {
  // State for QR code upload
  const [qrImage, setQrImage] = useState<string | null>(null);
  const [qrFile, setQrFile] = useState<File | null>(null);
  const [verificationResult, setVerificationResult] = useState<QRVerificationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // Modal for showing invoice details
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
  const [invoiceDetails, setInvoiceDetails] = useState<any>(null);
  
  // File input ref
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const toast = useToast();
  
  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Check if file is an image
    if (!file.type.match('image.*')) {
      toast({
        title: 'Invalid file type',
        description: 'Please select an image file (JPEG, PNG, etc.)',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setQrFile(file);
    
    // Display image preview
    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setQrImage(result);
    };
    reader.readAsDataURL(file);
    
    // Reset previous results
    setVerificationResult(null);
    setError(null);
  };
  
  // Verify QR code
  const verifyQRCode = async () => {
    if (!qrFile) {
      toast({
        title: 'No QR code',
        description: 'Please upload a QR code image first',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    setLoading(true);
    setError(null);
    setVerificationResult(null);
    
    // Create form data
    const formData = new FormData();
    formData.append('qr_file', qrFile);
    
    try {
      const response = await axios.post('/api/crypto/verify-qr-stamp', formData, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      setVerificationResult(response.data);
      
      // Show success/failure toast
      if (response.data.is_valid) {
        toast({
          title: 'Verification successful',
          description: 'The QR stamp is valid',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'Verification failed',
          description: response.data.error || 'The QR stamp is not valid',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
      
    } catch (error: unknown) {
      console.error('Error verifying QR code:', error);
      const errorMsg = axios.isAxiosError(error)
        ? error.response?.data?.detail || 'Failed to verify QR code'
        : 'Failed to verify QR code';
      setError(errorMsg);
      
      toast({
        title: 'Error',
        description: 'Failed to verify QR code',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Get invoice details from verification result
  const getInvoiceDetails = async () => {
    if (!verificationResult?.csid) {
      toast({
        title: 'No CSID available',
        description: 'Cannot retrieve invoice details without a valid CSID',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    try {
      const response = await axios.get(`/api/crypto/invoice-by-csid/${verificationResult.csid}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setInvoiceDetails(response.data.invoice_data);
      setIsModalOpen(true); // Open modal with invoice details
      
    } catch (error: unknown) {
      console.error('Error fetching invoice details:', error);
      
      toast({
        title: 'Error',
        description: axios.isAxiosError(error)
          ? error.response?.data?.detail || 'Failed to fetch invoice details'
          : 'Failed to fetch invoice details',
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    }
  };
  
  return (
    <div className="border-l-4 border-cyan-500 p-4">
      <div className="flex items-center mb-4">
        <Heading className="text-lg">QR Stamp Viewer & Verification</Heading>
        <Badge className="ml-2 bg-cyan-100 text-cyan-800">APP</Badge>
      </div>
      
      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="text-base">Upload QR Code</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept="image/*"
              className="hidden"
            />
            <Button 
              onClick={() => fileInputRef.current?.click()}
              size="default"
              variant="default"
              className="flex items-center gap-1 mb-2"
            >
              <Upload size={16} /> 
              Select QR Code Image
            </Button>
            <Text className="text-sm text-gray-500">
              Upload a QR code image from a FIRS cryptographically stamped invoice
            </Text>
          </div>
          
          {qrImage && (
            <div>
              <Text className="font-semibold mb-2">Preview:</Text>
              <img 
                src={qrImage} 
                alt="QR Code" 
                className="h-[150px] w-[150px] object-contain border border-gray-200 dark:border-gray-700 rounded-md"
              />
            </div>
          )}
            
          <Button
            onClick={verifyQRCode}
            disabled={loading || !qrFile}
            variant="default"
            className="bg-cyan-600 hover:bg-cyan-700 text-white w-full sm:w-auto"
          >
            {loading ? (
              <>
                <Spinner size="sm" className="mr-2" />
                Verifying...
              </>
            ) : 'Verify QR Code'}
          </Button>
          
          {error && (
            <Alert variant="error">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>Error: {error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
      
      {verificationResult && (
        <Card className={cn(
          "mb-4 border-2",
          verificationResult.is_valid 
            ? "border-green-500 bg-green-50 dark:bg-green-950" 
            : "border-red-500 bg-red-50 dark:bg-red-950"
        )}>
          <CardHeader>
            <div className="flex items-center">
              {verificationResult.is_valid ? (
                <CheckIcon className="text-green-500 mr-2 h-5 w-5" />
              ) : (
                <AlertTriangle className="text-red-500 mr-2 h-5 w-5" />
              )}
              <CardTitle className="text-base">
                QR Code Verification {verificationResult.is_valid ? "Successful" : "Failed"}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {verificationResult.is_valid ? (
              <>
                {verificationResult.csid && (
                  <div className="flex items-center gap-2">
                    <Text className="font-semibold">CSID:</Text>
                    <Text className="font-mono text-sm">
                      {verificationResult.csid.substring(0, 15)}...
                    </Text>
                  </div>
                )}
                
                {/* Only show issuer if it exists */}
                {verificationResult.issuer && (
                  <div className="flex items-center gap-2">
                    <Text className="font-semibold">Issuer:</Text>
                    <Text>{verificationResult.issuer}</Text>
                  </div>
                )}
                
                {verificationResult.timestamp && (
                  <div className="flex items-center gap-2">
                    <Text className="font-semibold">Timestamp:</Text>
                    <Text>{verificationResult.timestamp}</Text>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <Text className="font-semibold">Status:</Text>
                  <Badge className={cn(
                    verificationResult.is_valid 
                      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300" 
                      : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                  )}>
                    {verificationResult.is_valid ? "Valid" : "Invalid"}
                  </Badge>
                </div>
                
                {verificationResult.error && (
                  <div>
                    <Text className="font-semibold text-red-600">Error:</Text>
                    <Text className="text-red-600">{verificationResult.error}</Text>
                  </div>
                )}
              </>
            ) : (
              <Text className="text-red-600">
                {verificationResult.error || "The QR code is not a valid FIRS cryptographic stamp."}
              </Text>
            )}
            
            {verificationResult.is_valid && verificationResult.csid && (
              <Button
                onClick={getInvoiceDetails}
                variant="default"
                className="bg-cyan-600 hover:bg-cyan-700 text-white"
              >
                View Invoice Details
              </Button>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Invoice Details Modal */}
      <Modal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)}
        size="4xl"
      >
        <ModalHeader>
          <Heading className="text-lg">Invoice Details</Heading>
        </ModalHeader>
        
        <ModalBody>
          {invoiceDetails && (
            <>
              <Text className="mb-4">
                Below are the details of the invoice associated with the scanned QR code:
              </Text>
              
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Field</TableHead>
                    <TableHead>Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(invoiceDetails).map(([key, value]) => (
                    <TableRow key={key}>
                      <TableCell className="font-semibold">{key}</TableCell>
                      <TableCell className="break-all">
                        {typeof value === 'object' 
                          ? JSON.stringify(value)
                          : String(value)
                        }
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          )}
        </ModalBody>
        
        <ModalFooter>
          <Button 
            onClick={() => setIsModalOpen(false)}
            variant="default"
          >
            Close
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );
};

export default QRStampViewer;
