import React, { useEffect, useState, useRef } from 'react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { 
  Shield, 
  Zap, 
  RefreshCw, 
  BarChart3, 
  Lock, 
  CheckCircle,
  Clock,
  Globe
} from 'lucide-react';

interface ValueProposition {
  icon: React.ReactNode;
  title: string;
  description: string;
  stats?: string;
  color: string;
}

export const ValuePropositions: React.FC = () => {
  const [visibleCards, setVisibleCards] = useState<number[]>([]);
  const cardRefs = useRef<(HTMLDivElement | null)[]>([]);

  const valueProps: ValueProposition[] = [
    {
      icon: <Shield className="h-8 w-8" />,
      title: "FIRS Certified Security",
      description: "End-to-end encryption with digital certificates ensuring your invoices meet all Nigerian tax authority requirements.",
      stats: "256-bit SSL",
      color: "cyan"
    },
    {
      icon: <Zap className="h-8 w-8" />,
      title: "Lightning Fast Processing",
      description: "Process thousands of invoices in seconds with our optimized transmission engine and real-time validation.",
      stats: "< 2 sec response",
      color: "yellow"
    },
    {
      icon: <RefreshCw className="h-8 w-8" />,
      title: "Seamless Integration",
      description: "Connect with SAP, Odoo, Oracle, QuickBooks and more. Our APIs work with your existing business systems.",
      stats: "50+ Integrations",
      color: "green"
    },
    {
      icon: <BarChart3 className="h-8 w-8" />,
      title: "Real-time Analytics",
      description: "Monitor invoice status, track compliance rates, and get insights that help optimize your business processes.",
      stats: "Live Dashboard",
      color: "blue"
    },
    {
      icon: <Lock className="h-8 w-8" />,
      title: "Bank-Grade Security",
      description: "ISO 27001 certified infrastructure with multi-layer security controls protecting your sensitive business data.",
      stats: "ISO 27001",
      color: "purple"
    },
    {
      icon: <Globe className="h-8 w-8" />,
      title: "99.9% Uptime SLA",
      description: "Enterprise-grade reliability ensures your e-invoicing operations never stop, backed by our uptime guarantee.",
      stats: "99.9% Uptime",
      color: "indigo"
    }
  ];

  // Intersection Observer for staggered card animations
  useEffect(() => {
    const observers = cardRefs.current.map((ref, index) => {
      if (!ref) return null;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVisibleCards(prev => [...new Set([...prev, index])]);
          }
        },
        { threshold: 0.2 }
      );
      
      observer.observe(ref);
      return observer;
    });

    return () => {
      observers.forEach(observer => observer?.disconnect());
    };
  }, []);

  const getColorClasses = (color: string, isVisible: boolean) => {
    const baseClasses = "transition-all duration-700 ease-out transform";
    const visibilityClasses = isVisible 
      ? "translate-y-0 opacity-100 scale-100" 
      : "translate-y-8 opacity-0 scale-95";
    
    const colorMap = {
      cyan: "hover:border-cyan-200 hover:shadow-cyan-100/50",
      yellow: "hover:border-yellow-200 hover:shadow-yellow-100/50",
      green: "hover:border-green-200 hover:shadow-green-100/50",
      blue: "hover:border-blue-200 hover:shadow-blue-100/50",
      purple: "hover:border-purple-200 hover:shadow-purple-100/50",
      indigo: "hover:border-indigo-200 hover:shadow-indigo-100/50"
    };

    return `${baseClasses} ${visibilityClasses} ${colorMap[color as keyof typeof colorMap]}`;
  };

  const getIconColorClasses = (color: string) => {
    const colorMap = {
      cyan: "text-cyan-600 bg-cyan-50",
      yellow: "text-yellow-600 bg-yellow-50",
      green: "text-green-600 bg-green-50",
      blue: "text-blue-600 bg-blue-50",
      purple: "text-purple-600 bg-purple-50",
      indigo: "text-indigo-600 bg-indigo-50"
    };
    
    return colorMap[color as keyof typeof colorMap];
  };

  return (
    <div className="py-20 bg-gradient-to-b from-gray-100 to-gray-200">
      <div className="container mx-auto px-4">
        
        {/* Section Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 bg-primary-100 text-primary-800 px-4 py-2 rounded-full mb-6">
            <CheckCircle className="h-4 w-4" />
            <span className="font-medium text-sm">Trusted by 1000+ Nigerian Businesses</span>
          </div>
          
          <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Why Choose TaxPoynt?
          </Typography.Heading>
          
          <Typography.Text size="lg" className="text-gray-600 leading-relaxed">
            Built specifically for Nigerian businesses, our platform combines cutting-edge technology 
            with deep local expertise to deliver the most comprehensive e-invoicing solution.
          </Typography.Text>
        </div>

        {/* Value Proposition Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {valueProps.map((prop, index) => (
            <div
              key={index}
              ref={el => cardRefs.current[index] = el}
              className={getColorClasses(prop.color, visibleCards.includes(index))}
              style={{ transitionDelay: `${index * 150}ms` }}
            >
              <Card className="h-full border-2 border-gray-100 hover:shadow-xl bg-gray-100 backdrop-blur-sm group">
                <CardContent className="p-8">
                  
                  {/* Icon */}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300 ${getIconColorClasses(prop.color)}`}>
                    {prop.icon}
                  </div>

                  {/* Title */}
                  <Typography.Heading level="h3" className="text-xl font-bold mb-4 text-gray-900">
                    {prop.title}
                  </Typography.Heading>

                  {/* Description */}
                  <Typography.Text className="text-gray-600 leading-relaxed mb-6">
                    {prop.description}
                  </Typography.Text>

                  {/* Stats Badge */}
                  {prop.stats && (
                    <div className="inline-flex items-center space-x-2 bg-gray-100 text-gray-700 px-3 py-1.5 rounded-full text-sm font-medium">
                      <div className={`w-2 h-2 rounded-full bg-${prop.color}-500`}></div>
                      <span>{prop.stats}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          ))}
        </div>

        {/* Bottom CTA Section */}
        <div className="mt-20 text-center">
          <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-3xl p-12 md:p-16 text-white relative overflow-hidden">
            
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 left-0 w-40 h-40 bg-white rounded-full -translate-x-20 -translate-y-20"></div>
              <div className="absolute bottom-0 right-0 w-60 h-60 bg-cyan-300 rounded-full translate-x-30 translate-y-30"></div>
            </div>

            <div className="relative z-10">
              <Typography.Heading level="h3" className="text-3xl md:text-4xl font-bold mb-4">
                Ready to Transform Your E-Invoicing?
              </Typography.Heading>
              
              <Typography.Text size="lg" className="text-white/90 mb-8 max-w-2xl mx-auto">
                Join thousands of Nigerian businesses already saving time and ensuring compliance with TaxPoynt.
              </Typography.Text>

              <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                <div className="flex items-center space-x-2 text-white/80">
                  <Clock className="h-5 w-5" />
                  <span className="text-sm">Setup in 5 minutes</span>
                </div>
                <div className="hidden sm:block w-px h-6 bg-white/30"></div>
                <div className="flex items-center space-x-2 text-white/80">
                  <CheckCircle className="h-5 w-5" />
                  <span className="text-sm">No setup fees</span>
                </div>
                <div className="hidden sm:block w-px h-6 bg-white/30"></div>
                <div className="flex items-center space-x-2 text-white/80">
                  <Shield className="h-5 w-5" />
                  <span className="text-sm">FIRS certified</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ValuePropositions;