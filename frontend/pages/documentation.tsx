import React, { useState } from 'react';
import Head from 'next/head';
import MainLayout from '../components/layouts/MainLayout';
import { Container } from '../components/ui/Grid';
import { Typography } from '../components/ui/Typography';
import { Tabs } from '../components/ui/Tabs';
import { Card, CardContent } from '../components/ui/Card';
import { Search, Info, Book, FileText, Code, Shield, HelpCircle, AlertTriangle } from 'lucide-react';
import { Button } from '../components/ui/Button';

// Documentation sections
type Section = {
  id: string;
  title: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
};

const DocumentationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');

  // Documentation sections
  const sections: Section[] = [
    {
      id: 'overview',
      title: 'Overview',
      icon: <Info className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">FIRS E-Invoicing Overview</Typography.Heading>
          <Typography.Text className="mb-6">
            Essential information about the Nigerian e-invoicing mandate and how Taxpoynt helps businesses comply.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Nigerian E-Invoicing Mandate
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  The Federal Inland Revenue Service (FIRS) of Nigeria has mandated electronic invoicing for all businesses 
                  starting July 2025. This initiative aims to enhance tax compliance, reduce fraud, and streamline business 
                  operations across the country.
                </Typography.Text>
                <Typography.Text className="mb-4">
                  <span className="font-semibold">Key requirements include:</span>
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li>Real-time electronic submission of all business invoices</li>
                  <li>Invoice Reference Number (IRN) issuance for each valid invoice</li>
                  <li>Standardized invoice formats following UBL 2.1 specifications</li>
                  <li>QR code implementation for verification</li>
                  <li>Digital signature requirements for non-repudiation</li>
                </ul>
                <Typography.Text>
                  Businesses must either integrate with the FIRS portal directly or use a certified System Integrator 
                  like Taxpoynt to comply with these regulations.
                </Typography.Text>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Technical Standards
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Compliance with the FIRS e-invoicing mandate requires adherence to several technical standards:
                </Typography.Text>
                <div className="space-y-4">
                  <div>
                    <Typography.Text className="font-semibold">UBL 2.1 Compliance</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600">
                      Universal Business Language standard for electronic business documents. All invoices must conform 
                      to this structured XML format to ensure consistency and interoperability.
                    </Typography.Text>
                  </div>
                  <div>
                    <Typography.Text className="font-semibold">PEPPOL Compatibility</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600">
                      Pan-European Public Procurement Online standards facilitate cross-border e-invoice exchange. 
                      This enables Nigerian businesses to seamlessly transact with international partners.
                    </Typography.Text>
                  </div>
                  <div>
                    <Typography.Text className="font-semibold">QR Verification</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600">
                      Each e-invoice includes a QR code that enables verification of authenticity and provides 
                      a quick way to access invoice details.
                    </Typography.Text>
                  </div>
                  <div>
                    <Typography.Text className="font-semibold">API-First Design</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600">
                      Facilitates seamless integration with existing business systems through standardized 
                      API communications, ensuring minimal disruption to business operations.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Taxpoynt's Role as a System Integrator
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  As a certified System Integrator, Taxpoynt bridges the gap between your business systems and FIRS e-invoicing requirements:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li>We handle the technical complexity of UBL 2.1 and PEPPOL standards</li>
                  <li>We integrate directly with your existing ERP systems (SAP, Odoo, Oracle, etc.)</li>
                  <li>We manage real-time validation and submission to FIRS</li>
                  <li>We provide IRN storage and management for all your e-invoices</li>
                  <li>We ensure your business remains compliant as requirements evolve</li>
                </ul>
                <Typography.Text>
                  Our platform supports businesses of all sizes, from SMEs to large enterprises, with flexible 
                  integration options tailored to your technical capabilities and business needs.
                </Typography.Text>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'user-guide',
      title: 'User Guide',
      icon: <Book className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">User Guide</Typography.Heading>
          <Typography.Text className="mb-6">
            Comprehensive guide on how to use the Taxpoynt eInvoice system, from setup to advanced features.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  API Integration Approach
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Taxpoynt e-Invoice uses a server-side API integration to connect with your ERP systems:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li><span className="font-semibold">JSON-RPC Communication</span>: We connect directly to your ERP's API using secure JSON-RPC protocols</li>
                  <li><span className="font-semibold">Data Polling</span>: Our system periodically checks for new invoices in your ERP system</li>
                  <li><span className="font-semibold">Data Transformation</span>: Invoice data is automatically converted to UBL 2.1 format</li>
                  <li><span className="font-semibold">Response Handling</span>: IRNs and validation results are stored in our system for tracking</li>
                </ul>
                <Typography.Text>
                  This approach requires minimal changes to your existing systems while ensuring full compliance with FIRS requirements.
                </Typography.Text>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Security Considerations
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Taxpoynt implements comprehensive security measures to protect your business data:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li><span className="font-semibold">Data Encryption</span>: All data transmission uses TLS 1.3 encryption</li>
                  <li><span className="font-semibold">Role-based Access</span>: Granular permissions ensure users can only access appropriate data</li>
                  <li><span className="font-semibold">API Rate Limiting</span>: Prevents system overload and potential DDoS attacks</li>
                  <li><span className="font-semibold">Audit Logging</span>: Comprehensive logs of all system activities for compliance and security</li>
                  <li><span className="font-semibold">Tokenization</span>: Sensitive data is tokenized rather than transmitted directly</li>
                </ul>
                <Typography.Text>
                  Our security practices comply with international standards and Nigerian data protection regulations.
                </Typography.Text>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Business Continuity Features
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  We ensure your e-invoicing continues to function even during technical challenges:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li><span className="font-semibold">Offline Mode</span>: If connectivity is interrupted, invoices are queued locally</li>
                  <li><span className="font-semibold">Retry Logic</span>: Failed transmissions automatically retry with exponential backoff</li>
                  <li><span className="font-semibold">Failover Systems</span>: Multiple server instances ensure high availability</li>
                  <li><span className="font-semibold">Data Reconciliation</span>: Periodic checks ensure both systems remain in sync</li>
                </ul>
                <Typography.Text>
                  These features provide peace of mind that your business remains compliant even during technical difficulties.
                </Typography.Text>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'tutorials',
      title: 'Tutorials',
      icon: <FileText className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Tutorials</Typography.Heading>
          <Typography.Text className="mb-6">
            Step-by-step guides for setting up and using Taxpoynt E-Invoice with different ERP systems.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Odoo Integration
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Follow these steps to integrate Taxpoynt with your Odoo ERP system:
                </Typography.Text>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold mb-2">1. API Connection Setup</Typography.Text>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Log in to your Taxpoynt dashboard and navigate to "Integrations"</li>
                      <li>Select "Add New Integration" and choose "Odoo" from the ERP options</li>
                      <li>Generate a new API key specifically for your Odoo instance</li>
                      <li>Copy your Odoo instance URL, database name, username, and password</li>
                      <li>Enter these details in the Taxpoynt integration form</li>
                    </ol>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">2. Configuration Steps</Typography.Text>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Select which Odoo companies should be included in e-invoicing</li>
                      <li>Configure invoice types to be processed (sales invoices, credit notes, etc.)</li>
                      <li>Set up the polling frequency (real-time, hourly, daily)</li>
                      <li>Define notification preferences for successful/failed submissions</li>
                    </ol>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">3. Testing Procedures</Typography.Text>
                    <ol className="list-decimal pl-5 space-y-2">
                      <li>Click "Test Connection" to verify API connectivity</li>
                      <li>Create a test invoice in Odoo and run a manual sync</li>
                      <li>Verify the invoice appears in your Taxpoynt dashboard</li>
                      <li>Check that the test IRN was generated correctly</li>
                    </ol>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">4. Field Mapping Reference</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mb-2">
                      Key Odoo fields are mapped to UBL 2.1 as follows:
                    </Typography.Text>
                    <ul className="list-disc pl-5 space-y-1 text-sm">
                      <li>Odoo: partner_id.name → UBL: cac:AccountingCustomerParty/cac:Party/cac:PartyName/cbc:Name</li>
                      <li>Odoo: amount_total → UBL: cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount</li>
                      <li>Odoo: invoice_line_ids → UBL: cac:InvoiceLine</li>
                      <li>Full mapping documentation available in your integration dashboard</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Other ERP Systems
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Taxpoynt supports integration with the following ERP systems:
                </Typography.Text>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Typography.Text className="font-semibold mb-2">SAP Integration</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mb-2">
                      Connect via SAP OData services or RFC/BAPI functions
                    </Typography.Text>
                    <Button variant="link" size="sm" className="text-primary-600 pl-0">
                      View SAP integration guide →
                    </Button>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">Oracle Integration</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mb-2">
                      Connect via Oracle REST Data Services or Integration Cloud
                    </Typography.Text>
                    <Button variant="link" size="sm" className="text-primary-600 pl-0">
                      View Oracle integration guide →
                    </Button>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">Microsoft Dynamics Integration</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mb-2">
                      Connect via Web API or Power Automate
                    </Typography.Text>
                    <Button variant="link" size="sm" className="text-primary-600 pl-0">
                      View Dynamics integration guide →
                    </Button>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold mb-2">QuickBooks Integration</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mb-2">
                      Connect via QuickBooks API or Intuit Developer Platform
                    </Typography.Text>
                    <Button variant="link" size="sm" className="text-primary-600 pl-0">
                      View QuickBooks integration guide →
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'api-docs',
      title: 'API Documentation',
      icon: <Code className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">API Documentation</Typography.Heading>
          <Typography.Text className="mb-6">
            Technical documentation for developers integrating with the Taxpoynt eInvoice API.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Authentication Endpoints
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Secure your API requests with our authentication system:
                </Typography.Text>
                
                <div className="bg-gray-50 p-4 rounded-md mb-4 font-mono text-sm">
                  <div className="mb-2 font-semibold">POST /api/auth/token</div>
                  <div className="text-gray-600 mb-2">Generate an access token for API access</div>
                  <div className="mb-1">Request body:</div>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}`}
                  </pre>
                  <div className="mt-2 mb-1">Response:</div>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR...",
  "token_type": "bearer",
  "expires_in": 3600
}`}
                  </pre>
                </div>
                
                <Typography.Text>
                  All subsequent API requests must include the access token in the Authorization header:
                  <span className="block mt-2 bg-gray-50 p-2 rounded-md font-mono text-xs">
                    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR...
                  </span>
                </Typography.Text>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Invoice Submission API
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Endpoints for submitting invoices for e-invoice generation:
                </Typography.Text>
                
                <div className="bg-gray-50 p-4 rounded-md mb-4 font-mono text-sm">
                  <div className="mb-2 font-semibold">POST /api/invoices</div>
                  <div className="text-gray-600 mb-2">Submit a new invoice for processing</div>
                  <div className="mb-1">Request body:</div>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "invoice_data": {
    "invoice_number": "INV-001",
    "invoice_date": "2025-05-15",
    "customer": {
      "name": "Acme Corp",
      "tax_id": "12345678-9"
    },
    "line_items": [
      {
        "description": "Product A",
        "quantity": 5,
        "unit_price": 100.00,
        "tax_rate": 7.5
      }
    ],
    "total_amount": 537.50
  },
  "format": "ubl21"
}`}
                  </pre>
                </div>
                
                <Typography.Text>
                  Full API specification is available in the Swagger documentation available at your instance URL: 
                  <span className="block mt-2 bg-gray-50 p-2 rounded-md font-mono text-xs">
                    https://your-instance.taxpoynt.com/api/docs
                  </span>
                </Typography.Text>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Status Checking API
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Check the status of submitted invoices:
                </Typography.Text>
                
                <div className="bg-gray-50 p-4 rounded-md mb-4 font-mono text-sm">
                  <div className="mb-2 font-semibold">GET /api/invoices/{'{'}'invoice_id'{'}'}/status</div>
                  <div className="text-gray-600 mb-2">Retrieve current status of an invoice</div>
                  <div className="mt-2 mb-1">Response:</div>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "invoice_id": "6dc8c42f-92cb-41d4-a40a-c7f9d16d0447",
  "status": "VALIDATED",
  "irn": "FIRS-82930492-2934",
  "submission_date": "2025-05-15T10:30:45Z",
  "validation_date": "2025-05-15T10:31:12Z",
  "qr_code_url": "https://api.taxpoynt.com/qr/FIRS-82930492-2934"
}`}
                  </pre>
                </div>
                
                <Typography.Text>
                  Possible status values: <code>PENDING</code>, <code>VALIDATING</code>, <code>VALIDATED</code>, <code>REJECTED</code>, <code>ERROR</code>
                </Typography.Text>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Webhook Integration
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Receive real-time updates when invoice status changes:
                </Typography.Text>
                
                <div className="bg-gray-50 p-4 rounded-md mb-4 font-mono text-sm">
                  <div className="mb-2 font-semibold">POST /api/webhooks/configure</div>
                  <div className="text-gray-600 mb-2">Configure webhook endpoints for notifications</div>
                  <div className="mb-1">Request body:</div>
                  <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "url": "https://your-system.com/api/taxpoynt-callback",
  "events": ["invoice.validated", "invoice.rejected"],
  "secret": "your_webhook_secret"
}`}
                  </pre>
                </div>
                
                <Typography.Text className="mb-4">
                  Your webhook endpoint will receive event notifications in this format:
                </Typography.Text>
                <pre className="bg-gray-100 p-2 rounded text-xs overflow-x-auto">
{`{
  "event": "invoice.validated",
  "timestamp": "2025-05-15T10:31:12Z",
  "data": {
    "invoice_id": "6dc8c42f-92cb-41d4-a40a-c7f9d16d0447",
    "irn": "FIRS-82930492-2934",
    "customer_reference": "INV-001"
  }
}`}
                </pre>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'legal',
      title: 'Legal',
      icon: <Shield className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Legal Information</Typography.Heading>
          <Typography.Text className="mb-6">
            Licensing, terms of service, and legal agreements for the Taxpoynt eInvoice system.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Compliance Certifications
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Taxpoynt maintains the following certifications and compliance standards:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li><span className="font-semibold">FIRS Certified System Integrator</span>: Authorized to process e-invoices in compliance with Nigerian tax regulations</li>
                  <li><span className="font-semibold">ISO 27001</span>: Certified information security management system</li>
                  <li><span className="font-semibold">NDPR Compliance</span>: Full adherence to Nigerian Data Protection Regulation requirements</li>
                  <li><span className="font-semibold">UBL 2.1 Certification</span>: Validated implementation of Universal Business Language standards</li>
                </ul>
                <Typography.Text className="text-sm text-gray-600">
                  Copies of certificates are available upon request for due diligence purposes.
                </Typography.Text>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Terms of Service
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  By using the Taxpoynt e-Invoice platform, you agree to the following key terms:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li>You retain ownership of your data while granting us license to process it for e-invoicing purposes</li>
                  <li>Service availability commitment of 99.9% uptime (excluding scheduled maintenance)</li>
                  <li>Subscription fees are billed monthly or annually based on your selected plan</li>
                  <li>Either party may terminate the service with 30 days written notice</li>
                </ul>
                <Button variant="link" size="sm" className="text-primary-600 pl-0">
                  View full Terms of Service →
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Privacy Policy
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  Taxpoynt is committed to protecting your data privacy:
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li>We collect only the data necessary to provide the e-invoicing service</li>
                  <li>Your data is encrypted both in transit and at rest</li>
                  <li>We do not sell or share your data with third parties (except as required by law)</li>
                  <li>You may request export or deletion of your data at any time</li>
                  <li>We comply with NDPR and other applicable data protection regulations</li>
                </ul>
                <Button variant="link" size="sm" className="text-primary-600 pl-0">
                  View full Privacy Policy →
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  NDPR Compliance
                </Typography.Heading>
                <Typography.Text className="mb-4">
                  As a Nigerian business service provider, we fully comply with the Nigerian Data Protection Regulation (NDPR):
                </Typography.Text>
                <ul className="list-disc pl-5 space-y-2 mb-4">
                  <li>We maintain a comprehensive Data Protection Policy</li>
                  <li>We have appointed a Data Protection Officer</li>
                  <li>We conduct regular Data Protection Impact Assessments</li>
                  <li>We provide data subject access rights in accordance with the NDPR</li>
                  <li>We maintain records of all data processing activities</li>
                </ul>
                <Typography.Text className="text-sm text-gray-600">
                  For questions regarding our NDPR compliance, please contact our Data Protection Officer at dpo@taxpoynt.com.
                </Typography.Text>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'faq',
      title: 'FAQ',
      icon: <HelpCircle className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Frequently Asked Questions</Typography.Heading>
          <Typography.Text className="mb-6">
            Answers to common questions about the Taxpoynt eInvoice system.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Common Integration Questions
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">Do I need to change my existing invoicing workflow?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      No, one of the key advantages of Taxpoynt is that your team continues using their familiar ERP system for creating invoices. Our solution works in the background to handle the e-invoice compliance requirements automatically.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">How long does the integration process take?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      For standard ERP systems like Odoo, SAP, and Oracle, integration typically takes 2-5 business days from start to finish. Custom or legacy systems may require additional time depending on their API capabilities.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Can I test the integration before going live?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Yes, all integrations start with a sandbox environment where you can thoroughly test the connection and e-invoice generation without affecting your production system or submitting to FIRS.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">What happens if my ERP is temporarily offline?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Taxpoynt includes an offline queueing system that stores pending invoices locally until connectivity is restored. Once your system is back online, the queued invoices are automatically processed without any manual intervention.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Performance and Reliability
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">What is the system's uptime guarantee?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Taxpoynt guarantees 99.9% uptime for all production environments, with transparent monitoring available through our status page. Our infrastructure includes redundant systems and automatic failover mechanisms.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">How quickly are invoices processed?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Most invoices are processed and receive an IRN within 5-10 seconds of submission. During peak FIRS processing times (month-end), this might extend to 30-60 seconds in rare cases.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Is there a limit to how many invoices I can process?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      We offer tiered plans based on monthly invoice volume. The Standard plan includes up to 5,000 invoices per month, while Enterprise plans can accommodate unlimited volumes with rate limiting to ensure system stability.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">How does the system handle peak loads?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Our cloud infrastructure automatically scales to accommodate increased demand. Additionally, we implement intelligent queue management during peak periods to ensure all customers receive fair access to processing resources.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Security Concerns
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">How is my sensitive invoice data protected?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      All data is encrypted both in transit (using TLS 1.3) and at rest (using AES-256 encryption). Our systems are ISO 27001 certified and undergo regular security audits and penetration testing.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Who has access to my invoice data?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Access is strictly limited to authenticated users within your organization based on role-based permissions you define. Our support staff can only access your data with explicit authorization and all access is logged for audit purposes.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Is my data shared with third parties?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Your invoice data is only shared with FIRS as required by regulation. We do not sell, analyze, or otherwise share your data with any third parties unless explicitly required by law or with your written permission.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">How often are security updates applied?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Our infrastructure receives security patches within 24 hours of release for critical updates and weekly for non-critical updates. These updates are deployed using a rolling strategy that ensures zero downtime.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Pricing and Support
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">What pricing plans are available?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      We offer three tiers: Starter (up to 500 invoices/month), Standard (up to 5,000 invoices/month), and Enterprise (unlimited with SLA). All plans include essential features with advanced capabilities in higher tiers. Contact sales for custom pricing options.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">What support channels are available?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Standard plans include email support with 24-hour response time. Enterprise plans receive priority email support (4-hour response), phone support during business hours, and a dedicated account manager. Emergency support is available 24/7 for all paying customers.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Is there a free trial available?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      Yes, we offer a 30-day free trial with up to 100 test invoices. This trial includes full access to all features except production FIRS submissions. No credit card is required to start your trial.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Are there additional fees for updates or new FIRS requirements?</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      No, all regulatory updates and compliance changes are included in your subscription. We continually monitor FIRS requirements and automatically update our system to maintain compliance without additional charges.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    },
    {
      id: 'troubleshooting',
      title: 'Troubleshooting',
      icon: <AlertTriangle className="w-4 h-4" />,
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Troubleshooting Guide</Typography.Heading>
          <Typography.Text className="mb-6">
            Solutions to common issues and problems you might encounter using the system.
          </Typography.Text>
          
          <div className="space-y-8">
            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Common Error Codes
                </Typography.Heading>
                
                <div className="divide-y divide-gray-100">
                  <div className="py-4">
                    <Typography.Text className="font-semibold text-red-600">Error 401: Authentication Failed</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      This indicates your API credentials are invalid or expired.
                    </Typography.Text>
                    <Typography.Text className="text-sm font-medium">Resolution:</Typography.Text>
                    <ol className="list-decimal text-sm pl-5 space-y-1">
                      <li>Check that you're using the correct client ID and client secret</li>
                      <li>Ensure your API key hasn't expired (they rotate every 90 days)</li>
                      <li>Verify your account is active and in good standing</li>
                      <li>Generate new API credentials from your dashboard if needed</li>
                    </ol>
                  </div>
                  
                  <div className="py-4">
                    <Typography.Text className="font-semibold text-red-600">Error 422: Validation Failed</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      The invoice data doesn't meet FIRS validation requirements.
                    </Typography.Text>
                    <Typography.Text className="text-sm font-medium">Resolution:</Typography.Text>
                    <ol className="list-decimal text-sm pl-5 space-y-1">
                      <li>Check the detailed validation message in the response</li>
                      <li>Ensure all required fields (customer TIN, item descriptions, etc.) are present</li>
                      <li>Verify tax calculations are correct and consistent</li>
                      <li>Fix the identified issues and resubmit the invoice</li>
                    </ol>
                  </div>
                  
                  <div className="py-4">
                    <Typography.Text className="font-semibold text-red-600">Error 429: Rate Limit Exceeded</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      You've exceeded the allowed number of API requests for your plan.
                    </Typography.Text>
                    <Typography.Text className="text-sm font-medium">Resolution:</Typography.Text>
                    <ol className="list-decimal text-sm pl-5 space-y-1">
                      <li>Wait until your rate limit resets (typically within the hour)</li>
                      <li>Implement exponential backoff in your integration</li>
                      <li>Consider upgrading to a plan with higher API limits</li>
                      <li>Optimize your code to batch invoices where possible</li>
                    </ol>
                  </div>
                  
                  <div className="py-4">
                    <Typography.Text className="font-semibold text-red-600">Error 503: FIRS Service Unavailable</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      The FIRS e-invoicing system is temporarily unavailable.
                    </Typography.Text>
                    <Typography.Text className="text-sm font-medium">Resolution:</Typography.Text>
                    <ol className="list-decimal text-sm pl-5 space-y-1">
                      <li>Invoices will automatically queue until FIRS is available again</li>
                      <li>Check the Taxpoynt status page for FIRS service updates</li>
                      <li>No action is needed; the system will retry automatically</li>
                    </ol>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Connection Issues
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">ERP Connection Timeouts</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      If Taxpoynt cannot connect to your ERP system:
                    </Typography.Text>
                    <ul className="list-disc text-sm pl-5 space-y-1">
                      <li>Verify your ERP system is online and accessible</li>
                      <li>Check that your firewall allows connections from Taxpoynt IP addresses</li>
                      <li>Ensure API credentials have not expired or been revoked</li>
                      <li>Confirm your ERP API endpoint URLs are correct</li>
                    </ul>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Dashboard Access Issues</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      If you cannot access the Taxpoynt dashboard:
                    </Typography.Text>
                    <ul className="list-disc text-sm pl-5 space-y-1">
                      <li>Clear your browser cache and cookies</li>
                      <li>Try an incognito/private browsing window</li>
                      <li>Check if your corporate network blocks the domain</li>
                      <li>Verify your user account is active</li>
                      <li>Use password reset if you can't login</li>
                    </ul>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Webhook Delivery Failures</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1 mb-2">
                      If webhooks aren't being received by your system:
                    </Typography.Text>
                    <ul className="list-disc text-sm pl-5 space-y-1">
                      <li>Verify your endpoint is publicly accessible</li>
                      <li>Check that your webhook URL is correctly configured</li>
                      <li>Ensure your endpoint returns a 200 OK response</li>
                      <li>Review webhook logs in your Taxpoynt dashboard</li>
                      <li>Test with our webhook simulator tool</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Validation Failures
                </Typography.Heading>
                
                <div className="space-y-6">
                  <div>
                    <Typography.Text className="font-semibold">Missing or Invalid Tax Identification Number (TIN)</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      FIRS requires valid TINs for both seller and buyer. Ensure customer TINs are properly formatted and verified before submission. Use the TIN validation endpoint to pre-check TINs before invoice submission.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Tax Calculation Discrepancies</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      The sum of line item taxes must match the total tax amount, and all percentage calculations must be precise. Use our pre-validation API to check tax calculations before final submission to FIRS.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Invalid Currency Codes</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      All currency codes must be valid ISO 4217 codes. For Nigerian businesses, NGN should be used unless the transaction is explicitly in foreign currency. Multi-currency invoices must specify exchange rates.
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Duplicate Invoice Numbers</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 mt-1">
                      FIRS will reject invoices with previously used invoice numbers. Ensure your ERP generates unique invoice numbers, and use our duplicate detection feature to prevent this common error.
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <Typography.Heading level="h3" className="text-xl font-semibold mb-3">
                  Support Contact Information
                </Typography.Heading>
                
                <div className="space-y-4">
                  <div>
                    <Typography.Text className="font-semibold">Technical Support</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block mt-1">Email: support@taxpoynt.com</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block">Phone: +234 (0) 800-TAXPOYNT</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block">Hours: Monday - Friday, 8:00 AM - 6:00 PM WAT</Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text className="font-semibold">Emergency Support</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block mt-1">For production-critical issues outside business hours:</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block">Emergency Hotline: +234 (0) 801-TAXPOYNT-911</Typography.Text>
                    <Typography.Text className="text-sm text-gray-600 block">(Available 24/7 for Enterprise customers)</Typography.Text>
                  </div>
                  
                  <div className="pt-4">
                    <Button size="lg" className="bg-primary-600 text-white hover:bg-primary-700">
                      Submit Support Ticket
                    </Button>
                    <Typography.Text className="text-xs text-gray-500 mt-2 block">
                      Enterprise customers: Please include your account ID for priority handling
                    </Typography.Text>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )
    }
  ];

  // Filter sections based on search term
  const filteredSections = sections.filter(section => 
    section.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get the active section content
  const activeSection = sections.find(section => section.id === activeTab);

  return (
    <MainLayout title="Documentation | Taxpoynt eInvoice">
      <Container>
        <div className="py-8">
          <div className="flex flex-col md:flex-row justify-between items-center mb-8">
            <Typography.Heading level="h1" className="mb-4 md:mb-0">
              Documentation
            </Typography.Heading>
            
            {/* Search input */}
            <div className="relative w-full md:w-64">
              <input
                type="text"
                placeholder="Search documentation..."
                className="w-full pl-10 pr-4 py-2 border border-border rounded-md"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-secondary h-4 w-4" />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Sidebar Navigation */}
            <div className="col-span-1">
              <div className="sticky top-24">
                <Card>
                  <div className="p-4">
                    <Typography.Text weight="semibold" className="mb-4 block">
                      Documentation Sections
                    </Typography.Text>
                    <nav className="space-y-1">
                      {filteredSections.map(section => (
                        <Button
                          key={section.id}
                          variant={activeTab === section.id ? "default" : "ghost"}
                          className="w-full justify-start text-left"
                          onClick={() => setActiveTab(section.id)}
                        >
                          {section.title}
                        </Button>
                      ))}
                    </nav>
                  </div>
                </Card>
              </div>
            </div>
            
            {/* Main Content */}
            <div className="col-span-1 md:col-span-3">
              {activeSection ? activeSection.content : (
                <Typography.Text>Section not found</Typography.Text>
              )}
            </div>
          </div>
        </div>
      </Container>
    </MainLayout>
  );
};

export default DocumentationPage;
