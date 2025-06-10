import React, { useState, useEffect } from 'react';
import { cn } from '../../../utils/cn';
import {
  Heading,
  Text,
  Button,
  useToast,
  Badge,
  Card,
  CardHeader,
  CardContent,
  Input,
  Label,
  Spinner,
  FormField
} from '../../../components/ui';
import { Modal, ModalHeader, ModalBody, ModalFooter } from '../../../components/ui/Modal';
import { Alert, AlertDescription } from '../../../components/ui/Alert';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../../components/ui/Table';
import { AlertTriangle, Download, Plus, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface Certificate {
  filename: string;
  path: string;
  is_valid: boolean;
  subject?: {
    commonName?: string;
    organizationName?: string;
    countryName?: string;
  };
  issuer?: {
    commonName?: string;
    organizationName?: string;
  };
  valid_from?: string;
  valid_until?: string;
  error?: string;
}

const CertificateManager: React.FC = () => {
  const [certificates, setCertificates] = useState<Certificate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState<boolean>(false);
  
  const toast = useToast();

  useEffect(() => {
    fetchCertificates();
  }, []);

  const fetchCertificates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get('/api/crypto/certificates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      setCertificates(response.data);
      
    } catch (error: unknown) {
      console.error('Error fetching certificates:', error);
      
      const errorMsg = axios.isAxiosError(error)
        ? error.response?.data?.detail || 'Failed to fetch certificates'
        : 'Failed to fetch certificates';
      
      setError(errorMsg);
      
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };
  
  const handleUploadCertificate = async () => {
    if (!uploadFile) return;
    
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', uploadFile);
    
    try {
      const response = await axios.post('/api/crypto/certificates/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      toast({
        title: 'Success',
        description: 'Certificate uploaded successfully',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
      // Close modal and refresh certificates
      setIsUploadModalOpen(false);
      setUploadFile(null);
      fetchCertificates();
      
    } catch (error: unknown) {
      console.error('Error uploading certificate:', error);
      
      const errorMsg = axios.isAxiosError(error)
        ? error.response?.data?.detail || 'Failed to upload certificate file'
        : 'Failed to upload certificate file';
      
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setUploading(false);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    
    try {
      const date = new Date(dateStr);
      return date.toLocaleString();
    } catch (err) {
      return dateStr;
    }
  };

  const getCertificateStatus = (cert: Certificate) => {
    if (!cert.is_valid) {
      return (
        <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">
          Invalid
        </Badge>
      );
    }
    
    // Check if certificate is expired
    if (cert.valid_until) {
      const expiryDate = new Date(cert.valid_until);
      const now = new Date();
      
      if (expiryDate < now) {
        return (
          <Badge className="bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300">
            Expired
          </Badge>
        );
      }
      
      // Check if certificate is expiring soon (within 30 days)
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(thirtyDaysFromNow.getDate() + 30);
      
      if (expiryDate < thirtyDaysFromNow) {
        return (
          <Badge className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-300">
            Expiring Soon
          </Badge>
        );
      }
    }
    
    return (
      <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300">
        Valid
      </Badge>
    );
  };

  return (
    <div className="border-l-4 border-cyan-500 p-4">
      <div className="flex justify-between items-center mb-4">
        <div className="flex items-center">
          <Heading className="text-lg">Certificate Management</Heading>
          <Badge className="ml-2 bg-cyan-100 text-cyan-800">APP</Badge>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={fetchCertificates}
            disabled={loading}
            variant="outline"
            className="flex items-center gap-1"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </Button>
          <Button 
            onClick={() => setIsUploadModalOpen(true)}
            variant="default"
            className="bg-cyan-600 hover:bg-cyan-700 text-white flex items-center gap-1"
          >
            <Plus size={16} />
            Upload Certificate
          </Button>
        </div>
      </div>
      
      {loading ? (
        <div className="flex justify-center items-center h-48">
          <Spinner />
        </div>
      ) : error ? (
        <Alert variant="error">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : certificates.length === 0 ? (
        <Card className="bg-gray-50 dark:bg-gray-900">
          <CardContent className="p-4 text-center">
            <Text>No certificates found. Upload a certificate to get started.</Text>
          </CardContent>
        </Card>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Certificate</TableHead>
              <TableHead>Issued By</TableHead>
              <TableHead>Valid From</TableHead>
              <TableHead>Valid Until</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {certificates.map((cert, index) => (
              <TableRow key={index}>
                <TableCell>
                  <div>
                    <Text className="font-semibold">{cert.subject?.commonName || cert.filename}</Text>
                    <Text className="text-sm text-gray-500">{cert.filename}</Text>
                  </div>
                </TableCell>
                <TableCell>{cert.issuer?.organizationName || cert.issuer?.commonName || 'N/A'}</TableCell>
                <TableCell>{formatDate(cert.valid_from)}</TableCell>
                <TableCell>{formatDate(cert.valid_until)}</TableCell>
                <TableCell>{getCertificateStatus(cert)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
      
      {/* Upload Dialog */}
      <Modal 
        isOpen={isUploadModalOpen} 
        onClose={() => setIsUploadModalOpen(false)}
        size="lg"
      >
        <ModalHeader>
          Upload Certificate
        </ModalHeader>
        
        <ModalBody>
          <div className="py-4">
            <Text className="mb-4">
              Upload a cryptographic certificate (.crt, .pem, or .p12 file).
            </Text>
            <FormField className="space-y-2">
              <Label htmlFor="certificate-file">Certificate File</Label>
              <Input
                id="certificate-file"
                type="file"
                accept=".crt,.pem,.p12"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="p-1"
              />
            </FormField>
          </div>
        </ModalBody>
        
        <ModalFooter>
          <Button 
            variant="outline" 
            className="mr-2"
            onClick={() => {
              setUploadFile(null);
              setIsUploadModalOpen(false);
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={handleUploadCertificate}
            disabled={!uploadFile || uploading}
            variant="default"
          >
            {uploading ? (
              <>
                <Spinner className="mr-2" /> 
                Uploading...
              </>
            ) : 'Upload'}
          </Button>
        </ModalFooter>
      </Modal>
    </div>
  );

}

export default CertificateManager;
