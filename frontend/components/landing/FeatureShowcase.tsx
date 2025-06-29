import React, { useEffect, useState, useRef } from 'react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { 
  Shield, 
  Zap, 
  FileCheck, 
  BarChart3, 
  Clock, 
  RefreshCw,
  Users,
  Lock,
  Globe,
  CheckCircle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
  Layers,
  Database,
  Cloud,
  Settings,
  Eye,
  Download
} from 'lucide-react';

interface Feature {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  benefits: string[];
  category: 'core' | 'integration' | 'security' | 'analytics';
  isPopular?: boolean;
  comingSoon?: boolean;
}

interface FeatureShowcaseProps {
  className?: string;
  showCategories?: boolean;
  maxFeatures?: number;
}

export const FeatureShowcase: React.FC<FeatureShowcaseProps> = ({
  className = '',
  showCategories = true,
  maxFeatures
}) => {
  const [visibleCards, setVisibleCards] = useState<string[]>([]);
  const [expandedFeatures, setExpandedFeatures] = useState<Set<string>>(new Set());
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const cardRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const features: Feature[] = [
    {
      id: 'firs-submission',
      icon: <Shield className="h-8 w-8" />,
      title: 'FIRS Compliant Submission',
      description: 'Automated e-invoice submission to FIRS with real-time validation and compliance checking.',
      benefits: [
        'Real-time FIRS validation',
        'Automatic error correction',
        'Compliance reporting',
        'Audit trail maintenance'
      ],
      category: 'core',
      isPopular: true
    },
    {
      id: 'irn-generation',
      icon: <FileCheck className="h-8 w-8" />,
      title: 'IRN Generation & Management',
      description: 'Generate Invoice Reference Numbers (IRNs) automatically with cryptographic stamping.',
      benefits: [
        'Automatic IRN generation',
        'QR code creation',
        'Digital signatures',
        'Tamper-proof validation'
      ],
      category: 'core',
      isPopular: true
    },
    {
      id: 'erp-integration',
      icon: <Database className="h-8 w-8" />,
      title: 'ERP System Integration',
      description: 'Seamless integration with SAP, Odoo, Oracle, QuickBooks, and Microsoft Dynamics.',
      benefits: [
        'Real-time data sync',
        'Bi-directional communication',
        'Custom field mapping',
        'API-first architecture'
      ],
      category: 'integration',
      isPopular: true
    },
    {
      id: 'real-time-analytics',
      icon: <BarChart3 className="h-8 w-8" />,
      title: 'Real-time Analytics Dashboard',
      description: 'Monitor invoice processing, compliance rates, and business insights in real-time.',
      benefits: [
        'Live status monitoring',
        'Compliance tracking',
        'Performance metrics',
        'Custom reporting'
      ],
      category: 'analytics'
    },
    {
      id: 'security-encryption',
      icon: <Lock className="h-8 w-8" />,
      title: 'Enterprise Security',
      description: 'Bank-grade encryption with ISO 27001 certified infrastructure and security controls.',
      benefits: [
        '256-bit SSL encryption',
        'Multi-factor authentication',
        'Role-based access control',
        'Security audit logs'
      ],
      category: 'security'
    },
    {
      id: 'batch-processing',
      icon: <Layers className="h-8 w-8" />,
      title: 'Batch Processing Engine',
      description: 'Process thousands of invoices simultaneously with intelligent queuing and prioritization.',
      benefits: [
        'Bulk operations support',
        'Priority queue management',
        'Progress tracking',
        'Error handling & retry'
      ],
      category: 'core'
    },
    {
      id: 'api-access',
      icon: <Cloud className="h-8 w-8" />,
      title: 'Developer API Suite',
      description: 'Comprehensive RESTful APIs with extensive documentation and SDKs.',
      benefits: [
        'RESTful API endpoints',
        'Webhook notifications',
        'SDK libraries',
        'Sandbox environment'
      ],
      category: 'integration'
    },
    {
      id: 'certificate-management',
      icon: <Settings className="h-8 w-8" />,
      title: 'Certificate Lifecycle Management',
      description: 'Automatic digital certificate management with renewal notifications and backup systems.',
      benefits: [
        'Auto-renewal system',
        'Certificate backup',
        'Expiry notifications',
        'Multi-certificate support'
      ],
      category: 'security'
    },
    {
      id: 'audit-trail',
      icon: <Eye className="h-8 w-8" />,
      title: 'Complete Audit Trail',
      description: 'Comprehensive logging and audit trail for all invoice transactions and system activities.',
      benefits: [
        'Complete transaction logs',
        'User activity tracking',
        'Change history',
        'Compliance reporting'
      ],
      category: 'analytics'
    }
  ];

  const categories = [
    { id: 'all', name: 'All Features', count: features.length },
    { id: 'core', name: 'Core Platform', count: features.filter(f => f.category === 'core').length },
    { id: 'integration', name: 'Integrations', count: features.filter(f => f.category === 'integration').length },
    { id: 'security', name: 'Security', count: features.filter(f => f.category === 'security').length },
    { id: 'analytics', name: 'Analytics', count: features.filter(f => f.category === 'analytics').length }
  ];

  const filteredFeatures = activeCategory === 'all' 
    ? features 
    : features.filter(f => f.category === activeCategory);

  const displayFeatures = maxFeatures 
    ? filteredFeatures.slice(0, maxFeatures)
    : filteredFeatures;

  // Intersection Observer for staggered animations
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    
    displayFeatures.forEach((feature) => {
      const ref = cardRefs.current[feature.id];
      if (!ref) return;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVisibleCards(prev => [...new Set([...prev, feature.id])]);
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
  }, [displayFeatures]);

  const toggleFeatureExpansion = (featureId: string) => {
    setExpandedFeatures(prev => {
      const newSet = new Set(prev);
      if (newSet.has(featureId)) {
        newSet.delete(featureId);
      } else {
        newSet.add(featureId);
      }
      return newSet;
    });
  };

  const getCategoryColorClasses = (category: string) => {
    const colorMap = {
      core: 'border-blue-200 hover:border-blue-300 hover:shadow-blue-100/50',
      integration: 'border-green-200 hover:border-green-300 hover:shadow-green-100/50',
      security: 'border-red-200 hover:border-red-300 hover:shadow-red-100/50',
      analytics: 'border-purple-200 hover:border-purple-300 hover:shadow-purple-100/50'
    };
    return colorMap[category as keyof typeof colorMap] || 'border-gray-200 hover:border-gray-300';
  };

  const getIconColorClasses = (category: string) => {
    const colorMap = {
      core: 'text-blue-600 bg-blue-50',
      integration: 'text-green-600 bg-green-50',
      security: 'text-red-600 bg-red-50',
      analytics: 'text-purple-600 bg-purple-50'
    };
    return colorMap[category as keyof typeof colorMap] || 'text-gray-600 bg-gray-50';
  };

  return (
    <div className={`py-20 bg-gradient-to-b from-gray-100 to-gray-50 ${className}`}>
      <div className="container mx-auto px-4">
        
        {/* Section Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 bg-primary-100 text-primary-800 px-4 py-2 rounded-full mb-6">
            <Zap className="h-4 w-4" />
            <span className="font-medium text-sm">Comprehensive E-Invoicing Platform</span>
          </div>
          
          <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Platform Features & Capabilities
          </Typography.Heading>
          
          <Typography.Text size="lg" className="text-gray-600 leading-relaxed">
            Discover the comprehensive suite of features that make TaxPoynt the most advanced e-invoicing platform for Nigerian businesses.
          </Typography.Text>
        </div>

        {/* Category Filter */}
        {showCategories && (
          <div className="flex flex-wrap justify-center gap-3 mb-12">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => setActiveCategory(category.id)}
                className={`inline-flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                  activeCategory === category.id
                    ? 'bg-primary-600 text-white shadow-lg'
                    : 'bg-white text-gray-600 border border-gray-200 hover:border-primary-300 hover:text-primary-600 hover:bg-primary-50'
                }`}
              >
                <span>{category.name}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  activeCategory === category.id
                    ? 'bg-white/20 text-white'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {category.count}
                </span>
              </button>
            ))}
          </div>
        )}

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {displayFeatures.map((feature, index) => (
            <div
              key={feature.id}
              ref={el => cardRefs.current[feature.id] = el}
              className={`transform transition-all duration-700 ease-out ${
                visibleCards.includes(feature.id)
                  ? 'translate-y-0 opacity-100 scale-100'
                  : 'translate-y-8 opacity-0 scale-95'
              }`}
              style={{ transitionDelay: `${index * 150}ms` }}
            >
              <Card className={`h-full border-2 hover:shadow-xl bg-white/90 backdrop-blur-sm group cursor-pointer relative overflow-hidden ${getCategoryColorClasses(feature.category)}`}>
                
                {/* Popular Badge */}
                {feature.isPopular && (
                  <div className="absolute top-4 right-4 z-10">
                    <div className="bg-gradient-to-r from-yellow-400 to-orange-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                      POPULAR
                    </div>
                  </div>
                )}

                {/* Coming Soon Badge */}
                {feature.comingSoon && (
                  <div className="absolute top-4 right-4 z-10">
                    <div className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                      COMING SOON
                    </div>
                  </div>
                )}

                <CardContent className="p-8">
                  
                  {/* Icon */}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 ${getIconColorClasses(feature.category)}`}>
                    {feature.icon}
                  </div>

                  {/* Title */}
                  <Typography.Heading level="h3" className="text-xl font-bold mb-4 text-gray-900 group-hover:text-primary-700 transition-colors">
                    {feature.title}
                  </Typography.Heading>

                  {/* Description */}
                  <Typography.Text className="text-gray-600 leading-relaxed mb-6">
                    {feature.description}
                  </Typography.Text>

                  {/* Progressive Disclosure - Benefits */}
                  <div className="space-y-4">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => toggleFeatureExpansion(feature.id)}
                      className="w-full justify-between text-primary-600 hover:text-primary-700 hover:bg-primary-50"
                    >
                      <span className="font-medium">View Key Benefits</span>
                      {expandedFeatures.has(feature.id) ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>

                    {/* Expandable Benefits List */}
                    <div className={`overflow-hidden transition-all duration-300 ease-in-out ${
                      expandedFeatures.has(feature.id) 
                        ? 'max-h-48 opacity-100' 
                        : 'max-h-0 opacity-0'
                    }`}>
                      <div className="pt-2 space-y-2">
                        {feature.benefits.map((benefit, benefitIndex) => (
                          <div 
                            key={benefitIndex}
                            className="flex items-start space-x-3 p-2 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                          >
                            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                            <Typography.Text className="text-sm text-gray-700">
                              {benefit}
                            </Typography.Text>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Category Badge */}
                  <div className="mt-6 pt-4 border-t border-gray-100">
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                      feature.category === 'core' ? 'bg-blue-100 text-blue-700' :
                      feature.category === 'integration' ? 'bg-green-100 text-green-700' :
                      feature.category === 'security' ? 'bg-red-100 text-red-700' :
                      'bg-purple-100 text-purple-700'
                    }`}>
                      {feature.category.charAt(0).toUpperCase() + feature.category.slice(1)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-3xl p-8 md:p-12 text-white relative overflow-hidden">
            
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full -translate-x-20 -translate-y-20"></div>
              <div className="absolute bottom-0 right-0 w-60 h-60 bg-cyan-300 rounded-full translate-x-30 translate-y-30"></div>
            </div>

            <div className="relative z-10">
              <Typography.Heading level="h3" className="text-2xl md:text-3xl font-bold mb-4">
                Ready to Experience These Features?
              </Typography.Heading>
              
              <Typography.Text size="lg" className="text-white/90 mb-8 max-w-2xl mx-auto">
                Start your free trial today and see how TaxPoynt's comprehensive feature set can transform your e-invoicing process.
              </Typography.Text>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <Button 
                  size="lg"
                  className="bg-white text-primary-700 hover:bg-gray-50 font-bold shadow-xl"
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                >
                  <Download className="mr-2 h-4 w-4" />
                  Download Feature Guide
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeatureShowcase;