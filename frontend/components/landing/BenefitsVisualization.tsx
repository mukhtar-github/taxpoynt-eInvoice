import React, { useEffect, useState, useRef } from 'react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { 
  Clock, 
  DollarSign, 
  Shield, 
  TrendingUp, 
  Users, 
  CheckCircle,
  Target,
  Zap,
  Award,
  ArrowRight,
  BarChart3,
  Globe
} from 'lucide-react';

interface Benefit {
  id: string;
  icon: React.ReactNode;
  title: string;
  description: string;
  metric: {
    value: string;
    label: string;
    trend?: 'up' | 'down';
  };
  color: string;
  animationDelay: number;
}

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  suffix?: string;
  prefix?: string;
}

const AnimatedCounter: React.FC<AnimatedCounterProps> = ({ 
  value, 
  duration = 2000, 
  suffix = '', 
  prefix = '' 
}) => {
  const [currentValue, setCurrentValue] = useState(0);
  const [isVisible, setIsVisible] = useState(false);
  const counterRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !isVisible) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    if (counterRef.current) {
      observer.observe(counterRef.current);
    }

    return () => observer.disconnect();
  }, [isVisible]);

  useEffect(() => {
    if (!isVisible) return;

    const startTime = Date.now();
    const endTime = startTime + duration;

    const updateCounter = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      
      // Easing function for smooth animation
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      const currentCount = Math.floor(easeOutQuart * value);
      
      setCurrentValue(currentCount);
      
      if (progress < 1) {
        requestAnimationFrame(updateCounter);
      }
    };

    requestAnimationFrame(updateCounter);
  }, [isVisible, value, duration]);

  return (
    <span ref={counterRef} className="font-bold">
      {prefix}{currentValue.toLocaleString()}{suffix}
    </span>
  );
};

interface BenefitsVisualizationProps {
  className?: string;
  showMetrics?: boolean;
}

export const BenefitsVisualization: React.FC<BenefitsVisualizationProps> = ({
  className = '',
  showMetrics = true
}) => {
  const [visibleBenefits, setVisibleBenefits] = useState<string[]>([]);
  const [hoveredBenefit, setHoveredBenefit] = useState<string | null>(null);
  const benefitRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const benefits: Benefit[] = [
    {
      id: 'time-savings',
      icon: <Clock className="h-8 w-8" />,
      title: 'Time Savings',
      description: 'Reduce invoice processing time from hours to minutes with automated workflows and real-time synchronization.',
      metric: {
        value: '90%',
        label: 'Faster Processing',
        trend: 'up'
      },
      color: 'blue',
      animationDelay: 0
    },
    {
      id: 'cost-reduction',
      icon: <DollarSign className="h-8 w-8" />,
      title: 'Cost Reduction',
      description: 'Eliminate manual processing costs, reduce errors, and optimize your accounting operations for maximum efficiency.',
      metric: {
        value: '₦2.5M',
        label: 'Average Annual Savings',
        trend: 'up'
      },
      color: 'green',
      animationDelay: 200
    },
    {
      id: 'compliance',
      icon: <Shield className="h-8 w-8" />,
      title: 'FIRS Compliance',
      description: 'Stay 100% compliant with Nigerian tax regulations through automated validation and certified transmission.',
      metric: {
        value: '100%',
        label: 'Compliance Rate',
        trend: 'up'
      },
      color: 'cyan',
      animationDelay: 400
    },
    {
      id: 'accuracy',
      icon: <Target className="h-8 w-8" />,
      title: 'Improved Accuracy',
      description: 'Eliminate human errors with automated data validation, real-time checking, and intelligent error correction.',
      metric: {
        value: '99.8%',
        label: 'Accuracy Rate',
        trend: 'up'
      },
      color: 'purple',
      animationDelay: 600
    },
    {
      id: 'scalability',
      icon: <TrendingUp className="h-8 w-8" />,
      title: 'Business Growth',
      description: 'Scale your operations seamlessly with unlimited invoice processing and enterprise-grade infrastructure.',
      metric: {
        value: '10x',
        label: 'Processing Capacity',
        trend: 'up'
      },
      color: 'orange',
      animationDelay: 800
    },
    {
      id: 'integration',
      icon: <Globe className="h-8 w-8" />,
      title: 'Seamless Integration',
      description: 'Connect with your existing ERP, CRM, and accounting systems without disrupting current workflows.',
      metric: {
        value: '50+',
        label: 'System Integrations',
        trend: 'up'
      },
      color: 'indigo',
      animationDelay: 1000
    }
  ];

  // Intersection Observer for staggered animations
  useEffect(() => {
    const observers: IntersectionObserver[] = [];
    
    benefits.forEach((benefit) => {
      const ref = benefitRefs.current[benefit.id];
      if (!ref) return;
      
      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setTimeout(() => {
              setVisibleBenefits(prev => [...new Set([...prev, benefit.id])]);
            }, benefit.animationDelay);
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
  }, [benefits]);

  const getColorClasses = (color: string, variant: 'icon' | 'card' | 'metric' = 'icon') => {
    const colorMap = {
      blue: {
        icon: 'text-blue-600 bg-blue-50',
        card: 'border-blue-200 hover:border-blue-300 hover:shadow-blue-100/50',
        metric: 'text-blue-600 bg-blue-50'
      },
      green: {
        icon: 'text-green-600 bg-green-50',
        card: 'border-green-200 hover:border-green-300 hover:shadow-green-100/50',
        metric: 'text-green-600 bg-green-50'
      },
      cyan: {
        icon: 'text-cyan-600 bg-cyan-50',
        card: 'border-cyan-200 hover:border-cyan-300 hover:shadow-cyan-100/50',
        metric: 'text-cyan-600 bg-cyan-50'
      },
      purple: {
        icon: 'text-purple-600 bg-purple-50',
        card: 'border-purple-200 hover:border-purple-300 hover:shadow-purple-100/50',
        metric: 'text-purple-600 bg-purple-50'
      },
      orange: {
        icon: 'text-orange-600 bg-orange-50',
        card: 'border-orange-200 hover:border-orange-300 hover:shadow-orange-100/50',
        metric: 'text-orange-600 bg-orange-50'
      },
      indigo: {
        icon: 'text-indigo-600 bg-indigo-50',
        card: 'border-indigo-200 hover:border-indigo-300 hover:shadow-indigo-100/50',
        metric: 'text-indigo-600 bg-indigo-50'
      }
    };
    
    return colorMap[color as keyof typeof colorMap]?.[variant] || colorMap.blue[variant];
  };

  return (
    <div className={`py-20 bg-gray-50 ${className}`}>
      <div className="container mx-auto px-4">
        
        {/* Section Header */}
        <div className="text-center max-w-4xl mx-auto mb-16">
          <div className="inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-2 rounded-full mb-6">
            <Award className="h-4 w-4" />
            <span className="font-medium text-sm">Proven Business Impact</span>
          </div>
          
          <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold mb-6 bg-gradient-to-r from-gray-900 to-gray-700 bg-clip-text text-transparent">
            Measurable Business Benefits
          </Typography.Heading>
          
          <Typography.Text size="lg" className="text-gray-600 leading-relaxed">
            See the tangible impact TaxPoynt delivers for Nigerian businesses through automation, compliance, and intelligent e-invoicing workflows.
          </Typography.Text>
        </div>

        {/* Overall Stats Bar */}
        {showMetrics && (
          <div className="bg-gradient-to-r from-slate-800 to-slate-900 rounded-2xl p-8 mb-16 text-white relative overflow-hidden">
            
            {/* Background Pattern */}
            <div className="absolute inset-0 opacity-10">
              <div className="absolute top-0 right-0 w-40 h-40 bg-white rounded-full translate-x-20 -translate-y-20"></div>
              <div className="absolute bottom-0 left-0 w-60 h-60 bg-cyan-300 rounded-full -translate-x-30 translate-y-30"></div>
            </div>

            <div className="relative z-10">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
                <div>
                  <div className="text-3xl md:text-4xl font-bold mb-2">
                    <AnimatedCounter value={450} suffix="+" />
                  </div>
                  <div className="text-white/80">Active Businesses</div>
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-bold mb-2">
                    <AnimatedCounter value={1200000} suffix="+" />
                  </div>
                  <div className="text-white/80">Invoices Processed</div>
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-bold mb-2">
                    <AnimatedCounter value={99} suffix=".9%" />
                  </div>
                  <div className="text-white/80">Uptime SLA</div>
                </div>
                <div>
                  <div className="text-3xl md:text-4xl font-bold mb-2">
                    <AnimatedCounter value={24} suffix="/7" />
                  </div>
                  <div className="text-white/80">Support Available</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Benefits Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {benefits.map((benefit) => (
            <div
              key={benefit.id}
              ref={el => benefitRefs.current[benefit.id] = el}
              className={`transform transition-all duration-700 ease-out ${
                visibleBenefits.includes(benefit.id)
                  ? 'translate-y-0 opacity-100 scale-100'
                  : 'translate-y-8 opacity-0 scale-95'
              }`}
              onMouseEnter={() => setHoveredBenefit(benefit.id)}
              onMouseLeave={() => setHoveredBenefit(null)}
            >
              <Card className={`h-full border-2 hover:shadow-xl bg-gray-100 group cursor-pointer relative overflow-hidden ${getColorClasses(benefit.color, 'card')}`}>
                
                {/* Hover Glow Effect */}
                <div className={`absolute inset-0 opacity-0 group-hover:opacity-5 transition-opacity duration-300 bg-gradient-to-br ${
                  benefit.color === 'blue' ? 'from-blue-400 to-blue-600' :
                  benefit.color === 'green' ? 'from-green-400 to-green-600' :
                  benefit.color === 'cyan' ? 'from-cyan-400 to-cyan-600' :
                  benefit.color === 'purple' ? 'from-purple-400 to-purple-600' :
                  benefit.color === 'orange' ? 'from-orange-400 to-orange-600' :
                  'from-indigo-400 to-indigo-600'
                }`}></div>

                <CardContent className="p-8 relative z-10">
                  
                  {/* Icon with Animation */}
                  <div className={`w-16 h-16 rounded-2xl flex items-center justify-center mb-6 transition-all duration-300 ${getColorClasses(benefit.color, 'icon')} ${
                    hoveredBenefit === benefit.id ? 'scale-110 rotate-3' : 'group-hover:scale-105'
                  }`}>
                    {benefit.icon}
                  </div>

                  {/* Title */}
                  <Typography.Heading level="h3" className="text-xl font-bold mb-4 text-gray-900 group-hover:text-primary-700 transition-colors">
                    {benefit.title}
                  </Typography.Heading>

                  {/* Description */}
                  <Typography.Text className="text-gray-600 leading-relaxed mb-6">
                    {benefit.description}
                  </Typography.Text>

                  {/* Metric Display */}
                  <div className={`p-4 rounded-xl ${getColorClasses(benefit.color, 'metric')} transition-all duration-300 ${
                    hoveredBenefit === benefit.id ? 'scale-105' : ''
                  }`}>
                    <div className="flex items-center justify-between">
                      <div>
                        <div className={`text-2xl font-bold ${
                          benefit.color === 'blue' ? 'text-blue-700' :
                          benefit.color === 'green' ? 'text-green-700' :
                          benefit.color === 'cyan' ? 'text-cyan-700' :
                          benefit.color === 'purple' ? 'text-purple-700' :
                          benefit.color === 'orange' ? 'text-orange-700' :
                          'text-indigo-700'
                        }`}>
                          {benefit.metric.value}
                        </div>
                        <div className="text-sm text-gray-600 font-medium">
                          {benefit.metric.label}
                        </div>
                      </div>
                      
                      {benefit.metric.trend && (
                        <div className={`p-2 rounded-full ${
                          benefit.metric.trend === 'up' ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          <TrendingUp className={`h-4 w-4 ${
                            benefit.metric.trend === 'up' ? 'text-green-600' : 'text-red-600 rotate-180'
                          }`} />
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Micro-interaction: Pulse Effect */}
                  <div className={`absolute top-4 right-4 w-3 h-3 rounded-full transition-all duration-300 ${
                    hoveredBenefit === benefit.id 
                      ? `animate-pulse ${
                          benefit.color === 'blue' ? 'bg-blue-400' :
                          benefit.color === 'green' ? 'bg-green-400' :
                          benefit.color === 'cyan' ? 'bg-cyan-400' :
                          benefit.color === 'purple' ? 'bg-purple-400' :
                          benefit.color === 'orange' ? 'bg-orange-400' :
                          'bg-indigo-400'
                        }`
                      : 'bg-gray-200'
                  }`}></div>
                </CardContent>
              </Card>
            </div>
          ))}
        </div>

        {/* Bottom CTA Section */}
        <div className="mt-16 text-center">
          <Card className="border-none shadow-lg bg-gradient-to-r from-gray-50 to-gray-100 hover:shadow-xl transition-shadow">
            <CardContent className="p-12">
              <div className="max-w-3xl mx-auto">
                <div className="flex items-center justify-center mb-6">
                  <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mr-4">
                    <BarChart3 className="h-6 w-6 text-primary-600" />
                  </div>
                  <Typography.Heading level="h3" className="text-2xl font-bold">
                    Ready to Experience These Benefits?
                  </Typography.Heading>
                </div>
                
                <Typography.Text size="lg" className="text-gray-600 mb-8">
                  Join hundreds of Nigerian businesses already transforming their e-invoicing operations with measurable results.
                </Typography.Text>

                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="text-sm font-medium">Free 30-day trial</span>
                  </div>
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="text-sm font-medium">No setup fees</span>
                  </div>
                  <div className="flex items-center space-x-2 text-green-600">
                    <CheckCircle className="h-5 w-5" />
                    <span className="text-sm font-medium">Cancel anytime</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default BenefitsVisualization;