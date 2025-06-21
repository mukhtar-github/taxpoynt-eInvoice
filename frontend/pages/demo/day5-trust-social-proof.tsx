import React from 'react';
import { motion } from 'framer-motion';
import MainLayout from '../../components/layouts/MainLayout';
import { Typography } from '../../components/ui/Typography';
import { Card, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import {
  TrustBadges,
  SecurityIndicators,
  TestimonialsCarousel,
  UsageStatistics,
  SuccessStories
} from '../../components/landing';
import { 
  Shield, 
  Users, 
  Award,
  TrendingUp,
  Star,
  CheckCircle
} from 'lucide-react';
import Head from 'next/head';

const Day5TrustSocialProofDemo: React.FC = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2
      }
    }
  };

  const sectionVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut"
      }
    }
  };

  return (
    <>
      <Head>
        <title>Day 5: Trust & Social Proof Demo | TaxPoynt E-Invoice Platform</title>
        <meta name="description" content="Comprehensive showcase of Day 5 trust and social proof components including FIRS compliance badges, security indicators, customer testimonials, usage statistics, and success stories." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <MainLayout>
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="min-h-screen"
        >
          {/* Header Section */}
          <motion.section 
            variants={sectionVariants}
            className="py-16 bg-gradient-to-r from-blue-600 to-cyan-600 text-white"
          >
            <div className="container mx-auto px-4 text-center">
              <div className="flex items-center justify-center space-x-2 mb-4">
                <Shield className="h-8 w-8" />
                <Typography.Heading level="h1" className="text-4xl font-bold text-white">
                  Day 5: Trust & Social Proof
                </Typography.Heading>
              </div>
              <Typography.Text size="lg" className="text-blue-100 max-w-3xl mx-auto">
                Comprehensive showcase of trust-building components including FIRS compliance badges, 
                security indicators, customer testimonials, usage statistics, and detailed success stories.
              </Typography.Text>
              
              {/* Quick Stats */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-12">
                {[
                  { icon: <CheckCircle className="h-6 w-6" />, value: '99.99%', label: 'Uptime' },
                  { icon: <Users className="h-6 w-6" />, value: '15,000+', label: 'Businesses' },
                  { icon: <Star className="h-6 w-6" />, value: '4.9/5', label: 'Rating' },
                  { icon: <TrendingUp className="h-6 w-6" />, value: '25%', label: 'Growth' }
                ].map((stat, index) => (
                  <motion.div
                    key={index}
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.5 + index * 0.1 }}
                    className="text-center"
                  >
                    <div className="flex justify-center mb-2 text-blue-200">
                      {stat.icon}
                    </div>
                    <Typography.Text className="text-2xl font-bold text-white">
                      {stat.value}
                    </Typography.Text>
                    <Typography.Text className="text-sm text-blue-200">
                      {stat.label}
                    </Typography.Text>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.section>

          {/* Component Showcase Grid */}
          <div className="py-16 bg-gray-50">
            <div className="container mx-auto px-4">
              <motion.div variants={sectionVariants} className="text-center mb-12">
                <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                  Trust & Social Proof Components
                </Typography.Heading>
                <Typography.Text size="lg" className="text-gray-600">
                  Five powerful components designed to build customer trust and showcase social proof
                </Typography.Text>
              </motion.div>

              <div className="space-y-16">
                {/* Trust Badges Component */}
                <motion.section variants={sectionVariants}>
                  <Card className="p-8">
                    <CardContent className="p-0">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                            1. Trust Badges & Certifications
                          </Typography.Heading>
                          <Typography.Text className="text-gray-600">
                            FIRS compliance badges, security certifications, and trust indicators
                          </Typography.Text>
                        </div>
                        <div className="flex space-x-2">
                          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                            FIRS Certified
                          </span>
                          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                            Security First
                          </span>
                        </div>
                      </div>
                      
                      <div className="space-y-8">
                        <div>
                          <Typography.Text className="font-semibold mb-4 block">Inline Variant:</Typography.Text>
                          <TrustBadges variant="inline" animated={true} />
                        </div>
                        
                        <div>
                          <Typography.Text className="font-semibold mb-4 block">Grid Variant:</Typography.Text>
                          <TrustBadges variant="grid" animated={true} />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.section>

                {/* Security Indicators Component */}
                <motion.section variants={sectionVariants}>
                  <Card className="p-8">
                    <CardContent className="p-0">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                            2. Security Indicators
                          </Typography.Heading>
                          <Typography.Text className="text-gray-600">
                            Real-time security status, trust metrics, and uptime monitoring
                          </Typography.Text>
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-green-600 font-medium">All Systems Operational</span>
                        </div>
                      </div>
                      
                      <div className="space-y-8">
                        <div>
                          <Typography.Text className="font-semibold mb-4 block">Banner Layout:</Typography.Text>
                          <SecurityIndicators layout="banner" animated={true} />
                        </div>
                        
                        <div>
                          <Typography.Text className="font-semibold mb-4 block">Compact Metrics:</Typography.Text>
                          <SecurityIndicators layout="compact" animated={true} />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.section>

                {/* Usage Statistics Component */}
                <motion.section variants={sectionVariants}>
                  <Card className="p-8">
                    <CardContent className="p-0">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                            3. Usage Statistics with Animated Counters
                          </Typography.Heading>
                          <Typography.Text className="text-gray-600">
                            Live platform statistics with smooth counter animations
                          </Typography.Text>
                        </div>
                        <div className="flex items-center space-x-2">
                          <TrendingUp className="h-5 w-5 text-green-500" />
                          <span className="text-green-600 font-medium">Live Data</span>
                        </div>
                      </div>
                      
                      <UsageStatistics 
                        layout="grid"
                        animated={true}
                        showDescriptions={true}
                        theme="light"
                      />
                    </CardContent>
                  </Card>
                </motion.section>

                {/* Testimonials Carousel Component */}
                <motion.section variants={sectionVariants}>
                  <Card className="p-8">
                    <CardContent className="p-0">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                            4. Customer Testimonials Carousel
                          </Typography.Heading>
                          <Typography.Text className="text-gray-600">
                            Interactive testimonials with ratings, metrics, and auto-play functionality
                          </Typography.Text>
                        </div>
                        <div className="flex items-center space-x-1">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                          ))}
                          <span className="ml-2 text-gray-600 font-medium">4.9/5</span>
                        </div>
                      </div>
                      
                      <TestimonialsCarousel 
                        autoPlay={true}
                        interval={5000}
                        showMetrics={true}
                        showRating={true}
                        layout="single"
                        animated={true}
                      />
                    </CardContent>
                  </Card>
                </motion.section>

                {/* Success Stories Component */}
                <motion.section variants={sectionVariants}>
                  <Card className="p-8">
                    <CardContent className="p-0">
                      <div className="flex items-center justify-between mb-6">
                        <div>
                          <Typography.Heading level="h3" className="text-2xl font-bold mb-2">
                            5. Success Stories
                          </Typography.Heading>
                          <Typography.Text className="text-gray-600">
                            Detailed case studies with metrics, filters, and expandable content
                          </Typography.Text>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Award className="h-5 w-5 text-orange-500" />
                          <span className="text-orange-600 font-medium">6 Stories</span>
                        </div>
                      </div>
                      
                      <SuccessStories 
                        showFilters={true}
                        layout="grid"
                        maxStories={4}
                        animated={true}
                      />
                    </CardContent>
                  </Card>
                </motion.section>
              </div>
            </div>
          </div>

          {/* Implementation Guide */}
          <motion.section variants={sectionVariants} className="py-16 bg-white">
            <div className="container mx-auto px-4">
              <div className="text-center mb-12">
                <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                  Implementation Guide
                </Typography.Heading>
                <Typography.Text size="lg" className="text-gray-600">
                  How to integrate these trust and social proof components into your landing page
                </Typography.Text>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {[
                  {
                    step: '1',
                    title: 'Import Components',
                    description: 'Import the trust components from the landing components library',
                    code: `import { 
  TrustBadges, 
  SecurityIndicators,
  TestimonialsCarousel,
  UsageStatistics,
  SuccessStories
} from '../components/landing';`
                  },
                  {
                    step: '2',
                    title: 'Configure Props',
                    description: 'Customize each component with the appropriate props for your use case',
                    code: `<TrustBadges 
  variant="inline"
  animated={true}
  showFIRSBadges={true}
/>`
                  },
                  {
                    step: '3',
                    title: 'Position Strategically',
                    description: 'Place components at key conversion points throughout your landing page',
                    code: `// After hero section
<TrustBadges />

// Before pricing
<TestimonialsCarousel />

// At bottom
<SuccessStories />`
                  }
                ].map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + index * 0.1 }}
                  >
                    <Card className="h-full">
                      <CardContent className="p-6">
                        <div className="flex items-center mb-4">
                          <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center font-bold mr-3">
                            {item.step}
                          </div>
                          <Typography.Heading level="h3" className="text-lg font-semibold">
                            {item.title}
                          </Typography.Heading>
                        </div>
                        <Typography.Text className="text-gray-600 mb-4">
                          {item.description}
                        </Typography.Text>
                        <div className="bg-gray-100 rounded-lg p-3">
                          <code className="text-sm text-gray-800">
                            {item.code}
                          </code>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.section>

          {/* Call to Action */}
          <motion.section variants={sectionVariants} className="py-16 bg-gradient-to-r from-blue-600 to-cyan-600 text-white">
            <div className="container mx-auto px-4 text-center">
              <Typography.Heading level="h2" className="text-3xl font-bold mb-4">
                Ready to Build Trust with Your Customers?
              </Typography.Heading>
              <Typography.Text size="lg" className="text-blue-100 mb-8 max-w-2xl mx-auto">
                These trust and social proof components are now integrated into the TaxPoynt landing page, 
                helping convert visitors into confident customers.
              </Typography.Text>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Button size="lg" variant="outline" className="bg-white text-blue-600 hover:bg-gray-100">
                  View Landing Page
                </Button>
                <Button size="lg" className="bg-blue-700 hover:bg-blue-800 text-white">
                  Start Building Trust
                </Button>
              </div>
            </div>
          </motion.section>
        </motion.div>
      </MainLayout>
    </>
  );
};

export default Day5TrustSocialProofDemo;