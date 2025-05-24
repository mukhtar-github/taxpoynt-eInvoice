import React, { useState, useEffect } from "react";
import { NextPage } from "next";
import MainLayout from "../components/layouts/MainLayout";
import { Typography } from "../components/ui/Typography";
import { Card, CardHeader, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../components/ui/Tabs";
import FIRSTestForm from "../components/firs/FIRSTestForm";
import FIRSStatusCheck from "../components/firs/FIRSStatusCheck";
import FIRSBatchSubmit from "../components/firs/FIRSBatchSubmit";
import FIRSSettings from "../components/firs/FIRSSettings";
import withFirsAuth from "../components/firs/withFirsAuth";
import { AlertCircle, CheckCircle, Terminal, Settings, FileText, BarChart2, ArrowRight, Zap } from "lucide-react";

const FIRSTestPage: NextPage = () => {
  const [activeTab, setActiveTab] = useState("submit");
  const [isSandboxMode, setIsSandboxMode] = useState(true);
  const [submissionId, setSubmissionId] = useState("");
  const [pageLoaded, setPageLoaded] = useState(false);

  // Add animation effect on page load
  useEffect(() => {
    setPageLoaded(true);
  }, []);

  // When a submission is successful, switch to status tab and pass ID
  const handleSubmissionSuccess = (submissionId: string) => {
    setSubmissionId(submissionId);
    setActiveTab("status");
  };

  return (
    <MainLayout
      title="FIRS API Testing Dashboard"
      description="Test FIRS e-Invoice API submission process with sandbox and production environments"
    >
      <div className={`container mx-auto px-4 py-8 transition-all duration-500 ${pageLoaded ? "opacity-100" : "opacity-0"}`}>
        {/* Dashboard Hero Section */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-lg shadow-lg mb-8 p-8 text-white transition-all duration-300 transform hover:scale-[1.01]">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="p-3 bg-white bg-opacity-20 rounded-full mr-4">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold mb-2">FIRS API Testing Dashboard</h1>
                <p className="text-blue-100">Complete end-to-end testing environment for Odoo → UBL → FIRS workflow</p>
              </div>
            </div>
            <Badge className={`px-4 py-2 text-lg font-semibold ${isSandboxMode ? "bg-yellow-500 hover:bg-yellow-600" : "bg-red-500 hover:bg-red-600"} transition-colors duration-200`}>
              {isSandboxMode ? "Sandbox Mode" : "Production Mode"}
            </Badge>
          </div>
        </div>
        </div>      
        <div className="container mx-auto px-4">
        <div className="flex justify-between items-center mb-6">
          <Typography.Heading level="h1">FIRS API Testing Dashboard</Typography.Heading>
          <Badge className={isSandboxMode ? 'bg-yellow-500' : 'bg-red-500'}>
            {isSandboxMode ? 'Sandbox Mode' : 'Production Mode'}
          </Badge>
        </div>

        {!isSandboxMode && (
          <div className="bg-gradient-to-r from-yellow-50 to-orange-50 border-l-4 border-yellow-500 rounded-md shadow-md p-6 mb-6 animate-pulse">
            <div className="flex items-center">
              <div className="flex-shrink-0 bg-yellow-100 p-2 rounded-full">
                <AlertCircle className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <Typography.Heading level="h4" className="text-yellow-700 font-bold">Production Mode Warning</Typography.Heading>
                <Typography.Text className="text-yellow-700 mt-1">You are in PRODUCTION mode. All API calls will use the live FIRS API and may incur fees or affect real data.</Typography.Text>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div className="lg:col-span-1">
            <Card className="mb-6 border border-gray-200 shadow-lg rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-blue-700 text-white py-5">
                <div className="flex items-center">
                  <Terminal className="mr-2 h-5 w-5" />
                  <Typography.Heading level="h3" className="text-white font-bold">API Operations</Typography.Heading>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="flex flex-col">
                  <Button 
                    variant={activeTab === "submit" ? "default" : "ghost"} 
                    onClick={() => setActiveTab("submit")}
                    className={`w-full rounded-none py-4 px-4 flex items-center justify-start border-l-4 ${activeTab === "submit" ? "border-blue-600 bg-blue-50" : "border-transparent"} transition-all duration-200`}
                  >
                    <FileText className="mr-2 h-5 w-5" />
                    <span>Submit Invoice</span>
                    {activeTab === "submit" && <ArrowRight className="ml-auto h-4 w-4" />}
                  </Button>
                  <Button 
                    variant={activeTab === "status" ? "default" : "ghost"} 
                    onClick={() => setActiveTab("status")}
                    className={`w-full rounded-none py-4 px-4 flex items-center justify-start border-l-4 ${activeTab === "status" ? "border-blue-600 bg-blue-50" : "border-transparent"} transition-all duration-200`}
                  >
                    <CheckCircle className="mr-2 h-5 w-5" />
                    <span>Check Status</span>
                    {activeTab === "status" && <ArrowRight className="ml-auto h-4 w-4" />}
                  </Button>
                  <Button 
                    variant={activeTab === "batch" ? "default" : "ghost"} 
                    onClick={() => setActiveTab("batch")}
                    className={`w-full rounded-none py-4 px-4 flex items-center justify-start border-l-4 ${activeTab === "batch" ? "border-blue-600 bg-blue-50" : "border-transparent"} transition-all duration-200`}
                  >
                    <BarChart2 className="mr-2 h-5 w-5" />
                    <span>Batch Submit</span>
                    {activeTab === "batch" && <ArrowRight className="ml-auto h-4 w-4" />}
                  </Button>
                  <Button 
                    variant={activeTab === "settings" ? "default" : "ghost"} 
                    onClick={() => setActiveTab("settings")}
                    className={`w-full rounded-none py-4 px-4 flex items-center justify-start border-l-4 ${activeTab === "settings" ? "border-blue-600 bg-blue-50" : "border-transparent"} transition-all duration-200`}
                  >
                    <Settings className="mr-2 h-5 w-5" />
                    <span>Settings</span>
                    {activeTab === "settings" && <ArrowRight className="ml-auto h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>

            <Card className="border border-gray-200 shadow-lg rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl">
              <CardHeader className="bg-gradient-to-r from-blue-500 to-blue-600 text-white py-5">
                <div className="flex items-center">
                  <Settings className="mr-2 h-5 w-5" />
                  <Typography.Heading level="h3" className="text-white font-bold">Environment</Typography.Heading>
                </div>
              </CardHeader>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-6 bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <div className="flex-1">
                    <label htmlFor="sandboxToggle" className="font-medium">
                      {isSandboxMode ? "Sandbox Mode (Testing)" : "Production Mode (Live)"}
                    </label>
                    <p className="text-sm text-gray-500 mt-1">
                      {isSandboxMode ? "Safe environment for testing" : "Live environment with real data"}
                    </p>
                  </div>
                  <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
                    <input
                      type="checkbox"
                      id="sandboxToggle"
                      className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer focus:outline-none"
                      checked={isSandboxMode}
                      onChange={(e) => {
                        if (!e.target.checked) {
                          if (window.confirm("WARNING: You are switching to PRODUCTION mode. All API calls will use the live FIRS API. Continue?")) {
                            setIsSandboxMode(false);
                          }
                        } else {
                          setIsSandboxMode(true);
                        }
                      }}
                      style={{
                        right: isSandboxMode ? "0" : "auto",
                        left: isSandboxMode ? "auto" : "0",
                        borderColor: isSandboxMode ? "#3b82f6" : "#ef4444"
                      }}
                    />
                    <label
                      htmlFor="sandboxToggle"
                      className="toggle-label block overflow-hidden h-6 rounded-full cursor-pointer"
                      style={{
                        backgroundColor: isSandboxMode ? "#93c5fd" : "#fca5a5"
                      }}
                    ></label>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  className="w-full flex items-center justify-center bg-white hover:bg-blue-50 border-blue-200 text-blue-600 hover:text-blue-700 font-medium transition-colors duration-200"
                  onClick={() => {
                    fetch("/health")
                      .then(response => {
                        if (response.ok) {
                          alert("Connection successful. API server is online and responding.");
                        } else {
                          alert(`Connection issue. Server responded with status: ${response.status}`);
                        }
                      })
                      .catch(error => {
                        alert(`Connection failed: ${error.message}`);
                      });
                  }}
                >
                  <Terminal className="mr-2 h-4 w-4" />
                  Test API Connection
                </Button>
              </CardContent>
            </Card>
          </div>

          <div className="lg:col-span-3">
            <Card className="border border-gray-200 shadow-lg rounded-lg overflow-hidden transition-all duration-300 hover:shadow-xl h-full">
              <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200 py-5">
                <div className="flex items-center">
                  {activeTab === "submit" && <FileText className="mr-2 h-5 w-5 text-blue-600" />}
                  {activeTab === "status" && <CheckCircle className="mr-2 h-5 w-5 text-blue-600" />}
                  {activeTab === "batch" && <BarChart2 className="mr-2 h-5 w-5 text-blue-600" />}
                  {activeTab === "settings" && <Settings className="mr-2 h-5 w-5 text-blue-600" />}
                  <Typography.Heading level="h3" className="font-bold text-gray-800">
                    {activeTab === "submit" && "Submit Invoice to FIRS"}
                    {activeTab === "status" && "Check Submission Status"}
                    {activeTab === "batch" && "Batch Process Invoices"}
                    {activeTab === "settings" && "API Configuration Settings"}
                  </Typography.Heading>
                </div>
              </CardHeader>
              <CardContent className="p-6 bg-white">
                <div className="transition-all duration-500 transform">
                  {activeTab === "submit" && (
                    <FIRSTestForm 
                      sandboxMode={isSandboxMode} 
                      onSubmissionSuccess={handleSubmissionSuccess}
                    />
                  )}

                  {activeTab === "status" && (
                    <FIRSStatusCheck 
                      sandboxMode={isSandboxMode}
                      initialSubmissionId={submissionId}
                    />
                  )}

                  {activeTab === "batch" && (
                    <FIRSBatchSubmit 
                      sandboxMode={isSandboxMode}
                    />
                  )}

                  {activeTab === "settings" && (
                    <FIRSSettings />
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
        
        {/* Workflow Visualization - Add this to illustrate the Odoo → UBL → FIRS workflow */}
        <div className="mt-10 px-4 py-8 bg-white rounded-lg shadow-lg border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">Complete E2E Testing Workflow</h2>
          <div className="flex flex-col md:flex-row justify-between items-center max-w-4xl mx-auto">
            <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
              <div className="bg-blue-100 p-4 rounded-full mb-3">
                <svg className="h-8 w-8 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M20 7h-7m0 0v7m0-7l-3-3m-3-3H4m0 0v7m0-7l3-3" />
                </svg>
              </div>
              <h3 className="font-bold text-lg text-center">Odoo Integration</h3>
              <p className="text-gray-600 text-center text-sm mt-2">Fetch invoice data from Odoo</p>
            </div>
            
            <div className="hidden md:block text-blue-500">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>
            
            <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
              <div className="bg-indigo-100 p-4 rounded-full mb-3">
                <svg className="h-8 w-8 text-indigo-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 3v4a1 1 0 001 1h4" />
                  <path d="M17 21H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="font-bold text-lg text-center">UBL Transformation</h3>
              <p className="text-gray-600 text-center text-sm mt-2">Convert to BIS Billing 3.0 format</p>
            </div>
            
            <div className="hidden md:block text-blue-500">
              <svg className="h-8 w-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>
            
            <div className="flex flex-col items-center p-4 transition-all duration-300 transform hover:scale-105">
              <div className="bg-green-100 p-4 rounded-full mb-3">
                <svg className="h-8 w-8 text-green-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-bold text-lg text-center">FIRS Submission</h3>
              <p className="text-gray-600 text-center text-sm mt-2">Submit to FIRS & check status</p>
            </div>
          </div>
        </div>

      </div>
      
      {/* Add custom styles for the toggle switch */}
      <style jsx>{`
        .toggle-checkbox:checked {
          right: 0;
          border-color: #3b82f6;
        }
        .toggle-checkbox:not(:checked) {
          left: 0;
          border-color: #ef4444;
        }
        .toggle-label {
          transition: background-color 0.2s ease;
        }
      `}</style>
    </MainLayout>
  );
};

// Apply authentication wrapper to ensure only authenticated users can access this page
export default withFirsAuth(FIRSTestPage);
