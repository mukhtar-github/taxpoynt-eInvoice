import React from 'react';
import { BookOpen, ChevronRight, FileText, Info, Key } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '../../ui/Card';
import { Badge } from '../../ui/Badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '../../ui/Accordion';
import { Alert, AlertDescription } from '../../ui/Alert';

/**
 * Signature Documentation Component
 * 
 * Provides comprehensive documentation on signature functionality including:
 * - Overview of signature types and algorithms
 * - Best practices for signature management
 * - Troubleshooting common issues
 * - FIRS compliance information
 */
const SignatureDocumentation: React.FC = () => {
  return (
    <Card className="border-l-4 border-l-cyan-500">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-cyan-600" />
            Signature Documentation
          </CardTitle>
          <Badge variant="outline" className="bg-cyan-50 text-cyan-700 border-cyan-200">
            APP
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Introduction */}
        <div className="prose max-w-none">
          <p className="text-gray-700">
            The TaxPoynt eInvoice APP provides a comprehensive suite of signature 
            management tools to ensure compliance, security, and auditability of 
            your electronic invoices. The following documentation will help you 
            understand how to effectively use these features.
          </p>
        </div>
        
        {/* Best Practices Alert */}
        <Alert className="bg-amber-50 text-amber-800 border-amber-200">
          <Info className="h-4 w-4 text-amber-600" />
          <AlertDescription>
            <strong>Best Practice:</strong> Review your signature settings periodically and 
            ensure you're using the latest CSID version for maximum compliance with 
            regulatory requirements.
          </AlertDescription>
        </Alert>
        
        {/* Documentation Accordion */}
        <Accordion type="multiple" className="w-full">
          {/* Overview */}
          <AccordionItem value="overview">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center text-left">
                <FileText className="mr-2 h-5 w-5 text-cyan-600" /> 
                <span>Overview of Digital Signatures</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4 px-2 text-gray-700 space-y-3">
              <p>
                Digital signatures in TaxPoynt eInvoice ensure the authenticity and integrity
                of electronic invoices submitted to FIRS. A digital signature serves as electronic
                proof that an invoice was created by a specific business entity and has not been
                altered since it was signed.
              </p>
              
              <h4 className="font-medium text-gray-900 mt-4">Key Components:</h4>
              <ul className="list-disc pl-5 space-y-2">
                <li><strong>CSID (Cryptographic Stamp Identifier):</strong> A unique identifier that combines the signature with metadata.</li>
                <li><strong>Signature Algorithm:</strong> The cryptographic method used to generate the signature (RSA-PSS-SHA256, RSA-PKCS1-SHA256, ED25519).</li>
                <li><strong>Version:</strong> The CSID protocol version, with V2.0 being the latest with enhanced features.</li>
                <li><strong>Certificate:</strong> Contains the public key used to verify signatures and connects them to your business identity.</li>
              </ul>
            </AccordionContent>
          </AccordionItem>
          
          {/* Algorithms */}
          <AccordionItem value="algorithms">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center text-left">
                <Key className="mr-2 h-5 w-5 text-cyan-600" /> 
                <span>Supported Algorithms</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4 px-2 text-gray-700 space-y-3">
              <p>
                TaxPoynt supports multiple signing algorithms to balance security needs,
                performance, and compatibility with various systems.
              </p>
              
              <div className="space-y-4 mt-3">
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="font-medium text-cyan-700">RSA-PSS-SHA256 (Recommended)</h4>
                  <p className="text-sm mt-1">
                    Provides the highest level of security using PSS padding scheme with SHA-256 hash.
                    This is the FIRS-recommended algorithm for maximum security.
                  </p>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="font-medium text-gray-700">RSA-PKCS1-SHA256</h4>
                  <p className="text-sm mt-1">
                    Traditional RSA signing with PKCS#1 v1.5 padding scheme.
                    Offers good compatibility with older systems.
                  </p>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="font-medium text-gray-700">ED25519</h4>
                  <p className="text-sm mt-1">
                    Modern elliptic curve signature algorithm that offers excellent security with
                    shorter keys and faster verification times.
                  </p>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
          
          {/* Best Practices */}
          <AccordionItem value="best-practices">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center text-left">
                <ChevronRight className="mr-2 h-5 w-5 text-cyan-600" /> 
                <span>Best Practices</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4 px-2 text-gray-700 space-y-3">
              <ol className="list-decimal pl-5 space-y-4">
                <li>
                  <strong>Use the latest CSID version:</strong>
                  <p className="text-sm mt-1">
                    Always use the latest CSID version (currently 2.0) to ensure compliance with
                    the most recent FIRS requirements and security standards.
                  </p>
                </li>
                
                <li>
                  <strong>Enable caching for high-volume operations:</strong>
                  <p className="text-sm mt-1">
                    For businesses processing large numbers of invoices, enable signature caching
                    to improve performance. Adjust the cache size based on your transaction volume.
                  </p>
                </li>
                
                <li>
                  <strong>Regular verification:</strong>
                  <p className="text-sm mt-1">
                    Periodically verify a sample of your signed invoices to ensure
                    signature validity is maintained. This helps catch any issues before they
                    affect compliance.
                  </p>
                </li>
                
                <li>
                  <strong>Monitor performance metrics:</strong>
                  <p className="text-sm mt-1">
                    Use the performance monitoring tab to track signature generation and verification
                    times. Unexpected changes may indicate system issues.
                  </p>
                </li>
                
                <li>
                  <strong>Certificate management:</strong>
                  <p className="text-sm mt-1">
                    Ensure your signing certificates are kept current and renewed before expiration.
                    Schedule calendar reminders 30 days before expiration.
                  </p>
                </li>
              </ol>
            </AccordionContent>
          </AccordionItem>
          
          {/* Troubleshooting */}
          <AccordionItem value="troubleshooting">
            <AccordionTrigger className="hover:no-underline">
              <div className="flex items-center text-left">
                <Info className="mr-2 h-5 w-5 text-cyan-600" /> 
                <span>Troubleshooting</span>
              </div>
            </AccordionTrigger>
            <AccordionContent className="pt-2 pb-4 px-2 text-gray-700 space-y-3">
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900">Invalid Signature Errors</h4>
                  <ul className="list-disc pl-5 text-sm space-y-2 mt-2">
                    <li><strong>Data Mismatch:</strong> Any change to the invoice data after signing will invalidate the signature.</li>
                    <li><strong>Wrong Certificate:</strong> Using a different certificate for verification than was used for signing.</li>
                    <li><strong>Expired Certificate:</strong> Signatures remain valid only while the certificate is valid.</li>
                    <li><strong>Algorithm Mismatch:</strong> Using a different algorithm for verification than was used for signing.</li>
                  </ul>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-900">Performance Issues</h4>
                  <ul className="list-disc pl-5 text-sm space-y-2 mt-2">
                    <li><strong>High CPU Usage:</strong> Consider enabling parallel processing for batch operations.</li>
                    <li><strong>Slow Verification:</strong> Check for network latency if using remote certificate validation.</li>
                    <li><strong>Cache Misses:</strong> If your cache hit rate is low, consider increasing the cache size or TTL.</li>
                  </ul>
                </div>
                
                <div className="bg-gray-50 p-3 rounded-md">
                  <h4 className="font-medium text-gray-900">When to Contact Support</h4>
                  <p className="text-sm mt-1">
                    Contact TaxPoynt support if you encounter:
                  </p>
                  <ul className="list-disc pl-5 text-sm space-y-1 mt-2">
                    <li>Persistent verification failures despite troubleshooting</li>
                    <li>Significant performance degradation</li>
                    <li>Certificate issues that cannot be resolved through the platform</li>
                    <li>Questions about FIRS compliance requirements</li>
                  </ul>
                </div>
              </div>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </CardContent>
    </Card>
  );
};

export default SignatureDocumentation;
