import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ChevronLeft, 
  ChevronRight, 
  Star, 
  Quote,
  Users,
  Building,
  TrendingUp,
  CheckCircle,
  Play,
  Pause
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Card, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';

interface Testimonial {
  id: string;
  name: string;
  title: string;
  company: string;
  industry: string;
  rating: number;
  quote: string;
  avatar?: string;
  companyLogo?: string;
  metrics?: {
    label: string;
    value: string;
  }[];
}

interface TestimonialsCarouselProps {
  testimonials?: Testimonial[];
  autoPlay?: boolean;
  interval?: number;
  showMetrics?: boolean;
  showRating?: boolean;
  layout?: 'single' | 'multi' | 'grid';
  animated?: boolean;
}

const TestimonialsCarousel: React.FC<TestimonialsCarouselProps> = ({
  testimonials,
  autoPlay = true,
  interval = 5000,
  showMetrics = true,
  showRating = true,
  layout = 'single',
  animated = true
}) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);

  const defaultTestimonials: Testimonial[] = [
    {
      id: '1',
      name: 'Adebayo Ogundimu',
      title: 'Chief Financial Officer',
      company: 'Zenith Manufacturing Ltd',
      industry: 'Manufacturing',
      rating: 5,
      quote: 'TaxPoynt transformed our e-invoicing process completely. What used to take our accounting team 3 days now happens automatically in minutes. The FIRS compliance is seamless, and we\'ve had zero rejections since implementation.',
      metrics: [
        { label: 'Time Saved', value: '85%' },
        { label: 'Error Reduction', value: '100%' },
        { label: 'Processing Speed', value: '10x Faster' }
      ]
    },
    {
      id: '2',
      name: 'Fatima Al-Hassan',
      title: 'Head of Operations',
      company: 'Sahel Logistics Group',
      industry: 'Logistics',
      rating: 5,
      quote: 'The integration with our ERP system was surprisingly smooth. TaxPoynt\'s APP certification gives us confidence that all our invoices meet FIRS requirements. The real-time status updates help us stay on top of compliance.',
      metrics: [
        { label: 'Monthly Invoices', value: '12,000+' },
        { label: 'Compliance Rate', value: '100%' },
        { label: 'System Uptime', value: '99.9%' }
      ]
    },
    {
      id: '3',
      name: 'Chinedu Okoro',
      title: 'IT Director',
      company: 'Eagle Financial Services',
      industry: 'Financial Services',
      rating: 5,
      quote: 'Security was our biggest concern when moving to e-invoicing. TaxPoynt\'s enterprise-grade security and digital certificate management exceeded our expectations. The audit trails are comprehensive and always ready for compliance checks.',
      metrics: [
        { label: 'Security Score', value: 'A+' },
        { label: 'Audit Compliance', value: '100%' },
        { label: 'Data Protection', value: 'NDPR Certified' }
      ]
    },
    {
      id: '4',
      name: 'Amina Bello',
      title: 'Managing Director',
      company: 'Kano Trading Company',
      industry: 'Trading',
      rating: 5,
      quote: 'As a growing business, we needed an e-invoicing solution that could scale with us. TaxPoynt\'s flexible pricing and robust features mean we\'re prepared for future growth while staying compliant today.',
      metrics: [
        { label: 'Growth Support', value: '500% Scale' },
        { label: 'Cost Savings', value: '40%' },
        { label: 'Setup Time', value: '< 1 Day' }
      ]
    },
    {
      id: '5',
      name: 'Dr. Samuel Adebisi',
      title: 'Chief Technology Officer',
      company: 'HealthTech Solutions',
      industry: 'Healthcare Technology',
      rating: 5,
      quote: 'The API integration capabilities are outstanding. We connected our custom healthcare management system seamlessly. The developer support team was incredibly helpful throughout the integration process.',
      metrics: [
        { label: 'API Response Time', value: '<100ms' },
        { label: 'Integration Time', value: '2 Hours' },
        { label: 'Success Rate', value: '99.8%' }
      ]
    }
  ];

  const testimonialsData = testimonials || defaultTestimonials;

  useEffect(() => {
    if (isPlaying && testimonialsData.length > 1) {
      const timer = setInterval(() => {
        setCurrentIndex((prevIndex) => 
          (prevIndex + 1) % testimonialsData.length
        );
      }, interval);

      return () => clearInterval(timer);
    }
  }, [isPlaying, interval, testimonialsData.length]);

  const goToNext = () => {
    setCurrentIndex((prevIndex) => 
      (prevIndex + 1) % testimonialsData.length
    );
  };

  const goToPrevious = () => {
    setCurrentIndex((prevIndex) => 
      prevIndex === 0 ? testimonialsData.length - 1 : prevIndex - 1
    );
  };

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
  };

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const renderStars = (rating: number) => {
    return [...Array(5)].map((_, i) => (
      <Star
        key={i}
        className={`h-5 w-5 ${
          i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  const slideVariants = {
    enter: (direction: number) => ({
      x: direction > 0 ? 1000 : -1000,
      opacity: 0
    }),
    center: {
      zIndex: 1,
      x: 0,
      opacity: 1
    },
    exit: (direction: number) => ({
      zIndex: 0,
      x: direction < 0 ? 1000 : -1000,
      opacity: 0
    })
  };

  const TestimonialCard = ({ testimonial, index }: { testimonial: Testimonial; index: number }) => (
    <Card className="h-full bg-gray-100 shadow-lg border-0">
      <CardContent className="p-8">
        <div className="flex items-start space-x-4 mb-6">
          <Quote className="h-8 w-8 text-blue-600 flex-shrink-0 mt-1" />
          <div className="flex-1">
            {showRating && (
              <div className="flex items-center mb-4">
                {renderStars(testimonial.rating)}
              </div>
            )}
            <Typography.Text className="text-lg text-gray-700 italic leading-relaxed">
              "{testimonial.quote}"
            </Typography.Text>
          </div>
        </div>

        <div className="border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg">
                {testimonial.name.charAt(0)}
              </div>
              <div>
                <Typography.Text className="font-semibold text-gray-900">
                  {testimonial.name}
                </Typography.Text>
                <Typography.Text className="text-sm text-gray-600">
                  {testimonial.title}
                </Typography.Text>
                <div className="flex items-center space-x-2 mt-1">
                  <Building className="h-4 w-4 text-gray-400" />
                  <Typography.Text className="text-sm text-gray-600">
                    {testimonial.company}
                  </Typography.Text>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {testimonial.industry}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {showMetrics && testimonial.metrics && (
            <div className="grid grid-cols-3 gap-4 bg-gray-50 rounded-lg p-4">
              {testimonial.metrics.map((metric, metricIndex) => (
                <div key={metricIndex} className="text-center">
                  <Typography.Text className="text-lg font-bold text-blue-600">
                    {metric.value}
                  </Typography.Text>
                  <Typography.Text className="text-xs text-gray-600">
                    {metric.label}
                  </Typography.Text>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

  if (layout === 'grid') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {testimonialsData.slice(0, 6).map((testimonial, index) => (
          <motion.div
            key={testimonial.id}
            initial={animated ? { opacity: 0, y: 20 } : {}}
            animate={animated ? { opacity: 1, y: 0 } : {}}
            transition={{ delay: index * 0.1 }}
          >
            <TestimonialCard testimonial={testimonial} index={index} />
          </motion.div>
        ))}
      </div>
    );
  }

  if (layout === 'multi') {
    return (
      <div className="space-y-6">
        <div className="flex justify-center space-x-4 mb-8">
          {testimonialsData.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`w-3 h-3 rounded-full transition-colors ${
                index === currentIndex ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[currentIndex, (currentIndex + 1) % testimonialsData.length].map((index) => (
            <motion.div
              key={`multi-${index}`}
              initial={animated ? { opacity: 0, x: 50 } : {}}
              animate={animated ? { opacity: 1, x: 0 } : {}}
              transition={{ duration: 0.5 }}
            >
              <TestimonialCard testimonial={testimonialsData[index]} index={index} />
            </motion.div>
          ))}
        </div>
      </div>
    );
  }

  // Default single layout
  return (
    <div className="relative">
      <div className="overflow-hidden">
        <AnimatePresence mode="wait" custom={currentIndex}>
          <motion.div
            key={currentIndex}
            custom={currentIndex}
            variants={animated ? slideVariants : {}}
            initial={animated ? "enter" : ""}
            animate={animated ? "center" : ""}
            exit={animated ? "exit" : ""}
            transition={{
              x: { type: "spring", stiffness: 300, damping: 30 },
              opacity: { duration: 0.2 }
            }}
          >
            <TestimonialCard 
              testimonial={testimonialsData[currentIndex]} 
              index={currentIndex} 
            />
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Navigation Controls */}
      <div className="flex justify-between items-center mt-6">
        <div className="flex items-center space-x-4">
          <Button
            variant="outline"
            size="sm"
            onClick={goToPrevious}
            disabled={testimonialsData.length <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={goToNext}
            disabled={testimonialsData.length <= 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={togglePlayPause}
            disabled={testimonialsData.length <= 1}
          >
            {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
          </Button>
        </div>

        <div className="flex space-x-2">
          {testimonialsData.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`w-2 h-2 rounded-full transition-colors ${
                index === currentIndex ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            />
          ))}
        </div>

        <div className="text-sm text-gray-500">
          {currentIndex + 1} of {testimonialsData.length}
        </div>
      </div>
    </div>
  );
};

export default TestimonialsCarousel;