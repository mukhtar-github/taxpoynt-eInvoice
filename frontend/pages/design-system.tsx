/**
 * TaxPoynt Design System & Component Library
 * 
 * Permanent design system showcase for:
 * - Component documentation and testing
 * - Design consistency validation
 * - Developer onboarding and reference
 * - QA testing and regression detection
 */

import React, { useState } from 'react';
import { 
  Palette, 
  Component, 
  FileText, 
  Zap,
  CheckCircle,
  Settings
} from 'lucide-react';

import DashboardLayout from '@/components/layouts/DashboardLayout';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

// Import all Week 3 components for documentation
import { IntegrationStatusGrid } from '@/components/integrations';
import { EnhancedInput, LoadingButton, ProgressBar } from '@/components/ui';

const DesignSystem = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', name: 'Overview', icon: <Palette className="w-4 h-4" /> },
    { id: 'components', name: 'Components', icon: <Component className="w-4 h-4" /> },
    { id: 'forms', name: 'Forms', icon: <FileText className="w-4 h-4" /> },
    { id: 'integrations', name: 'Integrations', icon: <Settings className="w-4 h-4" /> },
    { id: 'animations', name: 'Animations', icon: <Zap className="w-4 h-4" /> }
  ];

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            TaxPoynt Design System
          </h1>
          <p className="text-gray-600">
            Component library, patterns, and guidelines for consistent UI/UX
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <Card className="p-4">
              <nav className="space-y-2">
                {sections.map((section) => (
                  <Button
                    key={section.id}
                    variant={activeSection === section.id ? 'default' : 'ghost'}
                    onClick={() => setActiveSection(section.id)}
                    className="w-full justify-start"
                  >
                    {section.icon}
                    <span className="ml-2">{section.name}</span>
                  </Button>
                ))}
              </nav>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeSection === 'overview' && (
              <Card className="p-6">
                <h2 className="text-xl font-semibold mb-4">Design System Overview</h2>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <h3 className="font-medium text-blue-900">Week 3 Enhanced</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Advanced components with mobile-first design
                    </p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <h3 className="font-medium text-green-900">Production Ready</h3>
                    <p className="text-sm text-green-700 mt-1">
                      Fully tested and documented components
                    </p>
                  </div>
                </div>
              </Card>
            )}

            {activeSection === 'components' && (
              <div className="space-y-6">
                <Card className="p-6">
                  <h2 className="text-xl font-semibold mb-4">UI Components</h2>
                  <div className="space-y-4">
                    <div>
                      <h3 className="font-medium mb-2">Buttons</h3>
                      <div className="flex gap-2">
                        <Button>Primary</Button>
                        <Button variant="outline">Outline</Button>
                        <Button variant="ghost">Ghost</Button>
                        <LoadingButton isLoading>Loading</LoadingButton>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="font-medium mb-2">Progress</h3>
                      <ProgressBar value={75} showPercentage animated />
                    </div>
                  </div>
                </Card>
              </div>
            )}

            {/* Add more sections as needed */}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-12 text-center">
          <Badge variant="outline" className="mb-2">
            Design System v3.0
          </Badge>
          <p className="text-sm text-gray-500">
            Updated with Week 3 enhancements • Mobile-first • Fully accessible
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default DesignSystem;