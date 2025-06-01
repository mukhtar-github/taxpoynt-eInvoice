import React, { useState } from 'react';
import { cn } from '../../../utils/cn';
import {
  Button,
  Card,
  CardHeader,
  CardContent,
  CardTitle,
  CardDescription,
  Divider,
  Heading,
  Text,
  Badge,
  Spinner,
  Input,
  Label,
  Textarea,
  useToast,
  FormField
} from '../../../components/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/Tabs';
import { CheckIcon, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '../../../components/ui/Alert';
import axios from 'axios';

// Generic interface for invoice data
interface InvoiceData {
  [key: string]: any;
}

// Types for stamp data
interface StampData {
  csid: string;
  timestamp: string;
  algorithm: string;
  qr_code?: string;
  certificate_id?: string;
}

// Types for verification results
interface VerificationResult {
  is_valid: boolean;
  details?: {
    verified_at?: string;
    certificate_status?: string;
    [key: string]: any;
  };
  error?: string;
}

const CryptoStamping: React.FC = () => {
  // State for the generate stamp tab
  const [invoiceData, setInvoiceData] = useState<string>('');
  const [generatedStamp, setGeneratedStamp] = useState<StampData | null>(null);
  const [stampedInvoice, setStampedInvoice] = useState<InvoiceData | null>(null);
  const [generating, setGenerating] = useState<boolean>(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  
  // State for the verify stamp tab
  const [verifyInvoiceData, setVerifyInvoiceData] = useState<string>('');
  const [verifyStampData, setVerifyStampData] = useState<string>('');
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [verifying, setVerifying] = useState<boolean>(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  
  const toast = useToast();
  
  // Generate a cryptographic stamp
  const handleGenerateStamp = async () => {
    if (!invoiceData) {
      toast({
        title: 'No data provided',
        description: 'Please enter invoice data to stamp',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    try {
      // Validate JSON
      const parsedInvoice = JSON.parse(invoiceData);
      
      // Reset states
      setGenerating(true);
      setGenerateError(null);
      setGeneratedStamp(null);
      setStampedInvoice(null);
      
      // Call API to generate stamp
      const response = await axios.post('/api/crypto/generate-stamp', {
        invoice_data: parsedInvoice
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Set results
      setGeneratedStamp(response.data.stamp_info);
      setStampedInvoice(response.data.stamped_invoice);
      
      toast({
        title: 'Stamp generated',
        description: 'Cryptographic stamp successfully generated',
        status: 'success',
        duration: 5000,
        isClosable: true,
      });
      
    } catch (err) {
      console.error('Error generating stamp:', err);
      
      // Set error message
      const errorMsg = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to generate cryptographic stamp'
        : 'Failed to generate cryptographic stamp';
      setGenerateError(errorMsg);
      
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setGenerating(false);
    }
  };
  
  // Verify a cryptographic stamp
  const handleVerifyStamp = async () => {
    if (!verifyInvoiceData || !verifyStampData) {
      toast({
        title: 'Missing data',
        description: 'Please provide both invoice data and stamp data',
        status: 'warning',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    
    try {
      // Validate JSON
      const parsedInvoice = JSON.parse(verifyInvoiceData);
      const parsedStamp = JSON.parse(verifyStampData);
      
      // Reset states
      setVerifying(true);
      setVerifyError(null);
      setVerificationResult(null);
      
      // Call API to verify stamp
      const response = await axios.post('/api/crypto/verify-stamp', {
        invoice_data: parsedInvoice,
        stamp_data: parsedStamp
      }, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Set results
      setVerificationResult(response.data);
      
      // Show success/failure toast
      if (response.data.is_valid) {
        toast({
          title: 'Verification successful',
          description: 'The cryptographic stamp is valid',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } else {
        toast({
          title: 'Verification failed',
          description: 'The cryptographic stamp is not valid',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
      
    } catch (err) {
      console.error('Error verifying stamp:', err);
      
      // Set error message
      const errorMsg = axios.isAxiosError(err)
        ? err.response?.data?.detail || 'Failed to verify cryptographic stamp'
        : 'Failed to verify cryptographic stamp';
      setVerifyError(errorMsg);
      
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setVerifying(false);
    }
  };
  
  // Helper to format JSON for display
  const formatJson = (jsonObj: any): string => {
    return JSON.stringify(jsonObj, null, 2);
  };
  
  return (
    <div className="border-l-4 border-cyan-500 p-4">
      <div className="flex items-center mb-4">
        <Heading className="text-lg">Cryptographic Stamping</Heading>
        <Badge className="ml-2 bg-cyan-100 text-cyan-800">Platform</Badge>
      </div>
      
      <Tabs defaultValue="generate" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="generate">Generate Stamp</TabsTrigger>
          <TabsTrigger value="verify">Verify Stamp</TabsTrigger>
        </TabsList>
          {/* Generate Stamp Tab */}
          <TabsContent value="generate">
            <div className="space-y-4">
              <FormField className="space-y-2">
                <Label htmlFor="invoice-data">Invoice Data (JSON)</Label>
                <Textarea
                  id="invoice-data"
                  value={invoiceData}
                  onChange={(e) => setInvoiceData(e.target.value)}
                  placeholder='{"invoice_number": "INV-001", "date": "2023-10-15", ...}'
                  className="h-48 font-mono"
                />
              </FormField>
              
              <Button
                className="bg-cyan-600 hover:bg-cyan-700 text-white w-full sm:w-auto"
                onClick={handleGenerateStamp}
                disabled={generating}
              >
                {generating ? (
                  <>
                    <Spinner size="sm" className="mr-2" />
                    Generating...
                  </>
                ) : 'Generate Cryptographic Stamp'}
              </Button>
              
              {generateError && (
                <Alert variant="error">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertDescription>Error: {generateError}</AlertDescription>
                </Alert>
              )}
              
              {verificationResult && (
                <Card className={cn(
                  "border-2",
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
                        Verification {verificationResult.is_valid ? "Successful" : "Failed"}
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {verificationResult.details && (
                      <div className="space-y-3">
                        {verificationResult.details.verified_at && (
                          <div className="flex items-center gap-2">
                            <Text className="font-semibold">Verified At:</Text>
                            <Text>{verificationResult.details.verified_at}</Text>
                          </div>
                        )}
                        
                        {verificationResult.details.certificate_status && (
                          <div className="flex items-center gap-2">
                            <Text className="font-semibold">Certificate Status:</Text>
                            <Badge className={cn(
                              verificationResult.details.certificate_status === "valid" 
                                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300" 
                                : "bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300"
                            )}>
                              {verificationResult.details.certificate_status}
                            </Badge>
                          </div>
                        )}
                        
                        {/* Display any additional details */}
                        {Object.keys(verificationResult.details).filter(
                          key => !["verified_at", "certificate_status"].includes(key)
                        ).map((key) => (
                          <div className="flex items-center gap-2" key={key}>
                            <Text className="font-semibold">{key}:</Text>
                            <Text className="break-all">
                              {typeof verificationResult.details![key] === 'object' 
                                ? JSON.stringify(verificationResult.details![key]) 
                                : String(verificationResult.details![key])
                              }
                            </Text>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>
      </Tabs>
    </div>
  );
};

export default CryptoStamping;
