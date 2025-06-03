import React from 'react';
import { InfoIcon, Shield, ShieldCheck, ShieldAlert, Calendar, Code, FileCheck } from 'lucide-react';
import { format } from 'date-fns';

import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../../ui/Tooltip';

interface SignatureVisualizerProps {
  signatureData: {
    isValid?: boolean;
    timestamp?: string;
    algorithm?: string;
    version?: string;
    signatureId?: string;
    keyInfo?: {
      keyId?: string;
      certificate?: string;
    };
  };
  compact?: boolean;
}

/**
 * Visualizes digital signature information for invoices
 * 
 * Provides a visual representation of the signature with validity status,
 * timestamp, and cryptographic details in either compact or detailed form
 */
const SignatureVisualizer: React.FC<SignatureVisualizerProps> = ({
  signatureData,
  compact = false
}) => {
  const {
    isValid = true,
    timestamp,
    algorithm,
    version,
    signatureId,
    keyInfo
  } = signatureData;

  // Format timestamp if available
  const formattedTimestamp = timestamp ? 
    format(new Date(timestamp), 'dd MMM yyyy, HH:mm:ss') : 
    'Not available';

  // Compact visualization for in-line display
  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip content={<div></div>}>
          <TooltipTrigger asChild>
            <div className="inline-flex items-center space-x-1 border rounded-md px-1.5 py-0.5 text-xs bg-white">
              {isValid ? (
                <ShieldCheck size={12} className="text-green-500" />
              ) : (
                <ShieldAlert size={12} className="text-red-500" />
              )}
              <span className="font-medium">
                {isValid ? 'Signed' : 'Invalid'} 
              </span>
              {timestamp && (
                <span className="text-gray-500">
                  • {format(new Date(timestamp), 'dd/MM/yyyy')}
                </span>
              )}
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1 text-xs">
              <p className="font-medium">Digital Signature</p>
              <p>Status: {isValid ? 'Valid' : 'Invalid'}</p>
              {timestamp && <p>Signed: {formattedTimestamp}</p>}
              {algorithm && <p>Algorithm: {algorithm}</p>}
              {version && <p>CSID Version: {version}</p>}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Full visualization
  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-md flex items-center gap-2">
            <FileCheck className="h-5 w-5 text-cyan-600" />
            Digital Signature
          </CardTitle>
          <Badge 
            variant="outline" 
            className={`${
              isValid 
                ? 'bg-green-50 text-green-700 border-green-200' 
                : 'bg-red-50 text-red-700 border-red-200'
            }`}
          >
            {isValid ? 'Valid' : 'Invalid'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex justify-between items-center border-b pb-2">
            <div className="flex items-center gap-2 text-sm">
              <Calendar className="h-4 w-4 text-gray-500" />
              <span className="font-medium">Timestamp</span>
            </div>
            <div className="text-sm">{formattedTimestamp}</div>
          </div>
          
          {algorithm && (
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2 text-sm">
                <Shield className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Algorithm</span>
              </div>
              <div className="text-sm">{algorithm}</div>
            </div>
          )}
          
          {version && (
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2 text-sm">
                <Code className="h-4 w-4 text-gray-500" />
                <span className="font-medium">CSID Version</span>
              </div>
              <div className="text-sm">{version}</div>
            </div>
          )}
          
          {signatureId && (
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2 text-sm">
                <InfoIcon className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Signature ID</span>
              </div>
              <div className="text-sm font-mono text-xs">{signatureId}</div>
            </div>
          )}
          
          {keyInfo?.keyId && (
            <div className="flex justify-between items-center border-b pb-2">
              <div className="flex items-center gap-2 text-sm">
                <InfoIcon className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Key ID</span>
              </div>
              <div className="text-sm font-mono text-xs">{keyInfo.keyId}</div>
            </div>
          )}
          
          {keyInfo?.certificate && (
            <div className="flex justify-between items-center pb-2">
              <div className="flex items-center gap-2 text-sm">
                <InfoIcon className="h-4 w-4 text-gray-500" />
                <span className="font-medium">Certificate</span>
              </div>
              <div className="text-sm font-mono text-xs">{keyInfo.certificate}</div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default SignatureVisualizer;
