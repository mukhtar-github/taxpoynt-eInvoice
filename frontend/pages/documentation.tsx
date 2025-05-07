import React, { useState } from 'react';
import Head from 'next/head';
import MainLayout from '../components/layouts/MainLayout';
import { Container } from '../components/ui/Grid';
import { Typography } from '../components/ui/Typography';
import { Tabs } from '../components/ui/Tabs';
import { Card, CardContent } from '../components/ui/Card';
import { Search } from 'lucide-react';
import { Button } from '../components/ui/Button';

// Documentation sections
type Section = {
  id: string;
  title: string;
  icon?: React.ReactNode;
  content: React.ReactNode;
};

const DocumentationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState('user-guide');
  const [searchTerm, setSearchTerm] = useState('');

  // Documentation sections
  const sections: Section[] = [
    {
      id: 'user-guide',
      title: 'User Guide',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">User Guide</Typography.Heading>
          <Typography.Text className="mb-6">
            Comprehensive guide on how to use the Taxpoynt eInvoice system, from setup to advanced features.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain detailed user guides for the eInvoice system.
              </Typography.Text>
            </CardContent>
          </Card>
        </div>
      )
    },
    {
      id: 'tutorials',
      title: 'Tutorials',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Tutorials</Typography.Heading>
          <Typography.Text className="mb-6">
            Step-by-step tutorials for common tasks and workflows in the Taxpoynt eInvoice system.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain interactive tutorials for common eInvoice tasks.
              </Typography.Text>
            </CardContent>
          </Card>
        </div>
      )
    },
    {
      id: 'api-docs',
      title: 'API Documentation',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">API Documentation</Typography.Heading>
          <Typography.Text className="mb-6">
            Technical documentation for developers integrating with the Taxpoynt eInvoice API.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain API references, authentication details, and code examples.
              </Typography.Text>
            </CardContent>
          </Card>
        </div>
      )
    },
    {
      id: 'legal',
      title: 'Legal',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Legal Information</Typography.Heading>
          <Typography.Text className="mb-6">
            Licensing, terms of service, and legal agreements for the Taxpoynt eInvoice system.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain terms of service, privacy policy, and licensing information.
              </Typography.Text>
            </CardContent>
          </Card>
        </div>
      )
    },
    {
      id: 'faq',
      title: 'FAQ',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Frequently Asked Questions</Typography.Heading>
          <Typography.Text className="mb-6">
            Answers to common questions about the Taxpoynt eInvoice system.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain frequently asked questions and their answers.
              </Typography.Text>
            </CardContent>
          </Card>
        </div>
      )
    },
    {
      id: 'troubleshooting',
      title: 'Troubleshooting',
      content: (
        <div>
          <Typography.Heading level="h2" className="mb-4">Troubleshooting Guide</Typography.Heading>
          <Typography.Text className="mb-6">
            Solutions to common issues and problems you might encounter using the system.
          </Typography.Text>
          
          {/* Placeholder for section content - to be filled in as the system develops */}
          <Card>
            <CardContent className="p-8 text-center">
              <Typography.Text variant="secondary">
                This section is under development and will contain troubleshooting guides and solutions to common problems.
              </Typography.Text>
            </CardContent>
          </Card>
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
