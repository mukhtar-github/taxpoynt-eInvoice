import React from 'react';
import { Badge } from '../../ui/Badge';
import { Card, CardContent } from '../../ui/Card';
import { CheckCircle, Download } from 'lucide-react';
import { Button } from '../../ui/Button';

interface TransmissionReceiptProps {
  receipt: {
    receipt_id: string;
    transmission_id: string;
    timestamp: string;
    verification_status: string;
    receipt_data: any;
  };
  onDownload?: () => void;
}

const TransmissionReceipt: React.FC<TransmissionReceiptProps> = ({ receipt, onDownload }) => {
  // Function to download receipt as JSON
  const downloadReceipt = () => {
    const receiptStr = JSON.stringify(receipt, null, 2);
    const blob = new Blob([receiptStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `receipt_${receipt.receipt_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    if (onDownload) {
      onDownload();
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-500">Receipt ID</p>
          <p className="font-mono text-xs">{receipt.receipt_id}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Verification</p>
          <p>{receipt.verification_status === 'verified' ? (
            <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Verified</Badge>
          ) : (
            <Badge>{receipt.verification_status}</Badge>
          )}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Timestamp</p>
          <p>{new Date(receipt.timestamp).toLocaleString()}</p>
        </div>
        <div>
          <p className="text-sm text-gray-500">Transmission ID</p>
          <p className="font-mono text-xs">{receipt.transmission_id}</p>
        </div>
      </div>

      <div className="mt-4">
        <div className="flex justify-between items-center mb-2">
          <h4 className="text-md font-semibold">Receipt Data</h4>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={downloadReceipt} 
            className="text-cyan-600 border-cyan-600"
          >
            <Download className="h-4 w-4 mr-1" /> Download
          </Button>
        </div>
        <Card>
          <CardContent className="p-4">
            <pre className="text-xs overflow-auto bg-gray-50 p-2 rounded max-h-96">
              {JSON.stringify(receipt.receipt_data, null, 2)}
            </pre>
          </CardContent>
        </Card>
      </div>

      <div className="mt-4 px-3 py-2 bg-gray-50 rounded text-sm">
        <p className="text-gray-600">
          <span className="font-semibold">Note:</span> This receipt serves as proof of transmission to FIRS. 
          It contains a digital signature that can be verified for authenticity. 
          We recommend downloading and storing this receipt for your records.
        </p>
      </div>
    </div>
  );
};

export default TransmissionReceipt;
