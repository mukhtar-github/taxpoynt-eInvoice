import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShieldCheck, Info, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';
import { Badge } from '../../ui/Badge';
import { Tooltip } from '../../ui/Tooltip';
import { Alert, AlertDescription, AlertTitle } from '../../ui/Alert';
import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Button } from '../../ui/Button';
import { Spinner } from '../../ui/Spinner';

interface SignatureDetails {
  algorithm: string;
  version: string;
  timestamp: string;
  signature_id: string;
  key_info?: {
    key_id: string;
    certificate: string;
  };
}

interface VerificationResult {
  is_valid: boolean;
  message: string;
  details: SignatureDetails;
}

interface InvoiceSignatureVisualizerProps {
  invoiceData: any;
  compact?: boolean;
  onStatusChange?: (isValid: boolean) => void;
  className?: string;
}

/**
 * Invoice Signature Visualizer
 * 
 * Displays signature verification status and details for an invoice.
 * Can be used in both detailed and compact modes to integrate with
 * different invoice view contexts.
 */
const InvoiceSignatureVisualizer: React.FC<InvoiceSignatureVisualizerProps> = ({
  invoiceData,
  compact = false,
  onStatusChange,
  className = '',
}) => {
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const verifySignature = async () => {
    if (!invoiceData) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post('/api/platform/signatures/verify', invoiceData);
      setVerificationResult(response.data);
      
      // Notify parent component of status change if callback provided
      if (onStatusChange) {
        onStatusChange(response.data.is_valid);
      }
    } catch (err) {
      console.error('Error verifying signature:', err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message || 'Failed to verify signature');
      } else {
        setError('An unexpected error occurred');
      }
      
      // Notify parent of invalid status due to error
      if (onStatusChange) {
        onStatusChange(false);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Verify signature when component mounts or invoice data changes
    if (invoiceData && invoiceData.csid) {
      verifySignature();
    }
  }, [invoiceData]);

  // If no CSID is present in the invoice
  if (!invoiceData?.csid) {
    return compact ? (
      <Badge variant="outline" className="bg-gray-100 text-gray-700">
        <Info className="h-3 w-3 mr-1" /> No Signature
      </Badge>
    ) : (
      <Card className={`border-l-4 border-l-gray-400 ${className}`}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center">
            <ShieldCheck className="h-4 w-4 mr-2 text-gray-500" />
            Digital Signature
            <Badge className="ml-2 bg-gray-100 text-gray-700">Not Present</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="default" className="mt-2">
            <Info className="h-4 w-4" />
            <AlertTitle>No digital signature found</AlertTitle>
            <AlertDescription>
              This invoice does not contain a digital signature or CSID.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Loading state
  if (loading) {
    return compact ? (
      <Badge className="bg-blue-100 text-blue-800">
        <Spinner size="xs" className="mr-1" /> Verifying...
      </Badge>
    ) : (
      <Card className={`border-l-4 border-l-blue-500 ${className}`}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center">
            <ShieldCheck className="h-4 w-4 mr-2 text-blue-500" />
            Digital Signature
            <Badge className="ml-2 bg-blue-100 text-blue-800">Verifying</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-2">
            <Spinner className="text-blue-500" />
            <span className="ml-2 text-sm text-gray-600">Verifying signature...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return compact ? (
      <Badge variant="destructive">
        <AlertCircle className="h-3 w-3 mr-1" /> Verification Error
      </Badge>
    ) : (
      <Card className={`border-l-4 border-l-red-500 ${className}`}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center">
            <ShieldCheck className="h-4 w-4 mr-2 text-red-500" />
            Digital Signature
            <Badge variant="destructive" className="ml-2">Error</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="error">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Verification Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="mt-2 flex justify-end">
            <Button size="sm" variant="outline" onClick={verifySignature}>
              <RefreshCw className="h-3 w-3 mr-1" /> Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Valid signature
  if (verificationResult?.is_valid) {
    return compact ? (
      <Tooltip content={`Verified: ${verificationResult.details.algorithm}, ${verificationResult.details.version}`}>
        <Badge className="bg-green-100 text-green-800">
          <CheckCircle className="h-3 w-3 mr-1" /> Signature Valid
        </Badge>
      </Tooltip>
    ) : (
      <Card className={`border-l-4 border-l-green-500 ${className}`}>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium flex items-center">
            <ShieldCheck className="h-4 w-4 mr-2 text-green-500" />
            Digital Signature
            <Badge className="ml-2 bg-green-100 text-green-800">Valid</Badge>
            <Badge className="ml-2 bg-cyan-100 text-cyan-800">Platform</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div className="text-gray-500">Algorithm</div>
            <div className="font-medium">{verificationResult.details.algorithm}</div>
            
            <div className="text-gray-500">Version</div>
            <div className="font-medium">{verificationResult.details.version}</div>
            
            <div className="text-gray-500">Timestamp</div>
            <div className="font-medium">{new Date(verificationResult.details.timestamp).toLocaleString()}</div>
            
            <div className="text-gray-500">Signature ID</div>
            <div className="font-medium">{verificationResult.details.signature_id}</div>
            
            {verificationResult.details.key_info && (
              <>
                <div className="text-gray-500">Key ID</div>
                <div className="font-medium">{verificationResult.details.key_info.key_id}</div>
              </>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Invalid signature
  return compact ? (
    <Tooltip content={verificationResult?.message || 'Invalid signature'}>
      <Badge variant="destructive">
        <AlertCircle className="h-3 w-3 mr-1" /> Invalid Signature
      </Badge>
    </Tooltip>
  ) : (
    <Card className={`border-l-4 border-l-red-500 ${className}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium flex items-center">
          <ShieldCheck className="h-4 w-4 mr-2 text-red-500" />
          Digital Signature
          <Badge variant="destructive" className="ml-2">Invalid</Badge>
          <Badge className="ml-2 bg-cyan-100 text-cyan-800">Platform</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <Alert variant="error" className="mb-3">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Invalid Signature</AlertTitle>
          <AlertDescription>{verificationResult?.message}</AlertDescription>
        </Alert>
        
        {verificationResult?.details && (
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm mt-3">
            <div className="text-gray-500">Algorithm</div>
            <div className="font-medium">{verificationResult.details.algorithm}</div>
            
            <div className="text-gray-500">Version</div>
            <div className="font-medium">{verificationResult.details.version}</div>
          </div>
        )}
        
        <div className="mt-3 flex justify-end">
          <Button size="sm" variant="outline" onClick={verifySignature}>
            <RefreshCw className="h-3 w-3 mr-1" /> Retry Verification
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};

export default InvoiceSignatureVisualizer;
