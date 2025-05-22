import React, { useState, useEffect } from 'react';
import { NextPage } from 'next';
import MainLayout from '../components/layouts/MainLayout';
import { Typography } from '../components/ui/Typography';
import { Card, CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs';
import FIRSTestForm from '../components/firs/FIRSTestForm';
import FIRSStatusCheck from '../components/firs/FIRSStatusCheck';
import FIRSBatchSubmit from '../components/firs/FIRSBatchSubmit';
import FIRSSettings from '../components/firs/FIRSSettings';
import withFirsAuth from '../components/firs/withFirsAuth';

const FIRSTestPage: NextPage = () => {
  const [activeTab, setActiveTab] = useState('submit');
  const [isSandboxMode, setIsSandboxMode] = useState(true);
  const [submissionId, setSubmissionId] = useState('');

  // When a submission is successful, switch to status tab and pass ID
  const handleSubmissionSuccess = (submissionId: string) => {
    setSubmissionId(submissionId);
    setActiveTab('status');
  };

  return (
    <MainLayout
      title="FIRS API Testing Dashboard"
      description="Test FIRS e-Invoice API submission process with sandbox and production environments"
    >
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <Typography.Heading level="h1">FIRS API Testing Dashboard</Typography.Heading>
          <Badge className={isSandboxMode ? 'bg-yellow-500' : 'bg-red-500'}>
            {isSandboxMode ? 'Sandbox Mode' : 'Production Mode'}
          </Badge>
        </div>

        {!isSandboxMode && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4 mb-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-500" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <Typography.Heading level="h4" className="text-yellow-700">Production Mode Warning</Typography.Heading>
                <Typography.Text className="text-yellow-700">You are in PRODUCTION mode. All API calls will use the live FIRS API and may incur fees or affect real data.</Typography.Text>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader className="bg-blue-600 text-white">
                <Typography.Heading level="h3" className="text-white">API Operations</Typography.Heading>
              </CardHeader>
              <CardContent>
                <div className="flex flex-col space-y-2">
                  <Button 
                    variant={activeTab === 'submit' ? 'default' : 'ghost'} 
                    onClick={() => setActiveTab('submit')}
                    className="w-full"
                  >
                    Submit Invoice
                  </Button>
                  <Button 
                    variant={activeTab === 'status' ? 'default' : 'ghost'} 
                    onClick={() => setActiveTab('status')}
                    className="w-full"
                  >
                    Check Status
                  </Button>
                  <Button 
                    variant={activeTab === 'batch' ? 'default' : 'ghost'} 
                    onClick={() => setActiveTab('batch')}
                    className="w-full"
                  >
                    Batch Submit
                  </Button>
                  <Button 
                    variant={activeTab === 'settings' ? 'default' : 'ghost'} 
                    onClick={() => setActiveTab('settings')}
                    className="w-full"
                  >
                    Settings
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="bg-blue-400 text-white">
                <Typography.Heading level="h3" className="text-white">Environment</Typography.Heading>
              </CardHeader>
              <CardContent>
                <div className="flex items-center mb-4">
                  <input
                    type="checkbox"
                    id="sandboxToggle"
                    className="mr-2"
                    checked={isSandboxMode}
                    onChange={(e) => {
                      if (!e.target.checked) {
                        if (window.confirm('WARNING: You are switching to PRODUCTION mode. All API calls will use the live FIRS API. Continue?')) {
                          setIsSandboxMode(false);
                        }
                      } else {
                        setIsSandboxMode(true);
                      }
                    }}
                  />
                  <label htmlFor="sandboxToggle">Sandbox Mode</label>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => {
                    fetch('/health')
                      .then(response => {
                        if (response.ok) {
                          alert('Connection successful. API server is online and responding.');
                        } else {
                          alert(`Connection issue. Server responded with status: ${response.status}`);
                        }
                      })
                      .catch(error => {
                        alert(`Connection failed: ${error.message}`);
                      });
                  }}
                >
                  Test Connection
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            {activeTab === 'submit' && (
              <FIRSTestForm 
                sandboxMode={isSandboxMode} 
                onSubmissionSuccess={handleSubmissionSuccess}
              />
            )}

            {activeTab === 'status' && (
              <FIRSStatusCheck 
                sandboxMode={isSandboxMode}
                initialSubmissionId={submissionId}
              />
            )}

            {activeTab === 'batch' && (
              <FIRSBatchSubmit 
                sandboxMode={isSandboxMode}
              />
            )}

            {activeTab === 'settings' && (
              <FIRSSettings />
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

// Apply authentication wrapper to ensure only authenticated users can access this page
export default withFirsAuth(FIRSTestPage);
