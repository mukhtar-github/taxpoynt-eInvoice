import React, { useState, useRef, useEffect } from 'react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { 
  ChevronDown, 
  ChevronRight, 
  Shield, 
  Database, 
  Cloud, 
  Settings,
  BarChart3,
  FileCheck,
  Users,
  Lock,
  Globe,
  Zap,
  CheckCircle,
  ArrowRight,
  Play,
  Pause,
  RotateCcw,
  Eye,
  EyeOff,
  Layers,
  Server,
  Cpu
} from 'lucide-react';

interface Capability {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  category: 'technical' | 'business' | 'security';
  features: {
    id: string;
    name: string;
    description: string;
    isAdvanced?: boolean;
    isPremium?: boolean;
  }[];
  technicalSpecs?: {
    label: string;
    value: string;
  }[];
}

interface PlatformCapabilitiesProps {
  className?: string;
  defaultExpanded?: string[];
}

export const PlatformCapabilities: React.FC<PlatformCapabilitiesProps> = ({
  className = '',
  defaultExpanded = []
}) => {
  const [expandedCapabilities, setExpandedCapabilities] = useState<Set<string>>(
    new Set(defaultExpanded)
  );
  const [visibleCapabilities, setVisibleCapabilities] = useState<string[]>([]);
  const [autoPlayDemo, setAutoPlayDemo] = useState(false);
  const [currentDemoStep, setCurrentDemoStep] = useState(0);
  const [showAdvancedFeatures, setShowAdvancedFeatures] = useState(false);
  const capabilityRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const capabilities: Capability[] = [
    {
      id: 'data-processing',
      icon: <Database className="h-8 w-8" />,
      title: 'Advanced Data Processing Engine',
      description: 'High-performance invoice processing with intelligent validation, transformation, and error handling capabilities.',
      category: 'technical',
      features: [
        {
          id: 'batch-processing',
          name: 'Batch Processing',
          description: 'Process thousands of invoices simultaneously with intelligent queuing'
        },
        {
          id: 'real-time-validation',
          name: 'Real-time Validation',
          description: 'Instant UBL 2.1 and FIRS compliance validation'
        },
        {
          id: 'data-transformation',
          name: 'Data Transformation',
          description: 'Automatic format conversion between systems',
          isAdvanced: true
        },
        {
          id: 'error-recovery',
          name: 'Error Recovery',
          description: 'Intelligent error detection and automatic correction',
          isAdvanced: true
        }
      ],
      technicalSpecs: [
        { label: 'Processing Speed', value: '10,000 invoices/hour' },
        { label: 'Uptime SLA', value: '99.9%' },
        { label: 'API Response Time', value: '<200ms' }
      ]
    },
    {
      id: 'integration-hub',
      icon: <Globe className="h-8 w-8" />,
      title: 'Universal Integration Hub',
      description: 'Connect with any ERP, CRM, or accounting system using our flexible integration framework and pre-built connectors.',
      category: 'technical',
      features: [
        {
          id: 'pre-built-connectors',
          name: 'Pre-built Connectors',
          description: 'Ready-to-use integrations for SAP, Odoo, Oracle, QuickBooks'
        },
        {
          id: 'custom-apis',
          name: 'Custom API Development',
          description: 'Build custom integrations using our comprehensive API suite'
        },
        {
          id: 'webhook-support',
          name: 'Webhook Support',
          description: 'Real-time event notifications and data synchronization',
          isAdvanced: true
        },
        {
          id: 'data-mapping',
          name: 'Intelligent Data Mapping',
          description: 'AI-powered field mapping and data transformation',
          isPremium: true
        }
      ],
      technicalSpecs: [
        { label: 'Supported Systems', value: '50+ integrations' },
        { label: 'API Endpoints', value: '200+ REST APIs' },
        { label: 'Webhook Events', value: '25+ event types' }
      ]
    },
    {
      id: 'security-compliance',
      icon: <Shield className="h-8 w-8" />,
      title: 'Enterprise Security & Compliance',
      description: 'Bank-grade security infrastructure with comprehensive compliance management and audit trail capabilities.',
      category: 'security',
      features: [
        {
          id: 'encryption',
          name: 'End-to-End Encryption',
          description: '256-bit SSL encryption for all data transmission'
        },
        {
          id: 'access-control',
          name: 'Role-Based Access Control',
          description: 'Granular permissions and user management'
        },
        {
          id: 'audit-logging',
          name: 'Comprehensive Audit Logging',
          description: 'Complete activity tracking and compliance reporting',
          isAdvanced: true
        },
        {
          id: 'certificate-management',
          name: 'Digital Certificate Management',
          description: 'Automatic certificate lifecycle management',
          isPremium: true
        }
      ],
      technicalSpecs: [
        { label: 'Security Certifications', value: 'ISO 27001, SOC 2' },
        { label: 'Data Retention', value: '7 years' },
        { label: 'Backup Frequency', value: 'Real-time' }
      ]
    },
    {
      id: 'analytics-reporting',
      icon: <BarChart3 className="h-8 w-8" />,
      title: 'Advanced Analytics & Reporting',
      description: 'Comprehensive business intelligence with real-time dashboards, custom reports, and predictive analytics.',
      category: 'business',
      features: [
        {
          id: 'real-time-dashboard',
          name: 'Real-time Dashboard',
          description: 'Live monitoring of invoice processing and compliance status'
        },
        {
          id: 'custom-reports',
          name: 'Custom Report Builder',
          description: 'Create tailored reports for your business needs'
        },
        {
          id: 'predictive-analytics',
          name: 'Predictive Analytics',
          description: 'AI-powered insights and forecasting',
          isAdvanced: true
        },
        {
          id: 'automated-alerts',
          name: 'Automated Alerts',
          description: 'Smart notifications for critical events and thresholds',
          isPremium: true
        }
      ],
      technicalSpecs: [
        { label: 'Data Points', value: '100+ metrics tracked' },
        { label: 'Report Formats', value: 'PDF, Excel, CSV, API' },
        { label: 'Refresh Rate', value: 'Real-time to daily' }
      ]
    },
    {
      id: 'workflow-automation',
      icon: <Settings className="h-8 w-8" />,
      title: 'Intelligent Workflow Automation',
      description: 'Automate complex business processes with configurable workflows, approval chains, and smart routing.',
      category: 'business',
      features: [
        {
          id: 'approval-workflows',
          name: 'Approval Workflows',
          description: 'Configurable multi-step approval processes'
        },
        {
          id: 'smart-routing',
          name: 'Smart Invoice Routing',
          description: 'Intelligent document routing based on rules and conditions'
        },
        {
          id: 'exception-handling',
          name: 'Exception Handling',
          description: 'Automated handling of edge cases and errors',
          isAdvanced: true
        },
        {
          id: 'ai-optimization',
          name: 'AI Process Optimization',
          description: 'Machine learning-powered workflow improvements',
          isPremium: true
        }
      ],
      technicalSpecs: [
        { label: 'Workflow Templates', value: '20+ pre-built' },
        { label: 'Custom Rules', value: 'Unlimited' },
        { label: 'Processing Time', value: '<5 minutes avg' }
      ]
    },
    {
      id: 'cloud-infrastructure',
      icon: <Cloud className="h-8 w-8" />,
      title: 'Scalable Cloud Infrastructure',
      description: 'Enterprise-grade cloud platform with automatic scaling, global availability, and disaster recovery.',
      category: 'technical',
      features: [
        {
          id: 'auto-scaling',
          name: 'Auto-scaling',
          description: 'Automatic resource scaling based on demand'
        },
        {
          id: 'global-cdn',
          name: 'Global CDN',
          description: 'Fast content delivery worldwide'
        },
        {
          id: 'disaster-recovery',
          name: 'Disaster Recovery',
          description: 'Multi-region backup and failover systems',
          isAdvanced: true
        },
        {
          id: 'edge-computing',
          name: 'Edge Computing',
          description: 'Distributed processing for ultra-low latency',
          isPremium: true
        }
      ],
      technicalSpecs: [
        { label: 'Availability Zones', value: '3+ regions' },
        { label: 'Scaling Capacity', value: '1000x auto-scale' },
        { label: 'Recovery Time', value: '<5 minutes RTO' }
      ]
    }
  ];

  // Intersection Observer for animations
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    
    capabilities.forEach((capability, index) => {
      const ref = capabilityRefs.current[capability.id];
      if (!ref) return;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              setVisibleCapabilities(prev => [...new Set([...prev, capability.id])]);
            }, index * 200);
          }
        },
        { threshold: 0.2 }
      );
      
      observer.observe(ref);
      observers.push(observer);
    });

    return () => {
      observers.forEach(observer => observer.disconnect());
    };
  }, [capabilities]);

  // Auto-play demo functionality
  useEffect(() => {
    if (!autoPlayDemo) return;

    const interval = setInterval(() => {
      setCurrentDemoStep(prev => (prev + 1) % capabilities.length);
      
      // Auto-expand the current capability
      const currentCapability = capabilities[currentDemoStep];
      if (currentCapability) {
        setExpandedCapabilities(prev => new Set([...prev, currentCapability.id]));
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [autoPlayDemo, currentDemoStep, capabilities]);

  const toggleCapability = (capabilityId: string) => {
    setExpandedCapabilities(prev => {
      const newSet = new Set(prev);
      if (newSet.has(capabilityId)) {
        newSet.delete(capabilityId);
      } else {
        newSet.add(capabilityId);
      }
      return newSet;
    });
  };

  const expandAll = () => {
    setExpandedCapabilities(new Set(capabilities.map(c => c.id)));
  };

  const collapseAll = () => {
    setExpandedCapabilities(new Set());
  };

  const getCategoryColor = (category: string) => {
    const colorMap = {
      technical: 'blue',
      business: 'green',
      security: 'red'
    };
    return colorMap[category as keyof typeof colorMap] || 'gray';
  };

  const getCategoryClasses = (category: string) => {
    const color = getCategoryColor(category);
    return {
      icon: `text-${color}-600 bg-${color}-50`,
      border: `border-${color}-200 hover:border-${color}-300`,
      badge: `bg-${color}-100 text-${color}-700`
    };
  };

  return (
    <div className={`py-20 bg-gradient-to-b from-gray-100 to-gray-200 ${className}`}>
      <div className="container mx-auto px-4">
        
        {/* Section Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 bg-blue-100 text-blue-800 px-4 py-2 rounded-full mb-6">
            <Cpu className="h-4 w-4" />
            <span className="font-medium text-sm">Platform Architecture</span>
          </div>
          
          <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Platform Capabilities Overview
          </Typography.Heading>
          
          <Typography.Text size="lg" className="text-gray-600 leading-relaxed mb-8">
            Explore the comprehensive technical and business capabilities that power TaxPoynt's e-invoicing platform. 
            Click any section to discover detailed features and specifications.
          </Typography.Text>

          {/* Demo Controls */}
          <div className="flex flex-wrap justify-center gap-4 mb-8">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoPlayDemo(!autoPlayDemo)}
              className="inline-flex items-center space-x-2"
            >
              {autoPlayDemo ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              <span>{autoPlayDemo ? 'Pause' : 'Start'} Demo</span>
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={expandAll}
              className="inline-flex items-center space-x-2"
            >
              <ChevronDown className="h-4 w-4" />
              <span>Expand All</span>
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={collapseAll}
              className="inline-flex items-center space-x-2"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Collapse All</span>
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAdvancedFeatures(!showAdvancedFeatures)}
              className="inline-flex items-center space-x-2"
            >
              {showAdvancedFeatures ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              <span>{showAdvancedFeatures ? 'Hide' : 'Show'} Advanced</span>
            </Button>
          </div>
        </div>

        {/* Capabilities Grid */}
        <div className="space-y-6">
          {capabilities.map((capability, index) => {
            const isExpanded = expandedCapabilities.has(capability.id);
            const isVisible = visibleCapabilities.includes(capability.id);
            const isDemoActive = autoPlayDemo && currentDemoStep === index;
            const categoryClasses = getCategoryClasses(capability.category);

            return (
              <div
                key={capability.id}
                ref={el => capabilityRefs.current[capability.id] = el}
                className={`transform transition-all duration-700 ease-out ${
                  isVisible ? 'translate-y-0 opacity-100' : 'translate-y-8 opacity-0'
                }`}
              >
                <Card className={`border-2 hover:shadow-lg transition-all duration-300 ${categoryClasses.border} ${
                  isDemoActive ? 'ring-4 ring-primary-200 shadow-xl' : ''
                }`}>
                  
                  {/* Header */}
                  <div 
                    className="cursor-pointer"
                    onClick={() => toggleCapability(capability.id)}
                  >
                    <CardContent className="p-6 md:p-8">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-4">
                          <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${categoryClasses.icon}`}>
                            {capability.icon}
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center space-x-3 mb-2">
                              <Typography.Heading level="h3" className="text-xl font-bold text-gray-900">
                                {capability.title}
                              </Typography.Heading>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${categoryClasses.badge}`}>
                                {capability.category.toUpperCase()}
                              </span>
                            </div>
                            <Typography.Text className="text-gray-600">
                              {capability.description}
                            </Typography.Text>
                          </div>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          {isDemoActive && (
                            <div className="w-3 h-3 bg-primary-500 rounded-full animate-pulse"></div>
                          )}
                          <ChevronRight className={`h-5 w-5 text-gray-400 transition-transform duration-200 ${
                            isExpanded ? 'rotate-90' : ''
                          }`} />
                        </div>
                      </div>
                    </CardContent>
                  </div>

                  {/* Expandable Content */}
                  <div className={`overflow-hidden transition-all duration-500 ease-in-out ${
                    isExpanded ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0'
                  }`}>
                    <div className="border-t border-gray-100 p-6 md:p-8 bg-gray-50/50">
                      
                      {/* Features Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                        {capability.features
                          .filter(feature => showAdvancedFeatures || (!feature.isAdvanced && !feature.isPremium))
                          .map((feature, featureIndex) => (
                          <div 
                            key={feature.id}
                            className={`p-4 rounded-lg border transition-all duration-300 hover:shadow-md ${
                              feature.isPremium ? 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200' :
                              feature.isAdvanced ? 'bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200' :
                              'bg-white border-gray-200'
                            }`}
                            style={{ animationDelay: `${featureIndex * 100}ms` }}
                          >
                            <div className="flex items-start space-x-3">
                              <CheckCircle className={`h-5 w-5 mt-0.5 flex-shrink-0 ${
                                feature.isPremium ? 'text-yellow-600' :
                                feature.isAdvanced ? 'text-blue-600' :
                                'text-green-600'
                              }`} />
                              <div>
                                <div className="flex items-center space-x-2 mb-1">
                                  <Typography.Text className="font-semibold text-gray-900">
                                    {feature.name}
                                  </Typography.Text>
                                  {feature.isPremium && (
                                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-yellow-200 text-yellow-800">
                                      PREMIUM
                                    </span>
                                  )}
                                  {feature.isAdvanced && (
                                    <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-blue-200 text-blue-800">
                                      ADVANCED
                                    </span>
                                  )}
                                </div>
                                <Typography.Text className="text-sm text-gray-600">
                                  {feature.description}
                                </Typography.Text>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Technical Specifications */}
                      {capability.technicalSpecs && (
                        <div className="bg-white rounded-lg p-4 border border-gray-200">
                          <Typography.Heading level="h4" className="text-sm font-semibold text-gray-700 mb-3">
                            Technical Specifications
                          </Typography.Heading>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            {capability.technicalSpecs.map((spec, specIndex) => (
                              <div key={specIndex} className="text-center">
                                <div className="font-bold text-lg text-primary-600">
                                  {spec.value}
                                </div>
                                <div className="text-sm text-gray-600">
                                  {spec.label}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <Card className="border-none shadow-lg bg-gradient-to-r from-primary-600 to-primary-700 text-white hover:shadow-xl transition-shadow">
            <CardContent className="p-12">
              <Typography.Heading level="h3" className="text-2xl md:text-3xl font-bold mb-4">
                Experience the Full Platform
              </Typography.Heading>
              
              <Typography.Text size="lg" className="text-white/90 mb-8 max-w-2xl mx-auto">
                See how all these capabilities work together in a live demonstration tailored to your business needs.
              </Typography.Text>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  size="lg"
                  className="bg-gray-200 text-gray-900 hover:bg-gray-300 font-bold"
                >
                  Schedule Live Demo
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                >
                  Download Technical Specs
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default PlatformCapabilities;