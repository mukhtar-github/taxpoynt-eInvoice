import React, { useEffect, useState, useRef } from 'react';
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
  const [isAnimating, setIsAnimating] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);
  const slideRef = useRef<HTMLDivElement>(null);

  // Trigger animations on mount (instead of intersection observer which may not work properly)
  useEffect(() => {
    // Small delay to ensure proper mounting
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  // Auto-rotating value propositions with smoother animation
  const valuePropositions = [
    "Automated E-Invoice Processing",
    "FIRS Compliant Transmission", 
    "Real-time Integration Sync",
    "Secure Certificate Management"
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setIsAnimating(true);
      
      // Small delay for animation to complete
      setTimeout(() => {
        setCurrentSlide((prev) => (prev + 1) % valuePropositions.length);
        setIsAnimating(false);
      }, 300);
    }, 4000);
    
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
      ref={heroRef}
      className={`relative overflow-hidden min-h-screen flex items-center ${className}`}
    >
      {/* Enhanced Gradient Background */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-900 to-gray-900">
        {/* Animated Background Patterns */}
        <div className="absolute inset-0 opacity-20">
          <div 
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500 rounded-full mix-blend-multiply filter blur-3xl"
            style={{
              animation: 'float 6s ease-in-out infinite',
              animationDelay: '0s'
            }}
          ></div>
          <div 
            className="absolute top-1/3 right-1/4 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl"
            style={{
              animation: 'float 8s ease-in-out infinite',
              animationDelay: '2s'
            }}
          ></div>
          <div 
            className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-3xl"
            style={{
              animation: 'float 7s ease-in-out infinite',
              animationDelay: '4s'
            }}
          ></div>
        </div>
        
        {/* Geometric Pattern Overlay */}
        <div className="absolute inset-0 opacity-5">
          <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
            <defs>
              <pattern id="heroGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                <path d="M 10 0 L 0 0 0 10" fill="none" stroke="white" strokeWidth="0.5"/>
              </pattern>
            </defs>
            <rect width="100" height="100" fill="url(#heroGrid)" />
          </svg>
        </div>
      </div>

      {/* CSS Keyframes for floating animation */}
      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) translateX(0px);
          }
          25% {
            transform: translateY(-20px) translateX(10px);
          }
          50% {
            transform: translateY(0px) translateX(-10px);
          }
          75% {
            transform: translateY(20px) translateX(5px);
          }
        }
        
        @keyframes slideIn {
          from {
            transform: translateY(30px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
        
        @keyframes fadeInUp {
          from {
            transform: translateY(20px);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }

        .animate-slide-in {
          animation: slideIn 0.8s ease-out forwards;
        }
        
        .animate-fade-in-up {
          animation: fadeInUp 0.6s ease-out forwards;
        }
      `}</style>

      {/* Main Content */}
      <div className="relative z-10 w-full">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[80vh]">
            
            {/* Left Column - Content */}
            <div className="space-y-8">
              
              {/* Badge */}
              <div 
                className={`inline-flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2 ${
                  isVisible ? 'animate-slide-in' : 'opacity-0 translate-y-10'
                }`}
                style={{ animationDelay: '0.1s' }}
              >
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-white font-medium text-sm">FIRS Certified Access Point Provider</span>
              </div>

              {/* Main Headline */}
              <div className="space-y-6">
                <div 
                  className={`${
                    isVisible ? 'animate-slide-in' : 'opacity-0 translate-y-10'
                  }`}
                  style={{ animationDelay: '0.2s' }}
                >
                  <Typography.Heading 
                    level="h1" 
                    className="text-4xl md:text-5xl xl:text-6xl font-bold text-white leading-tight"
                  >
                    Nigeria's Premier{' '}
                    <span className="block bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">
                      E-Invoicing Platform
                    </span>
                  </Typography.Heading>
                </div>

                {/* Animated Value Proposition */}
                <div 
                  className={`h-12 md:h-14 relative overflow-hidden ${
                    isVisible ? 'animate-slide-in' : 'opacity-0 translate-y-10'
                  }`}
                  style={{ animationDelay: '0.3s' }}
                  ref={slideRef}
                >
                  <div 
                    className={`transition-all duration-500 ease-in-out ${
                      isAnimating ? 'opacity-50 transform translate-y-2' : 'opacity-100 transform translate-y-0'
                    }`}
                    style={{ transform: `translateY(-${currentSlide * 100}%)` }}
                  >
                    {valuePropositions.map((proposition, index) => (
                      <div 
                        key={index}
                        className="h-12 md:h-14 flex items-center"
                      >
                        <Typography.Text 
                          size="lg" 
                          className="text-cyan-200 font-semibold text-lg md:text-xl"
                        >
                          ✨ {proposition}
                        </Typography.Text>
                      </div>
                    ))}
                  </div>
                </div>

                <div 
                  className={`${
                    isVisible ? 'animate-slide-in' : 'opacity-0 translate-y-10'
                  }`}
                  style={{ animationDelay: '0.4s' }}
                >
                  <Typography.Text 
                    size="lg" 
                    className="text-gray-200 leading-relaxed max-w-xl text-lg"
                  >
                    Streamline your entire e-invoicing workflow from ERP integration to secure FIRS submission. 
                    Our dual-certified platform ensures compliance while saving time and reducing errors.
                  </Typography.Text>
                </div>
              </div>

              {/* Call-to-Action Buttons */}
              <div 
                className={`flex flex-col sm:flex-row gap-4 ${
                  isVisible ? 'animate-slide-in' : 'opacity-0 translate-y-10'
                }`}
                style={{ animationDelay: '0.5s' }}
              >
                <Button 
                  size="lg"
                  className="bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-600 hover:to-blue-700 font-bold shadow-xl transform hover:scale-105 transition-all duration-300 border-0"
                  onClick={() => router.push('/auth/signup')}
                >
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="outline" 
                  className="border-white/30 text-white hover:bg-white/10 backdrop-blur-sm font-semibold group transition-all duration-300"
                  onClick={() => router.push('/pricing')}
                >
                  <span className="mr-2">₦</span>
                  View Pricing
                  <ArrowRight className="ml-2 h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
                
                <Button 
                  size="lg"
                  variant="ghost" 
                  className="text-white hover:bg-white/10 font-semibold group"
                  onClick={() => {
                    // Scroll to demo section or features
                    window.scrollTo({ top: window.innerHeight, behavior: 'smooth' });
                  }}
                >
                  <Play className="mr-2 h-4 w-4" />
                  Learn More
                </Button>
              </div>

              {/* Trust Indicators */}
              <div 
                className={`grid grid-cols-2 md:grid-cols-4 gap-4 pt-8 ${
                  isVisible ? 'animate-fade-in-up' : 'opacity-0 translate-y-10'
                }`}
                style={{ animationDelay: '0.6s' }}
              >
                {trustIndicators.map((indicator, index) => (
                  <div 
                    key={index}
                    className={`flex items-center space-x-2 text-gray-300 transform transition-all duration-300 hover:text-white hover:scale-105 ${
                      isVisible ? 'animate-fade-in-up' : 'opacity-0 translate-y-5'
                    }`}
                    style={{ animationDelay: `${0.7 + index * 0.1}s` }}
                  >
                    <div className="flex-shrink-0 text-cyan-400">
                      {indicator.icon}
                    </div>
                    <span className="text-sm font-medium">{indicator.text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Column - Visual */}
            <div 
              className={`hidden lg:flex justify-center ${
                isVisible ? 'animate-slide-in' : 'opacity-0 translate-x-10'
              }`}
              style={{ animationDelay: '0.4s' }}
            >
              <div className="relative">
                
                {/* Main Dashboard Preview */}
                <div 
                  className="relative w-full max-w-lg h-96 bg-white/5 backdrop-blur-md rounded-3xl overflow-hidden border border-white/10 shadow-2xl"
                  style={{
                    animation: isVisible ? 'float 6s ease-in-out infinite' : 'none',
                    animationDelay: '1s'
                  }}
                >
                  
                  {/* Browser Frame */}
                  <div className="h-10 bg-gray-800/30 flex items-center px-4 backdrop-blur-sm border-b border-white/10">
                    <div className="flex space-x-2">
                      <div className="w-3 h-3 rounded-full bg-red-400"></div>
                      <div className="w-3 h-3 rounded-full bg-yellow-400"></div>
                      <div className="w-3 h-3 rounded-full bg-green-400"></div>
                    </div>
                    <div className="ml-4 text-white/70 text-xs font-mono">taxpoynt.com/dashboard</div>
                  </div>
                  
                  {/* Dashboard Content Placeholder */}
                  <div className="h-[calc(100%-40px)] relative overflow-hidden bg-gradient-to-br from-slate-100 to-white">
                    {/* Simulated Dashboard UI */}
                    <div className="p-6 space-y-4">
                      {/* Header */}
                      <div className="flex items-center justify-between">
                        <div className="h-6 bg-gray-300 rounded w-40 animate-pulse"></div>
                        <div className="h-8 bg-green-500 rounded px-4 flex items-center">
                          <span className="text-white text-xs font-medium">FIRS Connected</span>
                        </div>
                      </div>
                      
                      {/* Stats Cards */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <div className="h-3 bg-gray-200 rounded w-20 mb-2"></div>
                          <div className="h-6 bg-blue-500 rounded w-16 mb-1"></div>
                          <div className="h-2 bg-green-200 rounded w-12"></div>
                        </div>
                        <div className="bg-white rounded-lg p-4 shadow-sm border">
                          <div className="h-3 bg-gray-200 rounded w-24 mb-2"></div>
                          <div className="h-6 bg-cyan-500 rounded w-20 mb-1"></div>
                          <div className="h-2 bg-green-200 rounded w-16"></div>
                        </div>
                      </div>
                      
                      {/* Chart Area */}
                      <div className="bg-white rounded-lg p-4 shadow-sm border h-32">
                        <div className="h-3 bg-gray-200 rounded w-32 mb-3"></div>
                        <div className="flex items-end space-x-1 h-20">
                          {[...Array(8)].map((_, i) => (
                            <div 
                              key={i}
                              className="bg-gradient-to-t from-blue-500 to-cyan-400 rounded-t flex-1"
                              style={{ 
                                height: `${Math.random() * 80 + 20}%`,
                                animation: `fadeInUp 0.5s ease-out ${i * 0.1}s forwards`
                              }}
                            ></div>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    {/* Floating Success Indicator */}
                    <div 
                      className="absolute top-4 right-4 bg-green-100 border border-green-200 rounded-lg p-3 shadow-lg"
                      style={{
                        animation: isVisible ? 'float 4s ease-in-out infinite' : 'none',
                        animationDelay: '2s'
                      }}
                    >
                      <div className="text-xs text-green-700">Invoices Today</div>
                      <div className="text-xl font-bold text-green-800">847</div>
                      <div className="text-xs text-green-600 flex items-center">
                        <span className="text-green-500 mr-1">↗</span> +23%
                      </div>
                    </div>
                  </div>
                </div>

                {/* Floating Elements */}
                <div 
                  className="absolute -top-6 -left-6 w-20 h-20 bg-cyan-400/20 backdrop-blur-sm rounded-2xl flex items-center justify-center border border-cyan-300/20"
                  style={{
                    animation: isVisible ? 'float 5s ease-in-out infinite' : 'none',
                    animationDelay: '0.5s'
                  }}
                >
                  <Shield className="h-8 w-8 text-cyan-300" />
                </div>
                
                <div 
                  className="absolute -bottom-6 -right-6 w-16 h-16 bg-green-400/20 backdrop-blur-sm rounded-2xl flex items-center justify-center border border-green-300/20"
                  style={{
                    animation: isVisible ? 'float 4s ease-in-out infinite' : 'none',
                    animationDelay: '1.5s'
                  }}
                >
                  <CheckCircle className="h-6 w-6 text-green-300" />
                </div>

                {/* Status Badge */}
                <div 
                  className="absolute top-1/2 -left-8 transform -translate-y-1/2"
                  style={{
                    animation: isVisible ? 'slideIn 0.8s ease-out forwards' : 'none',
                    animationDelay: '1s'
                  }}
                >
                  <div className="bg-green-500 text-white px-4 py-2 rounded-full text-sm font-medium shadow-lg relative">
                    FIRS Certified
                    <div className="absolute -right-1 top-1/2 transform -translate-y-1/2 w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div 
        className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 text-white/60 ${
          isVisible ? 'animate-bounce' : 'opacity-0'
        }`}
        style={{ animationDelay: '2s' }}
      >
        <div className="flex flex-col items-center space-y-2">
          <span className="text-sm">Scroll to explore</span>
          <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
            <div className="w-1 h-3 bg-white/60 rounded-full mt-2 animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedHero;