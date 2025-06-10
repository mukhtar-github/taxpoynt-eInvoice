import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';
import { 
  Activity, 
  FileBarChart, 
  ShieldCheck, 
  Server, 
  Users, 
  Layers,
  Shield, 
  Key, 
  Send
} from 'lucide-react';

// APP Component Imports
import CertificateStatusCards from '../../components/platform/CertificateStatusCards';
import TransmissionStatusVisualization from '../../components/platform/TransmissionStatusVisualization';

interface EnhancedDashboardProps {
  className?: string;
  organizationId: string;
}

/**
 * Enhanced Dashboard Component
 * 
 * Combines both SI functionality and APP features in a single dashboard view
 * with clear visual separation and indicators for APP components.
 */
const EnhancedDashboard: React.FC<EnhancedDashboardProps> = ({ 
  className, 
  organizationId 
}) => {
  // Module definitions - SI modules
  const siModules = [
    { 
      id: 'irn', 
      name: 'IRN Monitoring', 
      description: 'Invoice Reference Number generation tracking',
      icon: <FileBarChart className="h-8 w-8 text-indigo-600" />,
      path: '/dashboard/irn-monitoring',
      color: 'bg-indigo-50 dark:bg-indigo-950 border-indigo-100'
    },
    { 
      id: 'validation', 
      name: 'Validation Statistics', 
      description: 'Invoice validation success rates and errors',
      icon: <ShieldCheck className="h-8 w-8 text-violet-600" />,
      path: '/dashboard/validation-stats',
      color: 'bg-violet-50 dark:bg-violet-950 border-violet-100'
    },
    { 
      id: 'integration', 
      name: 'Integration Status', 
      description: 'Status of Odoo and other system integrations',
      icon: <Layers className="h-8 w-8 text-amber-600" />,
      path: '/dashboard/integration-status',
      color: 'bg-amber-50 dark:bg-amber-950 border-amber-100'
    },
    { 
      id: 'system', 
      name: 'System Health', 
      description: 'API performance and infrastructure health metrics',
      icon: <Server className="h-8 w-8 text-rose-600" />,
      path: '/dashboard/system-health',
      color: 'bg-rose-50 dark:bg-rose-950 border-rose-100'
    }
  ];

  // Module definitions - APP modules (Access Point Provider)
  const appModules = [
    { 
      id: 'certificates', 
      name: 'Certificate Management', 
      description: 'Manage digital certificates for secure transmission',
      icon: <Key className="h-8 w-8 text-cyan-600" />,
      path: '/dashboard/certificates',
      color: 'bg-cyan-50 dark:bg-cyan-950 border-l-4 border-cyan-500'
    },
    { 
      id: 'transmission', 
      name: 'Secure Transmission', 
      description: 'Monitor and manage e-Invoice transmissions',
      icon: <Send className="h-8 w-8 text-cyan-600" />,
      path: '/dashboard/transmission',
      color: 'bg-cyan-50 dark:bg-cyan-950 border-l-4 border-cyan-500'
    },
    { 
      id: 'crypto', 
      name: 'Cryptographic Stamping', 
      description: 'FIRS cryptographic stamping for invoices',
      icon: <Shield className="h-8 w-8 text-cyan-600" />,
      path: '/dashboard/crypto-stamping',
      color: 'bg-cyan-50 dark:bg-cyan-950 border-l-4 border-cyan-500'
    }
  ];

  return (
    <div className={cn("enhanced-dashboard", className)}>
      {/* Overview section with metrics */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-semibold">Dashboard Overview</h2>
          <Button 
            variant="outline" 
            className="flex items-center space-x-2"
          >
            <Activity className="h-4 w-4" />
            <span>Refresh Metrics</span>
          </Button>
        </div>
        
        {/* Certificate Status Cards - APP Feature */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Badge variant="outline" className="mr-2 bg-cyan-50 text-cyan-700 border-cyan-200">
              APP
            </Badge>
            <h3 className="text-lg font-medium">Certificate Status</h3>
          </div>
          <CertificateStatusCards organizationId={organizationId} />
        </div>
        
        {/* Transmission Status Visualization - APP Feature */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Badge variant="outline" className="mr-2 bg-cyan-50 text-cyan-700 border-cyan-200">
              APP
            </Badge>
            <h3 className="text-lg font-medium">Recent Transmissions</h3>
          </div>
          <TransmissionStatusVisualization organizationId={organizationId} />
        </div>
      </div>

      {/* APP Modules Section with enhanced visual indicators */}
      <div className="mb-10 border-l-4 border-cyan-500 pl-4 py-2">
        <div className="flex items-center mb-4">
          <Badge variant="outline" className="mr-2 bg-cyan-100 text-cyan-800 border-cyan-300 font-semibold">
            APP
          </Badge>
          <h3 className="text-xl font-semibold">Access Point Provider Modules</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {appModules.map(module => (
            <Link href={module.path} key={module.id}>
              <Card className={cn(
                "h-full hover:shadow-md transition-shadow cursor-pointer",
                module.color
              )}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div className="p-2 rounded-lg">
                      {module.icon}
                    </div>
                  </div>
                  <CardTitle className="mt-2">{module.name}</CardTitle>
                  <CardDescription>{module.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>

      {/* SI Modules Section */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">System Integration Modules</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {siModules.map(module => (
            <Link href={module.path} key={module.id}>
              <Card className={cn(
                "h-full hover:shadow-md transition-shadow cursor-pointer",
                module.color
              )}>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div className="p-2 rounded-lg">
                      {module.icon}
                    </div>
                  </div>
                  <CardTitle className="mt-2">{module.name}</CardTitle>
                  <CardDescription>{module.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};

export default EnhancedDashboard;
