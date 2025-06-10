import React, { useState } from 'react';
import { AlertCircle, Check, ChevronRight, FileCheck, FileCog, Upload, X } from 'lucide-react';
import axios from 'axios';

import { Button } from '../../ui/Button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../../ui/Card';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../ui/Tabs';
import { Badge } from '../../ui/Badge';
import { Textarea } from '../../ui/Textarea';
import { Input } from '../../ui/Input';

/**
 * Signature verification tool for debugging and validation
 * 
 * Allows for:
 * - Pasting invoice JSON with signature
 * - Uploading signed invoice files
 * - Displaying detailed verification results
 * - Examining signature properties and algorithm details
 */
const SignatureVerificationTool: React.FC = () => {
  const [verificationState, setVerificationState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string>('');
  const [invoiceJson, setInvoiceJson] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Handle JSON verification
  const handleVerifyJson = async () => {
    if (!invoiceJson.trim()) {
      setErrorMessage('Please enter JSON data to verify');
      setVerificationState('error');
      return;
    }

    setVerificationState('loading');
    setErrorMessage('');
    
    try {
      // Parse the JSON to validate format
      const invoiceData = JSON.parse(invoiceJson);
      
      // Check if the invoice has a signature or CSID
      if (!invoiceData.csid && !invoiceData.signature && !invoiceData.cryptographic_stamp) {
        setErrorMessage('No signature or CSID found in the provided JSON');
        setVerificationState('error');
        return;
      }
      
      // Send to API for verification
      const response = await axios.post('/api/platform/signatures/verify', invoiceData);
      setVerificationResult(response.data);
      setVerificationState('success');
    } catch (error) {
      setVerificationState('error');
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.detail || 'Failed to verify signature');
      } else if (error instanceof Error) {
        setErrorMessage(`Error: ${error.message}`);
      } else {
        setErrorMessage('An unknown error occurred during verification');
      }
    }
  };

  // Handle file upload verification
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
    }
  };

  const handleVerifyFile = async () => {
    if (!selectedFile) {
      setErrorMessage('Please select a file to verify');
      setVerificationState('error');
      return;
    }

    setVerificationState('loading');
    setErrorMessage('');
    
    try {
      // Create form data for file upload
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Send to API for verification
      const response = await axios.post('/api/platform/signatures/verify-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setVerificationResult(response.data);
      setVerificationState('success');
    } catch (error) {
      setVerificationState('error');
      if (axios.isAxiosError(error)) {
        setErrorMessage(error.response?.data?.detail || 'Failed to verify file');
      } else if (error instanceof Error) {
        setErrorMessage(`Error: ${error.message}`);
      } else {
        setErrorMessage('An unknown error occurred during verification');
      }
    }
  };

  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            Signature Verification Tool
          </CardTitle>
          <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
            APP
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="json">
          <TabsList className="mb-4">
            <TabsTrigger value="json" className="flex items-center gap-2">
              <FileCog size={16} />
              JSON Input
            </TabsTrigger>
            <TabsTrigger value="file" className="flex items-center gap-2">
              <Upload size={16} />
              File Upload
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="json">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground mb-2">
                  Paste the signed invoice JSON data below
                </p>
                <Textarea 
                  placeholder="Paste JSON here..." 
                  className="font-mono h-40"
                  value={invoiceJson}
                  onChange={(e) => setInvoiceJson(e.target.value)}
                />
              </div>
              <Button 
                variant="default" 
                onClick={handleVerifyJson} 
                disabled={verificationState === 'loading'}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                {verificationState === 'loading' ? 'Verifying...' : 'Verify Signature'}
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="file">
            <div className="space-y-4">
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <Input 
                  type="file" 
                  onChange={handleFileChange}
                  className="hidden" 
                  id="file-upload"
                />
                <label 
                  htmlFor="file-upload" 
                  className="cursor-pointer flex flex-col items-center justify-center"
                >
                  <Upload className="h-10 w-10 text-gray-400 mb-2" />
                  <p className="text-sm font-medium">
                    {selectedFile ? selectedFile.name : 'Select a file or drag and drop'}
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    JSON or XML invoice file with signature
                  </p>
                </label>
              </div>
              
              <Button 
                variant="default" 
                onClick={handleVerifyFile}
                disabled={!selectedFile || verificationState === 'loading'}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                {verificationState === 'loading' ? 'Verifying...' : 'Verify File'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Error message */}
        {verificationState === 'error' && (
          <Alert variant="error" className="mt-4">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Verification Failed</AlertTitle>
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}
        
        {/* Verification results */}
        {verificationState === 'success' && verificationResult && (
          <div className="mt-4 space-y-4">
            <Alert 
              variant={verificationResult.is_valid ? "success" : "error"}
              className="bg-opacity-50"
            >
              {verificationResult.is_valid ? (
                <Check className="h-4 w-4" />
              ) : (
                <X className="h-4 w-4" />
              )}
              <AlertTitle>
                {verificationResult.is_valid ? 'Signature Verified' : 'Invalid Signature'}
              </AlertTitle>
              <AlertDescription>
                {verificationResult.message}
              </AlertDescription>
            </Alert>
            
            {/* Detailed verification info */}
            <div className="border rounded-md divide-y">
              <div className="p-3 bg-gray-50">
                <h3 className="font-medium">Signature Details</h3>
              </div>
              
              <div className="p-3 flex justify-between">
                <span className="text-sm font-medium">Algorithm</span>
                <span className="text-sm">{verificationResult.details?.algorithm || 'Not specified'}</span>
              </div>
              
              <div className="p-3 flex justify-between">
                <span className="text-sm font-medium">Version</span>
                <span className="text-sm">{verificationResult.details?.version || 'Not specified'}</span>
              </div>
              
              <div className="p-3 flex justify-between">
                <span className="text-sm font-medium">Timestamp</span>
                <span className="text-sm">{verificationResult.details?.timestamp || 'Not specified'}</span>
              </div>
              
              {verificationResult.details?.key_info && (
                <div className="p-3 flex justify-between">
                  <span className="text-sm font-medium">Key ID</span>
                  <span className="text-sm">{verificationResult.details.key_info.key_id}</span>
                </div>
              )}
              
              {verificationResult.details?.signature_id && (
                <div className="p-3 flex justify-between">
                  <span className="text-sm font-medium">Signature ID</span>
                  <span className="text-sm">{verificationResult.details.signature_id}</span>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between border-t pt-4 text-xs text-gray-500">
        <div className="flex items-center">
          <FileCheck className="h-3 w-3 mr-1" />
          TaxPoynt APP Signature Verification
        </div>
        
        <a href="/documentation/signatures" className="flex items-center hover:text-cyan-600">
          View documentation
          <ChevronRight className="h-3 w-3 ml-1" />
        </a>
      </CardFooter>
    </Card>
  );
};

export default SignatureVerificationTool;
