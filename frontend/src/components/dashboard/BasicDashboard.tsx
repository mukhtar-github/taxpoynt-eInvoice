import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Badge } from '../../../components/ui/Badge';
import { 
  AlertCircle, 
  Lock, 
  Mail, 
  Phone, 
  User,
  HelpCircle,
  ArrowRight,
  Shield
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '../../../context/AuthContext';

/**
 * Basic Dashboard Component
 * 
 * Fallback dashboard for users with limited or no service access.
 * Provides information about available services and how to upgrade access.
 */
export const BasicDashboard: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* Welcome Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center w-16 h-16 bg-gray-100 rounded-full mx-auto">
          <User className="w-8 h-8 text-gray-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome, {user?.name || user?.email || 'User'}
          </h1>
          <p className="text-gray-600">
            Your account has limited access to TaxPoynt eInvoice services
          </p>
        </div>
        <Badge variant="outline" className="inline-flex items-center gap-2">
          <Lock className="w-3 h-3" />
          Limited Access
        </Badge>
      </div>

      {/* Access Limitation Notice */}
      <Card className="border-amber-200 bg-amber-50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-amber-800">
            <AlertCircle className="w-5 h-5" />
            Service Access Required
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-amber-700">
            To access TaxPoynt eInvoice features, you need to have one or more services enabled on your account.
          </p>
          
          <div className="space-y-3">
            <h4 className="font-medium text-amber-800">Available Services:</h4>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 bg-white rounded-lg border border-amber-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Shield className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-900">Access Point Provider (APP)</h5>
                    <p className="text-sm text-gray-600">FIRS-certified e-invoicing services</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500 space-y-1">
                  <div>• Digital certificate management</div>
                  <div>• Secure invoice transmission</div>
                  <div>• Compliance monitoring</div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border border-amber-200">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-cyan-100 rounded-lg">
                    <Shield className="w-4 h-4 text-cyan-600" />
                  </div>
                  <div>
                    <h5 className="font-medium text-gray-900">System Integration (SI)</h5>
                    <p className="text-sm text-gray-600">Business system connections</p>
                  </div>
                </div>
                <div className="text-xs text-gray-500 space-y-1">
                  <div>• ERP/CRM/POS integrations</div>
                  <div>• Data synchronization</div>
                  <div>• Business process automation</div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Available Actions */}
      <Card>
        <CardHeader>
          <CardTitle>What You Can Do</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Button variant="outline" className="h-auto py-4 px-6 justify-start" asChild>
              <Link href="/pricing">
                <div className="text-left">
                  <div className="font-medium flex items-center gap-2">
                    View Service Plans
                    <ArrowRight className="w-4 h-4" />
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Explore available services and pricing
                  </div>
                </div>
              </Link>
            </Button>

            <Button variant="outline" className="h-auto py-4 px-6 justify-start" asChild>
              <Link href="/help">
                <div className="text-left">
                  <div className="font-medium flex items-center gap-2">
                    <HelpCircle className="w-4 h-4" />
                    Get Help
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Contact support for assistance
                  </div>
                </div>
              </Link>
            </Button>

            <Button variant="outline" className="h-auto py-4 px-6 justify-start" asChild>
              <Link href="/dashboard/organization">
                <div className="text-left">
                  <div className="font-medium flex items-center gap-2">
                    <User className="w-4 h-4" />
                    Account Settings
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Manage your profile and preferences
                  </div>
                </div>
              </Link>
            </Button>

            <Button variant="outline" className="h-auto py-4 px-6 justify-start" asChild>
              <Link href="mailto:support@taxpoynt.com">
                <div className="text-left">
                  <div className="font-medium flex items-center gap-2">
                    <Mail className="w-4 h-4" />
                    Request Access
                  </div>
                  <div className="text-sm text-gray-600 mt-1">
                    Contact us to enable services
                  </div>
                </div>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Contact Information */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-900">Need Help?</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center gap-3 text-blue-800">
            <Mail className="w-4 h-4" />
            <div>
              <div className="font-medium">Email Support</div>
              <a href="mailto:support@taxpoynt.com" className="text-sm text-blue-600 hover:underline">
                support@taxpoynt.com
              </a>
            </div>
          </div>

          <div className="flex items-center gap-3 text-blue-800">
            <Phone className="w-4 h-4" />
            <div>
              <div className="font-medium">Phone Support</div>
              <a href="tel:+2348123456789" className="text-sm text-blue-600 hover:underline">
                +234 812 345 6789
              </a>
            </div>
          </div>

          <div className="text-sm text-blue-700 mt-4">
            Our support team is available Monday through Friday, 9 AM to 6 PM (WAT).
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default BasicDashboard;