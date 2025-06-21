import React, { useState, useEffect, useRef } from 'react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { 
  Database, 
  Server, 
  Cloud, 
  Layers,
  GitMerge,
  Zap,
  CheckCircle,
  ArrowRight,
  Building,
  ShoppingCart,
  Users,
  BarChart3,
  Globe,
  Settings,
  Smartphone,
  Monitor,
  Wifi,
  HardDrive,
  Play,
  Pause,
  Filter,
  Search,
  Eye
} from 'lucide-react';

interface Integration {
  id: string;
  name: string;
  category: 'erp' | 'crm' | 'pos' | 'accounting' | 'ecommerce' | 'government';
  icon: React.ReactNode;
  description: string;
  status: 'production' | 'beta' | 'coming-soon';
  popularity: number; // 1-5 scale
  features: string[];
  technicalSpecs: {
    method: string;
    protocol: string;
    realTime: boolean;
    dataSync: 'bidirectional' | 'unidirectional';
  };
  setupTime: string;
  complexity: 'simple' | 'moderate' | 'advanced';
}

interface IntegrationEcosystemProps {
  className?: string;
  showFilters?: boolean;
  maxIntegrations?: number;
}

export const IntegrationEcosystem: React.FC<IntegrationEcosystemProps> = ({
  className = '',
  showFilters = true,
  maxIntegrations
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedComplexity, setSelectedComplexity] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [visibleIntegrations, setVisibleIntegrations] = useState<string[]>([]);
  const [hoveredIntegration, setHoveredIntegration] = useState<string | null>(null);
  const [autoRotate, setAutoRotate] = useState(false);
  const [currentRotation, setCurrentRotation] = useState(0);
  const integrationRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const integrations: Integration[] = [
    {
      id: 'sap',
      name: 'SAP ERP',
      category: 'erp',
      icon: <Database className="h-8 w-8" />,
      description: 'Enterprise-grade SAP integration with real-time invoice synchronization and comprehensive data mapping.',
      status: 'production',
      popularity: 5,
      features: ['Real-time sync', 'Custom field mapping', 'Batch processing', 'Error handling'],
      technicalSpecs: {
        method: 'SAP API',
        protocol: 'RFC/SOAP',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '2-3 weeks',
      complexity: 'advanced'
    },
    {
      id: 'odoo',
      name: 'Odoo',
      category: 'erp',
      icon: <Server className="h-8 w-8" />,
      description: 'Seamless Odoo integration for small to medium businesses with automated invoice processing.',
      status: 'production',
      popularity: 4,
      features: ['Direct API integration', 'Module compatibility', 'Custom workflows', 'Multi-company support'],
      technicalSpecs: {
        method: 'REST API',
        protocol: 'HTTP/JSON',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '1-2 days',
      complexity: 'simple'
    },
    {
      id: 'oracle',
      name: 'Oracle ERP Cloud',
      category: 'erp',
      icon: <HardDrive className="h-8 w-8" />,
      description: 'Oracle ERP Cloud integration with enterprise security and scalable data processing.',
      status: 'production',
      popularity: 4,
      features: ['Cloud-native', 'Enterprise security', 'Bulk operations', 'Audit trails'],
      technicalSpecs: {
        method: 'REST API',
        protocol: 'HTTPS/JSON',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '1-2 weeks',
      complexity: 'moderate'
    },
    {
      id: 'quickbooks',
      name: 'QuickBooks',
      category: 'accounting',
      icon: <Layers className="h-8 w-8" />,
      description: 'QuickBooks integration designed for small businesses and accounting firms.',
      status: 'production',
      popularity: 5,
      features: ['Quick setup', 'Automated sync', 'Tax calculation', 'Report generation'],
      technicalSpecs: {
        method: 'QuickBooks API',
        protocol: 'OAuth 2.0',
        realTime: false,
        dataSync: 'bidirectional'
      },
      setupTime: '1 day',
      complexity: 'simple'
    },
    {
      id: 'dynamics',
      name: 'Microsoft Dynamics 365',
      category: 'erp',
      icon: <GitMerge className="h-8 w-8" />,
      description: 'Complete Microsoft Dynamics 365 integration with Power Platform compatibility.',
      status: 'production',
      popularity: 4,
      features: ['Power Platform', 'Azure integration', 'AI insights', 'Custom connectors'],
      technicalSpecs: {
        method: 'Graph API',
        protocol: 'REST/OData',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '1 week',
      complexity: 'moderate'
    },
    {
      id: 'hubspot',
      name: 'HubSpot CRM',
      category: 'crm',
      icon: <Users className="h-8 w-8" />,
      description: 'HubSpot CRM integration for seamless customer invoice management and sales tracking.',
      status: 'beta',
      popularity: 4,
      features: ['Deal tracking', 'Contact sync', 'Pipeline automation', 'Custom properties'],
      technicalSpecs: {
        method: 'HubSpot API',
        protocol: 'REST/JSON',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '2-3 days',
      complexity: 'simple'
    },
    {
      id: 'salesforce',
      name: 'Salesforce',
      category: 'crm',
      icon: <Cloud className="h-8 w-8" />,
      description: 'Salesforce integration with advanced customer relationship and invoice lifecycle management.',
      status: 'coming-soon',
      popularity: 5,
      features: ['Einstein AI', 'Custom objects', 'Workflow automation', 'Mobile sync'],
      technicalSpecs: {
        method: 'Salesforce API',
        protocol: 'REST/SOAP',
        realTime: true,
        dataSync: 'bidirectional'
      },
      setupTime: '1 week',
      complexity: 'moderate'
    },
    {
      id: 'shopify',
      name: 'Shopify',
      category: 'ecommerce',
      icon: <ShoppingCart className="h-8 w-8" />,
      description: 'Shopify e-commerce integration for automated online sales invoice processing.',
      status: 'coming-soon',
      popularity: 4,
      features: ['Order sync', 'Product catalog', 'Payment tracking', 'Multi-store support'],
      technicalSpecs: {
        method: 'Shopify API',
        protocol: 'GraphQL/REST',
        realTime: true,
        dataSync: 'unidirectional'
      },
      setupTime: '2-3 days',
      complexity: 'simple'
    },
    {
      id: 'square',
      name: 'Square POS',
      category: 'pos',
      icon: <Smartphone className="h-8 w-8" />,
      description: 'Square Point of Sale integration for retail businesses and restaurants.',
      status: 'beta',
      popularity: 3,
      features: ['Transaction sync', 'Inventory tracking', 'Payment processing', 'Offline support'],
      technicalSpecs: {
        method: 'Square API',
        protocol: 'REST/JSON',
        realTime: true,
        dataSync: 'unidirectional'
      },
      setupTime: '1 day',
      complexity: 'simple'
    },
    {
      id: 'firs',
      name: 'FIRS Direct',
      category: 'government',
      icon: <Building className="h-8 w-8" />,
      description: 'Direct FIRS integration as certified Access Point Provider for secure e-invoice submission.',
      status: 'production',
      popularity: 5,
      features: ['Certified APP', 'Real-time validation', 'IRN generation', 'Compliance reporting'],
      technicalSpecs: {
        method: 'FIRS API',
        protocol: 'HTTPS/XML',
        realTime: true,
        dataSync: 'unidirectional'
      },
      setupTime: 'Automatic',
      complexity: 'simple'
    }
  ];

  const categories = [
    { id: 'all', name: 'All Integrations', icon: <Globe className="h-4 w-4" /> },
    { id: 'erp', name: 'ERP Systems', icon: <Database className="h-4 w-4" /> },
    { id: 'crm', name: 'CRM Systems', icon: <Users className="h-4 w-4" /> },
    { id: 'accounting', name: 'Accounting', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'pos', name: 'Point of Sale', icon: <Smartphone className="h-4 w-4" /> },
    { id: 'ecommerce', name: 'E-commerce', icon: <ShoppingCart className="h-4 w-4" /> },
    { id: 'government', name: 'Government', icon: <Building className="h-4 w-4" /> }
  ];

  const complexityLevels = [
    { id: 'all', name: 'All Levels' },
    { id: 'simple', name: 'Simple Setup' },
    { id: 'moderate', name: 'Moderate Setup' },
    { id: 'advanced', name: 'Advanced Setup' }
  ];

  // Filter integrations
  const filteredIntegrations = integrations.filter(integration => {
    const matchesCategory = selectedCategory === 'all' || integration.category === selectedCategory;
    const matchesComplexity = selectedComplexity === 'all' || integration.complexity === selectedComplexity;
    const matchesSearch = integration.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         integration.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesComplexity && matchesSearch;
  });

  const displayIntegrations = maxIntegrations 
    ? filteredIntegrations.slice(0, maxIntegrations)
    : filteredIntegrations;

  // Intersection Observer for animations
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    
    displayIntegrations.forEach((integration, index) => {
      const ref = integrationRefs.current[integration.id];
      if (!ref) return;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              setVisibleIntegrations(prev => [...new Set([...prev, integration.id])]);
            }, index * 150);
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
  }, [displayIntegrations]);

  // Auto-rotation effect
  useEffect(() => {
    if (!autoRotate) return;

    const interval = setInterval(() => {
      setCurrentRotation(prev => (prev + 1) % displayIntegrations.length);
      const currentIntegration = displayIntegrations[currentRotation];
      if (currentIntegration) {
        setHoveredIntegration(currentIntegration.id);
        setTimeout(() => setHoveredIntegration(null), 2000);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [autoRotate, currentRotation, displayIntegrations]);

  const getStatusColor = (status: string) => {
    const colorMap = {
      production: 'green',
      beta: 'blue',
      'coming-soon': 'orange'
    };
    return colorMap[status as keyof typeof colorMap] || 'gray';
  };

  const getStatusLabel = (status: string) => {
    const labelMap = {
      production: 'Production Ready',
      beta: 'Beta',
      'coming-soon': 'Coming Soon'
    };
    return labelMap[status as keyof typeof labelMap] || status;
  };

  const getCategoryColor = (category: string) => {
    const colorMap = {
      erp: 'blue',
      crm: 'purple',
      accounting: 'green',
      pos: 'orange',
      ecommerce: 'pink',
      government: 'red'
    };
    return colorMap[category as keyof typeof colorMap] || 'gray';
  };

  const getComplexityColor = (complexity: string) => {
    const colorMap = {
      simple: 'green',
      moderate: 'yellow',
      advanced: 'red'
    };
    return colorMap[complexity as keyof typeof colorMap] || 'gray';
  };

  return (
    <div className={`py-20 bg-gradient-to-b from-gray-50 to-white ${className}`}>
      <div className="container mx-auto px-4">
        
        {/* Section Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 bg-purple-100 text-purple-800 px-4 py-2 rounded-full mb-6">
            <Wifi className="h-4 w-4" />
            <span className="font-medium text-sm">Integration Ecosystem</span>
          </div>
          
          <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Connect Your Business Systems
          </Typography.Heading>
          
          <Typography.Text size="lg" className="text-gray-600 leading-relaxed mb-8">
            Discover our comprehensive integration ecosystem. Connect with your existing ERP, CRM, POS, and accounting systems 
            to create a seamless e-invoicing workflow.
          </Typography.Text>

          {/* Controls */}
          <div className="flex flex-wrap justify-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoRotate(!autoRotate)}
              className="inline-flex items-center space-x-2"
            >
              {autoRotate ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              <span>{autoRotate ? 'Stop' : 'Start'} Tour</span>
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedCategory('all');
                setSelectedComplexity('all');
                setSearchTerm('');
              }}
              className="inline-flex items-center space-x-2"
            >
              <Filter className="h-4 w-4" />
              <span>Clear Filters</span>
            </Button>
          </div>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mb-12 space-y-6">
            
            {/* Search */}
            <div className="max-w-md mx-auto">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search integrations..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>

            {/* Category Filter */}
            <div className="flex flex-wrap justify-center gap-3">
              {categories.map((category) => (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                    selectedCategory === category.id
                      ? 'bg-primary-600 text-white shadow-lg'
                      : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50'
                  }`}
                >
                  {category.icon}
                  <span>{category.name}</span>
                </button>
              ))}
            </div>

            {/* Complexity Filter */}
            <div className="flex flex-wrap justify-center gap-3">
              {complexityLevels.map((level) => (
                <button
                  key={level.id}
                  onClick={() => setSelectedComplexity(level.id)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-200 ${
                    selectedComplexity === level.id
                      ? 'bg-gray-800 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {level.name}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Results Counter */}
        <div className="text-center mb-8">
          <Typography.Text className="text-gray-600">
            Showing {displayIntegrations.length} of {integrations.length} integrations
          </Typography.Text>
        </div>

        {/* Integration Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {displayIntegrations.map((integration, index) => {
            const isVisible = visibleIntegrations.includes(integration.id);
            const isHovered = hoveredIntegration === integration.id;
            const statusColor = getStatusColor(integration.status);
            const categoryColor = getCategoryColor(integration.category);
            const complexityColor = getComplexityColor(integration.complexity);

            return (
              <div
                key={integration.id}
                ref={el => integrationRefs.current[integration.id] = el}
                className={`transform transition-all duration-700 ease-out ${
                  isVisible ? 'translate-y-0 opacity-100 scale-100' : 'translate-y-8 opacity-0 scale-95'
                }`}
                style={{ transitionDelay: `${index * 150}ms` }}
                onMouseEnter={() => setHoveredIntegration(integration.id)}
                onMouseLeave={() => setHoveredIntegration(null)}
              >
                <Card className={`h-full border-2 hover:shadow-xl bg-white group cursor-pointer relative overflow-hidden transition-all duration-300 ${
                  isHovered ? 'border-primary-300 shadow-xl ring-4 ring-primary-100' : 'border-gray-200 hover:border-gray-300'
                }`}>
                  
                  {/* Status Badge */}
                  <div className="absolute top-4 right-4 z-10">
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                      statusColor === 'green' ? 'bg-green-100 text-green-800' :
                      statusColor === 'blue' ? 'bg-blue-100 text-blue-800' :
                      'bg-orange-100 text-orange-800'
                    }`}>
                      {getStatusLabel(integration.status)}
                    </span>
                  </div>

                  <CardContent className="p-8">
                    
                    {/* Icon and Title */}
                    <div className="flex items-center space-x-4 mb-4">
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-300 ${
                        categoryColor === 'blue' ? 'text-blue-600 bg-blue-50' :
                        categoryColor === 'purple' ? 'text-purple-600 bg-purple-50' :
                        categoryColor === 'green' ? 'text-green-600 bg-green-50' :
                        categoryColor === 'orange' ? 'text-orange-600 bg-orange-50' :
                        categoryColor === 'pink' ? 'text-pink-600 bg-pink-50' :
                        'text-red-600 bg-red-50'
                      } ${isHovered ? 'scale-110 rotate-3' : 'group-hover:scale-105'}`}>
                        {integration.icon}
                      </div>
                      
                      <div>
                        <Typography.Heading level="h3" className="text-lg font-bold text-gray-900 group-hover:text-primary-700 transition-colors">
                          {integration.name}
                        </Typography.Heading>
                        <div className="flex items-center space-x-2 mt-1">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            categoryColor === 'blue' ? 'bg-blue-100 text-blue-700' :
                            categoryColor === 'purple' ? 'bg-purple-100 text-purple-700' :
                            categoryColor === 'green' ? 'bg-green-100 text-green-700' :
                            categoryColor === 'orange' ? 'bg-orange-100 text-orange-700' :
                            categoryColor === 'pink' ? 'bg-pink-100 text-pink-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {integration.category.toUpperCase()}
                          </span>
                          <div className="flex">
                            {[...Array(5)].map((_, i) => (
                              <div
                                key={i}
                                className={`w-2 h-2 rounded-full mr-1 ${
                                  i < integration.popularity ? 'bg-yellow-400' : 'bg-gray-200'
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Description */}
                    <Typography.Text className="text-gray-600 leading-relaxed mb-6">
                      {integration.description}
                    </Typography.Text>

                    {/* Features */}
                    <div className="space-y-2 mb-6">
                      {integration.features.slice(0, 3).map((feature, featureIndex) => (
                        <div key={featureIndex} className="flex items-center space-x-2">
                          <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
                          <Typography.Text className="text-sm text-gray-700">
                            {feature}
                          </Typography.Text>
                        </div>
                      ))}
                      {integration.features.length > 3 && (
                        <Typography.Text className="text-sm text-gray-500 italic">
                          +{integration.features.length - 3} more features
                        </Typography.Text>
                      )}
                    </div>

                    {/* Technical Specs */}
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                      <Typography.Text className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wide">
                        Technical Details
                      </Typography.Text>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">Method:</span>
                          <span className="ml-1 font-medium text-gray-700">{integration.technicalSpecs.method}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Real-time:</span>
                          <span className={`ml-1 font-medium ${integration.technicalSpecs.realTime ? 'text-green-600' : 'text-orange-600'}`}>
                            {integration.technicalSpecs.realTime ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div>
                          <span className="text-gray-500">Setup:</span>
                          <span className="ml-1 font-medium text-gray-700">{integration.setupTime}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Complexity:</span>
                          <span className={`ml-1 px-1 py-0.5 rounded text-xs font-medium ${
                            complexityColor === 'green' ? 'bg-green-100 text-green-700' :
                            complexityColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {integration.complexity}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Action Button */}
                    <Button 
                      className="w-full group-hover:bg-primary-700 transition-colors"
                      disabled={integration.status === 'coming-soon'}
                    >
                      {integration.status === 'coming-soon' ? 'Coming Soon' : 
                       integration.status === 'beta' ? 'Join Beta' : 'Learn More'}
                      {integration.status !== 'coming-soon' && (
                        <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <Card className="border-none shadow-lg bg-gradient-to-r from-purple-600 to-blue-600 text-white hover:shadow-xl transition-shadow">
            <CardContent className="p-12">
              <Typography.Heading level="h3" className="text-2xl md:text-3xl font-bold mb-4">
                Don't See Your System?
              </Typography.Heading>
              
              <Typography.Text size="lg" className="text-white/90 mb-8 max-w-2xl mx-auto">
                We can build custom integrations for any system. Our team of integration experts will work with you 
                to connect TaxPoynt with your unique business requirements.
              </Typography.Text>

              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button 
                  size="lg"
                  className="bg-white text-purple-700 hover:bg-gray-50 font-bold"
                >
                  Request Custom Integration
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                >
                  <Eye className="mr-2 h-4 w-4" />
                  View Integration Docs
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default IntegrationEcosystem;