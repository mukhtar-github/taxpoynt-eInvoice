import React, { useState } from 'react';
import { Shield, CheckCircle, XCircle, AlertTriangle, ChevronRight, UploadCloud } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Alert, AlertDescription } from '../ui/Alert';
import { Badge } from '../ui/Badge';
import { Textarea } from '../ui/Textarea';
import { Input } from '../ui/Input';
import apiService from '../../utils/apiService';
import { cn } from '../../utils/cn';

interface ValidationResultItem {
  subject: string;
  issuer: string;
  validFrom: string;
  validTo: string;
  status: 'valid' | 'expired' | 'revoked' | 'unknown' | 'invalid';
  isRoot: boolean;
  errors?: string[];
  warnings?: string[];
}

interface ValidationResult {
  isValid: boolean;
  chainComplete: boolean;
  errors: string[];
  warnings: string[];
  certificates: ValidationResultItem[];
}

interface CertificateChainValidationProps {
  organizationId: string;
  className?: string;
}

/**
 * Certificate Chain Validation Component
 * 
 * Validates certificate trust chains for authenticity and integrity,
 * displaying detailed results about certificate hierarchy and trust status.
 */
const CertificateChainValidation: React.FC<CertificateChainValidationProps> = ({
  organizationId,
  className = ''
}) => {
  const [validationMethod, setValidationMethod] = useState<'upload' | 'paste'>('upload');
  const [certificateText, setCertificateText] = useState<string>('');
  const [certificateFile, setCertificateFile] = useState<File | null>(null);
  const [validating, setValidating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  
  // Handle file selection
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setCertificateFile(files[0]);
      setError(null);
    }
  };
  
  // Handle certificate text change
  const handleCertificateTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setCertificateText(e.target.value);
    setError(null);
  };
  
  // Get status badge for certificate
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'valid':
        return <Badge className="bg-green-100 text-green-800">Valid</Badge>;
      case 'expired':
        return <Badge className="bg-orange-100 text-orange-800">Expired</Badge>;
      case 'revoked':
        return <Badge className="bg-red-100 text-red-800">Revoked</Badge>;
      case 'invalid':
        return <Badge className="bg-red-100 text-red-800">Invalid</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };
  
  // Get status icon for certificate
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'valid':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'expired':
        return <AlertTriangle className="h-5 w-5 text-orange-500" />;
      case 'revoked':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'invalid':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };
  
  // Format date nicely
  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = {
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };
  
  // Start validation process
  const handleValidate = async () => {
    setError(null);
    setValidating(true);
    setValidationResult(null);
    
    try {
      let response;
      
      if (validationMethod === 'upload' && certificateFile) {
        // Create form data for file upload
        const formData = new FormData();
        formData.append('file', certificateFile);
        formData.append('organization_id', organizationId);
        
        response = await apiService.post('/api/v1/certificates/validate-chain/file', formData);
      } else if (validationMethod === 'paste' && certificateText.trim()) {
        // Send certificate text
        response = await apiService.post('/api/v1/certificates/validate-chain/text', {
          certificate_text: certificateText,
          organization_id: organizationId
        });
      } else {
        throw new Error('Please provide a certificate file or paste certificate content');
      }
      
      setValidationResult(response.data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to validate certificate chain. Please try again.'
      );
    } finally {
      setValidating(false);
    }
  };
  
  // Clear and reset form
  const handleClear = () => {
    setCertificateFile(null);
    setCertificateText('');
    setError(null);
    setValidationResult(null);
    
    // Also reset file input
    const fileInput = document.getElementById('certificate-file') as HTMLInputElement;
    if (fileInput) {
      fileInput.value = '';
    }
  };
  
  return (
    <Card className={cn('border-l-4 border-cyan-500', className)}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center">
          <Shield className="h-5 w-5 mr-2 text-cyan-500" />
          Certificate Chain Validation
        </CardTitle>
      </CardHeader>
      <CardContent>
        {validationResult ? (
          // Validation results
          <div>
            {/* Overall Result */}
            <div className={cn(
              "p-4 rounded-md mb-4 text-center",
              validationResult.isValid 
                ? "bg-green-50 border border-green-200" 
                : "bg-red-50 border border-red-200"
            )}>
              <div className="flex justify-center mb-2">
                <div className={cn(
                  "p-2 rounded-full",
                  validationResult.isValid ? "bg-green-100" : "bg-red-100"
                )}>
                  {validationResult.isValid 
                    ? <CheckCircle className="h-6 w-6 text-green-600" />
                    : <XCircle className="h-6 w-6 text-red-600" />
                  }
                </div>
              </div>
              
              <h3 className={cn(
                "text-lg font-medium mb-1",
                validationResult.isValid ? "text-green-800" : "text-red-800"
              )}>
                {validationResult.isValid 
                  ? "Certificate Chain is Valid" 
                  : "Certificate Chain Validation Failed"
                }
              </h3>
              
              {validationResult.chainComplete && validationResult.isValid ? (
                <p className="text-green-600">
                  Chain is complete and trusted
                </p>
              ) : validationResult.isValid ? (
                <p className="text-amber-600">
                  Chain is valid but {!validationResult.chainComplete && "incomplete"}
                </p>
              ) : (
                <p className="text-red-600">
                  Chain validation failed
                </p>
              )}
            </div>
            
            {/* Errors and Warnings */}
            {validationResult.errors.length > 0 && (
              <Alert variant="error" className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <div>
                  <AlertDescription>
                    <strong>Errors:</strong>
                    <ul className="list-disc pl-5 mt-1">
                      {validationResult.errors.map((err, i) => (
                        <li key={i}>{err}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </div>
              </Alert>
            )}
            
            {validationResult.warnings.length > 0 && (
              <Alert className="mb-4 bg-amber-50 border-amber-200">
                <AlertTriangle className="h-4 w-4 text-amber-500" />
                <div>
                  <AlertDescription className="text-amber-800">
                    <strong>Warnings:</strong>
                    <ul className="list-disc pl-5 mt-1">
                      {validationResult.warnings.map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </div>
              </Alert>
            )}
            
            {/* Certificate Chain */}
            <div className="mb-4">
              <h3 className="text-md font-medium mb-2">Certificate Chain</h3>
              
              <div className="border border-gray-200 rounded-md">
                {validationResult.certificates.map((cert, index, array) => (
                  <div 
                    key={index} 
                    className={cn(
                      "p-3 border-b border-gray-200 flex items-start",
                      index === array.length - 1 && "border-b-0",
                      cert.status === 'valid' ? "bg-green-50" : "bg-gray-50"
                    )}
                  >
                    <div className="mr-3 mt-1">
                      {getStatusIcon(cert.status)}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <div className="font-medium truncate mr-2">{cert.subject}</div>
                        {getStatusBadge(cert.status)}
                      </div>
                      
                      <div className="text-sm text-gray-500 mb-1">
                        Issued by: {cert.issuer}
                      </div>
                      
                      <div className="text-xs text-gray-500 flex flex-wrap gap-x-4">
                        <span>Valid from: {formatDate(cert.validFrom)}</span>
                        <span>Valid to: {formatDate(cert.validTo)}</span>
                      </div>
                      
                      {((cert.errors && cert.errors.length > 0) || (cert.warnings && cert.warnings.length > 0)) && (
                        <div className="mt-2 text-sm">
                          {cert.errors && cert.errors.length > 0 && (
                            <div className="text-red-600">
                              <span className="font-medium">Errors:</span>
                              <ul className="list-disc pl-5 mt-1">
                                {cert.errors && cert.errors.map((err, i) => (
                                  <li key={i}>{err}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          
                          {cert.warnings && cert.warnings.length > 0 && (
                            <div className="text-amber-600">
                              <span className="font-medium">Warnings:</span>
                              <ul className="list-disc pl-5 mt-1">
                                {cert.warnings && cert.warnings.map((warning, i) => (
                                  <li key={i}>{warning}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    
                    {index < array.length - 1 && (
                      <div className="flex justify-center items-center px-2">
                        <ChevronRight className="h-5 w-5 text-gray-400" />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex justify-end">
              <Button 
                onClick={handleClear}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                Validate Another Certificate
              </Button>
            </div>
          </div>
        ) : (
          // Validation form
          <div>
            {error && (
              <Alert variant="error" className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            {/* Validation Method Tabs */}
            <div className="flex border-b mb-4">
              <button
                className={cn(
                  "px-4 py-2 font-medium text-sm focus:outline-none",
                  validationMethod === 'upload' 
                    ? "border-b-2 border-cyan-500 text-cyan-700" 
                    : "text-gray-500 hover:text-gray-700"
                )}
                onClick={() => setValidationMethod('upload')}
              >
                Upload Certificate
              </button>
              <button
                className={cn(
                  "px-4 py-2 font-medium text-sm focus:outline-none",
                  validationMethod === 'paste' 
                    ? "border-b-2 border-cyan-500 text-cyan-700" 
                    : "text-gray-500 hover:text-gray-700"
                )}
                onClick={() => setValidationMethod('paste')}
              >
                Paste Certificate
              </button>
            </div>
            
            {/* File Upload */}
            {validationMethod === 'upload' && (
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Upload Certificate File
                </label>
                
                <div className="border-2 border-dashed border-gray-300 rounded-md p-6 text-center">
                  <Input
                    id="certificate-file"
                    type="file"
                    accept=".pem,.crt,.cer,.der"
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  
                  {certificateFile ? (
                    <div>
                      <CheckCircle className="h-8 w-8 text-green-500 mx-auto mb-2" />
                      <p className="text-sm font-medium">{certificateFile.name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {(certificateFile.size / 1024).toFixed(1)} KB
                      </p>
                      <Button 
                        variant="outline"
                        size="sm"
                        onClick={() => setCertificateFile(null)}
                        className="mt-2"
                      >
                        Change
                      </Button>
                    </div>
                  ) : (
                    <div>
                      <UploadCloud className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                      <p className="text-sm font-medium">Click to upload or drag and drop</p>
                      <p className="text-xs text-gray-500 mt-1">
                        PEM, CRT, CER, or DER files
                      </p>
                      <Button 
                        variant="outline"
                        size="sm"
                        onClick={() => document.getElementById('certificate-file')?.click()}
                        className="mt-2"
                      >
                        Select File
                      </Button>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Certificate Text */}
            {validationMethod === 'paste' && (
              <div className="mb-4">
                <label htmlFor="certificate-text" className="block text-sm font-medium mb-2">
                  Paste Certificate Content (PEM format)
                </label>
                <Textarea
                  id="certificate-text"
                  value={certificateText}
                  onChange={handleCertificateTextChange}
                  placeholder="-----BEGIN CERTIFICATE-----
MIIDXzCCAkegAwIBAgILBAAAAAABIVhTCKIwDQYJKoZIhvcNAQELBQAwTDEgMB4G
...
-----END CERTIFICATE-----"
                  className="h-48 font-mono text-sm"
                />
              </div>
            )}
            
            {/* Instructions */}
            <Alert className="mb-4 bg-blue-50 border-blue-200">
              <Shield className="h-4 w-4 text-blue-500" />
              <AlertDescription className="text-blue-800">
                <strong>What is certificate chain validation?</strong>
                <p className="mt-1">
                  Certificate chain validation verifies that a certificate is trusted by checking
                  its entire trust chain up to a trusted root certificate authority. This ensures
                  the certificate hasn't been tampered with and is from a legitimate source.
                </p>
              </AlertDescription>
            </Alert>
            
            {/* Actions */}
            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={handleClear}
                disabled={validating}
              >
                Clear
              </Button>
              <Button 
                onClick={handleValidate}
                disabled={validating || (validationMethod === 'upload' ? !certificateFile : !certificateText.trim())}
                className="bg-cyan-600 hover:bg-cyan-700"
              >
                {validating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Validating...
                  </>
                ) : (
                  <>
                    <Shield className="h-4 w-4 mr-2" />
                    Validate Chain
                  </>
                )}
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default CertificateChainValidation;
