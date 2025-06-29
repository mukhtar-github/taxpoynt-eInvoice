import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { Button } from '../ui/Button';
import { Typography } from '../ui/Typography';
import { 
  ArrowRight, 
  CheckCircle, 
  Star,
  Users,
  TrendingUp,
  Shield,
  Phone,
  Mail,
  Calendar
} from 'lucide-react';

interface CTAProps {
  variant?: 'primary' | 'secondary' | 'minimal';
  title?: string;
  description?: string;
  showStats?: boolean;
  showTestimonial?: boolean;
  trackingId?: string;
}

export const CallToAction: React.FC<CTAProps> = ({
  variant = 'primary',
  title,
  description,
  showStats = true,
  showTestimonial = true,
  trackingId = 'hero-cta'
}) => {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);
  const [conversions, setConversions] = useState({ signups: 1247, businesses: 450 });

  // Intersection Observer for animation
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.3 }
    );

    const ctaElement = document.getElementById(`cta-${trackingId}`);
    if (ctaElement) {
      observer.observe(ctaElement);
    }

    return () => observer.disconnect();
  }, [trackingId]);

  // Simulated real-time conversion tracking
  useEffect(() => {
    const interval = setInterval(() => {
      setConversions(prev => ({
        signups: prev.signups + Math.floor(Math.random() * 3),
        businesses: prev.businesses + (Math.random() > 0.8 ? 1 : 0)
      }));
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const handleCTAClick = (action: string) => {
    // Track conversion for analytics
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'cta_click', {
        event_category: 'engagement',
        event_label: `${trackingId}-${action}`,
        value: 1
      });
    }

    // Navigate based on action
    switch (action) {
      case 'signup':
        router.push('/auth/signup');
        break;
      case 'demo':
        router.push('/demo');
        break;
      case 'contact':
        router.push('/contact');
        break;
      default:
        router.push('/auth/signup');
    }
  };

  if (variant === 'minimal') {
    return (
      <div className="py-12 text-center">
        <div className="inline-flex flex-col sm:flex-row gap-4">
          <Button 
            size="lg"
            onClick={() => handleCTAClick('signup')}
            className="shadow-lg hover:shadow-xl transition-shadow"
          >
            Get Started Free
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
          <Button 
            size="lg"
            variant="outline"
            onClick={() => handleCTAClick('demo')}
          >
            Schedule Demo
          </Button>
        </div>
      </div>
    );
  }

  if (variant === 'secondary') {
    return (
      <div className="py-16 bg-gray-200">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center">
            <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
              {title || "Ready to Get Started?"}
            </Typography.Heading>
            <Typography.Text size="lg" className="text-gray-600 mb-8">
              {description || "Join hundreds of Nigerian businesses streamlining their e-invoicing process."}
            </Typography.Text>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg"
                onClick={() => handleCTAClick('signup')}
              >
                Start Free Trial
              </Button>
              <Button 
                size="lg"
                variant="outline"
                onClick={() => handleCTAClick('contact')}
              >
                <Phone className="mr-2 h-4 w-4" />
                Talk to Sales
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Primary variant with full features
  return (
    <div 
      id={`cta-${trackingId}`}
      className="py-20 bg-gradient-to-br from-slate-800 via-slate-900 to-gray-900 text-white overflow-hidden relative"
    >
      {/* Background Effects */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-1/3 h-1/3 bg-cyan-400/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-1/2 h-1/2 bg-blue-400/20 rounded-full blur-3xl"></div>
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            
            {/* Left Column - Main CTA */}
            <div className={`space-y-8 transform transition-all duration-1000 ${
              isVisible ? 'translate-x-0 opacity-100' : '-translate-x-10 opacity-0'
            }`}>
              
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 bg-green-500/20 border border-green-400/30 rounded-full px-4 py-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-100 font-medium text-sm">Join {conversions.businesses}+ Active Businesses</span>
              </div>

              <div className="space-y-6">
                <Typography.Heading level="h2" className="text-4xl md:text-5xl font-bold leading-tight">
                  {title || (
                    <>
                      Start Your E-Invoicing
                      <span className="block text-cyan-300">Journey Today</span>
                    </>
                  )}
                </Typography.Heading>

                <Typography.Text size="lg" className="text-white/90 leading-relaxed">
                  {description || "No setup fees, no long-term contracts. Get compliant with FIRS regulations in minutes, not months. Your first 100 invoices are completely free."}
                </Typography.Text>
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  size="lg"
                  className="bg-white text-primary-700 hover:bg-gray-50 font-bold shadow-xl transform hover:scale-105 transition-all duration-200"
                  onClick={() => handleCTAClick('signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm"
                  onClick={() => handleCTAClick('demo')}
                >
                  <Calendar className="mr-2 h-4 w-4" />
                  Schedule Demo
                </Button>

                <Button 
                  size="lg"
                  variant="ghost" 
                  className="text-white hover:bg-white/10"
                  onClick={() => handleCTAClick('contact')}
                >
                  <Mail className="mr-2 h-4 w-4" />
                  Contact Sales
                </Button>
              </div>

              {/* Trust Indicators */}
              <div className="flex flex-wrap items-center gap-6 pt-4">
                <div className="flex items-center space-x-2">
                  <Shield className="h-5 w-5 text-green-400" />
                  <span className="text-white/80 text-sm">FIRS Certified</span>
                </div>
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <span className="text-white/80 text-sm">Free Setup</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-green-400" />
                  <span className="text-white/80 text-sm">24/7 Support</span>
                </div>
              </div>
            </div>

            {/* Right Column - Stats & Social Proof */}
            <div className={`space-y-8 transform transition-all duration-1000 delay-300 ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
            }`}>
              
              {/* Live Stats */}
              {showStats && (
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white mb-1">
                        {conversions.signups.toLocaleString()}+
                      </div>
                      <div className="text-white/70 text-sm">Invoices Processed</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white mb-1">
                        {conversions.businesses}+
                      </div>
                      <div className="text-white/70 text-sm">Active Businesses</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white mb-1">99.9%</div>
                      <div className="text-white/70 text-sm">Uptime SLA</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white mb-1">&lt;2s</div>
                      <div className="text-white/70 text-sm">Avg Response</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Testimonial */}
              {showTestimonial && (
                <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 border border-white/20">
                  <div className="flex items-center space-x-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    ))}
                  </div>
                  <Typography.Text className="text-white/90 italic mb-4">
                    "TaxPoynt transformed our invoicing process completely. What used to take hours now takes minutes, and we're always FIRS compliant."
                  </Typography.Text>
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full flex items-center justify-center">
                      <span className="text-white font-semibold text-sm">AO</span>
                    </div>
                    <div>
                      <div className="text-white font-medium text-sm">Adebayo Ogundimu</div>
                      <div className="text-white/70 text-xs">CFO, TechCorp Nigeria</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Feature Highlights */}
              <div className="space-y-3">
                {[
                  "Setup completed in under 5 minutes",
                  "Free for your first 100 invoices",
                  "Direct integration with your existing ERP",
                  "24/7 customer support included"
                ].map((feature, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-400 flex-shrink-0" />
                    <span className="text-white/90 text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              {/* Conversion Indicator */}
              <div className="bg-green-500/20 border border-green-400/30 rounded-lg p-4">
                <div className="flex items-center space-x-3">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <div>
                    <div className="text-green-100 text-sm font-medium">
                      {Math.floor(Math.random() * 15) + 5} businesses signed up in the last 24 hours
                    </div>
                    <div className="text-green-200/70 text-xs">Don't miss out on streamlined e-invoicing</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CallToAction;