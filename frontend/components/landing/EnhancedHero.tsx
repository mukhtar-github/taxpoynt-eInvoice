import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Button } from '../ui/Button';
import { Typography } from '../ui/Typography';
import Image from 'next/image';
import { 
  ArrowRight, 
  Play,
  CheckCircle,
  Shield,
  Zap,
  Globe
} from 'lucide-react';

interface EnhancedHeroProps {
  className?: string;
}

export const EnhancedHero: React.FC<EnhancedHeroProps> = ({ className = '' }) => {
  const router = useRouter();
  const [isVisible, setIsVisible] = useState(false);
  const [currentSlide, setCurrentSlide] = useState(0);

  // Intersection Observer for scroll-triggered animations
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
        }
      },
      { threshold: 0.1 }
    );

    const heroElement = document.getElementById('enhanced-hero');
    if (heroElement) {
      observer.observe(heroElement);
    }

    return () => observer.disconnect();
  }, []);

  // Auto-rotating value propositions
  const valuePropositions = [
    "Automated E-Invoice Processing",
    "FIRS Compliant Transmission", 
    "Real-time Integration Sync",
    "Secure Certificate Management"
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % valuePropositions.length);
    }, 4000); // Increased from 3000ms to 4000ms for better readability
    return () => clearInterval(interval);
  }, [valuePropositions.length]);

  const trustIndicators = [
    { icon: <Shield className="h-5 w-5" />, text: "FIRS Certified APP" },
    { icon: <CheckCircle className="h-5 w-5" />, text: "ISO 27001 Security" },
    { icon: <Zap className="h-5 w-5" />, text: "99.9% Uptime SLA" },
    { icon: <Globe className="h-5 w-5" />, text: "Nigerian Tax Compliant" }
  ];

  return (
    <div 
      id="enhanced-hero"
      className={`relative overflow-hidden ${className}`}
    >
      {/* Enhanced Gradient Background with Animated Patterns - Darker for better contrast */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-900 to-gray-900">
        {/* Animated Background Patterns - Reduced opacity for better text readability */}
        <div className="absolute inset-0 opacity-15">
          <div className="absolute top-0 -left-4 w-72 h-72 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl animate-pulse"></div>
          <div className="absolute top-0 -right-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl animate-pulse animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl animate-pulse animation-delay-4000"></div>
        </div>
        
        {/* Geometric Pattern Overlay */}
        <div className="absolute inset-0 opacity-10">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="white" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#grid)" />
          </svg>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 py-16 md:py-24 lg:py-32">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            
            {/* Left Column - Content */}
            <div className={`space-y-8 transform transition-all duration-1000 ${
              isVisible ? 'translate-y-0 opacity-100' : 'translate-y-10 opacity-0'
            }`}>
              
              {/* Badge */}
              <div className="inline-flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-white font-medium text-sm">FIRS Certified Access Point Provider</span>
              </div>

              {/* Main Headline */}
              <div className="space-y-4">
                <Typography.Heading 
                  level="h1" 
                  className="text-4xl md:text-5xl xl:text-6xl font-bold text-white leading-tight"
                >
                  Nigeria's Premier
                  <span className="block bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">
                    E-Invoicing Platform
                  </span>
                </Typography.Heading>

                {/* Animated Value Proposition */}
                <div className="h-10 md:h-12 relative overflow-hidden">
                  <div 
                    className="transition-all duration-700 ease-in-out"
                    style={{ transform: `translateY(-${currentSlide * 100}%)` }}
                  >
                    {valuePropositions.map((proposition, index) => (
                      <div 
                        key={index}
                        className="h-10 md:h-12 flex items-center"
                      >
                        <Typography.Text 
                          size="lg" 
                          className="text-cyan-200 font-semibold whitespace-nowrap"
                        >
                          {proposition}
                        </Typography.Text>
                      </div>
                    ))}
                  </div>
                </div>

                <Typography.Text 
                  size="lg" 
                  className="text-gray-200 leading-relaxed max-w-xl"
                >
                  Streamline your entire e-invoicing workflow from ERP integration to secure FIRS submission. 
                  Our dual-certified platform ensures compliance while saving time and reducing errors.
                </Typography.Text>
              </div>

              {/* Call-to-Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Button 
                  size="lg"
                  className="bg-gray-200 text-gray-900 hover:bg-gray-300 font-bold shadow-xl border-2 border-gray-400 transform hover:scale-105 transition-all duration-200"
                  onClick={() => router.push('/auth/signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="bg-gray-200 text-gray-900 border-gray-400 hover:bg-gray-300 shadow-lg font-semibold group"
                  onClick={() => {
                    // Scroll to demo section
                    const demoSection = document.getElementById('demo-section');
                    if (demoSection) {
                      demoSection.scrollIntoView({ behavior: 'smooth' });
                    }
                  }}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Watch Demo
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </div>

              {/* Trust Indicators */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-8">
                {trustIndicators.map((indicator, index) => (
                  <div 
                    key={index}
                    className={`flex items-center space-x-2 text-gray-300 transform transition-all duration-500 ${
                      isVisible ? 'translate-y-0 opacity-100' : 'translate-y-5 opacity-0'
                    }`}
                    style={{ transitionDelay: `${index * 100}ms` }}
                  >
                    {indicator.icon}
                    <span className="text-sm font-medium">{indicator.text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column - Visual */}
            <div className={`hidden lg:flex justify-center transform transition-all duration-1000 delay-300 ${
              isVisible ? 'translate-x-0 opacity-100' : 'translate-x-10 opacity-0'
            }`}>
              <div className="relative">
                
                {/* Main Dashboard Preview */}
                <div className="relative w-full max-w-lg h-80 bg-white/10 backdrop-blur-md rounded-2xl overflow-hidden border border-white/20 shadow-2xl">
                  
                  {/* Browser Frame */}
                  <div className="h-8 bg-gray-800/50 flex items-center px-4 backdrop-blur-sm">
                    <div className="flex space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-400/80"></div>
                      <div className="w-3 h-3 rounded-full bg-yellow-400/80"></div>
                      <div className="w-3 h-3 rounded-full bg-green-400/80"></div>
                    </div>
                    <div className="ml-4 text-white/60 text-xs">taxpoynt.com/dashboard</div>
                  </div>
                  
                  {/* Dashboard Content */}
                  <div className="h-[calc(100%-32px)] relative overflow-hidden">
                    <Image 
                      src="/icons/dashboard-screenshot.webp" 
                      alt="TaxPoynt Dashboard Preview" 
                      width={500} 
                      height={300}
                      className="w-full h-full object-cover object-top"
                      priority
                    />
                    
                    {/* Overlay Animation Effects */}
                    <div className="absolute inset-0 bg-gradient-to-t from-primary-600/20 to-transparent"></div>
                    
                    {/* Floating Stats */}
                    <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg">
                      <div className="text-xs text-gray-600">Invoices Processed</div>
                      <div className="text-lg font-bold text-primary-700">12,847</div>
                      <div className="text-xs text-green-600">↗ +23% this month</div>
                    </div>
                  </div>
                </div>

                {/* Floating Elements */}
                <div className="absolute -top-4 -left-4 w-24 h-24 bg-cyan-400/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/10">
                  <Shield className="h-10 w-10 text-cyan-300" />
                </div>
                
                <div className="absolute -bottom-4 -right-4 w-20 h-20 bg-blue-400/20 backdrop-blur-sm rounded-xl flex items-center justify-center border border-white/10">
                  <CheckCircle className="h-8 w-8 text-blue-300" />
                </div>

                {/* Status Indicators */}
                <div className="absolute top-1/2 -left-6 transform -translate-y-1/2">
                  <div className="bg-green-500 text-white px-3 py-1 rounded-full text-sm font-medium shadow-lg">
                    FIRS Connected
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Fade Transition */}
      <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-white to-transparent"></div>
    </div>
  );
};

export default EnhancedHero;