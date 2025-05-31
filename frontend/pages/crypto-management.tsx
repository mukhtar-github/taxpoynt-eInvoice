import React from 'react';
import { cn } from '../utils/cn';
import { 
  Container,
  Heading,
  Text,
  Divider,
  Card,
  CardHeader,
  CardContent,
  Badge
} from '../components/ui';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs';
import { ShieldCheck } from 'lucide-react';
import ProtectedRoute from '../components/auth/ProtectedRoute';
import CertificateManager from '../components/app/crypto/CertificateManager';
import CryptoStamping from '../components/app/crypto/CryptoStamping';
import QRStampViewer from '../components/app/crypto/QRStampViewer';
import MainLayout from '../components/layouts/MainLayout';

/**
 * Crypto Management Page
 * 
 * This page provides a centralized interface for all cryptographic
 * stamping operations including:
 * - Certificate management
 * - Stamp generation
 * - Stamp verification
 * - QR code scanning and validation
 * 
 * This is an APP layer component that can be used by any SI layer integration.
 * 
 * @note This component follows the APP UI/UX guidelines with proper visual categorization
 *       and uses the application's standard component system.
 */
const CryptoManagementPage: React.FC = () => {
  return (
    <MainLayout>
      <Container className="py-6">
        {/* Header with APP indicator styling */}
        <div className="border-l-4 border-cyan-500 pl-4 mb-6">
          <div className="flex items-center">
            <Heading>Cryptographic Stamping Management</Heading>
            <Badge className="ml-3 bg-cyan-100 text-cyan-800">APP</Badge>
          </div>
          <Text className="text-gray-600 mt-2">
            Manage cryptographic certificates, generate and verify FIRS-compliant stamps
          </Text>
          <Divider className="my-4" />
        </div>
        
        {/* Page header card with icon */}
        <Card className="mb-6 bg-cyan-50 dark:bg-cyan-950">
          <CardHeader className="flex items-center gap-2">
            <div className="p-2 rounded-full bg-white dark:bg-gray-800">
              <ShieldCheck className="h-8 w-8 text-cyan-600" />
            </div>
            <div>
              <Heading className="text-sm">FIRS Cryptographic Compliance</Heading>
              <Text className="text-sm text-gray-600">
                Tools for maintaining FIRS compliance through cryptographic stamping
              </Text>
            </div>
          </CardHeader>
        </Card>
        
        {/* Tabs using ShadcnUI pattern */}
        <Tabs defaultValue="certificates" className="w-full">
          <TabsList className="mb-4">
            <TabsTrigger value="certificates">Certificates</TabsTrigger>
            <TabsTrigger value="stamping">Stamping</TabsTrigger>
            <TabsTrigger value="scanner">QR Scanner</TabsTrigger>
          </TabsList>
          
          <TabsContent value="certificates">
            <CertificateManager />
          </TabsContent>
          
          <TabsContent value="stamping">
            <CryptoStamping />
          </TabsContent>
          
          <TabsContent value="scanner">
            <QRStampViewer />
          </TabsContent>
        </Tabs>
      </Container>
    </MainLayout>
  );
};

// Protect the page with authentication
export default function CryptoManagement() {
  return (
    <ProtectedRoute>
      <CryptoManagementPage />
    </ProtectedRoute>
  );
}
