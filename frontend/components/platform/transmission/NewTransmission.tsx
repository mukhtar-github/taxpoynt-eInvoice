import React, { useState } from 'react';
import { useToast } from '@/components/ui/Toast';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Input } from '@/components/ui/Input';
import { Label } from '@/components/ui/Label';
import { Textarea } from '@/components/ui/Textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { Loader2, Send, Shield, Upload, FileUp } from 'lucide-react';
import axios from 'axios';

interface NewTransmissionProps {
  organizationId: string;
  certificates: Array<{
    id: string;
    name: string;
    status: string;
  }>;
  onTransmissionCreated?: () => void;
}

const NewTransmission: React.FC<NewTransmissionProps> = ({ 
  organizationId, 
  certificates, 
  onTransmissionCreated 
}) => {
  const toast = useToast();
  const [loading, setLoading] = useState<boolean>(false);
  const [selectedCertificate, setSelectedCertificate] = useState<string>('');
  const [payloadType, setPayloadType] = useState<'json' | 'file'>('json');
  const [jsonPayload, setJsonPayload] = useState<string>('');
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const validateJsonPayload = (jsonString: string): boolean => {
    try {
      JSON.parse(jsonString);
      return true;
    } catch (e) {
      return false;
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setLoading(true);

    try {
      // Validate inputs
      if (payloadType === 'json' && !jsonPayload.trim()) {
        throw new Error('JSON payload is required');
      }

      if (payloadType === 'json' && !validateJsonPayload(jsonPayload)) {
        throw new Error('Invalid JSON format');
      }

      if (payloadType === 'file' && !file) {
        throw new Error('Please select a file to upload');
      }

      const token = localStorage.getItem('token');
      let transmissionData;

      if (payloadType === 'json') {
        // Send JSON payload
        transmissionData = {
          payload: JSON.parse(jsonPayload),
          organization_id: organizationId,
          certificate_id: selectedCertificate || undefined,
          metadata: {
            source: 'manual_submission',
            content_type: 'application/json'
          }
        };

        const response = await axios.post('/api/v1/firs/transmit', transmissionData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        toast({
          title: 'Success',
          description: 'Transmission initiated successfully',
          status: 'success',
        });

        // Reset form
        setJsonPayload('');
        setSelectedCertificate('');

        // Notify parent component
        if (onTransmissionCreated) {
          onTransmissionCreated();
        }
      } else {
        // Send file payload
        const formData = new FormData();
        formData.append('file', file as File);
        formData.append('organization_id', organizationId);
        
        if (selectedCertificate) {
          formData.append('certificate_id', selectedCertificate);
        }

        const response = await axios.post('/api/v1/firs/transmit-file', formData, {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });

        toast({
          title: 'Success',
          description: 'File transmission initiated successfully',
          status: 'success',
        });

        // Reset form
        setFile(null);
        setSelectedCertificate('');

        // Notify parent component
        if (onTransmissionCreated) {
          onTransmissionCreated();
        }
      }
    } catch (err) {
      if (axios.isAxiosError(err)) {
        const errorMsg = err.response?.data?.detail || 'Failed to create transmission';
        setError(errorMsg);
        toast({
          title: 'Error',
          description: errorMsg,
          status: 'error',
        });
      } else if (err instanceof Error) {
        setError(err.message);
        toast({
          title: 'Error',
          description: err.message,
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

  return (
    <Card className="border-l-4 border-cyan-500">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>New Secure Transmission</CardTitle>
            <CardDescription>Create and send secure data to FIRS</CardDescription>
          </div>
          <Badge variant="outline" className="border-cyan-500 text-cyan-500">
            <Shield className="w-3 h-3 mr-1" /> Platform
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <Alert variant="error" className="mb-4">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="space-y-4">
          <div>
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

          <div>
            <Label htmlFor="payloadType">Payload Type</Label>
            <div className="flex gap-4 mt-1">
              <Button
                type="button"
                variant={payloadType === 'json' ? 'default' : 'outline'}
                onClick={() => setPayloadType('json')}
              >
                JSON Payload
              </Button>
              <Button
                type="button"
                variant={payloadType === 'file' ? 'default' : 'outline'}
                onClick={() => setPayloadType('file')}
              >
                File Upload
              </Button>
            </div>
          </div>

          {payloadType === 'json' ? (
            <div>
              <Label htmlFor="jsonPayload">JSON Payload</Label>
              <Textarea
                id="jsonPayload"
                value={jsonPayload}
                onChange={(e) => setJsonPayload(e.target.value)}
                placeholder='{
  "invoice_number": "INV-2025-0001",
  "issue_date": "2025-06-01",
  "supplier": {
    "name": "TaxPoynt Demo Ltd",
    "tax_id": "1234567890"
  },
  "items": []
}'
                className="font-mono h-64"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter valid JSON that conforms to the FIRS e-Invoice schema
              </p>
            </div>
          ) : (
            <div>
              <Label htmlFor="fileUpload">Upload File</Label>
              <div className="border-2 border-dashed border-gray-300 rounded-md p-6 mt-1">
                <div className="flex flex-col items-center justify-center text-center">
                  <FileUp className="h-8 w-8 text-gray-400 mb-2" />
                  <p className="text-sm text-gray-500 mb-2">
                    Drag and drop a file here, or click to select a file
                  </p>
                  <Input
                    id="fileUpload"
                    type="file"
                    onChange={handleFileChange}
                    className="mt-2"
                  />
                  {file && (
                    <p className="text-sm text-cyan-600 mt-2">
                      Selected: {file.name} ({Math.round(file.size / 1024)} KB)
                    </p>
                  )}
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Supported formats: JSON, XML, PDF (max 10MB)
              </p>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex justify-end">
        <Button onClick={handleSubmit} disabled={loading}>
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
      </CardFooter>
    </Card>
  );
};

export default NewTransmission;
